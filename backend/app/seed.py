import datetime as dt
import random
from sqlalchemy.orm import Session
from . import models


MACHINES = [
    ("CNC-101", "CNC Machining Center", "Brake Components Line"),
    ("CNC-102", "CNC Machining Center", "Brake Components Line"),
    ("PRS-201", "Hydraulic Press", "Suspension Line"),
    ("PRS-202", "Hydraulic Press", "Suspension Line"),
    ("WLD-301", "Robotic Welding Cell", "Transmission Parts Line"),
    ("WLD-302", "Robotic Welding Cell", "Transmission Parts Line"),
    ("PNT-401", "Paint Booth", "Suspension Line"),
    ("ASM-501", "Assembly Line", "Brake Components Line"),
]

PARTS = [
    ("BRK-4401", "Brake Caliper Bracket", "Brake Components Line", 420.0),
    ("BRK-4402", "Brake Disc Rotor", "Brake Components Line", 610.0),
    ("SUS-3301", "Lower Control Arm", "Suspension Line", 780.0),
    ("SUS-3302", "Coil Spring Seat", "Suspension Line", 250.0),
    ("TRN-2201", "Gearbox Housing", "Transmission Parts Line", 1450.0),
    ("TRN-2202", "Clutch Plate Assembly", "Transmission Parts Line", 890.0),
]

CUSTOMERS = ["Tata Motors", "Mahindra & Mahindra", "Maruti Suzuki", "Ashok Leyland", "Bajaj Auto"]


def seed(db: Session):
    if db.query(models.Machine).count() > 0:
        return

    for name, mtype, line in MACHINES:
        db.add(models.Machine(
            name=name, type=mtype, line=line,
            last_maintenance=dt.datetime.utcnow() - dt.timedelta(days=20),
            maintenance_interval_hours=30 * 24,
        ))

    for pn, name, line, cost in PARTS:
        db.add(models.Part(part_number=pn, name=name, line=line, unit_cost=cost))

    db.commit()

    for part in db.query(models.Part).all():
        db.add(models.Inventory(
            part_id=part.id,
            qty_on_hand=1200,
            reorder_point=400,
        ))
    db.commit()


def backfill_history(db: Session):
    """Seed a short synthetic history so charts/forecasts aren't empty on first load."""
    from . import simulator  # local import: simulator imports seed, avoid circular import at module load

    now = dt.datetime.utcnow()
    machines = db.query(models.Machine).all()
    parts = db.query(models.Part).all()

    for i in range(30, 0, -1):
        ts = now - dt.timedelta(minutes=i * 5)
        for m in machines:
            values = simulator._generate_reading(m, spike=False)
            db.add(models.SensorReading(
                machine_id=m.id, timestamp=ts,
                vibration_mm_s=values["vibration_mm_s"],
                temperature_c=values["temperature_c"],
                cycle_time_s=values["cycle_time_s"],
                pressure_bar=values["pressure_bar"],
            ))
        for p in parts:
            produced = random.randint(40, 90)
            rejected = int(produced * random.uniform(0.0, 0.05))
            db.add(models.ProductionRecord(
                timestamp=ts, line=p.line, part_id=p.id,
                units_produced=produced, units_rejected=rejected,
            ))
    db.commit()


def init_demo_state(db: Session):
    """Idempotent full bootstrap: seed static data, backfill history, log pipeline start."""
    from . import simulator

    seed(db)
    if db.query(models.SensorReading).count() == 0:
        backfill_history(db)
    if db.query(models.AuditLog).count() == 0:
        simulator.log_audit(db, "SYSTEM", "pipeline_initialized", "system", None, {
            "message": "Factory Intelligence Copilot pipeline started",
        })
        db.commit()
