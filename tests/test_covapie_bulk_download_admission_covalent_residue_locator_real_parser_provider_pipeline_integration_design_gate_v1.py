"""Tests for the metadata-only Step14AU-E0-P6-A design gate."""

from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate
    as gate,
)


MODULE_PATH = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate.py"
CHECK_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("p6a_checker", CHECK_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _hashes(root: Path) -> dict[str, str]:
    return {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in gate.OUTPUT_FILES
    }


def _materialize(tmp_path: Path) -> Path:
    root = tmp_path / "outputs"
    result = gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1(root)
    assert result["all_checks_passed"] is True
    return root


def _source_data() -> dict[Path, list[dict[str, str]]]:
    return {path: gate._read_csv(path) for path in (
        gate.HISTORICAL_EXECUTION_PATH,
        gate.SAMPLE_INDEX_PATH,
        gate.EXPANSION_EXECUTION_PATH,
    )}


def _patch_source_data(monkeypatch: pytest.MonkeyPatch, data: dict[Path, list[dict[str, str]]]) -> None:
    monkeypatch.setattr(gate, "_read_csv", lambda path: copy.deepcopy(data[path]))


def test_import_has_no_materialization_side_effect(tmp_path: Path) -> None:
    code = (
        "import pathlib; "
        "import covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate; "
        "print(sorted(p.name for p in pathlib.Path('.').iterdir()))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path,
        env={"PYTHONPATH": str(REPO_ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
        check=True, text=True, stdout=subprocess.PIPE,
    )
    assert result.stdout.strip() == "[]"


def test_exact_output_set_and_double_materialization(tmp_path: Path) -> None:
    root = _materialize(tmp_path)
    first = _hashes(root)
    gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1(root)
    assert _hashes(root) == first
    assert {path.name for path in root.iterdir()} == set(gate.OUTPUT_FILES)


def test_outputs_have_no_nondeterministic_or_absolute_content(tmp_path: Path) -> None:
    root = _materialize(tmp_path)
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.iterdir())
    assert "timestamp" not in text.lower()
    assert str(REPO_ROOT) not in text
    assert "manifest_sha256" not in text


def test_source_boundary_is_exact_ordered_and_valid() -> None:
    rows = gate._source_rows()
    assert len(rows) == 12
    assert tuple(row["source_relative_path"] for row in rows) == tuple(
        path.as_posix() for path in gate.SOURCE_PATHS
    )
    assert all(row["tracked"] and row["regular_file"] and not row["symlink"] for row in rows)
    assert gate.validate_source_rows(rows)


@pytest.mark.parametrize("mutation", ["missing", "extra", "reorder", "expected_hash", "observed_hash", "untracked", "nonregular", "symlink"])
def test_source_boundary_rejects_drift(mutation: str) -> None:
    rows = copy.deepcopy(gate._source_rows())
    if mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        rows.append(copy.deepcopy(rows[-1]))
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "expected_hash":
        rows[0]["sha256_expected"] = "0" * 64
    elif mutation == "observed_hash":
        rows[0]["sha256_observed"] = "0" * 64
    elif mutation == "untracked":
        rows[0]["tracked"] = False
    elif mutation == "nonregular":
        rows[0]["regular_file"] = False
    else:
        rows[0]["symlink"] = True
    assert not gate.validate_source_rows(rows)


def test_p5b_predecessor_contract_is_frozen() -> None:
    checks = gate._p5b_checks()
    assert checks and all(checks.values())
    manifest = gate._p5b_manifest()
    assert manifest["synthetic_case_count"] == 16
    assert manifest["synthetic_sidecar_column_count"] == 33
    assert (manifest["exported_pass_case_count"], manifest["exported_blocking_case_count"], manifest["rejected_case_count"]) == (5, 5, 6)
    assert manifest["real_parser_pipeline_integration_implemented"] is False
    assert manifest["real_provider_pipeline_integration_implemented"] is False
    assert (manifest["existing_real_sample_count"], manifest["real_insertion_unknown_sample_count"], manifest["real_insertion_absence_proven_sample_count"]) == (11, 11, 0)


def test_actual_p5b_header_binds_future_sidecar_schema() -> None:
    actual = gate._read_csv_header(gate.P5B_CASE_SIDECAR_PATH)
    assert len(actual) == 33
    assert actual == gate.P5B_CASE_COLUMNS
    assert gate.FUTURE_REAL_SIDECAR_COLUMNS == (
        *gate.FUTURE_SIDECAR_PREFIX_COLUMNS, *actual
    )
    assert len(gate.FUTURE_REAL_SIDECAR_COLUMNS) == 41


@pytest.mark.parametrize("mutation", ["missing", "reorder", "duplicate", "extra"])
def test_p5b_header_drift_fails_predecessor_contract_and_readiness(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    header = list(gate.P5B_CASE_COLUMNS)
    if mutation == "missing":
        header.pop()
    elif mutation == "reorder":
        header[0], header[1] = header[1], header[0]
    elif mutation == "duplicate":
        header[1] = header[0]
    else:
        header.append("extra")
    monkeypatch.setattr(gate, "_read_csv_header", lambda path: tuple(header))
    state = gate.build_design_state()
    manifest = gate._manifest_payload(
        state, {name: "0" * 64 for name in gate.CSV_OUTPUTS}
    )
    assert state["sections"]["p5b_predecessor"] is False
    assert state["sections"]["integration_contract"] is False
    assert state["validation_failures"] == [
        "P5B_PREDECESSOR_VALIDATION_FAILED",
        "INTEGRATION_CONTRACT_VALIDATION_FAILED",
    ]
    assert manifest["all_checks_passed"] is False
    assert manifest["real_pipeline_integration_design_frozen"] is False
    assert manifest["ready_for_real_raw_source_precondition_gate"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert len(manifest["current_domain_blocking_reasons"]) == 10
    assert len(manifest["integration_followup_issue_ids"]) == 3


def test_historical_join_is_one_to_one_and_uses_expected_sources() -> None:
    rows = gate.build_real_sample_binding_rows()[:3]
    execution = {row["sample_preparation_input_id"]: row for row in gate._read_csv(gate.HISTORICAL_EXECUTION_PATH)}
    index = {row["sample_preparation_input_id"]: row for row in gate._read_csv(gate.SAMPLE_INDEX_PATH)}
    assert len(rows) == len(execution) == len(index) == 3
    for row in rows:
        source = execution[row["sample_preparation_input_id"]]
        indexed = index[row["sample_preparation_input_id"]]
        assert row["raw_target_relative_path"] == source["raw_file_path"]
        assert row["conn_id"] == indexed["conn_id"]
        assert row["covalent_residue_name"] == indexed["covalent_residue_name"]
        assert row["covalent_event_table_relative_path"] == indexed["covalent_event_table_path"]
        assert row["ligand_residue_atom_pair_table_relative_path"] == indexed["ligand_residue_atom_pair_table_path"]


def test_historical_order_is_controlled_by_sample_index(monkeypatch: pytest.MonkeyPatch) -> None:
    data = _source_data()
    data[gate.HISTORICAL_EXECUTION_PATH].reverse()
    _patch_source_data(monkeypatch, data)
    rows = gate.build_real_sample_binding_rows()
    assert [(row["pdb_id"], row["ligand_comp_id"]) for row in rows[:3]] == [
        ("6BV6", "JUG"), ("6BV8", "JUG"), ("6BV5", "JUG")
    ]
    assert gate.validate_binding_rows(rows)


@pytest.mark.parametrize("mutation", ["duplicate_index", "missing_index", "unmatched_index", "duplicate_execution"])
def test_historical_join_fails_closed(monkeypatch: pytest.MonkeyPatch, mutation: str) -> None:
    data = _source_data()
    if mutation == "duplicate_index":
        data[gate.SAMPLE_INDEX_PATH][1]["sample_preparation_input_id"] = data[gate.SAMPLE_INDEX_PATH][0]["sample_preparation_input_id"]
    elif mutation == "missing_index":
        data[gate.SAMPLE_INDEX_PATH].pop()
    elif mutation == "unmatched_index":
        data[gate.SAMPLE_INDEX_PATH][0]["sample_preparation_input_id"] = "UNMATCHED"
    else:
        data[gate.HISTORICAL_EXECUTION_PATH][1]["sample_preparation_input_id"] = data[gate.HISTORICAL_EXECUTION_PATH][0]["sample_preparation_input_id"]
    _patch_source_data(monkeypatch, data)
    assert not gate.validate_binding_rows(gate.build_real_sample_binding_rows())


@pytest.mark.parametrize(
    ("target", "field", "value"),
    [
        (gate.HISTORICAL_EXECUTION_PATH, "expected_het_id", "MISMATCH"),
        (gate.SAMPLE_INDEX_PATH, "expected_het_id", "MISMATCH"),
        (gate.SAMPLE_INDEX_PATH, "ligand_comp_id", "MISMATCH"),
        (gate.HISTORICAL_EXECUTION_PATH, "sample_execution_id", "MISMATCH"),
        (gate.HISTORICAL_EXECUTION_PATH, "pdb_id", "MISMATCH"),
        (gate.HISTORICAL_EXECUTION_PATH, "sample_artifact_root", "data/derived/covalent_small/mismatch"),
        (gate.HISTORICAL_EXECUTION_PATH, "sample_preparation_status", "MISMATCH"),
        (gate.SAMPLE_INDEX_PATH, "sample_index_status", "MISMATCH"),
    ],
)
def test_historical_identity_and_status_mismatch_fails_closed(
    monkeypatch: pytest.MonkeyPatch, target: Path, field: str, value: str
) -> None:
    data = _source_data()
    data[target][0][field] = value
    _patch_source_data(monkeypatch, data)
    rows = gate.build_real_sample_binding_rows()
    row = rows[0]
    assert all(type(item) is str and item for item in (
        row["sample_preparation_input_id"], row["sample_execution_id"],
        row["pdb_id"], row["ligand_comp_id"], row["conn_id"],
    ))
    assert row["metadata_join_status"] == "metadata_join_failed"
    assert row["binding_status"] == "metadata_join_failed"
    assert row["blocking_reason"] == "REAL_SAMPLE_METADATA_JOIN_FAILED"
    assert row["real_export_execution_allowed_current_step"] is False
    assert not gate.validate_binding_rows(rows)


def test_binding_common_requires_exact_boolean_join_validity() -> None:
    values = {
        key: value for key, value in gate.build_real_sample_binding_rows()[0].items()
        if key in gate.BINDING_COLUMNS[2:15]
    }
    assert gate._binding_common("", "historical", values, True)["metadata_join_status"] == "one_to_one_metadata_join_complete"
    for invalid in (1, "true", None):
        assert gate._binding_common("", "historical", values, invalid)["metadata_join_status"] == "metadata_join_failed"


def test_expansion_binding_maps_ranked_metadata() -> None:
    rows = gate.build_real_sample_binding_rows()[3:]
    source = sorted(gate._read_csv(gate.EXPANSION_EXECUTION_PATH), key=lambda row: int(row["shortlist_rank"]))
    assert len(rows) == 8
    for row, execution in zip(rows, source):
        assert row["ligand_comp_id"] == execution["expected_het_id"]
        assert row["conn_id"] == execution["selected_struct_conn_id"]
        assert row["selected_residue_chain_id"] == execution["selected_cys_chain_id"]
        assert row["selected_residue_index"] == execution["selected_cys_seq_id"]
        assert row["selected_residue_atom_name"] == "SG"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sample_preparation_status", "mismatch"),
        ("embedded_qa_passed", "False"),
        ("embedded_qa_passed", "true"),
        ("covalent_event_count", "0"),
        ("ligand_residue_atom_pair_count", "0"),
        ("covalent_bond_atom_pair", "SG--MISMATCH"),
        ("selected_ligand_atom_name", ""),
        ("expected_het_id", ""),
    ],
)
def test_expansion_readiness_mismatch_preserves_row_and_fails_closed(
    monkeypatch: pytest.MonkeyPatch, field: str, value: str,
) -> None:
    data = _source_data()
    data[gate.EXPANSION_EXECUTION_PATH][0][field] = value
    _patch_source_data(monkeypatch, data)
    rows = gate.build_real_sample_binding_rows()
    assert len(rows) == 11
    row = rows[3]
    assert row["binding_row_id"] == "REAL_LOCATOR_BINDING_000004"
    assert row["metadata_join_status"] == "metadata_join_failed"
    assert row["binding_status"] == "metadata_join_failed"
    assert row["blocking_reason"] == "REAL_SAMPLE_METADATA_JOIN_FAILED"
    assert row["real_export_execution_allowed_current_step"] is False
    state = gate.build_design_state()
    manifest = gate._manifest_payload(
        state, {name: "0" * 64 for name in gate.CSV_OUTPUTS}
    )
    assert state["sections"]["binding_matrix"] is False
    assert state["sections"]["integration_contract"] is False
    assert manifest["all_checks_passed"] is False
    assert manifest["ready_for_real_raw_source_precondition_gate"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP


@pytest.mark.parametrize("mutation", ["duplicate_rank", "missing_rank", "duplicate_id", "bad_rank"])
def test_expansion_binding_fails_closed(monkeypatch: pytest.MonkeyPatch, mutation: str) -> None:
    data = _source_data()
    rows = data[gate.EXPANSION_EXECUTION_PATH]
    if mutation == "duplicate_rank":
        rows[1]["shortlist_rank"] = rows[0]["shortlist_rank"]
    elif mutation == "missing_rank":
        rows.pop()
    elif mutation == "duplicate_id":
        rows[1]["sample_preparation_input_id"] = rows[0]["sample_preparation_input_id"]
    else:
        rows[0]["shortlist_rank"] = "bad"
    _patch_source_data(monkeypatch, data)
    assert not gate.validate_binding_rows(gate.build_real_sample_binding_rows())


def test_binding_matrix_exact_shape_order_and_identities() -> None:
    rows = gate.build_real_sample_binding_rows()
    assert len(rows) == 11 and len(gate.BINDING_COLUMNS) == 26
    assert gate.validate_binding_rows(rows)
    assert [row["binding_row_id"] for row in rows] == [f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)]
    assert len({row["sample_preparation_input_id"] for row in rows}) == 11
    assert len({(row["pdb_id"], row["ligand_comp_id"]) for row in rows}) == 11


class _StringSubclass(str):
    pass


@pytest.mark.parametrize(
    "value",
    [None, _StringSubclass("data/x"), "", " data/x", "data/x ", "data\\x",
     "/data/x", ".", "?", "data/./x", "data/../x", "data//x",
     "data/\x00x", "https://example.test/x", "file:data/x", "C:/x"],
)
def test_generic_relative_path_helper_rejects_unsafe_values(value: object) -> None:
    assert not gate._safe_relative_path(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("data/raw/covalent_sources/a.cif", True),
        ("data/raw/covalent_sources/a.mmcif", True),
        ("docs/not_raw.cif", False),
        ("data/raw/covalent_sources/a.pdb", False),
        ("data/raw/covalent_sources/a.CIF", False),
        ("C:/raw.cif", False),
    ],
)
def test_raw_target_helper_enforces_root_and_suffix(value: str, expected: bool) -> None:
    assert gate._safe_raw_target_relative_path(value) is expected


def test_artifact_reference_helper_enforces_root_parent_and_filenames() -> None:
    root = "data/derived/covalent_small/sample"
    assert gate._safe_artifact_references(
        root, f"{root}/covalent_event_table.csv",
        f"{root}/ligand_residue_atom_pair_table.csv",
    )
    assert not gate._safe_artifact_references(
        "docs/sample", "docs/sample/covalent_event_table.csv",
        "docs/sample/ligand_residue_atom_pair_table.csv",
    )
    assert not gate._safe_artifact_references(
        root, "data/derived/covalent_small/other/covalent_event_table.csv",
        f"{root}/ligand_residue_atom_pair_table.csv",
    )
    assert not gate._safe_artifact_references(
        root, f"{root}/covalent_event_table.csv", f"{root}/wrong.csv",
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("data/derived/covalent_small", False),
        ("data/derived/covalent_small/sample", True),
        ("data/derived/other/sample", False),
        ("data/derived/covalent_small/../sample", False),
        ("/data/derived/covalent_small/sample", False),
    ],
)
def test_sample_artifact_root_requires_concrete_child(
    value: str, expected: bool,
) -> None:
    assert gate._safe_sample_artifact_root(value) is expected


