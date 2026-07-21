"""Independent semantic checker for the frozen ADMIT_011 standalone evidence."""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import io
import json
import os
import stat
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1"
DESIGN_STAGE = ROOT / "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1"
DESIGN_TRUTH = DESIGN_STAGE / "covapie_admit_011_raw_target_relative_path_grammar_truth_matrix.csv"
DESIGN_ISSUES = DESIGN_STAGE / "covapie_admit_011_raw_target_issue_readiness_inventory.csv"
FORMAL_RELATIVE_PATH = "src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py"
FORMAL_SOURCE_PATH = ROOT / FORMAL_RELATIVE_PATH
FORMAL_MODULE_NAME = "covalent_ext.covapie_bulk_download_admission_admit_011_rule_logic_interface"
DESIGN_MODULE_NAME = "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate"
DESIGN_TRUTH_RELATIVE_PATH = "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_grammar_truth_matrix.csv"
DESIGN_ISSUES_RELATIVE_PATH = "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_issue_readiness_inventory.csv"
EXPECTED_BASE_COMMIT = "3c53da1e80d04ad68e5d1e9760b5a5bcdb1005b3"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_011 raw target path contract v1"
EXPECTED_STAGE_NAME = "covapie_bulk_download_admission_admit_011_rule_logic_interface_v1"
OUTPUT_FILES = (
    "covapie_admit_011_rule_logic_interface_contract.csv",
    "covapie_admit_011_rule_logic_interface_truth_matrix.csv",
    "covapie_admit_011_rule_logic_interface_source_boundary_audit.csv",
    "covapie_admit_011_rule_logic_interface_purity_audit.csv",
    "covapie_admit_011_rule_logic_interface_issue_readiness_inventory.csv",
    "covapie_admit_011_rule_logic_interface_manifest.json",
)
CONTRACT_FILENAME, TRUTH_FILENAME, SOURCE_FILENAME, PURITY_FILENAME, ISSUE_FILENAME, MANIFEST_FILENAME = OUTPUT_FILES
CONTRACT_COLUMNS = ("field_order", "field", "contract", "passed")
TRUTH_COLUMNS = (
    "case_order", "case_id", "matrix_group", "candidate_representation", "contract_state", "snapshot_state",
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason", "canonical_raw_target_relative_path",
    "validated_candidate_fields", "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
    "expected_precedence", "truth_passed",
)
DESIGN_TRUTH_COLUMNS = (
    "case_order", "case_id", "matrix_group", "candidate_representation", "contract_state", "snapshot_state",
    "outcome", "passed", "blocks_candidate", "reason", "canonical", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used", "expected_precedence", "case_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status", "blocking_scope",
    "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)
PURITY_COLUMNS = ("audit_order", "audit_item", "observed", "passed")
EXACT_RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_raw_target_relative_path", "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used",
)
EXPECTED_CLOSURE = (
    "evaluate_admit_011", "_scalar_reason", "_canonical_path", "_result", "_contract_valid",
    "_snapshot_valid", "Admit011EvaluationResult", "Admit011EvaluationResult.__post_init__",
)
EXPECTED_REACHABLE_HELPERS = "_scalar_reason|_canonical_path|_result|_contract_valid|_snapshot_valid|Admit011EvaluationResult.__post_init__"
FROZEN_OUTPUT_SHA256 = {
    CONTRACT_FILENAME: "7624bfda25b7aca2a3db11fab18a883c52dee0e598a295ada0b0676a1847aea2",
    TRUTH_FILENAME: "974bc68fdd8c6d8c500cce3f70970bd16d18f07d49d7e4162776bd62cd0e064b",
    SOURCE_FILENAME: "096f0016610a428a39aa63c071e145c8f78051a8cf500510057a0712638904b6",
    PURITY_FILENAME: "e4f6df108d51188e87ac0d7d0de9363b82cd22f18f0b2f97a79e0fd448f4a93e",
    ISSUE_FILENAME: "eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0",
    MANIFEST_FILENAME: "a3c053d7b4af149b67b818721f11bb6920b5de00d5d15fb5ec176e10e5a70c3c",
}
FROZEN_SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.py", "c515afab9ac6dc4390d9ef0bf385de4261c612bb1cbe67a19b008c40c288cd7d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_context_responsibility_matrix.csv", "0f3772e65db51623fe7ab477e97cc7fc98166755f39d172ef017a87c7ebfba24"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_contract_source_boundary_audit.csv", "e0747e6b3be3a51d1884a76a85f70b05d34d4f687b20e2604f56783db985840f"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_issue_readiness_inventory.csv", "eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_observed_value_coverage_matrix.csv", "c55c48b58a66b44b2f6f0cc7fde27fe22fa317e3502a7eee9ee06c25006b74a2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_contract_manifest.json", "9718090b212e3338bddef1fb7d6fb62e39d95e1911fe5bdd0ff6613b364e8bf4"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_contract_schema_matrix.csv", "dd5f853c047c7457d110739edf6f2ac3647bc3a9069b2b7a6d15b1470504f13e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_grammar_truth_matrix.csv", "1b32c3cc658433da18b804336afec8c63a275bcf44f68556faf75804e3b386ca"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py", "3649971eec020c5981a3ba8bfddeb604797f8557fb6036efd6094a2b0d6ab4e4"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_010_rule_logic_interface.py", "05a89049fca65b6f9d9480392eb57b333a1960064fbd6c2c5061efeac3bb9a1c"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010.py", "b613321aa1563c7c559208fc08cf82d1e2ccee07cdc6b9c8c338d87b14c78436"),
)
SOURCE_COLUMNS = ("source_order", "source_relative_path", "expected_sha256", "base_tree_sha256", "filesystem_sha256", "git_tracked", "regular", "non_symlink", "source_boundary_passed")
EXPECTED_REASON_VOCABULARY = (
    "", "RAW_TARGET_RELATIVE_PATH_TYPE_INVALID", "RAW_TARGET_RELATIVE_PATH_EMPTY", "RAW_TARGET_RELATIVE_PATH_NON_ASCII_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_NUL_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_CONTROL_CHARACTER_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_WHITESPACE_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_ABSOLUTE_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_WINDOWS_DRIVE_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_UNC_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_URI_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_PERCENT_ENCODING_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_TILDE_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_ENVIRONMENT_EXPANSION_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_BACKSLASH_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_TRAILING_SEPARATOR", "RAW_TARGET_RELATIVE_PATH_REPEATED_SEPARATOR", "RAW_TARGET_RELATIVE_PATH_DOT_COMPONENT_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_DOTDOT_COMPONENT_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_NAMESPACE_FORBIDDEN", "RAW_TARGET_RELATIVE_PATH_CONTRACT_TYPE_INVALID", "RAW_TARGET_RELATIVE_PATH_CONTRACT_VALUE_INVALID", "EXISTING_RAW_TARGET_RELATIVE_PATHS_SNAPSHOT_TYPE_INVALID", "EXISTING_RAW_TARGET_RELATIVE_PATHS_SNAPSHOT_VALUE_INVALID", "RAW_TARGET_CONTEXT_ROOT_IDENTITY_MISMATCH", "RAW_TARGET_CONTEXT_COORDINATE_SYSTEM_MISMATCH", "RAW_TARGET_CONTEXT_GRAMMAR_MISMATCH", "RAW_TARGET_CONTEXT_EQUALITY_POLICY_MISMATCH", "RAW_TARGET_CONTEXT_PHASE_MISMATCH", "RAW_TARGET_RELATIVE_PATH_ALREADY_OCCUPIED",
)
EXPECTED_VALIDATION_PRECEDENCE = ("scalar_type", "scalar_empty", "scalar_ascii", "scalar_nul", "scalar_control", "scalar_whitespace", "scalar_absolute", "scalar_windows_drive", "scalar_unc", "scalar_uri", "scalar_percent", "scalar_tilde", "scalar_environment", "scalar_backslash", "scalar_trailing_separator", "scalar_repeated_separator", "scalar_dot", "scalar_dotdot", "scalar_namespace", "contract_type", "contract_value", "snapshot_type", "snapshot_value", "context_root", "context_coordinate", "context_grammar", "context_equality", "context_phase", "exact_occupied_collision", "passed")
TRUE_READINESS = ("admit_011_rule_logic_implemented", "standalone_evaluator_interface_frozen", "standalone_evaluator_pure_in_memory", "standalone_result_contract_frozen", "design_truth_parity_passed", "ready_for_admit_011_unified_adapter_contract_design", "feature_semantics_audit_required_before_training")
FALSE_READINESS = ("admit_011_adapter_implemented", "admit_011_registered_in_engine", "unified_dispatch_runtime_with_admit_001_to_011_implemented", "provider_mapping_validated", "real_provider_evaluation_ready", "combined_candidate_verdict_implemented", "ready_for_bulk_download_now", "checkpoint_compatibility_validated", "full_repository_canonical_validated", "ready_for_training")
EVALUATOR_CLOSURE_MARKER = "# Everything below this line is deliberately outside the evaluator closure."
EXPECTED_PRODUCTION_SOURCE_SHA256 = "73adad5c617ecae0dc5772d04ae5d777970a3d2a8c8963c3d2c4c4b19cbf85fc"
EXPECTED_EVALUATOR_PREFIX_SHA256 = "dd5ea58fa4d1fa229a596723ae2c1abefe9fa092246097da43f6d012cdc2e251"

