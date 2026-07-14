from __future__ import annotations

import csv
import copy
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from covalent_ext import covapie_final_dataset_qa_gate_v1 as gate


def _hashes(root: Path) -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.iterdir() if path.is_file()}


def test_import_has_no_output_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    importlib.reload(gate)
    assert not (tmp_path / gate.DEFAULT_OUTPUT_ROOT).exists()


def test_materializes_exact_outputs_deterministically(tmp_path: Path) -> None:
    manifest = gate.run_final_dataset_qa_gate_v1(tmp_path)
    first = _hashes(tmp_path)
    rerun = gate.run_final_dataset_qa_gate_v1(tmp_path)
    assert manifest["all_checks_passed"] is True
    assert rerun["all_checks_passed"] is True
    assert first == _hashes(tmp_path)
    assert sorted(first) == sorted([*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME])


def test_stage_constants_and_source_contract_are_exact() -> None:
    assert gate.STAGE == "covapie_final_dataset_qa_gate_v1"
    assert gate.STEP_LABEL == "Step14AS-B"
    assert gate.PROJECT_NAME == "CovaPIE"
    assert gate.PREVIOUS_STAGE == "covapie_final_dataset_materialization_smoke_v0"
    assert len(gate._source_input_paths()) == 12
    assert gate._source_input_paths()[-1].name == "covapie_final_dataset_materialization_smoke_manifest.json"
    assert gate.AQ_MANIFEST.name == "covapie_unified_leakage_split_materialization_smoke_manifest.json"


def test_source_inputs_are_tracked_regular_files_and_hashes_are_fixed() -> None:
    source = gate._load_source()
    assert len(source["ar_manifest"]) == 54
    assert gate._sha256(gate._repo_path(gate._source_input_paths()[-1])) == gate.SOURCE_STEP14AR_MANIFEST_SHA256
    assert gate._sha256(gate._repo_path(gate.AQ_MANIFEST)) == gate.SOURCE_STEP14AQ_MANIFEST_SHA256
    assert all(gate._repo_path(path).is_file() and gate._tracked_by_git(path) for path in gate._all_read_paths())


def test_schema_lineage_blocks_duplicate_final_dataset_row_id() -> None:
    source = copy.deepcopy(gate._load_source())
    source["index_csv"][1]["sample_index_row_id"] = source["index_csv"][0]["sample_index_row_id"]
    rows = gate._build_schema_lineage(source)
    assert any(row["schema_lineage_qa_passed"] == "false" for row in rows if row["qa_record_type"] == "lineage_row")


def test_schema_lineage_blocks_typed_json_value_drift() -> None:
    source = copy.deepcopy(gate._load_source())
    source["index_json"][0]["protein_atom_count"] = "7468"
    rows = gate._build_schema_lineage(source)
    assert rows[33]["csv_json_match"] == "false"


def test_split_and_group_contract_is_exact(tmp_path: Path) -> None:
    manifest = gate.run_covapie_final_dataset_qa_gate_v1(tmp_path)
    assert manifest["split_sample_counts"] == {"train": 8, "validation": 2, "test": 1, "total": 11}
    assert manifest["split_group_counts"] == {"train": 2, "validation": 2, "test": 1, "total": 5}
    assert manifest["split_artifact_reference_counts"] == {"train": 48, "validation": 12, "test": 6, "total": 66}


