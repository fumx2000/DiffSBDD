#!/usr/bin/env python3
"""Independently check a 6OA ingestion Exact7 candidate or clean successor."""

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
    covapie_6oa_completed_decision_ingestion_and_task_label_availability_v1 as owner,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_direct_attachment_optional_linker_runtime_v1 as runtime,
)


ERROR = "COVAPIE_6OA_INGESTION_CHECK_V1_ERROR"
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
    (
        "COVAPIE_CYS_SG_EVENT_V1:4OU2:A:CYS:302-:SG:G:6OA:C5",
        "855",
        "1.853206",
        "false",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4OU2:B:CYS:302-:SG:J:6OA:C5",
        "856",
        "1.674652",
        "false",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4OU2:C:CYS:302-:SG:M:6OA:C5",
        "857",
        "1.347977",
        "true",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4OU2:D:CYS:302-:SG:P:6OA:C5",
        "858",
        "1.677347",
        "false",
    ),
)
EVENT_IDS = tuple(row[0] for row in EVENTS)
W = ("C5", "O3")
L: tuple[str, ...] = ()
S = ("C", "C1", "C2", "C3", "C4", "O", "O1", "O2")
BONDS = (
    ("C", "C1", "SING"),
    ("C", "O", "SING"),
    ("C", "O1", "DOUB"),
    ("C1", "C2", "DOUB"),
    ("C1", "O2", "SING"),
    ("C2", "C3", "SING"),
    ("C3", "C4", "DOUB"),
    ("C4", "C5", "SING"),
    ("C5", "O3", "SING"),
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
        "6OA_COVAPIE_BULK_REVIEW_UNIT_E800FEC791DFDA72/formal-human-decision-v1/"
        "6oa_formal_human_decision_v1.json",
        "project_parent_relative",
        33043,
        "c79a0f03b0bb9847c190befd351c4c323e1243b10e30655c3b4f61c2f9034218",
    ),
    (
        "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
        "6OA_COVAPIE_BULK_REVIEW_UNIT_E800FEC791DFDA72/formal-human-decision-v1/"
        "validate_6oa_formal_human_decision_v1.py",
        "project_parent_relative",
        96246,
        "77800ac2056df2b0770967be15bb89c67d2be089d6c54180361f4922ee73731e",
    ),
    (
        "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
        "6OA_COVAPIE_BULK_REVIEW_UNIT_E800FEC791DFDA72/review-preparation-v1/"
        "6oa_exact4_event_evidence_v1.csv",
        "project_parent_relative",
        12443,
        "322434764911133ea51815e7ce45531423c84106bb618f5cbac033043bb8f31e",
    ),
    (
        "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
        "6OA_COVAPIE_BULK_REVIEW_UNIT_E800FEC791DFDA72/review-preparation-v1/"
        "6oa_graph_and_review_evidence_v1.json",
        "project_parent_relative",
        31059,
        "370569f68a3ff935695bffb5959413fff8382773780965fddd79d88ab5e53e6a",
    ),
    (
        "covapie-state/bulk-model-usable-auto-admission-scaleup-v1/"
        "ranks-0501-1000/attempt-001/cache/rcsb/ccd/6OA.cif",
        "project_parent_relative",
        6723,
        "2a5bcd59744ad76e127c09c308380e2fbe882c237b8f20f3f29f0adbfd006cf6",
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
        "src/covalent_ext/"
        "covapie_cumulative1000_current_global_readiness_census_with_nwj_v1.py",
        "repository_relative",
        75148,
        "aca86bfacf0811d3aca70a2c2d21e7ca8c1b2cb0382d847a03372339eec899a7",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_cumulative1000_current_global_readiness_census_with_nwj_v1/"
        "covapie_cumulative1000_current_global_readiness_census_with_nwj_v1.csv",
        "repository_relative",
        553770,
        "5e527a258f8589677c71c5271f3d305540ace8d87e8b647282f02856fd356a9e",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_cumulative1000_current_global_readiness_census_with_nwj_v1/"
        "covapie_cumulative1000_current_global_readiness_summary_with_nwj_v1.json",
        "repository_relative",
        21523,
        "a9dfa8d763c1a8c746f9ff9ec16d684a5dccfa581afd078090f2ab17a82c6bf4",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_cumulative1000_current_global_readiness_census_with_nwj_v1/"
        "covapie_cumulative1000_current_global_readiness_manifest_with_nwj_v1.json",
        "repository_relative",
        81923,
        "504134d0e0a92b8ffe4147992b1c0869c5e2289eb9161d6b2bdf079f0a19911f",
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
    untracked = git(repo_root, "ls-files", "--others", "--exclude-standard").splitlines()
    expected = [path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS]
    expected_set = set(expected)
    if modified:
        fail("TRACKED_MODIFICATIONS_PRESENT")
    if staged:
        fail("STAGED_INDEX_NOT_EMPTY")
    if set(untracked) == expected_set and len(untracked) == 7:
        profile = CANDIDATE_UNTRACKED
        if head != owner.BASELINE_COMMIT or origin != owner.BASELINE_COMMIT or ahead != 0:
            fail("CANDIDATE_UNTRACKED_BASELINE_PROFILE_DRIFT")
    elif not untracked:
        profile = TRACKED_CLEAN
        tracked = set(git(repo_root, "ls-files", "--", *expected).splitlines())
        if tracked != expected_set:
            fail("TRACKED_CLEAN_EXACT7_NOT_TRACKED")
        stages = git(repo_root, "ls-files", "--stage", "--", *expected).splitlines()
        if len(stages) != 7 or any(not row.startswith("100644 ") for row in stages):
            fail("TRACKED_CLEAN_GIT_MODE_NOT_100644")
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
    candidate_history = expected_set | historical_changed
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
        "ordinary_untracked_count": len(untracked),
        "ordinary_untracked_paths": untracked,
        "raw_changed_since_baseline_count": 0,
        "protected_source_changed_since_baseline_count": 0,
        "forbidden_candidate_file_count": 0,
    }


