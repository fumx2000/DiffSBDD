#!/usr/bin/env python3
"""Independent checker for the ADMIT_013 unified-adapter Design contract."""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import io
import json
import os
import stat
import subprocess
import sys
from dataclasses import fields
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = "da7bf5258365ecebde20ba1f09081b075312ebaf"
PARENT = "79e63dce368722b126ad21208a3de13f7ea4b6df"
TREE = "63fa16eeb3ccb53b0d900b2117ef91623f89e7c6"
SUBJECT = "add CovaPIE ADMIT_013 standalone evaluator interface v1"
STAGE = "covapie_bulk_download_admission_admit_013_unified_adapter_contract_v1"
OUTPUT_ROOT = ROOT / "data/derived/covalent_small" / STAGE
CANONICAL_IMPLEMENTATION = "cpython"
CANONICAL_VERSION = (3, 10, 4)

RULE_ID = "ADMIT_013"
RULE_NAME = "download_failure_fail_closed"
ADAPTER_ID = "covapie_admit_013_unified_adapter_v1"
FUTURE_HANDLER = "_evaluate_registered_admit_013"
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
DOWNLOAD_FIELDS = (
    "download_result_status", "observed_http_status",
    "observed_content_length_bytes", "observed_sha256",
)
AUTHORITY_FIELDS = (
    "expected_content_length_bytes", "expected_sha256",
    "explicit_integrity_verdict",
)
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
SOURCE_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_download_result_record", "canonical_integrity_authority_record",
    "validated_download_result_fields", "validated_integrity_authority_fields",
    "consumed_download_result_fields", "consumed_integrity_authority_fields",
    "evaluator_io_used",
)
ROUTING_ORDER = (
    "batch_context_must_be_none",
    "evaluation_context_mapping_validation",
    "download_result_context_mapping_validation",
    "stage_authorization_context_must_be_none",
    "candidate_record_mapping_validation",
    "download_result_exact4_required_lookup_first_missing_stops",
    "integrity_authority_exact3_optional_lookup_all",
    "formal_evaluator_exactly_once",
    "standalone_source_exact12_validation",
    "independent_design_oracle_exactly_once",
    "full_exact12_exact_type_value_equality",
    "typed_to_string_exact13_projection",
)
CONTEXT_REASONS = {
    "batch_context": "ADMIT_013_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_013_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "download_result_context": "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED",
    "stage_authorization_context": "ADMIT_013_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
    "download_result_lookup": "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_LOOKUP_FAILED",
    "evaluation_lookup": "ADMIT_013_EVALUATION_CONTEXT_LOOKUP_FAILED",
}
SOURCE_TYPE_REASON = "ADMIT_013_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
CANDIDATE_REASON = "ADMIT_013_CANDIDATE_RECORD_MAPPING_INVALID"
CURRENT_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 13))
FUTURE_ORDER = (*CURRENT_ORDER, RULE_ID)
KNOWN = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))

SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_admit_013_rule_logic_interface.py", "36a4d3080128dadcecbdda25c5a3e143ac054aba001e7ac9cd7de0e2c51307f4"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_contract.csv", "74cf6af87efb8661ddb6a2e5931827c0bd9a0148fb26fdaa3f9dd5da970e5e6f"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_truth_matrix.csv", "2399d1551e42b9343c1b849bb9a4fd06a2758c07e4ceff3be2d4758d9d519f52"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_purity_audit.csv", "0798e983838d42d635de786575c502a1472970fabe8459a51e8a8212d343e081"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_issue_readiness_inventory.csv", "e2d895dc822e5de8d6f1410e41f6cd79407b090a0055ebe2a79aeadabf033214"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_manifest.json", "3ecbbc4d99966c955b39cad4dae65ef9c8316c7847bd43ccef82c44863cd4fa5"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate.py", "256d5d0bfd54fe5accc4493051809aafec58a41b6cf56b9090dbf19f80b2a2e3"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_routing_and_consumption_contract.csv", "55b78fdf124efc0310d4e55b8564568c7cd88c5e3155666a75162d6c54c1af90"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_truth_matrix.csv", "1ffafe3dac824c91e9dcb3fef8760e1f8f1e92754755816d4cef2d0f58fd5631"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_contract_manifest.json", "5cadbddf7d75aac7b92f5f86ad204e96237ea80a58f4372eaa22460b4385ea71"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv", "7e856eb5ebd995793dcd82fb75266c7ee6f6a8b06b7785f3a70713a96b8efdbb"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_and_integrity_contract_manifest.json", "1bbfe88f459946b78bb14e5b0b672582d508a838bef220ecf292fa84d15f934d"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py", "4d9a49806d4ef71a95c8ad032dfa061f7473b1cb55a573459c155f0cd5d57282"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_registry_and_identity_audit.csv", "57ed1f04df27c7b30ec4cea97aead99e7788a2968f77245280850ae26f399e59"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_manifest.json", "bc909aefd86b62139fbb62025d9c323988a4c232ab9c960efb291fb0c196cee3"),
    ("src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py", "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate.py", "6de88444d8ee0b62e301fdb19e050166c80344cc45b3ee0612998a72c188f162"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract.csv", "12228051428134223dc4db4ec418ced573637047189056f1fb8df908ca2fe6c8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract_manifest.json", "1df0e2a09817b7763ec4eb767663db169d3239385094da151af28150c2c55d25"),
)
PATH_DIGEST = "a0916d1e55ccc4d070a2e1ec1a9ab9a23f5fff6b2efdba1c08573f8920403b07"
PAIR_DIGEST = "f9c74e0f1eddfea1e4ac49f8a6d2bc1596af48496d285420012ad8b8e37962e4"

