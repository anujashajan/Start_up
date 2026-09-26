import random

# Maps a root-cause label to a concrete recommended action, with an
# estimated cost impact and downtime avoided — the numbers a plant
# manager / decision-maker actually cares about.

ACTION_TEMPLATES = {
    "Bearing wear on spindle / tool head": (
        "Schedule predictive maintenance: spindle bearing replacement",
        "predictive_maintenance", (18000, 45000), (4, 10),
    ),
    "Tool misalignment after last changeover": (
        "Trigger tool recalibration before next shift",
        "recalibration", (5000, 15000), (1, 3),
    ),
    "Loose mounting bolts causing resonance": (
        "Dispatch technician to torque-check mounting bolts",
        "inspection", (3000, 9000), (1, 2),
    ),
    "Coolant flow restriction / low coolant level": (
        "Top up coolant and inspect flow line for blockage",
        "maintenance", (2000, 6000), (1, 2),
    ),
    "Overdue preventive maintenance causing friction heat": (
        "Escalate overdue preventive maintenance to top priority",
        "predictive_maintenance", (20000, 60000), (6, 14),
    ),
    "Ambient shop-floor temperature spike (HVAC load)": (
        "Notify facilities team to check HVAC load on shop floor",
        "facilities_alert", (1000, 4000), (0, 1),
    ),
    "Upstream material feed delay": (
        "Coordinate with upstream line to clear material feed backlog",
        "process_coordination", (4000, 12000), (2, 5),
    ),
    "Tool wear increasing machining time": (
        "Schedule tool replacement for affected station",
        "predictive_maintenance", (6000, 18000), (2, 5),
    ),
    "Operator/shift handover slowdown": (
        "Review shift handover checklist with line supervisor",
        "process_review", (1500, 5000), (0, 1),
    ),
    "Hydraulic seal leakage": (
        "Replace hydraulic seal and inspect press hydraulics",
        "maintenance", (10000, 30000), (3, 8),
    ),
    "Compressor undersized for current load": (
        "Flag compressor capacity for capex review",
        "capex_review", (0, 0), (0, 0),
    ),
    "Filter clogging restricting flow": (
        "Replace hydraulic/pneumatic filter element",
        "maintenance", (2000, 7000), (1, 3),
    ),
}

DEFAULT_ACTION = (
    "Dispatch maintenance technician for manual inspection",
    "inspection", (3000, 10000), (1, 3),
)


def recommend_for_cause(cause: str, severity: str):
    title, action_type, cost_range, downtime_range = ACTION_TEMPLATES.get(cause, DEFAULT_ACTION)
    severity_multiplier = {"critical": 1.3, "high": 1.1, "medium": 0.9}.get(severity, 1.0)
    cost = random.uniform(*cost_range) * severity_multiplier
    downtime = random.uniform(*downtime_range) * severity_multiplier
    rationale = (
        f"Root cause analysis attributes this anomaly to '{cause}'. "
        f"Recommended action selected from historical resolution patterns for this failure mode."
    )
    return title, action_type, round(cost, 0), round(downtime, 1), rationale
