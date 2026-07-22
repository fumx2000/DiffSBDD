#!/usr/bin/env python3
"""Independent checker for the ADMIT_012 formal-interface design contract."""
from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "727ef05f7e7bb4d7bda4eedd2ae0f3da2b4e993e"
BASE_SUBJECT = "add CovaPIE ADMIT_012 download integrity field contract v1"
STAGE = "covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
PRODUCTION_PATH = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate.py"
FIELD_STAGE = REPO_ROOT / "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1"

FIELDS = (
    "download_result_status", "observed_http_status",
    "observed_content_length_bytes", "observed_sha256",
)
CONTEXTS = (
    "allowed_download_result_statuses", "successful_http_status_contract",
    "content_length_contract", "sha256_format_contract",
)
RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_download_result_record", "validated_download_result_fields",
    "consumed_download_result_fields", "consumed_context_items", "evaluator_io_used",
)
ALLOWED = ("success", "failure")
HTTP_CONTRACT = (
    ("legal_minimum", 100), ("legal_maximum", 599),
    ("future_success_minimum", 200), ("future_success_maximum", 299),
    ("admit_012_executes_success_judgment", False),
)
CONTENT_CONTRACT = (
    ("legal_minimum", 0), ("legal_maximum", None), ("zero_allowed", True),
    ("recomputed_from_file_inside_evaluator", False),
)
SHA_CONTRACT = (
    ("length", 64), ("grammar", "[0-9a-f]{64}"),
    ("case_policy", "ASCII_lowercase_only"), ("normalization_allowed", False),
    ("recomputed_from_file_inside_evaluator", False),
)
CONTEXT_VALUES = (ALLOWED, HTTP_CONTRACT, CONTENT_CONTRACT, SHA_CONTRACT)
MISSING_REASONS = (
    "DOWNLOAD_RESULT_STATUS_MISSING", "OBSERVED_HTTP_STATUS_MISSING",
    "OBSERVED_CONTENT_LENGTH_BYTES_MISSING", "OBSERVED_SHA256_MISSING",
)
TYPE_REASONS = (
    "DOWNLOAD_RESULT_STATUS_TYPE_INVALID", "OBSERVED_HTTP_STATUS_TYPE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID", "OBSERVED_SHA256_TYPE_INVALID",
)
VALUE_REASONS = (
    "DOWNLOAD_RESULT_STATUS_VALUE_INVALID", "OBSERVED_HTTP_STATUS_RANGE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID", "OBSERVED_SHA256_FORMAT_INVALID",
)
FIELD_REASONS = (
    *MISSING_REASONS,
    *(reason for index in range(4) for reason in (TYPE_REASONS[index], VALUE_REASONS[index])),
)
CONTEXT_REASONS = (
    "ALLOWED_DOWNLOAD_RESULT_STATUSES_TYPE_INVALID",
    "ALLOWED_DOWNLOAD_RESULT_STATUSES_CONTENT_INVALID",
    "SUCCESSFUL_HTTP_STATUS_CONTRACT_TYPE_INVALID",
    "SUCCESSFUL_HTTP_STATUS_CONTRACT_CONTENT_INVALID",
    "CONTENT_LENGTH_CONTRACT_TYPE_INVALID",
    "CONTENT_LENGTH_CONTRACT_CONTENT_INVALID",
    "SHA256_FORMAT_CONTRACT_TYPE_INVALID",
    "SHA256_FORMAT_CONTRACT_CONTENT_INVALID",
)
REASONS = ("", *FIELD_REASONS, *CONTEXT_REASONS)

FILES = (
    "covapie_admit_012_formal_evaluator_interface_and_result_contract.csv",
    "covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv",
    "covapie_admit_012_formal_evaluator_interface_truth_matrix.csv",
    "covapie_admit_012_formal_evaluator_interface_source_boundary_audit.csv",
    "covapie_admit_012_formal_evaluator_interface_issue_readiness_inventory.csv",
    "covapie_admit_012_formal_evaluator_interface_contract_manifest.json",
)
CONTRACT_FILE, ROUTING_FILE, TRUTH_FILE, SOURCE_FILE, ISSUE_FILE, MANIFEST_FILE = FILES
FROZEN_SHA256 = {
    CONTRACT_FILE: "682192b492979d9b6114381cbfc02d57c349e3cd8db2541a01177235d34c04e6",
    ROUTING_FILE: "44709c3a679368476c87bcd97dafa2f9cf9bddb4af534c6eb950c565d0919aec",
    TRUTH_FILE: "cc848914ea24b376e29c477c4c0b5e8d32d6fc7caee11873f7a73c4bd207d6db",
    SOURCE_FILE: "4ba05848ba8fe437603d71f06d4b1161447c82c5ab14d838ff62470872c25d82",
    ISSUE_FILE: "bac586f54afac5a860a32ed161b6b8f41210b6ae06eb29f368045f10b3ac81e5",
    MANIFEST_FILE: "2845c2623a01087af8842177f4502402d0a8875a77ce12c6a49e2f77c60dae01",
}
FROZEN_TRUTH_INPUT_SHA256 = "8df0948aed25b07d79fdfc14f24c17fb0d315ca114e5fa8cb712a4889f0e48b2"

