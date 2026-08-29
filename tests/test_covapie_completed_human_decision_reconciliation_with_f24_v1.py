from __future__ import annotations

import ast
from collections import Counter
from copy import deepcopy
from dataclasses import fields, replace
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_f24_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_successor,
)
from covalent_ext import (  # noqa: E402
    covapie_f24_completed_decision_ingestion_and_task_label_availability_v1
    as f24_ingestion_owner,
)


ERROR = subject.CompletedDecisionReconciliationWithF24Error
GENERIC_ERROR = generic.CompletedDecisionReconciliationError
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_completed_human_decision_reconciliation_with_f24_v1",
    REPO
    / "scripts/check_covapie_completed_human_decision_reconciliation_with_f24_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


def _historical() -> list[dict[str, str]]:
    return [
        dict(row) for row in generic.load_real_historical_reconciliation_v1(REPO)
    ]


def _adapted_historical() -> tuple[dict[str, str], ...]:
    return onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        generic.load_real_historical_reconciliation_v1(REPO)
    )


def _bound() -> dict[str, object]:
    return f24_ingestion_owner.load_frozen_formal_decision_v1(REPO)


def _set_status(row: dict[str, str], status: str) -> None:
    row["current_review_status"] = status
    row["calibration_eligible"] = (
        "true" if status == generic.CURRENTLY_UNREVIEWED else "false"
    )
    row["calibration_exclusion_reason"] = (
        "" if status == generic.CURRENTLY_UNREVIEWED else status
    )


def test_public_api_is_minimal_and_f24_transition_adapter_is_not_created() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWithF24Error",
        "project_f24_completed_decision_v1",
        "load_real_completed_decision_sources_with_f24_v1",
        "reconcile_real_completed_human_decisions_with_f24_v1",
    )
    assert subject.F24_TRANSITION_ADAPTER_CREATED is False
    tree = ast.parse(Path(subject.__file__).read_bytes())
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert not any(
        name.lower().startswith("_adapt_f24")
        or ("f24" in name.lower() and "transition" in name.lower())
        for name in function_names
    )
    calls = [
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    ]
    assert calls.count("load_real_completed_decision_sources_with_ozj_v1") == 1
    assert calls.count("reconcile_real_completed_human_decisions_with_ozj_v1") == 0
    assert calls.count("project_f24_completed_decision_v1") == 1
    assert calls.count("load_frozen_formal_decision_v1") == 1
    assert calls.count(
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1"
    ) == 1
    assert calls.count("reconcile_completed_human_decisions_v1") == 1


def test_successor_has_no_second_authority_parse_or_training_runtime() -> None:
    tree = ast.parse(Path(subject.__file__).read_bytes())
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not imported & {
        "json", "csv", "dataset", "lightning_modules", "equivariant_diffusion"
    }
    text = Path(subject.__file__).read_text(encoding="utf-8")
    assert "covapie_f24_event_task_label_availability_v1.csv" not in text
    assert "completed_human_decision_snapshot" not in text
    assert "global_readiness_summary" not in text
    assert "global_readiness_manifest" not in text
    assert "materialize" not in text


def test_successor_reuses_generic_types_without_schema_fork() -> None:
    source = subject.project_f24_completed_decision_v1(repo_root=REPO)
    assert type(source) is generic.NormalizedDecisionSource
    assert type(source.binding) is generic.SourceBinding
    assert all(
        type(fact) is generic.NormalizedCompletedDecisionFact
        for fact in source.facts
    )
    tree = ast.parse(Path(subject.__file__).read_bytes())
    classes = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    assert not classes & {
        "SourceBinding",
        "NormalizedCompletedDecisionFact",
        "NormalizedDecisionSource",
        "ReconciliationResult",
    }


def test_f24_projector_calls_public_ingestion_owner_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = f24_ingestion_owner.load_frozen_formal_decision_v1
    calls: list[Path] = []

    def wrapped(repo_root: Path) -> dict[str, object]:
        calls.append(repo_root)
        return original(repo_root)

    monkeypatch.setattr(
        subject.f24_ingestion_owner, "load_frozen_formal_decision_v1", wrapped
    )
    subject.project_f24_completed_decision_v1(repo_root=REPO)
    assert calls == [REPO]


def test_f24_projector_wraps_only_ingestion_safety_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_repo_root: Path) -> dict[str, object]:
        raise f24_ingestion_owner.F24IngestionSafetyError("SOURCE_DRIFT")

    monkeypatch.setattr(
        subject.f24_ingestion_owner, "load_frozen_formal_decision_v1", fail
    )
    with pytest.raises(ERROR, match="F24_INGESTION_OWNER_VALIDATION_FAILED"):
        subject.project_f24_completed_decision_v1(repo_root=REPO)


