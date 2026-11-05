from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


Role = Literal["patient", "healthcare_worker", "admin"]


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone_number: Optional[str] = Field(default=None, max_length=30)
    age: Optional[int] = Field(default=None, ge=0, le=130)
    preferred_language: str = Field(default="en", min_length=2, max_length=10)
    role: Literal["patient", "healthcare_worker"] = "patient"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    phone_number: Optional[str]
    role: str
    is_active: bool
    preferred_language: LanguageResponse
    age: Optional[int] = None
    facility_name: Optional[str] = None
    specialization: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone_number: Optional[str] = Field(default=None, max_length=30)
    preferred_language: str = Field(min_length=2, max_length=10)
    age: Optional[int] = Field(default=None, ge=0, le=130)
    facility_name: Optional[str] = Field(default=None, max_length=160)
    specialization: Optional[str] = Field(default=None, max_length=160)
