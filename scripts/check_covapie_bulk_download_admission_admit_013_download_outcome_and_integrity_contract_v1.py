#!/usr/bin/env python3
"""Independent checker for the ADMIT_013 outcome/integrity Exact6 design set."""
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
BASE_COMMIT = "30c644de3973ba2968ecaa8ebff97159c07678b9"
BASE_PARENT = "5ff12d358a633c44c333022f7e0ebe30f039d6fc"
BASE_SUBJECT = "add CovaPIE ADMIT_013 formal evaluator preconditions audit v1"
STAGE = "covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

FIELDS = (
    "download_result_status", "observed_http_status",
    "observed_content_length_bytes", "observed_sha256",
)
AUTHORITIES = (
    "expected_content_length_bytes", "expected_sha256", "explicit_integrity_verdict",
)
REASONS = (
    "", "DOWNLOAD_RESULT_STATUS_FAILURE", "OBSERVED_HTTP_STATUS_NOT_SUCCESS",
    "OBSERVED_CONTENT_EMPTY", "OBSERVED_SHA256_MISMATCH",
    "EXPLICIT_INTEGRITY_VERDICT_FAILED", "OBSERVED_CONTENT_LENGTH_MISMATCH",
    "INTEGRITY_AUTHORITY_MISSING",
)
FAILURES = REASONS[1:]
PSEUDO = (
    "candidate_self_report", "test_fixture", "artifact_sha256", "checker_sha256",
    "git_sha256", "source_boundary_sha256",
    "post_download_self_generated_observed_sha256", "historical_pilot_download_value",
)

FILES = (
    "covapie_admit_013_download_outcome_policy_contract.csv",
    "covapie_admit_013_integrity_authority_contract.csv",
    "covapie_admit_013_failure_taxonomy_and_precedence.csv",
    "covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv",
    "covapie_admit_013_issue_readiness_inventory.csv",
    "covapie_admit_013_download_outcome_and_integrity_contract_manifest.json",
)
OUTCOME, AUTHORITY, FAILURE, TRUTH, ISSUE, MANIFEST = FILES
HEADERS = {
    OUTCOME: (
        "policy_order", "policy_id", "policy_area", "subject", "source_envelope",
        "contract", "disposition", "precedence_or_continuation",
        "forbidden_behavior", "contract_passed",
    ),
    AUTHORITY: (
        "authority_order", "authority_name", "source_envelope", "presence_required",
        "missing_behavior", "exact_builtin_type", "subclasses_allowed",
        "allowed_values_or_grammar", "minimum_value", "normalization_allowed",
        "trusted_producers", "sufficient_when", "comparison_semantics",
        "forbidden_pseudo_authorities", "evaluator_io_allowed", "contract_passed",
    ),
    FAILURE: (
        "precedence_rank", "outcome", "reason", "layer", "unique_trigger_condition",
        "requires_structural_validation", "blocks_candidate", "reason_empty",
        "catch_all_allowed", "contract_passed",
    ),
    TRUTH: (
        "case_order", "case_id", "case_group", "download_result_status",
        "observed_http_status", "observed_content_length_bytes", "observed_sha256",
        "expected_content_length_bytes", "expected_sha256", "explicit_integrity_verdict",
        "active_failure_reasons", "expected_outcome", "expected_reason",
        "expected_precedence_rank", "strong_authority_present", "case_passed",
    ),
    ISSUE: (
        "inherited_order", "issue_id", "issue_type", "affected_fields", "affected_rules",
        "severity", "status", "blocking_scope", "blocking_reason", "issue_origin",
        "integration_transition", "issue_count", "effective_status", "transition_stage",
        "transition_action", "transition_evidence",
    ),
}

