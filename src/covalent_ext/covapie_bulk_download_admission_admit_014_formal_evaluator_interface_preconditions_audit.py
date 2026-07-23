"""Read-only ADMIT_014 formal-evaluator interface precondition audit.

This module audits committed metadata pinned to ``BASE_COMMIT``.  It does not
implement an evaluator, result type, adapter, registry entry, combined
verdict, provider mapping, download operation, raw-data access, or training.
"""
from __future__ import annotations

import ast
import csv
import ctypes
import errno
import hashlib
import io
import json
import os
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "3ec07b2daa7e6fc2d51df2641e85c13be2196ff3"
BASE_PARENT = "dd17566f1b82eebcaaa49f17172a7b22a83b9c53"
BASE_TREE = "2d0f838cf2d7c4b197fd8ca44d0f6f5cb66b3750"
BASE_SUBJECT = "add CovaPIE unified dispatch runtime with ADMIT_001 to ADMIT_013 v1"
PREDECESSOR_PRODUCTION_SHA256 = (
    "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892"
)
STAGE = (
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_preconditions_audit_v1"
)
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / (
    "covapie_bulk_download_admission_admit_014_"
    "rule_logic_interface_preconditions_audit_v1"
)

ADMISSION_RULE_ID = "ADMIT_014"
ADMISSION_RULE_NAME = "current_gate_grants_no_download_permission"
EVIDENCE_SOURCE = "current_design_gate"
REQUIRED_STATUS = "bulk_download_not_authorized_now"
FAILURE_SEVERITY = "blocking"
BLOCKING_REASON = "bulk_download_not_authorized"
EVALUATION_PHASE = "current_step"
NETWORK_REQUIRED = False
RAW_STRUCTURE_REQUIRED = False
READY_FOR_FUTURE_IMPLEMENTATION = True
ADMIT_014_EVALUATOR_MODEL = "future_explicit_authorization_context"
ADMIT_014_AUTHORIZATION_CONTEXT_ITEM = "current_stage_download_authorized"
ADMIT_014_CONTEXT_SCOPE = "stage"
ADMIT_014_PROVIDED_BY = "future_caller"
ADMIT_014_CANDIDATE_FIELD_DEPENDENCIES: tuple[str, ...] = ()
ADMIT_014_BATCH_CONTEXT_DEPENDENCIES: tuple[str, ...] = ()

CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = "3.10.4"
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_014_download_authorization_contract_v1"

PRECONDITION = "covapie_admit_014_formal_evaluator_precondition_matrix.csv"
AUTHORIZATION = (
    "covapie_admit_014_authorization_evidence_and_routing_responsibility_matrix.csv"
)
CURRENT_STATE = "covapie_admit_014_current_gate_observed_state_inventory.csv"
SOURCE_AUDIT = "covapie_admit_014_source_boundary_audit.csv"
ISSUE = "covapie_admit_014_issue_readiness_inventory.csv"
MANIFEST = "covapie_admit_014_formal_evaluator_preconditions_manifest.json"
FILES = (PRECONDITION, AUTHORIZATION, CURRENT_STATE, SOURCE_AUDIT, ISSUE, MANIFEST)

COLUMNS = {
    PRECONDITION: (
        "precondition_order",
        "precondition_id",
        "precondition_group",
        "precondition_subject",
        "expected_contract",
        "observed_evidence",
        "completeness_status",
        "implementation_blocking",
        "blocking_reason",
        "precondition_passed",
    ),
    AUTHORIZATION: (
        "matrix_order",
        "matrix_group",
        "case_id",
        "authority_or_envelope",
        "committed_evidence",
        "authority_classification",
        "current_observed_state",
        "future_contract_requirement",
        "completeness_status",
        "implementation_blocking",
        "blocking_reason",
        "case_passed",
    ),
    CURRENT_STATE: (
        "inventory_order",
        "state_item",
        "source_path",
        "source_field_or_row",
        "expected_current_state",
        "observed_current_state",
        "authority_classification",
        "state_passed",
    ),
    SOURCE_AUDIT: (
        "source_order",
        "source_relative_path",
        "expected_sha256",
        "base_tree_mode",
        "tracked",
        "base_tree_blob",
        "filesystem_regular",
        "non_symlink",
        "parent_chain_non_symlink",
        "safe_descendant",
        "pinned_fd_read",
        "post_read_identity_verified",
        "source_verified",
    ),
}

DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
PRECONDITION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_"
    "implementation_precondition_gate_v1"
)
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1"
)
QA_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_qa_gate_v1")

DESIGN_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate.py"
)
DESIGN_RULES = DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"
DESIGN_SAFETY = DESIGN_ROOT / "covapie_bulk_download_admission_safety_audit.csv"
DESIGN_MANIFEST = DESIGN_ROOT / "covapie_bulk_download_admission_design_gate_manifest.json"
PRECONDITION_RULES = (
    PRECONDITION_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"
)
PRECONDITION_CONTEXT = (
    PRECONDITION_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"
)
PRECONDITION_ISSUES = (
    PRECONDITION_ROOT / "covapie_bulk_download_admission_implementation_issue_inventory.csv"
)
PRECONDITION_MANIFEST = (
    PRECONDITION_ROOT
    / "covapie_bulk_download_admission_implementation_precondition_manifest.json"
)
RUNTIME_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013.py"
)
RUNTIME_CONTRACT = RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_contract.csv"
RUNTIME_ISSUES = (
    RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_issue_readiness_inventory.csv"
)
RUNTIME_SAFETY = RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_safety_audit.csv"
RUNTIME_MANIFEST = RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_manifest.json"
QA_SAFETY = QA_ROOT / "covapie_final_dataset_qa_v1_safety_training_boundary_audit.csv"
QA_MANIFEST = QA_ROOT / "covapie_final_dataset_qa_v1_manifest.json"

SOURCE_PATHS = (
    DESIGN_PRODUCTION,
    DESIGN_RULES,
    DESIGN_SAFETY,
    DESIGN_MANIFEST,
    PRECONDITION_RULES,
    PRECONDITION_CONTEXT,
    PRECONDITION_ISSUES,
    PRECONDITION_MANIFEST,
    RUNTIME_PRODUCTION,
    RUNTIME_CONTRACT,
    RUNTIME_ISSUES,
    RUNTIME_SAFETY,
    RUNTIME_MANIFEST,
    QA_SAFETY,
    QA_MANIFEST,
)
SOURCE_SHA256 = {
    DESIGN_PRODUCTION: "79ecb3fb1084ddc161d1bec1a7db664ffbeda71952e31e4233317ecd487905d6",
    DESIGN_RULES: "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    DESIGN_SAFETY: "388869caf582bdf624d0016cae385dc2268f6cc05f54ecc9bf140608bbd3b208",
    DESIGN_MANIFEST: "085cb2f2a6bfe9bebe9e503dd10aa0b4d6f9ad754ff99539b1bafb33c78b5444",
    PRECONDITION_RULES: "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    PRECONDITION_CONTEXT: "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    PRECONDITION_ISSUES: "7c7707f5261461083bda7ab2177a423b608c725c070dafaff558bdf39256211e",
    PRECONDITION_MANIFEST: "2304b5754d8052b4b186981a98c12f259608a3492947e069c2afab84084a0d52",
    RUNTIME_PRODUCTION: PREDECESSOR_PRODUCTION_SHA256,
    RUNTIME_CONTRACT: "035effd65ca65ed1442bb7a29c03986390209f6d129d2ae078e223101c6a6144",
    RUNTIME_ISSUES: "477b4192579d3f64dac5bd0cc61c1a378b2f28c3355251e344b79999801a5d69",
    RUNTIME_SAFETY: "4b0c11cb59193bdfea9b7011e63ad4262cbbff2c1d57fd276de064997c28d8b4",
    RUNTIME_MANIFEST: "2940e6cc02a92b4919cdece3b1fa7c2f5e27d844f2962bb18757197266c23f79",
    QA_SAFETY: "8ea6a53d04456443014ba250a0cfacf4983e39d2138d7035ad188dc1dcceebe5",
    QA_MANIFEST: "4f7c884379f926af52101f40a7870b243f0309af3b1637dc65c8c0691acf9f35",
}