CONTRACT_FILE = "covapie_admit_013_unified_adapter_contract.csv"
ROUTING_FILE = "covapie_admit_013_download_and_integrity_authority_projection_and_context_routing_matrix.csv"
TRUTH_FILE = "covapie_admit_013_unified_result_projection_truth_matrix.csv"
SAFETY_FILE = "covapie_admit_013_unified_adapter_safety_audit.csv"
ISSUE_FILE = "covapie_admit_013_unified_adapter_issue_readiness_inventory.csv"
MANIFEST_FILE = "covapie_admit_013_unified_adapter_contract_manifest.json"
OUTPUT_FILES = (
    CONTRACT_FILE, ROUTING_FILE, TRUTH_FILE,
    SAFETY_FILE, ISSUE_FILE, MANIFEST_FILE,
)
OUTPUT_SHA256 = {
    CONTRACT_FILE: "398d40b3c4f53ad112bfe4f4aae0f1a1f630ef6a1176f826ae01d880711ea22b",
    ROUTING_FILE: "6c64e739e6fc94f9a5086ad6850fa0f457d517a506c2c5978aa62e1d29cd8c28",
    TRUTH_FILE: "d2910fa0626571873345d6ea5ad63fedf9c8259f9fb3116469da73d844a57de3",
    SAFETY_FILE: "90bc4f2f32822cbd98810f26aa49e91e1cc66de5b4585e86f49d731f6f632b65",
    ISSUE_FILE: "e2d895dc822e5de8d6f1410e41f6cd79407b090a0055ebe2a79aeadabf033214",
    MANIFEST_FILE: "b105404fba60c7e3ea2427717fd2aaeeefa1890b4fa050b25cd535a50895fdb8",
}

CONTRACT_COLUMNS = (
    "contract_order", "contract_id", "contract_group", "contract_subject",
    "contract_value", "contract_status",
)
ROUTING_COLUMNS = (
    "matrix_order", "matrix_group", "case_id", "routing_condition",
    "envelope_representation", "lookup_count", "lookup_order",
    "candidate_key_access_count", "formal_call_count", "oracle_call_count",
    "identity_preserved", "expected_dispatch_code", "expected_reason",
    "expected_result_json", "case_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "routing_condition",
    "candidate_record_representation", "batch_context_representation",
    "evaluation_context_representation", "download_result_context_representation",
    "stage_authorization_context_representation", "evaluation_lookup_count",
    "download_lookup_count", "candidate_key_access_count", "lookup_order",
    "formal_call_count", "oracle_call_count", "source_exact12_json",
    "oracle_exact12_json", "projected_exact13_json", "identity_preserved",
    "expected_dispatch_code", "expected_reason", "case_passed",
)
SAFETY_COLUMNS = (
    "safety_order", "safety_item", "expected_executed",
    "observed_executed", "evidence", "safety_passed",
)
ISSUE_COLUMNS = (
    "inherited_order", "issue_id", "issue_type", "affected_fields",
    "affected_rules", "severity", "status", "blocking_scope",
    "blocking_reason", "issue_origin", "integration_transition", "issue_count",
    "inherited_effective_status", "inherited_transition_stage",
    "inherited_transition_action", "inherited_transition_evidence",
    "successor_effective_status", "successor_transition_stage",
    "successor_transition_action", "successor_transition_evidence",
)

