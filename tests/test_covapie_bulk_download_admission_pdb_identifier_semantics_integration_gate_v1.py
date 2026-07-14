from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate as gate  # noqa: E402


def _hashes(root: Path) -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.iterdir() if path.is_file()}


def _source_hashes() -> dict[str, str]:
    return {path.as_posix(): hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate._source_paths()}


def _load_check_module() -> object:
    path = REPO_ROOT / "scripts" / "check_covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1.py"
    spec = importlib.util.spec_from_file_location("step14au_b2_check", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _failure_assertions(result: dict[str, object], failed_key: str, failure_id: str) -> None:
    section_key = f"all_{failed_key}_checks_passed" if failed_key != "safety" else "all_safety_checks_passed"
    if failed_key == "rules":
        section_key = "all_integrated_rule_checks_passed"
    elif failed_key == "fields":
        section_key = "all_integrated_field_checks_passed"
    elif failed_key == "contexts":
        section_key = "all_integrated_context_checks_passed"
    elif failed_key == "issues":
        section_key = "all_issue_transition_checks_passed"
    elif failed_key == "lineage":
        section_key = "all_integration_lineage_checks_passed"
    elif failed_key == "source":
        section_key = "all_source_boundary_checks_passed"
    assert result[section_key] is False
    assert result["all_checks_passed"] is False
    assert result["remaining_issue_count"] == 12
    issue_ids = [row["issue_id"] for row in result["issue_rows"]]  # type: ignore[index]
    expected_blocking_ids = [*gate.REMAINING_ISSUE_IDS, failure_id]
    assert issue_ids == expected_blocking_ids
    issue_rows = result["issue_rows"]  # type: ignore[assignment]
    assert [row["issue_origin"] for row in issue_rows[:12]] == ["step14au_a_remaining_semantics_blocker"] * 12
    assert issue_rows[-1]["issue_origin"] == "step14au_b2_integration_gate_failure"
    assert issue_rows[-1]["integration_transition"] == "added_by_gate_failure"
    manifest = gate._manifest_payload(result, {})
    assert manifest["blocking_reasons"] == expected_blocking_ids
    assert manifest["remaining_issue_count"] == 12
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert manifest["pdb_identifier_semantics_integrated"] is False
    assert manifest["admit_002_rule_logic_ready"] is False
    assert manifest["ready_for_admission_evaluator_interface_implementation"] is False
    assert all(manifest[key] is False for key in (
        "ready_for_admission_evaluator_rule_logic_implementation", "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
    ))


def test_import_has_no_output_side_effect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    importlib.reload(gate)
    assert not (tmp_path / gate.DEFAULT_OUTPUT_ROOT).exists()


def test_exact_outputs_are_deterministic(tmp_path: Path) -> None:
    first = gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1(tmp_path)
    hashes = _hashes(tmp_path)
    second = gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1(tmp_path)
    assert first == second and hashes == _hashes(tmp_path)
    assert sorted(hashes) == sorted([*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME])


def test_twelve_sources_are_fixed_tracked_metadata_and_unchanged(tmp_path: Path) -> None:
    before = _source_hashes()
    manifest = gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1(tmp_path)
    assert before == gate.SOURCE_SHA256 == _source_hashes()
    assert manifest["source_input_count"] == 12


@pytest.mark.parametrize("mutate", [
    lambda rows: rows.pop(), lambda rows: rows.reverse(),
    lambda rows: rows[0].__setitem__("tracked_by_git", "false"),
    lambda rows: rows[0].__setitem__("sha256_observed", "0" * 64),
    lambda rows: rows[0].__setitem__("extra", "x"),
])
def test_source_boundary_rows_fail_closed(mutate: object) -> None:
    rows = gate._source_boundary_rows()
    mutate(rows)  # type: ignore[operator]
    assert gate._validate_source_rows(rows) is False


def test_source_semantics_contains_au_a_pdb_blocker_and_b1_readiness() -> None:
    source = gate._load_source()
    assert gate._validate_source_semantics(source)
    assert gate.REMOVED_ISSUE_ID in [row["issue_id"] for row in source["issue_rows"]]
    assert source["b1_manifest"]["ready_for_pdb_identifier_semantics_integration"] is True


def test_source_hash_drift_fails_closed_in_materialization() -> None:
    rows = gate._source_boundary_rows()
    rows[0]["sha256_observed"] = "0" * 64
    result = gate._build_materialization(gate._load_source(), source_rows=rows)
    assert result["all_integration_lineage_checks_passed"] is True
    assert result["all_integrated_rule_checks_passed"] is True
    assert result["all_integrated_field_checks_passed"] is True
    assert result["all_integrated_context_checks_passed"] is True
    assert result["all_issue_transition_checks_passed"] is True
    assert result["all_safety_checks_passed"] is True
    _failure_assertions(result, "source", "PDB_IDENTIFIER_INTEGRATION_SOURCE_BOUNDARY_FAILED")


def test_only_three_named_rows_are_integrated() -> None:
    source = gate._load_source()
    rules = gate._overlay_rule_rows(source["rule_rows"])
    fields = gate._overlay_field_rows(source["field_rows"])
    contexts = gate._overlay_context_rows(source["context_rows"])
    assert [row["admission_rule_id"] for row in rules if row["integration_applied"] == "true"] == ["ADMIT_002"]
    assert [row["field_name"] for row in fields if row["integration_applied"] == "true"] == ["pdb_id"]
    assert [row["context_item"] for row in contexts if row["integration_applied"] == "true"] == ["pdb_id_format_contract"]


def test_nonintegrated_source_semantics_are_preserved_exactly() -> None:
    source = gate._load_source()
    for original, overlay, identifier in (
        (source["rule_rows"], gate._overlay_rule_rows(source["rule_rows"]), "admission_rule_id"),
        (source["field_rows"], gate._overlay_field_rows(source["field_rows"]), "field_name"),
        (source["context_rows"], gate._overlay_context_rows(source["context_rows"]), "context_item"),
    ):
        for before, after in zip(original, overlay):
            if after["integration_applied"] == "false":
                assert {key: after[key] for key in before} == before, identifier


def test_admit_002_effective_state_and_pure_predicate() -> None:
    row = next(row for row in gate._overlay_rule_rows(gate._load_source()["rule_rows"]) if row["admission_rule_id"] == "ADMIT_002")
    assert (row["semantics_complete"], row["deterministic_evaluation_possible_now"], row["implementation_disposition"], row["blocking_reasons"]) == ("true", "true", "rule_logic_ready", "")
    assert gate.evaluate_admit_002_pdb_identifier("1ABC") == {
        "admission_rule_id": "ADMIT_002", "passed": True, "canonical_pdb_id": "pdb_00001abc",
        "input_form": "legacy_4_character", "blocking_reason": "",
    }
    assert gate.evaluate_admit_002_pdb_identifier("invalid")["passed"] is False
    assert "exists" not in gate.evaluate_admit_002_pdb_identifier("1abc")


def test_pdb_field_and_context_effective_state() -> None:
    source = gate._load_source()
    field = next(row for row in gate._overlay_field_rows(source["field_rows"]) if row["field_name"] == "pdb_id")
    context = next(row for row in gate._overlay_context_rows(source["context_rows"]) if row["context_item"] == "pdb_id_format_contract")
    assert all(field[key] == "true" for key in ("allowed_values_defined", "normalization_defined", "exact_validation_defined", "implementation_semantics_complete"))
    assert field["semantics_evidence"] == gate.PREVIOUS_STAGES[1] and field["blocking_reasons"] == ""
    assert all(context[key] == "true" for key in ("deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined", "implementation_ready"))


def test_only_pdb_issue_is_removed_and_remaining_issues_are_exact() -> None:
    rows = gate._overlay_issue_rows(gate._load_source()["issue_rows"])
    assert [row["issue_id"] for row in rows] == list(gate.REMAINING_ISSUE_IDS)
    assert all(row["issue_origin"] == "step14au_a_remaining_semantics_blocker" and row["integration_transition"] == "unchanged" for row in rows)


def test_integrated_rule_validator_fails_closed_for_other_rule_drift() -> None:
    source = gate._load_source()
    rules = gate._overlay_rule_rows(source["rule_rows"])
    rules[0]["semantics_complete"] = "true"
    assert not gate._validate_integrated_rule_rows(rules, source["rule_rows"])


def test_rule_drift_fails_only_rule_section_and_emits_gate_failure_issue() -> None:
    source = gate._load_source()
    rules = gate._overlay_rule_rows(source["rule_rows"])
    rules[0]["semantics_complete"] = "true"
    result = gate._build_materialization(source, rule_rows=rules)
    assert result["all_source_boundary_checks_passed"] is True
    assert result["all_integration_lineage_checks_passed"] is True
    assert result["all_integrated_field_checks_passed"] is True
    assert result["all_integrated_context_checks_passed"] is True
    assert result["all_issue_transition_checks_passed"] is True
    assert result["all_safety_checks_passed"] is True
    _failure_assertions(result, "rules", "PDB_IDENTIFIER_INTEGRATED_RULE_VALIDATION_FAILED")


def test_field_drift_fails_only_field_section_and_emits_gate_failure_issue() -> None:
    source = gate._load_source()
    fields = gate._overlay_field_rows(source["field_rows"])
    next(row for row in fields if row["field_name"] == "pdb_id")["normalization_defined"] = "false"
    result = gate._build_materialization(source, field_rows=fields)
    assert result["all_integrated_rule_checks_passed"] is True
    assert result["all_integrated_context_checks_passed"] is True
    assert result["all_issue_transition_checks_passed"] is True
    _failure_assertions(result, "fields", "PDB_IDENTIFIER_INTEGRATED_FIELD_VALIDATION_FAILED")


def test_context_drift_fails_only_context_section_and_emits_gate_failure_issue() -> None:
    source = gate._load_source()
    contexts = gate._overlay_context_rows(source["context_rows"])
    next(row for row in contexts if row["context_item"] == "pdb_id_format_contract")["implementation_ready"] = "false"
    result = gate._build_materialization(source, context_rows=contexts)
    assert result["all_integrated_rule_checks_passed"] is True
    assert result["all_integrated_field_checks_passed"] is True
    assert result["all_issue_transition_checks_passed"] is True
    _failure_assertions(result, "contexts", "PDB_IDENTIFIER_INTEGRATED_CONTEXT_VALIDATION_FAILED")


def test_issue_drift_fails_only_issue_section_and_emits_gate_failure_issue() -> None:
    source = gate._load_source()
    issues = gate._overlay_issue_rows(source["issue_rows"])
    issues.pop()
    result = gate._build_materialization(source, issue_rows=issues)
    assert result["all_integrated_rule_checks_passed"] is True
    assert result["all_integrated_field_checks_passed"] is True
    assert result["all_integrated_context_checks_passed"] is True
    _failure_assertions(result, "issues", "PDB_IDENTIFIER_ISSUE_TRANSITION_VALIDATION_FAILED")


def test_lineage_drift_fails_only_lineage_section_and_emits_gate_failure_issue() -> None:
    source = gate._load_source()
    rules = gate._overlay_rule_rows(source["rule_rows"])
    next(row for row in rules if row["admission_rule_id"] == "ADMIT_002")["integration_reason"] = "drift"
    result = gate._build_materialization(source, rule_rows=rules)
    assert result["all_integrated_rule_checks_passed"] is True
    assert result["all_integrated_field_checks_passed"] is True
    assert result["all_integrated_context_checks_passed"] is True
    assert result["all_issue_transition_checks_passed"] is True
    _failure_assertions(result, "lineage", "PDB_IDENTIFIER_INTEGRATION_LINEAGE_VALIDATION_FAILED")


def test_safety_drift_fails_only_safety_section_and_emits_gate_failure_issue() -> None:
    source = gate._load_source()
    safety = gate._safety_rows()
    safety[0]["observed_status"] = "true"
    result = gate._build_materialization(source, safety_rows=safety)
    assert result["all_integrated_rule_checks_passed"] is True
    assert result["all_integrated_field_checks_passed"] is True
    assert result["all_integrated_context_checks_passed"] is True
    assert result["all_issue_transition_checks_passed"] is True
    _failure_assertions(result, "safety", "PDB_IDENTIFIER_INTEGRATION_SAFETY_VALIDATION_FAILED")


def test_all_seven_section_failures_append_gate_issues_in_fixed_order() -> None:
    source = gate._load_source()
    source_rows = gate._source_boundary_rows(); source_rows[0]["sha256_observed"] = "0" * 64
    rules = gate._overlay_rule_rows(source["rule_rows"])
    rules[0]["semantics_complete"] = "true"
    next(row for row in rules if row["admission_rule_id"] == "ADMIT_002")["integration_reason"] = "drift"
    fields = gate._overlay_field_rows(source["field_rows"])
    next(row for row in fields if row["field_name"] == "pdb_id")["normalization_defined"] = "false"
    contexts = gate._overlay_context_rows(source["context_rows"])
    next(row for row in contexts if row["context_item"] == "pdb_id_format_contract")["implementation_ready"] = "false"
    issues = gate._overlay_issue_rows(source["issue_rows"]); issues.pop()
    safety = gate._safety_rows(); safety[0]["observed_status"] = "true"
    result = gate._build_materialization(
        source, source_rows=source_rows, rule_rows=rules, field_rows=fields,
        context_rows=contexts, issue_rows=issues, safety_rows=safety,
    )
    failure_ids = [
        "PDB_IDENTIFIER_INTEGRATION_SOURCE_BOUNDARY_FAILED",
        "PDB_IDENTIFIER_INTEGRATION_LINEAGE_VALIDATION_FAILED",
        "PDB_IDENTIFIER_INTEGRATED_RULE_VALIDATION_FAILED",
        "PDB_IDENTIFIER_INTEGRATED_FIELD_VALIDATION_FAILED",
        "PDB_IDENTIFIER_INTEGRATED_CONTEXT_VALIDATION_FAILED",
        "PDB_IDENTIFIER_ISSUE_TRANSITION_VALIDATION_FAILED",
        "PDB_IDENTIFIER_INTEGRATION_SAFETY_VALIDATION_FAILED",
    ]
    expected = [*gate.REMAINING_ISSUE_IDS, *failure_ids]
    assert result["all_checks_passed"] is False
    assert [row["issue_id"] for row in result["issue_rows"]] == expected
    manifest = gate._manifest_payload(result, {})
    assert manifest["blocking_reasons"] == expected
    assert manifest["remaining_issue_count"] == 12
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert manifest["pdb_identifier_semantics_integrated"] is False
    assert manifest["admit_002_rule_logic_ready"] is False
    assert manifest["ready_for_admission_evaluator_interface_implementation"] is False


def test_issue_transition_validator_fails_closed_for_issue_drift() -> None:
    source = gate._load_source()
    issues = gate._overlay_issue_rows(source["issue_rows"])
    issues.pop()
    assert not gate._validate_issue_transition_rows(issues, source["issue_rows"])


def test_manifest_counts_readiness_masks_and_no_timestamp(tmp_path: Path) -> None:
    manifest = gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1(tmp_path)
    assert (manifest["integrated_rule_count"], manifest["semantics_complete_rule_count"], manifest["semantics_incomplete_rule_count"]) == (15, 3, 12)
    assert (manifest["integrated_field_count"], manifest["semantics_complete_field_count"], manifest["semantics_incomplete_field_count"]) == (17, 1, 16)
    assert (manifest["integrated_context_count"], manifest["deterministic_now_context_count"], manifest["deterministic_after_contract_freeze_context_count"], manifest["ready_evaluation_context_count"]) == (18, 6, 18, 6)
    assert manifest["remaining_issue_count"] == 12 and manifest["removed_issue_ids"] == [gate.REMOVED_ISSUE_ID]
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]
    assert all(manifest[key] is False for key in ("ready_for_admission_evaluator_rule_logic_implementation", "ready_for_real_candidate_evaluation", "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now"))
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert "timestamp" not in json.dumps(manifest, sort_keys=True).lower()


