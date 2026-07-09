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

from covalent_ext import covapie_cys_sg_discovery_download_manifest_gate as gate


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_discovery_download_manifest_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_discovery_download_manifest_gate_manifest.json"
    assert path.is_file(), "Run the Step 14G check script before artifact tests"
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


def test_step14f_precondition_and_zero_proposal_state() -> None:
    manifest14f = json.loads(gate.STEP14F_MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_discovery_precondition_audit.csv")
    manifest = _manifest()
    assert manifest14f["stage"] == gate.PREVIOUS_STAGE
    assert manifest14f["all_checks_passed"] is True
    assert manifest14f["support_proposal_count"] == 0
    assert manifest14f["cys_sg_struct_conn_candidate_count"] == 0
    assert manifest14f["local_raw_read_count"] == 5
    assert manifest14f["ready_for_training"] is False
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert manifest["step14f_zero_support_proposal_reviewed"] is True
    assert manifest["reason_for_strategy_shift"] == "current_top25_has_no_cys_sg_support_from_existing_local_raw"


def test_policy_exception_contract_candidate_audit_and_schema() -> None:
    policy = _csv_rows(ROOT / "covapie_cys_sg_discovery_policy_exception_contract.csv")
    candidates = _csv_rows(ROOT / "covapie_cys_sg_discovery_candidate_source_audit.csv")
    schema = _csv_rows(ROOT / "covapie_cys_sg_discovery_manifest_schema_audit.csv")
    assert len(policy) == 8
    assert [row["policy_item"] for row in policy] == [
        "pdb_id_for_event_identity_still_forbidden",
        "pdb_id_for_raw_evidence_discovery_allowed",
        "discovery_download_not_sample_download",
        "struct_conn_required_for_event_identity",
        "cys_sg_required_for_v1_candidate",
        "manual_review_required_after_discovery",
        "no_ready_candidate_current_step",
        "no_training_or_dataloader_current_step",
    ]
    assert {row["policy_contract_passed"] for row in policy} == {"True"}
    by_policy = {row["policy_item"]: row for row in policy}
    assert by_policy["pdb_id_for_event_identity_still_forbidden"]["allowed_current_step"] == "False"
    assert by_policy["pdb_id_for_raw_evidence_discovery_allowed"]["allowed_current_step"] == "True"
    candidate_rows = [row for row in candidates if row["discovery_candidate_id"].startswith("CYS_SG_DISC_")]
    assert len(candidate_rows) == 25
    assert {row["candidate_source_audit_passed"] for row in candidates} == {"True"}
    assert {row["included_in_discovery_manifest"] for row in candidate_rows} == {"True"}
    assert len(schema) == 22
    assert {row["schema_audit_passed"] for row in schema} == {"True"}


def test_discovery_manifest_csv_json_consistency_and_discovery_only_policy() -> None:
    manifest_csv = _csv_rows(ROOT / "covapie_cys_sg_discovery_download_manifest.csv")
    manifest_json = json.loads((ROOT / "covapie_cys_sg_discovery_download_manifest.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(manifest_csv) == len(manifest_json)
    assert len(manifest_csv) == 25
    assert manifest["discovery_manifest_row_count"] == 25
    assert {row["purpose"] for row in manifest_csv} == {"evidence_discovery_only"}
    assert {row["discovery_download_status"] for row in manifest_csv} == {"pending_not_downloaded"}
    assert {row["retry_count"] for row in manifest_csv} == {"0"}
    assert {row["pdb_only_join_role"] for row in manifest_csv} == {"raw_evidence_fetch_only_not_event_identity"}
    assert {row["event_identity_status"] for row in manifest_csv} == {"unknown_pending_struct_conn_discovery"}
    assert {row["ready_candidate_current_step"] for row in manifest_csv} == {"False"}
    assert {row["ready_for_training_current_step"] for row in manifest_csv} == {"False"}
    assert all(row["raw_output_path"].startswith("data/raw/covalent_sources/covpdb/cys_sg_discovery_raw_v0/") for row in manifest_csv)
    assert manifest["raw_files_written_current_step"] is False
    assert manifest["download_attempted"] is False
    assert manifest["purpose"] == "evidence_discovery_only"
    assert manifest["pdb_id_for_raw_evidence_discovery_allowed"] is True
    assert manifest["pdb_id_for_event_identity_allowed"] is False


def test_stop_readiness_and_runtime_boundaries() -> None:
    stop = _csv_rows(ROOT / "covapie_cys_sg_discovery_stop_condition_contract.csv")
    readiness = _csv_rows(ROOT / "covapie_cys_sg_discovery_readiness_contract.csv")
    manifest = _manifest()
    assert len(stop) == 8
    assert {row["stop_condition_passed"] for row in stop} == {"True"}
    assert len(readiness) == 8
    assert {row["readiness_passed"] for row in readiness} == {"True"}
    by_ready = {row["readiness_item"]: row for row in readiness}
    assert by_ready["ready_for_cys_sg_discovery_download_smoke"]["observed_status"] == "true"
    assert by_ready["ready_for_small_pilot_download_smoke_false"]["observed_status"] == "false"
    for key in [
        "ready_for_covapie_small_pilot_download_smoke",
        "ready_for_covapie_actual_dataloader_adapter_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "network_access_used",
        "download_attempted",
        "raw_files_written_current_step",
        "sample_download_manifest_written",
        "actual_download_smoke_written",
        "final_dataset_written",
        "sample_index_written_current_step",
        "split_assignments_written",
        "leakage_matrix_written",
        "training_artifacts_written",
        "torch_imported",
        "numpy_imported",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "gzip_open_used",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
    ]:
        assert manifest[key] is False, key
    assert manifest["ready_for_covapie_cys_sg_discovery_download_smoke"] is True
    assert manifest["download_manifest_is_discovery_only"] is True
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["recommended_next_step"] == "covapie_cys_sg_discovery_download_smoke"


def test_safety_masks_and_no_forbidden_imports_or_artifacts() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_discovery_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    by_item = {row["safety_item"]: row for row in safety}
    for item in [
        "raw_files_untracked",
        "raw_files_unstaged",
        "no_network_access_current_step",
        "no_download_current_step",
        "no_raw_files_written_current_step",
        "discovery_raw_output_paths_do_not_exist_current_step",
        "metadata_csv_unchanged",
        "step14f_artifacts_unchanged",
        "step14e_artifacts_unchanged",
        "step14d_artifacts_unchanged",
        "step14c_artifacts_unchanged",
        "step14b_artifacts_unchanged",
        "protected_source_diff_empty",
        "original_dataloader_diff_empty",
        "no_torch_numpy_rdkit_biopdb_gemmi_gzip_imports",
        "no_training_artifacts",
        "no_actual_dataloader_artifacts",
        "no_forbidden_binary_or_raw_suffix_in_derived_output",
    ]:
        assert by_item[item]["observed_status"] == "passed"
    assert manifest["canonical_mask_task_names"] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert manifest["canonical_mask_task_aliases"] == ["A", "B", "B2", "B3", "C"]
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    for name in ["torch", "numpy", "urllib", "requests", "rdkit", "Bio", "gemmi", "gzip"]:
        assert not _imports_name(Path("src/covalent_ext/covapie_cys_sg_discovery_download_manifest_gate.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_cys_sg_discovery_download_manifest_gate_v0.py"), name)
    assert not subprocess.run(["git", "ls-files", gate.RAW_STORAGE_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert not subprocess.run(["git", "ls-files", gate.DISCOVERY_RAW_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