DESIGN_PATH = "src/covalent_ext/covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate.py"
CHECKER_PATH = "scripts/check_covapie_bulk_download_admission_admit_013_unified_adapter_contract_v1.py"
TEST_PATH = "tests/test_covapie_bulk_download_admission_admit_013_unified_adapter_contract_v1.py"
DOC_PATH = "docs/covapie_bulk_download_admission_admit_013_unified_adapter_contract_v1_summary.md"
CANDIDATE_PATHS = (
    DESIGN_PATH, CHECKER_PATH, TEST_PATH, DOC_PATH,
    *(f"data/derived/covalent_small/{STAGE}/{name}" for name in OUTPUT_FILES),
)
EXPECTED_DESIGN_SHA256 = "1c36731e4db7be316f1fbb24602a2966c2c52ad57e91b7b8abfe341d2c137858"


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git(*arguments: str, allow_failure: bool = False) -> bytes:
    result = subprocess.run(
        ("git", *arguments), cwd=ROOT, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if result.returncode and not allow_failure:
        raise AssertionError("source git command failed")
    return result.stdout


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode


def _full_identity(item: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        item.st_dev, item.st_ino, item.st_mode, item.st_size,
        item.st_mtime_ns, item.st_ctime_ns,
    )


def _validate_canonical_evidence_runtime_identity(
    implementation_name: str,
    version: tuple[int, int, int],
) -> None:
    if (
        implementation_name != CANONICAL_IMPLEMENTATION
        or version != CANONICAL_VERSION
    ):
        observed_version = ".".join(str(part) for part in version)
        raise AssertionError(
            "required: CPython 3.10.4; "
            f"observed implementation: {implementation_name}; "
            f"observed version: {observed_version}; "
            "frozen evidence is Python-version-sensitive; "
            "noncanonical Python is not authorized to build artifacts or run the checker"
        )


def _assert_canonical_evidence_runtime() -> None:
    _validate_canonical_evidence_runtime_identity(
        sys.implementation.name, tuple(sys.version_info[:3])
    )


def _parent_chain(parent: Path, anchor: Path) -> None:
    current = parent
    while True:
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise AssertionError("parent chain unsafe")
        if current == anchor:
            break
        if current == current.parent:
            raise AssertionError("parent chain escaped")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise AssertionError("resolved parent drift")


def _read_pinned(
    root: Path,
    relative: Path,
    expected_leaf: tuple[int, int, int, int, int, int],
) -> bytes:
    if relative.is_absolute() or ".." in relative.parts:
        raise AssertionError("source path escape")
    root_lexical = os.lstat(root)
    root_identity = _identity(root_lexical)
    if (
        not stat.S_ISDIR(root_lexical.st_mode)
        or stat.S_ISLNK(root_lexical.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise AssertionError("source root structure")
    root_fd = os.open(
        root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    descriptors = [root_fd]
    parent_bindings: list[tuple[int, str, int, tuple[int, int, int]]] = []
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise AssertionError("source root descriptor identity")
        directory_fd = root_fd
        for part in relative.parts[:-1]:
            lexical = os.stat(
                part, dir_fd=directory_fd, follow_symlinks=False
            )
            lexical_identity = _identity(lexical)
            if not stat.S_ISDIR(lexical.st_mode) or stat.S_ISLNK(lexical.st_mode):
                raise AssertionError("source parent structure")
            child_fd = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=directory_fd,
            )
            if _identity(os.fstat(child_fd)) != lexical_identity:
                os.close(child_fd)
                raise AssertionError("source parent identity race")
            parent_bindings.append(
                (directory_fd, part, child_fd, lexical_identity)
            )
            directory_fd = child_fd
            descriptors.append(child_fd)
        leaf = os.stat(
            relative.name, dir_fd=directory_fd, follow_symlinks=False
        )
        if (
            _full_identity(leaf) != expected_leaf
            or not stat.S_ISREG(leaf.st_mode)
            or stat.S_ISLNK(leaf.st_mode)
        ):
            raise AssertionError("source lexical leaf identity")
        descriptor = os.open(
            relative.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=directory_fd,
        )
        try:
            if _full_identity(os.fstat(descriptor)) != expected_leaf:
                raise AssertionError("source descriptor identity")
            chunks = []
            while True:
                chunk = os.read(descriptor, 1 << 16)
                if not chunk:
                    break
                chunks.append(chunk)
            if _full_identity(os.fstat(descriptor)) != expected_leaf:
                raise AssertionError("source descriptor changed")
            after_leaf = os.stat(
                relative.name, dir_fd=directory_fd, follow_symlinks=False
            )
            if (
                _full_identity(after_leaf) != expected_leaf
                or not stat.S_ISREG(after_leaf.st_mode)
                or stat.S_ISLNK(after_leaf.st_mode)
            ):
                raise AssertionError("source lexical leaf changed after read")
            for parent_fd, part, child_fd, expected in reversed(parent_bindings):
                after_parent = os.stat(
                    part, dir_fd=parent_fd, follow_symlinks=False
                )
                if (
                    _identity(after_parent) != expected
                    or _identity(os.fstat(child_fd)) != expected
                    or not stat.S_ISDIR(after_parent.st_mode)
                    or stat.S_ISLNK(after_parent.st_mode)
                ):
                    raise AssertionError(
                        "source lexical parent changed after read"
                    )
            after_root = os.lstat(root)
            if (
                _identity(after_root) != root_identity
                or _identity(os.fstat(root_fd)) != root_identity
                or not stat.S_ISDIR(after_root.st_mode)
                or stat.S_ISLNK(after_root.st_mode)
            ):
                raise AssertionError("source root changed after read")
            return b"".join(chunks)
        finally:
            os.close(descriptor)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _verify_sources() -> tuple[dict[str, Any], ...]:
    _assert_canonical_evidence_runtime()
    if len(SOURCE_BOUNDARY) != 19 or len({path for path, _ in SOURCE_BOUNDARY}) != 19:
        raise AssertionError("source Exact19")
    path_digest = _sha(json.dumps(
        [path for path, _ in SOURCE_BOUNDARY], separators=(",", ":"),
    ).encode())
    pair_digest = _sha(json.dumps(
        SOURCE_BOUNDARY, separators=(",", ":"),
    ).encode())
    if path_digest != PATH_DIGEST or pair_digest != PAIR_DIGEST:
        raise AssertionError("source boundary digest")
    identity = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE,
    ).decode().splitlines()
    if identity != [BASE, PARENT, TREE, SUBJECT]:
        raise AssertionError("base identity")
    _git("merge-base", "--is-ancestor", BASE, "HEAD")
    inspected = []
    for relative, expected in SOURCE_BOUNDARY:
        path = ROOT / relative
        parts = Path(relative).parts
        if (
            Path(relative).is_absolute() or ".." in parts
            or parts[:2] == ("data", "raw") or parts[0] == "checkpoints"
        ):
            raise AssertionError("protected source path")
        _parent_chain(path.parent, ROOT)
        item = os.lstat(path)
        identity_tuple = _full_identity(item)
        if (
            not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode)
            or path.resolve(strict=True) != path
        ):
            raise AssertionError("source structure")
        if _git("ls-files", "--error-unmatch", "--", relative).decode() != f"{relative}\n":
            raise AssertionError("source tracked")
        entries = _git("ls-tree", BASE, "--", relative).splitlines()
        if len(entries) != 1 or b"\t" not in entries[0]:
            raise AssertionError("source base tree")
        metadata, tree_path = entries[0].split(b"\t", 1)
        mode, kind, blob = metadata.split()
        if (
            tree_path.decode() != relative or mode not in (b"100644", b"100755")
            or kind != b"blob"
        ):
            raise AssertionError("source base blob/mode")
        inspected.append((relative, expected, path, identity_tuple, mode.decode(), blob.decode()))
    rows = []
    for order, (relative, expected, path, identity_tuple, mode, blob) in enumerate(inspected, 1):
        filesystem = _read_pinned(
            ROOT, Path(relative), identity_tuple
        )
        base = _git("cat-file", "blob", blob)
        if expected != _sha(filesystem) or expected != _sha(base):
            raise AssertionError("source SHA")
        rows.append({
            "source_order": order, "source_relative_path": relative,
            "expected_sha256": expected, "mode": mode, "content": filesystem,
        })
    return tuple(rows)


def _output_bytes() -> dict[str, bytes]:
    _parent_chain(OUTPUT_ROOT.parent, ROOT)
    parent_item = os.lstat(OUTPUT_ROOT.parent)
    parent_identity = _identity(parent_item)
    root_item = os.lstat(OUTPUT_ROOT)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode) or stat.S_ISLNK(root_item.st_mode)
        or OUTPUT_ROOT.resolve(strict=True) != OUTPUT_ROOT
    ):
        raise AssertionError("output root structure")
    root_fd = os.open(
        OUTPUT_ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise AssertionError("output root identity")
        names = tuple(os.listdir(root_fd))
        if len(names) != 6 or set(names) != set(OUTPUT_FILES):
            raise AssertionError("output Exact6 inventory")
        leaf_identities = {}
        for name in OUTPUT_FILES:
            item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                not stat.S_ISREG(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
                or item.st_size > 100 * 1024 * 1024
            ):
                raise AssertionError("output leaf structure/size")
            leaf_identities[name] = _full_identity(item)
        payloads = {}
        for name in OUTPUT_FILES:
            descriptor = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=root_fd,
            )
            try:
                expected = leaf_identities[name]
                if _full_identity(os.fstat(descriptor)) != expected:
                    raise AssertionError("output leaf identity")
                chunks = []
                while True:
                    chunk = os.read(descriptor, 1 << 16)
                    if not chunk:
                        break
                    chunks.append(chunk)
                if _full_identity(os.fstat(descriptor)) != expected:
                    raise AssertionError("output leaf changed")
                after_leaf = os.stat(
                    name, dir_fd=root_fd, follow_symlinks=False
                )
                if (
                    _full_identity(after_leaf) != expected
                    or not stat.S_ISREG(after_leaf.st_mode)
                    or stat.S_ISLNK(after_leaf.st_mode)
                ):
                    raise AssertionError("output lexical leaf changed")
                payloads[name] = b"".join(chunks)
            finally:
                os.close(descriptor)
        after_parent = os.lstat(OUTPUT_ROOT.parent)
        after_root = os.lstat(OUTPUT_ROOT)
        if (
            _identity(after_parent) != parent_identity
            or not stat.S_ISDIR(after_parent.st_mode)
            or stat.S_ISLNK(after_parent.st_mode)
        ):
            raise AssertionError("output parent changed after traversal")
        if (
            _identity(after_root) != root_identity
            or _identity(os.fstat(root_fd)) != root_identity
            or not stat.S_ISDIR(after_root.st_mode)
            or stat.S_ISLNK(after_root.st_mode)
        ):
            raise AssertionError("output root changed after traversal")
        names = tuple(os.listdir(root_fd))
        if len(names) != 6 or set(names) != set(OUTPUT_FILES):
            raise AssertionError("output inventory changed after traversal")
        for name, expected in leaf_identities.items():
            item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                _full_identity(item) != expected
                or not stat.S_ISREG(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
            ):
                raise AssertionError("output leaf changed after traversal")
        return payloads
    finally:
        os.close(root_fd)


