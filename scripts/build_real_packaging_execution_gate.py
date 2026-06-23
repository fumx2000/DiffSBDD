#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


TARGETS = {
    "BTK_C481_6DI9_pre_reaction": "BTK_C481_6DI9",
    "KRAS_G12C_5F2E_pre_reaction": "KRAS_G12C_5F2E",
    "KRAS_G12C_6OIM_pre_reaction": "KRAS_G12C_6OIM",
}

PLANNED_PACKAGE_ROOT = "data/derived/covalent_small/packaging_real_review_only"

PLAN_COLUMNS = [
    "execution_gate_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "planned_package_root",
    "planned_protein_relative_path",
    "planned_ligand_relative_path",
    "planned_metadata_relative_path",
    "planned_protein_destination_path",
    "planned_ligand_destination_path",
    "planned_metadata_destination_path",
    "protein_pdb_path",
    "protein_pdb_sha256",
    "ligand_sdf_path",
    "ligand_sdf_sha256",
    "ligand_atom_count",
    "ligand_heavy_atom_count",
    "ligand_bond_count",
    "protein_atom_count",
    "protein_residue_count",
    "reactive_residue_chain",
    "reactive_residue_id",
    "reactive_residue_type",
    "reactive_atom_name",
    "ligand_reactive_atom_id",
    "scaffold_atoms",
    "linker_atoms",
    "warhead_atoms",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "execution_gate_stage",
    "explicit_approval_required_before_copy",
    "ready_for_real_packaging_execution_after_approval",
    "directories_created",
    "files_copied",
    "metadata_written",
    "package_archive_created",
    "real_dataset_generated",
    "training_ready",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "design_plan_row_found_once",
    "design_report_row_found_once",
    "packaging_qa_report_row_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "design_review_status_passed",
    "design_plan_row_written_confirmed",
    "ready_for_real_packaging_design_review_confirmed",
    "packaging_qa_status_passed",
    "ready_for_real_packaging_planning_later_confirmed",
    "planned_layout_valid",
    "source_mapping_valid",
    "protein_pdb_exists",
    "ligand_sdf_exists",
    "current_protein_hash_matches_design_plan",
    "current_ligand_hash_matches_design_plan",
    "manifest_candidate_paths_match_design_plan",
    "graph_counts_positive",
    "execution_gate_plan_row_written",
    "execution_gate_status",
    "explicit_approval_required_before_copy",
    "ready_for_real_packaging_execution_after_approval",
    "directories_created",
    "files_copied",
    "metadata_written",
    "package_archive_created",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "blocking_reasons",
    "recommended_next_action",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def index_many(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    indexed: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        indexed.setdefault(row.get(key, ""), []).append(row)
    return indexed


def one(indexed: dict[str, list[dict[str, str]]], key: str) -> dict[str, str]:
    rows = indexed.get(key, [])
    return rows[0] if len(rows) == 1 else {}


def found_once(indexed: dict[str, list[dict[str, str]]], key: str) -> bool:
    return len(indexed.get(key, [])) == 1


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def to_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def positive(value: str) -> bool:
    number = to_int(value)
    return number is not None and number > 0


def path_exists(path_value: str) -> bool:
    return bool(path_value) and Path(path_value).exists()


def destination(root: str, relative_path: str) -> str:
    return f"{root.rstrip('/')}/{relative_path.lstrip('/')}"


def expected_layout(plan: dict[str, str]) -> tuple[str, str, str, str]:
    source = plan.get("source_sample_id", "")
    pre_reaction = plan.get("pre_reaction_sample_id", "")
    return (
        PLANNED_PACKAGE_ROOT,
        f"proteins/{source}.pdb",
        f"ligands_pre_reaction/{pre_reaction}.sdf",
        f"metadata/{pre_reaction}.json",
    )


def build_plan_row(plan: dict[str, str]) -> dict[str, str]:
    root = plan["planned_package_root"]
    protein_rel = plan["planned_protein_relative_path"]
    ligand_rel = plan["planned_ligand_relative_path"]
    metadata_rel = plan["planned_metadata_relative_path"]
    return {
        "execution_gate_plan_id": plan["design_review_plan_id"],
        "source_sample_id": plan["source_sample_id"],
        "pre_reaction_sample_id": plan["pre_reaction_sample_id"],
        "planned_package_root": root,
        "planned_protein_relative_path": protein_rel,
        "planned_ligand_relative_path": ligand_rel,
        "planned_metadata_relative_path": metadata_rel,
        "planned_protein_destination_path": destination(root, protein_rel),
        "planned_ligand_destination_path": destination(root, ligand_rel),
        "planned_metadata_destination_path": destination(root, metadata_rel),
        "protein_pdb_path": plan["protein_pdb_path"],
        "protein_pdb_sha256": plan["protein_pdb_sha256"],
        "ligand_sdf_path": plan["ligand_sdf_path"],
        "ligand_sdf_sha256": plan["ligand_sdf_sha256"],
        "ligand_atom_count": plan["ligand_atom_count"],
        "ligand_heavy_atom_count": plan["ligand_heavy_atom_count"],
        "ligand_bond_count": plan["ligand_bond_count"],
        "protein_atom_count": plan["protein_atom_count"],
        "protein_residue_count": plan["protein_residue_count"],
        "reactive_residue_chain": plan["reactive_residue_chain"],
        "reactive_residue_id": plan["reactive_residue_id"],
        "reactive_residue_type": plan["reactive_residue_type"],
        "reactive_atom_name": plan["reactive_atom_name"],
        "ligand_reactive_atom_id": plan["ligand_reactive_atom_id"],
        "scaffold_atoms": plan["scaffold_atoms"],
        "linker_atoms": plan["linker_atoms"],
        "warhead_atoms": plan["warhead_atoms"],
        "scaffold_atom_count": plan["scaffold_atom_count"],
        "linker_atom_count": plan["linker_atom_count"],
        "warhead_atom_count": plan["warhead_atom_count"],
        "execution_gate_stage": "real_packaging_execution_gate_only_not_training",
        "explicit_approval_required_before_copy": "true",
        "ready_for_real_packaging_execution_after_approval": "true",
        "directories_created": "false",
        "files_copied": "false",
        "metadata_written": "false",
        "package_archive_created": "false",
        "real_dataset_generated": "false",
        "training_ready": "false",
    }


def evaluate_candidate(
    candidate_id: str,
    design_plan_by_id: dict[str, list[dict[str, str]]],
    design_report_by_id: dict[str, list[dict[str, str]]],
    packaging_qa_by_id: dict[str, list[dict[str, str]]],
    manifest_by_id: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, str], dict[str, str] | None]:
    source = TARGETS[candidate_id]
    plan = one(design_plan_by_id, candidate_id)
    design_report = one(design_report_by_id, candidate_id)
    packaging_qa = one(packaging_qa_by_id, candidate_id)
    manifest_candidate = one(manifest_by_id, candidate_id)
    root, protein_rel, ligand_rel, metadata_rel = expected_layout(plan)
    planned_layout_valid = (
        plan.get("planned_package_root", "") == root
        and plan.get("planned_protein_relative_path", "") == protein_rel
        and plan.get("planned_ligand_relative_path", "") == ligand_rel
        and plan.get("planned_metadata_relative_path", "") == metadata_rel
    )
    protein_path = plan.get("protein_pdb_path", "")
    ligand_path = plan.get("ligand_sdf_path", "")
    protein_exists = path_exists(protein_path)
    ligand_exists = path_exists(ligand_path)
    protein_hash_matches = protein_exists and sha256_file(protein_path) == plan.get("protein_pdb_sha256", "")
    ligand_hash_matches = ligand_exists and sha256_file(ligand_path) == plan.get("ligand_sdf_sha256", "")
    manifest_paths_match = (
        manifest_candidate.get("protein_pdb_path", "") == protein_path
        and manifest_candidate.get("ligand_sdf_path", "") == ligand_path
    )
    graph_counts_positive = all(
        positive(plan.get(field, ""))
        for field in [
            "ligand_atom_count",
            "ligand_heavy_atom_count",
            "ligand_bond_count",
            "protein_atom_count",
            "protein_residue_count",
        ]
    )
    source_mapping_valid = plan.get("source_sample_id", "") == source
    checks = [
        ("design_plan_row_not_found_once", found_once(design_plan_by_id, candidate_id)),
        ("design_report_row_not_found_once", found_once(design_report_by_id, candidate_id)),
        ("packaging_qa_report_row_not_found_once", found_once(packaging_qa_by_id, candidate_id)),
        ("manifest_candidate_row_not_found_once", found_once(manifest_by_id, candidate_id)),
        ("manifest_source_row_not_found_once", found_once(manifest_by_id, source)),
        ("design_review_status_not_passed", design_report.get("design_review_status", "") == "real_packaging_design_review_passed"),
        ("design_plan_row_written_not_true", design_report.get("design_plan_row_written", "") == "true"),
        ("ready_for_real_packaging_design_review_not_true", design_report.get("ready_for_real_packaging_design_review", "") == "true"),
        ("design_files_copied_not_false", design_report.get("files_copied", "") == "false"),
        ("design_package_archive_created_not_false", design_report.get("package_archive_created", "") == "false"),
        ("design_real_dataset_generated_not_false", design_report.get("real_dataset_generated", "") == "false"),
        ("design_training_ready_not_false", design_report.get("training_ready", "") == "false"),
        ("packaging_qa_status_not_passed", packaging_qa.get("packaging_dry_run_qa_status", "") == "dataset_packaging_dry_run_qa_passed"),
        ("ready_for_real_packaging_planning_later_not_true", packaging_qa.get("ready_for_real_packaging_planning_later", "") == "true"),
        ("qa_real_dataset_generated_false_not_true", packaging_qa.get("real_dataset_generated_false", "") == "true"),
        ("qa_training_ready_not_false", packaging_qa.get("training_ready", "") == "false"),
        ("planned_layout_invalid", planned_layout_valid),
        ("source_mapping_invalid", source_mapping_valid),
        ("protein_pdb_missing", protein_exists),
        ("ligand_sdf_missing", ligand_exists),
        ("current_protein_hash_mismatch_design_plan", protein_hash_matches),
        ("current_ligand_hash_mismatch_design_plan", ligand_hash_matches),
        ("manifest_candidate_paths_mismatch_design_plan", manifest_paths_match),
        ("graph_counts_not_positive", graph_counts_positive),
    ]
    reasons = [reason for reason, passed in checks if not passed]
    passed = not reasons
    report = {
        "candidate_id": candidate_id,
        "source_sample_id": plan.get("source_sample_id", source),
        "pre_reaction_sample_id": plan.get("pre_reaction_sample_id", candidate_id),
        "design_plan_row_found_once": str(found_once(design_plan_by_id, candidate_id)).lower(),
        "design_report_row_found_once": str(found_once(design_report_by_id, candidate_id)).lower(),
        "packaging_qa_report_row_found_once": str(found_once(packaging_qa_by_id, candidate_id)).lower(),
        "manifest_candidate_row_found_once": str(found_once(manifest_by_id, candidate_id)).lower(),
        "manifest_source_row_found_once": str(found_once(manifest_by_id, source)).lower(),
        "design_review_status_passed": str(design_report.get("design_review_status", "") == "real_packaging_design_review_passed").lower(),
        "design_plan_row_written_confirmed": str(design_report.get("design_plan_row_written", "") == "true").lower(),
        "ready_for_real_packaging_design_review_confirmed": str(design_report.get("ready_for_real_packaging_design_review", "") == "true").lower(),
        "packaging_qa_status_passed": str(packaging_qa.get("packaging_dry_run_qa_status", "") == "dataset_packaging_dry_run_qa_passed").lower(),
        "ready_for_real_packaging_planning_later_confirmed": str(packaging_qa.get("ready_for_real_packaging_planning_later", "") == "true").lower(),
        "planned_layout_valid": str(planned_layout_valid).lower(),
        "source_mapping_valid": str(source_mapping_valid).lower(),
        "protein_pdb_exists": str(protein_exists).lower(),
        "ligand_sdf_exists": str(ligand_exists).lower(),
        "current_protein_hash_matches_design_plan": str(protein_hash_matches).lower(),
        "current_ligand_hash_matches_design_plan": str(ligand_hash_matches).lower(),
        "manifest_candidate_paths_match_design_plan": str(manifest_paths_match).lower(),
        "graph_counts_positive": str(graph_counts_positive).lower(),
        "execution_gate_plan_row_written": str(passed).lower(),
        "execution_gate_status": "real_packaging_execution_gate_passed" if passed else "blocked",
        "explicit_approval_required_before_copy": str(passed).lower(),
        "ready_for_real_packaging_execution_after_approval": str(passed).lower(),
        "directories_created": "false",
        "files_copied": "false",
        "metadata_written": "false",
        "package_archive_created": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "await_explicit_approval_for_real_packaging_execution"
            if passed
            else "fix_real_packaging_execution_gate_blockers"
        ),
    }
    return report, build_plan_row(plan) if passed else None


