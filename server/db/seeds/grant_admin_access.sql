-- Grant admin dashboard access for requested users.
-- Safe to re-run: upserts identity rows and idempotently adds admin_staff bindings.

INSERT INTO user_identity_map (email, erp_id, role, dept, is_active)
VALUES
  ('202401401@dau.ac.in', '202401401', 'admin', 'ICTCS', TRUE),
  ('202401475@dau.ac.in', '202401475', 'admin', 'ICTCS', TRUE)
ON CONFLICT (email) DO UPDATE
SET erp_id = EXCLUDED.erp_id,
    role = EXCLUDED.role,
    dept = COALESCE(EXCLUDED.dept, user_identity_map.dept),
    is_active = TRUE;

INSERT INTO role_bindings (erp_id, binding, granted_by, expires_at)
SELECT v.erp_id, 'admin_staff', 'seed', NULL
FROM (VALUES ('202401401'), ('202401475')) AS v(erp_id)
WHERE NOT EXISTS (
  SELECT 1 FROM role_bindings rb
  WHERE rb.erp_id = v.erp_id
    AND rb.binding = 'admin_staff'
    AND rb.revoked = FALSE
    AND (rb.expires_at IS NULL OR rb.expires_at > NOW())
);
