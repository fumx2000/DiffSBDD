#!/usr/bin/env python3
"""Validate deterministic Step14AU-E0-P6-A design-gate outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate
    as gate,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _serialized_rows(
    rows: list[dict[str, Any]], columns: tuple[str, ...]
) -> list[dict[str, str]]:
    return [
        {column: str(gate._csv_value(row[column])) for column in columns}
        for row in rows
    ]


def _output_hashes(root: Path) -> dict[str, str]:
    return {name: _sha256(root / name) for name in gate.OUTPUT_FILES}


def _validate_exact_output_set(root: Path) -> None:
    assert root.is_dir() and not root.is_symlink()
    assert tuple(sorted(path.name for path in root.iterdir())) == tuple(
        sorted(gate.OUTPUT_FILES)
    )
    assert all(
        (root / name).is_file() and not (root / name).is_symlink()
        for name in gate.OUTPUT_FILES
    )


def validate_materialized_outputs(
    root: Path, expected_hashes: dict[str, str] | None = None
) -> dict[str, Any]:
    """Validate all persisted rows and the manifest without rewriting files."""
    _validate_exact_output_set(root)
    current_hashes = _output_hashes(root)
    if expected_hashes is not None:
        assert current_hashes == expected_hashes

    state = gate.build_design_state()
    contract = _csv_rows(root / gate.CONTRACT_FILENAME)
    bindings = _csv_rows(root / gate.BINDING_FILENAME)
    sources = _csv_rows(root / gate.SOURCE_FILENAME)
    safety = _csv_rows(root / gate.SAFETY_FILENAME)
    issues = _csv_rows(root / gate.ISSUE_FILENAME)
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))

    assert contract == _serialized_rows(state["contract_rows"], gate.CONTRACT_COLUMNS)
    assert bindings == _serialized_rows(state["binding_rows"], gate.BINDING_COLUMNS)
    assert sources == _serialized_rows(state["source_rows"], gate.SOURCE_COLUMNS)
    assert safety == _serialized_rows(state["safety_rows"], gate.SAFETY_COLUMNS)
    assert issues == _serialized_rows(state["issue_rows"], gate.ISSUE_COLUMNS)
    assert len(contract) == 48
    assert len(bindings) == 11 and len(gate.BINDING_COLUMNS) == 26
    assert len(sources) == 12
    assert len(safety) == 20
    assert len(issues) == 3

    actual_p5b_header = gate._read_csv_header(gate.P5B_CASE_SIDECAR_PATH)
    assert len(actual_p5b_header) == 33
    assert actual_p5b_header == gate.P5B_CASE_COLUMNS
    assert gate.FUTURE_REAL_SIDECAR_COLUMNS == (
        *gate.FUTURE_SIDECAR_PREFIX_COLUMNS, *actual_p5b_header
    )
    expansion_metadata = gate._read_csv(gate.EXPANSION_EXECUTION_PATH)
    assert len(expansion_metadata) == 8
    assert all(gate._expansion_identity_join_valid(row) for row in expansion_metadata)

    assert [row["binding_row_id"] for row in bindings] == [
        f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)
    ]
    assert [row["source_pipeline"] for row in bindings[:3]] == [
        "historical_sample_preparation_execution_smoke_v0"
    ] * 3
    assert [row["source_pipeline"] for row in bindings[3:]] == [
        "independent_group_expansion_batch_sample_preparation_execution_smoke_v0"
    ] * 8
    assert len({row["sample_preparation_input_id"] for row in bindings}) == 11
    assert len({(row["pdb_id"], row["ligand_comp_id"]) for row in bindings}) == 11
    assert all(
        row["metadata_join_status"] == "one_to_one_metadata_join_complete"
        for row in bindings
    )
    for row in bindings:
        assert gate._safe_raw_target_relative_path(row["raw_target_relative_path"])
        assert not Path(row["raw_target_relative_path"]).is_absolute()
        assert ".." not in Path(row["raw_target_relative_path"]).parts
        assert gate._safe_artifact_references(
            row["sample_artifact_root"],
            row["covalent_event_table_relative_path"],
            row["ligand_residue_atom_pair_table_relative_path"],
        )
        assert row["real_export_execution_allowed_current_step"] == "false"
        assert row["binding_status"] == "design_bound_raw_source_precondition_pending"

    expected_manifest = gate._manifest_payload(
        state, {name: current_hashes[name] for name in gate.CSV_OUTPUTS}
    )
    assert manifest == expected_manifest
    assert manifest["stage"] == gate.STAGE
    assert manifest["source_input_count"] == 12
    assert manifest["source_input_sha256"] == gate.SOURCE_SHA256
    assert manifest["output_files"] == list(gate.OUTPUT_FILES)
    assert manifest["output_file_count"] == 6
    assert manifest["non_manifest_output_count"] == 5
    assert manifest["canonical_mask_pairs"] == [
        list(pair) for pair in gate.CANONICAL_MASK_PAIRS
    ]
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["p5b_synthetic_smoke_passed"] is True
    assert manifest["p5b_case_count"] == 16
    assert manifest["p5b_sidecar_column_count"] == 33
    assert manifest["p5b_status_counts"] == {
        "exported_pass": 5, "exported_blocking": 5, "rejected": 6
    }
    assert manifest["real_sample_binding_count"] == 11
    assert manifest["historical_binding_count"] == 3
    assert manifest["expansion_binding_count"] == 8
    assert manifest["metadata_join_complete_count"] == 11
    assert manifest["raw_relative_path_persisted_count"] == 11
    assert manifest["raw_sha256_precondition_frozen_count"] == 0
    assert manifest["real_export_execution_allowed_count"] == 0
    assert manifest["integration_architecture"] == gate.INTEGRATION_ARCHITECTURE
    assert manifest["future_real_sidecar_column_count"] == 41
    assert manifest["future_real_sidecar_expected_row_count"] == 11
    assert manifest["real_pipeline_integration_design_frozen"] is True
    assert manifest["historical_parser_modification_required"] is False
    assert manifest["expansion_parser_modification_required"] is False
    assert manifest["real_executor_implemented"] is False
    assert manifest["real_raw_sources_read_current_step"] is False
    assert manifest["real_raw_sources_hashed_current_step"] is False
    assert manifest["real_provider_rows_materialized_current_step"] is False
    assert manifest["existing_real_sample_count"] == 11
    assert manifest["real_insertion_unknown_sample_count"] == 11
    assert manifest["real_insertion_absence_proven_sample_count"] == 0
    assert manifest["ready_for_real_raw_source_precondition_gate"] is True
    assert manifest["ready_for_real_provider_export_execution"] is False
    assert manifest["admit_004_rule_logic_ready"] is False
    assert manifest["ready_for_e1_residue_identity_semantics_design"] is False
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["validation_failures"] == []
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    return manifest


def main() -> None:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    source_hashes_before = {
        path.as_posix(): _sha256(REPO_ROOT / path) for path in gate.SOURCE_PATHS
    }
    first = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1()
    first_hashes = _output_hashes(root)
    first_manifest = validate_materialized_outputs(root, first_hashes)
    second = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1()
    second_manifest = validate_materialized_outputs(root, first_hashes)
    assert first["manifest"] == first_manifest == second["manifest"] == second_manifest
    assert _output_hashes(root) == first_hashes
    assert {
        path.as_posix(): _sha256(REPO_ROOT / path) for path in gate.SOURCE_PATHS
    } == source_hashes_before

    print(f"stage={gate.STAGE}")
    print("all_checks_passed=true")
    print("real_pipeline_integration_design_frozen=true")
    print(f"integration_architecture={gate.INTEGRATION_ARCHITECTURE}")
    print("real_sample_binding_count=11")
    print("historical_binding_count=3")
    print("expansion_binding_count=8")
    print("metadata_join_complete_count=11")
    print("raw_relative_path_persisted_count=11")
    print("raw_sha256_precondition_frozen_count=0")
    print("real_export_execution_allowed_count=0")
    print("future_real_sidecar_column_count=41")
    print("future_real_sidecar_expected_row_count=11")
    print("ready_for_real_raw_source_precondition_gate=true")
    print("ready_for_real_provider_export_execution=false")
    print("admit_004_rule_logic_ready=false")
    print("ready_for_e1_residue_identity_semantics_design=false")
    print("ready_for_real_candidate_evaluation=false")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    print("real_pipeline_integration_design_outputs_byte_identical=true")
    print(
        "covapie_bulk_download_admission_covalent_residue_locator_real_parser_"
        "provider_pipeline_integration_design_gate_v1_passed"
    )


if __name__ == "__main__":
    main()