def _csv(payload: bytes, columns: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode(), newline=""))
    rows = list(reader)
    if tuple(reader.fieldnames or ()) != columns:
        raise AssertionError("CSV header drift")
    if any(tuple(row) != columns or None in row for row in rows):
        raise AssertionError("CSV row schema drift")
    return rows


def _json_no_duplicates(payload: bytes) -> tuple[dict[str, Any], tuple[str, ...]]:
    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        keys = [key for key, _ in pairs]
        if len(keys) != len(set(keys)):
            raise AssertionError("manifest duplicate key")
        return dict(pairs)

    value = json.loads(payload, object_pairs_hook=hook)
    if type(value) is not dict:
        raise AssertionError("manifest object required")
    keys = tuple(value)
    if keys != tuple(sorted(keys)):
        raise AssertionError("manifest key order")
    return value, keys


def _literal_registry_keys(content: bytes) -> tuple[str, ...]:
    tree = ast.parse(content.decode())
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY" for target in node.targets)
    )
    if not isinstance(assignment.value, ast.Call) or not assignment.value.args:
        raise AssertionError("registry AST")
    dictionary = assignment.value.args[0]
    if not isinstance(dictionary, ast.Dict):
        raise AssertionError("registry literal")
    return tuple(ast.literal_eval(key) for key in dictionary.keys)


def _verify_design_ast() -> None:
    content = (ROOT / DESIGN_PATH).read_bytes()
    if EXPECTED_DESIGN_SHA256 != "TO_BE_FROZEN" and _sha(content) != EXPECTED_DESIGN_SHA256:
        raise AssertionError("production Design source SHA drift")
    tree = ast.parse(content.decode())
    functions = {
        node.name: node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    classes = {
        node.name for node in tree.body if isinstance(node, ast.ClassDef)
    }
    forbidden_functions = {
        FUTURE_HANDLER, "evaluate_admission_rule", "combined_candidate_verdict",
    }
    if forbidden_functions & functions.keys():
        raise AssertionError("runtime/aggregation function defined")
    if "UnifiedAdmissionRuleEvaluation" in classes:
        raise AssertionError("shared Exact13 redefined")
    assignments = {
        target.id
        for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets if isinstance(node, ast.Assign) else (node.target,)
        )
        if isinstance(target, ast.Name)
    }
    if "EVALUATOR_REGISTRY" in assignments:
        raise AssertionError("registry defined")
    required = {
        "simulate_admit_013_unified_adapter_design",
        "validate_source_shape_and_invariants_for_design",
        "expected_exact12_from_committed_oracle_for_design",
        "validate_source_oracle_equivalence_for_design",
        "project_exact12_to_exact13_for_design",
    }
    if not required <= functions.keys():
        raise AssertionError("Design API missing")
    module_text = content.decode()
    if ".get(" in ast.unparse(functions["simulate_admit_013_unified_adapter_design"]):
        raise AssertionError("Mapping.get forbidden")
    if "_MISSING" in module_text:
        raise AssertionError("standalone private sentinel referenced")
    routing_assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "CONTEXT_ROUTING_ORDER" for target in node.targets)
    )
    if tuple(ast.literal_eval(routing_assignment.value)) != ROUTING_ORDER:
        raise AssertionError("routing order AST drift")


class _Missing:
    __slots__ = ()


MISSING = _Missing()


class _StrSubclass(str):
    pass


class _IntSubclass(int):
    pass


def _decode(text: str) -> object:
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


def _exact12_json(value: object) -> str:
    return json.dumps(
        {name: getattr(value, name) for name in SOURCE_FIELDS},
        ensure_ascii=True, separators=(",", ":"),
    )


def _project_pairs(pairs: object) -> tuple[tuple[str, str], ...]:
    names = (*DOWNLOAD_FIELDS, *AUTHORITY_FIELDS)
    if type(pairs) is not tuple:
        raise AssertionError("pair tuple")
    result = []
    positions = []
    for pair in pairs:
        if (
            type(pair) is not tuple or len(pair) != 2
            or type(pair[0]) is not str or pair[0] not in names
        ):
            raise AssertionError("pair shape")
        positions.append(names.index(pair[0]))
        value = pair[1]
        if pair[0] in {
            "observed_http_status", "observed_content_length_bytes",
            "expected_content_length_bytes",
        }:
            if type(value) is not int:
                raise AssertionError("exact integer projection")
            projected = str(value)
        else:
            if type(value) is not str:
                raise AssertionError("exact string projection")
            projected = value
        result.append((pair[0], projected))
    if positions != sorted(set(positions)):
        raise AssertionError("pair order")
    return tuple(result)


