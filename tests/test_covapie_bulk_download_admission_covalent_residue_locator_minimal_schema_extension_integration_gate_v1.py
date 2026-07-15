from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate
    as p2_gate,
    covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate
    as gate,
)


CHECK_PATH = REPO_ROOT / (
    "scripts/check_covapie_bulk_download_admission_covalent_residue_locator_"
    "minimal_schema_extension_integration_gate_v1.py"
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hashes(root: Path) -> dict[str, str]:
    return {name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)}


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _load_check_module() -> object:
    spec = importlib.util.spec_from_file_location("step14au_e0_p3_check", CHECK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _materialized(root: Path) -> dict[str, object]:
    return gate.run_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1(root)


def test_import_has_no_materialization_side_effect(tmp_path: Path) -> None:
    module = (
        "covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_"
        "minimal_schema_extension_integration_gate"
    )
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"], cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []


def test_exact_six_outputs_and_double_materialization_are_deterministic(tmp_path: Path) -> None:
    first = _materialized(tmp_path)
    first_hashes = _hashes(tmp_path)
    second = _materialized(tmp_path)
    assert first == second and first_hashes == _hashes(tmp_path)
    assert {path.name for path in tmp_path.iterdir()} == {*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME}
    assert all(path.is_file() and not path.is_symlink() for path in tmp_path.iterdir())


def test_manifest_has_no_timestamp_absolute_path_or_self_hash(tmp_path: Path) -> None:
    manifest = _materialized(tmp_path)
    serialized = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in serialized.lower()
    assert "/home/" not in serialized
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]


def test_exact_twelve_sources_are_ordered_tracked_regular_and_hash_stable() -> None:
    before = {path.as_posix(): _hash(REPO_ROOT / path) for path in gate._source_paths()}
    rows = gate._source_boundary_rows()
    assert gate._validate_source_boundary_rows(rows)
    assert len(rows) == 12
    assert [row["source_relative_path"] for row in rows] == list(gate.SOURCE_SHA256)
    assert all(row["tracked_by_git"] == row["regular_file"] == "true" for row in rows)
    assert all(row["symlink"] == "false" for row in rows)
    assert before == gate.SOURCE_SHA256


@pytest.mark.parametrize(
    "mutation",
    [
        lambda rows: rows.pop(),
        lambda rows: rows.append(dict(rows[-1])),
        lambda rows: rows.reverse(),
        lambda rows: rows[0].update(source_relative_path="extra.csv"),
        lambda rows: rows[0].update(sha256_observed="0" * 64),
        lambda rows: rows[0].update(symlink="true"),
        lambda rows: rows[0].update(regular_file="false"),
        lambda rows: rows[0].update(tracked_by_git="false"),
    ],
)
def test_source_boundary_drift_fails_closed(mutation: object) -> None:
    rows = copy.deepcopy(gate._source_boundary_rows())
    mutation(rows)  # type: ignore[operator]
    assert not gate._validate_source_boundary_rows(rows)


def test_d2_predecessor_truth_and_admit_004_original_row_are_exact() -> None:
    source = gate._load_source()
    assert gate._validate_d2_predecessor(source)
    assert len(source["d2_rule_rows"]) == 15
    assert len(source["d2_field_rows"]) == 17
    assert len(source["d2_context_rows"]) == 18
    assert len(source["d2_issue_rows"]) == 10
    assert not set(p2_gate.PROPOSED_FIELD_NAMES).intersection(
        row["field_name"] for row in source["d2_field_rows"]
    )
    assert next(
        row for row in source["d2_rule_rows"] if row["admission_rule_id"] == "ADMIT_004"
    ) == gate._expected_admit_004()
    assert source["d2_manifest"]["candidate_record_id_semantics_integrated"] is True
    assert source["d2_manifest"]["pdb_identifier_semantics_integrated"] is True
    assert source["d2_manifest"]["ligand_comp_id_semantics_integrated"] is True


