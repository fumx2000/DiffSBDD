#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


REPORT_COLUMNS = [
    "sample_id",
    "warhead_type",
    "ligand_reactive_atom_candidate",
    "accepted_warhead_atoms",
    "unresolved_boundary_atoms",
    "covalent_bond_to_remove_candidate",
    "bond_order_to_restore_candidate",
    "atoms_requiring_charge_check_candidate",
    "atoms_requiring_valence_check_candidate",
    "requires_manual_review",
    "review_status",
    "reviewer_decision",
    "training_ready_candidate",
    "pre_reaction_graph_ready",
    "can_attempt_transform",
    "proposed_action",
    "dry_run_status",
    "blocking_reasons",
    "recommended_next_action",
]

BLOCKED_NEXT_ACTION = "manual_review_required_before_pre_reaction_transform"
ELIGIBLE_NEXT_ACTION = "ready_for_future_transform_checker_no_sdf_generation"


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def blocking_reasons(row: dict[str, str]) -> list[str]:
    reasons: list[str] = []
    if parse_bool(row.get("requires_manual_review", "")):
        reasons.append("requires_manual_review_true")
    if row.get("review_status", "") != "reviewed":
        reasons.append("review_status_not_reviewed")
    if row.get("reviewer_decision", "") != "approved":
        reasons.append("reviewer_decision_missing")
    if not row.get("ligand_reactive_atom_candidate", ""):
        reasons.append("ligand_reactive_atom_candidate_missing")
    if not row.get("covalent_bond_to_remove_candidate", ""):
        reasons.append("covalent_bond_to_remove_candidate_missing")
    if not row.get("bond_order_to_restore_candidate", ""):
        reasons.append("bond_order_to_restore_candidate_missing")
    if row.get("training_ready_candidate", "") != "false":
        reasons.append("training_ready_candidate_not_false")
    if row.get("pre_reaction_graph_ready", "") != "false":
        reasons.append("pre_reaction_graph_ready_not_false")
    if row.get("unresolved_boundary_atoms", ""):
        reasons.append("unresolved_boundary_atoms_present")
    return reasons


def check_row(row: dict[str, str]) -> dict[str, str]:
    reasons = blocking_reasons(row)
    can_attempt_transform = len(reasons) == 0
    if can_attempt_transform:
        proposed_action = "dry_run_only_ready_for_future_transform_check"
        dry_run_status = "eligible_for_future_checker_only"
        recommended_next_action = ELIGIBLE_NEXT_ACTION
    else:
        missing_rule = any(
            reason in reasons
            for reason in {
                "covalent_bond_to_remove_candidate_missing",
                "bond_order_to_restore_candidate_missing",
                "ligand_reactive_atom_candidate_missing",
            }
        )
        proposed_action = "blocked_missing_required_transform_rule" if missing_rule else "blocked_needs_manual_review"
        dry_run_status = "blocked"
        recommended_next_action = BLOCKED_NEXT_ACTION
    return {
        "sample_id": row["sample_id"],
        "warhead_type": row["warhead_type"],
        "ligand_reactive_atom_candidate": row["ligand_reactive_atom_candidate"],
        "accepted_warhead_atoms": row["accepted_warhead_atoms"],
        "unresolved_boundary_atoms": row["unresolved_boundary_atoms"],
        "covalent_bond_to_remove_candidate": row["covalent_bond_to_remove_candidate"],
        "bond_order_to_restore_candidate": row["bond_order_to_restore_candidate"],
        "atoms_requiring_charge_check_candidate": row["atoms_requiring_charge_check_candidate"],
        "atoms_requiring_valence_check_candidate": row["atoms_requiring_valence_check_candidate"],
        "requires_manual_review": row["requires_manual_review"],
        "review_status": row["review_status"],
        "reviewer_decision": row["reviewer_decision"],
        "training_ready_candidate": row["training_ready_candidate"],
        "pre_reaction_graph_ready": row["pre_reaction_graph_ready"],
        "can_attempt_transform": str(can_attempt_transform).lower(),
        "proposed_action": proposed_action,
        "dry_run_status": dry_run_status,
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": recommended_next_action,
    }


def build_report_rows(manual_review_csv: str | Path) -> list[dict[str, str]]:
    return [check_row(row) for row in read_csv(manual_review_csv)]


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Transform Dry-Run Summary",
        "",
        "This is a dry-run checker only.",
        "",
        "- It does not create pre-reaction SDF files.",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not modify manifest files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | can_attempt_transform | dry_run_status | proposed_action | blocking_reasons |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["can_attempt_transform"],
                    row["dry_run_status"],
                    row["proposed_action"],
                    row["blocking_reasons"],
                ]
            )
            + " |"
        )
    all_blocked = all(row["dry_run_status"] == "blocked" for row in rows)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- No pre-reaction SDF was generated.",
            f"- All current samples remain blocked: {str(all_blocked).lower()}.",
            "- Manual review is required before transform.",
            "- Do not use any sample for training yet.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a dry-run checker for pre-reaction transform readiness.")
    parser.add_argument("--manual_review_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command is a dry-run checker only.")
    print("warning: it does not generate pre-reaction SDF files.")
    print("warning: it does not modify raw or repaired trial SDF files.")
    rows = build_report_rows(args.manual_review_csv)
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote pre-reaction transform dry-run report: {args.output_csv}")
    print(f"wrote pre-reaction transform dry-run summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"can_attempt_transform={row['can_attempt_transform']} "
            f"dry_run_status={row['dry_run_status']} "
            f"blocking_reasons={row['blocking_reasons']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
