#!/usr/bin/env python3
"""Check deterministic Step14AU-E0-P2 residue-locator design outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate as gate  # noqa: E402


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expected_names() -> set[str]:
    return {*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME}


def _validate_exact_outputs(root: Path) -> None:
    assert root.is_dir() and not root.is_symlink()
    assert {path.name for path in root.iterdir()} == _expected_names()
    assert all(
        (root / name).is_file() and not (root / name).is_symlink()
        for name in _expected_names()
    )


def _validate_helpers() -> None:
    assert gate.normalize_covalent_residue_locator_namespace("auth").passed
    assert gate.normalize_covalent_residue_locator_namespace("label").passed
    assert not gate.normalize_covalent_residue_locator_namespace("AUTH").passed
    assert not gate.normalize_covalent_residue_locator_namespace("mixed").passed

    absent = gate.validate_covalent_residue_insertion_code("absent", "")
    assert absent.passed and absent.schema_combination_valid and not absent.blocks_admit_004
    assert not gate.validate_covalent_residue_insertion_code("absent", "A").passed
    present = gate.validate_covalent_residue_insertion_code("present", "A")
    assert present.passed and present.schema_combination_valid
    assert not gate.validate_covalent_residue_insertion_code("present", "").passed
    unknown = gate.validate_covalent_residue_insertion_code("unknown", "")
    assert not unknown.passed and unknown.schema_combination_valid
    assert unknown.blocks_admit_004
    assert unknown.blocking_reason == (
        "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
    )
    assert not gate.validate_covalent_residue_insertion_code("unknown", "A").passed

    source_id = gate.normalize_covalent_residue_locator_provenance_source_id(
        "step14au-e0-p1:tracked-evidence"
    )
    assert source_id.passed
    assert not gate.normalize_covalent_residue_locator_provenance_source_id(" bad").passed
    valid_sha = "a" * 64
    assert gate.validate_covalent_residue_locator_provenance_sha256(valid_sha).passed
    assert not gate.validate_covalent_residue_locator_provenance_sha256("A" * 64).passed
    assert not gate.validate_covalent_residue_locator_provenance_sha256(
        "sha256:" + valid_sha
    ).passed


def _validate_manifest_and_outputs(
    root: Path, manifest: dict[str, object], first_hashes: dict[str, str],
) -> None:
    _validate_exact_outputs(root)
    current_hashes = {name: _hash(root / name) for name in _expected_names()}
    assert current_hashes == first_hashes

    source_rows = gate._source_boundary_rows()
    assert gate._validate_source_boundary_rows(source_rows)
    assert {
        row["source_relative_path"]: row["sha256_observed"] for row in source_rows
    } == gate.SOURCE_SHA256
    assert gate._validate_d2_predecessor(gate._load_d2_source())
    assert gate._validate_representation_evidence(gate._load_representation_evidence())
    backfill_evidence = gate._load_backfill_evidence()
    backfill_specs = gate._derive_backfill_specs_from_committed_evidence(
        backfill_evidence
    )
    assert len(backfill_specs) == 11
    assert all(spec["evidence_complete"] is True for spec in backfill_specs)
    _validate_helpers()

    contract = _csv(root / gate.CSV_OUTPUTS[0])
    backfill = _csv(root / gate.CSV_OUTPUTS[1])
    disk_sources = _csv(root / gate.CSV_OUTPUTS[2])
    safety = _csv(root / gate.CSV_OUTPUTS[3])
    issues = _csv(root / gate.CSV_OUTPUTS[4])
    assert gate._validate_contract_rows(contract) and len(contract) == 40
    assert gate._validate_backfill_rows(backfill) and len(backfill) == 11
    assert gate._validate_source_boundary_rows(disk_sources)
    assert len(disk_sources) == len(gate.SOURCE_PATHS)
    assert gate._validate_safety_rows(safety) and len(safety) == 20
    assert gate._validate_issue_rows(issues) and len(issues) == 2
    assert [row["issue_id"] for row in issues] == list(gate.P2_ISSUE_IDS)

    assert sum(row["auth_label_conflict_observed"] == "true" for row in backfill) == 3
    assert sum(
        row["backfill_classification"] == "NAMESPACE_PROVABLE_INSERTION_UNKNOWN"
        for row in backfill
    ) == 8
    assert all(row["insertion_code_state"] == "unknown" for row in backfill)
    assert all(
        row["admissible_for_e1_after_schema_extension_only"] == "false"
        for row in backfill
    )

    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == gate.STEP_LABEL
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["manifest_schema_version"] == gate.MANIFEST_SCHEMA_VERSION
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["source_read_boundary"] == gate.SOURCE_READ_BOUNDARY
    assert manifest["source_input_count"] == len(gate.SOURCE_PATHS)
    assert manifest["source_input_sha256"] == gate.SOURCE_SHA256
    assert manifest["output_files"] == [*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME]
    assert manifest["output_file_count"] == 6
    assert manifest["non_manifest_output_count"] == 5
    assert manifest["output_sha256"] == {
        name: current_hashes[name] for name in gate.CSV_OUTPUTS
    }
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["canonical_mask_pairs"] == [
        list(pair) for pair in gate.CANONICAL_MASK_PAIRS
    ]
    assert manifest["canonical_mask_task_count"] == 5
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]
    assert manifest["current_effective_field_count"] == 17
    assert manifest["proposed_extension_field_count"] == 5
    assert manifest["proposed_post_extension_field_count"] == 22
    assert manifest["proposed_field_names"] == list(gate.PROPOSED_FIELD_NAMES)
    assert manifest["current_effective_context_count"] == 18
    assert manifest["current_effective_remaining_issue_count"] == 10
    assert manifest["existing_sample_count"] == 11
    assert manifest["auth_label_conflict_sample_count"] == 3
    assert manifest["namespace_provable_insertion_unknown_sample_count"] == 8
    assert manifest["fully_provable_pre_download_sample_count"] == 0
    assert manifest["insertion_unknown_sample_count"] == 11
    assert manifest["samples_admissible_after_schema_extension_only"] == 0

    true_keys = (
        "artifact_reference_paths_not_recursively_opened",
        "covalent_residue_locator_schema_extension_frozen",
        "namespace_contract_ready",
        "same_namespace_contract_ready",
        "insertion_code_state_contract_ready",
        "provenance_source_id_contract_ready",
        "provenance_sha256_contract_ready",
        "ready_for_schema_extension_integration",
        "parser_insertion_code_support_required",
        "provider_provenance_binding_required",
        "feature_semantics_audit_required_before_training",
        "all_source_boundary_checks_passed",
        "all_d2_predecessor_checks_passed",
        "all_representation_evidence_checks_passed",
        "all_contract_checks_passed",
        "all_backfill_audit_checks_passed",
        "all_safety_checks_passed",
        "all_issue_inventory_checks_passed",
        "all_checks_passed",
    )
    false_keys = (
        "covalent_residue_locator_schema_extension_integrated",
        "current_effective_schema_modified_current_step",
        "admit_004_rule_logic_ready",
        "covalent_residue_identity_semantics_resolved",
        "covalent_residue_atom_name_semantics_resolved",
        "insertion_code_present_value_grammar_fully_frozen",
        "ready_for_e1_residue_identity_semantics_design",
        "ready_for_admission_evaluator_rule_logic_implementation",
        "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now",
        "ready_for_training",
        "ready_to_train_now",
        "ignored_raw_structure_read_current_step",
        "checkpoint_read_current_step",
        "candidate_records_materialized_current_step",
        "download_queue_materialized_current_step",
    )
    assert all(manifest[key] is True for key in true_keys)
    assert all(manifest[key] is False for key in false_keys)
    assert manifest["blocking_reasons"] == list(gate.P2_ISSUE_IDS)
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    serialized = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in serialized.lower()
    assert "/home/" not in serialized


def _validate_disk_outputs(root: Path, first_hashes: dict[str, str]) -> None:
    """Reload every output from disk before applying all semantic checks."""
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    _validate_manifest_and_outputs(root, manifest, first_hashes)


def main() -> int:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    first_manifest = gate.run_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1(root)
    _validate_exact_outputs(root)
    first_hashes = {name: _hash(root / name) for name in _expected_names()}
    first_source_hashes = {
        path.as_posix(): _hash(REPO_ROOT / path) for path in gate.SOURCE_PATHS
    }

    second_manifest = gate.run_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1(root)
    _validate_exact_outputs(root)
    second_hashes = {name: _hash(root / name) for name in _expected_names()}
    second_source_hashes = {
        path.as_posix(): _hash(REPO_ROOT / path) for path in gate.SOURCE_PATHS
    }
    assert first_manifest == second_manifest
    assert first_hashes == second_hashes
    assert first_source_hashes == second_source_hashes == gate.SOURCE_SHA256

    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest == second_manifest
    _validate_disk_outputs(root, first_hashes)

    print(f"stage={gate.STAGE}")
    print("all_checks_passed=true")
    print("covalent_residue_locator_schema_extension_frozen=true")
    print("covalent_residue_locator_schema_extension_integrated=false")
    print("current_effective_field_count=17")
    print("proposed_extension_field_count=5")
    print("proposed_post_extension_field_count=22")
    print("existing_sample_count=11")
    print("insertion_unknown_sample_count=11")
    print("fully_provable_pre_download_sample_count=0")
    print("ready_for_schema_extension_integration=true")
    print("ready_for_e1_residue_identity_semantics_design=false")
    print("admit_004_rule_logic_ready=false")
    print("ready_for_real_candidate_evaluation=false")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    print("covalent_residue_locator_schema_extension_outputs_byte_identical=true")
    print(
        "covapie_bulk_download_admission_covalent_residue_locator_"
        "minimal_schema_extension_design_gate_v1_passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
