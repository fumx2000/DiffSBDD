#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
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

HASH_LOCKED_COLUMNS = [
    "hash_locked_candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "protein_pdb_path",
    "protein_pdb_size_bytes",
    "protein_pdb_sha256",
    "ligand_sdf_path",
    "ligand_sdf_size_bytes",
    "ligand_sdf_sha256",
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
    "file_hash_gate_stage",
    "training_ready",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "schema_valid_candidates_csv",
    "schema_validation_report_csv",
    "manifest_csv",
    "candidate_row_found_once",
    "source_mapping_valid",
    "protein_pdb_path",
    "protein_pdb_path_suffix_ok",
    "protein_pdb_exists",
    "protein_pdb_size_bytes",
    "protein_pdb_nonempty",
    "protein_pdb_sha256",
    "ligand_sdf_path",
    "ligand_sdf_path_expected",
    "ligand_sdf_path_matches_expected",
    "ligand_sdf_path_suffix_ok",
    "ligand_sdf_exists",
    "ligand_sdf_size_bytes",
    "ligand_sdf_nonempty",
    "ligand_sdf_sha256",
    "schema_validation_status_passed",
    "schema_valid_candidate_written_confirmed",
    "schema_validation_real_dataset_generated_false",
    "schema_validation_training_ready_false",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "manifest_candidate_paths_match_candidate_csv",
    "hash_locked_candidate_written",
    "file_existence_and_hash_gate_status",
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


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def file_size(path_value: str) -> str:
    if not path_value or not Path(path_value).exists():
        return ""
    return str(Path(path_value).stat().st_size)


def file_sha(path_value: str) -> str:
    if not path_value or not Path(path_value).exists():
        return ""
    return sha256_file(path_value)


def build_hash_locked(row: dict[str, str], protein_size: str, protein_sha: str, ligand_size: str, ligand_sha: str) -> dict[str, str]:
    return {
        "hash_locked_candidate_id": row["schema_valid_candidate_id"],
        "source_sample_id": row["source_sample_id"],
        "pre_reaction_sample_id": row["pre_reaction_sample_id"],
        "protein_pdb_path": row["protein_pdb_path"],
        "protein_pdb_size_bytes": protein_size,
        "protein_pdb_sha256": protein_sha,
        "ligand_sdf_path": row["ligand_sdf_path"],
        "ligand_sdf_size_bytes": ligand_size,
        "ligand_sdf_sha256": ligand_sha,
        "reactive_residue_chain": row["reactive_residue_chain"],
        "reactive_residue_id": row["reactive_residue_id"],
        "reactive_residue_type": row["reactive_residue_type"],
        "reactive_atom_name": row["reactive_atom_name"],
        "ligand_reactive_atom_id": row["ligand_reactive_atom_id"],
        "warhead_type": row["warhead_type"],
        "scaffold_atoms": row["scaffold_atoms"],
        "linker_atoms": row["linker_atoms"],
        "warhead_atoms": row["warhead_atoms"],
        "scaffold_atom_count": row["scaffold_atom_count"],
        "linker_atom_count": row["linker_atom_count"],
        "warhead_atom_count": row["warhead_atom_count"],
        "candidate_type": row["candidate_type"],
        "dataset_assembly_stage": row["dataset_assembly_stage"],
        "schema_validation_stage": row["schema_validation_stage"],
        "file_hash_gate_stage": "file_existence_and_hash_locked_candidate_only_not_training",
        "training_ready": "false",
    }


def evaluate_candidate(
    *,
    candidate_id: str,
    candidate_rows_by_id: dict[str, list[dict[str, str]]],
    schema_report_by_id: dict[str, dict[str, str]],
    manifest_rows_by_id: dict[str, list[dict[str, str]]],
    schema_valid_candidates_csv: Path,
    schema_validation_report_csv: Path,
    manifest_csv: Path,
) -> tuple[dict[str, str], dict[str, str] | None]:
    target = TARGETS[candidate_id]
    source_expected = target["source"]
    ligand_expected = target["ligand"]
    matching_rows = candidate_rows_by_id.get(candidate_id, [])
    row = matching_rows[0] if len(matching_rows) == 1 else {}
    schema_report = schema_report_by_id.get(candidate_id, {})
    manifest_candidate_rows = manifest_rows_by_id.get(candidate_id, [])
    manifest_source_rows = manifest_rows_by_id.get(source_expected, [])
    manifest_candidate = manifest_candidate_rows[0] if len(manifest_candidate_rows) == 1 else {}

    protein_path = row.get("protein_pdb_path", "")
    ligand_path = row.get("ligand_sdf_path", "")
    protein_size = file_size(protein_path)
    ligand_size = file_size(ligand_path)
    protein_sha = file_sha(protein_path)
    ligand_sha = file_sha(ligand_path)
    protein_exists = bool(protein_path) and Path(protein_path).exists()
    ligand_exists = bool(ligand_path) and Path(ligand_path).exists()
    protein_nonempty = bool(protein_size) and int(protein_size) > 0
    ligand_nonempty = bool(ligand_size) and int(ligand_size) > 0
    manifest_paths_match = (
        manifest_candidate.get("protein_pdb_path", "") == protein_path
        and manifest_candidate.get("ligand_sdf_path", "") == ligand_path
    )

    checks = [
        ("candidate_row_not_found_once", len(matching_rows) == 1),
        ("source_mapping_invalid", row.get("source_sample_id", "") == source_expected),
        ("protein_pdb_path_suffix_not_pdb", protein_path.endswith(".pdb")),
        ("protein_pdb_missing", protein_exists),
        ("protein_pdb_empty", protein_nonempty),
        ("protein_pdb_sha256_empty", bool(protein_sha)),
        ("ligand_sdf_path_not_expected", ligand_path == ligand_expected),
        ("ligand_sdf_path_suffix_not_sdf", ligand_path.endswith(".sdf")),
        ("ligand_sdf_missing", ligand_exists),
        ("ligand_sdf_empty", ligand_nonempty),
        ("ligand_sdf_sha256_empty", bool(ligand_sha)),
        (
            "schema_validation_status_not_passed",
            schema_report.get("schema_validation_status", "") == "dataset_assembly_schema_validation_passed",
        ),
        (
            "schema_valid_candidate_written_not_true",
            schema_report.get("schema_valid_candidate_written", "") == "true",
        ),
        (
            "schema_validation_real_dataset_generated_not_false",
            schema_report.get("real_dataset_generated", "") == "false",
        ),
        ("schema_validation_training_ready_not_false", schema_report.get("training_ready", "") == "false"),
        ("manifest_candidate_row_not_found_once", len(manifest_candidate_rows) == 1),
        ("manifest_source_row_not_found_once", len(manifest_source_rows) == 1),
        ("manifest_candidate_paths_mismatch_candidate_csv", manifest_paths_match),
        ("schema_validation_stage_invalid", row.get("schema_validation_stage", "") == "schema_validated_candidate_only_not_training"),
        ("training_ready_not_false", row.get("training_ready", "") == "false"),
    ]
    reasons = [reason for reason, passed in checks if not passed]
    passed = not reasons
    report = {
        "candidate_id": candidate_id,
        "source_sample_id": row.get("source_sample_id", source_expected),
        "pre_reaction_sample_id": row.get("pre_reaction_sample_id", candidate_id),
        "schema_valid_candidates_csv": str(schema_valid_candidates_csv),
        "schema_validation_report_csv": str(schema_validation_report_csv),
        "manifest_csv": str(manifest_csv),
        "candidate_row_found_once": str(len(matching_rows) == 1).lower(),
        "source_mapping_valid": str(row.get("source_sample_id", "") == source_expected).lower(),
        "protein_pdb_path": protein_path,
        "protein_pdb_path_suffix_ok": str(protein_path.endswith(".pdb")).lower(),
        "protein_pdb_exists": str(protein_exists).lower(),
        "protein_pdb_size_bytes": protein_size,
        "protein_pdb_nonempty": str(protein_nonempty).lower(),
        "protein_pdb_sha256": protein_sha,
        "ligand_sdf_path": ligand_path,
        "ligand_sdf_path_expected": ligand_expected,
        "ligand_sdf_path_matches_expected": str(ligand_path == ligand_expected).lower(),
        "ligand_sdf_path_suffix_ok": str(ligand_path.endswith(".sdf")).lower(),
        "ligand_sdf_exists": str(ligand_exists).lower(),
        "ligand_sdf_size_bytes": ligand_size,
        "ligand_sdf_nonempty": str(ligand_nonempty).lower(),
        "ligand_sdf_sha256": ligand_sha,
        "schema_validation_status_passed": str(
            schema_report.get("schema_validation_status", "") == "dataset_assembly_schema_validation_passed"
        ).lower(),
        "schema_valid_candidate_written_confirmed": str(
            schema_report.get("schema_valid_candidate_written", "") == "true"
        ).lower(),
        "schema_validation_real_dataset_generated_false": str(
            schema_report.get("real_dataset_generated", "") == "false"
        ).lower(),
        "schema_validation_training_ready_false": str(
            schema_report.get("training_ready", "") == "false"
        ).lower(),
        "manifest_candidate_row_found_once": str(len(manifest_candidate_rows) == 1).lower(),
        "manifest_source_row_found_once": str(len(manifest_source_rows) == 1).lower(),
        "manifest_candidate_paths_match_candidate_csv": str(manifest_paths_match).lower(),
        "hash_locked_candidate_written": str(passed).lower(),
        "file_existence_and_hash_gate_status": "file_existence_and_hash_gate_passed" if passed else "blocked",
        "manifest_modified": "false",
        "sdf_modified": "false",
        "sdf_generated": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "build_dataset_assembly_graph_preview_not_training"
            if passed
            else "fix_dataset_assembly_file_hash_gate_blockers"
        ),
    }
    return report, build_hash_locked(row, protein_size, protein_sha, ligand_size, ligand_sha) if passed else None


