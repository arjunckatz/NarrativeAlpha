from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.narratives.service import NarrativeAggregationService
from app.schemas.narratives import NarrativeCandidateResponse

router = APIRouter(tags=["narratives"])
DBSession = Depends(get_db)


@router.get("/narratives", response_model=list[NarrativeCandidateResponse])
def list_narratives(
    ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = DBSession,
) -> list[NarrativeCandidateResponse]:
    return NarrativeAggregationService(db).aggregate(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
    )
