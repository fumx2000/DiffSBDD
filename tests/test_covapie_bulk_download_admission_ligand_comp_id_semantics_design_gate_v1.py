from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate as gate  # noqa: E402


CHECK_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1.py"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hashes(root: Path) -> dict[str, str]:
    return {name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)}


def _source_hashes() -> dict[str, str]:
    return {path.as_posix(): _hash(REPO_ROOT / path) for path in gate._source_paths()}


def _load_check_module() -> object:
    spec = importlib.util.spec_from_file_location("step14au_d1_check", CHECK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _materialize(root: Path) -> tuple[dict[str, object], dict[str, str]]:
    manifest = gate.run_covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1(root)
    return manifest, _hashes(root)


def test_import_has_no_materialization_side_effect(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    result = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate"],
        cwd=tmp_path, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []


def test_exact_six_outputs_are_byte_deterministic(tmp_path: Path) -> None:
    first, hashes = _materialize(tmp_path)
    second = gate.run_covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1(tmp_path)
    assert first == second
    assert hashes == _hashes(tmp_path)
    assert {path.name for path in tmp_path.iterdir()} == {*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME}


def test_manifest_has_no_timestamp_absolute_path_or_self_hash(tmp_path: Path) -> None:
    manifest, _ = _materialize(tmp_path)
    payload = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in payload.lower()
    assert "/home/" not in payload
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]


def test_exact_six_c2_sources_are_tracked_regular_and_hash_stable() -> None:
    before = _source_hashes()
    rows = gate._source_boundary_rows()
    assert gate._validate_source_boundary_rows(rows)
    assert len(rows) == 6
    assert [row["source_relative_path"] for row in rows] == list(gate.SOURCE_SHA256)
    assert all(row["tracked_by_git"] == "true" for row in rows)
    assert all(row["regular_file"] == "true" and row["symlink"] == "false" for row in rows)
    assert before == gate.SOURCE_SHA256 == _source_hashes()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: rows.pop(),
        lambda rows: rows.append(dict(rows[-1])),
        lambda rows: rows.reverse(),
        lambda rows: rows[0].update(sha256_observed="0" * 64),
        lambda rows: rows[0].update(symlink="true"),
        lambda rows: rows[0].update(tracked_by_git="false"),
        lambda rows: rows[0].update(regular_file="false"),
    ],
)
def test_source_boundary_missing_extra_reorder_hash_symlink_and_tracking_fail_closed(
    mutate: object,
) -> None:
    rows = copy.deepcopy(gate._source_boundary_rows())
    mutate(rows)  # type: ignore[operator]
    assert not gate._validate_source_boundary_rows(rows)


def test_c2_predecessor_and_target_rows_are_exact() -> None:
    source = gate._load_source()
    assert gate._validate_source_semantics(source)
    manifest = source["manifest"]
    assert manifest["remaining_issue_count"] == 11
    assert manifest["candidate_record_id_semantics_integrated"] is True
    assert manifest["pdb_identifier_semantics_integrated"] is True
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]
    assert sum(row["issue_id"] == gate.TARGET_BLOCKER for row in source["issue_rows"]) == 1
    rule = gate._one(source["rule_rows"], "admission_rule_id", "ADMIT_003")
    field = gate._one(source["field_rows"], "field_name", "ligand_comp_id")
    context = gate._one(source["context_rows"], "context_item", "ligand_comp_id_contract")
    assert rule and rule["semantics_complete"] == "false" and rule["integration_applied"] == "false"
    assert field and field["implementation_semantics_complete"] == "false"
    assert context and context["implementation_ready"] == "false"


