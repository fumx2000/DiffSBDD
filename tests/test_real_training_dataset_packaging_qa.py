import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_real_training_dataset_packaging import PLANNED_REAL_PACKAGE_ROOT  # noqa: E402
from check_real_training_dataset_packaging_qa import PACKAGE_MODE, run  # noqa: E402
from test_apply_real_training_dataset_packaging import _make_fixture as _make_packaging_fixture, _run as _run_packaging  # noqa: E402
from test_training_dataset_design_gate import _read_csv, _write_csv  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _args(paths):
    return argparse.Namespace(
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
        output_report_csv=paths["real_package_root"] / "real_training_dataset_packaging_qa_report.csv",
        output_md=paths["real_packaging_summary"].parent / "real_training_dataset_packaging_qa_summary.md",
    )


def _make_fixture(tmp_path):
    paths = _make_packaging_fixture(tmp_path)
    manifest, file_index, sample_index, report, code = _run_packaging(paths)
    assert code == 0
    assert manifest["row_count"] == 3
    assert len(file_index) == 15
    assert len(sample_index) == 3
    assert len(report) == 3
    paths["real_packaging_qa_report"] = paths["real_package_root"] / "real_training_dataset_packaging_qa_report.csv"
    paths["real_packaging_qa_summary"] = paths["real_packaging_summary"].parent / "real_training_dataset_packaging_qa_summary.md"
    return paths


def _run(paths):
    return run(_args(paths))


def _assert_blocked(paths, reason):
    rows, code = _run(paths)
    assert code == 1
    assert len(rows) == 3
    assert len(_read_csv(paths["real_packaging_qa_report"])) == 3
    assert any(row["real_training_dataset_packaging_qa_status"] == "blocked" for row in rows)
    assert any(reason in row["blocking_reasons"] for row in rows)


