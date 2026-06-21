from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event
from app.narratives.aggregator import NarrativeAggregator, NarrativeCandidate


class NarrativeAggregationService:
    def __init__(
        self,
        session: Session,
        aggregator: NarrativeAggregator | None = None,
    ) -> None:
        self.session = session
        self.aggregator = aggregator or NarrativeAggregator()

    def aggregate(
        self,
        *,
        ticker: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[NarrativeCandidate]:
        events = self._load_events(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
        )
        return self.aggregator.aggregate(events)

    def _load_events(
        self,
        *,
        ticker: str | None,
        start_date: date | None,
        end_date: date | None,
    ) -> list[Event]:
        statement = select(Event).order_by(
            Event.ticker.asc(),
            Event.event_date.asc(),
            Event.id.asc(),
        )
        if ticker:
            statement = statement.where(Event.ticker == ticker.upper())
        if start_date:
            statement = statement.where(Event.event_date >= start_date)
        if end_date:
            statement = statement.where(Event.event_date <= end_date)
        return list(self.session.scalars(statement).all())
