#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


APPROVAL_TOKEN = "APPROVE_REAL_PACKAGING_EXECUTION_STEP_8AG"
PACKAGE_ROOT = "data/derived/covalent_small/packaging_real_review_only"

TARGETS = {
    "BTK_C481_6DI9_pre_reaction": "BTK_C481_6DI9",
    "KRAS_G12C_5F2E_pre_reaction": "KRAS_G12C_5F2E",
    "KRAS_G12C_6OIM_pre_reaction": "KRAS_G12C_6OIM",
}

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "approval_token_valid",
    "execution_gate_plan_row_found_once",
    "execution_gate_report_row_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "execution_gate_status_passed",
    "source_mapping_valid",
    "planned_layout_valid",
    "source_protein_exists",
    "source_ligand_exists",
    "source_protein_hash_matches_plan",
    "source_ligand_hash_matches_plan",
    "manifest_candidate_paths_match_plan",
    "graph_counts_positive",
    "directories_created",
    "protein_copied",
    "ligand_copied",
    "metadata_written",
    "packaged_protein_exists",
    "packaged_ligand_exists",
    "packaged_metadata_exists",
    "packaged_protein_hash_matches_source",
    "packaged_ligand_hash_matches_source",
    "metadata_hashes_match_packaged_files",
    "manifest_modified",
    "source_pdb_modified",
    "source_sdf_modified",
    "package_archive_created",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "real_packaging_execution_status",
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


def one(indexed: dict[str, list[dict[str, str]]], key: str) -> dict[str, str]:
    rows = indexed.get(key, [])
    return rows[0] if len(rows) == 1 else {}


def found_once(indexed: dict[str, list[dict[str, str]]], key: str) -> bool:
    return len(indexed.get(key, [])) == 1


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def to_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def bool_str(value: bool) -> str:
    return str(value).lower()


def positive(value: str) -> bool:
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def destination(root: str, relative_path: str) -> str:
    return f"{root.rstrip('/')}/{relative_path.lstrip('/')}"


def expected_layout(plan: dict[str, str]) -> tuple[str, str, str, str, str, str, str]:
    source_id = plan.get("source_sample_id", "")
    pre_reaction_id = plan.get("pre_reaction_sample_id", "")
    protein_rel = f"proteins/{source_id}.pdb"
    ligand_rel = f"ligands_pre_reaction/{pre_reaction_id}.sdf"
    metadata_rel = f"metadata/{pre_reaction_id}.json"
    return (
        PACKAGE_ROOT,
        protein_rel,
        ligand_rel,
        metadata_rel,
        destination(PACKAGE_ROOT, protein_rel),
        destination(PACKAGE_ROOT, ligand_rel),
        destination(PACKAGE_ROOT, metadata_rel),
    )


def graph_counts_positive(plan: dict[str, str]) -> bool:
    return all(
        positive(plan.get(field, ""))
        for field in [
            "ligand_atom_count",
            "ligand_heavy_atom_count",
            "ligand_bond_count",
            "protein_atom_count",
            "protein_residue_count",
        ]
    )


def has_forbidden_outputs(root: str | Path) -> tuple[bool, bool]:
    base = Path(root)
    if not base.exists():
        return False, False
    archives = any(path.suffix.lower() in {".tar", ".zip", ".tgz"} for path in base.rglob("*") if path.is_file())
    tensors = any(path.suffix.lower() in {".pt", ".pkl", ".npz", ".lmdb"} for path in base.rglob("*") if path.is_file())
    return archives, tensors


def manifest_paths_match(plan: dict[str, str], manifest_candidate: dict[str, str]) -> bool:
    return (
        manifest_candidate.get("protein_pdb_path", "") == plan.get("protein_pdb_path", "")
        and manifest_candidate.get("ligand_sdf_path", "") == plan.get("ligand_sdf_path", "")
    )


