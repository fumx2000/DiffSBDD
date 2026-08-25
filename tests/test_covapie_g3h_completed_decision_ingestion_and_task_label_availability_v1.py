from __future__ import annotations

from copy import deepcopy
import csv
import importlib.util
import io
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_g3h_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


REPO = Path(__file__).resolve().parents[1]
FORMAL = REPO.parent / subject.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_g3h_completed_decision_ingestion_v1",
    REPO
    / "scripts/"
    "check_covapie_g3h_completed_decision_ingestion_and_task_label_availability_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


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


def _mutated_artifacts(name: str, mutator) -> dict[str, bytes]:
    artifacts = dict(subject.build_artifacts_v1(REPO))
    document = json.loads(artifacts[name])
    mutator(document)
    artifacts[name] = subject._json_bytes(document)
    return artifacts


def _coordinated_snapshot_manifest_artifacts(mutator) -> dict[str, bytes]:
    artifacts = dict(subject.build_artifacts_v1(REPO))
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    manifest = json.loads(artifacts[subject.MANIFEST])
    mutator(snapshot, manifest)
    artifacts[subject.SNAPSHOT] = subject._json_bytes(snapshot)
    manifest["output_artifact_bindings"][subject.SNAPSHOT]["sha256"] = (
        subject._sha(artifacts[subject.SNAPSHOT])
    )
    artifacts[subject.MANIFEST] = subject._json_bytes(manifest)
    return artifacts


def test_formal_binding_constants_match_real_source() -> None:
    payload = FORMAL.read_bytes()
    assert len(payload) == subject.FORMAL_DECISION_BYTE_COUNT == 22456
    assert subject._sha(payload) == subject.FORMAL_DECISION_SHA256
    assert json.loads(payload)["schema_version"] == subject.FORMAL_DECISION_SCHEMA


def test_positive_build_exact4_snapshot_and_matrix_exact8() -> None:
    artifacts = subject.build_artifacts_v1(REPO)
    assert tuple(artifacts) == subject.OUTPUT_FILENAMES
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    rows = list(
        csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8")))
    )
    assert len(snapshot["events"]) == len(rows) == 8
    assert tuple(row["canonical_event_id"] for row in rows) == (
        subject.EXPECTED_EVENT_IDS
    )
    assert all(row["completed_lane"] == subject.EXPECTED_COMPLETED_LANE for row in rows)
    assert all(row["chemistry_identity_label"] == "POSITIVE" for row in rows)
    assert all(row["training_use_allowed"] == "false" for row in rows)
    assert all(row["training_admitted"] == "false" for row in rows)
    assert all(row["authority_created_by_this_successor"] == "false" for row in rows)


def test_build_is_deterministic_and_has_canonical_text() -> None:
    first = subject.build_artifacts_v1(REPO)
    second = subject.build_artifacts_v1(REPO)
    assert first == second
    for payload in first.values():
        assert payload.endswith(b"\n")
        assert not payload.endswith(b"\n\n")
        assert b"\r" not in payload
        assert b"\x00" not in payload
        assert not payload.startswith(b"\xef\xbb\xbf")


def test_double_materialization_to_distinct_directories_is_byte_identical(
    tmp_path: Path,
) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = subject.materialize_artifacts_v1(REPO, output_root=first_root)
    second = subject.materialize_artifacts_v1(REPO, output_root=second_root)
    assert first == second
    for name in subject.OUTPUT_FILENAMES:
        assert (first_root / name).read_bytes() == (second_root / name).read_bytes()


def test_formal_source_byte_count_change_fails_closed(tmp_path: Path) -> None:
    altered = tmp_path / "formal.json"
    altered.write_bytes(FORMAL.read_bytes() + b" ")
    with pytest.raises(
        subject.G3HIngestionSafetyError,
        match="BOUND_SOURCE_BYTE_COUNT_MISMATCH:formal_G3H_human_decision",
    ):
        subject.verify_bound_inputs_v1(REPO, formal_decision_path=altered)


