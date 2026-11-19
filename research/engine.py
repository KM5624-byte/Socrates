"""Route approved research operations to their numerical implementations."""

import hashlib
import json
from importlib.metadata import version
from itertools import pairwise
from pathlib import Path
from typing import Literal

import duckdb
import numpy as np
from pydantic import BaseModel, Field
from sklearn.linear_model import Ridge

from research.baselines import persistence


class Study(BaseModel):
    source: Literal["cps", "laus", "jolts"]
    release: str = Field(pattern=r"^[a-f0-9]{64}$")
    method: Literal[
        "descriptive", "deterministic", "predictive", "simulation", "causal-diagnostics"
    ]
    holdout: int = Field(default=12, ge=3, le=36)
    seed: int = Field(default=42, ge=0, le=2**32 - 1)
    monthly_change: float = Field(default=0, ge=-1000, le=1000, allow_inf_nan=False)
    shock_sd: float = Field(default=0.1, ge=0, le=1000, allow_inf_nan=False)
    horizon: int = Field(default=12, ge=1, le=36)


def run(study: Study, root: Path = Path("data/releases")) -> dict:
    directory = root / study.source / study.release
    manifest = json.loads((directory / "manifest.json").read_text())
    artifact = directory / "series.parquet"
    checksum = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if (
        manifest["version"] != study.release
        or manifest["source_id"] != study.source
        or checksum != manifest["gold_checksum"]
    ):
        raise ValueError("Release identity or checksum mismatch")
    with duckdb.connect(config={"threads": 1}) as db:
        rows = db.execute(
            "SELECT month, value FROM read_parquet(?) ORDER BY month", [str(artifact)]
        ).fetchall()
    if not rows:
        raise ValueError("The release contains no monthly rows")
    values = np.array([np.nan if value is None else value for _, value in rows])
    observed = values[np.isfinite(values)]
    if not len(observed):
        raise ValueError("The release contains no usable observations")
    method = study.method
    assumptions = []
    if method == "descriptive":
        result = {
            "mean": float(np.mean(observed)),
            "median": float(np.median(observed)),
            "minimum": float(np.min(observed)),
            "maximum": float(np.max(observed)),
        }
        assumptions.append(
            "Statistics exclude missing observations. Mean is unweighted across months."
        )
    elif method == "deterministic":
        if not np.isfinite(values[[0, -1]]).all():
            raise ValueError("Both endpoint months must have observations")
        result = {
            "absolute_change": float(values[-1] - values[0]),
            "first": float(values[0]),
            "last": float(values[-1]),
        }
        assumptions.append(
            "Endpoint subtraction retains the source unit. Rate changes are percentage points."
        )
    elif method == "predictive":
        if len(values) < study.holdout + 6 or not np.isfinite(values).all():
            raise ValueError(
                "Forecasting requires a complete series with at least six training months"
            )
        periods = [int(month[:4]) * 12 + int(month[5:]) for month, _ in rows]
        if any(right - left != 1 for left, right in pairwise(periods)):
            raise ValueError("Forecasting requires consecutive months")
        lagged = values[:-1].reshape(-1, 1)
        target = values[1:]
        split = len(target) - study.holdout
        ridge = Ridge(alpha=1.0).fit(lagged[:split], target[:split])
        errors = target[split:] - ridge.predict(lagged[split:])
        result = {
            "ridge_mae": float(np.abs(errors).mean()),
            "ridge_rmse": float(np.sqrt(np.square(errors).mean())),
            "persistence_baseline": persistence(values.tolist(), study.holdout),
            "evaluation_start": rows[-study.holdout][0],
            "evaluation_end": rows[-1][0],
        }
        assumptions.append(
            "Ridge fits only the pre-holdout window. Each forecast uses the prior month's published value. Revised-vintage evaluation does not recreate release lags."
        )
    elif method == "simulation":
        if not np.isfinite(values[-1]):
            raise ValueError("The last month must have an observation")
        rng = np.random.default_rng(study.seed)
        paths = values[-1] + rng.normal(
            study.monthly_change, study.shock_sd, size=(2000, study.horizon)
        ).cumsum(axis=1)
        upper = 100 if study.source in {"cps", "laus"} else np.inf
        paths = np.clip(paths, 0, upper)
        result = {
            "paths": len(paths),
            "horizon_months": study.horizon,
            "terminal_p05": float(np.quantile(paths[:, -1], 0.05)),
            "terminal_median": float(np.median(paths[:, -1])),
            "terminal_p95": float(np.quantile(paths[:, -1], 0.95)),
        }
        assumptions.append(
            "Changes and shock scale are scenario inputs. Gaussian paths are clipped to the source unit's feasible range. Percentiles describe simulations."
        )
    else:
        result = {"identification_status": "unsupported", "estimate": None}
        assumptions.extend(
            [
                "The public pilot contains single-series releases.",
                "A treated/control panel and a defensible timing and identification strategy are required.",
            ]
        )
    artifact = {
        "engine": "socrates-notebook-v1",
        "specification": study.model_dump(),
        "source": manifest["source_url"],
        "dataset_checksum": checksum,
        "coverage": {
            "first": rows[0][0],
            "last": rows[-1][0],
            "rows": len(rows),
            "missing": len(rows) - len(observed),
        },
        "inference": "identification_unsupported"
        if method == "causal-diagnostics"
        else method,
        "libraries": {
            name: version(name) for name in ("duckdb", "numpy", "scikit-learn")
        },
        "assumptions": assumptions,
        "result": result,
    }
    fingerprint = hashlib.sha256(
        json.dumps(artifact, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    return {"run_id": fingerprint, **artifact}
