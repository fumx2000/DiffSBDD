#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


EXTRA_COLUMNS = [
    "review_status",
    "decision_source",
    "decision_warning",
]

DECISION_WARNING = (
    "this file is a manual decision draft only; "
    "it does not repair bond orders; "
    "it does not create pre-reaction graphs"
)

ALLOWED_DEFAULT_DECISIONS = {"", "unresolved"}


def read_template(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    return fieldnames, rows


def build_decision_draft_rows(
    template_csv: str | Path,
    default_decision: str = "",
) -> tuple[list[str], list[dict[str, str]]]:
    if default_decision not in ALLOWED_DEFAULT_DECISIONS:
        raise ValueError(
            f"unsupported default_decision: {default_decision!r}; "
            "allowed values are empty string or 'unresolved'"
        )

    fieldnames, rows = read_template(template_csv)
    output_fieldnames = fieldnames + [column for column in EXTRA_COLUMNS if column not in fieldnames]
    output_rows: list[dict[str, str]] = []
    for row in rows:
        output_row = {fieldname: row.get(fieldname, "") for fieldname in fieldnames}
        output_row["manual_reference_atom_id"] = ""
        output_row["manual_decision"] = default_decision
        output_row["manual_note"] = ""
        output_row["review_status"] = "not_reviewed"
        output_row["decision_source"] = "empty_manual_draft"
        output_row["decision_warning"] = DECISION_WARNING
        output_rows.append(output_row)
    return output_fieldnames, output_rows


def write_decision_draft(fieldnames: list[str], rows: list[dict[str, str]], output_csv: str | Path) -> None:
    with Path(output_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize a warhead-local manual decision draft CSV.")
    parser.add_argument("--template_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--default_decision", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this file is a manual decision draft only.")
    print("warning: this command does not repair bond orders.")
    print("warning: this command does not create pre-reaction graphs.")
    fieldnames, rows = build_decision_draft_rows(args.template_csv, args.default_decision)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    write_decision_draft(fieldnames, rows, args.output_csv)
    print(f"wrote warhead-local manual decision draft: {args.output_csv}")
    print(f"rows: {len(rows)}")
    print(f"default_decision: {args.default_decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
