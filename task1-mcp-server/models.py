from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ClaimStatus(str, Enum):
    """
    Allowed lifecycle states for an enterprise insurance claim.

    Using an Enum ensures that arbitrary status values are rejected
    instead of allowing invalid business states into the system.
    """

    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ClaimRequest(BaseModel):
    """
    Request model used when retrieving a claim.

    The claim ID must follow the required enterprise format:
    CLM-XXXXX
    """

    claim_id: str = Field(
        pattern=r"^CLM-\d{5}$"
    )

    # Reject unexpected fields to enforce a strict input contract.
    model_config = ConfigDict(extra="forbid")


class ClaimStatusUpdateRequest(BaseModel):
    """
    Request model used when changing the status of a claim.

    Validation requirements:
    - claim_id must follow the CLM-XXXXX format
    - status must be one of the supported ClaimStatus values
    - reason must contain at least 10 characters
    """

    claim_id: str = Field(
        pattern=r"^CLM-\d{5}$"
    )

    status: ClaimStatus

    reason: str = Field(
        min_length=10
    )

    # Prevent clients from sending unexpected parameters.
    model_config = ConfigDict(extra="forbid")