def _exact13_json(source: object, download_kwargs: dict[str, object]) -> str:
    canonical = (
        *source.canonical_download_result_record,
        *source.canonical_integrity_authority_record,
    )
    validated = tuple(
        (name, download_kwargs[name])
        for name in source.validated_download_result_fields
    )
    value = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "admission_rule_id": source.admission_rule_id,
        "admission_rule_name": RULE_NAME,
        "outcome": source.outcome,
        "passed": source.passed,
        "blocks_candidate": source.blocks_candidate,
        "reason": source.reason,
        "normalized_values": _project_pairs(canonical),
        "validated_candidate_fields": _project_pairs(validated),
        "consumed_candidate_fields": source.consumed_download_result_fields,
        "consumed_context_items": source.consumed_integrity_authority_fields,
        "evaluator_io_used": source.evaluator_io_used,
        "adapter_id": ADAPTER_ID,
    }
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def _verify_truth(
    truth: list[dict[str, str]], source_rows: tuple[dict[str, Any], ...],
) -> None:
    formal_reader = csv.DictReader(io.StringIO(source_rows[8]["content"].decode()))
    formal_truth = list(formal_reader)
    if len(formal_truth) != 128 or len(truth) != 172:
        raise AssertionError("truth row counts")
    if tuple(row["case_id"] for row in truth[:128]) != tuple(
        row["case_id"] for row in formal_truth
    ):
        raise AssertionError("committed Exact128 identity")
    standalone = importlib.import_module(
        "covalent_ext.covapie_bulk_download_admission_admit_013_rule_logic_interface"
    )
    oracle = importlib.import_module(
        "covalent_ext.covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate"
    )
    normal_count = 0
    for prior, observed in zip(formal_truth, truth[:128], strict=True):
        if prior["assertion_kind"] == "result_contract_rejection":
            if (
                observed["formal_call_count"] != "0"
                or observed["oracle_call_count"] != "0"
                or observed["expected_reason"] != SOURCE_INVARIANT_REASON
            ):
                raise AssertionError("negative source attestation")
            continue
        values = tuple(
            _decode(prior[f"{name}_representation"])
            for name in (*DOWNLOAD_FIELDS, *AUTHORITY_FIELDS)
        )
        download_kwargs: dict[str, object] = {}
        download_lookups = 0
        complete = True
        for name, value in zip(DOWNLOAD_FIELDS, values[:4], strict=True):
            download_lookups += 1
            if value is MISSING:
                complete = False
                break
            download_kwargs[name] = value
        authority_kwargs: dict[str, object] = {}
        authority_lookups = 0
        if complete:
            for name, value in zip(AUTHORITY_FIELDS, values[4:], strict=True):
                authority_lookups += 1
                if value is not MISSING:
                    authority_kwargs[name] = value
        source = standalone.evaluate_admit_013(**download_kwargs, **authority_kwargs)
        design_result = oracle.classify_admit_013_formal_evaluator_interface_design(
            **download_kwargs, **authority_kwargs
        )
        if type(source) is not standalone.Admit013EvaluationResult:
            raise AssertionError("formal exact type")
        if type(design_result) is not oracle.Admit013EvaluationResultContractDesign:
            raise AssertionError("oracle exact type")
        source_values = tuple(getattr(source, name) for name in SOURCE_FIELDS)
        oracle_values = tuple(getattr(design_result, name) for name in SOURCE_FIELDS)
        if any(
            type(left) is not type(right) or left != right
            for left, right in zip(source_values, oracle_values, strict=True)
        ):
            raise AssertionError("source/oracle Exact12")
        expected_lookup = (
            *DOWNLOAD_FIELDS[:download_lookups],
            *AUTHORITY_FIELDS[:authority_lookups],
        )
        checks = (
            observed["routing_condition"] == "committed_Exact128_projection",
            observed["formal_call_count"] == "1",
            observed["oracle_call_count"] == "1",
            observed["candidate_key_access_count"] == "0",
            observed["evaluation_lookup_count"] == str(authority_lookups),
            observed["download_lookup_count"] == str(download_lookups),
            observed["lookup_order"] == "|".join(expected_lookup),
            observed["source_exact12_json"] == _exact12_json(source),
            observed["oracle_exact12_json"] == _exact12_json(source),
            observed["projected_exact13_json"] == _exact13_json(source, download_kwargs),
            observed["expected_reason"] == source.reason,
            observed["case_passed"] == "true",
        )
        if not all(checks):
            raise AssertionError(f"truth projection: {prior['case_id']}")
        projected = json.loads(observed["projected_exact13_json"])
        if tuple(projected) != RESULT_FIELDS:
            raise AssertionError("Exact13 JSON field order")
        authority_names = set(AUTHORITY_FIELDS)
        if any(pair[0] in authority_names for pair in projected["validated_candidate_fields"]):
            raise AssertionError("authority entered validated_candidate_fields")
        if not all(type(pair[1]) is str for pair in projected["normalized_values"]):
            raise AssertionError("non-string normalized value")
        normal_count += 1
    if normal_count != 102:
        raise AssertionError("normal Exact128 projection count")


