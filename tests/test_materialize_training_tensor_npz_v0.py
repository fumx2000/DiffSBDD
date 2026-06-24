import csv
import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from materialize_training_tensor_npz_v0 import NPZ_KEYS, OUTPUT_ROOT, run  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _fixture_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = REPO_ROOT / "data" / "derived" / "covalent_small"
    target = tmp_path / "data" / "derived" / "covalent_small"
    shutil.copytree(source, target)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _args():
    return argparse.Namespace(
        materialization_review_manifest_json="data/derived/covalent_small/training_tensor_materialization_review_only/training_tensor_materialization_manifest.json",
        materialization_plan_csv="data/derived/covalent_small/training_tensor_materialization_review_only/training_tensor_materialization_plan.csv",
        materialization_file_plan_csv="data/derived/covalent_small/training_tensor_materialization_review_only/training_tensor_materialization_file_plan.csv",
        index_csv="data/derived/covalent_small/dataset_index_review_only/covalent_small_pre_reaction_review_only_index.csv",
        dataset_manifest_json="data/derived/covalent_small/dataset_index_review_only/covalent_small_pre_reaction_review_only_manifest.json",
    )


def test_materializes_three_loadable_npz_files_with_expected_keys_and_shapes():
    assert run(_args()) == 0
    sample_rows = _read_csv(OUTPUT_ROOT / "sample_index.csv")
    report_rows = _read_csv(OUTPUT_ROOT / "materialization_report.csv")
    sanity_rows = _read_csv(OUTPUT_ROOT / "sanity_report.csv")
    assert len(sample_rows) == 3
    assert len(report_rows) == 3
    assert len(sanity_rows) == 3
    assert all(row["sanity_status"] == "passed" for row in sanity_rows)
    for row in sample_rows:
        npz_path = Path(row["npz_path"])
        assert npz_path.is_file()
        with np.load(npz_path, allow_pickle=False) as data:
            assert set(NPZ_KEYS).issubset(data.files)
            ligand_count = int(row["ligand_atom_count"])
            protein_count = int(row["protein_atom_count"])
            assert data["ligand_atom_coords"].shape == (ligand_count, 3)
            assert data["ligand_atomic_numbers"].shape == (ligand_count,)
            assert data["ligand_bond_index"].shape[0] == 2
            assert data["ligand_bond_type"].shape == (data["ligand_bond_index"].shape[1],)
            assert data["protein_atom_coords"].shape == (protein_count, 3)
            assert data["protein_atomic_numbers"].shape == (protein_count,)
            assert data["protein_residue_ids"].shape == (protein_count,)
            assert data["protein_chain_ids"].shape == (protein_count,)
            for key in [
                "scaffold_atom_mask",
                "linker_atom_mask",
                "warhead_atom_mask",
                "generation_mask_A_warhead_only",
                "generation_mask_B_linker_warhead",
                "generation_mask_B2_scaffold_warhead",
                "generation_mask_C_scaffold_linker_warhead",
            ]:
                assert data[key].shape == (ligand_count,)
                assert data[key].dtype == np.bool_
            reactive_idx = int(data["ligand_reactive_atom_index"])
            assert 0 <= reactive_idx < ligand_count
            assert bool(data["warhead_atom_mask"][reactive_idx])
            assert np.isfinite(data["ligand_atom_coords"]).all()
            assert np.isfinite(data["protein_atom_coords"]).all()


def test_manifest_and_reports_have_expected_counts_and_no_other_binary_artifacts():
    assert run(_args()) == 0
    import json

    manifest = json.loads((OUTPUT_ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["row_count"] == 3
    assert manifest["sample_index_row_count"] == 3
    assert manifest["materialization_report_row_count"] == 3
    assert manifest["sanity_report_row_count"] == 3
    assert len(list((OUTPUT_ROOT / "samples").glob("*.npz"))) == 3
    assert not list(OUTPUT_ROOT.rglob("*.pt"))
    assert not list(OUTPUT_ROOT.rglob("*.pkl"))
    assert not list(OUTPUT_ROOT.rglob("*.lmdb"))
    assert not list(OUTPUT_ROOT.rglob("*.tar"))
    assert not list(OUTPUT_ROOT.rglob("*.zip"))
    assert not list(OUTPUT_ROOT.rglob("*.tgz"))


def test_static_source_avoids_disallowed_runtime_terms():
    script = REPO_ROOT / "scripts" / "materialize_training_tensor_npz_v0.py"
    sources = [script, Path(__file__)]
    for source in sources:
        text = source.read_text(encoding="utf-8")
        assert ("tor" + "ch") not in text
        assert ("Data" + "Loader") not in text
        assert ("Data" + "set") not in text