def independently_check_sources(repo_root: Path) -> dict[str, object]:
    payloads: dict[str, bytes] = {}
    records = []
    for relative, namespace, expected_bytes, expected_sha in SOURCE_SPECS:
        path = repo_root / relative if namespace == "repository_relative" else repo_root.parent / relative
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
    if len(records) != 13 or len({(r["path_namespace"], r["path"], r["SHA256"]) for r in records}) != 13:
        fail("SOURCE_IDENTITIES_NOT_UNIQUE_EXACT13")

    formal = strict_json(payloads[SOURCE_SPECS[0][0]], "INDEPENDENT_FORMAL")
    expect_fields(
        formal,
        {
            "schema_version": "covapie_6oa_exact4_formal_human_decision_v1",
            "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        },
        "FORMAL_ROOT_DRIFT",
    )
    expect_fields(
        formal.get("formal_state"),
        {
            "approved": True,
            "unsigned": False,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "human_review_completed": True,
            "formal_decision_created": True,
            "machine_generated_human_authorization": False,
        },
        "FORMAL_STATE_DRIFT",
    )
    expect_fields(
        formal.get("human_authorization"),
        {
            "approval_time": None,
            "approval_time_status": "NOT_PROVIDED_VERIFIABLY",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "machine_generated_human_authorization": False,
            "platform_identity_verification_claimed": False,
        },
        "FORMAL_AUTHORIZATION_DRIFT",
    )
    candidate = formal["human_authorization"]["candidate_binding"]
    expect_fields(
        candidate,
        {
            "SHA256": "8eff75e7e23bc68013ac1549524c77b9d2731e376cc6b0ba0157e733d864d1c9",
            "binding_transfers_to_other_candidate_versions": False,
        },
        "FORMAL_CANDIDATE_BINDING_DRIFT",
    )
    expect_fields(
        formal.get("sample_identity"),
        {
            "PDB": "4OU2",
            "ligand_component_id": "6OA",
            "review_unit_id": owner.EXPECTED_REVIEW_UNIT_ID,
            "event_count": 4,
            "canonical_event_ids": list(EVENT_IDS),
            "scaleup_event_ranks": [855, 856, 857, 858],
            "current_pending_rank": 1,
        },
        "FORMAL_SAMPLE_IDENTITY_DRIFT",
    )
    decisions = formal.get("formal_decisions")
    if type(decisions) is not dict:
        fail("FORMAL_DECISIONS_MISSING")
    expect_fields(
        decisions.get("D1_observed_covalent_chemistry"),
        {"decision": "POSITIVE", "chemistry_negative": False},
        "FORMAL_D1_DRIFT",
    )
    expect_fields(
        decisions.get("D2_task_generation_domain_relevance"),
        {"decision": "OUT_OF_DOMAIN", "chemistry_positive_preserved": True},
        "FORMAL_D2_DRIFT",
    )
    expect_fields(
        decisions.get("D3_reactive_atom_pair_confirmation_or_revision"),
        {
            "decision": "CONFIRM_OBSERVED_PAIR",
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "C5",
            "reactive_pair_sample_authoritative": True,
            "reusable_pair_authority": False,
        },
        "FORMAL_D3_DRIFT",
    )
    expect_fields(
        decisions.get("D4_role_partition_and_minimal_seed"),
        {
            "selected_candidate": "CANDIDATE_A_DIRECT_POST_REACTION_CENTER",
            "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
            "role_partition_sample_authoritative": True,
            "reusable_role_authority": False,
            "PRE_precursor_role_authority": False,
        },
        "FORMAL_D4_DRIFT",
    )
    expect_fields(
        decisions.get("D5_structural_task_applicability"),
        {
            "applicable_task_ids": [0, 3, 4],
            "task_applicability_sample_authoritative": True,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
        },
        "FORMAL_D5_DRIFT",
    )
    expect_fields(
        decisions.get("D6_later_training_use_disposition"),
        {
            "decision": "NOT_APPLICABLE",
            "consistent_with_D2": "OUT_OF_DOMAIN",
            "formal_training_admitted": False,
            "training_materialization_allowed": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "FORMAL_D6_DRIFT",
    )
    selected = formal.get("selected_role_context")
    expect_fields(
        selected,
        {
            "candidate_id": "CANDIDATE_A_DIRECT_POST_REACTION_CENTER",
            "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
            "warhead_atom_ids": list(W),
            "linker_atom_ids": [],
            "scaffold_atom_ids": list(S),
            "boundary": "C4--C5/SING",
            "task_ids": [0, 3, 4],
        },
        "FORMAL_SELECTED_ROLE_DRIFT",
    )
    expect_fields(
        selected.get("minimal_seed"),
        {"atom_ids": ["C3", "C4"], "primary_scaffold_side_anchor": "C4"},
        "FORMAL_SEED_DRIFT",
    )
    expect_fields(
        formal.get("PRE_boundary"),
        {
            "supporting_adduct_source_graph_count_per_event": 0,
            "candidate_PRE_free_source_graph_count_per_event": 0,
            "source_mapping_count_per_event": 0,
            "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_NOT_AVAILABLE",
            "final_PRE_reaction_status": "PRE_REACTION_UNRESOLVED",
            "PRE_authority": False,
            "POST_to_PRE_copy": False,
            "PRE_zero_fill": False,
            "C5_O3_free_precursor_double_bond_authority": False,
            "2VS_substituted_for_6OA_PRE": False,
        },
        "FORMAL_PRE_DRIFT",
    )
    expect_fields(
        formal.get("training_boundary"),
        {
            "human_training_use_disposition": "NOT_APPLICABLE",
            "future_training_admission_candidate": False,
            "formal_training_admitted": False,
            "training_materialization_allowed": False,
            "task_label_authority": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "FORMAL_TRAINING_DRIFT",
    )
    exact5 = formal.get("canonical_Exact5")
    expect_fields(
        exact5,
        {
            "task_count": 5,
            "B3_present": True,
            "sixth_task": False,
            "selected_structural_applicability_task_ids": [0, 3, 4],
            "task_label_authority": False,
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
    geometry = formal.get("geometry_boundary")
    expect_fields(
        geometry,
        {
            "POST_geometry_training_authority": False,
            "POST_geometry_training_target_created": False,
            "new_bond_order_inferred": False,
        },
        "FORMAL_GEOMETRY_DRIFT",
    )
    expect_fields(
        geometry.get("rank857_caveat"),
        {
            "scaleup_event_rank": 857,
            "exact_POST_distance_angstrom": 1.347977,
            "geometry_outlier": True,
            "distance_normalized": False,
            "event_removed": False,
            "new_bond_order_inferred": False,
        },
        "FORMAL_RANK857_DRIFT",
    )

    event_rows = parse_csv(payloads[SOURCE_SPECS[2][0]], "INDEPENDENT_EVENT_EVIDENCE")
    if len(event_rows) != 4:
        fail("EVENT_EVIDENCE_NOT_EXACT4")
    for row, expected in zip(event_rows, EVENTS, strict=True):
        event_id, rank, distance, _outlier = expected
        expected_cells = {
            "canonical_event_id": event_id,
            "scaleup_event_rank": rank,
            "pdb_id": "4OU2",
            "ligand_component_id": "6OA",
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "C5",
            "exact_POST_distance_angstrom": distance,
            "explicit_covalent_evidence": "true",
            "distance_only_inference_used": "false",
            "supporting_adduct_graph_count": "0",
            "candidate_PRE_free_source_graph_count": "0",
            "source_PRE_mapping_count": "0",
            "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_NOT_AVAILABLE",
            "final_PRE_reaction_status": "PRE_REACTION_UNRESOLVED",
        }
        for key, value in expected_cells.items():
            if row.get(key) != value:
                fail("EVENT_EVIDENCE_DRIFT:" + rank + ":" + key)
        structure = json.loads(row["source_structure_binding_json"])
        if (
            structure.get("SHA256")
            != "f3de681dabd3fde72156fe03b0cf92afec9242f6fefa6c24ad76232eae1a992a"
            or structure.get("bytes") != 406996
        ):
            fail("FROZEN_4OU2_IDENTITY_DRIFT")

    graph_doc = strict_json(payloads[SOURCE_SPECS[3][0]], "INDEPENDENT_GRAPH")
    graph = graph_doc.get("CCD_complete_heavy_atom_graph")
    atom_ids = tuple(row["atom_id"] for row in graph["atom_inventory"])
    bonds = tuple(
        (row["atom_id_1"], row["atom_id_2"], row["bond_order"])
        for row in graph["bond_inventory"]
    )
    if len(atom_ids) != 10 or set(atom_ids) != set((*W, *S)):
        fail("GRAPH_EXACT10_DRIFT")
    if len(bonds) != 9 or set(bonds) != set(BONDS):
        fail("GRAPH_EXACT9_BONDS_DRIFT")
    pre = graph_doc.get("PRE_evidence")
    expect_fields(
        pre,
        {
            "mapping_status": "PRE_SOURCE_GRAPH_NOT_AVAILABLE",
            "reaction_status": "PRE_REACTION_UNRESOLVED",
            "POST_to_PRE_copy": False,
            "PRE_zero_fill": False,
            "PRE_topology_created": False,
            "PRE_coordinates_created": False,
        },
        "GRAPH_PRE_DRIFT",
    )

    role = runtime.validate_role_profile_v1(
        role_profile="DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        retained_heavy_atoms=atom_ids,
        scaffold_atoms=S,
        linker_atoms=L,
        warhead_atoms=W,
        reactive_atom_id="C5",
        direct_scaffold_warhead_boundaries=(("C4", "C5", "SING"),),
        explicit_graph_bonds=bonds,
    )
    boundary = role.direct_scaffold_warhead_boundary
    if not role.valid or boundary is None or not boundary.boundary_valid:
        fail("INDEPENDENT_ROLE_RUNTIME_FAILED")
    seed = runtime.validate_minimal_seed_for_role_profile_v1(
        role_profile="DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        seed_atoms=("C3", "C4"),
        scaffold_atoms=S,
        linker_atoms=L,
        warhead_atoms=W,
        explicit_graph_bonds=bonds,
        direct_boundary=boundary,
    )
    if not seed.valid or seed.primary_anchor_atom_id != "C4":
        fail("INDEPENDENT_SEED_RUNTIME_FAILED")
    if runtime.valid_canonical_task_ids_for_role_profile_v1(
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    ) != (0, 3, 4):
        fail("INDEPENDENT_TASK_RUNTIME_FAILED")

    owner_tree = ast.parse((repo_root / owner.SOURCE_RELATIVE).read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(owner_tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    if "subprocess" in imported or any(
        name.endswith("validate_6oa_formal_human_decision_v1") for name in imported
    ):
        fail("PRODUCTION_FORMAL_VALIDATOR_EXECUTABLE_DEPENDENCY")
    return {
        "source_count": 13,
        "records": records,
        "formal_json_independently_validated": True,
        "formal_validator_provenance_identity_only": True,
        "formal_validator_imported": False,
        "formal_validator_executed_by_production": False,
        "formal_validator_subprocessed_by_production": False,
        "frozen_4OU2_identity_validated_from_event_evidence": True,
        "independent_graph_Exact10": True,
        "independent_DIRECT_runtime": True,
    }


def independently_check_current_census(repo_root: Path) -> dict[str, object]:
    matrix_path = repo_root / SOURCE_SPECS[10][0]
    summary_path = repo_root / SOURCE_SPECS[11][0]
    rows = parse_csv(matrix_path.read_bytes(), "CURRENT_WITH_NWJ_CENSUS")
    targets = [row for row in rows if row.get("canonical_event_id") in set(EVENT_IDS)]
    if len(rows) != 1000 or tuple(row["canonical_event_id"] for row in targets) != EVENT_IDS:
        fail("CURRENT_CENSUS_EXACT4_DRIFT")
    expected = {
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "current_review_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false",
        "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED",
        "training_use_disposition": "UNRESOLVED",
        "reactive_pair_sample_authoritative": "false",
        "role_partition_sample_authoritative": "false",
        "canonical_mask_structural_labels_available": "false",
        "structurally_applicable_task_ids_json": "null",
        "formal_training_admitted": "false",
    }
    for row in targets:
        for key, value in expected.items():
            if row.get(key) != value:
                fail("CURRENT_CENSUS_PREINGESTION_DRIFT:" + key)
    summary = strict_json(summary_path.read_bytes(), "CURRENT_WITH_NWJ_SUMMARY")
    authority = summary.get("authority_boundary")
    expect_fields(
        authority,
        {
            "next_priority_review_current_pending_rank": 1,
            "next_priority_review_ligand": "6OA",
            "next_priority_review_unit": owner.EXPECTED_REVIEW_UNIT_ID,
            "NEXT_REVIEW_STARTED": False,
        },
        "CURRENT_CENSUS_PENDING_DRIFT",
    )
    return {
        "row_count": 1000,
        "6OA_event_count": 4,
        "6OA_current_review_status": "CURRENTLY_UNREVIEWED",
        "6OA_human_review_completed": False,
        "6OA_chemistry": "UNRESOLVED",
        "6OA_task_relevance": "UNRESOLVED",
        "6OA_training_use": "UNRESOLVED",
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
    if tuple(
        (
            row["canonical_event_id"],
            row["scaleup_rank"],
            row["POST_distance_angstrom"],
            row["geometry_outlier"],
        )
        for row in rows
    ) != EVENTS:
        fail("MATRIX_EVENT_IDENTITY_GEOMETRY_DRIFT")
    constant_cells = {
        "review_unit_id": owner.EXPECTED_REVIEW_UNIT_ID,
        "pdb_id": "4OU2",
        "ligand_component_id": "6OA",
        "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "human_review_completed": "true",
        "source_formal_generation_domain_decision": "OUT_OF_DOMAIN",
        "normalized_task_relevance_disposition": "NOT_RELEVANT",
        "chemistry_disposition": "POSITIVE",
        "negative_chemistry": "false",
        "task_domain_negative": "true",
        "positive_generative_supervision_eligible": "false",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C5",
        "pair_sample_authority": "true",
        "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        "role_sample_authority": "true",
        "warhead_atom_ids_json": '["C5","O3"]',
        "linker_atom_ids_json": "[]",
        "scaffold_atom_ids_json": '["C","C1","C2","C3","C4","O","O1","O2"]',
        "boundary_json": '{"bond_order":"SING","scaffold_atom_id":"C4","warhead_atom_id":"C5"}',
        "minimal_seed_atom_ids_json": '["C3","C4"]',
        "primary_anchor": "C4",
        "canonical_task_count": "5",
        "B3_present": "true",
        "sixth_task": "false",
        "structurally_applicable_task_ids_json": "[0,3,4]",
        "task_applicability_sample_authority": "true",
        "task_label_authority": "false",
        "authoritative_task_labels_created": "false",
        "event_task_label_rows_materialized": "false",
        "mask_tensor_targets_created": "false",
        "formal_event_training_use_decision": "NOT_APPLICABLE",
        "training_use_allowed": "false",
        "human_training_excluded": "false",
        "candidate_for_future_training_admission": "false",
        "future_training_admission_candidate": "false",
        "training_admitted": "false",
        "formal_training_admitted": "false",
        "training_materialization_allowed": "false",
        "tensor_target_created": "false",
        "model_supervision_usable": "false",
        "current_runtime_model_usable": "false",
        "POST_source_evidence_available": "true",
        "explicit_covalent_evidence": "true",
        "distance_only_inference": "false",
        "POST_geometry_training_authority": "false",
        "POST_geometry_training_target_created": "false",
        "supporting_adduct_source_graph_count": "0",
        "candidate_PRE_free_source_graph_count": "0",
        "mapping_count": "0",
        "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_NOT_AVAILABLE",
        "final_PRE_reaction_status": "PRE_REACTION_UNRESOLVED",
        "PRE_authority": "false",
        "POST_to_PRE_copy": "false",
        "PRE_zero_fill": "false",
        "C5_O3_free_precursor_double_bond_authority": "false",
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
            "schema_version": "covapie_6oa_completed_human_decision_snapshot_v1",
            "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
            "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
            "projection_of_frozen_formal_human_authority": True,
            "new_human_authority_created_by_ingestion": False,
        },
        "SNAPSHOT_ROOT_DRIFT",
    )
    expect_fields(
        snapshot.get("task_relevance_normalization"),
        {
            "source_formal_generation_domain_decision": "OUT_OF_DOMAIN",
            "normalized_task_relevance_disposition": "NOT_RELEVANT",
            "source_value_preserved": True,
            "chemistry_disposition_changed_by_normalization": False,
            "training_exclusion_created_by_normalization": False,
        },
        "SNAPSHOT_NORMALIZATION_DRIFT",
    )
    expect_fields(
        snapshot.get("selected_role_partition"),
        {
            "selected_candidate": "CANDIDATE_A_DIRECT_POST_REACTION_CENTER",
            "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
            "warhead_atom_ids": list(W),
            "linker_atom_ids": [],
            "scaffold_atom_ids": list(S),
            "boundary": {
                "scaffold_atom_id": "C4",
                "warhead_atom_id": "C5",
                "bond_order": "SING",
            },
            "minimal_seed_atom_ids": ["C3", "C4"],
            "primary_anchor": "C4",
            "sample_level_authoritative": True,
            "reusable_role_authority": False,
        },
        "SNAPSHOT_ROLE_DRIFT",
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
            "supporting_adduct_source_graph_count_per_event": 0,
            "candidate_PRE_free_source_graph_count_per_event": 0,
            "mapping_count_per_event": 0,
            "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_NOT_AVAILABLE",
            "final_PRE_reaction_status": "PRE_REACTION_UNRESOLVED",
            "PRE_authority": False,
            "POST_to_PRE_copy": False,
            "PRE_zero_fill": False,
            "C5_O3_free_precursor_double_bond_authority": False,
            "2VS_substituted_for_sample_specific_PRE": False,
        },
        "SNAPSHOT_PRE_DRIFT",
    )
    expect_fields(
        snapshot.get("POST_boundary"),
        {
            "POST_source_evidence_available": True,
            "explicit_covalent_evidence": True,
            "distance_only_inference": False,
            "POST_geometry_training_authority": False,
            "POST_geometry_training_target_created": False,
        },
        "SNAPSHOT_POST_DRIFT",
    )
    expect_fields(
        snapshot.get("training_boundary"),
        {
            "formal_event_training_use_decision": "NOT_APPLICABLE",
            "training_use_allowed": False,
            "human_training_excluded": False,
            "candidate_for_future_training_admission": False,
            "future_training_admission_candidate": False,
            "training_admitted": False,
            "formal_training_admitted": False,
            "training_materialization_allowed": False,
            "tensor_target_created": False,
            "model_supervision_usable": False,
            "current_runtime_model_usable": False,
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
        byte_count=33043,
        sha256=SOURCE_SPECS[0][3],
        schema_version="covapie_6oa_exact4_formal_human_decision_v1",
        review_unit_id=owner.EXPECTED_REVIEW_UNIT_ID,
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
            "completed_review_unit_count": 1,
            "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
            "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
            "source_formal_generation_domain_decision": "OUT_OF_DOMAIN",
            "normalized_task_relevance_disposition": "NOT_RELEVANT",
            "task_not_relevant_count": 4,
            "chemistry_positive_count": 4,
            "negative_chemistry_count": 0,
            "pair_authority_event_count": 4,
            "role_authority_event_count": 4,
            "task_applicability_determined_event_count": 4,
            "authoritative_task_label_event_count": 0,
            "event_task_label_rows_materialized_count": 0,
            "mask_tensor_target_count": 0,
            "training_NOT_APPLICABLE_event_count": 4,
            "human_training_excluded_count": 0,
            "future_training_admission_candidate_count": 0,
            "formal_training_admitted_count": 0,
            "PRE_authority_count": 0,
            "POST_training_authority_count": 0,
            "generic_exact11_accepted_count": 4,
            "rich_fields_leaked_to_generic_facts": False,
            "rank857_geometry_outlier_retained": True,
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
            "active_source_binding_count": 13,
            "semantic_source_identity_count": 13,
            "duplicate_source_binding_identity_count": 0,
            "formal_validator_provenance_identity_only": True,
            "formal_validator_imported": False,
            "formal_validator_executed_by_production": False,
            "formal_validator_subprocessed_by_production": False,
            "manifest_self_SHA256_recorded": False,
            "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        },
        "MANIFEST_DRIFT",
    )
    active = manifest.get("active_source_bindings")
    if type(active) is not list or len(active) != 13:
        fail("MANIFEST_ACTIVE_BINDINGS_NOT_EXACT13")
    expected_source_keys = {(path, namespace, size, digest) for path, namespace, size, digest in SOURCE_SPECS}
    actual_source_keys = {
        (row.get("path"), row.get("path_namespace"), row.get("byte_count"), row.get("SHA256"))
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
    for record, name in zip(output_records, (owner.SNAPSHOT, owner.MATRIX, owner.SUMMARY), strict=True):
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
    for value in manifest.values():
        if type(value) is str and value.startswith("/"):
            fail("MANIFEST_ABSOLUTE_PATH_VALUE")
    return {
        "event_count": 4,
        "matrix_column_count": len(owner.MATRIX_HEADER),
        "FORMAL_SOURCE_D2": "OUT_OF_DOMAIN",
        "NORMALIZED_TASK_RELEVANCE": "NOT_RELEVANT",
        "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "chemistry_disposition": "POSITIVE",
        "pair": "SG:C5",
        "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        "applicable_task_ids": [0, 3, 4],
        "generic_exact11_fact_count": 4,
        "rich_fields_leaked_to_generic_facts": False,
        "rank857_geometry_outlier_retained": True,
        "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_NOT_AVAILABLE",
        "PRE_reaction_status": "PRE_REACTION_UNRESOLVED",
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
        "COVAPIE_6OA_COMPLETED_DECISION_INGESTION_V1_PASS": True,
        "mode": "READ_ONLY_CHECK",
        "lifecycle": lifecycle,
        "files": files,
        "frozen_sources": sources,
        "current_census": census,
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
        "PAIR_SAMPLE_AUTHORITY": True,
        "ROLE_SAMPLE_AUTHORITY": True,
        "TASK_APPLICABILITY_SAMPLE_AUTHORITY": True,
        "TASK_LABEL_AUTHORITY": False,
        "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
        "MASK_TENSOR_TARGETS_CREATED": False,
        "GENERIC_EXACT11_FACT_COUNT": 4,
        "RICH_FIELDS_LEAKED_TO_GENERIC_FACTS": False,
        "RANK857_GEOMETRY_OUTLIER_RETAINED": True,
        "PRE_SOURCE_MAPPING_STATUS": "PRE_SOURCE_GRAPH_NOT_AVAILABLE",
        "PRE_REACTION_STATUS": "PRE_REACTION_UNRESOLVED",
        "EXACT7_CANDIDATE": lifecycle["profile"] == CANDIDATE_UNTRACKED,
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
