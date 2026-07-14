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

from covalent_ext import covapie_bulk_download_admission_candidate_record_id_semantics_design_gate as gate  # noqa: E402


def _hashes(root: Path) -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.iterdir() if path.is_file()}


def _load_check_module() -> object:
    path = REPO_ROOT / "scripts" / "check_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1.py"
    spec = importlib.util.spec_from_file_location("step14au_c1_check", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_import_has_no_output_side_effect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    importlib.reload(gate)
    assert not (tmp_path / gate.DEFAULT_OUTPUT_ROOT).exists()


def test_exact_outputs_are_deterministic(tmp_path: Path) -> None:
    first = gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(tmp_path)
    hashes = _hashes(tmp_path)
    second = gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(tmp_path)
    assert first == second and hashes == _hashes(tmp_path)
    assert sorted(hashes) == sorted([*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME])


def test_six_fixed_sources_are_tracked_and_unchanged(tmp_path: Path) -> None:
    before = {path.as_posix(): hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate._source_paths()}
    manifest = gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(tmp_path)
    assert before == gate.SOURCE_SHA256
    assert manifest["source_input_count"] == 6
    assert gate._validate_source_boundary_rows(gate._source_boundary_rows())
    assert gate._validate_source_semantics(gate._load_source())


@pytest.mark.parametrize("mutate", [
    lambda rows: rows.pop(), lambda rows: rows.reverse(),
    lambda rows: rows[0].__setitem__("sha256_observed", "0" * 64),
    lambda rows: rows[0].__setitem__("symlink", "true"),
    lambda rows: rows.append(copy.deepcopy(rows[0])),
])
def test_source_boundary_fails_closed(mutate: object) -> None:
    rows = gate._source_boundary_rows()
    mutate(rows)  # type: ignore[operator]
    assert not gate._validate_source_boundary_rows(rows)


@pytest.mark.parametrize("value,valid,reason", [
    ("A", True, ""), ("HR_0002", True, ""), ("candidate-001", True, ""),
    ("candidate.record:01", True, ""), ("A" * 128, True, ""), ("A" * 129, False, "candidate_record_id_length_out_of_range"),
    ("", False, "candidate_record_id_empty"), (" A", False, "candidate_record_id_pattern_invalid"),
    ("A\tB", False, "candidate_record_id_pattern_invalid"), ("A\nB", False, "candidate_record_id_pattern_invalid"),
    ("A\rB", False, "candidate_record_id_pattern_invalid"), ("A/B", False, "candidate_record_id_pattern_invalid"),
    ("A\\B", False, "candidate_record_id_pattern_invalid"), ("candidaté", False, "candidate_record_id_non_ascii"),
    ("_A", False, "candidate_record_id_pattern_invalid"), ("A_", False, "candidate_record_id_pattern_invalid"),
    (b"A", False, "candidate_record_id_not_exact_str"), (1, False, "candidate_record_id_not_exact_str"),
    (True, False, "candidate_record_id_not_exact_str"), (None, False, "candidate_record_id_not_exact_str"), (Path("A"), False, "candidate_record_id_not_exact_str"),
])
def test_single_value_syntax(value: object, valid: bool, reason: str) -> None:
    result = gate.normalize_candidate_record_id(value)
    assert result.syntax_valid is valid and result.blocking_reason == reason
    assert result.canonical_candidate_record_id == (value if valid else "")


def test_str_subclass_rejected_and_identity_is_case_sensitive() -> None:
    class Subclass(str):
        pass
    assert not gate.normalize_candidate_record_id(Subclass("A")).syntax_valid
    assert gate.normalize_candidate_record_id("ABC").canonical_candidate_record_id == "ABC"
    assert gate.normalize_candidate_record_id("abc").canonical_candidate_record_id == "abc"
    assert gate.evaluate_candidate_record_id_batch_uniqueness("ABC", ["ABC", "abc"]).passed


@pytest.mark.parametrize("candidate,batch,passed,reason", [
    ("A", ["A"], True, ""), ("A", ("A", "B"), True, ""), ("A", "A", False, "batch_candidate_record_ids_invalid_type"),
    ("A", b"A", False, "batch_candidate_record_ids_invalid_type"), ("A", {"A"}, False, "batch_candidate_record_ids_invalid_type"),
    ("A", {"A": 1}, False, "batch_candidate_record_ids_invalid_type"), ("A", [], False, "batch_candidate_record_ids_empty"),
    ("A", ["B"], False, "candidate_record_id_missing_from_batch"), ("A", ["A", "A"], False, "candidate_record_id_repeated_in_batch"),
    ("A", ["A", "B", "B"], False, "batch_candidate_record_ids_not_globally_unique"),
    ("A", ["A", "B B"], False, "batch_candidate_record_id_member_invalid"), ("A", ["A", 1], False, "batch_candidate_record_id_member_invalid"),
    ("A A", ["A A"], False, "candidate_record_id_pattern_invalid"),
])
def test_batch_contract(candidate: object, batch: object, passed: bool, reason: str) -> None:
    result = gate.evaluate_candidate_record_id_batch_uniqueness(candidate, batch)
    assert result.passed is passed and result.blocking_reason == reason


def test_generator_rejected_and_batch_order_does_not_matter() -> None:
    assert not gate.evaluate_candidate_record_id_batch_uniqueness("A", (item for item in ["A"])).passed
    assert gate.evaluate_candidate_record_id_batch_uniqueness("A", ["A", "B", "C"]).passed
    assert gate.evaluate_candidate_record_id_batch_uniqueness("A", ["C", "A", "B"]).passed


def test_contract_examples_and_safety_are_exact() -> None:
    probes = gate._candidate_record_id_contract_probe_results()
    assert tuple(probes) == tuple(spec[0] for spec in gate._contract_specs())
    assert len(probes) == 30 and all(probes.values())
    assert gate._validate_contract_rows(gate._contract_rows())
    assert len(gate._contract_rows()) == 30
    assert gate._validate_example_rows(gate._example_rows())
    assert all(row["example_passed"] == "true" for row in gate._example_rows())
    assert gate._validate_safety_rows(gate._safety_rows())
    assert len(gate._safety_rows()) == 19


def test_frozen_example_expectations_do_not_follow_validator_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_before = [(spec.example_id, spec.expected_passed, spec.expected_blocking_reason) for spec in gate._example_specs()]
    original = gate.normalize_candidate_record_id

    def broken(value: object) -> gate.CandidateRecordIdNormalizationResult:
        result = original(value)
        if value == "A":
            return gate.CandidateRecordIdNormalizationResult(result.input_type, False, "", "candidate_record_id_pattern_invalid")
        return result

    monkeypatch.setattr(gate, "normalize_candidate_record_id", broken)
    rows = gate._example_rows()
    assert expected_before == [(spec.example_id, spec.expected_passed, spec.expected_blocking_reason) for spec in gate._example_specs()]
    assert next(row for row in rows if row["example_id"] == "single_valid_01")["example_passed"] == "false"
    result = gate._build_materialization(gate._load_source(), example_rows=rows)
    assert result["all_example_checks_passed"] is False
    assert "CANDIDATE_RECORD_ID_EXAMPLE_VALIDATION_FAILED" in [row["issue_id"] for row in result["issue_rows"]]


def test_contract_probe_failure_is_not_hidden_by_contract_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = gate._contract_rows()
    original = gate.normalize_candidate_record_id

    def broken(value: object) -> gate.CandidateRecordIdNormalizationResult:
        result = original(value)
        if value == b"A":
            return gate.CandidateRecordIdNormalizationResult("bytes", True, "A", "")
        return result

    monkeypatch.setattr(gate, "normalize_candidate_record_id", broken)
    result = gate._build_materialization(gate._load_source(), contract_rows=rows)
    assert result["all_contract_checks_passed"] is False
    assert "CANDIDATE_RECORD_ID_CONTRACT_VALIDATION_FAILED" in [row["issue_id"] for row in result["issue_rows"]]


def test_batch_result_preserves_observed_facts_for_invalid_candidate() -> None:
    result = gate.evaluate_candidate_record_id_batch_uniqueness("A A", ["B"])
    assert (result.candidate_syntax_valid, result.batch_type_valid, result.batch_non_empty, result.all_batch_ids_syntax_valid) == (False, True, True, True)
    assert (result.candidate_occurrence_count, result.batch_ids_unique, result.passed, result.blocking_reason) == (0, True, False, "candidate_record_id_pattern_invalid")


def test_batch_result_preserves_member_and_empty_facts() -> None:
    member_invalid = gate.evaluate_candidate_record_id_batch_uniqueness("A", ["A", 1])
    assert (member_invalid.batch_non_empty, member_invalid.all_batch_ids_syntax_valid, member_invalid.candidate_occurrence_count, member_invalid.batch_ids_unique) == (True, False, 1, False)
    assert member_invalid.blocking_reason == "batch_candidate_record_id_member_invalid"
    empty = gate.evaluate_candidate_record_id_batch_uniqueness("A", [])
    assert (empty.batch_type_valid, empty.batch_non_empty, empty.all_batch_ids_syntax_valid, empty.candidate_occurrence_count, empty.batch_ids_unique) == (True, False, True, 0, True)
    assert empty.blocking_reason == "batch_candidate_record_ids_empty"


def test_source_semantics_key_row_drift_fails_closed() -> None:
    source = copy.deepcopy(gate._load_source())
    next(row for row in source["rule_rows"] if row["admission_rule_id"] == "ADMIT_001")["batch_context_dependencies"] = "wrong"
    assert gate._validate_source_semantics(source) is False
    source = copy.deepcopy(gate._load_source())
    next(row for row in source["field_rows"] if row["field_name"] == "candidate_record_id")["dependent_rules"] = "wrong"
    assert gate._validate_source_semantics(source) is False
    source = copy.deepcopy(gate._load_source())
    next(row for row in source["context_rows"] if row["context_item"] == "candidate_record_id_contract")["implementation_ready"] = "true"
    assert gate._validate_source_semantics(source) is False


def test_contract_and_example_drift_fail_closed() -> None:
    source = gate._load_source()
    contract = gate._contract_rows()
    contract[0]["contract_passed"] = "false"
    examples = gate._example_rows()
    examples[0]["expected_passed"] = "false"
    result = gate._build_materialization(source, contract_rows=contract, example_rows=examples)
    assert not result["all_contract_checks_passed"] and not result["all_example_checks_passed"]
    assert [row["issue_id"] for row in result["issue_rows"]] == [
        "CANDIDATE_RECORD_ID_CONTRACT_VALIDATION_FAILED", "CANDIDATE_RECORD_ID_EXAMPLE_VALIDATION_FAILED",
    ]
    assert not result["all_checks_passed"]


def test_source_and_safety_failure_inventory_order() -> None:
    rows = gate._source_boundary_rows()
    rows[0]["sha256_observed"] = "0" * 64
    safety = gate._safety_rows()
    safety[0]["observed_status"] = "true"
    result = gate._build_materialization(gate._load_source(), source_rows=rows, safety_rows=safety)
    assert [row["issue_id"] for row in result["issue_rows"]] == [
        "CANDIDATE_RECORD_ID_SOURCE_BOUNDARY_FAILED", "CANDIDATE_RECORD_ID_SAFETY_VALIDATION_FAILED",
    ]
    manifest = gate._manifest_payload(result, {})
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert manifest["candidate_record_id_semantics_frozen"] is False


def test_normal_manifest_claims_design_not_integration(tmp_path: Path) -> None:
    manifest = gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(tmp_path)
    assert manifest["upstream_effective_issue_count"] == 12
    assert manifest["expected_post_integration_issue_count"] == 11
    assert manifest["resolved_design_issue_ids"] == ["CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED"]
    assert manifest["blocking_reasons"] == []
    assert manifest["ready_for_candidate_record_id_semantics_integration"] is True
    assert manifest["candidate_record_id_semantics_integrated"] is False
    assert manifest["integration_applied_current_step"] is False
    assert manifest["admit_001_rule_logic_ready"] is False
    assert manifest["ready_for_admission_evaluator_rule_logic_implementation"] is False
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False and manifest["ready_to_train_now"] is False
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]