@pytest.mark.parametrize("mutation", ["missing", "reorder", "row_drift", "count_correct_set_wrong", "absolute_raw", "traversal_raw", "execution_overclaim", "status_drift"])
def test_binding_matrix_rejects_drift(mutation: str) -> None:
    rows = copy.deepcopy(gate.build_real_sample_binding_rows())
    if mutation == "missing":
        rows.pop()
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "row_drift":
        rows[0]["conn_id"] = "DRIFT"
    elif mutation == "count_correct_set_wrong":
        rows[-1] = copy.deepcopy(rows[-2])
        rows[-1]["binding_row_id"] = "REAL_LOCATOR_BINDING_000011"
    elif mutation == "absolute_raw":
        rows[0]["raw_target_relative_path"] = "/tmp/raw.cif"
    elif mutation == "traversal_raw":
        rows[0]["raw_target_relative_path"] = "data/../raw.cif"
    elif mutation == "execution_overclaim":
        rows[0]["real_export_execution_allowed_current_step"] = True
    else:
        rows[0]["binding_status"] = "ready"
    assert not gate.validate_binding_rows(rows)


def test_future_executor_input_contract_is_exact() -> None:
    assert gate.FUTURE_EXECUTOR_INPUT_FIELDS == (
        "binding_row_id", "source_pipeline", "sample_preparation_input_id",
        "sample_execution_id", "pdb_id", "ligand_comp_id", "conn_id",
        "covalent_residue_name", "selected_residue_chain_id",
        "selected_residue_index", "selected_residue_atom_name",
        "raw_target_relative_path", "expected_raw_sha256",
    )


