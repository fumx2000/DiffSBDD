#!/usr/bin/env python3
"""Read-only checker for the LCY completed-decision reconciliation Exact4."""

from __future__ import annotations

import argparse
import ast
import copy
from dataclasses import replace
import hashlib
from pathlib import Path
import stat
import subprocess
import sys


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_gve_v1
    as gve_predecessor,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_lcy_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1
    as lcy_ingestion_owner,
)


BASELINE_COMMIT = "30fa9bba79deee92224b3f7594896b81707f56cf"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_lcy_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_lcy_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_lcy_v1.py",
    "docs/"
    "covapie_completed_human_decision_reconciliation_with_lcy_v1_guide.md",
)
PURPOSES = {
    EXACT4_PATHS[0]: "rich LCY validation, narrow projection, and reconciliation",
    EXACT4_PATHS[1]: "read-only candidate and semantic checker",
    EXACT4_PATHS[2]: "success and fail-closed targeted tests",
    EXACT4_PATHS[3]: "concise reconciliation boundary guide",
}
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWithLCYError",
    "project_lcy_completed_decision_v1",
    "load_real_completed_decision_sources_with_lcy_v1",
    "reconcile_real_completed_human_decisions_with_lcy_v1",
)
EXPECTED_GENERIC_FACT_FIELDS = (
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
FROZEN_RUNTIME_LINEAGE = (
    (
        "GENERIC_RECONCILIATION_OWNER",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
    ),
    (
        "WITH_GVE_RECONCILIATION_PREDECESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_gve_v1.py",
        34765,
        "a8c3eba54364b42fd5de918f65fec3273f7c8913c9cf9821fd5b4861d235d541",
    ),
    (
        "LCY_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1.py",
        101342,
        "380d3f0c8000bb1c1af404620430039dd87e41a0f10018bb83ee68e98a83de7c",
    ),
)
BEFORE_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 115,
    "completed_positive_unit_count": 18,
    "completed_negative_event_count": 32,
    "completed_negative_unit_count": 6,
    "completed_total_event_count": 147,
    "completed_total_unit_count": 24,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 191,
    "unreviewed_unit_count": 107,
}
AFTER_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 115,
    "completed_positive_unit_count": 18,
    "completed_negative_event_count": 36,
    "completed_negative_unit_count": 7,
    "completed_total_event_count": 151,
    "completed_total_unit_count": 25,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 187,
    "unreviewed_unit_count": 106,
}
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
    ".log",
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


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_regular_file(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("NOT_REGULAR_FILE:" + label)
    try:
        return path.read_bytes()
    except OSError as error:
        raise ValueError("READ_FAILED:" + label) from error


def _git(root: Path, *arguments: str) -> str:
    allowed = {
        "diff",
        "ls-files",
        "merge-base",
        "rev-list",
        "rev-parse",
        "status",
    }
    if not arguments or arguments[0] not in allowed:
        raise ValueError("GIT_SUBCOMMAND_FORBIDDEN")
    result = subprocess.run(
        ("git", *arguments),
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError("GIT_COMMAND_FAILED:" + arguments[0])
    return result.stdout.rstrip("\n")


def _git_is_ancestor(root: Path, older: str, newer: str) -> bool:
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer),
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise ValueError("GIT_ANCESTRY_CHECK_FAILED")
    return result.returncode == 0


def classify_repository_profile(
    *,
    expected_paths: tuple[str, ...],
    tracked_paths: set[str],
    ordinary_untracked: set[str],
    status_lines: tuple[str, ...],
    working_diff: set[str],
    cached_diff: set[str],
) -> str:
    """Classify strict untracked candidate or future-stable tracked-clean state."""

    expected = set(expected_paths)
    if len(expected_paths) != 4 or len(expected) != 4:
        raise ValueError("EXPECTED_INVENTORY_NOT_EXACT4")
    tracked_candidate = expected & tracked_paths
    if tracked_candidate and tracked_candidate != expected:
        raise ValueError("MIXED_TRACKING_STATE")
    if working_diff:
        raise ValueError("TRACKED_WORKTREE_MODIFICATION_PRESENT")
    if cached_diff:
        raise ValueError("STAGED_INDEX_CHANGE_PRESENT")
    if len(status_lines) != len(set(status_lines)):
        raise ValueError("DUPLICATE_STATUS_ENTRY")
    if not tracked_candidate:
        if ordinary_untracked != expected:
            raise ValueError("ORDINARY_UNTRACKED_NOT_STRICT_EXACT4")
        if set(status_lines) != {"?? " + path for path in expected}:
            raise ValueError("CANDIDATE_STATUS_NOT_STRICT_EXACT4")
        return CANDIDATE_UNTRACKED
    if ordinary_untracked or status_lines:
        raise ValueError("TRACKED_CLEAN_STATE_DIRTY")
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
    """Validate baseline ancestry without pinning a one-commit successor."""

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
            raise ValueError("CANDIDATE_BASELINE_RELATION_INVALID")
        return
    if profile != TRACKED_CLEAN:
        raise ValueError("REPOSITORY_PROFILE_INVALID")
    if (
        not baseline_is_ancestor_of_head
        or not baseline_is_ancestor_of_origin
        or not origin_is_ancestor_of_head
        or head == BASELINE_COMMIT
        or behind != 0
        or ahead < 0
        or not expected_paths <= changed_since_baseline
    ):
        raise ValueError("TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID")
    if (ahead == 0) != (origin_main == head):
        raise ValueError("TRACKED_CLEAN_ORIGIN_RELATION_INVALID")


def _repository_observations(root: Path) -> dict[str, object]:
    tracked = set(filter(None, _git(root, "ls-files").splitlines()))
    ordinary_untracked = set(
        filter(
            None,
            _git(root, "ls-files", "--others", "--exclude-standard").splitlines(),
        )
    )
    return {
        "tracked_paths": tracked,
        "ordinary_untracked": ordinary_untracked,
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
        raise ValueError("REPOSITORY_IDENTITY_OR_RELATION_INVALID")
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
    return {
        "branch": branch,
        "HEAD": head,
        "origin_main": origin_main,
        "ahead": ahead,
        "behind": behind,
    }


def _validate_text_payload(payload: bytes, label: str) -> None:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("EXACT4_NOT_UTF8:" + label) from error
    if (
        not payload
        or len(payload) >= MAX_FILE_BYTES
        or payload.startswith(b"\xef\xbb\xbf")
        or "\x00" in text
        or "\r" in text
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
        or any(line.endswith((" ", "\t")) for line in text.splitlines())
    ):
        raise ValueError("EXACT4_TEXT_HYGIENE_INVALID:" + label)


def _verify_candidate_exact4(root: Path) -> dict[str, object]:
    observations = _repository_observations(root)
    profile = classify_repository_profile(
        expected_paths=EXACT4_PATHS,
        tracked_paths=observations["tracked_paths"],  # type: ignore[arg-type]
        ordinary_untracked=observations["ordinary_untracked"],  # type: ignore[arg-type]
        status_lines=observations["status_lines"],  # type: ignore[arg-type]
        working_diff=observations["working_diff"],  # type: ignore[arg-type]
        cached_diff=observations["cached_diff"],  # type: ignore[arg-type]
    )
    relation = _verify_repository_relation(root, profile, set(EXACT4_PATHS))
    artifacts: list[dict[str, object]] = []
    for relative in EXACT4_PATHS:
        payload = _read_regular_file(root / relative, relative)
        _validate_text_payload(payload, relative)
        executable = bool(
            (root / relative).stat().st_mode
            & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        )
        if executable:
            raise ValueError("EXACT4_EXECUTABLE_CLASS_INVALID:" + relative)
        artifacts.append(
            {
                "path": relative,
                "bytes": len(payload),
                "LOC": len(payload.decode("utf-8").splitlines()),
                "SHA256": _sha256(payload),
                "mode_class": "NON_EXECUTABLE",
                "purpose": PURPOSES[relative],
            }
        )
    dirty_paths = {
        *observations["ordinary_untracked"],  # type: ignore[misc]
        *observations["working_diff"],  # type: ignore[misc]
        *observations["cached_diff"],  # type: ignore[misc]
    }
    forbidden = sorted(
        path for path in dirty_paths if Path(path).suffix.lower() in FORBIDDEN_SUFFIXES
    )
    protected = sorted(
        path
        for path in dirty_paths
        if path in PROTECTED_FILES
        or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)
    )
    if forbidden:
        raise ValueError("FORBIDDEN_DIRTY_PATH:" + forbidden[0])
    if protected:
        raise ValueError("PROTECTED_DIRTY_PATH:" + protected[0])
    return {
        "candidate_file_count": len(artifacts),
        "lifecycle": profile,
        "artifacts": tuple(artifacts),
        **relation,
    }


def _verify_frozen_runtime_lineage(root: Path) -> tuple[dict[str, object], ...]:
    records: list[dict[str, object]] = []
    for label, relative, expected_bytes, expected_sha in FROZEN_RUNTIME_LINEAGE:
        payload = _read_regular_file(root / relative, label)
        if len(payload) != expected_bytes or _sha256(payload) != expected_sha:
            raise ValueError("FROZEN_RUNTIME_LINEAGE_DRIFT:" + label)
        records.append(
            {
                "label": label,
                "path": relative,
                "bytes": expected_bytes,
                "SHA256": expected_sha,
            }
        )
    return tuple(records)


def _verify_architecture(root: Path) -> dict[str, object]:
    if subject.__all__ != EXPECTED_PUBLIC_API:
        raise ValueError("PUBLIC_API_NOT_EXACT4")
    payload = _read_regular_file(root / EXACT4_PATHS[0], "LCY_RECONCILIATION")
    tree = ast.parse(payload)
    imported_covapie = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
        if alias.name.startswith("covapie_")
    }
    expected_imported = {
        "covapie_completed_human_decision_reconciliation_v1",
        "covapie_completed_human_decision_reconciliation_with_gve_v1",
        "covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1",
    }
    if imported_covapie != expected_imported:
        raise ValueError("RUNTIME_DEPENDENCY_GRAPH_INVALID")
    classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    if classes != {"CompletedDecisionReconciliationWithLCYError"}:
        raise ValueError("GENERIC_SCHEMA_FORK_OR_EXTRA_CLASS_CREATED")
    calls = [
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    ]
    expected_calls = {
        "load_frozen_formal_decision_v1": 1,
        "load_real_completed_decision_sources_with_gve_v1": 1,
        "reconcile_real_completed_human_decisions_with_gve_v1": 1,
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1": 1,
        "reconcile_completed_human_decisions_v1": 1,
    }
    if any(calls.count(name) != count for name, count in expected_calls.items()):
        raise ValueError("RUNTIME_DELEGATE_CALL_GRAPH_INVALID")
    forbidden_calls = {
        "open",
        "write",
        "write_bytes",
        "write_text",
        "mkdir",
        "makedirs",
        "materialize_artifacts_v1",
        "refresh_census",
        "run",
        "Popen",
        "check_call",
        "check_output",
        "urlopen",
    }
    if forbidden_calls & set(calls):
        raise ValueError("PRODUCTION_SIDE_EFFECT_CALL_FORBIDDEN")
    text = payload.decode("utf-8")
    if "validate_lcy_formal_human_decision_v1" in text or "import subprocess" in text:
        raise ValueError("FROZEN_VALIDATOR_DEPENDENCY_FORBIDDEN")
    return {
        "public_api": subject.__all__,
        "runtime_dependencies": tuple(sorted(imported_covapie)),
        "generic_schema_forked": False,
        "generic_reconciler_forked": False,
        "production_side_effect_calls": 0,
        "formal_validator_imported": False,
        "formal_validator_parsed": False,
        "formal_validator_executed": False,
        "formal_validator_subprocessed": False,
        "formal_validator_runtime_dependency": False,
    }


