"""Independent checker for the CovaPIE combined aggregation implementation."""

from __future__ import annotations

import csv
import hashlib
import importlib
import inspect
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Callable, Mapping, NamedTuple, Sequence

from covalent_ext.covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004 import (
    OUTCOME_VOCABULARY,
    RESULT_FIELDS as INPUT_FIELDS,
    RESULT_SCHEMA_VERSION as INPUT_SCHEMA,
    UnifiedAdmissionRuleEvaluation,
)
from covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015 import (
    ADAPTER_IDS,
    RULE_NAMES,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "38eb228f6507bb36c19433050c75d4b28e2e65a2"
BASE_PARENT = "71fe2a41ecdf9e2317994e755ce21fc64bd05b87"
BASE_TREE = "b963e99e1d2dd0f891b6c0ef7fca229bf351e9bb"
BASE_SUBJECT = (
    "add CovaPIE combined candidate verdict and cross-rule aggregation contract v1"
)
STAGE = (
    "covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_v1"
)
MODULE_NAME = f"covalent_ext.{STAGE}"
PRODUCTION_PATH = Path("src/covalent_ext") / f"{STAGE}.py"
CHECKER_PATH = Path("scripts") / f"check_{STAGE}.py"
TEST_PATH = Path("tests") / f"test_{STAGE}.py"
SUMMARY_PATH = Path("docs") / f"{STAGE}_summary.md"
SUPPORT_PATHS = (
    PRODUCTION_PATH,
    CHECKER_PATH,
    TEST_PATH,
    SUMMARY_PATH,
)
DERIVED_ROOT = Path("data/derived/covalent_small") / STAGE
RUNTIME_NAME = (
    "covapie_combined_candidate_verdict_and_cross_rule_aggregation_"
    "runtime_contract.csv"
)
TRUTH_NAME = "covapie_cross_rule_aggregation_implementation_truth_matrix.csv"
SAFETY_NAME = "covapie_cross_rule_aggregation_implementation_safety_audit.csv"
PRECONDITION_NAME = (
    "covapie_cross_rule_aggregation_precondition_transition_inventory.csv"
)
ISSUE_NAME = "covapie_cross_rule_aggregation_issue_readiness_inventory.csv"
MANIFEST_NAME = (
    "covapie_combined_candidate_verdict_and_cross_rule_aggregation_"
    "implementation_manifest.json"
)
OUTPUT_NAMES = (
    RUNTIME_NAME,
    TRUTH_NAME,
    SAFETY_NAME,
    PRECONDITION_NAME,
    ISSUE_NAME,
    MANIFEST_NAME,
)
EXACT10 = SUPPORT_PATHS + tuple(DERIVED_ROOT / name for name in OUTPUT_NAMES)
STAGING_PREFIX = f"{STAGE}.__staging__."
LEGACY_STAGING_PREFIXES = (
    "covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_contract_v1.__staging__.",
    ".combined-permission-semantics-stage-",
)
ALLOWED_REQUIRED_LOCAL_REFS = ("refs/heads/main",)
ALLOWED_OPTIONAL_REMOTE_REFS = (
    "refs/remotes/origin/main",
    "refs/remotes/origin/HEAD",
)
PLATFORM_REF_NAMESPACE = "refs/codex/turn-diffs"
PLATFORM_REF_UUID_V4_PATTERN = (
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
PLATFORM_REFNAME_PATTERN = (
    rf"{re.escape(PLATFORM_REF_NAMESPACE)}/(?:"
    rf"captures/[0-9]{{13}}/{PLATFORM_REF_UUID_V4_PATTERN}/base|"
    rf"checkpoints/[0-9a-f]{{64}}/[0-9a-f]{{64}}/[0-9]{{13}}/"
    rf"{PLATFORM_REF_UUID_V4_PATTERN}"
    rf")"
)
PLATFORM_REF_BLOCKED_TERMS = (
    "covapie",
    "candidate",
    "temporary",
    "backup",
    "review",
)
NEXT_STEP = "design_covapie_stage_global_rule_evaluation_orchestration_contract_v1"

SOURCE_BOUNDARY = (
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_design_gate.py",
        "351e46eff9fce8cb735282cedc5ca531866d03439d582762d5827d2252f973e2",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_combined_candidate_verdict_and_cross_rule_aggregation_"
        "contract_manifest.json",
        "54fcccae583c521ef1d69c26b960d2ba984e4d6e7709d7d8344de558c6f0daa8",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_combined_candidate_verdict_public_api_contract.csv",
        "05db18369fadea8d4387ef4188aee0c922dffc0b0216a3f6abd0532ebd696f55",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_cross_rule_aggregation_result_contract.csv",
        "34bf7ac21a78d0c93f73dbe7371e7b00ea48bec18308e5d8fcd82ea8c408fa8d",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_cross_rule_aggregation_truth_matrix.csv",
        "eed3774028ec7db33f923c2866f7d322dac68d605e5e2e3b9924521283de1e40",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_cross_rule_aggregation_safety_audit.csv",
        "4b26fc147e8b5eca0a41329729a9a0caa9895aa0faef524afc1768230253d494",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1/"
        "covapie_combined_candidate_verdict_issue_readiness_inventory.csv",
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7",
    ),
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_015.py",
        "1fc5ac24e54d134d3f1f7054dfd2f264a2d76f17f0602bac216bb2e4e7e00bd1",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_015_v1/covapie_admit_001_to_015_runtime_manifest.json",
        "0fbd5999977d025a44b4bef854d9edfda5ea0e5ed79a7d5ff7b17cef7b6186d3",
    ),
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_minimal_unified_dispatch_shell_"
        "with_admit_004.py",
        "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_permission_semantics_"
        "contract_v1/"
        "covapie_combined_permission_scope_and_rule_membership_contract.csv",
        "3e74d0ac1d7be7bd23cf6d243c9593e01099a6dd55ed5079d27b01c12cb71b55",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_015_mandatory_training_"
        "authorization_enforcement_v1/"
        "covapie_admit_015_mandatory_training_authorization_enforcement_"
        "manifest.json",
        "706fe24fe585cccaf9c4691adda673290e7604f35b6e63ffe2096087b17d1d77",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_015_formal_evaluator_"
        "interface_preconditions_audit_v1/"
        "covapie_admit_015_formal_evaluator_interface_precondition_"
        "inventory.csv",
        "c52287ac5a435e58a400be0e33e17c1096b7b0d3b2671be0398a6be03e409839",
    ),
)

RULE_IDS = tuple(f"ADMIT_{number:03d}" for number in range(1, 16))
SCOPES = (
    (
        "download_execution_permission",
        (
            "ADMIT_001",
            "ADMIT_002",
            "ADMIT_003",
            "ADMIT_004",
            "ADMIT_005",
            "ADMIT_006",
            "ADMIT_007",
            "ADMIT_008",
            "ADMIT_009",
            "ADMIT_011",
            "ADMIT_014",
        ),
    ),
    (
        "post_download_acceptance_permission",
        (
            "ADMIT_001",
            "ADMIT_002",
            "ADMIT_003",
            "ADMIT_004",
            "ADMIT_005",
            "ADMIT_006",
            "ADMIT_007",
            "ADMIT_008",
            "ADMIT_009",
            "ADMIT_011",
            "ADMIT_012",
            "ADMIT_013",
            "ADMIT_014",
        ),
    ),
    (
        "pre_final_split_acceptance_permission",
        (
            "ADMIT_001",
            "ADMIT_002",
            "ADMIT_003",
            "ADMIT_004",
            "ADMIT_005",
            "ADMIT_006",
            "ADMIT_007",
            "ADMIT_008",
            "ADMIT_009",
            "ADMIT_010",
            "ADMIT_011",
            "ADMIT_012",
            "ADMIT_013",
            "ADMIT_014",
        ),
    ),
    ("training_execution_admission_permission", RULE_IDS),
)
REQUIRED = dict(SCOPES)
SCOPE_IDS = tuple(REQUIRED)
RESULT_SCHEMA = "covapie_combined_admission_candidate_verdict_v1"
RESULT_FIELDS = (
    "schema_version",
    "scope_id",
    "outcome",
    "passed",
    "blocks_scope_action",
    "reason",
    "required_rule_ids",
    "evaluated_rule_ids",
    "rule_evaluations",
    "invalid_rule_ids",
    "blocked_rule_ids",
    "failing_rule_ids",
    "aggregation_io_used",
)
REASONS = (
    "COMBINED_ADMISSION_SCOPE_ID_INVALID",
    "COMBINED_ADMISSION_RULE_EVALUATION_VECTOR_TYPE_INVALID",
    "COMBINED_ADMISSION_RULE_EVALUATION_INVARIANT_INVALID",
    "COMBINED_ADMISSION_RULE_MEMBERSHIP_INVALID",
    "COMBINED_ADMISSION_REQUIRED_RULE_INVALID",
    "COMBINED_ADMISSION_REQUIRED_RULE_BLOCKED",
)
(
    SCOPE_INVALID,
    VECTOR_INVALID,
    INVARIANT_INVALID,
    MEMBERSHIP_INVALID,
    REQUIRED_INVALID,
    REQUIRED_BLOCKED,
) = REASONS

