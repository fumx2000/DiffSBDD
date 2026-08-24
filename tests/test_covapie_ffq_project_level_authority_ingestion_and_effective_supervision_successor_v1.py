from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Mapping

import pytest

from covalent_ext import (
    covapie_ffq_project_level_authority_ingestion_and_effective_supervision_successor_v1
    as owner,
)
from covalent_ext import (
    covapie_k36_w1_reaction_family_and_warhead_rule_authority_creator_v1
    as k36_authority_creator,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / (
    "scripts/check_covapie_ffq_project_level_authority_ingestion_and_"
    "effective_supervision_successor_v1.py"
)
SOURCE_PATH = ROOT / (
    "src/covalent_ext/covapie_ffq_project_level_authority_ingestion_and_"
    "effective_supervision_successor_v1.py"
)

spec = importlib.util.spec_from_file_location("ffq_effective_checker", CHECKER_PATH)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

EXACT3 = tuple(sorted(path.as_posix() for path in checker.CANDIDATE_PATHS))


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _real_inputs() -> dict[str, Any]:
    values = checker._read_inputs(ROOT)
    return {
        key: value
        for key, value in values.items()
        if key not in ("family_receipt", "rule_receipt")
    }


def _build(**overrides: Any) -> dict[str, Any]:
    inputs = _real_inputs()
    inputs.update(overrides)
    return owner.build_covapie_ffq_project_level_authority_effective_supervision_v1(
        **inputs
    )


@pytest.fixture(scope="module")
def real_inputs() -> dict[str, Any]:
    return _real_inputs()


@pytest.fixture(scope="module")
def real_result() -> dict[str, Any]:
    return _build()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")


def _authority_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")


def _reverse_mapping_order(value: Any) -> Any:
    if type(value) is dict:
        return {
            key: _reverse_mapping_order(child)
            for key, child in reversed(tuple(value.items()))
        }
    if type(value) is list:
        return [_reverse_mapping_order(child) for child in value]
    return value


def _matrix_rows(payload: bytes) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    assert reader.fieldnames is not None
    return list(reader.fieldnames), [dict(row) for row in reader]


def _matrix_bytes(header: list[str], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def test_real_published_inputs_build_exact8_and_are_sha_bound(
    real_inputs: dict[str, Any], real_result: dict[str, Any]
) -> None:
    assert len(real_inputs["completed_decision_snapshot_payload"]) == 18032
    assert _sha256(real_inputs["completed_decision_snapshot_payload"]) == (
        owner.COMPLETED_DECISION_SNAPSHOT_SHA256
    )
    assert len(real_inputs["event_task_label_availability_payload"]) == 21239
    assert _sha256(real_inputs["event_task_label_availability_payload"]) == (
        owner.EVENT_TASK_LABEL_AVAILABILITY_SHA256
    )
    assert len(real_inputs["reaction_family_authority_payload"]) == 7778
    assert _sha256(real_inputs["reaction_family_authority_payload"]) == (
        owner.REACTION_FAMILY_AUTHORITY_FILE_SHA256
    )
    assert len(real_inputs["warhead_rule_authority_payload"]) == 8131
    assert _sha256(real_inputs["warhead_rule_authority_payload"]) == (
        owner.WARHEAD_RULE_AUTHORITY_FILE_SHA256
    )
    owner.validate_covapie_ffq_project_level_authority_effective_supervision_v1(
        real_result
    )
    records = real_result["effective_supervision_records"]
    assert len(records) == 8
    assert [record["canonical_event_id"] for record in records] == list(
        owner._CANONICAL_EVENT_IDS
    )
    assert all(
        record["reaction_family_authority_id"]
        == owner.REACTION_FAMILY_AUTHORITY_ID
        and record["warhead_rule_authority_id"]
        == owner.WARHEAD_RULE_AUTHORITY_ID
        and record["project_level_chemistry_authority_linkage_complete"]
        is True
        and record["effective_supervision_record_sha256"]
        == owner.effective_supervision_record_sha256_v1(record)
        for record in records
    )


def test_disk_authorities_equal_fresh_creators_and_key_order_is_irrelevant(
    real_inputs: dict[str, Any], real_result: dict[str, Any]
) -> None:
    family = owner.strict_parse_authority_json_v1(
        real_inputs["reaction_family_authority_payload"]
    )
    rule = owner.strict_parse_authority_json_v1(
        real_inputs["warhead_rule_authority_payload"]
    )
    reordered = _build(
        reaction_family_authority_payload=_authority_bytes(
            _reverse_mapping_order(family)
        ),
        warhead_rule_authority_payload=_authority_bytes(_reverse_mapping_order(rule)),
    )
    assert reordered == real_result
    summary = reordered["ingestion_effective_authority_summary"]
    assert summary["disk_family_authority_equals_fresh_creator_output"] is True
    assert summary["disk_warhead_rule_authority_equals_fresh_creator_output"] is True
    assert summary["disk_authority_key_order_treated_as_semantically_irrelevant"] is True


def test_effective_record_semantics_preserve_human_training_boundary(
    real_result: dict[str, Any]
) -> None:
    records = real_result["effective_supervision_records"]
    included = [record for record in records if record["pdb_id"] == "3VCY"]
    excluded = [record for record in records if record["pdb_id"] == "4R7U"]
    assert len(included) == len(excluded) == 4
    assert all(
        record["completed_lane"]
        == "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"
        and record["formal_event_training_use_decision"] == "INCLUDE"
        and record["training_use_allowed"] is True
        and record["non_geometry_training_candidate"] is True
        and record["candidate_for_future_training_admission"] is True
        and record["model_supervision_usable"] is None
        and record["training_admitted"] is False
        and record["training_materialization_allowed_now"] is False
        for record in included
    )
    assert all(
        record["completed_lane"]
        == "COMPLETED_HUMAN_CHEMISTRY_POSITIVE_TRAINING_EXCLUDED"
        and record["formal_event_training_use_decision"]
        == "EXCLUDE_FROM_TRAINING_ONLY"
        and record["training_use_allowed"] is False
        and record["human_training_exclusion_preserved"] is True
        and record["non_geometry_training_candidate"] is False
        and record["training_admitted"] is False
        and record["model_supervision_usable"] is False
        for record in excluded
    )


def test_geometry_warhead_type_mask_and_runtime_boundaries_are_conservative(
    real_result: dict[str, Any]
) -> None:
    for record in real_result["effective_supervision_records"]:
        assert record["POST_geometry_training_label_available_now"] is False
        assert record["POST_geometry_supervision_authority_status"] == "NOT_ESTABLISHED"
        assert record["PRE_geometry_supervision_authority_status"] == "NOT_ESTABLISHED"
        assert record["warhead_type_target_available"] is False
        assert record["reaction_family_authority_target_available"] is True
        assert record["warhead_rule_authority_target_available"] is True
        assert record["valid_task_ids"] == [0, 3, 4]
        assert record["not_applicable_task_ids"] == [1, 2]
        assert record["training_mask_targets_available_now"] is False
        assert record["current11_tensorizer_direct_profile_supported"] is False
        assert record["current_runtime_model_usable"] is False


def test_summary_freezes_exact_counts_and_training_prerequisite_boundaries(
    real_result: dict[str, Any]
) -> None:
    summary = real_result["ingestion_effective_authority_summary"]
    assert summary["effective_supervision_record_count"] == 8
    assert summary["chemistry_positive_event_count"] == 8
    assert summary["project_level_family_authority_linked_event_count"] == 8
    assert summary["project_level_warhead_rule_authority_linked_event_count"] == 8
    assert summary["3VCY_human_training_include_count"] == 4
    assert summary["4R7U_human_training_excluded_count"] == 4
    assert summary["future_non_geometry_training_candidate_count"] == 4
    assert summary["training_admitted_count"] == 0
    assert summary["POST_geometry_training_label_available_count"] == 0
    assert summary["ffq_effective_authority_linkage_complete"] is True
    assert summary["training_supervision_authority_complete"] is False
    assert summary["ready_for_training"] is False
    assert summary["feature_semantics_audit_required_before_formal_training"] is True
    assert summary["feature_semantics_audit_performed"] is False
    assert summary["historical_UNKNOWN_ATOM_FEATURE_POLICY_resolved"] is False
    assert summary["CURRENT11_TENSORIZER_DIRECT_PROFILE_SUPPORTED_V1"] is False
    assert summary["Step12D"] == (
        "SMOKE_LEGALITY_CHECK_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT"
    )
    for field in (
        "state_modified",
        "effective_supervision_materialized",
        "global_authority_registry_modified",
        "family_rule_registration_performed",
        "effective_authority_persisted",
        "runtime_authority_updated",
        "tensorizer_integration_performed",
        "training_admission_created",
        "training_dataset_changed",
        "training_performed",
        "network_performed",
        "model_forward",
        "backward",
        "optimizer_step",
        "Trainer.fit",
        "RL",
    ):
        assert summary[field] is False


@pytest.mark.parametrize(
    ("mutation", "field", "value"),
    (
        ("chemistry_positive_false", "chemistry_known_positive", "false"),
        ("negative_chemistry_true", "negative_chemistry", "true"),
        ("post_atom_drift", "post_ligand_reactive_atom", "FFQ:C2"),
        ("precursor_atom_drift", "precursor_reactive_atom_context", "FCN:C1"),
        ("role_profile_drift", "role_profile", "STRICT_LINKER_PRESENT_V1"),
        ("family_candidate_drift", "reaction_family_candidate_id", "WRONG"),
        ("rule_candidate_drift", "warhead_rule_candidate_id", "WRONG"),
        ("3VCY_include_drift", "formal_event_training_use_decision", "EXCLUDE_FROM_TRAINING_ONLY"),
        ("warhead_type_upgrade", "warhead_type_target_available", "true"),
        ("mask_target_upgrade", "training_mask_targets_available_now", "true"),
        ("runtime_upgrade", "current_runtime_model_usable", "true"),
    ),
)
def test_matrix_semantic_drift_fails_closed(
    mutation: str,
    field: str,
    value: str,
    real_inputs: dict[str, Any],
) -> None:
    header, rows = _matrix_rows(real_inputs["event_task_label_availability_payload"])
    rows[0][field] = value
    with pytest.raises(owner.FFQEffectiveSupervisionValidationError):
        _build(event_task_label_availability_payload=_matrix_bytes(header, rows))


@pytest.mark.parametrize("inventory_mutation", ("missing", "extra", "duplicate"))
def test_matrix_event_inventory_mutations_fail_closed(
    inventory_mutation: str, real_inputs: dict[str, Any]
) -> None:
    header, rows = _matrix_rows(real_inputs["event_task_label_availability_payload"])
    if inventory_mutation == "missing":
        rows.pop()
    elif inventory_mutation == "extra":
        extra = dict(rows[-1])
        extra["canonical_event_id"] += ":EXTRA"
        rows.append(extra)
    else:
        rows[-1] = dict(rows[0])
    with pytest.raises(owner.FFQEffectiveSupervisionValidationError):
        _build(event_task_label_availability_payload=_matrix_bytes(header, rows))


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("scaffold_atom_ids_json", "[\"O2\",\"O3\",\"O4\"]"),
        ("warhead_atom_ids_json", "[\"C1\",\"C2\",\"C3\",\"O2\"]"),
        ("linker_atom_ids_json", "[\"P1\"]"),
        ("direct_profile_applicable_task_ids_json", "[0,1,3,4]"),
    ),
)
def test_role_partition_and_task_applicability_drift_fails_closed(
    field: str, value: str, real_inputs: dict[str, Any]
) -> None:
    header, rows = _matrix_rows(real_inputs["event_task_label_availability_payload"])
    rows[0][field] = value
    with pytest.raises(owner.FFQEffectiveSupervisionValidationError):
        _build(event_task_label_availability_payload=_matrix_bytes(header, rows))


