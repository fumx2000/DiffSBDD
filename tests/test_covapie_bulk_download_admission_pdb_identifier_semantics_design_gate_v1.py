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

from covalent_ext import covapie_bulk_download_admission_pdb_identifier_semantics_design_gate as gate  # noqa: E402


def _hashes(root: Path) -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.iterdir() if path.is_file()}


def _source_hashes() -> dict[str, str]:
    return {path.as_posix(): hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate._source_paths()}


def _load_check_module() -> object:
    path = REPO_ROOT / "scripts" / "check_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1.py"
    spec = importlib.util.spec_from_file_location("step14au_b1_check", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_rows(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_import_has_no_output_side_effect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    importlib.reload(gate)
    assert not (tmp_path / gate.DEFAULT_OUTPUT_ROOT).exists()


def test_exact_six_outputs_are_deterministic(tmp_path: Path) -> None:
    first = gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1(tmp_path)
    first_hashes = _hashes(tmp_path)
    second = gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1(tmp_path)
    assert first == second
    assert first_hashes == _hashes(tmp_path)
    assert sorted(first_hashes) == sorted([*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME])


def test_sources_are_fixed_tracked_metadata_and_unchanged(tmp_path: Path) -> None:
    before = _source_hashes()
    manifest = gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1(tmp_path)
    assert before == gate.SOURCE_SHA256
    assert _source_hashes() == before
    assert manifest["source_input_count"] == 8


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: rows.pop(),
        lambda rows: rows.append(copy.deepcopy(rows[0])),
        lambda rows: rows.reverse(),
        lambda rows: rows[1].__setitem__("source_relative_path", rows[0]["source_relative_path"]),
        lambda rows: rows[0].__setitem__("source_relative_path", "data/derived/unknown.csv"),
        lambda rows: rows[0].__setitem__("tracked_by_git", "false"),
        lambda rows: rows[0].__setitem__("regular_file", "false"),
        lambda rows: rows[0].__setitem__("symlink", "true"),
        lambda rows: rows[0].__setitem__("sha256_expected", "0" * 64),
        lambda rows: rows[0].__setitem__("sha256_observed", "0" * 64),
        lambda rows: rows[0].__setitem__("source_boundary_passed", "false"),
        lambda rows: rows[0].__setitem__("extra", "forbidden"),
    ],
)
def test_source_rows_validator_fails_closed_for_all_shape_or_evidence_drift(mutate: object) -> None:
    rows = gate._source_boundary_rows()
    assert gate._validate_source_rows(rows) is True
    mutate(rows)  # type: ignore[operator]
    assert gate._validate_source_rows(rows) is False


def test_empty_source_rows_fail_closed_in_materialization_and_manifest() -> None:
    assert gate._validate_source_rows([]) is False
    materialization = gate._build_materialization(source_rows=[])
    manifest = gate._build_manifest(materialization, {name: "0" * 64 for name in gate.CSV_OUTPUTS})
    assert materialization["source_passed"] is False
    assert materialization["all_passed"] is False
    assert manifest["all_source_boundary_checks_passed"] is False
    assert manifest["all_checks_passed"] is False
    assert manifest["pdb_identifier_semantics_contract_frozen"] is False
    assert manifest["ready_for_pdb_identifier_semantics_integration"] is False
    assert manifest["blocking_reasons"] == ["pdb_identifier_source_boundary_failed"]
    assert materialization["issue_rows"] == [{
        "issue_id": "PDB_IDENTIFIER_SOURCE_BOUNDARY_VALIDATION_FAILED",
        "issue_type": "pdb_identifier_source_boundary_validation_failure",
        "severity": "blocking", "status": "open", "issue_count": "1",
        "blocking_reason": "pdb_identifier_source_boundary_failed",
    }]


