import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_read_only_training_dataset_loader_dry_run import PLANNED_READ_ONLY_LOADER_ROOT, T_FIELD  # noqa: E402
from build_training_tensor_design_gate import PLANNED_TENSOR_DESIGN_ROOT, run  # noqa: E402
from test_read_only_training_dataset_loader_dry_run_qa import _make_fixture as _make_qa_fixture, _run as _run_qa  # noqa: E402
from test_training_dataset_design_gate import _read_csv, _write_csv  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _args(paths):
    root = Path(PLANNED_READ_ONLY_LOADER_ROOT)
    return argparse.Namespace(
        read_only_loader_dry_run_qa_report_csv=paths["dry_run_qa_report"],
        dry_run_manifest_json=paths["dry_run_manifest"],
        dry_run_report_csv=paths["dry_run_report"],
        dry_run_summary_md=paths["dry_run_summary"],
        read_only_training_dataset_loader_gate_plan_csv=paths["loader_gate_plan"],
        read_only_training_dataset_loader_gate_report_csv=paths["loader_gate_report"],
        real_training_dataset_packaging_qa_report_csv=paths["real_packaging_qa_report"],
        real_training_dataset_manifest_json=paths["real_manifest"],
        real_training_dataset_file_index_csv=paths["real_file_index"],
        real_training_dataset_sample_index_csv=paths["real_sample_index"],
        real_training_dataset_packaging_report_csv=paths["real_packaging_report"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_gate_plan_csv=root / "training_tensor_design_gate_plan.csv",
        output_report_csv=root / "training_tensor_design_gate_report.csv",
        output_md=Path("docs/training_tensor_design_gate_summary.md"),
    )


def _make_fixture(tmp_path):
    paths = _make_qa_fixture(tmp_path)
    rows, code = _run_qa(paths)
    assert code == 0
    assert len(rows) == 3
    paths["tensor_gate_plan"] = Path(PLANNED_READ_ONLY_LOADER_ROOT) / "training_tensor_design_gate_plan.csv"
    paths["tensor_gate_report"] = Path(PLANNED_READ_ONLY_LOADER_ROOT) / "training_tensor_design_gate_report.csv"
    paths["tensor_gate_summary"] = Path("docs/training_tensor_design_gate_summary.md")
    return paths


def _run(paths):
    return run(_args(paths))


def _write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _assert_blocked(paths, reason):
    plan_rows, report_rows, code = _run(paths)
    assert code == 1
    assert len(report_rows) == 3
    assert len(_read_csv(paths["tensor_gate_report"])) == 3
    assert any(row["training_tensor_design_gate_status"] == "blocked" for row in report_rows)
    assert any(reason in row["blocking_reasons"] for row in report_rows)
    assert len(plan_rows) < 3


def test_success_outputs_three_gate_rows_without_modifying_inputs(tmp_path):
    paths = _make_fixture(tmp_path)
    protected = [
        "dry_run_qa_report",
        "dry_run_manifest",
        "dry_run_report",
        "dry_run_summary",
        "loader_gate_plan",
        "loader_gate_report",
        "real_packaging_qa_report",
        "real_manifest",
        "real_file_index",
        "real_sample_index",
        "real_packaging_report",
        "index",
        "dataset_manifest",
        "raw_manifest",
    ]
    input_hashes = {key: _sha(paths[key]) for key in protected}
    plan_rows, report_rows, code = _run(paths)
    assert code == 0
    assert len(plan_rows) == 3
    assert len(report_rows) == 3
    assert len(_read_csv(paths["tensor_gate_plan"])) == 3
    assert len(_read_csv(paths["tensor_gate_report"])) == 3
    assert paths["tensor_gate_summary"].is_file()
    assert all(row["training_tensor_design_gate_status"] == "training_tensor_design_gate_passed" for row in report_rows)
    assert all(row["explicit_approval_required_before_training_tensor_design"] == "true" for row in report_rows)
    assert all(row["ready_for_training_tensor_design_after_approval"] == "true" for row in report_rows)
    assert all(row["training_tensor_design_executed"] == "false" for row in report_rows)
    assert all(row["tensor_schema_generated"] == "false" for row in report_rows)
    assert all(row["tensor_files_generated"] == "false" for row in report_rows)
    assert all(row["dataloader_tensor_generated"] == "false" for row in report_rows)
    assert all(row["real_training_tensor_generated"] == "false" for row in report_rows)
    assert all(row["real_dataset_generated"] == "false" for row in report_rows)
    assert all(row[T_FIELD] == "false" for row in report_rows)
    assert all(row["checkpoint_loaded"] == "false" for row in report_rows)
    assert all(row["model_initialized"] == "false" for row in report_rows)
    assert all(row["training_ready"] == "false" for row in report_rows)
    assert all(row["files_copied"] == "false" for row in report_rows)
    assert all(row["archive_created"] == "false" for row in report_rows)
    assert all(row["dry_run_qa_status_passed"] == "true" for row in report_rows)
    assert all(row["dry_run_record_fields_valid"] == "true" for row in report_rows)
    assert all(row["dry_run_record_hashes_valid"] == "true" for row in report_rows)
    assert all(row["dry_run_report_safety_flags_valid"] == "true" for row in report_rows)
    assert all(row["upstream_loader_gate_status_still_passed"] == "true" for row in report_rows)
    assert all(row["upstream_real_training_dataset_packaging_qa_status_still_passed"] == "true" for row in report_rows)
    assert all(row["planned_training_tensor_design_root_absent_before_gate"] == "true" for row in report_rows)
    assert {path.name for path in paths["dry_run_root"].iterdir()} == {
        "read_only_training_dataset_loader_dry_run_manifest.json",
        "read_only_training_dataset_loader_dry_run_report.csv",
        "read_only_training_dataset_loader_dry_run_summary.md",
        "read_only_training_dataset_loader_dry_run_qa_report.csv",
        "training_tensor_design_gate_plan.csv",
        "training_tensor_design_gate_report.csv",
    }
    assert not Path(PLANNED_TENSOR_DESIGN_ROOT).exists()
    for key, before in input_hashes.items():
        assert _sha(paths[key]) == before
    assert "Training Tensor Design Gate Summary" in paths["tensor_gate_summary"].read_text(encoding="utf-8")


def test_dry_run_qa_manifest_record_and_report_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["dry_run_qa_report"])
    rows[0]["read_only_training_dataset_loader_dry_run_qa_status"] = "blocked"
    _write_csv(paths["dry_run_qa_report"], rows, list(rows[0]))
    _assert_blocked(paths, "dry_run_qa_status_passed")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["dry_run_manifest"].read_text(encoding="utf-8"))
    manifest["row_count"] = 2
    _write_json(paths["dry_run_manifest"], manifest)
    _assert_blocked(paths, "dry_run_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["dry_run_manifest"].read_text(encoding="utf-8"))
    manifest["read_only_record_count"] = 2
    _write_json(paths["dry_run_manifest"], manifest)
    _assert_blocked(paths, "dry_run_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["dry_run_manifest"].read_text(encoding="utf-8"))
    manifest["loader_mode"] = "changed"
    _write_json(paths["dry_run_manifest"], manifest)
    _assert_blocked(paths, "dry_run_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["dry_run_manifest"].read_text(encoding="utf-8"))
    manifest["safety_flags"][T_FIELD] = True
    _write_json(paths["dry_run_manifest"], manifest)
    _assert_blocked(paths, "dry_run_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["dry_run_manifest"].read_text(encoding="utf-8"))
    manifest["read_only_records"] = manifest["read_only_records"][:2]
    _write_json(paths["dry_run_manifest"], manifest)
    _assert_blocked(paths, "dry_run_record_found_once")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["dry_run_manifest"].read_text(encoding="utf-8"))
    manifest["read_only_records"][0]["packaged_ligand_sdf_sha256"] = "bad"
    _write_json(paths["dry_run_manifest"], manifest)
    _assert_blocked(paths, "dry_run_record_hashes_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["dry_run_manifest"].read_text(encoding="utf-8"))
    manifest["read_only_records"][0]["tensor_generated"] = True
    _write_json(paths["dry_run_manifest"], manifest)
    _assert_blocked(paths, "dry_run_record_safety_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["dry_run_report"])
    rows[0]["loader_dry_run_status"] = "blocked"
    _write_csv(paths["dry_run_report"], rows, list(rows[0]))
    _assert_blocked(paths, "dry_run_report_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["dry_run_report"])
    rows[0]["dataloader_built"] = "true"
    _write_csv(paths["dry_run_report"], rows, list(rows[0]))
    _assert_blocked(paths, "dry_run_report_safety_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["dry_run_report"])
    rows[0]["tensor_file_count"] = "1"
    _write_csv(paths["dry_run_report"], rows, list(rows[0]))
    _assert_blocked(paths, "dry_run_report_safety_flags_valid")


def test_upstream_package_index_and_planned_root_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["loader_gate_report"])
    rows[0]["read_only_training_dataset_loader_gate_status"] = "blocked"
    _write_csv(paths["loader_gate_report"], rows, list(rows[0]))
    _assert_blocked(paths, "upstream_loader_gate_status_still_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_packaging_qa_report"])
    rows[0]["real_training_dataset_packaging_qa_status"] = "blocked"
    _write_csv(paths["real_packaging_qa_report"], rows, list(rows[0]))
    _assert_blocked(paths, "upstream_real_training_dataset_packaging_qa_status_still_passed")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["real_manifest"].read_text(encoding="utf-8"))
    manifest["file_index_row_count"] = 14
    _write_json(paths["real_manifest"], manifest)
    _assert_blocked(paths, "real_training_dataset_package_still_valid")
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
    Path(PLANNED_TENSOR_DESIGN_ROOT).mkdir(parents=True)
    _assert_blocked(paths, "planned_training_tensor_design_root_absent_before_gate")


def test_dry_root_forbidden_tensor_and_archive_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    paths["dry_run_summary"].unlink()
    _assert_blocked(paths, "dry_run_root_files_valid")
    paths = _make_fixture(tmp_path)
    (paths["dry_run_root"] / "copied.sdf").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "dry_run_root_files_valid")
    paths = _make_fixture(tmp_path)
    (paths["dry_run_root"] / "metadata_copy.json").write_text("{}", encoding="utf-8")
    _assert_blocked(paths, "dry_run_root_files_valid")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "forbidden_training_tensors_absent")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.tgz").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "forbidden_archives_absent")


def test_static_source_avoids_disallowed_runtime_terms():
    script = Path(__file__).resolve().parents[1] / "scripts" / "build_training_tensor_design_gate.py"
    sources = [script, Path(__file__)]
    for source in sources:
        text = source.read_text(encoding="utf-8")
        assert ("tor" + "ch") not in text
        assert ("Data" + "Loader") not in text
        assert ("Data" + "set") not in text
        tree = ast.parse(text)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert ("tor" + "ch") not in imported
        assert "load_" + "checkpoint(" not in text
        assert "initialize_" + "model(" not in text
        assert "tr" + "ain(" not in text
