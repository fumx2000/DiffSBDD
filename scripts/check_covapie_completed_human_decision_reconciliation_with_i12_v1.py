#!/usr/bin/env python3
"""Read-only checker for the I12 completed-decision reconciliation candidate."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import copy
from dataclasses import fields
import hashlib
from pathlib import Path
import re
import stat
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_i12_completed_decision_ingestion_and_task_label_availability_v1
    as i12_ingestion_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_2a2_v1
    as two_a2_successor,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_i12_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_onl_v1
    as onl_successor,
)
from covalent_ext import (  # noqa: E402
    covapie_source_binding_future_exact_posix_mode_guard_v2 as b4_guard,
)


BASELINE_COMMIT = "41151f58935f4341d2a5c997f99bc6640772440f"
EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_i12_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_i12_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_i12_v1.py",
    "docs/covapie_completed_human_decision_reconciliation_with_i12_v1_guide.md",
)
PURPOSES = {
    EXACT4_PATHS[0]: "rich I12 validation, narrow projection, and in-memory reconciliation",
    EXACT4_PATHS[1]: "read-only candidate and semantic checker",
    EXACT4_PATHS[2]: "success and fail-closed targeted tests",
    EXACT4_PATHS[3]: "concise reconciliation boundary guide",
}
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWithI12Error",
    "project_i12_completed_decision_v1",
    "load_real_completed_decision_sources_with_i12_v1",
    "reconcile_real_completed_human_decisions_with_i12_v1",
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
    "chemical_warhead_atom_ids",
    "warhead_role_atom_ids",
    "linker_atom_ids",
    "scaffold_atom_ids",
    "role_profile",
    "role_boundaries",
    "selected_candidate",
    "canonical_task_applicability",
    "minimal_seed",
    "POST_geometry",
    "PRE_topology",
    "PRE_geometry",
    "future_training_candidate",
    "training_admitted",
    "reaction_family",
    "warhead_rule",
    "warhead_type",
)
EXISTING_SOURCE_FACT_COUNTS = (8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4, 4, 4)
FUTURE_SOURCE_FACT_COUNTS = (*EXISTING_SOURCE_FACT_COUNTS, 4)
EXPECTED_REVIEW_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 99,
    "completed_positive_unit_count": 14,
    "completed_negative_event_count": 24,
    "completed_negative_unit_count": 4,
    "completed_total_event_count": 123,
    "completed_total_unit_count": 18,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 215,
    "unreviewed_unit_count": 113,
}
FROZEN_RUNTIME_LINEAGE = (
    (
        "I12_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_i12_completed_decision_ingestion_and_task_label_availability_v1.py",
        73596,
        "4e291fd0af910f2590b8f2041c388c70746d1bcdb77419bf552a87ae657a4ed8",
    ),
    (
        "GENERIC_RECONCILIATION_OWNER",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
    ),
    (
        "2A2_RECONCILIATION_PREDECESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_2a2_v1.py",
        26024,
        "c0f417bbc4effb5b02d788a42779bd0eae4db2df4de85c33bb40bf6111b67863",
    ),
    (
        "ONL_NORMALIZATION_SUCCESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_onl_v1.py",
        13046,
        "f2c94ac8b4fe8f3706d0de288e2d5bb24ef211cf56d39e8362b43bdb17a2f475",
    ),
)
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
    ".tgz", ".npz", ".pyc", ".tmp", ".part", ".log",
)
MAX_FILE_BYTES = 1024 * 1024
_CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
_TRACKED_CLEAN = "TRACKED_CLEAN"
_SUPPORTED_REPOSITORY_PROFILES = (_CANDIDATE_UNTRACKED, _TRACKED_CLEAN)
_COMMIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_regular_file(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("NOT_REGULAR_FILE:" + label)
    try:
        return path.read_bytes()
    except OSError as error:
        raise ValueError("READ_FAILED:" + label) from error


def _git(
    root: Path, *arguments: str, binary: bool = False
) -> str | bytes:
    try:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError("GIT_OBSERVATION_FAILED:" + arguments[0]) from error
    if binary:
        return completed.stdout
    try:
        return completed.stdout.decode("utf-8").rstrip("\n")
    except UnicodeDecodeError as error:
        raise ValueError("GIT_OBSERVATION_NOT_UTF8:" + arguments[0]) from error


def _git_nul(root: Path, *arguments: str) -> tuple[str, ...]:
    payload = _git(root, *arguments, binary=True)
    assert isinstance(payload, bytes)
    try:
        return tuple(
            sorted(item.decode("utf-8") for item in payload.split(b"\0") if item)
        )
    except UnicodeDecodeError as error:
        raise ValueError("GIT_NUL_OBSERVATION_NOT_UTF8") from error


def _classify_repository_profile(
    *,
    expected_paths: tuple[str, ...],
    tracked_paths: set[str],
    ordinary_untracked: set[str],
    status_lines: tuple[str, ...],
    working_tree_diff_paths: tuple[str, ...],
    cached_diff_paths: tuple[str, ...],
) -> str:
    expected = set(expected_paths)
    if len(expected_paths) != 4 or len(expected) != 4:
        raise ValueError("EXACT4_INVENTORY_INVALID")
    tracked_exact4 = tracked_paths & expected
    expected_status = tuple(sorted("?? " + path for path in expected_paths))
    if (
        not tracked_exact4
        and ordinary_untracked == expected
        and tuple(sorted(status_lines)) == expected_status
        and not working_tree_diff_paths
        and not cached_diff_paths
    ):
        return _CANDIDATE_UNTRACKED
    if (
        tracked_exact4 == expected
        and not ordinary_untracked
        and not status_lines
        and not working_tree_diff_paths
        and not cached_diff_paths
    ):
        return _TRACKED_CLEAN
    raise ValueError(
        "REPOSITORY_PROFILE_NOT_EXACT_CANDIDATE_UNTRACKED_OR_TRACKED_CLEAN"
    )


def _repository_observations(root: Path) -> dict[str, object]:
    tracked = set(_git_nul(root, "ls-files", "-z"))
    untracked = set(_git_nul(root, "ls-files", "--others", "--exclude-standard", "-z"))
    status = _git_nul(root, "status", "--short", "--untracked-files=all", "-z")
    working = _git_nul(root, "diff", "--name-only", "-z")
    cached = _git_nul(root, "diff", "--cached", "--name-only", "-z")
    return {
        "tracked_paths": tracked,
        "ordinary_untracked": untracked,
        "status_lines": status,
        "working_tree_diff_paths": working,
        "cached_diff_paths": cached,
    }


def _validate_repository_relation_facts(
    *,
    profile: str,
    branch: str,
    head: str,
    origin: str,
    relation: str,
    baseline_is_ancestor: bool | None = None,
    commit_count: int | None = None,
    head_parents: tuple[str, ...] | None = None,
    changed_paths: set[str] | None = None,
) -> tuple[int, int]:
    """Validate candidate or tracked-clean publication facts without Git I/O."""

    if branch != "main":
        raise ValueError("REPOSITORY_BRANCH_INVALID")
    if (
        type(head) is not str
        or _COMMIT_SHA_PATTERN.fullmatch(head) is None
        or type(origin) is not str
        or _COMMIT_SHA_PATTERN.fullmatch(origin) is None
    ):
        raise ValueError("REPOSITORY_COMMIT_IDENTITY_INVALID")
    if type(relation) is not str:
        raise ValueError("REPOSITORY_AHEAD_BEHIND_INVALID")
    relation_parts = relation.split("\t")
    if len(relation_parts) != 2 or any(
        not part.isdecimal() for part in relation_parts
    ):
        raise ValueError("REPOSITORY_AHEAD_BEHIND_INVALID")
    ahead, behind = (int(part) for part in relation_parts)

    if profile == _CANDIDATE_UNTRACKED:
        if (
            head != BASELINE_COMMIT
            or origin != BASELINE_COMMIT
            or (ahead, behind) != (0, 0)
        ):
            raise ValueError("CANDIDATE_REPOSITORY_RELATION_INVALID")
        return ahead, behind

    if profile != _TRACKED_CLEAN:
        raise ValueError("REPOSITORY_PROFILE_UNSUPPORTED")
    if head == BASELINE_COMMIT:
        raise ValueError("TRACKED_HEAD_MUST_BE_SUCCESSOR")
    if baseline_is_ancestor is not True:
        raise ValueError("TRACKED_BASELINE_NOT_ANCESTOR")
    if type(commit_count) is not int or commit_count != 1:
        raise ValueError("TRACKED_PUBLICATION_COMMIT_COUNT_NOT_EXACT1")
    if head_parents != (BASELINE_COMMIT,):
        raise ValueError("TRACKED_SUCCESSOR_PARENT_NOT_EXACT_BASELINE")
    if type(changed_paths) is not set or changed_paths != set(EXACT4_PATHS):
        raise ValueError("TRACKED_PUBLICATION_SCOPE_NOT_EXACT4")

    committed_unpushed = origin == BASELINE_COMMIT and (ahead, behind) == (1, 0)
    pushed_successor = origin == head and (ahead, behind) == (0, 0)
    if not (committed_unpushed or pushed_successor):
        raise ValueError("TRACKED_REPOSITORY_RELATION_INVALID")
    return ahead, behind


def _git_is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    try:
        completed = subprocess.run(
            ("git", "merge-base", "--is-ancestor", ancestor, descendant),
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as error:
        raise ValueError("GIT_ANCESTRY_OBSERVATION_FAILED") from error
    if completed.returncode not in {0, 1}:
        raise ValueError("GIT_ANCESTRY_OBSERVATION_FAILED")
    return completed.returncode == 0


def _verify_repository_relation(root: Path, profile: str) -> dict[str, object]:
    branch = _git(root, "branch", "--show-current")
    head = _git(root, "rev-parse", "HEAD")
    origin = _git(root, "rev-parse", "origin/main")
    relation = _git(root, "rev-list", "--left-right", "--count", "HEAD...origin/main")
    if not all(type(value) is str for value in (branch, head, origin, relation)):
        raise ValueError("REPOSITORY_RELATION_OBSERVATION_TYPE_INVALID")

    baseline_is_ancestor: bool | None = None
    commit_count: int | None = None
    head_parents: tuple[str, ...] | None = None
    changed_paths: set[str] | None = None
    if profile == _TRACKED_CLEAN:
        baseline_is_ancestor = _git_is_ancestor(root, BASELINE_COMMIT, head)
        count_text = _git(root, "rev-list", "--count", BASELINE_COMMIT + ".." + head)
        if type(count_text) is not str or not count_text.isdecimal():
            raise ValueError("TRACKED_PUBLICATION_COMMIT_COUNT_INVALID")
        commit_count = int(count_text)
        parent_text = _git(root, "rev-list", "--parents", "-n", "1", head)
        if type(parent_text) is not str:
            raise ValueError("TRACKED_SUCCESSOR_PARENT_OBSERVATION_INVALID")
        parent_parts = parent_text.split()
        if not parent_parts or parent_parts[0] != head:
            raise ValueError("TRACKED_SUCCESSOR_PARENT_OBSERVATION_INVALID")
        head_parents = tuple(parent_parts[1:])
        changed_paths = set(
            _git_nul(root, "diff", "--name-only", "-z", BASELINE_COMMIT, head)
        )

    ahead, behind = _validate_repository_relation_facts(
        profile=profile,
        branch=branch,
        head=head,
        origin=origin,
        relation=relation,
        baseline_is_ancestor=baseline_is_ancestor,
        commit_count=commit_count,
        head_parents=head_parents,
        changed_paths=changed_paths,
    )
    return {
        "branch": branch,
        "HEAD": head,
        "origin_main": origin,
        "ahead_behind": f"{ahead}/{behind}",
    }


def _validate_text_payload(payload: bytes, label: str) -> None:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("EXACT4_NOT_UTF8:" + label) from error
    if payload.startswith(b"\xef\xbb\xbf") or "\x00" in text or "\r" in text:
        raise ValueError("EXACT4_TEXT_INVARIANT_INVALID:" + label)
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise ValueError("EXACT4_TERMINAL_LF_INVALID:" + label)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        raise ValueError("EXACT4_TRAILING_WHITESPACE:" + label)


def _verify_candidate_exact4(root: Path) -> dict[str, object]:
    observations = _repository_observations(root)
    profile = _classify_repository_profile(
        expected_paths=EXACT4_PATHS,
        tracked_paths=observations["tracked_paths"],  # type: ignore[arg-type]
        ordinary_untracked=observations["ordinary_untracked"],  # type: ignore[arg-type]
        status_lines=observations["status_lines"],  # type: ignore[arg-type]
        working_tree_diff_paths=observations["working_tree_diff_paths"],  # type: ignore[arg-type]
        cached_diff_paths=observations["cached_diff_paths"],  # type: ignore[arg-type]
    )
    relation = _verify_repository_relation(root, profile)
    artifacts: list[dict[str, object]] = []
    for relative in EXACT4_PATHS:
        path = root / relative
        payload = _read_regular_file(path, relative)
        _validate_text_payload(payload, relative)
        if len(payload) >= MAX_FILE_BYTES:
            raise ValueError("EXACT4_FILE_TOO_LARGE:" + relative)
        metadata = path.stat()
        executable = bool(
            metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        )
        if executable:
            raise ValueError("EXACT4_EXECUTABLE_CLASS_INVALID:" + relative)
        artifacts.append(
            {
                "path": relative,
                "bytes": len(payload),
                "SHA256": _sha256(payload),
                "executable_class": "NON_EXECUTABLE",
                "purpose": PURPOSES[relative],
            }
        )
    ignored = _git_nul(
        root,
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "-z",
    )
    transient = tuple(
        path
        for path in ignored
        if "__pycache__" in path.split("/")
        or path.endswith((".pyc", ".tmp", ".part", ".log"))
    )
    if transient:
        raise ValueError("IGNORED_TRANSIENT_PATH:" + transient[0])
    dirty_paths = {
        *observations["ordinary_untracked"],  # type: ignore[misc]
        *observations["working_tree_diff_paths"],  # type: ignore[misc]
        *observations["cached_diff_paths"],  # type: ignore[misc]
    }
    forbidden = sorted(path for path in dirty_paths if path.endswith(FORBIDDEN_SUFFIXES))
    if forbidden:
        raise ValueError("FORBIDDEN_DIRTY_PATH:" + forbidden[0])
    return {
        "candidate_file_count": len(artifacts),
        "lifecycle": profile,
        "artifacts": tuple(artifacts),
        **relation,
    }


def _verify_frozen_runtime_lineage(root: Path) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for label, relative, expected_bytes, expected_sha in FROZEN_RUNTIME_LINEAGE:
        payload = _read_regular_file(root / relative, label)
        if len(payload) != expected_bytes or _sha256(payload) != expected_sha:
            raise ValueError("FROZEN_RUNTIME_LINEAGE_DRIFT:" + label)
        rows.append({"label": label, "path": relative, "SHA256": expected_sha})
    return tuple(rows)


def _verify_architecture(root: Path) -> dict[str, object]:
    if subject.__all__ != EXPECTED_PUBLIC_API:
        raise ValueError("PUBLIC_API_NOT_EXACT4")
    payload = _read_regular_file(root / EXACT4_PATHS[0], "I12_RECONCILIATION_OWNER")
    tree = ast.parse(payload)
    imported_covapie = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
        if alias.name.startswith("covapie_")
    }
    expected_imported = {
        "covapie_i12_completed_decision_ingestion_and_task_label_availability_v1",
        "covapie_completed_human_decision_reconciliation_v1",
        "covapie_completed_human_decision_reconciliation_with_2a2_v1",
        "covapie_completed_human_decision_reconciliation_with_onl_v1",
    }
    if imported_covapie != expected_imported:
        raise ValueError("RUNTIME_DEPENDENCY_GRAPH_INVALID")
    class_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    if class_names != {"CompletedDecisionReconciliationWithI12Error"}:
        raise ValueError("GENERIC_SCHEMA_FORK_OR_EXTRA_CLASS_CREATED")
    call_names = [
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    ]
    expected_calls = {
        "load_frozen_formal_decision_v1": 1,
        "load_real_completed_decision_sources_with_2a2_v1": 1,
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1": 1,
        "reconcile_completed_human_decisions_v1": 1,
    }
    if any(call_names.count(name) != count for name, count in expected_calls.items()):
        raise ValueError("RUNTIME_DELEGATE_CALL_GRAPH_INVALID")
    forbidden_calls = {
        "open", "write", "write_bytes", "write_text", "mkdir", "makedirs",
        "materialize_artifacts", "write_artifacts", "refresh_census", "run",
        "Popen", "check_call", "check_output", "urlopen",
    }
    if forbidden_calls & set(call_names):
        raise ValueError("PRODUCTION_SIDE_EFFECT_CALL_FORBIDDEN")
    source_text = payload.decode("utf-8")
    if "formal_validator" in source_text.lower():
        raise ValueError("FORMAL_VALIDATOR_DEPENDENCY_FORBIDDEN")
    return {
        "public_api": subject.__all__,
        "runtime_dependencies": tuple(sorted(imported_covapie)),
        "transition_adapter_created": False,
        "production_side_effect_calls": 0,
    }


def _verify_rich_authority(bound: dict[str, object]) -> dict[str, object]:
    binding = bound.get("formal_decision_binding")
    expected_binding = {
        "path": i12_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix(),
        "namespace": "project_parent_relative",
        "byte_count": 26474,
        "SHA256": "e117da5c10c45603450eaab26ea6093ef07e70c4bf2ec2f0c7908aa38f531fa0",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "I12_FROZEN_FORMAL_HUMAN_DECISION",
    }
    if binding != expected_binding:
        raise ValueError("I12_PUBLISHED_SOURCE_IDENTITY_INVALID")
    formal = bound.get("formal")
    if type(formal) is not dict:
        raise ValueError("I12_FORMAL_NOT_OBJECT")
    approval = formal.get("human_approval")
    identity = formal.get("identity")
    role = formal.get("selected_role_partition")
    chemical = formal.get("chemical_warhead_boundary")
    pre = formal.get("experimental_context_and_PRE_boundary")
    post = formal.get("POST_evidence_boundary")
    training = formal.get("training_use_human_decision")
    authority = formal.get("authority_boundary")
    events = formal.get("event_level_human_decisions")
    if not all(
        type(value) is dict
        for value in (approval, identity, role, chemical, pre, post, training, authority)
    ) or type(events) is not list:
        raise ValueError("I12_RICH_AUTHORITY_SHAPE_INVALID")
    assert isinstance(approval, dict)
    assert isinstance(identity, dict)
    assert isinstance(role, dict)
    assert isinstance(chemical, dict)
    assert isinstance(pre, dict)
    assert isinstance(post, dict)
    assert isinstance(training, dict)
    assert isinstance(authority, dict)
    if (
        formal.get("human_review_completed") is not True
        or formal.get("approved") is not True
        or formal.get("decision_finalized") is not True
        or identity.get("review_unit_id") != i12_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
        or identity.get("canonical_event_ids")
        != list(i12_ingestion_owner.EXPECTED_EVENT_IDS)
        or identity.get("scaleup_ranks") != [187, 188, 222, 223]
        or tuple(approval.get(key) for key in (
            "D1_task_relevance", "D2_chemistry", "D3_reactive_pair",
            "D4_role_partition", "D5_training_use",
        ))
        != ("RELEVANT", "POSITIVE", "CONFIRM_OBSERVED_PAIR", "SELECT_CANDIDATE_0", "INCLUDE")
        or role.get("selected_candidate_index_0based") != 0
        or role.get("human_selected") is not True
        or role.get("machine_selected") is not False
        or role.get("machine_recommended") is not False
        or role.get("role_profile") != "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        or role.get("applicable_task_ids") != [0, 3, 4]
        or chemical.get("chemical_warhead_human_authoritative") is not False
        or chemical.get("chemical_warhead_atom_ids") is not None
        or pre.get("PRE_status") != "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
        or pre.get("PRE_topology_authority_created") is not False
        or pre.get("PRE_geometry_authority_created") is not False
        or post.get("POST_source_evidence_count") != 4
        or post.get("POST_sample_authority_created") is not False
        or post.get("POST_geometry_training_authority_created") is not False
        or training.get("candidate_for_future_training_admission") is not True
        or training.get("formal_training_admitted") is not False
        or authority.get("warhead_type_authority_created") is not False
        or authority.get("READY_FOR_TRAINING") is not False
    ):
        raise ValueError("I12_RICH_AUTHORITY_SEMANTICS_INVALID")
    if len(events) != 4 or any(
        type(event) is not dict
        or event.get("D1_task_relevance") != "RELEVANT"
        or event.get("D2_chemistry") != "POSITIVE"
        or event.get("D3_reactive_pair") != "CONFIRM_OBSERVED_PAIR"
        or event.get("D4_role_partition") != "SELECT_CANDIDATE_0"
        or event.get("D5_training_use") != "INCLUDE"
        or event.get("formal_training_admitted") is not False
        for event in events
    ):
        raise ValueError("I12_RICH_EVENT_SEMANTICS_INVALID")
    subject._validate_rich_i12_semantics_v1(bound)
    return {
        "event_count": 4,
        "review_unit_id": i12_ingestion_owner.EXPECTED_REVIEW_UNIT_ID,
        "ranks": tuple(i12_ingestion_owner.EXPECTED_RANKS),
        "role_profile": i12_ingestion_owner.EXPECTED_ROLE_PROFILE,
        "applicable_task_ids": (0, 3, 4),
        "training_admitted": False,
    }


def _verify_projection(source: generic.NormalizedDecisionSource) -> dict[str, object]:
    observed_fields = tuple(field.name for field in fields(generic.NormalizedCompletedDecisionFact))
    if observed_fields != EXPECTED_GENERIC_FACT_FIELDS or len(observed_fields) != 11:
        raise ValueError("GENERIC_FACT_SCHEMA_NOT_EXACT11")
    if (
        source.binding.path_namespace != "repository_parent_relative"
        or source.binding.source_path != i12_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()
        or source.binding.sha256
        != "e117da5c10c45603450eaab26ea6093ef07e70c4bf2ec2f0c7908aa38f531fa0"
        or len(source.facts) != 4
        or tuple(fact.canonical_event_id for fact in source.facts)
        != tuple(sorted(i12_ingestion_owner.EXPECTED_EVENT_IDS))
    ):
        raise ValueError("I12_NARROW_PROJECTION_IDENTITY_INVALID")
    if any(
        fact.human_review_completed is not True
        or fact.legacy_completed_review_status != generic.COMPLETED_HUMAN_POSITIVE
        or fact.task_relevance_disposition != generic.TASK_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_INCLUDE
        or fact.human_training_excluded is not False
        or fact.source_decision_schema != i12_ingestion_owner.FORMAL_DECISION_SCHEMA
        or fact.source_decision_sha256 != source.binding.sha256
        or fact.source_binding_path != source.binding.source_path
        or any(hasattr(fact, name) for name in FORBIDDEN_FACT_ATTRIBUTES)
        for fact in source.facts
    ):
        raise ValueError("I12_GENERIC_FACT_INVALID_OR_RICH_LEAKAGE")
    return {
        "generic_fact_fields": observed_fields,
        "fact_count": 4,
        "rich_field_leakage_count": 0,
        "binding_namespace": source.binding.path_namespace,
    }


def _verify_sources(root: Path) -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    tuple[generic.NormalizedDecisionSource, ...],
]:
    existing = two_a2_successor.load_real_completed_decision_sources_with_2a2_v1(root)
    future = subject.load_real_completed_decision_sources_with_i12_v1(root)
    existing_ids = [fact.canonical_event_id for source in existing for fact in source.facts]
    future_ids = [fact.canonical_event_id for source in future for fact in source.facts]
    if (
        len(existing) != 13
        or tuple(len(source.facts) for source in existing) != EXISTING_SOURCE_FACT_COUNTS
        or len(existing_ids) != 95
        or len(set(existing_ids)) != 95
        or len({source.binding.review_unit_id for source in existing}) != 13
        or len({source.binding.stable_identity for source in existing}) != 13
    ):
        raise ValueError("EXISTING_SOURCE_CHAIN_NOT_EXACT13_95")
    if (
        len(future) != 14
        or tuple(len(source.facts) for source in future) != FUTURE_SOURCE_FACT_COUNTS
        or len(future_ids) != 99
        or len(set(future_ids)) != 99
        or len({source.binding.review_unit_id for source in future}) != 14
        or len({source.binding.stable_identity for source in future}) != 14
        or future[:-1] != existing
        or set(i12_ingestion_owner.EXPECTED_EVENT_IDS) & set(existing_ids)
    ):
        raise ValueError("FUTURE_SOURCE_CHAIN_NOT_EXACT14_99")
    return existing, future


def _verify_historical_and_onl(root: Path) -> tuple[
    tuple[dict[str, str], ...], tuple[dict[str, str], ...]
]:
    historical = generic.load_real_historical_reconciliation_v1(root)
    subject._prove_i12_original_unreviewed_prior_v1(historical)
    target_ids = set(i12_ingestion_owner.EXPECTED_EVENT_IDS)
    target = [row for row in historical if row["canonical_event_id"] in target_ids]
    if len(target) != 4 or any(
        row["raw_review_unit_id"] != i12_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
        or row["raw_priority_rank"] != "17"
        or row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in target
    ):
        raise ValueError("I12_HISTORICAL_PRIOR_INVALID")
    adapted = onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        historical
    )
    subject._prove_i12_rows_unchanged_after_onl_normalization_v1(historical, adapted)
    before = {row["canonical_event_id"]: row for row in target}
    after = {
        row["canonical_event_id"]: row
        for row in adapted
        if row["canonical_event_id"] in target_ids
    }
    if before != after:
        raise ValueError("ONL_ADAPTER_CHANGED_I12_ROW")
    return historical, adapted


def _verify_reconciliation(root: Path) -> generic.ReconciliationResult:
    result = subject.reconcile_real_completed_human_decisions_with_i12_v1(root)
    if result.review_summary != EXPECTED_REVIEW_SUMMARY:
        raise ValueError("I12_RECONCILIATION_SUMMARY_INVALID")
    target_ids = set(i12_ingestion_owner.EXPECTED_EVENT_IDS)
    facts = [fact for fact in result.normalized_facts if fact.canonical_event_id in target_ids]
    rows = [row for row in result.reconciled_rows if row["canonical_event_id"] in target_ids]
    if len(facts) != 4 or any(
        fact.task_relevance_disposition != generic.TASK_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_INCLUDE
        or fact.human_training_excluded is not False
        for fact in facts
    ):
        raise ValueError("I12_FINAL_GENERIC_FACTS_INVALID")
    if len(rows) != 4 or any(
        row["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE
        or row["calibration_eligible"] != "false"
        or row["calibration_exclusion_reason"] != generic.COMPLETED_HUMAN_POSITIVE
        for row in rows
    ):
        raise ValueError("I12_FINAL_TRANSITION_INVALID")
    return result


def _expect_subject_failure(callable_: object, token: str) -> None:
    try:
        callable_()  # type: ignore[operator]
    except subject.CompletedDecisionReconciliationWithI12Error as error:
        if token not in str(error):
            raise ValueError("FAIL_CLOSED_TOKEN_INVALID:" + str(error)) from error
    else:
        raise ValueError("FAIL_CLOSED_PROBE_NOT_REJECTED:" + token)


def _verify_fail_closed_probes(
    bound: dict[str, object],
    historical: tuple[dict[str, str], ...],
    adapted: tuple[dict[str, str], ...],
) -> dict[str, bool]:
    binding_drift = copy.deepcopy(bound)
    binding_drift["formal_decision_binding"]["SHA256"] = "0" * 64  # type: ignore[index]
    _expect_subject_failure(
        lambda: subject._project_validated_i12_binding_v1(binding_drift),
        "I12_FORMAL_DECISION_BINDING_INVALID",
    )
    role_drift = copy.deepcopy(bound)
    role_drift["formal"]["selected_role_partition"]["role_profile"] = "WRONG"  # type: ignore[index]
    _expect_subject_failure(
        lambda: subject._project_validated_i12_binding_v1(role_drift),
        "I12_CANDIDATE0_DIRECT_ROLE_PARTITION_INVALID",
    )
    missing = tuple(
        row
        for row in historical
        if row["canonical_event_id"] != i12_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    _expect_subject_failure(
        lambda: subject._prove_i12_original_unreviewed_prior_v1(missing),
        "I12_HISTORICAL_EVENT_MISSING",
    )
    changed = [dict(row) for row in adapted]
    target = next(
        row
        for row in changed
        if row["canonical_event_id"] == i12_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    target["current_status_authority_sources_json"] = '["unexpected"]'
    _expect_subject_failure(
        lambda: subject._prove_i12_rows_unchanged_after_onl_normalization_v1(
            historical, changed
        ),
        "ONL_ADAPTER_CHANGED_I12_ROW",
    )
    return {
        "source_identity_drift_rejected": True,
        "rich_role_drift_rejected": True,
        "historical_missing_event_rejected": True,
        "onl_i12_mutation_rejected": True,
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
        raise ValueError("B4_NEW_RECONCILIATION_PYTHON_FILES_NOT_ALL_SCANNED")
    return {**required, "new_reconciliation_files_scanned": True}


def run_check_v1(repo_root: Path = ROOT) -> dict[str, object]:
    """Run every read-only I12 reconciliation candidate gate."""

    root = repo_root.resolve()
    exact4 = _verify_candidate_exact4(root)
    lineage = _verify_frozen_runtime_lineage(root)
    architecture = _verify_architecture(root)
    bound = i12_ingestion_owner.load_frozen_formal_decision_v1(root)
    rich = _verify_rich_authority(bound)
    source = subject._project_validated_i12_binding_v1(bound)
    projection = _verify_projection(source)
    existing, future = _verify_sources(root)
    historical, adapted = _verify_historical_and_onl(root)
    result = _verify_reconciliation(root)
    protections = _verify_fail_closed_probes(bound, historical, adapted)
    b4 = _verify_b4_core(root)
    dispositions = Counter(fact.training_disposition for fact in result.normalized_facts)
    return {
        "status": "PASS",
        "repository": exact4,
        "runtime_lineage": lineage,
        "architecture": architecture,
        "rich_i12": rich,
        "projection": projection,
        "current_source_count": len(existing),
        "current_fact_count": sum(len(source.facts) for source in existing),
        "future_source_count": len(future),
        "future_fact_count": sum(len(source.facts) for source in future),
        "event_collisions": 0,
        "i12_prior_exact4_valid": True,
        "i12_rows_changed_by_onl": 0,
        "transition_adapter_created": False,
        "review_summary": result.review_summary,
        "training_dispositions": dict(dispositions),
        "fail_closed_probes": protections,
        "b4_core": b4,
        "reconciliation_data_outputs_created": 0,
        "census_refresh": False,
        "queue_refresh": False,
        "training_started": False,
        "ready_for_training": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    report = run_check_v1(parser.parse_args(argv).repo_root)
    if report["ready_for_training"] is not False:
        raise ValueError("READY_FOR_TRAINING_MUST_BE_FALSE")
    print("PASS")
    print(report["repository"]["lifecycle"])
    print("current_sources=13 current_facts=95")
    print("future_sources=14 future_facts=99 collisions=0")
    print("I12_rows_changed_by_ONL=0")
    print("reconciliation_outputs=0 census_refresh=false queue_refresh=false")
    print("TRAINING_STARTED=false READY_FOR_TRAINING=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