# These names are the complete evaluator runtime dependency surface.  They are
# deliberately checker-owned rather than derived from ``formal`` at runtime.
PROTECTED_RUNTIME_BINDINGS = (
    "evaluate_admit_011", "_scalar_reason", "_canonical_path", "_result", "_contract_valid",
    "_snapshot_valid", "Admit011EvaluationResult", "dataclass", "fields", "CANDIDATE_FIELD",
    "COLLISION_REASON", "CONTRACT_FIELDS", "CONTRACT_REASONS", "DEFAULT_CONTRACT",
    "ExistingRawTargetRelativePathsSnapshot", "RawTargetRelativePathContract", "REASON_VOCABULARY",
    "RULE_ID", "SCALAR_REASONS", "SNAPSHOT_FIELDS", "SNAPSHOT_REASONS",
    "STANDALONE_CONTEXT_VALIDATION_ORDER", "VALIDATION_PRECEDENCE", "RESULT_FIELDS",
    "CONSUMED_CANDIDATE_FIELDS", "OUTCOMES",
)
_PROTECTED_RUNTIME_BINDING_SET = frozenset(PROTECTED_RUNTIME_BINDINGS)
EXPECTED_IMPORTED_BINDINGS = {
    "dataclass": "dataclasses.dataclass",
    "fields": "dataclasses.fields",
    "CANDIDATE_FIELD": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.CANDIDATE_FIELD",
    "COLLISION_REASON": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.COLLISION_REASON",
    "CONTRACT_FIELDS": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.CONTRACT_FIELDS",
    "CONTRACT_REASONS": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.CONTRACT_REASONS",
    "DEFAULT_CONTRACT": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.DEFAULT_CONTRACT",
    "ExistingRawTargetRelativePathsSnapshot": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.ExistingRawTargetRelativePathsSnapshot",
    "RawTargetRelativePathContract": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.RawTargetRelativePathContract",
    "REASON_VOCABULARY": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.REASON_VOCABULARY",
    "RULE_ID": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.RULE_ID",
    "SCALAR_REASONS": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.SCALAR_REASONS",
    "SNAPSHOT_FIELDS": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.SNAPSHOT_FIELDS",
    "SNAPSHOT_REASONS": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.SNAPSHOT_REASONS",
    "STANDALONE_CONTEXT_VALIDATION_ORDER": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.STANDALONE_CONTEXT_VALIDATION_ORDER",
    "VALIDATION_PRECEDENCE": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.VALIDATION_PRECEDENCE",
}
EXPECTED_MODULE_CONSTANT_VALUES = {
    "RESULT_FIELDS": EXACT_RESULT_FIELDS,
    "CONSUMED_CANDIDATE_FIELDS": ("raw_target_relative_path",),
    "OUTCOMES": ("passed", "blocked", "invalid"),
}
EXPECTED_REACHABLE_AST_SHA256 = {
    "evaluate_admit_011": "b23150a44438a1296a41c0ad0c2806cc08b4e167d829ed3d4e8a783d861ca59e",
    "_scalar_reason": "be6b4a008af8e335cc0d321860f597441fe1b4b50e6f20ac0deba5292fdd88ff",
    "_canonical_path": "46427404c3a0eded11641945edc9e980976b6593ec13bfc3cfa2d398d03387b1",
    "_result": "8ae372ee4adc70d4377ad5febf5ffbf2f1dbc4cd773978daca606d66399c55ec",
    "_contract_valid": "b6bac83f9673c5283db0c1d2f875ddf6c08396d852d16e15b90f526cd89f71dd",
    "_snapshot_valid": "df429500f4c5f9c30ed6fb9ab1c62fb9df06c15344263870abdeef3054e3fa1f",
    "Admit011EvaluationResult": "ba669a49746cc779b438ac5d5e7a79b70cf248b84c4f50ae82b4dd90c0a83607",
    "Admit011EvaluationResult.__post_init__": "a266f065272035c92a60b8c1d28d00a05d0606b080ebc3ce783663e58ecbee8a",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return (int(item.st_dev), int(item.st_ino), int(item.st_mode))


def _git(arguments: list[str]) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise AssertionError("source attestation git command failed")
    return result.stdout


def _assert_real_parent_chain(parent: Path, anchor: Path) -> None:
    current = parent
    while True:
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise AssertionError("unsafe parent chain")
        if current == anchor:
            break
        if current == current.parent:
            raise AssertionError("parent chain escaped anchor")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise AssertionError("parent resolved identity drift")


def _read_fd(fd: int) -> bytes:
    chunks = []
    while True:
        chunk = os.read(fd, 1 << 16)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


@dataclass(frozen=True)
class SourcePlan:
    relative: str
    path: Path
    identity: tuple[int, int, int]


@dataclass(frozen=True)
class FormalAttestation:
    path: Path
    identity: tuple[int, int, int]
    content: bytes
    text: str
    tree: ast.Module


@dataclass(frozen=True)
class ModuleBundle:
    formal: object
    design: object


@dataclass(frozen=True)
class PinnedOutputTree:
    root: Path
    parent: Path
    anchor: Path
    parent_identity: tuple[int, int, int]
    root_identity: tuple[int, int, int]
    leaf_identities: dict[str, tuple[int, int, int]]
    root_fd: int


def _validate_repository_lineage() -> None:
    item = os.lstat(ROOT)
    if not ROOT.is_absolute() or not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode) or ROOT.resolve(strict=True) != ROOT:
        raise AssertionError("repository identity unsafe")
    if _git(["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT]).decode("utf-8", "strict").rstrip("\n") != EXPECTED_BASE_SUBJECT:
        raise AssertionError("base subject drift")
    _git(["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"])


def _inspect_attested_leaf(path: Path, anchor: Path, *, tracked_relative: str | None = None) -> SourcePlan:
    _assert_real_parent_chain(path.parent, anchor)
    item = os.lstat(path)
    if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode) or path.resolve(strict=True) != path or anchor not in (path, *path.parents):
        raise AssertionError("attested source structure unsafe")
    if tracked_relative is not None:
        if _git(["ls-files", "--error-unmatch", "--", tracked_relative]).decode("utf-8", "strict") != f"{tracked_relative}\n":
            raise AssertionError("attested source tracking drift")
        tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", tracked_relative]).splitlines()
        if len(tree) != 1 or b"\t" not in tree[0]:
            raise AssertionError("attested base tree cardinality drift")
        metadata, tree_path = tree[0].split(b"\t", 1)
        fields = metadata.split()
        if tree_path.decode("utf-8", "strict") != tracked_relative or len(fields) != 3 or fields[1] != b"blob" or fields[0] not in (b"100644", b"100755"):
            raise AssertionError("attested base tree entry drift")
    return SourcePlan(tracked_relative or FORMAL_RELATIVE_PATH, path, _identity(item))


def _read_attested_source(plan: SourcePlan) -> bytes:
    fd = os.open(plan.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if _identity(os.fstat(fd)) != plan.identity or _identity(os.lstat(plan.path)) != plan.identity:
            raise AssertionError("attested source identity changed before read")
        content = _read_fd(fd)
        if _identity(os.fstat(fd)) != plan.identity or _identity(os.lstat(plan.path)) != plan.identity:
            raise AssertionError("attested source identity changed during read")
        return content
    finally:
        os.close(fd)


def _inspect_fixed_source_plans() -> tuple[SourcePlan, ...]:
    if len(FROZEN_SOURCE_BOUNDARY) != 11 or len({path for path, _ in FROZEN_SOURCE_BOUNDARY}) != 11:
        raise AssertionError("fixed source configuration cardinality drift")
    plans = []
    for relative, digest in FROZEN_SOURCE_BOUNDARY:
        parts = relative.split("/")
        if type(relative) is not str or type(digest) is not str or len(digest) != 64 or not relative or relative.startswith("/") or "\\" in relative or any(part in ("", ".", "..") for part in parts) or parts[:2] == ["data", "raw"] or parts[0] == "checkpoints" or relative == FORMAL_RELATIVE_PATH or EXPECTED_STAGE_NAME in parts:
            raise AssertionError("fixed source configuration unsafe")
        plans.append(_inspect_attested_leaf(ROOT / relative, ROOT, tracked_relative=relative))
    return tuple(plans)


def _attest_fixed_sources(plans: tuple[SourcePlan, ...]) -> dict[str, bytes]:
    if tuple(plan.relative for plan in plans) != tuple(path for path, _ in FROZEN_SOURCE_BOUNDARY):
        raise AssertionError("fixed source order drift")
    result = {}
    for plan, (_, expected) in zip(plans, FROZEN_SOURCE_BOUNDARY, strict=True):
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{plan.relative}"])
        current = _read_attested_source(plan)
        if _sha(base) != expected or _sha(current) != expected:
            raise AssertionError("fixed source SHA256 drift")
        result[plan.relative] = current
    return result


def _open_pinned_output_tree(root: Path) -> PinnedOutputTree:
    candidate = Path(root)
    actual = candidate if candidate.is_absolute() else ROOT / candidate
    anchor = Path(actual.anchor) if candidate.is_absolute() else ROOT
    _assert_real_parent_chain(actual.parent, anchor)
    parent_identity = _identity(os.lstat(actual.parent))
    item = os.lstat(actual)
    if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode) or actual.resolve(strict=True) != actual:
        raise AssertionError("output root unsafe")
    if set(os.listdir(actual)) != set(OUTPUT_FILES):
        raise AssertionError("output inventory unsafe")
    root_fd = os.open(actual, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        root_identity = _identity(os.fstat(root_fd))
        if root_identity != _identity(item):
            raise AssertionError("output root identity changed")
        leaves = {}
        for name in OUTPUT_FILES:
            leaf = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if not stat.S_ISREG(leaf.st_mode) or stat.S_ISLNK(leaf.st_mode):
                raise AssertionError("output leaf unsafe")
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=root_fd)
            try:
                if _identity(os.fstat(fd)) != _identity(leaf):
                    raise AssertionError("output leaf identity changed")
            finally:
                os.close(fd)
            leaves[name] = _identity(leaf)
        return PinnedOutputTree(actual, actual.parent, anchor, parent_identity, root_identity, leaves, root_fd)
    except Exception:
        os.close(root_fd)
        raise


def _assert_pinned_output_identity(tree: PinnedOutputTree) -> None:
    _assert_real_parent_chain(tree.parent, tree.anchor)
    if _identity(os.lstat(tree.parent)) != tree.parent_identity or _identity(os.fstat(tree.root_fd)) != tree.root_identity or _identity(os.lstat(tree.root)) != tree.root_identity or tree.root.resolve(strict=True) != tree.root:
        raise AssertionError("pinned output root identity changed")
    if set(os.listdir(tree.root_fd)) != set(OUTPUT_FILES):
        raise AssertionError("pinned output inventory changed")


def _read_pinned_output_bytes(tree: PinnedOutputTree) -> dict[str, bytes]:
    _assert_pinned_output_identity(tree)
    content = {}
    for name in OUTPUT_FILES:
        before = os.stat(name, dir_fd=tree.root_fd, follow_symlinks=False)
        if _identity(before) != tree.leaf_identities[name] or not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
            raise AssertionError("pinned output leaf changed")
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=tree.root_fd)
        try:
            if _identity(os.fstat(fd)) != tree.leaf_identities[name]:
                raise AssertionError("pinned output leaf changed after open")
            content[name] = _read_fd(fd)
            if _identity(os.fstat(fd)) != tree.leaf_identities[name] or _identity(os.stat(name, dir_fd=tree.root_fd, follow_symlinks=False)) != tree.leaf_identities[name]:
                raise AssertionError("pinned output leaf changed during read")
        finally:
            os.close(fd)
    _assert_pinned_output_identity(tree)
    return content


