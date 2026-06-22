from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_post_manifest_dataset_assembly_dry_run import (
    CANDIDATE_COLUMNS,
    REPORT_COLUMNS,
    TARGETS,
    build_dry_run,
    build_markdown,
    write_csv,
    write_markdown,
)


SOURCE_IDS = {
    "BTK_C481_6DI9_pre_reaction": "BTK_C481_6DI9",
    "KRAS_G12C_5F2E_pre_reaction": "KRAS_G12C_5F2E",
    "KRAS_G12C_6OIM_pre_reaction": "KRAS_G12C_6OIM",
}
REACTIVE = {
    "BTK_C481_6DI9_pre_reaction": "19",
    "KRAS_G12C_5F2E_pre_reaction": "29",
    "KRAS_G12C_6OIM_pre_reaction": "7",
}
WARHEAD = {
    "BTK_C481_6DI9_pre_reaction": "17 18 19 32",
    "KRAS_G12C_5F2E_pre_reaction": "8 27 28 29",
    "KRAS_G12C_6OIM_pre_reaction": "4 5 6 7",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _manifest_row(sample_id: str, *, pre: bool = False) -> dict[str, str]:
    pre_id = sample_id if pre else ""
    reactive = REACTIVE.get(pre_id, "1")
    warhead = WARHEAD.get(pre_id, "2")
    ligand = TARGETS[pre_id]["ligand"] if pre else f"ligands/{sample_id}.sdf"
    protein = f"proteins/{SOURCE_IDS.get(pre_id, sample_id)}.pdb"
    Path(ligand).parent.mkdir(parents=True, exist_ok=True)
    Path(protein).parent.mkdir(parents=True, exist_ok=True)
    if pre:
        Path(ligand).write_text("toy sdf\n", encoding="utf-8")
    Path(protein).write_text("toy pdb\n", encoding="utf-8")
    return {
        "sample_id": sample_id,
        "protein_pdb_path": protein,
        "ligand_sdf_path": ligand,
        "reactive_residue_chain": "A",
        "reactive_residue_id": "1",
        "reactive_residue_type": "CYS",
        "reactive_atom_name": "SG",
        "ligand_reactive_atom_id": reactive,
        "warhead_type": "toy",
        "scaffold_atoms": "0 1",
        "linker_atoms": "3",
        "warhead_atoms": warhead,
    }


def _write_inputs(tmp_path: Path) -> dict[str, Path]:
    manifest = tmp_path / "manifest.csv"
    qa = tmp_path / "qa.csv"
    rows: list[dict[str, str]] = []
    for pre_id in sorted(TARGETS):
        rows.append(_manifest_row(SOURCE_IDS[pre_id]))
    for pre_id in sorted(TARGETS):
        rows.append(_manifest_row(pre_id, pre=True))
    qa_rows = [
        {
            "proposed_manifest_sample_id": pre_id,
            "source_sample_id": SOURCE_IDS[pre_id],
            "actual_manifest_update_qa_status": "actual_manifest_update_qa_passed",
            "training_ready": "false",
        }
        for pre_id in sorted(TARGETS)
    ]
    _write_csv(manifest, rows)
    _write_csv(qa, qa_rows)
    return {
        "manifest": manifest,
        "qa": qa,
        "candidates": tmp_path / "candidates.csv",
        "report": tmp_path / "report.csv",
        "summary": tmp_path / "summary.md",
    }


def _run(paths: dict[str, Path]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    return build_dry_run(
        manifest_csv=paths["manifest"],
        actual_manifest_update_qa_report_csv=paths["qa"],
    )


def _mutate_manifest(paths: dict[str, Path], sample_id: str, field: str, value: str) -> None:
    rows = _read_csv(paths["manifest"])
    for row in rows:
        if row["sample_id"] == sample_id:
            row[field] = value
    _write_csv(paths["manifest"], rows)


def _remove_manifest_row(paths: dict[str, Path], sample_id: str) -> None:
    rows = [row for row in _read_csv(paths["manifest"]) if row["sample_id"] != sample_id]
    _write_csv(paths["manifest"], rows)


def test_post_manifest_dataset_assembly_dry_run_passes_three_candidates(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    manifest_hash = _sha256(paths["manifest"])

    reports, candidates = _run(paths)
    write_csv(candidates, paths["candidates"], CANDIDATE_COLUMNS)
    write_csv(reports, paths["report"], REPORT_COLUMNS)
    write_markdown(build_markdown(reports, candidates), paths["summary"])

    candidate_rows = _read_csv(paths["candidates"])
    assert len(candidates) == 3
    assert len(candidate_rows) == 3
    assert {row["dataset_assembly_dry_run_status"] for row in reports} == {
        "post_manifest_dataset_assembly_dry_run_passed"
    }
    assert {row["candidate_id"] for row in candidates} == set(TARGETS)
    assert {row["training_ready"] for row in candidates} == {"false"}
    assert {row["training_ready"] for row in reports} == {"false"}
    assert {row["atom_groups_non_overlapping"] for row in reports} == {"true"}
    assert {row["warhead_contains_ligand_reactive_atom"] for row in reports} == {"true"}
    assert _sha256(paths["manifest"]) == manifest_hash
    assert "Post-Manifest Dataset Assembly Dry-Run Summary" in paths["summary"].read_text(encoding="utf-8")
    assert not list(tmp_path.rglob("*.pt"))
    assert not list(tmp_path.rglob("*.pkl"))
    assert not list(tmp_path.rglob("*.npz"))
    assert not list(tmp_path.rglob("*.lmdb"))


def test_missing_required_manifest_column_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    rows = _read_csv(paths["manifest"])
    fieldnames = [field for field in rows[0] if field != "warhead_atoms"]
    rows = [{key: value for key, value in row.items() if key in fieldnames} for row in rows]
    _write_csv(paths["manifest"], rows, fieldnames)

    reports, candidates = _run(paths)

    assert candidates == []
    assert {row["dataset_assembly_dry_run_status"] for row in reports} == {"blocked"}
    assert all("manifest_required_columns_missing" in row["blocking_reasons"] for row in reports)


def test_missing_pre_reaction_row_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _remove_manifest_row(paths, "BTK_C481_6DI9_pre_reaction")

    reports, _ = _run(paths)

    row = next(row for row in reports if row["pre_reaction_sample_id"] == "BTK_C481_6DI9_pre_reaction")
    assert row["dataset_assembly_dry_run_status"] == "blocked"
    assert "pre_reaction_manifest_row_not_found_once" in row["blocking_reasons"]


def test_missing_source_row_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _remove_manifest_row(paths, "BTK_C481_6DI9")

    reports, _ = _run(paths)

    row = next(row for row in reports if row["pre_reaction_sample_id"] == "BTK_C481_6DI9_pre_reaction")
    assert row["dataset_assembly_dry_run_status"] == "blocked"
    assert "source_manifest_row_not_found_once" in row["blocking_reasons"]


def test_ligand_path_mismatch_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_manifest(paths, "BTK_C481_6DI9_pre_reaction", "ligand_sdf_path", "wrong.sdf")

    reports, _ = _run(paths)

    row = next(row for row in reports if row["pre_reaction_sample_id"] == "BTK_C481_6DI9_pre_reaction")
    assert row["dataset_assembly_dry_run_status"] == "blocked"
    assert "ligand_sdf_path_not_expected" in row["blocking_reasons"]


def test_ligand_sdf_missing_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    Path(TARGETS["BTK_C481_6DI9_pre_reaction"]["ligand"]).unlink()

    reports, _ = _run(paths)

    row = next(row for row in reports if row["pre_reaction_sample_id"] == "BTK_C481_6DI9_pre_reaction")
    assert row["dataset_assembly_dry_run_status"] == "blocked"
    assert "ligand_sdf_missing" in row["blocking_reasons"]


def test_protein_path_empty_or_missing_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_manifest(paths, "BTK_C481_6DI9_pre_reaction", "protein_pdb_path", "")

    reports, _ = _run(paths)

    row = next(row for row in reports if row["pre_reaction_sample_id"] == "BTK_C481_6DI9_pre_reaction")
    assert row["dataset_assembly_dry_run_status"] == "blocked"
    assert "protein_pdb_path_empty" in row["blocking_reasons"]
    assert "protein_pdb_missing" in row["blocking_reasons"]


def test_ligand_reactive_atom_not_integer_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_manifest(paths, "BTK_C481_6DI9_pre_reaction", "ligand_reactive_atom_id", "bad")

    reports, _ = _run(paths)

    row = next(row for row in reports if row["pre_reaction_sample_id"] == "BTK_C481_6DI9_pre_reaction")
    assert row["dataset_assembly_dry_run_status"] == "blocked"
    assert "ligand_reactive_atom_id_missing_or_not_integer" in row["blocking_reasons"]


def test_atom_list_not_parseable_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_manifest(paths, "BTK_C481_6DI9_pre_reaction", "scaffold_atoms", "0 bad")

    reports, _ = _run(paths)

    row = next(row for row in reports if row["pre_reaction_sample_id"] == "BTK_C481_6DI9_pre_reaction")
    assert row["dataset_assembly_dry_run_status"] == "blocked"
    assert "scaffold_atoms_not_parseable" in row["blocking_reasons"]


def test_atom_groups_overlap_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_manifest(paths, "BTK_C481_6DI9_pre_reaction", "linker_atoms", "17")

    reports, _ = _run(paths)

    row = next(row for row in reports if row["pre_reaction_sample_id"] == "BTK_C481_6DI9_pre_reaction")
    assert row["dataset_assembly_dry_run_status"] == "blocked"
    assert "atom_groups_overlap" in row["blocking_reasons"]


def test_warhead_missing_ligand_reactive_atom_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_manifest(paths, "BTK_C481_6DI9_pre_reaction", "warhead_atoms", "17 18 32")

    reports, _ = _run(paths)

    row = next(row for row in reports if row["pre_reaction_sample_id"] == "BTK_C481_6DI9_pre_reaction")
    assert row["dataset_assembly_dry_run_status"] == "blocked"
    assert "warhead_atoms_missing_ligand_reactive_atom" in row["blocking_reasons"]


def test_actual_manifest_update_qa_not_passed_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    qa_rows = _read_csv(paths["qa"])
    qa_rows[0]["actual_manifest_update_qa_status"] = "blocked"
    _write_csv(paths["qa"], qa_rows)

    reports, _ = _run(paths)

    row = next(row for row in reports if row["pre_reaction_sample_id"] == qa_rows[0]["proposed_manifest_sample_id"])
    assert row["dataset_assembly_dry_run_status"] == "blocked"
    assert "actual_manifest_update_qa_not_passed" in row["blocking_reasons"]
