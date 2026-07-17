#!/usr/bin/env python3
"""Fail-closed checker for the ADMIT_005 standalone evaluator interface."""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import inspect
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from types import ModuleType
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate
    as oracle,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_005_rule_logic_interface as interface,
)


EXPECTED_OUTPUT_SHA256 = {
    interface.CONTRACT_FILENAME: "ddc25a44c212abdde590669f6d5a92125cad0657360eae87037fdde7c6c834e0",
    interface.TRUTH_FILENAME: "695c187ccd297671b74ae33a95c52e2c38f0f5d1c46b253b8dd84c682499b10f",
    interface.SOURCE_AUDIT_FILENAME: "a5b3c01374dfdcf5bf25c1717b8481880fa8c0e2fab7cd215ea3784bdb306e0c",
    interface.SAFETY_FILENAME: "84882940cc7e8ffe99b80635d8c58a94cc6968d20eb307e07305046c1cb31e48",
    interface.ISSUE_FILENAME: "27bed0fd2250e0c64c704771fdb2bca8f5e50554d99f53694dc579f85f578d1f",
    interface.MANIFEST_FILENAME: "304e6d83bd36faba951bfa024c9fb96d70534e3c49b556c79b9d2acdcec5c2b8",
}


def _assert(condition: bool, message: str) -> None:
    if condition is not True:
        raise AssertionError(message)


def _result_tuple(result: interface.Admit005EvaluationResult) -> tuple[Any, ...]:
    return tuple(getattr(result, field.name) for field in fields(result))


def _oracle_expected(residue: object, atom_name: object) -> tuple[Any, ...]:
    scope = oracle.classify_admit_004_admit_005_atom_scope_design(
        residue, atom_name
    )
    atom = oracle.validate_generic_covalent_residue_atom_name(atom_name)
    canonical_residue = scope.canonical_residue_name or ""
    if scope.canonical_residue_name is None:
        canonical_atom = ""
        validated: tuple[tuple[str, str], ...] = ()
    elif atom.valid is not True:
        canonical_atom = ""
        validated = (("covalent_residue_name", canonical_residue),)
    else:
        _assert(type(atom.canonical_value) is str, "oracle canonical atom type")
        canonical_atom = atom.canonical_value
        validated = (
            ("covalent_residue_name", canonical_residue),
            ("covalent_residue_atom_name", canonical_atom),
        )
    outcome = scope.admit_005_outcome
    return (
        "ADMIT_005",
        outcome,
        outcome == "passed",
        outcome != "passed",
        scope.reason,
        canonical_residue,
        canonical_atom,
        validated,
        interface.CANDIDATE_FIELDS,
        False,
    )


