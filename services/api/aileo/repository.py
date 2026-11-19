import hashlib
import json
import os
import re
from functools import lru_cache
from pathlib import Path

import duckdb

from .contracts import Observation, Occupation, PolicyEvent, Release, Source

ROOT = Path(__file__).resolve().parents[3] / "data"
RELEASES = Path(os.environ.get("AILEO_RELEASES_DIR", ROOT / "releases"))
SHA256 = re.compile(r"[0-9a-f]{64}")


@lru_cache(maxsize=1)
def sources():
    return {
        item.source_id: item
        for item in map(
            Source.model_validate,
            json.loads((ROOT / "registry/sources.json").read_text()),
        )
    }


def versions(source_id: str):
    manifests = []
    for folder in (RELEASES / source_id).glob("*"):
        path = folder / "manifest.json"
        if not SHA256.fullmatch(folder.name) or not path.is_file():
            continue
        release = Release.model_validate_json(path.read_bytes())
        if release.source_id != source_id or release.version != folder.name:
            raise ValueError(f"Manifest identity mismatch: {path}")
        manifests.append(release)
    return sorted(
        manifests, key=lambda item: (item.retrieved_at, item.version), reverse=True
    )


def source_with_release(source: Source, release: Release | None):
    if release is None:
        return source
    return source.model_copy(
        update={
            "retrieval_status": "Validated",
            "dataset_version": release.version,
            "temporal_coverage": f"{release.first_month} to {release.last_month}",
            "last_successful_sync": release.retrieved_at,
            "last_checked_at": release.retrieved_at,
            "source_checksum": release.source_checksum,
            "lineage_reference": f"/api/v1/datasets/{source.source_id}/releases/{release.version}",
        }
    )


@lru_cache(maxsize=64)
def verified_path(
    source_id: str, version: str, checksum: str, artifact: str = "series.parquet"
):
    path = RELEASES / source_id / version / artifact
    if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
        raise ValueError("Gold artifact checksum mismatch")
    return str(path)


def observations(release: Release, start: str | None, end: str | None):
    path = verified_path(release.source_id, release.version, release.gold_checksum)
    with duckdb.connect(config={"threads": 1}) as db:
        rows = db.execute(
            """SELECT month, value, footnotes FROM read_parquet(?)
               WHERE month >= ? AND month <= ? ORDER BY month""",
            [path, start or release.first_month, end or release.last_month],
        ).fetchall()
    return [
        Observation(month=month, value=value, footnotes=notes)
        for month, value, notes in rows
    ]


@lru_cache(maxsize=1)
def policy_events():
    return [
        PolicyEvent.model_validate(item)
        for item in json.loads((ROOT / "registry/policy-events.json").read_text())
    ]


def occupations(release: Release, query: str, offset: int, limit: int):
    path = verified_path(
        release.source_id, release.version, release.gold_checksum, release.artifact
    )
    with duckdb.connect(config={"threads": 1}) as db:
        rows = db.execute(
            """SELECT code, title, description FROM read_parquet(?)
               WHERE contains(lower(title), lower(?)) OR contains(code, ?)
               ORDER BY code LIMIT ? OFFSET ?""",
            [path, query, query, limit, offset],
        ).fetchall()
    return [
        Occupation(code=code, title=title, description=description)
        for code, title, description in rows
    ]
