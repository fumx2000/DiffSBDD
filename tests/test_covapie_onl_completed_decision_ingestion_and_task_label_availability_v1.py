from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (
    covapie_onl_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


FORMAL = ROOT.parent / subject.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT


def _checker_module():
    path = ROOT / subject.CHECKER_RELATIVE
    spec = importlib.util.spec_from_file_location("check_covapie_onl_ingestion_v1", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _formal() -> dict[str, object]:
    value = json.loads(FORMAL.read_bytes())
    assert type(value) is dict
    return value


def _set(value: dict[str, object], path: tuple[object, ...], replacement: object) -> None:
    target: object = value
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = replacement  # type: ignore[index]


def _append_extra_event(value: dict[str, object]) -> None:
    events = value["event_level_human_decisions"]
    canonical = value["canonical_event_ids"]
    assert type(events) is list and type(canonical) is list
    extra = copy.deepcopy(events[-1])
    extra["canonical_event_id"] = "COVAPIE_CYS_SG_EVENT_V1:EXTRA"
    events.append(extra)
    canonical.append(extra["canonical_event_id"])


def _duplicate_event(value: dict[str, object]) -> None:
    events = value["event_level_human_decisions"]
    assert type(events) is list
    events[1]["canonical_event_id"] = events[0]["canonical_event_id"]


def _missing_event(value: dict[str, object]) -> None:
    canonical = value["canonical_event_ids"]
    assert type(canonical) is list
    canonical.pop()


SEMANTIC_MUTATIONS = (
    ("schema", lambda value: _set(value, ("schema_version",), "mutated")),
    ("review_unit", lambda value: _set(value, ("review_unit_id",), "mutated")),
    ("ligand", lambda value: _set(value, ("ligand_component_id",), "DON")),
    ("reviewer", lambda value: _set(value, ("reviewer_id",), "other")),
    ("attestor", lambda value: _set(value, ("attestor_id",), "other")),
    ("approval_false", lambda value: _set(value, ("approved",), False)),
    ("unsigned_true", lambda value: _set(value, ("unsigned",), True)),
    ("approval_timestamp", lambda value: _set(value, ("human_approval", "approved_at_utc"), "2026-08-26T01:26:02Z")),
    ("exact9_count", lambda value: _set(value, ("exact_event_count",), 8)),
    ("missing_event", _missing_event),
    ("duplicate_event", _duplicate_event),
    ("extra_event", _append_extra_event),
    ("D1", lambda value: _set(value, ("event_level_human_decisions", 0, "D1_human_task_relevance_decision"), "NOT_RELEVANT")),
    ("D2", lambda value: _set(value, ("event_level_human_decisions", 0, "D2_human_chemistry_support_disposition"), "NEGATIVE")),
    ("negative_chemistry", lambda value: _set(value, ("event_level_human_decisions", 0, "negative_chemistry"), True)),
    ("task_domain_negative", lambda value: _set(value, ("event_level_human_decisions", 0, "task_domain_negative"), True)),
    ("D3", lambda value: _set(value, ("event_level_human_decisions", 0, "D3_human_reactive_pair_decision"), "REJECT")),
    ("protein_SG", lambda value: _set(value, ("event_level_human_decisions", 0, "protein_reactive_atom"), "CB")),
    ("ligand_CE", lambda value: _set(value, ("event_level_human_decisions", 0, "ligand_reactive_atom"), "CD")),
    ("D4", lambda value: _set(value, ("event_level_human_decisions", 0, "D4_human_role_partition_choice"), "SELECT_CANDIDATE_0")),
    ("candidate_index", lambda value: _set(value, ("selected_role_partition", "candidate_index_0based"), 0)),
    ("role_profile", lambda value: _set(value, ("selected_role_partition", "role_profile"), "STRICT_SCAFFOLD_LINKER_WARHEAD_V1")),
    ("warhead_atoms", lambda value: _set(value, ("selected_role_partition", "warhead_atoms"), ["CE"])),
    ("nonempty_linker", lambda value: _set(value, ("selected_role_partition", "linker_atoms"), ["CG"])),
    ("scaffold_atoms", lambda value: _set(value, ("selected_role_partition", "scaffold_atoms"), ["C"])),
    ("boundary_atom", lambda value: _set(value, ("selected_role_partition", "boundary_bonds", 0, "atom_id_1"), "CE")),
    ("boundary_bond_order", lambda value: _set(value, ("selected_role_partition", "boundary_bonds", 0, "bond_order"), "DOUB")),
    ("D5", lambda value: _set(value, ("event_level_human_decisions", 0, "D5_human_training_use_disposition"), "INCLUDE")),
    ("human_training_excluded", lambda value: _set(value, ("event_level_human_decisions", 0, "human_training_excluded"), False)),
    ("training_admitted", lambda value: _set(value, ("event_level_human_decisions", 0, "training_admitted"), True)),
    ("event_exception", lambda value: _set(value, ("event_level_human_decisions", 0, "event_specific_disposition_exception"), True)),
    ("PRE_authority", lambda value: _set(value, ("geometry_boundary", "PRE_geometry_authority_created"), True)),
    ("POST_training_authority", lambda value: _set(value, ("geometry_boundary", "POST_geometry_training_authority_created"), True)),
    ("reaction_family_authority", lambda value: _set(value, ("reaction_family_authority", "authority_created"), True)),
    ("warhead_rule_authority", lambda value: _set(value, ("warhead_rule_authority", "authority_created"), True)),
    ("warhead_type_authority", lambda value: _set(value, ("warhead_type_authority", "authority_created"), True)),
    ("reusable_authority", lambda value: _set(value, ("reusable_authority_boundary", "reusable_chemistry_authority_created"), True)),
)


def test_frozen_formal_binding_and_exact9_ingestion() -> None:
    assert FORMAL.stat().st_size == 28678
    assert hashlib.sha256(FORMAL.read_bytes()).hexdigest() == subject.FORMAL_DECISION_SHA256
    bound = subject.load_frozen_formal_decision_v1(ROOT)
    binding = bound["formal_decision_binding"]
    assert binding == subject._formal_binding()
    assert len(bound["frozen_review_package_bindings"]) == 6
    events = bound["normalized"]["events"]
    assert len(events) == 9
    assert tuple(event["canonical_event_id"] for event in events) == subject.EXPECTED_EVENT_IDS
    assert [event["scaleup_rank"] for event in events] == [24, 25, 26, 27, 134, 434, 435, 436, 437]
    assert all(event["task_relevant"] and event["chemistry_known_positive"] for event in events)
    assert all(event["reactive_pair_human_authoritative"] for event in events)
    assert all(event["role_partition_human_authoritative"] for event in events)
    assert all(event["authority_source"] == subject.AUTHORITY_SOURCE for event in events)
    assert all(event["authority_created_by_this_successor"] is False for event in events)


def test_selected_role_exact5_geometry_and_training_boundaries() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    role = snapshot["selected_role_partition"]
    assert role["selected_candidate_index_0based"] == 1
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    assert role["warhead_atoms"] == ["CD", "CE", "OD"]
    assert role["linker_atoms"] == []
    assert role["scaffold_atoms"] == ["C", "CA", "CB", "CG", "N", "O", "OXT"]
    assert role["boundary_bonds"] == [{"atom_id_1": "CD", "atom_id_2": "CG", "bond_order": "SING", "boundary_between_roles": ["warhead", "scaffold"]}]
    tasks = snapshot["canonical_task_contract"]
    assert tasks["global_canonical_task_count"] == 5
    assert tasks["B3_present"] is True
    assert tasks["direct_profile_applicable_task_ids"] == [0, 3, 4]
    assert [task["structurally_applicable"] for task in tasks["direct_profile_task_applicability"]] == [True, False, False, True, True]
    assert tasks["direct_profile_task_applicability"][1]["reason"] == subject.EXPECTED_ROLE_PROFILE
    assert tasks["direct_profile_task_applicability"][2]["reason"] == subject.EXPECTED_ROLE_PROFILE
    geometry = snapshot["geometry_boundary"]
    assert geometry["POST_source_evidence_count"] == 9
    assert geometry["POST_geometry_training_authority_count"] == 0
    assert geometry["PRE_geometry_authority_count"] == 0
    assert geometry["observed_product_graph_is_authoritative_PRE_precursor"] is False
    assert geometry["PRE_precursor_reconstruction_performed"] is False
    training = snapshot["training_boundary"]
    assert training["training_excluded_positive_count"] == 9
    assert training["training_include_count"] == 0
    assert training["candidate_for_future_training_admission_count"] == 0
    assert training["training_admitted_count"] == 0
    assert training["training_materialization_allowed_count"] == 0
    assert training["current_runtime_model_usable_count"] == 0
    assert training["ready_for_training"] is False


def test_exact4_outputs_are_deterministic_and_well_formed(tmp_path: Path) -> None:
    first = subject.build_artifacts_v1(ROOT)
    second = subject.build_artifacts_v1(ROOT)
    assert first == second
    assert tuple(first) == subject.OUTPUT_FILENAMES
    for name, payload in first.items():
        subject._validate_text_payload(name, payload)
        assert payload == subject.build_artifacts_v1(ROOT)[name]
    materialized = subject.materialize_artifacts_v1(ROOT, output_root=tmp_path / "one")
    subject.materialize_artifacts_v1(ROOT, output_root=tmp_path / "two")
    for name in subject.OUTPUT_FILENAMES:
        assert (tmp_path / "one" / name).read_bytes() == (tmp_path / "two" / name).read_bytes()
        assert (tmp_path / "one" / name).read_bytes() == materialized[name]


def test_matrix_summary_manifest_direct_evidence() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    subject.validate_completed_decision_projection_v1(artifacts, repo_root=ROOT)
    rows = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))
    assert len(rows) == 9
    assert [int(row["scaleup_rank"]) for row in rows] == [24, 25, 26, 27, 134, 434, 435, 436, 437]
    assert sum(row["POST_source_evidence_available"] == "true" for row in rows) == 9
    assert sum(row["POST_geometry_training_label_available_now"] == "true" for row in rows) == 0
    assert sum(row["PRE_geometry_authority_available"] == "true" for row in rows) == 0
    assert all(row["formal_event_training_use_decision"] == "EXCLUDE_FROM_TRAINING_ONLY" for row in rows)
    assert all(row["training_use_allowed"] == "false" for row in rows)
    assert all(row["training_admitted"] == "false" for row in rows)
    for row in rows:
        applicability = json.loads(row["canonical_task_applicability_json"])
        assert len(applicability) == 5
        assert [item["task_id"] for item in applicability if item["structurally_applicable"]] == [0, 3, 4]
        assert applicability[3]["semantic_long_name"] == "scaffold_only"
        assert applicability[1]["reason"] == subject.EXPECTED_ROLE_PROFILE
        assert applicability[2]["reason"] == subject.EXPECTED_ROLE_PROFILE
    summary = json.loads(artifacts[subject.SUMMARY])
    assert summary == subject._summary()
    assert summary["published_global_positive_count_remains"] == 49
    assert summary["global_reconciliation_update_status"] == "NOT_DONE_THIS_STEP"
    assert summary["global_census_update_status"] == "NOT_DONE_THIS_STEP"
    manifest = json.loads(artifacts[subject.MANIFEST])
    assert "sha256" not in manifest
    assert manifest["manifest_self_sha256_recorded"] is False
    assert len(manifest["candidate_source_bindings"]) == 3
    assert len(manifest["frozen_review_package_bindings"]) == 6
    assert len(manifest["immutable_semantic_owner_bindings"]) == 2
    assert manifest["output_artifact_bindings"] == {
        subject.SNAPSHOT: {"sha256": hashlib.sha256(artifacts[subject.SNAPSHOT]).hexdigest()},
        subject.MATRIX: {"sha256": hashlib.sha256(artifacts[subject.MATRIX]).hexdigest()},
        subject.SUMMARY: {"sha256": hashlib.sha256(artifacts[subject.SUMMARY]).hexdigest()},
    }