@pytest.mark.parametrize(
    ("value", "canonical"),
    [
        ("JUG", "JUG"), ("jug", "JUG"), ("JuG", "JUG"), ("E64", "E64"),
        ("IN3", "IN3"), ("UFP", "UFP"), ("0QE", "0QE"), ("A", "A"),
        ("1", "1"), ("ABC123", "ABC123"), ("A" * 32, "A" * 32),
        ("a" * 32, "A" * 32),
    ],
)
def test_valid_tokens_normalize_to_expected_uppercase(value: str, canonical: str) -> None:
    result = gate.normalize_ligand_comp_id(value)
    assert result.passed is True
    assert result.input_is_exact_str is True
    assert result.ascii_only is True
    assert result.length_valid is True
    assert result.syntax_valid is True
    assert result.canonical_ligand_comp_id == canonical
    assert result.blocking_reason == ""


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (None, "LIGAND_COMP_ID_TYPE_INVALID"), (b"JUG", "LIGAND_COMP_ID_TYPE_INVALID"),
        (7, "LIGAND_COMP_ID_TYPE_INVALID"), (True, "LIGAND_COMP_ID_TYPE_INVALID"),
        (1.5, "LIGAND_COMP_ID_TYPE_INVALID"), ("", "LIGAND_COMP_ID_EMPTY"),
        ("JÜG", "LIGAND_COMP_ID_NON_ASCII"), ("A" * 33, "LIGAND_COMP_ID_LENGTH_INVALID"),
        (" ", "LIGAND_COMP_ID_SYNTAX_INVALID"), (" JUG", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("JUG ", "LIGAND_COMP_ID_SYNTAX_INVALID"), ("JU G", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("\t", "LIGAND_COMP_ID_SYNTAX_INVALID"), ("\n", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        (".", "LIGAND_COMP_ID_SYNTAX_INVALID"), ("?", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("A-B", "LIGAND_COMP_ID_SYNTAX_INVALID"), ("A_B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("A/B", "LIGAND_COMP_ID_SYNTAX_INVALID"), ("A,B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("A;B", "LIGAND_COMP_ID_SYNTAX_INVALID"), ("A|B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("A:B", "LIGAND_COMP_ID_SYNTAX_INVALID"), ("A+B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
    ],
)
def test_invalid_tokens_fail_with_one_expected_reason(value: object, reason: str) -> None:
    result = gate.normalize_ligand_comp_id(value)
    assert result.passed is False
    assert result.canonical_ligand_comp_id == ""
    assert result.blocking_reason == reason


def test_exact_type_rejects_string_subclass_and_no_coercion() -> None:
    class StringSubclass(str):
        pass

    assert gate.normalize_ligand_comp_id(StringSubclass("JUG")).blocking_reason == "LIGAND_COMP_ID_TYPE_INVALID"
    assert gate.normalize_ligand_comp_id(object()).blocking_reason == "LIGAND_COMP_ID_TYPE_INVALID"


def test_normalization_is_idempotent_and_identity_is_case_insensitive() -> None:
    values = [gate.normalize_ligand_comp_id(value).canonical_ligand_comp_id for value in ("JUG", "jug", "JuG")]
    assert values == ["JUG", "JUG", "JUG"]
    assert gate.normalize_ligand_comp_id(values[0]).canonical_ligand_comp_id == values[0]


def test_error_priority_is_type_then_empty_then_ascii_then_length_then_regex() -> None:
    assert gate.normalize_ligand_comp_id(None).blocking_reason == "LIGAND_COMP_ID_TYPE_INVALID"
    assert gate.normalize_ligand_comp_id("").blocking_reason == "LIGAND_COMP_ID_EMPTY"
    assert gate.normalize_ligand_comp_id("Ü" * 33).blocking_reason == "LIGAND_COMP_ID_NON_ASCII"
    assert gate.normalize_ligand_comp_id("A" * 33 + "-").blocking_reason == "LIGAND_COMP_ID_LENGTH_INVALID"
    assert gate.normalize_ligand_comp_id("A-B").blocking_reason == "LIGAND_COMP_ID_SYNTAX_INVALID"


def test_design_wrapper_never_claims_admit_003_integration() -> None:
    assert gate.evaluate_ligand_comp_id_contract("jug") == {
        "passed": True, "canonical_ligand_comp_id": "JUG", "blocking_reason": "",
        "admit_003_integration_applied": False,
    }


def test_contract_has_exact_32_independently_observed_rows() -> None:
    rows = gate._contract_rows()
    assert gate._validate_contract_rows(rows)
    assert len(rows) == 32
    assert [row["contract_item_id"] for row in rows] == [f"LIGCON_{index:03d}" for index in range(1, 33)]
    assert all(row["observed_value"] == row["expected_value"] for row in rows)
    assert len({row["requirement"] for row in rows}) == 32


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: rows.pop(),
        lambda rows: rows.reverse(),
        lambda rows: rows[0].update(contract_item_id="LIGCON_999"),
        lambda rows: rows[0].update(observed_value="drift", contract_passed="false"),
    ],
)
def test_contract_count_order_identity_and_observation_drift_fail(mutate: object) -> None:
    rows = gate._contract_rows()
    mutate(rows)  # type: ignore[operator]
    assert not gate._validate_contract_rows(rows)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda row: row.update(contract_area="DRIFT"),
        lambda row: row.update(
            requirement="coordinated wrong requirement",
            expected_value="coordinated_wrong_value",
            observed_value="coordinated_wrong_value",
        ),
        lambda row: row.update(
            expected_value="same_wrong_value",
            observed_value="same_wrong_value",
        ),
    ],
)
def test_contract_validator_rejects_coordinated_canonical_row_drift(mutate: object) -> None:
    rows = gate._contract_rows()
    mutate(rows[0])  # type: ignore[operator]
    assert rows[0]["contract_passed"] == "true"
    assert rows[0]["blocking_reason"] == ""
    assert not gate._validate_contract_rows(rows)


