from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search import SearchResponse
from app.search.query import SearchParams
from app.search.service import SearchService

router = APIRouter(tags=["search"])
DBSession = Depends(get_db)


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(...),
    ticker: str | None = None,
    source_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 10,
    db: Session = DBSession,
) -> SearchResponse:
    try:
        params = SearchParams(
            q=q,
            ticker=ticker,
            source_type=source_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc

    return SearchService(db).search(params)
