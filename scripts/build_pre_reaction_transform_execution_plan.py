#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


APPROVAL_PHRASE = "APPROVE_PRE_REACTION_TRANSFORM_SDF_STEP_8P"
PLANNED_OUTPUT_ROOT = "data/derived/covalent_small/ligands_pre_reaction"

PLAN_COLUMNS = [
    "sample_id",
    "source_repaired_sdf",
    "source_repaired_sdf_sha256",
    "planned_output_pre_reaction_sdf",
    "dry_run_preview_status",
    "can_build_future_transform_script",
    "manual_covalent_bond_to_remove",
    "ligand_reactive_atom",
    "covalent_bond_removal_operation",
    "manual_bond_order_to_restore",
    "restore_bond_atom_1",
    "restore_bond_atom_2",
    "current_bond_order_in_repaired_sdf",
    "target_bond_order",
    "planned_bond_order_operation",
    "manual_atoms_requiring_charge_check",
    "manual_atoms_requiring_valence_check",
    "manual_boundary_resolution",
    "execution_plan_status",
    "write_sdf_allowed_by_plan",
    "explicit_human_approval_required_for_sdf_generation",
    "approval_phrase_required",
    "pre_reaction_sdf_generated",
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


def index_by_sample(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sample_id"]: row for row in rows}


def map_sdf_paths_to_samples(sample_ids: set[str], sdf_paths: list[Path]) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for sample_id in sample_ids:
        matches = [path for path in sdf_paths if path.name.startswith(sample_id)]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one SDF path for {sample_id}, found {len(matches)}")
        mapping[sample_id] = matches[0]
    return mapping


def planned_output_path(sample_id: str) -> str:
    return f"{PLANNED_OUTPUT_ROOT}/{sample_id}_pre_reaction.sdf"


def planned_bond_order_operation(preview: dict[str, str]) -> str:
    action = preview.get("bond_order_dry_run_action", "")
    if action == "already_target_order_no_change_needed":
        return "validate_existing_target_bond_order_and_copy_if_future_approved"
    if action == "would_restore_bond_order_to_target":
        return "set_bond_order_to_target_if_future_approved"
    return "blocked_no_future_transform"


def build_plan_row(
    *,
    preview: dict[str, str],
    decision: dict[str, str],
    source_sdf: Path,
) -> dict[str, str]:
    blocking_reasons: list[str] = []
    ready = (
        preview.get("dry_run_preview_status", "") == "preview_passed"
        and preview.get("can_build_future_transform_script", "") == "true"
    )
    if not ready:
        blocking_reasons.append("dry_run_preview_not_ready")
    plan_status = "ready_for_guarded_transform_script_design" if ready else "blocked"
    return {
        "sample_id": preview["sample_id"],
        "source_repaired_sdf": str(source_sdf),
        "source_repaired_sdf_sha256": sha256_file(source_sdf),
        "planned_output_pre_reaction_sdf": planned_output_path(preview["sample_id"]),
        "dry_run_preview_status": preview["dry_run_preview_status"],
        "can_build_future_transform_script": preview["can_build_future_transform_script"],
        "manual_covalent_bond_to_remove": preview["manual_covalent_bond_to_remove"],
        "ligand_reactive_atom": preview["ligand_reactive_atom"],
        "covalent_bond_removal_operation": (
            "protein_ligand_covalent_bond_removal_directive_recorded_not_applied_to_ligand_only_sdf"
        ),
        "manual_bond_order_to_restore": preview["manual_bond_order_to_restore"],
        "restore_bond_atom_1": preview["restore_bond_atom_1"],
        "restore_bond_atom_2": preview["restore_bond_atom_2"],
        "current_bond_order_in_repaired_sdf": preview["current_bond_order_in_repaired_sdf"],
        "target_bond_order": preview["target_bond_order"],
        "planned_bond_order_operation": planned_bond_order_operation(preview),
        "manual_atoms_requiring_charge_check": decision["manual_atoms_requiring_charge_check"],
        "manual_atoms_requiring_valence_check": decision["manual_atoms_requiring_valence_check"],
        "manual_boundary_resolution": decision["manual_boundary_resolution"],
        "execution_plan_status": plan_status,
        "write_sdf_allowed_by_plan": "false",
        "explicit_human_approval_required_for_sdf_generation": "true",
        "approval_phrase_required": APPROVAL_PHRASE,
        "pre_reaction_sdf_generated": "false",
        "raw_ligand_sdf_modified": "false",
        "repaired_trial_sdf_modified": "false",
        "manifest_modified": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(blocking_reasons),
        "recommended_next_action": (
            "implement_guarded_transform_script_but_do_not_run_write_mode"
            if ready
            else "fix_execution_plan_blockers"
        ),
    }


def build_plan_rows(
    *,
    preview_csv: str | Path,
    decision_csv: str | Path,
    sdf_paths: list[Path],
) -> list[dict[str, str]]:
    previews = read_csv(preview_csv)
    decisions = index_by_sample(read_csv(decision_csv))
    sdf_by_sample = map_sdf_paths_to_samples({row["sample_id"] for row in previews}, sdf_paths)
    rows: list[dict[str, str]] = []
    for preview in sorted(previews, key=lambda row: row["sample_id"]):
        sample_id = preview["sample_id"]
        if sample_id not in decisions:
            raise ValueError(f"missing decision row for {sample_id}")
        rows.append(
            build_plan_row(
                preview=preview,
                decision=decisions[sample_id],
                source_sdf=sdf_by_sample[sample_id],
            )
        )
    return rows


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PLAN_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Pre-Reaction Transform Execution Plan",
        "",
        "This is an execution plan only.",
        "",
        "- It does not create pre-reaction SDF files.",
        "- It does not modify raw ligand SDF files.",
        "- It does not modify repaired trial SDF files.",
        "- It does not modify manifest files.",
        "- It does not mark samples as training-ready.",
        "- SDF generation requires explicit future approval.",
        "",
        "| sample_id | source_repaired_sdf | planned_output_pre_reaction_sdf | planned_bond_order_operation | execution_plan_status | write_sdf_allowed_by_plan | approval_phrase_required |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["sample_id"],
                    row["source_repaired_sdf"],
                    row["planned_output_pre_reaction_sdf"],
                    row["planned_bond_order_operation"],
                    row["execution_plan_status"],
                    row["write_sdf_allowed_by_plan"],
                    row["approval_phrase_required"],
                ]
            )
            + " |"
        )
    all_ready = all(row["execution_plan_status"] == "ready_for_guarded_transform_script_design" for row in rows)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            f"- Execution plan is ready for guarded transform script design: {str(all_ready).lower()}.",
            "- No pre-reaction SDF was generated.",
            "- No sample is training-ready.",
            f"- Future SDF generation requires explicit approval phrase {APPROVAL_PHRASE}.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build guarded pre-reaction transform execution plan.")
    parser.add_argument("--preview_csv", type=Path, required=True)
    parser.add_argument("--decision_csv", type=Path, required=True)
    parser.add_argument("--sdf_paths", type=Path, nargs="+", required=True)
    parser.add_argument("--output_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command writes an execution plan only.")
    print("warning: it does not generate pre-reaction SDF files.")
    print("warning: it does not create the planned output SDF directory.")
    rows = build_plan_rows(preview_csv=args.preview_csv, decision_csv=args.decision_csv, sdf_paths=args.sdf_paths)
    write_csv(rows, args.output_csv)
    write_markdown(build_markdown(rows), args.output_md)
    print(f"wrote pre-reaction transform execution plan: {args.output_csv}")
    print(f"wrote pre-reaction transform execution plan Markdown: {args.output_md}")
    for row in rows:
        print(
            f"{row['sample_id']}: "
            f"execution_plan_status={row['execution_plan_status']} "
            f"planned_bond_order_operation={row['planned_bond_order_operation']} "
            f"write_sdf_allowed_by_plan={row['write_sdf_allowed_by_plan']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
