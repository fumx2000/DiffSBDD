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

from covalent_ext import covapie_covpdb_raw_structure_event_annotation_qa_gate as qa


ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_qa_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_raw_structure_event_annotation_qa_gate_manifest.json"
    assert path.is_file(), "Run the Step 13AW check script before artifact tests"
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


def test_step13av_precondition_and_manifest_contract() -> None:
    manifest13av = json.loads(qa.STEP13AV_MANIFEST_JSON.read_text(encoding="utf-8"))
    manifest = _manifest()
    assert manifest13av["stage"] == qa.PREVIOUS_STAGE
    assert manifest13av["raw_structure_download_succeeded_count"] == 5
    assert manifest13av["raw_resolves_preferred_event_key_count"] == 4
    assert manifest13av["raw_no_connectivity_records_found_count"] == 1
    assert manifest["stage"] == qa.STAGE
    assert manifest["previous_stage"] == qa.PREVIOUS_STAGE
    assert manifest["step13av_raw_structure_event_annotation_smoke_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_download_storage_and_format_qa() -> None:
    download = _csv_rows(ROOT / "covapie_raw_structure_download_integrity_qa.csv")
    storage = _csv_rows(ROOT / "covapie_raw_structure_storage_safety_qa.csv")
    formats = _csv_rows(ROOT / "covapie_raw_structure_format_coverage_qa.csv")
    assert len(download) == 5
    assert len(storage) == 5
    assert len(formats) == 5
    assert {row["selected_raw_format"] for row in download} == {"mmcif"}
    assert {row["primary_fetch_succeeded"] for row in download} == {"True"}
    assert {row["fallback_fetch_attempted"] for row in download} == {"False"}
    assert {row["raw_ligand_downloaded"] for row in download} == {"False"}
    assert {row["archive_downloaded"] for row in download} == {"False"}
    assert {row["download_integrity_qa_passed"] for row in download} == {"True"}
    for key in [
        "raw_file_exists",
        "under_allowed_raw_storage_root",
        "suffix_allowed",
        "raw_file_untracked",
        "raw_file_not_staged",
        "raw_file_not_committed",
        "raw_file_not_copied_to_derived",
        "storage_safety_qa_passed",
    ]:
        assert {row[key] for row in storage} == {"True"}
    assert {row["atom_site_loop_found"] for row in formats} == {"True"}
    assert sum(row["struct_conn_loop_found"] == "True" for row in formats) == 4
    assert {row["pdb_link_row_count"] for row in formats} == {"0"}
    assert {row["pdb_conect_row_count"] for row in formats} == {"0"}
    assert {row["format_coverage_qa_passed"] for row in formats} == {"True"}


def test_struct_conn_atom_site_and_candidate_integrity_qa() -> None:
    struct_conn = _csv_rows(ROOT / "covapie_raw_structure_struct_conn_coverage_qa.csv")
    atom_site = _csv_rows(ROOT / "covapie_raw_structure_atom_site_validation_qa.csv")
    candidate = _csv_rows(ROOT / "covapie_raw_structure_event_candidate_field_integrity_qa.csv")
    assert len(struct_conn) == 5
    assert len(atom_site) == 5
    assert len(candidate) == 5
    by_key = {(row["pdb_id"], row["het_code"]): row for row in struct_conn}
    assert sum(int(row["protein_ligand_candidate_count"]) == 1 for row in struct_conn) == 4
    assert by_key[("1A54", "MDC")]["struct_conn_coverage_status"] == "blocked_unresolved_no_connectivity"
    assert {row["struct_conn_coverage_qa_passed"] for row in struct_conn} == {"True"}
    assert {row["atom_site_loop_found"] for row in atom_site} == {"True"}
    assert {row["atom_site_validation_qa_passed"] for row in atom_site} == {"True"}
    accepted = [row for row in candidate if row["candidate_acceptance_status"] == "accepted_preferred_event_for_future_metadata"]
    blocked = [row for row in candidate if row["candidate_acceptance_status"] == "blocked_unresolved_no_connectivity"]
    assert len(accepted) == 4
    assert len(blocked) == 1
    assert blocked[0]["pdb_id"] == "1A54"
    assert blocked[0]["het_code"] == "MDC"
    for row in accepted:
        assert row["raw_connection_source"] == "mmcif_struct_conn"
        assert row["chain_id"]
        assert row["residue_name"]
        assert row["residue_index"]
        assert row["residue_atom_name"]
        assert row["ligand_atom_name"]
        assert row["covalent_bond_atom_pair"]
        assert row["protein_partner_atom_exists"] == "True"
        assert row["ligand_partner_atom_exists"] == "True"
        assert row["manual_review_required"] == "False"
    assert {row["candidate_field_integrity_qa_passed"] for row in candidate} == {"True"}


def test_resolution_preferred_unresolved_and_readiness_qa() -> None:
    resolution = _csv_rows(ROOT / "covapie_raw_structure_event_key_resolution_summary_qa.csv")
    preferred = _csv_rows(ROOT / "covapie_raw_structure_preferred_event_acceptance_qa.csv")
    unresolved = _csv_rows(ROOT / "covapie_raw_structure_unresolved_event_handling_qa.csv")
    readiness = _csv_rows(ROOT / "covapie_raw_structure_candidate_metadata_readiness_decision_qa.csv")
    manifest = _manifest()
    observed = {row["resolution_status"]: int(row["observed_count"]) for row in resolution}
    assert observed == {"raw_resolves_preferred_event_key": 4, "raw_no_connectivity_records_found": 1}
    assert {row["current_step_materialization_blocked"] for row in resolution} == {"True"}
    assert {row["event_key_resolution_summary_qa_passed"] for row in resolution} == {"True"}
    assert len(preferred) == 4
    assert {row["accepted_for_future_candidate_metadata"] for row in preferred} == {"True"}
    assert {row["accepted_for_future_automatic_allowlist"] for row in preferred} == {"True"}
    assert {row["current_step_materialization_allowed"] for row in preferred} == {"False"}
    assert {row["preferred_event_acceptance_qa_passed"] for row in preferred} == {"True"}
    assert unresolved == [
        {
            "pdb_id": "1A54",
            "het_code": "MDC",
            "resolution_status": "raw_no_connectivity_records_found",
            "candidate_found": "False",
            "reason_unresolved": "raw_no_connectivity_records_found",
            "automatic_candidate_metadata_blocked": "True",
            "automatic_allowlist_blocked": "True",
            "recommended_handling": "defer_to_manual_review_or_future_connectivity_fallback_design",
            "unresolved_event_handling_qa_passed": "True",
        }
    ]
    by_decision = {row["decision_item"]: row for row in readiness}
    assert by_decision["candidate_metadata_materialization_design_gate"]["current_readiness_status"] == "ready_next"
    assert by_decision["candidate_allowlist_materialization_design_gate"]["current_readiness_status"] == "blocked_until_candidate_metadata_gate"
    assert by_decision["training"]["current_readiness_status"] == "blocked_until_feature_semantics_and_leakage_split_and_dataset_materialization"
    assert manifest["ready_for_covapie_candidate_metadata_materialization_design_gate"] is True
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False


def test_boundaries_masks_feature_semantics_and_leakage() -> None:
    materialization = _csv_rows(ROOT / "covapie_raw_structure_materialization_boundary_audit.csv")
    execution = _csv_rows(ROOT / "covapie_raw_structure_execution_boundary_audit.csv")
    mask = _csv_rows(ROOT / "covapie_raw_structure_mask_scope_audit.csv")
    feature = _csv_rows(ROOT / "covapie_raw_structure_feature_semantics_audit.csv")
    leakage = _csv_rows(ROOT / "covapie_raw_structure_leakage_split_audit.csv")
    assert {row["current_step_status"] for row in materialization} == {"blocked_current_qa_gate"}
    assert {row["materialization_boundary_passed"] for row in materialization} == {"True"}
    by_boundary = {row["boundary_item"]: row["current_step_status"] for row in execution}
    assert by_boundary["raw_structure_event_annotation_qa_gate"] == "executed_readonly_qa_only"
    assert by_boundary["raw_file_presence_check"] == "executed_path_and_git_status_only_no_raw_text_read"
    for item in ["external_network_access", "raw_structure_download", "raw_data_text_read", "rdkit_use", "biopdb_use", "gemmi_use", "torch_import", "model_forward", "training_claim"]:
        assert by_boundary[item] == "not_executed_or_not_allowed"
    assert [row["canonical_mask_task_name"] for row in mask] == qa.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == qa.CANONICAL_MASK_TASK_ALIASES
    assert {row["no_extra_mask_tasks_added"] for row in mask} == {"True"}
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    assert {row["feature_semantics_audit_passed"] for row in feature} == {"True"}
    assert {row["split_written_current_step"] for row in leakage} == {"False"}
    assert {row["leakage_matrix_written_current_step"] for row in leakage} == {"False"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}


def test_no_forbidden_imports_raw_suffix_artifacts_or_raw_git_tracking() -> None:
    module_path = Path("src/covalent_ext/covapie_covpdb_raw_structure_event_annotation_qa_gate.py")
    script_path = Path("scripts/check_covapie_covpdb_raw_structure_event_annotation_qa_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    bad = [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden]
    assert bad == []
    raw_root = Path("data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0")
    tracked = subprocess.run(["git", "ls-files", str(raw_root)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(raw_root)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    manifest = _manifest()
    for key in ["network_access_used", "raw_structure_downloaded", "raw_data_read", "sdf_read", "pdb_read", "mmcif_text_read", "rdkit_used", "biopdb_parser_used", "gemmi_used", "torch_imported", "model_forward_called", "training_allowed"]:
        assert manifest[key] is False
