#!/usr/bin/env python3
"""Independent fail-closed checker for the CovaPIE Exact12 runtime."""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import inspect
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import fields
from pathlib import Path
from types import MappingProxyType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = "covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012"
SOURCE_RELATIVE_PATH = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py"
)
EXPECTED_SOURCE_SHA256 = "4d9a49806d4ef71a95c8ad032dfa061f7473b1cb55a573459c155f0cd5d57282"
EXPECTED_MARKER_PREFIX_SHA256 = "5d3f9bf28a022a75e84fcb49e0d85178122bfa900f13dd5f0e47bce422b24861"
MARKER = "# === EXACT12 PUBLIC " + "DISPATCH CLOSURE END ==="
BASE = "fc0f89c16b2afd2cac2e5629aa60cf8f962cbdad"
SUBJECT = "add CovaPIE ADMIT_012 unified adapter contract design v1"
STAGE = "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1"
OUTPUT_ROOT = ROOT / "data/derived/covalent_small" / STAGE
RULE_ID = "ADMIT_012"
RULE_NAME = "future_download_integrity_fields_required"
ADAPTER_ID = "covapie_admit_012_unified_adapter_v1"
KNOWN_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
REGISTERED_IDS = KNOWN_IDS[:12]
DOWNLOAD_FIELDS = (
    "download_result_status",
    "observed_http_status",
    "observed_content_length_bytes",
    "observed_sha256",
)
CONTEXT_ITEMS = (
    "allowed_download_result_statuses",
    "successful_http_status_contract",
    "content_length_contract",
    "sha256_format_contract",
)
SOURCE_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_download_result_record",
    "validated_download_result_fields",
    "consumed_download_result_fields",
    "consumed_context_items",
    "evaluator_io_used",
)
RESULT_FIELDS = (
    "schema_version",
    "admission_rule_id",
    "admission_rule_name",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "normalized_values",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
    "adapter_id",
)
ERROR_FIELDS = (
    "code",
    "admission_rule_id",
    "known_rule",
    "callable_discovered",
    "adapter_ready",
    "reason",
)
ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
    "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOMES = ("passed", "blocked", "invalid", "rejected")
EXPECTED_RULE_NAMES = {
    "ADMIT_001": "unique_candidate_identity",
    "ADMIT_002": "valid_pdb_id_format",
    "ADMIT_003": "ligand_or_het_identity_present",
    "ADMIT_004": "covalent_residue_identity_present",
    "ADMIT_005": "cys_sg_scope_only_v1",
    "ADMIT_006": "explicit_covalent_event_evidence",
    "ADMIT_007": "distance_only_inference_forbidden",
    "ADMIT_008": "topology_restoration_disposition",
    "ADMIT_009": "duplicate_identity_precheck",
    "ADMIT_010": "leakage_group_assignment_before_split",
    "ADMIT_011": "raw_overwrite_forbidden",
    "ADMIT_012": RULE_NAME,
}
EXPECTED_ADAPTER_IDS = {
    rule_id: f"covapie_admit_{index:03d}_unified_adapter_v1"
    for index, rule_id in enumerate(KNOWN_IDS[:12], 1)
}

OUTPUTS = (
    "covapie_admit_001_to_012_runtime_contract.csv",
    "covapie_admit_001_to_012_dispatch_truth_matrix.csv",
    "covapie_admit_001_to_012_registry_and_identity_audit.csv",
    "covapie_admit_001_to_012_runtime_safety_audit.csv",
    "covapie_admit_001_to_012_runtime_issue_readiness_inventory.csv",
    "covapie_admit_001_to_012_runtime_manifest.json",
)
FROZEN_OUTPUT_SHA256 = {
    "covapie_admit_001_to_012_runtime_contract.csv": "d839d9000076b1c257e4e58f7a9a4c9368dcd689dd65e819408422f9da264301",
    "covapie_admit_001_to_012_dispatch_truth_matrix.csv": "7b58708f4e22498d54575aebd618ace945c9902ac60c051ad2ee44bc3bd81e32",
    "covapie_admit_001_to_012_registry_and_identity_audit.csv": "57ed1f04df27c7b30ec4cea97aead99e7788a2968f77245280850ae26f399e59",
    "covapie_admit_001_to_012_runtime_safety_audit.csv": "354a41860031baff7bc54bc49e61787418fb40be0b5ed95170ac677609c97013",
    "covapie_admit_001_to_012_runtime_issue_readiness_inventory.csv": "6b6a543dd9fcce9a4b4451a05eae296a482093bba0bdb33bb37247bca4d17cfb",
    "covapie_admit_001_to_012_runtime_manifest.json": "bc909aefd86b62139fbb62025d9c323988a4c232ab9c960efb291fb0c196cee3",
}
FROZEN_CSV_SEMANTIC_SHA256 = {
    "covapie_admit_001_to_012_runtime_contract.csv": "e2f4874920a330a43f963e038968193d638bcab5b91a009070158407a0f9678f",
    "covapie_admit_001_to_012_dispatch_truth_matrix.csv": "42c6a00beb6bfea5e725d3e5d8a97f84a42d144ec91d6ee4d8524c485818073a",
    "covapie_admit_001_to_012_registry_and_identity_audit.csv": "377c6b05c800c8f8a8680ebe0282718f0ce57b70f22a1a9311669cccbf5479e9",
    "covapie_admit_001_to_012_runtime_safety_audit.csv": "6604624bd832d1daab675d5da65e036196f8033aab9631bb276efafccd725236",
    "covapie_admit_001_to_012_runtime_issue_readiness_inventory.csv": "39d2c2952f02c85e97b64fc4bf1d9bab6237f914b10841035ee62c5a64296ca0",
}
FROZEN_MANIFEST_SEMANTIC_SHA256 = "186118c9492f2897943398ed245728d4d3fbfd52abcc2a5848b8f9151d0fc76f"

