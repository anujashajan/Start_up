import type { Kpis } from "../api";

function Card({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone?: "good" | "bad" | "neutral" }) {
  const toneClass =
    tone === "good" ? "text-emerald-400" : tone === "bad" ? "text-rose-400" : "text-slate-100";
  return (
    <div className="flex-1 min-w-[150px] rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3">
      <div className="text-[11px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${toneClass}`}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}

export default function KpiBar({ kpis }: { kpis: Kpis | null }) {
  if (!kpis) {
    return <div className="text-sm text-slate-500">Loading live plant data…</div>;
  }
  return (
    <div className="flex flex-wrap gap-3">
      <Card label="OEE" value={`${kpis.oee_pct}%`} sub="Overall Equipment Effectiveness" />
      <Card
        label="Machines Running"
        value={`${kpis.machines_running}/${kpis.machines_total}`}
        tone={kpis.machines_running === kpis.machines_total ? "good" : "bad"}
      />
      <Card label="Units Produced (6h)" value={kpis.units_produced_6h.toLocaleString("en-IN")} />
      <Card
        label="Defect Rate"
        value={`${kpis.defect_rate_pct}%`}
        tone={kpis.defect_rate_pct > 3 ? "bad" : "good"}
      />
      <Card
        label="Open Anomalies"
        value={String(kpis.open_anomalies)}
        tone={kpis.open_anomalies > 0 ? "bad" : "good"}
      />
      <Card
        label="Pending Approvals"
        value={String(kpis.pending_recommendations)}
        tone={kpis.pending_recommendations > 0 ? "bad" : "neutral"}
      />
      <Card
        label="Cost Impact Avoided"
        value={`₹${kpis.cost_savings_inr.toLocaleString("en-IN")}`}
        sub={`${kpis.downtime_avoided_hours}h downtime avoided`}
        tone="good"
      />
    </div>
  );
}
