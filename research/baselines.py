"""Time-ordered one-month-ahead persistence benchmark for published levels."""

from math import isfinite, sqrt
from statistics import mean


def persistence(values: list[float], holdout: int) -> dict:
    if not 2 <= holdout < len(values) or not all(isfinite(value) for value in values):
        raise ValueError("Require a finite series and at least two holdout months")
    errors = [
        actual - prediction
        for actual, prediction in zip(
            values[-holdout:], values[-holdout - 1 : -1], strict=True
        )
    ]
    return {
        "family": "predictive_baseline",
        "method": "one-month persistence, rolling origin",
        "holdout_observations": holdout,
        "mae": mean(map(abs, errors)),
        "rmse": sqrt(mean(error**2 for error in errors)),
    }
