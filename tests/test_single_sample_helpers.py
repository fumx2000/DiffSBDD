from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/home/fmx_25111030037/bin/micromamba"
RUN_PREFIX = [
    PYTHON,
    "run",
    "-r",
    "/home/fmx_25111030037/micromamba",
    "-n",
    "covdiff",
    "python",
]


def run_script(*args):
    return subprocess.run(
        [*RUN_PREFIX, *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def test_print_ligand_atom_indices_runs_on_example_sdf():
    result = run_script(
        "scripts/print_ligand_atom_indices.py",
        "--ligand_sdf",
        "example/3rfm_B_CFF.sdf",
    )
    assert "atoms: 14" in result.stdout
    assert "0 N" in result.stdout
    assert "13 C" in result.stdout


def test_print_pdb_residue_atoms_runs_on_existing_residue():
    result = run_script(
        "scripts/print_pdb_residue_atoms.py",
        "--protein_pdb",
        "example/3rfm.pdb",
        "--chain",
        "A",
        "--residue_id",
        "7",
    )
    assert "residue: A:7 SER" in result.stdout
    assert " CA " in result.stdout or "\nCA " in result.stdout
