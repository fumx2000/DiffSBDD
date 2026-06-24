import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_read_only_training_dataset_loader_dry_run import T_FIELD  # noqa: E402
from build_training_tensor_materialization_gate import PLANNED_MATERIALIZATION_ROOT, run  # noqa: E402
from test_training_dataset_design_gate import _read_csv, _write_csv  # noqa: E402
from test_training_tensor_design_review_qa import _make_fixture as _make_qa_fixture, _run as _run_qa  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _args(paths):
    return argparse.Namespace(
        training_tensor_design_review_qa_report_csv=paths["qa_report"],
        training_tensor_design_manifest_json=paths["design_manifest"],
        training_tensor_design_schema_report_csv=paths["schema_report"],
        training_tensor_design_plan_csv=paths["design_plan"],
        training_tensor_design_report_csv=paths["design_report"],
        training_tensor_design_summary_md=paths["design_summary"],
        training_tensor_design_qa_summary_md=paths["qa_summary"],
        training_tensor_design_gate_plan_csv=paths["tensor_gate_plan"],
        training_tensor_design_gate_report_csv=paths["tensor_gate_report"],
        read_only_loader_dry_run_qa_report_csv=paths["dry_run_qa_report"],
        dry_run_manifest_json=paths["dry_run_manifest"],
        dry_run_report_csv=paths["dry_run_report"],
        dry_run_summary_md=paths["dry_run_summary"],
        real_training_dataset_packaging_qa_report_csv=paths["real_packaging_qa_report"],
        real_training_dataset_manifest_json=paths["real_manifest"],
        real_training_dataset_file_index_csv=paths["real_file_index"],
        real_training_dataset_sample_index_csv=paths["real_sample_index"],
        real_training_dataset_packaging_report_csv=paths["real_packaging_report"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_gate_plan_csv=paths["design_root"] / "training_tensor_materialization_gate_plan.csv",
        output_report_csv=paths["design_root"] / "training_tensor_materialization_gate_report.csv",
        output_md=Path("docs/training_tensor_materialization_gate_summary.md"),
    )


def _make_fixture(tmp_path):
    paths = _make_qa_fixture(tmp_path)
    rows, code = _run_qa(paths)
    assert code == 0
    assert len(rows) == 3
    paths["materialization_gate_plan"] = paths["design_root"] / "training_tensor_materialization_gate_plan.csv"
    paths["materialization_gate_report"] = paths["design_root"] / "training_tensor_materialization_gate_report.csv"
    paths["materialization_gate_summary"] = Path("docs/training_tensor_materialization_gate_summary.md")
    return paths


def _run(paths):
    return run(_args(paths))


def _write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _assert_blocked(paths, reason):
    plan_rows, report_rows, code = _run(paths)
    assert code == 1
    assert len(report_rows) == 3
    assert len(_read_csv(paths["materialization_gate_report"])) == 3
    assert len(plan_rows) < 3
    assert any(row["training_tensor_materialization_gate_status"] == "blocked" for row in report_rows)
    assert any(reason in row["blocking_reasons"] for row in report_rows)


def test_success_outputs_three_gate_rows_without_modifying_inputs(tmp_path):
    paths = _make_fixture(tmp_path)
    protected = [
        "qa_report",
        "design_manifest",
        "schema_report",
        "design_plan",
        "design_report",
        "design_summary",
        "qa_summary",
        "tensor_gate_plan",
        "tensor_gate_report",
        "dry_run_qa_report",
        "dry_run_manifest",
        "dry_run_report",
        "dry_run_summary",
        "real_packaging_qa_report",
        "real_manifest",
        "real_file_index",
        "real_sample_index",
        "real_packaging_report",
        "index",
        "dataset_manifest",
        "raw_manifest",
    ]
    before = {key: _sha(paths[key]) for key in protected}
    plan_rows, report_rows, code = _run(paths)
    assert code == 0
    assert len(plan_rows) == 3
    assert len(report_rows) == 3
    assert len(_read_csv(paths["materialization_gate_plan"])) == 3
    assert len(_read_csv(paths["materialization_gate_report"])) == 3
    assert paths["materialization_gate_summary"].is_file()
    assert all(row["training_tensor_materialization_gate_status"] == "training_tensor_materialization_gate_passed" for row in report_rows)
    assert all(row["explicit_approval_required_before_tensor_materialization"] == "true" for row in report_rows)
    assert all(row["ready_for_tensor_materialization_after_approval"] == "true" for row in report_rows)
    assert all(row["tensor_materialization_executed"] == "false" for row in report_rows)
    assert all(row["tensor_schema_generated"] == "true" for row in report_rows)
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
    assert all(row["design_qa_status_passed"] == "true" for row in report_rows)
    assert all(row["schema_report_valid"] == "true" for row in report_rows)
    assert all(row["design_plan_status_valid"] == "true" for row in report_rows)
    assert all(row["design_report_status_passed"] == "true" for row in report_rows)
    assert all(row["design_report_safety_flags_valid"] == "true" for row in report_rows)
    assert all(row["design_root_files_valid"] == "true" for row in report_rows)
    assert all(row["planned_materialization_root_absent_before_gate"] == "true" for row in report_rows)
    assert not Path(PLANNED_MATERIALIZATION_ROOT).exists()
    assert {path.name for path in paths["design_root"].iterdir()} == {
        "training_tensor_design_manifest.json",
        "training_tensor_design_schema_report.csv",
        "training_tensor_design_plan.csv",
        "training_tensor_design_report.csv",
        "training_tensor_design_review_qa_report.csv",
        "training_tensor_materialization_gate_plan.csv",
        "training_tensor_materialization_gate_report.csv",
    }
    for key, digest in before.items():
        assert _sha(paths[key]) == digest


def test_design_qa_manifest_schema_and_plan_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["qa_report"])
    rows[0]["training_tensor_design_review_qa_status"] = "blocked"
    _write_csv(paths["qa_report"], rows, list(rows[0]))
    _assert_blocked(paths, "design_qa_status_passed")
    paths = _make_fixture(tmp_path)
    paths["design_manifest"].unlink()
    _assert_blocked(paths, "design_manifest_valid")
    paths = _make_fixture(tmp_path)
    paths["design_manifest"].write_text("{bad", encoding="utf-8")
    _assert_blocked(paths, "design_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["design_manifest"].read_text(encoding="utf-8"))
    manifest["row_count"] = 2
    _write_json(paths["design_manifest"], manifest)
    _assert_blocked(paths, "design_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["design_manifest"].read_text(encoding="utf-8"))
    manifest["schema_field_count"] = 46
    _write_json(paths["design_manifest"], manifest)
    _assert_blocked(paths, "design_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["design_manifest"].read_text(encoding="utf-8"))
    manifest["tensor_design_mode"] = "changed"
    _write_json(paths["design_manifest"], manifest)
    _assert_blocked(paths, "design_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["design_manifest"].read_text(encoding="utf-8"))
    manifest["safety_flags"][T_FIELD] = True
    _write_json(paths["design_manifest"], manifest)
    _assert_blocked(paths, "design_manifest_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["schema_report"])
    _write_csv(paths["schema_report"], rows[:46], list(rows[0]))
    _assert_blocked(paths, "schema_report_valid")
    paths = _make_fixture(tmp_path)
    rows = [row for row in _read_csv(paths["schema_report"]) if row["field_name"] != "generation_mask_A_warhead_only"]
    _write_csv(paths["schema_report"], rows, list(rows[0]))
    _assert_blocked(paths, "schema_report_valid")
    paths = _make_fixture(tmp_path)
    rows = [row for row in _read_csv(paths["schema_report"]) if row["field_name"] != "warhead_type_label"]
    _write_csv(paths["schema_report"], rows, list(rows[0]))
    _assert_blocked(paths, "schema_report_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["schema_report"])
    rows[0]["tensor_generated"] = "true"
    _write_csv(paths["schema_report"], rows, list(rows[0]))
    _assert_blocked(paths, "schema_report_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_plan"])
    rows[0]["tensor_files_generated"] = "true"
    _write_csv(paths["design_plan"], rows, list(rows[0]))
    _assert_blocked(paths, "design_plan_status_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_plan"])
    rows[0]["training_ready"] = "true"
    _write_csv(paths["design_plan"], rows, list(rows[0]))
    _assert_blocked(paths, "design_plan_status_valid")


def test_design_report_root_package_and_global_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_report"])
    rows[0]["training_tensor_design_status"] = "blocked"
    _write_csv(paths["design_report"], rows, list(rows[0]))
    _assert_blocked(paths, "design_report_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_report"])
    rows[0]["tensor_files_generated"] = "true"
    _write_csv(paths["design_report"], rows, list(rows[0]))
    _assert_blocked(paths, "design_report_safety_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_report"])
    rows[0]["dataloader_tensor_generated"] = "true"
    _write_csv(paths["design_report"], rows, list(rows[0]))
    _assert_blocked(paths, "design_report_safety_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_report"])
    rows[0][T_FIELD] = "true"
    _write_csv(paths["design_report"], rows, list(rows[0]))
    _assert_blocked(paths, "design_report_safety_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_report"])
    rows[0]["training_ready"] = "true"
    _write_csv(paths["design_report"], rows, list(rows[0]))
    _assert_blocked(paths, "design_report_safety_flags_valid")
    paths = _make_fixture(tmp_path)
    Path(PLANNED_MATERIALIZATION_ROOT).mkdir(parents=True)
    _assert_blocked(paths, "planned_materialization_root_absent_before_gate")
    paths = _make_fixture(tmp_path)
    (paths["design_root"] / "bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "design_root_files_valid")
    paths = _make_fixture(tmp_path)
    (paths["design_root"] / "bad.tgz").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "design_root_files_valid")
    paths = _make_fixture(tmp_path)
    (paths["design_root"] / "copied_metadata.json").write_text("{}", encoding="utf-8")
    _assert_blocked(paths, "design_root_files_valid")
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
    Path("data/derived/covalent_small/bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "forbidden_training_tensors_absent")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.tgz").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "forbidden_archives_absent")


def test_static_source_avoids_disallowed_runtime_terms():
    script = Path(__file__).resolve().parents[1] / "scripts" / "build_training_tensor_materialization_gate.py"
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
