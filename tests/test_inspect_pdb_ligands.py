from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_PREFIX = [
    "/home/fmx_25111030037/bin/micromamba",
    "run",
    "-r",
    "/home/fmx_25111030037/micromamba",
    "-n",
    "covdiff",
    "python",
]


def test_inspect_pdb_ligands_runs_on_5f2e():
    result = subprocess.run(
        [
            *RUN_PREFIX,
            "scripts/inspect_pdb_ligands.py",
            "--protein_pdb",
            "data/raw/covalent_small/proteins/KRAS_G12C_5F2E.pdb",
        ],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert "HETATM residues:" in result.stdout
    assert "LINK records:" in result.stdout
    assert "CONECT records:" in result.stdout
    assert "5UT" in result.stdout
    assert "CYS12/SG" in result.stdout