CONTRACT_COLUMNS = (
    "contract_order",
    "contract_id",
    "contract_group",
    "contract_subject",
    "expected_value",
    "observed_value",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "entrypoint",
    "rule_id_representation",
    "candidate_record_representation",
    "batch_context_representation",
    "evaluation_context_representation",
    "download_result_context_representation",
    "stage_authorization_context_representation",
    "lookup_order",
    "evaluation_lookup_count",
    "download_lookup_count",
    "candidate_key_access_count",
    "formal_call_count",
    "oracle_call_count",
    "expected_result_or_error",
    "observed_result_or_error",
    "old_handler_identity_preserved",
    "case_passed",
)
REGISTRY_COLUMNS = (
    "audit_order",
    "audit_item",
    "expected_value",
    "observed_value",
    "audit_passed",
)
SAFETY_COLUMNS = (
    "safety_order",
    "safety_item",
    "expected_executed",
    "observed_executed",
    "evidence",
    "safety_passed",
)
ISSUE_COLUMNS = (
    "issue_id",
    "issue_type",
    "affected_fields",
    "affected_rules",
    "severity",
    "status",
    "blocking_scope",
    "blocking_reason",
    "issue_origin",
    "integration_transition",
    "issue_count",
)

SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py", "ca8e64897b30f961d999d37ce8af5eb985ddf34f332af40c29bf2142bad6e2c8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_contract.csv", "9616573151091786f07b3c4d1b6c8343a1ceb796f439e495023abd2f3ad37626"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_truth_matrix.csv", "c6d543b9c1ad6760e202074b981659ca34155c16ec0435b1cec3035c93d90901"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_registry_routing_and_oracle_audit.csv", "0ceb3aa607fb9a539a3d5a6fd519a685693d765b3606e52be9d3316ce476c752"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_manifest.json", "9895bf9b82eb9ca0f9c90ef8012af644a2b325dd971c3e6655b361fc8ff83011"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate.py", "6de88444d8ee0b62e301fdb19e050166c80344cc45b3ee0612998a72c188f162"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract.csv", "12228051428134223dc4db4ec418ced573637047189056f1fb8df908ca2fe6c8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_download_result_projection_and_context_routing_matrix.csv", "50d0e3d8ba7352d139d35a6cda35afad7f40ef4ea111bbea7b3cd31200ec9839"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_result_projection_truth_matrix.csv", "843754e8e8c4246f156ac27079fe0b890e62ed1df0703398e21af9b5bdb94fe7"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_safety_audit.csv", "736066e78df6e0acf28c539c8432b539855212ef1ff76693feae94d4725cc499"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_issue_readiness_inventory.csv", "bac586f54afac5a860a32ed161b6b8f41210b6ae06eb29f368045f10b3ac81e5"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract_manifest.json", "1df0e2a09817b7763ec4eb767663db169d3239385094da151af28150c2c55d25"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py", "a7b8585ea6d0080e87fc97f29026fbf5df4667dff21729c95f3045d762a55840"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_contract.csv", "c5c383e9a9e17c5eb5a4b2c92455da89a78e66f75df7ff31ce0494f08281433e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_truth_matrix.csv", "dc97cd08eabad03315a1533332e2b243122696b605c701051f3024f6189cb5d8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_purity_audit.csv", "c0773686a1a9d2d4406e09ff33bf3e217eb9d3135e8556d7461b208ec12990e9"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_manifest.json", "ad131895c0acfdaf5b350105031647bdcac9667370fb6cd43baf8826bea995c8"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate.py", "eea31caa76e06507f7dd482dc7c6b2928f6d0f28ded33c47eb31d25b3be7a927"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv", "44709c3a679368476c87bcd97dafa2f9cf9bddb4af534c6eb950c565d0919aec"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_truth_matrix.csv", "cc848914ea24b376e29c477c4c0b5e8d32d6fc7caee11873f7a73c4bd207d6db"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_contract_manifest.json", "2845c2623a01087af8842177f4502402d0a8875a77ce12c6a49e2f77c60dae01"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py", "92d6ab08c4e9fa4bd448895687c897f06a596d4fb73a2e9cf7e88ffebaa6448f"),
    ("src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py", "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978"),
)

