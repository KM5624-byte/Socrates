"""Ingest explicitly registered BLS series and write content-addressed releases."""

import argparse
import hashlib
import json
import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, build_opener

import polars as pl
from pydantic import BaseModel, Field, FiniteFloat

ROOT = Path(__file__).resolve().parents[1]
TRANSFORMATION = "bls-monthly-v1"
LIMIT = 2_000_000
logger = logging.getLogger(__name__)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(req.full_url, code, "Redirect refused", headers, fp)


class BLSRow(BaseModel):
    year: str = Field(pattern=r"^\d{4}$")
    period: str = Field(pattern=r"^M(0[1-9]|1[0-3])$")
    value: str
    footnotes: list[dict]


class MonthlyRow(BaseModel):
    month: str
    value: FiniteFloat | None = Field(ge=0)
    footnotes: list[str]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(raw: bytes, series_id: str, start: int, end: int, unit: str):
    payload = json.loads(raw)
    warnings = payload.get("message") or []
    catalog_warning = f"Unable to get Catalog Data for series {series_id}"
    if payload["status"] != "REQUEST_SUCCEEDED" or any(
        note != catalog_warning for note in warnings
    ):
        raise ValueError(f"BLS refused or returned warnings: {payload.get('message')}")
    series = payload["Results"]["series"]
    if len(series) != 1 or series[0]["seriesID"] != series_id:
        raise ValueError("Unexpected series in response")
    rows = {}
    for record in series[0]["data"]:
        row = BLSRow.model_validate(record)
        if not start <= int(row.year) <= end:
            raise ValueError("Unexpected observation year")
        if row.period == "M13":
            continue
        month = f"{row.year}-{row.period[1:]}"
        if month in rows:
            raise ValueError(f"Duplicate period {month}")
        notes = [f["text"] for f in row.footnotes if f.get("text")]
        value = None if row.value in {"-", "—", ""} else row.value
        rows[month] = MonthlyRow(month=month, value=value, footnotes=notes)
        if (
            unit == "percent"
            and rows[month].value is not None
            and rows[month].value > 100
        ):
            raise ValueError("Percentage outside expected bounds")
    if not any(row.value is not None for row in rows.values()):
        raise ValueError("No numerical monthly observations")
    periods = [
        f"{year}-{month:02}" for year in range(start, end + 1) for month in range(1, 13)
    ]
    return [
        rows.get(
            month,
            MonthlyRow(
                month=month, value=None, footnotes=["Absent from source response"]
            ),
        ).model_dump()
        for month in periods
    ]


def write_once(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent) as temp:
        temp.write(content)
        temp.flush()
        try:
            os.link(temp.name, path)
        except FileExistsError:
            if path.read_bytes() != content:
                raise ValueError(f"Immutable artifact differs at {path}")


def ingest(
    source: dict, start: int, end: int, lake: Path, releases: Path, *, rolling=False
):
    code = source["series_id"]
    url = f"https://api.bls.gov/publicAPI/v2/timeseries/data/{code}?startyear={start}&endyear={end}"
    with build_opener(NoRedirect()).open(url, timeout=20) as response:
        raw = response.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError("Source response exceeded byte limit")
    retrieved = datetime.now(UTC).isoformat()
    raw_hash = digest(raw)
    source_id = source["source_id"]
    write_once(lake / "bronze" / source_id / f"{raw_hash}.json", raw)
    rows = normalize(raw, code, start, end, source["unit"])
    if rolling:
        while rows and rows[-1]["footnotes"] == ["Absent from source response"]:
            rows.pop()
        manifests = [
            json.loads(path.read_text())
            for path in (releases / source_id).glob("*/manifest.json")
        ]
        newest = max(manifests, key=lambda item: item["retrieved_at"], default=None)
        if newest and rows[-1]["month"] < newest["last_month"]:
            raise ValueError("Publisher response regressed to an older reporting month")
    silver = json.dumps(rows, sort_keys=True).encode()
    silver_hash = digest(silver)
    if rolling and newest and newest["silver_checksum"] == silver_hash:
        logger.info(json.dumps({"event": "bls_unchanged", "source_id": source_id}))
        return newest
    write_once(lake / "silver" / source_id / f"{silver_hash}.json", silver)
    with tempfile.TemporaryDirectory() as path:
        target = Path(path) / "series.parquet"
        pl.DataFrame(
            rows,
            schema={
                "month": pl.String,
                "value": pl.Float64,
                "footnotes": pl.List(pl.String),
            },
        ).write_parquet(target)
        parquet = target.read_bytes()
    parquet_hash = digest(parquet)
    version = digest(
        f"{source_id}:{raw_hash}:{silver_hash}:{parquet_hash}:{TRANSFORMATION}".encode()
    )
    manifest = {
        "source_id": source_id,
        "version": version,
        "source_url": url,
        "retrieved_at": retrieved,
        "source_checksum": raw_hash,
        "silver_checksum": silver_hash,
        "gold_checksum": parquet_hash,
        "transformation": TRANSFORMATION,
        "first_month": rows[0]["month"],
        "last_month": rows[-1]["month"],
        "rows": len(rows),
        "missing": sum(row["value"] is None for row in rows),
    }
    if rolling:
        write_once(ROOT / "data/reproduction" / f"{raw_hash}.json", raw)
    folder = releases / source_id / version
    write_once(folder / "series.parquet", parquet)
    try:
        write_once(
            folder / "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode()
        )
    except ValueError:
        existing = json.loads((folder / "manifest.json").read_text())
        if {**existing, "retrieved_at": retrieved} != manifest:
            raise
        manifest = existing
    logger.info(json.dumps({"event": "bls_validated", **manifest}))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", choices=["cps", "laus", "jolts"])
    parser.add_argument("--start", type=int, default=2022)
    parser.add_argument("--end", type=int, default=2024)
    parser.add_argument("--rolling", action="store_true")
    parser.add_argument("--lake", type=Path, default=ROOT / ".lake")
    parser.add_argument("--releases", type=Path, default=ROOT / "data/releases")
    args = parser.parse_args()
    if (
        not 1900 <= args.start <= args.end <= datetime.now(UTC).year
        or args.end - args.start >= 10
    ):
        parser.error("Provide an ascending range of up to ten years")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    registry = {
        s["source_id"]: s
        for s in json.loads((ROOT / "data/registry/sources.json").read_text())
    }
    failed = False
    for source_id in dict.fromkeys(args.sources):
        try:
            ingest(
                registry[source_id],
                args.start,
                args.end,
                args.lake,
                args.releases,
                rolling=args.rolling,
            )
        except (OSError, ValueError, KeyError, TypeError) as error:
            logger.error(
                json.dumps(
                    {"event": "bls_failed", "source_id": source_id, "error": str(error)}
                )
            )
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
