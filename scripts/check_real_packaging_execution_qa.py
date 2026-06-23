#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


APPROVAL_TOKEN = "APPROVE_REAL_PACKAGING_EXECUTION_STEP_8AG"

TARGETS = {
    "BTK_C481_6DI9_pre_reaction": "BTK_C481_6DI9",
    "KRAS_G12C_5F2E_pre_reaction": "KRAS_G12C_5F2E",
    "KRAS_G12C_6OIM_pre_reaction": "KRAS_G12C_6OIM",
}

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "package_root_exists",
    "package_subdirs_exist",
    "packaged_file_counts_valid",
    "execution_report_row_found_once",
    "execution_gate_plan_row_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "execution_report_status_passed",
    "execution_report_flags_passed",
    "packaged_protein_exists",
    "packaged_ligand_exists",
    "packaged_metadata_exists",
    "source_protein_exists",
    "source_ligand_exists",
    "protein_hash_chain_valid",
    "ligand_hash_chain_valid",
    "manifest_paths_match_sources",
    "metadata_json_parseable",
    "metadata_ids_valid",
    "metadata_paths_valid",
    "metadata_hashes_valid",
    "metadata_provenance_valid",
    "metadata_safety_flags_valid",
    "forbidden_training_tensors_absent",
    "forbidden_archives_absent",
    "files_copied_by_qa",
    "metadata_written_by_qa",
    "manifest_modified_by_qa",
    "source_files_modified_by_qa",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "real_packaging_execution_qa_status",
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


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bool_str(value: bool) -> str:
    return str(value).lower()


def forbidden_counts(package_root: str | Path) -> tuple[int, int]:
    root = Path(package_root)
    if not root.exists():
        return 0, 0
    tensor_suffixes = {".pt", ".pkl", ".npz", ".lmdb"}
    archive_suffixes = {".tar", ".zip", ".tgz"}
    tensor_count = sum(1 for path in root.rglob("*") if path.is_file() and path.suffix.lower() in tensor_suffixes)
    archive_count = sum(1 for path in root.rglob("*") if path.is_file() and path.suffix.lower() in archive_suffixes)
    return tensor_count, archive_count


def path_exists(path_value: str) -> bool:
    return bool(path_value) and Path(path_value).exists() and Path(path_value).is_file()


def package_counts(package_root: str | Path) -> tuple[int, int, int]:
    root = Path(package_root)
    proteins = list((root / "proteins").glob("*.pdb")) if (root / "proteins").exists() else []
    ligands = list((root / "ligands_pre_reaction").glob("*.sdf")) if (root / "ligands_pre_reaction").exists() else []
    metadata = list((root / "metadata").glob("*.json")) if (root / "metadata").exists() else []
    return len(proteins), len(ligands), len(metadata)


def execution_report_flags_passed(row: dict[str, str]) -> bool:
    expected = {
        "approval_token_valid": "true",
        "directories_created": "true",
        "protein_copied": "true",
        "ligand_copied": "true",
        "metadata_written": "true",
        "packaged_protein_exists": "true",
        "packaged_ligand_exists": "true",
        "packaged_metadata_exists": "true",
        "packaged_protein_hash_matches_source": "true",
        "packaged_ligand_hash_matches_source": "true",
        "metadata_hashes_match_packaged_files": "true",
        "manifest_modified": "false",
        "source_pdb_modified": "false",
        "source_sdf_modified": "false",
        "package_archive_created": "false",
        "real_training_tensor_generated": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
    }
    return all(row.get(key, "") == value for key, value in expected.items())


def load_json(path: Path) -> tuple[dict[str, Any], bool]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), True
    except (OSError, json.JSONDecodeError):
        return {}, False


def metadata_ids_valid(metadata: dict[str, Any], candidate_id: str, source_id: str) -> bool:
    return (
        metadata.get("sample_id") == candidate_id
        and metadata.get("source_sample_id") == source_id
        and metadata.get("pre_reaction_sample_id") == candidate_id
    )


def metadata_paths_valid(
    metadata: dict[str, Any],
    *,
    source_protein: str,
    packaged_protein: str,
    source_ligand: str,
    packaged_ligand: str,
) -> bool:
    return (
        metadata.get("protein", {}).get("source_path") == source_protein
        and metadata.get("protein", {}).get("packaged_path") == packaged_protein
        and metadata.get("ligand", {}).get("source_path") == source_ligand
        and metadata.get("ligand", {}).get("packaged_path") == packaged_ligand
    )


