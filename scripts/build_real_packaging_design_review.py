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
    "design_review_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "planned_package_root",
    "planned_protein_relative_path",
    "planned_ligand_relative_path",
    "planned_metadata_relative_path",
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
    "candidate_type",
    "packaging_dry_run_stage",
    "design_review_stage",
    "ready_for_real_packaging_design_review",
    "files_copied",
    "package_archive_created",
    "real_dataset_generated",
    "training_ready",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "qa_report_row_found_once",
    "packaging_plan_row_found_once",
    "final_readiness_candidate_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "qa_status_passed",
    "ready_for_real_packaging_planning_later_confirmed",
    "source_mapping_valid",
    "path_consistency_passed",
    "hash_consistency_passed",
    "current_protein_hash_matches_plan",
    "current_ligand_hash_matches_plan",
    "graph_counts_positive",
    "reactive_residue_found",
    "reactive_atom_found",
    "planned_package_root",
    "planned_protein_relative_path",
    "planned_ligand_relative_path",
    "planned_metadata_relative_path",
    "design_plan_row_written",
    "design_review_status",
    "ready_for_real_packaging_design_review",
    "manifest_modified",
    "sdf_modified",
    "sdf_generated",
    "files_copied",
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


def planned_paths(plan: dict[str, str]) -> tuple[str, str, str]:
    source_id = plan.get("source_sample_id", "")
    pre_reaction_id = plan.get("pre_reaction_sample_id", "")
    return (
        f"proteins/{source_id}.pdb",
        f"ligands_pre_reaction/{pre_reaction_id}.sdf",
        f"metadata/{pre_reaction_id}.json",
    )


def build_plan_row(plan: dict[str, str]) -> dict[str, str]:
    protein_rel, ligand_rel, metadata_rel = planned_paths(plan)
    return {
        "design_review_plan_id": plan["packaging_plan_id"],
        "source_sample_id": plan["source_sample_id"],
        "pre_reaction_sample_id": plan["pre_reaction_sample_id"],
        "planned_package_root": PLANNED_PACKAGE_ROOT,
        "planned_protein_relative_path": protein_rel,
        "planned_ligand_relative_path": ligand_rel,
        "planned_metadata_relative_path": metadata_rel,
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
        "candidate_type": plan["candidate_type"],
        "packaging_dry_run_stage": plan["packaging_dry_run_stage"],
        "design_review_stage": "real_packaging_design_review_only_not_training",
        "ready_for_real_packaging_design_review": "true",
        "files_copied": "false",
        "package_archive_created": "false",
        "real_dataset_generated": "false",
        "training_ready": "false",
    }


