#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


REPORT_COLUMNS = [
    "sample_id",
    "proposed_covalent_bond_to_remove_candidate",
    "proposed_bond_order_to_restore_candidate",
    "manual_covalent_bond_to_remove",
    "manual_bond_order_to_restore",
    "manual_boundary_resolution",
    "reviewer_decision",
    "review_status",
    "requires_manual_review",
    "boundary_resolution_required",
    "pre_reaction_transform_ready",
    "training_ready",
    "decision_check_status",
    "can_approve_for_future_transform",
    "blocking_reasons",
    "recommended_next_action",
]

BLOCKED_NEXT_ACTION = "fill_manual_transform_decision_fields_before_transform"
ELIGIBLE_NEXT_ACTION = "eligible_for_future_transform_dry_run_only"


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def blocking_reasons(row: dict[str, str]) -> list[str]:
    reasons: list[str] = []
    if parse_bool(row.get("requires_manual_review", "")):
        reasons.append("requires_manual_review_true")
    if row.get("review_status", "") != "reviewed":
        reasons.append("review_status_not_reviewed")
    if row.get("reviewer_decision", "") != "approved":
        reasons.append("reviewer_decision_missing")
    if not row.get("manual_covalent_bond_to_remove", ""):
        reasons.append("manual_covalent_bond_to_remove_missing")
    if not row.get("manual_bond_order_to_restore", ""):
        reasons.append("manual_bond_order_to_restore_missing")
    if parse_bool(row.get("boundary_resolution_required", "")) and not row.get("manual_boundary_resolution", ""):
        reasons.append("manual_boundary_resolution_missing")
    if not row.get("proposed_bond_order_to_restore_candidate", ""):
        reasons.append("proposed_bond_order_to_restore_candidate_missing")
    if row.get("pre_reaction_transform_ready", "") != "false":
        reasons.append("pre_reaction_transform_ready_not_false")
    if row.get("training_ready", "") != "false":
        reasons.append("training_ready_not_false")
    return reasons


def check_row(row: dict[str, str]) -> dict[str, str]:
    reasons = blocking_reasons(row)
    can_approve = len(reasons) == 0
    return {
        "sample_id": row["sample_id"],
        "proposed_covalent_bond_to_remove_candidate": row["proposed_covalent_bond_to_remove_candidate"],
        "proposed_bond_order_to_restore_candidate": row["proposed_bond_order_to_restore_candidate"],
        "manual_covalent_bond_to_remove": row["manual_covalent_bond_to_remove"],
        "manual_bond_order_to_restore": row["manual_bond_order_to_restore"],
        "manual_boundary_resolution": row["manual_boundary_resolution"],
        "reviewer_decision": row["reviewer_decision"],
        "review_status": row["review_status"],
        "requires_manual_review": row["requires_manual_review"],
        "boundary_resolution_required": row["boundary_resolution_required"],
        "pre_reaction_transform_ready": row["pre_reaction_transform_ready"],
        "training_ready": row["training_ready"],
        "decision_check_status": "eligible_for_future_transform_dry_run_only" if can_approve else "blocked",
        "can_approve_for_future_transform": str(can_approve).lower(),
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": ELIGIBLE_NEXT_ACTION if can_approve else BLOCKED_NEXT_ACTION,
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
        "# Pre-Reaction Transform Manual Decision Check Summary",
        "",
        "This is a manual decision checker only.",
        "",
        "- It does not create pre-reaction SDF files.",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not modify manifest files.",
        "- It does not mark samples as training-ready.",
        "",
        "| sample_id | decision_check_status | can_approve_for_future_transform | blocking_reasons | recommended_next_action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["decision_check_status"],
                    row["can_approve_for_future_transform"],
                    row["blocking_reasons"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_blocked = all(row["decision_check_status"] == "blocked" for row in rows)
    any_approved = any(parse_bool(row["can_approve_for_future_transform"]) for row in rows)
    any_training_ready = any(parse_bool(row["training_ready"]) for row in rows)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            f"- All current samples remain blocked: {str(all_blocked).lower()}.",
            f"- No sample is approved for transform: {str(not any_approved).lower()}.",
            f"- No sample is training-ready: {str(not any_training_ready).lower()}.",
            "- No pre-reaction SDF was generated.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check pre-reaction transform manual decision draft.")
    parser.add_argument("--decision_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command checks manual decisions only.")
    print("warning: it does not generate pre-reaction SDF files.")
    print("warning: it does not modify raw or repaired trial SDF files.")
    rows = build_report_rows(args.decision_csv)
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote manual decision check report: {args.output_csv}")
    print(f"wrote manual decision check summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"decision_check_status={row['decision_check_status']} "
            f"can_approve_for_future_transform={row['can_approve_for_future_transform']} "
            f"blocking_reasons={row['blocking_reasons']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
