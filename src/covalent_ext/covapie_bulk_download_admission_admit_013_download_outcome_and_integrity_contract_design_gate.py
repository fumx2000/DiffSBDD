"""ADMIT_013 download-outcome and integrity-authority contract design gate.

This metadata-only module validates an exact committed predecessor boundary and
materializes six deterministic design artifacts.  It intentionally defines no
ADMIT_013 evaluator, evaluation-result type, adapter, registry entry, runtime,
provider mapping, download operation, aggregation, or training operation.
"""
from __future__ import annotations

import csv
import ctypes
import hashlib
import io
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "30c644de3973ba2968ecaa8ebff97159c07678b9"
BASE_PARENT = "5ff12d358a633c44c333022f7e0ebe30f039d6fc"
BASE_SUBJECT = "add CovaPIE ADMIT_013 formal evaluator preconditions audit v1"
STAGE = "covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1"
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

EXACT4_FIELDS = (
    "download_result_status",
    "observed_http_status",
    "observed_content_length_bytes",
    "observed_sha256",
)
AUTHORITY_FIELDS = (
    "expected_content_length_bytes",
    "expected_sha256",
    "explicit_integrity_verdict",
)
REASON_VOCABULARY = (
    "",
    "DOWNLOAD_RESULT_STATUS_FAILURE",
    "OBSERVED_HTTP_STATUS_NOT_SUCCESS",
    "OBSERVED_CONTENT_EMPTY",
    "OBSERVED_SHA256_MISMATCH",
    "EXPLICIT_INTEGRITY_VERDICT_FAILED",
    "OBSERVED_CONTENT_LENGTH_MISMATCH",
    "INTEGRITY_AUTHORITY_MISSING",
)
BUSINESS_FAILURE_REASONS = REASON_VOCABULARY[1:]
FORBIDDEN_PSEUDO_AUTHORITIES = (
    "candidate_self_report",
    "test_fixture",
    "artifact_sha256",
    "checker_sha256",
    "git_sha256",
    "source_boundary_sha256",
    "post_download_self_generated_observed_sha256",
    "historical_pilot_download_value",
)

OUTCOME_FILE = "covapie_admit_013_download_outcome_policy_contract.csv"
AUTHORITY_FILE = "covapie_admit_013_integrity_authority_contract.csv"
FAILURE_FILE = "covapie_admit_013_failure_taxonomy_and_precedence.csv"
TRUTH_FILE = "covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv"
ISSUE_FILE = "covapie_admit_013_issue_readiness_inventory.csv"
MANIFEST_FILE = "covapie_admit_013_download_outcome_and_integrity_contract_manifest.json"
OUTPUT_FILES = (
    OUTCOME_FILE,
    AUTHORITY_FILE,
    FAILURE_FILE,
    TRUTH_FILE,
    ISSUE_FILE,
    MANIFEST_FILE,
)

OUTCOME_COLUMNS = (
    "policy_order", "policy_id", "policy_area", "subject", "source_envelope",
    "contract", "disposition", "precedence_or_continuation",
    "forbidden_behavior", "contract_passed",
)
AUTHORITY_COLUMNS = (
    "authority_order", "authority_name", "source_envelope", "presence_required",
    "missing_behavior", "exact_builtin_type", "subclasses_allowed",
    "allowed_values_or_grammar", "minimum_value", "normalization_allowed",
    "trusted_producers", "sufficient_when", "comparison_semantics",
    "forbidden_pseudo_authorities", "evaluator_io_allowed", "contract_passed",
)
FAILURE_COLUMNS = (
    "precedence_rank", "outcome", "reason", "layer", "unique_trigger_condition",
    "requires_structural_validation", "blocks_candidate", "reason_empty",
    "catch_all_allowed", "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "download_result_status",
    "observed_http_status", "observed_content_length_bytes", "observed_sha256",
    "expected_content_length_bytes", "expected_sha256",
    "explicit_integrity_verdict", "active_failure_reasons", "expected_outcome",
    "expected_reason", "expected_precedence_rank", "strong_authority_present",
    "case_passed",
)
INHERITED_ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity",
    "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count",
)
ISSUE_COLUMNS = (
    "inherited_order", *INHERITED_ISSUE_COLUMNS, "effective_status",
    "transition_stage", "transition_action", "transition_evidence",
)

