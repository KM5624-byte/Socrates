import hashlib
import json
from pathlib import Path

import pytest

from pipelines.ingest import normalize, write_once

ROOT = Path(__file__).resolve().parents[1]


def test_pinned_bronze_replays_silver():
    registry = {
        s["source_id"]: s
        for s in json.loads((ROOT / "data/registry/sources.json").read_text())
    }
    for log in (ROOT / "data/manifests/pilot-ingestion.jsonl").read_text().splitlines():
        report = json.loads(log)
        raw = (
            ROOT / f"data/reproduction/{report['source_checksum']}.json"
        ).read_bytes()
        source = registry[report["source_id"]]
        rows = normalize(raw, source["series_id"], 2022, 2024, source["unit"])
        assert hashlib.sha256(raw).hexdigest() == report["source_checksum"]
        assert (
            hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
            == report["silver_checksum"]
        )
        assert len(rows) == 36
        assert all(row["value"] is not None for row in rows)


def payload(rows):
    return json.dumps(
        {
            "status": "REQUEST_SUCCEEDED",
            "Results": {
                "series": [
                    {"seriesID": "TEST", "data": rows},
                ]
            },
        }
    ).encode()


def test_absent_and_placeholder_are_missing():
    rows = normalize(
        payload(
            [
                {"year": "2024", "period": "M01", "value": "3.4", "footnotes": [{}]},
                {
                    "year": "2024",
                    "period": "M02",
                    "value": "-",
                    "footnotes": [{"text": "Suppressed"}],
                },
            ]
        ),
        "TEST",
        2024,
        2024,
        "percent",
    )
    assert rows[0]["value"] == 3.4
    assert rows[1] == {"month": "2024-02", "value": None, "footnotes": ["Suppressed"]}
    assert rows[2]["value"] is None


def test_duplicate_rejected():
    row = {"year": "2024", "period": "M01", "value": "3.4", "footnotes": []}
    with pytest.raises(ValueError, match="Duplicate period"):
        normalize(payload([row, row]), "TEST", 2024, 2024, "percent")


def test_revisions_cannot_overwrite_artifacts(tmp_path):
    path = tmp_path / "artifact"
    write_once(path, b"original")
    write_once(path, b"original")
    with pytest.raises(ValueError, match="Immutable"):
        write_once(path, b"revision")
    assert path.read_bytes() == b"original"
