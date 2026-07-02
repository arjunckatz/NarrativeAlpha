from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import AssetPrice
from app.prices.loader import NormalizedPrice, load_price_csv


@dataclass(frozen=True)
class PriceIngestionSummary:
    rows_read: int
    rows_inserted: int
    rows_skipped_existing: int


def ingest_prices(
    session: Session,
    prices: list[NormalizedPrice],
) -> PriceIngestionSummary:
    inserted = 0
    skipped_existing = 0

    for price in prices:
        if _find_existing_price(session, price) is not None:
            skipped_existing += 1
            continue

        try:
            with session.begin_nested():
                session.add(
                    AssetPrice(
                        ticker=price.ticker,
                        date=price.date,
                        open=price.open,
                        high=price.high,
                        low=price.low,
                        close=price.close,
                        adjusted_close=price.close,
                        volume=price.volume,
                        metadata_={"source": "sample_prices_csv", "synthetic": True},
                    )
                )
                session.flush()
        except IntegrityError:
            skipped_existing += 1
            continue

        inserted += 1

    session.commit()
    return PriceIngestionSummary(
        rows_read=len(prices),
        rows_inserted=inserted,
        rows_skipped_existing=skipped_existing,
    )


def ingest_price_file(session: Session, path: Path) -> PriceIngestionSummary:
    return ingest_prices(session, load_price_csv(path))


def _find_existing_price(
    session: Session,
    price: NormalizedPrice,
) -> AssetPrice | None:
    return session.scalar(
        select(AssetPrice).where(
            AssetPrice.ticker == price.ticker,
            AssetPrice.date == price.date,
        )
    )
