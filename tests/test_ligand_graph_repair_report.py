from pathlib import Path
import csv
import hashlib
import sys

from rdkit import Chem


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_ligand_graph_repair_report import CONFIDENCE_VALUES, REPORT_COLUMNS, build_report_rows, write_report


def write_sdf(path: Path) -> None:
    mol = Chem.MolFromSmiles("CCO")
    mol = Chem.AddHs(mol)
    writer = Chem.SDWriter(str(path))
    writer.write(mol)
    writer.close()


def write_mapping_csv(path: Path) -> None:
    fieldnames = ["sdf_atom_index", "pdb_atom_name", "element", "x", "y", "z"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for atom_idx, element in enumerate(["C", "C", "O", "H", "H", "H", "H", "H", "H"]):
            writer.writerow(
                {
                    "sdf_atom_index": atom_idx,
                    "pdb_atom_name": f"{element}{atom_idx}",
                    "element": element,
                    "x": "0.0",
                    "y": "0.0",
                    "z": "0.0",
                }
            )


def write_annotation_csv(path: Path) -> None:
    fieldnames = ["sdf_atom_index", "pdb_atom_name", "final_role", "notes"]
    roles = {
        0: "scaffold",
        1: "linker",
        2: "warhead",
    }
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for atom_idx in range(9):
            writer.writerow(
                {
                    "sdf_atom_index": atom_idx,
                    "pdb_atom_name": f"A{atom_idx}",
                    "final_role": roles.get(atom_idx, "unassigned"),
                    "notes": "",
                }
            )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_graph_repair_report_outputs_required_columns_without_modifying_sdf(tmp_path):
    extracted_sdf = tmp_path / "extracted.sdf"
    reference_sdf = tmp_path / "reference.sdf"
    mapping_csv = tmp_path / "mapping.csv"
    annotation_csv = tmp_path / "annotation.csv"
    output_csv = tmp_path / "report.csv"

    write_sdf(extracted_sdf)
    write_sdf(reference_sdf)
    write_mapping_csv(mapping_csv)
    write_annotation_csv(annotation_csv)
    before_hash = sha256(extracted_sdf)

    rows = build_report_rows(
        sample_id="toy",
        extracted_sdf=extracted_sdf,
        reference_sdf=reference_sdf,
        mapping_csv=mapping_csv,
        annotation=annotation_csv,
        reactive_atom_id=2,
    )
    write_report(rows, output_csv)

    assert sha256(extracted_sdf) == before_hash
    assert output_csv.exists()

    with output_csv.open("r", encoding="utf-8", newline="") as handle:
        parsed_rows = list(csv.DictReader(handle))

    assert parsed_rows
    assert set(REPORT_COLUMNS).issubset(parsed_rows[0])
    assert {row["mapping_confidence"] for row in parsed_rows}.issubset(CONFIDENCE_VALUES)

    reactive_rows = [row for row in parsed_rows if row["extracted_atom_id"] == "2"]
    assert len(reactive_rows) == 1
    assert reactive_rows[0]["is_reactive_atom"] == "true"
    assert reactive_rows[0]["mapping_confidence"] in CONFIDENCE_VALUES
