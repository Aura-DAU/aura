"""Regression tests for Pinecone-style → Qdrant filter translation.

The retrieval pipeline combines an authenticated student's academic-applicability
scope (an ``$or`` clause) with other constraints (authorization, entity filters)
under a top-level ``$and``. Translation used to flatten only the ``.must`` of each
sub-clause, which silently dropped any ``$or`` sub-clause — so the scope never
reached Qdrant and the dense candidate pool filled with out-of-scope documents.
"""

from qdrant_client.http import models as qmodels

from pipeline.retrieval.qdrant_client import translate_filter


def _scope_or():
    return {
        "$or": [
            {"applicability_scope": {"$eq": "global"}},
            {
                "$and": [
                    {"applicability_scope": {"$in": ["programme", "curriculum"]}},
                    {"programme_id": {"$eq": "btech-ict"}},
                    {"degree_level": {"$eq": "undergraduate"}},
                    {"admission_year_from": {"$lte": 2024}},
                    {"admission_year_to": {"$gte": 2024}},
                ]
            },
        ]
    }


def test_or_nested_in_and_is_not_dropped():
    """The academic-scope $or must survive when ANDed with other clauses."""
    combined = {
        "$and": [
            {"authorization": {"$in": ["public", "student"]}},
            {"program_name": {"$eq": "B.Tech. (ICT)"}},
            _scope_or(),
        ]
    }

    translated = translate_filter(combined)

    assert translated is not None
    # 2 flattened field conditions + 1 nested $or Filter.
    assert len(translated.must) == 3

    nested = [m for m in translated.must if isinstance(m, qmodels.Filter)]
    assert len(nested) == 1, "the $or clause must be preserved as a nested Filter"
    assert nested[0].should is not None
    assert len(nested[0].should) == 2  # global OR (programme/curriculum ...)

    blob = repr(translated)
    # The scope predicates must actually be present in what we send to Qdrant.
    assert "applicability_scope" in blob
    assert "programme_id" in blob
    # And the sibling constraints are still there.
    assert "authorization" in blob
    assert "program_name" in blob


def test_pure_conjunction_stays_flat():
    """A $and of plain equality/in clauses should flatten, not nest."""
    translated = translate_filter(
        {
            "$and": [
                {"authorization": {"$in": ["public"]}},
                {"program_name": {"$eq": "B.Tech. (ICT)"}},
            ]
        }
    )

    assert translated is not None
    assert len(translated.must) == 2
    assert all(isinstance(m, qmodels.FieldCondition) for m in translated.must)
    assert translated.should is None


def test_top_level_or_translates_to_should():
    translated = translate_filter(_scope_or())

    assert translated is not None
    assert translated.must is None
    assert translated.should is not None
    assert len(translated.should) == 2


def test_and_of_only_or_clauses_preserves_all():
    """Two OR clauses under $and must both survive as nested Filters."""
    combined = {
        "$and": [
            {"$or": [{"a": {"$eq": 1}}, {"b": {"$eq": 2}}]},
            {"$or": [{"c": {"$eq": 3}}, {"d": {"$eq": 4}}]},
        ]
    }

    translated = translate_filter(combined)

    assert translated is not None
    nested = [m for m in translated.must if isinstance(m, qmodels.Filter)]
    assert len(nested) == 2
    assert all(f.should is not None and len(f.should) == 2 for f in nested)


def test_student_semantic_path_filter_carries_scope_end_to_end():
    """The semantic path's real filter (auth AND academic-scope) must translate
    to a Qdrant filter that still constrains applicability_scope/programme_id.

    This guards the actual construction seam used by
    RetrievalPipeline._retrieve_dual_path — building it via the pipeline's own
    _combine_filters/_academic_scope_filter, not a hand-written dict — so a
    change to any of those (or to translate_filter) that drops scope again fails
    here. Before the fix the scope $or was silently dropped and the dense
    top-50 pulled candidates from every programme and admission year.
    """
    from types import SimpleNamespace

    from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline

    # _academic_scope_filter only reads these four attributes.
    scope = SimpleNamespace(
        programme_id="btech-ict",
        degree_level="undergraduate",
        admission_year=2024,
        registered_course_codes=("IT205",),
    )

    semantic_filter = RetrievalPipeline._combine_filters(
        {"authorization": {"$in": ["public", "student"]}},
        RetrievalPipeline._academic_scope_filter(scope),
    )

    translated = translate_filter(semantic_filter)
    blob = repr(translated)

    assert "authorization" in blob
    assert "applicability_scope" in blob  # scope survived translation
    assert "programme_id" in blob
    assert "course_code" in blob
