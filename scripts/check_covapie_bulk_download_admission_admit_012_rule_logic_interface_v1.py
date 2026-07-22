#!/usr/bin/env python3
"""Independent, source-first checker for the ADMIT_012 standalone evaluator."""

import ast
import csv
import dataclasses
import hashlib
import importlib.util
import inspect
import io
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "3e75daf58475de9deabc1efb55d978a2f458d0d5"
BASE_SUBJECT = "add CovaPIE ADMIT_012 formal evaluator interface contract v1"
STAGE = "covapie_bulk_download_admission_admit_012_rule_logic_interface_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
FORMAL_RELATIVE_PATH = Path("src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py")
FORMAL_PATH = REPO_ROOT / FORMAL_RELATIVE_PATH
FORMAL_MODULE_NAME = "covalent_ext.covapie_bulk_download_admission_admit_012_rule_logic_interface"
MARKER = "# === ADMIT_012 FORMAL EVALUATOR CLOSURE END ==="
EXPECTED_PRODUCTION_SHA256 = "a7b8585ea6d0080e87fc97f29026fbf5df4667dff21729c95f3045d762a55840"
EXPECTED_MARKER_PREFIX_SHA256 = "644af3750080f4333646a28a8eae147884e9733dfed1b18715fcb90cc9efc410"

FIELDS = (
    "download_result_status", "observed_http_status",
    "observed_content_length_bytes", "observed_sha256",
)
CONTEXTS = (
    "allowed_download_result_statuses", "successful_http_status_contract",
    "content_length_contract", "sha256_format_contract",
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
OUTCOMES = ("passed", "blocked", "invalid")
RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_download_result_record", "validated_download_result_fields",
    "consumed_download_result_fields", "consumed_context_items", "evaluator_io_used",
)
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
REASONS = (
    "", *MISSING_REASONS,
    *(reason for index in range(4) for reason in (TYPE_REASONS[index], VALUE_REASONS[index])),
    *CONTEXT_REASONS,
)
FORMAL_CLOSURE = (
    "evaluate_admit_012", "_record", "_make_result", "_context_reason",
    "Admit012EvaluationResult", "Admit012EvaluationResult.__post_init__",
    "_ordered_pair_prefix_valid", "_field_pair_valid",
)
EXPECTED_AST_SHA256 = {
    "evaluate_admit_012": "3af2beb350001329f8440e28fa5ae887517d25e33e16d2eaf491a660f9a1f60c",
    "_make_result": "600c65210c1957747b87e463f1312aee307e2f6d892286b65a147d96353d5b7f",
    "_record": "ac7961e68c410200a6cb6fecd6b5d4783735997d97751b9a88023f965f9d4869",
    "_context_reason": "13dbe9cf9d6c52c643d9574d20ea6add2ae10673a6c60a923f3162bf60ef46eb",
    "Admit012EvaluationResult": "e18dc4088c410020149181f65e1f9a348bf29e8238531d38da426b0ce5e014fd",
    "Admit012EvaluationResult.__post_init__": "efd4571277898098b620b88ab9ec714e3aab9e7f4158893b4ce4be37c981b97f",
    "_ordered_pair_prefix_valid": "9d75f3c824dec077af61356b92574bc29d453869e18c6e47a3327c53ebdc6af7",
    "_field_pair_valid": "5a5a9d7b2c4e98399dfc40770c86aa0799bb0cb9a4db518dde58d04a09b253ab",
}