def _name_store_targets(target: ast.AST) -> set[int]:
    return {
        id(item) for item in ast.walk(target)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store)
    }


def _check_module_constant_value(name: str, node: ast.Assign) -> None:
    if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name) or node.targets[0].id != name:
        raise AssertionError(f"protected module constant binding drift: {name}")
    value = node.value
    if name == "CONSUMED_CANDIDATE_FIELDS":
        if not isinstance(value, ast.Tuple) or len(value.elts) != 1 or not isinstance(value.elts[0], ast.Name) or value.elts[0].id != "CANDIDATE_FIELD":
            raise AssertionError("protected module constant AST drift: CONSUMED_CANDIDATE_FIELDS")
        observed = ("raw_target_relative_path",)
    else:
        try:
            observed = ast.literal_eval(value)
        except (ValueError, SyntaxError) as exc:
            raise AssertionError(f"protected module constant is not a literal: {name}") from exc
    if observed != EXPECTED_MODULE_CONSTANT_VALUES[name]:
        raise AssertionError(f"protected module constant value drift: {name}")


def _check_runtime_binding_provenance(tree: ast.Module) -> None:
    """Freeze evaluator globals against rebinding anywhere in the module."""
    local_definition_kinds = {
        "evaluate_admit_011": ast.FunctionDef,
        "_scalar_reason": ast.FunctionDef,
        "_canonical_path": ast.FunctionDef,
        "_result": ast.FunctionDef,
        "_contract_valid": ast.FunctionDef,
        "_snapshot_valid": ast.FunctionDef,
        "Admit011EvaluationResult": ast.ClassDef,
    }
    allowed_definitions: set[int] = set()
    for name, expected_kind in local_definition_kinds.items():
        declarations = [node for node in tree.body if type(node) is expected_kind and node.name == name]
        if len(declarations) != 1:
            raise AssertionError(f"protected local definition count/type drift: {name}")
        allowed_definitions.add(id(declarations[0]))
        all_named = [
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name
        ]
        if len(all_named) != 1 or id(all_named[0]) not in allowed_definitions:
            raise AssertionError(f"protected local definition rebound: {name}")

    import_counts = {name: 0 for name in EXPECTED_IMPORTED_BINDINGS}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                bound = item.asname or item.name.split(".")[0]
                if bound in _PROTECTED_RUNTIME_BINDING_SET:
                    raise AssertionError(f"protected runtime import binding drift: {bound}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for item in node.names:
                bound = item.asname or item.name
                if bound not in _PROTECTED_RUNTIME_BINDING_SET:
                    continue
                expected = EXPECTED_IMPORTED_BINDINGS.get(bound)
                observed = f"{module}.{item.name}".lstrip(".")
                if expected != observed or item.asname is not None or node.level != 0:
                    raise AssertionError(f"protected runtime import provenance drift: {bound}")
                import_counts[bound] += 1
    if import_counts != {name: 1 for name in EXPECTED_IMPORTED_BINDINGS}:
        raise AssertionError("protected runtime import count drift")

    allowed_constant_name_stores: set[int] = set()
    for name in EXPECTED_MODULE_CONSTANT_VALUES:
        declarations = [
            node for node in tree.body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name) and node.targets[0].id == name
        ]
        if len(declarations) != 1:
            raise AssertionError(f"protected module constant count/type drift: {name}")
        _check_module_constant_value(name, declarations[0])
        allowed_constant_name_stores.update(_name_store_targets(declarations[0].targets[0]))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in _PROTECTED_RUNTIME_BINDING_SET and id(node) not in allowed_definitions:
            raise AssertionError(f"protected runtime definition rebinding: {node.name}")
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) and node.id in _PROTECTED_RUNTIME_BINDING_SET:
            if id(node) not in allowed_constant_name_stores:
                raise AssertionError(f"protected runtime assignment/deletion: {node.id}")
        if isinstance(node, ast.ExceptHandler) and node.name in _PROTECTED_RUNTIME_BINDING_SET:
            raise AssertionError(f"protected runtime exception binding: {node.name}")
        if isinstance(node, (ast.Global, ast.Nonlocal)) and any(name in _PROTECTED_RUNTIME_BINDING_SET for name in node.names):
            raise AssertionError("protected runtime global/nonlocal binding")
        if isinstance(node, ast.arg) and node.arg in _PROTECTED_RUNTIME_BINDING_SET:
            raise AssertionError(f"protected runtime argument binding: {node.arg}")
        if isinstance(node, ast.MatchAs) and node.name in _PROTECTED_RUNTIME_BINDING_SET:
            raise AssertionError(f"protected runtime match binding: {node.name}")


