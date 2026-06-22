#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


PROPOSAL_COLUMNS = [
    "sample_id",
    "ligand_reactive_atom_candidate",
    "accepted_warhead_atoms",
    "unresolved_boundary_atoms",
    "proposed_manual_covalent_bond_to_remove",
    "selected_bond_order_candidate",
    "proposed_manual_bond_order_to_restore",
    "high_priority_candidate_count",
    "all_candidate_bonds",
    "all_high_priority_candidate_bonds",
    "proposed_manual_boundary_resolution",
    "requires_boundary_manual_confirmation",
    "proposal_status",
    "reviewer_decision",
    "reviewer_note",
    "review_status",
    "requires_manual_review",
    "can_write_back_to_decision_draft",
    "pre_reaction_transform_ready",
    "training_ready",
    "decision_source",
]

DECISION_SOURCE = "pre_reaction_bond_order_restore_candidate_review"
PROPOSAL_STATUS = "proposal_only_not_approved"
REVIEWER_NOTE_BASE = [
    "proposal_only_no_decision_written",
    "manual_confirmation_required",
    "no_pre_reaction_sdf_generated",
    "not_training_ready",
    "no_raw_or_repaired_sdf_modified",
]
BOUNDARY_RESOLUTION = "reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate"


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def high_priority_candidates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("candidate_priority", "") == "high"
        and row.get("candidate_reason", "") == "touches_ligand_reactive_atom_candidate"
        and row.get("proposed_restore_bond_order", "") == "double_candidate"
    ]


def build_proposal_rows(
    *,
    decision_csv: str | Path,
    bond_candidate_csv: str | Path,
) -> list[dict[str, str]]:
    decision_rows = read_csv(decision_csv)
    candidate_rows = read_csv(bond_candidate_csv)
    candidates_by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidate_rows:
        candidates_by_sample[row["sample_id"]].append(row)

    output_rows: list[dict[str, str]] = []
    for decision in sorted(decision_rows, key=lambda row: row["sample_id"]):
        sample_id = decision["sample_id"]
        sample_candidates = sorted(candidates_by_sample.get(sample_id, []), key=lambda row: row["candidate_bond"])
        high_candidates = high_priority_candidates(sample_candidates)
        reviewer_notes = list(REVIEWER_NOTE_BASE)

        selected_bond = ""
        proposed_restore = ""
        if len(high_candidates) == 1:
            selected_bond = high_candidates[0]["candidate_bond"]
            proposed_restore = f"{selected_bond}:double"
        else:
            reviewer_notes.append("high_priority_candidate_ambiguous")

        unresolved_boundary_atoms = decision.get("unresolved_boundary_atoms", "")
        output_rows.append(
            {
                "sample_id": sample_id,
                "ligand_reactive_atom_candidate": decision.get("ligand_reactive_atom_candidate", ""),
                "accepted_warhead_atoms": decision.get("accepted_warhead_atoms", ""),
                "unresolved_boundary_atoms": unresolved_boundary_atoms,
                "proposed_manual_covalent_bond_to_remove": decision.get(
                    "proposed_covalent_bond_to_remove_candidate", ""
                ),
                "selected_bond_order_candidate": selected_bond,
                "proposed_manual_bond_order_to_restore": proposed_restore,
                "high_priority_candidate_count": str(len(high_candidates)),
                "all_candidate_bonds": " ".join(row["candidate_bond"] for row in sample_candidates),
                "all_high_priority_candidate_bonds": " ".join(row["candidate_bond"] for row in high_candidates),
                "proposed_manual_boundary_resolution": BOUNDARY_RESOLUTION if unresolved_boundary_atoms else "",
                "requires_boundary_manual_confirmation": str(bool(unresolved_boundary_atoms)).lower(),
                "proposal_status": PROPOSAL_STATUS,
                "reviewer_decision": "",
                "reviewer_note": ";".join(reviewer_notes),
                "review_status": "draft_not_reviewed",
                "requires_manual_review": "true",
                "can_write_back_to_decision_draft": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "decision_source": DECISION_SOURCE,
            }
        )
    return output_rows


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROPOSAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Transform Manual Decision Proposal",
        "",
        "This is a proposal only.",
        "",
        "- It does not write back to decision draft files.",
        "- It does not create pre-reaction SDF files.",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | proposed_manual_covalent_bond_to_remove | selected_bond_order_candidate | proposed_manual_bond_order_to_restore | high_priority_candidate_count | proposal_status | can_write_back_to_decision_draft |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["proposed_manual_covalent_bond_to_remove"],
                    row["selected_bond_order_candidate"],
                    row["proposed_manual_bond_order_to_restore"],
                    row["high_priority_candidate_count"],
                    row["proposal_status"],
                    row["can_write_back_to_decision_draft"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- These proposals require manual confirmation before any write-back.",
            "- No decisions were written to the manual decision draft.",
            "- No pre-reaction SDF was generated.",
            "- No sample is training-ready.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build pre-reaction transform manual decision proposal.")
    parser.add_argument("--decision_csv", type=Path, required=True)
    parser.add_argument("--bond_candidate_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command writes a proposal only.")
    print("warning: it does not write back to decision draft files.")
    print("warning: it does not generate pre-reaction SDF files.")
    rows = build_proposal_rows(decision_csv=args.decision_csv, bond_candidate_csv=args.bond_candidate_csv)
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote pre-reaction transform manual decision proposal CSV: {args.output_csv}")
    print(f"wrote pre-reaction transform manual decision proposal Markdown: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"covalent_bond_to_remove={row['proposed_manual_covalent_bond_to_remove']} "
            f"selected_bond_order_candidate={row['selected_bond_order_candidate']} "
            f"proposed_bond_order_to_restore={row['proposed_manual_bond_order_to_restore']} "
            f"proposal_status={row['proposal_status']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
