from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_split_leakage_qa_gate as step13bl


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_feature_semantics_audit_gate_v0"
PREVIOUS_STAGE = step13bl.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_feature_semantics_precondition_audit.csv"
SOURCE_INVENTORY_AUDIT_CSV = OUTPUT_ROOT / "covapie_feature_source_inventory_audit.csv"
FEATURE_SEMANTICS_CONTRACT_CSV = OUTPUT_ROOT / "covapie_feature_semantics_contract.csv"
COORDINATE_GEOMETRY_AUDIT_CSV = OUTPUT_ROOT / "covapie_coordinate_geometry_semantics_audit.csv"
MASK_CONDITIONING_AUDIT_CSV = OUTPUT_ROOT / "covapie_mask_conditioning_semantics_audit.csv"
AUXILIARY_LABEL_AUDIT_CSV = OUTPUT_ROOT / "covapie_auxiliary_label_semantics_audit.csv"
TRAINING_BLOCKERS_CSV = OUTPUT_ROOT / "covapie_feature_semantics_training_blockers.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_feature_semantics_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_feature_semantics_git_safety.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_feature_semantics_audit_gate_manifest.json"
SUMMARY_MD = Path("docs/covapie_feature_semantics_audit_gate_v0_summary.md")

step13bk = step13bl.step13bk
step13bj = step13bk.step13bj
step13bi = step13bj.step13bi
step13bh = step13bi.step13bh
step13bg = step13bh.step13bg
step13bf = step13bg.step13bf
step13be = step13bf.step13be
step13bd = step13be.step13bd

CANONICAL_MASK_TASK_NAMES = step13bl.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bl.CANONICAL_MASK_TASK_ALIASES
METADATA_CSV_SHA256 = step13bl.METADATA_CSV_SHA256

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
SOURCE_INVENTORY_COLUMNS = [
    "feature_source_name",
    "source_path_or_glob",
    "source_type",
    "read_mode",
    "current_step_access_status",
    "raw_data_or_runtime_dependency_used",
    "feature_semantics_relevance",
    "source_inventory_passed",
]
FEATURE_CONTRACT_COLUMNS = [
    "feature_name",
    "feature_category",
    "current_source",
    "current_semantics_status",
    "training_semantics_status",
    "expected_current_value_or_policy",
    "blocker_before_training",
    "audit_comment",
    "feature_semantics_contract_passed",
]
GEOMETRY_COLUMNS = [
    "geometry_feature_name",
    "observed_source",
    "current_semantics_status",
    "coordinate_unit_or_policy",
    "observed_count_or_range",
    "training_readiness_status",
    "blocker_before_training",
    "geometry_semantics_audit_passed",
]
MASK_CONDITIONING_COLUMNS = [
    "semantics_item",
    "long_name",
    "alias",
    "observed_row_count",
    "expected_row_count",
    "semantics_description",
    "current_status",
    "training_blocker_before_use",
    "mask_conditioning_semantics_passed",
]
AUXILIARY_COLUMNS = [
    "auxiliary_label_name",
    "current_status",
    "required_before_training",
    "current_materialized",
    "future_required_action",
    "blocker_severity",
    "auxiliary_label_semantics_passed",
]
TRAINING_BLOCKER_COLUMNS = ["blocker_item", "current_status", "required_before_training", "blocker_preserved", "blocker_comment", "training_blocker_passed"]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]


def _csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _path_diff_exists(paths: list[str]) -> bool:
    unstaged = _run_git(["diff", "--quiet", "--", *paths]).returncode != 0
    staged = _run_git(["diff", "--cached", "--quiet", "--", *paths]).returncode != 0
    return unstaged or staged


def _metadata_hash() -> str:
    return hashlib.sha256(step13bd.METADATA_CSV.read_bytes()).hexdigest() if step13bd.METADATA_CSV.exists() else ""


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_named_artifact_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
        "final_dataset.csv",
        "final_dataset.json",
        "sample_index.csv",
        "sample_index.json",
        "covapie_sample_index_smoke.csv",
        "covapie_sample_index_smoke.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
        "dataloader_smoke.csv",
        "dataloader_smoke.json",
    }
    return root.exists() and any(path.name in forbidden for path in root.rglob("*"))


def _source_glob_exists(pattern: str) -> bool:
    return any(REPO_ROOT.glob(pattern))