def _verify_rich_authority(bound: dict[str, object]) -> dict[str, object]:
    events = subject._validate_rich_lcy_semantics_v1(bound)
    formal = bound["formal"]
    if not isinstance(formal, dict):
        raise ValueError("FORMAL_NOT_OBJECT_AFTER_VALIDATION")
    pair = formal["sample_reactive_pair"]
    role = formal["D4_role_boundary"]
    training = formal["training_boundary"]
    pre = formal["PRE_boundary"]
    post = formal["POST_boundary"]
    authority = formal["formal_authority_boundary"]
    if not all(
        isinstance(value, dict)
        for value in (pair, role, training, pre, post, authority)
    ):
        raise ValueError("RICH_AUTHORITY_SECTION_TYPE_INVALID")
    return {
        "event_count": len(events),
        "event_ids": tuple(event["canonical_event_id"] for event in events),
        "scaleup_ranks": tuple(event["scaleup_rank"] for event in events),
        "completed_lane": lcy_ingestion_owner.EXPECTED_COMPLETED_LANE,
        "pair": "SG-C1",
        "pair_authority_scope": pair["authority_scope"],
        "role_profile": role["role_profile"],
        "review_policy_candidate_count": role["review_policy_candidate_count"],
        "formal_valid_singleton_diagnostic_count": role[
            "formal_valid_singleton_diagnostic_count"
        ],
        "role_partition_sample_authority": role[
            "role_partition_sample_authority"
        ],
        "task_applicability_sample_authority": role[
            "task_applicability_sample_authority"
        ],
        "authority_true_set": authority["formal_authority_true_set"],
        "training_disposition": training["training_use_disposition"],
        "human_training_excluded": training["human_training_excluded"],
        "formal_training_admitted": training["formal_training_admitted"],
        "PRE_status": pre["PRE_status"],
        "POST_source_evidence_count": post["POST_source_evidence_count"],
        "chemistry_positive_but_task_domain_negative": True,
        "same_component_3A2G_authority_transferred": False,
    }


