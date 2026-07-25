# Timetable-only dashboard + agentic edits + class reminders

## What changed

**Dashboard**
- `StudentDashboard.tsx` now shows **only** the timetable (attendance, CGPA,
  fees removed). It fetches live from `GET /api/timetable/me`.
- A "Remind me 10 min before class" toggle sits under the welcome banner.

**Identity / Google SSO**
- `user_identity_map` gained `full_name`, `current_year`, `current_sem`,
  `current_sec` (migration `004_student_profile_and_timetable.sql`).
- `/internal/resolve-identity`, the NextAuth `jwt`/`session` callbacks, and
  the internal JWT (`signInternalJwt`) now all carry these four fields
  end-to-end, so the FastAPI backend's `Identity` (see `api/auth.py`) has
  them on every request without an extra DB round trip.

**Timetable data model** (all AURA-owned — nothing here touches the ERP DB)
- `timetable_master` — the shared weekly schedule per (year, sem, sec),
  loaded from your demo/official timetable file.
- `timetable_overrides` — one row per personal change a student asks AURA
  to make (`replace` / `add` / `remove`). Reads are always
  `master ⨝ student's own overrides` — nobody else's view changes.

**Agentic editing**
- New tools in `pipeline/timetable/tool_registry.py`: `get_my_timetable`,
  `list_my_timetable_changes`, `update_my_timetable`, `undo_timetable_change`.
  Merged into the existing `EcampusOrchestrator` (see
  `pipeline/ecampus/orchestrator.py`) alongside the read-only ERP tools.
- `update_my_timetable` is a genuine write tool, so it's confirm-gated: the
  model calls it once with `confirm=false` to preview, shows you the diff,
  and only applies it once you say yes (second call with `confirm=true`).
- Every handler takes `identity` from the verified JWT only — there's no
  argument path that lets a student name someone else's `erp_id`.
- `pipeline/ecampus/tool_registry.py`'s old `get_timetable` (ERP-sourced) was
  removed in favor of this — it's now AURA's own data, not scraped.

**Class reminders (10 min before lecture/lab)**
- `pipeline/timetable/notifier.py` runs a background tick every 60s
  (`server/api/api.py` startup/shutdown hooks) checking every subscribed
  student for a class starting in `TIMETABLE_REMINDER_MINUTES` (default 10).
- Uses Web Push (VAPID) + a service worker (`aura/public/sw.js`) +
  `manifest.json`. Dedup via Redis (`pipeline/redis_client.py`, graceful
  in-memory fallback if `REDIS_URL` isn't set) backed by a
  `notification_log` table for durability across restarts.

## Env vars to add

```
# server/.env
REDIS_URL=redis://localhost:6379/0          # optional but recommended
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
VAPID_CONTACT_EMAIL=mailto:aura-admin@dau.ac.in
TIMETABLE_REMINDER_MINUTES=10               # optional, defaults to 10
```

Generate a VAPID key pair once with:
```
pip install pywebpush --break-system-packages
python -c "from py_vapid import Vapid01; v=Vapid01(); v.generate_keys(); print(v.public_key, v.private_key)"
```
(or `npx web-push generate-vapid-keys` — same standard, either works.)

## Running the migration + loading the demo timetable

```bash
psql "$AUTH_DB_URL" -f server/db/migrations/004_student_profile_and_timetable.sql

# Send me the demo timetable and I'll map it into this CSV shape
# (or hand it to me directly and I'll write the import for your exact format):
#   year, sem, sec, day, start_time, end_time, course_code, course_name, session_type, room, faculty_name
python server/db/import_timetable.py path/to/demo_timetable.csv

# And re-run the identity seed with the new columns to backfill
# full_name/current_year/current_sem/current_sec for existing students:
python server/db/seed_identity_map.py users.csv
```

## Still to send me
Please share the demo timetable file (CSV/Excel/whatever format you have) —
`import_timetable.py` expects the column names above, but if your file is
shaped differently I'll adjust the parser rather than asking you to
reformat it.
