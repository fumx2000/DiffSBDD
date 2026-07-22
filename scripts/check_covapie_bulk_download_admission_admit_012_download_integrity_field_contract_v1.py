#!/usr/bin/env python3
"""Independent checker for the ADMIT_012 Exact4 field-contract design gate."""
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
BASE_COMMIT = "62b2ba8de9a38f48ae35b1fd217897191a0519cd"
BASE_SUBJECT = "add CovaPIE ADMIT_012 formal evaluator interface preconditions audit v1"
STAGE = "covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
FIELDS = (
    "download_result_status", "observed_http_status",
    "observed_content_length_bytes", "observed_sha256",
)
ALLOWED = ("success", "failure")
SUCCESS = ("success",)
ENUM_VERSION = "covapie_download_result_status_v1"
BLOCKING_REASON = "download_integrity_fields_missing"
MISSING = {
    FIELDS[0]: "DOWNLOAD_RESULT_STATUS_MISSING",
    FIELDS[1]: "OBSERVED_HTTP_STATUS_MISSING",
    FIELDS[2]: "OBSERVED_CONTENT_LENGTH_BYTES_MISSING",
    FIELDS[3]: "OBSERVED_SHA256_MISSING",
}
TYPE_REASON = {
    FIELDS[0]: "DOWNLOAD_RESULT_STATUS_TYPE_INVALID",
    FIELDS[1]: "OBSERVED_HTTP_STATUS_TYPE_INVALID",
    FIELDS[2]: "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
    FIELDS[3]: "OBSERVED_SHA256_TYPE_INVALID",
}
VALUE_REASON = {
    FIELDS[0]: "DOWNLOAD_RESULT_STATUS_VALUE_INVALID",
    FIELDS[1]: "OBSERVED_HTTP_STATUS_RANGE_INVALID",
    FIELDS[2]: "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID",
    FIELDS[3]: "OBSERVED_SHA256_FORMAT_INVALID",
}
REASONS = tuple(MISSING.values()) + tuple(
    reason for field in FIELDS for reason in (TYPE_REASON[field], VALUE_REASON[field])
)
FILES = (
    "covapie_admit_012_download_integrity_field_contract.csv",
    "covapie_admit_012_download_result_status_enum.csv",
    "covapie_admit_012_download_integrity_validation_truth_matrix.csv",
    "covapie_admit_012_download_integrity_contract_source_boundary_audit.csv",
    "covapie_admit_012_download_integrity_contract_issue_readiness_inventory.csv",
    "covapie_admit_012_download_integrity_field_contract_manifest.json",
)
CONTRACT_FILE, ENUM_FILE, TRUTH_FILE, SOURCE_FILE, ISSUE_FILE, MANIFEST_FILE = FILES
FROZEN_SHA256: dict[str, str] = {
    "covapie_admit_012_download_integrity_field_contract.csv": "03aef0a14257d9a2c028fcc3dd84c161c29b09bca1a1c71456edc66e2e73c9ce",
    "covapie_admit_012_download_result_status_enum.csv": "4c016e8c325ce6a422dff618ae166ec4f42243cc0d1fbf8f6a722c13f63139f6",
    "covapie_admit_012_download_integrity_validation_truth_matrix.csv": "766506f8c0bf2d7734b9c379c9437e1a48a2117873f7e974325b00ab685a39e1",
    "covapie_admit_012_download_integrity_contract_source_boundary_audit.csv": "73393c6c540cb00d040fa8154948f544e445bbcb63323d9f463709c7ee8b16ed",
    "covapie_admit_012_download_integrity_contract_issue_readiness_inventory.csv": "dfe8e16d741548323cddfcdf3db86bdf0c098d6bb2a86fcb8ec0914ebe924855",
    "covapie_admit_012_download_integrity_field_contract_manifest.json": "9fadff44ae15474783df2a3997c45f2c4d57a41ca2adbab0b40f1d890f51039f",
}

