import datetime as dt
from sqlalchemy.orm import Session

from . import models
from .simulator import log_audit


class RecommendationError(Exception):
    pass


def approve_recommendation(db: Session, rec_id: int, decided_by: str = "Plant Operations Manager"):
    rec = db.query(models.Recommendation).get(rec_id)
    if not rec:
        raise RecommendationError("Recommendation not found")
    if rec.status != "pending":
        raise RecommendationError(f"Recommendation already {rec.status}")

    rec.status = "executed"
    rec.decided_by = decided_by
    rec.decided_at = dt.datetime.utcnow()
    db.commit()

    log_audit(db, decided_by, "recommendation_approved", "recommendation", rec.id, {
        "title": rec.title,
    })

    db.add(models.ActionLog(
        recommendation_id=rec.id,
        result=f"Executed: {rec.title}",
        executor="AI_AUTOMATION",
    ))

    if rec.anomaly_id:
        anomaly = db.query(models.Anomaly).get(rec.anomaly_id)
        if anomaly:
            anomaly.status = "resolved"
            machine = db.query(models.Machine).get(anomaly.machine_id)
            if machine:
                if rec.action_type in ("predictive_maintenance", "maintenance"):
                    machine.last_maintenance = dt.datetime.utcnow()
                machine.status = "running"

    log_audit(db, "AI_AUTOMATION", "action_executed", "recommendation", rec.id, {
        "title": rec.title, "action_type": rec.action_type,
    })
    db.commit()
    return rec


def reject_recommendation(db: Session, rec_id: int, decided_by: str = "Plant Operations Manager"):
    rec = db.query(models.Recommendation).get(rec_id)
    if not rec:
        raise RecommendationError("Recommendation not found")
    if rec.status != "pending":
        raise RecommendationError(f"Recommendation already {rec.status}")

    rec.status = "rejected"
    rec.decided_by = decided_by
    rec.decided_at = dt.datetime.utcnow()
    db.commit()

    log_audit(db, decided_by, "recommendation_rejected", "recommendation", rec.id, {
        "title": rec.title,
    })

    if rec.anomaly_id:
        anomaly = db.query(models.Anomaly).get(rec.anomaly_id)
        if anomaly:
            anomaly.status = "dismissed"
    db.commit()
    return rec
