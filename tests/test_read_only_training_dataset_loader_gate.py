import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_read_only_training_dataset_loader_gate import (  # noqa: E402
    PLANNED_READ_ONLY_LOADER_ROOT,
    run,
)
from test_real_training_dataset_packaging_qa import _make_fixture as _make_qa_fixture, _run as _run_qa  # noqa: E402
from test_training_dataset_design_gate import _read_csv, _write_csv  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _args(paths):
    return argparse.Namespace(
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
        output_gate_plan_csv=paths["real_package_root"] / "read_only_training_dataset_loader_gate_plan.csv",
        output_report_csv=paths["real_package_root"] / "read_only_training_dataset_loader_gate_report.csv",
        output_md=paths["real_packaging_qa_summary"].parent / "read_only_training_dataset_loader_gate_summary.md",
    )


def _make_fixture(tmp_path):
    paths = _make_qa_fixture(tmp_path)
    rows, code = _run_qa(paths)
    assert code == 0
    assert len(rows) == 3
    paths["loader_gate_plan"] = paths["real_package_root"] / "read_only_training_dataset_loader_gate_plan.csv"
    paths["loader_gate_report"] = paths["real_package_root"] / "read_only_training_dataset_loader_gate_report.csv"
    paths["loader_gate_summary"] = paths["real_packaging_qa_summary"].parent / "read_only_training_dataset_loader_gate_summary.md"
    return paths


def _run(paths):
    return run(_args(paths))


def _assert_blocked(paths, reason, planned_root_should_be_absent=True):
    plan_rows, report_rows, code = _run(paths)
    assert code == 1
    assert len(report_rows) == 3
    assert len(_read_csv(paths["loader_gate_report"])) == 3
    assert any(row["read_only_training_dataset_loader_gate_status"] == "blocked" for row in report_rows)
    assert any(reason in row["blocking_reasons"] for row in report_rows)
    assert len(plan_rows) < 3
    if planned_root_should_be_absent:
        assert not Path(PLANNED_READ_ONLY_LOADER_ROOT).exists()
    else:
        assert not any(Path(PLANNED_READ_ONLY_LOADER_ROOT).rglob("*"))


def test_success_outputs_three_passed_gate_rows_without_modifying_inputs(tmp_path):
    paths = _make_fixture(tmp_path)
    protected = [
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
    plan_rows, report_rows, code = _run(paths)
    assert code == 0
    assert len(plan_rows) == 3
    assert len(report_rows) == 3
    assert len(_read_csv(paths["loader_gate_plan"])) == 3
    assert len(_read_csv(paths["loader_gate_report"])) == 3
    assert paths["loader_gate_summary"].is_file()
    assert all(row["read_only_training_dataset_loader_gate_status"] == "read_only_training_dataset_loader_gate_passed" for row in report_rows)
    assert all(row["explicit_approval_required_before_read_only_loader_dry_run"] == "true" for row in report_rows)
    assert all(row["ready_for_read_only_loader_dry_run_after_approval"] == "true" for row in report_rows)
    assert all(row["read_only_loader_dry_run_executed"] == "false" for row in report_rows)
    assert all(row["dataloader_tensor_generated"] == "false" for row in report_rows)
    assert all(row["real_training_tensor_generated"] == "false" for row in report_rows)
    assert all(row["real_dataset_generated"] == "false" for row in report_rows)
    assert all(row["torch_imported"] == "false" for row in report_rows)
    assert all(row["checkpoint_loaded"] == "false" for row in report_rows)
    assert all(row["model_initialized"] == "false" for row in report_rows)
    assert all(row["training_ready"] == "false" for row in report_rows)
    assert all(row["files_copied"] == "false" for row in report_rows)
    assert all(row["archive_created"] == "false" for row in report_rows)
    assert not Path(PLANNED_READ_ONLY_LOADER_ROOT).exists()
    assert {path.name for path in paths["real_package_root"].iterdir()} == {
        "real_training_dataset_manifest.json",
        "real_training_dataset_file_index.csv",
        "real_training_dataset_sample_index.csv",
        "real_training_dataset_packaging_report.csv",
        "real_training_dataset_packaging_qa_report.csv",
        "read_only_training_dataset_loader_gate_plan.csv",
        "read_only_training_dataset_loader_gate_report.csv",
    }
    for key, before in input_hashes.items():
        assert _sha(paths[key]) == before
    assert "Read-only Training Dataset Loader Gate Summary" in paths["loader_gate_summary"].read_text(encoding="utf-8")


def test_packaging_qa_manifest_file_index_sample_index_and_report_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_packaging_qa_report"])
    rows[0]["real_training_dataset_packaging_qa_status"] = "blocked"
    _write_csv(paths["real_packaging_qa_report"], rows, list(rows[0]))
    _assert_blocked(paths, "real_training_dataset_packaging_qa_status_passed")
    paths = _make_fixture(tmp_path)
    paths["real_manifest"].write_text("{bad", encoding="utf-8")
    _assert_blocked(paths, "real_training_dataset_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["real_manifest"].read_text(encoding="utf-8"))
    manifest["row_count"] = 2
    paths["real_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "real_training_dataset_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["real_manifest"].read_text(encoding="utf-8"))
    manifest["package_mode"] = "copy"
    paths["real_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "real_training_dataset_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["real_manifest"].read_text(encoding="utf-8"))
    manifest["safety_flags"]["torch_imported"] = True
    paths["real_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "real_training_dataset_manifest_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_file_index"])
    _write_csv(paths["real_file_index"], rows[:14], list(rows[0]))
    _assert_blocked(paths, "real_training_dataset_file_index_candidate_rows_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_file_index"])
    rows[0]["source_file_sha256"] = "bad"
    _write_csv(paths["real_file_index"], rows, list(rows[0]))
    _assert_blocked(paths, "real_training_dataset_file_index_hashes_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_file_index"])
    rows[0]["training_tensor"] = "true"
    _write_csv(paths["real_file_index"], rows, list(rows[0]))
    _assert_blocked(paths, "real_training_dataset_file_index_reference_only_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_sample_index"])
    rows[0]["training_ready"] = "true"
    _write_csv(paths["real_sample_index"], rows, list(rows[0]))
    _assert_blocked(paths, "real_training_dataset_sample_index_reference_only_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_packaging_report"])
    rows[0]["training_dataset_status"] = "blocked"
    _write_csv(paths["real_packaging_report"], rows, list(rows[0]))
    _assert_blocked(paths, "real_training_dataset_packaging_report_status_passed")