def test_p2_predecessor_truth_is_exact() -> None:
    source = gate._load_source()
    assert gate._validate_p2_predecessor(source)
    assert len(source["p2_contract_rows"]) == 40
    assert len(source["p2_backfill_rows"]) == 11
    assert len(source["p2_source_rows"]) == 24
    assert len(source["p2_safety_rows"]) == 20
    assert [row["issue_id"] for row in source["p2_issue_rows"]] == [
        *gate.REMAINING_P2_FOLLOWUP_ISSUE_IDS, *gate.RESOLVED_P2_ISSUE_IDS,
    ]
    assert source["p2_manifest"]["insertion_unknown_sample_count"] == 11
    assert source["p2_manifest"]["fully_provable_pre_download_sample_count"] == 0
    assert source["p2_manifest"]["covalent_residue_locator_schema_extension_integrated"] is False


def test_admit_004_changes_exactly_four_columns_and_keeps_blockers() -> None:
    source = gate._load_source()
    old = next(row for row in source["d2_rule_rows"] if row["admission_rule_id"] == "ADMIT_004")
    rows = gate._overlay_rule_rows(source["d2_rule_rows"])
    row = next(item for item in rows if item["admission_rule_id"] == "ADMIT_004")
    assert {key for key in gate.RULE_COLUMNS if row[key] != old[key]} == {
        "candidate_field_dependencies", "integration_source_stage",
        "integration_applied", "integration_reason",
    }
    assert row["candidate_field_dependencies"] == gate.ADMIT_004_NEW_DEPENDENCIES
    assert row["blocking_reasons"] == gate.ADMIT_004_BLOCKERS
    assert row["semantics_complete"] == row["deterministic_evaluation_possible_now"] == "false"
    assert row["implementation_disposition"] == "interface_only_pending_semantics"
    assert row["integration_source_stage"] == gate.PREVIOUS_STAGES[1]
    assert row["integration_applied"] == "true"
    assert row["integration_reason"] == gate.INTEGRATION_REASON
    assert gate._validate_integrated_rule_rows(rows, source["d2_rule_rows"])


def test_other_fourteen_rule_rows_are_field_for_field_unchanged() -> None:
    source = gate._load_source()
    rows = gate._overlay_rule_rows(source["d2_rule_rows"])
    assert sum(row != old for row, old in zip(rows, source["d2_rule_rows"])) == 1
    assert all(
        row == old for row, old in zip(rows, source["d2_rule_rows"])
        if row["admission_rule_id"] != "ADMIT_004"
    )


def test_field_extension_preserves_seventeen_and_appends_exact_five() -> None:
    source = gate._load_source()
    rows = gate._overlay_field_rows(source["d2_field_rows"])
    assert rows[:17] == source["d2_field_rows"]
    assert rows[17:] == gate._new_field_rows()
    assert [row["field_name"] for row in rows[17:]] == list(p2_gate.PROPOSED_FIELD_NAMES)
    assert len(rows) == len({row["field_name"] for row in rows}) == 22
    assert gate._validate_integrated_field_rows(rows, source["d2_field_rows"])


@pytest.mark.parametrize("index", range(5))
def test_each_new_field_row_is_exact(index: int) -> None:
    row = gate._new_field_rows()[index]
    assert tuple(row) == gate.FIELD_COLUMNS
    assert row["field_name"] == p2_gate.PROPOSED_FIELD_NAMES[index]
    assert row["requirement_phase"] == "pre_download"
    assert row["candidate_record_field"] == "true"
    assert row["producer_scope"] == "candidate_metadata_provider"
    assert row["dependent_rules"] == "ADMIT_004"
    assert row["batch_context_required"] == "false"
    assert row["evaluation_context_dependencies"] == "covalent_residue_identity_contract"
    assert row["field_contract_mapping_passed"] == "true"
    assert row["source_stage"] == row["integration_source_stage"] == gate.PREVIOUS_STAGES[1]
    assert row["integration_applied"] == "true"
    assert row["integration_reason"] == gate.INTEGRATION_REASON


