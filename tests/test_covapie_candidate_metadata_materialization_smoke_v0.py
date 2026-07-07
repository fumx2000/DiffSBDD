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

from covalent_ext import covapie_candidate_metadata_materialization_smoke as smoke


ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_smoke_v0")
DESIGN_ROOT = Path("data/derived/covalent_small/covapie_candidate_metadata_materialization_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_candidate_metadata_materialization_smoke_manifest.json"
    assert path.is_file(), "Run the Step 13AY check script before artifact tests"
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


def test_step13ax_precondition_and_manifest_readiness() -> None:
    manifest13ax = json.loads(smoke.STEP13AX_MANIFEST_JSON.read_text(encoding="utf-8"))
    manifest = _manifest()
    assert manifest13ax["stage"] == smoke.PREVIOUS_STAGE
    assert manifest13ax["all_checks_passed"] is True
    assert manifest13ax["ready_for_covapie_candidate_metadata_materialization_smoke"] is True
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13ax_candidate_metadata_materialization_design_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []


def test_candidate_metadata_smoke_csv_and_json_have_four_schema_compliant_rows() -> None:
    metadata_rows = _csv_rows(ROOT / "covapie_candidate_metadata_smoke.csv")
    schema_rows = _csv_rows(DESIGN_ROOT / "covapie_candidate_metadata_schema_contract.csv")
    json_rows = json.loads((ROOT / "covapie_candidate_metadata_smoke.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    expected_columns = [row["candidate_metadata_field"] for row in schema_rows]
    assert len(metadata_rows) == 4
    assert len(json_rows) == 4
    assert list(metadata_rows[0].keys()) == expected_columns
    assert expected_columns == smoke.CANDIDATE_METADATA_FIELDS
    assert len(expected_columns) == 33
    assert manifest["materialized_candidate_metadata_row_count"] == 4
    assert manifest["materialized_candidate_metadata_column_count"] == 33
    assert manifest["candidate_metadata_csv_written"] is True
    assert manifest["candidate_metadata_json_written"] is True


def test_candidate_metadata_ids_and_event_pairs_match_design_previews() -> None:
    rows = _csv_rows(ROOT / "covapie_candidate_metadata_smoke.csv")
    expected_ids = [
        "covpdb::1A3B::T29::H:SER195:OG-B",
        "covpdb::1A3E::T16::H:SER195:OG-B",
        "covpdb::1A46::00K::H:SER195:OG-C",
        "covpdb::1A5G::00L::H:SER195:OG-C",
    ]
    assert [row["candidate_metadata_id"] for row in rows] == expected_ids
    assert len(expected_ids) == len(set(expected_ids))
    assert all(not any(char.isspace() for char in candidate_id) for candidate_id in expected_ids)
    assert [(row["pdb_id"], row["het_code"]) for row in rows] == [
        ("1A3B", "T29"),
        ("1A3E", "T16"),
        ("1A46", "00K"),
        ("1A5G", "00L"),
    ]
    for row in rows:
        assert row["project_name"] == "CovaPIE"
        assert row["source_name"] == "covpdb"
        assert row["source_database"] == "CovPDB"
        assert row["source_stage"] == smoke.STAGE
        assert row["selected_raw_format"] == "mmcif"
        assert row["raw_connection_source"] == "mmcif_struct_conn"
        assert row["event_key_resolution_status"] == "raw_resolves_preferred_event_key"
        assert row["accepted_for_future_candidate_metadata"].lower() == "true"
        assert row["accepted_for_future_automatic_allowlist"].lower() == "true"
        assert row["current_step_materialization_allowed"].lower() == "true"
        assert row["manual_review_required"].lower() == "false"
        assert row["feature_semantics_audit_required_before_training"].lower() == "true"
        assert row["leakage_split_design_required_before_training"].lower() == "true"
        assert row["ready_for_training"].lower() == "false"


def test_all_fields_complete_and_source_traceability_passes() -> None:
    metadata_rows = _csv_rows(ROOT / "covapie_candidate_metadata_smoke.csv")
    completeness = _csv_rows(ROOT / "covapie_candidate_metadata_field_completeness_audit.csv")
    traceability = _csv_rows(ROOT / "covapie_candidate_metadata_source_traceability_audit.csv")
    assert all(value != "" for row in metadata_rows for value in row.values())
    assert len(completeness) == 33
    assert {row["non_empty_count"] for row in completeness} == {"4"}
    assert {row["expected_row_count"] for row in completeness} == {"4"}
    assert {row["field_completeness_status"] for row in completeness} == {"complete"}
    assert {row["field_completeness_audit_passed"] for row in completeness} == {"True"}
    assert len(traceability) == 4
    for key in [
        "source_step13ax_accepted_event_inventory_found",
        "source_step13aw_preferred_acceptance_found",
        "source_step13aw_candidate_integrity_found",
        "source_metadata_csv_row_found",
        "traceability_audit_passed",
    ]:
        assert {row[key] for row in traceability} == {"True"}
    assert all(row["source_metadata_csv_row_key"].startswith("CovPDB::covpdb_web_metadata_smoke_2026-07-06::") for row in traceability)


def test_unresolved_event_excluded_and_validation_audits_pass() -> None:
    metadata_rows = _csv_rows(ROOT / "covapie_candidate_metadata_smoke.csv")
    unresolved = _csv_rows(ROOT / "covapie_candidate_metadata_unresolved_event_exclusion_audit.csv")
    accepted = _csv_rows(ROOT / "covapie_candidate_metadata_accepted_event_materialization_audit.csv")
    schema = _csv_rows(ROOT / "covapie_candidate_metadata_schema_compliance_audit.csv")
    identity = _csv_rows(ROOT / "covapie_candidate_metadata_row_identity_uniqueness_audit.csv")
    validation = _csv_rows(ROOT / "covapie_candidate_metadata_validation_audit.csv")
    assert ("1A54", "MDC") not in {(row["pdb_id"], row["het_code"]) for row in metadata_rows}
    assert unresolved == [
        {
            "pdb_id": "1A54",
            "het_code": "MDC",
            "resolution_status": "raw_no_connectivity_records_found",
            "reason_unresolved": "raw_no_connectivity_records_found",
            "candidate_metadata_materialized": "False",
            "candidate_allowlist_materialized": "False",
            "exclusion_preserved": "True",
            "unresolved_event_exclusion_audit_passed": "True",
        }
    ]
    assert len(accepted) == 4
    assert {row["materialized"] for row in accepted} == {"True"}
    assert {row["id_matches_design_preview"] for row in accepted} == {"True"}
    assert {row["accepted_event_materialization_audit_passed"] for row in accepted} == {"True"}
    assert {row["schema_compliance_audit_passed"] for row in schema} == {"True"}
    assert {row["row_identity_uniqueness_audit_passed"] for row in identity} == {"True"}
    assert {row["validation_audit_passed"] for row in validation} == {"True"}


def test_boundaries_masks_feature_semantics_leakage_and_manifest() -> None:
    allowlist = _csv_rows(ROOT / "covapie_candidate_allowlist_boundary_audit.csv")
    materialization = _csv_rows(ROOT / "covapie_candidate_metadata_materialization_boundary_audit.csv")
    execution = _csv_rows(ROOT / "covapie_candidate_metadata_execution_boundary_audit.csv")
    mask = _csv_rows(ROOT / "covapie_candidate_metadata_mask_scope_audit.csv")
    feature = _csv_rows(ROOT / "covapie_candidate_metadata_feature_semantics_audit.csv")
    leakage = _csv_rows(ROOT / "covapie_candidate_metadata_leakage_split_audit.csv")
    manifest = _manifest()
    assert allowlist == [
        {
            "boundary_item": "candidate_allowlist_materialization",
            "automatic_allowlist_possible_count": "4",
            "candidate_metadata_rows_available": "4",
            "current_step_allowed": "False",
            "future_condition": "candidate_metadata_materialization_qa_gate_passed",
            "candidate_allowlist_boundary_passed": "True",
        }
    ]
    by_materialization = {row["boundary_item"]: row["current_step_status"] for row in materialization}
    assert by_materialization["candidate_metadata_materialization"] == "executed_first4_smoke_only"
    for item in ["candidate_allowlist_materialization", "sample_index", "final_dataset", "split_assignments", "leakage_matrix", "training"]:
        assert by_materialization[item] == "blocked_current_smoke"
    by_execution = {row["boundary_item"]: row["current_step_status"] for row in execution}
    assert by_execution["candidate_metadata_materialization_smoke"] == "executed_first4_candidate_metadata_only"
    assert by_execution["candidate_metadata_csv_write"] == "executed_first4_rows_only"
    assert by_execution["candidate_metadata_json_write"] == "executed_first4_rows_only"
    for item in ["candidate_allowlist_write", "external_network_access", "raw_structure_download", "raw_data_text_read", "rdkit_use", "biopdb_use", "gemmi_use", "torch_import", "model_forward", "training_claim"]:
        assert by_execution[item] == "not_executed_or_not_allowed"
    assert [row["canonical_mask_task_name"] for row in mask] == smoke.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    assert {row["feature_semantics_audit_passed"] for row in feature} == {"True"}
    assert {row["split_written_current_step"] for row in leakage} == {"False"}
    assert {row["leakage_matrix_written_current_step"] for row in leakage} == {"False"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}
    assert manifest["candidate_metadata_materialized"] is True
    assert manifest["candidate_allowlist_materialized"] is False
    assert manifest["sample_index_written"] is False
    assert manifest["final_dataset_written"] is False
    assert manifest["split_assignments_written"] is False
    assert manifest["leakage_matrix_written"] is False
    assert manifest["ready_for_covapie_candidate_metadata_materialization_qa_gate"] is True
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_candidate_metadata_materialization_qa_gate"


def test_no_forbidden_imports_outputs_or_raw_tracking() -> None:
    module_path = Path("src/covalent_ext/covapie_candidate_metadata_materialization_smoke.py")
    script_path = Path("scripts/check_covapie_candidate_metadata_materialization_smoke_v0.py")
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
