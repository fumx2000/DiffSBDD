#!/usr/bin/env python3
"""Fail-closed checker for Step14AU-E1-E4 Phase 1 design artifacts."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import stat
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_unified_rule_engine_contract_design_gate as gate,
)


EXPECTED_OUTPUT_SHA256 = {
    gate.MANIFEST_FILENAME: "62e21a2b4a982e734d6ecd02b1ec056fa0ddccfda6c41dd4bd90dfbe7eb47c3d",
    gate.ISSUE_FILENAME: "5295ee97d8cc3c81cd376116c4dc87489e1b04a65d700a6d08a927d5c72a9951",
    gate.SAFETY_FILENAME: "d05c54f805ad2118027124ae96c3bce132904e26bbd93daa3dc0298681aa159f",
    gate.ROUTING_FILENAME: "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
    gate.PUBLIC_API_FILENAME: "2d46faffb7505483b5dabc05a9451d1b6eea0671c722f78674175a8559e8a304",
    gate.RESULT_FILENAME: "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
}


def _csv(content: bytes) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    reader = csv.DictReader(
        io.StringIO(content.decode("utf-8", errors="strict"), newline="")
    )
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid output CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(
        tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values())
        for row in rows
    ):
        raise ValueError("invalid output CSV row")
    return tuple(reader.fieldnames), rows


def _assert_output_root(root: Path) -> dict[str, bytes]:
    metadata = os.lstat(root)
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ValueError("output root is not a real directory")
    entries = tuple(root.iterdir())
    if tuple(sorted(entry.name for entry in entries)) != tuple(sorted(gate.OUTPUT_FILES)):
        raise ValueError("output set is missing or extra")
    payloads: dict[str, bytes] = {}
    for entry in entries:
        metadata = os.lstat(entry)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError("output contains symlink or non-regular entry")
        payloads[entry.name] = entry.read_bytes()
    return payloads


def _assert_no_runtime_implementation() -> None:
    production_path = REPO_ROOT / "src/covalent_ext" / (
        "covapie_bulk_download_admission_unified_rule_engine_contract_design_gate.py"
    )
    checker_path = Path(__file__).resolve()
    allowed_roots = {
        "__future__",
        "ast",
        "collections",
        "csv",
        "dataclasses",
        "hashlib",
        "io",
        "json",
        "os",
        "pathlib",
        "stat",
        "subprocess",
        "sys",
        "tempfile",
        "typing",
        "covalent_ext",
    }
    for path in (production_path, checker_path):
        tree = ast.parse(path.read_bytes(), filename=path.as_posix())
        top_names = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        if top_names & {
            "evaluate_admission_rule",
            "UnifiedAdmissionRuleEvaluation",
            "UnifiedAdmissionDispatchError",
        }:
            raise ValueError("dispatcher or runtime result/error class was implemented")
        for node in tree.body:
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                roots = {(node.module or "").split(".", 1)[0]}
            else:
                continue
            if not roots <= allowed_roots:
                raise ValueError(f"non-standard-library production/checker import: {roots}")


def _assert_expected_base_lifecycle_contract() -> tuple[bool, bool]:
    production_path = REPO_ROOT / "src/covalent_ext" / (
        "covapie_bulk_download_admission_unified_rule_engine_contract_design_gate.py"
    )
    tree = ast.parse(production_path.read_bytes(), filename=production_path.as_posix())
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    helper = functions.get("_validate_expected_base_lineage")
    snapshot_builder = functions.get("build_frozen_source_snapshot")
    state_builder = functions.get("build_design_state")
    if helper is None or snapshot_builder is None or state_builder is None:
        raise ValueError("expected-base lifecycle helpers are missing")
    helper_source = ast.unparse(helper)
    for required in (
        "cat-file",
        "EXPECTED_BASE_COMMIT",
        "EXPECTED_BASE_SUBJECT",
        "merge-base",
        "--is-ancestor",
        "head_ref",
    ):
        if required not in helper_source:
            raise ValueError(f"expected-base lineage operation missing: {required}")
    constants = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value) is str
    }
    if "rev-parse" in constants:
        raise ValueError("production still contains an exact-HEAD identity query")
    for node in (snapshot_builder, state_builder):
        if "head_ref" not in {argument.arg for argument in node.args.kwonlyargs}:
            raise ValueError("successor HEAD injection contract is missing")
    gate._validate_expected_base_lineage(REPO_ROOT)
    return True, True


def _assert_stdout_report(report: Mapping[str, Any]) -> None:
    expected_scalars = {
        "stage": gate.STAGE,
        "output_file_count": 6,
        "source_input_count": 21,
        "formal_evaluator_callable_count": 4,
        "routing_row_count": 15,
        "active_issue_count": 12,
        "design_readiness": True,
        "all_checks_passed": True,
        "expected_base_is_ancestor_of_head": True,
        "successor_head_supported": True,
    }
    if set(report) != set(expected_scalars) | {"output_sha256"}:
        raise ValueError("checker stdout field set mismatch")
    if any(report[key] != value for key, value in expected_scalars.items()):
        raise ValueError("checker stdout scalar assertion failed")
    if report["output_sha256"] != EXPECTED_OUTPUT_SHA256:
        raise ValueError("checker stdout output SHA assertion failed")


def check_covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1(
    output_root: Path = gate.DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _assert_no_runtime_implementation()
    expected_base_is_ancestor, successor_head_supported = (
        _assert_expected_base_lifecycle_contract()
    )
    state = gate.build_design_state()
    if state["all_checks_passed"] is not True or state["design_readiness"] is not True:
        raise ValueError("reconstructed design state failed")
    actual = _assert_output_root(root)
    expected, expected_manifest = gate._payloads(state)
    if actual != expected:
        raise ValueError("output bytes differ from deterministic reconstruction")

    public_header, public_rows = _csv(actual[gate.PUBLIC_API_FILENAME])
    result_header, result_rows = _csv(actual[gate.RESULT_FILENAME])
    routing_header, routing_rows = _csv(actual[gate.ROUTING_FILENAME])
    issue_header, issue_rows = _csv(actual[gate.ISSUE_FILENAME])
    safety_header, safety_rows = _csv(actual[gate.SAFETY_FILENAME])
    if public_header != gate.PUBLIC_API_COLUMNS or len(public_rows) != 27:
        raise ValueError("public API contract mismatch")
    if result_header != gate.RESULT_COLUMNS or len(result_rows) != 29:
        raise ValueError("unified result contract mismatch")
    fields = tuple(
        row["field_name"] for row in result_rows if row["contract_kind"] == "result_field"
    )
    if fields != tuple(name for name, _ in gate.RESULT_FIELDS):
        raise ValueError("unified result Exact13 field order mismatch")
    if routing_header != gate.ROUTING_COLUMNS or len(routing_rows) != 15:
        raise ValueError("routing matrix mismatch")
    if tuple(row["admission_rule_id"] for row in routing_rows) != tuple(
        f"ADMIT_{index:03d}" for index in range(1, 16)
    ):
        raise ValueError("routing matrix rule order mismatch")
    if sum(row["callable_discovered"] == "true" for row in routing_rows) != 4:
        raise ValueError("formal evaluator inventory is not Exact4")
    admit004 = routing_rows[3]
    if not (
        admit004["evaluator_callable_name"] == "evaluate_admit_004"
        and admit004["result_adapter_contract_status"] == "design_ready"
        and admit004["engine_registration_status"]
        == "ready_for_minimal_dispatch_shell_registration"
        and admit004["evaluation_context_dependencies"]
        == "covalent_residue_identity_contract|covalent_residue_identity_evidence_context"
    ):
        raise ValueError("ADMIT_004 routing/pass-through contract mismatch")
    if any(
        row["routing_disposition"] != "known_unsupported_fail_closed"
        for row in routing_rows[4:]
    ):
        raise ValueError("known unsupported rules do not fail closed")
    if issue_header != gate.ISSUE_COLUMNS or len(issue_rows) != 12:
        raise ValueError("engine issue inventory mismatch")
    predecessor_issues = gate._csv_document(
        state["source_snapshot"], gate.E1E3_ISSUE_PATH
    ).rows
    if issue_rows[:9] != predecessor_issues:
        raise ValueError("predecessor Exact9 issues were not copied field-for-field")
    provider = next(
        row
        for row in issue_rows
        if row["issue_id"] == "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"
    )
    if not (
        provider["status"] == "open"
        and provider["severity"] == "blocking"
        and provider["issue_count"] == "11"
    ):
        raise ValueError("provider blocker was weakened")
    if safety_header != gate.SAFETY_COLUMNS or tuple(
        row["safety_item"] for row in safety_rows
    ) != gate.TRUE_SAFETY_ITEMS + gate.FALSE_SAFETY_ITEMS:
        raise ValueError("safety inventory contains missing, extra, or padding rows")

    manifest = json.loads(actual[gate.MANIFEST_FILENAME].decode("utf-8", errors="strict"))
    if manifest != expected_manifest:
        raise ValueError("manifest differs from direct reconstruction")
    for filename in gate.CSV_OUTPUTS:
        observed = hashlib.sha256(actual[filename]).hexdigest()
        if manifest["output_sha256"].get(filename) != observed:
            raise ValueError(f"manifest output SHA mismatch: {filename}")
    if set(manifest["output_sha256"]) != set(gate.CSV_OUTPUTS):
        raise ValueError("manifest output SHA set must exclude only its own self-hash")
    if not (
        manifest["design_readiness"] is True
        and manifest["all_checks_passed"] is True
        and all(manifest[name] is True for name in gate.TRUE_READINESS)
        and all(manifest[name] is False for name in gate.FALSE_READINESS)
        and manifest["global_cross_rule_precedence_frozen"] is False
        and manifest["evaluator_execution_current_step"] is False
    ):
        raise ValueError("manifest readiness overclaim or underclaim")
    hashes = {
        filename: hashlib.sha256(actual[filename]).hexdigest()
        for filename in gate.OUTPUT_FILES
    }
    if hashes != EXPECTED_OUTPUT_SHA256:
        raise ValueError("frozen output bytes changed")
    report = {
        "stage": gate.STAGE,
        "output_file_count": 6,
        "source_input_count": 21,
        "formal_evaluator_callable_count": 4,
        "routing_row_count": 15,
        "active_issue_count": 12,
        "design_readiness": True,
        "all_checks_passed": True,
        "expected_base_is_ancestor_of_head": expected_base_is_ancestor,
        "successor_head_supported": successor_head_supported,
        "output_sha256": hashes,
    }
    _assert_stdout_report(report)
    return report


if __name__ == "__main__":
    print(
        json.dumps(
            check_covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1(),
            indent=2,
            sort_keys=True,
        )
    )
