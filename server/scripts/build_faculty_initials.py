"""build_faculty_initials.py — derive server/api/faculty_initials.json.

Source: data/faculty/faculty_name_abbreviations_raw.txt, a clean text
extraction of data/faculty/faculty_name_abbreviations_source.pdf — DAU's
"FacultyNameAbbreviations" legend (Full Name (INITIALS) -> Short Name).
INITIALS/Short Name is the same short code stored in
timetable_master.faculty_name by scripts/import_timetable_xlsx.py (e.g.
"AM1", "AG1"), which is what pipeline/timetable/service.get_faculty_rows()
matches against. This legend is the canonical name<->initials source —
prefer it over trying to reverse-parse initials out of any generated
per-faculty timetable doc, which can drop or garble names that don't fit
that doc's synthesized cell format.

This script builds the login-time lookup identity_routes.py needs to turn
"which faculty just logged in" into "which initials do their classes use":
for every legend row, it derives the same email-prefix variants already
used in server/api/faculty_emails.json (firstname.lastname,
firstname_lastname, firstname.l, firstname_l) and keeps only the variants
that are IN faculty_emails.json — i.e. only maps initials onto an email
prefix AURA already knows is a real faculty login, rather than guessing at
one that isn't.

"Visiting Faculty (VF)" carries no short code / no real person and is
skipped. Legend names that don't match any faculty_emails.json entry
(typo'd spelling, visiting/adjunct faculty without a DAU login yet, etc.)
are reported so they can be fixed at the source and re-run through this
script, rather than silently mapped to a possibly-wrong prefix.

Run from server/: python scripts/build_faculty_initials.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_TXT = REPO_ROOT / "data" / "faculty" / "faculty_name_abbreviations_raw.txt"
FACULTY_EMAILS_PATH = Path(__file__).resolve().parent.parent / "api" / "faculty_emails.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "api" / "faculty_initials.json"

# "Full Name (INIT)   SHORT" or "Full Name (INIT)" (no short code — e.g.
# "Visiting Faculty (VF)", which isn't a real person and gets no email).
ROW_RE = re.compile(r"^(.+?)\s*\(([A-Za-z0-9]+)\)\s*([A-Za-z0-9]*)$")


def _email_variants(name: str) -> set[str]:
    """Same derivation as the email prefixes already curated into
    faculty_emails.json: firstname.lastname / firstname_lastname /
    firstname.<lastname-initial> / firstname_<lastname-initial>, using the
    first and last whitespace/hyphen-separated words of the name (middle
    names like "Abhishek Kantilal Tilva" are dropped, matching how that
    person's actual entries in faculty_emails.json are keyed).
    """
    words = [re.sub(r"[^a-z]", "", w) for w in re.split(r"[\s\-]+", name.lower())]
    words = [w for w in words if w]
    if len(words) < 2:
        return set()
    first, last = words[0], words[-1]
    return {f"{first}.{last}", f"{first}_{last}", f"{first}.{last[0]}", f"{first}_{last[0]}"}


def main() -> None:
    lines = [l.strip() for l in SOURCE_TXT.read_text(encoding="utf-8").split("\n") if l.strip()]
    lines = [l for l in lines if l != "Short Name"]  # the legend's own column header

    faculty_emails: set[str] = set(json.loads(FACULTY_EMAILS_PATH.read_text(encoding="utf-8")))

    # prefix -> set of (name, initials) that claimed it. Two different
    # people can share an abbreviated variant (e.g. two "Firstname T*"
    # faculty both reducing to "firstname.t") — such a prefix must NOT be
    # mapped to either, since a login-identity lookup that silently picks
    # one would show that person someone else's teaching schedule. Collect
    # every claim first, then only keep prefixes with exactly one claimant.
    claims: dict[str, set[tuple[str, str]]] = {}
    unmatched: list[tuple[str, str]] = []
    skipped: list[str] = []

    for line in lines:
        m = ROW_RE.match(line)
        if not m:
            skipped.append(line)
            continue
        name, initials, short = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        if not short:
            # e.g. "Visiting Faculty (VF)" — not a real person, no login to map.
            skipped.append(line)
            continue
        hits = _email_variants(name) & faculty_emails
        if not hits:
            unmatched.append((name, initials))
            continue
        for prefix in hits:
            claims.setdefault(prefix, set()).add((name, initials))

    mapping: dict[str, str] = {}
    ambiguous: dict[str, set[tuple[str, str]]] = {}
    for prefix, claimants in claims.items():
        if len(claimants) == 1:
            ((_, initials),) = claimants
            mapping[prefix] = initials
        else:
            ambiguous[prefix] = claimants

    OUT_PATH.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Wrote {len(mapping)} email-prefix -> initials entries to {OUT_PATH}")
    if skipped:
        print(f"\nSkipped {len(skipped)} legend row(s) with no real person / no short code:")
        for s in skipped:
            print(f"  - {s}")
    if unmatched:
        print(f"\nSkipped {len(unmatched)} name(s) with no match in faculty_emails.json "
              f"(add their email prefix there first, then re-run this script):")
        for name, initials in unmatched:
            print(f"  - {name} ({initials})")
    if ambiguous:
        print(f"\nExcluded {len(ambiguous)} prefix(es) shared by more than one faculty member "
              f"(ambiguous -- resolve manually, e.g. by adding a fuller email prefix for each "
              f"person to faculty_emails.json, then re-run):")
        for prefix, claimants in ambiguous.items():
            who = ", ".join(f"{name} ({initials})" for name, initials in sorted(claimants))
            print(f"  - {prefix}: {who}")


if __name__ == "__main__":
    main()
