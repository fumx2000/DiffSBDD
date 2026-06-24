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

from apply_read_only_training_dataset_loader_dry_run import T_FIELD  # noqa: E402
from check_training_tensor_design_review_qa import run  # noqa: E402
from test_apply_training_tensor_design_review import _make_fixture as _make_design_fixture, _run as _run_design  # noqa: E402
from test_training_dataset_design_gate import _read_csv, _write_csv  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _args(paths):
    return argparse.Namespace(
        training_tensor_design_manifest_json=paths["design_manifest"],
        training_tensor_design_schema_report_csv=paths["schema_report"],
        training_tensor_design_plan_csv=paths["design_plan"],
        training_tensor_design_report_csv=paths["design_report"],
        training_tensor_design_summary_md=paths["design_summary"],
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
        output_report_csv=paths["design_root"] / "training_tensor_design_review_qa_report.csv",
        output_md=Path("docs/training_tensor_design_review_qa_summary.md"),
    )


def _make_fixture(tmp_path):
    paths = _make_design_fixture(tmp_path)
    schema, plan, report, manifest, code = _run_design(paths)
    assert code == 0
    assert len(schema) == 47
    assert len(plan) == 3
    assert len(report) == 3
    assert manifest["row_count"] == 3
    paths["qa_report"] = paths["design_root"] / "training_tensor_design_review_qa_report.csv"
    paths["qa_summary"] = Path("docs/training_tensor_design_review_qa_summary.md")
    return paths


def _run(paths):
    return run(_args(paths))


def _write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _assert_blocked(paths, reason):
    rows, code = _run(paths)
    assert code == 1
    assert len(rows) == 3
    assert len(_read_csv(paths["qa_report"])) == 3
    assert any(row["training_tensor_design_review_qa_status"] == "blocked" for row in rows)
    assert any(reason in row["blocking_reasons"] for row in rows)


