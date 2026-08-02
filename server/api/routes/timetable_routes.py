"""
timetable_routes.py — direct (non-chat) endpoints for the dashboard.

The dashboard's timetable card calls GET /timetable/me directly (not through
the chat pipeline) so it renders instantly on login.

Editing the timetable can happen two ways, both funneling into the exact
same service.apply_change / service.clear_change functions so there is one
place that decides what a valid edit looks like and one place that writes
the override row:
  - Conversationally, through the agent tools in pipeline.timetable.tool_registry
    (update_my_timetable / undo_timetable_change), which use a confirm=false
    preview step before confirm=true actually writes -- appropriate for a
    multi-turn chat where the model needs to check its own understanding of
    a free-text request against the student before acting.
  - Directly, through POST/DELETE /me/changes below, used by the dashboard's
    inline edit form. There's no confirm-preview step here: filling out a
    form and pressing "Save" (or "Remove") already *is* the confirmation --
    the same way any other web form submit is -- so gating it behind a
    second round-trip would just be friction with no safety benefit.

Both paths also refresh the student's Google Calendar afterwards (best
effort, only if already linked with write access) via
pipeline.google_calendar.timetable_sync.resync_if_linked, so a change made
in the dashboard shows up on Google Calendar without a separate manual sync.

Also exposes the Web Push subscribe/unsubscribe endpoints used by the "class
in 10 minutes" reminder feature.
"""

import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import db.connection as db_conn
from api.auth import require_identity, Identity
from pipeline.timetable import service
from pipeline.timetable.service import TimetableError
from pipeline.google_calendar import timetable_sync

router = APIRouter(prefix="/timetable", tags=["timetable"])
push_router = APIRouter(prefix="/push", tags=["push"])


@router.get("/me")
def get_my_timetable(identity: Identity = Depends(require_identity)):
    """Student's own effective timetable — cohort master merged with their
    personal overrides. Used by the dashboard's timetable card."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have a personal timetable.")
    try:
        return service.get_effective_timetable(identity)
    except TimetableError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


class TimetableChangeIn(BaseModel):
    kind: str = Field(..., pattern="^(replace|add|remove)$")
    day: Optional[str] = Field(None, max_length=16)
    start_time: Optional[str] = Field(None, max_length=8)
    end_time: Optional[str] = Field(None, max_length=8)
    course_code: Optional[str] = Field(None, max_length=32)
    course_name: Optional[str] = Field(None, max_length=256)
    session_type: Optional[str] = Field(None, max_length=16)
    room: Optional[str] = Field(None, max_length=64)
    faculty_name: Optional[str] = Field(None, max_length=128)
    note: Optional[str] = Field(None, max_length=500)


@router.post("/me/changes")
def add_my_timetable_change(body: TimetableChangeIn, identity: Identity = Depends(require_identity)):
    """Dashboard write path for one timetable edit — the direct-call sibling
    of the chat agent's update_my_timetable tool (see module docstring for
    why no confirm-preview step is needed here). Writes exactly one
    override row scoped to identity.erp_id via service.apply_change, same
    as the chat tool."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have a personal timetable.")
    try:
        result = service.apply_change(
            identity,
            kind=body.kind,
            day=body.day,
            start_time=body.start_time,
            end_time=body.end_time,
            course_code=body.course_code,
            course_name=body.course_name,
            session_type=body.session_type,
            room=body.room,
            faculty_name=body.faculty_name,
            note=body.note,
        )
    except TimetableError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    result["calendar_sync"] = timetable_sync.resync_if_linked(identity)
    return result


@router.delete("/me/changes/{override_id}")
def remove_my_timetable_change(override_id: str, identity: Identity = Depends(require_identity)):
    """Soft-deletes one of the student's own overrides (service.clear_change
    already scopes the WHERE clause to erp_id, so this can never touch
    another student's row) and refreshes their calendar if linked."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have a personal timetable.")
    try:
        result = service.clear_change(identity, override_id)
    except TimetableError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    result["calendar_sync"] = timetable_sync.resync_if_linked(identity)
    return result


@router.get("/me/changes")
def get_my_timetable_changes(identity: Identity = Depends(require_identity)):
    """List of the student's own personal edits, for a small 'your changes' list in the UI."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have a personal timetable.")
    try:
        return {"changes": service.list_my_changes(identity)}
    except TimetableError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


class ElectiveSelectionsIn(BaseModel):
    course_codes: list[str]


@router.get("/electives")
def get_electives(identity: Identity = Depends(require_identity)):
    """Available elective courses for the student's own cohort (year + sem),
    with a `selected` flag for each. See service.get_available_electives —
    scoped so a student never sees electives offered to a different
    year/semester."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have elective selections.")
    try:
        return service.get_available_electives(identity)
    except TimetableError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.post("/electives")
def post_electives(body: ElectiveSelectionsIn, identity: Identity = Depends(require_identity)):
    """Save the student's elective course selections — resolved against
    their own cohort only (see service.save_elective_selections)."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have elective selections.")
    try:
        return service.save_elective_selections(identity, body.course_codes)
    except TimetableError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


class PushSubscriptionKeys(BaseModel):
    p256dh: str = Field(..., min_length=1, max_length=256)
    auth: str = Field(..., min_length=1, max_length=256)


class PushSubscriptionIn(BaseModel):
    endpoint: str = Field(..., min_length=1, max_length=2048)
    keys: PushSubscriptionKeys
    user_agent: str | None = Field(None, max_length=512)