CONTRACT_COLUMNS = (
    "contract_order", "contract_section", "section_order", "public_name", "formal_type",
    "default_or_missing_behavior", "required", "source_envelope", "validation_rule",
    "invariant", "contract_passed",
)
ROUTING_COLUMNS = (
    "route_consumption_order", "case_id", "contract_kind", "source_envelope", "source_key",
    "formal_parameter", "required", "missing_representation", "consumed_on_case",
    "validated_on_case", "adapter_responsibility", "evaluator_responsibility", "route_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "assertion_kind",
    "download_result_status_representation", "observed_http_status_representation",
    "observed_content_length_bytes_representation", "observed_sha256_representation",
    "allowed_download_result_statuses_representation",
    "successful_http_status_contract_representation", "content_length_contract_representation",
    "sha256_format_contract_representation", "expected_outcome", "expected_reason",
    "expected_canonical_download_result_record", "expected_validated_download_result_fields",
    "expected_consumed_download_result_fields", "expected_consumed_context_items",
    "expected_evaluator_io_used", "observed_design_result", "case_passed",
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
    "src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py": "92d6ab08c4e9fa4bd448895687c897f06a596d4fb73a2e9cf7e88ffebaa6448f",
    "scripts/check_covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1.py": "bd2fda1bb9f1d623fb33037df2f7d569f366a8c3f66df69b6c4d348f65057cd7",
    "tests/test_covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1.py": "270d6eb0a5b21f521d3568044179572bddad8f962cc81cded431b22d318470e0",
    "docs/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1_summary.md": "b9351a65f4065bfcd5f06f275c0c26f3f83c357de66744d4ed8d03d0cc05f345",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract.csv": "03aef0a14257d9a2c028fcc3dd84c161c29b09bca1a1c71456edc66e2e73c9ce",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_result_status_enum.csv": "4c016e8c325ce6a422dff618ae166ec4f42243cc0d1fbf8f6a722c13f63139f6",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_validation_truth_matrix.csv": "766506f8c0bf2d7734b9c379c9437e1a48a2117873f7e974325b00ab685a39e1",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_contract_source_boundary_audit.csv": "73393c6c540cb00d040fa8154948f544e445bbcb63323d9f463709c7ee8b16ed",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_contract_issue_readiness_inventory.csv": "dfe8e16d741548323cddfcdf3db86bdf0c098d6bb2a86fcb8ec0914ebe924855",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract_manifest.json": "9fadff44ae15474783df2a3997c45f2c4d57a41ca2adbab0b40f1d890f51039f",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_formal_evaluator_preconditions_manifest.json": "712caa27add06784db5cfe2e59a65952ae4b1c5a369ff43772d8e4f95b18c4de",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_formal_evaluator_precondition_matrix.csv": "c667c5f195a1d834672564835380896553339833041d17cc2f689db23f9d319f",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_issue_readiness_inventory.csv": "5ebe9332137bfa9c7804c82041ff695b3379ba505a5eb006fa5c7798510e8529",
    "docs/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_preconditions_audit_v1_summary.md": "76f93106cf52b3f205d1cce0daa2c64999c16f0283c878ea6a401b14c8b93d91",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv": "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py": "6fd3727234b4b3f637fa5812c78421ec944238518702bc7f9d0d57a654d9a46d",
    "scripts/check_covapie_bulk_download_admission_admit_006_rule_logic_interface_v1.py": "a26c48830cccf580987bade69c375ccb2a2a18add65abe15c7e3dffe2cf74c27",
    "tests/test_covapie_bulk_download_admission_admit_006_rule_logic_interface_v1.py": "a2ec0e56f53bf6eb6644e007505318efed4bc7d84cd83fa31ae30a9696c6e0e3",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_006_rule_logic_interface_v1/covapie_admit_006_rule_logic_interface_manifest.json": "921356eaa15f40fed925d11d73a6fbb868b4c881828c358fb35fde168b8c33f8",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py": "73adad5c617ecae0dc5772d04ae5d777970a3d2a8c8963c3d2c4c4b19cbf85fc",
    "scripts/check_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1.py": "72f33b9371c4eda533374e0535ba0da22467459da6a6488147e58ad680b7c7f1",
    "tests/test_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1.py": "10c8a798e99a9e8d8b4adab86f06ba259c1d721fac47dabbf4941850ff70581c",
    "docs/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1_summary.md": "abc525efa000206f1c3c80e56f73055c85895b0011dbf13f5a684be13a65243d",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_contract.csv": "7624bfda25b7aca2a3db11fab18a883c52dee0e598a295ada0b0676a1847aea2",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_manifest.json": "a3c053d7b4af149b67b818721f11bb6920b5de00d5d15fb5ec176e10e5a70c3c",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate.py": "93e6e726092f8c3e66b19c7ab4c6d363d47962c07eeb694c7237b2b0d5a31346",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract.csv": "4b4b41295364fcb83f807c054e2e561ca2c4a31fbf27fd55d04607f3c127c2cc",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract_manifest.json": "d5ad2622b5182898c418d774e4c0deb33fc2fb643caaa5da0507cabb3824f884",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py": "ca8e64897b30f961d999d37ce8af5eb985ddf34f332af40c29bf2142bad6e2c8",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_contract.csv": "9616573151091786f07b3c4d1b6c8343a1ceb796f439e495023abd2f3ad37626",
}
SOURCE_PATHS = tuple(SOURCE_SHA256)
PATH_LIST_SHA = "864f8b91f37d36dff28c28b8567e34b658ad5ec5bbe6bfeaf14e085f5217a501"
PATH_PAIR_SHA = "bf716e84b80a0ec51a2b41a6763fb7151969efb65b915b77590617dcd9dc272d"