@pytest.mark.parametrize("interrupt", (KeyboardInterrupt, SystemExit))
def test_f24_projector_propagates_base_exceptions(
    interrupt: type[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(_repo_root: Path) -> dict[str, object]:
        raise interrupt()

    monkeypatch.setattr(
        subject.f24_ingestion_owner, "load_frozen_formal_decision_v1", fail
    )
    with pytest.raises(interrupt):
        subject.project_f24_completed_decision_v1(repo_root=REPO)


def test_f24_projection_exact4_binding_context_and_minimal_semantics() -> None:
    source = subject.project_f24_completed_decision_v1(repo_root=REPO)
    assert source.binding == generic.SourceBinding(
        source_path=(
            "covapie-state/manual-review-aids/"
            "cumulative1000-high-yield-calibration-v1/"
            "F24_COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5/"
            "formal-human-decision-v1/f24_formal_human_decision_v1.json"
        ),
        path_namespace="repository_parent_relative",
        byte_count=26652,
        sha256="ec2bc7c96e6272e99202a8cdbdef330ea4c1189f5fd47abe43f55de2a2db5f22",
        schema_version="covapie_f24_exact4_formal_human_decision_v1",
        review_unit_id="COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5",
    )
    assert tuple(fact.canonical_event_id for fact in source.facts) == tuple(
        sorted(subject._F24_EVENT_IDS)
    )
    assert len(source.facts) == 4
    assert all(
        fact.human_review_completed is True
        and fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        and fact.task_relevance_disposition == generic.TASK_RELEVANT
        and fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        and fact.training_disposition == generic.TRAINING_INCLUDE
        and fact.human_training_excluded is False
        and fact.source_decision_schema == subject._F24_FORMAL_DECISION_SCHEMA
        and fact.source_decision_sha256 == subject._F24_FORMAL_DECISION_SHA256
        and fact.source_binding_path == source.binding.source_path
        for fact in source.facts
    )


def test_rich_f24_semantics_are_validated_before_projection() -> None:
    bound = _bound()
    events = subject._validate_rich_f24_semantics_v1(bound)
    assert tuple(event["canonical_event_id"] for event in events) == subject._F24_EVENT_IDS
    formal = bound["formal"]  # type: ignore[index]
    assert formal["human_approval"]["D4_role_partition"] == "REVISE_ROLE_PARTITION"
    assert formal["selected_role_partition"]["role_profile"] == (
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    )
    assert formal["chemical_warhead_annotation"]["chemical_warhead_atom_ids"] == [
        "C1", "C2", "C8", "O2", "O6"
    ]
    assert formal["selected_role_partition"]["warhead_role_atom_ids"] == [
        "C1", "C2", "C4", "C8", "O2", "O5", "O6"
    ]
    assert formal["canonical_Exact5_and_sample_applicability"][
        "sample_applicable_task_ids"
    ] == [0, 3, 4]
    assert f24_ingestion_owner._training_boundary()[
        "candidate_for_future_training_admission"
    ] is True
    assert f24_ingestion_owner._training_boundary()["training_admitted"] is False


def test_generic_fact_is_exact_thin_contract_without_rich_f24_fields() -> None:
    source = subject.project_f24_completed_decision_v1(repo_root=REPO)
    assert tuple(field.name for field in fields(generic.NormalizedCompletedDecisionFact)) == (
        checker.EXPECTED_GENERIC_FACT_FIELDS
    )
    for fact in source.facts:
        assert not any(
            hasattr(fact, name) for name in checker.FORBIDDEN_FACT_ATTRIBUTES
        )
    with pytest.raises(TypeError):
        generic.NormalizedCompletedDecisionFact(
            **{
                field: getattr(source.facts[0], field)
                for field in checker.EXPECTED_GENERIC_FACT_FIELDS
            },
            candidate_for_future_training_admission=True,
        )


def test_chemical_core_role_distinction_is_not_flattened_or_projected() -> None:
    bound = _bound()
    source = subject._project_validated_f24_binding_v1(bound)
    distinction = bound["formal"][  # type: ignore[index]
        "chemical_warhead_vs_role_region_distinction"
    ]
    assert distinction["sets_are_intentionally_distinct"] is True
    assert set(distinction["chemical_warhead_atom_ids"]) != set(
        distinction["warhead_role_atom_ids"]
    )
    assert all(
        not hasattr(fact, "chemical_warhead_atom_ids")
        and not hasattr(fact, "warhead_role_atom_ids")
        for fact in source.facts
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("path", "wrong/f24.json"),
        ("path_namespace", "wrong_namespace"),
        ("byte_count", 26653),
        ("sha256", "0" * 64),
        ("schema_version", "wrong_schema"),
        ("review_unit_id", "WRONG_REVIEW_UNIT"),
        ("mode", "0600"),
    ),
)
def test_projector_rejects_formal_binding_drift(
    field: str, value: object
) -> None:
    bound = _bound()
    bound["formal_decision_binding"][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match="F24_FORMAL_DECISION_BINDING_INVALID"):
        subject._project_validated_f24_binding_v1(bound)


@pytest.mark.parametrize("new_count", (3, 5))
def test_projector_rejects_exact4_count_drift(new_count: int) -> None:
    bound = _bound()
    events = bound["formal"]["event_level_human_decisions"]  # type: ignore[index]
    if new_count == 3:
        del events[-1]
    else:
        events.append(deepcopy(events[-1]))
    with pytest.raises(ERROR, match="EVENT_COUNT_NOT_EXACT4"):
        subject._project_validated_f24_binding_v1(bound)


def test_projector_rejects_duplicate_event_identity() -> None:
    bound = _bound()
    events = bound["formal"]["event_level_human_decisions"]  # type: ignore[index]
    events[1] = deepcopy(events[0])
    with pytest.raises(ERROR, match="EVENT_ID_DUPLICATE"):
        subject._project_validated_f24_binding_v1(bound)


def test_projector_rejects_missing_plus_extra_event_identity() -> None:
    bound = _bound()
    bound["formal"]["event_level_human_decisions"][0][  # type: ignore[index]
        "canonical_event_id"
    ] = "EXTRA_F24_EVENT"
    with pytest.raises(ERROR, match="EVENT_COVERAGE_NOT_EXACT4"):
        subject._project_validated_f24_binding_v1(bound)


@pytest.mark.parametrize(
    ("field", "value", "token"),
    (
        ("D1_task_relevance", "NOT_RELEVANT", "EVENT_DECISION_INVALID"),
        ("D2_chemistry", "NEGATIVE", "EVENT_DECISION_INVALID"),
        ("D3_reactive_pair", "REJECT", "EVENT_DECISION_INVALID"),
        ("D4_role_partition", "ACCEPT", "EVENT_DECISION_INVALID"),
        ("D5_training_use", "EXCLUDE_FROM_TRAINING_ONLY", "EVENT_DECISION_INVALID"),
        ("formal_training_admitted", True, "EVENT_DECISION_INVALID"),
    ),
)
def test_projector_rejects_event_decision_drift(
    field: str, value: object, token: str
) -> None:
    bound = _bound()
    bound["formal"]["event_level_human_decisions"][0][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match=token):
        subject._project_validated_f24_binding_v1(bound)


@pytest.mark.parametrize(
    ("field", "value", "token"),
    (
        ("scaleup_rank", 999, "RANK_COVERAGE"),
        ("pdb_id", "WRONG", "PDB_CONTEXT_COUNTS"),
        ("protein_asym", "WRONG", "DISTINCT_EVENT_CONTEXTS"),
        ("ligand_asym", "WRONG", "DISTINCT_EVENT_CONTEXTS"),
        ("protein_residue", "CYS:112-", "COVALENT_IDENTITY"),
    ),
)
def test_projector_rejects_context_identity_drift(
    field: str, value: object, token: str
) -> None:
    bound = _bound()
    bound["formal"]["event_level_human_decisions"][0][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match=token):
        subject._project_validated_f24_binding_v1(bound)


@pytest.mark.parametrize(
    ("path", "value", "token"),
    (
        (("human_approval", "D1_task_relevance"), "NOT_RELEVANT", "D1_D5"),
        (("human_approval", "D2_chemistry"), "NEGATIVE", "D1_D5"),
        (("human_approval", "D5_training_use"), "EXCLUDE", "D1_D5"),
        (
            ("human_approval", "human_selected_role_candidate_index_0based"),
            0,
            "SELECTED_CANDIDATE",
        ),
        (("selected_role_partition", "role_profile"), "WRONG", "ROLE_PARTITION"),
        (
            ("selected_role_partition", "warhead_role_atom_ids"),
            ["C1"],
            "ROLE_PARTITION",
        ),
        (
            ("chemical_warhead_annotation", "chemical_warhead_atom_ids"),
            ["C1"],
            "CHEMICAL_WARHEAD_ROLE_DISTINCTION",
        ),
        (
            (
                "chemical_warhead_vs_role_region_distinction",
                "sets_are_intentionally_distinct",
            ),
            False,
            "CHEMICAL_WARHEAD_ROLE_DISTINCTION",
        ),
        (
            ("canonical_Exact5_and_sample_applicability", "B3_present"),
            False,
            "CANONICAL_TASK_APPLICABILITY",
        ),
        (
            ("training_use_human_decision", "human_training_excluded"),
            True,
            "TRAINING_DISPOSITION_OR_ADMISSION_BOUNDARY",
        ),
        (
            ("training_use_human_decision", "formal_training_admitted"),
            True,
            "TRAINING_DISPOSITION_OR_ADMISSION_BOUNDARY",
        ),
    ),
)
def test_projector_rejects_rich_semantics_drift(
    path: tuple[str, str], value: object, token: str
) -> None:
    bound = _bound()
    bound["formal"][path[0]][path[1]] = value  # type: ignore[index]
    with pytest.raises(ERROR, match=token):
        subject._project_validated_f24_binding_v1(bound)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("candidate_for_future_training_admission", False),
        ("future_training_candidate_derived_by_ingestion", False),
        ("future_training_candidate_is_training_admission", True),
        ("training_admitted", True),
    ),
)
def test_projector_rejects_ingestion_future_boundary_drift(
    field: str, value: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = f24_ingestion_owner._training_boundary

    def drifted() -> dict[str, object]:
        result = original()
        result[field] = value
        return result

    monkeypatch.setattr(subject.f24_ingestion_owner, "_training_boundary", drifted)
    with pytest.raises(ERROR, match="INGESTION_DERIVED_FUTURE_CANDIDACY_INVALID"):
        subject._project_validated_f24_binding_v1(_bound())


def test_original_historical_f24_prior_is_exact4_unreviewed() -> None:
    rows = _historical()
    subject._prove_f24_original_unreviewed_prior_v1(rows)
    f24_rows = [row for row in rows if row["canonical_event_id"] in subject._F24_EVENT_IDS]
    assert len(f24_rows) == 4
    assert {row["raw_review_unit_id"] for row in f24_rows} == {
        subject._F24_REVIEW_UNIT_ID
    }
    assert all(
        row["current_review_status"] == generic.CURRENTLY_UNREVIEWED
        and row["calibration_eligible"] == "true"
        and row["calibration_exclusion_reason"] == ""
        for row in f24_rows
    )


def test_historical_proof_rejects_one_missing_f24_event() -> None:
    rows = [
        row for row in _historical()
        if row["canonical_event_id"] != subject._F24_EVENT_IDS[0]
    ]
    with pytest.raises(ERROR, match="F24_HISTORICAL_EVENT_MISSING"):
        subject._prove_f24_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_duplicate_f24_event() -> None:
    rows = _historical()
    row = next(
        row for row in rows
        if row["canonical_event_id"] == subject._F24_EVENT_IDS[0]
    )
    rows.append(dict(row))
    with pytest.raises(ERROR, match="F24_HISTORICAL_EVENT_DUPLICATE"):
        subject._prove_f24_original_unreviewed_prior_v1(rows)


@pytest.mark.parametrize("mutation", ("wrong_unit", "extra_unit_event"))
def test_historical_proof_rejects_wrong_f24_unit_inventory(mutation: str) -> None:
    rows = _historical()
    if mutation == "wrong_unit":
        row = next(
            row for row in rows
            if row["canonical_event_id"] == subject._F24_EVENT_IDS[0]
        )
        row["raw_review_unit_id"] = "WRONG_UNIT"
    else:
        row = next(
            row for row in rows
            if row["canonical_event_id"] not in subject._F24_EVENT_IDS
        )
        row["raw_review_unit_id"] = subject._F24_REVIEW_UNIT_ID
    with pytest.raises(ERROR, match="REVIEW_UNIT_EVENT_SET_NOT_EXACT4"):
        subject._prove_f24_original_unreviewed_prior_v1(rows)


@pytest.mark.parametrize(
    "status",
    (generic.CURRENTLY_IN_PROGRESS, generic.COMPLETED_HUMAN_POSITIVE),
)
def test_historical_proof_rejects_non_unreviewed_f24_prior(status: str) -> None:
    rows = _historical()
    for row in rows:
        if row["canonical_event_id"] in subject._F24_EVENT_IDS:
            _set_status(row, status)
    with pytest.raises(ERROR, match="PRIOR_STATE_NOT_EXACT4_UNREVIEWED"):
        subject._prove_f24_original_unreviewed_prior_v1(rows)


@pytest.mark.parametrize(
    ("field", "value"),
    (("calibration_eligible", "false"), ("calibration_exclusion_reason", "NONEMPTY")),
)
def test_historical_proof_rejects_calibration_prior_drift(
    field: str, value: str
) -> None:
    rows = _historical()
    row = next(
        row for row in rows
        if row["canonical_event_id"] == subject._F24_EVENT_IDS[0]
    )
    row[field] = value
    with pytest.raises(ERROR, match="PRIOR_STATE_NOT_EXACT4_UNREVIEWED"):
        subject._prove_f24_original_unreviewed_prior_v1(rows)


def test_onl_adapter_leaves_all_f24_rows_field_equal() -> None:
    original = tuple(_historical())
    adapted = onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        original
    )
    subject._prove_f24_rows_unchanged_after_onl_normalization_v1(original, adapted)
    f24_ids = set(subject._F24_EVENT_IDS)
    assert {
        row["canonical_event_id"]: row
        for row in original
        if row["canonical_event_id"] in f24_ids
    } == {
        row["canonical_event_id"]: row
        for row in adapted
        if row["canonical_event_id"] in f24_ids
    }


