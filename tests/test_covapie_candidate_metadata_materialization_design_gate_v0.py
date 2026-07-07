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

from covalent_ext import covapie_candidate_metadata_materialization_design_gate as design


ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_candidate_metadata_materialization_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 13AX check script before artifact tests"
    return json.loads(path.read_text(encoding="utf-8"))


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def test_step13aw_precondition_and_manifest_readiness() -> None:
    manifest13aw = json.loads(design.STEP13AW_MANIFEST_JSON.read_text(encoding="utf-8"))
    manifest = _manifest()
    assert manifest13aw["stage"] == design.PREVIOUS_STAGE
    assert manifest13aw["ready_for_covapie_candidate_metadata_materialization_design_gate"] is True
    assert manifest["stage"] == design.STAGE
    assert manifest["previous_stage"] == design.PREVIOUS_STAGE
    assert manifest["step13aw_raw_structure_event_annotation_qa_gate_validated"] is True
    assert manifest["accepted_preferred_event_count"] == 4
    assert manifest["blocked_unresolved_event_count"] == 1
    assert manifest["ready_for_covapie_candidate_metadata_materialization_smoke"] is True
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_accepted_inventory_has_four_unique_deterministic_ids() -> None:
    rows = _csv_rows(ROOT / "covapie_candidate_metadata_accepted_event_inventory.csv")
    manifest = _manifest()
    assert len(rows) == 4
    assert [row["pdb_id"] for row in rows] == ["1A3B", "1A3E", "1A46", "1A5G"]
    assert [row["het_code"] for row in rows] == ["T29", "T16", "00K", "00L"]
    ids = [row["future_candidate_metadata_id_preview"] for row in rows]
    assert ids == [
        "covpdb::1A3B::T29::H:SER195:OG-B",
        "covpdb::1A3E::T16::H:SER195:OG-B",
        "covpdb::1A46::00K::H:SER195:OG-C",
        "covpdb::1A5G::00L::H:SER195:OG-C",
    ]
    assert len(ids) == len(set(ids))
    assert all(" " not in candidate_id for candidate_id in ids)
    assert {row["accepted_for_future_candidate_metadata"] for row in rows} == {"True"}
    assert {row["accepted_for_future_automatic_allowlist"] for row in rows} == {"True"}
    assert {row["accepted_event_inventory_passed"] for row in rows} == {"True"}
    assert manifest["future_candidate_metadata_id_preview_count"] == 4
    assert manifest["future_candidate_metadata_id_unique_count"] == 4


def test_unresolved_event_is_excluded_without_candidate_id_preview() -> None:
    unresolved = _csv_rows(ROOT / "covapie_candidate_metadata_unresolved_event_exclusion_policy.csv")
    assert unresolved == [
        {
            "pdb_id": "1A54",
            "het_code": "MDC",
            "resolution_status": "raw_no_connectivity_records_found",
            "reason_unresolved": "raw_no_connectivity_records_found",
            "automatic_candidate_metadata_blocked": "True",
            "automatic_allowlist_blocked": "True",
            "future_allowed_path": "manual_review_or_connectivity_fallback_design",
            "exclusion_policy_passed": "True",
        }
    ]
    joined = "\n".join(",".join(row.values()) for row in unresolved)
    assert "candidate_metadata_id" not in joined


def test_schema_and_field_source_mapping_cover_required_fields() -> None:
    schema = _csv_rows(ROOT / "covapie_candidate_metadata_schema_contract.csv")
    mapping = _csv_rows(ROOT / "covapie_candidate_metadata_field_source_mapping_contract.csv")
    assert [row["candidate_metadata_field"] for row in schema] == design.CANDIDATE_METADATA_FIELDS
    assert {row["schema_contract_passed"] for row in schema} == {"True"}
    assert len(mapping) == len(schema)
    assert {row["candidate_metadata_field"] for row in mapping} == set(design.CANDIDATE_METADATA_FIELDS)
    assert {row["materialization_design_contract_passed"] for row in mapping} == {"True"}
    by_field = {row["candidate_metadata_field"]: row for row in mapping}
    assert by_field["pdb_id"]["source_artifact"].endswith("covapie_raw_structure_preferred_event_acceptance_qa.csv")
    assert by_field["event_key_resolution_status"]["source_artifact"].endswith("covapie_raw_structure_event_candidate_field_integrity_qa.csv")
    assert by_field["source_metadata_csv_row_key"]["source_artifact"].endswith("covpdb_complexes_metadata_manual.csv")
    assert by_field["unresolved_exclusion_reason"]["source_artifact"].endswith("covapie_raw_structure_unresolved_event_handling_qa.csv")


