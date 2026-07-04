"""
Session handling for ecampus.daiict.ac.in.

This is a classic ASP.NET WebForms portal: pages carry hidden __VIEWSTATE /
__EVENTVALIDATION / __VIEWSTATEGENERATOR fields that MUST be resubmitted with
every POST (including login), or the server rejects the request. Tab
navigation on WebForms sites is frequently a __doPostBack(target, argument)
call rather than a plain <a href>, so we support both plain GET navigation
and postback-style navigation.

TODO once you have access to the live login page source:
  - Confirm the actual login form's field names (commonly
    "txtUserName"/"txtPassword" or similar ASP.NET auto-generated IDs like
    "ctl00$ContentPlaceHolder1$txtUser") — replace LOGIN_FIELD_USER /
    LOGIN_FIELD_PASS below.
  - Confirm LOGIN_PATH (the .aspx file the login form posts to).
  - Confirm whether tabs are plain links (easy) or __doPostBack calls
    (need the exact __EVENTTARGET string per tab, visible in page source).
"""

import os
import re
import requests

ECAMPUS_BASE_URL = os.environ.get("ECAMPUS_BASE_URL", "https://ecampus.daiict.ac.in")

# ── TODO: confirm against the real login page ──────────────────────────────
LOGIN_PATH = "/Login.aspx"
LOGIN_FIELD_USER = "txtUserName"
LOGIN_FIELD_PASS = "txtPassword"
LOGIN_FIELD_SUBMIT = "btnLogin"

VIEWSTATE_RE = re.compile(r'id="__VIEWSTATE" value="([^"]*)"')
VIEWSTATEGEN_RE = re.compile(r'id="__VIEWSTATEGENERATOR" value="([^"]*)"')
EVENTVALIDATION_RE = re.compile(r'id="__EVENTVALIDATION" value="([^"]*)"')


class ECampusLoginError(Exception):
    pass


class ECampusSession:
    """One instance per scrape operation. Not meant to be held open for the
    lifetime of a user's AURA session — log in, fetch what's needed, let it
    go out of scope. eCampus is likely to have its own idle-session timeout
    and possibly account lockout after repeated rapid logins, so the caller
    (client.py, via cache.py) should avoid re-logging-in more than necessary."""

    def __init__(self):
        self.http = requests.Session()
        self.http.headers.update({
            "User-Agent": "AURA-Assistant/1.0 (+https://dau.ac.in; academic-data-integration)"
        })
        self._logged_in = False

    def _extract_form_state(self, html: str) -> dict:
        def first(pattern, s):
            m = pattern.search(s)
            return m.group(1) if m else ""
        return {
            "__VIEWSTATE": first(VIEWSTATE_RE, html),
            "__VIEWSTATEGENERATOR": first(VIEWSTATEGEN_RE, html),
            "__EVENTVALIDATION": first(EVENTVALIDATION_RE, html),
        }

    def login(self, username: str, password: str) -> None:
        login_url = ECAMPUS_BASE_URL + LOGIN_PATH
        get_resp = self.http.get(login_url, timeout=15)
        get_resp.raise_for_status()
        form_state = self._extract_form_state(get_resp.text)

        payload = {
            **form_state,
            LOGIN_FIELD_USER: username,
            LOGIN_FIELD_PASS: password,
            LOGIN_FIELD_SUBMIT: "Login",
        }
        post_resp = self.http.post(login_url, data=payload, timeout=15)
        post_resp.raise_for_status()

        # TODO: replace with a real success/failure signal once you've seen
        # an actual failed-login response (error message text, redirect
        # target, etc.). Checking for the post-login "Welcome <Name>" text
        # that appears in your screenshot is a reasonable heuristic.
        if "Welcome" not in post_resp.text:
            raise ECampusLoginError(
                "eCampus login failed — check credentials or update session.py "
                "selectors against the current login page markup."
            )
        self._logged_in = True

    def get_page(self, path: str) -> str:
        if not self._logged_in:
            raise ECampusLoginError("Must call login() before get_page().")
        resp = self.http.get(ECAMPUS_BASE_URL + path, timeout=15)
        resp.raise_for_status()
        return resp.text

    def post_back(self, path: str, event_target: str, event_argument: str = "",
                   extra_fields: dict | None = None) -> str:
        """For tabs implemented as __doPostBack(...) rather than plain links."""
        if not self._logged_in:
            raise ECampusLoginError("Must call login() before post_back().")
        current_html = self.get_page(path)
        form_state = self._extract_form_state(current_html)
        payload = {
            **form_state,
            "__EVENTTARGET": event_target,
            "__EVENTARGUMENT": event_argument,
            **(extra_fields or {}),
        }
        resp = self.http.post(ECAMPUS_BASE_URL + path, data=payload, timeout=15)
        resp.raise_for_status()
        return resp.text

    def logout(self) -> None:
        # TODO: confirm LOGOUT_PATH from the real "LOGOUT" tab — calling this
        # explicitly (rather than just dropping the session) is good
        # citizenship on a portal that may have limited concurrent sessions.
        try:
            self.http.get(ECAMPUS_BASE_URL + "/Logout.aspx", timeout=10)
        except requests.RequestException:
            pass
        self._logged_in = False
