# %% [markdown]
# # NYC Local Law 144 · policy and outcome coverage
#
# **Question.** Which curated policy events fall inside the pinned New York
# County unemployment series, and what can this alignment support?
#
# **Input.** Source-linked policy events from the Git checkout and BLS LAUS
# vintage pinned below. The series represents residents of one NYC borough.
#
# **Method.** Verify the artifact hash and intersect each event month with
# published observations. Assess geographical and comparison-group support.
#
# **Limitations.** Date overlap provides descriptive context. This setup
# has a geography mismatch and lacks a defensible comparison group.
# It yields no causal estimate.
#
# **Reproduction.** Use scripts/reproduce-notebook from the repository root.

# %% tags=["parameters"]
version = "8dd0f0c25c074473bfdcf926f983539a81c0d81d7947026cd18af49c03f02468"

# %%
import hashlib
import json
import re
from pathlib import Path

import duckdb

assert re.fullmatch(r"[0-9a-f]{64}", version)
dataset = Path("data/releases/laus") / version
manifest = json.loads((dataset / "manifest.json").read_text())
assert manifest["version"] == version
artifact = dataset / "series.parquet"
assert hashlib.sha256(artifact.read_bytes()).hexdigest() == manifest["gold_checksum"]
reference = Path("data/registry/policy-events.json").read_bytes()
events = json.loads(reference)
with duckdb.connect(config={"threads": 1}) as db:
    months = {
        row[0]
        for row in db.execute(
            "SELECT month FROM read_parquet(?) WHERE value IS NOT NULL", [str(artifact)]
        ).fetchall()
    }
diagnostics = {
    "release": version,
    "policy_registry_sha256": hashlib.sha256(reference).hexdigest(),
    "timing_overlap": {
        event["id"]: event["date"][:7] in months
        for event in events
        if event["jurisdiction"] == "New York City"
    },
    "policy_geography": "New York City",
    "outcome_geography": "New York County, NY",
    "matched_geography": False,
    "comparison_design": None,
    "identification_status": "unsupported",
}
print(json.dumps(diagnostics, indent=2))
assert diagnostics["timing_overlap"]["ll144-enforcement"]