def test_complete_field_count_and_exact_set_are_seven() -> None:
    source = gate._load_source()
    rows = gate._overlay_field_rows(source["d2_field_rows"])
    complete = tuple(
        row["field_name"] for row in rows if row["implementation_semantics_complete"] == "true"
    )
    assert complete == gate.COMPLETE_FIELD_NAMES and len(complete) == 7
    drift = copy.deepcopy(rows)
    drift[0]["implementation_semantics_complete"] = "false"
    drift[3]["implementation_semantics_complete"] = "true"
    assert sum(row["implementation_semantics_complete"] == "true" for row in drift) == 7
    assert not gate._validate_integrated_field_rows(drift, source["d2_field_rows"])


def test_contexts_are_all_unchanged_and_identity_context_remains_blocked() -> None:
    source = gate._load_source()
    rows = gate._overlay_context_rows(source["d2_context_rows"])
    assert rows == source["d2_context_rows"] and len(rows) == 18
    identity = next(row for row in rows if row["context_item"] == "covalent_residue_identity_contract")
    assert identity["deterministic_now"] == identity["exact_contract_defined"] == "false"
    assert identity["implementation_ready"] == identity["integration_applied"] == "false"
    assert identity["blocking_reasons"] == "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED"
    assert gate._validate_integrated_context_rows(rows, source["d2_context_rows"])


def test_domain_issues_are_all_unchanged_and_p2_transition_is_separate() -> None:
    source = gate._load_source()
    rows = gate._overlay_issue_rows(source["d2_issue_rows"])
    assert rows == source["d2_issue_rows"]
    assert tuple(row["issue_id"] for row in rows) == gate.REMAINING_ISSUE_IDS
    assert "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED" in gate.REMAINING_ISSUE_IDS
    assert "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED" in gate.REMAINING_ISSUE_IDS
    assert gate._validate_issue_preservation_rows(rows, source["d2_issue_rows"])
    result = gate._build_materialization(source)
    manifest = gate._manifest_payload(result, {})
    assert manifest["resolved_p2_issue_ids"] == list(gate.RESOLVED_P2_ISSUE_IDS)
    assert manifest["remaining_p2_followup_issue_ids"] == list(gate.REMAINING_P2_FOLLOWUP_ISSUE_IDS)
    assert manifest["remaining_issue_count"] == 10


@pytest.mark.parametrize("mutation", ["remove", "extra", "reverse", "rename", "no_issues"])
def test_issue_drift_fails_closed(mutation: str) -> None:
    source = gate._load_source()
    rows = copy.deepcopy(source["d2_issue_rows"])
    if mutation == "remove":
        rows.pop()
    elif mutation == "extra":
        rows.append(dict(rows[-1]))
    elif mutation == "reverse":
        rows.reverse()
    elif mutation == "rename":
        rows[0]["issue_id"] = "RENAMED"
    else:
        rows[0]["issue_id"] = "NO_ISSUES"
    assert not gate._validate_issue_preservation_rows(rows, source["d2_issue_rows"])


def test_p2_helpers_cover_positive_and_negative_cases() -> None:
    assert gate._validate_p2_helpers()


def test_p2_reload_changes_result_class_identity_but_p3_remains_deterministic(tmp_path: Path) -> None:
    before_class = p2_gate.CovalentResidueLocatorNamespaceResult
    before_manifest = _materialized(tmp_path)
    before_hashes = _hashes(tmp_path)
    importlib.reload(p2_gate)
    assert p2_gate.CovalentResidueLocatorNamespaceResult is not before_class
    assert gate._validate_p2_helpers()
    after_manifest = _materialized(tmp_path)
    assert before_manifest == after_manifest and before_hashes == _hashes(tmp_path)


