"""Factory Intelligence Copilot — Streamlit deployment.

Single-file dashboard for Streamlit Community Cloud. Reuses the same
SQLAlchemy models, simulator and ML pipeline as the FastAPI backend in
backend/app — this file is a presentation layer, not a re-implementation.
"""
import datetime as dt
import json
import os
import sys

import altair as alt
import pandas as pd
import streamlit as st
from apscheduler.schedulers.background import BackgroundScheduler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.database import Base, engine, SessionLocal  # noqa: E402
from app import models, simulator  # noqa: E402
from app.seed import init_demo_state  # noqa: E402
from app.ml.forecasting import exponential_smoothing_forecast  # noqa: E402
from app.actions import approve_recommendation, reject_recommendation, RecommendationError  # noqa: E402

st.set_page_config(
    page_title="Factory Intelligence Copilot",
    page_icon="🏭",
    layout="wide",
)

PIPELINE_STEPS = [
    "Operational Data", "AI Forecasting", "Anomaly Detection", "Root Cause",
    "Recommendation", "Human Approval", "Automated Action", "Audit Trail",
]

CHART_COLORS = {
    "vibration_mm_s": "#38bdf8",
    "temperature_c": "#fb923c",
    "cycle_time_s": "#a78bfa",
    "pressure_bar": "#34d399",
}
METRIC_LABELS = {
    "vibration_mm_s": "Vibration (mm/s)",
    "temperature_c": "Temperature (°C)",
    "cycle_time_s": "Cycle Time (s)",
    "pressure_bar": "Pressure (bar)",
}
SEVERITY_COLOR = {"critical": "#fb7185", "high": "#fbbf24", "medium": "#fde047"}


