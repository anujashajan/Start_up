import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..actions import approve_recommendation, reject_recommendation, RecommendationError

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class DecisionPayload(BaseModel):
    decided_by: str = "Plant Operations Manager"


@router.get("")
def list_recommendations(db: Session = Depends(get_db), status: str | None = None):
    q = db.query(models.Recommendation).order_by(models.Recommendation.timestamp.desc())
    if status:
        q = q.filter(models.Recommendation.status == status)
    recs = q.limit(50).all()
    out = []
    for r in recs:
        anomaly = db.query(models.Anomaly).get(r.anomaly_id) if r.anomaly_id else None
        machine = db.query(models.Machine).get(anomaly.machine_id) if anomaly else None
        rc = db.query(models.RootCause).get(r.root_cause_id) if r.root_cause_id else None
        out.append({
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "title": r.title,
            "rationale": r.rationale,
            "action_type": r.action_type,
            "est_cost_impact_inr": r.est_cost_impact_inr,
            "est_downtime_avoided_hours": r.est_downtime_avoided_hours,
            "confidence": r.confidence,
            "status": r.status,
            "decided_by": r.decided_by,
            "machine": machine.name if machine else None,
            "line": machine.line if machine else None,
            "severity": anomaly.severity if anomaly else None,
            "root_cause": rc.cause if rc else None,
            "evidence": json.loads(rc.evidence) if rc else None,
        })
    return out


@router.post("/{rec_id}/approve")
def approve(rec_id: int, payload: DecisionPayload, db: Session = Depends(get_db)):
    try:
        rec = approve_recommendation(db, rec_id, payload.decided_by)
    except RecommendationError as e:
        raise HTTPException(400, str(e))
    return {"status": rec.status, "id": rec.id}


@router.post("/{rec_id}/reject")
def reject(rec_id: int, payload: DecisionPayload, db: Session = Depends(get_db)):
    try:
        rec = reject_recommendation(db, rec_id, payload.decided_by)
    except RecommendationError as e:
        raise HTTPException(400, str(e))
    return {"status": rec.status, "id": rec.id}
