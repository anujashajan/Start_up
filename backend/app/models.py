import datetime as dt
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship
from .database import Base


def now():
    return dt.datetime.utcnow()


class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    line = Column(String, nullable=False)
    status = Column(String, default="running")
    last_maintenance = Column(DateTime, default=now)
    maintenance_interval_hours = Column(Float, default=720)

    readings = relationship("SensorReading", back_populates="machine")


class Part(Base):
    __tablename__ = "parts"
    id = Column(Integer, primary_key=True)
    part_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    line = Column(String, nullable=False)
    unit_cost = Column(Float, default=250.0)


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    timestamp = Column(DateTime, default=now, index=True)
    vibration_mm_s = Column(Float)
    temperature_c = Column(Float)
    cycle_time_s = Column(Float)
    pressure_bar = Column(Float)

    machine = relationship("Machine", back_populates="readings")


class ProductionRecord(Base):
    __tablename__ = "production_records"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=now, index=True)
    line = Column(String)
    part_id = Column(Integer, ForeignKey("parts.id"))
    units_produced = Column(Integer)
    units_rejected = Column(Integer)


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey("parts.id"), unique=True)
    qty_on_hand = Column(Integer)
    reorder_point = Column(Integer)
    warehouse = Column(String, default="Main Warehouse - Pune")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=now, index=True)
    customer = Column(String)
    part_id = Column(Integer, ForeignKey("parts.id"))
    qty = Column(Integer)
    due_date = Column(DateTime)
    status = Column(String, default="open")


class Forecast(Base):
    __tablename__ = "forecasts"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=now, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"))
    horizon_day = Column(Integer)
    forecast_qty = Column(Float)
    model = Column(String, default="Exponential Smoothing")


class Anomaly(Base):
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=now, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    metric = Column(String)
    value = Column(Float)
    expected_low = Column(Float)
    expected_high = Column(Float)
    severity = Column(String)
    status = Column(String, default="open")

    machine = relationship("Machine")


class RootCause(Base):
    __tablename__ = "root_causes"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=now, index=True)
    anomaly_id = Column(Integer, ForeignKey("anomalies.id"))
    cause = Column(String)
    confidence = Column(Float)
    evidence = Column(Text)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=now, index=True)
    anomaly_id = Column(Integer, ForeignKey("anomalies.id"), nullable=True)
    root_cause_id = Column(Integer, ForeignKey("root_causes.id"), nullable=True)
    title = Column(String)
    rationale = Column(Text)
    action_type = Column(String)
    est_cost_impact_inr = Column(Float)
    est_downtime_avoided_hours = Column(Float)
    confidence = Column(Float)
    status = Column(String, default="pending")  # pending / approved / rejected / executed
    decided_by = Column(String, nullable=True)
    decided_at = Column(DateTime, nullable=True)


class ActionLog(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=now, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"))
    result = Column(String)
    executor = Column(String, default="AI_AUTOMATION")


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=now, index=True)
    actor = Column(String)
    event_type = Column(String)
    entity_type = Column(String)
    entity_id = Column(Integer, nullable=True)
    details = Column(Text)