def _check_public_contract() -> int:
    signature = inspect.signature(interface.evaluate_admit_005)
    parameters = tuple(signature.parameters.values())
    _assert(tuple(parameter.name for parameter in parameters) == ("residue_name", "atom_name"), "public parameter names")
    _assert(all(parameter.default is inspect.Parameter.empty for parameter in parameters), "public defaults forbidden")
    _assert(all(parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in parameters), "public parameter kinds")
    _assert(tuple(field.name for field in fields(interface.Admit005EvaluationResult)) == interface.RESULT_FIELDS, "Exact10 result field order")
    _assert(interface.OUTCOME_VOCABULARY == ("passed", "rejected", "invalid"), "outcome vocabulary")

    result = interface.evaluate_admit_005("CYS", "SG")
    try:
        result.outcome = "invalid"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("result dataclass is mutable")
    invalid_constructions = (
        dict(outcome="passed", passed=False, blocks_candidate=False, reason=""),
        dict(outcome="passed", passed=True, blocks_candidate=True, reason=""),
        dict(outcome="passed", passed=True, blocks_candidate=False, reason="bad"),
        dict(outcome="blocked", passed=False, blocks_candidate=True, reason="bad"),
    )
    base = dict(
        admission_rule_id="ADMIT_005",
        canonical_residue_name="CYS",
        canonical_residue_atom_name="SG",
        validated_candidate_fields=(
            ("covalent_residue_name", "CYS"),
            ("covalent_residue_atom_name", "SG"),
        ),
        consumed_candidate_fields=interface.CANDIDATE_FIELDS,
        evaluator_io_used=False,
    )
    for override in invalid_constructions:
        try:
            interface.Admit005EvaluationResult(**base, **override)
        except (TypeError, ValueError):
            continue
        raise AssertionError("invalid direct construction accepted")

    def semantic_values(
        outcome: str,
        reason: str,
        canonical_residue: str,
        canonical_atom: str,
        validated: tuple[tuple[str, str], ...],
    ) -> dict[str, Any]:
        return {
            "admission_rule_id": "ADMIT_005",
            "outcome": outcome,
            "passed": outcome == "passed",
            "blocks_candidate": outcome != "passed",
            "reason": reason,
            "canonical_residue_name": canonical_residue,
            "canonical_residue_atom_name": canonical_atom,
            "validated_candidate_fields": validated,
            "consumed_candidate_fields": interface.CANDIDATE_FIELDS,
            "evaluator_io_used": False,
        }

    semantic_conflicts = (
        semantic_values(
            "passed", "", "SER", "CA",
            (("covalent_residue_name", "SER"), ("covalent_residue_atom_name", "CA")),
        ),
        semantic_values(
            "rejected", interface.RESIDUE_INVALID_REASONS[0], "SER", "CA",
            (("covalent_residue_name", "SER"), ("covalent_residue_atom_name", "CA")),
        ),
        semantic_values(
            "rejected", "", "SER", "CA",
            (("covalent_residue_name", "SER"), ("covalent_residue_atom_name", "CA")),
        ),
        semantic_values(
            "rejected", interface.SCOPE_REJECTION_REASON, "CYS", "SG",
            (("covalent_residue_name", "CYS"), ("covalent_residue_atom_name", "SG")),
        ),
        semantic_values(
            "invalid", interface.RESIDUE_INVALID_REASONS[3], "CYS", "",
            (("covalent_residue_name", "CYS"),),
        ),
        semantic_values(
            "invalid", interface.ATOM_INVALID_REASONS[0], "", "", (),
        ),
        semantic_values(
            "invalid", interface.ATOM_INVALID_REASONS[4], "CYS", "?",
            (("covalent_residue_name", "CYS"), ("covalent_residue_atom_name", "?")),
        ),
        semantic_values(
            "rejected", interface.SCOPE_REJECTION_REASON, "ser", "CA",
            (("covalent_residue_name", "ser"), ("covalent_residue_atom_name", "CA")),
        ),
        semantic_values(
            "invalid", interface.SCOPE_REJECTION_REASON, "", "", (),
        ),
        semantic_values("invalid", "", "", "", ()),
    )
    for values in semantic_conflicts:
        try:
            interface.Admit005EvaluationResult(**values)
        except (TypeError, ValueError):
            continue
        raise AssertionError("semantic direct-construction conflict accepted")
    return len(semantic_conflicts)


def _check_scalar_semantics_and_oracle() -> None:
    extra_valid = (
        ("CYS", "CA"),
        ("CYS", "ca"),
        ("CYS", "N1"),
        ("CYS", "OXT"),
        ("CYS", "C1'"),
        ("CYS", "A.B"),
        ("CYS", "+"),
        ("a" * 32, "SG"),
    )
    cases = tuple(
        (case["residue"], case["atom"])
        for case in interface._truth_case_definitions()
    ) + extra_valid
    for residue, atom_name in cases:
        before = (residue, atom_name)
        first = interface.evaluate_admit_005(residue, atom_name)
        second = interface.evaluate_admit_005(residue, atom_name)
        _assert(first == second, "repeated call is not deterministic")
        _assert((residue, atom_name) == before, "scalar input mutated")
        _assert(_result_tuple(first) == _oracle_expected(residue, atom_name), "formal/oracle field mismatch")
    precedence = interface.evaluate_admit_005("C-Y", "?")
    _assert(precedence.reason == "COVALENT_RESIDUE_NAME_SYNTAX_INVALID", "residue-first precedence")


def _called_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                names.add(node.func.attr)
    return names