def test_sixth_mask_is_not_present() -> None:
    assert len(gate.CANONICAL_MASK_PAIRS) == 5
    assert ("scaffold_only", "B3") in gate.CANONICAL_MASK_PAIRS


def test_forbidden_runtime_imports_are_absent() -> None:
    tree = ast.parse((REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate.py").read_text())
    names = {node.names[0].name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)}
    names |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert not names.intersection({"requests", "urllib", "aiohttp", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "shutil"})


@pytest.mark.parametrize(
    ("filename", "columns", "mutate"),
    [
        (gate.CSV_OUTPUTS[0], gate.RULE_COLUMNS, lambda rows: next(row for row in rows if row["admission_rule_id"] == "ADMIT_002").__setitem__("semantics_complete", "false")),
        (gate.CSV_OUTPUTS[1], gate.FIELD_COLUMNS, lambda rows: next(row for row in rows if row["field_name"] == "pdb_id").__setitem__("normalization_defined", "false")),
        (gate.CSV_OUTPUTS[2], gate.CONTEXT_COLUMNS, lambda rows: next(row for row in rows if row["context_item"] == "pdb_id_format_contract").__setitem__("implementation_ready", "false")),
        (gate.CSV_OUTPUTS[3], gate.SAFETY_COLUMNS, lambda rows: rows[0].__setitem__("observed_status", "true")),
        (gate.CSV_OUTPUTS[4], gate.ISSUE_COLUMNS, lambda rows: rows.pop()),
        (gate.CSV_OUTPUTS[0], gate.RULE_COLUMNS, lambda rows: rows[0].__setitem__("integration_applied", "true")),
    ],
)
def test_check_helper_rejects_csv_evidence_drift(tmp_path: Path, filename: str, columns: tuple[str, ...], mutate: object) -> None:
    gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1(tmp_path)
    hashes = _hashes(tmp_path)
    with (tmp_path / filename).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    mutate(rows)  # type: ignore[operator]
    _write_csv(tmp_path / filename, columns, rows)
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text()), tmp_path, hashes)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("changed_rule_ids", ["drift"]), ("removed_issue_ids", ["drift"]),
        ("remaining_issue_count", "drift"), ("recommended_next_step", "drift"),
        ("blocking_reasons", []), ("blocking_reasons", list(gate.REMAINING_ISSUE_IDS)[::-1]),
        ("canonical_mask_task_count", 6), ("rule_dependency_contract_passed_count", 14),
        ("evaluation_context_item_count", 17), ("output_file_count", 5),
        ("non_manifest_output_count", 4), ("artifact_reference_paths_not_recursively_opened", False),
        ("network_access_used_current_step", True), ("raw_structure_read_current_step", True),
        ("candidate_records_materialized_current_step", True), ("download_queue_materialized_current_step", True),
    ],
)
def test_check_helper_rejects_manifest_drift(tmp_path: Path, key: str, value: object) -> None:
    manifest = gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1(tmp_path)
    hashes = _hashes(tmp_path)
    manifest[key] = value
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(manifest, tmp_path, hashes)


def test_check_helper_rejects_source_hash_drift(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1(tmp_path)
    hashes = _hashes(tmp_path)
    monkeypatch.setattr(gate, "_source_boundary_rows", lambda: [])
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text()), tmp_path, hashes)


def test_check_helper_rejects_output_modified_after_first_hash(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1(tmp_path)
    hashes = _hashes(tmp_path)
    (tmp_path / gate.CSV_OUTPUTS[0]).write_text("drift\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text()), tmp_path, hashes)
