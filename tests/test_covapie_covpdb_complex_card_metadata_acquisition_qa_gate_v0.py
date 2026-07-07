from __future__ import annotations

import ast
import csv
import json
from pathlib import Path


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = Path("data/derived/covalent_small/covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0/covapie_covpdb_complex_card_metadata_acquisition_qa_gate_manifest.json")
    assert path.is_file(), "Run the Step 13AT QA check script before artifact tests"
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


ROOT = Path("data/derived/covalent_small/covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0")


def test_step13as_precondition_and_fetch_integrity_qa() -> None:
    manifest = _manifest()
    pre = _csv_rows(ROOT / "covapie_covpdb_complex_card_acquisition_qa_precondition_audit.csv")
    fetch = _csv_rows(ROOT / "covapie_covpdb_complex_card_fetch_integrity_qa.csv")
    assert manifest["stage"] == "covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0"
    assert manifest["previous_stage"] == "covapie_covpdb_complex_card_metadata_acquisition_smoke_v0"
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13as_acquisition_smoke_validated"] is True
    assert {row["precondition_passed"] for row in pre} == {"True"}
    assert len(fetch) == 5
    assert {row["fetch_attempted"] for row in fetch} == {"True"}
    assert {row["fetch_succeeded"] for row in fetch} == {"True"}
    assert {row["byte_count_positive"] for row in fetch} == {"True"}
    assert {row["html_sha256_present"] for row in fetch} == {"True"}
    assert {row["url_allowed"] for row in fetch} == {"True"}
    assert {row["fetch_integrity_passed"] for row in fetch} == {"True"}


def test_html_safety_qa_proves_no_html_or_raw_downloads() -> None:
    manifest = _manifest()
    safety = _csv_rows(ROOT / "covapie_covpdb_complex_card_html_safety_qa.csv")
    assert len(safety) == 5
    assert {row["content_type_allowed"] for row in safety} == {"True"}
    assert {row["full_html_written"] for row in safety} == {"False"}
    assert {row["raw_html_artifact_written"] for row in safety} == {"False"}
    assert {row["forbidden_suffix_links_followed"] for row in safety} == {"False"}
    assert {row["external_raw_links_followed"] for row in safety} == {"False"}
    assert {row["raw_structure_downloaded"] for row in safety} == {"False"}
    assert {row["raw_ligand_downloaded"] for row in safety} == {"False"}
    assert {row["html_safety_qa_passed"] for row in safety} == {"True"}
    assert manifest["network_access_used"] is False
    assert manifest["urllib_used"] is False
    assert manifest["raw_structure_downloaded"] is False
    assert manifest["raw_ligand_downloaded"] is False


def test_label_inventory_and_event_field_summaries() -> None:
    labels = _csv_rows(ROOT / "covapie_covpdb_complex_card_label_inventory_summary_qa.csv")
    fields = _csv_rows(ROOT / "covapie_covpdb_complex_card_event_field_status_summary_qa.csv")
    assert [row["label_category"] for row in labels] == [
        "chain",
        "residue",
        "residue_name",
        "residue_index",
        "residue_atom",
        "covalent_bond",
        "ligand_atom",
        "protein_atom",
        "mechanism",
        "warhead",
    ]
    assert {row["cards_checked"] for row in labels} == {"5"}
    assert {row["label_inventory_summary_passed"] for row in labels} == {"True"}
    assert {row["qa_interpretation"] for row in labels} == {"labels_are_weak_evidence_not_event_field_resolution"}
    assert [row["target_field"] for row in fields] == [
        "chain_id",
        "residue_name",
        "residue_index",
        "residue_atom_name",
        "covalent_bond_atom_pair",
    ]
    assert {row["found_count"] for row in fields} == {"0"}
    assert {row["not_found_count"] for row in fields} == {"5"}
    assert {row["ambiguous_count"] for row in fields} == {"0"}
    assert {row["event_field_status_summary_passed"] for row in fields} == {"True"}
    assert {row["qa_interpretation"] for row in fields} == {"complex_card_text_fetch_succeeded_but_event_key_fields_not_explicitly_parsed"}


