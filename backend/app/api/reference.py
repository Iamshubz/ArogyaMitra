from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.db.models import LanguagePreference

router = APIRouter(prefix="/reference", tags=["reference data"])


@router.get("/languages")
def list_languages(db: Session = Depends(get_db)) -> list[dict[str, str]]:
    return [
        {"code": language.code, "name": language.name}
        for language in db.scalars(select(LanguagePreference).order_by(LanguagePreference.id)).all()
    ]
