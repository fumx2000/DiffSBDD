#!/usr/bin/env python3
"""Independent checker for the ADMIT_013 formal-interface Exact6 Design set."""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "2eea08835c4ef88d5b810509134f8eef94e3e99e"
BASE_PARENT = "30c644de3973ba2968ecaa8ebff97159c07678b9"
BASE_SUBJECT = "add CovaPIE ADMIT_013 download outcome and integrity contract v1"
STAGE = "covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

DOWNLOAD_FIELDS = (
    "download_result_status", "observed_http_status",
    "observed_content_length_bytes", "observed_sha256",
)
AUTHORITIES = (
    "expected_content_length_bytes", "expected_sha256", "explicit_integrity_verdict",
)
PARAMETERS = (*DOWNLOAD_FIELDS, *AUTHORITIES)
RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_download_result_record", "canonical_integrity_authority_record",
    "validated_download_result_fields", "validated_integrity_authority_fields",
    "consumed_download_result_fields", "consumed_integrity_authority_fields",
    "evaluator_io_used",
)
OUTCOMES = ("passed", "blocked", "invalid")
PHASES = (
    "Exact4_presence", "Exact4_type_value",
    "Exact3_optional_authority_type_value", "Exact7_business_outcome", "passed",
)
MISSING_REASONS = (
    "DOWNLOAD_RESULT_STATUS_MISSING", "OBSERVED_HTTP_STATUS_MISSING",
    "OBSERVED_CONTENT_LENGTH_BYTES_MISSING", "OBSERVED_SHA256_MISSING",
)
DOWNLOAD_TYPE_REASONS = (
    "DOWNLOAD_RESULT_STATUS_TYPE_INVALID", "OBSERVED_HTTP_STATUS_TYPE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID", "OBSERVED_SHA256_TYPE_INVALID",
)
DOWNLOAD_VALUE_REASONS = (
    "DOWNLOAD_RESULT_STATUS_VALUE_INVALID", "OBSERVED_HTTP_STATUS_RANGE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID", "OBSERVED_SHA256_FORMAT_INVALID",
)
AUTHORITY_TYPE_REASONS = (
    "EXPECTED_CONTENT_LENGTH_BYTES_TYPE_INVALID", "EXPECTED_SHA256_TYPE_INVALID",
    "EXPLICIT_INTEGRITY_VERDICT_TYPE_INVALID",
)
AUTHORITY_VALUE_REASONS = (
    "EXPECTED_CONTENT_LENGTH_BYTES_RANGE_INVALID", "EXPECTED_SHA256_FORMAT_INVALID",
    "EXPLICIT_INTEGRITY_VERDICT_VALUE_INVALID",
)
BUSINESS_REASONS = (
    "DOWNLOAD_RESULT_STATUS_FAILURE", "OBSERVED_HTTP_STATUS_NOT_SUCCESS",
    "OBSERVED_CONTENT_EMPTY", "OBSERVED_SHA256_MISMATCH",
    "EXPLICIT_INTEGRITY_VERDICT_FAILED", "OBSERVED_CONTENT_LENGTH_MISMATCH",
    "INTEGRITY_AUTHORITY_MISSING",
)
REASONS = (
    "", *MISSING_REASONS,
    *(reason for index in range(4) for reason in (
        DOWNLOAD_TYPE_REASONS[index], DOWNLOAD_VALUE_REASONS[index]
    )),
    *(reason for index in range(3) for reason in (
        AUTHORITY_TYPE_REASONS[index], AUTHORITY_VALUE_REASONS[index]
    )),
    *BUSINESS_REASONS,
)

FILES = (
    "covapie_admit_013_formal_evaluator_interface_and_result_contract.csv",
    "covapie_admit_013_formal_evaluator_routing_and_consumption_contract.csv",
    "covapie_admit_013_formal_evaluator_interface_truth_matrix.csv",
    "covapie_admit_013_formal_evaluator_interface_source_boundary_audit.csv",
    "covapie_admit_013_formal_evaluator_interface_issue_readiness_inventory.csv",
    "covapie_admit_013_formal_evaluator_interface_contract_manifest.json",
)
CONTRACT, ROUTING, TRUTH, SOURCE, ISSUE, MANIFEST = FILES
HEADERS = {
    CONTRACT: (
        "contract_order", "contract_section", "section_order", "public_name",
        "formal_type", "presence", "default_or_absence", "source_envelope",
        "validation_rule", "invariant", "contract_passed",
    ),
    ROUTING: (
        "route_order", "case_id", "contract_kind", "source_envelope", "source_key",
        "formal_parameter", "presence", "missing_representation", "consumed_semantics",
        "validated_semantics", "canonical_semantics", "adapter_responsibility",
        "evaluator_responsibility", "route_passed",
    ),
    TRUTH: (
        "case_order", "case_id", "case_group", "assertion_kind", "inherited_case_id",
        *(f"{name}_representation" for name in PARAMETERS),
        "expected_outcome", "expected_reason", "expected_canonical_download_result_record",
        "expected_canonical_integrity_authority_record",
        "expected_validated_download_result_fields",
        "expected_validated_integrity_authority_fields",
        "expected_consumed_download_result_fields",
        "expected_consumed_integrity_authority_fields", "expected_passed",
        "expected_blocks_candidate", "expected_evaluator_io_used",
        "observed_design_result", "case_passed",
    ),
    SOURCE: (
        "source_order", "source_relative_path", "source_kind", "expected_sha256",
        "observed_sha256", "base_blob_sha256", "base_tree_mode", "git_tracked",
        "filesystem_regular", "non_symlink", "parent_chain_non_symlink",
        "pinned_fd_no_follow_read", "raw_checkpoint_excluded", "audit_result",
    ),
    ISSUE: (
        "inherited_order", "issue_id", "issue_type", "affected_fields", "affected_rules",
        "severity", "status", "blocking_scope", "blocking_reason", "issue_origin",
        "integration_transition", "issue_count", "inherited_effective_status",
        "inherited_transition_stage", "inherited_transition_action",
        "inherited_transition_evidence", "successor_effective_status",
        "successor_transition_stage", "successor_transition_action",
        "successor_transition_evidence",
    ),
}

SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_design_gate.py", "bcec99607dc5a27a6b62fe788c93f4a24f12d9af387a6e14c7d1695d2c4482b8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_policy_contract.csv", "2b64ce56c122ede2ea125944c164243e5bb7dc3da89c50607f29dd647208b43a"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_integrity_authority_contract.csv", "d95035d109a2c62646f11c822b50b18ab2e25ded1bfebd13e82a37b9723fa0e1"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_failure_taxonomy_and_precedence.csv", "42bead68915f7260aa2c48dabfe2968623de85a039a20a3b78682af246469031"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv", "7e856eb5ebd995793dcd82fb75266c7ee6f6a8b06b7785f3a70713a96b8efdbb"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_issue_readiness_inventory.csv", "240012c88668a3228139052d3920d02b839329fdda41280d31b5382b9de3620c"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_and_integrity_contract_manifest.json", "1bbfe88f459946b78bb14e5b0b672582d508a838bef220ecf292fa84d15f934d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_formal_evaluator_precondition_matrix.csv", "4b411c86cce23351d4aec3d58a894d161ab163e0305fdd91853bc54f16aa1fdf"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_issue_readiness_inventory.csv", "204923bbf26c286c14ce4feaeb7934b279cafa54287ba96b4e2455fd84cf1198"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_formal_evaluator_preconditions_manifest.json", "63f0f96a960135117b0c4c8d3f80d1991cb8138e7df69d3917e921a6a4c74ce0"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract.csv", "03aef0a14257d9a2c028fcc3dd84c161c29b09bca1a1c71456edc66e2e73c9ce"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_and_result_contract.csv", "682192b492979d9b6114381cbfc02d57c349e3cd8db2541a01177235d34c04e6"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv", "44709c3a679368476c87bcd97dafa2f9cf9bddb4af534c6eb950c565d0919aec"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_contract.csv", "c5c383e9a9e17c5eb5a4b2c92455da89a78e66f75df7ff31ce0494f08281433e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_manifest.json", "ad131895c0acfdaf5b350105031647bdcac9667370fb6cd43baf8826bea995c8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract.csv", "12228051428134223dc4db4ec418ced573637047189056f1fb8df908ca2fe6c8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract_manifest.json", "1df0e2a09817b7763ec4eb767663db169d3239385094da151af28150c2c55d25"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py", "4d9a49806d4ef71a95c8ad032dfa061f7473b1cb55a573459c155f0cd5d57282"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_registry_and_identity_audit.csv", "57ed1f04df27c7b30ec4cea97aead99e7788a2968f77245280850ae26f399e59"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_manifest.json", "bc909aefd86b62139fbb62025d9c323988a4c232ab9c960efb291fb0c196cee3"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv", "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv", "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv", "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv", "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv", "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0"),
)
PATH_SHA = hashlib.sha256(
    json.dumps([path for path, _ in SOURCE_BOUNDARY], separators=(",", ":")).encode()
).hexdigest()
PAIR_SHA = hashlib.sha256(
    json.dumps([list(pair) for pair in SOURCE_BOUNDARY], separators=(",", ":")).encode()
).hexdigest()

FROZEN_SHA256 = {
    CONTRACT: "655ff7c2af7f95a9eef8742e3fac3635b3a914be39aa1bf0cb5efc392d3ee6a7",
    ROUTING: "55b78fdf124efc0310d4e55b8564568c7cd88c5e3155666a75162d6c54c1af90",
    TRUTH: "1ffafe3dac824c91e9dcb3fef8760e1f8f1e92754755816d4cef2d0f58fd5631",
    SOURCE: "019d9949318dcea17d814505bff97229948e8338801c12b775af317130a08d97",
    ISSUE: "e2d895dc822e5de8d6f1410e41f6cd79407b090a0055ebe2a79aeadabf033214",
    MANIFEST: "5cadbddf7d75aac7b92f5f86ad204e96237ea80a58f4372eaa22460b4385ea71",
}