def evaluate_candidate(
    candidate_id: str,
    qa_by_id: dict[str, list[dict[str, str]]],
    plan_by_id: dict[str, list[dict[str, str]]],
    final_by_id: dict[str, list[dict[str, str]]],
    manifest_by_id: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, str], dict[str, str] | None]:
    source_id = TARGETS[candidate_id]
    qa = one(qa_by_id, candidate_id)
    plan = one(plan_by_id, candidate_id)
    final = one(final_by_id, candidate_id)
    manifest_candidate = one(manifest_by_id, candidate_id)
    protein_rel, ligand_rel, metadata_rel = planned_paths(plan)
    protein_path = plan.get("protein_pdb_path", "")
    ligand_path = plan.get("ligand_sdf_path", "")
    protein_exists = path_exists(protein_path)
    ligand_exists = path_exists(ligand_path)
    path_consistency = (
        plan.get("protein_pdb_path", "")
        == final.get("protein_pdb_path", "")
        == manifest_candidate.get("protein_pdb_path", "")
        and plan.get("ligand_sdf_path", "")
        == final.get("ligand_sdf_path", "")
        == manifest_candidate.get("ligand_sdf_path", "")
    )
    hash_consistency = (
        plan.get("protein_pdb_sha256", "")
        == final.get("protein_pdb_sha256", "")
        and plan.get("ligand_sdf_sha256", "")
        == final.get("ligand_sdf_sha256", "")
        and bool(plan.get("protein_pdb_sha256", ""))
        and bool(plan.get("ligand_sdf_sha256", ""))
    )
    current_protein_hash_matches = protein_exists and sha256_file(protein_path) == plan.get("protein_pdb_sha256", "")
    current_ligand_hash_matches = ligand_exists and sha256_file(ligand_path) == plan.get("ligand_sdf_sha256", "")
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
    source_mapping_valid = plan.get("source_sample_id", "") == source_id
    checks = [
        ("qa_report_row_not_found_once", found_once(qa_by_id, candidate_id)),
        ("packaging_plan_row_not_found_once", found_once(plan_by_id, candidate_id)),
        ("final_readiness_candidate_not_found_once", found_once(final_by_id, candidate_id)),
        ("manifest_candidate_row_not_found_once", found_once(manifest_by_id, candidate_id)),
        ("manifest_source_row_not_found_once", found_once(manifest_by_id, source_id)),
        ("qa_status_not_passed", qa.get("packaging_dry_run_qa_status", "") == "dataset_packaging_dry_run_qa_passed"),
        ("ready_for_real_packaging_planning_later_not_true", qa.get("ready_for_real_packaging_planning_later", "") == "true"),
        ("qa_real_dataset_generated_false_not_true", qa.get("real_dataset_generated_false", "") == "true"),
        ("qa_training_ready_not_false", qa.get("training_ready", "") == "false"),
        ("qa_files_copied_false_not_true", qa.get("files_copied_false", "") == "true"),
        ("qa_package_archive_created_false_not_true", qa.get("package_archive_created_false", "") == "true"),
        ("plan_ready_for_real_packaging_later_not_true", plan.get("ready_for_real_packaging_later", "") == "true"),
        ("plan_real_dataset_generated_not_false", plan.get("real_dataset_generated", "") == "false"),
        ("plan_training_ready_not_false", plan.get("training_ready", "") == "false"),
        ("final_training_ready_not_false", final.get("training_ready", "") == "false"),
        ("source_mapping_invalid", source_mapping_valid),
        ("path_consistency_failed", path_consistency),
        ("hash_consistency_failed", hash_consistency),
        ("protein_pdb_missing", protein_exists),
        ("ligand_sdf_missing", ligand_exists),
        ("current_protein_hash_mismatch_plan", current_protein_hash_matches),
        ("current_ligand_hash_mismatch_plan", current_ligand_hash_matches),
        ("graph_counts_not_positive", graph_counts_positive),
        ("reactive_residue_not_found", plan.get("reactive_residue_found", "") == "true"),
        ("reactive_atom_not_found", plan.get("reactive_atom_found", "") == "true"),
    ]
    reasons = [reason for reason, passed in checks if not passed]
    passed = not reasons
    report = {
        "candidate_id": candidate_id,
        "source_sample_id": plan.get("source_sample_id", source_id),
        "pre_reaction_sample_id": plan.get("pre_reaction_sample_id", candidate_id),
        "qa_report_row_found_once": str(found_once(qa_by_id, candidate_id)).lower(),
        "packaging_plan_row_found_once": str(found_once(plan_by_id, candidate_id)).lower(),
        "final_readiness_candidate_found_once": str(found_once(final_by_id, candidate_id)).lower(),
        "manifest_candidate_row_found_once": str(found_once(manifest_by_id, candidate_id)).lower(),
        "manifest_source_row_found_once": str(found_once(manifest_by_id, source_id)).lower(),
        "qa_status_passed": str(qa.get("packaging_dry_run_qa_status", "") == "dataset_packaging_dry_run_qa_passed").lower(),
        "ready_for_real_packaging_planning_later_confirmed": str(qa.get("ready_for_real_packaging_planning_later", "") == "true").lower(),
        "source_mapping_valid": str(source_mapping_valid).lower(),
        "path_consistency_passed": str(path_consistency).lower(),
        "hash_consistency_passed": str(hash_consistency).lower(),
        "current_protein_hash_matches_plan": str(current_protein_hash_matches).lower(),
        "current_ligand_hash_matches_plan": str(current_ligand_hash_matches).lower(),
        "graph_counts_positive": str(graph_counts_positive).lower(),
        "reactive_residue_found": plan.get("reactive_residue_found", "false"),
        "reactive_atom_found": plan.get("reactive_atom_found", "false"),
        "planned_package_root": PLANNED_PACKAGE_ROOT,
        "planned_protein_relative_path": protein_rel,
        "planned_ligand_relative_path": ligand_rel,
        "planned_metadata_relative_path": metadata_rel,
        "design_plan_row_written": str(passed).lower(),
        "design_review_status": "real_packaging_design_review_passed" if passed else "blocked",
        "ready_for_real_packaging_design_review": str(passed).lower(),
        "manifest_modified": "false",
        "sdf_modified": "false",
        "sdf_generated": "false",
        "files_copied": "false",
        "package_archive_created": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "prepare_real_packaging_execution_gate_not_training"
            if passed
            else "fix_real_packaging_design_review_blockers"
        ),
    }
    return report, build_plan_row(plan) if passed else None


