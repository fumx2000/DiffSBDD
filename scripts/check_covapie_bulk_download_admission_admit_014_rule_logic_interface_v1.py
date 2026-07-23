#!/usr/bin/env python3
"""Independent fail-closed checker for ADMIT_014 standalone evaluator v1."""

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


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "0ec764f03bd3fe227a1e346380f1cdf31837f023"
BASE_PARENT = "d56140d8558208ee34eb5a43773010a2dc69169b"
BASE_TREE = "13c3d43310ec6eaa53004f92550e7184d1f67229"
BASE_SUBJECT = "add CovaPIE ADMIT_014 formal evaluator interface contract v1"
STAGE = "covapie_bulk_download_admission_admit_014_rule_logic_interface_v1"
PRODUCTION_PATH = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_014_rule_logic_interface.py"
)
CHECKER_PATH = Path(
    "scripts/"
    "check_covapie_bulk_download_admission_admit_014_rule_logic_interface_v1.py"
)
TEST_PATH = Path(
    "tests/"
    "test_covapie_bulk_download_admission_admit_014_rule_logic_interface_v1.py"
)
SUMMARY_PATH = Path(
    "docs/"
    "covapie_bulk_download_admission_admit_014_rule_logic_interface_v1_summary.md"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
OUTPUT_FILES = (
    "covapie_admit_014_rule_logic_interface_contract.csv",
    "covapie_admit_014_rule_logic_interface_truth_matrix.csv",
    "covapie_admit_014_rule_logic_interface_source_boundary_audit.csv",
    "covapie_admit_014_rule_logic_interface_purity_audit.csv",
    "covapie_admit_014_rule_logic_interface_issue_readiness_inventory.csv",
    "covapie_admit_014_rule_logic_interface_manifest.json",
)
STAGE_PATHS = (
    PRODUCTION_PATH,
    CHECKER_PATH,
    TEST_PATH,
    SUMMARY_PATH,
    *(OUTPUT_ROOT / name for name in OUTPUT_FILES),
)
FORBIDDEN_SUFFIXES = {
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part",
}
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
    "str", "str", "bool", "bool", "str", "tuple", "tuple", "tuple", "bool",
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
PUBLIC_SIGNATURE = (
    "evaluate_admit_014(*, stage_authorization_context: object = _MISSING) "
    "-> Admit014EvaluationResult"
)
FORMAL_MARKER = "# === ADMIT_014 FORMAL EVALUATOR CLOSURE END ==="
FORMAL_CLOSURE = (
    "_MissingAdmit014Value",
    "_canonical_record_valid",
    "_field_tuple_valid",
    "Admit014EvaluationResult",
    "Admit014EvaluationResult.__post_init__",
    "_make_result",
    "evaluate_admit_014",
)
EXPECTED_PRODUCTION_SHA256 = (
    "5f0766a4eb9dac8b00b9729b7d593adfbe105fb212eabbd4e0a3e349b35f7399"
)
EXPECTED_PREFIX_SHA256 = (
    "503f60c182ab5840d1c56be31f562c94f2b72638b98918857ea0064da8c74cd3"
)
EXPECTED_AST_SHA256 = {
    "_MissingAdmit014Value": (
        "ee7527b1c1d027aeb6f1dd6e8f9f161f8e6dc2755d49d3a676598c81e21a14f9"
    ),
    "_canonical_record_valid": (
        "9e04222a22ae478a9bd53403c1258f39ba5daa2b5e94c7eb7b51a46510c6c6e0"
    ),
    "_field_tuple_valid": (
        "403164b296b64d7f06e27187dafd6346a9bc22cd24e60b72e9f7f738ecd12374"
    ),
    "Admit014EvaluationResult": (
        "d9580ade59b9935b80b4972a20d5b5ce2c9a4d481681e29cabe08580e60aa638"
    ),
    "Admit014EvaluationResult.__post_init__": (
        "a4b01999539926b13d0d48fca38f7bce29da3606ecb5d02f25a53ec86fa1e2f5"
    ),
    "_make_result": (
        "90a1edd05e6248f6e11c8487dc352a07cefd9130091799ca403bd6007ea6d370"
    ),
    "evaluate_admit_014": (
        "bf00f8b471ec5f179d0c2378096077fc850bed0342fe1fe9337d871b2ee87471"
    ),
}
EXPECTED_OUTPUT_SHA256 = {
    "covapie_admit_014_rule_logic_interface_contract.csv": (
        "90b07d8988a4ff8605e5fb4565d91374b91eb098fad850a492e72cf5dee60e79"
    ),
    "covapie_admit_014_rule_logic_interface_truth_matrix.csv": (
        "3f48127236c1e27839cd7960ca1e7f64efcc60d49a28805d727862fe5eb71b97"
    ),
    "covapie_admit_014_rule_logic_interface_source_boundary_audit.csv": (
        "7ed009637e145c3f0e004ad5bb113f57946d87127519be10a7ee87f4fcaf0e5d"
    ),
    "covapie_admit_014_rule_logic_interface_purity_audit.csv": (
        "f4814496d8ac19587c7f13bd22567e71d9843f7c59f3f80de5935336b1a1d11a"
    ),
    "covapie_admit_014_rule_logic_interface_issue_readiness_inventory.csv": (
        "d2510c9d2cf7ee1a1fc378e639eb69b68612e818f4e7af10a0e36dc0d788f54d"
    ),
    "covapie_admit_014_rule_logic_interface_manifest.json": (
        "f1266a2a471ddac3a0966951ff681b19ebd7d2725ff8242942a9365f92f7e056"
    ),
}
MANIFEST_KEYS = (
    "Admit014EvaluationResult_implemented",
    "actual_evaluator_design_oracle_projection_passed",
    "actual_result_negative_projection_rejected",
    "adapter_registry_runtime_changed",
    "admission_rule_id",
    "admit_014_download_authorization_contract_designed",
    "admit_014_formal_evaluator_interface_contract_frozen",
    "admit_014_formal_result_contract_frozen",
    "admit_014_future_evaluator_pure_in_memory_possible",
    "admit_014_preconditions_audited",
    "admit_014_registered_in_engine",
    "admit_014_result_representation_frozen",
    "admit_014_rule_logic_implemented",
    "admit_014_standalone_evaluator_interface_implemented",
    "admit_014_standalone_signature_frozen",
    "admit_014_unified_adapter_contract_frozen",
    "admit_014_unified_adapter_implemented",
    "all_checks_passed",
    "ast_attestation_cross_python_version_portable",
    "authorized_admit_014_download_execution_count",
    "base_commit",
    "base_parent",
    "base_subject",
    "base_tree",
    "canonical_evidence_python_implementation",
    "canonical_evidence_python_version",
    "combined_candidate_verdict_implemented",
    "coverage_affected_rules",
    "cross_rule_aggregation_implemented",
    "current_permission",
    "evaluate_admit_014_implemented",
    "feature_semantics_audit_required_before_training",
    "feature_semantics_audit_requirement",
    "formal_ast_sha256",
    "formal_closure",
    "formal_closure_count",
    "formal_evaluator_implemented",
    "formal_marker",
    "formal_marker_prefix_sha256",
    "formal_production_sha256",
    "formal_result_type_defined",
    "issue_inventory_byte_identical_to_formal_interface",
    "issue_transition_count",
    "mandatory_pre_download_authorization_enforcement_implemented",
    "manifest_schema_version",
    "mapping_consumption_contract",
    "materialization_policy",
    "noncanonical_python_policy",
    "outcome_vocabulary",
    "output_file_count",
    "output_files",
    "output_sha256",
    "parameter_count",
    "parameter_order",
    "precondition_transition",
    "private_missing_singleton",
    "project",
    "provider_mapping_validated",
    "public_evaluator",
    "public_signature",
    "purity_closure_complete",
    "python_runtime_migration_policy",
    "readiness",
    "ready_for_admit_014_unified_adapter_contract_design",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "real_provider_evaluation_ready",
    "reason_vocabulary",
    "recommended_next_step",
    "remaining_open_issue_ids",
    "result_field_count",
    "result_field_exact_types",
    "result_fields",
    "result_type",
    "row_counts",
    "safety",
    "source_boundary",
    "source_count",
    "source_validation_before_candidate_and_output_read",
    "stage",
    "step12d_is_final_training_feature_contract",
    "step12d_status",
    "truth_matrix_passed",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "unified_dispatch_runtime_with_admit_001_to_014_implemented",
)
MANIFEST_OBJECT_KEYS = {
    "formal_ast_sha256": (
        "Admit014EvaluationResult",
        "Admit014EvaluationResult.__post_init__",
        "_MissingAdmit014Value",
        "_canonical_record_valid",
        "_field_tuple_valid",
        "_make_result",
        "evaluate_admit_014",
    ),
    "mapping_consumption_contract": (
        "admit_015_key_access_count",
        "contains_count",
        "extra_keys_allowed",
        "get_count",
        "iteration_count",
        "len_count",
        "target_key",
        "target_lookup_exact_count_for_mappings",
    ),
    "materialization_policy": (
        "build_before_mutation",
        "complete_exact6_post_read",
        "destination_name_inode_binding",
        "exact_output_inventory",
        "gpfs_einval_fails_closed",
        "inode_preserving_exact_set_noop",
        "leaf_and_directory_fsync",
        "leaf_open_dir_fd",
        "o_excl_staging_leaves",
        "os_replace_fallback",
        "parent_fd_pinned",
        "post_fsync_destination_binding",
        "rename_noreplace_required",
        "rename_relative_to_parent_fd",
        "root_fd_no_follow",
        "staging_fd_pinned",
    ),
    "output_sha256": (
        "covapie_admit_014_rule_logic_interface_contract.csv",
        "covapie_admit_014_rule_logic_interface_issue_readiness_inventory.csv",
        "covapie_admit_014_rule_logic_interface_purity_audit.csv",
        "covapie_admit_014_rule_logic_interface_source_boundary_audit.csv",
        "covapie_admit_014_rule_logic_interface_truth_matrix.csv",
    ),
    "precondition_transition": (
        "complete_count",
        "implementation_blocking_count",
        "incomplete_count",
        "remaining_open_precondition_ids",
        "row_count",
    ),
    "readiness": (
        "Admit014EvaluationResult_implemented",
        "admit_014_download_authorization_contract_designed",
        "admit_014_formal_evaluator_interface_contract_frozen",
        "admit_014_formal_result_contract_frozen",
        "admit_014_future_evaluator_pure_in_memory_possible",
        "admit_014_preconditions_audited",
        "admit_014_registered_in_engine",
        "admit_014_result_representation_frozen",
        "admit_014_rule_logic_implemented",
        "admit_014_standalone_evaluator_interface_implemented",
        "admit_014_standalone_signature_frozen",
        "admit_014_unified_adapter_contract_frozen",
        "admit_014_unified_adapter_implemented",
        "combined_candidate_verdict_implemented",
        "cross_rule_aggregation_implemented",
        "evaluate_admit_014_implemented",
        "feature_semantics_audit_required_before_training",
        "mandatory_pre_download_authorization_enforcement_implemented",
        "provider_mapping_validated",
        "ready_for_admit_014_unified_adapter_contract_design",
        "ready_for_bulk_download_now",
        "ready_for_training",
        "real_provider_evaluation_ready",
        "step12d_is_final_training_feature_contract",
        "unified_dispatch_runtime_with_admit_001_to_013_implemented",
        "unified_dispatch_runtime_with_admit_001_to_014_implemented",
    ),
    "row_counts": (
        "actual_evaluator_design_projection",
        "actual_result_negative_projection",
        "formal_contract",
        "issue_inventory",
        "purity_audit",
        "source_boundary",
        "truth_matrix",
    ),
    "safety": (
        "combined_candidate_verdict",
        "cross_rule_aggregation",
        "dataloader",
        "download",
        "model_or_checkpoint",
        "network",
        "provider",
        "raw_read_or_write",
        "stage_commit_push",
        "training_or_parameter_update",
    ),
}
SOURCE_BOUNDARY_KEYS = (
    "base_tree_blob",
    "base_tree_mode",
    "path",
    "sha256",
)
FORMAL_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_v1"
)
DESIGN_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_design_gate.py"
)
SOURCE_SHA256 = {
    DESIGN_PRODUCTION: (
        "af25eb2f2fb84230b29d2204fff05308626e7f455a7b950aa8efb922607c298e"
    ),
    FORMAL_ROOT
    / "covapie_admit_014_formal_evaluator_interface_and_result_contract.csv": (
        "7baea79ce0010e31efcf2e70f11350ee5fc05a5c358df3926f9df591da3d3524"
    ),
    FORMAL_ROOT
    / "covapie_admit_014_formal_evaluator_routing_and_consumption_contract.csv": (
        "9df1faddeb8aa14e8b29af10296222925361cd1f1f98c05a2cc3a2cc64c7f769"
    ),
    FORMAL_ROOT
    / "covapie_admit_014_formal_evaluator_interface_truth_matrix.csv": (
        "55dbbddf1f3bcdb4bbd6ce763d7a0c812020241157098c6af18799cc5ffac062"
    ),
    FORMAL_ROOT
    / "covapie_admit_014_formal_evaluator_interface_issue_readiness_inventory.csv": (
        "d2510c9d2cf7ee1a1fc378e639eb69b68612e818f4e7af10a0e36dc0d788f54d"
    ),
    FORMAL_ROOT
    / "covapie_admit_014_formal_evaluator_interface_contract_manifest.json": (
        "217490ef69526486b51117e4900d0669b4de466a023023ecb56ebdf0822fb731"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_014_"
        "download_authorization_contract_v1/"
        "covapie_admit_014_download_authorization_truth_matrix.csv"
    ): "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482",
    Path(
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_014_"
        "download_authorization_contract_v1/"
        "covapie_admit_014_download_authorization_contract_manifest.json"
    ): "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
    Path(
        "src/covalent_ext/"
        "covapie_bulk_download_admission_admit_013_rule_logic_interface.py"
    ): "36a4d3080128dadcecbdda25c5a3e143ac054aba001e7ac9cd7de0e2c51307f4",
    Path(
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/"
        "covapie_admit_013_rule_logic_interface_manifest.json"
    ): "3ecbbc4d99966c955b39cad4dae65ef9c8316c7847bd43ccef82c44863cd4fa5",
    Path(
        "src/covalent_ext/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013.py"
    ): "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892",
    Path(
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1/"
        "covapie_admit_001_to_013_runtime_manifest.json"
    ): "2940e6cc02a92b4919cdece3b1fa7c2f5e27d844f2962bb18757197266c23f79",
}
NEGATIVE_RESULT_CASES = (
    "WRONG_ADMISSION_RULE_ID",
    "UNKNOWN_OUTCOME",
    "PASSED_NONEXACT_BOOL",
    "BLOCKS_NONEXACT_BOOL",
    "IO_NONEXACT_BOOL",
    "IO_TRUE",
    "PASS_NONEMPTY_REASON",
    "BLOCK_EMPTY_REASON",
    "CANONICAL_LIST",
    "CANONICAL_TUPLE_SUBCLASS",
    "PAIR_TUPLE_SUBCLASS",
    "WRONG_CANONICAL_KEY",
    "NONBOOL_CANONICAL_VALUE",
    "DUPLICATE_CANONICAL_PAIR",
    "VALIDATED_LIST",
    "VALIDATED_TUPLE_SUBCLASS",
    "UNKNOWN_VALIDATED_FIELD",
    "DUPLICATE_VALIDATED_FIELD",
    "CONSUMED_LIST",
    "CONSUMED_TUPLE_SUBCLASS",
    "UNKNOWN_CONSUMED_FIELD",
    "DUPLICATE_CONSUMED_FIELD",
    "CANONICAL_VALIDATED_MISMATCH",
    "VALIDATED_CONSUMED_MISMATCH",
)
TRUE_READINESS = (
    "admit_014_preconditions_audited",
    "admit_014_download_authorization_contract_designed",
    "admit_014_formal_evaluator_interface_contract_frozen",
    "admit_014_standalone_signature_frozen",
    "admit_014_formal_result_contract_frozen",
    "admit_014_result_representation_frozen",
    "admit_014_standalone_evaluator_interface_implemented",
    "evaluate_admit_014_implemented",
    "Admit014EvaluationResult_implemented",
    "admit_014_rule_logic_implemented",
    "admit_014_future_evaluator_pure_in_memory_possible",
    "ready_for_admit_014_unified_adapter_contract_design",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
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


class Truthy:
    def __bool__(self) -> bool:
        return True


class Falsy:
    def __bool__(self) -> bool:
        return False


class TupleSubclass(tuple):
    pass


def _guard() -> None:
    if (
        sys.implementation.name != "cpython"
        or tuple(sys.version_info[:3]) != (3, 10, 4)
    ):
        raise RuntimeError("independent checker requires canonical CPython 3.10.4")


def _git(
    args: list[str],
    repo_root: Path = REPO_ROOT,
    *,
    text: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=text,
        check=False,
    )


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _identity(
    item: os.stat_result,
) -> tuple[int, int, int, int, int, int]:
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


def _read_regular(path: Path, repo_root: Path = REPO_ROOT) -> bytes:
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
    root_item = os.lstat(repo_root)
    root_identity = _identity(root_item)
    if stat.S_ISLNK(root_item.st_mode) or not stat.S_ISDIR(root_item.st_mode):
        raise ValueError("unsafe repository root")
    descriptors: list[
        tuple[int, tuple[int, int, int, int, int, int], int | None, str | None]
    ] = []
    root_fd = os.open(repo_root, directory_flags)
    if _identity(os.fstat(root_fd)) != root_identity:
        os.close(root_fd)
        raise ValueError("repository root stat/open race")
    descriptors.append((root_fd, root_identity, None, None))
    try:
        parent_fd = root_fd
        for part in path.parts[:-1]:
            lexical = os.stat(
                part, dir_fd=parent_fd, follow_symlinks=False
            )
            expected = _identity(lexical)
            if stat.S_ISLNK(lexical.st_mode) or not stat.S_ISDIR(
                lexical.st_mode
            ):
                raise ValueError(f"unsafe source parent: {path}")
            child_fd = os.open(part, directory_flags, dir_fd=parent_fd)
            if _identity(os.fstat(child_fd)) != expected:
                os.close(child_fd)
                raise ValueError(f"source parent stat/open race: {path}")
            descriptors.append((child_fd, expected, parent_fd, part))
            parent_fd = child_fd
        before = os.stat(
            path.name, dir_fd=parent_fd, follow_symlinks=False
        )
        expected_leaf = _identity(before)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise ValueError(f"unsafe source leaf: {path}")
        leaf_fd = os.open(path.name, leaf_flags, dir_fd=parent_fd)
        try:
            if _identity(os.fstat(leaf_fd)) != expected_leaf:
                raise ValueError(f"source stat/open race: {path}")
            chunks = []
            while True:
                chunk = os.read(leaf_fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            if _identity(os.fstat(leaf_fd)) != expected_leaf:
                raise ValueError(f"source FD identity drift: {path}")
        finally:
            os.close(leaf_fd)
        if (
            _identity(
                os.stat(
                    path.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            )
            != expected_leaf
        ):
            raise ValueError(f"source lexical identity drift: {path}")
        for descriptor, expected, lexical_parent, lexical_name in descriptors:
            if _identity(os.fstat(descriptor)) != expected:
                raise ValueError(f"source parent FD identity drift: {path}")
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
                    raise ValueError(
                        f"source parent lexical identity drift: {path}"
                    )
        if _identity(os.lstat(repo_root)) != root_identity:
            raise ValueError("repository root identity drift")
        return b"".join(chunks)
    finally:
        for descriptor, _, _, _ in reversed(descriptors):
            os.close(descriptor)


def _check_base_and_sources() -> dict[Path, bytes]:
    identity = _git(
        ["show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT]
    )
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if identity.returncode or ancestor.returncode:
        raise ValueError("base lineage unavailable")
    if identity.stdout.splitlines() != [
        BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT
    ]:
        raise ValueError("base identity drift")
    if len(SOURCE_SHA256) != 12:
        raise ValueError("source boundary not Exact12")
    sources = {}
    for path, expected in SOURCE_SHA256.items():
        index = _git(["ls-files", "--stage", "--", path.as_posix()])
        tree = _git(["ls-tree", BASE_COMMIT, "--", path.as_posix()])
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
            raise ValueError(f"source index/base drift: {path}")
        current = _read_regular(path)
        base = _git(
            ["show", f"{BASE_COMMIT}:{path.as_posix()}"], text=False
        )
        if (
            base.returncode
            or not isinstance(base.stdout, bytes)
            or base.stdout != current
            or _sha(current) != expected
        ):
            raise ValueError(f"source SHA/base drift: {path}")
        sources[path] = current
    return sources


def _check_formal_source() -> tuple[bytes, dict[str, str]]:
    source = _read_regular(PRODUCTION_PATH)
    if _sha(source) != EXPECTED_PRODUCTION_SHA256:
        raise ValueError("candidate production SHA drift")
    text = source.decode()
    if text.count(FORMAL_MARKER) != 1:
        raise ValueError("formal marker drift")
    prefix = text.split(FORMAL_MARKER, 1)[0].encode()
    if _sha(prefix) != EXPECTED_PREFIX_SHA256:
        raise ValueError("formal prefix SHA drift")
    tree = ast.parse(prefix)
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    if set(definitions) != {
        "_MissingAdmit014Value",
        "_canonical_record_valid",
        "_field_tuple_valid",
        "Admit014EvaluationResult",
        "_make_result",
        "evaluate_admit_014",
    }:
        raise ValueError("formal definition set drift")
    result_class = definitions["Admit014EvaluationResult"]
    post = next(
        node for node in result_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "__post_init__"
    )
    class_fields = tuple(
        node.target.id
        for node in result_class.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
    )
    if class_fields != RESULT_FIELDS:
        raise ValueError("Exact9 result storage drift")
    evaluator = definitions["evaluate_admit_014"]
    if (
        evaluator.args.posonlyargs
        or evaluator.args.args
        or evaluator.args.vararg is not None
        or evaluator.args.kwarg is not None
        or tuple(arg.arg for arg in evaluator.args.kwonlyargs)
        != ("stage_authorization_context",)
        or len(evaluator.args.kw_defaults) != 1
        or not isinstance(evaluator.args.kw_defaults[0], ast.Name)
        or evaluator.args.kw_defaults[0].id != "_MISSING"
        or not isinstance(evaluator.returns, ast.Name)
        or evaluator.returns.id != "Admit014EvaluationResult"
    ):
        raise ValueError("public evaluator signature AST drift")
    nodes = {
        name: post if name.endswith(".__post_init__") else definitions[name]
        for name in FORMAL_CLOSURE
    }
    digests = {
        name: _sha(
            ast.dump(
                node, annotate_fields=True, include_attributes=False
            ).encode()
        )
        for name, node in nodes.items()
    }
    if digests != EXPECTED_AST_SHA256:
        raise ValueError("normalized formal AST drift")
    forbidden = {
        "open", "eval", "exec", "getattr", "globals", "locals", "__import__",
        "os", "Path", "subprocess", "socket", "requests", "urllib", "tempfile",
        "json", "csv", "hashlib", "importlib", "provider", "download", "raw",
        "registry", "dispatcher", "training",
    }
    for name, node in nodes.items():
        if any(
            isinstance(item, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal))
            for item in ast.walk(node)
        ):
            raise ValueError(f"purity statement violation: {name}")
        if any(
            isinstance(item, ast.Name) and item.id in forbidden
            for item in ast.walk(node)
        ):
            raise ValueError(f"purity binding violation: {name}")
        if any(
            isinstance(item, ast.Attribute)
            and item.attr in {"open", "read", "write", "fsync", "replace"}
            for item in ast.walk(node)
        ):
            raise ValueError(f"purity I/O violation: {name}")
    full_tree = ast.parse(source)
    forbidden_symbols = {
        "_evaluate_registered_admit_014",
        "EVALUATOR_REGISTRY",
        "evaluate_admission_rule",
    }
    symbols = {
        node.name
        for node in ast.walk(full_tree)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    } | {
        target.id
        for node in ast.walk(full_tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    if forbidden_symbols & symbols or b"os.replace" in source:
        raise ValueError("adapter/registry/runtime or os.replace present")
    return source, digests


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / path)
    if spec is None or spec.loader is None:
        raise ValueError(f"isolated import unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def _context(case_id: str) -> object:
    invalid = {
        "INT_ZERO": 0, "INT_ONE": 1, "FLOAT_ZERO": 0.0, "FLOAT_ONE": 1.0,
        "STRING_FALSE": "false", "STRING_TRUE": "true", "NONE_VALUE": None,
        "LIST_VALUE": [], "DICT_VALUE": {}, "CUSTOM_TRUTHY": Truthy(),
        "CUSTOM_FALSY": Falsy(),
    }
    if case_id in {"OMITTED", "PROJECTION_OMITTED"}:
        return MISSING
    if case_id == "EXPLICIT_NONE":
        return None
    if case_id == "CONTEXT_OBJECT":
        return object()
    if case_id == "CONTEXT_INT":
        return 7
    if case_id == "CONTEXT_STR":
        return "x"
    if case_id == "CONTEXT_LIST":
        return []
    if case_id in {"EMPTY_MAPPING", "PROJECTION_MISSING_KEY"}:
        return Probe()
    if case_id == "UNRELATED_ONLY_MAPPING":
        return Probe({"other": True})
    if case_id == "LOOKUP_KEYERROR":
        return Probe(error=KeyError(TARGET_KEY))
    if case_id in {"LOOKUP_RUNTIMEERROR", "PROJECTION_LOOKUP_FAILED"}:
        return Probe(error=RuntimeError("boom"))
    if case_id == "LOOKUP_VALUEERROR":
        return Probe(error=ValueError("boom"))
    if case_id in invalid:
        return Probe({TARGET_KEY: invalid[case_id]})
    if case_id == "PROJECTION_INVALID_TYPE":
        return Probe({TARGET_KEY: "true"})
    if case_id in {"EXACT_FALSE", "PROJECTION_FALSE"}:
        return Probe({TARGET_KEY: False})
    if case_id in {"EXACT_TRUE", "PROJECTION_TRUE"}:
        return Probe({TARGET_KEY: True})
    if case_id == "ADMIT015_PLUS_TRUE":
        return Probe({ADMIT015_KEY: False, TARGET_KEY: True})
    if case_id == "ADMIT015_PLUS_FALSE":
        return Probe({ADMIT015_KEY: True, TARGET_KEY: False})
    if case_id == "MANY_EXTRA_PLUS_TRUE":
        return Probe({**{f"extra_{i}": object() for i in range(20)}, TARGET_KEY: True})
    if case_id in {
        "ITERATION_RAISES", "LEN_RAISES", "GET_RAISES", "CONTAINS_RAISES"
    }:
        return Probe({TARGET_KEY: True})
    raise ValueError(f"unknown truth case: {case_id}")


class Missing:
    pass


MISSING = Missing()


def _access_valid(value: object) -> bool:
    return not isinstance(value, Probe) or (
        value.item_keys == [TARGET_KEY]
        and value.iteration == value.length == value.gets == value.contains == 0
    )


def _reject_negative(module, case_id: str) -> None:
    baseline = module.evaluate_admit_014(
        stage_authorization_context={TARGET_KEY: True}
    )
    values = {name: getattr(baseline, name) for name in RESULT_FIELDS}
    if case_id == "WRONG_ADMISSION_RULE_ID":
        values["admission_rule_id"] = "ADMIT_015"
    elif case_id == "UNKNOWN_OUTCOME":
        values["outcome"] = "invalid"
    elif case_id == "PASSED_NONEXACT_BOOL":
        values["passed"] = 1
    elif case_id == "BLOCKS_NONEXACT_BOOL":
        values["blocks_candidate"] = 0
    elif case_id == "IO_NONEXACT_BOOL":
        values["evaluator_io_used"] = 0
    elif case_id == "IO_TRUE":
        values["evaluator_io_used"] = True
    elif case_id == "PASS_NONEMPTY_REASON":
        values["reason"] = REASONS[-1]
    elif case_id == "BLOCK_EMPTY_REASON":
        values.update(outcome="blocked", passed=False, blocks_candidate=True)
    elif case_id == "CANONICAL_LIST":
        values["canonical_stage_authorization_record"] = [(TARGET_KEY, True)]
    elif case_id == "CANONICAL_TUPLE_SUBCLASS":
        values["canonical_stage_authorization_record"] = TupleSubclass(
            ((TARGET_KEY, True),)
        )
    elif case_id == "PAIR_TUPLE_SUBCLASS":
        values["canonical_stage_authorization_record"] = (
            TupleSubclass((TARGET_KEY, True)),
        )
    elif case_id == "WRONG_CANONICAL_KEY":
        values["canonical_stage_authorization_record"] = ((ADMIT015_KEY, True),)
    elif case_id == "NONBOOL_CANONICAL_VALUE":
        values["canonical_stage_authorization_record"] = ((TARGET_KEY, 1),)
    elif case_id == "DUPLICATE_CANONICAL_PAIR":
        values["canonical_stage_authorization_record"] = (
            (TARGET_KEY, True), (TARGET_KEY, True)
        )
    elif case_id == "VALIDATED_LIST":
        values["validated_stage_authorization_fields"] = [TARGET_KEY]
    elif case_id == "VALIDATED_TUPLE_SUBCLASS":
        values["validated_stage_authorization_fields"] = TupleSubclass((TARGET_KEY,))
    elif case_id == "UNKNOWN_VALIDATED_FIELD":
        values["validated_stage_authorization_fields"] = (ADMIT015_KEY,)
    elif case_id == "DUPLICATE_VALIDATED_FIELD":
        values["validated_stage_authorization_fields"] = (TARGET_KEY, TARGET_KEY)
    elif case_id == "CONSUMED_LIST":
        values["consumed_stage_authorization_fields"] = [TARGET_KEY]
    elif case_id == "CONSUMED_TUPLE_SUBCLASS":
        values["consumed_stage_authorization_fields"] = TupleSubclass((TARGET_KEY,))
    elif case_id == "UNKNOWN_CONSUMED_FIELD":
        values["consumed_stage_authorization_fields"] = (ADMIT015_KEY,)
    elif case_id == "DUPLICATE_CONSUMED_FIELD":
        values["consumed_stage_authorization_fields"] = (TARGET_KEY, TARGET_KEY)
    elif case_id == "CANONICAL_VALIDATED_MISMATCH":
        values["validated_stage_authorization_fields"] = ()
    elif case_id == "VALIDATED_CONSUMED_MISMATCH":
        values["consumed_stage_authorization_fields"] = ()
    try:
        module.Admit014EvaluationResult(*(values[name] for name in RESULT_FIELDS))
    except (TypeError, ValueError):
        return
    raise ValueError(f"negative result accepted: {case_id}")


def _check_actual(module, design, sources: dict[Path, bytes]) -> None:
    signature = inspect.signature(module.evaluate_admit_014)
    parameters = tuple(signature.parameters.values())
    if (
        len(parameters) != 1
        or parameters[0].name != "stage_authorization_context"
        or parameters[0].kind is not inspect.Parameter.KEYWORD_ONLY
        or parameters[0].annotation is not object
        or parameters[0].default is not module._MISSING
        or parameters[0].default is None
        or signature.return_annotation is not module.Admit014EvaluationResult
        or tuple(field.name for field in fields(module.Admit014EvaluationResult))
        != RESULT_FIELDS
    ):
        raise ValueError("actual public signature/result drift")
    if str(signature).replace(
        "<covalent_ext.covapie_bulk_download_admission_admit_014_rule_logic_interface.",
        "",
    ) != (
        "(*, stage_authorization_context: object = "
        "<covalent_ext.covapie_bulk_download_admission_admit_014_rule_logic_interface."
        "_MissingAdmit014Value object at "
    ):
        # Exact string is represented in the manifest; inspect properties above
        # are the authoritative runtime check because object repr has an address.
        pass
    try:
        module.evaluate_admit_014(object())
    except TypeError:
        pass
    else:
        raise ValueError("positional call accepted")
    try:
        module.evaluate_admit_014(unknown=True)
    except TypeError:
        pass
    else:
        raise ValueError("unknown keyword accepted")
    truth = list(
        csv.DictReader(
            io.StringIO(
                sources[
                    FORMAL_ROOT
                    / "covapie_admit_014_formal_evaluator_interface_truth_matrix.csv"
                ].decode(),
                newline="",
            )
        )
    )
    executable = [
        row
        for row in truth
        if row["case_group"] not in {"signature", "negative_result_contract"}
    ]
    if len(executable) != 37:
        raise ValueError("committed executable projection not Exact37")
    for row in executable:
        actual_context = _context(row["case_id"])
        design_context = _context(row["case_id"])
        actual_kwargs = {} if actual_context is MISSING else {
            "stage_authorization_context": actual_context
        }
        design_kwargs = {} if design_context is MISSING else {
            "stage_authorization_context": design_context
        }
        actual = module.evaluate_admit_014(**actual_kwargs)
        oracle = design.classify_admit_014_formal_evaluator_interface_design(
            **design_kwargs
        )
        left = tuple(getattr(actual, name) for name in RESULT_FIELDS)
        right = tuple(getattr(oracle, name) for name in RESULT_FIELDS)
        if not (
            type(actual) is module.Admit014EvaluationResult
            and type(oracle) is design.Admit014EvaluationResultContractDesign
            and left == right
            and all(type(a) is type(b) for a, b in zip(left, right, strict=True))
            and actual.evaluator_io_used is False
            and oracle.evaluator_io_used is False
            and _access_valid(actual_context)
            and _access_valid(design_context)
        ):
            raise ValueError(f"actual/design mismatch: {row['case_id']}")
    for case_id in NEGATIVE_RESULT_CASES:
        _reject_negative(module, case_id)
    class ResultSubclass(module.Admit014EvaluationResult):
        pass
    baseline = module.evaluate_admit_014(
        stage_authorization_context={TARGET_KEY: True}
    )
    try:
        ResultSubclass(*(getattr(baseline, name) for name in RESULT_FIELDS))
    except TypeError:
        pass
    else:
        raise ValueError("result subclass accepted")


def _read_outputs(root: Path) -> dict[str, bytes]:
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    parent_item = os.lstat(root.parent)
    parent_identity = _identity(parent_item)
    if stat.S_ISLNK(parent_item.st_mode) or not stat.S_ISDIR(
        parent_item.st_mode
    ):
        raise ValueError("unsafe output parent")
    parent_fd = os.open(root.parent, directory_flags)
    root_fd = -1
    leaves: list[tuple[str, int, tuple[int, ...], bytes]] = []
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("output parent stat/open race")
        root_item = os.stat(
            root.name, dir_fd=parent_fd, follow_symlinks=False
        )
        root_identity = _identity(root_item)
        if stat.S_ISLNK(root_item.st_mode) or not stat.S_ISDIR(
            root_item.st_mode
        ):
            raise ValueError("unsafe output root")
        root_fd = os.open(root.name, directory_flags, dir_fd=parent_fd)
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root stat/open race")
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("Exact6 output inventory drift")
        payloads = {}
        for name in OUTPUT_FILES:
            item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                stat.S_ISLNK(item.st_mode)
                or not stat.S_ISREG(item.st_mode)
                or item.st_size > 100 * 1024 * 1024
            ):
                raise ValueError(f"unsafe output leaf: {name}")
            expected = _identity(item)
            descriptor = os.open(
                name,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=root_fd,
            )
            if _identity(os.fstat(descriptor)) != expected:
                os.close(descriptor)
                raise ValueError("output stat/open race")
            try:
                chunks = []
                while True:
                    chunk = os.read(descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                payload = b"".join(chunks)
            except BaseException:
                os.close(descriptor)
                raise
            payloads[name] = payload
            leaves.append((name, descriptor, expected, payload))
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("Exact6 output inventory drift")
        for name, descriptor, expected, _ in leaves:
            if (
                _identity(os.fstat(descriptor)) != expected
                or _identity(
                    os.stat(name, dir_fd=root_fd, follow_symlinks=False)
                )
                != expected
            ):
                raise ValueError(f"output leaf identity drift: {name}")
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(
                os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != root_identity
            or _identity(os.fstat(parent_fd)) != parent_identity
            or _identity(os.lstat(root.parent)) != parent_identity
        ):
            raise ValueError("output identity/inventory drift")
        return payloads
    finally:
        for _, descriptor, _, _ in leaves:
            os.close(descriptor)
        if root_fd >= 0:
            os.close(root_fd)
        os.close(parent_fd)


def _pairs(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate manifest key: {key}")
        value[key] = item
    return value


def _parse_manifest_exact(data: bytes) -> dict:
    manifest = json.loads(data, object_pairs_hook=_pairs)
    if type(manifest) is not dict or tuple(manifest) != MANIFEST_KEYS:
        raise ValueError("manifest top-level schema/order drift")
    for name, keys in MANIFEST_OBJECT_KEYS.items():
        value = manifest[name]
        if type(value) is not dict or tuple(value) != keys:
            raise ValueError(f"manifest nested schema/order drift: {name}")
    source_boundary = manifest["source_boundary"]
    if (
        type(source_boundary) is not list
        or len(source_boundary) != len(SOURCE_SHA256)
        or any(
            type(row) is not dict or tuple(row) != SOURCE_BOUNDARY_KEYS
            for row in source_boundary
        )
    ):
        raise ValueError("manifest source_boundary schema/order drift")
    return manifest


def _rows(data: bytes, columns: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(data.decode(), newline=""))
    if tuple(reader.fieldnames or ()) != columns:
        raise ValueError("CSV schema/order drift")
    return list(reader)


def _committed_source_identity(path: Path) -> tuple[str, str]:
    index = _git(["ls-files", "--stage", "--", path.as_posix()])
    tree = _git(["ls-tree", BASE_COMMIT, "--", path.as_posix()])
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
        or len(tree_fields[2]) != 40
        or any(character not in "0123456789abcdef" for character in tree_fields[2])
    ):
        raise ValueError(f"source index/base identity drift: {path}")
    return tree_fields[0], tree_fields[2]


def _check_output_semantics(
    outputs: dict[str, bytes],
    sources: dict[Path, bytes],
    ast_digests: dict[str, str],
) -> dict:
    for name, expected in EXPECTED_OUTPUT_SHA256.items():
        if _sha(outputs[name]) != expected:
            raise ValueError(f"frozen output SHA drift: {name}")
    contract_columns = (
        "contract_order", "contract_section", "section_order", "public_name",
        "formal_type", "required", "frozen_value", "formal_invariant",
        "implementation_source", "contract_passed",
    )
    truth_columns = (
        "case_order", "case_id", "case_group", "assertion_kind",
        "inherited_case_id", "stage_context_representation",
        "expected_design_result", "observed_formal_result",
        "exact_type_value_equality", "evaluator_io_used", "formal_source",
        "truth_passed",
    )
    source_columns = (
        "source_order", "source_relative_path", "source_kind", "base_tree_mode",
        "expected_sha256", "base_tree_sha256", "filesystem_sha256",
        "frozen_snapshot_sha256", "git_tracked", "index_stage_zero",
        "base_tree_blob", "filesystem_regular", "non_symlink",
        "parent_chain_non_symlink", "safe_descendant", "pinned_fd_read",
        "post_read_identity_verified", "triple_sha256_passed",
        "source_boundary_passed",
    )
    purity_columns = (
        "audit_order", "audit_kind", "definition_name", "definition_kind",
        "reachable_from", "normalized_ast_sha256", "permitted_global_bindings",
        "permitted_calls", "observed", "forbidden_io_absent",
        "mutation_absent", "dynamic_dispatch_absent", "purity_passed",
    )
    contract = _rows(outputs[OUTPUT_FILES[0]], contract_columns)
    truth = _rows(outputs[OUTPUT_FILES[1]], truth_columns)
    source_rows = _rows(outputs[OUTPUT_FILES[2]], source_columns)
    purity = _rows(outputs[OUTPUT_FILES[3]], purity_columns)
    issues = list(csv.DictReader(io.StringIO(outputs[OUTPUT_FILES[4]].decode())))
    source_manifest = []
    for index, (row, (path, expected)) in enumerate(
        zip(source_rows, SOURCE_SHA256.items(), strict=True), 1
    ):
        mode, blob = _committed_source_identity(path)
        kind = (
            "python_source"
            if path.suffix == ".py"
            else "committed_csv"
            if path.suffix == ".csv"
            else "committed_manifest"
        )
        expected_row = {
            "source_order": str(index),
            "source_relative_path": path.as_posix(),
            "source_kind": kind,
            "base_tree_mode": mode,
            "expected_sha256": expected,
            "base_tree_sha256": expected,
            "filesystem_sha256": expected,
            "frozen_snapshot_sha256": expected,
            "git_tracked": "true",
            "index_stage_zero": "true",
            "base_tree_blob": blob,
            "filesystem_regular": "true",
            "non_symlink": "true",
            "parent_chain_non_symlink": "true",
            "safe_descendant": "true",
            "pinned_fd_read": "true",
            "post_read_identity_verified": "true",
            "triple_sha256_passed": "true",
            "source_boundary_passed": "true",
        }
        if row != expected_row:
            raise ValueError(f"source audit evidence drift: {path}")
        source_manifest.append(
            {
                "base_tree_blob": blob,
                "base_tree_mode": mode,
                "path": path.as_posix(),
                "sha256": expected,
            }
        )
    if not (
        all(row["contract_passed"] == "true" for row in contract)
        and len(truth) == 61
        and [row["case_order"] for row in truth]
        == [str(index) for index in range(1, 62)]
        and all(
            row["exact_type_value_equality"] == "true"
            and row["evaluator_io_used"] == "false"
            and row["truth_passed"] == "true"
            for row in truth
        )
        and sum(
            row["case_group"] != "negative_result_contract" for row in truth
        )
        == 37
        and sum(
            row["case_group"] == "negative_result_contract" for row in truth
        )
        == 24
        and len(source_rows) == 12
        and [row["source_relative_path"] for row in source_rows]
        == [path.as_posix() for path in SOURCE_SHA256]
        and [row["expected_sha256"] for row in source_rows]
        == list(SOURCE_SHA256.values())
        and all(row["source_boundary_passed"] == "true" for row in source_rows)
        and len(purity) == 16
        and [row["definition_name"] for row in purity[:7]]
        == list(FORMAL_CLOSURE)
        and [row["normalized_ast_sha256"] for row in purity[:7]]
        == [ast_digests[name] for name in FORMAL_CLOSURE]
        and all(row["purity_passed"] == "true" for row in purity)
        and len(issues) == 30
        and outputs[OUTPUT_FILES[4]]
        == sources[
            FORMAL_ROOT
            / "covapie_admit_014_formal_evaluator_interface_issue_readiness_inventory.csv"
        ]
    ):
        raise ValueError("Exact6 semantic drift")
    manifest = _parse_manifest_exact(outputs[OUTPUT_FILES[5]])
    readiness = {
        **{name: True for name in TRUE_READINESS},
        **{name: False for name in FALSE_READINESS},
    }
    expected_output_sha = {
        name: EXPECTED_OUTPUT_SHA256[name] for name in OUTPUT_FILES[:-1]
    }
    expected_materialization_policy = {
        "build_before_mutation": True,
        "complete_exact6_post_read": True,
        "destination_name_inode_binding": True,
        "exact_output_inventory": True,
        "gpfs_einval_fails_closed": True,
        "inode_preserving_exact_set_noop": True,
        "leaf_and_directory_fsync": True,
        "leaf_open_dir_fd": True,
        "o_excl_staging_leaves": True,
        "os_replace_fallback": False,
        "parent_fd_pinned": True,
        "post_fsync_destination_binding": True,
        "rename_noreplace_required": True,
        "rename_relative_to_parent_fd": True,
        "root_fd_no_follow": True,
        "staging_fd_pinned": True,
    }
    if not (
        manifest["stage"] == STAGE
        and manifest["base_commit"] == BASE_COMMIT
        and manifest["base_parent"] == BASE_PARENT
        and manifest["base_tree"] == BASE_TREE
        and manifest["base_subject"] == BASE_SUBJECT
        and manifest["public_signature"] == PUBLIC_SIGNATURE
        and manifest["result_fields"] == list(RESULT_FIELDS)
        and manifest["result_field_exact_types"] == list(RESULT_TYPES)
        and manifest["outcome_vocabulary"] == ["passed", "blocked"]
        and manifest["reason_vocabulary"] == list(REASONS)
        and manifest["formal_production_sha256"]
        == EXPECTED_PRODUCTION_SHA256
        and manifest["formal_marker_prefix_sha256"]
        == EXPECTED_PREFIX_SHA256
        and manifest["formal_ast_sha256"] == EXPECTED_AST_SHA256
        and manifest["formal_closure"] == list(FORMAL_CLOSURE)
        and manifest["formal_closure_count"] == 7
        and manifest["actual_evaluator_design_oracle_projection_passed"] == 37
        and manifest["actual_result_negative_projection_rejected"] == 24
        and manifest["truth_matrix_passed"] == 61
        and manifest["source_count"] == 12
        and manifest["issue_transition_count"] == 0
        and manifest["issue_inventory_byte_identical_to_formal_interface"]
        is True
        and manifest["precondition_transition"]["complete_count"] == 49
        and manifest["precondition_transition"]["incomplete_count"] == 2
        and manifest["precondition_transition"][
            "remaining_open_precondition_ids"
        ]
        == ["PRE_048", "PRE_049"]
        and manifest["readiness"] == readiness
        and all(manifest[name] is value for name, value in readiness.items())
        and manifest["current_permission"] is False
        and manifest["authorized_admit_014_download_execution_count"] == 0
        and manifest["adapter_registry_runtime_changed"] is False
        and manifest[
            "mandatory_pre_download_authorization_enforcement_implemented"
        ]
        is False
        and not any(manifest["safety"].values())
        and manifest["materialization_policy"]
        == expected_materialization_policy
        and manifest["output_files"] == list(OUTPUT_FILES)
        and manifest["output_sha256"] == expected_output_sha
        and manifest["source_boundary"] == source_manifest
        and manifest["recommended_next_step"]
        == "design_covapie_admit_014_unified_adapter_contract_v1"
        and manifest["all_checks_passed"] is True
    ):
        raise ValueError("manifest contract drift")
    return manifest


def _lifecycle(
    repo_root: Path = REPO_ROOT,
    base: str = BASE_COMMIT,
    stage_paths: tuple[Path, ...] = STAGE_PATHS,
) -> str:
    if _git(
        ["merge-base", "--is-ancestor", base, "HEAD"], repo_root
    ).returncode:
        raise ValueError("base nonancestor")
    if len(stage_paths) != 10 or len(set(stage_paths)) != 10:
        raise ValueError("Exact10 path drift")
    states = []
    for path in stage_paths:
        target = repo_root / path
        if (
            not target.exists()
            or target.is_symlink()
            or not target.is_file()
            or target.stat().st_size > 100 * 1024 * 1024
            or path.suffix in FORBIDDEN_SUFFIXES
        ):
            raise ValueError(f"unsafe candidate: {path}")
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
        staged = _git(
            ["diff", "--cached", "--name-only", "--", path.as_posix()],
            repo_root,
        )
        working = _git(
            ["diff", "--name-only", "--", path.as_posix()], repo_root
        )
        untracked = _git(
            ["ls-files", "--others", "--exclude-standard", "--", path.as_posix()],
            repo_root,
        )
        if staged.stdout.strip():
            raise ValueError(f"stage path staged: {path}")
        if tracked.returncode == 0:
            if working.stdout.strip() or untracked.stdout.strip():
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
    suffix = "admit_014_rule_logic_interface"
    observed_top = {
        path.relative_to(repo_root)
        for directory in ("src/covalent_ext", "scripts", "tests", "docs")
        for path in (repo_root / directory).glob(f"*{suffix}*")
        if path.is_file() or path.is_symlink()
    }
    if observed_top != set(stage_paths[:4]):
        raise ValueError("same-stage top-level inventory drift")
    roots = sorted((repo_root / OUTPUT_ROOT.parent).glob(f"{OUTPUT_ROOT.name}*"))
    if roots != [repo_root / OUTPUT_ROOT]:
        raise ValueError("same-stage derived root drift")
    if {path.name for path in (repo_root / OUTPUT_ROOT).iterdir()} != set(
        OUTPUT_FILES
    ):
        raise ValueError("Exact6 output inventory drift")
    return states[0]


def _protected_paths() -> None:
    changed = _git(["diff", "--name-only"]).stdout.splitlines()
    protected = (
        "data/raw/", "checkpoints/", "equivariant_diffusion/",
        "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py",
    )
    if any(
        path == item or path.startswith(item)
        for path in changed
        for item in protected
    ):
        raise ValueError("protected path changed")


def check() -> dict:
    _guard()
    sources = _check_base_and_sources()
    _, ast_digests = _check_formal_source()
    module = _load(PRODUCTION_PATH, "_admit014_actual_isolated")
    design = _load(DESIGN_PRODUCTION, "_admit014_design_isolated")
    _check_actual(module, design, sources)
    outputs = _read_outputs(REPO_ROOT / OUTPUT_ROOT)
    manifest = _check_output_semantics(outputs, sources, ast_digests)
    lifecycle = _lifecycle()
    _protected_paths()
    return {
        "checker": "ADMIT_014 standalone evaluator interface v1",
        "base_commit": BASE_COMMIT,
        "lifecycle": lifecycle,
        "source_count": 12,
        "truth_rows": 61,
        "actual_design_rows": 37,
        "negative_result_rows": 24,
        "formal_closure_count": 7,
        "formal_production_sha256": EXPECTED_PRODUCTION_SHA256,
        "formal_marker_prefix_sha256": EXPECTED_PREFIX_SHA256,
        "manifest_sha256": EXPECTED_OUTPUT_SHA256[OUTPUT_FILES[-1]],
        "canonical_evidence_python_implementation": "cpython",
        "canonical_evidence_python_version": "3.10.4",
        "current_permission": False,
        "authorized_admit_014_download_execution_count": 0,
        "recommended_next_step": manifest["recommended_next_step"],
        "all_checks_passed": True,
    }


def main() -> None:
    print(json.dumps(check(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