def build_execution_gate(
    *,
    design_review_plan_csv: str | Path,
    design_review_report_csv: str | Path,
    packaging_qa_report_csv: str | Path,
    manifest_csv: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    design_plan_by_id = index_many(read_csv(design_review_plan_csv), "design_review_plan_id")
    design_report_by_id = index_many(read_csv(design_review_report_csv), "candidate_id")
    packaging_qa_by_id = index_many(read_csv(packaging_qa_report_csv), "candidate_id")
    manifest_by_id = index_many(read_csv(manifest_csv), "sample_id")
    reports = []
    execution_plan = []
    for candidate_id in sorted(TARGETS):
        report, plan = evaluate_candidate(candidate_id, design_plan_by_id, design_report_by_id, packaging_qa_by_id, manifest_by_id)
        reports.append(report)
        if plan is not None:
            execution_plan.append(plan)
    return reports, execution_plan


def write_csv(rows: list[dict[str, str]], output_csv: str | Path, fieldnames: list[str]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(reports: list[dict[str, str]], execution_plan: list[dict[str, str]]) -> str:
    lines = [
        "# Real Packaging Execution Gate Summary",
        "",
        "This is real packaging execution gate only.",
        "",
        "- It reads real packaging design review outputs.",
        "- It does not modify manifest files.",
        "- It does not modify or generate SDF files.",
        "- It does not create directories.",
        "- It does not copy protein or ligand files.",
        "- It does not write metadata JSON files.",
        "- It does not create package archives.",
        "- It does not generate real training datasets.",
        "- It does not train or fine-tune any model.",
        "- Passing this gate means candidates can be packaged only after explicit approval.",
        "- Passing this gate still does not mean the samples are training-ready.",
        "",
        "## Planned Execution Layout",
        "",
        f"- planned_package_root: `{PLANNED_PACKAGE_ROOT}`",
        "- planned protein destination pattern: `data/derived/covalent_small/packaging_real_review_only/proteins/{source_sample_id}.pdb`",
        "- planned ligand destination pattern: `data/derived/covalent_small/packaging_real_review_only/ligands_pre_reaction/{pre_reaction_sample_id}.sdf`",
        "- planned metadata destination pattern: `data/derived/covalent_small/packaging_real_review_only/metadata/{pre_reaction_sample_id}.json`",
        "",
        "| candidate_id | source_sample_id | execution_gate_status | explicit_approval_required_before_copy | ready_for_real_packaging_execution_after_approval | directories_created | files_copied | metadata_written | real_dataset_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in reports:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["source_sample_id"],
                    row["execution_gate_status"],
                    row["explicit_approval_required_before_copy"],
                    row["ready_for_real_packaging_execution_after_approval"],
                    row["directories_created"],
                    row["files_copied"],
                    row["metadata_written"],
                    row["real_dataset_generated"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(row["execution_gate_status"] == "real_packaging_execution_gate_passed" for row in reports)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three candidates passed real packaging execution gate."
                if all_passed
                else "- One or more candidates are blocked by real packaging execution gate."
            ),
            f"- Execution plan CSV contains exactly 3 rows: {str(len(execution_plan) == 3).lower()}.",
            "- Explicit approval is required before any real packaging execution.",
            "- No directories were created.",
            "- No files were copied.",
            "- No metadata JSON files were written.",
            "- No package archive was created.",
            "- Manifest was not modified.",
            "- No SDF files were modified or generated.",
            "- No real dataset was generated.",
            "- No training was run.",
            "- Next step is explicit approval for real packaging execution, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build real packaging execution gate outputs.")
    parser.add_argument("--design_review_plan_csv", type=Path, required=True)
    parser.add_argument("--design_review_report_csv", type=Path, required=True)
    parser.add_argument("--packaging_qa_report_csv", type=Path, required=True)
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--output_execution_plan_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command performs real packaging execution gating only.")
    print("warning: it does not modify manifest or SDF files.")
    print("warning: it does not create directories, write metadata, copy files, or create archives.")
    print("warning: it does not generate real training datasets.")
    reports, execution_plan = build_execution_gate(
        design_review_plan_csv=args.design_review_plan_csv,
        design_review_report_csv=args.design_review_report_csv,
        packaging_qa_report_csv=args.packaging_qa_report_csv,
        manifest_csv=args.manifest_csv,
    )
    write_csv(execution_plan, args.output_execution_plan_csv, PLAN_COLUMNS)
    write_csv(reports, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports, execution_plan), args.output_md)
    print(f"wrote real packaging execution gate plan: {args.output_execution_plan_csv}")
    print(f"wrote real packaging execution gate report: {args.output_report_csv}")
    print(f"wrote real packaging execution gate summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['candidate_id']}: "
            f"execution_gate_status={row['execution_gate_status']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