NEW_ISSUES = (
    "ADMIT_014_AUTHORIZATION_EVIDENCE_SOURCE_UNRESOLVED",
    "ADMIT_014_STAGE_AUTHORIZATION_ROUTING_RESPONSIBILITY_UNRESOLVED",
    "ADMIT_014_PERMISSION_VALUE_VOCABULARY_UNRESOLVED",
    "ADMIT_014_PERMISSION_TRANSITION_AND_PRECEDENCE_UNRESOLVED",
    "ADMIT_014_STANDALONE_SIGNATURE_UNRESOLVED",
    "ADMIT_014_RESULT_CONTRACT_UNRESOLVED",
    "ADMIT_014_RUNTIME_ENFORCEMENT_WITHOUT_AGGREGATION_UNRESOLVED",
)
ISSUE_EVIDENCE = NEW_ISSUES[0]
ISSUE_ROUTING = NEW_ISSUES[1]
ISSUE_VOCABULARY = NEW_ISSUES[2]
ISSUE_TRANSITION = NEW_ISSUES[3]
ISSUE_SIGNATURE = NEW_ISSUES[4]
ISSUE_RESULT = NEW_ISSUES[5]
ISSUE_ENFORCEMENT = NEW_ISSUES[6]

TRUE_READINESS = (
    "admit_014_preconditions_audited",
    "admit_014_rule_identity_complete",
    "admit_014_evaluator_scope_resolved",
    "admit_014_explicit_stage_context_model_selected",
    "admit_014_authorization_field_identity_frozen",
    "admit_014_stage_global_scope_resolved",
    "admit_014_candidate_record_authorization_sourcing_forbidden",
    "admit_014_batch_context_authorization_sourcing_forbidden",
    "admit_014_download_result_context_authorization_sourcing_forbidden",
    "admit_014_future_evaluator_pure_in_memory_possible",
    "current_gate_bulk_download_not_authorized_complete",
    "current_gate_network_not_authorized_complete",
    "ready_for_admit_014_download_authorization_contract_design",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_014_trusted_authorization_producer_and_provenance_frozen",
    "admit_014_stage_authorization_routing_resolved",
    "admit_014_permission_value_vocabulary_frozen",
    "admit_014_permission_transition_and_precedence_resolved",
    "admit_014_standalone_signature_frozen",
    "admit_014_formal_result_contract_frozen",
    "admit_014_reason_vocabulary_frozen",
    "admit_014_multi_failure_precedence_resolved",
    "ready_for_admit_014_standalone_evaluator_interface_implementation",
    "evaluate_admit_014_implemented",
    "Admit014EvaluationResult_implemented",
    "admit_014_unified_adapter_contract_frozen",
    "admit_014_unified_adapter_implemented",
    "admit_014_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_014_implemented",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


@dataclass(frozen=True)
class Source:
    path: Path
    content: bytes
    sha256: str
    mode: str
    blob: str


def _canonical_runtime_guard() -> None:
    import sys

    if (
        sys.implementation.name != CANONICAL_PYTHON_IMPLEMENTATION
        or tuple(sys.version_info[:3]) != (3, 10, 4)
    ):
        raise RuntimeError(
            "canonical evidence build requires CPython 3.10.4; "
            + NONCANONICAL_PYTHON_POLICY
        )


def _git(args: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=text, check=False
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


def _safe_source(path: Path) -> bool:
    return (
        not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[:2] != ("data", "raw")
        and path.parts[0] != "checkpoints"
        and STAGE not in path.as_posix()
        and DEFAULT_OUTPUT_ROOT.as_posix() not in path.as_posix()
    )


def _pinned_read_relative(path: Path) -> bytes:
    if not _safe_source(path):
        raise ValueError(f"unsafe source path: {path}")
    root_before = os.lstat(REPO_ROOT)
    if stat.S_ISLNK(root_before.st_mode) or not stat.S_ISDIR(root_before.st_mode):
        raise ValueError("unsafe repository root")
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
    descriptors: list[tuple[int, Identity, int | None, str | None]] = []
    root_fd = os.open(REPO_ROOT, directory_flags)
    root_identity = _identity(root_before)
    if _identity(os.fstat(root_fd)) != root_identity:
        os.close(root_fd)
        raise ValueError("repository root stat/open race")
    descriptors.append((root_fd, root_identity, None, None))
    try:
        current_fd = root_fd
        for part in path.parts[:-1]:
            lexical = os.stat(part, dir_fd=current_fd, follow_symlinks=False)
            lexical_identity = _identity(lexical)
            if stat.S_ISLNK(lexical.st_mode) or not stat.S_ISDIR(lexical.st_mode):
                raise ValueError(f"unsafe source parent: {path}")
            next_fd = os.open(part, directory_flags, dir_fd=current_fd)
            item = os.fstat(next_fd)
            if _identity(item) != lexical_identity:
                os.close(next_fd)
                raise ValueError(f"source parent stat/open race: {path}")
            descriptors.append((next_fd, lexical_identity, current_fd, part))
            current_fd = next_fd
        before = os.stat(path.name, dir_fd=current_fd, follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise ValueError(f"unsafe source leaf: {path}")
        expected = _identity(before)
        leaf_fd = os.open(path.name, leaf_flags, dir_fd=current_fd)
        try:
            if _identity(os.fstat(leaf_fd)) != expected:
                raise ValueError(f"source stat/open race: {path}")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(leaf_fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            if _identity(os.fstat(leaf_fd)) != expected:
                raise ValueError(f"source FD identity drift: {path}")
        finally:
            os.close(leaf_fd)
        after = os.stat(path.name, dir_fd=current_fd, follow_symlinks=False)
        if _identity(after) != expected:
            raise ValueError(f"source replacement after read: {path}")
        for descriptor, identity, lexical_parent_fd, lexical_name in descriptors:
            if _identity(os.fstat(descriptor)) != identity:
                raise ValueError(f"source parent identity drift: {path}")
            if lexical_parent_fd is not None and lexical_name is not None:
                lexical_after = os.stat(
                    lexical_name,
                    dir_fd=lexical_parent_fd,
                    follow_symlinks=False,
                )
                if _identity(lexical_after) != identity:
                    raise ValueError(f"source parent lexical replacement: {path}")
        if (
            _identity(os.lstat(REPO_ROOT)) != root_identity
            or _identity(os.fstat(root_fd)) != root_identity
        ):
            raise ValueError("repository root identity drift")
        return b"".join(chunks)
    finally:
        for descriptor, _, _, _ in reversed(descriptors):
            os.close(descriptor)


def build_frozen_source_snapshot() -> tuple[Source, ...]:
    _canonical_runtime_guard()
    identity = _git(["show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if identity.returncode or ancestor.returncode:
        raise ValueError("base identity or ancestry unavailable")
    if identity.stdout.splitlines() != [
        BASE_COMMIT,
        BASE_PARENT,
        BASE_TREE,
        BASE_SUBJECT,
    ]:
        raise ValueError("base identity mismatch")

    preflight: list[tuple[Path, str, str]] = []
    for path in SOURCE_PATHS:
        if not _safe_source(path):
            raise ValueError(f"unsafe source boundary: {path}")
        index = _git(["ls-files", "--stage", "--", path.as_posix()])
        tree = _git(["ls-tree", BASE_COMMIT, "--", path.as_posix()])
        if index.returncode or tree.returncode:
            raise ValueError(f"source tracking unavailable: {path}")
        index_head, index_sep, index_path = index.stdout.partition("\t")
        tree_head, tree_sep, tree_path = tree.stdout.partition("\t")
        index_fields = index_head.split()
        tree_fields = tree_head.split()
        if (
            not index_sep
            or not tree_sep
            or index_path.strip() != path.as_posix()
            or tree_path.strip() != path.as_posix()
            or len(index_fields) != 3
            or len(tree_fields) != 3
            or index_fields[0] not in {"100644", "100755"}
            or index_fields[2] != "0"
            or tree_fields[0] != index_fields[0]
            or tree_fields[1] != "blob"
            or index_fields[1] != tree_fields[2]
        ):
            raise ValueError(f"source index/base identity mismatch: {path}")
        preflight.append((path, tree_fields[0], tree_fields[2]))

    snapshot: list[Source] = []
    for path, mode, blob in preflight:
        current = _pinned_read_relative(path)
        base = _git(["show", f"{BASE_COMMIT}:{path.as_posix()}"], text=False)
        if base.returncode or not isinstance(base.stdout, bytes) or base.stdout != current:
            raise ValueError(f"source base/filesystem mismatch: {path}")
        digest = hashlib.sha256(current).hexdigest()
        if digest != SOURCE_SHA256[path]:
            raise ValueError(f"source frozen SHA mismatch: {path}")
        snapshot.append(Source(path, current, digest, mode, blob))
    return tuple(snapshot)


def _source(snapshot: tuple[Source, ...], path: Path) -> Source:
    return next(item for item in snapshot if item.path == path)


def _csv_rows(snapshot: tuple[Source, ...], path: Path) -> list[dict[str, str]]:
    return list(
        csv.DictReader(io.StringIO(_source(snapshot, path).content.decode(), newline=""))
    )


def _json(snapshot: tuple[Source, ...], path: Path) -> dict[str, Any]:
    return json.loads(_source(snapshot, path).content)


def _verify_committed_contracts(snapshot: tuple[Source, ...]) -> None:
    expected_rule = {
        "admission_rule_id": ADMISSION_RULE_ID,
        "admission_rule_name": ADMISSION_RULE_NAME,
        "evidence_source": EVIDENCE_SOURCE,
        "required_status": REQUIRED_STATUS,
        "failure_severity": FAILURE_SEVERITY,
        "blocking_reason": BLOCKING_REASON,
        "evaluation_phase": EVALUATION_PHASE,
        "network_required": "false",
        "raw_structure_required": "false",
        "ready_for_future_implementation": "true",
    }
    rule = next(
        row
        for row in _csv_rows(snapshot, DESIGN_RULES)
        if row["admission_rule_id"] == ADMISSION_RULE_ID
    )
    if rule != expected_rule:
        raise ValueError("ADMIT_014 registry identity drift")

    design_safety = {
        row["safety_item"]: row for row in _csv_rows(snapshot, DESIGN_SAFETY)
    }
    for item in (
        "network_access_used_current_step",
        "download_queue_materialized_current_step",
        "download_manifest_materialized_current_step",
        "raw_files_written_current_step",
        "training_allowed",
    ):
        if (
            design_safety[item]["observed_status"] != "false"
            or design_safety[item]["safety_passed"] != "true"
        ):
            raise ValueError(f"Step14AT safety drift: {item}")
    design_manifest = _json(snapshot, DESIGN_MANIFEST)
    if not (
        design_manifest["ready_for_bulk_download_now"] is False
        and design_manifest["network_access_used_current_step"] is False
        and design_manifest["download_queue_materialized"] is False
        and design_manifest["raw_structure_read_current_step"] is False
        and design_manifest["ready_for_training"] is False
        and design_manifest["feature_semantics_audit_required_before_training"] is True
    ):
        raise ValueError("Step14AT readiness drift")

    executable = next(
        row
        for row in _csv_rows(snapshot, PRECONDITION_RULES)
        if row["admission_rule_id"] == ADMISSION_RULE_ID
    )
    if not (
        executable["admission_rule_name"] == ADMISSION_RULE_NAME
        and executable["evaluation_phase"] == EVALUATION_PHASE
        and executable["candidate_field_dependencies"] == ""
        and executable["batch_context_dependencies"] == ""
        and executable["evaluation_context_dependencies"]
        == ADMIT_014_AUTHORIZATION_CONTEXT_ITEM
        and executable["external_filesystem_required"] == "false"
        and executable["network_required"] == "false"
        and executable["download_execution_result_required"] == "false"
        and executable["pure_in_memory_interface_possible"] == "true"
        and executable["dependency_contract_passed"] == "true"
        and executable["semantics_complete"] == "true"
        and executable["deterministic_evaluation_possible_now"] == "true"
        and executable["deterministic_evaluation_possible_after_contract_freeze"]
        == "true"
        and executable["implementation_disposition"] == "rule_logic_ready"
        and executable["blocking_reasons"] == ""
    ):
        raise ValueError("Step14AU-A ADMIT_014 row drift")
    context = next(
        row
        for row in _csv_rows(snapshot, PRECONDITION_CONTEXT)
        if row["context_item"] == "current_stage_download_authorized"
    )
    if not (
        context["context_scope"] == ADMIT_014_CONTEXT_SCOPE
        and context["required_by_rules"] == ADMISSION_RULE_ID
        and context["provided_by_future_caller"] == "true"
        and context["filesystem_access_inside_evaluator"] == "false"
        and context["network_access_inside_evaluator"] == "false"
        and context["deterministic_now"] == "true"
        and context["deterministic_after_contract_freeze"] == "true"
        and context["exact_contract_defined"] == "true"
        and context["implementation_ready"] == "true"
        and context["blocking_reasons"] == ""
    ):
        raise ValueError("Step14AU-A context drift")
    precondition_manifest = _json(snapshot, PRECONDITION_MANIFEST)
    if not (
        precondition_manifest["all_rule_semantics_complete"] is False
        and precondition_manifest["ready_for_bulk_download_now"] is False
        and precondition_manifest["ready_for_real_candidate_evaluation"] is False
        and precondition_manifest["ready_for_training"] is False
        and precondition_manifest["feature_semantics_audit_required_before_training"]
        is True
    ):
        raise ValueError("Step14AU-A boundary drift")

    runtime = _json(snapshot, RUNTIME_MANIFEST)
    expected_registered = [f"ADMIT_{index:03d}" for index in range(1, 14)]
    if not (
        runtime["registered_rule_ids"] == expected_registered
        and runtime["known_not_registered_rule_ids"] == ["ADMIT_014", "ADMIT_015"]
        and runtime["admit_014_registered_in_engine"] is False
        and runtime["issue_coverage_after"] == ["ADMIT_014", "ADMIT_015"]
        and runtime["combined_candidate_verdict_implemented"] is False
        and runtime["cross_rule_aggregation_implemented"] is False
        and runtime["provider_mapping_validated"] is False
        and runtime["real_provider_evaluation_ready"] is False
        and runtime["ready_for_bulk_download_now"] is False
        and runtime["ready_for_training"] is False
        and runtime["feature_semantics_audit_required_before_training"] is True
    ):
        raise ValueError("Exact13 runtime boundary drift")
    tree = ast.parse(_source(snapshot, RUNTIME_PRODUCTION).content.decode())
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    if "_evaluate_registered_admit_014" in functions:
        raise ValueError("unexpected ADMIT_014 handler")
    dispatcher = functions.get("evaluate_admission_rule")
    if dispatcher is None:
        raise ValueError("Exact13 dispatcher missing")
    argument_names = [argument.arg for argument in dispatcher.args.args] + [
        argument.arg for argument in dispatcher.args.kwonlyargs
    ]
    if argument_names != [
        "admission_rule_id",
        "candidate_record",
        "batch_context",
        "evaluation_context",
        "download_result_context",
        "stage_authorization_context",
    ]:
        raise ValueError("Exact13 dispatcher signature drift")

    qa = _json(snapshot, QA_MANIFEST)
    if not (
        qa["ready_for_bulk_download_now"] is False
        and qa["ready_for_training"] is False
        and qa["feature_semantics_known_for_training"] is False
        and qa["unknown_atom_feature_policy_finalized_for_training"] is False
        and qa["feature_semantics_audit_required_before_training"] is True
    ):
        raise ValueError("canonical QA training boundary drift")


def _row(columns: tuple[str, ...], **values: str) -> dict[str, str]:
    return {column: values.get(column, "") for column in columns}


def _precondition_specs() -> tuple[tuple[str, str, str, str, str, str], ...]:
    complete = "complete"
    incomplete = "incomplete"
    return (
        ("identity", "rule ID", "ADMIT_014", "ADMIT_014 registry identity exact", complete, ""),
        ("identity", "rule name", ADMISSION_RULE_NAME, "Step14AT registry exact", complete, ""),
        ("identity", "evidence source", EVIDENCE_SOURCE, "Step14AT registry exact", complete, ""),
        ("identity", "required status", REQUIRED_STATUS, "Step14AT registry exact", complete, ""),
        ("identity", "failure severity", FAILURE_SEVERITY, "Step14AT registry exact", complete, ""),
        ("identity", "blocking reason", BLOCKING_REASON, "Step14AT registry exact", complete, ""),
        ("identity", "evaluation phase", EVALUATION_PHASE, "Step14AT registry exact", complete, ""),
        (
            "identity",
            "network/raw/future-implementation flags",
            "false|false|true",
            "Step14AT registry exact; future-ready means design may continue only",
            complete,
            "",
        ),
        (
            "current_committed_state",
            "current gate explicitly grants no download permission",
            "bulk download not authorized",
            "Step14AT ADMIT_014 required status and manifest",
            complete,
            "",
        ),
        (
            "current_committed_state",
            "current step network execution count is zero",
            "zero",
            "Step14AT and Exact13 safety",
            complete,
            "",
        ),
        (
            "current_committed_state",
            "current step download queue/manifest/raw-write count is zero",
            "zero|zero|zero",
            "Step14AT safety and manifest",
            complete,
            "",
        ),
        (
            "current_committed_state",
            "ADMIT_014 is known but not registered",
            "known=true; registered=false",
            "Exact13 manifest and registry audit",
            complete,
            "",
        ),
        (
            "current_committed_state",
            "ready_for_bulk_download_now is false",
            "false",
            "Step14AT, Step14AU-A, Exact13, and QA manifests",
            complete,
            "",
        ),
        (
            "current_committed_state",
            "provider mapping and real download readiness are false",
            "false|false",
            "Exact13 manifest",
            complete,
            "",
        ),
        (
            "authority_and_evidence",
            "authoritative permission producer identity",
            "one explicit trusted producer",
            "no committed future permission producer identity",
            incomplete,
            ISSUE_EVIDENCE,
        ),
        (
            "authority_and_evidence",
            "current-design-gate versus future authority boundary",
            "current fact must not be promoted into future authorization",
            "Step14AU-A selects explicit future-caller stage context; current value remains false",
            complete,
            "",
        ),
        (
            "authority_and_evidence",
            "stage_authorization_context routing responsibility",
            "exact sourcing and ownership contract",
            "signature envelope exists; ADMIT_014 semantics absent",
            incomplete,
            ISSUE_ROUTING,
        ),
        (
            "authority_and_evidence",
            "exact authorization field identity",
            "one frozen field name",
            "current_stage_download_authorized committed by Step14AU-A",
            complete,
            "",
        ),
        (
            "authority_and_evidence",
            "exact built-in scalar/container type",
            "one exact built-in representation",
            "not committed",
            incomplete,
            ISSUE_VOCABULARY,
        ),
        (
            "authority_and_evidence",
            "closed authorization value vocabulary",
            "closed exact values",
            "not committed",
            incomplete,
            ISSUE_VOCABULARY,
        ),
        (
            "authority_and_evidence",
            "normalization forbidden",
            "no coercion or normalization",
            "not committed for a future evaluator",
            incomplete,
            ISSUE_VOCABULARY,
        ),
        (
            "authority_and_evidence",
            "missing authority behavior",
            "fail closed with frozen reason",
            "not committed",
            incomplete,
            ISSUE_TRANSITION,
        ),
        (
            "authority_and_evidence",
            "invalid authority behavior",
            "fail closed with frozen reason",
            "not committed",
            incomplete,
            ISSUE_TRANSITION,
        ),
        (
            "authority_and_evidence",
            "contradictory authority behavior",
            "fail closed with frozen reason",
            "not committed",
            incomplete,
            ISSUE_TRANSITION,
        ),
        (
            "authority_and_evidence",
            "freshness/version/replay semantics",
            "frozen trust lifetime and replay rules",
            "not committed",
            incomplete,
            ISSUE_EVIDENCE,
        ),
        (
            "authority_and_evidence",
            "trusted producer and provenance contract",
            "authenticated producer and provenance",
            "not committed",
            incomplete,
            ISSUE_EVIDENCE,
        ),
        (
            "authority_and_evidence",
            "current-stage constant versus future-context evaluator scope",
            "inherit exactly one committed model",
            "future_explicit_authorization_context selected; current_stage_constant_guard rejected",
            complete,
            "",
        ),
        (
            "scope_and_routing",
            "global-stage versus per-candidate scope",
            "stage-global scope",
            "Step14AU-A context_scope=stage",
            complete,
            "",
        ),
        (
            "scope_and_routing",
            "candidate_record responsibility",
            "authorization sourcing forbidden",
            "candidate_field_dependencies is empty",
            complete,
            "",
        ),
        (
            "scope_and_routing",
            "batch_context responsibility",
            "authorization sourcing forbidden",
            "batch_context_dependencies is empty",
            complete,
            "",
        ),
        (
            "scope_and_routing",
            "evaluation_context responsibility",
            "forbidden or exact routing responsibility",
            "evaluation sourcing is not authorized",
            incomplete,
            ISSUE_ROUTING,
        ),
        (
            "scope_and_routing",
            "download_result_context responsibility",
            "authorization sourcing forbidden",
            "Step14AU-A dependency is a stage-scoped authorization context, not a download result",
            complete,
            "",
        ),
        (
            "scope_and_routing",
            "stage_authorization_context responsibility",
            "exact responsibility if future-context model selected",
            "likely envelope candidate only; not frozen",
            incomplete,
            ISSUE_ROUTING,
        ),
        (
            "scope_and_routing",
            "first-failure routing precedence",
            "closed envelope validation precedence",
            "not committed",
            incomplete,
            ISSUE_TRANSITION,
        ),
        (
            "outcome_and_interface",
            "current no-permission blocking outcome",
            "required status with blocking reason",
            "Step14AT registry exact",
            complete,
            "",
        ),
        (
            "outcome_and_interface",
            "future authorized transition semantics",
            "exact trusted transition only",
            "not committed",
            incomplete,
            ISSUE_TRANSITION,
        ),
        (
            "outcome_and_interface",
            "closed outcome vocabulary",
            "closed exact outcomes",
            "not committed",
            incomplete,
            ISSUE_RESULT,
        ),
        (
            "outcome_and_interface",
            "closed reason vocabulary",
            "closed exact reasons",
            "not committed",
            incomplete,
            ISSUE_RESULT,
        ),
        (
            "outcome_and_interface",
            "public standalone signature",
            "exact keyword and default contract",
            "no formal ADMIT_014 evaluator contract",
            incomplete,
            ISSUE_SIGNATURE,
        ),
        (
            "outcome_and_interface",
            "formal result contract",
            "exact result type and fields",
            "not committed",
            incomplete,
            ISSUE_RESULT,
        ),
        (
            "outcome_and_interface",
            "normalized/validated/consumed representation",
            "exact ordered representation",
            "not committed",
            incomplete,
            ISSUE_RESULT,
        ),
        (
            "outcome_and_interface",
            "multi-invalid precedence",
            "closed first-failure precedence",
            "not committed",
            incomplete,
            ISSUE_TRANSITION,
        ),
        (
            "outcome_and_interface",
            "pure in-memory/no-I/O boundary",
            "no evaluator filesystem or network I/O",
            "Step14AU-A records pure in-memory possible",
            complete,
            "",
        ),
        (
            "integration_and_enforcement",
            "dependency on ADMIT_001..013",
            "standalone evaluator independent of earlier rule-result inputs",
            "Step14AU-A lists only current_stage_download_authorized; workflow enforcement remains unresolved",
            complete,
            "",
        ),
        (
            "integration_and_enforcement",
            "single-rule runtime versus mandatory download enforcement",
            "caller-level enforcement contract",
            "Exact13 is single-rule dispatch only",
            incomplete,
            ISSUE_ENFORCEMENT,
        ),
        (
            "integration_and_enforcement",
            "caller obligation to evaluate ADMIT_014 before any download",
            "mandatory fail-closed caller guard",
            "not implemented or committed",
            incomplete,
            ISSUE_ENFORCEMENT,
        ),
        (
            "integration_and_enforcement",
            "combined-verdict/aggregation dependency",
            "explicit enforcement without ambiguity",
            "combined verdict and aggregation absent",
            incomplete,
            ISSUE_ENFORCEMENT,
        ),
        (
            "integration_and_enforcement",
            "adapter and Exact13 projection boundary",
            "future adapter contract",
            "no ADMIT_014 adapter contract",
            incomplete,
            ISSUE_ENFORCEMENT,
        ),
        (
            "integration_and_enforcement",
            "registration boundary",
            "register only after evaluator and adapter contracts",
            "known but not registered",
            incomplete,
            ISSUE_ENFORCEMENT,
        ),
        (
            "integration_and_enforcement",
            "provider/download authorization boundary",
            "no execution before explicit authority and enforcement",
            "provider, network, and download remain unauthorized",
            incomplete,
            ISSUE_ENFORCEMENT,
        ),
        (
            "integration_and_enforcement",
            "training and feature-semantics boundary",
            "feature-semantics audit required before training",
            "canonical QA and Exact13 preserve blocker",
            complete,
            "",
        ),
    )


def _precondition_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for order, spec in enumerate(_precondition_specs(), 1):
        group, subject, expected, observed, completeness, blocker = spec
        rows.append(
            _row(
                COLUMNS[PRECONDITION],
                precondition_order=str(order),
                precondition_id=f"PRE_{order:03d}",
                precondition_group=group,
                precondition_subject=subject,
                expected_contract=expected,
                observed_evidence=observed,
                completeness_status=completeness,
                implementation_blocking="true" if blocker else "false",
                blocking_reason=blocker,
                precondition_passed="true",
            )
        )
    if len(rows) != 51:
        raise AssertionError("precondition row count drift")
    return rows


def _authorization_rows() -> list[dict[str, str]]:
    specs = (
        ("current_evidence", "current_design_gate", "Step14AT registry/manifest", "authoritative", "current gate grants no download permission", "preserve current blocking fact", ""),
        ("current_runtime", "Exact13 known-not-registered", "Exact13 manifest/registry", "authoritative", "ADMIT_014 known and unregistered", "do not register in this audit", ""),
        ("routing_envelope", "successor envelope ownership", "Step14AU-A stage context plus Exact13 dispatcher envelopes", "authoritative", "stage-scoped context identity known; exact evaluation_context versus stage_authorization_context ownership unresolved", "freeze one exact successor envelope", ISSUE_ROUTING),
        ("current_safety", "no network/download/raw write", "Step14AT/Exact13/QA safety", "authoritative", "all observed false", "retain fail-closed boundary", ""),
        ("candidate_model", "current_stage_constant_guard", "Step14AU-A explicit context dependency", "committed alternative rejected", "rejected", "must remain rejected without contract migration", ""),
        ("candidate_model", "future_explicit_authorization_context", "Step14AU-A executability/context contracts", "authoritative inherited selection", "selected with current_stage_download_authorized", "preserve explicit-context model", ""),
        ("envelope_source", "candidate_record", "Step14AU-A empty candidate_field_dependencies", "authoritative", "forbidden as authorization source", "remain forbidden", ""),
        ("envelope_source", "batch_context", "Step14AU-A empty batch_context_dependencies", "authoritative", "forbidden as authorization source", "remain forbidden", ""),
        ("envelope_source", "evaluation_context", "Step14AU-A context identity and Exact13 envelope", "authoritative", "stage-scoped context identity known; exact successor envelope ownership unresolved", "freeze ownership or forbid", ISSUE_ROUTING),
        ("envelope_source", "download_result_context", "Step14AU-A stage-scoped dependency", "authoritative", "forbidden as authorization source", "remain forbidden", ""),
        ("envelope_source", "stage_authorization_context", "Step14AU-A stage context plus Exact13 signature", "authoritative", "stage-scoped context identity known; exact successor envelope ownership unresolved", "freeze ownership or forbid", ISSUE_ROUTING),
        ("authority", "explicit authority producer", "none committed", "absent", "producer identity missing", "freeze trusted producer/provenance", ISSUE_EVIDENCE),
        ("authority", "permission field name", "Step14AU-A context contract", "authoritative", "current_stage_download_authorized", "preserve exact field identity", ""),
        ("authority", "permission vocabulary", "none committed", "absent", "closed values missing", "freeze exact type and values", ISSUE_VOCABULARY),
        ("precedence", "missing/invalid/contradiction", "none committed", "absent", "precedence missing", "freeze fail-closed reasons/order", ISSUE_TRANSITION),
        ("enforcement", "cross-rule aggregation", "Exact13 manifest", "authoritative", "not implemented", "freeze enforcement dependency", ISSUE_ENFORCEMENT),
        ("enforcement", "caller-level mandatory download guard", "no committed authority", "absent", "not implemented", "freeze mandatory caller obligation", ISSUE_ENFORCEMENT),
        ("provider", "provider mapping", "Exact13 manifest", "authoritative", "not implemented", "remain unauthorized", ISSUE_ENFORCEMENT),
        ("authorization", "real download authorization", "Step14AT/Exact13/QA", "authoritative", "false", "requires explicit future gate", ISSUE_ENFORCEMENT),
        ("training", "training authorization", "canonical QA/Exact13", "authoritative", "false with feature-semantics audit required", "preserve training prohibition", ""),
    )
    rows = []
    for order, spec in enumerate(specs, 1):
        group, envelope, evidence, classification, observed, requirement, blocker = spec
        rows.append(
            _row(
                COLUMNS[AUTHORIZATION],
                matrix_order=str(order),
                matrix_group=group,
                case_id=f"AUTH_{order:03d}",
                authority_or_envelope=envelope,
                committed_evidence=evidence,
                authority_classification=classification,
                current_observed_state=observed,
                future_contract_requirement=requirement,
                completeness_status="incomplete" if blocker else "complete",
                implementation_blocking="true" if blocker else "false",
                blocking_reason=blocker,
                case_passed="true",
            )
        )
    return rows


def _current_state_rows() -> list[dict[str, str]]:
    specs = (
        ("Step14AT ADMIT_014 registry identity", DESIGN_RULES, "ADMIT_014 row", "exact canonical identity", "exact canonical identity", "authoritative"),
        ("Step14AT current download permission", DESIGN_RULES, "required_status", REQUIRED_STATUS, REQUIRED_STATUS, "authoritative"),
        ("Step14AT network execution", DESIGN_SAFETY, "network_access_used_current_step", "false", "false", "authoritative"),
        ("Step14AT queue/manifest/raw writes", DESIGN_SAFETY, "three safety rows", "false|false|false", "false|false|false", "authoritative"),
        ("Step14AT bulk readiness", DESIGN_MANIFEST, "ready_for_bulk_download_now", "false", "false", "authoritative"),
        ("Step14AU-A rule row", PRECONDITION_RULES, "ADMIT_014 row", "semantics_complete=true; rule_logic_ready", "semantics_complete=true; rule_logic_ready", "authoritative"),
        (
            "Step14AU-A current_stage_download_authorized context",
            PRECONDITION_CONTEXT,
            "current_stage_download_authorized row",
            "context_scope=stage|required_by_rules=ADMIT_014|provided_by_future_caller=true|exact_contract_defined=true|implementation_ready=true",
            "context_scope=stage|required_by_rules=ADMIT_014|provided_by_future_caller=true|exact_contract_defined=true|implementation_ready=true",
            "authoritative",
        ),
        ("Step14AU-A overall semantics", PRECONDITION_MANIFEST, "all_rule_semantics_complete", "false", "false", "authoritative"),
        ("Exact13 registered IDs", RUNTIME_MANIFEST, "registered_rule_ids", "ADMIT_001..ADMIT_013", "ADMIT_001..ADMIT_013", "authoritative"),
        ("Exact13 known-not-registered IDs", RUNTIME_MANIFEST, "known_not_registered_rule_ids", "ADMIT_014|ADMIT_015", "ADMIT_014|ADMIT_015", "authoritative"),
        ("Exact13 issue coverage after", RUNTIME_MANIFEST, "issue_coverage_after", "ADMIT_014|ADMIT_015", "ADMIT_014|ADMIT_015", "authoritative"),
        ("provider/download/raw/network/training flags", RUNTIME_SAFETY, "safety rows 20..27", "all false", "all false", "authoritative"),
        ("current base commit identity", Path(".git"), "base identity", BASE_COMMIT, BASE_COMMIT, "authoritative"),
    )
    return [
        _row(
            COLUMNS[CURRENT_STATE],
            inventory_order=str(order),
            state_item=item,
            source_path=path.as_posix(),
            source_field_or_row=field,
            expected_current_state=expected,
            observed_current_state=observed,
            authority_classification=classification,
            state_passed="true",
        )
        for order, (item, path, field, expected, observed, classification) in enumerate(
            specs, 1
        )
    ]


def _source_rows(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    return [
        _row(
            COLUMNS[SOURCE_AUDIT],
            source_order=str(order),
            source_relative_path=source.path.as_posix(),
            expected_sha256=source.sha256,
            base_tree_mode=source.mode,
            tracked="true",
            base_tree_blob="true",
            filesystem_regular="true",
            non_symlink="true",
            parent_chain_non_symlink="true",
            safe_descendant="true",
            pinned_fd_read="true",
            post_read_identity_verified="true",
            source_verified="true",
        )
        for order, source in enumerate(snapshot, 1)
    ]


def _issue_rows(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    inherited = _csv_rows(snapshot, RUNTIME_ISSUES)
    columns = tuple(inherited[0])
    scopes = (
        "admit_014_permission_authority",
        "admit_014_context_routing",
        "admit_014_permission_vocabulary",
        "admit_014_transition_and_precedence",
        "admit_014_standalone_interface",
        "admit_014_result_and_reason_contract",
        "unified_download_authorization_enforcement",
    )
    for order, (issue_id, scope) in enumerate(zip(NEW_ISSUES, scopes), 24):
        values = {
            "inherited_order": str(order),
            "issue_id": issue_id,
            "issue_type": "implementation_semantics_gap",
            "affected_fields": "",
            "affected_rules": ADMISSION_RULE_ID,
            "severity": "blocking",
            "status": "open",
            "blocking_scope": scope,
            "blocking_reason": issue_id,
            "issue_origin": STAGE,
            "integration_transition": "new_open",
            "issue_count": "1",
            "inherited_effective_status": "",
            "inherited_transition_stage": "",
            "inherited_transition_action": "not_applicable_new_issue",
            "inherited_transition_evidence": "new audit issue; no inherited resolution",
            "successor_effective_status": "open",
            "successor_transition_stage": STAGE,
            "successor_transition_action": "new_open",
            "successor_transition_evidence": "unresolved implementation precondition recorded",
        }
        inherited.append({column: values.get(column, "") for column in columns})
    return inherited


def _readiness() -> dict[str, bool]:
    return {
        **{key: True for key in TRUE_READINESS},
        **{key: False for key in FALSE_READINESS},
    }


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _payloads(snapshot: tuple[Source, ...]) -> dict[str, bytes]:
    _canonical_runtime_guard()
    _verify_committed_contracts(snapshot)
    preconditions = _precondition_rows()
    authorization = _authorization_rows()
    current_state = _current_state_rows()
    sources = _source_rows(snapshot)
    issues = _issue_rows(snapshot)
    payloads = {
        PRECONDITION: _csv_bytes(COLUMNS[PRECONDITION], preconditions),
        AUTHORIZATION: _csv_bytes(COLUMNS[AUTHORIZATION], authorization),
        CURRENT_STATE: _csv_bytes(COLUMNS[CURRENT_STATE], current_state),
        SOURCE_AUDIT: _csv_bytes(COLUMNS[SOURCE_AUDIT], sources),
        ISSUE: _csv_bytes(tuple(issues[0]), issues),
    }
    output_sha256 = {
        name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()
    }
    readiness = _readiness()
    precondition_groups = {
        group: sum(row["precondition_group"] == group for row in preconditions)
        for group in dict.fromkeys(row["precondition_group"] for row in preconditions)
    }
    authorization_groups = {
        group: sum(row["matrix_group"] == group for row in authorization)
        for group in dict.fromkeys(row["matrix_group"] for row in authorization)
    }
    manifest: dict[str, Any] = {
        "project": "CovaPIE",
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "base_parent": BASE_PARENT,
        "base_tree": BASE_TREE,
        "base_subject": BASE_SUBJECT,
        "canonical_evidence_python_implementation": CANONICAL_PYTHON_IMPLEMENTATION,
        "canonical_evidence_python_version": CANONICAL_PYTHON_VERSION,
        "ast_attestation_cross_python_version_portable": False,
        "noncanonical_python_policy": NONCANONICAL_PYTHON_POLICY,
        "python_runtime_migration_policy": PYTHON_RUNTIME_MIGRATION_POLICY,
        "admission_rule_id": ADMISSION_RULE_ID,
        "admission_rule_name": ADMISSION_RULE_NAME,
        "evidence_source": EVIDENCE_SOURCE,
        "required_status": REQUIRED_STATUS,
        "failure_severity": FAILURE_SEVERITY,
        "blocking_reason": BLOCKING_REASON,
        "evaluation_phase": EVALUATION_PHASE,
        "network_required": NETWORK_REQUIRED,
        "raw_structure_required": RAW_STRUCTURE_REQUIRED,
        "ready_for_future_implementation": READY_FOR_FUTURE_IMPLEMENTATION,
        "ready_for_future_implementation_means_contract_design_only": True,
        "ready_for_future_implementation_grants_download_permission": False,
        "current_gate_grants_download_permission": False,
        "current_gate_bulk_download_not_authorized": True,
        "current_gate_network_not_authorized": True,
        "current_gate_provider_not_authorized": True,
        "current_gate_raw_write_not_authorized": True,
        "current_stage_network_execution_count": 0,
        "current_stage_download_queue_count": 0,
        "current_stage_download_manifest_count": 0,
        "current_stage_raw_write_count": 0,
        "admit_014_evaluator_model": ADMIT_014_EVALUATOR_MODEL,
        "admit_014_evaluator_model_selected": True,
        "current_stage_constant_guard_rejected": True,
        "authorization_context_item": ADMIT_014_AUTHORIZATION_CONTEXT_ITEM,
        "authorization_context_scope": ADMIT_014_CONTEXT_SCOPE,
        "authorization_context_provided_by_future_caller": True,
        "authorization_context_exact_contract_available": True,
        "authorization_context_implementation_ready_in_step14au_a": True,
        "successor_runtime_envelope_ownership_frozen": False,
        "stage_authorization_context_present_in_dispatcher_signature": True,
        "stage_authorization_context_admit_014_semantics_frozen": False,
        "precondition_schema": list(COLUMNS[PRECONDITION]),
        "precondition_row_count": len(preconditions),
        "precondition_group_counts": precondition_groups,
        "precondition_complete_count": sum(
            row["completeness_status"] == "complete" for row in preconditions
        ),
        "precondition_incomplete_count": sum(
            row["completeness_status"] == "incomplete" for row in preconditions
        ),
        "precondition_implementation_blocking_count": sum(
            row["implementation_blocking"] == "true" for row in preconditions
        ),
        "authorization_matrix_schema": list(COLUMNS[AUTHORIZATION]),
        "authorization_matrix_row_count": len(authorization),
        "authorization_matrix_group_counts": authorization_groups,
        "authorization_matrix_complete_count": sum(
            row["completeness_status"] == "complete" for row in authorization
        ),
        "authorization_matrix_incomplete_count": sum(
            row["completeness_status"] == "incomplete" for row in authorization
        ),
        "current_state_inventory_schema": list(COLUMNS[CURRENT_STATE]),
        "current_state_inventory_row_count": len(current_state),
        "source_boundary_schema": list(COLUMNS[SOURCE_AUDIT]),
        "source_count": len(snapshot),
        "source_boundary": [
            {"path": source.path.as_posix(), "sha256": source.sha256}
            for source in snapshot
        ],
        "source_validation_before_output_read": True,
        "issue_schema": list(issues[0]),
        "issue_row_count": len(issues),
        "inherited_issue_row_count": 23,
        "new_admit_014_issue_row_count": len(NEW_ISSUES),
        "new_admit_014_issue_ids": list(NEW_ISSUES),
        "open_issue_ids": [
            row["issue_id"]
            for row in issues
            if row["successor_effective_status"] == "open"
        ],
        "coverage_issue_affected_rules": "ADMIT_014|ADMIT_015",
        "readiness": readiness,
        "safety": {
            "provider_mapping_or_execution": False,
            "network": False,
            "download": False,
            "download_queue_or_manifest": False,
            "raw_read_or_write": False,
            "model_or_checkpoint": False,
            "dataloader": False,
            "training_or_parameter_update": False,
            "combined_candidate_verdict": False,
            "cross_rule_aggregation": False,
            "current_main_stage_commit_push": False,
        },
        "output_files": list(FILES),
        "output_file_count": len(FILES),
        "output_sha256": output_sha256,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "feature_semantics_note": (
            "historical UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=false "
            "require an explicit feature-semantics audit before training"
        ),
        "renameat2_policy": (
            "RENAME_NOREPLACE_required; GPFS_EINVAL_fails_closed; "
            "no_os_replace_fallback"
        ),
        "all_checks_passed": True,
    }
    manifest.update(readiness)
    payloads[MANIFEST] = (
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    ).encode()
    return payloads


def _write_exclusive_leaf(directory_fd: int, name: str, data: bytes) -> None:
    descriptor = os.open(
        name,
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
        0o644,
        dir_fd=directory_fd,
    )
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(descriptor, view) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _rename_noreplace(
    source: Path, destination: Path, parent_fd: int | None = None
) -> None:
    if os.uname().machine not in {"x86_64", "amd64"}:
        raise RuntimeError("renameat2 syscall number unavailable")
    source_directory = -100 if parent_fd is None else parent_fd
    destination_directory = -100 if parent_fd is None else parent_fd
    source_name = source if parent_fd is None else Path(source.name)
    destination_name = destination if parent_fd is None else Path(destination.name)
    result = ctypes.CDLL(None, use_errno=True).syscall(
        316,
        source_directory,
        os.fsencode(source_name),
        destination_directory,
        os.fsencode(destination_name),
        1,
    )
    if result:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination)


def _read_output_set(
    root: Path,
    payloads: dict[str, bytes],
    expected_root_identity: Identity | None = None,
) -> bool:
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
    parent_lexical = os.lstat(parent)
    if stat.S_ISLNK(parent_lexical.st_mode) or not stat.S_ISDIR(parent_lexical.st_mode):
        raise ValueError("unsafe output parent")
    parent_identity = _identity(parent_lexical)
    parent_fd = os.open(parent, directory_flags)
    root_fd = -1
    leaves: list[tuple[str, int, Identity, bytes]] = []
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("output parent stat/open race")
        root_lexical = os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
        if stat.S_ISLNK(root_lexical.st_mode) or not stat.S_ISDIR(root_lexical.st_mode):
            raise ValueError("unsafe output root")
        root_identity = _identity(root_lexical)
        if expected_root_identity is not None and root_identity != expected_root_identity:
            raise ValueError("published destination identity mismatch")
        root_fd = os.open(root.name, directory_flags, dir_fd=parent_fd)
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root stat/open race")
        if set(os.listdir(root_fd)) != set(FILES):
            return False
        for name in FILES:
            before = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                stat.S_ISLNK(before.st_mode)
                or not stat.S_ISREG(before.st_mode)
                or before.st_size > 100 * 1024 * 1024
            ):
                raise ValueError("unsafe output leaf")
            identity = _identity(before)
            descriptor = os.open(name, leaf_flags, dir_fd=root_fd)
            if _identity(os.fstat(descriptor)) != identity:
                os.close(descriptor)
                raise ValueError("output leaf stat/open race")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            data = b"".join(chunks)
            leaves.append((name, descriptor, identity, data))

        if set(os.listdir(root_fd)) != set(FILES):
            raise ValueError("output inventory drift after traversal")
        for name, descriptor, identity, data in leaves:
            if (
                _identity(os.fstat(descriptor)) != identity
                or _identity(
                    os.stat(name, dir_fd=root_fd, follow_symlinks=False)
                )
                != identity
            ):
                raise ValueError("output leaf identity drift after traversal")
            if data != payloads[name]:
                return False
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(
                os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != root_identity
            or _identity(os.fstat(parent_fd)) != parent_identity
            or _identity(os.lstat(parent)) != parent_identity
        ):
            raise ValueError("output parent/root identity drift after traversal")
        return True
    finally:
        for _, descriptor, _, _ in leaves:
            os.close(descriptor)
        if root_fd >= 0:
            os.close(root_fd)
        os.close(parent_fd)


def _cleanup_staging(staging: Path) -> None:
    if not staging.exists() or staging.is_symlink():
        return
    entries = list(staging.iterdir())
    if any(entry.name not in FILES for entry in entries):
        return
    for entry in entries:
        item = os.lstat(entry)
        if stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode):
            entry.unlink()
    try:
        staging.rmdir()
    except OSError:
        pass


def materialize_audit(output_root: Path | None = None) -> dict[str, Any]:
    """Build and atomically publish the deterministic Exact6 audit evidence."""
    _canonical_runtime_guard()
    root = REPO_ROOT / DEFAULT_OUTPUT_ROOT if output_root is None else Path(output_root)
    parent = root.parent
    snapshot = build_frozen_source_snapshot()
    payloads = _payloads(snapshot)
    if os.path.lexists(root):
        if _read_output_set(root, payloads):
            return json.loads(payloads[MANIFEST])
        raise ValueError("existing output set mismatch")

    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    parent_lexical = os.lstat(parent)
    if stat.S_ISLNK(parent_lexical.st_mode) or not stat.S_ISDIR(parent_lexical.st_mode):
        raise ValueError("unsafe output parent")
    parent_fd = os.open(parent, directory_flags)
    parent_open_identity = _identity(os.fstat(parent_fd))
    if parent_open_identity != _identity(parent_lexical):
        os.close(parent_fd)
        raise ValueError("output parent stat/open race")
    staging = Path(
        tempfile.mkdtemp(prefix=f".{root.name}.", suffix=".staging", dir=parent)
    )
    staging_fd = -1
    published = False
    try:
        if _identity(os.fstat(parent_fd)) != _identity(os.lstat(parent)):
            raise ValueError("output parent replacement after staging creation")
        staging_lexical = os.stat(
            staging.name, dir_fd=parent_fd, follow_symlinks=False
        )
        if stat.S_ISLNK(staging_lexical.st_mode) or not stat.S_ISDIR(
            staging_lexical.st_mode
        ):
            raise ValueError("unsafe staging root")
        staging_fd = os.open(staging.name, directory_flags, dir_fd=parent_fd)
        if _identity(os.fstat(staging_fd)) != _identity(staging_lexical):
            raise ValueError("staging root stat/open race")
        for name in FILES:
            _write_exclusive_leaf(staging_fd, name, payloads[name])
        os.fsync(staging_fd)
        staging_identity = _identity(os.fstat(staging_fd))
        if _identity(
            os.stat(staging.name, dir_fd=parent_fd, follow_symlinks=False)
        ) != staging_identity:
            raise ValueError("staging root identity drift before publish")
        try:
            _rename_noreplace(staging, root, parent_fd)
        except OSError as error:
            if error.errno == errno.EEXIST and _read_output_set(root, payloads):
                if staging_fd >= 0:
                    os.close(staging_fd)
                    staging_fd = -1
                _cleanup_staging(staging)
                return json.loads(payloads[MANIFEST])
            raise
        published = True
        published_identity = _identity(os.fstat(staging_fd))
        if published_identity[:3] != staging_identity[:3]:
            raise ValueError("published staging object identity drift")
        if _identity(
            os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
        ) != published_identity:
            raise ValueError("destination name/inode binding mismatch")
        try:
            os.stat(staging.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("staging name remains after publish")
        if _identity(os.fstat(staging_fd)) != published_identity:
            raise ValueError("published staging FD identity drift")
        os.fsync(parent_fd)
        if (
            _identity(
                os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != published_identity
            or _identity(os.fstat(staging_fd)) != published_identity
            or _identity(os.fstat(parent_fd)) != _identity(os.lstat(parent))
        ):
            raise ValueError("post-fsync destination binding drift")
        if not _read_output_set(root, payloads, published_identity):
            raise ValueError("published output postverify failed")
    except BaseException:
        if not published:
            _cleanup_staging(staging)
        raise
    finally:
        if staging_fd >= 0:
            os.close(staging_fd)
        os.close(parent_fd)
    return json.loads(payloads[MANIFEST])


def run_covapie_bulk_download_admission_admit_014_formal_evaluator_interface_preconditions_audit_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Explicitly materialize the audit; importing the module has no side effect."""
    return materialize_audit(output_root)
