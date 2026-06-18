from pathlib import Path
import csv
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from manifest_row_from_annotation import MANIFEST_COLUMNS, ManifestRowError, build_manifest_row


def write_annotation(path: Path, roles: dict[int, str]) -> None:
    fieldnames = [
        "sdf_atom_index",
        "pdb_atom_name",
        "element",
        "x",
        "y",
        "z",
        "neighbors",
        "suggested_role",
        "final_role",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for atom_idx in range(6):
            writer.writerow(
                {
                    "sdf_atom_index": atom_idx,
                    "pdb_atom_name": f"C{atom_idx}",
                    "element": "C",
                    "x": "0.0",
                    "y": "0.0",
                    "z": "0.0",
                    "neighbors": "",
                    "suggested_role": "",
                    "final_role": roles.get(atom_idx, "unassigned"),
                    "notes": "",
                }
            )


def build_row(annotation: Path, ligand_reactive_atom_id: int = 5) -> dict[str, str]:
    return build_manifest_row(
        sample_id="KRAS_G12C_5F2E",
        protein_pdb_path="data/raw/covalent_small/proteins/KRAS_G12C_5F2E.pdb",
        ligand_sdf_path="data/raw/covalent_small/ligands/KRAS_G12C_5F2E_5UT.sdf",
        annotation=annotation,
        reactive_residue_chain="A",
        reactive_residue_id="12",
        reactive_residue_type="CYS",
        reactive_atom_name="SG",
        ligand_reactive_atom_id=ligand_reactive_atom_id,
        warhead_type="KRAS_G12C_covalent_electrophile_smoke_test",
    )


def test_complete_final_roles_generate_manifest_row(tmp_path):
    annotation = tmp_path / "annotation.csv"
    write_annotation(annotation, {0: "scaffold", 1: "scaffold", 2: "linker", 3: "linker", 4: "warhead", 5: "warhead"})

    row = build_row(annotation)

    assert row["sample_id"] == "KRAS_G12C_5F2E"
    assert row["scaffold_atoms"] == "0 1"
    assert row["linker_atoms"] == "2 3"
    assert row["warhead_atoms"] == "4 5"
    assert set(row) == set(MANIFEST_COLUMNS)


def test_warhead_must_contain_ligand_reactive_atom(tmp_path):
    annotation = tmp_path / "annotation.csv"
    write_annotation(annotation, {0: "scaffold", 1: "linker", 2: "warhead"})

    try:
        build_row(annotation, ligand_reactive_atom_id=5)
    except ManifestRowError as exc:
        assert "not in warhead_atoms" in str(exc)
    else:
        raise AssertionError("expected ManifestRowError")


def test_empty_role_group_fails(tmp_path):
    annotation = tmp_path / "annotation.csv"
    write_annotation(annotation, {0: "scaffold", 1: "scaffold", 2: "warhead"})

    try:
        build_row(annotation, ligand_reactive_atom_id=2)
    except ManifestRowError as exc:
        assert "missing: linker" in str(exc)
    else:
        raise AssertionError("expected ManifestRowError")


def test_cli_outputs_one_csv_row(tmp_path):
    annotation = tmp_path / "annotation.csv"
    write_annotation(annotation, {0: "scaffold", 1: "scaffold", 2: "linker", 3: "warhead", 4: "warhead"})

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "manifest_row_from_annotation.py"),
            "--sample_id",
            "KRAS_G12C_5F2E",
            "--protein_pdb_path",
            "data/raw/covalent_small/proteins/KRAS_G12C_5F2E.pdb",
            "--ligand_sdf_path",
            "data/raw/covalent_small/ligands/KRAS_G12C_5F2E_5UT.sdf",
            "--annotation",
            str(annotation),
            "--reactive_residue_chain",
            "A",
            "--reactive_residue_id",
            "12",
            "--reactive_residue_type",
            "CYS",
            "--reactive_atom_name",
            "SG",
            "--ligand_reactive_atom_id",
            "4",
            "--warhead_type",
            "KRAS_G12C_covalent_electrophile_smoke_test",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    parsed = next(csv.reader([result.stdout.strip()]))
    assert len(parsed) == len(MANIFEST_COLUMNS)
    row = dict(zip(MANIFEST_COLUMNS, parsed))
    assert row["scaffold_atoms"] == "0 1"
    assert row["linker_atoms"] == "2"
    assert row["warhead_atoms"] == "3 4"
