#!/usr/bin/env python3
"""Check deterministic Step14AU-D1 ligand component ID design outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate as gate  # noqa: E402


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _validate_exact_outputs(root: Path) -> None:
    expected = {*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME}
    assert {path.name for path in root.iterdir()} == expected
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in expected)


def _validate_helper_contract() -> None:
    assert gate.normalize_ligand_comp_id("jug").canonical_ligand_comp_id == "JUG"
    assert gate.normalize_ligand_comp_id(" JUG").blocking_reason == "LIGAND_COMP_ID_SYNTAX_INVALID"
    assert gate.normalize_ligand_comp_id(7).blocking_reason == "LIGAND_COMP_ID_TYPE_INVALID"
    assert gate.normalize_ligand_comp_id("JÜG").blocking_reason == "LIGAND_COMP_ID_NON_ASCII"
    assert gate.normalize_ligand_comp_id("A" * 32).passed is True
    assert gate.normalize_ligand_comp_id("A" * 33).blocking_reason == "LIGAND_COMP_ID_LENGTH_INVALID"
    assert all(not gate.normalize_ligand_comp_id(value).passed for value in (
        "A-B", "A_B", "A/B", "A,B", "A;B", "A|B", "A:B", "A+B",
    ))
    assert not gate.normalize_ligand_comp_id(".").passed
    assert not gate.normalize_ligand_comp_id("?").passed
    canonical = gate.normalize_ligand_comp_id("JuG").canonical_ligand_comp_id
    assert gate.normalize_ligand_comp_id(canonical).canonical_ligand_comp_id == canonical


def _validate_manifest_and_outputs(
    manifest: dict[str, object], root: Path, first_hashes: dict[str, str],
) -> None:
    _validate_exact_outputs(root)
    current_hashes = {
        name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    }
    assert current_hashes == first_hashes
    source_rows = gate._source_boundary_rows()
    source = gate._load_source()
    assert gate._validate_source_boundary_rows(source_rows)
    assert gate._validate_source_semantics(source)
    assert {row["source_relative_path"]: row["sha256_observed"] for row in source_rows} == gate.SOURCE_SHA256
    _validate_helper_contract()

    contract = _csv(root / gate.CSV_OUTPUTS[0])
    examples = _csv(root / gate.CSV_OUTPUTS[1])
    disk_source = _csv(root / gate.CSV_OUTPUTS[2])
    safety = _csv(root / gate.CSV_OUTPUTS[3])
    issues = _csv(root / gate.CSV_OUTPUTS[4])
    assert gate._validate_contract_rows(contract)
    assert gate._validate_example_rows(examples)
    assert gate._validate_source_boundary_rows(disk_source)
    assert gate._validate_safety_rows(safety)
    assert issues == [{
        "issue_id": "NO_ISSUES", "issue_type": "no_ligand_comp_id_semantics_design_issues",
        "severity": "none", "status": "no_issues", "issue_count": "0", "blocking_reason": "",
    }]
    assert len(contract) == 32
    assert len(examples) == 36
    assert sum(row["example_class"] == "valid" for row in examples) == 12
    assert sum(row["example_class"] == "invalid" for row in examples) == 24
    assert len(disk_source) == 6 and len(safety) == 19
    assert all(row["example_passed"] == "true" for row in examples)
    assert all(row["safety_passed"] == "true" for row in safety)

    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == "Step14AU-D1"
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["manifest_schema_version"] == gate.MANIFEST_SCHEMA_VERSION
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["source_read_boundary"] == "only_step14au_c2_six_committed_metadata_outputs"
    assert manifest["source_input_count"] == 6
    assert manifest["source_input_sha256"] == gate.SOURCE_SHA256
    assert manifest["output_files"] == [*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME]
    assert manifest["output_file_count"] == 6 and manifest["non_manifest_output_count"] == 5
    assert manifest["output_sha256"] == {name: current_hashes[name] for name in gate.CSV_OUTPUTS}
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]
    assert manifest["canonical_mask_task_count"] == 5
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]
    assert manifest["upstream_effective_issue_count"] == 11
    assert manifest["expected_post_integration_issue_count"] == 10
    assert manifest["resolved_design_issue_ids"] == [gate.TARGET_BLOCKER]
    assert manifest["contract_row_count"] == 32 and manifest["example_row_count"] == 36
    assert manifest["valid_example_count"] == 12 and manifest["invalid_example_count"] == 24
    assert manifest["source_audit_row_count"] == 6 and manifest["safety_audit_row_count"] == 19
    assert all(manifest[key] is True for key in (
        "artifact_reference_paths_not_recursively_opened",
        "ligand_comp_id_semantics_frozen", "ligand_comp_id_exact_type_contract_ready",
        "ligand_comp_id_syntax_contract_ready", "ligand_comp_id_normalization_contract_ready",
        "ligand_comp_id_single_component_contract_ready",
        "ready_for_ligand_comp_id_semantics_integration",
        "ready_for_admission_evaluator_interface_implementation",
        "feature_semantics_audit_required_before_training",
        "all_contract_checks_passed", "all_example_checks_passed",
        "all_source_boundary_checks_passed", "all_source_semantics_checks_passed",
        "all_safety_checks_passed", "all_checks_passed",
    ))
    assert all(manifest[key] is False for key in (
        "ligand_comp_id_semantics_integrated", "integration_applied_current_step",
        "admit_003_rule_logic_ready", "ready_for_admission_evaluator_rule_logic_implementation",
        "ready_for_real_candidate_evaluation", "ready_for_bulk_download_now",
        "ready_for_training", "ready_to_train_now", "candidate_records_materialized_current_step",
        "download_queue_materialized_current_step", "raw_structure_read_current_step",
        "network_access_used_current_step", "external_component_registry_lookup_current_step",
    ))
    assert manifest["blocking_reasons"] == []
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert gate.TARGET_BLOCKER in [row["issue_id"] for row in source["issue_rows"]]
    serialized = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in serialized.lower()
    assert "/home/" not in serialized


def main() -> int:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    first = gate.run_covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1(root)
    _validate_exact_outputs(root)
    first_hashes = {
        name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    }
    second = gate.run_covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1(root)
    _validate_exact_outputs(root)
    second_hashes = {
        name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    }
    assert first == second and first_hashes == second_hashes
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest == second
    _validate_manifest_and_outputs(manifest, root, first_hashes)
    print(f"stage={gate.STAGE}")
    print("all_checks_passed=true")
    print("ligand_comp_id_semantics_frozen=true")
    print("ligand_comp_id_semantics_integrated=false")
    print("admit_003_rule_logic_ready=false")
    print("upstream_effective_issue_count=11")
    print("expected_post_integration_issue_count=10")
    print("ready_for_ligand_comp_id_semantics_integration=true")
    print("ready_for_real_candidate_evaluation=false")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    print("ligand_comp_id_semantics_design_outputs_byte_identical=true")
    print("covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