PUBLIC_DEFINITIONS = (
    "_raise_dispatch_error",
    "_admit012_context_failure",
    "_admit012_adapter_failure",
    "_admit012_candidate_invalid",
    "_prevalidate_admit012_source",
    "_expected_admit012_from_oracle",
    "_validate_admit012_oracle_equivalence",
    "_project_download_result_pairs_to_exact_string_pairs",
    "_project_admit012_exact13",
    "_evaluate_registered_admit_012",
    "evaluate_admission_rule",
)
EXPECTED_AST_SHA256 = {
    "_raise_dispatch_error": "adb1d13a5bea21730e5d56742c1ba46faa30b5c31d80f827a892de73cc6e1356",
    "_admit012_context_failure": "727daa629805ac88d7d9304592a5736f73f1a619b13731f9b943ab654cc01eec",
    "_admit012_adapter_failure": "0949ac4e46dde5177bccb5254e8909b5a9812b177a545490d271f9f9477af065",
    "_admit012_candidate_invalid": "c3f55045ac3a9dda417d3351c385b17f6816b5fe1490cebe8a4554353fb6b683",
    "_prevalidate_admit012_source": "6eba3074096672ddac9ffbef878d5e47692af45f461b50c1f089433f592e7994",
    "_expected_admit012_from_oracle": "a2e242f833305b9e93a8fcb1a742044d6f4b1b4b10b18f6fe73b6e003f3e9b86",
    "_validate_admit012_oracle_equivalence": "d7b9b96b73eb220a8dcf43b107254a9aa33d0ccebe9e738b07aeafff4ff0bf90",
    "_project_download_result_pairs_to_exact_string_pairs": "b1a0367a6c5cf13a2f91b1c0679ef51c046afb0d0c1ef3d6e7bb126d03f7c2c3",
    "_project_admit012_exact13": "43533eb5a11a93a0c7db3923619636bdf7b6bf10ae270813f994c6ba179fcba2",
    "_evaluate_registered_admit_012": "5198f5571b9d008f81c92af77b56a54e42a62df40cd3bd1e500a20d0e15bde20",
    "evaluate_admission_rule": "436c53241254cf1229d4083a6caa3d555e10e17583c8ae4006275727b05fd5e9",
}
TRUE_READINESS = (
    "admit_012_preconditions_audited",
    "admit_012_download_integrity_field_contract_frozen",
    "admit_012_field_semantics_complete",
    "admit_012_routing_responsibility_resolved",
    "admit_012_standalone_signature_frozen",
    "admit_012_formal_result_contract_frozen",
    "admit_012_standalone_evaluator_interface_implemented",
    "admit_012_rule_logic_implemented",
    "evaluate_admit_012_implemented",
    "Admit012EvaluationResult_implemented",
    "admit_012_unified_adapter_contract_frozen",
    "admit_012_exact10_to_exact13_projection_frozen",
    "admit_012_download_result_routing_contract_frozen",
    "admit_012_unified_adapter_implemented",
    "admit_012_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented",
    "unified_dispatch_runtime_with_admit_001_to_012_implemented",
    "ready_for_admit_013_formal_evaluator_interface_preconditions_audit",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_013_preconditions_audited",
    "admit_013_implemented",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _semantic_sha(value: object) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _git(*arguments: str) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise AssertionError("source-boundary git command failed")
    return result.stdout


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return int(item.st_dev), int(item.st_ino), int(item.st_mode)


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
        raise AssertionError("parent chain resolved drift")


def _read_pinned(path: Path, identity: tuple[int, int, int]) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if _identity(os.fstat(descriptor)) != identity:
            raise AssertionError("pinned descriptor identity drift")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _identity(os.fstat(descriptor)) != identity
            or _identity(os.lstat(path)) != identity
        ):
            raise AssertionError("pinned file changed during read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _attest_successor_source_before_import(
    repo_root: Path = ROOT,
    *,
    relative_path: Path = SOURCE_RELATIVE_PATH,
    expected_sha256: str = EXPECTED_SOURCE_SHA256,
    event_hook: Any = None,
) -> dict[str, Any]:
    root = Path(os.path.abspath(repo_root))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise AssertionError("successor repository root unsafe")
    relative = Path(relative_path)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise AssertionError("successor relative path unsafe")
    target = root / relative
    if root not in target.parents:
        raise AssertionError("successor escaped repository")
    _parent_chain(target.parent, root)
    item = os.lstat(target)
    identity = _identity(item)
    if (
        not stat.S_ISREG(item.st_mode)
        or stat.S_ISLNK(item.st_mode)
        or target.resolve(strict=True) != target
    ):
        raise AssertionError("successor source leaf unsafe")
    if event_hook is not None:
        event_hook("before_open", target=target, identity=identity)
    content = _read_pinned(target, identity)
    if event_hook is not None:
        event_hook("after_read", target=target, identity=identity)
    if _identity(os.lstat(root)) != root_identity:
        raise AssertionError("successor repository root identity drift")
    actual = _sha(content)
    if actual != expected_sha256:
        raise AssertionError("successor source SHA mismatch")
    return {
        "repo_root": root,
        "relative_path": relative,
        "path": target,
        "root_identity": root_identity,
        "identity": identity,
        "sha256": actual,
        "content": content,
        "tree": ast.parse(content, filename=str(target)),
    }


def _assert_attested_successor_unchanged(attested: Mapping[str, Any]) -> None:
    root = attested["repo_root"]
    target = attested["path"]
    if _identity(os.lstat(root)) != attested["root_identity"]:
        raise AssertionError("attested repository root changed")
    _parent_chain(target.parent, root)
    item = os.lstat(target)
    if _identity(item) != attested["identity"]:
        raise AssertionError("attested successor identity changed")
    content = _read_pinned(target, attested["identity"])
    if content != attested["content"] or _sha(content) != attested["sha256"]:
        raise AssertionError("attested successor bytes changed")


def _verify_sources() -> tuple[dict[str, Any], ...]:
    if len(SOURCE_BOUNDARY) != 23 or len({path for path, _ in SOURCE_BOUNDARY}) != 23:
        raise AssertionError("Exact23 source boundary drift")
    if _git("show", "-s", "--format=%s", BASE).decode().rstrip("\n") != SUBJECT:
        raise AssertionError("base subject mismatch")
    _git("merge-base", "--is-ancestor", BASE, "HEAD")
    root = Path(os.path.abspath(ROOT))
    inspected = []
    for relative, expected in SOURCE_BOUNDARY:
        path = Path(relative)
        if (
            path.is_absolute()
            or not path.parts
            or ".." in path.parts
            or path.parts[:2] == ("data", "raw")
            or path.parts[0] == "checkpoints"
            or STAGE in path.parts
        ):
            raise AssertionError("unsafe source boundary path")
        target = root / path
        _parent_chain(target.parent, root)
        item = os.lstat(target)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or target.resolve(strict=True) != target
        ):
            raise AssertionError("source leaf unsafe")
        if _git("ls-files", "--error-unmatch", "--", relative).decode() != f"{relative}\n":
            raise AssertionError("source not tracked")
        tree = _git("ls-tree", BASE, "--", relative).splitlines()
        if len(tree) != 1 or b"\t" not in tree[0]:
            raise AssertionError("base tree cardinality")
        metadata, tree_path = tree[0].split(b"\t", 1)
        parts = metadata.split()
        if (
            tree_path.decode() != relative
            or len(parts) != 3
            or parts[0] not in (b"100644", b"100755")
            or parts[1] != b"blob"
        ):
            raise AssertionError("base tree entry")
        inspected.append((relative, expected, target, _identity(item), parts[0].decode()))
    verified = []
    for index, (relative, expected, target, identity, mode) in enumerate(inspected, 1):
        filesystem = _read_pinned(target, identity)
        base_bytes = _git("show", f"{BASE}:{relative}")
        if expected != _sha(filesystem) or expected != _sha(base_bytes):
            raise AssertionError(f"source SHA mismatch: {relative}")
        verified.append(
            {
                "source_order": index,
                "source_relative_path": relative,
                "base_tree_mode": mode,
                "expected_sha256": expected,
                "content": filesystem,
            }
        )
    return tuple(verified)


def _ast_sha(node: ast.AST) -> str:
    return _sha(
        ast.dump(node, annotate_fields=True, include_attributes=False).encode()
    )