def _verify_projection(
    source: generic.NormalizedDecisionSource,
) -> dict[str, object]:
    subject._validate_projected_lcy_source_v1(source)
    if tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) != (
        EXPECTED_GENERIC_FACT_FIELDS
    ):
        raise ValueError("GENERIC_FACT_SCHEMA_NOT_EXACT11")
    if any(
        hasattr(fact, attribute)
        for fact in source.facts
        for attribute in subject._FORBIDDEN_GENERIC_FACT_ATTRIBUTES
    ):
        raise ValueError("RICH_AUTHORITY_LEAKED_INTO_GENERIC_FACT")
    if any(
        fact.legacy_completed_review_status != generic.COMPLETED_HUMAN_NEGATIVE
        or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
        or fact.human_training_excluded is not False
        for fact in source.facts
    ):
        raise ValueError("LCY_GENERIC_PROJECTION_INVALID")
    if (
        source.binding.source_path
        != lcy_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()
        or source.binding.path_namespace != "repository_parent_relative"
    ):
        raise ValueError("GENERIC_AUTHORITY_NOT_REPOSITORY_PARENT_FORMAL_JSON")
    return {
        "fact_count": len(source.facts),
        "generic_field_count": len(EXPECTED_GENERIC_FACT_FIELDS),
        "legacy_status": generic.COMPLETED_HUMAN_NEGATIVE,
        "task_relevance": generic.TASK_NOT_RELEVANT,
        "chemistry": generic.CHEMISTRY_POSITIVE,
        "training_disposition": generic.TRAINING_NOT_APPLICABLE,
        "human_training_excluded": False,
        "authority_path": source.binding.source_path,
        "authority_namespace": source.binding.path_namespace,
        "authority_sha256": source.binding.sha256,
        "authority_schema": source.binding.schema_version,
        "rich_authority_leakage": False,
    }