def _reachable_ast_nodes(tree: ast.Module) -> dict[str, ast.AST]:
    found: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in EXPECTED_REACHABLE_AST_SHA256:
            found[node.name] = node
        elif isinstance(node, ast.ClassDef) and node.name == "Admit011EvaluationResult":
            found[node.name] = node
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__post_init__":
                    found["Admit011EvaluationResult.__post_init__"] = item
    return {name: found[name] for name in EXPECTED_REACHABLE_AST_SHA256 if name in found}


def _check_reachable_ast_digests(tree: ast.Module) -> None:
    nodes = _reachable_ast_nodes(tree)
    expected_names = tuple(EXPECTED_REACHABLE_AST_SHA256)
    if tuple(nodes) != expected_names:
        raise AssertionError(f"reachable exact AST definition keys drift: {tuple(nodes)}")
    observed = {
        name: _sha(ast.dump(node, annotate_fields=True, include_attributes=False).encode("utf-8"))
        for name, node in nodes.items()
    }
    if tuple(observed) != expected_names or observed != EXPECTED_REACHABLE_AST_SHA256:
        raise AssertionError("reachable exact AST digest drift")


def _check_frozen_production_source(source_text: str, source_bytes: bytes | None = None) -> ast.Module:
    """Validate the formal source bytes plus its runtime dependency provenance."""
    content = source_text.encode("utf-8") if source_bytes is None else source_bytes
    marker = EVALUATOR_CLOSURE_MARKER.encode("utf-8")
    if content.count(marker) != 1:
        raise AssertionError("evaluator closure marker must occur exactly once")
    marker_offset = content.index(marker)
    if _sha(content[:marker_offset]) != EXPECTED_EVALUATOR_PREFIX_SHA256:
        raise AssertionError("evaluator closure prefix SHA256 mismatch")
    if _sha(content) != EXPECTED_PRODUCTION_SOURCE_SHA256:
        raise AssertionError("production source SHA256 mismatch")
    try:
        tree = ast.parse(source_text)
    except SyntaxError as exc:
        raise AssertionError("production source AST is invalid") from exc
    _check_runtime_binding_provenance(tree)
    _check_reachable_ast_digests(tree)
    return tree


