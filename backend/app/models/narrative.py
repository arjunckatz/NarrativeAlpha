from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.narrative_evidence import NarrativeEvidence
    from app.models.narrative_score import NarrativeScore


class Narrative(TimestampMixin, Base):
    __tablename__ = "narratives"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sector: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    canonical_keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    evidence: Mapped[list[NarrativeEvidence]] = relationship(
        back_populates="narrative",
        cascade="all, delete-orphan",
    )
    scores: Mapped[list[NarrativeScore]] = relationship(
        back_populates="narrative",
        cascade="all, delete-orphan",
    )
