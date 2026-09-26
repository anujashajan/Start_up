const STEPS = [
  "Operational Data",
  "AI Forecasting",
  "Anomaly Detection",
  "Root Cause",
  "Recommendation",
  "Human Approval",
  "Automated Action",
  "Audit Trail",
];

export default function PipelineStepper() {
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
      {STEPS.map((step, i) => (
        <div key={step} className="flex items-center gap-1.5">
          <span className="rounded-full border border-slate-800 bg-slate-900/60 px-2.5 py-1 text-slate-400">
            {step}
          </span>
          {i < STEPS.length - 1 && <span className="text-slate-700">→</span>}
        </div>
      ))}
    </div>
  );
}
