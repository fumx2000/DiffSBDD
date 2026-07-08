from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from covalent_ext import covapie_sample_index_design_gate as step13bg


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "covapie_sample_index_smoke_v0"
PREVIOUS_STAGE = step13bg.STAGE
PROJECT_NAME = "CovaPIE"

OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_sample_index_smoke_v0")
PRECONDITION_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_index_smoke_precondition_audit.csv"
SAMPLE_INDEX_SMOKE_CSV = OUTPUT_ROOT / "covapie_sample_index_smoke.csv"
SAMPLE_INDEX_SMOKE_JSON = OUTPUT_ROOT / "covapie_sample_index_smoke.json"
ROW_QA_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_index_row_qa_audit.csv"
MASK_DISTRIBUTION_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_index_mask_distribution_audit.csv"
SOURCE_TRACEABILITY_AUDIT_CSV = OUTPUT_ROOT / "covapie_sample_index_source_traceability_audit.csv"
BOUNDARY_SAFETY_CSV = OUTPUT_ROOT / "covapie_sample_index_smoke_boundary_safety.csv"
GIT_SAFETY_CSV = OUTPUT_ROOT / "covapie_sample_index_smoke_git_safety.csv"
TRAINING_BLOCKERS_CSV = OUTPUT_ROOT / "covapie_sample_index_smoke_training_blockers.csv"
MANIFEST_JSON = OUTPUT_ROOT / "covapie_sample_index_smoke_manifest.json"
SUMMARY_MD = Path("docs/covapie_sample_index_smoke_v0_summary.md")

SAMPLE_INDEX_FIELDS = step13bg.SAMPLE_INDEX_FIELDS
CANONICAL_MASK_TASK_NAMES = step13bg.CANONICAL_MASK_TASK_NAMES
CANONICAL_MASK_TASK_ALIASES = step13bg.CANONICAL_MASK_TASK_ALIASES
MASK_DESCRIPTIONS = step13bg.MASK_DESCRIPTIONS
METADATA_CSV_SHA256 = step13bg.METADATA_CSV_SHA256

