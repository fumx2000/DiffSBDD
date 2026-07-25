"""Design-only combined-candidate verdict and aggregation contract.

The pure in-memory oracle in this module consumes mirror Exact13 child
results.  It is not the future production aggregator, its child mirror is not
the Exact15 runtime class, and its result mirror is not the future production
result class.  No dispatcher, handler, provider, download, raw-data, model,
checkpoint, dataloader, or training path is imported or executed.
"""

from __future__ import annotations

import csv
import ctypes
import hashlib
import io
import json
import os
import re
import secrets
import stat
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "combined candidate verdict and cross-rule aggregation contract v1"
STAGE = (
    "covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_contract_v1"
)
BASE_COMMIT = "71fe2a41ecdf9e2317994e755ce21fc64bd05b87"
BASE_PARENT = "bb282ef24343baebc05212715a8c7d56bc8224ad"
BASE_TREE = "a50b5a13fc9b476e20fad80b15fa408b8e0a0eae"
BASE_SUBJECT = "add CovaPIE combined permission semantics contract v1"
CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = (3, 10, 4)
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_combined_candidate_verdict_and_cross_rule_"
    "aggregation_v1"
)
REVISED2_REVISION = (
    "revise_covapie_combined_candidate_verdict_and_cross_rule_aggregation_contract_"
    "final_lifecycle_closure_v2"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
STAGING_NAME_PREFIX = f"{STAGE}.__staging__."

RUNTIME_OUTCOME_VOCABULARY = (
    "passed",
    "blocked",
    "invalid",
    "rejected",
)
AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES = (
    "passed",
    "blocked",
    "invalid",
)
FAIL_CLOSED_PRECEDENCE = ("invalid", "blocked", "passed")
PASS_REASON = ""
REASON_VOCABULARY = (
    "COMBINED_ADMISSION_SCOPE_ID_INVALID",
    "COMBINED_ADMISSION_RULE_EVALUATION_VECTOR_TYPE_INVALID",
    "COMBINED_ADMISSION_RULE_EVALUATION_INVARIANT_INVALID",
    "COMBINED_ADMISSION_RULE_MEMBERSHIP_INVALID",
    "COMBINED_ADMISSION_REQUIRED_RULE_INVALID",
    "COMBINED_ADMISSION_REQUIRED_RULE_BLOCKED",
)
SCOPE_ID_INVALID_REASON = REASON_VOCABULARY[0]
VECTOR_TYPE_INVALID_REASON = REASON_VOCABULARY[1]
EVALUATION_INVARIANT_INVALID_REASON = REASON_VOCABULARY[2]
MEMBERSHIP_INVALID_REASON = REASON_VOCABULARY[3]
REQUIRED_RULE_INVALID_REASON = REASON_VOCABULARY[4]
REQUIRED_RULE_BLOCKED_REASON = REASON_VOCABULARY[5]
CURRENT_PERMISSION = False
AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT = 0
DISPATCHER_CALL_COUNT = 0
SINGLE_RULE_HANDLER_CALL_COUNT = 0
AGGREGATION_IO_USED = False
INPUT_RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
FUTURE_RESULT_SCHEMA_VERSION = (
    "covapie_combined_admission_candidate_verdict_v1"
)
FUTURE_FUNCTION_NAME = "aggregate_admission_rule_evaluations"
FUTURE_API_SIGNATURE = (
    "aggregate_admission_rule_evaluations(scope_id: str, *, "
    "ordered_rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...]) "
    "-> CombinedAdmissionCandidateVerdict"
)
INPUT_RESULT_FIELDS = (
    "schema_version",
    "admission_rule_id",
    "admission_rule_name",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "normalized_values",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
    "adapter_id",
)
FUTURE_RESULT_FIELDS = (
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

RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
RULE_NAMES = {
    "ADMIT_001": "unique_candidate_identity",
    "ADMIT_002": "valid_pdb_id_format",
    "ADMIT_003": "ligand_or_het_identity_present",
    "ADMIT_004": "covalent_residue_identity_present",
    "ADMIT_005": "cys_sg_scope_only_v1",
    "ADMIT_006": "explicit_covalent_event_evidence",
    "ADMIT_007": "distance_only_inference_forbidden",
    "ADMIT_008": "topology_restoration_disposition",
    "ADMIT_009": "duplicate_identity_precheck",
    "ADMIT_010": "leakage_group_assignment_before_split",
    "ADMIT_011": "raw_overwrite_forbidden",
    "ADMIT_012": "future_download_integrity_fields_required",
    "ADMIT_013": "download_failure_fail_closed",
    "ADMIT_014": "current_gate_grants_no_download_permission",
    "ADMIT_015": "current_gate_grants_no_training_permission",
}
ADAPTER_IDS = {
    rule_id: f"covapie_admit_{index:03d}_unified_adapter_v1"
    for index, rule_id in enumerate(RULE_IDS, 1)
}
RULE_PHASES = (
    ("ADMIT_001", "pre_download"),
    ("ADMIT_002", "pre_download"),
    ("ADMIT_003", "pre_download"),
    ("ADMIT_004", "pre_download"),
    ("ADMIT_005", "pre_download"),
    ("ADMIT_006", "pre_download"),
    ("ADMIT_007", "pre_download"),
    ("ADMIT_008", "pre_download"),
    ("ADMIT_009", "pre_download"),
    ("ADMIT_010", "pre_final_split"),
    ("ADMIT_011", "pre_download"),
    ("ADMIT_012", "post_download"),
    ("ADMIT_013", "post_download"),
    ("ADMIT_014", "current_step"),
    ("ADMIT_015", "current_step"),
)
RULE_PHASE_BY_ID = dict(RULE_PHASES)

SCOPE_CONTRACT = (
    (
        "download_execution_permission",
        "download execution permission",
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
        "post-download acceptance permission",
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
        "pre-final-split acceptance permission",
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
    (
        "training_execution_admission_permission",
        "training execution admission permission",
        RULE_IDS,
    ),
)
SCOPE_IDS = tuple(item[0] for item in SCOPE_CONTRACT)
SCOPE_NAMES = {item[0]: item[1] for item in SCOPE_CONTRACT}
REQUIRED_RULE_IDS = {item[0]: item[2] for item in SCOPE_CONTRACT}

CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)

PUBLIC_API_FILENAME = "covapie_combined_candidate_verdict_public_api_contract.csv"
RESULT_FILENAME = "covapie_cross_rule_aggregation_result_contract.csv"
TRUTH_FILENAME = "covapie_cross_rule_aggregation_truth_matrix.csv"
SAFETY_FILENAME = "covapie_cross_rule_aggregation_safety_audit.csv"
ISSUE_FILENAME = "covapie_combined_candidate_verdict_issue_readiness_inventory.csv"
MANIFEST_FILENAME = (
    "covapie_combined_candidate_verdict_and_cross_rule_aggregation_contract_manifest.json"
)
OUTPUT_FILES = (
    PUBLIC_API_FILENAME,
    RESULT_FILENAME,
    TRUTH_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
    MANIFEST_FILENAME,
)

PUBLIC_API_COLUMNS = (
    "contract_order",
    "contract_item",
    "frozen_value",
    "design_boundary",
    "contract_passed",
)
RESULT_COLUMNS = (
    "contract_order",
    "contract_group",
    "field_order",
    "field_name",
    "exact_top_level_type",
    "nested_type",
    "fixed_or_conditional_invariant",
    "pass_projection",
    "blocked_projection",
    "invalid_projection",
    "identity_behavior",
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

SOURCE_BOUNDARY = (
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_combined_permission_semantics_"
        "contract_design_gate.py",
        "823250a84d637625abd20c11244614eb86492b010b75becbe03ce6b83fe0c328",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_permission_semantics_"
        "contract_v1/covapie_combined_permission_semantics_contract_manifest.json",
        "ffc919f2f1ac0c9248ebdb86c61a18ad713d15cfefb12d181f981271bb275fb1",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_permission_semantics_"
        "contract_v1/covapie_combined_permission_scope_and_rule_membership_"
        "contract.csv",
        "3e74d0ac1d7be7bd23cf6d243c9593e01099a6dd55ed5079d27b01c12cb71b55",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_permission_semantics_"
        "contract_v1/covapie_combined_permission_precedence_and_non_override_"
        "contract.csv",
        "0cf2c6fd4adf6b8e9f4ca87bcdb033024de9e54c15594f8d7282b4bde5da265e",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_permission_semantics_"
        "contract_v1/covapie_combined_permission_truth_matrix.csv",
        "9c9f8aa30cf1882ffbccfcf721f298030ab479636641d79e9755019c55065d5e",
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
        "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/"
        "covapie_bulk_download_admission_rule_registry.csv",
        "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
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
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_permission_semantics_"
        "contract_v1/covapie_combined_permission_issue_readiness_inventory.csv",
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7",
    ),
)
SOURCE_PATHS = tuple(Path(path) for path, _ in SOURCE_BOUNDARY)
SOURCE_SHA256 = {Path(path): digest for path, digest in SOURCE_BOUNDARY}

SUPPORT_PATHS = (
    Path(
        "src/covalent_ext/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_"
        "contract_design_gate.py"
    ),
    Path(
        "scripts/"
        "check_covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_contract_v1.py"
    ),
    Path(
        "docs/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_"
        "contract_v1_summary.md"
    ),
)


@dataclass(frozen=True)
class FrozenSource:
    """One fully pinned source-boundary record."""

    relative_path: Path
    expected_sha256: str
    base_tree_mode: str
    base_tree_blob: str
    index_mode: str
    index_blob: str
    index_stage: int
    filesystem_sha256: str
    content: bytes


@dataclass(frozen=True)
class UnifiedAdmissionRuleEvaluationContractDesign:
    """Exact13 mirror only; deliberately not the Exact15 runtime class."""

    schema_version: str
    admission_rule_id: str
    admission_rule_name: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    normalized_values: tuple[tuple[str, str], ...]
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    consumed_context_items: tuple[str, ...]
    evaluator_io_used: bool
    adapter_id: str


@dataclass(frozen=True)
class CombinedAdmissionCandidateVerdictContractDesign:
    """Future Exact13 result mirror only; not the production result class."""

    schema_version: str
    scope_id: str
    outcome: str
    passed: bool
    blocks_scope_action: bool
    reason: str
    required_rule_ids: tuple[str, ...]
    evaluated_rule_ids: tuple[str, ...]
    rule_evaluations: tuple[UnifiedAdmissionRuleEvaluationContractDesign, ...]
    invalid_rule_ids: tuple[str, ...]
    blocked_rule_ids: tuple[str, ...]
    failing_rule_ids: tuple[str, ...]
    aggregation_io_used: bool


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical_runtime_guard() -> None:
    if (
        sys.implementation.name != CANONICAL_PYTHON_IMPLEMENTATION
        or tuple(sys.version_info[:3]) != CANONICAL_PYTHON_VERSION
    ):
        raise ValueError("canonical evidence runtime requires CPython 3.10.4")


def _git(root: Path, *arguments: str) -> bytes:
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


def _parse_index(content: bytes, path: str) -> tuple[str, str, int]:
    try:
        metadata, observed = content.decode().rstrip("\n").split("\t", 1)
        mode, blob, stage = metadata.split(" ")
        number = int(stage)
    except ValueError as error:
        raise ValueError("index entry malformed") from error
    if (
        observed != path
        or mode != "100644"
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("index entry drift")
    return mode, blob, number


def _parse_tree(content: bytes, path: str) -> tuple[str, str]:
    try:
        metadata, observed = content.decode().rstrip("\n").split("\t", 1)
        mode, kind, blob = metadata.split(" ")
    except ValueError as error:
        raise ValueError("tree entry malformed") from error
    if (
        observed != path
        or mode != "100644"
        or kind != "blob"
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("tree entry drift")
    return mode, blob


DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
WRITE_FLAGS = (
    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
)
MAX_FILE_BYTES = 100 * 1024 * 1024
RENAME_NOREPLACE = 1
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


def _read_all(descriptor: int, maximum: int = MAX_FILE_BYTES) -> bytes:
    chunks = []
    total = 0
    while True:
        chunk = os.read(descriptor, 1 << 16)
        if not chunk:
            break
        total += len(chunk)
        if total > maximum:
            raise ValueError("pinned read exceeds maximum")
        chunks.append(chunk)
    return b"".join(chunks)


def _strict_head(root: Path) -> str:
    content = _git(root, "rev-parse", "--verify", "HEAD^{commit}")
    try:
        value = content.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("HEAD commit encoding drift") from error
    if re.fullmatch(r"[0-9a-f]{40}\n", value) is None:
        raise ValueError("HEAD commit malformed")
    return value[:-1]


def _pinned_read(
    root: Path,
    relative: Path,
    *,
    hook: Callable[[str, Path], None] | None = None,
) -> bytes:
    """Read one leaf while pinning its complete lexical directory chain."""
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("unsafe relative path")
    root = Path(os.path.abspath(root))
    callback = (lambda event, path: None) if hook is None else hook
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise ValueError("pinned repository root unsafe")
    callback("after_initial_root_lstat", root)
    root_fd = os.open(root, DIRECTORY_FLAGS)
    directory_fds = [root_fd]
    leaf_fd: int | None = None
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("pinned repository root stat/open race")
        parent_fd = root_fd
        bindings = []
        for component in relative.parts[:-1]:
            item = os.stat(
                component,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
            identity = _identity(item)
            if (
                not stat.S_ISDIR(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
            ):
                raise ValueError("pinned path component unsafe")
            child_fd = os.open(
                component,
                DIRECTORY_FLAGS,
                dir_fd=parent_fd,
            )
            if _identity(os.fstat(child_fd)) != identity:
                os.close(child_fd)
                raise ValueError("pinned component stat/open race")
            directory_fds.append(child_fd)
            bindings.append((parent_fd, component, child_fd, identity))
            parent_fd = child_fd
        leaf = relative.parts[-1]
        before = os.stat(
            leaf,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        leaf_identity = _identity(before)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or before.st_size > MAX_FILE_BYTES
        ):
            raise ValueError("pinned leaf unsafe")
        leaf_fd = os.open(leaf, READ_FLAGS, dir_fd=parent_fd)
        if _identity(os.fstat(leaf_fd)) != leaf_identity:
            raise ValueError("pinned leaf stat/open race")
        callback("after_leaf_open", root / relative)
        content = _read_all(leaf_fd)
        after = os.stat(
            leaf,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        if (
            _identity(os.fstat(leaf_fd)) != leaf_identity
            or _identity(after) != leaf_identity
        ):
            raise ValueError("pinned leaf changed during read")
        callback("before_final_bindings", root / relative)
        for lexical_parent, name, child_fd, expected in reversed(bindings):
            lexical = os.stat(
                name,
                dir_fd=lexical_parent,
                follow_symlinks=False,
            )
            if (
                _identity(os.fstat(lexical_parent))
                != (
                    root_identity
                    if lexical_parent == root_fd
                    else next(
                        item[3]
                        for item in bindings
                        if item[2] == lexical_parent
                    )
                )
                or _identity(os.fstat(child_fd)) != expected
                or _identity(lexical) != expected
            ):
                raise ValueError("pinned component final drift")
        # Deliberately the last successful validation operation.
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(os.lstat(root)) != root_identity
        ):
            raise ValueError("pinned repository root final drift")
        return content
    finally:
        if leaf_fd is not None:
            os.close(leaf_fd)
        for descriptor in reversed(directory_fds):
            os.close(descriptor)


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT,
    *,
    head_ref: str = "HEAD",
) -> tuple[FrozenSource, ...]:
    """Authenticate the exact ordered committed source boundary."""
    _canonical_runtime_guard()
    root = Path(os.path.abspath(repo_root))
    if head_ref != "HEAD":
        raise ValueError("source snapshot head_ref must be HEAD")
    initial_head = _strict_head(root)
    identity = _git(
        root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).decode().splitlines()
    if identity != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("base identity drift")
    _git(root, "merge-base", "--is-ancestor", BASE_COMMIT, initial_head)
    if (
        len(SOURCE_BOUNDARY) != 12
        or len(set(SOURCE_PATHS)) != 12
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact12 source boundary drift")
    records = []
    for relative in SOURCE_PATHS:
        if (
            relative.parts[:2] == ("data", "raw")
            or relative.parts[0] == "checkpoints"
            or STAGE in relative.parts
        ):
            raise ValueError("unsafe source boundary")
        raw = relative.as_posix()
        index_mode, index_blob, index_stage = _parse_index(
            _git(root, "ls-files", "--stage", "--", raw), raw
        )
        base_mode, base_blob = _parse_tree(
            _git(root, "ls-tree", BASE_COMMIT, "--", raw), raw
        )
        if (
            index_stage != 0
            or index_mode != base_mode
            or index_blob != base_blob
        ):
            raise ValueError("source index/base identity drift")
        base = _git(root, "cat-file", "blob", base_blob)
        index = _git(root, "cat-file", "blob", index_blob)
        filesystem = _pinned_read(root, relative)
        expected = SOURCE_SHA256[relative]
        if (
            base != index
            or index != filesystem
            or _sha(base) != expected
            or _sha(filesystem) != expected
        ):
            raise ValueError(f"source bytes/SHA drift: {relative}")
        records.append(
            FrozenSource(
                relative,
                expected,
                base_mode,
                base_blob,
                index_mode,
                index_blob,
                index_stage,
                _sha(filesystem),
                filesystem,
            )
        )
    final_head = _strict_head(root)
    if final_head != initial_head:
        raise ValueError("source snapshot HEAD drift")
    _git(root, "merge-base", "--is-ancestor", BASE_COMMIT, final_head)
    return tuple(records)


def _source(
    snapshot: Sequence[FrozenSource], suffix: str
) -> FrozenSource:
    matches = tuple(
        item
        for item in snapshot
        if item.relative_path.as_posix().endswith(suffix)
    )
    if len(matches) != 1:
        raise ValueError(f"source missing/duplicate: {suffix}")
    return matches[0]


def _json(content: bytes) -> dict[str, Any]:
    duplicates: list[str] = []

    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicates.append(key)
            result[key] = value
        return result

    value = json.loads(content, object_pairs_hook=hook)
    if duplicates or type(value) is not dict:
        raise ValueError("JSON object/unique keys required")
    return value


def _csv_rows(
    content: bytes, columns: Sequence[str] | None = None
) -> list[dict[str, str]]:
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


def _revised2_final_lifecycle_closure() -> dict[str, object]:
    """Return deterministic infrastructure metadata; no external authority."""
    return {
        "revision": REVISED2_REVISION,
        "business_semantics_changed": False,
        "full_recursive_lifecycle_runs_before_candidate": True,
        "full_recursive_lifecycle_runs_after_candidate": True,
        "final_recursive_lifecycle_is_last_filesystem_validation": True,
        "ignored_residue_after_candidate_rejected": True,
        "generic_symlink_after_candidate_rejected": True,
        "synchronized_tamper_uses_real_fail_closed_verifier": True,
    }


def _verdict(
    scope_id: object,
    *,
    reason: str,
    required_rule_ids: tuple[str, ...] = (),
    evaluated_rule_ids: tuple[str, ...] = (),
    rule_evaluations: tuple[
        UnifiedAdmissionRuleEvaluationContractDesign, ...
    ] = (),
    invalid_rule_ids: tuple[str, ...] = (),
    blocked_rule_ids: tuple[str, ...] = (),
    failing_rule_ids: tuple[str, ...] = (),
) -> CombinedAdmissionCandidateVerdictContractDesign:
    outcome = (
        "passed"
        if reason == ""
        else (
            "blocked"
            if reason == REQUIRED_RULE_BLOCKED_REASON
            else "invalid"
        )
    )
    return CombinedAdmissionCandidateVerdictContractDesign(
        schema_version=FUTURE_RESULT_SCHEMA_VERSION,
        scope_id=scope_id if type(scope_id) is str else "",
        outcome=outcome,
        passed=outcome == "passed",
        blocks_scope_action=outcome != "passed",
        reason=reason,
        required_rule_ids=required_rule_ids,
        evaluated_rule_ids=evaluated_rule_ids,
        rule_evaluations=rule_evaluations,
        invalid_rule_ids=invalid_rule_ids,
        blocked_rule_ids=blocked_rule_ids,
        failing_rule_ids=failing_rule_ids,
        aggregation_io_used=False,
    )


def _exact_string_tuple(value: object) -> bool:
    return type(value) is tuple and all(type(item) is str for item in value)


def _exact_string_pair_tuple(value: object) -> bool:
    return type(value) is tuple and all(
        type(item) is tuple
        and len(item) == 2
        and type(item[0]) is str
        and type(item[1]) is str
        for item in value
    )


def _runtime_structure_valid(
    value: object,
) -> bool:
    if type(value) is not UnifiedAdmissionRuleEvaluationContractDesign:
        return False
    values = vars(value)
    if (
        type(values) is not dict
        or tuple(values) != INPUT_RESULT_FIELDS
        or tuple(value.__dataclass_fields__) != INPUT_RESULT_FIELDS
    ):
        return False
    string_fields = (
        "schema_version",
        "admission_rule_id",
        "admission_rule_name",
        "outcome",
        "reason",
        "adapter_id",
    )
    bool_fields = ("passed", "blocks_candidate", "evaluator_io_used")
    tuple_fields = (
        "normalized_values",
        "validated_candidate_fields",
        "consumed_candidate_fields",
        "consumed_context_items",
    )
    if (
        any(type(values[name]) is not str for name in string_fields)
        or any(type(values[name]) is not bool for name in bool_fields)
        or any(type(values[name]) is not tuple for name in tuple_fields)
    ):
        return False
    try:
        if type(value)(**values) != value:
            return False
    except (TypeError, ValueError):
        return False
    if (
        value.schema_version != INPUT_RESULT_SCHEMA_VERSION
        or value.outcome not in RUNTIME_OUTCOME_VOCABULARY
        or value.passed is not (value.outcome == "passed")
        or value.blocks_candidate is not (value.outcome != "passed")
        or value.evaluator_io_used is not False
        or (
            value.outcome == "passed"
            and value.reason != ""
        )
        or (
            value.outcome != "passed"
            and value.reason == ""
        )
        or not _exact_string_pair_tuple(value.normalized_values)
        or not _exact_string_pair_tuple(
            value.validated_candidate_fields
        )
        or not _exact_string_tuple(value.consumed_candidate_fields)
        or not _exact_string_tuple(value.consumed_context_items)
    ):
        return False
    return True


def _aggregation_identity_and_outcome_admissible(
    value: UnifiedAdmissionRuleEvaluationContractDesign,
) -> bool:
    if value.outcome not in AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES:
        return False
    if value.admission_rule_id in RULE_NAMES:
        if (
            value.admission_rule_name
            != RULE_NAMES[value.admission_rule_id]
            or value.adapter_id != ADAPTER_IDS[value.admission_rule_id]
        ):
            return False
    return True


def _evaluation_invariant_valid(value: object) -> bool:
    """Compatibility composite; the classifier observes both phases."""
    return (
        _runtime_structure_valid(value)
        and _aggregation_identity_and_outcome_admissible(value)
    )


def classify_combined_candidate_verdict_contract_design(
    scope_id: object,
    *,
    ordered_rule_evaluations: object,
) -> CombinedAdmissionCandidateVerdictContractDesign:
    """Classify mirror results only; this is not the future production API."""
    if type(scope_id) is not str or scope_id not in REQUIRED_RULE_IDS:
        return _verdict(scope_id, reason=SCOPE_ID_INVALID_REASON)
    required = REQUIRED_RULE_IDS[scope_id]
    if type(ordered_rule_evaluations) is not tuple:
        return _verdict(
            scope_id,
            reason=VECTOR_TYPE_INVALID_REASON,
            required_rule_ids=required,
        )
    structural_results = []
    for item in ordered_rule_evaluations:
        item_valid = _runtime_structure_valid(item)
        structural_results.append(item_valid)
    if not all(structural_results):
        return _verdict(
            scope_id,
            reason=EVALUATION_INVARIANT_INVALID_REASON,
            required_rule_ids=required,
        )
    admissibility_results = []
    for item in ordered_rule_evaluations:
        admissibility_results.append(
            _aggregation_identity_and_outcome_admissible(item)
        )
    if not all(admissibility_results):
        return _verdict(
            scope_id,
            reason=EVALUATION_INVARIANT_INVALID_REASON,
            required_rule_ids=required,
        )
    evaluated = tuple(
        item.admission_rule_id for item in ordered_rule_evaluations
    )
    membership_valid = (
        evaluated == required
        and len(evaluated) == len(set(evaluated))
    )
    if not membership_valid:
        return _verdict(
            scope_id,
            reason=MEMBERSHIP_INVALID_REASON,
            required_rule_ids=required,
            evaluated_rule_ids=evaluated,
        )
    invalid = tuple(
        item.admission_rule_id
        for item in ordered_rule_evaluations
        if item.outcome == "invalid"
    )
    blocked = tuple(
        item.admission_rule_id
        for item in ordered_rule_evaluations
        if item.outcome == "blocked"
    )
    failing = tuple(
        item.admission_rule_id
        for item in ordered_rule_evaluations
        if item.outcome != "passed"
    )
    reason = (
        REQUIRED_RULE_INVALID_REASON
        if invalid
        else (
            REQUIRED_RULE_BLOCKED_REASON
            if blocked
            else PASS_REASON
        )
    )
    return _verdict(
        scope_id,
        reason=reason,
        required_rule_ids=required,
        evaluated_rule_ids=evaluated,
        rule_evaluations=ordered_rule_evaluations,
        invalid_rule_ids=invalid,
        blocked_rule_ids=blocked,
        failing_rule_ids=failing,
    )


def _evaluation(
    rule_id: str,
    outcome: str = "passed",
) -> UnifiedAdmissionRuleEvaluationContractDesign:
    known = rule_id in RULE_NAMES
    return UnifiedAdmissionRuleEvaluationContractDesign(
        schema_version=INPUT_RESULT_SCHEMA_VERSION,
        admission_rule_id=rule_id,
        admission_rule_name=(
            RULE_NAMES[rule_id] if known else "unknown_rule"
        ),
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason="" if outcome == "passed" else f"{rule_id}_{outcome.upper()}",
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=(),
        consumed_context_items=(),
        evaluator_io_used=False,
        adapter_id=(
            ADAPTER_IDS[rule_id] if known else "unknown_adapter"
        ),
    )


def _all_pass(
    scope_id: str,
) -> tuple[UnifiedAdmissionRuleEvaluationContractDesign, ...]:
    return tuple(_evaluation(rule_id) for rule_id in REQUIRED_RULE_IDS[scope_id])


def _replace_evaluation(
    vector: tuple[UnifiedAdmissionRuleEvaluationContractDesign, ...],
    index: int,
    replacement: object,
) -> tuple[object, ...]:
    return tuple(
        replacement if position == index else item
        for position, item in enumerate(vector)
    )


def _mutate(
    value: UnifiedAdmissionRuleEvaluationContractDesign,
    **changes: object,
) -> UnifiedAdmissionRuleEvaluationContractDesign:
    payload = dict(vars(value))
    payload.update(changes)
    return UnifiedAdmissionRuleEvaluationContractDesign(**payload)


class _ChildSubclass(UnifiedAdmissionRuleEvaluationContractDesign):
    pass


def _subclass_child(
    value: UnifiedAdmissionRuleEvaluationContractDesign,
) -> _ChildSubclass:
    return _ChildSubclass(**vars(value))


def _verify_authorities(snapshot: Sequence[FrozenSource]) -> None:
    combined_manifest = _json(
        _source(
            snapshot,
            "covapie_combined_permission_semantics_contract_manifest.json",
        ).content
    )
    membership_rows = _csv_rows(
        _source(
            snapshot,
            "covapie_combined_permission_scope_and_rule_membership_contract.csv",
        ).content
    )
    precedence_rows = _csv_rows(
        _source(
            snapshot,
            "covapie_combined_permission_precedence_and_non_override_contract.csv",
        ).content
    )
    predecessor_truth = _csv_rows(
        _source(
            snapshot,
            "covapie_combined_permission_truth_matrix.csv",
        ).content
    )
    runtime_manifest = _json(
        _source(snapshot, "covapie_admit_001_to_015_runtime_manifest.json").content
    )
    type_owner_source = _source(
        snapshot,
        "covapie_bulk_download_admission_minimal_unified_dispatch_shell_"
        "with_admit_004.py",
    ).content
    registry = _csv_rows(
        _source(snapshot, "covapie_bulk_download_admission_rule_registry.csv").content
    )
    enforcement = _json(
        _source(
            snapshot,
            "covapie_admit_015_mandatory_training_authorization_"
            "enforcement_manifest.json",
        ).content
    )
    preconditions = _csv_rows(
        _source(
            snapshot,
            "covapie_admit_015_formal_evaluator_interface_"
            "precondition_inventory.csv",
        ).content
    )
    issues = _csv_rows(
        _source(
            snapshot,
            "covapie_combined_permission_issue_readiness_inventory.csv",
        ).content,
        ISSUE_COLUMNS,
    )
    reconstructed = []
    for scope_id in SCOPE_IDS:
        reconstructed.append(
            tuple(
                row["admission_rule_id"]
                for row in membership_rows
                if row["scope_id"] == scope_id
                and row["included"] == "true"
            )
        )
    open_issues = tuple(
        row["issue_id"]
        for row in issues
        if row["successor_effective_status"] == "open"
    )
    if (
        combined_manifest["base_identity"]["commit"] != BASE_PARENT
        or combined_manifest["permission_scope_count"] != 4
        or combined_manifest["fail_closed_precedence"]
        != list(FAIL_CLOSED_PRECEDENCE)
        or combined_manifest["precondition_transition"][
            "complete_count"
        ] != 42
        or combined_manifest["precondition_transition"][
            "supported_but_not_frozen_count"
        ] != 0
        or combined_manifest["precondition_transition"][
            "incomplete_count"
        ] != 3
        or combined_manifest["precondition_transition"][
            "implementation_blocking_count"
        ] != 3
        or tuple(reconstructed)
        != tuple(item[2] for item in SCOPE_CONTRACT)
        or len(membership_rows) != 60
        or len(precedence_rows) != 25
        or len(predecessor_truth) != 163
        or runtime_manifest["result_fields"] != list(INPUT_RESULT_FIELDS)
        or runtime_manifest["result_schema_version"]
        != INPUT_RESULT_SCHEMA_VERSION
        or runtime_manifest["outcome_vocabulary"]
        != list(RUNTIME_OUTCOME_VOCABULARY)
        or runtime_manifest["rule_names"] != RULE_NAMES
        or runtime_manifest["adapter_ids"] != ADAPTER_IDS
        or runtime_manifest["registered_rule_ids"] != list(RULE_IDS)
        or b"class UnifiedAdmissionRuleEvaluation:" not in type_owner_source
        or b"def _exact_string_pair_tuple" not in type_owner_source
        or b"def __post_init__" not in type_owner_source
        or len(registry) != 15
        or tuple(row["admission_rule_id"] for row in registry) != RULE_IDS
        or tuple(
            (row["admission_rule_id"], row["evaluation_phase"])
            for row in registry
        ) != RULE_PHASES
        or enforcement["current_permission"] is not False
        or enforcement["authorized_admit_015_training_execution_count"] != 0
        or len(preconditions) != 45
        or len(issues) != 30
        or open_issues
        != (
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        )
    ):
        raise ValueError("authoritative predecessor contract drift")


def _public_api_rows() -> list[dict[str, str]]:
    contracts = (
        ("function_name", FUTURE_FUNCTION_NAME, "future production API"),
        ("signature", FUTURE_API_SIGNATURE, "future production API"),
        ("scope_id_parameter_kind", "positional_or_keyword", "future production API"),
        ("ordered_vector_parameter_kind", "keyword_only", "future production API"),
        ("parameter_defaults", "none", "future production API"),
        ("var_positional", "forbidden", "future production API"),
        ("var_keyword", "forbidden", "future production API"),
        ("candidate_parameter", "forbidden", "future production API"),
        ("context_parameters", "forbidden", "future production API"),
        ("dispatcher_injection", "forbidden", "future production API"),
        ("registry_injection", "forbidden", "future production API"),
        ("override_or_fallback_parameter", "forbidden", "future production API"),
        (
            "input_element_type",
            "Exact15 runtime UnifiedAdmissionRuleEvaluation",
            "future production API",
        ),
        (
            "output_type",
            "CombinedAdmissionCandidateVerdict",
            "future production API",
        ),
        ("dispatcher_call_count", "0", "aggregation boundary"),
        ("single_rule_handler_call_count", "0", "aggregation boundary"),
        ("aggregation_io_used", "false", "aggregation boundary"),
        (
            "design_oracle",
            "classify_combined_candidate_verdict_contract_design",
            "not future production API",
        ),
        (
            "design_child_type",
            "UnifiedAdmissionRuleEvaluationContractDesign",
            "not Exact15 runtime class",
        ),
        (
            "design_result_type",
            "CombinedAdmissionCandidateVerdictContractDesign",
            "not future production result class",
        ),
        (
            "runtime_outcome_vocabulary",
            "passed|blocked|invalid|rejected",
            "Exact15 runtime structural contract",
        ),
        (
            "aggregation_admissible_child_outcomes",
            "passed|blocked|invalid",
            "combined permission aggregation subset",
        ),
        (
            "runtime_nested_duplicate_policy",
            "permitted_by_exact_shape_contract_and_not_interpreted_by_aggregator",
            "Exact15 runtime compatibility",
        ),
        (
            "rejected_child_aggregation_policy",
            "runtime_valid_but_aggregation_inadmissible_fail_closed_as_"
            "evaluation_invariant_invalid",
            "combined permission aggregation subset",
        ),
    )
    return [
        {
            "contract_order": str(order),
            "contract_item": item,
            "frozen_value": value,
            "design_boundary": boundary,
            "contract_passed": "true",
        }
        for order, (item, value, boundary) in enumerate(contracts, 1)
    ]


def _result_rows() -> list[dict[str, str]]:
    types = (
        ("str", "exact str"),
        ("str", "exact str; Exact4 scope vocabulary"),
        ("str", "passed|blocked|invalid"),
        ("bool", "exact bool"),
        ("bool", "exact bool"),
        ("str", "empty pass or Exact6 nonempty failure reason"),
        ("tuple", "tuple[str, ...]"),
        ("tuple", "tuple[str, ...]"),
        (
            "tuple",
            "tuple[UnifiedAdmissionRuleEvaluation, ...]",
        ),
        ("tuple", "tuple[str, ...]"),
        ("tuple", "tuple[str, ...]"),
        ("tuple", "tuple[str, ...]"),
        ("bool", "exact bool"),
    )
    invariants = (
        FUTURE_RESULT_SCHEMA_VERSION,
        "validated scope; exact str preserved on scope failure else empty",
        "invalid>blocked>passed after structural and membership validation",
        "outcome == passed",
        "outcome != passed",
        "Exact6 closed vocabulary plus empty pass reason",
        "scope Exact membership; empty only for invalid scope",
        "required order after structural validation",
        (
            "retained only after runtime structural validity, aggregation "
            "outcome admissibility, and exact membership; nested duplicate "
            "payloads are not interpreted"
        ),
        "all invalid child IDs in required order",
        "all blocked child IDs in required order",
        "all non-passed child IDs in required order",
        "always false",
    )
    rows = []
    for order, (field_name, (top, nested), invariant) in enumerate(
        zip(FUTURE_RESULT_FIELDS, types, invariants, strict=True), 1
    ):
        rows.append(
            {
                "contract_order": str(order),
                "contract_group": "future_exact13_result_field",
                "field_order": str(order),
                "field_name": field_name,
                "exact_top_level_type": top,
                "nested_type": nested,
                "fixed_or_conditional_invariant": invariant,
                "pass_projection": "canonical fully valid projection",
                "blocked_projection": "canonical fully valid projection",
                "invalid_projection": "reason-specific fail-closed projection",
                "identity_behavior": (
                    "input tuple identity retained"
                    if field_name == "rule_evaluations"
                    else "immutable scalar or tuple"
                ),
                "contract_passed": "true",
            }
        )
    for reason_order, reason in enumerate(REASON_VOCABULARY, 1):
        rows.append(
            {
                "contract_order": str(len(rows) + 1),
                "contract_group": "exact6_nonempty_reason_vocabulary",
                "field_order": str(reason_order),
                "field_name": "reason",
                "exact_top_level_type": "str",
                "nested_type": "n/a",
                "fixed_or_conditional_invariant": reason,
                "pass_projection": "",
                "blocked_projection": (
                    reason if reason == REQUIRED_RULE_BLOCKED_REASON else "n/a"
                ),
                "invalid_projection": (
                    reason if reason != REQUIRED_RULE_BLOCKED_REASON else "n/a"
                ),
                "identity_behavior": "fixed vocabulary",
                "contract_passed": "true",
            }
        )
    return rows


TruthCase = tuple[str, str, object, object, str]


def _truth_cases() -> list[TruthCase]:
    cases: list[TruthCase] = []
    for scope_id in SCOPE_IDS:
        canonical = _all_pass(scope_id)
        cases.append(
            (
                f"{scope_id}__all_pass",
                "canonical_all_pass",
                scope_id,
                canonical,
                PASS_REASON,
            )
        )
        for index, rule_id in enumerate(REQUIRED_RULE_IDS[scope_id]):
            cases.append(
                (
                    f"{scope_id}__{rule_id}__blocked",
                    "every_required_rule_blocked",
                    scope_id,
                    _replace_evaluation(
                        canonical, index, _evaluation(rule_id, "blocked")
                    ),
                    REQUIRED_RULE_BLOCKED_REASON,
                )
            )
            cases.append(
                (
                    f"{scope_id}__{rule_id}__invalid",
                    "every_required_rule_invalid",
                    scope_id,
                    _replace_evaluation(
                        canonical, index, _evaluation(rule_id, "invalid")
                    ),
                    REQUIRED_RULE_INVALID_REASON,
                )
            )
        for label, index in (
            ("first", 0),
            ("middle", len(canonical) // 2),
            ("last", len(canonical) - 1),
        ):
            cases.append(
                (
                    f"{scope_id}__missing_{label}",
                    "missing_required",
                    scope_id,
                    canonical[:index] + canonical[index + 1 :],
                    MEMBERSHIP_INVALID_REASON,
                )
            )
        extra = (
            "ADMIT_010"
            if "ADMIT_010" not in REQUIRED_RULE_IDS[scope_id]
            else (
                "ADMIT_015"
                if "ADMIT_015" not in REQUIRED_RULE_IDS[scope_id]
                else "ADMIT_999"
            )
        )
        substitute = (
            "ADMIT_010"
            if "ADMIT_010" not in REQUIRED_RULE_IDS[scope_id]
            else (
                "ADMIT_015"
                if "ADMIT_015" not in REQUIRED_RULE_IDS[scope_id]
                else "ADMIT_999"
            )
        )
        multi_blocked = _replace_evaluation(
            canonical, 0, _evaluation(canonical[0].admission_rule_id, "blocked")
        )
        multi_blocked = _replace_evaluation(
            multi_blocked,
            len(canonical) - 1,
            _evaluation(canonical[-1].admission_rule_id, "blocked"),
        )
        multi_invalid = _replace_evaluation(
            canonical, 0, _evaluation(canonical[0].admission_rule_id, "invalid")
        )
        multi_invalid = _replace_evaluation(
            multi_invalid,
            len(canonical) - 1,
            _evaluation(canonical[-1].admission_rule_id, "invalid"),
        )
        mixed = _replace_evaluation(
            canonical, 0, _evaluation(canonical[0].admission_rule_id, "blocked")
        )
        mixed = _replace_evaluation(
            mixed, 1, _evaluation(canonical[1].admission_rule_id, "invalid")
        )
        cases.extend(
            (
                (
                    f"{scope_id}__multi_blocked",
                    "multi_blocked_full_collection",
                    scope_id,
                    multi_blocked,
                    REQUIRED_RULE_BLOCKED_REASON,
                ),
                (
                    f"{scope_id}__multi_invalid",
                    "multi_invalid_full_collection",
                    scope_id,
                    multi_invalid,
                    REQUIRED_RULE_INVALID_REASON,
                ),
                (
                    f"{scope_id}__invalid_and_blocked",
                    "invalid_blocked_full_collection",
                    scope_id,
                    mixed,
                    REQUIRED_RULE_INVALID_REASON,
                ),
                (
                    f"{scope_id}__all_blocked",
                    "all_blocked_full_collection",
                    scope_id,
                    tuple(
                        _evaluation(item.admission_rule_id, "blocked")
                        for item in canonical
                    ),
                    REQUIRED_RULE_BLOCKED_REASON,
                ),
                (
                    f"{scope_id}__all_invalid",
                    "all_invalid_full_collection",
                    scope_id,
                    tuple(
                        _evaluation(item.admission_rule_id, "invalid")
                        for item in canonical
                    ),
                    REQUIRED_RULE_INVALID_REASON,
                ),
                (
                    f"{scope_id}__extra",
                    "extra_rule",
                    scope_id,
                    canonical + (_evaluation(extra),),
                    MEMBERSHIP_INVALID_REASON,
                ),
                (
                    f"{scope_id}__duplicate",
                    "duplicate_rule",
                    scope_id,
                    canonical + (canonical[0],),
                    MEMBERSHIP_INVALID_REASON,
                ),
                (
                    f"{scope_id}__reorder",
                    "reordered_rule",
                    scope_id,
                    (canonical[1], canonical[0]) + canonical[2:],
                    MEMBERSHIP_INVALID_REASON,
                ),
                (
                    f"{scope_id}__unknown",
                    "unknown_rule",
                    scope_id,
                    canonical[:-1] + (_evaluation("ADMIT_999"),),
                    MEMBERSHIP_INVALID_REASON,
                ),
                (
                    f"{scope_id}__scope_external_substitution",
                    "scope_external_substitution",
                    scope_id,
                    canonical[:-1] + (_evaluation(substitute),),
                    MEMBERSHIP_INVALID_REASON,
                ),
            )
        )
    base_scope = SCOPE_IDS[0]
    canonical = _all_pass(base_scope)
    base = canonical[0]
    field_mutations = (
        ("schema_version", 7),
        ("admission_rule_id", 7),
        ("admission_rule_name", 7),
        ("outcome", 7),
        ("passed", 0),
        ("blocks_candidate", 0),
        ("reason", 7),
        ("normalized_values", []),
        ("validated_candidate_fields", []),
        ("consumed_candidate_fields", []),
        ("consumed_context_items", []),
        ("evaluator_io_used", True),
        ("adapter_id", 7),
    )
    for field_name, replacement in field_mutations:
        cases.append(
            (
                f"exact13_field_type_mutation__{field_name}",
                "exact13_field_invariant_mutation",
                base_scope,
                _replace_evaluation(
                    canonical, 0, _mutate(base, **{field_name: replacement})
                ),
                EVALUATION_INVARIANT_INVALID_REASON,
            )
        )
    logical_mutations = (
        ("schema_mismatch", {"schema_version": "schema_v2"}),
        ("rule_name_mismatch", {"admission_rule_name": "wrong"}),
        ("adapter_id_mismatch", {"adapter_id": "wrong"}),
        ("passed_outcome_mismatch", {"passed": False}),
        ("blocks_candidate_mismatch", {"blocks_candidate": True}),
        ("pass_reason_nonempty", {"reason": "x"}),
        ("failure_reason_empty", {"outcome": "blocked", "passed": False, "blocks_candidate": True, "reason": ""}),
        ("malformed_normalized_values", {"normalized_values": (("a",),)}),
        ("malformed_validated_fields", {"validated_candidate_fields": (("a",),)}),
    )
    for case_id, changes in logical_mutations:
        cases.append(
            (
                case_id,
                "child_invariant_mutation",
                base_scope,
                _replace_evaluation(canonical, 0, _mutate(base, **changes)),
                EVALUATION_INVARIANT_INVALID_REASON,
            )
        )
    cases.extend(
        (
            (
                "runtime_rejected_outcome_is_aggregation_inadmissible",
                "runtime_valid_rejected_aggregation_inadmissible",
                base_scope,
                _replace_evaluation(
                    canonical,
                    0,
                    _mutate(
                        base,
                        outcome="rejected",
                        passed=False,
                        blocks_candidate=True,
                        reason="SYNTHETIC_RUNTIME_REJECTED",
                    ),
                ),
                EVALUATION_INVARIANT_INVALID_REASON,
            ),
            (
                "unknown_outcome_string",
                "child_invariant_mutation",
                base_scope,
                _replace_evaluation(
                    canonical,
                    0,
                    _mutate(
                        base,
                        outcome="unknown_outcome",
                        passed=False,
                        blocks_candidate=True,
                        reason="SYNTHETIC_UNKNOWN_OUTCOME",
                    ),
                ),
                EVALUATION_INVARIANT_INVALID_REASON,
            ),
            (
                "duplicate_normalized_keys",
                "runtime_valid_duplicate_nested_compatibility",
                base_scope,
                _replace_evaluation(
                    canonical,
                    0,
                    _mutate(
                        base,
                        normalized_values=(("a", "1"), ("a", "2")),
                    ),
                ),
                PASS_REASON,
            ),
            (
                "duplicate_validated_fields",
                "runtime_valid_duplicate_nested_compatibility",
                base_scope,
                _replace_evaluation(
                    canonical,
                    0,
                    _mutate(
                        base,
                        validated_candidate_fields=(
                            ("a", "1"),
                            ("a", "2"),
                        ),
                    ),
                ),
                PASS_REASON,
            ),
            (
                "duplicate_consumed_candidate_fields",
                "runtime_valid_duplicate_nested_compatibility",
                base_scope,
                _replace_evaluation(
                    canonical,
                    0,
                    _mutate(
                        base,
                        consumed_candidate_fields=("a", "a"),
                    ),
                ),
                PASS_REASON,
            ),
            (
                "duplicate_consumed_context_items",
                "runtime_valid_duplicate_nested_compatibility",
                base_scope,
                _replace_evaluation(
                    canonical,
                    0,
                    _mutate(
                        base,
                        consumed_context_items=("a", "a"),
                    ),
                ),
                PASS_REASON,
            ),
        )
    )
    cases.extend(
        (
            ("unknown_scope", "scope_invalid", "unknown", (), SCOPE_ID_INVALID_REASON),
            ("scope_bool", "scope_invalid", True, (), SCOPE_ID_INVALID_REASON),
            ("scope_none", "scope_invalid", None, (), SCOPE_ID_INVALID_REASON),
            ("vector_list", "vector_type_invalid", base_scope, list(canonical), VECTOR_TYPE_INVALID_REASON),
            ("vector_dict", "vector_type_invalid", base_scope, {}, VECTOR_TYPE_INVALID_REASON),
            ("vector_string", "vector_type_invalid", base_scope, "x", VECTOR_TYPE_INVALID_REASON),
            ("vector_none", "vector_type_invalid", base_scope, None, VECTOR_TYPE_INVALID_REASON),
            ("wrong_child_type", "child_type_invalid", base_scope, _replace_evaluation(canonical, 0, object()), EVALUATION_INVARIANT_INVALID_REASON),
            ("child_subclass", "child_type_invalid", base_scope, _replace_evaluation(canonical, 0, _subclass_child(base)), EVALUATION_INVARIANT_INVALID_REASON),
            ("valid_tuple_identity", "identity_preservation", base_scope, canonical, PASS_REASON),
            ("synthetic_pass_no_mutation", "no_permission_mutation", SCOPE_IDS[3], _all_pass(SCOPE_IDS[3]), PASS_REASON),
        )
    )
    return cases


def _representation(value: object) -> str:
    if type(value) is str:
        return value
    if value is None:
        return "None"
    return f"<{type(value).__name__}>"


def _truth_rows() -> list[dict[str, str]]:
    rows = []
    for order, (case_id, group, scope, vector, expected_reason) in enumerate(
        _truth_cases(), 1
    ):
        result = classify_combined_candidate_verdict_contract_design(
            scope, ordered_rule_evaluations=vector
        )
        expected_outcome = (
            "passed"
            if expected_reason == ""
            else (
                "blocked"
                if expected_reason == REQUIRED_RULE_BLOCKED_REASON
                else "invalid"
            )
        )
        vector_items = vector if type(vector) is tuple else ()
        input_ids = tuple(
            item.admission_rule_id
            if isinstance(item, UnifiedAdmissionRuleEvaluationContractDesign)
            and type(item.admission_rule_id) is str
            else f"<{type(item).__name__}>"
            for item in vector_items
        )
        input_outcomes = tuple(
            item.outcome
            if isinstance(item, UnifiedAdmissionRuleEvaluationContractDesign)
            and type(item.outcome) is str
            else f"<{type(item).__name__}>"
            for item in vector_items
        )
        retained = bool(result.rule_evaluations)
        identity = (
            result.rule_evaluations is vector
            if retained
            else False
        )
        passed = (
            result.outcome == expected_outcome
            and result.reason == expected_reason
            and result.passed is (expected_outcome == "passed")
            and result.blocks_scope_action is (expected_outcome != "passed")
            and result.aggregation_io_used is False
            and DISPATCHER_CALL_COUNT == 0
            and SINGLE_RULE_HANDLER_CALL_COUNT == 0
            and CURRENT_PERMISSION is False
            and AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT == 0
            and (
                not retained
                or identity
            )
        )
        rows.append(
            {
                "case_order": str(order),
                "case_id": case_id,
                "case_group": group,
                "scope_id_representation": _representation(scope),
                "vector_type": type(vector).__name__,
                "input_rule_ids": "|".join(input_ids),
                "input_outcomes": "|".join(input_outcomes),
                "expected_outcome": expected_outcome,
                "observed_outcome": result.outcome,
                "expected_reason": expected_reason,
                "observed_reason": result.reason,
                "required_rule_ids": "|".join(result.required_rule_ids),
                "evaluated_rule_ids": "|".join(result.evaluated_rule_ids),
                "invalid_rule_ids": "|".join(result.invalid_rule_ids),
                "blocked_rule_ids": "|".join(result.blocked_rule_ids),
                "failing_rule_ids": "|".join(result.failing_rule_ids),
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
        ("dispatcher_calls", "0", "0"),
        ("single_rule_handler_calls", "0", "0"),
        ("network", "false", "false"),
        ("provider", "false", "false"),
        ("download", "false", "false"),
        ("raw", "false", "false"),
        ("torch_import", "false", "false"),
        ("dataloader", "false", "false"),
        ("checkpoint", "false", "false"),
        ("model", "false", "false"),
        ("forward", "false", "false"),
        ("loss", "false", "false"),
        ("backward", "false", "false"),
        ("optimizer", "false", "false"),
        ("scheduler", "false", "false"),
        ("parameter_update", "false", "false"),
        ("checkpoint_write", "false", "false"),
        ("training_result", "false", "false"),
        ("current_permission", "false", "false"),
        ("authorized_execution_count", "0", "0"),
        ("aggregator_implementation", "false", "false"),
        ("combined_verdict_implementation", "false", "false"),
        ("orchestrator", "false", "false"),
        ("feature_semantics_audit_completed", "false", "false"),
        ("ready_for_training", "false", "false"),
        ("exact15_runtime_modified", "false", "false"),
        ("combined_semantics_stage_modified", "false", "false"),
        ("aggregation_io_used", "false", "false"),
        ("runtime_dispatcher_call_order_frozen", "false", "false"),
        ("stage_global_rule_orchestration_frozen", "false", "false"),
    )
    return [
        {
            "audit_order": str(order),
            "audit_item": item,
            "expected_state": expected,
            "observed_state": observed,
            "safety_passed": str(expected == observed).lower(),
        }
        for order, (item, expected, observed) in enumerate(states, 1)
    ]


def _issue_bytes(snapshot: Sequence[FrozenSource]) -> bytes:
    content = _source(
        snapshot,
        "covapie_combined_permission_issue_readiness_inventory.csv",
    ).content
    rows = _csv_rows(content, ISSUE_COLUMNS)
    if (
        len(rows) != 30
        or tuple(
            row["issue_id"]
            for row in rows
            if row["successor_effective_status"] == "open"
        )
        != (
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        )
    ):
        raise ValueError("Exact30 issue continuity drift")
    return content


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, str]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


TRUE_READINESS = (
    "combined_permission_semantics_frozen",
    "combined_candidate_verdict_contract_frozen",
    "cross_rule_aggregation_contract_frozen",
    "cross_rule_aggregation_public_api_frozen",
    "cross_rule_aggregation_result_contract_frozen",
    "cross_rule_aggregation_validation_precedence_frozen",
    "cross_rule_aggregation_full_vector_semantics_frozen",
    "ready_for_cross_rule_aggregation_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "runtime_dispatcher_call_order_frozen",
    "stage_global_rule_evaluation_orchestration_frozen",
    "training_orchestrator_integration_implemented",
    "feature_semantics_audit_completed",
    "historical_unknown_atom_feature_policy_resolved",
    "historical_feature_semantics_known",
    "real_training_ready",
    "ready_for_training",
)


def build_artifacts(
    snapshot: Sequence[FrozenSource],
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, bytes]:
    """Rebuild the deterministic Exact6 evidence; no production aggregation."""
    _canonical_runtime_guard()
    _verify_authorities(snapshot)
    api_rows = _public_api_rows()
    result_rows = _result_rows()
    truth_rows = _truth_rows()
    safety_rows = _safety_rows()
    issue_content = _issue_bytes(snapshot)
    if (
        len(api_rows) != 24
        or len(result_rows) != 19
        or len(truth_rows) != 201
        or len({row["case_group"] for row in truth_rows}) != 23
        or any(row["case_passed"] != "true" for row in truth_rows)
        or len(safety_rows) != 30
        or any(row["safety_passed"] != "true" for row in safety_rows)
    ):
        raise ValueError("artifact row contract drift")
    payloads = {
        PUBLIC_API_FILENAME: _csv_bytes(PUBLIC_API_COLUMNS, api_rows),
        RESULT_FILENAME: _csv_bytes(RESULT_COLUMNS, result_rows),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, safety_rows),
        ISSUE_FILENAME: issue_content,
    }
    root = Path(os.path.abspath(repo_root))
    support_sha = {
        path.as_posix(): _sha(_pinned_read(root, path))
        for path in SUPPORT_PATHS
    }
    group_counts = dict(
        sorted(Counter(row["case_group"] for row in truth_rows).items())
    )
    manifest = {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "base_identity": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "canonical_evidence_runtime": {
            "implementation": CANONICAL_PYTHON_IMPLEMENTATION,
            "version": list(CANONICAL_PYTHON_VERSION),
        },
        "source_boundary_name": "fixed_ordered_exact12_committed_source_boundary",
        "source_boundary_count": 12,
        "source_boundary": [
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
            }
            for order, item in enumerate(snapshot, 1)
        ],
        "future_public_api": {
            "function_name": FUTURE_FUNCTION_NAME,
            "signature": FUTURE_API_SIGNATURE,
            "scope_id_parameter_kind": "positional_or_keyword",
            "ordered_rule_evaluations_parameter_kind": "keyword_only",
            "defaults": False,
            "var_positional": False,
            "var_keyword": False,
            "candidate_or_context_parameters": False,
            "dispatcher_or_registry_injection": False,
            "override_or_fallback_parameters": False,
            "input_runtime_type": "UnifiedAdmissionRuleEvaluation",
            "output_future_type": "CombinedAdmissionCandidateVerdict",
        },
        "input_single_rule_result_contract": {
            "runtime_owner": (
                "covapie_bulk_download_admission_minimal_unified_dispatch_"
                "shell_with_admit_004"
            ),
            "schema_version": INPUT_RESULT_SCHEMA_VERSION,
            "field_count": 13,
            "fields": list(INPUT_RESULT_FIELDS),
            "exact_type_required": True,
            "exact_vars_dict_and_order_required": True,
            "dataclass_field_order_required": True,
            "reconstruct_equality_required": True,
            "runtime_outcomes": list(RUNTIME_OUTCOME_VOCABULARY),
            "aggregation_admissible_outcomes": list(
                AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES
            ),
            "runtime_nested_duplicates_rejected": False,
            "aggregator_interprets_nested_payloads": False,
            "rejected_is_runtime_valid": True,
            "rejected_is_aggregation_admissible": False,
            "rejected_combined_reason": (
                EVALUATION_INVARIANT_INVALID_REASON
            ),
            "evaluator_io_used": False,
            "rule_names": RULE_NAMES,
            "adapter_ids": ADAPTER_IDS,
        },
        "future_result_contract": {
            "class_name": "CombinedAdmissionCandidateVerdict",
            "schema_version": FUTURE_RESULT_SCHEMA_VERSION,
            "field_count": 13,
            "fields": list(FUTURE_RESULT_FIELDS),
            "frozen_dataclass": True,
            "exact_vars_dict_and_order_required": True,
            "dataclass_field_order_required": True,
            "reconstruct_equality_required": True,
            "mutable_container_fields": False,
            "aggregation_io_used": False,
        },
        "permission_scope_count": 4,
        "permission_scopes": [
            {
                "scope_order": order,
                "scope_id": scope_id,
                "scope_semantic_name": semantic_name,
                "required_rule_count": len(required),
                "required_rule_ids": list(required),
            }
            for order, (scope_id, semantic_name, required) in enumerate(
                SCOPE_CONTRACT, 1
            )
        ],
        "reason_vocabulary": {
            "pass_reason": PASS_REASON,
            "nonempty_reason_count": 6,
            "nonempty_reasons": list(REASON_VOCABULARY),
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
        "fail_closed_precedence": list(FAIL_CLOSED_PRECEDENCE),
        "full_vector_aggregation": {
            "short_circuit": False,
            "complete_structure_validation": True,
            "complete_membership_validation": True,
            "complete_outcome_scan": True,
            "all_invalid_ids_collected": True,
            "all_blocked_ids_collected": True,
            "full_failing_ordered_union_collected": True,
            "reorders_or_copies_valid_input": False,
            "valid_input_tuple_identity_preserved": True,
            "scoring_weighting_voting_fallback": False,
            "dispatcher_calls": 0,
            "single_rule_handler_calls": 0,
            "aggregation_io_used": False,
        },
        "truth_matrix": {
            "columns": list(TRUTH_COLUMNS),
            "row_count": len(truth_rows),
            "group_count": len(group_counts),
            "group_counts": group_counts,
            "generated_by_pure_memory_design_oracle": True,
        },
        "safety_audit": {
            "columns": list(SAFETY_COLUMNS),
            "row_count": len(safety_rows),
        },
        "issue_continuity": {
            "row_count": 30,
            "byte_identical_to_predecessor": True,
            "transition_count": 0,
            "new_issue_count": 0,
            "remaining_open_issue_ids": [
                "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
                "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            ],
        },
        "precondition_continuity": {
            "row_count": 45,
            "complete_count": 42,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 3,
            "implementation_blocking_count": 3,
            "remaining_open_precondition_ids": [
                "PRE_036",
                "PRE_038",
                "PRE_042",
            ],
            "resolved_in_this_stage": [],
            "pre_036_required_state": "implemented only after contract",
            "pre_036_remains_open_because_aggregator_not_implemented": True,
        },
        "readiness": {
            **{key: True for key in TRUE_READINESS},
            **{key: False for key in FALSE_READINESS},
        },
        "design_only_boundary": {
            "design_oracle_is_future_production_function": False,
            "design_result_is_future_production_class": False,
            "mirror_child_is_runtime_actual_type": False,
            "combined_candidate_verdict_implemented": False,
            "cross_rule_aggregation_implemented": False,
            "dispatcher_called": False,
            "single_rule_handler_called": False,
            "orchestrator_implemented": False,
            "candidate_or_context_consumed": False,
            "provider_network_download_raw_training_executed": False,
            "runtime_dispatcher_call_order_frozen": False,
            "stage_global_rule_evaluation_orchestration_frozen": False,
        },
        "current_permission": CURRENT_PERMISSION,
        "authorized_admit_015_training_execution_count": (
            AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT
        ),
        "canonical_mask_count": 5,
        "canonical_masks": [
            {"semantic_name": name, "alias": alias}
            for name, alias in CANONICAL_MASKS
        ],
        "step12d_boundary": "smoke_legality_check_not_final_training_feature_contract",
        "feature_semantics_warning": (
            "feature-semantics audit remains mandatory before training; "
            "Step12D was only a smoke legality check; historical "
            "UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=False "
            "remain unresolved"
        ),
        "revised1_infrastructure_closure": {
            "source_parent_chain_fd_pinned": True,
            "strict_initial_final_head_bound": True,
            "exact6_parent_root_set_reader_fd_pinned": True,
            "materializer_build_before_mutation": True,
            "materializer_o_excl_and_fsync": True,
            "materializer_rename_noreplace": True,
            "materializer_gpfs_einval_fail_closed": True,
            "materializer_authenticated_staging_retained": True,
            "materializer_no_os_replace": True,
            "existing_exact_set_inode_preserving_noop": True,
            "checker_recursive_lifecycle_fd_pinned": True,
            "checker_full_index_bytes_snapshotted": True,
            "git_write_tree_index_snapshot_used": False,
        },
        "revised2_final_lifecycle_closure": _revised2_final_lifecycle_closure(),
        "stage_owned_staging_namespace_closure": {
            "materializer_staging_name_prefix": STAGING_NAME_PREFIX,
            "staging_prefix_belongs_to_current_stage": True,
            "empty_retained_staging_detected_by_recursive_lifecycle": True,
            "partial_retained_staging_detected": True,
            "legacy_misnamed_staging_prefix": (
                ".combined-permission"
                "-semantics-stage-"
            ),
            "legacy_misnamed_empty_staging_rejected": True,
            "git_empty_directory_visibility_not_relied_upon": True,
            "business_semantics_changed": False,
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
            "embedded_stage_file_residue_rejected": True,
            "embedded_stage_directory_residue_rejected": True,
            "matched_directory_descendants_observed": True,
            "git_ignored_same_stage_residue_rejected": True,
            "git_untracked_inventory_not_relied_upon": True,
            "unrelated_ignored_regular_file_outside_stage_family_allowed": True,
            "derived_parent_prefix_policy_unchanged": True,
            "business_semantics_changed": False,
        },
        "derived_output_sha256": {
            (Path("data/derived/covalent_small") / STAGE / name).as_posix():
            _sha(content)
            for name, content in payloads.items()
        },
        "support_file_sha256": support_sha,
        "manifest_self_sha256_recorded": False,
        "exact10_file_count": 10,
        "all_checks_passed": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    payloads[MANIFEST_FILENAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return {name: payloads[name] for name in OUTPUT_FILES}


Identity = tuple[int, int, int, int, int, int]


def _identity(item: os.stat_result) -> Identity:
    return (
        int(item.st_dev),
        int(item.st_ino),
        int(item.st_mode),
        int(item.st_size),
        int(item.st_mtime_ns),
        int(item.st_ctime_ns),
    )


try:
    _RENAMEAT2 = ctypes.CDLL(None, use_errno=True).renameat2
    _RENAMEAT2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    _RENAMEAT2.restype = ctypes.c_int
except AttributeError:
    _RENAMEAT2 = None


@dataclass(frozen=True)
class OutputPlan:
    root: Path
    parent: Path
    root_name: str
    root_exists: bool
    parent_identity: Identity
    root_identity: Identity | None


class MaterializationRetentionError(RuntimeError):
    """Publication failed closed; authenticated staging was not deleted."""

    def __init__(self, retained_path: Path | None) -> None:
        self.authenticated_retained_path = retained_path
        super().__init__(
            "materialization failed closed; no cleanup performed; "
            f"authenticated_retained_path={retained_path}"
        )


def _inspect_output_target(
    output_root: Path, repo_root: Path
) -> OutputPlan:
    candidate = Path(output_root)
    root = (
        Path(os.path.abspath(candidate))
        if candidate.is_absolute()
        else Path(os.path.abspath(repo_root)) / candidate
    )
    if not candidate.is_absolute() and ".." in candidate.parts:
        raise ValueError("relative output escape")
    parent = root.parent
    if parent.resolve(strict=True) != parent:
        raise ValueError("output parent symlink/resolution drift")
    parent_item = os.lstat(parent)
    if (
        not stat.S_ISDIR(parent_item.st_mode)
        or stat.S_ISLNK(parent_item.st_mode)
    ):
        raise ValueError("output parent unsafe")
    parent_identity = _identity(parent_item)
    if root.exists() or root.is_symlink():
        item = os.lstat(root)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("output root unsafe")
        return OutputPlan(
            root,
            parent,
            root.name,
            True,
            parent_identity,
            _identity(item),
        )
    return OutputPlan(
        root,
        parent,
        root.name,
        False,
        parent_identity,
        None,
    )


def _read_output_set(
    root: Path,
    *,
    expected_parent_identity: Identity | None = None,
    expected_root_identity: Identity | None = None,
    hook: Callable[[str, Path], None] | None = None,
) -> dict[str, bytes]:
    """Read Exact6 through held leaf/root/parent FDs and final bindings."""
    root = Path(os.path.abspath(root))
    parent = root.parent
    callback = (lambda event, path: None) if hook is None else hook
    parent_item = os.lstat(parent)
    root_item = os.lstat(root)
    if (
        not stat.S_ISDIR(parent_item.st_mode)
        or stat.S_ISLNK(parent_item.st_mode)
        or not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise ValueError("Exact6 parent/root unsafe")
    parent_identity = _identity(parent_item)
    root_identity = _identity(root_item)
    if (
        expected_parent_identity is not None
        and parent_identity != expected_parent_identity
    ):
        raise ValueError("Exact6 expected parent identity drift")
    if (
        expected_root_identity is not None
        and root_identity != expected_root_identity
    ):
        raise ValueError("Exact6 expected root identity drift")
    callback("after_initial_lstat", root)
    parent_fd = os.open(parent, DIRECTORY_FLAGS)
    root_fd: int | None = None
    descriptors: dict[str, int] = {}
    identities: dict[str, Identity] = {}
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("Exact6 parent stat/open race")
        root_fd = os.open(
            root.name,
            DIRECTORY_FLAGS,
            dir_fd=parent_fd,
        )
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("Exact6 root stat/open race")
        callback("after_root_open", root)

        def inventory(reason: str) -> tuple[str, ...]:
            names = tuple(sorted(os.listdir(root_fd)))
            if names != tuple(sorted(OUTPUT_FILES)):
                raise ValueError(reason)
            return names

        def assert_parent_root(reason: str) -> None:
            try:
                lexical_root = os.stat(
                    root.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                lexical_parent = os.lstat(parent)
                lexical_absolute_root = os.lstat(root)
            except OSError as error:
                raise ValueError(reason) from error
            if (
                _identity(os.fstat(parent_fd)) != parent_identity
                or _identity(os.fstat(root_fd)) != root_identity
                or _identity(lexical_parent) != parent_identity
                or _identity(lexical_root) != root_identity
                or _identity(lexical_absolute_root) != root_identity
            ):
                raise ValueError(reason)

        def assert_all_leaves(reason: str) -> None:
            for name in OUTPUT_FILES:
                try:
                    lexical = os.stat(
                        name,
                        dir_fd=root_fd,
                        follow_symlinks=False,
                    )
                except OSError as error:
                    raise ValueError(reason) from error
                if (
                    _identity(os.fstat(descriptors[name]))
                    != identities[name]
                    or _identity(lexical) != identities[name]
                    or not stat.S_ISREG(lexical.st_mode)
                    or stat.S_ISLNK(lexical.st_mode)
                ):
                    raise ValueError(reason)

        assert_parent_root("Exact6 initial parent/root drift")
        initial_inventory = inventory("Exact6 output inventory drift")
        for name in OUTPUT_FILES:
            item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                not stat.S_ISREG(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
                or item.st_size > MAX_FILE_BYTES
                or Path(name).suffix.lower() in FORBIDDEN_SUFFIXES
            ):
                raise ValueError("output leaf unsafe")
            identities[name] = _identity(item)
            descriptor = os.open(name, READ_FLAGS, dir_fd=root_fd)
            descriptors[name] = descriptor
            if _identity(os.fstat(descriptor)) != identities[name]:
                raise ValueError("output leaf stat/open race")
        callback("after_leaf_open", root)
        result = {
            name: _read_all(descriptors[name]) for name in OUTPUT_FILES
        }
        assert_all_leaves("Exact6 first all-leaf drift")
        if (
            inventory("Exact6 second inventory drift")
            != initial_inventory
        ):
            raise ValueError("Exact6 second inventory drift")
        assert_parent_root("Exact6 first parent/root drift")
        callback("before_final_checks", root)
        assert_all_leaves("Exact6 final all-leaf drift")
        if (
            inventory("Exact6 final inventory drift")
            != initial_inventory
        ):
            raise ValueError("Exact6 final inventory drift")
        # Deliberately the last successful validation operation.
        assert_parent_root("Exact6 final parent/root binding drift")
        return result
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        if root_fd is not None:
            os.close(root_fd)
        os.close(parent_fd)


def _write_all(descriptor: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        count = os.write(descriptor, content[offset:])
        if type(count) is not int or count <= 0:
            raise OSError("short output write")
        offset += count


def _materialize_set(
    plan: OutputPlan,
    payloads: Mapping[str, bytes],
    *,
    hook: Callable[[str, Path], None] | None = None,
) -> None:
    callback = (lambda event, path: None) if hook is None else hook
    if (
        type(payloads) is not dict
        or tuple(payloads) != OUTPUT_FILES
        or any(type(value) is not bytes for value in payloads.values())
    ):
        raise ValueError("output payload inventory drift")
    if plan.root_exists:
        callback("before_existing_read", plan.root)
        if (
            _read_output_set(
                plan.root,
                expected_parent_identity=plan.parent_identity,
                expected_root_identity=plan.root_identity,
            )
            != payloads
        ):
            raise ValueError("existing Exact6 output payload drift")
        return
    parent_fd = os.open(plan.parent, DIRECTORY_FLAGS)
    staging_name: str | None = None
    staging_fd: int | None = None
    staging_identity: Identity | None = None
    published = False
    try:
        if (
            _identity(os.fstat(parent_fd)) != plan.parent_identity
            or _identity(os.lstat(plan.parent)) != plan.parent_identity
        ):
            raise ValueError("materialization parent stat/open race")
        for _ in range(64):
            candidate = f"{STAGING_NAME_PREFIX}{secrets.token_hex(16)}"
            try:
                os.mkdir(candidate, 0o700, dir_fd=parent_fd)
                staging_name = candidate
                break
            except FileExistsError:
                continue
        if staging_name is None:
            raise ValueError("staging name exhaustion")
        staging_fd = os.open(
            staging_name, DIRECTORY_FLAGS, dir_fd=parent_fd
        )
        staging_identity = _identity(os.fstat(staging_fd))
        if os.listdir(staging_fd):
            raise ValueError("staging not empty")
        for name, content in payloads.items():
            descriptor = os.open(
                name, WRITE_FLAGS, 0o600, dir_fd=staging_fd
            )
            try:
                _write_all(descriptor, content)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
                staging_identity = _identity(os.fstat(staging_fd))
        os.fsync(staging_fd)
        staging_identity = _identity(os.fstat(staging_fd))
        current_parent_identity = _identity(os.fstat(parent_fd))
        if _identity(os.lstat(plan.parent)) != current_parent_identity:
            raise ValueError("staging parent binding drift")
        if (
            _read_output_set(
                plan.parent / staging_name,
                expected_parent_identity=current_parent_identity,
                expected_root_identity=staging_identity,
            )
            != payloads
        ):
            raise ValueError("staging verification failed")
        if _identity(os.fstat(staging_fd)) != staging_identity:
            raise ValueError("held staging identity drift")
        callback("before_pre_rename_binding", plan.parent / staging_name)
        lexical_staging = os.stat(
            staging_name,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        current_parent_identity = _identity(os.fstat(parent_fd))
        if (
            _identity(os.lstat(plan.parent)) != current_parent_identity
            or _identity(lexical_staging) != staging_identity
            or _identity(os.fstat(staging_fd)) != staging_identity
            or not stat.S_ISDIR(lexical_staging.st_mode)
            or stat.S_ISLNK(lexical_staging.st_mode)
            or tuple(sorted(os.listdir(staging_fd)))
            != tuple(sorted(OUTPUT_FILES))
        ):
            raise ValueError("pre-rename staging/parent binding drift")
        try:
            os.stat(
                plan.root_name, dir_fd=parent_fd, follow_symlinks=False
            )
        except FileNotFoundError:
            pass
        else:
            raise ValueError("final output race")
        if _RENAMEAT2 is None:
            raise ValueError("renameat2 required")
        if _RENAMEAT2(
            parent_fd,
            os.fsencode(staging_name),
            parent_fd,
            os.fsencode(plan.root_name),
            RENAME_NOREPLACE,
        ):
            error = ctypes.get_errno()
            raise OSError(
                error,
                os.strerror(error),
                f"{staging_name}->{plan.root_name}",
            )
        published = True
        staging_name = None
        callback("after_publish", plan.root)
        published_identity = _identity(os.fstat(staging_fd))
        final_item = os.stat(
            plan.root_name,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISDIR(final_item.st_mode)
            or stat.S_ISLNK(final_item.st_mode)
            or _identity(final_item) != published_identity
        ):
            raise ValueError("post-publish root identity drift")
        published_parent_identity = _identity(os.fstat(parent_fd))
        if (
            _read_output_set(
                plan.root,
                expected_parent_identity=published_parent_identity,
                expected_root_identity=published_identity,
            )
            != payloads
        ):
            raise ValueError("published output verification failed")
        os.fsync(parent_fd)
    except BaseException as error:
        retained = None
        if (
            not published
            and staging_name is not None
            and staging_fd is not None
            and staging_identity is not None
        ):
            try:
                lexical = os.stat(
                    staging_name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                if (
                    _identity(lexical) == staging_identity
                    and _identity(os.fstat(staging_fd))
                    == staging_identity
                ):
                    retained = plan.parent / staging_name
            except OSError:
                retained = None
            raise MaterializationRetentionError(retained) from error
        raise
    finally:
        if staging_fd is not None:
            os.close(staging_fd)
        os.close(parent_fd)


def run_covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_contract_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    """Publish exactly six deterministic design-contract evidence files."""
    snapshot = build_frozen_source_snapshot(repo_root, head_ref=head_ref)
    payloads = build_artifacts(snapshot, repo_root=repo_root)
    plan = _inspect_output_target(output_root, repo_root)
    _materialize_set(plan, payloads)
    return {
        "snapshot": snapshot,
        "manifest": _json(payloads[MANIFEST_FILENAME]),
        "output_root": plan.root,
    }


if __name__ == "__main__":
    run_covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_contract_v1()
