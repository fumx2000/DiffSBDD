#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


GATE_COLUMNS = [
    "sample_id",
    "output_pre_reaction_sdf",
    "qa_status",
    "source_restore_bond_order",
    "output_restore_bond_order",
    "target_bond_order",
    "bond_block_change_count",
    "allowed_bond_order_change_only",
    "atom_block_identical",
    "coordinate_block_identical",
    "source_repaired_sdf_sha256_matches_report",
    "output_pre_reaction_sdf_sha256_matches_report",
    "write_sdf_status",
    "execution_plan_status",
    "dataset_candidate_gate_status",
    "eligible_for_dataset_assembly_candidate_pool",
    "pre_reaction_sdf_qa_passed",
    "safe_as_derived_pre_reaction_artifact",
    "can_update_manifest_later",
    "manifest_updated",
    "pre_reaction_transform_ready",
    "training_ready",
    "blocking_reasons",
    "recommended_next_action",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def index_by_sample(rows: list[dict[str, str]], source_name: str) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        sample_id = row.get("sample_id", "")
        if not sample_id:
            raise ValueError(f"missing sample_id in {source_name}")
        if sample_id in indexed:
            raise ValueError(f"duplicate sample_id in {source_name}: {sample_id}")
        indexed[sample_id] = row
    return indexed


def is_true(value: str) -> bool:
    return value.strip().lower() == "true"


def output_path_exists(path_value: str) -> bool:
    return bool(path_value) and Path(path_value).exists()


def gate_row(
    qa_row: dict[str, str],
    write_row: dict[str, str],
    execution_row: dict[str, str],
) -> dict[str, str]:
    reasons: list[str] = []
    output_pre_reaction_sdf = qa_row.get("output_pre_reaction_sdf", "")
    qa_status = qa_row.get("qa_status", "")
    write_sdf_status = write_row.get("write_sdf_status", "")
    execution_plan_status = execution_row.get("execution_plan_status", "")
    output_restore_bond_order = qa_row.get("output_restore_bond_order", "")
    target_bond_order = qa_row.get("target_bond_order", "")
    training_ready = qa_row.get("training_ready", "false")

    checks = [
        ("qa_status_not_passed", qa_status == "generated_pre_reaction_sdf_qa_passed"),
        (
            "write_sdf_status_not_written_after_explicit_human_approval",
            write_sdf_status == "written_after_explicit_human_approval",
        ),
        (
            "execution_plan_status_not_ready_for_guarded_transform_script_design",
            execution_plan_status == "ready_for_guarded_transform_script_design",
        ),
        ("output_pre_reaction_sdf_missing_or_empty", output_path_exists(output_pre_reaction_sdf)),
        (
            "source_repaired_sdf_sha256_mismatch",
            is_true(qa_row.get("source_repaired_sdf_sha256_matches_report", "")),
        ),
        (
            "output_pre_reaction_sdf_sha256_mismatch",
            is_true(qa_row.get("output_pre_reaction_sdf_sha256_matches_report", "")),
        ),
        ("atom_block_not_identical", is_true(qa_row.get("atom_block_identical", ""))),
        ("coordinate_block_not_identical", is_true(qa_row.get("coordinate_block_identical", ""))),
        ("bond_order_change_not_allowed", is_true(qa_row.get("allowed_bond_order_change_only", ""))),
        ("output_restore_bond_order_not_target", output_restore_bond_order == target_bond_order),
        ("training_ready_not_false", training_ready == "false"),
    ]
    for reason, passed in checks:
        if not passed:
            reasons.append(reason)

    passed = not reasons
    return {
        "sample_id": qa_row["sample_id"],
        "output_pre_reaction_sdf": output_pre_reaction_sdf,
        "qa_status": qa_status,
        "source_restore_bond_order": qa_row.get("source_restore_bond_order", ""),
        "output_restore_bond_order": output_restore_bond_order,
        "target_bond_order": target_bond_order,
        "bond_block_change_count": qa_row.get("bond_block_change_count", ""),
        "allowed_bond_order_change_only": qa_row.get("allowed_bond_order_change_only", ""),
        "atom_block_identical": qa_row.get("atom_block_identical", ""),
        "coordinate_block_identical": qa_row.get("coordinate_block_identical", ""),
        "source_repaired_sdf_sha256_matches_report": qa_row.get(
            "source_repaired_sdf_sha256_matches_report", ""
        ),
        "output_pre_reaction_sdf_sha256_matches_report": qa_row.get(
            "output_pre_reaction_sdf_sha256_matches_report", ""
        ),
        "write_sdf_status": write_sdf_status,
        "execution_plan_status": execution_plan_status,
        "dataset_candidate_gate_status": (
            "passed_for_dataset_candidate_not_training" if passed else "blocked"
        ),
        "eligible_for_dataset_assembly_candidate_pool": str(passed).lower(),
        "pre_reaction_sdf_qa_passed": str(passed).lower(),
        "safe_as_derived_pre_reaction_artifact": str(passed).lower(),
        "can_update_manifest_later": str(passed).lower(),
        "manifest_updated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "build_manifest_staging_plan_not_training"
            if passed
            else "fix_pre_reaction_artifact_before_dataset_gate"
        ),
    }


