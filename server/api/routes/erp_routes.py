"""
erp_routes.py — Lightweight ERP data endpoints for the student dashboard.

These routes are called by Next.js /api/erp/* server routes and return
structured JSON directly from ERPConnector (SQL).  They are separate from
the chat pipeline so the dashboard can load data without triggering the
full RAG/LLM stack.

All routes require a valid internal JWT (require_identity dependency).
Guest tokens (role="guest") are rejected with 403.

Endpoints:
  GET /erp/student/cgpa          → CgpaData
  GET /erp/student/timetable     → { timetable: TimetableSlot[] }
  GET /erp/student/fees          → FeeStatus | null
  GET /erp/student/registration  → { courses: Course[] }
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from erp_connector import ERPConnector
from ..auth.middleware import require_identity

router = APIRouter(prefix="/erp/student", tags=["erp"])
_erp   = ERPConnector()


def _student_only(identity=Depends(require_identity)):
    """Dependency: reject guests and non-students for student-specific data."""
    if identity["role"] in ("guest", "public"):
        raise HTTPException(status_code=403, detail="Authentication required.")
    if identity["role"] != "student":
        raise HTTPException(status_code=403, detail="Student access only.")
    return identity


@router.get("/cgpa")
def get_cgpa(identity=Depends(_student_only)):
    data = _erp.get_cgpa(identity["erp_id"])
    if not data:
        raise HTTPException(status_code=404, detail="CGPA record not found.")
    return data


@router.get("/timetable")
def get_timetable(identity=Depends(_student_only)):
    slots = _erp.get_timetable(identity["erp_id"])
    return {"timetable": slots}


@router.get("/fees")
def get_fees(identity=Depends(_student_only)):
    data = _erp.get_fees(identity["erp_id"])
    if not data:
        raise HTTPException(status_code=404, detail="Fee record not found.")
    return data


@router.get("/registration")
def get_registration(identity=Depends(_student_only)):
    courses = _erp.get_registration(identity["erp_id"])
    return {"courses": courses}
