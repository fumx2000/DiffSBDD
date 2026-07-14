"""Read-only QA gate for the canonical Step 14AR final-dataset outputs.

This module reads only the twelve committed Step 14AR outputs and the one
Step 14AQ manifest named below.  It deliberately does not follow paths listed
inside the Step 14AR artifact inventory.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


STAGE = "covapie_final_dataset_qa_gate_v1"
STEP_LABEL = "Step14AS-B"
PROJECT_NAME = "CovaPIE"
PREVIOUS_STAGE = "covapie_final_dataset_materialization_smoke_v0"
MANIFEST_SCHEMA_VERSION = "covapie_final_dataset_qa_gate_v1_manifest_v1"
SOURCE_STEP14AR_MANIFEST_SHA256 = "6f25c8976b295749f3af6407c3bb8ce17cfbda9f18cb967df5fe9b47b480c433"
SOURCE_STEP14AQ_MANIFEST_SHA256 = "697f4ad7d4d5afb7598862ad82b93db7f8e6c1aa05ea61a9162cae45a1d59bba"
SOURCE_STEP14AQ_COMMIT = "b6f09468447e611a586751bf329d5b07bb308317"
NEXT_STAGE = "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"

REPO_ROOT = Path(__file__).resolve().parents[2]
AR_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0")
AQ_MANIFEST = Path(
    "data/derived/covalent_small/covapie_unified_leakage_split_materialization_smoke_v0/"
    "covapie_unified_leakage_split_materialization_smoke_manifest.json"
)
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_qa_gate_v1")
OUTPUT_ROOT = DEFAULT_OUTPUT_ROOT

FINAL_INDEX_FIELDS = (
    "sample_index_row_id", "sample_preparation_input_id", "sample_execution_id", "sample_qa_id",
    "pdb_id", "expected_het_id", "sample_artifact_root", "protein_atom_table_path",
    "ligand_atom_table_path", "pocket_atom_table_path", "covalent_event_table_path",
    "ligand_residue_atom_pair_table_path", "sample_preparation_audit_path", "protein_atom_count",
    "ligand_atom_count", "pocket_atom_count", "covalent_event_count",
    "ligand_residue_atom_pair_count", "covalent_residue_name", "covalent_residue_chain_id",
    "covalent_residue_index", "covalent_residue_atom_name", "ligand_comp_id",
    "ligand_covalent_atom_name", "covalent_bond_atom_pair", "conn_id", "conn_type_id",
    "bond_distance_angstrom", "sample_index_status", "eligible_for_final_dataset_design",
    "ready_for_training_current_step", "feature_semantics_audit_required_before_training",
    "leakage_split_design_required_before_training",
)
CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
INPUT_FILENAMES = (
    "covapie_final_dataset_precondition_audit.csv",
    "final_dataset_index.csv",
    "final_dataset_index.json",
    "covapie_final_dataset_membership.csv",
    "covapie_final_dataset_artifact_inventory.csv",
    "covapie_final_dataset_schema_validation_audit.csv",
    "covapie_final_dataset_source_preservation_audit.csv",
    "covapie_final_dataset_split_summary.csv",
    "covapie_final_dataset_integrity_audit.csv",
    "covapie_final_dataset_issue_inventory.csv",
    "covapie_final_dataset_safety_audit.csv",
    "covapie_final_dataset_materialization_smoke_manifest.json",
)
CSV_OUTPUTS = (
    "covapie_final_dataset_qa_v1_precondition_audit.csv",
    "covapie_final_dataset_qa_v1_artifact_inventory_audit.csv",
    "covapie_final_dataset_qa_v1_schema_lineage_audit.csv",
    "covapie_final_dataset_qa_v1_split_leakage_audit.csv",
    "covapie_final_dataset_qa_v1_mask_contract_audit.csv",
    "covapie_final_dataset_qa_v1_safety_training_boundary_audit.csv",
    "covapie_final_dataset_qa_v1_issue_inventory.csv",
)
MANIFEST_FILENAME = "covapie_final_dataset_qa_v1_manifest.json"

PRECONDITION_COLUMNS = (
    "precondition_item", "source_path_or_check", "expected_status", "observed_status",
    "precondition_passed", "blocking_reasons",
)
ARTIFACT_COLUMNS = (
    "artifact_name", "artifact_path", "expected_sha256", "observed_sha256", "tracked_by_git",
    "path_exists", "is_regular_file", "manifest_inventory_match", "artifact_inventory_qa_passed",
    "blocking_reasons",
)
LINEAGE_COLUMNS = (
    "qa_record_type", "qa_record_id", "field_name", "expected_position", "observed_position",
    "final_dataset_row_id", "csv_json_match", "membership_match", "source_preservation_match",
    "schema_lineage_qa_passed", "blocking_reasons",
)
SPLIT_COLUMNS = (
    "split_name", "source_summary_sample_count", "recomputed_membership_sample_count",
    "source_step14aq_sample_count", "source_step14aq_sample_count_status", "expected_sample_count",
    "sample_count_match", "source_summary_group_count", "recomputed_membership_group_count",
    "source_step14aq_group_count", "source_step14aq_group_count_status", "expected_group_count",
    "group_count_match", "source_summary_artifact_reference_count",
    "recomputed_inventory_artifact_reference_count", "source_step14aq_artifact_reference_count_status",
    "artifact_reference_count_evidence_source", "expected_artifact_reference_count",
    "artifact_reference_count_match", "group_exclusive", "artifact_inventory_join_complete",
    "leakage_preserved", "split_leakage_qa_passed", "blocking_reasons",
)
MASK_COLUMNS = (
    "mask_order", "mask_task_name", "mask_task_alias", "present_in_manifest", "mask_semantics_source",
    "final_index_mask_field_present", "final_index_mask_field_required", "final_index_sample_set_complete",
    "long_name_source_of_truth", "alias_display_only", "no_extra_masks", "mask_contract_qa_passed",
    "blocking_reasons",
)
SAFETY_COLUMNS = (
    "safety_item", "required_status", "observed_status", "safety_training_boundary_qa_passed",
    "blocking_reasons",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "severity", "status", "issue_count", "blocking_reasons",
)

INTEGER_FIELDS = {
    "protein_atom_count", "ligand_atom_count", "pocket_atom_count", "covalent_event_count",
    "ligand_residue_atom_pair_count",
}
FLOAT_FIELDS = {"bond_distance_angstrom"}
BOOLEAN_FIELDS = {
    "eligible_for_final_dataset_design", "ready_for_training_current_step",
    "feature_semantics_audit_required_before_training", "leakage_split_design_required_before_training",
}


def _repo_path(relative_path: Path) -> Path:
    return REPO_ROOT / relative_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(relative_path: Path) -> list[dict[str, str]]:
    with _repo_path(relative_path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(relative_path: Path) -> Any:
    return json.loads(_repo_path(relative_path).read_text(encoding="utf-8"))


def _tracked_by_git(relative_path: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path.as_posix()],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _normalize_csv_value(field: str, value: str) -> Any:
    if value == "":
        return None
    if field in BOOLEAN_FIELDS:
        if value not in {"True", "False"}:
            raise ValueError(f"invalid boolean for {field}: {value!r}")
        return value == "True"
    if field in INTEGER_FIELDS:
        if not re.fullmatch(r"-?[0-9]+", value):
            raise ValueError(f"invalid integer for {field}: {value!r}")
        return int(value)
    if field in FLOAT_FIELDS:
        return float(value)
    return value


def _normalize_json_value(field: str, value: Any) -> Any:
    if value is None:
        return None
    if field in BOOLEAN_FIELDS:
        if type(value) is not bool:
            raise ValueError(f"invalid JSON boolean for {field}: {value!r}")
        return value
    if field in INTEGER_FIELDS:
        if type(value) is not int:
            raise ValueError(f"invalid JSON integer for {field}: {value!r}")
        return value
    if field in FLOAT_FIELDS:
        if type(value) not in {int, float}:
            raise ValueError(f"invalid JSON float for {field}: {value!r}")
        return float(value)
    if type(value) is not str:
        raise ValueError(f"invalid JSON string for {field}: {value!r}")
    return value


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _pass_row(columns: tuple[str, ...], **values: Any) -> dict[str, Any]:
    return {column: values.get(column, "") for column in columns}


def _source_input_paths() -> tuple[Path, ...]:
    return tuple(AR_ROOT / filename for filename in INPUT_FILENAMES)


def _all_read_paths() -> tuple[Path, ...]:
    return _source_input_paths() + (AQ_MANIFEST,)


def _load_source() -> dict[str, Any]:
    ar_manifest_path = AR_ROOT / "covapie_final_dataset_materialization_smoke_manifest.json"
    return {
        "precondition": _read_csv(AR_ROOT / "covapie_final_dataset_precondition_audit.csv"),
        "index_csv": _read_csv(AR_ROOT / "final_dataset_index.csv"),
        "index_json": _read_json(AR_ROOT / "final_dataset_index.json"),
        "membership": _read_csv(AR_ROOT / "covapie_final_dataset_membership.csv"),
        "artifact_inventory": _read_csv(AR_ROOT / "covapie_final_dataset_artifact_inventory.csv"),
        "schema": _read_csv(AR_ROOT / "covapie_final_dataset_schema_validation_audit.csv"),
        "source_preservation": _read_csv(AR_ROOT / "covapie_final_dataset_source_preservation_audit.csv"),
        "split": _read_csv(AR_ROOT / "covapie_final_dataset_split_summary.csv"),
        "integrity": _read_csv(AR_ROOT / "covapie_final_dataset_integrity_audit.csv"),
        "issues": _read_csv(AR_ROOT / "covapie_final_dataset_issue_inventory.csv"),
        "safety": _read_csv(AR_ROOT / "covapie_final_dataset_safety_audit.csv"),
        "ar_manifest": _read_json(ar_manifest_path),
        "aq_manifest": _read_json(AQ_MANIFEST),
    }


def _expected_hashes(ar_manifest: dict[str, Any]) -> dict[str, str]:
    inventory = {
        entry["relative_path"]: entry["sha256"]
        for entry in ar_manifest.get("non_manifest_outputs", [])
    }
    expected = {
        str(AR_ROOT / filename): inventory.get(str(AR_ROOT / filename), "")
        for filename in INPUT_FILENAMES[:-1]
    }
    expected[str(AR_ROOT / INPUT_FILENAMES[-1])] = SOURCE_STEP14AR_MANIFEST_SHA256
    return expected


def _build_preconditions(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative_path in _all_read_paths():
        absolute = _repo_path(relative_path)
        observed = absolute.exists() and absolute.is_file() and _tracked_by_git(relative_path)
        rows.append(_pass_row(
            PRECONDITION_COLUMNS,
            precondition_item=f"tracked_regular_input:{relative_path.name}",
            source_path_or_check=relative_path.as_posix(), expected_status="true",
            observed_status=_bool_text(observed), precondition_passed=_bool_text(observed),
            blocking_reasons="" if observed else f"missing_or_untracked_input:{relative_path.as_posix()}",
        ))
    checks = (
        ("step14ar_manifest_sha256", _sha256(_repo_path(AR_ROOT / INPUT_FILENAMES[-1])) == SOURCE_STEP14AR_MANIFEST_SHA256),
        ("step14aq_manifest_sha256", _sha256(_repo_path(AQ_MANIFEST)) == SOURCE_STEP14AQ_MANIFEST_SHA256),
        ("step14ar_stage", source["ar_manifest"].get("stage") == PREVIOUS_STAGE),
        ("step14aq_stage", source["aq_manifest"].get("stage") == "covapie_unified_leakage_split_materialization_smoke_v0"),
        ("step14ar_source_step14aq_provenance", source["ar_manifest"].get("source_step14aq_commit") == SOURCE_STEP14AQ_COMMIT),
        ("source_root_read_only_boundary", True),
        ("raw_model_runtime_boundary_disabled", True),
        ("step14ar_manifest_field_count", len(source["ar_manifest"]) == 54),
        ("step14ar_output_file_count", len(source["ar_manifest"].get("non_manifest_outputs", [])) == 11),
        ("step14ar_precondition_audit", len(source["precondition"]) == 23 and _all_source_rows_pass(source["precondition"], "precondition_passed")),
        ("step14ar_schema_audit", len(source["schema"]) == 33 and _all_source_rows_pass(source["schema"], "schema_validation_passed")),
        ("step14ar_artifact_inventory_audit", len(source["artifact_inventory"]) == 66 and _all_source_rows_pass(source["artifact_inventory"], "artifact_inventory_passed")),
        ("step14ar_membership_audit", len(source["membership"]) == 11 and _all_source_rows_pass(source["membership"], "final_dataset_membership_passed")),
        ("step14ar_source_preservation_audit", len(source["source_preservation"]) == 11 and _all_source_rows_pass(source["source_preservation"], "source_preservation_passed")),
        ("step14ar_split_summary_audit", len(source["split"]) == 4 and _all_source_rows_pass(source["split"], "split_summary_passed")),
        ("step14ar_integrity_audit", len(source["integrity"]) == 24 and _all_source_rows_pass(source["integrity"], "integrity_check_passed")),
        ("step14ar_safety_audit", len(source["safety"]) == 55 and _all_source_rows_pass(source["safety"], "safety_passed")),
        ("step14ar_issue_inventory", len(source["issues"]) == 1 and source["issues"][0].get("issue_id") == "NO_COVAPIE_FINAL_DATASET_MATERIALIZATION_ISSUES"),
    )
    for item, passed in checks:
        rows.append(_pass_row(
            PRECONDITION_COLUMNS, precondition_item=item, source_path_or_check=item,
            expected_status="true", observed_status=_bool_text(passed),
            precondition_passed=_bool_text(passed), blocking_reasons="" if passed else item,
        ))
    return rows


def _build_artifact_inventory(source: dict[str, Any]) -> list[dict[str, Any]]:
    expected_hashes = _expected_hashes(source["ar_manifest"])
    expected_non_manifest = {str(AR_ROOT / filename) for filename in INPUT_FILENAMES[:-1]}
    manifest_non_manifest = {entry.get("relative_path") for entry in source["ar_manifest"].get("non_manifest_outputs", [])}
    exact_manifest_inventory = manifest_non_manifest == expected_non_manifest
    rows: list[dict[str, Any]] = []
    for relative_path in tuple(AR_ROOT / filename for filename in INPUT_FILENAMES):
        absolute = _repo_path(relative_path)
        exists = absolute.exists()
        regular = absolute.is_file()
        tracked = _tracked_by_git(relative_path)
        observed_hash = _sha256(absolute) if exists and regular else ""
        expected_hash = expected_hashes[str(relative_path)]
        inventory_match = observed_hash == expected_hash and exact_manifest_inventory
        passed = exists and regular and tracked and inventory_match
        rows.append(_pass_row(
            ARTIFACT_COLUMNS, artifact_name=relative_path.name, artifact_path=relative_path.as_posix(),
            expected_sha256=expected_hash, observed_sha256=observed_hash, tracked_by_git=_bool_text(tracked),
            path_exists=_bool_text(exists), is_regular_file=_bool_text(regular),
            manifest_inventory_match=_bool_text(inventory_match), artifact_inventory_qa_passed=_bool_text(passed),
            blocking_reasons="" if passed else f"artifact_inventory_mismatch:{relative_path.name}",
        ))
    return rows


def _build_schema_lineage(source: dict[str, Any]) -> list[dict[str, Any]]:
    index_csv = source["index_csv"]
    index_json = source["index_json"]
    membership = source["membership"]
    preservation = source["source_preservation"]
    if len(index_csv) != 11 or len(index_json) != 11:
        raise ValueError("final dataset index row count must be 11")
    csv_header = tuple(index_csv[0].keys()) if index_csv else ()
    source_schema_fields = tuple(row.get("sample_index_field") for row in source["schema"])
    json_schema_valid = all(tuple(row.keys()) == FINAL_INDEX_FIELDS for row in index_json)
    schema_rows: list[dict[str, Any]] = []
    for position, field in enumerate(FINAL_INDEX_FIELDS, start=1):
        observed_position = csv_header.index(field) + 1 if field in csv_header else 0
        passed = (
            source_schema_fields == FINAL_INDEX_FIELDS
            and csv_header == FINAL_INDEX_FIELDS
            and observed_position == position
            and json_schema_valid
        )
        schema_rows.append(_pass_row(
            LINEAGE_COLUMNS, qa_record_type="schema_field", qa_record_id=f"field_{position:02d}",
            field_name=field, expected_position=position, observed_position=observed_position,
            final_dataset_row_id="", csv_json_match=_bool_text(passed), membership_match="true",
            source_preservation_match="true", schema_lineage_qa_passed=_bool_text(passed),
            blocking_reasons="" if passed else f"schema_field_mismatch:{field}",
        ))
    membership_ids = {row["sample_index_row_id"] for row in membership}
    preservation_ids = {row["sample_index_row_id"] for row in preservation}
    seen: set[str] = set()
    for position, (csv_row, json_row) in enumerate(zip(index_csv, index_json), start=1):
        row_id = csv_row["sample_index_row_id"]
        csv_json_match = True
        try:
            if tuple(json_row.keys()) != FINAL_INDEX_FIELDS:
                csv_json_match = False
            for field in FINAL_INDEX_FIELDS:
                if _normalize_csv_value(field, csv_row[field]) != _normalize_json_value(field, json_row.get(field)):
                    csv_json_match = False
        except (KeyError, ValueError):
            csv_json_match = False
        membership_match = row_id in membership_ids
        preservation_match = row_id in preservation_ids
        unique = row_id not in seen
        seen.add(row_id)
        passed = csv_json_match and membership_match and preservation_match and unique
        schema_rows.append(_pass_row(
            LINEAGE_COLUMNS, qa_record_type="lineage_row", qa_record_id=f"row_{position:02d}",
            field_name="", expected_position=position, observed_position=position,
            final_dataset_row_id=row_id, csv_json_match=_bool_text(csv_json_match),
            membership_match=_bool_text(membership_match), source_preservation_match=_bool_text(preservation_match),
            schema_lineage_qa_passed=_bool_text(passed),
            blocking_reasons="" if passed else f"lineage_mismatch:{row_id}",
        ))
    return schema_rows


def _build_split_audit(source: dict[str, Any]) -> list[dict[str, Any]]:
    expected = {"train": (8, 2, 48), "validation": (2, 2, 12), "test": (1, 1, 6), "total": (11, 5, 66)}
    memberships = source["membership"]
    split_names = ("train", "validation", "test", "total")
    summary_by_split = {row.get("split_name"): row for row in source["split"]}
    membership_by_id: dict[str, dict[str, str]] = {}
    membership_id_unique = True
    for row in memberships:
        row_id = row["sample_index_row_id"]
        membership_id_unique = membership_id_unique and row_id not in membership_by_id
        membership_by_id[row_id] = row
    recomputed_sample_counts = {
        name: (len(memberships) if name == "total" else sum(row["assigned_split"] == name for row in memberships))
        for name in split_names
    }
    group_splits: dict[str, set[str]] = {}
    for row in memberships:
        group_splits.setdefault(row["final_leakage_group_id"], set()).add(row["assigned_split"])
    group_exclusive_global = all(len(splits) == 1 for splits in group_splits.values())
    recomputed_group_counts = {
        name: (
            len(group_splits) if name == "total" else len({
                row["final_leakage_group_id"] for row in memberships if row["assigned_split"] == name
            })
        )
        for name in split_names
    }
    inventory_split_counts = {name: 0 for name in split_names}
    inventory_join_complete = membership_id_unique
    for row in source["artifact_inventory"]:
        membership = membership_by_id.get(row.get("sample_index_row_id", ""))
        if membership is None:
            inventory_join_complete = False
            continue
        split_name = membership["assigned_split"]
        if row.get("assigned_split") != split_name or row.get("final_leakage_group_id") != membership["final_leakage_group_id"]:
            inventory_join_complete = False
        inventory_split_counts[split_name] += 1
        inventory_split_counts["total"] += 1
    aq = source["aq_manifest"]
    aq_sample_keys = {"train": "train_sample_count", "validation": "validation_sample_count", "test": "test_sample_count", "total": "unified_sample_count"}
    aq_group_keys = {"train": "train_group_count", "validation": "validation_group_count", "test": "test_group_count", "total": "final_leakage_group_count"}
    aq_sample_available = all(key in aq for key in aq_sample_keys.values())
    aq_group_available = all(key in aq for key in aq_group_keys.values())
    rows: list[dict[str, Any]] = []
    for split_name in split_names:
        source_row = summary_by_split.get(split_name, {})
        wanted = expected[split_name]
        source_sample = int(source_row["sample_count"]) if source_row.get("sample_count", "").isdigit() else -1
        source_group = int(source_row["leakage_group_count"]) if source_row.get("leakage_group_count", "").isdigit() else -1
        source_artifact = int(source_row["artifact_reference_count"]) if source_row.get("artifact_reference_count", "").isdigit() else -1
        aq_sample = aq.get(aq_sample_keys[split_name]) if aq_sample_available else ""
        aq_group = aq.get(aq_group_keys[split_name]) if aq_group_available else ""
        sample_match = aq_sample_available and source_sample == recomputed_sample_counts[split_name] == aq_sample == wanted[0]
        group_match = aq_group_available and source_group == recomputed_group_counts[split_name] == aq_group == wanted[1]
        artifact_match = source_artifact == inventory_split_counts[split_name] == wanted[2]
        group_exclusive = source_row.get("group_integrity_preserved") == "True" and group_exclusive_global
        leakage_preserved = source_row.get("source_rows_preserved") == "True"
        passed = (
            sample_match and group_match and artifact_match and group_exclusive and inventory_join_complete
            and leakage_preserved and source_row.get("split_summary_passed") == "True"
        )
        rows.append(_pass_row(
            SPLIT_COLUMNS, split_name=split_name, source_summary_sample_count=source_sample,
            recomputed_membership_sample_count=recomputed_sample_counts[split_name], source_step14aq_sample_count=aq_sample,
            source_step14aq_sample_count_status="available_and_crosschecked" if aq_sample_available else "missing_in_source_manifest",
            expected_sample_count=wanted[0], sample_count_match=_bool_text(sample_match),
            source_summary_group_count=source_group, recomputed_membership_group_count=recomputed_group_counts[split_name],
            source_step14aq_group_count=aq_group,
            source_step14aq_group_count_status="available_and_crosschecked" if aq_group_available else "missing_in_source_manifest",
            expected_group_count=wanted[1], group_count_match=_bool_text(group_match),
            source_summary_artifact_reference_count=source_artifact,
            recomputed_inventory_artifact_reference_count=inventory_split_counts[split_name],
            source_step14aq_artifact_reference_count_status="not_available_in_source_manifest",
            artifact_reference_count_evidence_source="step14ar_artifact_inventory_joined_to_membership",
            expected_artifact_reference_count=wanted[2], artifact_reference_count_match=_bool_text(artifact_match),
            group_exclusive=_bool_text(group_exclusive), artifact_inventory_join_complete=_bool_text(inventory_join_complete),
            leakage_preserved=_bool_text(leakage_preserved),
            split_leakage_qa_passed=_bool_text(passed), blocking_reasons="" if passed else f"split_mismatch:{split_name}",
        ))
    return rows


def _build_mask_audit(source: dict[str, Any]) -> list[dict[str, Any]]:
    manifest_pairs = tuple(tuple(pair) for pair in source["ar_manifest"].get("canonical_mask_pairs", []))
    index_ids = [row.get("sample_index_row_id") for row in source["index_csv"]]
    membership_ids = {row.get("sample_index_row_id") for row in source["membership"]}
    index_sample_set_complete = len(index_ids) == 11 and len(set(index_ids)) == 11 and set(index_ids) == membership_ids
    final_index_header = tuple(source["index_csv"][0].keys()) if source["index_csv"] else ()
    final_index_mask_field_present = "mask_task_name" in final_index_header or "mask_task_alias" in final_index_header
    rows: list[dict[str, Any]] = []
    for order, (name, alias) in enumerate(CANONICAL_MASK_PAIRS, start=1):
        present_manifest = (name, alias) in manifest_pairs
        no_extra = manifest_pairs == CANONICAL_MASK_PAIRS
        passed = (
            present_manifest and len(manifest_pairs) == 5 and ("scaffold_only", "B3") in manifest_pairs
            and index_sample_set_complete and no_extra and not final_index_mask_field_present
        )
        rows.append(_pass_row(
            MASK_COLUMNS, mask_order=order, mask_task_name=name, mask_task_alias=alias,
            present_in_manifest=_bool_text(present_manifest), mask_semantics_source="step14ar_manifest",
            final_index_mask_field_present=_bool_text(final_index_mask_field_present),
            final_index_mask_field_required="false", final_index_sample_set_complete=_bool_text(index_sample_set_complete),
            long_name_source_of_truth="true", alias_display_only="true", no_extra_masks=_bool_text(no_extra),
            mask_contract_qa_passed=_bool_text(passed), blocking_reasons="" if passed else f"mask_contract:{name}",
        ))
    return rows


def _build_safety_audit(source: dict[str, Any], source_hashes_before: dict[str, str]) -> list[dict[str, Any]]:
    ar_manifest = source["ar_manifest"]
    index_split_boundary = all(
        row["leakage_split_design_required_before_training"] == "True"
        for row in source["index_csv"]
    )
    required: tuple[tuple[str, bool, bool], ...] = (
        ("raw_data_read", False, False), ("network_access_used", False, False),
        ("torch_imported", False, False), ("tensor_created", False, False), ("numpy_imported", False, False),
        ("rdkit_used", False, False), ("biopython_used", False, False), ("gemmi_used", False, False),
        ("dataloader_instantiated", False, False), ("model_forward_called", False, False), ("loss_compute_called", False, False),
        ("backward_called", False, False), ("optimizer_created", False, False),
        ("trainer_fit_called", False, False), ("checkpoint_loaded", False, False),
        ("sample_index_written", False, False), ("final_dataset_written", False, False),
        ("split_assignments_written", False, False), ("leakage_matrix_written", False, False),
        ("protected_source_diff_empty", True, _protected_source_diff_empty()),
        ("feature_semantics_known_for_training", False, ar_manifest.get("feature_semantics_known_for_training") is True),
        ("unknown_atom_feature_policy_finalized_for_training", False, ar_manifest.get("unknown_atom_feature_policy_finalized_for_training") is True),
        ("ready_for_training", False, ar_manifest.get("ready_for_training") is True),
        ("ready_to_train_now", False, ar_manifest.get("ready_to_train_now") is True),
        ("feature_semantics_audit_required_before_training", True, ar_manifest.get("feature_semantics_audit_required_before_training") is True),
        ("leakage_split_design_required_before_training", True, index_split_boundary),
        ("ready_for_bulk_download_now", False, False),
        ("source_inputs_unchanged", True, source_hashes_before == {path.as_posix(): _sha256(_repo_path(path)) for path in _all_read_paths()}),
    )
    rows: list[dict[str, Any]] = []
    for item, expected, observed in required:
        passed = expected == observed
        rows.append(_pass_row(
            SAFETY_COLUMNS, safety_item=item, required_status=_bool_text(expected), observed_status=_bool_text(observed),
            safety_training_boundary_qa_passed=_bool_text(passed), blocking_reasons="" if passed else item,
        ))
    return rows


def _build_issue_rows(all_sections_passed: bool, blockers: list[str]) -> list[dict[str, Any]]:
    if all_sections_passed:
        return [_pass_row(
            ISSUE_COLUMNS, issue_id="NO_COVAPIE_FINAL_DATASET_QA_V1_ISSUES", issue_type="no_issues",
            severity="none", status="passed", issue_count=0, blocking_reasons="",
        )]
    return [_pass_row(
        ISSUE_COLUMNS, issue_id="COVAPIE_FINAL_DATASET_QA_V1_BLOCKED", issue_type="qa_blocking_issues",
        severity="blocking", status="failed", issue_count=len(blockers), blocking_reasons=";".join(blockers),
    )]


def _section_passed(rows: list[dict[str, Any]], field: str) -> bool:
    return bool(rows) and all(row[field] == "true" for row in rows)


def _all_source_rows_pass(rows: list[dict[str, str]], field: str) -> bool:
    return bool(rows) and all(row.get(field) == "True" and not row.get("blocking_reasons") for row in rows)


def _protected_source_diff_empty() -> bool:
    protected_paths = ("equivariant_diffusion/", "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py")
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *protected_paths], cwd=REPO_ROOT, check=False
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *protected_paths], cwd=REPO_ROOT, check=False
    )
    return unstaged.returncode == 0 and staged.returncode == 0


def _summarize_split_evidence(split_rows: list[dict[str, Any]]) -> dict[str, Any]:
    split_rows_by_name = {row["split_name"]: row for row in split_rows}
    split_order = ("train", "validation", "test", "total")
    return {
        "sample_counts": {
            name: int(split_rows_by_name[name]["recomputed_membership_sample_count"]) for name in split_order
        },
        "group_counts": {
            name: int(split_rows_by_name[name]["recomputed_membership_group_count"]) for name in split_order
        },
        "artifact_counts": {
            name: int(split_rows_by_name[name]["recomputed_inventory_artifact_reference_count"]) for name in split_order
        },
        "aq_sample_counts_available": all(
            split_rows_by_name[name]["source_step14aq_sample_count_status"] == "available_and_crosschecked"
            for name in split_order
        ),
        "aq_sample_counts_match": all(split_rows_by_name[name]["sample_count_match"] == "true" for name in split_order),
        "aq_group_counts_available": all(
            split_rows_by_name[name]["source_step14aq_group_count_status"] == "available_and_crosschecked"
            for name in split_order
        ),
        "aq_group_counts_match": all(split_rows_by_name[name]["group_count_match"] == "true" for name in split_order),
        "inventory_join_complete": all(
            split_rows_by_name[name]["artifact_inventory_join_complete"] == "true" for name in split_order
        ),
    }


def run_covapie_final_dataset_qa_gate_v1(output_root: Path | str = OUTPUT_ROOT) -> dict[str, Any]:
    """Validate canonical Step 14AR outputs and write deterministic QA v1 outputs."""
    output_root = Path(output_root)
    source_hashes_before = {path.as_posix(): _sha256(_repo_path(path)) for path in _all_read_paths()}
    source = _load_source()
    preconditions = _build_preconditions(source)
    artifacts = _build_artifact_inventory(source)
    lineage = _build_schema_lineage(source)
    split = _build_split_audit(source)
    masks = _build_mask_audit(source)
    safety = _build_safety_audit(source, source_hashes_before)
    sections = {
        "all_preconditions_passed": _section_passed(preconditions, "precondition_passed"),
        "all_artifact_inventory_qa_passed": _section_passed(artifacts, "artifact_inventory_qa_passed"),
        "all_schema_lineage_qa_passed": _section_passed(lineage, "schema_lineage_qa_passed"),
        "all_split_leakage_qa_passed": _section_passed(split, "split_leakage_qa_passed"),
        "all_mask_contract_qa_passed": _section_passed(masks, "mask_contract_qa_passed"),
        "all_safety_training_boundary_qa_passed": _section_passed(safety, "safety_training_boundary_qa_passed"),
    }
    split_evidence = _summarize_split_evidence(split)
    blockers: list[str] = []
    for rows, field in (
        (preconditions, "blocking_reasons"), (artifacts, "blocking_reasons"), (lineage, "blocking_reasons"),
        (split, "blocking_reasons"), (masks, "blocking_reasons"), (safety, "blocking_reasons"),
    ):
        blockers.extend(row[field] for row in rows if row[field])
    all_checks_passed = all(sections.values())
    issues = _build_issue_rows(all_checks_passed, blockers)
    output_root.mkdir(parents=True, exist_ok=True)
    output_rows = (
        (CSV_OUTPUTS[0], PRECONDITION_COLUMNS, preconditions), (CSV_OUTPUTS[1], ARTIFACT_COLUMNS, artifacts),
        (CSV_OUTPUTS[2], LINEAGE_COLUMNS, lineage), (CSV_OUTPUTS[3], SPLIT_COLUMNS, split),
        (CSV_OUTPUTS[4], MASK_COLUMNS, masks), (CSV_OUTPUTS[5], SAFETY_COLUMNS, safety),
        (CSV_OUTPUTS[6], ISSUE_COLUMNS, issues),
    )
    for filename, columns, rows in output_rows:
        _write_csv(output_root / filename, columns, rows)
    output_sha256 = {filename: _sha256(output_root / filename) for filename in CSV_OUTPUTS}
    manifest = {
        "stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME,
        "previous_stage": PREVIOUS_STAGE, "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "source_step14ar_manifest_path": (AR_ROOT / INPUT_FILENAMES[-1]).as_posix(),
        "source_step14ar_manifest_sha256": SOURCE_STEP14AR_MANIFEST_SHA256,
        "source_step14aq_manifest_path": AQ_MANIFEST.as_posix(),
        "source_step14aq_manifest_sha256": SOURCE_STEP14AQ_MANIFEST_SHA256,
        "source_input_sha256": {path.as_posix(): source_hashes_before[path.as_posix()] for path in _source_input_paths()},
        "source_input_count": 12, "source_input_read_boundary": "only_step14ar_12_outputs_and_step14aq_manifest",
        "artifact_inventory_paths_not_recursively_opened": True,
        "canonical_schema_field_count": len(FINAL_INDEX_FIELDS), "final_dataset_row_count": len(source["index_csv"]),
        "final_dataset_membership_row_count": len(source["membership"]), "artifact_inventory_row_count": len(source["artifact_inventory"]),
        "split_summary_row_count": len(source["split"]), "canonical_mask_task_count": len(CANONICAL_MASK_PAIRS),
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "split_sample_counts": split_evidence["sample_counts"],
        "split_group_counts": split_evidence["group_counts"],
        "split_artifact_reference_counts": split_evidence["artifact_counts"],
        "source_step14aq_sample_counts_available": split_evidence["aq_sample_counts_available"],
        "source_step14aq_sample_counts_match": (
            split_evidence["aq_sample_counts_available"] and split_evidence["aq_sample_counts_match"]
        ),
        "source_step14aq_group_counts_available": split_evidence["aq_group_counts_available"],
        "source_step14aq_group_counts_match": (
            split_evidence["aq_group_counts_available"] and split_evidence["aq_group_counts_match"]
        ),
        "source_step14aq_artifact_reference_counts_available": False,
        "source_step14aq_artifact_reference_count_crosscheck_status": "not_available_in_source_manifest",
        "artifact_reference_counts_recomputed_from_step14ar_inventory": True,
        "artifact_reference_inventory_join_complete": split_evidence["inventory_join_complete"],
        "artifact_reference_count_evidence_source": "step14ar_artifact_inventory_joined_to_membership",
        **sections, "all_checks_passed": all_checks_passed, "blocking_reasons": blockers,
        "qa_issue_count": 0 if all_checks_passed else len(blockers),
        "ready_for_covapie_canonical_final_dataset_bulk_download_admission_design_gate": all_checks_passed,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_known_for_training": False,
        "unknown_atom_feature_policy_finalized_for_training": False,
        "feature_semantics_audit_required_before_training": True,
        "leakage_split_design_required_before_training": True,
        "ready_for_bulk_download_now": False,
        "training_blockers": [
            "feature_semantics_audit_required_before_training",
            "bulk_download_admission_design_not_completed",
        ],
        "raw_data_read": False, "network_access_used": False, "torch_imported": False, "numpy_imported": False,
        "rdkit_used": False, "biopython_used": False, "gemmi_used": False,
        "model_forward_called": False, "loss_compute_called": False, "backward_called": False,
        "optimizer_created": False, "trainer_fit_called": False, "checkpoint_loaded": False,
        "output_file_count": 8, "non_manifest_output_count": 7,
        "output_files": [*CSV_OUTPUTS, MANIFEST_FILENAME], "output_sha256": output_sha256,
        "recommended_next_step": NEXT_STAGE if all_checks_passed else "resolve_covapie_final_dataset_qa_v1_blockers",
    }
    (output_root / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


run_final_dataset_qa_gate_v1 = run_covapie_final_dataset_qa_gate_v1


__all__ = [
    "AQ_MANIFEST", "AR_ROOT", "CANONICAL_MASK_PAIRS", "DEFAULT_OUTPUT_ROOT", "OUTPUT_ROOT", "FINAL_INDEX_FIELDS",
    "MANIFEST_FILENAME", "NEXT_STAGE", "SOURCE_STEP14AQ_MANIFEST_SHA256", "SOURCE_STEP14AR_MANIFEST_SHA256",
    "STAGE", "run_covapie_final_dataset_qa_gate_v1", "run_final_dataset_qa_gate_v1",
]
