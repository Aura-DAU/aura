import pytest
import os
import datetime
import jwt
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add paths to sys.path — parent.parent.parent is server/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ.setdefault("INTERNAL_JWT_SECRET", "test-secret-key")
os.environ["GOOGLE_CALENDAR_CLIENT_ID"] = "test-client-id"
os.environ["GOOGLE_CALENDAR_CLIENT_SECRET"] = "test-client-secret"

from api.routes.calendar_routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app, raise_server_exceptions=False)

def test_callback_with_valid_state():
    # Mint a valid OAuth state token (separate aud/iss from session JWTs)
    from api.auth import (
        GCAL_OAUTH_STATE_AUDIENCE,
        GCAL_OAUTH_STATE_ISSUER,
        GCAL_OAUTH_STATE_TYP,
    )
    payload = {
        "erp_id": "FAC001",
        "typ": GCAL_OAUTH_STATE_TYP,
        "iss": GCAL_OAUTH_STATE_ISSUER,
        "aud": GCAL_OAUTH_STATE_AUDIENCE,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    }
    secret = os.environ.get("INTERNAL_JWT_SECRET", "test-secret-key")
    state = jwt.encode(payload, secret, algorithm="HS256")
    
    # Mock requests.post to return 200 with tokens
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "access_token": "mock-access",
        "refresh_token": "mock-refresh",
        "expires_in": 3600
    }

    mock_calendar_resp = MagicMock()
    mock_calendar_resp.ok = False

    with patch("requests.post", return_value=mock_resp), \
         patch("requests.get", return_value=mock_calendar_resp), \
         patch("api.routes.calendar_routes.store_tokens") as mock_store, \
         patch("api.routes.calendar_routes.log_action") as mock_log, \
         patch(
             "api.routes.calendar_routes._frontend_origin",
             return_value="http://localhost:3000",
         ):
        res = client.get(f"/calendar/callback?code=mock_code&state={state}", follow_redirects=False)

    assert res.status_code == 307
    assert res.headers["location"] == "http://localhost:3000/dashboard?calendar=connected"
    mock_store.assert_called_once()
    mock_log.assert_called_once()


def test_callback_with_invalid_state_signature():
    # Mint token with a wrong secret
    from api.auth import (
        GCAL_OAUTH_STATE_AUDIENCE,
        GCAL_OAUTH_STATE_ISSUER,
        GCAL_OAUTH_STATE_TYP,
    )
    payload = {
        "erp_id": "FAC001",
        "typ": GCAL_OAUTH_STATE_TYP,
        "iss": GCAL_OAUTH_STATE_ISSUER,
        "aud": GCAL_OAUTH_STATE_AUDIENCE,
    }
    state = jwt.encode(payload, "wrong-secret", algorithm="HS256")
    
    res = client.get(f"/calendar/callback?code=mock_code&state={state}", follow_redirects=False)
    assert res.status_code == 400
    assert "invalid state token" in res.json()["detail"].lower()


def test_callback_with_expired_state():
    # Mint expired token
    from api.auth import (
        GCAL_OAUTH_STATE_AUDIENCE,
        GCAL_OAUTH_STATE_ISSUER,
        GCAL_OAUTH_STATE_TYP,
    )
    payload = {
        "erp_id": "FAC001",
        "typ": GCAL_OAUTH_STATE_TYP,
        "iss": GCAL_OAUTH_STATE_ISSUER,
        "aud": GCAL_OAUTH_STATE_AUDIENCE,
        "exp": datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
    }
    secret = os.environ.get("INTERNAL_JWT_SECRET", "test-secret-key")
    state = jwt.encode(payload, secret, algorithm="HS256")
    
    res = client.get(f"/calendar/callback?code=mock_code&state={state}", follow_redirects=False)
    assert res.status_code == 400
    assert "state token expired" in res.json()["detail"].lower()


def _mint_state(**extra):
    from api.auth import (
        GCAL_OAUTH_STATE_AUDIENCE,
        GCAL_OAUTH_STATE_ISSUER,
        GCAL_OAUTH_STATE_TYP,
    )
    payload = {
        "erp_id": "202401001",
        "role": "student",
        "typ": GCAL_OAUTH_STATE_TYP,
        "iss": GCAL_OAUTH_STATE_ISSUER,
        "aud": GCAL_OAUTH_STATE_AUDIENCE,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
        **extra,
    }
    secret = os.environ.get("INTERNAL_JWT_SECRET", "test-secret-key")
    return jwt.encode(payload, secret, algorithm="HS256")


def test_callback_return_to_chat_root():
    """Chat connect CTA uses return_to=/ — must land on /?calendar=connected."""
    state = _mint_state(return_to="/")
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "access_token": "mock-access",
        "refresh_token": "mock-refresh",
        "expires_in": 3600,
    }
    mock_calendar_resp = MagicMock()
    mock_calendar_resp.ok = False

    with patch("requests.post", return_value=mock_resp), \
         patch("requests.get", return_value=mock_calendar_resp), \
         patch("api.routes.calendar_routes.store_tokens"), \
         patch("api.routes.calendar_routes.log_action"), \
         patch(
             "api.routes.calendar_routes._frontend_origin",
             return_value="http://localhost:3000",
         ):
        res = client.get(
            f"/calendar/callback?code=mock_code&state={state}",
            follow_redirects=False,
        )

    assert res.status_code == 307
    assert res.headers["location"] == "http://localhost:3000/?calendar=connected"


def test_callback_missing_vault_key_returns_clear_500():
    """After Google consent, missing VAULT_KEY must not look like a silent auth fail."""
    state = _mint_state(return_to="/dashboard")
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "access_token": "mock-access",
        "refresh_token": "mock-refresh",
        "expires_in": 3600,
    }

    with patch("requests.post", return_value=mock_resp), \
         patch(
             "api.routes.calendar_routes.store_tokens",
             side_effect=RuntimeError("GOOGLE_CALENDAR_VAULT_KEY is not set."),
         ):
        res = client.get(
            f"/calendar/callback?code=mock_code&state={state}",
            follow_redirects=False,
        )

    assert res.status_code == 500
    assert "GOOGLE_CALENDAR_VAULT_KEY" in res.json()["detail"]


def test_google_redirect_uri_warns_on_missing_backend_prefix(caplog):
    import logging
    from api.routes import calendar_routes as cr

    with patch.dict(
        os.environ,
        {"GOOGLE_CALENDAR_REDIRECT_URI": "https://aura.dau.ac.in/calendar/callback"},
        clear=False,
    ):
        with caplog.at_level(logging.WARNING, logger=cr.logger.name):
            uri = cr._google_redirect_uri()

    assert uri == "https://aura.dau.ac.in/calendar/callback"
    assert any("/backend/" in rec.message for rec in caplog.records)