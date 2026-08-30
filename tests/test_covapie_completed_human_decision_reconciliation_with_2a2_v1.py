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
    covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1
    as two_a2_ingestion_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_2a2_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_successor,
)


ERROR = subject.CompletedDecisionReconciliationWith2A2Error
GENERIC_ERROR = generic.CompletedDecisionReconciliationError
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_completed_human_decision_reconciliation_with_2a2_v1",
    REPO
    / "scripts/check_covapie_completed_human_decision_reconciliation_with_2a2_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return two_a2_ingestion_owner.load_frozen_formal_decision_v1(
        REPO, execute_formal_validator=False
    )


@pytest.fixture(scope="module")
def source(bound: dict[str, object]) -> generic.NormalizedDecisionSource:
    return subject._project_validated_2a2_binding_v1(bound)


@pytest.fixture(scope="module")
def sources() -> tuple[generic.NormalizedDecisionSource, ...]:
    return subject.load_real_completed_decision_sources_with_2a2_v1(REPO)


@pytest.fixture(scope="module")
def result() -> generic.ReconciliationResult:
    return subject.reconcile_real_completed_human_decisions_with_2a2_v1(REPO)


def _historical() -> list[dict[str, str]]:
    return [
        dict(row) for row in generic.load_real_historical_reconciliation_v1(REPO)
    ]


def _adapted_historical() -> tuple[dict[str, str], ...]:
    return onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        generic.load_real_historical_reconciliation_v1(REPO)
    )


def _set_status(row: dict[str, str], status: str) -> None:
    row["current_review_status"] = status
    row["calibration_eligible"] = (
        "true" if status == generic.CURRENTLY_UNREVIEWED else "false"
    )
    row["calibration_exclusion_reason"] = (
        "" if status == generic.CURRENTLY_UNREVIEWED else status
    )


def _mutate_nested(
    value: dict[str, object], path: tuple[str, ...], replacement: object
) -> dict[str, object]:
    changed = deepcopy(value)
    cursor = changed
    for key in path[:-1]:
        cursor = cursor[key]  # type: ignore[assignment,index]
    cursor[path[-1]] = replacement
    return changed


def test_public_api_is_minimal_and_2a2_transition_adapter_is_not_created() -> None:
    assert subject.__all__ == checker.EXPECTED_PUBLIC_API
    assert subject.TWO_A2_TRANSITION_ADAPTER_CREATED is False
    tree = ast.parse(Path(subject.__file__).read_bytes())
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert not any(
        name.lower().startswith("_adapt_2a2")
        or ("2a2" in name.lower() and "transition" in name.lower())
        for name in function_names
    )
    calls = [
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    ]
    assert calls.count("load_real_completed_decision_sources_with_f24_v1") == 1
    assert calls.count("project_2a2_completed_decision_v1") == 1
    assert calls.count("load_frozen_formal_decision_v1") == 1
    assert calls.count(
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1"
    ) == 1
    assert calls.count("reconcile_completed_human_decisions_v1") == 1
    assert calls.count("reconcile_real_completed_human_decisions_with_f24_v1") == 0


def test_successor_has_no_second_parse_overlay_next_pending_or_training_runtime() -> None:
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
    assert "covapie_2a2_event_task_label_availability_v1.csv" not in text
    assert "completed_human_decision_snapshot_v1.json" not in text
    assert "COVAPIE_BULK_REVIEW_UNIT_7D83F048AF8A2295" not in text
    assert "I12" not in text


def test_successor_reuses_generic_types_without_schema_fork(
    source: generic.NormalizedDecisionSource,
) -> None:
    assert type(source) is generic.NormalizedDecisionSource
    assert type(source.binding) is generic.SourceBinding
    assert all(
        type(fact) is generic.NormalizedCompletedDecisionFact
        for fact in source.facts
    )
    tree = ast.parse(Path(subject.__file__).read_bytes())
    classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert not classes & {
        "SourceBinding",
        "NormalizedCompletedDecisionFact",
        "NormalizedDecisionSource",
        "ReconciliationResult",
    }


def test_2a2_projector_calls_public_ingestion_owner_once(
    bound: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Path] = []

    def wrapped(repo_root: Path) -> dict[str, object]:
        calls.append(repo_root)
        return bound

    monkeypatch.setattr(
        subject.two_a2_ingestion_owner,
        "load_frozen_formal_decision_v1",
        wrapped,
    )
    projected = subject.project_2a2_completed_decision_v1(repo_root=REPO)
    assert len(projected.facts) == 4
    assert calls == [REPO]


