from __future__ import annotations

import ast
import csv
import json
import subprocess
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_external_metadata_index_schema_probe_design_gate as gate


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_external_metadata_index_schema_probe_design_gate_v0.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    if not gate.MANIFEST_JSON.is_file():
        _ensure_outputs()
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def test_check_script_passes_and_validates_preconditions() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_external_metadata_index_schema_probe_design_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13ap_external_metadata_index_rediscovery_smoke_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_input_schemas_are_expected_sizes() -> None:
    assert gate.validate_step13ap_precondition_v0() is True
    assert gate.validate_metadata_csv_v0() is True
    assert gate.validate_allowlist_template_v0() is True
    assert gate.validate_step13am_source_config_v0() is True
    assert gate.validate_covapie_naming_convention_v0() is True
    assert len(_csv_rows(gate.METADATA_CSV)) == 25
    with gate.METADATA_CSV.open(newline="", encoding="utf-8") as handle:
        assert list(csv.DictReader(handle).fieldnames or []) == gate.METADATA_COLUMNS
    with gate.ALLOWLIST_TEMPLATE_CSV.open(newline="", encoding="utf-8") as handle:
        assert list(csv.DictReader(handle).fieldnames or []) == gate.ALLOWLIST_COLUMNS


def test_observed_schema_and_allowlist_mapping_outputs() -> None:
    manifest = _manifest()
    observed = _csv_rows(gate.OBSERVED_SCHEMA_AUDIT_CSV)
    mapping = _csv_rows(gate.ALLOWLIST_MAPPING_PROBE_CSV)
    missing = _csv_rows(gate.MISSING_FIELD_PLAN_CSV)
    assert manifest["metadata_csv_row_count"] == 25
    assert manifest["metadata_csv_column_count"] == 19
    assert manifest["observed_covpdb_metadata_column_count"] == 19
    assert len(observed) == 19
    assert [row["observed_column"] for row in observed] == gate.METADATA_COLUMNS
    assert {row["observed_schema_audit_passed"] for row in observed} == {"True"}
    assert len(mapping) == 15
    assert [row["allowlist_column"] for row in mapping] == gate.ALLOWLIST_COLUMNS
    by_column = {row["allowlist_column"]: row for row in mapping}
    assert {column for column, row in by_column.items() if row["mapping_status"] == "direct_available"} == {
        "source_dataset_name",
        "source_dataset_version",
        "pdb_id",
        "ligand_id",
    }
    assert {column for column, row in by_column.items() if row["mapping_status"] == "generated_future"} == {
        "candidate_id",
        "restoration_policy_id",
        "manual_review_status",
        "include_in_smoke",
        "exclusion_reason",
    }
    assert {column for column, row in by_column.items() if row["mapping_status"] == "missing_critical"} == {
        "chain_id",
        "residue_name",
        "residue_index",
        "residue_atom_name",
        "covalent_bond_atom_pair",
    }
    assert {column for column, row in by_column.items() if row["mapping_status"] == "missing_deferred"} == {"source_file_relative_path"}
    assert by_column["ligand_id"]["materialization_ready"] == "True"
    assert by_column["ligand_id"]["blocker_reason"] == "ambiguous_source_choice"
    assert len(missing) == 10
    assert {row["missing_field"] for row in missing if row["missing_field_type"] == "critical_event_key"} == {
        "chain_id",
        "residue_name",
        "residue_index",
        "residue_atom_name",
        "covalent_bond_atom_pair",
    }


def test_event_key_gap_and_materialization_boundaries() -> None:
    manifest = _manifest()
    event = _csv_rows(gate.EVENT_KEY_GAP_AUDIT_CSV)
    blockers = _csv_rows(gate.CANDIDATE_BLOCKER_AUDIT_CSV)
    assert len(event) == 1
    row = event[0]
    assert row["event_identity_key_policy"] == "no_pdb_id_only_join"
    assert row["currently_available_key_parts"] == "pdb_id+ligand_id_candidate"
    assert row["missing_minimal_key_parts"] == "chain_id+residue_name+residue_index+residue_atom_name"
    assert row["missing_preferred_key_parts"] == "covalent_bond_atom_pair"
    assert row["minimal_event_key_materializable"] == "False"
    assert row["preferred_event_key_materializable"] == "False"
    assert row["one_row_one_covalent_event_enforceable"] == "False"
    assert row["event_key_gap_audit_passed"] == "True"
    assert [row["blocker_name"] for row in blockers] == gate.CANDIDATE_BLOCKERS
    assert {row["candidate_metadata_materialized"] for row in blockers} == {"False"}
    assert {row["candidate_allowlist_materialized"] for row in blockers} == {"False"}
    assert manifest["minimal_event_key_materializable"] is False
    assert manifest["preferred_event_key_materializable"] is False
    assert manifest["one_row_one_covalent_event_enforceable"] is False
    assert manifest["candidate_metadata_materialized"] is False
    assert manifest["candidate_allowlist_materialized"] is False