@pytest.mark.parametrize(
    "section",
    [
        "source_boundary", "d2_predecessor", "p2_predecessor", "p2_helpers",
        "integrated_rules", "integrated_fields", "integrated_contexts",
        "issue_preservation", "safety",
    ],
)
def test_each_section_failure_closes_integration_without_polluting_domain_issues(section: str) -> None:
    source = gate._load_source()
    kwargs: dict[str, object] = {}
    if section == "source_boundary":
        rows = gate._source_boundary_rows(); rows.pop(); kwargs["source_rows"] = rows
    elif section == "d2_predecessor":
        source = copy.deepcopy(source); source["d2_manifest"]["integrated_field_count"] = 99
    elif section == "p2_predecessor":
        source = copy.deepcopy(source); source["p2_manifest"]["proposed_extension_field_count"] = 4
    elif section == "p2_helpers":
        kwargs["helper_status"] = False
    elif section == "integrated_rules":
        rows = gate._overlay_rule_rows(source["d2_rule_rows"]); rows[0]["semantics_complete"] = "false"; kwargs["rule_rows"] = rows
    elif section == "integrated_fields":
        rows = gate._overlay_field_rows(source["d2_field_rows"]); rows[-1]["field_name"] = "drift"; kwargs["field_rows"] = rows
    elif section == "integrated_contexts":
        rows = gate._overlay_context_rows(source["d2_context_rows"]); rows[0]["implementation_ready"] = "false"; kwargs["context_rows"] = rows
    elif section == "issue_preservation":
        rows = gate._overlay_issue_rows(source["d2_issue_rows"]); rows.pop(); kwargs["issue_rows"] = rows
    else:
        rows = gate._safety_rows(); rows[0]["observed_status"] = "true"; kwargs["safety_rows"] = rows
    result = gate._build_materialization(source, **kwargs)  # type: ignore[arg-type]
    manifest = gate._manifest_payload(result, {})
    assert result["all_checks_passed"] is False
    assert manifest["covalent_residue_locator_schema_extension_integrated"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert gate.SECTION_FAILURE_IDS[section] in manifest["validation_failures"]
    assert manifest["blocking_reasons"] == list(gate.REMAINING_ISSUE_IDS)
    assert manifest["validation_failures"] == [gate.SECTION_FAILURE_IDS[section]]
    assert not set(manifest["validation_failures"]).intersection(manifest["blocking_reasons"])
    assert [row["issue_id"] for row in result["issue_rows"]] == list(gate.REMAINING_ISSUE_IDS)


def test_normal_manifest_contract_and_readiness(tmp_path: Path) -> None:
    manifest = _materialized(tmp_path)
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == list(gate.REMAINING_ISSUE_IDS)
    assert manifest["validation_failures"] == []
    assert manifest["covalent_residue_locator_schema_extension_integrated"] is True
    assert manifest["integrated_field_count"] == 22
    assert manifest["integrated_context_count"] == 18
    assert manifest["remaining_issue_count"] == 10
    assert manifest["insertion_unknown_sample_count"] == 11
    assert manifest["fully_provable_pre_download_sample_count"] == 0
    assert manifest["admit_004_rule_logic_ready"] is False
    assert manifest["ready_for_e1_residue_identity_semantics_design"] is False
    assert manifest["parser_insertion_code_support_required"] is True
    assert manifest["provider_provenance_binding_required"] is True
    assert all(manifest[key] is False for key in (
        "ready_for_admission_evaluator_rule_logic_implementation",
        "ready_for_real_candidate_evaluation", "ready_for_bulk_download_now",
        "ready_for_training", "ready_to_train_now",
    ))
    assert manifest["feature_semantics_audit_required_before_training"] is True


@pytest.mark.parametrize(
    "target,mutation",
    [
        ("rules", lambda rows: rows[0].update(semantics_complete="false")),
        ("fields", lambda rows: rows[0].update(source_value_contract="drift")),
        ("fields", lambda rows: rows[-1].update(source_value_contract="drift")),
        ("fields", lambda rows: rows.reverse()),
        ("contexts", lambda rows: rows[0].update(implementation_ready="false")),
        ("issues", lambda rows: rows.pop()),
    ],
)
def test_check_rejects_disk_matrix_drift(tmp_path: Path, target: str, mutation: object) -> None:
    _materialized(tmp_path)
    index = {"rules": 0, "fields": 1, "contexts": 2, "issues": 4}[target]
    path = tmp_path / gate.CSV_OUTPUTS[index]
    rows = _csv(path)
    mutation(rows)  # type: ignore[operator]
    _write_csv(path, rows)
    check = _load_check_module()
    hashes = _hashes(tmp_path)
    manifest = json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text())
    with pytest.raises(AssertionError):
        check._validate_manifest_and_outputs(manifest, tmp_path, hashes)


