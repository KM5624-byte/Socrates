import csv
import io
import json
from pathlib import Path

from aileo.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]


def test_openapi_contract():
    assert app.openapi() == json.loads(
        (ROOT / "packages/api-client/openapi.json").read_text()
    )


def test_health_and_validated_catalog():
    assert client.get("/readyz").status_code == 200
    response = client.get("/api/v1/datasets")
    assert response.headers["x-request-id"]
    integrated = {
        s["source_id"] for s in response.json() if s["retrieval_status"] == "Validated"
    }
    assert {"cps", "laus", "jolts"} <= integrated
    assert "aclu-tracker" not in integrated


def test_series_csv_and_lineage():
    series = client.get("/api/v1/employment/laus?start=2023-07&end=2023-08").json()
    version = series["release"]["version"]
    assert series["inference"] == "published_estimate"
    assert series["source"]["geographic_coverage"] == "New York County, NY"
    assert [row["month"] for row in series["observations"]] == ["2023-07", "2023-08"]
    assert client.get(series["source"]["lineage_reference"]).json() == series["release"]
    download = client.get(
        f"/api/v1/employment/laus/csv?start=2023-07&end=2023-08&version={version}"
    )
    rows = list(csv.DictReader(io.StringIO(download.text)))
    assert [r["dataset_version"] for r in rows] == [version, version]
    assert [float(r["value"]) for r in rows] == [
        r["value"] for r in series["observations"]
    ]


def test_invalid_queries_and_empty_window():
    assert client.get("/api/v1/employment/unknown").status_code == 404
    assert client.get("/api/v1/employment/laus?start=2023-99").status_code == 422
    assert (
        client.get("/api/v1/employment/laus?start=2024-01&end=2023-01").status_code
        == 422
    )
    assert (
        client.get("/api/v1/employment/laus?end=1920-01").json()["observations"] == []
    )


def test_policy_milestones_are_distinct():
    response = client.get("/api/v1/policy-events?jurisdiction=New+York+City")
    events = {event["id"]: event for event in response.json()}
    assert events["ll144-effective"]["date"] == "2023-01-01"
    assert events["ll144-enforcement"]["date"] == "2023-07-05"
    assert (
        events["ll144-rule"]["source_url"] != events["ll144-enforcement"]["source_url"]
    )
    assert client.get("/api/v1/policy-events?jurisdiction=Other").json() == []


def test_occupations_search_paginates_and_keeps_attribution():
    response = client.get("/api/v1/occupations?q=11-1011&limit=1")
    assert response.status_code == 200
    page = response.json()
    assert page["items"][0]["title"] == "Chief Executives"
    assert page["release"]["rows"] == 1016
    assert "U.S. Department of Labor" in page["source"]["attribution"]
    assert client.get("/api/v1/occupations?q=11-1011.00&offset=1").json()["items"] == []
    assert client.get("/api/v1/employment/onet").status_code == 404
