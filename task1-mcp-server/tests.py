import pytest
from pydantic import ValidationError

from models import ClaimRequest, ClaimStatusUpdateRequest


# -------------------------------------------------------------------
# Claim ID validation
# -------------------------------------------------------------------

def test_valid_claim_id():
    """A correctly formatted claim ID should be accepted."""

    request = ClaimRequest(
        claim_id="CLM-12345"
    )

    assert request.claim_id == "CLM-12345"


def test_invalid_claim_id_prefix():
    """The claim ID must begin with CLM-."""

    with pytest.raises(ValidationError):
        ClaimRequest(
            claim_id="CUST-12345"
        )


def test_invalid_claim_id_length():
    """The numeric portion must contain exactly five digits."""

    with pytest.raises(ValidationError):
        ClaimRequest(
            claim_id="CLM-1234"
        )


def test_invalid_claim_id_non_numeric():
    """Letters are not allowed in the numeric portion."""

    with pytest.raises(ValidationError):
        ClaimRequest(
            claim_id="CLM-ABCDE"
        )


# -------------------------------------------------------------------
# Claim status validation
# -------------------------------------------------------------------

def test_valid_claim_status():
    """A supported claim status should be accepted."""

    request = ClaimStatusUpdateRequest(
        claim_id="CLM-12345",
        status="APPROVED",
        reason="All required documents were verified",
    )

    assert request.status.value == "APPROVED"


def test_invalid_claim_status():
    """Unsupported statuses must be rejected."""

    with pytest.raises(ValidationError):
        ClaimStatusUpdateRequest(
            claim_id="CLM-12345",
            status="PENDING_PAYMENT",
            reason="All required documents were verified",
        )


# -------------------------------------------------------------------
# Reason validation
# -------------------------------------------------------------------

def test_short_reason_rejected():
    """The business reason must contain at least 10 characters."""

    with pytest.raises(ValidationError):
        ClaimStatusUpdateRequest(
            claim_id="CLM-12345",
            status="REJECTED",
            reason="Too short",
        )


# -------------------------------------------------------------------
# Strict schema validation
# -------------------------------------------------------------------

def test_extra_fields_rejected():
    """
    Unexpected fields must not silently enter the request model.
    """

    with pytest.raises(ValidationError):
        ClaimStatusUpdateRequest(
            claim_id="CLM-12345",
            status="APPROVED",
            reason="Required documents verified",
            unexpected_field="should_fail",
        )