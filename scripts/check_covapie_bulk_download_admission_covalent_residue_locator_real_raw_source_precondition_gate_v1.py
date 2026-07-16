#!/usr/bin/env python3
"""Direct-evidence checker for Step14AU-E0-P6-B."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate
    as gate,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(gate.CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        return list(reader)


def _serialized(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> list[dict[str, str]]:
    return [{column: gate._csv_value(row[column]) for column in columns} for row in rows]


def _validated_source_snapshot() -> gate.FrozenSourceSnapshot:
    snapshot = gate._build_frozen_source_snapshot(REPO_ROOT)
    assert gate.validate_frozen_source_snapshot(snapshot, REPO_ROOT)
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert {str(record.relative_path): record.sha256 for record in snapshot.records} == gate.SOURCE_SHA256
    return snapshot


def _source_hashes(snapshot: gate.FrozenSourceSnapshot) -> dict[str, str]:
    return {str(record.relative_path): record.sha256 for record in snapshot.records}


def _output_hashes(root: Path) -> dict[str, str]:
    return {name: _sha256(root / name) for name in gate.OUTPUT_FILES}


def _raw_hashes(matrix: Sequence[Mapping[str, str]]) -> dict[str, str]:
    return {row["raw_target_relative_path"]: row["observed_sha256"] for row in matrix}


def validate_outputs(root: Path, expected_hashes: Mapping[str, str] | None = None) -> dict[str, Any]:
    assert root.is_dir() and not root.is_symlink()
    assert {path.name for path in root.iterdir()} == set(gate.OUTPUT_FILES)
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in gate.OUTPUT_FILES)
    hashes = _output_hashes(root)
    if expected_hashes is not None:
        assert hashes == dict(expected_hashes)

    fresh = gate.build_precondition_state(repo_root=REPO_ROOT)
    contract = _csv_rows(root / gate.CONTRACT_FILENAME)
    matrix = _csv_rows(root / gate.MATRIX_FILENAME)
    authority = _csv_rows(root / gate.AUTHORITY_AUDIT_FILENAME)
    safety = _csv_rows(root / gate.SAFETY_FILENAME)
    issues = _csv_rows(root / gate.ISSUE_FILENAME)
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))

    assert contract == _serialized(fresh["contract_rows"], gate.CONTRACT_COLUMNS)
    assert matrix == _serialized(fresh["matrix_rows"], gate.MATRIX_COLUMNS)
    assert authority == _serialized(fresh["authority_audit_rows"], gate.AUTHORITY_AUDIT_COLUMNS)
    assert safety == _serialized(fresh["safety_rows"], gate.SAFETY_COLUMNS)
    assert issues == _serialized(fresh["issue_rows"], gate.ISSUE_COLUMNS)
    assert gate.validate_authority_mapping(fresh["mapping"])
    assert gate.validate_authority_audit_rows(fresh["authority_audit_rows"], fresh["mapping"])
    assert gate.validate_matrix_rows(
        fresh["matrix_rows"], fresh["mapping"],
        fresh["raw_observations"], fresh["git_states"],
    )
    assert gate.validate_contract_rows(fresh["contract_rows"], fresh["observations"])
    assert gate.validate_safety_rows(fresh["safety_rows"], fresh["execution"])
    assert gate.validate_issue_rows(fresh["issue_rows"])
    assert fresh["source_snapshot_validated"] is True
    assert fresh["source_content_read_count"] == 9
    assert gate.validate_frozen_source_snapshot(
        fresh["source_snapshot"], REPO_ROOT
    )
    assert fresh["all_checks_passed"] is True
    assert fresh["sections"] == {
        "source_boundary": True, "p6b0_predecessor": True,
        "p6a_binding": True, "authority_mapping": True,
        "raw_access": True, "precondition_contract": True,
        "issue_inventory": True, "safety": True,
    }
    assert fresh["raw_open_count"] == 11
    assert fresh["raw_stat_count"] == 11
    assert fresh["raw_read_count"] == 11
    assert fresh["raw_hash_count"] == 11
    assert len(matrix) == 11 and tuple(matrix[0]) == gate.MATRIX_COLUMNS
    assert len(authority) == 2 and tuple(authority[0]) == gate.AUTHORITY_AUDIT_COLUMNS
    assert len(contract) == 50 and tuple(contract[0]) == gate.CONTRACT_COLUMNS
    assert issues == _serialized(gate._issue_rows(), gate.ISSUE_COLUMNS)
    assert safety == _serialized(fresh["safety_rows"], gate.SAFETY_COLUMNS)
    expected_manifest = gate._manifest_payload(fresh, {name: hashes[name] for name in gate.CSV_OUTPUTS})
    assert manifest == expected_manifest
    assert manifest["all_checks_passed"] is True
    assert manifest["real_raw_source_precondition_gate_passed"] is True
    assert manifest["validation_failures"] == []
    assert manifest["source_input_count"] == 9
    assert manifest["canonical_mask_task_count"] == 5
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["real_raw_sources_parsed_current_step"] is False
    assert manifest["p5b_parser_called_current_step"] is False
    assert manifest["p4_provider_called_current_step"] is False
    assert manifest["existing_real_sample_count"] == 11
    assert manifest["real_insertion_unknown_sample_count"] == 11
    assert manifest["real_insertion_absence_proven_sample_count"] == 0
    assert manifest["admit_004_rule_logic_ready"] is False
    assert manifest["ready_for_e1_residue_identity_semantics_design"] is False
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["untracked_historical_authority_runtime_count"] == 3
    assert manifest["ignored_expansion_runtime_count"] == 8
    assert manifest["exact_raw_tracked_count"] == 0
    return manifest


def main() -> None:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    source_before = _validated_source_snapshot()
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(
        repo_root=REPO_ROOT,
        source_snapshot=source_before
    )
    first_hashes = _output_hashes(root)
    first_manifest = validate_outputs(root, first_hashes)
    first_matrix = _csv_rows(root / gate.MATRIX_FILENAME)
    first_raw_hashes = _raw_hashes(first_matrix)
    source_second = _validated_source_snapshot()
    assert _source_hashes(source_second) == _source_hashes(source_before)
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(
        repo_root=REPO_ROOT,
        source_snapshot=source_second
    )
    second_manifest = validate_outputs(root, first_hashes)
    second_matrix = _csv_rows(root / gate.MATRIX_FILENAME)
    assert first_manifest == second_manifest
    assert _output_hashes(root) == first_hashes
    assert _raw_hashes(second_matrix) == first_raw_hashes
    assert _source_hashes(_validated_source_snapshot()) == _source_hashes(source_before)
    assert not tuple(root.glob("*.tmp"))

    manifest = second_manifest
    assert manifest["stage"] == gate.STAGE
    print(f"stage={manifest['stage']}")
    assert manifest["all_checks_passed"] is True
    print("all_checks_passed=true")
    for key, expected in (
        ("historical_authority_row_count", 3),
        ("expansion_authority_row_count", 8),
        ("authority_binding_match_count", 11),
        ("raw_source_precondition_row_count", 11),
        ("raw_source_precondition_passed_count", 11),
        ("raw_source_precondition_blocked_count", 0),
        ("raw_sha256_precondition_frozen_count", 11),
        ("raw_sha256_match_count", 11),
        ("raw_file_size_match_count", 11),
        ("untracked_historical_authority_runtime_count", 3),
        ("ignored_expansion_runtime_count", 8),
        ("exact_raw_tracked_count", 0),
        ("raw_stat_stable_count", 11),
    ):
        assert manifest[key] == expected
        print(f"{key}={expected}")
    for key, expected in (
        ("real_raw_sources_stat_current_step", True),
        ("real_raw_sources_read_current_step", True),
        ("real_raw_sources_hashed_current_step", True),
        ("real_raw_sources_parsed_current_step", False),
        ("p5b_parser_called_current_step", False),
        ("p4_provider_called_current_step", False),
        ("ready_for_real_provider_export_execution_smoke", True),
        ("ready_for_real_provider_export_execution", False),
        ("admit_004_rule_logic_ready", False),
        ("ready_for_e1_residue_identity_semantics_design", False),
        ("ready_for_real_candidate_evaluation", False),
        ("ready_for_bulk_download_now", False),
        ("ready_for_training", False),
        ("ready_to_train_now", False),
    ):
        assert manifest[key] is expected
        print(f"{key}={str(expected).lower()}")
    for key, expected in (
        ("existing_real_sample_count", 11),
        ("real_insertion_unknown_sample_count", 11),
        ("real_insertion_absence_proven_sample_count", 0),
    ):
        assert manifest[key] == expected
        print(f"{key}={expected}")
    assert _output_hashes(root) == first_hashes
    print("real_raw_source_precondition_outputs_byte_identical=true")
    print("covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1_passed")


if __name__ == "__main__":
    main()
