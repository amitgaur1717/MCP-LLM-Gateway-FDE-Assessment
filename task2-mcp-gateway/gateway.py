from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
import httpx

from auth import get_role
from policy import is_authorized


app = FastAPI(title="Enterprise Claims MCP Security Gateway")

DOWNSTREAM_URL = "http://localhost:8001/mcp"


async def forward_request(payload: dict):
    """
    Forward a JSON-RPC request to the downstream MCP server.

    Internal connection errors must not expose implementation
    details to the client.
    """

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                DOWNSTREAM_URL,
                json=payload,
            )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )

    except httpx.RequestError:
        return JSONResponse(
            status_code=502,
            content={
                "jsonrpc": "2.0",
                "id": payload.get("id"),
                "error": {
                    "code": -32002,
                    "message": "Downstream MCP server unavailable",
                },
            },
        )


@app.post("/mcp")
async def mcp_gateway(
    payload: dict,
    authorization: str | None = Header(default=None),
):
    """
    Security gateway for the enterprise claims MCP server.

    Responsibilities:
    1. Authenticate the caller.
    2. Apply tool-level authorization.
    3. Forward authorized MCP requests.
    """

    # ---------------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------------

    role = get_role(authorization)

    if role is None:
        return JSONResponse(
            status_code=401,
            content={
                "jsonrpc": "2.0",
                "id": payload.get("id"),
                "error": {
                    "code": -32000,
                    "message": "Unauthorized",
                },
            },
        )

    method = payload.get("method")

    # ---------------------------------------------------------------
    # MCP tool authorization
    # ---------------------------------------------------------------

    if method == "tools/call":

        params = payload.get("params", {})
        tool_name = params.get("name", "")

        if not is_authorized(role, tool_name):
            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": "2.0",
                    "id": payload.get("id"),
                    "error": {
                        "code": -32001,
                        "message": "Unauthorized Tool Call",
                    },
                },
            )

    # ---------------------------------------------------------------
    # Authorized request
    # ---------------------------------------------------------------

    return await forward_request(payload)