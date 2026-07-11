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
    # Mint a valid token
    payload = {
        "erp_id": "FAC001",
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
    
    with patch("requests.post", return_value=mock_resp), \
         patch("api.routes.calendar_routes.store_tokens") as mock_store:
        res = client.get(f"/calendar/callback?code=mock_code&state={state}", follow_redirects=False)
        
    assert res.status_code == 307
    assert res.headers["location"] == "http://localhost:3000/dashboard?calendar=connected"
    mock_store.assert_called_once()

def test_callback_with_invalid_state_signature():
    # Mint token with a wrong secret
    payload = {"erp_id": "FAC001"}
    state = jwt.encode(payload, "wrong-secret", algorithm="HS256")
    
    res = client.get(f"/calendar/callback?code=mock_code&state={state}", follow_redirects=False)
    assert res.status_code == 400
    assert "invalid state token" in res.json()["detail"].lower()

def test_callback_with_expired_state():
    # Mint expired token
    payload = {
        "erp_id": "FAC001",
        "exp": datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
    }
    secret = os.environ.get("INTERNAL_JWT_SECRET", "test-secret-key")
    state = jwt.encode(payload, secret, algorithm="HS256")
    
    res = client.get(f"/calendar/callback?code=mock_code&state={state}", follow_redirects=False)
    assert res.status_code == 400
    assert "state token expired" in res.json()["detail"].lower()