@push_router.get("/vapid-public-key")
def get_vapid_public_key():
    """The frontend needs this to create a PushSubscription in the browser."""
    key = os.environ.get("VAPID_PUBLIC_KEY", "")
    if not key:
        raise HTTPException(status_code=503, detail="Push notifications are not configured on this server yet.")
    return {"publicKey": key}


@push_router.post("/subscribe")
def subscribe_to_push(body: PushSubscriptionIn, identity: Identity = Depends(require_identity)):
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can subscribe to timetable reminders.")

    existing = db_conn.query(
        "SELECT id FROM push_subscriptions WHERE endpoint = %s", (body.endpoint,)
    )
    if existing:
        db_conn.execute(
            """UPDATE push_subscriptions
               SET erp_id = %s, p256dh = %s, auth_key = %s, user_agent = %s,
                   is_active = TRUE, last_seen_at = now()
               WHERE endpoint = %s""",
            (identity.erp_id, body.keys.p256dh, body.keys.auth, body.user_agent, body.endpoint),
        )
    else:
        db_conn.execute(
            """INSERT INTO push_subscriptions (id, erp_id, endpoint, p256dh, auth_key, user_agent)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (str(uuid.uuid4()), identity.erp_id, body.endpoint, body.keys.p256dh, body.keys.auth, body.user_agent),
        )
    return {"status": "subscribed"}


@push_router.delete("/subscribe")
def unsubscribe_from_push(
    endpoint: str = Query(..., min_length=1, max_length=2048),
    identity: Identity = Depends(require_identity),
):
    db_conn.execute(
        "UPDATE push_subscriptions SET is_active = FALSE WHERE endpoint = %s AND erp_id = %s",
        (endpoint, identity.erp_id),
    )
    return {"status": "unsubscribed"}


# -- Cohort Profile endpoints (/profile/*) -------------------------------------

profile_router = APIRouter(prefix="/profile", tags=["profile"])


class SaveCohortIn(BaseModel):
    program: str
    year: int
    semester: int
    section: str
    branch: Optional[str] = None


@profile_router.get("/cohort")
def get_cohort_profile(identity: Identity = Depends(require_identity)):
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have a cohort profile.")
    
    rows = db_conn.query(
        "SELECT current_year, current_sem, current_sec FROM user_identity_map WHERE erp_id = %s AND is_active = TRUE",
        (identity.erp_id,),
    )
    if not rows:
        return {
            "erp_id": identity.erp_id,
            "current_year": None,
            "current_sem": None,
            "current_sec": None,
            "is_configured": False
        }
        
    row = rows[0]
    year = row.get("current_year")
    sem = row.get("current_sem")
    sec = row.get("current_sec")
    is_configured = (year is not None) and (sem is not None) and (sec is not None and sec != "")
    
    return {
        "erp_id": identity.erp_id,
        "current_year": year,
        "current_sem": sem,
        "current_sec": sec,
        "is_configured": is_configured
    }


@profile_router.post("/cohort")
def post_cohort_profile(body: SaveCohortIn, identity: Identity = Depends(require_identity)):
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can set their cohort.")
    try:
        return service.update_student_cohort(
            identity,
            year=body.year,
            sem=body.semester,
            sec=body.section
        )
    except service.TimetableError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@profile_router.get("/cohort-options")
def get_cohort_options(identity: Identity = Depends(require_identity)):
    # C-6 fix: require_identity alone also accepts the "guest" role (any
    # anonymous demo visitor — see the guest-cookie flow), which let anyone
    # on the internet enumerate every program/year/sem/section combination
    # in the university via this endpoint with no real authentication.
    # This data is only needed for a signed-in student/faculty/admin
    # setting up their own cohort, so guests are excluded here.
    if identity.role not in ("student", "faculty", "admin"):
        raise HTTPException(status_code=403, detail="Sign in to view cohort options.")

    rows = db_conn.query(
        "SELECT DISTINCT program, year, sem, sec FROM timetable_master WHERE program IS NOT NULL ORDER BY program, year, sem, sec"
    )
    
    by_program = {}
    for r in rows:
        prog = r["program"] or "BTech"
        if "btech" in prog.lower():
            prog_key = "BTech"
        elif "mtech" in prog.lower():
            prog_key = "MTech"
        elif "msc" in prog.lower():
            prog_key = "MSc"
        elif "phd" in prog.lower() or "ph.d" in prog.lower():
            prog_key = "PhD"
        else:
            prog_key = prog

        year = r["year"]
        sem = r["sem"]
        sec = r["sec"]
        
        if year is None or sem is None or year <= 0:
            continue
            
        if prog_key not in by_program:
            by_program[prog_key] = {
                "program": prog_key,
                "branches": [],
                "years": {}
            }
            
        years_dict = by_program[prog_key]["years"]
        if year not in years_dict:
            years_dict[year] = {
                "year": year,
                "semesters": set(),
                "sections": set()
            }
            
        if sem:
            years_dict[year]["semesters"].add(sem)
        if sec:
            years_dict[year]["sections"].add(sec)
            
    options = []
    for prog_key, data in by_program.items():
        years_list = []
        for yr, ydata in sorted(data["years"].items()):
            years_list.append({
                "year": yr,
                "semesters": sorted(list(ydata["semesters"])),
                "sections": sorted(list(ydata["sections"])) if ydata["sections"] else ["A"]
            })
        
        branches = []
        if prog_key == "BTech":
            branches = ["ICT", "ICT-CS", "MnC", "EVD"]
        elif prog_key == "MSc":
            branches = ["AA", "DS", "IT"]
        elif prog_key == "MTech":
            branches = ["Core"]
            
        options.append({
            "program": prog_key,
            "branches": branches,
            "years": years_list
        })
        
    return {"options": options}