def _read_csv(content: bytes, columns: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8", "strict")))
    if tuple(reader.fieldnames or ()) != columns:
        raise AssertionError("exact CSV header mismatch")
    return list(reader)


def _empty_snapshot(bundle: ModuleBundle) -> object:
    design = bundle.design
    return design.ExistingRawTargetRelativePathsSnapshot(
        "covapie_existing_raw_target_relative_paths_snapshot_v1", design.DEFAULT_CONTRACT.canonical_raw_root_identity,
        design.DEFAULT_CONTRACT.candidate_coordinate_system, design.DEFAULT_CONTRACT.path_grammar_version,
        design.DEFAULT_CONTRACT.equality_policy, design.DEFAULT_CONTRACT.snapshot_phase, True, (),
    )


def _unsafe_contract(bundle: ModuleBundle) -> object:
    design = bundle.design
    value = object.__new__(design.RawTargetRelativePathContract)
    for field in design.CONTRACT_FIELDS:
        object.__setattr__(value, field, getattr(design.DEFAULT_CONTRACT, field))
    object.__setattr__(value, "contract_id", "invalid")
    return value


def _unsafe_snapshot(bundle: ModuleBundle, **changes: object) -> object:
    design = bundle.design
    result = object.__new__(design.ExistingRawTargetRelativePathsSnapshot)
    base = _empty_snapshot(bundle)
    for field in design.SNAPSHOT_FIELDS:
        object.__setattr__(result, field, getattr(base, field))
    for field, value in changes.items():
        object.__setattr__(result, field, value)
    return result


def _context(bundle: ModuleBundle, case_id: str) -> tuple[object, object]:
    design = bundle.design
    if case_id in ("CONTRACT_TYPE", "MULTI_CONTRACT_SNAPSHOT"):
        return object(), _empty_snapshot(bundle)
    if case_id == "CONTRACT_VALUE":
        return _unsafe_contract(bundle), _empty_snapshot(bundle)
    if case_id == "SNAPSHOT_TYPE":
        return design.DEFAULT_CONTRACT, object()
    if case_id == "SNAPSHOT_VALUE":
        return design.DEFAULT_CONTRACT, _unsafe_snapshot(bundle, snapshot_complete=False)
    mismatches = {
        "MISMATCH_001": "canonical_raw_root_identity", "MISMATCH_002": "candidate_coordinate_system",
        "MISMATCH_003": "path_grammar_version", "MISMATCH_004": "equality_policy", "MISMATCH_005": "snapshot_phase",
    }
    if case_id in mismatches:
        return design.DEFAULT_CONTRACT, _unsafe_snapshot(bundle, **{mismatches[case_id]: "wrong"})
    if case_id == "COLLISION":
        return design.DEFAULT_CONTRACT, design.ExistingRawTargetRelativePathsSnapshot(
            "covapie_existing_raw_target_relative_paths_snapshot_v1", design.DEFAULT_CONTRACT.canonical_raw_root_identity,
            design.DEFAULT_CONTRACT.candidate_coordinate_system, design.DEFAULT_CONTRACT.path_grammar_version,
            design.DEFAULT_CONTRACT.equality_policy, design.DEFAULT_CONTRACT.snapshot_phase, True, ("data/raw/a.cif",),
        )
    return design.DEFAULT_CONTRACT, _empty_snapshot(bundle)


def _result_projection(value: object) -> dict[str, str]:
    result = asdict(value)
    return {
        "admission_rule_id": str(result["admission_rule_id"]), "outcome": str(result["outcome"]),
        "passed": str(result["passed"]).lower(), "blocks_candidate": str(result["blocks_candidate"]).lower(),
        "reason": str(result["reason"]), "canonical_raw_target_relative_path": str(result["canonical_raw_target_relative_path"]),
        "validated_candidate_fields": json.dumps(result["validated_candidate_fields"], separators=(",", ":")),
        "consumed_candidate_fields": json.dumps(result["consumed_candidate_fields"], separators=(",", ":")),
        "consumed_context_items": json.dumps(result["consumed_context_items"], separators=(",", ":")),
        "evaluator_io_used": str(result["evaluator_io_used"]).lower(),
    }


@dataclass(frozen=True)
class ReachabilityResult:
    reachable_definitions: tuple[str, ...]
    imported_symbols: dict[str, str]
    local_call_graph: dict[str, tuple[str, ...]]


APPROVED_GLOBAL_SYMBOLS = {
    "CANDIDATE_FIELD", "COLLISION_REASON", "CONTRACT_FIELDS", "CONTRACT_REASONS", "DEFAULT_CONTRACT",
    "ExistingRawTargetRelativePathsSnapshot", "RawTargetRelativePathContract", "REASON_VOCABULARY", "RULE_ID",
    "SCALAR_REASONS", "SNAPSHOT_FIELDS", "SNAPSHOT_REASONS", "STANDALONE_CONTEXT_VALIDATION_ORDER",
    "RESULT_FIELDS", "CONSUMED_CANDIDATE_FIELDS", "OUTCOMES", "Admit011EvaluationResult", "_scalar_reason",
    "_canonical_path", "_result", "_contract_valid", "_snapshot_valid", "fields",
}
APPROVED_PURE_BUILTINS = {
    "type", "tuple", "len", "set", "all", "any", "ord", "getattr", "TypeError", "ValueError",
    "object", "str", "bool",
}
APPROVED_ATTRIBUTE_NAMES = {
    *EXACT_RESULT_FIELDS,
    "allowed_namespace_prefixes", "candidate_coordinate_system", "canonical_raw_root_identity", "equality_policy",
    "occupied_relative_paths", "path_grammar_version", "schema_version", "snapshot_complete", "snapshot_phase",
    "name", "isascii", "startswith", "isspace", "split", "isalpha", "endswith",
}
APPROVED_ATTRIBUTE_CALLS = {"isascii", "startswith", "isspace", "split", "isalpha", "endswith"}
REJECTED_DYNAMIC_STRUCTURE_TYPES = (
    ast.Lambda, ast.NamedExpr, ast.Global, ast.Nonlocal, ast.With, ast.AsyncWith, ast.Await, ast.Yield,
    ast.YieldFrom, ast.Import, ast.ImportFrom,
)
_METADATA_HELPER_NAMES = {
    "build_interface_artifacts", "_truth_rows", "_source_rows", "_contract_rows", "_purity_rows",
    "_csv_bytes", "_sha", "run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1",
}


def _dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        return None if base is None else f"{base}.{node.attr}"
    return None


def _module_symbol_maps(tree: ast.Module) -> tuple[dict[str, ast.FunctionDef], dict[str, ast.ClassDef], dict[str, str]]:
    functions: dict[str, ast.FunctionDef] = {}
    classes: dict[str, ast.ClassDef] = {}
    imported: dict[str, str] = {}
    aliases: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = node
        elif isinstance(node, ast.ClassDef):
            classes[node.name] = node
        elif isinstance(node, ast.Import):
            for item in node.names:
                imported[item.asname or item.name.split(".")[0]] = item.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for item in node.names:
                imported[item.asname or item.name] = f"{module}.{item.name}".lstrip(".")
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            dotted = _dotted_name(value) if value is not None else None
            if dotted is not None:
                for target in targets:
                    if isinstance(target, ast.Name):
                        aliases[target.id] = dotted
    changed = True
    while changed:
        changed = False
        for alias, target in tuple(aliases.items()):
            head, *tail = target.split(".")
            if head in imported:
                resolved = ".".join((imported[head], *tail))
                if aliases[alias] != resolved:
                    aliases[alias] = resolved
                    changed = True
            elif head in aliases and aliases[head] != target:
                resolved = ".".join((aliases[head], *tail))
                if aliases[alias] != resolved:
                    aliases[alias] = resolved
                    changed = True
    return functions, classes, {**imported, **aliases}


def _resolve_dotted(name: str | None, imported_symbols: dict[str, str]) -> str | None:
    if name is None:
        return None
    head, *tail = name.split(".")
    if head in imported_symbols:
        return ".".join((imported_symbols[head], *tail))
    return name


def _bound_names(node: ast.AST) -> set[str]:
    """Collect local bindings while excluding nested scopes."""
    bound: set[str] = set()
    if isinstance(node, ast.FunctionDef):
        arguments = node.args
        bound.update(argument.arg for argument in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs))
        if arguments.vararg is not None:
            bound.add(arguments.vararg.arg)
        if arguments.kwarg is not None:
            bound.add(arguments.kwarg.arg)
    for child in ast.walk(node):
        if child is not node and isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        targets: tuple[ast.AST, ...] = ()
        if isinstance(child, ast.Assign):
            targets = child.targets
        elif isinstance(child, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = (child.target,)
        elif isinstance(child, (ast.For, ast.AsyncFor, ast.comprehension)):
            targets = (child.target,)
        elif isinstance(child, ast.ExceptHandler) and child.name is not None:
            bound.add(child.name)
        for target in targets:
            bound.update(item.id for item in ast.walk(target) if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store))
    return bound


