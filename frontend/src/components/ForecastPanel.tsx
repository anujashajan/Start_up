import { Area, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import type { ForecastResponse, PartRow } from "../api";

export default function ForecastPanel({
  parts,
  selectedPartId,
  onSelect,
  forecast,
}: {
  parts: PartRow[] | null;
  selectedPartId: number | null;
  onSelect: (id: number) => void;
  forecast: ForecastResponse | null;
}) {
  const data: Record<string, number | null>[] = [];
  if (forecast) {
    forecast.history.forEach((v, i) => {
      data.push({ idx: i - forecast.history.length, actual: v, forecast: null });
    });
    forecast.forecast.forEach((v, i) => {
      data.push({ idx: i + 1, actual: null, forecast: v });
    });
    if (data.length > forecast.history.length) {
      data[forecast.history.length - 1].forecast = forecast.history[forecast.history.length - 1];
    }
  }

  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-1">
        {parts?.map((p) => (
          <button
            key={p.id}
            onClick={() => onSelect(p.id)}
            className={`rounded-full border px-2.5 py-1 text-[11px] ${
              selectedPartId === p.id
                ? "border-sky-500 bg-sky-500/10 text-sky-300"
                : "border-slate-800 text-slate-400 hover:border-slate-700"
            }`}
          >
            {p.part_number}
          </button>
        ))}
      </div>
      {forecast ? (
        <>
          <div className="mb-1 text-xs text-slate-500">
            Demand forecast — {forecast.part_name} (next 7 days, exponential smoothing)
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="idx" stroke="#64748b" fontSize={10} />
              <YAxis stroke="#64748b" fontSize={10} />
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", fontSize: 12 }} />
              <Area type="monotone" dataKey="actual" stroke="#38bdf8" fill="#38bdf822" strokeWidth={2} name="Actual production" connectNulls={false} />
              <Line type="monotone" dataKey="forecast" stroke="#facc15" strokeWidth={2} strokeDasharray="5 4" dot={false} name="Forecast" connectNulls />
            </ComposedChart>
          </ResponsiveContainer>
        </>
      ) : (
        <div className="text-sm text-slate-500">Select a part to view demand forecast.</div>
      )}
    </div>
  );
}