def test_2a2_projector_wraps_only_ingestion_safety_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_repo_root: Path) -> dict[str, object]:
        raise two_a2_ingestion_owner.TwoA2IngestionSafetyError("SOURCE_DRIFT")

    monkeypatch.setattr(
        subject.two_a2_ingestion_owner,
        "load_frozen_formal_decision_v1",
        fail,
    )
    with pytest.raises(ERROR, match="2A2_INGESTION_OWNER_VALIDATION_FAILED"):
        subject.project_2a2_completed_decision_v1(repo_root=REPO)


@pytest.mark.parametrize("interrupt", (KeyboardInterrupt, SystemExit))
def test_2a2_projector_propagates_base_exceptions(
    interrupt: type[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(_repo_root: Path) -> dict[str, object]:
        raise interrupt()

    monkeypatch.setattr(
        subject.two_a2_ingestion_owner,
        "load_frozen_formal_decision_v1",
        fail,
    )
    with pytest.raises(interrupt):
        subject.project_2a2_completed_decision_v1(repo_root=REPO)


def test_2a2_projection_exact4_binding_identity_and_narrow_semantics(
    source: generic.NormalizedDecisionSource,
) -> None:
    assert source.binding == generic.SourceBinding(
        source_path=(
            "covapie-state/manual-review-aids/"
            "cumulative1000-high-yield-calibration-v1/"
            "2A2_COVAPIE_BULK_REVIEW_UNIT_6B422BBF7FAD44F6/"
            "formal-human-decision-v1/2a2_formal_human_decision_v1.json"
        ),
        path_namespace="repository_parent_relative",
        byte_count=26532,
        sha256="f0b10505af55883a3a4305a637b2299d2d5e1a25ef9f8e979efaad361d7351bd",
        schema_version="covapie_2a2_exact4_formal_human_decision_v1",
        review_unit_id="COVAPIE_BULK_REVIEW_UNIT_6B422BBF7FAD44F6",
    )
    assert tuple(fact.canonical_event_id for fact in source.facts) == tuple(
        sorted(subject._TWO_A2_EVENT_IDS)
    )
    assert len(source.facts) == 4
    assert all(
        fact.human_review_completed is True
        and fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        and fact.task_relevance_disposition == generic.TASK_RELEVANT
        and fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        and fact.training_disposition == generic.TRAINING_EXCLUDE
        and fact.human_training_excluded is True
        and fact.source_decision_schema == subject._TWO_A2_FORMAL_DECISION_SCHEMA
        and fact.source_decision_sha256 == subject._TWO_A2_FORMAL_DECISION_SHA256
        and fact.source_binding_path == source.binding.source_path
        for fact in source.facts
    )


def test_rich_2a2_semantics_are_validated_upstream_before_projection(
    bound: dict[str, object],
) -> None:
    events = subject._validate_rich_2a2_semantics_v1(bound)
    assert tuple(event["canonical_event_id"] for event in events) == (
        subject._TWO_A2_EVENT_IDS
    )
    formal = bound["formal"]
    assert formal["human_approval"]["D1_task_relevance"] == "RELEVANT"
    assert formal["human_approval"]["D2_chemistry"] == "POSITIVE"
    assert formal["human_approval"]["D3_reactive_pair"] == "CONFIRM_OBSERVED_PAIR"
    assert formal["human_approval"]["D4_role_partition"] == "SELECT_CANDIDATE_4"
    assert formal["human_approval"]["D5_training_use"] == (
        "EXCLUDE_FROM_TRAINING_ONLY"
    )
    role = formal["selected_role_partition"]
    assert role["role_profile"] == "STRICT_LINKER_PRESENT_V1"
    assert role["warhead_role_atom_ids"] == ["SD"]
    assert role["linker_atom_ids"] == ["C1", "C15", "C16", "C17", "O18"]
    assert role["scaffold_atom_ids"] == list(two_a2_ingestion_owner.SCAFFOLD_ROLE)
    assert role["applicable_task_ids"] == [0, 1, 2, 3, 4]


def test_upstream_only_chemical_pre_post_seed_precedent_and_training_boundaries(
    bound: dict[str, object],
) -> None:
    formal = bound["formal"]
    chemical = formal["chemical_warhead_boundary"]
    assert chemical["chemical_warhead_atom_ids"] is None
    assert chemical["chemical_warhead_human_authoritative"] is False
    pre = formal["experimental_context_and_PRE_boundary"]
    assert pre["complete_PRE_disulfide_reagent_authority"] is False
    assert pre["PRE_topology_authority_created"] is False
    assert pre["PRE_geometry_authority_created"] is False
    assert formal["POST_evidence_boundary"][
        "POST_geometry_training_authority_created"
    ] is False
    assert formal["minimal_seed"] == {
        "minimal_seed_atom_ids": None,
        "minimal_seed_authority_created": False,
    }
    training = formal["training_use_human_decision"]
    assert training["candidate_for_future_training_admission"] is False
    assert training["formal_training_admitted"] is False
    assert training["current_runtime_model_usable"] is False
    precedent = formal["published_1F8_same_context_precedent"]
    assert "2A2_independent_human_review_still_required" not in precedent
    assert precedent["2A2_independent_human_review_completed"] is True
    assert precedent["precedent_did_not_substitute_for_2A2_independent_review"] is True


def test_generic_fact_is_exact_thin_contract_without_rich_2a2_fields(
    source: generic.NormalizedDecisionSource,
) -> None:
    assert tuple(
        field.name for field in fields(generic.NormalizedCompletedDecisionFact)
    ) == checker.EXPECTED_GENERIC_FACT_FIELDS
    assert all(
        not any(hasattr(fact, name) for name in checker.FORBIDDEN_FACT_ATTRIBUTES)
        for fact in source.facts
    )
    for rich_name in ("future_training_candidate", "warhead_role_atom_ids"):
        with pytest.raises(TypeError):
            generic.NormalizedCompletedDecisionFact(
                **{
                    field: getattr(source.facts[0], field)
                    for field in checker.EXPECTED_GENERIC_FACT_FIELDS
                },
                **{rich_name: True},
            )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("path", "wrong/2a2.json"),
        ("path_namespace", "wrong_namespace"),
        ("byte_count", 26533),
        ("sha256", "0" * 64),
        ("source_role", "WRONG_ROLE"),
        ("mode", "0600"),
    ),
)
def test_projector_rejects_formal_binding_drift(
    bound: dict[str, object], field: str, value: object
) -> None:
    changed = deepcopy(bound)
    changed["formal_decision_binding"][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match="2A2_FORMAL_DECISION_BINDING_INVALID"):
        subject._project_validated_2a2_binding_v1(changed)


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "extra_identity"))
def test_projector_rejects_missing_duplicate_or_extra_event(
    bound: dict[str, object], mutation: str
) -> None:
    changed = deepcopy(bound)
    events = changed["formal"]["event_level_human_decisions"]  # type: ignore[index]
    if mutation == "missing":
        events.pop()
        token = "EVENT_COUNT_NOT_EXACT4"
    elif mutation == "duplicate":
        events[1] = deepcopy(events[0])
        token = "EVENT_ID_DUPLICATE"
    else:
        events[0]["canonical_event_id"] = "EXTRA_2A2_EVENT"
        token = "EVENT_COVERAGE_NOT_EXACT4"
    with pytest.raises(ERROR, match=token):
        subject._project_validated_2a2_binding_v1(changed)


