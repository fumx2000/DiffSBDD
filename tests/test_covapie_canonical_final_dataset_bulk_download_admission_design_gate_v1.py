from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import covapie_canonical_final_dataset_bulk_download_admission_design_gate as gate


def _hashes(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.iterdir()
        if path.is_file()
    }


def _source_hashes() -> dict[str, str]:
    return {
        path.as_posix(): hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
        for path in gate._source_paths()
    }


def test_import_has_no_output_side_effect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    importlib.reload(gate)
    assert not (tmp_path / gate.DEFAULT_OUTPUT_ROOT).exists()


def test_materializes_exact_outputs_deterministically(tmp_path: Path) -> None:
    first = gate.run_bulk_download_admission_design_gate_v1(tmp_path)
    first_hashes = _hashes(tmp_path)
    second = gate.run_bulk_download_admission_design_gate_v1(tmp_path)
    assert first["all_checks_passed"] is True
    assert second["all_checks_passed"] is True
    assert first_hashes == _hashes(tmp_path)
    assert sorted(first_hashes) == sorted([*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME])


def test_source_contract_is_fixed_metadata_only_and_unchanged(tmp_path: Path) -> None:
    before = _source_hashes()
    manifest = gate.run_bulk_download_admission_design_gate_v1(tmp_path)
    assert before == gate.SOURCE_SHA256
    assert _source_hashes() == before
    assert manifest["source_input_count"] == 10
    assert manifest["artifact_inventory_reference_paths_not_recursively_opened"] is True
    assert "data/raw" not in "\n".join(manifest["source_input_sha256"])


def test_schema_and_rule_order_are_exact() -> None:
    schema = gate._schema_rows()
    rules = gate._rule_rows()
    assert [row["admission_field_name"] for row in schema] == list(gate.ADMISSION_RECORD_FIELDS)
    assert [row["admission_rule_id"] for row in rules] == [f"ADMIT_{index:03d}" for index in range(1, 16)]
    assert len({row["admission_rule_id"] for row in rules}) == 15
    assert [row["admission_field_name"] for row in schema[-4:]] == [
        "download_result_status",
        "observed_http_status",
        "observed_content_length_bytes",
        "observed_sha256",
    ]


def test_cys_sg_and_no_distance_inference_rules_are_present() -> None:
    rules = {row["admission_rule_name"]: row for row in gate._rule_rows()}
    assert rules["cys_sg_scope_only_v1"]["required_status"] == "residue_name_CYS_and_atom_SG"
    assert rules["distance_only_inference_forbidden"]["blocking_reason"] == "distance_only_inference_not_admissible"
    assert rules["topology_restoration_disposition"]["required_status"] == "approved_or_manual_review"


def test_source_boundary_fails_closed_for_wrong_qa_stage() -> None:
    source = copy.deepcopy(gate._load_source())
    source["qa_manifest"]["stage"] = "wrong_stage"
    rows = gate._source_boundary_rows(source)
    failed = {row["boundary_item"] for row in rows if row["source_boundary_passed"] == "false"}
    assert "qa_v1_stage" in failed


def test_source_boundary_fails_closed_for_sixth_mask() -> None:
    source = copy.deepcopy(gate._load_source())
    source["qa_manifest"]["canonical_mask_pairs"].append(["extra", "X"])
    rows = gate._source_boundary_rows(source)
    assert next(row for row in rows if row["boundary_item"] == "qa_v1_canonical_masks")["source_boundary_passed"] == "false"


def test_five_canonical_masks_include_b3_and_final_index_is_not_reinterpreted(tmp_path: Path) -> None:
    manifest = gate.run_bulk_download_admission_design_gate_v1(tmp_path)
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["canonical_final_dataset_baseline_only"] is True
    assert manifest["candidate_records_materialized"] is False