def test_B_and_B2_cannot_be_marked_applicable(real_inputs: dict[str, Any]) -> None:
    header, rows = _matrix_rows(real_inputs["event_task_label_availability_payload"])
    applicability = json.loads(rows[0]["canonical_task_applicability_json"])
    applicability[1]["profile_applicable"] = True
    rows[0]["canonical_task_applicability_json"] = json.dumps(
        applicability, sort_keys=True, separators=(",", ":")
    )
    with pytest.raises(owner.FFQEffectiveSupervisionValidationError):
        _build(event_task_label_availability_payload=_matrix_bytes(header, rows))


@pytest.mark.parametrize(
    ("pdb_id", "field", "value"),
    (
        ("3VCY", "formal_event_training_use_decision", "EXCLUDE_FROM_TRAINING_ONLY"),
        ("4R7U", "formal_event_training_use_decision", "INCLUDE"),
        ("4R7U", "training_use_allowed", True),
        ("4R7U", "candidate_for_future_training_admission", True),
        ("4R7U", "training_admitted", True),
        ("3VCY", "POST_geometry_training_label_available_now", True),
        ("3VCY", "current_runtime_model_usable", True),
    ),
)
def test_snapshot_training_and_geometry_drift_fails_closed(
    pdb_id: str, field: str, value: object, real_inputs: dict[str, Any]
) -> None:
    snapshot = json.loads(real_inputs["completed_decision_snapshot_payload"])
    event = next(item for item in snapshot["events"] if item["pdb_id"] == pdb_id)
    event[field] = value
    with pytest.raises(owner.FFQEffectiveSupervisionValidationError):
        _build(completed_decision_snapshot_payload=_canonical_bytes(snapshot) + b"\n")


