from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import pytest
from rdkit import Chem
from rdkit.Geometry import Point3D

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_warhead_only_bond_order_trial import apply_trial, build_markdown, write_markdown, write_report


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_toy_sdf(path: Path) -> None:
    mol = Chem.RWMol()
    for _ in range(5):
        mol.AddAtom(Chem.Atom("C"))
    mol.AddBond(0, 1, Chem.BondType.SINGLE)
    mol.AddBond(1, 2, Chem.BondType.SINGLE)
    mol.AddBond(0, 3, Chem.BondType.SINGLE)
    mol.AddBond(3, 4, Chem.BondType.SINGLE)
    out = mol.GetMol()
    conf = Chem.Conformer(out.GetNumAtoms())
    for idx in range(out.GetNumAtoms()):
        conf.SetAtomPosition(idx, Point3D(float(idx), float(idx % 2), 0.0))
    out.AddConformer(conf)
    writer = Chem.SDWriter(str(path))
    writer.write(out)
    writer.close()


def _bond_type(path: Path, atom_a: int, atom_b: int) -> Chem.BondType:
    mol = Chem.SDMolSupplier(str(path), removeHs=False, sanitize=False)[0]
    return mol.GetBondBetweenAtoms(atom_a, atom_b).GetBondType()


def _manifest(path: Path, raw_sdf: Path) -> None:
    _write_csv(path, [{"sample_id": "toy", "ligand_sdf_path": str(raw_sdf)}])


def _dry_run_rows() -> list[dict[str, str]]:
    return [
        {
            "sample_id": "toy",
            "bond_endpoint_a": "0",
            "bond_endpoint_b": "1",
            "extracted_old_bond_type": "single",
            "reference_candidate_bond_type": "double",
            "both_atoms_accepted_warhead": "true",
            "touches_unresolved_boundary": "false",
            "proposed_action": "would_transfer_in_warhead_only_scope",
            "safety_decision": "eligible",
            "rationale": "allowed local transfer",
        },
        {
            "sample_id": "toy",
            "bond_endpoint_a": "1",
            "bond_endpoint_b": "2",
            "extracted_old_bond_type": "single",
            "reference_candidate_bond_type": "single",
            "both_atoms_accepted_warhead": "true",
            "touches_unresolved_boundary": "false",
            "proposed_action": "keep",
            "safety_decision": "eligible",
            "rationale": "already matches",
        },
        {
            "sample_id": "toy",
            "bond_endpoint_a": "0",
            "bond_endpoint_b": "3",
            "extracted_old_bond_type": "single",
            "reference_candidate_bond_type": "",
            "both_atoms_accepted_warhead": "false",
            "touches_unresolved_boundary": "false",
            "proposed_action": "blocked_atom_not_accepted",
            "safety_decision": "blocked",
            "rationale": "outside scope",
        },
    ]


def test_warhead_only_trial_transfers_only_allowed_bonds(tmp_path: Path) -> None:
    raw_sdf = tmp_path / "raw.sdf"
    manifest_csv = tmp_path / "manifest.csv"
    dry_run_csv = tmp_path / "dry_run.csv"
    output_dir = tmp_path / "derived"
    report_csv = tmp_path / "report.csv"
    summary_md = tmp_path / "summary.md"
    _write_toy_sdf(raw_sdf)
    _manifest(manifest_csv, raw_sdf)
    _write_csv(dry_run_csv, _dry_run_rows())
    raw_hash_before = _sha256(raw_sdf)
    manifest_hash_before = _sha256(manifest_csv)

    rows = apply_trial(manifest_csv=manifest_csv, dry_run_csv=dry_run_csv, output_sdf_dir=output_dir)
    write_report(rows, report_csv)
    write_markdown(build_markdown(rows), summary_md)

    output_sdf = output_dir / "toy_warhead_only_repaired_trial.sdf"
    assert output_sdf.exists()
    assert _bond_type(output_sdf, 0, 1) == Chem.BondType.DOUBLE
    assert _bond_type(output_sdf, 1, 2) == Chem.BondType.SINGLE
    assert _bond_type(output_sdf, 0, 3) == Chem.BondType.SINGLE
    assert _bond_type(raw_sdf, 0, 1) == Chem.BondType.SINGLE
    assert _sha256(raw_sdf) == raw_hash_before
    assert _sha256(manifest_csv) == manifest_hash_before
    assert not list(tmp_path.rglob("*pre*reaction*.sdf"))

    actions = [row["action_applied"] for row in rows]
    assert actions == ["transferred", "kept", "blocked"]
    assert {row["coordinate_hash_same"] for row in rows} == {"true"}
    assert {row["raw_sdf_hash_same"] for row in rows} == {"true"}


def test_warhead_only_trial_rejects_eligible_boundary_touch(tmp_path: Path) -> None:
    raw_sdf = tmp_path / "raw.sdf"
    manifest_csv = tmp_path / "manifest.csv"
    dry_run_csv = tmp_path / "dry_run.csv"
    output_dir = tmp_path / "derived"
    _write_toy_sdf(raw_sdf)
    _manifest(manifest_csv, raw_sdf)
    rows = _dry_run_rows()
    rows[0]["touches_unresolved_boundary"] = "true"
    _write_csv(dry_run_csv, rows)
    raw_hash_before = _sha256(raw_sdf)
    manifest_hash_before = _sha256(manifest_csv)

    with pytest.raises(ValueError, match="touches unresolved boundary"):
        apply_trial(manifest_csv=manifest_csv, dry_run_csv=dry_run_csv, output_sdf_dir=output_dir)

    assert _sha256(raw_sdf) == raw_hash_before
    assert _sha256(manifest_csv) == manifest_hash_before
    assert not output_dir.exists()
