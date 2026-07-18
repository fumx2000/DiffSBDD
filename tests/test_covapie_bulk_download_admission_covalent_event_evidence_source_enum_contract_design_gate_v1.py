from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate as gate,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1.py"


def _load_checker() -> object:
    spec = importlib.util.spec_from_file_location("covapie_enum_checker_test", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rewrite_truth_and_refresh_manifest_hash(
    root: Path, row_mutator: object,
) -> None:
    truth_path = root / gate.TRUTH_MATRIX_FILENAME
    with truth_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        fieldnames = tuple(reader.fieldnames)
        rows = list(reader)
    row_mutator(rows)  # type: ignore[operator]
    with truth_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][gate.TRUTH_MATRIX_FILENAME] = hashlib.sha256(truth_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_production_import_is_silent_and_has_no_materialization(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate"],
        cwd=tmp_path, env={"PYTHONPATH": str(REPO_ROOT / "src")}, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0 and result.stdout == "" and result.stderr == ""
    assert list(tmp_path.iterdir()) == []


def test_checker_import_is_silent(capsys: pytest.CaptureFixture[str]) -> None:
    _load_checker()
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_production_is_standard_library_only_and_has_no_project_imports() -> None:
    tree = ast.parse(Path(gate.__file__).read_text(encoding="utf-8"))
    allowed = {"ast", "csv", "hashlib", "io", "json", "os", "re", "stat", "subprocess", "tempfile", "collections", "dataclasses", "pathlib", "typing", "__future__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".")[0] in allowed for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] in allowed


def test_exact12_source_boundary_order_and_hashes() -> None:
    assert len(gate.SOURCE_PATHS) == len(set(gate.SOURCE_PATHS)) == 12
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS
    snapshot = gate.build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert all(record.expected_sha256 == hashlib.sha256(record.content_bytes).hexdigest() for record in snapshot.records)


def test_all_structure_checks_precede_first_explicit_content_read(monkeypatch: pytest.MonkeyPatch) -> None:
    completed: list[Path] = []
    original_structure = gate._structural_source_check
    original_read_bytes = Path.read_bytes

    def structure(path: Path, root: Path) -> bool:
        result = original_structure(path, root)
        completed.append(path)
        return result

    def read_bytes(path: Path) -> bytes:
        assert len(completed) == 12
        return original_read_bytes(path)

    monkeypatch.setattr(gate, "_structural_source_check", structure)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    gate.build_frozen_source_snapshot()
    assert tuple(completed) == gate.SOURCE_PATHS


def test_non_descendant_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = gate._git

    def fake(arguments: object, repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[object]:
        if list(arguments)[:2] == ["merge-base", "--is-ancestor"]:
            return subprocess.CompletedProcess([], 1, "" if text else b"", "" if text else b"")
        return original(arguments, repo_root, text=text)  # type: ignore[arg-type]

    monkeypatch.setattr(gate, "_git", fake)
    with pytest.raises(ValueError, match="not an ancestor"):
        gate.build_frozen_source_snapshot()


@pytest.mark.parametrize("failure", ["missing", "symlink"])
def test_missing_or_symlink_source_fails_before_content_read(monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    calls = 0

    def structural(path: Path, root: Path) -> bool:
        nonlocal calls
        calls += 1
        return not (calls == 4 and failure in {"missing", "symlink"})

    def forbidden_read(path: Path) -> bytes:
        raise AssertionError("content read occurred")

    monkeypatch.setattr(gate, "_structural_source_check", structural)
    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    with pytest.raises(ValueError, match="structural"):
        gate.build_frozen_source_snapshot()
    assert calls == 12


def test_snapshot_hash_tamper_fails_closed() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    records = list(snapshot.records)
    first = records[0]
    records[0] = gate.FrozenSourceRecord(first.relative_path, first.expected_sha256, first.base_tree_sha256, "0" * 64, first.content_bytes)
    assert not gate.validate_frozen_source_snapshot(gate.FrozenSourceSnapshot(tuple(records)))


def test_exact3_normative_enum_is_ordered_and_not_observed() -> None:
    assert gate.CANONICAL_ENUM_MEMBERS == (
        "explicit_structure_bond_record", "explicit_curated_covalent_annotation", "distance_only_inference"
    )
    rows = gate._enum_registry_rows()
    assert len(rows) == 3
    assert tuple(row["canonical_value"] for row in rows) == gate.CANONICAL_ENUM_MEMBERS
    assert all(row["normative_contract_member"] == "true" for row in rows)
    assert all(row["observed_in_committed_metadata"] == "false" for row in rows)


def test_no_fourth_catchall_manual_review_or_alias_member() -> None:
    forbidden = {"unknown", "unspecified", "other", "none", "null", "manual_review", "manual_review_confirmed", "inferred", "predicted"}
    assert len(gate.CANONICAL_ENUM_MEMBERS) == 3
    assert forbidden.isdisjoint(gate.CANONICAL_ENUM_MEMBERS)
    assert all(row["alias_allowed"] == "false" for row in gate._enum_registry_rows())


@pytest.mark.parametrize("value", gate.CANONICAL_ENUM_MEMBERS)
def test_scalar_exact_canonical_preservation_without_normalization(value: str) -> None:
    result = gate.validate_covalent_event_evidence_source_design(value)
    assert result == gate.ScalarValidationDesign("canonical", value, "")


@pytest.mark.parametrize("value", [None, 1, True, [], {}, type("S", (str,), {})("explicit_structure_bond_record")])
def test_scalar_exact_type_rejection(value: object) -> None:
    result = gate.validate_covalent_event_evidence_source_design(value)
    assert result.classification == "invalid"
    assert result.reason == "COVALENT_EVENT_EVIDENCE_SOURCE_TYPE_INVALID"


@pytest.mark.parametrize("value,reason", [
    ("", "COVALENT_EVENT_EVIDENCE_SOURCE_EMPTY"),
    ("évidence", "COVALENT_EVENT_EVIDENCE_SOURCE_NON_ASCII"),
    (" explicit_structure_bond_record", "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID"),
    ("explicit_structure_bond_record ", "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID"),
    ("Explicit_structure_bond_record", "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID"),
    ("a" * 65, "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID"),
])
def test_scalar_validation_precedence_and_no_trim_casefold(value: str, reason: str) -> None:
    result = gate.validate_covalent_event_evidence_source_design(value)
    assert result.classification == "invalid" and result.canonical_value == "" and result.reason == reason


@pytest.mark.parametrize("value", ["unregistered_value", "explicit_database_bond", "manual_review", "manual_review_confirmed", "other", "unknown"])
def test_syntactically_valid_unknowns_fail_closed_without_mapping(value: str) -> None:
    result = gate.validate_covalent_event_evidence_source_design(value)
    assert result == gate.ScalarValidationDesign("unknown", "", "COVALENT_EVENT_EVIDENCE_SOURCE_UNKNOWN")


def test_context_exact2_tuple_is_the_only_valid_context() -> None:
    exact = ("explicit_structure_bond_record", "explicit_curated_covalent_annotation")
    assert gate.ALLOWED_COVALENT_EVIDENCE_CLASSES == exact
    assert gate.validate_allowed_covalent_evidence_classes_design(exact) == gate.ContextValidationDesign(True, "")


@pytest.mark.parametrize("value", [None, [], set(), frozenset()])
def test_context_rejects_non_tuple_types(value: object) -> None:
    result = gate.validate_allowed_covalent_evidence_classes_design(value)
    assert result == gate.ContextValidationDesign(False, "ALLOWED_COVALENT_EVIDENCE_CLASSES_TYPE_INVALID")


def test_context_rejects_wrong_content_order_duplicate_extra_unknown_and_subclass() -> None:
    a, b = gate.ALLOWED_COVALENT_EVIDENCE_CLASSES
    subclass = type("S", (str,), {})
    values = [(b, a), (a,), (a, a), (a, b, "distance_only_inference"), (a, b, "unknown"), (subclass(a), b), (a, b, "extra")]
    assert all(gate.validate_allowed_covalent_evidence_classes_design(value).reason == "ALLOWED_COVALENT_EVIDENCE_CLASSES_CONTENT_INVALID" for value in values)


@pytest.mark.parametrize("value", gate.ALLOWED_COVALENT_EVIDENCE_CLASSES)
def test_explicit_members_pass_both_rules(value: str) -> None:
    result = gate.classify_admit_006_admit_007_evidence_design(value)
    expected = gate.RuleOutcomeDesign("passed", True, False, "")
    assert result.admit_006 == expected and result.admit_007 == expected


def test_distance_only_has_two_distinct_rule_specific_blockers() -> None:
    result = gate.classify_admit_006_admit_007_evidence_design("distance_only_inference")
    assert result.admit_006 == gate.RuleOutcomeDesign("blocked", False, True, "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT")
    assert result.admit_007 == gate.RuleOutcomeDesign("blocked", False, True, "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE")


def test_malformed_unknown_and_context_invalid_map_both_rules_to_invalid() -> None:
    cases = [(None, gate.ALLOWED_COVALENT_EVIDENCE_CLASSES), ("unknown", gate.ALLOWED_COVALENT_EVIDENCE_CLASSES), (gate.CANONICAL_ENUM_MEMBERS[0], list(gate.ALLOWED_COVALENT_EVIDENCE_CLASSES))]
    for scalar, context in cases:
        result = gate.classify_admit_006_admit_007_evidence_design(scalar, context)
        assert result.admit_006.outcome == result.admit_007.outcome == "invalid"
        assert result.admit_006.reason == result.admit_007.reason
        assert result.admit_006.blocks_candidate and result.admit_007.blocks_candidate


def test_scalar_failure_precedes_context_failure() -> None:
    result = gate.classify_admit_006_admit_007_evidence_design(None, None)
    assert result.admit_006.reason == result.admit_007.reason == "COVALENT_EVENT_EVIDENCE_SOURCE_TYPE_INVALID"
    assert result.context.reason == "ALLOWED_COVALENT_EVIDENCE_CLASSES_TYPE_INVALID"


def test_design_oracle_is_deterministic_and_has_no_io(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("I/O attempted")
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    first = gate.classify_admit_006_admit_007_evidence_design("distance_only_inference")
    second = gate.classify_admit_006_admit_007_evidence_design("distance_only_inference")
    assert first == second


def test_truth_matrix_has_37_unique_nonpadding_cases_and_exact_groups() -> None:
    rows = gate._truth_matrix_rows()
    assert len(rows) == len({row["case_id"] for row in rows}) == 37
    assert {group: sum(row["case_group"] == group for row in rows) for group in (
        "canonical", "scalar_type", "empty_syntax", "unknown", "context"
    )} == {"canonical": 3, "scalar_type": 6, "empty_syntax": 11, "unknown": 5, "context": 12}
    assert all(row["case_passed"] == "true" for row in rows)


def test_responsibility_matrix_keeps_shared_validator_and_two_rules_separate() -> None:
    rows = gate._responsibility_rows()
    assert len(rows) == 3
    assert [row["rule_id"] for row in rows] == ["SHARED", "ADMIT_006", "ADMIT_007"]
    assert rows[1]["blocked_reason"] != rows[2]["blocked_reason"]
    assert "cross-rule aggregation is not frozen" in rows[2]["responsibility_boundary"]


def test_issue_exact11_changes_only_enum_status_and_transition() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    predecessor = gate._csv_document(snapshot, gate.AUDIT_ISSUE_PATH).rows
    successor = gate._issue_rows(predecessor)
    changed = []
    for old, new in zip(predecessor, successor, strict=True):
        differences = {key for key in old if old[key] != new[key]}
        if differences:
            changed.append((new["issue_id"], differences))
    assert changed == [("COVALENT_EVIDENCE_ENUM_UNRESOLVED", {"status", "integration_transition"})]
    assert sum(row["status"] == "open" for row in successor) == 10
    coverage = next(row for row in successor if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert "ADMIT_006" in coverage["affected_rules"].split("|")


def test_manifest_readiness_is_truthful_and_does_not_overclaim(tmp_path: Path) -> None:
    manifest = gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(tmp_path)["manifest"]
    assert all(manifest[key] is True for key in gate.TRUE_READINESS)
    assert all(manifest[key] is False for key in gate.FALSE_READINESS)
    assert manifest["observed_evidence_value_count"] == 0
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP


def test_exact_six_outputs_are_byte_deterministic(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(tmp_path)
    first = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(tmp_path)
    second = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    assert first == second and set(first) == set(gate.OUTPUT_FILES)


def test_unexpected_output_entry_fails_closed_without_deletion(tmp_path: Path) -> None:
    unexpected = tmp_path / "unexpected.txt"
    unexpected.write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(tmp_path)
    assert unexpected.read_text(encoding="utf-8") == "keep"


def test_symlink_output_victim_is_not_modified(tmp_path: Path) -> None:
    victim = tmp_path / "victim.txt"
    victim.write_text("unchanged", encoding="utf-8")
    output = tmp_path / "output"
    output.mkdir()
    (output / gate.SOURCE_BOUNDARY_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError, match="unsafe"):
        gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(output)
    assert victim.read_text(encoding="utf-8") == "unchanged"


def test_symlink_output_root_fails_closed(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="real non-symlink"):
        gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(link)


def test_no_temporary_or_part_files_remain(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(tmp_path)
    assert not [path for path in tmp_path.iterdir() if path.suffix in {".tmp", ".part"}]


def test_checker_rejects_tamper_overclaim_extra_and_missing(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(tmp_path)
    checker = _load_checker()
    checker._validate_disk(tmp_path, enforce_frozen_hashes=False)
    truth = tmp_path / gate.TRUTH_MATRIX_FILENAME
    original = truth.read_bytes()
    truth.write_bytes(original + b"tamper")
    with pytest.raises(AssertionError):
        checker._validate_disk(tmp_path, enforce_frozen_hashes=False)
    truth.write_bytes(original)
    manifest_path = tmp_path / gate.MANIFEST_FILENAME
    manifest_original = manifest_path.read_bytes()
    manifest = json.loads(manifest_original)
    manifest["ready_for_training"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._validate_disk(tmp_path, enforce_frozen_hashes=False)
    manifest_path.write_bytes(manifest_original)
    extra = tmp_path / "extra"
    extra.write_text("x", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._validate_disk(tmp_path, enforce_frozen_hashes=False)
    extra.unlink()
    (tmp_path / gate.ENUM_REGISTRY_FILENAME).unlink()
    with pytest.raises(AssertionError):
        checker._validate_disk(tmp_path, enforce_frozen_hashes=False)


def test_checker_rejects_self_consistent_wrong_scalar_and_rule_reasons_without_frozen_hashes(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(tmp_path)
    checker = _load_checker()

    def mutate(rows: list[dict[str, str]]) -> None:
        row = next(item for item in rows if item["case_id"] == "CASE_004_type_none")
        wrong = "COVALENT_EVENT_EVIDENCE_SOURCE_EMPTY"
        row["expected_scalar_reason"] = wrong
        row["expected_admit_006_reason"] = wrong
        row["expected_admit_007_reason"] = wrong

    _rewrite_truth_and_refresh_manifest_hash(tmp_path, mutate)
    with pytest.raises(AssertionError):
        checker._validate_disk(tmp_path, enforce_frozen_hashes=False)


def test_checker_rejects_canonical_explicit_member_wrongly_blocked_without_frozen_hashes(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(tmp_path)
    checker = _load_checker()

    def mutate(rows: list[dict[str, str]]) -> None:
        row = next(item for item in rows if item["case_id"] == "CASE_001_canonical_structure_bond")
        row["expected_admit_006_outcome"] = "blocked"
        row["expected_admit_006_reason"] = "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT"

    _rewrite_truth_and_refresh_manifest_hash(tmp_path, mutate)
    with pytest.raises(AssertionError):
        checker._validate_disk(tmp_path, enforce_frozen_hashes=False)


def test_checker_rejects_self_consistent_wrong_context_semantics_without_frozen_hashes(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(tmp_path)
    checker = _load_checker()

    def mutate(rows: list[dict[str, str]]) -> None:
        row = next(item for item in rows if item["case_id"] == "CASE_027_context_none")
        row["expected_context_valid"] = "true"
        row["expected_context_reason"] = ""
        row["expected_admit_006_outcome"] = "passed"
        row["expected_admit_006_reason"] = ""
        row["expected_admit_007_outcome"] = "passed"
        row["expected_admit_007_reason"] = ""

    _rewrite_truth_and_refresh_manifest_hash(tmp_path, mutate)
    with pytest.raises(AssertionError):
        checker._validate_disk(tmp_path, enforce_frozen_hashes=False)


def test_checker_independent_contract_constants_are_exact_and_complete() -> None:
    checker = _load_checker()
    assert checker.IndependentOracleResult._fields == (
        "scalar_classification", "canonical_value", "scalar_reason",
        "context_valid", "context_reason", "admit_006_outcome",
        "admit_006_reason", "admit_007_outcome", "admit_007_reason",
    )
    result = checker._independent_oracle(
        "explicit_structure_bond_record",
        ("explicit_structure_bond_record", "explicit_curated_covalent_annotation"),
    )
    with pytest.raises(AttributeError):
        result.scalar_reason = "changed"
    assert checker.INDEPENDENT_CANONICAL_ENUM_MEMBERS == (
        "explicit_structure_bond_record", "explicit_curated_covalent_annotation", "distance_only_inference"
    )
    assert checker.INDEPENDENT_ALLOWED_CONTEXT == (
        "explicit_structure_bond_record", "explicit_curated_covalent_annotation"
    )
    assert checker.INDEPENDENT_SCALAR_SYNTAX == r"[a-z][a-z0-9_]{0,63}"
    assert checker.INDEPENDENT_SCALAR_VALIDATION_PRECEDENCE == (
        "exact_type", "nonempty", "ascii", "syntax", "membership"
    )
    assert checker.INDEPENDENT_TRUTH_MATRIX_COLUMNS == gate.TRUTH_MATRIX_COLUMNS
    assert checker.INDEPENDENT_TRUTH_GROUP_COUNTS == (
        ("canonical", 3), ("scalar_type", 6), ("empty_syntax", 11),
        ("unknown", 5), ("context", 12),
    )
    assert tuple(checker.INDEPENDENT_SCALAR_REASONS.values()) == gate.SCALAR_REASONS
    assert tuple(checker.INDEPENDENT_CONTEXT_REASONS.values()) == gate.CONTEXT_REASONS
    assert set(checker.INDEPENDENT_ADMIT_006_MAPPING) == set(checker.INDEPENDENT_CANONICAL_ENUM_MEMBERS)
    assert set(checker.INDEPENDENT_ADMIT_007_MAPPING) == set(checker.INDEPENDENT_CANONICAL_ENUM_MEMBERS)


def test_checker_independent_oracle_and_truth_builder_ast_have_no_gate_semantic_dependency() -> None:
    checker = _load_checker()
    checker._validate_independent_ast()
    tree = ast.parse(CHECKER_PATH.read_text(encoding="utf-8"))
    protected_functions = {
        "_independent_oracle", "_independent_display", "_independent_truth_cases", "_independent_truth_rows"
    }
    nodes = {
        node.name: node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in protected_functions
    }
    assert set(nodes) == protected_functions
    forbidden_names = {
        "CANONICAL_ENUM_MEMBERS", "ALLOWED_COVALENT_EVIDENCE_CLASSES", "SCALAR_REASONS",
        "CONTEXT_REASONS", "validate_covalent_event_evidence_source_design",
        "validate_allowed_covalent_evidence_classes_design",
        "classify_admit_006_admit_007_evidence_design", "_truth_definitions",
        "_truth_matrix_rows",
    }
    for node in nodes.values():
        assert not any(
            isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name) and child.value.id == "gate"
            for child in ast.walk(node)
        )
        assert not forbidden_names.intersection(
            child.id for child in ast.walk(node) if isinstance(child, ast.Name)
        )


def test_checker_independent_truth_survives_production_monkeypatch_but_cross_check_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    before = checker._independent_truth_rows()

    def wrong_scalar(value: object) -> gate.ScalarValidationDesign:
        return gate.ScalarValidationDesign("invalid", "", "COVALENT_EVENT_EVIDENCE_SOURCE_EMPTY")

    monkeypatch.setattr(checker.gate, "validate_covalent_event_evidence_source_design", wrong_scalar)
    assert checker._independent_truth_rows() == before
    with pytest.raises(AssertionError):
        checker._validate_oracles()


def test_production_contains_no_evaluator_adapter_or_registry_implementation() -> None:
    source = Path(gate.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert "evaluate_admit_006" not in functions
    assert "evaluate_admit_007" not in functions
    assert "evaluate_all_rules" not in functions
    assigned = {target.id for node in tree.body if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)}
    assert "EVALUATOR_REGISTRY" not in assigned
    assert not any("adapter" in name for name in functions)


def test_runtime_remains_exact5_and_admit006_007_unregistered() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    tree = gate._ast_document(snapshot, gate.RUNTIME_SOURCE_PATH)
    assert gate._registry_keys(tree) == tuple(f"ADMIT_{index:03d}" for index in range(1, 6))


def test_materializer_does_not_mutate_exact12_sources(tmp_path: Path) -> None:
    before = {path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate.SOURCE_PATHS}
    gate.run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(tmp_path)
    after = {path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate.SOURCE_PATHS}
    assert before == after == gate.SOURCE_SHA256