def planned_layout_valid(plan: dict[str, str]) -> bool:
    root, protein_rel, ligand_rel, metadata_rel, protein_dest, ligand_dest, metadata_dest = expected_layout(plan)
    return (
        plan.get("planned_package_root", "") == root
        and plan.get("planned_protein_relative_path", "") == protein_rel
        and plan.get("planned_ligand_relative_path", "") == ligand_rel
        and plan.get("planned_metadata_relative_path", "") == metadata_rel
        and plan.get("planned_protein_destination_path", "") == protein_dest
        and plan.get("planned_ligand_destination_path", "") == ligand_dest
        and plan.get("planned_metadata_destination_path", "") == metadata_dest
    )


def gate_report_passed(gate: dict[str, str]) -> bool:
    expected = {
        "execution_gate_status": "real_packaging_execution_gate_passed",
        "execution_gate_plan_row_written": "true",
        "explicit_approval_required_before_copy": "true",
        "ready_for_real_packaging_execution_after_approval": "true",
        "directories_created": "false",
        "files_copied": "false",
        "metadata_written": "false",
        "package_archive_created": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
    }
    return all(gate.get(key, "") == value for key, value in expected.items())


def base_report(candidate_id: str, source_id: str, preflight: dict[str, bool], blockers: list[str]) -> dict[str, str]:
    passed = not blockers
    return {
        "candidate_id": candidate_id,
        "source_sample_id": source_id,
        "pre_reaction_sample_id": candidate_id,
        "approval_token_valid": bool_str(preflight.get("approval_token_valid", False)),
        "execution_gate_plan_row_found_once": bool_str(preflight.get("execution_gate_plan_row_found_once", False)),
        "execution_gate_report_row_found_once": bool_str(preflight.get("execution_gate_report_row_found_once", False)),
        "manifest_candidate_row_found_once": bool_str(preflight.get("manifest_candidate_row_found_once", False)),
        "manifest_source_row_found_once": bool_str(preflight.get("manifest_source_row_found_once", False)),
        "execution_gate_status_passed": bool_str(preflight.get("execution_gate_status_passed", False)),
        "source_mapping_valid": bool_str(preflight.get("source_mapping_valid", False)),
        "planned_layout_valid": bool_str(preflight.get("planned_layout_valid", False)),
        "source_protein_exists": bool_str(preflight.get("source_protein_exists", False)),
        "source_ligand_exists": bool_str(preflight.get("source_ligand_exists", False)),
        "source_protein_hash_matches_plan": bool_str(preflight.get("source_protein_hash_matches_plan", False)),
        "source_ligand_hash_matches_plan": bool_str(preflight.get("source_ligand_hash_matches_plan", False)),
        "manifest_candidate_paths_match_plan": bool_str(preflight.get("manifest_candidate_paths_match_plan", False)),
        "graph_counts_positive": bool_str(preflight.get("graph_counts_positive", False)),
        "directories_created": "false",
        "protein_copied": "false",
        "ligand_copied": "false",
        "metadata_written": "false",
        "packaged_protein_exists": "false",
        "packaged_ligand_exists": "false",
        "packaged_metadata_exists": "false",
        "packaged_protein_hash_matches_source": "false",
        "packaged_ligand_hash_matches_source": "false",
        "metadata_hashes_match_packaged_files": "false",
        "manifest_modified": "false",
        "source_pdb_modified": "false",
        "source_sdf_modified": "false",
        "package_archive_created": "false",
        "real_training_tensor_generated": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "real_packaging_execution_status": "preflight_passed" if passed else "blocked",
        "blocking_reasons": ";".join(blockers),
        "recommended_next_action": "execute_real_packaging_copy" if passed else "fix_real_packaging_execution_blockers",
    }


