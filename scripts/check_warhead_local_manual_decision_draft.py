#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


REQUIRED_COLUMNS = {
    "sample_id",
    "extracted_atom_id",
    "reference_candidate_atom_id",
    "final_role",
    "is_reactive_atom",
    "mapping_confidence",
    "local_review_reason",
    "manual_reference_atom_id",
    "manual_decision",
    "manual_note",
    "review_status",
    "decision_source",
    "decision_warning",
}

ALLOWED_MANUAL_DECISIONS = {
    "",
    "accept_candidate",
    "replace_candidate",
    "unresolved",
    "exclude_sample",
}

ALLOWED_REVIEW_STATUSES = {
    "not_reviewed",
    "reviewed",
    "needs_followup",
    "excluded",
}


@dataclass
class SampleSummary:
    sample_id: str
    rows: int
    decision_counts: Counter[str]
    review_status_counts: Counter[str]
    reactive_atom_rows: int
    warhead_rows: int
    errors: list[str]
    warnings: list[str]


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def read_draft(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def validate_row(row: dict[str, str], row_number: int) -> list[str]:
    errors: list[str] = []
    manual_decision = row.get("manual_decision", "")
    review_status = row.get("review_status", "")

    if manual_decision not in ALLOWED_MANUAL_DECISIONS:
        errors.append(f"row {row_number}: invalid manual_decision={manual_decision!r}")
    if review_status not in ALLOWED_REVIEW_STATUSES:
        errors.append(f"row {row_number}: invalid review_status={review_status!r}")

    if manual_decision == "" and review_status not in {"not_reviewed", "needs_followup"}:
        errors.append(f"row {row_number}: empty manual_decision requires review_status not_reviewed or needs_followup")
    if manual_decision == "accept_candidate" and not row.get("reference_candidate_atom_id", ""):
        errors.append(f"row {row_number}: accept_candidate requires reference_candidate_atom_id")
    if manual_decision == "replace_candidate" and not row.get("manual_reference_atom_id", ""):
        errors.append(f"row {row_number}: replace_candidate requires manual_reference_atom_id")
    if manual_decision == "unresolved" and review_status not in {"needs_followup", "excluded"}:
        errors.append(f"row {row_number}: unresolved requires review_status needs_followup or excluded")
    if manual_decision == "exclude_sample" and review_status != "excluded":
        errors.append(f"row {row_number}: exclude_sample requires review_status excluded")
    return errors


def validate_draft(path: str | Path) -> list[SampleSummary]:
    fieldnames, rows = read_draft(path)
    missing_columns = sorted(REQUIRED_COLUMNS - set(fieldnames))
    summaries_by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        summaries_by_sample[row.get("sample_id", "")].append(row)

    summaries: list[SampleSummary] = []
    if missing_columns:
        summaries.append(
            SampleSummary(
                sample_id=f"{Path(path).name}:missing_columns",
                rows=len(rows),
                decision_counts=Counter(),
                review_status_counts=Counter(),
                reactive_atom_rows=0,
                warhead_rows=0,
                errors=[f"missing required columns: {', '.join(missing_columns)}"],
                warnings=[],
            )
        )
        return summaries

    for sample_id, sample_rows in sorted(summaries_by_sample.items()):
        errors: list[str] = []
        warnings: list[str] = []
        if not sample_id:
            errors.append("sample_id is empty")
        for index, row in enumerate(sample_rows, start=2):
            errors.extend(validate_row(row, index))

        reactive_atom_rows = sum(1 for row in sample_rows if parse_bool(row.get("is_reactive_atom", "")))
        warhead_rows = sum(1 for row in sample_rows if row.get("final_role", "") == "warhead")
        if reactive_atom_rows < 1:
            errors.append("sample must contain at least one is_reactive_atom=true row")
        if warhead_rows < 1:
            errors.append("sample must contain at least one final_role=warhead row")

        decision_counts = Counter(row.get("manual_decision", "") for row in sample_rows)
        review_status_counts = Counter(row.get("review_status", "") for row in sample_rows)
        if decision_counts.get("", 0):
            warnings.append("manual decisions are still empty for one or more rows")

        summaries.append(
            SampleSummary(
                sample_id=sample_id,
                rows=len(sample_rows),
                decision_counts=decision_counts,
                review_status_counts=review_status_counts,
                reactive_atom_rows=reactive_atom_rows,
                warhead_rows=warhead_rows,
                errors=errors,
                warnings=warnings,
            )
        )
    return summaries


def format_counts(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return ", ".join(f"{key or '<empty>'}:{counter[key]}" for key in sorted(counter))


def print_summaries(summaries: list[SampleSummary]) -> None:
    for summary in summaries:
        print(f"sample_id: {summary.sample_id}")
        print(f"  rows: {summary.rows}")
        print(f"  decision counts: {format_counts(summary.decision_counts)}")
        print(f"  review_status counts: {format_counts(summary.review_status_counts)}")
        print(f"  reactive atom rows: {summary.reactive_atom_rows}")
        print(f"  warhead rows: {summary.warhead_rows}")
        print(f"  errors: {len(summary.errors)}")
        for error in summary.errors:
            print(f"    error: {error}")
        print(f"  warnings: {len(summary.warnings)}")
        for warning in summary.warnings:
            print(f"    warning: {warning}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check warhead-local manual decision draft CSV files.")
    parser.add_argument("--drafts", type=Path, nargs="+", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    all_summaries: list[SampleSummary] = []
    for draft in args.drafts:
        print(f"checking: {draft}")
        all_summaries.extend(validate_draft(draft))
    print_summaries(all_summaries)
    error_count = sum(len(summary.errors) for summary in all_summaries)
    if error_count:
        print(f"status: FAILED errors={error_count}")
        return 1
    print("status: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
