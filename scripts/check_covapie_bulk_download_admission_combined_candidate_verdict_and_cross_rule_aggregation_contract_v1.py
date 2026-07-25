#!/usr/bin/env python3
"""Independent checker for the combined-verdict aggregation design contract."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple


BASE_COMMIT = "71fe2a41ecdf9e2317994e755ce21fc64bd05b87"
BASE_PARENT = "bb282ef24343baebc05212715a8c7d56bc8224ad"
BASE_TREE = "a50b5a13fc9b476e20fad80b15fa408b8e0a0eae"
BASE_SUBJECT = "add CovaPIE combined permission semantics contract v1"
STAGE = (
    "covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_contract_v1"
)
NEXT_STEP = (
    "implement_covapie_combined_candidate_verdict_and_cross_rule_"
    "aggregation_v1"
)
REVISED2_REVISION = (
    "revise_covapie_combined_candidate_verdict_and_cross_rule_aggregation_contract_"
    "final_lifecycle_closure_v2"
)
ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_PATH = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_"
    "contract_design_gate.py"
)
CHECKER_PATH = Path(
    "scripts/"
    "check_covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_contract_v1.py"
)
TEST_PATH = Path(
    "tests/"
    "test_covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_contract_v1.py"
)
SUMMARY_PATH = Path(
    "docs/"
    "covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_"
    "contract_v1_summary.md"
)
DERIVED_ROOT = Path("data/derived/covalent_small") / STAGE
STAGING_NAME_PREFIX = (
    "covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_contract_v1.__staging__."
)
LEGACY_MISNAMED_STAGING_PREFIX = (
    ".combined-permission-semantics-stage-"
)
PUBLIC_API_NAME = "covapie_combined_candidate_verdict_public_api_contract.csv"
RESULT_NAME = "covapie_cross_rule_aggregation_result_contract.csv"
TRUTH_NAME = "covapie_cross_rule_aggregation_truth_matrix.csv"
SAFETY_NAME = "covapie_cross_rule_aggregation_safety_audit.csv"
ISSUE_NAME = "covapie_combined_candidate_verdict_issue_readiness_inventory.csv"
MANIFEST_NAME = (
    "covapie_combined_candidate_verdict_and_cross_rule_aggregation_contract_manifest.json"
)
OUTPUT_NAMES = (
    PUBLIC_API_NAME,
    RESULT_NAME,
    TRUTH_NAME,
    SAFETY_NAME,
    ISSUE_NAME,
    MANIFEST_NAME,
)
EXACT10 = (
    PRODUCTION_PATH,
    CHECKER_PATH,
    TEST_PATH,
    SUMMARY_PATH,
    *(DERIVED_ROOT / name for name in OUTPUT_NAMES),
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

RULE_IDS = tuple(f"ADMIT_{number:03d}" for number in range(1, 16))
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
PHASES = dict(RULE_PHASES)
SCOPES = (
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
SCOPE_IDS = tuple(scope[0] for scope in SCOPES)
REQUIRED = {scope[0]: scope[2] for scope in SCOPES}
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
    rule: f"covapie_admit_{index:03d}_unified_adapter_v1"
    for index, rule in enumerate(RULE_IDS, 1)
}
INPUT_SCHEMA = "covapie_unified_admission_rule_evaluation_v1"
RESULT_SCHEMA = "covapie_combined_admission_candidate_verdict_v1"
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
INPUT_FIELDS = (
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
SCOPE_REASON, VECTOR_REASON, INVARIANT_REASON, MEMBERSHIP_REASON, INVALID_REASON, BLOCKED_REASON = REASONS
FUTURE_SIGNATURE = (
    "aggregate_admission_rule_evaluations(scope_id: str, *, "
    "ordered_rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...]) "
    "-> CombinedAdmissionCandidateVerdict"
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


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git_at(root: Path, *arguments: str) -> bytes:
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


def _git(*arguments: str) -> bytes:
    return _git_at(ROOT, *arguments)


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


def _identity(item: os.stat_result) -> tuple[int, ...]:
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )


def _read_all(descriptor: int, maximum: int = MAX_BYTES) -> bytes:
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


def _strict_head(root: Path = ROOT) -> str:
    result = _git_result(root, "rev-parse", "--verify", "HEAD^{commit}")
    if result.returncode:
        raise ValueError("HEAD commit query failed")
    try:
        value = result.stdout.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("HEAD commit encoding drift") from error
    if re.fullmatch(r"[0-9a-f]{40}\n", value) is None:
        raise ValueError("HEAD commit malformed")
    return value[:-1]


def _read_repo_relative_no_follow(
    root: Path,
    relative: Path,
    *,
    hook: Callable[[str, Path], None] | None = None,
) -> bytes:
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("source relative path unsafe")
    root = Path(os.path.abspath(root))
    callback = (lambda event, path: None) if hook is None else hook
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise ValueError("source repository root unsafe")
    callback("after_initial_root_lstat", root)
    root_fd = os.open(root, DIR_FLAGS)
    directory_fds = [root_fd]
    leaf_fd: int | None = None
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("source root stat/open race")
        parent_fd = root_fd
        bindings = []
        parent_identities = {root_fd: root_identity}
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
                raise ValueError("source path component unsafe")
            child_fd = os.open(component, DIR_FLAGS, dir_fd=parent_fd)
            if _identity(os.fstat(child_fd)) != identity:
                os.close(child_fd)
                raise ValueError("source component stat/open race")
            directory_fds.append(child_fd)
            bindings.append((parent_fd, component, child_fd, identity))
            parent_identities[child_fd] = identity
            parent_fd = child_fd
        leaf = relative.name
        item = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        leaf_identity = _identity(item)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > MAX_BYTES
        ):
            raise ValueError("source leaf unsafe")
        leaf_fd = os.open(leaf, READ_FLAGS, dir_fd=parent_fd)
        if _identity(os.fstat(leaf_fd)) != leaf_identity:
            raise ValueError("source leaf stat/open race")
        callback("after_leaf_open", root / relative)
        content = _read_all(leaf_fd)
        lexical_leaf = os.stat(
            leaf,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        if (
            _identity(os.fstat(leaf_fd)) != leaf_identity
            or _identity(lexical_leaf) != leaf_identity
        ):
            raise ValueError("source leaf final drift")
        callback("before_final_bindings", root / relative)
        for lexical_parent, name, child_fd, expected in reversed(bindings):
            if (
                _identity(os.fstat(lexical_parent))
                != parent_identities[lexical_parent]
                or _identity(os.fstat(child_fd)) != expected
                or _identity(
                    os.stat(
                        name,
                        dir_fd=lexical_parent,
                        follow_symlinks=False,
                    )
                )
                != expected
            ):
                raise ValueError("source component final drift")
        # Deliberately the last successful validation operation.
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(os.lstat(root)) != root_identity
        ):
            raise ValueError("source repository root final drift")
        return content
    finally:
        if leaf_fd is not None:
            os.close(leaf_fd)
        for descriptor in reversed(directory_fds):
            os.close(descriptor)


def _read(relative: Path) -> bytes:
    """Compatibility wrapper; all checker reads use the hardened reader."""
    return _read_repo_relative_no_follow(ROOT, relative)


def read_exact6_no_follow(
    root: Path = ROOT / DERIVED_ROOT,
    *,
    hook: Callable[[str, Path], None] | None = None,
) -> dict[str, bytes]:
    """Independently read Exact6 through held parent/root/leaf FDs."""
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
    callback("after_initial_lstat", root)
    parent_fd = os.open(parent, DIR_FLAGS)
    root_fd: int | None = None
    descriptors: dict[str, int] = {}
    identities: dict[str, tuple[int, ...]] = {}
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("Exact6 parent stat/open race")
        root_fd = os.open(root.name, DIR_FLAGS, dir_fd=parent_fd)
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("Exact6 root stat/open race")
        callback("after_root_open", root)

        def inventory(reason: str) -> tuple[str, ...]:
            names = tuple(sorted(os.listdir(root_fd)))
            if names != tuple(sorted(OUTPUT_NAMES)):
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
                absolute_root = os.lstat(root)
            except OSError as error:
                raise ValueError(reason) from error
            if (
                _identity(os.fstat(parent_fd)) != parent_identity
                or _identity(os.fstat(root_fd)) != root_identity
                or _identity(lexical_parent) != parent_identity
                or _identity(lexical_root) != root_identity
                or _identity(absolute_root) != root_identity
            ):
                raise ValueError(reason)

        def assert_all_leaves(reason: str) -> None:
            for name in OUTPUT_NAMES:
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
        initial_inventory = inventory("Exact6 inventory is not exact")
        for name in OUTPUT_NAMES:
            item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                not stat.S_ISREG(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
                or item.st_size > MAX_BYTES
                or Path(name).suffix.lower() in FORBIDDEN_SUFFIXES
            ):
                raise ValueError("Exact6 leaf unsafe")
            identities[name] = _identity(item)
            descriptor = os.open(name, READ_FLAGS, dir_fd=root_fd)
            descriptors[name] = descriptor
            if _identity(os.fstat(descriptor)) != identities[name]:
                raise ValueError("Exact6 leaf stat/open race")
        callback("after_leaf_open", root)
        payloads = {
            name: _read_all(descriptors[name]) for name in OUTPUT_NAMES
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
        return payloads
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        if root_fd is not None:
            os.close(root_fd)
        os.close(parent_fd)


def _json(content: bytes) -> dict[str, Any]:
    duplicates = []

    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                duplicates.append(key)
            value[key] = item
        return value

    value = json.loads(content, object_pairs_hook=hook)
    if duplicates or type(value) is not dict:
        raise ValueError("duplicate key/non-object JSON")
    return value


def _csv(content: bytes, columns: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    if tuple(reader.fieldnames or ()) != columns:
        raise ValueError("CSV schema drift")
    rows = [dict(row) for row in reader]
    if any(tuple(row) != columns for row in rows):
        raise ValueError("CSV row schema drift")
    return rows


def _csv_bytes(
    columns: tuple[str, ...], rows: list[dict[str, str]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _parse_stage(content: bytes, path: str) -> tuple[str, str, int]:
    metadata, observed = content.decode().rstrip("\n").split("\t", 1)
    mode, blob, stage = metadata.split(" ")
    if observed != path:
        raise ValueError("index path drift")
    return mode, blob, int(stage)


def _parse_tree(content: bytes, path: str) -> tuple[str, str]:
    metadata, observed = content.decode().rstrip("\n").split("\t", 1)
    mode, kind, blob = metadata.split(" ")
    if observed != path or kind != "blob":
        raise ValueError("tree path drift")
    return mode, blob


def _source_snapshot(root: Path = ROOT) -> list[dict[str, Any]]:
    root = Path(os.path.abspath(root))
    initial_head = _strict_head(root)
    identity = _git_at(
        root,
        "show",
        "-s",
        "--format=%H%n%P%n%T%n%s",
        BASE_COMMIT,
    ).decode().splitlines()
    if identity != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("base identity drift")
    _git_at(
        root,
        "merge-base",
        "--is-ancestor",
        BASE_COMMIT,
        initial_head,
    )
    if len(SOURCE_BOUNDARY) != 12:
        raise ValueError("source count drift")
    result = []
    for order, (raw, expected) in enumerate(SOURCE_BOUNDARY, 1):
        relative = Path(raw)
        mode, blob, stage = _parse_stage(
            _git_at(root, "ls-files", "--stage", "--", raw), raw
        )
        base_mode, base_blob = _parse_tree(
            _git_at(root, "ls-tree", BASE_COMMIT, "--", raw), raw
        )
        filesystem = _read_repo_relative_no_follow(root, relative)
        base = _git_at(root, "cat-file", "blob", base_blob)
        index = _git_at(root, "cat-file", "blob", blob)
        if (
            mode != "100644"
            or base_mode != mode
            or stage != 0
            or blob != base_blob
            or index != base
            or filesystem != base
            or _sha(filesystem) != expected
        ):
            raise ValueError(f"source drift: {raw}")
        result.append(
            {
                "source_order": order,
                "path": raw,
                "sha256": expected,
                "base_tree_mode": base_mode,
                "base_tree_blob": base_blob,
                "index_mode": mode,
                "index_blob": blob,
                "index_stage": stage,
                "filesystem_sha256": expected,
                "_content": filesystem,
            }
        )
    final_head = _strict_head(root)
    if final_head != initial_head:
        raise ValueError("source snapshot HEAD drift")
    _git_at(
        root,
        "merge-base",
        "--is-ancestor",
        BASE_COMMIT,
        final_head,
    )
    return result


@dataclass(frozen=True)
class UnifiedAdmissionRuleEvaluationContractDesign:
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
class LocalVerdict:
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


def _pairs(value: object) -> bool:
    return (
        type(value) is tuple
        and all(
            type(item) is tuple
            and len(item) == 2
            and type(item[0]) is str
            and type(item[1]) is str
            for item in value
        )
    )


def _strings(value: object) -> bool:
    return type(value) is tuple and all(type(item) is str for item in value)


def _runtime_structure_valid(value: object) -> bool:
    if type(value) is not UnifiedAdmissionRuleEvaluationContractDesign:
        return False
    values = vars(value)
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
        reconstructed = type(value)(**values)
    except (TypeError, ValueError):
        return False
    if reconstructed != value:
        return False
    if (
        value.schema_version != INPUT_SCHEMA
        or value.outcome not in RUNTIME_OUTCOME_VOCABULARY
        or value.passed is not (value.outcome == "passed")
        or value.blocks_candidate is not (value.outcome != "passed")
        or value.evaluator_io_used is not False
        or (value.outcome == "passed" and value.reason != "")
        or (value.outcome != "passed" and value.reason == "")
        or not _pairs(value.normalized_values)
        or not _pairs(value.validated_candidate_fields)
        or not _strings(value.consumed_candidate_fields)
        or not _strings(value.consumed_context_items)
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


def _child_valid(value: object) -> bool:
    return (
        _runtime_structure_valid(value)
        and _aggregation_identity_and_outcome_admissible(value)
    )


def _local_classify(scope: object, vector: object) -> LocalVerdict:
    def result(
        reason: str,
        required: tuple[str, ...] = (),
        evaluated: tuple[str, ...] = (),
        retained: tuple[UnifiedAdmissionRuleEvaluationContractDesign, ...] = (),
        invalid: tuple[str, ...] = (),
        blocked: tuple[str, ...] = (),
        failing: tuple[str, ...] = (),
    ) -> LocalVerdict:
        outcome = (
            "passed"
            if reason == ""
            else "blocked" if reason == BLOCKED_REASON else "invalid"
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
            retained,
            invalid,
            blocked,
            failing,
            False,
        )

    if type(scope) is not str or scope not in REQUIRED:
        return result(SCOPE_REASON)
    required = REQUIRED[scope]
    if type(vector) is not tuple:
        return result(VECTOR_REASON, required)
    structural = []
    for item in vector:
        structural.append(_runtime_structure_valid(item))
    if not all(structural):
        return result(INVARIANT_REASON, required)
    admissibility = []
    for item in vector:
        admissibility.append(
            _aggregation_identity_and_outcome_admissible(item)
        )
    if not all(admissibility):
        return result(INVARIANT_REASON, required)
    evaluated = tuple(item.admission_rule_id for item in vector)
    if evaluated != required or len(evaluated) != len(set(evaluated)):
        return result(MEMBERSHIP_REASON, required, evaluated)
    invalid = tuple(
        item.admission_rule_id for item in vector if item.outcome == "invalid"
    )
    blocked = tuple(
        item.admission_rule_id for item in vector if item.outcome == "blocked"
    )
    failing = tuple(
        item.admission_rule_id for item in vector if item.outcome != "passed"
    )
    reason = INVALID_REASON if invalid else BLOCKED_REASON if blocked else ""
    return result(reason, required, evaluated, vector, invalid, blocked, failing)


def _evaluation(rule: str, outcome: str = "passed") -> UnifiedAdmissionRuleEvaluationContractDesign:
    known = rule in RULE_NAMES
    return UnifiedAdmissionRuleEvaluationContractDesign(
        INPUT_SCHEMA,
        rule,
        RULE_NAMES[rule] if known else "unknown_rule",
        outcome,
        outcome == "passed",
        outcome != "passed",
        "" if outcome == "passed" else f"{rule}_{outcome.upper()}",
        (),
        (),
        (),
        (),
        False,
        ADAPTER_IDS[rule] if known else "unknown_adapter",
    )


def _pass(scope: str) -> tuple[UnifiedAdmissionRuleEvaluationContractDesign, ...]:
    return tuple(_evaluation(rule) for rule in REQUIRED[scope])


def _replace(vector: tuple[Any, ...], index: int, value: object) -> tuple[Any, ...]:
    return tuple(
        value if position == index else item
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


def _truth_cases() -> list[tuple[str, str, object, object, str]]:
    cases = []
    for scope in SCOPE_IDS:
        canonical = _pass(scope)
        cases.append((f"{scope}__all_pass", "canonical_all_pass", scope, canonical, ""))
        for index, rule in enumerate(REQUIRED[scope]):
            cases.append((f"{scope}__{rule}__blocked", "every_required_rule_blocked", scope, _replace(canonical, index, _evaluation(rule, "blocked")), BLOCKED_REASON))
            cases.append((f"{scope}__{rule}__invalid", "every_required_rule_invalid", scope, _replace(canonical, index, _evaluation(rule, "invalid")), INVALID_REASON))
        for label, index in (("first", 0), ("middle", len(canonical) // 2), ("last", len(canonical) - 1)):
            cases.append((f"{scope}__missing_{label}", "missing_required", scope, canonical[:index] + canonical[index + 1 :], MEMBERSHIP_REASON))
        extra = "ADMIT_010" if "ADMIT_010" not in REQUIRED[scope] else "ADMIT_015" if "ADMIT_015" not in REQUIRED[scope] else "ADMIT_999"
        substitute = extra
        multi_blocked = _replace(_replace(canonical, 0, _evaluation(canonical[0].admission_rule_id, "blocked")), len(canonical) - 1, _evaluation(canonical[-1].admission_rule_id, "blocked"))
        multi_invalid = _replace(_replace(canonical, 0, _evaluation(canonical[0].admission_rule_id, "invalid")), len(canonical) - 1, _evaluation(canonical[-1].admission_rule_id, "invalid"))
        mixed = _replace(_replace(canonical, 0, _evaluation(canonical[0].admission_rule_id, "blocked")), 1, _evaluation(canonical[1].admission_rule_id, "invalid"))
        cases.extend(
            (
                (f"{scope}__multi_blocked", "multi_blocked_full_collection", scope, multi_blocked, BLOCKED_REASON),
                (f"{scope}__multi_invalid", "multi_invalid_full_collection", scope, multi_invalid, INVALID_REASON),
                (f"{scope}__invalid_and_blocked", "invalid_blocked_full_collection", scope, mixed, INVALID_REASON),
                (f"{scope}__all_blocked", "all_blocked_full_collection", scope, tuple(_evaluation(item.admission_rule_id, "blocked") for item in canonical), BLOCKED_REASON),
                (f"{scope}__all_invalid", "all_invalid_full_collection", scope, tuple(_evaluation(item.admission_rule_id, "invalid") for item in canonical), INVALID_REASON),
                (f"{scope}__extra", "extra_rule", scope, canonical + (_evaluation(extra),), MEMBERSHIP_REASON),
                (f"{scope}__duplicate", "duplicate_rule", scope, canonical + (canonical[0],), MEMBERSHIP_REASON),
                (f"{scope}__reorder", "reordered_rule", scope, (canonical[1], canonical[0]) + canonical[2:], MEMBERSHIP_REASON),
                (f"{scope}__unknown", "unknown_rule", scope, canonical[:-1] + (_evaluation("ADMIT_999"),), MEMBERSHIP_REASON),
                (f"{scope}__scope_external_substitution", "scope_external_substitution", scope, canonical[:-1] + (_evaluation(substitute),), MEMBERSHIP_REASON),
            )
        )
    scope = SCOPE_IDS[0]
    canonical = _pass(scope)
    base = canonical[0]
    for field_name, replacement in (
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
    ):
        cases.append((f"exact13_field_type_mutation__{field_name}", "exact13_field_invariant_mutation", scope, _replace(canonical, 0, _mutate(base, **{field_name: replacement})), INVARIANT_REASON))
    for case_id, changes in (
        ("schema_mismatch", {"schema_version": "schema_v2"}),
        ("rule_name_mismatch", {"admission_rule_name": "wrong"}),
        ("adapter_id_mismatch", {"adapter_id": "wrong"}),
        ("passed_outcome_mismatch", {"passed": False}),
        ("blocks_candidate_mismatch", {"blocks_candidate": True}),
        ("pass_reason_nonempty", {"reason": "x"}),
        ("failure_reason_empty", {"outcome": "blocked", "passed": False, "blocks_candidate": True, "reason": ""}),
        ("malformed_normalized_values", {"normalized_values": (("a",),)}),
        ("malformed_validated_fields", {"validated_candidate_fields": (("a",),)}),
    ):
        cases.append((case_id, "child_invariant_mutation", scope, _replace(canonical, 0, _mutate(base, **changes)), INVARIANT_REASON))
    cases.extend(
        (
            (
                "runtime_rejected_outcome_is_aggregation_inadmissible",
                "runtime_valid_rejected_aggregation_inadmissible",
                scope,
                _replace(
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
                INVARIANT_REASON,
            ),
            (
                "unknown_outcome_string",
                "child_invariant_mutation",
                scope,
                _replace(
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
                INVARIANT_REASON,
            ),
            (
                "duplicate_normalized_keys",
                "runtime_valid_duplicate_nested_compatibility",
                scope,
                _replace(
                    canonical,
                    0,
                    _mutate(
                        base,
                        normalized_values=(("a", "1"), ("a", "2")),
                    ),
                ),
                "",
            ),
            (
                "duplicate_validated_fields",
                "runtime_valid_duplicate_nested_compatibility",
                scope,
                _replace(
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
                "",
            ),
            (
                "duplicate_consumed_candidate_fields",
                "runtime_valid_duplicate_nested_compatibility",
                scope,
                _replace(
                    canonical,
                    0,
                    _mutate(
                        base,
                        consumed_candidate_fields=("a", "a"),
                    ),
                ),
                "",
            ),
            (
                "duplicate_consumed_context_items",
                "runtime_valid_duplicate_nested_compatibility",
                scope,
                _replace(
                    canonical,
                    0,
                    _mutate(
                        base,
                        consumed_context_items=("a", "a"),
                    ),
                ),
                "",
            ),
        )
    )
    cases.extend(
        (
            ("unknown_scope", "scope_invalid", "unknown", (), SCOPE_REASON),
            ("scope_bool", "scope_invalid", True, (), SCOPE_REASON),
            ("scope_none", "scope_invalid", None, (), SCOPE_REASON),
            ("vector_list", "vector_type_invalid", scope, list(canonical), VECTOR_REASON),
            ("vector_dict", "vector_type_invalid", scope, {}, VECTOR_REASON),
            ("vector_string", "vector_type_invalid", scope, "x", VECTOR_REASON),
            ("vector_none", "vector_type_invalid", scope, None, VECTOR_REASON),
            ("wrong_child_type", "child_type_invalid", scope, _replace(canonical, 0, object()), INVARIANT_REASON),
            ("child_subclass", "child_type_invalid", scope, _replace(canonical, 0, _ChildSubclass(**vars(base))), INVARIANT_REASON),
            ("valid_tuple_identity", "identity_preservation", scope, canonical, ""),
            ("synthetic_pass_no_mutation", "no_permission_mutation", SCOPE_IDS[3], _pass(SCOPE_IDS[3]), ""),
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
    for order, (case_id, group, scope, vector, expected_reason) in enumerate(_truth_cases(), 1):
        result = _local_classify(scope, vector)
        expected_outcome = "passed" if expected_reason == "" else "blocked" if expected_reason == BLOCKED_REASON else "invalid"
        items = vector if type(vector) is tuple else ()
        ids = tuple(item.admission_rule_id if isinstance(item, UnifiedAdmissionRuleEvaluationContractDesign) and type(item.admission_rule_id) is str else f"<{type(item).__name__}>" for item in items)
        outcomes = tuple(item.outcome if isinstance(item, UnifiedAdmissionRuleEvaluationContractDesign) and type(item.outcome) is str else f"<{type(item).__name__}>" for item in items)
        retained = bool(result.rule_evaluations)
        identity = result.rule_evaluations is vector if retained else False
        case_passed = (
            result.outcome == expected_outcome
            and result.reason == expected_reason
            and result.passed is (expected_outcome == "passed")
            and result.blocks_scope_action is (expected_outcome != "passed")
            and result.aggregation_io_used is False
            and (not retained or identity)
        )
        rows.append(
            {
                "case_order": str(order),
                "case_id": case_id,
                "case_group": group,
                "scope_id_representation": _representation(scope),
                "vector_type": type(vector).__name__,
                "input_rule_ids": "|".join(ids),
                "input_outcomes": "|".join(outcomes),
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
                "case_passed": str(case_passed).lower(),
            }
        )
    return rows


def _public_api_rows() -> list[dict[str, str]]:
    contracts = (
        ("function_name", "aggregate_admission_rule_evaluations", "future production API"),
        ("signature", FUTURE_SIGNATURE, "future production API"),
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
        ("input_element_type", "Exact15 runtime UnifiedAdmissionRuleEvaluation", "future production API"),
        ("output_type", "CombinedAdmissionCandidateVerdict", "future production API"),
        ("dispatcher_call_count", "0", "aggregation boundary"),
        ("single_rule_handler_call_count", "0", "aggregation boundary"),
        ("aggregation_io_used", "false", "aggregation boundary"),
        ("design_oracle", "classify_combined_candidate_verdict_contract_design", "not future production API"),
        ("design_child_type", "UnifiedAdmissionRuleEvaluationContractDesign", "not Exact15 runtime class"),
        ("design_result_type", "CombinedAdmissionCandidateVerdictContractDesign", "not future production result class"),
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
        ("tuple", "tuple[UnifiedAdmissionRuleEvaluation, ...]"),
        ("tuple", "tuple[str, ...]"),
        ("tuple", "tuple[str, ...]"),
        ("tuple", "tuple[str, ...]"),
        ("bool", "exact bool"),
    )
    invariants = (
        RESULT_SCHEMA,
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
    for order, (field_name, (top, nested), invariant) in enumerate(zip(RESULT_FIELDS, types, invariants, strict=True), 1):
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
                "identity_behavior": "input tuple identity retained" if field_name == "rule_evaluations" else "immutable scalar or tuple",
                "contract_passed": "true",
            }
        )
    for reason_order, reason in enumerate(REASONS, 1):
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
                "blocked_projection": reason if reason == BLOCKED_REASON else "n/a",
                "invalid_projection": reason if reason != BLOCKED_REASON else "n/a",
                "identity_behavior": "fixed vocabulary",
                "contract_passed": "true",
            }
        )
    return rows


def _safety_rows() -> list[dict[str, str]]:
    names = (
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
        ("aggregator_implementation", "false"),
        ("combined_verdict_implementation", "false"),
        ("orchestrator", "false"),
        ("feature_semantics_audit_completed", "false"),
        ("ready_for_training", "false"),
        ("exact15_runtime_modified", "false"),
        ("combined_semantics_stage_modified", "false"),
        ("aggregation_io_used", "false"),
        ("runtime_dispatcher_call_order_frozen", "false"),
        ("stage_global_rule_orchestration_frozen", "false"),
    )
    return [
        {
            "audit_order": str(order),
            "audit_item": name,
            "expected_state": state,
            "observed_state": state,
            "safety_passed": "true",
        }
        for order, (name, state) in enumerate(names, 1)
    ]


def _revised2_final_lifecycle_closure() -> dict[str, Any]:
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


def _local_expected(
    snapshot: list[dict[str, Any]],
) -> dict[str, bytes]:
    by_suffix = {
        Path(item["path"]).name: item["_content"]
        for item in snapshot
    }
    registry_content = by_suffix["covapie_bulk_download_admission_rule_registry.csv"]
    registry_columns = tuple(next(csv.reader(io.StringIO(registry_content.decode()))))
    registry = _csv(registry_content, registry_columns)
    runtime_manifest = _json(
        by_suffix["covapie_admit_001_to_015_runtime_manifest.json"]
    )
    type_owner_source = by_suffix[
        "covapie_bulk_download_admission_minimal_unified_dispatch_shell_"
        "with_admit_004.py"
    ]
    predecessor_manifest = _json(
        by_suffix["covapie_combined_permission_semantics_contract_manifest.json"]
    )
    issues = by_suffix[
        "covapie_combined_permission_issue_readiness_inventory.csv"
    ]
    if (
        len(registry) != 15
        or tuple(row["admission_rule_id"] for row in registry) != RULE_IDS
        or tuple((row["admission_rule_id"], row["evaluation_phase"]) for row in registry) != RULE_PHASES
        or runtime_manifest["result_fields"] != list(INPUT_FIELDS)
        or runtime_manifest["result_schema_version"] != INPUT_SCHEMA
        or runtime_manifest["outcome_vocabulary"]
        != list(RUNTIME_OUTCOME_VOCABULARY)
        or runtime_manifest["rule_names"] != RULE_NAMES
        or runtime_manifest["adapter_ids"] != ADAPTER_IDS
        or b"class UnifiedAdmissionRuleEvaluation:" not in type_owner_source
        or b"def _exact_string_pair_tuple" not in type_owner_source
        or b"def __post_init__" not in type_owner_source
        or predecessor_manifest["precondition_transition"]["complete_count"] != 42
        or len(_csv(issues, ISSUE_COLUMNS)) != 30
    ):
        raise ValueError("checker-local authority semantic drift")
    api = _public_api_rows()
    result = _result_rows()
    truth = _truth_rows()
    safety = _safety_rows()
    payloads = {
        PUBLIC_API_NAME: _csv_bytes(PUBLIC_API_COLUMNS, api),
        RESULT_NAME: _csv_bytes(RESULT_COLUMNS, result),
        TRUTH_NAME: _csv_bytes(TRUTH_COLUMNS, truth),
        SAFETY_NAME: _csv_bytes(SAFETY_COLUMNS, safety),
        ISSUE_NAME: issues,
    }
    support = {
        path.as_posix(): _sha(_read(path))
        for path in (PRODUCTION_PATH, CHECKER_PATH, TEST_PATH, SUMMARY_PATH)
    }
    group_counts = dict(sorted(Counter(row["case_group"] for row in truth).items()))
    manifest = {
        "project": "CovaPIE",
        "step": "combined candidate verdict and cross-rule aggregation contract v1",
        "stage": STAGE,
        "base_identity": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "canonical_evidence_runtime": {
            "implementation": "cpython",
            "version": [3, 10, 4],
        },
        "source_boundary_name": "fixed_ordered_exact12_committed_source_boundary",
        "source_boundary_count": 12,
        "source_boundary": [
            {key: value for key, value in item.items() if key != "_content"}
            for item in snapshot
        ],
        "future_public_api": {
            "function_name": "aggregate_admission_rule_evaluations",
            "signature": FUTURE_SIGNATURE,
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
            "schema_version": INPUT_SCHEMA,
            "field_count": 13,
            "fields": list(INPUT_FIELDS),
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
            "rejected_combined_reason": INVARIANT_REASON,
            "evaluator_io_used": False,
            "rule_names": RULE_NAMES,
            "adapter_ids": ADAPTER_IDS,
        },
        "future_result_contract": {
            "class_name": "CombinedAdmissionCandidateVerdict",
            "schema_version": RESULT_SCHEMA,
            "field_count": 13,
            "fields": list(RESULT_FIELDS),
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
                "scope_id": scope,
                "scope_semantic_name": name,
                "required_rule_count": len(required),
                "required_rule_ids": list(required),
            }
            for order, (scope, name, required) in enumerate(SCOPES, 1)
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
        "fail_closed_precedence": ["invalid", "blocked", "passed"],
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
            "row_count": len(truth),
            "group_count": len(group_counts),
            "group_counts": group_counts,
            "generated_by_pure_memory_design_oracle": True,
        },
        "safety_audit": {
            "columns": list(SAFETY_COLUMNS),
            "row_count": len(safety),
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
            "remaining_open_precondition_ids": ["PRE_036", "PRE_038", "PRE_042"],
            "resolved_in_this_stage": [],
            "pre_036_required_state": "implemented only after contract",
            "pre_036_remains_open_because_aggregator_not_implemented": True,
        },
        "readiness": {
            "combined_permission_semantics_frozen": True,
            "combined_candidate_verdict_contract_frozen": True,
            "cross_rule_aggregation_contract_frozen": True,
            "cross_rule_aggregation_public_api_frozen": True,
            "cross_rule_aggregation_result_contract_frozen": True,
            "cross_rule_aggregation_validation_precedence_frozen": True,
            "cross_rule_aggregation_full_vector_semantics_frozen": True,
            "ready_for_cross_rule_aggregation_implementation": True,
            "feature_semantics_audit_required_before_training": True,
            "combined_candidate_verdict_implemented": False,
            "cross_rule_aggregation_implemented": False,
            "runtime_dispatcher_call_order_frozen": False,
            "stage_global_rule_evaluation_orchestration_frozen": False,
            "training_orchestrator_integration_implemented": False,
            "feature_semantics_audit_completed": False,
            "historical_unknown_atom_feature_policy_resolved": False,
            "historical_feature_semantics_known": False,
            "real_training_ready": False,
            "ready_for_training": False,
        },
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
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
        "stage_owned_staging_namespace_closure": {
            "materializer_staging_name_prefix": STAGING_NAME_PREFIX,
            "staging_prefix_belongs_to_current_stage": True,
            "empty_retained_staging_detected_by_recursive_lifecycle": True,
            "partial_retained_staging_detected": True,
            "legacy_misnamed_staging_prefix": (
                LEGACY_MISNAMED_STAGING_PREFIX
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
            (DERIVED_ROOT / name).as_posix(): _sha(content)
            for name, content in payloads.items()
        },
        "support_file_sha256": support,
        "manifest_self_sha256_recorded": False,
        "exact10_file_count": 10,
        "all_checks_passed": True,
        "recommended_next_step": NEXT_STEP,
    }
    manifest["revised2_final_lifecycle_closure"] = (
        _revised2_final_lifecycle_closure()
    )
    payloads[MANIFEST_NAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return {name: payloads[name] for name in OUTPUT_NAMES}


def _verify_observed_artifacts(
    observed: dict[str, bytes],
    expected: dict[str, bytes],
) -> dict[str, Any]:
    """Require exact payload bytes plus canonical recursive Manifest truth."""
    if (
        type(observed) is not dict
        or type(expected) is not dict
        or tuple(observed) != OUTPUT_NAMES
        or tuple(expected) != OUTPUT_NAMES
        or any(type(value) is not bytes for value in observed.values())
        or any(type(value) is not bytes for value in expected.values())
    ):
        raise ValueError("observed/expected Exact6 payload inventory drift")
    for name in OUTPUT_NAMES[:-1]:
        if observed[name] != expected[name]:
            raise ValueError(f"checker-local CSV reconstruction mismatch: {name}")
    observed_manifest = _json(observed[MANIFEST_NAME])
    expected_manifest = _json(expected[MANIFEST_NAME])
    observed_canonical = (
        json.dumps(observed_manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    expected_canonical = (
        json.dumps(expected_manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    if observed[MANIFEST_NAME] != observed_canonical:
        raise ValueError("observed Manifest is not canonical JSON")
    if expected[MANIFEST_NAME] != expected_canonical:
        raise ValueError("expected Manifest is not canonical JSON")
    if (
        observed[MANIFEST_NAME] != expected[MANIFEST_NAME]
        or observed_manifest != expected_manifest
    ):
        raise ValueError("checker-local recursive Manifest mismatch")
    return observed_manifest


def _load_candidate() -> Any:
    spec = importlib.util.spec_from_file_location(
        "covapie_combined_aggregation_contract_candidate",
        ROOT / PRODUCTION_PATH,
    )
    if spec is None or spec.loader is None:
        raise ValueError("candidate import spec failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _matches_bounded_support_stage_family(name: str) -> bool:
    return (
        STAGE in name
        or name
        in {
            PRODUCTION_PATH.name,
            CHECKER_PATH.name,
            TEST_PATH.name,
            SUMMARY_PATH.name,
        }
    )


def _bounded_recursive_stage_inventory(
    root: Path,
    *,
    hook: Callable[[str, Path], None] | None = None,
) -> tuple[dict[Path, os.stat_result], tuple[Path, ...]]:
    """Scan only bounded roots while pinning every traversed directory."""
    root = Path(os.path.abspath(root))
    callback = (lambda event, path: None) if hook is None else hook
    observed: dict[Path, os.stat_result] = {}
    derived_roots: list[Path] = []
    fd_identities: dict[int, tuple[int, ...]] = {}

    def stat_at(parent_fd: int, name: str, reason: str) -> os.stat_result:
        try:
            return os.stat(
                name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except OSError as error:
            raise ValueError(f"{reason} stat failed") from error

    def names(directory_fd: int, reason: str) -> tuple[str, ...]:
        try:
            return tuple(sorted(os.listdir(directory_fd)))
        except OSError as error:
            raise ValueError(f"{reason} inventory failed") from error

    def assert_directory(
        item: os.stat_result,
        expected: tuple[int, ...],
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
        expected: tuple[int, ...],
        reason: str,
    ) -> int:
        callback("before_top_root_open", Path(name))
        try:
            descriptor = os.open(name, DIR_FLAGS, dir_fd=parent_fd)
        except OSError as error:
            raise ValueError(f"{reason} open failed") from error
        try:
            assert_directory(os.fstat(descriptor), expected, reason)
        except BaseException:
            os.close(descriptor)
            raise
        callback("after_top_root_open", Path(name))
        return descriptor

    def assert_child_binding(
        parent_fd: int,
        name: str,
        child_fd: int,
        expected: tuple[int, ...],
        reason: str,
    ) -> None:
        assert_directory(
            os.fstat(parent_fd),
            fd_identities[parent_fd],
            reason,
        )
        assert_directory(stat_at(parent_fd, name, reason), expected, reason)
        assert_directory(os.fstat(child_fd), expected, reason)

    def scan_directory(
        directory_fd: int,
        logical: Path,
        expected: tuple[int, ...],
        *,
        observe_all: bool,
    ) -> None:
        assert_directory(os.fstat(directory_fd), expected, "bounded scan")
        initial_names = names(directory_fd, "bounded scan initial")
        identities = {}
        for name in initial_names:
            item = stat_at(directory_fd, name, "bounded scan entry")
            identity = _identity(item)
            identities[name] = identity
            # Reject generic symlinks before applying any stage-name filter.
            if stat.S_ISLNK(item.st_mode):
                raise ValueError("bounded scan generic symlink rejected")
            relative = logical / name
            matched = (
                observe_all
                or _matches_bounded_support_stage_family(name)
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
        expected: tuple[int, ...],
    ) -> None:
        assert_directory(os.fstat(directory_fd), expected, "derived parent")
        initial_names = names(directory_fd, "derived parent initial")
        matching = {}
        for name in initial_names:
            item = stat_at(directory_fd, name, "derived parent entry")
            # This check intentionally precedes the matching-root filter.
            if stat.S_ISLNK(item.st_mode):
                raise ValueError("derived parent generic symlink rejected")
            if name.startswith(LEGACY_MISNAMED_STAGING_PREFIX):
                raise ValueError(
                    "legacy misnamed current-stage staging residue rejected"
                )
            if not (
                name.startswith(STAGING_NAME_PREFIX)
                or name.startswith(STAGE)
            ):
                continue
            identity = _identity(item)
            if not stat.S_ISDIR(item.st_mode):
                raise ValueError("matching derived root unsafe")
            relative = logical / name
            matching[name] = identity
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
        if names(directory_fd, "derived parent final") != initial_names:
            raise ValueError("derived parent inventory drift")
        assert_directory(
            os.fstat(directory_fd),
            expected,
            "derived parent final",
        )
        for name, identity in matching.items():
            assert_directory(
                stat_at(directory_fd, name, "derived root final"),
                identity,
                "derived root final",
            )

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
        descriptors = []
        bindings = []
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
                bindings.append(
                    (parent_fd, component, child_fd, identity)
                )
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
) -> None:
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


class LifecycleSnapshot(NamedTuple):
    head: str
    identities: tuple[tuple[str, tuple[int, ...]], ...]
    tracked: frozenset[str]
    untracked: frozenset[str]
    listed_untracked: tuple[str, ...]
    staged: tuple[str, ...]
    unstaged: tuple[str, ...]
    status: bytes
    full_index: bytes


def _capture_lifecycle_state(
    root: Path,
    ordered: Sequence[str],
    *,
    base: str,
) -> LifecycleSnapshot:
    head = _strict_head(root)
    if _git_result(
        root,
        "merge-base",
        "--is-ancestor",
        base,
        head,
    ).returncode:
        raise ValueError("lifecycle base is not HEAD ancestor")
    identities = []
    tracked = set()
    untracked = set()
    for relative in ordered:
        path = Path(relative)
        item = os.lstat(root / path)
        if (
            path.is_absolute()
            or ".." in path.parts
            or not stat.S_ISREG(item.st_mode)
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
        index = _git_result(root, "ls-files", "--stage", "--", relative)
        if index.returncode:
            raise ValueError("lifecycle index query failed")
        if index.stdout:
            mode, _, stage_number = _parse_stage(
                index.stdout,
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
    if staged or unstaged:
        raise ValueError("lifecycle repository staged/dirty")
    if tracked and untracked:
        raise ValueError("mixed tracked/untracked lifecycle")
    if set(listed_untracked) != untracked:
        raise ValueError("entire untracked inventory is not Exact10")
    return LifecycleSnapshot(
        head,
        tuple(identities),
        frozenset(tracked),
        frozenset(untracked),
        listed_untracked,
        staged,
        unstaged,
        results["status"].stdout,
        results["index"].stdout,
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
) -> str:
    root = Path(os.path.abspath(root))
    ordered = tuple(path.as_posix() for path in exact10)
    expected = set(ordered)
    if len(ordered) != 10 or len(expected) != 10:
        raise ValueError("candidate is not Exact10")
    initial = _capture_lifecycle_state(root, ordered, base=base)
    assert_exact10_recursive_inventory(root, exact10, hook=hook)
    final = _capture_lifecycle_state(root, ordered, base=base)
    if final != initial:
        raise ValueError("final HEAD/inventory/index/identity drift")
    if initial.untracked == expected and not initial.tracked:
        return "pre_commit"
    if initial.tracked != expected or initial.untracked:
        raise ValueError("post-commit lifecycle inventory drift")
    _assert_post_commit_history(root, initial.head, expected, base)
    return "post_commit"


def _lifecycle() -> str:
    """Compatibility alias for the hardened lifecycle verifier."""
    return verify_lifecycle()


def _verify_complete_checker_run(
    *,
    after_candidate_validation: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Run both full lifecycle closures around all candidate validation."""
    if (
        sys.implementation.name != "cpython"
        or tuple(sys.version_info[:3]) != (3, 10, 4)
    ):
        raise ValueError("checker requires CPython 3.10.4")
    ordered = tuple(path.as_posix() for path in EXACT10)
    initial = _capture_lifecycle_state(
        ROOT,
        ordered,
        base=BASE_COMMIT,
    )
    initial_lifecycle = verify_lifecycle()
    snapshot = _source_snapshot()
    expected = _local_expected(snapshot)
    observed = read_exact6_no_follow()
    manifest = _verify_observed_artifacts(observed, expected)
    candidate = _load_candidate()
    actual_snapshot = candidate.build_frozen_source_snapshot(ROOT)
    actual = candidate.build_artifacts(actual_snapshot, repo_root=ROOT)
    _verify_observed_artifacts(actual, expected)
    if after_candidate_validation is not None:
        after_candidate_validation()
    prefinal = _capture_lifecycle_state(
        ROOT,
        ordered,
        base=BASE_COMMIT,
    )
    if prefinal != initial:
        raise ValueError(
            "checker prefinal HEAD/inventory/index/identity drift"
        )
    # Deliberately the final Git/filesystem/candidate validation operation.
    final_lifecycle = verify_lifecycle()
    if final_lifecycle != initial_lifecycle:
        raise ValueError("initial/final complete lifecycle result drift")
    report = {
        "all_checks_passed": True,
        "lifecycle": final_lifecycle,
        "exact10_file_count": 10,
        "source_attestation_count": 12,
        "full_recursive_lifecycle_run_count": 2,
        "final_recursive_lifecycle_after_candidate_validation": True,
        "final_recursive_lifecycle_is_last_filesystem_validation": True,
        "permission_scope_count": 4,
        "public_api_contract_row_count": 24,
        "result_contract_row_count": 19,
        "truth_row_count": manifest["truth_matrix"]["row_count"],
        "truth_group_count": manifest["truth_matrix"]["group_count"],
        "safety_row_count": manifest["safety_audit"]["row_count"],
        "precondition_counts": "42/0/3/3",
        "issue_transition_count": 0,
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "stage_owned_staging_namespace_closure": True,
        "embedded_stage_residue_lifecycle_closure": True,
        "ready_for_training": False,
        "manifest_sha256": _sha(observed[MANIFEST_NAME]),
        "recommended_next_step": NEXT_STEP,
    }
    return report


def main() -> int:
    report = _verify_complete_checker_run()
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
