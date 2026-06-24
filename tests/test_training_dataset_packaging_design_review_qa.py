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

from apply_training_dataset_packaging_design_review import (  # noqa: E402
    PLANNED_PACKAGING_RECORD_FIELDS,
    PLANNED_PACKAGING_DESIGN_ROOT,
)
from check_training_dataset_packaging_design_review_qa import run  # noqa: E402
from test_apply_training_dataset_packaging_design_review import _make_fixture as _make_packaging_fixture, _run as _run_packaging  # noqa: E402
from test_training_dataset_design_gate import _read_csv, _write_csv  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _args(paths):
    root = Path(PLANNED_PACKAGING_DESIGN_ROOT)
    return argparse.Namespace(
        packaging_design_manifest_json=paths["packaging_design_manifest"],
        packaging_file_plan_csv=paths["packaging_file_plan"],
        packaging_schema_report_csv=paths["packaging_schema_report"],
        packaging_design_report_csv=paths["packaging_design_report"],
        training_dataset_packaging_design_gate_plan_csv=paths["packaging_gate_plan"],
        training_dataset_packaging_design_gate_report_csv=paths["packaging_gate_report"],
        training_dataset_design_review_qa_report_csv=paths["design_qa_report"],
        design_manifest_json=paths["design_manifest"],
        schema_report_csv=paths["schema_report"],
        split_plan_csv=paths["split_plan"],
        design_report_csv=paths["design_report"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_report_csv=root / "training_dataset_packaging_design_review_qa_report.csv",
        output_md=paths["packaging_design_summary"].parent / "training_dataset_packaging_design_review_qa_summary.md",
    )


def _make_fixture(tmp_path):
    paths = _make_packaging_fixture(tmp_path)
    report, file_plan, manifest, schema, code = _run_packaging(paths)
    assert code == 0
    assert len(report) == 3
    assert len(file_plan) == 23
    assert manifest["row_count"] == 3
    assert set(PLANNED_PACKAGING_RECORD_FIELDS).issubset({row["field_name"] for row in schema})
    paths["packaging_qa_report"] = Path(PLANNED_PACKAGING_DESIGN_ROOT) / "training_dataset_packaging_design_review_qa_report.csv"
    paths["packaging_qa_summary"] = paths["packaging_design_summary"].parent / "training_dataset_packaging_design_review_qa_summary.md"
    return paths


def _run(paths):
    return run(_args(paths))


def _assert_blocked(paths, reason):
    rows, code = _run(paths)
    assert code == 1
    assert len(rows) == 3
    assert any(row["training_dataset_packaging_design_review_qa_status"] == "blocked" for row in rows)
    assert any(reason in row["blocking_reasons"] for row in rows)


def test_success_outputs_three_passed_qa_rows_without_modifying_inputs(tmp_path):
    paths = _make_fixture(tmp_path)
    input_hashes = {
        key: _sha(paths[key])
        for key in [
            "packaging_design_manifest",
            "packaging_file_plan",
            "packaging_schema_report",
            "packaging_design_report",
            "packaging_gate_plan",
            "packaging_gate_report",
            "design_qa_report",
            "design_manifest",
            "schema_report",
            "split_plan",
            "design_report",
            "index",
            "dataset_manifest",
            "raw_manifest",
        ]
    }
    rows, code = _run(paths)
    assert code == 0
    assert len(rows) == 3
    assert len(_read_csv(paths["packaging_qa_report"])) == 3
    assert all(row["training_dataset_packaging_design_review_qa_status"] == "training_dataset_packaging_design_review_qa_passed" for row in rows)
    assert all(row["packaging_design_manifest_valid"] == "true" for row in rows)
    assert all(row["packaging_manifest_file_roles_valid"] == "true" for row in rows)
    assert all(row["packaging_manifest_record_fields_valid"] == "true" for row in rows)
    assert all(row["packaging_file_plan_row_count_valid"] == "true" for row in rows)
    assert all(row["candidate_file_plan_rows_valid"] == "true" for row in rows)
    assert all(row["candidate_file_plan_hashes_valid"] == "true" for row in rows)
    assert all(row["candidate_file_plan_reference_only_flags_valid"] == "true" for row in rows)
    assert all(row["global_artifact_file_plan_rows_valid"] == "true" for row in rows)
    assert all(row["global_artifact_file_plan_hashes_valid"] == "true" for row in rows)
    assert all(row["packaging_schema_report_fields_valid"] == "true" for row in rows)
    assert all(row["packaging_design_report_status_passed"] == "true" for row in rows)
    assert all(row["only_allowed_packaging_design_files_created"] == "true" for row in rows)
    assert all(row["no_real_training_dataset_created"] == "true" for row in rows)
    assert all(row["no_training_tensors_created"] == "true" for row in rows)
    assert all(row["torch_imported"] == "false" for row in rows)
    assert all(row["checkpoint_loaded"] == "false" for row in rows)
    assert all(row["model_initialized"] == "false" for row in rows)
    assert all(row["dataloader_tensor_generated"] == "false" for row in rows)
    assert all(row["files_copied"] == "false" for row in rows)
    assert all(row["archive_created"] == "false" for row in rows)
    assert all(row["real_training_tensor_generated"] == "false" for row in rows)
    assert all(row["real_dataset_generated"] == "false" for row in rows)
    assert all(row["training_ready"] == "false" for row in rows)
    assert "Training Dataset Packaging Design Review QA Summary" in paths["packaging_qa_summary"].read_text(encoding="utf-8")
    for key, before in input_hashes.items():
        assert _sha(paths[key]) == before


def test_manifest_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    paths["packaging_design_manifest"].unlink()
    _assert_blocked(paths, "packaging_design_manifest_parseable")
    paths = _make_fixture(tmp_path)
    paths["packaging_design_manifest"].write_text("{bad", encoding="utf-8")
    _assert_blocked(paths, "packaging_design_manifest_parseable")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["packaging_design_manifest"].read_text(encoding="utf-8"))
    manifest["row_count"] = 4
    paths["packaging_design_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "packaging_design_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["packaging_design_manifest"].read_text(encoding="utf-8"))
    manifest["planned_packaging_file_roles"] = ["packaged_protein"]
    paths["packaging_design_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "packaging_manifest_file_roles_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["packaging_design_manifest"].read_text(encoding="utf-8"))
    manifest["planned_packaging_record_fields"] = ["sample_id"]
    paths["packaging_design_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "packaging_manifest_record_fields_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["packaging_design_manifest"].read_text(encoding="utf-8"))
    manifest["supported_mask_levels"] = ["A_warhead_only"]
    paths["packaging_design_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "packaging_manifest_mask_levels_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["packaging_design_manifest"].read_text(encoding="utf-8"))
    manifest["required_auxiliary_labels"] = ["warhead_type"]
    paths["packaging_design_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "packaging_manifest_auxiliary_labels_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["packaging_design_manifest"].read_text(encoding="utf-8"))
    manifest["safety_flags"]["real_dataset_generated"] = True
    paths["packaging_design_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "packaging_manifest_safety_flags_valid")


def test_file_plan_schema_and_report_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_file_plan"])
    _write_csv(paths["packaging_file_plan"], rows[:22], list(rows[0]))
    _assert_blocked(paths, "packaging_file_plan_row_count_valid")
    paths = _make_fixture(tmp_path)
    rows = [row for row in _read_csv(paths["packaging_file_plan"]) if not (row["candidate_id"] == "BTK_C481_6DI9_pre_reaction" and row["file_role"] == "source_ligand_sdf")]
    _write_csv(paths["packaging_file_plan"], rows, list(rows[0]))
    _assert_blocked(paths, "candidate_file_plan_rows_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_file_plan"])
    rows[0]["source_file_sha256"] = "bad"
    _write_csv(paths["packaging_file_plan"], rows, list(rows[0]))
    _assert_blocked(paths, "candidate_file_plan_hashes_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_file_plan"])
    rows[0]["training_tensor"] = "true"
    _write_csv(paths["packaging_file_plan"], rows, list(rows[0]))
    _assert_blocked(paths, "candidate_file_plan_reference_only_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = [row for row in _read_csv(paths["packaging_file_plan"]) if row["row_type"] != "global_artifact" or row["file_role"] != "raw_manifest_csv"]
    _write_csv(paths["packaging_file_plan"], rows, list(rows[0]))
    _assert_blocked(paths, "global_artifact_file_plan_rows_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_file_plan"])
    for row in rows:
        if row["row_type"] == "global_artifact":
            row["source_file_sha256"] = "bad"
            break
    _write_csv(paths["packaging_file_plan"], rows, list(rows[0]))
    _assert_blocked(paths, "global_artifact_file_plan_hashes_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_schema_report"])
    _write_csv(paths["packaging_schema_report"], rows[:-1], list(rows[0]))
    _assert_blocked(paths, "packaging_schema_report_fields_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_schema_report"])
    rows[0]["generated_now"] = "true"
    _write_csv(paths["packaging_schema_report"], rows, list(rows[0]))
    _assert_blocked(paths, "packaging_schema_report_fields_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_design_report"])
    rows[0]["training_dataset_packaging_design_status"] = "blocked"
    _write_csv(paths["packaging_design_report"], rows, list(rows[0]))
    _assert_blocked(paths, "packaging_design_report_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_design_report"])
    rows[0]["training_ready"] = "true"
    _write_csv(paths["packaging_design_report"], rows, list(rows[0]))
    _assert_blocked(paths, "packaging_design_report_safety_flags_valid")


