#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


REPORT_COLUMNS = [
    "sample_id",
    "proposed_manifest_sample_id",
    "source_sample_id",
    "current_manifest_csv",
    "current_manifest_sha256_before",
    "current_manifest_sha256_after",
    "current_manifest_unchanged",
    "current_manifest_contains_source_sample",
    "current_manifest_contains_proposed_sample",
    "source_manifest_row_found",
    "manifest_ligand_path_column",
    "proposed_ligand_sdf_path",
    "proposed_row_sample_id",
    "proposed_row_ligand_sdf_path",
    "proposed_rows_preview_written",
    "can_stage_manifest_row",
    "manifest_row_should_be_added_later",
    "manifest_update_dry_run_status",
    "would_add_manifest_row_later",
    "manifest_updated",
    "new_manifest_created",
    "pre_reaction_transform_ready",
    "training_ready",
    "blocking_reasons",
    "recommended_next_action",
]

LIGAND_PATH_COLUMNS = ["ligand_sdf_path", "ligand_path", "sdf_path", "ligand_file"]


def read_csv_with_fieldnames(path: str | Path) -> tuple[list[dict[str, str]], list[str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def read_csv(path: str | Path) -> list[dict[str, str]]:
    rows, _ = read_csv_with_fieldnames(path)
    return rows


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def is_true(value: str) -> bool:
    return value.strip().lower() == "true"


def ligand_path_column(fieldnames: list[str]) -> str:
    for column in LIGAND_PATH_COLUMNS:
        if column in fieldnames:
            return column
    return ""


def index_by_sample(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        sample_id = row.get("sample_id", "")
        if sample_id:
            indexed[sample_id] = row
    return indexed


def build_proposed_row(
    *,
    staging_row: dict[str, str],
    manifest_row: dict[str, str],
    ligand_column: str,
) -> dict[str, str]:
    proposed = dict(manifest_row)
    proposed["sample_id"] = staging_row["proposed_manifest_sample_id"]
    proposed[ligand_column] = staging_row["proposed_ligand_sdf_path"]
    return proposed


def evaluate_row(
    *,
    staging_row: dict[str, str],
    manifest_path: Path,
    manifest_hash_before: str,
    manifest_hash_after: str,
    manifest_ids: set[str],
    manifest_by_sample: dict[str, dict[str, str]],
    ligand_column: str,
) -> tuple[dict[str, str], dict[str, str] | None]:
    sample_id = staging_row["sample_id"]
    source_id = staging_row["source_sample_id"]
    proposed_id = staging_row["proposed_manifest_sample_id"]
    source_row = manifest_by_sample.get(source_id)
    proposed_row: dict[str, str] | None = None
    reasons: list[str] = []
    proposed_ligand_path = staging_row.get("proposed_ligand_sdf_path", "")

    source_found = source_row is not None
    contains_source = source_id in manifest_ids
    contains_proposed = proposed_id in manifest_ids
    manifest_unchanged = manifest_hash_before == manifest_hash_after
    if not ligand_column:
        reasons.append("manifest_ligand_path_column_missing")
    if not is_true(staging_row.get("can_stage_manifest_row", "")):
        reasons.append("can_stage_manifest_row_not_true")
    if not is_true(staging_row.get("manifest_row_should_be_added_later", "")):
        reasons.append("manifest_row_should_be_added_later_not_true")
    if contains_proposed:
        reasons.append("current_manifest_already_contains_proposed_sample")
    if not source_found:
        reasons.append("source_manifest_row_missing")
    if not proposed_ligand_path:
        reasons.append("proposed_ligand_sdf_path_missing")
    if not manifest_unchanged:
        reasons.append("current_manifest_changed_during_dry_run")
    if staging_row.get("training_ready", "false") != "false":
        reasons.append("training_ready_not_false")

    proposed_row_sample_id = ""
    proposed_row_ligand_path = ""
    if not reasons and source_row is not None and ligand_column:
        proposed_row = build_proposed_row(
            staging_row=staging_row,
            manifest_row=source_row,
            ligand_column=ligand_column,
        )
        proposed_row_sample_id = proposed_row.get("sample_id", "")
        proposed_row_ligand_path = proposed_row.get(ligand_column, "")
        if proposed_row_sample_id != proposed_id:
            reasons.append("proposed_row_sample_id_mismatch")
        if proposed_row_ligand_path != proposed_ligand_path:
            reasons.append("proposed_row_ligand_sdf_path_mismatch")

    passed = not reasons
    report = {
        "sample_id": sample_id,
        "proposed_manifest_sample_id": proposed_id,
        "source_sample_id": source_id,
        "current_manifest_csv": str(manifest_path),
        "current_manifest_sha256_before": manifest_hash_before,
        "current_manifest_sha256_after": manifest_hash_after,
        "current_manifest_unchanged": str(manifest_unchanged).lower(),
        "current_manifest_contains_source_sample": str(contains_source).lower(),
        "current_manifest_contains_proposed_sample": str(contains_proposed).lower(),
        "source_manifest_row_found": str(source_found).lower(),
        "manifest_ligand_path_column": ligand_column,
        "proposed_ligand_sdf_path": proposed_ligand_path,
        "proposed_row_sample_id": proposed_row_sample_id,
        "proposed_row_ligand_sdf_path": proposed_row_ligand_path,
        "proposed_rows_preview_written": str(passed).lower(),
        "can_stage_manifest_row": staging_row.get("can_stage_manifest_row", ""),
        "manifest_row_should_be_added_later": staging_row.get("manifest_row_should_be_added_later", ""),
        "manifest_update_dry_run_status": (
            "passed_manifest_update_dry_run_not_written" if passed else "blocked"
        ),
        "would_add_manifest_row_later": str(passed).lower(),
        "manifest_updated": "false",
        "new_manifest_created": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "manual_review_manifest_update_dry_run_before_approval"
            if passed
            else "fix_manifest_update_dry_run_blockers"
        ),
    }
    return report, proposed_row if passed else None


def build_dry_run(
    *,
    staging_plan_csv: str | Path,
    current_manifest_csv: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    manifest_path = Path(current_manifest_csv)
    if not manifest_path.exists():
        raise FileNotFoundError(f"current manifest CSV does not exist: {manifest_path}")
    manifest_hash_before = sha256_file(manifest_path)
    manifest_rows, manifest_fieldnames = read_csv_with_fieldnames(manifest_path)
    ligand_column = ligand_path_column(manifest_fieldnames)
    manifest_by_sample = index_by_sample(manifest_rows)
    manifest_ids = set(manifest_by_sample)
    manifest_hash_after = sha256_file(manifest_path)

    reports: list[dict[str, str]] = []
    proposed_rows: list[dict[str, str]] = []
    for staging_row in sorted(read_csv(staging_plan_csv), key=lambda row: row["sample_id"]):
        report, proposed = evaluate_row(
            staging_row=staging_row,
            manifest_path=manifest_path,
            manifest_hash_before=manifest_hash_before,
            manifest_hash_after=manifest_hash_after,
            manifest_ids=manifest_ids,
            manifest_by_sample=manifest_by_sample,
            ligand_column=ligand_column,
        )
        reports.append(report)
        if proposed is not None:
            proposed_rows.append(proposed)
    return reports, proposed_rows, manifest_fieldnames


def write_report(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_proposed_rows(rows: list[dict[str, str]], fieldnames: list[str], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Manifest Update Dry-Run Summary",
        "",
        "This is a manifest update dry-run only.",
        "",
        "- It does not modify manifest_real_small.csv.",
        "- It does not create a new full manifest file.",
        "- It only writes a proposed rows preview.",
        "- It does not modify any SDF files.",
        "- It does not train or fine-tune any model.",
        "- Passing this dry-run does not mean the samples are training-ready.",
        "",
        "| sample_id | proposed_manifest_sample_id | proposed_ligand_sdf_path | manifest_update_dry_run_status | would_add_manifest_row_later | manifest_updated | new_manifest_created | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["proposed_manifest_sample_id"],
                    row["proposed_ligand_sdf_path"],
                    row["manifest_update_dry_run_status"],
                    row["would_add_manifest_row_later"],
                    row["manifest_updated"],
                    row["new_manifest_created"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(row["manifest_update_dry_run_status"] == "passed_manifest_update_dry_run_not_written" for row in rows)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three proposed manifest rows passed dry-run."
                if all_passed
                else "- One or more proposed manifest rows are blocked."
            ),
            "- manifest_real_small.csv was not modified.",
            "- No new full manifest was created.",
            "- Proposed rows preview was written.",
            "- No SDF was modified.",
            "- No training was run.",
            "- Next step is manual review and explicit approval before actual manifest update.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a pre-reaction manifest update dry-run report.")
    parser.add_argument("--staging_plan_csv", type=Path, required=True)
    parser.add_argument("--current_manifest_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_proposed_rows_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command is a manifest update dry-run only.")
    print("warning: it does not modify manifest_real_small.csv or create a new full manifest.")
    print("warning: it does not modify or generate SDF files.")
    rows, proposed_rows, manifest_fieldnames = build_dry_run(
        staging_plan_csv=args.staging_plan_csv,
        current_manifest_csv=args.current_manifest_csv,
    )
    write_report(rows, args.output_report_csv)
    write_proposed_rows(proposed_rows, manifest_fieldnames, args.output_proposed_rows_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote manifest update dry-run report: {args.output_report_csv}")
    print(f"wrote proposed manifest rows preview: {args.output_proposed_rows_csv}")
    print(f"wrote manifest update dry-run summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"manifest_update_dry_run_status={row['manifest_update_dry_run_status']} "
            f"would_add_manifest_row_later={row['would_add_manifest_row_later']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
