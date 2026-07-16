#!/usr/bin/env python3
"""Deterministic, direct-evidence check for Step14AU-E0-P6-B0."""
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
    covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate
    as gate,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        return list(reader)


def _serialized_rows(
    rows: Sequence[Mapping[str, Any]], columns: tuple[str, ...]
) -> list[dict[str, str]]:
    return [
        {column: gate._csv_value(row[column]) for column in columns}
        for row in rows
    ]


def _output_hashes(root: Path) -> dict[str, str]:
    return {name: _sha256(root / name) for name in gate.OUTPUT_FILES}


def _validated_source_hash_snapshot() -> dict[str, str]:
    """Return hashes only from the production-validated source audit."""
    rows = gate._source_rows()
    assert gate.validate_source_rows(rows)
    assert len(rows) == len(gate.SOURCE_PATHS)
    assert tuple(row["source_relative_path"] for row in rows) == tuple(
        str(path) for path in gate.SOURCE_PATHS
    )
    snapshot = {
        row["source_relative_path"]: row["sha256_observed"]
        for row in rows
    }
    assert tuple(snapshot) == tuple(str(path) for path in gate.SOURCE_PATHS)
    assert snapshot == gate.SOURCE_SHA256
    return snapshot


def validate_materialized_outputs(
    root: Path, expected_hashes: Mapping[str, str] | None = None
) -> dict[str, Any]:
    assert root.is_dir() and not root.is_symlink()
    assert {path.name for path in root.iterdir()} == set(gate.OUTPUT_FILES)
    assert all(
        (root / name).is_file() and not (root / name).is_symlink()
        for name in gate.OUTPUT_FILES
    )
    current_hashes = _output_hashes(root)
    if expected_hashes is not None:
        assert current_hashes == dict(expected_hashes)

    state = gate.build_authority_state()
    assert state["all_checks_passed"] is True
    assert state["sections"] == {
        "source_boundary": True,
        "p6a_predecessor": True,
        "source_role_contract": True,
        "authority_rows": True,
        "authority_contract": True,
        "issue_inventory": True,
        "safety": True,
    }
    contract = _csv_rows(root / gate.CONTRACT_FILENAME)
    authority = _csv_rows(root / gate.AUTHORITY_FILENAME)
    sources = _csv_rows(root / gate.SOURCE_FILENAME)
    safety = _csv_rows(root / gate.SAFETY_FILENAME)
    issues = _csv_rows(root / gate.ISSUE_FILENAME)
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))

    assert contract == _serialized_rows(state["contract_rows"], gate.CONTRACT_COLUMNS)
    assert authority == _serialized_rows(state["authority_rows"], gate.AUTHORITY_COLUMNS)
    assert sources == _serialized_rows(state["source_rows"], gate.SOURCE_COLUMNS)
    assert safety == _serialized_rows(state["safety_rows"], gate.SAFETY_COLUMNS)
    assert issues == _serialized_rows(state["issue_rows"], gate.ISSUE_COLUMNS)
    assert len(contract) == 48 and all(row["contract_passed"] == "true" for row in contract)
    assert len(authority) == 3 and tuple(authority[0]) == gate.AUTHORITY_COLUMNS
    assert len(sources) == 10 and tuple(sources[0]) == gate.SOURCE_COLUMNS
    assert len(safety) == 20 and tuple(safety[0]) == gate.SAFETY_COLUMNS
    assert len(issues) == 3 and tuple(issues[0]) == gate.ISSUE_COLUMNS

    expected_manifest = gate._manifest_payload(
        state, {name: current_hashes[name] for name in gate.CSV_OUTPUTS}
    )
    assert manifest == expected_manifest
    assert [(row["pdb_id"], row["ligand_comp_id"]) for row in authority] == list(gate.HISTORICAL_IDENTITIES)
    expected_locators = [
        ("AVAILABILITY_ROW_000002", "INTEGRITY_ROW_000002"),
        ("AVAILABILITY_ROW_000004", "INTEGRITY_ROW_000004"),
        ("AVAILABILITY_ROW_000005", "INTEGRITY_ROW_000005"),
    ]
    assert [(row["availability_source_row_id"], row["integrity_source_row_id"]) for row in authority] == expected_locators
    assert all(
        row["expected_sha256"]
        == row["prior_observed_sha256"]
        == row["independence_sha256_before"]
        == row["independence_sha256_after"]
        for row in authority
    )
    assert all(
        row["expected_file_size_bytes"] == row["prior_observed_file_size_bytes"]
        and row["sha256_matches"] == "true"
        and row["file_size_matches"] == "true"
        and row["identity_match"] == "true"
        and row["raw_path_match"] == "true"
        and row["all_source_statuses_passed"] == "true"
        and row["authority_status"] == "passed"
        for row in authority
    )
    integrity = gate._historical_documents()["integrity"]
    for row in authority:
        ordinal = int(row["integrity_source_row_id"].removeprefix("INTEGRITY_ROW_"))
        source_row = integrity.rows[ordinal - 1]
        assert (source_row["pdb_id"], source_row["raw_path"]) == (
            row["pdb_id"], row["raw_target_relative_path"]
        )
    assert all(row["source_check_passed"] == "true" for row in sources)
    documents = gate._historical_documents()
    for pdb_id, _ligand in gate.HISTORICAL_IDENTITIES:
        availability_rows = [row for row in documents["availability"].rows if row["pdb_id"] == pdb_id]
        integrity_rows = [row for row in documents["integrity"].rows if row["pdb_id"] == pdb_id]
        independence_rows = [row for row in documents["independence"].rows if row["pdb_id"] == pdb_id]
        assert len(availability_rows) == len(integrity_rows) == len(independence_rows) == 1
        assert gate._availability_status(availability_rows[0])
        assert gate._integrity_status(integrity_rows[0], pdb_id)
        assert gate._independence_status(independence_rows[0])
    assert safety == _serialized_rows(gate._safety_rows(), gate.SAFETY_COLUMNS)
    assert issues == _serialized_rows(gate._issue_rows(), gate.ISSUE_COLUMNS)
    assert manifest["current_raw_used_to_define_expected_hash"] is False
    assert all(
        manifest[key] is False
        for key in (
            "real_raw_sources_stat_current_step",
            "real_raw_sources_read_current_step",
            "real_raw_sources_hashed_current_step",
            "real_raw_sources_parsed_current_step",
            "p5b_parser_called_current_step",
            "p4_provider_called_current_step",
            "ready_for_real_provider_export_execution_smoke",
            "admit_004_rule_logic_ready",
            "ready_for_e1_residue_identity_semantics_design",
            "ready_for_real_candidate_evaluation",
            "ready_for_bulk_download_now",
            "ready_for_training",
            "ready_to_train_now",
        )
    )
    assert manifest["existing_real_sample_count"] == 11
    assert manifest["real_insertion_unknown_sample_count"] == 11
    assert manifest["real_insertion_absence_proven_sample_count"] == 0
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]
    assert manifest["feature_semantics_audit_required_before_training"] is True
    return manifest


