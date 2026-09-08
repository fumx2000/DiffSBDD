#!/usr/bin/env python3
"""Independently check an ME7 ingestion Exact7 candidate or clean successor."""

from __future__ import annotations

import ast
import csv
from dataclasses import fields
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any, Mapping, NoReturn


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_me7_completed_decision_ingestion_and_task_label_availability_v1 as owner,
)


ERROR = "COVAPIE_ME7_INGESTION_CHECK_V1_ERROR"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_3CF0AB1696EEA129"
FORMAL_SCHEMA = "covapie_me7_exact3_formal_human_decision_v1"
FORMAL_SHA256 = "9641bee4a40c9501a494fdd76ee086b7c5dbc97130a176261575d3ad1e306407"
FORBIDDEN_SUFFIXES = (
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".pyc",
    ".tmp",
    ".part",
)
PROTECTED_PATHS = (
    "data/raw",
    "checkpoints",
    "equivariant_diffusion",
    "lightning_modules.py",
    "dataset.py",
    "data/prepare_crossdocked.py",
)
EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:3QVY:B:CYS:82-:SG:U:ME7:CAE",
        "528",
        "3QVY",
        "covale4",
        "1.805",
        "1.804924",
        "0.000076",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:3QVY:C:CYS:82-:SG:O:ME7:CAE",
        "529",
        "3QVY",
        "covale7",
        "1.816",
        "1.816389",
        "0.000389",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:3QVZ:A:CYS:82-:SG:F:ME7:CAE",
        "531",
        "3QVZ",
        "covale1",
        "1.831",
        "1.831178",
        "0.000178",
    ),
)
EVENT_IDS = tuple(row[0] for row in EVENTS)
CONTEXT_EVENTS = (
    ("527", "COVAPIE_CYS_SG_EVENT_V1:3QVY:A:CYS:82-:SG:O:ME7:CAG"),
    ("530", "COVAPIE_CYS_SG_EVENT_V1:3QVY:D:CYS:82-:SG:U:ME7:CAH"),
    ("533", "COVAPIE_CYS_SG_EVENT_V1:3QVZ:C:CYS:82-:SG:F:ME7:CAH"),
)
CANONICAL_LONG_NAMES = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
GENERIC_FIELDS = (
    "canonical_event_id",
    "review_unit_id",
    "human_review_completed",
    "legacy_completed_review_status",
    "task_relevance_disposition",
    "chemistry_disposition",
    "training_disposition",
    "human_training_excluded",
    "source_decision_schema",
    "source_decision_sha256",
    "source_binding_path",
)

# path, namespace, bytes, SHA256
SOURCE_SPECS = (
    (
        "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
        "ME7_COVAPIE_BULK_REVIEW_UNIT_3CF0AB1696EEA129/formal-human-decision-v1/"
        "me7_formal_human_decision_v1.json",
        "project_parent_relative",
        13344,
        FORMAL_SHA256,
    ),
    (
        "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
        "ME7_COVAPIE_BULK_REVIEW_UNIT_3CF0AB1696EEA129/formal-human-decision-v1/"
        "validate_me7_formal_human_decision_v1.py",
        "project_parent_relative",
        52865,
        "67a68f9b1c14cb90591a6e377c4fc680cc816c53e138995adf0c1544eaf91009",
    ),
    (
        "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
        "ME7_COVAPIE_BULK_REVIEW_UNIT_3CF0AB1696EEA129/review-preparation-v1/"
        "me7_exact3_event_evidence_v1.csv",
        "project_parent_relative",
        2674,
        "94bf6660ce6458f93dd3ac6ff5e58648b3e5357fe4706b606af195c14f98f2e5",
    ),
    (
        "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
        "ME7_COVAPIE_BULK_REVIEW_UNIT_3CF0AB1696EEA129/review-preparation-v1/"
        "me7_graph_and_review_evidence_v1.json",
        "project_parent_relative",
        89828,
        "02861ec451e4dcddbdb00c8e4b22540b438308bfcfef50177f5624a64cb191e1",
    ),
    (
        "src/covalent_ext/covapie_source_binding_policy_v2.py",
        "repository_relative",
        3704,
        "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
    ),
    (
        "src/covalent_ext/"
        "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py",
        "repository_relative",
        67274,
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
    ),
    (
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
        "repository_relative",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_cumulative1000_current_global_readiness_census_with_pyr_v1/"
        "covapie_cumulative1000_current_global_readiness_census_with_pyr_v1.csv",
        "repository_relative",
        557958,
        "e1c2b9c465401f544fe91d2641e10274cc2dd489fbb0b9a4c197779f55f405e2",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1/"
        "covapie_bulk_cys_sg_priority_human_review_queue_v1.csv",
        "repository_relative",
        50116,
        "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2",
    ),
)


def fail(reason: str) -> NoReturn:
    raise RuntimeError(ERROR + ":" + reason)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        fail("GIT_COMMAND_FAILED:" + ":".join(args))
    return result.stdout.strip()


def is_ancestor(repo_root: Path, older: str, newer: str) -> bool:
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer),
        cwd=repo_root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode not in (0, 1):
        fail("GIT_ANCESTRY_CHECK_FAILED")
    return result.returncode == 0