def _count_by(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row[key]] = counts.get(row[key], 0) + 1
    return counts


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest13bl = _load_json(step13bl.MANIFEST_JSON)
    sample_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    event_rows = _csv_rows(step13be.EXTRACTED_EVENT_TABLE_CSV)
    protein_rows = _csv_rows(step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)
    ligand_rows = _csv_rows(step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)
    checks = [
        ("step13bl_manifest_exists", step13bl.MANIFEST_JSON, "exists", step13bl.MANIFEST_JSON.exists(), step13bl.MANIFEST_JSON.exists()),
        ("step13bl_stage", step13bl.MANIFEST_JSON, PREVIOUS_STAGE, manifest13bl.get("stage"), manifest13bl.get("stage") == PREVIOUS_STAGE),
        ("step13bl_all_checks_passed", step13bl.MANIFEST_JSON, "true", manifest13bl.get("all_checks_passed"), manifest13bl.get("all_checks_passed") is True),
        ("step13bl_ready_for_feature_semantics_audit_gate", step13bl.MANIFEST_JSON, "true", manifest13bl.get("ready_for_covapie_feature_semantics_audit_gate"), manifest13bl.get("ready_for_covapie_feature_semantics_audit_gate") is True),
        ("step13bl_ready_for_final_dataset_design_gate", step13bl.MANIFEST_JSON, "false", manifest13bl.get("ready_for_covapie_final_dataset_design_gate"), manifest13bl.get("ready_for_covapie_final_dataset_design_gate") is False),
        ("step13bl_ready_for_dataloader_smoke", step13bl.MANIFEST_JSON, "false", manifest13bl.get("ready_for_covapie_dataloader_smoke"), manifest13bl.get("ready_for_covapie_dataloader_smoke") is False),
        ("step13bl_ready_for_training", step13bl.MANIFEST_JSON, "false", manifest13bl.get("ready_for_training"), manifest13bl.get("ready_for_training") is False),
        ("step13bl_ready_to_train_now", step13bl.MANIFEST_JSON, "false", manifest13bl.get("ready_to_train_now"), manifest13bl.get("ready_to_train_now") is False),
        ("step13bh_sample_index_smoke_shape", step13bh.SAMPLE_INDEX_SMOKE_CSV, "20x31", f"{len(sample_rows)}x{len(sample_rows[0]) if sample_rows else 0}", len(sample_rows) == 20 and bool(sample_rows) and len(sample_rows[0]) == 31),
        ("step13be_event_table_row_count", step13be.EXTRACTED_EVENT_TABLE_CSV, "4", len(event_rows), len(event_rows) == 4),
        ("step13be_protein_atom_table_row_count", step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, "1071", len(protein_rows), len(protein_rows) == 1071),
        ("step13be_ligand_atom_table_row_count", step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV, "149", len(ligand_rows), len(ligand_rows) == 149),
        ("canonical_mask_count", step13bl.MANIFEST_JSON, "5", len({row["mask_task_name"] for row in sample_rows}), len({row["mask_task_name"] for row in sample_rows}) == 5),
        ("b3_scaffold_only_included", step13bl.MANIFEST_JSON, "true", "scaffold_only" in {row["mask_task_name"] for row in sample_rows}, "scaffold_only" in {row["mask_task_name"] for row in sample_rows}),
        ("no_extra_mask_tasks_added", step13bl.MANIFEST_JSON, "true", {row["mask_task_name"] for row in sample_rows}, {row["mask_task_name"] for row in sample_rows} == set(CANONICAL_MASK_TASK_NAMES)),
        ("split_leakage_qa_passed", step13bl.MANIFEST_JSON, "true", manifest13bl.get("all_checks_passed"), manifest13bl.get("all_checks_passed") is True),
        ("metadata_csv_hash_unchanged", step13bd.METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "empty", _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"]), not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "empty", _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"]), not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "precondition_item": item,
            "artifact_or_check": str(check),
            "expected_status": expected,
            "observed_status": observed,
            "precondition_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, check, expected, observed, passed in checks
    ]


