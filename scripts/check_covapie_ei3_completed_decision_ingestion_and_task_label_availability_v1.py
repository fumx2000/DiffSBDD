#!/usr/bin/env python3
"""Independent checker for EI3 completed-decision ingestion Exact7."""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import io
import json
from pathlib import Path
import stat
import subprocess
from typing import Any, Callable, Mapping, NoReturn


ERROR_PREFIX = "COVAPIE_EI3_INGESTION_CHECK_ERROR"
BASELINE = "6c22eb41d55f7d08ff076a928070258700b335d9"
UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_79526304E5FB38A6"
FORMAL_SCHEMA = "covapie_ei3_exact3_formal_human_decision_v1"
FORMAL_SHA = "f0cf2e1703a327d2ace42bb0aba900e1f4a5ef46de96cc2c5f4acf93add2f5f7"
EVENT_IDS = (
    "COVAPIE_CYS_SG_EVENT_V1:5ARB:A:CYS:217-:SG:F:EI3:C1",
    "COVAPIE_CYS_SG_EVENT_V1:5ARC:A:CYS:217-:SG:C:EI3:C1",
    "COVAPIE_CYS_SG_EVENT_V1:5ARD:A:CYS:217-:SG:E:EI3:C1",
)
PDB_IDS = ("5ARB", "5ARC", "5ARD")
RANKS = (967, 968, 969)
METAL_COUNTS = {"5ARB": 0, "5ARC": 0, "5ARD": 2}
GENERIC_FIELDS = (
    "canonical_event_id", "review_unit_id", "human_review_completed",
    "legacy_completed_review_status", "task_relevance_disposition",
    "chemistry_disposition", "training_disposition", "human_training_excluded",
    "source_decision_schema", "source_decision_sha256", "source_binding_path",
)
SOURCE = Path("src/covalent_ext/covapie_ei3_completed_decision_ingestion_and_task_label_availability_v1.py")
CHECKER = Path("scripts/check_covapie_ei3_completed_decision_ingestion_and_task_label_availability_v1.py")
TEST = Path("tests/test_covapie_ei3_completed_decision_ingestion_and_task_label_availability_v1.py")
OUT = Path("data/derived/covalent_small/covapie_ei3_completed_decision_ingestion_and_task_label_availability_v1")
SNAPSHOT = OUT / "covapie_ei3_completed_human_decision_snapshot_v1.json"
MATRIX = OUT / "covapie_ei3_event_task_label_availability_v1.csv"
SUMMARY = OUT / "covapie_ei3_completed_decision_ingestion_summary_v1.json"
MANIFEST = OUT / "covapie_ei3_completed_decision_ingestion_manifest_v1.json"
EXACT7 = (SOURCE, CHECKER, TEST, SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
STATE = Path(
    "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
    "EI3_COVAPIE_BULK_REVIEW_UNIT_79526304E5FB38A6"
)
FORMAL = STATE / "formal-human-decision-v1/ei3_formal_human_decision_v1.json"
FORMAL_VALIDATOR = STATE / "formal-human-decision-v1/validate_ei3_formal_human_decision_v1.py"
EVENT_SOURCE = STATE / "review-preparation-v1/ei3_exact3_event_evidence_v1.csv"
GRAPH_SOURCE = STATE / "review-preparation-v1/ei3_graph_and_review_evidence_v1.json"
POLICY = Path("src/covalent_ext/covapie_source_binding_policy_v2.py")
TASK_OWNER = Path("src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py")
GENERIC_OWNER = Path("src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py")
CENSUS = Path(
    "data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_me7_v1/"
    "covapie_cumulative1000_current_global_readiness_census_with_me7_v1.csv"
)
QUEUE = Path(
    "data/derived/covalent_small/covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1/"
    "covapie_bulk_cys_sg_priority_human_review_queue_v1.csv"
)
SOURCE_BINDINGS = (
    (FORMAL, "project_parent_relative", 68366, FORMAL_SHA),
    (FORMAL_VALIDATOR, "project_parent_relative", 69828, "90773895c5a74ffb65a7f59d50cfcc5766355d74b98e269ebc1848acf184ae9b"),
    (EVENT_SOURCE, "project_parent_relative", 2702, "0a942726c4b2dd30ded1ec3225ab9b8ffbb253e76ddfc14be4f420da92d48323"),
    (GRAPH_SOURCE, "project_parent_relative", 82960, "851eb35b2845e7d06cd90136ff1d8bf59fdfcbdf9049a8380d14ee69c967b4a4"),
    (POLICY, "repository_relative", 3704, "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee"),
    (TASK_OWNER, "repository_relative", 67274, "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b"),
    (GENERIC_OWNER, "repository_relative", 35925, "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548"),
    (CENSUS, "repository_relative", 559446, "9e45211a66a003be7f5f8c8b49b0a7f6f22bce362a06601708affff6a0ce4b4a"),
    (QUEUE, "repository_relative", 50116, "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2"),
)

MATRIX_HEADER = (
    "artifact_role", "canonical_event_id", "scaleup_rank", "review_unit_id", "pdb_id",
    "protein_label_asym_id", "component_label_asym_id", "component_auth_asym_id",
    "connection_id", "source_observed_pair", "reported_distance_angstrom",
    "recalculated_distance_angstrom", "absolute_difference_angstrom",
    "protein_coordinates_json", "component_coordinates_json", "source_datasets_json",
    "source_record_ids_json", "evidence_human_selected", "human_review_completed",
    "D4_formally_answered", "D5_formally_answered", "completed_lane",
    "legacy_completed_review_status", "source_formal_D1", "chemistry_disposition",
    "negative_chemistry", "source_formal_D2", "normalized_task_relevance_disposition",
    "task_domain_negative", "source_formal_D3", "pair_sample_authority",
    "target_covalent_connection_count", "metal_context_connection_count",
    "source_formal_D4", "D4_source_proposal_field", "role_candidate_count",
    "selected_role_candidate_json", "role_profile_raw_json", "role_profile_derived_state",
    "warhead_atom_ids_json", "linker_atom_ids_json", "scaffold_atom_ids_json",
    "minimal_seed_json", "minimal_seed_atom_ids_json", "primary_anchor_json",
    "role_partition_sample_authoritative", "minimal_seed_sample_authoritative",
    "role_runtime_executed", "seed_runtime_executed", "source_formal_D5",
    "structurally_applicable_task_ids_json", "task_applicability_sample_authoritative",
    "task_runtime_executed", "canonical_task_count", "B3_present", "sixth_task",
    "canonical_mask_structural_labels_available", "task_label_authority",
    "event_task_label_rows_materialized", "mask_tensor_targets_created",
    "source_formal_D6", "training_disposition", "human_training_excluded",
    "future_training_admission_candidate", "formal_training_admitted",
    "training_materialization_allowed", "POST_source_evidence_available",
    "POST_sample_geometry_authority", "POST_geometry_training_authority",
    "PRE_source_graph_count", "PRE_source_mapping_count",
    "PRE_source_graph_mapping_status", "PRE_mapping_auto_selected", "PRE_authority",
    "POST_to_PRE_copy", "PRE_zero_fill",
    "accurate_PRE_required_before_training_feature_contract",
    "FEATURE_SEMANTICS_AUDIT_PERFORMED",
    "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING", "READY_FOR_TRAINING",
    "TRAINING_STARTED",
)
MATRIX_JSON_COLUMNS = frozenset(
    {
        "protein_coordinates_json", "component_coordinates_json", "source_datasets_json",
        "source_record_ids_json", "selected_role_candidate_json", "role_profile_raw_json",
        "warhead_atom_ids_json", "linker_atom_ids_json", "scaffold_atom_ids_json",
        "minimal_seed_json", "minimal_seed_atom_ids_json", "primary_anchor_json",
        "structurally_applicable_task_ids_json",
    }
)
MATRIX_INTEGER_COLUMNS = frozenset(
    {
        "scaleup_rank", "target_covalent_connection_count",
        "metal_context_connection_count", "role_candidate_count", "canonical_task_count",
        "PRE_source_graph_count", "PRE_source_mapping_count",
    }
)
MATRIX_STRING_COLUMNS = frozenset(
    {
        "artifact_role", "canonical_event_id", "review_unit_id", "pdb_id",
        "protein_label_asym_id", "component_label_asym_id", "component_auth_asym_id",
        "connection_id", "source_observed_pair", "reported_distance_angstrom",
        "recalculated_distance_angstrom", "absolute_difference_angstrom",
        "completed_lane", "legacy_completed_review_status", "source_formal_D1",
        "chemistry_disposition", "source_formal_D2",
        "normalized_task_relevance_disposition", "source_formal_D3", "source_formal_D4",
        "D4_source_proposal_field", "role_profile_derived_state", "source_formal_D5",
        "source_formal_D6", "training_disposition", "PRE_source_graph_mapping_status",
    }
)
MATRIX_BOOLEAN_COLUMNS = frozenset(MATRIX_HEADER) - (
    MATRIX_JSON_COLUMNS | MATRIX_INTEGER_COLUMNS | MATRIX_STRING_COLUMNS
)
MATRIX_COLUMN_TYPES = tuple(
    {
        "column": column,
        "value_type": (
            "canonical_json"
            if column in MATRIX_JSON_COLUMNS
            else "integer"
            if column in MATRIX_INTEGER_COLUMNS
            else "boolean"
            if column in MATRIX_BOOLEAN_COLUMNS
            else "string"
        ),
    }
    for column in MATRIX_HEADER
)

if len(MATRIX_HEADER) != 81 or len(set(MATRIX_HEADER)) != 81:
    raise RuntimeError("EI3 checker matrix contract must be unique Exact81")


class CheckError(ValueError):
    pass


def fail(reason: str) -> NoReturn:
    raise CheckError(ERROR_PREFIX + ":" + reason)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def strict_json(payload: bytes, label: str) -> dict[str, Any]:
    if type(payload) is not bytes or payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload or b"\r" in payload:
        fail("JSON_TEXT_INVALID:" + label)

    def hook(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                fail("JSON_DUPLICATE_KEY:" + label + ":" + key)
            result[key] = value
        return result

    try:
        value = json.loads(
            payload.decode("utf-8"), object_pairs_hook=hook,
            parse_constant=lambda value: fail("JSON_NONFINITE:" + value),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CheckError(ERROR_PREFIX + ":JSON_PARSE_FAILED:" + label) from error
    if type(value) is not dict:
        fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def parse_csv(payload: bytes, label: str) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    if type(payload) is not bytes or payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload or b"\r" in payload:
        fail("CSV_TEXT_INVALID:" + label)
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""), strict=True)
        header = tuple(reader.fieldnames or ())
        if not header or len(header) != len(set(header)):
            fail("CSV_HEADER_DUPLICATE_OR_EMPTY:" + label)
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise CheckError(ERROR_PREFIX + ":CSV_PARSE_FAILED:" + label) from error
    if any(None in row or set(row) != set(header) for row in rows):
        fail("CSV_ROW_WIDTH_INVALID:" + label)
    return header, rows


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _canonical_json_cell(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _canonical_csv_bytes(
    header: tuple[str, ...], rows: list[dict[str, str]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=header,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _strict_json_cell(value: str, event_id: str, column: str) -> object:
    try:
        parsed = json.loads(
            value,
            object_pairs_hook=lambda pairs: _unique_json_cell_pairs(
                pairs, event_id, column
            ),
            parse_constant=lambda constant: fail(
                "MATRIX_JSON_NONFINITE:"
                + event_id
                + ":"
                + column
                + ":"
                + constant
            ),
        )
    except json.JSONDecodeError as error:
        raise CheckError(
            ERROR_PREFIX + ":MATRIX_JSON_INVALID:" + event_id + ":" + column
        ) from error
    return parsed


def _unique_json_cell_pairs(
    pairs: list[tuple[str, object]], event_id: str, column: str
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            fail("MATRIX_JSON_DUPLICATE_KEY:" + event_id + ":" + column + ":" + key)
        result[key] = value
    return result


def git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo_root, check=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )


def _git_text(repo_root: Path, *args: str) -> str:
    result = git(repo_root, *args)
    if result.returncode != 0:
        fail("GIT_COMMAND_FAILED:" + " ".join(args))
    return result.stdout


def _is_ancestor(repo_root: Path, older: str, newer: str) -> bool:
    result = git(repo_root, "merge-base", "--is-ancestor", older, newer)
    if result.returncode not in {0, 1}:
        fail("GIT_ANCESTOR_CHECK_FAILED")
    return result.returncode == 0


def check_git_lifecycle(repo_root: Path) -> dict[str, object]:
    branch = _git_text(repo_root, "branch", "--show-current").strip()
    head = _git_text(repo_root, "rev-parse", "HEAD").strip()
    origin = _git_text(repo_root, "rev-parse", "refs/remotes/origin/main").strip()
    split = _git_text(repo_root, "rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main").split()
    if branch != "main" or len(split) != 2 or not all(value.isdigit() for value in split):
        fail("GIT_BASE_STATE_INVALID")
    if _git_text(repo_root, "ls-files", "-u"):
        fail("GIT_CONFLICTS_PRESENT")
    if _git_text(repo_root, "diff", "--name-only") or _git_text(repo_root, "diff", "--cached", "--name-only"):
        fail("TRACKED_OR_STAGED_MODIFICATION_PRESENT")
    untracked = set(
        line for line in _git_text(repo_root, "ls-files", "--others", "--exclude-standard").splitlines() if line
    )
    exact = {path.as_posix() for path in EXACT7}
    index_text = _git_text(repo_root, "ls-files", "--stage", "--", *(path.as_posix() for path in EXACT7))
    records = []
    for line in index_text.splitlines():
        left, path = line.split("\t", 1)
        mode, oid, stage = left.split()
        records.append((mode, oid, stage, path))
    if not records:
        profile = "CANDIDATE_UNTRACKED"
        if head != BASELINE or origin != BASELINE or split != ["0", "0"]:
            fail("UNTRACKED_PROFILE_BASELINE_DRIFT")
        if untracked != exact:
            fail("UNTRACKED_PROFILE_INVENTORY_DRIFT")
    elif len(records) == 7:
        profile = "TRACKED_CLEAN"
        if untracked:
            fail("TRACKED_PROFILE_UNTRACKED_PRESENT")
        if {record[3] for record in records} != exact:
            fail("TRACKED_PROFILE_INVENTORY_DRIFT")
        if any(record[0] != "100644" or record[2] != "0" for record in records):
            fail("TRACKED_PROFILE_STAGE_OR_MODE_DRIFT")
        if not _is_ancestor(repo_root, BASELINE, head) or not _is_ancestor(repo_root, BASELINE, origin):
            fail("TRACKED_PROFILE_BASELINE_NOT_ANCESTOR")
        if not (_is_ancestor(repo_root, head, origin) or _is_ancestor(repo_root, origin, head)):
            fail("TRACKED_PROFILE_DIVERGED")
    else:
        fail("GIT_LIFECYCLE_PROFILE_UNKNOWN")
    for path in EXACT7:
        full = repo_root / path
        try:
            metadata = full.lstat()
        except OSError as error:
            raise CheckError(ERROR_PREFIX + ":EXACT7_PATH_MISSING:" + path.as_posix()) from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            fail("EXACT7_PATH_CLASS_INVALID:" + path.as_posix())
        if metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            fail("EXACT7_PATH_EXECUTABLE:" + path.as_posix())
    return {
        "profile": profile, "branch": branch, "HEAD": head, "origin_main": origin,
        "ahead": int(split[0]), "behind": int(split[1]), "exact7_count": 7,
        "staged_modification_count": 0, "tracked_modification_count": 0,
        "conflicted_count": 0, "ordinary_untracked_count": len(untracked),
    }


def _source_path(repo_root: Path, relative: Path, namespace: str) -> Path:
    if namespace == "repository_relative":
        return repo_root / relative
    if namespace == "project_parent_relative":
        return repo_root.parent / relative
    fail("SOURCE_NAMESPACE_INVALID:" + namespace)


def _verified_source_payload(repo_root: Path, relative: Path) -> bytes:
    matches = [binding for binding in SOURCE_BINDINGS if binding[0] == relative]
    if len(matches) != 1:
        fail("SOURCE_BINDING_LOOKUP_NOT_EXACT1:" + relative.as_posix())
    _, namespace, size, digest = matches[0]
    path = _source_path(repo_root, relative, namespace)
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise CheckError(
            ERROR_PREFIX + ":SOURCE_READ_FAILED:" + relative.as_posix()
        ) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        fail("SOURCE_CLASS_INVALID:" + relative.as_posix())
    if len(payload) != size or sha256(payload) != digest:
        fail("SOURCE_IDENTITY_DRIFT:" + relative.as_posix())
    return payload


def independently_check_sources(repo_root: Path) -> dict[str, object]:
    payloads: dict[Path, bytes] = {}
    for relative, _namespace, _size, _digest in SOURCE_BINDINGS:
        payloads[relative] = _verified_source_payload(repo_root, relative)
    formal = strict_json(payloads[FORMAL], "FORMAL")
    if formal.get("schema_version") != FORMAL_SCHEMA or formal.get("stage") != "EI3_FORMAL_HUMAN_DECISION_V1":
        fail("FORMAL_SCHEMA_OR_STAGE_DRIFT")
    identity = formal.get("sample_identity")
    if type(identity) is not dict or identity.get("review_unit_id") != UNIT_ID or identity.get("canonical_target_event_ids") != list(EVENT_IDS) or identity.get("scaleup_ranks") != list(RANKS) or identity.get("pdb_ids") != list(PDB_IDS):
        fail("FORMAL_SAMPLE_IDENTITY_DRIFT")
    authority = formal.get("sample_level_authority")
    if type(authority) is not dict or authority.get("human_review_completed") is not True or authority.get("sample_observed_pair_authority") is not True or authority.get("role_partition_sample_authoritative") is not False or authority.get("task_applicability_sample_authoritative") is not False:
        fail("FORMAL_SAMPLE_AUTHORITY_DRIFT")
    decisions = formal.get("approved_D1_D6")
    if type(decisions) is not dict:
        fail("FORMAL_DECISIONS_NOT_OBJECT")
    expected_decisions = {
        "D1_observed_covalent_chemistry": "POSITIVE",
        "D2_task_generation_domain_relevance": "OUT_OF_DOMAIN",
        "D3_reactive_atom_pair_confirmation_or_revision": "CONFIRM_OBSERVED_PAIR",
        "D4_role_partition_and_minimal_seed": "CANNOT_DETERMINE",
        "D5_structural_task_applicability": "NOT_DETERMINABLE",
        "D6_later_training_use_disposition": "NOT_APPLICABLE",
    }
    for key, value in expected_decisions.items():
        if type(decisions.get(key)) is not dict or decisions[key].get("decision") != value or decisions[key].get("human_answered") is not True:
            fail("FORMAL_DECISION_DRIFT:" + key)
    if decisions["D5_structural_task_applicability"].get("task_ids", object()) is not None:
        fail("FORMAL_D5_TASK_IDS_NOT_NULL")
    pre = formal.get("PRE_boundary", {}).get("frozen_source_projection")
    if type(pre) is not dict or pre.get("PRE_source_graph_count_per_event") != [0, 0, 0] or pre.get("PRE_source_graph_mapping_count_per_event") != [0, 0, 0] or pre.get("PRE_source_graph_mapping_status_per_event") != ["PRE_SOURCE_GRAPH_NOT_AVAILABLE"] * 3 or pre.get("PRE_status_per_event") != ["PRE_REACTION_UNRESOLVED"] * 3 or pre.get("accurate_PRE_required_before_training_feature_contract") is not False:
        fail("FORMAL_PRE_BOUNDARY_DRIFT")
    if len(formal.get("source_bindings", [])) != 10 or any(row.get("path_namespace") != "review_unit_relative" for row in formal["source_bindings"]):
        fail("FORMAL_INTERNAL_BINDINGS_DRIFT")
    _header, rows = parse_csv(payloads[EVENT_SOURCE], "EVENT_SOURCE")
    if len(rows) != 3 or [row["canonical_event_id"] for row in rows] != list(EVENT_IDS):
        fail("EVENT_SOURCE_EXACT3_DRIFT")
    for row, pdb, rank in zip(rows, PDB_IDS, RANKS, strict=True):
        if row["pdb_id"] != pdb or row["scaleup_rank"] != str(rank) or row["source_observed_pair"] != "SG:C1" or row["connection_id"] != "covale1" or row["human_selected"] != "false" or row["protein_label_seq_id"] != "211" or row["protein_auth_seq_id"] != "217" or row["pre_source_graph_count"] != "0" or row["pre_source_graph_mapping_count"] != "0":
            fail("EVENT_SOURCE_ROW_DRIFT:" + pdb)
    graph = strict_json(payloads[GRAPH_SOURCE], "GRAPH_SOURCE")
    if graph.get("review_unit_id") != UNIT_ID or [row.get("canonical_event_id") for row in graph.get("target_events", [])] != list(EVENT_IDS):
        fail("GRAPH_TARGET_EXACT3_DRIFT")
    context = graph.get("additional_instance_connection_context")
    if type(context) is not list or [row.get("connection_id") for row in context] != ["metalc8", "metalc9"] or any(row.get("target_event") is not False or row.get("supporting_context_only") is not True or row.get("canonical_event_id") is not None for row in context):
        fail("GRAPH_METAL_CONTEXT_DRIFT")
    pre_graph = graph.get("pre_post_observation_summary")
    if type(pre_graph) is not dict or pre_graph.get("PRE_source_graph_count_per_event") != [0, 0, 0] or pre_graph.get("PRE_source_graph_mapping_count_per_event") != [0, 0, 0]:
        fail("GRAPH_PRE_BOUNDARY_DRIFT")
    _census_header, census_rows = parse_csv(payloads[CENSUS], "CENSUS")
    selected = [row for row in census_rows if row.get("canonical_event_id") in EVENT_IDS]
    if len(selected) != 3 or any(row.get("current_review_status") != "CURRENTLY_UNREVIEWED" or row.get("human_review_completed") != "false" for row in selected):
        fail("CENSUS_PENDING_STATE_DRIFT")
    _queue_header, queue_rows = parse_csv(payloads[QUEUE], "QUEUE")
    units = [row for row in queue_rows if row.get("review_unit_id") == UNIT_ID]
    if len(units) != 1 or units[0].get("priority_rank") != "33" or units[0].get("human_decision_created") != "false":
        fail("QUEUE_PENDING_STATE_DRIFT")
    source_tree = ast.parse((repo_root / SOURCE).read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(source_tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    if "subprocess" in imported or "runpy" in imported:
        fail("OWNER_FORBIDDEN_VALIDATOR_EXECUTION_IMPORT")
    checker_tree = ast.parse((repo_root / CHECKER).read_text(encoding="utf-8"))
    if any(isinstance(node, ast.ImportFrom) and node.module and "covapie_ei3_completed_decision" in node.module for node in ast.walk(checker_tree)):
        fail("CHECKER_IMPORTS_OWNER")
    return {
        "active_source_binding_count": 9,
        "formal_internal_source_binding_count": 10,
        "formal_source_sha256": FORMAL_SHA,
        "formal_validator_identity_only": True,
        "formal_validator_imported_executed_or_subprocessed": False,
        "source_schema": FORMAL_SCHEMA,
        "source_event_count": 3,
        "census_row_count": len(census_rows),
        "queue_row_count": len(queue_rows),
    }


def _read_artifacts(repo_root: Path) -> dict[Path, bytes]:
    if not (repo_root / OUT).is_dir() or (repo_root / OUT).is_symlink():
        fail("OUTPUT_DIRECTORY_INVALID")
    inventory = {path.name for path in (repo_root / OUT).iterdir()}
    if inventory != {path.name for path in (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)}:
        fail("OUTPUT_INVENTORY_NOT_EXACT4")
    result: dict[Path, bytes] = {}
    for relative in (SNAPSHOT, MATRIX, SUMMARY, MANIFEST):
        path = repo_root / relative
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            fail("OUTPUT_CLASS_INVALID:" + relative.name)
        if metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            fail("OUTPUT_EXECUTABLE:" + relative.name)
        payload = path.read_bytes()
        if not payload.endswith(b"\n") or payload.endswith(b"\n\n") or b"\r" in payload or b"\x00" in payload or payload.startswith(b"\xef\xbb\xbf"):
            fail("OUTPUT_TEXT_INVARIANT:" + relative.name)
        result[relative] = payload
    return result


def _check_snapshot(snapshot: Mapping[str, Any]) -> None:
    expected = {
        "schema_version": "covapie_ei3_completed_human_decision_snapshot_v1",
        "stage": "EI3_COMPLETED_DECISION_INGESTION_V1",
        "artifact_role": "PROJECTION_OF_FROZEN_FORMAL_HUMAN_AUTHORITY",
        "review_unit_id": UNIT_ID,
        "event_count": 3,
        "active_source_binding_count": 9,
        "historical_source_snapshot_human_authority_false_does_not_override_formal": True,
    }
    for key, value in expected.items():
        if snapshot.get(key) != value:
            fail("SNAPSHOT_ROOT_DRIFT:" + key)
    authority = snapshot.get("sample_level_authority")
    if type(authority) is not dict or authority.get("human_review_completed") is not True or authority.get("sample_observed_pair_authority") is not True or authority.get("role_partition_sample_authoritative") is not False or authority.get("minimal_seed_sample_authoritative") is not False or authority.get("task_applicability_sample_authoritative") is not False:
        fail("SNAPSHOT_AUTHORITY_DRIFT")
    role = snapshot.get("role_and_task_disposition")
    for key in (
        "applicable_task_ids", "linker_atom_ids", "minimal_seed", "minimal_seed_atom_ids",
        "primary_anchor", "role_partitions", "role_profile", "scaffold_atom_ids",
        "selected_candidate_id", "selected_role_candidate", "warhead_atom_ids",
    ):
        if type(role) is not dict or key not in role or role[key] is not None:
            fail("SNAPSHOT_ROLE_TASK_NULL_DRIFT:" + key)
    events = snapshot.get("events")
    if type(events) is not list or [row.get("canonical_event_id") for row in events] != list(EVENT_IDS):
        fail("SNAPSHOT_EVENTS_NOT_EXACT3")
    for row, pdb, metal in zip(events, PDB_IDS, (0, 0, 2), strict=True):
        expected_event = {
            "pdb_id": pdb, "human_review_completed": True,
            "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
            "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
            "source_formal_D1": "POSITIVE", "chemistry_disposition": "POSITIVE",
            "negative_chemistry": False, "source_formal_D2": "OUT_OF_DOMAIN",
            "normalized_task_relevance_disposition": "NOT_RELEVANT",
            "task_domain_negative": True, "source_formal_D3": "CONFIRM_OBSERVED_PAIR",
            "pair_sample_authority": True, "target_covalent_connection_count": 1,
            "metal_context_connection_count": metal, "source_formal_D4": "CANNOT_DETERMINE",
            "D4_formally_answered": True, "source_formal_D5": "NOT_DETERMINABLE",
            "D5_formally_answered": True, "source_formal_D6": "NOT_APPLICABLE",
            "training_disposition": "NOT_APPLICABLE", "human_training_excluded": False,
            "future_training_admission_candidate": False,
            "formal_training_admitted": False, "training_materialization_allowed": False,
            "evidence_human_selected": False,
        }
        for key, value in expected_event.items():
            if row.get(key) != value:
                fail("SNAPSHOT_EVENT_DRIFT:" + pdb + ":" + key)
        protein, component = row.get("protein_endpoint"), row.get("component_endpoint")
        if type(protein) is not dict or protein.get("label_seq_id") != 211 or protein.get("auth_seq_id") != 217 or protein.get("occupancy_lexeme") != "1.00":
            fail("SNAPSHOT_PROTEIN_LOCATOR_DRIFT:" + pdb)
        if type(component) is not dict or component.get("auth_seq_id") not in {1280, 1277, 1279} or component.get("occupancy_lexeme") not in {"0.70", "0.50"}:
            fail("SNAPSHOT_COMPONENT_LOCATOR_DRIFT:" + pdb)
    context = snapshot.get("covalent_and_metal_context_boundary")
    records = context.get("metal_supporting_context_records") if type(context) is dict else None
    if type(records) is not list or [row.get("connection_id") for row in records] != ["metalc8", "metalc9"] or context.get("metal_context_is_not_generic_fact") is not True or context.get("metal_context_is_not_pair_or_geometry_authority") is not True:
        fail("SNAPSHOT_METAL_CONTEXT_DRIFT")
    pre = snapshot.get("PRE_boundary")
    frozen = pre.get("frozen_source_projection") if type(pre) is dict else None
    if type(frozen) is not dict or frozen.get("PRE_source_graph_count_per_event") != [0, 0, 0] or frozen.get("PRE_source_graph_mapping_count_per_event") != [0, 0, 0] or frozen.get("accurate_PRE_required_before_training_feature_contract") is not False:
        fail("SNAPSHOT_PRE_BOUNDARY_DRIFT")
    tasks = snapshot.get("canonical_task_contract")
    names = [row.get("semantic_long_name") for row in tasks.get("global_canonical_tasks", [])] if type(tasks) is dict else []
    if names != ["warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only", "scaffold_plus_linker_plus_warhead"] or tasks.get("B3_present") is not True or tasks.get("sixth_task") is not False:
        fail("SNAPSHOT_CANONICAL_EXACT5_DRIFT")
    generic = snapshot.get("generic_Exact11_compatibility")
    facts = generic.get("facts") if type(generic) is dict else None
    if type(facts) is not list or len(facts) != 3 or generic.get("rich_fields_leaked") is not False:
        fail("SNAPSHOT_GENERIC_ROOT_DRIFT")
    generic_owner = importlib.import_module("covalent_ext.covapie_completed_human_decision_reconciliation_v1")
    binding = generic_owner.SourceBinding(
        source_path=FORMAL.as_posix(), path_namespace="repository_parent_relative",
        byte_count=68366, sha256=FORMAL_SHA, schema_version=FORMAL_SCHEMA,
        review_unit_id=UNIT_ID,
    )
    generic_owner._validate_source_binding(binding)
    objects = []
    rich = {"coordinates", "occupancy", "role_profile", "task_ids", "source_datasets"}
    for fact, event_id in zip(facts, EVENT_IDS, strict=True):
        if type(fact) is not dict or set(fact) != set(GENERIC_FIELDS) or set(fact) & rich:
            fail("GENERIC_EXACT11_FIELD_SET_OR_RICH_LEAK:" + event_id)
        if fact != {
            "canonical_event_id": event_id, "review_unit_id": UNIT_ID,
            "human_review_completed": True,
            "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
            "task_relevance_disposition": "NOT_RELEVANT",
            "chemistry_disposition": "POSITIVE", "training_disposition": "NOT_APPLICABLE",
            "human_training_excluded": False, "source_decision_schema": FORMAL_SCHEMA,
            "source_decision_sha256": FORMAL_SHA, "source_binding_path": FORMAL.as_posix(),
        }:
            fail("GENERIC_EXACT11_FACT_DRIFT:" + event_id)
        obj = generic_owner.NormalizedCompletedDecisionFact(**fact)
        generic_owner._validate_fact(obj, binding)
        objects.append(obj)
    generic_owner.NormalizedDecisionSource(binding=binding, facts=tuple(objects))
    current = snapshot.get("current_with_ME7_census_and_queue_preingestion_boundary")
    if type(current) is not dict or current.get("EI3_current_pending_rank") != 1 or current.get("EI3_raw_priority_rank") != 33 or current.get("historical_pending_state_is_expected_until_refresh") is not True:
        fail("SNAPSHOT_CURRENT_PENDING_BOUNDARY_DRIFT")


def _matrix_value(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _matrix_field_fail(
    event_id: str, field: str, actual: object, expected: object
) -> NoReturn:
    fail(
        "MATRIX_FIELD_MISMATCH:"
        + event_id
        + ":"
        + field
        + ":actual="
        + _matrix_value(actual)
        + ":expected="
        + _matrix_value(expected)
    )


def _trusted_matrix_projection(
    repo_root: Path, snapshot: Mapping[str, Any]
) -> list[dict[str, str]]:
    formal = strict_json(_verified_source_payload(repo_root, FORMAL), "MATRIX_FORMAL")
    prep_header, prep_rows = parse_csv(
        _verified_source_payload(repo_root, EVENT_SOURCE), "MATRIX_PREP_EVENT"
    )
    if len(prep_rows) != 3 or [row.get("canonical_event_id") for row in prep_rows] != list(EVENT_IDS):
        fail("MATRIX_PREP_SOURCE_NOT_EXACT3")
    required_prep = {
        "scaleup_rank", "canonical_event_id", "review_unit_id", "pdb_id",
        "protein_label_asym_id", "component_label_asym_id", "component_auth_asym_id",
        "connection_id", "source_observed_pair", "reported_distance_angstrom",
        "recalculated_distance_angstrom", "absolute_difference_angstrom",
        "protein_x", "protein_y", "protein_z", "component_x", "component_y",
        "component_z", "source_datasets_json", "source_record_ids_json", "human_selected",
        "pre_source_graph_count", "pre_source_graph_mapping_count",
        "post_geometry_source_evidence_available",
        "post_geometry_sample_authoritative", "post_geometry_training_target_available",
    }
    if not required_prep.issubset(prep_header):
        fail("MATRIX_PREP_SOURCE_COLUMNS_MISSING")
    decisions = formal["approved_D1_D6"]
    authority = formal["sample_level_authority"]
    formal_pre = formal["PRE_boundary"]["frozen_source_projection"]
    context = formal["event_context_boundary"]
    snapshot_events = snapshot["events"]
    expected_rows: list[dict[str, str]] = []
    null_columns = {
        "selected_role_candidate_json", "role_profile_raw_json", "warhead_atom_ids_json",
        "linker_atom_ids_json", "scaffold_atom_ids_json", "minimal_seed_json",
        "minimal_seed_atom_ids_json", "primary_anchor_json",
        "structurally_applicable_task_ids_json",
    }
    for index, (prep, snapshot_event) in enumerate(
        zip(prep_rows, snapshot_events, strict=True)
    ):
        event_id = EVENT_IDS[index]
        pdb_id = PDB_IDS[index]
        rank = RANKS[index]
        datasets = _strict_json_cell(prep["source_datasets_json"], event_id, "source_datasets_json")
        source_records = _strict_json_cell(
            prep["source_record_ids_json"], event_id, "source_record_ids_json"
        )
        protein_coordinates = [prep["protein_x"], prep["protein_y"], prep["protein_z"]]
        component_coordinates = [
            prep["component_x"], prep["component_y"], prep["component_z"]
        ]
        snapshot_crosscheck = {
            "canonical_event_id": event_id,
            "scaleup_rank": rank,
            "review_unit_id": UNIT_ID,
            "pdb_id": pdb_id,
            "connection_id": prep["connection_id"],
            "source_observed_pair": prep["source_observed_pair"],
            "reported_distance_angstrom_lexeme": prep["reported_distance_angstrom"],
            "recalculated_distance_angstrom_lexeme": prep[
                "recalculated_distance_angstrom"
            ],
            "absolute_difference_angstrom_lexeme": prep[
                "absolute_difference_angstrom"
            ],
            "source_datasets": datasets,
            "source_record_ids": source_records,
            "evidence_human_selected": False,
            "target_covalent_connection_count": context[
                "target_covalent_connection_count_by_pdb"
            ][pdb_id],
            "metal_context_connection_count": context[
                "metal_context_connection_count_by_pdb"
            ][pdb_id],
        }
        for field, expected in snapshot_crosscheck.items():
            actual = snapshot_event.get(field)
            if actual != expected:
                fail(
                    "MATRIX_SNAPSHOT_FIELD_MISMATCH:"
                    + event_id
                    + ":"
                    + field
                    + ":actual="
                    + _matrix_value(actual)
                    + ":expected="
                    + _matrix_value(expected)
                )
        endpoint_crosscheck = {
            "protein_coordinates": (
                snapshot_event.get("protein_endpoint", {}).get("coordinates_lexemes"),
                protein_coordinates,
            ),
            "component_coordinates": (
                snapshot_event.get("component_endpoint", {}).get("coordinates_lexemes"),
                component_coordinates,
            ),
            "protein_label_asym_id": (
                snapshot_event.get("protein_endpoint", {}).get("label_asym_id"),
                prep["protein_label_asym_id"],
            ),
            "component_label_asym_id": (
                snapshot_event.get("component_endpoint", {}).get("label_asym_id"),
                prep["component_label_asym_id"],
            ),
            "component_auth_asym_id": (
                snapshot_event.get("component_endpoint", {}).get("auth_asym_id"),
                prep["component_auth_asym_id"],
            ),
        }
        for field, (actual, expected) in endpoint_crosscheck.items():
            if actual != expected:
                fail(
                    "MATRIX_SNAPSHOT_ENDPOINT_MISMATCH:"
                    + event_id
                    + ":"
                    + field
                    + ":actual="
                    + _matrix_value(actual)
                    + ":expected="
                    + _matrix_value(expected)
                )
        row = {
            "artifact_role": "TASK_LABEL_AVAILABILITY_METADATA_ONLY_NOT_LABEL_ROWS",
            "canonical_event_id": event_id,
            "scaleup_rank": str(rank),
            "review_unit_id": UNIT_ID,
            "pdb_id": pdb_id,
            "protein_label_asym_id": prep["protein_label_asym_id"],
            "component_label_asym_id": prep["component_label_asym_id"],
            "component_auth_asym_id": prep["component_auth_asym_id"],
            "connection_id": prep["connection_id"],
            "source_observed_pair": prep["source_observed_pair"],
            "reported_distance_angstrom": prep["reported_distance_angstrom"],
            "recalculated_distance_angstrom": prep["recalculated_distance_angstrom"],
            "absolute_difference_angstrom": prep["absolute_difference_angstrom"],
            "protein_coordinates_json": _canonical_json_cell(protein_coordinates),
            "component_coordinates_json": _canonical_json_cell(component_coordinates),
            "source_datasets_json": _canonical_json_cell(datasets),
            "source_record_ids_json": _canonical_json_cell(source_records),
            "evidence_human_selected": prep["human_selected"],
            "human_review_completed": "true",
            "D4_formally_answered": (
                "true"
                if decisions["D4_role_partition_and_minimal_seed"]["human_answered"]
                else "false"
            ),
            "D5_formally_answered": (
                "true"
                if decisions["D5_structural_task_applicability"]["human_answered"]
                else "false"
            ),
            "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
            "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
            "source_formal_D1": decisions["D1_observed_covalent_chemistry"]["decision"],
            "chemistry_disposition": "POSITIVE",
            "negative_chemistry": "false",
            "source_formal_D2": decisions["D2_task_generation_domain_relevance"]["decision"],
            "normalized_task_relevance_disposition": "NOT_RELEVANT",
            "task_domain_negative": "true",
            "source_formal_D3": decisions[
                "D3_reactive_atom_pair_confirmation_or_revision"
            ]["decision"],
            "pair_sample_authority": (
                "true" if authority["sample_observed_pair_authority"] else "false"
            ),
            "target_covalent_connection_count": str(
                context["target_covalent_connection_count_by_pdb"][pdb_id]
            ),
            "metal_context_connection_count": str(
                context["metal_context_connection_count_by_pdb"][pdb_id]
            ),
            "source_formal_D4": decisions["D4_role_partition_and_minimal_seed"][
                "decision"
            ],
            "D4_source_proposal_field": "D4_role_partition_and_minimal_seed",
            "role_candidate_count": "0",
            "selected_role_candidate_json": "null",
            "role_profile_raw_json": "null",
            "role_profile_derived_state": "NOT_ESTABLISHED",
            "warhead_atom_ids_json": "null",
            "linker_atom_ids_json": "null",
            "scaffold_atom_ids_json": "null",
            "minimal_seed_json": "null",
            "minimal_seed_atom_ids_json": "null",
            "primary_anchor_json": "null",
            "role_partition_sample_authoritative": "false",
            "minimal_seed_sample_authoritative": "false",
            "role_runtime_executed": "false",
            "seed_runtime_executed": "false",
            "source_formal_D5": decisions["D5_structural_task_applicability"][
                "decision"
            ],
            "structurally_applicable_task_ids_json": "null",
            "task_applicability_sample_authoritative": "false",
            "task_runtime_executed": "false",
            "canonical_task_count": "5",
            "B3_present": "true",
            "sixth_task": "false",
            "canonical_mask_structural_labels_available": "false",
            "task_label_authority": "false",
            "event_task_label_rows_materialized": "false",
            "mask_tensor_targets_created": "false",
            "source_formal_D6": decisions["D6_later_training_use_disposition"][
                "decision"
            ],
            "training_disposition": "NOT_APPLICABLE",
            "human_training_excluded": "false",
            "future_training_admission_candidate": "false",
            "formal_training_admitted": "false",
            "training_materialization_allowed": "false",
            "POST_source_evidence_available": prep[
                "post_geometry_source_evidence_available"
            ],
            "POST_sample_geometry_authority": prep[
                "post_geometry_sample_authoritative"
            ],
            "POST_geometry_training_authority": prep[
                "post_geometry_training_target_available"
            ],
            "PRE_source_graph_count": prep["pre_source_graph_count"],
            "PRE_source_mapping_count": prep["pre_source_graph_mapping_count"],
            "PRE_source_graph_mapping_status": formal_pre[
                "PRE_source_graph_mapping_status_per_event"
            ][index],
            "PRE_mapping_auto_selected": "false",
            "PRE_authority": "false",
            "POST_to_PRE_copy": "false",
            "PRE_zero_fill": "false",
            "accurate_PRE_required_before_training_feature_contract": (
                "true"
                if formal_pre["accurate_PRE_required_before_training_feature_contract"]
                else "false"
            ),
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": "false",
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": "true",
            "READY_FOR_TRAINING": "false",
            "TRAINING_STARTED": "false",
        }
        if set(row) != set(MATRIX_HEADER) or len(row) != 81:
            fail("TRUSTED_MATRIX_PROJECTION_NOT_EXACT81")
        if any(row[column] != "null" for column in null_columns):
            fail("TRUSTED_MATRIX_NULL_CONTRACT_DRIFT")
        expected_rows.append(row)
    return expected_rows


def _check_matrix_types(rows: list[dict[str, str]]) -> None:
    for row in rows:
        event_id = row["canonical_event_id"]
        for column in MATRIX_BOOLEAN_COLUMNS:
            if row[column] not in {"true", "false"}:
                fail(
                    "MATRIX_BOOLEAN_REPRESENTATION_INVALID:"
                    + event_id
                    + ":"
                    + column
                    + ":actual="
                    + _matrix_value(row[column])
                )
        for column in MATRIX_INTEGER_COLUMNS:
            value = row[column]
            try:
                integer = int(value)
            except ValueError as error:
                raise CheckError(
                    ERROR_PREFIX
                    + ":MATRIX_INTEGER_REPRESENTATION_INVALID:"
                    + event_id
                    + ":"
                    + column
                    + ":actual="
                    + _matrix_value(value)
                ) from error
            if str(integer) != value or integer < 0:
                fail(
                    "MATRIX_INTEGER_REPRESENTATION_INVALID:"
                    + event_id
                    + ":"
                    + column
                    + ":actual="
                    + _matrix_value(value)
                )
        for column in MATRIX_JSON_COLUMNS:
            parsed = _strict_json_cell(row[column], event_id, column)
            if _canonical_json_cell(parsed) != row[column]:
                fail(
                    "MATRIX_JSON_REPRESENTATION_NOT_CANONICAL:"
                    + event_id
                    + ":"
                    + column
                )


def _check_matrix(
    header: tuple[str, ...],
    rows: list[dict[str, str]],
    expected_rows: list[dict[str, str]],
) -> None:
    if len(header) != len(set(header)):
        fail("MATRIX_HEADER_DUPLICATE")
    missing = [column for column in MATRIX_HEADER if column not in header]
    extra = [column for column in header if column not in MATRIX_HEADER]
    if missing:
        fail("MATRIX_HEADER_MISSING:" + missing[0])
    if extra:
        fail("MATRIX_HEADER_EXTRA:" + extra[0])
    if header != MATRIX_HEADER:
        fail("MATRIX_HEADER_ORDER_DRIFT")
    if len(rows) != 3 or len(expected_rows) != 3:
        fail("MATRIX_NOT_EXACT3")
    _check_matrix_types(rows)
    for row, expected in zip(rows, expected_rows, strict=True):
        event_id = expected["canonical_event_id"]
        if set(row) != set(MATRIX_HEADER):
            fail("MATRIX_ROW_FIELD_SET_DRIFT:" + event_id)
        for field in MATRIX_HEADER:
            if row[field] != expected[field]:
                _matrix_field_fail(event_id, field, row[field], expected[field])


def _computed_summary_counts(
    rows: list[dict[str, str]], snapshot: Mapping[str, Any]
) -> dict[str, object]:
    def count(column: str, value: str) -> int:
        return sum(row[column] == value for row in rows)

    return {
        "event_count": len(rows),
        "human_review_completed_count": count("human_review_completed", "true"),
        "chemistry_positive_count": count("chemistry_disposition", "POSITIVE"),
        "negative_chemistry_count": count("negative_chemistry", "true"),
        "task_not_relevant_count": count(
            "normalized_task_relevance_disposition", "NOT_RELEVANT"
        ),
        "training_not_applicable_count": count(
            "training_disposition", "NOT_APPLICABLE"
        ),
        "pair_sample_authority_count": count("pair_sample_authority", "true"),
        "role_partition_sample_authority_count": count(
            "role_partition_sample_authoritative", "true"
        ),
        "minimal_seed_sample_authority_count": count(
            "minimal_seed_sample_authoritative", "true"
        ),
        "task_applicability_sample_authority_count": count(
            "task_applicability_sample_authoritative", "true"
        ),
        "role_candidate_count": sum(int(row["role_candidate_count"]) for row in rows),
        "role_runtime_execution_count": count("role_runtime_executed", "true"),
        "seed_runtime_execution_count": count("seed_runtime_executed", "true"),
        "task_runtime_execution_count": count("task_runtime_executed", "true"),
        "generic_exact11_fact_count": len(
            snapshot["generic_Exact11_compatibility"]["facts"]
        ),
        "generic_exact11_field_count": snapshot["generic_Exact11_compatibility"][
            "generic_fact_field_count"
        ],
        "rich_fields_leaked_to_generic_facts": snapshot[
            "generic_Exact11_compatibility"
        ]["rich_fields_leaked"],
        "human_training_excluded_count": count("human_training_excluded", "true"),
        "future_training_admission_candidate_count": count(
            "future_training_admission_candidate", "true"
        ),
        "formal_training_admitted_count": count("formal_training_admitted", "true"),
        "training_materialization_allowed_count": count(
            "training_materialization_allowed", "true"
        ),
        "task_label_authority_count": count("task_label_authority", "true"),
        "event_task_label_rows_materialized_count": count(
            "event_task_label_rows_materialized", "true"
        ),
        "mask_tensor_targets_created_count": count(
            "mask_tensor_targets_created", "true"
        ),
        "canonical_structural_label_available_count": count(
            "canonical_mask_structural_labels_available", "true"
        ),
        "target_covalent_connection_count": sum(
            int(row["target_covalent_connection_count"]) for row in rows
        ),
        "metal_context_connection_count": sum(
            int(row["metal_context_connection_count"]) for row in rows
        ),
    }


def _check_summary(
    summary: Mapping[str, Any],
    rows: list[dict[str, str]],
    snapshot: Mapping[str, Any],
) -> None:
    fixed = {
        "schema_version": "covapie_ei3_completed_decision_ingestion_summary_v1",
        "stage": "EI3_COMPLETED_DECISION_INGESTION_V1",
        "artifact_role": "COUNTS_COMPUTED_FROM_EXACT3_AVAILABILITY_METADATA",
        "review_unit_id": UNIT_ID,
    }
    for key, expected in fixed.items():
        actual = summary.get(key)
        if actual != expected:
            fail(
                "SUMMARY_FIELD_MISMATCH:"
                + key
                + ":actual="
                + _matrix_value(actual)
                + ":expected="
                + _matrix_value(expected)
            )
    for key, expected in _computed_summary_counts(rows, snapshot).items():
        actual = summary.get(key)
        if actual != expected:
            fail(
                "MATRIX_SUMMARY_COUNT_MISMATCH:"
                + key
                + ":actual="
                + _matrix_value(actual)
                + ":expected="
                + _matrix_value(expected)
            )


def _check_manifest(
    repo_root: Path, manifest: Mapping[str, Any], artifacts: Mapping[Path, bytes],
    matrix_header: tuple[str, ...],
) -> None:
    expected_root = {
        "schema_version": "covapie_ei3_completed_decision_ingestion_manifest_v1",
        "stage": "EI3_COMPLETED_DECISION_INGESTION_V1",
        "baseline_commit": BASELINE, "active_source_binding_count": 9,
        "formal_internal_source_binding_count": 10,
        "duplicate_source_binding_identity_count": 0,
    }
    for key, value in expected_root.items():
        if manifest.get(key) != value:
            fail("MANIFEST_ROOT_DRIFT:" + key)
    serialization = manifest.get("serialization_contract")
    if (
        type(serialization) is not dict
        or tuple(serialization.get("csv_header", [])) != MATRIX_HEADER
        or serialization.get("csv_column_count") != 81
        or tuple(serialization.get("csv_column_types", [])) != MATRIX_COLUMN_TYPES
        or serialization.get("encoding") != "UTF-8"
        or serialization.get("line_endings") != "LF"
        or serialization.get("single_terminal_LF") is not True
        or serialization.get("json_serialization") != "canonical_compact_json"
        or serialization.get("nullable_json_literal") != "null"
        or matrix_header != MATRIX_HEADER
    ):
        fail("MANIFEST_SERIALIZATION_DRIFT")
    candidates = manifest.get("candidate_source_bindings")
    if type(candidates) is not list or [row.get("path") for row in candidates] != [SOURCE.as_posix(), CHECKER.as_posix(), TEST.as_posix()]:
        fail("MANIFEST_CANDIDATE_BINDINGS_DRIFT")
    for row, relative in zip(candidates, (SOURCE, CHECKER, TEST), strict=True):
        payload = (repo_root / relative).read_bytes()
        if row.get("byte_count") != len(payload) or row.get("SHA256") != sha256(payload):
            fail("MANIFEST_CANDIDATE_IDENTITY_DRIFT:" + relative.as_posix())
    outputs = manifest.get("output_artifact_bindings_excluding_manifest_self")
    expected_paths = [SNAPSHOT, MATRIX, SUMMARY]
    if type(outputs) is not list or [row.get("path") for row in outputs] != [path.as_posix() for path in expected_paths]:
        fail("MANIFEST_OUTPUT_BINDINGS_DRIFT")
    for row, relative in zip(outputs, expected_paths, strict=True):
        payload = artifacts[relative]
        if row.get("byte_count") != len(payload) or row.get("SHA256") != sha256(payload):
            fail("MANIFEST_OUTPUT_IDENTITY_DRIFT:" + relative.name)
    if manifest.get("output_inventory", {}).get("manifest_self_SHA256_recorded") is not False:
        fail("MANIFEST_SELF_HASH_RECORDED")
    encoded = json.dumps(manifest, sort_keys=True).lower()
    if any(token in encoded for token in ("timestamp", "hostname", '"pid"', "/tmp/")):
        fail("MANIFEST_DYNAMIC_METADATA_PRESENT")


def _compare_bytes(
    actual: Mapping[Path, bytes], expected: Mapping[Path, bytes], token: str
) -> None:
    exact4 = {SNAPSHOT, MATRIX, SUMMARY, MANIFEST}
    if type(actual) is not dict or type(expected) is not dict:
        fail(token + ":MAPPING_TYPE_INVALID")
    if set(actual) != exact4 or set(expected) != exact4:
        fail(token + ":INVENTORY_NOT_EXACT4")
    if any(type(payload) is not bytes for payload in (*actual.values(), *expected.values())):
        fail(token + ":PAYLOAD_TYPE_INVALID")
    for path in (SNAPSHOT, MATRIX, SUMMARY, MANIFEST):
        if actual[path] != expected[path]:
            fail(token + ":" + path.name)


def _raw_comparator_probe(
    artifacts: Mapping[Path, bytes],
    expected_canonical: Mapping[Path, bytes] | None = None,
    comparator: Callable[
        [Mapping[Path, bytes], Mapping[Path, bytes], str], None
    ]
    | None = None,
) -> bool:
    if expected_canonical is None:
        snapshot = strict_json(artifacts[SNAPSHOT], "RAW_PROBE_SNAPSHOT")
        header, rows = parse_csv(artifacts[MATRIX], "RAW_PROBE_MATRIX")
        summary = strict_json(artifacts[SUMMARY], "RAW_PROBE_SUMMARY")
        manifest = strict_json(artifacts[MANIFEST], "RAW_PROBE_MANIFEST")
        expected_canonical = {
            SNAPSHOT: _canonical_json_bytes(snapshot),
            MATRIX: _canonical_csv_bytes(header, rows),
            SUMMARY: _canonical_json_bytes(summary),
            MANIFEST: _canonical_json_bytes(manifest),
        }
    active_comparator = _compare_bytes if comparator is None else comparator
    corrupted = dict(artifacts)
    corrupted[SUMMARY] = corrupted[SUMMARY][:-1] + b" \n"
    try:
        active_comparator(
            corrupted, expected_canonical, "RAW_BYTE_NEGATIVE_PROBE"
        )
    except CheckError as error:
        if str(error) == ERROR_PREFIX + ":RAW_BYTE_NEGATIVE_PROBE:" + SUMMARY.name:
            return True
        raise
    fail("RAW_COMPARATOR_NOOP_CONTROL_DID_NOT_FAIL")


def _noop_comparator_control_probe(
    artifacts: Mapping[Path, bytes], expected_canonical: Mapping[Path, bytes]
) -> bool:
    try:
        _raw_comparator_probe(
            artifacts,
            expected_canonical,
            comparator=lambda _actual, _expected, _token: None,
        )
    except CheckError as error:
        if str(error) == ERROR_PREFIX + ":RAW_COMPARATOR_NOOP_CONTROL_DID_NOT_FAIL":
            return True
        raise
    fail("NOOP_COMPARATOR_CONTROL_UNEXPECTEDLY_PASSED")


def independently_check_artifacts(
    repo_root: Path,
    artifacts: Mapping[Path, bytes] | None = None,
    *,
    run_raw_probe: bool = True,
) -> dict[str, object]:
    values = dict(artifacts) if artifacts is not None else _read_artifacts(repo_root)
    if set(values) != {SNAPSHOT, MATRIX, SUMMARY, MANIFEST}:
        fail("ARTIFACT_MAPPING_NOT_EXACT4")
    snapshot = strict_json(values[SNAPSHOT], "SNAPSHOT")
    header, rows = parse_csv(values[MATRIX], "MATRIX")
    summary = strict_json(values[SUMMARY], "SUMMARY")
    manifest = strict_json(values[MANIFEST], "MANIFEST")
    _check_snapshot(snapshot)
    expected_rows = _trusted_matrix_projection(repo_root, snapshot)
    _check_matrix(header, rows, expected_rows)
    _check_summary(summary, rows, snapshot)
    _check_manifest(repo_root, manifest, values, header)
    expected_canonical = {
        SNAPSHOT: _canonical_json_bytes(snapshot),
        MATRIX: _canonical_csv_bytes(MATRIX_HEADER, rows),
        SUMMARY: _canonical_json_bytes(summary),
        MANIFEST: _canonical_json_bytes(manifest),
    }
    _compare_bytes(
        values,
        expected_canonical,
        "INDEPENDENT_CANONICAL_BYTE_IDENTITY",
    )
    canonical_byte_identity = True
    if run_raw_probe:
        raw_probe_passed = _raw_comparator_probe(values, expected_canonical)
        noop_control_passed = _noop_comparator_control_probe(
            values, expected_canonical
        )
    else:
        raw_probe_passed = False
        noop_control_passed = False
    return {
        "artifact_count": 4, "event_count": 3, "matrix_column_count": len(header),
        "generic_exact11_fact_count": 3, "generic_exact11_field_count": 11,
        "semantic_check_path_exercised": True,
        "matrix_dispositions_source_bound": True,
        "matrix_snapshot_summary_consistent": True,
        "independent_canonical_byte_identity": canonical_byte_identity,
        "normal_checker_byte_path_uses_shared_comparator": canonical_byte_identity,
        "raw_byte_comparator_probe": raw_probe_passed,
        "raw_probe_uses_same_comparator": raw_probe_passed,
        "raw_byte_noop_comparator_would_fail_probe": noop_control_passed,
    }


def _matrix_bytes(rows: list[dict[str, str]]) -> bytes:
    return _canonical_csv_bytes(MATRIX_HEADER, rows)


def _with_matrix_and_synchronized_manifest(
    artifacts: Mapping[Path, bytes], rows: list[dict[str, str]]
) -> dict[Path, bytes]:
    changed = dict(artifacts)
    matrix_payload = _matrix_bytes(rows)
    changed[MATRIX] = matrix_payload
    manifest = strict_json(changed[MANIFEST], "MATRIX_PROBE_MANIFEST")
    matches = [
        record
        for record in manifest["output_artifact_bindings_excluding_manifest_self"]
        if record.get("path") == MATRIX.as_posix()
    ]
    if len(matches) != 1:
        fail("MATRIX_PROBE_MANIFEST_BINDING_NOT_EXACT1")
    matches[0]["byte_count"] = len(matrix_payload)
    matches[0]["SHA256"] = sha256(matrix_payload)
    changed[MANIFEST] = _canonical_json_bytes(manifest)
    return changed


def _matrix_semantic_negative_probes(
    repo_root: Path, artifacts: Mapping[Path, bytes]
) -> tuple[str, ...]:
    header, base_rows = parse_csv(artifacts[MATRIX], "MATRIX_SEMANTIC_PROBE_BASE")
    if header != MATRIX_HEADER:
        fail("MATRIX_SEMANTIC_PROBE_BASE_HEADER_DRIFT")
    cases = (
        ("chemistry_disposition", "NEGATIVE", "POSITIVE"),
        ("normalized_task_relevance_disposition", "RELEVANT", "NOT_RELEVANT"),
        ("training_disposition", "INCLUDE", "NOT_APPLICABLE"),
        ("accurate_PRE_required_before_training_feature_contract", "true", "false"),
        ("D4_formally_answered", "false", "true"),
        ("review_unit_id", "WRONG_UNIT", UNIT_ID),
        ("source_observed_pair", "SG:WRONG", "SG:C1"),
    )
    passed: list[str] = []
    for field, bad_value, expected_value in cases:
        rows = [dict(row) for row in base_rows]
        rows[0][field] = bad_value
        changed = _with_matrix_and_synchronized_manifest(artifacts, rows)
        expected_error = (
            ERROR_PREFIX
            + ":MATRIX_FIELD_MISMATCH:"
            + EVENT_IDS[0]
            + ":"
            + field
            + ":actual="
            + _matrix_value(bad_value)
            + ":expected="
            + _matrix_value(expected_value)
        )
        try:
            independently_check_artifacts(repo_root, changed, run_raw_probe=False)
        except CheckError as error:
            if str(error) != expected_error:
                raise
            passed.append(field)
            continue
        fail("MATRIX_SEMANTIC_PROBE_DID_NOT_FAIL:" + field)
    return tuple(passed)


def _semantic_negative_probe(repo_root: Path, artifacts: Mapping[Path, bytes]) -> bool:
    mutated = dict(artifacts)
    snapshot = strict_json(mutated[SNAPSHOT], "PROBE_SNAPSHOT")
    snapshot["events"][0]["human_review_completed"] = False
    mutated[SNAPSHOT] = (
        json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    try:
        independently_check_artifacts(repo_root, mutated, run_raw_probe=False)
    except CheckError as error:
        if str(error) == ERROR_PREFIX + ":SNAPSHOT_EVENT_DRIFT:5ARB:human_review_completed":
            return True
        raise
    fail("SEMANTIC_NEGATIVE_PROBE_DID_NOT_FAIL")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sources = independently_check_sources(repo_root)
    artifacts = _read_artifacts(repo_root)
    checked = independently_check_artifacts(repo_root, artifacts)
    semantic_probe = _semantic_negative_probe(repo_root, artifacts)
    matrix_semantic_probes = _matrix_semantic_negative_probes(
        repo_root, artifacts
    )
    lifecycle = check_git_lifecycle(repo_root)
    report = {
        "status": "PASS", "operation": "CHECK", **sources, **checked,
        "semantic_negative_probe": semantic_probe,
        "matrix_semantic_negative_probe_count": len(matrix_semantic_probes),
        "matrix_semantic_negative_probe_fields": list(matrix_semantic_probes),
        "hash_consistent_semantic_tamper_rejected": len(matrix_semantic_probes) == 7,
        "git_lifecycle": lifecycle,
        "formal_source_D2": "OUT_OF_DOMAIN", "normalized_task_relevance": "NOT_RELEVANT",
        "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "chemistry_disposition": "POSITIVE", "negative_chemistry": False,
        "training_disposition": "NOT_APPLICABLE", "human_training_excluded": False,
        "future_training_admission_candidate": False, "human_review_completed": True,
        "pair_sample_authority": True, "covalent_and_metal_context_distinguished": True,
        "D4_formally_answered": True, "D5_formally_answered": True,
        "role_partition_sample_authoritative": False,
        "task_applicability_sample_authoritative": False,
        "structurally_applicable_task_ids": None, "runtime_API_called": False,
        "rich_fields_leaked": False, "task_label_authority": False,
        "event_task_label_rows_materialized": False, "mask_tensor_targets_created": False,
        "formal_training_admitted": False, "ready_for_training": False,
        "training_started": False,
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    print("COVAPIE_EI3_COMPLETED_DECISION_INGESTION_V1_CHECK_PASS=true")
    print("FORMAL_SOURCE_D2=OUT_OF_DOMAIN")
    print("NORMALIZED_TASK_RELEVANCE=NOT_RELEVANT")
    print("COMPLETED_LANE=COMPLETED_TASK_DOMAIN_NEGATIVE")
    print("LEGACY_COMPLETED_REVIEW_STATUS=COMPLETED_HUMAN_NEGATIVE")
    print("READY_FOR_TRAINING=false")
    print("TRAINING_STARTED=false")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckError as error:
        print(str(error))
        raise SystemExit(1) from error