SOURCE_BOUNDARY = (
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv", "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv", "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv", "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv", "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv", "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract.csv", "03aef0a14257d9a2c028fcc3dd84c161c29b09bca1a1c71456edc66e2e73c9ce"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_result_status_enum.csv", "4c016e8c325ce6a422dff618ae166ec4f42243cc0d1fbf8f6a722c13f63139f6"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract_manifest.json", "9fadff44ae15474783df2a3997c45f2c4d57a41ca2adbab0b40f1d890f51039f"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_and_result_contract.csv", "682192b492979d9b6114381cbfc02d57c349e3cd8db2541a01177235d34c04e6"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv", "44709c3a679368476c87bcd97dafa2f9cf9bddb4af534c6eb950c565d0919aec"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_contract_manifest.json", "2845c2623a01087af8842177f4502402d0a8875a77ce12c6a49e2f77c60dae01"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_contract.csv", "c5c383e9a9e17c5eb5a4b2c92455da89a78e66f75df7ff31ce0494f08281433e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_manifest.json", "ad131895c0acfdaf5b350105031647bdcac9667370fb6cd43baf8826bea995c8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract.csv", "12228051428134223dc4db4ec418ced573637047189056f1fb8df908ca2fe6c8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract_manifest.json", "1df0e2a09817b7763ec4eb767663db169d3239385094da151af28150c2c55d25"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py", "4d9a49806d4ef71a95c8ad032dfa061f7473b1cb55a573459c155f0cd5d57282"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_registry_and_identity_audit.csv", "57ed1f04df27c7b30ec4cea97aead99e7788a2968f77245280850ae26f399e59"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_issue_readiness_inventory.csv", "6b6a543dd9fcce9a4b4451a05eae296a482093bba0bdb33bb37247bca4d17cfb"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_manifest.json", "bc909aefd86b62139fbb62025d9c323988a4c232ab9c960efb291fb0c196cee3"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_formal_evaluator_precondition_matrix.csv", "4b411c86cce23351d4aec3d58a894d161ab163e0305fdd91853bc54f16aa1fdf"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_issue_readiness_inventory.csv", "204923bbf26c286c14ce4feaeb7934b279cafa54287ba96b4e2455fd84cf1198"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_formal_evaluator_preconditions_manifest.json", "63f0f96a960135117b0c4c8d3f80d1991cb8138e7df69d3917e921a6a4c74ce0"),
)
PATH_SHA = hashlib.sha256(json.dumps([path for path, _ in SOURCE_BOUNDARY], separators=(",", ":")).encode()).hexdigest()
PAIR_SHA = hashlib.sha256(json.dumps([list(pair) for pair in SOURCE_BOUNDARY], separators=(",", ":")).encode()).hexdigest()

# Filled from the independently reconstructed canonical set; the manifest never hashes itself.
FROZEN_SHA256 = {
    OUTCOME: "2b64ce56c122ede2ea125944c164243e5bb7dc3da89c50607f29dd647208b43a",
    AUTHORITY: "d95035d109a2c62646f11c822b50b18ab2e25ded1bfebd13e82a37b9723fa0e1",
    FAILURE: "42bead68915f7260aa2c48dabfe2968623de85a039a20a3b78682af246469031",
    TRUTH: "7e856eb5ebd995793dcd82fb75266c7ee6f6a8b06b7785f3a70713a96b8efdbb",
    ISSUE: "240012c88668a3228139052d3920d02b839329fdda41280d31b5382b9de3620c",
    MANIFEST: "1bbfe88f459946b78bb14e5b0b672582d508a838bef220ecf292fa84d15f934d",
}


def _git(arguments: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=text, check=False)


def _identity(value: os.stat_result) -> tuple[int, int, int]:
    return value.st_dev, value.st_ino, value.st_mode


def _pinned(path: Path, expected: tuple[int, int, int]) -> bytes:
    if _identity(os.lstat(path)) != expected:
        raise AssertionError("source identity changed before open")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
    try:
        assert _identity(os.fstat(descriptor)) == expected
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        assert _identity(os.fstat(descriptor)) == expected
        assert _identity(os.lstat(path)) == expected
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _assert_base_lineage() -> None:
    identity = _git(["show", "-s", "--format=%H%n%P%n%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    assert identity.returncode == ancestor.returncode == 0
    assert identity.stdout.splitlines() == [BASE_COMMIT, BASE_PARENT, BASE_SUBJECT]


def source_snapshot() -> tuple[tuple[str, bytes, str, str], ...]:
    # Lineage and all sources are verified before any output byte is read.
    _assert_base_lineage()
    structures = []
    for relative, digest in SOURCE_BOUNDARY:
        path = Path(relative)
        assert not path.is_absolute() and ".." not in path.parts
        assert path.parts[:2] != ("data", "raw") and path.parts[0] != "checkpoints"
        absolute = REPO_ROOT / path
        current = absolute.parent
        while current != REPO_ROOT:
            item = os.lstat(current)
            assert stat.S_ISDIR(item.st_mode) and not stat.S_ISLNK(item.st_mode)
            current = current.parent
        item = os.lstat(absolute)
        tree = _git(["ls-tree", BASE_COMMIT, "--", relative])
        tracked = _git(["ls-files", "--error-unmatch", "--", relative])
        prefix, separator, tree_path = tree.stdout.partition("\t")
        fields = prefix.split()
        assert tree.returncode == tracked.returncode == 0
        assert tracked.stdout.splitlines() == [relative]
        assert separator and tree_path.strip() == relative
        assert len(fields) == 3 and fields[0] in {"100644", "100755"} and fields[1] == "blob"
        assert stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode)
        structures.append((relative, digest, fields[0], _identity(item)))
    records = []
    for relative, digest, mode, frozen_identity in structures:
        data = _pinned(REPO_ROOT / relative, frozen_identity)
        base = _git(["show", f"{BASE_COMMIT}:{relative}"], text=False)
        assert base.returncode == 0 and isinstance(base.stdout, bytes)
        assert hashlib.sha256(data).hexdigest() == hashlib.sha256(base.stdout).hexdigest() == digest
        records.append((relative, data, digest, mode))
    return tuple(records)


def _source(records: tuple[tuple[str, bytes, str, str], ...], suffix: str) -> bytes:
    return next(data for path, data, _, _ in records if path.endswith(suffix))


def _source_rows(records: tuple[tuple[str, bytes, str, str], ...], suffix: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(_source(records, suffix).decode(), newline="")))


