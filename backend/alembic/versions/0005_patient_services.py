"""Add medication reminders, bookmarks, emergency contacts, and facilities."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0005_patient_services"
down_revision = "0004_ai_healthcare_modules"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "medication_reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("medication_name", sa.String(200), nullable=False),
        sa.Column("dosage", sa.String(120), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("delivery_status", sa.String(20), nullable=False, server_default="not_sent"),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_medication_reminders_patient_schedule", "medication_reminders", ["patient_id", "scheduled_at"])
    op.create_table(
        "bookmarks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content_id", sa.Integer(), sa.ForeignKey("healthcare_contents.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_bookmarks_user_content", "bookmarks", ["user_id", "content_id"], unique=True)
    op.create_table(
        "emergency_contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("phone_number", sa.String(30), nullable=False),
        sa.Column("region", sa.String(120), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "healthcare_facilities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("facility_type", sa.String(80), nullable=False),
        sa.Column("phone_number", sa.String(30), nullable=True),
        sa.Column("address", sa.String(300), nullable=False),
        sa.Column("region", sa.String(120), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_healthcare_facilities_region", "healthcare_facilities", ["region"])
    op.bulk_insert(
        sa.table(
            "emergency_contacts",
            sa.column("name", sa.String),
            sa.column("phone_number", sa.String),
            sa.column("region", sa.String),
            sa.column("is_verified", sa.Boolean),
        ),
        [{"name": "India emergency services", "phone_number": "112", "region": "India", "is_verified": True}],
    )


def downgrade() -> None:
    op.drop_index("ix_healthcare_facilities_region", table_name="healthcare_facilities")
    op.drop_table("healthcare_facilities")
    op.drop_table("emergency_contacts")
    op.drop_index("ix_bookmarks_user_content", table_name="bookmarks")
    op.drop_table("bookmarks")
    op.drop_index("ix_medication_reminders_patient_schedule", table_name="medication_reminders")
    op.drop_table("medication_reminders")
