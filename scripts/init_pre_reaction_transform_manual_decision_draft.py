#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


DECISION_COLUMNS = [
    "sample_id",
    "warhead_type",
    "ligand_reactive_atom_candidate",
    "accepted_warhead_atoms",
    "unresolved_boundary_atoms",
    "proposed_covalent_bond_to_remove_candidate",
    "proposed_bond_order_to_restore_candidate",
    "proposed_atoms_requiring_charge_check",
    "proposed_atoms_requiring_valence_check",
    "boundary_resolution_required",
    "manual_covalent_bond_to_remove",
    "manual_bond_order_to_restore",
    "manual_atoms_requiring_charge_check",
    "manual_atoms_requiring_valence_check",
    "manual_boundary_resolution",
    "reviewer_decision",
    "reviewer_note",
    "review_status",
    "requires_manual_review",
    "pre_reaction_transform_ready",
    "training_ready",
    "decision_source",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_reviewer_note(boundary_resolution_required: bool) -> str:
    notes = [
        "draft_only_no_transform_performed",
        "proposed_covalent_bond_requires_manual_confirmation",
        "requires_manual_warhead_bond_order_identification",
        "no_pre_reaction_sdf_generated",
        "not_training_ready",
    ]
    if boundary_resolution_required:
        notes.append("unresolved_boundary_requires_manual_resolution")
    return ";".join(notes)


def proposed_covalent_bond(ligand_reactive_atom: str) -> str:
    if not ligand_reactive_atom:
        return ""
    return f"CYS:SG-{ligand_reactive_atom}"


def build_decision_rows(
    *,
    readiness_csv: str | Path,
    manual_review_csv: str | Path,
) -> list[dict[str, str]]:
    readiness_rows = {row["sample_id"]: row for row in read_csv(readiness_csv)}
    manual_rows = {row["sample_id"]: row for row in read_csv(manual_review_csv)}
    rows: list[dict[str, str]] = []
    for sample_id in sorted(manual_rows):
        if sample_id not in readiness_rows:
            raise ValueError(f"sample_id missing from readiness summary: {sample_id}")
        readiness = readiness_rows[sample_id]
        manual = manual_rows[sample_id]
        boundary_resolution_required = bool(manual["unresolved_boundary_atoms"])
        rows.append(
            {
                "sample_id": sample_id,
                "warhead_type": manual["warhead_type"],
                "ligand_reactive_atom_candidate": manual["ligand_reactive_atom_candidate"],
                "accepted_warhead_atoms": manual["accepted_warhead_atoms"],
                "unresolved_boundary_atoms": manual["unresolved_boundary_atoms"],
                "proposed_covalent_bond_to_remove_candidate": proposed_covalent_bond(
                    manual["ligand_reactive_atom_candidate"]
                ),
                "proposed_bond_order_to_restore_candidate": "",
                "proposed_atoms_requiring_charge_check": manual["ligand_reactive_atom_candidate"],
                "proposed_atoms_requiring_valence_check": manual["accepted_warhead_atoms"],
                "boundary_resolution_required": str(boundary_resolution_required).lower(),
                "manual_covalent_bond_to_remove": "",
                "manual_bond_order_to_restore": "",
                "manual_atoms_requiring_charge_check": "",
                "manual_atoms_requiring_valence_check": "",
                "manual_boundary_resolution": "",
                "reviewer_decision": "",
                "reviewer_note": build_reviewer_note(boundary_resolution_required),
                "review_status": "draft_not_reviewed",
                "requires_manual_review": "true",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "decision_source": "pre_reaction_transform_readiness_summary",
            }
        )
        if readiness.get("training_ready", "") != "false":
            raise ValueError(f"readiness summary unexpectedly marks training_ready for {sample_id}")
    return rows


def write_decision_rows(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISION_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize pre-reaction transform manual decision draft.")
    parser.add_argument("--readiness_csv", type=Path, required=True)
    parser.add_argument("--manual_review_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command initializes a manual decision draft only.")
    print("warning: it does not generate pre-reaction SDF files.")
    print("warning: it does not modify raw or repaired trial SDF files.")
    rows = build_decision_rows(readiness_csv=args.readiness_csv, manual_review_csv=args.manual_review_csv)
    write_decision_rows(rows, args.output_csv)
    print(f"wrote pre-reaction transform manual decision draft: {args.output_csv}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"proposed_covalent_bond_to_remove_candidate={row['proposed_covalent_bond_to_remove_candidate']} "
            f"boundary_resolution_required={row['boundary_resolution_required']} "
            f"pre_reaction_transform_ready={row['pre_reaction_transform_ready']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