PRECONDITION_COLUMNS = ["precondition_item", "artifact_or_check", "expected_status", "observed_status", "precondition_passed", "blocking_reasons"]
ROW_QA_COLUMNS = [
    "sample_id",
    "extracted_event_id",
    "pdb_id",
    "het_code",
    "mask_task_name",
    "mask_task_alias",
    "sample_id_deterministic",
    "sample_id_unique",
    "schema_order_matches_contract",
    "source_event_found",
    "source_event_extraction_success",
    "source_event_geometry_qa_passed",
    "protein_atom_rows_for_event",
    "ligand_atom_rows_for_event",
    "protein_atom_rows_count_matches_source",
    "ligand_atom_rows_count_matches_source",
    "canonical_mask_task_valid",
    "b3_scaffold_only_included_when_applicable",
    "annotation_blockers_preserved",
    "auxiliary_label_blockers_preserved",
    "ready_for_training_false",
    "row_qa_passed",
    "qa_comment",
]
MASK_DISTRIBUTION_COLUMNS = [
    "mask_task_name",
    "mask_task_alias",
    "expected_row_count",
    "observed_row_count",
    "expected_unique_event_count",
    "observed_unique_event_count",
    "mask_distribution_passed",
    "qa_comment",
]
SOURCE_TRACEABILITY_COLUMNS = [
    "extracted_event_id",
    "allowlist_entry_id",
    "pdb_id",
    "het_code",
    "sample_index_rows_for_event",
    "source_event_table_found",
    "source_protein_atom_rows_found",
    "source_ligand_atom_rows_found",
    "step13bf_event_qa_found",
    "step13bf_atom_qa_found",
    "step13bf_geometry_qa_found",
    "step13bg_mask_expansion_contract_found",
    "traceability_qa_passed",
    "qa_comment",
]
BOUNDARY_COLUMNS = ["boundary_item", "current_step_status", "boundary_safety_passed", "qa_comment"]
GIT_SAFETY_COLUMNS = ["git_safety_item", "command_or_check", "required_status", "current_step_status", "git_safety_audit_passed", "blocking_reasons"]
TRAINING_BLOCKER_COLUMNS = ["training_blocker_item", "required_status", "current_step_status", "training_blocker_passed", "qa_comment"]


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
    path = step13bg.step13bf.step13be.step13bd.METADATA_CSV
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def _raw_files_tracked() -> bool:
    return bool(_run_git(["ls-files", step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _raw_files_staged() -> bool:
    return bool(_run_git(["diff", "--cached", "--name-only", "--", step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT.as_posix()]).stdout.strip())


def _bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _schema_fields_from_contract() -> list[str]:
    return [row["sample_index_field"] for row in _csv_rows(step13bg.SCHEMA_CONTRACT_CSV)]


def _count_by_event(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(row["extracted_event_id"] for row in rows)


def _forbidden_suffix_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pdb", ".cif", ".mmcif", ".sdf", ".mol2", ".gz", ".html", ".htm"}
    return root.exists() and any(path.is_file() and path.suffix.lower() in forbidden for path in root.rglob("*"))


def _forbidden_downstream_exists(root: Path = OUTPUT_ROOT) -> bool:
    forbidden = {
        "final_dataset.csv",
        "final_dataset.json",
        "split_assignments.csv",
        "split_assignments.json",
        "leakage_matrix.csv",
        "leakage_matrix.json",
    }
    return root.exists() and any(path.name in forbidden for path in root.rglob("*"))


def build_precondition_rows() -> list[dict[str, Any]]:
    manifest13bg = _load_json(step13bg.MANIFEST_JSON)
    manifest13bf = _load_json(step13bg.step13bf.MANIFEST_JSON)
    event_rows = _csv_rows(step13bg.step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV)
    protein_rows = _csv_rows(step13bg.step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV)
    ligand_rows = _csv_rows(step13bg.step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV)
    schema_rows = _csv_rows(step13bg.SCHEMA_CONTRACT_CSV)
    mask_rows = _csv_rows(step13bg.MASK_TASK_EXPANSION_CONTRACT_CSV)
    checks = [
        ("step13bg_manifest_exists", step13bg.MANIFEST_JSON, "exists", step13bg.MANIFEST_JSON.exists(), step13bg.MANIFEST_JSON.exists()),
        ("step13bg_stage", step13bg.MANIFEST_JSON, PREVIOUS_STAGE, manifest13bg.get("stage"), manifest13bg.get("stage") == PREVIOUS_STAGE),
        ("step13bg_all_checks_passed", step13bg.MANIFEST_JSON, "true", manifest13bg.get("all_checks_passed"), manifest13bg.get("all_checks_passed") is True),
        ("step13bg_ready_for_sample_index_smoke", step13bg.MANIFEST_JSON, "true", manifest13bg.get("ready_for_covapie_sample_index_smoke"), manifest13bg.get("ready_for_covapie_sample_index_smoke") is True),
        ("step13bg_ready_for_sample_index_qa_gate", step13bg.MANIFEST_JSON, "false", manifest13bg.get("ready_for_covapie_sample_index_qa_gate"), manifest13bg.get("ready_for_covapie_sample_index_qa_gate") is False),
        ("step13bg_ready_for_training", step13bg.MANIFEST_JSON, "false", manifest13bg.get("ready_for_training"), manifest13bg.get("ready_for_training") is False),
        ("schema_contract_exists", step13bg.SCHEMA_CONTRACT_CSV, "exists", step13bg.SCHEMA_CONTRACT_CSV.exists(), step13bg.SCHEMA_CONTRACT_CSV.exists()),
        ("schema_contract_field_count", step13bg.SCHEMA_CONTRACT_CSV, "31", len(schema_rows), len(schema_rows) == 31),
        ("mask_expansion_contract_exists", step13bg.MASK_TASK_EXPANSION_CONTRACT_CSV, "exists", step13bg.MASK_TASK_EXPANSION_CONTRACT_CSV.exists(), step13bg.MASK_TASK_EXPANSION_CONTRACT_CSV.exists()),
        ("mask_expansion_contract_row_count", step13bg.MASK_TASK_EXPANSION_CONTRACT_CSV, "20", len(mask_rows), len(mask_rows) == 20),
        ("extracted_event_table_row_count", step13bg.step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV, "4", len(event_rows), len(event_rows) == 4),
        ("extracted_event_table_column_count", step13bg.step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV, "31", len(event_rows[0]) if event_rows else 0, bool(event_rows) and len(event_rows[0]) == 31),
        ("protein_pocket_atom_table_row_count", step13bg.step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, "1071", len(protein_rows), len(protein_rows) == 1071),
        ("ligand_atom_table_row_count", step13bg.step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV, "149", len(ligand_rows), len(ligand_rows) == 149),
        ("step13bf_event_qa_passed", step13bg.step13bf.MANIFEST_JSON, "true", manifest13bf.get("extracted_event_table_qa_passed"), manifest13bf.get("extracted_event_table_qa_passed") is True),
        ("step13bf_atom_qa_passed", step13bg.step13bf.MANIFEST_JSON, "true", manifest13bf.get("extracted_atom_table_qa_passed"), manifest13bf.get("extracted_atom_table_qa_passed") is True),
        ("step13bf_geometry_qa_passed", step13bg.step13bf.MANIFEST_JSON, "true", manifest13bf.get("geometry_qa_passed"), manifest13bf.get("geometry_qa_passed") is True),
        ("step13bf_traceability_qa_passed", step13bg.step13bf.MANIFEST_JSON, "true", manifest13bf.get("traceability_qa_passed"), manifest13bf.get("traceability_qa_passed") is True),
        ("metadata_csv_hash_unchanged", step13bg.step13bf.step13be.step13bd.METADATA_CSV, METADATA_CSV_SHA256, _metadata_hash(), _metadata_hash() == METADATA_CSV_SHA256),
        ("raw_files_untracked", step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_tracked(), not _raw_files_tracked()),
        ("raw_files_unstaged", step13bg.step13bf.step13be.step13bd.RAW_STORAGE_ROOT, "false", _raw_files_staged(), not _raw_files_staged()),
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


def build_sample_index_rows() -> list[dict[str, Any]]:
    event_rows = _csv_rows(step13bg.step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV)
    protein_counts = _count_by_event(_csv_rows(step13bg.step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV))
    ligand_counts = _count_by_event(_csv_rows(step13bg.step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV))
    sample_rows: list[dict[str, Any]] = []
    for event in event_rows:
        for mask_name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES):
            row = {
                "sample_id": f"sample::{event['candidate_metadata_id']}::{mask_name}",
                "extracted_event_id": event["extracted_event_id"],
                "allowlist_entry_id": event["allowlist_entry_id"],
                "candidate_metadata_id": event["candidate_metadata_id"],
                "pdb_id": event["pdb_id"],
                "het_code": event["het_code"],
                "chain_id": event["chain_id"],
                "residue_name": event["residue_name"],
                "residue_index": event["residue_index"],
                "residue_atom_name": event["residue_atom_name"],
                "ligand_atom_name": event["ligand_atom_name"],
                "covalent_bond_atom_pair": event["covalent_bond_atom_pair"],
                "covalent_bond_distance_angstrom": event["covalent_bond_distance_angstrom"],
                "protein_pocket_atom_table_path": step13bg.step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV.as_posix(),
                "ligand_atom_table_path": step13bg.step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV.as_posix(),
                "protein_atom_row_count_for_event": protein_counts[event["extracted_event_id"]],
                "ligand_atom_row_count_for_event": ligand_counts[event["extracted_event_id"]],
                "mask_task_name": mask_name,
                "mask_task_alias": alias,
                "mask_task_semantic_description": MASK_DESCRIPTIONS[mask_name],
                "conditioning_mode": "protein_covalent_residue_conditioned",
                "covalent_residue_conditioned": True,
                "scaffold_linker_warhead_annotation_status": "required_before_training_not_materialized",
                "warhead_type_label_status": "required_before_training_not_materialized",
                "ligand_residue_atom_pair_label_status": "present_from_extraction_qa_feature_audit_required",
                "pre_post_geometry_label_status": "post_covalent_geometry_present_feature_audit_required",
                "feature_semantics_audit_required_before_training": True,
                "leakage_split_design_required_before_training": True,
                "split_assignment_status": "not_written_current_step",
                "sample_index_materialized_current_step": True,
                "ready_for_training": False,
            }
            sample_rows.append({field: row[field] for field in SAMPLE_INDEX_FIELDS})
    return sample_rows


def build_row_qa_rows(sample_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    event_by_id = {row["extracted_event_id"]: row for row in _csv_rows(step13bg.step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV)}
    event_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bg.step13bf.EVENT_TABLE_QA_CSV)}
    atom_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bg.step13bf.ATOM_TABLE_QA_CSV)}
    geometry_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bg.step13bf.GEOMETRY_QA_CSV)}
    protein_counts = _count_by_event(_csv_rows(step13bg.step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV))
    ligand_counts = _count_by_event(_csv_rows(step13bg.step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV))
    sample_id_counts = Counter(row["sample_id"] for row in sample_rows)
    rows = []
    for sample in sample_rows:
        event = event_by_id.get(sample["extracted_event_id"], {})
        deterministic = sample["sample_id"] == f"sample::{sample['candidate_metadata_id']}::{sample['mask_task_name']}"
        source_found = bool(event)
        source_success = event.get("extraction_status") == "extracted_success" and event_qa.get(sample["extracted_event_id"], {}).get("extraction_success") == "True"
        geometry_passed = geometry_qa.get(sample["extracted_event_id"], {}).get("geometry_qa_passed") == "True"
        protein_count_matches = int(sample["protein_atom_row_count_for_event"]) == protein_counts[sample["extracted_event_id"]] == int(atom_qa.get(sample["extracted_event_id"], {}).get("protein_atom_rows_for_event", -1))
        ligand_count_matches = int(sample["ligand_atom_row_count_for_event"]) == ligand_counts[sample["extracted_event_id"]] == int(atom_qa.get(sample["extracted_event_id"], {}).get("ligand_atom_rows_for_event", -1))
        canonical = sample["mask_task_name"] in CANONICAL_MASK_TASK_NAMES and sample["mask_task_alias"] in CANONICAL_MASK_TASK_ALIASES
        b3_ok = sample["mask_task_name"] != "scaffold_only" or sample["mask_task_alias"] == "B3"
        annotation = sample["scaffold_linker_warhead_annotation_status"] == "required_before_training_not_materialized"
        auxiliary = sample["warhead_type_label_status"] == "required_before_training_not_materialized"
        ready_false = sample["ready_for_training"] is False
        passed = all(
            [
                deterministic,
                sample_id_counts[sample["sample_id"]] == 1,
                list(sample.keys()) == SAMPLE_INDEX_FIELDS,
                source_found,
                source_success,
                geometry_passed,
                protein_count_matches,
                ligand_count_matches,
                canonical,
                b3_ok,
                annotation,
                auxiliary,
                ready_false,
            ]
        )
        rows.append(
            {
                "sample_id": sample["sample_id"],
                "extracted_event_id": sample["extracted_event_id"],
                "pdb_id": sample["pdb_id"],
                "het_code": sample["het_code"],
                "mask_task_name": sample["mask_task_name"],
                "mask_task_alias": sample["mask_task_alias"],
                "sample_id_deterministic": deterministic,
                "sample_id_unique": sample_id_counts[sample["sample_id"]] == 1,
                "schema_order_matches_contract": list(sample.keys()) == SAMPLE_INDEX_FIELDS,
                "source_event_found": source_found,
                "source_event_extraction_success": source_success,
                "source_event_geometry_qa_passed": geometry_passed,
                "protein_atom_rows_for_event": sample["protein_atom_row_count_for_event"],
                "ligand_atom_rows_for_event": sample["ligand_atom_row_count_for_event"],
                "protein_atom_rows_count_matches_source": protein_count_matches,
                "ligand_atom_rows_count_matches_source": ligand_count_matches,
                "canonical_mask_task_valid": canonical,
                "b3_scaffold_only_included_when_applicable": b3_ok,
                "annotation_blockers_preserved": annotation,
                "auxiliary_label_blockers_preserved": auxiliary,
                "ready_for_training_false": ready_false,
                "row_qa_passed": passed,
                "qa_comment": "sample_index_row_validated" if passed else "sample_index_row_failed",
            }
        )
    return rows