def _verify_runtime_ast(attested: Mapping[str, Any] | bytes) -> None:
    if isinstance(attested, bytes):
        content = attested
        tree = ast.parse(content)
    else:
        content = attested["content"]
        tree = attested["tree"]
    text = content.decode("utf-8")
    if text.count(MARKER) != 1:
        raise AssertionError("unique public marker drift")
    prefix = text.split(MARKER, 1)[0].encode()
    if _sha(prefix) != EXPECTED_MARKER_PREFIX_SHA256:
        raise AssertionError("marker-prefix SHA drift")
    marker_line = text[: text.index(MARKER)].count("\n") + 1
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in PUBLIC_DEFINITIONS
    }
    if tuple(definitions) != PUBLIC_DEFINITIONS:
        raise AssertionError("public definition order/cardinality drift")
    if any(node.lineno >= marker_line for node in definitions.values()):
        raise AssertionError("public definition placed after marker")
    actual_hashes = {name: _ast_sha(definitions[name]) for name in PUBLIC_DEFINITIONS}
    if actual_hashes != EXPECTED_AST_SHA256:
        raise AssertionError("normalized public AST SHA drift")

    imports = [
        node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    if any(
        isinstance(node, (ast.Import, ast.ImportFrom)) and node not in imports
        for node in ast.walk(tree)
    ):
        raise AssertionError("local or nested import forbidden")
    project_imports = []
    for node in imports:
        if isinstance(node, ast.ImportFrom) and node.module == "covalent_ext":
            project_imports.extend((alias.name, alias.asname) for alias in node.names)
    if project_imports != [
        (
            "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011",
            "predecessor",
        ),
        ("covapie_bulk_download_admission_admit_012_rule_logic_interface", "admit012"),
        (
            "covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate",
            "admit012_oracle",
        ),
    ]:
        raise AssertionError("exact project import provenance drift")
    if "classify_admit_012_unified_adapter_design" in prefix.decode():
        raise AssertionError("adapter design classifier leaked into runtime closure")

    protected = set(PUBLIC_DEFINITIONS) | {
        "predecessor",
        "admit012",
        "admit012_oracle",
        "UnifiedAdmissionRuleEvaluation",
        "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
        "KNOWN_RULE_IDS",
        "CALLABLE_DISCOVERED_RULE_IDS",
        "ADAPTER_READY_RULE_IDS",
        "LEGACY_ADAPTER_NOT_READY_RULE_IDS",
        "RULE_NAMES",
        "ADAPTER_IDS",
        "EVALUATOR_REGISTRY",
    }
    counts = Counter()
    for node in tree.body:
        bound: list[str] = []
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            bound.append(node.name)
        elif isinstance(node, ast.ImportFrom):
            bound.extend(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, ast.Assign):
            bound.extend(
                target.id for target in node.targets if isinstance(target, ast.Name)
            )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            bound.append(node.target.id)
        for name in bound:
            if name in protected:
                counts[name] += 1
                if node.lineno >= marker_line:
                    raise AssertionError(f"protected binding after marker: {name}")
    if set(counts) != protected or any(count != 1 for count in counts.values()):
        raise AssertionError("protected binding duplicate/missing/rebinding")

    allowed_names = set(PUBLIC_DEFINITIONS) | {
        "UnifiedAdmissionDispatchError",
        "UnifiedAdmissionRuleEvaluation",
        "Exception",
        "TypeError",
        "ValueError",
        "any",
        "enumerate",
        "fields",
        "getattr",
        "isinstance",
        "len",
        "str",
        "tuple",
        "type",
        "vars",
        "zip",
        "result_type",
        "handler",
    }
    allowed_attributes = {
        "admit012.Admit012EvaluationResult",
        "admit012.evaluate_admit_012",
        "admit012_oracle.classify_admit_012_formal_evaluator_interface_design",
    }
    for name, function in definitions.items():
        for node in ast.walk(function):
            if isinstance(node, (ast.Global, ast.Nonlocal, ast.Import, ast.ImportFrom)):
                raise AssertionError(f"public closure mutation/import: {name}")
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del)):
                raise AssertionError(f"public closure object mutation: {name}")
            if isinstance(node, ast.Name) and node.id.startswith("__"):
                raise AssertionError("reflective dunder name forbidden")
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                if node.func.id not in allowed_names:
                    raise AssertionError(f"unknown public callable: {node.func.id}")
            elif isinstance(node.func, ast.Attribute):
                rendered = ast.unparse(node.func)
                if rendered not in allowed_attributes:
                    raise AssertionError(f"imported public callable forbidden: {rendered}")
            else:
                raise AssertionError("dynamic/subscript public callable forbidden")
    direct_calls = {
        name: {
            node.func.id
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in PUBLIC_DEFINITIONS
        }
        for name, function in definitions.items()
    }

    def closure(root: str) -> set[str]:
        found = {root}
        pending = [root]
        while pending:
            current = pending.pop()
            for called in direct_calls[current]:
                if called not in found:
                    found.add(called)
                    pending.append(called)
        return found

    expected_handler = set(PUBLIC_DEFINITIONS[:-1])
    if closure("_evaluate_registered_admit_012") != expected_handler:
        raise AssertionError("handler transitive closure drift")
    if closure("evaluate_admission_rule") != {
        "evaluate_admission_rule",
        "_raise_dispatch_error",
    }:
        raise AssertionError("dispatcher direct closure drift")
    dispatcher_source = ast.get_source_segment(text, definitions["evaluate_admission_rule"])
    if (
        dispatcher_source is None
        or "handler = EVALUATOR_REGISTRY[admission_rule_id]" not in dispatcher_source
        or "return handler(" not in dispatcher_source
    ):
        raise AssertionError("dispatcher local registry handler binding drift")


def _csv(content: bytes, columns: Sequence[str]) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != tuple(columns):
        raise AssertionError("CSV header mismatch")
    rows = tuple(dict(row) for row in reader)
    if any(
        tuple(row) != tuple(columns) or any(value is None for value in row.values())
        for row in rows
    ):
        raise AssertionError("CSV row shape mismatch")
    return rows