def _check_evaluator_independence() -> None:
    source = (REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_005_rule_logic_interface.py").read_text()
    tree = ast.parse(source)
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    evaluator = functions["evaluate_admit_005"]
    calls = _called_names(evaluator)
    banned_oracles = {
        "classify_admit_004_admit_005_atom_scope_design",
        "validate_generic_covalent_residue_atom_name",
        "normalize_covalent_residue_name",
        "validate_covalent_residue_atom_name",
    }
    _assert(not calls.intersection(banned_oracles), "formal evaluator calls design oracle")
    banned_io = {
        "open", "read", "read_bytes", "read_text", "write", "write_bytes",
        "write_text", "run", "Popen", "system", "urlopen", "request",
    }
    _assert(not calls.intersection(banned_io), "formal evaluator performs I/O")
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
    standard = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
    _assert(all(name in standard for name in imports), "production has a non-stdlib import")


def _check_snapshot_and_predecessors() -> dict[str, Any]:
    original_git = interface._git
    structural_count = 0
    first_content_read_after = -1

    def observed_git(arguments: Any, repo_root: Path, *, text: bool = False) -> Any:
        nonlocal structural_count, first_content_read_after
        if tuple(arguments[:2]) == ("ls-files", "--error-unmatch"):
            structural_count += 1
        if arguments[0] == "show" and len(arguments) == 2 and ":" in arguments[1]:
            if first_content_read_after == -1:
                first_content_read_after = structural_count
        return original_git(arguments, repo_root, text=text)

    interface._git = observed_git
    try:
        snapshot = interface.build_frozen_source_snapshot()
    finally:
        interface._git = original_git
    _assert(structural_count == 12 and first_content_read_after == 12, "source structure was not fully checked before byte reads")
    _assert(interface.validate_frozen_source_snapshot(snapshot), "snapshot invalid")

    def non_descendant_git(arguments: Any, repo_root: Path, *, text: bool = False) -> Any:
        if tuple(arguments[:2]) == ("merge-base", "--is-ancestor"):
            return subprocess.CompletedProcess(arguments, 1, b"", b"")
        return original_git(arguments, repo_root, text=text)

    interface._git = non_descendant_git
    try:
        try:
            interface.build_frozen_source_snapshot(head_ref="HEAD")
        except ValueError as error:
            _assert("not an ancestor" in str(error), "wrong non-descendant failure")
        else:
            raise AssertionError("non-descendant accepted")
    finally:
        interface._git = original_git

    state = interface.build_interface_state(snapshot)
    _assert(len(state["contract_rows"]) == 24, "contract row count")
    _assert(len(state["truth_rows"]) == 22, "truth row count")
    _assert(len(state["source_audit_rows"]) == 12, "source audit row count")
    _assert(len(state["issue_rows"]) == 11, "Exact11 issue count")
    _assert(all(row["case_passed"] == "true" for row in state["truth_rows"]), "truth failure")
    outcomes = {
        value: sum(row["observed_outcome"] == value for row in state["truth_rows"])
        for value in interface.OUTCOME_VOCABULARY
    }
    _assert(outcomes == {"passed": 2, "rejected": 6, "invalid": 14}, "truth group counts")
    provider = [row for row in state["issue_rows"] if row["issue_id"] == "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]
    _assert(len(provider) == 1 and provider[0]["issue_count"] == "11", "provider blocker")
    return state


def _validate_output_tree(root: Path, expected_payloads: dict[str, bytes]) -> None:
    _assert(root.exists() and root.is_dir() and not root.is_symlink(), "output root unsafe")
    entries = tuple(root.iterdir())
    _assert({entry.name for entry in entries} == set(interface.OUTPUT_FILES), "output set mismatch")
    _assert(all(entry.is_file() and not entry.is_symlink() for entry in entries), "unsafe output entry")
    for name, expected in expected_payloads.items():
        observed = (root / name).read_bytes()
        _assert(observed == expected, f"output content mismatch: {name}")
    manifest = json.loads((root / interface.MANIFEST_FILENAME).read_text())
    _assert(manifest["output_files"] == list(interface.OUTPUT_FILES), "manifest output set")
    _assert(manifest["output_file_count"] == 6, "manifest output count")
    _assert(manifest["readiness"] == interface.READINESS, "manifest readiness mismatch")
    _assert(manifest["all_checks_passed"] is True, "manifest check overclaim")
    for name in interface.CSV_OUTPUTS:
        digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
        _assert(manifest["output_sha256"].get(name) == digest, f"manifest hash mismatch: {name}")
    _assert(interface.MANIFEST_FILENAME not in manifest["output_sha256"], "manifest self hash forbidden")


def _expect_output_failure(root: Path, expected_payloads: dict[str, bytes]) -> None:
    try:
        _validate_output_tree(root, expected_payloads)
    except (AssertionError, OSError, ValueError, json.JSONDecodeError):
        return
    raise AssertionError("unsafe output mutation accepted")


def _check_materialization(state: dict[str, Any]) -> dict[str, str]:
    expected_payloads, _ = interface._payloads(state)
    output_root = REPO_ROOT / interface.DEFAULT_OUTPUT_ROOT
    _validate_output_tree(output_root, expected_payloads)
    with tempfile.TemporaryDirectory(prefix="covapie-admit005-check-") as temporary:
        root = Path(temporary) / "outputs"
        interface.run_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1(root)
        first = {name: (root / name).read_bytes() for name in interface.OUTPUT_FILES}
        interface.run_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1(root)
        second = {name: (root / name).read_bytes() for name in interface.OUTPUT_FILES}
        _assert(first == second == expected_payloads, "double materialization differs")

        for mutation in ("missing", "extra", "tamper", "overclaim"):
            victim = Path(temporary) / mutation
            shutil.copytree(root, victim)
            if mutation == "missing":
                (victim / interface.CONTRACT_FILENAME).unlink()
            elif mutation == "extra":
                (victim / "extra.txt").write_text("extra")
            elif mutation == "tamper":
                (victim / interface.TRUTH_FILENAME).write_bytes(b"tampered\n")
            else:
                path = victim / interface.MANIFEST_FILENAME
                manifest = json.loads(path.read_text())
                manifest["readiness"]["ready_for_training"] = True
                path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            _expect_output_failure(victim, expected_payloads)

        symlink_root = Path(temporary) / "symlink"
        symlink_root.mkdir()
        outside = Path(temporary) / "victim.txt"
        outside.write_text("unchanged")
        (symlink_root / interface.CONTRACT_FILENAME).symlink_to(outside)
        try:
            interface.run_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1(symlink_root)
        except ValueError:
            pass
        else:
            raise AssertionError("symlink output victim accepted")
        _assert(outside.read_text() == "unchanged", "symlink victim modified")
    _assert(not tuple(output_root.glob("*.tmp")) and not tuple(output_root.glob("*.part")), "temporary residue")
    output_hashes = {
        name: hashlib.sha256((output_root / name).read_bytes()).hexdigest()
        for name in interface.OUTPUT_FILES
    }
    _assert(
        output_hashes == EXPECTED_OUTPUT_SHA256,
        "actual output SHA256 does not match the frozen six-output map",
    )
    return output_hashes


def _check_import_smoke() -> None:
    command = [
        sys.executable,
        "-c",
        (
            "import covalent_ext.covapie_bulk_download_admission_"
            "admit_005_rule_logic_interface"
        ),
    ]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(SRC_ROOT)
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    _assert(completed.returncode == 0, "production import failed")
    _assert(completed.stdout == "" and completed.stderr == "", "production import emitted output")


def main() -> int:
    semantic_conflict_count = _check_public_contract()
    _check_scalar_semantics_and_oracle()
    _check_evaluator_independence()
    state = _check_snapshot_and_predecessors()
    output_hashes = _check_materialization(state)
    _check_import_smoke()
    phase4_sha = hashlib.sha256((REPO_ROOT / interface.SOURCE_PATHS[0]).read_bytes()).hexdigest()
    registry_sha = hashlib.sha256((REPO_ROOT / interface.SOURCE_PATHS[4]).read_bytes()).hexdigest()
    _assert(phase4_sha == interface.SOURCE_SHA256[interface.SOURCE_PATHS[0]], "Phase 4 runtime changed")
    _assert(registry_sha == interface.SOURCE_SHA256[interface.SOURCE_PATHS[4]], "registry changed")

    _assert(len(state["truth_rows"]) == 22, "stdout truth assertion")
    print("admit_005_truth_matrix=22/22")
    _assert(len(state["contract_rows"]) == 24, "stdout contract assertion")
    print("admit_005_contract=24/24")
    _assert(len(state["source_audit_rows"]) == 12, "stdout source assertion")
    print("exact12_source_audit=12/12")
    _assert(len(state["issue_rows"]) == 11, "stdout issues assertion")
    print("exact11_active_issues=11")
    _assert(semantic_conflict_count == 10, "stdout semantic-invariant assertion")
    print("direct_result_semantic_invariants=10/10")
    _assert(state["readiness"]["ready_for_training"] is False, "stdout readiness assertion")
    print("ready_for_training=false")
    for name in interface.OUTPUT_FILES:
        _assert(
            output_hashes[name] == EXPECTED_OUTPUT_SHA256[name],
            "stdout frozen hash assertion",
        )
        print(f"sha256 {name} {output_hashes[name]}")
    print("ADMIT_005_STANDALONE_EVALUATOR_INTERFACE_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
