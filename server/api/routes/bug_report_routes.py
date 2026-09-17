# /bug-report — student/faculty "Report a Bug" submissions, plus the
# /bug-report/admin/* endpoints backing the admin bug-resolver dashboard.
#
# POST /bug-report was restored after commit f1a1d06 ("chore: remove backend
# bug report files") deleted this route, the migration, and the api.py
# registration while leaving the frontend (BugReportModal.tsx,
# app/api/bug-report/route.ts) in place — that mismatch is what produced
# the 404 on submit.
#
# The /admin/* routes below (added alongside db/migrations/012_bug_reports_admin.sql)
# let an admin identity triage what gets filed: list/filter reports, move
# them through open -> in_progress -> resolved, view aggregate stats by
# status/category, and stream a report's screenshot without ever exposing
# BUG_REPORT_UPLOAD_DIR as a static/public path.
import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator

from api.auth import Identity, require_identity
from api.schemas import ALLOWED_IMAGE, BUG_CATEGORIES, BUG_STATUSES, MAX_IMAGE_BYTES
from db.connection import get_conn

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bug-report"])

# Directory bug-report screenshots are written to. Configurable so deploys
# can point it at a mounted volume; falls back to a local dir in dev.
BUG_REPORT_UPLOAD_DIR = Path(
    os.environ.get("BUG_REPORT_UPLOAD_DIR", "uploads/bug-reports")
)

_IMAGE_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _require_admin(identity: Identity = Depends(require_identity)) -> Identity:
    if identity.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return identity


@router.post("/bug-report")
async def submit_bug_report(
    query_text: str = Form(..., min_length=1, max_length=5000),
    category: str = Form("other"),
    image: UploadFile | None = File(None),
    identity: Identity = Depends(require_identity),
):
    query_text = query_text.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="query_text is required")

    category = (category or "other").strip().lower()
    if category not in BUG_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category}")

    image_rel_path: str | None = None

    if image is not None and image.filename:
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in ALLOWED_IMAGE:
            raise HTTPException(status_code=400, detail=f"Unsupported image type: {ext}")

        # Never trust the client filename for the on-disk path.
        safe_name = f"{uuid.uuid4().hex}{ext}"

        try:
            BUG_REPORT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            dest_path = BUG_REPORT_UPLOAD_DIR / safe_name

            size = 0
            with open(dest_path, "wb") as out:
                while chunk := await image.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_IMAGE_BYTES:
                        out.close()
                        dest_path.unlink(missing_ok=True)
                        raise HTTPException(status_code=413, detail="Screenshot must be under 5 MB")
                    out.write(chunk)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("[bug-report] failed to save screenshot: %s", e)
            raise HTTPException(status_code=500, detail="Could not save screenshot")

        image_rel_path = safe_name

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO bug_reports (erp_id, role, query_text, image_path, category)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, created_at
                    """,
                    (identity.erp_id, identity.role, query_text, image_rel_path, category),
                )
                row = cur.fetchone()
    except Exception as e:
        logger.error("[bug-report] insert failed: %s", e)
        raise HTTPException(status_code=500, detail="Could not submit report")

    return {"id": row["id"], "created_at": row["created_at"].isoformat()}


# ── Admin dashboard ─────────────────────────────────────────────────────

@router.get("/bug-report/admin/list")
def list_bug_reports(
    status: str | None = None,
    category: str | None = None,
    limit: int = 100,
    offset: int = 0,
    admin: Identity = Depends(_require_admin),
):
    """List bug reports for the resolver dashboard, newest first.

    Optional `status`/`category` filters map directly onto the columns
    added in 012_bug_reports_admin.sql; both are validated against the
    same fixed sets the submit form and the CHECK constraints use, so a
    typo'd filter fails fast with a 400 instead of silently returning
    nothing.
    """
    if status is not None and status not in BUG_STATUSES:
        raise HTTPException(status_code=400, detail=f"Unknown status: {status}")
    if category is not None and category not in BUG_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category}")
    if limit <= 0 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")

    clauses = []
    params: list = []
    if status is not None:
        clauses.append("status = %s")
        params.append(status)
    if category is not None:
        clauses.append("category = %s")
        params.append(category)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, erp_id, role, query_text, image_path, category,
                       status, created_at, updated_at, resolved_at, resolved_by
                FROM bug_reports
                {where}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            rows = cur.fetchall()
            cur.execute(f"SELECT COUNT(*) AS n FROM bug_reports {where}", tuple(params))
            total = cur.fetchone()["n"]

    return {
        "total": total,
        "reports": [
            {
                "id": r["id"],
                "erp_id": r["erp_id"],
                "role": r["role"],
                "query_text": r["query_text"],
                "has_screenshot": r["image_path"] is not None,
                "category": r["category"],
                "status": r["status"],
                "created_at": r["created_at"].isoformat(),
                "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                "resolved_at": r["resolved_at"].isoformat() if r["resolved_at"] else None,
                "resolved_by": r["resolved_by"],
            }
            for r in rows
        ],
    }


@router.get("/bug-report/admin/stats")
def bug_report_stats(admin: Identity = Depends(_require_admin)):
    """Counts for the dashboard's Statistics tab: totals by status and by
    category, plus a status breakdown per category (so "which category has
    the most open bugs" is answerable directly, not just total volume)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status, COUNT(*) AS n FROM bug_reports GROUP BY status"
            )
            status_rows = cur.fetchall()

            cur.execute(
                """
                SELECT category, status, COUNT(*) AS n
                FROM bug_reports
                GROUP BY category, status
                """
            )
            category_status_rows = cur.fetchall()

    by_status = {"open": 0, "in_progress": 0, "resolved": 0}
    for r in status_rows:
        by_status[r["status"]] = r["n"]
    total = sum(by_status.values())

    by_category: dict[str, dict] = {}
    for r in category_status_rows:
        cat = r["category"]
        entry = by_category.setdefault(
            cat, {"category": cat, "open": 0, "in_progress": 0, "resolved": 0, "total": 0}
        )
        entry[r["status"]] = r["n"]
        entry["total"] += r["n"]

    categories = sorted(by_category.values(), key=lambda e: e["total"], reverse=True)

    return {
        "total": total,
        "by_status": by_status,
        "by_category": categories,
    }


class UpdateStatusRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in BUG_STATUSES:
            raise ValueError(f"status must be one of {sorted(BUG_STATUSES)}")
        return value


@router.patch("/bug-report/admin/{report_id}")
def update_bug_report_status(
    report_id: int,
    body: UpdateStatusRequest,
    admin: Identity = Depends(_require_admin),
):
    """Move a report between open / in_progress / resolved.

    resolved_at/resolved_by are stamped when a report lands on `resolved`
    and cleared if it's ever reopened, so they always reflect the *current*
    resolution rather than the first time it happened to be marked done.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM bug_reports WHERE id = %s", (report_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Bug report not found")

            if body.status == "resolved":
                cur.execute(
                    """
                    UPDATE bug_reports
                    SET status = %s, updated_at = now(), resolved_at = now(), resolved_by = %s
                    WHERE id = %s
                    RETURNING id, erp_id, role, query_text, image_path, category,
                              status, created_at, updated_at, resolved_at, resolved_by
                    """,
                    (body.status, admin.erp_id, report_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE bug_reports
                    SET status = %s, updated_at = now(), resolved_at = NULL, resolved_by = NULL
                    WHERE id = %s
                    RETURNING id, erp_id, role, query_text, image_path, category,
                              status, created_at, updated_at, resolved_at, resolved_by
                    """,
                    (body.status, report_id),
                )
            row = cur.fetchone()

    return {
        "id": row["id"],
        "erp_id": row["erp_id"],
        "role": row["role"],
        "query_text": row["query_text"],
        "has_screenshot": row["image_path"] is not None,
        "category": row["category"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        "resolved_at": row["resolved_at"].isoformat() if row["resolved_at"] else None,
        "resolved_by": row["resolved_by"],
    }


@router.get("/bug-report/admin/{report_id}/screenshot")
def get_bug_report_screenshot(
    report_id: int,
    admin: Identity = Depends(_require_admin),
):
    """Stream a report's screenshot. image_path in the DB is always just a
    uuid-derived filename (never client input — see submit_bug_report), but
    we still resolve-and-contain it under BUG_REPORT_UPLOAD_DIR before
    serving, the same defense-in-depth pattern as GET /documents/{doc_path}."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT image_path FROM bug_reports WHERE id = %s", (report_id,)
            )
            row = cur.fetchone()

    if row is None or not row["image_path"]:
        raise HTTPException(status_code=404, detail="No screenshot for this report")

    upload_root = BUG_REPORT_UPLOAD_DIR.resolve()
    candidate = (upload_root / row["image_path"]).resolve()
    if upload_root not in candidate.parents or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Screenshot not found")

    media_type = _IMAGE_MEDIA_TYPES.get(candidate.suffix.lower(), "application/octet-stream")
    return FileResponse(candidate, media_type=media_type)
