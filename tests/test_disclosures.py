import pytest
from pydantic import ValidationError

from research.disclosures import DisclosureCapture, summarize


def capture(capture_id, availability, status=None):
    return DisclosureCapture.model_validate(
        {
            "capture_id": capture_id,
            "report_url": "https://example.invalid/audit",
            "captured_on": "2024-01-01",
            "availability": availability,
            "reviewer_id": "test",
            "attributes": {
                "methodology": {"status": status, "locator": "Review scope: pp. 1–3"}
            }
            if status
            else {},
        }
    )


def test_access_and_field_denominators_differ():
    items = [
        capture("1", "accessible", "present"),
        capture("2", "accessible", "absent_after_review"),
        capture("3", "inaccessible"),
        capture("4", "accessible", "not_reviewed"),
    ]
    result = summarize(items, "methodology")
    assert (result["accessible"], result["reviewed"], result["present_share"]) == (
        3,
        2,
        0.5,
    )
    assert summarize(items, "demographics")["present_share"] is None
    with pytest.raises(ValueError, match="at most once"):
        summarize(items + items[:1], "methodology")


def test_inaccessible_record_cannot_assert_absence():
    with pytest.raises(ValidationError, match="accessible document"):
        capture("1", "inaccessible", "absent_after_review")
