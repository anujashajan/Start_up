from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models

router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])


@router.get("")
def list_anomalies(db: Session = Depends(get_db), status: str | None = None):
    q = db.query(models.Anomaly).order_by(models.Anomaly.timestamp.desc())
    if status:
        q = q.filter(models.Anomaly.status == status)
    anomalies = q.limit(50).all()
    out = []
    for a in anomalies:
        machine = db.query(models.Machine).get(a.machine_id)
        rc = db.query(models.RootCause).filter_by(anomaly_id=a.id).first()
        out.append({
            "id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "machine": machine.name if machine else None,
            "line": machine.line if machine else None,
            "metric": a.metric,
            "value": a.value,
            "expected_low": a.expected_low,
            "expected_high": a.expected_high,
            "severity": a.severity,
            "status": a.status,
            "root_cause": rc.cause if rc else None,
            "root_cause_confidence": rc.confidence if rc else None,
        })
    return out
