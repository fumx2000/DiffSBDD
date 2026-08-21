#!/usr/bin/env python3
"""Fail-closed checker for batch-001 formal split/leakage admission V1."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from covalent_ext import covapie_batch001_formal_split_leakage_admission_v1 as subject


CHECK_ERROR = "COVAPIE_BATCH001_FORMAL_SPLIT_LEAKAGE_ADMISSION_V1_CHECK_ERROR"


def _fail(reason: str) -> None:
    raise ValueError(f"{CHECK_ERROR}:{reason}")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def check_v1() -> dict[str, object]:
    first = subject.compute_covapie_batch001_formal_split_admission_v1()
    second = subject.compute_covapie_batch001_formal_split_admission_v1()
    if first != second:
        _fail("FULL_COMPUTATION_DETERMINISM_FAILED")
    if not subject.validate_covapie_batch001_formal_split_admission_v1(first):
        _fail("FULL_COMPUTATION_VALIDATION_FAILED")

    artifacts_first = subject.build_covapie_batch001_formal_split_admission_artifacts_v1()
    artifacts_second = subject.build_covapie_batch001_formal_split_admission_artifacts_v1()
    if (
        artifacts_first != artifacts_second
        or tuple(artifacts_first) != subject.OUTPUT_FILENAMES_V1
        or len(artifacts_first) != 4
    ):
        _fail("ARTIFACT_DETERMINISM_OR_EXACT4_FAILED")
    output_root = REPOSITORY_ROOT / subject.OUTPUT_ROOT_RELATIVE_V1
    if (
        not output_root.is_dir()
        or {path.name for path in output_root.iterdir() if path.is_file()}
        != set(subject.OUTPUT_FILENAMES_V1)
    ):
        _fail("PERSISTED_EXACT4_OUTPUT_SET_INVALID")
    for name, payload in artifacts_first.items():
        if (output_root / name).read_bytes() != payload:
            _fail("PERSISTED_ARTIFACT_MISMATCH:" + name)

    source_rows = list(csv.DictReader(io.StringIO(
        artifacts_first[subject.SOURCE_BINDING_INVENTORY_V1].decode("utf-8")
    )))
    event_rows = list(csv.DictReader(io.StringIO(
        artifacts_first[subject.EVENT_ADMISSION_V1].decode("utf-8")
    )))
    registry = json.loads(artifacts_first[subject.COMPONENT_REGISTRY_V1])
    manifest = json.loads(artifacts_first[subject.MANIFEST_V1])
    if (
        len(source_rows) != len(first.source_bindings)
        or any(row["sha256_verified"] != "True" for row in source_rows)
        or any(row["actual_sha256"] != row["expected_sha256"] for row in source_rows)
    ):
        _fail("SOURCE_BINDING_INVENTORY_INVALID")
    if (
        registry.get("schema_version")
        != "covapie_batch001_formal_leakage_component_registry_v1"
        or registry.get("component_count") != 4
        or len(registry.get("components", ())) != 4
    ):
        _fail("COMPONENT_REGISTRY_INVALID")
    component_by_name = {
        item["component_name"]: item for item in registry["components"]
    }
    if set(component_by_name) != {"DJK", "LN5", "PX5", "PTG"}:
        _fail("COMPONENT_REGISTRY_NAME_SET_INVALID")
    expected_splits = {
        "DJK": ("train", "train", True),
        "LN5": ("train", "validation", False),
        "PX5": ("train", "validation", False),
        "PTG": ("validation", "train", False),
    }
    for name, (read_only, formal, split_parity) in expected_splits.items():
        item = component_by_name[name]
        if (
            item["read_only_split"] != read_only
            or item["formal_split"] != formal
            or item["group_parity"] is not True
            or item["split_parity"] is not split_parity
            or item["formal_assignment_is_authority_candidate"] is not True
            or item["non_target_members_are_training_samples"] is not False
            or item["non_target_members_inherit_split_reservation_only"] is not True
        ):
            _fail("COMPONENT_FORMAL_AUTHORITY_INVALID:" + name)
    if (
        len(event_rows) != 13
        or len({row["canonical_event_id"] for row in event_rows}) != 13
        or sum(row["split_admission_authoritative"] == "true" for row in event_rows) != 9
        or sum(row["assigned_split"] == "train" for row in event_rows) != 5
        or sum(row["assigned_split"] == "validation" for row in event_rows) != 4
        or sum(row["split_admission_status"] == "UNRESOLVED_FAIL_CLOSED" for row in event_rows) != 4
        or any(row["sample_training_admitted"] != "false" for row in event_rows)
        or any(row["model_training_activation_authorized"] != "false" for row in event_rows)
    ):
        _fail("EVENT_AUTHORITY_COUNTS_OR_ACTIVATION_INVALID")
    ndu = [row for row in event_rows if row["ligand_component_id"] == "NDU"]
    if (
        len(ndu) != 4
        or any(row["formal_leakage_group_id"] or row["assigned_split"] for row in ndu)
        or any(row["split_admission_authoritative"] != "false" for row in ndu)
        or any(row["split_admission_reason"] != "LEAKAGE_EVIDENCE_INCOMPLETE" for row in ndu)
    ):
        _fail("NDU_FAIL_CLOSED_BOUNDARY_INVALID")

    bindings = manifest.get("artifact_bindings", {})
    if set(bindings) != {
        subject.SOURCE_BINDING_INVENTORY_V1,
        subject.COMPONENT_REGISTRY_V1,
        subject.EVENT_ADMISSION_V1,
    }:
        _fail("MANIFEST_ARTIFACT_BINDING_SET_INVALID")
    for name, binding in bindings.items():
        if binding.get("sha256") != _sha256(artifacts_first[name]):
            _fail("MANIFEST_ARTIFACT_SHA256_INVALID:" + name)
    prediction = manifest.get("prediction_and_formal_assignment", {})
    oracle = manifest.get("independent_exhaustive_formal_assignment_oracle", {})
    counts = manifest.get("population_counts", {})
    frozen = manifest.get("frozen_group_invariants", {})
    cross = manifest.get("cross_component_leakage_audit", {})
    safety = manifest.get("safety", {})
    if (
        prediction.get("read_only_prediction_reproduced_exactly") is not True
        or prediction.get("read_only_prediction_is_authority") is not False
        or prediction.get("formal_joint_assignment_recomputed") is not True
        or prediction.get("formal_read_only_group_parity") is not True
        or prediction.get("formal_read_only_split_parity") is not False
        or prediction.get("read_only_split_superseded_event_count") != 7
        or oracle.get("candidate_assignment_count") != 81
        or oracle.get("valid_assignment_count") != 46
        or oracle.get("selected_full_signature")
        != [2, 0, 0, 1, 1, 0, 0, 1, 1, 0, 2]
        or oracle.get("selected_objective_fractions") != ["4", "2", "27/5"]
        or oracle.get("tie_count_before_signature") != 3
        or manifest.get("formal_owner_independent_oracle_parity") is not True
        or counts.get("formal_split_admission_event_count") != 9
        or counts.get("formal_train_event_count") != 5
        or counts.get("formal_validation_event_count") != 4
        or counts.get("formal_unresolved_event_count") != 4
        or frozen.get("existing_frozen_groups_modified") is not False
        or cross.get("cross_split_leakage_violation_count") != 0
        or safety.get("network_used") is not False
        or safety.get("tensorization_performed") is not False
        or safety.get("model_forward_performed") is not False
        or safety.get("loss_performed") is not False
        or safety.get("training_performed") is not False
        or manifest.get("ready_for_admission_aware_cpu_model_smoke") is not True
        or manifest.get("ready_for_training") is not False
    ):
        _fail("MANIFEST_AUTHORITY_OR_SAFETY_CONTRACT_INVALID")
    for payload in artifacts_first.values():
        text = payload.decode("utf-8")
        if (
            "timestamp" in text.lower()
            or "mtime" in text.lower()
            or str(REPOSITORY_ROOT) in text
        ):
            _fail("RUNTIME_OR_MACHINE_SPECIFIC_METADATA_PRESENT")
    return {
        "source_binding_count": len(source_rows),
        "full_predictor_population_count": first.context_counts[
            "full_predictor_population_count"
        ],
        "formal_component_count": len(first.components),
        "candidate_assignment_count": first.oracle.candidate_assignment_count,
        "valid_assignment_count": first.oracle.valid_assignment_count,
        "tie_count_before_signature": first.oracle.tie_count_before_signature,
        "input_order_case_count": first.input_order_case_count,
        "formal_split_admission_event_count": len([
            row for row in event_rows
            if row["split_admission_authoritative"] == "true"
        ]),
        "formal_train_event_count": sum(
            row["assigned_split"] == "train" for row in event_rows
        ),
        "formal_validation_event_count": sum(
            row["assigned_split"] == "validation" for row in event_rows
        ),
        "formal_unresolved_event_count": len(ndu),
        "read_only_split_superseded_event_count": 7,
        "formal_owner_independent_oracle_parity": True,
        "formal_read_only_group_parity": True,
        "formal_read_only_split_parity": False,
        "existing_frozen_groups_modified": False,
        "cross_split_leakage_violation_count": 0,
        "model_training_activation_authorized_event_count": 0,
        "network_used": False,
        "tensorization_performed": False,
        "model_forward_performed": False,
        "loss_performed": False,
        "training_performed": False,
        "ready_for_gpt_review": True,
        "ready_for_admission_aware_cpu_model_smoke": True,
    }


def main() -> int:
    result = check_v1()
    for name, value in result.items():
        print(f"{name}={str(value).lower() if isinstance(value, bool) else value}")
    print("batch001_formal_split_leakage_admission_successor_built=true")
    print("read_only_prediction_is_authority=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
