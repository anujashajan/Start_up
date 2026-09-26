import type { MachineRow } from "../api";

const statusStyles: Record<string, string> = {
  running: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  anomaly: "bg-rose-500/15 text-rose-400 border-rose-500/30",
  idle: "bg-slate-500/15 text-slate-400 border-slate-500/30",
};

export default function MachineGrid({
  machines,
  selectedId,
  onSelect,
}: {
  machines: MachineRow[] | null;
  selectedId: number | null;
  onSelect: (id: number) => void;
}) {
  if (!machines) return <div className="text-sm text-slate-500">Loading machines…</div>;

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {machines.map((m) => (
        <button
          key={m.id}
          onClick={() => onSelect(m.id)}
          className={`rounded-lg border p-3 text-left transition ${
            selectedId === m.id ? "border-sky-500 bg-sky-500/10" : "border-slate-800 bg-slate-900/60 hover:border-slate-700"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-200">{m.name}</span>
            <span className={`rounded border px-1.5 py-0.5 text-[10px] uppercase ${statusStyles[m.status] ?? statusStyles.idle}`}>
              {m.status}
            </span>
          </div>
          <div className="mt-0.5 text-[11px] text-slate-500">{m.type}</div>
          <div className="mt-0.5 text-[11px] text-slate-600">{m.line}</div>
          {m.latest_reading && (
            <div className="mt-2 grid grid-cols-2 gap-x-2 gap-y-0.5 text-[11px] text-slate-400">
              <span>Vib {m.latest_reading.vibration_mm_s} mm/s</span>
              <span>Temp {m.latest_reading.temperature_c}°C</span>
              <span>Cycle {m.latest_reading.cycle_time_s}s</span>
              <span>Pres {m.latest_reading.pressure_bar} bar</span>
            </div>
          )}
        </button>
      ))}
    </div>
  );
}