def _verify_semantics(
    payloads: dict[str, bytes], source_rows: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    if {name: _sha(content) for name, content in payloads.items()} != OUTPUT_SHA256:
        raise AssertionError("frozen output SHA")
    contract = _csv(payloads[CONTRACT_FILE], CONTRACT_COLUMNS)
    routing = _csv(payloads[ROUTING_FILE], ROUTING_COLUMNS)
    truth = _csv(payloads[TRUTH_FILE], TRUTH_COLUMNS)
    safety = _csv(payloads[SAFETY_FILE], SAFETY_COLUMNS)
    issues = _csv(payloads[ISSUE_FILE], ISSUE_COLUMNS)
    manifest, keys = _json_no_duplicates(payloads[MANIFEST_FILE])
    if (len(contract), len(routing), len(truth), len(safety), len(issues)) != (48, 44, 172, 32, 23):
        raise AssertionError("artifact row counts")
    if any(row["contract_status"] != "frozen" for row in contract):
        raise AssertionError("contract status")
    if any(row["case_passed"] != "true" for row in (*routing, *truth)):
        raise AssertionError("routing/truth pass")
    if any(row["safety_passed"] != "true" for row in safety):
        raise AssertionError("safety pass")
    keyed_contract = {
        (row["contract_group"], row["contract_subject"]): row["contract_value"]
        for row in contract
    }
    expected_contract = {
        ("routing", "precedence"): "|".join(ROUTING_ORDER),
        ("download_result", "required_exact4"): "|".join(DOWNLOAD_FIELDS),
        ("authority", "optional_exact3"): "|".join(AUTHORITY_FIELDS),
        ("registry", "current_order"): "|".join(CURRENT_ORDER),
        ("registry", "future_order"): "|".join(FUTURE_ORDER),
        ("registry", "future_known_not_registered"): "ADMIT_014|ADMIT_015",
        ("boundary", "runtime"): "design_only_no_handler_registry_dispatcher_runtime_mutation",
        ("projection", "no_schema_widening"): "Exact13_exact_string_pairs_only",
    }
    if any(keyed_contract.get(key) != value for key, value in expected_contract.items()):
        raise AssertionError("contract semantics")
    route_by_id = {row["case_id"]: row for row in routing}
    expected_reasons = {
        "batch_non_none": CONTEXT_REASONS["batch_context"],
        "evaluation_non_mapping": CONTEXT_REASONS["evaluation_context"],
        "download_non_mapping": CONTEXT_REASONS["download_result_context"],
        "stage_non_none": CONTEXT_REASONS["stage_authorization_context"],
        "required_non_keyerror": CONTEXT_REASONS["download_result_lookup"],
        "authority_non_keyerror": CONTEXT_REASONS["evaluation_lookup"],
        "formal_wrong_type": SOURCE_TYPE_REASON,
        "formal_oracle_mismatch": SOURCE_INVARIANT_REASON,
    }
    if any(route_by_id[case]["expected_reason"] != reason for case, reason in expected_reasons.items()):
        raise AssertionError("routing reasons")
    for index, name in enumerate(DOWNLOAD_FIELDS, 1):
        row = route_by_id[f"required_{index}_missing"]
        if (
            row["lookup_order"] != "|".join(DOWNLOAD_FIELDS[:index])
            or row["formal_call_count"] != "1" or row["oracle_call_count"] != "1"
        ):
            raise AssertionError("required first-missing semantics")
    for index in range(1, 4):
        row = route_by_id[f"authority_{index}_missing"]
        if row["lookup_order"] != "|".join((*DOWNLOAD_FIELDS, *AUTHORITY_FIELDS)):
            raise AssertionError("optional authority continue semantics")
    candidate = json.loads(route_by_id["candidate_non_mapping"]["expected_result_json"])
    if candidate != {
        "schema_version": RESULT_SCHEMA_VERSION,
        "admission_rule_id": RULE_ID,
        "admission_rule_name": RULE_NAME,
        "outcome": "invalid", "passed": False, "blocks_candidate": True,
        "reason": CANDIDATE_REASON, "normalized_values": [],
        "validated_candidate_fields": [], "consumed_candidate_fields": [],
        "consumed_context_items": [], "evaluator_io_used": False,
        "adapter_id": ADAPTER_ID,
    }:
        raise AssertionError("candidate invalid Exact13")
    if payloads[ISSUE_FILE] != source_rows[4]["content"]:
        raise AssertionError("issue inventory byte continuity")
    issue_by_id = {row["issue_id"]: row for row in issues}
    open_ids = {
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    }
    if any(issue_by_id[name]["successor_effective_status"] != "open" for name in open_ids):
        raise AssertionError("open issue continuity")
    if issue_by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] != "ADMIT_013|ADMIT_014|ADMIT_015":
        raise AssertionError("coverage issue rules")
    safety_map = {row["safety_item"]: row for row in safety}
    for name in (
        "runtime_handler", "registry", "runtime_source_change", "schema_widening",
        "provider_mapping", "network", "download", "raw", "model", "checkpoint",
        "dataloader", "training", "combined_candidate_verdict", "cross_rule_aggregation",
    ):
        if safety_map[name]["expected_executed"] != "false" or safety_map[name]["observed_executed"] != "false":
            raise AssertionError("negative safety")
    _verify_truth(truth, source_rows)
    _verify_manifest(manifest, keys, contract, routing, truth, safety, issues, source_rows)
    return manifest