SOURCE_SHA256 = {
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv": "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv": "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv": "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv": "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv": "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract.csv": "03aef0a14257d9a2c028fcc3dd84c161c29b09bca1a1c71456edc66e2e73c9ce",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_result_status_enum.csv": "4c016e8c325ce6a422dff618ae166ec4f42243cc0d1fbf8f6a722c13f63139f6",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract_manifest.json": "9fadff44ae15474783df2a3997c45f2c4d57a41ca2adbab0b40f1d890f51039f",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_and_result_contract.csv": "682192b492979d9b6114381cbfc02d57c349e3cd8db2541a01177235d34c04e6",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv": "44709c3a679368476c87bcd97dafa2f9cf9bddb4af534c6eb950c565d0919aec",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_contract_manifest.json": "2845c2623a01087af8842177f4502402d0a8875a77ce12c6a49e2f77c60dae01",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_contract.csv": "c5c383e9a9e17c5eb5a4b2c92455da89a78e66f75df7ff31ce0494f08281433e",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_manifest.json": "ad131895c0acfdaf5b350105031647bdcac9667370fb6cd43baf8826bea995c8",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract.csv": "12228051428134223dc4db4ec418ced573637047189056f1fb8df908ca2fe6c8",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract_manifest.json": "1df0e2a09817b7763ec4eb767663db169d3239385094da151af28150c2c55d25",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py": "4d9a49806d4ef71a95c8ad032dfa061f7473b1cb55a573459c155f0cd5d57282",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_registry_and_identity_audit.csv": "57ed1f04df27c7b30ec4cea97aead99e7788a2968f77245280850ae26f399e59",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_issue_readiness_inventory.csv": "6b6a543dd9fcce9a4b4451a05eae296a482093bba0bdb33bb37247bca4d17cfb",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_manifest.json": "bc909aefd86b62139fbb62025d9c323988a4c232ab9c960efb291fb0c196cee3",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_formal_evaluator_precondition_matrix.csv": "4b411c86cce23351d4aec3d58a894d161ab163e0305fdd91853bc54f16aa1fdf",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_issue_readiness_inventory.csv": "204923bbf26c286c14ce4feaeb7934b279cafa54287ba96b4e2455fd84cf1198",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_formal_evaluator_preconditions_manifest.json": "63f0f96a960135117b0c4c8d3f80d1991cb8138e7df69d3917e921a6a4c74ce0",
}
SOURCE_PATHS = tuple(Path(value) for value in SOURCE_SHA256)
SOURCE_PATH_LIST_SHA256 = hashlib.sha256(
    json.dumps([value.as_posix() for value in SOURCE_PATHS], separators=(",", ":")).encode()
).hexdigest()
SOURCE_PATH_SHA256_PAIRS_SHA256 = hashlib.sha256(
    json.dumps([[path.as_posix(), SOURCE_SHA256[path.as_posix()]] for path in SOURCE_PATHS], separators=(",", ":")).encode()
).hexdigest()


def _git(arguments: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=text, check=False
    )


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode


def _assert_parent_chain(path: Path) -> None:
    current = (REPO_ROOT / path).parent
    while current != REPO_ROOT:
        item = os.lstat(current)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
            raise ValueError("unsafe source parent")
        current = current.parent


def _pinned_read(path: Path, expected_identity: tuple[int, int, int]) -> bytes:
    absolute = REPO_ROOT / path
    if _identity(os.lstat(absolute)) != expected_identity:
        raise ValueError("source identity drift before open")
    descriptor = os.open(
        absolute,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("source stat/open race")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("source FD identity drift")
        if _identity(os.lstat(absolute)) != expected_identity:
            raise ValueError("source lexical identity drift")
        _assert_parent_chain(path)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _assert_base_lineage() -> None:
    identity = _git(["show", "-s", "--format=%H%n%P%n%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if identity.returncode or ancestor.returncode:
        raise ValueError("base lineage unavailable")
    if identity.stdout.splitlines() != [BASE_COMMIT, BASE_PARENT, BASE_SUBJECT]:
        raise ValueError("base identity drift")


def build_frozen_source_snapshot() -> tuple[tuple[Path, bytes, str, str], ...]:
    root = os.lstat(REPO_ROOT)
    if stat.S_ISLNK(root.st_mode) or not stat.S_ISDIR(root.st_mode):
        raise ValueError("unsafe repository root")
    _assert_base_lineage()
    structures: list[tuple[Path, str, tuple[int, int, int]]] = []
    for path in SOURCE_PATHS:
        if path.is_absolute() or ".." in path.parts or path.parts[:2] == ("data", "raw"):
            raise ValueError("unsafe source path")
        _assert_parent_chain(path)
        absolute = REPO_ROOT / path
        item = os.lstat(absolute)
        tree = _git(["ls-tree", BASE_COMMIT, "--", path.as_posix()])
        tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()])
        head_part, separator, tree_path = tree.stdout.partition("\t")
        fields = head_part.split()
        if (
            tree.returncode or tracked.returncode or not separator
            or tree_path.strip() != path.as_posix()
            or tracked.stdout.splitlines() != [path.as_posix()]
            or len(fields) != 3 or fields[0] not in {"100644", "100755"}
            or fields[1] != "blob" or stat.S_ISLNK(item.st_mode)
            or not stat.S_ISREG(item.st_mode) or absolute.resolve(strict=True) != absolute
        ):
            raise ValueError(f"unsafe committed source: {path}")
        structures.append((path, fields[0], _identity(item)))
    snapshot: list[tuple[Path, bytes, str, str]] = []
    for path, mode, expected_identity in structures:
        base = _git(["show", f"{BASE_COMMIT}:{path.as_posix()}"], text=False)
        current = _pinned_read(path, expected_identity)
        digest = hashlib.sha256(current).hexdigest()
        if (
            base.returncode or not isinstance(base.stdout, bytes)
            or hashlib.sha256(base.stdout).hexdigest() != digest
            or digest != SOURCE_SHA256[path.as_posix()]
        ):
            raise ValueError(f"source SHA drift: {path}")
        snapshot.append((path, current, digest, mode))
    return tuple(snapshot)


def _content(snapshot: tuple[tuple[Path, bytes, str, str], ...], path: str) -> bytes:
    wanted = Path(path)
    return next(record[1] for record in snapshot if record[0] == wanted)


def _rows(snapshot: tuple[tuple[Path, bytes, str, str], ...], path: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(_content(snapshot, path).decode(), newline="")))


