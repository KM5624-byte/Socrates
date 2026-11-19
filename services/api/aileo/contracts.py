from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class Release(BaseModel):
    source_id: str
    version: str
    source_url: str
    retrieved_at: datetime
    source_checksum: str
    silver_checksum: str
    gold_checksum: str
    transformation: str
    first_month: str
    last_month: str
    rows: int
    missing: int
    artifact: Literal["series.parquet", "occupations.parquet"] = "series.parquet"


class Source(BaseModel):
    source_id: str
    publisher: str
    canonical_url: str
    dataset_name: str
    dataset_version: str | None = None
    license: str
    access_method: str
    authentication_required: bool | None
    retrieval_status: str
    last_successful_sync: datetime | None = None
    last_checked_at: datetime | None = None
    next_scheduled_sync: datetime | None
    geographic_coverage: str
    temporal_coverage: str | None = None
    original_schema: str | None
    normalization_schema: str | None
    attribution: str
    known_limitations: str
    source_checksum: str | None = None
    lineage_reference: str | None = None
    series_id: str | None = None
    unit: str | None = None
    adjustment: str | None = None
    program: str | None = None
    methodology_url: str | None = None
    license_url: str | None = None


class Observation(BaseModel):
    month: str
    value: float | None
    footnotes: list[str]


class Series(BaseModel):
    inference: Literal["published_estimate"] = "published_estimate"
    source: Source
    release: Release
    observations: list[Observation]


class PolicyEvent(BaseModel):
    id: str
    instrument: str
    jurisdiction: str
    date: date
    kind: str
    summary: str
    source_url: str


class Occupation(BaseModel):
    code: str
    title: str
    description: str


class Occupations(BaseModel):
    release: Release
    source: Source
    items: list[Occupation]
    offset: int
    limit: int