def test_formal_source_sha_change_fails_closed(tmp_path: Path) -> None:
    payload = bytearray(FORMAL.read_bytes())
    payload[1] = ord("!")
    altered = tmp_path / "formal.json"
    altered.write_bytes(payload)
    with pytest.raises(
        subject.G3HIngestionSafetyError,
        match="BOUND_SOURCE_SHA256_MISMATCH:formal_G3H_human_decision",
    ):
        subject.verify_bound_inputs_v1(REPO, formal_decision_path=altered)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("schema_version", "wrong_schema"),
        ("review_unit_id", "WRONG_REVIEW_UNIT"),
        ("human_review_completed", False),
        ("formal_authority_created", False),
    ),
)
def test_formal_top_level_drift_fails_closed(field: str, value: object) -> None:
    formal = _formal()
    formal[field] = value
    with pytest.raises(subject.G3HIngestionSafetyError):
        subject.validate_formal_decision_v1(formal)


@pytest.mark.parametrize("mode", ("event_omitted", "event_duplicate", "id_omitted", "id_duplicate"))
def test_formal_event_exact8_coverage_fails_closed(mode: str) -> None:
    formal = _formal()
    if mode == "event_omitted":
        formal["event_level_human_decisions"].pop()
    elif mode == "event_duplicate":
        formal["event_level_human_decisions"][-1] = deepcopy(
            formal["event_level_human_decisions"][0]
        )
    elif mode == "id_omitted":
        formal["canonical_event_ids"].pop()
    else:
        formal["canonical_event_ids"][-1] = formal["canonical_event_ids"][0]
    with pytest.raises(subject.G3HIngestionSafetyError):
        subject.validate_formal_decision_v1(formal)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("human_task_relevance_decision", "NOT_RELEVANT"),
        ("human_chemistry_support_disposition", "NEGATIVE"),
        ("negative_chemistry", True),
        ("task_domain_negative", True),
        ("human_reactive_pair_acceptance", "REJECT"),
        ("ligand_reactive_endpoint", "G3H:C2"),
        ("human_role_partition_acceptance", "SELECT_CANDIDATE_2"),
        ("selected_candidate_index", 2),
        ("human_event_training_use_disposition", "INCLUDE"),
        ("human_event_training_use_disposition", "NOT_APPLICABLE"),
        ("human_training_excluded", False),
        ("decision_finalized", False),
        ("training_admitted", True),
    ),
)
def test_formal_event_semantic_drift_fails_closed(field: str, value: object) -> None:
    formal = _formal()
    formal["event_level_human_decisions"][0][field] = value
    with pytest.raises(subject.G3HIngestionSafetyError):
        subject.validate_formal_decision_v1(formal)


def test_reactive_pair_C1_drift_fails_closed() -> None:
    formal = _formal()
    formal["reactive_pair_human_decision"]["ligand_reactive_atom_id"] = "C2"
    with pytest.raises(
        subject.G3HIngestionSafetyError,
        match="FORMAL_REACTIVE_PAIR_SEMANTICS_DRIFT",
    ):
        subject.validate_formal_decision_v1(formal)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        ("selected_candidate_index", 2, "FORMAL_ROLE_SELECTED_CANDIDATE_INDEX_DRIFT"),
        ("linker_atom_ids", ["C2"], "FORMAL_G3H_LINKER_NOT_EXACTLY_EMPTY"),
        (
            "scaffold_atom_ids",
            ["C1", "C2", "C3", "O1P", "O2", "O2P", "O3P", "O4P", "P"],
            "FORMAL_SCAFFOLD_ROLE_ATOM_DRIFT",
        ),
        (
            "warhead_atom_ids",
            ["C1"],
            "FORMAL_WARHEAD_ROLE_ATOM_DRIFT",
        ),
        ("selected_role_profile", "OTHER_PROFILE", "FORMAL_ROLE_PROFILE_DRIFT"),
    ),
)
def test_role_partition_drift_fails_closed(
    field: str, value: object, reason: str
) -> None:
    formal = _formal()
    formal["role_human_decision"][field] = value
    with pytest.raises(subject.G3HIngestionSafetyError, match=reason):
        subject.validate_formal_decision_v1(formal)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda boundary: boundary["tasks"][1].update(structurally_applicable=True),
        lambda boundary: boundary["tasks"][2].update(structurally_applicable=True),
        lambda boundary: boundary["tasks"].pop(3),
        lambda boundary: boundary["tasks"].append(
            {
                "task_id": 5,
                "semantic_long_name": "sixth_task",
                "display_alias": "D",
                "structurally_applicable": True,
                "reason": "INVALID",
            }
        ),
        lambda boundary: boundary.update(global_canonical_task_count=6),
    ),
)
def test_formal_canonical_mask_drift_fails_closed(mutation) -> None:
    formal = _formal()
    mutation(formal["canonical_exact5_mask_boundary"])
    with pytest.raises(
        subject.G3HIngestionSafetyError,
        match="FORMAL_CANONICAL_EXACT5_MASK_BOUNDARY_INVALID",
    ):
        subject.validate_formal_decision_v1(formal)


