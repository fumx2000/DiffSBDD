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

from covalent_ext import covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke as smoke
from covalent_ext import covapie_cys_sg_targeted_metadata_expansion_next_batch_gate as step14m


ROOT = Path("data/derived/covalent_small/covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    assert path.is_file(), f"missing artifact: {path}"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    path = ROOT / "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_manifest.json"
    assert path.is_file(), "Run the Step 14N check script before artifact tests"
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


def test_parser_extracts_synthetic_covpdb_complex_fields() -> None:
    html = """
    <html><body>
      <a href="/covpdb/complex_card/pdb_ligand_id=42">SHOW</a>
      <a href="/covpdb/ligand_card/ligand_id=COVPDB999">Ligand</a>
      <a href="https://www.rcsb.org/ligand/ABC?ev=1">ABC</a>
      PDB Entry (9XYZ) Protein Name: Kinase X Uniprot ID/ACC: Q99999 (KINX_HUMAN)
      Ligand Name: Test inhibitor
      <table><tr><th>Reaction</th><th>Targetable Residue</th><th>Chain</th><th>SASA</th><th>pKa</th><th>Warhead</th></tr>
      <tr><td>Michael Addition</td><td>CYS 145</td><td>A</td><td>18.2</td><td>12.4</td><td>Vinyl Carbonyl</td></tr></table>
    </body></html>
    """
    info = smoke.parse_complex_card(html)
    assert info["covpdb_pdb_id_observed"] == "9XYZ"
    assert info["covpdb_het_code_observed"] == "ABC"
    assert info["covpdb_uniprot_observed"] == "Q99999 (KINX_HUMAN)"
    assert info["covpdb_reaction_name_observed"] == "Michael Addition"
    assert info["covpdb_residue_name_observed"] == "CYS"
    assert info["covpdb_residue_index_observed"] == "145"
    assert info["covpdb_chain_id_observed"] == "A"
    assert info["covpdb_warhead_name_observed"] == "Vinyl Carbonyl"
    assert info["ligand_identifier_if_available"] == "COVPDB999"


def test_forbidden_url_filter_blocks_raw_artifact_suffixes() -> None:
    blocked = [
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/download/foo.zip",
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex.pdb",
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/ligand.sdf",
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/model.mmcif",
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/archive.gz",
    ]
    assert all(not smoke.allowed_metadata_url(url) for url in blocked)
    assert smoke.allowed_metadata_url("https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=124")
    assert smoke.allowed_metadata_url("https://data.rcsb.org/rest/v1/core/chemcomp/ABC")


def test_step14m_precondition_and_network_metadata_boundary() -> None:
    step14m_manifest = json.loads(step14m.MANIFEST_JSON.read_text(encoding="utf-8"))
    pre = _csv_rows(ROOT / "covapie_cys_sg_next_batch_acquisition_precondition_audit.csv")
    discovery = _csv_rows(ROOT / "covapie_cys_sg_next_batch_source_discovery_audit.csv")
    manifest = _manifest()
    assert step14m_manifest["stage"] == smoke.PREVIOUS_STAGE
    assert step14m_manifest["all_checks_passed"] is True
    assert step14m_manifest["current_candidate_count"] == 9
    assert step14m_manifest["ready_for_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke"] is True
    assert {row["precondition_passed"] for row in pre} == {"True"}
    assert len(discovery) >= 1
    assert {row["discovery_audit_passed"] for row in discovery} == {"True"}
    assert manifest["existing_candidate_count"] == 9
    assert manifest["network_access_used"] is True
    assert manifest["download_attempted"] is True
    assert manifest["raw_coordinate_downloaded"] is False
    assert manifest["raw_file_content_read_current_step"] is False
    assert manifest["html_files_written_current_step"] is False


def test_complex_extraction_and_candidates_are_consistent() -> None:
    complex_rows = _csv_rows(ROOT / "covapie_cys_sg_next_batch_covpdb_complex_extraction_audit.csv")
    candidates = _csv_rows(ROOT / "covapie_cys_sg_next_batch_acquired_annotation_candidates.csv")
    candidates_json = json.loads((ROOT / "covapie_cys_sg_next_batch_acquired_annotation_candidates.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    assert len(complex_rows) == manifest["complex_card_fetch_attempt_count"]
    assert manifest["complex_card_fetch_success_count"] >= 1
    assert manifest["complex_card_cys_event_annotation_count"] >= manifest["new_candidate_count"]
    assert len(candidates) == len(candidates_json) == manifest["new_candidate_count"]
    assert manifest["next_batch_acquired_candidates_csv_json_consistent"] is True
    assert [row["next_batch_acquired_candidate_id"] for row in candidates] == [
        row["next_batch_acquired_candidate_id"] for row in candidates_json
    ]
    assert {row["manual_review_status"] for row in candidates} <= {"pending_manual_review"}
    assert {row["ready_candidate_current_step"] for row in candidates} <= {"False"}
    assert {row["ready_for_training_current_step"] for row in candidates} <= {"False"}
    assert {row["duplicate_exclusion_status"] for row in candidates} <= {"not_duplicate_against_step14l"}


def test_candidate_optional_names_are_cleaned_without_losing_event_metadata() -> None:
    candidates = _csv_rows(ROOT / "covapie_cys_sg_next_batch_acquired_annotation_candidates.csv")
    candidates_json = json.loads((ROOT / "covapie_cys_sg_next_batch_acquired_annotation_candidates.json").read_text(encoding="utf-8"))
    manifest = _manifest()
    forbidden_fragments = [
        "HET Code Ligand ID Sequence",
        "PDB ID Uniprot ID/ACC",
        "Download Help Contact",
        "table {",
    ]
    for row in candidates:
        for key in ["covpdb_ligand_name", "covpdb_protein_name"]:
            assert not any(fragment in row[key] for fragment in forbidden_fragments), (key, row[key])
        assert row["covpdb_reaction_name"]
        assert row["covpdb_residue_name"] == "CYS"
        assert row["covpdb_chain_id"]
        assert row["covpdb_warhead_name"]
    for row in candidates_json:
        for key in ["covpdb_ligand_name", "covpdb_protein_name"]:
            assert not any(fragment in str(row[key]) for fragment in forbidden_fragments), (key, row[key])
    assert manifest["new_candidate_count"] >= 11
    assert manifest["combined_candidate_count"] >= 20
    assert manifest["additional_candidate_needed_after_step"] == 0
    assert manifest["ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["no_ready_candidates_created"] is True
    ccd_backed = [row for row in candidates if row["ccd_ligand_name"]]
    assert ccd_backed


def test_no_duplicate_against_step14m_exclusion_registry() -> None:
    exclusion = _csv_rows(step14m.EXCLUSION_REGISTRY_CSV)
    candidates = _csv_rows(ROOT / "covapie_cys_sg_next_batch_acquired_annotation_candidates.csv")
    excluded_urls = {row["covpdb_complex_card_url"] for row in exclusion}
    excluded_event_keys = {
        (
            row["pdb_id"].upper(),
            row["suggested_ligand_comp_id"].upper(),
            "CYS",
            "",
            "",
        )
        for row in exclusion
    }
    for row in candidates:
        assert row["complex_card_url"] not in excluded_urls
        broad_key = (
            row["pdb_id"].upper(),
            row["suggested_ligand_comp_id"].upper(),
            row["covpdb_residue_name"].upper(),
            "",
            "",
        )
        assert broad_key not in excluded_event_keys


def test_threshold_readiness_and_training_boundaries() -> None:
    threshold = _csv_rows(ROOT / "covapie_cys_sg_next_batch_threshold_gap_audit.csv")
    manifest = _manifest()
    by_item = {row["threshold_gap_item"]: row for row in threshold}
    assert int(by_item["existing_candidate_count"]["threshold_gap_value"]) == 9
    assert int(by_item["new_candidate_count"]["threshold_gap_value"]) == manifest["new_candidate_count"]
    assert int(by_item["combined_candidate_count"]["threshold_gap_value"]) == manifest["combined_candidate_count"]
    assert int(by_item["additional_candidate_needed_before_step"]["threshold_gap_value"]) == 11
    assert int(by_item["ready_candidate_count_current_step"]["threshold_gap_value"]) == 0
    if manifest["combined_candidate_count"] >= 20:
        assert manifest["ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate"] is True
        assert manifest["recommended_next_step"] == "covapie_cys_sg_acquired_annotation_manual_review_gate"
    else:
        assert manifest["ready_for_covapie_cys_sg_targeted_metadata_expansion_next_batch_gate"] is True
        assert manifest["recommended_next_step"] == "covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_v1"
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True


def test_safety_no_raw_training_or_forbidden_imports() -> None:
    safety = _csv_rows(ROOT / "covapie_cys_sg_next_batch_acquisition_safety_audit.csv")
    manifest = _manifest()
    assert {row["safety_passed"] for row in safety} == {"True"}
    for key in [
        "sample_index_written_current_step",
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "sample_download_manifest_written",
        "actual_dataloader_adapter_smoke_written",
        "actual_dataloader_smoke_written",
        "training_artifacts_written",
        "torch_imported",
        "numpy_imported",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "gzip_open_used",
        "requests_used",
        "selenium_used",
        "playwright_used",
        "bs4_used",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
    ]:
        assert manifest[key] is False, key
    for root in [smoke.RAW_OUTPUT_ROOT, smoke.RAW_REFERENCE_ROOT]:
        tracked = subprocess.run(["git", "ls-files", root.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
        staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--", root.as_posix()], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
        assert not tracked
        assert not staged
    for name in ["requests", "torch", "numpy", "rdkit", "Bio", "gemmi", "gzip", "selenium", "playwright", "bs4"]:
        assert not _imports_name(Path("src/covalent_ext/covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke.py"), name)
        assert not _imports_name(Path("scripts/check_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0.py"), name)
    assert _imports_name(Path("src/covalent_ext/covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke.py"), "urllib")


def test_canonical_masks_preserved() -> None:
    manifest = _manifest()
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
    assert manifest["all_checks_passed"] is True