class _Missing:
    pass


MISSING = _Missing()


class _StrSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _TupleSubclass(tuple):
    pass


class _PairSubclass(tuple):
    pass


def _git(arguments: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=text, check=False)


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode


def _read_outputs(root: Path) -> dict[str, bytes]:
    parent_identity = _identity(os.lstat(root.parent))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    assert stat.S_ISDIR(root_item.st_mode) and not stat.S_ISLNK(root_item.st_mode)
    assert root.resolve(strict=True) == root and {entry.name for entry in root.iterdir()} == set(FILES)
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        assert _identity(os.fstat(descriptor)) == root_identity
        output = {}
        identities = {}
        for name in FILES:
            item = os.lstat(root / name)
            identity = _identity(item)
            identities[name] = identity
            assert stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode)
            leaf = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=descriptor)
            try:
                assert _identity(os.fstat(leaf)) == identity
                chunks = []
                while True:
                    chunk = os.read(leaf, 1 << 16)
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


def _rows(data: bytes, columns: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(data.decode(), newline=""))
    assert tuple(reader.fieldnames or ()) == columns
    rows = list(reader)
    assert all(tuple(row) == columns and None not in row.values() for row in rows)
    return rows


def _expected_contract_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(section: str, name: str, type_name: str, default: str, required: bool,
            source: str, validation: str, invariant: str) -> None:
        rows.append({
            "contract_order": str(len(rows) + 1), "contract_section": section,
            "section_order": str(1 + sum(row["contract_section"] == section for row in rows)),
            "public_name": name, "formal_type": type_name,
            "default_or_missing_behavior": default, "required": str(required).lower(),
            "source_envelope": source, "validation_rule": validation,
            "invariant": invariant, "contract_passed": "true",
        })

    for name in FIELDS:
        add("signature_parameter", name, "object", "private_singleton_missing_default", False,
            "download_result_context", "keyword_only; exact field contract", "Exact4 field order; no Mapping record")
    for name in CONTEXTS:
        add("signature_parameter", name, "object", "no_default", True, "evaluation_context",
            "keyword_only; required by Python signature", "missing is signature failure, not result semantics")
    types = (
        "exact tuple[str,str]", "exact tuple[exact tuple[str,int_or_bool],...]",
        "exact tuple[exact tuple[str,int_or_bool_or_None],...]",
        "exact tuple[exact tuple[str,int_or_bool],...]",
    )
    for name, type_name, value in zip(CONTEXTS, types, CONTEXT_VALUES, strict=True):
        add("policy_context_shape", name, type_name, "not_applicable", True, "evaluation_context",
            repr(value), "exact outer type, pair shape/order/key/value/type; no normalization")
    result_types = ("exact str", "exact str", "exact bool", "exact bool", "exact str", "exact tuple", "exact tuple", "exact tuple[str,...]", "exact tuple[str,...]", "exact bool")
    for name, type_name in zip(RESULT_FIELDS, result_types, strict=True):
        add("result_field", name, type_name, "not_applicable", True, "standalone_evaluator_result",
            "Exact10 ordered field", "see frozen outcome/canonical/validated/consumed invariants")
    invariants = (
        ("passed_iff_outcome", "passed == (outcome == 'passed')"),
        ("blocks_iff_not_passed", "blocks_candidate == (outcome != 'passed')"),
        ("reason_empty_iff_passed", "reason empty iff outcome passed"),
        ("missing_outcome", "field missing reasons imply blocked"),
        ("field_invalid_outcome", "field type/value reasons imply invalid"),
        ("context_invalid_outcome", "context reasons imply invalid"),
        ("canonical_shape", "empty on field failure; complete Exact4 on context failure/pass"),
        ("validated_prefix", "ordered prefix excluding failure field"),
        ("consumption_prefix", "fields/contexts reflect actual ordered consumption"),
        ("io", "evaluator_io_used is exact false"),
    )
    for name, rule in invariants:
        add("outcome_invariant", name, "invariant", "not_applicable", True, "result_contract", rule, rule)
    for reason in REASONS:
        add("reason_vocabulary", reason if reason else "<empty>", "exact str", "not_applicable", True,
            "result_contract", "closed vocabulary member", "no catch-all reason")
    precedence = [
        *(f"presence:{name}" for name in FIELDS), *(f"type_then_value:{name}" for name in FIELDS),
        *(f"context_type:{name}" for name in CONTEXTS), *(f"context_content:{name}" for name in CONTEXTS),
        "passed",
    ]
    for item in precedence:
        add("validation_precedence", item, "precedence_step", "not_applicable", True,
            "standalone_evaluator", item, "first failure returns immediately")
    return rows


