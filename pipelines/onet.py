"""Acquire the O*NET 31.0 occupation definition table."""

import argparse
import csv
import io
import json
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import build_opener

import polars as pl

from pipelines.ingest import ROOT, NoRedirect, digest, write_once

URL = "https://www.onetcenter.org/dl_files/database/db_31_0_csv/occupation_data.csv"
FIELDS = ("O*NET-SOC Code", "Title", "Description")
LIMIT = 2_000_000


def normalize(raw: bytes):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError("Unexpected occupation schema")
    rows = []
    seen = set()
    for item in reader:
        code, title, description = (item[field] for field in FIELDS)
        if (
            None in item
            or not re.fullmatch(r"\d{2}-\d{4}\.\d{2}", code or "")
            or not title
            or not description
            or code in seen
        ):
            raise ValueError(f"Invalid or duplicate O*NET-SOC occupation: {code}")
        seen.add(code)
        rows.append({"code": code, "title": title, "description": description})
    if not rows:
        raise ValueError("No occupations returned")
    return sorted(rows, key=lambda row: row["code"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", type=Path, default=ROOT / ".lake")
    parser.add_argument("--releases", type=Path, default=ROOT / "data/releases")
    args = parser.parse_args()
    with build_opener(NoRedirect()).open(URL, timeout=20) as response:
        raw = response.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError("Source response exceeded byte limit")
    raw_hash = digest(raw)
    write_once(args.lake / "bronze" / "onet" / f"{raw_hash}.csv", raw)
    rows = normalize(raw)
    silver = json.dumps(rows, sort_keys=True).encode()
    silver_hash = digest(silver)
    write_once(args.lake / "silver" / "onet" / f"{silver_hash}.json", silver)
    with tempfile.TemporaryDirectory() as directory:
        file = Path(directory) / "occupations.parquet"
        pl.DataFrame(rows).write_parquet(file)
        parquet = file.read_bytes()
    gold_hash = digest(parquet)
    transform = "onet-occupations-v1"
    version = digest(f"onet:{raw_hash}:{silver_hash}:{gold_hash}:{transform}".encode())
    folder = args.releases / "onet" / version
    manifest = {
        "source_id": "onet",
        "version": version,
        "source_url": URL,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "source_checksum": raw_hash,
        "silver_checksum": silver_hash,
        "gold_checksum": gold_hash,
        "transformation": transform,
        "first_month": "2026-08",
        "last_month": "2026-08",
        "rows": len(rows),
        "missing": 0,
        "artifact": "occupations.parquet",
    }
    write_once(folder / "occupations.parquet", parquet)
    path = folder / "manifest.json"
    try:
        write_once(path, (json.dumps(manifest, indent=2) + "\n").encode())
    except ValueError:
        existing = json.loads(path.read_text())
        if {**existing, "retrieved_at": manifest["retrieved_at"]} != manifest:
            raise
        manifest = existing
    print(json.dumps({"event": "onet_validated", **manifest}))


if __name__ == "__main__":
    main()