EXPECTED_MANIFEST_KEYS = (
    "Admit013EvaluationResult_implemented", "adapter_id", "admission_rule_id",
    "admission_rule_name", "admit_013_download_outcome_and_integrity_contract_designed",
    "admit_013_download_result_routing_contract_frozen",
    "admit_013_exact12_to_exact13_projection_frozen",
    "admit_013_formal_evaluator_interface_contract_frozen",
    "admit_013_formal_result_contract_frozen",
    "admit_013_integrity_authority_routing_contract_frozen",
    "admit_013_preconditions_audited", "admit_013_registered_in_engine",
    "admit_013_rule_logic_implemented",
    "admit_013_standalone_evaluator_interface_implemented",
    "admit_013_standalone_signature_frozen",
    "admit_013_unified_adapter_contract_frozen",
    "admit_013_unified_adapter_implemented",
    "admit_013_validation_precedence_resolved", "all_checks_passed",
    "ast_attestation_cross_python_version_portable", "candidate_invalid_call_counts",
    "candidate_invalid_projection", "candidate_mapping_invalid_reason",
    "candidate_record_semantics", "canonical_evidence_python_implementation",
    "canonical_evidence_python_version", "combined_candidate_verdict_implemented",
    "committed_exact128_case_count", "committed_exact128_case_ids_preserved",
    "committed_exact128_negative_source_attestation_count",
    "committed_exact128_normal_projection_count", "committed_normal_formal_call_count",
    "committed_normal_oracle_call_count", "context_failure_dispatch_code",
    "context_failure_flags", "context_routing_order", "context_routing_reasons",
    "contract_group_counts", "contract_row_count", "coverage_issue_affected_rules",
    "cross_rule_aggregation_implemented", "current_registered_rule_order",
    "dispatch_error_fields", "download_result_fields", "evaluate_admit_013_implemented",
    "exact13_projection", "exact13_schema_widened", "expected_base_commit",
    "expected_base_parent", "expected_base_subject", "expected_base_tree",
    "feature_semantics_audit_required_before_training",
    "first_twelve_handler_object_identity_preserved", "formal_call_count_after_routing",
    "formal_evaluator", "formal_keyword_only", "formal_result_type",
    "future_adapter_handler", "future_adapter_handler_implemented",
    "future_adapter_ready_rule_ids", "future_callable_discovered_rule_ids",
    "future_registered_rule_order", "historical_candidate_field_names_note",
    "independent_oracle", "independent_oracle_result_type",
    "integrity_authority_fields", "issue_inventory_preserved_byte_identical",
    "issue_inventory_row_count", "issue_inventory_sha256", "issue_transition_count",
    "known_not_registered_rule_ids_after_future", "known_rule_ids",
    "manifest_schema_version", "noncanonical_python_policy", "normalized_values_note",
    "open_issue_ids", "optional_authority_lookup_contract",
    "oracle_call_count_after_source_validation", "oracle_exact_type_storage_validation",
    "output_file_count", "output_files", "output_sha256",
    "output_sha256_excludes_manifest_self_hash", "present_object_identity_preserved",
    "private_missing_sentinel_used", "project", "projection_truth_formal_call_count",
    "projection_truth_matrix_group_counts", "projection_truth_matrix_row_count",
    "projection_truth_oracle_call_count", "provider_mapping_implemented",
    "provider_mapping_validated", "python_runtime_migration_policy", "readiness",
    "ready_for_bulk_download_now", "ready_for_training",
    "ready_for_unified_dispatch_runtime_with_admit_001_to_013_implementation",
    "real_download_executed", "real_provider_evaluation_ready", "recommended_next_step",
    "registry_changed", "required_download_lookup_contract", "result_fields",
    "result_schema_version", "routing_matrix_group_counts", "routing_matrix_row_count",
    "runtime_changed", "safety_row_count", "source_boundary_name",
    "source_exact12_full_invariant_validation", "source_exact_type_required",
    "source_failure_dispatch_code", "source_failure_flags", "source_input_count",
    "source_input_paths", "source_input_sha256", "source_input_verification",
    "source_invariant_invalid_reason",
    "source_oracle_full_exact12_exact_type_value_equality_required",
    "source_path_list_sha256", "source_path_sha256_pairs_sha256",
    "source_type_invalid_reason", "source_validation_before_output_read", "stage",
    "standalone_result_fields", "step", "step12d_is_final_training_feature_contract",
    "step12d_status", "string_projection_contract",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented", "validation_failures",
)


def _verify_manifest(
    manifest: dict[str, Any], keys: tuple[str, ...],
    contract: list[dict[str, str]], routing: list[dict[str, str]],
    truth: list[dict[str, str]], safety: list[dict[str, str]],
    issues: list[dict[str, str]], source_rows: tuple[dict[str, Any], ...],
) -> None:
    if EXPECTED_MANIFEST_KEYS and keys != EXPECTED_MANIFEST_KEYS:
        raise AssertionError("manifest missing/extra/reordered key")
    exact = (
        manifest.get("expected_base_commit") == BASE,
        manifest.get("expected_base_parent") == PARENT,
        manifest.get("expected_base_tree") == TREE,
        manifest.get("expected_base_subject") == SUBJECT,
        manifest.get("canonical_evidence_python_implementation") == "cpython",
        manifest.get("canonical_evidence_python_version") == "3.10.4",
        manifest.get("ast_attestation_cross_python_version_portable") is False,
        manifest.get("admission_rule_id") == RULE_ID,
        manifest.get("admission_rule_name") == RULE_NAME,
        manifest.get("adapter_id") == ADAPTER_ID,
        manifest.get("future_adapter_handler") == FUTURE_HANDLER,
        manifest.get("future_adapter_handler_implemented") is False,
        manifest.get("download_result_fields") == list(DOWNLOAD_FIELDS),
        manifest.get("integrity_authority_fields") == list(AUTHORITY_FIELDS),
        manifest.get("result_fields") == list(RESULT_FIELDS),
        manifest.get("standalone_result_fields") == list(SOURCE_FIELDS),
        manifest.get("context_routing_order") == list(ROUTING_ORDER),
        manifest.get("context_routing_reasons") == CONTEXT_REASONS,
        manifest.get("current_registered_rule_order") == list(CURRENT_ORDER),
        manifest.get("future_registered_rule_order") == list(FUTURE_ORDER),
        manifest.get("future_callable_discovered_rule_ids") == list(FUTURE_ORDER),
        manifest.get("future_adapter_ready_rule_ids") == list(FUTURE_ORDER),
        manifest.get("known_not_registered_rule_ids_after_future") == ["ADMIT_014", "ADMIT_015"],
        manifest.get("exact13_schema_widened") is False,
        manifest.get("source_input_count") == 19,
        manifest.get("source_input_paths") == [path for path, _ in SOURCE_BOUNDARY],
        manifest.get("source_input_sha256") == dict(SOURCE_BOUNDARY),
        manifest.get("source_path_list_sha256") == PATH_DIGEST,
        manifest.get("source_path_sha256_pairs_sha256") == PAIR_DIGEST,
        manifest.get("source_validation_before_output_read") is True,
        manifest.get("output_files") == list(OUTPUT_FILES),
        manifest.get("output_sha256") == {name: OUTPUT_SHA256[name] for name in OUTPUT_FILES[:-1]},
        manifest.get("output_sha256_excludes_manifest_self_hash") is True,
        manifest.get("contract_row_count") == len(contract),
        manifest.get("routing_matrix_row_count") == len(routing),
        manifest.get("projection_truth_matrix_row_count") == len(truth),
        manifest.get("safety_row_count") == len(safety),
        manifest.get("issue_inventory_row_count") == len(issues),
        manifest.get("issue_transition_count") == 0,
        manifest.get("recommended_next_step") == "implement_covapie_unified_dispatch_runtime_with_admit_001_to_013_v1",
        manifest.get("runtime_changed") is False,
        manifest.get("registry_changed") is False,
        manifest.get("provider_mapping_implemented") is False,
        manifest.get("real_download_executed") is False,
        manifest.get("all_checks_passed") is True,
        manifest.get("validation_failures") == [],
    )
    if not all(exact):
        raise AssertionError("manifest semantic contract")
    readiness = manifest.get("readiness")
    if type(readiness) is not dict:
        raise AssertionError("readiness object")
    true_keys = {
        "admit_013_preconditions_audited",
        "admit_013_download_outcome_and_integrity_contract_designed",
        "admit_013_standalone_signature_frozen",
        "admit_013_formal_result_contract_frozen",
        "admit_013_formal_evaluator_interface_contract_frozen",
        "admit_013_validation_precedence_resolved",
        "evaluate_admit_013_implemented", "Admit013EvaluationResult_implemented",
        "admit_013_rule_logic_implemented",
        "admit_013_standalone_evaluator_interface_implemented",
        "admit_013_download_result_routing_contract_frozen",
        "admit_013_integrity_authority_routing_contract_frozen",
        "admit_013_exact12_to_exact13_projection_frozen",
        "admit_013_unified_adapter_contract_frozen",
        "ready_for_unified_dispatch_runtime_with_admit_001_to_013_implementation",
        "feature_semantics_audit_required_before_training",
    }
    false_keys = {
        "admit_013_unified_adapter_implemented", "admit_013_registered_in_engine",
        "unified_dispatch_runtime_with_admit_001_to_013_implemented",
        "provider_mapping_validated", "real_provider_evaluation_ready",
        "ready_for_bulk_download_now", "combined_candidate_verdict_implemented",
        "cross_rule_aggregation_implemented", "ready_for_training",
        "step12d_is_final_training_feature_contract",
    }
    if set(readiness) != true_keys | false_keys:
        raise AssertionError("readiness key set")
    if any(readiness[key] is not True for key in true_keys):
        raise AssertionError("true readiness")
    if any(readiness[key] is not False for key in false_keys):
        raise AssertionError("false readiness")
    verification = manifest.get("source_input_verification")
    if type(verification) is not list or len(verification) != 19:
        raise AssertionError("source verification rows")
    for row, actual in zip(verification, source_rows, strict=True):
        if (
            row.get("source_order") != actual["source_order"]
            or row.get("source_relative_path") != actual["source_relative_path"]
            or row.get("expected_sha256") != actual["expected_sha256"]
            or row.get("base_tree_sha256") != actual["expected_sha256"]
            or row.get("filesystem_sha256") != actual["expected_sha256"]
            or row.get("base_tree_mode") != actual["mode"]
            or any(row.get(key) is not True for key in (
                "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
                "parent_chain_non_symlink", "safe_descendant", "pinned_fd_read",
                "source_verified",
            ))
        ):
            raise AssertionError("source verification manifest")


