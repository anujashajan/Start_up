import numpy as np


def exponential_smoothing_forecast(history: list[float], horizon: int = 7, alpha: float = 0.35):
    """Simple exponential smoothing with a light trend component.
    history: chronological list of daily demand values (most recent last).
    Returns list of `horizon` forecast values.
    """
    if not history:
        return [0.0] * horizon

    level = history[0]
    trend = 0.0
    beta = 0.15
    for value in history[1:]:
        prev_level = level
        level = alpha * value + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend

    forecasts = []
    for h in range(1, horizon + 1):
        forecasts.append(max(0.0, level + h * trend))
    return forecasts


def forecast_accuracy(actual: list[float], predicted: list[float]) -> float:
    if not actual or not predicted:
        return 0.0
    n = min(len(actual), len(predicted))
    a = np.array(actual[:n])
    p = np.array(predicted[:n])
    denom = np.where(a == 0, 1, a)
    mape = np.mean(np.abs((a - p) / denom))
    return max(0.0, 1 - mape) * 100
