"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-09 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("exchange", sa.String(length=64), nullable=True),
        sa.Column("sector", sa.String(length=128), nullable=True),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_companies")),
        sa.UniqueConstraint("ticker", name=op.f("uq_companies_ticker")),
    )
    op.create_index(op.f("ix_companies_ticker"), "companies", ["ticker"], unique=False)

    op.create_table(
        "asset_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("high", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("low", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("close", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("adjusted_close", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asset_prices")),
        sa.UniqueConstraint("ticker", "date", name="uq_asset_prices_ticker_date"),
    )
    op.create_index(op.f("ix_asset_prices_date"), "asset_prices", ["date"], unique=False)
    op.create_index(op.f("ix_asset_prices_ticker"), "asset_prices", ["ticker"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "source_type in ('news', 'filing', 'transcript', 'analyst_note', 'synthetic')",
            name=op.f("ck_documents_document_source_type"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        sa.UniqueConstraint(
            "source_type",
            "ticker",
            "source_name",
            "content_hash",
            name="uq_documents_source_ticker_source_name_content_hash",
        ),
    )
    op.create_index(op.f("ix_documents_published_at"), "documents", ["published_at"], unique=False)
    op.create_index(op.f("ix_documents_ticker"), "documents", ["ticker"], unique=False)
    op.create_index(
        "ix_documents_ticker_published_at",
        "documents",
        ["ticker", "published_at"],
        unique=False,
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("sentiment", sa.String(length=32), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    op.create_index(op.f("ix_events_event_date"), "events", ["event_date"], unique=False)
    op.create_index(op.f("ix_events_event_type"), "events", ["event_type"], unique=False)
    op.create_index(op.f("ix_events_ticker"), "events", ["ticker"], unique=False)

    op.create_table(
        "narratives",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("sector", sa.String(length=128), nullable=True),
        sa.Column("canonical_keywords", sa.JSON(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_narratives")),
        sa.UniqueConstraint("name", name=op.f("uq_narratives_name")),
    )
    op.create_index(op.f("ix_narratives_name"), "narratives", ["name"], unique=False)
    op.create_index(op.f("ix_narratives_sector"), "narratives", ["sector"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("bm25_text", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], name=op.f("fk_document_chunks_document_id_documents")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_chunks")),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_chunk"),
        sa.UniqueConstraint("id", "document_id", name="uq_document_chunks_id_document"),
    )

    op.create_table(
        "narrative_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("narrative_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=True),
        sa.Column("relevance_score", sa.Numeric(precision=8, scale=6), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id", "document_id"],
            ["document_chunks.id", "document_chunks.document_id"],
            name="fk_narrative_evidence_chunk_document_consistency",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_narrative_evidence_document_id_documents"),
        ),
        sa.ForeignKeyConstraint(
            ["narrative_id"],
            ["narratives.id"],
            name=op.f("fk_narrative_evidence_narrative_id_narratives"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_narrative_evidence")),
    )

    op.create_table(
        "narrative_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("narrative_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("score", sa.Numeric(precision=8, scale=6), nullable=False),
        sa.Column("score_components", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["narrative_id"],
            ["narratives.id"],
            name=op.f("fk_narrative_scores_narrative_id_narratives"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_narrative_scores")),
        sa.UniqueConstraint(
            "ticker", "narrative_id", "date", name="uq_narrative_scores_ticker_narrative_date"
        ),
    )
    op.create_index(op.f("ix_narrative_scores_date"), "narrative_scores", ["date"], unique=False)
    op.create_index(
        op.f("ix_narrative_scores_ticker"), "narrative_scores", ["ticker"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_narrative_scores_ticker"), table_name="narrative_scores")
    op.drop_index(op.f("ix_narrative_scores_date"), table_name="narrative_scores")
    op.drop_table("narrative_scores")
    op.drop_table("narrative_evidence")
    op.drop_table("document_chunks")
    op.drop_index(op.f("ix_narratives_sector"), table_name="narratives")
    op.drop_index(op.f("ix_narratives_name"), table_name="narratives")
    op.drop_table("narratives")
    op.drop_index(op.f("ix_events_ticker"), table_name="events")
    op.drop_index(op.f("ix_events_event_type"), table_name="events")
    op.drop_index(op.f("ix_events_event_date"), table_name="events")
    op.drop_table("events")
    op.drop_index(op.f("ix_documents_ticker"), table_name="documents")
    op.drop_index(op.f("ix_documents_published_at"), table_name="documents")
    op.drop_index("ix_documents_ticker_published_at", table_name="documents")
    op.drop_table("documents")
    op.drop_index(op.f("ix_asset_prices_ticker"), table_name="asset_prices")
    op.drop_index(op.f("ix_asset_prices_date"), table_name="asset_prices")
    op.drop_table("asset_prices")
    op.drop_index(op.f("ix_companies_ticker"), table_name="companies")
    op.drop_table("companies")