def test_examples_have_exact_12_valid_24_invalid_independent_expectations() -> None:
    specs = gate._example_specs()
    rows = gate._example_rows()
    assert len(specs) == len(rows) == 36
    assert sum(spec.expected_passed for spec in specs) == 12
    assert sum(not spec.expected_passed for spec in specs) == 24
    assert gate._validate_example_rows(rows)
    assert all(row["example_passed"] == "true" for row in rows)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: rows.pop(),
        lambda rows: rows.reverse(),
        lambda rows: rows[0].update(example_class="invalid"),
        lambda rows: rows[0].update(expected_canonical_ligand_comp_id="DRIFT", example_passed="false"),
    ],
)
def test_example_count_class_order_and_expected_drift_fail(mutate: object) -> None:
    rows = gate._example_rows()
    mutate(rows)  # type: ignore[operator]
    assert not gate._validate_example_rows(rows)


@pytest.mark.parametrize(
    ("row_index", "mutate"),
    [
        (0, lambda row: row.update(input_kind="DRIFT")),
        (0, lambda row: row.update(
            expected_canonical_ligand_comp_id="WRONG",
            observed_canonical_ligand_comp_id="WRONG",
        )),
        (12, lambda row: row.update(
            expected_blocking_reason="WRONG_REASON",
            observed_blocking_reason="WRONG_REASON",
        )),
        (0, lambda row: row.update(input_literal="coordinated_wrong_literal")),
    ],
)
def test_example_validator_rejects_coordinated_canonical_row_drift(
    row_index: int,
    mutate: object,
) -> None:
    rows = gate._example_rows()
    mutate(rows[row_index])  # type: ignore[operator]
    assert rows[row_index]["example_passed"] == "true"
    assert not gate._validate_example_rows(rows)


def test_canonical_contract_and_example_rows_still_validate() -> None:
    assert gate._validate_contract_rows(gate._contract_rows()) is True
    assert gate._validate_example_rows(gate._example_rows()) is True


