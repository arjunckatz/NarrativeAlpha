from collections.abc import Generator
from datetime import UTC, datetime
from hashlib import sha256

import pytest
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import Document, DocumentChunk
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def search_client() -> Generator[tuple[TestClient, Session], None, None]:
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


def add_document(
    session: Session,
    *,
    ticker: str,
    source_type: str,
    published_at: datetime,
    title: str,
    bm25_text: str,
    chunk_index: int = 0,
) -> None:
    document = Document(
        source_type=source_type,
        ticker=ticker,
        title=title,
        published_at=published_at,
        source_name="Synthetic Test Source",
        url=None,
        content_hash=sha256(
            f"{ticker}|{source_type}|{published_at.isoformat()}|{title}|{chunk_index}".encode()
        ).hexdigest(),
        raw_text=bm25_text,
        metadata_={"test": True},
    )
    session.add(document)
    session.flush()
    session.add(
        DocumentChunk(
            document_id=document.id,
            chunk_index=chunk_index,
            text=bm25_text,
            bm25_text=bm25_text,
            metadata_={"chunk": chunk_index},
        )
    )
    session.commit()


def test_search_endpoint_returns_results(search_client: tuple[TestClient, Session]) -> None:
    client, session = search_client
    add_document(
        session,
        ticker="NVDA",
        source_type="synthetic",
        published_at=datetime(2026, 6, 1, tzinfo=UTC),
        title="Export restrictions",
        bm25_text="export restrictions affect accelerator sales",
    )

    response = client.get("/api/search", params={"q": "export restrictions"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "export restrictions"
    assert payload["results"][0]["document"]["ticker"] == "NVDA"
    assert payload["results"][0]["score"] > 0
    assert payload["results"][0]["snippet"] == "export restrictions affect accelerator sales"


def test_search_endpoint_ticker_filter(search_client: tuple[TestClient, Session]) -> None:
    client, session = search_client
    add_document(
        session,
        ticker="NVDA",
        source_type="synthetic",
        published_at=datetime(2026, 6, 1, tzinfo=UTC),
        title="NVDA export restrictions",
        bm25_text="export restrictions affect accelerator sales",
    )
    add_document(
        session,
        ticker="AAPL",
        source_type="synthetic",
        published_at=datetime(2026, 6, 2, tzinfo=UTC),
        title="AAPL export restrictions",
        bm25_text="export restrictions mentioned in market note",
    )

    response = client.get("/api/search", params={"q": "export restrictions", "ticker": "nvda"})

    assert response.status_code == 200
    assert [result["document"]["ticker"] for result in response.json()["results"]] == ["NVDA"]


def test_search_endpoint_source_type_filter(search_client: tuple[TestClient, Session]) -> None:
    client, session = search_client
    add_document(
        session,
        ticker="NVDA",
        source_type="synthetic",
        published_at=datetime(2026, 6, 1, tzinfo=UTC),
        title="Synthetic capex note",
        bm25_text="cloud capex demand",
    )
    add_document(
        session,
        ticker="NVDA",
        source_type="news",
        published_at=datetime(2026, 6, 2, tzinfo=UTC),
        title="News capex note",
        bm25_text="cloud capex demand",
    )

    response = client.get("/api/search", params={"q": "cloud capex", "source_type": "synthetic"})

    assert response.status_code == 200
    assert [result["document"]["source_type"] for result in response.json()["results"]] == [
        "synthetic"
    ]


def test_search_endpoint_date_filter(search_client: tuple[TestClient, Session]) -> None:
    client, session = search_client
    add_document(
        session,
        ticker="TSLA",
        source_type="synthetic",
        published_at=datetime(2026, 5, 1, tzinfo=UTC),
        title="Old delivery miss",
        bm25_text="delivery miss pressure",
    )
    add_document(
        session,
        ticker="TSLA",
        source_type="synthetic",
        published_at=datetime(2026, 6, 10, tzinfo=UTC),
        title="Current delivery miss",
        bm25_text="delivery miss pressure",
    )

    response = client.get(
        "/api/search",
        params={"q": "delivery miss", "start_date": "2026-06-01", "end_date": "2026-06-30"},
    )

    assert response.status_code == 200
    assert [result["document"]["title"] for result in response.json()["results"]] == [
        "Current delivery miss"
    ]


def test_search_endpoint_limit_behavior(search_client: tuple[TestClient, Session]) -> None:
    client, session = search_client
    for index in range(3):
        add_document(
            session,
            ticker="NVDA",
            source_type="synthetic",
            published_at=datetime(2026, 6, index + 1, tzinfo=UTC),
            title=f"AI demand {index}",
            bm25_text="ai demand datacenter",
            chunk_index=index,
        )

    response = client.get("/api/search", params={"q": "ai demand", "limit": 2})

    assert response.status_code == 200
    assert len(response.json()["results"]) == 2


def test_search_endpoint_empty_query_validation(search_client: tuple[TestClient, Session]) -> None:
    client, _session = search_client

    response = client.get("/api/search", params={"q": "   "})

    assert response.status_code == 422


def test_search_endpoint_invalid_source_type(search_client: tuple[TestClient, Session]) -> None:
    client, _session = search_client

    response = client.get("/api/search", params={"q": "cloud capex", "source_type": "blog"})

    assert response.status_code == 422


def test_search_endpoint_invalid_date_range(search_client: tuple[TestClient, Session]) -> None:
    client, _session = search_client

    response = client.get(
        "/api/search",
        params={"q": "china demand", "start_date": "2026-06-30", "end_date": "2026-06-01"},
    )

    assert response.status_code == 422


def test_search_endpoint_no_results_returns_empty_list(
    search_client: tuple[TestClient, Session],
) -> None:
    client, session = search_client
    add_document(
        session,
        ticker="AAPL",
        source_type="synthetic",
        published_at=datetime(2026, 6, 1, tzinfo=UTC),
        title="China demand",
        bm25_text="china demand concerns",
    )

    response = client.get("/api/search", params={"q": "export restrictions"})

    assert response.status_code == 200
    assert response.json()["results"] == []
