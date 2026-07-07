from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_covpdb_metadata_only_acquisition_smoke as smoke


SYNTHETIC_HTML = """
<html><body>
<table class="result_table">
<thead><td colspan="10"><h5>2 Complex(es)</h5></td></thead>
<tbody>
<tr class="color1">
<td>1</td><td> 1A3B </td>
<td><a href="/covpdb/protein_card/protein_id=434"> Prothrombin </a></td>
<td> Homo sapiens (Human) </td>
<td><a href="https://www.uniprot.org/uniprot/P00734"> P00734 (THRB_HUMAN) </a></td>
<td><a href="/covpdb/ligand_card/ligand_id=COVPDB1333"> TRI166 </a></td>
<td><a href="https://www.rcsb.org/ligand/T29"> T29 </a></td>
<td><img src="/staticfiles/covpdb/img/img_ligands/COVPDB1333.svg"></td>
<td><a href="/covpdb/complex_card/pdb_ligand_id=2037"> SHOW </a></td>
</tr>
<tr class="color2">
<td>2</td><td> 5F2E </td>
<td><a href="/covpdb/protein_card/protein_id=200"> Test kinase </a></td>
<td> Mus musculus </td>
<td><a href="https://www.uniprot.org/uniprot/Q9TEST"> Q9TEST (KIN_MOUSE) </a></td>
<td><a href="/covpdb/ligand_card/ligand_id=COVPDB999"> TESTLIG </a></td>
<td><a href="https://www.rcsb.org/ligand/ABC"> ABC </a></td>
<td></td>
<td><a href="/covpdb/complex_card/pdb_ligand_id=999"> SHOW </a></td>
</tr>
</tbody>
</table>
</body></html>
"""


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    assert smoke.MANIFEST_JSON.is_file(), "Committed Step 13AO manifest is required; tests must not rerun the check script"
    return json.loads(smoke.MANIFEST_JSON.read_text(encoding="utf-8"))


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def test_parser_extracts_covpdb_complex_metadata() -> None:
    rows = smoke.parse_covpdb_complex_rows(SYNTHETIC_HTML, smoke.COMPLEXES_LIST_URL, "2026-07-06T00:00:00+00:00")
    assert len(rows) == 2
    first = rows[0]
    assert first["pdb_id"] == "1A3B"
    assert first["protein_name"] == "Prothrombin"
    assert first["organism"] == "Homo sapiens (Human)"
    assert first["uniprot_id"] == "P00734"
    assert first["uniprot_label"] == "THRB_HUMAN"
    assert first["ligand_name"] == "TRI166"
    assert first["het_code"] == "T29"
    assert first["covpdb_ligand_id"] == "COVPDB1333"
    assert first["covpdb_complex_card_url"].endswith("/covpdb/complex_card/pdb_ligand_id=2037")
    assert first["raw_structure_downloaded"] is False
    assert first["raw_ligand_downloaded"] is False
    assert first["metadata_only_record"] is True


def test_forbidden_url_filter_blocks_raw_suffixes_and_external_raw_hosts() -> None:
    for url in [
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/download/all.zip",
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/file.pdb",
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/file.sdf",
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/file.mmcif",
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/file.gz",
        "https://files.rcsb.org/download/1A3B.pdb",
    ]:
        assert smoke.is_forbidden_raw_url(url)
        assert not smoke.is_allowed_covpdb_html_url(url)
    assert smoke.is_allowed_covpdb_html_url(smoke.COMPLEXES_LIST_URL)


def test_synthetic_success_writes_19_column_metadata_csv(tmp_path: Path) -> None:
    def fake_fetch(url: str) -> dict:
        return {
            "url": url,
            "fetched": True,
            "status": "200",
            "content_type": "text/html; charset=utf-8",
            "byte_count": len(SYNTHETIC_HTML),
            "html": SYNTHETIC_HTML,
            "blocking_reasons": "",
        }

    metadata_csv = tmp_path / "covpdb_complexes_metadata_manual.csv"
    result = smoke.run_covpdb_metadata_only_acquisition_smoke_v0(
        output_root=tmp_path / "out",
        metadata_csv_path=metadata_csv,
        fetcher=fake_fetch,
    )
    manifest = result["manifest"]
    assert manifest["metadata_csv_written"] is True
    assert manifest["metadata_csv_row_count"] == 2
    assert manifest["metadata_csv_column_count"] == 19
    assert manifest["covpdb_metadata_only_acquisition_smoke_passed"] is True
    assert manifest["ready_for_covapie_external_metadata_index_download_smoke_rerun"] is True
    assert manifest["recommended_next_step"] == "rerun_covapie_external_metadata_index_download_smoke"
    rows = _csv_rows(metadata_csv)
    assert list(rows[0]) == smoke.METADATA_COLUMNS
    assert rows[0]["pdb_id"] == "1A3B"
    assert rows[0]["het_code"] == "T29"
    assert rows[1]["pdb_id"] == "5F2E"
    assert rows[1]["het_code"] == "ABC"


