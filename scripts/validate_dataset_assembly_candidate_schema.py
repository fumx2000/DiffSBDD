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

REQUIRED_CANDIDATE_COLUMNS = [
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

VALID_CANDIDATE_COLUMNS = [
    "schema_valid_candidate_id",
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
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "candidate_type",
    "dataset_assembly_stage",
    "schema_validation_stage",
    "training_ready",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "candidates_csv",
    "dry_run_report_csv",
    "manifest_csv",
    "candidate_row_found_once",
    "source_mapping_valid",
    "candidate_id_matches_pre_reaction_sample_id",
    "required_candidate_columns_present",
    "protein_pdb_path",
    "protein_pdb_exists",
    "ligand_sdf_path",
    "ligand_sdf_path_expected",
    "ligand_sdf_path_matches_expected",
    "ligand_sdf_exists",
    "reactive_residue_chain",
    "reactive_residue_id",
    "reactive_residue_id_is_integer",
    "reactive_residue_type",
    "reactive_atom_name",
    "ligand_reactive_atom_id",
    "ligand_reactive_atom_id_is_integer",
    "scaffold_atoms_parseable",
    "linker_atoms_parseable",
    "warhead_atoms_parseable",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "atom_groups_non_overlapping",
    "warhead_contains_ligand_reactive_atom",
    "dry_run_status_passed",
    "dry_run_candidate_written",
    "dry_run_real_dataset_generated_false",
    "dry_run_training_ready_false",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "schema_valid_candidate_written",
    "schema_validation_status",
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


def index_many(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    indexed: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        indexed.setdefault(row.get(key, ""), []).append(row)
    return indexed


def index_one(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def is_integer(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False
    return True


def parse_atom_list(value: str) -> tuple[bool, list[int]]:
    if not value.strip():
        return False, []
    try:
        return True, [int(part) for part in value.split()]
    except ValueError:
        return False, []


def atom_groups_non_overlapping(groups: list[list[int]]) -> bool:
    seen: set[int] = set()
    for group in groups:
        group_set = set(group)
        if seen & group_set:
            return False
        seen.update(group_set)
    return True


def valid_candidate(row: dict[str, str], counts: tuple[int, int, int]) -> dict[str, str]:
    scaffold_count, linker_count, warhead_count = counts
    return {
        "schema_valid_candidate_id": row["candidate_id"],
        "source_sample_id": row["source_sample_id"],
        "pre_reaction_sample_id": row["pre_reaction_sample_id"],
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
        "scaffold_atom_count": str(scaffold_count),
        "linker_atom_count": str(linker_count),
        "warhead_atom_count": str(warhead_count),
        "candidate_type": row["candidate_type"],
        "dataset_assembly_stage": row["dataset_assembly_stage"],
        "schema_validation_stage": "schema_validated_candidate_only_not_training",
        "training_ready": "false",
    }


def evaluate_candidate(
    *,
    candidate_id: str,
    candidate_rows_by_id: dict[str, list[dict[str, str]]],
    candidate_columns_present: bool,
    dry_rows_by_id: dict[str, dict[str, str]],
    manifest_rows_by_id: dict[str, list[dict[str, str]]],
    candidates_csv: Path,
    dry_run_report_csv: Path,
    manifest_csv: Path,
) -> tuple[dict[str, str], dict[str, str] | None]:
    expected = TARGETS[candidate_id]
    source_id_expected = expected["source"]
    ligand_expected = expected["ligand"]
    matching_rows = candidate_rows_by_id.get(candidate_id, [])
    row = matching_rows[0] if len(matching_rows) == 1 else {}
    dry = dry_rows_by_id.get(candidate_id, {})
    reasons: list[str] = []

    candidate_row_found_once = len(matching_rows) == 1
    candidate_id_matches = row.get("candidate_id", "") == row.get("pre_reaction_sample_id", "") == candidate_id
    source_mapping_valid = row.get("source_sample_id", "") == source_id_expected
    source_sample_id = row.get("source_sample_id", source_id_expected)
    pre_reaction_sample_id = row.get("pre_reaction_sample_id", candidate_id)
    protein_path = row.get("protein_pdb_path", "")
    ligand_path = row.get("ligand_sdf_path", "")
    reactive_residue_id = row.get("reactive_residue_id", "")
    ligand_reactive_atom_id = row.get("ligand_reactive_atom_id", "")
    scaffold_ok, scaffold_atoms = parse_atom_list(row.get("scaffold_atoms", ""))
    linker_ok, linker_atoms = parse_atom_list(row.get("linker_atoms", ""))
    warhead_ok, warhead_atoms = parse_atom_list(row.get("warhead_atoms", ""))
    reactive_id_ok = is_integer(reactive_residue_id)
    ligand_reactive_ok = is_integer(ligand_reactive_atom_id)
    non_overlapping = atom_groups_non_overlapping([scaffold_atoms, linker_atoms, warhead_atoms])
    warhead_contains = ligand_reactive_ok and int(ligand_reactive_atom_id) in set(warhead_atoms)
    manifest_candidate_count = len(manifest_rows_by_id.get(candidate_id, []))
    manifest_source_count = len(manifest_rows_by_id.get(source_id_expected, []))
    dry_run_status_passed = dry.get("dataset_assembly_dry_run_status", "") == "post_manifest_dataset_assembly_dry_run_passed"
    dry_run_candidate_written = dry.get("candidate_written_to_dry_run_list", "") == "true"
    dry_run_real_dataset_false = dry.get("real_dataset_generated", "") == "false"
    dry_run_training_false = dry.get("training_ready", "") == "false"

    checks = [
        ("required_candidate_columns_missing", candidate_columns_present),
        ("candidate_row_not_found_once", candidate_row_found_once),
        ("candidate_id_not_target", candidate_id in TARGETS),
        ("candidate_id_mismatch_pre_reaction_sample_id", candidate_id_matches),
        ("source_mapping_invalid", source_mapping_valid),
        ("candidate_type_invalid", row.get("candidate_type", "") == "derived_pre_reaction_ligand_candidate"),
        ("dataset_assembly_stage_invalid", row.get("dataset_assembly_stage", "") == "dry_run_candidate_only_not_training"),
        ("training_ready_not_false", row.get("training_ready", "") == "false"),
        ("protein_pdb_path_empty_or_missing", bool(protein_path) and Path(protein_path).exists()),
        ("ligand_sdf_path_empty_or_missing", bool(ligand_path) and Path(ligand_path).exists()),
        ("ligand_sdf_path_not_expected", ligand_path == ligand_expected),
        ("reactive_residue_type_not_CYS", row.get("reactive_residue_type", "") == "CYS"),
        ("reactive_atom_name_not_SG", row.get("reactive_atom_name", "") == "SG"),
        ("reactive_residue_chain_empty", bool(row.get("reactive_residue_chain", ""))),
        ("reactive_residue_id_not_integer", reactive_id_ok),
        ("ligand_reactive_atom_id_not_integer", ligand_reactive_ok),
        ("scaffold_atoms_not_parseable", scaffold_ok),
        ("linker_atoms_not_parseable", linker_ok),
        ("warhead_atoms_not_parseable", warhead_ok),
        ("atom_groups_overlap", non_overlapping),
        ("warhead_missing_ligand_reactive_atom", warhead_contains),
        ("dry_run_status_not_passed", dry_run_status_passed),
        ("dry_run_candidate_not_written", dry_run_candidate_written),
        ("dry_run_real_dataset_generated_not_false", dry_run_real_dataset_false),
        ("dry_run_training_ready_not_false", dry_run_training_false),
        ("manifest_candidate_row_not_found_once", manifest_candidate_count == 1),
        ("manifest_source_row_not_found_once", manifest_source_count == 1),
    ]
    for reason, passed in checks:
        if not passed:
            reasons.append(reason)

    passed = not reasons
    counts = (len(scaffold_atoms), len(linker_atoms), len(warhead_atoms))
    report = {
        "candidate_id": candidate_id,
        "source_sample_id": source_sample_id,
        "pre_reaction_sample_id": pre_reaction_sample_id,
        "candidates_csv": str(candidates_csv),
        "dry_run_report_csv": str(dry_run_report_csv),
        "manifest_csv": str(manifest_csv),
        "candidate_row_found_once": str(candidate_row_found_once).lower(),
        "source_mapping_valid": str(source_mapping_valid).lower(),
        "candidate_id_matches_pre_reaction_sample_id": str(candidate_id_matches).lower(),
        "required_candidate_columns_present": str(candidate_columns_present).lower(),
        "protein_pdb_path": protein_path,
        "protein_pdb_exists": str(bool(protein_path) and Path(protein_path).exists()).lower(),
        "ligand_sdf_path": ligand_path,
        "ligand_sdf_path_expected": ligand_expected,
        "ligand_sdf_path_matches_expected": str(ligand_path == ligand_expected).lower(),
        "ligand_sdf_exists": str(bool(ligand_path) and Path(ligand_path).exists()).lower(),
        "reactive_residue_chain": row.get("reactive_residue_chain", ""),
        "reactive_residue_id": reactive_residue_id,
        "reactive_residue_id_is_integer": str(reactive_id_ok).lower(),
        "reactive_residue_type": row.get("reactive_residue_type", ""),
        "reactive_atom_name": row.get("reactive_atom_name", ""),
        "ligand_reactive_atom_id": ligand_reactive_atom_id,
        "ligand_reactive_atom_id_is_integer": str(ligand_reactive_ok).lower(),
        "scaffold_atoms_parseable": str(scaffold_ok).lower(),
        "linker_atoms_parseable": str(linker_ok).lower(),
        "warhead_atoms_parseable": str(warhead_ok).lower(),
        "scaffold_atom_count": str(len(scaffold_atoms)),
        "linker_atom_count": str(len(linker_atoms)),
        "warhead_atom_count": str(len(warhead_atoms)),
        "atom_groups_non_overlapping": str(non_overlapping).lower(),
        "warhead_contains_ligand_reactive_atom": str(warhead_contains).lower(),
        "dry_run_status_passed": str(dry_run_status_passed).lower(),
        "dry_run_candidate_written": str(dry_run_candidate_written).lower(),
        "dry_run_real_dataset_generated_false": str(dry_run_real_dataset_false).lower(),
        "dry_run_training_ready_false": str(dry_run_training_false).lower(),
        "manifest_candidate_row_found_once": str(manifest_candidate_count == 1).lower(),
        "manifest_source_row_found_once": str(manifest_source_count == 1).lower(),
        "schema_valid_candidate_written": str(passed).lower(),
        "schema_validation_status": "dataset_assembly_schema_validation_passed" if passed else "blocked",
        "manifest_modified": "false",
        "sdf_modified": "false",
        "sdf_generated": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "build_dataset_assembly_file_existence_and_hash_gate_not_training"
            if passed
            else "fix_dataset_assembly_schema_validation_blockers"
        ),
    }
    return report, valid_candidate(row, counts) if passed else None


def build_validation(
    *,
    candidates_csv: str | Path,
    dry_run_report_csv: str | Path,
    manifest_csv: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    candidates_path = Path(candidates_csv)
    dry_path = Path(dry_run_report_csv)
    manifest_path = Path(manifest_csv)
    candidate_rows, candidate_fields = read_csv_with_fieldnames(candidates_path)
    dry_rows, _ = read_csv_with_fieldnames(dry_path)
    manifest_rows, _ = read_csv_with_fieldnames(manifest_path)
    candidate_columns_present = all(column in candidate_fields for column in REQUIRED_CANDIDATE_COLUMNS)
    candidate_rows_by_id = index_many(candidate_rows, "candidate_id")
    dry_rows_by_id = index_one(dry_rows, "pre_reaction_sample_id")
    manifest_rows_by_id = index_many(manifest_rows, "sample_id")

    reports: list[dict[str, str]] = []
    valid_candidates: list[dict[str, str]] = []
    for candidate_id in sorted(TARGETS):
        report, valid = evaluate_candidate(
            candidate_id=candidate_id,
            candidate_rows_by_id=candidate_rows_by_id,
            candidate_columns_present=candidate_columns_present,
            dry_rows_by_id=dry_rows_by_id,
            manifest_rows_by_id=manifest_rows_by_id,
            candidates_csv=candidates_path,
            dry_run_report_csv=dry_path,
            manifest_csv=manifest_path,
        )
        reports.append(report)
        if valid is not None:
            valid_candidates.append(valid)
    return reports, valid_candidates


def write_csv(rows: list[dict[str, str]], output_csv: str | Path, fieldnames: list[str]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(reports: list[dict[str, str]], valid_candidates: list[dict[str, str]]) -> str:
    lines = [
        "# Dataset Assembly Schema Validation Summary",
        "",
        "This is schema validation only.",
        "",
        "- It reads the post-manifest dry-run candidate list.",
        "- It does not modify manifest files.",
        "- It does not modify or generate SDF files.",
        "- It does not generate real training datasets.",
        "- It does not train or fine-tune any model.",
        "- Passing this validation means candidates can enter file existence and hash gate.",
        "- Passing this validation does not mean the samples are training-ready.",
        "",
        "| candidate_id | source_sample_id | ligand_sdf_path | protein_pdb_path | schema_validation_status | schema_valid_candidate_written | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in reports:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["source_sample_id"],
                    row["ligand_sdf_path"],
                    row["protein_pdb_path"],
                    row["schema_validation_status"],
                    row["schema_valid_candidate_written"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(row["schema_validation_status"] == "dataset_assembly_schema_validation_passed" for row in reports)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three candidates passed schema validation."
                if all_passed
                else "- One or more candidates are blocked by schema validation."
            ),
            f"- Valid candidates CSV contains exactly 3 rows: {str(len(valid_candidates) == 3).lower()}.",
            "- Manifest was not modified.",
            "- No SDF files were modified or generated.",
            "- No real dataset was generated.",
            "- No training was run.",
            "- Next step is file existence and hash gate, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate dataset assembly candidate schema.")
    parser.add_argument("--candidates_csv", type=Path, required=True)
    parser.add_argument("--dry_run_report_csv", type=Path, required=True)
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--output_valid_candidates_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command validates candidate schema only.")
    print("warning: it does not modify manifest or SDF files.")
    print("warning: it does not generate real training datasets.")
    reports, valid_candidates = build_validation(
        candidates_csv=args.candidates_csv,
        dry_run_report_csv=args.dry_run_report_csv,
        manifest_csv=args.manifest_csv,
    )
    write_csv(valid_candidates, args.output_valid_candidates_csv, VALID_CANDIDATE_COLUMNS)
    write_csv(reports, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports, valid_candidates), args.output_md)
    print(f"wrote schema-valid candidates: {args.output_valid_candidates_csv}")
    print(f"wrote schema validation report: {args.output_report_csv}")
    print(f"wrote schema validation summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['candidate_id']}: "
            f"schema_validation_status={row['schema_validation_status']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
