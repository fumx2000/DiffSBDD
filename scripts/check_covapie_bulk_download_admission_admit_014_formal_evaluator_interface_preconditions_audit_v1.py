"""Independent checker for the ADMIT_014 precondition audit Exact10 stage."""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE = "3ec07b2daa7e6fc2d51df2641e85c13be2196ff3"
PARENT = "dd17566f1b82eebcaaa49f17172a7b22a83b9c53"
TREE = "2d0f838cf2d7c4b197fd8ca44d0f6f5cb66b3750"
SUBJECT = "add CovaPIE unified dispatch runtime with ADMIT_001 to ADMIT_013 v1"
STAGE = (
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_preconditions_audit_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / (
    "covapie_bulk_download_admission_admit_014_"
    "rule_logic_interface_preconditions_audit_v1"
)
PRE = "covapie_admit_014_formal_evaluator_precondition_matrix.csv"
AUTH = "covapie_admit_014_authorization_evidence_and_routing_responsibility_matrix.csv"
STATE = "covapie_admit_014_current_gate_observed_state_inventory.csv"
SOURCE = "covapie_admit_014_source_boundary_audit.csv"
ISSUE = "covapie_admit_014_issue_readiness_inventory.csv"
MANIFEST = "covapie_admit_014_formal_evaluator_preconditions_manifest.json"
FILES = (PRE, AUTH, STATE, SOURCE, ISSUE, MANIFEST)

PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_preconditions_audit.py"
)
CHECKER = Path(
    "scripts/"
    "check_covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_preconditions_audit_v1.py"
)
TEST = Path(
    "tests/"
    "test_covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_preconditions_audit_v1.py"
)
DOC = Path(
    "docs/"
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_preconditions_audit_v1_summary.md"
)
EXACT10 = (
    PRODUCTION,
    CHECKER,
    TEST,
    DOC,
    *(OUTPUT_ROOT / name for name in FILES),
)

HEADERS = {
    PRE: (
        "precondition_order", "precondition_id", "precondition_group",
        "precondition_subject", "expected_contract", "observed_evidence",
        "completeness_status", "implementation_blocking", "blocking_reason",
        "precondition_passed",
    ),
    AUTH: (
        "matrix_order", "matrix_group", "case_id", "authority_or_envelope",
        "committed_evidence", "authority_classification",
        "current_observed_state", "future_contract_requirement",
        "completeness_status", "implementation_blocking", "blocking_reason",
        "case_passed",
    ),
    STATE: (
        "inventory_order", "state_item", "source_path", "source_field_or_row",
        "expected_current_state", "observed_current_state",
        "authority_classification", "state_passed",
    ),
    SOURCE: (
        "source_order", "source_relative_path", "expected_sha256",
        "base_tree_mode", "tracked", "base_tree_blob", "filesystem_regular",
        "non_symlink", "parent_chain_non_symlink", "safe_descendant",
        "pinned_fd_read", "post_read_identity_verified", "source_verified",
    ),
}

DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
PRE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_"
    "implementation_precondition_gate_v1"
)
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1"
)
QA_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_qa_gate_v1")
SOURCES = (
    (
        Path("src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py"),
        "79ecb3fb1084ddc161d1bec1a7db664ffbeda71952e31e4233317ecd487905d6",
    ),
    (DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv", "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc"),
    (DESIGN_ROOT / "covapie_bulk_download_admission_safety_audit.csv", "388869caf582bdf624d0016cae385dc2268f6cc05f54ecc9bf140608bbd3b208"),
    (DESIGN_ROOT / "covapie_bulk_download_admission_design_gate_manifest.json", "085cb2f2a6bfe9bebe9e503dd10aa0b4d6f9ad754ff99539b1bafb33c78b5444"),
    (PRE_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv", "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b"),
    (PRE_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv", "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0"),
    (PRE_ROOT / "covapie_bulk_download_admission_implementation_issue_inventory.csv", "7c7707f5261461083bda7ab2177a423b608c725c070dafaff558bdf39256211e"),
    (PRE_ROOT / "covapie_bulk_download_admission_implementation_precondition_manifest.json", "2304b5754d8052b4b186981a98c12f259608a3492947e069c2afab84084a0d52"),
    (
        Path("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013.py"),
        "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892",
    ),
    (RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_contract.csv", "035effd65ca65ed1442bb7a29c03986390209f6d129d2ae078e223101c6a6144"),
    (RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_issue_readiness_inventory.csv", "477b4192579d3f64dac5bd0cc61c1a378b2f28c3355251e344b79999801a5d69"),
    (RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_safety_audit.csv", "4b0c11cb59193bdfea9b7011e63ad4262cbbff2c1d57fd276de064997c28d8b4"),
    (RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_manifest.json", "2940e6cc02a92b4919cdece3b1fa7c2f5e27d844f2962bb18757197266c23f79"),
    (QA_ROOT / "covapie_final_dataset_qa_v1_safety_training_boundary_audit.csv", "8ea6a53d04456443014ba250a0cfacf4983e39d2138d7035ad188dc1dcceebe5"),
    (QA_ROOT / "covapie_final_dataset_qa_v1_manifest.json", "4f7c884379f926af52101f40a7870b243f0309af3b1637dc65c8c0691acf9f35"),
)

OUTPUT_SHA256 = {
    PRE: "6b52a4e96dd960e7df53b7160f5cd00d63fbeb62ee5bc5ec9882623efd268c30",
    AUTH: "c1804d6ff7bd0a6eecb68877defa41316dd8afc999fb1152eba323f185b03834",
    STATE: "0de58b224639f5eb624ecf0055eed5654706d8aa64c57138d7f91493b664eb59",
    SOURCE: "52dd3b004dbfee76bacf0e2ddd55b39fc1659f7763cc150007b7a4801721b511",
    ISSUE: "6af875d474f0c0e1320f2584eec080acf6cf4d1097c25f004380430e4c5fab06",
    MANIFEST: "b9582357f392a6aa1af68012a1469c886b2de4b5af8196cddad56f94625e4b61",
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
TRUE_KEYS = (
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
FALSE_KEYS = (
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
BASE_MANIFEST_KEYS = (
    "project", "stage", "base_commit", "base_parent", "base_tree", "base_subject",
    "canonical_evidence_python_implementation", "canonical_evidence_python_version",
    "ast_attestation_cross_python_version_portable", "noncanonical_python_policy",
    "python_runtime_migration_policy", "admission_rule_id", "admission_rule_name",
    "evidence_source", "required_status", "failure_severity", "blocking_reason",
    "evaluation_phase", "network_required", "raw_structure_required",
    "ready_for_future_implementation",
    "ready_for_future_implementation_means_contract_design_only",
    "ready_for_future_implementation_grants_download_permission",
    "current_gate_grants_download_permission",
    "current_gate_bulk_download_not_authorized",
    "current_gate_network_not_authorized", "current_gate_provider_not_authorized",
    "current_gate_raw_write_not_authorized", "current_stage_network_execution_count",
    "current_stage_download_queue_count", "current_stage_download_manifest_count",
    "current_stage_raw_write_count", "admit_014_evaluator_model",
    "admit_014_evaluator_model_selected", "current_stage_constant_guard_rejected",
    "authorization_context_item", "authorization_context_scope",
    "authorization_context_provided_by_future_caller",
    "authorization_context_exact_contract_available",
    "authorization_context_implementation_ready_in_step14au_a",
    "successor_runtime_envelope_ownership_frozen",
    "stage_authorization_context_present_in_dispatcher_signature",
    "stage_authorization_context_admit_014_semantics_frozen",
    "precondition_schema", "precondition_row_count", "precondition_group_counts",
    "precondition_complete_count", "precondition_incomplete_count",
    "precondition_implementation_blocking_count", "authorization_matrix_schema",
    "authorization_matrix_row_count", "authorization_matrix_group_counts",
    "authorization_matrix_complete_count", "authorization_matrix_incomplete_count",
    "current_state_inventory_schema", "current_state_inventory_row_count",
    "source_boundary_schema", "source_count", "source_boundary",
    "source_validation_before_output_read", "issue_schema", "issue_row_count",
    "inherited_issue_row_count", "new_admit_014_issue_row_count",
    "new_admit_014_issue_ids", "open_issue_ids",
    "coverage_issue_affected_rules", "readiness", "safety", "output_files",
    "output_file_count", "output_sha256", "recommended_next_step",
    "step12d_status", "feature_semantics_note", "renameat2_policy",
    "all_checks_passed",
)
EXPECTED_MANIFEST_KEYS = BASE_MANIFEST_KEYS + TRUE_KEYS + FALSE_KEYS


def _guard() -> None:
    if sys.implementation.name != "cpython" or tuple(sys.version_info[:3]) != (3, 10, 4):
        raise RuntimeError("independent checker requires canonical CPython 3.10.4")


def _git(
    args: list[str], repo_root: Path = REPO_ROOT
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True, check=False
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
    flags_dir = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    flags_leaf = (
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    root_lexical = os.lstat(repo_root)
    if stat.S_ISLNK(root_lexical.st_mode) or not stat.S_ISDIR(root_lexical.st_mode):
        raise ValueError("unsafe repository root")
    root_identity = _identity(root_lexical)
    descriptors: list[tuple[int, Identity, int | None, str | None]] = []
    root_fd = os.open(repo_root, flags_dir)
    if _identity(os.fstat(root_fd)) != root_identity:
        os.close(root_fd)
        raise ValueError("repository root stat/open race")
    descriptors.append((root_fd, root_identity, None, None))
    try:
        parent_fd = root_fd
        for part in path.parts[:-1]:
            lexical = os.stat(part, dir_fd=parent_fd, follow_symlinks=False)
            lexical_identity = _identity(lexical)
            if stat.S_ISLNK(lexical.st_mode) or not stat.S_ISDIR(lexical.st_mode):
                raise ValueError("unsafe source parent")
            child_fd = os.open(part, flags_dir, dir_fd=parent_fd)
            if _identity(os.fstat(child_fd)) != lexical_identity:
                os.close(child_fd)
                raise ValueError("source parent stat/open race")
            descriptors.append((child_fd, lexical_identity, parent_fd, part))
            parent_fd = child_fd
        before = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise ValueError(f"unsafe source leaf: {path}")
        expected = _identity(before)
        leaf_fd = os.open(path.name, flags_leaf, dir_fd=parent_fd)
        try:
            if _identity(os.fstat(leaf_fd)) != expected:
                raise ValueError("source stat/open race")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(leaf_fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            if _identity(os.fstat(leaf_fd)) != expected:
                raise ValueError("source FD identity drift")
        finally:
            os.close(leaf_fd)
        if _identity(os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)) != expected:
            raise ValueError("source lexical replacement")
        for fd, expected_id, lexical_parent_fd, lexical_name in descriptors:
            if _identity(os.fstat(fd)) != expected_id:
                raise ValueError("source parent FD identity drift")
            if lexical_parent_fd is not None and lexical_name is not None:
                if _identity(
                    os.stat(
                        lexical_name,
                        dir_fd=lexical_parent_fd,
                        follow_symlinks=False,
                    )
                ) != expected_id:
                    raise ValueError("source parent lexical replacement")
        if (
            _identity(os.lstat(repo_root)) != root_identity
            or _identity(os.fstat(root_fd)) != root_identity
        ):
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
    result: dict[Path, bytes] = {}
    for path, digest in SOURCES:
        index = _git(["ls-files", "--stage", "--", path.as_posix()])
        tree = _git(["ls-tree", BASE, "--", path.as_posix()])
        if index.returncode or tree.returncode or not index.stdout or not tree.stdout:
            raise ValueError(f"source is not current-index/base tracked: {path}")
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
            or index_fields[2] != "0"
            or index_fields[0] != tree_fields[0]
            or index_fields[1] != tree_fields[2]
            or tree_fields[1] != "blob"
        ):
            raise ValueError(f"source index/base mode/blob drift: {path}")
        current = _pinned_relative(path)
        if hashlib.sha256(current).hexdigest() != digest:
            raise ValueError(f"source SHA mismatch: {path}")
        base = subprocess.run(
            ["git", "show", f"{BASE}:{path.as_posix()}"], cwd=REPO_ROOT,
            capture_output=True, check=False,
        )
        if base.returncode or base.stdout != current:
            raise ValueError(f"source base/current mismatch: {path}")
        result[path] = current
    return result


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
    parent_lexical = os.lstat(parent)
    if stat.S_ISLNK(parent_lexical.st_mode) or not stat.S_ISDIR(parent_lexical.st_mode):
        raise ValueError("unsafe output parent")
    parent_identity = _identity(parent_lexical)
    parent_fd = os.open(parent, directory_flags)
    root_fd = -1
    leaves: list[tuple[str, int, Identity, bytes]] = []
    outputs: dict[str, bytes] = {}
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("output parent stat/open race")
        root_lexical = os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
        if stat.S_ISLNK(root_lexical.st_mode) or not stat.S_ISDIR(root_lexical.st_mode):
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
                raise ValueError(f"unsafe output leaf: {name}")
            identity = _identity(before)
            descriptor = os.open(name, leaf_flags, dir_fd=root_fd)
            if _identity(os.fstat(descriptor)) != identity:
                os.close(descriptor)
                raise ValueError("output stat/open race")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            leaves.append((name, descriptor, identity, b"".join(chunks)))

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
            outputs[name] = data
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
        return outputs
    finally:
        for _, descriptor, _, _ in leaves:
            os.close(descriptor)
        if root_fd >= 0:
            os.close(root_fd)
        os.close(parent_fd)


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_manifest_exact(data: bytes) -> dict[str, Any]:
    manifest = json.loads(data, object_pairs_hook=_pairs_no_duplicates)
    if tuple(manifest) != EXPECTED_MANIFEST_KEYS:
        raise ValueError("manifest missing/extra/reordered keys")
    return manifest


def _validate_output_hashes(outputs: dict[str, bytes]) -> None:
    if set(outputs) != set(FILES):
        raise ValueError("Exact6 output key mismatch")
    for name, expected in OUTPUT_SHA256.items():
        if hashlib.sha256(outputs[name]).hexdigest() != expected:
            raise ValueError(f"frozen output SHA mismatch: {name}")


def _validate_manifest_readiness(manifest: dict[str, Any]) -> None:
    expected = {
        **{key: True for key in TRUE_KEYS},
        **{key: False for key in FALSE_KEYS},
    }
    if manifest["readiness"] != expected:
        raise ValueError("manifest readiness drift")
    if any(manifest[key] is not True for key in TRUE_KEYS):
        raise ValueError("flattened true readiness drift")
    if any(manifest[key] is not False for key in FALSE_KEYS):
        raise ValueError("flattened false readiness drift")


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode(), newline="")))


def _validate_step14aua_lineage(snapshot: dict[Path, bytes]) -> None:
    executable_path = (
        PRE_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"
    )
    context_path = (
        PRE_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"
    )
    executable = next(
        row
        for row in _rows(snapshot[executable_path])
        if row["admission_rule_id"] == "ADMIT_014"
    )
    expected_executable = {
        "admission_rule_id": "ADMIT_014",
        "admission_rule_name": "current_gate_grants_no_download_permission",
        "evaluation_phase": "current_step",
        "candidate_field_dependencies": "",
        "batch_context_dependencies": "",
        "evaluation_context_dependencies": "current_stage_download_authorized",
        "external_filesystem_required": "false",
        "network_required": "false",
        "download_execution_result_required": "false",
        "pure_in_memory_interface_possible": "true",
        "dependency_contract_passed": "true",
        "semantics_complete": "true",
        "deterministic_evaluation_possible_now": "true",
        "deterministic_evaluation_possible_after_contract_freeze": "true",
        "implementation_disposition": "rule_logic_ready",
        "blocking_reasons": "",
    }
    if executable != expected_executable:
        raise ValueError("Step14AU-A ADMIT_014 executability lineage drift")
    context = next(
        row
        for row in _rows(snapshot[context_path])
        if row["context_item"] == "current_stage_download_authorized"
    )
    expected_context = {
        "context_item": "current_stage_download_authorized",
        "context_scope": "stage",
        "required_by_rules": "ADMIT_014",
        "provided_by_future_caller": "true",
        "filesystem_access_inside_evaluator": "false",
        "network_access_inside_evaluator": "false",
        "deterministic_now": "true",
        "deterministic_after_contract_freeze": "true",
        "exact_contract_defined": "true",
        "implementation_ready": "true",
        "blocking_reasons": "",
    }
    if context != expected_context:
        raise ValueError("Step14AU-A authorization context lineage drift")


def _lifecycle(
    repo_root: Path = REPO_ROOT,
    base: str = BASE,
    exact10: tuple[Path, ...] = EXACT10,
    output_root: Path = OUTPUT_ROOT,
) -> str:
    if _git(["merge-base", "--is-ancestor", base, "HEAD"], repo_root).returncode:
        raise ValueError("base nonancestor")
    if len(exact10) != 10 or len(set(exact10)) != 10:
        raise ValueError("Exact10 path contract drift")
    forbidden_suffixes = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
        ".npz", ".tmp", ".part",
    }
    if any(path.suffix in forbidden_suffixes for path in exact10):
        raise ValueError("forbidden candidate suffix")
    states: list[str] = []
    for path in exact10:
        if not (repo_root / path).exists() or (repo_root / path).is_symlink():
            raise ValueError(f"missing or symlink candidate: {path}")
        if (repo_root / path).stat().st_size > 100 * 1024 * 1024:
            raise ValueError(f"oversized candidate: {path}")
        ignored = _git(
            ["check-ignore", "--no-index", "-q", "--", path.as_posix()],
            repo_root,
        )
        if ignored.returncode == 0:
            raise ValueError(f"ignored candidate: {path}")
        if ignored.returncode != 1:
            raise ValueError(f"candidate ignore check failed: {path}")
        tracked = _git(
            ["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root
        )
        untracked = _git(
            ["ls-files", "--others", "--exclude-standard", "--", path.as_posix()],
            repo_root,
        )
        staged = _git(
            ["diff", "--cached", "--name-only", "--", path.as_posix()], repo_root
        )
        working = _git(["diff", "--name-only", "--", path.as_posix()], repo_root)
        if staged.stdout.strip():
            raise ValueError(f"stage path is staged: {path}")
        if tracked.returncode == 0:
            if untracked.stdout.strip() or working.stdout.strip():
                raise ValueError(f"dirty post-commit candidate: {path}")
            states.append("post_commit")
        elif tracked.returncode != 0:
            if untracked.stdout.splitlines() != [path.as_posix()] or working.stdout.strip():
                raise ValueError(f"invalid pre-commit candidate: {path}")
            states.append("pre_commit")
    if len(set(states)) != 1:
        raise ValueError("mixed lifecycle")

    suffix = "admit_014_formal_evaluator_interface_preconditions_audit"
    expected_stage_files = set(exact10[:4])
    found: set[Path] = set()
    for directory in ("src/covalent_ext", "scripts", "tests", "docs"):
        for path in (repo_root / directory).glob(f"*{suffix}*"):
            if path.is_file() or path.is_symlink():
                found.add(path.relative_to(repo_root))
    if found != expected_stage_files:
        raise ValueError("extra or missing same-stage source/checker/test/doc")
    stage_roots = sorted(
        (repo_root / output_root.parent).glob(f"{output_root.name}*")
    )
    expected_root = repo_root / output_root
    if stage_roots != [expected_root] or expected_root.is_symlink():
        raise ValueError("extra or missing same-stage derived root")
    inventory = {path.name for path in expected_root.iterdir()}
    if inventory != set(FILES):
        raise ValueError("missing or seventh Exact6 output")
    if any(
        path.is_symlink()
        or not path.is_file()
        or path.stat().st_size > 100 * 1024 * 1024
        or path.suffix in forbidden_suffixes
        for path in expected_root.iterdir()
    ):
        raise ValueError("unsafe Exact6 lifecycle leaf")
    return states[0]


def _validate_production_ast() -> None:
    tree = ast.parse((REPO_ROOT / PRODUCTION).read_text(encoding="utf-8"))
    forbidden = {
        "evaluate_admit_014", "Admit014EvaluationResult",
        "_evaluate_registered_admit_014", "EVALUATOR_REGISTRY",
        "evaluate_admission_rule",
    }
    defined = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    assigned = {
        target.id for node in ast.walk(tree) if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    if forbidden & (defined | assigned):
        raise ValueError("production contains forbidden evaluator/adapter/runtime")
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    if imported & {"requests", "urllib", "torch", "numpy", "rdkit", "Bio", "gemmi"}:
        raise ValueError("production imports forbidden execution dependency")
    text = (REPO_ROOT / PRODUCTION).read_text(encoding="utf-8")
    if "os.replace" in text:
        raise ValueError("forbidden replacement fallback")


def validate() -> str:
    _guard()
    snapshot = _source_snapshot()  # source authority is verified before output reads
    _validate_step14aua_lineage(snapshot)
    lifecycle = _lifecycle()
    outputs = _pinned_outputs(REPO_ROOT / OUTPUT_ROOT)
    _validate_output_hashes(outputs)
    manifest = _parse_manifest_exact(outputs[MANIFEST])

    pre = _rows(outputs[PRE])
    auth = _rows(outputs[AUTH])
    state = _rows(outputs[STATE])
    source = _rows(outputs[SOURCE])
    issues = _rows(outputs[ISSUE])
    if tuple(pre[0]) != HEADERS[PRE] or len(pre) != 51:
        raise ValueError("precondition schema/count mismatch")
    if [row["precondition_order"] for row in pre] != [str(i) for i in range(1, 52)]:
        raise ValueError("precondition order mismatch")
    if [row["precondition_id"] for row in pre] != [f"PRE_{i:03d}" for i in range(1, 52)]:
        raise ValueError("precondition ID mismatch")
    complete = [row["completeness_status"] for row in pre]
    expected_complete_orders = set(range(1, 15)) | {
        16, 18, 27, 28, 29, 30, 32, 35, 43, 44, 51
    }
    if any(
        status != ("complete" if index in expected_complete_orders else "incomplete")
        for index, status in enumerate(complete, 1)
    ):
        raise ValueError("precondition completeness drift")
    if any(row["precondition_passed"] != "true" for row in pre):
        raise ValueError("audit row failure")
    if sum(row["implementation_blocking"] == "true" for row in pre) != 26:
        raise ValueError("implementation blocker count drift")
    expected_observed = {
        18: "current_stage_download_authorized committed by Step14AU-A",
        27: "future_explicit_authorization_context selected; current_stage_constant_guard rejected",
        28: "Step14AU-A context_scope=stage",
        29: "candidate_field_dependencies is empty",
        30: "batch_context_dependencies is empty",
        32: "Step14AU-A dependency is a stage-scoped authorization context, not a download result",
        44: "Step14AU-A lists only current_stage_download_authorized; workflow enforcement remains unresolved",
    }
    if any(
        pre[order - 1]["observed_evidence"] != value
        for order, value in expected_observed.items()
    ):
        raise ValueError("Step14AU-A inherited precondition lineage drift")

    if tuple(auth[0]) != HEADERS[AUTH] or len(auth) != 20:
        raise ValueError("authorization matrix schema/count mismatch")
    if [row["case_id"] for row in auth] != [f"AUTH_{i:03d}" for i in range(1, 21)]:
        raise ValueError("authorization case order mismatch")
    if sum(row["completeness_status"] == "complete" for row in auth) != 10:
        raise ValueError("authorization completeness drift")
    if any(row["case_passed"] != "true" for row in auth):
        raise ValueError("authorization audit failure")
    if [auth[4]["authority_or_envelope"], auth[5]["authority_or_envelope"]] != [
        "current_stage_constant_guard", "future_explicit_authorization_context"
    ]:
        raise ValueError("candidate models drift")
    if (
        auth[4]["authority_classification"] != "committed alternative rejected"
        or auth[5]["authority_classification"]
        != "authoritative inherited selection"
        or auth[6]["current_observed_state"]
        != "forbidden as authorization source"
        or auth[7]["current_observed_state"]
        != "forbidden as authorization source"
        or auth[9]["current_observed_state"]
        != "forbidden as authorization source"
        or auth[12]["current_observed_state"]
        != "current_stage_download_authorized"
    ):
        raise ValueError("authorization lineage classification drift")
    expected_unresolved_envelopes = {
        3: (
            "stage-scoped context identity known; exact evaluation_context "
            "versus stage_authorization_context ownership unresolved"
        ),
        9: (
            "stage-scoped context identity known; exact successor envelope "
            "ownership unresolved"
        ),
        11: (
            "stage-scoped context identity known; exact successor envelope "
            "ownership unresolved"
        ),
    }
    for order, observed in expected_unresolved_envelopes.items():
        if auth[order - 1]["current_observed_state"] != observed:
            raise ValueError("successor envelope ownership was fabricated")

    if tuple(state[0]) != HEADERS[STATE] or len(state) != 13:
        raise ValueError("current-state schema/count mismatch")
    if any(row["state_passed"] != "true" for row in state):
        raise ValueError("current-state inventory failure")
    context_state = next(
        row
        for row in state
        if row["state_item"]
        == "Step14AU-A current_stage_download_authorized context"
    )
    if (
        context_state["authority_classification"] != "authoritative"
        or "context_scope=stage" not in context_state["observed_current_state"]
        or "exact_contract_defined=true" not in context_state["observed_current_state"]
        or "implementation_ready=true" not in context_state["observed_current_state"]
    ):
        raise ValueError("current-state context authority drift")

    if tuple(source[0]) != HEADERS[SOURCE] or len(source) != len(SOURCES):
        raise ValueError("source audit schema/count mismatch")
    if [row["source_relative_path"] for row in source] != [
        path.as_posix() for path, _ in SOURCES
    ]:
        raise ValueError("source audit path order mismatch")
    if [row["expected_sha256"] for row in source] != [digest for _, digest in SOURCES]:
        raise ValueError("source audit SHA mismatch")
    if any(row["source_verified"] != "true" for row in source):
        raise ValueError("source audit failed")

    inherited = _rows(
        snapshot[
            RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_issue_readiness_inventory.csv"
        ]
    )
    if len(issues) != 30 or issues[:23] != inherited:
        raise ValueError("inherited Exact23 issue continuity failure")
    if [row["issue_id"] for row in issues[23:]] != list(NEW_ISSUES):
        raise ValueError("new Exact7 issue identity/order mismatch")
    if {
        "ADMIT_014_EVALUATOR_SCOPE_UNRESOLVED",
        "ADMIT_014_GLOBAL_VS_CANDIDATE_SCOPE_UNRESOLVED",
    } & {row["issue_id"] for row in issues}:
        raise ValueError("removed pseudo-issue reintroduced")
    if any(
        row["severity"] != "blocking"
        or row["status"] != "open"
        or row["successor_effective_status"] != "open"
        or row["issue_origin"] != STAGE
        or row["successor_transition_action"] != "new_open"
        for row in issues[23:]
    ):
        raise ValueError("new issue state drift")
    coverage = next(
        row for row in issues if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    )
    if coverage["affected_rules"] != "ADMIT_014|ADMIT_015":
        raise ValueError("ADMIT_014 prematurely removed from coverage issue")

    exact_identity = {
        "admission_rule_id": "ADMIT_014",
        "admission_rule_name": "current_gate_grants_no_download_permission",
        "evidence_source": "current_design_gate",
        "required_status": "bulk_download_not_authorized_now",
        "failure_severity": "blocking",
        "blocking_reason": "bulk_download_not_authorized",
        "evaluation_phase": "current_step",
        "network_required": False,
        "raw_structure_required": False,
        "ready_for_future_implementation": True,
    }
    if any(manifest[key] != value for key, value in exact_identity.items()):
        raise ValueError("manifest ADMIT_014 identity drift")
    if not (
        manifest["admit_014_evaluator_model"]
        == "future_explicit_authorization_context"
        and manifest["admit_014_evaluator_model_selected"] is True
        and manifest["current_stage_constant_guard_rejected"] is True
        and manifest["authorization_context_item"]
        == "current_stage_download_authorized"
        and manifest["authorization_context_scope"] == "stage"
        and manifest["authorization_context_provided_by_future_caller"] is True
        and manifest["authorization_context_exact_contract_available"] is True
        and manifest["authorization_context_implementation_ready_in_step14au_a"]
        is True
        and manifest["successor_runtime_envelope_ownership_frozen"] is False
    ):
        raise ValueError("manifest explicit-context lineage drift")
    if manifest["precondition_row_count"] != 51:
        raise ValueError("manifest precondition count drift")
    if (
        manifest["precondition_complete_count"] != 25
        or manifest["precondition_incomplete_count"] != 26
        or manifest["precondition_implementation_blocking_count"] != 26
    ):
        raise ValueError("manifest precondition classification drift")
    if (
        manifest["authorization_matrix_row_count"] != 20
        or manifest["authorization_matrix_complete_count"] != 10
        or manifest["authorization_matrix_incomplete_count"] != 10
    ):
        raise ValueError("manifest authorization count drift")
    if (
        manifest["issue_row_count"] != 30
        or manifest["inherited_issue_row_count"] != 23
        or manifest["new_admit_014_issue_ids"] != list(NEW_ISSUES)
    ):
        raise ValueError("manifest issue inventory drift")
    _validate_manifest_readiness(manifest)
    if manifest["coverage_issue_affected_rules"] != "ADMIT_014|ADMIT_015":
        raise ValueError("manifest coverage drift")
    if manifest["recommended_next_step"] != (
        "design_covapie_admit_014_download_authorization_contract_v1"
    ):
        raise ValueError("unsafe next-step recommendation")
    if manifest["output_files"] != list(FILES) or manifest["output_file_count"] != 6:
        raise ValueError("manifest output inventory drift")
    if manifest["output_sha256"] != {
        name: OUTPUT_SHA256[name] for name in FILES[:-1]
    }:
        raise ValueError("manifest non-self output SHA drift")
    if (
        manifest["current_gate_grants_download_permission"] is not False
        or manifest["ready_for_future_implementation_grants_download_permission"]
        is not False
        or manifest["stage_authorization_context_admit_014_semantics_frozen"]
        is not False
    ):
        raise ValueError("download permission or routing was fabricated")
    if any(manifest["safety"].values()):
        raise ValueError("safety boundary drift")
    if manifest["all_checks_passed"] is not True:
        raise ValueError("manifest audit did not pass")
    _validate_production_ast()
    return lifecycle


def main() -> int:
    lifecycle = validate()
    print(f"stage={STAGE}")
    print(f"base_commit={BASE}")
    print("canonical_evidence_python=cpython-3.10.4")
    print(f"source_count={len(SOURCES)}")
    print("precondition_rows=51")
    print("precondition_complete=25")
    print("precondition_incomplete=26")
    print("authorization_rows=20")
    print("issue_rows=30")
    print("new_admit_014_issues=7")
    print("current_gate_grants_download_permission=false")
    print("ready_for_bulk_download_now=false")
    print("admit_014_registered_in_engine=false")
    print("recommended_next_step=design_covapie_admit_014_download_authorization_contract_v1")
    print(f"lifecycle={lifecycle}")
    print(f"{STAGE}_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