GROUP_COUNTS = {
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
TRANSITIONS = {
    "ADMIT_013_STANDALONE_SIGNATURE_UNRESOLVED": "exact seven-keyword-only signature with private missing singleton defaults",
    "ADMIT_013_RESULT_CONTRACT_UNRESOLVED": "Exact12 result contract, Exact5 validation precedence, and exact representation invariants",
}
TRANSITION_ACTION = "resolved_by_successor_formal_interface_contract_design"


def _git(arguments: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=text, check=False
    )


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode


def _assert_base_lineage() -> None:
    identity = _git(["show", "-s", "--format=%H%n%P%n%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    assert identity.returncode == ancestor.returncode == 0
    assert identity.stdout.splitlines() == [BASE_COMMIT, BASE_PARENT, BASE_SUBJECT]


def _pinned(path: Path, expected: tuple[int, int, int]) -> bytes:
    assert _identity(os.lstat(path)) == expected
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
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


def source_snapshot() -> tuple[tuple[str, bytes, str, str], ...]:
    _assert_base_lineage()
    assert len(SOURCE_BOUNDARY) == len(set(SOURCE_BOUNDARY)) == 25
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
        head, separator, tree_path = tree.stdout.partition("\t")
        parts = head.split()
        assert tree.returncode == tracked.returncode == 0
        assert tracked.stdout.splitlines() == [relative]
        assert separator and tree_path.strip() == relative
        assert len(parts) == 3 and parts[0] in {"100644", "100755"} and parts[1] == "blob"
        assert stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode)
        structures.append((relative, digest, parts[0], _identity(item)))
    records = []
    for relative, digest, mode, frozen_identity in structures:
        data = _pinned(REPO_ROOT / relative, frozen_identity)
        base = _git(["show", f"{BASE_COMMIT}:{relative}"], text=False)
        assert base.returncode == 0 and isinstance(base.stdout, bytes)
        assert hashlib.sha256(data).hexdigest() == hashlib.sha256(base.stdout).hexdigest() == digest
        records.append((relative, data, digest, mode))
    return tuple(records)


def _source(records: tuple[tuple[str, bytes, str, str], ...], suffix: str) -> bytes:
    matches = [data for path, data, _, _ in records if path.endswith(suffix)]
    assert len(matches) == 1
    return matches[0]


def _source_rows(
    records: tuple[tuple[str, bytes, str, str], ...], suffix: str
) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(_source(records, suffix).decode(), newline="")))


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
    item = os.lstat(root)
    root_identity = _identity(item)
    assert stat.S_ISDIR(item.st_mode) and not stat.S_ISLNK(item.st_mode)
    assert root.resolve(strict=True) == root
    root_fd = os.open(
        root,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        assert _identity(os.fstat(root_fd)) == root_identity
        assert set(os.listdir(root_fd)) == set(FILES)
        identities = {}
        for name in FILES:
            leaf = os.lstat(name, dir_fd=root_fd)
            assert stat.S_ISREG(leaf.st_mode) and not stat.S_ISLNK(leaf.st_mode)
            identities[name] = _identity(leaf)
        output = {name: _read_output_at(root_fd, name, identities[name]) for name in FILES}
        assert _identity(os.lstat(root.parent)) == parent_identity
        assert _identity(os.fstat(root_fd)) == root_identity == _identity(os.lstat(root))
        assert set(os.listdir(root_fd)) == set(FILES)
        assert all(_identity(os.lstat(name, dir_fd=root_fd)) == identities[name] for name in FILES)
        return output
    finally:
        os.close(root_fd)


def _rows(data: bytes, header: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(data.decode(), newline=""))
    assert tuple(reader.fieldnames or ()) == header
    rows = list(reader)
    assert all(None not in row for row in rows)
    return rows


def _validate_contract(rows: list[dict[str, str]]) -> None:
    assert len(rows) == 76
    assert [row["contract_order"] for row in rows] == [str(index) for index in range(1, 77)]
    assert len({(row["contract_section"], row["section_order"]) for row in rows}) == 76
    assert all(row["contract_passed"] == "true" for row in rows)
    by_section: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_section.setdefault(row["contract_section"], []).append(row)
    assert set(by_section) == {
        "signature_parameter", "result_field", "result_invariant", "reason_vocabulary",
        "validation_phase", "business_precedence", "formal_symbol_state",
    }
    signature = by_section["signature_parameter"]
    assert [row["public_name"] for row in signature] == list(PARAMETERS)
    assert [row["formal_type"] for row in signature] == ["object"] * 7
    assert [row["presence"] for row in signature] == ["required"] * 4 + ["optional"] * 3
    assert [row["source_envelope"] for row in signature] == ["download_result_context"] * 4 + ["evaluation_context"] * 3
    assert all("keyword-only" in row["validation_rule"] for row in signature)
    assert all("normalization" in row["invariant"] or "canonical" in row["invariant"] for row in signature)
    result = by_section["result_field"]
    assert [row["public_name"] for row in result] == list(RESULT_FIELDS)
    assert [row["formal_type"] for row in result] == [
        "exact str", "exact str", "exact bool", "exact bool", "exact str",
        "exact tuple of exact pair tuples", "exact tuple of exact pair tuples",
        "exact tuple of exact str", "exact tuple of exact str",
        "exact tuple of exact str", "exact tuple of exact str", "exact bool",
    ]
    reasons = by_section["reason_vocabulary"]
    assert [row["public_name"] for row in reasons] == ["<empty>", *REASONS[1:]]
    assert len(reasons) == len(REASONS) == 26
    assert not {"UNKNOWN", "OTHER", "INTERNAL_ERROR", "UNEXPECTED"} & set(REASONS)
    assert [row["public_name"] for row in by_section["validation_phase"]] == list(PHASES)
    assert [row["public_name"] for row in by_section["business_precedence"]] == [*BUSINESS_REASONS, "<passed>"]
    assert [row["public_name"] for row in by_section["formal_symbol_state"]] == [
        "evaluate_admit_013_not_implemented", "Admit013EvaluationResult_not_implemented",
        "adapter_registry_exact13_not_implemented",
    ]


def _validate_routing(rows: list[dict[str, str]]) -> None:
    assert len(rows) == 30
    assert [row["route_order"] for row in rows] == [str(index) for index in range(1, 31)]
    assert len({row["case_id"] for row in rows}) == 30
    assert all(row["route_passed"] == "true" for row in rows)
    routes = [row for row in rows if row["contract_kind"] == "route"]
    assert [row["formal_parameter"] for row in routes] == list(PARAMETERS)
    assert [row["source_envelope"] for row in routes] == ["download_result_context"] * 4 + ["evaluation_context"] * 3
    assert [row["presence"] for row in routes] == ["required"] * 4 + ["optional"] * 3
    forbidden = [row["source_envelope"] for row in rows if row["contract_kind"] == "forbidden_route"]
    assert forbidden == [
        "candidate_record", "batch_context", "stage_authorization_context", "fallback_envelope",
        "filesystem", "network", "raw", "provider_or_download_execution_inside_evaluator",
    ]
    dependency = next(row for row in rows if row["case_id"] == "NO_ADMIT012_RESULT_DEPENDENCY")
    assert dependency["source_key"] == "Admit012EvaluationResult"
    assert "no prior_admit_012_result" in dependency["evaluator_responsibility"]
    scalar = next(row for row in rows if row["case_id"] == "SCALAR_ONLY")
    assert "no dynamic Mapping" in scalar["evaluator_responsibility"]
    for index, name in enumerate(DOWNLOAD_FIELDS):
        missing = next(row for row in rows if row["case_id"] == f"MISSING_{name.upper()}")
        invalid = next(row for row in rows if row["case_id"] == f"INVALID_{name.upper()}")
        assert missing["consumed_semantics"].split("|") == list(DOWNLOAD_FIELDS[:index + 1])
        assert missing["validated_semantics"].split("|") if index else missing["validated_semantics"] == ""
        assert invalid["consumed_semantics"].split("|") == list(DOWNLOAD_FIELDS)
    for index, name in enumerate(AUTHORITIES):
        invalid = next(row for row in rows if row["case_id"] == f"INVALID_{name.upper()}")
        assert invalid["consumed_semantics"].split("|") == list(AUTHORITIES[:index + 1])


def _decode(value: str) -> tuple[str, object]:
    if value == "<MISSING>":
        return "missing", None
    if value.startswith("<str-subclass:"):
        return "str_subclass", ast.literal_eval(value[14:-1])
    if value.startswith("<int-subclass:"):
        return "int_subclass", int(value[14:-1])
    if value.startswith("<bytes:"):
        return "bytes", ast.literal_eval(value[7:-1]).encode()
    if value == "<object>":
        return "object", None
    decoded = ast.literal_eval(value)
    return type(decoded).__name__, decoded


def _valid_download(index: int, observed: tuple[str, object]) -> tuple[bool, bool]:
    kind, value = observed
    expected_kind = ("str", "int", "int", "str")[index]
    type_valid = kind == expected_kind
    if not type_valid:
        return False, False
    if index == 0:
        return True, value in {"success", "failure"}
    if index == 1:
        return True, 100 <= value <= 599  # type: ignore[operator]
    if index == 2:
        return True, value >= 0  # type: ignore[operator]
    return True, re.fullmatch(r"[0-9a-f]{64}", value, flags=re.ASCII) is not None  # type: ignore[arg-type]


def _valid_authority(index: int, observed: tuple[str, object]) -> tuple[bool, bool]:
    kind, value = observed
    expected_kind = ("int", "str", "str")[index]
    type_valid = kind == expected_kind
    if not type_valid:
        return False, False
    if index == 0:
        return True, value >= 0  # type: ignore[operator]
    if index == 1:
        return True, re.fullmatch(r"[0-9a-f]{64}", value, flags=re.ASCII) is not None  # type: ignore[arg-type]
    return True, value in {"verified", "failed"}


def _independent_result(representations: list[str]) -> tuple[object, ...]:
    observed = [_decode(value) for value in representations]
    for index, (kind, _) in enumerate(observed[:4]):
        if kind == "missing":
            return (
                "ADMIT_013", "blocked", False, True, MISSING_REASONS[index], (), (),
                DOWNLOAD_FIELDS[:index], (), DOWNLOAD_FIELDS[:index + 1], (), False,
            )
    download_record = []
    for index, item in enumerate(observed[:4]):
        type_valid, value_valid = _valid_download(index, item)
        if not type_valid or not value_valid:
            reason = DOWNLOAD_TYPE_REASONS[index] if not type_valid else DOWNLOAD_VALUE_REASONS[index]
            return (
                "ADMIT_013", "invalid", False, True, reason, (), (),
                DOWNLOAD_FIELDS[:index], (), DOWNLOAD_FIELDS, (), False,
            )
        download_record.append((DOWNLOAD_FIELDS[index], item[1]))
    download = tuple(download_record)
    authority_record = []
    for index, item in enumerate(observed[4:]):
        if item[0] == "missing":
            continue
        type_valid, value_valid = _valid_authority(index, item)
        if not type_valid or not value_valid:
            reason = AUTHORITY_TYPE_REASONS[index] if not type_valid else AUTHORITY_VALUE_REASONS[index]
            authority = tuple(authority_record)
            return (
                "ADMIT_013", "invalid", False, True, reason, download, authority,
                DOWNLOAD_FIELDS, tuple(pair[0] for pair in authority), DOWNLOAD_FIELDS,
                AUTHORITIES[:index + 1], False,
            )
        authority_record.append((AUTHORITIES[index], item[1]))
    authority = tuple(authority_record)
    values = dict(download)
    authorities = dict(authority)
    if values[DOWNLOAD_FIELDS[0]] == "failure":
        reason = BUSINESS_REASONS[0]
    elif not 200 <= values[DOWNLOAD_FIELDS[1]] <= 299:
        reason = BUSINESS_REASONS[1]
    elif values[DOWNLOAD_FIELDS[2]] == 0:
        reason = BUSINESS_REASONS[2]
    elif AUTHORITIES[1] in authorities and authorities[AUTHORITIES[1]] != values[DOWNLOAD_FIELDS[3]]:
        reason = BUSINESS_REASONS[3]
    elif authorities.get(AUTHORITIES[2]) == "failed":
        reason = BUSINESS_REASONS[4]
    elif AUTHORITIES[0] in authorities and authorities[AUTHORITIES[0]] != values[DOWNLOAD_FIELDS[2]]:
        reason = BUSINESS_REASONS[5]
    elif not (
        authorities.get(AUTHORITIES[1]) == values[DOWNLOAD_FIELDS[3]]
        or authorities.get(AUTHORITIES[2]) == "verified"
    ):
        reason = BUSINESS_REASONS[6]
    else:
        reason = ""
    outcome = "passed" if reason == "" else "blocked"
    return (
        "ADMIT_013", outcome, outcome == "passed", outcome != "passed", reason,
        download, authority, DOWNLOAD_FIELDS, tuple(pair[0] for pair in authority),
        DOWNLOAD_FIELDS, AUTHORITIES, False,
    )


def _validate_truth(
    rows: list[dict[str, str]], records: tuple[tuple[str, bytes, str, str], ...]
) -> None:
    assert len(rows) == 128
    assert [row["case_order"] for row in rows] == [str(index) for index in range(1, 129)]
    assert len({row["case_id"] for row in rows}) == 128
    assert all(row["case_passed"] == "true" for row in rows)
    counts = {
        group: sum(row["case_group"] == group for row in rows)
        for group in sorted({row["case_group"] for row in rows})
    }
    assert counts == GROUP_COUNTS
    negative = [row for row in rows if row["case_group"] == "result_invariant_negative"]
    assert [row["case_id"] for row in negative] == list(NEGATIVE_RESULT_CASES)
    assert all(row["assertion_kind"] == "result_contract_rejection" for row in negative)
    assert all(row["observed_design_result"].startswith("RESULT_CONTRACT_REJECTED:") for row in negative)
    assert not any("DesignMissing" in "|".join(row.values()) or "0x" in row["observed_design_result"] for row in rows)

    for row in rows:
        if row["assertion_kind"] == "result_contract_rejection":
            continue
        result = _independent_result([row[f"{name}_representation"] for name in PARAMETERS])
        assert row["expected_outcome"] == result[1]
        assert row["expected_reason"] == result[4]
        assert row["expected_canonical_download_result_record"] == repr(result[5])
        assert row["expected_canonical_integrity_authority_record"] == repr(result[6])
        assert row["expected_validated_download_result_fields"] == repr(result[7])
        assert row["expected_validated_integrity_authority_fields"] == repr(result[8])
        assert row["expected_consumed_download_result_fields"] == repr(result[9])
        assert row["expected_consumed_integrity_authority_fields"] == repr(result[10])
        assert row["expected_passed"] == str(result[2]).lower()
        assert row["expected_blocks_candidate"] == str(result[3]).lower()
        assert row["expected_evaluator_io_used"] == "false"
        assert row["observed_design_result"] == repr(result)

    inherited = [row for row in rows if row["case_group"] == "inherited_exact7_business_projection"]
    predecessor = _source_rows(
        records, "covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv"
    )
    assert [row["inherited_case_id"] for row in inherited] == [row["case_id"] for row in predecessor]
    for actual, prior in zip(inherited, predecessor, strict=True):
        assert actual["expected_outcome"] == prior["expected_outcome"]
        assert actual["expected_reason"] == prior["expected_reason"]
        for name in DOWNLOAD_FIELDS:
            expected = repr(int(prior[name])) if name in {DOWNLOAD_FIELDS[1], DOWNLOAD_FIELDS[2]} else repr(prior[name])
            assert actual[f"{name}_representation"] == expected
        for name in AUTHORITIES:
            value = prior[name]
            expected = "<MISSING>" if value == "<MISSING>" else repr(int(value)) if name == AUTHORITIES[0] else repr(value)
            assert actual[f"{name}_representation"] == expected


def _validate_source_rows(
    rows: list[dict[str, str]], records: tuple[tuple[str, bytes, str, str], ...]
) -> None:
    assert len(rows) == 25
    assert [row["source_order"] for row in rows] == [str(index) for index in range(1, 26)]
    for row, (path, _, digest, mode) in zip(rows, records, strict=True):
        assert row["source_relative_path"] == path
        assert row["expected_sha256"] == row["observed_sha256"] == row["base_blob_sha256"] == digest
        assert row["base_tree_mode"] == mode
        assert all(row[key] == "true" for key in (
            "git_tracked", "filesystem_regular", "non_symlink",
            "parent_chain_non_symlink", "pinned_fd_no_follow_read", "raw_checkpoint_excluded",
        ))
        assert row["audit_result"] == "passed"


def _validate_issues(
    rows: list[dict[str, str]], records: tuple[tuple[str, bytes, str, str], ...]
) -> None:
    inherited = _source_rows(
        records,
        "covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_issue_readiness_inventory.csv",
    )
    assert len(rows) == len(inherited) == 23
    assert [row["issue_id"] for row in rows] == [row["issue_id"] for row in inherited]
    for actual, prior in zip(rows, inherited, strict=True):
        for name in (
            "inherited_order", "issue_id", "issue_type", "affected_fields", "affected_rules",
            "severity", "status", "blocking_scope", "blocking_reason", "issue_origin",
            "integration_transition", "issue_count",
        ):
            assert actual[name] == prior[name]
        assert actual["inherited_effective_status"] == prior["effective_status"]
        assert actual["inherited_transition_stage"] == prior["transition_stage"]
        assert actual["inherited_transition_action"] == prior["transition_action"]
        assert actual["inherited_transition_evidence"] == prior["transition_evidence"]
        evidence = TRANSITIONS.get(actual["issue_id"])
        assert actual["successor_effective_status"] == ("resolved" if evidence else prior["effective_status"])
        assert actual["successor_transition_stage"] == (STAGE if evidence else "")
        assert actual["successor_transition_action"] == (TRANSITION_ACTION if evidence else "unchanged")
        assert actual["successor_transition_evidence"] == (evidence or "inherited effective state retained")
    by_id = {row["issue_id"]: row for row in rows}
    assert by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "ADMIT_013|ADMIT_014|ADMIT_015"
    assert by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["successor_effective_status"] == "open"
    assert by_id["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["successor_effective_status"] == "open"


TRUE_READINESS = (
    "admit_013_preconditions_audited",
    "admit_013_download_outcome_and_integrity_contract_designed",
    "admit_013_standalone_signature_frozen",
    "admit_013_formal_result_contract_frozen",
    "admit_013_formal_evaluator_interface_contract_frozen",
    "admit_013_validation_precedence_resolved",
    "admit_013_future_evaluator_pure_in_memory_possible",
    "ready_for_admit_013_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "evaluate_admit_013_implemented", "Admit013EvaluationResult_implemented",
    "admit_013_rule_logic_implemented", "admit_013_unified_adapter_contract_frozen",
    "admit_013_unified_adapter_implemented", "admit_013_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "provider_mapping_validated", "real_provider_evaluation_ready",
    "ready_for_bulk_download_now", "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented", "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


def readiness() -> dict[str, bool]:
    return {**{name: True for name in TRUE_READINESS}, **{name: False for name in FALSE_READINESS}}


MANIFEST_KEYS = (
    "admission_rule_id", "admission_rule_name", "all_checks_passed",
    "authority_fields_optional", "base_commit", "base_parent", "base_subject",
    "blocking_reason", "business_failure_precedence",
    "canonical_download_result_representation",
    "canonical_integrity_authority_representation", "consumed_semantics", "design_oracle",
    "design_result_type", "download_result_fields", "evaluation_phase", "evidence_source",
    "failure_severity", "feature_semantics_audit_requirement", "formal_evaluator_implemented",
    "formal_result_type_defined", "future_function_name", "future_public_signature",
    "future_result_type_name", "integrity_authority_fields", "issue_transition_action",
    "issue_transition_count", "issue_transition_ids", "manifest_schema_version",
    "outcome_vocabulary", "output_file_count", "output_files", "output_sha256", "project",
    "readiness", "reason_vocabulary", "reason_vocabulary_count_including_empty",
    "recommended_next_step", "remaining_open_issue_ids", "rename_policy", "required_status",
    "result_field_count", "result_field_exact_types", "result_fields", "result_invariants",
    "routing_contract", "row_counts", "safety", "signature_all_keyword_only",
    "signature_dynamic_mapping_or_policy_context", "signature_parameter_count",
    "signature_parameters", "signature_private_missing_singleton_defaults",
    "signature_varargs", "signature_varkw", "source_boundary", "source_count",
    "source_path_list_sha256", "source_path_sha256_pairs_sha256", "stage", "step12d_status",
    "truth_matrix_group_counts", "unified_adapter_or_registry_or_exact13_runtime_changed",
    "validated_semantics", "validation_phase_order",
)


def _validate_manifest(
    value: dict[str, Any], records: tuple[tuple[str, bytes, str, str], ...]
) -> None:
    assert list(value) == list(MANIFEST_KEYS) == sorted(MANIFEST_KEYS)
    assert value["manifest_schema_version"] == "covapie_admit_013_formal_evaluator_interface_contract_manifest_v1"
    assert value["project"] == "CovaPIE" and value["stage"] == STAGE
    assert [value["base_commit"], value["base_parent"], value["base_subject"]] == [BASE_COMMIT, BASE_PARENT, BASE_SUBJECT]
    assert {
        key: value[key] for key in (
            "admission_rule_id", "admission_rule_name", "evidence_source", "required_status",
            "failure_severity", "blocking_reason", "evaluation_phase",
        )
    } == {
        "admission_rule_id": "ADMIT_013", "admission_rule_name": "download_failure_fail_closed",
        "evidence_source": "future_download_result",
        "required_status": "non_success_or_integrity_failure_not_admitted",
        "failure_severity": "blocking", "blocking_reason": "download_failure_must_fail_closed",
        "evaluation_phase": "post_download",
    }
    assert value["future_function_name"] == "evaluate_admit_013"
    assert value["future_result_type_name"] == "Admit013EvaluationResult"
    assert value["future_public_signature"] == (
        "evaluate_admit_013(*, download_result_status: object = _MISSING, "
        "observed_http_status: object = _MISSING, observed_content_length_bytes: object = _MISSING, "
        "observed_sha256: object = _MISSING, expected_content_length_bytes: object = _MISSING, "
        "expected_sha256: object = _MISSING, explicit_integrity_verdict: object = _MISSING) -> Admit013EvaluationResult"
    )
    assert value["signature_parameters"] == list(PARAMETERS)
    assert value["signature_parameter_count"] == 7
    assert value["signature_all_keyword_only"] is True
    assert value["signature_varargs"] is value["signature_varkw"] is False
    assert value["signature_dynamic_mapping_or_policy_context"] is False
    assert value["signature_private_missing_singleton_defaults"] is True
    assert value["download_result_fields"] == list(DOWNLOAD_FIELDS)
    assert value["integrity_authority_fields"] == list(AUTHORITIES)
    assert value["authority_fields_optional"] is True
    assert value["outcome_vocabulary"] == list(OUTCOMES)
    assert value["reason_vocabulary"] == list(REASONS) and len(REASONS) == 26
    assert value["reason_vocabulary_count_including_empty"] == 26
    assert value["validation_phase_order"] == list(PHASES)
    assert value["business_failure_precedence"] == list(BUSINESS_REASONS)
    assert value["result_fields"] == list(RESULT_FIELDS) and value["result_field_count"] == 12
    assert value["result_field_exact_types"] == [
        "str", "str", "bool", "bool", "str", "tuple", "tuple", "tuple",
        "tuple", "tuple", "tuple", "bool",
    ]
    assert value["formal_evaluator_implemented"] is False
    assert value["formal_result_type_defined"] is False
    assert value["unified_adapter_or_registry_or_exact13_runtime_changed"] is False
    routing = value["routing_contract"]
    assert routing == {
        "Admit012EvaluationResult_consumed": False,
        "download_result_context": list(DOWNLOAD_FIELDS),
        "evaluation_context": list(AUTHORITIES),
        "forbidden_envelopes": [
            "candidate_record", "batch_context", "stage_authorization_context",
            "fallback_envelope", "filesystem", "network", "raw",
            "provider_or_download_execution_inside_evaluator",
        ],
        "scalar_keyword_consumption_only": True,
    }
    assert value["source_count"] == len(records) == 25
    assert value["source_path_list_sha256"] == PATH_SHA
    assert value["source_path_sha256_pairs_sha256"] == PAIR_SHA
    assert value["source_boundary"] == [
        {"path": path, "sha256": digest, "base_tree_mode": mode}
        for path, _, digest, mode in records
    ]
    assert value["output_file_count"] == 6 and value["output_files"] == list(FILES)
    assert value["output_sha256"] == {name: FROZEN_SHA256[name] for name in FILES[:-1]}
    assert MANIFEST not in value["output_sha256"]
    assert value["row_counts"] == {
        "inherited_business_projection": 23, "interface_result_contract": 76,
        "issue_inventory": 23, "result_negative": 26, "routing_consumption": 30,
        "source_boundary": 25, "truth_matrix": 128,
    }
    assert value["truth_matrix_group_counts"] == GROUP_COUNTS
    assert value["issue_transition_count"] == 2
    assert value["issue_transition_ids"] == list(TRANSITIONS)
    assert value["issue_transition_action"] == TRANSITION_ACTION
    assert value["remaining_open_issue_ids"] == [
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED", "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    ]
    expected_readiness = readiness()
    assert list(value["readiness"]) == sorted(expected_readiness)
    assert value["readiness"] == expected_readiness
    assert list(value["safety"]) == sorted(value["safety"])
    assert value["safety"] == {
        "dataloader": False, "download": False, "model_or_checkpoint": False,
        "network": False, "provider": False, "raw": False, "runtime_change": False,
        "stage_commit_push": False, "training": False,
    }
    assert value["recommended_next_step"] == "implement_covapie_admit_013_standalone_evaluator_interface_v1"
    assert value["step12d_status"] == "smoke_legality_only_not_final_training_feature_contract"
    assert "UNKNOWN_ATOM_FEATURE_POLICY" in value["feature_semantics_audit_requirement"]
    assert value["rename_policy"] == "RENAME_NOREPLACE_required; GPFS_EINVAL_fails_closed; no_os.replace_fallback"
    assert value["all_checks_passed"] is True


def _validate_candidate_source() -> None:
    path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate.py"
    source = path.read_text()
    tree = ast.parse(source)
    definitions = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    assert "evaluate_admit_013" not in definitions
    assert "Admit013EvaluationResult" not in definitions
    assert "_evaluate_registered_admit_013" not in definitions
    classifier = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "classify_admit_013_formal_evaluator_interface_design"
    )
    assert classifier.args.posonlyargs == classifier.args.args == []
    assert [argument.arg for argument in classifier.args.kwonlyargs] == list(PARAMETERS)
    assert classifier.args.vararg is classifier.args.kwarg is None
    assert len(classifier.args.kw_defaults) == 7
    result_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "Admit013EvaluationResultContractDesign"
    )
    annotations = [
        node.target.id for node in result_class.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    ]
    assert annotations == list(RESULT_FIELDS)
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os" and node.func.attr == "replace"
        for node in ast.walk(tree)
    )