def _validate_predecessors(snapshot: tuple[tuple[Path, bytes, str, str], ...]) -> None:
    design = "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/"
    pre = "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/"
    field_root = "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/"
    formal_root = "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/"
    runtime_root = "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/"
    audit_root = "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/"
    registry = _rows(snapshot, design + "covapie_bulk_download_admission_rule_registry.csv")
    rule = next(row for row in registry if row["admission_rule_id"] == "ADMIT_013")
    if rule != {
        "admission_rule_id": "ADMIT_013", "admission_rule_name": "download_failure_fail_closed",
        "evidence_source": "future_download_result",
        "required_status": "non_success_or_integrity_failure_not_admitted",
        "failure_severity": "blocking", "blocking_reason": "download_failure_must_fail_closed",
        "evaluation_phase": "post_download", "network_required": "false",
        "raw_structure_required": "false", "ready_for_future_implementation": "true",
    }:
        raise ValueError("ADMIT_013 identity drift")
    schema = _rows(snapshot, design + "covapie_bulk_download_admission_schema_contract.csv")
    if [row["admission_field_name"] for row in schema if row["admission_field_name"] in EXACT4_FIELDS] != list(EXACT4_FIELDS):
        raise ValueError("Step14AT Exact4 schema drift")
    executable = next(
        row for row in _rows(snapshot, pre + "covapie_bulk_download_admission_rule_executability_matrix.csv")
        if row["admission_rule_id"] == "ADMIT_013"
    )
    if (
        executable["candidate_field_dependencies"].split("|") != list(EXACT4_FIELDS)
        or executable["batch_context_dependencies"] != ""
        or executable["download_execution_result_required"] != "true"
        or executable["pure_in_memory_interface_possible"] != "true"
    ):
        raise ValueError("Step14AU-A executability drift")
    semantics = [
        row for row in _rows(snapshot, pre + "covapie_bulk_download_admission_field_semantics_matrix.csv")
        if row["field_name"] in EXACT4_FIELDS
    ]
    if [row["field_name"] for row in semantics] != list(EXACT4_FIELDS) or not all(
        row["candidate_record_field"] == "false"
        and row["producer_scope"] == "download_execution_result"
        and row["dependent_rules"] == "ADMIT_012|ADMIT_013" for row in semantics
    ):
        raise ValueError("Step14AU-A field routing drift")
    contexts = _rows(snapshot, pre + "covapie_bulk_download_admission_evaluation_context_contract.csv")
    old_contexts = (
        "allowed_download_result_statuses", "successful_http_status_contract",
        "content_length_contract", "sha256_format_contract",
    )
    selected = [row for row in contexts if row["context_item"] in old_contexts]
    if [row["context_item"] for row in selected] != list(old_contexts) or not all(
        row["filesystem_access_inside_evaluator"] == "false"
        and row["network_access_inside_evaluator"] == "false" for row in selected
    ):
        raise ValueError("Step14AU-A evaluation context drift")
    exact4 = _rows(snapshot, field_root + "covapie_admit_012_download_integrity_field_contract.csv")
    if [row["field_name"] for row in exact4] != list(EXACT4_FIELDS):
        raise ValueError("shared Exact4 order drift")
    if [row["exact_builtin_type"] for row in exact4] != ["str", "int", "int", "str"]:
        raise ValueError("shared Exact4 type drift")
    if not all(row["subclasses_allowed"] == row["normalization_allowed"] == "false" for row in exact4):
        raise ValueError("shared Exact4 exactness drift")
    if exact4[0]["ordered_allowed_values"] != "success|failure" or exact4[1]["future_success_minimum"] != "200" or exact4[1]["future_success_maximum"] != "299":
        raise ValueError("shared status/HTTP bounds drift")
    if ">= 0" not in exact4[2]["value_contract"] or exact4[3]["value_contract"] != "exactly 64 ASCII lowercase hexadecimal characters [0-9a-f]{64}":
        raise ValueError("shared content/SHA contract drift")
    statuses = [row for row in _rows(snapshot, field_root + "covapie_admit_012_download_result_status_enum.csv") if row["row_kind"] == "canonical_enum"]
    if [row["status_value"] for row in statuses] != ["success", "failure"]:
        raise ValueError("download status enum drift")
    formal_routes = _rows(snapshot, formal_root + "covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv")
    route_rows = [row for row in formal_routes if row["contract_kind"] == "route"]
    if [row["source_envelope"] for row in route_rows[:4]] != ["download_result_context"] * 4:
        raise ValueError("ADMIT_012 download routing drift")
    if any("ADMIT_013" in "|".join(row.values()) for row in route_rows):
        raise ValueError("direct cross-rule routing unexpectedly exists")
    standalone_manifest = json.loads(_content(snapshot, "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_manifest.json"))
    adapter_manifest = json.loads(_content(snapshot, "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract_manifest.json"))
    if standalone_manifest["evaluate_admit_012_implemented"] is not True or adapter_manifest["admit_012_unified_adapter_contract_frozen"] is not True:
        raise ValueError("ADMIT_012 implementation-chain drift")
    runtime_registry = _rows(snapshot, runtime_root + "covapie_admit_001_to_012_registry_and_identity_audit.csv")
    if next(row for row in runtime_registry if row["audit_item"] == "not_registered:ADMIT_013")["observed_value"] != "False":
        raise ValueError("ADMIT_013 runtime registration drift")
    runtime_manifest = json.loads(_content(snapshot, runtime_root + "covapie_admit_001_to_012_runtime_manifest.json"))
    if runtime_manifest["registered_rule_count"] != 12 or runtime_manifest["known_not_registered_rule_ids"] != ["ADMIT_013", "ADMIT_014", "ADMIT_015"]:
        raise ValueError("Exact12 runtime drift")
    if runtime_manifest["combined_candidate_verdict_implemented"] is not False or runtime_manifest["cross_rule_aggregation_implemented"] is not False:
        raise ValueError("aggregation boundary drift")
    preconditions = _rows(snapshot, audit_root + "covapie_admit_013_formal_evaluator_precondition_matrix.csv")
    if len(preconditions) != 32 or [row["precondition_id"] for row in preconditions] != [f"PRE_{index:03d}" for index in range(1, 33)]:
        raise ValueError("Exact32 precondition identity drift")
    issues = _rows(snapshot, audit_root + "covapie_admit_013_issue_readiness_inventory.csv")
    if len(issues) != 23:
        raise ValueError("Exact23 issue inventory drift")
    if next(row for row in issues if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")["affected_rules"] != "ADMIT_013|ADMIT_014|ADMIT_015":
        raise ValueError("unified coverage drift")


def _outcome_rows() -> list[dict[str, str]]:
    specs = (
        ("DEPENDENCY_PIPELINE", "dependency", "pipeline-level prerequisite", "combined_pipeline", "ADMIT_012 may run first logically", "logical_prerequisite_only", "before ADMIT_013 when combined", "direct result consumption"),
        ("DEPENDENCY_SELF_VALIDATION", "dependency", "standalone self-validation", "standalone_future_evaluator", "repeat shared Exact4 presence/type/value validation", "required", "before business precedence", "trusting prior validation without revalidation"),
        ("DEPENDENCY_NO_RESULT_OBJECT", "dependency", "direct cross-rule result consumption", "none", "Admit012EvaluationResult is not an ADMIT_013 input", "forbidden", "not applicable", "Python result-object dependency"),
        ("ROUTE_EXACT4", "routing", "Exact4 observations", "download_result_context", "source exactly the shared Exact4 in canonical order", "required", "structural validation first", "candidate/batch/stage/fallback sourcing"),
        ("ROUTE_AUTHORITY", "routing", "integrity comparison authority", "evaluation_context", "source exactly the three authority fields", "optional individually", "authority validation before business precedence", "candidate/batch/stage/fallback sourcing"),
        ("ROUTE_FORBIDDEN_ENVELOPES", "routing", "candidate_record|batch_context|stage_authorization_context", "forbidden", "must provide neither observations nor authority", "forbidden", "fail closed at future routing layer", "fallback envelope"),
        ("NO_IO_OR_NORMALIZATION", "boundary", "future standalone evaluator", "pure_memory", "no normalization inference file network provider read or recomputation", "required", "all phases", "I/O or现场重算"),
        ("HTTP_SUCCESS_RANGE", "outcome", "observed_http_status", "download_result_context", "inclusive success range 200..299", "continue_only", "after successful status", "treating structural 100..599 as success"),
        ("STATUS_FAILURE", "outcome", "download_result_status=failure", "download_result_context", "always blocked", "blocked", "business rank 1", "override by 2xx length SHA or verdict"),
        ("STATUS_SUCCESS_NON2XX", "outcome", "success plus HTTP outside 200..299", "download_result_context", "blocked", "blocked", "business rank 2", "treating status success as sufficient"),
        ("STATUS_SUCCESS_2XX", "outcome", "success plus HTTP 200..299", "download_result_context", "continue to content and integrity checks", "continue_only", "not a pass", "automatic pass"),
        ("ZERO_CONTENT", "outcome", "observed_content_length_bytes=0", "download_result_context", "always blocked even when expected length is zero and authorities appear to pass", "blocked", "business rank 3", "zero-byte materialization"),
        ("ALL_AUTHORITIES_MUST_AGREE", "integrity", "provided trusted authorities", "evaluation_context", "every provided authority must avoid failure or mismatch", "required", "business ranks 4..6", "ignoring a provided mismatch"),
        ("STRONG_AUTHORITY", "integrity", "expected SHA match or explicit verified", "evaluation_context", "at least one strong authority is required", "required", "business rank 7 if absent", "length-only or grammar-only authority"),
        ("LENGTH_COMPARISON", "integrity", "expected_content_length_bytes", "evaluation_context", "when present require exact integer equality", "required_if_present", "rank 6 mismatch", "length match as sufficient pass"),
        ("PASS_CONJUNCTION", "outcome", "complete business outcome", "pure_memory", "success AND HTTP 2xx AND nonzero AND no provided mismatch/failure AND strong authority", "passed", "rank 8", "any simpler condition treated as pass"),
    )
    return [{
        "policy_order": str(index), "policy_id": item[0], "policy_area": item[1],
        "subject": item[2], "source_envelope": item[3], "contract": item[4],
        "disposition": item[5], "precedence_or_continuation": item[6],
        "forbidden_behavior": item[7], "contract_passed": "true",
    } for index, item in enumerate(specs, 1)]


def _authority_rows() -> list[dict[str, str]]:
    forbidden = "|".join(FORBIDDEN_PSEUDO_AUTHORITIES)
    specs = (
        (
            "expected_content_length_bytes", "false",
            "absence allowed; cannot satisfy strong-authority requirement", "int", "", "0",
            "trusted provider or HTTP metadata path",
            "never sufficient alone; corroborating comparison only",
            "if present must exactly equal observed_content_length_bytes",
        ),
        (
            "expected_sha256", "false",
            "absence allowed if explicit_integrity_verdict is verified", "str",
            "ASCII lowercase [0-9a-f]{64}", "",
            "trusted provider manifest|trusted pre-download catalog|separately approved equivalent authority",
            "sufficient strong authority only when exactly equal to observed_sha256",
            "if present mismatch blocks; exact equality contributes strong authority",
        ),
        (
            "explicit_integrity_verdict", "false",
            "absence allowed if expected_sha256 is present and matches", "str",
            "verified|failed", "", "future designated integrity verifier",
            "verified is sufficient strong authority; failed always blocks",
            "failed blocks; verified contributes strong authority but cannot override any mismatch",
        ),
    )
    return [{
        "authority_order": str(index), "authority_name": item[0],
        "source_envelope": "evaluation_context", "presence_required": item[1],
        "missing_behavior": item[2], "exact_builtin_type": item[3],
        "subclasses_allowed": "false", "allowed_values_or_grammar": item[4],
        "minimum_value": item[5], "normalization_allowed": "false",
        "trusted_producers": item[6], "sufficient_when": item[7],
        "comparison_semantics": item[8], "forbidden_pseudo_authorities": forbidden,
        "evaluator_io_allowed": "false", "contract_passed": "true",
    } for index, item in enumerate(specs, 1)]


def _failure_rows() -> list[dict[str, str]]:
    triggers = (
        "download_result_status is exact canonical failure",
        "status is success and observed_http_status is outside inclusive 200..299",
        "status is success and HTTP is 2xx and observed_content_length_bytes equals 0",
        "earlier reasons absent and expected_sha256 is present but differs from observed_sha256",
        "earlier reasons absent and explicit_integrity_verdict equals failed",
        "earlier reasons absent and expected_content_length_bytes is present but differs from observed_content_length_bytes",
        "earlier reasons absent and neither exact expected SHA match nor explicit verified is present",
    )
    rows = []
    for rank, (reason, trigger) in enumerate(zip(BUSINESS_FAILURE_REASONS, triggers, strict=True), 1):
        rows.append({
            "precedence_rank": str(rank), "outcome": "blocked", "reason": reason,
            "layer": "business_outcome", "unique_trigger_condition": trigger,
            "requires_structural_validation": "true", "blocks_candidate": "true",
            "reason_empty": "false", "catch_all_allowed": "false",
            "contract_passed": "true",
        })
    rows.append({
        "precedence_rank": "8", "outcome": "passed", "reason": "",
        "layer": "terminal_pass", "unique_trigger_condition": "no rank 1..7 failure after structural validation",
        "requires_structural_validation": "true", "blocks_candidate": "false",
        "reason_empty": "true", "catch_all_allowed": "false", "contract_passed": "true",
    })
    return rows


SHA_A = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
SHA_B = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
MISSING = "<MISSING>"


def _truth_rows() -> list[dict[str, str]]:
    # Each case is declarative contract evidence; this design gate runs no evaluator.
    specs = (
        ("PASS_SHA_MATCH", "pass", "success", "200", "10", SHA_A, "10", SHA_A, MISSING, (), "passed", "", 8, True),
        ("PASS_EXPLICIT_VERIFIED", "pass", "success", "299", "10", SHA_A, MISSING, MISSING, "verified", (), "passed", "", 8, True),
        ("PASS_ALL_AUTHORITIES", "pass", "success", "204", "10", SHA_A, "10", SHA_A, "verified", (), "passed", "", 8, True),
        ("FAILURE_WITH_2XX", "status", "failure", "200", "10", SHA_A, "10", SHA_A, "verified", (1,), "blocked", BUSINESS_FAILURE_REASONS[0], 1, True),
        ("FAILURE_WITH_404", "status", "failure", "404", "10", SHA_A, "10", SHA_B, "failed", (1, 2, 4, 5, 7), "blocked", BUSINESS_FAILURE_REASONS[0], 1, False),
        ("SUCCESS_WITH_404", "http", "success", "404", "10", SHA_A, "10", SHA_A, "verified", (2,), "blocked", BUSINESS_FAILURE_REASONS[1], 2, True),
        ("ZERO_CONTENT", "content", "success", "200", "0", SHA_A, MISSING, SHA_A, MISSING, (3,), "blocked", BUSINESS_FAILURE_REASONS[2], 3, True),
        ("SHA_MISMATCH", "integrity", "success", "200", "10", SHA_A, MISSING, SHA_B, MISSING, (4, 7), "blocked", BUSINESS_FAILURE_REASONS[3], 4, False),
        ("EXPLICIT_FAILED", "integrity", "success", "200", "10", SHA_A, MISSING, MISSING, "failed", (5, 7), "blocked", BUSINESS_FAILURE_REASONS[4], 5, False),
        ("LENGTH_MISMATCH_WITH_SHA_MATCH", "integrity", "success", "200", "10", SHA_A, "11", SHA_A, MISSING, (6,), "blocked", BUSINESS_FAILURE_REASONS[5], 6, True),
        ("ONLY_LENGTH_MATCH", "authority", "success", "200", "10", SHA_A, "10", MISSING, MISSING, (7,), "blocked", BUSINESS_FAILURE_REASONS[6], 7, False),
        ("NO_STRONG_AUTHORITY", "authority", "success", "200", "10", SHA_A, MISSING, MISSING, MISSING, (7,), "blocked", BUSINESS_FAILURE_REASONS[6], 7, False),
        ("SHA_MATCH_AND_EXPLICIT_FAILED", "precedence", "success", "200", "10", SHA_A, MISSING, SHA_A, "failed", (5,), "blocked", BUSINESS_FAILURE_REASONS[4], 5, True),
        ("SHA_MISMATCH_AND_EXPLICIT_VERIFIED", "precedence", "success", "200", "10", SHA_A, MISSING, SHA_B, "verified", (4,), "blocked", BUSINESS_FAILURE_REASONS[3], 4, True),
        ("ZERO_ALL_AUTHORITIES_APPEAR_PASS", "precedence", "success", "200", "0", SHA_A, "0", SHA_A, "verified", (3,), "blocked", BUSINESS_FAILURE_REASONS[2], 3, True),
        ("STATUS_FAILURE_AND_SHA_MISMATCH", "precedence", "failure", "200", "10", SHA_A, MISSING, SHA_B, MISSING, (1, 4, 7), "blocked", BUSINESS_FAILURE_REASONS[0], 1, False),
        ("NON2XX_ZERO_INTEGRITY_FAILURE", "triple_failure", "success", "500", "0", SHA_A, "1", SHA_B, "failed", (2, 3, 4, 5, 6, 7), "blocked", BUSINESS_FAILURE_REASONS[1], 2, False),
        ("ADJACENT_STATUS_HTTP", "adjacent_precedence", "failure", "404", "10", SHA_A, MISSING, SHA_A, MISSING, (1, 2), "blocked", BUSINESS_FAILURE_REASONS[0], 1, True),
        ("ADJACENT_HTTP_EMPTY", "adjacent_precedence", "success", "404", "0", SHA_A, MISSING, SHA_A, MISSING, (2, 3), "blocked", BUSINESS_FAILURE_REASONS[1], 2, True),
        ("ADJACENT_EMPTY_SHA", "adjacent_precedence", "success", "200", "0", SHA_A, MISSING, SHA_B, MISSING, (3, 4, 7), "blocked", BUSINESS_FAILURE_REASONS[2], 3, False),
        ("ADJACENT_SHA_VERDICT", "adjacent_precedence", "success", "200", "10", SHA_A, MISSING, SHA_B, "failed", (4, 5, 7), "blocked", BUSINESS_FAILURE_REASONS[3], 4, False),
        ("ADJACENT_VERDICT_LENGTH", "adjacent_precedence", "success", "200", "10", SHA_A, "11", MISSING, "failed", (5, 6, 7), "blocked", BUSINESS_FAILURE_REASONS[4], 5, False),
        ("ADJACENT_LENGTH_AUTHORITY", "adjacent_precedence", "success", "200", "10", SHA_A, "11", MISSING, MISSING, (6, 7), "blocked", BUSINESS_FAILURE_REASONS[5], 6, False),
    )
    rows = []
    for order, item in enumerate(specs, 1):
        case_id, group, status_value, http, length, observed_sha, expected_length, expected_sha, verdict, active, outcome, reason, rank, strong = item
        rows.append({
            "case_order": str(order), "case_id": case_id, "case_group": group,
            "download_result_status": status_value, "observed_http_status": http,
            "observed_content_length_bytes": length, "observed_sha256": observed_sha,
            "expected_content_length_bytes": expected_length, "expected_sha256": expected_sha,
            "explicit_integrity_verdict": verdict,
            "active_failure_reasons": "|".join(BUSINESS_FAILURE_REASONS[index - 1] for index in active),
            "expected_outcome": outcome, "expected_reason": reason,
            "expected_precedence_rank": str(rank),
            "strong_authority_present": str(strong).lower(), "case_passed": "true",
        })
    return rows


RESOLVED_TRANSITIONS = {
    "ADMIT_013_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED": "download and evaluation envelopes frozen; candidate/batch/stage/fallback forbidden",
    "ADMIT_013_ADMIT_012_VALIDATION_DEPENDENCY_UNRESOLVED": "pipeline prerequisite distinguished from self-validation and direct result consumption",
    "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED": "status HTTP zero-content strong-authority and pass conjunction frozen",
    "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED": "Exact3 trusted authority types producers and comparisons frozen",
    "ADMIT_013_MULTI_FAILURE_PRECEDENCE_UNRESOLVED": "closed Exact7 business failure precedence frozen",
}


def _issue_rows(snapshot: tuple[tuple[Path, bytes, str, str], ...]) -> list[dict[str, str]]:
    path = "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_issue_readiness_inventory.csv"
    inherited = _rows(snapshot, path)
    output = []
    for order, row in enumerate(inherited, 1):
        resolution = RESOLVED_TRANSITIONS.get(row["issue_id"])
        output.append({
            "inherited_order": str(order),
            **{column: row[column] for column in INHERITED_ISSUE_COLUMNS},
            "effective_status": "resolved" if resolution else row["status"],
            "transition_stage": STAGE if resolution else "",
            "transition_action": "resolved_by_successor_contract_design" if resolution else "unchanged",
            "transition_evidence": resolution or "inherited identity and status retained",
        })
    return output


def _readiness() -> dict[str, bool]:
    return {
        "admit_013_preconditions_audited": True,
        "admit_013_download_outcome_and_integrity_contract_designed": True,
        "admit_013_routing_responsibility_resolved": True,
        "admit_013_admit_012_validation_dependency_resolved": True,
        "admit_013_download_outcome_policy_frozen": True,
        "admit_013_integrity_comparison_authority_resolved": True,
        "admit_013_multi_failure_precedence_resolved": True,
        "admit_013_reason_vocabulary_frozen": True,
        "admit_013_future_evaluator_pure_in_memory_possible": True,
        "ready_for_admit_013_formal_evaluator_interface_contract_design": True,
        "feature_semantics_audit_required_before_training": True,
        "admit_013_standalone_signature_frozen": False,
        "admit_013_formal_result_contract_frozen": False,
        "ready_for_admit_013_standalone_evaluator_interface_implementation": False,
        "evaluate_admit_013_implemented": False,
        "Admit013EvaluationResult_implemented": False,
        "admit_013_unified_adapter_contract_frozen": False,
        "admit_013_unified_adapter_implemented": False,
        "admit_013_registered_in_engine": False,
        "unified_dispatch_runtime_with_admit_001_to_013_implemented": False,
        "provider_mapping_validated": False,
        "real_provider_evaluation_ready": False,
        "ready_for_bulk_download_now": False,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "ready_for_training": False,
        "step12d_is_final_training_feature_contract": False,
    }


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def build_artifacts(
    snapshot: tuple[tuple[Path, bytes, str, str], ...] | None = None,
) -> dict[str, bytes]:
    frozen = build_frozen_source_snapshot() if snapshot is None else snapshot
    _validate_predecessors(frozen)
    outcome = _outcome_rows()
    authority = _authority_rows()
    failure = _failure_rows()
    truth = _truth_rows()
    issues = _issue_rows(frozen)
    payloads = {
        OUTCOME_FILE: _csv_bytes(OUTCOME_COLUMNS, outcome),
        AUTHORITY_FILE: _csv_bytes(AUTHORITY_COLUMNS, authority),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, failure),
        TRUTH_FILE: _csv_bytes(TRUTH_COLUMNS, truth),
        ISSUE_FILE: _csv_bytes(ISSUE_COLUMNS, issues),
    }
    output_sha256 = {name: hashlib.sha256(value).hexdigest() for name, value in payloads.items()}
    readiness = _readiness()
    manifest: dict[str, Any] = {
        "project": "CovaPIE",
        "stage": STAGE,
        "manifest_schema_version": "covapie_admit_013_download_outcome_and_integrity_contract_manifest_v1",
        "base_commit": BASE_COMMIT,
        "base_parent": BASE_PARENT,
        "base_subject": BASE_SUBJECT,
        "admission_rule_id": "ADMIT_013",
        "admission_rule_name": "download_failure_fail_closed",
        "evidence_source": "future_download_result",
        "required_status": "non_success_or_integrity_failure_not_admitted",
        "failure_severity": "blocking",
        "blocking_reason": "download_failure_must_fail_closed",
        "evaluation_phase": "post_download",
        "exact4_fields": list(EXACT4_FIELDS),
        "integrity_authority_fields": list(AUTHORITY_FIELDS),
        "http_success_range": [200, 299],
        "zero_content_length_structurally_allowed": True,
        "zero_content_length_admitted": False,
        "outcome_vocabulary": ["passed", "blocked"],
        "reason_vocabulary": list(REASON_VOCABULARY),
        "business_failure_precedence": list(BUSINESS_FAILURE_REASONS),
        "structural_validation_precedes_business_outcome": True,
        "admit_012_dependency_boundary": {
            "pipeline_level_prerequisite_allowed": True,
            "standalone_evaluator_self_validation_required": True,
            "direct_cross_rule_result_consumption_allowed": False,
            "Admit012EvaluationResult_consumed": False,
        },
        "routing_contract": {
            "download_result_context": list(EXACT4_FIELDS),
            "evaluation_context": list(AUTHORITY_FIELDS),
            "forbidden_envelopes": ["candidate_record", "batch_context", "stage_authorization_context", "fallback_envelope"],
            "normalization_inference_file_network_recompute_allowed": False,
        },
        "pass_conditions": [
            "download_result_status == success",
            "200 <= observed_http_status <= 299",
            "observed_content_length_bytes > 0",
            "all provided trusted authorities agree",
            "expected SHA exact match or explicit verified",
        ],
        "insufficient_pass_conditions": [
            "status success alone", "HTTP 2xx alone", "content length > 0 alone",
            "valid SHA grammar alone", "expected content length match alone",
            "nonzero content plus valid SHA grammar",
        ],
        "forbidden_pseudo_authorities": list(FORBIDDEN_PSEUDO_AUTHORITIES),
        "row_counts": {
            "outcome_policy": len(outcome), "integrity_authority": len(authority),
            "failure_taxonomy": len(failure), "truth_matrix": len(truth),
            "issue_inventory": len(issues),
        },
        "truth_matrix_group_counts": {
            group: sum(row["case_group"] == group for row in truth)
            for group in sorted({row["case_group"] for row in truth})
        },
        "issue_transition_counts": {
            "inherited": len(issues),
            "resolved_by_this_stage": len(RESOLVED_TRANSITIONS),
            "remaining_open_admit_013": sum(
                row["affected_rules"] == "ADMIT_013" and row["effective_status"] == "open"
                for row in issues
            ),
        },
        "resolved_precondition_ids": [
            "PRE_013", "PRE_014", "PRE_015", "PRE_016", "PRE_018", "PRE_019",
            "PRE_020", "PRE_021", "PRE_022", "PRE_023", "PRE_024", "PRE_026",
            "PRE_027", "PRE_028",
        ],
        "remaining_open_precondition_ids": ["PRE_029", "PRE_030"],
        "source_count": len(frozen),
        "source_path_list_sha256": SOURCE_PATH_LIST_SHA256,
        "source_path_sha256_pairs_sha256": SOURCE_PATH_SHA256_PAIRS_SHA256,
        "source_boundary": [
            {"path": path.as_posix(), "sha256": digest, "base_tree_mode": mode}
            for path, _, digest, mode in frozen
        ],
        "output_file_count": len(OUTPUT_FILES),
        "output_files": list(OUTPUT_FILES),
        "output_sha256": output_sha256,
        "recommended_next_step": "design_covapie_admit_013_formal_evaluator_interface_contract_v1",
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "renameat2_policy": "RENAME_NOREPLACE_required;_EINVAL_fails_closed_without_os.replace_fallback",
        "readiness": readiness,
        "safety": {
            "provider": False, "network": False, "download": False, "raw": False,
            "model_or_checkpoint": False, "dataloader": False, "runtime_change": False,
            "training": False, "stage_commit_push": False,
        },
        "all_checks_passed": True,
    }
    payloads[MANIFEST_FILE] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return payloads