def _expected_routing_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(case_id: str, kind: str, envelope: str, key: str, parameter: str, required: bool,
            missing: str, consumed: str, validated: str, adapter: str, evaluator: str) -> None:
        rows.append({
            "route_consumption_order": str(len(rows) + 1), "case_id": case_id,
            "contract_kind": kind, "source_envelope": envelope, "source_key": key,
            "formal_parameter": parameter, "required": str(required).lower(),
            "missing_representation": missing, "consumed_on_case": consumed,
            "validated_on_case": validated, "adapter_responsibility": adapter,
            "evaluator_responsibility": evaluator, "route_passed": "true",
        })

    for name in FIELDS:
        add(f"ROUTE_{name.upper()}", "route", "download_result_context", name, name, True,
            "private_missing_singleton", "case_dependent_field_prefix", "case_dependent_validated_prefix",
            "extract exactly once and pass by identity", "presence and exact field validation")
    for name in CONTEXTS:
        add(f"ROUTE_{name.upper()}", "route", "evaluation_context", name, name, True,
            "adapter routing failure before call", "case_dependent_context_prefix", "not_applicable",
            "require key and pass by identity", "exact context type/content validation")
    for envelope in ("candidate_record", "batch_context", "stage_authorization_context"):
        add(f"FORBIDDEN_{envelope.upper()}", "forbidden_route", envelope, "*", "", False, "not_applicable",
            "none", "none", "must not source ADMIT_012 formal parameters", "does not consume envelope")
    for index, name in enumerate(FIELDS):
        add(f"MISSING_{name.upper()}", "consumption_case", "standalone_evaluator", name, name, True,
            "private_missing_singleton", "|".join(FIELDS[:index + 1]), "", "route Exact4 before call",
            "blocked at first missing during presence phase")
    for index, name in enumerate(FIELDS):
        add(f"INVALID_{name.upper()}", "consumption_case", "standalone_evaluator", name, name, True,
            "present_invalid", "|".join(FIELDS), "|".join(FIELDS[:index]), "route Exact4 before call",
            "invalid at first type/value failure")
    for index, name in enumerate(CONTEXTS):
        add(f"INVALID_{name.upper()}", "consumption_case", "standalone_evaluator", name, name, True,
            "present_invalid", "|".join(CONTEXTS[:index + 1]), "|".join(FIELDS),
            "route Exact4 contexts before call", "invalid at first context type/content failure")
    for case_id in ("PASSED", "PASSED_FAILURE_STATUS", "PASSED_HTTP_4XX", "PASSED_HTTP_5XX"):
        add(case_id, "consumption_case", "standalone_evaluator", "Exact4", "Exact8", True, "all_present",
            "|".join((*FIELDS, *CONTEXTS)), "|".join(FIELDS), "route only download/evaluation envelopes",
            "passed; success/2xx judgment belongs to ADMIT_013")
    return rows


def _decode(value: str) -> object:
    if value == "<MISSING>":
        return MISSING
    if value == "<object>":
        return object()
    if value.startswith("<str-subclass:"):
        return _StrSubclass(ast.literal_eval(value[14:-1]))
    if value.startswith("<int-subclass:"):
        return _IntSubclass(ast.literal_eval(value[14:-1]))
    if value.startswith("<tuple-subclass:"):
        return _TupleSubclass(ast.literal_eval(value[16:-1]))
    if value.startswith("<tuple-member-str-subclass:"):
        index_text, literal = value[27:-1].split(":", 1)
        index = int(index_text)
        plain = list(ast.literal_eval(literal))
        plain[index] = _StrSubclass(plain[index])
        return tuple(plain)
    if value.startswith("<tuple-pair-subclass:"):
        index_text, literal = value[21:-1].split(":", 1)
        index = int(index_text)
        plain = list(ast.literal_eval(literal))
        plain[index] = _PairSubclass(plain[index])
        return tuple(plain)
    if value.startswith("<regex:"):
        return re.compile(ast.literal_eval(value[7:-1]))
    return ast.literal_eval(value)