AuthorityMutation = Callable[[dict[str, Any], dict[str, Any]], None]


def _family_id_drift(family: dict[str, Any], rule: dict[str, Any]) -> None:
    family["authority_id"] = "COVAPIE_CYS_SG_REACTION_FAMILY_0000000000000000"


def _family_sha_drift(family: dict[str, Any], rule: dict[str, Any]) -> None:
    family["canonical_semantic_signature_sha256"] = "0" * 64


def _rule_id_drift(family: dict[str, Any], rule: dict[str, Any]) -> None:
    rule["authority_id"] = "COVAPIE_CYS_SG_WARHEAD_RULE_0000000000000000"


def _rule_sha_drift(family: dict[str, Any], rule: dict[str, Any]) -> None:
    rule["canonical_semantic_signature_sha256"] = "0" * 64


def _family_rule_link_drift(family: dict[str, Any], rule: dict[str, Any]) -> None:
    rule["canonical_semantic_signature"]["reaction_family_authority_id"] = (
        "COVAPIE_CYS_SG_REACTION_FAMILY_0000000000000000"
    )


def _family_candidate_lineage_drift(family: dict[str, Any], rule: dict[str, Any]) -> None:
    family["source_candidate_to_authority_provenance"][
        "source_candidate_reaction_family_id"
    ] = "WRONG"


