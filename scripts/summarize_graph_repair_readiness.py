#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


SUMMARY_COLUMNS = [
    "sample_id",
    "total_atoms",
    "high_count",
    "medium_count",
    "low_count",
    "unresolved_count",
    "reactive_atom_confidence",
    "reactive_atom_ready",
    "unresolved_fraction",
    "low_fraction",
    "whole_graph_auto_repair_ready",
    "needs_manual_mapping_review",
    "recommended_next_action",
    "summary_warning",
]

WARNING_TEXT = (
    "this summary does not repair bond orders; "
    "this summary does not create pre-reaction graphs; "
    "low/unresolved mapping prevents automatic whole-graph repair"
)


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def read_report(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def summarize_report(path: str | Path) -> dict[str, str]:
    rows = read_report(path)
    if not rows:
        raise ValueError(f"empty graph repair report: {path}")

    sample_ids = {row.get("sample_id", "") for row in rows}
    if len(sample_ids) != 1:
        raise ValueError(f"expected exactly one sample_id in {path}, found: {sorted(sample_ids)}")
    sample_id = sample_ids.pop()

    total_atoms = len(rows)
    confidence_counts = Counter(row.get("mapping_confidence", "") for row in rows)
    reactive_rows = [row for row in rows if parse_bool(row.get("is_reactive_atom", ""))]
    if len(reactive_rows) != 1:
        raise ValueError(f"expected exactly one reactive atom row in {path}, found: {len(reactive_rows)}")

    reactive_atom_confidence = reactive_rows[0].get("mapping_confidence", "")
    high_count = confidence_counts.get("high", 0)
    medium_count = confidence_counts.get("medium", 0)
    low_count = confidence_counts.get("low", 0)
    unresolved_count = confidence_counts.get("unresolved", 0)

    reactive_atom_ready = reactive_atom_confidence == "high"
    whole_graph_auto_repair_ready = unresolved_count == 0 and low_count == 0
    needs_manual_mapping_review = low_count > 0 or unresolved_count > 0

    if whole_graph_auto_repair_ready:
        recommended_next_action = "eligible_for_non_destructive_bond_order_transfer_trial"
    elif reactive_atom_ready:
        recommended_next_action = "manual_mapping_review_before_bond_order_transfer"
    else:
        recommended_next_action = "exclude_or_recurate_mapping"

    return {
        "sample_id": sample_id,
        "total_atoms": str(total_atoms),
        "high_count": str(high_count),
        "medium_count": str(medium_count),
        "low_count": str(low_count),
        "unresolved_count": str(unresolved_count),
        "reactive_atom_confidence": reactive_atom_confidence,
        "reactive_atom_ready": str(reactive_atom_ready).lower(),
        "unresolved_fraction": f"{unresolved_count / total_atoms:.6f}",
        "low_fraction": f"{low_count / total_atoms:.6f}",
        "whole_graph_auto_repair_ready": str(whole_graph_auto_repair_ready).lower(),
        "needs_manual_mapping_review": str(needs_manual_mapping_review).lower(),
        "recommended_next_action": recommended_next_action,
        "summary_warning": WARNING_TEXT,
    }


def write_summary(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    with Path(output_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize graph repair readiness from diagnostic reports.")
    parser.add_argument("--reports", type=Path, nargs="+", required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this summary does not repair bond orders.")
    print("warning: this summary does not create pre-reaction graphs.")
    print("warning: low/unresolved mapping prevents automatic whole-graph repair.")
    rows = [summarize_report(path) for path in args.reports]
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    write_summary(rows, args.output_csv)
    print(f"wrote graph repair readiness summary: {args.output_csv}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"reactive_atom_ready={row['reactive_atom_ready']} "
            f"whole_graph_auto_repair_ready={row['whole_graph_auto_repair_ready']} "
            f"needs_manual_mapping_review={row['needs_manual_mapping_review']} "
            f"recommended_next_action={row['recommended_next_action']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