CONTRACT_COLUMNS = (
    "field_order", "field_name", "requirement_phase", "producer_scope", "exact_builtin_type",
    "subclasses_allowed", "normalization_allowed", "presence_required", "missing_reason",
    "type_invalid_reason", "value_invalid_reason", "value_contract", "enum_version",
    "ordered_allowed_values", "success_subset", "legal_minimum", "legal_maximum",
    "future_success_minimum", "future_success_maximum", "admit_012_executes_success_judgment",
    "used_by_admit_012", "reserved_for_admit_013", "contract_passed",
)
ENUM_COLUMNS = (
    "row_order", "row_kind", "enum_version", "canonical_order", "status_value",
    "canonical_allowed", "success_member", "future_admit_013_disposition",
    "historical_source_path", "historical_field_name", "historical_literal",
    "promoted_to_canonical", "notes", "row_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "presence_representation",
    "download_result_status_representation", "observed_http_status_representation",
    "observed_content_length_bytes_representation", "observed_sha256_representation",
    "expected_contract_outcome", "expected_reason", "expected_first_failing_field",
    "expected_rule_blocking_reason", "future_admit_013_disposition",
    "observed_contract_outcome", "observed_reason", "observed_first_failing_field",
    "observed_rule_blocking_reason", "case_passed",
)
SOURCE_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "base_tree_mode", "expected_sha256",
    "base_tree_sha256", "filesystem_sha256", "frozen_snapshot_sha256", "git_tracked",
    "base_tree_blob", "filesystem_regular", "non_symlink", "parent_chain_non_symlink",
    "safe_descendant", "pinned_fd_read", "triple_sha256_passed", "source_boundary_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