def test_event_key_resolution_and_unresolved_reason_qa() -> None:
    manifest = _manifest()
    summary = _csv_rows(ROOT / "covapie_covpdb_complex_card_event_key_resolution_summary_qa.csv")
    unresolved = _csv_rows(ROOT / "covapie_covpdb_complex_card_unresolved_reason_qa.csv")
    assert summary == [
        {
            "resolution_status": "card_no_event_key_fields_found",
            "observed_count": "5",
            "candidate_metadata_can_proceed_any": "False",
            "candidate_allowlist_can_proceed_any": "False",
            "raw_structure_annotation_may_be_required_any": "True",
            "event_key_resolution_summary_passed": "True",
            "qa_interpretation": "event_key_unresolved_candidate_metadata_and_allowlist_blocked",
        }
    ]
    assert len(unresolved) == 5
    assert {row["why_candidate_metadata_blocked"] for row in unresolved} == {"minimal_event_key_not_resolved"}
    assert {row["why_allowlist_blocked"] for row in unresolved} == {"preferred_event_key_not_resolved"}
    assert {row["likely_next_information_source"] for row in unresolved} == {"sanitized_complex_card_html_structure_probe_or_later_raw_structure_annotation"}
    assert {row["unresolved_reason_qa_passed"] for row in unresolved} == {"True"}
    assert manifest["minimal_event_key_resolved_card_count"] == 0
    assert manifest["preferred_event_key_resolved_card_count"] == 0
    assert manifest["partial_event_key_card_count"] == 0
    assert manifest["unresolved_card_count"] == 5


def test_materialization_next_step_and_training_boundaries() -> None:
    manifest = _manifest()
    decisions = {row["decision_item"]: row for row in _csv_rows(ROOT / "covapie_covpdb_complex_card_materialization_decision_qa.csv")}
    next_step = _csv_rows(ROOT / "covapie_covpdb_complex_card_next_step_decision_qa.csv")
    assert decisions["candidate_metadata_materialization"]["current_step_decision"] == "blocked"
    assert decisions["candidate_allowlist_materialization"]["current_step_decision"] == "blocked"
    assert decisions["raw_read_smoke"]["current_step_decision"] == "blocked"
    assert decisions["training"]["current_step_decision"] == "blocked"
    assert {row["decision_qa_passed"] for row in decisions.values()} == {"True"}
    assert next_step[0]["recommended_next_step"] == "covapie_covpdb_complex_card_html_structure_probe_design_gate"
    assert next_step[0]["next_step_decision_qa_passed"] == "True"
    assert manifest["future_candidate_metadata_possible_count"] == 0
    assert manifest["future_automatic_allowlist_possible_count"] == 0
    assert manifest["ready_for_covapie_covpdb_complex_card_html_structure_probe_design_gate"] is True
    assert manifest["ready_for_covapie_candidate_metadata_materialization"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False


def test_no_network_or_forbidden_runtime_imports_in_step13at() -> None:
    module_path = Path("src/covalent_ext/covapie_covpdb_complex_card_metadata_acquisition_qa_gate.py")
    script_path = Path("scripts/check_covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    execution = {row["boundary_item"]: row for row in _csv_rows(ROOT / "covapie_covpdb_complex_card_acquisition_qa_execution_boundary_audit.csv")}
    assert execution["external_network_access"]["current_step_status"] == "not_executed_or_not_allowed"
    assert execution["complex_card_fetch"]["current_step_status"] == "not_executed_or_not_allowed"
    assert execution["raw_structure_download"]["current_step_status"] == "not_executed_or_not_allowed"
    assert execution["torch_import"]["current_step_status"] == "not_executed_or_not_allowed"
    assert {row["execution_boundary_passed"] for row in execution.values()} == {"True"}


def test_masks_feature_semantics_and_leakage_split_boundaries() -> None:
    manifest = _manifest()
    mask = _csv_rows(ROOT / "covapie_covpdb_complex_card_acquisition_qa_mask_scope_audit.csv")
    feature = _csv_rows(ROOT / "covapie_covpdb_complex_card_acquisition_qa_feature_semantics_audit.csv")
    leakage = _csv_rows(ROOT / "covapie_covpdb_complex_card_acquisition_qa_leakage_split_audit.csv")
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

