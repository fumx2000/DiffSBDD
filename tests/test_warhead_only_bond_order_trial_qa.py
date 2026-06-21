from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Geometry import Point3D

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_warhead_only_bond_order_trial import build_markdown, run_qa, write_markdown, write_qa_csv


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_sdf(path: Path, bond_01: Chem.BondType, bond_12: Chem.BondType, bond_03: Chem.BondType) -> None:
    mol = Chem.RWMol()
    for _ in range(4):
        mol.AddAtom(Chem.Atom("C"))
    mol.AddBond(0, 1, bond_01)
    mol.AddBond(1, 2, bond_12)
    mol.AddBond(0, 3, bond_03)
    out = mol.GetMol()
    conf = Chem.Conformer(out.GetNumAtoms())
    for idx in range(out.GetNumAtoms()):
        conf.SetAtomPosition(idx, Point3D(float(idx), 0.0, 0.0))
    out.AddConformer(conf)
    writer = Chem.SDWriter(str(path))
    writer.write(out)
    writer.close()


def _base_report_rows(raw_sdf: Path, repaired_sdf: Path) -> list[dict[str, str]]:
    base = {
        "sample_id": "toy",
        "output_sdf_path": str(repaired_sdf),
        "source_ligand_sdf_path": str(raw_sdf),
        "safety_decision": "eligible",
        "touched_unresolved_boundary": "false",
        "coordinate_hash_before": "coord",
        "coordinate_hash_after": "coord",
        "coordinate_hash_same": "true",
        "raw_sdf_hash_before": "raw",
        "raw_sdf_hash_after": "raw",
        "raw_sdf_hash_same": "true",
        "rationale": "",
    }
    return [
        {
            **base,
            "bond_endpoint_a": "0",
            "bond_endpoint_b": "1",
            "old_bond_type": "single",
            "new_bond_type": "double",
            "action_applied": "transferred",
        },
        {
            **base,
            "bond_endpoint_a": "1",
            "bond_endpoint_b": "2",
            "old_bond_type": "single",
            "new_bond_type": "single",
            "action_applied": "kept",
        },
        {
            **base,
            "bond_endpoint_a": "0",
            "bond_endpoint_b": "3",
            "old_bond_type": "single",
            "new_bond_type": "single",
            "action_applied": "blocked",
            "safety_decision": "blocked",
        },
    ]


def _make_inputs(tmp_path: Path, blocked_bond: Chem.BondType = Chem.BondType.SINGLE) -> tuple[Path, Path, Path, Path]:
    raw_sdf = tmp_path / "raw.sdf"
    repaired_sdf = tmp_path / "toy_warhead_only_repaired_trial.sdf"
    manifest_csv = tmp_path / "manifest.csv"
    trial_report_csv = tmp_path / "trial_report.csv"
    _write_sdf(raw_sdf, Chem.BondType.SINGLE, Chem.BondType.SINGLE, Chem.BondType.SINGLE)
    _write_sdf(repaired_sdf, Chem.BondType.DOUBLE, Chem.BondType.SINGLE, blocked_bond)
    _write_csv(manifest_csv, [{"sample_id": "toy", "ligand_sdf_path": str(raw_sdf)}])
    _write_csv(trial_report_csv, _base_report_rows(raw_sdf, repaired_sdf))
    return raw_sdf, repaired_sdf, manifest_csv, trial_report_csv


def test_warhead_only_trial_qa_passes_expected_actions(tmp_path: Path) -> None:
    raw_sdf, repaired_sdf, manifest_csv, trial_report_csv = _make_inputs(tmp_path)
    output_qa_csv = tmp_path / "qa.csv"
    output_md = tmp_path / "qa.md"
    raw_hash = _sha256(raw_sdf)
    repaired_hash = _sha256(repaired_sdf)
    manifest_hash = _sha256(manifest_csv)

    rows = run_qa(manifest_csv=manifest_csv, trial_report_csv=trial_report_csv)
    write_qa_csv(rows, output_qa_csv)
    write_markdown(build_markdown(rows), output_md)

    assert [row["qa_status"] for row in rows] == ["passed", "passed", "passed"]
    assert [row["bond_change_matches_action"] for row in rows] == ["true", "true", "true"]
    assert _sha256(raw_sdf) == raw_hash
    assert _sha256(repaired_sdf) == repaired_hash
    assert _sha256(manifest_csv) == manifest_hash
    assert not list(tmp_path.rglob("*pre*reaction*.sdf"))


def test_warhead_only_trial_qa_fails_changed_blocked_bond(tmp_path: Path) -> None:
    _, _, manifest_csv, trial_report_csv = _make_inputs(tmp_path, blocked_bond=Chem.BondType.DOUBLE)

    rows = run_qa(manifest_csv=manifest_csv, trial_report_csv=trial_report_csv)

    blocked = rows[2]
    assert blocked["action_applied"] == "blocked"
    assert blocked["qa_status"] == "failed"
    assert "blocked row changed bond type" in blocked["qa_error"]


def test_warhead_only_trial_qa_fails_boundary_touch_not_blocked(tmp_path: Path) -> None:
    _, _, manifest_csv, trial_report_csv = _make_inputs(tmp_path)
    rows = list(csv.DictReader(trial_report_csv.open(newline="", encoding="utf-8")))
    rows[0]["touched_unresolved_boundary"] = "true"
    _write_csv(trial_report_csv, rows)

    qa_rows = run_qa(manifest_csv=manifest_csv, trial_report_csv=trial_report_csv)

    assert qa_rows[0]["qa_status"] == "failed"
    assert "transferred row touches unresolved boundary" in qa_rows[0]["qa_error"]
    assert "boundary-touching row is not blocked" in qa_rows[0]["qa_error"]


def test_warhead_only_trial_qa_fails_hash_flags(tmp_path: Path) -> None:
    _, _, manifest_csv, trial_report_csv = _make_inputs(tmp_path)
    rows = list(csv.DictReader(trial_report_csv.open(newline="", encoding="utf-8")))
    rows[0]["coordinate_hash_same"] = "false"
    rows[1]["raw_sdf_hash_same"] = "false"
    _write_csv(trial_report_csv, rows)

    qa_rows = run_qa(manifest_csv=manifest_csv, trial_report_csv=trial_report_csv)

    assert qa_rows[0]["qa_status"] == "failed"
    assert "coordinate_hash_same is not true" in qa_rows[0]["qa_error"]
    assert qa_rows[1]["qa_status"] == "failed"
    assert "raw_sdf_hash_same is not true" in qa_rows[1]["qa_error"]
