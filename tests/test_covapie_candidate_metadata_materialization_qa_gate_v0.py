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

from covalent_ext import covapie_candidate_metadata_materialization_qa_gate as qa_gate


ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_qa_gate_v0")
SMOKE_ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_candidate_metadata_materialization_qa_gate_manifest.json"
    assert path.is_file(), "Run the Step 13AZ check script before artifact tests"
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


def test_step13ay_precondition_and_readiness() -> None:
    manifest13ay = json.loads(qa_gate.STEP13AY_MANIFEST_JSON.read_text(encoding="utf-8"))
    manifest = _manifest()
    assert manifest13ay["stage"] == qa_gate.PREVIOUS_STAGE
    assert manifest13ay["all_checks_passed"] is True
    assert manifest13ay["candidate_metadata_materialized"] is True
    assert manifest13ay["candidate_allowlist_materialized"] is False
    assert manifest13ay["ready_for_covapie_candidate_metadata_materialization_qa_gate"] is True
    assert manifest["stage"] == qa_gate.STAGE
    assert manifest["previous_stage"] == qa_gate.PREVIOUS_STAGE
    assert manifest["step13ay_candidate_metadata_materialization_smoke_validated"] is True
    assert manifest["candidate_metadata_materialized_previous_step"] is True
    assert manifest["candidate_metadata_materialized_current_step"] is False
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_candidate_metadata_smoke_csv_json_and_content_integrity() -> None:
    smoke_rows = _csv_rows(SMOKE_ROOT / "covapie_candidate_metadata_smoke.csv")
    json_rows = json.loads((SMOKE_ROOT / "covapie_candidate_metadata_smoke.json").read_text(encoding="utf-8"))
    content = _csv_rows(ROOT / "covapie_candidate_metadata_qa_gate_content_integrity.csv")
    manifest = _manifest()
    assert len(smoke_rows) == 4
    assert len(smoke_rows[0]) == 33
    assert len(json_rows) == 4
    assert len(content) == 4
    expected_ids = [
        "covpdb::1A3B::T29::H:SER195:OG-B",
        "covpdb::1A3E::T16::H:SER195:OG-B",
        "covpdb::1A46::00K::H:SER195:OG-C",
        "covpdb::1A5G::00L::H:SER195:OG-C",
    ]
    assert [row["candidate_metadata_id"] for row in smoke_rows] == expected_ids
    assert [row["candidate_metadata_id"] for row in json_rows] == expected_ids
    assert [row["candidate_metadata_id"] for row in content] == expected_ids
    assert [(row["pdb_id"], row["het_code"]) for row in smoke_rows] == [
        ("1A3B", "T29"),
        ("1A3E", "T16"),
        ("1A46", "00K"),
        ("1A5G", "00L"),
    ]
    for key in [
        "schema_column_order_matches",
        "id_matches_expected",
        "pair_is_allowed",
        "pair_is_not_unresolved",
        "required_boolean_fields_valid",
        "training_ready_false",
        "content_integrity_passed",
    ]:
        assert {row[key] for row in content} == {"True"}
    assert {row["column_count"] for row in content} == {"33"}
    assert manifest["qa_candidate_metadata_row_count"] == 4
    assert manifest["qa_candidate_metadata_column_count"] == 33
    assert manifest["qa_candidate_metadata_id_count"] == 4
    assert manifest["qa_candidate_metadata_id_unique_count"] == 4
    assert manifest["qa_candidate_metadata_id_matches_expected_count"] == 4
    assert manifest["qa_content_integrity_passed"] is True


def test_traceability_and_unresolved_exclusion() -> None:
    trace = _csv_rows(ROOT / "covapie_candidate_metadata_qa_gate_traceability.csv")
    unresolved = _csv_rows(ROOT / "covapie_candidate_metadata_qa_gate_unresolved_exclusion.csv")
    manifest = _manifest()
    assert len(trace) == 4
    for key in [
        "source_step13ay_traceability_passed",
        "source_step13ax_accepted_event_found",
        "source_step13aw_preferred_event_found",
        "source_metadata_csv_row_found",
        "traceability_qa_passed",
    ]:
        assert {row[key] for row in trace} == {"True"}
    assert all(row["source_metadata_csv_row_key"].startswith("CovPDB::covpdb_web_metadata_smoke_2026-07-06::") for row in trace)
    assert unresolved == [
        {
            "pdb_id": "1A54",
            "het_code": "MDC",
            "resolution_status": "raw_no_connectivity_records_found",
            "reason_unresolved": "raw_no_connectivity_records_found",
            "present_in_candidate_metadata": "False",
            "candidate_metadata_materialized": "False",
            "candidate_allowlist_materialized": "False",
            "exclusion_preserved": "True",
            "unresolved_exclusion_qa_passed": "True",
            "qa_comment": "unresolved_case_remains_blocked",
        }
    ]
    assert manifest["qa_traceability_passed"] is True
    assert manifest["qa_unresolved_exclusion_preserved"] is True


