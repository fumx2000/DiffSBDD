#!/usr/bin/env python3
"""Independent checker for the CovaPIE combined-permission design contract."""

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
from pathlib import Path
from typing import Any, NamedTuple


BASE_COMMIT = "bb282ef24343baebc05212715a8c7d56bc8224ad"
BASE_PARENT = "1e076d90439e75ec9f797ed4890f8fd6594dc9fa"
BASE_TREE = "57203816d33c18ea8466633376367a2a25b9418d"
BASE_SUBJECT = (
    "add CovaPIE ADMIT_015 mandatory training authorization enforcement v1"
)
STAGE = (
    "covapie_bulk_download_admission_combined_permission_"
    "semantics_contract_v1"
)
NEXT_STEP = (
    "design_covapie_combined_candidate_verdict_and_cross_rule_"
    "aggregation_contract_v1"
)
REVISED2_REVISION = (
    "revise_covapie_combined_permission_semantics_contract_"
    "final_lifecycle_closure_v2"
)
ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_PATH = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_combined_permission_semantics_"
    "contract_design_gate.py"
)
CHECKER_PATH = Path(
    "scripts/"
    "check_covapie_bulk_download_admission_combined_permission_"
    "semantics_contract_v1.py"
)
TEST_PATH = Path(
    "tests/"
    "test_covapie_bulk_download_admission_combined_permission_"
    "semantics_contract_v1.py"
)
SUMMARY_PATH = Path(
    "docs/"
    "covapie_bulk_download_admission_combined_permission_semantics_"
    "contract_v1_summary.md"
)
DERIVED_ROOT = Path("data/derived/covalent_small") / STAGE
MEMBERSHIP_NAME = (
    "covapie_combined_permission_scope_and_rule_membership_contract.csv"
)
PRECEDENCE_NAME = (
    "covapie_combined_permission_precedence_and_non_override_contract.csv"
)
TRUTH_NAME = "covapie_combined_permission_truth_matrix.csv"
SAFETY_NAME = "covapie_combined_permission_safety_audit.csv"
ISSUE_NAME = "covapie_combined_permission_issue_readiness_inventory.csv"
MANIFEST_NAME = (
    "covapie_combined_permission_semantics_contract_manifest.json"
)
OUTPUT_NAMES = (
    MEMBERSHIP_NAME,
    PRECEDENCE_NAME,
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
INVALID_REASON = (
    "COMBINED_PERMISSION_SCOPE_OR_VECTOR_OR_STATE_CONTRACT_INVALID"
)
BLOCKED_REASON = "COMBINED_PERMISSION_REQUIRED_RULE_BLOCKED"

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
    if len(SOURCE_BOUNDARY) != 11:
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


def _reason(scope: str, rule: str, included: bool) -> str:
    if included:
        if rule == "ADMIT_014":
            return "required stage download authorization; necessary not sufficient"
        if rule == "ADMIT_015":
            return "required only for training admission; necessary not sufficient"
        return "required admission rule for this phase-scoped permission"
    if rule == "ADMIT_010":
        if scope == SCOPE_IDS[0]:
            return "excluded: pre_final_split is not a download prerequisite"
        return "excluded: scope has not entered pre_final_split"
    if rule in {"ADMIT_012", "ADMIT_013"}:
        return "excluded: post_download evidence is unavailable before download"
    if rule == "ADMIT_015":
        return "excluded: training permission is phase-isolated"
    return "excluded by exact phase-scoped membership"


def _membership_rows() -> list[dict[str, str]]:
    rows = []
    for scope_order, (scope, name, required) in enumerate(SCOPES, 1):
        positions = {rule: index for index, rule in enumerate(required, 1)}
        for rule in RULE_IDS:
            included = rule in positions
            rows.append(
                {
                    "scope_order": str(scope_order),
                    "scope_id": scope,
                    "scope_semantic_name": name,
                    "required_rule_order": (
                        str(positions[rule]) if included else ""
                    ),
                    "admission_rule_id": rule,
                    "registry_evaluation_phase": PHASES[rule],
                    "included": str(included).lower(),
                    "exclusion_or_inclusion_reason": _reason(
                        scope, rule, included
                    ),
                    "contract_passed": "true",
                }
            )
    return rows


def _precedence_rows() -> list[dict[str, str]]:
    values = (
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
        for order, (group, item, value) in enumerate(values, 1)
    ]


def _pass(scope: str) -> tuple[tuple[str, str], ...]:
    return tuple((rule, "passed") for rule in REQUIRED[scope])


def _replace(
    vector: tuple[tuple[str, Any], ...], index: int, state: Any
) -> tuple[tuple[str, Any], ...]:
    return tuple(
        (rule, state if position == index else value)
        for position, (rule, value) in enumerate(vector)
    )


def _simulate(scope: Any, vector: Any) -> tuple[str, bool, bool, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if type(scope) is not str or scope not in REQUIRED:
        return "invalid", False, True, INVALID_REASON, (), (), ()
    required = REQUIRED[scope]
    if type(vector) is not tuple:
        return "invalid", False, True, INVALID_REASON, required, (), ()
    ids, states = [], []
    for item in vector:
        if (
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not str
        ):
            return (
                "invalid",
                False,
                True,
                INVALID_REASON,
                required,
                tuple(ids),
                (),
            )
        ids.append(item[0])
        states.append(item[1])
    observed = tuple(ids)
    if (
        len(observed) != len(set(observed))
        or observed != required
        or any(state not in {"passed", "blocked", "invalid"} for state in states)
    ):
        return "invalid", False, True, INVALID_REASON, required, observed, ()
    failing = tuple(
        rule for rule, state in vector if state != "passed"
    )
    if "invalid" in states:
        return "invalid", False, True, INVALID_REASON, required, observed, failing
    if "blocked" in states:
        return "blocked", False, True, BLOCKED_REASON, required, observed, failing
    return "passed", True, False, "", required, observed, ()


def _truth_cases() -> list[tuple[str, str, Any, Any, str]]:
    cases = []
    for scope in SCOPE_IDS:
        canonical = _pass(scope)
        cases.append((f"{scope}__all_pass", "canonical_all_pass", scope, canonical, "passed"))
        for index, (rule, _) in enumerate(canonical):
            cases.append((f"{scope}__{rule}__blocked", "every_required_rule_blocked", scope, _replace(canonical, index, "blocked"), "blocked"))
            cases.append((f"{scope}__{rule}__invalid", "every_required_rule_invalid", scope, _replace(canonical, index, "invalid"), "invalid"))
        for label, index in (("first", 0), ("middle", len(canonical) // 2), ("last", len(canonical) - 1)):
            cases.append((f"{scope}__missing_{label}", "missing_required", scope, canonical[:index] + canonical[index + 1 :], "invalid"))
        cases.append((f"{scope}__duplicate", "duplicate_rule_id", scope, canonical + (canonical[0],), "invalid"))
        cases.append((f"{scope}__reorder", "reordered_rule_ids", scope, (canonical[1], canonical[0]) + canonical[2:], "invalid"))
        extra = {
            SCOPE_IDS[0]: "ADMIT_010",
            SCOPE_IDS[1]: "ADMIT_010",
            SCOPE_IDS[2]: "ADMIT_015",
            SCOPE_IDS[3]: "ADMIT_999",
        }[scope]
        cases.append((f"{scope}__extra", "extra_rule_id", scope, canonical + ((extra, "passed"),), "invalid"))
        mixed = _replace(_replace(canonical, 0, "blocked"), 1, "invalid")
        cases.append((f"{scope}__invalid_over_blocked", "invalid_blocked_precedence", scope, mixed, "invalid"))
        cases.append((f"{scope}__admit014_non_override", "admit014_pass_non_override", scope, _replace(canonical, 0, "blocked"), "blocked"))
    cases.extend(
        (
            ("unknown_scope", "unknown_scope", "unknown_permission_scope", (), "invalid"),
            ("unknown_state", "unknown_state", SCOPE_IDS[0], _replace(_pass(SCOPE_IDS[0]), 0, "PASSED"), "invalid"),
            ("bool_state", "bool_state", SCOPE_IDS[0], _replace(_pass(SCOPE_IDS[0]), 0, True), "invalid"),
            ("scope_bool", "wrong_top_level_type", True, (), "invalid"),
            ("scope_none", "wrong_top_level_type", None, (), "invalid"),
            ("vector_list", "wrong_top_level_type", SCOPE_IDS[0], list(_pass(SCOPE_IDS[0])), "invalid"),
            ("vector_dict", "wrong_top_level_type", SCOPE_IDS[0], {}, "invalid"),
            ("vector_string", "wrong_top_level_type", SCOPE_IDS[0], "passed", "invalid"),
            ("vector_none", "wrong_top_level_type", SCOPE_IDS[0], None, "invalid"),
            ("admit014_only", "necessary_not_sufficient", SCOPE_IDS[0], (("ADMIT_014", "passed"),), "invalid"),
            ("admit015_only", "necessary_not_sufficient", SCOPE_IDS[3], (("ADMIT_015", "passed"),), "invalid"),
            ("admit015_pass_non_override", "admit015_pass_non_override", SCOPE_IDS[3], _replace(_pass(SCOPE_IDS[3]), 0, "blocked"), "blocked"),
        )
    )
    for case_id, scope, extra in (
        ("download_extra_admit010", SCOPE_IDS[0], "ADMIT_010"),
        ("download_extra_admit012", SCOPE_IDS[0], "ADMIT_012"),
        ("download_extra_admit013", SCOPE_IDS[0], "ADMIT_013"),
        ("post_extra_admit010", SCOPE_IDS[1], "ADMIT_010"),
        ("download_extra_admit015", SCOPE_IDS[0], "ADMIT_015"),
        ("post_extra_admit015", SCOPE_IDS[1], "ADMIT_015"),
        ("prefinal_extra_admit015", SCOPE_IDS[2], "ADMIT_015"),
    ):
        cases.append((case_id, "phase_isolation", scope, _pass(scope) + ((extra, "passed"),), "invalid"))
    download = _pass(SCOPE_IDS[0])
    index = tuple(item[0] for item in download).index("ADMIT_014")
    cases.append(("download_missing_admit014", "phase_isolation", SCOPE_IDS[0], download[:index] + download[index + 1 :], "invalid"))
    cases.append(("synthetic_pass_no_mutation", "synthetic_pass_no_mutation", SCOPE_IDS[3], _pass(SCOPE_IDS[3]), "passed"))
    return cases


def _representation(value: Any) -> str:
    if type(value) is str:
        return value
    if value is None:
        return "None"
    if type(value) is bool:
        return str(value)
    return type(value).__name__


def _truth_rows() -> list[dict[str, str]]:
    rows = []
    for order, (case_id, group, scope, vector, expected) in enumerate(_truth_cases(), 1):
        outcome, passed, blocked, reason, required, _observed, failing = _simulate(scope, vector)
        pairs = vector if type(vector) is tuple and all(type(item) is tuple and len(item) == 2 for item in vector) else ()
        ids = tuple(item[0] for item in pairs if type(item[0]) is str)
        states = tuple(item[1] if type(item[1]) is str else f"<{type(item[1]).__name__}>" for item in pairs)
        expected_passed = expected == "passed"
        expected_reason = {"passed": "", "blocked": BLOCKED_REASON, "invalid": INVALID_REASON}[expected]
        case_passed = (
            outcome == expected
            and passed is expected_passed
            and blocked is (not expected_passed)
            and reason == expected_reason
        )
        rows.append(
            {
                "case_order": str(order),
                "case_id": case_id,
                "case_group": group,
                "scope_id_representation": _representation(scope),
                "vector_type": type(vector).__name__,
                "observed_rule_ids": "|".join(ids),
                "observed_states": "|".join(states),
                "expected_outcome": expected,
                "observed_outcome": outcome,
                "expected_passed": str(expected_passed).lower(),
                "observed_passed": str(passed).lower(),
                "expected_blocks_action": str(not expected_passed).lower(),
                "observed_blocks_action": str(blocked).lower(),
                "expected_reason": expected_reason,
                "observed_reason": reason,
                "required_rule_ids": "|".join(required),
                "failing_rule_ids": "|".join(failing),
                "design_io_used": "false",
                "current_permission": "false",
                "authorized_execution_count": "0",
                "case_passed": str(case_passed).lower(),
            }
        )
    return rows


def _safety_rows() -> list[dict[str, str]]:
    names = (
        "runtime_dispatcher_calls",
        "network",
        "provider",
        "download",
        "raw",
        "torch_import",
        "dataloader",
        "checkpoint",
        "model",
        "forward",
        "loss",
        "backward",
        "optimizer",
        "scheduler",
        "parameter_update",
        "checkpoint_write",
        "training_result",
        "current_permission",
        "authorized_execution_count",
        "combined_candidate_verdict_implemented",
        "cross_rule_aggregation_implemented",
        "training_orchestrator_integration_implemented",
        "feature_semantics_audit_completed",
        "historical_unknown_atom_feature_policy_resolved",
        "historical_feature_semantics_known",
        "real_training_ready",
        "ready_for_training",
        "exact15_single_rule_runtime_modified",
        "admit015_mandatory_guard_modified",
        "actual_permission_mutation",
    )
    rows = []
    for order, name in enumerate(names, 1):
        expected = "0" if name in {"runtime_dispatcher_calls", "authorized_execution_count"} else "false"
        rows.append(
            {
                "audit_order": str(order),
                "audit_item": name,
                "expected_state": expected,
                "observed_state": expected,
                "safety_passed": "true",
            }
        )
    return rows


def _issue_rows(source: bytes) -> list[dict[str, str]]:
    rows = _csv(source, ISSUE_COLUMNS)
    result = []
    target = "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
    for row in rows:
        value = dict(row)
        if row["issue_id"] == target:
            value.update(
                {
                    "successor_effective_status": "resolved",
                    "successor_transition_stage": STAGE,
                    "successor_transition_action": "resolved_by_phase_scoped_combined_permission_semantics_contract",
                    "successor_transition_evidence": (
                        "Exact4 phase-scoped permission memberships; invalid>"
                        "blocked>passed monotone conjunction; ADMIT_014/015 "
                        "non-override frozen; aggregation remains unimplemented"
                    ),
                }
            )
        result.append(value)
    if len(rows) != 30 or sum(a != b for a, b in zip(rows, result, strict=True)) != 1:
        raise ValueError("issue transition drift")
    return result


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
    registry_columns = tuple(
        next(csv.reader(io.StringIO(snapshot[0]["_content"].decode())))
    )
    registry = _csv(snapshot[0]["_content"], registry_columns)
    if (
        len(registry) != 15
        or tuple(row["admission_rule_id"] for row in registry) != RULE_IDS
        or tuple((row["admission_rule_id"], row["evaluation_phase"]) for row in registry) != RULE_PHASES
    ):
        raise ValueError("registry semantic drift")
    membership = _membership_rows()
    precedence = _precedence_rows()
    truth = _truth_rows()
    safety = _safety_rows()
    issues = _issue_rows(snapshot[-1]["_content"])
    payloads = {
        MEMBERSHIP_NAME: _csv_bytes(MEMBERSHIP_COLUMNS, membership),
        PRECEDENCE_NAME: _csv_bytes(PRECEDENCE_COLUMNS, precedence),
        TRUTH_NAME: _csv_bytes(TRUTH_COLUMNS, truth),
        SAFETY_NAME: _csv_bytes(SAFETY_COLUMNS, safety),
        ISSUE_NAME: _csv_bytes(ISSUE_COLUMNS, issues),
    }
    support = {
        path.as_posix(): _sha(_read(path))
        for path in (PRODUCTION_PATH, CHECKER_PATH, TEST_PATH, SUMMARY_PATH)
    }
    group_counts = dict(sorted(Counter(row["case_group"] for row in truth).items()))
    manifest = {
        "project": "CovaPIE",
        "step": "combined permission semantics contract v1",
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
        "source_boundary": [
            {key: value for key, value in item.items() if key != "_content"}
            for item in snapshot
        ],
        "source_boundary_count": 11,
        "registry_phase_sha256": SOURCE_BOUNDARY[0][1],
        "exact15_rule_order": list(RULE_IDS),
        "registry_evaluation_phases": [
            {"admission_rule_id": rule, "evaluation_phase": phase}
            for rule, phase in RULE_PHASES
        ],
        "permission_scopes": [
            {
                "scope_order": order,
                "scope_id": scope,
                "scope_semantic_name": name,
                "required_rule_count": len(required),
                "required_rule_ids": list(required),
                "membership_sha256": _sha(("\n".join(required) + "\n").encode()),
            }
            for order, (scope, name, required) in enumerate(SCOPES, 1)
        ],
        "permission_scope_count": 4,
        "state_vocabulary": ["passed", "blocked", "invalid"],
        "outcome_vocabulary": ["passed", "blocked", "invalid"],
        "fail_closed_precedence": ["invalid", "blocked", "passed"],
        "precedence_semantics": "deterministic_failure_priority_only",
        "combination_semantics": "monotone_conjunction_all_required_pass",
        "pass_reason": "",
        "blocked_reason": BLOCKED_REASON,
        "invalid_reason": INVALID_REASON,
        "admit_014_necessary_not_sufficient": True,
        "admit_015_necessary_not_sufficient": True,
        "blocked_invalid_non_override_frozen": True,
        "phase_isolation_frozen": True,
        "truth_matrix": {
            "columns": list(TRUTH_COLUMNS),
            "row_count": len(truth),
            "group_count": len(group_counts),
            "group_counts": group_counts,
            "generated_by_pure_memory_design_simulator": True,
        },
        "safety_audit": {
            "columns": list(SAFETY_COLUMNS),
            "row_count": len(safety),
        },
        "issue_transition": {
            "row_count": 30,
            "transition_count": 1,
            "transition_issue_id": "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
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
            "remaining_open_precondition_ids": ["PRE_036", "PRE_038", "PRE_042"],
        },
        "readiness": {
            "mandatory_training_authorization_enforcement_implemented": True,
            "combined_permission_semantics_frozen": True,
            "phase_scoped_permission_membership_frozen": True,
            "combined_permission_precedence_frozen": True,
            "combined_permission_non_override_frozen": True,
            "ready_for_combined_candidate_verdict_and_cross_rule_aggregation_contract_design": True,
            "feature_semantics_audit_required_before_training": True,
            "combined_candidate_verdict_implemented": False,
            "cross_rule_aggregation_contract_frozen": False,
            "cross_rule_aggregation_implemented": False,
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
        "covapie_combined_permission_candidate", ROOT / PRODUCTION_PATH
    )
    if spec is None or spec.loader is None:
        raise ValueError("candidate import spec failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _matches_stage_family(name: str) -> bool:
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
            matched = observe_all or _matches_stage_family(name)
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
            if not name.startswith(STAGE):
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
        "source_attestation_count": 11,
        "full_recursive_lifecycle_run_count": 2,
        "final_recursive_lifecycle_after_candidate_validation": True,
        "final_recursive_lifecycle_is_last_filesystem_validation": True,
        "permission_scope_count": 4,
        "truth_row_count": manifest["truth_matrix"]["row_count"],
        "truth_group_count": manifest["truth_matrix"]["group_count"],
        "safety_row_count": manifest["safety_audit"]["row_count"],
        "precondition_counts": "42/0/3/3",
        "issue_transition_count": 1,
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
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
