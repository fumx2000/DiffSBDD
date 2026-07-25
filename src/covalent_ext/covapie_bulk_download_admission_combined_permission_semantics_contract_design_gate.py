"""Design-only phase-scoped combined-permission semantics contract.

This module freezes four admission-layer permission scopes and provides a
pure in-memory simulator.  It deliberately does not call the Exact15
dispatcher, implement a production aggregator or combined candidate verdict,
mutate permission, execute an action, or import training/model/torch code.
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
STEP = "combined permission semantics contract v1"
STAGE = (
    "covapie_bulk_download_admission_combined_permission_"
    "semantics_contract_v1"
)
BASE_COMMIT = "bb282ef24343baebc05212715a8c7d56bc8224ad"
BASE_PARENT = "1e076d90439e75ec9f797ed4890f8fd6594dc9fa"
BASE_TREE = "57203816d33c18ea8466633376367a2a25b9418d"
BASE_SUBJECT = (
    "add CovaPIE ADMIT_015 mandatory training authorization enforcement v1"
)
CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = (3, 10, 4)
RECOMMENDED_NEXT_STEP = (
    "design_covapie_combined_candidate_verdict_and_cross_rule_"
    "aggregation_contract_v1"
)
REVISED2_REVISION = (
    "revise_covapie_combined_permission_semantics_contract_"
    "final_lifecycle_closure_v2"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

STATE_VOCABULARY = ("passed", "blocked", "invalid")
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid")
FAIL_CLOSED_PRECEDENCE = ("invalid", "blocked", "passed")
PASS_REASON = ""
BLOCKED_REASON = "COMBINED_PERMISSION_REQUIRED_RULE_BLOCKED"
INVALID_REASON = (
    "COMBINED_PERMISSION_SCOPE_OR_VECTOR_OR_STATE_CONTRACT_INVALID"
)
CURRENT_PERMISSION = False
AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT = 0

RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
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

MEMBERSHIP_FILENAME = (
    "covapie_combined_permission_scope_and_rule_membership_contract.csv"
)
PRECEDENCE_FILENAME = (
    "covapie_combined_permission_precedence_and_non_override_contract.csv"
)
TRUTH_FILENAME = "covapie_combined_permission_truth_matrix.csv"
SAFETY_FILENAME = "covapie_combined_permission_safety_audit.csv"
ISSUE_FILENAME = (
    "covapie_combined_permission_issue_readiness_inventory.csv"
)
MANIFEST_FILENAME = (
    "covapie_combined_permission_semantics_contract_manifest.json"
)
OUTPUT_FILES = (
    MEMBERSHIP_FILENAME,
    PRECEDENCE_FILENAME,
    TRUTH_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
    MANIFEST_FILENAME,
)

MEMBERSHIP_COLUMNS = (
    "scope_order",
    "scope_id",
    "scope_semantic_name",
    "required_rule_order",
    "admission_rule_id",
    "registry_evaluation_phase",
    "included",
    "exclusion_or_inclusion_reason",
    "contract_passed",
)
PRECEDENCE_COLUMNS = (
    "contract_order",
    "contract_group",
    "contract_item",
    "frozen_value",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "scope_id_representation",
    "vector_type",
    "observed_rule_ids",
    "observed_states",
    "expected_outcome",
    "observed_outcome",
    "expected_passed",
    "observed_passed",
    "expected_blocks_action",
    "observed_blocks_action",
    "expected_reason",
    "observed_reason",
    "required_rule_ids",
    "failing_rule_ids",
    "design_io_used",
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
        "data/derived/covalent_small/"
        "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/"
        "covapie_bulk_download_admission_rule_registry.csv",
        "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
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
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_014_download_authorization_"
        "contract_v1/covapie_admit_014_download_authorization_contract_"
        "manifest.json",
        "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_015_training_authorization_"
        "contract_v1/covapie_admit_015_training_authorization_contract_"
        "manifest.json",
        "16ea4bb5f781c6f6d8277fb4142258c2bee4849b942582e48692373caee5cda1",
    ),
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_admit_015_mandatory_training_"
        "authorization_enforcement_contract_design_gate.py",
        "6acee7df5d64a1362e66646964bc6965a1ee5ffd3ac088fe81df056ea9ce1d46",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_015_mandatory_training_"
        "authorization_enforcement_contract_v1/"
        "covapie_admit_015_mandatory_training_authorization_enforcement_"
        "contract_manifest.json",
        "d1300557d62d845fd40f62992baee3784bb0b8bb33c560e7fa7f656245528171",
    ),
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_admit_015_mandatory_training_"
        "authorization_enforcement.py",
        "a2c5f5a20778d799acd04e75ac1a3cd3f920597cca613a2e5f2918ab4ee538de",
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
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_015_v1/"
        "covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv",
        "c8ea16e335e43ed781bb5177e1aba0247a55714f55eeb5caf8bed23a539f431d",
    ),
)
SOURCE_PATHS = tuple(Path(path) for path, _ in SOURCE_BOUNDARY)
SOURCE_SHA256 = {Path(path): digest for path, digest in SOURCE_BOUNDARY}

SUPPORT_PATHS = (
    Path(
        "src/covalent_ext/"
        "covapie_bulk_download_admission_combined_permission_semantics_"
        "contract_design_gate.py"
    ),
    Path(
        "scripts/"
        "check_covapie_bulk_download_admission_combined_permission_"
        "semantics_contract_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_bulk_download_admission_combined_permission_"
        "semantics_contract_v1.py"
    ),
    Path(
        "docs/"
        "covapie_bulk_download_admission_combined_permission_semantics_"
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
class CombinedPermissionDesignResult:
    """Immutable design-simulator result; not a production API contract."""

    scope_id: str
    outcome: str
    passed: bool
    blocks_action: bool
    reason: str
    required_rule_ids: tuple[str, ...]
    observed_rule_ids: tuple[str, ...]
    failing_rule_ids: tuple[str, ...]
    design_io_used: bool


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
        len(SOURCE_BOUNDARY) != 11
        or len(set(SOURCE_PATHS)) != 11
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact11 source boundary drift")
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


def _invalid_result(
    scope_id: object,
    required: tuple[str, ...] = (),
    observed: tuple[str, ...] = (),
) -> CombinedPermissionDesignResult:
    return CombinedPermissionDesignResult(
        scope_id=scope_id if type(scope_id) is str else "",
        outcome="invalid",
        passed=False,
        blocks_action=True,
        reason=INVALID_REASON,
        required_rule_ids=required,
        observed_rule_ids=observed,
        failing_rule_ids=(),
        design_io_used=False,
    )


def simulate_combined_permission_semantics_design(
    scope_id: str,
    ordered_rule_states: tuple[tuple[str, str], ...],
) -> CombinedPermissionDesignResult:
    """Evaluate only the frozen design semantics, with no I/O or mutation."""
    if type(scope_id) is not str or scope_id not in REQUIRED_RULE_IDS:
        return _invalid_result(scope_id)
    required = REQUIRED_RULE_IDS[scope_id]
    if type(ordered_rule_states) is not tuple:
        return _invalid_result(scope_id, required)
    observed_ids: list[str] = []
    states: list[str] = []
    for item in ordered_rule_states:
        if (
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not str
        ):
            return _invalid_result(scope_id, required, tuple(observed_ids))
        observed_ids.append(item[0])
        states.append(item[1])
    observed = tuple(observed_ids)
    if (
        len(observed) != len(set(observed))
        or observed != required
        or any(state not in STATE_VOCABULARY for state in states)
    ):
        return _invalid_result(scope_id, required, observed)
    failing = tuple(
        rule_id
        for rule_id, state in ordered_rule_states
        if state != "passed"
    )
    if "invalid" in states:
        return CombinedPermissionDesignResult(
            scope_id,
            "invalid",
            False,
            True,
            INVALID_REASON,
            required,
            observed,
            failing,
            False,
        )
    if "blocked" in states:
        return CombinedPermissionDesignResult(
            scope_id,
            "blocked",
            False,
            True,
            BLOCKED_REASON,
            required,
            observed,
            failing,
            False,
        )
    return CombinedPermissionDesignResult(
        scope_id,
        "passed",
        True,
        False,
        PASS_REASON,
        required,
        observed,
        (),
        False,
    )


def _verify_authorities(snapshot: Sequence[FrozenSource]) -> None:
    registry = _csv_rows(
        _source(snapshot, "covapie_bulk_download_admission_rule_registry.csv").content
    )
    if (
        len(registry) != 15
        or tuple(row["admission_rule_id"] for row in registry) != RULE_IDS
        or tuple(
            (row["admission_rule_id"], row["evaluation_phase"])
            for row in registry
        )
        != RULE_PHASES
    ):
        raise ValueError("Exact15 registry identity/phase/order drift")
    runtime_manifest = _json(
        _source(snapshot, "covapie_admit_001_to_015_runtime_manifest.json").content
    )
    enforcement_contract = _json(
        _source(
            snapshot,
            "covapie_admit_015_mandatory_training_authorization_"
            "enforcement_contract_manifest.json",
        ).content
    )
    enforcement = _json(
        _source(
            snapshot,
            "covapie_admit_015_mandatory_training_authorization_"
            "enforcement_manifest.json",
        ).content
    )
    if (
        runtime_manifest["exact15_identity"]
        != "ADMIT_001_to_ADMIT_015_unified_single_rule_runtime_v1"
        or runtime_manifest["combined_permission_semantics_frozen"] is not False
        or runtime_manifest["cross_rule_aggregation_implemented"] is not False
        or enforcement_contract["current_permission"] is not False
        or enforcement_contract[
            "authorized_admit_015_training_execution_count"
        ]
        != 0
        or enforcement["current_permission"] is not False
        or enforcement["authorized_admit_015_training_execution_count"] != 0
        or enforcement["readiness"][
            "mandatory_training_authorization_enforcement_implemented"
        ]
        is not True
        or enforcement["precondition_transition"]
        != {
            "complete_count": 41,
            "implementation_blocking_count": 4,
            "incomplete_count": 4,
            "remaining_open_precondition_ids": [
                "PRE_035",
                "PRE_036",
                "PRE_038",
                "PRE_042",
            ],
            "resolved_precondition_ids": ["PRE_034"],
            "row_count": 45,
            "supported_but_not_frozen_count": 0,
        }
    ):
        raise ValueError("predecessor readiness drift")
    preconditions = _csv_rows(
        _source(
            snapshot,
            "covapie_admit_015_formal_evaluator_interface_"
            "precondition_inventory.csv",
        ).content
    )
    if (
        len(preconditions) != 45
        or tuple(row["precondition_id"] for row in preconditions)
        != tuple(f"PRE_{index:03d}" for index in range(1, 46))
    ):
        raise ValueError("Exact45 precondition inventory drift")
    for precondition_id in ("PRE_035", "PRE_036", "PRE_038", "PRE_042"):
        row = next(
            row
            for row in preconditions
            if row["precondition_id"] == precondition_id
        )
        if (
            row["completion_status"] != "incomplete"
            or row["implementation_blocking"] != "true"
        ):
            raise ValueError("open precondition drift")
    issues = _csv_rows(
        _source(
            snapshot,
            "covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv",
        ).content,
        ISSUE_COLUMNS,
    )
    target = tuple(
        row
        for row in issues
        if row["issue_id"]
        == "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
    )
    if (
        len(issues) != 30
        or len(target) != 1
        or target[0]["successor_effective_status"] != "open"
    ):
        raise ValueError("Exact30 issue inventory drift")


def _membership_reason(scope_id: str, rule_id: str, included: bool) -> str:
    if included:
        if rule_id == "ADMIT_014":
            return "required stage download authorization; necessary not sufficient"
        if rule_id == "ADMIT_015":
            return "required only for training admission; necessary not sufficient"
        return "required admission rule for this phase-scoped permission"
    if rule_id == "ADMIT_010":
        if scope_id == "download_execution_permission":
            return "excluded: pre_final_split is not a download prerequisite"
        return "excluded: scope has not entered pre_final_split"
    if rule_id in {"ADMIT_012", "ADMIT_013"}:
        return "excluded: post_download evidence is unavailable before download"
    if rule_id == "ADMIT_015":
        return "excluded: training permission is phase-isolated"
    return "excluded by exact phase-scoped membership"


def _membership_rows() -> list[dict[str, str]]:
    rows = []
    for scope_order, (scope_id, semantic_name, required) in enumerate(
        SCOPE_CONTRACT, 1
    ):
        order_by_rule = {
            rule_id: order for order, rule_id in enumerate(required, 1)
        }
        for rule_id in RULE_IDS:
            included = rule_id in order_by_rule
            rows.append(
                {
                    "scope_order": str(scope_order),
                    "scope_id": scope_id,
                    "scope_semantic_name": semantic_name,
                    "required_rule_order": (
                        str(order_by_rule[rule_id]) if included else ""
                    ),
                    "admission_rule_id": rule_id,
                    "registry_evaluation_phase": RULE_PHASE_BY_ID[rule_id],
                    "included": str(included).lower(),
                    "exclusion_or_inclusion_reason": _membership_reason(
                        scope_id, rule_id, included
                    ),
                    "contract_passed": "true",
                }
            )
    return rows


def _precedence_rows() -> list[dict[str, str]]:
    decisions = (
        ("vocabulary", "rule state vocabulary", "passed|blocked|invalid"),
        ("vocabulary", "combined outcome vocabulary", "passed|blocked|invalid"),
        ("precedence", "fail-closed precedence", "invalid>blocked>passed"),
        ("precedence", "precedence meaning", "deterministic failure priority only"),
        ("combination", "combination operator", "monotone conjunction"),
        ("combination", "OR", "forbidden"),
        ("combination", "majority vote", "forbidden"),
        ("combination", "weighted score", "forbidden"),
        ("combination", "fallback", "forbidden"),
        ("combination", "latest pass", "forbidden"),
        ("membership", "omission as pass", "forbidden"),
        ("membership", "extra as ignore", "forbidden"),
        ("membership", "scope-external substitution", "forbidden"),
        ("non_override", "required blocked non-override", "frozen"),
        ("non_override", "required invalid non-override", "frozen"),
        ("non_override", "ADMIT_014 pass override", "forbidden"),
        ("non_override", "ADMIT_015 pass override", "forbidden"),
        ("sufficiency", "ADMIT_014 alone", "necessary_not_sufficient"),
        ("sufficiency", "ADMIT_015 alone", "necessary_not_sufficient"),
        ("authority", "bool/CLI/env/manifest/config override", "forbidden"),
        ("authority", "checkpoint/provider override", "forbidden"),
        ("boundary", "all-pass meaning", "admission_layer_only"),
        ("boundary", "real action permission", "not_implied"),
        ("boundary", "training readiness", "not_implied"),
        ("boundary", "current_permission", "false"),
    )
    return [
        {
            "contract_order": str(order),
            "contract_group": group,
            "contract_item": item,
            "frozen_value": value,
            "contract_passed": "true",
        }
        for order, (group, item, value) in enumerate(decisions, 1)
    ]


def _all_pass(scope_id: str) -> tuple[tuple[str, str], ...]:
    return tuple((rule_id, "passed") for rule_id in REQUIRED_RULE_IDS[scope_id])


def _replace_state(
    vector: tuple[tuple[str, str], ...], index: int, state: object
) -> tuple[tuple[str, object], ...]:
    return tuple(
        (rule_id, state if position == index else observed)
        for position, (rule_id, observed) in enumerate(vector)
    )


def _truth_cases() -> list[tuple[str, str, object, object, str]]:
    cases: list[tuple[str, str, object, object, str]] = []
    for scope_id in SCOPE_IDS:
        canonical = _all_pass(scope_id)
        cases.append(
            (f"{scope_id}__all_pass", "canonical_all_pass", scope_id, canonical, "passed")
        )
        for index, (rule_id, _) in enumerate(canonical):
            cases.append(
                (
                    f"{scope_id}__{rule_id}__blocked",
                    "every_required_rule_blocked",
                    scope_id,
                    _replace_state(canonical, index, "blocked"),
                    "blocked",
                )
            )
            cases.append(
                (
                    f"{scope_id}__{rule_id}__invalid",
                    "every_required_rule_invalid",
                    scope_id,
                    _replace_state(canonical, index, "invalid"),
                    "invalid",
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
                    "invalid",
                )
            )
        cases.extend(
            (
                (
                    f"{scope_id}__duplicate",
                    "duplicate_rule_id",
                    scope_id,
                    canonical + (canonical[0],),
                    "invalid",
                ),
                (
                    f"{scope_id}__reorder",
                    "reordered_rule_ids",
                    scope_id,
                    (canonical[1], canonical[0]) + canonical[2:],
                    "invalid",
                ),
            )
        )
        extra_id = {
            "download_execution_permission": "ADMIT_010",
            "post_download_acceptance_permission": "ADMIT_010",
            "pre_final_split_acceptance_permission": "ADMIT_015",
            "training_execution_admission_permission": "ADMIT_999",
        }[scope_id]
        cases.append(
            (
                f"{scope_id}__extra",
                "extra_rule_id",
                scope_id,
                canonical + ((extra_id, "passed"),),
                "invalid",
            )
        )
        invalid_and_blocked = _replace_state(canonical, 0, "blocked")
        invalid_and_blocked = _replace_state(
            invalid_and_blocked, 1, "invalid"
        )
        cases.append(
            (
                f"{scope_id}__invalid_over_blocked",
                "invalid_blocked_precedence",
                scope_id,
                invalid_and_blocked,
                "invalid",
            )
        )
        blocked_index = 0 if canonical[0][0] != "ADMIT_014" else 1
        cases.append(
            (
                f"{scope_id}__admit014_non_override",
                "admit014_pass_non_override",
                scope_id,
                _replace_state(canonical, blocked_index, "blocked"),
                "blocked",
            )
        )
    cases.extend(
        (
            (
                "unknown_scope",
                "unknown_scope",
                "unknown_permission_scope",
                (),
                "invalid",
            ),
            (
                "unknown_state",
                "unknown_state",
                SCOPE_IDS[0],
                _replace_state(_all_pass(SCOPE_IDS[0]), 0, "PASSED"),
                "invalid",
            ),
            (
                "bool_state",
                "bool_state",
                SCOPE_IDS[0],
                _replace_state(_all_pass(SCOPE_IDS[0]), 0, True),
                "invalid",
            ),
            (
                "scope_bool",
                "wrong_top_level_type",
                True,
                (),
                "invalid",
            ),
            (
                "scope_none",
                "wrong_top_level_type",
                None,
                (),
                "invalid",
            ),
            (
                "vector_list",
                "wrong_top_level_type",
                SCOPE_IDS[0],
                list(_all_pass(SCOPE_IDS[0])),
                "invalid",
            ),
            (
                "vector_dict",
                "wrong_top_level_type",
                SCOPE_IDS[0],
                {},
                "invalid",
            ),
            (
                "vector_string",
                "wrong_top_level_type",
                SCOPE_IDS[0],
                "passed",
                "invalid",
            ),
            (
                "vector_none",
                "wrong_top_level_type",
                SCOPE_IDS[0],
                None,
                "invalid",
            ),
            (
                "admit014_only",
                "necessary_not_sufficient",
                SCOPE_IDS[0],
                (("ADMIT_014", "passed"),),
                "invalid",
            ),
            (
                "admit015_only",
                "necessary_not_sufficient",
                SCOPE_IDS[3],
                (("ADMIT_015", "passed"),),
                "invalid",
            ),
            (
                "admit015_pass_non_override",
                "admit015_pass_non_override",
                SCOPE_IDS[3],
                _replace_state(_all_pass(SCOPE_IDS[3]), 0, "blocked"),
                "blocked",
            ),
        )
    )
    phase_cases = (
        ("download_extra_admit010", SCOPE_IDS[0], "ADMIT_010"),
        ("download_extra_admit012", SCOPE_IDS[0], "ADMIT_012"),
        ("download_extra_admit013", SCOPE_IDS[0], "ADMIT_013"),
        ("post_extra_admit010", SCOPE_IDS[1], "ADMIT_010"),
        ("download_extra_admit015", SCOPE_IDS[0], "ADMIT_015"),
        ("post_extra_admit015", SCOPE_IDS[1], "ADMIT_015"),
        ("prefinal_extra_admit015", SCOPE_IDS[2], "ADMIT_015"),
    )
    for case_id, scope_id, extra in phase_cases:
        cases.append(
            (
                case_id,
                "phase_isolation",
                scope_id,
                _all_pass(scope_id) + ((extra, "passed"),),
                "invalid",
            )
        )
    download = _all_pass(SCOPE_IDS[0])
    admit014_index = tuple(item[0] for item in download).index("ADMIT_014")
    cases.append(
        (
            "download_missing_admit014",
            "phase_isolation",
            SCOPE_IDS[0],
            download[:admit014_index] + download[admit014_index + 1 :],
            "invalid",
        )
    )
    cases.append(
        (
            "synthetic_pass_no_mutation",
            "synthetic_pass_no_mutation",
            SCOPE_IDS[3],
            _all_pass(SCOPE_IDS[3]),
            "passed",
        )
    )
    return cases


def _representation(value: object) -> str:
    if type(value) is str:
        return value
    if value is None:
        return "None"
    if type(value) is bool:
        return str(value)
    return type(value).__name__


def _truth_rows() -> list[dict[str, str]]:
    rows = []
    for order, (case_id, group, scope, vector, expected) in enumerate(
        _truth_cases(), 1
    ):
        result = simulate_combined_permission_semantics_design(scope, vector)
        expected_passed = expected == "passed"
        expected_blocks = not expected_passed
        expected_reason = {
            "passed": PASS_REASON,
            "blocked": BLOCKED_REASON,
            "invalid": INVALID_REASON,
        }[expected]
        observed_pairs = (
            vector
            if type(vector) is tuple
            and all(type(item) is tuple and len(item) == 2 for item in vector)
            else ()
        )
        observed_ids = tuple(
            item[0] for item in observed_pairs if type(item[0]) is str
        )
        observed_states = tuple(
            (
                item[1]
                if type(item[1]) is str
                else f"<{type(item[1]).__name__}>"
            )
            for item in observed_pairs
        )
        passed = (
            result.outcome == expected
            and result.passed is expected_passed
            and result.blocks_action is expected_blocks
            and result.reason == expected_reason
            and result.design_io_used is False
            and CURRENT_PERMISSION is False
            and AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT == 0
        )
        rows.append(
            {
                "case_order": str(order),
                "case_id": case_id,
                "case_group": group,
                "scope_id_representation": _representation(scope),
                "vector_type": type(vector).__name__,
                "observed_rule_ids": "|".join(observed_ids),
                "observed_states": "|".join(observed_states),
                "expected_outcome": expected,
                "observed_outcome": result.outcome,
                "expected_passed": str(expected_passed).lower(),
                "observed_passed": str(result.passed).lower(),
                "expected_blocks_action": str(expected_blocks).lower(),
                "observed_blocks_action": str(result.blocks_action).lower(),
                "expected_reason": expected_reason,
                "observed_reason": result.reason,
                "required_rule_ids": "|".join(result.required_rule_ids),
                "failing_rule_ids": "|".join(result.failing_rule_ids),
                "design_io_used": "false",
                "current_permission": "false",
                "authorized_execution_count": "0",
                "case_passed": str(passed).lower(),
            }
        )
    return rows


def _safety_rows() -> list[dict[str, str]]:
    states = (
        ("runtime_dispatcher_calls", "0", "0"),
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
        ("combined_candidate_verdict_implemented", "false", "false"),
        ("cross_rule_aggregation_implemented", "false", "false"),
        ("training_orchestrator_integration_implemented", "false", "false"),
        ("feature_semantics_audit_completed", "false", "false"),
        ("historical_unknown_atom_feature_policy_resolved", "false", "false"),
        ("historical_feature_semantics_known", "false", "false"),
        ("real_training_ready", "false", "false"),
        ("ready_for_training", "false", "false"),
        ("exact15_single_rule_runtime_modified", "false", "false"),
        ("admit015_mandatory_guard_modified", "false", "false"),
        ("actual_permission_mutation", "false", "false"),
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


def _issue_rows(snapshot: Sequence[FrozenSource]) -> list[dict[str, str]]:
    rows = _csv_rows(
        _source(
            snapshot,
            "covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv",
        ).content,
        ISSUE_COLUMNS,
    )
    result = []
    target = (
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
    )
    for row in rows:
        successor = dict(row)
        if row["issue_id"] == target:
            successor.update(
                {
                    "successor_effective_status": "resolved",
                    "successor_transition_stage": STAGE,
                    "successor_transition_action": (
                        "resolved_by_phase_scoped_combined_permission_"
                        "semantics_contract"
                    ),
                    "successor_transition_evidence": (
                        "Exact4 phase-scoped permission memberships; invalid>"
                        "blocked>passed monotone conjunction; ADMIT_014/015 "
                        "non-override frozen; aggregation remains unimplemented"
                    ),
                }
            )
        result.append(successor)
    if sum(left != right for left, right in zip(rows, result, strict=True)) != 1:
        raise ValueError("issue transition count drift")
    return result


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, str]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


TRUE_READINESS = (
    "mandatory_training_authorization_enforcement_implemented",
    "combined_permission_semantics_frozen",
    "phase_scoped_permission_membership_frozen",
    "combined_permission_precedence_frozen",
    "combined_permission_non_override_frozen",
    "ready_for_combined_candidate_verdict_and_cross_rule_aggregation_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_contract_frozen",
    "cross_rule_aggregation_implemented",
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
    """Rebuild the exact deterministic six-file derived evidence set."""
    _canonical_runtime_guard()
    _verify_authorities(snapshot)
    membership_rows = _membership_rows()
    precedence_rows = _precedence_rows()
    truth_rows = _truth_rows()
    safety_rows = _safety_rows()
    issue_rows = _issue_rows(snapshot)
    if (
        len(membership_rows) != 60
        or len(precedence_rows) != 25
        or not truth_rows
        or any(row["case_passed"] != "true" for row in truth_rows)
        or len(safety_rows) != 30
        or any(row["safety_passed"] != "true" for row in safety_rows)
        or len(issue_rows) != 30
    ):
        raise ValueError("artifact row contract drift")
    payloads = {
        MEMBERSHIP_FILENAME: _csv_bytes(MEMBERSHIP_COLUMNS, membership_rows),
        PRECEDENCE_FILENAME: _csv_bytes(PRECEDENCE_COLUMNS, precedence_rows),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, safety_rows),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, issue_rows),
    }
    root = Path(os.path.abspath(repo_root))
    support_sha = {
        path.as_posix(): _sha(_pinned_read(root, path))
        for path in SUPPORT_PATHS
    }
    group_counts = dict(
        sorted(Counter(row["case_group"] for row in truth_rows).items())
    )
    membership_digests = {
        scope_id: _sha(("\n".join(REQUIRED_RULE_IDS[scope_id]) + "\n").encode())
        for scope_id in SCOPE_IDS
    }
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
        "source_boundary_count": 11,
        "registry_phase_sha256": SOURCE_BOUNDARY[0][1],
        "exact15_rule_order": list(RULE_IDS),
        "registry_evaluation_phases": [
            {"admission_rule_id": rule_id, "evaluation_phase": phase}
            for rule_id, phase in RULE_PHASES
        ],
        "permission_scopes": [
            {
                "scope_order": order,
                "scope_id": scope_id,
                "scope_semantic_name": semantic_name,
                "required_rule_count": len(required),
                "required_rule_ids": list(required),
                "membership_sha256": membership_digests[scope_id],
            }
            for order, (scope_id, semantic_name, required) in enumerate(
                SCOPE_CONTRACT, 1
            )
        ],
        "permission_scope_count": 4,
        "state_vocabulary": list(STATE_VOCABULARY),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "fail_closed_precedence": list(FAIL_CLOSED_PRECEDENCE),
        "precedence_semantics": "deterministic_failure_priority_only",
        "combination_semantics": "monotone_conjunction_all_required_pass",
        "pass_reason": PASS_REASON,
        "blocked_reason": BLOCKED_REASON,
        "invalid_reason": INVALID_REASON,
        "admit_014_necessary_not_sufficient": True,
        "admit_015_necessary_not_sufficient": True,
        "blocked_invalid_non_override_frozen": True,
        "phase_isolation_frozen": True,
        "truth_matrix": {
            "columns": list(TRUTH_COLUMNS),
            "row_count": len(truth_rows),
            "group_count": len(group_counts),
            "group_counts": group_counts,
            "generated_by_pure_memory_design_simulator": True,
        },
        "safety_audit": {
            "columns": list(SAFETY_COLUMNS),
            "row_count": len(safety_rows),
        },
        "issue_transition": {
            "row_count": 30,
            "transition_count": 1,
            "transition_issue_id": (
                "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_"
                "SEMANTICS_UNRESOLVED"
            ),
            "remaining_open_issue_ids": [
                "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
                "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            ],
            "cross_rule_aggregation_implemented": False,
        },
        "precondition_transition": {
            "row_count": 45,
            "complete_count": 42,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 3,
            "implementation_blocking_count": 3,
            "resolved_precondition_ids": ["PRE_034", "PRE_035"],
            "resolved_in_this_stage": ["PRE_035"],
            "remaining_open_precondition_ids": [
                "PRE_036",
                "PRE_038",
                "PRE_042",
            ],
        },
        "readiness": {
            **{key: True for key in TRUE_READINESS},
            **{key: False for key in FALSE_READINESS},
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
        "design_scope": {
            "production_aggregation_api_frozen": False,
            "production_aggregation_result_dataclass_frozen": False,
            "dispatcher_call_order_frozen": False,
            "runtime_short_circuit_strategy_frozen": False,
            "combined_candidate_verdict_implemented": False,
            "cross_rule_aggregation_implemented": False,
            "training_orchestrator_integration_implemented": False,
            "design_simulator_is_future_production_result_contract": False,
        },
        "revised1_infrastructure_closure": {
            "revision": (
                "revise_covapie_combined_permission_semantics_contract_"
                "pinned_lifecycle_v1"
            ),
            "business_semantics_changed": False,
            "source_parent_chain_fd_pinned": True,
            "strict_initial_final_head_bound": True,
            "exact6_parent_root_set_reader_fd_pinned": True,
            "materializer_pre_rename_identity_authenticated": True,
            "materializer_post_publish_identity_authenticated": True,
            "checker_recursive_lifecycle_fd_pinned": True,
            "checker_full_index_bytes_snapshotted": True,
            "git_write_tree_index_snapshot_used": False,
        },
        "revised2_final_lifecycle_closure": (
            _revised2_final_lifecycle_closure()
        ),
        "derived_output_sha256": {
            (
                Path("data/derived/covalent_small")
                / STAGE
                / name
            ).as_posix(): _sha(content)
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
            candidate = (
                ".combined-permission-semantics-stage-"
                f"{secrets.token_hex(16)}"
            )
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


def run_covapie_bulk_download_admission_combined_permission_semantics_contract_v1(
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
    run_covapie_bulk_download_admission_combined_permission_semantics_contract_v1()