def _rule_candidate_lineage_drift(family: dict[str, Any], rule: dict[str, Any]) -> None:
    rule["source_candidate_to_authority_provenance"][
        "source_candidate_warhead_rule_id"
    ] = "WRONG"


@pytest.mark.parametrize(
    "mutation",
    (
        _family_id_drift,
        _family_sha_drift,
        _rule_id_drift,
        _rule_sha_drift,
        _family_rule_link_drift,
        _family_candidate_lineage_drift,
        _rule_candidate_lineage_drift,
    ),
)
def test_authority_identity_lineage_and_linkage_mutations_fail_closed(
    mutation: AuthorityMutation, real_inputs: dict[str, Any]
) -> None:
    family = owner.strict_parse_authority_json_v1(
        real_inputs["reaction_family_authority_payload"]
    )
    rule = owner.strict_parse_authority_json_v1(
        real_inputs["warhead_rule_authority_payload"]
    )
    mutation(family, rule)
    with pytest.raises(owner.FFQEffectiveSupervisionValidationError):
        _build(
            reaction_family_authority_payload=_authority_bytes(family),
            warhead_rule_authority_payload=_authority_bytes(rule),
        )


def test_authority_file_hash_drift_is_rejected_by_checker_binding(tmp_path: Path) -> None:
    source = ROOT.parent / checker.FAMILY_AUTHORITY_PATH
    drifted = tmp_path / "reaction_family_authority_v2.json"
    drifted.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="SHA256_MISMATCH|BYTE_COUNT_MISMATCH"):
        checker._read_bound_regular(
            drifted,
            byte_count=owner.REACTION_FAMILY_AUTHORITY_FILE_BYTE_COUNT,
            sha256=owner.REACTION_FAMILY_AUTHORITY_FILE_SHA256,
            label="MATERIALIZED_FFQ_FAMILY_AUTHORITY",
        )


def test_current_baseline_and_k36_authorities_are_actually_consumed_without_collision(
    real_inputs: dict[str, Any], real_result: dict[str, Any]
) -> None:
    summary = real_result["ingestion_effective_authority_summary"]
    assert summary["existing_approved_authority_collision_status"] == (
        "NO_APPROVED_AUTHORITY_COLLISION"
    )
    assert summary["K36_published_authorities_coexist_without_collision"] is True
    assert summary["K36_authority_overwritten"] is False
    k36_ids = []
    for source in owner.K36_PUBLISHED_AUTHORITY_SOURCES_V1:
        payload = real_inputs["k36_published_authority_payloads"][source["source_path"]]
        parsed = owner.strict_parse_authority_json_v1(payload)
        k36_ids.append(parsed["authority_id"])
    assert owner.REACTION_FAMILY_AUTHORITY_ID not in k36_ids
    assert owner.WARHEAD_RULE_AUTHORITY_ID not in k36_ids