def build_gate_rows(
    *,
    qa_report_csv: str | Path,
    write_sdf_report_csv: str | Path,
    execution_plan_csv: str | Path,
) -> list[dict[str, str]]:
    qa_rows = index_by_sample(read_csv(qa_report_csv), "qa_report_csv")
    write_rows = index_by_sample(read_csv(write_sdf_report_csv), "write_sdf_report_csv")
    execution_rows = index_by_sample(read_csv(execution_plan_csv), "execution_plan_csv")
    rows: list[dict[str, str]] = []
    for sample_id in sorted(qa_rows):
        if sample_id not in write_rows:
            raise ValueError(f"missing write-SDF report row for {sample_id}")
        if sample_id not in execution_rows:
            raise ValueError(f"missing execution plan row for {sample_id}")
        rows.append(gate_row(qa_rows[sample_id], write_rows[sample_id], execution_rows[sample_id]))
    return rows


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=GATE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Training-Readiness Gate Summary",
        "",
        "This is a readiness gate only.",
        "",
        "- It does not train or fine-tune any model.",
        "- It does not modify manifest files.",
        "- It does not modify any SDF files.",
        "- Passing this gate means the derived pre-reaction SDF can enter a dataset assembly candidate pool.",
        "- Passing this gate does not mean the sample is training-ready.",
        "",
        "| sample_id | dataset_candidate_gate_status | eligible_for_dataset_assembly_candidate_pool | output_pre_reaction_sdf | qa_status | can_update_manifest_later | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["dataset_candidate_gate_status"],
                    row["eligible_for_dataset_assembly_candidate_pool"],
                    row["output_pre_reaction_sdf"],
                    row["qa_status"],
                    row["can_update_manifest_later"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(
        row["dataset_candidate_gate_status"] == "passed_for_dataset_candidate_not_training"
        for row in rows
    )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All generated pre-reaction SDFs passed the dataset-candidate gate."
                if all_passed
                else "- One or more generated pre-reaction SDFs are blocked by this gate."
            ),
            "- Manifest was not modified.",
            "- No SDF was modified.",
            "- No training was run.",
            "- Next step is manifest staging plan, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build pre-reaction training-readiness gate report.")
    parser.add_argument("--qa_report_csv", type=Path, required=True)
    parser.add_argument("--write_sdf_report_csv", type=Path, required=True)
    parser.add_argument("--execution_plan_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command writes a readiness gate report only.")
    print("warning: it does not modify manifest files.")
    print("warning: it does not read, generate, or modify SDF files.")
    print("warning: it does not mark samples training-ready.")
    rows = build_gate_rows(
        qa_report_csv=args.qa_report_csv,
        write_sdf_report_csv=args.write_sdf_report_csv,
        execution_plan_csv=args.execution_plan_csv,
    )
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote pre-reaction training-readiness gate report: {args.output_csv}")
    print(f"wrote pre-reaction training-readiness gate summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"dataset_candidate_gate_status={row['dataset_candidate_gate_status']} "
            f"eligible={row['eligible_for_dataset_assembly_candidate_pool']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
