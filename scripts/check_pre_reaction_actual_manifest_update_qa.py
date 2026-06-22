#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


EXPECTED_LIGAND_PATHS = {
    "BTK_C481_6DI9_pre_reaction": "data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf",
    "KRAS_G12C_5F2E_pre_reaction": "data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf",
    "KRAS_G12C_6OIM_pre_reaction": "data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf",
}
SOURCE_BY_PROPOSED = {
    "BTK_C481_6DI9_pre_reaction": "BTK_C481_6DI9",
    "KRAS_G12C_5F2E_pre_reaction": "KRAS_G12C_5F2E",
    "KRAS_G12C_6OIM_pre_reaction": "KRAS_G12C_6OIM",
}

QA_COLUMNS = [
    "proposed_manifest_sample_id",
    "source_sample_id",
    "current_manifest_csv",
    "backup_manifest_csv",
    "proposed_rows_csv",
    "actual_update_report_csv",
    "current_manifest_exists",
    "backup_manifest_exists",
    "proposed_rows_exists",
    "actual_update_report_exists",
    "backup_sha256_current",
    "current_manifest_sha256_current",
    "report_manifest_sha256_before",
    "report_backup_manifest_sha256",
    "report_manifest_sha256_after",
    "backup_matches_report_before_hash",
    "backup_matches_report_backup_hash",
    "current_matches_report_after_hash",
    "current_manifest_changed_from_backup",
    "row_count_backup",
    "row_count_current",
    "row_count_proposed",
    "row_count_current_equals_backup_plus_3",
    "schema_preserved",
    "proposed_schema_matches_manifest",
    "existing_rows_preserved",
    "appended_rows_match_proposed_rows",
    "proposed_row_present_once",
    "source_row_still_present",
    "proposed_ligand_sdf_path",
    "proposed_ligand_sdf_exists",
    "actual_update_status_confirmed",
    "manifest_updated_confirmed",
    "backup_created_confirmed",
    "new_full_manifest_created_false_confirmed",
    "sdf_modified_false_confirmed",
    "sdf_generated_false_confirmed",
    "pre_reaction_transform_ready",
    "training_ready",
    "actual_manifest_update_qa_status",
    "blocking_reasons",
    "recommended_next_action",
]


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv_with_fieldnames(path: str | Path) -> tuple[list[dict[str, str]], list[str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def count_ids(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        sample_id = row.get("sample_id", "")
        counts[sample_id] = counts.get(sample_id, 0) + 1
    return counts


def index_report_by_proposed(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["proposed_manifest_sample_id"]: row for row in rows}


def file_exists(path: Path) -> bool:
    return path.exists()


def load_inputs(
    *,
    current_manifest_csv: Path,
    backup_manifest_csv: Path,
    proposed_rows_csv: Path,
    actual_update_report_csv: Path,
) -> dict[str, object]:
    for path in [current_manifest_csv, backup_manifest_csv, proposed_rows_csv, actual_update_report_csv]:
        if not path.exists():
            raise FileNotFoundError(f"required input missing: {path}")
    current_rows, current_fields = read_csv_with_fieldnames(current_manifest_csv)
    backup_rows, backup_fields = read_csv_with_fieldnames(backup_manifest_csv)
    proposed_rows, proposed_fields = read_csv_with_fieldnames(proposed_rows_csv)
    report_rows, _ = read_csv_with_fieldnames(actual_update_report_csv)
    return {
        "current_rows": current_rows,
        "current_fields": current_fields,
        "backup_rows": backup_rows,
        "backup_fields": backup_fields,
        "proposed_rows": proposed_rows,
        "proposed_fields": proposed_fields,
        "report_rows": report_rows,
    }


def build_qa_rows(
    *,
    current_manifest_csv: str | Path,
    backup_manifest_csv: str | Path,
    proposed_rows_csv: str | Path,
    actual_update_report_csv: str | Path,
) -> list[dict[str, str]]:
    current_path = Path(current_manifest_csv)
    backup_path = Path(backup_manifest_csv)
    proposed_path = Path(proposed_rows_csv)
    report_path = Path(actual_update_report_csv)
    inputs = load_inputs(
        current_manifest_csv=current_path,
        backup_manifest_csv=backup_path,
        proposed_rows_csv=proposed_path,
        actual_update_report_csv=report_path,
    )
    current_rows = inputs["current_rows"]  # type: ignore[assignment]
    current_fields = inputs["current_fields"]  # type: ignore[assignment]
    backup_rows = inputs["backup_rows"]  # type: ignore[assignment]
    backup_fields = inputs["backup_fields"]  # type: ignore[assignment]
    proposed_rows = inputs["proposed_rows"]  # type: ignore[assignment]
    proposed_fields = inputs["proposed_fields"]  # type: ignore[assignment]
    report_rows = inputs["report_rows"]  # type: ignore[assignment]

    backup_sha = sha256_file(backup_path)
    current_sha = sha256_file(current_path)
    report_by_proposed = index_report_by_proposed(report_rows)
    current_id_counts = count_ids(current_rows)
    source_ids = {row["sample_id"] for row in current_rows}
    appended_rows = current_rows[len(backup_rows) :]
    rows: list[dict[str, str]] = []

    shared_checks = {
        "current_manifest_exists": file_exists(current_path),
        "backup_manifest_exists": file_exists(backup_path),
        "proposed_rows_exists": file_exists(proposed_path),
        "actual_update_report_exists": file_exists(report_path),
        "current_manifest_changed_from_backup": current_sha != backup_sha,
        "row_count_current_equals_backup_plus_3": len(current_rows) == len(backup_rows) + 3,
        "schema_preserved": current_fields == backup_fields,
        "proposed_schema_matches_manifest": proposed_fields == current_fields,
        "existing_rows_preserved": current_rows[: len(backup_rows)] == backup_rows,
        "appended_rows_match_proposed_rows": appended_rows == proposed_rows,
    }

    for proposed_id in sorted(EXPECTED_LIGAND_PATHS):
        source_id = SOURCE_BY_PROPOSED[proposed_id]
        report = report_by_proposed.get(proposed_id, {})
        expected_ligand_path = EXPECTED_LIGAND_PATHS[proposed_id]
        proposed_ligand_path = ""
        for row in proposed_rows:
            if row.get("sample_id") == proposed_id:
                proposed_ligand_path = row.get("ligand_sdf_path", "")
                break

        checks = dict(shared_checks)
        checks.update(
            {
                "backup_matches_report_before_hash": backup_sha == report.get("current_manifest_sha256_before", ""),
                "backup_matches_report_backup_hash": backup_sha == report.get("backup_manifest_sha256", ""),
                "current_matches_report_after_hash": current_sha == report.get("current_manifest_sha256_after", ""),
                "proposed_row_present_once": current_id_counts.get(proposed_id, 0) == 1,
                "source_row_still_present": source_id in source_ids,
                "proposed_ligand_sdf_path_correct": proposed_ligand_path == expected_ligand_path,
                "proposed_ligand_sdf_exists": Path(expected_ligand_path).exists(),
                "actual_update_status_confirmed": report.get("actual_manifest_update_status", "")
                == "manifest_updated_with_3_pre_reaction_rows_after_explicit_approval",
                "manifest_updated_confirmed": report.get("manifest_updated", "") == "true",
                "backup_created_confirmed": report.get("backup_created", "") == "true",
                "new_full_manifest_created_false_confirmed": report.get("new_full_manifest_created", "") == "false",
                "sdf_modified_false_confirmed": report.get("sdf_modified", "") == "false",
                "sdf_generated_false_confirmed": report.get("sdf_generated", "") == "false",
                "pre_reaction_transform_ready_false": report.get("pre_reaction_transform_ready", "") == "false",
                "training_ready_false": report.get("training_ready", "") == "false",
                "report_blocking_reasons_empty": report.get("blocking_reasons", "") == "",
                "row_count_proposed_is_3": len(proposed_rows) == 3,
            }
        )
        reason_names = {
            "current_manifest_exists": "current_manifest_missing",
            "backup_manifest_exists": "backup_manifest_missing",
            "proposed_rows_exists": "proposed_rows_missing",
            "actual_update_report_exists": "actual_update_report_missing",
            "backup_matches_report_before_hash": "backup_hash_mismatch_report_before_hash",
            "backup_matches_report_backup_hash": "backup_hash_mismatch_report_backup_hash",
            "current_matches_report_after_hash": "current_manifest_hash_mismatch_report_after_hash",
            "current_manifest_changed_from_backup": "current_manifest_not_changed_from_backup",
            "row_count_current_equals_backup_plus_3": "current_manifest_not_backup_plus_3_rows",
            "schema_preserved": "manifest_schema_not_preserved",
            "proposed_schema_matches_manifest": "proposed_schema_mismatch_manifest",
            "existing_rows_preserved": "existing_manifest_rows_not_preserved",
            "appended_rows_match_proposed_rows": "appended_rows_do_not_match_proposed_rows",
            "proposed_row_present_once": "proposed_sample_not_present_once",
            "source_row_still_present": "source_sample_missing",
            "proposed_ligand_sdf_path_correct": "proposed_ligand_sdf_path_incorrect",
            "proposed_ligand_sdf_exists": "proposed_ligand_sdf_missing",
            "actual_update_status_confirmed": "actual_update_status_not_confirmed",
            "manifest_updated_confirmed": "manifest_updated_not_true",
            "backup_created_confirmed": "backup_created_not_true",
            "new_full_manifest_created_false_confirmed": "new_full_manifest_created_not_false",
            "sdf_modified_false_confirmed": "sdf_modified_not_false",
            "sdf_generated_false_confirmed": "sdf_generated_not_false",
            "pre_reaction_transform_ready_false": "pre_reaction_transform_ready_not_false",
            "training_ready_false": "training_ready_not_false",
            "report_blocking_reasons_empty": "actual_update_report_blocking_reasons_not_empty",
            "row_count_proposed_is_3": "proposed_rows_count_not_3",
        }
        reasons = [reason_names[name] for name, passed in checks.items() if not passed]
        qa_passed = not reasons
        rows.append(
            {
                "proposed_manifest_sample_id": proposed_id,
                "source_sample_id": source_id,
                "current_manifest_csv": str(current_path),
                "backup_manifest_csv": str(backup_path),
                "proposed_rows_csv": str(proposed_path),
                "actual_update_report_csv": str(report_path),
                "current_manifest_exists": str(checks["current_manifest_exists"]).lower(),
                "backup_manifest_exists": str(checks["backup_manifest_exists"]).lower(),
                "proposed_rows_exists": str(checks["proposed_rows_exists"]).lower(),
                "actual_update_report_exists": str(checks["actual_update_report_exists"]).lower(),
                "backup_sha256_current": backup_sha,
                "current_manifest_sha256_current": current_sha,
                "report_manifest_sha256_before": report.get("current_manifest_sha256_before", ""),
                "report_backup_manifest_sha256": report.get("backup_manifest_sha256", ""),
                "report_manifest_sha256_after": report.get("current_manifest_sha256_after", ""),
                "backup_matches_report_before_hash": str(checks["backup_matches_report_before_hash"]).lower(),
                "backup_matches_report_backup_hash": str(checks["backup_matches_report_backup_hash"]).lower(),
                "current_matches_report_after_hash": str(checks["current_matches_report_after_hash"]).lower(),
                "current_manifest_changed_from_backup": str(checks["current_manifest_changed_from_backup"]).lower(),
                "row_count_backup": str(len(backup_rows)),
                "row_count_current": str(len(current_rows)),
                "row_count_proposed": str(len(proposed_rows)),
                "row_count_current_equals_backup_plus_3": str(
                    checks["row_count_current_equals_backup_plus_3"]
                ).lower(),
                "schema_preserved": str(checks["schema_preserved"]).lower(),
                "proposed_schema_matches_manifest": str(checks["proposed_schema_matches_manifest"]).lower(),
                "existing_rows_preserved": str(checks["existing_rows_preserved"]).lower(),
                "appended_rows_match_proposed_rows": str(checks["appended_rows_match_proposed_rows"]).lower(),
                "proposed_row_present_once": str(checks["proposed_row_present_once"]).lower(),
                "source_row_still_present": str(checks["source_row_still_present"]).lower(),
                "proposed_ligand_sdf_path": proposed_ligand_path,
                "proposed_ligand_sdf_exists": str(checks["proposed_ligand_sdf_exists"]).lower(),
                "actual_update_status_confirmed": str(checks["actual_update_status_confirmed"]).lower(),
                "manifest_updated_confirmed": str(checks["manifest_updated_confirmed"]).lower(),
                "backup_created_confirmed": str(checks["backup_created_confirmed"]).lower(),
                "new_full_manifest_created_false_confirmed": str(
                    checks["new_full_manifest_created_false_confirmed"]
                ).lower(),
                "sdf_modified_false_confirmed": str(checks["sdf_modified_false_confirmed"]).lower(),
                "sdf_generated_false_confirmed": str(checks["sdf_generated_false_confirmed"]).lower(),
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "actual_manifest_update_qa_status": (
                    "actual_manifest_update_qa_passed" if qa_passed else "blocked"
                ),
                "blocking_reasons": ";".join(reasons),
                "recommended_next_action": (
                    "commit_actual_manifest_update_after_qa_not_training"
                    if qa_passed
                    else "fix_actual_manifest_update_before_commit"
                ),
            }
        )
    return rows


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QA_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Actual Manifest Update QA Summary",
        "",
        "This QA validates the actual manifest update after Step 8V.",
        "",
        "- It does not modify manifest files.",
        "- It does not modify or generate SDF files.",
        "- It does not train or fine-tune any model.",
        "- Passing this QA means the actual manifest update can be committed.",
        "- Passing this QA does not mean the samples are training-ready.",
        "",
        "| proposed_manifest_sample_id | source_sample_id | actual_manifest_update_qa_status | proposed_ligand_sdf_path | existing_rows_preserved | appended_rows_match_proposed_rows | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["proposed_manifest_sample_id"],
                    row["source_sample_id"],
                    row["actual_manifest_update_qa_status"],
                    row["proposed_ligand_sdf_path"],
                    row["existing_rows_preserved"],
                    row["appended_rows_match_proposed_rows"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(row["actual_manifest_update_qa_status"] == "actual_manifest_update_qa_passed" for row in rows)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- Actual manifest update QA passed for all three rows."
                if all_passed
                else "- One or more actual manifest update QA rows are blocked."
            ),
            "- Backup matches manifest before update.",
            "- Current manifest equals backup plus exactly 3 proposed rows.",
            "- No existing manifest rows were modified.",
            "- No SDF files were modified or generated.",
            "- No training was run.",
            "- Next step is commit actual manifest update and QA files.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="QA the actual pre-reaction manifest update.")
    parser.add_argument("--current_manifest_csv", type=Path, required=True)
    parser.add_argument("--backup_manifest_csv", type=Path, required=True)
    parser.add_argument("--proposed_rows_csv", type=Path, required=True)
    parser.add_argument("--actual_update_report_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command performs QA only.")
    print("warning: it does not modify manifest files.")
    print("warning: it does not modify or generate SDF files.")
    rows = build_qa_rows(
        current_manifest_csv=args.current_manifest_csv,
        backup_manifest_csv=args.backup_manifest_csv,
        proposed_rows_csv=args.proposed_rows_csv,
        actual_update_report_csv=args.actual_update_report_csv,
    )
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote actual manifest update QA report: {args.output_csv}")
    print(f"wrote actual manifest update QA summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['proposed_manifest_sample_id']}: "
            f"qa_status={row['actual_manifest_update_qa_status']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
