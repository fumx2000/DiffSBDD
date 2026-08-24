from __future__ import annotations

from copy import deepcopy
import csv
import importlib.util
import io
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


REPO = Path(__file__).resolve().parents[1]
FORMAL = REPO.parent / subject.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT

CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_ffq_completed_decision_ingestion_v1",
    REPO
    / "scripts/"
    "check_covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)

EXACT7 = tuple(
    sorted(path.as_posix() for path in subject.CANDIDATE_PUBLICATION_PATHS)
)


def _formal() -> dict[str, object]:
    return json.loads(FORMAL.read_bytes())


def _runtime_values() -> dict[str, object]:
    return {
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": subject.EXPECTED_ROLE_PROFILE,
        "DIRECT_VALID_CANONICAL_TASK_IDS_V1": subject.DIRECT_VALID_TASK_IDS,
        "DIRECT_PROFILE_TASK_APPLICABILITY_V1": (
            subject.DIRECT_PROFILE_TASK_APPLICABILITY
        ),
        "CURRENT11_TENSORIZER_DIRECT_PROFILE_SUPPORTED_V1": False,
        "DIRECT_PROFILE_RUNTIME_PRIMITIVES_READY_V1": True,
        "EXPANDED_TENSORIZER_INTEGRATION_PENDING_V1": True,
        "MODEL_ARCHITECTURE_CHANGE_REQUIRED_V1": False,
    }


def _canonical_values() -> dict[str, object]:
    return {
        "EXACT3_ROLES": ("scaffold", "linker", "warhead"),
        "CANONICAL_TASKS": subject.CANONICAL_TASKS,
    }


def _mutated_snapshot_artifacts(mutator) -> dict[str, bytes]:
    artifacts = dict(subject.build_artifacts_v1(REPO))
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    mutator(snapshot)
    artifacts[subject.SNAPSHOT] = subject._json_bytes(snapshot)
    return artifacts


def _precommit_observation() -> dict[str, object]:
    return {
        "branch": "main",
        "head": checker.BASELINE_COMMIT,
        "origin_main": checker.BASELINE_COMMIT,
        "ahead": 0,
        "behind": 0,
        "baseline_ancestor_of_head": True,
        "baseline_ancestor_of_origin_main": True,
        "modified_tracked_paths": (),
        "staged_paths": (),
        "untracked_paths": EXACT7,
        "tracked_candidate_paths": (),
    }


def _published_observation() -> dict[str, object]:
    successor = "f" * 40
    return {
        "branch": "main",
        "head": successor,
        "origin_main": successor,
        "ahead": 0,
        "behind": 0,
        "baseline_ancestor_of_head": True,
        "baseline_ancestor_of_origin_main": True,
        "modified_tracked_paths": (),
        "staged_paths": (),
        "untracked_paths": (),
        "tracked_candidate_paths": EXACT7,
    }


def test_valid_synthetic_precommit_lifecycle_profile() -> None:
    assert checker.validate_repository_observation_v1(_precommit_observation()) == (
        checker.PRECOMMIT_PROFILE
    )


def test_valid_synthetic_published_clean_descendant_lifecycle_profile() -> None:
    observation = _published_observation()
    assert observation["head"] != checker.BASELINE_COMMIT
    assert observation["head"] == observation["origin_main"]
    assert observation["tracked_candidate_paths"] == EXACT7
    assert observation["untracked_paths"] == ()
    assert checker.validate_repository_observation_v1(observation) == (
        checker.PUBLISHED_PROFILE
    )


def test_published_candidate_at_baseline_HEAD_is_rejected() -> None:
    observation = _published_observation()
    observation["head"] = checker.BASELINE_COMMIT
    observation["origin_main"] = checker.BASELINE_COMMIT
    with pytest.raises(ValueError, match=checker.LIFECYCLE_ERROR):
        checker.validate_repository_observation_v1(observation)


def test_mixed_tracked_and_untracked_candidate_is_rejected() -> None:
    observation = _published_observation()
    observation["tracked_candidate_paths"] = EXACT7[:3]
    observation["untracked_paths"] = EXACT7[3:]
    with pytest.raises(ValueError, match=checker.LIFECYCLE_ERROR):
        checker.validate_repository_observation_v1(observation)


