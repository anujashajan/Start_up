import datetime as dt

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from .database import Base, engine, SessionLocal
from . import simulator
from .seed import init_demo_state
from .routers import dashboard, anomalies, recommendations, audit

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Factory Intelligence Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(anomalies.router)
app.include_router(recommendations.router)
app.include_router(audit.router)

scheduler = BackgroundScheduler()


def scheduled_tick():
    db = SessionLocal()
    try:
        simulator.run_tick(db)
    except Exception as e:
        print(f"[simulator tick error] {e}")
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        init_demo_state(db)
    finally:
        db.close()

    scheduler.add_job(scheduled_tick, "interval", seconds=5, id="factory_tick", max_instances=1)
    scheduler.start()


@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown(wait=False)


@app.get("/api/health")
def health():
    return {"status": "ok", "time": dt.datetime.utcnow().isoformat()}
