import json
from pathlib import Path

from pipelines.ingest import digest
from pipelines.worldbank import GEO, YEARS, normalize

ROOT = Path(__file__).resolve().parents[1]


def test_world_bank_pinned_releases_replay():
    releases = json.loads((ROOT / "apps/web/app/global-releases.json").read_text())
    assert len(releases) == 3
    for release in releases:
        sha = release["version"]
        raw = (ROOT / "data/reproduction" / f"{sha}.json").read_bytes()
        updated, series = normalize(raw, release["indicator"])
        assert digest(raw) == sha
        assert updated == release["source_updated"]
        assert series == release["series"]
        assert sum(len(item["values"]) for item in series) == len(GEO) * len(YEARS)
