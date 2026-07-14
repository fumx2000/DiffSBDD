#!/usr/bin/env python3
"""Verify deterministic Step14AU-C1 candidate-record ID design evidence."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import covapie_bulk_download_admission_candidate_record_id_semantics_design_gate as gate  # noqa: E402


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _validate_production_source_text(text: str) -> None:
    """Audit production source externally; C1 materialization never reads it."""
    tree = ast.parse(text)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden_imports = {
        "requests", "urllib", "aiohttp", "torch", "numpy", "rdkit", "gemmi", "Bio", "pandas", "sklearn",
        "random", "uuid", "time", "secrets", "inspect", "ast",
    }
    assert not imported.intersection(forbidden_imports)
    forbidden_calls = {"hash", "uuid4", "random", "randint", "randrange", "token_hex", "token_urlsafe", "time", "time_ns"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        assert name not in forbidden_calls
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "inspect":
                assert node.func.attr not in {"getsource", "getsourcelines"}
            if isinstance(node.func.value, ast.Name) and node.func.value.id in {"linecache", "tokenize"}:
                assert node.func.attr not in {"getline", "open"}
            if node.func.attr in {"read_text", "read_bytes"} and isinstance(node.func.value, ast.Call):
                value = node.func.value
                assert not (
                    isinstance(value.func, ast.Name) and value.func.id == "Path"
                    and any(isinstance(argument, ast.Name) and argument.id == "__file__" for argument in value.args)
                )
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            assert not any(isinstance(argument, ast.Name) and argument.id == "__file__" for argument in node.args)
    helper_names = {"normalize_candidate_record_id", "evaluate_candidate_record_id_batch_uniqueness"}
    helpers = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in helper_names]
    assert {node.name for node in helpers} == helper_names
    forbidden_helper_symbols = {"pdb_id", "ligand_comp_id", "raw_target_relative_path", "duplicate_identity_key", "batch_index"}
    for helper in helpers:
        symbols = {
            node.id for node in ast.walk(helper) if isinstance(node, ast.Name)
        } | {
            node.value for node in ast.walk(helper) if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        assert not symbols.intersection(forbidden_helper_symbols)


def _validate_production_source_file() -> None:
    source_path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_candidate_record_id_semantics_design_gate.py"
    _validate_production_source_text(source_path.read_text(encoding="utf-8"))


def _validate_disk(manifest: dict[str, object], root: Path, hashes: dict[str, str]) -> None:
    _validate_production_source_file()
    expected_names = {*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME}
    entries = {path.name for path in root.iterdir()}
    assert entries == expected_names
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in expected_names)
    current_hashes = {name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)}
    assert current_hashes == hashes
    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == gate.STEP_LABEL and manifest["project_name"] == gate.PROJECT_NAME
    assert manifest["manifest_schema_version"] == gate.MANIFEST_SCHEMA_VERSION
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["source_read_boundary"] == "only_step14au_b2_six_committed_metadata_outputs"
    assert manifest["source_input_count"] == 6
    assert manifest["source_input_sha256"] == gate.SOURCE_SHA256
    assert manifest["output_files"] == [*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME]
    assert manifest["output_file_count"] == 6 and manifest["non_manifest_output_count"] == 5
    assert manifest["output_sha256"] == {name: current_hashes[name] for name in gate.CSV_OUTPUTS}
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["resolved_design_issue_ids"] == ["CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED"]
    assert manifest["upstream_effective_issue_count"] == 12
    assert manifest["expected_post_integration_issue_count"] == 11
    for key in (
        "all_source_boundary_checks_passed", "all_source_semantics_checks_passed", "all_contract_checks_passed",
        "all_example_checks_passed", "all_safety_checks_passed", "all_checks_passed",
        "candidate_record_id_semantics_frozen", "candidate_record_id_syntax_contract_ready",
        "candidate_record_id_batch_uniqueness_contract_ready", "ready_for_candidate_record_id_semantics_integration",
        "ready_for_admission_evaluator_interface_implementation",
    ):
        assert manifest[key] is True
    for key in (
        "candidate_record_id_semantics_integrated", "integration_applied_current_step", "admit_001_rule_logic_ready",
        "ready_for_admission_evaluator_rule_logic_implementation", "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
        "network_access_used_current_step", "raw_structure_read_current_step",
        "candidate_records_materialized_current_step", "download_queue_materialized_current_step",
    ):
        assert manifest[key] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["blocking_reasons"] == [] and manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert "timestamp" not in json.dumps(manifest, sort_keys=True).lower()
    assert "/home/" not in json.dumps(manifest, sort_keys=True)
    source = gate._load_source()
    assert gate._validate_source_boundary_rows(gate._source_boundary_rows())
    assert gate._validate_source_semantics(source)
    contract = _csv(root / gate.CSV_OUTPUTS[0])
    examples = _csv(root / gate.CSV_OUTPUTS[1])
    source_rows = _csv(root / gate.CSV_OUTPUTS[2])
    safety = _csv(root / gate.CSV_OUTPUTS[3])
    issues = _csv(root / gate.CSV_OUTPUTS[4])
    assert gate._validate_contract_rows(contract)
    assert gate._validate_example_rows(examples)
    assert gate._validate_source_boundary_rows(source_rows)
    assert gate._validate_safety_rows(safety)
    assert issues == [{"issue_id": "NO_ISSUES", "issue_type": "no_candidate_record_id_semantics_design_issues", "severity": "none", "status": "no_issues", "issue_count": "0", "blocking_reason": ""}]
    assert gate.normalize_candidate_record_id("HR_0002").canonical_candidate_record_id == "HR_0002"
    assert not gate.normalize_candidate_record_id(" A").syntax_valid
    assert gate.evaluate_candidate_record_id_batch_uniqueness("A", ["A", "B"]).passed
    assert not gate.evaluate_candidate_record_id_batch_uniqueness("A", ["A", "A"]).passed
    assert not gate.evaluate_candidate_record_id_batch_uniqueness("A", ["B"]).passed
    assert not gate.evaluate_candidate_record_id_batch_uniqueness("A", ["A", "B B"]).passed
    assert not gate.evaluate_candidate_record_id_batch_uniqueness("A", "A").passed


def main() -> int:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    first = gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(root)
    first_hashes = {name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)}
    second = gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(root)
    second_hashes = {name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)}
    assert first == second and first_hashes == second_hashes
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest == second
    _validate_disk(manifest, root, first_hashes)
    print(f"stage={gate.STAGE}")
    print("all_checks_passed=true")
    print("candidate_record_id_semantics_frozen=true")
    print("candidate_record_id_batch_uniqueness_contract_ready=true")
    print("ready_for_candidate_record_id_semantics_integration=true")
    print("ready_for_admission_evaluator_rule_logic_implementation=false")
    print("ready_for_real_candidate_evaluation=false")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    print("candidate_record_id_semantics_design_outputs_byte_identical=true")
    print("covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
