from __future__ import annotations

from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

ALLOWED_SOURCE_TYPES = {"news", "filing", "transcript", "analyst_note", "synthetic"}


class SearchParams(BaseModel):
    q: str
    ticker: str | None = None
    source_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    limit: Annotated[int, Field(ge=1, le=50)] = 10

    @field_validator("q")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("q must not be empty")
        return normalized

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        return normalized or None

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if normalized not in ALLOWED_SOURCE_TYPES:
            raise ValueError("source_type is not supported")
        return normalized

    @model_validator(mode="after")
    def validate_date_range(self) -> SearchParams:
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be before or equal to end_date")
        return self