def metadata_hashes_valid(metadata: dict[str, Any], protein_hash: str, ligand_hash: str) -> bool:
    return (
        metadata.get("protein", {}).get("sha256") == protein_hash
        and metadata.get("ligand", {}).get("sha256") == ligand_hash
    )


def metadata_provenance_valid(metadata: dict[str, Any]) -> bool:
    provenance = metadata.get("provenance", {})
    return (
        provenance.get("approval_token") == APPROVAL_TOKEN
        and provenance.get("packaging_stage") == "real_packaging_execution_step_8ag"
    )


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


def evaluate_candidate(
    candidate_id: str,
    *,
    package_root: str | Path,
    execution_report_by_id: dict[str, list[dict[str, str]]],
    execution_plan_by_id: dict[str, list[dict[str, str]]],
    manifest_by_id: dict[str, list[dict[str, str]]],
    package_root_exists: bool,
    package_subdirs_exist: bool,
    packaged_file_counts_valid: bool,
    forbidden_training_tensors_absent: bool,
    forbidden_archives_absent: bool,
) -> dict[str, str]:
    source_id = TARGETS[candidate_id]
    execution_report = one(execution_report_by_id, candidate_id)
    plan = one(execution_plan_by_id, candidate_id)
    manifest_candidate = one(manifest_by_id, candidate_id)
    packaged_protein_value = plan.get("planned_protein_destination_path", "")
    packaged_ligand_value = plan.get("planned_ligand_destination_path", "")
    packaged_metadata_value = plan.get("planned_metadata_destination_path", "")
    source_protein_value = plan.get("protein_pdb_path", "")
    source_ligand_value = plan.get("ligand_sdf_path", "")
    packaged_protein = Path(packaged_protein_value)
    packaged_ligand = Path(packaged_ligand_value)
    packaged_metadata = Path(packaged_metadata_value)
    source_protein = Path(source_protein_value)
    source_ligand = Path(source_ligand_value)
    packaged_protein_exists = path_exists(packaged_protein_value)
    packaged_ligand_exists = path_exists(packaged_ligand_value)
    packaged_metadata_exists = path_exists(packaged_metadata_value)
    source_protein_exists = path_exists(source_protein_value)
    source_ligand_exists = path_exists(source_ligand_value)
    protein_hash = sha256_file(source_protein) if source_protein_exists else ""
    ligand_hash = sha256_file(source_ligand) if source_ligand_exists else ""
    packaged_protein_hash = sha256_file(packaged_protein) if packaged_protein_exists else ""
    packaged_ligand_hash = sha256_file(packaged_ligand) if packaged_ligand_exists else ""
    protein_hash_chain_valid = (
        bool(protein_hash)
        and protein_hash == packaged_protein_hash
        and protein_hash == plan.get("protein_pdb_sha256", "")
    )
    ligand_hash_chain_valid = (
        bool(ligand_hash)
        and ligand_hash == packaged_ligand_hash
        and ligand_hash == plan.get("ligand_sdf_sha256", "")
    )
    manifest_paths_match_sources = (
        manifest_candidate.get("protein_pdb_path", "") == plan.get("protein_pdb_path", "")
        and manifest_candidate.get("ligand_sdf_path", "") == plan.get("ligand_sdf_path", "")
    )
    metadata, metadata_json_parseable = load_json(packaged_metadata) if packaged_metadata_exists else ({}, False)
    ids_valid = metadata_json_parseable and metadata_ids_valid(metadata, candidate_id, source_id)
    paths_valid = metadata_json_parseable and metadata_paths_valid(
        metadata,
        source_protein=plan.get("protein_pdb_path", ""),
        packaged_protein=plan.get("planned_protein_destination_path", ""),
        source_ligand=plan.get("ligand_sdf_path", ""),
        packaged_ligand=plan.get("planned_ligand_destination_path", ""),
    )
    hashes_valid = metadata_json_parseable and metadata_hashes_valid(metadata, packaged_protein_hash, packaged_ligand_hash)
    provenance_valid = metadata_json_parseable and metadata_provenance_valid(metadata)
    safety_flags_valid = metadata_json_parseable and metadata_safety_flags_valid(metadata)
    execution_report_status_passed = (
        execution_report.get("real_packaging_execution_status", "") == "real_packaging_execution_passed"
    )
    checks = [
        ("package_root_missing", package_root_exists),
        ("package_subdirs_missing", package_subdirs_exist),
        ("packaged_file_counts_invalid", packaged_file_counts_valid),
        ("execution_report_row_not_found_once", found_once(execution_report_by_id, candidate_id)),
        ("execution_gate_plan_row_not_found_once", found_once(execution_plan_by_id, candidate_id)),
        ("manifest_candidate_row_not_found_once", found_once(manifest_by_id, candidate_id)),
        ("manifest_source_row_not_found_once", found_once(manifest_by_id, source_id)),
        ("execution_report_status_not_passed", execution_report_status_passed),
        ("execution_report_flags_not_passed", execution_report_flags_passed(execution_report)),
        ("packaged_protein_missing", packaged_protein_exists),
        ("packaged_ligand_missing", packaged_ligand_exists),
        ("packaged_metadata_missing", packaged_metadata_exists),
        ("source_protein_missing", source_protein_exists),
        ("source_ligand_missing", source_ligand_exists),
        ("protein_hash_chain_invalid", protein_hash_chain_valid),
        ("ligand_hash_chain_invalid", ligand_hash_chain_valid),
        ("manifest_paths_mismatch_sources", manifest_paths_match_sources),
        ("metadata_json_not_parseable", metadata_json_parseable),
        ("metadata_ids_invalid", ids_valid),
        ("metadata_paths_invalid", paths_valid),
        ("metadata_hashes_invalid", hashes_valid),
        ("metadata_provenance_invalid", provenance_valid),
        ("metadata_safety_flags_invalid", safety_flags_valid),
        ("forbidden_training_tensors_present", forbidden_training_tensors_absent),
        ("forbidden_archives_present", forbidden_archives_absent),
    ]
    blockers = [reason for reason, passed in checks if not passed]
    passed = not blockers
    return {
        "candidate_id": candidate_id,
        "source_sample_id": plan.get("source_sample_id", source_id),
        "pre_reaction_sample_id": plan.get("pre_reaction_sample_id", candidate_id),
        "package_root_exists": bool_str(package_root_exists),
        "package_subdirs_exist": bool_str(package_subdirs_exist),
        "packaged_file_counts_valid": bool_str(packaged_file_counts_valid),
        "execution_report_row_found_once": bool_str(found_once(execution_report_by_id, candidate_id)),
        "execution_gate_plan_row_found_once": bool_str(found_once(execution_plan_by_id, candidate_id)),
        "manifest_candidate_row_found_once": bool_str(found_once(manifest_by_id, candidate_id)),
        "manifest_source_row_found_once": bool_str(found_once(manifest_by_id, source_id)),
        "execution_report_status_passed": bool_str(execution_report_status_passed),
        "execution_report_flags_passed": bool_str(execution_report_flags_passed(execution_report)),
        "packaged_protein_exists": bool_str(packaged_protein_exists),
        "packaged_ligand_exists": bool_str(packaged_ligand_exists),
        "packaged_metadata_exists": bool_str(packaged_metadata_exists),
        "source_protein_exists": bool_str(source_protein_exists),
        "source_ligand_exists": bool_str(source_ligand_exists),
        "protein_hash_chain_valid": bool_str(protein_hash_chain_valid),
        "ligand_hash_chain_valid": bool_str(ligand_hash_chain_valid),
        "manifest_paths_match_sources": bool_str(manifest_paths_match_sources),
        "metadata_json_parseable": bool_str(metadata_json_parseable),
        "metadata_ids_valid": bool_str(ids_valid),
        "metadata_paths_valid": bool_str(paths_valid),
        "metadata_hashes_valid": bool_str(hashes_valid),
        "metadata_provenance_valid": bool_str(provenance_valid),
        "metadata_safety_flags_valid": bool_str(safety_flags_valid),
        "forbidden_training_tensors_absent": bool_str(forbidden_training_tensors_absent),
        "forbidden_archives_absent": bool_str(forbidden_archives_absent),
        "files_copied_by_qa": "false",
        "metadata_written_by_qa": "false",
        "manifest_modified_by_qa": "false",
        "source_files_modified_by_qa": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "real_packaging_execution_qa_status": "real_packaging_execution_qa_passed" if passed else "blocked",
        "blocking_reasons": ";".join(blockers),
        "recommended_next_action": (
            "prepare_dataset_index_design_review_not_training"
            if passed
            else "fix_real_packaging_execution_qa_blockers"
        ),
    }


