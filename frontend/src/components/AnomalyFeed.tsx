import type { AnomalyRow } from "../api";

const severityStyles: Record<string, string> = {
  critical: "border-rose-500/40 bg-rose-500/10 text-rose-400",
  high: "border-amber-500/40 bg-amber-500/10 text-amber-400",
  medium: "border-yellow-500/40 bg-yellow-500/10 text-yellow-400",
};

export default function AnomalyFeed({ anomalies }: { anomalies: AnomalyRow[] | null }) {
  if (!anomalies) return <div className="text-sm text-slate-500">Loading anomalies…</div>;
  if (anomalies.length === 0) {
    return <div className="text-sm text-slate-500">No anomalies detected. All machines nominal.</div>;
  }

  return (
    <div className="flex max-h-[420px] flex-col gap-2 overflow-y-auto pr-1">
      {anomalies.map((a) => (
        <div key={a.id} className={`rounded-lg border p-3 ${severityStyles[a.severity] ?? "border-slate-800"}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-100">{a.machine}</span>
            <span className="rounded border px-1.5 py-0.5 text-[10px] uppercase">{a.severity}</span>
          </div>
          <div className="mt-0.5 text-xs text-slate-400">{a.line}</div>
          <div className="mt-1 text-xs text-slate-300">
            {a.metric.replace(/_/g, " ")}: <span className="font-mono">{a.value}</span>{" "}
            <span className="text-slate-500">(expected {a.expected_low}–{a.expected_high})</span>
          </div>
          {a.root_cause && (
            <div className="mt-1 text-xs text-slate-400">
              Root cause: <span className="text-slate-200">{a.root_cause}</span>{" "}
              {a.root_cause_confidence != null && (
                <span className="text-slate-500">({Math.round(a.root_cause_confidence * 100)}% confidence)</span>
              )}
            </div>
          )}
          <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
            <span>{new Date(a.timestamp).toLocaleTimeString("en-IN")}</span>
            <span className="capitalize">{a.status}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
