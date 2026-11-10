from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.records import router as records_router, content_router
from app.api.admin import router as admin_router
from app.api.reference import router as reference_router
from app.api.ai_healthcare import router as ai_healthcare_router
from app.api.patient_services import (
    education_router,
    emergency_router,
    reminder_router,
    voice_router,
)
from app.api.worker_admin import admin_router as worker_admin_router, worker_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Healthcare in Your Language, Care for Everyone.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(records_router, prefix="/api/v1")
app.include_router(content_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(reference_router, prefix="/api/v1")
app.include_router(ai_healthcare_router, prefix="/api/v1")
app.include_router(reminder_router, prefix="/api/v1")
app.include_router(education_router, prefix="/api/v1")
app.include_router(emergency_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")
app.include_router(worker_router, prefix="/api/v1")
app.include_router(worker_admin_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "ArogyaMitra API is running"}