def build_qa(
    *,
    execution_report_csv: str | Path,
    execution_gate_plan_csv: str | Path,
    manifest_csv: str | Path,
    package_root: str | Path,
) -> list[dict[str, str]]:
    execution_report_by_id = index_many(read_csv(execution_report_csv), "candidate_id")
    execution_plan_by_id = index_many(read_csv(execution_gate_plan_csv), "execution_gate_plan_id")
    manifest_by_id = index_many(read_csv(manifest_csv), "sample_id")
    root = Path(package_root)
    root_exists = root.exists()
    subdirs_exist = all((root / child).is_dir() for child in ["proteins", "ligands_pre_reaction", "metadata"])
    protein_count, ligand_count, metadata_count = package_counts(root)
    counts_valid = protein_count == 3 and ligand_count == 3 and metadata_count == 3
    tensor_count, archive_count = forbidden_counts(root)
    return [
        evaluate_candidate(
            candidate_id,
            package_root=root,
            execution_report_by_id=execution_report_by_id,
            execution_plan_by_id=execution_plan_by_id,
            manifest_by_id=manifest_by_id,
            package_root_exists=root_exists,
            package_subdirs_exist=subdirs_exist,
            packaged_file_counts_valid=counts_valid,
            forbidden_training_tensors_absent=tensor_count == 0,
            forbidden_archives_absent=archive_count == 0,
        )
        for candidate_id in sorted(TARGETS)
    ]