def _attribute_root_name(node: ast.Attribute) -> str | None:
    current: ast.AST = node
    while isinstance(current, ast.Attribute):
        current = current.value
    return current.id if isinstance(current, ast.Name) else None


def _assert_class_envelope(node: ast.ClassDef, imported_symbols: dict[str, str]) -> None:
    if node.name != "Admit011EvaluationResult" or node.bases or node.keywords:
        raise AssertionError("reachable class bases or metaclass drift")
    if len(node.decorator_list) != 1 or not isinstance(node.decorator_list[0], ast.Call):
        raise AssertionError("reachable class decorator envelope drift")
    decorator = node.decorator_list[0]
    if not isinstance(decorator.func, ast.Name) or decorator.func.id != "dataclass" or _resolve_dotted("dataclass", imported_symbols) != "dataclasses.dataclass":
        raise AssertionError("reachable class decorator alias drift")
    if decorator.args or len(decorator.keywords) != 1 or decorator.keywords[0].arg != "frozen" or not isinstance(decorator.keywords[0].value, ast.Constant) or decorator.keywords[0].value.value is not True:
        raise AssertionError("reachable dataclass decorator arguments drift")
    field_nodes = [item for item in node.body if isinstance(item, ast.AnnAssign)]
    if len(field_nodes) != 10 or tuple(item.target.id if isinstance(item.target, ast.Name) else "" for item in field_nodes) != EXACT_RESULT_FIELDS:
        raise AssertionError("reachable class field envelope drift")
    if any(item.value is not None or not isinstance(item.annotation, ast.Name) or item.annotation.id != "object" for item in field_nodes):
        raise AssertionError("reachable class field annotation drift")
    methods = [item for item in node.body if isinstance(item, ast.FunctionDef)]
    docstrings = [item for item in node.body if isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and type(item.value.value) is str]
    if len(methods) != 1 or methods[0].name != "__post_init__" or len(node.body) != len(field_nodes) + len(methods) + len(docstrings):
        raise AssertionError("reachable class body envelope drift")


def _assert_closed_world_definition(node: ast.FunctionDef, owner: str, imported_symbols: dict[str, str], local_names: set[str]) -> None:
    if node.decorator_list:
        raise AssertionError("reachable function decorator drift")
    if any(isinstance(child, REJECTED_DYNAMIC_STRUCTURE_TYPES) for child in ast.walk(node) if child is not node):
        raise AssertionError("reachable dynamic AST structure is forbidden")
    if any(isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for child in ast.walk(node) if child is not node):
        raise AssertionError("nested reachable definition is forbidden")
    locals_in_scope = _bound_names(node)
    approved_local_store_ids: set[int] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Assign):
            for target in child.targets:
                approved_local_store_ids.update(_name_store_targets(target))
        elif isinstance(child, (ast.For, ast.AsyncFor, ast.comprehension)):
            approved_local_store_ids.update(_name_store_targets(child.target))
    for child in ast.walk(node):
        if isinstance(child, (ast.Attribute, ast.Subscript)) and isinstance(child.ctx, (ast.Store, ast.Del)):
            raise AssertionError("reachable attribute/subscript mutation is forbidden")
        if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)) and id(child) not in approved_local_store_ids:
            raise AssertionError("reachable local binding/deletion shape is forbidden")
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load) and child.id not in locals_in_scope:
            if child.id not in APPROVED_GLOBAL_SYMBOLS and child.id not in APPROVED_PURE_BUILTINS:
                raise AssertionError(f"unapproved reachable global/imported symbol: {child.id}")
        if isinstance(child, ast.Attribute):
            if child.attr.startswith("__") or child.attr not in APPROVED_ATTRIBUTE_NAMES:
                raise AssertionError(f"unapproved reachable attribute load: {child.attr}")
            root = _attribute_root_name(child)
            if root is not None and root in imported_symbols:
                raise AssertionError(f"module/import attribute load is forbidden: {root}")
        if not isinstance(child, ast.Call):
            continue
        if isinstance(child.func, ast.Name):
            name = child.func.id
            if name in {"setattr", "delattr"}:
                raise AssertionError("reachable reflective mutation is forbidden")
            if name == "getattr":
                if owner not in {"_contract_valid", "_snapshot_valid"} or len(child.args) != 2 or child.keywords or not all(isinstance(argument, ast.Name) for argument in child.args) or tuple(argument.id for argument in child.args) != ("value", "field"):
                    raise AssertionError("reachable getattr shape is not frozen")
            elif name not in APPROVED_PURE_BUILTINS and name not in local_names and name != "fields":
                raise AssertionError(f"unapproved reachable callable: {name}")
            if name in _METADATA_HELPER_NAMES:
                raise AssertionError(f"metadata helper is evaluator-reachable: {name}")
        elif isinstance(child.func, ast.Attribute):
            if child.func.attr not in APPROVED_ATTRIBUTE_CALLS:
                raise AssertionError(f"unapproved reachable attribute callable: {child.func.attr}")
        else:
            raise AssertionError("dynamic reachable callable shape is forbidden")


def _analyze_evaluator_reachable_closure(source_text: str) -> ReachabilityResult:
    """Discover and purity-check the true transitive local closure from the public evaluator."""
    try:
        tree = ast.parse(source_text)
    except SyntaxError as exc:
        raise AssertionError("production source AST is invalid") from exc
    functions, classes, imported_symbols = _module_symbol_maps(tree)
    if "evaluate_admit_011" not in functions:
        raise AssertionError("public evaluator definition is absent")
    class_methods = {
        name: {item.name: item for item in node.body if isinstance(item, ast.FunctionDef)}
        for name, node in classes.items()
    }
    local_names = set(functions) | set(classes)
    visited: set[str] = set()
    queue = ["evaluate_admit_011"]
    call_graph: dict[str, tuple[str, ...]] = {}
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        if "." in current:
            class_name, method_name = current.split(".", 1)
            node = class_methods.get(class_name, {}).get(method_name)
            if node is None:
                raise AssertionError(f"reachable class method missing: {current}")
        elif current in functions:
            node = functions[current]
        elif current in classes:
            _assert_class_envelope(classes[current], imported_symbols)
            visited.add(current)
            method = class_methods.get(current, {}).get("__post_init__")
            call_graph[current] = (() if method is None else (f"{current}.__post_init__",))
            if method is not None:
                queue.append(f"{current}.__post_init__")
            continue
        else:
            raise AssertionError(f"reachable local definition missing: {current}")
        _assert_closed_world_definition(node, current, imported_symbols, local_names)
        discovered: list[str] = []
        for child in ast.walk(node):
            if not isinstance(child, ast.Call) or not isinstance(child.func, ast.Name):
                continue
            name = child.func.id
            if name in functions or name in classes:
                discovered.append(name)
        call_graph[current] = tuple(dict.fromkeys(discovered))
        visited.add(current)
        for name in discovered:
            if name not in visited:
                queue.append(name)
    ordered = tuple(name for name in EXPECTED_CLOSURE if name in visited) + tuple(sorted(visited - set(EXPECTED_CLOSURE)))
    return ReachabilityResult(ordered, imported_symbols, call_graph)