def main() -> None:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    source_hashes_before = _validated_source_hash_snapshot()
    first = gate.run_covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate_v1()
    first_hashes = _output_hashes(root)
    first_manifest = validate_materialized_outputs(root, first_hashes)
    second = gate.run_covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate_v1()
    second_manifest = validate_materialized_outputs(root, first_hashes)
    assert first["manifest"] == first_manifest == second["manifest"] == second_manifest
    assert _output_hashes(root) == first_hashes
    assert _validated_source_hash_snapshot() == source_hashes_before
    assert not tuple(root.glob("*.tmp"))

    manifest = second_manifest
    assert manifest["stage"] == gate.STAGE
    print(f"stage={manifest['stage']}")
    assert manifest["all_checks_passed"] is True
    print("all_checks_passed=true")
    assert manifest["historical_authority_row_count"] == 3
    print("historical_authority_row_count=3")
    assert manifest["authority_passed_count"] == 3
    print("authority_passed_count=3")
    assert manifest["authority_blocked_count"] == 0
    print("authority_blocked_count=0")
    assert manifest["authority_hash_match_count"] == 3
    print("authority_hash_match_count=3")
    assert manifest["authority_size_match_count"] == 3
    print("authority_size_match_count=3")
    assert manifest["authority_identity_match_count"] == 3
    print("authority_identity_match_count=3")
    assert manifest["authority_raw_path_match_count"] == 3
    print("authority_raw_path_match_count=3")
    assert manifest["historical_single_authority_file_materialized"] is True
    print("historical_single_authority_file_materialized=true")
    assert manifest["current_raw_used_to_define_expected_hash"] is False
    print("current_raw_used_to_define_expected_hash=false")
    assert manifest["real_raw_sources_stat_current_step"] is False
    print("real_raw_sources_stat_current_step=false")
    assert manifest["real_raw_sources_read_current_step"] is False
    print("real_raw_sources_read_current_step=false")
    assert manifest["real_raw_sources_hashed_current_step"] is False
    print("real_raw_sources_hashed_current_step=false")
    assert manifest["p5b_parser_called_current_step"] is False
    print("p5b_parser_called_current_step=false")
    assert manifest["p4_provider_called_current_step"] is False
    print("p4_provider_called_current_step=false")
    assert manifest["ready_for_real_raw_source_precondition_gate"] is True
    print("ready_for_real_raw_source_precondition_gate=true")
    assert manifest["ready_for_real_provider_export_execution_smoke"] is False
    print("ready_for_real_provider_export_execution_smoke=false")
    assert manifest["existing_real_sample_count"] == 11
    print("existing_real_sample_count=11")
    assert manifest["real_insertion_unknown_sample_count"] == 11
    print("real_insertion_unknown_sample_count=11")
    assert manifest["real_insertion_absence_proven_sample_count"] == 0
    print("real_insertion_absence_proven_sample_count=0")
    assert manifest["admit_004_rule_logic_ready"] is False
    print("admit_004_rule_logic_ready=false")
    assert manifest["ready_for_e1_residue_identity_semantics_design"] is False
    print("ready_for_e1_residue_identity_semantics_design=false")
    assert manifest["ready_for_real_candidate_evaluation"] is False
    print("ready_for_real_candidate_evaluation=false")
    assert manifest["ready_for_bulk_download_now"] is False
    print("ready_for_bulk_download_now=false")
    assert manifest["ready_for_training"] is False
    print("ready_for_training=false")
    assert manifest["ready_to_train_now"] is False
    print("ready_to_train_now=false")
    assert _output_hashes(root) == first_hashes
    print("historical_raw_fingerprint_authority_outputs_byte_identical=true")
    assert manifest["all_checks_passed"] is True
    print("covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate_v1_passed")


if __name__ == "__main__":
    main()