@pytest.mark.parametrize(
    ("value", "form", "canonical", "normalized"),
    [
        ("1abc", "legacy_4_character", "pdb_00001abc", True),
        ("1ABC", "legacy_4_character", "pdb_00001abc", True),
        ("9xyz", "legacy_4_character", "pdb_00009xyz", True),
        ("0abc", "legacy_4_character", "pdb_00000abc", True),
        ("pdb_00001abc", "extended_12_character", "pdb_00001abc", False),
        ("PDB_00001ABC", "extended_12_character", "pdb_00001abc", True),
        ("pDb_1000AbCd", "extended_12_character", "pdb_1000abcd", True),
    ],
)
def test_valid_identifier_normalization(value: str, form: str, canonical: str, normalized: bool) -> None:
    result = gate.normalize_pdb_identifier(value)
    assert (result.input_type_valid, result.input_form, result.syntax_valid) == (True, form, True)
    assert (result.canonical_pdb_id, result.normalization_applied, result.blocking_reason) == (canonical, normalized, "")
    assert gate.CANONICAL_PATTERN.fullmatch(result.canonical_pdb_id) is not None


@pytest.mark.parametrize("value", [" 1abc", "1abc ", "\t1abc", "1abc\n"])
def test_surrounding_whitespace_is_rejected_without_trim(value: str) -> None:
    result = gate.normalize_pdb_identifier(value)
    assert result.syntax_valid is False
    assert result.blocking_reason == "pdb_id_surrounding_whitespace_forbidden"


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("abc", "pdb_id_length_invalid"), ("1abcd", "pdb_id_length_invalid"),
        ("pdb_0001abc", "pdb_id_length_invalid"), ("pdb_000001abc", "pdb_id_length_invalid"),
        ("foo_00001abc", "pdb_id_format_invalid"), ("pdb/1abc", "pdb_id_format_invalid"),
        ("pdb\\1abc", "pdb_id_format_invalid"), ("1abc.", "pdb_id_format_invalid"), ("1abc.cif", "pdb_id_format_invalid"),
        ("1abc.cif.gz", "pdb_id_format_invalid"), ("https://example/1abc", "pdb_id_format_invalid"),
        ("pdb_００００1abc", "pdb_id_non_ascii_forbidden"),
    ],
)
def test_invalid_string_forms_are_rejected(value: str, reason: str) -> None:
    result = gate.normalize_pdb_identifier(value)
    assert (result.input_form, result.syntax_valid, result.canonical_pdb_id, result.blocking_reason) == ("invalid", False, "", reason)


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (None, "pdb_id_missing"), (1234, "pdb_id_not_string"), (1.0, "pdb_id_not_string"),
        (b"1abc", "pdb_id_not_string"), (Path("1abc"), "pdb_id_not_string"),
        (["1abc"], "pdb_id_not_string"), ({"pdb_id": "1abc"}, "pdb_id_not_string"),
    ],
)
def test_non_string_objects_are_never_coerced(value: object, reason: str) -> None:
    result = gate.normalize_pdb_identifier(value)
    assert result.input_type_valid is False
    assert result.syntax_valid is False
    assert result.blocking_reason == reason


def test_leading_zero_is_syntax_only_without_archive_existence_claim() -> None:
    result = gate.normalize_pdb_identifier("0abc")
    assert result.canonical_pdb_id == "pdb_00000abc"
    assert not hasattr(result, "archive_exists")
    assert not hasattr(result, "download_ready")


def test_example_specs_use_real_control_characters_and_display_escapes_them() -> None:
    by_id = {row[0]: row for row in gate._example_specs()}
    assert by_id["EXAMPLE_011"][1] == "\t1abc"
    assert by_id["EXAMPLE_012"][1] == "1abc\n"
    assert by_id["EXAMPLE_011"][1] != r"\t1abc"
    assert by_id["EXAMPLE_012"][1] != r"1abc\n"
    assert gate._display_input("\t1abc") == r"\t1abc"
    assert gate._display_input("1abc\n") == r"1abc\n"


def test_contract_and_safety_exact_validators_fail_closed() -> None:
    contract = gate._contract_rows()
    safety = gate._safety_rows()
    assert gate._validate_contract_rows(contract)
    assert gate._validate_safety_rows(safety)
    for mutation in (
        lambda rows: rows.pop(),
        lambda rows: rows.append(copy.deepcopy(rows[0])),
        lambda rows: rows.reverse(),
        lambda rows: rows[0].__setitem__("required_value", "drift"),
    ):
        candidate = copy.deepcopy(contract)
        mutation(candidate)
        assert gate._validate_contract_rows(candidate) is False
    for mutation in (
        lambda rows: rows.pop(), lambda rows: rows.append(copy.deepcopy(rows[0])),
        lambda rows: rows.reverse(), lambda rows: rows[0].__setitem__("observed_status", "true"),
    ):
        candidate = copy.deepcopy(safety)
        mutation(candidate)
        assert gate._validate_safety_rows(candidate) is False


