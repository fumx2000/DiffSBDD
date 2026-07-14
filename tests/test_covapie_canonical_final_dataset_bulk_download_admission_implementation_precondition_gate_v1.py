from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate as gate,
)


def _hashes(root: Path) -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.iterdir() if path.is_file()}


def _source_hashes() -> dict[str, str]:
    return {path.as_posix(): hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate._source_paths()}


def _result(**overrides: object) -> dict[str, object]:
    return gate._build_materialization(copy.deepcopy(gate._load_source()), **overrides)


def _rule_rows() -> list[dict[str, str]]:
    contexts = gate._context_rows()
    return gate._rule_rows(contexts)


def _field_rows() -> list[dict[str, str]]:
    source = gate._load_source()
    contexts = gate._context_rows()
    rules = gate._rule_rows(contexts)
    return gate._field_rows(source["schema"], contexts, rules)


def _load_check_module() -> object:
    path = REPO_ROOT / "scripts" / "check_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1.py"
    spec = importlib.util.spec_from_file_location("step14au_a_check", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _valid_manifest_and_hashes(tmp_path: Path) -> tuple[dict[str, object], dict[str, str]]:
    manifest = gate.run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1(tmp_path)
    hashes = {name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)}
    return manifest, hashes


def test_import_has_no_output_side_effect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    importlib.reload(gate)
    assert not (tmp_path / gate.DEFAULT_OUTPUT_ROOT).exists()


def test_exact_six_outputs_are_deterministic_and_truthfully_blocked(tmp_path: Path) -> None:
    first = gate.run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1(tmp_path)
    first_hashes = _hashes(tmp_path)
    second = gate.run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1(tmp_path)
    assert first_hashes == _hashes(tmp_path)
    assert first["precondition_audit_completed"] is True
    assert second["all_checks_passed"] is False
    assert sorted(first_hashes) == sorted([*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME])


def test_step14at_sources_are_fixed_tracked_metadata_and_unchanged(tmp_path: Path) -> None:
    before = _source_hashes()
    manifest = gate.run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1(tmp_path)
    assert before == gate.SOURCE_SHA256
    assert _source_hashes() == before
    assert manifest["source_input_count"] == 6
    assert "data/raw" not in json.dumps(manifest["source_input_sha256"], sort_keys=True)


def test_rule_dependency_contract_and_rule_semantics_are_separate() -> None:
    result = _result()
    assert result["all_rule_dependency_contract_checks_passed"] is True
    assert result["all_rule_semantics_complete"] is False
    assert result["ready_for_admission_evaluator_rule_logic_implementation"] is False


def test_unresolved_rules_do_not_claim_executability_passed_semantics() -> None:
    row = _rule_rows()[1]
    assert "rule_executability_passed" not in row
    assert row["dependency_contract_passed"] == "true"
    assert row["semantics_complete"] == "false"
    assert row["deterministic_evaluation_possible_now"] == "false"
    assert row["implementation_disposition"] == "interface_only_pending_semantics"


def test_rule_ids_order_and_no_admit_016_are_exact() -> None:
    rows = _rule_rows()
    assert [row["admission_rule_id"] for row in rows] == [f"ADMIT_{index:03d}" for index in range(1, 16)]
    assert len({row["admission_rule_id"] for row in rows}) == 15
    assert "ADMIT_016" not in {row["admission_rule_id"] for row in rows}


def test_admit_001_and_009_require_distinct_batch_uniqueness_contexts() -> None:
    rows = _rule_rows()
    assert rows[0]["batch_context_dependencies"] == "batch_candidate_record_ids"
    assert rows[8]["batch_context_dependencies"] == "batch_duplicate_identity_keys"


def test_admit_010_only_requires_leakage_group_at_pre_final_split() -> None:
    row = _rule_rows()[9]
    assert row["evaluation_phase"] == "pre_final_split"
    assert row["candidate_field_dependencies"] == "leakage_group_id"


