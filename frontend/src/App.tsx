import { useEffect, useState } from "react";
import { api } from "./api";
import type {
  AnomalyRow,
  AuditRow,
  ForecastResponse,
  InventoryRow,
  Kpis,
  MachineRow,
  OrderRow,
  PartRow,
  RecommendationRow,
} from "./api";
import { usePolling } from "./hooks/usePolling";
import KpiBar from "./components/KpiBar";
import MachineGrid from "./components/MachineGrid";
import SensorChart from "./components/SensorChart";
import ForecastPanel from "./components/ForecastPanel";
import AnomalyFeed from "./components/AnomalyFeed";
import RecommendationQueue from "./components/RecommendationQueue";
import AuditTrail from "./components/AuditTrail";
import InventoryOrders from "./components/InventoryOrders";
import PipelineStepper from "./components/PipelineStepper";

export default function App() {
  const [refreshTick, setRefreshTick] = useState(0);
  const [selectedMachine, setSelectedMachine] = useState<number | null>(null);
  const [selectedPart, setSelectedPart] = useState<number | null>(null);
  const [machineHistory, setMachineHistory] = useState<import("./api").SensorSnapshot[] | null>(null);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);

  const { data: kpis } = usePolling<Kpis>(() => api.get("/kpis").then((r) => r.data), 3000, [refreshTick]);
  const { data: machines } = usePolling<MachineRow[]>(() => api.get("/machines").then((r) => r.data), 3000, [refreshTick]);
  const { data: anomalies } = usePolling<AnomalyRow[]>(() => api.get("/anomalies").then((r) => r.data), 3000, [refreshTick]);
  const { data: recommendations } = usePolling<RecommendationRow[]>(
    () => api.get("/recommendations").then((r) => r.data),
    3000,
    [refreshTick]
  );
  const { data: audit } = usePolling<AuditRow[]>(() => api.get("/audit").then((r) => r.data), 4000, [refreshTick]);
  const { data: inventory } = usePolling<InventoryRow[]>(() => api.get("/inventory").then((r) => r.data), 6000, [refreshTick]);
  const { data: orders } = usePolling<OrderRow[]>(() => api.get("/orders").then((r) => r.data), 6000, [refreshTick]);
  const { data: parts } = usePolling<PartRow[]>(() => api.get("/parts").then((r) => r.data), 30000, []);

  useEffect(() => {
    if (!selectedMachine && machines && machines.length > 0) {
      setSelectedMachine(machines[0].id);
    }
  }, [machines, selectedMachine]);

  useEffect(() => {
    if (!selectedPart && parts && parts.length > 0) {
      setSelectedPart(parts[0].id);
    }
  }, [parts, selectedPart]);

  useEffect(() => {
    if (!selectedMachine) return;
    let cancelled = false;
    const load = () =>
      api.get(`/machines/${selectedMachine}/history`).then((r) => {
        if (!cancelled) setMachineHistory(r.data);
      });
    load();
    const id = setInterval(load, 3000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [selectedMachine]);

  useEffect(() => {
    if (!selectedPart) return;
    let cancelled = false;
    const load = () =>
      api.get(`/forecast/${selectedPart}`).then((r) => {
        if (!cancelled) setForecast(r.data);
      });
    load();
    const id = setInterval(load, 8000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [selectedPart]);

  const selectedMachineName = machines?.find((m) => m.id === selectedMachine)?.name;

  return (
    <div className="min-h-screen bg-slate-950 pb-16 text-slate-200">
      <header className="border-b border-slate-800 bg-slate-950/80 px-6 py-5 backdrop-blur">
        <div className="mx-auto max-w-[1400px]">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-xl font-semibold text-slate-50">Factory Intelligence Copilot</h1>
              <p className="text-sm text-slate-500">
                Industrial AI Decision &amp; Automation Platform — POC · Auto-Components Manufacturing
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              Live simulation running
            </div>
          </div>
          <div className="mt-4">
            <PipelineStepper />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1400px] px-6 pt-5">
        <section className="mb-5">
          <KpiBar kpis={kpis ?? null} />
        </section>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="flex flex-col gap-4 lg:col-span-2">
            <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <h2 className="mb-3 text-sm font-semibold text-slate-300">Plant Floor — Machines</h2>
              <MachineGrid machines={machines ?? null} selectedId={selectedMachine} onSelect={setSelectedMachine} />
            </section>

            <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <h2 className="mb-1 text-sm font-semibold text-slate-300">Sensor Telemetry</h2>
              <SensorChart history={machineHistory} machineName={selectedMachineName} />
            </section>

            <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <h2 className="mb-1 text-sm font-semibold text-slate-300">Demand Forecasting</h2>
              <ForecastPanel parts={parts ?? null} selectedPartId={selectedPart} onSelect={setSelectedPart} forecast={forecast} />
            </section>

            <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <h2 className="mb-2 text-sm font-semibold text-slate-300">Inventory &amp; Orders</h2>
              <InventoryOrders inventory={inventory ?? null} orders={orders ?? null} />
            </section>
          </div>

          <div className="flex flex-col gap-4">
            <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <h2 className="mb-2 text-sm font-semibold text-slate-300">Anomaly Detection</h2>
              <AnomalyFeed anomalies={anomalies ?? null} />
            </section>

            <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
              <h2 className="mb-2 text-sm font-semibold text-slate-300">Recommendations — Human Approval Required</h2>
              <RecommendationQueue recommendations={recommendations ?? null} onDecided={() => setRefreshTick((t) => t + 1)} />
            </section>
          </div>
        </div>

        <section className="mt-4 rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <h2 className="mb-2 text-sm font-semibold text-slate-300">Audit Trail</h2>
          <AuditTrail rows={audit ?? null} />
        </section>
      </main>
    </div>
  );
}
