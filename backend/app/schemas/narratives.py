from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class NarrativeCandidateResponse(BaseModel):
    narrative_name: str
    ticker: str
    event_count: int
    average_confidence: float
    max_confidence: float
    first_seen: date
    last_seen: date
    event_types: tuple[str, ...]
    supporting_event_ids: tuple[int, ...]