def build_design_review(
    *,
    packaging_qa_report_csv: str | Path,
    packaging_plan_csv: str | Path,
    final_readiness_candidates_csv: str | Path,
    manifest_csv: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    qa_by_id = index_many(read_csv(packaging_qa_report_csv), "candidate_id")
    plan_by_id = index_many(read_csv(packaging_plan_csv), "packaging_plan_id")
    final_by_id = index_many(read_csv(final_readiness_candidates_csv), "final_readiness_candidate_id")
    manifest_by_id = index_many(read_csv(manifest_csv), "sample_id")
    reports = []
    design_plan = []
    for candidate_id in sorted(TARGETS):
        report, plan_row = evaluate_candidate(candidate_id, qa_by_id, plan_by_id, final_by_id, manifest_by_id)
        reports.append(report)
        if plan_row is not None:
            design_plan.append(plan_row)
    return reports, design_plan


def write_csv(rows: list[dict[str, str]], output_csv: str | Path, fieldnames: list[str]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(reports: list[dict[str, str]], design_plan: list[dict[str, str]]) -> str:
    lines = [
        "# Real Packaging Design Review Summary",
        "",
        "This is real packaging design review only.",
        "",
        "- It reads packaging dry-run QA outputs.",
        "- It does not modify manifest files.",
        "- It does not modify or generate SDF files.",
        "- It does not copy protein or ligand files.",
        "- It does not create package archives.",
        "- It does not generate real training datasets.",
        "- It does not train or fine-tune any model.",
        "- Passing this review means candidates can enter real packaging execution gate.",
        "- Passing this review still does not mean the samples are training-ready.",
        "",
        "## Planned Layout",
        "",
        f"- planned_package_root: `{PLANNED_PACKAGE_ROOT}`",
        "- planned_protein_relative_path pattern: `proteins/{source_sample_id}.pdb`",
        "- planned_ligand_relative_path pattern: `ligands_pre_reaction/{pre_reaction_sample_id}.sdf`",
        "- planned_metadata_relative_path pattern: `metadata/{pre_reaction_sample_id}.json`",
        "",
        "| candidate_id | source_sample_id | design_review_status | ready_for_real_packaging_design_review | files_copied | package_archive_created | real_dataset_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in reports:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["source_sample_id"],
                    row["design_review_status"],
                    row["ready_for_real_packaging_design_review"],
                    row["files_copied"],
                    row["package_archive_created"],
                    row["real_dataset_generated"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(row["design_review_status"] == "real_packaging_design_review_passed" for row in reports)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three candidates passed real packaging design review."
                if all_passed
                else "- One or more candidates are blocked by real packaging design review."
            ),
            f"- Design plan CSV contains exactly 3 rows: {str(len(design_plan) == 3).lower()}.",
            "- No files were copied.",
            "- No package archive was created.",
            "- Manifest was not modified.",
            "- No SDF files were modified or generated.",
            "- No real dataset was generated.",
            "- No training was run.",
            "- Next step is real packaging execution gate, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build real packaging design review outputs.")
    parser.add_argument("--packaging_qa_report_csv", type=Path, required=True)
    parser.add_argument("--packaging_plan_csv", type=Path, required=True)
    parser.add_argument("--final_readiness_candidates_csv", type=Path, required=True)
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--output_design_plan_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command performs real packaging design review only.")
    print("warning: it does not modify manifest or SDF files.")
    print("warning: it does not copy input files or create archives.")
    print("warning: it does not generate real training datasets.")
    reports, design_plan = build_design_review(
        packaging_qa_report_csv=args.packaging_qa_report_csv,
        packaging_plan_csv=args.packaging_plan_csv,
        final_readiness_candidates_csv=args.final_readiness_candidates_csv,
        manifest_csv=args.manifest_csv,
    )
    write_csv(design_plan, args.output_design_plan_csv, PLAN_COLUMNS)
    write_csv(reports, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports, design_plan), args.output_md)
    print(f"wrote real packaging design review plan: {args.output_design_plan_csv}")
    print(f"wrote real packaging design review report: {args.output_report_csv}")
    print(f"wrote real packaging design review summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['candidate_id']}: "
            f"design_review_status={row['design_review_status']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