def _computed_reachable_helpers(result: ReachabilityResult) -> str:
    return "|".join(name for name in result.reachable_definitions if name != "evaluate_admit_011" and name != "Admit011EvaluationResult")


def _check_ast_closure(source_text: str | None = None) -> ReachabilityResult:
    text = FORMAL_SOURCE_PATH.read_text(encoding="utf-8") if source_text is None else source_text
    result = _analyze_evaluator_reachable_closure(text)
    if result.reachable_definitions != EXPECTED_CLOSURE:
        raise AssertionError(f"transitive evaluator closure drift: {result.reachable_definitions}")
    return result


def _expected_contract_rows() -> list[dict[str, str]]:
    return [
        {"field_order": str(index), "field": field, "contract": "Exact10 formal result field order", "passed": "true"}
        for index, field in enumerate(EXACT_RESULT_FIELDS, 1)
    ]


def _check_contract(content: dict[str, bytes]) -> None:
    rows = _read_csv(content[CONTRACT_FILENAME], CONTRACT_COLUMNS)
    if rows != _expected_contract_rows():
        raise AssertionError("Exact10 contract CSV semantic tamper")


def _expected_truth_rows(design_truth: bytes) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    design_rows = _read_csv(design_truth, DESIGN_TRUTH_COLUMNS)
    if len(design_rows) != 84 or [row["case_order"] for row in design_rows] != [str(index) for index in range(1, 85)]:
        raise AssertionError("committed design Exact84 order drift")
    if len({row["case_id"] for row in design_rows}) != 84 or sum(row["matrix_group"] == "historical_observed" for row in design_rows) != 47:
        raise AssertionError("committed design Exact84 identity drift")
    if set(row["matrix_group"] for row in design_rows) != {"historical_observed", "scalar_reason", "contract_reason", "snapshot_reason", "cross_context_mismatch", "collision", "passed", "multi_invalid"}:
        raise AssertionError("committed design matrix-group drift")
    if set(row["contract_state"] for row in design_rows) != {"valid_contract", "type_invalid", "value_invalid"}:
        raise AssertionError("committed design contract-state drift")
    if set(row["snapshot_state"] for row in design_rows) != {"valid_snapshot", "not_consumed", "type_invalid", "value_invalid", "canonical_raw_root_identity", "candidate_coordinate_system", "path_grammar_version", "equality_policy", "snapshot_phase", "occupied", "empty"}:
        raise AssertionError("committed design snapshot-state drift")
    expected = []
    for row in design_rows:
        expected.append({
            "case_order": row["case_order"], "case_id": row["case_id"], "matrix_group": row["matrix_group"],
            "candidate_representation": row["candidate_representation"], "contract_state": row["contract_state"], "snapshot_state": row["snapshot_state"],
            "admission_rule_id": "ADMIT_011", "outcome": row["outcome"], "passed": row["passed"],
            "blocks_candidate": row["blocks_candidate"], "reason": row["reason"],
            "canonical_raw_target_relative_path": row["canonical"], "validated_candidate_fields": row["validated_candidate_fields"],
            "consumed_candidate_fields": row["consumed_candidate_fields"], "consumed_context_items": row["consumed_context_items"],
            "evaluator_io_used": row["evaluator_io_used"], "expected_precedence": row["expected_precedence"], "truth_passed": "true",
        })
    return expected, design_rows


def _check_truth(content: dict[str, bytes], sources: dict[str, bytes], bundle: ModuleBundle) -> None:
    actual_rows = _read_csv(content[TRUTH_FILENAME], TRUTH_COLUMNS)
    expected_rows, design_rows = _expected_truth_rows(sources[DESIGN_TRUTH_RELATIVE_PATH])
    for row in actual_rows:
        try:
            ast.literal_eval(row["candidate_representation"])
        except (ValueError, SyntaxError) as exc:
            raise AssertionError("candidate representation is not a literal") from exc
    if actual_rows != expected_rows:
        raise AssertionError("Exact84 truth CSV semantic tamper")
    for expected, design in zip(expected_rows, design_rows, strict=True):
        try:
            candidate = ast.literal_eval(design["candidate_representation"])
        except (ValueError, SyntaxError) as exc:
            raise AssertionError("candidate representation is not a literal") from exc
        contract, snapshot = _context(bundle, design["case_id"])
        runtime = _result_projection(bundle.formal.evaluate_admit_011(candidate, snapshot, contract))
        if runtime != {field: expected[field] for field in EXACT_RESULT_FIELDS}:
            raise AssertionError(f"runtime result differs from checker-owned expected: {design['case_id']}")


def _check_issues(content: dict[str, bytes], sources: dict[str, bytes]) -> None:
    actual_bytes = content[ISSUE_FILENAME]
    expected_bytes = sources[DESIGN_ISSUES_RELATIVE_PATH]
    actual_rows = _read_csv(actual_bytes, ISSUE_COLUMNS)
    expected_rows = _read_csv(expected_bytes, ISSUE_COLUMNS)
    if actual_bytes != expected_bytes or actual_rows != expected_rows or len(actual_rows) != 11:
        raise AssertionError("Exact11 issue inventory semantic tamper")
    issues = {row["issue_id"]: row for row in actual_rows}
    if issues["RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED"]["status"] != "resolved":
        raise AssertionError("ADMIT_011 raw target issue must remain resolved")
    coverage = issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    if coverage["status"] != "open" or coverage["affected_rules"] != "ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015":
        raise AssertionError("unified admission coverage issue drift")


def _check_purity(content: dict[str, bytes], closure: ReachabilityResult, bundle: ModuleBundle) -> None:
    rows = _read_csv(content[PURITY_FILENAME], PURITY_COLUMNS)
    expected = [
        {"audit_order": "1", "audit_item": "public_evaluator", "observed": "evaluate_admit_011", "passed": "true"},
        {"audit_order": "2", "audit_item": "reachable_helpers", "observed": _computed_reachable_helpers(closure), "passed": "true"},
        {"audit_order": "3", "audit_item": "forbidden_reachable_symbols", "observed": "Path|os|subprocess|open|classify_admit_011_raw_target_relative_path_design absent", "passed": "true"},
        {"audit_order": "4", "audit_item": "evaluator_io_used", "observed": "false", "passed": "true"},
    ]
    if _computed_reachable_helpers(closure) != EXPECTED_REACHABLE_HELPERS or rows != expected:
        raise AssertionError("computed AST purity evidence tamper")
    if bundle.formal.evaluate_admit_011("data/raw/a.cif", _empty_snapshot(bundle), bundle.design.DEFAULT_CONTRACT).evaluator_io_used is not False:
        raise AssertionError("evaluator I/O attestation mismatch")


def _expected_source_rows() -> list[dict[str, str]]:
    return [
        {"source_order": str(index), "source_relative_path": path, "expected_sha256": digest,
         "base_tree_sha256": digest, "filesystem_sha256": digest, "git_tracked": "true", "regular": "true",
         "non_symlink": "true", "source_boundary_passed": "true"}
        for index, (path, digest) in enumerate(FROZEN_SOURCE_BOUNDARY, 1)
    ]


