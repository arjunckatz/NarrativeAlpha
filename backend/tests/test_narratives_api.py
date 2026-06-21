from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import Event
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def narratives_client() -> Generator[tuple[TestClient, Session], None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()

    def override_get_db() -> Generator[Session, None, None]:
        yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client, session

    session.close()
    app.dependency_overrides.clear()


def add_event(
    session: Session,
    *,
    ticker: str = "NVDA",
    event_type: str = "export_restriction",
    event_date: date = date(2026, 6, 1),
    confidence: Decimal = Decimal("0.80"),
) -> Event:
    event_row = Event(
        ticker=ticker,
        event_type=event_type,
        event_date=event_date,
        extracted_text=f"{ticker} {event_type}",
        sentiment="negative",
        confidence=confidence,
        metadata_={"test": True},
    )
    session.add(event_row)
    session.commit()
    return event_row


def test_narratives_route_is_registered(narratives_client: tuple[TestClient, Session]) -> None:
    client, _session = narratives_client

    response = client.get("/api/narratives")

    assert response.status_code == 200


def test_narratives_empty_event_table_returns_empty_list(
    narratives_client: tuple[TestClient, Session],
) -> None:
    client, _session = narratives_client

    response = client.get("/api/narratives")

    assert response.status_code == 200
    assert response.json() == []


def test_narratives_successful_response_shape(
    narratives_client: tuple[TestClient, Session],
) -> None:
    client, session = narratives_client
    event_row = add_event(session)

    response = client.get("/api/narratives")

    assert response.status_code == 200
    payload = response.json()
    assert payload == [
        {
            "narrative_name": "Export Restrictions",
            "ticker": "NVDA",
            "event_count": 1,
            "average_confidence": 0.8,
            "max_confidence": 0.8,
            "first_seen": "2026-06-01",
            "last_seen": "2026-06-01",
            "event_types": ["export_restriction"],
            "supporting_event_ids": [event_row.id],
        }
    ]
