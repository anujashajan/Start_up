from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def list_audit(db: Session = Depends(get_db)):
    rows = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).limit(80).all()
    return [{
        "id": r.id,
        "timestamp": r.timestamp.isoformat(),
        "actor": r.actor,
        "event_type": r.event_type,
        "entity_type": r.entity_type,
        "entity_id": r.entity_id,
        "details": r.details,
    } for r in rows]