def _output_bytes(output_root: Path, *, event_hook: Any = None) -> dict[str, bytes]:
    root = Path(os.path.abspath(output_root))
    _parent_chain(root.parent, Path(root.anchor))
    parent_identity = _identity(os.lstat(root.parent))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise AssertionError("output root unsafe")
    names = tuple(os.listdir(root))
    if len(names) != 6 or set(names) != set(OUTPUTS):
        raise AssertionError("output inventory")
    identities = {}
    for name in OUTPUTS:
        item = os.lstat(root / name)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise AssertionError("output leaf unsafe")
        identities[name] = _identity(item)
    if event_hook is not None:
        event_hook("after_preflight", root=root, identities=dict(identities))
    descriptor = os.open(
        root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    try:
        if _identity(os.fstat(descriptor)) != root_identity:
            raise AssertionError("pinned output root drift")
        contents = {}
        for name in OUTPUTS:
            if event_hook is not None:
                event_hook("before_leaf_open", root=root, name=name)
            leaf = os.open(
                name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=descriptor,
            )
            try:
                if _identity(os.fstat(leaf)) != identities[name]:
                    raise AssertionError("output stat/open race")
                chunks = []
                while True:
                    chunk = os.read(leaf, 1 << 16)
                    if not chunk:
                        break
                    chunks.append(chunk)
                if (
                    _identity(os.fstat(leaf)) != identities[name]
                    or _identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False))
                    != identities[name]
                ):
                    raise AssertionError("output leaf changed during read")
                contents[name] = b"".join(chunks)
            finally:
                os.close(leaf)
        if event_hook is not None:
            event_hook("before_final_validation", root=root, identities=dict(identities))
        if (
            _identity(os.lstat(root.parent)) != parent_identity
            or _identity(os.lstat(root)) != root_identity
            or set(os.listdir(descriptor)) != set(OUTPUTS)
        ):
            raise AssertionError("output tree changed")
        return contents
    finally:
        os.close(descriptor)


