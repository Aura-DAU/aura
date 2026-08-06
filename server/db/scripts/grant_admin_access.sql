-- Grant AURA admin dashboard access to team leads.
--
-- Requirements (see aura/app/dashboard/dashboard-shell.tsx, aura/app/api/admin/*,
-- server/api/routes/admin_routes.py, server/rag/access_control.py):
--   • user_identity_map.role = 'admin'  → NextAuth JWT role=admin (dashboard + BFF gates)
--   • resolve_effective_role maps broad role 'admin' → 'admin_staff' for backend /admin/*
--   • Explicit admin_staff bindings below are optional but kept for RBAC audit trail.
--
-- Apply on Node 1 Postgres (aura_auth):
--   psql "$AUTH_DB_URL" -f server/db/scripts/grant_admin_access.sql
--
-- Or via seed script (same outcome for identity map; bindings still need this SQL or admin UI):
--   python server/db/seed_identity_map.py server/db/seeds/admin_access.csv
--
-- Users must sign out and sign back in so NextAuth picks up the new role.

BEGIN;

INSERT INTO user_identity_map (email, erp_id, role, dept, is_active)
VALUES
  ('202401401@dau.ac.in', '202401401', 'admin', 'ICTCS', TRUE),
  ('202401475@dau.ac.in', '202401475', 'admin', 'ICTCS', TRUE)
ON CONFLICT (email) DO UPDATE SET
  erp_id    = EXCLUDED.erp_id,
  role      = 'admin',
  dept      = COALESCE(user_identity_map.dept, EXCLUDED.dept),
  is_active = TRUE;

INSERT INTO role_bindings (erp_id, binding, granted_by)
SELECT v.erp_id, 'admin_staff', 'system'
FROM (VALUES ('202401401'), ('202401475')) AS v(erp_id)
WHERE NOT EXISTS (
  SELECT 1
  FROM role_bindings rb
  WHERE rb.erp_id = v.erp_id
    AND rb.binding = 'admin_staff'
    AND rb.revoked = FALSE
);

COMMIT;
