from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from app.db.base import Base
from app.models import AssetPrice
from app.prices.loader import PriceValidationError, load_price_csv
from app.prices.service import ingest_price_file
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def write_prices(path: Path, rows: list[str]) -> Path:
    path.write_text(
        "ticker,date,open,high,low,close,volume\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )
    return path


def test_price_csv_parsing(tmp_path: Path) -> None:
    path = write_prices(
        tmp_path / "prices.csv",
        ["NVDA,2026-05-01,890.00,912.50,872.40,881.20,42000000"],
    )

    prices = load_price_csv(path)

    assert len(prices) == 1
    assert prices[0].ticker == "NVDA"
    assert prices[0].date == date(2026, 5, 1)
    assert prices[0].open == Decimal("890.00")
    assert prices[0].high == Decimal("912.50")
    assert prices[0].low == Decimal("872.40")
    assert prices[0].close == Decimal("881.20")
    assert prices[0].volume == 42000000


def test_price_ticker_normalization(tmp_path: Path) -> None:
    path = write_prices(
        tmp_path / "prices.csv",
        ["nvda,2026-05-01,890.00,912.50,872.40,881.20,42000000"],
    )

    prices = load_price_csv(path)

    assert prices[0].ticker == "NVDA"


@pytest.mark.parametrize(
    "row, expected_message",
    [
        ("NVDA,not-a-date,890.00,912.50,872.40,881.20,42000000", "date"),
        ("NVDA,2026-05-01,bad,912.50,872.40,881.20,42000000", "open"),
        ("NVDA,2026-05-01,890.00,912.50,872.40,881.20,bad", "volume"),
        (" ,2026-05-01,890.00,912.50,872.40,881.20,42000000", "ticker"),
    ],
)
def test_invalid_price_row_fails_fast(
    tmp_path: Path,
    row: str,
    expected_message: str,
) -> None:
    path = write_prices(tmp_path / "prices.csv", [row])

    with pytest.raises(PriceValidationError, match=expected_message):
        load_price_csv(path)


def test_ingest_price_file_creates_asset_prices(
    tmp_path: Path,
    db_session: Session,
) -> None:
    path = write_prices(
        tmp_path / "prices.csv",
        ["NVDA,2026-05-01,890.00,912.50,872.40,881.20,42000000"],
    )

    summary = ingest_price_file(db_session, path)

    prices = db_session.query(AssetPrice).all()
    assert summary.rows_read == 1
    assert summary.rows_inserted == 1
    assert summary.rows_skipped_existing == 0
    assert len(prices) == 1
    assert prices[0].ticker == "NVDA"
    assert prices[0].adjusted_close == Decimal("881.200000")
    assert prices[0].metadata_["synthetic"] is True


def test_price_ingestion_is_idempotent(tmp_path: Path, db_session: Session) -> None:
    path = write_prices(
        tmp_path / "prices.csv",
        ["NVDA,2026-05-01,890.00,912.50,872.40,881.20,42000000"],
    )

    first = ingest_price_file(db_session, path)
    second = ingest_price_file(db_session, path)

    assert first.rows_inserted == 1
    assert second.rows_inserted == 0
    assert second.rows_skipped_existing == 1
    assert db_session.query(AssetPrice).count() == 1


def test_duplicate_rows_do_not_duplicate_asset_prices(
    tmp_path: Path,
    db_session: Session,
) -> None:
    duplicate = "NVDA,2026-05-01,890.00,912.50,872.40,881.20,42000000"
    path = write_prices(tmp_path / "prices.csv", [duplicate, duplicate])

    summary = ingest_price_file(db_session, path)

    assert summary.rows_read == 2
    assert summary.rows_inserted == 1
    assert summary.rows_skipped_existing == 1
    assert db_session.query(AssetPrice).count() == 1


def test_sample_prices_file_is_valid(db_session: Session) -> None:
    summary = ingest_price_file(db_session, Path("data/sample_prices.csv"))

    assert summary.rows_read == 21
    assert summary.rows_inserted == 21
    assert db_session.query(AssetPrice).count() == 21
