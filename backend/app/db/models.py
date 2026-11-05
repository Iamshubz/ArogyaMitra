from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
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

    user: Mapped[User] = relationship(back_populates="patient_profile")


class HealthcareWorkerProfile(Base):
    __tablename__ = "healthcare_worker_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    facility_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    specialization: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)

    user: Mapped[User] = relationship(back_populates="worker_profile")
