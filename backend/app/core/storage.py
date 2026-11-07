from __future__ import annotations

import httpx

from app.core.config import settings


class StorageNotConfigured(RuntimeError):
    pass


def _storage_url(path: str) -> str:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise StorageNotConfigured("Private document storage is not configured")
    return f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{settings.storage_bucket}/{path}"


def upload_private(path: str, content: bytes, content_type: str) -> None:
    response = httpx.post(
        _storage_url(path),
        content=content,
        headers={
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "apikey": settings.supabase_service_role_key,
            "Content-Type": content_type,
            "x-upsert": "false",
        },
        timeout=30,
    )
    response.raise_for_status()


def download_private(path: str) -> httpx.Response:
    response = httpx.get(
        _storage_url(path),
        headers={
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "apikey": settings.supabase_service_role_key,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response