def test_upstream_index_package_planned_root_and_forbidden_artifact_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_packaging_gate_report"])
    rows[0]["real_training_dataset_packaging_gate_status"] = "blocked"
    _write_csv(paths["real_packaging_gate_report"], rows, list(rows[0]))
    _assert_blocked(paths, "upstream_gate_and_design_qa_still_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_qa_report"])
    rows[0]["training_dataset_packaging_design_review_qa_status"] = "blocked"
    _write_csv(paths["packaging_qa_report"], rows, list(rows[0]))
    _assert_blocked(paths, "upstream_gate_and_design_qa_still_passed")
    paths = _make_fixture(tmp_path)
    Path(_read_csv(paths["index"])[0]["packaged_ligand_sdf_path"]).write_text("changed\n$$$$\n", encoding="utf-8")
    _assert_blocked(paths, "packaged_hashes_match_index_and_manifest")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["raw_manifest"])
    rows[1]["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["raw_manifest"], rows, list(rows[0]))
    _assert_blocked(paths, "manifest_paths_match_index_sources")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["supported_mask_levels"] = "A_warhead_only"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked(paths, "mask_levels_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["required_auxiliary_labels"] = "warhead_type"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked(paths, "auxiliary_labels_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["ligand_atom_count"] = "0"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked(paths, "graph_counts_positive")
    paths = _make_fixture(tmp_path)
    (paths["real_package_root"] / "bad.sdf").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "real_package_files_valid")
    paths = _make_fixture(tmp_path)
    (paths["real_package_root"] / "metadata_copy.json").write_text("{}", encoding="utf-8")
    _assert_blocked(paths, "real_package_files_valid")
    paths = _make_fixture(tmp_path)
    Path(PLANNED_READ_ONLY_LOADER_ROOT).mkdir(parents=True)
    _assert_blocked(paths, "planned_read_only_loader_dry_run_root_absent_before_gate", planned_root_should_be_absent=False)
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "forbidden_training_tensors_absent")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.tgz").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "forbidden_archives_absent")


def test_script_has_no_disallowed_runtime_calls():
    source = Path(__file__).resolve().parents[1] / "scripts" / "build_read_only_training_dataset_loader_gate.py"
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
    assert "loader_dry_run(" not in text
