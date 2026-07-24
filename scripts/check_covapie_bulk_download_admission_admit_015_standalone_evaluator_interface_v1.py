#!/usr/bin/env python3
"""Independent fail-closed checker for ADMIT_015 standalone evaluator v1."""

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
BASE_COMMIT = "809ec4f8c9494db893d2d66b7551856b2ead4401"
BASE_PARENT = "a7800cfad9f55809d6161c2db12f49c8312165fb"
BASE_TREE = "0a047613fed8bd6094675c8d4bc799284e53c43e"
BASE_SUBJECT = "add CovaPIE ADMIT_015 formal evaluator interface contract v1"
STAGE = "covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1"
PRODUCTION_PATH = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_015_standalone_evaluator_interface.py"
)
CHECKER_PATH = Path(
    "scripts/"
    "check_covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1.py"
)
TEST_PATH = Path(
    "tests/"
    "test_covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1.py"
)
SUMMARY_PATH = Path(
    "docs/"
    "covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1_summary.md"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
OUTPUT_FILES = (
    "covapie_admit_015_standalone_evaluator_interface_contract.csv",
    "covapie_admit_015_standalone_evaluator_interface_truth_matrix.csv",
    "covapie_admit_015_standalone_evaluator_interface_source_boundary_audit.csv",
    "covapie_admit_015_standalone_evaluator_interface_purity_audit.csv",
    "covapie_admit_015_standalone_evaluator_interface_issue_readiness_inventory.csv",
    "covapie_admit_015_standalone_evaluator_interface_manifest.json",
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
TARGET_KEY = "current_stage_training_authorized"
DOWNLOAD_KEY = "current_stage_download_authorized"
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
    "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING",
    "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
    "CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID",
    "TRAINING_NOT_AUTHORIZED",
)
PUBLIC_SIGNATURE = (
    "evaluate_admit_015(*, stage_authorization_context: object = _MISSING) "
    "-> Admit015EvaluationResult"
)
FORMAL_MARKER = "# === ADMIT_015 FORMAL EVALUATOR CLOSURE END ==="
FORMAL_CLOSURE = (
    "_MissingAdmit015Value",
    "_canonical_record_valid",
    "_field_tuple_valid",
    "Admit015EvaluationResult",
    "Admit015EvaluationResult.__post_init__",
    "_make_result",
    "evaluate_admit_015",
)
EXPECTED_PRODUCTION_SHA256 = (
    "eacb5c1ac583649a34cdb9dcde4c004a861da43609b9ffb964a715a427883a82"
)
EXPECTED_PREFIX_SHA256 = (
    "d9c98704ea4464e12c6866d725b5445c566ab0183b67ca1e2e8f53860c47dbf9"
)
EXPECTED_AST_SHA256 = {
    "_MissingAdmit015Value": (
        "c21678cb19cf064c4ebb60df2fb3cf93000cd155bc895baa796a339218168786"
    ),
    "_canonical_record_valid": (
        "9e04222a22ae478a9bd53403c1258f39ba5daa2b5e94c7eb7b51a46510c6c6e0"
    ),
    "_field_tuple_valid": (
        "403164b296b64d7f06e27187dafd6346a9bc22cd24e60b72e9f7f738ecd12374"
    ),
    "Admit015EvaluationResult": (
        "8e7993360580f359cf2a531883509a8521107c6b80d6df6c612767e3b3ac18a8"
    ),
    "Admit015EvaluationResult.__post_init__": (
        "a2d0358aed8dfb6679e1210b690f54b3b4e7f5e4ebe67d413bbe11a43707ff74"
    ),
    "_make_result": (
        "6bd7a06114e040b1aba9d5b27e580a5cd7780f76336836848e7ef32891919a22"
    ),
    "evaluate_admit_015": (
        "b91ce410ddd4cb555952531144e377a7cd296b4b66011c6a2473e683dd39cbed"
    ),
}
EXPECTED_OUTPUT_SHA256 = {
    "covapie_admit_015_standalone_evaluator_interface_contract.csv": (
        "1ad1b44677abf7cd262d5928aee17381e5767dd82880aee689be07cd8b031245"
    ),
    "covapie_admit_015_standalone_evaluator_interface_truth_matrix.csv": (
        "e5e641d590b6a49e536193f7b523605dcfc700cd7196668995fb4ce442561fbf"
    ),
    "covapie_admit_015_standalone_evaluator_interface_source_boundary_audit.csv": (
        "d9499b8851ae79be18c480ba40763c13aabfcee22502266889b4ea09125879d5"
    ),
    "covapie_admit_015_standalone_evaluator_interface_purity_audit.csv": (
        "c5a734085889ff56adce29c23d3f910b088fbcc98ab1c98f08065fb29dbe7cd1"
    ),
    "covapie_admit_015_standalone_evaluator_interface_issue_readiness_inventory.csv": (
        "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec"
    ),
    "covapie_admit_015_standalone_evaluator_interface_manifest.json": (
        "238aadcf819ffc2c30c5de063b1873ce16df59f82cb4be4b4d6222fbdc143758"
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
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_contract_v1"
)
DESIGN_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_contract_design_gate.py"
)
SOURCE_SHA256 = {
    DESIGN_PRODUCTION: (
        "48e2135517cad1ad7744345c3cb5f45e5b29d9c91fd41850eb80a96785e0daa3"
    ),
    FORMAL_ROOT
    / "covapie_admit_015_formal_evaluator_interface_and_result_contract.csv": (
        "5e4e6b3a222ebe65c2ed89e8ce2d98a9ce31043235417bee9d166cb14199651d"
    ),
    FORMAL_ROOT
    / "covapie_admit_015_formal_evaluator_routing_and_consumption_contract.csv": (
        "a0c586281e96f063f67d7c47c1a0b8336a73cb0841b283ca1de64f30fe60cf66"
    ),
    FORMAL_ROOT
    / "covapie_admit_015_formal_evaluator_interface_truth_matrix.csv": (
        "7b09b3c917e4bbc7d140daafa99a9b6a34584ce3a008e9f0193db804c57b4885"
    ),
    FORMAL_ROOT
    / "covapie_admit_015_formal_evaluator_interface_source_boundary_audit.csv": (
        "1725691b3659f4c166289cce17999caa7c13e172199d6df612fe11cf6f38fb43"
    ),
    FORMAL_ROOT
    / "covapie_admit_015_formal_evaluator_interface_issue_readiness_inventory.csv": (
        "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec"
    ),
    FORMAL_ROOT
    / "covapie_admit_015_formal_evaluator_interface_contract_manifest.json": (
        "08ce241290c66e87881c983a563be9f406d904c39e99bd9c6830c78fc3b4b021"
    ),
    Path("data/derived/covalent_small/"
         "covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/"
         "covapie_admit_015_training_authorization_contract_manifest.json"):
        "16ea4bb5f781c6f6d8277fb4142258c2bee4849b942582e48692373caee5cda1",
    Path("data/derived/covalent_small/"
         "covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1/"
         "covapie_admit_015_formal_evaluator_interface_precondition_inventory.csv"):
        "c52287ac5a435e58a400be0e33e17c1096b7b0d3b2671be0398a6be03e409839",
    Path("data/derived/covalent_small/"
         "covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1/"
         "covapie_admit_015_formal_evaluator_interface_preconditions_manifest.json"):
        "7f64389a018c9bc1170ffeb94d1f393aefc27f67edef1d85143659f43dc8d729",
    Path("src/covalent_ext/"
         "covapie_bulk_download_admission_admit_014_rule_logic_interface.py"):
        "5f0766a4eb9dac8b00b9729b7d593adfbe105fb212eabbd4e0a3e349b35f7399",
    Path("data/derived/covalent_small/"
         "covapie_bulk_download_admission_admit_014_rule_logic_interface_v1/"
         "covapie_admit_014_rule_logic_interface_manifest.json"):
        "f1266a2a471ddac3a0966951ff681b19ebd7d2725ff8242942a9365f92f7e056",
    Path("data/derived/covalent_small/"
         "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/"
         "covapie_admit_001_to_014_runtime_manifest.json"):
        "bf7bbe3c2158f661c6e71835bf603af76ffbb315d4ef377c9f72da246619ba40",
    Path("data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/"
         "covapie_feature_semantics_audit_gate_manifest.json"):
        "a625335dd670ceb53f1515237a676c25d156b510eb80113ea8c4073e1ae1879d",
    Path("data/derived/covalent_small/pretrained_masked_loss_smoke_v0/"
         "pretrained_masked_loss_smoke_manifest.json"):
        "f2b3165d70c046f27defbe821afcc5294ff5cdf0037595cd5c42066ab27ea08b",
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
    "admit_015_preconditions_audited",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "admit_015_standalone_signature_frozen",
    "admit_015_formal_result_contract_frozen",
    "admit_015_result_representation_frozen",
    "evaluate_admit_015_implemented",
    "Admit015EvaluationResult_implemented",
    "admit_015_rule_logic_implemented",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_future_evaluator_pure_in_memory_possible",
    "feature_semantics_audit_required_before_training",
    "ready_for_admit_015_unified_adapter_contract_design",
)
FALSE_READINESS = (
    "admit_015_runtime_independent_oracle_implemented",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented",
    "admit_015_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
    "mandatory_training_authorization_enforcement_api_frozen",
    "mandatory_training_authorization_enforcement_implemented",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "feature_semantics_audit_completed",
    "real_training_ready",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)

MANIFEST_KEYS = (
    "Admit015EvaluationResult_implemented",
    "actual_evaluator_independent_oracle_projection_passed",
    "actual_result_negative_projection_rejected",
    "adapter_registry_runtime_changed",
    "admission_rule_id",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "admit_015_formal_result_contract_frozen",
    "admit_015_future_evaluator_pure_in_memory_possible",
    "admit_015_preconditions_audited",
    "admit_015_registered_in_engine",
    "admit_015_result_representation_frozen",
    "admit_015_rule_logic_implemented",
    "admit_015_runtime_independent_oracle_implemented",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_standalone_signature_frozen",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented",
    "all_checks_passed",
    "ast_attestation_cross_python_version_portable",
    "authorized_admit_015_training_execution_count",
    "base_commit",
    "base_parent",
    "base_subject",
    "base_tree",
    "canonical_evidence_python_implementation",
    "canonical_evidence_python_version",
    "canonical_mask_count",
    "canonical_masks",
    "combined_candidate_verdict_implemented",
    "coverage_affected_rules",
    "cross_rule_aggregation_implemented",
    "current_permission",
    "evaluate_admit_015_implemented",
    "feature_semantics_audit_completed",
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
    "historical_feature_semantics_known",
    "historical_unknown_atom_feature_policy_resolved",
    "issue_inventory_byte_identical_to_formal_interface",
    "issue_transition_count",
    "mandatory_training_authorization_enforcement_api_frozen",
    "mandatory_training_authorization_enforcement_implemented",
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
    "public_evaluator",
    "public_signature",
    "purity_closure_complete",
    "python_runtime_migration_policy",
    "readiness",
    "ready_for_admit_015_unified_adapter_contract_design",
    "ready_for_training",
    "real_training_ready",
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
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
)
MANIFEST_OBJECT_KEYS = {
    "formal_ast_sha256": (
        "Admit015EvaluationResult",
        "Admit015EvaluationResult.__post_init__",
        "_MissingAdmit015Value",
        "_canonical_record_valid",
        "_field_tuple_valid",
        "_make_result",
        "evaluate_admit_015",
    ),
    "mapping_consumption_contract": (
        "contains_count",
        "download_key_access_count",
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
        "failure_cleanup_rmdir_forbidden",
        "failure_cleanup_unlink_forbidden",
        "failure_path_non_destructive",
        "failure_staging_retained",
        "gpfs_einval_fails_closed",
        "inode_preserving_exact_set_noop",
        "leaf_and_directory_fsync",
        "leaf_open_dir_fd",
        "o_excl_staging_leaves",
        "os_replace_fallback",
        "output_final_set_traversal",
        "parent_fd_pinned",
        "post_fsync_destination_binding",
        "rename_noreplace_required",
        "rename_relative_to_parent_fd",
        "root_fd_no_follow",
        "source_final_leaf_fd_retained",
        "staging_fd_pinned",
        "staging_lexical_binding_verified",
    ),
    "output_sha256": tuple(sorted(OUTPUT_FILES[:-1])),
    "precondition_transition": (
        "complete_count",
        "implementation_blocking_count",
        "incomplete_count",
        "remaining_open_precondition_ids",
        "row_count",
        "supported_but_not_frozen_count",
    ),
    "readiness": tuple(sorted((*TRUE_READINESS, *FALSE_READINESS))),
    "row_counts": (
        "actual_evaluator_independent_oracle_projection",
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
    leaf_fd = -1
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
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("repository root FD identity drift")
        if _identity(os.lstat(repo_root)) != root_identity:
            raise ValueError("repository root identity drift")
        if _identity(os.fstat(leaf_fd)) != expected_leaf:
            raise ValueError(f"source final FD identity drift: {path}")
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
            raise ValueError(f"source final lexical replacement: {path}")
        return b"".join(chunks)
    finally:
        if leaf_fd >= 0:
            os.close(leaf_fd)
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
    if len(SOURCE_SHA256) != 15:
        raise ValueError("source boundary not Exact15")
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
        "_MissingAdmit015Value",
        "_canonical_record_valid",
        "_field_tuple_valid",
        "Admit015EvaluationResult",
        "_make_result",
        "evaluate_admit_015",
    }:
        raise ValueError("formal definition set drift")
    result_class = definitions["Admit015EvaluationResult"]
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
    evaluator = definitions["evaluate_admit_015"]
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
        or evaluator.returns.id != "Admit015EvaluationResult"
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
        "registry", "dispatcher", "training", "environ", "getenv", "torch",
        "numpy", "pytorch_lightning", "rdkit", "dataset", "dataloader",
        "checkpoint", "model", "forward", "loss", "backward", "optimizer",
        "scheduler", "train", "fit", "save", "build_artifacts",
        "materialize_contract",
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
        "_evaluate_registered_admit_015",
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
        return Probe({DOWNLOAD_KEY: False, TARGET_KEY: True})
    if case_id == "ADMIT015_PLUS_FALSE":
        return Probe({DOWNLOAD_KEY: True, TARGET_KEY: False})
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


def _reject_negative(module, case_id: str) -> str:
    baseline = module.evaluate_admit_015(
        stage_authorization_context={TARGET_KEY: True}
    )
    values = {name: getattr(baseline, name) for name in RESULT_FIELDS}
    if case_id == "WRONG_ADMISSION_RULE_ID":
        values["admission_rule_id"] = "ADMIT_014"
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
        values["canonical_stage_authorization_record"] = ((DOWNLOAD_KEY, True),)
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
        values["validated_stage_authorization_fields"] = (DOWNLOAD_KEY,)
    elif case_id == "DUPLICATE_VALIDATED_FIELD":
        values["validated_stage_authorization_fields"] = (TARGET_KEY, TARGET_KEY)
    elif case_id == "CONSUMED_LIST":
        values["consumed_stage_authorization_fields"] = [TARGET_KEY]
    elif case_id == "CONSUMED_TUPLE_SUBCLASS":
        values["consumed_stage_authorization_fields"] = TupleSubclass((TARGET_KEY,))
    elif case_id == "UNKNOWN_CONSUMED_FIELD":
        values["consumed_stage_authorization_fields"] = (DOWNLOAD_KEY,)
    elif case_id == "DUPLICATE_CONSUMED_FIELD":
        values["consumed_stage_authorization_fields"] = (TARGET_KEY, TARGET_KEY)
    elif case_id == "CANONICAL_VALIDATED_MISMATCH":
        values["validated_stage_authorization_fields"] = ()
    elif case_id == "VALIDATED_CONSUMED_MISMATCH":
        values["consumed_stage_authorization_fields"] = ()
    else:
        raise ValueError(f"unknown negative result case: {case_id}")
    try:
        module.Admit015EvaluationResult(*(values[name] for name in RESULT_FIELDS))
    except (TypeError, ValueError) as error:
        return f"RESULT_CONTRACT_REJECTED:{type(error).__name__}"
    raise ValueError(f"negative result accepted: {case_id}")


def _oracle(case_id: str) -> tuple[object, ...]:
    field = (TARGET_KEY,)
    required = {"OMITTED", "EXPLICIT_NONE", "PROJECTION_OMITTED"}
    nonmapping = {"CONTEXT_OBJECT", "CONTEXT_INT", "CONTEXT_STR", "CONTEXT_LIST"}
    missing = {
        "EMPTY_MAPPING", "UNRELATED_ONLY_MAPPING", "LOOKUP_KEYERROR",
        "PROJECTION_MISSING_KEY",
    }
    lookup_failed = {
        "LOOKUP_RUNTIMEERROR", "LOOKUP_VALUEERROR", "PROJECTION_LOOKUP_FAILED",
    }
    invalid = {
        "INT_ZERO", "INT_ONE", "FLOAT_ZERO", "FLOAT_ONE", "STRING_FALSE",
        "STRING_TRUE", "NONE_VALUE", "LIST_VALUE", "DICT_VALUE",
        "CUSTOM_TRUTHY", "CUSTOM_FALSY", "PROJECTION_INVALID_TYPE",
    }
    false_cases = {"EXACT_FALSE", "ADMIT015_PLUS_FALSE", "PROJECTION_FALSE"}
    true_cases = {
        "EXACT_TRUE", "ADMIT015_PLUS_TRUE", "MANY_EXTRA_PLUS_TRUE",
        "ITERATION_RAISES", "LEN_RAISES", "GET_RAISES", "CONTAINS_RAISES",
        "PROJECTION_TRUE",
    }
    if case_id in required:
        outcome, reason, canonical, validated, consumed = (
            "blocked", REASONS[1], (), (), (),
        )
    elif case_id in nonmapping:
        outcome, reason, canonical, validated, consumed = (
            "blocked", REASONS[2], (), (), (),
        )
    elif case_id in missing:
        outcome, reason, canonical, validated, consumed = (
            "blocked", REASONS[3], (), (), field,
        )
    elif case_id in lookup_failed:
        outcome, reason, canonical, validated, consumed = (
            "blocked", REASONS[4], (), (), field,
        )
    elif case_id in invalid:
        outcome, reason, canonical, validated, consumed = (
            "blocked", REASONS[5], (), (), field,
        )
    elif case_id in false_cases:
        outcome, reason, canonical, validated, consumed = (
            "blocked", REASONS[6], ((TARGET_KEY, False),), field, field,
        )
    elif case_id in true_cases:
        outcome, reason, canonical, validated, consumed = (
            "passed", "", ((TARGET_KEY, True),), field, field,
        )
    else:
        raise ValueError(f"independent oracle case unknown: {case_id}")
    return (
        "ADMIT_015", outcome, outcome == "passed", outcome == "blocked",
        reason, canonical, validated, consumed, False,
    )


def _check_actual(module, sources: dict[Path, bytes]) -> None:
    signature = inspect.signature(module.evaluate_admit_015)
    parameters = tuple(signature.parameters.values())
    if (
        len(parameters) != 1
        or parameters[0].name != "stage_authorization_context"
        or parameters[0].kind is not inspect.Parameter.KEYWORD_ONLY
        or parameters[0].annotation is not object
        or parameters[0].default is not module._MISSING
        or parameters[0].default is None
        or signature.return_annotation is not module.Admit015EvaluationResult
        or tuple(field.name for field in fields(module.Admit015EvaluationResult))
        != RESULT_FIELDS
        or tuple(module.Admit015EvaluationResult.__annotations__.values())
        != (str, str, bool, bool, str, tuple, tuple, tuple, bool)
    ):
        raise ValueError("actual public signature/result drift")
    if str(signature).replace(
        "<covalent_ext.covapie_bulk_download_admission_admit_015_standalone_evaluator_interface.",
        "",
    ) != (
        "(*, stage_authorization_context: object = "
        "<covalent_ext.covapie_bulk_download_admission_admit_015_standalone_evaluator_interface."
        "_MissingAdmit015Value object at "
    ):
        # Exact string is represented in the manifest; inspect properties above
        # are the authoritative runtime check because object repr has an address.
        pass
    try:
        module.evaluate_admit_015(object())
    except TypeError:
        pass
    else:
        raise ValueError("positional call accepted")
    try:
        module.evaluate_admit_015(unknown=True)
    except TypeError:
        pass
    else:
        raise ValueError("unknown keyword accepted")
    truth = list(
        csv.DictReader(
            io.StringIO(
                sources[
                    FORMAL_ROOT
                    / "covapie_admit_015_formal_evaluator_interface_truth_matrix.csv"
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
        actual_kwargs = {} if actual_context is MISSING else {
            "stage_authorization_context": actual_context
        }
        actual = module.evaluate_admit_015(**actual_kwargs)
        left = tuple(getattr(actual, name) for name in RESULT_FIELDS)
        right = _oracle(row["case_id"])
        if not (
            type(actual) is module.Admit015EvaluationResult
            and left == right
            and all(type(a) is type(b) for a, b in zip(left, right, strict=True))
            and actual.evaluator_io_used is False
            and _access_valid(actual_context)
        ):
            raise ValueError(f"actual/independent-oracle mismatch: {row['case_id']}")
    for case_id in NEGATIVE_RESULT_CASES:
        _reject_negative(module, case_id)
    try:
        class ResultSubclass(module.Admit015EvaluationResult):
            pass
    except TypeError:
        pass
    else:
        raise ValueError("result subclass definition accepted")


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
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("Exact6 final output inventory drift")
        for name, descriptor, expected, _ in leaves:
            if (
                _identity(os.fstat(descriptor)) != expected
                or _identity(
                    os.stat(name, dir_fd=root_fd, follow_symlinks=False)
                )
                != expected
            ):
                raise ValueError(f"output final leaf identity drift: {name}")
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(
                os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != root_identity
            or _identity(os.fstat(parent_fd)) != parent_identity
            or _identity(os.lstat(root.parent)) != parent_identity
        ):
            raise ValueError("output final root/parent identity drift")
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


def _parse_manifest_exact(
    data: bytes,
    expected: dict | None = None,
) -> dict:
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
    if expected is not None:
        _assert_exact_object(manifest, expected, "manifest")
    return manifest


def _assert_exact_object(actual: object, expected: object, path: str) -> None:
    if type(actual) is not type(expected):
        raise ValueError(f"{path} exact type mismatch")
    if type(expected) is dict:
        if tuple(actual) != tuple(expected):
            raise ValueError(f"{path} exact schema/order mismatch")
        for key in expected:
            _assert_exact_object(
                actual[key],
                expected[key],
                f"{path}.{key}",
            )
    elif type(expected) is list:
        if len(actual) != len(expected):
            raise ValueError(f"{path} exact list length mismatch")
        for index, (left, right) in enumerate(
            zip(actual, expected, strict=True)
        ):
            _assert_exact_object(left, right, f"{path}[{index}]")
    elif actual != expected:
        raise ValueError(f"{path} exact value mismatch")


def _sort_json_object(value: object) -> object:
    if type(value) is dict:
        return {
            key: _sort_json_object(value[key])
            for key in sorted(value)
        }
    if type(value) is list:
        return [_sort_json_object(item) for item in value]
    return value


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


def _expected_manifest(
    outputs: dict[str, bytes],
    source_manifest: list[dict[str, str]],
    ast_digests: dict[str, str],
) -> dict:
    readiness = {
        **{name: True for name in TRUE_READINESS},
        **{name: False for name in FALSE_READINESS},
    }
    manifest = {
        "manifest_schema_version": (
            "covapie_admit_015_standalone_evaluator_interface_manifest_v1"
        ),
        "project": "CovaPIE",
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "base_parent": BASE_PARENT,
        "base_tree": BASE_TREE,
        "base_subject": BASE_SUBJECT,
        "admission_rule_id": "ADMIT_015",
        "public_evaluator": "evaluate_admit_015",
        "public_signature": PUBLIC_SIGNATURE,
        "parameter_order": ["stage_authorization_context"],
        "parameter_count": 1,
        "private_missing_singleton": True,
        "result_type": "Admit015EvaluationResult",
        "result_fields": list(RESULT_FIELDS),
        "result_field_count": 9,
        "result_field_exact_types": list(RESULT_TYPES),
        "outcome_vocabulary": ["passed", "blocked"],
        "reason_vocabulary": list(REASONS),
        "formal_evaluator_implemented": True,
        "formal_result_type_defined": True,
        "formal_production_sha256": EXPECTED_PRODUCTION_SHA256,
        "formal_marker_prefix_sha256": EXPECTED_PREFIX_SHA256,
        "formal_marker": FORMAL_MARKER,
        "formal_closure": list(FORMAL_CLOSURE),
        "formal_closure_count": 7,
        "formal_ast_sha256": ast_digests,
        "canonical_evidence_python_implementation": "cpython",
        "canonical_evidence_python_version": "3.10.4",
        "ast_attestation_cross_python_version_portable": False,
        "noncanonical_python_policy": (
            "evaluator_semantic_smoke_only; "
            "artifact_build_checker_and_frozen_ast_forbidden"
        ),
        "python_runtime_migration_policy": (
            "explicit_contract_refresh_required"
        ),
        "mapping_consumption_contract": {
            "target_key": TARGET_KEY,
            "target_lookup_exact_count_for_mappings": 1,
            "iteration_count": 0,
            "len_count": 0,
            "get_count": 0,
            "contains_count": 0,
            "download_key_access_count": 0,
            "extra_keys_allowed": True,
        },
        "source_count": 15,
        "source_boundary": source_manifest,
        "source_validation_before_candidate_and_output_read": True,
        "row_counts": {
            "formal_contract": 37,
            "truth_matrix": 61,
            "actual_evaluator_independent_oracle_projection": 37,
            "actual_result_negative_projection": 24,
            "source_boundary": 15,
            "purity_audit": 16,
            "issue_inventory": 30,
        },
        "actual_evaluator_independent_oracle_projection_passed": 37,
        "actual_result_negative_projection_rejected": 24,
        "truth_matrix_passed": 61,
        "purity_closure_complete": True,
        "issue_transition_count": 0,
        "issue_inventory_byte_identical_to_formal_interface": True,
        "coverage_affected_rules": "ADMIT_015",
        "remaining_open_issue_ids": [
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
        ],
        "precondition_transition": {
            "row_count": 45,
            "complete_count": 37,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 8,
            "implementation_blocking_count": 8,
            "remaining_open_precondition_ids": [
                "PRE_031",
                "PRE_032",
                "PRE_033",
                "PRE_034",
                "PRE_035",
                "PRE_036",
                "PRE_038",
                "PRE_042",
            ],
        },
        "readiness": readiness,
        **readiness,
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "adapter_registry_runtime_changed": False,
        "mandatory_training_authorization_enforcement_implemented": False,
        "canonical_masks": [
            {"semantic_name": "warhead_only", "alias": "A"},
            {"semantic_name": "linker_plus_warhead", "alias": "B"},
            {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
            {"semantic_name": "scaffold_only", "alias": "B3"},
            {
                "semantic_name": "scaffold_plus_linker_plus_warhead",
                "alias": "C",
            },
        ],
        "canonical_mask_count": 5,
        "feature_semantics_audit_completed": False,
        "historical_unknown_atom_feature_policy_resolved": False,
        "historical_feature_semantics_known": False,
        "safety": {
            "provider": False,
            "network": False,
            "download": False,
            "raw_read_or_write": False,
            "model_or_checkpoint": False,
            "dataloader": False,
            "training_or_parameter_update": False,
            "combined_candidate_verdict": False,
            "cross_rule_aggregation": False,
            "stage_commit_push": False,
        },
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "materialization_policy": {
            "build_before_mutation": True,
            "exact_output_inventory": True,
            "o_excl_staging_leaves": True,
            "leaf_and_directory_fsync": True,
            "rename_noreplace_required": True,
            "gpfs_einval_fails_closed": True,
            "os_replace_fallback": False,
            "root_fd_no_follow": True,
            "leaf_open_dir_fd": True,
            "inode_preserving_exact_set_noop": True,
            "parent_fd_pinned": True,
            "staging_fd_pinned": True,
            "rename_relative_to_parent_fd": True,
            "destination_name_inode_binding": True,
            "post_fsync_destination_binding": True,
            "complete_exact6_post_read": True,
            "source_final_leaf_fd_retained": True,
            "output_final_set_traversal": True,
            "staging_lexical_binding_verified": True,
            "failure_path_non_destructive": True,
            "failure_staging_retained": True,
            "failure_cleanup_unlink_forbidden": True,
            "failure_cleanup_rmdir_forbidden": True,
        },
        "output_sha256": {
            name: _sha(outputs[name]) for name in OUTPUT_FILES[:-1]
        },
        "recommended_next_step": (
            "design_covapie_admit_015_unified_adapter_contract_v1"
        ),
        "step12d_status": (
            "smoke_legality_only_not_final_training_feature_contract"
        ),
        "feature_semantics_audit_requirement": (
            "required_before_training; historical UNKNOWN_ATOM_FEATURE_POLICY "
            "and feature_semantics_known=False require audit"
        ),
        "all_checks_passed": True,
    }
    expected = _sort_json_object(manifest)
    if type(expected) is not dict:
        raise AssertionError("expected manifest construction failed")
    return expected


def _expected_contract_rows(
    ast_digests: dict[str, str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(
        section: str,
        public_name: str,
        formal_type: str,
        required: bool,
        frozen_value: str,
        formal_invariant: str,
    ) -> None:
        rows.append(
            {
                "contract_order": str(len(rows) + 1),
                "contract_section": section,
                "section_order": str(
                    1
                    + sum(
                        row["contract_section"] == section
                        for row in rows
                    )
                ),
                "public_name": public_name,
                "formal_type": formal_type,
                "required": str(required).lower(),
                "frozen_value": frozen_value,
                "formal_invariant": formal_invariant,
                "implementation_source": "formal_closure",
                "contract_passed": "true",
            }
        )

    add(
        "signature_parameter",
        "stage_authorization_context",
        "object",
        False,
        "keyword_only|private_missing_singleton",
        "one parameter; no positional/varargs/varkw/unknown keyword",
    )
    for name, formal_type in zip(
        RESULT_FIELDS,
        RESULT_TYPES,
        strict=True,
    ):
        add(
            "result_field",
            name,
            formal_type,
            True,
            "Exact9_ordered",
            "exact built-in top-level type and reason-state invariant",
        )
    for reason in REASONS:
        add(
            "reason_vocabulary",
            reason or "<empty>",
            "str",
            True,
            reason,
            "closed Exact7 ordered vocabulary",
        )
    for name in FORMAL_CLOSURE:
        add(
            "formal_closure",
            name,
            "normalized_ast_sha256",
            True,
            ast_digests[name],
            "pure in-memory reachable definition",
        )
    for name, invariant in (
        ("exact_result_type", "type(self) is Admit015EvaluationResult"),
        ("exact_result_storage", "dataclass fields equal RESULT_FIELDS"),
        ("exact_top_level_types", "exact str/bool/tuple only"),
        ("identity", "admission_rule_id == ADMIT_015"),
        ("outcome", "closed passed|blocked"),
        ("reason", "closed Exact7"),
        ("flags", "passed/blocks agree with outcome"),
        ("reason_emptiness", "reason empty iff passed"),
        ("evaluator_io", "evaluator_io_used is exact False"),
        (
            "projection",
            "canonical/validated/consumed agree with reason",
        ),
    ):
        add(
            "result_invariant",
            name,
            "invariant",
            True,
            invariant,
            "fail closed",
        )
    for name in (
        "no_adapter_registry_runtime",
        "no_provider_network_download_raw",
        "no_model_checkpoint_dataloader_training",
    ):
        add(
            "safety_boundary",
            name,
            "boolean",
            True,
            "true",
            "absence attested",
        )
    if len(rows) != 37:
        raise ValueError("independent contract rebuild not Exact37")
    return rows


def _expected_truth_rows(
    committed_formal_truth: list[dict[str, str]],
    production_module,
) -> list[dict[str, str]]:
    inherited = [
        row
        for row in committed_formal_truth
        if row["case_group"] != "signature"
    ]
    if (
        len(committed_formal_truth) != 69
        or len(inherited) != 61
        or len({row["case_id"] for row in inherited}) != 61
    ):
        raise ValueError("committed formal truth Exact69/Exact61 drift")
    rows: list[dict[str, str]] = []
    executable = 0
    negative = 0
    for order, prior in enumerate(inherited, 1):
        case_id = prior["case_id"]
        if prior["case_group"] == "negative_result_contract":
            observed = _reject_negative(production_module, case_id)
            expected = observed
            equal = (
                case_id in NEGATIVE_RESULT_CASES
                and observed.startswith("RESULT_CONTRACT_REJECTED:")
            )
            assertion_kind = (
                "actual_result_malformed_direct_construction_rejected"
            )
            negative += 1
        else:
            context = _context(case_id)
            kwargs = (
                {}
                if context is MISSING
                else {"stage_authorization_context": context}
            )
            actual_result = production_module.evaluate_admit_015(**kwargs)
            actual_values = tuple(
                getattr(actual_result, name) for name in RESULT_FIELDS
            )
            expected_values = _oracle(case_id)
            equal = (
                type(actual_result)
                is production_module.Admit015EvaluationResult
                and actual_values == expected_values
                and all(
                    type(left) is type(right)
                    for left, right in zip(
                        actual_values,
                        expected_values,
                        strict=True,
                    )
                )
                and actual_result.evaluator_io_used is False
                and _access_valid(context)
            )
            expected = repr(expected_values)
            observed = repr(actual_values)
            assertion_kind = (
                "actual_evaluator_independent_oracle_exact9_projection"
            )
            executable += 1
        rows.append(
            {
                "case_order": str(order),
                "case_id": case_id,
                "case_group": prior["case_group"],
                "assertion_kind": assertion_kind,
                "inherited_case_id": case_id,
                "stage_context_representation": prior[
                    "stage_context_representation"
                ],
                "expected_design_result": expected,
                "observed_formal_result": observed,
                "exact_type_value_equality": str(equal).lower(),
                "evaluator_io_used": "false",
                "formal_source": (
                    "evaluate_admit_015|Admit015EvaluationResult"
                ),
                "truth_passed": str(equal).lower(),
            }
        )
    if executable != 37 or negative != 24:
        raise ValueError("independent truth rebuild not Exact37/Exact24")
    return rows


def _expected_purity_rows(
    production_full_sha: str,
    marker_prefix_sha: str,
    ast_digests: dict[str, str],
) -> list[dict[str, str]]:
    reachable_from = (
        "evaluate_admit_015|signature_default",
        "Admit015EvaluationResult.__post_init__",
        "Admit015EvaluationResult.__post_init__",
        "_make_result|root",
        "Admit015EvaluationResult",
        "evaluate_admit_015",
        "root",
    )
    definition_kinds = (
        "private_sentinel_class",
        "function",
        "function",
        "frozen_dataclass",
        "method",
        "function",
        "function",
    )
    rows: list[dict[str, str]] = []
    for index, name in enumerate(FORMAL_CLOSURE):
        rows.append(
            {
                "audit_order": str(index + 1),
                "audit_kind": "closure_definition",
                "definition_name": name,
                "definition_kind": definition_kinds[index],
                "reachable_from": reachable_from[index],
                "normalized_ast_sha256": ast_digests[name],
                "permitted_global_bindings": (
                    "immutable_formal_constants|Mapping|dataclass|fields|"
                    "pure_helpers"
                ),
                "permitted_calls": (
                    "exact_builtins|isinstance|formal_helpers|"
                    "Admit015EvaluationResult"
                ),
                "observed": "reachable_and_frozen",
                "forbidden_io_absent": "true",
                "mutation_absent": "true",
                "dynamic_dispatch_absent": "true",
                "purity_passed": "true",
            }
        )
    metadata = (
        ("production_full_sha256", production_full_sha),
        ("marker_prefix_sha256", marker_prefix_sha),
        ("closure_complete", "|".join(FORMAL_CLOSURE)),
        (
            "reachable_global_bindings",
            "immutable constants|Mapping|dataclass|fields|formal helpers",
        ),
        (
            "forbidden_io",
            "os|pathlib|subprocess|tempfile|json|csv|hashlib|importlib|"
            "environment|socket|requests|urllib|provider|download|raw absent",
        ),
        (
            "forbidden_runtime",
            "evidence_builder|materializer|registry|dispatcher|model|"
            "training absent",
        ),
        (
            "forbidden_dynamic_dispatch",
            "dynamic_import|eval|exec|getattr|globals|locals absent",
        ),
        ("mutable_global_state", "absent"),
        ("purity_closure_complete", "true"),
    )
    for definition_name, observed in metadata:
        rows.append(
            {
                "audit_order": str(len(rows) + 1),
                "audit_kind": "closure_metadata",
                "definition_name": definition_name,
                "definition_kind": "attestation",
                "reachable_from": "checker_recomputed",
                "normalized_ast_sha256": "",
                "permitted_global_bindings": "",
                "permitted_calls": "",
                "observed": observed,
                "forbidden_io_absent": "true",
                "mutation_absent": "true",
                "dynamic_dispatch_absent": "true",
                "purity_passed": "true",
            }
        )
    if len(rows) != 16:
        raise ValueError("independent purity rebuild not Exact16")
    return rows


def _check_output_semantics(
    outputs: dict[str, bytes],
    sources: dict[Path, bytes],
    ast_digests: dict[str, str],
    production_module,
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
    committed_formal_truth = list(
        csv.DictReader(
            io.StringIO(
                sources[
                    FORMAL_ROOT
                    / "covapie_admit_015_formal_evaluator_interface_truth_matrix.csv"
                ].decode(),
                newline="",
            )
        )
    )
    expected_contract = _expected_contract_rows(ast_digests)
    expected_truth = _expected_truth_rows(
        committed_formal_truth,
        production_module,
    )
    expected_purity = _expected_purity_rows(
        EXPECTED_PRODUCTION_SHA256,
        EXPECTED_PREFIX_SHA256,
        ast_digests,
    )
    if contract != expected_contract:
        raise ValueError("Contract Exact37x10 full semantic rebuild drift")
    if truth != expected_truth:
        raise ValueError("Truth Exact61x12 full semantic rebuild drift")
    if purity != expected_purity:
        raise ValueError("Purity Exact16x13 full semantic rebuild drift")
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
        len(source_rows) == 15
        and [row["source_relative_path"] for row in source_rows]
        == [path.as_posix() for path in SOURCE_SHA256]
        and [row["expected_sha256"] for row in source_rows]
        == list(SOURCE_SHA256.values())
        and all(row["source_boundary_passed"] == "true" for row in source_rows)
        and len(issues) == 30
        and outputs[OUTPUT_FILES[4]]
        == sources[
            FORMAL_ROOT
            / "covapie_admit_015_formal_evaluator_interface_issue_readiness_inventory.csv"
        ]
    ):
        raise ValueError("Source/Issue semantic drift")
    expected_manifest = _expected_manifest(
        outputs,
        source_manifest,
        ast_digests,
    )
    manifest = _parse_manifest_exact(
        outputs[OUTPUT_FILES[5]],
        expected_manifest,
    )
    return manifest


STAGE_FAMILY_TOKENS = (
    "admit_015_standalone_evaluator_interface",
    "covapie_bulk_download_admission_admit_015_"
    "standalone_evaluator_interface",
    "covapie_admit_015_standalone_evaluator_interface_contract",
    "covapie_admit_015_standalone_evaluator_interface_truth_matrix",
    "covapie_admit_015_standalone_evaluator_interface_source_boundary_audit",
    "covapie_admit_015_standalone_evaluator_interface_purity_audit",
    "covapie_admit_015_standalone_evaluator_interface_"
    "issue_readiness_inventory",
    "covapie_admit_015_standalone_evaluator_interface_manifest",
)
STAGE_FAMILY_SCAN_ROOTS = (
    Path("src/covalent_ext"),
    Path("scripts"),
    Path("tests"),
    Path("docs"),
)


def _check_ignore(path: Path, repo_root: Path) -> bool:
    result = _git(
        ["check-ignore", "--no-index", "-q", "--", path.as_posix()],
        repo_root,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise ValueError(f"git check-ignore failed closed: {path}")


def _is_stage_family_name(name: str) -> bool:
    candidate = name.lstrip(".")
    return any(token in candidate for token in STAGE_FAMILY_TOKENS)


def _is_stage_family_path(path: Path) -> bool:
    return _is_stage_family_name(path.as_posix())


def _scan_bounded_stage_root(
    scan_root: Path,
    discovered: set[Path],
    repo_root: Path,
) -> None:
    pending = [scan_root]
    while pending:
        current = pending.pop()
        try:
            entries = tuple(os.scandir(repo_root / current))
        except OSError as error:
            raise ValueError(
                f"stage-family scan unavailable: {current}"
            ) from error
        for entry in entries:
            relative = current / entry.name
            if entry.is_symlink():
                raise ValueError(
                    f"symlink blocks no-follow stage-family scan: {relative}"
                )
            if _is_stage_family_path(relative):
                discovered.add(relative)
            if entry.is_dir(follow_symlinks=False):
                pending.append(relative)


def _filesystem_stage_family(
    repo_root: Path,
    exact10: tuple[Path, ...],
) -> set[Path]:
    discovered: set[Path] = set()
    for scan_root in STAGE_FAMILY_SCAN_ROOTS:
        _scan_bounded_stage_root(scan_root, discovered, repo_root)
    derived_parent = OUTPUT_ROOT.parent
    try:
        derived_entries = tuple(os.scandir(repo_root / derived_parent))
    except OSError as error:
        raise ValueError("derived stage-family scan unavailable") from error
    for entry in derived_entries:
        if not _is_stage_family_name(entry.name):
            continue
        relative = derived_parent / entry.name
        discovered.add(relative)
        if entry.is_symlink():
            raise ValueError(f"symlink derived stage-family root: {relative}")
        pending = [relative] if entry.is_dir(follow_symlinks=False) else []
        while pending:
            current = pending.pop()
            try:
                children = tuple(os.scandir(repo_root / current))
            except OSError as error:
                raise ValueError(
                    f"derived stage-family inventory unavailable: {current}"
                ) from error
            for child in children:
                child_relative = current / child.name
                discovered.add(child_relative)
                if child.is_symlink():
                    raise ValueError(
                        f"symlink derived stage-family path: {child_relative}"
                    )
                if child.is_dir(follow_symlinks=False):
                    pending.append(child_relative)
    expected = set(exact10) | {OUTPUT_ROOT}
    for path in sorted(discovered, key=Path.as_posix):
        try:
            item = os.lstat(repo_root / path)
        except OSError as error:
            raise ValueError(
                f"stage-family path vanished during scan: {path}"
            ) from error
        if _check_ignore(path, repo_root):
            raise ValueError(f"ignored stage-family path: {path}")
        if stat.S_ISLNK(item.st_mode):
            raise ValueError(f"symlink stage-family path: {path}")
        if path == OUTPUT_ROOT:
            if not stat.S_ISDIR(item.st_mode):
                raise ValueError("Exact6 parent is not a directory")
            continue
        if (
            not stat.S_ISREG(item.st_mode)
            or item.st_size > 100 * 1024 * 1024
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
        ):
            raise ValueError(f"unsafe stage-family artifact: {path}")
    if discovered != expected:
        raise ValueError("filesystem stage-family allowlist mismatch")
    return discovered


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
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
        ):
            raise ValueError(f"unsafe candidate: {path}")
        if _check_ignore(path, repo_root):
            raise ValueError(f"ignored candidate: {path}")
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
    if {path.name for path in (repo_root / OUTPUT_ROOT).iterdir()} != set(
        OUTPUT_FILES
    ):
        raise ValueError("Exact6 output inventory drift")
    _filesystem_stage_family(repo_root, stage_paths)
    tracked_inventory = _git(["ls-files"], repo_root)
    untracked_inventory = _git(
        ["ls-files", "--others", "--exclude-standard"], repo_root
    )
    if tracked_inventory.returncode or untracked_inventory.returncode:
        raise ValueError("tracked/untracked inventory unavailable")
    stage_related = {
        path
        for path in (
            set(tracked_inventory.stdout.splitlines())
            | set(untracked_inventory.stdout.splitlines())
        )
        if _is_stage_family_path(Path(path))
    }
    if stage_related != {path.as_posix() for path in stage_paths}:
        raise ValueError("extra tracked/untracked stage-family path")
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
    module = _load(PRODUCTION_PATH, "_admit015_actual_isolated")
    _check_actual(module, sources)
    outputs = _read_outputs(REPO_ROOT / OUTPUT_ROOT)
    manifest = _check_output_semantics(
        outputs,
        sources,
        ast_digests,
        module,
    )
    lifecycle = _lifecycle()
    _protected_paths()
    return {
        "checker": "ADMIT_015 standalone evaluator interface v1",
        "base_commit": BASE_COMMIT,
        "lifecycle": lifecycle,
        "source_count": 15,
        "truth_rows": 61,
        "actual_independent_oracle_rows": 37,
        "negative_result_rows": 24,
        "formal_closure_count": 7,
        "formal_production_sha256": EXPECTED_PRODUCTION_SHA256,
        "formal_marker_prefix_sha256": EXPECTED_PREFIX_SHA256,
        "manifest_sha256": EXPECTED_OUTPUT_SHA256[OUTPUT_FILES[-1]],
        "canonical_evidence_python_implementation": "cpython",
        "canonical_evidence_python_version": "3.10.4",
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "recommended_next_step": manifest["recommended_next_step"],
        "all_checks_passed": True,
    }


def main() -> None:
    print(json.dumps(check(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
