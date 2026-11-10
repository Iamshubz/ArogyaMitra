from __future__ import annotations

"""Align audit timestamps with the non-nullable ORM models."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_align_timestamp_nullability"
down_revision = "0002_healthcare_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table, column in (
        ("users", "created_at"),
        ("users", "updated_at"),
        ("patient_access_grants", "created_at"),
        ("medical_documents", "created_at"),
        ("prescriptions", "created_at"),
        ("healthcare_contents", "created_at"),
        ("healthcare_contents", "updated_at"),
    ):
        op.alter_column(
            table,
            column,
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
        )


def downgrade() -> None:
    for table, column in (
        ("healthcare_contents", "updated_at"),
        ("healthcare_contents", "created_at"),
        ("prescriptions", "created_at"),
        ("medical_documents", "created_at"),
        ("patient_access_grants", "created_at"),
        ("users", "updated_at"),
        ("users", "created_at"),
    ):
        op.alter_column(
            table,
            column,
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
        )
