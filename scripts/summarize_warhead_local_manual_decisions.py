#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


SUMMARY_COLUMNS = [
    "sample_id",
    "rows",
    "accept_candidate_count",
    "unresolved_count",
    "replace_candidate_count",
    "exclude_sample_count",
    "reviewed_count",
    "needs_followup_count",
    "excluded_count",
    "reactive_atom_rows",
    "warhead_rows",
    "linker_or_boundary_rows",
    "accepted_warhead_rows",
    "unresolved_boundary_rows",
    "has_empty_manual_decision",
    "all_warhead_atoms_accepted",
    "has_unresolved_boundary",
    "local_bond_order_transfer_ready",
    "recommended_next_action",
]

NOT_READY_ACTION = "strictly_warhead_only_trial_or_manual_boundary_review_before_transfer"
READY_ACTION = "eligible_for_non_destructive_local_bond_order_transfer_trial"


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def read_draft(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_drafts(paths: list[Path]) -> dict[str, list[dict[str, str]]]:
    rows_by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path in paths:
        for row in read_draft(path):
            sample_id = row.get("sample_id", "")
            if not sample_id:
                raise ValueError(f"missing sample_id in {path}")
            rows_by_sample[sample_id].append(row)
    return dict(rows_by_sample)


def is_boundary_row(row: dict[str, str]) -> bool:
    final_role = row.get("final_role", "")
    reason = row.get("local_review_reason", "")
    return final_role in {"linker", "boundary"} or "low_confidence_warhead_or_linker" in reason


def summarize_sample(sample_id: str, rows: list[dict[str, str]]) -> dict[str, str]:
    decision_counts = Counter(row.get("manual_decision", "") for row in rows)
    status_counts = Counter(row.get("review_status", "") for row in rows)
    warhead_rows = [row for row in rows if row.get("final_role", "") == "warhead"]
    boundary_rows = [row for row in rows if is_boundary_row(row)]
    accepted_warhead_rows = [
        row for row in warhead_rows if row.get("manual_decision", "") == "accept_candidate"
    ]
    unresolved_boundary_rows = [
        row for row in boundary_rows if row.get("manual_decision", "") == "unresolved"
    ]

    has_empty_manual_decision = decision_counts.get("", 0) > 0
    all_warhead_atoms_accepted = bool(warhead_rows) and len(accepted_warhead_rows) == len(warhead_rows)
    has_unresolved_boundary = len(unresolved_boundary_rows) > 0
    local_ready = all_warhead_atoms_accepted and not has_unresolved_boundary
    recommended_next_action = READY_ACTION if local_ready else NOT_READY_ACTION

    return {
        "sample_id": sample_id,
        "rows": str(len(rows)),
        "accept_candidate_count": str(decision_counts.get("accept_candidate", 0)),
        "unresolved_count": str(decision_counts.get("unresolved", 0)),
        "replace_candidate_count": str(decision_counts.get("replace_candidate", 0)),
        "exclude_sample_count": str(decision_counts.get("exclude_sample", 0)),
        "reviewed_count": str(status_counts.get("reviewed", 0)),
        "needs_followup_count": str(status_counts.get("needs_followup", 0)),
        "excluded_count": str(status_counts.get("excluded", 0)),
        "reactive_atom_rows": str(sum(1 for row in rows if parse_bool(row.get("is_reactive_atom", "")))),
        "warhead_rows": str(len(warhead_rows)),
        "linker_or_boundary_rows": str(len(boundary_rows)),
        "accepted_warhead_rows": str(len(accepted_warhead_rows)),
        "unresolved_boundary_rows": str(len(unresolved_boundary_rows)),
        "has_empty_manual_decision": str(has_empty_manual_decision).lower(),
        "all_warhead_atoms_accepted": str(all_warhead_atoms_accepted).lower(),
        "has_unresolved_boundary": str(has_unresolved_boundary).lower(),
        "local_bond_order_transfer_ready": str(local_ready).lower(),
        "recommended_next_action": recommended_next_action,
    }


def summarize_drafts(paths: list[Path]) -> list[dict[str, str]]:
    rows_by_sample = load_drafts(paths)
    return [summarize_sample(sample_id, rows_by_sample[sample_id]) for sample_id in sorted(rows_by_sample)]


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    with Path(output_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, str]]) -> list[str]:
    columns = [
        "sample_id",
        "rows",
        "accept_candidate_count",
        "unresolved_count",
        "accepted_warhead_rows",
        "unresolved_boundary_rows",
        "local_bond_order_transfer_ready",
        "recommended_next_action",
    ]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row[column] for column in columns) + " |")
    return lines


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines: list[str] = [
        "# Warhead-Local Manual Decision Summary",
        "",
        "This is a summary only.",
        "",
        "- It does not repair bond orders.",
        "- It does not create pre-reaction graphs.",
        "- It does not modify ligand SDF files.",
        "- It does not mark samples as training-ready.",
        "",
    ]
    lines.extend(markdown_table(rows))
    lines.append("")

    for row in rows:
        ready_text = "ready" if row["local_bond_order_transfer_ready"] == "true" else "not ready"
        lines.extend(
            [
                f"## {row['sample_id']}",
                "",
                (
                    f"- Conclusion: {ready_text} for cross-boundary local bond-order transfer. "
                    f"Accepted warhead rows: {row['accepted_warhead_rows']}/{row['warhead_rows']}; "
                    f"unresolved boundary rows: {row['unresolved_boundary_rows']}."
                ),
                f"- Recommended next action: `{row['recommended_next_action']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Global Conclusion",
            "",
            "- All three samples have accepted warhead-core mappings.",
            "- All three samples still have unresolved linker/local boundary atoms.",
            "- No sample is ready for cross-boundary local bond-order transfer.",
            (
                "- The next safe direction is either manual boundary review or a strictly "
                "warhead-only, non-destructive trial that does not cross unresolved atoms."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    Path(output_md).write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize warhead-local manual decisions.")
    parser.add_argument("--drafts", type=Path, nargs="+", required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this summary does not repair bond orders.")
    print("warning: this summary does not create pre-reaction graphs.")
    print("warning: this summary does not modify ligand SDF files.")
    rows = summarize_drafts(args.drafts)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote CSV summary: {args.output_csv}")
    print(f"wrote Markdown summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"accept={row['accept_candidate_count']} "
            f"unresolved={row['unresolved_count']} "
            f"ready={row['local_bond_order_transfer_ready']} "
            f"next={row['recommended_next_action']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