def test_boundary_safety_git_safety_and_training_blockers() -> None:
    boundary = _csv_rows(ROOT / "covapie_candidate_metadata_qa_gate_boundary_safety.csv")
    git_safety = _csv_rows(ROOT / "covapie_candidate_metadata_qa_gate_git_safety.csv")
    blockers = _csv_rows(ROOT / "covapie_candidate_metadata_qa_gate_training_blockers.csv")
    manifest = _manifest()
    by_boundary = {row["boundary_item"]: row for row in boundary}
    assert by_boundary["candidate_metadata_materialization"]["current_step_status"] == "qa_only_existing_first4_metadata"
    assert by_boundary["candidate_allowlist_materialization"]["current_step_status"] == "blocked_until_candidate_metadata_qa_gate_passed"
    for item in ["sample_index", "final_dataset", "split_assignments", "leakage_matrix", "training"]:
        assert by_boundary[item]["current_step_status"] == "blocked_current_qa_gate"
    for item in ["network_access", "raw_download", "raw_text_read", "rdkit_biopdb_gemmi", "torch_model_training"]:
        assert by_boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["boundary_safety_passed"] for row in boundary} == {"True"}
    assert {row["git_safety_audit_passed"] for row in git_safety} == {"True"}
    assert {row["training_blocker_passed"] for row in blockers} == {"True"}
    assert [row["training_blocker_item"] for row in blockers[:5]] == [
        "mask_warhead_only_A",
        "mask_linker_plus_warhead_B",
        "mask_scaffold_plus_warhead_B2",
        "mask_scaffold_only_B3",
        "mask_scaffold_plus_linker_plus_warhead_C",
    ]
    assert manifest["qa_boundary_safety_passed"] is True
    assert manifest["qa_git_safety_passed"] is True
    assert manifest["qa_training_blockers_passed"] is True
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True


def test_readiness_boundary_not_training_or_allowlist_smoke() -> None:
    manifest = _manifest()
    assert manifest["candidate_allowlist_materialized"] is False
    assert manifest["sample_index_written"] is False
    assert manifest["final_dataset_written"] is False
    assert manifest["split_assignments_written"] is False
    assert manifest["leakage_matrix_written"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_design_gate"] is True
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_candidate_allowlist_materialization_design_gate"


def test_no_forbidden_imports_outputs_or_raw_tracking() -> None:
    module_path = Path("src/covalent_ext/covapie_candidate_metadata_materialization_qa_gate.py")
    script_path = Path("scripts/check_covapie_candidate_metadata_materialization_qa_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    bad = [path for path in ROOT.rglob("*") if path.is_file() and path.suffix.lower() in forbidden]
    assert bad == []
    forbidden_names = {
        "covapie_candidate_allowlist.csv",
        "covapie_candidate_allowlist.json",
        "sample_index.csv",
        "sample_index.json",
        "final_dataset.csv",
        "final_dataset.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
    }
    assert not any(path.name in forbidden_names for path in ROOT.rglob("*"))
    raw_root = Path("data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0")
    tracked = subprocess.run(["git", "ls-files", str(raw_root)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(raw_root)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip().splitlines()
    assert tracked == []
    assert staged == []
    manifest = _manifest()
    for key in [
        "network_access_used",
        "urllib_used",
        "requests_used",
        "browser_used",
        "raw_structure_downloaded",
        "raw_ligand_downloaded",
        "archive_downloaded",
        "raw_file_created",
        "raw_data_read",
        "sdf_read",
        "pdb_read",
        "mmcif_text_read",
        "gzip_open_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "torch_imported",
        "torch_tensor_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
    ]:
        assert manifest[key] is False
