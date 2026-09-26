import datetime as dt
import json
import random

from sqlalchemy.orm import Session
from . import models
from .ml import anomaly as anomaly_ml
from .ml import root_cause as root_cause_ml
from .ml import recommend as recommend_ml
from .seed import CUSTOMERS

BASELINES = {
    "vibration_mm_s": 2.0,
    "temperature_c": 55.0,
    "cycle_time_s": 24.0,
    "pressure_bar": 6.5,
}

# fraction of ticks (per machine) that inject an anomalous spike
ANOMALY_CHANCE = 0.018


def log_audit(db: Session, actor: str, event_type: str, entity_type: str, entity_id, details: dict):
    db.add(models.AuditLog(
        actor=actor,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        details=json.dumps(details),
    ))


def _generate_reading(machine: models.Machine, spike: bool):
    reading = {}
    for metric, baseline in BASELINES.items():
        noise = random.gauss(0, baseline * 0.04)
        value = baseline + noise
        if spike and metric == random.choice(list(BASELINES.keys())):
            direction = random.choice([1, -1])
            value += direction * baseline * random.uniform(0.5, 1.1)
        reading[metric] = round(max(0.0, value), 2)
    return reading


def tick_sensors(db: Session):
    machines = db.query(models.Machine).all()
    for machine in machines:
        spike = random.random() < ANOMALY_CHANCE
        values = _generate_reading(machine, spike)
        db.add(models.SensorReading(
            machine_id=machine.id,
            vibration_mm_s=values["vibration_mm_s"],
            temperature_c=values["temperature_c"],
            cycle_time_s=values["cycle_time_s"],
            pressure_bar=values["pressure_bar"],
        ))
    db.commit()


def tick_production(db: Session):
    for part in db.query(models.Part).all():
        produced = random.randint(40, 90)
        rejected = int(produced * random.uniform(0.0, 0.06))
        db.add(models.ProductionRecord(
            line=part.line, part_id=part.id,
            units_produced=produced, units_rejected=rejected,
        ))
        inv = db.query(models.Inventory).filter_by(part_id=part.id).first()
        if inv:
            inv.qty_on_hand = max(0, inv.qty_on_hand + produced - random.randint(30, 70))
    db.commit()


def tick_orders(db: Session):
    if random.random() < 0.35:
        part = random.choice(db.query(models.Part).all())
        db.add(models.Order(
            customer=random.choice(CUSTOMERS),
            part_id=part.id,
            qty=random.randint(200, 1500),
            due_date=dt.datetime.utcnow() + dt.timedelta(days=random.randint(5, 30)),
        ))
        db.commit()


def detect_anomalies_and_pipeline(db: Session):
    machines = db.query(models.Machine).all()
    for machine in machines:
        recent = (
            db.query(models.SensorReading)
            .filter(models.SensorReading.machine_id == machine.id)
            .order_by(models.SensorReading.timestamp.desc())
            .limit(30)
            .all()
        )
        if len(recent) < 6:
            continue
        latest = recent[0]
        history = list(reversed(recent[1:]))

        machine_has_open = (
            db.query(models.Anomaly)
            .filter_by(machine_id=machine.id, status="open")
            .first()
        )
        if machine_has_open:
            continue

        for metric in BASELINES.keys():
            hist_values = [getattr(r, metric) for r in history]
            latest_value = getattr(latest, metric)
            severity = anomaly_ml.classify_severity(metric, latest_value)
            flagged, z = anomaly_ml.zscore_flag(hist_values, latest_value)

            if severity and flagged:
                low, high = anomaly_ml.NORMAL_RANGES[metric]

                already_open = (
                    db.query(models.Anomaly)
                    .filter_by(machine_id=machine.id, metric=metric, status="open")
                    .first()
                )
                if already_open:
                    continue

                anomaly = models.Anomaly(
                    machine_id=machine.id, metric=metric, value=latest_value,
                    expected_low=low, expected_high=high, severity=severity,
                )
                db.add(anomaly)
                db.commit()
                db.refresh(anomaly)

                log_audit(db, "AI_SYSTEM", "anomaly_detected", "anomaly", anomaly.id, {
                    "machine": machine.name, "metric": metric, "value": latest_value,
                    "severity": severity, "z_score": round(z, 2),
                })

                cause, confidence, evidence = root_cause_ml.analyze(machine, metric, latest_value, low, high)
                rc = models.RootCause(
                    anomaly_id=anomaly.id, cause=cause, confidence=confidence, evidence=evidence,
                )
                db.add(rc)
                db.commit()
                db.refresh(rc)

                log_audit(db, "AI_SYSTEM", "root_cause_identified", "root_cause", rc.id, {
                    "anomaly_id": anomaly.id, "cause": cause, "confidence": confidence,
                })

                title, action_type, cost, downtime, rationale = recommend_ml.recommend_for_cause(cause, severity)
                rec = models.Recommendation(
                    anomaly_id=anomaly.id, root_cause_id=rc.id, title=title,
                    rationale=rationale, action_type=action_type,
                    est_cost_impact_inr=cost, est_downtime_avoided_hours=downtime,
                    confidence=confidence,
                )
                db.add(rec)
                db.commit()
                db.refresh(rec)

                log_audit(db, "AI_SYSTEM", "recommendation_generated", "recommendation", rec.id, {
                    "title": title, "est_cost_impact_inr": cost,
                    "est_downtime_avoided_hours": downtime,
                })
                break
    db.commit()


def run_tick(db: Session):
    tick_sensors(db)
    tick_production(db)
    tick_orders(db)
    detect_anomalies_and_pipeline(db)