def _csv_bytes(header: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def expected_outcome_rows() -> list[dict[str, str]]:
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
        "policy_order": str(index), "policy_id": row[0], "policy_area": row[1],
        "subject": row[2], "source_envelope": row[3], "contract": row[4],
        "disposition": row[5], "precedence_or_continuation": row[6],
        "forbidden_behavior": row[7], "contract_passed": "true",
    } for index, row in enumerate(specs, 1)]


def expected_authority_rows() -> list[dict[str, str]]:
    specs = (
        ("expected_content_length_bytes", "absence allowed; cannot satisfy strong-authority requirement", "int", "", "0", "trusted provider or HTTP metadata path", "never sufficient alone; corroborating comparison only", "if present must exactly equal observed_content_length_bytes"),
        ("expected_sha256", "absence allowed if explicit_integrity_verdict is verified", "str", "ASCII lowercase [0-9a-f]{64}", "", "trusted provider manifest|trusted pre-download catalog|separately approved equivalent authority", "sufficient strong authority only when exactly equal to observed_sha256", "if present mismatch blocks; exact equality contributes strong authority"),
        ("explicit_integrity_verdict", "absence allowed if expected_sha256 is present and matches", "str", "verified|failed", "", "future designated integrity verifier", "verified is sufficient strong authority; failed always blocks", "failed blocks; verified contributes strong authority but cannot override any mismatch"),
    )
    forbidden = "|".join(PSEUDO)
    return [{
        "authority_order": str(index), "authority_name": row[0],
        "source_envelope": "evaluation_context", "presence_required": "false",
        "missing_behavior": row[1], "exact_builtin_type": row[2],
        "subclasses_allowed": "false", "allowed_values_or_grammar": row[3],
        "minimum_value": row[4], "normalization_allowed": "false",
        "trusted_producers": row[5], "sufficient_when": row[6],
        "comparison_semantics": row[7], "forbidden_pseudo_authorities": forbidden,
        "evaluator_io_allowed": "false", "contract_passed": "true",
    } for index, row in enumerate(specs, 1)]


def expected_failure_rows() -> list[dict[str, str]]:
    triggers = (
        "download_result_status is exact canonical failure",
        "status is success and observed_http_status is outside inclusive 200..299",
        "status is success and HTTP is 2xx and observed_content_length_bytes equals 0",
        "earlier reasons absent and expected_sha256 is present but differs from observed_sha256",
        "earlier reasons absent and explicit_integrity_verdict equals failed",
        "earlier reasons absent and expected_content_length_bytes is present but differs from observed_content_length_bytes",
        "earlier reasons absent and neither exact expected SHA match nor explicit verified is present",
    )
    rows = [{
        "precedence_rank": str(index), "outcome": "blocked", "reason": reason,
        "layer": "business_outcome", "unique_trigger_condition": trigger,
        "requires_structural_validation": "true", "blocks_candidate": "true",
        "reason_empty": "false", "catch_all_allowed": "false", "contract_passed": "true",
    } for index, (reason, trigger) in enumerate(zip(FAILURES, triggers, strict=True), 1)]
    rows.append({
        "precedence_rank": "8", "outcome": "passed", "reason": "", "layer": "terminal_pass",
        "unique_trigger_condition": "no rank 1..7 failure after structural validation",
        "requires_structural_validation": "true", "blocks_candidate": "false",
        "reason_empty": "true", "catch_all_allowed": "false", "contract_passed": "true",
    })
    return rows


