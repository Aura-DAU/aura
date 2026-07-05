ALL_ROLES = [
    "public",
    "student",
    "faculty",
    "faculty_coord",
    "faculty_convenor_ug",
    "faculty_convenor_pg",
    "dean_students",
    "dean_faculty",
    "dean_academic",
    "registrar",
    "admin_staff",
    "superadmin"
]

def get_allowed_roles(user_role: str) -> list[str]:
    """
    Map a user's role to the set of document authorization tags they can access.
    Implements the additive hierarchy for Document-Level Security (DLS).
    """
    user_role = user_role.lower()
    
    # Base mapping defined from specification
    mapping = {
        "public": ["public"],
        "guest": ["public"],
        
        "student": ["public", "student"],
        
        "faculty_general": ["public", "faculty"],
        "faculty": ["public", "faculty"], # Alias
        
        "faculty_coord": ["public", "faculty", "faculty_coord"],
        
        "faculty_convenor_ug": ["public", "faculty", "faculty_coord", "faculty_convenor_ug", "faculty_convenor_pg"],
        "faculty_convenor_pg": ["public", "faculty", "faculty_coord", "faculty_convenor_ug", "faculty_convenor_pg"],
        
        "dean_students": ["public", "student", "faculty", "dean_students"],
        
        "dean_academic": ["public", "faculty", "faculty_coord", "faculty_convenor_ug", "faculty_convenor_pg", "dean_academic"],
        
        "dean_faculty": ["public", "faculty", "dean_faculty"],
        
        "registrar": ["public", "registrar"],
        
        "admin_staff": ["public", "admin_staff", "student"], # Assuming admin staff can see student docs
        
        "superadmin": ALL_ROLES,
        "admin_full": ALL_ROLES,
        "admin": ALL_ROLES
    }
    
    # Check if a specific binding exists, else fall back to public
    return mapping.get(user_role, ["public"])