def test_examples_and_manifest_readiness_are_exact(tmp_path: Path) -> None:
    examples = gate._example_rows()
    assert gate._validate_example_rows(examples)
    assert len(examples) == 29
    assert all(row["example_passed"] == "true" for row in examples)
    assert sum(row["expected_syntax_valid"] == "true" for row in examples) == 7
    assert sum(row["expected_syntax_valid"] == "false" for row in examples) == 22
    examples[1]["expected_canonical_pdb_id"] = "drift"
    assert gate._validate_example_rows(examples) is False
    manifest = gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1(tmp_path)
    assert manifest["issue_count"] == 0 and manifest["blocking_reasons"] == []
    assert manifest["ready_for_pdb_identifier_semantics_integration"] is True
    assert all(manifest[key] is False for key in (
        "ready_for_admission_evaluator_rule_logic_implementation", "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
    ))
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["output_sha256"] == {name: _hashes(tmp_path)[name] for name in gate.CSV_OUTPUTS}
    assert manifest["output_files"] == [*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME]
    assert manifest["output_file_count"] == 6
    assert manifest["non_manifest_output_count"] == 5
    assert manifest["manifest_schema_version"] == gate.MANIFEST_SCHEMA_VERSION
    assert manifest["source_read_boundary"] == "only_step14au_a_6_outputs_and_step14at_schema_rule_metadata_only"
    text = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in text.lower() and "/home/" not in text


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: rows.pop(),
        lambda rows: rows.append(copy.deepcopy(rows[0])),
        lambda rows: rows.reverse(),
        lambda rows: rows[1].__setitem__("example_id", "EXAMPLE_001"),
        lambda rows: rows[1].__setitem__("expected_blocking_reason", "drift"),
    ],
)
def test_example_validator_fails_closed_for_structural_or_expected_drift(mutate: object) -> None:
    rows = gate._example_rows()
    mutate(rows)  # type: ignore[operator]
    assert gate._validate_example_rows(rows) is False


def test_example_validator_rejects_same_regenerated_rows_when_any_example_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = gate._example_rows()
    rows[10]["example_passed"] = "false"
    monkeypatch.setattr(gate, "_example_rows", lambda: copy.deepcopy(rows))
    assert gate._validate_example_rows(rows) is False


def test_injected_failed_example_fails_manifest_and_emits_real_issue() -> None:
    examples = gate._example_rows()
    examples[10]["example_passed"] = "false"
    materialization = gate._build_materialization(example_rows=examples)
    manifest = gate._build_manifest(materialization, {name: "0" * 64 for name in gate.CSV_OUTPUTS})
    assert materialization["examples_passed"] is False
    assert materialization["all_passed"] is False
    assert manifest["all_normalization_example_checks_passed"] is False
    assert manifest["all_checks_passed"] is False
    assert manifest["pdb_identifier_semantics_contract_frozen"] is False
    assert manifest["ready_for_pdb_identifier_semantics_integration"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert manifest["issue_count"] > 0
    assert manifest["blocking_reasons"] == ["pdb_identifier_normalization_examples_failed"]
    assert materialization["issue_rows"][0]["issue_id"] == "PDB_IDENTIFIER_NORMALIZATION_EXAMPLE_VALIDATION_FAILED"
    assert materialization["issue_rows"][0]["issue_id"] != "NO_ISSUES"


def test_check_helper_reads_csv_evidence_and_output_contract(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1(tmp_path)
    check = _load_check_module()
    manifest = json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text())
    hashes = _hashes(tmp_path)
    check._validate_manifest_and_outputs(manifest, tmp_path, hashes)

    bad_examples = list(csv.DictReader((tmp_path / gate.CSV_OUTPUTS[1]).open(encoding="utf-8")))
    bad_examples[0]["example_passed"] = "false"
    _write_rows(tmp_path / gate.CSV_OUTPUTS[1], gate.EXAMPLE_COLUMNS, bad_examples)
    with pytest.raises(AssertionError):
        check._validate_manifest_and_outputs(manifest, tmp_path, hashes)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda manifest: manifest.__setitem__("output_files", [*gate.CSV_OUTPUTS]),
        lambda manifest: manifest.__setitem__("output_files", [gate.CSV_OUTPUTS[1], gate.CSV_OUTPUTS[0], *gate.CSV_OUTPUTS[2:], gate.MANIFEST_FILENAME]),
        lambda manifest: manifest.__setitem__("issue_count", 1),
    ],
)
def test_check_helper_fails_closed_for_manifest_or_issue_drift(tmp_path: Path, mutate: object) -> None:
    gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1(tmp_path)
    check = _load_check_module()
    manifest = json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text())
    mutate(manifest)  # type: ignore[operator]
    with pytest.raises(AssertionError):
        check._validate_manifest_and_outputs(manifest, tmp_path, _hashes(tmp_path))


