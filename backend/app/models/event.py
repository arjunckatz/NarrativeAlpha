from datetime import date
from decimal import Decimal

from sqlalchemy import JSON, Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base, TimestampMixin


class Event(TimestampMixin, Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    event_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
