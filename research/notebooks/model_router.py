# %% [markdown]
# # Socrates · model routing
#
# Execute a pre-approved method on a pinned release. The exported run records
# the engine, library versions, source checksum, parameters and limitations.
# Methods include descriptive summaries, endpoint changes, Ridge forecasting
# against persistence, seeded Monte Carlo scenarios and causal coverage checks.
# The pilot's single-series releases support no causal effect estimate.
#
# Reproduce from the repository root using scripts/reproduce-notebook.

# %% tags=["parameters"]
source = "cps"
release = "a58072605e4eaf36ecbb6386a14a9c1c18796fd638f8cdb2d76c8a1657a32f4a"
method = "predictive"
holdout = 12
seed = 42
monthly_change = 0.0
shock_sd = 0.1
horizon = 12

# %%
import json

from research.engine import Study, run

result = run(
    Study(
        source=source,
        release=release,
        method=method,
        holdout=holdout,
        seed=seed,
        monthly_change=monthly_change,
        shock_sd=shock_sd,
        horizon=horizon,
    )
)
print(json.dumps(result, indent=2))
