from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED_PRICE_FIELDS = ("ticker", "date", "open", "high", "low", "close", "volume")


class PriceValidationError(ValueError):
    pass


@dataclass(frozen=True)
class NormalizedPrice:
    ticker: str
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


def load_price_csv(path: Path) -> list[NormalizedPrice]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        _validate_header(reader.fieldnames)
        return [
            _normalize_price_row(row, row_number=index)
            for index, row in enumerate(reader, start=2)
        ]


def _validate_header(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise PriceValidationError("price CSV is missing a header row")

    missing = [field for field in REQUIRED_PRICE_FIELDS if field not in fieldnames]
    if missing:
        raise PriceValidationError(f"missing required field: {missing[0]}")


def _normalize_price_row(row: dict[str, str], *, row_number: int) -> NormalizedPrice:
    ticker = _required_text(row, "ticker", row_number=row_number).upper()
    return NormalizedPrice(
        ticker=ticker,
        date=_parse_date(row, row_number=row_number),
        open=_parse_decimal(row, "open", row_number=row_number),
        high=_parse_decimal(row, "high", row_number=row_number),
        low=_parse_decimal(row, "low", row_number=row_number),
        close=_parse_decimal(row, "close", row_number=row_number),
        volume=_parse_volume(row, row_number=row_number),
    )


def _required_text(row: dict[str, str], field: str, *, row_number: int) -> str:
    value = (row.get(field) or "").strip()
    if not value:
        raise PriceValidationError(f"row {row_number}: {field} is required")
    return value


def _parse_date(row: dict[str, str], *, row_number: int) -> date:
    value = _required_text(row, "date", row_number=row_number)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise PriceValidationError(
            f"row {row_number}: date must be YYYY-MM-DD"
        ) from exc


def _parse_decimal(
    row: dict[str, str],
    field: str,
    *,
    row_number: int,
) -> Decimal:
    value = _required_text(row, field, row_number=row_number)
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise PriceValidationError(f"row {row_number}: {field} must be numeric") from exc
    if parsed <= 0:
        raise PriceValidationError(f"row {row_number}: {field} must be positive")
    return parsed


def _parse_volume(row: dict[str, str], *, row_number: int) -> int:
    value = _required_text(row, "volume", row_number=row_number)
    try:
        parsed = int(value)
    except ValueError as exc:
        raise PriceValidationError(
            f"row {row_number}: volume must be an integer"
        ) from exc
    if parsed < 0:
        raise PriceValidationError(f"row {row_number}: volume must be non-negative")
    return parsed