def test_future_sidecar_is_exact_41_column_additive_schema() -> None:
    assert len(gate.FUTURE_REAL_SIDECAR_COLUMNS) == 41
    assert gate.FUTURE_REAL_SIDECAR_COLUMNS[:8] == gate.FUTURE_SIDECAR_PREFIX_COLUMNS
    assert gate.FUTURE_REAL_SIDECAR_COLUMNS[8:] == gate.P5B_CASE_COLUMNS
    assert all("timestamp" not in field and "raw_content" not in field for field in gate.FUTURE_REAL_SIDECAR_COLUMNS)


def test_contract_is_exact_48_full_rows() -> None:
    state = gate.build_design_state()
    assert len(state["contract_rows"]) == 48
    assert gate.validate_contract_rows(state["contract_rows"])
    assert all(row["contract_passed"] and not row["blocking_reason"] for row in state["contract_rows"])


@pytest.mark.parametrize("mutation", ["empty", "reorder", "coordinated_drift", "passed_false"])
def test_contract_rejects_drift(mutation: str) -> None:
    rows = copy.deepcopy(gate.build_design_state()["contract_rows"])
    if mutation == "empty":
        rows = []
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "coordinated_drift":
        rows[0]["expected_value"] = rows[0]["observed_value"] = "drift"
    else:
        rows[0]["contract_passed"] = False
    assert not gate.validate_contract_rows(rows)


