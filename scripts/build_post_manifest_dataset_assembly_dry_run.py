#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


TARGETS = {
    "BTK_C481_6DI9_pre_reaction": {
        "source": "BTK_C481_6DI9",
        "ligand": "data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf",
    },
    "KRAS_G12C_5F2E_pre_reaction": {
        "source": "KRAS_G12C_5F2E",
        "ligand": "data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf",
    },
    "KRAS_G12C_6OIM_pre_reaction": {
        "source": "KRAS_G12C_6OIM",
        "ligand": "data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf",
    },
}

REQUIRED_MANIFEST_COLUMNS = [
    "sample_id",
    "protein_pdb_path",
    "ligand_sdf_path",
    "reactive_residue_chain",
    "reactive_residue_id",
    "reactive_residue_type",
    "reactive_atom_name",
    "ligand_reactive_atom_id",
    "warhead_type",
    "scaffold_atoms",
    "linker_atoms",
    "warhead_atoms",
]

CANDIDATE_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "protein_pdb_path",
    "ligand_sdf_path",
    "reactive_residue_chain",
    "reactive_residue_id",
    "reactive_residue_type",
    "reactive_atom_name",
    "ligand_reactive_atom_id",
    "warhead_type",
    "scaffold_atoms",
    "linker_atoms",
    "warhead_atoms",
    "candidate_type",
    "dataset_assembly_stage",
    "training_ready",
]

REPORT_COLUMNS = [
    "pre_reaction_sample_id",
    "source_sample_id",
    "manifest_csv",
    "manifest_row_found_once",
    "source_row_found_once",
    "manifest_required_columns_present",
    "ligand_sdf_path",
    "ligand_sdf_path_expected",
    "ligand_sdf_path_matches_expected",
    "ligand_sdf_exists",
    "protein_pdb_path",
    "protein_pdb_exists",
    "reactive_residue_chain",
    "reactive_residue_id",
    "reactive_residue_type",
    "reactive_atom_name",
    "ligand_reactive_atom_id",
    "ligand_reactive_atom_id_is_integer",
    "scaffold_atoms_parseable",
    "linker_atoms_parseable",
    "warhead_atoms_parseable",
    "atom_groups_non_overlapping",
    "warhead_contains_ligand_reactive_atom",
    "actual_manifest_update_qa_passed",
    "candidate_written_to_dry_run_list",
    "dataset_assembly_dry_run_status",
    "manifest_modified",
    "sdf_modified",
    "sdf_generated",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "blocking_reasons",
    "recommended_next_action",
]


