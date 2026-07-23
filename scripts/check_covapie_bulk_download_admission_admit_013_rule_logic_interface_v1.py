#!/usr/bin/env python3
"""Independent fail-closed checker for ADMIT_013 standalone evaluator v1."""

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


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "79e63dce368722b126ad21208a3de13f7ea4b6df"
BASE_PARENT = "2eea08835c4ef88d5b810509134f8eef94e3e99e"
BASE_TREE = "ac3633abc2cf52a715faf36faea827f76d4236d9"
BASE_SUBJECT = "add CovaPIE ADMIT_013 formal evaluator interface contract v1"
STAGE = "covapie_bulk_download_admission_admit_013_rule_logic_interface_v1"
CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = (3, 10, 4)
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"
PRODUCTION_PATH = Path(
    "src/covalent_ext/covapie_bulk_download_admission_admit_013_rule_logic_interface.py"
)
CHECKER_PATH = Path(
    "scripts/check_covapie_bulk_download_admission_admit_013_rule_logic_interface_v1.py"
)
TEST_PATH = Path(
    "tests/test_covapie_bulk_download_admission_admit_013_rule_logic_interface_v1.py"
)
SUMMARY_PATH = Path(
    "docs/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1_summary.md"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
OUTPUT_FILES = (
    "covapie_admit_013_rule_logic_interface_contract.csv",
    "covapie_admit_013_rule_logic_interface_truth_matrix.csv",
    "covapie_admit_013_rule_logic_interface_source_boundary_audit.csv",
    "covapie_admit_013_rule_logic_interface_purity_audit.csv",
    "covapie_admit_013_rule_logic_interface_issue_readiness_inventory.csv",
    "covapie_admit_013_rule_logic_interface_manifest.json",
)
STAGE_PATHS = (
    PRODUCTION_PATH,
    CHECKER_PATH,
    TEST_PATH,
    SUMMARY_PATH,
    *(OUTPUT_ROOT / name for name in OUTPUT_FILES),
)
STAGE_TOP_LEVEL_DIRECTORIES = (
    Path("src/covalent_ext"),
    Path("scripts"),
    Path("tests"),
    Path("docs"),
)
STAGE_TOP_LEVEL_GLOB = "*admit_013_rule_logic_interface*"
FORBIDDEN_SUFFIXES = {
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part",
}

DOWNLOAD_FIELDS = (
    "download_result_status", "observed_http_status",
    "observed_content_length_bytes", "observed_sha256",
)
AUTHORITY_FIELDS = (
    "expected_content_length_bytes", "expected_sha256", "explicit_integrity_verdict",
)
PARAMETERS = (*DOWNLOAD_FIELDS, *AUTHORITY_FIELDS)
RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_download_result_record", "canonical_integrity_authority_record",
    "validated_download_result_fields", "validated_integrity_authority_fields",
    "consumed_download_result_fields", "consumed_integrity_authority_fields",
    "evaluator_io_used",
)
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid")
VALIDATION_PHASES = (
    "Exact4_presence", "Exact4_type_value",
    "Exact3_optional_authority_type_value", "Exact7_business_outcome", "passed",
)
REASON_VOCABULARY = (
    "", "DOWNLOAD_RESULT_STATUS_MISSING", "OBSERVED_HTTP_STATUS_MISSING",
    "OBSERVED_CONTENT_LENGTH_BYTES_MISSING", "OBSERVED_SHA256_MISSING",
    "DOWNLOAD_RESULT_STATUS_TYPE_INVALID", "DOWNLOAD_RESULT_STATUS_VALUE_INVALID",
    "OBSERVED_HTTP_STATUS_TYPE_INVALID", "OBSERVED_HTTP_STATUS_RANGE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID", "OBSERVED_SHA256_TYPE_INVALID",
    "OBSERVED_SHA256_FORMAT_INVALID", "EXPECTED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
    "EXPECTED_CONTENT_LENGTH_BYTES_RANGE_INVALID", "EXPECTED_SHA256_TYPE_INVALID",
    "EXPECTED_SHA256_FORMAT_INVALID", "EXPLICIT_INTEGRITY_VERDICT_TYPE_INVALID",
    "EXPLICIT_INTEGRITY_VERDICT_VALUE_INVALID", "DOWNLOAD_RESULT_STATUS_FAILURE",
    "OBSERVED_HTTP_STATUS_NOT_SUCCESS", "OBSERVED_CONTENT_EMPTY",
    "OBSERVED_SHA256_MISMATCH", "EXPLICIT_INTEGRITY_VERDICT_FAILED",
    "OBSERVED_CONTENT_LENGTH_MISMATCH", "INTEGRITY_AUTHORITY_MISSING",
)
BUSINESS_REASONS = REASON_VOCABULARY[-7:]
FORMAL_MARKER = "# === ADMIT_013 FORMAL EVALUATOR CLOSURE END ==="
FORMAL_CLOSURE = (
    "evaluate_admit_013", "_make_result", "_business_reason",
    "Admit013EvaluationResult", "Admit013EvaluationResult.__post_init__",
    "_download_value_valid", "_authority_value_valid", "_pair_record_shape_valid",
    "_name_tuple_valid", "_MissingAdmit013Value",
)
EXPECTED_PRODUCTION_SHA256 = "36a4d3080128dadcecbdda25c5a3e143ac054aba001e7ac9cd7de0e2c51307f4"
EXPECTED_PREFIX_SHA256 = "e5b6e3e51022b342f022f38a498d7b64e7b882382ea887260d34acf9ea0e00c2"
EXPECTED_AST_SHA256 = {
    "evaluate_admit_013": "0b42e4c6e4d51e1b60a39af66d42ba3b0a86c5daa3e088bec1dbabb4995eb91f",
    "_make_result": "6c404d01cde2b88b4103996606421f975087dcc15fbdf6ac67985a8b9a109379",
    "_business_reason": "eb714b15ae11489501c7e6c3bc96fd8b66c2f926784a1870d67f6329ef68af52",
    "Admit013EvaluationResult": "30793fc44c5522e9408241349b1801e8591bdb21fe5f8008238dd0bee59ae113",
    "Admit013EvaluationResult.__post_init__": "5d3d041f10e11e204d5eb0e9b2ff754a4b71d6bff801c63603de85c2fd6ae2d5",
    "_download_value_valid": "5da80ba5d90e13579caca05cc291d05a05e7be4e080d486a557f371ce4bfc815",
    "_authority_value_valid": "ff60eb0868bdc31784cc8be92e05260a170b39f654092513c3166199faea0919",
    "_pair_record_shape_valid": "6aaa58c523af2eaf7e1b23560ee2977cbbbe2d7967d6f4f6a4879ebff625b1ef",
    "_name_tuple_valid": "8428ddcce209873193f9cc59690ed9ac915f6811e3b685ca5107cfcd6014a030",
    "_MissingAdmit013Value": "036c3099407e7a052d48a6a6dc37b269b41c7144bfe52a0c1e96eb623944ca0b",
}
EXPECTED_OUTPUT_SHA256 = {
    "covapie_admit_013_rule_logic_interface_contract.csv": "74cf6af87efb8661ddb6a2e5931827c0bd9a0148fb26fdaa3f9dd5da970e5e6f",
    "covapie_admit_013_rule_logic_interface_truth_matrix.csv": "2399d1551e42b9343c1b849bb9a4fd06a2758c07e4ceff3be2d4758d9d519f52",
    "covapie_admit_013_rule_logic_interface_source_boundary_audit.csv": "fbaa3eb5ee82a036932884c6c29a7528700eb6a5f6af45098aab164208a05ac3",
    "covapie_admit_013_rule_logic_interface_purity_audit.csv": "0798e983838d42d635de786575c502a1472970fabe8459a51e8a8212d343e081",
    "covapie_admit_013_rule_logic_interface_issue_readiness_inventory.csv": "e2d895dc822e5de8d6f1410e41f6cd79407b090a0055ebe2a79aeadabf033214",
    "covapie_admit_013_rule_logic_interface_manifest.json": "3ecbbc4d99966c955b39cad4dae65ef9c8316c7847bd43ccef82c44863cd4fa5",
}
SOURCE_SHA256 = {
    "src/covalent_ext/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate.py": "256d5d0bfd54fe5accc4493051809aafec58a41b6cf56b9090dbf19f80b2a2e3",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_and_result_contract.csv": "655ff7c2af7f95a9eef8742e3fac3635b3a914be39aa1bf0cb5efc392d3ee6a7",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_routing_and_consumption_contract.csv": "55b78fdf124efc0310d4e55b8564568c7cd88c5e3155666a75162d6c54c1af90",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_truth_matrix.csv": "1ffafe3dac824c91e9dcb3fef8760e1f8f1e92754755816d4cef2d0f58fd5631",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_issue_readiness_inventory.csv": "e2d895dc822e5de8d6f1410e41f6cd79407b090a0055ebe2a79aeadabf033214",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_contract_manifest.json": "5cadbddf7d75aac7b92f5f86ad204e96237ea80a58f4372eaa22460b4385ea71",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv": "7e856eb5ebd995793dcd82fb75266c7ee6f6a8b06b7785f3a70713a96b8efdbb",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_and_integrity_contract_manifest.json": "1bbfe88f459946b78bb14e5b0b672582d508a838bef220ecf292fa84d15f934d",
    "src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py": "a7b8585ea6d0080e87fc97f29026fbf5df4667dff21729c95f3045d762a55840",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_manifest.json": "ad131895c0acfdaf5b350105031647bdcac9667370fb6cd43baf8826bea995c8",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py": "4d9a49806d4ef71a95c8ad032dfa061f7473b1cb55a573459c155f0cd5d57282",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_manifest.json": "bc909aefd86b62139fbb62025d9c323988a4c232ab9c960efb291fb0c196cee3",
}
SOURCE_PATH_LIST_SHA256 = "d61ddc0b6b0063d41b9b063a744412c079e3e6c529169141371ca8f73f79dcd0"
SOURCE_PATH_SHA256_PAIRS_SHA256 = "4399ae88529132a7e872419c95490e0978857248205956b63515b154b3d0aae7"
NEGATIVE_RESULT_CASES = (
    "WRONG_TOP_LEVEL_RESULT_TYPE", "RESULT_SUBCLASS", "STORAGE_NOT_EXACT_DATACLASS",
    "MISSING_FIELD", "EXTRA_FIELD", "FIELD_REORDER", "PASSED_INT_ONE",
    "BLOCKS_INT_ZERO", "CANONICAL_OUTER_LIST", "MALFORMED_PAIR", "PAIR_LIST",
    "PAIR_SUBCLASS", "TUPLE_SUBCLASS", "WRONG_PAIR_NAME", "WRONG_PAIR_ORDER",
    "DUPLICATE_PAIR", "EXTRA_PAIR", "CANONICAL_AUTHORITY_CONTAINS_MISSING_FIELD",
    "VALIDATED_TUPLE_LIST", "CONSUMED_TUPLE_LIST", "VALIDATED_NAME_NOT_EXACT_STR",
    "CONSUMED_NAME_NOT_EXACT_STR", "DESIGN_SENTINEL_LEAK", "EVALUATOR_IO_TRUE",
    "OUTCOME_REASON_INVARIANT_CONFLICT", "ADMISSION_RULE_ID_DRIFT",
)
CONTRACT_COLUMNS = (
    "contract_order", "contract_section", "section_order", "public_name",
    "formal_type", "required", "frozen_value", "formal_invariant",
    "implementation_source", "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "assertion_kind", "inherited_case_id",
    *(f"{name}_representation" for name in PARAMETERS),
    "expected_design_result", "observed_formal_result", "exact_type_value_equality",
    "evaluator_io_used", "formal_source", "truth_passed",
)
SOURCE_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "base_tree_mode",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256",
    "frozen_snapshot_sha256", "git_tracked", "base_tree_blob",
    "filesystem_regular", "non_symlink", "parent_chain_non_symlink",
    "safe_descendant", "pinned_fd_read", "triple_sha256_passed",
    "source_boundary_passed",
)
PURITY_COLUMNS = (
    "audit_order", "audit_kind", "definition_name", "definition_kind",
    "reachable_from", "normalized_ast_sha256", "permitted_global_bindings",
    "permitted_calls", "observed", "forbidden_io_absent", "mutation_absent",
    "dynamic_dispatch_absent", "purity_passed",
)
ISSUE_COLUMNS = (
    "inherited_order", "issue_id", "issue_type", "affected_fields", "affected_rules",
    "severity", "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count", "inherited_effective_status",
    "inherited_transition_stage", "inherited_transition_action",
    "inherited_transition_evidence", "successor_effective_status",
    "successor_transition_stage", "successor_transition_action",
    "successor_transition_evidence",
)
EXPECTED_MANIFEST_KEYS = (
    "Admit013EvaluationResult_implemented",
    "actual_evaluator_design_oracle_projection_passed",
    "adapter_registry_runtime_changed",
    "admission_rule_id",
    "admit_013_download_outcome_and_integrity_contract_designed",
    "admit_013_formal_evaluator_interface_contract_frozen",
    "admit_013_formal_result_contract_frozen",
    "admit_013_future_evaluator_pure_in_memory_possible",
    "admit_013_preconditions_audited",
    "admit_013_registered_in_engine",
    "admit_013_rule_logic_implemented",
    "admit_013_standalone_evaluator_interface_implemented",
    "admit_013_standalone_signature_frozen",
    "admit_013_unified_adapter_contract_frozen",
    "admit_013_unified_adapter_implemented",
    "admit_013_validation_precedence_resolved",
    "all_checks_passed",
    "ast_attestation_cross_python_version_portable",
    "authority_fields",
    "authorized_admit_013_download_execution_count",
    "base_commit",
    "base_parent",
    "base_subject",
    "base_tree",
    "business_failure_precedence",
    "canonical_evidence_python_implementation",
    "canonical_evidence_python_version",
    "combined_candidate_verdict_implemented",
    "coverage_affected_rules",
    "cross_rule_aggregation_implemented",
    "download_fields",
    "evaluate_admit_013_implemented",
    "feature_semantics_audit_required_before_training",
    "feature_semantics_audit_requirement",
    "formal_ast_sha256",
    "formal_closure",
    "formal_closure_count",
    "formal_evaluator_implemented",
    "formal_marker_prefix_sha256",
    "formal_production_sha256",
    "formal_result_type_defined",
    "inherited_business_projection_passed",
    "issue_inventory_byte_identical_to_formal_interface",
    "issue_transition_count",
    "manifest_schema_version",
    "materialization_policy",
    "noncanonical_python_policy",
    "outcome_vocabulary",
    "output_file_count",
    "output_files",
    "output_sha256",
    "parameter_order",
    "private_missing_singleton",
    "project",
    "provider_mapping_validated",
    "public_evaluator",
    "public_signature",
    "purity_closure_complete",
    "python_runtime_migration_policy",
    "readiness",
    "ready_for_admit_013_standalone_evaluator_interface_implementation",
    "ready_for_admit_013_unified_adapter_contract_design",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "real_provider_evaluation_ready",
    "reason_vocabulary",
    "reason_vocabulary_count_including_empty",
    "recommended_next_step",
    "remaining_open_issue_ids",
    "result_field_count",
    "result_fields",
    "result_negative_projection_rejected",
    "result_type",
    "row_counts",
    "safety",
    "source_boundary",
    "source_count",
    "source_path_list_sha256",
    "source_path_sha256_pairs_sha256",
    "stage",
    "step12d_is_final_training_feature_contract",
    "step12d_status",
    "truth_matrix_group_counts",
    "truth_matrix_passed",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "validation_phase_order",
)


