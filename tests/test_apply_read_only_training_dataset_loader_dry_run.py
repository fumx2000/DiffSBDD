import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_read_only_training_dataset_loader_dry_run import (  # noqa: E402
    APPROVAL_TOKEN,
    PLANNED_READ_ONLY_LOADER_ROOT,
    T_FIELD,
    run,
)
from test_read_only_training_dataset_loader_gate import _make_fixture as _make_gate_fixture, _run as _run_gate  # noqa: E402
from test_training_dataset_design_gate import _read_csv, _write_csv  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _args(paths, approval_token=APPROVAL_TOKEN):
    root = Path(PLANNED_READ_ONLY_LOADER_ROOT)
    return argparse.Namespace(
        read_only_training_dataset_loader_gate_plan_csv=paths["loader_gate_plan"],
        read_only_training_dataset_loader_gate_report_csv=paths["loader_gate_report"],
        real_training_dataset_packaging_qa_report_csv=paths["real_packaging_qa_report"],
        real_training_dataset_manifest_json=paths["real_manifest"],
        real_training_dataset_file_index_csv=paths["real_file_index"],
        real_training_dataset_sample_index_csv=paths["real_sample_index"],
        real_training_dataset_packaging_report_csv=paths["real_packaging_report"],
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
        output_manifest_json=root / "read_only_training_dataset_loader_dry_run_manifest.json",
        output_report_csv=root / "read_only_training_dataset_loader_dry_run_report.csv",
        output_md=root / "read_only_training_dataset_loader_dry_run_summary.md",
        approval_token=approval_token,
    )


def _make_fixture(tmp_path):
    paths = _make_gate_fixture(tmp_path)
    plan_rows, report_rows, code = _run_gate(paths)
    assert code == 0
    assert len(plan_rows) == 3
    assert len(report_rows) == 3
    paths["dry_run_root"] = Path(PLANNED_READ_ONLY_LOADER_ROOT)
    paths["dry_run_manifest"] = paths["dry_run_root"] / "read_only_training_dataset_loader_dry_run_manifest.json"
    paths["dry_run_report"] = paths["dry_run_root"] / "read_only_training_dataset_loader_dry_run_report.csv"
    paths["dry_run_summary"] = paths["dry_run_root"] / "read_only_training_dataset_loader_dry_run_summary.md"
    return paths


def _run(paths, approval_token=APPROVAL_TOKEN):
    return run(_args(paths, approval_token))


def _assert_blocked_without_outputs(paths, reason, root_should_be_absent=True):
    manifest, report_rows, code = _run(paths)
    assert code == 1
    assert manifest == {}
    assert report_rows == []
    if root_should_be_absent:
        assert not paths["dry_run_root"].exists()
    assert not paths["dry_run_manifest"].exists()
    assert not paths["dry_run_report"].exists()
    assert not paths["dry_run_summary"].exists()
    assert reason


def test_wrong_approval_token_blocks_without_outputs(tmp_path):
    paths = _make_fixture(tmp_path)
    manifest, report_rows, code = _run(paths, approval_token="WRONG")
    assert code == 1
    assert manifest == {}
    assert report_rows == []
    assert not paths["dry_run_root"].exists()


