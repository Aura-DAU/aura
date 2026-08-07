# POST /bug-report — student/faculty "Report a Bug" submissions.
#
# Restored after commit f1a1d06 ("chore: remove backend bug report files")
# deleted this route, the migration, and the api.py registration while
# leaving the frontend (BugReportModal.tsx, app/api/bug-report/route.ts)
# in place — that mismatch is what produced the 404 on submit.
import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.auth import Identity, require_identity
from api.schemas import ALLOWED_IMAGE, MAX_IMAGE_BYTES
from db.connection import get_conn

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bug-report"])

# Directory bug-report screenshots are written to. Configurable so deploys
# can point it at a mounted volume; falls back to a local dir in dev.
BUG_REPORT_UPLOAD_DIR = Path(
    os.environ.get("BUG_REPORT_UPLOAD_DIR", "uploads/bug-reports")
)


@router.post("/bug-report")
async def submit_bug_report(
    query_text: str = Form(..., min_length=1, max_length=5000),
    image: UploadFile | None = File(None),
    identity: Identity = Depends(require_identity),
):
    query_text = query_text.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="query_text is required")

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
                    INSERT INTO bug_reports (erp_id, role, query_text, image_path)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, created_at
                    """,
                    (identity.erp_id, identity.role, query_text, image_rel_path),
                )
                row = cur.fetchone()
    except Exception as e:
        logger.error("[bug-report] insert failed: %s", e)
        raise HTTPException(status_code=500, detail="Could not submit report")

    return {"id": row["id"], "created_at": row["created_at"].isoformat()}