from __future__ import annotations

from app.schemas.search import SearchResponse
from app.search.query import SearchParams


class SearchService:
    def search(self, params: SearchParams) -> SearchResponse:
        raise NotImplementedError("Search retrieval is not implemented yet")
