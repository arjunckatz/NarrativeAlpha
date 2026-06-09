from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_initial_migration_upgrades_clean_database(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db_path = tmp_path / "migration.db"
    database_url = f"sqlite:///{db_path}"
    alembic_cfg = Config("backend/alembic.ini")
    alembic_cfg.set_main_option("script_location", "backend/alembic")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(alembic_cfg, "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert {
        "companies",
        "asset_prices",
        "documents",
        "document_chunks",
        "events",
        "narratives",
        "narrative_evidence",
        "narrative_scores",
    }.issubset(set(inspector.get_table_names()))
