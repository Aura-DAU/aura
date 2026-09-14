import datetime
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

SERVER_DIR = Path(__file__).resolve().parent.parent
RAG_DIR = SERVER_DIR / "rag"
for p in (str(SERVER_DIR), str(RAG_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

SECRET = "test-internal-secret-for-bug-reports"
os.environ["INTERNAL_JWT_SECRET"] = SECRET

from api.auth import INTERNAL_JWT_AUDIENCE, INTERNAL_JWT_ISSUER
from api.routes import bug_report_routes

app = FastAPI()
app.include_router(bug_report_routes.router)
client = TestClient(app, raise_server_exceptions=False)


def make_token(erp_id: str = "ADMIN001", role: str = "admin") -> str:
    payload = {
        "erpId": erp_id,
        "role": role,
        "department": "ICT",
        "iss": INTERNAL_JWT_ISSUER,
        "aud": INTERNAL_JWT_AUDIENCE,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def auth_headers(role: str = "admin", erp_id: str = "ADMIN001") -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(erp_id=erp_id, role=role)}"}


@pytest.fixture
def mock_db_store():
    store = {
        "reports": [
            {
                "id": 1,
                "erp_id": "202301001",
                "role": "student",
                "query_text": "The AI hallucinated my timetable schedule.",
                "image_path": None,
                "category": "chat_ai",
                "status": "open",
                "created_at": datetime.datetime(2026, 9, 10, 12, 0, tzinfo=datetime.timezone.utc),
                "updated_at": datetime.datetime(2026, 9, 10, 12, 0, tzinfo=datetime.timezone.utc),
                "resolved_at": None,
                "resolved_by": None,
            },
            {
                "id": 2,
                "erp_id": "202301002",
                "role": "student",
                "query_text": "Slot 4 conflicts with lab course.",
                "image_path": "shot_2.png",
                "category": "timetable",
                "status": "in_progress",
                "created_at": datetime.datetime(2026, 9, 11, 14, 30, tzinfo=datetime.timezone.utc),
                "updated_at": datetime.datetime(2026, 9, 11, 15, 0, tzinfo=datetime.timezone.utc),
                "resolved_at": None,
                "resolved_by": None,
            },
            {
                "id": 3,
                "erp_id": "FAC001",
                "role": "faculty",
                "query_text": "Calendar sync error resolved.",
                "image_path": None,
                "category": "calendar",
                "status": "resolved",
                "created_at": datetime.datetime(2026, 9, 9, 9, 0, tzinfo=datetime.timezone.utc),
                "updated_at": datetime.datetime(2026, 9, 9, 10, 0, tzinfo=datetime.timezone.utc),
                "resolved_at": datetime.datetime(2026, 9, 9, 10, 0, tzinfo=datetime.timezone.utc),
                "resolved_by": "ADMIN001",
            },
        ]
    }
    return store


@pytest.fixture(autouse=True)
def patch_db_connection(monkeypatch, mock_db_store):
    class FakeCursor:
        def __init__(self):
            self.last_results = []
            self.last_one = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def execute(self, sql_query, params=()):
            norm_sql = " ".join(sql_query.split())
            reports = mock_db_store["reports"]

            if "INSERT INTO bug_reports" in norm_sql:
                erp_id, role, q_text, img_path, cat = params
                new_id = max(r["id"] for r in reports) + 1 if reports else 1
                now = datetime.datetime.now(datetime.timezone.utc)
                new_report = {
                    "id": new_id,
                    "erp_id": erp_id,
                    "role": role,
                    "query_text": q_text,
                    "image_path": img_path,
                    "category": cat,
                    "status": "open",
                    "created_at": now,
                    "updated_at": now,
                    "resolved_at": None,
                    "resolved_by": None,
                }
                reports.append(new_report)
                self.last_one = {"id": new_id, "created_at": now}
                return

            if "SELECT COUNT(*) AS n FROM bug_reports" in norm_sql:
                filtered = reports
                if len(params) == 1:
                    val = params[0]
                    filtered = [r for r in reports if r["status"] == val or r["category"] == val]
                elif len(params) >= 2:
                    st, cat = params[0], params[1]
                    filtered = [r for r in reports if r["status"] == st and r["category"] == cat]
                self.last_one = {"n": len(filtered)}
                return

            if "SELECT id, erp_id, role, query_text, image_path, category" in norm_sql:
                filtered = reports
                # Check where params
                if "WHERE" in norm_sql:
                    if len(params) == 3:  # status OR category, limit, offset
                        val = params[0]
                        filtered = [r for r in reports if r["status"] == val or r["category"] == val]
                    elif len(params) == 4:  # status AND category, limit, offset
                        st, cat = params[0], params[1]
                        filtered = [r for r in reports if r["status"] == st and r["category"] == cat]
                limit = params[-2]
                offset = params[-1]
                res = sorted(filtered, key=lambda x: x["created_at"], reverse=True)[offset : offset + limit]
                self.last_results = res
                return

            if "SELECT status, COUNT(*) AS n FROM bug_reports GROUP BY status" in norm_sql:
                counts = {}
                for r in reports:
                    counts[r["status"]] = counts.get(r["status"], 0) + 1
                self.last_results = [{"status": k, "n": v} for k, v in counts.items()]
                return

            if "SELECT category, status, COUNT(*) AS n" in norm_sql:
                counts = {}
                for r in reports:
                    k = (r["category"], r["status"])
                    counts[k] = counts.get(k, 0) + 1
                self.last_results = [
                    {"category": cat, "status": st, "n": n}
                    for (cat, st), n in counts.items()
                ]
                return

            if "SELECT id FROM bug_reports WHERE id = %s" in norm_sql:
                r_id = params[0]
                matched = [r for r in reports if r["id"] == r_id]
                self.last_one = matched[0] if matched else None
                return

            if "SELECT image_path FROM bug_reports WHERE id = %s" in norm_sql:
                r_id = params[0]
                matched = [r for r in reports if r["id"] == r_id]
                self.last_one = {"image_path": matched[0]["image_path"]} if matched else None
                return

            if "UPDATE bug_reports" in norm_sql:
                if "resolved_by = %s" in norm_sql:
                    st, admin_erp, r_id = params
                    for r in reports:
                        if r["id"] == r_id:
                            r["status"] = st
                            r["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
                            r["resolved_at"] = datetime.datetime.now(datetime.timezone.utc)
                            r["resolved_by"] = admin_erp
                            self.last_one = r
                            break
                else:
                    st, r_id = params
                    for r in reports:
                        if r["id"] == r_id:
                            r["status"] = st
                            r["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
                            r["resolved_at"] = None
                            r["resolved_by"] = None
                            self.last_one = r
                            break
                return

        def fetchone(self):
            return self.last_one

        def fetchall(self):
            return self.last_results

    class FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def cursor(self):
            return FakeCursor()

    from contextlib import contextmanager

    @contextmanager
    def fake_get_conn():
        yield FakeConn()

    monkeypatch.setattr(bug_report_routes, "get_conn", fake_get_conn)


# ── Tests ─────────────────────────────────────────────────────────────────

def test_admin_auth_guard():
    # Anonymous -> 401
    res = client.get("/bug-report/admin/list")
    assert res.status_code == 401

    # Student -> 403
    res = client.get("/bug-report/admin/list", headers=auth_headers(role="student"))
    assert res.status_code == 403

    # Admin -> 200
    res = client.get("/bug-report/admin/list", headers=auth_headers(role="admin"))
    assert res.status_code == 200


def test_submit_bug_report_with_category():
    # Valid category
    res = client.post(
        "/bug-report",
        data={"query_text": "Login button unresponsive", "category": "login_auth"},
        headers=auth_headers(role="student", erp_id="202301099"),
    )
    assert res.status_code == 200
    data = res.json()
    assert "id" in data

    # Invalid category -> 400
    res = client.post(
        "/bug-report",
        data={"query_text": "Random bug", "category": "non_existent_category"},
        headers=auth_headers(role="student"),
    )
    assert res.status_code == 400
    assert "Unknown category" in res.json()["detail"]


def test_list_bug_reports_filters():
    # List all
    res = client.get("/bug-report/admin/list", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert "reports" in body
    assert body["total"] >= 3

    # Filter by valid status
    res = client.get("/bug-report/admin/list?status=open", headers=auth_headers())
    assert res.status_code == 200

    # Filter by invalid status -> 400
    res = client.get("/bug-report/admin/list?status=bad_status", headers=auth_headers())
    assert res.status_code == 400
    assert "Unknown status" in res.json()["detail"]

    # Filter by valid category
    res = client.get("/bug-report/admin/list?category=chat_ai", headers=auth_headers())
    assert res.status_code == 200

    # Filter by invalid category -> 400
    res = client.get("/bug-report/admin/list?category=fake_cat", headers=auth_headers())
    assert res.status_code == 400
    assert "Unknown category" in res.json()["detail"]


def test_bug_report_stats():
    res = client.get("/bug-report/admin/stats", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert "total" in body
    assert "by_status" in body
    assert "open" in body["by_status"]
    assert "in_progress" in body["by_status"]
    assert "resolved" in body["by_status"]
    assert "by_category" in body
    assert isinstance(body["by_category"], list)


def test_update_bug_report_status():
    # Move to in_progress
    res = client.patch(
        "/bug-report/admin/1",
        json={"status": "in_progress"},
        headers=auth_headers(),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "in_progress"
    assert res.json()["resolved_by"] is None

    # Move to resolved
    res = client.patch(
        "/bug-report/admin/1",
        json={"status": "resolved"},
        headers=auth_headers(erp_id="ADMIN042"),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "resolved"
    assert res.json()["resolved_by"] == "ADMIN042"
    assert res.json()["resolved_at"] is not None

    # Reopen to open
    res = client.patch(
        "/bug-report/admin/1",
        json={"status": "open"},
        headers=auth_headers(),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "open"
    assert res.json()["resolved_by"] is None
    assert res.json()["resolved_at"] is None

    # Invalid status -> 422
    res = client.patch(
        "/bug-report/admin/1",
        json={"status": "invalid_status"},
        headers=auth_headers(),
    )
    assert res.status_code == 422

    # Non-existent report -> 404
    res = client.patch(
        "/bug-report/admin/999999",
        json={"status": "in_progress"},
        headers=auth_headers(),
    )
    assert res.status_code == 404


def test_get_bug_report_screenshot(tmp_path, monkeypatch):
    monkeypatch.setattr(bug_report_routes, "BUG_REPORT_UPLOAD_DIR", tmp_path)

    # Report without screenshot -> 404
    res = client.get("/bug-report/admin/1/screenshot", headers=auth_headers())
    assert res.status_code == 404
    assert "No screenshot" in res.json()["detail"]

    # Create dummy screenshot file
    img_file = tmp_path / "shot_2.png"
    img_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...")

    # Report with screenshot -> 200 FileResponse
    res = client.get("/bug-report/admin/2/screenshot", headers=auth_headers())
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert res.content == b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR..."
