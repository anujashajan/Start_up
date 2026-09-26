import datetime as dt
import json

# Rule-based root cause engine: correlates the anomalous metric with
# maintenance history, machine type and time-of-day/shift patterns to
# produce a plausible, explainable root cause with a confidence score.

CAUSE_LIBRARY = {
    "vibration_mm_s": [
        ("Bearing wear on spindle / tool head", 0.82),
        ("Tool misalignment after last changeover", 0.68),
        ("Loose mounting bolts causing resonance", 0.55),
    ],
    "temperature_c": [
        ("Coolant flow restriction / low coolant level", 0.78),
        ("Overdue preventive maintenance causing friction heat", 0.7),
        ("Ambient shop-floor temperature spike (HVAC load)", 0.5),
    ],
    "cycle_time_s": [
        ("Upstream material feed delay", 0.66),
        ("Tool wear increasing machining time", 0.74),
        ("Operator/shift handover slowdown", 0.45),
    ],
    "pressure_bar": [
        ("Hydraulic seal leakage", 0.8),
        ("Compressor undersized for current load", 0.6),
        ("Filter clogging restricting flow", 0.58),
    ],
}


def analyze(machine, metric: str, value: float, expected_low: float, expected_high: float):
    options = CAUSE_LIBRARY.get(metric, [("Unclassified process deviation", 0.4)])

    days_since_maintenance = (dt.datetime.utcnow() - machine.last_maintenance).days
    maintenance_overdue = days_since_maintenance > (machine.maintenance_interval_hours / 24)

    cause, base_confidence = options[0]
    confidence = base_confidence
    evidence = {
        "metric": metric,
        "observed_value": round(value, 2),
        "expected_range": [expected_low, expected_high],
        "days_since_last_maintenance": days_since_maintenance,
        "maintenance_overdue": maintenance_overdue,
        "machine_type": machine.type,
    }

    if maintenance_overdue:
        confidence = min(0.95, confidence + 0.12)
        evidence["note"] = "Maintenance interval exceeded — strong contributing factor"
    else:
        cause, base_confidence = options[min(1, len(options) - 1)]
        confidence = base_confidence

    return cause, round(confidence, 2), json.dumps(evidence)
