"""Add healthcare profiles, records, content, and private storage metadata."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_healthcare_records"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("patient_profiles", sa.Column("gender", sa.String(30), nullable=True))
    op.add_column("patient_profiles", sa.Column("address", sa.String(300), nullable=True))
    op.add_column("healthcare_worker_profiles", sa.Column("designation", sa.String(160), nullable=True))
    op.add_column("healthcare_worker_profiles", sa.Column("address", sa.String(300), nullable=True))
    op.add_column("healthcare_worker_profiles", sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.bulk_insert(
        sa.table("language_preferences", sa.column("code", sa.String), sa.column("name", sa.String)),
        [
            {"code": "bn", "name": "Bengali"},
            {"code": "ta", "name": "Tamil"},
            {"code": "te", "name": "Telugu"},
        ],
    )
    op.create_table(
        "patient_access_grants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("worker_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_patient_access_worker_patient", "patient_access_grants", ["worker_id", "patient_id"])
    op.create_table(
        "medical_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("document_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False, unique=True),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_medical_documents_patient_date", "medical_documents", ["patient_id", "created_at"])
    op.create_table(
        "prescriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("healthcare_worker_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("medication_name", sa.String(200), nullable=False),
        sa.Column("dosage", sa.String(120), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("prescription_date", sa.Date(), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("medical_documents.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_prescriptions_patient_date", "prescriptions", ["patient_id", "prescription_date"])
    op.create_table(
        "medical_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("medical_documents.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("report_type", sa.String(100), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_medical_reports_patient_date", "medical_reports", ["patient_id", "report_date"])
    op.create_table(
        "discharge_summaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("medical_documents.id"), nullable=False),
        sa.Column("discharge_date", sa.Date(), nullable=False),
        sa.Column("facility_name", sa.String(160), nullable=True),
    )
    op.create_table(
        "healthcare_contents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("language_code", sa.String(10), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_healthcare_contents_language_category", "healthcare_contents", ["language_code", "category"])


def downgrade() -> None:
    op.drop_index("ix_healthcare_contents_language_category", table_name="healthcare_contents")
    op.drop_table("healthcare_contents")
    op.drop_table("discharge_summaries")
    op.drop_index("ix_medical_reports_patient_date", table_name="medical_reports")
    op.drop_table("medical_reports")
    op.drop_index("ix_prescriptions_patient_date", table_name="prescriptions")
    op.drop_table("prescriptions")
    op.drop_index("ix_medical_documents_patient_date", table_name="medical_documents")
    op.drop_table("medical_documents")
    op.drop_index("ix_patient_access_worker_patient", table_name="patient_access_grants")
    op.drop_table("patient_access_grants")
    op.drop_column("healthcare_worker_profiles", "is_approved")
    op.drop_column("healthcare_worker_profiles", "address")
    op.drop_column("healthcare_worker_profiles", "designation")
    op.drop_column("patient_profiles", "address")
    op.drop_column("patient_profiles", "gender")
