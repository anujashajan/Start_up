# Factory Intelligence Copilot (POC)

An Industrial AI Decision & Automation Platform demo for auto-components manufacturing.
Simulates a real plant (CNC machining, hydraulic press, robotic welding, paint booth,
assembly) and runs the full decision loop live, end to end:

```
Operational Data -> AI Forecasting -> Anomaly Detection -> Root Cause
  -> Recommendation -> Human Approval -> Automated Action -> Audit Trail
```

## Architecture

- **backend/** - FastAPI + SQLite. A background scheduler ticks every 5s, generating
  realistic sensor/production/order data across 8 machines and 6 parts (brake,
  suspension, transmission lines). Each tick runs the AI pipeline:
  - `app/ml/forecasting.py` - exponential smoothing demand forecast per part
  - `app/ml/anomaly.py` - rolling z-score + operating-range checks on sensor telemetry
  - `app/ml/root_cause.py` - rule-based root cause engine (maintenance history,
    machine type, deviation pattern)
  - `app/ml/recommend.py` - maps root cause to a concrete recommended action with
    estimated cost impact (INR) and downtime avoided
  - Every step is written to an immutable `audit_log` table (actor, event, entity, details)
  - Recommendations sit `pending` until a human approves/rejects via the API; approval
    triggers automated action execution and closes the loop

- **frontend/** - React + Vite + TypeScript + Tailwind + Recharts. Polls the API and
  renders: plant floor status, live sensor telemetry, demand forecast, anomaly feed,
  a human approval queue (Approve & Execute / Reject), inventory & orders, and the
  full audit trail.

- **streamlit_app.py** (repo root) - a second, self-contained presentation layer over
  the *same* `backend/app` package (models, simulator, ML pipeline, `actions.py` for
  approve/reject) — no logic duplicated. Built for one-command sharing via
  Streamlit Community Cloud instead of running two separate dev servers.

There are two ways to run this demo. Pick one.

## Option A — FastAPI + React (fuller UI, needs two processes)

**First-time setup:**

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

cd ..\frontend
npm install
```

**Every time after that**, from the project root:

```powershell
.\start.ps1
```

This opens two windows: the backend on `http://127.0.0.1:8000` and the dashboard on
`http://localhost:5173`.

## Option B — Streamlit (single process, one-click cloud deploy)

**First-time setup:**

```powershell
python -m venv venv_streamlit
.\venv_streamlit\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Run it:**

```powershell
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`. Same simulation, same pipeline, same approve/reject
loop — rendered with Streamlit's native components (`st.fragment(run_every=...)` for
the live-updating sections) instead of a polling React app.

**Deploying it for real** (to get a shareable `https://...streamlit.app` link):

1. Push this repo to GitHub (see below — this step needs your GitHub account, so I
   didn't do it automatically).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, click
   "New app", pick this repo/branch, and set the main file path to `streamlit_app.py`.
   It reads `requirements.txt` and `.streamlit/config.toml` from the repo root
   automatically.
3. That's it — Streamlit Cloud builds and hosts it. The free tier sleeps after
   inactivity and wakes on the next visit (~30s cold start).

Note: the SQLite database resets on every redeploy/restart on Streamlit Cloud (its
filesystem is ephemeral) — the simulation regenerates data on its own, so this is
expected and fine for a live demo, not a concern.

### Pushing this repo to GitHub

I haven't touched git or GitHub for this project — that needs your account. From the
project root:

```powershell
git init
git add .
git commit -m "Factory Intelligence Copilot POC"
gh repo create <your-repo-name> --private --source=. --push   # if you have GitHub CLI
# or: create an empty repo on github.com, then:
# git remote add origin <your-repo-url>
# git push -u origin main
```

## Notes for the demo

- The simulation is intentionally paced (roughly one new anomaly every 30-60s) so the
  story is legible live rather than a wall of noise.
- All figures (cost impact, downtime avoided, OEE) are simulated for demonstration —
  swap `app/simulator.py` and `app/seed.py` for real plant data sources to move this
  from POC to pilot.