def test_check_validator_rejects_contract_example_safety_and_manifest_drift(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(tmp_path)
    check = _load_check_module()
    hashes = {name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)}
    manifest = json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text())
    check._validate_disk(manifest, tmp_path, hashes)
    manifest["upstream_effective_issue_count"] = 11
    with pytest.raises(AssertionError):
        check._validate_disk(manifest, tmp_path, hashes)


@pytest.mark.parametrize("field,value", [
    ("output_file_count", 7), ("canonical_mask_task_count", 4),
    ("expected_post_integration_issue_count", 12),
    ("ready_for_admission_evaluator_rule_logic_implementation", True),
])
def test_check_validator_rejects_manifest_truthfulness_drift(tmp_path: Path, field: str, value: object) -> None:
    gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(tmp_path)
    check = _load_check_module()
    hashes = {name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)}
    manifest = json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text())
    manifest[field] = value
    with pytest.raises(AssertionError):
        check._validate_disk(manifest, tmp_path, hashes)


@pytest.mark.parametrize("filename", [
    gate.CSV_OUTPUTS[0], gate.CSV_OUTPUTS[1], gate.CSV_OUTPUTS[3], gate.CSV_OUTPUTS[4],
])
def test_check_validator_rejects_output_content_or_hash_drift(tmp_path: Path, filename: str) -> None:
    gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(tmp_path)
    check = _load_check_module()
    hashes = {name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)}
    manifest = json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text())
    with (tmp_path / filename).open("a", encoding="utf-8") as handle:
        handle.write("drift\n")
    with pytest.raises(AssertionError):
        check._validate_disk(manifest, tmp_path, hashes)


