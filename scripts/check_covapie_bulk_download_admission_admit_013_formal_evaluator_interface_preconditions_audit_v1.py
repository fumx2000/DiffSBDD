#!/usr/bin/env python3
"""Independent checker for the ADMIT_013 precondition audit Exact6 set."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE = "5ff12d358a633c44c333022f7e0ebe30f039d6fc"
SUBJECT = "add CovaPIE unified dispatch runtime with ADMIT_001 to ADMIT_012 v1"
STAGE = "covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
FIELDS = (
    "download_result_status", "observed_http_status",
    "observed_content_length_bytes", "observed_sha256",
)
CONTEXTS = (
    "allowed_download_result_statuses", "successful_http_status_contract",
    "content_length_contract", "sha256_format_contract",
)
AUTHORITY_TERMS = (
    "expected_sha256", "expected_content_length_bytes", "download_integrity_passed",
    "checksum_verified", "content_length_verified", "provider_integrity_verdict",
    "trusted_download_manifest",
)
TERMS = (
    "ADMIT_013", "download_failure_fail_closed",
    "non_success_or_integrity_failure_not_admitted",
    "download_failure_must_fail_closed", *FIELDS,
    "successful_http_status_contract", "content_length_contract",
    "sha256_format_contract", "expected_sha256",
    "expected_content_length_bytes", "integrity", "checksum", "content_length",
)
FRAGMENTS = (
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate",
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate",
    "covapie_bulk_download_admission_admit_012_download_integrity_field_contract",
    "covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract",
    "covapie_bulk_download_admission_admit_012_rule_logic_interface",
    "covapie_bulk_download_admission_admit_012_unified_adapter_contract",
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012",
    "covapie_bulk_download_admission_admit_012_formal_evaluator_interface_preconditions_audit",
)
COUNT = 545
PATH_SHA = "d0cfd2b25097e62a23af6c89339b606d07ebb176c298e406f47c1981953bc105"
PAIR_SHA = "d81100221ae603ccc2e660a194d4f8da009e96c85130a1f29f3678163a696d2d"

DESIGN = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1")
PRE_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1")
FIELD_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1")
FORMAL_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1")
RUNTIME_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1")
RULE = DESIGN / "covapie_bulk_download_admission_rule_registry.csv"
SCHEMA = DESIGN / "covapie_bulk_download_admission_schema_contract.csv"
EXEC = PRE_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"
FIELD = PRE_ROOT / "covapie_bulk_download_admission_field_semantics_matrix.csv"
CTX = PRE_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"
FIELD_CONTRACT = FIELD_ROOT / "covapie_admit_012_download_integrity_field_contract.csv"
STATUS_ENUM = FIELD_ROOT / "covapie_admit_012_download_result_status_enum.csv"
FIELD_TRUTH = FIELD_ROOT / "covapie_admit_012_download_integrity_validation_truth_matrix.csv"
FORMAL_ROUTE = FORMAL_ROOT / "covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv"
RUNTIME_REGISTRY = RUNTIME_ROOT / "covapie_admit_001_to_012_registry_and_identity_audit.csv"
RUNTIME_ISSUES = RUNTIME_ROOT / "covapie_admit_001_to_012_runtime_issue_readiness_inventory.csv"
RUNTIME_MANIFEST = RUNTIME_ROOT / "covapie_admit_001_to_012_runtime_manifest.json"
RUNTIME_SOURCE = Path("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py")

FILES = (
    "covapie_admit_013_formal_evaluator_precondition_matrix.csv",
    "covapie_admit_013_field_occurrence_inventory.csv",
    "covapie_admit_013_observed_value_inventory.csv",
    "covapie_admit_013_source_boundary_audit.csv",
    "covapie_admit_013_issue_readiness_inventory.csv",
    "covapie_admit_013_formal_evaluator_preconditions_manifest.json",
)
PRE, OCC, OBS, SRC, ISSUE, MANIFEST = FILES
HEADERS = {
    PRE: (
        "precondition_order", "precondition_id", "precondition_group",
        "precondition_subject", "expected_contract", "observed_evidence",
        "completeness_status", "implementation_blocking", "blocking_reason",
        "precondition_passed",
    ),
    OCC: (
        "occurrence_order", "semantic_subject", "field_or_term_name",
        "relative_path", "file_role", "occurrence_kind",
        "declaring_or_referencing", "phase_claim", "type_claim",
        "validation_claim", "source_authority_level", "current_contract_effect",
        "admit_013_relevance", "occurrence_passed",
    ),
    OBS: (
        "value_order", "semantic_subject", "field_name", "source_path",
        "representation", "source_kind", "real_observed_value",
        "synthetic_example", "placeholder", "schema_only",
        "produced_by_download_execution", "trusted_comparison_authority",
        "admissible_as_admit_013_semantic_evidence", "notes",
    ),
    SRC: (
        "source_order", "source_relative_path", "source_kind", "base_tree_mode",
        "base_tree_sha256", "filesystem_sha256", "tracked_regular_non_symlink",
        "parent_chain_verified", "pinned_fd_read", "triple_sha256_passed",
        "source_boundary_passed",
    ),
}
AUTHORITY_LEVELS = (
    "primary_committed_contract", "committed_runtime_contract",
    "committed_design_evidence", "historical_or_reference", "test_fixture",
    "source_attestation_hash", "documentation_only", "unrelated_text",
)
PRIMARY = frozenset((RULE, SCHEMA, EXEC, FIELD, CTX, FIELD_CONTRACT, STATUS_ENUM, FIELD_TRUTH))
DESIGN_EVIDENCE = frozenset((
    FORMAL_ROUTE,
    FIELD_ROOT / "covapie_admit_012_download_integrity_field_contract_manifest.json",
    FORMAL_ROOT / "covapie_admit_012_formal_evaluator_interface_contract_manifest.json",
))
FROZEN_SHA = {
    PRE: "4b411c86cce23351d4aec3d58a894d161ab163e0305fdd91853bc54f16aa1fdf",
    OCC: "f692807cfaaf5d6ac7ba4416167d74401239eb2a012a95b4294fd911aead41f0",
    OBS: "6d200da869dd54b18347478168ca3b153083e26138e068e903c41729216aee8e",
    SRC: "ff49f781b087136ed28a1fcf60ed0af10bb23793aab767821c01ecc14db347aa",
    ISSUE: "204923bbf26c286c14ce4feaeb7934b279cafa54287ba96b4e2455fd84cf1198",
    MANIFEST: "63f0f96a960135117b0c4c8d3f80d1991cb8138e7df69d3917e921a6a4c74ce0",
}


def git(args: list[str], text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=text, check=False)


def csv_bytes(header: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def safe(path: Path) -> bool:
    return (
        not path.is_absolute() and bool(path.parts) and ".." not in path.parts
        and path.parts[:2] != ("data", "raw") and path.parts[0] != "checkpoints"
        and STAGE not in path.as_posix()
    )


def kind(path: Path) -> str:
    if path.suffix == ".py":
        return "python_source"
    if path.suffix == ".csv":
        return "committed_csv"
    if path.suffix == ".json":
        return "committed_manifest"
    return "tracked_text"


def paths() -> tuple[Path, ...]:
    command = ["grep", "-l", "-I"]
    for term in TERMS:
        command.extend(("-e", term))
    command.extend((BASE, "--", ":!data/raw/**", ":!checkpoints/**"))
    result = git(command)
    prefix = BASE + ":"
    assert result.returncode in (0, 1)
    assert all(line.startswith(prefix) for line in result.stdout.splitlines() if line)
    discovered = {Path(line.removeprefix(prefix)) for line in result.stdout.splitlines() if line}
    tree = git(["ls-tree", "-r", "--name-only", BASE])
    assert tree.returncode == 0
    required = {
        Path(line) for line in tree.stdout.splitlines()
        if any(fragment in line for fragment in FRAGMENTS)
    }
    result_paths = tuple(sorted(discovered | required, key=lambda path: path.as_posix()))
    assert len(result_paths) == COUNT and all(safe(path) for path in result_paths)
    digest = hashlib.sha256(json.dumps([path.as_posix() for path in result_paths], separators=(",", ":")).encode()).hexdigest()
    assert digest == PATH_SHA
    return result_paths


def identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode


def pinned(path: Path, expected: tuple[int, int, int]) -> bytes:
    absolute = REPO_ROOT / path
    assert identity(os.lstat(absolute)) == expected
    descriptor = os.open(absolute, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
    try:
        assert identity(os.fstat(descriptor)) == expected
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        assert identity(os.fstat(descriptor)) == expected
        assert identity(os.lstat(absolute)) == expected
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def snapshot() -> list[tuple[Path, bytes, str, str]]:
    root = os.lstat(REPO_ROOT)
    assert stat.S_ISDIR(root.st_mode) and not stat.S_ISLNK(root.st_mode)
    assert REPO_ROOT.resolve(strict=True) == REPO_ROOT
    subject = git(["show", "-s", "--format=%s", BASE])
    ancestor = git(["merge-base", "--is-ancestor", BASE, "HEAD"])
    assert subject.returncode == ancestor.returncode == 0 and subject.stdout.strip() == SUBJECT
    structures: list[tuple[Path, str, tuple[int, int, int]]] = []
    for path in paths():
        absolute = REPO_ROOT / path
        current = absolute.parent
        while current != REPO_ROOT:
            item = os.lstat(current)
            assert stat.S_ISDIR(item.st_mode) and not stat.S_ISLNK(item.st_mode)
            current = current.parent
        leaf = os.lstat(absolute)
        tree = git(["ls-tree", BASE, "--", path.as_posix()])
        tracked = git(["ls-files", "--error-unmatch", "--", path.as_posix()])
        head, separator, tree_path = tree.stdout.partition("\t")
        bits = head.split()
        assert tree.returncode == tracked.returncode == 0
        assert tracked.stdout.splitlines() == [path.as_posix()]
        assert separator and tree_path.strip() == path.as_posix()
        assert len(bits) == 3 and bits[0] in {"100644", "100755"} and bits[1] == "blob"
        assert stat.S_ISREG(leaf.st_mode) and not stat.S_ISLNK(leaf.st_mode)
        assert absolute.resolve(strict=True) == absolute
        structures.append((path, bits[0], identity(leaf)))
    output: list[tuple[Path, bytes, str, str]] = []
    pairs: list[list[str]] = []
    for path, mode, expected in structures:
        base = git(["show", f"{BASE}:{path.as_posix()}"], False)
        data = pinned(path, expected)
        digest = hashlib.sha256(data).hexdigest()
        assert base.returncode == 0 and hashlib.sha256(base.stdout).hexdigest() == digest
        pairs.append([path.as_posix(), digest])
        output.append((path, data, digest, mode))
    assert hashlib.sha256(json.dumps(pairs, separators=(",", ":")).encode()).hexdigest() == PAIR_SHA
    return output


def content(records: list[tuple[Path, bytes, str, str]], path: Path) -> bytes:
    return next(record[1] for record in records if record[0] == path)


def rows(records: list[tuple[Path, bytes, str, str]], path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(content(records, path).decode(), newline="")))


def contract_checks(records: list[tuple[Path, bytes, str, str]]) -> None:
    rule = next(row for row in rows(records, RULE) if row["admission_rule_id"] == "ADMIT_013")
    assert rule == {
        "admission_rule_id": "ADMIT_013", "admission_rule_name": "download_failure_fail_closed",
        "evidence_source": "future_download_result",
        "required_status": "non_success_or_integrity_failure_not_admitted",
        "failure_severity": "blocking", "blocking_reason": "download_failure_must_fail_closed",
        "evaluation_phase": "post_download", "network_required": "false",
        "raw_structure_required": "false", "ready_for_future_implementation": "true",
    }
    executable = next(row for row in rows(records, EXEC) if row["admission_rule_id"] == "ADMIT_013")
    assert executable["candidate_field_dependencies"].split("|") == list(FIELDS)
    assert executable["evaluation_context_dependencies"].split("|") == list(CONTEXTS)
    assert executable["batch_context_dependencies"] == ""
    assert executable["download_execution_result_required"] == "true"
    assert executable["pure_in_memory_interface_possible"] == "true"
    assert executable["semantics_complete"] == executable["deterministic_evaluation_possible_now"] == "false"
    assert executable["implementation_disposition"] == "interface_only_pending_semantics"
    fields = [row for row in rows(records, FIELD) if row["field_name"] in FIELDS]
    assert [row["field_name"] for row in fields] == list(FIELDS)
    assert all(row["candidate_record_field"] == "false" and row["producer_scope"] == "download_execution_result" and row["dependent_rules"] == "ADMIT_012|ADMIT_013" for row in fields)
    contexts = [row for row in rows(records, CTX) if row["context_item"] in CONTEXTS]
    assert [row["context_item"] for row in contexts] == list(CONTEXTS)
    assert all(row["required_by_rules"] == "ADMIT_012|ADMIT_013" and row["provided_by_future_caller"] == "true" and row["exact_contract_defined"] == "false" for row in contexts)
    exact4 = rows(records, FIELD_CONTRACT)
    assert [row["field_name"] for row in exact4] == list(FIELDS)
    assert [row["exact_builtin_type"] for row in exact4] == ["str", "int", "int", "str"]
    assert exact4[0]["ordered_allowed_values"] == "success|failure"
    assert (exact4[1]["legal_minimum"], exact4[1]["legal_maximum"], exact4[1]["future_success_minimum"], exact4[1]["future_success_maximum"]) == ("100", "599", "200", "299")
    assert exact4[2]["legal_minimum"] == "" and ">= 0" in exact4[2]["value_contract"]
    assert exact4[3]["value_contract"] == "exactly 64 ASCII lowercase hexadecimal characters [0-9a-f]{64}"
    assert all(row["subclasses_allowed"] == "false" and row["normalization_allowed"] == "false" and row["admit_012_executes_success_judgment"] == "false" for row in exact4)
    statuses = [row for row in rows(records, STATUS_ENUM) if row["row_kind"] == "canonical_enum"]
    assert [row["status_value"] for row in statuses] == ["success", "failure"]
    assert [row["future_admit_013_disposition"] for row in statuses] == ["pending_integrity_match_checks_not_implemented_here", "blocked_not_implemented_here"]
    truth = {row["case_id"]: row for row in rows(records, FIELD_TRUTH)}
    assert all(truth[name]["observed_contract_outcome"] == "contract_valid" for name in ("BOUNDARY_FAILURE_STATUS", "BOUNDARY_VALID_4XX", "BOUNDARY_VALID_5XX_FAILURE", "VALID_CONTENT_ZERO"))
    routes = [row for row in rows(records, FORMAL_ROUTE) if row["contract_kind"] == "route"]
    assert [row["formal_parameter"] for row in routes[:4]] == list(FIELDS)
    assert [row["formal_parameter"] for row in routes[4:8]] == list(CONTEXTS)
    assert not any("ADMIT_013" in "|".join(row.values()) for row in routes)
    registry = rows(records, RUNTIME_REGISTRY)
    assert {row["audit_item"] for row in registry if row["audit_item"].startswith("not_registered:")} == {"not_registered:ADMIT_013", "not_registered:ADMIT_014", "not_registered:ADMIT_015"}
    inherited = rows(records, RUNTIME_ISSUES)
    assert len(inherited) == 16
    coverage = next(row for row in inherited if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    aggregation = next(row for row in inherited if row["issue_id"] == "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED")
    assert coverage["affected_rules"] == "ADMIT_013|ADMIT_014|ADMIT_015" and coverage["status"] == aggregation["status"] == "open"
    manifest = json.loads(content(records, RUNTIME_MANIFEST))
    assert manifest["registered_rule_count"] == 12
    assert manifest["known_not_registered_rule_ids"] == ["ADMIT_013", "ADMIT_014", "ADMIT_015"]
    assert manifest["combined_candidate_verdict_implemented"] is manifest["cross_rule_aggregation_implemented"] is False
    source = content(records, RUNTIME_SOURCE).decode()
    assert "def evaluate_admit_013" not in source and "class Admit013EvaluationResult" not in source and "def _evaluate_registered_admit_013" not in source
    authoritative = "\n".join(content(records, path).decode() for path in (SCHEMA, EXEC, FIELD, CTX, FIELD_CONTRACT, FORMAL_ROUTE))
    assert not any(term in authoritative for term in AUTHORITY_TERMS)


def preconditions() -> list[dict[str, str]]:
    specs = (
        ("identity", "rule ID", "ADMIT_013", "Step14AT exact registry row", 1, ""),
        ("identity", "rule name", "download_failure_fail_closed", "Step14AT exact registry row", 1, ""),
        ("identity", "evaluation phase", "post_download", "Step14AT exact registry row", 1, ""),
        ("identity", "evidence source", "future_download_result", "Step14AT exact registry row", 1, ""),
        ("identity", "required status", "non_success_or_integrity_failure_not_admitted", "Step14AT exact registry row", 1, ""),
        ("identity", "blocking reason", "download_failure_must_fail_closed", "Step14AT exact registry row", 1, ""),
        ("structural", "Exact4 field identity/order", "download_result_status|observed_http_status|observed_content_length_bytes|observed_sha256", "shared ADMIT_012 field contract exact order", 1, ""),
        ("structural", "download_result_status structural contract", "exact built-in str; closed success|failure; no normalization", "ADMIT_012 shared structural contract", 1, ""),
        ("structural", "observed_http_status structural contract", "exact built-in int; bool/subclass rejected; 100..599", "ADMIT_012 shared structural contract", 1, ""),
        ("structural", "observed_content_length_bytes structural contract", "exact built-in int; >=0; zero allowed; no upper bound; no file recompute", "ADMIT_012 shared structural contract", 1, ""),
        ("structural", "observed_sha256 structural contract", "exact built-in str; ASCII lowercase [0-9a-f]{64}; no normalization or file recompute", "ADMIT_012 shared structural contract", 1, ""),
        ("structural", "existing Exact4 policy-context identity", "allowed statuses|HTTP contract|content contract|SHA format contract", "ADMIT_012 formal interface freezes these identities for ADMIT_012", 1, ""),
        ("routing", "post-download routing responsibility", "ADMIT_013 envelope sources and forbidden envelopes frozen", "only ADMIT_012 routing is frozen", 0, "ADMIT_013_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED"),
        ("dependency", "ADMIT_012 prerequisite/revalidation boundary", "self-validation versus prior formal ADMIT_012 result frozen", "single-rule runtime has no cross-rule prerequisite contract", 0, "ADMIT_013_ADMIT_012_VALIDATION_DEPENDENCY_UNRESOLVED"),
        ("dependency", "missing/presence behavior", "ADMIT_013 missing handling and precedence frozen", "ADMIT_012 presence semantics exist but ADMIT_013 adoption is absent", 0, "ADMIT_013_ADMIT_012_VALIDATION_DEPENDENCY_UNRESOLVED"),
        ("outcome", "canonical success-status decision", "success alone has a deterministic ADMIT_013 disposition", "only pending future integrity checks is stated", 0, "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("outcome", "canonical failure-status decision", "failure is blocked", "registry non-success fail-closed plus shared status row blocked_not_implemented_here", 1, ""),
        ("outcome", "HTTP success-range adoption", "ADMIT_013 explicitly adopts or rejects 200..299", "future bounds exist but no ADMIT_013 adoption contract", 0, "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("outcome", "status/HTTP contradiction behavior", "success+non-2xx and failure+2xx precedence frozen", "no committed ADMIT_013 contradiction table", 0, "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("integrity", "zero-content-length disposition", "zero allowed/blocked cases frozen", "zero is structurally legal; business disposition absent", 0, "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("integrity", "expected content-length authority", "trusted producer/context/type frozen", "no assigned authoritative field or context", 0, "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("integrity", "content-length comparison contract", "observed-versus-expected comparison/reason/precedence frozen", "no authoritative comparison contract", 0, "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("integrity", "expected SHA256 authority", "trusted producer/context/type frozen", "source/artifact hashes exist but no download authority", 0, "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("integrity", "SHA comparison contract", "observed-versus-expected comparison/reason/precedence frozen", "no authoritative comparison contract or verdict", 0, "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("integrity", "syntactic SHA versus integrity semantics", "valid grammar is not an integrity verdict", "ADMIT_012 explicitly limits SHA to representation grammar", 1, ""),
        ("outcome", "provider/transport failure taxonomy", "HTTP timeout DNS partial empty checksum provider write failures represented", "success|failure does not freeze category mapping or reasons", 0, "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("precedence", "multi-failure precedence", "missing invalid status HTTP length SHA conflicts ordered", "no committed ADMIT_013 precedence table", 0, "ADMIT_013_MULTI_FAILURE_PRECEDENCE_UNRESOLVED"),
        ("result", "closed reason vocabulary", "complete ADMIT_013 reason vocabulary frozen", "registry blocker is not a closed result-reason vocabulary", 0, "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("interface", "public standalone signature", "scalar/context/prior-result/Mapping choice frozen", "no ADMIT_013 standalone signature contract", 0, "ADMIT_013_STANDALONE_SIGNATURE_UNRESOLVED"),
        ("interface", "formal result contract", "representation/prefix/consumption/outcome/reason invariants frozen", "ADMIT_012 Exact10 is rule-specific; no ADMIT_013 result contract", 0, "ADMIT_013_RESULT_CONTRACT_UNRESOLVED"),
        ("boundary", "pure in-memory/no-I/O boundary", "future evaluator may be pure; no network/raw/filesystem", "Step14AT/AU-A exact false I/O requirements", 1, ""),
        ("authorization", "authorization/training boundary", "no provider/network/download/raw/runtime/training; feature audit required", "current task and committed readiness fail closed", 1, ""),
    )
    return [{
        "precondition_order": str(number), "precondition_id": f"PRE_{number:03d}",
        "precondition_group": group, "precondition_subject": subject,
        "expected_contract": expected, "observed_evidence": evidence,
        "completeness_status": "complete" if complete else "incomplete",
        "implementation_blocking": "false" if complete else "true",
        "blocking_reason": blocker, "precondition_passed": str(bool(complete)).lower(),
    } for number, (group, subject, expected, evidence, complete, blocker) in enumerate(specs, 1)]


def role(path: Path) -> str:
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


def semantic_subject(term: str) -> str:
    if term in {"ADMIT_013", "download_failure_fail_closed", "non_success_or_integrity_failure_not_admitted", "download_failure_must_fail_closed"}:
        return "rule_identity"
    if term in FIELDS:
        return "exact4_download_result_field"
    if term.endswith("_contract"):
        return "policy_context"
    if term.startswith("expected_"):
        return "comparison_authority"
    return "integrity_or_transport_semantics"


def authority(path: Path, term: str, line: str) -> str:
    value = path.as_posix()
    if value.startswith("tests/"):
        return "test_fixture"
    if term == "expected_sha256" and ("source_boundary" in path.name or path.suffix == ".json" or "source_input_verification" in line):
        return "source_attestation_hash"
    if value.startswith("docs/"):
        return "documentation_only"
    if path in PRIMARY:
        return "primary_committed_contract"
    if "unified_dispatch_runtime_with_admit_001_to_012" in value:
        return "committed_runtime_contract"
    if path in DESIGN_EVIDENCE or any(fragment in value for fragment in FRAGMENTS[:7]):
        return "committed_design_evidence"
    if "admit_012_formal_evaluator_interface_preconditions_audit" in value or "real_covalent_pilot_download" in value:
        return "historical_or_reference"
    return "unrelated_text"


def declaration(path: Path, term: str, line: str) -> bool:
    if path == RULE and line.startswith("ADMIT_013,"):
        return True
    if path == SCHEMA and line.startswith(f"{term},"):
        return True
    if path in {EXEC, FIELD, CTX} and (line.startswith("ADMIT_013,") or line.startswith(f"{term},")):
        return True
    if path == FIELD_CONTRACT and term in FIELDS and f",{term}," in line:
        return True
    return path == STATUS_ENUM and term == "integrity" and line.startswith(("1,", "2,"))


def occurrences(records: list[tuple[Path, bytes, str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    type_claims = {
        "download_result_status": "exact_builtin_str_no_subclasses",
        "observed_http_status": "exact_builtin_int_100_599_no_bool_or_subclasses",
        "observed_content_length_bytes": "exact_builtin_int_minimum_0_no_upper_bound",
        "observed_sha256": "exact_builtin_str_lowercase_hex64",
    }
    for path, data, _, _ in records:
        for line in data.decode().splitlines():
            for term in TERMS:
                if term not in line:
                    continue
                auth = authority(path, term, line)
                declares = declaration(path, term, line)
                if declares and path == RULE:
                    effect = "ADMIT_013_rule_identity_authority_only"
                elif declares and term in FIELDS:
                    effect = "shared_Exact4_identity_or_structural_authority"
                elif auth == "committed_runtime_contract":
                    effect = "Exact12_runtime_state_authority"
                elif auth in {"test_fixture", "documentation_only", "source_attestation_hash", "unrelated_text"}:
                    effect = "not_ADMIT_013_semantic_authority"
                else:
                    effect = "committed_boundary_or_reference_evidence"
                relevance = (
                    "shared_structural_contract_or_observed_value_reference" if term in FIELDS
                    else "candidate_comparison_authority_but_not_assigned_to_ADMIT_013" if term.startswith("expected_")
                    else "integrity_semantics_search_evidence" if term in {"integrity", "checksum", "content_length"}
                    else "ADMIT_013_identity_or_context_evidence"
                )
                output.append({
                    "occurrence_order": str(len(output) + 1),
                    "semantic_subject": semantic_subject(term), "field_or_term_name": term,
                    "relative_path": path.as_posix(), "file_role": role(path),
                    "occurrence_kind": "contract_declaration" if declares else "textual_or_structured_reference",
                    "declaring_or_referencing": "declaring" if declares else "referencing",
                    "phase_claim": "post_download" if "post_download" in line else "not_claimed",
                    "type_claim": type_claims.get(term, "not_claimed") if path == FIELD_CONTRACT else "not_claimed",
                    "validation_claim": "shared_structural_validation_only" if path == FIELD_CONTRACT else "rule_identity_not_truth_table" if path == RULE and declares else "no_direct_ADMIT_013_validation_claim",
                    "source_authority_level": auth, "current_contract_effect": effect,
                    "admit_013_relevance": relevance, "occurrence_passed": "true",
                })
    return output


def observed_kind(path: Path, auth: str, line: str) -> str:
    value = path.as_posix()
    if auth == "test_fixture":
        return "synthetic_test_fixture"
    if auth == "source_attestation_hash":
        return "source_or_artifact_attestation_hash"
    if value.startswith("docs/"):
        return "documentation_example"
    if "real_covalent_pilot_download_execution" in value or "real_covalent_pilot_download_integrity" in value:
        return "historical_real_download_execution_observation"
    if "real_provider" in value:
        return "historical_real_provider_observation"
    if auth in {"primary_committed_contract", "committed_design_evidence", "committed_runtime_contract"}:
        return "schema_or_committed_contract_representation"
    if "future" in line or "<MISSING>" in line or "placeholder" in line.lower():
        return "placeholder"
    if auth == "historical_or_reference":
        return "historical_or_reference"
    return "unrelated_numeric_or_status_value"


def observed(records: list[tuple[Path, bytes, str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for field_name in ("expected_content_length_bytes", "expected_sha256", "explicit_integrity_verdict"):
        output.append({
            "value_order": str(len(output) + 1), "semantic_subject": "comparison_authority_absence",
            "field_name": field_name, "source_path": "authoritative_schema_and_context_boundary",
            "representation": "<NO_ASSIGNED_ADMIT_013_AUTHORITY>", "source_kind": "schema_authority_absence",
            "real_observed_value": "false", "synthetic_example": "false", "placeholder": "false",
            "schema_only": "true", "produced_by_download_execution": "false",
            "trusted_comparison_authority": "false", "admissible_as_admit_013_semantic_evidence": "true",
            "notes": "negative authority finding; no producer/consumer/comparison contract",
        })
    for path, data, _, _ in records:
        for line_number, line in enumerate(data.decode().splitlines(), 1):
            for term in TERMS:
                if term not in line:
                    continue
                auth = authority(path, term, line)
                source_kind = observed_kind(path, auth, line)
                historical_real = source_kind in {"historical_real_download_execution_observation", "historical_real_provider_observation"}
                produced = source_kind == "historical_real_download_execution_observation" and term in {*FIELDS, "integrity", "checksum", "content_length"}
                excerpt = line.strip()
                if len(excerpt) > 240:
                    excerpt = excerpt[:240] + "..."
                representation = f"line:{line_number};sha256:{hashlib.sha256(line.encode()).hexdigest()};excerpt:{excerpt}"
                admissible = auth in {"primary_committed_contract", "committed_runtime_contract", "committed_design_evidence"}
                if auth == "source_attestation_hash":
                    note = "attests a source/artifact; never a trusted expected download checksum"
                elif source_kind == "synthetic_test_fixture":
                    note = "synthetic fixture; not a real provider/download observation"
                elif historical_real:
                    note = "historical execution/provider evidence; not an authorized ADMIT_013 observation or comparison authority"
                elif source_kind == "schema_or_committed_contract_representation":
                    note = "committed identity/structural/boundary evidence; not a current download observation"
                else:
                    note = "non-authoritative representation"
                output.append({
                    "value_order": str(len(output) + 1), "semantic_subject": semantic_subject(term),
                    "field_name": term, "source_path": path.as_posix(), "representation": representation,
                    "source_kind": source_kind, "real_observed_value": str(historical_real).lower(),
                    "synthetic_example": str(source_kind == "synthetic_test_fixture").lower(),
                    "placeholder": str(source_kind == "placeholder").lower(),
                    "schema_only": str(source_kind in {"schema_or_committed_contract_representation", "schema_authority_absence"}).lower(),
                    "produced_by_download_execution": str(produced).lower(), "trusted_comparison_authority": "false",
                    "admissible_as_admit_013_semantic_evidence": str(admissible).lower(), "notes": note,
                })
    return output


def source_rows(records: list[tuple[Path, bytes, str, str]]) -> list[dict[str, str]]:
    return [{
        "source_order": str(number), "source_relative_path": path.as_posix(),
        "source_kind": kind(path), "base_tree_mode": mode,
        "base_tree_sha256": digest, "filesystem_sha256": digest,
        "tracked_regular_non_symlink": "true", "parent_chain_verified": "true",
        "pinned_fd_read": "true", "triple_sha256_passed": "true",
        "source_boundary_passed": "true",
    } for number, (path, _, digest, mode) in enumerate(records, 1)]


NEW_ISSUES = (
    ("ADMIT_013_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED", "download_result_status|observed_http_status|observed_content_length_bytes|observed_sha256"),
    ("ADMIT_013_ADMIT_012_VALIDATION_DEPENDENCY_UNRESOLVED", "download_result_status|observed_http_status|observed_content_length_bytes|observed_sha256"),
    ("ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED", "download_result_status|observed_http_status"),
    ("ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED", "observed_content_length_bytes|observed_sha256|expected_content_length_bytes|expected_sha256|integrity_verdict"),
    ("ADMIT_013_MULTI_FAILURE_PRECEDENCE_UNRESOLVED", "download_result_status|observed_http_status|observed_content_length_bytes|observed_sha256"),
    ("ADMIT_013_STANDALONE_SIGNATURE_UNRESOLVED", ""),
    ("ADMIT_013_RESULT_CONTRACT_UNRESOLVED", ""),
)


def issues(records: list[tuple[Path, bytes, str, str]]) -> list[dict[str, str]]:
    output = rows(records, RUNTIME_ISSUES)
    header = tuple(output[0])
    for issue_id, affected_fields in NEW_ISSUES:
        output.append({column: {
            "issue_id": issue_id, "issue_type": "implementation_semantics_gap",
            "affected_fields": affected_fields, "affected_rules": "ADMIT_013",
            "severity": "blocking", "status": "open",
            "blocking_scope": "admission_evaluator_rule_logic", "blocking_reason": issue_id,
            "issue_origin": STAGE, "integration_transition": "new_open", "issue_count": "1",
        }.get(column, "") for column in header})
    return output


def readiness() -> dict[str, bool]:
    return {
        "unified_dispatch_runtime_with_admit_001_to_012_implemented": True,
        "admit_012_registered_in_engine": True, "admit_013_preconditions_audited": True,
        "admit_013_rule_identity_complete": True, "admit_013_exact4_structural_contract_available": True,
        "admit_013_future_evaluator_pure_in_memory_possible": True,
        "ready_for_admit_013_download_outcome_and_integrity_contract_design": True,
        "feature_semantics_audit_required_before_training": True,
        "admit_013_routing_responsibility_resolved": False,
        "admit_013_admit_012_validation_dependency_resolved": False,
        "admit_013_download_outcome_policy_frozen": False,
        "admit_013_integrity_comparison_authority_resolved": False,
        "admit_013_multi_failure_precedence_resolved": False,
        "admit_013_reason_vocabulary_frozen": False, "admit_013_standalone_signature_frozen": False,
        "admit_013_formal_result_contract_frozen": False,
        "ready_for_admit_013_standalone_evaluator_interface_implementation": False,
        "evaluate_admit_013_implemented": False, "Admit013EvaluationResult_implemented": False,
        "admit_013_unified_adapter_contract_frozen": False, "admit_013_unified_adapter_implemented": False,
        "admit_013_registered_in_engine": False,
        "unified_dispatch_runtime_with_admit_001_to_013_implemented": False,
        "provider_mapping_validated": False, "real_provider_evaluation_ready": False,
        "ready_for_bulk_download_now": False, "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False, "ready_for_training": False,
        "step12d_is_final_training_feature_contract": False,
    }


def expected(records: list[tuple[Path, bytes, str, str]]) -> dict[str, bytes]:
    contract_checks(records)
    pc = preconditions()
    occ = occurrences(records)
    obs = observed(records)
    src = source_rows(records)
    issue_rows = issues(records)
    payload = {
        PRE: csv_bytes(HEADERS[PRE], pc), OCC: csv_bytes(HEADERS[OCC], occ),
        OBS: csv_bytes(HEADERS[OBS], obs), SRC: csv_bytes(HEADERS[SRC], src),
        ISSUE: csv_bytes(tuple(issue_rows[0]), issue_rows),
    }
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()}
    ready = readiness()
    complete = sum(row["completeness_status"] == "complete" for row in pc)
    observed_kinds = sorted({row["source_kind"] for row in obs})
    manifest: dict[str, Any] = {
        "project": "CovaPIE", "stage": STAGE, "base_commit": BASE, "base_subject": SUBJECT,
        "admission_rule_id": "ADMIT_013", "admission_rule_name": "download_failure_fail_closed",
        "evidence_source": "future_download_result",
        "required_status": "non_success_or_integrity_failure_not_admitted",
        "failure_severity": "blocking", "blocking_reason": "download_failure_must_fail_closed",
        "evaluation_phase": "post_download", "network_required": False,
        "raw_structure_required": False, "ready_for_future_implementation_registry_flag": True,
        "registry_flag_does_not_imply_semantics_complete": True,
        "exact4_fields": list(FIELDS), "exact4_policy_contexts": list(CONTEXTS),
        "exact4_structural_contract_available": True,
        "admit_012_revalidation_or_prerequisite_boundary": "unresolved",
        "admit_013_routing_responsibility": "unresolved", "download_outcome_policy": "unresolved",
        "http_success_range_future_bounds": [200, 299], "http_success_range_adopted_by_admit_013": False,
        "zero_content_length_structurally_allowed": True,
        "zero_content_length_admit_013_disposition": "unresolved",
        "expected_content_length_authority_present": False,
        "content_length_comparison_contract_present": False,
        "trusted_expected_sha256_authority_present": False, "sha256_comparison_contract_present": False,
        "explicit_integrity_verdict_authority_present": False, "syntactic_sha_is_integrity_verdict": False,
        "source_or_artifact_sha_admissible_as_expected_download_sha": False,
        "provider_transport_failure_taxonomy_complete": False, "multi_failure_precedence_frozen": False,
        "reason_vocabulary_frozen": False, "standalone_signature_frozen": False,
        "formal_result_contract_frozen": False,
        "admit_012_exact10_direct_cross_rule_result_contract_available": False,
        "precondition_row_count": len(pc), "precondition_complete_count": complete,
        "precondition_incomplete_count": len(pc) - complete,
        "precondition_implementation_blocking_count": sum(row["implementation_blocking"] == "true" for row in pc),
        "source_count": COUNT, "source_path_list_sha256": PATH_SHA,
        "source_path_sha256_pairs_sha256": PAIR_SHA, "occurrence_row_count": len(occ),
        "occurrence_authority_counts": {key: sum(row["source_authority_level"] == key for row in occ) for key in AUTHORITY_LEVELS},
        "observed_value_row_count": len(obs),
        "observed_value_source_kind_counts": {key: sum(row["source_kind"] == key for row in obs) for key in observed_kinds},
        "authorized_admit_013_download_execution_count": 0, "real_download_result_observation_count": 0,
        "historical_real_download_or_provider_representation_count": sum(row["real_observed_value"] == "true" for row in obs),
        "issue_row_count": len(issue_rows), "inherited_issue_row_count": 16,
        "new_admit_013_issue_row_count": 7,
        "recommended_next_step": "design_covapie_admit_013_download_outcome_and_integrity_contract_v1",
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "future_evaluator_pure_in_memory": True,
        "renameat2_policy": "RENAME_NOREPLACE_required;_EINVAL_fails_closed_without_os.replace_fallback",
        "readiness": ready,
        "safety": {"provider": False, "network": False, "real_download": False, "raw": False,
                   "model_or_checkpoint": False, "dataloader": False, "runtime_change": False,
                   "training": False, "stage_commit_push": False},
        "output_sha256": hashes, "all_checks_passed": True,
    }
    manifest.update(ready)
    payload[MANIFEST] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return payload


def pinned_outputs(root: Path) -> dict[str, bytes]:
    parent_identity = identity(os.lstat(root.parent))
    root_identity = identity(os.lstat(root))
    assert root.is_dir() and not root.is_symlink() and {path.name for path in root.iterdir()} == set(FILES)
    root_fd = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
    try:
        assert identity(os.fstat(root_fd)) == root_identity
        result: dict[str, bytes] = {}
        frozen: dict[str, tuple[int, int, int]] = {}
        for name in FILES:
            leaf = os.lstat(root / name)
            assert stat.S_ISREG(leaf.st_mode) and not stat.S_ISLNK(leaf.st_mode)
            leaf_identity = identity(leaf)
            frozen[name] = leaf_identity
            descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0), dir_fd=root_fd)
            try:
                assert identity(os.fstat(descriptor)) == leaf_identity
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                assert identity(os.fstat(descriptor)) == leaf_identity
                result[name] = b"".join(chunks)
            finally:
                os.close(descriptor)
        assert identity(os.lstat(root.parent)) == parent_identity
        assert identity(os.fstat(root_fd)) == root_identity and identity(os.lstat(root)) == root_identity
        assert {path.name for path in root.iterdir()} == set(FILES)
        assert all(identity(os.lstat(root / name)) == frozen[name] for name in FILES)
        return result
    finally:
        os.close(root_fd)


def validate(root: Path = REPO_ROOT / OUTPUT_ROOT, enforce_frozen_hashes: bool = True) -> None:
    # Source attestation and independent contract reconstruction precede output reads.
    records = snapshot()
    wanted = expected(records)
    actual = pinned_outputs(root)
    assert actual == wanted
    if enforce_frozen_hashes:
        assert {name: hashlib.sha256(actual[name]).hexdigest() for name in FILES} == FROZEN_SHA


def main() -> None:
    validate()
    print(json.dumps({"stage": STAGE, "status": "passed", "output_sha256": FROZEN_SHA}, sort_keys=True))


if __name__ == "__main__":
    main()
