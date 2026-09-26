import type { AuditRow } from "../api";

const eventStyles: Record<string, string> = {
  anomaly_detected: "text-rose-400",
  root_cause_identified: "text-amber-400",
  recommendation_generated: "text-sky-400",
  recommendation_approved: "text-emerald-400",
  recommendation_rejected: "text-slate-400",
  action_executed: "text-emerald-400",
  pipeline_initialized: "text-slate-500",
};

function formatDetails(raw: string) {
  try {
    const parsed = JSON.parse(raw);
    return Object.entries(parsed)
      .map(([k, v]) => `${k}: ${v}`)
      .join("  ·  ");
  } catch {
    return raw;
  }
}

export default function AuditTrail({ rows }: { rows: AuditRow[] | null }) {
  if (!rows) return <div className="text-sm text-slate-500">Loading audit trail…</div>;

  return (
    <div className="max-h-[420px] overflow-y-auto">
      <table className="w-full border-collapse text-left text-xs">
        <thead className="sticky top-0 bg-slate-950">
          <tr className="text-slate-500">
            <th className="px-2 py-1.5 font-medium">Time</th>
            <th className="px-2 py-1.5 font-medium">Actor</th>
            <th className="px-2 py-1.5 font-medium">Event</th>
            <th className="px-2 py-1.5 font-medium">Details</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="border-t border-slate-800/60">
              <td className="whitespace-nowrap px-2 py-1.5 text-slate-500">
                {new Date(r.timestamp).toLocaleTimeString("en-IN")}
              </td>
              <td className="whitespace-nowrap px-2 py-1.5 text-slate-300">{r.actor}</td>
              <td className={`whitespace-nowrap px-2 py-1.5 font-medium ${eventStyles[r.event_type] ?? "text-slate-300"}`}>
                {r.event_type.replace(/_/g, " ")}
              </td>
              <td className="px-2 py-1.5 text-slate-500">{formatDetails(r.details)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
