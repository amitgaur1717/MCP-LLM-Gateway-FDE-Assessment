import logging
import sys

from fastmcp import FastMCP

from models import ClaimRequest, ClaimStatusUpdateRequest


# -------------------------------------------------------------------
# Logging configuration
# -------------------------------------------------------------------
# IMPORTANT:
# MCP is running over stdio, so stdout must remain reserved for
# protocol messages. Application logs therefore go to stderr.
# -------------------------------------------------------------------

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# MCP Server
# -------------------------------------------------------------------
# This server exposes enterprise claim-management capabilities
# through MCP tools.
# -------------------------------------------------------------------

mcp = FastMCP("claims-mcp")


# -------------------------------------------------------------------
# Mock enterprise claim data
# -------------------------------------------------------------------
# In a production system this could be replaced with a database
# or an enterprise claims-management API.
# -------------------------------------------------------------------

CLAIMS = {
    "CLM-12345": {
        "claim_id": "CLM-12345",
        "customer_name": "John Doe",
        "claim_type": "AUTO",
        "amount": 2500.00,
        "status": "OPEN",
    },
    "CLM-67890": {
        "claim_id": "CLM-67890",
        "customer_name": "Jane Smith",
        "claim_type": "HEALTH",
        "amount": 7500.00,
        "status": "UNDER_REVIEW",
    },
}


# -------------------------------------------------------------------
# Tool 1: Retrieve claim record
# -------------------------------------------------------------------

@mcp.tool()
def get_claim_record(claim_id: str) -> dict:
    """
    Retrieve an enterprise claim record.

    Input:
        claim_id: Must match CLM-XXXXX.

    The tool performs explicit Pydantic validation before accessing
    the underlying data store.
    """

    # ---------------------------------------------------------------
    # Validate the incoming request.
    # ---------------------------------------------------------------
    request = ClaimRequest(
        claim_id=claim_id
    )

    logger.info(
        "Retrieving claim: %s",
        request.claim_id,
    )

    # ---------------------------------------------------------------
    # Look up the claim.
    # ---------------------------------------------------------------
    claim = CLAIMS.get(request.claim_id)

    if claim is None:
        logger.warning(
            "Claim not found: %s",
            request.claim_id,
        )

        return {
            "success": False,
            "claim_id": request.claim_id,
            "message": "Claim not found",
        }

    # ---------------------------------------------------------------
    # Return the claim record.
    # ---------------------------------------------------------------
    return {
        "success": True,
        "claim": claim,
    }


# -------------------------------------------------------------------
# Tool 2: Update claim status
# -------------------------------------------------------------------

@mcp.tool()
def update_claim_status(
    claim_id: str,
    status: str,
    reason: str,
) -> dict:
    """
    Update the status of an enterprise claim.

    Validation rules:
    - claim_id must match CLM-XXXXX
    - status must be OPEN, UNDER_REVIEW, APPROVED, or REJECTED
    - reason must contain at least 10 characters
    """

    # ---------------------------------------------------------------
    # Validate all incoming fields using Pydantic.
    # ---------------------------------------------------------------
    request = ClaimStatusUpdateRequest(
        claim_id=claim_id,
        status=status,
        reason=reason,
    )

    logger.info(
        "Updating claim %s to status %s",
        request.claim_id,
        request.status.value,
    )

    # ---------------------------------------------------------------
    # Verify that the claim exists before modifying it.
    # ---------------------------------------------------------------
    claim = CLAIMS.get(request.claim_id)

    if claim is None:
        logger.warning(
            "Cannot update unknown claim: %s",
            request.claim_id,
        )

        return {
            "success": False,
            "claim_id": request.claim_id,
            "message": "Claim not found",
        }

    # ---------------------------------------------------------------
    # Update the mock claim record.
    # ---------------------------------------------------------------
    claim["status"] = request.status.value

    # ---------------------------------------------------------------
    # Return a structured result.
    # ---------------------------------------------------------------
    return {
        "success": True,
        "claim_id": request.claim_id,
        "new_status": request.status.value,
        "reason": request.reason,
        "message": "Claim status updated successfully",
    }


# -------------------------------------------------------------------
# Start MCP server
# -------------------------------------------------------------------
# stdio is required so MCP clients can communicate with the server
# through standard input/output.
#
# Do NOT print application logs to stdout because that would corrupt
# the MCP JSON-RPC communication stream.
# -------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(
        transport="stdio"
    )