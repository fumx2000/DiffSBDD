#!/usr/bin/env python3
"""Read-only checker for the CER completed-decision reconciliation Exact4."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import copy
from dataclasses import fields
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_cer_completed_decision_ingestion_and_task_label_availability_v1
    as cer_ingestion_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_1n0_v1
    as one_n0_predecessor,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_cer_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_onl_v1
    as onl_successor,
)
from covalent_ext import (  # noqa: E402
    covapie_source_binding_future_exact_posix_mode_guard_v2 as b4_guard,
)


BASELINE_COMMIT = "08b1b6517af1404066ec0a01af7752564b9af006"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_cer_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_cer_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_cer_v1.py",
    "docs/"
    "covapie_completed_human_decision_reconciliation_with_cer_v1_guide.md",
)
PURPOSES = {
    EXACT4_PATHS[0]: "rich CER validation, narrow projection, and reconciliation",
    EXACT4_PATHS[1]: "read-only candidate and semantic checker",
    EXACT4_PATHS[2]: "success and fail-closed targeted tests",
    EXACT4_PATHS[3]: "concise reconciliation boundary guide",
}
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWithCERError",
    "project_cer_completed_decision_v1",
    "load_real_completed_decision_sources_with_cer_v1",
    "reconcile_real_completed_human_decisions_with_cer_v1",
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
    "POST_geometry",
    "warhead_type",
    "reaction_family",
    "future_training_candidate",
    "training_admission",
)
PREDECESSOR_SOURCE_FACT_COUNTS = (
    8,
    16,
    8,
    9,
    8,
    8,
    8,
    7,
    6,
    5,
    4,
    4,
    4,
    4,
    4,
)
SUCCESSOR_SOURCE_FACT_COUNTS = (*PREDECESSOR_SOURCE_FACT_COUNTS, 4)
BEFORE_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 99,
    "completed_positive_unit_count": 14,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 127,
    "completed_total_unit_count": 19,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 211,
    "unreviewed_unit_count": 112,
}
AFTER_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 103,
    "completed_positive_unit_count": 15,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 131,
    "completed_total_unit_count": 20,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 207,
    "unreviewed_unit_count": 111,
}
FROZEN_RUNTIME_LINEAGE = (
    (
        "GENERIC_RECONCILIATION_OWNER",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
    ),
    (
        "ONL_NORMALIZATION_OWNER",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_onl_v1.py",
        13046,
        "f2c94ac8b4fe8f3706d0de288e2d5bb24ef211cf56d39e8362b43bdb17a2f475",
    ),
    (
        "WITH_1N0_RECONCILIATION_PREDECESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_1n0_v1.py",
        24762,
        "86e722b46a1ad4c25c0c3c9c8de2f48461ff7153e2b6bbd7c901dfcd338e5af8",
    ),
    (
        "CER_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_cer_completed_decision_ingestion_and_task_label_availability_v1.py",
        81662,
        "bc190935f661cd94e7dd5cf4f48782d6c99fba4455224ef3c73a3d1411b84e54",
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
                _git(
                    root, "status", "--short", "--untracked-files=all"
                ).splitlines(),
            )
        ),
        "working_diff": set(
            filter(None, _git(root, "diff", "--name-only").splitlines())
        ),
        "cached_diff": set(
            filter(
                None,
                _git(root, "diff", "--cached", "--name-only").splitlines(),
            )
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
                    root,
                    "diff",
                    "--name-only",
                    BASELINE_COMMIT + "..HEAD",
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
    large = sorted(
        path
        for path in observations["ordinary_untracked"]  # type: ignore[union-attr]
        if (root / path).is_file() and (root / path).stat().st_size > MAX_FILE_BYTES
    )
    if forbidden:
        raise ValueError("FORBIDDEN_DIRTY_PATH:" + forbidden[0])
    if protected:
        raise ValueError("PROTECTED_DIRTY_PATH:" + protected[0])
    if large:
        raise ValueError("UNEXPECTED_LARGE_UNTRACKED_FILE:" + large[0])
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
    payload = _read_regular_file(root / EXACT4_PATHS[0], "CER_RECONCILIATION")
    tree = ast.parse(payload)
    imported_covapie = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
        if alias.name.startswith("covapie_")
    }
    expected_imported = {
        "covapie_cer_completed_decision_ingestion_and_task_label_availability_v1",
        "covapie_completed_human_decision_reconciliation_v1",
        "covapie_completed_human_decision_reconciliation_with_1n0_v1",
        "covapie_completed_human_decision_reconciliation_with_onl_v1",
    }
    if imported_covapie != expected_imported:
        raise ValueError("RUNTIME_DEPENDENCY_GRAPH_INVALID")
    classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    if classes != {"CompletedDecisionReconciliationWithCERError"}:
        raise ValueError("GENERIC_SCHEMA_FORK_OR_EXTRA_CLASS_CREATED")
    calls = [
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    ]
    expected_calls = {
        "load_frozen_formal_decision_v1": 1,
        "load_real_completed_decision_sources_with_1n0_v1": 1,
        "reconcile_real_completed_human_decisions_with_1n0_v1": 1,
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
    if "validate_cer_formal_human_decision_v1" in payload.decode("utf-8"):
        raise ValueError("FROZEN_VALIDATOR_DEPENDENCY_FORBIDDEN")
    return {
        "public_api": subject.__all__,
        "runtime_dependencies": tuple(sorted(imported_covapie)),
        "generic_schema_forked": False,
        "generic_reconciler_forked": False,
        "new_transition_adapter_created": False,
        "production_side_effect_calls": 0,
    }


def _verify_rich_authority(bound: dict[str, object]) -> dict[str, object]:
    binding = bound.get("formal_decision_binding")
    expected_binding = {
        "path": cer_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": 26123,
        "SHA256": (
            "380d54ba35cf8eff1760d540e0874c8a7e920dac9473a002dac156812164fb2c"
        ),
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "CER_FROZEN_FORMAL_HUMAN_DECISION",
    }
    if binding != expected_binding:
        raise ValueError("CER_PUBLISHED_SOURCE_IDENTITY_INVALID")
    events = subject._validate_rich_cer_semantics_v1(bound)
    formal = bound.get("formal")
    if type(formal) is not dict:
        raise ValueError("CER_FORMAL_NOT_OBJECT")
    pair = formal.get("reactive_pair_authority")
    role = formal.get("selected_role_partition")
    training = formal.get("training_use_boundary")
    pre = formal.get("PRE_POST_boundary")
    post = formal.get("POST_evidence_boundary")
    if not all(type(value) is dict for value in (pair, role, training, pre, post)):
        raise ValueError("CER_RICH_AUTHORITY_SHAPE_INVALID")
    assert isinstance(pair, dict)
    assert isinstance(role, dict)
    assert isinstance(training, dict)
    assert isinstance(pre, dict)
    assert isinstance(post, dict)
    if (
        len(events) != 4
        or pair.get("pair_scope") != "CURRENT_CER_EXACT4_SAMPLE_REVIEW_UNIT_ONLY"
        or role.get("role_profile") != "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        or role.get("warhead_role_atom_ids") != list(cer_ingestion_owner.WARHEAD_ROLE)
        or role.get("linker_atom_ids") != []
        or role.get("scaffold_atom_ids")
        != list(cer_ingestion_owner.SCAFFOLD_ROLE)
        or role.get("applicable_task_ids") != [0, 3, 4]
        or training.get("formal_training_admitted") is not False
        or training.get("training_materialization_allowed") is not False
        or training.get("tensor_target_created") is not False
        or pre.get("PRE_status") != "PRE_REACTION_UNRESOLVED"
        or post.get("POST_geometry_training_authority") is not False
    ):
        raise ValueError("CER_RICH_AUTHORITY_SEMANTICS_INVALID")
    return {
        "event_count": 4,
        "review_unit_id": cer_ingestion_owner.EXPECTED_REVIEW_UNIT_ID,
        "ranks": tuple(cer_ingestion_owner.EXPECTED_RANKS),
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C2",
        "pair_authority_scope": cer_ingestion_owner.AUTHORITY_SCOPE,
        "role_profile": cer_ingestion_owner.EXPECTED_ROLE_PROFILE,
        "applicable_task_ids": (0, 3, 4),
        "formal_training_admitted": False,
        "ready_for_training": False,
    }


def _verify_projection(
    source: generic.NormalizedDecisionSource,
) -> dict[str, object]:
    observed_fields = tuple(
        field.name for field in fields(generic.NormalizedCompletedDecisionFact)
    )
    if observed_fields != EXPECTED_GENERIC_FACT_FIELDS or len(observed_fields) != 11:
        raise ValueError("GENERIC_FACT_SCHEMA_NOT_EXACT11")
    subject._validate_projected_cer_source_v1(source)
    if (
        source.binding.path_namespace != "repository_parent_relative"
        or source.binding.source_path
        != cer_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()
        or source.binding.byte_count != 26123
        or source.binding.sha256
        != "380d54ba35cf8eff1760d540e0874c8a7e920dac9473a002dac156812164fb2c"
        or len(source.facts) != 4
        or any(
            fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_POSITIVE
            or fact.task_relevance_disposition != generic.TASK_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_INCLUDE
            or fact.human_training_excluded is not False
            or any(hasattr(fact, name) for name in FORBIDDEN_FACT_ATTRIBUTES)
            for fact in source.facts
        )
    ):
        raise ValueError("CER_GENERIC_PROJECTION_INVALID_OR_RICH_LEAKAGE")
    return {
        "generic_fact_fields": observed_fields,
        "fact_count": 4,
        "completed_positive_count": 4,
        "relevant_count": 4,
        "chemistry_positive_count": 4,
        "training_include_count": 4,
        "human_training_excluded_count": 0,
        "rich_field_leakage_count": 0,
    }


def _verify_sources(
    root: Path,
) -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    tuple[generic.NormalizedDecisionSource, ...],
]:
    before = one_n0_predecessor.load_real_completed_decision_sources_with_1n0_v1(
        root
    )
    after = subject.load_real_completed_decision_sources_with_cer_v1(root)
    before_ids = [fact.canonical_event_id for source in before for fact in source.facts]
    after_ids = [fact.canonical_event_id for source in after for fact in source.facts]
    if (
        len(before) != 15
        or tuple(len(source.facts) for source in before)
        != PREDECESSOR_SOURCE_FACT_COUNTS
        or len(before_ids) != 103
        or len(set(before_ids)) != 103
        or len({source.binding.review_unit_id for source in before}) != 15
        or len({source.binding.stable_identity for source in before}) != 15
    ):
        raise ValueError("PREDECESSOR_SOURCE_CHAIN_NOT_EXACT15_103")
    if (
        len(after) != 16
        or tuple(len(source.facts) for source in after)
        != SUCCESSOR_SOURCE_FACT_COUNTS
        or len(after_ids) != 107
        or len(set(after_ids)) != 107
        or len({source.binding.review_unit_id for source in after}) != 16
        or len({source.binding.stable_identity for source in after}) != 16
        or after[:-1] != before
        or set(cer_ingestion_owner.EXPECTED_EVENT_IDS) & set(before_ids)
    ):
        raise ValueError("SUCCESSOR_SOURCE_CHAIN_NOT_EXACT16_107")
    return before, after


def _verify_historical_and_onl(
    root: Path,
) -> tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...]]:
    historical = generic.load_real_historical_reconciliation_v1(root)
    original_snapshot = copy.deepcopy(historical)
    if len(historical) != 338 or len(
        {row["raw_review_unit_id"] for row in historical}
    ) != 131:
        raise ValueError("HISTORICAL_POPULATION_NOT_EXACT338_131")
    subject._prove_cer_original_unreviewed_prior_v1(historical)
    target_ids = set(cer_ingestion_owner.EXPECTED_EVENT_IDS)
    target = [row for row in historical if row["canonical_event_id"] in target_ids]
    if len(target) != 4 or any(
        row["raw_review_unit_id"] != cer_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
        or row["raw_priority_rank"] != "19"
        or row["raw_unit_event_count"] != "4"
        or row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in target
    ):
        raise ValueError("CER_HISTORICAL_PRIOR_INVALID")
    adapted = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    if historical != original_snapshot:
        raise ValueError("ONL_ADAPTER_MUTATED_ORIGINAL_HISTORICAL_ROWS")
    subject._prove_cer_rows_unchanged_after_onl_normalization_v1(
        historical, adapted
    )
    before = {
        row["canonical_event_id"]: row
        for row in historical
        if row["canonical_event_id"] in target_ids
    }
    after = {
        row["canonical_event_id"]: row
        for row in adapted
        if row["canonical_event_id"] in target_ids
    }
    if before != after:
        raise ValueError("ONL_ADAPTER_CHANGED_CER_ROW")
    return historical, adapted


def _verify_reconciliation(root: Path) -> generic.ReconciliationResult:
    before = (
        one_n0_predecessor.reconcile_real_completed_human_decisions_with_1n0_v1(
            root
        )
    )
    after = subject.reconcile_real_completed_human_decisions_with_cer_v1(root)
    subject._validate_reconciliation_delta_v1(before, after)
    if before.review_summary != BEFORE_SUMMARY or after.review_summary != AFTER_SUMMARY:
        raise ValueError("CER_REVIEW_SUMMARY_DELTA_INVALID")
    before_by_event = {
        row["canonical_event_id"]: row for row in before.reconciled_rows
    }
    after_by_event = {
        row["canonical_event_id"]: row for row in after.reconciled_rows
    }
    target_ids = set(cer_ingestion_owner.EXPECTED_EVENT_IDS)
    changed = {
        event_id
        for event_id in before_by_event
        if before_by_event[event_id] != after_by_event[event_id]
    }
    allowed = {
        "current_review_status",
        "current_status_authority_sources_json",
        "calibration_eligible",
        "calibration_exclusion_reason",
    }
    expected_authority = json.dumps(
        [cer_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    if changed != target_ids:
        raise ValueError("CER_CHANGED_ROWS_NOT_EXACT4")
    for event_id in target_ids:
        old = before_by_event[event_id]
        new = after_by_event[event_id]
        changed_fields = {key for key in old if old[key] != new[key]}
        if (
            changed_fields != allowed
            or old["current_review_status"] != generic.CURRENTLY_UNREVIEWED
            or new["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE
            or new["current_status_authority_sources_json"] != expected_authority
            or new["calibration_eligible"] != "false"
            or new["calibration_exclusion_reason"]
            != generic.COMPLETED_HUMAN_POSITIVE
        ):
            raise ValueError("CER_EXACT_FOUR_FIELD_TRANSITION_INVALID")
    if any(
        before_by_event[event_id] != after_by_event[event_id]
        for event_id in set(before_by_event) - target_ids
    ):
        raise ValueError("CER_NON_TARGET_ROW_CHANGED")
    if len(after.normalized_facts) != 107 or len(after.source_bindings) != 16:
        raise ValueError("CER_RECONCILIATION_RESULT_COMPOSITION_INVALID")
    return after


def _expect_subject_failure(callable_: object, token: str) -> None:
    try:
        callable_()  # type: ignore[operator]
    except subject.CompletedDecisionReconciliationWithCERError as error:
        if token not in str(error):
            raise ValueError("FAIL_CLOSED_TOKEN_INVALID:" + str(error)) from error
    else:
        raise ValueError("FAIL_CLOSED_PROBE_DID_NOT_FAIL:" + token)


def _verify_fail_closed_probes(
    bound: dict[str, object],
    historical: tuple[dict[str, str], ...],
    adapted: tuple[dict[str, str], ...],
) -> dict[str, bool]:
    decision_mutations = {
        "D1_task_relevance": "NOT_RELEVANT",
        "D2_chemistry": "NEGATIVE",
        "D3_reactive_pair": "UNRESOLVED",
        "D4_role_candidate": "SELECT_CANDIDATE_0",
        "D5_training_use": "EXCLUDE_FROM_TRAINING_ONLY",
    }
    for key, replacement in decision_mutations.items():
        changed = copy.deepcopy(bound)
        changed["formal"]["human_authorization"][key] = (  # type: ignore[index]
            replacement
        )
        _expect_subject_failure(
            lambda changed=changed: subject._project_validated_cer_binding_v1(
                changed
            ),
            "CER_D1_D5_DECISIONS_INVALID",
        )

    for mutation in ("missing", "duplicate", "extra"):
        changed = copy.deepcopy(bound)
        events = changed["formal"]["event_level_human_decisions"]  # type: ignore[index]
        identities = changed["formal"]["identity"][  # type: ignore[index]
            "canonical_event_ids"
        ]
        if mutation == "missing":
            events.pop()  # type: ignore[union-attr]
            identities.pop()  # type: ignore[union-attr]
        elif mutation == "duplicate":
            events[-1] = copy.deepcopy(events[0])  # type: ignore[index]
            identities[-1] = identities[0]  # type: ignore[index]
        else:
            extra_event = copy.deepcopy(events[-1])  # type: ignore[index]
            extra_event["canonical_event_id"] = "SYNTHETIC_EXTRA"
            events.append(extra_event)  # type: ignore[union-attr]
            identities.append("SYNTHETIC_EXTRA")  # type: ignore[union-attr]
        _expect_subject_failure(
            lambda changed=changed: subject._project_validated_cer_binding_v1(
                changed
            ),
            "CER_FORMAL_IDENTITY_NOT_EXACT4",
        )

    wrong_prior = tuple(dict(row) for row in historical)
    for row in wrong_prior:
        if row["canonical_event_id"] == cer_ingestion_owner.EXPECTED_EVENT_IDS[0]:
            row["current_review_status"] = generic.COMPLETED_HUMAN_POSITIVE
            row["calibration_eligible"] = "false"
            row["calibration_exclusion_reason"] = generic.COMPLETED_HUMAN_POSITIVE
            break
    _expect_subject_failure(
        lambda: subject._prove_cer_original_unreviewed_prior_v1(wrong_prior),
        "CER_RECONCILIATION_PRECONDITION_FAILED",
    )

    changed_adapted = tuple(dict(row) for row in adapted)
    for row in changed_adapted:
        if row["canonical_event_id"] == cer_ingestion_owner.EXPECTED_EVENT_IDS[0]:
            row["calibration_eligible"] = "false"
            break
    _expect_subject_failure(
        lambda: subject._prove_cer_rows_unchanged_after_onl_normalization_v1(
            historical, changed_adapted
        ),
        "ONL_ADAPTER_CHANGED_CER_ROW",
    )
    return {
        "D1_D5_mutations_fail": True,
        "missing_duplicate_extra_fail": True,
        "prior_state_mutation_fails": True,
        "ONL_CER_mutation_fails": True,
    }


def check_lifecycle_simulations() -> dict[str, bool]:
    expected = tuple(sorted(EXACT4_PATHS))
    expected_set = set(expected)
    future_paths = {
        "src/covalent_ext/synthetic_future_reconciliation_v1.py",
        "data/derived/covalent_small/synthetic_future_census_v1.json",
    }
    if classify_repository_profile(
        expected_paths=expected,
        tracked_paths=set(),
        ordinary_untracked=expected_set,
        status_lines=tuple("?? " + path for path in expected),
        working_diff=set(),
        cached_diff=set(),
    ) != CANDIDATE_UNTRACKED:
        raise ValueError("CANDIDATE_LIFECYCLE_SIMULATION_FAILED")
    if classify_repository_profile(
        expected_paths=expected,
        tracked_paths=expected_set,
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    ) != TRACKED_CLEAN:
        raise ValueError("TRACKED_LIFECYCLE_SIMULATION_FAILED")

    candidate_relation = {
        "profile": CANDIDATE_UNTRACKED,
        "expected_paths": expected_set,
        "head": BASELINE_COMMIT,
        "origin_main": BASELINE_COMMIT,
        "ahead": 0,
        "behind": 0,
        "baseline_is_ancestor_of_head": True,
        "baseline_is_ancestor_of_origin": True,
        "origin_is_ancestor_of_head": True,
        "changed_since_baseline": set(),
    }
    validate_repository_relation_values(**candidate_relation)  # type: ignore[arg-type]
    tracked_relation = {
        "profile": TRACKED_CLEAN,
        "expected_paths": expected_set,
        "head": "synthetic-head",
        "origin_main": BASELINE_COMMIT,
        "ahead": 3,
        "behind": 0,
        "baseline_is_ancestor_of_head": True,
        "baseline_is_ancestor_of_origin": True,
        "origin_is_ancestor_of_head": True,
        "changed_since_baseline": expected_set | future_paths,
    }
    validate_repository_relation_values(**tracked_relation)  # type: ignore[arg-type]
    validate_repository_relation_values(
        **{
            **tracked_relation,
            "head": "synthetic-published-head",
            "origin_main": "synthetic-published-head",
            "ahead": 0,
        }
    )  # type: ignore[arg-type]

    def relation_fails(**updates: object) -> bool:
        values = {**tracked_relation, **updates}
        try:
            validate_repository_relation_values(**values)  # type: ignore[arg-type]
        except ValueError:
            return True
        return False

    def profile_fails(**updates: object) -> bool:
        values: dict[str, object] = {
            "expected_paths": expected,
            "tracked_paths": expected_set,
            "ordinary_untracked": set(),
            "status_lines": (),
            "working_diff": set(),
            "cached_diff": set(),
        }
        values.update(updates)
        try:
            classify_repository_profile(**values)  # type: ignore[arg-type]
        except ValueError:
            return True
        return False

    failures = (
        relation_fails(baseline_is_ancestor_of_head=False),
        relation_fails(baseline_is_ancestor_of_origin=False),
        relation_fails(origin_is_ancestor_of_head=False),
        relation_fails(behind=1),
        relation_fails(changed_since_baseline=expected_set - {expected[0]}),
        profile_fails(
            tracked_paths={expected[0]},
            ordinary_untracked=set(expected[1:]),
            status_lines=tuple("?? " + path for path in expected[1:]),
        ),
        profile_fails(working_diff={expected[0]}),
        profile_fails(cached_diff={expected[0]}),
        profile_fails(
            ordinary_untracked={"synthetic-unrelated.txt"},
            status_lines=("?? synthetic-unrelated.txt",),
        ),
    )
    if not all(failures):
        raise ValueError("FAIL_CLOSED_LIFECYCLE_SIMULATION_INVALID")
    return {
        "candidate_untracked": True,
        "tracked_clean": True,
        "multiple_commits_allowed": True,
        "unrelated_successors_allowed": True,
        "origin_at_baseline_allowed": True,
        "origin_at_head_allowed": True,
        "origin_between_baseline_and_head_allowed": True,
        "missing_path_fails": True,
        "baseline_rewind_fails": True,
        "origin_divergence_fails": True,
        "behind_remote_fails": True,
        "mixed_tracking_fails": True,
        "dirty_worktree_fails": True,
        "staged_change_fails": True,
        "unrelated_untracked_fails": True,
    }


def _verify_b4_core(root: Path) -> dict[str, object]:
    result = b4_guard.verify_covapie_source_binding_future_exact_posix_mode_guard_v2(
        repo_root=root
    )
    required = {
        "new_semantic_exact_posix_mode_occurrence_count": 0,
        "new_ambiguous_mode_occurrence_count": 0,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "ready_for_training": False,
    }
    if any(result.get(key) != value for key, value in required.items()):
        raise ValueError("B4_FUTURE_GUARD_RESULT_INVALID")
    scanned = set(result.get("future_guard_scanned_python_paths", ()))
    if not set(EXACT4_PATHS[:3]) <= scanned:
        raise ValueError("B4_CANDIDATE_PYTHON_FILES_NOT_ALL_SCANNED")
    return {**required, "candidate_python_files_scanned": True}


def _verify_no_outputs_or_transients(root: Path) -> None:
    forbidden_root = (
        root
        / "data/derived/covalent_small/"
        "covapie_completed_human_decision_reconciliation_with_cer_v1"
    )
    if forbidden_root.exists():
        raise ValueError("MATERIALIZED_CER_RECONCILIATION_ROOT_FORBIDDEN")
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
    """Run every read-only CER reconciliation candidate gate."""

    root = repo_root.resolve()
    exact4 = _verify_candidate_exact4(root)
    lineage = _verify_frozen_runtime_lineage(root)
    architecture = _verify_architecture(root)
    bound = cer_ingestion_owner.load_frozen_formal_decision_v1(root)
    rich = _verify_rich_authority(bound)
    projection_source = subject._project_validated_cer_binding_v1(bound)
    projection = _verify_projection(projection_source)
    before_sources, after_sources = _verify_sources(root)
    historical, adapted = _verify_historical_and_onl(root)
    result = _verify_reconciliation(root)
    fail_closed = _verify_fail_closed_probes(bound, historical, adapted)
    lifecycle = check_lifecycle_simulations()
    _verify_no_outputs_or_transients(root)
    b4 = _verify_b4_core(root)
    dispositions = Counter(
        fact.training_disposition for fact in projection_source.facts
    )
    return {
        "status": "PASS",
        "repository": exact4,
        "runtime_lineage": lineage,
        "architecture": architecture,
        "rich_CER": rich,
        "projection": projection,
        "predecessor_source_count": len(before_sources),
        "successor_source_count": len(after_sources),
        "predecessor_fact_count": sum(
            len(source.facts) for source in before_sources
        ),
        "successor_fact_count": sum(len(source.facts) for source in after_sources),
        "event_collisions": 0,
        "CER_rows_changed_by_ONL": 0,
        "CER_changed_rows": 4,
        "non_CER_unchanged_rows": 334,
        "review_summary": result.review_summary,
        "CER_training_dispositions": dict(dispositions),
        "fail_closed": fail_closed,
        "lifecycle_simulations": lifecycle,
        "b4_core": b4,
        "new_human_authority_created": False,
        "new_scientific_authority_created": False,
        "formal_training_admitted": False,
        "training_materialization_allowed": False,
        "tensor_target_created": False,
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
    ):
        raise ValueError("OPERATION_BOUNDARY_INVALID")
    print("PASS")
    print(report["repository"]["lifecycle"])
    print("predecessor_sources=15 predecessor_facts=103")
    print("successor_sources=16 successor_facts=107 collisions=0")
    print("CER_changed_rows=4 non_CER_unchanged_rows=334")
    print("census_refresh=false queue_refresh=false training_started=false")
    print("READY_FOR_TRAINING=false FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
