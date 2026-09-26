import { useState } from "react";
import { api, type RecommendationRow } from "../api";

const severityBorder: Record<string, string> = {
  critical: "border-l-rose-500",
  high: "border-l-amber-500",
  medium: "border-l-yellow-500",
};

const statusBadge: Record<string, string> = {
  pending: "bg-sky-500/15 text-sky-400",
  executed: "bg-emerald-500/15 text-emerald-400",
  rejected: "bg-slate-600/20 text-slate-400",
};

export default function RecommendationQueue({
  recommendations,
  onDecided,
}: {
  recommendations: RecommendationRow[] | null;
  onDecided: () => void;
}) {
  const [busyId, setBusyId] = useState<number | null>(null);

  if (!recommendations) return <div className="text-sm text-slate-500">Loading recommendations…</div>;

  async function decide(id: number, action: "approve" | "reject") {
    setBusyId(id);
    try {
      await api.post(`/recommendations/${id}/${action}`, { decided_by: "Plant Operations Manager" });
      onDecided();
    } finally {
      setBusyId(null);
    }
  }

  if (recommendations.length === 0) {
    return <div className="text-sm text-slate-500">No recommendations awaiting review.</div>;
  }

  return (
    <div className="flex max-h-[520px] flex-col gap-3 overflow-y-auto pr-1">
      {recommendations.map((r) => (
        <div key={r.id} className={`rounded-lg border border-slate-800 border-l-4 bg-slate-900/60 p-3 ${severityBorder[r.severity ?? ""] ?? ""}`}>
          <div className="flex items-start justify-between gap-2">
            <div className="text-sm font-medium text-slate-100">{r.title}</div>
            <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] uppercase ${statusBadge[r.status] ?? "bg-slate-700/30 text-slate-400"}`}>
              {r.status}
            </span>
          </div>
          <div className="mt-0.5 text-[11px] text-slate-500">
            {r.machine} · {r.line}
          </div>
          <p className="mt-1.5 text-xs leading-relaxed text-slate-400">{r.rationale}</p>
          <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-slate-400">
            <span>Est. cost impact: <span className="text-emerald-400">₹{r.est_cost_impact_inr.toLocaleString("en-IN")}</span></span>
            <span>Downtime avoided: <span className="text-emerald-400">{r.est_downtime_avoided_hours}h</span></span>
            <span>Confidence: {Math.round(r.confidence * 100)}%</span>
          </div>
          {r.status === "pending" ? (
            <div className="mt-2.5 flex gap-2">
              <button
                disabled={busyId === r.id}
                onClick={() => decide(r.id, "approve")}
                className="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
              >
                Approve &amp; Execute
              </button>
              <button
                disabled={busyId === r.id}
                onClick={() => decide(r.id, "reject")}
                className="rounded-md border border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800 disabled:opacity-50"
              >
                Reject
              </button>
            </div>
          ) : (
            <div className="mt-2 text-[11px] text-slate-500">
              {r.status === "executed" ? "Executed" : "Rejected"} by {r.decided_by}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
