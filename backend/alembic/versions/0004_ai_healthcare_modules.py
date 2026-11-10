"""Add translation, extraction, and AI processing audit tables."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004_ai_healthcare_modules"
down_revision = "0003_align_timestamp_nullability"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_translations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("medical_documents.id"), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source_language", sa.String(10), nullable=False),
        sa.Column("target_language", sa.String(10), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("translated_text", sa.Text(), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_document_translations_document_target",
        "document_translations",
        ["document_id", "target_language"],
    )
    op.create_table(
        "extracted_medical_entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("medical_documents.id"), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("value", sa.String(200), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(20), nullable=False, server_default="low"),
        sa.Column("review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_extracted_entities_document", "extracted_medical_entities", ["document_id"])
    op.create_table(
        "ai_processing_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("operation", sa.String(40), nullable=False),
        sa.Column("input_language", sa.String(10), nullable=True),
        sa.Column("output_language", sa.String(10), nullable=True),
        sa.Column("provider", sa.String(40), nullable=False, server_default="local"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("ai_processing_logs")
    op.drop_index("ix_extracted_entities_document", table_name="extracted_medical_entities")
    op.drop_table("extracted_medical_entities")
    op.drop_index("ix_document_translations_document_target", table_name="document_translations")
    op.drop_table("document_translations")