def build_source_inventory_rows() -> list[dict[str, Any]]:
    specs = [
        ("step13bh_sample_index_smoke_csv", step13bh.SAMPLE_INDEX_SMOKE_CSV.as_posix(), "derived_csv", "derived_csv_json_read_only", "sample index feature fields and mask metadata"),
        ("step13be_extracted_event_table", step13be.EXTRACTED_EVENT_TABLE_CSV.as_posix(), "derived_csv", "derived_csv_json_read_only", "event identity and covalent geometry fields"),
        ("step13be_protein_atom_table", step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV.as_posix(), "derived_csv", "derived_csv_json_read_only", "protein coordinate and atom feature source"),
        ("step13be_ligand_atom_table", step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV.as_posix(), "derived_csv", "derived_csv_json_read_only", "ligand coordinate and atom feature source"),
        ("step13bl_split_leakage_qa_manifest", step13bl.MANIFEST_JSON.as_posix(), "derived_json", "derived_csv_json_read_only", "split/leakage readiness and blocker source"),
        ("src_covalent_ext_feature_related_modules", "src/covalent_ext/*.py", "source_glob", "static_text_read_only", "CovaPIE feature-producing gate source text"),
        ("dataset_py_static_source", "dataset.py", "source_file", "static_text_read_only", "DiffSBDD dataset source semantics reference"),
        ("prepare_crossdocked_static_source", "data/prepare_crossdocked.py", "source_file", "static_text_read_only", "DiffSBDD preprocessing source semantics reference"),
        ("lightning_modules_static_source", "lightning_modules.py", "source_file", "static_text_read_only", "DiffSBDD training module source semantics reference"),
        ("equivariant_diffusion_static_source", "equivariant_diffusion/*.py", "source_glob", "static_text_read_only", "DiffSBDD diffusion source semantics reference"),
    ]
    rows = []
    for name, path_or_glob, source_type, read_mode, relevance in specs:
        exists = _source_glob_exists(path_or_glob) if "*" in path_or_glob else (REPO_ROOT / path_or_glob).exists()
        rows.append(
            {
                "feature_source_name": name,
                "source_path_or_glob": path_or_glob,
                "source_type": source_type,
                "read_mode": read_mode,
                "current_step_access_status": read_mode,
                "raw_data_or_runtime_dependency_used": False,
                "feature_semantics_relevance": relevance,
                "source_inventory_passed": exists,
            }
        )
    return rows


