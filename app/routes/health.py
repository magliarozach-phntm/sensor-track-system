from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.database import get_db


router = APIRouter(
    tags=["health"],
)


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "sensor-track-api",
    }


@router.get("/ready")
def readiness(
    db: Session = Depends(get_db),
):
    try:
        db.execute(
            text("SELECT 1")
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )

    return {
        "status": "ready",
        "database": "reachable",
    }