FILES = (
    "covapie_admit_012_rule_logic_interface_contract.csv",
    "covapie_admit_012_rule_logic_interface_truth_matrix.csv",
    "covapie_admit_012_rule_logic_interface_source_boundary_audit.csv",
    "covapie_admit_012_rule_logic_interface_purity_audit.csv",
    "covapie_admit_012_rule_logic_interface_issue_readiness_inventory.csv",
    "covapie_admit_012_rule_logic_interface_manifest.json",
)
CONTRACT_FILE, TRUTH_FILE, SOURCE_FILE, PURITY_FILE, ISSUE_FILE, MANIFEST_FILE = FILES
FROZEN_OUTPUT_SHA256 = {
    CONTRACT_FILE: "c5c383e9a9e17c5eb5a4b2c92455da89a78e66f75df7ff31ce0494f08281433e",
    TRUTH_FILE: "dc97cd08eabad03315a1533332e2b243122696b605c701051f3024f6189cb5d8",
    SOURCE_FILE: "038f742be4be15d5d064580f55f59243b864708bc6bd9d4c9c7d1a3cab38f866",
    PURITY_FILE: "c0773686a1a9d2d4406e09ff33bf3e217eb9d3135e8556d7461b208ec12990e9",
    ISSUE_FILE: "bac586f54afac5a860a32ed161b6b8f41210b6ae06eb29f368045f10b3ac81e5",
    MANIFEST_FILE: "ad131895c0acfdaf5b350105031647bdcac9667370fb6cd43baf8826bea995c8",
}
CONTRACT_COLUMNS = (
    "contract_order", "contract_section", "section_order", "public_name",
    "parameter_kind_or_result_role", "formal_type", "default_behavior", "required",
    "source_envelope", "formal_invariant", "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "assertion_kind",
    "download_result_status_representation", "observed_http_status_representation",
    "observed_content_length_bytes_representation", "observed_sha256_representation",
    "allowed_download_result_statuses_representation",
    "successful_http_status_contract_representation", "content_length_contract_representation",
    "sha256_format_contract_representation", "expected_admission_rule_id", "expected_outcome",
    "expected_passed", "expected_blocks_candidate", "expected_reason",
    "expected_canonical_download_result_record", "expected_validated_download_result_fields",
    "expected_consumed_download_result_fields", "expected_consumed_context_items",
    "expected_evaluator_io_used", "observed_formal_result", "formal_source",
    "evaluator_io_used", "truth_passed",
)
SOURCE_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "base_tree_mode", "expected_sha256",
    "base_tree_sha256", "filesystem_sha256", "frozen_snapshot_sha256", "git_tracked",
    "base_tree_blob", "filesystem_regular", "non_symlink", "parent_chain_non_symlink",
    "safe_descendant", "pinned_fd_read", "triple_sha256_passed", "source_boundary_passed",
)
PURITY_COLUMNS = (
    "audit_order", "audit_kind", "definition_name", "definition_kind", "reachable_from",
    "normalized_ast_sha256", "permitted_global_bindings", "permitted_calls", "observed",
    "forbidden_io_absent", "mutation_absent", "purity_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

SOURCE_SHA256 = {
    "src/covalent_ext/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate.py": "eea31caa76e06507f7dd482dc7c6b2928f6d0f28ded33c47eb31d25b3be7a927",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_and_result_contract.csv": "682192b492979d9b6114381cbfc02d57c349e3cd8db2541a01177235d34c04e6",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv": "44709c3a679368476c87bcd97dafa2f9cf9bddb4af534c6eb950c565d0919aec",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_truth_matrix.csv": "cc848914ea24b376e29c477c4c0b5e8d32d6fc7caee11873f7a73c4bd207d6db",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_issue_readiness_inventory.csv": "bac586f54afac5a860a32ed161b6b8f41210b6ae06eb29f368045f10b3ac81e5",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_contract_manifest.json": "2845c2623a01087af8842177f4502402d0a8875a77ce12c6a49e2f77c60dae01",
    "src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py": "92d6ab08c4e9fa4bd448895687c897f06a596d4fb73a2e9cf7e88ffebaa6448f",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract.csv": "03aef0a14257d9a2c028fcc3dd84c161c29b09bca1a1c71456edc66e2e73c9ce",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_result_status_enum.csv": "4c016e8c325ce6a422dff618ae166ec4f42243cc0d1fbf8f6a722c13f63139f6",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_validation_truth_matrix.csv": "766506f8c0bf2d7734b9c379c9437e1a48a2117873f7e974325b00ab685a39e1",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract_manifest.json": "9fadff44ae15474783df2a3997c45f2c4d57a41ca2adbab0b40f1d890f51039f",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py": "73adad5c617ecae0dc5772d04ae5d777970a3d2a8c8963c3d2c4c4b19cbf85fc",
    "scripts/check_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1.py": "72f33b9371c4eda533374e0535ba0da22467459da6a6488147e58ad680b7c7f1",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_manifest.json": "a3c053d7b4af149b67b818721f11bb6920b5de00d5d15fb5ec176e10e5a70c3c",
    "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py": "6fd3727234b4b3f637fa5812c78421ec944238518702bc7f9d0d57a654d9a46d",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract.csv": "4b4b41295364fcb83f807c054e2e561ca2c4a31fbf27fd55d04607f3c127c2cc",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate.py": "93e6e726092f8c3e66b19c7ab4c6d363d47962c07eeb694c7237b2b0d5a31346",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py": "ca8e64897b30f961d999d37ce8af5eb985ddf34f332af40c29bf2142bad6e2c8",
}
SOURCE_PATHS = tuple(SOURCE_SHA256)
PATH_LIST_SHA256 = "c1e4c37aba5b1f130d766920b15e4f286bdc5cc961ba830ecdb6d1dff72b27cf"
PATH_PAIRS_SHA256 = "73f8cf567cb1dfbb40d610bafbd7f88b1ffacefd0d4f2b2ff0059688537b9979"
DESIGN_TRUTH_PATH = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_truth_matrix.csv")
DESIGN_ISSUE_PATH = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_issue_readiness_inventory.csv")


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


def _read_fd(path: Path, identity: tuple[int, int, int]) -> bytes:
    if _identity(os.lstat(path)) != identity:
        raise AssertionError("identity drift before open")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if _identity(os.fstat(descriptor)) != identity:
            raise AssertionError("descriptor identity drift")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != identity or _identity(os.lstat(path)) != identity:
            raise AssertionError("identity drift during read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _check_lineage() -> None:
    subject = _git(["show", "-s", "--format=%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if subject.returncode or subject.stdout.strip() != BASE_SUBJECT or ancestor.returncode:
        raise AssertionError("base lineage drift")


def _check_parent_chain(path: Path) -> None:
    current = path.parent
    while current != REPO_ROOT:
        item = os.lstat(current)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
            raise AssertionError("unsafe parent chain")
        current = current.parent


def _normalized_sha(node: ast.AST) -> str:
    return hashlib.sha256(ast.dump(node, annotate_fields=True, include_attributes=False).encode()).hexdigest()


def _top_level_bindings(tree: ast.Module) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in tree.body:
        names = []
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names = [node.name]
        elif isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
        elif isinstance(node, ast.Import):
            names = [alias.asname or alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [alias.asname or alias.name for alias in node.names]
        for name in names:
            counts[name] = counts.get(name, 0) + 1
    return counts


def _definition_nodes(tree: ast.Module) -> dict[str, ast.AST]:
    definitions: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if node.name in definitions:
                raise AssertionError("duplicate formal definition")
            definitions[node.name] = node
    result_class = definitions.get("Admit012EvaluationResult")
    if not isinstance(result_class, ast.ClassDef):
        raise AssertionError("formal result class absent")
    posts = [node for node in result_class.body if isinstance(node, ast.FunctionDef) and node.name == "__post_init__"]
    if len(posts) != 1:
        raise AssertionError("formal result post-init drift")
    definitions["Admit012EvaluationResult.__post_init__"] = posts[0]
    return definitions


def _check_signature_ast(node: ast.AST) -> None:
    if not isinstance(node, ast.FunctionDef):
        raise AssertionError("evaluator function absent")
    arguments = node.args
    if arguments.posonlyargs or arguments.args or arguments.vararg or arguments.kwarg:
        raise AssertionError("public evaluator must be exact keyword-only")
    if tuple(item.arg for item in arguments.kwonlyargs) != (*FIELDS, *CONTEXTS):
        raise AssertionError("public parameter order drift")
    if len(arguments.kw_defaults) != 8:
        raise AssertionError("public default count drift")
    for default in arguments.kw_defaults[:4]:
        if not isinstance(default, ast.Name) or default.id != "_MISSING":
            raise AssertionError("private shared missing default drift")
    if any(default is not None for default in arguments.kw_defaults[4:]):
        raise AssertionError("context must be required")
    if any(ast.unparse(item.annotation) != "object" for item in arguments.kwonlyargs):
        raise AssertionError("parameter annotation drift")
    if ast.unparse(node.returns) != "Admit012EvaluationResult":
        raise AssertionError("return annotation drift")


def _check_class_envelope(node: ast.AST) -> None:
    if not isinstance(node, ast.ClassDef) or node.bases or node.keywords:
        raise AssertionError("result class base/metaclass drift")
    if len(node.decorator_list) != 1:
        raise AssertionError("result decorator drift")
    decorator = node.decorator_list[0]
    if not (
        isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name)
        and decorator.func.id == "dataclass" and not decorator.args and len(decorator.keywords) == 1
        and decorator.keywords[0].arg == "frozen" and isinstance(decorator.keywords[0].value, ast.Constant)
        and decorator.keywords[0].value.value is True
    ):
        raise AssertionError("exact frozen dataclass decorator required")
    fields_nodes = [item for item in node.body if isinstance(item, ast.AnnAssign)]
    methods = [item for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
    other = [item for item in node.body if not isinstance(item, (ast.AnnAssign, ast.FunctionDef, ast.Expr))]
    if tuple(item.target.id for item in fields_nodes if isinstance(item.target, ast.Name)) != RESULT_FIELDS:
        raise AssertionError("Exact10 class field order drift")
    annotations = tuple(ast.unparse(item.annotation) for item in fields_nodes)
    if annotations != ("str", "str", "bool", "bool", "str", "tuple", "tuple", "tuple[str, ...]", "tuple[str, ...]", "bool"):
        raise AssertionError("Exact10 class annotation drift")
    if len(methods) != 1 or methods[0].name != "__post_init__" or other:
        raise AssertionError("result class explicit body drift")


def _discover_closure(definitions: dict[str, ast.AST]) -> tuple[str, ...]:
    discovered = ["evaluate_admit_012"]
    index = 0
    while index < len(discovered):
        name = discovered[index]
        node = definitions[name]
        for call in (item for item in ast.walk(node) if isinstance(item, ast.Call)):
            if isinstance(call.func, ast.Name) and call.func.id in definitions and call.func.id not in discovered:
                discovered.append(call.func.id)
                if call.func.id == "Admit012EvaluationResult":
                    discovered.append("Admit012EvaluationResult.__post_init__")
        index += 1
    return tuple(discovered)


def _check_closed_world(definitions: dict[str, ast.AST]) -> None:
    forbidden_names = {
        "open", "eval", "exec", "compile", "__import__", "globals", "locals", "vars",
        "getattr", "setattr", "delattr", "os", "Path", "subprocess", "tempfile", "hashlib",
        "json", "csv", "io", "socket", "Mapping", "importlib",
        "classify_admit_012_formal_evaluator_interface_design", "materialize_contract",
        "build_artifacts", "build_frozen_source_snapshot",
    }
    allowed_call_names = {
        "type", "len", "tuple", "zip", "enumerate", "all", "any", "fields", "dataclass",
        "TypeError", "ValueError",
        "_make_result", "_record", "_context_reason", "Admit012EvaluationResult",
        "_ordered_pair_prefix_valid", "_field_pair_valid",
    }
    for name in FORMAL_CLOSURE:
        node = definitions[name]
        for item in ast.walk(node):
            if isinstance(item, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom)):
                raise AssertionError("forbidden closure syntax")
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id in forbidden_names:
                raise AssertionError("forbidden closure binding")
            if isinstance(item, ast.Attribute) and item.attr.startswith("__"):
                raise AssertionError("dunder reflection forbidden")
            if isinstance(item, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete)):
                targets = item.targets if isinstance(item, (ast.Assign, ast.Delete)) else [item.target]
                if any(isinstance(target, (ast.Attribute, ast.Subscript)) for target in targets):
                    raise AssertionError("closure mutation forbidden")
            if isinstance(item, ast.Call):
                if isinstance(item.func, ast.Name) and item.func.id not in allowed_call_names:
                    raise AssertionError(f"unknown dynamic closure call: {item.func.id}")
                if isinstance(item.func, ast.Attribute) and item.func.attr not in {"fullmatch", "index"}:
                    raise AssertionError("unknown closure attribute call")


def inspect_formal_source(path: Path = FORMAL_PATH, *, enforce_full_sha: bool = True) -> dict[str, Any]:
    path = Path(path)
    if path == FORMAL_PATH:
        _check_parent_chain(path)
    item = os.lstat(path)
    if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode) or path.resolve(strict=True) != path:
        raise AssertionError("unsafe formal source leaf")
    source = _read_fd(path, _identity(item))
    full_sha = hashlib.sha256(source).hexdigest()
    if enforce_full_sha and full_sha != EXPECTED_PRODUCTION_SHA256:
        raise AssertionError("formal production SHA drift")
    text = source.decode()
    if text.count(MARKER) != 1:
        raise AssertionError("formal closure marker drift")
    prefix_sha = hashlib.sha256(text.split(MARKER, 1)[0].encode()).hexdigest()
    if prefix_sha != EXPECTED_MARKER_PREFIX_SHA256:
        raise AssertionError("formal marker-prefix SHA drift")
    tree = ast.parse(source)
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend((alias.name, alias.asname) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.extend((f"{node.module}.{alias.name}", alias.asname) for alias in node.names)
    expected_imports = [
        *((name, None) for name in ("ast", "csv", "ctypes", "hashlib", "io", "json", "os", "re", "stat", "subprocess", "tempfile")),
        ("dataclasses.dataclass", None), ("dataclasses.fields", None),
        ("pathlib.Path", None), ("typing.Any", None),
    ]
    if imports != expected_imports:
        raise AssertionError("exact import map drift")
    bindings = _top_level_bindings(tree)
    protected = {
        "dataclass", "fields", "re", "_SHA256_RE", "_MissingAdmit012Value", "_MISSING",
        "evaluate_admit_012", "_make_result", "_record", "_context_reason",
        "Admit012EvaluationResult", "_ordered_pair_prefix_valid", "_field_pair_valid",
        "ADMISSION_RULE_ID", "EXACT4_FIELDS", "EXACT4_CONTEXT_ITEMS",
        "ALLOWED_DOWNLOAD_RESULT_STATUSES", "SUCCESSFUL_HTTP_STATUS_CONTRACT",
        "CONTENT_LENGTH_CONTRACT", "SHA256_FORMAT_CONTRACT", "OUTCOME_VOCABULARY",
        "RESULT_FIELDS", "MISSING_REASONS", "TYPE_INVALID_REASONS", "VALUE_INVALID_REASONS",
        "CONTEXT_REASONS", "REASON_VOCABULARY", "FORMAL_CONTEXT_VALUES",
    }
    if any(bindings.get(name) != 1 for name in protected):
        raise AssertionError("formal runtime binding count drift")
    definitions = _definition_nodes(tree)
    _check_signature_ast(definitions["evaluate_admit_012"])
    _check_class_envelope(definitions["Admit012EvaluationResult"])
    closure = _discover_closure(definitions)
    if closure != FORMAL_CLOSURE:
        raise AssertionError(f"formal transitive closure drift: {closure!r}")
    digests = {name: _normalized_sha(definitions[name]) for name in FORMAL_CLOSURE}
    if digests != EXPECTED_AST_SHA256:
        raise AssertionError("normalized formal AST drift")
    _check_closed_world(definitions)
    return {"source": source, "full_sha": full_sha, "prefix_sha": prefix_sha, "digests": digests, "identity": _identity(item), "path": path}


def _attest_sources() -> tuple[dict[str, bytes], dict[str, str]]:
    if len(SOURCE_PATHS) != 18 or len(set(SOURCE_PATHS)) != 18:
        raise AssertionError("fixed Exact18 source boundary drift")
    if hashlib.sha256(json.dumps(list(SOURCE_PATHS), separators=(",", ":")).encode()).hexdigest() != PATH_LIST_SHA256:
        raise AssertionError("source path-list digest drift")
    if hashlib.sha256(json.dumps([[path, SOURCE_SHA256[path]] for path in SOURCE_PATHS], separators=(",", ":")).encode()).hexdigest() != PATH_PAIRS_SHA256:
        raise AssertionError("source path/SHA-pair digest drift")
    structures = []
    modes = {}
    for relative in SOURCE_PATHS:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or path.parts[:2] == ("data", "raw") or path.parts[0] == "checkpoints" or STAGE in path.parts:
            raise AssertionError("source path outside fixed boundary")
        absolute = REPO_ROOT / path
        _check_parent_chain(absolute)
        item = os.lstat(absolute)
        tracked = _git(["ls-files", "--error-unmatch", "--", relative])
        tree = _git(["ls-tree", BASE_COMMIT, "--", relative])
        head, separator, tree_path = tree.stdout.partition("\t")
        parts = head.split()
        if (
            tracked.returncode or tracked.stdout.splitlines() != [relative]
            or tree.returncode or not separator or tree_path.strip() != relative
            or len(parts) != 3 or parts[0] not in {"100644", "100755"} or parts[1] != "blob"
            or stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode)
            or absolute.resolve(strict=True) != absolute
        ):
            raise AssertionError(f"unsafe fixed source: {relative}")
        structures.append((relative, absolute, _identity(item)))
        modes[relative] = parts[0]
    content = {}
    for relative, absolute, identity in structures:
        current = _read_fd(absolute, identity)
        base = _git(["show", f"{BASE_COMMIT}:{relative}"], text=False)
        digest = hashlib.sha256(current).hexdigest()
        if base.returncode or hashlib.sha256(base.stdout).hexdigest() != digest or digest != SOURCE_SHA256[relative]:
            raise AssertionError(f"fixed source SHA drift: {relative}")
        content[relative] = current
    return content, modes


def _lazy_import(attestation: dict[str, Any]) -> Any:
    existing = sys.modules.get(FORMAL_MODULE_NAME)
    if existing is not None:
        module = existing
    else:
        spec = importlib.util.spec_from_file_location(FORMAL_MODULE_NAME, FORMAL_PATH)
        if spec is None or spec.loader is None:
            raise AssertionError("formal import spec unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[FORMAL_MODULE_NAME] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(FORMAL_MODULE_NAME, None)
            raise
    if sys.modules.get(FORMAL_MODULE_NAME) is not module:
        raise AssertionError("formal sys.modules identity drift")
    if Path(module.__file__).resolve() != FORMAL_PATH or module.__spec__ is None or Path(module.__spec__.origin).resolve() != FORMAL_PATH:
        raise AssertionError("formal module origin drift")
    if module.dataclass is not dataclasses.dataclass or module.fields is not dataclasses.fields or module.re is not re:
        raise AssertionError("formal imported binding drift")
    constants = {
        "ADMISSION_RULE_ID": "ADMIT_012", "EXACT4_FIELDS": FIELDS,
        "EXACT4_CONTEXT_ITEMS": CONTEXTS, "ALLOWED_DOWNLOAD_RESULT_STATUSES": ALLOWED,
        "SUCCESSFUL_HTTP_STATUS_CONTRACT": HTTP_CONTRACT, "CONTENT_LENGTH_CONTRACT": CONTENT_CONTRACT,
        "SHA256_FORMAT_CONTRACT": SHA_CONTRACT, "OUTCOME_VOCABULARY": OUTCOMES,
        "RESULT_FIELDS": RESULT_FIELDS, "MISSING_REASONS": MISSING_REASONS,
        "TYPE_INVALID_REASONS": TYPE_REASONS, "VALUE_INVALID_REASONS": VALUE_REASONS,
        "CONTEXT_REASONS": CONTEXT_REASONS, "REASON_VOCABULARY": REASONS,
        "FORMAL_CONTEXT_VALUES": CONTEXT_VALUES,
    }
    for name, expected in constants.items():
        observed = getattr(module, name)
        if type(observed) is not type(expected) or observed != expected:
            raise AssertionError(f"formal constant drift: {name}")
    if not all(getattr(module, "FORMAL_CONTEXT_VALUES")[index] is getattr(module, name) for index, name in enumerate(("ALLOWED_DOWNLOAD_RESULT_STATUSES", "SUCCESSFUL_HTTP_STATUS_CONTRACT", "CONTENT_LENGTH_CONTRACT", "SHA256_FORMAT_CONTRACT"))):
        raise AssertionError("formal context constant identity drift")
    if type(module._SHA256_RE) is not re.Pattern or module._SHA256_RE.pattern != "[0-9a-f]{64}":
        raise AssertionError("formal regex binding drift")
    signature = inspect.signature(module.evaluate_admit_012)
    parameters = tuple(signature.parameters.values())
    if tuple(item.name for item in parameters) != (*FIELDS, *CONTEXTS) or any(item.kind is not inspect.Parameter.KEYWORD_ONLY for item in parameters):
        raise AssertionError("runtime public signature drift")
    defaults = tuple(item.default for item in parameters)
    if not all(default is module._MISSING for default in defaults[:4]) or any(default is not inspect.Parameter.empty for default in defaults[4:]):
        raise AssertionError("runtime missing/context defaults drift")
    if tuple(field.name for field in dataclasses.fields(module.Admit012EvaluationResult)) != RESULT_FIELDS:
        raise AssertionError("runtime Exact10 order drift")
    if module.Admit012EvaluationResult.__dataclass_params__.frozen is not True or module.Admit012EvaluationResult.__bases__ != (object,):
        raise AssertionError("runtime result envelope drift")
    if module.evaluate_admit_012.__module__ != FORMAL_MODULE_NAME or module.Admit012EvaluationResult.__module__ != FORMAL_MODULE_NAME:
        raise AssertionError("formal public binding provenance drift")
    if _read_fd(FORMAL_PATH, attestation["identity"]) != attestation["source"]:
        raise AssertionError("formal source drift after import")
    return module


def _read_output_tree(root: Path) -> dict[str, bytes]:
    root = Path(root)
    parent_identity = _identity(os.lstat(root.parent))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if stat.S_ISLNK(root_item.st_mode) or not stat.S_ISDIR(root_item.st_mode) or root.resolve(strict=True) != root:
        raise AssertionError("unsafe output root")
    if {entry.name for entry in root.iterdir()} != set(FILES):
        raise AssertionError("Exact6 output inventory drift")
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if _identity(os.fstat(descriptor)) != root_identity:
            raise AssertionError("output root descriptor drift")
        output = {}
        identities = {}
        for name in FILES:
            item = os.lstat(root / name)
            identity = _identity(item)
            identities[name] = identity
            if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
                raise AssertionError("unsafe output leaf")
            leaf = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=descriptor)
            try:
                if _identity(os.fstat(leaf)) != identity:
                    raise AssertionError("output leaf descriptor drift")
                chunks = []
                while True:
                    chunk = os.read(leaf, 1 << 16)
                    if not chunk:
                        break
                    chunks.append(chunk)
                if _identity(os.fstat(leaf)) != identity:
                    raise AssertionError("output leaf read drift")
                output[name] = b"".join(chunks)
            finally:
                os.close(leaf)
        if _identity(os.lstat(root.parent)) != parent_identity or _identity(os.lstat(root)) != root_identity:
            raise AssertionError("output tree identity drift")
        if {entry.name for entry in root.iterdir()} != set(FILES):
            raise AssertionError("output inventory race")
        if any(_identity(os.lstat(root / name)) != identity for name, identity in identities.items()):
            raise AssertionError("output leaf identity race")
        return output
    finally:
        os.close(descriptor)


def _rows(data: bytes, columns: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(data.decode(), newline=""))
    if tuple(reader.fieldnames or ()) != columns:
        raise AssertionError("CSV schema drift")
    rows = list(reader)
    if any(tuple(row) != columns or None in row.values() for row in rows):
        raise AssertionError("CSV row shape drift")
    return rows


def _expected_contract() -> list[dict[str, str]]:
    rows = []
    for order, name in enumerate((*FIELDS, *CONTEXTS), 1):
        is_field = order <= 4
        rows.append({
            "contract_order": str(order), "contract_section": "signature_parameter",
            "section_order": str(order), "public_name": name,
            "parameter_kind_or_result_role": "keyword_only", "formal_type": "object",
            "default_behavior": "private_shared_missing_singleton" if is_field else "no_default",
            "required": str(not is_field).lower(),
            "source_envelope": "download_result_context" if is_field else "evaluation_context",
            "formal_invariant": "Exact8 order; no positional/varargs/varkw/Mapping; exact validation",
            "contract_passed": "true",
        })
    types = ("str", "str", "bool", "bool", "str", "tuple", "tuple", "tuple[str,...]", "tuple[str,...]", "bool")
    for section_order, (name, formal_type) in enumerate(zip(RESULT_FIELDS, types, strict=True), 1):
        rows.append({
            "contract_order": str(len(rows) + 1), "contract_section": "result_field",
            "section_order": str(section_order), "public_name": name,
            "parameter_kind_or_result_role": "Exact10_frozen_result_field", "formal_type": formal_type,
            "default_behavior": "not_applicable", "required": "true",
            "source_envelope": "Admit012EvaluationResult",
            "formal_invariant": "exact built-in type; ordered frozen reason-specific state contract",
            "contract_passed": "true",
        })
    return rows


def _decode(text: str) -> object:
    if text == "<MISSING>":
        return MISSING
    if text == "<object>":
        return object()
    if text.startswith("<str-subclass:"):
        return _StrSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<int-subclass:"):
        return _IntSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<tuple-subclass:"):
        return _TupleSubclass(ast.literal_eval(text[16:-1]))
    if text.startswith("<tuple-member-str-subclass:"):
        index, representation = text[27:-1].split(":", 1)
        values = list(ast.literal_eval(representation))
        values[int(index)] = _StrSubclass(values[int(index)])
        return tuple(values)
    if text.startswith("<tuple-pair-subclass:"):
        index, representation = text[21:-1].split(":", 1)
        values = list(ast.literal_eval(representation))
        values[int(index)] = _PairSubclass(values[int(index)])
        return tuple(values)
    if text.startswith("<regex:"):
        return re.compile(ast.literal_eval(text[7:-1]))
    return ast.literal_eval(text)


def _context_reason(value: object, expected: tuple, index: int) -> str:
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


def _classify(values: tuple[object, ...], contexts: tuple[object, ...]) -> tuple:
    for index, value in enumerate(values):
        if value is MISSING:
            return ("ADMIT_012", "blocked", False, True, MISSING_REASONS[index], (), (), FIELDS[:index + 1], (), False)
    validated = []
    for index, value in enumerate(values):
        if index == 0:
            type_valid = type(value) is str
            value_valid = type_valid and value in ALLOWED
        elif index == 1:
            type_valid = type(value) is int
            value_valid = type_valid and 100 <= value <= 599
        elif index == 2:
            type_valid = type(value) is int
            value_valid = type_valid and value >= 0
        else:
            type_valid = type(value) is str
            value_valid = type_valid and re.fullmatch("[0-9a-f]{64}", value) is not None
        if not type_valid:
            return ("ADMIT_012", "invalid", False, True, TYPE_REASONS[index], (), tuple(validated), FIELDS, (), False)
        if not value_valid:
            return ("ADMIT_012", "invalid", False, True, VALUE_REASONS[index], (), tuple(validated), FIELDS, (), False)
        validated.append((FIELDS[index], value))
    canonical = tuple(validated)
    for index, (value, expected) in enumerate(zip(contexts, CONTEXT_VALUES, strict=True)):
        reason = _context_reason(value, expected, index)
        if reason:
            return ("ADMIT_012", "invalid", False, True, reason, canonical, canonical, FIELDS, CONTEXTS[:index + 1], False)
    return ("ADMIT_012", "passed", True, False, "", canonical, canonical, FIELDS, CONTEXTS, False)


NEGATIVE_IDS = (
    "WRONG_RESULT_FIELD_ORDER", "WRONG_OUTCOME_BOOL", "WRONG_CANONICAL_SHAPE",
    "PARTIAL_CANONICAL_RECORD", "VALIDATED_NOT_PREFIX", "CONSUMED_ORDER_DRIFT",
    "EVALUATOR_IO_TRUE", "UNKNOWN_REASON",
)
NEGATIVE_EXPECTED = {
    "WRONG_RESULT_FIELD_ORDER": "RESULT_CONTRACT_REJECTED:TypeError",
    "WRONG_OUTCOME_BOOL": "RESULT_CONTRACT_REJECTED:ValueError",
    "WRONG_CANONICAL_SHAPE": "RESULT_CONTRACT_REJECTED:TypeError",
    "PARTIAL_CANONICAL_RECORD": "RESULT_CONTRACT_REJECTED:ValueError",
    "VALIDATED_NOT_PREFIX": "RESULT_CONTRACT_REJECTED:ValueError",
    "CONSUMED_ORDER_DRIFT": "RESULT_CONTRACT_REJECTED:ValueError",
    "EVALUATOR_IO_TRUE": "RESULT_CONTRACT_REJECTED:ValueError",
    "UNKNOWN_REASON": "RESULT_CONTRACT_REJECTED:ValueError",
}


def _negative_runtime(module: Any, case_id: str) -> str:
    baseline = module.evaluate_admit_012(
        download_result_status="success", observed_http_status=200,
        observed_content_length_bytes=1, observed_sha256="0123456789abcdef" * 4,
        allowed_download_result_statuses=module.ALLOWED_DOWNLOAD_RESULT_STATUSES,
        successful_http_status_contract=module.SUCCESSFUL_HTTP_STATUS_CONTRACT,
        content_length_contract=module.CONTENT_LENGTH_CONTRACT,
        sha256_format_contract=module.SHA256_FORMAT_CONTRACT,
    )
    values = {name: getattr(baseline, name) for name in RESULT_FIELDS}
    try:
        if case_id == "WRONG_RESULT_FIELD_ORDER":
            @dataclasses.dataclass(frozen=True)
            class Wrong:
                outcome: object
                admission_rule_id: object
            candidate = Wrong("passed", "ADMIT_012")
            if type(candidate) is not module.Admit012EvaluationResult:
                raise TypeError("exact result required")
        else:
            if case_id == "WRONG_OUTCOME_BOOL":
                values["passed"] = False
            elif case_id == "WRONG_CANONICAL_SHAPE":
                values["canonical_download_result_record"] = {"download_result_status": "success"}
            elif case_id == "PARTIAL_CANONICAL_RECORD":
                values["canonical_download_result_record"] = baseline.canonical_download_result_record[:2]
            elif case_id == "VALIDATED_NOT_PREFIX":
                values["validated_download_result_fields"] = tuple(reversed(baseline.validated_download_result_fields))
            elif case_id == "CONSUMED_ORDER_DRIFT":
                values["consumed_download_result_fields"] = tuple(reversed(FIELDS))
            elif case_id == "EVALUATOR_IO_TRUE":
                values["evaluator_io_used"] = True
            elif case_id == "UNKNOWN_REASON":
                values.update(outcome="invalid", passed=False, blocks_candidate=True, reason="UNKNOWN_REASON")
            module.Admit012EvaluationResult(*(values[name] for name in RESULT_FIELDS))
    except (TypeError, ValueError) as error:
        return f"RESULT_CONTRACT_REJECTED:{type(error).__name__}"
    raise AssertionError("negative result invariant accepted")


def _check_truth(rows: list[dict[str, str]], source: dict[str, bytes], module: Any) -> None:
    predecessor = list(csv.DictReader(io.StringIO(source[DESIGN_TRUTH_PATH.as_posix()].decode(), newline="")))
    if len(rows) != len(predecessor) != 105:
        raise AssertionError("Exact105 truth count drift")
    if len(rows) != 105 or len(predecessor) != 105:
        raise AssertionError("Exact105 truth count drift")
    representations = tuple(f"{name}_representation" for name in (*FIELDS, *CONTEXTS))
    for index, (row, prior) in enumerate(zip(rows, predecessor, strict=True), 1):
        if row["case_order"] != str(index) or row["case_id"] != prior["case_id"] or row["case_group"] != prior["case_group"] or row["assertion_kind"] != prior["assertion_kind"]:
            raise AssertionError("truth identity/order drift")
        if tuple(row[column] for column in representations) != tuple(prior[column] for column in representations):
            raise AssertionError("truth input projection drift")
        decoded = tuple(_decode(row[column]) for column in representations)
        expected = _classify(decoded[:4], decoded[4:])
        expected_cells = (
            row["expected_admission_rule_id"], row["expected_outcome"], row["expected_passed"],
            row["expected_blocks_candidate"], row["expected_reason"],
            row["expected_canonical_download_result_record"], row["expected_validated_download_result_fields"],
            row["expected_consumed_download_result_fields"], row["expected_consumed_context_items"],
            row["expected_evaluator_io_used"],
        )
        projected = (
            expected[0], expected[1], str(expected[2]).lower(), str(expected[3]).lower(), expected[4],
            repr(expected[5]), repr(expected[6]), repr(expected[7]), repr(expected[8]), str(expected[9]).lower(),
        )
        if expected_cells != projected:
            raise AssertionError("checker-owned expected semantics mismatch")
        if row["case_id"] in NEGATIVE_IDS:
            runtime = _negative_runtime(module, row["case_id"])
            if runtime != NEGATIVE_EXPECTED[row["case_id"]] or row["observed_formal_result"] != runtime:
                raise AssertionError("formal negative invariant projection drift")
        else:
            kwargs = {name: decoded[position] for position, name in enumerate(FIELDS) if decoded[position] is not MISSING}
            kwargs.update({name: decoded[position + 4] for position, name in enumerate(CONTEXTS)})
            runtime_result = module.evaluate_admit_012(**kwargs)
            runtime = tuple(getattr(runtime_result, name) for name in RESULT_FIELDS)
            if runtime != expected or ast.literal_eval(row["observed_formal_result"]) != expected:
                raise AssertionError("formal evaluator truth projection drift")
        if row["formal_source"] != "evaluate_admit_012|Admit012EvaluationResult" or row["evaluator_io_used"] != "false" or row["truth_passed"] != "true":
            raise AssertionError("formal truth attestation drift")
    if tuple(row["case_id"] for row in rows[-8:]) != NEGATIVE_IDS:
        raise AssertionError("negative result case order drift")
    if sum(row["case_id"].startswith("FIELD52_") for row in rows) != 52 or len(rows[52:91]) != 39 or len(rows[91:97]) != 6:
        raise AssertionError("truth group partition drift")


def _check_source_rows(rows: list[dict[str, str]], modes: dict[str, str]) -> None:
    if len(rows) != 18:
        raise AssertionError("source audit row count drift")
    for index, (row, path) in enumerate(zip(rows, SOURCE_PATHS, strict=True), 1):
        digest = SOURCE_SHA256[path]
        expected_kind = "python_source" if Path(path).suffix == ".py" else "committed_csv" if Path(path).suffix == ".csv" else "committed_manifest"
        expected = {
            "source_order": str(index), "source_relative_path": path, "source_kind": expected_kind,
            "base_tree_mode": modes[path], "expected_sha256": digest, "base_tree_sha256": digest,
            "filesystem_sha256": digest, "frozen_snapshot_sha256": digest, "git_tracked": "true",
            "base_tree_blob": "true", "filesystem_regular": "true", "non_symlink": "true",
            "parent_chain_non_symlink": "true", "safe_descendant": "true", "pinned_fd_read": "true",
            "triple_sha256_passed": "true", "source_boundary_passed": "true",
        }
        if row != expected:
            raise AssertionError("source-boundary evidence drift")


def _expected_purity() -> list[dict[str, str]]:
    parents = (
        "root", "evaluate_admit_012", "evaluate_admit_012", "evaluate_admit_012",
        "_make_result", "Admit012EvaluationResult", "Admit012EvaluationResult.__post_init__",
        "_ordered_pair_prefix_valid",
    )
    kinds = ("function", "function", "function", "function", "frozen_dataclass", "method", "function", "function")
    globals_used = (
        "_MISSING|MISSING_REASONS|TYPE_INVALID_REASONS|VALUE_INVALID_REASONS|EXACT4_FIELDS|EXACT4_CONTEXT_ITEMS|ALLOWED_DOWNLOAD_RESULT_STATUSES|FORMAL_CONTEXT_VALUES|_SHA256_RE",
        "EXACT4_FIELDS", "ADMISSION_RULE_ID|Admit012EvaluationResult", "CONTEXT_REASONS",
        "dataclass", "fields|RESULT_FIELDS|EXACT4_FIELDS|EXACT4_CONTEXT_ITEMS|ADMISSION_RULE_ID|OUTCOME_VOCABULARY|REASON_VOCABULARY|MISSING_REASONS|TYPE_INVALID_REASONS|VALUE_INVALID_REASONS|CONTEXT_REASONS",
        "", "", "EXACT4_FIELDS|ALLOWED_DOWNLOAD_RESULT_STATUSES|_SHA256_RE",
    )
    calls = (
        "enumerate|type|_SHA256_RE.fullmatch|_make_result|_record|_context_reason",
        "zip|tuple", "Admit012EvaluationResult", "type|len|all|zip",
        "dataclass", "type|fields|tuple|any|len|_ordered_pair_prefix_valid",
        "type|fields|tuple|any|len|_ordered_pair_prefix_valid", "len|all|enumerate|_field_pair_valid",
        "type|len|_SHA256_RE.fullmatch",
    )
    rows = []
    for index, name in enumerate(FORMAL_CLOSURE):
        rows.append({
            "audit_order": str(index + 1), "audit_kind": "closure_definition", "definition_name": name,
            "definition_kind": kinds[index], "reachable_from": parents[index],
            "normalized_ast_sha256": EXPECTED_AST_SHA256[name], "permitted_global_bindings": globals_used[index],
            "permitted_calls": calls[index], "observed": "reachable_and_frozen",
            "forbidden_io_absent": "true", "mutation_absent": "true", "purity_passed": "true",
        })
    metadata = (
        ("production_full_sha256", EXPECTED_PRODUCTION_SHA256),
        ("marker_prefix_sha256", EXPECTED_MARKER_PREFIX_SHA256),
        ("exact_imported_symbol_map", "ast|csv|ctypes|hashlib|io|json|os|re|stat|subprocess|tempfile|dataclasses.dataclass|dataclasses.fields|pathlib.Path|typing.Any"),
        ("exact_constant_binding_map", "ADMISSION_RULE_ID|EXACT4_FIELDS|EXACT4_CONTEXT_ITEMS|ALLOWED_DOWNLOAD_RESULT_STATUSES|SUCCESSFUL_HTTP_STATUS_CONTRACT|CONTENT_LENGTH_CONTRACT|SHA256_FORMAT_CONTRACT|OUTCOME_VOCABULARY|RESULT_FIELDS|MISSING_REASONS|TYPE_INVALID_REASONS|VALUE_INVALID_REASONS|CONTEXT_REASONS|REASON_VOCABULARY|FORMAL_CONTEXT_VALUES|_SHA256_RE|_MISSING"),
        ("result_dataclass_shape", "Admit012EvaluationResult|frozen=True|Exact10|only___post_init__|no_base_or_metaclass"),
        ("closure_complete", "|".join(FORMAL_CLOSURE)),
    )
    for name, observed in metadata:
        rows.append({
            "audit_order": str(len(rows) + 1), "audit_kind": "closure_metadata", "definition_name": name,
            "definition_kind": "attestation", "reachable_from": "checker_recomputed",
            "normalized_ast_sha256": "", "permitted_global_bindings": "", "permitted_calls": "",
            "observed": observed, "forbidden_io_absent": "true", "mutation_absent": "true", "purity_passed": "true",
        })
    return rows


TRUE_READINESS = (
    "admit_012_preconditions_audited", "admit_012_download_integrity_field_contract_frozen",
    "admit_012_field_semantics_complete", "admit_012_presence_semantics_resolved",
    "admit_012_validation_precedence_resolved", "admit_012_routing_responsibility_resolved",
    "admit_012_standalone_signature_frozen", "admit_012_formal_result_contract_frozen",
    "admit_012_formal_evaluator_interface_contract_frozen",
    "ready_for_admit_012_standalone_evaluator_interface_implementation",
    "admit_012_standalone_evaluator_interface_implemented", "admit_012_rule_logic_implemented",
    "evaluate_admit_012_implemented", "Admit012EvaluationResult_implemented",
    "ready_for_admit_012_unified_adapter_contract_design",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_012_unified_adapter_contract_frozen", "admit_012_unified_adapter_implemented",
    "admit_012_registered_in_engine", "unified_dispatch_runtime_with_admit_001_to_012_implemented",
    "provider_mapping_validated", "real_provider_evaluation_ready", "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented", "ready_for_training", "step12d_is_final_training_feature_contract",
)


def _check_manifest(manifest: dict[str, Any], output: dict[str, bytes]) -> None:
    readiness = {**{name: True for name in TRUE_READINESS}, **{name: False for name in FALSE_READINESS}}
    expected = {
        "manifest_schema_version": "covapie_admit_012_rule_logic_interface_manifest_v1",
        "project": "CovaPIE", "stage": STAGE, "base_commit": BASE_COMMIT, "base_subject": BASE_SUBJECT,
        "admission_rule_id": "ADMIT_012", "public_evaluator": "evaluate_admit_012",
        "public_signature": "evaluate_admit_012(*, download_result_status: object = _MISSING, observed_http_status: object = _MISSING, observed_content_length_bytes: object = _MISSING, observed_sha256: object = _MISSING, allowed_download_result_statuses: object, successful_http_status_contract: object, content_length_contract: object, sha256_format_contract: object) -> Admit012EvaluationResult",
        "result_type": "Admit012EvaluationResult", "result_fields": list(RESULT_FIELDS), "result_field_count": 10,
        "field_order": list(FIELDS), "context_order": list(CONTEXTS), "outcome_vocabulary": list(OUTCOMES),
        "reason_vocabulary": list(REASONS),
        "validation_phase_order": ["Exact4_presence", "Exact4_type_value", "policy_context_type_content", "passed"],
        "canonical_record_representation": "empty or complete ordered Exact4 exact-pair tuple",
        "validated_representation": "ordered valid Exact4 pair-tuple prefix excluding failing field",
        "consumption_semantics": "ordered actual field/context prefixes; all fields consumed after presence completes",
        "failure_status_4xx_5xx_outcome": "passed", "admit_013_success_or_integrity_judgment_executed": False,
        "formal_evaluator_implemented": True, "formal_result_type_defined": True,
        "formal_production_sha256": EXPECTED_PRODUCTION_SHA256,
        "formal_marker_prefix_sha256": EXPECTED_MARKER_PREFIX_SHA256,
        "formal_closure": list(FORMAL_CLOSURE), "formal_closure_count": 8,
        "formal_ast_sha256": EXPECTED_AST_SHA256,
        "source_count": 18, "source_path_list_sha256": PATH_LIST_SHA256,
        "source_path_sha256_pairs_sha256": PATH_PAIRS_SHA256,
        "output_files": list(FILES), "output_file_count": 6,
        "row_counts": {"formal_contract": 18, "truth_matrix": 105, "field52_projection": 52, "context_projection": 39, "cross_phase_projection": 6, "negative_result_projection": 8, "source_boundary": 18, "purity_audit": 14, "issue_inventory": 16},
        "truth_matrix_passed": 105, "purity_closure_complete": True,
        "coverage_affected_rules": "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        "readiness": readiness, **readiness,
        "feature_semantics_audit_required_before_training": True,
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": "design_covapie_admit_012_unified_adapter_contract_v1",
        "unified_adapter_or_runtime_changed": False, "admit_013_implemented": False,
        "authorized_admit_012_download_execution_count": 0,
        "safety": {"network": False, "raw": False, "provider_mapping": False, "real_download": False, "model_or_checkpoint": False, "runtime_change": False, "training": False},
        "renameat2_policy": "RENAME_NOREPLACE_required;_EINVAL_fails_closed_without_os.replace_fallback",
        "output_sha256": {name: hashlib.sha256(output[name]).hexdigest() for name in FILES[:-1]},
        "all_checks_passed": True,
    }
    if manifest != expected:
        raise AssertionError("manifest exact-value drift")


def validate_output_tree(root: Path = REPO_ROOT / OUTPUT_ROOT, *, enforce_frozen_hashes: bool = True) -> None:
    _check_lineage()
    formal_attestation = inspect_formal_source()
    source_content, source_modes = _attest_sources()
    module = _lazy_import(formal_attestation)
    output = _read_output_tree(root)
    if enforce_frozen_hashes:
        observed_hashes = {name: hashlib.sha256(output[name]).hexdigest() for name in FILES}
        if observed_hashes != FROZEN_OUTPUT_SHA256:
            raise AssertionError("frozen Exact6 output SHA drift")
    contract = _rows(output[CONTRACT_FILE], CONTRACT_COLUMNS)
    truth = _rows(output[TRUTH_FILE], TRUTH_COLUMNS)
    sources = _rows(output[SOURCE_FILE], SOURCE_COLUMNS)
    purity = _rows(output[PURITY_FILE], PURITY_COLUMNS)
    issues = _rows(output[ISSUE_FILE], ISSUE_COLUMNS)
    manifest = json.loads(output[MANIFEST_FILE])
    if contract != _expected_contract():
        raise AssertionError("formal contract evidence drift")
    _check_truth(truth, source_content, module)
    _check_source_rows(sources, source_modes)
    if purity != _expected_purity():
        raise AssertionError("purity evidence drift")
    predecessor_issues = list(csv.DictReader(io.StringIO(source_content[DESIGN_ISSUE_PATH.as_posix()].decode(), newline="")))
    if issues != predecessor_issues or len(issues) != 16:
        raise AssertionError("Exact16 issue continuity drift")
    by_id = {row["issue_id"]: row for row in issues}
    resolved = {
        "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED", "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
        "ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED", "ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED",
        "ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED",
        "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED", "ADMIT_012_RESULT_CONTRACT_UNRESOLVED",
    }
    if not all(by_id[item]["status"] == "resolved" for item in resolved):
        raise AssertionError("resolved issue continuity drift")
    if by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] != "open" or by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] != "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015":
        raise AssertionError("coverage issue continuity drift")
    if by_id["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] != "open":
        raise AssertionError("cross-rule issue continuity drift")
    _check_manifest(manifest, output)


def main() -> int:
    validate_output_tree()
    print(json.dumps({"output_sha256": FROZEN_OUTPUT_SHA256, "stage": STAGE, "status": "passed"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
