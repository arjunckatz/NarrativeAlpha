from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from app.db.base import Base
from app.models import (
    AssetPrice,
    Company,
    Document,
    DocumentChunk,
    Event,
    Narrative,
    NarrativeEvidence,
    NarrativeScore,
)
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_models_import_cleanly() -> None:
    assert Company.__tablename__ == "companies"
    assert AssetPrice.__tablename__ == "asset_prices"
    assert Document.__tablename__ == "documents"
    assert DocumentChunk.__tablename__ == "document_chunks"
    assert Event.__tablename__ == "events"
    assert Narrative.__tablename__ == "narratives"
    assert NarrativeEvidence.__tablename__ == "narrative_evidence"
    assert NarrativeScore.__tablename__ == "narrative_scores"


def test_metadata_contains_phase_one_tables() -> None:
    expected_tables = {
        "companies",
        "asset_prices",
        "documents",
        "document_chunks",
        "events",
        "narratives",
        "narrative_evidence",
        "narrative_scores",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())


def test_document_columns_match_contract() -> None:
    columns = Base.metadata.tables["documents"].columns

    for column_name in [
        "id",
        "source_type",
        "ticker",
        "title",
        "published_at",
        "source_name",
        "url",
        "content_hash",
        "raw_text",
        "metadata",
    ]:
        assert column_name in columns


def test_narrative_score_unique_contract() -> None:
    constraints = Base.metadata.tables["narrative_scores"].constraints

    assert any(
        constraint.name == "uq_narrative_scores_ticker_narrative_date" for constraint in constraints
    )


def test_metadata_attribute_maps_to_metadata_column() -> None:
    document_table = Base.metadata.tables["documents"]

    assert Document.metadata_.property.columns[0].name == "metadata"
    assert "metadata" in document_table.columns


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def make_document(
    *,
    ticker: str = "AAPL",
    source_type: str = "news",
    source_name: str = "Example News",
    content_hash: str = "a" * 64,
) -> Document:
    return Document(
        source_type=source_type,
        ticker=ticker,
        title="Example document",
        published_at=datetime(2026, 6, 9, tzinfo=UTC),
        source_name=source_name,
        url=None,
        content_hash=content_hash,
        raw_text="Market narrative text.",
        metadata_={},
    )


def test_document_dedupe_constraint(db_session: Session) -> None:
    db_session.add(make_document())
    db_session.commit()

    db_session.add(make_document())

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_document_source_type_check_constraint(db_session: Session) -> None:
    db_session.add(make_document(source_type="blog"))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_chunk_uniqueness(db_session: Session) -> None:
    document = make_document()
    db_session.add(document)
    db_session.flush()
    db_session.add_all(
        [
            DocumentChunk(
                document_id=document.id,
                chunk_index=0,
                text="chunk",
                bm25_text="chunk",
                metadata_={},
            ),
            DocumentChunk(
                document_id=document.id,
                chunk_index=0,
                text="duplicate chunk",
                bm25_text="duplicate chunk",
                metadata_={},
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_asset_price_uniqueness(db_session: Session) -> None:
    price = {
        "ticker": "AAPL",
        "date": date(2026, 6, 9),
        "open": Decimal("100.00"),
        "high": Decimal("101.00"),
        "low": Decimal("99.00"),
        "close": Decimal("100.50"),
        "adjusted_close": Decimal("100.50"),
        "volume": 1000,
        "metadata_": {},
    }
    db_session.add_all([AssetPrice(**price), AssetPrice(**price)])

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_narrative_name_uniqueness(db_session: Session) -> None:
    db_session.add_all(
        [
            Narrative(
                name="AI capex cycle",
                description="Capital spending tied to AI infrastructure.",
                canonical_keywords=["ai", "capex"],
            ),
            Narrative(
                name="AI capex cycle",
                description="Duplicate narrative.",
                canonical_keywords=["ai"],
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_narrative_evidence_foreigns_and_chunk_document_consistency(
    db_session: Session,
) -> None:
    first_document = make_document(content_hash="b" * 64)
    second_document = make_document(content_hash="c" * 64)
    narrative = Narrative(
        name="Margin pressure",
        description="Narrative about margin compression.",
        canonical_keywords=["margin"],
    )
    db_session.add_all([first_document, second_document, narrative])
    db_session.flush()

    chunk = DocumentChunk(
        document_id=first_document.id,
        chunk_index=0,
        text="margin evidence",
        bm25_text="margin evidence",
        metadata_={},
    )
    db_session.add(chunk)
    db_session.flush()

    db_session.add(
        NarrativeEvidence(
            narrative_id=narrative.id,
            document_id=second_document.id,
            chunk_id=chunk.id,
            relevance_score=Decimal("0.900000"),
            evidence_text="margin evidence",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_document_evidence_relationships(db_session: Session) -> None:
    document = make_document(content_hash="d" * 64)
    narrative = Narrative(
        name="Demand recovery",
        description="Narrative about recovering demand.",
        canonical_keywords=["demand"],
    )
    db_session.add_all([document, narrative])
    db_session.flush()

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        text="demand evidence",
        bm25_text="demand evidence",
        metadata_={},
    )
    db_session.add(chunk)
    db_session.flush()
    evidence = NarrativeEvidence(
        narrative_id=narrative.id,
        document_id=document.id,
        chunk_id=chunk.id,
        relevance_score=Decimal("0.800000"),
        evidence_text="demand evidence",
    )
    db_session.add(evidence)
    db_session.commit()

    assert document.evidence == [evidence]
    assert chunk.evidence == [evidence]