def test_masks_are_exactly_five_and_include_b3(tmp_path: Path) -> None:
    gate.run_covapie_final_dataset_qa_gate_v1(tmp_path)
    with (tmp_path / gate.CSV_OUTPUTS[4]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [(row["mask_task_name"], row["mask_task_alias"]) for row in rows] == list(gate.CANONICAL_MASK_PAIRS)
    assert ("scaffold_only", "B3") in gate.CANONICAL_MASK_PAIRS
    assert {row["mask_contract_qa_passed"] for row in rows} == {"true"}


def test_safety_and_training_boundary_is_closed(tmp_path: Path) -> None:
    manifest = gate.run_covapie_final_dataset_qa_gate_v1(tmp_path)
    with (tmp_path / gate.CSV_OUTPUTS[5]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["safety_training_boundary_qa_passed"] for row in rows} == {"true"}
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["training_blockers"] == [
        "feature_semantics_audit_required_before_training",
        "bulk_download_admission_design_not_completed",
    ]


def test_manifest_has_no_runtime_metadata_or_absolute_paths(tmp_path: Path) -> None:
    gate.run_covapie_final_dataset_qa_gate_v1(tmp_path)
    text = (tmp_path / gate.MANIFEST_FILENAME).read_text(encoding="utf-8")
    manifest = json.loads(text)
    assert "timestamp" not in text.lower()
    assert "/home/" not in text
    assert manifest["source_input_count"] == 12
    assert len(manifest["source_input_sha256"]) == 12
    assert len(manifest["output_sha256"]) == 7


def test_source_manifest_inventory_has_exact_path_set() -> None:
    source = gate._load_source()
    expected = {str(gate.AR_ROOT / name) for name in gate.INPUT_FILENAMES[:-1]}
    observed = {row["relative_path"] for row in source["ar_manifest"]["non_manifest_outputs"]}
    assert observed == expected


def test_manifest_reports_canonical_counts_and_boundaries(tmp_path: Path) -> None:
    manifest = gate.run_final_dataset_qa_gate_v1(tmp_path)
    assert manifest["canonical_schema_field_count"] == 33
    assert manifest["final_dataset_row_count"] == 11
    assert manifest["split_sample_counts"] == {"train": 8, "validation": 2, "test": 1, "total": 11}
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True


def test_schema_lineage_has_33_fields_and_11_rows(tmp_path: Path) -> None:
    gate.run_final_dataset_qa_gate_v1(tmp_path)
    with (tmp_path / gate.CSV_OUTPUTS[2]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len([row for row in rows if row["qa_record_type"] == "schema_field"]) == 33
    assert len([row for row in rows if row["qa_record_type"] == "lineage_row"]) == 11
    assert {row["schema_lineage_qa_passed"] for row in rows} == {"true"}


def test_typed_csv_json_normalization_rejects_wrong_types() -> None:
    assert gate._normalize_csv_value("protein_atom_count", "12") == 12
    assert gate._normalize_json_value("ready_for_training_current_step", False) is False
    with pytest.raises(ValueError):
        gate._normalize_json_value("protein_atom_count", "12")
    with pytest.raises(ValueError):
        gate._normalize_csv_value("ready_for_training_current_step", "false")


def test_artifact_inventory_is_12_tracked_inputs(tmp_path: Path) -> None:
    gate.run_final_dataset_qa_gate_v1(tmp_path)
    with (tmp_path / gate.CSV_OUTPUTS[1]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 12
    assert {row["artifact_inventory_qa_passed"] for row in rows} == {"true"}
    assert {row["tracked_by_git"] for row in rows} == {"true"}


def test_issue_inventory_is_normal_sentinel(tmp_path: Path) -> None:
    gate.run_final_dataset_qa_gate_v1(tmp_path)
    with (tmp_path / gate.CSV_OUTPUTS[6]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [{
        "issue_id": "NO_COVAPIE_FINAL_DATASET_QA_V1_ISSUES", "issue_type": "no_issues",
        "severity": "none", "status": "passed", "issue_count": "0", "blocking_reasons": "",
    }]


def test_module_has_no_forbidden_runtime_imports() -> None:
    source = Path(gate.__file__).read_text(encoding="utf-8")
    for forbidden in ("import torch", "import numpy", "import rdkit", "import gemmi", "Bio.PDB"):
        assert forbidden not in source


def test_check_script_is_deterministic() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_covapie_final_dataset_qa_gate_v1.py"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    assert "qa_v1_output_hashes_byte_identical=true" in result.stdout
    assert "covapie_final_dataset_qa_gate_v1_passed" in result.stdout
    manifest = json.loads((Path("data/derived/covalent_small/covapie_final_dataset_qa_gate_v1") / gate.MANIFEST_FILENAME).read_text())
    assert manifest["output_file_count"] == 8


def test_mask_audit_does_not_claim_masks_are_index_fields() -> None:
    rows = gate._build_mask_audit(gate._load_source())
    assert {row["mask_semantics_source"] for row in rows} == {"step14ar_manifest"}
    assert {row["final_index_mask_field_present"] for row in rows} == {"false"}
    assert {row["final_index_mask_field_required"] for row in rows} == {"false"}
    assert {row["final_index_sample_set_complete"] for row in rows} == {"true"}


def test_sixth_mask_blocks_mask_contract() -> None:
    source = copy.deepcopy(gate._load_source())
    source["ar_manifest"]["canonical_mask_pairs"].append(["extra_mask", "X"])
    assert {row["mask_contract_qa_passed"] for row in gate._build_mask_audit(source)} == {"false"}


def test_mask_order_drift_blocks_mask_contract() -> None:
    source = copy.deepcopy(gate._load_source())
    pairs = source["ar_manifest"]["canonical_mask_pairs"]
    pairs[0], pairs[1] = pairs[1], pairs[0]
    assert {row["mask_contract_qa_passed"] for row in gate._build_mask_audit(source)} == {"false"}


def test_index_membership_sample_set_drift_blocks_mask_contract() -> None:
    source = copy.deepcopy(gate._load_source())
    source["membership"] = source["membership"][:-1]
    rows = gate._build_mask_audit(source)
    assert {row["final_index_sample_set_complete"] for row in rows} == {"false"}
    assert {row["mask_contract_qa_passed"] for row in rows} == {"false"}


def test_cross_split_group_blocks_split_audit() -> None:
    source = copy.deepcopy(gate._load_source())
    source["membership"][1]["assigned_split"] = "validation"
    rows = gate._build_split_audit(source)
    assert any(row["group_exclusive"] == "false" for row in rows)
    assert any(row["split_leakage_qa_passed"] == "false" for row in rows)


def test_recomputed_group_count_drift_blocks_split_audit() -> None:
    source = copy.deepcopy(gate._load_source())
    source["membership"][1]["final_leakage_group_id"] = "COVAPIE_LEAKAGE_GROUP_NEW"
    rows = gate._build_split_audit(source)
    train = next(row for row in rows if row["split_name"] == "train")
    assert train["recomputed_membership_group_count"] == 3
    assert train["split_leakage_qa_passed"] == "false"


def test_step14aq_sample_count_drift_blocks_split_audit() -> None:
    source = copy.deepcopy(gate._load_source())
    source["aq_manifest"]["train_sample_count"] = 7
    train = next(row for row in gate._build_split_audit(source) if row["split_name"] == "train")
    assert train["sample_count_match"] == "false"
    assert train["split_leakage_qa_passed"] == "false"


def test_step14aq_group_count_drift_blocks_split_audit() -> None:
    source = copy.deepcopy(gate._load_source())
    source["aq_manifest"]["train_group_count"] = 3
    train = next(row for row in gate._build_split_audit(source) if row["split_name"] == "train")
    assert train["group_count_match"] == "false"
    assert train["split_leakage_qa_passed"] == "false"


def test_step14aq_artifact_reference_counts_are_explicitly_unavailable() -> None:
    rows = gate._build_split_audit(gate._load_source())
    assert {row["source_step14aq_artifact_reference_count_status"] for row in rows} == {
        "not_available_in_source_manifest"
    }
    assert all("source_step14aq_artifact_reference_count" not in row for row in rows)


def test_artifact_inventory_counts_are_independently_recomputed() -> None:
    rows = {row["split_name"]: row for row in gate._build_split_audit(gate._load_source())}
    assert {name: int(row["recomputed_inventory_artifact_reference_count"]) for name, row in rows.items()} == {
        "train": 48, "validation": 12, "test": 6, "total": 66,
    }
    assert {row["artifact_reference_count_evidence_source"] for row in rows.values()} == {
        "step14ar_artifact_inventory_joined_to_membership"
    }


def test_artifact_inventory_unmatched_sample_blocks_split_audit() -> None:
    source = copy.deepcopy(gate._load_source())
    source["artifact_inventory"][0]["sample_index_row_id"] = "UNKNOWN_SAMPLE"
    rows = gate._build_split_audit(source)
    assert {row["artifact_inventory_join_complete"] for row in rows} == {"false"}
    assert any(row["split_leakage_qa_passed"] == "false" for row in rows)


def test_artifact_inventory_assigned_split_mismatch_blocks_split_audit() -> None:
    source = copy.deepcopy(gate._load_source())
    source["artifact_inventory"][0]["assigned_split"] = "test"
    rows = gate._build_split_audit(source)
    assert {row["artifact_inventory_join_complete"] for row in rows} == {"false"}


def test_artifact_inventory_group_mismatch_blocks_split_audit() -> None:
    source = copy.deepcopy(gate._load_source())
    source["artifact_inventory"][0]["final_leakage_group_id"] = "COVAPIE_LEAKAGE_GROUP_UNKNOWN"
    rows = gate._build_split_audit(source)
    assert {row["artifact_inventory_join_complete"] for row in rows} == {"false"}


def test_split_manifest_counts_come_from_recomputed_evidence(tmp_path: Path) -> None:
    manifest = gate.run_covapie_final_dataset_qa_gate_v1(tmp_path)
    assert manifest["artifact_reference_counts_recomputed_from_step14ar_inventory"] is True
    assert manifest["artifact_reference_inventory_join_complete"] is True
    assert manifest["source_step14aq_artifact_reference_counts_available"] is False
    assert manifest["source_step14aq_artifact_reference_count_crosscheck_status"] == "not_available_in_source_manifest"


def test_read_boundary_is_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    csv_paths: list[Path] = []
    json_paths: list[Path] = []
    original_csv = gate._read_csv
    original_json = gate._read_json

    def record_csv(path: Path) -> list[dict[str, str]]:
        csv_paths.append(path)
        return original_csv(path)

    def record_json(path: Path):
        json_paths.append(path)
        return original_json(path)

    monkeypatch.setattr(gate, "_read_csv", record_csv)
    monkeypatch.setattr(gate, "_read_json", record_json)
    gate._load_source()
    assert set(csv_paths) == {path for path in gate._source_input_paths() if path.suffix == ".csv"}
    assert set(json_paths) == {
        gate.AR_ROOT / "final_dataset_index.json",
        gate.AR_ROOT / gate.INPUT_FILENAMES[-1],
        gate.AQ_MANIFEST,
    }


def test_missing_aq_sample_count_clears_manifest_evidence_availability() -> None:
    source = copy.deepcopy(gate._load_source())
    del source["aq_manifest"]["train_sample_count"]
    rows = gate._build_split_audit(source)
    evidence = gate._summarize_split_evidence(rows)
    assert {row["source_step14aq_sample_count_status"] for row in rows} == {"missing_in_source_manifest"}
    assert {row["sample_count_match"] for row in rows} == {"false"}
    assert evidence["aq_sample_counts_available"] is False
    assert evidence["aq_sample_counts_match"] is False


def test_missing_aq_group_count_clears_manifest_evidence_availability() -> None:
    source = copy.deepcopy(gate._load_source())
    del source["aq_manifest"]["train_group_count"]
    rows = gate._build_split_audit(source)
    evidence = gate._summarize_split_evidence(rows)
    assert {row["source_step14aq_group_count_status"] for row in rows} == {"missing_in_source_manifest"}
    assert {row["group_count_match"] for row in rows} == {"false"}
    assert evidence["aq_group_counts_available"] is False
    assert evidence["aq_group_counts_match"] is False


def test_normal_aq_evidence_is_available_and_matches() -> None:
    evidence = gate._summarize_split_evidence(gate._build_split_audit(gate._load_source()))
    assert evidence["aq_sample_counts_available"] is True
    assert evidence["aq_sample_counts_match"] is True
    assert evidence["aq_group_counts_available"] is True
    assert evidence["aq_group_counts_match"] is True


def test_later_json_row_extra_field_blocks_schema_lineage() -> None:
    source = copy.deepcopy(gate._load_source())
    source["index_json"][1]["unexpected_field"] = "blocked"
    rows = gate._build_schema_lineage(source)
    assert any(row["schema_lineage_qa_passed"] == "false" for row in rows)
    assert rows[34]["csv_json_match"] == "false"


def test_later_json_row_order_drift_blocks_schema_lineage() -> None:
    source = copy.deepcopy(gate._load_source())
    source["index_json"][1] = {
        key: source["index_json"][1][key] for key in reversed(tuple(gate.FINAL_INDEX_FIELDS))
    }
    rows = gate._build_schema_lineage(source)
    assert any(row["schema_lineage_qa_passed"] == "false" for row in rows)
    assert rows[34]["csv_json_match"] == "false"


def test_protected_source_diff_checks_staged_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    class Result:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    calls: list[list[str]] = []

    def fake_run(args: list[str], **_kwargs: object) -> Result:
        calls.append(args)
        return Result(0 if len(calls) == 1 else 1)

    monkeypatch.setattr(gate.subprocess, "run", fake_run)
    assert gate._protected_source_diff_empty() is False
    assert calls[0][:4] == ["git", "diff", "--quiet", "--"]
    assert calls[1][:5] == ["git", "diff", "--cached", "--quiet", "--"]


def test_protected_source_diff_requires_both_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    class Result:
        returncode = 0

    def fake_run(_args: list[str], **_kwargs: object) -> Result:
        return Result()

    monkeypatch.setattr(gate.subprocess, "run", fake_run)
    assert gate._protected_source_diff_empty() is True
