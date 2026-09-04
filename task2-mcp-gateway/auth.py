def get_role(authorization: str | None) -> str | None:
    """
    Extract and validate the role from the Authorization header.

    Expected format:
        Bearer <token>

    This assessment intentionally uses mock tokens.
    """

    if not authorization:
        return None

    parts = authorization.split(" ", 1)

    if len(parts) != 2:
        return None

    scheme, token = parts

    if scheme.lower() != "bearer":
        return None

    if token == "claims-admin-token":
        return "claims_admin"

    if token == "claims-viewer-token":
        return "claims_viewer"

    return None