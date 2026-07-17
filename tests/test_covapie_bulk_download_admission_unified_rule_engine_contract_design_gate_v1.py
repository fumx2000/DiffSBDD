from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_unified_rule_engine_contract_design_gate as gate,
)


def _checker_module():
    path = gate.REPO_ROOT / "scripts" / (
        "check_covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1.py"
    )
    spec = importlib.util.spec_from_file_location("phase1_checker", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _materialize(root: Path) -> dict[str, object]:
    return gate.run_covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1(
        root
    )


def test_exact21_order_structure_and_sha_contract() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 21
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS
    assert all(
        record.expected_sha256
        == record.base_tree_sha256
        == record.filesystem_sha256
        == hashlib.sha256(record.content_bytes).hexdigest()
        for record in snapshot.records
    )


def test_newly_discovered_admit001_to_003_source_hashes_are_fully_frozen() -> None:
    assert tuple(gate.SOURCE_SHA256[path] for path in gate.SOURCE_PATHS[:3]) == (
        "3246a131a3815aa184338637edef6d8c9020b2dc23f41794e5697812467d269b",
        "c78ed4986551913dea75dc220609f97154941ebda5afffaa84ff252e9d36df83",
        "8d616a02b5f87ea98be3029879d55acd3c06c26e7286a46cb293bd6a4a7f6e11",
    )


def test_all_structure_checks_precede_first_source_read(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    original_structure = gate._structural_source_check
    original_git = gate._git

    def structure(path: Path, root: Path) -> bool:
        events.append(f"structure:{path}")
        return original_structure(path, root)

    def git(arguments, root, *, text=True):
        if arguments and arguments[0] == "show" and len(arguments) == 2:
            events.append(f"read:{arguments[1]}")
        return original_git(arguments, root, text=text)

    monkeypatch.setattr(gate, "_structural_source_check", structure)
    monkeypatch.setattr(gate, "_git", git)
    gate.build_frozen_source_snapshot()
    first_read = next(index for index, value in enumerate(events) if value.startswith("read:"))
    assert first_read == 21
    assert all(value.startswith("structure:") for value in events[:first_read])


@pytest.mark.parametrize("failure", ["missing", "symlink"])
def test_source_missing_or_symlink_fails_closed(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    target = gate.REPO_ROOT / gate.SOURCE_PATHS[0]
    original_lstat = gate.os.lstat

    def lstat(path):
        if Path(path) == target:
            if failure == "missing":
                raise FileNotFoundError(path)
            original = original_lstat(path)
            values = list(original)
            values[stat.ST_MODE] = stat.S_IFLNK | 0o777
            return os.stat_result(values)
        return original_lstat(path)

    monkeypatch.setattr(gate.os, "lstat", lstat)
    state = gate.build_design_state()
    assert state["contract_success_count"] == 0
    assert state["routing_success_count"] == 0
    assert state["issue_success_count"] == 0
    assert state["design_readiness"] is False
    assert state["all_checks_passed"] is False


def test_source_hash_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original_git = gate._git
    changed = False

    def git(arguments, root, *, text=True):
        nonlocal changed
        result = original_git(arguments, root, text=text)
        if arguments[:1] == ["show"] and len(arguments) == 2 and text is False and not changed:
            changed = True
            return subprocess.CompletedProcess(result.args, 0, result.stdout + b"drift", result.stderr)
        return result

    monkeypatch.setattr(gate, "_git", git)
    state = gate.build_design_state()
    assert state["contract_success_count"] == 0
    assert state["routing_success_count"] == 0
    assert state["issue_success_count"] == 0
    assert state["design_readiness"] is False
    assert state["all_checks_passed"] is False


def test_expected_base_commit_identity_and_subject_are_frozen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_git = gate._git

    def missing_base(arguments, root, *, text=True):
        if arguments == [
            "cat-file",
            "-e",
            f"{gate.EXPECTED_BASE_COMMIT}^{{commit}}",
        ]:
            return subprocess.CompletedProcess(arguments, 1, "", "missing")
        return original_git(arguments, root, text=text)

    monkeypatch.setattr(gate, "_git", missing_base)
    with pytest.raises(ValueError, match="object is missing"):
        gate.build_frozen_source_snapshot()

    def wrong_base_subject(arguments, root, *, text=True):
        if arguments == [
            "show",
            "-s",
            "--format=%s",
            gate.EXPECTED_BASE_COMMIT,
        ]:
            return subprocess.CompletedProcess(arguments, 0, "wrong subject\n", "")
        return original_git(arguments, root, text=text)

    monkeypatch.setattr(gate, "_git", wrong_base_subject)
    with pytest.raises(ValueError, match="subject mismatch"):
        gate.build_frozen_source_snapshot()

    observed: list[tuple[str, ...]] = []

    def record_metadata(arguments, root, *, text=True):
        observed.append(tuple(arguments))
        return original_git(arguments, root, text=text)

    monkeypatch.setattr(gate, "_git", record_metadata)
    assert gate.build_design_state()["all_checks_passed"] is True
    assert ("show", "-s", "--format=%s", gate.EXPECTED_BASE_COMMIT) in observed
    assert ("show", "-s", "--format=%s", "HEAD") not in observed


def test_expected_base_or_successor_head_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert gate.build_design_state()["all_checks_passed"] is True
    successor = "f" * 40
    assert successor != gate.EXPECTED_BASE_COMMIT
    original_git = gate._git
    observed: list[tuple[str, ...]] = []

    def successor_metadata(arguments, root, *, text=True):
        observed.append(tuple(arguments))
        if arguments == [
            "merge-base",
            "--is-ancestor",
            gate.EXPECTED_BASE_COMMIT,
            successor,
        ]:
            return subprocess.CompletedProcess(arguments, 0, "", "")
        return original_git(arguments, root, text=text)

    monkeypatch.setattr(gate, "_git", successor_metadata)
    state = gate.build_design_state(head_ref=successor)
    assert state["all_checks_passed"] is True
    assert (
        "merge-base",
        "--is-ancestor",
        gate.EXPECTED_BASE_COMMIT,
        successor,
    ) in observed
    assert not any(arguments[:1] == ("rev-parse",) for arguments in observed)


def test_non_descendant_head_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original_git = gate._git

    def non_descendant(arguments, root, *, text=True):
        if arguments == [
            "merge-base",
            "--is-ancestor",
            gate.EXPECTED_BASE_COMMIT,
            "HEAD",
        ]:
            return subprocess.CompletedProcess(arguments, 1, "", "not ancestor")
        return original_git(arguments, root, text=text)

    monkeypatch.setattr(gate, "_git", non_descendant)
    state = gate.build_design_state()
    assert state["contract_success_count"] == 0
    assert state["routing_success_count"] == 0
    assert state["issue_success_count"] == 0
    assert state["design_readiness"] is False
    assert state["all_checks_passed"] is False


def test_ast_discovers_exactly_four_formal_evaluators_without_execution() -> None:
    state = gate.build_design_state()
    inventory = state["predecessor"]["callables"]
    assert tuple(row["evaluator_callable_name"] for row in inventory) == (
        "evaluate_admit_001_candidate_record_id",
        "evaluate_admit_002_pdb_identifier",
        "evaluate_admit_003_ligand_comp_id",
        "evaluate_admit_004",
    )
    assert all(name not in gate.__dict__ for name in (
        "evaluate_admit_001_candidate_record_id",
        "evaluate_admit_002_pdb_identifier",
        "evaluate_admit_003_ligand_comp_id",
        "evaluate_admit_004",
    ))


def test_current_head_and_phase1_production_have_no_dispatch_runtime() -> None:
    result = subprocess.run(
        [
            "git",
            "grep",
            "-n",
            "-E",
            "def evaluate_admission_rule|class UnifiedAdmissionRuleEvaluation|class UnifiedAdmissionDispatchError",
            gate.EXPECTED_BASE_COMMIT,
            "--",
            "*.py",
        ],
        cwd=gate.REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1 and result.stdout == ""
    tree = ast.parse(Path(gate.__file__).read_bytes())
    names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    assert not names & {
        "evaluate_admission_rule",
        "UnifiedAdmissionRuleEvaluation",
        "UnifiedAdmissionDispatchError",
    }


def test_legacy_dict_results_are_incompatible_with_admit004_frozen_dataclass() -> None:
    state = gate.build_design_state()
    rows = state["routing_rows"]
    assert [row["evaluator_result_type"] for row in rows[:3]] == [
        "legacy_mutable_dict"
    ] * 3
    assert rows[3]["evaluator_result_type"] == "Admit004EvaluationResult"
    assert [row["result_adapter_contract_status"] for row in rows[:3]] == [
        "unresolved"
    ] * 3
    assert rows[3]["result_adapter_contract_status"] == "design_ready"


def test_public_api_signature_and_single_rule_boundaries() -> None:
    rows = gate.build_design_state()["public_api_rows"]
    values = {row["contract_item"]: row["contract_value"] for row in rows}
    assert values["conceptual_signature"].startswith(
        "evaluate_admission_rule(admission_rule_id: str, candidate_record: Mapping[str, object]"
    )
    assert values["dispatch_cardinality"] == "single_rule_only"
    assert values["evaluate_all_rules"] == "not_provided"
    assert values["combined_candidate_verdict"] == "not_generated"
    assert values["engine_context_behavior"] == "pass_through_explicit_context_only"


def test_unified_result_exact13_and_outcome_contract() -> None:
    rows = gate.build_design_state()["result_rows"]
    fields = tuple(
        (row["field_name"], row["field_type"])
        for row in rows
        if row["contract_kind"] == "result_field"
    )
    assert fields == gate.RESULT_FIELDS
    values = {(row["contract_kind"], row["field_name"]): row["contract_value"] for row in rows}
    assert values[("result_invariant", "outcome_vocabulary")] == "passed|blocked|invalid|rejected"
    assert values[("result_invariant", "passed")] == "true_iff_outcome_passed"
    assert values[("result_invariant", "blocks_candidate")] == "true_iff_outcome_not_passed"
    assert values[("result_invariant", "evaluator_io_used")] == "false"


def test_rule_outcome_subsets_do_not_freeze_global_precedence() -> None:
    rows = gate.build_design_state()["result_rows"]
    values = {(row["contract_kind"], row["field_name"]): row["contract_value"] for row in rows}
    assert values[("rule_outcome_subset", "ADMIT_004")] == "passed|blocked|invalid"
    assert values[("rule_outcome_subset", "ADMIT_005")] == "passed|rejected|invalid"
    assert values[("aggregation_boundary", "global_engine_precedence")] == "not_frozen"
    assert values[("aggregation_boundary", "local_precedence_promoted_globally")] == "false"


def test_dispatch_error_exact6_exact5_and_failure_distinctions() -> None:
    rows = gate.build_design_state()["public_api_rows"]
    assert tuple(
        (row["contract_item"], row["contract_value"])
        for row in rows
        if row["contract_area"] == "dispatch_error_field"
    ) == gate.DISPATCH_ERROR_FIELDS
    assert tuple(
        row["contract_item"]
        for row in rows
        if row["contract_area"] == "dispatch_error_code"
    ) == gate.DISPATCH_ERROR_CODES
    values = {row["contract_item"]: row["contract_value"] for row in rows}
    assert values["unknown_vs_known_unsupported"] == "distinct"
    assert values["known_unsupported_default_passed"] == "forbidden"
    assert values["invalid_or_missing_context_invokes_evaluator"] == "false"


def test_routing_exact15_and_context_partition() -> None:
    rows = gate.build_design_state()["routing_rows"]
    assert len(rows) == 15
    assert tuple(row["admission_rule_id"] for row in rows) == tuple(
        f"ADMIT_{index:03d}" for index in range(1, 16)
    )
    assert rows[0]["batch_context_dependencies"] == "batch_candidate_record_ids"
    assert rows[8]["batch_context_dependencies"] == "batch_duplicate_identity_keys"
    assert rows[11]["download_result_context_dependencies"]
    assert rows[12]["download_result_context_dependencies"]
    assert rows[13]["stage_authorization_context_dependencies"] == (
        "current_step|current_stage_download_authorized"
    )
    assert rows[14]["stage_authorization_context_dependencies"] == (
        "current_step|current_stage_training_authorized"
    )


def test_admit004_evidence_context_is_caller_provided_pass_through_only() -> None:
    state = gate.build_design_state()
    row = state["routing_rows"][3]
    assert row["evaluation_context_dependencies"] == (
        "covalent_residue_identity_contract|covalent_residue_identity_evidence_context"
    )
    public = {row["contract_item"]: row["contract_value"] for row in state["public_api_rows"]}
    assert public["engine_context_behavior"] == "pass_through_explicit_context_only"
    assert public["provider_evidence_construction"] == "forbidden"
    assert public["engine_filesystem_access"] == "forbidden"
    assert public["engine_network_access"] == "forbidden"


def test_known_unsupported_rules_never_default_passed() -> None:
    rows = gate.build_design_state()["routing_rows"]
    assert all(row["callable_discovered"] == "false" for row in rows[4:])
    assert all(row["engine_registration_status"] == "unsupported" for row in rows[4:])
    assert all(
        row["routing_disposition"] == "known_unsupported_fail_closed" for row in rows[4:]
    )


def test_issue_exact12_preserves_exact9_and_provider_count11() -> None:
    state = gate.build_design_state()
    issues = state["issue_rows"]
    predecessor = gate._csv_document(state["source_snapshot"], gate.E1E3_ISSUE_PATH).rows
    assert len(issues) == 12
    assert issues[:9] == [dict(row) for row in predecessor]
    assert [row["issue_id"] for row in issues[9:]] == [
        "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_SEMANTICS_UNRESOLVED",
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    ]
    provider = next(
        row for row in issues if row["issue_id"] == "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"
    )
    assert (provider["status"], provider["severity"], provider["issue_count"]) == (
        "open",
        "blocking",
        "11",
    )


def test_readiness_does_not_overclaim(tmp_path: Path) -> None:
    result = _materialize(tmp_path / "out")
    manifest = result["manifest"]
    assert all(manifest[name] is True for name in gate.TRUE_READINESS)
    assert all(manifest[name] is False for name in gate.FALSE_READINESS)
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP


def test_deterministic_double_materialization(tmp_path: Path) -> None:
    roots = (tmp_path / "one", tmp_path / "two")
    for root in roots:
        _materialize(root)
    assert {
        name: (roots[0] / name).read_bytes() for name in gate.OUTPUT_FILES
    } == {
        name: (roots[1] / name).read_bytes() for name in gate.OUTPUT_FILES
    }
    assert not list(tmp_path.rglob("*.tmp"))
    assert not list(tmp_path.rglob("*.part"))


@pytest.mark.parametrize("tamper", ["missing", "extra", "symlink", "hash", "overclaim"])
def test_checker_fails_closed_for_output_tampering(tmp_path: Path, tamper: str) -> None:
    root = tmp_path / "out"
    _materialize(root)
    checker = _checker_module()
    if tamper == "missing":
        (root / gate.PUBLIC_API_FILENAME).unlink()
    elif tamper == "extra":
        (root / "extra.txt").write_text("extra", encoding="utf-8")
    elif tamper == "symlink":
        victim = tmp_path / "victim"
        victim.write_text("victim", encoding="utf-8")
        path = root / gate.PUBLIC_API_FILENAME
        path.unlink()
        path.symlink_to(victim)
    elif tamper == "hash":
        (root / gate.RESULT_FILENAME).write_bytes(b"changed")
    else:
        path = root / gate.MANIFEST_FILENAME
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["ready_for_training"] = True
        path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises((ValueError, OSError)):
        checker.check_covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1(
            root
        )


def test_materializer_symlink_victim_is_not_rewritten(tmp_path: Path) -> None:
    root = tmp_path / "out"
    root.mkdir()
    victim = tmp_path / "victim.txt"
    victim.write_text("unchanged", encoding="utf-8")
    (root / gate.PUBLIC_API_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError):
        _materialize(root)
    assert victim.read_text(encoding="utf-8") == "unchanged"
    assert tuple(entry.name for entry in root.iterdir()) == (gate.PUBLIC_API_FILENAME,)


def test_production_and_checker_are_standard_library_only() -> None:
    checker = _checker_module()
    checker._assert_no_runtime_implementation()


def test_import_smoke_has_no_output_or_materialization_side_effect() -> None:
    output_root = gate.REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    before = output_root.exists()
    command = (
        "import covalent_ext."
        "covapie_bulk_download_admission_unified_rule_engine_contract_design_gate"
    )
    result = subprocess.run(
        [sys.executable, "-c", command],
        cwd=gate.REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(gate.REPO_ROOT / "src")},
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert output_root.exists() is before


def test_success_outputs_and_checker_direct_evidence(tmp_path: Path) -> None:
    root = tmp_path / "out"
    _materialize(root)
    checked = _checker_module().check_covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1(
        root
    )
    assert checked["all_checks_passed"] is True
    assert checked["output_file_count"] == 6
    assert set(checked["output_sha256"]) == set(gate.OUTPUT_FILES)
