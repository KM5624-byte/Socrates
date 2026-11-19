"""Serialize the verified API pilot for Vercel's read-only fallback."""

import json
from pathlib import Path

from aileo.main import datasets, policy_events, series_data

root = Path(__file__).resolve().parents[1]
catalog = datasets()
snapshot = {
    "catalog": [item.model_dump(mode="json") for item in catalog],
    "events": [event.model_dump(mode="json") for event in policy_events()],
    "series": {
        source.source_id: series_data(source.source_id, None, None, None).model_dump(mode="json")
        for source in catalog
        if source.series_id and source.dataset_version
    },
}
(root / "apps/web/app/release-snapshot.json").write_text(
    json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
)