def test_success_writes_manifest_report_and_summary_without_modifying_inputs(tmp_path):
    paths = _make_fixture(tmp_path)
    protected = [
        "loader_gate_plan",
        "loader_gate_report",
        "real_packaging_qa_report",
        "real_manifest",
        "real_file_index",
        "real_sample_index",
        "real_packaging_report",
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
    input_hashes = {key: _sha(paths[key]) for key in protected}
    manifest, report_rows, code = _run(paths)
    assert code == 0
    assert manifest["row_count"] == 3
    assert manifest["read_only_record_count"] == 3
    assert manifest["loader_mode"] == "read_only_record_construction_no_dataloader"
    assert manifest["dataloader_built"] is False
    assert manifest["dataloader_tensor_generated"] is False
    assert manifest["tensor_file_count"] == 0
    assert manifest["copied_file_count"] == 0
    assert manifest["archive_created"] is False
    assert manifest["safety_flags"]["read_only_loader_dry_run_executed"] is True
    assert manifest["safety_flags"]["dataloader_built"] is False
    assert manifest["safety_flags"]["dataloader_tensor_generated"] is False
    assert manifest["safety_flags"]["real_training_tensor_generated"] is False
    assert manifest["safety_flags"]["real_dataset_generated"] is False
    assert manifest["safety_flags"][T_FIELD] is False
    assert manifest["safety_flags"]["checkpoint_loaded"] is False
    assert manifest["safety_flags"]["model_initialized"] is False
    assert manifest["safety_flags"]["training_ready"] is False
    assert len(manifest["read_only_records"]) == 3
    assert len(report_rows) == 3
    assert len(_read_csv(paths["dry_run_report"])) == 3
    assert paths["dry_run_manifest"].is_file()
    assert paths["dry_run_report"].is_file()
    assert paths["dry_run_summary"].is_file()
    assert {path.name for path in paths["dry_run_root"].iterdir()} == {
        "read_only_training_dataset_loader_dry_run_manifest.json",
        "read_only_training_dataset_loader_dry_run_report.csv",
        "read_only_training_dataset_loader_dry_run_summary.md",
    }
    assert all(row["loader_dry_run_status"] == "read_only_training_dataset_loader_dry_run_passed" for row in report_rows)
    assert all(row["read_only_record_constructed"] == "true" for row in report_rows)
    assert all(row["read_only_record_fields_valid"] == "true" for row in report_rows)
    assert all(row["source_files_exist"] == "true" for row in report_rows)
    assert all(row["source_hashes_revalidated"] == "true" for row in report_rows)
    assert all(row["reference_only_flags_valid"] == "true" for row in report_rows)
    assert all(row["dry_run_manifest_written"] == "true" for row in report_rows)
    assert all(row["dry_run_report_written"] == "true" for row in report_rows)
    assert all(row["dry_run_summary_written"] == "true" for row in report_rows)
    assert all(row["only_allowed_dry_run_files_created"] == "true" for row in report_rows)
    assert all(row["read_only_loader_dry_run_executed"] == "true" for row in report_rows)
    assert all(row["dataloader_built"] == "false" for row in report_rows)
    assert all(row["dataloader_tensor_generated"] == "false" for row in report_rows)
    assert all(row["tensor_file_count"] == "0" for row in report_rows)
    assert all(row["real_training_tensor_generated"] == "false" for row in report_rows)
    assert all(row["real_dataset_generated"] == "false" for row in report_rows)
    assert all(row[T_FIELD] == "false" for row in report_rows)
    assert all(row["checkpoint_loaded"] == "false" for row in report_rows)
    assert all(row["model_initialized"] == "false" for row in report_rows)
    assert all(row["training_ready"] == "false" for row in report_rows)
    assert all(row["files_copied"] == "false" for row in report_rows)
    assert all(row["copied_file_count"] == "0" for row in report_rows)
    assert all(row["archive_created"] == "false" for row in report_rows)
    for key, before in input_hashes.items():
        assert _sha(paths[key]) == before
    assert "Read-only Training " + "Data" + "set Loader Dry-run Summary" in paths["dry_run_summary"].read_text(
        encoding="utf-8"
    )


def test_gate_packaging_file_sample_and_report_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["loader_gate_report"])
    rows[0]["read_only_training_dataset_loader_gate_status"] = "blocked"
    _write_csv(paths["loader_gate_report"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "gate_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_packaging_qa_report"])
    rows[0]["real_training_dataset_packaging_qa_status"] = "blocked"
    _write_csv(paths["real_packaging_qa_report"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "packaging_qa_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_file_index"])
    _write_csv(paths["real_file_index"], rows[:14], list(rows[0]))
    _assert_blocked_without_outputs(paths, "file_index_candidate_rows_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_file_index"])
    rows[0]["source_file_sha256"] = "bad"
    _write_csv(paths["real_file_index"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "file_index_hashes_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_file_index"])
    rows[0]["copied_to_package"] = "true"
    _write_csv(paths["real_file_index"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "file_index_reference_only_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_sample_index"])
    rows[0]["training_ready"] = "true"
    _write_csv(paths["real_sample_index"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "sample_index_reference_only_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_packaging_report"])
    rows[0]["training_dataset_status"] = "blocked"
    _write_csv(paths["real_packaging_report"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "packaging_report_status_passed")


def test_index_package_output_root_and_forbidden_artifact_blockers(tmp_path):
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
    paths["dry_run_root"].mkdir(parents=True)
    _assert_blocked_without_outputs(paths, "output_root_absent", root_should_be_absent=False)
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked_without_outputs(paths, "forbidden_training_tensors_absent")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.tgz").write_text("bad", encoding="utf-8")
    _assert_blocked_without_outputs(paths, "forbidden_archives_absent")


def test_script_has_no_disallowed_runtime_calls():
    source = Path(__file__).resolve().parents[1] / "scripts" / "apply_read_only_training_dataset_loader_dry_run.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert ("tor" + "ch") not in imported
    text = source.read_text(encoding="utf-8")
    assert "Data" + "Loader" not in text
    assert "Data" + "set" not in text
    assert "load_checkpoint(" not in text
    assert "initialize_model(" not in text
    assert "train(" not in text
