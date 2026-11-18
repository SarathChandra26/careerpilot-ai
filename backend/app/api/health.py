from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import get_db
from app.services.llm_service import llm_service
from app.config import settings

router = APIRouter(tags=["System Health"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = False
    try:
        db.execute(text("SELECT 1"))
        db_status = True
    except Exception:
        db_status = False

    llm_health = llm_service.check_health()

    return {
        "status": "healthy" if db_status else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database_connected": db_status,
        "llm_service": llm_health,
    }
