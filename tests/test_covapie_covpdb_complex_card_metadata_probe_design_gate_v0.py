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

from covalent_ext import covapie_covpdb_complex_card_metadata_probe_design_gate as gate


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_covpdb_complex_card_metadata_probe_design_gate_v0.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    if not gate.MANIFEST_JSON.is_file():
        _ensure_outputs()
    return json.loads(gate.MANIFEST_JSON.read_text(encoding="utf-8"))


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def test_check_script_passes_and_validates_step13aq_precondition() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_covpdb_complex_card_metadata_probe_design_gate_v0_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == gate.STAGE
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13aq_schema_probe_design_gate_validated"] is True
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []
    assert gate.validate_step13aq_precondition_v0() is True


def test_metadata_csv_has_card_urls_and_allowed_path_contract() -> None:
    rows = gate.read_metadata_rows()
    urls = gate.complex_card_urls(rows)
    assert len(rows) == 25
    assert len(urls) == 25
    assert urls[:5] == [
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=2037",
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=2034",
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=1",
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=1614",
        "https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/pdb_ligand_id=2",
    ]
    assert all(gate.is_allowed_complex_card_url(url) for url in urls)
    assert not gate.is_allowed_complex_card_url("https://drug-discovery.vm.uni-freiburg.de/covpdb/complex_card/1A3B.pdb")
    assert not gate.is_allowed_complex_card_url("https://files.rcsb.org/download/1A3B.pdb")
    allowed = _csv_rows(gate.ALLOWED_URL_CONTRACT_CSV)
    by_item = {row["url_contract_item"]: row for row in allowed}
    assert by_item["allowed_domain"]["contract_value"] == "drug-discovery.vm.uni-freiburg.de"
    assert by_item["allowed_path_prefix"]["contract_value"] == "/covpdb/complex_card/"
    assert by_item["maximum_cards_first_smoke"]["contract_value"] == "5"
    assert by_item["recursive_crawling"]["contract_value"] == "not_allowed"


def test_target_field_contract_covers_event_key_and_supporting_fields() -> None:
    target = _csv_rows(gate.TARGET_FIELD_CONTRACT_CSV)
    assert len(target) == len(gate.CRITICAL_EVENT_KEY_FIELDS) + len(gate.SUPPORTING_FIELDS) + len(gate.OPTIONAL_ANNOTATION_FIELDS)
    by_field = {row["target_field"]: row for row in target}
    for field in gate.CRITICAL_EVENT_KEY_FIELDS:
        assert by_field[field]["field_class"] == "critical_event_key"
        assert by_field[field]["required_for_preferred_event_key"] == "True"
        assert by_field[field]["raw_structure_required_current_step"] == "False"
        assert by_field[field]["materialization_blocking_if_missing"] == "True"
    assert by_field["chain_id"]["required_for_minimal_event_key"] == "True"
    assert by_field["covalent_bond_atom_pair"]["required_for_minimal_event_key"] == "False"
    for field in ["covpdb_complex_card_url", "source_record_url", "pdb_id", "het_code", "covpdb_ligand_id"]:
        assert by_field[field]["field_class"] == "supporting_metadata"
    assert by_field["parse_failure_reason"]["field_class"] == "optional_annotation"


def test_forbidden_artifact_parse_strategy_and_failure_taxonomy_contracts() -> None:
    forbidden = _csv_rows(gate.FORBIDDEN_ARTIFACT_CONTRACT_CSV)
    assert [row["forbidden_artifact_or_action"] for row in forbidden] == gate.FORBIDDEN_ARTIFACT_ITEMS
    assert {".zip", ".pdb", ".mmcif", ".sdf", ".gz"} <= {row["forbidden_artifact_or_action"] for row in forbidden}
    assert {row["forbidden_artifact_contract_passed"] for row in forbidden} == {"True"}
    parse = _csv_rows(gate.PARSE_STRATEGY_CONTRACT_CSV)
    assert [row["parse_strategy_item"] for row in parse] == [item for item, _ in gate.PARSE_STRATEGY_ITEMS]
    assert {row["parse_strategy_contract_passed"] for row in parse} == {"True"}
    failure = _csv_rows(gate.FAILURE_TAXONOMY_CSV)
    assert [row["failure_reason"] for row in failure] == gate.FAILURE_REASONS
    assert "raw_download_required_for_resolution" in {row["failure_reason"] for row in failure}
    assert "training_attempted_too_early" in {row["failure_reason"] for row in failure}


