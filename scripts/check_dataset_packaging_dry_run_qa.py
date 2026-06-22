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

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "packaging_plan_row_found_once",
    "packaging_report_row_found_once",
    "final_readiness_candidate_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "source_mapping_valid",
    "path_consistency_passed",
    "hash_consistency_passed",
    "current_protein_hash_matches_plan",
    "current_ligand_hash_matches_plan",
    "manifest_candidate_paths_match_plan",
    "packaging_dry_run_status_passed",
    "packaging_plan_row_written_confirmed",
    "ready_for_real_packaging_later_confirmed",
    "files_copied_false",
    "package_archive_created_false",
    "manifest_modified_false",
    "sdf_modified_false",
    "sdf_generated_false",
    "real_dataset_generated_false",
    "pre_reaction_transform_ready",
    "training_ready",
    "graph_counts_positive",
    "reactive_residue_found",
    "reactive_atom_found",
    "packaging_dry_run_qa_status",
    "ready_for_real_packaging_planning_later",
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


def evaluate_candidate(
    candidate_id: str,
    plan_by_id: dict[str, list[dict[str, str]]],
    report_by_id: dict[str, list[dict[str, str]]],
    final_by_id: dict[str, list[dict[str, str]]],
    manifest_by_id: dict[str, list[dict[str, str]]],
) -> dict[str, str]:
    source_id = TARGETS[candidate_id]
    plan = one(plan_by_id, candidate_id)
    packaging_report = one(report_by_id, candidate_id)
    final = one(final_by_id, candidate_id)
    manifest_candidate = one(manifest_by_id, candidate_id)
    protein_path = plan.get("protein_pdb_path", "")
    ligand_path = plan.get("ligand_sdf_path", "")
    protein_exists = path_exists(protein_path)
    ligand_exists = path_exists(ligand_path)
    current_protein_hash_matches = protein_exists and sha256_file(protein_path) == plan.get("protein_pdb_sha256", "")
    current_ligand_hash_matches = ligand_exists and sha256_file(ligand_path) == plan.get("ligand_sdf_sha256", "")
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
    manifest_paths_match = (
        manifest_candidate.get("protein_pdb_path", "") == protein_path
        and manifest_candidate.get("ligand_sdf_path", "") == ligand_path
    )
    checks = [
        ("packaging_plan_row_not_found_once", found_once(plan_by_id, candidate_id)),
        ("packaging_report_row_not_found_once", found_once(report_by_id, candidate_id)),
        ("final_readiness_candidate_not_found_once", found_once(final_by_id, candidate_id)),
        ("manifest_candidate_row_not_found_once", found_once(manifest_by_id, candidate_id)),
        ("manifest_source_row_not_found_once", found_once(manifest_by_id, source_id)),
        ("packaging_plan_id_mismatch_pre_reaction_sample_id", plan.get("pre_reaction_sample_id", "") == candidate_id),
        ("source_mapping_invalid", source_mapping_valid),
        ("path_consistency_failed", path_consistency),
        ("hash_consistency_failed", hash_consistency),
        ("protein_pdb_missing", protein_exists),
        ("ligand_sdf_missing", ligand_exists),
        ("current_protein_hash_mismatch_plan", current_protein_hash_matches),
        ("current_ligand_hash_mismatch_plan", current_ligand_hash_matches),
        ("manifest_candidate_paths_mismatch_plan", manifest_paths_match),
        ("packaging_dry_run_stage_invalid", plan.get("packaging_dry_run_stage", "") == "packaging_dry_run_plan_only_not_training"),
        ("ready_for_real_packaging_later_not_true", plan.get("ready_for_real_packaging_later", "") == "true"),
        ("plan_real_dataset_generated_not_false", plan.get("real_dataset_generated", "") == "false"),
        ("plan_training_ready_not_false", plan.get("training_ready", "") == "false"),
        ("packaging_dry_run_status_not_passed", packaging_report.get("packaging_dry_run_status", "") == "dataset_packaging_dry_run_passed"),
        ("packaging_plan_row_written_not_true", packaging_report.get("packaging_plan_row_written", "") == "true"),
        ("files_copied_not_false", packaging_report.get("files_copied", "") == "false"),
        ("package_archive_created_not_false", packaging_report.get("package_archive_created", "") == "false"),
        ("manifest_modified_not_false", packaging_report.get("manifest_modified", "") == "false"),
        ("sdf_modified_not_false", packaging_report.get("sdf_modified", "") == "false"),
        ("sdf_generated_not_false", packaging_report.get("sdf_generated", "") == "false"),
        ("report_real_dataset_generated_not_false", packaging_report.get("real_dataset_generated", "") == "false"),
        ("report_training_ready_not_false", packaging_report.get("training_ready", "") == "false"),
        ("graph_counts_not_positive", graph_counts_positive),
        ("reactive_residue_not_found", plan.get("reactive_residue_found", "") == "true"),
        ("reactive_atom_not_found", plan.get("reactive_atom_found", "") == "true"),
    ]
    reasons = [reason for reason, passed in checks if not passed]
    passed = not reasons
    return {
        "candidate_id": candidate_id,
        "source_sample_id": plan.get("source_sample_id", source_id),
        "pre_reaction_sample_id": plan.get("pre_reaction_sample_id", candidate_id),
        "packaging_plan_row_found_once": str(found_once(plan_by_id, candidate_id)).lower(),
        "packaging_report_row_found_once": str(found_once(report_by_id, candidate_id)).lower(),
        "final_readiness_candidate_found_once": str(found_once(final_by_id, candidate_id)).lower(),
        "manifest_candidate_row_found_once": str(found_once(manifest_by_id, candidate_id)).lower(),
        "manifest_source_row_found_once": str(found_once(manifest_by_id, source_id)).lower(),
        "source_mapping_valid": str(source_mapping_valid).lower(),
        "path_consistency_passed": str(path_consistency).lower(),
        "hash_consistency_passed": str(hash_consistency).lower(),
        "current_protein_hash_matches_plan": str(current_protein_hash_matches).lower(),
        "current_ligand_hash_matches_plan": str(current_ligand_hash_matches).lower(),
        "manifest_candidate_paths_match_plan": str(manifest_paths_match).lower(),
        "packaging_dry_run_status_passed": str(packaging_report.get("packaging_dry_run_status", "") == "dataset_packaging_dry_run_passed").lower(),
        "packaging_plan_row_written_confirmed": str(packaging_report.get("packaging_plan_row_written", "") == "true").lower(),
        "ready_for_real_packaging_later_confirmed": str(plan.get("ready_for_real_packaging_later", "") == "true").lower(),
        "files_copied_false": str(packaging_report.get("files_copied", "") == "false").lower(),
        "package_archive_created_false": str(packaging_report.get("package_archive_created", "") == "false").lower(),
        "manifest_modified_false": str(packaging_report.get("manifest_modified", "") == "false").lower(),
        "sdf_modified_false": str(packaging_report.get("sdf_modified", "") == "false").lower(),
        "sdf_generated_false": str(packaging_report.get("sdf_generated", "") == "false").lower(),
        "real_dataset_generated_false": str(plan.get("real_dataset_generated", "") == "false" and packaging_report.get("real_dataset_generated", "") == "false").lower(),
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "graph_counts_positive": str(graph_counts_positive).lower(),
        "reactive_residue_found": plan.get("reactive_residue_found", "false"),
        "reactive_atom_found": plan.get("reactive_atom_found", "false"),
        "packaging_dry_run_qa_status": "dataset_packaging_dry_run_qa_passed" if passed else "blocked",
        "ready_for_real_packaging_planning_later": str(passed).lower(),
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "prepare_real_packaging_design_review_not_training"
            if passed
            else "fix_dataset_packaging_dry_run_qa_blockers"
        ),
    }


