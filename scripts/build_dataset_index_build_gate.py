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

INTENDED_DATASET_NAME = "covalent_small_pre_reaction_review_only"
INTENDED_DATASET_ROLE = "smoke_test_pre_reaction_packaged_artifact"
INTENDED_SPLIT = "smoke_test"
SCHEMA_VERSION = "dataset_index_v0_review_only"
PLANNED_INDEX_ROOT = "data/derived/covalent_small/dataset_index_review_only"
PLANNED_DATASET_INDEX_PATH = f"{PLANNED_INDEX_ROOT}/covalent_small_pre_reaction_review_only_index.csv"
PLANNED_DATASET_MANIFEST_PATH = f"{PLANNED_INDEX_ROOT}/covalent_small_pre_reaction_review_only_manifest.json"

REQUIRED_MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
REQUIRED_AUXILIARY_LABELS = [
    "warhead_type",
    "ligand_reactive_atom_id",
    "protein_reactive_residue",
    "pre_reaction_geometry_label",
]

PLAN_COLUMNS = [
    "dataset_index_build_gate_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "intended_dataset_name",
    "intended_dataset_role",
    "intended_split",
    "planned_index_schema_version",
    "planned_index_root",
    "planned_dataset_index_path",
    "planned_dataset_manifest_path",
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
    "build_gate_stage",
    "explicit_approval_required_before_index_write",
    "ready_for_actual_dataset_index_build_after_approval",
    "actual_dataset_index_written",
    "dataset_manifest_written",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "package_root_exists",
    "package_file_counts_valid",
    "design_plan_row_found_once",
    "design_report_row_found_once",
    "packaging_qa_report_row_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "design_review_status_passed",
    "design_plan_ready_for_build_gate",
    "packaging_qa_status_passed",
    "source_mapping_valid",
    "packaged_paths_exist",
    "packaged_hashes_match_design_plan",
    "planned_dataset_identity_valid",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "actual_index_absent_before_gate",
    "dataset_manifest_absent_before_gate",
    "forbidden_training_tensors_absent",
    "forbidden_archives_absent",
    "build_gate_plan_row_written",
    "dataset_index_build_gate_status",
    "explicit_approval_required_before_index_write",
    "ready_for_actual_dataset_index_build_after_approval",
    "actual_dataset_index_written",
    "dataset_manifest_written",
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


def nonnegative(value: str) -> bool:
    try:
        return int(value) >= 0
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


def contains_all(value: str, required_values: list[str]) -> bool:
    present = {part.strip() for part in value.split(";") if part.strip()}
    return all(required in present for required in required_values)


def graph_counts_positive(plan: dict[str, str]) -> bool:
    positive_fields = [
        "ligand_atom_count",
        "ligand_heavy_atom_count",
        "ligand_bond_count",
        "protein_atom_count",
        "protein_residue_count",
        "scaffold_atom_count",
        "warhead_atom_count",
    ]
    return all(positive(plan.get(field, "")) for field in positive_fields) and nonnegative(plan.get("linker_atom_count", ""))


def planned_dataset_identity_valid(plan: dict[str, str]) -> bool:
    return (
        plan.get("intended_dataset_name", "") == INTENDED_DATASET_NAME
        and plan.get("intended_dataset_role", "") == INTENDED_DATASET_ROLE
        and plan.get("intended_split", "") == INTENDED_SPLIT
        and plan.get("planned_index_schema_version", "") == SCHEMA_VERSION
    )


def packaged_hashes_match(plan: dict[str, str]) -> bool:
    protein_path = plan.get("packaged_protein_path", "")
    ligand_path = plan.get("packaged_ligand_sdf_path", "")
    metadata_path = plan.get("packaged_metadata_json_path", "")
    return (
        path_exists(protein_path)
        and path_exists(ligand_path)
        and path_exists(metadata_path)
        and sha256_file(protein_path) == plan.get("packaged_protein_sha256", "")
        and sha256_file(ligand_path) == plan.get("packaged_ligand_sha256", "")
        and sha256_file(metadata_path) == plan.get("packaged_metadata_sha256", "")
    )


def build_plan_row(plan: dict[str, str]) -> dict[str, str]:
    return {
        "dataset_index_build_gate_plan_id": plan["pre_reaction_sample_id"],
        "source_sample_id": plan["source_sample_id"],
        "pre_reaction_sample_id": plan["pre_reaction_sample_id"],
        "intended_dataset_name": plan["intended_dataset_name"],
        "intended_dataset_role": plan["intended_dataset_role"],
        "intended_split": plan["intended_split"],
        "planned_index_schema_version": plan["planned_index_schema_version"],
        "planned_index_root": PLANNED_INDEX_ROOT,
        "planned_dataset_index_path": PLANNED_DATASET_INDEX_PATH,
        "planned_dataset_manifest_path": PLANNED_DATASET_MANIFEST_PATH,
        "packaged_protein_path": plan["packaged_protein_path"],
        "packaged_ligand_sdf_path": plan["packaged_ligand_sdf_path"],
        "packaged_metadata_json_path": plan["packaged_metadata_json_path"],
        "source_protein_path": plan["source_protein_path"],
        "source_ligand_sdf_path": plan["source_ligand_sdf_path"],
        "packaged_protein_sha256": plan["packaged_protein_sha256"],
        "packaged_ligand_sha256": plan["packaged_ligand_sha256"],
        "packaged_metadata_sha256": plan["packaged_metadata_sha256"],
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
        "supported_mask_levels": plan["supported_mask_levels"],
        "required_auxiliary_labels": plan["required_auxiliary_labels"],
        "build_gate_stage": "dataset_index_build_gate_only_not_training",
        "explicit_approval_required_before_index_write": "true",
        "ready_for_actual_dataset_index_build_after_approval": "true",
        "actual_dataset_index_written": "false",
        "dataset_manifest_written": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
    }


def evaluate_candidate(
    candidate_id: str,
    *,
    design_plan_by_id: dict[str, list[dict[str, str]]],
    design_report_by_id: dict[str, list[dict[str, str]]],
    packaging_qa_by_id: dict[str, list[dict[str, str]]],
    manifest_by_id: dict[str, list[dict[str, str]]],
    package_root_exists: bool,
    package_file_counts_valid: bool,
    actual_index_absent: bool,
    dataset_manifest_absent: bool,
    forbidden_training_tensors_absent: bool,
    forbidden_archives_absent: bool,
) -> tuple[dict[str, str], dict[str, str] | None]:
    source_id = TARGETS[candidate_id]
    plan = one(design_plan_by_id, candidate_id)
    report = one(design_report_by_id, candidate_id)
    qa = one(packaging_qa_by_id, candidate_id)
    packaged_paths_exist = all(
        path_exists(plan.get(field, ""))
        for field in ["packaged_protein_path", "packaged_ligand_sdf_path", "packaged_metadata_json_path"]
    )
    hashes_match = packaged_hashes_match(plan)
    source_mapping_valid = plan.get("source_sample_id", "") == source_id
    design_status_passed = (
        report.get("dataset_index_design_review_status", "") == "dataset_index_design_review_passed"
        and report.get("design_plan_row_written", "") == "true"
        and report.get("actual_dataset_index_written", "") == "false"
        and report.get("real_dataset_generated", "") == "false"
        and report.get("training_ready", "") == "false"
    )
    design_ready = (
        plan.get("ready_for_dataset_index_build_gate", "") == "true"
        and plan.get("actual_dataset_index_written", "") == "false"
        and plan.get("real_dataset_generated", "") == "false"
        and plan.get("pre_reaction_transform_ready", "") == "false"
        and plan.get("training_ready", "") == "false"
    )
    qa_status_passed = (
        qa.get("real_packaging_execution_qa_status", "") == "real_packaging_execution_qa_passed"
        and qa.get("real_dataset_generated", "") == "false"
        and qa.get("training_ready", "") == "false"
    )
    mask_levels_valid = contains_all(plan.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS)
    auxiliary_labels_valid = contains_all(plan.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS)
    counts_positive = (
        graph_counts_positive(plan)
        and bool(plan.get("scaffold_atoms", "").strip())
        and bool(plan.get("warhead_atoms", "").strip())
    )
    checks = [
        ("package_root_missing", package_root_exists),
        ("package_file_counts_invalid", package_file_counts_valid),
        ("design_plan_row_not_found_once", found_once(design_plan_by_id, candidate_id)),
        ("design_report_row_not_found_once", found_once(design_report_by_id, candidate_id)),
        ("packaging_qa_report_row_not_found_once", found_once(packaging_qa_by_id, candidate_id)),
        ("manifest_candidate_row_not_found_once", found_once(manifest_by_id, candidate_id)),
        ("manifest_source_row_not_found_once", found_once(manifest_by_id, source_id)),
        ("design_review_status_not_passed", design_status_passed),
        ("design_plan_not_ready_for_build_gate", design_ready),
        ("packaging_qa_status_not_passed", qa_status_passed),
        ("source_mapping_invalid", source_mapping_valid),
        ("packaged_paths_missing", packaged_paths_exist),
        ("packaged_hashes_mismatch_design_plan", hashes_match),
        ("planned_dataset_identity_invalid", planned_dataset_identity_valid(plan)),
        ("mask_levels_invalid", mask_levels_valid),
        ("auxiliary_labels_invalid", auxiliary_labels_valid),
        ("graph_counts_not_positive", counts_positive),
        ("actual_index_already_exists", actual_index_absent),
        ("dataset_manifest_already_exists", dataset_manifest_absent),
        ("forbidden_training_tensors_present", forbidden_training_tensors_absent),
        ("forbidden_archives_present", forbidden_archives_absent),
    ]
    blockers = [reason for reason, passed in checks if not passed]
    passed = not blockers
    gate_plan = build_plan_row(plan) if passed else None
    row = {
        "candidate_id": candidate_id,
        "source_sample_id": plan.get("source_sample_id", source_id),
        "pre_reaction_sample_id": plan.get("pre_reaction_sample_id", candidate_id),
        "package_root_exists": bool_str(package_root_exists),
        "package_file_counts_valid": bool_str(package_file_counts_valid),
        "design_plan_row_found_once": bool_str(found_once(design_plan_by_id, candidate_id)),
        "design_report_row_found_once": bool_str(found_once(design_report_by_id, candidate_id)),
        "packaging_qa_report_row_found_once": bool_str(found_once(packaging_qa_by_id, candidate_id)),
        "manifest_candidate_row_found_once": bool_str(found_once(manifest_by_id, candidate_id)),
        "manifest_source_row_found_once": bool_str(found_once(manifest_by_id, source_id)),
        "design_review_status_passed": bool_str(design_status_passed),
        "design_plan_ready_for_build_gate": bool_str(design_ready),
        "packaging_qa_status_passed": bool_str(qa_status_passed),
        "source_mapping_valid": bool_str(source_mapping_valid),
        "packaged_paths_exist": bool_str(packaged_paths_exist),
        "packaged_hashes_match_design_plan": bool_str(hashes_match),
        "planned_dataset_identity_valid": bool_str(planned_dataset_identity_valid(plan)),
        "mask_levels_valid": bool_str(mask_levels_valid),
        "auxiliary_labels_valid": bool_str(auxiliary_labels_valid),
        "graph_counts_positive": bool_str(counts_positive),
        "actual_index_absent_before_gate": bool_str(actual_index_absent),
        "dataset_manifest_absent_before_gate": bool_str(dataset_manifest_absent),
        "forbidden_training_tensors_absent": bool_str(forbidden_training_tensors_absent),
        "forbidden_archives_absent": bool_str(forbidden_archives_absent),
        "build_gate_plan_row_written": bool_str(passed),
        "dataset_index_build_gate_status": "dataset_index_build_gate_passed" if passed else "blocked",
        "explicit_approval_required_before_index_write": bool_str(passed),
        "ready_for_actual_dataset_index_build_after_approval": bool_str(passed),
        "actual_dataset_index_written": "false",
        "dataset_manifest_written": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": ";".join(blockers),
        "recommended_next_action": (
            "await_explicit_approval_for_actual_dataset_index_build"
            if passed
            else "fix_dataset_index_build_gate_blockers"
        ),
    }
    return row, gate_plan


def build_gate(
    *,
    dataset_index_design_plan_csv: str | Path,
    dataset_index_design_report_csv: str | Path,
    packaging_qa_report_csv: str | Path,
    manifest_csv: str | Path,
    package_root: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    design_plan_by_id = index_many(read_csv(dataset_index_design_plan_csv), "dataset_index_design_plan_id")
    design_report_by_id = index_many(read_csv(dataset_index_design_report_csv), "candidate_id")
    packaging_qa_by_id = index_many(read_csv(packaging_qa_report_csv), "candidate_id")
    manifest_by_id = index_many(read_csv(manifest_csv), "sample_id")
    root = Path(package_root)
    protein_count, ligand_count, metadata_count = package_counts(root)
    tensor_count, archive_count = forbidden_counts(root)
    reports: list[dict[str, str]] = []
    gate_plan: list[dict[str, str]] = []
    for candidate_id in sorted(TARGETS):
        report, plan = evaluate_candidate(
            candidate_id,
            design_plan_by_id=design_plan_by_id,
            design_report_by_id=design_report_by_id,
            packaging_qa_by_id=packaging_qa_by_id,
            manifest_by_id=manifest_by_id,
            package_root_exists=root.exists(),
            package_file_counts_valid=protein_count == 3 and ligand_count == 3 and metadata_count == 3,
            actual_index_absent=not Path(PLANNED_DATASET_INDEX_PATH).exists(),
            dataset_manifest_absent=not Path(PLANNED_DATASET_MANIFEST_PATH).exists(),
            forbidden_training_tensors_absent=tensor_count == 0,
            forbidden_archives_absent=archive_count == 0,
        )
        reports.append(report)
        if plan is not None:
            gate_plan.append(plan)
    return reports, gate_plan


def build_markdown(reports: list[dict[str, str]], gate_plan: list[dict[str, str]]) -> str:
    all_passed = all(row["dataset_index_build_gate_status"] == "dataset_index_build_gate_passed" for row in reports)
    lines = [
        "# Dataset Index Build Gate Summary",
        "",
        "This is dataset index build gate only.",
        "",
        "- It reads dataset index design review outputs and packaged review-only artifacts.",
        "- It does not write the actual dataset index.",
        "- It does not write the dataset manifest.",
        "- It does not modify manifest files.",
        "- It does not modify source or packaged PDB/SDF/JSON files.",
        "- It does not copy files.",
        "- It does not create package archives.",
        "- It does not generate real training tensor datasets.",
        "- It does not train or fine-tune any model.",
        "- Passing this gate means an actual dataset index can be written only after explicit approval.",
        "- Passing this gate still does not mean the samples are training-ready.",
        "",
        "## Planned Index Outputs",
        "",
        f"- planned_index_root: `{PLANNED_INDEX_ROOT}`",
        f"- planned_dataset_index_path: `{PLANNED_DATASET_INDEX_PATH}`",
        f"- planned_dataset_manifest_path: `{PLANNED_DATASET_MANIFEST_PATH}`",
        f"- planned_index_schema_version: `{SCHEMA_VERSION}`",
        f"- intended_dataset_name: `{INTENDED_DATASET_NAME}`",
        f"- intended_split: `{INTENDED_SPLIT}`",
        "",
        "| candidate_id | source_sample_id | packaged_paths_exist | packaged_hashes_match_design_plan | mask_levels_valid | auxiliary_labels_valid | dataset_index_build_gate_status | explicit_approval_required_before_index_write | actual_dataset_index_written | real_dataset_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in reports:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["source_sample_id"],
                    row["packaged_paths_exist"],
                    row["packaged_hashes_match_design_plan"],
                    row["mask_levels_valid"],
                    row["auxiliary_labels_valid"],
                    row["dataset_index_build_gate_status"],
                    row["explicit_approval_required_before_index_write"],
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
                "- All three packaged review-only samples passed dataset index build gate."
                if all_passed
                else "- One or more packaged review-only samples are blocked by dataset index build gate."
            ),
            f"- Build gate plan CSV contains exactly 3 rows: {bool_str(len(gate_plan) == 3)}.",
            "- Explicit approval is required before actual dataset index writing.",
            "- No actual dataset index was written.",
            "- No dataset manifest was written.",
            "- No archive was created.",
            "- No training tensor dataset was generated.",
            "- Manifest was not modified.",
            "- Source/packaged PDB/SDF/JSON were not modified.",
            "- No training was run.",
            "- Next step is explicit approval for actual dataset index build, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build dataset index build gate outputs.")
    parser.add_argument("--dataset_index_design_plan_csv", type=Path, required=True)
    parser.add_argument("--dataset_index_design_report_csv", type=Path, required=True)
    parser.add_argument("--packaging_qa_report_csv", type=Path, required=True)
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--package_root", type=Path, required=True)
    parser.add_argument("--output_build_gate_plan_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command performs dataset index build gating only.")
    print("warning: it does not write an actual dataset index or dataset manifest.")
    print("warning: it does not copy files, modify manifest, create archives, or generate training data.")
    reports, gate_plan = build_gate(
        dataset_index_design_plan_csv=args.dataset_index_design_plan_csv,
        dataset_index_design_report_csv=args.dataset_index_design_report_csv,
        packaging_qa_report_csv=args.packaging_qa_report_csv,
        manifest_csv=args.manifest_csv,
        package_root=args.package_root,
    )
    write_csv(gate_plan, args.output_build_gate_plan_csv, PLAN_COLUMNS)
    write_csv(reports, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports, gate_plan), args.output_md)
    print(f"wrote dataset index build gate plan: {args.output_build_gate_plan_csv}")
    print(f"wrote dataset index build gate report: {args.output_report_csv}")
    print(f"wrote dataset index build gate summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['candidate_id']}: "
            f"status={row['dataset_index_build_gate_status']} "
            f"actual_dataset_index_written={row['actual_dataset_index_written']} "
            f"training_ready={row['training_ready']}"
        )
    return 0 if all(row["dataset_index_build_gate_status"] == "dataset_index_build_gate_passed" for row in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
