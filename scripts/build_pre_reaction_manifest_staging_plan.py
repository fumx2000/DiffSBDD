#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


STAGING_COLUMNS = [
    "sample_id",
    "proposed_manifest_sample_id",
    "source_sample_id",
    "source_repaired_sdf",
    "output_pre_reaction_sdf",
    "proposed_ligand_sdf_path",
    "dataset_candidate_gate_status",
    "eligible_for_dataset_assembly_candidate_pool",
    "qa_status",
    "write_sdf_status",
    "execution_plan_status",
    "planned_bond_order_operation",
    "source_restore_bond_order",
    "output_restore_bond_order",
    "target_bond_order",
    "covalent_bond_removed_in_ligand_only_sdf",
    "pre_reaction_ligand_graph_ready",
    "can_stage_manifest_row",
    "manifest_row_should_be_added_later",
    "manifest_updated",
    "current_manifest_contains_source_sample",
    "current_manifest_contains_proposed_sample",
    "proposed_manifest_record_type",
    "pre_reaction_transform_ready",
    "training_ready",
    "blocking_reasons",
    "recommended_next_action",
]


RAW_MANIFEST_FALLBACK = Path("data/raw/covalent_small/manifests/manifest_real_small.csv")


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_manifest_path(path: str | Path) -> Path:
    manifest_path = Path(path)
    if manifest_path.exists():
        return manifest_path
    if manifest_path.as_posix() == "data/derived/covalent_small/manifest_real_small.csv" and RAW_MANIFEST_FALLBACK.exists():
        return RAW_MANIFEST_FALLBACK
    raise FileNotFoundError(f"current manifest CSV does not exist: {manifest_path}")


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


def proposed_sample_id(sample_id: str) -> str:
    return f"{sample_id}_pre_reaction"


def output_path_exists(path_value: str) -> bool:
    return bool(path_value) and Path(path_value).exists()


def manifest_sample_ids(manifest_csv: str | Path) -> set[str]:
    manifest_path = resolve_manifest_path(manifest_csv)
    return {row["sample_id"] for row in read_csv(manifest_path)}


def staging_row(
    gate_row: dict[str, str],
    qa_row: dict[str, str],
    write_row: dict[str, str],
    execution_row: dict[str, str],
    manifest_ids: set[str],
) -> dict[str, str]:
    sample_id = gate_row["sample_id"]
    proposed_id = proposed_sample_id(sample_id)
    output_pre_reaction_sdf = gate_row.get("output_pre_reaction_sdf", "")
    source_repaired_sdf = write_row.get("source_repaired_sdf", "")
    reasons: list[str] = []

    current_contains_source = sample_id in manifest_ids
    current_contains_proposed = proposed_id in manifest_ids
    graph_ready = (
        gate_row.get("dataset_candidate_gate_status", "") == "passed_for_dataset_candidate_not_training"
        and qa_row.get("qa_status", "") == "generated_pre_reaction_sdf_qa_passed"
        and qa_row.get("output_restore_bond_order", "") == qa_row.get("target_bond_order", "")
        and output_path_exists(output_pre_reaction_sdf)
    )

    checks = [
        (
            "dataset_candidate_gate_status_not_passed",
            gate_row.get("dataset_candidate_gate_status", "") == "passed_for_dataset_candidate_not_training",
        ),
        (
            "not_eligible_for_dataset_assembly_candidate_pool",
            is_true(gate_row.get("eligible_for_dataset_assembly_candidate_pool", "")),
        ),
        ("qa_status_not_passed", qa_row.get("qa_status", "") == "generated_pre_reaction_sdf_qa_passed"),
        (
            "write_sdf_status_not_written_after_explicit_human_approval",
            write_row.get("write_sdf_status", "") == "written_after_explicit_human_approval",
        ),
        (
            "execution_plan_status_not_ready_for_guarded_transform_script_design",
            execution_row.get("execution_plan_status", "") == "ready_for_guarded_transform_script_design",
        ),
        ("output_pre_reaction_sdf_missing_or_empty", output_path_exists(output_pre_reaction_sdf)),
        (
            "output_restore_bond_order_not_target",
            qa_row.get("output_restore_bond_order", "") == qa_row.get("target_bond_order", ""),
        ),
        ("current_manifest_already_contains_proposed_sample", not current_contains_proposed),
        ("training_ready_not_false", gate_row.get("training_ready", "false") == "false"),
    ]
    for reason, passed in checks:
        if not passed:
            reasons.append(reason)

    can_stage = not reasons
    return {
        "sample_id": sample_id,
        "proposed_manifest_sample_id": proposed_id,
        "source_sample_id": sample_id,
        "source_repaired_sdf": source_repaired_sdf,
        "output_pre_reaction_sdf": output_pre_reaction_sdf,
        "proposed_ligand_sdf_path": output_pre_reaction_sdf,
        "dataset_candidate_gate_status": gate_row.get("dataset_candidate_gate_status", ""),
        "eligible_for_dataset_assembly_candidate_pool": gate_row.get(
            "eligible_for_dataset_assembly_candidate_pool", ""
        ),
        "qa_status": qa_row.get("qa_status", ""),
        "write_sdf_status": write_row.get("write_sdf_status", ""),
        "execution_plan_status": execution_row.get("execution_plan_status", ""),
        "planned_bond_order_operation": execution_row.get("planned_bond_order_operation", ""),
        "source_restore_bond_order": qa_row.get("source_restore_bond_order", ""),
        "output_restore_bond_order": qa_row.get("output_restore_bond_order", ""),
        "target_bond_order": qa_row.get("target_bond_order", ""),
        "covalent_bond_removed_in_ligand_only_sdf": "true",
        "pre_reaction_ligand_graph_ready": str(graph_ready).lower(),
        "can_stage_manifest_row": str(can_stage).lower(),
        "manifest_row_should_be_added_later": str(can_stage).lower(),
        "manifest_updated": "false",
        "current_manifest_contains_source_sample": str(current_contains_source).lower(),
        "current_manifest_contains_proposed_sample": str(current_contains_proposed).lower(),
        "proposed_manifest_record_type": "derived_pre_reaction_ligand_candidate",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "build_manifest_update_dry_run_not_training"
            if can_stage
            else "fix_manifest_staging_blockers_before_manifest_update"
        ),
    }


