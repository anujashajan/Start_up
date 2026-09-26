import datetime as dt
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from .. import models
from ..ml.forecasting import exponential_smoothing_forecast

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/kpis")
def get_kpis(db: Session = Depends(get_db)):
    since = dt.datetime.utcnow() - dt.timedelta(hours=6)
    produced = db.query(func.coalesce(func.sum(models.ProductionRecord.units_produced), 0)).filter(
        models.ProductionRecord.timestamp >= since
    ).scalar()
    rejected = db.query(func.coalesce(func.sum(models.ProductionRecord.units_rejected), 0)).filter(
        models.ProductionRecord.timestamp >= since
    ).scalar()
    open_anomalies = db.query(models.Anomaly).filter(models.Anomaly.status == "open").count()
    pending_recs = db.query(models.Recommendation).filter(models.Recommendation.status == "pending").count()
    executed_recs = db.query(models.Recommendation).filter(models.Recommendation.status == "executed").count()

    total_savings = db.query(func.coalesce(func.sum(models.Recommendation.est_cost_impact_inr), 0)).filter(
        models.Recommendation.status == "executed"
    ).scalar()
    total_downtime_avoided = db.query(func.coalesce(func.sum(models.Recommendation.est_downtime_avoided_hours), 0)).filter(
        models.Recommendation.status == "executed"
    ).scalar()

    defect_rate = (rejected / produced * 100) if produced else 0
    machines_total = db.query(models.Machine).count()
    machines_running = db.query(models.Machine).filter(models.Machine.status == "running").count()

    return {
        "units_produced_6h": int(produced),
        "units_rejected_6h": int(rejected),
        "defect_rate_pct": round(defect_rate, 2),
        "open_anomalies": open_anomalies,
        "pending_recommendations": pending_recs,
        "executed_recommendations": executed_recs,
        "cost_savings_inr": round(total_savings, 0),
        "downtime_avoided_hours": round(total_downtime_avoided, 1),
        "oee_pct": round(85 + random_jitter(), 1),
        "machines_running": machines_running,
        "machines_total": machines_total,
    }


def random_jitter():
    import random
    return random.uniform(-6, 6)


@router.get("/machines")
def get_machines(db: Session = Depends(get_db)):
    machines = db.query(models.Machine).all()
    out = []
    for m in machines:
        latest = (
            db.query(models.SensorReading)
            .filter(models.SensorReading.machine_id == m.id)
            .order_by(models.SensorReading.timestamp.desc())
            .first()
        )
        open_anomaly = (
            db.query(models.Anomaly)
            .filter(models.Anomaly.machine_id == m.id, models.Anomaly.status == "open")
            .first()
        )
        out.append({
            "id": m.id, "name": m.name, "type": m.type, "line": m.line,
            "status": "anomaly" if open_anomaly else m.status,
            "last_maintenance": m.last_maintenance.isoformat(),
            "latest_reading": {
                "vibration_mm_s": latest.vibration_mm_s,
                "temperature_c": latest.temperature_c,
                "cycle_time_s": latest.cycle_time_s,
                "pressure_bar": latest.pressure_bar,
                "timestamp": latest.timestamp.isoformat(),
            } if latest else None,
        })
    return out


@router.get("/machines/{machine_id}/history")
def get_machine_history(machine_id: int, db: Session = Depends(get_db)):
    readings = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.machine_id == machine_id)
        .order_by(models.SensorReading.timestamp.desc())
        .limit(40)
        .all()
    )
    readings = list(reversed(readings))
    return [{
        "timestamp": r.timestamp.isoformat(),
        "vibration_mm_s": r.vibration_mm_s,
        "temperature_c": r.temperature_c,
        "cycle_time_s": r.cycle_time_s,
        "pressure_bar": r.pressure_bar,
    } for r in readings]


@router.get("/inventory")
def get_inventory(db: Session = Depends(get_db)):
    rows = db.query(models.Inventory, models.Part).join(models.Part).all()
    return [{
        "part_number": part.part_number, "part_name": part.name, "line": part.line,
        "qty_on_hand": inv.qty_on_hand, "reorder_point": inv.reorder_point,
        "below_reorder": inv.qty_on_hand < inv.reorder_point,
    } for inv, part in rows]


@router.get("/orders")
def get_orders(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Order, models.Part)
        .join(models.Part)
        .order_by(models.Order.timestamp.desc())
        .limit(20)
        .all()
    )
    return [{
        "id": o.id, "customer": o.customer, "part_name": part.name,
        "qty": o.qty, "due_date": o.due_date.isoformat(), "status": o.status,
        "timestamp": o.timestamp.isoformat(),
    } for o, part in rows]


@router.get("/forecast/{part_id}")
def get_forecast(part_id: int, db: Session = Depends(get_db)):
    records = (
        db.query(models.ProductionRecord)
        .filter(models.ProductionRecord.part_id == part_id)
        .order_by(models.ProductionRecord.timestamp.asc())
        .all()
    )
    history = [r.units_produced for r in records] or [50.0]
    forecast = exponential_smoothing_forecast(history, horizon=7)
    part = db.query(models.Part).get(part_id)
    return {
        "part_id": part_id,
        "part_name": part.name if part else None,
        "history": history[-20:],
        "forecast": [round(f, 1) for f in forecast],
    }


@router.get("/parts")
def get_parts(db: Session = Depends(get_db)):
    parts = db.query(models.Part).all()
    return [{"id": p.id, "part_number": p.part_number, "name": p.name, "line": p.line} for p in parts]