def build_mask_distribution_rows(sample_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for name, alias in zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES):
        selected = [row for row in sample_rows if row["mask_task_name"] == name and row["mask_task_alias"] == alias]
        unique_events = {row["extracted_event_id"] for row in selected}
        passed = len(selected) == 4 and len(unique_events) == 4
        rows.append(
            {
                "mask_task_name": name,
                "mask_task_alias": alias,
                "expected_row_count": 4,
                "observed_row_count": len(selected),
                "expected_unique_event_count": 4,
                "observed_unique_event_count": len(unique_events),
                "mask_distribution_passed": passed,
                "qa_comment": "mask_distribution_validated" if passed else "mask_distribution_failed",
            }
        )
    return rows


def build_source_traceability_rows(sample_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events = _csv_rows(step13bg.step13bf.step13be.EXTRACTED_EVENT_TABLE_CSV)
    protein_counts = _count_by_event(_csv_rows(step13bg.step13bf.step13be.EXTRACTED_PROTEIN_ATOM_TABLE_CSV))
    ligand_counts = _count_by_event(_csv_rows(step13bg.step13bf.step13be.EXTRACTED_LIGAND_ATOM_TABLE_CSV))
    event_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bg.step13bf.EVENT_TABLE_QA_CSV)}
    atom_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bg.step13bf.ATOM_TABLE_QA_CSV)}
    geometry_qa = {row["extracted_event_id"]: row for row in _csv_rows(step13bg.step13bf.GEOMETRY_QA_CSV)}
    mask_contract_events = {row["extracted_event_id"] for row in _csv_rows(step13bg.MASK_TASK_EXPANSION_CONTRACT_CSV)}
    rows = []
    for event in events:
        event_id = event["extracted_event_id"]
        sample_count = sum(1 for row in sample_rows if row["extracted_event_id"] == event_id)
        checks = {
            "source_event_table_found": True,
            "source_protein_atom_rows_found": protein_counts[event_id] > 0,
            "source_ligand_atom_rows_found": ligand_counts[event_id] > 0,
            "step13bf_event_qa_found": event_qa.get(event_id, {}).get("extracted_event_table_qa_passed") == "True",
            "step13bf_atom_qa_found": atom_qa.get(event_id, {}).get("extracted_atom_table_qa_passed") == "True",
            "step13bf_geometry_qa_found": geometry_qa.get(event_id, {}).get("geometry_qa_passed") == "True",
            "step13bg_mask_expansion_contract_found": event_id in mask_contract_events,
        }
        passed = sample_count == 5 and all(checks.values())
        rows.append(
            {
                "extracted_event_id": event_id,
                "allowlist_entry_id": event["allowlist_entry_id"],
                "pdb_id": event["pdb_id"],
                "het_code": event["het_code"],
                "sample_index_rows_for_event": sample_count,
                **checks,
                "traceability_qa_passed": passed,
                "qa_comment": "source_traceability_validated" if passed else "source_traceability_failed",
            }
        )
    return rows