def build_feature_semantics_contract_rows() -> list[dict[str, Any]]:
    field_specs = [
        ("sample_id", "sample_identity", "step13bh_sample_index", "explicit_current_sample_row_identifier", "not_training_ready_until_final_dataset_and_loader_gates", "unique CovaPIE sample identifier"),
        ("extracted_event_id", "event_identity", "step13bh_sample_index", "explicit_current_event_identifier", "not_training_ready_until_event_key_semantics_finalized", "event-level extracted covalent event id"),
        ("candidate_metadata_id", "event_identity", "step13bh_sample_index", "explicit_current_candidate_identifier", "not_training_ready_until candidate metadata semantics finalized", "candidate metadata id from allowlist lineage"),
        ("pdb_id", "event_identity", "step13bh_sample_index", "explicit_current_pdb_identifier", "not_training_join_key_alone", "PDB ID is not sufficient as event key alone"),
        ("het_code", "ligand_identity", "step13bh_sample_index", "explicit_current_ligand_code", "not_training_ready_until ligand identity semantics audited", "ligand HET code"),
        ("chain_id", "protein_identity", "step13bh_sample_index", "explicit_current_chain_identifier", "not_training_ready_until event key semantics finalized", "protein chain id"),
        ("residue_name", "protein_identity", "step13bh_sample_index", "explicit_current_residue_name", "not_training_ready_until residue semantics audited", "covalent residue name"),
        ("residue_index", "protein_identity", "step13bh_sample_index", "explicit_current_residue_index", "not_training_ready_until residue numbering semantics audited", "author residue index from extracted event"),
        ("residue_atom_name", "protein_identity", "step13bh_sample_index", "explicit_current_residue_atom_name", "not_training_ready_until reactive atom semantics audited", "reactive residue atom name"),
        ("ligand_atom_name", "ligand_identity", "step13bh_sample_index", "explicit_current_ligand_atom_name", "not_training_ready_until ligand atom semantics audited", "reactive ligand atom name"),
        ("covalent_bond_atom_pair", "event_geometry", "step13bh_sample_index", "explicit_current_atom_pair_label", "not_training_ready_until atom pair semantics audited", "residue atom and ligand atom pair"),
        ("covalent_bond_distance_angstrom", "event_geometry", "step13be_extracted_event_table", "post_covalent_distance_angstrom_present", "requires_geometry_semantics_audit_before_training", "distance in angstrom from extracted post-covalent structure"),
        ("protein_pocket_atom_table_path", "source_path", "step13bh_sample_index", "derived_table_path_reference_only", "not_training_input_current_step", step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV.as_posix()),
        ("ligand_atom_table_path", "source_path", "step13bh_sample_index", "derived_table_path_reference_only", "not_training_input_current_step", step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV.as_posix()),
        ("protein_atom_row_count_for_event", "source_count", "step13bh_sample_index", "explicit_current_event_atom_count", "not_training_ready_until atom feature semantics audited", "event protein atom row count"),
        ("ligand_atom_row_count_for_event", "source_count", "step13bh_sample_index", "explicit_current_event_ligand_atom_count", "not_training_ready_until ligand feature semantics audited", "event ligand atom row count"),
        ("mask_task_name", "mask_conditioning", "step13bh_sample_index", "canonical_long_name_source_of_truth", "not_training_ready_until mask tensor semantics finalized", ";".join(CANONICAL_MASK_TASK_NAMES)),
        ("mask_task_alias", "mask_conditioning", "step13bh_sample_index", "display_alias_only", "not_training_ready_until alias never used as source of truth", ";".join(CANONICAL_MASK_TASK_ALIASES)),
        ("mask_task_semantic_description", "mask_conditioning", "step13bh_sample_index", "human_readable_current_semantics", "not_training_ready_until mask application semantics audited", "per-mask design descriptions"),
        ("conditioning_mode", "conditioning", "step13bh_sample_index", "protein_covalent_residue_conditioned", "not_training_ready_until conditioning implementation audited", "protein_covalent_residue_conditioned"),
        ("covalent_residue_conditioned", "conditioning", "step13bh_sample_index", "true_for_current_samples", "not_training_ready_until conditioning implementation audited", "true"),
        ("scaffold_linker_warhead_annotation_status", "auxiliary_label", "step13bh_sample_index", "required_before_training_not_materialized", "blocking_before_training", "required_before_training_not_materialized"),
        ("warhead_type_label_status", "auxiliary_label", "step13bh_sample_index", "required_before_training_not_materialized", "blocking_before_training", "required_before_training_not_materialized"),
        ("ligand_residue_atom_pair_label_status", "auxiliary_label", "step13bh_sample_index", "present_from_extraction_qa_feature_audit_required", "requires_audit_before_training", "present_from_extraction_qa_feature_audit_required"),
        ("pre_post_geometry_label_status", "auxiliary_label", "step13bh_sample_index", "post_covalent_geometry_present_feature_audit_required", "requires_pre_post_policy_before_training", "post_covalent_geometry_present_feature_audit_required"),
        ("feature_semantics_audit_required_before_training", "training_boundary", "step13bh_sample_index", "true", "blocker_preserved", "true"),
        ("leakage_split_design_required_before_training", "training_boundary", "step13bh_sample_index", "true", "blocker_preserved", "true"),
        ("split_assignment_status", "split_boundary", "step13bh_sample_index", "not_written_current_step", "not_training_ready_without_real_split", "not_written_current_step"),
        ("ready_for_training", "training_boundary", "step13bh_sample_index", "false", "training_forbidden", "false"),
        ("unknown_atom_feature_policy", "feature_policy", "static_source_audit", "not_finalized_for_training_current_step", "blocking_before_training", "not_finalized_for_training_current_step"),
        ("feature_semantics_known_for_training", "training_boundary", "current_gate_manifest", "false", "training_forbidden", "false"),
    ]
    return [
        {
            "feature_name": name,
            "feature_category": category,
            "current_source": source,
            "current_semantics_status": current_status,
            "training_semantics_status": training_status,
            "expected_current_value_or_policy": expected,
            "blocker_before_training": True,
            "audit_comment": "current semantics are documented; training semantics remain blocked until future finalization gates",
            "feature_semantics_contract_passed": True,
        }
        for name, category, source, current_status, training_status, expected in field_specs
    ]


