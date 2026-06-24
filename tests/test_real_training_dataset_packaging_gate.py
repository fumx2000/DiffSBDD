import argparse
import ast
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_real_training_dataset_packaging_gate import PLANNED_REAL_PACKAGE_ROOT, run  # noqa: E402
from test_training_dataset_design_gate import _read_csv, _write_csv  # noqa: E402
from test_training_dataset_packaging_design_review_qa import _make_fixture as _make_qa_fixture, _run as _run_qa  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _args(paths):
    return argparse.Namespace(
        packaging_design_review_qa_report_csv=paths["packaging_qa_report"],
        packaging_design_manifest_json=paths["packaging_design_manifest"],
        packaging_file_plan_csv=paths["packaging_file_plan"],
        packaging_schema_report_csv=paths["packaging_schema_report"],
        packaging_design_report_csv=paths["packaging_design_report"],
        training_dataset_packaging_design_gate_plan_csv=paths["packaging_gate_plan"],
        training_dataset_packaging_design_gate_report_csv=paths["packaging_gate_report"],
        training_dataset_design_review_qa_report_csv=paths["design_qa_report"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_gate_plan_csv=Path("data/derived/covalent_small/training_dataset_packaging_design_review_only/real_training_dataset_packaging_gate_plan.csv"),
        output_report_csv=Path("data/derived/covalent_small/training_dataset_packaging_design_review_only/real_training_dataset_packaging_gate_report.csv"),
        output_md=paths["packaging_qa_summary"].parent / "real_training_dataset_packaging_gate_summary.md",
    )


def _make_fixture(tmp_path):
    paths = _make_qa_fixture(tmp_path)
    rows, code = _run_qa(paths)
    assert code == 0
    assert len(rows) == 3
    paths["real_packaging_gate_plan"] = Path("data/derived/covalent_small/training_dataset_packaging_design_review_only/real_training_dataset_packaging_gate_plan.csv")
    paths["real_packaging_gate_report"] = Path("data/derived/covalent_small/training_dataset_packaging_design_review_only/real_training_dataset_packaging_gate_report.csv")
    paths["real_packaging_gate_summary"] = paths["packaging_qa_summary"].parent / "real_training_dataset_packaging_gate_summary.md"
    return paths


def _run(paths):
    return run(_args(paths))


def _assert_blocked(paths, reason):
    plan, report, code = _run(paths)
    assert code == 1
    assert len(report) == 3
    assert any(row["real_training_dataset_packaging_gate_status"] == "blocked" for row in report)
    assert any(reason in row["blocking_reasons"] for row in report)
    assert len(plan) < 3


def test_success_outputs_three_passed_rows(tmp_path):
    paths = _make_fixture(tmp_path)
    plan, report, code = _run(paths)
    assert code == 0
    assert len(plan) == 3
    assert len(report) == 3
    assert len(_read_csv(paths["real_packaging_gate_plan"])) == 3
    assert len(_read_csv(paths["real_packaging_gate_report"])) == 3
    assert all(row["real_training_dataset_packaging_gate_status"] == "real_training_dataset_packaging_gate_passed" for row in report)
    assert all(row["explicit_approval_required_before_real_training_dataset_packaging"] == "true" for row in report)
    assert all(row["ready_for_real_training_dataset_packaging_after_approval"] == "true" for row in report)
    assert all(row["real_training_dataset_packaging_executed"] == "false" for row in report)
    assert all(row["real_training_tensor_generated"] == "false" for row in report)
    assert all(row["real_dataset_generated"] == "false" for row in report)
    assert all(row["dataloader_tensor_generated"] == "false" for row in report)
    assert all(row["torch_imported"] == "false" for row in report)
    assert all(row["checkpoint_loaded"] == "false" for row in report)
    assert all(row["model_initialized"] == "false" for row in report)
    assert all(row["training_ready"] == "false" for row in report)
    assert all(row["files_copied"] == "false" for row in report)
    assert all(row["archive_created"] == "false" for row in report)
    assert not Path(PLANNED_REAL_PACKAGE_ROOT).exists()
    assert "Real Training Dataset Packaging Gate Summary" in paths["real_packaging_gate_summary"].read_text(encoding="utf-8")


def test_packaging_qa_manifest_file_plan_schema_and_design_report_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    paths["packaging_qa_report"].unlink()
    _assert_blocked(paths, "packaging_design_review_qa_row_found_once")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_qa_report"])
    rows[0]["training_dataset_packaging_design_review_qa_status"] = "blocked"
    _write_csv(paths["packaging_qa_report"], rows, list(rows[0]))
    _assert_blocked(paths, "packaging_design_review_qa_status_passed")
    paths = _make_fixture(tmp_path)
    paths["packaging_design_manifest"].write_text("{bad", encoding="utf-8")
    _assert_blocked(paths, "packaging_design_manifest_valid")
    paths = _make_fixture(tmp_path)
    rows = [
        row
        for row in _read_csv(paths["packaging_file_plan"])
        if not (row["candidate_id"] == "BTK_C481_6DI9_pre_reaction" and row["file_role"] == "source_ligand_sdf")
    ]
    _write_csv(paths["packaging_file_plan"], rows, list(rows[0]))
    _assert_blocked(paths, "packaging_file_plan_candidate_rows_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_file_plan"])
    rows[0]["source_file_sha256"] = "bad"
    _write_csv(paths["packaging_file_plan"], rows, list(rows[0]))
    _assert_blocked(paths, "packaging_file_plan_hashes_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_file_plan"])
    rows[0]["copied_to_training_package"] = "true"
    _write_csv(paths["packaging_file_plan"], rows, list(rows[0]))
    _assert_blocked(paths, "packaging_file_plan_reference_only_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_schema_report"])
    _write_csv(paths["packaging_schema_report"], rows[:-1], list(rows[0]))
    _assert_blocked(paths, "packaging_schema_report_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_design_report"])
    rows[0]["training_dataset_packaging_design_status"] = "blocked"
    _write_csv(paths["packaging_design_report"], rows, list(rows[0]))
    _assert_blocked(paths, "packaging_design_report_status_passed")


def test_index_package_path_label_count_and_forbidden_artifact_blockers(tmp_path):
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
    paths = _make_fixture(tmp_path)
    (Path("data/derived/covalent_small/training_dataset_packaging_design_review_only") / "bad.sdf").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "packaging_design_review_only_files_valid")
    paths = _make_fixture(tmp_path)
    Path(PLANNED_REAL_PACKAGE_ROOT).mkdir(parents=True)
    _assert_blocked(paths, "planned_real_training_dataset_package_root_absent_before_gate")
    paths = _make_fixture(tmp_path)
    tensor = Path("data/derived/covalent_small/bad.pt")
    tensor.parent.mkdir(parents=True, exist_ok=True)
    tensor.write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "forbidden_training_tensors_absent")
    paths = _make_fixture(tmp_path)
    archive = Path("data/derived/covalent_small/bad.tgz")
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "forbidden_archives_absent")


def test_script_has_no_disallowed_runtime_calls():
    source = Path(__file__).resolve().parents[1] / "scripts" / "build_real_training_dataset_packaging_gate.py"
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
