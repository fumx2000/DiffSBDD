#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


REPORT_COLUMNS = [
    "sample_id",
    "manual_covalent_bond_to_remove",
    "manual_bond_order_to_restore",
    "manual_boundary_resolution",
    "manual_atoms_requiring_charge_check",
    "manual_atoms_requiring_valence_check",
    "reviewer_decision",
    "review_status",
    "requires_manual_review",
    "pre_reaction_transform_ready",
    "training_ready",
    "post_write_back_check_status",
    "eligible_for_future_transform_dry_run_only",
    "blocking_reasons",
    "recommended_next_action",
]

ELIGIBLE_STATUS = "eligible_for_future_transform_dry_run_only"
BLOCKED_STATUS = "blocked"
ELIGIBLE_NEXT_ACTION = "build_pre_reaction_transform_dry_run_next"
BLOCKED_NEXT_ACTION = "fix_manual_write_back_fields_before_dry_run"


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def blocking_reasons(row: dict[str, str]) -> list[str]:
    reasons: list[str] = []
    if not row.get("manual_covalent_bond_to_remove", ""):
        reasons.append("manual_covalent_bond_to_remove_missing")
    if not row.get("manual_bond_order_to_restore", ""):
        reasons.append("manual_bond_order_to_restore_missing")
    if not row.get("manual_boundary_resolution", ""):
        reasons.append("manual_boundary_resolution_missing")
    if not row.get("manual_atoms_requiring_charge_check", ""):
        reasons.append("manual_atoms_requiring_charge_check_missing")
    if not row.get("manual_atoms_requiring_valence_check", ""):
        reasons.append("manual_atoms_requiring_valence_check_missing")
    if row.get("reviewer_decision", "") != "approved":
        reasons.append("reviewer_decision_not_approved")
    if row.get("review_status", "") != "reviewed":
        reasons.append("review_status_not_reviewed")
    if row.get("requires_manual_review", "") != "false":
        reasons.append("requires_manual_review_not_false")
    if row.get("pre_reaction_transform_ready", "") != "false":
        reasons.append("pre_reaction_transform_ready_not_false")
    if row.get("training_ready", "") != "false":
        reasons.append("training_ready_not_false")
    return reasons


def check_row(row: dict[str, str]) -> dict[str, str]:
    reasons = blocking_reasons(row)
    eligible = len(reasons) == 0
    return {
        "sample_id": row["sample_id"],
        "manual_covalent_bond_to_remove": row["manual_covalent_bond_to_remove"],
        "manual_bond_order_to_restore": row["manual_bond_order_to_restore"],
        "manual_boundary_resolution": row["manual_boundary_resolution"],
        "manual_atoms_requiring_charge_check": row["manual_atoms_requiring_charge_check"],
        "manual_atoms_requiring_valence_check": row["manual_atoms_requiring_valence_check"],
        "reviewer_decision": row["reviewer_decision"],
        "review_status": row["review_status"],
        "requires_manual_review": row["requires_manual_review"],
        "pre_reaction_transform_ready": row["pre_reaction_transform_ready"],
        "training_ready": row["training_ready"],
        "post_write_back_check_status": ELIGIBLE_STATUS if eligible else BLOCKED_STATUS,
        "eligible_for_future_transform_dry_run_only": str(eligible).lower(),
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": ELIGIBLE_NEXT_ACTION if eligible else BLOCKED_NEXT_ACTION,
    }


def build_report_rows(decision_csv: str | Path) -> list[dict[str, str]]:
    return [check_row(row) for row in read_csv(decision_csv)]


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Transform Manual Write-Back Readiness Summary",
        "",
        "This is a post-write-back readiness checker only.",
        "",
        "- It does not generate pre-reaction SDF files.",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not modify manifest files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | post_write_back_check_status | eligible_for_future_transform_dry_run_only | manual_covalent_bond_to_remove | manual_bond_order_to_restore | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["post_write_back_check_status"],
                    row["eligible_for_future_transform_dry_run_only"],
                    row["manual_covalent_bond_to_remove"],
                    row["manual_bond_order_to_restore"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_eligible = all(row["post_write_back_check_status"] == ELIGIBLE_STATUS for row in rows)
    any_training_ready = any(row["training_ready"] == "true" for row in rows)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- Manual write-back is complete.",
            f"- Samples are eligible for future transform dry-run only: {str(all_eligible).lower()}.",
            "- No pre-reaction SDF was generated.",
            f"- No sample is training-ready: {str(not any_training_ready).lower()}.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check post-write-back pre-reaction transform readiness.")
    parser.add_argument("--decision_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command checks post-write-back readiness only.")
    print("warning: it does not generate pre-reaction SDF files.")
    print("warning: it does not modify raw or repaired trial SDF files.")
    rows = build_report_rows(args.decision_csv)
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote post-write-back readiness report: {args.output_csv}")
    print(f"wrote post-write-back readiness summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"post_write_back_check_status={row['post_write_back_check_status']} "
            f"eligible_for_future_transform_dry_run_only={row['eligible_for_future_transform_dry_run_only']} "
            f"blocking_reasons={row['blocking_reasons']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