def strict_json(payload: bytes, label: str) -> dict[str, Any]:
    if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload or b"\r" in payload:
        fail("JSON_TEXT_INVALID:" + label)

    def pairs_hook(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                fail("JSON_DUPLICATE_KEY:" + label + ":" + key)
            result[key] = value
        return result

    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=pairs_hook,
            parse_constant=lambda value: fail("JSON_NONFINITE:" + label + ":" + value),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(ERROR + ":JSON_INVALID:" + label) from error
    if type(value) is not dict:
        fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def parse_csv(payload: bytes, label: str) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        reader = csv.DictReader(
            io.StringIO(payload.decode("utf-8"), newline=""), strict=True
        )
        header = tuple(reader.fieldnames or ())
        if not header or len(header) != len(set(header)):
            fail("CSV_HEADER_DUPLICATE_OR_EMPTY:" + label)
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise RuntimeError(ERROR + ":CSV_INVALID:" + label) from error
    if any(None in row or set(row) != set(header) for row in rows):
        fail("CSV_WIDTH_INVALID:" + label)
    return header, rows


def expect_fields(mapping: object, expected: Mapping[str, object], reason: str) -> None:
    if type(mapping) is not dict:
        fail(reason + ":NOT_OBJECT")
    for key, value in expected.items():
        if key not in mapping:
            fail(reason + ":MISSING:" + key)
        if type(mapping[key]) is not type(value) or mapping[key] != value:
            fail(reason + ":" + key)


def file_record(repo_root: Path, relative: Path) -> dict[str, object]:
    path = repo_root / relative
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise RuntimeError(ERROR + ":FILE_READ_FAILED:" + relative.as_posix()) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        fail("FILE_NOT_REGULAR_NON_SYMLINK:" + relative.as_posix())
    if metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        fail("FILE_EXECUTABLE:" + relative.as_posix())
    if stat.S_IMODE(metadata.st_mode) not in (0o644, 0o664):
        fail("FILE_MODE_NOT_0644_OR_0664:" + relative.as_posix())
    if (
        len(payload) >= 1024 * 1024
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
        or b"\r" in payload
        or b"\x00" in payload
        or payload.startswith(b"\xef\xbb\xbf")
    ):
        fail("FILE_TEXT_HYGIENE_INVALID:" + relative.as_posix())
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(ERROR + ":FILE_UTF8_INVALID:" + relative.as_posix()) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        fail("FILE_TRAILING_WHITESPACE:" + relative.as_posix())
    return {
        "path": relative.as_posix(),
        "bytes": len(payload),
        "SHA256": sha256(payload),
        "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
        "class": "REGULAR_NON_SYMLINK_NON_EXECUTABLE",
    }


def parse_exact7_index_records(
    payload: str, expected_paths: tuple[str, ...]
) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for line in payload.splitlines():
        try:
            prefix, path = line.split("\t", 1)
            mode, object_id, stage = prefix.split()
        except ValueError as error:
            raise RuntimeError(ERROR + ":GIT_INDEX_RECORD_PARSE_FAILED") from error
        rows.append({"mode": mode, "object_id": object_id, "stage": stage, "path": path})
    if len(rows) != 7:
        fail("TRACKED_CLEAN_GIT_INDEX_RECORD_COUNT_NOT_EXACT7")
    paths = [row["path"] for row in rows]
    if len(paths) != len(set(paths)):
        fail("TRACKED_CLEAN_GIT_INDEX_DUPLICATE_PATH")
    if set(paths) != set(expected_paths):
        fail("TRACKED_CLEAN_GIT_INDEX_PATH_SET_DRIFT")
    if any(row["stage"] != "0" for row in rows):
        fail("TRACKED_CLEAN_GIT_INDEX_NONZERO_STAGE")
    if any(row["mode"] != "100644" for row in rows):
        fail("TRACKED_CLEAN_GIT_INDEX_MODE_NOT_100644")
    return tuple(rows)


def check_git_lifecycle(repo_root: Path) -> dict[str, object]:
    branch = git(repo_root, "branch", "--show-current")
    head = git(repo_root, "rev-parse", "HEAD")
    origin = git(repo_root, "rev-parse", "origin/main")
    if branch != "main":
        fail("BRANCH_NOT_MAIN")
    if not is_ancestor(repo_root, owner.BASELINE_COMMIT, head):
        fail("BASELINE_NOT_ANCESTOR_OF_HEAD")
    if not is_ancestor(repo_root, owner.BASELINE_COMMIT, origin):
        fail("BASELINE_NOT_ANCESTOR_OF_ORIGIN_MAIN")
    if not is_ancestor(repo_root, origin, head):
        fail("ORIGIN_MAIN_NOT_ANCESTOR_OF_HEAD")
    try:
        behind, ahead = (
            int(value)
            for value in git(
                repo_root,
                "rev-list",
                "--left-right",
                "--count",
                "origin/main...HEAD",
            ).split()
        )
    except ValueError as error:
        raise RuntimeError(ERROR + ":AHEAD_BEHIND_PARSE_FAILED") from error
    if behind != 0:
        fail("HEAD_BEHIND_ORIGIN_MAIN")
    modified = git(repo_root, "diff", "--name-only").splitlines()
    staged = git(repo_root, "diff", "--cached", "--name-only").splitlines()
    conflicts = git(repo_root, "ls-files", "-u").splitlines()
    untracked = git(repo_root, "ls-files", "--others", "--exclude-standard").splitlines()
    expected = tuple(path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS)
    expected_set = set(expected)
    if conflicts:
        fail("CONFLICTED_INDEX_PRESENT")
    if modified:
        fail("TRACKED_MODIFICATIONS_PRESENT")
    if staged:
        fail("STAGED_INDEX_NOT_EMPTY")
    if set(untracked) == expected_set and len(untracked) == 7:
        profile = CANDIDATE_UNTRACKED
        if (
            head != owner.BASELINE_COMMIT
            or origin != owner.BASELINE_COMMIT
            or ahead != 0
            or behind != 0
        ):
            fail("CANDIDATE_UNTRACKED_BASELINE_PROFILE_DRIFT")
        index_records: tuple[dict[str, str], ...] = ()
        index_mode_checked = False
    elif not untracked:
        profile = TRACKED_CLEAN
        tracked = set(git(repo_root, "ls-files", "--", *expected).splitlines())
        if tracked != expected_set:
            fail("TRACKED_CLEAN_EXACT7_NOT_TRACKED")
        index_records = parse_exact7_index_records(
            git(repo_root, "ls-files", "--stage", "--", *expected), expected
        )
        index_mode_checked = True
        changed = set(
            git(
                repo_root,
                "diff",
                "--name-only",
                owner.BASELINE_COMMIT + "..HEAD",
            ).splitlines()
        )
        if not expected_set.issubset(changed):
            fail("TRACKED_CLEAN_EXACT7_NOT_DESCENDED_FROM_BASELINE")
    else:
        fail("ORDINARY_UNTRACKED_NOT_EXACT7_OR_EMPTY")
    historical_changed = set(
        git(repo_root, "diff", "--name-only", owner.BASELINE_COMMIT + "..HEAD").splitlines()
    )
    protected_changed = {
        path
        for path in historical_changed
        if any(path == root or path.startswith(root + "/") for root in PROTECTED_PATHS)
    }
    if protected_changed:
        fail("PROTECTED_HISTORY_CHANGED")
    candidate_history = expected_set | historical_changed | set(untracked)
    if any(path.endswith(FORBIDDEN_SUFFIXES) for path in candidate_history):
        fail("FORBIDDEN_SUFFIX_IN_CANDIDATE_HISTORY")
    return {
        "profile": profile,
        "branch": branch,
        "HEAD": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "tracked_modification_count": 0,
        "staged_count": 0,
        "conflicted_count": 0,
        "ordinary_untracked_count": len(untracked),
        "ordinary_untracked_paths": untracked,
        "git_index_mode_checked": index_mode_checked,
        "git_index_record_count": len(index_records),
        "git_index_expected_mode": "100644" if index_mode_checked else None,
        "raw_changed_since_baseline_count": 0,
        "protected_source_changed_since_baseline_count": 0,
        "forbidden_candidate_file_count": 0,
    }


EVENT_EVIDENCE_HEADER = tuple(
    "scaleup_rank canonical_event_id review_unit_id pdb_id model_number "
    "protein_label_asym_id protein_auth_asym_id protein_label_comp_id "
    "protein_auth_comp_id protein_label_seq_id protein_auth_seq_id "
    "protein_insertion_code protein_atom_id protein_altloc protein_occupancy "
    "component_label_asym_id component_auth_asym_id component_label_comp_id "
    "component_auth_comp_id component_label_seq_id component_auth_seq_id "
    "component_insertion_code component_atom_id component_altloc "
    "component_occupancy connection_id connection_type connection_value_order "
    "protein_symmetry component_symmetry source_observed_pair "
    "explicit_covalent_evidence distance_only_event_inference_used "
    "reported_distance_angstrom recalculated_distance_angstrom "
    "absolute_difference_angstrom protein_x protein_y protein_z component_x "
    "component_y component_z source_datasets_json source_record_ids_json "
    "processing_pre_status pre_source_graph_count pre_source_graph_mapping_count "
    "pre_geometry_authoritative pre_geometry_training_target_available "
    "post_geometry_source_evidence_available post_geometry_sample_authoritative "
    "post_geometry_training_target_available target_event human_selected"
    .split()
)
EXPECTED_MATRIX_HEADER = tuple(
    "artifact_role canonical_event_id scaleup_rank review_unit_id pdb_id "
    "protein_label_asym_id component_label_asym_id component_auth_asym_id "
    "connection_id source_observed_pair reported_distance_angstrom "
    "recalculated_distance_angstrom absolute_difference_angstrom "
    "protein_coordinates_json component_coordinates_json source_datasets_json "
    "source_record_ids_json evidence_human_selected human_review_completed "
    "D4_formally_answered D5_formally_answered completed_lane "
    "legacy_completed_review_status source_formal_D1 chemistry_disposition "
    "negative_chemistry source_formal_D2 normalized_task_relevance_disposition "
    "task_domain_negative source_formal_D3 pair_sample_authority "
    "target_pair_is_only_attachment source_formal_D4 D4_source_proposal_field "
    "role_candidate_count selected_role_candidate_json role_profile_raw_json "
    "role_profile_derived_state warhead_atom_ids_json linker_atom_ids_json "
    "scaffold_atom_ids_json minimal_seed_json minimal_seed_atom_ids_json "
    "primary_anchor_json role_partition_sample_authoritative "
    "minimal_seed_sample_authoritative role_runtime_executed seed_runtime_executed "
    "source_formal_D5 structurally_applicable_task_ids_json "
    "task_applicability_sample_authoritative task_runtime_executed "
    "canonical_task_count B3_present sixth_task "
    "canonical_mask_structural_labels_available task_label_authority "
    "event_task_label_rows_materialized mask_tensor_targets_created "
    "source_formal_D6 training_disposition human_training_excluded "
    "future_training_admission_candidate formal_training_admitted "
    "training_materialization_allowed POST_source_evidence_available "
    "POST_sample_geometry_authority POST_geometry_training_authority "
    "PRE_source_graph_count PRE_source_mapping_count PRE_source_mapping_status "
    "PRE_mapping_auto_selected PRE_authority POST_to_PRE_copy PRE_zero_fill "
    "FEATURE_SEMANTICS_AUDIT_PERFORMED "
    "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING READY_FOR_TRAINING "
    "TRAINING_STARTED"
    .split()
)


def _source_path(repo_root: Path, relative: str, namespace: str) -> Path:
    if namespace == "repository_relative":
        return repo_root / relative
    if namespace == "project_parent_relative":
        return repo_root.parent / relative
    fail("SOURCE_NAMESPACE_INVALID:" + namespace)


def independently_check_sources(repo_root: Path) -> dict[str, object]:
    payloads: dict[str, bytes] = {}
    records = []
    for relative, namespace, expected_bytes, expected_sha in SOURCE_SPECS:
        path = _source_path(repo_root, relative, namespace)
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise RuntimeError(ERROR + ":SOURCE_READ_FAILED:" + relative) from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        ):
            fail("SOURCE_CLASS_INVALID:" + relative)
        if len(payload) != expected_bytes or sha256(payload) != expected_sha:
            fail("SOURCE_IDENTITY_DRIFT:" + relative)
        payloads[relative] = payload
        records.append(
            {
                "path": relative,
                "path_namespace": namespace,
                "byte_count": expected_bytes,
                "SHA256": expected_sha,
            }
        )
    identities = {
        (row["path_namespace"], row["path"], row["SHA256"]) for row in records
    }
    if len(records) != 9 or len(identities) != 9:
        fail("SOURCE_IDENTITIES_NOT_UNIQUE_EXACT9")

    formal = strict_json(payloads[SOURCE_SPECS[0][0]], "INDEPENDENT_FORMAL")
    expected_top = {
        "PRE_boundary",
        "approved_D1_D6",
        "authorization_record",
        "event_context_boundary",
        "frozen_candidate_binding",
        "non_created_authority",
        "operation_boundary",
        "output_inventory",
        "readiness",
        "record_role",
        "role_and_task_disposition",
        "sample_identity",
        "sample_level_authority",
        "schema_version",
        "source_bindings",
    }
    if set(formal) != expected_top:
        fail("FORMAL_TOP_LEVEL_FIELDS_DRIFT")
    expect_fields(
        formal,
        {
            "schema_version": FORMAL_SCHEMA,
            "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        },
        "FORMAL_ROOT_DRIFT",
    )
    expect_fields(
        formal["authorization_record"],
        {
            "approval_time": None,
            "approval_time_status": "NOT_PROVIDED_VERIFIABLY",
            "authorization_complete": True,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "machine_generated_human_authorization": False,
            "platform_identity_verification_claimed": False,
            "chat_backend_access_claimed": False,
            "electronic_signature_claimed": False,
            "two_independent_authenticated_people_claimed": False,
        },
        "FORMAL_AUTHORIZATION_DRIFT",
    )
    expect_fields(
        formal["frozen_candidate_binding"],
        {
            "SHA256": "5e0604a86961937ece43779673b0f0d15e60aecd40f0f037058c00d8380afcf6",
            "authorization_bound_to_exact_SHA256": (
                "5e0604a86961937ece43779673b0f0d15e60aecd40f0f037058c00d8380afcf6"
            ),
            "candidate_human_fields_remained_unset": True,
            "candidate_is_human_authority": False,
            "candidate_was_unsigned": True,
            "candidate_modified": False,
        },
        "FORMAL_CANDIDATE_BINDING_DRIFT",
    )
    expect_fields(
        formal["sample_identity"],
        {
            "canonical_target_event_ids": list(EVENT_IDS),
            "pdb_ids": ["3QVY", "3QVZ"],
            "ligand_component_id": "ME7",
            "review_unit_id": UNIT_ID,
            "scope": "CURRENT_ME7_EXACT3_TARGET_REVIEW_UNIT_ONLY",
            "target_event_count": 3,
            "target_scaleup_ranks": [528, 529, 531],
            "ligand_wide_authority": False,
            "cross_structure_authority": False,
        },
        "FORMAL_SAMPLE_IDENTITY_DRIFT",
    )
    expect_fields(
        formal["event_context_boundary"],
        {
            "target_event_ids": list(EVENT_IDS),
            "target_scaleup_ranks": [528, 529, 531],
            "context_only_scaleup_ranks": [527, 530, 533],
            "context_only_event_count": 3,
            "context_merged_into_target_exact3": False,
            "context_only_events_received_formal_decisions": False,
            "target_pair_is_only_attachment_for_component_instance": False,
        },
        "FORMAL_CONTEXT_BOUNDARY_DRIFT",
    )
    decisions = formal["approved_D1_D6"]
    expected_decisions = {
        "D1_observation_record_judgment": {
            "decision": "POSITIVE",
            "chemistry_positive": True,
            "human_answered": True,
            "human_approved": True,
        },
        "D2_project_domain_relevance": {
            "decision": "OUT_OF_DOMAIN",
            "chemistry_negative": False,
            "chemistry_positive_is_preserved": True,
            "human_answered": True,
            "human_approved": True,
        },
        "D3_recorded_endpoint_confirmation": {
            "decision": "CONFIRM_OBSERVED_PAIR",
            "pair": "SG:CAE",
            "protein_atom": "SG",
            "component_atom": "CAE",
            "target_pair_is_only_attachment_for_component_instance": False,
            "human_answered": True,
            "human_approved": True,
        },
        "D4_role_partition_and_retained_information": {
            "decision": "CANNOT_DETERMINE",
            "formal_question_field": "D4_role_partition_and_retained_information",
            "source_proposal_field": "D4_role_partition_and_minimal_seed",
            "role_candidate_count": 0,
            "selected_candidate_id": None,
            "human_answered": True,
            "human_approved": True,
        },
        "D5_structural_task_applicability": {
            "decision": "NOT_DETERMINABLE",
            "task_ids": None,
            "human_answered": True,
            "human_approved": True,
        },
        "D6_later_use_disposition": {
            "decision": "NOT_APPLICABLE",
            "chemistry_negative": False,
            "human_training_excluded": False,
            "future_training_admission_candidate": False,
            "formal_training_admitted": False,
            "human_answered": True,
            "human_approved": True,
        },
    }
    for key, expected in expected_decisions.items():
        expect_fields(decisions.get(key), expected, "FORMAL_DECISION_DRIFT:" + key)
    expect_fields(
        formal["sample_level_authority"],
        {
            "approved": True,
            "human_review_completed": True,
            "sample_chemistry_authority": True,
            "sample_task_domain_authority": True,
            "sample_pair_authority": True,
            "sample_D6_disposition_authority": True,
            "role_partition_sample_authoritative": False,
            "minimal_seed_sample_authoritative": False,
            "task_applicability_sample_authoritative": False,
        },
        "FORMAL_SAMPLE_AUTHORITY_DRIFT",
    )
    role = formal["role_and_task_disposition"]
    expect_fields(
        role,
        {
            "D4_formally_answered": True,
            "D5_formally_answered": True,
            "role_candidate_count": 0,
            "selected_candidate_id": None,
            "selected_role_candidate": None,
            "role_profile": None,
            "warhead_atom_ids": None,
            "linker_atom_ids": None,
            "scaffold_atom_ids": None,
            "minimal_seed": None,
            "minimal_seed_atom_ids": None,
            "primary_anchor": None,
            "applicable_task_ids": None,
            "role_runtime_executed": False,
            "task_runtime_executed": False,
            "canonical_v1_task_count": 5,
            "B3_present": True,
            "sixth_task_created": False,
        },
        "FORMAL_ROLE_TASK_NULL_STATE_DRIFT",
    )
    if [row["semantic_long_name"] for row in role["canonical_v1_tasks"]] != list(
        CANONICAL_LONG_NAMES
    ):
        fail("FORMAL_CANONICAL_TASK_LONG_NAMES_DRIFT")
    expect_fields(
        formal["non_created_authority"],
        {
            "TASK_LABEL_AUTHORITY": False,
            "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
            "MASK_TENSOR_TARGETS_CREATED": False,
            "PRE_authority": False,
            "POST_geometry_training_authority": False,
            "FORMAL_TRAINING_ADMITTED": False,
            "TRAINING_MATERIALIZATION_ALLOWED": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "FORMAL_NON_CREATED_AUTHORITY_DRIFT",
    )
    if type(formal["source_bindings"]) is not list or len(formal["source_bindings"]) != 10:
        fail("FORMAL_SOURCE_BINDING_COUNT_DRIFT")
    formal_binding_keys = {
        (row.get("relative_path"), row.get("bytes"), row.get("SHA256"))
        for row in formal["source_bindings"]
        if type(row) is dict
    }
    for expected in (
        ("review-preparation-v1/me7_exact3_event_evidence_v1.csv", 2674, SOURCE_SPECS[2][3]),
        ("review-preparation-v1/me7_graph_and_review_evidence_v1.json", 89828, SOURCE_SPECS[3][3]),
        (
            "human-decision-candidate-v1/me7_filled_unsigned_human_decision_candidate_v1.json",
            17668,
            "5e0604a86961937ece43779673b0f0d15e60aecd40f0f037058c00d8380afcf6",
        ),
    ):
        if expected not in formal_binding_keys:
            fail("FORMAL_SOURCE_BINDING_SEMANTIC_DRIFT")

    event_header, event_rows = parse_csv(
        payloads[SOURCE_SPECS[2][0]], "INDEPENDENT_EVENT_EVIDENCE"
    )
    if event_header != EVENT_EVIDENCE_HEADER or len(event_rows) != 3:
        fail("EVENT_EVIDENCE_HEADER_OR_EXACT3_DRIFT")
    for row, expected in zip(event_rows, EVENTS, strict=True):
        event_id, rank, pdb_id, connection, reported, recalculated, difference = expected
        expected_cells = {
            "canonical_event_id": event_id,
            "scaleup_rank": rank,
            "review_unit_id": UNIT_ID,
            "pdb_id": pdb_id,
            "ligand_component_id" if "ligand_component_id" in row else "component_label_comp_id": "ME7",
            "protein_atom_id": "SG",
            "component_atom_id": "CAE",
            "connection_id": connection,
            "source_observed_pair": "SG:CAE",
            "reported_distance_angstrom": reported,
            "recalculated_distance_angstrom": recalculated,
            "absolute_difference_angstrom": difference,
            "explicit_covalent_evidence": "true",
            "distance_only_event_inference_used": "false",
            "processing_pre_status": "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS",
            "pre_source_graph_count": "1",
            "pre_source_graph_mapping_count": "8",
            "pre_geometry_authoritative": "false",
            "post_geometry_source_evidence_available": "true",
            "post_geometry_sample_authoritative": "false",
            "target_event": "true",
            "human_selected": "false",
        }
        for key, value in expected_cells.items():
            if row.get(key) != value:
                fail("EVENT_EVIDENCE_DRIFT:" + rank + ":" + key)
        if json.loads(row["source_datasets_json"]) != [
            "SOURCE_COVBINDERINPDB",
            "SOURCE_RCSB_PDB_DIRECT",
        ]:
            fail("EVENT_SOURCE_DATASETS_DRIFT:" + rank)

    graph = strict_json(payloads[SOURCE_SPECS[3][0]], "INDEPENDENT_GRAPH")
    expect_fields(
        graph,
        {
            "schema_version": "covapie_me7_graph_and_review_evidence_v1",
            "artifact_role": "FROZEN_EVIDENCE_REVIEW_AID_NOT_HUMAN_AUTHORITY",
            "review_unit_id": UNIT_ID,
        },
        "GRAPH_ROOT_DRIFT",
    )
    target_events = graph.get("target_events")
    context_events = graph.get("additional_instance_connection_context")
    if type(target_events) is not list or len(target_events) != 3:
        fail("GRAPH_TARGET_EVENTS_NOT_EXACT3")
    if type(context_events) is not list or len(context_events) != 3:
        fail("GRAPH_CONTEXT_EVENTS_NOT_EXACT3")
    if [row["canonical_event_id"] for row in target_events] != list(EVENT_IDS):
        fail("GRAPH_TARGET_EVENT_IDS_DRIFT")
    if [(str(row["scaleup_rank"]), row["canonical_event_id"]) for row in context_events] != list(
        CONTEXT_EVENTS
    ):
        fail("GRAPH_CONTEXT_EVENT_IDS_DRIFT")
    if any(
        row.get("target_event") is not True
        or row.get("supporting_context_only") is not False
        or row.get("human_selected") is not False
        or row.get("source_observed_pair") != "SG:CAE"
        or row["processing_observation"]["pre"].get("pre_source_graph_count") != 1
        or row["processing_observation"]["pre"].get("pre_source_graph_mapping_count") != 8
        or row["processing_observation"]["pre"].get("status")
        != "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS"
        for row in target_events
    ):
        fail("GRAPH_TARGET_EVIDENCE_DRIFT")
    if any(
        row.get("target_event") is not False
        or row.get("supporting_context_only") is not True
        for row in context_events
    ):
        fail("GRAPH_CONTEXT_BOUNDARY_DRIFT")
    exact5 = graph.get("canonical_Exact5")
    expect_fields(
        exact5,
        {
            "task_count": 5,
            "B3_present": True,
            "sixth_task_present": False,
            "sample_applicable_task_ids": None,
        },
        "GRAPH_EXACT5_DRIFT",
    )
    if [row["semantic_long_name"] for row in exact5["tasks"]] != list(CANONICAL_LONG_NAMES):
        fail("GRAPH_EXACT5_LONG_NAMES_DRIFT")

    canonical_tree = ast.parse(payloads[SOURCE_SPECS[5][0]].decode("utf-8"))
    assignment = next(
        node for node in canonical_tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "CANONICAL_TASKS" for target in node.targets)
    )
    literal_tasks = ast.literal_eval(assignment.value)
    if len(literal_tasks) != 5 or [row[1] for row in literal_tasks] != list(CANONICAL_LONG_NAMES):
        fail("PUBLISHED_CANONICAL_TASK_OWNER_DRIFT")

    owner_tree = ast.parse((repo_root / owner.SOURCE_RELATIVE).read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(owner_tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    if "subprocess" in imports or "runpy" in imports:
        fail("PRODUCTION_FORMAL_VALIDATOR_EXECUTABLE_DEPENDENCY")

    binding = generic.SourceBinding(
        source_path=SOURCE_SPECS[0][0],
        path_namespace="repository_parent_relative",
        byte_count=13344,
        sha256=FORMAL_SHA256,
        schema_version=FORMAL_SCHEMA,
        review_unit_id=UNIT_ID,
    )
    generic._validate_source_binding(binding)
    facts = []
    for event_id in EVENT_IDS:
        fact = generic.NormalizedCompletedDecisionFact(
            canonical_event_id=event_id,
            review_unit_id=UNIT_ID,
            human_review_completed=True,
            legacy_completed_review_status="COMPLETED_HUMAN_NEGATIVE",
            task_relevance_disposition="NOT_RELEVANT",
            chemistry_disposition="POSITIVE",
            training_disposition="NOT_APPLICABLE",
            human_training_excluded=False,
            source_decision_schema=FORMAL_SCHEMA,
            source_decision_sha256=FORMAL_SHA256,
            source_binding_path=SOURCE_SPECS[0][0],
        )
        if tuple(field.name for field in fields(fact)) != GENERIC_FIELDS:
            fail("GENERIC_FACT_NOT_EXACT11")
        generic._validate_fact(fact, binding)
        facts.append(fact)
    source = generic.NormalizedDecisionSource(binding=binding, facts=tuple(facts))
    if len(source.facts) != 3:
        fail("GENERIC_SOURCE_NOT_EXACT3")

    census_header, census_rows = parse_csv(payloads[SOURCE_SPECS[7][0]], "CENSUS")
    if len(census_header) != 47 or len(census_rows) != 1000:
        fail("CURRENT_CENSUS_SCHEMA_OR_ROW_COUNT_DRIFT")
    census_targets = [row for row in census_rows if row.get("review_unit_id") == UNIT_ID]
    if len(census_targets) != 3 or [row["canonical_event_id"] for row in census_targets] != list(EVENT_IDS):
        fail("CURRENT_CENSUS_TARGET_EXACT3_DRIFT")
    for row in census_targets:
        for key, value in {
            "current_review_status": "CURRENTLY_UNREVIEWED",
            "human_review_completed": "false",
            "chemistry_disposition": "UNRESOLVED",
            "task_relevance_disposition": "UNRESOLVED",
            "training_use_disposition": "UNRESOLVED",
            "role_profile": "NOT_ESTABLISHED",
            "canonical_mask_structural_labels_available": "false",
            "structurally_applicable_task_ids_json": "null",
            "formal_training_admitted": "false",
        }.items():
            if row.get(key) != value:
                fail("CURRENT_CENSUS_TARGET_DRIFT:" + key)
    queue_header, queue_rows = parse_csv(payloads[SOURCE_SPECS[8][0]], "QUEUE")
    queue_targets = [row for row in queue_rows if row.get("review_unit_id") == UNIT_ID]
    if len(queue_header) != 17 or len(queue_rows) != 131 or len(queue_targets) != 1:
        fail("FROZEN_QUEUE_SCHEMA_OR_TARGET_DRIFT")
    expect_fields(
        queue_targets[0],
        {
            "priority_rank": "32",
            "event_count": "3",
            "canonical_event_ids_json": json.dumps(list(EVENT_IDS), separators=(",", ":")),
            "pdb_ids_json": '["3QVY","3QVZ"]',
            "ligand_component_ids_json": '["ME7"]',
            "human_decision_created": "false",
        },
        "FROZEN_QUEUE_TARGET_DRIFT",
    )
    return {
        "source_count": 9,
        "semantic_source_identity_count": 9,
        "source_records": records,
        "formal_json_independently_validated": True,
        "formal_validator_identity_only": True,
        "formal_validator_imported": False,
        "formal_validator_executed": False,
        "formal_validator_subprocessed": False,
        "event_evidence_header_validated": True,
        "graph_target_context_boundary_validated": True,
        "canonical_exact5_validated": True,
        "role_seed_task_runtime_executed": False,
        "generic_exact11_fact_count": 3,
        "current_census_ME7_pending": True,
        "frozen_queue_ME7_pending": True,
    }


def independently_check_artifacts(
    repo_root: Path, artifacts: Mapping[str, bytes]
) -> dict[str, object]:
    if set(artifacts) != set(owner.OUTPUT_FILENAMES):
        fail("ARTIFACT_INVENTORY_NOT_EXACT4")
    snapshot = strict_json(artifacts[owner.SNAPSHOT], "SNAPSHOT")
    summary = strict_json(artifacts[owner.SUMMARY], "SUMMARY")
    manifest = strict_json(artifacts[owner.MANIFEST], "MANIFEST")
    matrix_header, rows = parse_csv(artifacts[owner.MATRIX], "MATRIX")
    if matrix_header != EXPECTED_MATRIX_HEADER or len(rows) != 3:
        fail("MATRIX_HEADER_OR_EXACT3_DRIFT")
    if matrix_header != owner.MATRIX_HEADER:
        fail("MATRIX_OWNER_AND_INDEPENDENT_HEADER_DISAGREE")
    observed = [
        (
            row["canonical_event_id"],
            row["scaleup_rank"],
            row["pdb_id"],
            row["connection_id"],
            row["reported_distance_angstrom"],
            row["recalculated_distance_angstrom"],
            row["absolute_difference_angstrom"],
        )
        for row in rows
    ]
    if observed != list(EVENTS):
        fail("MATRIX_EVENT_IDENTITY_GEOMETRY_DRIFT")
    constant_cells = {
        "artifact_role": "TASK_LABEL_AVAILABILITY_METADATA_ONLY_NOT_LABEL_ROWS",
        "review_unit_id": UNIT_ID,
        "source_observed_pair": "SG:CAE",
        "evidence_human_selected": "false",
        "human_review_completed": "true",
        "D4_formally_answered": "true",
        "D5_formally_answered": "true",
        "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "source_formal_D1": "POSITIVE",
        "chemistry_disposition": "POSITIVE",
        "negative_chemistry": "false",
        "source_formal_D2": "OUT_OF_DOMAIN",
        "normalized_task_relevance_disposition": "NOT_RELEVANT",
        "task_domain_negative": "true",
        "source_formal_D3": "CONFIRM_OBSERVED_PAIR",
        "pair_sample_authority": "true",
        "target_pair_is_only_attachment": "false",
        "source_formal_D4": "CANNOT_DETERMINE",
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
        "source_formal_D5": "NOT_DETERMINABLE",
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
        "source_formal_D6": "NOT_APPLICABLE",
        "training_disposition": "NOT_APPLICABLE",
        "human_training_excluded": "false",
        "future_training_admission_candidate": "false",
        "formal_training_admitted": "false",
        "training_materialization_allowed": "false",
        "POST_source_evidence_available": "true",
        "POST_sample_geometry_authority": "false",
        "POST_geometry_training_authority": "false",
        "PRE_source_graph_count": "1",
        "PRE_source_mapping_count": "8",
        "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS",
        "PRE_mapping_auto_selected": "false",
        "PRE_authority": "false",
        "POST_to_PRE_copy": "false",
        "PRE_zero_fill": "false",
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": "false",
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": "true",
        "READY_FOR_TRAINING": "false",
        "TRAINING_STARTED": "false",
    }
    for row in rows:
        for key, value in constant_cells.items():
            if key not in row or row[key] != value:
                fail("MATRIX_HIGH_VALUE_CELL_DRIFT:" + key)
        for key in (
            "protein_coordinates_json",
            "component_coordinates_json",
            "source_datasets_json",
            "source_record_ids_json",
        ):
            parsed = json.loads(row[key])
            if type(parsed) is not list or not parsed:
                fail("MATRIX_OBSERVED_JSON_CELL_INVALID:" + key)

    expect_fields(
        snapshot,
        {
            "schema_version": "covapie_me7_completed_human_decision_snapshot_v1",
            "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
            "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
            "projection_of_frozen_formal_human_authority": True,
            "new_human_authority_created_by_ingestion": False,
        },
        "SNAPSHOT_ROOT_DRIFT",
    )
    expect_fields(
        snapshot["formal_human_authority"],
        {
            "approved": True,
            "human_review_completed": True,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "approval_time": None,
            "machine_generated_human_authorization": False,
            "platform_identity_verification_claimed": False,
            "authorization_bound_candidate_SHA256": (
                "5e0604a86961937ece43779673b0f0d15e60aecd40f0f037058c00d8380afcf6"
            ),
        },
        "SNAPSHOT_FORMAL_AUTHORITY_DRIFT",
    )
    normalization = snapshot.get("normalization_contract")
    expect_fields(
        normalization.get("task_relevance") if type(normalization) is dict else None,
        {
            "source_field": "D2_project_domain_relevance",
            "source_formal_value": "OUT_OF_DOMAIN",
            "normalized_value": "NOT_RELEVANT",
            "mapping": "OUT_OF_DOMAIN_TO_NOT_RELEVANT",
            "source_value_preserved": True,
        },
        "SNAPSHOT_D2_NORMALIZATION_DRIFT",
    )
    expect_fields(
        normalization.get("training_disposition") if type(normalization) is dict else None,
        {
            "source_field": "D6_later_use_disposition",
            "source_formal_value": "NOT_APPLICABLE",
            "normalized_value": "NOT_APPLICABLE",
            "mapping": "NOT_APPLICABLE_TO_NOT_APPLICABLE",
            "source_value_preserved": True,
        },
        "SNAPSHOT_D6_NORMALIZATION_DRIFT",
    )
    events = snapshot.get("events")
    if type(events) is not list or len(events) != 3:
        fail("SNAPSHOT_EVENTS_NOT_EXACT3")
    if [event["canonical_event_id"] for event in events] != list(EVENT_IDS):
        fail("SNAPSHOT_EVENT_IDS_DRIFT")
    for event in events:
        expect_fields(
            event,
            {
                "human_review_completed": True,
                "D4_formally_answered": True,
                "D5_formally_answered": True,
                "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
                "source_formal_D1": "POSITIVE",
                "chemistry_disposition": "POSITIVE",
                "negative_chemistry": False,
                "source_formal_D2": "OUT_OF_DOMAIN",
                "task_relevance_disposition": "NOT_RELEVANT",
                "task_domain_negative": True,
                "pair_sample_authority": True,
                "target_pair_is_only_attachment_for_component_instance": False,
                "source_formal_D4": "CANNOT_DETERMINE",
                "role_candidate_count": 0,
                "role_profile": None,
                "warhead_atom_ids": None,
                "linker_atom_ids": None,
                "scaffold_atom_ids": None,
                "minimal_seed": None,
                "minimal_seed_atom_ids": None,
                "primary_anchor": None,
                "role_partition_sample_authoritative": False,
                "minimal_seed_sample_authoritative": False,
                "source_formal_D5": "NOT_DETERMINABLE",
                "structurally_applicable_task_ids": None,
                "task_applicability_sample_authoritative": False,
                "canonical_mask_structural_labels_available": False,
                "role_runtime_executed": False,
                "seed_runtime_executed": False,
                "task_runtime_executed": False,
                "source_formal_D6": "NOT_APPLICABLE",
                "training_disposition": "NOT_APPLICABLE",
                "human_training_excluded": False,
                "future_training_admission_candidate": False,
                "formal_training_admitted": False,
                "training_materialization_allowed": False,
                "POST_geometry_training_authority": False,
                "PRE_authority": False,
                "READY_FOR_TRAINING": False,
                "TRAINING_STARTED": False,
            },
            "SNAPSHOT_EVENT_DRIFT",
        )
    context = snapshot.get("context_boundary")
    expect_fields(
        context,
        {
            "context_merged_into_target_exact3": False,
            "context_only_event_count": 3,
            "context_only_scaleup_ranks": [527, 530, 533],
            "context_only_events_received_formal_decisions": False,
        },
        "SNAPSHOT_CONTEXT_DRIFT",
    )
    if [(str(row["scaleup_rank"]), row["canonical_event_id"]) for row in context["context_only_records"]] != list(
        CONTEXT_EVENTS
    ):
        fail("SNAPSHOT_CONTEXT_RECORDS_DRIFT")
    null_state = snapshot.get("role_seed_and_task_null_state")
    expect_fields(
        null_state,
        {
            "D4_formally_answered": True,
            "D5_formally_answered": True,
            "selected_role_candidate": None,
            "role_profile": None,
            "role_profile_derived_state": "NOT_ESTABLISHED",
            "warhead_atom_ids": None,
            "linker_atom_ids": None,
            "scaffold_atom_ids": None,
            "minimal_seed": None,
            "minimal_seed_atom_ids": None,
            "primary_anchor": None,
            "structurally_applicable_task_ids": None,
            "role_partition_sample_authoritative": False,
            "minimal_seed_sample_authoritative": False,
            "task_applicability_sample_authoritative": False,
            "canonical_mask_structural_labels_available": False,
            "role_runtime_executed": False,
            "seed_runtime_executed": False,
            "task_runtime_executed": False,
        },
        "SNAPSHOT_NULL_STATE_DRIFT",
    )
    tasks = snapshot.get("canonical_task_contract")
    expect_fields(
        tasks,
        {
            "global_canonical_task_count": 5,
            "B3_present": True,
            "sixth_task": False,
            "role_profile": None,
            "sample_applicable_task_ids": None,
            "task_applicability_determined": False,
            "task_applicability_sample_authority": False,
            "canonical_mask_structural_labels_available": False,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
        },
        "SNAPSHOT_TASK_CONTRACT_DRIFT",
    )
    if [row["semantic_long_name"] for row in tasks["global_canonical_tasks"]] != list(
        CANONICAL_LONG_NAMES
    ):
        fail("SNAPSHOT_CANONICAL_TASK_LONG_NAMES_DRIFT")
    generic_block = snapshot.get("generic_Exact11_compatibility")
    expect_fields(
        generic_block,
        {
            "accepted_fact_count": 3,
            "generic_fact_field_count": 11,
            "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
            "rich_fields_leaked": False,
            "reconciliation_performed": False,
        },
        "SNAPSHOT_GENERIC_DRIFT",
    )
    facts_payload = generic_block.get("facts")
    if type(facts_payload) is not list or len(facts_payload) != 3:
        fail("GENERIC_FACTS_NOT_EXACT3")
    binding = generic.SourceBinding(
        source_path=SOURCE_SPECS[0][0],
        path_namespace="repository_parent_relative",
        byte_count=13344,
        sha256=FORMAL_SHA256,
        schema_version=FORMAL_SCHEMA,
        review_unit_id=UNIT_ID,
    )
    fact_objects = []
    for payload in facts_payload:
        if type(payload) is not dict or set(payload) != set(GENERIC_FIELDS):
            fail("GENERIC_FACT_NOT_EXACT11")
        fact = generic.NormalizedCompletedDecisionFact(**payload)
        if tuple(field.name for field in fields(fact)) != GENERIC_FIELDS:
            fail("GENERIC_DATACLASS_NOT_EXACT11")
        generic._validate_fact(fact, binding)
        fact_objects.append(fact)
    source = generic.NormalizedDecisionSource(binding=binding, facts=tuple(fact_objects))
    if len(source.facts) != 3:
        fail("GENERIC_SOURCE_NOT_EXACT3")

    expected_summary = {
        "event_count": 3,
        "review_unit_count": 1,
        "human_review_completed_count": 3,
        "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "source_formal_D2": "OUT_OF_DOMAIN",
        "normalized_task_relevance_disposition": "NOT_RELEVANT",
        "source_formal_D6": "NOT_APPLICABLE",
        "normalized_training_disposition": "NOT_APPLICABLE",
        "chemistry_positive_count": 3,
        "negative_chemistry_count": 0,
        "task_not_relevant_count": 3,
        "task_domain_negative_count": 3,
        "training_not_applicable_count": 3,
        "human_training_excluded_count": 0,
        "future_training_admission_candidate_count": 0,
        "pair_sample_authority_count": 3,
        "role_partition_sample_authority_count": 0,
        "minimal_seed_sample_authority_count": 0,
        "task_applicability_sample_authority_count": 0,
        "canonical_structural_label_available_count": 0,
        "generic_exact11_fact_count": 3,
        "formal_training_admitted_count": 0,
    }
    expect_fields(summary, expected_summary, "SUMMARY_DRIFT")

    expect_fields(
        manifest,
        {
            "candidate_publication_file_count": 7,
            "candidate_publication_paths": [
                path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS
            ],
            "output_artifact_count": 4,
            "output_paths": [path.as_posix() for path in owner.OUTPUT_RELATIVE_PATHS],
            "active_source_binding_count": 9,
            "semantic_source_identity_count": 9,
            "duplicate_source_binding_identity_count": 0,
            "formal_validator_provenance_identity_only": True,
            "formal_validator_imported": False,
            "formal_validator_executed_by_production": False,
            "formal_validator_subprocessed_by_production": False,
            "manifest_self_SHA256_recorded": False,
            "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
            "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
        },
        "MANIFEST_DRIFT",
    )
    matrix_contract = manifest.get("matrix_contract")
    expect_fields(
        matrix_contract,
        {
            "header_frozen": True,
            "header": list(EXPECTED_MATRIX_HEADER),
            "column_count": len(EXPECTED_MATRIX_HEADER),
            "boolean_serialization": "lowercase_true_false",
            "json_serialization": "canonical_compact_json",
            "null_json_serialization": "null",
            "nullable_json_empty_string_forbidden": True,
            "rows_are_availability_metadata_not_event_task_label_rows": True,
        },
        "MANIFEST_MATRIX_CONTRACT_DRIFT",
    )
    active = manifest.get("active_source_bindings")
    if type(active) is not list or len(active) != 9:
        fail("MANIFEST_ACTIVE_BINDINGS_NOT_EXACT9")
    expected_source_keys = {
        (path, namespace, size, digest)
        for path, namespace, size, digest in SOURCE_SPECS
    }
    actual_source_keys = {
        (
            row.get("path"),
            row.get("path_namespace"),
            row.get("byte_count"),
            row.get("SHA256"),
        )
        for row in active
    }
    if actual_source_keys != expected_source_keys:
        fail("MANIFEST_ACTIVE_SOURCE_IDENTITY_DRIFT")
    if len({row.get("semantic_source_identity") for row in active}) != 9:
        fail("MANIFEST_ACTIVE_SOURCE_DUPLICATE")
    candidate_records = manifest.get("candidate_source_bindings")
    if type(candidate_records) is not list or len(candidate_records) != 3:
        fail("MANIFEST_CANDIDATE_SOURCES_NOT_EXACT3")
    for record, relative in zip(
        candidate_records,
        (owner.SOURCE_RELATIVE, owner.CHECKER_RELATIVE, owner.TEST_RELATIVE),
        strict=True,
    ):
        live = (repo_root / relative).read_bytes()
        expect_fields(
            record,
            {
                "path": relative.as_posix(),
                "byte_count": len(live),
                "SHA256": sha256(live),
                "expected_executable_class": "NON_EXECUTABLE",
            },
            "MANIFEST_CANDIDATE_SOURCE_DRIFT",
        )
    output_records = manifest.get("output_artifact_bindings_excluding_manifest_self")
    if type(output_records) is not list or len(output_records) != 3:
        fail("MANIFEST_OUTPUT_BINDINGS_NOT_EXACT3")
    for record, name in zip(
        output_records,
        (owner.SNAPSHOT, owner.MATRIX, owner.SUMMARY),
        strict=True,
    ):
        expect_fields(
            record,
            {
                "path": (owner.OUTPUT_ROOT_RELATIVE / name).as_posix(),
                "byte_count": len(artifacts[name]),
                "SHA256": sha256(artifacts[name]),
            },
            "MANIFEST_OUTPUT_BINDING_DRIFT",
        )
    if any(owner.MANIFEST in str(record.get("path")) for record in output_records):
        fail("MANIFEST_SELF_SHA256_RECORDED")
    operation = manifest.get("operation_boundary")
    expect_fields(
        operation,
        {
            "reconciliation_performed": False,
            "census_refresh_performed": False,
            "queue_refresh_performed": False,
            "next_review_started": False,
            "event_task_label_row_materialization_performed": False,
            "mask_or_tensor_materialization_performed": False,
            "training_preparation_performed": False,
            "feature_semantics_audit_performed": False,
            "parameter_update_performed": False,
            "training_performed": False,
            "commit_performed": False,
            "push_performed": False,
        },
        "MANIFEST_OPERATION_DRIFT",
    )
    return {
        "event_count": 3,
        "matrix_column_count": len(EXPECTED_MATRIX_HEADER),
        "FORMAL_SOURCE_D2": "OUT_OF_DOMAIN",
        "NORMALIZED_TASK_RELEVANCE": "NOT_RELEVANT",
        "COMPLETED_LANE": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        "LEGACY_COMPLETED_REVIEW_STATUS": "COMPLETED_HUMAN_NEGATIVE",
        "CHEMISTRY_DISPOSITION": "POSITIVE",
        "TRAINING_DISPOSITION": "NOT_APPLICABLE",
        "HUMAN_TRAINING_EXCLUDED": False,
        "FUTURE_TRAINING_ADMISSION_CANDIDATE": False,
        "PAIR_SAMPLE_AUTHORITY": True,
        "TARGET_PAIR_IS_ONLY_ATTACHMENT": False,
        "ROLE_PARTITION_SAMPLE_AUTHORITATIVE": False,
        "TASK_APPLICABILITY_SAMPLE_AUTHORITATIVE": False,
        "STRUCTURALLY_APPLICABLE_TASK_IDS": None,
        "generic_exact11_fact_count": 3,
        "rich_fields_leaked_to_generic_facts": False,
        "independent_artifact_validation": True,
        "TASK_LABEL_AUTHORITY": False,
        "READY_FOR_TRAINING": False,
    }


def main() -> int:
    repo_root = REPO_ROOT
    lifecycle = check_git_lifecycle(repo_root)
    files = [file_record(repo_root, path) for path in owner.CANDIDATE_PUBLICATION_PATHS]
    sources = independently_check_sources(repo_root)
    artifacts = {
        name: (repo_root / owner.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in owner.OUTPUT_FILENAMES
    }
    independent = independently_check_artifacts(repo_root, artifacts)
    owner_result = owner.check_materialized_v1(repo_root)
    if owner_result.get("status") != "PASS":
        fail("OWNER_MATERIALIZED_CHECK_FAILED")
    result = {
        "COVAPIE_ME7_COMPLETED_DECISION_INGESTION_V1_PASS": True,
        "mode": "READ_ONLY_CHECK",
        "lifecycle": lifecycle,
        "files": files,
        "frozen_sources": sources,
        "independent_artifacts": independent,
        "owner_materialized_check": owner_result,
        "candidate_publication_file_count": 7,
        "output_artifact_count": 4,
        "FORMAL_SOURCE_D2": "OUT_OF_DOMAIN",
        "NORMALIZED_TASK_RELEVANCE": "NOT_RELEVANT",
        "COMPLETED_LANE": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        "LEGACY_COMPLETED_REVIEW_STATUS": "COMPLETED_HUMAN_NEGATIVE",
        "CHEMISTRY_DISPOSITION": "POSITIVE",
        "NEGATIVE_CHEMISTRY": False,
        "TRAINING_DISPOSITION": "NOT_APPLICABLE",
        "HUMAN_TRAINING_EXCLUDED": False,
        "FUTURE_TRAINING_ADMISSION_CANDIDATE": False,
        "HUMAN_REVIEW_COMPLETED": True,
        "PAIR_SAMPLE_AUTHORITY": True,
        "TARGET_PAIR_IS_ONLY_ATTACHMENT": False,
        "ROLE_PARTITION_SAMPLE_AUTHORITATIVE": False,
        "TASK_APPLICABILITY_SAMPLE_AUTHORITATIVE": False,
        "STRUCTURALLY_APPLICABLE_TASK_IDS": None,
        "GENERIC_EXACT11_FACT_COUNT": 3,
        "RICH_FIELDS_LEAKED": False,
        "TASK_LABEL_AUTHORITY": False,
        "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
        "MASK_TENSOR_TARGETS_CREATED": False,
        "EXACT7_CANDIDATE": lifecycle["profile"] == CANDIDATE_UNTRACKED,
        "PROJECTION_OF_FROZEN_FORMAL_HUMAN_AUTHORITY": True,
        "NEW_HUMAN_AUTHORITY_CREATED_BY_INGESTION": False,
        "RECONCILIATION_PERFORMED": False,
        "CENSUS_REFRESH_PERFORMED": False,
        "QUEUE_REFRESH_PERFORMED": False,
        "NEXT_REVIEW_STARTED": False,
        "FORMAL_TRAINING_ADMITTED": False,
        "TRAINING_MATERIALIZATION_ALLOWED": False,
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
        "STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK": True,
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
        "COMMIT_PERFORMED": False,
        "PUSH_PERFORMED": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