def test_architecture_contract_freezes_additive_external_executor() -> None:
    rows = gate.build_design_state()["contract_rows"]
    by_requirement = {row["requirement"]: row["observed_value"] for row in rows}
    assert by_requirement["integration architecture"] == gate.INTEGRATION_ARCHITECTURE
    assert by_requirement["historical parser unchanged"] == "true"
    assert by_requirement["expansion parser unchanged"] == "true"
    assert by_requirement["admission evaluator does not open raw"] == "true"
    assert by_requirement["distance inference forbidden"] == "true"
    assert by_requirement["sidecar remains independent"] == "true"
    assert by_requirement["later sidecar QA required"] == "true"
    assert by_requirement["later admission merge required"] == "true"


def test_issue_inventory_is_exact_three_open_blockers() -> None:
    rows = gate._issue_rows()
    assert gate.validate_issue_rows(rows)
    assert [row["issue_id"] for row in rows] == list(gate.FOLLOWUP_ISSUES)
    assert [row["issue_count"] for row in rows] == [11, 11, 1]
    assert all(row["severity"] == "blocking" and row["status"] == "open" for row in rows)


@pytest.mark.parametrize("mutation", ["no_issues", "missing", "reorder", "count", "closed"])
def test_issue_inventory_rejects_drift(mutation: str) -> None:
    rows = copy.deepcopy(gate._issue_rows())
    if mutation == "no_issues":
        rows = [{**rows[0], "issue_id": "NO_ISSUES"}]
    elif mutation == "missing":
        rows.pop()
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "count":
        rows[0]["issue_count"] = 0
    else:
        rows[0]["status"] = "closed"
    assert not gate.validate_issue_rows(rows)


