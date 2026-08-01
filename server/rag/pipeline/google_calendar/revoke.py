"""
revoke.py — Google OAuth token revocation.

When a student disconnects their Google Calendar, we must:
  1. Revoke the refresh token with Google (this invalidates the token
     server-side — Google stops accepting it, EVEN if someone stole it).
  2. Then call unlink_calendar() to drop it from our vault.

If revocation fails (network down, token already expired), we log it and
proceed with local unlinking anyway — the local token is gone, so even if
Google's copy lingers, it can't be used through AURA. This is the correct
"best-effort" approach used by industry (Google's own docs recommend it).

Revocation endpoint: https://oauth2.googleapis.com/revoke
Method: POST with ?token=<refresh_token>
"""

from __future__ import annotations

import logging

import requests

from .token_vault import get_tokens, CalendarNotLinked

GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"

logger = logging.getLogger("aura.gcal.revoke")


def revoke_oauth_token(erp_id: str) -> bool:
    """
    Revoke the stored Google refresh token for this student.

    Must be called BEFORE unlink_calendar() because unlinking drops the
    token from the vault and we'd have no way to retrieve it afterwards.

    Returns:
        True  — token was successfully revoked on Google's side.
        False — revocation failed (network issue / already revoked).
                Caller should still proceed with local unlink.

    Does NOT raise — revocation failure is logged but never blocks disconnect.
    """
    try:
        tokens = get_tokens(erp_id)
    except CalendarNotLinked:
        # Nothing stored locally — nothing to revoke
        return True

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        logger.warning("[revoke] No refresh token found for %s — skipping revocation.", erp_id)
        return False

    try:
        resp = requests.post(
            GOOGLE_REVOKE_URL,
            params={"token": refresh_token},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        if resp.status_code == 200:
            logger.info("[revoke] Successfully revoked Google OAuth token for %s.", erp_id)
            return True

        # 400 means the token was already revoked or expired — that's fine
        if resp.status_code == 400:
            logger.info(
                "[revoke] Token for %s was already invalid/revoked (HTTP 400). "
                "Proceeding with local unlink.",
                erp_id,
            )
            return True

        logger.warning(
            "[revoke] Google returned HTTP %d for %s. Proceeding with local unlink anyway.",
            resp.status_code,
            erp_id,
        )
        return False

    except requests.RequestException as exc:
        logger.error(
            "[revoke] Network error revoking token for %s: %s. "
            "Proceeding with local unlink — token may still be valid on Google's side.",
            erp_id,
            exc,
        )
        return False