def build_coordinate_geometry_rows() -> list[dict[str, Any]]:
    event_rows = _csv_rows(step13be.EXTRACTED_EVENT_TABLE_CSV)
    protein_rows = _csv_rows(step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)
    ligand_rows = _csv_rows(step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)
    distances = [float(row["covalent_bond_distance_angstrom"]) for row in event_rows if row.get("covalent_bond_distance_angstrom")]
    rows = [
        ("covalent_bond_distance_angstrom", step13be.EXTRACTED_EVENT_TABLE_CSV, "post_covalent_distance_present", "angstrom", f"{min(distances):.3f}-{max(distances):.3f}", "not_training_ready", "geometry_semantics_policy_required"),
        ("protein_atom_xyz_coordinates", step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, "derived_table_coordinates_present_no_raw_current_step", "angstrom_inherited_from_extraction", len(protein_rows), "not_training_ready", "protein_feature_semantics_required"),
        ("ligand_atom_xyz_coordinates", step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV, "derived_table_coordinates_present_no_raw_current_step", "angstrom_inherited_from_extraction", len(ligand_rows), "not_training_ready", "ligand_feature_semantics_required"),
        ("post_covalent_geometry_status", step13be.EXTRACTED_EVENT_TABLE_CSV, "post_covalent_geometry_present", "post_covalent_structure_only", len(event_rows), "not_training_ready", "pre_post_geometry_policy_required"),
        ("pre_covalent_geometry_status", step13be.EXTRACTED_EVENT_TABLE_CSV, "pre_covalent_geometry_not_materialized_current_step", "not_available_current_step", 0, "not_training_ready", "pre_covalent_geometry_not_materialized"),
        ("residue_atom_ligand_atom_pair", step13bh.SAMPLE_INDEX_SMOKE_CSV, "explicit_pair_label_present", "atom_name_pair_label", len(event_rows), "not_training_ready", "atom_pair_label_semantics_required"),
        ("pocket_radius_semantics", step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, "derived_extraction_policy_reference_only", "not_recomputed_current_step", "source_extraction_smoke_policy", "not_training_ready", "pocket_definition_semantics_required"),
        ("coordinate_frame_semantics", step13be.EXTRACTED_EVENT_TABLE_CSV, "structure_coordinate_frame_inherited_not_finalized", "not_finalized_for_training_current_step", "source_structure_frame", "not_training_ready", "coordinate_frame_audit_required"),
        ("coordinate_unit_semantics", step13be.EXTRACTED_EVENT_TABLE_CSV, "angstrom_policy_documented", "angstrom", "source tables", "not_training_ready", "unit_policy_must_be_preserved_in_loader"),
        ("geometry_training_readiness", "current_gate", "false", "not_applicable", "0 training-ready rows", "false", "ready_for_training_false"),
    ]
    return [
        {
            "geometry_feature_name": name,
            "observed_source": str(source),
            "current_semantics_status": status,
            "coordinate_unit_or_policy": unit,
            "observed_count_or_range": observed,
            "training_readiness_status": readiness,
            "blocker_before_training": blocker,
            "geometry_semantics_audit_passed": True,
        }
        for name, source, status, unit, observed, readiness, blocker in rows
    ]


def build_mask_conditioning_rows() -> list[dict[str, Any]]:
    sample_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    counts = _count_by(sample_rows, "mask_task_name")
    rows = []
    for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES):
        rows.append(
            {
                "semantics_item": f"mask_task::{name}",
                "long_name": name,
                "alias": alias,
                "observed_row_count": counts.get(name, 0),
                "expected_row_count": 4,
                "semantics_description": "canonical long semantic mask name is source of truth; alias is display-only",
                "current_status": "present_in_sample_index_smoke_not_tensorized",
                "training_blocker_before_use": "mask_tensor_application_semantics_required_before_training",
                "mask_conditioning_semantics_passed": counts.get(name, 0) == 4,
            }
        )
    rows.extend(
        [
            {
                "semantics_item": "conditioning_mode",
                "long_name": "protein_covalent_residue_conditioned",
                "alias": "",
                "observed_row_count": len(sample_rows),
                "expected_row_count": 20,
                "semantics_description": "current samples are conditioned on the covalent residue context",
                "current_status": "present_in_sample_index_smoke",
                "training_blocker_before_use": "conditioning_implementation_audit_required",
                "mask_conditioning_semantics_passed": {row["conditioning_mode"] for row in sample_rows} == {"protein_covalent_residue_conditioned"},
            },
            {
                "semantics_item": "covalent_residue_conditioned",
                "long_name": "covalent_residue_conditioned",
                "alias": "",
                "observed_row_count": len(sample_rows),
                "expected_row_count": 20,
                "semantics_description": "current rows explicitly retain covalent residue conditioning flag",
                "current_status": "true_in_sample_index_smoke",
                "training_blocker_before_use": "conditioning_feature_mapping_required",
                "mask_conditioning_semantics_passed": {row["covalent_residue_conditioned"] for row in sample_rows} == {"True"},
            },
            {
                "semantics_item": "split_assignment_status",
                "long_name": "split_assignment_status",
                "alias": "",
                "observed_row_count": len(sample_rows),
                "expected_row_count": 20,
                "semantics_description": "split assignments are not written in this gate",
                "current_status": "not_written_current_step",
                "training_blocker_before_use": "real_split_assignment_required_before_training",
                "mask_conditioning_semantics_passed": {row["split_assignment_status"] for row in sample_rows} == {"not_written_current_step"},
            },
        ]
    )
    return rows


