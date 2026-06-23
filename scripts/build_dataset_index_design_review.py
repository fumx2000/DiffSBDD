#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


TARGETS = {
    "BTK_C481_6DI9_pre_reaction": "BTK_C481_6DI9",
    "KRAS_G12C_5F2E_pre_reaction": "KRAS_G12C_5F2E",
    "KRAS_G12C_6OIM_pre_reaction": "KRAS_G12C_6OIM",
}

INTENDED_DATASET_NAME = "covalent_small_pre_reaction_review_only"
INTENDED_DATASET_ROLE = "smoke_test_pre_reaction_packaged_artifact"
INTENDED_SPLIT = "smoke_test"
SUPPORTED_MASK_LEVELS = "A_warhead_only;B_linker_warhead;B2_scaffold_warhead;C_scaffold_linker_warhead"
REQUIRED_AUXILIARY_LABELS = "warhead_type;ligand_reactive_atom_id;protein_reactive_residue;pre_reaction_geometry_label"
SCHEMA_VERSION = "dataset_index_v0_review_only"

PLAN_COLUMNS = [
    "dataset_index_design_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "package_root",
    "intended_dataset_name",
    "intended_dataset_role",
    "intended_split",
    "packaged_protein_path",
    "packaged_ligand_sdf_path",
    "packaged_metadata_json_path",
    "source_protein_path",
    "source_ligand_sdf_path",
    "packaged_protein_sha256",
    "packaged_ligand_sha256",
    "packaged_metadata_sha256",
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
    "supported_mask_levels",
    "required_auxiliary_labels",
    "planned_index_schema_version",
    "index_design_stage",
    "actual_dataset_index_written",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "ready_for_dataset_index_build_gate",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "package_root_exists",
    "package_subdirs_exist",
    "package_file_counts_valid",
    "packaging_qa_report_row_found_once",
    "packaging_execution_report_row_found_once",
    "execution_gate_plan_row_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "packaging_qa_status_passed",
    "packaging_qa_flags_passed",
    "packaging_execution_status_passed",
    "source_mapping_valid",
    "packaged_files_exist",
    "metadata_json_parseable",
    "metadata_ids_valid",
    "metadata_paths_valid",
    "metadata_hashes_valid",
    "metadata_safety_flags_valid",
    "manifest_paths_match_sources",
    "graph_counts_positive",
    "mask_label_fields_present",
    "forbidden_training_tensors_absent",
    "forbidden_archives_absent",
    "design_plan_row_written",
    "dataset_index_design_review_status",
    "actual_dataset_index_written",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "blocking_reasons",
    "recommended_next_action",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(rows: list[dict[str, str]], output_csv: str | Path, fieldnames: list[str]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def index_many(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    indexed: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        indexed.setdefault(row.get(key, ""), []).append(row)
    return indexed


def found_once(indexed: dict[str, list[dict[str, str]]], key: str) -> bool:
    return len(indexed.get(key, [])) == 1


def one(indexed: dict[str, list[dict[str, str]]], key: str) -> dict[str, str]:
    rows = indexed.get(key, [])
    return rows[0] if len(rows) == 1 else {}


def bool_str(value: bool) -> str:
    return str(value).lower()


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def positive(value: str) -> bool:
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def path_exists(path_value: str) -> bool:
    return bool(path_value) and Path(path_value).is_file()


def package_counts(package_root: str | Path) -> tuple[int, int, int]:
    root = Path(package_root)
    proteins = list((root / "proteins").glob("*.pdb")) if (root / "proteins").is_dir() else []
    ligands = list((root / "ligands_pre_reaction").glob("*.sdf")) if (root / "ligands_pre_reaction").is_dir() else []
    metadata = list((root / "metadata").glob("*.json")) if (root / "metadata").is_dir() else []
    return len(proteins), len(ligands), len(metadata)


def forbidden_counts(package_root: str | Path) -> tuple[int, int]:
    root = Path(package_root)
    if not root.exists():
        return 0, 0
    tensor_suffixes = {".pt", ".pkl", ".npz", ".lmdb"}
    archive_suffixes = {".tar", ".zip", ".tgz"}
    tensor_count = sum(1 for path in root.rglob("*") if path.is_file() and path.suffix.lower() in tensor_suffixes)
    archive_count = sum(1 for path in root.rglob("*") if path.is_file() and path.suffix.lower() in archive_suffixes)
    return tensor_count, archive_count


def load_json(path: str | Path) -> tuple[dict[str, Any], bool]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), True
    except (OSError, json.JSONDecodeError):
        return {}, False


def packaging_qa_flags_passed(row: dict[str, str]) -> bool:
    expected = {
        "protein_hash_chain_valid": "true",
        "ligand_hash_chain_valid": "true",
        "metadata_ids_valid": "true",
        "metadata_paths_valid": "true",
        "metadata_hashes_valid": "true",
        "metadata_provenance_valid": "true",
        "metadata_safety_flags_valid": "true",
        "forbidden_training_tensors_absent": "true",
        "forbidden_archives_absent": "true",
        "files_copied_by_qa": "false",
        "metadata_written_by_qa": "false",
        "manifest_modified_by_qa": "false",
        "source_files_modified_by_qa": "false",
        "real_dataset_generated": "false",
        "training_ready": "false",
    }
    return all(row.get(key, "") == value for key, value in expected.items())


def graph_counts_positive(plan: dict[str, str]) -> bool:
    return all(
        positive(plan.get(field, ""))
        for field in [
            "ligand_atom_count",
            "ligand_heavy_atom_count",
            "ligand_bond_count",
            "protein_atom_count",
            "protein_residue_count",
            "scaffold_atom_count",
            "warhead_atom_count",
        ]
    )


def mask_label_fields_present(plan: dict[str, str]) -> bool:
    return all(
        bool(plan.get(field, "").strip())
        for field in [
            "scaffold_atoms",
            "linker_atoms",
            "warhead_atoms",
            "scaffold_atom_count",
            "linker_atom_count",
            "warhead_atom_count",
        ]
    )


def metadata_ids_valid(metadata: dict[str, Any], candidate_id: str, source_id: str) -> bool:
    return (
        metadata.get("sample_id") == candidate_id
        and metadata.get("source_sample_id") == source_id
        and metadata.get("pre_reaction_sample_id") == candidate_id
    )


def metadata_paths_valid(metadata: dict[str, Any], plan: dict[str, str]) -> bool:
    return (
        metadata.get("protein", {}).get("source_path") == plan.get("protein_pdb_path", "")
        and metadata.get("protein", {}).get("packaged_path") == plan.get("planned_protein_destination_path", "")
        and metadata.get("ligand", {}).get("source_path") == plan.get("ligand_sdf_path", "")
        and metadata.get("ligand", {}).get("packaged_path") == plan.get("planned_ligand_destination_path", "")
    )


def metadata_hashes_valid(metadata: dict[str, Any], protein_sha: str, ligand_sha: str) -> bool:
    return metadata.get("protein", {}).get("sha256") == protein_sha and metadata.get("ligand", {}).get("sha256") == ligand_sha


def metadata_safety_flags_valid(metadata: dict[str, Any]) -> bool:
    flags = metadata.get("safety_flags", {})
    expected_false = [
        "manifest_modified",
        "source_sdf_modified",
        "source_pdb_modified",
        "package_archive_created",
        "real_training_tensor_generated",
        "real_dataset_generated",
        "training_ready",
    ]
    return all(flags.get(key) is False for key in expected_false)


def build_plan_row(plan: dict[str, str], package_root: str | Path) -> dict[str, str]:
    metadata_path = plan["planned_metadata_destination_path"]
    return {
        "dataset_index_design_plan_id": plan["pre_reaction_sample_id"],
        "source_sample_id": plan["source_sample_id"],
        "pre_reaction_sample_id": plan["pre_reaction_sample_id"],
        "package_root": str(package_root),
        "intended_dataset_name": INTENDED_DATASET_NAME,
        "intended_dataset_role": INTENDED_DATASET_ROLE,
        "intended_split": INTENDED_SPLIT,
        "packaged_protein_path": plan["planned_protein_destination_path"],
        "packaged_ligand_sdf_path": plan["planned_ligand_destination_path"],
        "packaged_metadata_json_path": metadata_path,
        "source_protein_path": plan["protein_pdb_path"],
        "source_ligand_sdf_path": plan["ligand_sdf_path"],
        "packaged_protein_sha256": sha256_file(plan["planned_protein_destination_path"]),
        "packaged_ligand_sha256": sha256_file(plan["planned_ligand_destination_path"]),
        "packaged_metadata_sha256": sha256_file(metadata_path),
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
        "supported_mask_levels": SUPPORTED_MASK_LEVELS,
        "required_auxiliary_labels": REQUIRED_AUXILIARY_LABELS,
        "planned_index_schema_version": SCHEMA_VERSION,
        "index_design_stage": "dataset_index_design_review_only_not_training",
        "actual_dataset_index_written": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "ready_for_dataset_index_build_gate": "true",
    }


def evaluate_candidate(
    candidate_id: str,
    *,
    package_root: str | Path,
    qa_by_id: dict[str, list[dict[str, str]]],
    execution_by_id: dict[str, list[dict[str, str]]],
    plan_by_id: dict[str, list[dict[str, str]]],
    manifest_by_id: dict[str, list[dict[str, str]]],
    package_root_exists: bool,
    package_subdirs_exist: bool,
    package_file_counts_valid: bool,
    forbidden_training_tensors_absent: bool,
    forbidden_archives_absent: bool,
) -> tuple[dict[str, str], dict[str, str] | None]:
    source_id = TARGETS[candidate_id]
    qa = one(qa_by_id, candidate_id)
    execution = one(execution_by_id, candidate_id)
    plan = one(plan_by_id, candidate_id)
    manifest_candidate = one(manifest_by_id, candidate_id)
    packaged_protein = plan.get("planned_protein_destination_path", "")
    packaged_ligand = plan.get("planned_ligand_destination_path", "")
    packaged_metadata = plan.get("planned_metadata_destination_path", "")
    packaged_files_exist = all(path_exists(path) for path in [packaged_protein, packaged_ligand, packaged_metadata])
    metadata, metadata_parseable = load_json(packaged_metadata) if path_exists(packaged_metadata) else ({}, False)
    protein_sha = sha256_file(packaged_protein) if path_exists(packaged_protein) else ""
    ligand_sha = sha256_file(packaged_ligand) if path_exists(packaged_ligand) else ""
    metadata_ids_ok = metadata_parseable and metadata_ids_valid(metadata, candidate_id, source_id)
    metadata_paths_ok = metadata_parseable and metadata_paths_valid(metadata, plan)
    metadata_hashes_ok = metadata_parseable and metadata_hashes_valid(metadata, protein_sha, ligand_sha)
    metadata_safety_ok = metadata_parseable and metadata_safety_flags_valid(metadata)
    manifest_paths_match = (
        manifest_candidate.get("protein_pdb_path", "") == plan.get("protein_pdb_path", "")
        and manifest_candidate.get("ligand_sdf_path", "") == plan.get("ligand_sdf_path", "")
    )
    qa_status_passed = qa.get("real_packaging_execution_qa_status", "") == "real_packaging_execution_qa_passed"
    qa_flags_passed = packaging_qa_flags_passed(qa)
    execution_status_passed = (
        execution.get("real_packaging_execution_status", "") == "real_packaging_execution_passed"
        and execution.get("real_dataset_generated", "") == "false"
        and execution.get("training_ready", "") == "false"
    )
    source_mapping_valid = plan.get("source_sample_id", "") == source_id and execution.get("source_sample_id", "") == source_id
    counts_positive = graph_counts_positive(plan)
    labels_present = mask_label_fields_present(plan)
    checks = [
        ("package_root_missing", package_root_exists),
        ("package_subdirs_missing", package_subdirs_exist),
        ("package_file_counts_invalid", package_file_counts_valid),
        ("packaging_qa_report_row_not_found_once", found_once(qa_by_id, candidate_id)),
        ("packaging_execution_report_row_not_found_once", found_once(execution_by_id, candidate_id)),
        ("execution_gate_plan_row_not_found_once", found_once(plan_by_id, candidate_id)),
        ("manifest_candidate_row_not_found_once", found_once(manifest_by_id, candidate_id)),
        ("manifest_source_row_not_found_once", found_once(manifest_by_id, source_id)),
        ("packaging_qa_status_not_passed", qa_status_passed),
        ("packaging_qa_flags_not_passed", qa_flags_passed),
        ("packaging_execution_status_not_passed", execution_status_passed),
        ("source_mapping_invalid", source_mapping_valid),
        ("packaged_files_missing", packaged_files_exist),
        ("metadata_json_not_parseable", metadata_parseable),
        ("metadata_ids_invalid", metadata_ids_ok),
        ("metadata_paths_invalid", metadata_paths_ok),
        ("metadata_hashes_invalid", metadata_hashes_ok),
        ("metadata_safety_flags_invalid", metadata_safety_ok),
        ("manifest_paths_mismatch_sources", manifest_paths_match),
        ("graph_counts_not_positive", counts_positive),
        ("mask_label_fields_missing", labels_present),
        ("forbidden_training_tensors_present", forbidden_training_tensors_absent),
        ("forbidden_archives_present", forbidden_archives_absent),
    ]
    blockers = [reason for reason, passed in checks if not passed]
    passed = not blockers
    report = {
        "candidate_id": candidate_id,
        "source_sample_id": plan.get("source_sample_id", source_id),
        "pre_reaction_sample_id": plan.get("pre_reaction_sample_id", candidate_id),
        "package_root_exists": bool_str(package_root_exists),
        "package_subdirs_exist": bool_str(package_subdirs_exist),
        "package_file_counts_valid": bool_str(package_file_counts_valid),
        "packaging_qa_report_row_found_once": bool_str(found_once(qa_by_id, candidate_id)),
        "packaging_execution_report_row_found_once": bool_str(found_once(execution_by_id, candidate_id)),
        "execution_gate_plan_row_found_once": bool_str(found_once(plan_by_id, candidate_id)),
        "manifest_candidate_row_found_once": bool_str(found_once(manifest_by_id, candidate_id)),
        "manifest_source_row_found_once": bool_str(found_once(manifest_by_id, source_id)),
        "packaging_qa_status_passed": bool_str(qa_status_passed),
        "packaging_qa_flags_passed": bool_str(qa_flags_passed),
        "packaging_execution_status_passed": bool_str(execution_status_passed),
        "source_mapping_valid": bool_str(source_mapping_valid),
        "packaged_files_exist": bool_str(packaged_files_exist),
        "metadata_json_parseable": bool_str(metadata_parseable),
        "metadata_ids_valid": bool_str(metadata_ids_ok),
        "metadata_paths_valid": bool_str(metadata_paths_ok),
        "metadata_hashes_valid": bool_str(metadata_hashes_ok),
        "metadata_safety_flags_valid": bool_str(metadata_safety_ok),
        "manifest_paths_match_sources": bool_str(manifest_paths_match),
        "graph_counts_positive": bool_str(counts_positive),
        "mask_label_fields_present": bool_str(labels_present),
        "forbidden_training_tensors_absent": bool_str(forbidden_training_tensors_absent),
        "forbidden_archives_absent": bool_str(forbidden_archives_absent),
        "design_plan_row_written": bool_str(passed),
        "dataset_index_design_review_status": "dataset_index_design_review_passed" if passed else "blocked",
        "actual_dataset_index_written": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(blockers),
        "recommended_next_action": (
            "prepare_dataset_index_build_gate_not_training"
            if passed
            else "fix_dataset_index_design_review_blockers"
        ),
    }
    return report, build_plan_row(plan, package_root) if passed else None


def build_design_review(
    *,
    packaging_qa_report_csv: str | Path,
    packaging_execution_report_csv: str | Path,
    execution_gate_plan_csv: str | Path,
    manifest_csv: str | Path,
    package_root: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    qa_by_id = index_many(read_csv(packaging_qa_report_csv), "candidate_id")
    execution_by_id = index_many(read_csv(packaging_execution_report_csv), "candidate_id")
    plan_by_id = index_many(read_csv(execution_gate_plan_csv), "execution_gate_plan_id")
    manifest_by_id = index_many(read_csv(manifest_csv), "sample_id")
    root = Path(package_root)
    root_exists = root.exists()
    subdirs_exist = all((root / child).is_dir() for child in ["proteins", "ligands_pre_reaction", "metadata"])
    protein_count, ligand_count, metadata_count = package_counts(root)
    counts_valid = protein_count == 3 and ligand_count == 3 and metadata_count == 3
    tensor_count, archive_count = forbidden_counts(root)
    reports = []
    plan_rows = []
    for candidate_id in sorted(TARGETS):
        report, plan = evaluate_candidate(
            candidate_id,
            package_root=package_root,
            qa_by_id=qa_by_id,
            execution_by_id=execution_by_id,
            plan_by_id=plan_by_id,
            manifest_by_id=manifest_by_id,
            package_root_exists=root_exists,
            package_subdirs_exist=subdirs_exist,
            package_file_counts_valid=counts_valid,
            forbidden_training_tensors_absent=tensor_count == 0,
            forbidden_archives_absent=archive_count == 0,
        )
        reports.append(report)
        if plan is not None:
            plan_rows.append(plan)
    return reports, plan_rows


def build_markdown(reports: list[dict[str, str]], plan_rows: list[dict[str, str]], package_root: str | Path) -> str:
    protein_count, ligand_count, metadata_count = package_counts(package_root)
    tensor_count, archive_count = forbidden_counts(package_root)
    all_passed = all(row["dataset_index_design_review_status"] == "dataset_index_design_review_passed" for row in reports)
    lines = [
        "# Dataset Index Design Review Summary",
        "",
        "This is dataset index design review only.",
        "",
        "- It reads real packaging execution QA outputs and packaged review-only artifacts.",
        "- It does not write an actual dataset index.",
        "- It does not modify manifest files.",
        "- It does not modify source or packaged PDB/SDF/JSON files.",
        "- It does not copy files.",
        "- It does not create package archives.",
        "- It does not generate real training tensor datasets.",
        "- It does not train or fine-tune any model.",
        "- Passing this review still does not mean the samples are training-ready.",
        "",
        "## Planned Dataset Index Schema",
        "",
        f"- intended_dataset_name: `{INTENDED_DATASET_NAME}`",
        f"- intended_dataset_role: `{INTENDED_DATASET_ROLE}`",
        f"- intended_split: `{INTENDED_SPLIT}`",
        f"- planned_index_schema_version: `{SCHEMA_VERSION}`",
        f"- supported_mask_levels: `{SUPPORTED_MASK_LEVELS}`",
        f"- required_auxiliary_labels: `{REQUIRED_AUXILIARY_LABELS}`",
        "",
        "| candidate_id | source_sample_id | packaged_files_exist | metadata_ids_valid | metadata_paths_valid | metadata_hashes_valid | mask_label_fields_present | dataset_index_design_review_status | actual_dataset_index_written | real_dataset_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in reports:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["source_sample_id"],
                    row["packaged_files_exist"],
                    row["metadata_ids_valid"],
                    row["metadata_paths_valid"],
                    row["metadata_hashes_valid"],
                    row["mask_label_fields_present"],
                    row["dataset_index_design_review_status"],
                    row["actual_dataset_index_written"],
                    row["real_dataset_generated"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three packaged review-only samples passed dataset index design review."
                if all_passed
                else "- One or more packaged review-only samples are blocked by dataset index design review."
            ),
            f"- Design plan CSV contains exactly 3 rows: {bool_str(len(plan_rows) == 3)}.",
            "- No actual dataset index was written.",
            "- No archive was created." if archive_count == 0 else "- Forbidden archive files are present.",
            "- No training tensor dataset was generated." if tensor_count == 0 else "- Forbidden training tensor files are present.",
            f"- Package file counts are PDB={protein_count}, SDF={ligand_count}, JSON={metadata_count}.",
            "- Manifest was not modified.",
            "- Source/packaged PDB/SDF/JSON were not modified.",
            "- No training was run.",
            "- Next step is dataset index build gate, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build dataset index design review outputs.")
    parser.add_argument("--packaging_qa_report_csv", type=Path, required=True)
    parser.add_argument("--packaging_execution_report_csv", type=Path, required=True)
    parser.add_argument("--execution_gate_plan_csv", type=Path, required=True)
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--package_root", type=Path, required=True)
    parser.add_argument("--output_design_plan_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command performs dataset index design review only.")
    print("warning: it does not write an actual dataset index or generate training data.")
    print("warning: it does not copy files, modify manifest, or modify PDB/SDF/JSON files.")
    reports, plan_rows = build_design_review(
        packaging_qa_report_csv=args.packaging_qa_report_csv,
        packaging_execution_report_csv=args.packaging_execution_report_csv,
        execution_gate_plan_csv=args.execution_gate_plan_csv,
        manifest_csv=args.manifest_csv,
        package_root=args.package_root,
    )
    write_csv(plan_rows, args.output_design_plan_csv, PLAN_COLUMNS)
    write_csv(reports, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports, plan_rows, args.package_root), args.output_md)
    print(f"wrote dataset index design plan: {args.output_design_plan_csv}")
    print(f"wrote dataset index design review report: {args.output_report_csv}")
    print(f"wrote dataset index design review summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['candidate_id']}: "
            f"status={row['dataset_index_design_review_status']} "
            f"actual_dataset_index_written={row['actual_dataset_index_written']} "
            f"training_ready={row['training_ready']}"
        )
    return 0 if all(row["dataset_index_design_review_status"] == "dataset_index_design_review_passed" for row in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
