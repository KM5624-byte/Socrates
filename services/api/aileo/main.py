import csv
import io
import json
import logging
from time import perf_counter
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Response

from . import repository as repo
from .contracts import Occupations, PolicyEvent, Release, Series, Source

app = FastAPI(title="AILEO Research Data API", version="0.1.0")
logger = logging.getLogger("uvicorn.error")
Month = Annotated[str | None, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]
Version = Annotated[str | None, Query(pattern=r"^[a-f0-9]{64}$")]


@app.middleware("http")
async def request_context(request, call_next):
    request_id = str(uuid4())
    start = perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    logger.info(
        json.dumps(
            {
                "request_id": request_id,
                "route": getattr(request.scope.get("route"), "path", "unmatched"),
                "status": response.status_code,
                "duration_ms": round((perf_counter() - start) * 1000, 1),
            }
        )
    )
    return response


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/readyz")
def readiness():
    try:
        for source in repo.sources().values():
            if source.series_id or source.source_id == "onet":
                release = select_release(source.source_id, None)
                repo.verified_path(
                    release.source_id,
                    release.version,
                    release.gold_checksum,
                    release.artifact,
                )
        repo.policy_events()
    except (OSError, ValueError, HTTPException) as error:
        logger.error("Release readiness failed: %s", error)
        raise HTTPException(503, "Release assets unavailable") from None
    return {"status": "ready"}


def require_source(source_id: str):
    if source_id not in repo.sources():
        raise HTTPException(404, "Unknown source")
    return repo.sources()[source_id]


def select_release(source_id: str, version: str | None):
    require_source(source_id)
    for release in repo.versions(source_id):
        if version is None or version == release.version:
            return release
    raise HTTPException(404, "Dataset release unavailable")


@app.get("/api/v1/datasets", response_model=list[Source])
def datasets():
    return [
        repo.source_with_release(
            source, next(iter(repo.versions(source.source_id)), None)
        )
        for source in repo.sources().values()
    ]


@app.get("/api/v1/datasets/{source_id}/releases", response_model=list[Release])
def releases(source_id: str):
    require_source(source_id)
    return repo.versions(source_id)


@app.get("/api/v1/datasets/{source_id}/releases/{version}", response_model=Release)
def release(source_id: str, version: str):
    return select_release(source_id, version)


@app.get("/api/v1/policy-events", response_model=list[PolicyEvent])
def policy_events(jurisdiction: Annotated[str | None, Query(max_length=100)] = None):
    return [
        event
        for event in repo.policy_events()
        if jurisdiction is None or event.jurisdiction == jurisdiction
    ]


def series_data(
    source_id: str, version: str | None, start: str | None, end: str | None
):
    if start and end and start > end:
        raise HTTPException(422, "Start month must precede or equal end month")
    source = require_source(source_id)
    if not source.series_id:
        raise HTTPException(404, "Monthly series unavailable")
    manifest = select_release(source_id, version)
    return Series(
        source=repo.source_with_release(source, manifest),
        release=manifest,
        observations=repo.observations(manifest, start, end),
    )


@app.get("/api/v1/employment/{source_id}", response_model=Series)
def employment(
    source_id: str, version: Version = None, start: Month = None, end: Month = None
):
    return series_data(source_id, version, start, end)


@app.get(
    "/api/v1/employment/{source_id}/csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def employment_csv(
    source_id: str, version: Version = None, start: Month = None, end: Month = None
):
    data = series_data(source_id, version, start, end)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["month", "value", "unit", "dataset_version", "footnotes"])
    for row in data.observations:
        footnotes = " | ".join(row.footnotes)
        if footnotes.lstrip().startswith(("=", "+", "-", "@")) or footnotes.startswith(
            ("\t", "\r", "\n")
        ):
            footnotes = "'" + footnotes
        writer.writerow(
            [row.month, row.value, data.source.unit, data.release.version, footnotes]
        )
    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{source_id}-{data.release.version[:12]}.csv"'
        },
    )


@app.get("/api/v1/occupations", response_model=Occupations)
def occupations(
    q: Annotated[str, Query(max_length=100)] = "",
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    version: Version = None,
):
    manifest = select_release("onet", version)
    return Occupations(
        release=manifest,
        source=repo.source_with_release(require_source("onet"), manifest),
        items=repo.occupations(manifest, q.strip(), offset, limit),
        offset=offset,
        limit=limit,
    )
