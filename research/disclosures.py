"""Protocol primitives for evidence-backed review of public audit summaries."""

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, model_validator


class Finding(StrEnum):
    PRESENT = "present"
    ABSENT = "absent_after_review"
    UNAVAILABLE = "unavailable"
    UNREVIEWED = "not_reviewed"


class AttributeReview(BaseModel):
    status: Finding
    locator: str | None = Field(default=None, min_length=1, max_length=2000)

    @model_validator(mode="after")
    def examined_scope(self):
        if (
            self.status in {Finding.PRESENT, Finding.ABSENT}
            and not (self.locator or "").strip()
        ):
            raise ValueError("Document evidence locator or reviewed scope required")
        return self


class DisclosureCapture(BaseModel):
    report_url: HttpUrl
    captured_on: date
    capture_id: str = Field(min_length=1)
    availability: Literal["accessible", "inaccessible", "unknown"]
    reviewer_id: str = Field(min_length=1)
    attributes: dict[
        Literal[
            "employer",
            "tool_or_vendor",
            "audit_date",
            "methodology",
            "demographics",
            "result_fields",
        ],
        AttributeReview,
    ]

    @model_validator(mode="after")
    def observed_evidence_requires_access(self):
        reviewed = {Finding.PRESENT, Finding.ABSENT}
        if self.availability != "accessible" and any(
            field.status in reviewed for field in self.attributes.values()
        ):
            raise ValueError("Reviewed attributes require an accessible document")
        return self


def summarize(captures: list[DisclosureCapture], attribute: str) -> dict:
    if len({capture.capture_id for capture in captures}) != len(captures):
        raise ValueError("Each capture must appear at most once")
    findings = [
        capture.attributes[attribute].status
        for capture in captures
        if attribute in capture.attributes
    ]
    present = findings.count(Finding.PRESENT)
    absent = findings.count(Finding.ABSENT)
    return {
        "captures": len(captures),
        "accessible": sum(c.availability == "accessible" for c in captures),
        "inaccessible": sum(c.availability == "inaccessible" for c in captures),
        "reviewed": present + absent,
        "present": present,
        "absent_after_review": absent,
        "present_share": present / (present + absent) if present + absent else None,
    }
