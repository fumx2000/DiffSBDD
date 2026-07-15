from __future__ import annotations

import ast
import copy
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

from covalent_ext import (
    covapie_bulk_download_admission_candidate_record_id_semantics_design_gate as c1_gate,
    covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate as gate,
)


CHECK_PATH = (
    REPO_ROOT
    / "scripts/check_covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1.py"
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hashes(root: Path) -> dict[str, str]:
    return {
        name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    }


def _source_hashes() -> dict[str, str]:
    return {path.as_posix(): _hash(REPO_ROOT / path) for path in gate._source_paths()}


def _load_check_module() -> object:
    spec = importlib.util.spec_from_file_location("step14au_c2_check", CHECK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _materialized(tmp_path: Path) -> tuple[dict[str, object], dict[str, str]]:
    manifest = gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1(
        tmp_path
    )
    return manifest, _hashes(tmp_path)


def _target(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    return next(row for row in rows if row[key] == value)


def test_import_has_no_materialization_side_effect(tmp_path: Path) -> None:
    code = (
        "import covalent_ext."
        "covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate"
    )
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, env=env, check=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []


def test_exact_six_outputs_and_double_materialization_are_deterministic(tmp_path: Path) -> None:
    first, first_hashes = _materialized(tmp_path)
    second = gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1(
        tmp_path
    )
    assert first == second
    assert first_hashes == _hashes(tmp_path)
    assert {path.name for path in tmp_path.iterdir()} == {*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME}


def test_manifest_has_no_timestamp_or_absolute_path(tmp_path: Path) -> None:
    manifest, _ = _materialized(tmp_path)
    payload = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in payload.lower()
    assert "/home/" not in payload


def test_exact_twelve_sources_are_tracked_regular_nonsymlinks_and_hash_stable() -> None:
    before = _source_hashes()
    rows = gate._source_boundary_rows()
    assert gate._validate_source_rows(rows)
    assert len(rows) == 12
    assert [row["source_relative_path"] for row in rows] == list(gate.SOURCE_SHA256)
    assert all(row["tracked_by_git"] == "true" for row in rows)
    assert all(row["regular_file"] == "true" and row["symlink"] == "false" for row in rows)
    assert before == gate.SOURCE_SHA256 == _source_hashes()


@pytest.mark.parametrize(
    ("mutation",),
    [
        (lambda rows: rows.pop(),),
        (lambda rows: rows.append(dict(rows[-1])),),
        (lambda rows: rows.reverse(),),
        (lambda rows: rows[0].update(source_relative_path="extra.csv"),),
        (lambda rows: rows[0].update(sha256_observed="0" * 64),),
        (lambda rows: rows[0].update(symlink="true"),),
        (lambda rows: rows[0].update(regular_file="false"),),
        (lambda rows: rows[0].update(tracked_by_git="false"),),
    ],
)
def test_source_boundary_missing_extra_reorder_drift_and_symlink_fail_closed(
    mutation: object,
) -> None:
    rows = copy.deepcopy(gate._source_boundary_rows())
    mutation(rows)  # type: ignore[operator]
    assert not gate._validate_source_rows(rows)


def test_b2_and_c1_predecessor_truth_is_validated() -> None:
    source = gate._load_source()
    assert gate._validate_source_semantics(source)
    assert source["b2_manifest"]["remaining_issue_count"] == 12
    assert source["c1_manifest"]["expected_post_integration_issue_count"] == 11
    assert source["c1_manifest"]["candidate_record_id_semantics_frozen"] is True
    assert source["c1_manifest"]["candidate_record_id_semantics_integrated"] is False
    assert ["scaffold_only", "B3"] in source["c1_manifest"]["canonical_mask_pairs"]


def test_only_three_named_rows_are_changed() -> None:
    source = gate._load_source()
    rules = gate._overlay_rule_rows(source["rule_rows"])
    fields = gate._overlay_field_rows(source["field_rows"])
    contexts = gate._overlay_context_rows(source["context_rows"])
    assert [
        row["admission_rule_id"] for row, old in zip(rules, source["rule_rows"]) if row != old
    ] == ["ADMIT_001"]
    assert [
        row["field_name"] for row, old in zip(fields, source["field_rows"]) if row != old
    ] == ["candidate_record_id"]
    assert [
        row["context_item"] for row, old in zip(contexts, source["context_rows"]) if row != old
    ] == ["candidate_record_id_contract"]


def test_all_non_target_rows_are_field_for_field_identical_to_b2() -> None:
    source = gate._load_source()
    for rows, old_rows, key, target in (
        (gate._overlay_rule_rows(source["rule_rows"]), source["rule_rows"], "admission_rule_id", "ADMIT_001"),
        (gate._overlay_field_rows(source["field_rows"]), source["field_rows"], "field_name", "candidate_record_id"),
        (gate._overlay_context_rows(source["context_rows"]), source["context_rows"], "context_item", "candidate_record_id_contract"),
    ):
        assert all(row == old for row, old in zip(rows, old_rows) if row[key] != target)


def test_admit_001_exact_overlay_values() -> None:
    source = gate._load_source()
    row = _target(gate._overlay_rule_rows(source["rule_rows"]), "admission_rule_id", "ADMIT_001")
    assert row["semantics_complete"] == "true"
    assert row["deterministic_evaluation_possible_now"] == "true"
    assert row["implementation_disposition"] == "rule_logic_ready"
    assert row["blocking_reasons"] == ""
    assert row["integration_source_stage"] == gate.PREVIOUS_STAGES[1]
    assert row["integration_applied"] == "true"
    assert row["integration_reason"] == gate.INTEGRATION_REASON


def test_candidate_record_id_field_exact_overlay_values() -> None:
    source = gate._load_source()
    row = _target(gate._overlay_field_rows(source["field_rows"]), "field_name", "candidate_record_id")
    assert all(row[key] == "true" for key in (
        "allowed_values_defined", "normalization_defined", "exact_validation_defined",
        "implementation_semantics_complete",
    ))
    assert row["semantics_evidence"] == gate.PREVIOUS_STAGES[1]
    assert row["blocking_reasons"] == ""
    assert row["integration_source_stage"] == gate.PREVIOUS_STAGES[1]
    assert row["integration_applied"] == "true"
    assert row["integration_reason"] == gate.INTEGRATION_REASON


def test_candidate_record_id_context_exact_overlay_values() -> None:
    source = gate._load_source()
    row = _target(
        gate._overlay_context_rows(source["context_rows"]),
        "context_item", "candidate_record_id_contract",
    )
    assert row["deterministic_now"] == "true"
    assert row["deterministic_after_contract_freeze"] == "true"
    assert row["exact_contract_defined"] == "true"
    assert row["implementation_ready"] == "true"
    assert row["blocking_reasons"] == ""
    assert row["integration_source_stage"] == gate.PREVIOUS_STAGES[1]
    assert row["integration_applied"] == "true"
    assert row["integration_reason"] == gate.INTEGRATION_REASON


def test_only_candidate_issue_is_removed_and_remaining_order_is_exact() -> None:
    source = gate._load_source()
    rows = gate._overlay_issue_rows(source["issue_rows"])
    assert [row["issue_id"] for row in rows] == list(gate.REMAINING_ISSUE_IDS)
    assert all(row in source["issue_rows"] for row in rows)
    assert gate.REMOVED_ISSUE_ID not in {row["issue_id"] for row in rows}


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: rows.pop(),
        lambda rows: rows.pop(1),
        lambda rows: rows.reverse(),
        lambda rows: rows[0].update(issue_id="RENAMED"),
        lambda rows: rows.append({
            key: ("NO_ISSUES" if key == "issue_id" else "") for key in gate.ISSUE_COLUMNS
        }),
    ],
)
def test_issue_transition_extra_removal_order_rename_and_no_issues_fail(
    mutate: object,
) -> None:
    source = gate._load_source()
    rows = gate._overlay_issue_rows(source["issue_rows"])
    mutate(rows)  # type: ignore[operator]
    assert not gate._validate_issue_transition_rows(rows, source["issue_rows"])


def test_complete_rule_field_and_ready_context_sets_are_exact() -> None:
    source = gate._load_source()
    rules = gate._overlay_rule_rows(source["rule_rows"])
    fields = gate._overlay_field_rows(source["field_rows"])
    contexts = gate._overlay_context_rows(source["context_rows"])
    assert tuple(row["admission_rule_id"] for row in rules if row["semantics_complete"] == "true") == gate.COMPLETE_RULE_IDS
    assert tuple(
        row["field_name"] for row in fields if row["implementation_semantics_complete"] == "true"
    ) == gate.COMPLETE_FIELD_NAMES
    assert tuple(row["context_item"] for row in contexts if row["implementation_ready"] == "true") == gate.READY_CONTEXT_ITEMS


@pytest.mark.parametrize(
    ("kind", "key", "target", "other"),
    [
        ("rule", "admission_rule_id", "ADMIT_001", "ADMIT_003"),
        ("field", "field_name", "candidate_record_id", "ligand_comp_id"),
        ("context", "context_item", "candidate_record_id_contract", "ligand_comp_id_contract"),
    ],
)
def test_correct_count_but_wrong_identity_set_fails(
    kind: str, key: str, target: str, other: str,
) -> None:
    source = gate._load_source()
    if kind == "rule":
        rows = gate._overlay_rule_rows(source["rule_rows"])
        _target(rows, key, target)["semantics_complete"] = "false"
        _target(rows, key, other)["semantics_complete"] = "true"
        assert not gate._validate_integrated_rule_rows(rows, source["rule_rows"])
    elif kind == "field":
        rows = gate._overlay_field_rows(source["field_rows"])
        _target(rows, key, target)["implementation_semantics_complete"] = "false"
        _target(rows, key, other)["implementation_semantics_complete"] = "true"
        assert not gate._validate_integrated_field_rows(rows, source["field_rows"])
    else:
        rows = gate._overlay_context_rows(source["context_rows"])
        _target(rows, key, target)["implementation_ready"] = "false"
        _target(rows, key, other)["implementation_ready"] = "true"
        assert not gate._validate_integrated_context_rows(rows, source["context_rows"])


@pytest.mark.parametrize(
    ("section", "failure_id"),
    list((key, value[0]) for key, value in gate.SECTION_FAILURE_SPECS.items()),
)
def test_each_section_failure_appends_exact_gate_issue_after_domain_blockers(
    section: str, failure_id: str,
) -> None:
    statuses = tuple((key, key != section) for key in gate.SECTION_FAILURE_SPECS)
    rows = gate._failure_issue_rows(gate._overlay_issue_rows(gate._load_source()["issue_rows"]), statuses)
    assert [row["issue_id"] for row in rows[:11]] == list(gate.REMAINING_ISSUE_IDS)
    assert [row["issue_id"] for row in rows[11:]] == [failure_id]


def test_multiple_section_failures_have_fixed_order_and_keep_domain_blockers() -> None:
    statuses = tuple((key, False) for key in gate.SECTION_FAILURE_SPECS)
    rows = gate._failure_issue_rows(gate._overlay_issue_rows(gate._load_source()["issue_rows"]), statuses)
    assert [row["issue_id"] for row in rows[:11]] == list(gate.REMAINING_ISSUE_IDS)
    assert [row["issue_id"] for row in rows[11:]] == [
        spec[0] for spec in gate.SECTION_FAILURE_SPECS.values()
    ]


def test_c1_helpers_and_admit_001_wrapper_preserve_frozen_semantics() -> None:
    assert gate._validate_c1_helpers()
    assert gate.evaluate_admit_001_candidate_record_id("HR_0002", ["HR_0002", "HR_0003"]) == {
        "admission_rule_id": "ADMIT_001", "passed": True,
        "normalized_candidate_record_id": "HR_0002", "blocking_reason": "",
    }
    assert gate.evaluate_admit_001_candidate_record_id("HR_0002", ["HR_0002", "HR_0002"])[
        "passed"
    ] is False


def test_c2_survives_c1_module_reload_without_stale_class_identity() -> None:
    assert gate._validate_c1_helpers() is True
    old_normalization_class = c1_gate.CandidateRecordIdNormalizationResult
    old_batch_class = c1_gate.CandidateRecordIdBatchEvaluationResult

    reloaded = importlib.reload(c1_gate)

    assert reloaded.CandidateRecordIdNormalizationResult is not old_normalization_class
    assert reloaded.CandidateRecordIdBatchEvaluationResult is not old_batch_class
    assert gate._validate_c1_helpers() is True
    assert gate.evaluate_admit_001_candidate_record_id(
        "HR_0002", ["HR_0002", "HR_0003"]
    ) == {
        "admission_rule_id": "ADMIT_001", "passed": True,
        "normalized_candidate_record_id": "HR_0002", "blocking_reason": "",
    }
    assert gate.evaluate_admit_001_candidate_record_id(
        "HR_0002", ["HR_0002", "HR_0002"]
    )["passed"] is False


def test_c2_materialization_is_identical_before_and_after_c1_reload(tmp_path: Path) -> None:
    before_root = tmp_path / "before"
    after_root = tmp_path / "after"
    before = gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1(
        before_root
    )
    before_hashes = _hashes(before_root)

    importlib.reload(c1_gate)

    after = gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1(
        after_root
    )
    after_hashes = _hashes(after_root)
    assert before == after
    assert {path.name for path in before_root.iterdir()} == {
        path.name for path in after_root.iterdir()
    } == {*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME}
    assert before_hashes == after_hashes
    assert all(
        (before_root / name).read_bytes() == (after_root / name).read_bytes()
        for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    )


@pytest.mark.parametrize(
    ("candidate", "batch", "passed"),
    [
        ("HR_0002", ("HR_0002",), True),
        ("ABC", ["ABC"], True),
        ("abc", ["abc"], True),
        (" HR_0002", [" HR_0002"], False),
        ("HR_0002", ["HR_0002", "HR_0002"], False),
        ("HR_0002", ["HR_0003"], False),
        ("HR_0002", ["HR_0002", " bad"], False),
        ("HR_0002", {"HR_0002"}, False),
        (1, [1], False),
    ],
)
def test_c1_helper_integration_paths(candidate: object, batch: object, passed: bool) -> None:
    assert gate.evaluate_admit_001_candidate_record_id(candidate, batch)["passed"] is passed


def test_manifest_counts_masks_and_readiness_are_truthful(tmp_path: Path) -> None:
    manifest, _ = _materialized(tmp_path)
    assert manifest["candidate_record_id_semantics_integrated"] is True
    assert manifest["admit_001_rule_logic_ready"] is True
    assert manifest["pdb_identifier_semantics_integrated"] is True
    assert (manifest["semantics_complete_rule_count"], manifest["semantics_incomplete_rule_count"]) == (4, 11)
    assert (manifest["semantics_complete_field_count"], manifest["semantics_incomplete_field_count"]) == (2, 15)
    assert (manifest["deterministic_now_context_count"], manifest["ready_evaluation_context_count"]) == (7, 7)
    assert manifest["remaining_issue_count"] == 11
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]
    assert manifest["canonical_mask_task_count"] == 5
    assert all(manifest[key] is False for key in (
        "ready_for_admission_evaluator_rule_logic_implementation",
        "ready_for_real_candidate_evaluation", "ready_for_bulk_download_now",
        "ready_for_training", "ready_to_train_now",
    ))
    assert manifest["feature_semantics_audit_required_before_training"] is True