class _Missing:
    pass


MISSING = _Missing()


class _StrSubclass(str):
    pass


class _IntSubclass(int):
    pass


def _git(arguments: list[str], *, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=text, check=False
    )


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_canonical_evidence_runtime_identity(
    implementation_name: str,
    version: tuple[int, int, int],
) -> None:
    if (
        implementation_name != CANONICAL_PYTHON_IMPLEMENTATION
        or tuple(version) != CANONICAL_PYTHON_VERSION
    ):
        observed_version = ".".join(str(part) for part in version)
        raise RuntimeError(
            "canonical evidence runtime required: CPython 3.10.4; "
            f"observed implementation: {implementation_name}; "
            f"observed version: {observed_version}; "
            "frozen AST evidence is version-sensitive; noncanonical Python may only "
            "be used for evaluator-only semantic smoke"
        )


def _assert_canonical_evidence_runtime() -> None:
    _validate_canonical_evidence_runtime_identity(
        sys.implementation.name,
        tuple(sys.version_info[:3]),
    )


def _identity(item: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )


def _assert_repo_root() -> tuple[int, int, int, int, int, int]:
    item = os.lstat(REPO_ROOT)
    if (
        stat.S_ISLNK(item.st_mode)
        or not stat.S_ISDIR(item.st_mode)
        or REPO_ROOT.resolve(strict=True) != REPO_ROOT
    ):
        raise ValueError("unsafe repository root")
    return _identity(item)