def _verify_sources(
    root: Path,
) -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    tuple[generic.NormalizedDecisionSource, ...],
]:
    after = subject.load_real_completed_decision_sources_with_lcy_v1(root)
    before = after[:-1]
    before_facts = [fact for source in before for fact in source.facts]
    after_facts = [fact for source in after for fact in source.facts]
    if (
        len(before) != 20
        or len(before_facts) != 123
        or len({source.binding.review_unit_id for source in before}) != 20
        or len({source.binding.stable_identity for source in before}) != 20
        or len(after) != 21
        or len(after_facts) != 127
        or len({source.binding.review_unit_id for source in after}) != 21
        or len({source.binding.stable_identity for source in after}) != 21
        or after[:-1] != before
        or len({fact.canonical_event_id for fact in after_facts}) != 127
        or after[-1].binding.review_unit_id
        != lcy_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
        or any(
            fact.canonical_event_id == subject._SAME_COMPONENT_3A2G_EVENT_ID
            for fact in after_facts
        )
    ):
        raise ValueError("SOURCE_CHAIN_20_123_TO_21_127_INVALID")
    return before, after


def _verify_reconciliation(
    root: Path,
) -> tuple[generic.ReconciliationResult, generic.ReconciliationResult]:
    before = gve_predecessor.reconcile_real_completed_human_decisions_with_gve_v1(
        root
    )
    subject._prove_lcy_predecessor_historical_state_v1(before.reconciled_rows)
    after = subject.reconcile_real_completed_human_decisions_with_lcy_v1(root)
    subject._validate_reconciliation_delta_v1(before, after)
    if before.review_summary != BEFORE_SUMMARY or after.review_summary != AFTER_SUMMARY:
        raise ValueError("RECONCILIATION_SUMMARY_INVALID")
    before_3a2g = [
        row
        for row in before.reconciled_rows
        if row["canonical_event_id"] == subject._SAME_COMPONENT_3A2G_EVENT_ID
    ]
    after_3a2g = [
        row
        for row in after.reconciled_rows
        if row["canonical_event_id"] == subject._SAME_COMPONENT_3A2G_EVENT_ID
    ]
    if len(before_3a2g) != 1 or before_3a2g != after_3a2g:
        raise ValueError("LCY_3A2G_HISTORICAL_NON_TARGET_GUARD_INVALID")
    return before, after