def _context_reason(value: object, expected: tuple[object, ...], index: int) -> str:
    if type(value) is not tuple:
        return CONTEXT_REASONS[index * 2]
    if len(value) != len(expected):
        return CONTEXT_REASONS[index * 2 + 1]
    if index == 0:
        valid = all(type(item) is str for item in value) and value == expected
    else:
        valid = all(
            type(pair) is tuple and len(pair) == 2 and type(pair[0]) is str
            and type(pair[1]) is type(expected_pair[1]) and pair == expected_pair
            for pair, expected_pair in zip(value, expected, strict=True)
        )
    return "" if valid else CONTEXT_REASONS[index * 2 + 1]


def _classify(values: tuple[object, ...], contexts: tuple[object, ...]) -> tuple[object, ...]:
    for index, value in enumerate(values):
        if value is MISSING:
            return ("ADMIT_012", "blocked", False, True, MISSING_REASONS[index], (), (), FIELDS[:index + 1], (), False)
    validators = (
        lambda value: (type(value) is str, value in ALLOWED if type(value) is str else False),
        lambda value: (type(value) is int, 100 <= value <= 599 if type(value) is int else False),
        lambda value: (type(value) is int, value >= 0 if type(value) is int else False),
        lambda value: (type(value) is str, re.fullmatch(r"[0-9a-f]{64}", value, flags=re.ASCII) is not None if type(value) is str else False),
    )
    validated = []
    for index, (value, validator) in enumerate(zip(values, validators, strict=True)):
        exact_type, legal = validator(value)
        if not exact_type or not legal:
            reason = TYPE_REASONS[index] if not exact_type else VALUE_REASONS[index]
            return ("ADMIT_012", "invalid", False, True, reason, (), tuple(validated), FIELDS, (), False)
        validated.append((FIELDS[index], value))
    canonical = tuple(validated)
    for index, (value, expected) in enumerate(zip(contexts, CONTEXT_VALUES, strict=True)):
        reason = _context_reason(value, expected, index)
        if reason:
            return ("ADMIT_012", "invalid", False, True, reason, canonical, canonical, FIELDS, CONTEXTS[:index + 1], False)
    return ("ADMIT_012", "passed", True, False, "", canonical, canonical, FIELDS, CONTEXTS, False)


CONTEXT_CASE_IDS = (
    "ALLOWED_OUTER_LIST", "ALLOWED_TUPLE_SUBCLASS", "ALLOWED_MEMBER_SUBCLASS",
    "ALLOWED_DUPLICATE", "ALLOWED_REORDERED", "ALLOWED_EXTRA", "ALLOWED_MISSING",
    *(f"{name}_{suffix}" for name in ("HTTP", "CONTENT", "SHA") for suffix in (
        "OUTER_LIST", "TUPLE_SUBCLASS", "PAIR_LIST", "PAIR_TUPLE_SUBCLASS", "WRONG_KEY",
        "KEY_ORDER", "WRONG_VALUE", "BOOL_INT_MIX", "EXTRA_PAIR", "MISSING_PAIR",
    )),
    "SHA_MAPPING", "SHA_REGEX",
)
CROSS_CASE_IDS = (
    "CROSS_MISSING_FIELD_INVALID_CONTEXT", "CROSS_FIELD_TYPE_CONTEXT",
    "CROSS_FIELD_VALUE_CONTEXT", "CROSS_VALID_MULTIPLE_CONTEXT", "CROSS_EARLIER_CONTEXT",
    "CROSS_CONTEXT_TYPE_OVER_CONTENT",
)
NEGATIVE_CASE_IDS = (
    "WRONG_RESULT_FIELD_ORDER", "WRONG_OUTCOME_BOOL", "WRONG_CANONICAL_SHAPE",
    "PARTIAL_CANONICAL_RECORD", "VALIDATED_NOT_PREFIX", "CONSUMED_ORDER_DRIFT",
    "EVALUATOR_IO_TRUE", "UNKNOWN_REASON",
)
NEGATIVE_REJECTIONS = {
    "WRONG_RESULT_FIELD_ORDER": "RESULT_CONTRACT_REJECTED:TypeError",
    "WRONG_OUTCOME_BOOL": "RESULT_CONTRACT_REJECTED:ValueError",
    "WRONG_CANONICAL_SHAPE": "RESULT_CONTRACT_REJECTED:TypeError",
    "PARTIAL_CANONICAL_RECORD": "RESULT_CONTRACT_REJECTED:ValueError",
    "VALIDATED_NOT_PREFIX": "RESULT_CONTRACT_REJECTED:ValueError",
    "CONSUMED_ORDER_DRIFT": "RESULT_CONTRACT_REJECTED:ValueError",
    "EVALUATOR_IO_TRUE": "RESULT_CONTRACT_REJECTED:ValueError",
    "UNKNOWN_REASON": "RESULT_CONTRACT_REJECTED:ValueError",
}


