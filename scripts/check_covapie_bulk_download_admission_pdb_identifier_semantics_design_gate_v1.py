#!/usr/bin/env python3
"""Verify deterministic Step14AU-B1 PDB identifier semantics outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext.covapie_bulk_download_admission_pdb_identifier_semantics_design_gate import (  # noqa: E402
    CANONICAL_SAFETY_ITEMS,
    CANONICAL_MASK_PAIRS,
    CONTRACT_COLUMNS,
    CONTRACT_SPECS,
    CSV_OUTPUTS,
    DEFAULT_OUTPUT_ROOT,
    MANIFEST_SCHEMA_VERSION,
    MANIFEST_FILENAME,
    PREVIOUS_STAGE,
    SOURCE_SHA256,
    SOURCE_COLUMNS,
    SAFETY_COLUMNS,
    STAGE,
    _source_paths,
    run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _validate_manifest_and_outputs(
    manifest: dict[str, object], root: Path, first_hashes: dict[str, str],
) -> None:
    """Validate the manifest against the materialized CSV evidence."""
    assert manifest["stage"] == STAGE
    assert manifest["step_label"] == "Step14AU-B1"
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["previous_stage"] == PREVIOUS_STAGE
    assert manifest["manifest_schema_version"] == MANIFEST_SCHEMA_VERSION
    assert manifest["source_read_boundary"] == "only_step14au_a_6_outputs_and_step14at_schema_rule_metadata_only"
    assert manifest["source_input_count"] == 8
    assert manifest["source_input_sha256"] == SOURCE_SHA256
    assert manifest["semantics_contract_item_count"] == 20
    assert (manifest["normalization_example_count"], manifest["positive_example_count"], manifest["negative_example_count"]) == (29, 7, 22)
    assert all(manifest[key] is True for key in (
        "all_source_boundary_checks_passed", "all_semantics_contract_checks_passed",
        "all_normalization_example_checks_passed", "all_safety_checks_passed", "all_checks_passed",
        "pdb_identifier_semantics_contract_frozen", "ready_for_pdb_identifier_semantics_integration",
    ))
    assert all(manifest[key] is False for key in (
        "ready_for_admission_evaluator_rule_logic_implementation", "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
        "network_access_used_current_step", "filesystem_scan_used_current_step", "raw_structure_read_current_step",
        "artifact_reference_paths_followed_current_step", "pdb_archive_existence_lookup_performed",
        "candidate_records_materialized_current_step", "download_queue_materialized_current_step",
        "download_manifest_materialized_current_step", "raw_files_written_current_step",
    ))
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == "integrate_covapie_pdb_identifier_semantics_into_admission_preconditions_v1"
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in CANONICAL_MASK_PAIRS]
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["issue_count"] == 0 and manifest["blocking_reasons"] == []
    assert manifest["output_file_count"] == 6 and manifest["non_manifest_output_count"] == 5
    assert manifest["output_files"] == [*CSV_OUTPUTS, MANIFEST_FILENAME]
    current_hashes = {name: _sha256(root / name) for name in (*CSV_OUTPUTS, MANIFEST_FILENAME)}
    assert current_hashes == first_hashes
    assert manifest["output_sha256"] == {name: current_hashes[name] for name in CSV_OUTPUTS}
    contracts = _read_csv(root / CSV_OUTPUTS[0])
    assert len(contracts) == 20
    assert all(tuple(row.keys()) == CONTRACT_COLUMNS for row in contracts)
    assert [row["contract_item"] for row in contracts] == [spec[0] for spec in CONTRACT_SPECS]
    assert len({row["contract_item"] for row in contracts}) == 20
    assert all(row["contract_status"] == "frozen" for row in contracts)
    assert all(row["blocking_reason"] == "" for row in contracts)
    assert all(row["contract_passed"] == "true" for row in contracts)
    assert all(row["external_lookup_required"] == "false" for row in contracts)
    sources = _read_csv(root / CSV_OUTPUTS[2])
    expected_paths = [path.as_posix() for path in _source_paths()]
    assert len(sources) == 8
    assert all(tuple(row.keys()) == SOURCE_COLUMNS for row in sources)
    assert [row["source_relative_path"] for row in sources] == expected_paths
    assert len({row["source_relative_path"] for row in sources}) == 8
    for row in sources:
        expected_hash = SOURCE_SHA256[row["source_relative_path"]]
        assert row["tracked_by_git"] == "true"
        assert row["regular_file"] == "true"
        assert row["symlink"] == "false"
        assert row["sha256_expected"] == expected_hash
        assert row["sha256_observed"] == expected_hash
        assert row["source_boundary_passed"] == "true"
    safety = _read_csv(root / CSV_OUTPUTS[3])
    assert len(safety) == len(CANONICAL_SAFETY_ITEMS)
    assert all(tuple(row.keys()) == SAFETY_COLUMNS for row in safety)
    assert [row["safety_item"] for row in safety] == list(CANONICAL_SAFETY_ITEMS)
    assert len({row["safety_item"] for row in safety}) == len(CANONICAL_SAFETY_ITEMS)
    assert all(row["required_status"] == "false" for row in safety)
    assert all(row["observed_status"] == "false" for row in safety)
    assert all(row["safety_passed"] == "true" for row in safety)
    assert all(row["blocking_reason"] == "" for row in safety)
    examples = _read_csv(root / CSV_OUTPUTS[1])
    assert len(examples) == 29
    assert all(row["example_passed"] == "true" for row in examples)
    assert sum(row["expected_syntax_valid"] == "true" for row in examples) == 7
    assert sum(row["expected_syntax_valid"] == "false" for row in examples) == 22
    by_id = {row["example_id"]: row for row in examples}
    assert by_id["EXAMPLE_011"] == {
        "example_id": "EXAMPLE_011", "input_representation": r"\t1abc", "input_type": "str",
        "expected_input_form": "invalid", "expected_syntax_valid": "false",
        "expected_canonical_pdb_id": "", "expected_normalization_applied": "false",
        "expected_blocking_reason": "pdb_id_surrounding_whitespace_forbidden", "example_passed": "true",
    }
    assert by_id["EXAMPLE_012"] == {
        "example_id": "EXAMPLE_012", "input_representation": r"1abc\n", "input_type": "str",
        "expected_input_form": "invalid", "expected_syntax_valid": "false",
        "expected_canonical_pdb_id": "", "expected_normalization_applied": "false",
        "expected_blocking_reason": "pdb_id_surrounding_whitespace_forbidden", "example_passed": "true",
    }
    issues = _read_csv(root / CSV_OUTPUTS[4])
    assert issues == [{
        "issue_id": "NO_ISSUES", "issue_type": "no_pdb_identifier_semantics_design_issues",
        "severity": "none", "status": "no_issues", "issue_count": "0", "blocking_reason": "",
    }]
    serialized = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in serialized.lower() and "/home/" not in serialized


def main() -> int:
    root = REPO_ROOT / DEFAULT_OUTPUT_ROOT
    first = run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1(root)
    first_hashes = {name: _sha256(root / name) for name in (*CSV_OUTPUTS, MANIFEST_FILENAME)}
    second = run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1(root)
    second_hashes = {name: _sha256(root / name) for name in (*CSV_OUTPUTS, MANIFEST_FILENAME)}
    assert first_hashes == second_hashes
    manifest = json.loads((root / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest == second
    _validate_manifest_and_outputs(manifest, root, first_hashes)
    print(f"stage={STAGE}")
    print("all_checks_passed=true")
    print("ready_for_pdb_identifier_semantics_integration=true")
    print("ready_for_admission_evaluator_rule_logic_implementation=false")
    print("ready_for_real_candidate_evaluation=false")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    print("pdb_identifier_semantics_outputs_byte_identical=true")
    print("covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
