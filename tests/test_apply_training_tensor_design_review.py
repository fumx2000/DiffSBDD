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
from apply_training_tensor_design_review import APPROVAL_TOKEN, PLANNED_TENSOR_DESIGN_ROOT, run  # noqa: E402
from test_training_dataset_design_gate import _read_csv, _write_csv  # noqa: E402
from test_training_tensor_design_gate import _make_fixture as _make_gate_fixture, _run as _run_gate  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _args(paths, approval_token=APPROVAL_TOKEN):
    root = Path(PLANNED_TENSOR_DESIGN_ROOT)
    return argparse.Namespace(
        training_tensor_design_gate_plan_csv=paths["tensor_gate_plan"],
        training_tensor_design_gate_report_csv=paths["tensor_gate_report"],
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
        output_manifest_json=root / "training_tensor_design_manifest.json",
        output_schema_report_csv=root / "training_tensor_design_schema_report.csv",
        output_plan_csv=root / "training_tensor_design_plan.csv",
        output_report_csv=root / "training_tensor_design_report.csv",
        output_md=Path("docs/training_tensor_design_review_summary.md"),
        approval_token=approval_token,
    )


def _make_fixture(tmp_path):
    paths = _make_gate_fixture(tmp_path)
    plan_rows, report_rows, code = _run_gate(paths)
    assert code == 0
    assert len(plan_rows) == 3
    assert len(report_rows) == 3
    paths["design_root"] = Path(PLANNED_TENSOR_DESIGN_ROOT)
    paths["design_manifest"] = paths["design_root"] / "training_tensor_design_manifest.json"
    paths["schema_report"] = paths["design_root"] / "training_tensor_design_schema_report.csv"
    paths["design_plan"] = paths["design_root"] / "training_tensor_design_plan.csv"
    paths["design_report"] = paths["design_root"] / "training_tensor_design_report.csv"
    paths["design_summary"] = Path("docs/training_tensor_design_review_summary.md")
    return paths


def _run(paths, approval_token=APPROVAL_TOKEN):
    return run(_args(paths, approval_token))


def _write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _assert_blocked_without_outputs(paths, reason=None):
    schema, plan, report, manifest, code = _run(paths)
    assert code == 1
    assert schema == []
    assert plan == []
    assert report == []
    assert manifest == {}
    assert not paths["design_root"].exists()
    assert reason or True


def test_wrong_approval_token_blocks_without_design_root(tmp_path):
    paths = _make_fixture(tmp_path)
    schema, plan, report, manifest, code = _run(paths, "WRONG")
    assert code == 1
    assert schema == []
    assert plan == []
    assert report == []
    assert manifest == {}
    assert not paths["design_root"].exists()


def test_success_writes_design_files_without_modifying_inputs(tmp_path):
    paths = _make_fixture(tmp_path)
    protected = [
        "tensor_gate_plan",
        "tensor_gate_report",
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
    schema, plan, report, manifest, code = _run(paths)
    assert code == 0
    assert paths["design_manifest"].is_file()
    assert paths["schema_report"].is_file()
    assert paths["design_plan"].is_file()
    assert paths["design_report"].is_file()
    assert paths["design_summary"].is_file()
    assert len(schema) > 20
    assert len(_read_csv(paths["schema_report"])) == len(schema)
    assert len(plan) == 3
    assert len(_read_csv(paths["design_plan"])) == 3
    assert len(report) == 3
    assert len(_read_csv(paths["design_report"])) == 3
    parsed = json.loads(paths["design_manifest"].read_text(encoding="utf-8"))
    assert parsed["design_stage"] == "training_tensor_design_review_only_not_training"
    assert parsed["row_count"] == 3
    assert parsed["plan_row_count"] == 3
    assert parsed["report_row_count"] == 3
    assert parsed["schema_field_count"] == len(schema)
    assert parsed["tensor_schema_generated"] is True
    assert parsed["tensor_files_generated"] is False
    assert manifest["tensor_design_mode"] == "schema_and_plan_only_no_tensor_files"
    assert all(row["training_tensor_design_status"] == "training_tensor_design_review_passed" for row in report)
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
    summary = paths["design_summary"].read_text(encoding="utf-8")
    assert "Training Tensor Design Review Summary" in summary
    assert "BTK_C481_6DI9_pre_reaction" in summary
    assert "{candidate_id}" not in summary
    for key, before in input_hashes.items():
        assert _sha(paths[key]) == before


def test_design_root_contains_only_four_review_files(tmp_path):
    paths = _make_fixture(tmp_path)
    _run(paths)
    files = sorted(path.name for path in paths["design_root"].rglob("*") if path.is_file())
    assert files == [
        "training_tensor_design_manifest.json",
        "training_tensor_design_plan.csv",
        "training_tensor_design_report.csv",
        "training_tensor_design_schema_report.csv",
    ]
    for suffix in [".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"]:
        assert not list(paths["design_root"].rglob(f"*{suffix}"))


def test_gate_dry_run_and_record_blockers_do_not_create_outputs(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["tensor_gate_report"])
    rows[0]["training_tensor_design_gate_status"] = "blocked"
    _write_csv(paths["tensor_gate_report"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "gate_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["dry_run_qa_report"])
    rows[0]["read_only_training_dataset_loader_dry_run_qa_status"] = "blocked"
    _write_csv(paths["dry_run_qa_report"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "dry_run_qa_status_passed")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["dry_run_manifest"].read_text(encoding="utf-8"))
    manifest["read_only_records"] = manifest["read_only_records"][:2]
    _write_json(paths["dry_run_manifest"], manifest)
    _assert_blocked_without_outputs(paths, "dry_run_record_found_once")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["dry_run_manifest"].read_text(encoding="utf-8"))
    manifest["read_only_records"][0]["packaged_ligand_sdf_sha256"] = "bad"
    _write_json(paths["dry_run_manifest"], manifest)
    _assert_blocked_without_outputs(paths, "dry_run_record_hashes_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["dry_run_manifest"].read_text(encoding="utf-8"))
    manifest["read_only_records"][0]["tensor_generated"] = True
    _write_json(paths["dry_run_manifest"], manifest)
    _assert_blocked_without_outputs(paths, "dry_run_record_safety_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["dry_run_report"])
    rows[0]["loader_dry_run_status"] = "blocked"
    _write_csv(paths["dry_run_report"], rows, list(rows[0]))
    _assert_blocked_without_outputs(paths, "dry_run_report_status_passed")


def test_index_output_and_forbidden_artifact_blockers_do_not_create_outputs(tmp_path):
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
    paths["design_root"].mkdir(parents=True)
    schema, plan, report, manifest, code = _run(paths)
    assert code == 1
    assert schema == []
    assert plan == []
    assert report == []
    assert manifest == {}
    assert not paths["design_manifest"].exists()
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked_without_outputs(paths, "forbidden_training_tensors_absent")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.tgz").write_text("bad", encoding="utf-8")
    _assert_blocked_without_outputs(paths, "forbidden_archives_absent")


def test_static_source_avoids_disallowed_runtime_terms():
    script = Path(__file__).resolve().parents[1] / "scripts" / "apply_training_tensor_design_review.py"
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