def _assert_safe_source_path(path: Path) -> None:
    if (
        path.is_absolute()
        or not path.parts
        or ".." in path.parts
        or path.parts[:2] == ("data", "raw")
        or path.parts[0] == "checkpoints"
        or STAGE in path.parts
    ):
        raise ValueError(f"unsafe source path: {path}")


def _assert_parent_chain(path: Path) -> None:
    current = (REPO_ROOT / path).parent
    while current != REPO_ROOT:
        if current == current.parent:
            raise ValueError(f"source escaped repository: {path}")
        item = os.lstat(current)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
            raise ValueError(f"unsafe source parent chain: {path}")
        current = current.parent


def _read_regular(path: Path) -> bytes:
    _assert_safe_source_path(path)
    root_identity = _assert_repo_root()
    _assert_parent_chain(path)
    absolute = REPO_ROOT / path
    item = os.lstat(absolute)
    expected_identity = _identity(item)
    if (
        stat.S_ISLNK(item.st_mode)
        or not stat.S_ISREG(item.st_mode)
        or absolute.resolve(strict=True) != absolute
    ):
        raise ValueError(f"not a regular non-symlink file: {path}")
    descriptor = os.open(
        absolute,
        os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError(f"stat/open race: {path}")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError(f"FD identity drift: {path}")
        if _identity(os.lstat(absolute)) != expected_identity:
            raise ValueError(f"identity drift: {path}")
        _assert_parent_chain(path)
        if _assert_repo_root() != root_identity:
            raise ValueError("repository root identity drift")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _check_base_and_sources() -> tuple[dict[str, bytes], dict[str, str]]:
    _assert_canonical_evidence_runtime()
    root_identity = _assert_repo_root()
    identity = _git(["show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if identity.returncode or ancestor.returncode:
        raise ValueError("base lineage unavailable")
    if identity.stdout.splitlines() != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("base identity drift")
    path_list = "\n".join(SOURCE_SHA256) + "\n"
    pairs = "\n".join(f"{path}\t{digest}" for path, digest in SOURCE_SHA256.items()) + "\n"
    if _sha(path_list.encode()) != SOURCE_PATH_LIST_SHA256:
        raise ValueError("source path-list attestation drift")
    if _sha(pairs.encode()) != SOURCE_PATH_SHA256_PAIRS_SHA256:
        raise ValueError("source pair attestation drift")
    sources = {}
    modes = {}
    for relative, expected in SOURCE_SHA256.items():
        path = Path(relative)
        _assert_safe_source_path(path)
        _assert_parent_chain(path)
        tracked = _git(["ls-files", "--error-unmatch", "--", relative])
        tree = _git(["ls-tree", BASE_COMMIT, "--", relative])
        head, separator, tree_path = tree.stdout.partition("\t")
        parts = head.split()
        if (
            tracked.returncode
            or tracked.stdout.splitlines() != [relative]
            or tree.returncode
            or not separator
            or tree_path.strip() != relative
            or len(parts) != 3
            or parts[0] not in {"100644", "100755"}
            or parts[1] != "blob"
        ):
            raise ValueError(f"unsafe base source lineage: {relative}")
        base = _git(["show", f"{BASE_COMMIT}:{relative}"], text=False)
        current = _read_regular(path)
        if (
            base.returncode
            or not isinstance(base.stdout, bytes)
            or _sha(base.stdout) != expected
            or _sha(current) != expected
        ):
            raise ValueError(f"source SHA drift: {relative}")
        sources[relative] = current
        modes[relative] = parts[0]
    if _assert_repo_root() != root_identity:
        raise ValueError("repository root identity drift")
    return sources, modes


def _literal_assignment(tree: ast.Module, name: str):
    node = next(
        item for item in tree.body
        if isinstance(item, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in item.targets)
    )
    return ast.literal_eval(node.value)


def _check_formal_source() -> tuple[bytes, dict[str, str]]:
    _assert_canonical_evidence_runtime()
    source = _read_regular(PRODUCTION_PATH)
    if _sha(source) != EXPECTED_PRODUCTION_SHA256:
        raise ValueError("production full SHA drift")
    text = source.decode()
    if text.count(FORMAL_MARKER) != 1:
        raise ValueError("formal marker missing or duplicated")
    prefix = text.split(FORMAL_MARKER, 1)[0].encode()
    if _sha(prefix) != EXPECTED_PREFIX_SHA256:
        raise ValueError("formal marker-prefix SHA drift")
    tree = ast.parse(prefix)
    if _literal_assignment(tree, "DOWNLOAD_FIELDS") != DOWNLOAD_FIELDS:
        raise ValueError("download field order drift")
    if _literal_assignment(tree, "AUTHORITY_FIELDS") != AUTHORITY_FIELDS:
        raise ValueError("authority field order drift")
    if _literal_assignment(tree, "OUTCOME_VOCABULARY") != OUTCOME_VOCABULARY:
        raise ValueError("outcome vocabulary drift")
    if _literal_assignment(tree, "VALIDATION_PHASES") != VALIDATION_PHASES:
        raise ValueError("validation phase order drift")
    if _literal_assignment(tree, "RESULT_FIELDS") != RESULT_FIELDS:
        raise ValueError("result field order drift")
    if _literal_assignment(tree, "REASON_VOCABULARY") != REASON_VOCABULARY:
        raise ValueError("reason vocabulary drift")
    definitions = {
        node.name: node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    if set(definitions) != {
        "_MissingAdmit013Value", "_download_value_valid", "_authority_value_valid",
        "_pair_record_shape_valid", "_name_tuple_valid", "_business_reason",
        "Admit013EvaluationResult", "_make_result", "evaluate_admit_013",
    }:
        raise ValueError("formal definition set drift")
    sentinel = definitions["_MissingAdmit013Value"]
    if (
        sentinel.bases
        or sentinel.keywords
        or sentinel.decorator_list
        or len(sentinel.body) != 1
        or not isinstance(sentinel.body[0], ast.Assign)
        or len(sentinel.body[0].targets) != 1
        or not isinstance(sentinel.body[0].targets[0], ast.Name)
        or sentinel.body[0].targets[0].id != "__slots__"
        or not isinstance(sentinel.body[0].value, ast.Tuple)
        or sentinel.body[0].value.elts
    ):
        raise ValueError("private sentinel class definition drift")
    evaluator = definitions["evaluate_admit_013"]
    args = evaluator.args
    if (
        args.posonlyargs or args.args or args.vararg is not None or args.kwarg is not None
        or tuple(arg.arg for arg in args.kwonlyargs) != PARAMETERS
        or len(args.kw_defaults) != 7
        or any(not isinstance(default, ast.Name) or default.id != "_MISSING" for default in args.kw_defaults)
    ):
        raise ValueError("exact seven-keyword-only signature drift")
    if not isinstance(evaluator.returns, ast.Name) or evaluator.returns.id != "Admit013EvaluationResult":
        raise ValueError("evaluator return annotation drift")
    result_class = definitions["Admit013EvaluationResult"]
    decorators = result_class.decorator_list
    if len(decorators) != 1 or not isinstance(decorators[0], ast.Call):
        raise ValueError("result dataclass decorator drift")
    decorator = decorators[0]
    if not isinstance(decorator.func, ast.Name) or decorator.func.id != "dataclass":
        raise ValueError("result must be dataclass")
    if not any(
        keyword.arg == "frozen" and isinstance(keyword.value, ast.Constant)
        and keyword.value.value is True for keyword in decorator.keywords
    ):
        raise ValueError("result dataclass must be frozen")
    class_fields = tuple(
        node.target.id for node in result_class.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    )
    if class_fields != RESULT_FIELDS:
        raise ValueError("Exact12 storage order drift")
    post = next(
        node for node in result_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "__post_init__"
    )
    nodes = {
        name: post if name.endswith(".__post_init__") else definitions[name]
        for name in FORMAL_CLOSURE
    }
    digests = {
        name: _sha(ast.dump(node, annotate_fields=True, include_attributes=False).encode())
        for name, node in nodes.items()
    }
    if digests != EXPECTED_AST_SHA256:
        raise ValueError("normalized formal AST digest drift")
    forbidden_names = {
        "open", "eval", "exec", "getattr", "globals", "locals", "__import__",
        "subprocess", "socket", "Path",
    }
    for name, node in nodes.items():
        if any(isinstance(item, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)) for item in ast.walk(node)):
            raise ValueError(f"purity statement violation: {name}")
        if any(isinstance(item, ast.Name) and item.id in forbidden_names for item in ast.walk(node)):
            raise ValueError(f"purity binding violation: {name}")
        if any(
            isinstance(item, ast.Attribute)
            and item.attr in {"open", "read", "write", "fsync", "replace"}
            for item in ast.walk(node)
        ):
            raise ValueError(f"purity I/O violation: {name}")
    if "classify_admit_013_formal_evaluator_interface_design" in prefix.decode():
        raise ValueError("formal closure calls design oracle")
    return source, digests


def _decode(text: str):
    if text == "<MISSING>":
        return MISSING
    if text == "<object>":
        return object()
    if text.startswith("<str-subclass:"):
        return _StrSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<int-subclass:"):
        return _IntSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<bytes:"):
        return ast.literal_eval(text[7:-1]).encode()
    return ast.literal_eval(text)


def _independent_oracle(values: tuple[object, ...]) -> tuple:
    missing_reasons = REASON_VOCABULARY[1:5]
    download_type = (
        "DOWNLOAD_RESULT_STATUS_TYPE_INVALID", "OBSERVED_HTTP_STATUS_TYPE_INVALID",
        "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID", "OBSERVED_SHA256_TYPE_INVALID",
    )
    download_value = (
        "DOWNLOAD_RESULT_STATUS_VALUE_INVALID", "OBSERVED_HTTP_STATUS_RANGE_INVALID",
        "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID", "OBSERVED_SHA256_FORMAT_INVALID",
    )
    authority_type = (
        "EXPECTED_CONTENT_LENGTH_BYTES_TYPE_INVALID", "EXPECTED_SHA256_TYPE_INVALID",
        "EXPLICIT_INTEGRITY_VERDICT_TYPE_INVALID",
    )
    authority_value = (
        "EXPECTED_CONTENT_LENGTH_BYTES_RANGE_INVALID", "EXPECTED_SHA256_FORMAT_INVALID",
        "EXPLICIT_INTEGRITY_VERDICT_VALUE_INVALID",
    )

    def result(outcome, reason, download, authority, valid_d, valid_a, used_d, used_a):
        return (
            "ADMIT_013", outcome, outcome == "passed", outcome != "passed", reason,
            download, authority, valid_d, valid_a, used_d, used_a, False,
        )

    for index, value in enumerate(values[:4]):
        if value is MISSING:
            return result(
                "blocked", missing_reasons[index], (), (), DOWNLOAD_FIELDS[:index], (),
                DOWNLOAD_FIELDS[:index + 1], (),
            )
    download = []
    for index, value in enumerate(values[:4]):
        expected_type = (str, int, int, str)[index]
        if type(value) is not expected_type:
            return result("invalid", download_type[index], (), (), DOWNLOAD_FIELDS[:index], (), DOWNLOAD_FIELDS, ())
        valid = (
            value in {"success", "failure"} if index == 0
            else 100 <= value <= 599 if index == 1
            else value >= 0 if index == 2
            else len(value) == 64 and value.isascii() and all(character in "0123456789abcdef" for character in value)
        )
        if not valid:
            return result("invalid", download_value[index], (), (), DOWNLOAD_FIELDS[:index], (), DOWNLOAD_FIELDS, ())
        download.append((DOWNLOAD_FIELDS[index], value))
    canonical_download = tuple(download)
    authority = []
    for index, value in enumerate(values[4:]):
        if value is MISSING:
            continue
        expected_type = (int, str, str)[index]
        if type(value) is not expected_type:
            return result(
                "invalid", authority_type[index], canonical_download, tuple(authority),
                DOWNLOAD_FIELDS, tuple(pair[0] for pair in authority), DOWNLOAD_FIELDS,
                AUTHORITY_FIELDS[:index + 1],
            )
        valid = (
            value >= 0 if index == 0
            else len(value) == 64 and value.isascii() and all(character in "0123456789abcdef" for character in value) if index == 1
            else value in {"verified", "failed"}
        )
        if not valid:
            return result(
                "invalid", authority_value[index], canonical_download, tuple(authority),
                DOWNLOAD_FIELDS, tuple(pair[0] for pair in authority), DOWNLOAD_FIELDS,
                AUTHORITY_FIELDS[:index + 1],
            )
        authority.append((AUTHORITY_FIELDS[index], value))
    canonical_authority = tuple(authority)
    observed = dict(canonical_download)
    trusted = dict(canonical_authority)
    if observed[DOWNLOAD_FIELDS[0]] == "failure":
        reason = BUSINESS_REASONS[0]
    elif not 200 <= observed[DOWNLOAD_FIELDS[1]] <= 299:
        reason = BUSINESS_REASONS[1]
    elif observed[DOWNLOAD_FIELDS[2]] == 0:
        reason = BUSINESS_REASONS[2]
    elif AUTHORITY_FIELDS[1] in trusted and trusted[AUTHORITY_FIELDS[1]] != observed[DOWNLOAD_FIELDS[3]]:
        reason = BUSINESS_REASONS[3]
    elif trusted.get(AUTHORITY_FIELDS[2]) == "failed":
        reason = BUSINESS_REASONS[4]
    elif AUTHORITY_FIELDS[0] in trusted and trusted[AUTHORITY_FIELDS[0]] != observed[DOWNLOAD_FIELDS[2]]:
        reason = BUSINESS_REASONS[5]
    elif not (
        trusted.get(AUTHORITY_FIELDS[1]) == observed[DOWNLOAD_FIELDS[3]]
        or trusted.get(AUTHORITY_FIELDS[2]) == "verified"
    ):
        reason = BUSINESS_REASONS[6]
    else:
        reason = ""
    return result(
        "passed" if not reason else "blocked", reason, canonical_download,
        canonical_authority, DOWNLOAD_FIELDS, tuple(pair[0] for pair in authority),
        DOWNLOAD_FIELDS, AUTHORITY_FIELDS,
    )


def _csv_rows(
    data: bytes,
    expected_columns: tuple[str, ...],
    label: str,
) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(data.decode(), newline=""))
    if tuple(reader.fieldnames or ()) != expected_columns:
        raise ValueError(f"{label} schema/order drift")
    return list(reader)


def _expected_contract_rows(ast_digests: dict[str, str]) -> list[dict[str, str]]:
    rows = []

    def add(
        section: str,
        name: str,
        formal_type: str,
        required: bool,
        value: str,
        invariant: str,
    ) -> None:
        section_order = 1 + sum(row["contract_section"] == section for row in rows)
        rows.append({
            "contract_order": str(len(rows) + 1),
            "contract_section": section,
            "section_order": str(section_order),
            "public_name": name,
            "formal_type": formal_type,
            "required": str(required).lower(),
            "frozen_value": value,
            "formal_invariant": invariant,
            "implementation_source": "formal_closure",
            "contract_passed": "true",
        })

    for index, name in enumerate(PARAMETERS):
        add(
            "signature_parameter",
            name,
            "object",
            index < 4,
            "keyword_only|private_shared_missing_singleton",
            "Exact7 order; no positional/varargs/varkw/Mapping/normalization",
        )
    result_types = (
        "str", "str", "bool", "bool", "str", "tuple", "tuple", "tuple",
        "tuple", "tuple", "tuple", "bool",
    )
    for name, formal_type in zip(RESULT_FIELDS, result_types, strict=True):
        add(
            "result_field",
            name,
            formal_type,
            True,
            "Exact12_ordered",
            "exact built-in top-level type and reason-phase state invariant",
        )
    for reason in REASON_VOCABULARY:
        add(
            "reason_vocabulary",
            reason or "<empty>",
            "str",
            True,
            reason,
            "closed Exact26 ordered vocabulary; no catch-all or free text",
        )
    for phase in VALIDATION_PHASES:
        add(
            "validation_phase",
            phase,
            "phase",
            True,
            phase,
            "first failure returns; frozen Exact5 order",
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
    invariants = (
        ("exact_result_type", "type(self) is Admit013EvaluationResult"),
        ("exact_result_storage", "dataclass fields equal RESULT_FIELDS"),
        ("exact_top_level_types", "exact str/bool/tuple only"),
        ("identity", "admission_rule_id == ADMIT_013"),
        ("outcome", "closed Exact3"),
        ("reason", "closed Exact26"),
        ("passed", "passed iff outcome passed"),
        ("blocks_candidate", "blocks iff outcome not passed"),
        ("reason_emptiness", "reason empty iff outcome passed"),
        ("evaluator_io", "evaluator_io_used is False"),
        ("canonical_records", "exact ordered raw pair tuples; no sentinel"),
        ("phase_state", "canonical/validated/consumed agree with reason phase"),
    )
    for name, invariant in invariants:
        add("result_invariant", name, "invariant", True, invariant, "fail closed")
    for name in (
        "no_adapter_or_runtime", "no_provider_or_network", "no_raw_or_download",
        "no_model_checkpoint_dataloader_training",
    ):
        add("safety_boundary", name, "boolean", True, "true", "absence attested")
    if len(rows) != 76:
        raise ValueError("checker contract expectation row count drift")
    return rows


def _expected_purity_rows(ast_digests: dict[str, str]) -> list[dict[str, str]]:
    parents = (
        "root", "evaluate_admit_013", "evaluate_admit_013",
        "_make_result|_business_reason", "Admit013EvaluationResult",
        "evaluate_admit_013|Admit013EvaluationResult.__post_init__",
        "evaluate_admit_013|Admit013EvaluationResult.__post_init__",
        "Admit013EvaluationResult.__post_init__",
        "Admit013EvaluationResult.__post_init__",
        "evaluate_admit_013|signature_defaults|_MISSING",
    )
    kinds = (
        "function", "function", "function", "frozen_dataclass", "method",
        "function", "function", "function", "function", "private sentinel class",
    )
    rows = []
    for index, name in enumerate(FORMAL_CLOSURE):
        rows.append({
            "audit_order": str(index + 1),
            "audit_kind": "closure_definition",
            "definition_name": name,
            "definition_kind": kinds[index],
            "reachable_from": parents[index],
            "normalized_ast_sha256": ast_digests[name],
            "permitted_global_bindings": "immutable_formal_constants|pure_helpers",
            "permitted_calls": "exact_builtin_and_formal_helper_calls",
            "observed": "reachable_and_frozen",
            "forbidden_io_absent": "true",
            "mutation_absent": "true",
            "dynamic_dispatch_absent": "true",
            "purity_passed": "true",
        })
    metadata = (
        ("production_full_sha256", EXPECTED_PRODUCTION_SHA256),
        ("marker_prefix_sha256", EXPECTED_PREFIX_SHA256),
        ("closure_complete", "|".join(FORMAL_CLOSURE)),
        ("forbidden_io", "open|Path_IO|os_IO|subprocess|socket|provider|raw absent"),
        (
            "forbidden_dynamic_dispatch",
            "import_in_function|eval|exec|getattr|globals|locals absent",
        ),
        ("mutable_global_state", "absent"),
    )
    for name, observed in metadata:
        rows.append({
            "audit_order": str(len(rows) + 1),
            "audit_kind": "closure_metadata",
            "definition_name": name,
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
        })
    if len(rows) != 16:
        raise ValueError("checker purity expectation row count drift")
    return rows


def _expected_source_rows(source_modes: dict[str, str]) -> list[dict[str, str]]:
    return [{
        "source_order": str(index),
        "source_relative_path": relative,
        "source_kind": (
            "python_source" if Path(relative).suffix == ".py"
            else "committed_csv" if Path(relative).suffix == ".csv"
            else "committed_manifest"
        ),
        "base_tree_mode": source_modes[relative],
        "expected_sha256": digest,
        "base_tree_sha256": digest,
        "filesystem_sha256": digest,
        "frozen_snapshot_sha256": digest,
        "git_tracked": "true",
        "base_tree_blob": "true",
        "filesystem_regular": "true",
        "non_symlink": "true",
        "parent_chain_non_symlink": "true",
        "safe_descendant": "true",
        "pinned_fd_read": "true",
        "triple_sha256_passed": "true",
        "source_boundary_passed": "true",
    } for index, (relative, digest) in enumerate(SOURCE_SHA256.items(), 1)]


def _read_output_leaf_at(
    root_fd: int,
    name: str,
    expected_identity: tuple[int, int, int, int, int, int],
) -> bytes:
    if _identity(os.lstat(name, dir_fd=root_fd)) != expected_identity:
        raise ValueError(f"output leaf identity drift before open: {name}")
    descriptor = os.open(
        name,
        os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
        dir_fd=root_fd,
    )
    try:
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError(f"output leaf stat/open race: {name}")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError(f"output leaf FD identity drift: {name}")
        if _identity(os.lstat(name, dir_fd=root_fd)) != expected_identity:
            raise ValueError(f"output leaf lexical identity drift: {name}")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _read_pinned_output_payloads(root: Path) -> dict[str, bytes]:
    parent_item = os.lstat(root.parent)
    parent_identity = _identity(parent_item)
    if (
        stat.S_ISLNK(parent_item.st_mode)
        or not stat.S_ISDIR(parent_item.st_mode)
        or root.parent.resolve(strict=True) != root.parent
    ):
        raise ValueError("unsafe output parent")
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        stat.S_ISLNK(root_item.st_mode)
        or not stat.S_ISDIR(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("unsafe output root")
    root_fd = os.open(
        root,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root stat/open race")
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("Exact6 output inventory drift")
        leaf_identities = {}
        for name in OUTPUT_FILES:
            item = os.lstat(name, dir_fd=root_fd)
            if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
                raise ValueError(f"unsafe output leaf: {name}")
            leaf_identities[name] = _identity(item)
        payloads = {
            name: _read_output_leaf_at(root_fd, name, leaf_identities[name])
            for name in OUTPUT_FILES
        }
        if _identity(os.lstat(root.parent)) != parent_identity:
            raise ValueError("output parent lexical identity drift")
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root FD identity drift")
        if _identity(os.lstat(root)) != root_identity:
            raise ValueError("output root lexical identity drift")
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("output inventory drift after traversal")
        if any(
            _identity(os.lstat(name, dir_fd=root_fd)) != leaf_identities[name]
            for name in OUTPUT_FILES
        ):
            raise ValueError("output leaf identity drift after traversal")
        return payloads
    finally:
        os.close(root_fd)


def _json_object_without_duplicates(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate manifest key: {key}")
        result[key] = value
    return result


def _validate_output_semantics(
    payloads: dict[str, bytes],
    sources: dict[str, bytes],
    source_modes: dict[str, str],
    ast_digests: dict[str, str],
) -> dict:
    if set(payloads) != set(OUTPUT_FILES):
        raise ValueError("Exact6 semantic payload inventory drift")
    truth = _csv_rows(payloads[OUTPUT_FILES[1]], TRUTH_COLUMNS, "truth matrix")
    if len(truth) != 128 or [row["case_order"] for row in truth] != [str(i) for i in range(1, 129)]:
        raise ValueError("Exact128 truth order drift")
    predecessor = _csv_rows(
        sources[next(path for path in SOURCE_SHA256 if path.endswith("formal_evaluator_interface_truth_matrix.csv"))],
        tuple(csv.DictReader(io.StringIO(
            sources[next(path for path in SOURCE_SHA256 if path.endswith("formal_evaluator_interface_truth_matrix.csv"))].decode()
        )).fieldnames or ()),
        "predecessor truth matrix",
    )
    if len(predecessor) != 128:
        raise ValueError("predecessor Exact128 drift")
    representation_columns = tuple(f"{name}_representation" for name in PARAMETERS)
    negative_ids = []
    normal_count = 0
    business_count = 0
    for prior, row in zip(predecessor, truth, strict=True):
        inherited_columns = (
            "case_order", "case_id", "case_group", "assertion_kind", "inherited_case_id",
            *representation_columns,
        )
        if any(row[column] != prior[column] for column in inherited_columns):
            raise ValueError("truth inherited identity/input drift")
        if row["expected_design_result"] != prior["observed_design_result"]:
            raise ValueError("truth Design expectation drift")
        if row["case_id"] in NEGATIVE_RESULT_CASES:
            negative_ids.append(row["case_id"])
            if not row["observed_formal_result"].startswith("RESULT_CONTRACT_REJECTED:"):
                raise ValueError("negative result was not rejected")
        else:
            values = tuple(_decode(row[column]) for column in representation_columns)
            expected = _independent_oracle(values)
            if ast.literal_eval(row["observed_formal_result"]) != expected:
                raise ValueError(f"independent oracle mismatch: {row['case_id']}")
            if row["expected_design_result"] != repr(expected):
                raise ValueError(f"committed Design projection mismatch: {row['case_id']}")
            normal_count += 1
            business_count += row["case_group"] == "inherited_exact7_business_projection"
        if (
            row["exact_type_value_equality"] != "true"
            or row["evaluator_io_used"] != "false"
            or row["formal_source"] != "evaluate_admit_013|Admit013EvaluationResult"
            or row["truth_passed"] != "true"
        ):
            raise ValueError("truth pass/I/O assertion drift")
    if tuple(negative_ids) != NEGATIVE_RESULT_CASES or normal_count != 102 or business_count != 23:
        raise ValueError("Exact102/Exact23/Exact26 projection count drift")
    contract = _csv_rows(payloads[OUTPUT_FILES[0]], CONTRACT_COLUMNS, "contract")
    source_rows = _csv_rows(payloads[OUTPUT_FILES[2]], SOURCE_COLUMNS, "source audit")
    purity = _csv_rows(payloads[OUTPUT_FILES[3]], PURITY_COLUMNS, "purity audit")
    issues = _csv_rows(payloads[OUTPUT_FILES[4]], ISSUE_COLUMNS, "issue inventory")
    if contract != _expected_contract_rows(ast_digests):
        raise ValueError("implementation contract drift")
    if source_rows != _expected_source_rows(source_modes):
        raise ValueError("source boundary evidence drift")
    if purity != _expected_purity_rows(ast_digests):
        raise ValueError("purity evidence drift")
    predecessor_issues = sources[
        next(path for path in SOURCE_SHA256 if path.endswith("formal_evaluator_interface_issue_readiness_inventory.csv"))
    ]
    if payloads[OUTPUT_FILES[4]] != predecessor_issues or len(issues) != 23:
        raise ValueError("Exact23 issue bytes/identity drift")
    by_id = {row["issue_id"]: row for row in issues}
    required_open = (
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    )
    if any(by_id[name]["successor_effective_status"] != "open" for name in required_open):
        raise ValueError("required issue was closed")
    manifest = json.loads(
        payloads[OUTPUT_FILES[5]],
        object_pairs_hook=_json_object_without_duplicates,
    )
    if tuple(manifest) != EXPECTED_MANIFEST_KEYS:
        raise ValueError("manifest exact top-level keys/order drift")
    for value in manifest.values():
        if isinstance(value, dict) and tuple(value) != tuple(sorted(value)):
            raise ValueError("manifest nested key order drift")
    expected_readiness_true = (
        "admit_013_preconditions_audited",
        "admit_013_download_outcome_and_integrity_contract_designed",
        "admit_013_standalone_signature_frozen", "admit_013_formal_result_contract_frozen",
        "admit_013_formal_evaluator_interface_contract_frozen",
        "admit_013_validation_precedence_resolved",
        "admit_013_future_evaluator_pure_in_memory_possible",
        "ready_for_admit_013_standalone_evaluator_interface_implementation",
        "evaluate_admit_013_implemented", "Admit013EvaluationResult_implemented",
        "admit_013_rule_logic_implemented",
        "admit_013_standalone_evaluator_interface_implemented",
        "ready_for_admit_013_unified_adapter_contract_design",
        "feature_semantics_audit_required_before_training",
    )
    expected_readiness_false = (
        "admit_013_unified_adapter_contract_frozen", "admit_013_unified_adapter_implemented",
        "admit_013_registered_in_engine",
        "unified_dispatch_runtime_with_admit_001_to_013_implemented",
        "provider_mapping_validated", "real_provider_evaluation_ready",
        "ready_for_bulk_download_now", "combined_candidate_verdict_implemented",
        "cross_rule_aggregation_implemented", "ready_for_training",
        "step12d_is_final_training_feature_contract",
    )
    if any(manifest["readiness"][name] is not True for name in expected_readiness_true):
        raise ValueError("required true readiness drift")
    if any(manifest["readiness"][name] is not False for name in expected_readiness_false):
        raise ValueError("required false readiness drift")
    expected_readiness = {
        **{name: True for name in expected_readiness_true},
        **{name: False for name in expected_readiness_false},
    }
    expected_output_sha = {
        name: EXPECTED_OUTPUT_SHA256[name]
        for name in sorted(OUTPUT_FILES[:-1])
    }
    expected_row_counts = {
        "evaluator_result_projection": 102,
        "formal_contract": 76,
        "inherited_business_projection": 23,
        "issue_inventory": 23,
        "purity_audit": 16,
        "result_negative_projection": 26,
        "source_boundary": 12,
        "truth_matrix": 128,
    }
    expected_safety = {
        "dataloader": False,
        "download": False,
        "model_or_checkpoint": False,
        "network": False,
        "provider": False,
        "raw": False,
        "runtime_change": False,
        "stage_commit_push": False,
        "training": False,
    }
    expected_materialization = {
        "build_before_mutation": True,
        "exact_output_inventory": True,
        "gpfs_einval_fails_closed": True,
        "inode_preserving_exact_set_noop": True,
        "leaf_and_directory_fsync": True,
        "leaf_open_dir_fd": True,
        "o_excl_staging_leaves": True,
        "os_replace_fallback": False,
        "rename_noreplace_required": True,
        "root_fd_no_follow": True,
    }
    expected_groups = {
        "cross_phase_precedence": 12,
        "download_result_status_validation": 7,
        "exact4_presence": 6,
        "expected_content_length_optional": 8,
        "expected_sha256_optional": 9,
        "explicit_integrity_verdict_optional": 9,
        "inherited_exact7_business_projection": 23,
        "observed_content_length_boundary": 2,
        "observed_content_length_validation": 5,
        "observed_http_status_boundary": 6,
        "observed_http_status_validation": 6,
        "observed_sha256_validation": 9,
        "result_invariant_negative": 26,
    }
    expected_source_boundary = [
        {
            "base_tree_mode": source_modes[relative],
            "path": relative,
            "sha256": digest,
        }
        for relative, digest in SOURCE_SHA256.items()
    ]
    if not (
        manifest["manifest_schema_version"] == "covapie_admit_013_rule_logic_interface_manifest_v1"
        and manifest["project"] == "CovaPIE"
        and manifest["stage"] == STAGE
        and manifest["base_commit"] == BASE_COMMIT
        and manifest["base_parent"] == BASE_PARENT
        and manifest["base_tree"] == BASE_TREE
        and manifest["base_subject"] == BASE_SUBJECT
        and manifest["admission_rule_id"] == "ADMIT_013"
        and manifest["public_evaluator"] == "evaluate_admit_013"
        and manifest["public_signature"] == (
            "evaluate_admit_013(*, download_result_status: object = _MISSING, "
            "observed_http_status: object = _MISSING, observed_content_length_bytes: "
            "object = _MISSING, observed_sha256: object = _MISSING, "
            "expected_content_length_bytes: object = _MISSING, expected_sha256: "
            "object = _MISSING, explicit_integrity_verdict: object = _MISSING) -> "
            "Admit013EvaluationResult"
        )
        and manifest["result_type"] == "Admit013EvaluationResult"
        and manifest["formal_production_sha256"] == EXPECTED_PRODUCTION_SHA256
        and manifest["formal_marker_prefix_sha256"] == EXPECTED_PREFIX_SHA256
        and manifest["formal_ast_sha256"] == EXPECTED_AST_SHA256
        and tuple(manifest["formal_ast_sha256"]) == tuple(sorted(EXPECTED_AST_SHA256))
        and manifest["formal_closure"] == list(FORMAL_CLOSURE)
        and manifest["formal_closure_count"] == 10
        and manifest["canonical_evidence_python_implementation"] == "cpython"
        and manifest["canonical_evidence_python_version"] == "3.10.4"
        and manifest["ast_attestation_cross_python_version_portable"] is False
        and manifest["noncanonical_python_policy"] == NONCANONICAL_PYTHON_POLICY
        and manifest["python_runtime_migration_policy"] == PYTHON_RUNTIME_MIGRATION_POLICY
        and manifest["download_fields"] == list(DOWNLOAD_FIELDS)
        and manifest["authority_fields"] == list(AUTHORITY_FIELDS)
        and manifest["parameter_order"] == list(PARAMETERS)
        and manifest["outcome_vocabulary"] == list(OUTCOME_VOCABULARY)
        and manifest["reason_vocabulary"] == list(REASON_VOCABULARY)
        and manifest["reason_vocabulary_count_including_empty"] == 26
        and manifest["validation_phase_order"] == list(VALIDATION_PHASES)
        and manifest["business_failure_precedence"] == list(BUSINESS_REASONS)
        and manifest["result_fields"] == list(RESULT_FIELDS)
        and manifest["result_field_count"] == 12
        and manifest["source_count"] == 12
        and manifest["source_path_list_sha256"] == SOURCE_PATH_LIST_SHA256
        and manifest["source_path_sha256_pairs_sha256"] == SOURCE_PATH_SHA256_PAIRS_SHA256
        and manifest["source_boundary"] == expected_source_boundary
        and manifest["output_files"] == list(OUTPUT_FILES)
        and manifest["output_file_count"] == 6
        and manifest["output_sha256"] == expected_output_sha
        and all(
            _sha(payloads[name]) == manifest["output_sha256"][name]
            for name in OUTPUT_FILES[:-1]
        )
        and manifest["row_counts"] == expected_row_counts
        and manifest["truth_matrix_group_counts"] == expected_groups
        and manifest["actual_evaluator_design_oracle_projection_passed"] == 102
        and manifest["inherited_business_projection_passed"] == 23
        and manifest["result_negative_projection_rejected"] == 26
        and manifest["truth_matrix_passed"] == 128
        and manifest["purity_closure_complete"] is True
        and manifest["issue_transition_count"] == 0
        and manifest["issue_inventory_byte_identical_to_formal_interface"] is True
        and manifest["coverage_affected_rules"] == "ADMIT_013|ADMIT_014|ADMIT_015"
        and manifest["remaining_open_issue_ids"] == list(required_open)
        and manifest["readiness"] == expected_readiness
        and all(manifest[name] is value for name, value in expected_readiness.items())
        and manifest["safety"] == expected_safety
        and manifest["materialization_policy"] == expected_materialization
        and manifest["adapter_registry_runtime_changed"] is False
        and manifest["authorized_admit_013_download_execution_count"] == 0
        and manifest["recommended_next_step"] == "design_covapie_admit_013_unified_adapter_contract_v1"
        and manifest["step12d_status"] == "smoke_legality_only_not_final_training_feature_contract"
        and manifest["feature_semantics_audit_requirement"] == (
            "required_before_training; historical UNKNOWN_ATOM_FEATURE_POLICY and "
            "feature_semantics_known=False require audit"
        )
        and manifest["all_checks_passed"] is True
    ):
        raise ValueError("manifest contract drift")
    return manifest


def _check_outputs(
    sources: dict[str, bytes],
    source_modes: dict[str, str],
    ast_digests: dict[str, str],
) -> dict:
    _assert_canonical_evidence_runtime()
    payloads = _read_pinned_output_payloads(REPO_ROOT / OUTPUT_ROOT)
    for name in OUTPUT_FILES:
        if _sha(payloads[name]) != EXPECTED_OUTPUT_SHA256[name]:
            raise ValueError(f"frozen output SHA drift: {name}")
    return _validate_output_semantics(payloads, sources, source_modes, ast_digests)


def _check_lifecycle() -> str:
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if ancestor.returncode:
        raise ValueError("base commit is not an ancestor of HEAD")
    observed_top_level = set()
    for directory in STAGE_TOP_LEVEL_DIRECTORIES:
        absolute_directory = REPO_ROOT / directory
        directory_item = os.lstat(absolute_directory)
        if (
            stat.S_ISLNK(directory_item.st_mode)
            or not stat.S_ISDIR(directory_item.st_mode)
            or absolute_directory.resolve(strict=True) != absolute_directory
        ):
            raise ValueError(f"unsafe stage top-level directory: {directory}")
        observed_top_level.update(
            path.relative_to(REPO_ROOT)
            for path in absolute_directory.glob(STAGE_TOP_LEVEL_GLOB)
        )
    output_root = REPO_ROOT / OUTPUT_ROOT
    output_item = os.lstat(output_root)
    if (
        stat.S_ISLNK(output_item.st_mode)
        or not stat.S_ISDIR(output_item.st_mode)
        or output_root.resolve(strict=True) != output_root
    ):
        raise ValueError("unsafe lifecycle output root")
    output_fd = os.open(
        output_root,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        if _identity(os.fstat(output_fd)) != _identity(output_item):
            raise ValueError("lifecycle output root stat/open race")
        output_names = set(os.listdir(output_fd))
    finally:
        os.close(output_fd)
    observed_stage_paths = observed_top_level | {
        OUTPUT_ROOT / name for name in output_names
    }
    if observed_stage_paths != set(STAGE_PATHS):
        raise ValueError("Exact10 same-stage lifecycle inventory drift")

    tracked = []
    untracked = []
    for path in STAGE_PATHS:
        relative = path.as_posix()
        result = _git(["ls-files", "--error-unmatch", "--", relative])
        if result.returncode not in {0, 1}:
            raise ValueError(f"stage tracking state unavailable: {relative}")
        if result.returncode == 0 and result.stdout.splitlines() != [relative]:
            raise ValueError(f"stage tracking identity drift: {relative}")
        (tracked if result.returncode == 0 else untracked).append(relative)
        absolute = REPO_ROOT / path
        item = os.lstat(absolute)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
            raise ValueError(f"stage path not regular: {relative}")
        if item.st_size > 100 * 1024 * 1024:
            raise ValueError(f"oversized stage path: {relative}")
        if path.suffix in FORBIDDEN_SUFFIXES:
            raise ValueError(f"forbidden stage suffix: {relative}")
        ignored = _git(["check-ignore", "-q", "--", relative])
        if ignored.returncode not in {0, 1}:
            raise ValueError(f"stage ignore state unavailable: {relative}")
        if result.returncode and ignored.returncode == 0:
            raise ValueError(f"ignored stage path: {relative}")
    cached = _git(["diff", "--cached", "--name-only", "--", *(path.as_posix() for path in STAGE_PATHS)])
    working = _git(["diff", "--name-only", "--", *(path.as_posix() for path in STAGE_PATHS)])
    if cached.returncode or working.returncode:
        raise ValueError("stage-scoped diff unavailable")
    if cached.stdout:
        raise ValueError("stage path staged")
    if len(untracked) == len(STAGE_PATHS):
        status = _git(["status", "--porcelain", "--untracked-files=all", "--", *(path.as_posix() for path in STAGE_PATHS)])
        observed = {line[3:] for line in status.stdout.splitlines() if line.startswith("?? ")}
        if status.returncode or working.stdout or observed != set(untracked):
            raise ValueError("pre_commit lifecycle drift")
        return "pre_commit"
    if len(tracked) == len(STAGE_PATHS):
        if working.stdout:
            raise ValueError("post_commit stage paths dirty")
        return "post_commit"
    raise ValueError("mixed stage lifecycle")


def check() -> dict:
    _assert_canonical_evidence_runtime()
    sources, source_modes = _check_base_and_sources()
    _, ast_digests = _check_formal_source()
    manifest = _check_outputs(sources, source_modes, ast_digests)
    lifecycle = _check_lifecycle()
    return {
        "checker": "ADMIT_013 standalone evaluator interface v1",
        "base_commit": BASE_COMMIT,
        "lifecycle": lifecycle,
        "source_count": 12,
        "truth_rows": 128,
        "business_rows": 23,
        "negative_result_rows": 26,
        "formal_closure_count": len(FORMAL_CLOSURE),
        "formal_production_sha256": EXPECTED_PRODUCTION_SHA256,
        "formal_marker_prefix_sha256": EXPECTED_PREFIX_SHA256,
        "manifest_sha256": EXPECTED_OUTPUT_SHA256[OUTPUT_FILES[-1]],
        "canonical_evidence_python_implementation": CANONICAL_PYTHON_IMPLEMENTATION,
        "canonical_evidence_python_version": ".".join(
            str(part) for part in CANONICAL_PYTHON_VERSION
        ),
        "recommended_next_step": manifest["recommended_next_step"],
        "all_checks_passed": True,
    }


def main() -> None:
    print(json.dumps(check(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