def build_qa(
    *,
    packaging_plan_csv: str | Path,
    packaging_report_csv: str | Path,
    final_readiness_candidates_csv: str | Path,
    manifest_csv: str | Path,
) -> list[dict[str, str]]:
    plan_by_id = index_many(read_csv(packaging_plan_csv), "packaging_plan_id")
    report_by_id = index_many(read_csv(packaging_report_csv), "candidate_id")
    final_by_id = index_many(read_csv(final_readiness_candidates_csv), "final_readiness_candidate_id")
    manifest_by_id = index_many(read_csv(manifest_csv), "sample_id")
    return [
        evaluate_candidate(candidate_id, plan_by_id, report_by_id, final_by_id, manifest_by_id)
        for candidate_id in sorted(TARGETS)
    ]


def write_csv(rows: list[dict[str, str]], output_csv: str | Path, fieldnames: list[str]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(reports: list[dict[str, str]]) -> str:
    lines = [
        "# Dataset Packaging Dry-Run QA Summary",
        "",
        "This is packaging dry-run QA only.",
        "",
        "- It reads packaging dry-run plan and report.",
        "- It does not modify manifest files.",
        "- It does not modify or generate SDF files.",
        "- It does not copy protein or ligand files.",
        "- It does not create package archives.",
        "- It does not generate real training datasets.",
        "- It does not train or fine-tune any model.",
        "- Passing this QA means candidates can enter real packaging design review.",
        "- Passing this QA still does not mean the samples are training-ready.",
        "",
        "| candidate_id | source_sample_id | packaging_dry_run_qa_status | ready_for_real_packaging_planning_later | files_copied_false | package_archive_created_false | real_dataset_generated_false | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in reports:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["source_sample_id"],
                    row["packaging_dry_run_qa_status"],
                    row["ready_for_real_packaging_planning_later"],
                    row["files_copied_false"],
                    row["package_archive_created_false"],
                    row["real_dataset_generated_false"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(row["packaging_dry_run_qa_status"] == "dataset_packaging_dry_run_qa_passed" for row in reports)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three candidates passed packaging dry-run QA."
                if all_passed
                else "- One or more candidates are blocked by packaging dry-run QA."
            ),
            "- No files were copied.",
            "- No package archive was created.",
            "- Manifest was not modified.",
            "- No SDF files were modified or generated.",
            "- No real dataset was generated.",
            "- No training was run.",
            "- Next step is real packaging design review, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check dataset packaging dry-run QA.")
    parser.add_argument("--packaging_plan_csv", type=Path, required=True)
    parser.add_argument("--packaging_report_csv", type=Path, required=True)
    parser.add_argument("--final_readiness_candidates_csv", type=Path, required=True)
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command performs packaging dry-run QA only.")
    print("warning: it does not modify manifest or SDF files.")
    print("warning: it does not copy input files or create archives.")
    print("warning: it does not generate real training datasets.")
    reports = build_qa(
        packaging_plan_csv=args.packaging_plan_csv,
        packaging_report_csv=args.packaging_report_csv,
        final_readiness_candidates_csv=args.final_readiness_candidates_csv,
        manifest_csv=args.manifest_csv,
    )
    write_csv(reports, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports), args.output_md)
    print(f"wrote packaging dry-run QA report: {args.output_report_csv}")
    print(f"wrote packaging dry-run QA summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['candidate_id']}: "
            f"packaging_dry_run_qa_status={row['packaging_dry_run_qa_status']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
