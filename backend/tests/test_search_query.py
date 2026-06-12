from datetime import date

import pytest
from app.search.query import SearchParams
from pydantic import ValidationError


def test_query_must_not_be_empty() -> None:
    with pytest.raises(ValidationError, match="q must not be empty"):
        SearchParams(q="   ")


def test_query_whitespace_is_normalized() -> None:
    params = SearchParams(q="  export   restrictions  ")

    assert params.q == "export restrictions"


def test_ticker_is_normalized() -> None:
    params = SearchParams(q="delivery miss", ticker=" tsla ")

    assert params.ticker == "TSLA"


def test_blank_ticker_becomes_none() -> None:
    params = SearchParams(q="margin pressure", ticker="   ")

    assert params.ticker is None


def test_source_type_must_be_supported() -> None:
    with pytest.raises(ValidationError, match="source_type is not supported"):
        SearchParams(q="cloud capex", source_type="blog")


def test_date_range_must_be_ordered() -> None:
    with pytest.raises(ValidationError, match="start_date must be before or equal to end_date"):
        SearchParams(
            q="china demand",
            start_date=date(2026, 6, 12),
            end_date=date(2026, 6, 1),
        )


def test_date_range_accepts_same_day() -> None:
    params = SearchParams(
        q="china demand",
        start_date=date(2026, 6, 12),
        end_date=date(2026, 6, 12),
    )

    assert params.start_date == params.end_date


@pytest.mark.parametrize("limit", [0, 51])
def test_limit_bounds(limit: int) -> None:
    with pytest.raises(ValidationError):
        SearchParams(q="export restrictions", limit=limit)


def test_limit_defaults_to_ten() -> None:
    params = SearchParams(q="export restrictions")

    assert params.limit == 10