def _contract_expected() -> tuple[tuple[str, str, str], ...]:
    return (
        ("identity", "Exact11 public result/error/constants identity", "7/7"),
        ("registry", "Exact12 order", "ADMIT_001_to_ADMIT_012"),
        ("registry", "first eleven handler object identities", "11/11"),
        ("registry", "sole new handler", "_evaluate_registered_admit_012"),
        ("sets", "known", "ADMIT_001_to_ADMIT_015"),
        ("sets", "callable and ready", "ADMIT_001_to_ADMIT_012"),
        ("sets", "legacy adapter not ready", "empty"),
        ("routing", "five-envelope signature", "frozen"),
        ("routing", "precedence", "batch|evaluation_mapping|policy4|download_mapping|stage|candidate_mapping|download4|formal|source|oracle|equality|projection"),
        ("routing", "context reasons", "Exact8"),
        ("candidate", "Mapping envelope only", "zero_key_access"),
        ("candidate", "non-Mapping result", "ADMIT_012_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("download", "first missing", "omit_keyword_and_stop_later_lookup"),
        ("download", "present None False zero", "forwarded_by_identity"),
        ("formal", "call", "keyword_only_exactly_once"),
        ("formal", "exception", "propagated_oracle_zero"),
        ("source", "type", "exact_Admit012EvaluationResult"),
        ("source", "Exact10", "storage_order_types_reconstruction_invariants"),
        ("oracle", "call", "same_kwargs_exactly_once"),
        ("oracle", "type", "Admit012EvaluationResultContractDesign"),
        ("equality", "full Exact10", "exact_type_and_value_each_position"),
        ("projection", "status", "exact_str_unchanged"),
        ("projection", "HTTP", "exact_int_to_decimal_str"),
        ("projection", "content", "exact_int_to_decimal_str"),
        ("projection", "SHA", "exact_str_unchanged"),
        ("projection", "prefix", "empty_or_ordered_Exact4_prefix"),
        ("projection", "schema", "Exact13_unchanged_string_pairs_only"),
        ("projection", "historical field names", "download_result_semantics_not_candidate_source"),
        ("dispatch", "precedence", "exact_str|known|callable|ready|local_handler"),
        ("dispatch", "ADMIT_013_to_015", "known_not_registered"),
        ("truth", "Exact11 regression", "Exact534"),
        ("truth", "ADMIT_012 formal", "Exact105"),
        ("truth", "ADMIT_012 adapter contract", "Exact43"),
        ("issue", "single transition", "ADMIT_012_removed_from_open_coverage"),
        ("boundary", "ADMIT_013", "not_implemented"),
        ("boundary", "combined verdict and aggregation", "not_implemented"),
        ("boundary", "provider network download raw", "not_executed"),
        ("boundary", "model checkpoint training", "not_executed"),
        ("training", "feature semantics audit", "required_Step12D_smoke_only"),
        ("materializer", "publication", "set_atomic_RENAME_NOREPLACE"),
        ("materializer", "GPFS EINVAL", "fail_closed_no_replace"),
        ("materializer", "existing exact set", "inode_preserving_noop"),
    )


def _validate_output_tree(
    output_root: Path = OUTPUT_ROOT,
    *,
    enforce_frozen_hashes: bool = True,
    source_records: tuple[dict[str, Any], ...] | None = None,
) -> dict[str, str]:
    sources = _verify_sources() if source_records is None else source_records
    contents = _output_bytes(output_root)
    hashes = {name: _sha(content) for name, content in contents.items()}
    contract = _csv(contents[OUTPUTS[0]], CONTRACT_COLUMNS)
    truth = _csv(contents[OUTPUTS[1]], TRUTH_COLUMNS)
    registry = _csv(contents[OUTPUTS[2]], REGISTRY_COLUMNS)
    safety = _csv(contents[OUTPUTS[3]], SAFETY_COLUMNS)
    issues = _csv(contents[OUTPUTS[4]], ISSUE_COLUMNS)
    if tuple(map(len, (contract, truth, registry, safety, issues))) != (42, 694, 39, 29, 16):
        raise AssertionError("CSV exact row counts")
    expected_contract = tuple(
        {
            "contract_order": str(index),
            "contract_id": f"CONTRACT_{index:03d}",
            "contract_group": group,
            "contract_subject": subject,
            "expected_value": value,
            "observed_value": value,
            "contract_passed": "true",
        }
        for index, (group, subject, value) in enumerate(_contract_expected(), 1)
    )
    if contract != expected_contract:
        raise AssertionError("contract complete semantic equality")
    groups = {
        "predecessor_exact11_regression": 534,
        "admit012_formal_exact105": 105,
        "admit012_adapter_exact43": 43,
        "exact12_dispatcher": 12,
    }
    if (
        Counter(row["case_group"] for row in truth) != groups
        or tuple(row["case_order"] for row in truth)
        != tuple(str(index) for index in range(1, 695))
        or len({row["case_id"] for row in truth}) != 694
        or any(
            row["case_passed"] != "true"
            or row["expected_result_or_error"] != row["observed_result_or_error"]
            or row["old_handler_identity_preserved"] != "true"
            for row in truth
        )
    ):
        raise AssertionError("truth complete status/order/group semantics")
    predecessor_truth = _csv(sources[2]["content"], (
        "case_order", "case_id", "case_group", "admission_rule_id", "behavior",
        "expected_result_or_error", "observed_result_or_error", "expected_reason",
        "observed_reason", "formal_call_count", "oracle_call_count",
        "candidate_access_status", "handler_identity_status", "case_passed",
    ))
    if tuple(row["case_id"] for row in truth[:534]) != tuple(
        f"EXACT11_{row['case_id']}" for row in predecessor_truth
    ):
        raise AssertionError("Exact11 source truth lineage")
    standalone_truth = _csv(sources[14]["content"], (
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
    ))
    if tuple(row["case_id"] for row in truth[534:639]) != tuple(
        f"ADMIT012_FORMAL_{row['case_id']}" for row in standalone_truth
    ):
        raise AssertionError("Exact105 source truth lineage")
    adapter_routing = _csv(sources[7]["content"], (
        "matrix_order", "matrix_group", "case_id", "routing_condition",
        "envelope_representation", "lookup_count", "lookup_order",
        "candidate_key_access_count", "formal_call_count", "oracle_call_count",
        "identity_preserved", "expected_dispatch_code", "expected_reason",
        "expected_result_json", "case_passed",
    ))
    if tuple(row["case_id"] for row in truth[639:682]) != tuple(
        f"ADMIT012_CONTRACT_{row['case_id']}" for row in adapter_routing
    ):
        raise AssertionError("Exact43 source routing lineage")
    if any(row["audit_passed"] != "true" or row["expected_value"] != row["observed_value"] for row in registry):
        raise AssertionError("registry identity audit status")
    required_registry = {
        *(f"handler_identity:{rule_id}" for rule_id in KNOWN_IDS[:11]),
        "handler_binding:ADMIT_012",
        "exact11_registry_order",
        "exact12_registry_order",
        "rule_names",
        "adapter_ids",
        *(f"not_registered:{rule_id}" for rule_id in KNOWN_IDS[12:]),
    }
    if not required_registry <= {row["audit_item"] for row in registry}:
        raise AssertionError("registry audit coverage")
    if any(
        row["safety_passed"] != "true"
        or row["expected_executed"] != row["observed_executed"]
        for row in safety
    ):
        raise AssertionError("safety audit status")
    source_issues = _csv(sources[10]["content"], ISSUE_COLUMNS)
    expected_issues = [dict(row) for row in source_issues]
    coverage = next(
        row
        for row in expected_issues
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    )
    coverage["affected_rules"] = "ADMIT_013|ADMIT_014|ADMIT_015"
    coverage["integration_transition"] = (
        "unified_dispatch_runtime_with_admit_001_to_012_implemented_v1"
    )
    if issues != tuple(expected_issues):
        raise AssertionError("Exact16 single issue transition")
    issue_map = {row["issue_id"]: row for row in issues}
    if (
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] != "open"
        or issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"]
        != "open"
    ):
        raise AssertionError("required issues unexpectedly closed")

    semantic_hashes = {
        OUTPUTS[0]: _semantic_sha(contract),
        OUTPUTS[1]: _semantic_sha(truth),
        OUTPUTS[2]: _semantic_sha(registry),
        OUTPUTS[3]: _semantic_sha(safety),
        OUTPUTS[4]: _semantic_sha(issues),
    }
    if FROZEN_CSV_SEMANTIC_SHA256 and semantic_hashes != FROZEN_CSV_SEMANTIC_SHA256:
        raise AssertionError("CSV independent complete semantic SHA")
    manifest = json.loads(contents[OUTPUTS[5]])
    if type(manifest) is not dict:
        raise AssertionError("manifest object required")
    if FROZEN_MANIFEST_SEMANTIC_SHA256 and _semantic_sha(manifest) != FROZEN_MANIFEST_SEMANTIC_SHA256:
        raise AssertionError("manifest independent complete semantic SHA")
    readiness = {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }
    required_manifest = {
        "project": "CovaPIE",
        "stage": STAGE,
        "expected_base_commit": BASE,
        "expected_base_subject": SUBJECT,
        "source_input_count": 23,
        "registered_rule_ids": list(REGISTERED_IDS),
        "known_not_registered_rule_ids": list(KNOWN_IDS[12:]),
        "registered_rule_count": 12,
        "contract_row_count": 42,
        "truth_matrix_row_count": 694,
        "registry_identity_audit_row_count": 39,
        "safety_audit_row_count": 29,
        "issue_inventory_row_count": 16,
        "issue_transition_count": 1,
        "admit_013_implemented": False,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "provider_mapping_validated": False,
        "ready_for_training": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": "audit_covapie_admit_013_formal_evaluator_interface_preconditions_v1",
        "all_checks_passed": True,
    }
    if any(manifest.get(key) != value for key, value in required_manifest.items()):
        raise AssertionError("manifest required semantics")
    if manifest.get("readiness") != readiness or any(
        manifest.get(name) is not value for name, value in readiness.items()
    ):
        raise AssertionError("manifest readiness")
    if (
        manifest.get("source_input_paths") != [path for path, _ in SOURCE_BOUNDARY]
        or manifest.get("source_input_sha256") != dict(SOURCE_BOUNDARY)
        or manifest.get("output_sha256") != {name: hashes[name] for name in OUTPUTS[:5]}
    ):
        raise AssertionError("manifest source/output hashes")
    if enforce_frozen_hashes and hashes != FROZEN_OUTPUT_SHA256:
        raise AssertionError("frozen output SHA")
    return hashes


class _CountingMapping(Mapping[str, object]):
    def __init__(self, values: Mapping[str, object]) -> None:
        self.values = dict(values)
        self.calls: list[str] = []
        self.iterated = False
        self.sized = False

    def __getitem__(self, key: str) -> object:
        self.calls.append(key)
        return self.values[key]

    def __iter__(self):
        self.iterated = True
        return iter(self.values)

    def __len__(self) -> int:
        self.sized = True
        return len(self.values)