def test_k36_authority_or_current_baseline_drift_fails_closed(
    real_inputs: dict[str, Any]
) -> None:
    k36 = dict(real_inputs["k36_published_authority_payloads"])
    first = next(iter(k36))
    k36[first] += b"\n"
    with pytest.raises(owner.FFQEffectiveSupervisionValidationError):
        _build(k36_published_authority_payloads=k36)
    baseline = dict(real_inputs["approved_authority_baseline_source_payloads"])
    first = next(iter(baseline))
    baseline[first] += b"\n"
    with pytest.raises(owner.FFQEffectiveSupervisionValidationError):
        _build(approved_authority_baseline_source_payloads=baseline)


@pytest.mark.parametrize(
    ("pdb_id", "field", "value"),
    (
        ("3VCY", "formal_event_training_use_decision", "EXCLUDE_FROM_TRAINING_ONLY"),
        ("4R7U", "formal_event_training_use_decision", "INCLUDE"),
        ("4R7U", "non_geometry_training_candidate", True),
        ("4R7U", "candidate_for_future_training_admission", True),
        ("4R7U", "training_admitted", True),
        ("4R7U", "training_materialization_allowed_now", True),
        ("4R7U", "model_supervision_usable", True),
        ("3VCY", "POST_geometry_training_label_available_now", True),
        ("3VCY", "POST_geometry_supervision_authority_status", "ESTABLISHED"),
        ("3VCY", "PRE_geometry_supervision_authority_status", "ESTABLISHED"),
        ("3VCY", "warhead_type_target_available", True),
        ("3VCY", "valid_task_ids", [0, 1, 3, 4]),
        ("3VCY", "not_applicable_task_ids", [2]),
        ("3VCY", "training_mask_targets_available_now", True),
        ("3VCY", "current_runtime_model_usable", True),
        ("3VCY", "reaction_family_authority_id", "WRONG"),
        ("3VCY", "warhead_rule_semantic_signature_sha256", "0" * 64),
    ),
)
def test_effective_record_mutations_fail_closed_even_when_rehashed(
    pdb_id: str, field: str, value: object, real_result: dict[str, Any]
) -> None:
    result = copy.deepcopy(real_result)
    record = next(item for item in result["effective_supervision_records"] if item["pdb_id"] == pdb_id)
    record[field] = value
    record["effective_supervision_record_sha256"] = (
        owner.effective_supervision_record_sha256_v1(record)
    )
    with pytest.raises(
        owner.FFQEffectiveSupervisionValidationError,
        match="EFFECTIVE_SUPERVISION_RECORD_INVALID",
    ):
        owner.validate_covapie_ffq_project_level_authority_effective_supervision_v1(
            result
        )


@pytest.mark.parametrize("inventory_mutation", ("missing", "extra", "duplicate"))
def test_effective_record_inventory_mutations_fail_closed(
    inventory_mutation: str, real_result: dict[str, Any]
) -> None:
    result = copy.deepcopy(real_result)
    records = result["effective_supervision_records"]
    if inventory_mutation == "missing":
        records.pop()
    elif inventory_mutation == "extra":
        records.append(copy.deepcopy(records[-1]))
    else:
        records[-1] = copy.deepcopy(records[0])
    with pytest.raises(owner.FFQEffectiveSupervisionValidationError):
        owner.validate_covapie_ffq_project_level_authority_effective_supervision_v1(
            result
        )


def test_repeated_builds_are_deep_and_canonical_byte_deterministic_without_input_mutation(
    real_inputs: dict[str, Any], real_result: dict[str, Any]
) -> None:
    inputs = copy.deepcopy(real_inputs)
    snapshot = copy.deepcopy(inputs)
    repeated = owner.build_covapie_ffq_project_level_authority_effective_supervision_v1(
        **inputs
    )
    assert repeated == real_result
    assert _canonical_bytes(repeated) == _canonical_bytes(real_result)
    assert inputs == snapshot