def _expect_subject_failure(callable_: object, token: str) -> None:
    try:
        callable_()  # type: ignore[operator]
    except subject.CompletedDecisionReconciliationWithLCYError as error:
        if token not in str(error):
            raise ValueError("FAIL_CLOSED_TOKEN_INVALID:" + token) from error
        return
    raise ValueError("FAIL_CLOSED_PROBE_DID_NOT_FAIL:" + token)


def _mutate_formal(
    bound: dict[str, object], section: str, key: str, value: object
) -> dict[str, object]:
    candidate = copy.deepcopy(bound)
    formal = candidate["formal"]
    if not isinstance(formal, dict):
        raise ValueError("FAIL_CLOSED_FORMAL_NOT_OBJECT")
    target = formal[section]
    if not isinstance(target, dict):
        raise ValueError("FAIL_CLOSED_SECTION_NOT_OBJECT")
    target[key] = value
    return candidate


def _verify_fail_closed_probes(
    bound: dict[str, object],
    projection: generic.NormalizedDecisionSource,
    before: generic.ReconciliationResult,
    after: generic.ReconciliationResult,
) -> dict[str, bool]:
    probes = (
        (
            "inherited_human_scientific_decision",
            "D1_task_relevance",
            "RELEVANT",
            "LCY_D1_D5",
        ),
        (
            "inherited_human_scientific_decision",
            "D2_chemistry",
            "NEGATIVE",
            "LCY_D1_D5",
        ),
        (
            "inherited_human_scientific_decision",
            "D4_role_candidate",
            "SELECT_CANDIDATE_0",
            "LCY_D1_D5",
        ),
        (
            "inherited_human_scientific_decision",
            "D5_training_use",
            "INCLUDE",
            "LCY_D1_D5",
        ),
        (
            "sample_reactive_pair",
            "ligand_reactive_atom",
            "C2",
            "LCY_SG_C1",
        ),
        (
            "D4_role_boundary",
            "role_partition_sample_authority",
            True,
            "LCY_UNRESOLVED_ROLE",
        ),
        (
            "training_boundary",
            "human_training_excluded",
            True,
            "LCY_TRAINING_NOT_APPLICABLE",
        ),
        (
            "PRE_boundary",
            "PRE_status",
            "PRE_REACTION_RESOLVED",
            "LCY_PRE_UNRESOLVED",
        ),
        (
            "same_component_3A2G_boundary",
            "pair_promoted",
            True,
            "LCY_3A2G_AUTHORITY_TRANSFER",
        ),
        (
            "downstream_operations",
            "census_refresh",
            True,
            "LCY_UNAUTHORIZED_DOWNSTREAM",
        ),
        (
            "downstream_operations",
            "queue_refresh",
            True,
            "LCY_UNAUTHORIZED_DOWNSTREAM",
        ),
        (
            "downstream_operations",
            "training",
            True,
            "LCY_UNAUTHORIZED_DOWNSTREAM",
        ),
    )
    for section, key, value, token in probes:
        _expect_subject_failure(
            lambda section=section, key=key, value=value: (
                subject._validate_rich_lcy_semantics_v1(
                    _mutate_formal(bound, section, key, value)
                )
            ),
            token,
        )

    fifth = copy.deepcopy(bound)
    fifth_formal = fifth["formal"]
    if not isinstance(fifth_formal, dict):
        raise ValueError("FAIL_CLOSED_FORMAL_NOT_OBJECT")
    fifth_events = fifth_formal["event_level_formal_decisions"]
    if not isinstance(fifth_events, list):
        raise ValueError("FAIL_CLOSED_EVENTS_NOT_LIST")
    fifth_events.append(copy.deepcopy(fifth_events[-1]))
    fifth_formal["event_level_formal_decision_count"] = 5
    _expect_subject_failure(
        lambda: subject._validate_rich_lcy_semantics_v1(fifth),
        "LCY_FORMAL_EVENT_COVERAGE_NOT_EXACT4",
    )

    fact_mutations = (
        {"legacy_completed_review_status": "COMPLETED_TASK_DOMAIN_NEGATIVE"},
        {"legacy_completed_review_status": generic.COMPLETED_HUMAN_POSITIVE},
        {"task_relevance_disposition": generic.TASK_RELEVANT},
        {"chemistry_disposition": generic.CHEMISTRY_NOT_ESTABLISHED},
        {"chemistry_disposition": generic.CHEMISTRY_NEGATIVE},
        {"training_disposition": generic.TRAINING_INCLUDE},
        {"training_disposition": generic.TRAINING_EXCLUDE},
        {"human_training_excluded": True},
    )
    for changes in fact_mutations:
        changed = replace(projection.facts[0], **changes)
        _expect_subject_failure(
            lambda changed=changed: subject._validate_projected_lcy_source_v1(
                replace(projection, facts=(changed, *projection.facts[1:]))
            ),
            "LCY_SOURCE_PROJECTION_INVALID",
        )
    wrong_namespace = replace(
        projection.binding, path_namespace="project_parent_relative"
    )
    _expect_subject_failure(
        lambda: subject._validate_projected_lcy_source_v1(
            replace(projection, binding=wrong_namespace)
        ),
        "LCY_SOURCE_PROJECTION_IDENTITY_INVALID",
    )

    non_target_rows = [dict(row) for row in after.reconciled_rows]
    non_target_rows[0]["calibration_eligible"] = (
        "true"
        if non_target_rows[0]["calibration_eligible"] == "false"
        else "false"
    )
    _expect_subject_failure(
        lambda: subject._validate_reconciliation_delta_v1(
            before, replace(after, reconciled_rows=tuple(non_target_rows))
        ),
        "LCY_NON_TARGET_ROW_CHANGED",
    )
    fifth_field_rows = [dict(row) for row in after.reconciled_rows]
    fifth_field_rows[0]["fifth_field"] = "forbidden"
    _expect_subject_failure(
        lambda: subject._validate_reconciliation_delta_v1(
            before, replace(after, reconciled_rows=tuple(fifth_field_rows))
        ),
        "LCY_RECONCILIATION_ROW_ORDER_OR_SCHEMA_CHANGED",
    )
    return {
        "D1_D5_mutations_rejected": True,
        "pair_and_role_mutations_rejected": True,
        "training_boundary_mutations_rejected": True,
        "PRE_resolution_rejected": True,
        "fifth_event_rejected": True,
        "completed_lane_leak_rejected": True,
        "chemistry_collapse_rejected": True,
        "training_disposition_drift_rejected": True,
        "human_training_excluded_true_rejected": True,
        "wrong_namespace_rejected": True,
        "non_LCY_mutation_rejected": True,
        "fifth_reconciliation_field_rejected": True,
        "3A2G_authority_transfer_rejected": True,
        "census_queue_training_operations_rejected": True,
    }