@pytest.mark.parametrize(
    ("kind", "field", "value"),
    (
        ("canonical", "CANONICAL_TASKS", subject.CANONICAL_TASKS[:4]),
        ("canonical", "CANONICAL_TASKS", (*subject.CANONICAL_TASKS, (5,))),
        ("runtime", "DIRECT_VALID_CANONICAL_TASK_IDS_V1", (0, 1, 3, 4)),
        ("runtime", "CURRENT11_TENSORIZER_DIRECT_PROFILE_SUPPORTED_V1", True),
        ("runtime", "DIRECT_PROFILE_RUNTIME_PRIMITIVES_READY_V1", False),
    ),
)
def test_canonical_or_runtime_owner_drift_fails_closed(
    kind: str, field: str, value: object
) -> None:
    canonical = _canonical_values()
    runtime = _runtime_values()
    (canonical if kind == "canonical" else runtime)[field] = value
    with pytest.raises(subject.G3HIngestionSafetyError):
        subject.validate_runtime_contract_v1(canonical, runtime)


def test_bound_semantic_owner_sha_drift_fails_closed(tmp_path: Path) -> None:
    relative = subject.RUNTIME_SOURCE_RELATIVE
    payload = bytearray((REPO / relative).read_bytes())
    payload[0] = ord("#")
    altered = tmp_path / "runtime.py"
    altered.write_bytes(payload)
    with pytest.raises(
        subject.G3HIngestionSafetyError,
        match="BOUND_SOURCE_SHA256_MISMATCH:direct_profile_runtime_contract",
    ):
        subject.verify_bound_inputs_v1(
            REPO, repository_path_overrides={relative: altered}
        )


@pytest.mark.parametrize(
    "mutator",
    (
        lambda snapshot: snapshot["events"][0].update(
            completed_lane="COMPLETED_HUMAN_NEGATIVE"
        ),
        lambda snapshot: snapshot["events"][0].update(chemistry="NEGATIVE"),
        lambda snapshot: snapshot["events"][0].update(training_use_allowed=True),
        lambda snapshot: snapshot["events"][0].update(model_supervision_usable=True),
        lambda snapshot: snapshot["events"][0].update(training_admitted=True),
        lambda snapshot: snapshot["authority_provenance"].update(
            authority_created_by_this_successor=True
        ),
        lambda snapshot: snapshot["geometry_authority_boundary"].update(
            PRE_geometry_authority_available=True
        ),
        lambda snapshot: snapshot["geometry_authority_boundary"].update(
            POST_geometry_training_authority_available=True
        ),
        lambda snapshot: snapshot["auxiliary_authority_boundary"].update(
            reaction_family_training_class_target_available=True
        ),
        lambda snapshot: snapshot["auxiliary_authority_boundary"].update(
            warhead_rule_training_class_target_available=True
        ),
        lambda snapshot: snapshot["auxiliary_authority_boundary"].update(
            warhead_type_target_available=True
        ),
        lambda snapshot: snapshot["auxiliary_authority_boundary"].update(
            reusable_authority_label_available=True
        ),
        lambda snapshot: snapshot["training_boundary"].update(
            training_materialization_allowed_count=1
        ),
        lambda snapshot: snapshot["training_boundary"].update(
            current_runtime_model_usable_count=1
        ),
        lambda snapshot: snapshot["canonical_task_contract"].update(
            global_canonical_task_count=6
        ),
    ),
)
def test_artifact_authority_training_and_task_promotions_fail_closed(mutator) -> None:
    artifacts = _mutated_artifacts(subject.SNAPSHOT, mutator)
    with pytest.raises(subject.G3HIngestionSafetyError):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


