"""Acquire the comparable annual ILO-modeled unemployment indicator."""

import json
from datetime import UTC, datetime
from urllib.request import build_opener

from pipelines.ingest import ROOT, NoRedirect, digest, write_once

GEO = {
    "USA": "United States",
    "CAN": "Canada",
    "MEX": "Mexico",
    "DEU": "Germany",
    "GBR": "United Kingdom",
    "JPN": "Japan",
    "WLD": "World",
}
YEARS = range(2015, 2026)
INDICATORS = {
    "SL.UEM.TOTL.ZS": ("Unemployment rate", "Percent of total labor force"),
    "SL.TLF.CACT.ZS": (
        "Labor force participation rate",
        "Percent of population ages 15 and older",
    ),
    "SL.EMP.TOTL.SP.ZS": (
        "Employment-to-population ratio",
        "Percent of population ages 15 and older",
    ),
}


def normalize(raw: bytes, code: str):
    metadata, items = json.loads(raw)
    if metadata["pages"] != 1 or metadata["total"] != len(items):
        raise ValueError("Incomplete World Bank response")
    records = {}
    for item in items:
        key = item["countryiso3code"], int(item["date"])
        value = item["value"]
        if (
            item["indicator"]["id"] != code
            or key[0] not in GEO
            or key[1] not in YEARS
            or key in records
        ):
            raise ValueError(f"Unexpected or duplicate record: {key}")
        if value is not None and (
            type(value) not in (int, float) or not 0 <= value <= 100
        ):
            raise ValueError(f"Invalid unemployment rate: {value}")
        records[key] = value
    expected = {(geo, year) for geo in GEO for year in YEARS}
    if records.keys() != expected:
        raise ValueError("Unexpected geographical or temporal coverage")
    return metadata["lastupdated"], [
        {
            "code": geo,
            "name": GEO[geo],
            "values": [{"year": year, "value": records[geo, year]} for year in YEARS],
        }
        for geo in GEO
    ]


def acquire(code: str):
    label, unit = INDICATORS[code]
    url = f"https://api.worldbank.org/v2/country/{';'.join(GEO)}/indicator/{code}?format=json&date=2015:2025&per_page=1000"
    with build_opener(NoRedirect()).open(url, timeout=20) as response:
        raw = response.read(250_001)
    if len(raw) > 250_000:
        raise ValueError("World Bank response exceeded byte limit")
    updated, series = normalize(raw, code)
    sha = digest(raw)
    write_once(ROOT / "data" / "reproduction" / f"{sha}.json", raw)
    result = {
        "version": sha,
        "source": f"https://data.worldbank.org/indicator/{code}",
        "source_url": url,
        "source_updated": updated,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "indicator": code,
        "label": label,
        "license": "CC BY 4.0",
        "inference": "modeled_estimate",
        "frequency": "annual",
        "unit": unit,
        "series": series,
    }
    return result


def main():
    target = ROOT / "apps" / "web" / "app" / "global-releases.json"
    existing = (
        {r["version"]: r for r in json.loads(target.read_text())}
        if target.exists()
        else {}
    )
    releases = [acquire(code) for code in INDICATORS]
    for release in releases:
        previous = existing.get(release["version"])
        if previous:
            release["retrieved_at"] = previous["retrieved_at"]
        print(
            json.dumps(
                {k: v for k, v in release.items() if k != "series"}
                | {"rows": len(GEO) * len(YEARS)}
            )
        )
    target.write_text(json.dumps(releases, indent=2) + "\n")


if __name__ == "__main__":
    main()