def check_lifecycle_simulations() -> dict[str, bool]:
    expected = set(EXACT4_PATHS)
    if classify_repository_profile(
        expected_paths=EXACT4_PATHS,
        tracked_paths=set(),
        ordinary_untracked=expected,
        status_lines=tuple("?? " + path for path in EXACT4_PATHS),
        working_diff=set(),
        cached_diff=set(),
    ) != CANDIDATE_UNTRACKED:
        raise ValueError("CANDIDATE_LIFECYCLE_SIMULATION_FAILED")
    if classify_repository_profile(
        expected_paths=EXACT4_PATHS,
        tracked_paths=expected,
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    ) != TRACKED_CLEAN:
        raise ValueError("TRACKED_LIFECYCLE_SIMULATION_FAILED")
    for head, origin, ahead, changed in (
        ("head-1", BASELINE_COMMIT, 1, expected),
        ("head-2", "head-2", 0, expected),
        ("head-3", "origin-2", 3, {*expected, "docs/later.md"}),
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
    return {
        "candidate_untracked": True,
        "committed_unpushed": True,
        "pushed": True,
        "multiple_later_commits": True,
        "unrelated_later_paths": True,
        "origin_between_baseline_and_head": True,
    }


def _verify_no_outputs_or_transients(root: Path) -> None:
    forbidden_roots = (
        root
        / "data/derived/covalent_small/"
        "covapie_completed_human_decision_reconciliation_with_lcy_v1",
        root / "data/derived/covalent_small/with_lcy_reconciliation",
    )
    if any(path.exists() for path in forbidden_roots):
        raise ValueError("MATERIALIZED_LCY_RECONCILIATION_ROOT_FORBIDDEN")
    ignored = set(
        filter(
            None,
            _git(
                root,
                "ls-files",
                "--others",
                "--ignored",
                "--exclude-standard",
            ).splitlines(),
        )
    )
    transient = sorted(
        path
        for path in ignored
        if "__pycache__" in path.split("/")
        or ".pytest_cache" in path.split("/")
        or Path(path).suffix.lower() in {".pyc", ".tmp", ".part", ".log"}
    )
    if transient:
        raise ValueError("TRANSIENT_OR_FORBIDDEN_FILE_PRESENT:" + transient[0])


def run_check_v1(repo_root: Path = ROOT) -> dict[str, object]:
    """Run every read-only LCY reconciliation candidate gate."""

    root = repo_root.resolve()
    exact4 = _verify_candidate_exact4(root)
    lineage = _verify_frozen_runtime_lineage(root)
    architecture = _verify_architecture(root)
    bound = lcy_ingestion_owner.load_frozen_formal_decision_v1(root)
    rich = _verify_rich_authority(bound)
    projection_source = subject._project_validated_lcy_binding_v1(bound)
    projection = _verify_projection(projection_source)
    before_sources, after_sources = _verify_sources(root)
    before, after = _verify_reconciliation(root)
    fail_closed = _verify_fail_closed_probes(
        bound, projection_source, before, after
    )
    lifecycle = check_lifecycle_simulations()
    _verify_no_outputs_or_transients(root)
    return {
        "status": "PASS",
        "repository": exact4,
        "runtime_lineage": lineage,
        "architecture": architecture,
        "rich_LCY": rich,
        "projection": projection,
        "predecessor_source_count": len(before_sources),
        "successor_source_count": len(after_sources),
        "predecessor_fact_count": sum(
            len(source.facts) for source in before_sources
        ),
        "successor_fact_count": sum(len(source.facts) for source in after_sources),
        "review_unit_identity_count": len(
            {source.binding.review_unit_id for source in after_sources}
        ),
        "stable_source_identity_count": len(
            {source.binding.stable_identity for source in after_sources}
        ),
        "event_collision_count": 0,
        "review_unit_collision_count": 0,
        "stable_source_collision_count": 0,
        "LCY_changed_rows": 4,
        "non_LCY_unchanged_rows": 334,
        "allowed_changed_field_count": 4,
        "before_review_summary": before.review_summary,
        "after_review_summary": after.review_summary,
        "historical_raw_priority_rank": 24,
        "historical_raw_unit_event_count": 4,
        "historical_3A2G_event_count": 1,
        "fail_closed": fail_closed,
        "lifecycle_simulations": lifecycle,
        "reconciliation_complete_in_memory": True,
        "reconciliation_outputs_created": 0,
        "census_refresh": False,
        "queue_refresh": False,
        "training_started": False,
        "ready_for_training": False,
        "feature_semantics_audit_required_later": True,
        "ready_for_external_review": True,
        "commit": False,
        "push": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    report = run_check_v1(parser.parse_args(argv).repo_root)
    if (
        report["status"] != "PASS"
        or report["ready_for_external_review"] is not True
        or report["ready_for_training"] is not False
        or report["census_refresh"] is not False
        or report["queue_refresh"] is not False
        or report["training_started"] is not False
        or report["reconciliation_complete_in_memory"] is not True
        or report["reconciliation_outputs_created"] != 0
        or report["feature_semantics_audit_required_later"] is not True
        or report["commit"] is not False
        or report["push"] is not False
    ):
        raise ValueError("OPERATION_OR_READINESS_BOUNDARY_INVALID")
    repository = report["repository"]
    if not isinstance(repository, dict):
        raise ValueError("REPOSITORY_REPORT_INVALID")
    print("PASS")
    print(repository["lifecycle"])
    for artifact in repository["artifacts"]:
        print(
            "EXACT4 "
            f"path={artifact['path']} bytes={artifact['bytes']} "
            f"LOC={artifact['LOC']} SHA256={artifact['SHA256']} "
            f"mode_class={artifact['mode_class']}"
        )
    print("WITH_LCY_RECONCILIATION_CANDIDATE_PASS=true")
    print("WITH_LCY_GENERIC_EXACT11_SCHEMA_UNCHANGED=true")
    print("LCY_GENERIC_SOURCE_PROJECTED=true")
    print("LCY_GENERIC_SOURCE_NAMESPACE_REPOSITORY_PARENT_RELATIVE=true")
    print("LCY_GENERIC_FACT_COUNT_4=true")
    print("LCY_TASK_NOT_RELEVANT=true")
    print("LCY_CHEMISTRY_POSITIVE=true")
    print("LCY_TRAINING_NOT_APPLICABLE=true")
    print("LCY_HUMAN_TRAINING_EXCLUDED=false")
    print("LCY_RICH_AUTHORITY_LEAKAGE_TO_GENERIC=false")
    print("PREDECESSOR_SOURCE_CHAIN_20_123=true")
    print("SUCCESSOR_SOURCE_CHAIN_21_127=true")
    print("LCY_EVENT_COLLISION_COUNT_0=true")
    print("LCY_REVIEW_UNIT_COLLISION_COUNT_0=true")
    print("LCY_STABLE_SOURCE_COLLISION_COUNT_0=true")
    print("LCY_RECONCILIATION_CHANGED_ROWS_4=true")
    print("NON_LCY_RECONCILIATION_ROWS_UNCHANGED_334=true")
    print("LCY_RECONCILIATION_CHANGED_FIELDS_EXACT4=true")
    print("BEFORE_COMPLETED_POSITIVE_115_18=true")
    print("BEFORE_COMPLETED_NEGATIVE_32_6=true")
    print("BEFORE_COMPLETED_TOTAL_147_24=true")
    print("BEFORE_UNREVIEWED_191_107=true")
    print("COMPLETED_POSITIVE_115_18=true")
    print("COMPLETED_NEGATIVE_36_7=true")
    print("COMPLETED_TOTAL_151_25=true")
    print("UNREVIEWED_187_106=true")
    print("IN_PROGRESS_0_0=true")
    print("LCY_TASK_NEGATIVE_CHEMISTRY_POSITIVE_ORTHOGONALITY=true")
    print("LCY_3A2G_AUTHORITY_TRANSFERRED=false")
    print("RECONCILIATION_MATERIALIZED=false")
    print("CENSUS_REFRESH=false")
    print("QUEUE_REFRESH=false")
    print("TRAINING_STARTED=false")
    print("READY_FOR_TRAINING=false")
    print("FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER=true")
    print("READY_FOR_EXTERNAL_REVIEW=true")
    print("COMMIT=false")
    print("PUSH=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
