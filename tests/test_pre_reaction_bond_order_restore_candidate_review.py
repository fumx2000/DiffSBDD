from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_pre_reaction_bond_order_restore_candidate_review import (
    build_candidate_rows,
    parse_v2000_bonds,
    write_csv,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_toy_sdf(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "toy",
                "  test",
                "",
                "  6  5  0  0  0  0            999 V2000",
                "    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                "    1.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                "    2.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                "    3.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0",
                "    4.0000    0.0000    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0",
                "    5.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                "  1  2  1  0",
                "  2  3  1  0",
                "  3  4  2  0",
                "  4  5  1  0",
                "  5  6  1  0",
                "M  END",
                "$$$$",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_parse_v2000_bonds_reads_bond_block(tmp_path: Path) -> None:
    sdf_path = tmp_path / "toy_sample_warhead_only_repaired_trial.sdf"
    _write_toy_sdf(sdf_path)

    assert parse_v2000_bonds(sdf_path) == [
        (0, 1, "1"),
        (1, 2, "1"),
        (2, 3, "2"),
        (3, 4, "1"),
        (4, 5, "1"),
    ]


def test_candidate_review_only_uses_accepted_warhead_internal_bonds(tmp_path: Path) -> None:
    decision_csv = tmp_path / "decision.csv"
    sdf_path = tmp_path / "toy_sample_warhead_only_repaired_trial.sdf"
    output_csv = tmp_path / "review.csv"
    _write_toy_sdf(sdf_path)
    _write_csv(
        decision_csv,
        [
            {
                "sample_id": "toy_sample",
                "warhead_type": "toy",
                "ligand_reactive_atom_candidate": "2",
                "accepted_warhead_atoms": "1 2 3 4",
                "unresolved_boundary_atoms": "5",
                "proposed_covalent_bond_to_remove_candidate": "CYS:SG-2",
                "proposed_bond_order_to_restore_candidate": "",
                "proposed_atoms_requiring_charge_check": "2",
                "proposed_atoms_requiring_valence_check": "1 2 3 4",
                "boundary_resolution_required": "true",
                "manual_covalent_bond_to_remove": "",
                "manual_bond_order_to_restore": "",
                "manual_atoms_requiring_charge_check": "",
                "manual_atoms_requiring_valence_check": "",
                "manual_boundary_resolution": "",
                "reviewer_decision": "",
                "reviewer_note": "",
                "review_status": "draft_not_reviewed",
                "requires_manual_review": "true",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "decision_source": "test",
            }
        ],
    )
    decision_hash = _sha256(decision_csv)
    sdf_hash = _sha256(sdf_path)

    rows = build_candidate_rows(decision_csv=decision_csv, sdf_paths=[sdf_path])
    write_csv(rows, output_csv)

    by_bond = {row["candidate_bond"]: row for row in rows}
    assert set(by_bond) == {"1-2", "2-3", "3-4"}
    assert by_bond["1-2"]["candidate_priority"] == "high"
    assert by_bond["2-3"]["candidate_priority"] == "high"
    assert by_bond["3-4"]["candidate_priority"] == "medium"
    assert {row["proposed_restore_bond_order"] for row in rows} == {"double_candidate"}
    assert {row["requires_manual_review"] for row in rows} == {"true"}
    assert {row["review_status"] for row in rows} == {"draft_not_reviewed"}
    assert _sha256(decision_csv) == decision_hash
    assert _sha256(sdf_path) == sdf_hash
    assert not list(tmp_path.glob("*pre*reaction*.sdf"))
