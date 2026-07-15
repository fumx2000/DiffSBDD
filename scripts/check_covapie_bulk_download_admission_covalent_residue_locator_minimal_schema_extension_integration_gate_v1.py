#!/usr/bin/env python3
"""Verify deterministic Step14AU-E0-P3 successor-schema outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate
    as gate,
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _validate_exact_output_files(root: Path) -> None:
    expected = {*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME}
    assert root.is_dir() and not root.is_symlink()
    assert {path.name for path in root.iterdir()} == expected
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in expected)


def _validate_manifest_and_outputs(
    manifest: dict[str, object], root: Path, first_hashes: dict[str, str],
) -> None:
    _validate_exact_output_files(root)
    current_hashes = {
        name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    }
    assert current_hashes == first_hashes

    source_rows = gate._source_boundary_rows()
    source = gate._load_source()
    assert gate._validate_source_boundary_rows(source_rows)
    assert gate._validate_d2_predecessor(source)
    assert gate._validate_p2_predecessor(source)
    assert gate._validate_p2_helpers()
    assert {row["source_relative_path"]: row["sha256_observed"] for row in source_rows} == gate.SOURCE_SHA256

    rules = _csv(root / gate.CSV_OUTPUTS[0])
    fields = _csv(root / gate.CSV_OUTPUTS[1])
    contexts = _csv(root / gate.CSV_OUTPUTS[2])
    safety = _csv(root / gate.CSV_OUTPUTS[3])
    issues = _csv(root / gate.CSV_OUTPUTS[4])
    assert gate._validate_integrated_rule_rows(rules, source["d2_rule_rows"])
    assert gate._validate_integrated_field_rows(fields, source["d2_field_rows"])
    assert gate._validate_integrated_context_rows(contexts, source["d2_context_rows"])
    assert gate._validate_issue_preservation_rows(issues, source["d2_issue_rows"])
    assert gate._validate_safety_rows(safety)
    assert len(rules) == 15 and len(fields) == 22 and len(contexts) == 18
    assert len(safety) == 20 and len(issues) == 10
    assert rules[:3] == source["d2_rule_rows"][:3]
    assert [row for row, old in zip(rules, source["d2_rule_rows"]) if row != old][0][
        "admission_rule_id"
    ] == "ADMIT_004"
    assert sum(row != old for row, old in zip(rules, source["d2_rule_rows"])) == 1
    assert fields[:17] == source["d2_field_rows"]
    assert fields[17:] == gate._new_field_rows()
    assert contexts == source["d2_context_rows"]
    assert issues == source["d2_issue_rows"]
    assert tuple(
        row["field_name"] for row in fields if row["implementation_semantics_complete"] == "true"
    ) == gate.COMPLETE_FIELD_NAMES
    assert tuple(row["issue_id"] for row in issues) == gate.REMAINING_ISSUE_IDS

    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == gate.STEP_LABEL
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["manifest_schema_version"] == gate.MANIFEST_SCHEMA_VERSION
    assert manifest["previous_stages"] == list(gate.PREVIOUS_STAGES)
    assert manifest["source_read_boundary"] == gate.SOURCE_READ_BOUNDARY
    assert manifest["source_input_count"] == 12
    assert manifest["source_input_sha256"] == gate.SOURCE_SHA256
    assert manifest["output_files"] == [*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME]
    assert manifest["output_file_count"] == 6 and manifest["non_manifest_output_count"] == 5
    assert manifest["output_sha256"] == {name: current_hashes[name] for name in gate.CSV_OUTPUTS}
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]
    assert manifest["canonical_mask_task_count"] == 5
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]
    assert (
        manifest["predecessor_field_count"], manifest["added_field_count"],
        manifest["integrated_field_count"], manifest["semantics_complete_field_count"],
        manifest["semantics_incomplete_field_count"],
    ) == (17, 5, 22, 7, 15)
    assert manifest["added_field_names"] == list(gate.p2_gate.PROPOSED_FIELD_NAMES)
    assert (
        manifest["predecessor_rule_count"], manifest["integrated_rule_count"],
        manifest["semantics_complete_rule_count"], manifest["semantics_incomplete_rule_count"],
    ) == (15, 15, 5, 10)
    assert (
        manifest["predecessor_context_count"], manifest["integrated_context_count"],
        manifest["deterministic_now_context_count"],
        manifest["deterministic_after_contract_freeze_context_count"],
        manifest["ready_evaluation_context_count"],
    ) == (18, 18, 8, 18, 8)
    assert manifest["remaining_issue_count"] == 10
    assert manifest["changed_rule_ids"] == ["ADMIT_004"]
    assert manifest["changed_context_items"] == []
    assert manifest["unchanged_predecessor_field_row_count"] == 17
    assert manifest["unchanged_context_row_count"] == 18
    assert manifest["unchanged_non_target_rule_row_count"] == 14
    assert manifest["resolved_p2_issue_ids"] == list(gate.RESOLVED_P2_ISSUE_IDS)
    assert manifest["remaining_p2_followup_issue_ids"] == list(
        gate.REMAINING_P2_FOLLOWUP_ISSUE_IDS
    )
    assert manifest["insertion_unknown_sample_count"] == 11
    assert manifest["fully_provable_pre_download_sample_count"] == 0
    assert manifest["samples_admissible_after_schema_extension_only"] == 0
    assert manifest["blocking_reasons"] == list(gate.REMAINING_ISSUE_IDS)
    assert manifest["validation_failures"] == []
    assert all(manifest[key] is True for key in (
        "covalent_residue_locator_schema_extension_frozen",
        "covalent_residue_locator_schema_extension_integrated",
        "parser_insertion_code_support_required", "provider_provenance_binding_required",
        "ready_for_parser_and_provider_provenance_export_design",
        "ready_for_admission_evaluator_interface_implementation",
        "feature_semantics_audit_required_before_training",
        "all_source_boundary_checks_passed", "all_d2_predecessor_checks_passed",
        "all_p2_predecessor_checks_passed", "all_p2_helper_checks_passed",
        "all_integrated_rule_checks_passed", "all_integrated_field_checks_passed",
        "all_integrated_context_checks_passed", "all_issue_preservation_checks_passed",
        "all_safety_checks_passed", "all_checks_passed",
    ))
    assert all(manifest[key] is False for key in (
        "insertion_code_provenance_export_ready",
        "insertion_code_present_value_grammar_fully_frozen", "admit_004_rule_logic_ready",
        "covalent_residue_identity_semantics_resolved",
        "covalent_residue_atom_name_semantics_resolved",
        "ready_for_e1_residue_identity_semantics_design",
        "ready_for_admission_evaluator_rule_logic_implementation",
        "ready_for_real_candidate_evaluation", "ready_for_bulk_download_now",
        "ready_for_training", "ready_to_train_now", "ignored_raw_structure_read_current_step",
        "checkpoint_read_current_step", "parser_modified_current_step",
        "sample_index_producer_modified_current_step", "candidate_provider_implemented_current_step",
        "candidate_records_materialized_current_step", "download_queue_materialized_current_step",
    ))
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    payload = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in payload.lower() and "/home/" not in payload


def main() -> int:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    source_before = {path.as_posix(): _hash(REPO_ROOT / path) for path in gate._source_paths()}
    first = gate.run_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1(root)
    _validate_exact_output_files(root)
    first_hashes = {
        name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    }
    second = gate.run_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1(root)
    _validate_exact_output_files(root)
    second_hashes = {
        name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    }
    source_after = {path.as_posix(): _hash(REPO_ROOT / path) for path in gate._source_paths()}
    assert first == second and first_hashes == second_hashes
    assert source_before == gate.SOURCE_SHA256 == source_after
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest == second
    _validate_manifest_and_outputs(manifest, root, first_hashes)

    print(f"stage={gate.STAGE}")
    print("all_checks_passed=true")
    print("covalent_residue_locator_schema_extension_integrated=true")
    print("predecessor_field_count=17")
    print("added_field_count=5")
    print("integrated_field_count=22")
    print("integrated_context_count=18")
    print("remaining_issue_count=10")
    print("insertion_unknown_sample_count=11")
    print("fully_provable_pre_download_sample_count=0")
    print("admit_004_rule_logic_ready=false")
    print("ready_for_e1_residue_identity_semantics_design=false")
    print("ready_for_parser_and_provider_provenance_export_design=true")
    print("ready_for_real_candidate_evaluation=false")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    print("covalent_residue_locator_schema_extension_integration_outputs_byte_identical=true")
    print(
        "covapie_bulk_download_admission_covalent_residue_locator_"
        "minimal_schema_extension_integration_gate_v1_passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