def read_csv_with_fieldnames(path: str | Path) -> tuple[list[dict[str, str]], list[str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def index_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    indexed: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        indexed.setdefault(row.get("sample_id", ""), []).append(row)
    return indexed


def index_qa(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["proposed_manifest_sample_id"]: row for row in rows}


def parse_atom_list(value: str) -> tuple[bool, list[int]]:
    if not value.strip():
        return False, []
    try:
        return True, [int(part) for part in value.split()]
    except ValueError:
        return False, []


def atom_groups_non_overlapping(*groups: list[int]) -> bool:
    seen: set[int] = set()
    for group in groups:
        group_set = set(group)
        if seen & group_set:
            return False
        seen.update(group_set)
    return True


def is_integer(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False
    return True


def build_candidate(row: dict[str, str], pre_id: str, source_id: str) -> dict[str, str]:
    return {
        "candidate_id": pre_id,
        "source_sample_id": source_id,
        "pre_reaction_sample_id": pre_id,
        "protein_pdb_path": row["protein_pdb_path"],
        "ligand_sdf_path": row["ligand_sdf_path"],
        "reactive_residue_chain": row["reactive_residue_chain"],
        "reactive_residue_id": row["reactive_residue_id"],
        "reactive_residue_type": row["reactive_residue_type"],
        "reactive_atom_name": row["reactive_atom_name"],
        "ligand_reactive_atom_id": row["ligand_reactive_atom_id"],
        "warhead_type": row["warhead_type"],
        "scaffold_atoms": row["scaffold_atoms"],
        "linker_atoms": row["linker_atoms"],
        "warhead_atoms": row["warhead_atoms"],
        "candidate_type": "derived_pre_reaction_ligand_candidate",
        "dataset_assembly_stage": "dry_run_candidate_only_not_training",
        "training_ready": "false",
    }


def evaluate_target(
    *,
    pre_id: str,
    manifest_csv: Path,
    manifest_rows_by_id: dict[str, list[dict[str, str]]],
    required_columns_present: bool,
    qa_by_id: dict[str, dict[str, str]],
) -> tuple[dict[str, str], dict[str, str] | None]:
    source_id = TARGETS[pre_id]["source"]
    expected_ligand = TARGETS[pre_id]["ligand"]
    pre_rows = manifest_rows_by_id.get(pre_id, [])
    source_rows = manifest_rows_by_id.get(source_id, [])
    row = pre_rows[0] if len(pre_rows) == 1 else {}
    qa = qa_by_id.get(pre_id, {})
    reasons: list[str] = []

    manifest_row_found_once = len(pre_rows) == 1
    source_row_found_once = len(source_rows) == 1
    if not required_columns_present:
        reasons.append("manifest_required_columns_missing")
    if not manifest_row_found_once:
        reasons.append("pre_reaction_manifest_row_not_found_once")
    if not source_row_found_once:
        reasons.append("source_manifest_row_not_found_once")

    ligand_sdf_path = row.get("ligand_sdf_path", "")
    protein_pdb_path = row.get("protein_pdb_path", "")
    reactive_chain = row.get("reactive_residue_chain", "")
    reactive_id = row.get("reactive_residue_id", "")
    reactive_type = row.get("reactive_residue_type", "")
    reactive_atom = row.get("reactive_atom_name", "")
    ligand_reactive_atom_id = row.get("ligand_reactive_atom_id", "")
    scaffold_value = row.get("scaffold_atoms", "")
    linker_value = row.get("linker_atoms", "")
    warhead_value = row.get("warhead_atoms", "")

    ligand_matches = ligand_sdf_path == expected_ligand
    ligand_exists = bool(ligand_sdf_path) and Path(ligand_sdf_path).exists()
    protein_exists = bool(protein_pdb_path) and Path(protein_pdb_path).exists()
    reactive_int = is_integer(ligand_reactive_atom_id) if ligand_reactive_atom_id else False
    scaffold_ok, scaffold_atoms = parse_atom_list(scaffold_value)
    linker_ok, linker_atoms = parse_atom_list(linker_value)
    warhead_ok, warhead_atoms = parse_atom_list(warhead_value)
    non_overlapping = atom_groups_non_overlapping(scaffold_atoms, linker_atoms, warhead_atoms)
    warhead_contains = reactive_int and int(ligand_reactive_atom_id) in set(warhead_atoms)
    qa_passed = (
        qa.get("actual_manifest_update_qa_status", "") == "actual_manifest_update_qa_passed"
        and qa.get("training_ready", "") == "false"
    )

    checks = [
        ("ligand_sdf_path_not_expected", ligand_matches),
        ("ligand_sdf_missing", ligand_exists),
        ("protein_pdb_path_empty", bool(protein_pdb_path)),
        ("protein_pdb_missing", protein_exists),
        ("reactive_residue_type_not_CYS", reactive_type == "CYS"),
        ("reactive_atom_name_not_SG", reactive_atom == "SG"),
        ("reactive_residue_chain_empty", bool(reactive_chain)),
        ("reactive_residue_id_empty", bool(reactive_id)),
        ("ligand_reactive_atom_id_missing_or_not_integer", reactive_int),
        ("scaffold_atoms_not_parseable", scaffold_ok),
        ("linker_atoms_not_parseable", linker_ok),
        ("warhead_atoms_not_parseable", warhead_ok),
        ("atom_groups_overlap", non_overlapping),
        ("warhead_atoms_missing_ligand_reactive_atom", warhead_contains),
        ("actual_manifest_update_qa_not_passed", qa_passed),
    ]
    for reason, passed in checks:
        if not passed:
            reasons.append(reason)

    passed = not reasons
    report = {
        "pre_reaction_sample_id": pre_id,
        "source_sample_id": source_id,
        "manifest_csv": str(manifest_csv),
        "manifest_row_found_once": str(manifest_row_found_once).lower(),
        "source_row_found_once": str(source_row_found_once).lower(),
        "manifest_required_columns_present": str(required_columns_present).lower(),
        "ligand_sdf_path": ligand_sdf_path,
        "ligand_sdf_path_expected": expected_ligand,
        "ligand_sdf_path_matches_expected": str(ligand_matches).lower(),
        "ligand_sdf_exists": str(ligand_exists).lower(),
        "protein_pdb_path": protein_pdb_path,
        "protein_pdb_exists": str(protein_exists).lower(),
        "reactive_residue_chain": reactive_chain,
        "reactive_residue_id": reactive_id,
        "reactive_residue_type": reactive_type,
        "reactive_atom_name": reactive_atom,
        "ligand_reactive_atom_id": ligand_reactive_atom_id,
        "ligand_reactive_atom_id_is_integer": str(reactive_int).lower(),
        "scaffold_atoms_parseable": str(scaffold_ok).lower(),
        "linker_atoms_parseable": str(linker_ok).lower(),
        "warhead_atoms_parseable": str(warhead_ok).lower(),
        "atom_groups_non_overlapping": str(non_overlapping).lower(),
        "warhead_contains_ligand_reactive_atom": str(warhead_contains).lower(),
        "actual_manifest_update_qa_passed": str(qa_passed).lower(),
        "candidate_written_to_dry_run_list": str(passed).lower(),
        "dataset_assembly_dry_run_status": (
            "post_manifest_dataset_assembly_dry_run_passed" if passed else "blocked"
        ),
        "manifest_modified": "false",
        "sdf_modified": "false",
        "sdf_generated": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "build_dataset_assembly_schema_validation_not_training"
            if passed
            else "fix_post_manifest_dataset_assembly_dry_run_blockers"
        ),
    }
    return report, build_candidate(row, pre_id, source_id) if passed else None


def build_dry_run(
    *,
    manifest_csv: str | Path,
    actual_manifest_update_qa_report_csv: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    manifest_path = Path(manifest_csv)
    manifest_rows, fieldnames = read_csv_with_fieldnames(manifest_path)
    qa_rows, _ = read_csv_with_fieldnames(actual_manifest_update_qa_report_csv)
    required_columns_present = all(column in fieldnames for column in REQUIRED_MANIFEST_COLUMNS)
    rows_by_id = index_rows(manifest_rows)
    qa_by_id = index_qa(qa_rows)
    reports: list[dict[str, str]] = []
    candidates: list[dict[str, str]] = []
    for pre_id in sorted(TARGETS):
        report, candidate = evaluate_target(
            pre_id=pre_id,
            manifest_csv=manifest_path,
            manifest_rows_by_id=rows_by_id,
            required_columns_present=required_columns_present,
            qa_by_id=qa_by_id,
        )
        reports.append(report)
        if candidate is not None:
            candidates.append(candidate)
    return reports, candidates


def write_csv(rows: list[dict[str, str]], output_csv: str | Path, fieldnames: list[str]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(reports: list[dict[str, str]], candidates: list[dict[str, str]]) -> str:
    lines = [
        "# Post-Manifest Dataset Assembly Dry-Run Summary",
        "",
        "This is a dataset assembly dry-run only.",
        "",
        "- It reads the updated manifest after actual manifest update QA.",
        "- It does not modify manifest files.",
        "- It does not modify or generate SDF files.",
        "- It does not generate real training datasets.",
        "- It does not train or fine-tune any model.",
        "- Passing this dry-run means the rows can enter schema validation.",
        "- Passing this dry-run does not mean the samples are training-ready.",
        "",
        "| pre_reaction_sample_id | source_sample_id | ligand_sdf_path | protein_pdb_path | dataset_assembly_dry_run_status | candidate_written_to_dry_run_list | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in reports:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["pre_reaction_sample_id"],
                    row["source_sample_id"],
                    row["ligand_sdf_path"],
                    row["protein_pdb_path"],
                    row["dataset_assembly_dry_run_status"],
                    row["candidate_written_to_dry_run_list"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(row["dataset_assembly_dry_run_status"] == "post_manifest_dataset_assembly_dry_run_passed" for row in reports)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three pre-reaction manifest rows passed post-manifest dataset assembly dry-run."
                if all_passed
                else "- One or more pre-reaction manifest rows are blocked."
            ),
            f"- Candidates CSV contains exactly 3 rows: {str(len(candidates) == 3).lower()}.",
            "- Manifest was not modified.",
            "- No SDF files were modified or generated.",
            "- No real dataset was generated.",
            "- No training was run.",
            "- Next step is dataset assembly schema validation, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build post-manifest dataset assembly dry-run outputs.")
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--actual_manifest_update_qa_report_csv", type=Path, required=True)
    parser.add_argument("--output_candidates_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command is a dataset assembly dry-run only.")
    print("warning: it does not modify manifest or SDF files.")
    print("warning: it does not generate real training datasets.")
    reports, candidates = build_dry_run(
        manifest_csv=args.manifest_csv,
        actual_manifest_update_qa_report_csv=args.actual_manifest_update_qa_report_csv,
    )
    write_csv(candidates, args.output_candidates_csv, CANDIDATE_COLUMNS)
    write_csv(reports, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports, candidates), args.output_md)
    print(f"wrote dataset assembly dry-run candidates: {args.output_candidates_csv}")
    print(f"wrote dataset assembly dry-run report: {args.output_report_csv}")
    print(f"wrote dataset assembly dry-run summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['pre_reaction_sample_id']}: "
            f"status={row['dataset_assembly_dry_run_status']} "
            f"candidate={row['candidate_written_to_dry_run_list']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