SOURCE_SHA256 = {
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_contract_manifest.json": "9718090b212e3338bddef1fb7d6fb62e39d95e1911fe5bdd0ff6613b364e8bf4",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract_manifest.json": "d5ad2622b5182898c418d774e4c0deb33fc2fb643caaa5da0507cabb3824f884",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_formal_evaluator_precondition_matrix.csv": "c667c5f195a1d834672564835380896553339833041d17cc2f689db23f9d319f",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_formal_evaluator_preconditions_manifest.json": "712caa27add06784db5cfe2e59a65952ae4b1c5a369ff43772d8e4f95b18c4de",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_issue_readiness_inventory.csv": "5ebe9332137bfa9c7804c82041ff695b3379ba505a5eb006fa5c7798510e8529",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_observed_value_inventory.csv": "dc47865f2f176b9e37aac0caf71fdacee1275eece19351cb69d31f64ad14104f",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_source_boundary_audit.csv": "4272d31320a9b32e503d4fda49df5c21778238b46e5f2b51bb1dbbb1a3d5ce5e",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_design_gate_manifest.json": "085cb2f2a6bfe9bebe9e503dd10aa0b4d6f9ad754ff99539b1bafb33c78b5444",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv": "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv": "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv": "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv": "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_implementation_issue_inventory.csv": "7c7707f5261461083bda7ab2177a423b608c725c070dafaff558bdf39256211e",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_implementation_precondition_manifest.json": "2304b5754d8052b4b186981a98c12f259608a3492947e069c2afab84084a0d52",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv": "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "data/derived/covalent_small/real_covalent_pilot_download_execution_gate_v0/real_covalent_pilot_download_provenance.csv": "0c280d377091df6d6e269cd7ac0bac5fc02c9883daaca46ce23a71b390704f2d",
    "data/derived/covalent_small/real_covalent_pilot_download_integrity_gate_v0/real_covalent_pilot_download_integrity_gate_manifest.json": "00eda1c687d83d813ecd411ab769ec2d500fa56b80c009dda85b93d1cf757868",
    "docs/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1_summary.md": "86cd3da95b990d0143ee8df1eafe2f7d974bf09cef06142965b09aed67c7a9d2",
    "scripts/check_covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1.py": "f5e1c695869f21c149ea441ea878c9005c1015ec3bc5ece25d0784b38496774e",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.py": "c515afab9ac6dc4390d9ef0bf385de4261c612bb1cbe67a19b008c40c288cd7d",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate.py": "93e6e726092f8c3e66b19c7ab4c6d363d47962c07eeb694c7237b2b0d5a31346",
    "src/covalent_ext/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_preconditions_audit.py": "3547991855ab8a828e89174b5c725e1c1ef9627a56dc9c22b2d5769b7830035b",
    "src/covalent_ext/covapie_cys_sg_discovery_download_smoke.py": "68335a0991772a5c57af476f4d538a3d1d8f40d71a2836715707c1c2d9aa5c8c",
    "src/covalent_ext/covapie_independent_group_expansion_acquisition_execution_smoke.py": "30f80efb146689eb88c0f94962703a447aec8613e9eef78d6be012d0548e17d0",
    "src/covalent_ext/covapie_small_pilot_download_manifest_gate.py": "3f45d0d97bbbf087e6258e8fd87d82c830697b0a24f7bb914ef4593a82da4bb4",
    "src/covalent_ext/real_covalent_pilot_download_execution_gate.py": "ecf2bbafd25dfe8da746dc56974eecbddb703cbc144dbf20a8f0c50fbf840a78",
    "src/covalent_ext/real_covalent_pilot_download_integrity_gate.py": "df5a8bfe9935db416a934535ffa33285d6b0aea466617c1ae1a89a934e1dd20c",
    "tests/test_covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1.py": "47784344fccdf94a3b285d5ba3423bd34cd6fd11441184952a67e26c2555b71e",
    "tests/test_real_covalent_pilot_download_integrity_gate_v0.py": "29a341fb066d170bc2b2a10fa3d58d7cb899e225af94b6a7267cec6fc497e708",
}
SOURCE_PATHS = tuple(sorted(SOURCE_SHA256))
PATH_LIST_SHA = "02979f002c72725ffb30b5367a923d7b0e61ac13a88b594a3ecb0c74b5403c85"
PATH_PAIR_SHA = "fab86f35f2adcc12e3cbb99ac36bf05074e53b8b547a550b7e9503ab4cc011a9"
HISTORY = (
    ("src/covalent_ext/covapie_cys_sg_discovery_download_smoke.py", "download_status", "downloaded"),
    ("src/covalent_ext/covapie_cys_sg_discovery_download_smoke.py", "download_status", "existing_reused"),
    ("src/covalent_ext/covapie_cys_sg_discovery_download_smoke.py", "download_status", "failed_with_reason"),
    ("src/covalent_ext/covapie_independent_group_expansion_acquisition_execution_smoke.py", "download_status", "blocked_invalid_existing_raw"),
    ("src/covalent_ext/covapie_independent_group_expansion_acquisition_execution_smoke.py", "download_status", "blocked_network_execution_not_requested"),
    ("src/covalent_ext/covapie_independent_group_expansion_acquisition_execution_smoke.py", "download_status", "download_failed_or_invalid_payload"),
    ("src/covalent_ext/covapie_independent_group_expansion_acquisition_execution_smoke.py", "download_status", "downloaded"),
    ("src/covalent_ext/covapie_independent_group_expansion_acquisition_execution_smoke.py", "download_status", "reused_existing_valid_raw"),
    ("src/covalent_ext/covapie_small_pilot_download_manifest_gate.py", "download_status", "pending_not_downloaded"),
    ("src/covalent_ext/real_covalent_pilot_download_execution_gate.py", "provenance_status", "download_failed"),
    ("src/covalent_ext/real_covalent_pilot_download_execution_gate.py", "provenance_status", "downloaded_raw_file_recorded"),
    ("src/covalent_ext/real_covalent_pilot_download_execution_gate.py", "provenance_status", "recorded_without_raw_file_copy"),
    ("src/covalent_ext/real_covalent_pilot_download_integrity_gate.py", "integrity_status", "failed"),
    ("src/covalent_ext/real_covalent_pilot_download_integrity_gate.py", "integrity_status", "passed"),
)
RESOLVED = {
    "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
    "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
    "ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED",
    "ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED",
}
OPEN_REQUIRED = {
    "ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED",
    "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED",
    "ADMIT_012_RESULT_CONTRACT_UNRESOLVED",
    "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
    "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
}
TRANSITION = "admit_012_download_integrity_field_contract_frozen_v1"
CASE_IDS = (
    "VALID_STATUS_SUCCESS", "VALID_STATUS_FAILURE", "VALID_HTTP_100", "VALID_HTTP_299",
    "VALID_HTTP_300", "VALID_HTTP_599", "VALID_CONTENT_ZERO", "VALID_CONTENT_LARGE",
    "VALID_SHA_LOWERCASE64", "MISSING_STATUS", "MISSING_HTTP", "MISSING_CONTENT", "MISSING_SHA",
    "MULTI_MISSING_STATUS_HTTP", "MULTI_MISSING_HTTP_SHA", "STATUS_NONE_PRESENT",
    "STATUS_EMPTY_PRESENT", "STATUS_UNKNOWN", "STATUS_UPPERCASE_ALIAS", "STATUS_STR_SUBCLASS",
    "STATUS_NON_STR", "HTTP_BOOL", "HTTP_INT_SUBCLASS", "HTTP_STRING", "HTTP_99", "HTTP_600",
    "CONTENT_BOOL", "CONTENT_INT_SUBCLASS", "CONTENT_STRING", "CONTENT_NEGATIVE",
    "SHA_NONE_PRESENT", "SHA_BYTES", "SHA_STR_SUBCLASS", "SHA_EMPTY", "SHA_63", "SHA_65",
    "SHA_UPPERCASE", "SHA_MIXED_CASE", "SHA_NONHEX", "SHA_WHITESPACE", "SHA_0X_PREFIX",
    "SHA_SHA256_PREFIX", "MULTI_EARLIER_INVALID_LATER_MISSING", "MULTI_MISSING_PRECEDENCE",
    "MULTI_TYPE_FAILURES", "MULTI_TYPE_VALUE_FAILURES", "MULTI_STATUS_HTTP_INVALID",
    "MULTI_HTTP_CONTENT_INVALID", "MULTI_CONTENT_SHA_INVALID", "BOUNDARY_FAILURE_STATUS",
    "BOUNDARY_VALID_4XX", "BOUNDARY_VALID_5XX_FAILURE",
)
GROUP_COUNTS = {
    "admit_013_boundary": 3, "canonical_valid": 9, "content_invalid": 4,
    "http_invalid": 5, "missing": 6, "multi_invalid_precedence": 7,
    "sha_invalid": 12, "status_invalid": 6,
}