def test_RED_001_coordinated_formal_authority_training_promotion_fails_closed() -> None:
    artifacts = _coordinated_snapshot_manifest_artifacts(
        lambda snapshot, manifest: snapshot[
            "formal_authority_boundary_source"
        ].update(training_admitted=True)
    )
    with pytest.raises(
        subject.G3HIngestionSafetyError,
        match="SNAPSHOT_FORMAL_AUTHORITY_BOUNDARY_SOURCE_INVALID",
    ):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        pytest.param(
            "sample_level_role_decision_created_by_ingestion",
            True,
            id="RED_002_created_by_ingestion",
        ),
        pytest.param("scaffold_connected", False, id="RED_003_scaffold_connected"),
        pytest.param("warhead_connected", False, id="RED_004_warhead_connected"),
    ),
)
def test_coordinated_role_snapshot_drift_fails_closed(
    field: str, value: object
) -> None:
    artifacts = _coordinated_snapshot_manifest_artifacts(
        lambda snapshot, manifest: snapshot["role_decision"].update(
            {field: value}
        )
    )
    with pytest.raises(
        subject.G3HIngestionSafetyError, match="SNAPSHOT_ROLE_DECISION_INVALID"
    ):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        pytest.param(
            "expanded_tensorizer_integration_pending",
            False,
            id="RED_005_expanded_pending",
        ),
        pytest.param(
            "model_architecture_change_required",
            True,
            id="RED_006_architecture_required",
        ),
    ),
)
def test_coordinated_snapshot_runtime_drift_fails_closed(
    field: str, value: object
) -> None:
    artifacts = _coordinated_snapshot_manifest_artifacts(
        lambda snapshot, manifest: snapshot[
            "direct_profile_runtime_contract"
        ].update({field: value})
    )
    with pytest.raises(
        subject.G3HIngestionSafetyError, match="SNAPSHOT_RUNTIME_CONTRACT_INVALID"
    ):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        pytest.param("reviewer_id", "other", id="RED_007_reviewer"),
        pytest.param("attestor_id", "other", id="RED_008_attestor"),
        pytest.param("approved_at_utc", "other", id="RED_009_approval_time"),
        pytest.param("path", "wrong/path.json", id="RED_010_path"),
        pytest.param("path_namespace", "other", id="RED_011_path_namespace"),
        pytest.param(
            "verification_status", "MISMATCHED", id="RED_012_verification_status"
        ),
    ),
)
def test_coordinated_snapshot_and_manifest_formal_binding_drift_fails_closed(
    field: str, value: object
) -> None:
    def mutate(snapshot, manifest) -> None:
        snapshot["formal_decision_binding"][field] = value
        manifest["formal_decision_binding"][field] = value

    artifacts = _coordinated_snapshot_manifest_artifacts(mutate)
    with pytest.raises(
        subject.G3HIngestionSafetyError, match="SNAPSHOT_FORMAL_BINDING_INVALID"
    ):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        pytest.param("artifact_role", "DRIFTED", id="RED_013_artifact_role"),
        pytest.param("source_path", "wrong/source.py", id="RED_014_source_path"),
        pytest.param("checker_path", "wrong/checker.py", id="RED_015_checker_path"),
        pytest.param("test_path", "wrong/test.py", id="RED_016_test_path"),
    ),
)
def test_manifest_identity_drift_fails_closed(field: str, value: object) -> None:
    artifacts = _coordinated_snapshot_manifest_artifacts(
        lambda snapshot, manifest: manifest.update({field: value})
    )
    with pytest.raises(
        subject.G3HIngestionSafetyError, match="MANIFEST_BOUNDARY_INVALID"
    ):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        pytest.param(
            "current11_tensorizer_direct_profile_supported",
            True,
            id="RED_017_tensorizer_supported",
        ),
        pytest.param(
            "direct_valid_canonical_task_ids",
            [0, 1, 3, 4],
            id="RED_018_direct_task_ids",
        ),
    ),
)
def test_manifest_runtime_drift_fails_closed(field: str, value: object) -> None:
    artifacts = _coordinated_snapshot_manifest_artifacts(
        lambda snapshot, manifest: manifest[
            "direct_profile_runtime_contract"
        ].update({field: value})
    )
    with pytest.raises(
        subject.G3HIngestionSafetyError, match="MANIFEST_RUNTIME_CONTRACT_INVALID"
    ):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