SHA_A = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
SHA_B = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
MISSING = "<MISSING>"
TRUTH_CASES = (
    ("PASS_SHA_MATCH", "pass", "success", "200", "10", SHA_A, "10", SHA_A, MISSING),
    ("PASS_EXPLICIT_VERIFIED", "pass", "success", "299", "10", SHA_A, MISSING, MISSING, "verified"),
    ("PASS_ALL_AUTHORITIES", "pass", "success", "204", "10", SHA_A, "10", SHA_A, "verified"),
    ("FAILURE_WITH_2XX", "status", "failure", "200", "10", SHA_A, "10", SHA_A, "verified"),
    ("FAILURE_WITH_404", "status", "failure", "404", "10", SHA_A, "10", SHA_B, "failed"),
    ("SUCCESS_WITH_404", "http", "success", "404", "10", SHA_A, "10", SHA_A, "verified"),
    ("ZERO_CONTENT", "content", "success", "200", "0", SHA_A, MISSING, SHA_A, MISSING),
    ("SHA_MISMATCH", "integrity", "success", "200", "10", SHA_A, MISSING, SHA_B, MISSING),
    ("EXPLICIT_FAILED", "integrity", "success", "200", "10", SHA_A, MISSING, MISSING, "failed"),
    ("LENGTH_MISMATCH_WITH_SHA_MATCH", "integrity", "success", "200", "10", SHA_A, "11", SHA_A, MISSING),
    ("ONLY_LENGTH_MATCH", "authority", "success", "200", "10", SHA_A, "10", MISSING, MISSING),
    ("NO_STRONG_AUTHORITY", "authority", "success", "200", "10", SHA_A, MISSING, MISSING, MISSING),
    ("SHA_MATCH_AND_EXPLICIT_FAILED", "precedence", "success", "200", "10", SHA_A, MISSING, SHA_A, "failed"),
    ("SHA_MISMATCH_AND_EXPLICIT_VERIFIED", "precedence", "success", "200", "10", SHA_A, MISSING, SHA_B, "verified"),
    ("ZERO_ALL_AUTHORITIES_APPEAR_PASS", "precedence", "success", "200", "0", SHA_A, "0", SHA_A, "verified"),
    ("STATUS_FAILURE_AND_SHA_MISMATCH", "precedence", "failure", "200", "10", SHA_A, MISSING, SHA_B, MISSING),
    ("NON2XX_ZERO_INTEGRITY_FAILURE", "triple_failure", "success", "500", "0", SHA_A, "1", SHA_B, "failed"),
    ("ADJACENT_STATUS_HTTP", "adjacent_precedence", "failure", "404", "10", SHA_A, MISSING, SHA_A, MISSING),
    ("ADJACENT_HTTP_EMPTY", "adjacent_precedence", "success", "404", "0", SHA_A, MISSING, SHA_A, MISSING),
    ("ADJACENT_EMPTY_SHA", "adjacent_precedence", "success", "200", "0", SHA_A, MISSING, SHA_B, MISSING),
    ("ADJACENT_SHA_VERDICT", "adjacent_precedence", "success", "200", "10", SHA_A, MISSING, SHA_B, "failed"),
    ("ADJACENT_VERDICT_LENGTH", "adjacent_precedence", "success", "200", "10", SHA_A, "11", MISSING, "failed"),
    ("ADJACENT_LENGTH_AUTHORITY", "adjacent_precedence", "success", "200", "10", SHA_A, "11", MISSING, MISSING),
)


def _business(row: tuple[str, ...]) -> tuple[list[str], str, str, int, bool]:
    _, _, status_value, http_text, length_text, observed_sha, expected_length, expected_sha, verdict = row
    active = []
    if status_value == "failure":
        active.append(FAILURES[0])
    if not 200 <= int(http_text) <= 299:
        active.append(FAILURES[1])
    if int(length_text) == 0:
        active.append(FAILURES[2])
    if expected_sha != MISSING and expected_sha != observed_sha:
        active.append(FAILURES[3])
    if verdict == "failed":
        active.append(FAILURES[4])
    if expected_length != MISSING and int(expected_length) != int(length_text):
        active.append(FAILURES[5])
    strong = (expected_sha != MISSING and expected_sha == observed_sha) or verdict == "verified"
    if not strong:
        active.append(FAILURES[6])
    if active:
        reason = min(active, key=FAILURES.index)
        return active, "blocked", reason, FAILURES.index(reason) + 1, strong
    return active, "passed", "", 8, strong