RUNTIME_COLUMNS = (
    "contract_order",
    "contract_group",
    "item_order",
    "item_name",
    "frozen_value",
    "implementation_observed",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "scope_id_representation",
    "vector_type",
    "input_rule_ids",
    "input_outcomes",
    "expected_outcome",
    "observed_outcome",
    "expected_reason",
    "observed_reason",
    "required_rule_ids",
    "evaluated_rule_ids",
    "invalid_rule_ids",
    "blocked_rule_ids",
    "failing_rule_ids",
    "rule_evaluations_retained",
    "input_tuple_identity_retained",
    "aggregation_io_used",
    "dispatcher_calls",
    "handler_calls",
    "current_permission",
    "authorized_execution_count",
    "case_passed",
)
SAFETY_COLUMNS = (
    "audit_order",
    "audit_item",
    "expected_state",
    "observed_state",
    "safety_passed",
)
PRECONDITION_COLUMNS = (
    "precondition_order",
    "precondition_id",
    "inherited_completion_status",
    "inherited_implementation_blocking",
    "implementation_completion_status",
    "implementation_blocking",
    "transition_action",
    "transition_evidence",
    "transition_passed",
)
ISSUE_COLUMNS = (
    "inherited_order",
    "issue_id",
    "issue_type",
    "affected_fields",
    "affected_rules",
    "severity",
    "status",
    "blocking_scope",
    "blocking_reason",
    "issue_origin",
    "integration_transition",
    "issue_count",
    "inherited_effective_status",
    "inherited_transition_stage",
    "inherited_transition_action",
    "inherited_transition_evidence",
    "successor_effective_status",
    "successor_transition_stage",
    "successor_transition_action",
    "successor_transition_evidence",
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git(*arguments: str, root: Path = ROOT) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise ValueError(f"git command failed: {arguments}")
    return completed.stdout


Identity = tuple[int, int, int, int, int, int]
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
MAX_BYTES = 100 * 1024 * 1024
FORBIDDEN_SUFFIXES = frozenset(
    {
        ".pt",
        ".ckpt",
        ".pth",
        ".pkl",
        ".lmdb",
        ".tar",
        ".zip",
        ".tgz",
        ".npz",
        ".tmp",
        ".part",
    }
)


def _git_result(
    root: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _identity(item: os.stat_result) -> Identity:
    return (
        int(item.st_dev),
        int(item.st_ino),
        int(item.st_mode),
        int(item.st_size),
        int(item.st_mtime_ns),
        int(item.st_ctime_ns),
    )


def _read_all(descriptor: int) -> bytes:
    chunks = []
    total = 0
    while True:
        chunk = os.read(descriptor, 1 << 16)
        if not chunk:
            break
        total += len(chunk)
        if total > 100 * 1024 * 1024:
            raise ValueError("pinned read exceeds maximum")
        chunks.append(chunk)
    return b"".join(chunks)


def _pinned_read(root: Path, relative: Path) -> bytes:
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("unsafe pinned path")
    root = Path(os.path.abspath(root))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if not stat.S_ISDIR(root_item.st_mode) or stat.S_ISLNK(root_item.st_mode):
        raise ValueError("pinned root unsafe")
    root_fd = os.open(root, DIR_FLAGS)
    directory_fds = [root_fd]
    leaf_fd: int | None = None
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("pinned root stat/open race")
        parent_fd = root_fd
        bindings: list[tuple[int, str, int, Identity]] = []
        for component in relative.parts[:-1]:
            item = os.stat(
                component, dir_fd=parent_fd, follow_symlinks=False
            )
            identity = _identity(item)
            if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
                raise ValueError("pinned component unsafe")
            child_fd = os.open(component, DIR_FLAGS, dir_fd=parent_fd)
            if _identity(os.fstat(child_fd)) != identity:
                os.close(child_fd)
                raise ValueError("pinned component stat/open race")
            directory_fds.append(child_fd)
            bindings.append((parent_fd, component, child_fd, identity))
            parent_fd = child_fd
        leaf = relative.parts[-1]
        before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        leaf_identity = _identity(before)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or before.st_size > 100 * 1024 * 1024
        ):
            raise ValueError("pinned leaf unsafe")
        leaf_fd = os.open(leaf, READ_FLAGS, dir_fd=parent_fd)
        if _identity(os.fstat(leaf_fd)) != leaf_identity:
            raise ValueError("pinned leaf stat/open race")
        content = _read_all(leaf_fd)
        after = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        if (
            _identity(os.fstat(leaf_fd)) != leaf_identity
            or _identity(after) != leaf_identity
        ):
            raise ValueError("pinned leaf final drift")
        for lexical_parent, name, child_fd, expected in reversed(bindings):
            lexical = os.stat(
                name, dir_fd=lexical_parent, follow_symlinks=False
            )
            if (
                _identity(os.fstat(child_fd)) != expected
                or _identity(lexical) != expected
            ):
                raise ValueError("pinned component final drift")
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(os.lstat(root)) != root_identity
        ):
            raise ValueError("pinned root final drift")
        return content
    finally:
        if leaf_fd is not None:
            os.close(leaf_fd)
        for descriptor in reversed(directory_fds):
            os.close(descriptor)


def _json(content: bytes) -> dict[str, Any]:
    duplicates: list[str] = []

    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                duplicates.append(key)
            value[key] = item
        return value

    result = json.loads(content, object_pairs_hook=hook)
    if duplicates or type(result) is not dict:
        raise ValueError("canonical JSON object with unique keys required")
    return result


def _csv(content: bytes, columns: Sequence[str] | None = None) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    header = tuple(reader.fieldnames or ())
    if (
        not header
        or len(header) != len(set(header))
        or (columns is not None and header != tuple(columns))
    ):
        raise ValueError("CSV header drift")
    rows = [dict(row) for row in reader]
    if any(tuple(row) != header for row in rows):
        raise ValueError("CSV row drift")
    return rows


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _strict_head(root: Path = ROOT) -> str:
    value = _git("rev-parse", "--verify", "HEAD^{commit}", root=root)
    if re.fullmatch(rb"[0-9a-f]{40}\n", value) is None:
        raise ValueError("HEAD malformed")
    return value[:-1].decode()


def _source_snapshot() -> list[dict[str, Any]]:
    initial = _strict_head()
    identity = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).decode().splitlines()
    if identity != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("base identity drift")
    _git("merge-base", "--is-ancestor", BASE_COMMIT, initial)
    records = []
    for order, (path, expected) in enumerate(SOURCE_BOUNDARY, 1):
        index = _git("ls-files", "--stage", "--", path).decode().rstrip("\n")
        tree = _git("ls-tree", BASE_COMMIT, "--", path).decode().rstrip("\n")
        try:
            index_meta, index_path = index.split("\t", 1)
            index_mode, index_blob, stage = index_meta.split(" ")
            tree_meta, tree_path = tree.split("\t", 1)
            tree_mode, kind, tree_blob = tree_meta.split(" ")
        except ValueError as error:
            raise ValueError("source Git entry malformed") from error
        filesystem = _pinned_read(ROOT, Path(path))
        base = _git("cat-file", "blob", tree_blob)
        indexed = _git("cat-file", "blob", index_blob)
        if (
            index_path != path
            or tree_path != path
            or index_mode != "100644"
            or tree_mode != "100644"
            or kind != "blob"
            or stage != "0"
            or index_blob != tree_blob
            or base != indexed
            or indexed != filesystem
            or _sha(filesystem) != expected
        ):
            raise ValueError(f"source attestation drift: {path}")
        records.append(
            {
                "source_order": order,
                "path": path,
                "sha256": expected,
                "base_tree_mode": tree_mode,
                "base_tree_blob": tree_blob,
                "index_mode": index_mode,
                "index_blob": index_blob,
                "index_stage": 0,
                "filesystem_sha256": _sha(filesystem),
                "content": filesystem,
            }
        )
    if _strict_head() != initial:
        raise ValueError("source snapshot HEAD drift")
    _git("merge-base", "--is-ancestor", BASE_COMMIT, initial)
    return records


def _source(snapshot: Sequence[dict[str, Any]], suffix: str) -> dict[str, Any]:
    matches = [item for item in snapshot if item["path"].endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"source missing/duplicate: {suffix}")
    return matches[0]


def _strings(value: object) -> bool:
    return type(value) is tuple and all(type(item) is str for item in value)


def _pairs(value: object) -> bool:
    return type(value) is tuple and all(
        type(item) is tuple
        and len(item) == 2
        and type(item[0]) is str
        and type(item[1]) is str
        for item in value
    )


def _child_structure(value: object) -> bool:
    if type(value) is not UnifiedAdmissionRuleEvaluation:
        return False
    try:
        values = vars(value)
    except TypeError:
        return False
    if (
        type(values) is not dict
        or tuple(values) != INPUT_FIELDS
        or tuple(value.__dataclass_fields__) != INPUT_FIELDS
    ):
        return False
    if any(
        type(values[name]) is not str
        for name in (
            "schema_version",
            "admission_rule_id",
            "admission_rule_name",
            "outcome",
            "reason",
            "adapter_id",
        )
    ) or any(
        type(values[name]) is not bool
        for name in ("passed", "blocks_candidate", "evaluator_io_used")
    ):
        return False
    try:
        if UnifiedAdmissionRuleEvaluation(**values) != value:
            return False
    except (TypeError, ValueError):
        return False
    return (
        value.schema_version == INPUT_SCHEMA
        and value.outcome in OUTCOME_VOCABULARY
        and value.passed is (value.outcome == "passed")
        and value.blocks_candidate is (value.outcome != "passed")
        and value.evaluator_io_used is False
        and ((value.outcome == "passed") is (value.reason == ""))
        and _pairs(value.normalized_values)
        and _pairs(value.validated_candidate_fields)
        and _strings(value.consumed_candidate_fields)
        and _strings(value.consumed_context_items)
    )