class _CandidateBomb(Mapping[str, object]):
    def __init__(self) -> None:
        self.accesses = 0

    def __getitem__(self, key: str) -> object:
        self.accesses += 1
        raise AssertionError("candidate accessed")

    def __iter__(self):
        raise AssertionError("candidate iterated")

    def __len__(self) -> int:
        raise AssertionError("candidate sized")


def _verify_runtime_identity(runtime: Any) -> None:
    predecessor = runtime.predecessor
    original = importlib.import_module(
        "covalent_ext.covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004"
    )
    for name in (
        "UnifiedAdmissionRuleEvaluation",
        "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
    ):
        if (
            getattr(runtime, name) is not getattr(predecessor, name)
            or getattr(runtime, name) is not getattr(original, name)
        ):
            raise AssertionError(f"public identity drift: {name}")
    if inspect.signature(runtime.evaluate_admission_rule) != inspect.signature(
        predecessor.evaluate_admission_rule
    ):
        raise AssertionError("dispatcher signature drift")
    expected_handler_signature = (
        "(candidate_record: 'object', *, batch_context: 'object', "
        "evaluation_context: 'object', download_result_context: 'object', "
        "stage_authorization_context: 'object') -> 'UnifiedAdmissionRuleEvaluation'"
    )
    if str(inspect.signature(runtime._evaluate_registered_admit_012)) != expected_handler_signature:
        raise AssertionError("ADMIT_012 handler signature drift")
    if (
        type(runtime.EVALUATOR_REGISTRY) is not MappingProxyType
        or tuple(runtime.EVALUATOR_REGISTRY) != REGISTERED_IDS
        or any(
            runtime.EVALUATOR_REGISTRY[rule_id]
            is not predecessor.EVALUATOR_REGISTRY[rule_id]
            for rule_id in KNOWN_IDS[:11]
        )
        or runtime.EVALUATOR_REGISTRY[RULE_ID]
        is not runtime._evaluate_registered_admit_012
    ):
        raise AssertionError("Exact12 registry/identity drift")
    if (
        type(runtime.RULE_NAMES) is not MappingProxyType
        or dict(runtime.RULE_NAMES) != EXPECTED_RULE_NAMES
        or type(runtime.ADAPTER_IDS) is not MappingProxyType
        or dict(runtime.ADAPTER_IDS) != EXPECTED_ADAPTER_IDS
    ):
        raise AssertionError("immutable names/adapters drift")
    if (
        tuple(runtime.KNOWN_RULE_IDS) != KNOWN_IDS
        or tuple(runtime.CALLABLE_DISCOVERED_RULE_IDS) != REGISTERED_IDS
        or tuple(runtime.ADAPTER_READY_RULE_IDS) != REGISTERED_IDS
        or tuple(runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS) != ()
    ):
        raise AssertionError("known/callable/ready sets drift")
    if hasattr(runtime, "evaluate_all_rules") or hasattr(runtime, "combined_candidate_verdict"):
        raise AssertionError("aggregation API leaked")


