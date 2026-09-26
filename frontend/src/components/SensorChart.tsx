import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import type { SensorSnapshot } from "../api";

const COLORS = {
  vibration_mm_s: "#38bdf8",
  temperature_c: "#fb923c",
  cycle_time_s: "#a78bfa",
  pressure_bar: "#34d399",
};

const LABELS: Record<string, string> = {
  vibration_mm_s: "Vibration (mm/s)",
  temperature_c: "Temperature (°C)",
  cycle_time_s: "Cycle Time (s)",
  pressure_bar: "Pressure (bar)",
};

export default function SensorChart({ history, machineName }: { history: SensorSnapshot[] | null; machineName?: string }) {
  if (!history || history.length === 0) {
    return <div className="text-sm text-slate-500">Select a machine to view live sensor telemetry.</div>;
  }

  const data = history.map((r) => ({
    time: new Date(r.timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    ...r,
  }));

  return (
    <div>
      <div className="mb-1 text-xs text-slate-500">{machineName ? `Live telemetry — ${machineName}` : "Live telemetry"}</div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
          <YAxis stroke="#64748b" fontSize={10} />
          <Tooltip
            contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", fontSize: 12 }}
            labelStyle={{ color: "#94a3b8" }}
          />
          {(Object.keys(COLORS) as (keyof typeof COLORS)[]).map((key) => (
            <Line key={key} type="monotone" dataKey={key} stroke={COLORS[key]} dot={false} strokeWidth={2} name={LABELS[key]} />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div className="mt-1 flex flex-wrap gap-3 text-[11px]">
        {(Object.keys(COLORS) as (keyof typeof COLORS)[]).map((key) => (
          <span key={key} className="flex items-center gap-1 text-slate-400">
            <span className="inline-block h-2 w-2 rounded-full" style={{ background: COLORS[key] }} />
            {LABELS[key]}
          </span>
        ))}
      </div>
    </div>
  );
}
