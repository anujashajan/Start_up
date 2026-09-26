import axios from "axios";

export const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
});

export interface Kpis {
  units_produced_6h: number;
  units_rejected_6h: number;
  defect_rate_pct: number;
  open_anomalies: number;
  pending_recommendations: number;
  executed_recommendations: number;
  cost_savings_inr: number;
  downtime_avoided_hours: number;
  oee_pct: number;
  machines_running: number;
  machines_total: number;
}

export interface SensorSnapshot {
  vibration_mm_s: number;
  temperature_c: number;
  cycle_time_s: number;
  pressure_bar: number;
  timestamp: string;
}

export interface MachineRow {
  id: number;
  name: string;
  type: string;
  line: string;
  status: string;
  last_maintenance: string;
  latest_reading: SensorSnapshot | null;
}

export interface AnomalyRow {
  id: number;
  timestamp: string;
  machine: string;
  line: string;
  metric: string;
  value: number;
  expected_low: number;
  expected_high: number;
  severity: "critical" | "high" | "medium";
  status: string;
  root_cause: string | null;
  root_cause_confidence: number | null;
}

export interface RecommendationRow {
  id: number;
  timestamp: string;
  title: string;
  rationale: string;
  action_type: string;
  est_cost_impact_inr: number;
  est_downtime_avoided_hours: number;
  confidence: number;
  status: "pending" | "approved" | "rejected" | "executed";
  decided_by: string | null;
  machine: string | null;
  line: string | null;
  severity: string | null;
  root_cause: string | null;
  evidence: Record<string, unknown> | null;
}

export interface AuditRow {
  id: number;
  timestamp: string;
  actor: string;
  event_type: string;
  entity_type: string;
  entity_id: number | null;
  details: string;
}

export interface InventoryRow {
  part_number: string;
  part_name: string;
  line: string;
  qty_on_hand: number;
  reorder_point: number;
  below_reorder: boolean;
}

export interface OrderRow {
  id: number;
  customer: string;
  part_name: string;
  qty: number;
  due_date: string;
  status: string;
  timestamp: string;
}

export interface PartRow {
  id: number;
  part_number: string;
  name: string;
  line: string;
}

export interface ForecastResponse {
  part_id: number;
  part_name: string;
  history: number[];
  forecast: number[];
}