@pytest.mark.parametrize(
    ("path", "value", "token"),
    (
        (("human_approval", "D1_task_relevance"), "NOT_RELEVANT", "D1_D5"),
        (("human_approval", "D2_chemistry"), "NEGATIVE", "D1_D5"),
        (("human_approval", "D3_reactive_pair"), "REJECT", "D1_D5"),
        (("human_approval", "D4_role_partition"), "SELECT_CANDIDATE_3", "D1_D5"),
        (("human_approval", "D5_training_use"), "INCLUDE", "D1_D5"),
        (("selected_role_partition", "role_profile"), "WRONG", "STRICT_ROLE"),
        (("selected_role_partition", "warhead_role_atom_ids"), ["SD", "C1"], "STRICT_ROLE"),
        (("selected_role_partition", "linker_atom_ids"), [], "STRICT_ROLE"),
        (("selected_role_partition", "scaffold_atom_ids"), [], "STRICT_ROLE"),
        (("chemical_warhead_boundary", "chemical_warhead_atom_ids"), ["SD"], "CHEMICAL_WARHEAD"),
        (("chemical_warhead_boundary", "chemical_warhead_human_authoritative"), True, "CHEMICAL_WARHEAD"),
        (("experimental_context_and_PRE_boundary", "PRE_topology_authority_created"), True, "PRE_AUTHORITY"),
        (("experimental_context_and_PRE_boundary", "PRE_geometry_authority_created"), True, "PRE_AUTHORITY"),
        (("POST_evidence_boundary", "POST_geometry_training_authority_created"), True, "POST_TRAINING"),
        (("minimal_seed", "minimal_seed_authority_created"), True, "MINIMAL_SEED"),
        (("training_use_human_decision", "human_training_excluded"), False, "EXCLUDE_OR_TRAINING"),
        (("training_use_human_decision", "candidate_for_future_training_admission"), True, "EXCLUDE_OR_TRAINING"),
        (("training_use_human_decision", "formal_training_admitted"), True, "EXCLUDE_OR_TRAINING"),
        (("published_1F8_same_context_precedent", "2A2_independent_human_review_completed"), False, "PRECEDENT"),
    ),
)
def test_projector_rejects_rich_semantics_tampering(
    bound: dict[str, object],
    path: tuple[str, str],
    value: object,
    token: str,
) -> None:
    changed = _mutate_nested(bound, ("formal", *path), value)
    with pytest.raises(ERROR, match=token):
        subject._project_validated_2a2_binding_v1(changed)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("candidate_for_future_training_admission", True),
        ("future_training_candidate_derived_by_ingestion", True),
        ("training_admitted", True),
        ("current_runtime_model_usable", True),
        ("ready_for_training", True),
    ),
)
def test_projector_rejects_ingestion_derived_training_boundary_drift(
    bound: dict[str, object],
    field: str,
    value: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = two_a2_ingestion_owner._training_boundary

    def drifted() -> dict[str, object]:
        result = original()
        result[field] = value
        return result

    monkeypatch.setattr(subject.two_a2_ingestion_owner, "_training_boundary", drifted)
    with pytest.raises(ERROR, match="INGESTION_DERIVED_AUTHORITY_BOUNDARY_INVALID"):
        subject._project_validated_2a2_binding_v1(bound)


def test_projector_rejects_stale_precedent_key(
    bound: dict[str, object],
) -> None:
    changed = deepcopy(bound)
    changed["formal"]["published_1F8_same_context_precedent"][  # type: ignore[index]
        "2A2_independent_human_review_still_required"
    ] = True
    with pytest.raises(ERROR, match="2A2_REVISED_PRECEDENT_STATE_INVALID"):
        subject._project_validated_2a2_binding_v1(changed)


def test_projector_rejects_future_census_mislabeled_current(
    bound: dict[str, object],
) -> None:
    changed = deepcopy(bound)
    changed["future_census_informational"]["status"] = "CURRENT"  # type: ignore[index]
    with pytest.raises(ERROR, match="FUTURE_CENSUS_INFORMATIONAL_BOUNDARY_INVALID"):
        subject._project_validated_2a2_binding_v1(changed)


def test_original_historical_2a2_prior_is_exact4_unreviewed() -> None:
    rows = _historical()
    subject._prove_2a2_original_unreviewed_prior_v1(rows)
    target = [
        row for row in rows if row["canonical_event_id"] in subject._TWO_A2_EVENT_IDS
    ]
    assert len(target) == 4
    assert {row["raw_review_unit_id"] for row in target} == {
        subject._TWO_A2_REVIEW_UNIT_ID
    }
    assert all(
        row["current_review_status"] == generic.CURRENTLY_UNREVIEWED
        and row["calibration_eligible"] == "true"
        and row["calibration_exclusion_reason"] == ""
        for row in target
    )


@pytest.mark.parametrize(
    "mutation",
    ("missing", "duplicate", "wrong_unit", "extra_unit_event", "already_reviewed"),
)
def test_historical_proof_rejects_inventory_or_prior_drift(mutation: str) -> None:
    rows = _historical()
    if mutation == "missing":
        rows = [
            row
            for row in rows
            if row["canonical_event_id"] != subject._TWO_A2_EVENT_IDS[0]
        ]
        token = "HISTORICAL_EVENT_MISSING"
    elif mutation == "duplicate":
        row = next(
            row
            for row in rows
            if row["canonical_event_id"] == subject._TWO_A2_EVENT_IDS[0]
        )
        rows.append(dict(row))
        token = "HISTORICAL_EVENT_DUPLICATE"
    elif mutation == "wrong_unit":
        row = next(
            row
            for row in rows
            if row["canonical_event_id"] == subject._TWO_A2_EVENT_IDS[0]
        )
        row["raw_review_unit_id"] = "WRONG_UNIT"
        token = "REVIEW_UNIT_EVENT_SET_NOT_EXACT4"
    elif mutation == "extra_unit_event":
        row = next(
            row
            for row in rows
            if row["canonical_event_id"] not in subject._TWO_A2_EVENT_IDS
        )
        row["raw_review_unit_id"] = subject._TWO_A2_REVIEW_UNIT_ID
        token = "REVIEW_UNIT_EVENT_SET_NOT_EXACT4"
    else:
        for row in rows:
            if row["canonical_event_id"] in subject._TWO_A2_EVENT_IDS:
                _set_status(row, generic.COMPLETED_HUMAN_POSITIVE)
        token = "PRIOR_STATE_NOT_EXACT4_UNREVIEWED"
    with pytest.raises(ERROR, match=token):
        subject._prove_2a2_original_unreviewed_prior_v1(rows)


@pytest.mark.parametrize(
    ("field", "value"),
    (("calibration_eligible", "false"), ("calibration_exclusion_reason", "X")),
)
def test_historical_proof_rejects_calibration_drift(field: str, value: str) -> None:
    rows = _historical()
    row = next(
        row
        for row in rows
        if row["canonical_event_id"] == subject._TWO_A2_EVENT_IDS[0]
    )
    row[field] = value
    with pytest.raises(ERROR, match="PRIOR_STATE_NOT_EXACT4_UNREVIEWED"):
        subject._prove_2a2_original_unreviewed_prior_v1(rows)


def test_onl_adapter_is_sole_transition_and_leaves_all_2a2_rows_equal() -> None:
    original = tuple(_historical())
    adapted = onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        original
    )
    subject._prove_2a2_rows_unchanged_after_onl_normalization_v1(original, adapted)
    target_ids = set(subject._TWO_A2_EVENT_IDS)
    assert {
        row["canonical_event_id"]: row
        for row in original
        if row["canonical_event_id"] in target_ids
    } == {
        row["canonical_event_id"]: row
        for row in adapted
        if row["canonical_event_id"] in target_ids
    }