def test_contract_builder_failure_propagates_to_section_and_issue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical_examples = gate._example_rows()
    original_probe = gate._probe

    def wrong_probe(value: object) -> gate.LigandCompIdNormalizationResult:
        if value == "JuG":
            return gate.LigandCompIdNormalizationResult(
                passed=True,
                input_is_exact_str=True,
                ascii_only=True,
                length_valid=True,
                syntax_valid=True,
                canonical_ligand_comp_id="WRONG",
                blocking_reason="",
            )
        return original_probe(value)

    monkeypatch.setattr(gate, "_probe", wrong_probe)
    contract_rows = gate._contract_rows()
    assert any(row["contract_passed"] == "false" for row in contract_rows)
    assert gate._validate_contract_rows(contract_rows) is False

    result = gate._build_materialization(
        contract_rows=contract_rows,
        example_rows=canonical_examples,
    )
    assert result["all_contract_checks_passed"] is False
    assert result["all_example_checks_passed"] is True
    assert result["all_checks_passed"] is False
    assert [row["issue_id"] for row in result["issue_rows"]] == [
        "LIGAND_COMP_ID_DESIGN_CONTRACT_VALIDATION_FAILED"
    ]


def test_example_builder_failure_propagates_to_section_and_issue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical_contract = gate._contract_rows()
    original_normalize = gate.normalize_ligand_comp_id

    def wrong_normalize(value: object) -> gate.LigandCompIdNormalizationResult:
        if value == "E64":
            return gate.LigandCompIdNormalizationResult(
                passed=True,
                input_is_exact_str=True,
                ascii_only=True,
                length_valid=True,
                syntax_valid=True,
                canonical_ligand_comp_id="WRONG",
                blocking_reason="",
            )
        return original_normalize(value)

    monkeypatch.setattr(gate, "normalize_ligand_comp_id", wrong_normalize)
    example_rows = gate._example_rows()
    assert any(row["example_passed"] == "false" for row in example_rows)
    assert gate._validate_example_rows(example_rows) is False

    result = gate._build_materialization(
        contract_rows=canonical_contract,
        example_rows=example_rows,
    )
    assert result["all_contract_checks_passed"] is True
    assert result["all_example_checks_passed"] is False
    assert result["all_checks_passed"] is False
    assert [row["issue_id"] for row in result["issue_rows"]] == [
        "LIGAND_COMP_ID_DESIGN_EXAMPLE_VALIDATION_FAILED"
    ]


def test_semantic_non_goals_are_explicit_and_multi_component_rejected() -> None:
    requirements = {row["requirement"] for row in gate._contract_rows()}
    assert {
        "no registry membership claim", "no raw presence claim", "no nonpolymer claim",
        "no drug-likeness claim", "no chemical equivalence claim", "not candidate_record_id",
        "not duplicate_identity_key", "not ligand graph identity",
    }.issubset(requirements)
    assert not gate.normalize_ligand_comp_id("JUG E64").passed
    assert not gate.normalize_ligand_comp_id("JUG|E64").passed


def test_safety_has_exact_19_false_observations() -> None:
    rows = gate._safety_rows()
    assert len(rows) == 19
    assert gate._validate_safety_rows(rows)
    assert all(
        row["required_status"] == "false" and row["observed_status"] == "false"
        and row["safety_passed"] == "true" and row["blocking_reason"] == ""
        for row in rows
    )


def test_any_safety_overclaim_fails_closed() -> None:
    rows = gate._safety_rows()
    rows[0]["observed_status"] = "true"
    assert not gate._validate_safety_rows(rows)
    result = gate._build_materialization(safety_rows=rows)
    assert result["all_checks_passed"] is False
    assert result["issue_rows"][0]["issue_id"] == "LIGAND_COMP_ID_DESIGN_SAFETY_VALIDATION_FAILED"


def test_normal_issue_inventory_is_no_issues_without_effective_blocker_removal() -> None:
    result = gate._build_materialization()
    assert result["issue_rows"] == [{
        "issue_id": "NO_ISSUES", "issue_type": "no_ligand_comp_id_semantics_design_issues",
        "severity": "none", "status": "no_issues", "issue_count": "0", "blocking_reason": "",
    }]
    assert gate.TARGET_BLOCKER in [row["issue_id"] for row in gate._load_source()["issue_rows"]]