class _Missing:
    pass


MISSING_VALUE = _Missing()


class _StrSubclass(str):
    pass


class _IntSubclass(int):
    pass


def _git(args: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=text, check=False)


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode


def _read_outputs(root: Path) -> dict[str, bytes]:
    parent_identity = _identity(os.lstat(root.parent))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    assert stat.S_ISDIR(root_item.st_mode) and not stat.S_ISLNK(root_item.st_mode)
    assert root.resolve(strict=True) == root and {entry.name for entry in root.iterdir()} == set(FILES)
    descriptor = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try:
        assert _identity(os.fstat(descriptor)) == root_identity
        output: dict[str, bytes] = {}
        identities: dict[str, tuple[int, int, int]] = {}
        for name in FILES:
            item = os.lstat(root / name)
            identity = _identity(item)
            identities[name] = identity
            assert stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode)
            leaf = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=descriptor)
            try:
                assert _identity(os.fstat(leaf)) == identity
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(leaf, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                assert _identity(os.fstat(leaf)) == identity
                output[name] = b"".join(chunks)
            finally:
                os.close(leaf)
        assert _identity(os.lstat(root.parent)) == parent_identity
        assert _identity(os.lstat(root)) == root_identity == _identity(os.fstat(descriptor))
        assert {entry.name for entry in root.iterdir()} == set(FILES)
        assert all(_identity(os.lstat(root / name)) == identity for name, identity in identities.items())
        return output
    finally:
        os.close(descriptor)


def _rows(data: bytes, expected_columns: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(data.decode(), newline=""))
    assert tuple(reader.fieldnames or ()) == expected_columns
    rows = list(reader)
    assert all(tuple(row) == expected_columns and None not in row for row in rows)
    return rows


def _validate_base_and_sources(rows: list[dict[str, str]]) -> None:
    subject = _git(["show", "-s", "--format=%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    assert subject.returncode == 0 and subject.stdout.strip() == BASE_SUBJECT and ancestor.returncode == 0
    assert len(rows) == len(SOURCE_PATHS) == 29
    assert hashlib.sha256(json.dumps(list(SOURCE_PATHS), separators=(",", ":")).encode()).hexdigest() == PATH_LIST_SHA
    assert hashlib.sha256(json.dumps([[p, SOURCE_SHA256[p]] for p in SOURCE_PATHS], separators=(",", ":")).encode()).hexdigest() == PATH_PAIR_SHA
    for index, (row, value) in enumerate(zip(rows, SOURCE_PATHS), 1):
        path = Path(value)
        assert row["source_order"] == str(index) and row["source_relative_path"] == value
        assert row["source_kind"] == ("python_source" if path.suffix == ".py" else "committed_csv" if path.suffix == ".csv" else "committed_manifest" if path.suffix == ".json" else "tracked_text")
        assert row["expected_sha256"] == SOURCE_SHA256[value]
        assert {row[key] for key in (
            "base_tree_sha256", "filesystem_sha256", "frozen_snapshot_sha256"
        )} == {SOURCE_SHA256[value]}
        assert all(row[key] == "true" for key in SOURCE_COLUMNS[8:])
        assert not path.is_absolute() and ".." not in path.parts and path.parts[:2] != ("data", "raw") and path.parts[0] != "checkpoints"
        absolute = REPO_ROOT / path
        item = os.lstat(absolute)
        assert stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode) and absolute.resolve(strict=True) == absolute
        tree = _git(["ls-tree", BASE_COMMIT, "--", value])
        tracked = _git(["ls-files", "--error-unmatch", "--", value])
        head, separator, tree_path = tree.stdout.partition("\t")
        parts = head.split()
        assert tree.returncode == tracked.returncode == 0 and tracked.stdout.splitlines() == [value]
        assert separator and tree_path.strip() == value and len(parts) == 3 and parts[0] in {"100644", "100755"} and parts[1] == "blob"
        assert row["base_tree_mode"] == parts[0]
        before = _identity(item)
        descriptor = os.open(absolute, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            assert _identity(os.fstat(descriptor)) == before
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            assert _identity(os.fstat(descriptor)) == before == _identity(os.lstat(absolute))
        finally:
            os.close(descriptor)
        data = b"".join(chunks)
        base = _git(["show", f"{BASE_COMMIT}:{value}"], text=False)
        assert base.returncode == 0 and hashlib.sha256(data).hexdigest() == SOURCE_SHA256[value]
        assert hashlib.sha256(base.stdout).hexdigest() == SOURCE_SHA256[value]


def _expected_contract_rows() -> list[dict[str, str]]:
    specs = (
        (FIELDS[0], "str", "exact member of ordered canonical enum success|failure"),
        (FIELDS[1], "int", "integer HTTP status in inclusive structural range 100..599"),
        (FIELDS[2], "int", "integer observed byte count >= 0; no V1 upper bound"),
        (FIELDS[3], "str", "exactly 64 ASCII lowercase hexadecimal characters [0-9a-f]{64}"),
    )
    result = []
    for index, (field, type_name, value_contract) in enumerate(specs, 1):
        result.append({
            "field_order": str(index), "field_name": field, "requirement_phase": "post_download",
            "producer_scope": "download_execution_result", "exact_builtin_type": type_name,
            "subclasses_allowed": "false", "normalization_allowed": "false", "presence_required": "true",
            "missing_reason": MISSING[field], "type_invalid_reason": TYPE_REASON[field],
            "value_invalid_reason": VALUE_REASON[field], "value_contract": value_contract,
            "enum_version": ENUM_VERSION if field == FIELDS[0] else "",
            "ordered_allowed_values": "success|failure" if field == FIELDS[0] else "",
            "success_subset": "success" if field == FIELDS[0] else "",
            "legal_minimum": "100" if field == FIELDS[1] else "",
            "legal_maximum": "599" if field == FIELDS[1] else "",
            "future_success_minimum": "200" if field == FIELDS[1] else "",
            "future_success_maximum": "299" if field == FIELDS[1] else "",
            "admit_012_executes_success_judgment": "false", "used_by_admit_012": "true",
            "reserved_for_admit_013": "true", "contract_passed": "true",
        })
    return result


def _validate_enum(rows: list[dict[str, str]]) -> None:
    assert len(rows) == 2 + len(HISTORY)
    for index, value in enumerate(ALLOWED, 1):
        row = rows[index - 1]
        success = value in SUCCESS
        assert row == {
            "row_order": str(index), "row_kind": "canonical_enum", "enum_version": ENUM_VERSION,
            "canonical_order": str(index), "status_value": value, "canonical_allowed": "true",
            "success_member": str(success).lower(),
            "future_admit_013_disposition": "pending_integrity_match_checks_not_implemented_here" if success else "blocked_not_implemented_here",
            "historical_source_path": "", "historical_field_name": "", "historical_literal": "",
            "promoted_to_canonical": "not_applicable", "notes": "closed V1 canonical enum", "row_passed": "true",
        }
    for order, (row, history) in enumerate(zip(rows[2:], HISTORY), 3):
        path, field, literal = history
        assert row == {
            "row_order": str(order), "row_kind": "historical_literal", "enum_version": ENUM_VERSION,
            "canonical_order": "", "status_value": "", "canonical_allowed": "false", "success_member": "false",
            "future_admit_013_disposition": "not_applicable_historical_noncontract_evidence",
            "historical_source_path": path, "historical_field_name": field, "historical_literal": literal,
            "promoted_to_canonical": "false",
            "notes": "static historical naming evidence only; no alias conversion or semantic promotion",
            "row_passed": "true",
        }
        assert f'"{literal}"' in (REPO_ROOT / path).read_text()


def _decode(value: str) -> object:
    if value == "<MISSING>":
        return MISSING_VALUE
    if value.startswith("<str-subclass:") and value.endswith(">"):
        parsed = ast.literal_eval(value[len("<str-subclass:"):-1])
        assert type(parsed) is str
        return _StrSubclass(parsed)
    if value.startswith("<int-subclass:") and value.endswith(">"):
        parsed = ast.literal_eval(value[len("<int-subclass:"):-1])
        assert type(parsed) is int
        return _IntSubclass(parsed)
    return ast.literal_eval(value)


def _classify(values: tuple[object, ...]) -> tuple[str, str, str, str]:
    for field, value in zip(FIELDS, values):
        if value is MISSING_VALUE:
            return "missing", MISSING[field], field, BLOCKING_REASON
    status, http, content, sha = values
    if type(status) is not str:
        return "invalid", TYPE_REASON[FIELDS[0]], FIELDS[0], BLOCKING_REASON
    if status not in ALLOWED:
        return "invalid", VALUE_REASON[FIELDS[0]], FIELDS[0], BLOCKING_REASON
    if type(http) is not int:
        return "invalid", TYPE_REASON[FIELDS[1]], FIELDS[1], BLOCKING_REASON
    if not 100 <= http <= 599:
        return "invalid", VALUE_REASON[FIELDS[1]], FIELDS[1], BLOCKING_REASON
    if type(content) is not int:
        return "invalid", TYPE_REASON[FIELDS[2]], FIELDS[2], BLOCKING_REASON
    if content < 0:
        return "invalid", VALUE_REASON[FIELDS[2]], FIELDS[2], BLOCKING_REASON
    if type(sha) is not str:
        return "invalid", TYPE_REASON[FIELDS[3]], FIELDS[3], BLOCKING_REASON
    if re.fullmatch(r"[0-9a-f]{64}", sha, flags=re.ASCII) is None:
        return "invalid", VALUE_REASON[FIELDS[3]], FIELDS[3], BLOCKING_REASON
    return "contract_valid", "", "", ""


def _validate_truth(rows: list[dict[str, str]]) -> None:
    assert len(rows) == len(CASE_IDS) == 52
    assert [row["case_order"] for row in rows] == [str(index) for index in range(1, 53)]
    assert tuple(row["case_id"] for row in rows) == CASE_IDS
    assert {group: sum(row["case_group"] == group for row in rows) for group in GROUP_COUNTS} == GROUP_COUNTS
    seen_reasons: set[str] = set()
    for row in rows:
        reps = tuple(row[name] for name in TRUTH_COLUMNS[4:8])
        values = tuple(_decode(value) for value in reps)
        presence = "|".join(
            f"{field}={'missing' if value is MISSING_VALUE else 'present'}"
            for field, value in zip(FIELDS, values)
        )
        assert row["presence_representation"] == presence
        outcome, reason, field, blocker = _classify(values)
        assert (row["expected_contract_outcome"], row["expected_reason"], row["expected_first_failing_field"], row["expected_rule_blocking_reason"]) == (outcome, reason, field, blocker)
        assert (row["observed_contract_outcome"], row["observed_reason"], row["observed_first_failing_field"], row["observed_rule_blocking_reason"]) == (outcome, reason, field, blocker)
        assert row["case_passed"] == "true"
        if reason:
            seen_reasons.add(reason)
            assert row["future_admit_013_disposition"] == "not_reached_admit_012_contract_invalid"
        else:
            status, http = values[:2]
            expected = (
                "blocked_not_implemented_here"
                if status == "failure" or not 200 <= http <= 299
                else "pending_integrity_match_checks_not_implemented_here"
            )
            assert row["future_admit_013_disposition"] == expected
    assert seen_reasons == set(REASONS)
    by_id = {row["case_id"]: row for row in rows}
    assert by_id["MULTI_EARLIER_INVALID_LATER_MISSING"]["expected_reason"] == "OBSERVED_SHA256_MISSING"
    assert by_id["MULTI_MISSING_PRECEDENCE"]["expected_reason"] == "DOWNLOAD_RESULT_STATUS_MISSING"
    assert by_id["MULTI_TYPE_FAILURES"]["expected_reason"] == "DOWNLOAD_RESULT_STATUS_TYPE_INVALID"
    assert by_id["MULTI_STATUS_HTTP_INVALID"]["expected_reason"] == "DOWNLOAD_RESULT_STATUS_VALUE_INVALID"
    assert by_id["MULTI_HTTP_CONTENT_INVALID"]["expected_reason"] == "OBSERVED_HTTP_STATUS_RANGE_INVALID"
    assert by_id["MULTI_CONTENT_SHA_INVALID"]["expected_reason"] == "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID"
    assert {by_id[key]["future_admit_013_disposition"] for key in (
        "BOUNDARY_FAILURE_STATUS", "BOUNDARY_VALID_4XX", "BOUNDARY_VALID_5XX_FAILURE"
    )} == {"blocked_not_implemented_here"}


def _expected_issues() -> list[dict[str, str]]:
    path = REPO_ROOT / "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_issue_readiness_inventory.csv"
    rows = list(csv.DictReader(path.read_text().splitlines()))
    assert len(rows) == 16 and tuple(rows[0]) == ISSUE_COLUMNS
    for row in rows:
        if row["issue_id"] in RESOLVED:
            row["status"] = "resolved"
            row["integration_transition"] = TRANSITION
    return rows


def _readiness() -> dict[str, bool]:
    true_keys = (
        "admit_012_preconditions_audited", "admit_012_download_integrity_field_contract_frozen",
        "admit_012_download_result_status_enum_frozen", "admit_012_field_semantics_complete",
        "admit_012_presence_semantics_resolved", "admit_012_validation_precedence_resolved",
        "admit_012_admit_013_field_contract_boundary_frozen", "feature_semantics_audit_required_before_training",
    )
    false_keys = (
        "admit_012_routing_responsibility_resolved", "ready_for_admit_012_standalone_evaluator_interface_implementation",
        "admit_012_rule_logic_implemented", "evaluate_admit_012_implemented", "Admit012EvaluationResult_implemented",
        "admit_012_unified_adapter_contract_frozen", "admit_012_unified_adapter_implemented",
        "admit_012_registered_in_engine", "unified_dispatch_runtime_with_admit_001_to_012_implemented",
        "provider_mapping_validated", "real_provider_evaluation_ready", "ready_for_bulk_download_now",
        "combined_candidate_verdict_implemented", "ready_for_training", "step12d_is_final_training_feature_contract",
    )
    return {**{key: True for key in true_keys}, **{key: False for key in false_keys}}


def _validate_manifest(manifest: dict[str, Any], output: dict[str, bytes]) -> None:
    readiness = _readiness()
    expected = {
        "manifest_schema_version": "covapie_admit_012_download_integrity_field_contract_manifest_v1",
        "project": "CovaPIE", "stage": STAGE, "base_commit": BASE_COMMIT, "base_subject": BASE_SUBJECT,
        "admission_rule_id": "ADMIT_012", "admission_rule_name": "future_download_integrity_fields_required",
        "evidence_source": "future_download_result", "evaluation_phase": "post_download",
        "required_status": "download_status_http_status_content_length_and_sha256_present",
        "blocking_reason": BLOCKING_REASON, "exact4_fields": list(FIELDS), "exact4_presence_required": True,
        "status_enum_version": ENUM_VERSION, "ordered_allowed_download_result_statuses": list(ALLOWED),
        "success_download_result_status_subset": list(SUCCESS), "historical_status_literal_count": len(HISTORY),
        "historical_status_literals_promoted_automatically": False,
        "observed_http_status_contract": {
            "exact_builtin_type": "int", "subclasses_allowed": False, "legal_minimum": 100,
            "legal_maximum": 599, "future_success_minimum": 200, "future_success_maximum": 299,
            "admit_012_executes_success_judgment": False,
        },
        "observed_content_length_bytes_contract": {
            "exact_builtin_type": "int", "subclasses_allowed": False, "legal_minimum": 0,
            "legal_maximum": None, "zero_allowed": True, "recomputed_from_file_inside_classifier": False,
        },
        "observed_sha256_contract": {
            "exact_builtin_type": "str", "subclasses_allowed": False, "length": 64,
            "grammar": "[0-9a-f]{64}", "case_policy": "ASCII_lowercase_only",
            "normalization_allowed": False, "recomputed_from_file_inside_classifier": False,
        },
        "presence_semantics": {
            "order": list(FIELDS), "phase_before_type_value_validation": True,
            "only_private_design_missing_sentinel_means_missing": True,
            "none_empty_zero_false_implicitly_missing": False,
        },
        "validation_precedence": {
            "phase_order": ["presence", "type_and_value"], "presence_order": list(FIELDS),
            "validation_order": list(FIELDS), "within_field_order": ["exact_type", "enum_range_or_grammar"],
        },
        "reason_vocabulary": list(REASONS), "contract_outcomes": ["contract_valid", "missing", "invalid"],
        "admit_012_responsibilities": [
            "Exact4_presence", "exact_builtin_types", "status_enum_membership", "HTTP_structural_range",
            "content_length_structural_range", "SHA256_representation_grammar", "deterministic_reason_precedence",
        ],
        "admit_012_non_responsibilities": [
            "status_success_judgment", "HTTP_2xx_judgment", "content_length_header_or_file_match",
            "SHA256_expected_digest_match", "candidate_materialization_admission",
        ],
        "future_admit_013_responsibilities_not_implemented_here": [
            "non_success_status_fail_closed", "non_2xx_fail_closed", "integrity_mismatch_fail_closed",
            "combined_download_admission_verdict",
        ],
        "admit_012_routing_responsibility_resolved": False,
        "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED": "open", "ADMIT_012_RESULT_CONTRACT_UNRESOLVED": "open",
        "design_classifier_only": True, "formal_evaluator_implemented": False,
        "formal_result_contract_defined": False, "unified_adapter_or_runtime_changed": False,
        "source_count": 29, "source_path_list_sha256": PATH_LIST_SHA,
        "source_path_sha256_pairs_sha256": PATH_PAIR_SHA, "output_files": list(FILES), "output_file_count": 6,
        "row_counts": {"field_contract": 4, "status_enum_and_history": 16, "truth_matrix": 52, "source_boundary": 29, "issue_inventory": 16},
        "truth_matrix_group_counts": GROUP_COUNTS, "resolved_issue_ids": sorted(RESOLVED),
        "issue_integration_transition": TRANSITION, "required_open_issue_ids": sorted(OPEN_REQUIRED),
        "authorized_admit_012_download_execution_count": 0,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": "design_covapie_admit_012_formal_evaluator_interface_contract_v1",
        "readiness": readiness,
        "safety": {"network": False, "raw": False, "provider_mapping": False, "real_download": False, "model_or_checkpoint": False, "runtime_change": False, "training": False},
        "renameat2_policy": "RENAME_NOREPLACE_required;_EINVAL_fails_closed_without_os.replace_fallback",
        "output_sha256": {name: hashlib.sha256(output[name]).hexdigest() for name in FILES[:-1]},
        "all_checks_passed": True,
    }
    expected.update(readiness)
    assert manifest == expected


def validate(root: Path = REPO_ROOT / OUTPUT_ROOT, enforce_frozen_hashes: bool = True) -> None:
    output = _read_outputs(root)
    if enforce_frozen_hashes:
        assert FROZEN_SHA256 and set(FROZEN_SHA256) == set(FILES)
        assert {name: hashlib.sha256(output[name]).hexdigest() for name in FILES} == FROZEN_SHA256
    contract = _rows(output[CONTRACT_FILE], CONTRACT_COLUMNS)
    enum = _rows(output[ENUM_FILE], ENUM_COLUMNS)
    truth = _rows(output[TRUTH_FILE], TRUTH_COLUMNS)
    sources = _rows(output[SOURCE_FILE], SOURCE_COLUMNS)
    issues = _rows(output[ISSUE_FILE], ISSUE_COLUMNS)
    manifest = json.loads(output[MANIFEST_FILE])
    assert contract == _expected_contract_rows()
    _validate_enum(enum)
    _validate_truth(truth)
    _validate_base_and_sources(sources)
    assert issues == _expected_issues()
    by_id = {row["issue_id"]: row for row in issues}
    assert all(by_id[issue]["status"] == "resolved" and by_id[issue]["integration_transition"] == TRANSITION for issue in RESOLVED)
    assert all(by_id[issue]["status"] == "open" for issue in OPEN_REQUIRED)
    assert by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    _validate_manifest(manifest, output)
    production = (REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py").read_text()
    assert "def evaluate_admit_012" not in production
    assert "class Admit012EvaluationResult" not in production
    assert "def register_" not in production and "dispatcher" not in production.lower().replace("dispatcher route", "")


def main() -> int:
    validate()
    print(json.dumps({"output_sha256": FROZEN_SHA256, "stage": STAGE, "status": "passed"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
