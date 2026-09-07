#!/usr/bin/env python3
"""Independently check a PYR ingestion Exact7 candidate or clean successor."""

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
    covapie_pyr_completed_decision_ingestion_and_task_label_availability_v1 as owner,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_direct_attachment_optional_linker_runtime_v1 as runtime,
)


ERROR = "COVAPIE_PYR_INGESTION_CHECK_V1_ERROR"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
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
    ("COVAPIE_CYS_SG_EVENT_V1:1F8M:A:CYS:191-:SG:F:PYR:CB", "46", "1.780689", "1.781"),
    ("COVAPIE_CYS_SG_EVENT_V1:1F8M:B:CYS:191-:SG:H:PYR:CB", "47", "1.804200", "1.804"),
    ("COVAPIE_CYS_SG_EVENT_V1:1F8M:C:CYS:191-:SG:J:PYR:CB", "48", "1.787779", "1.788"),
    ("COVAPIE_CYS_SG_EVENT_V1:1F8M:D:CYS:191-:SG:L:PYR:CB", "49", "1.770279", "1.770"),
)
EVENT_IDS = tuple(row[0] for row in EVENTS)
W = ("CB", "CA", "O3")
L: tuple[str, ...] = ()
S = ("C", "O", "OXT")
BONDS = (
    ("C", "CA", "SING"),
    ("C", "O", "DOUB"),
    ("C", "OXT", "SING"),
    ("CA", "CB", "SING"),
    ("CA", "O3", "DOUB"),
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
        "PYR_COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4/formal-human-decision-v1/"
        "pyr_formal_human_decision_v1.json",
        "project_parent_relative",
        17975,
        "58736b2b9dda6078e2e57495d698af110b13f42eec6668cbdb358820dfb66e2d",
    ),
    (
        "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
        "PYR_COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4/formal-human-decision-v1/"
        "validate_pyr_formal_human_decision_v1.py",
        "project_parent_relative",
        75613,
        "003a1e6f85616bc8d5f255bd2333f0b61ee0144afaed32a3e7ba64114cdc543c",
    ),
    (
        "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
        "PYR_COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4/review-preparation-v1/"
        "pyr_exact4_event_evidence_v1.csv",
        "project_parent_relative",
        12452,
        "20292f757470d5b423c85a01067536bdc09099956ae3d3fc791dfe6aeb6da174",
    ),
    (
        "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
        "PYR_COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4/review-preparation-v1/"
        "pyr_graph_and_review_evidence_v1.json",
        "project_parent_relative",
        38379,
        "4697252320487560da6b239aef69d6855632f4d9e03b6f102ebe26a811e9ab28",
    ),
    (
        "covapie-state/bulk-multisource-cys-sg-v1/rcsb/ccd/PYR.cif",
        "project_parent_relative",
        6538,
        "cb79f4b4d65c6aab3d17e69acdf77bf46b79b2a9dd1457eea7ebc763f5ce88ad",
    ),
    (
        "src/covalent_ext/covapie_source_binding_policy_v2.py",
        "repository_relative",
        3704,
        "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
    ),
    (
        "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py",
        "repository_relative",
        37255,
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
    ),
    (
        "src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py",
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
        "src/covalent_ext/covapie_cumulative1000_current_global_readiness_census_with_6oa_v1.py",
        "repository_relative",
        77260,
        "7211246fc5bf52f1c47a903e4207f288bb828bcd1c746385d2aa1ddc4566822b",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_cumulative1000_current_global_readiness_census_with_6oa_v1/"
        "covapie_cumulative1000_current_global_readiness_census_with_6oa_v1.csv",
        "repository_relative",
        555850,
        "440bebc49aefd2a7b920063f5fca949f8f9930b76b6cca496bd8942b83d88a1b",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_cumulative1000_current_global_readiness_census_with_6oa_v1/"
        "covapie_cumulative1000_current_global_readiness_summary_with_6oa_v1.json",
        "repository_relative",
        22749,
        "f3bbdae930e4115e0bf0a51119ad3c5863064cf1fa68670d2ea1e610983dccd8",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_cumulative1000_current_global_readiness_census_with_6oa_v1/"
        "covapie_cumulative1000_current_global_readiness_manifest_with_6oa_v1.json",
        "repository_relative",
        85531,
        "e20eaddb68035f06cf910fc6aef9dbb87f10f260f62fad09e76afef11c44bf69",
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
    if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload:
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


def parse_csv(payload: bytes, label: str) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    except UnicodeDecodeError as error:
        raise RuntimeError(ERROR + ":CSV_INVALID:" + label) from error
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        fail("CSV_HEADER_INVALID:" + label)
    rows = list(reader)
    if any(None in row for row in rows):
        fail("CSV_WIDTH_INVALID:" + label)
    return rows


def expect_fields(mapping: object, expected: Mapping[str, object], reason: str) -> None:
    if type(mapping) is not dict:
        fail(reason + ":NOT_OBJECT")
    for key, value in expected.items():
        if type(mapping.get(key)) is not type(value) or mapping.get(key) != value:
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
    """Parse and validate exact stage-0 regular Git index records."""
    rows: list[dict[str, str]] = []
    for line in payload.splitlines():
        try:
            prefix, path = line.split("\t", 1)
            mode, object_id, stage = prefix.split()
        except ValueError as error:
            raise RuntimeError(ERROR + ":GIT_INDEX_RECORD_PARSE_FAILED") from error
        rows.append(
            {"mode": mode, "object_id": object_id, "stage": stage, "path": path}
        )
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
        index_mode_checked = False
        index_records: tuple[dict[str, str], ...] = ()
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
            git(repo_root, "diff", "--name-only", owner.BASELINE_COMMIT + "..HEAD").splitlines()
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


def independently_check_sources(repo_root: Path) -> dict[str, object]:
    payloads: dict[str, bytes] = {}
    records = []
    for relative, namespace, expected_bytes, expected_sha in SOURCE_SPECS:
        path = (
            repo_root / relative
            if namespace == "repository_relative"
            else repo_root.parent / relative
        )
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
    if len(records) != 13 or len(identities) != 13:
        fail("SOURCE_IDENTITIES_NOT_UNIQUE_EXACT13")

    formal = strict_json(payloads[SOURCE_SPECS[0][0]], "INDEPENDENT_FORMAL")
    expect_fields(
        formal,
        {
            "schema_version": "covapie_pyr_exact4_formal_human_decision_v1",
            "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        },
        "FORMAL_ROOT_DRIFT",
    )
    expect_fields(
        formal.get("authorization_record"),
        {
            "approval_time": None,
            "approval_time_status": "NOT_PROVIDED_VERIFIABLY",
            "authorization_complete": True,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "machine_generated_human_authorization": False,
            "platform_identity_verification_claimed": False,
            "independent_identity_authentication_claimed": False,
        },
        "FORMAL_AUTHORIZATION_DRIFT",
    )
    expect_fields(
        formal.get("frozen_candidate_binding"),
        {
            "SHA256": "db81fe86ac264fb9eed5ef5d1ac40eaffb0896b48429cfe7471b2d0669f56b69",
            "authorization_bound_to_exact_SHA256": (
                "db81fe86ac264fb9eed5ef5d1ac40eaffb0896b48429cfe7471b2d0669f56b69"
            ),
            "candidate_is_human_authority": False,
            "candidate_was_unsigned": True,
            "candidate_modified": False,
        },
        "FORMAL_CANDIDATE_BINDING_DRIFT",
    )
    expect_fields(
        formal.get("sample_identity"),
        {
            "PDB": "1F8M",
            "ligand_component_id": "PYR",
            "review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4",
            "scope": "CURRENT_PYR_EXACT4_SAMPLE_REVIEW_UNIT_ONLY",
            "event_count": 4,
            "canonical_event_ids": list(EVENT_IDS),
            "scaleup_event_ranks": [46, 47, 48, 49],
            "ligand_wide_authority": False,
            "cross_structure_authority": False,
        },
        "FORMAL_SAMPLE_IDENTITY_DRIFT",
    )
    decisions = formal.get("approved_D1_D6")
    if type(decisions) is not dict:
        fail("FORMAL_DECISIONS_MISSING")
    expected_decisions = {
        "D1_observed_covalent_chemistry": {
            "decision": "POSITIVE",
            "human_approved": True,
        },
        "D2_task_generation_domain_relevance": {
            "decision": "IN_DOMAIN",
            "human_approved": True,
        },
        "D3_reactive_atom_pair": {
            "decision": "CONFIRM_OBSERVED_PAIR",
            "pair": "SG:CB",
            "protein_atom": "SG",
            "component_atom": "CB",
            "human_approved": True,
        },
        "D4_role_partition_and_minimal_seed": {
            "decision": "PROVIDE_ROLE_PARTITION",
            "selected_candidate_id": (
                "CANDIDATE_A_DIRECT_ALPHA_KETOCARBOXYL_POST_CENTER"
            ),
            "human_approved": True,
        },
        "D5_structural_task_applicability": {
            "decision": "PROVIDE_APPLICABLE_TASK_IDS",
            "selected_task_ids": [0, 3, 4],
            "human_approved": True,
        },
        "D6_later_training_use_disposition": {
            "decision": "EXCLUDE",
            "human_training_excluded": True,
            "future_training_admission_candidate": False,
            "formal_training_admitted": False,
            "D6_is_chemistry_negative": False,
            "D6_is_out_of_domain": False,
        },
    }
    for key, expected in expected_decisions.items():
        expect_fields(decisions.get(key), expected, "FORMAL_DECISION_DRIFT:" + key)
    expect_fields(
        formal.get("selected_role_partition"),
        {
            "selected_candidate_id": (
                "CANDIDATE_A_DIRECT_ALPHA_KETOCARBOXYL_POST_CENTER"
            ),
            "selected_role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
            "selected_group_W": ["CB", "CA", "O3"],
            "selected_group_L": [],
            "selected_group_S": ["C", "O", "OXT"],
            "selected_boundary": "C--CA/SING",
            "human_selected": True,
        },
        "FORMAL_SELECTED_ROLE_DRIFT",
    )
    expect_fields(
        formal.get("selected_seed_and_anchor"),
        {
            "selected_seed_atom_ids": ["C", "O"],
            "selected_primary_anchor": "C",
            "human_selected": True,
        },
        "FORMAL_SELECTED_SEED_DRIFT",
    )
    expect_fields(
        formal.get("selected_task_ids"),
        {
            "selected_task_ids": [0, 3, 4],
            "runtime_returned_task_ids": [0, 3, 4],
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
        },
        "FORMAL_SELECTED_TASK_DRIFT",
    )
    exact5 = formal["selected_task_ids"]["canonical_V1_contract"]
    expect_fields(
        exact5,
        {
            "task_count": 5,
            "B3_present": True,
            "sixth_task": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
        },
        "FORMAL_EXACT5_DRIFT",
    )
    if [row["semantic_long_name"] for row in exact5["tasks"]] != [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]:
        fail("FORMAL_EXACT5_LONG_NAMES_DRIFT")
    expect_fields(
        formal.get("unselected_alternatives"),
        {
            "alternative_candidate_id": (
                "CANDIDATE_B_STRICT_TERMINAL_ELECTROPHILE_POST_CENTER"
            ),
            "alternative_human_selected": False,
            "alternative_formal_selected": False,
            "alternative_authority_created": False,
            "alternative_group_W": ["CB"],
            "alternative_group_L": ["CA", "O3"],
            "alternative_group_S": ["C", "O", "OXT"],
            "alternate_seed_proposal": ["C", "OXT"],
        },
        "FORMAL_ALTERNATIVE_DRIFT",
    )
    non_created = formal.get("non_created_authority")
    expect_fields(
        non_created,
        {
            "reusable_authority_created": False,
            "PRE_authority": False,
            "POST_geometry_training_authority": False,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
            "formal_training_admitted": False,
            "training_materialization_allowed": False,
            "parameter_update_authorization": False,
        },
        "FORMAL_NON_CREATED_AUTHORITY_DRIFT",
    )
    source_bindings = formal.get("source_bindings")
    if type(source_bindings) is not list or len(source_bindings) != 11:
        fail("FORMAL_SOURCE_BINDING_COUNT_DRIFT")
    bound_keys = {
        (row.get("relative_path"), row.get("bytes"), row.get("SHA256"))
        for row in source_bindings
        if type(row) is dict
    }
    for expected_key in (
        (
            "review-preparation-v1/pyr_exact4_event_evidence_v1.csv",
            12452,
            SOURCE_SPECS[2][3],
        ),
        (
            "review-preparation-v1/pyr_graph_and_review_evidence_v1.json",
            38379,
            SOURCE_SPECS[3][3],
        ),
        (
            "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py",
            37255,
            SOURCE_SPECS[6][3],
        ),
    ):
        if expected_key not in bound_keys:
            fail("FORMAL_SOURCE_BINDING_SEMANTIC_DRIFT")

    evidence = parse_csv(payloads[SOURCE_SPECS[2][0]], "INDEPENDENT_EVENT_EVIDENCE")
    if len(evidence) != 4:
        fail("EVENT_EVIDENCE_NOT_EXACT4")
    for row, expected in zip(evidence, EVENTS, strict=True):
        event_id, rank, exact, reported = expected
        expected_cells = {
            "canonical_event_id": event_id,
            "scaleup_event_rank": rank,
            "review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4",
            "pdb_id": "1F8M",
            "protein_reactive_atom": "SG",
            "ligand_component_id": "PYR",
            "ligand_reactive_atom": "CB",
            "exact_POST_distance_angstrom": exact,
            "reported_POST_distance_angstrom": reported,
            "explicit_covalent_evidence": "true",
            "distance_only_inference_used": "false",
            "supporting_adduct_graph_count": "1",
            "candidate_PRE_free_source_graph_count": "1",
            "source_PRE_mapping_count": "0",
            "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
            "final_PRE_reaction_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
            "human_review_completed": "false",
            "chemistry_disposition": "UNRESOLVED",
            "task_relevance_disposition": "UNRESOLVED",
            "training_use_disposition": "UNRESOLVED",
        }
        for key, value in expected_cells.items():
            if row.get(key) != value:
                fail("EVENT_EVIDENCE_DRIFT:" + rank + ":" + key)

    graph_doc = strict_json(payloads[SOURCE_SPECS[3][0]], "INDEPENDENT_GRAPH")
    graph = graph_doc.get("CCD_complete_heavy_atom_graph")
    expect_fields(
        graph,
        {
            "component_id": "PYR",
            "heavy_atom_count": 6,
            "heavy_heavy_bond_count": 5,
            "connected": True,
            "canonical_heavy_graph_SHA256": (
                "f72ed3b88a9e2191bd16667fcea942bb2738d1bf23dc71605c63079f197074ff"
            ),
        },
        "GRAPH_ROOT_DRIFT",
    )
    atoms = tuple(row["atom_id"] for row in graph["atom_inventory"])
    bonds = tuple(
        (row["atom_id_1"], row["atom_id_2"], row["bond_order"])
        for row in graph["bond_inventory"]
    )
    if atoms != ("C", "CA", "CB", "O", "O3", "OXT") or set(bonds) != set(BONDS):
        fail("GRAPH_INVENTORY_DRIFT")
    pre = graph_doc.get("PRE_evidence")
    expect_fields(
        pre,
        {
            "mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
            "reaction_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
            "POST_to_PRE_copy": False,
            "PRE_zero_fill": False,
            "PRE_topology_created": False,
            "PRE_coordinates_created": False,
        },
        "GRAPH_PRE_DRIFT",
    )
    audit = pre.get("event_audit")
    if type(audit) is not list or len(audit) != 4:
        fail("GRAPH_PRE_AUDIT_NOT_EXACT4")
    for row, event_id in zip(audit, EVENT_IDS, strict=True):
        expect_fields(
            row,
            {
                "canonical_event_id": event_id,
                "supporting_adduct_graph_count": 1,
                "candidate_PRE_free_source_graph_count": 1,
                "source_PRE_mapping_count": 0,
                "source_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
                "final_PRE_reaction_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
            },
            "GRAPH_PRE_EVENT_DRIFT",
        )

    role = runtime.validate_role_profile_v1(
        role_profile="DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        retained_heavy_atoms=atoms,
        scaffold_atoms=S,
        linker_atoms=L,
        warhead_atoms=W,
        reactive_atom_id="CB",
        direct_scaffold_warhead_boundaries=(("C", "CA", "SING"),),
        explicit_graph_bonds=bonds,
    )
    if not role.valid or role.reasons or role.direct_scaffold_warhead_boundary is None:
        fail("INDEPENDENT_RUNTIME_ROLE_FAILED")
    seed = runtime.validate_minimal_seed_for_role_profile_v1(
        role_profile="DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        seed_atoms=("C", "O"),
        scaffold_atoms=S,
        linker_atoms=L,
        warhead_atoms=W,
        explicit_graph_bonds=bonds,
        direct_boundary=role.direct_scaffold_warhead_boundary,
    )
    if (
        not seed.valid
        or seed.reasons
        or seed.primary_anchor_atom_id != "C"
        or runtime.valid_canonical_task_ids_for_role_profile_v1(
            "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        )
        != (0, 3, 4)
    ):
        fail("INDEPENDENT_RUNTIME_SEED_TASK_FAILED")

    binding = generic.SourceBinding(
        source_path=SOURCE_SPECS[0][0],
        path_namespace="repository_parent_relative",
        byte_count=17975,
        sha256=SOURCE_SPECS[0][3],
        schema_version="covapie_pyr_exact4_formal_human_decision_v1",
        review_unit_id="COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4",
    )
    generic._validate_source_binding(binding)
    facts = []
    for event_id in EVENT_IDS:
        fact = generic.NormalizedCompletedDecisionFact(
            canonical_event_id=event_id,
            review_unit_id=binding.review_unit_id,
            human_review_completed=True,
            legacy_completed_review_status="COMPLETED_HUMAN_POSITIVE",
            task_relevance_disposition="RELEVANT",
            chemistry_disposition="POSITIVE",
            training_disposition="EXCLUDE_FROM_TRAINING_ONLY",
            human_training_excluded=True,
            source_decision_schema=binding.schema_version,
            source_decision_sha256=binding.sha256,
            source_binding_path=binding.source_path,
        )
        if tuple(field.name for field in fields(fact)) != GENERIC_FIELDS:
            fail("GENERIC_FACT_NOT_EXACT11")
        generic._validate_fact(fact, binding)
        facts.append(fact)
    source = generic.NormalizedDecisionSource(binding=binding, facts=tuple(facts))
    if len(source.facts) != 4:
        fail("GENERIC_SOURCE_NOT_EXACT4")
    return {
        "source_count": 13,
        "semantic_source_identity_count": 13,
        "formal_semantics_independently_validated": True,
        "formal_validator_identity_only": True,
        "formal_validator_executed": False,
        "runtime_revalidation_passed": True,
        "generic_exact11_fact_count": 4,
        "source_records": records,
    }


def independently_check_current_census(repo_root: Path) -> dict[str, object]:
    matrix_path = repo_root / SOURCE_SPECS[10][0]
    summary_path = repo_root / SOURCE_SPECS[11][0]
    manifest_path = repo_root / SOURCE_SPECS[12][0]
    rows = parse_csv(matrix_path.read_bytes(), "CURRENT_WITH_6OA_CENSUS")
    if len(rows) != 1000:
        fail("CURRENT_CENSUS_ROW_COUNT_DRIFT")
    targets = [row for row in rows if row.get("canonical_event_id") in set(EVENT_IDS)]
    if [row.get("canonical_event_id") for row in targets] != list(EVENT_IDS):
        fail("CURRENT_CENSUS_PYR_EXACT4_DRIFT")
    expected = {
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "current_review_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false",
        "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED",
        "training_use_disposition": "UNRESOLVED",
        "human_training_excluded": "false",
        "role_partition_sample_authoritative": "false",
        "canonical_mask_structural_labels_available": "false",
        "structurally_applicable_task_ids_json": "null",
        "formal_training_admitted": "false",
    }
    for row in targets:
        for key, value in expected.items():
            if row.get(key) != value:
                fail("CURRENT_CENSUS_PYR_PRIOR_STATE_DRIFT:" + key)
    summary = strict_json(summary_path.read_bytes(), "CURRENT_WITH_6OA_SUMMARY")
    manifest = strict_json(manifest_path.read_bytes(), "CURRENT_WITH_6OA_MANIFEST")
    schema = "covapie_cumulative1000_current_global_readiness_census_with_6oa_v1"
    if summary.get("schema_version") != schema or manifest.get("schema_version") != schema:
        fail("CURRENT_CENSUS_SCHEMA_DRIFT")
    expect_fields(
        summary.get("authority_boundary"),
        {
            "next_priority_review_current_pending_rank": 1,
            "next_priority_review_event_count": 4,
            "next_priority_review_ligand": "PYR",
            "next_priority_review_pdb": "1F8M",
            "next_priority_review_raw_priority_rank": 30,
            "next_priority_review_unit": (
                "COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4"
            ),
            "NEXT_REVIEW_STARTED": False,
        },
        "CURRENT_CENSUS_PENDING_DRIFT",
    )
    return {
        "row_count": 1000,
        "PYR_event_count": 4,
        "PYR_current_review_status": "CURRENTLY_UNREVIEWED",
        "PYR_human_review_completed": False,
        "PYR_chemistry": "UNRESOLVED",
        "PYR_task_relevance": "UNRESOLVED",
        "PYR_training_use": "UNRESOLVED",
        "current_pending_rank": 1,
        "census_refresh_performed": False,
    }


def independently_check_artifacts(
    repo_root: Path, artifacts: Mapping[str, bytes]
) -> dict[str, object]:
    if set(artifacts) != set(owner.OUTPUT_FILENAMES):
        fail("ARTIFACT_INVENTORY_NOT_EXACT4")
    snapshot = strict_json(artifacts[owner.SNAPSHOT], "SNAPSHOT")
    summary = strict_json(artifacts[owner.SUMMARY], "SUMMARY")
    manifest = strict_json(artifacts[owner.MANIFEST], "MANIFEST")
    rows = parse_csv(artifacts[owner.MATRIX], "MATRIX")
    if len(rows) != 4 or tuple(rows[0]) != owner.MATRIX_HEADER:
        fail("MATRIX_NOT_EXACT4_OR_HEADER_DRIFT")
    if [
        (
            row["canonical_event_id"],
            row["scaleup_rank"],
            row["POST_distance_angstrom"],
            row["reported_POST_distance_angstrom"],
        )
        for row in rows
    ] != list(EVENTS):
        fail("MATRIX_EVENT_IDENTITY_GEOMETRY_DRIFT")
    constant_cells = {
        "artifact_role": "TASK_LABEL_AVAILABILITY_METADATA_ONLY",
        "review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4",
        "pdb_id": "1F8M",
        "ligand_component_id": "PYR",
        "legacy_completed_review_status": "COMPLETED_HUMAN_POSITIVE",
        "human_review_completed": "true",
        "source_formal_generation_domain_decision": "IN_DOMAIN",
        "normalized_task_relevance_disposition": "RELEVANT",
        "source_formal_training_use_decision": "EXCLUDE",
        "normalized_training_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
        "chemistry_disposition": "POSITIVE",
        "negative_chemistry": "false",
        "task_domain_negative": "false",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "CB",
        "pair_sample_authority": "true",
        "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        "role_sample_authority": "true",
        "warhead_atom_ids_json": '["CB","CA","O3"]',
        "linker_atom_ids_json": "[]",
        "scaffold_atom_ids_json": '["C","O","OXT"]',
        "boundary_json": (
            '{"bond_order":"SING","scaffold_atom_id":"C","warhead_atom_id":"CA"}'
        ),
        "minimal_seed_atom_ids_json": '["C","O"]',
        "primary_anchor": "C",
        "canonical_task_count": "5",
        "B3_present": "true",
        "sixth_task": "false",
        "structurally_applicable_task_ids_json": "[0,3,4]",
        "task_applicability_sample_authority": "true",
        "task_label_authority": "false",
        "authoritative_task_labels_created": "false",
        "event_task_label_rows_materialized": "false",
        "mask_tensor_targets_created": "false",
        "training_use_allowed": "false",
        "human_training_excluded": "true",
        "future_training_admission_candidate": "false",
        "formal_training_admitted": "false",
        "training_materialization_allowed": "false",
        "model_supervision_usable": "false",
        "POST_source_evidence_available": "true",
        "explicit_covalent_evidence": "true",
        "distance_only_inference": "false",
        "POST_geometry_training_authority": "false",
        "POST_geometry_training_target_created": "false",
        "supporting_adduct_source_graph_count": "1",
        "candidate_PRE_free_source_graph_count": "1",
        "mapping_count": "0",
        "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "final_PRE_reaction_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "PRE_authority": "false",
        "POST_to_PRE_copy": "false",
        "PRE_zero_fill": "false",
        "reusable_pair_authority": "false",
        "reusable_role_authority": "false",
        "reaction_family_authority": "false",
        "warhead_rule_authority": "false",
        "warhead_type_authority": "false",
        "parameter_update_authorization": "false",
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": "false",
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": "true",
        "READY_FOR_TRAINING": "false",
        "TRAINING_STARTED": "false",
    }
    for row in rows:
        for key, value in constant_cells.items():
            if row.get(key) != value:
                fail("MATRIX_HIGH_VALUE_CELL_DRIFT:" + key)

    expect_fields(
        snapshot,
        {
            "schema_version": "covapie_pyr_completed_human_decision_snapshot_v1",
            "legacy_completed_review_status": "COMPLETED_HUMAN_POSITIVE",
            "projection_of_frozen_formal_human_authority": True,
            "new_human_authority_created_by_ingestion": False,
        },
        "SNAPSHOT_ROOT_DRIFT",
    )
    normalization = snapshot.get("normalization_contract")
    expect_fields(
        normalization.get("task_relevance") if type(normalization) is dict else None,
        {
            "source_formal_generation_domain_decision": "IN_DOMAIN",
            "normalized_task_relevance_disposition": "RELEVANT",
            "mapping": "IN_DOMAIN_TO_RELEVANT",
            "source_value_preserved": True,
        },
        "SNAPSHOT_D2_NORMALIZATION_DRIFT",
    )
    expect_fields(
        normalization.get("training_disposition") if type(normalization) is dict else None,
        {
            "source_formal_training_use_decision": "EXCLUDE",
            "normalized_training_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
            "mapping": "EXCLUDE_TO_EXCLUDE_FROM_TRAINING_ONLY",
            "source_value_preserved": True,
        },
        "SNAPSHOT_D6_NORMALIZATION_DRIFT",
    )
    events = snapshot.get("events")
    if type(events) is not list or len(events) != 4:
        fail("SNAPSHOT_EVENTS_NOT_EXACT4")
    for event in events:
        expect_fields(
            event,
            {
                "human_review_completed": True,
                "legacy_completed_review_status": "COMPLETED_HUMAN_POSITIVE",
                "source_formal_generation_domain_decision": "IN_DOMAIN",
                "normalized_task_relevance_disposition": "RELEVANT",
                "source_formal_training_use_decision": "EXCLUDE",
                "normalized_training_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
                "chemistry_disposition": "POSITIVE",
                "training_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
                "human_training_excluded": True,
                "future_training_admission_candidate": False,
                "task_label_authority": False,
                "event_task_label_rows_materialized": False,
                "mask_tensor_targets_created": False,
                "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
                "mapping_count": 0,
                "POST_geometry_training_authority": False,
                "formal_training_admitted": False,
                "READY_FOR_TRAINING": False,
            },
            "SNAPSHOT_EVENT_DRIFT",
        )
    expect_fields(
        snapshot.get("selected_role_partition"),
        {
            "selected_candidate_id": (
                "CANDIDATE_A_DIRECT_ALPHA_KETOCARBOXYL_POST_CENTER"
            ),
            "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
            "warhead_atom_ids": ["CB", "CA", "O3"],
            "linker_atom_ids": [],
            "scaffold_atom_ids": ["C", "O", "OXT"],
            "boundary": {
                "scaffold_atom_id": "C",
                "warhead_atom_id": "CA",
                "bond_order": "SING",
            },
            "minimal_seed_atom_ids": ["C", "O"],
            "primary_anchor": "C",
            "sample_level_authoritative": True,
            "reusable_role_authority": False,
        },
        "SNAPSHOT_ROLE_DRIFT",
    )
    expect_fields(
        snapshot.get("unselected_alternatives"),
        {
            "alternative_candidate_id": (
                "CANDIDATE_B_STRICT_TERMINAL_ELECTROPHILE_POST_CENTER"
            ),
            "alternative_human_selected": False,
            "alternative_formal_selected": False,
            "alternative_authority_created": False,
            "warhead_atom_ids": ["CB"],
            "linker_atom_ids": ["CA", "O3"],
            "scaffold_atom_ids": ["C", "O", "OXT"],
            "minimal_seed_atom_ids": ["C", "OXT"],
            "authoritative_event_labels_created": False,
        },
        "SNAPSHOT_ALTERNATIVE_DRIFT",
    )
    tasks = snapshot.get("canonical_task_contract")
    expect_fields(
        tasks,
        {
            "global_canonical_task_count": 5,
            "B3_present": True,
            "sixth_task": False,
            "sample_applicable_task_ids": [0, 3, 4],
            "task_applicability_sample_authority": True,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
        },
        "SNAPSHOT_EXACT5_DRIFT",
    )
    if [task["semantic_long_name"] for task in tasks["global_canonical_tasks"]] != [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]:
        fail("SNAPSHOT_EXACT5_LONG_NAMES_DRIFT")
    expect_fields(
        snapshot.get("PRE_boundary"),
        {
            "supporting_adduct_source_graph_count_per_event": 1,
            "candidate_PRE_free_source_graph_count_per_event": 1,
            "mapping_count_per_event": 0,
            "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
            "final_PRE_reaction_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
            "PRE_authority": False,
            "POST_to_PRE_copy": False,
            "PRE_zero_fill": False,
            "C_Br_bond_created": False,
        },
        "SNAPSHOT_PRE_DRIFT",
    )
    expect_fields(
        snapshot.get("training_boundary"),
        {
            "source_formal_training_use_decision": "EXCLUDE",
            "normalized_training_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
            "training_use_allowed": False,
            "human_training_excluded": True,
            "future_training_admission_candidate": False,
            "formal_training_admitted": False,
            "training_materialization_allowed": False,
            "model_supervision_usable": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "SNAPSHOT_TRAINING_DRIFT",
    )
    generic_block = snapshot.get("generic_Exact11_compatibility")
    expect_fields(
        generic_block,
        {
            "accepted_fact_count": 4,
            "generic_fact_field_count": 11,
            "rich_fields_leaked": False,
            "reconciliation_performed": False,
        },
        "SNAPSHOT_GENERIC_DRIFT",
    )
    facts_payload = generic_block.get("facts")
    if type(facts_payload) is not list or len(facts_payload) != 4:
        fail("GENERIC_FACTS_NOT_EXACT4")
    binding = generic.SourceBinding(
        source_path=SOURCE_SPECS[0][0],
        path_namespace="repository_parent_relative",
        byte_count=17975,
        sha256=SOURCE_SPECS[0][3],
        schema_version="covapie_pyr_exact4_formal_human_decision_v1",
        review_unit_id="COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4",
    )
    fact_objects = []
    for payload in facts_payload:
        if set(payload) != set(GENERIC_FIELDS):
            fail("GENERIC_FACT_NOT_EXACT11")
        fact = generic.NormalizedCompletedDecisionFact(**payload)
        if tuple(field.name for field in fields(fact)) != GENERIC_FIELDS:
            fail("GENERIC_DATACLASS_NOT_EXACT11")
        generic._validate_fact(fact, binding)
        fact_objects.append(fact)
    source = generic.NormalizedDecisionSource(binding=binding, facts=tuple(fact_objects))
    if len(source.facts) != 4:
        fail("GENERIC_SOURCE_NOT_EXACT4")

    expect_fields(
        summary,
        {
            "event_count": 4,
            "review_unit_count": 1,
            "legacy_completed_review_status": "COMPLETED_HUMAN_POSITIVE",
            "source_formal_generation_domain_decision": "IN_DOMAIN",
            "normalized_task_relevance_disposition": "RELEVANT",
            "source_formal_training_use_decision": "EXCLUDE",
            "normalized_training_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
            "task_relevant_count": 4,
            "chemistry_positive_count": 4,
            "negative_chemistry_count": 0,
            "task_label_authority_count": 0,
            "event_task_label_rows_materialized_count": 0,
            "mask_tensor_target_count": 0,
            "human_training_excluded_count": 4,
            "future_training_admission_candidate_count": 0,
            "generic_exact11_fact_count": 4,
            "formal_training_admitted_count": 0,
        },
        "SUMMARY_DRIFT",
    )
    expect_fields(
        manifest,
        {
            "candidate_publication_file_count": 7,
            "candidate_publication_paths": [
                path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS
            ],
            "output_artifact_count": 4,
            "matrix_header_frozen": True,
            "matrix_header": list(owner.MATRIX_HEADER),
            "active_source_binding_count": 13,
            "semantic_source_identity_count": 13,
            "duplicate_source_binding_identity_count": 0,
            "formal_validator_provenance_identity_only": True,
            "formal_validator_imported": False,
            "formal_validator_executed_by_production": False,
            "formal_validator_subprocessed_by_production": False,
            "manifest_self_SHA256_recorded": False,
            "legacy_completed_review_status": "COMPLETED_HUMAN_POSITIVE",
        },
        "MANIFEST_DRIFT",
    )
    active = manifest.get("active_source_bindings")
    if type(active) is not list or len(active) != 13:
        fail("MANIFEST_ACTIVE_BINDINGS_NOT_EXACT13")
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
    if len({row.get("semantic_source_identity") for row in active}) != 13:
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
        "event_count": 4,
        "matrix_column_count": len(owner.MATRIX_HEADER),
        "FORMAL_SOURCE_D2": "IN_DOMAIN",
        "NORMALIZED_TASK_RELEVANCE": "RELEVANT",
        "FORMAL_SOURCE_D6": "EXCLUDE",
        "NORMALIZED_TRAINING_DISPOSITION": "EXCLUDE_FROM_TRAINING_ONLY",
        "legacy_completed_review_status": "COMPLETED_HUMAN_POSITIVE",
        "chemistry_disposition": "POSITIVE",
        "human_training_excluded": True,
        "pair": "SG:CB",
        "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        "applicable_task_ids": [0, 3, 4],
        "generic_exact11_fact_count": 4,
        "rich_fields_leaked_to_generic_facts": False,
        "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "TASK_LABEL_AUTHORITY": False,
        "READY_FOR_TRAINING": False,
        "independent_artifact_validation": True,
    }


def main() -> int:
    repo_root = REPO_ROOT
    lifecycle = check_git_lifecycle(repo_root)
    files = [file_record(repo_root, path) for path in owner.CANDIDATE_PUBLICATION_PATHS]
    sources = independently_check_sources(repo_root)
    census = independently_check_current_census(repo_root)
    artifacts = {
        name: (repo_root / owner.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in owner.OUTPUT_FILENAMES
    }
    independent = independently_check_artifacts(repo_root, artifacts)
    owner_result = owner.check_materialized_v1(repo_root)
    if owner_result.get("status") != "PASS":
        fail("OWNER_MATERIALIZED_CHECK_FAILED")
    result = {
        "COVAPIE_PYR_COMPLETED_DECISION_INGESTION_V1_PASS": True,
        "mode": "READ_ONLY_CHECK",
        "lifecycle": lifecycle,
        "files": files,
        "frozen_sources": sources,
        "current_census": census,
        "independent_artifacts": independent,
        "owner_materialized_check": owner_result,
        "candidate_publication_file_count": 7,
        "output_artifact_count": 4,
        "FORMAL_SOURCE_D2": "IN_DOMAIN",
        "NORMALIZED_TASK_RELEVANCE": "RELEVANT",
        "FORMAL_SOURCE_D6": "EXCLUDE",
        "NORMALIZED_TRAINING_DISPOSITION": "EXCLUDE_FROM_TRAINING_ONLY",
        "LEGACY_COMPLETED_REVIEW_STATUS": "COMPLETED_HUMAN_POSITIVE",
        "CHEMISTRY_DISPOSITION": "POSITIVE",
        "NEGATIVE_CHEMISTRY": False,
        "TRAINING_DISPOSITION": "EXCLUDE_FROM_TRAINING_ONLY",
        "HUMAN_TRAINING_EXCLUDED": True,
        "FUTURE_TRAINING_ADMISSION_CANDIDATE": False,
        "PAIR_SAMPLE_AUTHORITY": True,
        "ROLE_SAMPLE_AUTHORITY": True,
        "TASK_APPLICABILITY_SAMPLE_AUTHORITY": True,
        "TASK_LABEL_AUTHORITY": False,
        "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
        "MASK_TENSOR_TARGETS_CREATED": False,
        "GENERIC_EXACT11_FACT_COUNT": 4,
        "RICH_FIELDS_LEAKED_TO_GENERIC_FACTS": False,
        "PRE_SOURCE_MAPPING_STATUS": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "PRE_REACTION_STATUS": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "EXACT7_CANDIDATE": lifecycle["profile"] == CANDIDATE_UNTRACKED,
        "PROJECTION_OF_FROZEN_FORMAL_HUMAN_AUTHORITY": True,
        "NEW_HUMAN_AUTHORITY_CREATED_BY_INGESTION": False,
        "RECONCILIATION_PERFORMED": False,
        "CENSUS_REFRESH_PERFORMED": False,
        "QUEUE_REFRESH_PERFORMED": False,
        "NEXT_REVIEW_STARTED": False,
        "FORMAL_TRAINING_ADMITTED": False,
        "TRAINING_ADMISSION_CREATED": False,
        "TRAINING_MATERIALIZATION_ALLOWED": False,
        "PARAMETER_UPDATE_AUTHORIZATION": False,
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
        "STEP12D_STATUS": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
        "COMMIT_PERFORMED": False,
        "PUSH_PERFORMED": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