def test_check_validator_rejects_source_hash_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(tmp_path)
    check = _load_check_module()
    hashes = {name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)}
    manifest = json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text())
    changed = dict(gate.SOURCE_SHA256)
    changed[next(iter(changed))] = "0" * 64
    monkeypatch.setattr(gate, "SOURCE_SHA256", changed)
    with pytest.raises(AssertionError):
        check._validate_disk(manifest, tmp_path, hashes)


def test_check_validator_rejects_semantically_equivalent_byte_drift(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(tmp_path)
    check = _load_check_module()
    hashes = {name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)}
    manifest = json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text())
    contract = tmp_path / gate.CSV_OUTPUTS[0]
    contract.write_bytes(contract.read_bytes().replace(b"\n", b"\r\n"))
    assert list(csv.DictReader(contract.open(newline="", encoding="utf-8"))) == gate._contract_rows()
    with pytest.raises(AssertionError):
        check._validate_disk(manifest, tmp_path, hashes)


@pytest.mark.parametrize("kind", ["extra", "missing", "symlink"])
def test_check_validator_rejects_nonexact_output_set(tmp_path: Path, kind: str) -> None:
    gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(tmp_path)
    check = _load_check_module()
    hashes = {name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)}
    manifest = json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text())
    target = tmp_path / gate.CSV_OUTPUTS[0]
    if kind == "extra":
        (tmp_path / "unexpected.csv").write_text("x\n", encoding="utf-8")
    elif kind == "missing":
        target.unlink()
    else:
        target.unlink()
        target.symlink_to(tmp_path / gate.CSV_OUTPUTS[1])
    with pytest.raises(AssertionError):
        check._validate_disk(manifest, tmp_path, hashes)


