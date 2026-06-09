from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.narrative import Narrative


class NarrativeScore(Base):
    __tablename__ = "narrative_scores"
    __table_args__ = (
        UniqueConstraint(
            "ticker", "narrative_id", "date", name="uq_narrative_scores_ticker_narrative_date"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    narrative_id: Mapped[int] = mapped_column(ForeignKey("narratives.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    score_components: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    narrative: Mapped[Narrative] = relationship(back_populates="scores")
