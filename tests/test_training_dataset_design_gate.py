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

from apply_dataset_snapshot_review import SNAPSHOT_ROOT, TARGETS  # noqa: E402
from build_training_dataset_design_gate import PLANNED_TRAINING_DATASET_DESIGN_ROOT, run  # noqa: E402
from test_dataset_snapshot_review_qa import _make_fixture as _make_snapshot_fixture, _read_csv, _run_qa, _write_csv  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _args(paths):
    return argparse.Namespace(
        snapshot_review_qa_report_csv=paths["qa_report"],
        snapshot_manifest_json=paths["snapshot_manifest"],
        snapshot_file_list_csv=paths["snapshot_file_list"],
        snapshot_review_report_csv=paths["snapshot_report"],
        snapshot_review_gate_plan_csv=paths["snapshot_gate_plan"],
        snapshot_review_gate_report_csv=paths["snapshot_gate_report"],
        loader_dry_run_qa_report_csv=paths["loader_qa"],
        loader_dry_run_report_csv=paths["loader_report"],
        actual_dataset_index_qa_report_csv=paths["index_qa"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_gate_plan_csv=Path(SNAPSHOT_ROOT) / "training_dataset_design_gate_plan.csv",
        output_report_csv=Path(SNAPSHOT_ROOT) / "training_dataset_design_gate_report.csv",
        output_md=paths["qa_summary"].parent / "training_dataset_design_gate_summary.md",
    )


def _make_fixture(tmp_path):
    paths = _make_snapshot_fixture(tmp_path)
    rows, code = _run_qa(paths)
    assert code == 0
    assert len(rows) == 3
    paths["training_gate_plan"] = Path(SNAPSHOT_ROOT) / "training_dataset_design_gate_plan.csv"
    paths["training_gate_report"] = Path(SNAPSHOT_ROOT) / "training_dataset_design_gate_report.csv"
    paths["training_gate_summary"] = paths["qa_summary"].parent / "training_dataset_design_gate_summary.md"
    return paths


def _run(paths):
    return run(_args(paths))


def _assert_blocked(paths, reason):
    plan, report, code = _run(paths)
    assert code == 1
    assert len(report) == 3
    assert any(row["training_dataset_design_gate_status"] == "blocked" for row in report)
    assert any(reason in row["blocking_reasons"] for row in report)
    assert len(plan) < 3


def test_success_outputs_three_passed_rows(tmp_path):
    paths = _make_fixture(tmp_path)
    input_hashes = {
        key: _sha(paths[key])
        for key in [
            "qa_report",
            "snapshot_manifest",
            "snapshot_file_list",
            "snapshot_report",
            "index",
            "dataset_manifest",
            "raw_manifest",
        ]
    }
    plan, report, code = _run(paths)
    assert code == 0
    assert len(plan) == 3
    assert len(report) == 3
    assert len(_read_csv(paths["training_gate_plan"])) == 3
    assert len(_read_csv(paths["training_gate_report"])) == 3
    assert all(row["training_dataset_design_gate_status"] == "training_dataset_design_gate_passed" for row in report)
    assert all(row["explicit_approval_required_before_training_dataset_design"] == "true" for row in report)
    assert all(row["ready_for_training_dataset_design_after_approval"] == "true" for row in report)
    assert all(row["training_dataset_design_executed"] == "false" for row in report)
    assert all(row["real_training_tensor_generated"] == "false" for row in report)
    assert all(row["real_dataset_generated"] == "false" for row in report)
    assert all(row["dataloader_tensor_generated"] == "false" for row in report)
    assert all(row["torch_imported"] == "false" for row in report)
    assert all(row["checkpoint_loaded"] == "false" for row in report)
    assert all(row["model_initialized"] == "false" for row in report)
    assert all(row["training_ready"] == "false" for row in report)
    assert not Path(PLANNED_TRAINING_DATASET_DESIGN_ROOT).exists()
    assert "Training Dataset Design Gate Summary" in paths["training_gate_summary"].read_text(encoding="utf-8")
    for key, before in input_hashes.items():
        assert _sha(paths[key]) == before


def test_snapshot_qa_report_missing_or_bad_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    paths["qa_report"].unlink()
    _assert_blocked(paths, "snapshot_review_qa_row_found_once")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["qa_report"])
    _write_csv(paths["qa_report"], rows[:2], list(rows[0]))
    _assert_blocked(paths, "snapshot_review_qa_row_found_once")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["qa_report"])
    rows[0]["dataset_snapshot_review_qa_status"] = "blocked"
    _write_csv(paths["qa_report"], rows, list(rows[0]))
    _assert_blocked(paths, "snapshot_review_qa_status_passed")


def test_snapshot_review_report_manifest_and_file_list_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_report"])
    _write_csv(paths["snapshot_report"], rows[:2], list(rows[0]))
    _assert_blocked(paths, "snapshot_review_report_row_found_once")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_report"])
    rows[0]["dataset_snapshot_review_status"] = "blocked"
    _write_csv(paths["snapshot_report"], rows, list(rows[0]))
    _assert_blocked(paths, "snapshot_review_status_passed")
    paths = _make_fixture(tmp_path)
    paths["snapshot_manifest"].write_text("{bad", encoding="utf-8")
    _assert_blocked(paths, "snapshot_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["snapshot_manifest"].read_text(encoding="utf-8"))
    manifest["row_count"] = 4
    paths["snapshot_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "snapshot_manifest_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_file_list"])
    _write_csv(paths["snapshot_file_list"], rows[:22], list(rows[0]))
    _assert_blocked(paths, "snapshot_file_list_row_count_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_file_list"])
    rows = [row for row in rows if not (row["row_type"] == "candidate_file" and row["candidate_id"] == next(iter(TARGETS)))]
    _write_csv(paths["snapshot_file_list"], rows, list(rows[0]))
    _assert_blocked(paths, "snapshot_candidate_file_rows_valid")


def test_index_package_manifest_label_and_count_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    Path(rows[0]["packaged_ligand_sdf_path"]).write_text("changed\n$$$$\n", encoding="utf-8")
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


def test_snapshot_forbidden_files_planned_outputs_and_global_forbidden_outputs_block(tmp_path):
    paths = _make_fixture(tmp_path)
    (Path(SNAPSHOT_ROOT) / "bad.sdf").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "snapshot_review_only_files_valid")
    paths = _make_fixture(tmp_path)
    Path(PLANNED_TRAINING_DATASET_DESIGN_ROOT).mkdir(parents=True)
    _assert_blocked(paths, "planned_training_dataset_design_outputs_absent_before_gate")
    paths = _make_fixture(tmp_path)
    tensor = Path("data/derived/covalent_small/bad.pt")
    tensor.parent.mkdir(parents=True, exist_ok=True)
    tensor.write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "forbidden_training_tensors_absent")
    paths = _make_fixture(tmp_path)
    archive = Path("data/derived/covalent_small/bad.zip")
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "forbidden_archives_absent")


def test_script_has_no_torch_import_checkpoint_model_or_training_calls():
    source = Path(__file__).resolve().parents[1] / "scripts" / "build_training_dataset_design_gate.py"
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
