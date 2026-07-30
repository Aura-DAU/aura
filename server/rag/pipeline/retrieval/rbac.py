from access_control import ROLE_ALLOWED_SETS

def get_allowed_roles(user_role: str) -> list[str]:
    # Single source of truth — delegates to access_control.ROLE_ALLOWED_SETS.
    user_role = user_role.lower()
    # Resolve aliases/legacy mapping for backward compatibility and tests.
    # Batch-year roles (student_2026 etc.) are mapped to themselves — they
    # must not be collapsed to the generic "student" role or "public".
    alias_map = {
        "faculty": "faculty_general",
        "guest": "public",
        "admin_full": "superadmin",
        # Broad JWT "admin" resolves to admin_staff via resolve_effective_role;
        # do not elevate bare "admin" to superadmin for document DLS.
        "admin": "admin_staff",
        # Batch-year student roles — identity pass-through
        "student_2026": "student_2026",
        "student_2025": "student_2025",
        "student_2024": "student_2024",
        "student_2023": "student_2023",
    }
    canonical_role = alias_map.get(user_role, user_role)
    return list(ROLE_ALLOWED_SETS.get(canonical_role, {"public"}))