def test_manifest_design_readiness_and_boundaries_are_truthful(tmp_path: Path) -> None:
    manifest, _ = _materialize(tmp_path)
    assert manifest["ligand_comp_id_semantics_frozen"] is True
    assert manifest["ligand_comp_id_semantics_integrated"] is False
    assert manifest["integration_applied_current_step"] is False
    assert manifest["admit_003_rule_logic_ready"] is False
    assert manifest["upstream_effective_issue_count"] == 11
    assert manifest["expected_post_integration_issue_count"] == 10
    assert manifest["resolved_design_issue_ids"] == [gate.TARGET_BLOCKER]
    assert manifest["ready_for_ligand_comp_id_semantics_integration"] is True
    assert all(manifest[key] is False for key in (
        "ready_for_admission_evaluator_rule_logic_implementation", "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
    ))
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP


def test_five_canonical_masks_include_b3_without_sixth_mask() -> None:
    assert gate.CANONICAL_MASK_PAIRS == (
        ("warhead_only", "A"), ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"), ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    )


def test_production_has_no_forbidden_imports_or_self_inspection() -> None:
    path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate.py"
    source = path.read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint({
        "requests", "urllib", "aiohttp", "torch", "numpy", "rdkit", "gemmi", "Bio",
        "pandas", "sklearn", "inspect", "ast", "importlib",
    })
    assert all(token not in source for token in (
        "model.forward", "trainer.fit", "importlib.reload", "inspect.getsource",
        "Path(__file__).read_text",
    ))


@pytest.mark.parametrize(
    ("filename", "needle"),
    [
        (gate.CSV_OUTPUTS[0], "LIGCON_001"),
        (gate.CSV_OUTPUTS[1], "LIGEX_001"),
        (gate.CSV_OUTPUTS[2], "source_relative_path"),
        (gate.CSV_OUTPUTS[3], "network_access_used_current_step"),
        (gate.CSV_OUTPUTS[4], "NO_ISSUES"),
    ],
)
def test_check_rejects_output_and_evidence_drift(tmp_path: Path, filename: str, needle: str) -> None:
    manifest, first = _materialize(tmp_path)
    path = tmp_path / filename
    path.write_text(path.read_text(encoding="utf-8").replace(needle, needle + "_DRIFT", 1), encoding="utf-8")
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(manifest, tmp_path, first)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("output_file_count", 7), ("contract_row_count", 31),
        ("canonical_mask_task_count", 6), ("upstream_effective_issue_count", 10),
        ("ligand_comp_id_semantics_integrated", True), ("admit_003_rule_logic_ready", True),
        ("ready_for_real_candidate_evaluation", True), ("ready_for_bulk_download_now", True),
        ("ready_for_training", True),
    ],
)
def test_check_rejects_manifest_count_mask_integration_and_readiness_overclaim(
    tmp_path: Path, key: str, value: object,
) -> None:
    manifest, _ = _materialize(tmp_path)
    manifest[key] = value
    (tmp_path / gate.MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(manifest, tmp_path, _hashes(tmp_path))


def test_check_rejects_source_hash_drift(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    manifest, hashes = _materialize(tmp_path)
    monkeypatch.setitem(gate.SOURCE_SHA256, next(iter(gate.SOURCE_SHA256)), "0" * 64)
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(manifest, tmp_path, hashes)


def test_check_rejects_output_modified_after_first_hash(tmp_path: Path) -> None:
    manifest, hashes = _materialize(tmp_path)
    path = tmp_path / gate.CSV_OUTPUTS[0]
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(AssertionError):
        _load_check_module()._validate_manifest_and_outputs(manifest, tmp_path, hashes)


@pytest.mark.parametrize("case", ["extra", "missing", "symlink"])
def test_check_rejects_extra_missing_and_symlink_output(tmp_path: Path, case: str) -> None:
    manifest, _ = _materialize(tmp_path)
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
