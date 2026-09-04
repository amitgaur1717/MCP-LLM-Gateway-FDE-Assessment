from fastapi.testclient import TestClient

from gateway import app


client = TestClient(app)


def test_missing_authentication():
    """
    Requests without an Authorization header must be rejected.
    """

    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Unauthorized"


def test_invalid_claims_token():
    """
    Unknown bearer tokens must not authenticate.
    """

    response = client.post(
        "/mcp",
        headers={
            "Authorization": "Bearer invalid-token"
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
        },
    )

    assert response.status_code == 401


def test_claims_viewer_cannot_call_admin_tool():
    """
    A claims viewer must not invoke privileged tools.
    """

    response = client.post(
        "/mcp",
        headers={
            "Authorization": "Bearer claims-viewer-token"
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "claims_admin_approve",
            },
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["error"]["code"] == -32001
    assert body["error"]["message"] == "Unauthorized Tool Call"


def test_claims_admin_can_call_admin_tool():
    """
    A claims admin is allowed to invoke privileged tools.

    Since the downstream server is not running during this unit test,
    the request should reach the forwarding layer and return 502.
    """

    response = client.post(
        "/mcp",
        headers={
            "Authorization": "Bearer claims-admin-token"
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "claims_admin_approve",
            },
        },
    )

    assert response.status_code == 502


def test_viewer_can_call_normal_tool():
    """
    Authenticated viewers can call non-privileged tools.
    """

    response = client.post(
        "/mcp",
        headers={
            "Authorization": "Bearer claims-viewer-token"
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_claim_record",
            },
        },
    )

    assert response.status_code == 502