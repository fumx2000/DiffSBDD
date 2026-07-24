#!/usr/bin/env python3
"""Independent checker for the ADMIT_015 formal-interface Exact10."""
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
SUBJECT = "add CovaPIE ADMIT_015 download authorization contract v1"
STAGE = (
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_contract_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
CONTRACT = (
    "covapie_admit_015_formal_evaluator_interface_and_result_contract.csv"
)
ROUTING = (
    "covapie_admit_015_formal_evaluator_routing_and_consumption_contract.csv"
)
TRUTH = "covapie_admit_015_formal_evaluator_interface_truth_matrix.csv"
SOURCE = (
    "covapie_admit_015_formal_evaluator_interface_source_boundary_audit.csv"
)
ISSUE = (
    "covapie_admit_015_formal_evaluator_interface_issue_readiness_inventory.csv"
)
MANIFEST = (
    "covapie_admit_015_formal_evaluator_interface_contract_manifest.json"
)
FILES = (CONTRACT, ROUTING, TRUTH, SOURCE, ISSUE, MANIFEST)

PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_contract_design_gate.py"
)
CHECKER = Path(
    "scripts/"
    "check_covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_contract_v1.py"
)
TEST = Path(
    "tests/"
    "test_covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_contract_v1.py"
)
DOC = Path(
    "docs/"
    "covapie_bulk_download_admission_admit_015_"
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
    "48e2135517cad1ad7744345c3cb5f45e5b29d9c91fd41850eb80a96785e0daa3"
)
PRODUCTION_NORMALIZED_AST_SHA256 = (
    "f355af3b7a321cbf7ec91048d2c4c2f405a4b2834664f44a99525ff5539d49c4"
)
OUTPUT_SHA256 = {
    CONTRACT: "5e4e6b3a222ebe65c2ed89e8ce2d98a9ce31043235417bee9d166cb14199651d",
    ROUTING: "a0c586281e96f063f67d7c47c1a0b8336a73cb0841b283ca1de64f30fe60cf66",
    TRUTH: "7b09b3c917e4bbc7d140daafa99a9b6a34584ce3a008e9f0193db804c57b4885",
    SOURCE: "1725691b3659f4c166289cce17999caa7c13e172199d6df612fe11cf6f38fb43",
    ISSUE: "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec",
    MANIFEST: "08ce241290c66e87881c983a563be9f406d904c39e99bd9c6830c78fc3b4b021",
}
FUTURE_SIGNATURE = (
    "evaluate_admit_015(*, stage_authorization_context: object = _MISSING) "
    "-> Admit015EvaluationResult"
)
TARGET_KEY = "current_stage_training_authorized"
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
    "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING",
    "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
    "CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID",
    "TRAINING_NOT_AUTHORIZED",
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
    "da7ae9ac5010422a9fe3c2f9d275943bab3e50f791bb002f1ac931cbacf3bf10"
)

