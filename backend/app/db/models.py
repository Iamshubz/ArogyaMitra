from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Boolean, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class LanguagePreference(Base):
    __tablename__ = "language_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))

    users: Mapped[list["User"]] = relationship(back_populates="preferred_language")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    role: Mapped[str] = mapped_column(String(30), default="patient")
    preferred_language_id: Mapped[int] = mapped_column(
        ForeignKey("language_preferences.id"), default=1
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    preferred_language: Mapped[LanguagePreference] = relationship(back_populates="users")
    patient_profile: Mapped[Optional["PatientProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    worker_profile: Mapped[Optional["HealthcareWorkerProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    user: Mapped[User] = relationship(back_populates="patient_profile")


class HealthcareWorkerProfile(Base):
    __tablename__ = "healthcare_worker_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    facility_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    specialization: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship(back_populates="worker_profile")


class PatientAccessGrant(Base):
    __tablename__ = "patient_access_grants"
    __table_args__ = (Index("ix_patient_access_worker_patient", "worker_id", "patient_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MedicalDocument(Base):
    __tablename__ = "medical_documents"
    __table_args__ = (Index("ix_medical_documents_patient_date", "patient_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    document_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Prescription(Base):
    __tablename__ = "prescriptions"
    __table_args__ = (Index("ix_prescriptions_patient_date", "patient_id", "prescription_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    healthcare_worker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    medication_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[str] = mapped_column(String(120), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    prescription_date: Mapped[date] = mapped_column(Date, nullable=False)
    document_id: Mapped[Optional[int]] = mapped_column(ForeignKey("medical_documents.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MedicalReport(Base):
    __tablename__ = "medical_reports"
    __table_args__ = (Index("ix_medical_reports_patient_date", "patient_id", "report_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("medical_documents.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DischargeSummary(Base):
    __tablename__ = "discharge_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("medical_documents.id"), nullable=False)
    discharge_date: Mapped[date] = mapped_column(Date, nullable=False)
    facility_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)


class HealthcareContent(Base):
    __tablename__ = "healthcare_contents"
    __table_args__ = (Index("ix_healthcare_contents_language_category", "language_code", "category"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    publication_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
