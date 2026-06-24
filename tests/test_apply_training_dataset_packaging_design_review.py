import argparse
import ast
import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_training_dataset_packaging_design_review import (  # noqa: E402
    APPROVAL_TOKEN,
    PLANNED_PACKAGING_RECORD_FIELDS,
    PLANNED_PACKAGING_DESIGN_ROOT,
    run,
)
from test_training_dataset_design_gate import _read_csv, _write_csv  # noqa: E402
from test_training_dataset_packaging_design_gate import _make_fixture as _make_gate_fixture, _run as _run_gate  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _args(paths, approval_token=APPROVAL_TOKEN):
    root = Path(PLANNED_PACKAGING_DESIGN_ROOT)
    return argparse.Namespace(
        training_dataset_packaging_design_gate_plan_csv=paths["packaging_gate_plan"],
        training_dataset_packaging_design_gate_report_csv=paths["packaging_gate_report"],
        training_dataset_design_review_qa_report_csv=paths["design_qa_report"],
        design_manifest_json=paths["design_manifest"],
        schema_report_csv=paths["schema_report"],
        split_plan_csv=paths["split_plan"],
        design_report_csv=paths["design_report"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_packaging_design_manifest_json=root / "training_dataset_packaging_design_manifest.json",
        output_file_plan_csv=root / "training_dataset_packaging_file_plan.csv",
        output_packaging_schema_report_csv=root / "training_dataset_packaging_schema_report.csv",
        output_packaging_design_report_csv=root / "training_dataset_packaging_design_report.csv",
        output_md=paths["packaging_gate_summary"].parent / "training_dataset_packaging_design_review_summary.md",
        approval_token=approval_token,
    )


def _make_fixture(tmp_path):
    paths = _make_gate_fixture(tmp_path)
    plan, report, code = _run_gate(paths)
    assert code == 0
    assert len(plan) == 3
    assert len(report) == 3
    root = Path(PLANNED_PACKAGING_DESIGN_ROOT)
    paths["packaging_design_manifest"] = root / "training_dataset_packaging_design_manifest.json"
    paths["packaging_file_plan"] = root / "training_dataset_packaging_file_plan.csv"
    paths["packaging_schema_report"] = root / "training_dataset_packaging_schema_report.csv"
    paths["packaging_design_report"] = root / "training_dataset_packaging_design_report.csv"
    paths["packaging_design_summary"] = paths["packaging_gate_summary"].parent / "training_dataset_packaging_design_review_summary.md"
    return paths


def _run(paths, approval_token=APPROVAL_TOKEN):
    return run(_args(paths, approval_token))


def test_wrong_approval_token_blocks_without_output_directory(tmp_path):
    paths = _make_fixture(tmp_path)
    report, file_plan, manifest, schema, code = _run(paths, "WRONG")
    assert code == 1
    assert report == []
    assert file_plan == []
    assert manifest == {}
    assert schema == []
    assert not Path(PLANNED_PACKAGING_DESIGN_ROOT).exists()


def test_success_writes_review_only_manifest_file_plan_schema_and_report(tmp_path):
    paths = _make_fixture(tmp_path)
    input_hashes = {
        key: _sha(paths[key])
        for key in [
            "packaging_gate_plan",
            "packaging_gate_report",
            "design_qa_report",
            "design_manifest",
            "schema_report",
            "split_plan",
            "design_report",
            "index",
            "dataset_manifest",
            "raw_manifest",
        ]
    }
    report, file_plan, manifest, schema, code = _run(paths)
    assert code == 0
    assert len(report) == 3
    assert len(_read_csv(paths["packaging_design_report"])) == 3
    assert len([row for row in file_plan if row["row_type"] == "candidate_file"]) == 15
    assert len([row for row in file_plan if row["row_type"] == "global_artifact"]) >= 8
    assert len(_read_csv(paths["packaging_file_plan"])) == 23
    assert set(PLANNED_PACKAGING_RECORD_FIELDS).issubset({row["field_name"] for row in schema})
    assert set(PLANNED_PACKAGING_RECORD_FIELDS).issubset({row["field_name"] for row in _read_csv(paths["packaging_schema_report"])})
    parsed = json.loads(paths["packaging_design_manifest"].read_text(encoding="utf-8"))
    assert parsed["packaging_design_stage"] == "training_dataset_packaging_design_review_only_not_training"
    assert parsed["row_count"] == 3
    assert manifest["target_packaging_name"] == "covalent_small_pre_reaction_training_packaging_candidate_design"
    assert all(row["training_dataset_packaging_design_status"] == "training_dataset_packaging_design_passed" for row in report)
    assert all(row["planned_packaging_file_roles_present"] == "true" for row in report)
    assert all(row["planned_packaging_record_fields_present"] == "true" for row in report)
    assert all(row["candidate_file_plan_rows_written"] == "true" for row in report)
    assert all(row["global_artifact_file_plan_rows_written"] == "true" for row in report)
    assert all(row["only_allowed_packaging_design_files_created"] == "true" for row in report)
    assert all(row["training_dataset_packaging_design_executed"] == "true" for row in report)
    assert all(row["real_training_tensor_generated"] == "false" for row in report)
    assert all(row["real_dataset_generated"] == "false" for row in report)
    assert all(row["dataloader_tensor_generated"] == "false" for row in report)
    assert all(row["torch_imported"] == "false" for row in report)
    assert all(row["checkpoint_loaded"] == "false" for row in report)
    assert all(row["model_initialized"] == "false" for row in report)
    assert all(row["training_ready"] == "false" for row in report)
    assert all(row["files_copied"] == "false" for row in report)
    assert all(row["archive_created"] == "false" for row in report)
    assert "Training Dataset Packaging Design Review Summary" in paths["packaging_design_summary"].read_text(encoding="utf-8")
    for key, before in input_hashes.items():
        assert _sha(paths[key]) == before


def test_output_directory_contains_only_four_review_files_and_no_data_files(tmp_path):
    paths = _make_fixture(tmp_path)
    _run(paths)
    files = sorted(path.name for path in Path(PLANNED_PACKAGING_DESIGN_ROOT).rglob("*") if path.is_file())
    assert files == [
        "training_dataset_packaging_design_manifest.json",
        "training_dataset_packaging_design_report.csv",
        "training_dataset_packaging_file_plan.csv",
        "training_dataset_packaging_schema_report.csv",
    ]
    forbidden = [".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"]
    for suffix in forbidden:
        assert not list(Path(PLANNED_PACKAGING_DESIGN_ROOT).rglob(f"*{suffix}"))


def test_gate_qa_hash_path_label_and_count_blockers_do_not_create_output_directory(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_gate_report"])
    rows[0]["training_dataset_packaging_design_gate_status"] = "blocked"
    _write_csv(paths["packaging_gate_report"], rows, list(rows[0]))
    _assert_blocked_without_output(paths)
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_qa_report"])
    rows[0]["training_dataset_design_review_qa_status"] = "blocked"
    _write_csv(paths["design_qa_report"], rows, list(rows[0]))
    _assert_blocked_without_output(paths)
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    Path(rows[0]["packaged_ligand_sdf_path"]).write_text("changed\n$$$$\n", encoding="utf-8")
    _assert_blocked_without_output(paths)
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["raw_manifest"])
    rows[1]["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["raw_manifest"], rows, list(rows[0]))
    _assert_blocked_without_output(paths)
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["supported_mask_levels"] = "A_warhead_only"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_without_output(paths)
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["required_auxiliary_labels"] = "warhead_type"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_without_output(paths)
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["ligand_atom_count"] = "0"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_without_output(paths)


def _assert_blocked_without_output(paths):
    report, file_plan, manifest, schema, code = _run(paths)
    assert code == 1
    assert report == []
    assert file_plan == []
    assert manifest == {}
    assert schema == []
    assert not Path(PLANNED_PACKAGING_DESIGN_ROOT).exists()


def test_script_has_no_disallowed_runtime_calls():
    source = Path(__file__).resolve().parents[1] / "scripts" / "apply_training_dataset_packaging_design_review.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert "torch" not in imported
    text = source.read_text(encoding="utf-8").lower()
    assert "load_checkpoint(" not in text
    assert "initialize_model(" not in text
    assert "dataloader(" not in text
    assert "train(" not in text