def build_staging_rows(
    *,
    gate_report_csv: str | Path,
    qa_report_csv: str | Path,
    write_sdf_report_csv: str | Path,
    execution_plan_csv: str | Path,
    current_manifest_csv: str | Path,
) -> list[dict[str, str]]:
    gate_rows = index_by_sample(read_csv(gate_report_csv), "gate_report_csv")
    qa_rows = index_by_sample(read_csv(qa_report_csv), "qa_report_csv")
    write_rows = index_by_sample(read_csv(write_sdf_report_csv), "write_sdf_report_csv")
    execution_rows = index_by_sample(read_csv(execution_plan_csv), "execution_plan_csv")
    ids = manifest_sample_ids(current_manifest_csv)
    rows: list[dict[str, str]] = []
    for sample_id in sorted(gate_rows):
        if sample_id not in qa_rows:
            raise ValueError(f"missing QA row for {sample_id}")
        if sample_id not in write_rows:
            raise ValueError(f"missing write-SDF row for {sample_id}")
        if sample_id not in execution_rows:
            raise ValueError(f"missing execution plan row for {sample_id}")
        rows.append(staging_row(gate_rows[sample_id], qa_rows[sample_id], write_rows[sample_id], execution_rows[sample_id], ids))
    return rows


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=STAGING_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Manifest Staging Plan",
        "",
        "This is a manifest staging plan only.",
        "",
        "- It does not modify manifest_real_small.csv.",
        "- It does not create a new manifest file.",
        "- It does not modify any SDF files.",
        "- It does not train or fine-tune any model.",
        "- Passing this plan means proposed manifest rows may be built in a later dry-run step.",
        "- Passing this plan does not mean the sample is training-ready.",
        "",
        "| sample_id | proposed_manifest_sample_id | proposed_ligand_sdf_path | can_stage_manifest_row | manifest_row_should_be_added_later | manifest_updated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["proposed_manifest_sample_id"],
                    row["proposed_ligand_sdf_path"],
                    row["can_stage_manifest_row"],
                    row["manifest_row_should_be_added_later"],
                    row["manifest_updated"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_can_stage = all(is_true(row["can_stage_manifest_row"]) for row in rows)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three pre-reaction artifacts can be staged for future manifest update dry-run."
                if all_can_stage
                else "- One or more pre-reaction artifacts are blocked before manifest staging."
            ),
            "- manifest_real_small.csv was not modified.",
            "- No new manifest was created.",
            "- No SDF was modified.",
            "- No training was run.",
            "- Next step is manifest update dry-run, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a pre-reaction manifest staging plan.")
    parser.add_argument("--gate_report_csv", type=Path, required=True)
    parser.add_argument("--qa_report_csv", type=Path, required=True)
    parser.add_argument("--write_sdf_report_csv", type=Path, required=True)
    parser.add_argument("--execution_plan_csv", type=Path, required=True)
    parser.add_argument("--current_manifest_csv", type=Path, required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command writes a manifest staging plan only.")
    print("warning: it does not modify manifest files or create a new manifest.")
    print("warning: it does not generate or modify SDF files.")
    rows = build_staging_rows(
        gate_report_csv=args.gate_report_csv,
        qa_report_csv=args.qa_report_csv,
        write_sdf_report_csv=args.write_sdf_report_csv,
        execution_plan_csv=args.execution_plan_csv,
        current_manifest_csv=args.current_manifest_csv,
    )
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote pre-reaction manifest staging plan: {args.output_csv}")
    print(f"wrote pre-reaction manifest staging summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"proposed_manifest_sample_id={row['proposed_manifest_sample_id']} "
            f"can_stage_manifest_row={row['can_stage_manifest_row']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
