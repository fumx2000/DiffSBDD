from __future__ import annotations

import ast
import csv
import json
from pathlib import Path


ROOT = Path("data/derived/covalent_small/covapie_covpdb_raw_structure_event_annotation_design_gate_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_raw_structure_event_annotation_design_gate_manifest.json"
    assert path.is_file(), "Run the Step 13AU check script before artifact tests"
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


def test_step13at_precondition_and_first5_metadata() -> None:
    manifest = _manifest()
    pre = _csv_rows(ROOT / "covapie_raw_structure_event_annotation_precondition_audit.csv")
    assert manifest["stage"] == "covapie_covpdb_raw_structure_event_annotation_design_gate_v0"
    assert manifest["previous_stage"] == "covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0"
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13at_acquisition_qa_gate_validated"] is True
    assert {row["precondition_passed"] for row in pre} == {"True"}
    assert manifest["first5_pdb_id_count"] == 5
    assert manifest["first5_ligand_het_code_count"] == 5
    assert manifest["first5_pdb_ids"] == ["1A3B", "1A3E", "1A46", "1A54", "1A5G"]
    assert manifest["first5_ligand_het_codes"] == ["T29", "T16", "00K", "MDC", "00L"]


def test_raw_download_scope_and_source_url_contracts() -> None:
    manifest = _manifest()
    scope = _csv_rows(ROOT / "covapie_raw_structure_download_scope_contract.csv")
    urls = _csv_rows(ROOT / "covapie_raw_structure_source_url_contract.csv")
    assert len(scope) == 5
    assert {row["allowed_for_next_smoke"] for row in scope} == {"True"}
    assert {row["preferred_format"] for row in scope} == {"mmcif"}
    assert {row["fallback_format"] for row in scope} == {"pdb"}
    assert {row["max_structure_count"] for row in scope} == {"5"}
    assert {row["ligand_sdf_allowed"] for row in scope} == {"False"}
    assert {row["archive_download_allowed"] for row in scope} == {"False"}
    assert {row["download_scope_contract_passed"] for row in scope} == {"True"}
    assert len(urls) == 10
    assert {row["source_domain"] for row in urls} == {"files.rcsb.org"}
    assert {row["accessed_current_step"] for row in urls} == {"False"}
    assert {row["source_url_contract_passed"] for row in urls} == {"True"}
    assert manifest["preferred_raw_format"] == "mmcif"
    assert manifest["fallback_raw_format"] == "pdb"
    assert manifest["network_access_used"] is False


def test_raw_storage_contract_keeps_files_untracked() -> None:
    manifest = _manifest()
    storage = _csv_rows(ROOT / "covapie_raw_structure_storage_contract.csv")
    by_item = {row["storage_contract_item"]: row for row in storage}
    assert by_item["raw_storage_root"]["contract_value"] == "data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0/"
    assert {row["raw_files_must_remain_untracked"] for row in storage} == {"True"}
    assert {row["git_add_allowed"] for row in storage} == {"False"}
    assert {row["git_commit_allowed"] for row in storage} == {"False"}
    assert manifest["raw_storage_root"] == by_item["raw_storage_root"]["contract_value"]
    assert manifest["raw_file_created"] is False
    assert manifest["raw_structure_downloaded"] is False


def test_parser_priority_contract() -> None:
    parser = _csv_rows(ROOT / "covapie_raw_structure_parser_priority_contract.csv")
    assert [row["parser_source"] for row in parser] == [
        "mmcif_struct_conn",
        "mmcif_atom_site",
        "pdb_link",
        "pdb_conect",
        "coordinate_distance_fallback",
    ]
    assert parser[0]["parser_priority"] == "1"
    assert parser[0]["allowed_in_first_raw_annotation_smoke"] == "True"
    assert parser[4]["allowed_in_first_raw_annotation_smoke"] == "False"
    assert parser[4]["contract_status"] == "not_allowed_first_smoke"
    assert {row["parser_priority_contract_passed"] for row in parser} == {"True"}


def test_mmcif_and_pdb_mapping_contracts() -> None:
    mmcif = _csv_rows(ROOT / "covapie_mmcif_struct_conn_field_mapping_contract.csv")
    pdb = _csv_rows(ROOT / "covapie_pdb_link_record_field_mapping_contract.csv")
    mmcif_fields = {(row["source_category"], row["source_field"]) for row in mmcif}
    pdb_fields = {(row["source_category"], row["source_field"]) for row in pdb}
    assert ("struct_conn", "conn_type_id") in mmcif_fields
    assert ("struct_conn", "ptnr1_label_atom_id") in mmcif_fields
    assert ("struct_conn", "ptnr2_auth_seq_id") in mmcif_fields
    assert ("atom_site", "Cartn_x") in mmcif_fields
    assert ("atom_site", "Cartn_y") in mmcif_fields
    assert ("atom_site", "Cartn_z") in mmcif_fields
    assert {row["source_format"] for row in mmcif} == {"mmcif"}
    assert {row["mapping_contract_passed"] for row in mmcif} == {"True"}
    assert ("LINK", "atomName1") in pdb_fields
    assert ("LINK", "resName2") in pdb_fields
    assert ("LINK", "chainID2") in pdb_fields
    assert ("ATOM/HETATM", "serial") in pdb_fields
    assert ("ATOM/HETATM", "x/y/z") in pdb_fields
    assert {row["source_format"] for row in pdb} == {"pdb"}
    assert {row["mapping_contract_passed"] for row in pdb} == {"True"}


def test_event_key_resolution_and_materialization_boundaries() -> None:
    manifest = _manifest()
    event = _csv_rows(ROOT / "covapie_raw_structure_event_key_resolution_contract.csv")
    materialization = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_raw_structure_materialization_boundary_audit.csv")}
    statuses = [row["resolution_status"] for row in event]
    assert "raw_resolves_preferred_event_key" in statuses
    assert "raw_resolves_minimal_event_key" in statuses
    assert "raw_multiple_candidate_links" in statuses
    assert "raw_no_connectivity_records_found" in statuses
    assert {row["candidate_metadata_can_materialize"] for row in event} == {"False"}
    assert {row["allowlist_can_materialize"] for row in event} == {"False"}
    assert materialization["candidate_metadata_materialization"]["current_step_status"] == "blocked_current_design_gate"
    assert materialization["candidate_allowlist_materialization"]["current_step_status"] == "blocked_current_design_gate"
    assert materialization["raw_structure_download"]["current_step_status"] == "blocked_current_design_gate"
    assert materialization["training"]["current_step_status"] == "blocked_current_design_gate"
    assert manifest["candidate_metadata_materialized"] is False
    assert manifest["candidate_allowlist_materialized"] is False
    assert manifest["ready_for_covapie_covpdb_raw_structure_event_annotation_smoke"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["recommended_next_step"] == "covapie_covpdb_raw_structure_event_annotation_smoke"


def test_no_network_raw_or_forbidden_imports_and_masks() -> None:
    manifest = _manifest()
    module_path = Path("src/covalent_ext/covapie_covpdb_raw_structure_event_annotation_design_gate.py")
    script_path = Path("scripts/check_covapie_covpdb_raw_structure_event_annotation_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    execution = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_raw_structure_execution_boundary_audit.csv")}
    assert execution["external_network_access"]["current_step_status"] == "not_executed_or_not_allowed"
    assert execution["raw_structure_download"]["current_step_status"] == "not_executed_or_not_allowed"
    assert execution["raw_file_created"]["current_step_status"] == "not_executed_or_not_allowed"
    assert execution["mmcif_read"]["current_step_status"] == "not_executed_or_not_allowed"
    assert manifest["raw_download_executed"] is False
    assert manifest["raw_data_read"] is False
    assert manifest["network_access_used"] is False
    mask = _csv_rows(ROOT / "covapie_raw_structure_mask_scope_audit.csv")
    assert [row["canonical_mask_task_name"] for row in mask] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert [row["display_alias"] for row in mask] == ["A", "B", "B2", "B3", "C"]
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True


def test_feature_semantics_and_leakage_split_remain_training_blockers() -> None:
    manifest = _manifest()
    feature = _csv_rows(ROOT / "covapie_raw_structure_feature_semantics_audit.csv")
    leakage = _csv_rows(ROOT / "covapie_raw_structure_leakage_split_audit.csv")
    assert len(feature) == 12
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    assert len(leakage) == 12
    assert {row["split_written_current_step"] for row in leakage} == {"False"}
    assert {row["leakage_matrix_written_current_step"] for row in leakage} == {"False"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True

