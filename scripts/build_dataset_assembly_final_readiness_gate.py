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

EXPECTED_LIGAND_PATHS = {
    "BTK_C481_6DI9_pre_reaction": "data/derived/covalent_small/ligands_pre_reaction/BTK_C481_6DI9_pre_reaction.sdf",
    "KRAS_G12C_5F2E_pre_reaction": "data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_5F2E_pre_reaction.sdf",
    "KRAS_G12C_6OIM_pre_reaction": "data/derived/covalent_small/ligands_pre_reaction/KRAS_G12C_6OIM_pre_reaction.sdf",
}

FINAL_CANDIDATE_COLUMNS = [
    "final_readiness_candidate_id",
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
    "ready_for_packaging_dry_run",
    "training_ready",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "dry_run_candidate_found_once",
    "schema_valid_candidate_found_once",
    "hash_locked_candidate_found_once",
    "graph_preview_candidate_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "source_mapping_consistent",
    "protein_pdb_path_consistent",
    "ligand_sdf_path_consistent",
    "protein_pdb_exists",
    "ligand_sdf_exists",
    "protein_pdb_sha256_consistent",
    "ligand_sdf_sha256_consistent",
    "current_protein_pdb_sha256_matches_record",
    "current_ligand_sdf_sha256_matches_record",
    "dry_run_status_passed",
    "schema_validation_status_passed",
    "file_existence_and_hash_gate_passed",
    "graph_preview_status_passed",
    "ligand_atom_count",
    "ligand_heavy_atom_count",
    "ligand_bond_count",
    "protein_atom_count",
    "protein_residue_count",
    "reactive_residue_found",
    "reactive_atom_found",
    "final_readiness_candidate_written",
    "final_readiness_status",
    "ready_for_packaging_dry_run",
    "manifest_modified",
    "sdf_modified",
    "sdf_generated",
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


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def to_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def one(indexed: dict[str, list[dict[str, str]]], key: str) -> dict[str, str]:
    rows = indexed.get(key, [])
    return rows[0] if len(rows) == 1 else {}


def unique_bool(indexed: dict[str, list[dict[str, str]]], key: str) -> bool:
    return len(indexed.get(key, [])) == 1


def path_exists(path_value: str) -> bool:
    return bool(path_value) and Path(path_value).exists()


def same_nonempty(values: list[str]) -> bool:
    return bool(values) and all(values) and len(set(values)) == 1


def build_final_candidate(graph_row: dict[str, str]) -> dict[str, str]:
    return {
        "final_readiness_candidate_id": graph_row["graph_preview_candidate_id"],
        "source_sample_id": graph_row["source_sample_id"],
        "pre_reaction_sample_id": graph_row["pre_reaction_sample_id"],
        "protein_pdb_path": graph_row["protein_pdb_path"],
        "protein_pdb_sha256": graph_row["protein_pdb_sha256"],
        "ligand_sdf_path": graph_row["ligand_sdf_path"],
        "ligand_sdf_sha256": graph_row["ligand_sdf_sha256"],
        "ligand_atom_count": graph_row["ligand_atom_count"],
        "ligand_heavy_atom_count": graph_row["ligand_heavy_atom_count"],
        "ligand_bond_count": graph_row["ligand_bond_count"],
        "protein_atom_count": graph_row["protein_atom_count"],
        "protein_residue_count": graph_row["protein_residue_count"],
        "reactive_residue_chain": graph_row["reactive_residue_chain"],
        "reactive_residue_id": graph_row["reactive_residue_id"],
        "reactive_residue_type": graph_row["reactive_residue_type"],
        "reactive_atom_name": graph_row["reactive_atom_name"],
        "reactive_residue_found": graph_row["reactive_residue_found"],
        "reactive_atom_found": graph_row["reactive_atom_found"],
        "ligand_reactive_atom_id": graph_row["ligand_reactive_atom_id"],
        "scaffold_atoms": graph_row["scaffold_atoms"],
        "linker_atoms": graph_row["linker_atoms"],
        "warhead_atoms": graph_row["warhead_atoms"],
        "scaffold_atom_count": graph_row["scaffold_atom_count"],
        "linker_atom_count": graph_row["linker_atom_count"],
        "warhead_atom_count": graph_row["warhead_atom_count"],
        "candidate_type": graph_row["candidate_type"],
        "dataset_assembly_stage": graph_row["dataset_assembly_stage"],
        "schema_validation_stage": graph_row["schema_validation_stage"],
        "file_hash_gate_stage": graph_row["file_hash_gate_stage"],
        "graph_preview_stage": graph_row["graph_preview_stage"],
        "final_readiness_stage": "final_readiness_passed_candidate_only_not_training",
        "ready_for_packaging_dry_run": "true",
        "training_ready": "false",
    }


def evaluate_candidate(candidate_id: str, indexes: dict[str, dict[str, list[dict[str, str]]]]) -> tuple[dict[str, str], dict[str, str] | None]:
    expected_source = TARGETS[candidate_id]
    expected_ligand = EXPECTED_LIGAND_PATHS[candidate_id]
    dry = one(indexes["dry_candidates"], candidate_id)
    dry_report = one(indexes["dry_reports"], candidate_id)
    schema = one(indexes["schema_candidates"], candidate_id)
    schema_report = one(indexes["schema_reports"], candidate_id)
    hash_locked = one(indexes["hash_candidates"], candidate_id)
    hash_report = one(indexes["hash_reports"], candidate_id)
    graph = one(indexes["graph_candidates"], candidate_id)
    graph_report = one(indexes["graph_reports"], candidate_id)
    manifest_candidate = one(indexes["manifest"], candidate_id)
    manifest_source = one(indexes["manifest"], expected_source)

    source_values = [
        dry.get("source_sample_id", ""),
        schema.get("source_sample_id", ""),
        hash_locked.get("source_sample_id", ""),
        graph.get("source_sample_id", ""),
        manifest_candidate.get("sample_id", candidate_id) and expected_source,
    ]
    protein_paths = [
        schema.get("protein_pdb_path", ""),
        hash_locked.get("protein_pdb_path", ""),
        graph.get("protein_pdb_path", ""),
        manifest_candidate.get("protein_pdb_path", ""),
    ]
    ligand_paths = [
        dry.get("ligand_sdf_path", ""),
        schema.get("ligand_sdf_path", ""),
        hash_locked.get("ligand_sdf_path", ""),
        graph.get("ligand_sdf_path", ""),
        manifest_candidate.get("ligand_sdf_path", ""),
    ]
    protein_path = graph.get("protein_pdb_path", hash_locked.get("protein_pdb_path", ""))
    ligand_path = graph.get("ligand_sdf_path", hash_locked.get("ligand_sdf_path", ""))
    protein_exists = path_exists(protein_path)
    ligand_exists = path_exists(ligand_path)
    protein_sha_values = [hash_locked.get("protein_pdb_sha256", ""), graph.get("protein_pdb_sha256", "")]
    ligand_sha_values = [hash_locked.get("ligand_sdf_sha256", ""), graph.get("ligand_sdf_sha256", "")]
    current_protein_hash_matches = protein_exists and sha256_file(protein_path) == graph.get("protein_pdb_sha256", "")
    current_ligand_hash_matches = ligand_exists and sha256_file(ligand_path) == graph.get("ligand_sdf_sha256", "")
    ligand_atom_count = to_int(graph.get("ligand_atom_count", ""))
    ligand_heavy_atom_count = to_int(graph.get("ligand_heavy_atom_count", ""))
    ligand_bond_count = to_int(graph.get("ligand_bond_count", ""))
    protein_atom_count = to_int(graph.get("protein_atom_count", ""))
    protein_residue_count = to_int(graph.get("protein_residue_count", ""))

    checks = [
        ("dry_run_candidate_not_found_once", unique_bool(indexes["dry_candidates"], candidate_id)),
        ("schema_valid_candidate_not_found_once", unique_bool(indexes["schema_candidates"], candidate_id)),
        ("hash_locked_candidate_not_found_once", unique_bool(indexes["hash_candidates"], candidate_id)),
        ("graph_preview_candidate_not_found_once", unique_bool(indexes["graph_candidates"], candidate_id)),
        ("manifest_candidate_row_not_found_once", unique_bool(indexes["manifest"], candidate_id)),
        ("manifest_source_row_not_found_once", unique_bool(indexes["manifest"], expected_source)),
        ("source_mapping_inconsistent", same_nonempty(source_values) and source_values[0] == expected_source),
        ("protein_pdb_path_inconsistent", same_nonempty(protein_paths)),
        ("ligand_sdf_path_inconsistent", same_nonempty(ligand_paths) and ligand_paths[0] == expected_ligand),
        ("protein_pdb_missing", protein_exists),
        ("ligand_sdf_missing", ligand_exists),
        ("protein_pdb_sha256_inconsistent", same_nonempty(protein_sha_values)),
        ("ligand_sdf_sha256_inconsistent", same_nonempty(ligand_sha_values)),
        ("current_protein_pdb_sha256_mismatch", current_protein_hash_matches),
        ("current_ligand_sdf_sha256_mismatch", current_ligand_hash_matches),
        ("dry_run_status_not_passed", dry_report.get("dataset_assembly_dry_run_status", "") == "post_manifest_dataset_assembly_dry_run_passed"),
        ("dry_run_candidate_not_written", dry_report.get("candidate_written_to_dry_run_list", "") == "true"),
        ("dry_run_real_dataset_generated_not_false", dry_report.get("real_dataset_generated", "") == "false"),
        ("dry_run_training_ready_not_false", dry_report.get("training_ready", "") == "false"),
        ("schema_validation_status_not_passed", schema_report.get("schema_validation_status", "") == "dataset_assembly_schema_validation_passed"),
        ("schema_valid_candidate_not_written", schema_report.get("schema_valid_candidate_written", "") == "true"),
        ("schema_real_dataset_generated_not_false", schema_report.get("real_dataset_generated", "") == "false"),
        ("schema_training_ready_not_false", schema_report.get("training_ready", "") == "false"),
        ("file_hash_gate_not_passed", hash_report.get("file_existence_and_hash_gate_status", "") == "file_existence_and_hash_gate_passed"),
        ("hash_locked_candidate_not_written", hash_report.get("hash_locked_candidate_written", "") == "true"),
        ("hash_real_dataset_generated_not_false", hash_report.get("real_dataset_generated", "") == "false"),
        ("hash_training_ready_not_false", hash_report.get("training_ready", "") == "false"),
        ("graph_preview_status_not_passed", graph_report.get("graph_preview_status", "") == "dataset_assembly_graph_preview_passed"),
        ("graph_preview_candidate_not_written", graph_report.get("graph_preview_candidate_written", "") == "true"),
        ("graph_real_dataset_generated_not_false", graph_report.get("real_dataset_generated", "") == "false"),
        ("graph_training_ready_not_false", graph_report.get("training_ready", "") == "false"),
        ("ligand_atom_count_not_positive", ligand_atom_count is not None and ligand_atom_count > 0),
        ("ligand_heavy_atom_count_not_positive", ligand_heavy_atom_count is not None and ligand_heavy_atom_count > 0),
        ("ligand_bond_count_not_positive", ligand_bond_count is not None and ligand_bond_count > 0),
        ("protein_atom_count_not_positive", protein_atom_count is not None and protein_atom_count > 0),
        ("protein_residue_count_not_positive", protein_residue_count is not None and protein_residue_count > 0),
        ("reactive_residue_not_found", graph.get("reactive_residue_found", "") == "true"),
        ("reactive_atom_not_found", graph.get("reactive_atom_found", "") == "true"),
    ]
    reasons = [reason for reason, passed in checks if not passed]
    passed = not reasons
    report = {
        "candidate_id": candidate_id,
        "source_sample_id": graph.get("source_sample_id", expected_source),
        "pre_reaction_sample_id": graph.get("pre_reaction_sample_id", candidate_id),
        "dry_run_candidate_found_once": str(unique_bool(indexes["dry_candidates"], candidate_id)).lower(),
        "schema_valid_candidate_found_once": str(unique_bool(indexes["schema_candidates"], candidate_id)).lower(),
        "hash_locked_candidate_found_once": str(unique_bool(indexes["hash_candidates"], candidate_id)).lower(),
        "graph_preview_candidate_found_once": str(unique_bool(indexes["graph_candidates"], candidate_id)).lower(),
        "manifest_candidate_row_found_once": str(unique_bool(indexes["manifest"], candidate_id)).lower(),
        "manifest_source_row_found_once": str(unique_bool(indexes["manifest"], expected_source)).lower(),
        "source_mapping_consistent": str(same_nonempty(source_values) and source_values[0] == expected_source).lower(),
        "protein_pdb_path_consistent": str(same_nonempty(protein_paths)).lower(),
        "ligand_sdf_path_consistent": str(same_nonempty(ligand_paths) and ligand_paths[0] == expected_ligand).lower(),
        "protein_pdb_exists": str(protein_exists).lower(),
        "ligand_sdf_exists": str(ligand_exists).lower(),
        "protein_pdb_sha256_consistent": str(same_nonempty(protein_sha_values)).lower(),
        "ligand_sdf_sha256_consistent": str(same_nonempty(ligand_sha_values)).lower(),
        "current_protein_pdb_sha256_matches_record": str(current_protein_hash_matches).lower(),
        "current_ligand_sdf_sha256_matches_record": str(current_ligand_hash_matches).lower(),
        "dry_run_status_passed": str(dry_report.get("dataset_assembly_dry_run_status", "") == "post_manifest_dataset_assembly_dry_run_passed").lower(),
        "schema_validation_status_passed": str(schema_report.get("schema_validation_status", "") == "dataset_assembly_schema_validation_passed").lower(),
        "file_existence_and_hash_gate_passed": str(hash_report.get("file_existence_and_hash_gate_status", "") == "file_existence_and_hash_gate_passed").lower(),
        "graph_preview_status_passed": str(graph_report.get("graph_preview_status", "") == "dataset_assembly_graph_preview_passed").lower(),
        "ligand_atom_count": graph.get("ligand_atom_count", "0"),
        "ligand_heavy_atom_count": graph.get("ligand_heavy_atom_count", "0"),
        "ligand_bond_count": graph.get("ligand_bond_count", "0"),
        "protein_atom_count": graph.get("protein_atom_count", "0"),
        "protein_residue_count": graph.get("protein_residue_count", "0"),
        "reactive_residue_found": graph.get("reactive_residue_found", "false"),
        "reactive_atom_found": graph.get("reactive_atom_found", "false"),
        "final_readiness_candidate_written": str(passed).lower(),
        "final_readiness_status": "dataset_assembly_final_readiness_passed" if passed else "blocked",
        "ready_for_packaging_dry_run": str(passed).lower(),
        "manifest_modified": "false",
        "sdf_modified": "false",
        "sdf_generated": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(reasons),
        "recommended_next_action": (
            "build_dataset_packaging_dry_run_not_training"
            if passed
            else "fix_dataset_assembly_final_readiness_blockers"
        ),
    }
    return report, build_final_candidate(graph) if passed else None


def build_gate(
    *,
    dry_run_candidates_csv: str | Path,
    dry_run_report_csv: str | Path,
    schema_valid_candidates_csv: str | Path,
    schema_validation_report_csv: str | Path,
    hash_locked_candidates_csv: str | Path,
    file_hash_report_csv: str | Path,
    graph_preview_candidates_csv: str | Path,
    graph_preview_report_csv: str | Path,
    manifest_csv: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    indexes = {
        "dry_candidates": index_many(read_csv(dry_run_candidates_csv), "candidate_id"),
        "dry_reports": index_many(read_csv(dry_run_report_csv), "pre_reaction_sample_id"),
        "schema_candidates": index_many(read_csv(schema_valid_candidates_csv), "schema_valid_candidate_id"),
        "schema_reports": index_many(read_csv(schema_validation_report_csv), "candidate_id"),
        "hash_candidates": index_many(read_csv(hash_locked_candidates_csv), "hash_locked_candidate_id"),
        "hash_reports": index_many(read_csv(file_hash_report_csv), "candidate_id"),
        "graph_candidates": index_many(read_csv(graph_preview_candidates_csv), "graph_preview_candidate_id"),
        "graph_reports": index_many(read_csv(graph_preview_report_csv), "candidate_id"),
        "manifest": index_many(read_csv(manifest_csv), "sample_id"),
    }
    reports: list[dict[str, str]] = []
    final_candidates: list[dict[str, str]] = []
    for candidate_id in sorted(TARGETS):
        report, candidate = evaluate_candidate(candidate_id, indexes)
        reports.append(report)
        if candidate is not None:
            final_candidates.append(candidate)
    return reports, final_candidates


def write_csv(rows: list[dict[str, str]], output_csv: str | Path, fieldnames: list[str]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(reports: list[dict[str, str]], final_candidates: list[dict[str, str]]) -> str:
    lines = [
        "# Dataset Assembly Final Readiness Gate Summary",
        "",
        "This is final readiness gate only.",
        "",
        "- It reads dry-run, schema, hash, and graph preview outputs.",
        "- It does not modify manifest files.",
        "- It does not modify or generate SDF files.",
        "- It does not generate real training datasets.",
        "- It does not train or fine-tune any model.",
        "- Passing this gate means candidates can enter packaging dry-run.",
        "- Passing this gate still does not mean the samples are training-ready.",
        "",
        "| candidate_id | source_sample_id | ligand_atom_count | protein_atom_count | reactive_residue_found | reactive_atom_found | final_readiness_status | ready_for_packaging_dry_run | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in reports:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["source_sample_id"],
                    row["ligand_atom_count"],
                    row["protein_atom_count"],
                    row["reactive_residue_found"],
                    row["reactive_atom_found"],
                    row["final_readiness_status"],
                    row["ready_for_packaging_dry_run"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    all_passed = all(row["final_readiness_status"] == "dataset_assembly_final_readiness_passed" for row in reports)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three candidates passed final readiness gate."
                if all_passed
                else "- One or more candidates are blocked by final readiness gate."
            ),
            f"- Final readiness candidates CSV contains exactly 3 rows: {str(len(final_candidates) == 3).lower()}.",
            "- Candidates are ready for packaging dry-run." if all_passed else "- Blockers must be fixed before packaging dry-run.",
            "- Manifest was not modified.",
            "- No SDF files were modified or generated.",
            "- No real dataset was generated.",
            "- No training was run.",
            "- Next step is packaging dry-run, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build dataset assembly final readiness gate outputs.")
    parser.add_argument("--dry_run_candidates_csv", type=Path, required=True)
    parser.add_argument("--dry_run_report_csv", type=Path, required=True)
    parser.add_argument("--schema_valid_candidates_csv", type=Path, required=True)
    parser.add_argument("--schema_validation_report_csv", type=Path, required=True)
    parser.add_argument("--hash_locked_candidates_csv", type=Path, required=True)
    parser.add_argument("--file_hash_report_csv", type=Path, required=True)
    parser.add_argument("--graph_preview_candidates_csv", type=Path, required=True)
    parser.add_argument("--graph_preview_report_csv", type=Path, required=True)
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--output_final_candidates_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command performs final readiness gating only.")
    print("warning: it does not modify manifest or SDF files.")
    print("warning: it does not generate real training datasets.")
    reports, final_candidates = build_gate(
        dry_run_candidates_csv=args.dry_run_candidates_csv,
        dry_run_report_csv=args.dry_run_report_csv,
        schema_valid_candidates_csv=args.schema_valid_candidates_csv,
        schema_validation_report_csv=args.schema_validation_report_csv,
        hash_locked_candidates_csv=args.hash_locked_candidates_csv,
        file_hash_report_csv=args.file_hash_report_csv,
        graph_preview_candidates_csv=args.graph_preview_candidates_csv,
        graph_preview_report_csv=args.graph_preview_report_csv,
        manifest_csv=args.manifest_csv,
    )
    write_csv(final_candidates, args.output_final_candidates_csv, FINAL_CANDIDATE_COLUMNS)
    write_csv(reports, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports, final_candidates), args.output_md)
    print(f"wrote final readiness candidates: {args.output_final_candidates_csv}")
    print(f"wrote final readiness report: {args.output_report_csv}")
    print(f"wrote final readiness summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['candidate_id']}: "
            f"final_readiness_status={row['final_readiness_status']} "
            f"ready_for_packaging_dry_run={row['ready_for_packaging_dry_run']} "
            f"training_ready={row['training_ready']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