def _check_truth(rows: list[dict[str, str]]) -> None:
    predecessor = list(csv.DictReader((FIELD_STAGE / "covapie_admit_012_download_integrity_validation_truth_matrix.csv").read_text().splitlines()))
    expected_ids = tuple(f"FIELD52_{row['case_id']}" for row in predecessor) + CONTEXT_CASE_IDS + CROSS_CASE_IDS + NEGATIVE_CASE_IDS
    assert len(rows) == len(expected_ids) == 105
    assert tuple(row["case_id"] for row in rows) == expected_ids
    assert [row["case_order"] for row in rows] == [str(index) for index in range(1, 106)]
    input_columns = ("case_id", *TRUTH_COLUMNS[4:12])
    digest_payload = [[row[column] for column in input_columns] for row in rows]
    assert hashlib.sha256(json.dumps(digest_payload, separators=(",", ":")).encode()).hexdigest() == FROZEN_TRUTH_INPUT_SHA256
    fixed_context_reps = tuple(repr(value) for value in CONTEXT_VALUES)
    for index, prior in enumerate(predecessor):
        row = rows[index]
        assert tuple(row[column] for column in TRUTH_COLUMNS[4:8]) == tuple(prior[column] for column in TRUTH_COLUMNS[4:8])
        assert tuple(row[column] for column in TRUTH_COLUMNS[8:12]) == fixed_context_reps
    for row in rows:
        values = tuple(_decode(row[column]) for column in TRUTH_COLUMNS[4:8])
        contexts = tuple(_decode(row[column]) for column in TRUTH_COLUMNS[8:12])
        expected = _classify(values, contexts)
        expected_projection = (
            expected[1], expected[4], repr(expected[5]), repr(expected[6]), repr(expected[7]),
            repr(expected[8]), str(expected[9]).lower(),
        )
        observed_projection = (
            row["expected_outcome"], row["expected_reason"],
            row["expected_canonical_download_result_record"],
            row["expected_validated_download_result_fields"],
            row["expected_consumed_download_result_fields"], row["expected_consumed_context_items"],
            row["expected_evaluator_io_used"],
        )
        assert observed_projection == expected_projection and row["case_passed"] == "true"
        if row["assertion_kind"] == "formal_projection":
            assert ast.literal_eval(row["observed_design_result"]) == expected
        else:
            assert row["case_id"] in NEGATIVE_REJECTIONS
            assert row["observed_design_result"] == NEGATIVE_REJECTIONS[row["case_id"]]