def test_no_network_raw_model_or_forbidden_runtime_imports() -> None:
    module_path = Path("src/covalent_ext/covapie_external_metadata_index_schema_probe_design_gate.py")
    script_path = Path("scripts/check_covapie_external_metadata_index_schema_probe_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    for path in [module_path, script_path]:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run":
                call_text = ast.get_source_segment(text, node) or ""
                assert "curl" not in call_text
                assert "wget" not in call_text


def test_masks_feature_semantics_leakage_and_readiness() -> None:
    manifest = _manifest()
    mask = _csv_rows(gate.MASK_SCOPE_AUDIT_CSV)
    feature = _csv_rows(gate.FEATURE_SEMANTICS_AUDIT_CSV)
    leakage = _csv_rows(gate.LEAKAGE_SPLIT_AUDIT_CSV)
    assert [row["canonical_mask_task_name"] for row in mask] == gate.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == gate.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert len(feature) == 12
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    assert len(leakage) == 12
    assert {row["current_step_status"] for row in leakage} == {"placeholder_only_no_split_written"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}
    assert manifest["ready_for_covapie_external_metadata_index_schema_probe_design_gate"] is False
    assert manifest["ready_for_covapie_covpdb_complex_card_metadata_probe_design_gate"] is True
    assert manifest["ready_for_covapie_candidate_metadata_materialization"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_covpdb_complex_card_metadata_probe_design_gate"


def test_manifest_safety_flags_and_output_row_counts() -> None:
    manifest = _manifest()
    assert manifest["precondition_audit_row_count"] == len(_csv_rows(gate.PRECONDITION_AUDIT_CSV)) == 8
    assert manifest["observed_schema_audit_row_count"] == len(_csv_rows(gate.OBSERVED_SCHEMA_AUDIT_CSV)) == 19
    assert manifest["allowlist_schema_mapping_probe_row_count"] == len(_csv_rows(gate.ALLOWLIST_MAPPING_PROBE_CSV)) == 15
    assert manifest["missing_field_resolution_plan_row_count"] == len(_csv_rows(gate.MISSING_FIELD_PLAN_CSV)) == 10
    assert manifest["event_key_gap_audit_row_count"] == len(_csv_rows(gate.EVENT_KEY_GAP_AUDIT_CSV)) == 1
    assert manifest["candidate_materialization_blocker_audit_row_count"] == len(_csv_rows(gate.CANDIDATE_BLOCKER_AUDIT_CSV)) == 9
    assert manifest["execution_boundary_audit_row_count"] == len(_csv_rows(gate.EXECUTION_BOUNDARY_AUDIT_CSV)) == 20
    assert manifest["git_safety_audit_row_count"] == len(_csv_rows(gate.GIT_SAFETY_AUDIT_CSV)) == 10
    assert manifest["mask_scope_audit_row_count"] == len(_csv_rows(gate.MASK_SCOPE_AUDIT_CSV)) == 5
    assert manifest["feature_semantics_audit_row_count"] == len(_csv_rows(gate.FEATURE_SEMANTICS_AUDIT_CSV)) == 12
    assert manifest["leakage_split_audit_row_count"] == len(_csv_rows(gate.LEAKAGE_SPLIT_AUDIT_CSV)) == 12
    for key in [
        "network_access_used",
        "urllib_used",
        "requests_used",
        "browser_used",
        "raw_structure_downloaded",
        "raw_ligand_downloaded",
        "raw_data_read",
        "raw_file_copied",
        "sdf_read",
        "pdb_read",
        "mmcif_text_read",
        "gzip_open_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "torch_imported",
        "torch_tensor_created",
        "tensor_artifact_written",
        "npz_created",
        "pt_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
    ]:
        assert manifest[key] is False
