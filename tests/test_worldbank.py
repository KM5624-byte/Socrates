import json
from pathlib import Path

from pipelines.ingest import digest
from pipelines.worldbank import GEO, normalize

ROOT = Path(__file__).resolve().parents[1]


def test_world_bank_pinned_releases_replay():
    releases = json.loads((ROOT / "apps/web/app/global-releases.json").read_text())
    assert len(releases) == 3
    for release in releases:
        sha = release["version"]
        raw = (ROOT / "data/reproduction" / f"{sha}.json").read_bytes()
        expected_last = max(item["values"][-1]["year"] for item in release["series"])
        updated, series = normalize(
            raw, release["indicator"], range(2015, expected_last + 2)
        )
        for item in series:
            while item["values"] and item["values"][-1]["value"] is None:
                item["values"].pop()
        assert digest(raw) == sha
        assert updated == release["source_updated"]
        assert series == release["series"]
        assert len(series) == len(GEO)
