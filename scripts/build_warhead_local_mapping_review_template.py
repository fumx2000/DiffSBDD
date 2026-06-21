#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


TEMPLATE_COLUMNS = [
    "sample_id",
    "extracted_atom_id",
    "extracted_element",
    "extracted_pdb_atom_name",
    "reference_candidate_atom_id",
    "reference_element",
    "graph_distance_to_reactive_atom",
    "final_role",
    "is_reactive_atom",
    "mapping_confidence",
    "mapping_warning",
    "local_review_reason",
    "manual_reference_atom_id",
    "manual_decision",
    "manual_note",
]

MANUAL_DECISION_VALUES = (
    "accept_candidate",
    "replace_candidate",
    "unresolved",
    "exclude_sample",
)


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def parse_optional_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def read_report(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def local_review_reasons(row: dict[str, str], max_graph_distance: int) -> list[str]:
    reasons: list[str] = []
    final_role = row.get("final_role", "")
    confidence = row.get("mapping_confidence", "")
    distance = parse_optional_int(row.get("graph_distance_to_reactive_atom", ""))

    if parse_bool(row.get("is_reactive_atom", "")):
        reasons.append("reactive_atom")
    if final_role == "warhead":
        reasons.append("warhead_atom")
    if distance is not None and distance <= max_graph_distance:
        reasons.append(f"within_graph_distance_{max_graph_distance}")
    if confidence in {"low", "unresolved"} and final_role in {"warhead", "linker"}:
        reasons.append("low_confidence_warhead_or_linker")
    return reasons


def build_template_rows(
    graph_repair_report: str | Path,
    max_graph_distance: int,
) -> list[dict[str, str]]:
    rows = read_report(graph_repair_report)
    template_rows: list[dict[str, str]] = []
    for row in rows:
        reasons = local_review_reasons(row, max_graph_distance)
        if not reasons:
            continue
        template_rows.append(
            {
                "sample_id": row.get("sample_id", ""),
                "extracted_atom_id": row.get("extracted_atom_id", ""),
                "extracted_element": row.get("extracted_element", ""),
                "extracted_pdb_atom_name": row.get("extracted_pdb_atom_name", ""),
                "reference_candidate_atom_id": row.get("reference_candidate_atom_id", ""),
                "reference_element": row.get("reference_element", ""),
                "graph_distance_to_reactive_atom": row.get("graph_distance_to_reactive_atom", ""),
                "final_role": row.get("final_role", ""),
                "is_reactive_atom": row.get("is_reactive_atom", ""),
                "mapping_confidence": row.get("mapping_confidence", ""),
                "mapping_warning": row.get("mapping_warning", ""),
                "local_review_reason": ";".join(reasons),
                "manual_reference_atom_id": "",
                "manual_decision": "",
                "manual_note": "",
            }
        )
    return template_rows


def write_template(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    with Path(output_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TEMPLATE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a warhead-local manual atom mapping review template. "
            "manual_decision suggested values: "
            + ", ".join(MANUAL_DECISION_VALUES)
        )
    )
    parser.add_argument("--graph_repair_report", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--max_graph_distance", type=int, default=3)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this template does not repair bond orders.")
    print("warning: this template does not create pre-reaction graphs.")
    print("warning: warhead-local mapping must be reviewed before local bond-order transfer.")
    print("warning: ideal/reference atom order must not be used directly for manifest indices.")
    print("manual_decision suggested values: " + ", ".join(MANUAL_DECISION_VALUES))
    rows = build_template_rows(args.graph_repair_report, args.max_graph_distance)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    write_template(rows, args.output_csv)
    print(f"wrote warhead-local mapping review template: {args.output_csv}")
    print(f"rows: {len(rows)}")
    print(f"max_graph_distance: {args.max_graph_distance}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
