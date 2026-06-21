#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


TABLE_COLUMNS = [
    "extracted_atom_id",
    "extracted_pdb_atom_name",
    "extracted_element",
    "reference_candidate_atom_id",
    "reference_element",
    "graph_distance_to_reactive_atom",
    "final_role",
    "is_reactive_atom",
    "mapping_confidence",
    "local_review_reason",
    "manual_reference_atom_id",
    "manual_decision",
    "manual_note",
]


def read_template(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_templates(paths: list[Path]) -> dict[str, list[dict[str, str]]]:
    rows_by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path in paths:
        for row in read_template(path):
            sample_id = row.get("sample_id", "")
            if not sample_id:
                raise ValueError(f"missing sample_id in {path}")
            rows_by_sample[sample_id].append(row)
    return dict(rows_by_sample)


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def atom_list(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "none"
    return ", ".join(row.get("extracted_atom_id", "") for row in rows)


def confidence_rows(rows: list[dict[str, str]], confidence: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get("mapping_confidence", "") == confidence]


def reason_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        for reason in row.get("local_review_reason", "").split(";"):
            if reason:
                counts[reason] += 1
    return counts


def format_reason_counts(counts: Counter[str]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{reason}={counts[reason]}" for reason in sorted(counts))


def table_for_rows(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| " + " | ".join(TABLE_COLUMNS) + " |",
        "| " + " | ".join(["---"] * len(TABLE_COLUMNS)) + " |",
    ]
    for row in sorted(rows, key=lambda item: int(item.get("extracted_atom_id", "0"))):
        lines.append("| " + " | ".join(markdown_escape(row.get(column, "")) for column in TABLE_COLUMNS) + " |")
    return lines


def build_markdown(rows_by_sample: dict[str, list[dict[str, str]]]) -> str:
    lines: list[str] = [
        "# Warhead-Local Mapping Review Summary",
        "",
        "This document is for manual review only.",
        "",
        "- It does not repair bond orders.",
        "- It does not create pre-reaction graphs.",
        "- It does not modify ligand SDF files.",
        "- Reference atom order must not be used directly for manifest indices.",
        "",
    ]

    for sample_id in sorted(rows_by_sample):
        rows = rows_by_sample[sample_id]
        reactive_rows = [row for row in rows if row.get("is_reactive_atom", "") == "true"]
        warhead_rows = [row for row in rows if row.get("final_role", "") == "warhead"]
        linker_low_rows = [
            row
            for row in rows
            if row.get("final_role", "") == "linker"
            and "low_confidence_warhead_or_linker" in row.get("local_review_reason", "")
        ]
        low_rows = confidence_rows(rows, "low")
        medium_rows = confidence_rows(rows, "medium")

        lines.extend(
            [
                f"## {sample_id}",
                "",
                f"- sample_id: `{sample_id}`",
                f"- row count: {len(rows)}",
                f"- reactive atom row: {atom_list(reactive_rows)}",
                f"- warhead atom rows: {atom_list(warhead_rows)}",
                f"- linker rows included by low_confidence_warhead_or_linker: {atom_list(linker_low_rows)}",
                f"- rows with mapping_confidence=low: {atom_list(low_rows)}",
                f"- rows with mapping_confidence=medium: {atom_list(medium_rows)}",
                f"- rows with local_review_reason: {format_reason_counts(reason_counts(rows))}",
                "- manual review status: not_reviewed",
                "",
            ]
        )
        lines.extend(table_for_rows(rows))
        lines.append("")
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    Path(output_md).write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Markdown summary for warhead-local mapping review.")
    parser.add_argument("--templates", type=Path, nargs="+", required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this document is for manual review only.")
    print("warning: this document does not repair bond orders.")
    print("warning: this document does not create pre-reaction graphs.")
    print("warning: this document does not modify ligand SDF files.")
    print("warning: reference atom order must not be used directly for manifest indices.")
    rows_by_sample = load_templates(args.templates)
    content = build_markdown(rows_by_sample)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(content, args.output_md)
    print(f"wrote warhead-local mapping review Markdown: {args.output_md}")
    for sample_id in sorted(rows_by_sample):
        print(f"{sample_id}: rows={len(rows_by_sample[sample_id])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
