"""
Covers pipeline.ecampus.intent_router.PersonalDataIntentRouter's
deterministic regex fast-paths, which decide PERSONAL_DATA vs COMMUNITY
for timetable/schedule-shaped queries without an LLM round-trip:

  - _OWN_SCHEDULE_PAT: first-person ("my", "next class", "tomorrow's
    timetable") -> PERSONAL_DATA, routed to the personal-tools path
    (get_my_timetable / get_my_teaching_schedule).
  - _PUBLIC_TIMETABLE_LOOKUP_PAT: "when/what time/which day ... lecture/
    class/course" with NO first-person pronoun -> COMMUNITY, routed to
    the published-timetable / RAG path instead of personal-tools.

Both fast-paths return before any LLM call, so these tests don't need to
mock InferenceRouter.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.ecampus.intent_router import PersonalDataIntentRouter

router = PersonalDataIntentRouter()


def test_when_does_course_lecture_happen_is_community_not_personal():
    # The reported bug: a query naming a subject, with no personal pronoun,
    # was intermittently classified PERSONAL_DATA and answered from the
    # requester's own (irrelevant) record instead of the published timetable.
    assert router.classify("when does the Machine Learning lecture take place") == "COMMUNITY"


def test_what_time_is_course_on_weekday_is_community():
    assert router.classify("what time is IT302 on Mondays") == "COMMUNITY"


def test_which_day_is_lab_is_community():
    assert router.classify("which day is the DBMS lab") == "COMMUNITY"


def test_my_timetable_is_still_personal_data():
    assert router.classify("what is my time table?") == "PERSONAL_DATA"


def test_my_next_class_is_personal_data():
    assert router.classify("what's my next class") == "PERSONAL_DATA"


def test_when_is_my_next_class_is_personal_data():
    assert router.classify("when is my next class") == "PERSONAL_DATA"


def test_tomorrows_timetable_is_personal_data():
    assert router.classify("what's my timetable for tomorrow") == "PERSONAL_DATA"
    assert router.classify("tomorrow's timetable") == "PERSONAL_DATA"


def test_named_cohort_timetable_stays_community_even_with_my():
    # A query that names a full cohort is COMMUNITY even if phrased with
    # "my" -- the PUBLIC_PROGRAMME_OVERRIDE_PAT guard from
    # personal_query_classifier.py applies here too. This phrasing doesn't
    # hit either deterministic fast-path (contains "my", so the public-
    # lookup pattern correctly stays out of it; isn't a when/what-time/
    # which-day question, so it doesn't hit that pattern either) -- it's
    # the pre-existing LLM classifier's job, unchanged by this fix, so the
    # LLM call is mocked here rather than asserting new regex behavior.
    from unittest.mock import patch, MagicMock
    mock_choice = MagicMock()
    mock_choice.message.content = "COMMUNITY"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    with patch("pipeline.ecampus.intent_router.InferenceRouter.call_with_rotation",
               return_value=mock_response):
        assert router.classify("what's my timetable for BTech ICT 3rd sem section A") == "COMMUNITY"


def test_add_a_lab_command_not_swallowed_by_public_lookup_pattern():
    # "add a lab on Friday" has no first-person pronoun and mentions "lab",
    # but it's an edit command, not a "when/what time/which day" question --
    # the public-lookup fast-path must not fire here, leaving it to the LLM
    # (which the intent_router's own docstring says should call this
    # PERSONAL_DATA).
    from pipeline.ecampus.intent_router import _PUBLIC_TIMETABLE_LOOKUP_PAT
    assert not _PUBLIC_TIMETABLE_LOOKUP_PAT.search("add a lab on Friday")