@pytest.mark.parametrize("index", [11, 12])
def test_post_download_rules_require_download_execution_result(index: int) -> None:
    row = _rule_rows()[index]
    assert row["download_execution_result_required"] == "true"
    assert row["evaluation_phase"] == "post_download"


def test_admit_012_and_013_include_both_download_blockers_in_sorted_order() -> None:
    expected = "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED|DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED"
    rows = _rule_rows()
    assert rows[11]["blocking_reasons"] == expected
    assert rows[12]["blocking_reasons"] == expected


def test_batch_duplicate_identity_keys_is_explicit_batch_context_for_admit_009() -> None:
    contexts = {row["context_item"]: row for row in gate._context_rows()}
    assert contexts["batch_duplicate_identity_keys"]["context_scope"] == "batch"
    assert contexts["batch_duplicate_identity_keys"]["required_by_rules"] == "ADMIT_009"
    assert _rule_rows()[8]["batch_context_dependencies"] == "batch_duplicate_identity_keys"


def test_missing_batch_duplicate_identity_keys_fails_context_and_dependency_contracts() -> None:
    contexts = [row for row in gate._context_rows() if row["context_item"] != "batch_duplicate_identity_keys"]
    result = _result(context_rows=contexts)
    assert result["all_evaluation_context_contract_checks_passed"] is False
    assert result["all_rule_dependency_contract_checks_passed"] is False
    assert result["ready_for_admission_evaluator_interface_implementation"] is False


@pytest.mark.parametrize(
    ("column", "replacement"),
    [
        ("batch_context_dependencies", "batch_unknown"),
        ("candidate_field_dependencies", "unknown_candidate_field"),
        ("evaluation_context_dependencies", "unknown_evaluation_context"),
    ],
)
def test_unknown_rule_dependencies_fail_closed(column: str, replacement: str) -> None:
    rows = _rule_rows()
    rows[8][column] = replacement
    assert _result(rule_rows=rows)["all_rule_dependency_contract_checks_passed"] is False


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: next(row for row in rows if row["context_item"] == "batch_candidate_record_ids").__setitem__("required_by_rules", ""),
        lambda rows: next(row for row in rows if row["context_item"] == "batch_candidate_record_ids").__setitem__("required_by_rules", "ADMIT_001|ADMIT_002"),
        lambda rows: next(row for row in rows if row["context_item"] == "batch_candidate_record_ids").__setitem__("context_scope", "evaluation_policy"),
    ],
)
def test_context_reverse_mapping_and_scope_drift_fail_closed(mutate: object) -> None:
    contexts = gate._context_rows()
    mutate(contexts)  # type: ignore[operator]
    result = _result(context_rows=contexts)
    assert result["all_evaluation_context_contract_checks_passed"] is False
    assert result["all_rule_dependency_contract_checks_passed"] is False


def test_admit_004_and_005_inherit_all_field_blockers() -> None:
    expected = "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED|COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED"
    rows = _rule_rows()
    assert rows[3]["blocking_reasons"] == expected
    assert rows[4]["blocking_reasons"] == expected
    assert rows[4]["semantics_complete"] == "false"


def test_complete_rules_and_complete_incomplete_counts_are_graph_derived() -> None:
    rows = _rule_rows()
    assert [row["admission_rule_id"] for row in rows if row["semantics_complete"] == "true"] == ["ADMIT_014", "ADMIT_015"]
    assert sum(row["semantics_complete"] == "true" for row in rows) == 2
    assert sum(row["semantics_complete"] != "true" for row in rows) == 13