def evaluate_preflight(
    candidate_id: str,
    source_id: str,
    *,
    approval_token_valid: bool,
    plan_by_id: dict[str, list[dict[str, str]]],
    gate_by_id: dict[str, list[dict[str, str]]],
    manifest_by_id: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, str], dict[str, str] | None]:
    plan = one(plan_by_id, candidate_id)
    gate = one(gate_by_id, candidate_id)
    manifest_candidate = one(manifest_by_id, candidate_id)
    protein_path = Path(plan.get("protein_pdb_path", ""))
    ligand_path = Path(plan.get("ligand_sdf_path", ""))
    protein_exists = bool(plan.get("protein_pdb_path", "")) and protein_path.exists()
    ligand_exists = bool(plan.get("ligand_sdf_path", "")) and ligand_path.exists()
    preflight = {
        "approval_token_valid": approval_token_valid,
        "execution_gate_plan_row_found_once": found_once(plan_by_id, candidate_id),
        "execution_gate_report_row_found_once": found_once(gate_by_id, candidate_id),
        "manifest_candidate_row_found_once": found_once(manifest_by_id, candidate_id),
        "manifest_source_row_found_once": found_once(manifest_by_id, source_id),
        "execution_gate_status_passed": gate_report_passed(gate),
        "source_mapping_valid": plan.get("source_sample_id", "") == source_id and gate.get("source_sample_id", "") == source_id,
        "planned_layout_valid": planned_layout_valid(plan),
        "source_protein_exists": protein_exists,
        "source_ligand_exists": ligand_exists,
        "source_protein_hash_matches_plan": protein_exists and sha256_file(protein_path) == plan.get("protein_pdb_sha256", ""),
        "source_ligand_hash_matches_plan": ligand_exists and sha256_file(ligand_path) == plan.get("ligand_sdf_sha256", ""),
        "manifest_candidate_paths_match_plan": manifest_paths_match(plan, manifest_candidate),
        "graph_counts_positive": graph_counts_positive(plan),
    }
    blockers = [key for key, value in preflight.items() if not value]
    return base_report(candidate_id, source_id, preflight, blockers), plan if not blockers else None


def metadata_for(plan: dict[str, str], manifest_csv: str | Path, plan_csv: str | Path, gate_csv: str | Path) -> dict[str, object]:
    candidate_id = plan["pre_reaction_sample_id"]
    source_id = plan["source_sample_id"]
    return {
        "sample_id": candidate_id,
        "source_sample_id": source_id,
        "pre_reaction_sample_id": candidate_id,
        "protein": {
            "source_path": plan["protein_pdb_path"],
            "packaged_relative_path": plan["planned_protein_relative_path"],
            "packaged_path": plan["planned_protein_destination_path"],
            "sha256": plan["protein_pdb_sha256"],
            "atom_count": plan["protein_atom_count"],
            "residue_count": plan["protein_residue_count"],
        },
        "ligand": {
            "source_path": plan["ligand_sdf_path"],
            "packaged_relative_path": plan["planned_ligand_relative_path"],
            "packaged_path": plan["planned_ligand_destination_path"],
            "sha256": plan["ligand_sdf_sha256"],
            "atom_count": plan["ligand_atom_count"],
            "heavy_atom_count": plan["ligand_heavy_atom_count"],
            "bond_count": plan["ligand_bond_count"],
            "ligand_reactive_atom_id": plan["ligand_reactive_atom_id"],
        },
        "covalent_context": {
            "reactive_residue_chain": plan["reactive_residue_chain"],
            "reactive_residue_id": plan["reactive_residue_id"],
            "reactive_residue_type": plan["reactive_residue_type"],
            "reactive_atom_name": plan["reactive_atom_name"],
            "scaffold_atoms": plan["scaffold_atoms"],
            "linker_atoms": plan["linker_atoms"],
            "warhead_atoms": plan["warhead_atoms"],
            "scaffold_atom_count": plan["scaffold_atom_count"],
            "linker_atom_count": plan["linker_atom_count"],
            "warhead_atom_count": plan["warhead_atom_count"],
        },
        "provenance": {
            "source_manifest": str(manifest_csv),
            "execution_gate_plan_csv": str(plan_csv),
            "execution_gate_report_csv": str(gate_csv),
            "approval_token": APPROVAL_TOKEN,
            "packaging_stage": "real_packaging_execution_step_8ag",
        },
        "safety_flags": {
            "manifest_modified": False,
            "source_sdf_modified": False,
            "source_pdb_modified": False,
            "package_archive_created": False,
            "real_training_tensor_generated": False,
            "real_dataset_generated": False,
            "training_ready": False,
        },
    }