def _validate_lifecycle() -> str:
    if len(CANDIDATE_PATHS) != 10 or len(set(CANDIDATE_PATHS)) != 10:
        raise AssertionError("candidate Exact10")
    for relative in CANDIDATE_PATHS:
        path = ROOT / relative
        item = os.lstat(path)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise AssertionError("candidate leaf shape")
        if item.st_size > 100 * 1024 * 1024:
            raise AssertionError("candidate oversized")
        if path.suffix in {
            ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
            ".tgz", ".npz", ".tmp", ".part",
        }:
            raise AssertionError("candidate forbidden suffix")
        ignored = subprocess.run(
            ("git", "check-ignore", "-q", "--", relative), cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if ignored.returncode == 0:
            raise AssertionError("candidate ignored")
    tracked = []
    for relative in CANDIDATE_PATHS:
        result = subprocess.run(
            ("git", "ls-files", "--error-unmatch", "--", relative), cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        tracked.append(result.returncode == 0)
    if all(not value for value in tracked):
        lifecycle = "pre_commit"
    elif all(tracked):
        lifecycle = "post_commit"
    else:
        raise AssertionError("mixed lifecycle")
    pathspec = tuple(CANDIDATE_PATHS)
    if _git("diff", "--cached", "--name-only", "--", *pathspec):
        raise AssertionError("candidate staged")
    if lifecycle == "post_commit" and _git("diff", "--name-only", "--", *pathspec):
        raise AssertionError("candidate dirty")
    if lifecycle == "pre_commit":
        untracked = set(
            _git("ls-files", "--others", "--exclude-standard", "--", *pathspec)
            .decode().splitlines()
        )
        if untracked != set(CANDIDATE_PATHS):
            raise AssertionError("pre-commit candidate untracked set")
    patterns = (
        (ROOT / "src/covalent_ext", "covapie_bulk_download_admission_admit_013_unified_adapter_contract*", DESIGN_PATH),
        (ROOT / "scripts", "*admit_013_unified_adapter_contract*", CHECKER_PATH),
        (ROOT / "tests", "*admit_013_unified_adapter_contract*", TEST_PATH),
        (ROOT / "docs", "*admit_013_unified_adapter_contract*", DOC_PATH),
    )
    for parent, pattern, expected in patterns:
        matches = {
            path.relative_to(ROOT).as_posix() for path in parent.glob(pattern)
            if path.is_file() or path.is_symlink()
        }
        if matches != {expected}:
            raise AssertionError("stage top-level candidate inventory")
    if set(path.name for path in OUTPUT_ROOT.iterdir()) != set(OUTPUT_FILES):
        raise AssertionError("stage Exact6 leaf inventory")
    return lifecycle


def main() -> int:
    _assert_canonical_evidence_runtime()
    source_rows = _verify_sources()
    _verify_design_ast()
    lifecycle = _validate_lifecycle()
    payloads = _output_bytes()
    manifest = _verify_semantics(payloads, source_rows)
    runtime_content = source_rows[12]["content"]
    if _literal_registry_keys(runtime_content) != CURRENT_ORDER:
        raise AssertionError("current registry order")
    if FUTURE_HANDLER in {
        node.name for node in ast.parse(runtime_content.decode()).body
        if isinstance(node, ast.FunctionDef)
    }:
        raise AssertionError("runtime prematurely contains ADMIT_013 handler")
    print("CovaPIE ADMIT_013 unified adapter contract check: PASS")
    print(f"lifecycle={lifecycle}")
    print(f"base={BASE}")
    print(f"source_count={len(source_rows)}")
    print(f"contract_rows={manifest['contract_row_count']}")
    print(f"routing_rows={manifest['routing_matrix_row_count']}")
    print(f"truth_rows={manifest['projection_truth_matrix_row_count']}")
    print(f"safety_rows={manifest['safety_row_count']}")
    print(f"issue_rows={manifest['issue_inventory_row_count']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