def _rename_noreplace(source: Path, destination: Path) -> None:
    if os.uname().machine not in {"x86_64", "amd64"}:
        raise ValueError("renameat2 syscall number unavailable")
    result = ctypes.CDLL(None, use_errno=True).syscall(
        316, -100, os.fsencode(source), -100, os.fsencode(destination), 1
    )
    if result:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination)


def _write_leaf(path: Path, data: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        0o644,
    )
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(descriptor, view):]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_output_at(
    root_fd: int, name: str, expected_identity: tuple[int, int, int]
) -> bytes:
    if _identity(os.lstat(name, dir_fd=root_fd)) != expected_identity:
        raise ValueError("output leaf identity drift before open")
    descriptor = os.open(
        name,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        dir_fd=root_fd,
    )
    try:
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("output leaf stat/open race")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("output leaf FD identity drift")
        if _identity(os.lstat(name, dir_fd=root_fd)) != expected_identity:
            raise ValueError("output leaf lexical identity drift")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _read_exact_output_set(root: Path, payloads: dict[str, bytes]) -> bool:
    parent_identity = _identity(os.lstat(root.parent))
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
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root stat/open race")
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            return False
        leaf_identities: dict[str, tuple[int, int, int]] = {}
        for name in OUTPUT_FILES:
            item = os.lstat(name, dir_fd=root_fd)
            if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
                raise ValueError("unsafe output leaf")
            leaf_identities[name] = _identity(item)
        matches = True
        for name, expected in payloads.items():
            if _read_output_at(root_fd, name, leaf_identities[name]) != expected:
                matches = False
        if _identity(os.lstat(root.parent)) != parent_identity:
            raise ValueError("output parent identity drift")
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root FD identity drift")
        if _identity(os.lstat(root)) != root_identity:
            raise ValueError("output root lexical identity drift")
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("output inventory drift")
        if any(
            _identity(os.lstat(name, dir_fd=root_fd)) != leaf_identities[name]
            for name in OUTPUT_FILES
        ):
            raise ValueError("output leaf identity drift after traversal")
        return matches
    finally:
        os.close(root_fd)