def write_metadata(plan: dict[str, str], manifest_csv: str | Path, plan_csv: str | Path, gate_csv: str | Path) -> None:
    path = Path(plan["planned_metadata_destination_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata_for(plan, manifest_csv, plan_csv, gate_csv), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def metadata_hashes_match(plan: dict[str, str]) -> bool:
    metadata_path = Path(plan["planned_metadata_destination_path"])
    if not metadata_path.exists():
        return False
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    protein_path = Path(plan["planned_protein_destination_path"])
    ligand_path = Path(plan["planned_ligand_destination_path"])
    return (
        data.get("sample_id") == plan["pre_reaction_sample_id"]
        and data.get("source_sample_id") == plan["source_sample_id"]
        and data.get("protein", {}).get("sha256") == sha256_file(protein_path)
        and data.get("ligand", {}).get("sha256") == sha256_file(ligand_path)
    )


def execute_package(
    plans: list[dict[str, str]],
    *,
    manifest_csv: str | Path,
    plan_csv: str | Path,
    gate_csv: str | Path,
    source_hashes_before: dict[str, str],
    manifest_hash_before: str,
) -> list[dict[str, str]]:
    root = Path(PACKAGE_ROOT)
    (root / "proteins").mkdir(parents=True, exist_ok=True)
    (root / "ligands_pre_reaction").mkdir(parents=True, exist_ok=True)
    (root / "metadata").mkdir(parents=True, exist_ok=True)
    for plan in plans:
        shutil.copyfile(plan["protein_pdb_path"], plan["planned_protein_destination_path"])
        shutil.copyfile(plan["ligand_sdf_path"], plan["planned_ligand_destination_path"])
        write_metadata(plan, manifest_csv, plan_csv, gate_csv)
    archive_created, tensor_created = has_forbidden_outputs(root)
    rows: list[dict[str, str]] = []
    for plan in plans:
        source_protein = Path(plan["protein_pdb_path"])
        source_ligand = Path(plan["ligand_sdf_path"])
        packaged_protein = Path(plan["planned_protein_destination_path"])
        packaged_ligand = Path(plan["planned_ligand_destination_path"])
        packaged_metadata = Path(plan["planned_metadata_destination_path"])
        source_pdb_modified = sha256_file(source_protein) != source_hashes_before[str(source_protein)]
        source_sdf_modified = sha256_file(source_ligand) != source_hashes_before[str(source_ligand)]
        manifest_modified = sha256_file(manifest_csv) != manifest_hash_before
        metadata_ok = metadata_hashes_match(plan)
        protein_hash_ok = packaged_protein.exists() and sha256_file(packaged_protein) == sha256_file(source_protein) == plan["protein_pdb_sha256"]
        ligand_hash_ok = packaged_ligand.exists() and sha256_file(packaged_ligand) == sha256_file(source_ligand) == plan["ligand_sdf_sha256"]
        passed = (
            protein_hash_ok
            and ligand_hash_ok
            and packaged_metadata.exists()
            and metadata_ok
            and not manifest_modified
            and not source_pdb_modified
            and not source_sdf_modified
            and not archive_created
            and not tensor_created
        )
        row = {
            "candidate_id": plan["execution_gate_plan_id"],
            "source_sample_id": plan["source_sample_id"],
            "pre_reaction_sample_id": plan["pre_reaction_sample_id"],
            "approval_token_valid": "true",
            "execution_gate_plan_row_found_once": "true",
            "execution_gate_report_row_found_once": "true",
            "manifest_candidate_row_found_once": "true",
            "manifest_source_row_found_once": "true",
            "execution_gate_status_passed": "true",
            "source_mapping_valid": "true",
            "planned_layout_valid": "true",
            "source_protein_exists": "true",
            "source_ligand_exists": "true",
            "source_protein_hash_matches_plan": "true",
            "source_ligand_hash_matches_plan": "true",
            "manifest_candidate_paths_match_plan": "true",
            "graph_counts_positive": "true",
            "directories_created": "true",
            "protein_copied": bool_str(packaged_protein.exists()),
            "ligand_copied": bool_str(packaged_ligand.exists()),
            "metadata_written": bool_str(packaged_metadata.exists()),
            "packaged_protein_exists": bool_str(packaged_protein.exists()),
            "packaged_ligand_exists": bool_str(packaged_ligand.exists()),
            "packaged_metadata_exists": bool_str(packaged_metadata.exists()),
            "packaged_protein_hash_matches_source": bool_str(protein_hash_ok),
            "packaged_ligand_hash_matches_source": bool_str(ligand_hash_ok),
            "metadata_hashes_match_packaged_files": bool_str(metadata_ok),
            "manifest_modified": bool_str(manifest_modified),
            "source_pdb_modified": bool_str(source_pdb_modified),
            "source_sdf_modified": bool_str(source_sdf_modified),
            "package_archive_created": bool_str(archive_created),
            "real_training_tensor_generated": bool_str(tensor_created),
            "real_dataset_generated": "false",
            "pre_reaction_transform_ready": "false",
            "training_ready": "false",
            "real_packaging_execution_status": "real_packaging_execution_passed" if passed else "blocked",
            "blocking_reasons": "" if passed else "post_copy_safety_check_failed",
            "recommended_next_action": "build_real_packaging_execution_qa_not_training" if passed else "inspect_packaging_execution_outputs",
        }
        rows.append(row)
    return rows


def build_blocked_markdown(reports: list[dict[str, str]]) -> str:
    return build_markdown(reports)


def build_markdown(reports: list[dict[str, str]]) -> str:
    lines = [
        "# Real Packaging Execution Summary",
        "",
        "This is real packaging execution for review-only derived artifacts.",
        "",
        "- It copied only approved protein PDB files.",
        "- It copied only approved pre-reaction ligand SDF files.",
        "- It wrote one metadata JSON per approved sample.",
        "- It did not modify manifest files.",
        "- It did not modify source PDB or SDF files.",
        "- It did not create package archives.",
        "- It did not generate training tensor files.",
        "- It did not mark samples as training-ready.",
        "- It did not train or fine-tune any model.",
        "",
        f"- package_root: `{PACKAGE_ROOT}`",
        "",
        "| candidate_id | status | protein_copied | ligand_copied | metadata_written | packaged_protein_hash_matches_source | packaged_ligand_hash_matches_source | metadata_hashes_match_packaged_files | manifest_modified | source_pdb_modified | source_sdf_modified | real_dataset_generated | training_ready |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in reports:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["real_packaging_execution_status"],
                    row["protein_copied"],
                    row["ligand_copied"],
                    row["metadata_written"],
                    row["packaged_protein_hash_matches_source"],
                    row["packaged_ligand_hash_matches_source"],
                    row["metadata_hashes_match_packaged_files"],
                    row["manifest_modified"],
                    row["source_pdb_modified"],
                    row["source_sdf_modified"],
                    row["real_dataset_generated"],
                    row["training_ready"],
                ]
            )
            + " |"
        )
    all_passed = all(row["real_packaging_execution_status"] == "real_packaging_execution_passed" for row in reports)
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three review-only packages were created successfully."
                if all_passed
                else "- One or more review-only packages were blocked or failed safety checks."
            ),
            "- Packaged artifacts are review-only derived curation artifacts.",
            "- No source/raw ligand SDF was modified.",
            "- No source protein PDB was modified.",
            "- Manifest was not modified.",
            "- No package archive was created.",
            "- No real training tensor dataset was generated.",
            "- No sample is training-ready from this step.",
            "- Next step is real packaging QA, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def apply_real_packaging_execution(
    *,
    execution_gate_plan_csv: str | Path,
    execution_gate_report_csv: str | Path,
    manifest_csv: str | Path,
    output_report_csv: str | Path,
    output_md: str | Path,
    approval_token: str,
) -> tuple[list[dict[str, str]], int]:
    approval_token_valid = approval_token == APPROVAL_TOKEN
    plan_by_id = index_many(read_csv(execution_gate_plan_csv), "execution_gate_plan_id")
    gate_by_id = index_many(read_csv(execution_gate_report_csv), "candidate_id")
    manifest_by_id = index_many(read_csv(manifest_csv), "sample_id")
    manifest_hash_before = sha256_file(manifest_csv)
    reports = []
    executable_plans = []
    for candidate_id in sorted(TARGETS):
        report, plan = evaluate_preflight(
            candidate_id,
            TARGETS[candidate_id],
            approval_token_valid=approval_token_valid,
            plan_by_id=plan_by_id,
            gate_by_id=gate_by_id,
            manifest_by_id=manifest_by_id,
        )
        reports.append(report)
        if plan is not None:
            executable_plans.append(plan)
    all_preflight_passed = approval_token_valid and len(executable_plans) == len(TARGETS) and all(
        row["real_packaging_execution_status"] == "preflight_passed" for row in reports
    )
    if not all_preflight_passed:
        for row in reports:
            if row["real_packaging_execution_status"] == "preflight_passed":
                row["real_packaging_execution_status"] = "blocked"
                row["blocking_reasons"] = "global_preflight_blocked_no_files_copied"
                row["recommended_next_action"] = "fix_real_packaging_execution_blockers"
        write_csv(reports, output_report_csv, REPORT_COLUMNS)
        write_markdown(build_blocked_markdown(reports), output_md)
        return reports, 1
    source_hashes_before: dict[str, str] = {}
    for plan in executable_plans:
        source_hashes_before[plan["protein_pdb_path"]] = sha256_file(plan["protein_pdb_path"])
        source_hashes_before[plan["ligand_sdf_path"]] = sha256_file(plan["ligand_sdf_path"])
    reports = execute_package(
        executable_plans,
        manifest_csv=manifest_csv,
        plan_csv=execution_gate_plan_csv,
        gate_csv=execution_gate_report_csv,
        source_hashes_before=source_hashes_before,
        manifest_hash_before=manifest_hash_before,
    )
    write_csv(reports, output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports), output_md)
    return reports, 0 if all(row["real_packaging_execution_status"] == "real_packaging_execution_passed" for row in reports) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute approved real packaging for review-only derived artifacts.")
    parser.add_argument("--execution_gate_plan_csv", type=Path, required=True)
    parser.add_argument("--execution_gate_report_csv", type=Path, required=True)
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    parser.add_argument("--approval_token", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command performs approved real packaging execution for review-only artifacts.")
    print("warning: it does not modify manifest files, source PDB files, or source SDF files.")
    print("warning: it does not create archives, training tensors, or training-ready flags.")
    reports, exit_code = apply_real_packaging_execution(
        execution_gate_plan_csv=args.execution_gate_plan_csv,
        execution_gate_report_csv=args.execution_gate_report_csv,
        manifest_csv=args.manifest_csv,
        output_report_csv=args.output_report_csv,
        output_md=args.output_md,
        approval_token=args.approval_token,
    )
    print(f"wrote real packaging execution report: {args.output_report_csv}")
    print(f"wrote real packaging execution summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['candidate_id']}: "
            f"status={row['real_packaging_execution_status']} "
            f"protein_copied={row['protein_copied']} "
            f"ligand_copied={row['ligand_copied']} "
            f"metadata_written={row['metadata_written']} "
            f"training_ready={row['training_ready']}"
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
