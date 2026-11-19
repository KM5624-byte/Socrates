# %% [markdown]
# # National unemployment · release profile and persistence benchmark
#
# **Question.** How complete is the pinned national unemployment release, and
# how large were the errors of a one-month persistence forecast over 2024?
#
# **Input.** BLS CPS seasonally adjusted national unemployment rate LNS14000000.
# Pin a content-addressed Gold release and verify its checksum before analysis.
#
# **Method.** Profile coverage, missingness, and levels. For each of the final
# twelve months, forecast the latest available prior month's value and compute
# MAE and RMSE in percentage points. This rolling-origin benchmark updates
# its input each month and requires regular, non-missing monthly observations.
#
# **Limitations.** Evaluated against a single revised vintage, with no
# real-time publication lag reconstruction. The errors measure performance
# in this interval. This benchmark contains no uncertainty interval and
# does not identify policy effects.
#
# **Reproduction.** Run from the repository root using the research environment.
# The README provides the Jupytext and Papermill commands.

# %% tags=["parameters"]
source_id = "cps"
dataset_version = "a58072605e4eaf36ecbb6386a14a9c1c18796fd638f8cdb2d76c8a1657a32f4a"
holdout = 12

# %%
import hashlib
import json
import platform
import re
from pathlib import Path

import duckdb
import pandas as pd
from IPython.display import display

from research.baselines import persistence

assert re.fullmatch(r"[a-z]+", source_id)
assert re.fullmatch(r"[0-9a-f]{64}", dataset_version)
folder = Path("data/releases") / source_id / dataset_version
manifest = json.loads((folder / "manifest.json").read_text())
series_file = folder / "series.parquet"
assert manifest["version"] == dataset_version
assert hashlib.sha256(series_file.read_bytes()).hexdigest() == manifest["gold_checksum"]

with duckdb.connect(config={"threads": 1}) as db:
    frame = db.execute(
        "SELECT month, value FROM read_parquet(?) ORDER BY month", [str(series_file)]
    ).df()
missing = int(frame.value.isna().sum())
print(
    json.dumps(
        {
            "release": dataset_version,
            "months": len(frame),
            "missing": missing,
            "first": frame.month.min(),
            "last": frame.month.max(),
        },
        indent=2,
    )
)
display(frame.value.describe())

# %%
months = pd.PeriodIndex(frame.month, freq="M")
assert months.equals(pd.period_range(months.min(), months.max(), freq="M"))
assert missing == 0
result = persistence(frame.value.tolist(), holdout) | {
    "implementation": "persistence-v1",
    "dataset_version": dataset_version,
    "python": platform.python_version(),
    "unit": "percentage points" if source_id in {"cps", "laus"} else "thousands",
    "evaluation_start": frame.month.iloc[-holdout],
    "evaluation_end": frame.month.iloc[-1],
}
print(json.dumps(result, indent=2))
if source_id == "cps" and holdout == 12 and dataset_version.startswith("a5807260"):
    assert abs(result["mae"] - 0.075) < 1e-10
    assert abs(result["rmse"] - 0.1040832999733067) < 1e-10
