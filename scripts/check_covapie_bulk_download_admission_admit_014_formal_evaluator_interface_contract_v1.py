#!/usr/bin/env python3
"""Independent checker for the ADMIT_014 formal-interface Exact10."""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import inspect
import io
import json
import os
import stat
import subprocess
import sys
from collections.abc import Iterator, Mapping
from dataclasses import fields
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE = "d56140d8558208ee34eb5a43773010a2dc69169b"
PARENT = "30bbfaba4df0843d1f028e695d3dc499079a9b36"
TREE = "3dbdc1a9723d30e05a1f856cc02ac60af5a25120"
SUBJECT = "add CovaPIE ADMIT_014 download authorization contract v1"
STAGE = (
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
CONTRACT = (
    "covapie_admit_014_formal_evaluator_interface_and_result_contract.csv"
)
ROUTING = (
    "covapie_admit_014_formal_evaluator_routing_and_consumption_contract.csv"
)
TRUTH = "covapie_admit_014_formal_evaluator_interface_truth_matrix.csv"
SOURCE = (
    "covapie_admit_014_formal_evaluator_interface_source_boundary_audit.csv"
)
ISSUE = (
    "covapie_admit_014_formal_evaluator_interface_issue_readiness_inventory.csv"
)
MANIFEST = (
    "covapie_admit_014_formal_evaluator_interface_contract_manifest.json"
)
FILES = (CONTRACT, ROUTING, TRUTH, SOURCE, ISSUE, MANIFEST)

PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_design_gate.py"
)
CHECKER = Path(
    "scripts/"
    "check_covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_v1.py"
)
TEST = Path(
    "tests/"
    "test_covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_v1.py"
)
DOC = Path(
    "docs/"
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_v1_summary.md"
)
EXACT10 = (
    PRODUCTION,
    CHECKER,
    TEST,
    DOC,
    *(OUTPUT_ROOT / name for name in FILES),
)

PRODUCTION_SHA256 = (
    "af25eb2f2fb84230b29d2204fff05308626e7f455a7b950aa8efb922607c298e"
)
OUTPUT_SHA256 = {
    CONTRACT: "7baea79ce0010e31efcf2e70f11350ee5fc05a5c358df3926f9df591da3d3524",
    ROUTING: "9df1faddeb8aa14e8b29af10296222925361cd1f1f98c05a2cc3a2cc64c7f769",
    TRUTH: "55dbbddf1f3bcdb4bbd6ce763d7a0c812020241157098c6af18799cc5ffac062",
    SOURCE: "43c399551ee861014fffdb50b1acdf56bd08374781fb6e6170d3af5f832651be",
    ISSUE: "d2510c9d2cf7ee1a1fc378e639eb69b68612e818f4e7af10a0e36dc0d788f54d",
    MANIFEST: "217490ef69526486b51117e4900d0669b4de466a023023ecb56ebdf0822fb731",
}
FUTURE_SIGNATURE = (
    "evaluate_admit_014(*, stage_authorization_context: object = _MISSING) "
    "-> Admit014EvaluationResult"
)
TARGET_KEY = "current_stage_download_authorized"
ADMIT015_KEY = "current_stage_training_authorized"
RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_stage_authorization_record",
    "validated_stage_authorization_fields",
    "consumed_stage_authorization_fields",
    "evaluator_io_used",
)
RESULT_TYPES = (
    "str",
    "str",
    "bool",
    "bool",
    "str",
    "tuple",
    "tuple",
    "tuple",
    "bool",
)
REASONS = (
    "",
    "STAGE_AUTHORIZATION_CONTEXT_REQUIRED",
    "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID",
    "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING",
    "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
    "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID",
    "BULK_DOWNLOAD_NOT_AUTHORIZED",
)
SIGNATURE_CASE_IDS = (
    "SIGNATURE_EXACT_STRING",
    "SIGNATURE_ONE_KEYWORD_ONLY",
    "SIGNATURE_PRIVATE_MISSING",
    "SIGNATURE_RETURN_ANNOTATION",
    "SIGNATURE_NO_VARARGS",
    "SIGNATURE_NO_VARKW",
    "SIGNATURE_POSITIONAL_REJECTED",
    "SIGNATURE_UNKNOWN_KEYWORD_REJECTED",
)
NON_SIGNATURE_TRUTH_SHA256 = (
    "70b88800b54de6538252de9ec8618cc8379dfccd4016c6f036d57634cff152da"
)

