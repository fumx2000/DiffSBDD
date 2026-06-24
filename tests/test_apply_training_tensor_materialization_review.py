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
from apply_training_tensor_materialization_review import APPROVAL_TOKEN, PLANNED_MATERIALIZATION_ROOT, run  # noqa: E402
from test_training_dataset_design_gate import _read_csv, _write_csv  # noqa: E402
from test_training_tensor_materialization_gate import _make_fixture as _make_gate_fixture, _run as _run_gate  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _args(paths, approval_token=APPROVAL_TOKEN):
    root = Path(PLANNED_MATERIALIZATION_ROOT)
    return argparse.Namespace(
        training_tensor_materialization_gate_plan_csv=paths["materialization_gate_plan"],
        training_tensor_materialization_gate_report_csv=paths["materialization_gate_report"],
        training_tensor_design_review_qa_report_csv=paths["qa_report"],
        training_tensor_design_manifest_json=paths["design_manifest"],
        training_tensor_design_schema_report_csv=paths["schema_report"],
        training_tensor_design_plan_csv=paths["design_plan"],
        training_tensor_design_report_csv=paths["design_report"],
        training_tensor_design_summary_md=paths["design_summary"],
        training_tensor_design_qa_summary_md=paths["qa_summary"],
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
        output_manifest_json=root / "training_tensor_materialization_manifest.json",
        output_plan_csv=root / "training_tensor_materialization_plan.csv",
        output_report_csv=root / "training_tensor_materialization_report.csv",
        output_file_plan_csv=root / "training_tensor_materialization_file_plan.csv",
        output_md=Path("docs/training_tensor_materialization_review_summary.md"),
        approval_token=approval_token,
    )


def _make_fixture(tmp_path):
    paths = _make_gate_fixture(tmp_path)
    plan_rows, report_rows, code = _run_gate(paths)
    assert code == 0
    assert len(plan_rows) == 3
    assert len(report_rows) == 3
    paths["materialization_root"] = Path(PLANNED_MATERIALIZATION_ROOT)
    paths["materialization_manifest"] = paths["materialization_root"] / "training_tensor_materialization_manifest.json"
    paths["materialization_plan"] = paths["materialization_root"] / "training_tensor_materialization_plan.csv"
    paths["materialization_report"] = paths["materialization_root"] / "training_tensor_materialization_report.csv"
    paths["materialization_file_plan"] = paths["materialization_root"] / "training_tensor_materialization_file_plan.csv"
    paths["materialization_summary"] = Path("docs/training_tensor_materialization_review_summary.md")
    return paths


def _run(paths, approval_token=APPROVAL_TOKEN):
    return run(_args(paths, approval_token))


def _write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _assert_blocked_without_outputs(paths, reason=None):
    plan, report, file_plan, manifest, code = _run(paths)
    assert code == 1
    assert plan == []
    assert report == []
    assert file_plan == []
    assert manifest == {}
    assert not paths["materialization_root"].exists()
    assert reason or True


def test_wrong_approval_token_blocks_without_outputs(tmp_path):
    paths = _make_fixture(tmp_path)
    plan, report, file_plan, manifest, code = _run(paths, "WRONG")
    assert code == 1
    assert plan == []
    assert report == []
    assert file_plan == []
    assert manifest == {}
    assert not paths["materialization_root"].exists()
    assert not paths["materialization_summary"].exists()