@st.cache_resource
def bootstrap():
    """Runs once per app process: create schema, seed demo data, start the live tick."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_demo_state(db)
    finally:
        db.close()

    def scheduled_tick():
        tick_db = SessionLocal()
        try:
            simulator.run_tick(tick_db)
        except Exception as e:
            print(f"[simulator tick error] {e}")
        finally:
            tick_db.close()

    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_tick, "interval", seconds=5, id="factory_tick", max_instances=1)
    scheduler.start()
    return scheduler


bootstrap()


def db_session():
    return SessionLocal()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🏭 Factory Intelligence Copilot")
st.caption("Industrial AI Decision & Automation Platform — POC · Auto-Components Manufacturing")
st.markdown(
    " → ".join(f"`{step}`" for step in PIPELINE_STEPS)
)
st.divider()


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
@st.fragment(run_every="3s")
def kpi_section():
    db = db_session()
    try:
        since = dt.datetime.utcnow() - dt.timedelta(hours=6)
        produced = db.query(models.ProductionRecord).filter(models.ProductionRecord.timestamp >= since).all()
        units_produced = sum(p.units_produced for p in produced)
        units_rejected = sum(p.units_rejected for p in produced)
        defect_rate = (units_rejected / units_produced * 100) if units_produced else 0.0

        open_anomalies = db.query(models.Anomaly).filter(models.Anomaly.status == "open").count()
        pending = db.query(models.Recommendation).filter(models.Recommendation.status == "pending").count()
        executed = db.query(models.Recommendation).filter(models.Recommendation.status == "executed").all()
        cost_savings = sum(r.est_cost_impact_inr for r in executed)
        downtime_avoided = sum(r.est_downtime_avoided_hours for r in executed)
        machines_total = db.query(models.Machine).count()
        machines_running = db.query(models.Machine).filter(models.Machine.status == "running").count()

        cols = st.columns(7)
        cols[0].metric("OEE", "85%")
        cols[1].metric("Machines Running", f"{machines_running}/{machines_total}")
        cols[2].metric("Units Produced (6h)", f"{units_produced:,}")
        cols[3].metric("Defect Rate", f"{defect_rate:.2f}%")
        cols[4].metric("Open Anomalies", open_anomalies)
        cols[5].metric("Pending Approvals", pending)
        cols[6].metric("Cost Impact Avoided", f"₹{cost_savings:,.0f}", f"{downtime_avoided:.1f}h downtime avoided")
    finally:
        db.close()


kpi_section()
st.write("")

left, right = st.columns([2, 1])

# ---------------------------------------------------------------------------
# Left column: machines, telemetry, forecast, inventory/orders
# ---------------------------------------------------------------------------
with left:
    st.subheader("Plant Floor — Machines")

    @st.fragment(run_every="3s")
    def machines_section():
        db = db_session()
        try:
            machines = db.query(models.Machine).all()
            names = [m.name for m in machines]
            if "selected_machine" not in st.session_state:
                st.session_state.selected_machine = names[0] if names else None

            st.session_state.selected_machine = st.radio(
                "Select a machine for live telemetry",
                names,
                index=names.index(st.session_state.selected_machine) if st.session_state.selected_machine in names else 0,
                horizontal=True,
                label_visibility="collapsed",
            )

            rows = []
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
                status = "anomaly" if open_anomaly else m.status
                rows.append({
                    "Machine": m.name, "Type": m.type, "Line": m.line,
                    "Status": "🔴 anomaly" if status == "anomaly" else ("🟢 running" if status == "running" else status),
                    "Vibration (mm/s)": latest.vibration_mm_s if latest else None,
                    "Temp (°C)": latest.temperature_c if latest else None,
                    "Cycle (s)": latest.cycle_time_s if latest else None,
                    "Pressure (bar)": latest.pressure_bar if latest else None,
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        finally:
            db.close()

    machines_section()

    st.subheader("Sensor Telemetry")

    @st.fragment(run_every="3s")
    def telemetry_section():
        machine_name = st.session_state.get("selected_machine")
        if not machine_name:
            st.info("No machine selected.")
            return
        db = db_session()
        try:
            machine = db.query(models.Machine).filter_by(name=machine_name).first()
            if not machine:
                return
            readings = (
                db.query(models.SensorReading)
                .filter(models.SensorReading.machine_id == machine.id)
                .order_by(models.SensorReading.timestamp.desc())
                .limit(40)
                .all()
            )
            readings = list(reversed(readings))
            if not readings:
                st.info("No telemetry yet.")
                return

            df = pd.DataFrame([{
                "timestamp": r.timestamp,
                **{metric: getattr(r, metric) for metric in CHART_COLORS},
            } for r in readings])
            df_long = df.melt("timestamp", var_name="metric", value_name="value")
            df_long["Metric"] = df_long["metric"].map(METRIC_LABELS)

            chart = alt.Chart(df_long).mark_line(point=False).encode(
                x=alt.X("timestamp:T", title=None),
                y=alt.Y("value:Q", title=None),
                color=alt.Color(
                    "Metric:N",
                    scale=alt.Scale(domain=list(METRIC_LABELS.values()), range=list(CHART_COLORS.values())),
                    legend=alt.Legend(orient="bottom", title=None),
                ),
                tooltip=["Metric", "value", "timestamp"],
            ).properties(height=260, title=f"Live telemetry — {machine_name}")
            st.altair_chart(chart, width="stretch")
        finally:
            db.close()

    telemetry_section()

    st.subheader("Demand Forecasting")

    @st.fragment(run_every="8s")
    def forecast_section():
        db = db_session()
        try:
            parts = db.query(models.Part).all()
            labels = [p.part_number for p in parts]
            if "selected_part" not in st.session_state:
                st.session_state.selected_part = labels[0] if labels else None
            st.session_state.selected_part = st.radio(
                "Select a part for demand forecast",
                labels,
                index=labels.index(st.session_state.selected_part) if st.session_state.selected_part in labels else 0,
                horizontal=True,
                label_visibility="collapsed",
            )
            part = next((p for p in parts if p.part_number == st.session_state.selected_part), None)
            if not part:
                return

            records = (
                db.query(models.ProductionRecord)
                .filter(models.ProductionRecord.part_id == part.id)
                .order_by(models.ProductionRecord.timestamp.asc())
                .all()
            )
            history = [r.units_produced for r in records] or [50.0]
            forecast = exponential_smoothing_forecast(history, horizon=7)

            hist_tail = history[-20:]
            hist_df = pd.DataFrame({
                "idx": list(range(-len(hist_tail) + 1, 1)),
                "value": hist_tail,
                "series": "Actual production",
            })
            fc_df = pd.DataFrame({
                "idx": list(range(1, len(forecast) + 1)),
                "value": forecast,
                "series": "Forecast",
            })
            combined = pd.concat([hist_df, fc_df])

            chart = alt.Chart(combined).mark_line(point=True).encode(
                x=alt.X("idx:Q", title="Days (0 = today)"),
                y=alt.Y("value:Q", title="Units"),
                color=alt.Color(
                    "series:N",
                    scale=alt.Scale(domain=["Actual production", "Forecast"], range=["#38bdf8", "#facc15"]),
                    legend=alt.Legend(orient="bottom", title=None),
                ),
                strokeDash=alt.condition("datum.series == 'Forecast'", alt.value([5, 4]), alt.value([0])),
            ).properties(height=240, title=f"Demand forecast — {part.name} (next 7 days)")
            st.altair_chart(chart, width="stretch")
        finally:
            db.close()

    forecast_section()

    st.subheader("Inventory & Orders")

    @st.fragment(run_every="6s")
    def inventory_orders_section():
        db = db_session()
        try:
            tab1, tab2 = st.tabs(["Inventory", "Orders"])
            with tab1:
                rows = db.query(models.Inventory, models.Part).join(models.Part).all()
                df = pd.DataFrame([{
                    "Part": part.name, "Line": part.line,
                    "On Hand": inv.qty_on_hand, "Reorder Pt.": inv.reorder_point,
                } for inv, part in rows])
                st.dataframe(df, hide_index=True, width="stretch")
            with tab2:
                rows = (
                    db.query(models.Order, models.Part)
                    .join(models.Part)
                    .order_by(models.Order.timestamp.desc())
                    .limit(20)
                    .all()
                )
                df = pd.DataFrame([{
                    "Customer": o.customer, "Part": part.name, "Qty": o.qty,
                    "Due": o.due_date.strftime("%d %b %Y"), "Status": o.status,
                } for o, part in rows])
                st.dataframe(df, hide_index=True, width="stretch")
        finally:
            db.close()

    inventory_orders_section()


# ---------------------------------------------------------------------------
# Right column: anomalies + recommendations (human approval)
# ---------------------------------------------------------------------------
with right:
    st.subheader("Anomaly Detection")

    @st.fragment(run_every="3s")
    def anomaly_section():
        db = db_session()
        try:
            anomalies = db.query(models.Anomaly).order_by(models.Anomaly.timestamp.desc()).limit(20).all()
            if not anomalies:
                st.success("No anomalies detected. All machines nominal.")
                return
            for a in anomalies:
                machine = db.query(models.Machine).get(a.machine_id)
                rc = db.query(models.RootCause).filter_by(anomaly_id=a.id).first()
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**{machine.name if machine else '—'}** · {machine.line if machine else ''}")
                    c2.markdown(f":{'red' if a.severity == 'critical' else 'orange'}[{a.severity.upper()}]")
                    st.caption(
                        f"{METRIC_LABELS.get(a.metric, a.metric)}: **{a.value}** "
                        f"(expected {a.expected_low}–{a.expected_high})"
                    )
                    if rc:
                        st.caption(f"Root cause: **{rc.cause}** ({rc.confidence * 100:.0f}% confidence)")
                    st.caption(f"{a.timestamp.strftime('%H:%M:%S')} · status: {a.status}")
        finally:
            db.close()

    anomaly_section()

    st.subheader("Recommendations — Human Approval Required")

    @st.fragment(run_every="3s")
    def recommendation_section():
        db = db_session()
        try:
            recs = db.query(models.Recommendation).order_by(models.Recommendation.timestamp.desc()).limit(20).all()
            if not recs:
                st.info("No recommendations awaiting review.")
                return
            for r in recs:
                anomaly = db.query(models.Anomaly).get(r.anomaly_id) if r.anomaly_id else None
                machine = db.query(models.Machine).get(anomaly.machine_id) if anomaly else None
                rc = db.query(models.RootCause).get(r.root_cause_id) if r.root_cause_id else None

                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**{r.title}**")
                    badge = {"pending": "🔵 pending", "executed": "🟢 executed", "rejected": "⚪ rejected"}.get(r.status, r.status)
                    c2.caption(badge)
                    st.caption(f"{machine.name if machine else ''} · {machine.line if machine else ''}")
                    st.write(r.rationale)
                    m1, m2, m3 = st.columns(3)
                    m1.caption(f"Est. cost impact: ₹{r.est_cost_impact_inr:,.0f}")
                    m2.caption(f"Downtime avoided: {r.est_downtime_avoided_hours}h")
                    m3.caption(f"Confidence: {r.confidence * 100:.0f}%")

                    if r.status == "pending":
                        b1, b2 = st.columns(2)
                        if b1.button("Approve & Execute", key=f"approve_{r.id}", type="primary"):
                            try:
                                approve_recommendation(db, r.id, "Plant Operations Manager")
                                st.rerun(scope="fragment")
                            except RecommendationError as e:
                                st.error(str(e))
                        if b2.button("Reject", key=f"reject_{r.id}"):
                            try:
                                reject_recommendation(db, r.id, "Plant Operations Manager")
                                st.rerun(scope="fragment")
                            except RecommendationError as e:
                                st.error(str(e))
                    else:
                        st.caption(f"{r.status.capitalize()} by {r.decided_by}")
        finally:
            db.close()

    recommendation_section()

st.divider()
st.subheader("Audit Trail")


@st.fragment(run_every="4s")
def audit_section():
    db = db_session()
    try:
        rows = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).limit(60).all()

        def format_details(raw: str) -> str:
            try:
                parsed = json.loads(raw)
                return "  ·  ".join(f"{k}: {v}" for k, v in parsed.items())
            except (TypeError, ValueError):
                return raw

        df = pd.DataFrame([{
            "Time": r.timestamp.strftime("%H:%M:%S"),
            "Actor": r.actor,
            "Event": r.event_type.replace("_", " "),
            "Details": format_details(r.details),
        } for r in rows])
        st.dataframe(df, hide_index=True, width="stretch", height=350)
    finally:
        db.close()


audit_section()
