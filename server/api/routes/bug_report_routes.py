"""
Bug report submission route.

POST /bug-report
    Accepts multipart/form-data:
        query_text  : str  (required)  — description of the bug
        image       : File (optional)  — screenshot (png/jpg/webp/gif, max 5 MB)

    Stores the report in the `bug_reports` Postgres table.
    When an image is provided it is written to BUG_REPORT_UPLOAD_DIR
    (env var, default ./uploads/bug-reports) and only the relative
    path is stored in the DB.

    Returns: { id, created_at }
"""
import os
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from api.auth import require_identity, Identity
from db.connection import execute, query

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Config ────────────────────────────────────────────────────────────────────
_DEFAULT_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "bug-reports"
_UPLOAD_DIR = Path(os.environ.get("BUG_REPORT_UPLOAD_DIR", str(_DEFAULT_UPLOAD_DIR)))

ALLOWED_IMAGE_MIME = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
}
ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def _ext_of(filename: str) -> str:
    i = filename.rfind(".")
    return filename[i:].lower() if i >= 0 else ""


# ── Route ─────────────────────────────────────────────────────────────────────
@router.post("/bug-report")
async def submit_bug_report(
    query_text: str = Form(..., min_length=1, max_length=5000),
    image: UploadFile | None = File(None),
    identity: Identity = Depends(require_identity),
):
    """
    Submit a bug report. Available to any authenticated user (student / faculty / admin).
    """
    image_path: str | None = None

    # ── Handle optional image upload ──────────────────────────────────────────
    if image is not None and image.filename:
        ext = _ext_of(image.filename)
        if ext not in ALLOWED_IMAGE_EXT:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type: {ext or '(none)'}. Allowed: png, jpg, webp, gif.",
            )
        if image.content_type and image.content_type.lower() not in ALLOWED_IMAGE_MIME:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported content-type: {image.content_type}.",
            )

        # Read & size-check before writing to disk.
        raw = await image.read(MAX_IMAGE_BYTES + 1)
        if len(raw) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Image too large (max 5 MB).")

        # Ensure upload directory exists.
        await run_in_threadpool(_UPLOAD_DIR.mkdir, parents=True, exist_ok=True)

        # Write with a collision-safe name: <uuid><ext>
        safe_name = f"{uuid.uuid4().hex}{ext}"
        dest = _UPLOAD_DIR / safe_name

        def _write():
            dest.write_bytes(raw)

        await run_in_threadpool(_write)
        # Store only the relative sub-path so the record stays portable.
        image_path = f"bug-reports/{safe_name}"
        logger.info("[bug_report] image saved → %s", image_path)

    # ── Persist to DB ──────────────────────────────────────────────────────────
    def _insert() -> dict:
        execute(
            """
            INSERT INTO bug_reports (erp_id, role, query_text, image_path)
            VALUES (%s, %s, %s, %s)
            """,
            (identity.erp_id, identity.role, query_text.strip(), image_path),
        )
        rows = query(
            "SELECT id, created_at FROM bug_reports WHERE erp_id = %s ORDER BY created_at DESC LIMIT 1",
            (identity.erp_id,),
        )
        return rows[0] if rows else {}

    row = await run_in_threadpool(_insert)
    logger.info(
        "[bug_report] submitted  erp_id=%s  role=%s  id=%s  has_image=%s",
        identity.erp_id,
        identity.role,
        row.get("id"),
        image_path is not None,
    )

    return {"id": row.get("id"), "created_at": str(row.get("created_at", ""))}