def test_success_outputs_three_passed_rows_without_modifying_inputs(tmp_path):
    paths = _make_fixture(tmp_path)
    protected = [
        "design_manifest",
        "schema_report",
        "design_plan",
        "design_report",
        "design_summary",
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
    rows, code = _run(paths)
    assert code == 0
    assert len(rows) == 3
    assert len(_read_csv(paths["qa_report"])) == 3
    assert paths["qa_summary"].is_file()
    assert all(row["training_tensor_design_review_qa_status"] == "training_tensor_design_review_qa_passed" for row in rows)
    assert all(row["design_manifest_valid"] == "true" for row in rows)
    assert all(row["design_manifest_safety_flags_valid"] == "true" for row in rows)
    assert all(row["schema_report_row_count_valid"] == "true" for row in rows)
    assert all(row["schema_report_required_fields_present"] == "true" for row in rows)
    assert all(row["schema_report_mask_fields_present"] == "true" for row in rows)
    assert all(row["schema_report_auxiliary_fields_present"] == "true" for row in rows)
    assert all(row["schema_report_no_tensor_generated"] == "true" for row in rows)
    assert all(row["design_plan_status_valid"] == "true" for row in rows)
    assert all(row["design_report_status_passed"] == "true" for row in rows)
    assert all(row["design_report_safety_flags_valid"] == "true" for row in rows)
    assert all(row["upstream_tensor_design_gate_status_still_passed"] == "true" for row in rows)
    assert all(row["upstream_loader_dry_run_qa_status_still_passed"] == "true" for row in rows)
    assert all(row["upstream_dry_run_manifest_still_valid"] == "true" for row in rows)
    assert all(row["upstream_dry_run_report_still_passed"] == "true" for row in rows)
    assert all(row["real_training_dataset_package_still_valid"] == "true" for row in rows)
    assert all(row["only_allowed_design_files_created"] == "true" for row in rows)
    assert all(row["no_data_files_copied"] == "true" for row in rows)
    assert all(row["no_archive_created"] == "true" for row in rows)
    assert all(row["no_training_tensors_created"] == "true" for row in rows)
    assert all(row["tensor_schema_generated"] == "true" for row in rows)
    assert all(row["tensor_files_generated"] == "false" for row in rows)
    assert all(row["dataloader_tensor_generated"] == "false" for row in rows)
    assert all(row[T_FIELD] == "false" for row in rows)
    assert all(row["checkpoint_loaded"] == "false" for row in rows)
    assert all(row["model_initialized"] == "false" for row in rows)
    assert all(row["training_ready"] == "false" for row in rows)
    assert all(row["copied_file_count"] == "0" for row in rows)
    assert {path.name for path in paths["design_root"].iterdir()} == {
        "training_tensor_design_manifest.json",
        "training_tensor_design_schema_report.csv",
        "training_tensor_design_plan.csv",
        "training_tensor_design_report.csv",
        "training_tensor_design_review_qa_report.csv",
    }
    for key, before in input_hashes.items():
        assert _sha(paths[key]) == before


def test_manifest_and_schema_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    paths["design_manifest"].unlink()
    _assert_blocked(paths, "design_manifest_parseable")
    paths = _make_fixture(tmp_path)
    paths["design_manifest"].write_text("{bad", encoding="utf-8")
    _assert_blocked(paths, "design_manifest_parseable")
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
    manifest["safety_flags"][T_FIELD] = True
    _write_json(paths["design_manifest"], manifest)
    _assert_blocked(paths, "design_manifest_safety_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["schema_report"])
    _write_csv(paths["schema_report"], rows[:46], list(rows[0]))
    _assert_blocked(paths, "schema_report_row_count_valid")
    paths = _make_fixture(tmp_path)
    rows = [row for row in _read_csv(paths["schema_report"]) if row["field_name"] != "sample_id"]
    _write_csv(paths["schema_report"], rows, list(rows[0]))
    _assert_blocked(paths, "schema_report_required_fields_present")
    paths = _make_fixture(tmp_path)
    rows = [row for row in _read_csv(paths["schema_report"]) if row["field_name"] != "generation_mask_A_warhead_only"]
    _write_csv(paths["schema_report"], rows, list(rows[0]))
    _assert_blocked(paths, "schema_report_mask_fields_present")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["schema_report"])
    rows[0]["tensor_generated"] = "true"
    _write_csv(paths["schema_report"], rows, list(rows[0]))
    _assert_blocked(paths, "schema_report_no_tensor_generated")


def test_plan_report_and_upstream_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_plan"])
    rows[0]["tensor_files_generated"] = "true"
    _write_csv(paths["design_plan"], rows, list(rows[0]))
    _assert_blocked(paths, "design_plan_status_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_report"])
    rows[0]["training_tensor_design_status"] = "blocked"
    _write_csv(paths["design_report"], rows, list(rows[0]))
    _assert_blocked(paths, "design_report_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_report"])
    rows[0][T_FIELD] = "true"
    _write_csv(paths["design_report"], rows, list(rows[0]))
    _assert_blocked(paths, "design_report_safety_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["tensor_gate_report"])
    rows[0]["training_tensor_design_gate_status"] = "blocked"
    _write_csv(paths["tensor_gate_report"], rows, list(rows[0]))
    _assert_blocked(paths, "upstream_tensor_design_gate_status_still_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["dry_run_qa_report"])
    rows[0]["read_only_training_dataset_loader_dry_run_qa_status"] = "blocked"
    _write_csv(paths["dry_run_qa_report"], rows, list(rows[0]))
    _assert_blocked(paths, "upstream_loader_dry_run_qa_status_still_passed")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["dry_run_manifest"].read_text(encoding="utf-8"))
    manifest["row_count"] = 2
    _write_json(paths["dry_run_manifest"], manifest)
    _assert_blocked(paths, "upstream_dry_run_manifest_still_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["dry_run_report"])
    rows[0]["loader_dry_run_status"] = "blocked"
    _write_csv(paths["dry_run_report"], rows, list(rows[0]))
    _assert_blocked(paths, "upstream_dry_run_report_still_passed")


def test_index_design_root_and_forbidden_artifact_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    Path(_read_csv(paths["index"])[0]["packaged_ligand_sdf_path"]).write_text("changed\n$$$$\n", encoding="utf-8")
    _assert_blocked(paths, "packaged_hashes_still_match_index_and_manifest")
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
    (paths["design_root"] / "bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "only_allowed_design_files_created")
    paths = _make_fixture(tmp_path)
    (paths["design_root"] / "copied_metadata.json").write_text("{}", encoding="utf-8")
    _assert_blocked(paths, "no_data_files_copied")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "no_training_tensors_created")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.tgz").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "no_archive_created")


def test_static_source_avoids_disallowed_runtime_terms():
    script = Path(__file__).resolve().parents[1] / "scripts" / "check_training_tensor_design_review_qa.py"
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