def build_markdown(rows: list[dict[str, str]], package_root: str | Path) -> str:
    protein_count, ligand_count, metadata_count = package_counts(package_root)
    tensor_count, archive_count = forbidden_counts(package_root)
    all_passed = all(row["real_packaging_execution_qa_status"] == "real_packaging_execution_qa_passed" for row in rows)
    lines = [
        "# Real Packaging Execution QA Summary",
        "",
        "This is real packaging execution QA only.",
        "",
        "- It reads the packaged review-only artifacts.",
        "- It does not modify manifest files.",
        "- It does not modify source or packaged PDB/SDF files.",
        "- It does not modify metadata JSON files.",
        "- It does not copy files.",
        "- It does not create package archives.",
        "- It does not generate real training tensor datasets.",
        "- It does not train or fine-tune any model.",
        "- Passing this QA still does not mean the samples are training-ready.",
        "",
        "## Package Contents",
        "",
        f"- package root: `{package_root}`",
        f"- protein PDB count: {protein_count}",
        f"- ligand SDF count: {ligand_count}",
        f"- metadata JSON count: {metadata_count}",
        f"- forbidden archive count: {archive_count}",
        f"- forbidden training tensor count: {tensor_count}",
        "",
        "| candidate_id | source_sample_id | protein_hash_chain_valid | ligand_hash_chain_valid | metadata_ids_valid | metadata_paths_valid | metadata_hashes_valid | metadata_safety_flags_valid | real_packaging_execution_qa_status | real_dataset_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["source_sample_id"],
                    row["protein_hash_chain_valid"],
                    row["ligand_hash_chain_valid"],
                    row["metadata_ids_valid"],
                    row["metadata_paths_valid"],
                    row["metadata_hashes_valid"],
                    row["metadata_safety_flags_valid"],
                    row["real_packaging_execution_qa_status"],
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
                "- All three packaged review-only samples passed QA."
                if all_passed
                else "- One or more packaged review-only samples are blocked by QA."
            ),
            "- Package contains exactly 3 protein PDB, 3 ligand SDF, and 3 metadata JSON files."
            if protein_count == 3 and ligand_count == 3 and metadata_count == 3
            else "- Package file counts are not exactly 3 protein PDB, 3 ligand SDF, and 3 metadata JSON files.",
            "- No archive was created." if archive_count == 0 else "- Forbidden archive files are present.",
            "- No training tensor dataset was generated." if tensor_count == 0 else "- Forbidden training tensor files are present.",
            "- Manifest was not modified by QA.",
            "- Source/packaged PDB/SDF/metadata were not modified by QA.",
            "- No training was run.",
            "- Next step is dataset index design review, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check real packaging execution QA outputs.")
    parser.add_argument("--execution_report_csv", type=Path, required=True)
    parser.add_argument("--execution_gate_plan_csv", type=Path, required=True)
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--package_root", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command performs read-only real packaging execution QA.")
    print("warning: it does not copy files, modify metadata JSON, modify manifest, or create archives.")
    print("warning: it does not generate training tensors or run training.")
    rows = build_qa(
        execution_report_csv=args.execution_report_csv,
        execution_gate_plan_csv=args.execution_gate_plan_csv,
        manifest_csv=args.manifest_csv,
        package_root=args.package_root,
    )
    write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(rows, args.package_root), args.output_md)
    print(f"wrote real packaging execution QA report: {args.output_report_csv}")
    print(f"wrote real packaging execution QA summary: {args.output_md}")
    for row in rows:
        print(
            f"{row['candidate_id']}: "
            f"qa_status={row['real_packaging_execution_qa_status']} "
            f"training_ready={row['training_ready']}"
        )
    return 0 if all(row["real_packaging_execution_qa_status"] == "real_packaging_execution_qa_passed" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
