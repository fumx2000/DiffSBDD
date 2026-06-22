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

PLAN_COLUMNS = [
    "packaging_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
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
    "reactive_residue_found",
    "reactive_atom_found",
    "ligand_reactive_atom_id",
    "scaffold_atoms",
    "linker_atoms",
    "warhead_atoms",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "candidate_type",
    "dataset_assembly_stage",
    "schema_validation_stage",
    "file_hash_gate_stage",
    "graph_preview_stage",
    "final_readiness_stage",
    "packaging_dry_run_stage",
    "ready_for_real_packaging_later",
    "real_dataset_generated",
    "training_ready",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "final_readiness_candidate_found_once",
    "final_readiness_report_found",
    "final_readiness_status_passed",
    "final_readiness_candidate_written_confirmed",
    "ready_for_packaging_dry_run_confirmed",
    "final_readiness_real_dataset_generated_false",
    "final_readiness_training_ready_false",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "manifest_candidate_paths_match_final_candidate",
    "protein_pdb_path",
    "protein_pdb_exists",
    "protein_pdb_sha256_matches_record",
    "ligand_sdf_path",
    "ligand_sdf_exists",
    "ligand_sdf_sha256_matches_record",
    "ligand_atom_count",
    "ligand_heavy_atom_count",
    "ligand_bond_count",
    "protein_atom_count",
    "protein_residue_count",
    "reactive_residue_found",
    "reactive_atom_found",
    "packaging_plan_row_written",
    "packaging_dry_run_status",
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


def path_exists(path_value: str) -> bool:
    return bool(path_value) and Path(path_value).exists()


def build_plan_row(candidate: dict[str, str]) -> dict[str, str]:
    return {
        "packaging_plan_id": candidate["final_readiness_candidate_id"],
        "source_sample_id": candidate["source_sample_id"],
        "pre_reaction_sample_id": candidate["pre_reaction_sample_id"],
        "protein_pdb_path": candidate["protein_pdb_path"],
        "protein_pdb_sha256": candidate["protein_pdb_sha256"],
        "ligand_sdf_path": candidate["ligand_sdf_path"],
        "ligand_sdf_sha256": candidate["ligand_sdf_sha256"],
        "ligand_atom_count": candidate["ligand_atom_count"],
        "ligand_heavy_atom_count": candidate["ligand_heavy_atom_count"],
        "ligand_bond_count": candidate["ligand_bond_count"],
        "protein_atom_count": candidate["protein_atom_count"],
        "protein_residue_count": candidate["protein_residue_count"],
        "reactive_residue_chain": candidate["reactive_residue_chain"],
        "reactive_residue_id": candidate["reactive_residue_id"],
        "reactive_residue_type": candidate["reactive_residue_type"],
        "reactive_atom_name": candidate["reactive_atom_name"],
        "reactive_residue_found": candidate["reactive_residue_found"],
        "reactive_atom_found": candidate["reactive_atom_found"],
        "ligand_reactive_atom_id": candidate["ligand_reactive_atom_id"],
        "scaffold_atoms": candidate["scaffold_atoms"],
        "linker_atoms": candidate["linker_atoms"],
        "warhead_atoms": candidate["warhead_atoms"],
        "scaffold_atom_count": candidate["scaffold_atom_count"],
        "linker_atom_count": candidate["linker_atom_count"],
        "warhead_atom_count": candidate["warhead_atom_count"],
        "candidate_type": candidate["candidate_type"],
        "dataset_assembly_stage": candidate["dataset_assembly_stage"],
        "schema_validation_stage": candidate["schema_validation_stage"],
        "file_hash_gate_stage": candidate["file_hash_gate_stage"],
        "graph_preview_stage": candidate["graph_preview_stage"],
        "final_readiness_stage": candidate["final_readiness_stage"],
        "packaging_dry_run_stage": "packaging_dry_run_plan_only_not_training",
        "ready_for_real_packaging_later": "true",
        "real_dataset_generated": "false",
        "training_ready": "false",
    }


def evaluate_candidate(
    candidate_id: str,
    candidates_by_id: dict[str, list[dict[str, str]]],
    reports_by_id: dict[str, list[dict[str, str]]],
    manifest_by_id: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, str], dict[str, str] | None]:
    source_id = TARGETS[candidate_id]
    candidate = one(candidates_by_id, candidate_id)
    final_report = one(reports_by_id, candidate_id)
    manifest_candidate = one(manifest_by_id, candidate_id)
    protein_path = candidate.get("protein_pdb_path", "")
    ligand_path = candidate.get("ligand_sdf_path", "")
    protein_exists = path_exists(protein_path)
    ligand_exists = path_exists(ligand_path)
    protein_hash_matches = protein_exists and sha256_file(protein_path) == candidate.get("protein_pdb_sha256", "")
    ligand_hash_matches = ligand_exists and sha256_file(ligand_path) == candidate.get("ligand_sdf_sha256", "")
    manifest_paths_match = (
        manifest_candidate.get("protein_pdb_path", "") == protein_path
        and manifest_candidate.get("ligand_sdf_path", "") == ligand_path
    )
    ligand_atom_count = to_int(candidate.get("ligand_atom_count", ""))
    ligand_heavy_atom_count = to_int(candidate.get("ligand_heavy_atom_count", ""))
    ligand_bond_count = to_int(candidate.get("ligand_bond_count", ""))
    protein_atom_count = to_int(candidate.get("protein_atom_count", ""))
    protein_residue_count = to_int(candidate.get("protein_residue_count", ""))
    checks = [
        ("final_readiness_candidate_not_found_once", found_once(candidates_by_id, candidate_id)),
        ("final_readiness_report_not_found_once", found_once(reports_by_id, candidate_id)),
        ("candidate_id_not_target", candidate_id in TARGETS),
        ("pre_reaction_sample_id_mismatch", candidate.get("pre_reaction_sample_id", "") == candidate_id),
        ("ready_for_packaging_dry_run_not_true", candidate.get("ready_for_packaging_dry_run", "") == "true"),
        ("training_ready_not_false", candidate.get("training_ready", "") == "false"),
        (
            "final_readiness_stage_invalid",
            candidate.get("final_readiness_stage", "") == "final_readiness_passed_candidate_only_not_training",
        ),
        ("protein_pdb_missing", protein_exists),
        ("ligand_sdf_missing", ligand_exists),
        ("protein_pdb_sha256_mismatch", protein_hash_matches),
        ("ligand_sdf_sha256_mismatch", ligand_hash_matches),
        ("ligand_atom_count_not_positive", ligand_atom_count is not None and ligand_atom_count > 0),
        ("ligand_heavy_atom_count_not_positive", ligand_heavy_atom_count is not None and ligand_heavy_atom_count > 0),
        ("ligand_bond_count_not_positive", ligand_bond_count is not None and ligand_bond_count > 0),
        ("protein_atom_count_not_positive", protein_atom_count is not None and protein_atom_count > 0),
        ("protein_residue_count_not_positive", protein_residue_count is not None and protein_residue_count > 0),
        ("reactive_residue_not_found", candidate.get("reactive_residue_found", "") == "true"),
        ("reactive_atom_not_found", candidate.get("reactive_atom_found", "") == "true"),
        ("final_readiness_status_not_passed", final_report.get("final_readiness_status", "") == "dataset_assembly_final_readiness_passed"),
        ("final_readiness_candidate_written_not_true", final_report.get("final_readiness_candidate_written", "") == "true"),
        ("final_readiness_report_ready_for_packaging_not_true", final_report.get("ready_for_packaging_dry_run", "") == "true"),
        ("final_readiness_real_dataset_generated_not_false", final_report.get("real_dataset_generated", "") == "false"),
        ("final_readiness_training_ready_not_false", final_report.get("training_ready", "") == "false"),
        ("manifest_candidate_row_not_found_once", found_once(manifest_by_id, candidate_id)),
        ("manifest_source_row_not_found_once", found_once(manifest_by_id, source_id)),
        ("manifest_candidate_paths_mismatch_final_candidate", manifest_paths_match),
    ]
    reasons = [reason for reason, passed in checks if not passed]
    passed = not reasons
    report = {
        "candidate_id": candidate_id,
        "source_sample_id": candidate.get("source_sample_id", source_id),
        "pre_reaction_sample_id": candidate.get("pre_reaction_sample_id", candidate_id),
        "final_readiness_candidate_found_once": str(found_once(candidates_by_id, candidate_id)).lower(),
        "final_readiness_report_found": str(found_once(reports_by_id, candidate_id)).lower(),
        "final_readiness_status_passed": str(final_report.get("final_readiness_status", "") == "dataset_assembly_final_readiness_passed").lower(),
        "final_readiness_candidate_written_confirmed": str(final_report.get("final_readiness_candidate_written", "") == "true").lower(),
        "ready_for_packaging_dry_run_confirmed": str(candidate.get("ready_for_packaging_dry_run", "") == "true" and final_report.get("ready_for_packaging_dry_run", "") == "true").lower(),
        "final_readiness_real_dataset_generated_false": str(final_report.get("real_dataset_generated", "") == "false").lower(),
        "final_readiness_training_ready_false": str(final_report.get("training_ready", "") == "false").lower(),
        "manifest_candidate_row_found_once": str(found_once(manifest_by_id, candidate_id)).lower(),
        "manifest_source_row_found_once": str(found_once(manifest_by_id, source_id)).lower(),
        "manifest_candidate_paths_match_final_candidate": str(manifest_paths_match).lower(),
        "protein_pdb_path": protein_path,
        "protein_pdb_exists": str(protein_exists).lower(),
        "protein_pdb_sha256_matches_record": str(protein_hash_matches).lower(),
        "ligand_sdf_path": ligand_path,
        "ligand_sdf_exists": str(ligand_exists).lower(),
        "ligand_sdf_sha256_matches_record": str(ligand_hash_matches).lower(),
        "ligand_atom_count": candidate.get("ligand_atom_count", "0"),
        "ligand_heavy_atom_count": candidate.get("ligand_heavy_atom_count", "0"),
        "ligand_bond_count": candidate.get("ligand_bond_count", "0"),
        "protein_atom_count": candidate.get("protein_atom_count", "0"),
        "protein_residue_count": candidate.get("protein_residue_count", "0"),
        "reactive_residue_found": candidate.get("reactive_residue_found", "false"),
        "reactive_atom_found": candidate.get("reactive_atom_found", "false"),
        "packaging_plan_row_written": str(passed).lower(),
        "packaging_dry_run_status": "dataset_packaging_dry_run_passed" if passed else "blocked",
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
            "build_dataset_packaging_dry_run_qa_not_training"
            if passed
            else "fix_dataset_packaging_dry_run_blockers"
        ),
    }
    return report, build_plan_row(candidate) if passed else None


