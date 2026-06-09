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
        "raw_text",
        "metadata",
    ]:
        assert column_name in columns


def test_narrative_score_unique_contract() -> None:
    constraints = Base.metadata.tables["narrative_scores"].constraints

    assert any(
        constraint.name == "uq_narrative_scores_ticker_narrative_date" for constraint in constraints
    )
