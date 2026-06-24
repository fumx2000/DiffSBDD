import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_real_training_dataset_packaging import (  # noqa: E402
    APPROVAL_TOKEN,
    DISALLOWED_SUFFIXES,
    PACKAGE_MODE,
    PLANNED_REAL_PACKAGE_ROOT,
    run,
)
from test_real_training_dataset_packaging_gate import _make_fixture as _make_gate_fixture, _run as _run_gate  # noqa: E402
from test_training_dataset_design_gate import _read_csv, _write_csv  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _args(paths, approval_token=APPROVAL_TOKEN):
    root = Path(PLANNED_REAL_PACKAGE_ROOT)
    return argparse.Namespace(
        real_training_dataset_packaging_gate_plan_csv=paths["real_packaging_gate_plan"],
        real_training_dataset_packaging_gate_report_csv=paths["real_packaging_gate_report"],
        packaging_design_review_qa_report_csv=paths["packaging_qa_report"],
        packaging_design_manifest_json=paths["packaging_design_manifest"],
        packaging_file_plan_csv=paths["packaging_file_plan"],
        packaging_schema_report_csv=paths["packaging_schema_report"],
        packaging_design_report_csv=paths["packaging_design_report"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_real_training_dataset_manifest_json=root / "real_training_dataset_manifest.json",
        output_real_training_dataset_file_index_csv=root / "real_training_dataset_file_index.csv",
        output_real_training_dataset_sample_index_csv=root / "real_training_dataset_sample_index.csv",
        output_real_training_dataset_packaging_report_csv=root / "real_training_dataset_packaging_report.csv",
        output_md=paths["real_packaging_gate_summary"].parent / "real_training_dataset_packaging_summary.md",
        approval_token=approval_token,
    )


def _make_fixture(tmp_path):
    paths = _make_gate_fixture(tmp_path)
    plan, report, code = _run_gate(paths)
    assert code == 0
    assert len(plan) == 3
    assert len(report) == 3
    paths["real_package_root"] = Path(PLANNED_REAL_PACKAGE_ROOT)
    paths["real_manifest"] = paths["real_package_root"] / "real_training_dataset_manifest.json"
    paths["real_file_index"] = paths["real_package_root"] / "real_training_dataset_file_index.csv"
    paths["real_sample_index"] = paths["real_package_root"] / "real_training_dataset_sample_index.csv"
    paths["real_packaging_report"] = paths["real_package_root"] / "real_training_dataset_packaging_report.csv"
    paths["real_packaging_summary"] = paths["real_packaging_gate_summary"].parent / "real_training_dataset_packaging_summary.md"
    return paths


def _run(paths, approval_token=APPROVAL_TOKEN):
    return run(_args(paths, approval_token))


def _assert_blocked_without_outputs(paths, reason, output_root_should_be_absent=True):
    manifest, file_index, sample_index, report, code = _run(paths)
    assert code == 1
    assert manifest == {}
    assert file_index == []
    assert sample_index == []
    assert report == []
    if output_root_should_be_absent:
        assert not paths["real_package_root"].exists()
    assert not paths["real_manifest"].exists()
    assert not paths["real_file_index"].exists()
    assert not paths["real_sample_index"].exists()
    assert not paths["real_packaging_report"].exists()
    assert reason


def test_wrong_approval_token_blocks_without_outputs(tmp_path):
    paths = _make_fixture(tmp_path)
    manifest, file_index, sample_index, report, code = _run(paths, approval_token="WRONG")
    assert code == 1
    assert manifest == {}
    assert file_index == []
    assert sample_index == []
    assert report == []
    assert not paths["real_package_root"].exists()


def test_success_writes_reference_only_manifest_indexes_and_report(tmp_path):
    paths = _make_fixture(tmp_path)
    input_hashes = {
        key: _sha(paths[key])
        for key in [
            "real_packaging_gate_plan",
            "real_packaging_gate_report",
            "packaging_qa_report",
            "packaging_design_manifest",
            "packaging_file_plan",
            "packaging_schema_report",
            "packaging_design_report",
            "index",
            "dataset_manifest",
            "raw_manifest",
        ]
    }
    manifest, file_index, sample_index, report, code = _run(paths)
    assert code == 0
    assert manifest["row_count"] == 3
    assert manifest["file_index_row_count"] == 15
    assert manifest["sample_index_row_count"] == 3
    assert manifest["package_mode"] == PACKAGE_MODE
    assert manifest["copied_file_count"] == 0
    assert manifest["training_tensor_file_count"] == 0
    assert manifest["safety_flags"]["real_training_dataset_packaging_executed"] is True
    assert manifest["safety_flags"]["real_training_tensor_generated"] is False
    assert manifest["safety_flags"]["real_dataset_generated"] is False
    assert manifest["safety_flags"]["dataloader_tensor_generated"] is False
    assert manifest["safety_flags"]["torch_imported"] is False
    assert manifest["safety_flags"]["checkpoint_loaded"] is False
    assert manifest["safety_flags"]["model_initialized"] is False
    assert manifest["safety_flags"]["training_ready"] is False
    assert manifest["safety_flags"]["files_copied"] is False
    assert manifest["safety_flags"]["archive_created"] is False
    assert len(file_index) == 15
    assert len(sample_index) == 3
    assert len(report) == 3
    assert paths["real_manifest"].is_file()
    assert paths["real_file_index"].is_file()
    assert paths["real_sample_index"].is_file()
    assert paths["real_packaging_report"].is_file()
    assert len(_read_csv(paths["real_file_index"])) == 15
    assert len(_read_csv(paths["real_sample_index"])) == 3
    assert len(_read_csv(paths["real_packaging_report"])) == 3
    assert {path.name for path in paths["real_package_root"].iterdir()} == {
        "real_training_dataset_manifest.json",
        "real_training_dataset_file_index.csv",
        "real_training_dataset_sample_index.csv",
        "real_training_dataset_packaging_report.csv",
    }
    assert not any(path.suffix.lower() in DISALLOWED_SUFFIXES for path in paths["real_package_root"].rglob("*") if path.is_file())
    assert all(row["training_dataset_status"] == "real_training_dataset_packaging_passed_reference_only" for row in report)
    assert all(row["gate_status_passed"] == "true" for row in report)
    assert all(row["packaging_design_review_qa_status_passed"] == "true" for row in report)
    assert all(row["file_index_rows_written"] == "true" for row in report)
    assert all(row["sample_index_row_written"] == "true" for row in report)
    assert all(row["manifest_written"] == "true" for row in report)
    assert all(row["packaging_report_written"] == "true" for row in report)
    assert all(row["only_allowed_real_package_files_created"] == "true" for row in report)
    assert all(row["no_data_files_copied"] == "true" for row in report)
    assert all(row["copied_file_count"] == "0" for row in report)
    assert all(row["archive_created"] == "false" for row in report)
    assert all(row["real_training_dataset_packaging_executed"] == "true" for row in report)
    assert all(row["real_training_tensor_generated"] == "false" for row in report)
    assert all(row["real_dataset_generated"] == "false" for row in report)
    assert all(row["dataloader_tensor_generated"] == "false" for row in report)
    assert all(row["torch_imported"] == "false" for row in report)
    assert all(row["checkpoint_loaded"] == "false" for row in report)
    assert all(row["model_initialized"] == "false" for row in report)
    assert all(row["training_ready"] == "false" for row in report)
    assert all(row["files_copied"] == "false" for row in report)
    for row in file_index:
        assert Path(row["source_file_path"]).is_file()
        assert row["source_file_sha256"] == _sha(row["source_file_path"])
        assert row["package_mode"] == PACKAGE_MODE
        assert row["copied_to_package"] == "false"
        assert row["copied_file_path"] == ""
        assert row["archive_member"] == "false"
        assert row["training_tensor"] == "false"
        assert row["generated_now"] == "false"
    for row in sample_index:
        assert row["package_mode"] == PACKAGE_MODE
        assert row["copied_file_count"] == "0"
        assert row["training_tensor"] == "false"
        assert row["generated_now"] == "false"
        assert row["training_ready"] == "false"
    for key, before in input_hashes.items():
        assert _sha(paths[key]) == before
    assert "Real Training Dataset Packaging Summary" in paths["real_packaging_summary"].read_text(encoding="utf-8")


def test_gate_and_qa_blockers_do_not_write_outputs(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_packaging_gate_report"])
    rows[0]["real_training_dataset_packaging_gate_status"] = "blocked"
    _write_csv(paths["real_packaging_gate_report"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "gate_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_qa_report"])
    rows[0]["training_dataset_packaging_design_review_qa_status"] = "blocked"
    _write_csv(paths["packaging_qa_report"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "packaging_design_review_qa_status_passed")


def test_file_plan_index_manifest_and_forbidden_artifact_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_file_plan"])
    rows[0]["source_file_sha256"] = "bad"
    _write_csv(paths["packaging_file_plan"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "candidate_file_hashes_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_file_plan"])
    rows[0]["training_tensor"] = "true"
    _write_csv(paths["packaging_file_plan"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "candidate_file_reference_flags_valid")
    paths = _make_fixture(tmp_path)
    Path(_read_csv(paths["index"])[0]["packaged_ligand_sdf_path"]).write_text("changed\n$$$$\n", encoding="utf-8")
    _assert_blocked_without_outputs(paths, "packaged_hashes_match_index_and_manifest")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["raw_manifest"])
    rows[1]["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["raw_manifest"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "manifest_paths_match_index_sources")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["supported_mask_levels"] = "A_warhead_only"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "mask_levels_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["required_auxiliary_labels"] = "warhead_type"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "auxiliary_labels_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["ligand_atom_count"] = "0"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "graph_counts_positive")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked_without_outputs(paths, "forbidden_training_tensors_absent")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.tgz").write_text("bad", encoding="utf-8")
    _assert_blocked_without_outputs(paths, "forbidden_archives_absent")


def test_existing_output_root_blocks_without_rewriting(tmp_path):
    paths = _make_fixture(tmp_path)
    paths["real_package_root"].mkdir(parents=True)
    _assert_blocked_without_outputs(paths, "output_root_absent", output_root_should_be_absent=False)


def test_script_has_no_disallowed_runtime_calls():
    source = Path(__file__).resolve().parents[1] / "scripts" / "apply_real_training_dataset_packaging.py"
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
