import numpy as np

# Expected normal operating ranges per metric (auto-components CNC/press/weld/paint lines)
NORMAL_RANGES = {
    "vibration_mm_s": (0.5, 4.5),
    "temperature_c": (35, 75),
    "cycle_time_s": (18, 32),
    "pressure_bar": (4.0, 9.0),
}


def zscore_flag(values: list[float], latest: float, z_threshold: float = 3.0):
    if len(values) < 5:
        return False, 0.0
    arr = np.array(values)
    mean, std = arr.mean(), arr.std()
    if std == 0:
        return False, 0.0
    z = (latest - mean) / std
    return abs(z) >= z_threshold, float(z)


def classify_severity(metric: str, value: float) -> str | None:
    low, high = NORMAL_RANGES[metric]
    if value < low or value > high:
        margin = max(abs(value - low), abs(value - high))
        span = high - low
        ratio = margin / span if span else 1
        if ratio > 0.6:
            return "critical"
        elif ratio > 0.25:
            return "high"
        else:
            return "medium"
    return None
