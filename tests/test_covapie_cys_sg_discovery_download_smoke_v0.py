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

from covalent_ext import covapie_cys_sg_discovery_download_smoke as smoke


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_discovery_download_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_discovery_download_smoke_manifest.json"
    assert path.is_file(), "Run the Step 14H check script before artifact tests"
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


def test_step14g_precondition_and_download_execution() -> None:
    manifest14g = json.loads(smoke.STEP14G_MANIFEST_JSON.read_text(encoding="utf-8"))
    precondition = _csv_rows(ROOT / "covapie_cys_sg_discovery_download_precondition_audit.csv")
    execution = _csv_rows(ROOT / "covapie_cys_sg_discovery_download_execution_audit.csv")
    manifest = _manifest()
    assert manifest14g["stage"] == smoke.PREVIOUS_STAGE
    assert manifest14g["all_checks_passed"] is True
    assert manifest14g["discovery_manifest_row_count"] == 25
    assert manifest14g["ready_for_covapie_cys_sg_discovery_download_smoke"] is True
    assert {row["precondition_passed"] for row in precondition} == {"True"}
    assert len(execution) == 25
    assert {row["execution_audit_passed"] for row in execution} == {"True"}
    assert manifest["discovery_manifest_row_count"] == 25
    assert manifest["network_access_used"] is True
    assert manifest["download_attempted"] is True
    assert manifest["download_success_count"] + manifest["download_failure_count"] == 25


def test_raw_files_downloaded_under_allowed_root_and_untracked() -> None:
    execution = _csv_rows(ROOT / "covapie_cys_sg_discovery_download_execution_audit.csv")
    manifest = _manifest()
    for row in execution:
        assert row["raw_output_path"].startswith(smoke.RAW_OUTPUT_ROOT.as_posix() + "/")
        assert row["raw_file_tracked_by_git"] == "False"
        assert row["raw_file_staged_by_git"] == "False"
        assert row["temp_file_cleaned"] == "True"
        if row["raw_file_exists_after_download"] == "True":
            assert int(row["raw_file_size_bytes"]) > 0
            assert row["raw_file_sha256"]
    assert manifest["raw_files_tracked"] is False
    assert manifest["raw_files_staged"] is False
    assert manifest["temp_part_files_remaining_count"] == 0
    assert not subprocess.run(["git", "ls-files", smoke.RAW_OUTPUT_ROOT.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()


def test_download_status_manifest_struct_conn_and_proposals_consistency() -> None:
    status_csv = _csv_rows(ROOT / "covapie_cys_sg_discovery_download_status_manifest.csv")
    status_json = json.loads((ROOT / "covapie_cys_sg_discovery_download_status_manifest.json").read_text(encoding="utf-8"))
    struct_conn = _csv_rows(ROOT / "covapie_cys_sg_struct_conn_discovery_audit.csv")
    proposals_csv = _csv_rows(ROOT / "covapie_cys_sg_discovery_event_proposals.csv")
    proposals_json = json.loads((ROOT / "covapie_cys_sg_discovery_event_proposals.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(status_csv) == len(status_json) == 25
    assert {row["ready_candidate_current_step"] for row in status_csv} == {"False"}
    assert {row["ready_for_training_current_step"] for row in status_csv} == {"False"}
    assert {row["discovery_audit_passed"] for row in struct_conn} == {"True"}
    assert len(proposals_csv) == len(proposals_json) == manifest["support_proposal_count"]
    assert manifest["support_proposals_csv_json_consistent"] is True
    assert {row["proposal_status"] for row in proposals_csv}.issubset({"pending_manual_review"})
    assert {row["manual_review_status"] for row in proposals_csv}.issubset({"pending_manual_review"})
    for row in proposals_csv:
        assert row["suggested_residue_name"] == "CYS"
        assert row["suggested_residue_atom_name"] == "SG"
        assert row["ready_candidate_current_step"] == "False"


def test_readiness_next_step_and_training_boundaries() -> None:
    readiness = _csv_rows(ROOT / "covapie_cys_sg_discovery_stop_decision_readiness_audit.csv")
    manifest = _manifest()
    assert len(readiness) == 10
    assert {row["readiness_passed"] for row in readiness} == {"True"}
    if manifest["support_proposal_count"] > 0:
        assert manifest["ready_for_covapie_cys_sg_discovery_support_review_gate"] is True
        assert manifest["recommended_next_step"] == "covapie_cys_sg_discovery_support_review_gate"
    else:
        assert manifest["ready_for_covapie_cys_sg_targeted_metadata_expansion_gate"] is True
        assert manifest["recommended_next_step"] == "covapie_cys_sg_targeted_metadata_expansion_gate"
    for key in [
        "ready_for_covapie_small_pilot_download_smoke",
        "ready_for_covapie_actual_dataloader_adapter_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "pdb_id_used_as_event_identity",
        "sample_download_manifest_written",
        "actual_download_smoke_for_sample",
        "actual_dataloader_adapter_smoke_written",
        "actual_dataloader_smoke_written",
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
    assert manifest["ready_candidate_count_current_step"] == 0
    assert manifest["no_ready_candidates_created"] is True


def test_safety_masks_no_forbidden_artifacts_or_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_discovery_download_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    by_item = {row["safety_item"]: row for row in safety}
    for item in [
        "raw_files_untracked",
        "raw_files_unstaged",
        "temp_part_files_cleaned_or_reported",
        "metadata_csv_unchanged",
        "step14g_artifacts_unchanged",
        "step14f_artifacts_unchanged",
        "step14e_artifacts_unchanged",
        "protected_source_diff_empty",
        "original_dataloader_diff_empty",
        "no_sample_download_manifest_written",
        "no_actual_dataloader_artifacts",
        "no_training_artifacts",
        "no_final_dataset_written",
        "no_sample_index_written",
        "no_split_assignments_written",
        "no_leakage_matrix_written",
        "no_torch_numpy_rdkit_biopdb_gemmi_gzip_imports",
        "derived_output_no_forbidden_binary_or_raw_suffix",
        "raw_output_only_under_allowed_raw_root",
        "pdb_id_not_used_as_event_identity",
    ]:
        assert by_item[item]["observed_status"] == "passed"
    assert by_item["network_access_used_current_step"]["observed_status"] == "true"
    assert by_item["download_attempted_current_step"]["observed_status"] == "true"
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
    for name in ["torch", "numpy", "requests", "rdkit", "Bio", "gemmi", "gzip"]:
        assert not _imports_name(Path("src/covalent_ext/covapie_cys_sg_discovery_download_smoke.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_cys_sg_discovery_download_smoke_v0.py"), name)