def test_safety_audit_is_exact_twenty_false_observations() -> None:
    rows = gate._safety_rows()
    assert gate.validate_safety_rows(rows)
    assert len(rows) == 20
    assert all(row["required_status"] is False and row["observed_status"] is False and row["safety_passed"] is True for row in rows)


@pytest.mark.parametrize("mutation", ["missing", "extra", "reorder", "overclaim", "passed_false"])
def test_safety_rejects_drift(mutation: str) -> None:
    rows = copy.deepcopy(gate._safety_rows())
    if mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        rows.append(copy.deepcopy(rows[-1]))
    elif mutation == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "overclaim":
        rows[0]["observed_status"] = True
    else:
        rows[0]["safety_passed"] = False
    assert not gate.validate_safety_rows(rows)


def test_manifest_truth_and_readiness_boundaries(tmp_path: Path) -> None:
    root = _materialize(tmp_path)
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest["real_pipeline_integration_design_frozen"] is True
    assert manifest["real_executor_implemented"] is False
    assert manifest["real_raw_sources_read_current_step"] is False
    assert manifest["real_raw_sources_hashed_current_step"] is False
    assert manifest["real_provider_rows_materialized_current_step"] is False
    assert (manifest["real_sample_binding_count"], manifest["historical_binding_count"], manifest["expansion_binding_count"]) == (11, 3, 8)
    assert manifest["raw_sha256_precondition_frozen_count"] == 0
    assert manifest["real_export_execution_allowed_count"] == 0
    assert manifest["ready_for_real_raw_source_precondition_gate"] is True
    for key in ("ready_for_real_provider_export_execution", "admit_004_rule_logic_ready", "ready_for_e1_residue_identity_semantics_design", "ready_for_real_candidate_evaluation", "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now"):
        assert manifest[key] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert len(manifest["current_domain_blocking_reasons"]) == 10
    assert manifest["integration_followup_issue_ids"] == list(gate.FOLLOWUP_ISSUES)