def test_fetch_failure_blocks_safely_and_writes_no_fake_metadata(tmp_path: Path) -> None:
    def failing_fetch(url: str) -> dict:
        return {
            "url": url,
            "fetched": False,
            "status": "TimeoutError: synthetic",
            "content_type": "",
            "byte_count": 0,
            "html": "",
            "blocking_reasons": "covpdb_fetch_failed",
        }

    metadata_csv = tmp_path / "missing.csv"
    result = smoke.run_covpdb_metadata_only_acquisition_smoke_v0(
        output_root=tmp_path / "out",
        metadata_csv_path=metadata_csv,
        fetcher=failing_fetch,
    )
    manifest = result["manifest"]
    assert manifest["metadata_csv_written"] is False
    assert manifest["metadata_csv_row_count"] == 0
    assert manifest["metadata_only_acquisition_status"] == "blocked_due_to_covpdb_metadata_fetch_or_parse_failure"
    assert manifest["ready_for_covapie_external_metadata_index_download_smoke_rerun"] is False
    assert manifest["recommended_next_step"] == "inspect_covpdb_html_metadata_structure"
    assert manifest["blocking_reasons"] == ["covpdb_fetch_failed"]
    assert not metadata_csv.exists()


def test_no_forbidden_runtime_imports_except_allowed_urllib() -> None:
    module_path = Path("src/covalent_ext/covapie_covpdb_metadata_only_acquisition_smoke.py")
    for name in ["torch", "rdkit", "gemmi", "Bio", "requests", "selenium", "playwright", "gzip"]:
        assert not _imports_name(module_path, name)
    assert _imports_name(module_path, "urllib")
    text = module_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run":
            call_text = ast.get_source_segment(text, node) or ""
            assert "curl" not in call_text
            assert "wget" not in call_text


def test_committed_step13ao_artifacts_are_present_and_read_only() -> None:
    manifest = _manifest()
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["metadata_csv_written"] is True
    assert manifest["metadata_csv_row_count"] == 25
    assert manifest["metadata_csv_column_count"] == 19
    assert manifest["covpdb_metadata_only_acquisition_smoke_passed"] is True
    assert manifest["ready_for_covapie_external_metadata_index_download_smoke_rerun"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert smoke.METADATA_CSV.is_file()
    rows = _csv_rows(smoke.METADATA_CSV)
    assert len(rows) == 25
    assert list(rows[0]) == smoke.METADATA_COLUMNS
    assert [(row["pdb_id"], row["het_code"]) for row in rows[:5]] == [
        ("1A3B", "T29"),
        ("1A3E", "T16"),
        ("1A46", "00K"),
        ("1A54", "MDC"),
        ("1A5G", "00L"),
    ]


def test_output_audits_masks_feature_leakage_and_boundaries() -> None:
    manifest = _manifest()
    assert manifest["precondition_audit_row_count"] == len(_csv_rows(smoke.PRECONDITION_AUDIT_CSV)) == 8
    assert manifest["network_scope_audit_row_count"] == len(_csv_rows(smoke.NETWORK_SCOPE_AUDIT_CSV)) == 1
    assert manifest["page_fetch_audit_row_count"] == len(_csv_rows(smoke.PAGE_FETCH_AUDIT_CSV))
    assert manifest["parse_audit_row_count"] == len(_csv_rows(smoke.PARSE_AUDIT_CSV)) == 1
    assert manifest["csv_schema_audit_row_count"] == len(_csv_rows(smoke.CSV_SCHEMA_AUDIT_CSV)) == 19
    assert manifest["raw_artifact_safety_audit_row_count"] == len(_csv_rows(smoke.RAW_ARTIFACT_SAFETY_AUDIT_CSV)) == 10
    assert manifest["event_key_boundary_audit_row_count"] == len(_csv_rows(smoke.EVENT_KEY_BOUNDARY_AUDIT_CSV)) == 7
    assert manifest["execution_boundary_audit_row_count"] == len(_csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)) == 15
    assert manifest["git_safety_audit_row_count"] == len(_csv_rows(smoke.GIT_SAFETY_AUDIT_CSV)) == 10
    assert manifest["mask_scope_audit_row_count"] == len(_csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)) == 5
    assert manifest["feature_semantics_audit_row_count"] == len(_csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)) == 12
    assert manifest["leakage_split_audit_row_count"] == len(_csv_rows(smoke.LEAKAGE_SPLIT_AUDIT_CSV)) == 12

    network = _csv_rows(smoke.NETWORK_SCOPE_AUDIT_CSV)[0]
    assert network["allowed_domain"] == smoke.ALLOWED_DOMAIN
    assert network["forbidden_suffix_urls_fetched"] == "[]"
    assert network["network_scope_passed"] == "True"
    raw = _csv_rows(smoke.RAW_ARTIFACT_SAFETY_AUDIT_CSV)
    assert {row["raw_artifact_status"] for row in raw} == {"False"}
    assert {row["raw_artifact_safety_passed"] for row in raw} == {"True"}

    masks = _csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)
    assert [row["canonical_mask_task_name"] for row in masks] == smoke.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in masks] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True

    feature = _csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    leakage = _csv_rows(smoke.LEAKAGE_SPLIT_AUDIT_CSV)
    assert {row["current_step_status"] for row in leakage} == {"placeholder_only_no_split_written"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}


def test_manifest_safety_flags_and_readiness() -> None:
    manifest = _manifest()
    for key in [
        "external_source_url_verified",
        "external_metadata_downloaded",
        "raw_data_read",
        "sdf_read",
        "pdb_read",
        "mmcif_text_read",
        "gzip_open_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "candidate_metadata_materialized",
        "candidate_allowlist_materialized",
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
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
    ]:
        assert manifest[key] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
