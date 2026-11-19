import pytest

from research.engine import Study, run

PIN = "a58072605e4eaf36ecbb6386a14a9c1c18796fd638f8cdb2d76c8a1657a32f4a"


@pytest.mark.parametrize(
    "method",
    ["descriptive", "deterministic", "predictive", "simulation", "causal-diagnostics"],
)
def test_routes_pinned_releases_reproducibly(method):
    study = Study(source="cps", release=PIN, method=method)
    first = run(study)
    assert first == run(study)
    assert first["coverage"]["rows"] == 36
    if method == "predictive":
        assert first["result"]["evaluation_start"] == "2024-01"
        assert first["result"]["persistence_baseline"]["mae"] == pytest.approx(0.075)
    if method == "causal-diagnostics":
        assert first["result"]["estimate"] is None
    if method == "simulation":
        assert first["result"]["terminal_p05"] <= first["result"]["terminal_p95"]
