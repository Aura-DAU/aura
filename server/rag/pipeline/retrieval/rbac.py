from access_control import ROLE_ALLOWED_SETS

def get_allowed_roles(user_role: str) -> list[str]:
    """Single source of truth — delegates to access_control.ROLE_ALLOWED_SETS."""
    user_role = user_role.lower()
    # Resolve aliases/legacy mapping for backward compatibility and tests
    alias_map = {
        "faculty": "faculty_general",
        "guest": "public",
        "admin_full": "superadmin",
        "admin": "superadmin",
    }
    canonical_role = alias_map.get(user_role, user_role)
    return list(ROLE_ALLOWED_SETS.get(canonical_role, {"public"}))
