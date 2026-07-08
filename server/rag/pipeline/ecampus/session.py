"""
Session handling for ecampus.daiict.ac.in.

This is a Java servlet portal (NOT ASP.NET) — confirmed from Network tab:
  - Login POSTs to /webapp/intranet/LoginServlet
  - Redirects to /webapp/intranet/DefaultStudentHomePage.jsp on success
  - No __VIEWSTATE / __EVENTVALIDATION fields — plain form POST only

Field names confirmed from DevTools → Form Data:
  - UserID    (username / ERP ID)
  - Password  (password)

Tab URLs still need confirming — click each tab and note the URL bar,
they will all be under /webapp/intranet/. Update pages.py accordingly.
"""

import os
import requests

ECAMPUS_BASE_URL = os.environ.get("ECAMPUS_BASE_URL", "https://ecampus.daiict.ac.in")

# ── Confirmed from DevTools Form Data ─────────────────────────────────────
LOGIN_PATH       = "/webapp/intranet/LoginServlet"
LOGIN_FIELD_USER = "UserID"
LOGIN_FIELD_PASS = "Password"

# Post-login success signal — DefaultStudentHomePage.jsp appears in the
# final URL after the 302 redirect. Used as the login success check.
LOGIN_SUCCESS_URL_FRAGMENT = "DefaultStudentHomePage"


class ECampusLoginError(Exception):
    pass


class ECampusSession:
    """One instance per scrape operation. Not meant to be held open for the
    lifetime of a user's AURA session — log in, fetch what's needed, let it
    go out of scope."""

    def __init__(self):
        self.http = requests.Session()
        self.http.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
            "Referer": ECAMPUS_BASE_URL,
        })
        self._logged_in = False

    def login(self, username: str, password: str) -> None:
        """Plain POST to LoginServlet — no VIEWSTATE needed (Java servlet, not ASP.NET)."""
        login_url = ECAMPUS_BASE_URL + LOGIN_PATH
        payload = {
            LOGIN_FIELD_USER: username,
            LOGIN_FIELD_PASS: password,
        }
        resp = self.http.post(
            login_url,
            data=payload,
            timeout=15,
            allow_redirects=True,   # follow the 302 → DefaultStudentHomePage.jsp
        )
        resp.raise_for_status()

        # Success check: after the redirect, we should land on the home page
        if LOGIN_SUCCESS_URL_FRAGMENT not in resp.url:
            raise ECampusLoginError(
                f"eCampus login failed — landed on {resp.url!r} instead of "
                f"the expected home page. Check credentials or confirm that "
                f"LOGIN_PATH is still '/webapp/intranet/LoginServlet'."
            )
        self._logged_in = True

    def get_page(self, path: str) -> str:
        """GET any page under ECAMPUS_BASE_URL. path should start with /webapp/intranet/"""
        if not self._logged_in:
            raise ECampusLoginError("Must call login() before get_page().")
        resp = self.http.get(ECAMPUS_BASE_URL + path, timeout=15)
        resp.raise_for_status()
        return resp.text

    def logout(self) -> None:
        """Best-effort logout — confirm real logout URL from the portal's LOGOUT tab."""
        try:
            # TODO: confirm real logout path from the portal's LOGOUT link href
            self.http.get(ECAMPUS_BASE_URL + "/webapp/intranet/LogoutServlet", timeout=10)
        except requests.RequestException:
            pass
        self._logged_in = False