def is_authorized(role: str, tool_name: str) -> bool:
    """
    Determine whether the authenticated role can invoke a tool.

    Any tool beginning with `claims_admin_` requires the
    claims_admin role.
    """

    if tool_name.startswith("claims_admin_"):
        return role == "claims_admin"

    # Non-privileged tools are available to authenticated users.
    return True