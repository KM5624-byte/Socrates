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
PILOT_YEARS = range(2015, 2026)
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


def normalize(raw: bytes, code: str, years=PILOT_YEARS):
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
            or key[1] not in years
            or key in records
        ):
            raise ValueError(f"Unexpected or duplicate record: {key}")
        if value is not None and (
            type(value) not in (int, float) or not 0 <= value <= 100
        ):
            raise ValueError(f"Invalid unemployment rate: {value}")
        records[key] = value
    if not records:
        raise ValueError("No annual data returned")
    years = range(years.start, max(year for _, year in records) + 1)
    expected = {(geo, year) for geo in GEO for year in years}
    if records.keys() != expected:
        raise ValueError("Unexpected geographical or temporal coverage")
    return metadata["lastupdated"], [
        {
            "code": geo,
            "name": GEO[geo],
            "values": [{"year": year, "value": records[geo, year]} for year in years],
        }
        for geo in GEO
    ]


def acquire(code: str, years):
    label, unit = INDICATORS[code]
    url = f"https://api.worldbank.org/v2/country/{';'.join(GEO)}/indicator/{code}?format=json&date={years.start}:{years.stop - 1}&per_page=1000"
    with build_opener(NoRedirect()).open(url, timeout=20) as response:
        raw = response.read(250_001)
    if len(raw) > 250_000:
        raise ValueError("World Bank response exceeded byte limit")
    updated, series = normalize(raw, code, years)
    sha = digest(raw)
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
    return result, raw


def main():
    target = ROOT / "apps" / "web" / "app" / "global-releases.json"
    existing = {r["indicator"]: r for r in json.loads(target.read_text())}
    years = range(PILOT_YEARS.start, datetime.now(UTC).year + 1)
    releases = []
    failed = False
    for code in INDICATORS:
        previous = existing[code]
        try:
            release, raw = acquire(code, years)
            for series, old_series in zip(
                release["series"], previous["series"], strict=True
            ):
                while series["values"] and series["values"][-1]["value"] is None:
                    series["values"].pop()
                if (
                    not series["values"]
                    or series["values"][-1]["year"] < old_series["values"][-1]["year"]
                ):
                    raise ValueError("World Bank coverage regressed")
            if release["series"] == previous["series"]:
                releases.append(previous)
                continue
            write_once(ROOT / "data/reproduction" / f"{release['version']}.json", raw)
            releases.append(release)
            print(
                json.dumps(
                    {
                        "event": "worldbank_validated",
                        **{k: v for k, v in release.items() if k != "series"},
                    }
                )
            )
        except (OSError, ValueError, KeyError, TypeError) as error:
            failed = True
            releases.append(previous)
            print(
                json.dumps(
                    {
                        "event": "worldbank_failed",
                        "indicator": code,
                        "error": str(error),
                    }
                )
            )
    target.write_text(json.dumps(releases, indent=2) + "\n")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