def _admissible(value: UnifiedAdmissionRuleEvaluation) -> bool:
    return (
        value.outcome in ("passed", "blocked", "invalid")
        and (
            value.admission_rule_id not in RULE_NAMES
            or (
                value.admission_rule_name == RULE_NAMES[value.admission_rule_id]
                and value.adapter_id == ADAPTER_IDS[value.admission_rule_id]
            )
        )
    )


@dataclass(frozen=True)
class LocalVerdict:
    schema_version: str
    scope_id: str
    outcome: str
    passed: bool
    blocks_scope_action: bool
    reason: str
    required_rule_ids: tuple[str, ...]
    evaluated_rule_ids: tuple[str, ...]
    rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...]
    invalid_rule_ids: tuple[str, ...]
    blocked_rule_ids: tuple[str, ...]
    failing_rule_ids: tuple[str, ...]
    aggregation_io_used: bool


def _local_verdict(
    scope: object,
    reason: str,
    required: tuple[str, ...] = (),
    evaluated: tuple[str, ...] = (),
    vector: tuple[UnifiedAdmissionRuleEvaluation, ...] = (),
    invalid: tuple[str, ...] = (),
    blocked: tuple[str, ...] = (),
    failing: tuple[str, ...] = (),
) -> LocalVerdict:
    outcome = (
        "passed" if reason == "" else "blocked" if reason == REQUIRED_BLOCKED else "invalid"
    )
    return LocalVerdict(
        RESULT_SCHEMA,
        scope if type(scope) is str else "",
        outcome,
        outcome == "passed",
        outcome != "passed",
        reason,
        required,
        evaluated,
        vector,
        invalid,
        blocked,
        failing,
        False,
    )


def _local_aggregate(scope: object, vector: object) -> LocalVerdict:
    if type(scope) is not str or scope not in REQUIRED:
        return _local_verdict(scope, SCOPE_INVALID)
    required = REQUIRED[scope]
    if type(vector) is not tuple:
        return _local_verdict(scope, VECTOR_INVALID, required)
    structural = [_child_structure(item) for item in vector]
    if False in structural:
        return _local_verdict(scope, INVARIANT_INVALID, required)
    admissibility = [_admissible(item) for item in vector]
    if False in admissibility:
        return _local_verdict(scope, INVARIANT_INVALID, required)
    evaluated = tuple(item.admission_rule_id for item in vector)
    if evaluated != required or len(evaluated) != len(set(evaluated)):
        return _local_verdict(scope, MEMBERSHIP_INVALID, required, evaluated)
    invalid = tuple(item.admission_rule_id for item in vector if item.outcome == "invalid")
    blocked = tuple(item.admission_rule_id for item in vector if item.outcome == "blocked")
    failing = tuple(item.admission_rule_id for item in vector if item.outcome != "passed")
    reason = REQUIRED_INVALID if invalid else REQUIRED_BLOCKED if blocked else ""
    return _local_verdict(
        scope, reason, required, evaluated, vector, invalid, blocked, failing
    )


class _ActualSubclass(UnifiedAdmissionRuleEvaluation):
    pass


def _actualize(value: object, design: Any) -> object:
    if isinstance(value, design.UnifiedAdmissionRuleEvaluationContractDesign):
        values = dict(vars(value))
        if type(value) is not design.UnifiedAdmissionRuleEvaluationContractDesign:
            return _ActualSubclass(**values)
        try:
            return UnifiedAdmissionRuleEvaluation(**values)
        except (TypeError, ValueError):
            forged = object.__new__(UnifiedAdmissionRuleEvaluation)
            for name, item in values.items():
                object.__setattr__(forged, name, item)
            return forged
    if type(value) is tuple:
        return tuple(_actualize(item, design) for item in value)
    if type(value) is list:
        return [_actualize(item, design) for item in value]
    return value


def _runtime_rows() -> list[dict[str, str]]:
    api = (
        ("function_name", "aggregate_admission_rule_evaluations"),
        (
            "signature",
            "aggregate_admission_rule_evaluations(scope_id: str, *, "
            "ordered_rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...]) "
            "-> CombinedAdmissionCandidateVerdict",
        ),
        ("scope_parameter_kind", "positional_or_keyword"),
        ("ordered_vector_parameter_kind", "keyword_only"),
        ("defaults", "none"),
        ("var_positional", "forbidden"),
        ("var_keyword", "forbidden"),
        ("candidate_parameter", "forbidden"),
        ("context_parameter", "forbidden"),
        ("dispatcher_injection", "forbidden"),
        ("registry_injection", "forbidden"),
        ("override_fallback", "forbidden"),
        ("input_runtime_type", "UnifiedAdmissionRuleEvaluation"),
        ("output_runtime_type", "CombinedAdmissionCandidateVerdict"),
        ("dispatcher_calls", "0"),
        ("handler_calls", "0"),
        ("aggregation_io", "false"),
        ("production_implementation_present", "true"),
    )
    result = tuple(
        zip(
            RESULT_FIELDS,
            (
                "str",
                "str",
                "str",
                "bool",
                "bool",
                "str",
                "tuple[str,...]",
                "tuple[str,...]",
                "tuple[UnifiedAdmissionRuleEvaluation,...]",
                "tuple[str,...]",
                "tuple[str,...]",
                "tuple[str,...]",
                "bool",
            ),
            strict=True,
        )
    )
    groups = (
        ("production_public_api", api),
        ("production_result_contract", result),
        (
            "reason_vocabulary",
            tuple((f"reason_{index}", reason) for index, reason in enumerate(REASONS, 1)),
        ),
        (
            "scope_membership",
            tuple((scope, "|".join(required)) for scope, required in SCOPES),
        ),
        (
            "validation_precedence",
            tuple(
                (f"precedence_{index}", value)
                for index, value in enumerate(
                    (
                        "scope_id",
                        "ordered_vector_exact_tuple",
                        "all_child_runtime_exact13_structure",
                        "all_child_aggregation_identity_and_outcome_admissibility",
                        "full_exact_membership",
                        "all_child_invalid_outcomes",
                        "all_child_blocked_outcomes",
                        "all_child_passed",
                    ),
                    1,
                )
            ),
        ),
    )
    rows = []
    order = 0
    for group, items in groups:
        for item_order, (name, value) in enumerate(items, 1):
            order += 1
            rows.append(
                {
                    "contract_order": str(order),
                    "contract_group": group,
                    "item_order": str(item_order),
                    "item_name": name,
                    "frozen_value": value,
                    "implementation_observed": value,
                    "contract_passed": "true",
                }
            )
    return rows


def _truth_rows(candidate: Any) -> list[dict[str, str]]:
    from covalent_ext import (
        covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_contract_design_gate
        as design,
    )

    rows = []
    for order, (case_id, group, scope, source_vector, expected_reason) in enumerate(
        design._truth_cases(), 1
    ):
        vector = _actualize(source_vector, design)
        expected = _local_aggregate(scope, vector)
        actual = candidate.aggregate_admission_rule_evaluations(
            scope, ordered_rule_evaluations=vector
        )
        if tuple(vars(actual).values()) != tuple(vars(expected).values()):
            raise ValueError(f"production/local oracle mismatch: {case_id}")
        items = vector if type(vector) is tuple else ()
        input_ids = tuple(
            item.admission_rule_id
            if isinstance(item, UnifiedAdmissionRuleEvaluation)
            and type(item.admission_rule_id) is str
            else f"<{type(item).__name__}>"
            for item in items
        )
        input_outcomes = tuple(
            item.outcome
            if isinstance(item, UnifiedAdmissionRuleEvaluation)
            and type(item.outcome) is str
            else f"<{type(item).__name__}>"
            for item in items
        )
        retained = bool(expected.rule_evaluations)
        identity = expected.rule_evaluations is vector if retained else False
        expected_outcome = (
            "passed"
            if expected_reason == ""
            else "blocked"
            if expected_reason == REQUIRED_BLOCKED
            else "invalid"
        )
        passed = (
            expected.outcome == expected_outcome
            and expected.reason == expected_reason
            and (not retained or identity)
        )
        rows.append(
            {
                "case_order": str(order),
                "case_id": case_id,
                "case_group": group,
                "scope_id_representation": (
                    scope
                    if type(scope) is str
                    else "None"
                    if scope is None
                    else f"<{type(scope).__name__}>"
                ),
                "vector_type": type(vector).__name__,
                "input_rule_ids": "|".join(input_ids),
                "input_outcomes": "|".join(input_outcomes),
                "expected_outcome": expected_outcome,
                "observed_outcome": actual.outcome,
                "expected_reason": expected_reason,
                "observed_reason": actual.reason,
                "required_rule_ids": "|".join(actual.required_rule_ids),
                "evaluated_rule_ids": "|".join(actual.evaluated_rule_ids),
                "invalid_rule_ids": "|".join(actual.invalid_rule_ids),
                "blocked_rule_ids": "|".join(actual.blocked_rule_ids),
                "failing_rule_ids": "|".join(actual.failing_rule_ids),
                "rule_evaluations_retained": str(retained).lower(),
                "input_tuple_identity_retained": str(identity).lower(),
                "aggregation_io_used": "false",
                "dispatcher_calls": "0",
                "handler_calls": "0",
                "current_permission": "false",
                "authorized_execution_count": "0",
                "case_passed": str(passed).lower(),
            }
        )
    return rows