def test_success_outputs_three_passed_qa_rows_without_modifying_inputs(tmp_path):
    paths = _make_fixture(tmp_path)
    input_hashes = {
        key: _sha(paths[key])
        for key in [
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
    }
    rows, code = _run(paths)
    assert code == 0
    assert len(rows) == 3
    assert len(_read_csv(paths["real_packaging_qa_report"])) == 3
    assert paths["real_packaging_qa_summary"].is_file()
    assert all(row["real_training_dataset_packaging_qa_status"] == "real_training_dataset_packaging_qa_passed" for row in rows)
    assert all(row["real_training_dataset_manifest_valid"] == "true" for row in rows)
    assert all(row["candidate_file_index_rows_valid"] == "true" for row in rows)
    assert all(row["candidate_file_index_hashes_valid"] == "true" for row in rows)
    assert all(row["candidate_file_index_reference_only_flags_valid"] == "true" for row in rows)
    assert all(row["candidate_sample_index_row_found_once"] == "true" for row in rows)
    assert all(row["candidate_sample_index_reference_only_flags_valid"] == "true" for row in rows)
    assert all(row["real_training_dataset_packaging_report_status_passed"] == "true" for row in rows)
    assert all(row["upstream_real_training_dataset_packaging_gate_status_still_passed"] == "true" for row in rows)
    assert all(row["upstream_packaging_design_review_qa_status_still_passed"] == "true" for row in rows)
    assert all(row["only_allowed_real_package_files_created"] == "true" for row in rows)
    assert all(row["no_data_files_copied"] == "true" for row in rows)
    assert all(row["no_archive_created"] == "true" for row in rows)
    assert all(row["no_training_tensors_created"] == "true" for row in rows)
    assert all(row["real_training_tensor_generated"] == "false" for row in rows)
    assert all(row["real_dataset_generated"] == "false" for row in rows)
    assert all(row["dataloader_tensor_generated"] == "false" for row in rows)
    assert all(row["torch_imported"] == "false" for row in rows)
    assert all(row["checkpoint_loaded"] == "false" for row in rows)
    assert all(row["model_initialized"] == "false" for row in rows)
    assert all(row["training_ready"] == "false" for row in rows)
    assert {path.name for path in paths["real_package_root"].iterdir()} == {
        "real_training_dataset_manifest.json",
        "real_training_dataset_file_index.csv",
        "real_training_dataset_sample_index.csv",
        "real_training_dataset_packaging_report.csv",
        "real_training_dataset_packaging_qa_report.csv",
    }
    for key, before in input_hashes.items():
        assert _sha(paths[key]) == before
    assert "Real Training Dataset Packaging QA Summary" in paths["real_packaging_qa_summary"].read_text(encoding="utf-8")


def test_manifest_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    paths["real_manifest"].unlink()
    _assert_blocked(paths, "real_training_dataset_manifest_parseable")
    paths = _make_fixture(tmp_path)
    paths["real_manifest"].write_text("{bad", encoding="utf-8")
    _assert_blocked(paths, "real_training_dataset_manifest_parseable")
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
    manifest["copied_file_count"] = 1
    paths["real_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "real_training_dataset_manifest_valid")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["real_manifest"].read_text(encoding="utf-8"))
    manifest["safety_flags"]["real_dataset_generated"] = True
    paths["real_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "real_training_dataset_manifest_safety_flags_valid")


def test_file_index_sample_index_and_report_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_file_index"])
    _write_csv(paths["real_file_index"], rows[:14], list(rows[0]))
    _assert_blocked(paths, "real_training_dataset_file_index_row_count_valid")
    paths = _make_fixture(tmp_path)
    rows = [row for row in _read_csv(paths["real_file_index"]) if not (row["sample_id"] == "BTK_C481_6DI9_pre_reaction" and row["file_role"] == "source_ligand_sdf")]
    _write_csv(paths["real_file_index"], rows, list(rows[0]))
    _assert_blocked(paths, "candidate_file_index_rows_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_file_index"])
    rows[0]["source_file_sha256"] = "bad"
    _write_csv(paths["real_file_index"], rows, list(rows[0]))
    _assert_blocked(paths, "candidate_file_index_hashes_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_file_index"])
    rows[0]["copied_to_package"] = "true"
    _write_csv(paths["real_file_index"], rows, list(rows[0]))
    _assert_blocked(paths, "candidate_file_index_reference_only_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_file_index"])
    rows[0]["copied_file_path"] = "copied.pdb"
    _write_csv(paths["real_file_index"], rows, list(rows[0]))
    _assert_blocked(paths, "candidate_file_index_reference_only_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_sample_index"])
    _write_csv(paths["real_sample_index"], rows[:2], list(rows[0]))
    _assert_blocked(paths, "real_training_dataset_sample_index_row_count_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_sample_index"])
    rows[0]["package_mode"] = "copy"
    _write_csv(paths["real_sample_index"], rows, list(rows[0]))
    _assert_blocked(paths, "candidate_sample_index_reference_only_flags_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_packaging_report"])
    rows[0]["training_dataset_status"] = "blocked"
    _write_csv(paths["real_packaging_report"], rows, list(rows[0]))
    _assert_blocked(paths, "real_training_dataset_packaging_report_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_packaging_report"])
    rows[0]["real_training_tensor_generated"] = "true"
    _write_csv(paths["real_packaging_report"], rows, list(rows[0]))
    _assert_blocked(paths, "real_training_dataset_packaging_report_safety_flags_valid")


def test_upstream_index_package_and_forbidden_artifact_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["real_packaging_gate_report"])
    rows[0]["real_training_dataset_packaging_gate_status"] = "blocked"
    _write_csv(paths["real_packaging_gate_report"], rows, list(rows[0]))
    _assert_blocked(paths, "upstream_real_training_dataset_packaging_gate_status_still_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["packaging_qa_report"])
    rows[0]["training_dataset_packaging_design_review_qa_status"] = "blocked"
    _write_csv(paths["packaging_qa_report"], rows, list(rows[0]))
    _assert_blocked(paths, "upstream_packaging_design_review_qa_status_still_passed")
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
    (paths["real_package_root"] / "bad.sdf").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "only_allowed_real_package_files_created")
    paths = _make_fixture(tmp_path)
    (paths["real_package_root"] / "metadata_copy.json").write_text("{}", encoding="utf-8")
    _assert_blocked(paths, "no_data_files_copied")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "no_training_tensors_created")
    paths = _make_fixture(tmp_path)
    Path("data/derived/covalent_small/bad.tgz").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "no_archive_created")


def test_script_has_no_disallowed_runtime_calls():
    source = Path(__file__).resolve().parents[1] / "scripts" / "check_real_training_dataset_packaging_qa.py"
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
    assert Path(PLANNED_REAL_PACKAGE_ROOT).as_posix()
