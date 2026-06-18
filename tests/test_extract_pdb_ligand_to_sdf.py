from pathlib import Path
import csv
import sys

from rdkit import Chem


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from check_ligand_mapping import find_mapping
from extract_pdb_ligand_to_sdf import extract_ligand_to_sdf


PDB_PATH = REPO_ROOT / "data/raw/covalent_small/proteins/KRAS_G12C_5F2E.pdb"


def test_extract_5f2e_5ut_to_sdf_and_mapping(tmp_path):
    output_sdf = tmp_path / "KRAS_G12C_5F2E_5UT.sdf"
    output_mapping = tmp_path / "KRAS_G12C_5F2E_5UT_atom_mapping.csv"
    atom_count, bond_count = extract_ligand_to_sdf(
        protein_pdb=PDB_PATH,
        ligand_resname="5UT",
        chain="A",
        residue_id=204,
        output_sdf=output_sdf,
        output_mapping_csv=output_mapping,
    )

    assert atom_count == 30
    assert bond_count > 0
    assert output_sdf.exists()
    assert output_mapping.exists()

    mol = Chem.SDMolSupplier(str(output_sdf), sanitize=False)[0]
    assert mol is not None
    assert mol.GetNumAtoms() == 30

    with output_mapping.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 30
    c15_rows = [row for row in rows if row["pdb_atom_name"] == "C15"]
    assert len(c15_rows) == 1
    assert int(c15_rows[0]["sdf_atom_index"]) >= 0

    matches = find_mapping(output_mapping, "C15")
    assert len(matches) == 1
    assert matches[0]["pdb_atom_name"] == "C15"
