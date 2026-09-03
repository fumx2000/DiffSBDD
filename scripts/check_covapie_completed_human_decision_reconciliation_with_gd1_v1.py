#!/usr/bin/env python3
"""Read-only checker for the GD1 completed-decision reconciliation Exact4."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
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
    covapie_completed_human_decision_reconciliation_with_4m5_v1
    as four_m5_predecessor,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_gd1_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1
    as gd1_ingestion_owner,
)


BASELINE_COMMIT = "7857f129cec3af990b8f3a200df835bc606c463e"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_gd1_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_gd1_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_gd1_v1.py",
    "docs/"
    "covapie_completed_human_decision_reconciliation_with_gd1_v1_guide.md",
)
PURPOSES = {
    EXACT4_PATHS[0]: "rich GD1 validation, narrow projection, and reconciliation",
    EXACT4_PATHS[1]: "read-only candidate and semantic checker",
    EXACT4_PATHS[2]: "success and fail-closed targeted tests",
    EXACT4_PATHS[3]: "concise reconciliation boundary guide",
}
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWithGD1Error",
    "project_gd1_completed_decision_v1",
    "load_real_completed_decision_sources_with_gd1_v1",
    "reconcile_real_completed_human_decisions_with_gd1_v1",
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
FORBIDDEN_FACT_ATTRIBUTES = (
    "protein_reactive_atom",
    "ligand_reactive_atom",
    "role_profile",
    "selected_candidate",
    "warhead_atoms",
    "linker_atoms",
    "scaffold_atoms",
    "boundary_bonds",
    "canonical_mask_applicability",
    "PRE_geometry",
    "PRE_topology",
    "POST_geometry",
    "warhead_type",
    "reaction_family",
    "future_training_candidate",
    "training_admission",
    "tensor_target",
    "training_use_allowed",
    "training_materialization_allowed",
    "current_runtime_model_usable",
)
FROZEN_RUNTIME_LINEAGE = (
    (
        "GENERIC_RECONCILIATION_OWNER",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
    ),
    (
        "WITH_4M5_RECONCILIATION_PREDECESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_4m5_v1.py",
        34162,
        "e2fefef61382bfa3b716e83d8c09312f1d51f45f10d7bbdbd25c31adfc3aac02",
    ),
    (
        "GD1_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1.py",
        95722,
        "b9d87c844759ce5e6fd9b8aafb411854113fccb3ef00941b21f0eb79a4751670",
    ),
)
BEFORE_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 107,
    "completed_positive_unit_count": 16,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 135,
    "completed_total_unit_count": 21,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 203,
    "unreviewed_unit_count": 110,
}
AFTER_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 111,
    "completed_positive_unit_count": 17,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 139,
    "completed_total_unit_count": 22,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 199,
    "unreviewed_unit_count": 109,
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
    payload = _read_regular_file(root / EXACT4_PATHS[0], "GD1_RECONCILIATION")
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
        "covapie_completed_human_decision_reconciliation_with_4m5_v1",
        "covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1",
    }
    if imported_covapie != expected_imported:
        raise ValueError("RUNTIME_DEPENDENCY_GRAPH_INVALID")
    classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    if classes != {"CompletedDecisionReconciliationWithGD1Error"}:
        raise ValueError("GENERIC_SCHEMA_FORK_OR_EXTRA_CLASS_CREATED")
    calls = [
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    ]
    expected_calls = {
        "load_frozen_formal_decision_v1": 1,
        "load_real_completed_decision_sources_with_4m5_v1": 1,
        "reconcile_real_completed_human_decisions_with_4m5_v1": 1,
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
        "materialize_artifacts",
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
    if "formal_human_decision_v1.py" in text or "import subprocess" in text:
        raise ValueError("FROZEN_VALIDATOR_DEPENDENCY_FORBIDDEN")
    return {
        "public_api": subject.__all__,
        "runtime_dependencies": tuple(sorted(imported_covapie)),
        "generic_schema_forked": False,
        "generic_reconciler_forked": False,
        "production_side_effect_calls": 0,
        "formal_validator_imported": False,
        "formal_validator_executed": False,
        "formal_validator_subprocess": False,
    }


def _verify_rich_authority(bound: dict[str, object]) -> dict[str, object]:
    events = subject._validate_rich_gd1_semantics_v1(bound)
    formal = bound["formal"]
    if not isinstance(formal, dict):
        raise ValueError("FORMAL_NOT_OBJECT_AFTER_VALIDATION")
    role = formal["selected_role_partition"]
    training = formal["training_use_boundary"]
    pre = formal["PRE_POST_boundary"]
    post = formal["POST_evidence_boundary"]
    tasks = formal["canonical_Exact5_and_sample_applicability"]
    if not all(isinstance(value, dict) for value in (role, training, pre, post, tasks)):
        raise ValueError("RICH_AUTHORITY_SECTION_TYPE_INVALID")
    return {
        "event_count": len(events),
        "event_ids": tuple(event["canonical_event_id"] for event in events),
        "scaleup_ranks": tuple(event["scaleup_rank"] for event in events),
        "pair": "SG-C77",
        "role_profile": role["role_profile"],
        "W_L_S_counts": tuple(role["W_L_S_counts"]),
        "applicable_tasks": tuple(role["applicable_task_ids"]),
        "task_count": tasks["global_canonical_task_count"],
        "B3_present": tasks["B3_present"],
        "sixth_task_present": tasks["sixth_task_present"],
        "training_disposition": training["training_use_disposition"],
        "human_training_excluded": training["human_training_excluded"],
        "future_training_admission_candidate": training[
            "future_training_admission_candidate"
        ],
        "PRE_status": pre["PRE_status"],
        "POST_source_evidence_count": post["POST_source_evidence_count"],
    }


def _verify_projection(
    source: generic.NormalizedDecisionSource,
) -> dict[str, object]:
    subject._validate_projected_gd1_source_v1(source)
    if tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) != (
        EXPECTED_GENERIC_FACT_FIELDS
    ):
        raise ValueError("GENERIC_FACT_SCHEMA_NOT_EXACT11")
    if any(
        hasattr(fact, attribute)
        for fact in source.facts
        for attribute in FORBIDDEN_FACT_ATTRIBUTES
    ):
        raise ValueError("RICH_AUTHORITY_LEAKED_INTO_GENERIC_FACT")
    if any(
        fact.legacy_completed_review_status != generic.COMPLETED_HUMAN_POSITIVE
        or fact.training_disposition != generic.TRAINING_EXCLUDE
        or fact.human_training_excluded is not True
        for fact in source.facts
    ):
        raise ValueError("POSITIVE_EXCLUDED_GENERIC_PROJECTION_INVALID")
    if source.binding.source_path != (
        gd1_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()
    ):
        raise ValueError("GENERIC_AUTHORITY_NOT_FORMAL_JSON")
    return {
        "fact_count": len(source.facts),
        "generic_field_count": len(EXPECTED_GENERIC_FACT_FIELDS),
        "legacy_status": generic.COMPLETED_HUMAN_POSITIVE,
        "task_relevance": generic.TASK_RELEVANT,
        "chemistry": generic.CHEMISTRY_POSITIVE,
        "training_disposition": generic.TRAINING_EXCLUDE,
        "human_training_excluded": True,
        "authority_path": source.binding.source_path,
        "ingestion_snapshot_used_as_authority": False,
        "rich_authority_leakage": False,
    }


def _verify_sources(root: Path) -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    tuple[generic.NormalizedDecisionSource, ...],
]:
    before = four_m5_predecessor.load_real_completed_decision_sources_with_4m5_v1(
        root
    )
    after = subject.load_real_completed_decision_sources_with_gd1_v1(root)
    before_facts = [fact for source in before for fact in source.facts]
    after_facts = [fact for source in after for fact in source.facts]
    if (
        len(before) != 17
        or len(before_facts) != 111
        or len({source.binding.review_unit_id for source in before}) != 17
        or len({source.binding.stable_identity for source in before}) != 17
        or len(after) != 18
        or len(after_facts) != 115
        or len({source.binding.review_unit_id for source in after}) != 18
        or len({source.binding.stable_identity for source in after}) != 18
        or after[:-1] != before
        or len({fact.canonical_event_id for fact in after_facts}) != 115
    ):
        raise ValueError("SOURCE_CHAIN_17_111_TO_18_115_INVALID")
    return before, after


def _verify_reconciliation(
    root: Path,
) -> tuple[generic.ReconciliationResult, generic.ReconciliationResult]:
    before = (
        four_m5_predecessor.reconcile_real_completed_human_decisions_with_4m5_v1(
            root
        )
    )
    subject._prove_gd1_predecessor_historical_state_v1(before.reconciled_rows)
    after = subject.reconcile_real_completed_human_decisions_with_gd1_v1(root)
    subject._validate_reconciliation_delta_v1(before, after)
    if before.review_summary != BEFORE_SUMMARY or after.review_summary != AFTER_SUMMARY:
        raise ValueError("RECONCILIATION_SUMMARY_INVALID")
    return before, after


def _expect_subject_failure(callable_: object, token: str) -> None:
    try:
        callable_()  # type: ignore[operator]
    except subject.CompletedDecisionReconciliationWithGD1Error as error:
        if token not in str(error):
            raise ValueError("FAIL_CLOSED_TOKEN_INVALID:" + token) from error
        return
    raise ValueError("FAIL_CLOSED_PROBE_DID_NOT_FAIL:" + token)


def _verify_fail_closed_probes(
    bound: dict[str, object],
    projection: generic.NormalizedDecisionSource,
    before: generic.ReconciliationResult,
    after: generic.ReconciliationResult,
) -> dict[str, bool]:
    include = copy.deepcopy(bound)
    include_formal = include["formal"]
    if not isinstance(include_formal, dict):
        raise ValueError("FAIL_CLOSED_PROBE_FORMAL_NOT_OBJECT")
    include_training = include_formal["training_use_boundary"]
    if not isinstance(include_training, dict):
        raise ValueError("FAIL_CLOSED_PROBE_TRAINING_NOT_OBJECT")
    include_training["training_use_disposition"] = "INCLUDE"
    _expect_subject_failure(
        lambda: subject._validate_rich_gd1_semantics_v1(include),
        "GD1_RICH_TRAINING_EXCLUSION_BOUNDARY_INVALID",
    )
    not_excluded = copy.deepcopy(bound)
    excluded_formal = not_excluded["formal"]
    if not isinstance(excluded_formal, dict):
        raise ValueError("FAIL_CLOSED_PROBE_FORMAL_NOT_OBJECT")
    excluded_training = excluded_formal["training_use_boundary"]
    if not isinstance(excluded_training, dict):
        raise ValueError("FAIL_CLOSED_PROBE_TRAINING_NOT_OBJECT")
    excluded_training["human_training_excluded"] = False
    _expect_subject_failure(
        lambda: subject._validate_rich_gd1_semantics_v1(not_excluded),
        "GD1_RICH_TRAINING_EXCLUSION_BOUNDARY_INVALID",
    )
    negative = replace(
        projection.facts[0],
        legacy_completed_review_status=generic.COMPLETED_HUMAN_NEGATIVE,
    )
    _expect_subject_failure(
        lambda: subject._validate_projected_gd1_source_v1(
            replace(projection, facts=(negative, *projection.facts[1:]))
        ),
        "GD1_SOURCE_PROJECTION_INVALID",
    )
    snapshot_path = (
        "data/derived/covalent_small/"
        "covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1/"
        "covapie_gd1_completed_human_decision_snapshot_v1.json"
    )
    snapshot_binding = replace(projection.binding, source_path=snapshot_path)
    snapshot_facts = tuple(
        replace(fact, source_binding_path=snapshot_path) for fact in projection.facts
    )
    _expect_subject_failure(
        lambda: subject._validate_projected_gd1_source_v1(
            replace(projection, binding=snapshot_binding, facts=snapshot_facts)
        ),
        "GD1_SOURCE_PROJECTION_IDENTITY_INVALID",
    )
    rows = [dict(row) for row in after.reconciled_rows]
    rows[0]["fifth_changed_field"] = "forbidden"
    _expect_subject_failure(
        lambda: subject._validate_reconciliation_delta_v1(
            before, replace(after, reconciled_rows=tuple(rows))
        ),
        "GD1_RECONCILIATION_ROW_ORDER_OR_SCHEMA_CHANGED",
    )
    return {
        "training_include_rejected": True,
        "human_training_excluded_false_rejected": True,
        "legacy_negative_rejected": True,
        "ingestion_snapshot_authority_rejected": True,
        "fifth_row_field_rejected": True,
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
    forbidden_root = (
        root
        / "data/derived/covalent_small/"
        "covapie_completed_human_decision_reconciliation_with_gd1_v1"
    )
    if forbidden_root.exists():
        raise ValueError("MATERIALIZED_GD1_RECONCILIATION_ROOT_FORBIDDEN")
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
    """Run every read-only GD1 reconciliation candidate gate."""

    root = repo_root.resolve()
    exact4 = _verify_candidate_exact4(root)
    lineage = _verify_frozen_runtime_lineage(root)
    architecture = _verify_architecture(root)
    bound = gd1_ingestion_owner.load_frozen_formal_decision_v1(root)
    rich = _verify_rich_authority(bound)
    projection_source = subject._project_validated_gd1_binding_v1(bound)
    projection = _verify_projection(projection_source)
    before_sources, after_sources = _verify_sources(root)
    before, after = _verify_reconciliation(root)
    fail_closed = _verify_fail_closed_probes(
        bound, projection_source, before, after
    )
    lifecycle = check_lifecycle_simulations()
    _verify_no_outputs_or_transients(root)
    dispositions = Counter(
        fact.training_disposition for fact in projection_source.facts
    )
    return {
        "status": "PASS",
        "repository": exact4,
        "runtime_lineage": lineage,
        "architecture": architecture,
        "rich_GD1": rich,
        "projection": projection,
        "predecessor_source_count": len(before_sources),
        "successor_source_count": len(after_sources),
        "predecessor_fact_count": sum(
            len(source.facts) for source in before_sources
        ),
        "successor_fact_count": sum(len(source.facts) for source in after_sources),
        "review_unit_count": len(
            {source.binding.review_unit_id for source in after_sources}
        ),
        "stable_source_identity_count": len(
            {source.binding.stable_identity for source in after_sources}
        ),
        "event_collisions": 0,
        "GD1_changed_rows": 4,
        "non_GD1_unchanged_rows": 334,
        "review_summary": after.review_summary,
        "GD1_training_dispositions": dict(dispositions),
        "fail_closed": fail_closed,
        "lifecycle_simulations": lifecycle,
        "formal_validator_imported": False,
        "formal_validator_executed": False,
        "formal_validator_subprocess": False,
        "reconciliation_outputs_created": 0,
        "census_refresh": False,
        "queue_refresh": False,
        "training_started": False,
        "ready_for_training": False,
        "feature_semantics_audit_required_later": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    report = run_check_v1(parser.parse_args(argv).repo_root)
    if (
        report["ready_for_training"] is not False
        or report["census_refresh"] is not False
        or report["queue_refresh"] is not False
        or report["training_started"] is not False
        or report["formal_validator_imported"] is not False
        or report["formal_validator_executed"] is not False
        or report["formal_validator_subprocess"] is not False
    ):
        raise ValueError("OPERATION_BOUNDARY_INVALID")
    print("PASS")
    print(report["repository"]["lifecycle"])
    print("predecessor_sources=17 predecessor_facts=111")
    print("successor_sources=18 successor_facts=115 collisions=0")
    print("review_units=18 stable_source_identities=18")
    print("GD1_changed_rows=4 non_GD1_unchanged_rows=334")
    print("positive=111/17 negative=28/5 completed=139/22 unreviewed=199/109")
    print("legacy_status=COMPLETED_HUMAN_POSITIVE")
    print("training_disposition=EXCLUDE_FROM_TRAINING_ONLY")
    print("human_training_excluded=true")
    print("census_refresh=false queue_refresh=false training_started=false")
    print("READY_FOR_TRAINING=false FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
