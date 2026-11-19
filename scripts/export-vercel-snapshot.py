"""Serialize the verified API pilot for Vercel's read-only fallback."""

import json
from pathlib import Path

from aileo import repository
from aileo.main import datasets, policy_events, series_data

root = Path(__file__).resolve().parents[1]
catalog = datasets()
snapshot = {
    "catalog": [item.model_dump(mode="json") for item in catalog],
    "events": [event.model_dump(mode="json") for event in policy_events()],
    "history": {
        source.source_id: {
            release.version: series_data(
                source.source_id, release.version, None, None
            ).model_dump(mode="json")
            for release in repository.versions(source.source_id)
            if release.version != source.dataset_version
        }
        for source in catalog
        if source.series_id and source.dataset_version
    },
    "series": {
        source.source_id: series_data(source.source_id, None, None, None).model_dump(
            mode="json"
        )
        for source in catalog
        if source.series_id and source.dataset_version
    },
}
(root / "apps/web/app/release-snapshot.json").write_text(
    json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
)