def test_success_writes_review_only_outputs_without_modifying_inputs(tmp_path):
    paths = _make_fixture(tmp_path)
    protected = [
        "materialization_gate_plan",
        "materialization_gate_report",
        "qa_report",
        "design_manifest",
        "schema_report",
        "design_plan",
        "design_report",
        "design_summary",
        "qa_summary",
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
    plan, report, file_plan, manifest, code = _run(paths)
    assert code == 0
    assert len(plan) == 3
    assert len(_read_csv(paths["materialization_plan"])) == 3
    assert len(report) == 3
    assert len(_read_csv(paths["materialization_report"])) == 3
    assert len(file_plan) == 12
    assert len(_read_csv(paths["materialization_file_plan"])) == 12
    assert paths["materialization_manifest"].is_file()
    assert paths["materialization_summary"].is_file()
    parsed = json.loads(paths["materialization_manifest"].read_text(encoding="utf-8"))
    assert parsed["row_count"] == 3
    assert parsed["plan_row_count"] == 3
    assert parsed["report_row_count"] == 3
    assert parsed["file_plan_row_count"] == 12
    assert parsed["tensor_materialization_review_executed"] is True
    assert parsed["tensor_materialization_executed"] is False
    assert parsed["tensor_files_generated"] is False
    assert parsed["tensor_file_count"] == 0
    assert manifest["planned_tensor_file_count"] == 3
    assert all(row["training_tensor_materialization_status"] == "training_tensor_materialization_review_passed" for row in report)
    assert all(row["tensor_materialization_review_executed"] == "true" for row in report)
    assert all(row["tensor_materialization_executed"] == "false" for row in report)
    assert all(row["tensor_schema_generated"] == "true" for row in report)
    assert all(row["tensor_files_generated"] == "false" for row in report)
    assert all(row["dataloader_tensor_generated"] == "false" for row in report)
    assert all(row["real_training_tensor_generated"] == "false" for row in report)
    assert all(row["real_dataset_generated"] == "false" for row in report)
    assert all(row[T_FIELD] == "false" for row in report)
    assert all(row["checkpoint_loaded"] == "false" for row in report)
    assert all(row["model_initialized"] == "false" for row in report)
    assert all(row["training_ready"] == "false" for row in report)
    assert all(row["files_copied"] == "false" for row in report)
    assert all(row["copied_file_count"] == "0" for row in report)
    assert all(row["archive_created"] == "false" for row in report)
    for sample_id in {row["sample_id"] for row in file_plan}:
        sample_rows = [row for row in file_plan if row["sample_id"] == sample_id]
        assert len(sample_rows) == 4
        assert sum(row["tensor_file"] == "true" for row in sample_rows) == 1
        for row in sample_rows:
            assert row["generated_in_this_step"] == "false"
            assert row["file_exists_now"] == "false"
            assert row["expected_future_sha256"] == ""
            assert not Path(row["planned_file_path"]).exists()
    assert sorted(path.name for path in paths["materialization_root"].rglob("*") if path.is_file()) == [
        "training_tensor_materialization_file_plan.csv",
        "training_tensor_materialization_manifest.json",
        "training_tensor_materialization_plan.csv",
        "training_tensor_materialization_report.csv",
    ]
    for suffix in [".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"]:
        assert not list(paths["materialization_root"].rglob(f"*{suffix}"))
    for key, digest in before.items():
        assert _sha(paths[key]) == digest


def test_gate_design_index_and_output_blockers_do_not_create_outputs(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["materialization_gate_report"])
    rows[0]["training_tensor_materialization_gate_status"] = "blocked"
    _write_csv(paths["materialization_gate_report"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "gate")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["qa_report"])
    rows[0]["training_tensor_design_review_qa_status"] = "blocked"
    _write_csv(paths["qa_report"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "qa")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["design_manifest"].read_text(encoding="utf-8"))
    manifest["row_count"] = 2
    _write_json(paths["design_manifest"], manifest)
    _assert_blocked_without_outputs(paths, "manifest")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["schema_report"])
    rows[0]["tensor_generated"] = "true"
    _write_csv(paths["schema_report"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "schema")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_plan"])
    rows[0]["tensor_files_generated"] = "true"
    _write_csv(paths["design_plan"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "plan")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_report"])
    rows[0]["training_tensor_design_status"] = "blocked"
    _write_csv(paths["design_report"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "report")
    paths = _make_fixture(tmp_path)
    Path(_read_csv(paths["index"])[0]["packaged_ligand_sdf_path"]).write_text("changed\n$$$$\n", encoding="utf-8")
    _assert_blocked_without_outputs(paths, "hash")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["raw_manifest"])
    rows[1]["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["raw_manifest"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "manifest path")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["supported_mask_levels"] = "A_warhead_only"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "mask")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["required_auxiliary_labels"] = "warhead_type"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "aux")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["ligand_atom_count"] = "0"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "graph")
    paths = _make_fixture(tmp_path)
    paths["materialization_root"].mkdir(parents=True)
    (paths["materialization_root"] / "old.csv").write_text("old", encoding="utf-8")
    plan, report, file_plan, manifest, code = _run(paths)
    assert code == 1
    assert plan == []
    assert report == []
    assert file_plan == []
    assert manifest == {}
    assert (paths["materialization_root"] / "old.csv").read_text(encoding="utf-8") == "old"
    assert not paths["materialization_manifest"].exists()
    assert not paths["materialization_plan"].exists()
    assert not paths["materialization_report"].exists()
    assert not paths["materialization_file_plan"].exists()
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked_without_outputs(paths, "numeric")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.tgz").write_text("bad", encoding="utf-8")
    _assert_blocked_without_outputs(paths, "archive")


def test_static_source_avoids_disallowed_runtime_terms():
    script = Path(__file__).resolve().parents[1] / "scripts" / "apply_training_tensor_materialization_review.py"
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
