from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from check_manifest_real_small import REQUIRED_COLUMNS, check_manifest, parse_atom_indices


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [",".join(REQUIRED_COLUMNS)]
    for row in rows:
        lines.append(",".join(row.get(column, "") for column in REQUIRED_COLUMNS))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def valid_row(**overrides):
    row = {
        "sample_id": "sample_001",
        "protein_pdb_path": "missing_protein.pdb",
        "ligand_sdf_path": "missing_ligand.sdf",
        "reactive_residue_chain": "A",
        "reactive_residue_id": "145",
        "reactive_residue_type": "CYS",
        "reactive_atom_name": "SG",
        "ligand_reactive_atom_id": "5",
        "warhead_type": "acrylamide",
        "scaffold_atoms": "0 1 2",
        "linker_atoms": "3 4",
        "warhead_atoms": "5 6",
    }
    row.update(overrides)
    return row


def test_empty_template_is_template_ok():
    template = REPO_ROOT / "data/raw/covalent_small/manifests/manifest_real_small_template.csv"
    result = check_manifest(template)
    assert result.ok
    assert result.is_template


def test_mock_manifest_row_parses_with_path_warnings(tmp_path):
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest, [valid_row()])
    result = check_manifest(manifest)
    assert result.ok
    assert result.rows == 1
    assert len(result.warnings) == 2


def test_atom_index_parser_accepts_spaces_and_commas():
    assert parse_atom_indices("0,1,2 3") == [0, 1, 2, 3]


def test_overlapping_atom_indices_are_detected(tmp_path):
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest, [valid_row(linker_atoms="2 3")])
    result = check_manifest(manifest)
    assert not result.ok
    assert any("overlaps" in error for error in result.errors)


def test_ligand_reactive_atom_must_be_in_warhead(tmp_path):
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest, [valid_row(ligand_reactive_atom_id="4")])
    result = check_manifest(manifest)
    assert not result.ok
    assert any("not in warhead_atoms" in error for error in result.errors)
