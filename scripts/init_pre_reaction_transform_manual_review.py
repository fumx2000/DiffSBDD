#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


REVIEW_COLUMNS = [
    "sample_id",
    "warhead_type",
    "residue_name",
    "residue_atom",
    "ligand_reactive_atom_candidate",
    "accepted_warhead_atoms",
    "unresolved_boundary_atoms",
    "covalent_bond_to_remove_candidate",
    "bond_order_to_restore_candidate",
    "atoms_requiring_charge_check_candidate",
    "atoms_requiring_valence_check_candidate",
    "protonation_note",
    "geometry_note",
    "confidence_level",
    "requires_manual_review",
    "review_status",
    "reviewer_decision",
    "reviewer_note",
    "training_ready_candidate",
    "pre_reaction_graph_ready",
    "rule_source",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def atom_sort_key(atom_id: str) -> tuple[int, str]:
    try:
        return (int(atom_id), atom_id)
    except ValueError:
        return (10**9, atom_id)


def load_decision_rows(paths: list[Path]) -> dict[str, list[dict[str, str]]]:
    rows_by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path in paths:
        for row in read_csv(path):
            rows_by_sample[row["sample_id"]].append(row)
    return dict(rows_by_sample)


def is_unresolved_boundary(row: dict[str, str]) -> bool:
    final_role = row.get("final_role", "")
    reason = row.get("local_review_reason", "")
    return row.get("manual_decision", "") == "unresolved" and (
        final_role in {"linker", "boundary"} or "low_confidence_warhead_or_linker" in reason
    )


def build_reviewer_note(
    *,
    reactive_atom_ambiguous: bool,
    unresolved_boundary_atoms: list[str],
) -> str:
    notes = [
        "template_only_no_transform_performed",
        "no_pre_reaction_sdf_generated",
        "requires_manual_review_protein_ligand_covalent_bond",
        "requires_manual_review_warhead_electrophile_restore_rule",
        "requires_manual_review_before_transform",
    ]
    if reactive_atom_ambiguous:
        notes.append("requires_manual_review_reactive_atom_ambiguous")
    if unresolved_boundary_atoms:
        notes.append("unresolved_boundary_present")
    return ";".join(notes)


def summarize_decision_rows(rows: list[dict[str, str]]) -> dict[str, str]:
    reactive_candidates = sorted(
        {
            row["extracted_atom_id"]
            for row in rows
            if parse_bool(row.get("is_reactive_atom", "")) and row.get("manual_decision", "") == "accept_candidate"
        },
        key=atom_sort_key,
    )
    accepted_warhead_atoms = sorted(
        {
            row["extracted_atom_id"]
            for row in rows
            if row.get("final_role", "") == "warhead" and row.get("manual_decision", "") == "accept_candidate"
        },
        key=atom_sort_key,
    )
    unresolved_boundary_atoms = sorted(
        {row["extracted_atom_id"] for row in rows if is_unresolved_boundary(row)},
        key=atom_sort_key,
    )
    reactive_atom_ambiguous = len(reactive_candidates) != 1
    ligand_reactive_atom_candidate = reactive_candidates[0] if len(reactive_candidates) == 1 else ""
    return {
        "ligand_reactive_atom_candidate": ligand_reactive_atom_candidate,
        "accepted_warhead_atoms": " ".join(accepted_warhead_atoms),
        "unresolved_boundary_atoms": " ".join(unresolved_boundary_atoms),
        "atoms_requiring_charge_check_candidate": ligand_reactive_atom_candidate,
        "atoms_requiring_valence_check_candidate": " ".join(accepted_warhead_atoms),
        "reviewer_note": build_reviewer_note(
            reactive_atom_ambiguous=reactive_atom_ambiguous,
            unresolved_boundary_atoms=unresolved_boundary_atoms,
        ),
    }


def build_review_rows(
    *,
    rule_template_csv: str | Path,
    manual_decision_drafts: list[Path],
) -> list[dict[str, str]]:
    template_rows = read_csv(rule_template_csv)
    decisions_by_sample = load_decision_rows(manual_decision_drafts)
    review_rows: list[dict[str, str]] = []
    for template in sorted(template_rows, key=lambda row: row["sample_id"]):
        sample_id = template["sample_id"]
        if sample_id not in decisions_by_sample:
            raise ValueError(f"sample_id missing from manual decision drafts: {sample_id}")
        decision_summary = summarize_decision_rows(decisions_by_sample[sample_id])
        review_rows.append(
            {
                "sample_id": sample_id,
                "warhead_type": template["warhead_type"],
                "residue_name": template["residue_name"],
                "residue_atom": template["residue_atom"],
                "ligand_reactive_atom_candidate": decision_summary["ligand_reactive_atom_candidate"],
                "accepted_warhead_atoms": decision_summary["accepted_warhead_atoms"],
                "unresolved_boundary_atoms": decision_summary["unresolved_boundary_atoms"],
                "covalent_bond_to_remove_candidate": "",
                "bond_order_to_restore_candidate": "",
                "atoms_requiring_charge_check_candidate": decision_summary["atoms_requiring_charge_check_candidate"],
                "atoms_requiring_valence_check_candidate": decision_summary["atoms_requiring_valence_check_candidate"],
                "protonation_note": template["protonation_note"],
                "geometry_note": template["geometry_note"],
                "confidence_level": template["confidence_level"],
                "requires_manual_review": template["requires_manual_review"],
                "review_status": "draft_not_reviewed",
                "reviewer_decision": "",
                "reviewer_note": decision_summary["reviewer_note"],
                "training_ready_candidate": template["training_ready_candidate"],
                "pre_reaction_graph_ready": template["pre_reaction_graph_ready"],
                "rule_source": template["rule_source"],
            }
        )
    return review_rows


def write_review(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize pre-reaction transform manual review draft.")
    parser.add_argument("--rule_template_csv", type=Path, required=True)
    parser.add_argument("--manual_decision_drafts", type=Path, nargs="+", required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command initializes a manual review draft only.")
    print("warning: it does not generate pre-reaction SDF files.")
    print("warning: it does not modify raw or repaired trial SDF files.")
    rows = build_review_rows(
        rule_template_csv=args.rule_template_csv,
        manual_decision_drafts=args.manual_decision_drafts,
    )
    write_review(rows, args.output_csv)
    print(f"wrote pre-reaction transform manual review draft: {args.output_csv}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"ligand_reactive_atom_candidate={row['ligand_reactive_atom_candidate']} "
            f"accepted_warhead_atoms={row['accepted_warhead_atoms']} "
            f"unresolved_boundary_atoms={row['unresolved_boundary_atoms']} "
            f"training_ready_candidate={row['training_ready_candidate']} "
            f"pre_reaction_graph_ready={row['pre_reaction_graph_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