def test_unknown_snapshot_event_authority_field_fails_closed() -> None:
    artifacts = _coordinated_snapshot_manifest_artifacts(
        lambda snapshot, manifest: snapshot["events"][0].update(
            injected_reusable_authority_available=True
        )
    )
    with pytest.raises(
        subject.G3HIngestionSafetyError,
        match="SNAPSHOT_EVENT_EXACT_SCHEMA_OR_SEMANTICS_INVALID",
    ):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


@pytest.mark.parametrize(
    "mutation",
    (
        pytest.param(
            lambda contract: contract["global_canonical_tasks"][0].update(
                generated_roles=["scaffold"]
            ),
            id="RED_019_A_generated_roles",
        ),
        pytest.param(
            lambda contract: contract["global_canonical_tasks"][0].update(
                fixed_or_seed_roles=["warhead"]
            ),
            id="RED_020_A_fixed_roles",
        ),
        pytest.param(
            lambda contract: contract["global_canonical_tasks"][0].update(
                training_authority_created=True
            ),
            id="RED_021_global_task_unknown_field",
        ),
        pytest.param(
            lambda contract: contract["direct_profile_task_applicability"][0].update(
                training_authority_created=True
            ),
            id="RED_022_applicability_unknown_field",
        ),
        pytest.param(
            lambda contract: contract["global_canonical_tasks"][3].update(
                generated_roles=["warhead"]
            ),
            id="B3_generated_roles_drift",
        ),
        pytest.param(
            lambda contract: contract["global_canonical_tasks"][4].update(
                fixed_or_seed_roles=["scaffold"]
            ),
            id="C_minimal_seed_drift",
        ),
        pytest.param(
            lambda contract: contract.update(training_authority_created=True),
            id="canonical_contract_unknown_top_level_field",
        ),
    ),
)
def test_snapshot_canonical_task_exact_contract_drift_fails_closed(mutation) -> None:
    artifacts = _coordinated_snapshot_manifest_artifacts(
        lambda snapshot, manifest: mutation(snapshot["canonical_task_contract"])
    )
    with pytest.raises(
        subject.G3HIngestionSafetyError,
        match="SNAPSHOT_CANONICAL_TASK_CONTRACT_INVALID",
    ):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


def test_RED_023_manifest_generated_roles_drift_fails_closed() -> None:
    artifacts = _coordinated_snapshot_manifest_artifacts(
        lambda snapshot, manifest: manifest["canonical_task_contract"][
            "global_canonical_tasks"
        ][0].update(generated_roles=["scaffold"])
    )
    with pytest.raises(
        subject.G3HIngestionSafetyError,
        match="MANIFEST_CANONICAL_TASK_CONTRACT_INVALID",
    ):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


def test_RED_024_coordinated_snapshot_manifest_task_drift_fails_closed() -> None:
    def mutate(snapshot, manifest) -> None:
        for document in (snapshot, manifest):
            task = document["canonical_task_contract"]["global_canonical_tasks"][0]
            task["generated_roles"] = ["scaffold"]
            task["fixed_or_seed_roles"] = ["warhead"]

    artifacts = _coordinated_snapshot_manifest_artifacts(mutate)
    with pytest.raises(
        subject.G3HIngestionSafetyError,
        match="SNAPSHOT_CANONICAL_TASK_CONTRACT_INVALID",
    ):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


def test_H_W_context_cannot_become_disposition_exception() -> None:
    formal = _formal()
    formal["event_level_human_decisions"][-1][
        "event_specific_disposition_exception"
    ] = True
    with pytest.raises(subject.G3HIngestionSafetyError):
        subject.validate_formal_decision_v1(formal)


def test_matrix_B_B2_B3_and_exact5_semantics() -> None:
    artifacts = subject.build_artifacts_v1(REPO)
    rows = list(
        csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8")))
    )
    for row in rows:
        applicability = json.loads(row["canonical_task_applicability_json"])
        assert len(applicability) == 5
        assert [item["task_id"] for item in applicability] == [0, 1, 2, 3, 4]
        assert applicability[1]["structurally_applicable"] is False
        assert applicability[2]["structurally_applicable"] is False
        assert applicability[3]["semantic_long_name"] == "scaffold_only"
        assert [
            item["task_id"] for item in applicability if item["structurally_applicable"]
        ] == [0, 3, 4]


