#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_INCLUDE_CONFIDENCE = ("low", "unresolved", "medium")

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


def parse_confidence_values(raw_values: list[str] | None) -> set[str]:
    if not raw_values:
        raw_values = list(DEFAULT_INCLUDE_CONFIDENCE)
    values: set[str] = set()
    for raw_value in raw_values:
        for part in raw_value.split(","):
            value = part.strip()
            if value:
                values.add(value)
    return values


def read_report(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_template_rows(
    graph_repair_report: str | Path,
    include_confidence: set[str],
) -> list[dict[str, str]]:
    rows = read_report(graph_repair_report)
    template_rows: list[dict[str, str]] = []
    for row in rows:
        if row.get("mapping_confidence", "") not in include_confidence:
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
            "Build a manual atom mapping review template. "
            "manual_decision suggested values: "
            + ", ".join(MANUAL_DECISION_VALUES)
        )
    )
    parser.add_argument("--graph_repair_report", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument(
        "--include_confidence",
        nargs="*",
        default=list(DEFAULT_INCLUDE_CONFIDENCE),
        help="Mapping confidence values to include. Defaults to: low unresolved medium.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    include_confidence = parse_confidence_values(args.include_confidence)
    print("warning: this template does not repair bond orders.")
    print("warning: this template does not create pre-reaction graphs.")
    print("warning: manual_reference_atom_id must be reviewed before bond-order transfer.")
    print("warning: ideal/reference atom order must not be used directly for manifest indices.")
    print("manual_decision suggested values: " + ", ".join(MANUAL_DECISION_VALUES))
    rows = build_template_rows(args.graph_repair_report, include_confidence)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    write_template(rows, args.output_csv)
    print(f"wrote manual mapping review template: {args.output_csv}")
    print(f"rows: {len(rows)}")
    print(f"include_confidence: {' '.join(sorted(include_confidence))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