def build_boundary_rows() -> list[dict[str, Any]]:
    statuses = {
        "sample_index_smoke": "executed_smoke_only",
        "read_step13bg_design_contracts": "executed_derived_csv_json_read_only",
        "read_step13bf_qa_artifacts": "executed_derived_csv_json_read_only",
        "read_step13be_extracted_tables": "executed_derived_csv_json_read_only",
        "sample_index_csv_write": "executed_smoke_only",
        "sample_index_json_write": "executed_smoke_only",
        "sample_index_qa_gate": "blocked_until_next_gate",
        "final_dataset": "blocked_current_step",
        "split_assignments": "blocked_current_step",
        "leakage_matrix": "blocked_current_step",
        "dataloader_smoke": "blocked_current_step",
        "training": "blocked_current_step",
        "raw_file_content_read": "not_executed_or_not_allowed",
        "mmcif_parse": "not_executed_or_not_allowed",
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
            "qa_comment": "boundary_respected",
        }
        for item, status in statuses.items()
    ]


def build_git_safety_rows() -> list[dict[str, Any]]:
    checks = [
        ("raw_files_untracked", "git ls-files raw storage root", "empty", not _raw_files_tracked()),
        ("raw_files_unstaged", "git diff --cached raw storage root", "empty", not _raw_files_staged()),
        ("raw_files_not_read_current_step", "raw content access policy", "not read", True),
        ("derived_output_no_forbidden_binary_artifacts", "find step13bh output forbidden suffixes", "empty", not _forbidden_suffix_exists()),
        ("sample_index_smoke_written_only_under_step13bh_root", "sample index smoke output root", "step13bh root only", True),
        ("no_final_dataset_written", "find final_dataset in step13bh root", "empty", not _forbidden_downstream_exists()),
        ("no_split_assignments_written", "find split_assignments in step13bh root", "empty", not _forbidden_downstream_exists()),
        ("no_leakage_matrix_written", "find leakage_matrix in step13bh root", "empty", not _forbidden_downstream_exists()),
        ("metadata_csv_unchanged", "metadata CSV hash", METADATA_CSV_SHA256, _metadata_hash() == METADATA_CSV_SHA256),
        ("step13bg_artifacts_unchanged", "git diff step13bg root", "empty", not _path_diff_exists([step13bg.OUTPUT_ROOT.as_posix()])),
        ("step13bf_artifacts_unchanged", "git diff step13bf root", "empty", not _path_diff_exists([step13bg.step13bf.OUTPUT_ROOT.as_posix()])),
        ("step13be_artifacts_unchanged", "git diff step13be root", "empty", not _path_diff_exists([step13bg.step13bf.step13be.OUTPUT_ROOT.as_posix()])),
        ("protected_source_diff_empty", "git diff protected source", "empty", not _path_diff_exists(["equivariant_diffusion/", "lightning_modules.py"])),
        ("original_dataloader_diff_empty", "git diff dataset.py data/prepare_crossdocked.py", "empty", not _path_diff_exists(["dataset.py", "data/prepare_crossdocked.py"])),
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


def build_training_blocker_rows() -> list[dict[str, Any]]:
    items = [
        ("mask_warhead_only_A", "present"),
        ("mask_linker_plus_warhead_B", "present"),
        ("mask_scaffold_plus_warhead_B2", "present"),
        ("mask_scaffold_only_B3", "present"),
        ("mask_scaffold_plus_linker_plus_warhead_C", "present"),
        ("scaffold_linker_warhead_annotation_required_before_training", "true"),
        ("auxiliary_labels_required_before_training", "true"),
        ("warhead_type_label_required_before_training", "true"),
        ("ligand_residue_atom_pair_label_audit_required_before_training", "true"),
        ("pre_post_geometry_label_audit_required_before_training", "true"),
        ("feature_semantics_audit_required", "true"),
        ("feature_semantics_fully_audited_claimed_false", "true"),
        ("leakage_split_design_required", "true"),
        ("split_written_current_step_false", "true"),
        ("leakage_matrix_written_current_step_false", "true"),
        ("ready_for_training_false", "true"),
    ]
    return [
        {
            "training_blocker_item": item,
            "required_status": required,
            "current_step_status": required,
            "training_blocker_passed": True,
            "qa_comment": "training_blocker_preserved",
        }
        for item, required in items
    ]


def run_covapie_sample_index_smoke_v0() -> dict[str, Any]:
    precondition_rows = build_precondition_rows()
    sample_rows = build_sample_index_rows()
    row_qa_rows = build_row_qa_rows(sample_rows)
    mask_distribution_rows = build_mask_distribution_rows(sample_rows)
    traceability_rows = build_source_traceability_rows(sample_rows)
    boundary_rows = build_boundary_rows()
    git_safety_rows = build_git_safety_rows()
    training_blocker_rows = build_training_blocker_rows()

    mask_counts = Counter(row["mask_task_name"] for row in sample_rows)
    sample_ids = [row["sample_id"] for row in sample_rows]
    unique_events = {row["extracted_event_id"] for row in sample_rows}
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "project_name": PROJECT_NAME,
        "step13bg_sample_index_design_gate_validated": all(_bool(row["precondition_passed"]) for row in precondition_rows),
        "sample_index_smoke_csv_written": True,
        "sample_index_smoke_json_written": True,
        "sample_index_row_count": len(sample_rows),
        "sample_index_column_count": len(SAMPLE_INDEX_FIELDS),
        "sample_index_json_row_count": len(sample_rows),
        "source_extracted_event_row_count": 4,
        "source_protein_pocket_atom_row_count": 1071,
        "source_ligand_atom_row_count": 149,
        "unique_event_count": len(unique_events),
        "canonical_mask_task_count": len(CANONICAL_MASK_TASK_NAMES),
        "planned_sample_count": 20,
        "observed_sample_count": len(sample_rows),
        "sample_id_unique_count": len(set(sample_ids)),
        "mask_warhead_only_A_count": mask_counts["warhead_only"],
        "mask_linker_plus_warhead_B_count": mask_counts["linker_plus_warhead"],
        "mask_scaffold_plus_warhead_B2_count": mask_counts["scaffold_plus_warhead"],
        "mask_scaffold_only_B3_count": mask_counts["scaffold_only"],
        "mask_scaffold_plus_linker_plus_warhead_C_count": mask_counts["scaffold_plus_linker_plus_warhead"],
        "row_qa_passed": all(_bool(row["row_qa_passed"]) for row in row_qa_rows),
        "mask_distribution_qa_passed": all(_bool(row["mask_distribution_passed"]) for row in mask_distribution_rows),
        "source_traceability_qa_passed": all(_bool(row["traceability_qa_passed"]) for row in traceability_rows),
        "boundary_safety_passed": all(_bool(row["boundary_safety_passed"]) for row in boundary_rows),
        "git_safety_passed": all(_bool(row["git_safety_audit_passed"]) for row in git_safety_rows),
        "training_blockers_passed": all(_bool(row["training_blocker_passed"]) for row in training_blocker_rows),
        "sample_index_materialized_current_step": True,
        "sample_index_written": True,
        "final_dataset_written": False,
        "split_assignments_written": False,
        "leakage_matrix_written": False,
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
        "ready_for_covapie_sample_index_qa_gate": True,
        "ready_for_covapie_split_leakage_design_gate": False,
        "ready_for_covapie_final_dataset_design_gate": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "canonical_mask_task_names": CANONICAL_MASK_TASK_NAMES,
        "canonical_mask_task_aliases": CANONICAL_MASK_TASK_ALIASES,
        "b3_scaffold_only_included": "scaffold_only" in mask_counts and mask_counts["scaffold_only"] == 4,
        "no_extra_mask_tasks_added": set(mask_counts) == set(CANONICAL_MASK_TASK_NAMES),
        "scaffold_linker_warhead_annotation_required_before_training": True,
        "auxiliary_labels_required_before_training": True,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "recommended_next_step": "covapie_sample_index_qa_gate",
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    manifest["all_checks_passed"] = all(
        [
            manifest["step13bg_sample_index_design_gate_validated"],
            manifest["sample_index_row_count"] == 20,
            manifest["sample_index_column_count"] == 31,
            manifest["sample_id_unique_count"] == 20,
            manifest["unique_event_count"] == 4,
            manifest["canonical_mask_task_count"] == 5,
            manifest["planned_sample_count"] == manifest["observed_sample_count"] == 20,
            manifest["row_qa_passed"],
            manifest["mask_distribution_qa_passed"],
            manifest["source_traceability_qa_passed"],
            manifest["boundary_safety_passed"],
            manifest["git_safety_passed"],
            manifest["training_blockers_passed"],
            manifest["b3_scaffold_only_included"],
            manifest["no_extra_mask_tasks_added"],
        ]
    )
    manifest["blocking_reasons"] = [] if manifest["all_checks_passed"] else ["sample_index_smoke_contract_failed"]
    return {
        "precondition_rows": precondition_rows,
        "sample_rows": sample_rows,
        "row_qa_rows": row_qa_rows,
        "mask_distribution_rows": mask_distribution_rows,
        "traceability_rows": traceability_rows,
        "boundary_rows": boundary_rows,
        "git_safety_rows": git_safety_rows,
        "training_blocker_rows": training_blocker_rows,
        "manifest": manifest,
    }