def test_public_standalone_validator_accepts_exact_current_artifacts() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    subject.validate_completed_decision_projection_v1(artifacts)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("D1_human_task_relevance_decision", "NOT_RELEVANT"),
        ("ligand_reactive_atom", "CD"),
        ("D5_human_training_use_disposition", "INCLUDE"),
    ),
    ids=("RED_001_D1", "RED_002_ligand_atom", "RED_003_D5"),
)
def test_public_standalone_validator_rejects_coordinated_snapshot_drift(
    field: str, replacement: str
) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    snapshot["events"][0][field] = replacement
    mutated = dict(artifacts)
    mutated[subject.SNAPSHOT] = subject._json_bytes(snapshot)
    manifest = json.loads(mutated[subject.MANIFEST])
    manifest["output_artifact_bindings"][subject.SNAPSHOT]["sha256"] = (
        hashlib.sha256(mutated[subject.SNAPSHOT]).hexdigest()
    )
    mutated[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(
        subject.ONLIngestionSafetyError,
        match="SNAPSHOT_EXACT_PROJECTION_SHA256_INVALID",
    ):
        subject.validate_completed_decision_projection_v1(mutated)


def test_public_validator_repo_root_mode_accepts_exact_current_artifacts() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    subject.validate_completed_decision_projection_v1(artifacts, repo_root=ROOT)


def test_frozen_derived_projection_digests_match_current_artifacts() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    assert hashlib.sha256(artifacts[subject.SNAPSHOT]).hexdigest() == (
        subject._EXPECTED_SNAPSHOT_SHA256_V1
    )
    assert hashlib.sha256(artifacts[subject.MATRIX]).hexdigest() == (
        subject._EXPECTED_MATRIX_SHA256_V1
    )
    assert hashlib.sha256(artifacts[subject.SUMMARY]).hexdigest() == (
        subject._EXPECTED_SUMMARY_SHA256_V1
    )


def test_formal_payload_wrong_byte_count_fails_closed(tmp_path: Path) -> None:
    mutated = tmp_path / "formal.json"
    mutated.write_bytes(FORMAL.read_bytes() + b" ")
    with pytest.raises(subject.ONLIngestionSafetyError, match="BYTE_COUNT_MISMATCH"):
        subject.load_frozen_formal_decision_v1(ROOT, formal_decision_path=mutated)


def test_formal_payload_same_size_sha_mutation_fails_closed(tmp_path: Path) -> None:
    payload = FORMAL.read_bytes()
    mutated_payload = payload.replace(b'"approved": true', b'"approved": fals', 1)
    assert len(mutated_payload) == len(payload) and mutated_payload != payload
    mutated = tmp_path / "formal.json"
    mutated.write_bytes(mutated_payload)
    with pytest.raises(subject.ONLIngestionSafetyError, match="SHA256_MISMATCH"):
        subject.load_frozen_formal_decision_v1(ROOT, formal_decision_path=mutated)


@pytest.mark.parametrize(("case", "mutate"), SEMANTIC_MUTATIONS, ids=[case for case, _ in SEMANTIC_MUTATIONS])
def test_formal_semantic_drift_fails_closed(case: str, mutate) -> None:
    formal = copy.deepcopy(_formal())
    mutate(formal)
    with pytest.raises(subject.ONLIngestionSafetyError):
        subject._validate_formal_decision_v1(formal)


@pytest.mark.parametrize(
    ("path", "replacement"),
    (
        (("authority_boundary", "model_bound_pair_target_created_by_ingestion"), True),
        (("authority_boundary", "tensor_target_created"), True),
        (("authority_boundary", "model_forward_performed"), True),
        (("authority_boundary", "training_admission_created"), True),
        (("authority_boundary", "training_dataset_changed"), True),
        (("authority_boundary", "training_performed"), True),
        (("geometry_boundary", "PRE_geometry_authority_count"), 1),
        (("geometry_boundary", "POST_geometry_training_authority_count"), 1),
        (("training_boundary", "training_admitted_count"), 1),
    ),
)
def test_snapshot_non_action_mutation_fails_closed(path: tuple[object, ...], replacement: object) -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    _set(snapshot, path, replacement)
    mutated = dict(artifacts)
    mutated[subject.SNAPSHOT] = subject._json_bytes(snapshot)
    with pytest.raises(subject.ONLIngestionSafetyError):
        subject.validate_completed_decision_projection_v1(mutated, repo_root=ROOT)


def test_output_text_and_manifest_mutations_fail_closed() -> None:
    artifacts = subject.build_artifacts_v1(ROOT)
    trailing = dict(artifacts)
    trailing[subject.SUMMARY] = trailing[subject.SUMMARY][:-1] + b" \n"
    with pytest.raises(subject.ONLIngestionSafetyError, match="TRAILING_WHITESPACE"):
        subject.validate_completed_decision_projection_v1(trailing, repo_root=ROOT)
    manifest = json.loads(artifacts[subject.MANIFEST])
    manifest["generated_at_utc"] = "2026-08-26T01:26:01Z"
    dynamic = dict(artifacts)
    dynamic[subject.MANIFEST] = subject._json_bytes(manifest)
    with pytest.raises(subject.ONLIngestionSafetyError, match="DYNAMIC_OR_LIFECYCLE"):
        subject.validate_completed_decision_projection_v1(dynamic, repo_root=ROOT)


def test_materialized_exact7_checker() -> None:
    result = _checker_module().run_check_v1(ROOT)
    assert result["candidate_publication_file_count"] == 7
    assert result["output_artifact_count"] == 4
    assert result["exact9_unique_complete"] is True
    assert result["completed_human_positive_count"] == 9
    assert result["training_excluded_positive_count"] == 9
    assert result["training_include_count"] == 0
    assert result["future_training_admission_candidate_count"] == 0
    assert result["training_admitted_count"] == 0
    assert result["training_materialization_allowed_count"] == 0
    assert result["current_runtime_model_usable_count"] == 0
    assert result["global_reconciliation_update_done"] is False
    assert result["global_census_update_done"] is False
    assert result["ready_for_training"] is False
