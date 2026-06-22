#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


SUMMARY_COLUMNS = [
    "sample_id",
    "warhead_type",
    "ligand_reactive_atom_candidate",
    "accepted_warhead_atoms",
    "unresolved_boundary_atoms",
    "requires_manual_review",
    "review_status",
    "reviewer_decision",
    "covalent_bond_to_remove_candidate_present",
    "bond_order_to_restore_candidate_present",
    "can_attempt_transform",
    "dry_run_status",
    "blocking_reasons",
    "pre_reaction_transform_ready",
    "training_ready",
    "recommended_next_action",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def recommended_actions(manual_row: dict[str, str], dry_run_row: dict[str, str]) -> str:
    actions: list[str] = []
    if not parse_bool(dry_run_row.get("can_attempt_transform", "")) and parse_bool(
        manual_row.get("requires_manual_review", "")
    ):
        actions.append("manual_review_required_before_pre_reaction_transform")
    if not manual_row.get("covalent_bond_to_remove_candidate", ""):
        actions.append("add_covalent_bond_to_remove_candidate_after_manual_review")
    if not manual_row.get("bond_order_to_restore_candidate", ""):
        actions.append("add_bond_order_to_restore_candidate_after_manual_review")
    if manual_row.get("unresolved_boundary_atoms", ""):
        actions.append("resolve_boundary_atoms_before_transform")
    if not actions:
        actions.append("ready_for_future_pre_reaction_transform_checker")
    return ";".join(actions)


def build_summary_rows(*, manual_review_csv: str | Path, dry_run_csv: str | Path) -> list[dict[str, str]]:
    manual_rows = {row["sample_id"]: row for row in read_csv(manual_review_csv)}
    dry_rows = {row["sample_id"]: row for row in read_csv(dry_run_csv)}
    rows: list[dict[str, str]] = []
    for sample_id in sorted(manual_rows):
        if sample_id not in dry_rows:
            raise ValueError(f"sample_id missing from dry-run report: {sample_id}")
        manual = manual_rows[sample_id]
        dry = dry_rows[sample_id]
        can_attempt = parse_bool(dry["can_attempt_transform"])
        pre_reaction_transform_ready = (
            can_attempt
            and dry["dry_run_status"] == "eligible_for_future_checker_only"
            and manual.get("review_status", "") == "reviewed"
            and manual.get("reviewer_decision", "") == "approved"
        )
        rows.append(
            {
                "sample_id": sample_id,
                "warhead_type": manual["warhead_type"],
                "ligand_reactive_atom_candidate": manual["ligand_reactive_atom_candidate"],
                "accepted_warhead_atoms": manual["accepted_warhead_atoms"],
                "unresolved_boundary_atoms": manual["unresolved_boundary_atoms"],
                "requires_manual_review": manual["requires_manual_review"],
                "review_status": manual["review_status"],
                "reviewer_decision": manual["reviewer_decision"],
                "covalent_bond_to_remove_candidate_present": str(
                    bool(manual.get("covalent_bond_to_remove_candidate", ""))
                ).lower(),
                "bond_order_to_restore_candidate_present": str(
                    bool(manual.get("bond_order_to_restore_candidate", ""))
                ).lower(),
                "can_attempt_transform": dry["can_attempt_transform"],
                "dry_run_status": dry["dry_run_status"],
                "blocking_reasons": dry["blocking_reasons"],
                "pre_reaction_transform_ready": str(pre_reaction_transform_ready).lower(),
                "training_ready": "false",
                "recommended_next_action": recommended_actions(manual, dry),
            }
        )
    return rows


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Transform Readiness Summary",
        "",
        "This is a readiness summary only.",
        "",
        "- It does not create pre-reaction SDF files.",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not modify manifest files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | pre_reaction_transform_ready | training_ready | can_attempt_transform | dry_run_status | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["pre_reaction_transform_ready"],
                    row["training_ready"],
                    row["can_attempt_transform"],
                    row["dry_run_status"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_blocked = all(row["dry_run_status"] == "blocked" for row in rows)
    any_training_ready = any(parse_bool(row["training_ready"]) for row in rows)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            f"- All current samples remain blocked: {str(all_blocked).lower()}.",
            f"- No sample is training-ready: {str(not any_training_ready).lower()}.",
            "- No pre-reaction SDF was generated.",
            "- Manual review is required before any transform.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize pre-reaction transform readiness.")
    parser.add_argument("--manual_review_csv", type=Path, required=True)
    parser.add_argument("--dry_run_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command writes a readiness summary only.")
    print("warning: it does not generate pre-reaction SDF files.")
    print("warning: it does not modify raw or repaired trial SDF files.")
    rows = build_summary_rows(manual_review_csv=args.manual_review_csv, dry_run_csv=args.dry_run_csv)
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote pre-reaction transform readiness summary: {args.output_csv}")
    print(f"wrote pre-reaction transform readiness Markdown: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"pre_reaction_transform_ready={row['pre_reaction_transform_ready']} "
            f"training_ready={row['training_ready']} "
            f"next={row['recommended_next_action']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
