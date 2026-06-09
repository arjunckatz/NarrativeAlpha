from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.document_chunk import DocumentChunk
    from app.models.narrative import Narrative


class NarrativeEvidence(TimestampMixin, Base):
    __tablename__ = "narrative_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    narrative_id: Mapped[int] = mapped_column(ForeignKey("narratives.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    chunk_id: Mapped[int | None] = mapped_column(ForeignKey("document_chunks.id"), nullable=True)
    relevance_score: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)

    narrative: Mapped[Narrative] = relationship(back_populates="evidence")
    document: Mapped[Document] = relationship()
    chunk: Mapped[DocumentChunk | None] = relationship()