def test_event_key_resolution_contract_blocks_materialization_without_minimal_key() -> None:
    event = _csv_rows(gate.EVENT_KEY_RESOLUTION_CONTRACT_CSV)
    by_status = {row["resolution_status"]: row for row in event}
    assert list(by_status) == gate.EVENT_KEY_RESOLUTION_STATUSES
    assert by_status["card_resolves_minimal_event_key"]["candidate_metadata_can_proceed"] == "True"
    assert by_status["card_resolves_minimal_event_key"]["candidate_allowlist_can_proceed"] == "False"
    assert by_status["card_resolves_minimal_event_key"]["manual_review_path_allowed"] == "True"
    assert by_status["card_resolves_preferred_event_key"]["candidate_allowlist_can_proceed"] == "True"
    for status in [
        "card_partial_event_key_only",
        "card_no_event_key_fields_found",
        "card_ambiguous_multi_event",
        "card_requires_raw_structure_annotation",
        "card_parse_failed",
    ]:
        assert by_status[status]["candidate_metadata_can_proceed"] == "False"
        assert by_status[status]["blocking_reasons"] == "minimal_event_key_unresolved"


def test_readiness_manifest_and_safety_boundaries() -> None:
    manifest = _manifest()
    assert manifest["metadata_csv_row_count"] == 25
    assert manifest["metadata_csv_column_count"] == 19
    assert manifest["complex_card_url_count"] == 25
    assert manifest["target_field_contract_row_count"] == len(_csv_rows(gate.TARGET_FIELD_CONTRACT_CSV))
    assert manifest["allowed_url_contract_row_count"] == len(_csv_rows(gate.ALLOWED_URL_CONTRACT_CSV))
    assert manifest["forbidden_artifact_contract_row_count"] == len(_csv_rows(gate.FORBIDDEN_ARTIFACT_CONTRACT_CSV))
    assert manifest["parse_strategy_contract_row_count"] == len(_csv_rows(gate.PARSE_STRATEGY_CONTRACT_CSV))
    assert manifest["event_key_resolution_contract_row_count"] == len(_csv_rows(gate.EVENT_KEY_RESOLUTION_CONTRACT_CSV))
    assert manifest["failure_taxonomy_row_count"] == len(_csv_rows(gate.FAILURE_TAXONOMY_CSV))
    assert manifest["ready_for_covapie_covpdb_complex_card_metadata_acquisition_smoke"] is True
    assert manifest["ready_for_covapie_candidate_metadata_materialization"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"] is False
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["candidate_metadata_materialized"] is False
    assert manifest["candidate_allowlist_materialized"] is False
    assert manifest["recommended_next_step"] == "covapie_covpdb_complex_card_metadata_acquisition_smoke"
    for key in [
        "network_access_used",
        "urllib_used",
        "requests_used",
        "browser_used",
        "raw_structure_downloaded",
        "raw_ligand_downloaded",
        "raw_data_read",
        "raw_file_copied",
        "sdf_read",
        "pdb_read",
        "mmcif_text_read",
        "gzip_open_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
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
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
    ]:
        assert manifest[key] is False


def test_no_network_raw_model_imports_and_canonical_masks() -> None:
    module_path = Path("src/covalent_ext/covapie_covpdb_complex_card_metadata_probe_design_gate.py")
    script_path = Path("scripts/check_covapie_covpdb_complex_card_metadata_probe_design_gate_v0.py")
    for name in ["urllib", "requests", "torch", "rdkit", "gemmi", "Bio", "gzip", "selenium", "playwright"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)
    for path in [module_path, script_path]:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run":
                call_text = ast.get_source_segment(text, node) or ""
                assert "curl" not in call_text
                assert "wget" not in call_text
    mask = _csv_rows(gate.MASK_SCOPE_AUDIT_CSV)
    assert [row["canonical_mask_task_name"] for row in mask] == gate.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == gate.CANONICAL_MASK_TASK_ALIASES
    manifest = _manifest()
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