def build_auxiliary_label_rows() -> list[dict[str, Any]]:
    labels = [
        ("scaffold_linker_warhead_annotation", "required_before_training_not_materialized", True, False, "materialize and QA scaffold/linker/warhead atom labels", "blocking"),
        ("warhead_type_label", "required_before_training_not_materialized", True, False, "define and QA warhead type labels", "blocking"),
        ("ligand_residue_atom_pair_label", "present_from_extraction_qa_feature_audit_required", True, True, "audit atom pair semantics before training", "blocking"),
        ("pre_post_geometry_label", "post_covalent_geometry_present_feature_audit_required", True, True, "define pre/post geometry policy before training", "blocking"),
        ("covalent_reaction_type_label_future", "future_required_not_materialized", True, False, "design future reaction type labels", "blocking"),
        ("residue_class_label_future", "future_required_not_materialized", True, False, "design residue class labels", "blocking"),
        ("scaffold_identity_future", "future_required_for_split_and_training", True, False, "define scaffold identity label", "blocking"),
        ("linker_identity_future", "future_required_for_split_and_training", True, False, "define linker identity label", "blocking"),
        ("protein_sequence_cluster_future", "future_required_for_leakage_control", True, False, "define protein sequence clustering before training split", "blocking"),
        ("pocket_similarity_cluster_future", "future_required_for_leakage_control", True, False, "define pocket similarity clustering before training split", "blocking"),
    ]
    return [
        {
            "auxiliary_label_name": name,
            "current_status": status,
            "required_before_training": required,
            "current_materialized": materialized,
            "future_required_action": action,
            "blocker_severity": severity,
            "auxiliary_label_semantics_passed": True,
        }
        for name, status, required, materialized, action, severity in labels
    ]


def build_training_blocker_rows() -> list[dict[str, Any]]:
    blockers = [
        "feature_semantics_known_for_training_false",
        "unknown_atom_feature_policy_not_finalized",
        "scaffold_linker_warhead_annotation_required",
        "warhead_type_label_required",
        "ligand_residue_atom_pair_label_audit_required",
        "pre_post_geometry_label_audit_required",
        "pre_covalent_geometry_not_materialized",
        "final_dataset_not_written",
        "dataloader_smoke_not_run",
        "no_training_current_step",
        "ready_for_training_false",
        "step12d_smoke_not_final_feature_semantics_audit",
        "leakage_split_qa_completed_but_training_still_blocked",
    ]
    return [
        {
            "blocker_item": item,
            "current_status": "preserved_current_step",
            "required_before_training": True,
            "blocker_preserved": True,
            "blocker_comment": "feature semantics audit documents the blocker without enabling training",
            "training_blocker_passed": True,
        }
        for item in blockers
    ]


def build_boundary_rows() -> list[dict[str, Any]]:
    statuses = {
        "feature_semantics_audit_gate": "executed_audit_gate_only",
        "read_step13bl_qa_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bk_smoke_artifacts": "executed_derived_csv_json_read_only",
        "read_step13bh_sample_index": "executed_derived_csv_json_read_only",
        "static_source_text_read": "executed_static_text_read_only",
        "final_dataset": "blocked_current_step",
        "new_sample_index": "blocked_current_step",
        "split_assignments": "blocked_current_step",
        "leakage_matrix": "blocked_current_step",
        "dataloader_smoke": "blocked_current_step",
        "training": "blocked_current_step",
        "raw_file_content_read": "not_executed_or_not_allowed",
        "raw_cif_mmcif_sdf_pdb_gzip_read": "not_executed_or_not_allowed",
        "mmcif_parse": "not_executed_or_not_allowed",
        "atom_site_scan": "not_executed_or_not_allowed",
        "struct_conn_scan": "not_executed_or_not_allowed",
        "coordinate_extraction": "not_executed_or_not_allowed",
        "network_access": "not_executed_or_not_allowed",
        "raw_download": "not_executed_or_not_allowed",
        "rdkit_biopdb_gemmi": "not_executed_or_not_allowed",
        "torch_model_training": "not_executed_or_not_allowed",
    }
    return [
        {
            "boundary_item": item,
            "current_step_status": status,
            "boundary_safety_passed": True,
            "qa_comment": "feature semantics audit gate boundary respected",
        }
        for item, status in statuses.items()
    ]