def test_safety_and_readiness_boundaries_are_closed(tmp_path: Path) -> None:
    manifest = gate.run_bulk_download_admission_design_gate_v1(tmp_path)
    with (tmp_path / gate.CSV_OUTPUTS[3]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["safety_passed"] for row in rows} == {"true"}
    assert manifest["ready_for_bulk_download_admission_implementation"] is True
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["all_source_boundary_checks_passed"] is True
    assert manifest["all_admission_schema_contract_checks_passed"] is True
    assert manifest["all_admission_rule_contract_checks_passed"] is True
    assert manifest["all_safety_checks_passed"] is True
    assert manifest["recommended_next_step"] == gate.NEXT_STAGE


def test_normal_issue_inventory_is_no_issues_sentinel(tmp_path: Path) -> None:
    gate.run_bulk_download_admission_design_gate_v1(tmp_path)
    with (tmp_path / gate.CSV_OUTPUTS[4]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [{
        "issue_id": "NO_ISSUES", "issue_type": "no_admission_design_issues",
        "severity": "none", "status": "no_issues", "issue_count": "0", "blocking_reason": "",
    }]


def test_manifest_records_non_manifest_output_hashes(tmp_path: Path) -> None:
    manifest = gate.run_bulk_download_admission_design_gate_v1(tmp_path)
    assert manifest["output_file_count"] == 6
    assert manifest["non_manifest_output_count"] == 5
    assert manifest["output_sha256"] == {
        name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
        for name in gate.CSV_OUTPUTS
    }
    assert "/home/" not in json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in json.dumps(manifest, sort_keys=True).lower()


def test_module_and_check_script_do_not_import_forbidden_runtime_dependencies() -> None:
    forbidden = {"urllib", "requests", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip"}
    for relative_path in (
        Path("src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py"),
        Path("scripts/check_covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1.py"),
    ):
        tree = ast.parse((REPO_ROOT / relative_path).read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        assert not names & forbidden


def test_check_script_passes_and_writes_no_raw_or_network_outputs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1.py"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1_passed" in result.stdout


def _materialization(
    *,
    schema_rows: list[dict[str, str]] | None = None,
    rule_rows: list[dict[str, str]] | None = None,
    safety_rows: list[dict[str, str]] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    source = copy.deepcopy(gate._load_source())
    result = gate._build_materialization(
        source,
        schema_rows=schema_rows,
        rule_rows=rule_rows,
        safety_rows=safety_rows,
    )
    return result, gate._manifest_payload(source, result, {})


def test_schema_contract_fails_closed_when_field_is_removed() -> None:
    rows = gate._schema_rows()
    rows.pop()
    result, manifest = _materialization(schema_rows=rows)
    assert result["all_admission_schema_contract_checks_passed"] is False
    assert manifest["all_checks_passed"] is False
    assert manifest["blocking_reasons"] == ["admission_schema_contract_failed"]
    assert manifest["admission_schema_field_count"] == 16
    assert manifest["expected_admission_schema_field_count"] == 17


def test_schema_contract_fails_closed_when_extra_field_is_added() -> None:
    rows = gate._schema_rows()
    extra = copy.deepcopy(rows[-1])
    extra["admission_field_name"] = "unexpected_extra_field"
    rows.append(extra)
    result, _ = _materialization(schema_rows=rows)
    assert result["all_admission_schema_contract_checks_passed"] is False


def test_schema_contract_fails_closed_when_order_drifts() -> None:
    rows = gate._schema_rows()
    rows[0], rows[1] = rows[1], rows[0]
    result, _ = _materialization(schema_rows=rows)
    assert result["all_admission_schema_contract_checks_passed"] is False


def test_rule_contract_fails_closed_when_admit_015_is_removed() -> None:
    rows = gate._rule_rows()[:-1]
    result, manifest = _materialization(rule_rows=rows)
    assert result["all_admission_rule_contract_checks_passed"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STAGE
    assert manifest["admission_rule_count"] == 14
    assert manifest["expected_admission_rule_count"] == 15


def test_rule_contract_fails_closed_when_admit_016_is_added() -> None:
    rows = gate._rule_rows()
    extra = copy.deepcopy(rows[-1])
    extra["admission_rule_id"] = "ADMIT_016"
    extra["admission_rule_name"] = "unique_extra_rule"
    rows.append(extra)
    result, _ = _materialization(rule_rows=rows)
    assert result["all_admission_rule_contract_checks_passed"] is False


def test_rule_contract_fails_closed_for_duplicate_rule_name() -> None:
    rows = gate._rule_rows()
    rows[-1]["admission_rule_name"] = rows[0]["admission_rule_name"]
    result, _ = _materialization(rule_rows=rows)
    assert result["all_admission_rule_contract_checks_passed"] is False


@pytest.mark.parametrize(
    ("rule_name", "field", "replacement"),
    [
        ("cys_sg_scope_only_v1", "required_status", "residue_name_CYS_and_atom_CB"),
        ("distance_only_inference_forbidden", "blocking_reason", "distance_inference_allowed"),
        ("topology_restoration_disposition", "required_status", "approved_template_only"),
    ],
)
def test_key_rule_semantics_fail_closed(
    rule_name: str,
    field: str,
    replacement: str,
) -> None:
    rows = gate._rule_rows()
    next(row for row in rows if row["admission_rule_name"] == rule_name)[field] = replacement
    result, _ = _materialization(rule_rows=rows)
    assert result["all_admission_rule_contract_checks_passed"] is False


def test_schema_failure_has_only_schema_issue_and_blocker() -> None:
    rows = gate._schema_rows()[:-1]
    result, manifest = _materialization(schema_rows=rows)
    assert manifest["blocking_reasons"] == ["admission_schema_contract_failed"]
    assert result["issue_rows"] == [{
        "issue_id": "ADMISSION_SCHEMA_CONTRACT_FAILURE",
        "issue_type": "admission_schema_contract_failure",
        "severity": "blocking",
        "status": "open",
        "issue_count": "1",
        "blocking_reason": "admission_schema_contract_failed",
    }]


def test_rule_failure_has_only_rule_issue_and_blocker() -> None:
    rows = gate._rule_rows()[:-1]
    result, manifest = _materialization(rule_rows=rows)
    assert manifest["blocking_reasons"] == ["admission_rule_contract_failed"]
    assert result["issue_rows"][0]["issue_id"] == "ADMISSION_RULE_CONTRACT_FAILURE"


def test_safety_failure_has_only_safety_issue_and_blocker() -> None:
    rows = gate._safety_rows()
    rows[0]["observed_status"] = "true"
    rows[0]["safety_passed"] = "false"
    rows[0]["blocking_reason"] = rows[0]["safety_item"]
    result, manifest = _materialization(safety_rows=rows)
    assert manifest["blocking_reasons"] == ["safety_boundary_audit_failed"]
    assert result["issue_rows"][0]["issue_id"] == "SAFETY_BOUNDARY_FAILURE"


def test_multiple_failed_sections_have_ordered_blockers_and_issues() -> None:
    schema = gate._schema_rows()[:-1]
    rules = gate._rule_rows()[:-1]
    safety = gate._safety_rows()
    safety[0]["observed_status"] = "true"
    safety[0]["safety_passed"] = "false"
    safety[0]["blocking_reason"] = safety[0]["safety_item"]
    result, manifest = _materialization(schema_rows=schema, rule_rows=rules, safety_rows=safety)
    assert manifest["blocking_reasons"] == [
        "admission_schema_contract_failed",
        "admission_rule_contract_failed",
        "safety_boundary_audit_failed",
    ]
    assert [row["issue_id"] for row in result["issue_rows"]] == [
        "ADMISSION_SCHEMA_CONTRACT_FAILURE",
        "ADMISSION_RULE_CONTRACT_FAILURE",
        "SAFETY_BOUNDARY_FAILURE",
    ]


def test_source_boundary_checks_include_step14ar_and_step14aq_semantics() -> None:
    rows = gate._source_boundary_rows(gate._load_source())
    by_item = {row["boundary_item"]: row for row in rows}
    assert by_item["step14ar_stage"]["source_boundary_passed"] == "true"
    assert by_item["step14aq_stage"]["source_boundary_passed"] == "true"
    assert by_item["step14ar_step14aq_provenance"]["source_boundary_passed"] == "true"


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("value_contract", "drifted contract"),
        ("requirement_phase", "post_download"),
        ("admission_schema_passed", "false"),
    ],
)
def test_schema_exact_contract_drift_fails_closed(field: str, replacement: str) -> None:
    rows = gate._schema_rows()
    rows[0][field] = replacement
    result, _ = _materialization(schema_rows=rows)
    assert result["all_admission_schema_contract_checks_passed"] is False


def test_schema_extra_key_fails_closed() -> None:
    rows = gate._schema_rows()
    rows[0]["unexpected_key"] = "unexpected"
    result, _ = _materialization(schema_rows=rows)
    assert result["all_admission_schema_contract_checks_passed"] is False


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("evidence_source", "drifted_evidence_source"),
        ("required_status", "drifted_required_status"),
        ("evaluation_phase", "pre_final_split"),
    ],
)
def test_non_key_rule_exact_contract_drift_fails_closed(field: str, replacement: str) -> None:
    rows = gate._rule_rows()
    rows[1][field] = replacement  # ADMIT_002 is intentionally not a key-rule audit.
    result, _ = _materialization(rule_rows=rows)
    assert result["all_admission_rule_contract_checks_passed"] is False


def test_rule_extra_key_fails_closed() -> None:
    rows = gate._rule_rows()
    rows[0]["unexpected_key"] = "unexpected"
    result, _ = _materialization(rule_rows=rows)
    assert result["all_admission_rule_contract_checks_passed"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda rows: rows.clear(),
        lambda rows: rows.pop(),
        lambda rows: rows.append(copy.deepcopy(rows[0])),
        lambda rows: rows.__setitem__(slice(0, 2), [rows[1], rows[0]]),
        lambda rows: rows.__setitem__(1, copy.deepcopy(rows[0])),
    ],
    ids=["empty", "missing", "extra", "reordered", "duplicate"],
)
def test_safety_exact_contract_shape_drift_fails_closed(mutation: object) -> None:
    rows = gate._safety_rows()
    mutation(rows)  # type: ignore[operator]
    result, manifest = _materialization(safety_rows=rows)
    assert result["all_safety_checks_passed"] is False
    assert manifest["ready_for_bulk_download_admission_implementation"] is False
    assert manifest["safety_item_count"] == len(rows)
    assert manifest["expected_safety_item_count"] == len(gate.CANONICAL_SAFETY_ITEMS)


def test_lifecycle_phase_counts_and_field_sets_are_exact(tmp_path: Path) -> None:
    manifest = gate.run_bulk_download_admission_design_gate_v1(tmp_path)
    rows = gate._schema_rows()
    by_phase = {
        phase: [row["admission_field_name"] for row in rows if row["requirement_phase"] == phase]
        for phase in ("pre_download", "pre_final_split", "post_download")
    }
    assert manifest["pre_download_required_field_count"] == 12
    assert manifest["pre_final_split_required_field_count"] == 1
    assert manifest["post_download_required_field_count"] == 4
    assert by_phase["pre_download"] == list(gate.ADMISSION_RECORD_FIELDS[:12])
    assert by_phase["pre_final_split"] == ["leakage_group_id"]
    assert by_phase["post_download"] == [
        "download_result_status",
        "observed_http_status",
        "observed_content_length_bytes",
        "observed_sha256",
    ]