def test_failed_state_manifest_inventory_counts_are_dynamic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _source_data()
    data[gate.SAMPLE_INDEX_PATH].pop()
    _patch_source_data(monkeypatch, data)
    state = gate.build_design_state()
    manifest = gate._manifest_payload(
        state, {name: "0" * 64 for name in gate.CSV_OUTPUTS}
    )
    assert state["all_checks_passed"] is False
    assert manifest["real_sample_binding_count"] == 10
    assert manifest["historical_binding_count"] == 2
    assert manifest["expansion_binding_count"] == 8
    assert manifest["unique_sample_preparation_input_count"] == 10
    assert manifest["unique_pdb_ligand_identity_count"] < 11
    assert manifest["metadata_join_complete_count"] == 8
    assert manifest["raw_relative_path_persisted_count"] == 8
    assert manifest["real_export_execution_allowed_count"] == 0
    assert manifest["ready_for_real_raw_source_precondition_gate"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP


def test_manifest_unique_counts_are_canonical_on_success() -> None:
    state = gate.build_design_state()
    manifest = gate._manifest_payload(
        state, {name: "0" * 64 for name in gate.CSV_OUTPUTS}
    )
    assert manifest["unique_sample_preparation_input_count"] == 11
    assert manifest["unique_pdb_ligand_identity_count"] == 11


def test_manifest_unique_sample_count_excludes_empty_identity() -> None:
    state = gate.build_design_state()
    state["binding_rows"] = copy.deepcopy(state["binding_rows"])
    state["binding_rows"][0]["sample_preparation_input_id"] = ""
    manifest = gate._manifest_payload(
        state, {name: "0" * 64 for name in gate.CSV_OUTPUTS}
    )
    assert manifest["unique_sample_preparation_input_count"] == 10


@pytest.mark.parametrize("field", ["pdb_id", "ligand_comp_id"])
def test_manifest_unique_identity_count_excludes_empty_component(field: str) -> None:
    state = gate.build_design_state()
    state["binding_rows"] = copy.deepcopy(state["binding_rows"])
    state["binding_rows"][0][field] = ""
    manifest = gate._manifest_payload(
        state, {name: "0" * 64 for name in gate.CSV_OUTPUTS}
    )
    assert manifest["unique_pdb_ligand_identity_count"] == 10


def test_manifest_unique_identity_count_deduplicates_valid_identity() -> None:
    state = gate.build_design_state()
    state["binding_rows"] = copy.deepcopy(state["binding_rows"])
    state["binding_rows"][1]["pdb_id"] = state["binding_rows"][0]["pdb_id"]
    state["binding_rows"][1]["ligand_comp_id"] = state["binding_rows"][0]["ligand_comp_id"]
    manifest = gate._manifest_payload(
        state, {name: "0" * 64 for name in gate.CSV_OUTPUTS}
    )
    assert manifest["unique_pdb_ligand_identity_count"] == 10


@pytest.mark.parametrize("section", gate.SECTION_NAMES)
def test_each_section_failure_is_independent_and_fail_closed(section: str) -> None:
    state = gate.build_design_state([section])
    manifest = gate._manifest_payload(state, {name: "0" * 64 for name in gate.CSV_OUTPUTS})
    assert state["all_checks_passed"] is False
    assert manifest["real_pipeline_integration_design_frozen"] is False
    assert manifest["ready_for_real_raw_source_precondition_gate"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert manifest["validation_failures"] == [f"{section.upper()}_VALIDATION_FAILED"]
    assert len(manifest["current_domain_blocking_reasons"]) == 10
    assert manifest["integration_followup_issue_ids"] == list(gate.FOLLOWUP_ISSUES)


@pytest.mark.parametrize("binding_result", [[], "identity_invalid"])
def test_binding_helper_failure_propagates_to_contract_and_readiness(
    monkeypatch: pytest.MonkeyPatch, binding_result: object,
) -> None:
    if binding_result == "identity_invalid":
        rows = copy.deepcopy(gate.build_real_sample_binding_rows())
        rows[0]["metadata_join_status"] = "metadata_join_failed"
        rows[0]["binding_status"] = "metadata_join_failed"
        rows[0]["blocking_reason"] = "REAL_SAMPLE_METADATA_JOIN_FAILED"
    else:
        rows = []
    monkeypatch.setattr(gate, "build_real_sample_binding_rows", lambda: rows)
    state = gate.build_design_state()
    manifest = gate._manifest_payload(
        state, {name: "0" * 64 for name in gate.CSV_OUTPUTS}
    )
    assert state["sections"]["binding_matrix"] is False
    assert state["sections"]["integration_contract"] is False
    assert state["validation_failures"] == [
        "BINDING_MATRIX_VALIDATION_FAILED", "INTEGRATION_CONTRACT_VALIDATION_FAILED"
    ]
    assert manifest["all_checks_passed"] is False
    assert manifest["real_pipeline_integration_design_frozen"] is False
    assert manifest["ready_for_real_raw_source_precondition_gate"] is False
    assert manifest["recommended_next_step"] == gate.BLOCKED_NEXT_STEP
    assert len(manifest["current_domain_blocking_reasons"]) == 10
    assert len(manifest["integration_followup_issue_ids"]) == 3


def test_unknown_section_failure_is_rejected() -> None:
    with pytest.raises(ValueError):
        gate.build_design_state(["unknown"])


def test_checker_validates_materialized_outputs(tmp_path: Path) -> None:
    root = _materialize(tmp_path)
    checker = _load_checker()
    manifest = checker.validate_materialized_outputs(root, _hashes(root))
    assert manifest["all_checks_passed"] is True


def test_checker_rejects_runtime_p5b_header_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _materialize(tmp_path)
    monkeypatch.setattr(gate, "_read_csv_header", lambda path: gate.P5B_CASE_COLUMNS[:-1])
    with pytest.raises(AssertionError):
        _load_checker().validate_materialized_outputs(root)


def test_checker_rejects_runtime_expansion_readiness_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _materialize(tmp_path)
    data = _source_data()
    data[gate.EXPANSION_EXECUTION_PATH][0]["embedded_qa_passed"] = "False"
    _patch_source_data(monkeypatch, data)
    with pytest.raises(AssertionError):
        _load_checker().validate_materialized_outputs(root)


@pytest.mark.parametrize("mutation", ["binding_drift", "binding_reorder", "execution_overclaim", "manifest_raw_sha", "manifest_executor", "manifest_unknown", "manifest_absence", "manifest_admit", "manifest_e1", "manifest_candidate", "manifest_download", "manifest_training"])
def test_checker_rejects_persisted_overclaim_or_drift(tmp_path: Path, mutation: str) -> None:
    root = _materialize(tmp_path)
    if mutation.startswith("binding") or mutation == "execution_overclaim":
        path = root / gate.BINDING_FILENAME
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if mutation == "binding_drift":
            rows[0]["conn_id"] = "DRIFT"
        elif mutation == "binding_reorder":
            rows[0], rows[1] = rows[1], rows[0]
        else:
            rows[0]["real_export_execution_allowed_current_step"] = "true"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=gate.BINDING_COLUMNS, lineterminator="\n")
            writer.writeheader(); writer.writerows(rows)
    else:
        path = root / gate.MANIFEST_FILENAME
        manifest = json.loads(path.read_text(encoding="utf-8"))
        key_values = {
            "manifest_raw_sha": ("raw_sha256_precondition_frozen_count", 1),
            "manifest_executor": ("real_executor_implemented", True),
            "manifest_unknown": ("real_insertion_unknown_sample_count", 10),
            "manifest_absence": ("real_insertion_absence_proven_sample_count", 1),
            "manifest_admit": ("admit_004_rule_logic_ready", True),
            "manifest_e1": ("ready_for_e1_residue_identity_semantics_design", True),
            "manifest_candidate": ("ready_for_real_candidate_evaluation", True),
            "manifest_download": ("ready_for_bulk_download_now", True),
            "manifest_training": ("ready_for_training", True),
        }
        key, value = key_values[mutation]
        manifest[key] = value
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        _load_checker().validate_materialized_outputs(root)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("raw_target_relative_path", "/tmp/raw.cif"),
        ("raw_target_relative_path", "data/../raw.cif"),
        ("raw_target_relative_path", "docs/not_raw.cif"),
        ("raw_target_relative_path", "C:/raw.cif"),
        (
            "covalent_event_table_relative_path",
            "data/derived/covalent_small/other/covalent_event_table.csv",
        ),
        (
            "ligand_residue_atom_pair_table_relative_path",
            "data/derived/covalent_small/sample/wrong.csv",
        ),
    ],
)
def test_checker_rejects_persisted_path_contract_drift(
    tmp_path: Path, field: str, value: str,
) -> None:
    root = _materialize(tmp_path)
    path = root / gate.BINDING_FILENAME
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows[0][field] = value
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=gate.BINDING_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(AssertionError):
        _load_checker().validate_materialized_outputs(root)