def build_gate(
    *,
    schema_valid_candidates_csv: str | Path,
    schema_validation_report_csv: str | Path,
    manifest_csv: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    candidates_path = Path(schema_valid_candidates_csv)
    schema_report_path = Path(schema_validation_report_csv)
    manifest_path = Path(manifest_csv)
    candidate_rows, _ = read_csv_with_fieldnames(candidates_path)
    schema_report_rows, _ = read_csv_with_fieldnames(schema_report_path)
    manifest_rows, _ = read_csv_with_fieldnames(manifest_path)
    candidate_rows_by_id = index_many(candidate_rows, "schema_valid_candidate_id")
    schema_report_by_id = index_one(schema_report_rows, "candidate_id")
    manifest_rows_by_id = index_many(manifest_rows, "sample_id")
    reports: list[dict[str, str]] = []
    locked: list[dict[str, str]] = []
    for candidate_id in sorted(TARGETS):
        report, locked_row = evaluate_candidate(
            candidate_id=candidate_id,
            candidate_rows_by_id=candidate_rows_by_id,
            schema_report_by_id=schema_report_by_id,
            manifest_rows_by_id=manifest_rows_by_id,
            schema_valid_candidates_csv=candidates_path,
            schema_validation_report_csv=schema_report_path,
            manifest_csv=manifest_path,
        )
        reports.append(report)
        if locked_row is not None:
            locked.append(locked_row)
    return reports, locked


def write_csv(rows: list[dict[str, str]], output_csv: str | Path, fieldnames: list[str]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(reports: list[dict[str, str]], locked: list[dict[str, str]]) -> str:
    lines = [
        "# Dataset Assembly File Existence and Hash Gate Summary",
        "",
        "This is file existence and hash gate only.",
        "",
        "- It reads schema-valid candidates.",
        "- It does not modify manifest files.",
        "- It does not modify or generate SDF files.",
        "- It does not generate real training datasets.",
        "- It does not train or fine-tune any model.",
        "- Passing this gate means candidate files are hash-locked for the next preview step.",
        "- Passing this gate does not mean the samples are training-ready.",
        "",
        "| candidate_id | source_sample_id | protein_pdb_path | protein_pdb_size_bytes | protein_pdb_sha256 | ligand_sdf_path | ligand_sdf_size_bytes | ligand_sdf_sha256 | file_existence_and_hash_gate_status | hash_locked_candidate_written | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in reports:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["source_sample_id"],
                    row["protein_pdb_path"],
                    row["protein_pdb_size_bytes"],
                    row["protein_pdb_sha256"],
                    row["ligand_sdf_path"],
                    row["ligand_sdf_size_bytes"],
                    row["ligand_sdf_sha256"],
                    row["file_existence_and_hash_gate_status"],
                    row["hash_locked_candidate_written"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(row["file_existence_and_hash_gate_status"] == "file_existence_and_hash_gate_passed" for row in reports)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three candidates passed file existence and hash gate."
                if all_passed
                else "- One or more candidates are blocked by the file existence and hash gate."
            ),
            f"- Hash-locked candidates CSV contains exactly 3 rows: {str(len(locked) == 3).lower()}.",
            "- Manifest was not modified.",
            "- No SDF files were modified or generated.",
            "- No real dataset was generated.",
            "- No training was run.",
            "- Next step is graph preview, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build dataset assembly file existence and hash gate outputs.")
    parser.add_argument("--schema_valid_candidates_csv", type=Path, required=True)
    parser.add_argument("--schema_validation_report_csv", type=Path, required=True)
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--output_hash_locked_candidates_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command performs file existence and hash gating only.")
    print("warning: it does not modify manifest or SDF files.")
    print("warning: it does not generate real training datasets.")
    reports, locked = build_gate(
        schema_valid_candidates_csv=args.schema_valid_candidates_csv,
        schema_validation_report_csv=args.schema_validation_report_csv,
        manifest_csv=args.manifest_csv,
    )
    write_csv(locked, args.output_hash_locked_candidates_csv, HASH_LOCKED_COLUMNS)
    write_csv(reports, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports, locked), args.output_md)
    print(f"wrote hash-locked candidates: {args.output_hash_locked_candidates_csv}")
    print(f"wrote file existence and hash report: {args.output_report_csv}")
    print(f"wrote file existence and hash summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['candidate_id']}: "
            f"file_existence_and_hash_gate_status={row['file_existence_and_hash_gate_status']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