def validate(
    root: Path = REPO_ROOT / OUTPUT_ROOT,
    *,
    enforce_frozen_hashes: bool = True,
) -> None:
    # Base identity and every source are pinned before the first output read.
    records = source_snapshot()
    actual = _read_outputs(root)
    contract = _rows(actual[CONTRACT], HEADERS[CONTRACT])
    routing = _rows(actual[ROUTING], HEADERS[ROUTING])
    truth = _rows(actual[TRUTH], HEADERS[TRUTH])
    sources = _rows(actual[SOURCE], HEADERS[SOURCE])
    issues = _rows(actual[ISSUE], HEADERS[ISSUE])
    manifest = json.loads(actual[MANIFEST])
    _validate_contract(contract)
    _validate_routing(routing)
    _validate_truth(truth, records)
    _validate_source_rows(sources, records)
    _validate_issues(issues, records)
    _validate_manifest(manifest, records)
    _validate_candidate_source()
    if enforce_frozen_hashes:
        assert {
            name: hashlib.sha256(content).hexdigest() for name, content in actual.items()
        } == FROZEN_SHA256


def main() -> int:
    validate()
    print(json.dumps({
        "stage": STAGE,
        "status": "passed",
        "source_path_list_sha256": PATH_SHA,
        "source_path_sha256_pairs_sha256": PAIR_SHA,
        "output_sha256": FROZEN_SHA256,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