def test_forbidden_imports_and_no_identity_derivation() -> None:
    source = (REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_candidate_record_id_semantics_design_gate.py").read_text()
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = {"requests", "urllib", "aiohttp", "torch", "numpy", "rdkit", "gemmi", "Bio", "pandas", "sklearn", "random", "uuid", "time", "secrets", "ast", "inspect"}
    assert not imported.intersection(forbidden)
    called_names = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    assert not called_names.intersection({"hash", "uuid4", "random", "randint", "token_hex", "time", "time_ns"})
    helper_source = ast.get_source_segment(source, next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "evaluate_candidate_record_id_batch_uniqueness"))
    assert helper_source is not None
    assert not any(token in helper_source for token in ("pdb_id", "ligand_comp_id", "raw_target_relative_path", "batch_index"))


def test_contract_probes_use_only_in_memory_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_source_read(*args: object, **kwargs: object) -> str:
        raise AssertionError("production source read")

    monkeypatch.setattr(gate.Path, "read_text", fail_source_read)
    probes = gate._candidate_record_id_contract_probe_results()
    assert len(probes) == 30 and all(probes.values())


def test_check_ast_audit_accepts_real_production_source() -> None:
    check = _load_check_module()
    check._validate_production_source_file()


def _minimal_production_source(extra: str = "") -> str:
    return "\n".join([
        "def normalize_candidate_record_id(value):", "    return value", "",
        "def evaluate_candidate_record_id_batch_uniqueness(value, batch):", "    return value", "", extra,
    ])


@pytest.mark.parametrize("extra", [
    "import random",
    "from uuid import uuid4",
    "import inspect\ninspect.getsource(target)",
    "from pathlib import Path\nPath(__file__).read_text()",
    "hash(value)",
    "from time import time\ntime()",
    "import requests",
    "def unrelated():\n    return duplicate_identity_key",
])
def test_check_ast_audit_rejects_forbidden_source_patterns(extra: str) -> None:
    check = _load_check_module()
    if "duplicate_identity_key" in extra:
        extra = "def evaluate_candidate_record_id_batch_uniqueness(value, batch):\n    return duplicate_identity_key"
        text = "\n".join(["def normalize_candidate_record_id(value):", "    return value", "", extra])
    else:
        text = _minimal_production_source(extra)
    with pytest.raises(AssertionError):
        check._validate_production_source_text(text)


def test_check_does_not_print_readiness_when_source_audit_fails(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    check = _load_check_module()

    def fail() -> None:
        raise AssertionError("source audit failed")

    monkeypatch.setattr(check, "_validate_production_source_file", fail)
    with pytest.raises(AssertionError):
        check.main()
    output = capsys.readouterr().out
    assert "candidate_record_id_semantics_frozen=true" not in output
    assert "ready_for_candidate_record_id_semantics_integration=true" not in output