def test_extra_untracked_path_is_rejected() -> None:
    observation = _precommit_observation()
    observation["untracked_paths"] = tuple(sorted((*EXACT7, "unexpected.txt")))
    with pytest.raises(ValueError, match=checker.LIFECYCLE_ERROR):
        checker.validate_repository_observation_v1(observation)


def test_missing_published_candidate_path_is_rejected() -> None:
    observation = _published_observation()
    observation["tracked_candidate_paths"] = EXACT7[:-1]
    with pytest.raises(ValueError, match=checker.LIFECYCLE_ERROR):
        checker.validate_repository_observation_v1(observation)


def test_published_baseline_not_ancestor_is_rejected() -> None:
    observation = _published_observation()
    observation["baseline_ancestor_of_head"] = False
    with pytest.raises(ValueError, match=checker.LIFECYCLE_ERROR):
        checker.validate_repository_observation_v1(observation)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("branch", "feature"),
        ("origin_main", "e" * 40),
        ("ahead", 1),
        ("behind", 1),
        ("modified_tracked_paths", ("tracked.txt",)),
        ("staged_paths", ("staged.txt",)),
    ),
)
def test_dirty_staged_or_diverged_lifecycle_is_rejected(
    field: str, value: object
) -> None:
    observation = _published_observation()
    observation[field] = value
    with pytest.raises(ValueError, match=checker.LIFECYCLE_ERROR):
        checker.validate_repository_observation_v1(observation)


def test_real_current_candidate_has_observation_determined_lifecycle_profile() -> None:
    observation = checker.observe_repository_state_v1(REPO)
    expected_profile = checker.validate_repository_observation_v1(observation)
    result = checker.verify_candidate_exact7_v1(REPO)

    assert result["lifecycle_profile"] == expected_profile
    if observation["head"] == checker.BASELINE_COMMIT:
        assert expected_profile == checker.PRECOMMIT_PROFILE
    else:
        assert expected_profile == checker.PUBLISHED_PROFILE
    assert result["candidate_publication_file_count"] == 7


def test_positive_build_exact4_and_event_matrix_exact8() -> None:
    artifacts = subject.build_artifacts_v1(REPO)
    assert tuple(artifacts) == subject.OUTPUT_FILENAMES
    assert len(artifacts) == 4
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    rows = list(
        csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8")))
    )
    assert snapshot["snapshot_role"] == (
        "ADDITIVE_IMMUTABLE_FFQ_COMPLETED_HUMAN_DECISION_SUCCESSOR"
    )
    assert len(snapshot["events"]) == len(rows) == 8
    assert len({row["canonical_event_id"] for row in rows}) == 8
    assert all(row["chemistry_known_positive"] == "true" for row in rows)
    assert all(row["training_admitted"] == "false" for row in rows)
    assert all(row["current_runtime_model_usable"] == "false" for row in rows)


def test_build_is_deterministic_and_contains_no_dynamic_metadata() -> None:
    first = subject.build_artifacts_v1(REPO)
    second = subject.build_artifacts_v1(REPO)
    assert first == second
    combined = b"".join(first.values())
    for forbidden in (
        b'"generated_at"',
        b'"hostname"',
        b'"pid"',
        b'"uuid"',
    ):
        assert forbidden not in combined


def test_repository_source_sha_mismatch_fails_closed(tmp_path: Path) -> None:
    relative = subject.RUNTIME_SOURCE_RELATIVE
    payload = bytearray((REPO / relative).read_bytes())
    payload[0] = ord("#")
    altered = tmp_path / "runtime.py"
    altered.write_bytes(payload)
    with pytest.raises(
        subject.FFQIngestionSafetyError,
        match="BOUND_SOURCE_SHA256_MISMATCH:direct_profile_runtime_contract",
    ):
        subject.verify_bound_inputs_v1(
            REPO, repository_path_overrides={relative: altered}
        )


