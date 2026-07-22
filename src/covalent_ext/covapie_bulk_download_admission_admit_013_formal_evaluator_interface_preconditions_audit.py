"""Read-only ADMIT_013 formal-evaluator precondition audit.

The module reads only committed metadata pinned to ``BASE_COMMIT``.  It does
not implement an ADMIT_013 evaluator, result type, adapter, registry entry,
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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "5ff12d358a633c44c333022f7e0ebe30f039d6fc"
BASE_SUBJECT = "add CovaPIE unified dispatch runtime with ADMIT_001 to ADMIT_012 v1"
STAGE = "covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1"
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

FIELDS = (
    "download_result_status",
    "observed_http_status",
    "observed_content_length_bytes",
    "observed_sha256",
)
POLICY_CONTEXTS = (
    "allowed_download_result_statuses",
    "successful_http_status_contract",
    "content_length_contract",
    "sha256_format_contract",
)
COMPARISON_AUTHORITY_TERMS = (
    "expected_sha256",
    "expected_content_length_bytes",
    "download_integrity_passed",
    "checksum_verified",
    "content_length_verified",
    "provider_integrity_verdict",
    "trusted_download_manifest",
)
SEARCH_TERMS = (
    "ADMIT_013",
    "download_failure_fail_closed",
    "non_success_or_integrity_failure_not_admitted",
    "download_failure_must_fail_closed",
    *FIELDS,
    "successful_http_status_contract",
    "content_length_contract",
    "sha256_format_contract",
    "expected_sha256",
    "expected_content_length_bytes",
    "integrity",
    "checksum",
    "content_length",
)
REQUIRED_STAGE_FRAGMENTS = (
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate",
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate",
    "covapie_bulk_download_admission_admit_012_download_integrity_field_contract",
    "covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract",
    "covapie_bulk_download_admission_admit_012_rule_logic_interface",
    "covapie_bulk_download_admission_admit_012_unified_adapter_contract",
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012",
    "covapie_bulk_download_admission_admit_012_formal_evaluator_interface_preconditions_audit",
)
EXPECTED_SOURCE_COUNT = 545
EXPECTED_PATH_LIST_SHA256 = "d0cfd2b25097e62a23af6c89339b606d07ebb176c298e406f47c1981953bc105"
EXPECTED_PATH_SHA256_PAIRS_SHA256 = "d81100221ae603ccc2e660a194d4f8da009e96c85130a1f29f3678163a696d2d"

DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
PRECONDITION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
)
FIELD_CONTRACT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1"
)
FORMAL_CONTRACT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1"
)
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1"
)
RULE_REGISTRY = DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"
SCHEMA_CONTRACT = DESIGN_ROOT / "covapie_bulk_download_admission_schema_contract.csv"
EXECUTABILITY = PRECONDITION_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"
FIELD_SEMANTICS = PRECONDITION_ROOT / "covapie_bulk_download_admission_field_semantics_matrix.csv"
EVALUATION_CONTEXT = PRECONDITION_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"
ADMIT012_FIELD_CONTRACT = FIELD_CONTRACT_ROOT / "covapie_admit_012_download_integrity_field_contract.csv"
ADMIT012_STATUS_ENUM = FIELD_CONTRACT_ROOT / "covapie_admit_012_download_result_status_enum.csv"
ADMIT012_FIELD_TRUTH = FIELD_CONTRACT_ROOT / "covapie_admit_012_download_integrity_validation_truth_matrix.csv"
ADMIT012_FORMAL_ROUTING = FORMAL_CONTRACT_ROOT / "covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv"
RUNTIME_REGISTRY = RUNTIME_ROOT / "covapie_admit_001_to_012_registry_and_identity_audit.csv"
RUNTIME_ISSUES = RUNTIME_ROOT / "covapie_admit_001_to_012_runtime_issue_readiness_inventory.csv"
RUNTIME_MANIFEST = RUNTIME_ROOT / "covapie_admit_001_to_012_runtime_manifest.json"
RUNTIME_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py"
)

FILES = (
    "covapie_admit_013_formal_evaluator_precondition_matrix.csv",
    "covapie_admit_013_field_occurrence_inventory.csv",
    "covapie_admit_013_observed_value_inventory.csv",
    "covapie_admit_013_source_boundary_audit.csv",
    "covapie_admit_013_issue_readiness_inventory.csv",
    "covapie_admit_013_formal_evaluator_preconditions_manifest.json",
)
PRECONDITION, OCCURRENCE, OBSERVED, SOURCE_AUDIT, ISSUE, MANIFEST = FILES
COLUMNS = {
    PRECONDITION: (
        "precondition_order", "precondition_id", "precondition_group",
        "precondition_subject", "expected_contract", "observed_evidence",
        "completeness_status", "implementation_blocking", "blocking_reason",
        "precondition_passed",
    ),
    OCCURRENCE: (
        "occurrence_order", "semantic_subject", "field_or_term_name",
        "relative_path", "file_role", "occurrence_kind",
        "declaring_or_referencing", "phase_claim", "type_claim",
        "validation_claim", "source_authority_level", "current_contract_effect",
        "admit_013_relevance", "occurrence_passed",
    ),
    OBSERVED: (
        "value_order", "semantic_subject", "field_name", "source_path",
        "representation", "source_kind", "real_observed_value",
        "synthetic_example", "placeholder", "schema_only",
        "produced_by_download_execution", "trusted_comparison_authority",
        "admissible_as_admit_013_semantic_evidence", "notes",
    ),
    SOURCE_AUDIT: (
        "source_order", "source_relative_path", "source_kind", "base_tree_mode",
        "base_tree_sha256", "filesystem_sha256", "tracked_regular_non_symlink",
        "parent_chain_verified", "pinned_fd_read", "triple_sha256_passed",
        "source_boundary_passed",
    ),
}

AUTHORITY_LEVELS = (
    "primary_committed_contract",
    "committed_runtime_contract",
    "committed_design_evidence",
    "historical_or_reference",
    "test_fixture",
    "source_attestation_hash",
    "documentation_only",
    "unrelated_text",
)

PRIMARY_CONTRACT_PATHS = frozenset(
    (
        RULE_REGISTRY,
        SCHEMA_CONTRACT,
        EXECUTABILITY,
        FIELD_SEMANTICS,
        EVALUATION_CONTEXT,
        ADMIT012_FIELD_CONTRACT,
        ADMIT012_STATUS_ENUM,
        ADMIT012_FIELD_TRUTH,
    )
)
DESIGN_EVIDENCE_PATHS = frozenset(
    (
        ADMIT012_FORMAL_ROUTING,
        FIELD_CONTRACT_ROOT / "covapie_admit_012_download_integrity_field_contract_manifest.json",
        FORMAL_CONTRACT_ROOT / "covapie_admit_012_formal_evaluator_interface_contract_manifest.json",
    )
)


@dataclass(frozen=True)
class Source:
    path: Path
    content: bytes
    sha256: str
    base_mode: str


def _git(args: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=text, check=False
    )


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _safe(path: Path) -> bool:
    return (
        not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[:2] != ("data", "raw")
        and path.parts[0] != "checkpoints"
        and STAGE not in path.as_posix()
    )


def _kind(path: Path) -> str:
    if path.suffix == ".py":
        return "python_source"
    if path.suffix == ".csv":
        return "committed_csv"
    if path.suffix == ".json":
        return "committed_manifest"
    return "tracked_text"


def _paths() -> tuple[Path, ...]:
    command = ["grep", "-l", "-I"]
    for term in SEARCH_TERMS:
        command.extend(("-e", term))
    command.extend((BASE_COMMIT, "--", ":!data/raw/**", ":!checkpoints/**"))
    result = _git(command)
    if result.returncode not in (0, 1):
        raise ValueError("base occurrence discovery failed")
    prefix = f"{BASE_COMMIT}:"
    lines = [line for line in result.stdout.splitlines() if line]
    if any(not line.startswith(prefix) for line in lines):
        raise ValueError("unsafe base occurrence discovery")
    discovered = {Path(line.removeprefix(prefix)) for line in lines}

    tree = _git(["ls-tree", "-r", "--name-only", BASE_COMMIT])
    if tree.returncode:
        raise ValueError("base tree path discovery failed")
    required = {
        Path(line)
        for line in tree.stdout.splitlines()
        if any(fragment in line for fragment in REQUIRED_STAGE_FRAGMENTS)
    }
    paths = tuple(sorted(discovered | required, key=lambda value: value.as_posix()))
    serialized = [path.as_posix() for path in paths]
    digest = hashlib.sha256(
        json.dumps(serialized, separators=(",", ":")).encode()
    ).hexdigest()
    if not all(_safe(path) for path in paths):
        raise ValueError("unsafe source boundary")
    if len(paths) != EXPECTED_SOURCE_COUNT or digest != EXPECTED_PATH_LIST_SHA256:
        raise ValueError("frozen source path boundary mismatch")
    return paths


def _real_repo_root() -> Path:
    item = os.lstat(REPO_ROOT)
    if (
        stat.S_ISLNK(item.st_mode)
        or not stat.S_ISDIR(item.st_mode)
        or REPO_ROOT.resolve(strict=True) != REPO_ROOT
    ):
        raise ValueError("unsafe repository root")
    return REPO_ROOT


def _parent_chain(path: Path) -> None:
    current = (REPO_ROOT / path).parent
    while current != REPO_ROOT:
        item = os.lstat(current)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
            raise ValueError("unsafe source parent")
        current = current.parent


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode


def _pinned_read(
    path: Path, expected_identity: tuple[int, int, int] | None = None
) -> bytes:
    absolute = REPO_ROOT / path
    _real_repo_root()
    _parent_chain(path)
    before = os.lstat(absolute)
    expected_identity = expected_identity or _identity(before)
    if _identity(before) != expected_identity:
        raise ValueError("source lexical identity drift before open")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(absolute, flags)
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
            raise ValueError("source FD identity drift after read")
        if _identity(os.lstat(absolute)) != expected_identity:
            raise ValueError("source lexical replacement after read")
        _parent_chain(path)
        _real_repo_root()
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def build_frozen_source_snapshot() -> tuple[Source, ...]:
    _real_repo_root()
    subject = _git(["show", "-s", "--format=%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if (
        subject.returncode
        or ancestor.returncode
        or subject.stdout.strip() != BASE_SUBJECT
    ):
        raise ValueError("base lineage unavailable")
    paths = _paths()

    # Complete structural preflight occurs before the first filesystem source read.
    structures: list[tuple[Path, str, tuple[int, int, int]]] = []
    for path in paths:
        absolute = REPO_ROOT / path
        _parent_chain(path)
        item = os.lstat(absolute)
        tree = _git(["ls-tree", BASE_COMMIT, "--", path.as_posix()])
        tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()])
        head, separator, tree_path = tree.stdout.partition("\t")
        fields = head.split() if tree.returncode == 0 else []
        if (
            tracked.returncode
            or tracked.stdout.splitlines() != [path.as_posix()]
            or tree.returncode
            or not separator
            or tree_path.strip() != path.as_posix()
            or len(fields) != 3
            or fields[0] not in {"100644", "100755"}
            or fields[1] != "blob"
            or stat.S_ISLNK(item.st_mode)
            or not stat.S_ISREG(item.st_mode)
            or absolute.resolve(strict=True) != absolute
        ):
            raise ValueError(f"unsafe source: {path}")
        structures.append((path, fields[0], _identity(item)))

    records: list[Source] = []
    pairs: list[list[str]] = []
    for path, mode, expected_identity in structures:
        base = _git(["show", f"{BASE_COMMIT}:{path.as_posix()}"], text=False)
        current = _pinned_read(path, expected_identity)
        if base.returncode or not isinstance(base.stdout, bytes):
            raise ValueError(f"base source unavailable: {path}")
        base_digest = hashlib.sha256(base.stdout).hexdigest()
        digest = hashlib.sha256(current).hexdigest()
        if base_digest != digest:
            raise ValueError(f"source drift: {path}")
        pairs.append([path.as_posix(), digest])
        records.append(Source(path, current, digest, mode))
    pair_digest = hashlib.sha256(
        json.dumps(pairs, separators=(",", ":")).encode()
    ).hexdigest()
    if pair_digest != EXPECTED_PATH_SHA256_PAIRS_SHA256:
        raise ValueError("frozen source SHA boundary mismatch")
    return tuple(records)


def _record(snapshot: tuple[Source, ...], path: Path) -> Source:
    return next(source for source in snapshot if source.path == path)


def _rows(snapshot: tuple[Source, ...], path: Path) -> list[dict[str, str]]:
    return list(
        csv.DictReader(io.StringIO(_record(snapshot, path).content.decode(), newline=""))
    )


def _contracts(snapshot: tuple[Source, ...]) -> None:
    rule = next(
        row for row in _rows(snapshot, RULE_REGISTRY)
        if row["admission_rule_id"] == "ADMIT_013"
    )
    expected_rule = {
        "admission_rule_id": "ADMIT_013",
        "admission_rule_name": "download_failure_fail_closed",
        "evidence_source": "future_download_result",
        "required_status": "non_success_or_integrity_failure_not_admitted",
        "failure_severity": "blocking",
        "blocking_reason": "download_failure_must_fail_closed",
        "evaluation_phase": "post_download",
        "network_required": "false",
        "raw_structure_required": "false",
        "ready_for_future_implementation": "true",
    }
    if rule != expected_rule:
        raise ValueError("ADMIT_013 registry identity drift")

    executable = next(
        row for row in _rows(snapshot, EXECUTABILITY)
        if row["admission_rule_id"] == "ADMIT_013"
    )
    if not (
        executable["admission_rule_name"] == "download_failure_fail_closed"
        and executable["evaluation_phase"] == "post_download"
        and executable["candidate_field_dependencies"].split("|") == list(FIELDS)
        and executable["batch_context_dependencies"] == ""
        and executable["evaluation_context_dependencies"].split("|")
        == list(POLICY_CONTEXTS)
        and executable["external_filesystem_required"] == "false"
        and executable["network_required"] == "false"
        and executable["download_execution_result_required"] == "true"
        and executable["pure_in_memory_interface_possible"] == "true"
        and executable["semantics_complete"] == "false"
        and executable["deterministic_evaluation_possible_now"] == "false"
        and executable["deterministic_evaluation_possible_after_contract_freeze"] == "true"
        and executable["implementation_disposition"] == "interface_only_pending_semantics"
    ):
        raise ValueError("ADMIT_013 executability evidence drift")

    field_rows = [
        row for row in _rows(snapshot, FIELD_SEMANTICS)
        if row["field_name"] in FIELDS
    ]
    if [row["field_name"] for row in field_rows] != list(FIELDS):
        raise ValueError("Exact4 field order drift")
    if not all(
        row["candidate_record_field"] == "false"
        and row["producer_scope"] == "download_execution_result"
        and row["dependent_rules"] == "ADMIT_012|ADMIT_013"
        and row["implementation_semantics_complete"] == "false"
        for row in field_rows
    ):
        raise ValueError("Exact4 lifecycle evidence drift")

    context_rows = [
        row for row in _rows(snapshot, EVALUATION_CONTEXT)
        if row["context_item"] in POLICY_CONTEXTS
    ]
    if [row["context_item"] for row in context_rows] != list(POLICY_CONTEXTS):
        raise ValueError("Exact4 context identity drift")
    if not all(
        row["required_by_rules"] == "ADMIT_012|ADMIT_013"
        and row["provided_by_future_caller"] == "true"
        and row["filesystem_access_inside_evaluator"] == "false"
        and row["network_access_inside_evaluator"] == "false"
        and row["exact_contract_defined"] == "false"
        for row in context_rows
    ):
        raise ValueError("Step14AU-A context evidence drift")

    exact4 = _rows(snapshot, ADMIT012_FIELD_CONTRACT)
    if [row["field_name"] for row in exact4] != list(FIELDS):
        raise ValueError("ADMIT_012 shared Exact4 contract drift")
    expected_shapes = (
        ("str", "", "", "", ""),
        ("int", "100", "599", "200", "299"),
        ("int", "", "", "", ""),
        ("str", "", "", "", ""),
    )
    for row, shape in zip(exact4, expected_shapes):
        if (
            row["exact_builtin_type"], row["legal_minimum"], row["legal_maximum"],
            row["future_success_minimum"], row["future_success_maximum"]
        ) != shape:
            raise ValueError("shared Exact4 structural shape drift")
        if not (
            row["subclasses_allowed"] == "false"
            and row["normalization_allowed"] == "false"
            and row["presence_required"] == "true"
            and row["admit_012_executes_success_judgment"] == "false"
            and row["used_by_admit_012"] == "true"
            and row["reserved_for_admit_013"] == "true"
            and row["contract_passed"] == "true"
        ):
            raise ValueError("shared Exact4 boundary drift")
    if not (
        exact4[0]["ordered_allowed_values"] == "success|failure"
        and exact4[0]["success_subset"] == "success"
        and exact4[2]["value_contract"]
        == "integer observed byte count >= 0; no V1 upper bound"
        and exact4[3]["value_contract"]
        == "exactly 64 ASCII lowercase hexadecimal characters [0-9a-f]{64}"
    ):
        raise ValueError("shared Exact4 value contract drift")

    canonical_status = [
        row for row in _rows(snapshot, ADMIT012_STATUS_ENUM)
        if row["row_kind"] == "canonical_enum"
    ]
    if [row["status_value"] for row in canonical_status] != ["success", "failure"]:
        raise ValueError("download status enum drift")
    if [row["future_admit_013_disposition"] for row in canonical_status] != [
        "pending_integrity_match_checks_not_implemented_here",
        "blocked_not_implemented_here",
    ]:
        raise ValueError("ADMIT_012/013 status boundary drift")

    truth = {row["case_id"]: row for row in _rows(snapshot, ADMIT012_FIELD_TRUTH)}
    for case_id in (
        "BOUNDARY_FAILURE_STATUS", "BOUNDARY_VALID_4XX",
        "BOUNDARY_VALID_5XX_FAILURE", "VALID_CONTENT_ZERO",
    ):
        if truth[case_id]["observed_contract_outcome"] != "contract_valid":
            raise ValueError("ADMIT_012 boundary case drift")

    routes = _rows(snapshot, ADMIT012_FORMAL_ROUTING)
    route_rows = [row for row in routes if row["contract_kind"] == "route"]
    if [row["formal_parameter"] for row in route_rows[:4]] != list(FIELDS):
        raise ValueError("ADMIT_012 formal Exact4 route drift")
    if [row["formal_parameter"] for row in route_rows[4:8]] != list(POLICY_CONTEXTS):
        raise ValueError("ADMIT_012 formal policy route drift")
    if any("ADMIT_013" in "|".join(row.values()) for row in route_rows):
        raise ValueError("ADMIT_012 routing unexpectedly promoted to ADMIT_013")

    registry = _rows(snapshot, RUNTIME_REGISTRY)
    not_registered = {
        row["audit_item"]: row["observed_value"]
        for row in registry if row["audit_item"].startswith("not_registered:")
    }
    if not_registered != {
        "not_registered:ADMIT_013": "False",
        "not_registered:ADMIT_014": "False",
        "not_registered:ADMIT_015": "False",
    }:
        raise ValueError("known-unregistered runtime evidence drift")

    issues = _rows(snapshot, RUNTIME_ISSUES)
    if len(issues) != 16:
        raise ValueError("Exact16 runtime issue inventory drift")
    coverage = next(
        row for row in issues
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    )
    aggregation = next(
        row for row in issues
        if row["issue_id"]
        == "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
    )
    if not (
        coverage["affected_rules"] == "ADMIT_013|ADMIT_014|ADMIT_015"
        and coverage["status"] == "open"
        and aggregation["status"] == "open"
    ):
        raise ValueError("runtime open-issue evidence drift")
    runtime_manifest = json.loads(_record(snapshot, RUNTIME_MANIFEST).content.decode())
    if not (
        runtime_manifest["registered_rule_count"] == 12
        and runtime_manifest["known_not_registered_rule_ids"]
        == ["ADMIT_013", "ADMIT_014", "ADMIT_015"]
        and runtime_manifest["combined_candidate_verdict_implemented"] is False
        and runtime_manifest["cross_rule_aggregation_implemented"] is False
    ):
        raise ValueError("Exact12 runtime manifest drift")
    runtime_source = _record(snapshot, RUNTIME_PRODUCTION).content.decode()
    forbidden_definitions = (
        "def evaluate_admit_013", "class Admit013EvaluationResult",
        "def _evaluate_registered_admit_013",
    )
    if any(value in runtime_source for value in forbidden_definitions):
        raise ValueError("ADMIT_013 unexpectedly implemented at base")

    # The assigned authoritative schema/context has no comparison producer,
    # consumer, value, verdict, or precedence contract for these keys.
    authority_paths = (
        SCHEMA_CONTRACT, EXECUTABILITY, FIELD_SEMANTICS, EVALUATION_CONTEXT,
        ADMIT012_FIELD_CONTRACT, ADMIT012_FORMAL_ROUTING,
    )
    authority_text = "\n".join(
        _record(snapshot, path).content.decode() for path in authority_paths
    )
    if any(term in authority_text for term in COMPARISON_AUTHORITY_TERMS):
        raise ValueError("unexpected ADMIT_013 comparison authority")


def _preconditions() -> list[dict[str, str]]:
    specs = (
        ("identity", "rule ID", "ADMIT_013", "Step14AT exact registry row", True, ""),
        ("identity", "rule name", "download_failure_fail_closed", "Step14AT exact registry row", True, ""),
        ("identity", "evaluation phase", "post_download", "Step14AT exact registry row", True, ""),
        ("identity", "evidence source", "future_download_result", "Step14AT exact registry row", True, ""),
        ("identity", "required status", "non_success_or_integrity_failure_not_admitted", "Step14AT exact registry row", True, ""),
        ("identity", "blocking reason", "download_failure_must_fail_closed", "Step14AT exact registry row", True, ""),
        ("structural", "Exact4 field identity/order", "download_result_status|observed_http_status|observed_content_length_bytes|observed_sha256", "shared ADMIT_012 field contract exact order", True, ""),
        ("structural", "download_result_status structural contract", "exact built-in str; closed success|failure; no normalization", "ADMIT_012 shared structural contract", True, ""),
        ("structural", "observed_http_status structural contract", "exact built-in int; bool/subclass rejected; 100..599", "ADMIT_012 shared structural contract", True, ""),
        ("structural", "observed_content_length_bytes structural contract", "exact built-in int; >=0; zero allowed; no upper bound; no file recompute", "ADMIT_012 shared structural contract", True, ""),
        ("structural", "observed_sha256 structural contract", "exact built-in str; ASCII lowercase [0-9a-f]{64}; no normalization or file recompute", "ADMIT_012 shared structural contract", True, ""),
        ("structural", "existing Exact4 policy-context identity", "allowed statuses|HTTP contract|content contract|SHA format contract", "ADMIT_012 formal interface freezes these identities for ADMIT_012", True, ""),
        ("routing", "post-download routing responsibility", "ADMIT_013 envelope sources and forbidden envelopes frozen", "only ADMIT_012 routing is frozen", False, "ADMIT_013_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED"),
        ("dependency", "ADMIT_012 prerequisite/revalidation boundary", "self-validation versus prior formal ADMIT_012 result frozen", "single-rule runtime has no cross-rule prerequisite contract", False, "ADMIT_013_ADMIT_012_VALIDATION_DEPENDENCY_UNRESOLVED"),
        ("dependency", "missing/presence behavior", "ADMIT_013 missing handling and precedence frozen", "ADMIT_012 presence semantics exist but ADMIT_013 adoption is absent", False, "ADMIT_013_ADMIT_012_VALIDATION_DEPENDENCY_UNRESOLVED"),
        ("outcome", "canonical success-status decision", "success alone has a deterministic ADMIT_013 disposition", "only pending future integrity checks is stated", False, "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("outcome", "canonical failure-status decision", "failure is blocked", "registry non-success fail-closed plus shared status row blocked_not_implemented_here", True, ""),
        ("outcome", "HTTP success-range adoption", "ADMIT_013 explicitly adopts or rejects 200..299", "future bounds exist but no ADMIT_013 adoption contract", False, "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("outcome", "status/HTTP contradiction behavior", "success+non-2xx and failure+2xx precedence frozen", "no committed ADMIT_013 contradiction table", False, "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("integrity", "zero-content-length disposition", "zero allowed/blocked cases frozen", "zero is structurally legal; business disposition absent", False, "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("integrity", "expected content-length authority", "trusted producer/context/type frozen", "no assigned authoritative field or context", False, "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("integrity", "content-length comparison contract", "observed-versus-expected comparison/reason/precedence frozen", "no authoritative comparison contract", False, "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("integrity", "expected SHA256 authority", "trusted producer/context/type frozen", "source/artifact hashes exist but no download authority", False, "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("integrity", "SHA comparison contract", "observed-versus-expected comparison/reason/precedence frozen", "no authoritative comparison contract or verdict", False, "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("integrity", "syntactic SHA versus integrity semantics", "valid grammar is not an integrity verdict", "ADMIT_012 explicitly limits SHA to representation grammar", True, ""),
        ("outcome", "provider/transport failure taxonomy", "HTTP timeout DNS partial empty checksum provider write failures represented", "success|failure does not freeze category mapping or reasons", False, "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("precedence", "multi-failure precedence", "missing invalid status HTTP length SHA conflicts ordered", "no committed ADMIT_013 precedence table", False, "ADMIT_013_MULTI_FAILURE_PRECEDENCE_UNRESOLVED"),
        ("result", "closed reason vocabulary", "complete ADMIT_013 reason vocabulary frozen", "registry blocker is not a closed result-reason vocabulary", False, "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("interface", "public standalone signature", "scalar/context/prior-result/Mapping choice frozen", "no ADMIT_013 standalone signature contract", False, "ADMIT_013_STANDALONE_SIGNATURE_UNRESOLVED"),
        ("interface", "formal result contract", "representation/prefix/consumption/outcome/reason invariants frozen", "ADMIT_012 Exact10 is rule-specific; no ADMIT_013 result contract", False, "ADMIT_013_RESULT_CONTRACT_UNRESOLVED"),
        ("boundary", "pure in-memory/no-I/O boundary", "future evaluator may be pure; no network/raw/filesystem", "Step14AT/AU-A exact false I/O requirements", True, ""),
        ("authorization", "authorization/training boundary", "no provider/network/download/raw/runtime/training; feature audit required", "current task and committed readiness fail closed", True, ""),
    )
    rows: list[dict[str, str]] = []
    for number, (group, subject, expected, evidence, complete, blocker) in enumerate(specs, 1):
        rows.append(
            {
                "precondition_order": str(number),
                "precondition_id": f"PRE_{number:03d}",
                "precondition_group": group,
                "precondition_subject": subject,
                "expected_contract": expected,
                "observed_evidence": evidence,
                "completeness_status": "complete" if complete else "incomplete",
                "implementation_blocking": "false" if complete else "true",
                "blocking_reason": blocker,
                "precondition_passed": str(complete).lower(),
            }
        )
    return rows


def _role(path: Path) -> str:
    value = path.as_posix()
    if value.startswith("src/"):
        return "production_source"
    if value.startswith("tests/"):
        return "tests"
    if value.startswith("scripts/"):
        return "checker"
    if value.startswith("docs/"):
        return "documentation"
    if path.suffix == ".json":
        return "manifest"
    if "source_boundary" in path.name:
        return "source_boundary"
    if "issue" in path.name:
        return "issue_inventory"
    return "derived_contract_or_evidence"


def _semantic_subject(term: str) -> str:
    if term in {
        "ADMIT_013", "download_failure_fail_closed",
        "non_success_or_integrity_failure_not_admitted",
        "download_failure_must_fail_closed",
    }:
        return "rule_identity"
    if term in FIELDS:
        return "exact4_download_result_field"
    if term.endswith("_contract"):
        return "policy_context"
    if term.startswith("expected_"):
        return "comparison_authority"
    return "integrity_or_transport_semantics"


def _authority(path: Path, term: str, line: str) -> str:
    value = path.as_posix()
    if value.startswith("tests/"):
        return "test_fixture"
    if term == "expected_sha256" and (
        "source_boundary" in path.name
        or path.suffix == ".json"
        or "source_input_verification" in line
    ):
        return "source_attestation_hash"
    if value.startswith("docs/"):
        return "documentation_only"
    if path in PRIMARY_CONTRACT_PATHS:
        return "primary_committed_contract"
    if "unified_dispatch_runtime_with_admit_001_to_012" in value:
        return "committed_runtime_contract"
    if path in DESIGN_EVIDENCE_PATHS or any(
        fragment in value for fragment in REQUIRED_STAGE_FRAGMENTS[:7]
    ):
        return "committed_design_evidence"
    if (
        "admit_012_formal_evaluator_interface_preconditions_audit" in value
        or "real_covalent_pilot_download" in value
    ):
        return "historical_or_reference"
    return "unrelated_text"


def _is_declaration(path: Path, term: str, line: str) -> bool:
    if path == RULE_REGISTRY and line.startswith("ADMIT_013,"):
        return True
    if path == SCHEMA_CONTRACT and line.startswith(f"{term},"):
        return True
    if path in {EXECUTABILITY, FIELD_SEMANTICS, EVALUATION_CONTEXT} and (
        line.startswith("ADMIT_013,") or line.startswith(f"{term},")
    ):
        return True
    if path == ADMIT012_FIELD_CONTRACT and term in FIELDS and f",{term}," in line:
        return True
    if path == ADMIT012_STATUS_ENUM and term == "integrity" and line.startswith(("1,", "2,")):
        return True
    return False


def _occurrences(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    type_claims = {
        "download_result_status": "exact_builtin_str_no_subclasses",
        "observed_http_status": "exact_builtin_int_100_599_no_bool_or_subclasses",
        "observed_content_length_bytes": "exact_builtin_int_minimum_0_no_upper_bound",
        "observed_sha256": "exact_builtin_str_lowercase_hex64",
    }
    for source in snapshot:
        for line in source.content.decode(errors="strict").splitlines():
            for term in SEARCH_TERMS:
                if term not in line:
                    continue
                authority = _authority(source.path, term, line)
                declaration = _is_declaration(source.path, term, line)
                if declaration and source.path == RULE_REGISTRY:
                    effect = "ADMIT_013_rule_identity_authority_only"
                elif declaration and term in FIELDS:
                    effect = "shared_Exact4_identity_or_structural_authority"
                elif authority == "committed_runtime_contract":
                    effect = "Exact12_runtime_state_authority"
                elif authority in {"test_fixture", "documentation_only", "source_attestation_hash", "unrelated_text"}:
                    effect = "not_ADMIT_013_semantic_authority"
                else:
                    effect = "committed_boundary_or_reference_evidence"
                if term in FIELDS:
                    relevance = "shared_structural_contract_or_observed_value_reference"
                elif term.startswith("expected_"):
                    relevance = "candidate_comparison_authority_but_not_assigned_to_ADMIT_013"
                elif term in {"integrity", "checksum", "content_length"}:
                    relevance = "integrity_semantics_search_evidence"
                else:
                    relevance = "ADMIT_013_identity_or_context_evidence"
                rows.append(
                    {
                        "occurrence_order": str(len(rows) + 1),
                        "semantic_subject": _semantic_subject(term),
                        "field_or_term_name": term,
                        "relative_path": source.path.as_posix(),
                        "file_role": _role(source.path),
                        "occurrence_kind": "contract_declaration" if declaration else "textual_or_structured_reference",
                        "declaring_or_referencing": "declaring" if declaration else "referencing",
                        "phase_claim": "post_download" if "post_download" in line else "not_claimed",
                        "type_claim": type_claims.get(term, "not_claimed") if source.path == ADMIT012_FIELD_CONTRACT else "not_claimed",
                        "validation_claim": (
                            "shared_structural_validation_only"
                            if source.path == ADMIT012_FIELD_CONTRACT
                            else "rule_identity_not_truth_table"
                            if source.path == RULE_REGISTRY and declaration
                            else "no_direct_ADMIT_013_validation_claim"
                        ),
                        "source_authority_level": authority,
                        "current_contract_effect": effect,
                        "admit_013_relevance": relevance,
                        "occurrence_passed": "true",
                    }
                )
    return rows


def _observed_kind(path: Path, authority: str, term: str, line: str) -> str:
    value = path.as_posix()
    if authority == "test_fixture":
        return "synthetic_test_fixture"
    if authority == "source_attestation_hash":
        return "source_or_artifact_attestation_hash"
    if value.startswith("docs/"):
        return "documentation_example"
    if "real_covalent_pilot_download_execution" in value or "real_covalent_pilot_download_integrity" in value:
        return "historical_real_download_execution_observation"
    if "real_provider" in value:
        return "historical_real_provider_observation"
    if authority in {"primary_committed_contract", "committed_design_evidence", "committed_runtime_contract"}:
        return "schema_or_committed_contract_representation"
    if "future" in line or "<MISSING>" in line or "placeholder" in line.lower():
        return "placeholder"
    if authority == "historical_or_reference":
        return "historical_or_reference"
    return "unrelated_numeric_or_status_value"


def _observed(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for field in (
        "expected_content_length_bytes", "expected_sha256", "explicit_integrity_verdict"
    ):
        rows.append(
            {
                "value_order": str(len(rows) + 1),
                "semantic_subject": "comparison_authority_absence",
                "field_name": field,
                "source_path": "authoritative_schema_and_context_boundary",
                "representation": "<NO_ASSIGNED_ADMIT_013_AUTHORITY>",
                "source_kind": "schema_authority_absence",
                "real_observed_value": "false",
                "synthetic_example": "false",
                "placeholder": "false",
                "schema_only": "true",
                "produced_by_download_execution": "false",
                "trusted_comparison_authority": "false",
                "admissible_as_admit_013_semantic_evidence": "true",
                "notes": "negative authority finding; no producer/consumer/comparison contract",
            }
        )
    for source in snapshot:
        path_text = source.path.as_posix()
        for line_number, line in enumerate(
            source.content.decode(errors="strict").splitlines(), 1
        ):
            for term in SEARCH_TERMS:
                if term not in line:
                    continue
                authority = _authority(source.path, term, line)
                kind = _observed_kind(source.path, authority, term, line)
                historical_real = kind in {
                    "historical_real_download_execution_observation",
                    "historical_real_provider_observation",
                }
                produced = (
                    kind == "historical_real_download_execution_observation"
                    and term in {*FIELDS, "integrity", "checksum", "content_length"}
                )
                excerpt = line.strip()
                if len(excerpt) > 240:
                    excerpt = excerpt[:240] + "..."
                representation = (
                    f"line:{line_number};sha256:{hashlib.sha256(line.encode()).hexdigest()};"
                    f"excerpt:{excerpt}"
                )
                admissible = authority in {
                    "primary_committed_contract",
                    "committed_runtime_contract",
                    "committed_design_evidence",
                }
                if authority == "source_attestation_hash":
                    note = "attests a source/artifact; never a trusted expected download checksum"
                elif kind == "synthetic_test_fixture":
                    note = "synthetic fixture; not a real provider/download observation"
                elif historical_real:
                    note = "historical execution/provider evidence; not an authorized ADMIT_013 observation or comparison authority"
                elif kind == "schema_or_committed_contract_representation":
                    note = "committed identity/structural/boundary evidence; not a current download observation"
                else:
                    note = "non-authoritative representation"
                rows.append(
                    {
                        "value_order": str(len(rows) + 1),
                        "semantic_subject": _semantic_subject(term),
                        "field_name": term,
                        "source_path": path_text,
                        "representation": representation,
                        "source_kind": kind,
                        "real_observed_value": str(historical_real).lower(),
                        "synthetic_example": str(kind == "synthetic_test_fixture").lower(),
                        "placeholder": str(kind == "placeholder").lower(),
                        "schema_only": str(kind in {"schema_or_committed_contract_representation", "schema_authority_absence"}).lower(),
                        "produced_by_download_execution": str(produced).lower(),
                        "trusted_comparison_authority": "false",
                        "admissible_as_admit_013_semantic_evidence": str(admissible).lower(),
                        "notes": note,
                    }
                )
    return rows


def _source_rows(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    return [
        {
            "source_order": str(index),
            "source_relative_path": source.path.as_posix(),
            "source_kind": _kind(source.path),
            "base_tree_mode": source.base_mode,
            "base_tree_sha256": source.sha256,
            "filesystem_sha256": source.sha256,
            "tracked_regular_non_symlink": "true",
            "parent_chain_verified": "true",
            "pinned_fd_read": "true",
            "triple_sha256_passed": "true",
            "source_boundary_passed": "true",
        }
        for index, source in enumerate(snapshot, 1)
    ]


NEW_ISSUES = (
    (
        "ADMIT_013_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED",
        "download_result_status|observed_http_status|observed_content_length_bytes|observed_sha256",
    ),
    (
        "ADMIT_013_ADMIT_012_VALIDATION_DEPENDENCY_UNRESOLVED",
        "download_result_status|observed_http_status|observed_content_length_bytes|observed_sha256",
    ),
    (
        "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED",
        "download_result_status|observed_http_status",
    ),
    (
        "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED",
        "observed_content_length_bytes|observed_sha256|expected_content_length_bytes|expected_sha256|integrity_verdict",
    ),
    (
        "ADMIT_013_MULTI_FAILURE_PRECEDENCE_UNRESOLVED",
        "download_result_status|observed_http_status|observed_content_length_bytes|observed_sha256",
    ),
    ("ADMIT_013_STANDALONE_SIGNATURE_UNRESOLVED", ""),
    ("ADMIT_013_RESULT_CONTRACT_UNRESOLVED", ""),
)


def _issue_rows(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    inherited = _rows(snapshot, RUNTIME_ISSUES)
    columns = tuple(inherited[0])
    for issue_id, fields in NEW_ISSUES:
        inherited.append(
            {
                column: {
                    "issue_id": issue_id,
                    "issue_type": "implementation_semantics_gap",
                    "affected_fields": fields,
                    "affected_rules": "ADMIT_013",
                    "severity": "blocking",
                    "status": "open",
                    "blocking_scope": "admission_evaluator_rule_logic",
                    "blocking_reason": issue_id,
                    "issue_origin": STAGE,
                    "integration_transition": "new_open",
                    "issue_count": "1",
                }.get(column, "")
                for column in columns
            }
        )
    return inherited


def _readiness() -> dict[str, bool]:
    return {
        "unified_dispatch_runtime_with_admit_001_to_012_implemented": True,
        "admit_012_registered_in_engine": True,
        "admit_013_preconditions_audited": True,
        "admit_013_rule_identity_complete": True,
        "admit_013_exact4_structural_contract_available": True,
        "admit_013_future_evaluator_pure_in_memory_possible": True,
        "ready_for_admit_013_download_outcome_and_integrity_contract_design": True,
        "feature_semantics_audit_required_before_training": True,
        "admit_013_routing_responsibility_resolved": False,
        "admit_013_admit_012_validation_dependency_resolved": False,
        "admit_013_download_outcome_policy_frozen": False,
        "admit_013_integrity_comparison_authority_resolved": False,
        "admit_013_multi_failure_precedence_resolved": False,
        "admit_013_reason_vocabulary_frozen": False,
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


def _payloads(snapshot: tuple[Source, ...]) -> dict[str, bytes]:
    _contracts(snapshot)
    preconditions = _preconditions()
    occurrences = _occurrences(snapshot)
    observed = _observed(snapshot)
    sources = _source_rows(snapshot)
    issues = _issue_rows(snapshot)
    payloads = {
        PRECONDITION: _csv_bytes(COLUMNS[PRECONDITION], preconditions),
        OCCURRENCE: _csv_bytes(COLUMNS[OCCURRENCE], occurrences),
        OBSERVED: _csv_bytes(COLUMNS[OBSERVED], observed),
        SOURCE_AUDIT: _csv_bytes(COLUMNS[SOURCE_AUDIT], sources),
        ISSUE: _csv_bytes(tuple(issues[0]), issues),
    }
    output_sha256 = {
        name: hashlib.sha256(content).hexdigest()
        for name, content in payloads.items()
    }
    readiness = _readiness()
    occurrence_counts = {
        authority: sum(
            row["source_authority_level"] == authority for row in occurrences
        )
        for authority in AUTHORITY_LEVELS
    }
    observed_kinds = sorted({row["source_kind"] for row in observed})
    complete_count = sum(
        row["completeness_status"] == "complete" for row in preconditions
    )
    manifest: dict[str, Any] = {
        "project": "CovaPIE",
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "base_subject": BASE_SUBJECT,
        "admission_rule_id": "ADMIT_013",
        "admission_rule_name": "download_failure_fail_closed",
        "evidence_source": "future_download_result",
        "required_status": "non_success_or_integrity_failure_not_admitted",
        "failure_severity": "blocking",
        "blocking_reason": "download_failure_must_fail_closed",
        "evaluation_phase": "post_download",
        "network_required": False,
        "raw_structure_required": False,
        "ready_for_future_implementation_registry_flag": True,
        "registry_flag_does_not_imply_semantics_complete": True,
        "exact4_fields": list(FIELDS),
        "exact4_policy_contexts": list(POLICY_CONTEXTS),
        "exact4_structural_contract_available": True,
        "admit_012_revalidation_or_prerequisite_boundary": "unresolved",
        "admit_013_routing_responsibility": "unresolved",
        "download_outcome_policy": "unresolved",
        "http_success_range_future_bounds": [200, 299],
        "http_success_range_adopted_by_admit_013": False,
        "zero_content_length_structurally_allowed": True,
        "zero_content_length_admit_013_disposition": "unresolved",
        "expected_content_length_authority_present": False,
        "content_length_comparison_contract_present": False,
        "trusted_expected_sha256_authority_present": False,
        "sha256_comparison_contract_present": False,
        "explicit_integrity_verdict_authority_present": False,
        "syntactic_sha_is_integrity_verdict": False,
        "source_or_artifact_sha_admissible_as_expected_download_sha": False,
        "provider_transport_failure_taxonomy_complete": False,
        "multi_failure_precedence_frozen": False,
        "reason_vocabulary_frozen": False,
        "standalone_signature_frozen": False,
        "formal_result_contract_frozen": False,
        "admit_012_exact10_direct_cross_rule_result_contract_available": False,
        "precondition_row_count": len(preconditions),
        "precondition_complete_count": complete_count,
        "precondition_incomplete_count": len(preconditions) - complete_count,
        "precondition_implementation_blocking_count": sum(
            row["implementation_blocking"] == "true" for row in preconditions
        ),
        "source_count": EXPECTED_SOURCE_COUNT,
        "source_path_list_sha256": EXPECTED_PATH_LIST_SHA256,
        "source_path_sha256_pairs_sha256": EXPECTED_PATH_SHA256_PAIRS_SHA256,
        "occurrence_row_count": len(occurrences),
        "occurrence_authority_counts": occurrence_counts,
        "observed_value_row_count": len(observed),
        "observed_value_source_kind_counts": {
            kind: sum(row["source_kind"] == kind for row in observed)
            for kind in observed_kinds
        },
        "authorized_admit_013_download_execution_count": 0,
        "real_download_result_observation_count": 0,
        "historical_real_download_or_provider_representation_count": sum(
            row["real_observed_value"] == "true" for row in observed
        ),
        "issue_row_count": len(issues),
        "inherited_issue_row_count": 16,
        "new_admit_013_issue_row_count": 7,
        "recommended_next_step": "design_covapie_admit_013_download_outcome_and_integrity_contract_v1",
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "future_evaluator_pure_in_memory": True,
        "renameat2_policy": "RENAME_NOREPLACE_required;_EINVAL_fails_closed_without_os.replace_fallback",
        "readiness": readiness,
        "safety": {
            "provider": False,
            "network": False,
            "real_download": False,
            "raw": False,
            "model_or_checkpoint": False,
            "dataloader": False,
            "runtime_change": False,
            "training": False,
            "stage_commit_push": False,
        },
        "output_sha256": output_sha256,
        "all_checks_passed": True,
    }
    manifest.update(readiness)
    payloads[MANIFEST] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return payloads


def _rename_noreplace(source: Path, destination: Path) -> None:
    if os.uname().machine not in {"x86_64", "amd64"}:
        raise ValueError("renameat2 syscall number unavailable")
    result = ctypes.CDLL(None, use_errno=True).syscall(
        316, -100, os.fsencode(source), -100, os.fsencode(destination), 1
    )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_staged_leaf(path: Path, data: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
        0o644,
    )
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(descriptor, view):]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_exact_output_set(root: Path, payloads: dict[str, bytes]) -> bool:
    item = os.lstat(root)
    if (
        stat.S_ISLNK(item.st_mode)
        or not stat.S_ISDIR(item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("unsafe output root")
    entries = {entry.name: entry for entry in root.iterdir()}
    if set(entries) != set(FILES):
        return False
    for name, expected in payloads.items():
        leaf = entries[name]
        before = os.lstat(leaf)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise ValueError("unsafe output leaf")
        descriptor = os.open(
            leaf,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
        try:
            expected_identity = _identity(before)
            if _identity(os.fstat(descriptor)) != expected_identity:
                raise ValueError("output leaf stat/open race")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            if _identity(os.fstat(descriptor)) != expected_identity:
                raise ValueError("output leaf FD identity drift after read")
        finally:
            os.close(descriptor)
        if _identity(os.lstat(leaf)) != expected_identity:
            raise ValueError("output leaf lexical replacement")
        if b"".join(chunks) != expected:
            return False
    return True


def _cleanup_owned_staging(staging: Path, owned: set[str]) -> None:
    if not staging.exists():
        return
    entries = {item.name: item for item in staging.iterdir()}
    if set(entries) - owned:
        return
    for name in owned:
        item = entries.get(name)
        if item is not None:
            leaf = os.lstat(item)
            if stat.S_ISREG(leaf.st_mode) and not stat.S_ISLNK(leaf.st_mode):
                item.unlink()
    try:
        staging.rmdir()
    except OSError:
        pass


def materialize_audit(output_root: Path | None = None) -> dict[str, Any]:
    root = REPO_ROOT / DEFAULT_OUTPUT_ROOT if output_root is None else Path(output_root)
    parent = root.parent
    parent_item = os.lstat(parent)
    if (
        (root.is_absolute() and parent.resolve(strict=True) != parent)
        or stat.S_ISLNK(parent_item.st_mode)
        or not stat.S_ISDIR(parent_item.st_mode)
    ):
        raise ValueError("unsafe output parent")
    root_exists = root.exists()
    snapshot = build_frozen_source_snapshot()
    payloads = _payloads(snapshot)
    if root_exists:
        if _read_exact_output_set(root, payloads):
            return json.loads(payloads[MANIFEST])
        raise ValueError("existing output set mismatch")
    staging = Path(
        tempfile.mkdtemp(prefix=f".{root.name}.", suffix=".staging", dir=parent)
    )
    owned = set(FILES)
    try:
        for name, data in payloads.items():
            _write_staged_leaf(staging / name, data)
        _fsync_directory(staging)
        _rename_noreplace(staging, root)
        _fsync_directory(parent)
        if not _read_exact_output_set(root, payloads):
            raise ValueError("published output postverify failed")
    except BaseException:
        _cleanup_owned_staging(staging, owned)
        raise
    return json.loads(payloads[MANIFEST])


def run_covapie_bulk_download_admission_admit_013_formal_evaluator_interface_preconditions_audit_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Explicitly materialize the read-only audit's Exact6 evidence set."""
    return materialize_audit(output_root)
