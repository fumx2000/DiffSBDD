#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from pathlib import Path


APPROVAL_PHRASE = "APPROVE_PRE_REACTION_ACTUAL_MANIFEST_UPDATE_STEP_8V"
EXPECTED_PROPOSED_IDS = {
    "BTK_C481_6DI9_pre_reaction": "data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf",
    "KRAS_G12C_5F2E_pre_reaction": "data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf",
    "KRAS_G12C_6OIM_pre_reaction": "data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf",
}
SOURCE_BY_PROPOSED = {
    "BTK_C481_6DI9_pre_reaction": "BTK_C481_6DI9",
    "KRAS_G12C_5F2E_pre_reaction": "KRAS_G12C_5F2E",
    "KRAS_G12C_6OIM_pre_reaction": "KRAS_G12C_6OIM",
}

REPORT_COLUMNS = [
    "sample_id",
    "proposed_manifest_sample_id",
    "source_sample_id",
    "current_manifest_csv",
    "backup_manifest_csv",
    "current_manifest_sha256_before",
    "backup_manifest_sha256",
    "current_manifest_sha256_after",
    "backup_matches_before_manifest",
    "row_count_before",
    "row_count_after",
    "appended_row_count",
    "manifest_schema_preserved",
    "proposed_row_schema_matches_manifest",
    "proposed_row_appended",
    "proposed_row_matches_preview",
    "proposed_ligand_sdf_path",
    "proposed_ligand_sdf_exists",
    "dry_run_status_confirmed",
    "approval_phrase_used",
    "actual_manifest_update_status",
    "manifest_updated",
    "backup_created",
    "new_full_manifest_created",
    "sdf_modified",
    "sdf_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "blocking_reasons",
    "recommended_next_action",
]


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv_with_fieldnames(path: str | Path) -> tuple[list[dict[str, str]], list[str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv_rows(path: str | Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def append_rows(path: str | Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with Path(path).open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writerows(rows)


def index_by_sample(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in rows}


def precheck(
    *,
    current_manifest_csv: Path,
    proposed_rows_csv: Path,
    dry_run_report_csv: Path,
    approval_phrase: str,
    backup_manifest_csv: Path,
) -> tuple[list[dict[str, str]], list[str], list[dict[str, str]], list[dict[str, str]], list[str]]:
    if approval_phrase != APPROVAL_PHRASE:
        raise ValueError("approval_phrase_mismatch")
    if not current_manifest_csv.exists():
        raise FileNotFoundError(f"current manifest CSV does not exist: {current_manifest_csv}")
    if not proposed_rows_csv.exists():
        raise FileNotFoundError(f"proposed rows CSV does not exist: {proposed_rows_csv}")
    if not dry_run_report_csv.exists():
        raise FileNotFoundError(f"dry-run report CSV does not exist: {dry_run_report_csv}")
    if backup_manifest_csv.exists():
        raise FileExistsError(f"backup manifest already exists: {backup_manifest_csv}")

    manifest_rows, manifest_fieldnames = read_csv_with_fieldnames(current_manifest_csv)
    proposed_rows, proposed_fieldnames = read_csv_with_fieldnames(proposed_rows_csv)
    dry_rows, _ = read_csv_with_fieldnames(dry_run_report_csv)

    if proposed_fieldnames != manifest_fieldnames:
        raise ValueError("proposed_rows_schema_does_not_match_manifest")
    if len(proposed_rows) != 3:
        raise ValueError("proposed_rows_count_not_3")
    proposed_ids = {row["sample_id"] for row in proposed_rows}
    if proposed_ids != set(EXPECTED_PROPOSED_IDS):
        raise ValueError("proposed_rows_sample_ids_unexpected")

    manifest_ids = {row["sample_id"] for row in manifest_rows}
    existing_proposed = sorted(proposed_ids & manifest_ids)
    if existing_proposed:
        raise ValueError(f"current_manifest_already_contains_proposed_sample:{','.join(existing_proposed)}")
    missing_sources = sorted(set(SOURCE_BY_PROPOSED.values()) - manifest_ids)
    if missing_sources:
        raise ValueError(f"source_sample_missing_from_current_manifest:{','.join(missing_sources)}")

    proposed_by_id = index_by_sample(proposed_rows)
    for proposed_id, expected_path in EXPECTED_PROPOSED_IDS.items():
        row = proposed_by_id[proposed_id]
        actual_path = row.get("ligand_sdf_path", "")
        if actual_path != expected_path:
            raise ValueError(f"proposed_ligand_sdf_path_mismatch:{proposed_id}")
        if not Path(actual_path).exists():
            raise FileNotFoundError(f"proposed ligand SDF does not exist: {actual_path}")

    dry_by_proposed = {row["proposed_manifest_sample_id"]: row for row in dry_rows}
    for proposed_id in EXPECTED_PROPOSED_IDS:
        dry = dry_by_proposed.get(proposed_id)
        if dry is None:
            raise ValueError(f"dry_run_report_missing_proposed_sample:{proposed_id}")
        checks = {
            "manifest_update_dry_run_status": "passed_manifest_update_dry_run_not_written",
            "would_add_manifest_row_later": "true",
            "manifest_updated": "false",
            "new_manifest_created": "false",
            "training_ready": "false",
            "blocking_reasons": "",
        }
        for field, expected in checks.items():
            if dry.get(field, "") != expected:
                raise ValueError(f"dry_run_report_field_not_expected:{proposed_id}:{field}")
    return manifest_rows, manifest_fieldnames, proposed_rows, dry_rows, sorted(proposed_ids)


def verify_after_append(
    *,
    manifest_rows_before: list[dict[str, str]],
    proposed_rows: list[dict[str, str]],
    manifest_rows_after: list[dict[str, str]],
    backup_rows: list[dict[str, str]],
) -> None:
    if len(manifest_rows_after) != len(manifest_rows_before) + len(proposed_rows):
        raise ValueError("row_count_after_not_before_plus_appended")
    if backup_rows != manifest_rows_before:
        raise ValueError("backup_rows_do_not_match_manifest_before")
    if manifest_rows_after[: len(manifest_rows_before)] != manifest_rows_before:
        raise ValueError("existing_manifest_rows_changed")
    if manifest_rows_after[len(manifest_rows_before) :] != proposed_rows:
        raise ValueError("appended_rows_do_not_match_proposed_rows")


def build_report_rows(
    *,
    proposed_rows: list[dict[str, str]],
    dry_rows: list[dict[str, str]],
    current_manifest_csv: Path,
    backup_manifest_csv: Path,
    sha_before: str,
    backup_sha: str,
    sha_after: str,
    row_count_before: int,
    row_count_after: int,
    manifest_schema_preserved: bool,
    proposed_schema_matches: bool,
) -> list[dict[str, str]]:
    dry_by_proposed = {row["proposed_manifest_sample_id"]: row for row in dry_rows}
    backup_matches = backup_sha == sha_before
    rows: list[dict[str, str]] = []
    for proposed in proposed_rows:
        proposed_id = proposed["sample_id"]
        source_id = SOURCE_BY_PROPOSED[proposed_id]
        dry = dry_by_proposed[proposed_id]
        ligand_path = proposed["ligand_sdf_path"]
        rows.append(
            {
                "sample_id": source_id,
                "proposed_manifest_sample_id": proposed_id,
                "source_sample_id": source_id,
                "current_manifest_csv": str(current_manifest_csv),
                "backup_manifest_csv": str(backup_manifest_csv),
                "current_manifest_sha256_before": sha_before,
                "backup_manifest_sha256": backup_sha,
                "current_manifest_sha256_after": sha_after,
                "backup_matches_before_manifest": str(backup_matches).lower(),
                "row_count_before": str(row_count_before),
                "row_count_after": str(row_count_after),
                "appended_row_count": str(len(proposed_rows)),
                "manifest_schema_preserved": str(manifest_schema_preserved).lower(),
                "proposed_row_schema_matches_manifest": str(proposed_schema_matches).lower(),
                "proposed_row_appended": "true",
                "proposed_row_matches_preview": "true",
                "proposed_ligand_sdf_path": ligand_path,
                "proposed_ligand_sdf_exists": str(Path(ligand_path).exists()).lower(),
                "dry_run_status_confirmed": str(
                    dry["manifest_update_dry_run_status"] == "passed_manifest_update_dry_run_not_written"
                ).lower(),
                "approval_phrase_used": APPROVAL_PHRASE,
                "actual_manifest_update_status": (
                    "manifest_updated_with_3_pre_reaction_rows_after_explicit_approval"
                ),
                "manifest_updated": "true",
                "backup_created": "true",
                "new_full_manifest_created": "false",
                "sdf_modified": "false",
                "sdf_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "blocking_reasons": "",
                "recommended_next_action": "run_actual_manifest_update_qa_before_training_readiness",
            }
        )
    return rows


def write_report(rows: list[dict[str, str]], output_report_csv: str | Path) -> None:
    output_path = Path(output_report_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv_rows(output_path, rows, REPORT_COLUMNS)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Actual Manifest Update Summary",
        "",
        "This actual manifest update was performed only after explicit human approval.",
        "",
        f"- Approval phrase: {APPROVAL_PHRASE}",
        "- It modified only data/raw/covalent_small/manifests/manifest_real_small.csv.",
        "- It appended exactly 3 derived pre-reaction rows.",
        "- It created a backup before modification.",
        "- It did not modify or generate any SDF files.",
        "- It did not train or fine-tune any model.",
        "- Samples are still not training-ready until post-update QA passes.",
        "",
        "| proposed_manifest_sample_id | source_sample_id | proposed_ligand_sdf_path | proposed_row_appended | actual_manifest_update_status | training_ready |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["proposed_manifest_sample_id"],
                    row["source_sample_id"],
                    row["proposed_ligand_sdf_path"],
                    row["proposed_row_appended"],
                    row["actual_manifest_update_status"],
                    row["training_ready"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- manifest_real_small.csv was updated by appending exactly 3 rows.",
            "- Backup was created.",
            "- No existing manifest rows were modified.",
            "- No SDF files were modified.",
            "- No SDF files were generated.",
            "- No training was run.",
            "- Next step is actual manifest update QA.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def apply_update(
    *,
    current_manifest_csv: str | Path,
    proposed_rows_csv: str | Path,
    dry_run_report_csv: str | Path,
    approval_phrase: str,
    backup_manifest_csv: str | Path,
    output_report_csv: str | Path,
    output_md: str | Path,
) -> list[dict[str, str]]:
    current_path = Path(current_manifest_csv)
    proposed_path = Path(proposed_rows_csv)
    dry_path = Path(dry_run_report_csv)
    backup_path = Path(backup_manifest_csv)
    manifest_rows_before, fieldnames, proposed_rows, dry_rows, _ = precheck(
        current_manifest_csv=current_path,
        proposed_rows_csv=proposed_path,
        dry_run_report_csv=dry_path,
        approval_phrase=approval_phrase,
        backup_manifest_csv=backup_path,
    )
    proposed_fieldnames = read_csv_with_fieldnames(proposed_path)[1]
    sha_before = sha256_file(current_path)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(current_path, backup_path)
    backup_sha = sha256_file(backup_path)
    append_rows(current_path, proposed_rows, fieldnames)
    sha_after = sha256_file(current_path)
    manifest_rows_after, fieldnames_after = read_csv_with_fieldnames(current_path)
    backup_rows, fieldnames_backup = read_csv_with_fieldnames(backup_path)
    verify_after_append(
        manifest_rows_before=manifest_rows_before,
        proposed_rows=proposed_rows,
        manifest_rows_after=manifest_rows_after,
        backup_rows=backup_rows,
    )
    if fieldnames_after != fieldnames or fieldnames_backup != fieldnames:
        raise ValueError("manifest_schema_not_preserved")
    if sha_after == sha_before:
        raise ValueError("manifest_sha256_after_equals_before")
    reports = build_report_rows(
        proposed_rows=proposed_rows,
        dry_rows=dry_rows,
        current_manifest_csv=current_path,
        backup_manifest_csv=backup_path,
        sha_before=sha_before,
        backup_sha=backup_sha,
        sha_after=sha_after,
        row_count_before=len(manifest_rows_before),
        row_count_after=len(manifest_rows_after),
        manifest_schema_preserved=fieldnames_after == fieldnames,
        proposed_schema_matches=proposed_fieldnames == fieldnames,
    )
    write_report(reports, output_report_csv)
    write_markdown(build_markdown(reports), output_md)
    return reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply the approved pre-reaction manifest update.")
    parser.add_argument("--current_manifest_csv", type=Path, required=True)
    parser.add_argument("--proposed_rows_csv", type=Path, required=True)
    parser.add_argument("--dry_run_report_csv", type=Path, required=True)
    parser.add_argument("--approval_phrase", required=True)
    parser.add_argument("--backup_manifest_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command modifies manifest_real_small.csv after explicit approval.")
    print("warning: it does not modify or generate SDF files.")
    rows = apply_update(
        current_manifest_csv=args.current_manifest_csv,
        proposed_rows_csv=args.proposed_rows_csv,
        dry_run_report_csv=args.dry_run_report_csv,
        approval_phrase=args.approval_phrase,
        backup_manifest_csv=args.backup_manifest_csv,
        output_report_csv=args.output_report_csv,
        output_md=args.output_md,
    )
    print(f"wrote actual manifest update report: {args.output_report_csv}")
    print(f"wrote actual manifest update summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['proposed_manifest_sample_id']}: "
            f"status={row['actual_manifest_update_status']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