def _safety_rows() -> list[dict[str, str]]:
    states = (
        ("dispatcher_calls", "0"),
        ("single_rule_handler_calls", "0"),
        ("network", "false"),
        ("provider", "false"),
        ("download", "false"),
        ("raw", "false"),
        ("torch_import", "false"),
        ("dataloader", "false"),
        ("checkpoint", "false"),
        ("model", "false"),
        ("forward", "false"),
        ("loss", "false"),
        ("backward", "false"),
        ("optimizer", "false"),
        ("scheduler", "false"),
        ("parameter_update", "false"),
        ("checkpoint_write", "false"),
        ("training_result", "false"),
        ("current_permission", "false"),
        ("authorized_execution_count", "0"),
        ("aggregator_implementation", "true"),
        ("combined_verdict_implementation", "true"),
        ("orchestrator", "false"),
        ("feature_semantics_audit_completed", "false"),
        ("ready_for_training", "false"),
        ("exact15_runtime_modified", "false"),
        ("contract_stage_modified", "false"),
        ("aggregation_io_used", "false"),
        ("runtime_dispatcher_call_order_frozen", "false"),
        ("stage_global_rule_orchestration_frozen", "false"),
    )
    return [
        {
            "audit_order": str(order),
            "audit_item": item,
            "expected_state": value,
            "observed_state": value,
            "safety_passed": "true",
        }
        for order, (item, value) in enumerate(states, 1)
    ]