def test_formal_decision_sha_mismatch_fails_closed(tmp_path: Path) -> None:
    payload = bytearray(FORMAL.read_bytes())
    payload[1] = ord("!")
    altered = tmp_path / "formal.json"
    altered.write_bytes(payload)
    with pytest.raises(
        subject.FFQIngestionSafetyError,
        match="BOUND_SOURCE_SHA256_MISMATCH:formal_FFQ_human_decision",
    ):
        subject.verify_bound_inputs_v1(REPO, formal_decision_path=altered)


@pytest.mark.parametrize("mode", ("duplicate", "missing"))
def test_formal_event_identity_coverage_fails_closed(mode: str) -> None:
    formal = _formal()
    events = formal["event_level_human_decisions"]
    if mode == "duplicate":
        events[-1] = deepcopy(events[0])
    else:
        events.pop()
    with pytest.raises(subject.FFQIngestionSafetyError):
        subject.validate_formal_decision_v1(formal)


@pytest.mark.parametrize(
    ("pdb_id", "replacement"),
    (("3VCY", "EXCLUDE"), ("4R7U", "EXCLUDE")),
)
def test_event_token_drift_fails_closed(pdb_id: str, replacement: str) -> None:
    formal = _formal()
    event = next(
        row for row in formal["event_level_human_decisions"] if row["pdb_id"] == pdb_id
    )
    event["event_training_use_decision"] = replacement
    with pytest.raises(
        subject.FFQIngestionSafetyError,
        match="FORMAL_EVENT_TRAINING_USE_TOKEN_DRIFT",
    ):
        subject.validate_formal_decision_v1(formal)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("chemistry_identity", "UNKNOWN"),
        ("negative_chemistry", True),
        ("task_domain_negative", True),
        ("distance_threshold_rejection", True),
    ),
)
def test_4R7U_chemistry_positive_semantics_loss_fails_closed(
    field: str, value: object
) -> None:
    formal = _formal()
    event = next(
        row for row in formal["event_level_human_decisions"] if row["pdb_id"] == "4R7U"
    )
    event[field] = value
    with pytest.raises(
        subject.FFQIngestionSafetyError,
        match="FFQ_4R7U_CHEMISTRY_POSITIVE_SEMANTICS_LOST",
    ):
        subject.validate_formal_decision_v1(formal)


def test_reactive_pair_drift_fails_closed() -> None:
    formal = _formal()
    formal["reactive_pair_human_decision"]["post_ligand_atom"] = "C2"
    with pytest.raises(
        subject.FFQIngestionSafetyError,
        match="FORMAL_REACTIVE_PAIR_SEMANTICS_DRIFT",
    ):
        subject.validate_formal_decision_v1(formal)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        ("scaffold_atom_ids", ["O2", "O3", "P1"], "FORMAL_SCAFFOLD_ROLE_ATOM_DRIFT"),
        ("linker_atom_ids", ["C2"], "FORMAL_FFQ_LINKER_NOT_EXACTLY_EMPTY"),
        ("warhead_atom_ids", ["C1", "C2", "O1"], "FORMAL_WARHEAD_ROLE_ATOM_DRIFT"),
        ("role_profile", "STRICT_LINKER_PRESENT_V1", "FORMAL_ROLE_PROFILE_DRIFT"),
    ),
)
def test_role_partition_or_profile_drift_fails_closed(
    field: str, value: object, reason: str
) -> None:
    formal = _formal()
    formal["role_human_decision"][field] = value
    with pytest.raises(subject.FFQIngestionSafetyError, match=reason):
        subject.validate_formal_decision_v1(formal)


@pytest.mark.parametrize(
    ("kind", "field", "value"),
    (
        ("canonical", "CANONICAL_TASKS", subject.CANONICAL_TASKS[:4]),
        ("runtime", "DIRECT_VALID_CANONICAL_TASK_IDS_V1", (0, 1, 3, 4)),
        ("runtime", "CURRENT11_TENSORIZER_DIRECT_PROFILE_SUPPORTED_V1", True),
        ("runtime", "DIRECT_PROFILE_RUNTIME_PRIMITIVES_READY_V1", False),
    ),
)
def test_canonical_or_direct_runtime_contract_drift_fails_closed(
    kind: str, field: str, value: object
) -> None:
    canonical = _canonical_values()
    runtime = _runtime_values()
    (canonical if kind == "canonical" else runtime)[field] = value
    with pytest.raises(subject.FFQIngestionSafetyError):
        subject.validate_runtime_contract_v1(canonical, runtime)