@pytest.mark.parametrize("mutation", ["extra", "missing", "symlink"])
def test_checker_rejects_output_set_drift(tmp_path: Path, mutation: str) -> None:
    root = _materialize(tmp_path)
    if mutation == "extra":
        (root / "extra.csv").write_text("x\n", encoding="utf-8")
    elif mutation == "missing":
        (root / gate.ISSUE_FILENAME).unlink()
    else:
        target = root / gate.ISSUE_FILENAME
        target.unlink()
        target.symlink_to(root / gate.SAFETY_FILENAME)
    with pytest.raises(AssertionError):
        _load_checker().validate_materialized_outputs(root)


def test_checker_rejects_first_hash_drift(tmp_path: Path) -> None:
    root = _materialize(tmp_path)
    hashes = _hashes(root)
    (root / gate.ISSUE_FILENAME).write_text("drift\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        _load_checker().validate_materialized_outputs(root, hashes)


def test_checker_rejects_source_hash_constant_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _materialize(tmp_path)
    monkeypatch.setitem(gate.SOURCE_SHA256, gate.SOURCE_PATHS[0].as_posix(), "0" * 64)
    with pytest.raises(AssertionError):
        _load_checker().validate_materialized_outputs(root)


def test_output_root_symlink_and_non_directory_are_rejected(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(RuntimeError):
        gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1(link)
    file_root = tmp_path / "file"
    file_root.write_text("x", encoding="utf-8")
    with pytest.raises(RuntimeError):
        gate.run_covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1(file_root)


def test_canonical_masks_are_exactly_five_with_b3() -> None:
    assert gate.CANONICAL_MASK_PAIRS == (
        ("warhead_only", "A"), ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"), ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    )


def test_static_import_boundary_and_forbidden_calls() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports.isdisjoint({"requests", "urllib", "aiohttp", "torch", "numpy", "rdkit", "Bio", "gemmi", "pandas", "importlib", "inspect"})
    assert "model.forward" not in source
    assert "trainer.fit" not in source
    assert "importlib.reload" not in source
    assert "getsource" not in source
    assert "data/raw/covalent_sources" not in source
    assert "rglob(" not in source and "glob(" not in source and "os.walk" not in source


def test_production_does_not_import_historical_or_expansion_parser_modules() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "from covalent_ext.covapie_sample_preparation_execution_smoke" not in source
    assert "from covalent_ext.covapie_independent_group_expansion_batch_sample_preparation_execution_smoke" not in source


def test_materialization_preserves_all_source_hashes(tmp_path: Path) -> None:
    before = {path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate.SOURCE_PATHS}
    _materialize(tmp_path)
    after = {path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate.SOURCE_PATHS}
    assert before == after == {path: gate.SOURCE_SHA256[path.as_posix()] for path in gate.SOURCE_PATHS}
