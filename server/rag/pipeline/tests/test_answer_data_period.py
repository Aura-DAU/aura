"""Source-date disclosure for generated AURA answers."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.generation.answer_generator import (
    AnswerGenerator,
    build_data_period_note,
    strip_sources_marker,
)


def _context(*docs: str) -> str:
    return "<context>\n" + "\n".join(docs) + "\n</context>"


def _doc(doc_id: int, rule_year: str = "", scraped_date: str = "") -> str:
    return (
        f'<doc id="{doc_id}" rule_year="{rule_year}" '
        f'scraped_date="{scraped_date}">evidence</doc>'
    )


def test_academic_year_is_expanded_to_four_digit_range():
    context = _context(_doc(1, rule_year="2025-26", scraped_date="2026-07-01"))
    assert build_data_period_note(context, {1}) == (
        "Data period: Academic Year 2025-2026."
    )


def test_scraped_date_is_used_only_when_academic_year_is_missing():
    context = _context(_doc(1, scraped_date="2024-11-03"))
    assert build_data_period_note(context, {1}) == (
        "Data period: source fetched as of 2024-11-03."
    )


def test_multiple_cited_academic_years_are_disclosed():
    context = _context(
        _doc(1, rule_year="24-25"),
        _doc(2, rule_year="2025-2026"),
    )
    assert build_data_period_note(context, {1, 2}) == (
        "Data period: Academic Years 2024-2025, 2025-2026."
    )


def test_undated_cited_source_is_disclosed():
    context = _context(_doc(1))
    assert build_data_period_note(context, {1}) == (
        "Data period: The cited source does not specify a date."
    )


def test_buffered_generation_appends_period_before_sources():
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="The fee is listed. [1]"))]
    )
    context = _context(_doc(1, rule_year="2025-26"))
    generator = AnswerGenerator()

    with patch.object(generator, "_budget_max_tokens", return_value=256), patch(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        return_value=response,
    ):
        answer = generator.generate(
            query="What is the fee?",
            context=context,
            plan={"retrieval_intent": "general", "entities": {}},
        )

    assert answer == (
        "The fee is listed.\n\n"
        "Data period: Academic Year 2025-2026.\n\n"
        "[Sources: 1]"
    )


def test_streaming_generation_appends_period_before_sources():
    stream = [
        SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content="The fee is listed. [1]"))]
        )
    ]
    context = _context(_doc(1, rule_year="2025-26"))
    generator = AnswerGenerator()
    emitted = []

    with patch(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        return_value=stream,
    ):
        answer = generator._generate_streaming(
            system_prompt="system",
            user_prompt="question",
            on_delta=emitted.append,
            max_tokens=256,
            context=context,
        )

    expected = (
        "The fee is listed.\n\n"
        "Data period: Academic Year 2025-2026.\n\n"
        "[Sources: 1]"
    )
    expected_emitted = (
        "The fee is listed.\n\n"
        "Data period: Academic Year 2025-2026."
    )
    assert answer == expected
    assert "".join(emitted) == expected_emitted


def test_strip_sources_marker_keeps_data_period_visible():
    answer = (
        "The fee is listed.\n\n"
        "Data period: Academic Year 2025-2026.\n\n"
        "[Sources: 1]"
    )

    assert strip_sources_marker(answer) == (
        "The fee is listed.\n\n"
        "Data period: Academic Year 2025-2026."
    )