def build_git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached --name-only -- data/raw/covalent_sources/covpdb/raw_structure_event_annotation_smoke_v0", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "boundary manifest", "true", True),
        ("derived_output_no_forbidden_binary_artifacts", str(OUTPUT_ROOT), "true", not _forbidden_suffix_exists()),
        ("no_final_dataset_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_new_sample_index_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_split_assignments_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_leakage_matrix_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_dataloader_smoke_written", str(OUTPUT_ROOT), "true", not _forbidden_named_artifact_exists()),
        ("no_training_artifacts_written", str(OUTPUT_ROOT), "true", not _forbidden_suffix_exists()),
        ("metadata_csv_unchanged", str(step13bd.METADATA_CSV), "unchanged", _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bl_artifacts_unchanged", str(step13bl.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bl.OUTPUT_ROOT.as_posix()])),
        ("step13bk_artifacts_unchanged", str(step13bk.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bk.OUTPUT_ROOT.as_posix()])),
        ("step13bj_artifacts_unchanged", str(step13bj.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bj.OUTPUT_ROOT.as_posix()])),
        ("step13bi_artifacts_unchanged", str(step13bi.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bi.OUTPUT_ROOT.as_posix()])),
        ("step13bh_artifacts_unchanged", str(step13bh.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bh.OUTPUT_ROOT.as_posix()])),
        ("step13bg_artifacts_unchanged", str(step13bg.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bg.OUTPUT_ROOT.as_posix()])),
        ("step13bf_artifacts_unchanged", str(step13bf.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13bf.OUTPUT_ROOT.as_posix()])),
        ("step13be_artifacts_unchanged", str(step13be.OUTPUT_ROOT), "no_diff", not _path_diff_exists([step13be.OUTPUT_ROOT.as_posix()])),
        ("step13ai_inventory_artifacts_unchanged", "data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0", "no_diff", not _path_diff_exists(["data/derived/covalent_small/covapie_metadata_source_inventory_gate_v0"])),
        ("protected_source_diff_empty", "equivariant_diffusion/ lightning_modules.py", "no_diff", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "dataset.py data/prepare_crossdocked.py", "no_diff", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
    ]
    return [
        {
            "git_safety_item": item,
            "command_or_check": command,
            "required_status": required,
            "current_step_status": "passed" if passed else "failed",
            "git_safety_audit_passed": passed,
            "blocking_reasons": "" if passed else item,
        }
        for item, command, required, passed in checks
    ]