def test_rule_blocker_union_is_derived_from_unready_contexts() -> None:
    contexts = {row["context_item"]: row for row in gate._context_rows()}
    fields = {row["field_name"]: row for row in _field_rows()}
    for row in _rule_rows():
        expected = sorted({
            blocker
            for field in row["candidate_field_dependencies"].split("|")
            if field
            for blocker in fields[field]["blocking_reasons"].split("|")
            if blocker
        } | {
            blocker
            for item in row["batch_context_dependencies"].split("|")
            if item
            for blocker in contexts[item]["blocking_reasons"].split("|")
            if blocker
        } | {
            blocker
            for item in row["evaluation_context_dependencies"].split("|")
            if item
            for blocker in contexts[item]["blocking_reasons"].split("|")
            if blocker
        })
        assert row["blocking_reasons"] == "|".join(expected)
        assert (row["blocking_reasons"] == "") == (row["semantics_complete"] == "true")


def test_lifecycle_fields_preserve_step14at_value_contracts_exactly() -> None:
    source = gate._load_source()["schema"]
    rows = _field_rows()
    assert [(row["field_name"], row["requirement_phase"], row["source_value_contract"]) for row in rows] == [
        (row["admission_field_name"], row["requirement_phase"], row["value_contract"])
        for row in source
    ]
    assert "frozen_step14at_contract_only" not in {row["source_value_contract"] for row in rows}


def test_lifecycle_schema_phase_distribution_is_exact_12_1_4() -> None:
    rows = _field_rows()
    assert len(rows) == 17
    assert [row["requirement_phase"] for row in rows].count("pre_download") == 12
    assert [row["requirement_phase"] for row in rows].count("pre_final_split") == 1
    assert [row["requirement_phase"] for row in rows].count("post_download") == 4


def test_field_producer_scopes_are_phase_accurate() -> None:
    rows = {row["field_name"]: row for row in _field_rows()}
    assert rows["leakage_group_id"]["producer_scope"] == "leakage_assignment_stage"
    for name in ("download_result_status", "observed_http_status", "observed_content_length_bytes", "observed_sha256"):
        assert rows[name]["producer_scope"] == "download_execution_result"
        assert rows[name]["candidate_record_field"] == "false"


def test_field_dependent_rules_are_derived_from_candidate_field_dependencies() -> None:
    rows = {row["field_name"]: row for row in _field_rows()}
    assert rows["candidate_record_id"]["dependent_rules"] == "ADMIT_001"
    assert rows["covalent_residue_atom_name"]["dependent_rules"] == "ADMIT_004|ADMIT_005"
    for name in ("download_result_status", "observed_http_status", "observed_content_length_bytes", "observed_sha256"):
        assert rows[name]["dependent_rules"] == "ADMIT_012|ADMIT_013"
    assert rows["covalent_bond_atom_pair"]["dependent_rules"] == ""


def test_nonempty_contracts_do_not_claim_allowed_values_or_normalization() -> None:
    rows = {row["field_name"]: row for row in _field_rows()}
    for name in ("candidate_record_id", "ligand_comp_id", "covalent_residue_chain_id", "duplicate_identity_key"):
        assert rows[name]["allowed_values_defined"] == "false"
        assert rows[name]["normalization_defined"] == "false"
        assert rows[name]["exact_validation_defined"] == "false"


def test_no_field_claims_complete_semantics_without_normalization() -> None:
    rows = _field_rows()
    assert {row["normalization_defined"] for row in rows} == {"false"}
    assert {row["implementation_semantics_complete"] for row in rows} == {"false"}


def test_contexts_split_deterministic_now_from_after_contract_freeze() -> None:
    rows = {row["context_item"]: row for row in gate._context_rows()}
    pdb = rows["pdb_id_format_contract"]
    assert pdb["exact_contract_defined"] == "false"
    assert pdb["deterministic_now"] == "false"
    assert pdb["deterministic_after_contract_freeze"] == "true"
    assert pdb["implementation_ready"] == "false"