def test_upstream_index_package_and_forbidden_artifact_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_gate_report"])
    rows[0]["training_dataset_packaging_design_gate_status"] = "blocked"
    _write_csv(paths["packaging_gate_report"], rows, list(rows[0]))
    _assert_blocked(paths, "upstream_packaging_design_gate_status_still_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["design_qa_report"])
    rows[0]["training_dataset_design_review_qa_status"] = "blocked"
    _write_csv(paths["design_qa_report"], rows, list(rows[0]))
    _assert_blocked(paths, "upstream_training_dataset_design_review_qa_status_still_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    Path(rows[0]["packaged_ligand_sdf_path"]).write_text("changed\n$$$$\n", encoding="utf-8")
    _assert_blocked(paths, "packaged_hashes_still_match_index_and_manifest")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["raw_manifest"])
    rows[1]["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["raw_manifest"], rows, list(rows[0]))
    _assert_blocked(paths, "manifest_paths_match_index_sources")
    paths = _make_fixture(tmp_path)
    (Path(PLANNED_PACKAGING_DESIGN_ROOT) / "bad.sdf").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "only_allowed_packaging_design_files_created")
    paths = _make_fixture(tmp_path)
    (Path(PLANNED_PACKAGING_DESIGN_ROOT) / "bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "only_allowed_packaging_design_files_created")
    paths = _make_fixture(tmp_path)
    tensor = Path("data/derived/covalent_small/bad.lmdb")
    tensor.parent.mkdir(parents=True, exist_ok=True)
    tensor.write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "no_training_tensors_created")
    paths = _make_fixture(tmp_path)
    archive = Path("data/derived/covalent_small/bad.zip")
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "no_archive_created")


def test_script_has_no_disallowed_runtime_calls():
    source = Path(__file__).resolve().parents[1] / "scripts" / "check_training_dataset_packaging_design_review_qa.py"
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