@pytest.mark.parametrize(
    ("filename", "columns", "mutate"),
    [
        (gate.CSV_OUTPUTS[0], gate.CONTRACT_COLUMNS, lambda rows: rows.pop()),
        (gate.CSV_OUTPUTS[0], gate.CONTRACT_COLUMNS, lambda rows: rows[0].__setitem__("contract_passed", "false")),
        (gate.CSV_OUTPUTS[0], gate.CONTRACT_COLUMNS, lambda rows: rows[0].__setitem__("contract_status", "draft")),
        (gate.CSV_OUTPUTS[2], gate.SOURCE_COLUMNS, lambda rows: rows.pop()),
        (gate.CSV_OUTPUTS[2], gate.SOURCE_COLUMNS, lambda rows: rows[0].__setitem__("sha256_observed", "0" * 64)),
        (gate.CSV_OUTPUTS[2], gate.SOURCE_COLUMNS, lambda rows: rows[0].__setitem__("source_boundary_passed", "false")),
        (gate.CSV_OUTPUTS[3], gate.SAFETY_COLUMNS, lambda rows: rows.pop()),
        (gate.CSV_OUTPUTS[3], gate.SAFETY_COLUMNS, lambda rows: rows[0].__setitem__("observed_status", "true")),
        (gate.CSV_OUTPUTS[3], gate.SAFETY_COLUMNS, lambda rows: rows[0].__setitem__("safety_passed", "false")),
        (gate.CSV_OUTPUTS[4], gate.ISSUE_COLUMNS, lambda rows: rows[0].__setitem__("issue_id", "BLOCKING_ISSUE")),
    ],
)
def test_check_helper_reads_direct_csv_evidence(tmp_path: Path, filename: str, columns: tuple[str, ...], mutate: object) -> None:
    gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1(tmp_path)
    check = _load_check_module()
    rows = list(csv.DictReader((tmp_path / filename).open(encoding="utf-8")))
    mutate(rows)  # type: ignore[operator]
    _write_rows(tmp_path / filename, columns, rows)
    manifest = json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text())
    manifest["output_sha256"] = {name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() for name in gate.CSV_OUTPUTS}
    (tmp_path / gate.MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AssertionError):
        check._validate_manifest_and_outputs(manifest, tmp_path, _hashes(tmp_path))


def test_check_helper_recomputes_current_disk_hashes(tmp_path: Path) -> None:
    gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1(tmp_path)
    check = _load_check_module()
    manifest = json.loads((tmp_path / gate.MANIFEST_FILENAME).read_text())
    hashes = _hashes(tmp_path)
    rows = list(csv.DictReader((tmp_path / gate.CSV_OUTPUTS[0]).open(encoding="utf-8")))
    rows[0]["contract_status"] = "draft"
    _write_rows(tmp_path / gate.CSV_OUTPUTS[0], gate.CONTRACT_COLUMNS, rows)
    with pytest.raises(AssertionError):
        check._validate_manifest_and_outputs(manifest, tmp_path, hashes)


def test_five_canonical_masks_include_b3_and_no_sixth_mask(tmp_path: Path) -> None:
    manifest = gate.run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1(tmp_path)
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]
    assert manifest["canonical_mask_task_count"] == 5
    assert [pair[1] for pair in manifest["canonical_mask_pairs"]] == ["A", "B", "B2", "B3", "C"]


def test_module_has_no_forbidden_runtime_imports() -> None:
    tree = ast.parse((REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_pdb_identifier_semantics_design_gate.py").read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): names.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module: names.add(node.module.split(".")[0])
    assert not names.intersection({"requests", "urllib", "aiohttp", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "shutil"})
