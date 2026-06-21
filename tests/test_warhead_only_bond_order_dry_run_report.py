from pathlib import Path
import csv
import hashlib
import sys

from rdkit import Chem


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_warhead_only_bond_order_dry_run_report import (
    build_dry_run_rows,
    write_report,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mol_from_bonds(bonds: list[tuple[int, int, Chem.BondType]]) -> Chem.Mol:
    mol = Chem.RWMol()
    for _ in range(5):
        mol.AddAtom(Chem.Atom("C"))
    for begin, end, bond_type in bonds:
        mol.AddBond(begin, end, bond_type)
    result = mol.GetMol()
    Chem.SanitizeMol(result)
    return result


def write_sdf(path: Path, mol: Chem.Mol) -> None:
    writer = Chem.SDWriter(str(path))
    writer.write(mol)
    writer.close()


def write_manifest(path: Path, ligand_sdf: Path) -> None:
    fieldnames = ["sample_id", "ligand_sdf_path"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({"sample_id": "toy", "ligand_sdf_path": str(ligand_sdf)})


def write_draft(path: Path) -> None:
    fieldnames = [
        "sample_id",
        "extracted_atom_id",
        "reference_candidate_atom_id",
        "final_role",
        "is_reactive_atom",
        "local_review_reason",
        "manual_decision",
    ]
    rows = [
        ("0", "warhead", "accept_candidate", "warhead_atom"),
        ("1", "warhead", "accept_candidate", "warhead_atom"),
        ("2", "linker", "unresolved", "low_confidence_warhead_or_linker"),
        ("4", "warhead", "accept_candidate", "warhead_atom"),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for atom_id, role, decision, reason in rows:
            writer.writerow(
                {
                    "sample_id": "toy",
                    "extracted_atom_id": atom_id,
                    "reference_candidate_atom_id": atom_id,
                    "final_role": role,
                    "is_reactive_atom": "false",
                    "local_review_reason": reason,
                    "manual_decision": decision,
                }
            )


def test_warhead_only_dry_run_actions_without_modifying_inputs(tmp_path, monkeypatch):
    extracted_sdf = tmp_path / "toy_extracted.sdf"
    reference_sdf = tmp_path / "toy_reference.sdf"
    manifest = tmp_path / "manifest.csv"
    draft = tmp_path / "draft.csv"
    output_csv = tmp_path / "dry_run.csv"

    extracted = mol_from_bonds(
        [
            (0, 1, Chem.BondType.SINGLE),  # accepted warhead; ref differs.
            (1, 2, Chem.BondType.SINGLE),  # touches unresolved boundary.
            (0, 3, Chem.BondType.SINGLE),  # endpoint not accepted.
            (0, 4, Chem.BondType.SINGLE),  # accepted warhead; missing ref bond.
        ]
    )
    reference = mol_from_bonds([(0, 1, Chem.BondType.DOUBLE)])
    write_sdf(extracted_sdf, extracted)
    write_sdf(reference_sdf, reference)
    write_manifest(manifest, extracted_sdf)
    write_draft(draft)

    before_hashes = {
        extracted_sdf: sha256(extracted_sdf),
        reference_sdf: sha256(reference_sdf),
        manifest: sha256(manifest),
        draft: sha256(draft),
    }

    monkeypatch.setattr(
        "build_warhead_only_bond_order_dry_run_report.sample_reference_sdf",
        lambda sample_id, manifest_row: reference_sdf,
    )
    rows = build_dry_run_rows(manifest_csv=manifest, decision_drafts=[draft])
    write_report(rows, output_csv)

    assert output_csv.exists()
    for path, before_hash in before_hashes.items():
        assert sha256(path) == before_hash
    assert not list(tmp_path.glob("*repaired*.sdf"))
    assert not list(tmp_path.glob("*pre_reaction*.sdf"))

    by_bond = {
        (row["bond_endpoint_a"], row["bond_endpoint_b"]): (row["proposed_action"], row["safety_decision"])
        for row in rows
    }
    assert by_bond[("0", "1")] == ("would_transfer_in_warhead_only_scope", "eligible")
    assert by_bond[("1", "2")] == ("blocked_touches_unresolved_boundary", "blocked")
    assert by_bond[("0", "3")] == ("blocked_atom_not_accepted", "blocked")
    assert by_bond[("0", "4")] == ("blocked_missing_reference_bond", "blocked")