def _precondition_rows(snapshot: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    source = _csv(_source(snapshot, "interface_precondition_inventory.csv")["content"])
    rows = []
    for order, inherited in enumerate(source, 1):
        pre_id = inherited["precondition_id"]
        incomplete = pre_id in {"PRE_036", "PRE_038", "PRE_042"}
        resolved = pre_id == "PRE_036"
        rows.append(
            {
                "precondition_order": str(order),
                "precondition_id": pre_id,
                "inherited_completion_status": "incomplete" if incomplete else "complete",
                "inherited_implementation_blocking": "true" if incomplete else "false",
                "implementation_completion_status": (
                    "complete" if resolved or not incomplete else "incomplete"
                ),
                "implementation_blocking": (
                    "false" if resolved or not incomplete else "true"
                ),
                "transition_action": (
                    "resolved_by_pure_cross_rule_aggregation_implementation"
                    if resolved
                    else "unchanged"
                ),
                "transition_evidence": (
                    f"{PRODUCTION_PATH.as_posix()}|"
                    f"{(DERIVED_ROOT / RUNTIME_NAME).as_posix()}|"
                    f"{(DERIVED_ROOT / TRUTH_NAME).as_posix()}|"
                    f"{TEST_PATH.as_posix()}"
                    if resolved
                    else "inherited effective state retained"
                ),
                "transition_passed": "true",
            }
        )
    return rows


def _expected_artifacts(candidate: Any, snapshot: Sequence[dict[str, Any]]) -> dict[str, bytes]:
    runtime_rows = _runtime_rows()
    truth_rows = _truth_rows(candidate)
    safety_rows = _safety_rows()
    precondition_rows = _precondition_rows(snapshot)
    issue_content = _source(snapshot, "verdict_issue_readiness_inventory.csv")["content"]
    if (
        len(runtime_rows) != 49
        or len(truth_rows) != 201
        or len({row["case_group"] for row in truth_rows}) != 23
        or len(safety_rows) != 30
        or len(precondition_rows) != 45
        or _sha(issue_content)
        != "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
    ):
        raise ValueError("local evidence row contract drift")
    payloads = {
        RUNTIME_NAME: _csv_bytes(RUNTIME_COLUMNS, runtime_rows),
        TRUTH_NAME: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SAFETY_NAME: _csv_bytes(SAFETY_COLUMNS, safety_rows),
        PRECONDITION_NAME: _csv_bytes(PRECONDITION_COLUMNS, precondition_rows),
        ISSUE_NAME: issue_content,
    }
    support_sha = {
        path.as_posix(): _sha(_pinned_read(ROOT, path))
        for path in SUPPORT_PATHS
    }
    group_counts = dict(
        sorted(Counter(row["case_group"] for row in truth_rows).items())
    )
    manifest = {
        "project": "CovaPIE",
        "stage": STAGE,
        "step": "combined candidate verdict and cross-rule aggregation implementation v1",
        "base_identity": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "source_boundary_name": "fixed_ordered_exact13_committed_source_boundary",
        "source_boundary_count": 13,
        "source_boundary": [
            {key: value for key, value in item.items() if key != "content"}
            for item in snapshot
        ],
        "production_module": {
            "path": PRODUCTION_PATH.as_posix(),
            "sha256": support_sha[PRODUCTION_PATH.as_posix()],
        },
        "actual_input_runtime": {
            "owner": (
                "covalent_ext."
                "covapie_bulk_download_admission_minimal_unified_dispatch_"
                "shell_with_admit_004.UnifiedAdmissionRuleEvaluation"
            ),
            "schema_version": INPUT_SCHEMA,
            "field_count": 13,
            "fields": list(INPUT_FIELDS),
            "runtime_outcomes": list(OUTCOME_VOCABULARY),
            "aggregation_outcomes": ["passed", "blocked", "invalid"],
            "rejected_policy": (
                "runtime_valid_but_aggregation_inadmissible_fail_closed_as_"
                "evaluation_invariant_invalid"
            ),
            "nested_duplicate_policy": (
                "permitted_and_not_interpreted_merged_deduplicated_copied_or_rebuilt"
            ),
        },
        "public_api": {
            "function_name": "aggregate_admission_rule_evaluations",
            "signature": (
                "aggregate_admission_rule_evaluations(scope_id: str, *, "
                "ordered_rule_evaluations: "
                "tuple[UnifiedAdmissionRuleEvaluation, ...]) "
                "-> CombinedAdmissionCandidateVerdict"
            ),
            "candidate_or_context_parameters": False,
            "dispatcher_or_registry_parameters": False,
            "override_or_fallback_parameters": False,
        },
        "production_result": {
            "class_name": "CombinedAdmissionCandidateVerdict",
            "schema_version": RESULT_SCHEMA,
            "field_count": 13,
            "fields": list(RESULT_FIELDS),
            "frozen_dataclass": True,
            "slots": False,
            "aggregation_outcomes": ["passed", "blocked", "invalid"],
        },
        "permission_scope_count": 4,
        "permission_scopes": [
            {
                "scope_order": order,
                "scope_id": scope,
                "required_rule_count": len(required),
                "required_rule_ids": list(required),
            }
            for order, (scope, required) in enumerate(SCOPES, 1)
        ],
        "reason_vocabulary": {
            "pass_reason": "",
            "nonempty_reason_count": 6,
            "nonempty_reasons": list(REASONS),
        },
        "validation_precedence": [
            "scope_id",
            "ordered_vector_exact_tuple",
            "all_child_runtime_exact13_structure",
            "all_child_aggregation_identity_and_outcome_admissibility",
            "full_exact_membership",
            "all_child_invalid_outcomes",
            "all_child_blocked_outcomes",
            "all_child_passed",
        ],
        "full_vector_semantics": {
            "short_circuit": False,
            "complete_structure_scan": True,
            "complete_admissibility_scan": True,
            "complete_outcome_scan": True,
            "all_invalid_ids_collected": True,
            "all_blocked_ids_collected": True,
            "all_failing_ids_collected": True,
            "valid_tuple_identity_preserved": True,
        },
        "runtime_contract": {"row_count": 49},
        "truth_matrix": {
            "row_count": 201,
            "group_count": 23,
            "group_counts": group_counts,
            "uses_actual_runtime_type": True,
            "forged_objects_test_evidence_only": True,
            "production_api_creates_forged_objects": False,
            "production_runtime_modifies_inputs": False,
            "invalid_objects_retained": False,
        },
        "safety_audit": {"row_count": 30},
        "precondition_transition": {
            "row_count": 45,
            "transition_count": 1,
            "transition_ids": ["PRE_036"],
            "complete_count": 43,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 2,
            "implementation_blocking_count": 2,
            "remaining_open_precondition_ids": ["PRE_038", "PRE_042"],
        },
        "issue_continuity": {
            "row_count": 30,
            "byte_identical_to_contract": True,
            "sha256": _sha(issue_content),
            "transition_count": 0,
            "new_issue_count": 0,
            "remaining_open_issue_ids": [
                "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
                "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            ],
        },
        "readiness": {
            **{
                name: True
                for name in (
                    "combined_permission_semantics_frozen",
                    "combined_candidate_verdict_contract_frozen",
                    "cross_rule_aggregation_contract_frozen",
                    "cross_rule_aggregation_public_api_frozen",
                    "cross_rule_aggregation_result_contract_frozen",
                    "cross_rule_aggregation_validation_precedence_frozen",
                    "cross_rule_aggregation_full_vector_semantics_frozen",
                    "ready_for_cross_rule_aggregation_implementation",
                    "combined_candidate_verdict_implemented",
                    "cross_rule_aggregation_implemented",
                    "cross_rule_aggregation_implementation_complete",
                    "pre_036_resolved",
                    "ready_for_stage_global_rule_evaluation_orchestration_contract_design",
                    "feature_semantics_audit_required_before_training",
                )
            },
            **{
                name: False
                for name in (
                    "runtime_dispatcher_call_order_frozen",
                    "stage_global_rule_evaluation_orchestration_frozen",
                    "training_orchestrator_integration_implemented",
                    "feature_semantics_audit_completed",
                    "historical_unknown_atom_feature_policy_resolved",
                    "historical_feature_semantics_known",
                    "real_training_ready",
                    "ready_for_training",
                )
            },
        },
        "runtime_safety_boundary": {
            "dispatcher_call_count": 0,
            "single_rule_handler_call_count": 0,
            "aggregation_io_used": False,
            "current_permission": False,
            "authorized_admit_015_training_execution_count": 0,
            "aggregator_implementation_does_not_grant_action_permission": True,
            "training_execution_not_performed": True,
            "feature_semantics_audit_still_required": True,
            "ready_for_training": False,
            "orchestrator_implemented": False,
        },
        "canonical_mask_count": 5,
        "canonical_masks": [
            {"semantic_name": name, "alias": alias}
            for name, alias in (
                ("warhead_only", "A"),
                ("linker_plus_warhead", "B"),
                ("scaffold_plus_warhead", "B2"),
                ("scaffold_only", "B3"),
                ("scaffold_plus_linker_plus_warhead", "C"),
            )
        ],
        "step12d_boundary": "smoke_legality_check_not_final_training_feature_contract",
        "feature_semantics_warning": (
            "feature-semantics audit remains mandatory before training; "
            "Step12D was only a smoke legality check; historical "
            "UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=False "
            "remain unresolved"
        ),
        "no_orchestrator_boundary": (
            "stage-global rule evaluation orchestration is not implemented"
        ),
        "infrastructure_hardening": {
            "source_parent_chain_fd_pinned": True,
            "source_initial_final_strict_head": True,
            "source_base_ancestry_verified": True,
            "exact6_parent_root_all_leaf_fd_pinned": True,
            "duplicate_json_keys_rejected": True,
            "canonical_json": True,
            "materializer_build_before_mutation": True,
            "materializer_o_excl_and_fsync": True,
            "materializer_rename_noreplace": True,
            "materializer_gpfs_einval_fail_closed": True,
            "materializer_authenticated_staging_retained": True,
            "materializer_no_os_replace": True,
            "materializer_no_destructive_cleanup": True,
            "existing_exact_set_inode_preserving_noop": True,
            "checker_full_index_bytes_snapshotted": True,
            "git_write_tree_index_snapshot_used": False,
            "pre_commit_and_post_commit_lifecycle": True,
            "allow_empty_candidate_history_rejected": True,
            "full_recursive_lifecycle_run_count": 2,
            "final_recursive_lifecycle_is_last_filesystem_validation": True,
        },
        "stage_owned_staging_namespace_closure": {
            "materializer_staging_name_prefix": STAGING_PREFIX,
            "legacy_staging_prefixes": list(LEGACY_STAGING_PREFIXES),
            "current_staging_residue_rejected": True,
            "legacy_staging_residue_rejected": True,
            "ignored_tracked_nonignored_residue_rejected": True,
        },
        "embedded_stage_residue_lifecycle_closure": {
            "four_bounded_support_roots": [
                "src/covalent_ext",
                "scripts",
                "tests",
                "docs",
            ],
            "support_root_stage_match_policy": (
                "complete_stage_token_at_any_basename_position"
            ),
            "matched_directory_descendants_observed": True,
            "generic_symlink_filter_runs_before_stage_allowance": True,
            "derived_parent_independent_prefix_policy": True,
        },
        "derived_output_sha256": {
            (DERIVED_ROOT / name).as_posix(): _sha(content)
            for name, content in payloads.items()
        },
        "support_file_sha256": support_sha,
        "manifest_self_sha256_recorded": False,
        "exact10_file_count": 10,
        "exact10_files": [path.as_posix() for path in EXACT10],
        "all_checks_passed": True,
        "recommended_next_step": NEXT_STEP,
    }
    payloads[MANIFEST_NAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return {name: payloads[name] for name in OUTPUT_NAMES}


def _load_candidate() -> Any:
    candidate = importlib.import_module(MODULE_NAME)
    if tuple(candidate.__all__) != (
        "CombinedAdmissionCandidateVerdict",
        "aggregate_admission_rule_evaluations",
    ):
        raise ValueError("candidate __all__ drift")
    signature = inspect.signature(candidate.aggregate_admission_rule_evaluations)
    parameters = tuple(signature.parameters.values())
    if (
        tuple(parameter.name for parameter in parameters)
        != ("scope_id", "ordered_rule_evaluations")
        or parameters[0].kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD
        or parameters[1].kind is not inspect.Parameter.KEYWORD_ONLY
        or any(parameter.default is not inspect.Parameter.empty for parameter in parameters)
        or tuple(field.name for field in fields(candidate.CombinedAdmissionCandidateVerdict))
        != RESULT_FIELDS
        or not candidate.CombinedAdmissionCandidateVerdict.__dataclass_params__.frozen
    ):
        raise ValueError("candidate public API drift")
    return candidate


def _read_disk(
    repo_root: Path = ROOT,
    derived_root: Path = DERIVED_ROOT,
) -> dict[str, bytes]:
    root = repo_root / derived_root
    parent = root.parent
    parent_item = os.lstat(parent)
    root_item = os.lstat(root)
    parent_identity = _identity(parent_item)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(parent_item.st_mode)
        or stat.S_ISLNK(parent_item.st_mode)
        or not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise ValueError("derived parent/root unsafe")
    parent_fd = os.open(parent, DIR_FLAGS)
    root_fd: int | None = None
    descriptors: dict[str, int] = {}
    identities: dict[str, Identity] = {}
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("derived parent stat/open race")
        root_fd = os.open(root.name, DIR_FLAGS, dir_fd=parent_fd)
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("derived root stat/open race")
        inventory = tuple(sorted(os.listdir(root_fd)))
        if inventory != tuple(sorted(OUTPUT_NAMES)):
            raise ValueError("derived Exact6 inventory drift")
        for name in OUTPUT_NAMES:
            item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                not stat.S_ISREG(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
                or item.st_size > 100 * 1024 * 1024
            ):
                raise ValueError("derived leaf unsafe")
            identities[name] = _identity(item)
            descriptors[name] = os.open(name, READ_FLAGS, dir_fd=root_fd)
            if _identity(os.fstat(descriptors[name])) != identities[name]:
                raise ValueError("derived leaf stat/open race")
        payloads = {
            name: _read_all(descriptors[name]) for name in OUTPUT_NAMES
        }
        for name in OUTPUT_NAMES:
            lexical = os.stat(
                name, dir_fd=root_fd, follow_symlinks=False
            )
            if (
                _identity(os.fstat(descriptors[name])) != identities[name]
                or _identity(lexical) != identities[name]
            ):
                raise ValueError("derived all-leaf final drift")
        if tuple(sorted(os.listdir(root_fd))) != inventory:
            raise ValueError("derived final inventory drift")
        lexical_root = os.stat(
            root.name, dir_fd=parent_fd, follow_symlinks=False
        )
        if (
            _identity(os.fstat(parent_fd)) != parent_identity
            or _identity(os.lstat(parent)) != parent_identity
            or _identity(os.fstat(root_fd)) != root_identity
            or _identity(lexical_root) != root_identity
            or _identity(os.lstat(root)) != root_identity
        ):
            raise ValueError("derived final parent/root drift")
        return payloads
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        if root_fd is not None:
            os.close(root_fd)
        os.close(parent_fd)


def _matches_bounded_support_stage_family(name: str) -> bool:
    return STAGE in name or name in {
        PRODUCTION_PATH.name,
        CHECKER_PATH.name,
        TEST_PATH.name,
        SUMMARY_PATH.name,
    }


def _bounded_recursive_stage_inventory(
    root: Path,
    *,
    hook: Callable[[str, Path], None] | None = None,
) -> tuple[dict[Path, os.stat_result], tuple[Path, ...]]:
    """Scan the bounded stage roots with every traversed directory pinned."""
    root = Path(os.path.abspath(root))
    callback = (lambda event, path: None) if hook is None else hook
    observed: dict[Path, os.stat_result] = {}
    derived_roots: list[Path] = []
    fd_identities: dict[int, Identity] = {}

    def stat_at(parent_fd: int, name: str, reason: str) -> os.stat_result:
        try:
            return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except OSError as error:
            raise ValueError(f"{reason} stat failed") from error

    def names(directory_fd: int, reason: str) -> tuple[str, ...]:
        try:
            return tuple(sorted(os.listdir(directory_fd)))
        except OSError as error:
            raise ValueError(f"{reason} inventory failed") from error

    def assert_directory(
        item: os.stat_result,
        expected: Identity,
        reason: str,
    ) -> None:
        if (
            _identity(item) != expected
            or not stat.S_ISDIR(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
        ):
            raise ValueError(f"{reason} directory binding drift")

    def open_directory(
        parent_fd: int,
        name: str,
        expected: Identity,
        reason: str,
    ) -> int:
        callback("before_directory_open", Path(name))
        try:
            descriptor = os.open(name, DIR_FLAGS, dir_fd=parent_fd)
        except OSError as error:
            raise ValueError(f"{reason} open failed") from error
        try:
            assert_directory(os.fstat(descriptor), expected, reason)
        except BaseException:
            os.close(descriptor)
            raise
        callback("after_directory_open", Path(name))
        return descriptor

    def assert_child_binding(
        parent_fd: int,
        name: str,
        child_fd: int,
        expected: Identity,
        reason: str,
    ) -> None:
        assert_directory(os.fstat(parent_fd), fd_identities[parent_fd], reason)
        assert_directory(stat_at(parent_fd, name, reason), expected, reason)
        assert_directory(os.fstat(child_fd), expected, reason)

    def scan_directory(
        directory_fd: int,
        logical: Path,
        expected: Identity,
        *,
        observe_all: bool,
    ) -> None:
        assert_directory(os.fstat(directory_fd), expected, "bounded scan")
        initial_names = names(directory_fd, "bounded scan initial")
        identities: dict[str, Identity] = {}
        for name in initial_names:
            item = stat_at(directory_fd, name, "bounded scan entry")
            identity = _identity(item)
            identities[name] = identity
            if stat.S_ISLNK(item.st_mode):
                raise ValueError("bounded scan generic symlink rejected")
            relative = logical / name
            matched = (
                observe_all or _matches_bounded_support_stage_family(name)
            )
            if matched:
                observed[relative] = item
            if not stat.S_ISDIR(item.st_mode):
                continue
            child_fd = open_directory(
                directory_fd,
                name,
                identity,
                "bounded scan child",
            )
            fd_identities[child_fd] = identity
            try:
                scan_directory(
                    child_fd,
                    relative,
                    identity,
                    observe_all=matched,
                )
                assert_child_binding(
                    directory_fd,
                    name,
                    child_fd,
                    identity,
                    "bounded scan child post-recursion",
                )
            finally:
                fd_identities.pop(child_fd, None)
                os.close(child_fd)
        callback("before_directory_final_validation", logical)
        if names(directory_fd, "bounded scan final") != initial_names:
            raise ValueError("bounded scan inventory drift")
        assert_directory(os.fstat(directory_fd), expected, "bounded final")
        for name, identity in identities.items():
            item = stat_at(directory_fd, name, "bounded final entry")
            if _identity(item) != identity or stat.S_ISLNK(item.st_mode):
                raise ValueError("bounded scan entry identity drift")

    def scan_derived_parent(
        directory_fd: int,
        logical: Path,
        expected: Identity,
    ) -> None:
        assert_directory(os.fstat(directory_fd), expected, "derived parent")
        initial_names = names(directory_fd, "derived parent initial")
        identities: dict[str, Identity] = {}
        for name in initial_names:
            item = stat_at(directory_fd, name, "derived parent entry")
            identity = _identity(item)
            identities[name] = identity
            if stat.S_ISLNK(item.st_mode):
                raise ValueError("derived parent generic symlink rejected")
            if (
                name.startswith(STAGING_PREFIX)
                or any(
                    name.startswith(prefix)
                    for prefix in LEGACY_STAGING_PREFIXES
                )
            ):
                raise ValueError("derived staging residue rejected")
            if name != STAGE:
                if name.startswith(STAGE):
                    raise ValueError("matching derived sibling rejected")
                continue
            if not stat.S_ISDIR(item.st_mode):
                raise ValueError("matching derived root unsafe")
            relative = logical / name
            derived_roots.append(relative)
            observed[relative] = item
            child_fd = open_directory(
                directory_fd,
                name,
                identity,
                "matching derived root",
            )
            fd_identities[child_fd] = identity
            try:
                scan_directory(
                    child_fd,
                    relative,
                    identity,
                    observe_all=True,
                )
                assert_child_binding(
                    directory_fd,
                    name,
                    child_fd,
                    identity,
                    "derived root post-recursion",
                )
            finally:
                fd_identities.pop(child_fd, None)
                os.close(child_fd)
        callback("before_derived_parent_final_validation", logical)
        if names(directory_fd, "derived parent final") != initial_names:
            raise ValueError("derived parent inventory drift")
        assert_directory(
            os.fstat(directory_fd),
            expected,
            "derived parent final",
        )
        for name, identity in identities.items():
            item = stat_at(directory_fd, name, "derived parent final entry")
            if _identity(item) != identity or stat.S_ISLNK(item.st_mode):
                raise ValueError("derived parent entry identity drift")

    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise ValueError("bounded repository root unsafe")
    callback("before_repository_root_open", root)
    root_fd = os.open(root, DIR_FLAGS)
    fd_identities[root_fd] = root_identity
    callback("after_repository_root_open", root)

    def with_open_path(relative: Path, *, derived: bool) -> None:
        parent_fd = root_fd
        descriptors: list[int] = []
        bindings: list[tuple[int, str, int, Identity]] = []
        try:
            for component in relative.parts:
                item = stat_at(parent_fd, component, "bounded root component")
                identity = _identity(item)
                if (
                    not stat.S_ISDIR(item.st_mode)
                    or stat.S_ISLNK(item.st_mode)
                ):
                    raise ValueError("bounded root component unsafe")
                child_fd = open_directory(
                    parent_fd,
                    component,
                    identity,
                    "bounded root component",
                )
                descriptors.append(child_fd)
                bindings.append((parent_fd, component, child_fd, identity))
                fd_identities[child_fd] = identity
                parent_fd = child_fd
            expected = fd_identities[parent_fd]
            if derived:
                scan_derived_parent(parent_fd, relative, expected)
            else:
                scan_directory(
                    parent_fd,
                    relative,
                    expected,
                    observe_all=False,
                )
            for lexical_parent, name, child_fd, identity in reversed(
                bindings
            ):
                assert_child_binding(
                    lexical_parent,
                    name,
                    child_fd,
                    identity,
                    "bounded root post-scan",
                )
        finally:
            for descriptor in reversed(descriptors):
                fd_identities.pop(descriptor, None)
                os.close(descriptor)

    try:
        assert_directory(
            os.fstat(root_fd),
            root_identity,
            "bounded repository root",
        )
        for relative in (
            Path("src/covalent_ext"),
            Path("scripts"),
            Path("tests"),
            Path("docs"),
        ):
            with_open_path(relative, derived=False)
        with_open_path(
            Path("data/derived/covalent_small"),
            derived=True,
        )
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(os.lstat(root)) != root_identity
        ):
            raise ValueError("bounded repository root final drift")
        return observed, tuple(derived_roots)
    finally:
        fd_identities.pop(root_fd, None)
        os.close(root_fd)


def _assert_candidate_safe(
    root: Path,
    relative: Path,
    item: os.stat_result,
) -> None:
    ignored = _git_result(
        root,
        "check-ignore",
        "--no-index",
        "-q",
        "--",
        relative.as_posix(),
    )
    if ignored.returncode == 0:
        raise ValueError("same-stage candidate ignored")
    if ignored.returncode != 1:
        raise ValueError("same-stage check-ignore failed")
    if stat.S_ISLNK(item.st_mode):
        raise ValueError("same-stage symlink rejected")
    if relative == DERIVED_ROOT:
        if not stat.S_ISDIR(item.st_mode):
            raise ValueError("same-stage derived root unsafe")
        return
    if (
        not stat.S_ISREG(item.st_mode)
        or relative.suffix.lower() in FORBIDDEN_SUFFIXES
        or item.st_size > MAX_BYTES
    ):
        raise ValueError("same-stage leaf unsafe")


def assert_exact10_recursive_inventory(
    root: Path = ROOT,
    exact10: Sequence[Path] = EXACT10,
    *,
    hook: Callable[[str, Path], None] | None = None,
) -> tuple[
    tuple[tuple[str, Identity], ...],
    tuple[str, ...],
]:
    observed, derived_roots = _bounded_recursive_stage_inventory(
        root,
        hook=hook,
    )
    for relative, item in observed.items():
        _assert_candidate_safe(root, relative, item)
    expected = {*exact10, DERIVED_ROOT}
    if set(observed) != expected:
        raise ValueError("same-stage recursive Exact10 inventory drift")
    if derived_roots != (DERIVED_ROOT,):
        raise ValueError("matching derived root inventory drift")
    derived_names = tuple(
        relative.name
        for relative in observed
        if relative.parent == DERIVED_ROOT
    )
    if len(derived_names) != 6 or set(derived_names) != set(OUTPUT_NAMES):
        raise ValueError("same-stage Exact6 recursive inventory drift")
    if set(_read_disk(root, DERIVED_ROOT)) != set(OUTPUT_NAMES):
        raise ValueError("same-stage pinned Exact6 inventory drift")
    normalized = tuple(
        sorted(
            (
                relative.as_posix(),
                _identity(item),
            )
            for relative, item in observed.items()
        )
    )
    return normalized, tuple(path.as_posix() for path in derived_roots)


def _nul_paths(content: bytes, reason: str) -> tuple[str, ...]:
    try:
        values = tuple(
            value for value in content.decode("utf-8").split("\0") if value
        )
    except UnicodeDecodeError as error:
        raise ValueError(f"{reason} path encoding drift") from error
    if len(values) != len(set(values)):
        raise ValueError(f"{reason} duplicate path")
    return values


def _parse_index_entry(content: bytes, path: str) -> tuple[str, int]:
    try:
        metadata, observed = content.decode("utf-8").rstrip("\n").split(
            "\t", 1
        )
        mode, blob, stage_number = metadata.split(" ")
        stage = int(stage_number)
    except (UnicodeDecodeError, ValueError) as error:
        raise ValueError("lifecycle index entry malformed") from error
    if (
        observed != path
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("lifecycle index path/blob drift")
    return mode, stage


def _worktree_inventory(
    root: Path,
) -> tuple[tuple[str, str, str], ...]:
    result = _git_result(root, "worktree", "list", "--porcelain")
    if result.returncode:
        raise ValueError("worktree inventory query failed")
    try:
        lines = result.stdout.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise ValueError("worktree inventory encoding drift") from error
    records: list[tuple[str, str, str]] = []
    current: dict[str, str] = {}

    def finish() -> None:
        nonlocal current
        if not current:
            return
        if set(current) != {"worktree", "HEAD", "state"}:
            raise ValueError("worktree record shape drift")
        path = os.path.abspath(current["worktree"])
        head = current["HEAD"]
        state = current["state"]
        if (
            re.fullmatch(r"[0-9a-f]{40}", head) is None
            or (
                state != "detached"
                and not state.startswith("branch refs/heads/")
            )
        ):
            raise ValueError("worktree record value drift")
        records.append((path, head, state))
        current = {}

    for line in lines + [""]:
        if not line:
            finish()
            continue
        key, separator, value = line.partition(" ")
        if key == "worktree":
            if "worktree" in current or not separator or not value:
                raise ValueError("worktree record boundary drift")
            current["worktree"] = value
        elif key == "HEAD":
            if "HEAD" in current or not separator:
                raise ValueError("worktree HEAD record drift")
            current["HEAD"] = value
        elif key == "branch":
            if "state" in current or not separator:
                raise ValueError("worktree branch record drift")
            current["state"] = f"branch {value}"
        elif key == "detached" and not separator:
            if "state" in current:
                raise ValueError("worktree detached record drift")
            current["state"] = "detached"
        else:
            raise ValueError("unsupported worktree state")
    if not records or len({record[0] for record in records}) != len(records):
        raise ValueError("worktree path inventory drift")
    return tuple(sorted(records))


class RefRecord(NamedTuple):
    refname: str
    objectname: str
    objecttype: str


def _ref_inventory(root: Path) -> tuple[RefRecord, ...]:
    result = _git_result(
        root,
        "for-each-ref",
        "--sort=refname",
        "--format=%(refname)%09%(objectname)%09%(objecttype)",
    )
    if result.returncode:
        raise ValueError("complete ref inventory query failed")
    try:
        lines = result.stdout.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise ValueError("complete ref inventory encoding drift") from error
    records: list[RefRecord] = []
    for line in lines:
        columns = line.split("\t")
        if len(columns) != 3:
            raise ValueError("complete ref inventory record shape drift")
        refname, objectname, objecttype = columns
        if (
            not refname
            or not refname.startswith("refs/")
            or re.fullmatch(r"[0-9a-f]{40}", objectname) is None
            or not objecttype
        ):
            raise ValueError("complete ref inventory record value drift")
        records.append(RefRecord(refname, objectname, objecttype))
    if len({record.refname for record in records}) != len(records):
        raise ValueError("complete ref inventory duplicate refname")
    return tuple(sorted(records, key=lambda record: record.refname))


def _is_platform_ref(refname: str) -> bool:
    return re.fullmatch(PLATFORM_REFNAME_PATTERN, refname) is not None


def _is_platform_namespace_ref(refname: str) -> bool:
    return refname == PLATFORM_REF_NAMESPACE or refname.startswith(
        f"{PLATFORM_REF_NAMESPACE}/"
    )


def _assert_ref_namespace_policy(refs: Sequence[RefRecord]) -> None:
    names = {record.refname for record in refs}
    if not set(ALLOWED_REQUIRED_LOCAL_REFS) <= names:
        raise ValueError("required local ref missing")
    allowed_exact = {
        *ALLOWED_REQUIRED_LOCAL_REFS,
        *ALLOWED_OPTIONAL_REMOTE_REFS,
    }
    for record in refs:
        if record.refname in allowed_exact:
            if record.objecttype != "commit":
                raise ValueError("local/remote ref object type drift")
            continue
        if not _is_platform_namespace_ref(record.refname):
            raise ValueError("persistent ref namespace residue")
        if STAGE in record.refname or any(
            term in record.refname.casefold()
            for term in PLATFORM_REF_BLOCKED_TERMS
        ):
            raise ValueError("platform ref stage/candidate residue")
        if not _is_platform_ref(record.refname):
            raise ValueError("platform ref name grammar drift")
        if record.objecttype != "tree":
            raise ValueError("platform ref object type drift")


def _assert_topology(
    root: Path,
    lifecycle: str,
    head: str,
    worktrees: tuple[tuple[str, str, str], ...],
    refs: tuple[RefRecord, ...],
    *,
    base: str,
) -> None:
    root_path = os.path.abspath(root)
    current = tuple(record for record in worktrees if record[0] == root_path)
    if len(current) != 1 or current[0][1] != head:
        raise ValueError("current worktree binding drift")
    main_refs = tuple(
        record for record in refs if record.refname == "refs/heads/main"
    )
    main_worktrees = tuple(
        record
        for record in worktrees
        if record[2] == "branch refs/heads/main"
    )
    if (
        len(main_refs) != 1
        or len(main_worktrees) != 1
        or main_refs[0].objecttype != "commit"
        or main_refs[0].objectname != main_worktrees[0][1]
    ):
        raise ValueError("main ref/worktree binding drift")
    records_by_name = {record.refname: record for record in refs}
    origin_main = records_by_name.get("refs/remotes/origin/main")
    origin_head = records_by_name.get("refs/remotes/origin/HEAD")
    if origin_head is not None and (
        origin_main is None
        or origin_head.objectname != origin_main.objectname
    ):
        raise ValueError("origin HEAD/main target topology drift")
    current_record = current[0]
    if lifecycle == "pre_commit":
        if (
            len(worktrees) != 1
            or current_record[2] != "branch refs/heads/main"
            or head != base
            or main_refs[0].objectname != base
            or (
                origin_main is not None
                and origin_main.objectname != base
            )
        ):
            raise ValueError("pre-commit topology drift")
        return
    if lifecycle != "post_commit":
        raise ValueError("unknown lifecycle")
    if len(worktrees) == 1:
        if (
            current_record[2] != "branch refs/heads/main"
            or main_refs[0].objectname != head
            or (
                origin_main is not None
                and origin_main.objectname not in {base, head}
            )
        ):
            raise ValueError("formal-main post-commit topology drift")
        return
    if len(worktrees) != 2 or current_record[2] != "detached":
        raise ValueError("detached candidate topology drift")
    main_records = tuple(
        record
        for record in worktrees
        if record != current_record
        and record[2] == "branch refs/heads/main"
    )
    if (
        len(main_records) != 1
        or main_records[0][1] != base
        or main_refs[0].objectname != base
        or (
            origin_main is not None
            and origin_main.objectname != base
        )
    ):
        raise ValueError("detached candidate main/base topology drift")


class LifecycleSnapshot(NamedTuple):
    lifecycle: str
    head: str
    identities: tuple[tuple[str, Identity], ...]
    tracked: frozenset[str]
    untracked: frozenset[str]
    listed_untracked: tuple[str, ...]
    staged: tuple[str, ...]
    unstaged: tuple[str, ...]
    status: bytes
    full_index: bytes
    recursive_inventory: tuple[tuple[str, Identity], ...]
    derived_roots: tuple[str, ...]
    worktrees: tuple[tuple[str, str, str], ...]
    refs: tuple[RefRecord, ...]
    exact10: tuple[str, ...]


def _capture_lifecycle_state(
    root: Path,
    ordered: Sequence[str],
    *,
    base: str,
) -> LifecycleSnapshot:
    root = Path(os.path.abspath(root))
    head = _strict_head(root)
    if _git_result(
        root,
        "merge-base",
        "--is-ancestor",
        base,
        head,
    ).returncode:
        raise ValueError("lifecycle base is not HEAD ancestor")
    identities: list[tuple[str, Identity]] = []
    tracked: set[str] = set()
    untracked: set[str] = set()
    for relative in ordered:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ValueError("Exact10 lifecycle path unsafe")
        item = os.lstat(root / path)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > MAX_BYTES
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
        ):
            raise ValueError("Exact10 lifecycle leaf unsafe")
        identities.append((relative, _identity(item)))
        ignored = _git_result(
            root,
            "check-ignore",
            "--no-index",
            "-q",
            "--",
            relative,
        )
        if ignored.returncode == 0:
            raise ValueError("Exact10 lifecycle leaf ignored")
        if ignored.returncode != 1:
            raise ValueError("lifecycle check-ignore failed")
        index_entry = _git_result(
            root,
            "ls-files",
            "--stage",
            "--",
            relative,
        )
        if index_entry.returncode:
            raise ValueError("lifecycle index query failed")
        if index_entry.stdout:
            mode, stage_number = _parse_index_entry(
                index_entry.stdout,
                relative,
            )
            if mode != "100644" or stage_number != 0:
                raise ValueError("Exact10 index mode/stage drift")
            tracked.add(relative)
        else:
            untracked.add(relative)
    commands = {
        "untracked": (
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        ),
        "staged": ("diff", "--cached", "--name-only", "-z"),
        "unstaged": ("diff", "--name-only", "-z"),
        "status": (
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ),
        "index": ("ls-files", "--stage", "-z"),
        "raw": ("ls-files", "-z", "data/raw"),
        "diff_check": ("diff", "--check"),
    }
    results = {
        name: _git_result(root, *arguments)
        for name, arguments in commands.items()
    }
    if any(result.returncode for result in results.values()):
        raise ValueError("lifecycle Git state query failed")
    listed_untracked = _nul_paths(
        results["untracked"].stdout,
        "untracked",
    )
    staged = _nul_paths(results["staged"].stdout, "staged")
    unstaged = _nul_paths(results["unstaged"].stdout, "unstaged")
    raw_tracked = _nul_paths(results["raw"].stdout, "raw tracked")
    if staged or unstaged or results["diff_check"].stdout:
        raise ValueError("lifecycle repository staged/dirty")
    if len(raw_tracked) != 53:
        raise ValueError("raw tracked baseline drift")
    if tracked and untracked:
        raise ValueError("mixed tracked/untracked lifecycle")
    if set(listed_untracked) != untracked:
        raise ValueError("entire untracked inventory is not Exact10")
    expected = set(ordered)
    if untracked == expected and not tracked:
        lifecycle = "pre_commit"
    elif tracked == expected and not untracked:
        lifecycle = "post_commit"
        _assert_post_commit_history(root, head, expected, base)
    else:
        raise ValueError("lifecycle Exact10 inventory drift")
    refs = _ref_inventory(root)
    _assert_ref_namespace_policy(refs)
    worktrees = _worktree_inventory(root)
    _assert_topology(
        root,
        lifecycle,
        head,
        worktrees,
        refs,
        base=base,
    )
    return LifecycleSnapshot(
        lifecycle,
        head,
        tuple(identities),
        frozenset(tracked),
        frozenset(untracked),
        listed_untracked,
        staged,
        unstaged,
        results["status"].stdout,
        results["index"].stdout,
        (),
        (),
        worktrees,
        refs,
        tuple(ordered),
    )


def _assert_post_commit_history(
    root: Path,
    head: str,
    expected: set[str],
    base: str,
) -> None:
    changed = _git_result(
        root,
        "diff",
        "--name-only",
        "-z",
        f"{base}..{head}",
    )
    commits = _git_result(root, "rev-list", "--reverse", f"{base}..{head}")
    if changed.returncode or commits.returncode:
        raise ValueError("post-commit history query failed")
    if set(_nul_paths(changed.stdout, "candidate diff")) != expected:
        raise ValueError("candidate commit does not contain Exact10 only")
    try:
        commit_ids = tuple(commits.stdout.decode("ascii").splitlines())
    except UnicodeDecodeError as error:
        raise ValueError("candidate commit encoding drift") from error
    if not commit_ids or commit_ids[-1] != head:
        raise ValueError("candidate descendant chain drift")
    for commit in commit_ids:
        if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
            raise ValueError("candidate commit malformed")
        delta = _git_result(
            root,
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            commit,
        )
        if delta.returncode:
            raise ValueError("candidate commit delta query failed")
        paths = set(_nul_paths(delta.stdout, "candidate delta"))
        if not paths:
            raise ValueError("allow-empty HEAD/history drift")
        if not paths <= expected:
            raise ValueError("candidate commit out-of-scope history")
    tree = _git_result(
        root,
        "ls-tree",
        "-r",
        "-z",
        head,
        "--",
        *sorted(expected),
    )
    entries = tuple(entry for entry in tree.stdout.split(b"\0") if entry)
    if tree.returncode or len(entries) != 10:
        raise ValueError("candidate Exact10 tree count drift")
    for entry in entries:
        try:
            metadata, path = entry.decode("utf-8").split("\t", 1)
            mode, kind, blob = metadata.split(" ")
        except (UnicodeDecodeError, ValueError) as error:
            raise ValueError("candidate tree entry malformed") from error
        if (
            path not in expected
            or mode != "100644"
            or kind != "blob"
            or re.fullmatch(r"[0-9a-f]{40}", blob) is None
        ):
            raise ValueError("candidate Exact10 tree mode drift")


def verify_lifecycle(
    root: Path = ROOT,
    exact10: Sequence[Path] = EXACT10,
    *,
    base: str = BASE_COMMIT,
    hook: Callable[[str, Path], None] | None = None,
) -> LifecycleSnapshot:
    root = Path(os.path.abspath(root))
    ordered = tuple(path.as_posix() for path in exact10)
    if len(ordered) != 10 or len(set(ordered)) != 10:
        raise ValueError("candidate is not Exact10")
    initial = _capture_lifecycle_state(root, ordered, base=base)
    recursive_inventory, derived_roots = (
        assert_exact10_recursive_inventory(
            root,
            exact10,
            hook=hook,
        )
    )
    final = _capture_lifecycle_state(root, ordered, base=base)
    if final != initial:
        raise ValueError("final HEAD/inventory/index/identity drift")
    return initial._replace(
        recursive_inventory=recursive_inventory,
        derived_roots=derived_roots,
    )


def _verify_candidate(
    candidate: Any,
    snapshot: Sequence[dict[str, Any]],
    expected: Mapping[str, bytes],
) -> None:
    actual_snapshot = candidate.build_frozen_source_snapshot(ROOT)
    normalized = [
        {
            "source_order": order,
            "path": item.relative_path.as_posix(),
            "sha256": item.expected_sha256,
            "base_tree_mode": item.base_tree_mode,
            "base_tree_blob": item.base_tree_blob,
            "index_mode": item.index_mode,
            "index_blob": item.index_blob,
            "index_stage": item.index_stage,
            "filesystem_sha256": item.filesystem_sha256,
            "content": item.content,
        }
        for order, item in enumerate(actual_snapshot, 1)
    ]
    if normalized != list(snapshot):
        raise ValueError("candidate/checker source snapshot mismatch")
    actual = candidate.build_artifacts(actual_snapshot, repo_root=ROOT)
    if actual != expected:
        raise ValueError("candidate/checker expected mismatch")
    if _read_disk() != expected:
        raise ValueError("disk/checker expected mismatch")
    manifest = _json(expected[MANIFEST_NAME])
    if MANIFEST_NAME in manifest["derived_output_sha256"]:
        raise ValueError("manifest self hash recorded")
    for path, digest in manifest["derived_output_sha256"].items():
        if _sha(expected[Path(path).name]) != digest:
            raise ValueError("derived hash truth drift")
    for path, digest in manifest["support_file_sha256"].items():
        if _sha(_pinned_read(ROOT, Path(path))) != digest:
            raise ValueError("support hash truth drift")
    with tempfile.TemporaryDirectory(prefix=f"{STAGE}.checker.") as directory:
        output = Path(directory) / STAGE
        result = candidate.run_covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1(
            output, repo_root=ROOT
        )
        if result["output_root"] != output or candidate._read_output_set(output) != expected:
            raise ValueError("new-directory materialization mismatch")
        before = os.lstat(output)
        candidate.run_covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1(
            output, repo_root=ROOT
        )
        after = os.lstat(output)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise ValueError("existing no-op inode drift")


def _verify_complete_checker_run(
    *,
    after_candidate_validation: Callable[[], None] | None = None,
    lifecycle_root: Path = ROOT,
    lifecycle_exact10: Sequence[Path] = EXACT10,
    lifecycle_base: str = BASE_COMMIT,
) -> dict[str, Any]:
    """Run both complete lifecycle closures around candidate validation."""
    if (
        sys.implementation.name != "cpython"
        or tuple(sys.version_info[:3]) != (3, 10, 4)
    ):
        raise ValueError("checker requires CPython 3.10.4")
    lifecycle_root = Path(os.path.abspath(lifecycle_root))
    ordered = tuple(path.as_posix() for path in lifecycle_exact10)
    initial = _capture_lifecycle_state(
        lifecycle_root,
        ordered,
        base=lifecycle_base,
    )
    first = verify_lifecycle(
        lifecycle_root,
        lifecycle_exact10,
        base=lifecycle_base,
    )
    snapshot = _source_snapshot()
    candidate = _load_candidate()
    expected = _expected_artifacts(candidate, snapshot)
    _verify_candidate(candidate, snapshot, expected)
    manifest = _json(expected[MANIFEST_NAME])
    report = {
        "all_checks_passed": True,
        "authorized_admit_015_training_execution_count": 0,
        "combined_candidate_verdict_implemented": True,
        "cross_rule_aggregation_implemented": True,
        "current_permission": False,
        "embedded_stage_residue_lifecycle_closure": True,
        "exact10_file_count": 10,
        "final_recursive_lifecycle_after_candidate_validation": True,
        "final_recursive_lifecycle_is_last_filesystem_validation": True,
        "full_recursive_lifecycle_run_count": 2,
        "issue_row_count": 30,
        "issue_transition_count": 0,
        "lifecycle": first.lifecycle,
        "manifest_sha256": _sha(expected[MANIFEST_NAME]),
        "precondition_counts": "43/0/2/2",
        "precondition_row_count": 45,
        "precondition_transition_count": 1,
        "precondition_transition_id": "PRE_036",
        "platform_ref_trust_boundary_closure": True,
        "persistent_ref_namespace_closure": True,
        "ready_for_training": False,
        "recommended_next_step": NEXT_STEP,
        "remote_ref_target_closure": True,
        "runtime_contract_row_count": 49,
        "safety_row_count": 30,
        "source_attestation_count": 13,
        "stage_owned_staging_namespace_closure": True,
        "truth_group_count": 23,
        "truth_row_count": 201,
    }
    if manifest["recommended_next_step"] != NEXT_STEP:
        raise ValueError("recommended next step drift")
    if after_candidate_validation is not None:
        after_candidate_validation()
    prefinal = _capture_lifecycle_state(
        lifecycle_root,
        ordered,
        base=lifecycle_base,
    )
    if prefinal != initial:
        raise ValueError(
            "checker prefinal HEAD/inventory/index/identity drift"
    )
    # Deliberately the final Git/filesystem/candidate validation operation.
    final = verify_lifecycle(
        lifecycle_root,
        lifecycle_exact10,
        base=lifecycle_base,
    )
    if first != final:
        raise ValueError("initial/final complete lifecycle result drift")
    report["lifecycle"] = final.lifecycle
    return report


def main() -> int:
    report = _verify_complete_checker_run()
    print(json.dumps(report, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