def test_geometry_and_auxiliary_targets_are_unavailable_exact8() -> None:
    artifacts = subject.build_artifacts_v1(REPO)
    rows = list(
        csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8")))
    )
    false_fields = (
        "independent_POST_geometry_human_decision_available",
        "POST_geometry_training_label_available_now",
        "reaction_family_training_class_target_available",
        "warhead_rule_training_class_target_available",
        "warhead_type_target_available",
        "reusable_authority_label_available",
        "training_mask_targets_available_now",
        "training_admitted",
        "training_materialization_allowed_now",
        "current_runtime_model_usable",
    )
    assert all(row["precursor_reactive_atom_context"] == "PRE_REACTION_UNRESOLVED" for row in rows)
    assert all(
        row["POST_geometry_source_evidence_status"]
        == "OBSERVED_POST_COVALENT_REVIEW_EVIDENCE"
        for row in rows
    )
    assert all(row[field] == "false" for row in rows for field in false_fields)


def test_H_W_context_note_is_one_row_without_new_lane() -> None:
    artifacts = subject.build_artifacts_v1(REPO)
    rows = list(
        csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8")))
    )
    noted = [row for row in rows if row["event_specific_context_note"]]
    assert len(noted) == 1
    assert noted[0]["canonical_event_id"] == subject.H_W_EVENT_ID
    assert noted[0]["event_specific_context_note"] == "NAD_NOT_MODELED_CONTEXT_ONLY"
    assert noted[0]["completed_lane"] == subject.EXPECTED_COMPLETED_LANE
    assert noted[0]["event_specific_disposition_exception"] == "false"


def test_manifest_output_sha_tamper_fails_closed() -> None:
    artifacts = _mutated_artifacts(
        subject.MANIFEST,
        lambda manifest: manifest["output_artifact_bindings"][subject.SNAPSHOT].update(
            sha256="0" * 64
        ),
    )
    with pytest.raises(
        subject.G3HIngestionSafetyError, match="MANIFEST_OUTPUT_BINDINGS_INVALID"
    ):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


def test_manifest_candidate_source_sha_tamper_fails_closed() -> None:
    artifacts = _mutated_artifacts(
        subject.MANIFEST,
        lambda manifest: manifest["candidate_source_bindings"][0].update(
            sha256="0" * 64
        ),
    )
    with pytest.raises(
        subject.G3HIngestionSafetyError,
        match="MANIFEST_CANDIDATE_SOURCE_BINDINGS_INVALID",
    ):
        subject.validate_artifacts_v1(artifacts, repo_root=REPO)


def test_unknown_output_file_fails_closed(tmp_path: Path) -> None:
    output_root = tmp_path / "outputs"
    output_root.mkdir()
    (output_root / "unknown.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        subject.G3HIngestionSafetyError,
        match="OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES",
    ):
        subject.materialize_artifacts_v1(REPO, output_root=output_root)


def test_dynamic_and_git_lifecycle_metadata_are_rejected() -> None:
    for field in ("generated_at", "hostname", "pid", "git_head", "origin_main"):
        artifacts = _mutated_artifacts(
            subject.MANIFEST,
            lambda manifest, field=field: manifest.update({field: "forbidden"}),
        )
        with pytest.raises(
            subject.G3HIngestionSafetyError,
            match="DYNAMIC_OR_LIFECYCLE_METADATA_FORBIDDEN",
        ):
            subject.validate_artifacts_v1(artifacts, repo_root=REPO)


def test_checker_is_repository_state_neutral_and_candidate_exact7() -> None:
    source = (REPO / subject.CHECKER_RELATIVE).read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "rev-parse" not in source
    assert "origin/main" not in source
    result = checker.verify_candidate_exact7_v1(REPO)
    assert result["repository_state_neutral"] is True
    assert result["candidate_publication_file_count"] == 7


def test_owner_has_no_torch_loader_or_model_dependency() -> None:
    source = (REPO / subject.SOURCE_RELATIVE).read_text(encoding="utf-8")
    for forbidden in (
        "import torch",
        "equivariant_diffusion",
        "lightning_modules",
        "optimizer.step",
        "backward(",
    ):
        assert forbidden not in source