AUTH_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_"
    "download_authorization_contract_v1"
)
PRE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_"
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
            "covapie_bulk_download_admission_admit_015_"
            "download_authorization_contract_design_gate.py"
        ),
        "b2616c01234c899695c08280daacfa21cb137b847a01f5bf6e52e807b0770434",
    ),
    (
        AUTH_ROOT
        / "covapie_admit_015_download_authorization_value_and_trust_contract.csv",
        "b22f02efdd53dce995730a05cc5c12ffa659c2d98b345afc663b118cc104752d",
    ),
    (
        AUTH_ROOT
        / "covapie_admit_015_stage_authorization_routing_and_enforcement_contract.csv",
        "68bc56b214f212ffec359049146e371ac7ce48bed34bfd6bb80313a2fd7046a6",
    ),
    (
        AUTH_ROOT / "covapie_admit_015_failure_taxonomy_and_precedence.csv",
        "1970da57fdec24e9c5b6e518e1dfa7c2103d3bef6da065b24e3d61a296cdeffc",
    ),
    (
        AUTH_ROOT
        / "covapie_admit_015_download_authorization_truth_matrix.csv",
        "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482",
    ),
    (
        AUTH_ROOT / "covapie_admit_015_issue_readiness_inventory.csv",
        "10e3475cb329d517c27fae26636294d0aa69a609a3c59a8b7f0119b0b123edbe",
    ),
    (
        AUTH_ROOT
        / "covapie_admit_015_download_authorization_contract_manifest.json",
        "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
    ),
    (
        PRE_ROOT / "covapie_admit_015_formal_evaluator_precondition_matrix.csv",
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
    "ADMIT_015_STANDALONE_SIGNATURE_UNRESOLVED": (
        "future one-keyword-only signature with private missing singleton frozen"
    ),
    "ADMIT_015_RESULT_CONTRACT_UNRESOLVED": (
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
    "admit_015_preconditions_audited",
    "admit_015_download_authorization_contract_designed",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "admit_015_standalone_signature_frozen",
    "admit_015_formal_result_contract_frozen",
    "admit_015_result_representation_frozen",
    "admit_015_stage_authorization_routing_resolved",
    "admit_015_exact_bool_value_contract_frozen",
    "admit_015_permission_transition_and_precedence_resolved",
    "admit_015_reason_vocabulary_frozen",
    "admit_015_mandatory_pre_download_enforcement_contract_frozen",
    "admit_015_future_evaluator_pure_in_memory_possible",
    "ready_for_admit_015_standalone_evaluator_interface_implementation",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_KEYS = (
    "evaluate_admit_015_implemented",
    "Admit015EvaluationResult_implemented",
    "admit_015_rule_logic_implemented",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented",
    "admit_015_registered_in_engine",
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

# Successor constants intentionally override the mechanically inherited
# ADMIT_014 block above.  The checker owns these expectations independently of
# the candidate production module.
BASE = "a7800cfad9f55809d6161c2db12f49c8312165fb"
PARENT = "4fb86e7d6b8cd27258362cae34eec196b117c265"
TREE = "7f74b75e63e2f949a5ed73b7f7df6aa921235132"
SUBJECT = "add CovaPIE ADMIT_015 training authorization contract v1"
TARGET_KEY = "current_stage_training_authorized"
ADMIT015_KEY = "current_stage_download_authorized"
AUTH_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_"
    "training_authorization_contract_v1"
)
PRE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit_v1"
)
PRECEDENT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_v1"
)
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1"
)
SOURCES = (
    (
        Path(
            "src/covalent_ext/"
            "covapie_bulk_download_admission_admit_015_"
            "training_authorization_contract.py"
        ),
        "77d278f6c0666d9843c86151bb8189836639e89f93b9488c92c5e7169a3d76e1",
    ),
    (
        AUTH_ROOT / "covapie_admit_015_training_authorization_contract.csv",
        "d8cdc33a8debac9959563047b54a0975c5318c09ffefc3b69b9025e8e768254d",
    ),
    (
        AUTH_ROOT / "covapie_admit_015_training_authorization_truth_matrix.csv",
        "bc1070cb7df2db7ee05c4c8aa21ea9563a08974b620d44ee42c193c63b4fb37b",
    ),
    (
        AUTH_ROOT
        / "covapie_admit_015_training_authorization_value_and_trust_contract.csv",
        "eab6be6568b3a8a8fba298eab6fff052184922a70b2893663311d437c6735d7e",
    ),
    (
        AUTH_ROOT
        / "covapie_admit_015_training_authorization_safety_boundary_audit.csv",
        "ed6fb5650716c9135157393eff6b8882781c063c569a5be5aafc550c249969d0",
    ),
    (
        AUTH_ROOT / "covapie_admit_015_issue_readiness_inventory.csv",
        "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec",
    ),
    (
        AUTH_ROOT / "covapie_admit_015_training_authorization_contract_manifest.json",
        "16ea4bb5f781c6f6d8277fb4142258c2bee4849b942582e48692373caee5cda1",
    ),
    (
        PRE_ROOT
        / "covapie_admit_015_formal_evaluator_interface_precondition_inventory.csv",
        "c52287ac5a435e58a400be0e33e17c1096b7b0d3b2671be0398a6be03e409839",
    ),
    (
        PRE_ROOT
        / "covapie_admit_015_formal_evaluator_interface_preconditions_manifest.json",
        "7f64389a018c9bc1170ffeb94d1f393aefc27f67edef1d85143659f43dc8d729",
    ),
    (
        Path(
            "src/covalent_ext/"
            "covapie_bulk_download_admission_admit_014_"
            "formal_evaluator_interface_contract_design_gate.py"
        ),
        "af25eb2f2fb84230b29d2204fff05308626e7f455a7b950aa8efb922607c298e",
    ),
    (
        PRECEDENT_ROOT
        / "covapie_admit_014_formal_evaluator_interface_and_result_contract.csv",
        "7baea79ce0010e31efcf2e70f11350ee5fc05a5c358df3926f9df591da3d3524",
    ),
    (
        PRECEDENT_ROOT
        / "covapie_admit_014_formal_evaluator_routing_and_consumption_contract.csv",
        "9df1faddeb8aa14e8b29af10296222925361cd1f1f98c05a2cc3a2cc64c7f769",
    ),
    (
        PRECEDENT_ROOT / "covapie_admit_014_formal_evaluator_interface_truth_matrix.csv",
        "55dbbddf1f3bcdb4bbd6ce763d7a0c812020241157098c6af18799cc5ffac062",
    ),
    (
        PRECEDENT_ROOT
        / "covapie_admit_014_formal_evaluator_interface_issue_readiness_inventory.csv",
        "d2510c9d2cf7ee1a1fc378e639eb69b68612e818f4e7af10a0e36dc0d788f54d",
    ),
    (
        PRECEDENT_ROOT
        / "covapie_admit_014_formal_evaluator_interface_contract_manifest.json",
        "217490ef69526486b51117e4900d0669b4de466a023023ecb56ebdf0822fb731",
    ),
    (
        RUNTIME_ROOT / "covapie_admit_001_to_014_runtime_manifest.json",
        "bf7bbe3c2158f661c6e71835bf603af76ffbb315d4ef377c9f72da246619ba40",
    ),
    (
        Path(
            "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/"
            "covapie_feature_semantics_audit_gate_manifest.json"
        ),
        "a625335dd670ceb53f1515237a676c25d156b510eb80113ea8c4073e1ae1879d",
    ),
    (
        Path(
            "data/derived/covalent_small/pretrained_masked_loss_smoke_v0/"
            "pretrained_masked_loss_smoke_manifest.json"
        ),
        "f2b3165d70c046f27defbe821afcc5294ff5cdf0037595cd5c42066ab27ea08b",
    ),
)
SOURCE_HEADER = (
    "source_order",
    "source_relative_path",
    "expected_sha256",
    "base_tree_mode",
    "base_tree_blob",
    "index_mode",
    "index_blob",
    "index_stage",
    "base_tree_sha256",
    "filesystem_sha256",
    "tracked",
    "regular_file",
    "non_symlink",
    "pinned_read",
    "post_read_identity_verified",
    "final_leaf_identity_verified",
    "source_verified",
)
TRANSITIONS: dict[str, str] = {}
TRUE_KEYS = (
    "admit_015_preconditions_audited",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "admit_015_standalone_signature_frozen",
    "admit_015_formal_result_contract_frozen",
    "admit_015_result_representation_frozen",
    "admit_015_design_oracle_contract_frozen",
    "admit_015_multi_invalid_precedence_frozen",
    "admit_015_stage_authorization_routing_resolved",
    "admit_015_exact_bool_value_contract_frozen",
    "admit_015_reason_vocabulary_frozen",
    "admit_015_future_evaluator_pure_in_memory_possible",
    "future_mandatory_training_authorization_responsibility_frozen",
    "ready_for_admit_015_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_KEYS = (
    "evaluate_admit_015_implemented",
    "Admit015EvaluationResult_implemented",
    "admit_015_rule_logic_implemented",
    "admit_015_runtime_independent_oracle_implemented",
    "admit_015_standalone_evaluator_implemented",
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
    leaf_fd = -1
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
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("repository root FD identity drift")
        if _identity(os.lstat(repo_root)) != root_identity:
            raise ValueError("repository root identity drift")
        if _identity(os.fstat(leaf_fd)) != expected_leaf:
            raise ValueError("source final FD identity drift")
        if (
            _identity(
                os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != expected_leaf
        ):
            raise ValueError("source final lexical replacement")
        return b"".join(chunks)
    finally:
        if leaf_fd >= 0:
            os.close(leaf_fd)
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
    if len(SOURCES) != 18 or len(set(path for path, _ in SOURCES)) != 18:
        raise ValueError("source boundary not Exact18")
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


def _parse_manifest_exact(
    data: bytes,
    expected: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        manifest = json.loads(
            data.decode(), object_pairs_hook=_pairs_no_duplicates
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("manifest JSON invalid") from error
    if type(manifest) is not dict:
        raise ValueError("manifest object required")
    if expected is not None:
        _assert_exact_object(manifest, expected, "manifest")
    return manifest


def _assert_exact_object(actual: Any, expected: Any, path: str) -> None:
    if type(actual) is not type(expected):
        raise ValueError(f"{path} exact type mismatch")
    if type(expected) is dict:
        if tuple(actual) != tuple(expected):
            raise ValueError(f"{path} exact schema/order mismatch")
        for key in expected:
            _assert_exact_object(actual[key], expected[key], f"{path}.{key}")
    elif type(expected) is list:
        if len(actual) != len(expected):
            raise ValueError(f"{path} list length mismatch")
        for index, (left, right) in enumerate(
            zip(actual, expected, strict=True)
        ):
            _assert_exact_object(left, right, f"{path}[{index}]")
    elif actual != expected:
        raise ValueError(f"{path} value mismatch")


def _rows(data: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(data.decode(), newline=""))
    if (
        not reader.fieldnames
        or len(reader.fieldnames) != len(set(reader.fieldnames))
    ):
        raise ValueError("CSV duplicate/empty header")
    return list(reader)


def _admit015_successor_text(value: str) -> str:
    """Apply the narrow precedent-to-successor semantic mapping."""
    return (
        value.replace(
            "current_stage_training_authorized",
            "__ADMIT015_DOWNLOAD_COEXISTENCE_KEY__",
        )
        .replace(
            "current_stage_download_authorized",
            "current_stage_training_authorized",
        )
        .replace(
            "__ADMIT015_DOWNLOAD_COEXISTENCE_KEY__",
            "current_stage_download_authorized",
        )
        .replace(
            "CURRENT_STAGE_DOWNLOAD_AUTHORIZED",
            "CURRENT_STAGE_TRAINING_AUTHORIZED",
        )
        .replace("BULK_DOWNLOAD_NOT_AUTHORIZED", "TRAINING_NOT_AUTHORIZED")
        .replace("ADMIT_014", "ADMIT_015")
        .replace("Admit014", "Admit015")
        .replace("admit_014", "admit_015")
    )


def _successor_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {key: _admit015_successor_text(value) for key, value in row.items()}
        for row in rows
    ]


def _expected_source_rows(
    sources: dict[Path, bytes],
) -> list[dict[str, str]]:
    if tuple(sources) != tuple(path for path, _ in SOURCES):
        raise ValueError("source snapshot name/order mismatch")
    rows = []
    for order, (path, digest) in enumerate(SOURCES, 1):
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
            or hashlib.sha256(sources[path]).hexdigest() != digest
        ):
            raise ValueError(f"independent source metadata drift: {path}")
        rows.append(
            {
                "source_order": str(order),
                "source_relative_path": path.as_posix(),
                "expected_sha256": digest,
                "base_tree_mode": tree_fields[0],
                "base_tree_blob": tree_fields[2],
                "index_mode": index_fields[0],
                "index_blob": index_fields[1],
                "index_stage": "0",
                "base_tree_sha256": digest,
                "filesystem_sha256": digest,
                "tracked": "true",
                "regular_file": "true",
                "non_symlink": "true",
                "pinned_read": "true",
                "post_read_identity_verified": "true",
                "final_leaf_identity_verified": "true",
                "source_verified": "true",
            }
        )
    return rows


def _expected_transition(sources: dict[Path, bytes]) -> str:
    rows = _rows(
        sources[
            PRE_ROOT
            / "covapie_admit_015_formal_evaluator_interface_precondition_inventory.csv"
        ]
    )
    authorization_resolved = {
        "PRE_007",
        "PRE_008",
        "PRE_009",
        "PRE_010",
        "PRE_011",
        "PRE_012",
        "PRE_016",
        "PRE_017",
        "PRE_018",
        "PRE_025",
        "PRE_026",
        "PRE_027",
    }
    interface_resolved = {
        "PRE_019",
        "PRE_020",
        "PRE_021",
        "PRE_022",
        "PRE_023",
        "PRE_024",
    }
    for row in rows:
        identifier = row["precondition_id"]
        if identifier in authorization_resolved:
            row["observed_state"] = (
                "frozen by ADMIT_015 training authorization contract v1"
            )
            row["completion_status"] = "complete"
            row["implementation_blocking"] = "false"
            row["resolution_or_gap"] = "authorization contract frozen"
        elif identifier in interface_resolved:
            row["observed_state"] = (
                "frozen by ADMIT_015 formal evaluator interface contract v1"
            )
            row["completion_status"] = "complete"
            row["implementation_blocking"] = "false"
            row["resolution_or_gap"] = (
                "formal interface and result design contract frozen"
            )
    if not (
        len(rows) == 45
        and sum(row["completion_status"] == "complete" for row in rows) == 37
        and sum(
            row["completion_status"] == "supported_but_not_frozen"
            for row in rows
        )
        == 0
        and sum(row["completion_status"] == "incomplete" for row in rows) == 8
        and sum(row["implementation_blocking"] == "true" for row in rows) == 8
        and [
            row["precondition_id"]
            for row in rows
            if row["completion_status"] != "complete"
        ]
        == [
            "PRE_031",
            "PRE_032",
            "PRE_033",
            "PRE_034",
            "PRE_035",
            "PRE_036",
            "PRE_038",
            "PRE_042",
        ]
    ):
        raise ValueError("independent precondition 37/0/8/8 drift")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=tuple(rows[0]),
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return hashlib.sha256(stream.getvalue().encode()).hexdigest()


def _expected_manifest(
    payloads: dict[str, bytes],
    source_rows: list[dict[str, str]],
    truth: list[dict[str, str]],
    transition_sha: str,
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    readiness = {
        **{key: True for key in TRUE_KEYS},
        **{key: False for key in FALSE_KEYS},
    }
    group_counts = {
        group: sum(row["case_group"] == group for row in truth)
        for group in dict.fromkeys(row["case_group"] for row in truth)
    }
    output_sha = {
        name: hashlib.sha256(payloads[name]).hexdigest()
        for name in FILES[:-1]
    }
    issue_source_sha = next(
        digest
        for path, digest in SOURCES
        if path
        == AUTH_ROOT / "covapie_admit_015_issue_readiness_inventory.csv"
    )
    manifest: dict[str, Any] = {
        "project": "CovaPIE",
        "stage": STAGE,
        "manifest_schema_version": (
            "covapie_admit_015_formal_evaluator_interface_contract_manifest_v1"
        ),
        "base_commit": BASE,
        "base_parent": PARENT,
        "base_tree": TREE,
        "base_subject": SUBJECT,
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
        "admission_rule_id": "ADMIT_015",
        "future_function_name": "evaluate_admit_015",
        "future_result_type_name": "Admit015EvaluationResult",
        "future_public_signature": FUTURE_SIGNATURE,
        "signature_parameters": ["stage_authorization_context"],
        "signature_parameter_count": 1,
        "signature_all_keyword_only": True,
        "signature_parameter_annotation": "object",
        "signature_private_missing_singleton_default": True,
        "signature_varargs": False,
        "signature_varkw": False,
        "signature_forbidden_parameters": [
            "candidate_record",
            "batch_context",
            "evaluation_context",
            "download_result_context",
            "provider_result",
            "policy_mapping",
            "fallback_envelope",
            "current_stage_training_authorized",
            "current_stage_download_authorized",
        ],
        "formal_evaluator_implemented": False,
        "formal_result_type_defined": False,
        "design_oracle": (
            "classify_admit_015_formal_evaluator_interface_design"
        ),
        "design_result_type": "Admit015EvaluationResultContractDesign",
        "result_fields": list(RESULT_FIELDS),
        "result_field_count": 9,
        "result_field_exact_types": list(RESULT_TYPES),
        "result_dataclass_frozen": True,
        "result_subclassing_forbidden": True,
        "canonical_stage_authorization_record_representation": {
            "empty": "()",
            "false": "(('current_stage_training_authorized', False),)",
            "true": "(('current_stage_training_authorized', True),)",
            "outer_type": "exact tuple",
            "pair_type": "exact tuple",
            "value_type": "exact bool",
        },
        "validated_stage_authorization_fields_representation": [
            "()",
            "('current_stage_training_authorized',)",
        ],
        "consumed_stage_authorization_fields_representation": [
            "()",
            "('current_stage_training_authorized',)",
        ],
        "outcome_vocabulary": ["passed", "blocked"],
        "reason_vocabulary": list(REASONS),
        "failure_precedence": list(REASONS[1:] + ("",)),
        "result_invariants": [
            "admission_rule_id == ADMIT_015",
            "passed == (outcome == passed)",
            "blocks_candidate == (outcome == blocked)",
            "reason empty iff outcome passed",
            "blocked iff reason is one of six blocker reasons",
            "evaluator_io_used is exact false",
        ],
        "projection_contract": {
            "omitted": ["()", "()", "()"],
            "explicit_none": ["()", "()", "()"],
            "non_mapping": ["()", "()", "()"],
            "missing_key": [
                "()",
                "()",
                "('current_stage_training_authorized',)",
            ],
            "lookup_failure": [
                "()",
                "()",
                "('current_stage_training_authorized',)",
            ],
            "invalid_type": [
                "()",
                "()",
                "('current_stage_training_authorized',)",
            ],
            "exact_false": [
                "(('current_stage_training_authorized', False),)",
                "('current_stage_training_authorized',)",
                "('current_stage_training_authorized',)",
            ],
            "exact_true": [
                "(('current_stage_training_authorized', True),)",
                "('current_stage_training_authorized',)",
                "('current_stage_training_authorized',)",
            ],
        },
        "mapping_consumption_contract": {
            "target_key": TARGET_KEY,
            "target_lookup_maximum_count": 1,
            "iteration_count": 0,
            "len_count": 0,
            "get_count": 0,
            "contains_count": 0,
            "extra_keys_allowed": True,
            "download_coexistence_key": ADMIT015_KEY,
            "download_key_access_count": 0,
        },
        "truth_matrix_schema": list(TRUTH_HEADER),
        "truth_matrix_row_count": 69,
        "truth_matrix_positive_row_count": 45,
        "truth_matrix_negative_result_row_count": 24,
        "truth_matrix_group_counts": group_counts,
        "truth_matrix_signature_meta_semantics": {
            "row_count": 8,
            "property_rows": 6,
            "property_meta_outcome": "verified",
            "rejection_rows": 2,
            "rejection_meta_outcome": "rejected",
            "rejection_reason": "TypeError",
            "generated_by_real_signature_introspection_bind_and_invocation": True,
            "meta_outcomes_are_formal_evaluator_outcomes": False,
        },
        "truth_matrix_all_cases_passed": True,
        "precondition_transition": {
            "row_count": 45,
            "complete_count": 37,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 8,
            "implementation_blocking_count": 8,
            "resolved_precondition_ids": [
                "PRE_019",
                "PRE_020",
                "PRE_021",
                "PRE_022",
                "PRE_023",
                "PRE_024",
            ],
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
            "transition_rows_sha256": transition_sha,
        },
        "issue_continuity": {
            "row_count": 30,
            "transition_count": 0,
            "inventory_source_sha256": issue_source_sha,
            "byte_identical_to_training_authorization_contract": True,
            "coverage": ["ADMIT_015"],
            "coverage_issue_open": True,
        },
        "remaining_open_issue_ids": list(GLOBAL_OPEN),
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "synthetic_true_design_case_grants_current_permission": False,
        "synthetic_true_design_case_starts_real_training": False,
        "future_mandatory_training_authorization_responsibility": {
            "frozen": True,
            "api_frozen": False,
            "implemented": False,
            "evaluate_once_each_real_training_invocation": True,
            "must_complete_before_any_protected_operation": True,
            "blocked_must_not_continue": True,
            "combined_verdict_may_override_blocked": False,
        },
        "unified_adapter_contract_frozen": False,
        "unified_adapter_implemented": False,
        "admit_015_registered_in_engine": False,
        "unified_dispatch_runtime_with_admit_001_to_015_implemented": False,
        "source_count": 18,
        "source_boundary_schema": list(SOURCE_HEADER),
        "source_boundary": [
            {
                "order": int(row["source_order"]),
                "path": row["source_relative_path"],
                "sha256": row["expected_sha256"],
                "base_tree_mode": row["base_tree_mode"],
                "base_tree_blob": row["base_tree_blob"],
                "index_mode": row["index_mode"],
                "index_blob": row["index_blob"],
                "index_stage": int(row["index_stage"]),
                "base_tree_filesystem_byte_equal": True,
                "pinned_no_follow_read": True,
                "post_read_identity_verified": True,
                "final_leaf_fd_retained": True,
            }
            for row in source_rows
        ],
        "source_validation_before_candidate_and_output_read": True,
        "readiness": readiness,
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
        "canonical_mask_long_names_are_authoritative": True,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "historical_unknown_atom_feature_policy_resolved": False,
        "historical_feature_semantics_known": False,
        "safety": {
            "formal_evaluator_or_result": False,
            "adapter_registry_runtime": False,
            "mandatory_enforcement_implementation": False,
            "provider": False,
            "network": False,
            "download": False,
            "raw_read_or_write": False,
            "model_or_checkpoint": False,
            "dataloader": False,
            "training_or_parameter_update": False,
            "combined_candidate_verdict": False,
            "cross_rule_aggregation": False,
            "current_main_stage_commit_push": False,
        },
        "exact6_schemas": {
            CONTRACT: list(CONTRACT_HEADER),
            ROUTING: list(ROUTING_HEADER),
            TRUTH: list(TRUTH_HEADER),
            SOURCE: list(SOURCE_HEADER),
            ISSUE: list(issues[0]),
            MANIFEST: "closed JSON contract asserted by independent checker",
        },
        "exact6_row_counts": {
            CONTRACT: 22,
            ROUTING: 8,
            TRUTH: 69,
            SOURCE: 18,
            ISSUE: 30,
        },
        "output_file_count": 6,
        "output_files": list(FILES),
        "output_sha256": output_sha,
        "output_sha256_excludes_manifest_self_hash": True,
        "renameat2_policy": (
            "RENAME_NOREPLACE_required; GPFS_EINVAL_fails_closed; "
            "no_os_replace_fallback"
        ),
        "materialization": {
            "build_before_mutation": True,
            "exclusive_leaf_create": True,
            "rename_noreplace_required": True,
            "gpfs_einval_fails_closed": True,
            "os_replace_forbidden": True,
            "inode_preserving_exact_noop": True,
            "pinned_post_read_verification": True,
            "source_final_leaf_fd_retained": True,
            "output_final_set_traversal": True,
            "staging_lexical_binding_verified": True,
            "ownership_safe_cleanup": True,
            "failure_cleanup_is_non_destructive": True,
            "failure_cleanup_unlink_forbidden": True,
            "failure_cleanup_rmdir_forbidden": True,
            "failure_staging_may_be_retained": True,
            "concurrent_eexist_fails_closed": True,
            "preexisting_exact_destination_is_noop": True,
            "successful_publish_has_no_staging_residue": True,
            "unknown_identity_objects_are_never_deleted": True,
            "nested_exact_bool_types_verified": True,
            "bool_int_equivalence_rejected": True,
            "ignored_extra_stage_artifacts_rejected": True,
            "extra_derived_roots_rejected": True,
        },
        "step12d_status": (
            "smoke_legality_only_not_final_training_feature_contract"
        ),
        "feature_semantics_note": (
            "historical UNKNOWN_ATOM_FEATURE_POLICY and "
            "feature_semantics_known=false require an explicit "
            "feature-semantics audit before training"
        ),
        "recommended_next_step": (
            "implement_covapie_admit_015_standalone_evaluator_interface_v1"
        ),
        "all_checks_passed": True,
    }
    manifest.update(readiness)
    return manifest


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
    normalized = ast.dump(
        tree, annotate_fields=True, include_attributes=False
    ).encode()
    if hashlib.sha256(normalized).hexdigest() != PRODUCTION_NORMALIZED_AST_SHA256:
        raise ValueError("candidate production normalized AST mismatch")
    forbidden = {
        "evaluate_admit_015",
        "Admit015EvaluationResult",
        "_evaluate_registered_admit_015",
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
        or parameters[0].default is not module._MISSING
        or parameters[0].default is None
        or signature.return_annotation != "Admit015EvaluationResult"
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
            module.Admit015EvaluationResultContractDesign
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
    classify = module.classify_admit_015_formal_evaluator_interface_design
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
            or module.validate_admit_015_evaluation_result_contract_design(
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
        {"admission_rule_id": "ADMIT_014"},
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
            module.Admit015EvaluationResultContractDesign(
                *(values[name] for name in RESULT_FIELDS)
            )
        except (TypeError, ValueError):
            continue
        raise ValueError(f"negative result contract accepted: {mutation}")


FORBIDDEN_SUFFIXES = {
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
STAGE_FAMILY_TOKENS = (
    "admit_015_formal_evaluator_interface_contract",
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_contract",
    "covapie_admit_015_formal_evaluator_interface_and_result_contract",
    "covapie_admit_015_formal_evaluator_routing_and_consumption_contract",
    "covapie_admit_015_formal_evaluator_interface_truth_matrix",
    "covapie_admit_015_formal_evaluator_interface_source_boundary_audit",
    "covapie_admit_015_formal_evaluator_interface_issue_readiness_inventory",
    "covapie_admit_015_formal_evaluator_interface_contract_manifest",
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
    """Find stage-family paths with a bounded recursive no-follow scan."""
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
    base: str = BASE,
    exact10: tuple[Path, ...] = EXACT10,
) -> str:
    if _git(
        ["merge-base", "--is-ancestor", base, "HEAD"], repo_root
    ).returncode:
        raise ValueError("base nonancestor")
    if len(exact10) != 10 or len(set(exact10)) != 10:
        raise ValueError("Exact10 path contract drift")
    states = []
    for path in exact10:
        target = repo_root / path
        if (
            not target.exists()
            or target.is_symlink()
            or target.stat().st_size > 100 * 1024 * 1024
        ):
            raise ValueError(f"unsafe candidate: {path}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise ValueError("forbidden candidate suffix")
        if _check_ignore(path, repo_root):
            raise ValueError(f"ignored candidate: {path}")
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
    if {
        path.name for path in (repo_root / OUTPUT_ROOT).iterdir()
    } != set(FILES):
        raise ValueError("missing or seventh Exact6 output")
    _filesystem_stage_family(repo_root, exact10)
    tracked_inventory = _git(["ls-files"], repo_root)
    untracked_inventory = _git(
        ["ls-files", "--others", "--exclude-standard"], repo_root
    )
    if tracked_inventory.returncode or untracked_inventory.returncode:
        raise ValueError("tracked/untracked inventory unavailable")
    inherited_issue_sources = {
        path.as_posix() for path, _ in SOURCES if path.name == ISSUE
    }
    stage_related = {
        path
        for path in (
            set(tracked_inventory.stdout.splitlines())
            | set(untracked_inventory.stdout.splitlines())
        )
        if (
            _is_stage_family_path(Path(path))
            and path not in inherited_issue_sources
        )
    }
    if stage_related != {path.as_posix() for path in exact10}:
        raise ValueError("extra tracked/untracked stage-family path")
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


def verify_exact6_semantics(
    payloads: dict[str, bytes],
    sources: dict[Path, bytes],
    candidate_module: Any,
) -> dict[str, Any]:
    if tuple(payloads) != FILES:
        raise ValueError("Exact6 name/order mismatch")
    if tuple(OUTPUT_SHA256) != FILES:
        raise ValueError("frozen SHA map name/order mismatch")
    for name in FILES:
        if hashlib.sha256(payloads[name]).hexdigest() != OUTPUT_SHA256[name]:
            raise ValueError(f"frozen output SHA mismatch: {name}")

    expected_contract = _successor_rows(
        _rows(
            sources[
                PRECEDENT_ROOT
                / "covapie_admit_014_formal_evaluator_interface_and_result_contract.csv"
            ]
        )
    )
    expected_routing = _successor_rows(
        _rows(
            sources[
                PRECEDENT_ROOT
                / "covapie_admit_014_formal_evaluator_routing_and_consumption_contract.csv"
            ]
        )
    )
    expected_truth = _successor_rows(
        _rows(
            sources[
                PRECEDENT_ROOT
                / "covapie_admit_014_formal_evaluator_interface_truth_matrix.csv"
            ]
        )
    )
    expected_source = _expected_source_rows(sources)
    contract = _rows(payloads[CONTRACT])
    routing = _rows(payloads[ROUTING])
    truth = _rows(payloads[TRUTH])
    source_rows = _rows(payloads[SOURCE])
    issues = _rows(payloads[ISSUE])
    if contract != expected_contract:
        raise ValueError("independent Exact22 successor rebuild mismatch")
    if routing != expected_routing:
        raise ValueError("independent Exact8 routing rebuild mismatch")
    if truth != expected_truth:
        raise ValueError("independent Exact69 precedent rebuild mismatch")
    if source_rows != expected_source:
        raise ValueError("independent Exact18 source rebuild mismatch")
    if payloads[ISSUE] != sources[
        AUTH_ROOT / "covapie_admit_015_issue_readiness_inventory.csv"
    ]:
        raise ValueError("Exact30 issue bytes are not inherited byte-identically")
    if not (
        tuple(contract[0]) == CONTRACT_HEADER
        and tuple(routing[0]) == ROUTING_HEADER
        and tuple(truth[0]) == TRUTH_HEADER
        and tuple(source_rows[0]) == SOURCE_HEADER
        and len(contract) == 22
        and len(routing) == 8
        and len(truth) == 69
        and len(source_rows) == 18
        and len(issues) == 30
    ):
        raise ValueError("Exact6 schema/count drift")
    by_id = {row["issue_id"]: row for row in issues}
    if any(
        by_id[issue]["successor_effective_status"] != "open"
        for issue in GLOBAL_OPEN
    ):
        raise ValueError("required global issue closed")
    if (
        by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
            "affected_rules"
        ]
        != "ADMIT_015"
    ):
        raise ValueError("coverage affected-rules drift")
    transition_sha = _expected_transition(sources)
    expected_manifest = _expected_manifest(
        payloads,
        expected_source,
        expected_truth,
        transition_sha,
        issues,
    )
    manifest = _parse_manifest_exact(payloads[MANIFEST], expected_manifest)
    if MANIFEST in manifest["output_sha256"]:
        raise ValueError("manifest self hash forbidden")
    _validate_signature_and_oracle(candidate_module)
    return manifest


def validate() -> str:
    _guard()
    sources = _source_snapshot()
    module = _validate_ast_and_load()
    lifecycle = _lifecycle()
    outputs = _pinned_outputs(REPO_ROOT / OUTPUT_ROOT)
    verify_exact6_semantics(outputs, sources, module)
    _validate_protected_paths()
    return lifecycle


def main() -> int:
    lifecycle = validate()
    print(f"stage={STAGE}")
    print(f"base_commit={BASE}")
    print("canonical_evidence_python=cpython-3.10.4")
    print("source_count=18")
    print(f"future_public_signature={FUTURE_SIGNATURE}")
    print("result_field_count=9")
    print("truth_matrix_rows=69")
    print("truth_matrix_negative_result_rows=24")
    print("precondition_complete=37")
    print("precondition_supported_but_not_frozen=0")
    print("precondition_open=8")
    print("issue_rows=30")
    print("issue_transitions=0")
    print("remaining_open_admit_015_coverage=ADMIT_015")
    print("current_permission=false")
    print("authorized_admit_015_training_execution_count=0")
    print("formal_evaluator_implemented=false")
    print("formal_result_type_defined=false")
    print("adapter_registry_runtime_implemented=false")
    print("mandatory_enforcement_implemented=false")
    print(
        "recommended_next_step="
        "implement_covapie_admit_015_standalone_evaluator_interface_v1"
    )
    print(f"lifecycle={lifecycle}")
    print(f"{STAGE}_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