@pytest.mark.parametrize(
    "key,value",
    [
        ("output_file_count", 5), ("predecessor_field_count", 18),
        ("integrated_field_count", 21), ("semantics_complete_field_count", 6),
        ("admit_004_rule_logic_ready", True),
        ("ready_for_e1_residue_identity_semantics_design", True),
        ("insertion_unknown_sample_count", 10),
        ("fully_provable_pre_download_sample_count", 1),
        ("remaining_issue_count", 9), ("ready_for_real_candidate_evaluation", True),
        ("ready_for_bulk_download_now", True), ("ready_for_training", True),
    ],
)
def test_check_rejects_manifest_overclaim_or_count_drift(
    tmp_path: Path, key: str, value: object,
) -> None:
    manifest = _materialized(tmp_path)
    manifest[key] = value
    check = _load_check_module()
    with pytest.raises(AssertionError):
        check._validate_manifest_and_outputs(manifest, tmp_path, _hashes(tmp_path))


def test_check_rejects_output_hash_and_manifest_hash_drift(tmp_path: Path) -> None:
    manifest = _materialized(tmp_path)
    check = _load_check_module()
    hashes = _hashes(tmp_path)
    stale = dict(hashes); stale[gate.CSV_OUTPUTS[0]] = "0" * 64
    with pytest.raises(AssertionError):
        check._validate_manifest_and_outputs(manifest, tmp_path, stale)
    manifest = copy.deepcopy(manifest)
    manifest["output_sha256"][gate.CSV_OUTPUTS[0]] = "0" * 64
    with pytest.raises(AssertionError):
        check._validate_manifest_and_outputs(manifest, tmp_path, hashes)


def test_check_rejects_source_hash_constant_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _materialized(tmp_path)
    first_hashes = _hashes(tmp_path)
    check = _load_check_module()
    drifted = dict(check.gate.SOURCE_SHA256)
    first_source = next(iter(drifted))
    drifted[first_source] = "0" * 64
    monkeypatch.setattr(check.gate, "SOURCE_SHA256", drifted)
    with pytest.raises(AssertionError):
        check._validate_manifest_and_outputs(manifest, tmp_path, first_hashes)


def test_check_rejects_output_modified_after_first_hash(tmp_path: Path) -> None:
    manifest = _materialized(tmp_path)
    first_hashes = _hashes(tmp_path)
    path = tmp_path / gate.CSV_OUTPUTS[0]
    path.write_bytes(path.read_bytes() + b"\n")
    check = _load_check_module()
    with pytest.raises(AssertionError):
        check._validate_manifest_and_outputs(manifest, tmp_path, first_hashes)


@pytest.mark.parametrize("kind", ["extra", "missing", "symlink"])
def test_check_rejects_extra_missing_or_symlink_output(tmp_path: Path, kind: str) -> None:
    _materialized(tmp_path)
    if kind == "extra":
        (tmp_path / "extra.csv").write_text("x\n")
    elif kind == "missing":
        (tmp_path / gate.CSV_OUTPUTS[0]).unlink()
    else:
        path = tmp_path / gate.CSV_OUTPUTS[0]
        path.unlink(); path.symlink_to(tmp_path / gate.CSV_OUTPUTS[1])
    check = _load_check_module()
    with pytest.raises(AssertionError):
        check._validate_exact_output_files(tmp_path)


def test_production_static_boundary_and_p2_alias_import() -> None:
    path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not imports.intersection({
        "requests", "urllib", "aiohttp", "torch", "numpy", "rdkit", "Bio", "gemmi",
        "pandas", "sklearn", "inspect", "ast", "importlib",
    })
    assert " as p2_gate" in source
    assert "importlib.reload" not in source
    assert "model.forward" not in source and "trainer.fit" not in source
    assert "inspect.getsource" not in source and "Path(__file__).read_text" not in source
    assert "data/raw" not in source