@pytest.mark.parametrize(
    "mutator",
    (
        lambda snapshot: snapshot["reaction_family_candidate"].update(
            project_level_authority_available=True
        ),
        lambda snapshot: snapshot["warhead_rule_candidate"].update(
            training_class_target_available=True
        ),
        lambda snapshot: snapshot["deferred_semantics"].update(
            SMARTS_status="MATERIALIZED", approved_warhead_smarts="[*:1]"
        ),
        lambda snapshot: snapshot["events"][0].update(training_admitted=True),
        lambda snapshot: snapshot["events"][0].update(
            current_runtime_model_usable=True
        ),
        lambda snapshot: snapshot["canonical_task_contract"].update(
            global_canonical_task_count=6
        ),
    ),
)
def test_artifact_authority_training_and_task_drift_fails_closed(mutator) -> None:
    artifacts = _mutated_snapshot_artifacts(mutator)
    with pytest.raises(subject.FFQIngestionSafetyError):
        subject.validate_artifacts_v1(artifacts)


def test_dynamic_metadata_is_rejected() -> None:
    artifacts = dict(subject.build_artifacts_v1(REPO))
    manifest = json.loads(artifacts[subject.MANIFEST])
    manifest["generated_at"] = "2026-08-23T00:00:00Z"
    artifacts[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(
        subject.FFQIngestionSafetyError, match="DYNAMIC_METADATA_FORBIDDEN"
    ):
        subject.validate_artifacts_v1(artifacts)


def test_legacy_overlay_mutation_fails_source_binding(tmp_path: Path) -> None:
    relative = subject.IMMUTABLE_REPOSITORY_BINDINGS[0][0]
    payload = bytearray((REPO / relative).read_bytes())
    payload[0] = ord("[")
    altered = tmp_path / "legacy.json"
    altered.write_bytes(payload)
    with pytest.raises(
        subject.FFQIngestionSafetyError,
        match="BOUND_SOURCE_SHA256_MISMATCH:legacy_human_review_overlay_read_only",
    ):
        subject.verify_bound_inputs_v1(
            REPO, repository_path_overrides={relative: altered}
        )


def test_POST_geometry_three_layer_guard_and_direct_task_reasons() -> None:
    artifacts = subject.build_artifacts_v1(REPO)
    rows = list(
        csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8")))
    )
    three = [row for row in rows if row["pdb_id"] == "3VCY"]
    four = [row for row in rows if row["pdb_id"] == "4R7U"]
    assert len(three) == len(four) == 4
    assert all(
        row["independent_POST_geometry_human_decision_available"] == "false"
        and row["POST_geometry_source_evidence_status"]
        == "PRESENT_IN_UPSTREAM_EVIDENCE_LINEAGE_NOT_REAUTHORIZED_HERE"
        and row["POST_geometry_training_label_available_now"] == "false"
        for row in three
    )
    assert all(
        row["independent_POST_geometry_human_decision_available"] == "true"
        and row["model_supervision_usable"] == "false"
        for row in four
    )
    applicability = json.loads(three[0]["canonical_task_applicability_json"])
    assert len(applicability) == 5
    assert [row["task_id"] for row in applicability if row["profile_applicable"]] == [
        0,
        3,
        4,
    ]
    assert applicability[1]["applicability_reason"] == (
        "not_applicable_empty_linker_redundant_with_A"
    )
    assert applicability[2]["applicability_reason"] == (
        "not_applicable_empty_non_C_fixed_context"
    )


def test_owner_has_no_torch_or_model_dependency() -> None:
    source = (REPO / subject.SOURCE_RELATIVE).read_text(encoding="utf-8")
    assert "import torch" not in source
    assert "equivariant_diffusion" not in source
    assert "lightning_modules" not in source