AUTH_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_"
    "download_authorization_contract_v1"
)
PRE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_"
    "rule_logic_interface_preconditions_audit_v1"
)
AUA_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_"
    "implementation_precondition_gate_v1"
)
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1"
)
SOURCES = (
    (
        Path(
            "src/covalent_ext/"
            "covapie_bulk_download_admission_admit_014_"
            "download_authorization_contract_design_gate.py"
        ),
        "b2616c01234c899695c08280daacfa21cb137b847a01f5bf6e52e807b0770434",
    ),
    (
        AUTH_ROOT
        / "covapie_admit_014_download_authorization_value_and_trust_contract.csv",
        "b22f02efdd53dce995730a05cc5c12ffa659c2d98b345afc663b118cc104752d",
    ),
    (
        AUTH_ROOT
        / "covapie_admit_014_stage_authorization_routing_and_enforcement_contract.csv",
        "68bc56b214f212ffec359049146e371ac7ce48bed34bfd6bb80313a2fd7046a6",
    ),
    (
        AUTH_ROOT / "covapie_admit_014_failure_taxonomy_and_precedence.csv",
        "1970da57fdec24e9c5b6e518e1dfa7c2103d3bef6da065b24e3d61a296cdeffc",
    ),
    (
        AUTH_ROOT
        / "covapie_admit_014_download_authorization_truth_matrix.csv",
        "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482",
    ),
    (
        AUTH_ROOT / "covapie_admit_014_issue_readiness_inventory.csv",
        "10e3475cb329d517c27fae26636294d0aa69a609a3c59a8b7f0119b0b123edbe",
    ),
    (
        AUTH_ROOT
        / "covapie_admit_014_download_authorization_contract_manifest.json",
        "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
    ),
    (
        PRE_ROOT / "covapie_admit_014_formal_evaluator_precondition_matrix.csv",
        "6b52a4e96dd960e7df53b7160f5cd00d63fbeb62ee5bc5ec9882623efd268c30",
    ),
    (
        AUA_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv",
        "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    ),
    (
        Path(
            "src/covalent_ext/"
            "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013.py"
        ),
        "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892",
    ),
    (
        RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_manifest.json",
        "2940e6cc02a92b4919cdece3b1fa7c2f5e27d844f2962bb18757197266c23f79",
    ),
)

CONTRACT_HEADER = (
    "contract_order",
    "contract_group",
    "contract_item",
    "future_public_name",
    "exact_contract",
    "exact_type_or_value",
    "contract_passed",
)
ROUTING_HEADER = (
    "routing_order",
    "routing_case",
    "input_state",
    "lookup_attempted",
    "canonical_record",
    "validated_fields",
    "consumed_fields",
    "expected_outcome",
    "expected_reason",
    "routing_passed",
)
TRUTH_HEADER = (
    "case_order",
    "case_id",
    "case_group",
    "invocation_form",
    "stage_context_representation",
    "expected_outcome",
    "observed_outcome",
    "expected_reason",
    "observed_reason",
    "expected_canonical_record",
    "observed_canonical_record",
    "expected_validated_fields",
    "observed_validated_fields",
    "expected_consumed_fields",
    "observed_consumed_fields",
    "result_contract_passed",
    "case_passed",
)
SOURCE_HEADER = (
    "source_order",
    "source_relative_path",
    "expected_sha256",
    "base_tree_mode",
    "tracked",
    "index_stage_zero",
    "base_tree_blob",
    "filesystem_regular",
    "non_symlink",
    "parent_chain_non_symlink",
    "safe_descendant",
    "pinned_fd_read",
    "post_read_identity_verified",
    "source_verified",
)

TRANSITIONS = {
    "ADMIT_014_STANDALONE_SIGNATURE_UNRESOLVED": (
        "future one-keyword-only signature with private missing singleton frozen"
    ),
    "ADMIT_014_RESULT_CONTRACT_UNRESOLVED": (
        "future Exact9 result fields types canonical validated consumed "
        "representations and invariants frozen"
    ),
}
GLOBAL_OPEN = (
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
    "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
    "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
)
TRUE_KEYS = (
    "admit_014_preconditions_audited",
    "admit_014_download_authorization_contract_designed",
    "admit_014_formal_evaluator_interface_contract_frozen",
    "admit_014_standalone_signature_frozen",
    "admit_014_formal_result_contract_frozen",
    "admit_014_result_representation_frozen",
    "admit_014_stage_authorization_routing_resolved",
    "admit_014_exact_bool_value_contract_frozen",
    "admit_014_permission_transition_and_precedence_resolved",
    "admit_014_reason_vocabulary_frozen",
    "admit_014_mandatory_pre_download_enforcement_contract_frozen",
    "admit_014_future_evaluator_pure_in_memory_possible",
    "ready_for_admit_014_standalone_evaluator_interface_implementation",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_KEYS = (
    "evaluate_admit_014_implemented",
    "Admit014EvaluationResult_implemented",
    "admit_014_rule_logic_implemented",
    "admit_014_unified_adapter_contract_frozen",
    "admit_014_unified_adapter_implemented",
    "admit_014_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_014_implemented",
    "mandatory_pre_download_authorization_enforcement_implemented",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


def _guard() -> None:
    if (
        sys.implementation.name != "cpython"
        or tuple(sys.version_info[:3]) != (3, 10, 4)
    ):
        raise RuntimeError("independent checker requires canonical CPython 3.10.4")


def _git(
    args: list[str], repo_root: Path = REPO_ROOT
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


Identity = tuple[int, int, int, int, int, int]


def _identity(item: os.stat_result) -> Identity:
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )


def _safe(path: Path) -> bool:
    return (
        not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[:2] != ("data", "raw")
        and path.parts[0] != "checkpoints"
        and OUTPUT_ROOT.as_posix() not in path.as_posix()
    )


def _pinned_relative(path: Path, repo_root: Path = REPO_ROOT) -> bytes:
    if not _safe(path):
        raise ValueError(f"unsafe source path: {path}")
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    leaf_flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    root_lexical = os.lstat(repo_root)
    if (
        stat.S_ISLNK(root_lexical.st_mode)
        or not stat.S_ISDIR(root_lexical.st_mode)
    ):
        raise ValueError("unsafe repository root")
    root_identity = _identity(root_lexical)
    descriptors: list[tuple[int, Identity, int | None, str | None]] = []
    root_fd = os.open(repo_root, directory_flags)
    if _identity(os.fstat(root_fd)) != root_identity:
        os.close(root_fd)
        raise ValueError("repository root stat/open race")
    descriptors.append((root_fd, root_identity, None, None))
    try:
        parent_fd = root_fd
        for part in path.parts[:-1]:
            lexical = os.stat(part, dir_fd=parent_fd, follow_symlinks=False)
            expected = _identity(lexical)
            if stat.S_ISLNK(lexical.st_mode) or not stat.S_ISDIR(
                lexical.st_mode
            ):
                raise ValueError("unsafe source parent")
            child_fd = os.open(part, directory_flags, dir_fd=parent_fd)
            if _identity(os.fstat(child_fd)) != expected:
                os.close(child_fd)
                raise ValueError("source parent stat/open race")
            descriptors.append((child_fd, expected, parent_fd, part))
            parent_fd = child_fd
        before = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        expected_leaf = _identity(before)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise ValueError("unsafe source leaf")
        leaf_fd = os.open(path.name, leaf_flags, dir_fd=parent_fd)
        try:
            if _identity(os.fstat(leaf_fd)) != expected_leaf:
                raise ValueError("source stat/open race")
            chunks = []
            while True:
                chunk = os.read(leaf_fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            if _identity(os.fstat(leaf_fd)) != expected_leaf:
                raise ValueError("source FD identity drift")
        finally:
            os.close(leaf_fd)
        if (
            _identity(
                os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != expected_leaf
        ):
            raise ValueError("source lexical replacement")
        for descriptor, expected, lexical_parent, lexical_name in descriptors:
            if _identity(os.fstat(descriptor)) != expected:
                raise ValueError("source parent FD identity drift")
            if lexical_parent is not None and lexical_name is not None:
                if (
                    _identity(
                        os.stat(
                            lexical_name,
                            dir_fd=lexical_parent,
                            follow_symlinks=False,
                        )
                    )
                    != expected
                ):
                    raise ValueError("source parent lexical replacement")
        if _identity(os.lstat(repo_root)) != root_identity:
            raise ValueError("repository root identity drift")
        return b"".join(chunks)
    finally:
        for descriptor, _, _, _ in reversed(descriptors):
            os.close(descriptor)


def _source_snapshot() -> dict[Path, bytes]:
    identity = _git(["show", "-s", "--format=%H%n%P%n%T%n%s", BASE])
    ancestor = _git(["merge-base", "--is-ancestor", BASE, "HEAD"])
    if identity.returncode or ancestor.returncode:
        raise ValueError("base identity/ancestry failure")
    if identity.stdout.splitlines() != [BASE, PARENT, TREE, SUBJECT]:
        raise ValueError("base identity mismatch")
    records = {}
    if len(SOURCES) != 11 or len(set(path for path, _ in SOURCES)) != 11:
        raise ValueError("source boundary not Exact11")
    for path, digest in SOURCES:
        index = _git(["ls-files", "--stage", "--", path.as_posix()])
        tree = _git(["ls-tree", BASE, "--", path.as_posix()])
        index_head, index_sep, index_path = index.stdout.partition("\t")
        tree_head, tree_sep, tree_path = tree.stdout.partition("\t")
        index_fields = index_head.split()
        tree_fields = tree_head.split()
        if (
            index.returncode
            or tree.returncode
            or not index_sep
            or not tree_sep
            or index_path.strip() != path.as_posix()
            or tree_path.strip() != path.as_posix()
            or len(index_fields) != 3
            or len(tree_fields) != 3
            or index_fields[2] != "0"
            or index_fields[0] != tree_fields[0]
            or index_fields[1] != tree_fields[2]
            or tree_fields[1] != "blob"
        ):
            raise ValueError(f"source index/base mode/blob drift: {path}")
        current = _pinned_relative(path)
        base = subprocess.run(
            ["git", "show", f"{BASE}:{path.as_posix()}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if (
            hashlib.sha256(current).hexdigest() != digest
            or base.returncode
            or base.stdout != current
        ):
            raise ValueError(f"source SHA/base mismatch: {path}")
        records[path] = current
    return records


def _pinned_outputs(root: Path) -> dict[str, bytes]:
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    leaf_flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    parent = root.parent
    parent_identity = _identity(os.lstat(parent))
    parent_fd = os.open(parent, directory_flags)
    root_fd = -1
    leaves: list[tuple[str, int, Identity, bytes]] = []
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("output parent stat/open race")
        root_lexical = os.stat(
            root.name, dir_fd=parent_fd, follow_symlinks=False
        )
        if (
            stat.S_ISLNK(root_lexical.st_mode)
            or not stat.S_ISDIR(root_lexical.st_mode)
        ):
            raise ValueError("unsafe output root")
        root_identity = _identity(root_lexical)
        root_fd = os.open(root.name, directory_flags, dir_fd=parent_fd)
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root stat/open race")
        if set(os.listdir(root_fd)) != set(FILES):
            raise ValueError("missing or extra Exact6 output")
        for name in FILES:
            before = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                stat.S_ISLNK(before.st_mode)
                or not stat.S_ISREG(before.st_mode)
                or before.st_size > 100 * 1024 * 1024
            ):
                raise ValueError("unsafe output leaf")
            expected = _identity(before)
            descriptor = os.open(name, leaf_flags, dir_fd=root_fd)
            if _identity(os.fstat(descriptor)) != expected:
                os.close(descriptor)
                raise ValueError("output stat/open race")
            chunks = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            leaves.append((name, descriptor, expected, b"".join(chunks)))
        if set(os.listdir(root_fd)) != set(FILES):
            raise ValueError("output inventory drift after traversal")
        outputs = {}
        for name, descriptor, expected, data in leaves:
            if (
                _identity(os.fstat(descriptor)) != expected
                or _identity(
                    os.stat(name, dir_fd=root_fd, follow_symlinks=False)
                )
                != expected
            ):
                raise ValueError("output leaf identity drift after traversal")
            outputs[name] = data
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(
                os.stat(
                    root.name, dir_fd=parent_fd, follow_symlinks=False
                )
            )
            != root_identity
            or _identity(os.fstat(parent_fd)) != parent_identity
            or _identity(os.lstat(parent)) != parent_identity
        ):
            raise ValueError("output parent/root identity drift")
        return outputs
    finally:
        for _, descriptor, _, _ in leaves:
            os.close(descriptor)
        if root_fd >= 0:
            os.close(root_fd)
        os.close(parent_fd)


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _parse_manifest_exact(data: bytes) -> dict[str, Any]:
    manifest = json.loads(data, object_pairs_hook=_pairs_no_duplicates)
    expected = (
        "project",
        "stage",
        "manifest_schema_version",
        "base_commit",
        "base_parent",
        "base_tree",
        "base_subject",
        "canonical_evidence_python_implementation",
        "canonical_evidence_python_version",
        "ast_attestation_cross_python_version_portable",
        "noncanonical_python_policy",
        "python_runtime_migration_policy",
        "admission_rule_id",
        "future_function_name",
        "future_result_type_name",
        "future_public_signature",
        "signature_parameters",
        "signature_parameter_count",
        "signature_all_keyword_only",
        "signature_parameter_annotation",
        "signature_private_missing_singleton_default",
        "signature_varargs",
        "signature_varkw",
        "signature_forbidden_parameters",
        "formal_evaluator_implemented",
        "formal_result_type_defined",
        "design_oracle",
        "design_result_type",
        "result_fields",
        "result_field_count",
        "result_field_exact_types",
        "result_dataclass_frozen",
        "result_subclassing_forbidden",
        "canonical_stage_authorization_record_representation",
        "validated_stage_authorization_fields_representation",
        "consumed_stage_authorization_fields_representation",
        "outcome_vocabulary",
        "reason_vocabulary",
        "failure_precedence",
        "result_invariants",
        "projection_contract",
        "mapping_consumption_contract",
        "truth_matrix_schema",
        "truth_matrix_row_count",
        "truth_matrix_positive_row_count",
        "truth_matrix_negative_result_row_count",
        "truth_matrix_group_counts",
        "truth_matrix_signature_meta_semantics",
        "truth_matrix_all_cases_passed",
        "precondition_transition",
        "issue_transition",
        "remaining_open_issue_ids",
        "current_permission",
        "synthetic_true_design_case_grants_current_permission",
        "mandatory_pre_download_authorization_enforcement_contract",
        "unified_adapter_contract_frozen",
        "unified_adapter_implemented",
        "admit_014_registered_in_engine",
        "unified_dispatch_runtime_with_admit_001_to_014_implemented",
        "source_count",
        "source_boundary",
        "source_validation_before_candidate_and_output_read",
        "readiness",
        "safety",
        "output_file_count",
        "output_files",
        "output_sha256",
        "output_sha256_excludes_manifest_self_hash",
        "renameat2_policy",
        "step12d_status",
        "feature_semantics_note",
        "recommended_next_step",
        "all_checks_passed",
        *TRUE_KEYS,
        *(
            key
            for key in FALSE_KEYS
            if key
            not in {
                "admit_014_registered_in_engine",
                "unified_dispatch_runtime_with_admit_001_to_014_implemented",
            }
        ),
    )
    if tuple(manifest) != expected:
        raise ValueError("manifest missing/extra/reordered keys")
    return manifest


def _rows(data: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(data.decode(), newline=""))
    if (
        not reader.fieldnames
        or len(reader.fieldnames) != len(set(reader.fieldnames))
    ):
        raise ValueError("CSV duplicate/empty header")
    return list(reader)


class Probe(Mapping[str, object]):
    def __init__(
        self,
        values: dict[str, object] | None = None,
        *,
        error: BaseException | None = None,
    ) -> None:
        self.values = {} if values is None else values
        self.error = error
        self.item_keys: list[str] = []
        self.iteration = 0
        self.length = 0
        self.gets = 0
        self.contains = 0

    def __getitem__(self, key: str) -> object:
        self.item_keys.append(key)
        if self.error is not None:
            raise self.error
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        self.iteration += 1
        raise AssertionError("iteration forbidden")

    def __len__(self) -> int:
        self.length += 1
        raise AssertionError("len forbidden")

    def get(self, key: str, default: object = None) -> object:
        self.gets += 1
        raise AssertionError("get forbidden")

    def __contains__(self, key: object) -> bool:
        self.contains += 1
        raise AssertionError("contains forbidden")


def _validate_ast_and_load() -> Any:
    content = _pinned_relative(PRODUCTION)
    if hashlib.sha256(content).hexdigest() != PRODUCTION_SHA256:
        raise ValueError("candidate production SHA mismatch")
    tree = ast.parse(content)
    forbidden = {
        "evaluate_admit_014",
        "Admit014EvaluationResult",
        "_evaluate_registered_admit_014",
        "EVALUATOR_REGISTRY",
        "evaluate_admission_rule",
    }
    definitions = {
        node.name
        for node in ast.walk(tree)
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        )
    }
    assignments = {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    if forbidden & (definitions | assignments):
        raise ValueError("production contains forbidden formal/runtime symbol")
    if b"os.replace" in content:
        raise ValueError("forbidden os.replace fallback")
    spec = importlib.util.spec_from_file_location(
        "admit014_formal_design_isolated", REPO_ROOT / PRODUCTION
    )
    if spec is None or spec.loader is None:
        raise ValueError("isolated production import unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _validate_signature_and_oracle(module: Any) -> None:
    signature = module.FORMAL_SIGNATURE_DESIGN
    if not isinstance(signature, inspect.Signature):
        raise ValueError("formal signature Design is not inspect.Signature")
    parameters = tuple(signature.parameters.values())
    if (
        module.FUTURE_PUBLIC_SIGNATURE != FUTURE_SIGNATURE
        or len(parameters) != 1
        or parameters[0].name != "stage_authorization_context"
        or parameters[0].kind is not inspect.Parameter.KEYWORD_ONLY
        or parameters[0].annotation is not object
        or parameters[0].default is not module._DESIGN_MISSING
        or parameters[0].default is None
        or signature.return_annotation != "Admit014EvaluationResult"
        or any(
            parameter.kind is inspect.Parameter.VAR_POSITIONAL
            for parameter in parameters
        )
        or any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD
            for parameter in parameters
        )
    ):
        raise ValueError("future signature drift")
    try:
        signature.bind(object())
    except TypeError:
        pass
    else:
        raise ValueError("positional invocation accepted")
    try:
        signature.bind(unknown=True)
    except TypeError:
        pass
    else:
        raise ValueError("unknown keyword accepted")
    if (
        tuple(field.name for field in fields(
            module.Admit014EvaluationResultContractDesign
        ))
        != RESULT_FIELDS
    ):
        raise ValueError("Exact9 result fields drift")

    field = (TARGET_KEY,)
    cases = (
        ({}, "blocked", REASONS[1], (), (), ()),
        (
            {"stage_authorization_context": None},
            "blocked",
            REASONS[1],
            (),
            (),
            (),
        ),
        (
            {"stage_authorization_context": object()},
            "blocked",
            REASONS[2],
            (),
            (),
            (),
        ),
        (
            {"stage_authorization_context": Probe()},
            "blocked",
            REASONS[3],
            (),
            (),
            field,
        ),
        (
            {
                "stage_authorization_context": Probe(
                    error=RuntimeError("boom")
                )
            },
            "blocked",
            REASONS[4],
            (),
            (),
            field,
        ),
        (
            {"stage_authorization_context": Probe({TARGET_KEY: 1})},
            "blocked",
            REASONS[5],
            (),
            (),
            field,
        ),
        (
            {"stage_authorization_context": Probe({TARGET_KEY: False})},
            "blocked",
            REASONS[6],
            ((TARGET_KEY, False),),
            field,
            field,
        ),
        (
            {
                "stage_authorization_context": Probe(
                    {ADMIT015_KEY: False, TARGET_KEY: True}
                )
            },
            "passed",
            "",
            ((TARGET_KEY, True),),
            field,
            field,
        ),
    )
    classify = module.classify_admit_014_formal_evaluator_interface_design
    for kwargs, outcome, reason, canonical, validated, consumed in cases:
        result = classify(**kwargs)
        if (
            result.outcome != outcome
            or result.reason != reason
            or result.passed is not (outcome == "passed")
            or result.blocks_candidate is not (outcome == "blocked")
            or result.canonical_stage_authorization_record != canonical
            or result.validated_stage_authorization_fields != validated
            or result.consumed_stage_authorization_fields != consumed
            or result.evaluator_io_used is not False
            or module.validate_admit_014_evaluation_result_contract_design(
                result
            )
            is not True
        ):
            raise ValueError("independent Design oracle mismatch")
        probe = kwargs.get("stage_authorization_context")
        if isinstance(probe, Probe):
            if (
                probe.item_keys != [TARGET_KEY]
                or probe.iteration
                or probe.length
                or probe.gets
                or probe.contains
            ):
                raise ValueError("target-only Mapping access drift")
    try:
        classify(object())
    except TypeError:
        pass
    else:
        raise ValueError("oracle positional call accepted")
    try:
        classify(unknown=True)
    except TypeError:
        pass
    else:
        raise ValueError("oracle unknown keyword accepted")
    base = classify(stage_authorization_context={TARGET_KEY: True})
    mutations = (
        {"admission_rule_id": "ADMIT_015"},
        {"outcome": "invalid"},
        {"passed": 1},
        {"blocks_candidate": 0},
        {"reason": REASONS[6]},
        {"canonical_stage_authorization_record": [(TARGET_KEY, True)]},
        {"canonical_stage_authorization_record": ((ADMIT015_KEY, True),)},
        {"canonical_stage_authorization_record": ((TARGET_KEY, "true"),)},
        {"validated_stage_authorization_fields": [TARGET_KEY]},
        {"validated_stage_authorization_fields": (ADMIT015_KEY,)},
        {"consumed_stage_authorization_fields": [TARGET_KEY]},
        {"consumed_stage_authorization_fields": ()},
        {"evaluator_io_used": True},
    )
    for mutation in mutations:
        values = {name: getattr(base, name) for name in RESULT_FIELDS}
        values.update(mutation)
        try:
            module.Admit014EvaluationResultContractDesign(
                *(values[name] for name in RESULT_FIELDS)
            )
        except (TypeError, ValueError):
            continue
        raise ValueError(f"negative result contract accepted: {mutation}")


def _lifecycle(
    repo_root: Path = REPO_ROOT,
    base: str = BASE,
    exact10: tuple[Path, ...] = EXACT10,
) -> str:
    if _git(
        ["merge-base", "--is-ancestor", base, "HEAD"], repo_root
    ).returncode:
        raise ValueError("base nonancestor")
    if len(exact10) != 10 or len(set(exact10)) != 10:
        raise ValueError("Exact10 path contract drift")
    forbidden_suffixes = {
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
    states = []
    for path in exact10:
        target = repo_root / path
        if (
            not target.exists()
            or target.is_symlink()
            or target.stat().st_size > 100 * 1024 * 1024
        ):
            raise ValueError(f"unsafe candidate: {path}")
        if path.suffix in forbidden_suffixes:
            raise ValueError("forbidden candidate suffix")
        ignored = _git(
            ["check-ignore", "--no-index", "-q", "--", path.as_posix()],
            repo_root,
        )
        if ignored.returncode == 0:
            raise ValueError(f"ignored candidate: {path}")
        if ignored.returncode != 1:
            raise ValueError("candidate ignore check failed")
        tracked = _git(
            ["ls-files", "--error-unmatch", "--", path.as_posix()],
            repo_root,
        )
        untracked = _git(
            [
                "ls-files",
                "--others",
                "--exclude-standard",
                "--",
                path.as_posix(),
            ],
            repo_root,
        )
        staged = _git(
            ["diff", "--cached", "--name-only", "--", path.as_posix()],
            repo_root,
        )
        working = _git(
            ["diff", "--name-only", "--", path.as_posix()], repo_root
        )
        if staged.stdout.strip():
            raise ValueError(f"stage path is staged: {path}")
        if tracked.returncode == 0:
            if untracked.stdout.strip() or working.stdout.strip():
                raise ValueError(f"dirty post-commit candidate: {path}")
            states.append("post_commit")
        else:
            if (
                untracked.stdout.splitlines() != [path.as_posix()]
                or working.stdout.strip()
            ):
                raise ValueError(f"invalid pre-commit candidate: {path}")
            states.append("pre_commit")
    if len(set(states)) != 1:
        raise ValueError("mixed lifecycle")
    suffix = "admit_014_formal_evaluator_interface_contract"
    expected_top = set(exact10[:4])
    observed_top = {
        path.relative_to(repo_root)
        for directory in ("src/covalent_ext", "scripts", "tests", "docs")
        for path in (repo_root / directory).glob(f"*{suffix}*")
        if path.is_file() or path.is_symlink()
    }
    if observed_top != expected_top:
        raise ValueError("extra or missing same-stage top-level candidate")
    roots = sorted(
        (repo_root / OUTPUT_ROOT.parent).glob(f"{OUTPUT_ROOT.name}*")
    )
    if roots != [repo_root / OUTPUT_ROOT]:
        raise ValueError("extra or missing same-stage derived root")
    if {
        path.name for path in (repo_root / OUTPUT_ROOT).iterdir()
    } != set(FILES):
        raise ValueError("missing or seventh Exact6 output")
    return states[0]


def _validate_protected_paths() -> None:
    changed = _git(["diff", "--name-only"]).stdout.splitlines()
    protected = (
        "data/raw/",
        "checkpoints/",
        "equivariant_diffusion/",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
    )
    if any(
        path == item or path.startswith(item)
        for path in changed
        for item in protected
    ):
        raise ValueError("protected path changed")


def validate() -> str:
    _guard()
    sources = _source_snapshot()
    module = _validate_ast_and_load()
    lifecycle = _lifecycle()
    outputs = _pinned_outputs(REPO_ROOT / OUTPUT_ROOT)
    if set(outputs) != set(FILES):
        raise ValueError("Exact6 output key drift")
    for name, digest in OUTPUT_SHA256.items():
        if hashlib.sha256(outputs[name]).hexdigest() != digest:
            raise ValueError(f"frozen output SHA mismatch: {name}")
    manifest = _parse_manifest_exact(outputs[MANIFEST])
    contract = _rows(outputs[CONTRACT])
    routing = _rows(outputs[ROUTING])
    truth = _rows(outputs[TRUTH])
    source_rows = _rows(outputs[SOURCE])
    issues = _rows(outputs[ISSUE])
    if (
        tuple(contract[0]) != CONTRACT_HEADER
        or tuple(routing[0]) != ROUTING_HEADER
        or tuple(truth[0]) != TRUTH_HEADER
        or tuple(source_rows[0]) != SOURCE_HEADER
    ):
        raise ValueError("Exact6 schema drift")
    if not (
        len(contract) == 22
        and len(routing) == 8
        and len(truth) == 69
        and len(source_rows) == 11
        and len(issues) == 30
        and all(row["contract_passed"] == "true" for row in contract)
        and all(row["routing_passed"] == "true" for row in routing)
        and all(row["case_passed"] == "true" for row in truth)
        and all(row["source_verified"] == "true" for row in source_rows)
    ):
        raise ValueError("Exact6 row/pass count drift")
    signature_rows = truth[:8]
    if (
        [row["case_id"] for row in signature_rows]
        != list(SIGNATURE_CASE_IDS)
        or [row["case_group"] for row in signature_rows]
        != ["signature"] * 8
        or [row["expected_outcome"] for row in signature_rows]
        != ["verified"] * 6 + ["rejected"] * 2
        or [row["observed_outcome"] for row in signature_rows]
        != ["verified"] * 6 + ["rejected"] * 2
        or [row["expected_reason"] for row in signature_rows]
        != [""] * 6 + ["TypeError"] * 2
        or [row["observed_reason"] for row in signature_rows]
        != [""] * 6 + ["TypeError"] * 2
        or any(
            row[column] != "()"
            for row in signature_rows
            for column in (
                "expected_canonical_record",
                "observed_canonical_record",
                "expected_validated_fields",
                "observed_validated_fields",
                "expected_consumed_fields",
                "observed_consumed_fields",
            )
        )
        or any(
            row["result_contract_passed"] != "true"
            or row["case_passed"] != "true"
            or row["expected_reason"]
            == "STAGE_AUTHORIZATION_CONTEXT_REQUIRED"
            or row["observed_reason"]
            == "STAGE_AUTHORIZATION_CONTEXT_REQUIRED"
            for row in signature_rows
        )
    ):
        raise ValueError("signature Exact8 meta evidence drift")
    non_signature_digest = hashlib.sha256(
        json.dumps(
            truth[8:], sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    if non_signature_digest != NON_SIGNATURE_TRUTH_SHA256:
        raise ValueError("non-signature Exact61 truth evidence drift")
    if [row["source_relative_path"] for row in source_rows] != [
        path.as_posix() for path, _ in SOURCES
    ]:
        raise ValueError("source audit order drift")
    if [row["expected_sha256"] for row in source_rows] != [
        digest for _, digest in SOURCES
    ]:
        raise ValueError("source audit SHA drift")
    inherited = _rows(
        sources[AUTH_ROOT / "covapie_admit_014_issue_readiness_inventory.csv"]
    )
    if [row["issue_id"] for row in issues] != [
        row["issue_id"] for row in inherited
    ]:
        raise ValueError("Exact30 issue identity/order drift")
    by_id = {row["issue_id"]: row for row in issues}
    for issue_id, evidence in TRANSITIONS.items():
        row = by_id[issue_id]
        if (
            row["successor_effective_status"] != "resolved"
            or row["successor_transition_action"]
            != "resolved_by_successor_formal_interface_contract_design"
            or row["successor_transition_evidence"] != evidence
        ):
            raise ValueError("Exact2 issue transition drift")
    if any(
        by_id[issue]["successor_effective_status"] != "open"
        for issue in GLOBAL_OPEN
    ):
        raise ValueError("required global issue closed")
    if any(
        row["successor_effective_status"] != "resolved"
        for row in issues[23:]
    ):
        raise ValueError("ADMIT_014 Exact7 issue not all resolved")
    if (
        by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
            "affected_rules"
        ]
        != "ADMIT_014|ADMIT_015"
    ):
        raise ValueError("coverage affected-rules drift")
    expected_readiness = {
        **{key: True for key in TRUE_KEYS},
        **{key: False for key in FALSE_KEYS},
    }
    if (
        manifest["readiness"] != expected_readiness
        or any(manifest[key] is not True for key in TRUE_KEYS)
        or any(manifest[key] is not False for key in FALSE_KEYS)
    ):
        raise ValueError("readiness drift")
    pre = manifest["precondition_transition"]
    if pre != {
        "row_count": 51,
        "complete_count": 49,
        "incomplete_count": 2,
        "implementation_blocking_count": 2,
        "resolved_precondition_ids": ["PRE_039", "PRE_040", "PRE_041"],
        "remaining_open_precondition_ids": ["PRE_048", "PRE_049"],
    }:
        raise ValueError("precondition 49/2 drift")
    if not (
        manifest["future_public_signature"] == FUTURE_SIGNATURE
        and manifest["result_fields"] == list(RESULT_FIELDS)
        and manifest["result_field_exact_types"] == list(RESULT_TYPES)
        and manifest["outcome_vocabulary"] == ["passed", "blocked"]
        and manifest["truth_matrix_signature_meta_semantics"]
        == {
            "row_count": 8,
            "property_rows": 6,
            "property_meta_outcome": "verified",
            "rejection_rows": 2,
            "rejection_meta_outcome": "rejected",
            "rejection_reason": "TypeError",
            "generated_by_real_signature_introspection_bind_and_invocation": True,
            "meta_outcomes_are_formal_evaluator_outcomes": False,
        }
        and manifest["reason_vocabulary"] == list(REASONS)
        and manifest["formal_evaluator_implemented"] is False
        and manifest["formal_result_type_defined"] is False
        and manifest["current_permission"] is False
        and manifest["ready_for_bulk_download_now"] is False
        and manifest[
            "mandatory_pre_download_authorization_enforcement_contract"
        ]["implemented"]
        is False
        and manifest["unified_adapter_contract_frozen"] is False
        and manifest["unified_adapter_implemented"] is False
        and manifest["admit_014_registered_in_engine"] is False
        and manifest[
            "unified_dispatch_runtime_with_admit_001_to_014_implemented"
        ]
        is False
        and manifest["source_count"] == 11
        and manifest["output_files"] == list(FILES)
        and manifest["output_sha256"]
        == {name: OUTPUT_SHA256[name] for name in FILES[:-1]}
        and manifest["recommended_next_step"]
        == "implement_covapie_admit_014_standalone_evaluator_interface_v1"
        and not any(manifest["safety"].values())
    ):
        raise ValueError("manifest contract boundary drift")
    _validate_signature_and_oracle(module)
    _validate_protected_paths()
    return lifecycle


def main() -> int:
    lifecycle = validate()
    print(f"stage={STAGE}")
    print(f"base_commit={BASE}")
    print("canonical_evidence_python=cpython-3.10.4")
    print("source_count=11")
    print(f"future_public_signature={FUTURE_SIGNATURE}")
    print("result_field_count=9")
    print("truth_matrix_rows=69")
    print("truth_matrix_negative_result_rows=24")
    print("precondition_complete=49")
    print("precondition_open=2")
    print("issue_rows=30")
    print("issue_transitions=2")
    print("remaining_open_admit_014_issues=0")
    print("current_permission=false")
    print("formal_evaluator_implemented=false")
    print("formal_result_type_defined=false")
    print("adapter_registry_runtime_implemented=false")
    print("mandatory_enforcement_implemented=false")
    print(
        "recommended_next_step="
        "implement_covapie_admit_014_standalone_evaluator_interface_v1"
    )
    print(f"lifecycle={lifecycle}")
    print(f"{STAGE}_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