@pytest.mark.parametrize(
    "payload",
    (
        b'{"a":1,"a":2}',
        b'{"a":NaN}',
        b"\xef\xbb\xbf{}",
        b'{"a":"\x00"}',
        b"[]",
        b"not-json",
    ),
)
def test_strict_authority_parser_rejects_ambiguous_or_invalid_json(payload: bytes) -> None:
    with pytest.raises(owner.FFQEffectiveSupervisionValidationError):
        owner.strict_parse_authority_json_v1(payload)


def test_production_source_is_stateless_and_exposes_no_write_or_training_api() -> None:
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not imported_roots.intersection(
        {"pathlib", "os", "subprocess", "socket", "requests", "torch"}
    )
    forbidden_api = {
        "materialize_artifacts_v1",
        "write_authority",
        "register_authority",
        "update_registry",
        "update_effective_authority",
        "tensorize",
        "train",
    }
    assert not forbidden_api.intersection(vars(owner))
    source_text = SOURCE_PATH.read_text(encoding="utf-8")
    for token in ("Trainer.fit(", ".backward(", "optimizer.step(", "requests.get("):
        assert token not in source_text


def test_import_smoke_has_no_stdout_stderr_or_filesystem_side_effect(tmp_path: Path) -> None:
    before = tuple(tmp_path.iterdir())
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import covalent_ext."
                "covapie_ffq_project_level_authority_ingestion_and_"
                "effective_supervision_successor_v1"
            ),
        ],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout == completed.stderr == ""
    assert tuple(tmp_path.iterdir()) == before


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
        "untracked_paths": EXACT3,
        "tracked_candidate_paths": (),
    }


def _published_observation() -> dict[str, object]:
    observation = _precommit_observation()
    observation.update(
        {
            "head": "1" * 40,
            "origin_main": "1" * 40,
            "untracked_paths": (),
            "tracked_candidate_paths": EXACT3,
        }
    )
    return observation


def test_dual_lifecycle_profiles_and_mixed_states_fail_closed() -> None:
    assert checker.validate_repository_observation_v1(_precommit_observation()) == (
        checker.PRECOMMIT_PROFILE
    )
    assert checker.validate_repository_observation_v1(_published_observation()) == (
        checker.PUBLISHED_PROFILE
    )
    mutations = []
    for field, value in (
        ("branch", "feature"),
        ("ahead", 1),
        ("modified_tracked_paths", ("tracked.py",)),
        ("staged_paths", (EXACT3[0],)),
        ("tracked_candidate_paths", EXACT3[:1]),
        ("untracked_paths", tuple(sorted((*EXACT3, "unexpected.txt")))),
    ):
        observation = _precommit_observation()
        observation[field] = value
        mutations.append(observation)
    for observation in mutations:
        with pytest.raises(ValueError, match=checker.LIFECYCLE_ERROR):
            checker.validate_repository_observation_v1(observation)


def test_real_checker_reads_all_sources_builds_exact8_and_reports_boundaries() -> None:
    observation = checker.observe_repository_state_v1(ROOT)
    expected_profile = checker.validate_repository_observation_v1(observation)
    result = checker.run_check_v1(ROOT)
    assert result["lifecycle_profile"] == expected_profile
    if observation["head"] == checker.BASELINE_COMMIT:
        assert expected_profile == checker.PRECOMMIT_PROFILE
    else:
        assert expected_profile == checker.PUBLISHED_PROFILE
    assert result["effective_supervision_record_count"] == 8
    assert result["reaction_family_authority_id"] == owner.REACTION_FAMILY_AUTHORITY_ID
    assert result["warhead_rule_authority_id"] == owner.WARHEAD_RULE_AUTHORITY_ID
    assert result["family_linked_event_count"] == 8
    assert result["rule_linked_event_count"] == 8
    assert result["3VCY_training_candidate_count"] == 4
    assert result["4R7U_training_excluded_count"] == 4
    assert result["training_admitted_count"] == 0
    assert result["POST_geometry_training_label_available_count"] == 0
    assert result["warhead_type_target_available"] is False
    assert result["training_mask_targets_available_now"] is False
    assert result["ffq_effective_authority_linkage_complete"] is True
    assert result["watched_source_trees_byte_identical_after_build"] is True
    assert result["state_modified"] is False
    assert result["training_performed"] is False
    assert result["network_performed"] is False
