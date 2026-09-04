#!/usr/bin/env python3
"""Fail-closed checker for the 0D8 completed-decision reconciliation Exact4."""

from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any, NoReturn


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_0d8_completed_decision_ingestion_and_task_label_availability_v1
    as ingestion,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_0d8_v1 as subject,
)


BASELINE_COMMIT = "4ce24b7b15f3989d92d9c716ad464c472926c9ab"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
DEPENDENCY_BINDINGS = (
    (
        "GENERIC_OWNER",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
    ),
    (
        "WITH_LCY_PREDECESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_lcy_v1.py",
        38419,
        "e800a49ca10e9b9c025ca0413abb8818a8a3d3fb6e63d4d6cb0635f81f46fda7",
    ),
    (
        "0D8_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_0d8_completed_decision_ingestion_and_task_label_availability_v1.py",
        106540,
        "1be00e2d03d7eb709fbe3ba11c577bd48308a77c03c795d77226da50599b2579",
    ),
)
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
PROTECTED_PREFIXES = (
    "data/raw/",
    "checkpoints/",
    "equivariant_diffusion/",
    "covapie-state/",
)
PROTECTED_FILES = {
    "lightning_modules.py",
    "dataset.py",
    "data/prepare_crossdocked.py",
}
MAX_FILE_BYTES = 1024 * 1024
EXPECTED_PREDECESSOR_COVERAGE = {
    "accepted_fact_count": 127,
    "accepted_review_unit_count": 21,
    "stable_source_identity_count": 21,
    "remaining_unreviewed_chemistry_event_count": 211,
    "remaining_unreviewed_review_unit_upper_bound": 110,
    "decision_category_distribution": {
        "chemistry_positive": 91,
        "chemistry_negative": 20,
        "task_domain_negative": 16,
        "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}
EXPECTED_SUCCESSOR_COVERAGE = {
    "accepted_fact_count": 131,
    "accepted_review_unit_count": 22,
    "stable_source_identity_count": 22,
    "remaining_unreviewed_chemistry_event_count": 207,
    "remaining_unreviewed_review_unit_upper_bound": 109,
    "decision_category_distribution": {
        "chemistry_positive": 91,
        "chemistry_negative": 20,
        "task_domain_negative": 20,
        "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}


def _fail(token: str) -> NoReturn:
    raise ValueError("COVAPIE_0D8_RECONCILIATION_V1_ERROR:" + token)


def _git(root: Path, *arguments: str) -> str:
    allowed = {
        "branch",
        "diff",
        "ls-files",
        "merge-base",
        "rev-list",
        "rev-parse",
        "status",
    }
    if not arguments or arguments[0] not in allowed:
        _fail("GIT_SUBCOMMAND_FORBIDDEN")
    process = subprocess.run(
        ("git", *arguments), cwd=root, text=True, capture_output=True, check=False
    )
    if process.returncode:
        _fail("GIT_COMMAND_FAILED:" + arguments[0])
    return process.stdout.rstrip("\n")


def _git_is_ancestor(root: Path, older: str, newer: str) -> bool:
    process = subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer),
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode not in (0, 1):
        _fail("GIT_ANCESTRY_CHECK_FAILED")
    return process.returncode == 0


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_regular(path: Path, label: str) -> bytes:
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise ValueError("READ_FAILED:" + label) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        _fail("NOT_REGULAR_FILE:" + label)
    return payload


def classify_repository_profile(
    *,
    expected_paths: tuple[str, ...],
    tracked_paths: set[str],
    ordinary_untracked: set[str],
    status_lines: tuple[str, ...],
    working_diff: set[str],
    cached_diff: set[str],
) -> str:
    """Classify only the strict untracked or tracked-clean lifecycle profile."""

    expected = set(expected_paths)
    if len(expected_paths) != 4 or len(expected) != 4:
        _fail("EXPECTED_INVENTORY_NOT_EXACT4")
    tracked_candidate = expected & tracked_paths
    if tracked_candidate and tracked_candidate != expected:
        _fail("MIXED_TRACKING_STATE")
    if working_diff:
        _fail("TRACKED_WORKTREE_MODIFICATION_PRESENT")
    if cached_diff:
        _fail("STAGED_INDEX_CHANGE_PRESENT")
    if len(status_lines) != len(set(status_lines)):
        _fail("DUPLICATE_STATUS_ENTRY")
    if not tracked_candidate:
        if ordinary_untracked != expected:
            _fail("ORDINARY_UNTRACKED_NOT_STRICT_EXACT4")
        if set(status_lines) != {"?? " + path for path in expected}:
            _fail("CANDIDATE_STATUS_NOT_STRICT_EXACT4")
        return CANDIDATE_UNTRACKED
    if ordinary_untracked or status_lines:
        _fail("TRACKED_CLEAN_STATE_DIRTY")
    return TRACKED_CLEAN


def validate_repository_relation_values(
    *,
    profile: str,
    expected_paths: set[str],
    head: str,
    origin_main: str,
    ahead: int,
    behind: int,
    baseline_is_ancestor_of_head: bool,
    baseline_is_ancestor_of_origin: bool,
    origin_is_ancestor_of_head: bool,
    changed_since_baseline: set[str],
) -> None:
    """Validate publication ancestry without pinning a future commit hash."""

    if profile == CANDIDATE_UNTRACKED:
        if not (
            head == BASELINE_COMMIT
            and origin_main == BASELINE_COMMIT
            and (ahead, behind) == (0, 0)
            and baseline_is_ancestor_of_head
            and baseline_is_ancestor_of_origin
            and origin_is_ancestor_of_head
            and not changed_since_baseline
        ):
            _fail("CANDIDATE_BASELINE_RELATION_INVALID")
        return
    if profile != TRACKED_CLEAN:
        _fail("REPOSITORY_PROFILE_INVALID")
    if (
        not baseline_is_ancestor_of_head
        or not baseline_is_ancestor_of_origin
        or not origin_is_ancestor_of_head
        or head == BASELINE_COMMIT
        or behind != 0
        or ahead < 0
        or not expected_paths <= changed_since_baseline
    ):
        _fail("TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID")
    if (ahead == 0) != (origin_main == head):
        _fail("TRACKED_CLEAN_ORIGIN_RELATION_INVALID")


def _repository_observations(root: Path) -> dict[str, object]:
    return {
        "tracked_paths": set(filter(None, _git(root, "ls-files").splitlines())),
        "ordinary_untracked": set(
            filter(
                None,
                _git(root, "ls-files", "--others", "--exclude-standard").splitlines(),
            )
        ),
        "status_lines": tuple(
            filter(
                None,
                _git(root, "status", "--short", "--untracked-files=all").splitlines(),
            )
        ),
        "working_diff": set(
            filter(None, _git(root, "diff", "--name-only").splitlines())
        ),
        "cached_diff": set(
            filter(None, _git(root, "diff", "--cached", "--name-only").splitlines())
        ),
    }


def _validate_history_scope(changed_since_baseline: set[str]) -> None:
    protected = sorted(
        path
        for path in changed_since_baseline
        if path in PROTECTED_FILES
        or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)
    )
    forbidden = sorted(
        path
        for path in changed_since_baseline
        if Path(path).suffix.lower() in FORBIDDEN_SUFFIXES
    )
    if protected:
        _fail("PROTECTED_PATH_CHANGED_SINCE_BASELINE:" + protected[0])
    if forbidden:
        _fail("FORBIDDEN_SUFFIX_CHANGED_SINCE_BASELINE:" + forbidden[0])


def _verify_repository_relation(
    root: Path, profile: str, expected_paths: set[str]
) -> dict[str, object]:
    head = _git(root, "rev-parse", "HEAD")
    origin_main = _git(root, "rev-parse", "origin/main")
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    relation = _git(
        root, "rev-list", "--left-right", "--count", "HEAD...origin/main"
    ).split()
    if branch != "main" or len(relation) != 2 or any(
        not value.isdigit() for value in relation
    ):
        _fail("REPOSITORY_IDENTITY_OR_RELATION_INVALID")
    ahead, behind = (int(value) for value in relation)
    if profile == TRACKED_CLEAN:
        baseline_head = _git_is_ancestor(root, BASELINE_COMMIT, "HEAD")
        baseline_origin = _git_is_ancestor(root, BASELINE_COMMIT, "origin/main")
        origin_head = _git_is_ancestor(root, "origin/main", "HEAD")
        changed = set(
            filter(
                None,
                _git(
                    root, "diff", "--name-only", BASELINE_COMMIT + "..HEAD"
                ).splitlines(),
            )
        )
    else:
        baseline_head = baseline_origin = origin_head = True
        changed = set()
    validate_repository_relation_values(
        profile=profile,
        expected_paths=expected_paths,
        head=head,
        origin_main=origin_main,
        ahead=ahead,
        behind=behind,
        baseline_is_ancestor_of_head=baseline_head,
        baseline_is_ancestor_of_origin=baseline_origin,
        origin_is_ancestor_of_head=origin_head,
        changed_since_baseline=changed,
    )
    _validate_history_scope(changed)
    return {
        "branch": branch,
        "HEAD": head,
        "origin_main": origin_main,
        "ahead": ahead,
        "behind": behind,
        "changed_since_baseline": tuple(sorted(changed)),
    }


def _verify_repository(root: Path) -> dict[str, object]:
    observations = _repository_observations(root)
    expected_paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    profile = classify_repository_profile(
        expected_paths=expected_paths,
        tracked_paths=observations["tracked_paths"],  # type: ignore[arg-type]
        ordinary_untracked=observations["ordinary_untracked"],  # type: ignore[arg-type]
        status_lines=observations["status_lines"],  # type: ignore[arg-type]
        working_diff=observations["working_diff"],  # type: ignore[arg-type]
        cached_diff=observations["cached_diff"],  # type: ignore[arg-type]
    )
    relation = _verify_repository_relation(root, profile, set(expected_paths))
    return {
        **relation,
        "lifecycle": profile,
        "staged_count": 0,
        "tracked_modification_count": 0,
        "untracked_count": len(observations["ordinary_untracked"]),  # type: ignore[arg-type]
    }


def _verify_exact4_files(root: Path) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    for relative in subject.EXACT4_PATHS:
        path = root / relative
        payload = _read_regular(path, relative.as_posix())
        if len(payload) > MAX_FILE_BYTES:
            _fail("EXACT4_FILE_TOO_LARGE:" + relative.as_posix())
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("EXACT4_NOT_UTF8:" + relative.as_posix()) from error
        if text.startswith("\ufeff") or "\x00" in text or "\r" in text:
            _fail("EXACT4_TEXT_INVARIANT_INVALID:" + relative.as_posix())
        mode = stat.S_IMODE(path.lstat().st_mode)
        if mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            _fail("EXACT4_FILE_EXECUTABLE:" + relative.as_posix())
        reports.append(
            {
                "path": relative.as_posix(),
                "bytes": len(payload),
                "LOC": len(text.splitlines()),
                "SHA256": _sha256(payload),
                "git_mode": "100644",
            }
        )
    return reports


def _verify_dependencies(root: Path) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    for role, relative, expected_bytes, expected_sha in DEPENDENCY_BINDINGS:
        payload = _read_regular(root / relative, role)
        if len(payload) != expected_bytes or _sha256(payload) != expected_sha:
            _fail("PUBLISHED_DEPENDENCY_DRIFT:" + role)
        reports.append(
            {
                "role": role,
                "path": relative,
                "bytes": len(payload),
                "SHA256": _sha256(payload),
            }
        )
    return reports


def _strict_json(payload: bytes) -> dict[str, Any]:
    try:
        value = generic._strict_json_object(payload, "0D8_RECONCILIATION_ARTIFACT")
    except generic.CompletedDecisionReconciliationError as error:
        raise ValueError("ARTIFACT_JSON_INVALID:" + str(error)) from error
    return value


def _stable_identity(binding: dict[str, object]) -> str:
    return (
        str(binding["path_namespace"])
        + ":"
        + str(binding["source_path"])
        + "@"
        + str(binding["sha256"])
    )


def _verify_artifact_byte_identity(expected_payload: bytes, observed_payload: bytes) -> None:
    if observed_payload != expected_payload:
        _fail("MATERIALIZED_ARTIFACT_BYTES_MISMATCH")


def _verify_artifact_semantics(
    artifact: dict[str, Any],
    *,
    expected_predecessor_facts: list[dict[str, object]],
    expected_projection: list[dict[str, object]],
) -> dict[str, object]:
    """Validate structure and semantics independently of serialized bytes."""

    if tuple(artifact) != subject._ARTIFACT_FIELDS:
        _fail("ARTIFACT_TOP_LEVEL_SCHEMA_INVALID")
    bindings = artifact.get("source_bindings")
    facts = artifact.get("normalized_facts")
    rows = artifact.get("reconciled_rows")
    if not isinstance(bindings, list) or not isinstance(facts, list) or not isinstance(rows, list):
        _fail("ARTIFACT_COLLECTION_TYPE_INVALID")
    if len(bindings) != 22 or len(facts) != 131 or len(rows) != 338:
        _fail("ARTIFACT_EXACT_COUNTS_INVALID")
    if any(
        type(binding) is not dict
        or set(binding) != set(subject._SOURCE_BINDING_FIELDS)
        or binding.get("path_namespace") != "repository_parent_relative"
        or str(binding.get("source_path", "")).startswith("/")
        for binding in bindings
    ):
        _fail("ARTIFACT_SOURCE_BINDING_SCHEMA_OR_NAMESPACE_INVALID")
    identities = [_stable_identity(binding) for binding in bindings]
    review_units = [str(binding["review_unit_id"]) for binding in bindings]
    if len(set(identities)) != 22 or len(set(review_units)) != 22:
        _fail("ARTIFACT_SOURCE_IDENTITY_DUPLICATE")
    if any(
        type(fact) is not dict
        or set(fact) != set(subject._GENERIC_FACT_FIELDS)
        or subject._FORBIDDEN_RICH_FACT_FIELDS & set(fact)
        for fact in facts
    ):
        _fail("ARTIFACT_GENERIC_FACT_NOT_EXACT11")

    new_facts = facts[-4:]
    if facts[:127] != expected_predecessor_facts:
        _fail("PREDECESSOR_FACT_PREFIX_INVALID")
    if new_facts != expected_projection:
        _fail("0D8_FACTS_NOT_EXACT_INGESTION_PROJECTION")
    if any(
        fact.get("task_relevance_disposition") != generic.TASK_NOT_RELEVANT
        or fact.get("chemistry_disposition") != generic.CHEMISTRY_POSITIVE
        or fact.get("legacy_completed_review_status")
        != generic.COMPLETED_HUMAN_NEGATIVE
        or fact.get("training_disposition") != generic.TRAINING_NOT_APPLICABLE
        or fact.get("human_training_excluded") is not False
        for fact in new_facts
    ):
        _fail("0D8_CLASSIFICATION_OR_TRAINING_BOUNDARY_INVALID")
    if artifact.get("review_summary") != subject._SUCCESSOR_REVIEW_SUMMARY:
        _fail("ARTIFACT_GENERIC_REVIEW_SUMMARY_INVALID")
    return {
        "source_count": 22,
        "review_unit_count": 22,
        "stable_source_identity_count": 22,
        "accepted_fact_count": 131,
        "duplicate_count": 0,
        "source_namespace": "repository_parent_relative",
        "generic_fact_field_count": 11,
        "rich_key_leakage": False,
        "predecessor_prefix_count": 127,
        "0D8_appended_fact_count": 4,
    }


def _verify_coverage_contract() -> dict[str, object]:
    before = subject.PREDECESSOR_COVERAGE_SUMMARY
    after = subject.SUCCESSOR_COVERAGE_SUMMARY
    if before != EXPECTED_PREDECESSOR_COVERAGE or after != EXPECTED_SUCCESSOR_COVERAGE:
        _fail("COVERAGE_SUMMARY_CONTRACT_DRIFT")
    before_distribution = before["decision_category_distribution"]
    after_distribution = after["decision_category_distribution"]
    if not isinstance(before_distribution, dict) or not isinstance(after_distribution, dict):
        _fail("DECISION_DISTRIBUTION_NOT_OBJECT")
    if (
        sum(before_distribution.values()) != 127
        or sum(after_distribution.values()) != 131
        or after_distribution["task_domain_negative"]
        - before_distribution["task_domain_negative"]
        != 4
        or any(
            after_distribution[key] != before_distribution[key]
            for key in ("chemistry_positive", "chemistry_negative", "task_domain_positive")
        )
        or after["label_ready_event_count"] != before["label_ready_event_count"]
        or after["training_mask_target_count"] != 0
        or after["training_authority"] is not False
    ):
        _fail("COVERAGE_DELTA_NOT_EXACT_0D8_TASK_NEGATIVE_4")
    return {"predecessor": copy.deepcopy(before), "successor": copy.deepcopy(after)}


def _verify_upstream_0d8_boundary(bound: dict[str, object]) -> dict[str, object]:
    subject._validate_rich_0d8_boundary_v1(bound)
    formal = bound["formal"]
    tasks = formal["canonical_Exact5_and_sample_applicability"]
    d3 = formal["D3_formal_reactive_pair"]
    d4 = formal["D4_formal_role_partition"]
    d5 = formal["D5_formal_training_use"]
    return {
        "chemistry_positive_evidence": formal["D2_formal_chemistry"]["D2"] == "POSITIVE",
        "completed_lane": ingestion.EXPECTED_COMPLETED_LANE,
        "task": formal["D1_formal_task_relevance"]["D1"],
        "training": d5["D5"],
        "pair": d3["protein_atom"] + "-" + d3["ligand_atom"],
        "pair_authority_count": 4,
        "role_authority_count": 4,
        "role_profile": d4["role_profile"],
        "W": d4["W_atom_ids"],
        "L": d4["L_atom_ids"],
        "S": d4["S_atom_ids"],
        "canonical_task_count": tasks["global_task_count"],
        "B3_present": tasks["B3_present"],
        "sixth_task": tasks["sixth_task"],
        "applicable_task_ids": tasks["sample_applicable_task_ids"],
        "authoritative_task_labels_created": tasks["authoritative_task_labels_created"],
        "event_task_label_rows_materialized": tasks["event_task_label_rows_materialized"],
        "training_mask_targets_available": False,
        "formal_training_admitted": d5["formal_training_admitted"],
        "training_authority": False,
    }


def _expect_failure(callable_: object, token: str) -> str:
    try:
        callable_()  # type: ignore[operator]
    except ValueError as error:
        if token not in str(error):
            _fail("TAMPER_FAILURE_TOKEN_INVALID:" + token)
        return token
    _fail("TAMPER_PROBE_DID_NOT_FAIL:" + token)


def _verify_tamper_probes(
    artifact: dict[str, Any],
    *,
    expected_payload: bytes,
    expected_predecessor_facts: list[dict[str, object]],
    expected_projection: list[dict[str, object]],
) -> dict[str, str]:
    def verify(candidate: dict[str, Any]) -> None:
        _verify_artifact_semantics(
            candidate,
            expected_predecessor_facts=expected_predecessor_facts,
            expected_projection=expected_projection,
        )

    prefix = copy.deepcopy(artifact)
    prefix["normalized_facts"][0], prefix["normalized_facts"][1] = (
        prefix["normalized_facts"][1], prefix["normalized_facts"][0]
    )
    prefix_token = _expect_failure(
        lambda: verify(prefix), "PREDECESSOR_FACT_PREFIX_INVALID"
    )
    fact = copy.deepcopy(artifact)
    fact["normalized_facts"][-1]["chemistry_disposition"] = "NEGATIVE"
    fact_token = _expect_failure(
        lambda: verify(fact), "0D8_FACTS_NOT_EXACT_INGESTION_PROJECTION"
    )
    duplicate = copy.deepcopy(artifact)
    duplicate["source_bindings"][-1] = copy.deepcopy(duplicate["source_bindings"][0])
    duplicate_token = _expect_failure(
        lambda: verify(duplicate), "ARTIFACT_SOURCE_IDENTITY_DUPLICATE"
    )
    count = copy.deepcopy(artifact)
    count["normalized_facts"].pop()
    count_token = _expect_failure(
        lambda: verify(count), "ARTIFACT_EXACT_COUNTS_INVALID"
    )
    category = copy.deepcopy(artifact)
    category["normalized_facts"][-1]["task_relevance_disposition"] = "RELEVANT"
    category_token = _expect_failure(
        lambda: verify(category), "0D8_FACTS_NOT_EXACT_INGESTION_PROJECTION"
    )
    byte_token = _expect_failure(
        lambda: _verify_artifact_byte_identity(
            expected_payload, expected_payload + b" "
        ),
        "MATERIALIZED_ARTIFACT_BYTES_MISMATCH",
    )
    return {
        "predecessor_order_tamper": prefix_token,
        "0D8_fact_tamper": fact_token,
        "duplicate_source_tamper": duplicate_token,
        "count_tamper": count_token,
        "decision_category_tamper": category_token,
        "artifact_bytes_tamper": byte_token,
    }


def _verify_no_forbidden_or_large_files(root: Path) -> dict[str, object]:
    status_paths = [
        line[3:]
        for line in _git(root, "status", "--short", "--untracked-files=all").splitlines()
        if line
    ]
    forbidden = [path for path in status_paths if Path(path).suffix.lower() in FORBIDDEN_SUFFIXES]
    large = [path for path in status_paths if (root / path).stat().st_size > MAX_FILE_BYTES]
    if forbidden or large:
        _fail("FORBIDDEN_OR_LARGE_CANDIDATE_FILE")
    return {"forbidden_files": forbidden, "large_files": large}


def check_lifecycle_simulations() -> dict[str, bool]:
    """Prove supported publication states with pure lifecycle inputs."""

    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    expected = set(paths)
    if classify_repository_profile(
        expected_paths=paths,
        tracked_paths=set(),
        ordinary_untracked=expected,
        status_lines=tuple("?? " + path for path in paths),
        working_diff=set(),
        cached_diff=set(),
    ) != CANDIDATE_UNTRACKED:
        _fail("CANDIDATE_UNTRACKED_SIMULATION_FAILED")
    if classify_repository_profile(
        expected_paths=paths,
        tracked_paths=expected,
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    ) != TRACKED_CLEAN:
        _fail("TRACKED_CLEAN_SIMULATION_FAILED")
    for head, origin, ahead, changed in (
        ("publication-head", BASELINE_COMMIT, 1, expected),
        ("pushed-head", "pushed-head", 0, expected),
        ("later-head", "later-origin", 2, {*expected, "docs/later.md"}),
    ):
        validate_repository_relation_values(
            profile=TRACKED_CLEAN,
            expected_paths=expected,
            head=head,
            origin_main=origin,
            ahead=ahead,
            behind=0,
            baseline_is_ancestor_of_head=True,
            baseline_is_ancestor_of_origin=True,
            origin_is_ancestor_of_head=True,
            changed_since_baseline=changed,
        )
        _validate_history_scope(changed)
    return {
        "candidate_untracked": True,
        "tracked_clean": True,
        "committed_unpushed": True,
        "pushed_successor": True,
        "later_clean_descendant": True,
    }


def run_check_v1(repo_root: Path = ROOT) -> dict[str, object]:
    """Run the bounded, read-only 0D8 reconciliation gate."""

    root = Path(repo_root).resolve()
    repository = _verify_repository(root)
    exact4 = _verify_exact4_files(root)
    dependencies = _verify_dependencies(root)
    expected = subject.build_artifact_v1(root)
    observed = _read_regular(root / subject.OUTPUT_RELATIVE, "0D8_ARTIFACT")
    artifact = _strict_json(observed)
    expected_artifact = _strict_json(expected)
    expected_facts = expected_artifact.get("normalized_facts")
    if not isinstance(expected_facts, list) or len(expected_facts) != 131:
        _fail("REBUILT_EXPECTED_FACTS_INVALID")
    bound = ingestion.load_frozen_formal_decision_v1(root)
    expected_projection = [
        dict(record) for record in subject._projection_records_v1(bound)
    ]
    _verify_artifact_byte_identity(expected, observed)
    semantics = {
        **_verify_artifact_semantics(
            artifact,
            expected_predecessor_facts=expected_facts[:127],
            expected_projection=expected_projection,
        ),
        "artifact_bytes": len(observed),
        "artifact_SHA256": _sha256(observed),
    }
    coverage = _verify_coverage_contract()
    upstream = _verify_upstream_0d8_boundary(bound)
    tamper = _verify_tamper_probes(
        artifact,
        expected_payload=expected,
        expected_predecessor_facts=expected_facts[:127],
        expected_projection=expected_projection,
    )
    lifecycle_simulations = check_lifecycle_simulations()
    safety = _verify_no_forbidden_or_large_files(root)
    return {
        "status": "PASS",
        "repository": repository,
        "Exact4": exact4,
        "dependencies": dependencies,
        "artifact": semantics,
        "coverage": coverage,
        "0D8_boundary": upstream,
        "tamper_probes": tamper,
        "lifecycle_simulations": lifecycle_simulations,
        "safety": safety,
        "repo_root_global_ROOT_dependency_removed": True,
        "current_census_refresh": False,
        "queue_refresh": False,
        "formal_refresh": False,
        "scientific_state_refresh": False,
        "preparation_refresh": False,
        "preview_refresh": False,
        "training_started": False,
        "ready_for_training": False,
        "feature_semantics_audit_required_later": True,
        "commit": False,
        "push": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    report = run_check_v1(parser.parse_args(argv).repo_root)
    if (
        report["status"] != "PASS"
        or report["current_census_refresh"] is not False
        or report["queue_refresh"] is not False
        or report["training_started"] is not False
        or report["ready_for_training"] is not False
        or report["feature_semantics_audit_required_later"] is not True
        or report["commit"] is not False
        or report["push"] is not False
    ):
        _fail("FINAL_OPERATION_BOUNDARY_INVALID")
    print("PASS")
    for record in report["Exact4"]:
        print(
            "EXACT4 "
            f"path={record['path']} bytes={record['bytes']} LOC={record['LOC']} "
            f"SHA256={record['SHA256']} git_mode={record['git_mode']}"
        )
    print("0D8_RECONCILIATION_V1_PASS=true")
    print("0D8_RECONCILIATION_REVISED1_PASS=true")
    print("0D8_RECONCILIATION_EXACT4_LOCAL=true")
    print(f"CHECKER_LIFECYCLE_PROFILE={report['repository']['lifecycle']}")
    print("CHECKER_CANDIDATE_UNTRACKED_SUPPORTED=true")
    print("CHECKER_TRACKED_CLEAN_SUPPORTED=true")
    print("CHECKER_COMMITTED_UNPUSHED_SIMULATION_PASS=true")
    print("CHECKER_PUSHED_SUCCESSOR_SIMULATION_PASS=true")
    print("CHECKER_SEMANTIC_TAMPER_PROBES_REAL=true")
    print("CHECKER_BYTE_TAMPER_PROBE_SEPARATE=true")
    print("CHECKER_REPO_ROOT_CONSISTENT=true")
    print("0D8_GENERIC_FACTS_ADDED=4")
    print("0D8_GENERIC_TOTAL_ACCEPTED_FACTS=131")
    print("0D8_TASK_DOMAIN_NEGATIVE_DELTA=4")
    print("0D8_AUTHORITATIVE_TASK_LABELS_CREATED=false")
    print("0D8_EVENT_TASK_LABEL_ROWS_MATERIALIZED=false")
    print("0D8_TRAINING_MASK_TARGETS_AVAILABLE=false")
    print("EXACT5_B3_PRESENT=true")
    print("SIXTH_TASK=false")
    print("CURRENT_CENSUS_REFRESH=false")
    print("QUEUE_REFRESH=false")
    print("TRAINING_STARTED=false")
    print("READY_FOR_TRAINING=false")
    print("FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER=true")
    print("COMMIT=false")
    print("PUSH=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