def test_f24_unchanged_proof_rejects_onl_adapter_change() -> None:
    original = tuple(_historical())
    adapted = [dict(row) for row in original]
    row = next(
        row for row in adapted
        if row["canonical_event_id"] == subject._F24_EVENT_IDS[0]
    )
    row["current_status_authority_sources_json"] = '["unexpected"]'
    with pytest.raises(ERROR, match="ONL_ADAPTER_CHANGED_F24_ROW"):
        subject._prove_f24_rows_unchanged_after_onl_normalization_v1(original, adapted)


def test_original_historical_with_exact12_sources_still_fails_for_onl() -> None:
    with pytest.raises(GENERIC_ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"):
        generic.reconcile_completed_human_decisions_v1(
            generic.load_real_historical_reconciliation_v1(REPO),
            subject.load_real_completed_decision_sources_with_f24_v1(REPO),
        )


def test_onl_adapted_historical_plus_exact12_sources_passes_generic() -> None:
    result = generic.reconcile_completed_human_decisions_v1(
        _adapted_historical(),
        subject.load_real_completed_decision_sources_with_f24_v1(REPO),
    )
    assert result.review_summary == checker.EXPECTED_REVIEW_SUMMARY


def test_exact11_predecessor_and_exact12_composition_are_collision_free() -> None:
    predecessor = (
        subject.ozj_successor.load_real_completed_decision_sources_with_ozj_v1(REPO)
    )
    assert len(predecessor) == 11
    assert tuple(len(source.facts) for source in predecessor) == (
        checker.EXPECTED_PREDECESSOR_SOURCE_FACT_COUNTS
    )
    assert sum(len(source.facts) for source in predecessor) == 87
    sources = subject.load_real_completed_decision_sources_with_f24_v1(REPO)
    assert len(sources) == 12
    assert tuple(len(source.facts) for source in sources) == (
        checker.EXPECTED_SOURCE_FACT_COUNTS
    )
    assert len({source.binding.stable_identity for source in sources}) == 12
    assert len({source.binding.review_unit_id for source in sources}) == 12
    event_ids = [fact.canonical_event_id for source in sources for fact in source.facts]
    assert len(event_ids) == len(set(event_ids)) == 91


def test_source_loader_calls_ozj_predecessor_and_f24_projector_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_predecessor = (
        subject.ozj_successor.load_real_completed_decision_sources_with_ozj_v1
    )
    original_projector = subject.project_f24_completed_decision_v1
    calls: Counter[str] = Counter()

    def wrapped_predecessor(root: Path) -> tuple[generic.NormalizedDecisionSource, ...]:
        calls["predecessor"] += 1
        return original_predecessor(root)

    def wrapped_projector(*, repo_root: Path) -> generic.NormalizedDecisionSource:
        calls["projector"] += 1
        return original_projector(repo_root=repo_root)

    monkeypatch.setattr(
        subject.ozj_successor,
        "load_real_completed_decision_sources_with_ozj_v1",
        wrapped_predecessor,
    )
    monkeypatch.setattr(subject, "project_f24_completed_decision_v1", wrapped_projector)
    subject.load_real_completed_decision_sources_with_f24_v1(REPO)
    assert calls == {"predecessor": 1, "projector": 1}


def test_source_loader_rejects_predecessor_composition_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = list(
        subject.ozj_successor.load_real_completed_decision_sources_with_ozj_v1(REPO)
    )
    existing.pop()
    monkeypatch.setattr(
        subject.ozj_successor,
        "load_real_completed_decision_sources_with_ozj_v1",
        lambda _root: tuple(existing),
    )
    with pytest.raises(ERROR, match="EXISTING_OZJ_SOURCE_COMPOSITION_INVALID"):
        subject.load_real_completed_decision_sources_with_f24_v1(REPO)


def test_source_loader_rejects_f24_collision_with_predecessor87(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = subject.ozj_successor.load_real_completed_decision_sources_with_ozj_v1(
        REPO
    )
    f24 = subject.project_f24_completed_decision_v1(repo_root=REPO)
    collision = replace(
        f24,
        facts=(
            replace(
                f24.facts[0],
                canonical_event_id=existing[0].facts[0].canonical_event_id,
            ),
            *f24.facts[1:],
        ),
    )
    monkeypatch.setattr(
        subject,
        "project_f24_completed_decision_v1",
        lambda *, repo_root: collision,
    )
    with pytest.raises(ERROR, match="F24_SOURCE_PROJECTION_INVALID"):
        subject.load_real_completed_decision_sources_with_f24_v1(REPO)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("review_unit_id", "WRONG_UNIT"),
        ("task_relevance_disposition", generic.TASK_NOT_RELEVANT),
        ("chemistry_disposition", generic.CHEMISTRY_NEGATIVE),
        ("training_disposition", generic.TRAINING_EXCLUDE),
        ("human_training_excluded", True),
    ),
)
def test_source_loader_rejects_fact_semantics_drift(
    field: str, value: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    f24 = subject.project_f24_completed_decision_v1(repo_root=REPO)
    wrong = replace(
        f24,
        facts=(replace(f24.facts[0], **{field: value}), *f24.facts[1:]),
    )
    monkeypatch.setattr(
        subject,
        "project_f24_completed_decision_v1",
        lambda *, repo_root: wrong,
    )
    with pytest.raises(ERROR, match="F24_SOURCE_PROJECTION_INVALID"):
        subject.load_real_completed_decision_sources_with_f24_v1(REPO)


def test_real_reconciliation_counts_training_and_final_f24_authority() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_f24_v1(REPO)
    assert result.review_summary == checker.EXPECTED_REVIEW_SUMMARY
    assert Counter(fact.training_disposition for fact in result.normalized_facts) == {
        generic.TRAINING_INCLUDE: 27,
        generic.TRAINING_EXCLUDE: 64,
    }
    f24_source = subject.project_f24_completed_decision_v1(repo_root=REPO)
    expected_authority = json.dumps(
        [f24_source.binding.source_path], separators=(",", ":"), sort_keys=True
    )
    f24_rows = [
        row for row in result.reconciled_rows
        if row["canonical_event_id"] in subject._F24_EVENT_IDS
    ]
    f24_facts = [
        fact for fact in result.normalized_facts
        if fact.canonical_event_id in subject._F24_EVENT_IDS
    ]
    assert len(f24_rows) == len(f24_facts) == 4
    assert all(
        row["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE
        and row["raw_review_unit_id"] == subject._F24_REVIEW_UNIT_ID
        and row["current_status_authority_sources_json"] == expected_authority
        for row in f24_rows
    )
    assert all(
        fact.human_review_completed is True
        and fact.task_relevance_disposition == generic.TASK_RELEVANT
        and fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        and fact.training_disposition == generic.TRAINING_INCLUDE
        and fact.human_training_excluded is False
        for fact in f24_facts
    )


def test_exact_f24_delta_relative_to_published_ozj_chain() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_f24_v1(REPO)
    summary = result.review_summary
    dispositions = Counter(fact.training_disposition for fact in result.normalized_facts)
    assert summary["completed_positive_event_count"] - 87 == 4
    assert summary["completed_positive_unit_count"] - 11 == 1
    assert summary["completed_total_event_count"] - 111 == 4
    assert summary["completed_total_unit_count"] - 15 == 1
    assert summary["unreviewed_event_count"] - 227 == -4
    assert summary["unreviewed_unit_count"] - 116 == -1
    assert summary["in_progress_event_count"] == 0
    assert dispositions[generic.TRAINING_INCLUDE] - 23 == 4
    assert dispositions[generic.TRAINING_EXCLUDE] - 64 == 0
    assert not hasattr(result, "future_training_candidate_count")
    assert not hasattr(result, "training_admitted_count")


def test_source_order_is_semantically_deterministic() -> None:
    rows = _adapted_historical()
    sources = subject.load_real_completed_decision_sources_with_f24_v1(REPO)
    assert generic.reconcile_completed_human_decisions_v1(
        rows, sources
    ) == generic.reconcile_completed_human_decisions_v1(
        rows, tuple(reversed(sources))
    )


def test_production_pipeline_calls_all_delegates_exactly_once_and_adapted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_predecessor = (
        subject.ozj_successor.load_real_completed_decision_sources_with_ozj_v1
    )
    original_projector = subject.project_f24_completed_decision_v1
    original_ingestion = subject.f24_ingestion_owner.load_frozen_formal_decision_v1
    original_onl = (
        subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1
    )
    original_generic = subject.generic.reconcile_completed_human_decisions_v1
    calls: Counter[str] = Counter()
    expected_adapted = _adapted_historical()

    def counted_predecessor(root: Path) -> tuple[generic.NormalizedDecisionSource, ...]:
        calls["predecessor"] += 1
        return original_predecessor(root)

    def counted_projector(*, repo_root: Path) -> generic.NormalizedDecisionSource:
        calls["projector"] += 1
        return original_projector(repo_root=repo_root)

    def counted_ingestion(root: Path) -> dict[str, object]:
        calls["ingestion"] += 1
        return original_ingestion(root)

    def counted_onl(rows: object) -> tuple[dict[str, str], ...]:
        calls["onl"] += 1
        return original_onl(rows)  # type: ignore[arg-type]

    def counted_generic(rows: object, sources: object) -> generic.ReconciliationResult:
        calls["generic"] += 1
        assert tuple(rows) == expected_adapted  # type: ignore[arg-type]
        return original_generic(rows, sources)  # type: ignore[arg-type]

    monkeypatch.setattr(
        subject.ozj_successor,
        "load_real_completed_decision_sources_with_ozj_v1",
        counted_predecessor,
    )
    monkeypatch.setattr(subject, "project_f24_completed_decision_v1", counted_projector)
    monkeypatch.setattr(
        subject.f24_ingestion_owner,
        "load_frozen_formal_decision_v1",
        counted_ingestion,
    )
    monkeypatch.setattr(
        subject.onl_successor,
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1",
        counted_onl,
    )
    monkeypatch.setattr(
        subject.generic, "reconcile_completed_human_decisions_v1", counted_generic
    )
    subject.reconcile_real_completed_human_decisions_with_f24_v1(REPO)
    assert calls == {
        "predecessor": 1,
        "projector": 1,
        "ingestion": 1,
        "onl": 1,
        "generic": 1,
    }


def test_current_ozj_census_stays_published_and_f24_unreviewed() -> None:
    published = checker._published_census_state(REPO)
    assert published["counts"] == checker.EXPECTED_CURRENT_CENSUS
    rows = published["rows"]
    f24_rows = [
        row for row in rows if row["canonical_event_id"] in subject._F24_EVENT_IDS
    ]
    assert len(f24_rows) == 4
    assert all(row["current_global_status"] == generic.CURRENTLY_UNREVIEWED for row in f24_rows)


def test_future_census_is_independently_derived_and_informational() -> None:
    published = checker._published_census_state(REPO)
    derived = checker._verify_future_census_informational(
        subject.project_f24_completed_decision_v1(repo_root=REPO),
        _bound(),
        published,
    )
    assert derived == checker.EXPECTED_FUTURE_CENSUS
    assert derived["warhead_only_A"] == 108
    assert derived["linker_plus_warhead_B"] == 48
    assert derived["scaffold_plus_warhead_B2"] == 48
    assert derived["scaffold_only_B3"] == 108
    assert derived["scaffold_plus_linker_plus_warhead_C"] == 108


def test_next_pending_is_derived_from_reconciliation_not_hardcoded() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_f24_v1(REPO)
    pending = checker._derive_next_pending(result)
    assert pending["review_unit_id"] != subject._F24_REVIEW_UNIT_ID
    assert pending["raw_priority_rank"] == 16
    assert pending["event_count"] == 4
    assert pending["ligand_component_ids"] == ("2A2",)
    source_text = Path(subject.__file__).read_text(encoding="utf-8")
    assert pending["review_unit_id"] not in source_text
    assert "2A2" not in source_text


def test_checker_exact4_frozen_architecture_and_all_gates() -> None:
    report = checker.run_check_v1(REPO)
    assert report["check"] == "PASS"
    assert report["exact4"]["count"] == 4
    assert report["exact4"]["lifecycle"] in (
        checker._CANDIDATE_UNTRACKED,
        checker._TRACKED_CLEAN,
    )
    assert report["exact4"]["third_successful_profile"] is False
    assert report["frozen_bindings"]["count"] == 14
    assert report["delegate_runtime_calls"] == {
        "predecessor_source_loader": 1,
        "f24_projector": 1,
        "f24_ingestion_loader": 1,
        "onl_adapter": 1,
        "generic_reconciler": 1,
    }
    assert report["source_fact_counts"] == checker.EXPECTED_SOURCE_FACT_COUNTS
    assert report["normalized_fact_count"] == 91
    assert report["event_collisions"] == 0
    assert report["generic_fact_thinness"]["future_candidate_projected"] is False
    assert report["rich_semantics_boundary"][
        "warhead_role_7_set_validated_upstream"
    ] is True
    assert report["global_census_update"] == "NOT_DONE"
    assert report["priority_queue_update"] == "NOT_DONE"
    assert report["reconciliation_materialized"] is False
    assert report["ready_for_external_review"] is True
    assert report["ready_for_training"] is False


@pytest.mark.parametrize(
    "expected_profile",
    (checker._CANDIDATE_UNTRACKED, checker._TRACKED_CLEAN),
)
def test_repository_profile_classifier_accepts_only_exact_success_profiles(
    expected_profile: str,
) -> None:
    expected = checker.EXACT4_PATHS
    if expected_profile == checker._CANDIDATE_UNTRACKED:
        tracked = {"README.md"}
        status = tuple("?? " + path for path in expected)
    else:
        tracked = {*expected, "README.md"}
        status = ()
    assert checker._classify_repository_profile(
        expected_paths=expected,
        tracked_paths=tracked,
        status_lines=status,
        working_tree_diff_paths=(),
        cached_diff_paths=(),
    ) == expected_profile


@pytest.mark.parametrize(
    ("tracked", "status", "working", "cached"),
    (
        pytest.param(
            set(checker.EXACT4_PATHS[:2]),
            tuple("?? " + path for path in checker.EXACT4_PATHS[2:]),
            (),
            (),
            id="partial-tracked-partial-untracked",
        ),
        pytest.param(
            set(),
            (*tuple("?? " + path for path in checker.EXACT4_PATHS), "?? extra.txt"),
            (),
            (),
            id="extra-ordinary-untracked",
        ),
        pytest.param(
            set(checker.EXACT4_PATHS),
            tuple("A  " + path for path in checker.EXACT4_PATHS),
            (),
            checker.EXACT4_PATHS,
            id="all-exact4-staged-new",
        ),
        pytest.param(
            {checker.EXACT4_PATHS[0]},
            (
                "A  " + checker.EXACT4_PATHS[0],
                *tuple("?? " + path for path in checker.EXACT4_PATHS[1:]),
            ),
            (),
            (checker.EXACT4_PATHS[0],),
            id="one-exact4-staged-new",
        ),
        pytest.param(
            set(checker.EXACT4_PATHS),
            (" M " + checker.EXACT4_PATHS[0],),
            (checker.EXACT4_PATHS[0],),
            (),
            id="tracked-exact4-working-modification",
        ),
        pytest.param(
            set(checker.EXACT4_PATHS),
            ("M  " + checker.EXACT4_PATHS[0],),
            (),
            (checker.EXACT4_PATHS[0],),
            id="tracked-exact4-staged-modification",
        ),
        pytest.param(
            set(checker.EXACT4_PATHS),
            (" M unrelated.txt",),
            ("unrelated.txt",),
            (),
            id="unrelated-working-modification",
        ),
        pytest.param(
            set(checker.EXACT4_PATHS),
            ("M  unrelated.txt",),
            (),
            ("unrelated.txt",),
            id="unrelated-staged-modification",
        ),
        pytest.param(
            set(),
            tuple("?? " + path for path in checker.EXACT4_PATHS[:-1]),
            (),
            (),
            id="missing-candidate-status",
        ),
        pytest.param(
            set(checker.EXACT4_PATHS),
            ("UU " + checker.EXACT4_PATHS[0],),
            (),
            (),
            id="unexpected-status-entry",
        ),
    ),
)
def test_repository_profile_classifier_rejects_all_mixed_or_dirty_states(
    tracked: set[str],
    status: tuple[str, ...],
    working: tuple[str, ...],
    cached: tuple[str, ...],
) -> None:
    with pytest.raises(
        ValueError,
        match="REPOSITORY_PROFILE_NOT_EXACT_CANDIDATE_UNTRACKED_OR_TRACKED_CLEAN",
    ):
        checker._classify_repository_profile(
            expected_paths=checker.EXACT4_PATHS,
            tracked_paths=tracked,
            status_lines=status,
            working_tree_diff_paths=working,
            cached_diff_paths=cached,
        )


def test_live_repository_profile_uses_full_cleanliness_observations() -> None:
    report = checker.verify_candidate_exact4_v1(REPO)
    assert report["count"] == 4
    assert report["supported_successful_profiles"] == (
        checker._CANDIDATE_UNTRACKED,
        checker._TRACKED_CLEAN,
    )
    assert report["third_successful_profile"] is False
    assert report["working_tree_diff_count"] == 0
    assert report["cached_diff_count"] == 0
    if report["lifecycle"] == checker._CANDIDATE_UNTRACKED:
        assert report["tracked_exact4_count"] == 0
        assert report["git_status_entry_count"] == 4
    else:
        assert report["lifecycle"] == checker._TRACKED_CLEAN
        assert report["tracked_exact4_count"] == 4
        assert report["git_status_entry_count"] == 0


@pytest.mark.parametrize(
    "path",
    ("candidate.pt", "build/__pycache__/module.pyc", "scratch.tmp"),
)
def test_checker_rejects_dirty_forbidden_or_transient_paths(path: str) -> None:
    with pytest.raises(ValueError, match="FORBIDDEN_OR_TRANSIENT_REPOSITORY_PATH"):
        checker._reject_dirty_forbidden_or_transient_paths(
            ("?? " + path,), (), ()
        )


def test_candidate_regular_file_gate_rejects_missing_directory_and_symlink(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.py"
    with pytest.raises(ValueError, match="NOT_REGULAR_FILE"):
        checker._read_regular_file(missing, "missing")
    directory = tmp_path / "directory.py"
    directory.mkdir()
    with pytest.raises(ValueError, match="NOT_REGULAR_FILE"):
        checker._read_regular_file(directory, "directory")
    target = tmp_path / "target.py"
    target.write_bytes(b"pass\n")
    symlink = tmp_path / "symlink.py"
    symlink.symlink_to(target)
    with pytest.raises(ValueError, match="NOT_REGULAR_FILE"):
        checker._read_regular_file(symlink, "symlink")


def test_checker_rejects_frozen_f24_owner_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = list(checker.FROZEN_REPOSITORY_FILES)
    owner = rows[6]
    rows[6] = (owner[0], owner[1], owner[2], "0" * 64)
    monkeypatch.setattr(checker, "FROZEN_REPOSITORY_FILES", tuple(rows))
    with pytest.raises(ValueError, match="FROZEN_SHA256_MISMATCH:F24_INGESTION_OWNER"):
        checker._verify_frozen_inputs(REPO)


def test_checker_rejects_frozen_current_census_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = list(checker.FROZEN_REPOSITORY_FILES)
    census = rows[10]
    rows[10] = (census[0], census[1], census[2], "0" * 64)
    monkeypatch.setattr(checker, "FROZEN_REPOSITORY_FILES", tuple(rows))
    with pytest.raises(ValueError, match="FROZEN_SHA256_MISMATCH"):
        checker._verify_frozen_inputs(REPO)


def test_checker_rejects_frozen_f24_formal_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(checker, "F24_FORMAL_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="FROZEN_SHA256_MISMATCH"):
        checker._verify_frozen_inputs(REPO)


def test_exact4_contains_no_materialized_reconciliation_or_census_artifact() -> None:
    assert all(path.startswith(("src/", "scripts/", "tests/", "docs/")) for path in checker.EXACT4_PATHS)
    assert not any(path.endswith((".csv", ".json")) for path in checker.EXACT4_PATHS)
    assert subject.F24_TRANSITION_ADAPTER_CREATED is False
    result = subject.reconcile_real_completed_human_decisions_with_f24_v1(REPO)
    assert not hasattr(result, "global_census")
    assert not hasattr(result, "priority_queue")
    assert not hasattr(result, "training_admitted")