def expected_truth_rows() -> list[dict[str, str]]:
    rows = []
    for order, case in enumerate(TRUTH_CASES, 1):
        active, outcome, reason, rank, strong = _business(case)
        rows.append({
            "case_order": str(order), "case_id": case[0], "case_group": case[1],
            "download_result_status": case[2], "observed_http_status": case[3],
            "observed_content_length_bytes": case[4], "observed_sha256": case[5],
            "expected_content_length_bytes": case[6], "expected_sha256": case[7],
            "explicit_integrity_verdict": case[8], "active_failure_reasons": "|".join(active),
            "expected_outcome": outcome, "expected_reason": reason,
            "expected_precedence_rank": str(rank), "strong_authority_present": str(strong).lower(),
            "case_passed": "true",
        })
    return rows


TRANSITIONS = {
    "ADMIT_013_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED": "download and evaluation envelopes frozen; candidate/batch/stage/fallback forbidden",
    "ADMIT_013_ADMIT_012_VALIDATION_DEPENDENCY_UNRESOLVED": "pipeline prerequisite distinguished from self-validation and direct result consumption",
    "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED": "status HTTP zero-content strong-authority and pass conjunction frozen",
    "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED": "Exact3 trusted authority types producers and comparisons frozen",
    "ADMIT_013_MULTI_FAILURE_PRECEDENCE_UNRESOLVED": "closed Exact7 business failure precedence frozen",
}


def expected_issue_rows(records: tuple[tuple[str, bytes, str, str], ...]) -> list[dict[str, str]]:
    inherited = _source_rows(records, "covapie_admit_013_issue_readiness_inventory.csv")
    rows = []
    for order, row in enumerate(inherited, 1):
        evidence = TRANSITIONS.get(row["issue_id"])
        rows.append({
            "inherited_order": str(order), **row,
            "effective_status": "resolved" if evidence else row["status"],
            "transition_stage": STAGE if evidence else "",
            "transition_action": "resolved_by_successor_contract_design" if evidence else "unchanged",
            "transition_evidence": evidence or "inherited identity and status retained",
        })
    return rows


def readiness() -> dict[str, bool]:
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