def build_packaging_dry_run(
    *,
    final_readiness_candidates_csv: str | Path,
    final_readiness_report_csv: str | Path,
    manifest_csv: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    candidates_by_id = index_many(read_csv(final_readiness_candidates_csv), "final_readiness_candidate_id")
    reports_by_id = index_many(read_csv(final_readiness_report_csv), "candidate_id")
    manifest_by_id = index_many(read_csv(manifest_csv), "sample_id")
    reports = []
    plan = []
    for candidate_id in sorted(TARGETS):
        report, plan_row = evaluate_candidate(candidate_id, candidates_by_id, reports_by_id, manifest_by_id)
        reports.append(report)
        if plan_row is not None:
            plan.append(plan_row)
    return reports, plan


def write_csv(rows: list[dict[str, str]], output_csv: str | Path, fieldnames: list[str]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(reports: list[dict[str, str]], plan: list[dict[str, str]]) -> str:
    lines = [
        "# Dataset Packaging Dry-Run Summary",
        "",
        "This is packaging dry-run only.",
        "",
        "- It reads final readiness candidates.",
        "- It does not modify manifest files.",
        "- It does not modify or generate SDF files.",
        "- It does not copy protein or ligand files.",
        "- It does not create package archives.",
        "- It does not generate real training datasets.",
        "- It does not train or fine-tune any model.",
        "- Passing this dry-run means candidates can enter packaging dry-run QA.",
        "- Passing this dry-run still does not mean the samples are training-ready.",
        "",
        "| candidate_id | source_sample_id | protein_pdb_path | ligand_sdf_path | packaging_dry_run_status | packaging_plan_row_written | ready_for_real_packaging_later | real_dataset_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    plan_by_id = {row["packaging_plan_id"]: row for row in plan}
    for row in reports:
        plan_row = plan_by_id.get(row["candidate_id"], {})
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["source_sample_id"],
                    row["protein_pdb_path"],
                    row["ligand_sdf_path"],
                    row["packaging_dry_run_status"],
                    row["packaging_plan_row_written"],
                    plan_row.get("ready_for_real_packaging_later", "false"),
                    row["real_dataset_generated"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(row["packaging_dry_run_status"] == "dataset_packaging_dry_run_passed" for row in reports)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three candidates passed packaging dry-run."
                if all_passed
                else "- One or more candidates are blocked by packaging dry-run."
            ),
            f"- Packaging dry-run plan CSV contains exactly 3 rows: {str(len(plan) == 3).lower()}.",
            "- No files were copied.",
            "- No package archive was created.",
            "- Manifest was not modified.",
            "- No SDF files were modified or generated.",
            "- No real dataset was generated.",
            "- No training was run.",
            "- Next step is packaging dry-run QA, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build dataset packaging dry-run plan and report.")
    parser.add_argument("--final_readiness_candidates_csv", type=Path, required=True)
    parser.add_argument("--final_readiness_report_csv", type=Path, required=True)
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--output_plan_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command performs packaging dry-run only.")
    print("warning: it does not modify manifest or SDF files.")
    print("warning: it does not copy input files or create archives.")
    print("warning: it does not generate real training datasets.")
    reports, plan = build_packaging_dry_run(
        final_readiness_candidates_csv=args.final_readiness_candidates_csv,
        final_readiness_report_csv=args.final_readiness_report_csv,
        manifest_csv=args.manifest_csv,
    )
    write_csv(plan, args.output_plan_csv, PLAN_COLUMNS)
    write_csv(reports, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports, plan), args.output_md)
    print(f"wrote packaging dry-run plan: {args.output_plan_csv}")
    print(f"wrote packaging dry-run report: {args.output_report_csv}")
    print(f"wrote packaging dry-run summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['candidate_id']}: "
            f"packaging_dry_run_status={row['packaging_dry_run_status']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