def test_context_implementation_ready_is_exact_fail_closed_formula() -> None:
    for row in gate._context_rows():
        expected = (
            row["exact_contract_defined"] == "true"
            and row["deterministic_now"] == "true"
            and row["provided_by_future_caller"] == "true"
            and row["filesystem_access_inside_evaluator"] == "false"
            and row["network_access_inside_evaluator"] == "false"
        )
        assert (row["implementation_ready"] == "true") is expected


def test_safety_rows_validate_exactly() -> None:
    assert gate._validate_safety_rows(gate._safety_rows()) is True


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: rows.clear(),
        lambda rows: rows.pop(),
        lambda rows: rows.append(copy.deepcopy(rows[-1])),
        lambda rows: rows.reverse(),
        lambda rows: rows.__setitem__(1, copy.deepcopy(rows[0])),
        lambda rows: rows[0].__setitem__("required_status", "true"),
        lambda rows: rows[0].__setitem__("observed_status", "true"),
        lambda rows: rows[0].__setitem__("safety_passed", "false"),
        lambda rows: rows[0].__setitem__("blocking_reason", "unexpected_blocker"),
    ],
)
def test_safety_shape_and_status_drift_fail_closed(mutate: object) -> None:
    rows = gate._safety_rows()
    mutate(rows)  # type: ignore[operator]
    result = _result(safety_rows=rows)
    assert result["all_safety_checks_passed"] is False
    assert result["ready_for_admission_evaluator_interface_implementation"] is False


def test_rule_dependency_drift_fails_closed() -> None:
    rows = _rule_rows()
    rows[0]["candidate_field_dependencies"] = "candidate_record_id|pdb_id"
    assert _result(rule_rows=rows)["all_rule_dependency_contract_checks_passed"] is False


def test_rule_removal_and_extra_rule_fail_closed() -> None:
    rows = _rule_rows()
    assert _result(rule_rows=rows[:-1])["all_rule_dependency_contract_checks_passed"] is False
    extra = copy.deepcopy(rows[-1])
    extra["admission_rule_id"] = "ADMIT_016"
    assert _result(rule_rows=[*rows, extra])["all_rule_dependency_contract_checks_passed"] is False


def test_field_phase_drift_and_context_removal_fail_closed() -> None:
    fields = _field_rows()
    fields[12]["requirement_phase"] = "pre_download"
    assert _result(field_rows=fields)["all_field_contract_mapping_checks_passed"] is False
    assert _result(context_rows=gate._context_rows()[:-1])["all_evaluation_context_contract_checks_passed"] is False


def test_issue_inventory_is_dependency_graph_derived(tmp_path: Path) -> None:
    gate.run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1(tmp_path)
    with (tmp_path / gate.CSV_OUTPUTS[4]).open(newline="", encoding="utf-8") as handle:
        issues = list(csv.DictReader(handle))
    by_issue = {row["issue_id"]: row for row in issues}
    assert by_issue["DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED"]["affected_rules"] == "ADMIT_012|ADMIT_013"
    assert by_issue["DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED"]["affected_rules"] == "ADMIT_012|ADMIT_013"
    assert by_issue["COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED"]["affected_rules"] == "ADMIT_004|ADMIT_005"
    assert by_issue["COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED"]["affected_rules"] == ""
    assert [row["issue_id"] for row in issues] == sorted(by_issue)


def test_manifest_separates_structure_completion_from_semantics_completion(tmp_path: Path) -> None:
    manifest = gate.run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1(tmp_path)
    assert manifest["all_rule_dependency_contract_checks_passed"] is True
    assert manifest["all_field_contract_mapping_checks_passed"] is True
    assert manifest["all_evaluation_context_contract_checks_passed"] is True
    assert manifest["all_rule_semantics_complete"] is False
    assert manifest["all_field_semantics_complete"] is False
    assert manifest["all_evaluation_contexts_ready"] is False
    assert manifest["precondition_audit_completed"] is True
    assert manifest["all_checks_passed"] is False
    assert (manifest["semantics_complete_rule_count"], manifest["semantics_incomplete_rule_count"]) == (2, 13)
    assert (manifest["semantics_complete_field_count"], manifest["semantics_incomplete_field_count"]) == (0, 17)
    assert (manifest["evaluation_context_item_count"], manifest["deterministic_now_context_count"], manifest["deterministic_after_contract_freeze_context_count"], manifest["ready_evaluation_context_count"]) == (18, 5, 18, 5)