def _cleanup_owned_staging(staging: Path) -> None:
    if not staging.exists():
        return
    entries = {entry.name: entry for entry in staging.iterdir()}
    if set(entries) - set(OUTPUT_FILES):
        return
    for entry in entries.values():
        item = os.lstat(entry)
        if stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode):
            entry.unlink()
    try:
        staging.rmdir()
    except OSError:
        pass


def materialize_contract(output_root: Path | None = None) -> dict[str, Any]:
    root = REPO_ROOT / DEFAULT_OUTPUT_ROOT if output_root is None else Path(output_root)
    parent = root.parent
    parent_item = os.lstat(parent)
    if stat.S_ISLNK(parent_item.st_mode) or not stat.S_ISDIR(parent_item.st_mode):
        raise ValueError("unsafe output parent")
    payloads = build_artifacts()
    if root.exists() or root.is_symlink():
        if _read_exact_output_set(root, payloads):
            return json.loads(payloads[MANIFEST_FILE])
        raise ValueError("existing output set mismatch")
    staging = Path(tempfile.mkdtemp(prefix=f".{root.name}.", suffix=".staging", dir=parent))
    try:
        for name in OUTPUT_FILES:
            _write_leaf(staging / name, payloads[name])
        descriptor = os.open(staging, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        _rename_noreplace(staging, root)
        _fsync_directory(parent)
        if not _read_exact_output_set(root, payloads):
            raise ValueError("published output postverify failed")
    except BaseException:
        _cleanup_owned_staging(staging)
        raise
    return json.loads(payloads[MANIFEST_FILE])


def run_covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Explicitly materialize the Exact6 design evidence set."""
    return materialize_contract(output_root)
