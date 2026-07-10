"""
HTML parsers for ecampus.daiict.ac.in's tab pages.

Every function here takes raw HTML (from session.get_page()) and returns
structured Python data. ASP.NET WebForms GridViews render as plain <table>
elements with auto-generated IDs (e.g. id="ctl00_ContentPlaceHolder1_GridView1"),
so the general pattern is: find the right table, iterate <tr>, map <td>
columns by position or header text.

EVERY function below is a TODO stub with a reasonable, generic table-parsing
strategy — none of them have been validated against real eCampus HTML yet,
because I don't have it. Send me a saved HTML snippet (View Source, or a
screenshot is enough for the layout) of any of these pages once you're past
login and I'll replace the guessed column ordering with the real one. The
parsing approach (find table, iterate rows) is very likely right for a site
like this either way — it's the column names/order that need confirming.
"""

from typing import Optional
from bs4 import BeautifulSoup


def _first_table_after(soup: BeautifulSoup, hint_text: Optional[str] = None):
    """Generic helper: ASP.NET GridViews are usually the largest <table> on
    the content area. If hint_text is given, prefer a table whose nearest
    preceding heading/text contains it."""
    tables = soup.find_all("table")
    if not tables:
        return None
    if hint_text:
        for t in tables:
            if hint_text.lower() in t.get_text(" ", strip=True).lower():
                return t
    # fallback: the table with the most rows is almost always the data grid,
    # not a layout table
    return max(tables, key=lambda t: len(t.find_all("tr")))


def _rows_as_dicts(table, headers: list[str]) -> list[dict]:
    rows = table.find_all("tr")
    out = []
    for tr in rows[1:]:  # skip header row
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if not cells or len(cells) < len(headers):
            continue
        out.append(dict(zip(headers, cells)))
    return out


def parse_student_detail(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    # TODO: Student Detail looks like a label/value form, not a grid — once
    # you have the real markup, this likely becomes a series of
    # soup.find(id="ctl00_..._lblName") style lookups rather than a table
    # parse. Stub returns raw text for now so nothing silently breaks.
    content = soup.get_text("\n", strip=True)
    return {"raw_text": content}  # TODO: replace with structured fields


def parse_registration(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = _first_table_after(soup, hint_text="course")
    if not table:
        return []
    # TODO confirm real column order
    headers = ["course_code", "course_name", "credits", "instructor", "status"]
    return _rows_as_dicts(table, headers)


def parse_course_adjustments(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = _first_table_after(soup, hint_text="adjustment")
    if not table:
        return []
    headers = ["course_code", "action", "date", "approved_by", "status"]  # TODO confirm
    return _rows_as_dicts(table, headers)


def parse_result(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    table = _first_table_after(soup, hint_text="grade")
    grades = []
    if table:
        headers = ["semester", "course_code", "course_name", "credits", "grade"]  # TODO confirm
        grades = _rows_as_dicts(table, headers)

    # TODO: confirm whether SGPA/CGPA appear as a separate summary table/row
    # or as standalone labeled fields elsewhere on the page.
    cgpa_text = soup.find(string=lambda s: s and "CGPA" in s)
    sgpa_text = soup.find(string=lambda s: s and "SGPA" in s)

    return {
        "grades": grades,
        "cgpa_raw_label": cgpa_text.strip() if cgpa_text else None,  # TODO parse numeric value out of this
        "sgpa_raw_label": sgpa_text.strip() if sgpa_text else None,
    }


def parse_hostel(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    content = soup.get_text("\n", strip=True)
    return {"raw_text": content}  # TODO: structure into {block, room_no, mess_group, ...}


def parse_fees(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    table = _first_table_after(soup, hint_text="fee")
    payments = []
    if table:
        headers = ["semester", "head", "amount", "due_date", "status"]  # TODO confirm
        payments = _rows_as_dicts(table, headers)
    return {"payments": payments}


def parse_attendance(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = _first_table_after(soup, hint_text="attendance")
    if not table:
        return []
    headers = ["course_code", "course_name", "classes_held", "classes_attended", "percentage"]  # TODO confirm
    return _rows_as_dicts(table, headers)


def parse_utilities(html: str) -> dict:
    # TODO: "Utilities" is a catch-all label and I genuinely can't guess its
    # contents (could be ID-card requests, document downloads, password
    # change, etc.). Send a screenshot once you're on this tab and I'll
    # write the real parser + corresponding tool(s).
    soup = BeautifulSoup(html, "html.parser")
    return {"raw_text": soup.get_text("\n", strip=True)}