def test_interface_readiness_is_higher_than_rule_logic_readiness(tmp_path: Path) -> None:
    manifest = gate.run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1(tmp_path)
    assert manifest["ready_for_admission_evaluator_interface_implementation"] is True
    assert manifest["ready_for_admission_evaluator_rule_logic_implementation"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STAGE


def test_masks_and_bulk_download_training_boundaries_remain_closed(tmp_path: Path) -> None:
    manifest = gate.run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1(tmp_path)
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]
    assert manifest["canonical_mask_task_count"] == 5
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True


def test_source_boundary_fails_closed_for_sixth_mask_and_rule_drift() -> None:
    source = copy.deepcopy(gate._load_source())
    source["manifest"]["canonical_mask_pairs"].append(["extra", "X"])
    assert gate._build_materialization(source)["all_source_boundary_checks_passed"] is False
    source = copy.deepcopy(gate._load_source())
    source["rules"][0]["admission_rule_name"] = "wrong"
    assert gate._build_materialization(source)["all_source_boundary_checks_passed"] is False


def test_manifest_hashes_only_non_manifest_outputs(tmp_path: Path) -> None:
    manifest = gate.run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1(tmp_path)
    assert manifest["output_sha256"] == {name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() for name in gate.CSV_OUTPUTS}
    assert manifest["output_file_count"] == 6
    assert "/home/" not in json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in json.dumps(manifest, sort_keys=True).lower()


def test_module_and_check_script_do_not_import_forbidden_runtime_dependencies() -> None:
    forbidden = {"urllib", "requests", "aiohttp", "torch", "numpy", "rdkit", "gemmi", "Bio", "gzip", "shutil"}
    for path in (
        REPO_ROOT / "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate.py",
        REPO_ROOT / "scripts/check_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        assert not names & forbidden


def test_check_script_passes_for_honest_blocker_discovery_state() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1.py"],
        cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all_source_boundary_checks_passed=true" in result.stdout
    assert "all_rule_semantics_complete=false" in result.stdout
    assert "issue_count=13" in result.stdout
    assert "canonical_mask_task_count=5" in result.stdout
    assert "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1_passed" in result.stdout


def test_check_manifest_helper_accepts_real_manifest(tmp_path: Path) -> None:
    check = _load_check_module()
    manifest, hashes = _valid_manifest_and_hashes(tmp_path)
    check._validate_manifest(manifest, hashes)  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("feature_semantics_audit_required_before_training", False),
        ("recommended_next_step", "unexpected_next_step"),
        ("candidate_records_materialized", True),
        ("download_queue_materialized", True),
        ("network_access_used_current_step", True),
        ("raw_structure_read_current_step", True),
        ("artifact_reference_paths_not_recursively_opened", False),
        ("ready_for_real_candidate_evaluation", True),
        ("ready_for_bulk_download_now", True),
        ("ready_for_training", True),
        ("ready_to_train_now", True),
        ("ready_for_admission_evaluator_rule_logic_implementation", True),
        ("precondition_audit_completed", False),
        ("all_checks_passed", True),
    ],
)
def test_check_manifest_helper_fails_closed_for_truth_drift(tmp_path: Path, key: str, value: object) -> None:
    check = _load_check_module()
    manifest, hashes = _valid_manifest_and_hashes(tmp_path)
    drifted = copy.deepcopy(manifest)
    drifted[key] = value
    with pytest.raises(AssertionError):
        check._validate_manifest(drifted, hashes)  # type: ignore[attr-defined]