def _check_sources(content: dict[str, bytes]) -> None:
    if _read_csv(content[SOURCE_FILENAME], SOURCE_COLUMNS) != _expected_source_rows():
        raise AssertionError("Exact11 source boundary semantic tamper")


def _check_manifest(content: dict[str, bytes]) -> None:
    manifest = json.loads(content[MANIFEST_FILENAME])
    readiness = {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}
    fixed = {
        "manifest_schema_version": "covapie_admit_011_rule_logic_interface_manifest_v1", "stage": EXPECTED_STAGE_NAME,
        "base_commit": EXPECTED_BASE_COMMIT, "base_subject": EXPECTED_BASE_SUBJECT, "admission_rule_id": "ADMIT_011",
        "admission_rule_name": "raw_overwrite_forbidden", "public_api": "evaluate_admit_011(raw_target_relative_path, existing_raw_target_relative_paths, raw_target_relative_path_contract)",
        "public_signature_parameters": ["raw_target_relative_path", "existing_raw_target_relative_paths", "raw_target_relative_path_contract"],
        "result_type": "Admit011EvaluationResult", "result_fields": list(EXACT_RESULT_FIELDS),
        "source_paths": [path for path, _ in FROZEN_SOURCE_BOUNDARY], "source_input_count": 11,
        "output_files": list(OUTPUT_FILES), "output_file_count": 6,
        "row_counts": {"contract": 10, "truth": 84, "truth_historical": 47, "source_boundary": 11, "purity": 4, "issue": 11},
        "reason_vocabulary": list(EXPECTED_REASON_VOCABULARY), "validation_precedence": list(EXPECTED_VALIDATION_PRECEDENCE),
        "readiness": readiness, **readiness, "feature_semantics_audit_required_before_training": True,
        "step12d_is_final_training_feature_contract": False, "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": "design_covapie_admit_011_unified_adapter_contract_v1",
        "safety": {"filesystem_used_by_evaluator": False, "network_used_by_evaluator": False, "raw_read_by_evaluator": False, "mutation_by_evaluator": False},
        "all_checks_passed": True,
    }
    if {key: manifest.get(key) for key in fixed} != fixed or tuple(manifest.get("readiness", {})) != (*TRUE_READINESS, *FALSE_READINESS) or tuple(manifest.get("row_counts", {})) != ("contract", "truth", "truth_historical", "source_boundary", "purity", "issue") or tuple(manifest.get("safety", {})) != ("filesystem_used_by_evaluator", "network_used_by_evaluator", "raw_read_by_evaluator", "mutation_by_evaluator"):
        raise AssertionError("manifest exact-value tamper")
    expected_hashes = {name: _sha(content[name]) for name in OUTPUT_FILES[:-1]}
    if tuple(manifest.get("output_sha256", {})) != OUTPUT_FILES[:-1] or manifest.get("output_sha256") != expected_hashes:
        raise AssertionError("manifest output hash tamper")
    expected_keys = (
        "manifest_schema_version", "stage", "base_commit", "base_subject", "admission_rule_id", "admission_rule_name",
        "public_api", "public_signature_parameters", "result_type", "result_fields", "source_paths", "source_input_count",
        "output_files", "output_file_count", "row_counts", "reason_vocabulary", "validation_precedence", "readiness",
        *TRUE_READINESS, *FALSE_READINESS, "step12d_is_final_training_feature_contract", "step12d_status",
        "recommended_next_step", "safety", "output_sha256", "all_checks_passed",
    )
    if tuple(manifest) != expected_keys:
        raise AssertionError("manifest key/order tamper")


def _default_lazy_importer(_attestation: FormalAttestation) -> ModuleBundle:
    source_root = str(ROOT / "src")
    if source_root not in sys.path:
        sys.path.insert(0, source_root)
    importlib.invalidate_caches()
    return ModuleBundle(importlib.import_module(FORMAL_MODULE_NAME), importlib.import_module(DESIGN_MODULE_NAME))


def _verify_imported_modules(bundle: ModuleBundle, formal_attestation: FormalAttestation) -> None:
    try:
        formal_path = Path(bundle.formal.__file__).resolve(strict=True)
        formal_identity = _identity(os.lstat(bundle.formal.__file__))
        design_path = Path(bundle.design.__file__).resolve(strict=True)
    except (AttributeError, OSError) as exc:
        raise AssertionError("imported module path identity drift") from exc
    if formal_path != formal_attestation.path or formal_identity != formal_attestation.identity:
        raise AssertionError("imported formal module path identity drift")
    expected_design_path = ROOT / FROZEN_SOURCE_BOUNDARY[0][0]
    if design_path != expected_design_path:
        raise AssertionError("imported design module path identity drift")
    import dataclasses
    if bundle.formal.dataclass is not dataclasses.dataclass or bundle.formal.fields is not dataclasses.fields:
        raise AssertionError("runtime dataclass binding drift")
    for name, dotted in EXPECTED_IMPORTED_BINDINGS.items():
        if name in {"dataclass", "fields"}:
            continue
        if getattr(bundle.formal, name) is not getattr(bundle.design, name):
            raise AssertionError(f"runtime imported binding drift: {dotted}")
    for name, expected in EXPECTED_MODULE_CONSTANT_VALUES.items():
        if getattr(bundle.formal, name) != expected:
            raise AssertionError(f"runtime module constant drift: {name}")
    for name in ("evaluate_admit_011", "_scalar_reason", "_canonical_path", "_result", "_contract_valid", "_snapshot_valid"):
        value = getattr(bundle.formal, name)
        if not callable(value) or Path(value.__code__.co_filename).resolve(strict=True) != formal_attestation.path:
            raise AssertionError(f"runtime local binding drift: {name}")
    if getattr(bundle.formal, "Admit011EvaluationResult").__module__ != FORMAL_MODULE_NAME:
        raise AssertionError("runtime result-class binding drift")


def validate_output_tree(root: Path = STAGE, *, enforce_frozen_hashes: bool = True, lazy_importer: object | None = None) -> None:
    pinned = _open_pinned_output_tree(root)
    try:
        _validate_repository_lineage()
        formal_plan = _inspect_attested_leaf(FORMAL_SOURCE_PATH, ROOT)
        fixed_plans = _inspect_fixed_source_plans()
        source_bytes = _read_attested_source(formal_plan)
        try:
            source_text = source_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AssertionError("production source is not UTF-8") from exc
        source_tree = _check_frozen_production_source(source_text, source_bytes)
        fixed_sources = _attest_fixed_sources(fixed_plans)
        closure = _check_ast_closure(source_text)
        attestation = FormalAttestation(formal_plan.path, formal_plan.identity, source_bytes, source_text, source_tree)
        bundle = (lazy_importer or _default_lazy_importer)(attestation)
        _verify_imported_modules(bundle, attestation)
        content = _read_pinned_output_bytes(pinned)
        _check_contract(content)
        _check_truth(content, fixed_sources, bundle)
        _check_issues(content, fixed_sources)
        _check_purity(content, closure, bundle)
        _check_sources(content)
        _check_manifest(content)
        if enforce_frozen_hashes and {name: _sha(content[name]) for name in OUTPUT_FILES} != FROZEN_OUTPUT_SHA256:
            raise AssertionError("frozen output SHA256 mismatch")
    finally:
        os.close(pinned.root_fd)


def main() -> int:
    validate_output_tree()
    print(json.dumps({"checked": True, "stage": EXPECTED_STAGE_NAME}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