def _validate_sources(rows: list[dict[str, str]]) -> None:
    subject = _git(["show", "-s", "--format=%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    assert subject.returncode == 0 and subject.stdout.strip() == BASE_SUBJECT and ancestor.returncode == 0
    assert len(rows) == len(SOURCE_PATHS) == 30
    assert hashlib.sha256(json.dumps(list(SOURCE_PATHS), separators=(",", ":")).encode()).hexdigest() == PATH_LIST_SHA
    assert hashlib.sha256(json.dumps([[path, SOURCE_SHA256[path]] for path in SOURCE_PATHS], separators=(",", ":")).encode()).hexdigest() == PATH_PAIR_SHA
    for index, (row, relative) in enumerate(zip(rows, SOURCE_PATHS, strict=True), 1):
        path = Path(relative)
        expected = SOURCE_SHA256[relative]
        assert row["source_order"] == str(index) and row["source_relative_path"] == relative
        assert row["expected_sha256"] == expected
        assert {row[key] for key in ("base_tree_sha256", "filesystem_sha256", "frozen_snapshot_sha256")} == {expected}
        assert all(row[key] == "true" for key in SOURCE_COLUMNS[8:])
        assert not path.is_absolute() and ".." not in path.parts and path.parts[:2] != ("data", "raw") and path.parts[0] != "checkpoints"
        absolute = REPO_ROOT / path
        item = os.lstat(absolute)
        assert stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode) and absolute.resolve(strict=True) == absolute
        tree = _git(["ls-tree", BASE_COMMIT, "--", relative])
        tracked = _git(["ls-files", "--error-unmatch", "--", relative])
        head, separator, tree_path = tree.stdout.partition("\t")
        parts = head.split()
        assert tree.returncode == tracked.returncode == 0 and tracked.stdout.splitlines() == [relative]
        assert separator and tree_path.strip() == relative and len(parts) == 3 and parts[0] in {"100644", "100755"} and parts[1] == "blob"
        assert row["base_tree_mode"] == parts[0]
        before = _identity(item)
        descriptor = os.open(absolute, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            assert _identity(os.fstat(descriptor)) == before
            chunks = []
            while True:
                chunk = os.read(descriptor, 1 << 16)
                if not chunk:
                    break
                chunks.append(chunk)
            assert _identity(os.fstat(descriptor)) == before == _identity(os.lstat(absolute))
        finally:
            os.close(descriptor)
        data = b"".join(chunks)
        base = _git(["show", f"{BASE_COMMIT}:{relative}"], text=False)
        assert base.returncode == 0 and hashlib.sha256(data).hexdigest() == expected
        assert hashlib.sha256(base.stdout).hexdigest() == expected


RESOLVED_INTERFACE = {
    "ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED",
    "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED", "ADMIT_012_RESULT_CONTRACT_UNRESOLVED",
}
FIELD_RESOLVED = {
    "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED", "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
    "ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED", "ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED",
}
OPEN_REQUIRED = {
    "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
    "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
}
TRANSITION = "admit_012_formal_evaluator_interface_contract_frozen_v1"


def _expected_issues() -> list[dict[str, str]]:
    rows = list(csv.DictReader((FIELD_STAGE / "covapie_admit_012_download_integrity_contract_issue_readiness_inventory.csv").read_text().splitlines()))
    for row in rows:
        if row["issue_id"] in RESOLVED_INTERFACE:
            row["status"] = "resolved"
            row["integration_transition"] = TRANSITION
    return rows


TRUE_READINESS = (
    "admit_012_preconditions_audited", "admit_012_download_integrity_field_contract_frozen",
    "admit_012_download_result_status_enum_frozen", "admit_012_field_semantics_complete",
    "admit_012_presence_semantics_resolved", "admit_012_validation_precedence_resolved",
    "admit_012_routing_responsibility_resolved", "admit_012_standalone_signature_frozen",
    "admit_012_formal_result_contract_frozen", "admit_012_formal_evaluator_interface_contract_frozen",
    "ready_for_admit_012_standalone_evaluator_interface_implementation",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_012_rule_logic_implemented", "evaluate_admit_012_implemented",
    "Admit012EvaluationResult_implemented", "admit_012_unified_adapter_contract_frozen",
    "admit_012_unified_adapter_implemented", "admit_012_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_012_implemented", "provider_mapping_validated",
    "real_provider_evaluation_ready", "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented", "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


def _check_manifest(manifest: dict[str, Any], output: dict[str, bytes], contract_count: int,
                    routing_count: int, truth_rows: list[dict[str, str]]) -> None:
    readiness = {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}
    groups = {group: sum(row["case_group"] == group for row in truth_rows) for group in sorted({row["case_group"] for row in truth_rows})}
    expected = {
        "manifest_schema_version": "covapie_admit_012_formal_evaluator_interface_contract_manifest_v1",
        "project": "CovaPIE", "stage": STAGE, "base_commit": BASE_COMMIT, "base_subject": BASE_SUBJECT,
        "admission_rule_id": "ADMIT_012",
        "routing_responsibility": {
            "download_result_context": list(FIELDS), "evaluation_context": list(CONTEXTS),
            "forbidden_sources": ["candidate_record", "batch_context", "stage_authorization_context", "filesystem", "network", "raw", "provider", "download_execution_inside_evaluator"],
        },
        "future_public_signature": "evaluate_admit_012(*, download_result_status: object = _MISSING, observed_http_status: object = _MISSING, observed_content_length_bytes: object = _MISSING, observed_sha256: object = _MISSING, allowed_download_result_statuses: object, successful_http_status_contract: object, content_length_contract: object, sha256_format_contract: object) -> Admit012EvaluationResult",
        "signature_parameters": list((*FIELDS, *CONTEXTS)), "signature_all_keyword_only": True,
        "signature_varargs": False, "signature_varkw": False,
        "field_missing_defaults_private_singleton": True, "policy_context_parameters_required": True,
        "policy_context_values": {name: repr(value) for name, value in zip(CONTEXTS, CONTEXT_VALUES, strict=True)},
        "outcome_vocabulary": ["passed", "blocked", "invalid"], "reason_vocabulary": list(REASONS),
        "context_reason_vocabulary": list(CONTEXT_REASONS), "result_type": "Admit012EvaluationResult",
        "result_fields": list(RESULT_FIELDS), "result_field_count": 10,
        "validation_phase_order": ["Exact4_presence", "Exact4_type_value", "policy_context_type_content", "passed"],
        "field_order": list(FIELDS), "context_order": list(CONTEXTS),
        "canonical_record_representation": "exact ordered tuple of Exact4 exact pair tuples",
        "validated_representation": "ordered Exact4 pair-tuple prefix excluding failing field",
        "consumption_semantics": "actual ordered field/context prefixes; all fields consumed after complete presence phase",
        "failure_status_4xx_5xx_outcome": "passed", "admit_013_success_or_integrity_judgment_executed": False,
        "design_oracle": "classify_admit_012_formal_evaluator_interface_design",
        "design_result_type": "Admit012EvaluationResultContractDesign",
        "formal_evaluator_implemented": False, "formal_result_type_defined": False,
        "unified_adapter_or_runtime_changed": False, "admit_013_implemented": False,
        "source_count": 30, "source_path_list_sha256": PATH_LIST_SHA,
        "source_path_sha256_pairs_sha256": PATH_PAIR_SHA,
        "output_files": list(FILES), "output_file_count": 6,
        "row_counts": {"interface_result_contract": contract_count, "routing_consumption": routing_count,
                       "truth_matrix": 105, "field52_projection": 52, "source_boundary": 30,
                       "issue_inventory": 16},
        "truth_matrix_group_counts": groups,
        "resolved_issue_ids": sorted(FIELD_RESOLVED | RESOLVED_INTERFACE),
        "issue_integration_transition": TRANSITION, "required_open_issue_ids": sorted(OPEN_REQUIRED),
        "readiness": readiness, **readiness,
        "feature_semantics_audit_required_before_training": True,
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": "implement_covapie_admit_012_standalone_evaluator_interface_v1",
        "authorized_admit_012_download_execution_count": 0,
        "safety": {"network": False, "raw": False, "provider_mapping": False, "real_download": False,
                   "model_or_checkpoint": False, "runtime_change": False, "training": False},
        "renameat2_policy": "RENAME_NOREPLACE_required;_EINVAL_fails_closed_without_os.replace_fallback",
        "output_sha256": {name: hashlib.sha256(output[name]).hexdigest() for name in FILES[:-1]},
        "all_checks_passed": True,
    }
    assert manifest == expected


def _check_production_design_only() -> None:
    source = PRODUCTION_PATH.read_text()
    tree = ast.parse(source)
    functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    assert "evaluate_admit_012" not in functions
    assert "Admit012EvaluationResult" not in classes
    assert not {name for name in functions if name.startswith("_evaluate_registered_") or name.startswith("register_")}
    assert not any(isinstance(node, (ast.Assign, ast.AnnAssign)) and any(isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY" for target in ([node.target] if isinstance(node, ast.AnnAssign) else node.targets)) for node in tree.body)
    design_signature = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "classify_admit_012_formal_evaluator_interface_design")
    assert design_signature.args.vararg is None and design_signature.args.kwarg is None
    assert not design_signature.args.args and not design_signature.args.posonlyargs
    assert [argument.arg for argument in design_signature.args.kwonlyargs] == list((*FIELDS, *CONTEXTS))
    assert len(design_signature.args.kw_defaults) == 8
    assert all(value is not None for value in design_signature.args.kw_defaults[:4])
    assert all(value is None for value in design_signature.args.kw_defaults[4:])


def validate(root: Path = REPO_ROOT / OUTPUT_ROOT, enforce_frozen_hashes: bool = True) -> None:
    output = _read_outputs(root)
    if enforce_frozen_hashes:
        assert {name: hashlib.sha256(output[name]).hexdigest() for name in FILES} == FROZEN_SHA256
    contract = _rows(output[CONTRACT_FILE], CONTRACT_COLUMNS)
    routing = _rows(output[ROUTING_FILE], ROUTING_COLUMNS)
    truth = _rows(output[TRUTH_FILE], TRUTH_COLUMNS)
    sources = _rows(output[SOURCE_FILE], SOURCE_COLUMNS)
    issues = _rows(output[ISSUE_FILE], ISSUE_COLUMNS)
    manifest = json.loads(output[MANIFEST_FILE])
    assert contract == _expected_contract_rows()
    assert routing == _expected_routing_rows()
    _check_truth(truth)
    _validate_sources(sources)
    assert issues == _expected_issues()
    by_id = {row["issue_id"]: row for row in issues}
    assert all(by_id[issue]["status"] == "resolved" for issue in FIELD_RESOLVED | RESOLVED_INTERFACE)
    assert all(by_id[issue]["status"] == "open" for issue in OPEN_REQUIRED)
    assert by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    _check_manifest(manifest, output, len(contract), len(routing), truth)
    _check_production_design_only()


def main() -> int:
    validate()
    print(json.dumps({"output_sha256": FROZEN_SHA256, "stage": STAGE, "status": "passed"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