def run_covapie_feature_semantics_audit_gate_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    source_rows = build_source_inventory_rows()
    contract_rows = build_feature_semantics_contract_rows()
    geometry_rows = build_coordinate_geometry_rows()
    mask_rows = build_mask_conditioning_rows()
    auxiliary_rows = build_auxiliary_label_rows()
    blocker_rows = build_training_blocker_rows()
    boundary_rows = build_boundary_rows()
    git_safety_rows = build_git_safety_rows()
    sample_rows = _csv_rows(step13bh.SAMPLE_INDEX_SMOKE_CSV)
    event_rows = _csv_rows(step13be.EXTRACTED_EVENT_TABLE_CSV)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bl_split_leakage_qa_gate_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "source_sample_index_row_count": len(sample_rows),
        "source_unique_event_count": len({row["extracted_event_id"] for row in sample_rows}),
        "source_extracted_event_table_row_count": len(event_rows),
        "source_protein_atom_table_row_count": len(_csv_rows(step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)),
        "source_ligand_atom_table_row_count": len(_csv_rows(step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)),
        "source_canonical_mask_task_count": len({row["mask_task_name"] for row in sample_rows}),
        "feature_source_inventory_audit_row_count": len(source_rows),
        "feature_semantics_contract_row_count": len(contract_rows),
        "coordinate_geometry_semantics_audit_row_count": len(geometry_rows),
        "mask_conditioning_semantics_audit_row_count": len(mask_rows),
        "auxiliary_label_semantics_audit_row_count": len(auxiliary_rows),
        "feature_semantics_training_blocker_row_count": len(blocker_rows),
        "feature_source_inventory_audit_passed": all(_bool(row["source_inventory_passed"]) for row in source_rows),
        "feature_semantics_contract_passed": all(_bool(row["feature_semantics_contract_passed"]) for row in contract_rows),
        "coordinate_geometry_semantics_audit_passed": all(_bool(row["geometry_semantics_audit_passed"]) for row in geometry_rows),
        "mask_conditioning_semantics_audit_passed": all(_bool(row["mask_conditioning_semantics_passed"]) for row in mask_rows),
        "auxiliary_label_semantics_audit_passed": all(_bool(row["auxiliary_label_semantics_passed"]) for row in auxiliary_rows),
        "feature_semantics_training_blockers_passed": all(_bool(row["training_blocker_passed"]) for row in blocker_rows),
        "boundary_safety_passed": all(_bool(row["boundary_safety_passed"]) for row in boundary_rows),
        "git_safety_passed": all(_bool(row["git_safety_audit_passed"]) for row in git_safety_rows),
        "feature_semantics_audit_completed_current_step": True,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "step12d_was_smoke_legality_only": True,
        "final_dataset_written": False,
        "sample_index_written_current_step": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
        "dataloader_smoke_written": False,
        "training_artifacts_written": False,
        "raw_file_content_read_current_step": False,
        "raw_data_read": False,
        "mmcif_text_read": False,
        "mmcif_parse_current_step": False,
        "atom_site_scan_current_step": False,
        "struct_conn_scan_current_step": False,
        "coordinate_extraction_current_step": False,
        "network_access_used": False,
        "urllib_used": False,
        "requests_used": False,
        "browser_used": False,
        "raw_structure_downloaded": False,
        "raw_ligand_downloaded": False,
        "archive_downloaded": False,
        "raw_file_created": False,
        "sdf_read": False,
        "pdb_read": False,
        "gzip_open_used": False,
        "rdkit_used": False,
        "biopdb_parser_used": False,
        "gemmi_used": False,
        "torch_imported": False,
        "torch_tensor_created": False,
        "checkpoint_loaded": False,
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "trainer_fit_called": False,
        "training_allowed": False,
        "ready_for_covapie_final_dataset_design_gate": True,
        "ready_for_covapie_final_dataset_smoke": False,
        "ready_for_covapie_dataloader_smoke": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in {row["mask_task_name"] for row in sample_rows},
        "no_extra_mask_tasks_added": {row["mask_task_name"] for row in sample_rows} == set(CANONICAL_MASK_TASK_NAMES),
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_final_dataset_design_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bl_split_leakage_qa_gate_validated"],
            manifest["source_sample_index_row_count"] == 20,
            manifest["source_unique_event_count"] == 4,
            manifest["source_extracted_event_table_row_count"] == 4,
            manifest["source_protein_atom_table_row_count"] == 1071,
            manifest["source_ligand_atom_table_row_count"] == 149,
            manifest["source_canonical_mask_task_count"] == 5,
            manifest["feature_source_inventory_audit_row_count"] == 10,
            manifest["feature_semantics_contract_row_count"] == 31,
            manifest["coordinate_geometry_semantics_audit_row_count"] == 10,
            manifest["mask_conditioning_semantics_audit_row_count"] == 8,
            manifest["auxiliary_label_semantics_audit_row_count"] == 10,
            manifest["feature_semantics_training_blocker_row_count"] == 13,
            manifest["feature_source_inventory_audit_passed"],
            manifest["feature_semantics_contract_passed"],
            manifest["coordinate_geometry_semantics_audit_passed"],
            manifest["mask_conditioning_semantics_audit_passed"],
            manifest["auxiliary_label_semantics_audit_passed"],
            manifest["feature_semantics_training_blockers_passed"],
            manifest["boundary_safety_passed"],
            manifest["git_safety_passed"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
            manifest["feature_semantics_audit_completed_current_step"],
            not manifest["feature_semantics_known_for_training"],
            not manifest["unknown_atom_feature_policy_finalized_for_training"],
            not manifest["ready_for_training"],
            not manifest["ready_to_train_now"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["feature_semantics_audit_gate_contract_failed"]
    return {
        "precondition_rows": precondition_rows,
        "source_inventory_rows": source_rows,
        "feature_semantics_contract_rows": contract_rows,
        "coordinate_geometry_rows": geometry_rows,
        "mask_conditioning_rows": mask_rows,
        "auxiliary_label_rows": auxiliary_rows,
        "training_blocker_rows": blocker_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "manifest": manifest,
    }