def expected(records: tuple[tuple[str, bytes, str, str], ...]) -> dict[str, bytes]:
    outcome = expected_outcome_rows()
    authority = expected_authority_rows()
    failure = expected_failure_rows()
    truth = expected_truth_rows()
    issues = expected_issue_rows(records)
    payloads = {
        OUTCOME: _csv_bytes(HEADERS[OUTCOME], outcome),
        AUTHORITY: _csv_bytes(HEADERS[AUTHORITY], authority),
        FAILURE: _csv_bytes(HEADERS[FAILURE], failure),
        TRUTH: _csv_bytes(HEADERS[TRUTH], truth),
        ISSUE: _csv_bytes(HEADERS[ISSUE], issues),
    }
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}
    ready = readiness()
    source_boundary = [
        {"path": path, "sha256": digest, "base_tree_mode": mode}
        for path, _, digest, mode in records
    ]
    manifest: dict[str, Any] = {
        "project": "CovaPIE", "stage": STAGE,
        "manifest_schema_version": "covapie_admit_013_download_outcome_and_integrity_contract_manifest_v1",
        "base_commit": BASE_COMMIT, "base_parent": BASE_PARENT, "base_subject": BASE_SUBJECT,
        "admission_rule_id": "ADMIT_013", "admission_rule_name": "download_failure_fail_closed",
        "evidence_source": "future_download_result",
        "required_status": "non_success_or_integrity_failure_not_admitted",
        "failure_severity": "blocking", "blocking_reason": "download_failure_must_fail_closed",
        "evaluation_phase": "post_download", "exact4_fields": list(FIELDS),
        "integrity_authority_fields": list(AUTHORITIES), "http_success_range": [200, 299],
        "zero_content_length_structurally_allowed": True, "zero_content_length_admitted": False,
        "outcome_vocabulary": ["passed", "blocked"], "reason_vocabulary": list(REASONS),
        "business_failure_precedence": list(FAILURES),
        "structural_validation_precedes_business_outcome": True,
        "admit_012_dependency_boundary": {
            "pipeline_level_prerequisite_allowed": True,
            "standalone_evaluator_self_validation_required": True,
            "direct_cross_rule_result_consumption_allowed": False,
            "Admit012EvaluationResult_consumed": False,
        },
        "routing_contract": {
            "download_result_context": list(FIELDS), "evaluation_context": list(AUTHORITIES),
            "forbidden_envelopes": ["candidate_record", "batch_context", "stage_authorization_context", "fallback_envelope"],
            "normalization_inference_file_network_recompute_allowed": False,
        },
        "pass_conditions": [
            "download_result_status == success", "200 <= observed_http_status <= 299",
            "observed_content_length_bytes > 0", "all provided trusted authorities agree",
            "expected SHA exact match or explicit verified",
        ],
        "insufficient_pass_conditions": [
            "status success alone", "HTTP 2xx alone", "content length > 0 alone",
            "valid SHA grammar alone", "expected content length match alone",
            "nonzero content plus valid SHA grammar",
        ],
        "forbidden_pseudo_authorities": list(PSEUDO),
        "row_counts": {
            "outcome_policy": 16, "integrity_authority": 3, "failure_taxonomy": 8,
            "truth_matrix": 23, "issue_inventory": 23,
        },
        "truth_matrix_group_counts": {
            group: sum(row["case_group"] == group for row in truth)
            for group in sorted({row["case_group"] for row in truth})
        },
        "issue_transition_counts": {
            "inherited": 23, "resolved_by_this_stage": 5,
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
        "source_count": 22, "source_path_list_sha256": PATH_SHA,
        "source_path_sha256_pairs_sha256": PAIR_SHA, "source_boundary": source_boundary,
        "output_file_count": 6, "output_files": list(FILES), "output_sha256": hashes,
        "recommended_next_step": "design_covapie_admit_013_formal_evaluator_interface_contract_v1",
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "renameat2_policy": "RENAME_NOREPLACE_required;_EINVAL_fails_closed_without_os.replace_fallback",
        "readiness": ready,
        "safety": {
            "provider": False, "network": False, "download": False, "raw": False,
            "model_or_checkpoint": False, "dataloader": False, "runtime_change": False,
            "training": False, "stage_commit_push": False,
        },
        "all_checks_passed": True,
    }
    payloads[MANIFEST] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return payloads


def _read_output_at(
    root_fd: int, name: str, expected_identity: tuple[int, int, int]
) -> bytes:
    assert _identity(os.lstat(name, dir_fd=root_fd)) == expected_identity
    descriptor = os.open(
        name,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        dir_fd=root_fd,
    )
    try:
        assert _identity(os.fstat(descriptor)) == expected_identity
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        assert _identity(os.fstat(descriptor)) == expected_identity
        assert _identity(os.lstat(name, dir_fd=root_fd)) == expected_identity
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _read_outputs(root: Path) -> dict[str, bytes]:
    parent_identity = _identity(os.lstat(root.parent))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    assert stat.S_ISDIR(root_item.st_mode) and not stat.S_ISLNK(root_item.st_mode)
    assert root.resolve(strict=True) == root
    root_fd = os.open(
        root,
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        assert _identity(os.fstat(root_fd)) == root_identity
        assert set(os.listdir(root_fd)) == set(FILES)
        frozen = {}
        for name in FILES:
            item = os.lstat(name, dir_fd=root_fd)
            assert stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode)
            frozen[name] = _identity(item)
        output = {
            name: _read_output_at(root_fd, name, frozen[name]) for name in FILES
        }
        assert _identity(os.lstat(root.parent)) == parent_identity
        assert _identity(os.fstat(root_fd)) == root_identity
        assert _identity(os.lstat(root)) == root_identity
        assert set(os.listdir(root_fd)) == set(FILES)
        assert all(
            _identity(os.lstat(name, dir_fd=root_fd)) == frozen[name]
            for name in FILES
        )
        return output
    finally:
        os.close(root_fd)


def validate(root: Path = REPO_ROOT / OUTPUT_ROOT, enforce_frozen_hashes: bool = True) -> None:
    records = source_snapshot()
    wanted = expected(records)
    actual = _read_outputs(root)
    assert actual == wanted
    if enforce_frozen_hashes:
        assert {name: hashlib.sha256(actual[name]).hexdigest() for name in FILES} == FROZEN_SHA256


def main() -> int:
    validate()
    print(json.dumps({"stage": STAGE, "status": "passed", "output_sha256": FROZEN_SHA256}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
