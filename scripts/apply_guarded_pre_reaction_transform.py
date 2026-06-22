#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


APPROVAL_PHRASE = "APPROVE_PRE_REACTION_TRANSFORM_SDF_STEP_8P"
ALLOWED_OUTPUT_PARENT = Path("data/derived/covalent_small/ligands_pre_reaction")
ALLOWED_OPERATIONS = {
    "validate_existing_target_bond_order_and_copy_if_future_approved",
    "set_bond_order_to_target_if_future_approved",
}

REPORT_COLUMNS = [
    "sample_id",
    "mode",
    "source_repaired_sdf",
    "source_repaired_sdf_sha256_matches",
    "planned_output_pre_reaction_sdf",
    "planned_output_parent",
    "planned_bond_order_operation",
    "execution_plan_status",
    "dry_run_status",
    "can_attempt_future_write_sdf_after_explicit_approval",
    "write_sdf_attempted",
    "pre_reaction_sdf_generated",
    "ligands_pre_reaction_dir_created",
    "raw_ligand_sdf_modified",
    "repaired_trial_sdf_modified",
    "manifest_modified",
    "pre_reaction_transform_ready",
    "training_ready",
    "blocking_reasons",
    "recommended_next_action",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_mode(mode: str) -> None:
    if mode not in {"dry_run", "write_sdf"}:
        raise ValueError(f"unsupported mode: {mode}")


def validate_write_sdf_gate(
    *,
    execution_plan_rows: list[dict[str, str]],
    approval_phrase: str,
    override_plan_write_lock: bool,
) -> None:
    if approval_phrase != APPROVAL_PHRASE:
        raise ValueError(f"write_sdf mode requires approval phrase {APPROVAL_PHRASE}")
    locked_samples = [
        row["sample_id"]
        for row in execution_plan_rows
        if row.get("write_sdf_allowed_by_plan", "") != "true"
    ]
    if locked_samples and not override_plan_write_lock:
        raise ValueError(
            "write_sdf mode blocked by execution plan write lock for samples: "
            + ", ".join(sorted(locked_samples))
        )
    raise NotImplementedError("write_sdf mode is intentionally not implemented in this step")


def output_parent_is_allowed(path_text: str) -> bool:
    return Path(path_text).parent.as_posix() == ALLOWED_OUTPUT_PARENT.as_posix()


def check_plan_row(row: dict[str, str]) -> dict[str, str]:
    reasons: list[str] = []
    source_path = Path(row["source_repaired_sdf"])
    source_exists = source_path.exists()
    if not source_exists:
        reasons.append("source_repaired_sdf_missing")
        hash_matches = False
    else:
        hash_matches = sha256_file(source_path) == row.get("source_repaired_sdf_sha256", "")
        if not hash_matches:
            reasons.append("source_repaired_sdf_sha256_mismatch")

    if row.get("execution_plan_status", "") != "ready_for_guarded_transform_script_design":
        reasons.append("execution_plan_status_not_ready")
    if not output_parent_is_allowed(row.get("planned_output_pre_reaction_sdf", "")):
        reasons.append("planned_output_parent_not_allowed")
    if row.get("planned_bond_order_operation", "") not in ALLOWED_OPERATIONS:
        reasons.append("planned_bond_order_operation_not_allowed")

    passed = not reasons
    return {
        "sample_id": row["sample_id"],
        "mode": "dry_run",
        "source_repaired_sdf": row["source_repaired_sdf"],
        "source_repaired_sdf_sha256_matches": str(hash_matches).lower(),
        "planned_output_pre_reaction_sdf": row["planned_output_pre_reaction_sdf"],
        "planned_output_parent": str(Path(row["planned_output_pre_reaction_sdf"]).parent),
        "planned_bond_order_operation": row["planned_bond_order_operation"],
        "execution_plan_status": row["execution_plan_status"],
        "dry_run_status": "dry_run_passed_no_files_written" if passed else "blocked",
        "can_attempt_future_write_sdf_after_explicit_approval": str(passed).lower(),
        "write_sdf_attempted": "false",
        "pre_reaction_sdf_generated": "false",
        "ligands_pre_reaction_dir_created": "false",
        "raw_ligand_sdf_modified": "false",
        "repaired_trial_sdf_modified": "false",
        "manifest_modified": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "wait_for_explicit_human_approval_before_write_sdf"
            if passed
            else "fix_guarded_transform_dry_run_blockers"
        ),
    }


def build_dry_run_rows(execution_plan_csv: str | Path) -> list[dict[str, str]]:
    return [check_plan_row(row) for row in read_csv(execution_plan_csv)]


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Guarded Pre-Reaction Transform Dry-Run Summary",
        "",
        "This is a dry-run of the guarded transform script only.",
        "",
        "- It does not create pre-reaction SDF files.",
        "- It does not create the ligands_pre_reaction directory.",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not modify manifest files.",
        "- It does not mark samples as training-ready.",
        f"- Future write_sdf mode requires explicit approval phrase {APPROVAL_PHRASE}.",
        "",
        "| sample_id | dry_run_status | source_repaired_sdf_sha256_matches | planned_bond_order_operation | planned_output_pre_reaction_sdf | can_attempt_future_write_sdf_after_explicit_approval |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["dry_run_status"],
                    row["source_repaired_sdf_sha256_matches"],
                    row["planned_bond_order_operation"],
                    row["planned_output_pre_reaction_sdf"],
                    row["can_attempt_future_write_sdf_after_explicit_approval"],
                ]
            )
            + " |"
        )
    all_passed = all(row["dry_run_status"] == "dry_run_passed_no_files_written" for row in rows)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            f"- Guarded transform dry-run passed: {str(all_passed).lower()}.",
            "- No pre-reaction SDF was generated.",
            "- No output directory was created.",
            "- No sample is training-ready.",
            "- Wait for explicit human approval before write_sdf.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def run(
    *,
    execution_plan_csv: str | Path,
    mode: str,
    output_report_csv: str | Path,
    output_md: str | Path,
    approval_phrase: str = "",
    override_plan_write_lock: bool = False,
) -> list[dict[str, str]]:
    validate_mode(mode)
    plan_rows = read_csv(execution_plan_csv)
    if mode == "write_sdf":
        validate_write_sdf_gate(
            execution_plan_rows=plan_rows,
            approval_phrase=approval_phrase,
            override_plan_write_lock=override_plan_write_lock,
        )
    rows = [check_plan_row(row) for row in plan_rows]
    write_csv(rows, output_report_csv)
    write_markdown(build_markdown(rows), output_md)
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply guarded pre-reaction transform.")
    parser.add_argument("--execution_plan_csv", type=Path, required=True)
    parser.add_argument("--mode", choices=["dry_run", "write_sdf"], required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    parser.add_argument("--approval_phrase", default="")
    parser.add_argument("--override_plan_write_lock", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: dry_run mode does not generate pre-reaction SDF files.")
    print("warning: write_sdf mode is guarded and must not be used without explicit approval.")
    rows = run(
        execution_plan_csv=args.execution_plan_csv,
        mode=args.mode,
        output_report_csv=args.output_report_csv,
        output_md=args.output_md,
        approval_phrase=args.approval_phrase,
        override_plan_write_lock=args.override_plan_write_lock,
    )
    print(f"wrote guarded transform dry-run report: {args.output_report_csv}")
    print(f"wrote guarded transform dry-run summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"dry_run_status={row['dry_run_status']} "
            f"source_hash_matches={row['source_repaired_sdf_sha256_matches']} "
            f"future_write={row['can_attempt_future_write_sdf_after_explicit_approval']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