def test_safety_audit_is_exactly_sixteen_false_observations() -> None:
    rows = gate._safety_rows()
    assert len(rows) == 16
    assert gate._validate_safety_rows(rows)
    assert all(
        row["required_status"] == "false" and row["observed_status"] == "false"
        and row["safety_passed"] == "true" and row["blocking_reason"] == ""
        for row in rows
    )


def test_forbidden_runtime_imports_are_absent() -> None:
    source = (
        REPO_ROOT
        / "src/covalent_ext/covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate.py"
    ).read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint({
        "requests", "urllib", "aiohttp", "torch", "numpy", "rdkit", "gemmi",
        "Bio", "pandas", "sklearn",
    })
    assert (
        "from covalent_ext.covapie_bulk_download_admission_"
        "candidate_record_id_semantics_design_gate import"
    ) not in source
    assert "as c1_gate" in source
    assert "c1_gate.normalize_candidate_record_id" in source
    assert "c1_gate.evaluate_candidate_record_id_batch_uniqueness" in source
    assert "c1_gate.CandidateRecordIdNormalizationResult" in source
    assert "c1_gate.CandidateRecordIdBatchEvaluationResult" in source
    assert "model.forward" not in source
    assert "trainer.fit" not in source


@pytest.mark.parametrize(
    ("filename", "key"),
    [
        (gate.CSV_OUTPUTS[0], "ADMIT_001"),
        (gate.CSV_OUTPUTS[1], "candidate_record_id"),
        (gate.CSV_OUTPUTS[2], "candidate_record_id_contract"),
        (gate.CSV_OUTPUTS[3], "network_access_used_current_step"),
        (gate.CSV_OUTPUTS[4], gate.REMAINING_ISSUE_IDS[0]),
    ],
)
def test_check_helper_rejects_csv_evidence_and_output_hash_drift(
    tmp_path: Path, filename: str, key: str,
) -> None:
    manifest, first_hashes = _materialized(tmp_path)
    path = tmp_path / filename
    path.write_text(path.read_text(encoding="utf-8").replace(key, f"{key}_DRIFT", 1), encoding="utf-8")
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(manifest, tmp_path, first_hashes)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("output_file_count", 7),
        ("canonical_mask_task_count", 6),
        ("remaining_issue_count", 12),
        ("semantics_complete_rule_count", 5),
        ("ready_for_admission_evaluator_rule_logic_implementation", True),
        ("ready_for_real_candidate_evaluation", True),
        ("ready_for_bulk_download_now", True),
        ("ready_for_training", True),
    ],
)
def test_check_helper_rejects_manifest_count_mask_and_readiness_overclaim(
    tmp_path: Path, key: str, value: object,
) -> None:
    manifest, _ = _materialized(tmp_path)
    manifest[key] = value
    (tmp_path / gate.MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    current = _hashes(tmp_path)
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(manifest, tmp_path, current)


def test_check_helper_rejects_source_hash_drift(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    manifest, current = _materialized(tmp_path)
    monkeypatch.setitem(gate.SOURCE_SHA256, next(iter(gate.SOURCE_SHA256)), "0" * 64)
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(manifest, tmp_path, current)


def test_check_helper_rejects_modified_output_after_first_hash(tmp_path: Path) -> None:
    manifest, first = _materialized(tmp_path)
    path = tmp_path / gate.CSV_OUTPUTS[0]
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(manifest, tmp_path, first)


@pytest.mark.parametrize("case", ["extra", "missing", "symlink"])
def test_check_helper_rejects_extra_missing_and_symlink_output(
    tmp_path: Path, case: str,
) -> None:
    manifest, _ = _materialized(tmp_path)
    if case == "extra":
        (tmp_path / "extra.csv").write_text("x\n", encoding="utf-8")
    elif case == "missing":
        (tmp_path / gate.CSV_OUTPUTS[0]).unlink()
    else:
        target = tmp_path / gate.CSV_OUTPUTS[0]
        payload = target.read_bytes()
        target.unlink()
        replacement = tmp_path / "replacement"
        replacement.write_bytes(payload)
        target.symlink_to(replacement.name)
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(manifest, tmp_path, {})