def test_2a2_unchanged_proof_rejects_onl_adapter_change() -> None:
    original = tuple(_historical())
    adapted = [dict(row) for row in original]
    row = next(
        row
        for row in adapted
        if row["canonical_event_id"] == subject._TWO_A2_EVENT_IDS[0]
    )
    row["current_status_authority_sources_json"] = '["unexpected"]'
    with pytest.raises(ERROR, match="ONL_ADAPTER_CHANGED_2A2_ROW"):
        subject._prove_2a2_rows_unchanged_after_onl_normalization_v1(
            original, adapted
        )


def test_original_historical_with_exact13_sources_still_fails_for_onl(
    sources: tuple[generic.NormalizedDecisionSource, ...],
) -> None:
    with pytest.raises(GENERIC_ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"):
        generic.reconcile_completed_human_decisions_v1(
            generic.load_real_historical_reconciliation_v1(REPO), sources
        )


def test_exact12_predecessor_and_exact13_composition_are_collision_free(
    sources: tuple[generic.NormalizedDecisionSource, ...],
) -> None:
    predecessor = (
        subject.f24_successor.load_real_completed_decision_sources_with_f24_v1(REPO)
    )
    assert len(predecessor) == 12
    assert tuple(len(item.facts) for item in predecessor) == (
        checker.EXPECTED_PREDECESSOR_SOURCE_FACT_COUNTS
    )
    assert sum(len(item.facts) for item in predecessor) == 91
    assert len(sources) == 13
    assert tuple(len(item.facts) for item in sources) == checker.EXPECTED_SOURCE_FACT_COUNTS
    assert len({item.binding.stable_identity for item in sources}) == 13
    assert len({item.binding.review_unit_id for item in sources}) == 13
    event_ids = [fact.canonical_event_id for item in sources for fact in item.facts]
    assert len(event_ids) == len(set(event_ids)) == 95


def test_source_loader_calls_f24_predecessor_and_2a2_projector_once(
    source: generic.NormalizedDecisionSource,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_predecessor = (
        subject.f24_successor.load_real_completed_decision_sources_with_f24_v1
    )
    calls: Counter[str] = Counter()

    def wrapped_predecessor(root: Path) -> tuple[generic.NormalizedDecisionSource, ...]:
        calls["predecessor"] += 1
        return original_predecessor(root)

    def wrapped_projector(*, repo_root: Path) -> generic.NormalizedDecisionSource:
        del repo_root
        calls["projector"] += 1
        return source

    monkeypatch.setattr(
        subject.f24_successor,
        "load_real_completed_decision_sources_with_f24_v1",
        wrapped_predecessor,
    )
    monkeypatch.setattr(subject, "project_2a2_completed_decision_v1", wrapped_projector)
    loaded = subject.load_real_completed_decision_sources_with_2a2_v1(REPO)
    assert len(loaded) == 13
    assert calls == {"predecessor": 1, "projector": 1}


@pytest.mark.parametrize("drift", ("source_count", "fact_count"))
def test_source_loader_rejects_predecessor_composition_drift(
    drift: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    existing = list(
        subject.f24_successor.load_real_completed_decision_sources_with_f24_v1(REPO)
    )
    if drift == "source_count":
        existing.pop()
    else:
        existing[0] = replace(existing[0], facts=existing[0].facts[:-1])
    monkeypatch.setattr(
        subject.f24_successor,
        "load_real_completed_decision_sources_with_f24_v1",
        lambda _root: tuple(existing),
    )
    with pytest.raises(ERROR, match="EXISTING_F24_SOURCE_COMPOSITION_INVALID"):
        subject.load_real_completed_decision_sources_with_2a2_v1(REPO)


def test_source_loader_rejects_2a2_collision_with_predecessor91(
    source: generic.NormalizedDecisionSource,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = subject.f24_successor.load_real_completed_decision_sources_with_f24_v1(
        REPO
    )
    collision = replace(
        source,
        facts=(
            replace(
                source.facts[0],
                canonical_event_id=existing[0].facts[0].canonical_event_id,
            ),
            *source.facts[1:],
        ),
    )
    monkeypatch.setattr(
        subject,
        "project_2a2_completed_decision_v1",
        lambda *, repo_root: collision,
    )
    with pytest.raises(ERROR, match="2A2_SOURCE_PROJECTION_INVALID"):
        subject.load_real_completed_decision_sources_with_2a2_v1(REPO)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("review_unit_id", "WRONG_UNIT"),
        ("task_relevance_disposition", generic.TASK_NOT_RELEVANT),
        ("chemistry_disposition", generic.CHEMISTRY_NEGATIVE),
        ("training_disposition", generic.TRAINING_INCLUDE),
        ("human_training_excluded", False),
    ),
)
def test_source_loader_rejects_fact_semantics_drift(
    source: generic.NormalizedDecisionSource,
    field: str,
    value: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrong = replace(
        source,
        facts=(replace(source.facts[0], **{field: value}), *source.facts[1:]),
    )
    monkeypatch.setattr(
        subject,
        "project_2a2_completed_decision_v1",
        lambda *, repo_root: wrong,
    )
    with pytest.raises(ERROR, match="2A2_SOURCE_PROJECTION_INVALID"):
        subject.load_real_completed_decision_sources_with_2a2_v1(REPO)


def test_real_reconciliation_counts_training_and_final_2a2_authority(
    result: generic.ReconciliationResult,
    source: generic.NormalizedDecisionSource,
) -> None:
    assert result.review_summary == checker.EXPECTED_REVIEW_SUMMARY
    assert Counter(fact.training_disposition for fact in result.normalized_facts) == {
        generic.TRAINING_INCLUDE: 27,
        generic.TRAINING_EXCLUDE: 68,
    }
    expected_authority = json.dumps(
        [source.binding.source_path], separators=(",", ":"), sort_keys=True
    )
    target_rows = [
        row
        for row in result.reconciled_rows
        if row["canonical_event_id"] in subject._TWO_A2_EVENT_IDS
    ]
    target_facts = [
        fact
        for fact in result.normalized_facts
        if fact.canonical_event_id in subject._TWO_A2_EVENT_IDS
    ]
    assert len(target_rows) == len(target_facts) == 4
    assert all(
        row["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE
        and row["raw_review_unit_id"] == subject._TWO_A2_REVIEW_UNIT_ID
        and row["current_status_authority_sources_json"] == expected_authority
        for row in target_rows
    )
    assert all(
        fact.human_review_completed is True
        and fact.task_relevance_disposition == generic.TASK_RELEVANT
        and fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        and fact.training_disposition == generic.TRAINING_EXCLUDE
        and fact.human_training_excluded is True
        for fact in target_facts
    )


def test_exact_2a2_delta_relative_to_published_f24_chain(
    result: generic.ReconciliationResult,
) -> None:
    predecessor = (
        subject.f24_successor.reconcile_real_completed_human_decisions_with_f24_v1(
            REPO
        )
    )
    summary = result.review_summary
    prior = predecessor.review_summary
    dispositions = Counter(fact.training_disposition for fact in result.normalized_facts)
    prior_dispositions = Counter(
        fact.training_disposition for fact in predecessor.normalized_facts
    )
    assert summary["completed_positive_event_count"] - prior["completed_positive_event_count"] == 4
    assert summary["completed_positive_unit_count"] - prior["completed_positive_unit_count"] == 1
    assert summary["completed_total_event_count"] - prior["completed_total_event_count"] == 4
    assert summary["completed_total_unit_count"] - prior["completed_total_unit_count"] == 1
    assert summary["unreviewed_event_count"] - prior["unreviewed_event_count"] == -4
    assert summary["unreviewed_unit_count"] - prior["unreviewed_unit_count"] == -1
    assert dispositions[generic.TRAINING_INCLUDE] - prior_dispositions[generic.TRAINING_INCLUDE] == 0
    assert dispositions[generic.TRAINING_EXCLUDE] - prior_dispositions[generic.TRAINING_EXCLUDE] == 4


def test_source_order_is_semantically_deterministic(
    sources: tuple[generic.NormalizedDecisionSource, ...],
) -> None:
    rows = _adapted_historical()
    assert generic.reconcile_completed_human_decisions_v1(
        rows, sources
    ) == generic.reconcile_completed_human_decisions_v1(
        rows, tuple(reversed(sources))
    )


def test_checker_rejects_wrong_completed_positive_or_exclude_count(
    result: generic.ReconciliationResult,
) -> None:
    wrong_summary = dict(result.review_summary)
    wrong_summary["completed_positive_event_count"] = 94
    with pytest.raises(ValueError, match="RECONCILIATION_SUMMARY_INVALID"):
        checker._verify_reconciliation_counts_v1(
            replace(result, review_summary=wrong_summary)
        )
    excluded_index = next(
        index
        for index, fact in enumerate(result.normalized_facts)
        if fact.training_disposition == generic.TRAINING_EXCLUDE
    )
    changed_fact = replace(
        result.normalized_facts[excluded_index],
        training_disposition=generic.TRAINING_INCLUDE,
        human_training_excluded=False,
    )
    changed_facts = list(result.normalized_facts)
    changed_facts[excluded_index] = changed_fact
    with pytest.raises(ValueError, match="NORMALIZED_TRAINING_DISPOSITIONS_INVALID"):
        checker._verify_reconciliation_counts_v1(
            replace(
                result,
                normalized_facts=tuple(changed_facts),
            )
        )


def test_checker_rejects_source_order_nondeterminism(
    result: generic.ReconciliationResult,
    sources: tuple[generic.NormalizedDecisionSource, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    drifted_summary = dict(result.review_summary)
    drifted_summary["unreviewed_event_count"] = 220
    drifted = replace(result, review_summary=drifted_summary)

    def order_sensitive(_rows: object, _sources: object) -> generic.ReconciliationResult:
        nonlocal calls
        calls += 1
        return result if calls == 1 else drifted

    monkeypatch.setattr(
        checker.generic, "reconcile_completed_human_decisions_v1", order_sensitive
    )
    with pytest.raises(ValueError, match="SOURCE_ORDER_NOT_DETERMINISTIC"):
        checker._verify_source_order_determinism_v1(
            _adapted_historical(), sources, result
        )


def test_production_pipeline_calls_direct_delegates_once_without_f24_result(
    bound: dict[str, object],
) -> None:
    result, calls, original, adapted = checker._run_production_pipeline_counted(
        REPO, bound
    )
    assert calls == {
        "f24_source_loader": 1,
        "two_a2_projector": 1,
        "two_a2_ingestion_loader": 1,
        "onl_adapter": 1,
        "generic_reconciler": 1,
    }
    assert result.review_summary == checker.EXPECTED_REVIEW_SUMMARY
    subject._prove_2a2_rows_unchanged_after_onl_normalization_v1(original, adapted)


def test_current_f24_census_stays_published_and_2a2_unreviewed() -> None:
    published = checker._published_census_state(REPO)
    assert published["counts"] == checker.EXPECTED_CURRENT_CENSUS
    rows = published["rows"]
    target = [
        row for row in rows if row["canonical_event_id"] in subject._TWO_A2_EVENT_IDS
    ]
    assert len(target) == 4
    assert all(
        row["current_global_status"] == generic.CURRENTLY_UNREVIEWED
        for row in target
    )


def test_current_census_semantic_drift_is_rejected(tmp_path: Path) -> None:
    for relative in (checker.CURRENT_CENSUS_CSV, checker.CURRENT_CENSUS_SUMMARY):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((REPO / relative).read_bytes())
    summary_path = tmp_path / checker.CURRENT_CENSUS_SUMMARY
    summary = json.loads(summary_path.read_bytes())
    summary["reactive_pair"]["sample_level_authoritative_pair_count"] = 109
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(ValueError, match="PUBLISHED_CURRENT_CENSUS_COUNTS_INVALID"):
        checker._published_census_state(tmp_path)


def test_future_census_is_independently_derived_and_informational(
    source: generic.NormalizedDecisionSource,
    bound: dict[str, object],
) -> None:
    published = checker._published_census_state(REPO)
    derived = checker._verify_future_census_informational(source, bound, published)
    assert derived == checker.EXPECTED_FUTURE_CENSUS
    assert [
        derived["warhead_only_A"],
        derived["linker_plus_warhead_B"],
        derived["scaffold_plus_warhead_B2"],
        derived["scaffold_only_B3"],
        derived["scaffold_plus_linker_plus_warhead_C"],
    ] == [112, 52, 52, 112, 112]


def test_next_pending_is_derived_as_i12_and_not_hardcoded_in_production(
    result: generic.ReconciliationResult,
) -> None:
    pending = checker._derive_next_pending(result)
    assert {
        key: pending[key] for key in checker.EXPECTED_NEXT_PENDING
    } == checker.EXPECTED_NEXT_PENDING
    source_text = Path(subject.__file__).read_text(encoding="utf-8")
    assert pending["review_unit_id"] not in source_text
    assert "I12" not in source_text


def test_checker_exact4_frozen_architecture_and_all_gates() -> None:
    report = checker.run_check_v1(REPO)
    assert report["check"] == "PASS"
    assert report["exact4"]["count"] == 4
    assert report["exact4"]["lifecycle"] in checker._SUPPORTED_REPOSITORY_PROFILES
    assert report["exact4"]["third_successful_profile"] is False
    assert report["frozen_bindings"]["count"] == 13
    assert report["delegate_runtime_calls"] == {
        "f24_source_loader": 1,
        "two_a2_projector": 1,
        "two_a2_ingestion_loader": 1,
        "onl_adapter": 1,
        "generic_reconciler": 1,
    }
    assert report["source_fact_counts"] == checker.EXPECTED_SOURCE_FACT_COUNTS
    assert report["normalized_fact_count"] == 95
    assert report["event_collisions"] == 0
    assert report["global_census_update"] == "NOT_DONE"
    assert report["priority_queue_update"] == "NOT_DONE"
    assert report["i12_review_started"] is False
    assert report["reconciliation_materialized"] is False
    assert report["ready_for_external_review"] is True
    assert report["ready_for_training"] is False


@pytest.mark.parametrize(
    "expected_profile", (checker._CANDIDATE_UNTRACKED, checker._TRACKED_CLEAN)
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
        (set(checker.EXACT4_PATHS[:2]), tuple("?? " + p for p in checker.EXACT4_PATHS[2:]), (), ()),
        (set(), (*tuple("?? " + p for p in checker.EXACT4_PATHS), "?? extra.txt"), (), ()),
        (set(checker.EXACT4_PATHS), tuple("A  " + p for p in checker.EXACT4_PATHS), (), checker.EXACT4_PATHS),
        ({checker.EXACT4_PATHS[0]}, ("A  " + checker.EXACT4_PATHS[0], *tuple("?? " + p for p in checker.EXACT4_PATHS[1:])), (), (checker.EXACT4_PATHS[0],)),
        (set(checker.EXACT4_PATHS), (" M " + checker.EXACT4_PATHS[0],), (checker.EXACT4_PATHS[0],), ()),
        (set(checker.EXACT4_PATHS), ("M  " + checker.EXACT4_PATHS[0],), (), (checker.EXACT4_PATHS[0],)),
        (set(checker.EXACT4_PATHS), (" M unrelated.txt",), ("unrelated.txt",), ()),
        (set(checker.EXACT4_PATHS), ("M  unrelated.txt",), (), ("unrelated.txt",)),
        (set(), tuple("?? " + p for p in checker.EXACT4_PATHS[:-1]), (), ()),
        (set(checker.EXACT4_PATHS), ("UU " + checker.EXACT4_PATHS[0],), (), ()),
    ),
)
def test_repository_profile_classifier_rejects_partial_staged_dirty_or_extra(
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


@pytest.mark.parametrize(
    "path", ("candidate.pt", "build/__pycache__/module.pyc", "scratch.tmp")
)
def test_checker_rejects_dirty_forbidden_or_transient_paths(path: str) -> None:
    with pytest.raises(ValueError, match="FORBIDDEN_OR_TRANSIENT_REPOSITORY_PATH"):
        checker._reject_dirty_forbidden_or_transient_paths(("?? " + path,), (), ())


@pytest.mark.parametrize(
    ("label", "index"),
    (
        ("2A2_INGESTION_OWNER", 6),
        ("2A2_PUBLISHED_MATRIX_CROSS_CHECK_ONLY", 7),
        ("F24_RECONCILIATION_SOURCE_PREDECESSOR", 2),
    ),
)
def test_checker_rejects_frozen_owner_matrix_or_predecessor_drift(
    label: str, index: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    rows = list(checker.FROZEN_REPOSITORY_FILES)
    record = rows[index]
    assert record[0] == label
    rows[index] = (record[0], record[1], record[2], "0" * 64)
    monkeypatch.setattr(checker, "FROZEN_REPOSITORY_FILES", tuple(rows))
    with pytest.raises(ValueError, match="FROZEN_SHA256_MISMATCH:" + label):
        checker._verify_frozen_inputs(REPO)


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


def test_exact4_contains_no_reconciliation_or_census_artifact_and_no_training(
    result: generic.ReconciliationResult,
) -> None:
    assert all(
        path.startswith(("src/", "scripts/", "tests/", "docs/"))
        for path in checker.EXACT4_PATHS
    )
    assert not any(path.endswith((".csv", ".json")) for path in checker.EXACT4_PATHS)
    assert subject.TWO_A2_TRANSITION_ADAPTER_CREATED is False
    assert not hasattr(result, "global_census")
    assert not hasattr(result, "priority_queue")
    assert not hasattr(result, "training_admitted")