def test_row_identity_validation_plan_and_allowlist_dependency() -> None:
    identity = _csv_rows(ROOT / "covapie_candidate_metadata_row_identity_contract.csv")
    validation = _csv_rows(ROOT / "covapie_candidate_metadata_validation_contract.csv")
    plan = _csv_rows(ROOT / "covapie_candidate_metadata_materialization_smoke_plan.csv")
    allowlist = _csv_rows(ROOT / "covapie_candidate_allowlist_dependency_contract.csv")
    assert {row["row_identity_contract_passed"] for row in identity} == {"True"}
    by_identity = {row["identity_contract_item"]: row for row in identity}
    assert by_identity["candidate_metadata_id_format"]["contract_value"] == "covpdb::{pdb_id}::{het_code}::{chain_id}:{residue_name}{residue_index}:{residue_atom_name}-{ligand_atom_name}"
    assert by_identity["unresolved_event_has_no_candidate_metadata_id"]["row_identity_contract_passed"] == "True"
    assert {row["validation_contract_passed"] for row in validation} == {"True"}
    by_plan = {row["planned_step"]: row for row in plan}
    assert by_plan["first4_candidate_metadata_materialization_smoke"]["planned_action"] == "ready_next"
    assert "candidate_metadata_smoke" in by_plan["first4_candidate_metadata_materialization_smoke"]["allowed_outputs"]
    assert by_plan["candidate_allowlist_materialization_design_gate"]["planned_action"] == "blocked_until_candidate_metadata_qa"
    assert by_plan["training"]["planned_action"] == "blocked"
    assert {row["materialization_smoke_plan_passed"] for row in plan} == {"True"}
    assert {row["current_step_allowed"] for row in allowlist} == {"False"}
    assert {row["dependency"] for row in allowlist} >= {"candidate_metadata_materialization_smoke_and_qa"}
    assert {row["dependency_contract_passed"] for row in allowlist} == {"True"}


def test_boundaries_masks_feature_semantics_and_leakage() -> None:
    materialization = _csv_rows(ROOT / "covapie_candidate_metadata_materialization_boundary_audit.csv")
    execution = _csv_rows(ROOT / "covapie_candidate_metadata_execution_boundary_audit.csv")
    mask = _csv_rows(ROOT / "covapie_candidate_metadata_mask_scope_audit.csv")
    feature = _csv_rows(ROOT / "covapie_candidate_metadata_feature_semantics_audit.csv")
    leakage = _csv_rows(ROOT / "covapie_candidate_metadata_leakage_split_audit.csv")
    manifest = _manifest()
    assert {row["current_step_status"] for row in materialization} == {"blocked_current_design_gate"}
    assert {row["materialization_boundary_passed"] for row in materialization} == {"True"}
    by_boundary = {row["boundary_item"]: row["current_step_status"] for row in execution}
    assert by_boundary["candidate_metadata_materialization_design_gate"] == "executed_design_gate_only"
    assert by_boundary["metadata_csv_read"] == "executed_metadata_read_only"
    for item in ["raw_file_presence_check", "external_network_access", "raw_structure_download", "raw_data_text_read", "rdkit_use", "biopdb_use", "gemmi_use", "torch_import", "model_forward", "training_claim"]:
        assert by_boundary[item] == "not_executed_or_not_allowed"
    assert [row["canonical_mask_task_name"] for row in mask] == design.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == design.CANONICAL_MASK_TASK_ALIASES
    assert {row["no_extra_mask_tasks_added"] for row in mask} == {"True"}
    assert manifest["b3_scaffold_only_included"] is True
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    assert {row["feature_semantics_audit_passed"] for row in feature} == {"True"}
    assert {row["split_written_current_step"] for row in leakage} == {"False"}
    assert {row["leakage_matrix_written_current_step"] for row in leakage} == {"False"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True


def test_no_forbidden_imports_outputs_or_materialization() -> None:
    module_path = Path("src/covalent_ext/covapie_candidate_metadata_materialization_design_gate.py")
    script_path = Path("scripts/check_covapie_candidate_metadata_materialization_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    bad = [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden]
    assert bad == []
    materialized_names = {"covapie_candidate_metadata.csv", "covapie_candidate_allowlist.csv"}
    assert not any(path.name in materialized_names for path in ROOT.rglob("*"))
    raw_root = Path("data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0")
    tracked = subprocess.run(["git", "ls-files", str(raw_root)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(raw_root)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    manifest = _manifest()
    for key in ["network_access_used", "raw_structure_downloaded", "raw_data_read", "sdf_read", "pdb_read", "mmcif_text_read", "rdkit_used", "biopdb_parser_used", "gemmi_used", "torch_imported", "model_forward_called", "training_allowed", "candidate_metadata_materialized", "candidate_allowlist_materialized"]:
        assert manifest[key] is False
