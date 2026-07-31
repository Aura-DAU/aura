"""CHAT-02: ICT-CS students must not collapse into plain ICT.

Decision recorded here because the tests encode it: ICT-CS is a ``branch_id``
layered on ``programme_id="btech-ict"``, NOT a distinct programme. The corpus
decides this — the ICT-CS requirements document describes itself as "a
companion document to the main Academic Requirements for B.Tech. (ICT)
Program" and says "All other rules apply uniformly to all B.Tech. (ICT)
programs as stated in that document".

The invariant these tests protect: an ICT-CS student must match BOTH generic
B.Tech.-ICT material and ICT-CS-specific material. Preferring the specific must
never exclude the generic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from api.academic_scope_persist import derive_academic_identity
from api.request_context import AcademicScope
from pipeline.ingestion.chunking.metadata_extractors import (
    extract_academic_applicability,
)
from pipeline.retrieval.retrieval_pipeline import (
    ICT_CS_PROGRAM_NAME,
    RetrievalPipeline,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "data"


def _scope(branch_id, programme_id="btech-ict", admission_year=2024) -> AcademicScope:
    return AcademicScope(
        erp_id="202401401",
        identity_version=1,
        admission_year=admission_year,
        programme_id=programme_id,
        branch_id=branch_id,
        department_id="ICTCS" if branch_id else "ICT",
        degree_level="undergraduate",
        profile_version=1,
        academic_status="active",
        expected_graduation_year=admission_year + 4,
        curriculum_version=None,
        regulation_version=None,
        enrollment_snapshot_id=None,
        current_semester=3,
        registered_course_codes=(),
        elective_course_codes=(),
        profile_stale=False,
        enrollment_stale=False,
    )


GENERIC_ICT_DOC = {
    "applicability_scope": "curriculum",
    "programme_id": "btech-ict",
    "degree_level": "undergraduate",
    "admission_year_from": 2000,
    "admission_year_to": 9999,
}
ICT_CS_DOC = {**GENERIC_ICT_DOC, "branch_id": "ict-cs"}


# ── The load-bearing invariant ──────────────────────────────────────────────

def test_ict_cs_student_matches_both_generic_and_specific():
    """An ICT-CS student sees generic ICT docs AND ICT-CS-only docs."""
    ict_cs_student = _scope("ict-cs")
    assert ict_cs_student.document_is_eligible(GENERIC_ICT_DOC)
    assert ict_cs_student.document_is_eligible(ICT_CS_DOC)


def test_plain_ict_student_does_not_see_ict_cs_only_docs():
    """The converse: branch-specific material stays out of plain ICT scope."""
    plain_ict_student = _scope(None)
    assert plain_ict_student.document_is_eligible(GENERIC_ICT_DOC)
    assert not plain_ict_student.document_is_eligible(ICT_CS_DOC)


def test_other_programme_student_sees_neither():
    mnc_student = _scope(None, programme_id="btech-mnc")
    assert not mnc_student.document_is_eligible(GENERIC_ICT_DOC)
    assert not mnc_student.document_is_eligible(ICT_CS_DOC)


# ── Identity derivation ─────────────────────────────────────────────────────

def test_ictcs_identity_keeps_parent_programme_and_adds_branch():
    """ICT-CS is a branch, not a programme: programme_id must stay btech-ict."""
    derived = derive_academic_identity(erp_id="202401401", dept="ICTCS")
    assert derived is not None
    assert derived.programme_id == "btech-ict"
    assert derived.branch_id == "ict-cs"
    assert derived.department_id == "ICTCS"


# ── PROGRAM_ALIASES ─────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "raw",
    [
        "ICT-CS",
        "ict cs",
        "ICTCS",
        "B.Tech ICT-CS",
        "BTech ICT CS",
        "B.Tech. (Honours) in ICT with minor in Computational Science",
        "ICT with minor in Computational Science",
    ],
)
def test_ict_cs_aliases_resolve_to_ict_cs_canonical(raw):
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    assert pipeline._canonical_program_name(raw) == ICT_CS_PROGRAM_NAME


@pytest.mark.parametrize("raw", ["ICT", "btech ict", "B.Tech. (ICT)", "btech-ict"])
def test_plain_ict_aliases_still_resolve_to_plain_ict(raw):
    """Adding ICT-CS keys must not steal plain-ICT lookups."""
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    assert pipeline._canonical_program_name(raw) == "B.Tech. (ICT)"


# ── Scope-inferred program entity widens rather than narrows ───────────────

def test_scope_program_names_for_ict_cs_includes_parent():
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    names = pipeline._scope_program_names(_scope("ict-cs"))
    assert names == [ICT_CS_PROGRAM_NAME, "B.Tech. (ICT)"]


def test_scope_program_names_for_plain_ict_is_single():
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    assert pipeline._scope_program_names(_scope(None)) == ["B.Tech. (ICT)"]


def test_ict_cs_program_filter_is_an_in_clause_not_an_eq():
    """A list of program names must widen (``$in``), never pin to one value."""
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    plan = {"entities": {"program_name": [ICT_CS_PROGRAM_NAME, "B.Tech. (ICT)"]}}
    built = pipeline._build_metadata_filter(plan)
    assert built == {
        "program_name": {"$in": [ICT_CS_PROGRAM_NAME, "B.Tech. (ICT)"]}
    }


def test_academic_scope_filter_does_not_constrain_branch():
    """Branch is enforced post-retrieval only.

    Putting branch into the pre-filter would drop programme-wide documents that
    carry no branch_id at all, i.e. most of the ICT corpus.
    """
    built = RetrievalPipeline._academic_scope_filter(_scope("ict-cs"))
    assert "branch_id" not in repr(built)


# ── Real corpus documents ───────────────────────────────────────────────────

def _classify(relative_path: str) -> dict:
    path = DATA / relative_path
    body = path.read_text(encoding="utf-8", errors="replace")
    metadata = {}
    if body.startswith("---"):
        end = body.find("\n---", 3)
        for line in body[3:end].splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip('"')
    return extract_academic_applicability(metadata, str(path), body)


@pytest.mark.skipif(not DATA.exists(), reason="corpus not present")
@pytest.mark.parametrize(
    "relative_path",
    [
        "academics/academic_policy_academic_requirements_btech_ict_cs_wef_2021-22.md",
        "academics/programs_of_study/undergraduate_programs/btech_honours_ict_minor_computational_science.md",
        "academics/timetable/ICT-CS_1st_Yr.md",
        "academics/timetable/ICT-CS_3rd_Yr_Sem5_Sec_A.md",
    ],
)
def test_real_ict_cs_documents_get_branch_tagged(relative_path):
    out = _classify(relative_path)
    assert out["programme_id"] == "btech-ict"
    assert out["branch_id"] == "ict-cs"


@pytest.mark.skipif(not DATA.exists(), reason="corpus not present")
@pytest.mark.parametrize(
    "relative_path",
    [
        # The primary ICT curriculum MENTIONS ICT-CS in its opening paragraph.
        # Tagging it ict-cs would hide it from every plain-ICT student.
        "academics/programs_of_study/undergraduate_programs/btech_ict_curriculum_syllabus.md",
        "academics/timetable/ICT_1st_Yr.md",
        # Explicitly shared cohorts — both branches must keep these.
        "academics/timetable/ICT_and_ICT-CS_2nd_Yr_Sem3.md",
        "academics/timetable/ICT_and_ICT-CS_2nd_Yr_Sem3_Sec_A.md",
        "academics/timetable/ICT_and_ICT-CS_2nd_Yr_Sem3_Sec_B.md",
    ],
)
def test_generic_and_shared_ict_documents_are_not_branch_tagged(relative_path):
    out = _classify(relative_path)
    assert out["programme_id"] == "btech-ict"
    assert out.get("branch_id") is None


@pytest.mark.skipif(not DATA.exists(), reason="corpus not present")
def test_mnc_timetable_not_stolen_by_ict_cs_body_mention():
    """MNC_1st_Yr.md names ICT-CS in a shared-Institute-Core note."""
    out = _classify("academics/timetable/MNC_1st_Yr.md")
    assert out["programme_id"] == "btech-mnc"
    assert out.get("branch_id") is None


# ── CHAT-03: programme identity comes from title/H1/path, not body prose ────

@pytest.mark.skipif(not DATA.exists(), reason="corpus not present")
@pytest.mark.parametrize(
    "relative_path",
    [
        # Campus-wide pages that merely MENTION a programme in prose. Pinning
        # them to that programme hides them from every other programme.
        "academics/grading_policy_v2.md",
        "academics/academic_areas.md",
        "academics/course_catalog_v2.md",
        "academics/curriculum_guide_v2.md",
        "academics/program_regulations_v2.md",
        "academics/programs_of_study/postgraduate_programs/postgraduate_programs.md",
        "academics/programs_of_study/undergraduate_programs/undergraduate_programs.md",
        "academics/leadership/director_general_v2.md",
    ],
)
def test_campus_wide_pages_are_global_not_pinned_to_one_programme(relative_path):
    out = _classify(relative_path)
    assert out["applicability_scope"] == "global"
    assert out.get("programme_id") is None


@pytest.mark.skipif(not DATA.exists(), reason="corpus not present")
def test_mtech_ec_requirements_not_mislabelled_ece_ai():
    """The ECE-AI pattern's "electronics and communication" alternative used to
    match M.Tech (EC) prose and win on ordering."""
    out = _classify(
        "academics/academic_policy_academic_requirements_m_tech_ec_program_wef_2022-23.md"
    )
    assert out["programme_id"] == "mtech-ec"


@pytest.mark.skipif(not DATA.exists(), reason="corpus not present")
def test_timetables_still_classified_from_h1_when_frontmatter_absent():
    """Timetable docs carry no frontmatter — the H1 is their only identity."""
    assert _classify("academics/timetable/ICT_1st_Yr.md")["programme_id"] == "btech-ict"
    assert _classify("academics/timetable/MNC_1st_Yr.md")["programme_id"] == "btech-mnc"
    assert _classify("academics/timetable/EVD_1st_Yr.md")["programme_id"] == "btech-evd"


def test_body_mention_alone_does_not_scope_a_document():
    """Unit-level guard for the rule, independent of the corpus."""
    out = extract_academic_applicability(
        {"title": "Grading Policy", "category": "Academics"},
        "/data/academics/grading_policy.md",
        "# Grading Policy\n\nThis applies to B.Tech. (ICT) and B.Tech. (MnC) students "
        "admitted in 2021 as well as everyone else.\n",
    )
    assert out["applicability_scope"] == "global"


def test_h1_mention_does_scope_a_document():
    out = extract_academic_applicability(
        {},
        "/data/academics/timetable/some_file.md",
        "# Timetable — B.Tech ICT-CS — 1st Year\n\nrows...\n",
    )
    assert out["applicability_scope"] == "curriculum"
    assert out["programme_id"] == "btech-ict"
    assert out["branch_id"] == "ict-cs"


@pytest.mark.skipif(not DATA.exists(), reason="corpus not present")
def test_ict_cs_student_is_eligible_for_every_real_ict_document():
    """End-to-end: the ICT-CS student loses nothing a plain ICT student has."""
    ict_cs_student = _scope("ict-cs", admission_year=2022)
    plain_ict_student = _scope(None, admission_year=2022)
    paths = [
        "academics/academic_policy_academic_requirements_btech_ict_cs_wef_2021-22.md",
        "academics/programs_of_study/undergraduate_programs/btech_ict_curriculum_syllabus.md",
        "academics/timetable/ICT_and_ICT-CS_2nd_Yr_Sem3.md",
        "academics/timetable/ICT-CS_1st_Yr.md",
    ]
    for relative_path in paths:
        metadata = _classify(relative_path)
        assert ict_cs_student.document_is_eligible(metadata), relative_path

    # And the ICT-CS-only ones are exactly what the plain student loses.
    only_ict_cs = [
        p for p in paths
        if not plain_ict_student.document_is_eligible(_classify(p))
    ]
    assert only_ict_cs == [
        "academics/academic_policy_academic_requirements_btech_ict_cs_wef_2021-22.md",
        "academics/timetable/ICT-CS_1st_Yr.md",
    ]