def _verify_runtime_behavior(runtime: Any) -> None:
    context_values = dict(zip(CONTEXT_ITEMS, runtime.admit012.FORMAL_CONTEXT_VALUES, strict=True))
    error_cases = (
        ({"batch_context": object(), "evaluation_context": object(), "download_result_context": object()}, "ADMIT_012_BATCH_CONTEXT_MUST_BE_NONE", 0),
        ({"evaluation_context": object(), "download_result_context": object()}, "ADMIT_012_EVALUATION_CONTEXT_MAPPING_REQUIRED", 0),
        ({"evaluation_context": {}, "download_result_context": object()}, "ADMIT_012_ALLOWED_DOWNLOAD_RESULT_STATUSES_REQUIRED", 0),
        ({"evaluation_context": {CONTEXT_ITEMS[0]: object()}, "download_result_context": object()}, "ADMIT_012_SUCCESSFUL_HTTP_STATUS_CONTRACT_REQUIRED", 0),
        ({"evaluation_context": dict(zip(CONTEXT_ITEMS[:2], (object(), object()), strict=True)), "download_result_context": object()}, "ADMIT_012_CONTENT_LENGTH_CONTRACT_REQUIRED", 0),
        ({"evaluation_context": dict(zip(CONTEXT_ITEMS[:3], (object(), object(), object()), strict=True)), "download_result_context": object()}, "ADMIT_012_SHA256_FORMAT_CONTRACT_REQUIRED", 0),
        ({"evaluation_context": context_values, "download_result_context": object()}, "ADMIT_012_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED", 0),
        ({"evaluation_context": context_values, "download_result_context": {}, "stage_authorization_context": object()}, "ADMIT_012_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE", 0),
    )
    for kwargs, reason, candidate_access in error_cases:
        candidate = _CandidateBomb()
        try:
            runtime._evaluate_registered_admit_012(
                candidate,
                batch_context=kwargs.get("batch_context"),
                evaluation_context=kwargs.get("evaluation_context"),
                download_result_context=kwargs.get("download_result_context"),
                stage_authorization_context=kwargs.get("stage_authorization_context"),
            )
        except runtime.UnifiedAdmissionDispatchError as error:
            expected = (
                "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
                RULE_ID,
                True,
                True,
                True,
                reason,
            )
            if tuple(getattr(error, name) for name in ERROR_FIELDS) != expected:
                raise AssertionError("context failure semantics drift")
        else:
            raise AssertionError("context routing failure missing")
        if candidate.accesses != candidate_access:
            raise AssertionError("candidate accessed before routing complete")

    invalid = runtime._evaluate_registered_admit_012(
        object(),
        batch_context=None,
        evaluation_context=context_values,
        download_result_context={},
        stage_authorization_context=None,
    )
    expected_invalid = (
        runtime.RESULT_SCHEMA_VERSION,
        RULE_ID,
        RULE_NAME,
        "invalid",
        False,
        True,
        "ADMIT_012_CANDIDATE_RECORD_MAPPING_INVALID",
        (),
        (),
        (),
        CONTEXT_ITEMS,
        False,
        ADAPTER_ID,
    )
    if tuple(getattr(invalid, name) for name in RESULT_FIELDS) != expected_invalid:
        raise AssertionError("candidate invalid Exact13 drift")

    for missing_index in range(4):
        evaluation = _CountingMapping(context_values)
        values = {
            "download_result_status": "success",
            "observed_http_status": 200,
            "observed_content_length_bytes": 0,
            "observed_sha256": "0123456789abcdef" * 4,
        }
        download = _CountingMapping(
            {name: values[name] for name in DOWNLOAD_FIELDS[:missing_index]}
        )
        candidate = _CandidateBomb()
        value = runtime._evaluate_registered_admit_012(
            candidate,
            batch_context=None,
            evaluation_context=evaluation,
            download_result_context=download,
            stage_authorization_context=None,
        )
        if (
            evaluation.calls != list(CONTEXT_ITEMS)
            or download.calls != list(DOWNLOAD_FIELDS[: missing_index + 1])
            or candidate.accesses != 0
            or value.reason != runtime.admit012.MISSING_REASONS[missing_index]
        ):
            raise AssertionError("first-missing lookup/omission drift")

    projection_cases = (
        ((), ()),
        ((("download_result_status", "success"),), (("download_result_status", "success"),)),
        (("download_result_status", "success"),),
    )
    if runtime._project_download_result_pairs_to_exact_string_pairs(projection_cases[0][0]) != projection_cases[0][1]:
        raise AssertionError("empty projection drift")
    full = (
        ("download_result_status", "success"),
        ("observed_http_status", 200),
        ("observed_content_length_bytes", 10**100),
        ("observed_sha256", "0123456789abcdef" * 4),
    )
    projected = runtime._project_download_result_pairs_to_exact_string_pairs(full)
    if projected[1][1] != "200" or projected[2][1] != str(10**100) or any(
        type(value) is not str for _, value in projected
    ):
        raise AssertionError("typed string projection drift")
    invalid_pairs = (
        [],
        (("download_result_status", True),),
        (("observed_http_status", 200),),
        (("download_result_status", "success"), ("observed_http_status", True)),
        (("download_result_status", "success"), ("observed_http_status", type("I", (int,), {})(200))),
        (("download_result_status", type("S", (str,), {})("success")),),
        (type("P", (tuple,), {})(("download_result_status", "success")),),
        type("T", (tuple,), {})((("download_result_status", "success"),)),
    )
    for pairs in invalid_pairs:
        try:
            runtime._project_download_result_pairs_to_exact_string_pairs(pairs)
        except TypeError:
            pass
        else:
            raise AssertionError("invalid typed projection accepted")

    for rule_id, code in (
        (12, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"),
        ("ADMIT_013", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"),
        ("ADMIT_014", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"),
        ("ADMIT_015", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"),
    ):
        try:
            runtime.evaluate_admission_rule(rule_id, {})
        except runtime.UnifiedAdmissionDispatchError as error:
            if error.code != code:
                raise AssertionError("dispatcher error precedence drift")
        else:
            raise AssertionError("dispatcher error missing")
    for rule_id in KNOWN_IDS[:11]:
        def observe(module: Any) -> tuple[str, tuple[object, ...]]:
            try:
                value = module.evaluate_admission_rule(rule_id, {})
            except runtime.UnifiedAdmissionDispatchError as error:
                return "error", tuple(getattr(error, name) for name in ERROR_FIELDS)
            return "result", tuple(getattr(value, name) for name in RESULT_FIELDS)
        if observe(runtime) != observe(runtime.predecessor):
            raise AssertionError(f"old rule parity drift: {rule_id}")


def _verify_imported_successor(
    runtime: Any,
    attested: Mapping[str, Any],
    sources: Sequence[Mapping[str, Any]],
) -> None:
    if Path(os.path.abspath(runtime.__file__)) != attested["path"]:
        raise AssertionError("imported successor path mismatch")
    if runtime.__spec__ is None or Path(os.path.abspath(runtime.__spec__.origin)) != attested["path"]:
        raise AssertionError("imported successor origin mismatch")
    _assert_attested_successor_unchanged(attested)
    for alias, index in (("predecessor", 0), ("admit012", 12), ("admit012_oracle", 17)):
        module = getattr(runtime, alias)
        if Path(os.path.abspath(module.__file__)) != ROOT / sources[index]["source_relative_path"]:
            raise AssertionError(f"dependency provenance drift: {alias}")


def _silent_import(attested: Mapping[str, Any]) -> None:
    script = (
        "import importlib\n"
        f"importlib.import_module({MODULE!r})\n"
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        (sys.executable, "-B", "-c", script),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
    )
    if completed.returncode or completed.stdout or completed.stderr:
        raise AssertionError("production isolated import not silent")
    _assert_attested_successor_unchanged(attested)


def main() -> int:
    sources = _verify_sources()
    attested = _attest_successor_source_before_import()
    _verify_runtime_ast(attested)
    before = _output_bytes(OUTPUT_ROOT)
    sys.path.insert(0, str(ROOT / "src"))
    runtime = importlib.import_module(MODULE)
    _verify_imported_successor(runtime, attested, sources)
    _verify_runtime_identity(runtime)
    _verify_runtime_behavior(runtime)
    _silent_import(attested)
    if _output_bytes(OUTPUT_ROOT) != before:
        raise AssertionError("runtime import side effect")
    hashes = _validate_output_tree(source_records=sources)
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        first_root = Path(first) / "set"
        second_root = Path(second) / "set"
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1(
            first_root, repo_root=ROOT
        )
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1(
            second_root, repo_root=ROOT
        )
        first_bytes = _output_bytes(first_root)
        second_bytes = _output_bytes(second_root)
        if first_bytes != second_bytes or first_bytes != before:
            raise AssertionError("deterministic double materialization")
        inodes = {name: (first_root / name).stat().st_ino for name in OUTPUTS}
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1(
            first_root, repo_root=ROOT
        )
        if inodes != {name: (first_root / name).stat().st_ino for name in OUTPUTS}:
            raise AssertionError("existing exact set not inode-preserving no-op")
        _validate_output_tree(
            first_root, enforce_frozen_hashes=False, source_records=sources
        )
    print(
        json.dumps(
            {"checked": True, "output_sha256": hashes},
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
