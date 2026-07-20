#!/usr/bin/env python3
"""Independent checker for the ADMIT_010 provenance-contract design gate v1."""

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
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext.covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate import (  # noqa: E402
    LeakageGroupAssignmentProvenanceContractV1,
    classify_admit_010_leakage_group_assignment_provenance_design,
    run_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1,
)


EXPECTED_BASE_COMMIT = "0f687e007e532c4b2b5a9ab98ad96ae877fbd151"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_010 evaluator preconditions audit v1"
EXPECTED_STAGE = "covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1"
EXPECTED_OUTPUT_ROOT = Path("data/derived/covalent_small") / EXPECTED_STAGE
EXPECTED_RULE_ID = "ADMIT_010"
EXPECTED_RULE_NAME = "leakage_group_assignment_before_split"
EXPECTED_PHASE = "pre_final_split"
EXPECTED_FIELD = "leakage_group_id"
EXPECTED_CONTEXT = "leakage_group_assignment_provenance_contract"
EXPECTED_HISTORICAL_FIELD = "final_leakage_group_id"
EXPECTED_VERSION = "covapie_leakage_group_assignment_provenance_contract_v1"
EXPECTED_MAPPING = "exact_value_identity_after_provider_field_rename_only"
EXPECTED_POLICY = "conservative_union_of_ligand_graph_scaffold_and_protein_accession_sequence_clusters_v1"
EXPECTED_POLICY_VERSION = "v1"
EXPECTED_STAGE_KIND = "pre_final_split_leakage_group_assignment"
EXPECTED_STATUS = "leakage_group_assigned_before_final_split"
EXPECTED_BLOCKED_REASON = "leakage_group_unassigned"
EXPECTED_PREFIX = "COVAPIE_LEAKAGE_GROUP_"
EXPECTED_REGEX = r"^COVAPIE_LEAKAGE_GROUP_[0-9]{6}$"
EXPECTED_BLOCKER = "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED"
EXPECTED_COVERAGE = "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
EXPECTED_NEXT_STEP = "implement_covapie_admit_010_standalone_evaluator_interface_v1"

CONTRACT_FILE = "covapie_admit_010_leakage_group_assignment_provenance_contract.csv"
MAPPING_FILE = "covapie_admit_010_leakage_group_id_field_mapping_and_grammar_contract.csv"
TRUTH_FILE = "covapie_admit_010_provenance_validation_truth_matrix.csv"
SOURCE_FILE = "covapie_admit_010_provenance_contract_source_boundary_audit.csv"
ISSUE_FILE = "covapie_admit_010_provenance_contract_issue_readiness_inventory.csv"
MANIFEST_FILE = "covapie_admit_010_leakage_group_assignment_provenance_contract_manifest.json"
EXPECTED_FILES = (CONTRACT_FILE, MAPPING_FILE, TRUTH_FILE, SOURCE_FILE, ISSUE_FILE, MANIFEST_FILE)
EXPECTED_OUTPUT_SHA256 = {
    CONTRACT_FILE: "6daea490d7a355015f9b9f0da134d0c4e58ae48dfb7e38ed0337efdcfbe8a4a6",
    MAPPING_FILE: "9de1347f94498f1e79f95b48bc4e943fe6b311715bebeb1acd730110907fb3ba",
    TRUTH_FILE: "1a40d6e7ef0cbccf9408f9fca2524ab260f3291dd1fe4f1838d3e0a73b8a3ee7",
    SOURCE_FILE: "607660277c3f2ee4931cfc4601017ed57b8953eb738a3535f5580a21591107f6",
    ISSUE_FILE: "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd",
    MANIFEST_FILE: "33fb0d6f35b49dbf98e61e2c16fafece4b01cdfcce629ff7f1ac5afb1e7e5af2",
}

AUDIT_ROOT = "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1"
RUNTIME_ROOT = "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1"
DESIGN_ROOT = "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
IMPLEMENTATION_ROOT = "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
ASSIGNMENT_ROOT = "data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0"
EXPECTED_SOURCE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit.py",
    f"{AUDIT_ROOT}/covapie_admit_010_formal_evaluator_preconditions_manifest.json",
    f"{AUDIT_ROOT}/covapie_admit_010_formal_evaluator_precondition_matrix.csv",
    f"{AUDIT_ROOT}/covapie_admit_010_field_occurrence_inventory.csv",
    f"{AUDIT_ROOT}/covapie_admit_010_observed_value_inventory.csv",
    f"{AUDIT_ROOT}/covapie_admit_010_source_boundary_audit.csv",
    f"{AUDIT_ROOT}/covapie_admit_010_formal_evaluator_issue_readiness_inventory.csv",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009.py",
    f"{RUNTIME_ROOT}/covapie_admit_001_to_009_runtime_issue_inventory.csv",
    "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py",
    f"{DESIGN_ROOT}/covapie_bulk_download_admission_rule_registry.csv",
    f"{DESIGN_ROOT}/covapie_bulk_download_admission_schema_contract.csv",
    "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate.py",
    f"{IMPLEMENTATION_ROOT}/covapie_bulk_download_admission_rule_executability_matrix.csv",
    f"{IMPLEMENTATION_ROOT}/covapie_bulk_download_admission_field_semantics_matrix.csv",
    f"{IMPLEMENTATION_ROOT}/covapie_bulk_download_admission_evaluation_context_contract.csv",
    "src/covalent_ext/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke.py",
    f"{ASSIGNMENT_ROOT}/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_manifest.json",
    f"{ASSIGNMENT_ROOT}/covapie_final_leakage_group_assignment.csv",
    f"{ASSIGNMENT_ROOT}/covapie_final_leakage_group_inventory.csv",
    f"{ASSIGNMENT_ROOT}/unified_sample_index.csv",
)
EXPECTED_SOURCE_SHA256 = dict(zip(EXPECTED_SOURCE_PATHS, (
    "229945a3edad28ee7770172cb931e05ac463db56b0dd1abe57a8053bb4d7e5b1",
    "29df6cdf3b1eb7c1a690610d9fad88055797caba58f27f01f0b7da0d488d4c43",
    "eaa26be3e624f9c07f2e5f69313f9258b4f6dc33f470b7bf4422da1a5c998a2c",
    "e494e55bdf147985a03d936458577948099b61bd77e220b86a045f4f9337240b",
    "ac8774eea9942063d7593f8e1de5a084afa93865f14e0e796c8418022fcea3e3",
    "b28a90a36bddf7b3522637a1374bbeddaf394cb204de198b34bf9edab6182e10",
    "bb159a201f103a4cc04087978a7ca2a7bec7574fb9fc55d3cc0b059415f679e6",
    "80bdc66d2b0b2a1d761b0a1eb07f644f47535516598c3869f75a92cddafbdb39",
    "bb159a201f103a4cc04087978a7ca2a7bec7574fb9fc55d3cc0b059415f679e6",
    "79ecb3fb1084ddc161d1bec1a7db664ffbeda71952e31e4233317ecd487905d6",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "5fcc47a764a8a87e110350359e7c17056773c7ffd659b9094b6433beded2a9f8",
    "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "3e0f182e192d06be5fe4baa8cfdb2687ee23856ec5cbefbdac9c6bd2b6206212",
    "0609a4e7773c948c232e69fb4dafe5ace59d7bebea3f183f1d0d1629b93741cf",
    "768c964f22e19a8fb6232b1fa26c531e53d023042abcd9b1bcca44df2b4f4416",
    "ae18fd8d0ed8bad803126fb65bc947446d99ca0e4c6f42c63927d969f4bacfbc",
    "d610e7171ad976f16055584582335ce756ed0210e6c15d6b55a1a234bc92c326",
), strict=True))

EXACT19_FIELDS = (
    "contract_version", "canonical_candidate_field_name", "historical_artifact_field_name",
    "field_mapping_rule", "assignment_policy", "assignment_policy_version",
    "assignment_stage_kind", "assignment_manifest_sha256", "assignment_artifact_sha256",
    "group_inventory_sha256", "sample_index_sha256", "assignment_id",
    "historical_leakage_group_id", "sample_index_row_id", "member_sample_index_row_ids",
    "member_count", "assignment_passed", "split_assignments_written", "pre_split_assignment_status",
)
CONTRACT_HEADER = (
    "contract_order", "contract_area", "contract_item", "exact_requirement",
    "validation_precedence", "failure_outcome", "failure_reason", "forbidden_behavior",
    "contract_passed",
)
MAPPING_HEADER = (
    "mapping_order", "contract_area", "contract_item", "exact_requirement",
    "historical_evidence_boundary", "forbidden_behavior", "mapping_passed",
)
TRUTH_HEADER = (
    "truth_order", "truth_group", "case_id", "input_summary", "outcome", "passed",
    "blocks_candidate", "reason", "canonical_leakage_group_id",
    "validated_candidate_fields", "consumed_candidate_fields", "consumed_context_items",
    "evaluator_io_used", "expected_precedence", "truth_passed",
)
SOURCE_HEADER = (
    "source_order", "source_relative_path", "expected_sha256", "base_tree_sha256",
    "filesystem_sha256", "tracked", "base_tree_blob", "filesystem_regular",
    "non_symlink", "safe_descendant", "source_boundary_passed",
)
ISSUE_HEADER = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

TRUE_READINESS = (
    "admit_010_precondition_audit_complete",
    "leakage_group_assignment_provenance_contract_frozen",
    "leakage_group_id_final_grammar_frozen",
    "leakage_group_id_historical_field_mapping_rule_frozen",
    "leakage_group_assignment_policy_and_version_frozen",
    "leakage_group_assignment_source_attestation_contract_frozen",
    "leakage_group_assignment_membership_contract_frozen",
    "leakage_group_assignment_pre_split_evidence_contract_frozen",
    "admit_010_design_oracle_implemented", "leakage_group_assignment_provenance_blocker_resolved",
    "admit_010_provider_mapping_boundary_preserved",
    "ready_for_admit_010_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "leakage_group_id_provider_mapping_validated", "real_provider_leakage_group_id_count_nonzero",
    "evaluate_admit_010_implemented", "Admit010EvaluationResult_implemented",
    "admit_010_unified_adapter_contract_frozen", "admit_010_unified_adapter_implemented",
    "admit_010_registered_in_engine", "unified_dispatch_runtime_with_admit_001_to_010_implemented",
    "admit_011_started", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen", "real_candidate_evaluation", "ready_for_bulk_download_now",
    "ready_for_training", "ready_to_train_now",
)
EXPECTED_GROUP_COUNTS = {
    "candidate_scalar": 14, "context_type": 4, "static_fields": 7, "sha256": 6,
    "assignment_id": 5, "historical_group": 3, "sample_id": 5, "membership": 12,
    "member_count": 6, "assignment_semantics": 9,
}
EXPECTED_REASONS = (
    "LEAKAGE_GROUP_ID_TYPE_INVALID", EXPECTED_BLOCKED_REASON,
    "LEAKAGE_GROUP_ID_NON_ASCII", "LEAKAGE_GROUP_ID_SYNTAX_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_TYPE_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_VERSION_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_POLICY_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_POLICY_VERSION_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_STAGE_KIND_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_ID_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_HISTORICAL_GROUP_ID_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_SAMPLE_ID_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_MEMBER_COUNT_INVALID",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(arguments: Sequence[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT, text=text,
        capture_output=True, check=False,
    )


def _csv(path: Path, header: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != header or len(header) != len(set(header)):
            raise ValueError(f"header mismatch: {path.name}")
        rows = [dict(row) for row in reader]
    if any(tuple(row) != header or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"row shape mismatch: {path.name}")
    return rows


def _csv_bytes(content: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8"), newline=""))
    return [dict(row) for row in reader]


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path) and not path.is_absolute() and bool(path.parts)
        and ".." not in path.parts and path.parts[0] != "checkpoints"
        and path.parts[:2] != ("data", "raw")
    )


def _resolved_safe_descendant(path: Path, repo_root: Path) -> bool:
    if not _safe_relative_path(path):
        return False
    try:
        repo_resolved = repo_root.resolve(strict=True)
        source_resolved = (repo_root / path).resolve(strict=True)
        source_resolved.relative_to(repo_resolved)
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _verified_sources() -> dict[str, bytes]:
    if (
        len(EXPECTED_SOURCE_PATHS) != 21 or len(set(EXPECTED_SOURCE_PATHS)) != 21
        or tuple(EXPECTED_SOURCE_SHA256) != EXPECTED_SOURCE_PATHS
    ):
        raise ValueError("Exact21 source boundary invalid")
    subject = _git(["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"])
    if subject.returncode or ancestor.returncode or subject.stdout.strip() != EXPECTED_BASE_SUBJECT:
        raise ValueError("base lineage mismatch")
    for value in EXPECTED_SOURCE_PATHS:
        path = Path(value)
        if not _safe_relative_path(path):
            raise ValueError("unsafe source path")
        metadata = os.lstat(REPO_ROOT / path)
        tracked = _git(["ls-files", "--error-unmatch", "--", value])
        tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", value])
        head = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
        if (
            tracked.returncode or tree.returncode or len(head) != 3
            or head[0] not in ("100644", "100755") or head[1] != "blob"
            or not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode)
            or not _resolved_safe_descendant(path, REPO_ROOT)
        ):
            raise ValueError("source structure mismatch")
    sources: dict[str, bytes] = {}
    for value in EXPECTED_SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{value}"], text=False)
        filesystem = (REPO_ROOT / value).read_bytes()
        if base.returncode or type(base.stdout) is not bytes:
            raise ValueError("base source read failed")
        if hashlib.sha256(base.stdout).hexdigest() != EXPECTED_SOURCE_SHA256[value]:
            raise ValueError("base source SHA mismatch")
        if hashlib.sha256(filesystem).hexdigest() != EXPECTED_SOURCE_SHA256[value]:
            raise ValueError("filesystem source SHA mismatch")
        sources[value] = filesystem
    return sources


def _one(rows: Sequence[Mapping[str, str]], key: str, value: str) -> Mapping[str, str]:
    matches = [row for row in rows if row.get(key) == value]
    if len(matches) != 1:
        raise ValueError(f"expected one {key}={value}")
    return matches[0]


def _validate_issue_transition(rows: list[dict[str, str]], sources: Mapping[str, bytes]) -> None:
    predecessor = _csv_bytes(sources[EXPECTED_SOURCE_PATHS[6]])
    if len(predecessor) != 11 or len(rows) != 11:
        raise ValueError("issue row count mismatch")
    for before, after in zip(predecessor, rows, strict=True):
        expected = dict(before)
        if before["issue_id"] == EXPECTED_BLOCKER:
            expected["status"] = "resolved"
            expected["integration_transition"] = "leakage_group_assignment_provenance_contract_frozen_v1"
        if after != expected:
            raise ValueError("issue transition mismatch")
    coverage = _one(rows, "issue_id", EXPECTED_COVERAGE)
    if coverage["affected_rules"] != "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015":
        raise ValueError("coverage changed")


def _validate_contract(rows: list[dict[str, str]]) -> None:
    expected_items = (
        "rule_identity", "Exact19_type", "Exact19_field_order", "contract_version",
        "canonical_candidate_field_name", "historical_artifact_field_name", "field_mapping_rule",
        "assignment_policy", "assignment_policy_version", "assignment_stage_kind",
        "assignment_manifest_sha256", "assignment_artifact_sha256", "group_inventory_sha256",
        "sample_index_sha256", "assignment_id", "historical_leakage_group_id",
        "sample_index_row_id", "member_sample_index_row_ids", "member_count",
        "assignment_passed", "split_assignments_written", "pre_split_assignment_status",
        "candidate_historical_equality", "sample_membership", "passed", "nonpassed", "purity",
        "source_SHA256", "formal_evaluator", "provider_mapping", "runtime", "training",
    )
    if len(rows) != 32 or tuple(row["contract_item"] for row in rows) != expected_items:
        raise ValueError("contract row identity mismatch")
    if [row["contract_order"] for row in rows] != [str(i) for i in range(1, 33)]:
        raise ValueError("contract order mismatch")
    if any(row["contract_passed"] != "true" for row in rows):
        raise ValueError("contract attestation mismatch")
    exact = {row["contract_item"]: row["exact_requirement"] for row in rows}
    required = {
        "rule_identity": "ADMIT_010/leakage_group_assignment_before_split/pre_final_split",
        "Exact19_field_order": "|".join(EXACT19_FIELDS),
        "contract_version": EXPECTED_VERSION,
        "canonical_candidate_field_name": EXPECTED_FIELD,
        "historical_artifact_field_name": EXPECTED_HISTORICAL_FIELD,
        "field_mapping_rule": EXPECTED_MAPPING, "assignment_policy": EXPECTED_POLICY,
        "assignment_policy_version": EXPECTED_POLICY_VERSION,
        "assignment_stage_kind": EXPECTED_STAGE_KIND,
        "historical_leakage_group_id": EXPECTED_REGEX,
        "pre_split_assignment_status": EXPECTED_STATUS,
        "candidate_historical_equality": "candidate leakage_group_id == provenance historical_leakage_group_id",
        "purity": "pure in-memory; evaluator_io_used=false",
        "provider_mapping": "contract frozen but real mapping unvalidated",
        "runtime": "Exact9 unchanged; ADMIT_010 unregistered",
    }
    if any(exact[key] != value for key, value in required.items()):
        raise ValueError("contract semantic mismatch")


def _validate_mapping(rows: list[dict[str, str]]) -> None:
    expected_items = (
        "exact_type", "empty", "ASCII", "regex", "prefix", "suffix", "normalization",
        "canonical_field", "historical_field", "mapping_rule", "value_identity", "assignment_id",
        "group_order", "split_assignment", "single_axis_group", "duplicate_identity_key",
        "policy_value", "policy_version", "policy_version_consistency", "SHA_truth_boundary",
        "assignment_record", "tuple", "assignment_evidence", "historical_final_group_status",
        "split_ids_and_assigned_split", "real_mapping",
    )
    if len(rows) != 26 or tuple(row["contract_item"] for row in rows) != expected_items:
        raise ValueError("mapping row identity mismatch")
    if any(row["mapping_passed"] != "true" for row in rows):
        raise ValueError("mapping attestation mismatch")
    exact = {row["contract_item"]: row["exact_requirement"] for row in rows}
    required = {
        "regex": EXPECTED_REGEX, "prefix": EXPECTED_PREFIX,
        "canonical_field": EXPECTED_FIELD, "historical_field": EXPECTED_HISTORICAL_FIELD,
        "mapping_rule": EXPECTED_MAPPING,
        "value_identity": "candidate leakage_group_id == provenance historical_leakage_group_id",
        "policy_value": EXPECTED_POLICY, "policy_version": EXPECTED_POLICY_VERSION,
        "real_mapping": "not validated in this design step",
    }
    if any(exact[key] != value for key, value in required.items()):
        raise ValueError("mapping semantic mismatch")


def _truth_expectation(case_id: str) -> tuple[str, str]:
    type_invalid = {"candidate_none", "candidate_integer", "candidate_str_subclass"}
    non_ascii = {"candidate_non_ascii", "candidate_unicode_digit"}
    syntax_invalid = {
        "candidate_lowercase_prefix", "candidate_case_drift", "candidate_short_digits",
        "candidate_long_digits", "candidate_non_digit_suffix", "candidate_leading_whitespace",
        "candidate_trailing_whitespace",
    }
    context_invalid = {"context_none", "context_dict", "context_dataclass_subclass"}
    static_reasons = {
        "contract_version_wrong": "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_VERSION_INVALID",
        "candidate_field_wrong": "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID",
        "historical_field_wrong": "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID",
        "mapping_rule_wrong": "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID",
        "policy_wrong": "LEAKAGE_GROUP_ASSIGNMENT_POLICY_INVALID",
        "policy_version_wrong": "LEAKAGE_GROUP_ASSIGNMENT_POLICY_VERSION_INVALID",
        "stage_kind_wrong": "LEAKAGE_GROUP_ASSIGNMENT_STAGE_KIND_INVALID",
    }
    invalid_groups = {
        "sha_none": "LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID",
        "sha_str_subclass": "LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID",
        "sha_uppercase": "LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID",
        "sha_short": "LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID",
        "sha_non_hex": "LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID",
        "assignment_id_wrong_type": "LEAKAGE_GROUP_ASSIGNMENT_ID_INVALID",
        "assignment_id_empty": "LEAKAGE_GROUP_ASSIGNMENT_ID_INVALID",
        "assignment_id_non_ascii": "LEAKAGE_GROUP_ASSIGNMENT_ID_INVALID",
        "assignment_id_whitespace": "LEAKAGE_GROUP_ASSIGNMENT_ID_INVALID",
        "historical_group_wrong_type": "LEAKAGE_GROUP_ASSIGNMENT_HISTORICAL_GROUP_ID_INVALID",
        "historical_group_malformed": "LEAKAGE_GROUP_ASSIGNMENT_HISTORICAL_GROUP_ID_INVALID",
        "sample_id_wrong_type": "LEAKAGE_GROUP_ASSIGNMENT_SAMPLE_ID_INVALID",
        "sample_id_empty": "LEAKAGE_GROUP_ASSIGNMENT_SAMPLE_ID_INVALID",
        "sample_id_non_ascii": "LEAKAGE_GROUP_ASSIGNMENT_SAMPLE_ID_INVALID",
        "sample_id_whitespace": "LEAKAGE_GROUP_ASSIGNMENT_SAMPLE_ID_INVALID",
        "membership_list": "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID",
        "membership_tuple_subclass": "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID",
        "membership_empty_tuple": "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID",
        "membership_non_str_member": "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID",
        "membership_str_subclass_member": "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID",
        "membership_empty_member": "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID",
        "membership_non_ascii_member": "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID",
        "membership_unsorted": "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID",
        "membership_duplicate": "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID",
        "member_count_bool": "LEAKAGE_GROUP_ASSIGNMENT_MEMBER_COUNT_INVALID",
        "member_count_float": "LEAKAGE_GROUP_ASSIGNMENT_MEMBER_COUNT_INVALID",
        "member_count_zero": "LEAKAGE_GROUP_ASSIGNMENT_MEMBER_COUNT_INVALID",
        "member_count_negative": "LEAKAGE_GROUP_ASSIGNMENT_MEMBER_COUNT_INVALID",
        "member_count_mismatch": "LEAKAGE_GROUP_ASSIGNMENT_MEMBER_COUNT_INVALID",
    }
    blocked = {
        "candidate_empty", "membership_sample_absent", "assignment_passed_false",
        "assignment_passed_int_one", "split_assignments_written_true",
        "split_assignments_written_int_zero", "pre_split_status_wrong",
        "candidate_historical_mismatch",
    }
    if case_id in type_invalid:
        return "invalid", "LEAKAGE_GROUP_ID_TYPE_INVALID"
    if case_id == "candidate_empty":
        return "blocked", EXPECTED_BLOCKED_REASON
    if case_id in non_ascii:
        return "invalid", "LEAKAGE_GROUP_ID_NON_ASCII"
    if case_id in syntax_invalid:
        return "invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID"
    if case_id in context_invalid:
        return "invalid", "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_TYPE_INVALID"
    if case_id in static_reasons:
        return "invalid", static_reasons[case_id]
    if case_id in invalid_groups:
        return "invalid", invalid_groups[case_id]
    if case_id in blocked:
        return "blocked", EXPECTED_BLOCKED_REASON
    return "passed", ""


def _validate_truth(rows: list[dict[str, str]]) -> None:
    if len(rows) != 71 or [row["truth_order"] for row in rows] != [str(i) for i in range(1, 72)]:
        raise ValueError("truth row count/order mismatch")
    counts = {group: sum(row["truth_group"] == group for row in rows) for group in EXPECTED_GROUP_COUNTS}
    if counts != EXPECTED_GROUP_COUNTS or len({row["case_id"] for row in rows}) != 71:
        raise ValueError("truth group or case identity mismatch")
    scalar_failure_ids = {
        "candidate_none", "candidate_integer", "candidate_empty", "candidate_str_subclass",
        "candidate_non_ascii", "candidate_lowercase_prefix", "candidate_case_drift",
        "candidate_short_digits", "candidate_long_digits", "candidate_non_digit_suffix",
        "candidate_leading_whitespace", "candidate_trailing_whitespace", "candidate_unicode_digit",
    }
    for row in rows:
        outcome, reason = _truth_expectation(row["case_id"])
        if row["outcome"] != outcome or row["reason"] != reason:
            raise ValueError(f"truth classification mismatch: {row['case_id']}")
        if (row["passed"] == "true") != (outcome == "passed"):
            raise ValueError("passed invariant mismatch")
        if (row["blocks_candidate"] == "true") != (outcome != "passed"):
            raise ValueError("blocks invariant mismatch")
        if row["evaluator_io_used"] != "false" or row["truth_passed"] != "true":
            raise ValueError("truth safety mismatch")
        if row["consumed_candidate_fields"] != '["leakage_group_id"]':
            raise ValueError("candidate consumption mismatch")
        scalar_failed = row["case_id"] in scalar_failure_ids
        if scalar_failed:
            if (
                row["canonical_leakage_group_id"] != ""
                or row["validated_candidate_fields"] != "[]"
                or row["consumed_context_items"] != "[]"
            ):
                raise ValueError("scalar short-circuit state mismatch")
        else:
            if (
                row["canonical_leakage_group_id"] != "COVAPIE_LEAKAGE_GROUP_000001"
                or row["validated_candidate_fields"] != '[["leakage_group_id","COVAPIE_LEAKAGE_GROUP_000001"]]'
                or row["consumed_context_items"] != '["leakage_group_assignment_provenance_contract"]'
            ):
                raise ValueError("validated scalar retained-state mismatch")


def _validate_source_rows(rows: list[dict[str, str]]) -> None:
    if len(rows) != 21:
        raise ValueError("source row count mismatch")
    for index, (row, path) in enumerate(zip(rows, EXPECTED_SOURCE_PATHS, strict=True), 1):
        digest = EXPECTED_SOURCE_SHA256[path]
        expected = {
            "source_order": str(index), "source_relative_path": path,
            "expected_sha256": digest, "base_tree_sha256": digest,
            "filesystem_sha256": digest, "tracked": "true", "base_tree_blob": "true",
            "filesystem_regular": "true", "non_symlink": "true", "safe_descendant": "true",
            "source_boundary_passed": "true",
        }
        if row != expected:
            raise ValueError("source boundary output mismatch")


def _expected_manifest() -> dict[str, object]:
    readiness = {
        **{key: True for key in TRUE_READINESS},
        **{key: False for key in FALSE_READINESS},
    }
    expected: dict[str, object] = {
        "project": "CovaPIE",
        "step": "ADMIT_010 leakage group assignment provenance contract design gate v1",
        "stage": EXPECTED_STAGE,
        "manifest_schema_version": "covapie_admit_010_leakage_group_assignment_provenance_contract_manifest_v1",
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": EXPECTED_RULE_ID,
        "admission_rule_name": EXPECTED_RULE_NAME,
        "evaluation_phase": EXPECTED_PHASE,
        "candidate_field": EXPECTED_FIELD,
        "context_item": EXPECTED_CONTEXT,
        "historical_artifact_field": EXPECTED_HISTORICAL_FIELD,
        "provenance_contract_version": EXPECTED_VERSION,
        "field_mapping_rule": EXPECTED_MAPPING,
        "assignment_policy": EXPECTED_POLICY,
        "assignment_policy_version": EXPECTED_POLICY_VERSION,
        "assignment_stage_kind": EXPECTED_STAGE_KIND,
        "pre_split_assigned_status": EXPECTED_STATUS,
        "historical_blocking_reason": EXPECTED_BLOCKED_REASON,
        "leakage_group_id_grammar": {
            "exact_type": "builtins.str", "subclasses_allowed": False,
            "ASCII_only": True, "prefix": EXPECTED_PREFIX, "regex": EXPECTED_REGEX,
            "suffix_digits": 6, "suffix_digit_class": "ASCII_[0-9]",
            "normalization_allowed": False, "historical_observed_value_count": 5,
            "grammar_is_explicit_v1_design_not_natural_inference": True,
        },
        "exact19_class_name": "LeakageGroupAssignmentProvenanceContractV1",
        "exact19_field_count": 19,
        "exact19_field_order": list(EXACT19_FIELDS),
        "exact19_slots_used": False,
        "class_is_formal_result": False,
        "source_sha256_contract": {
            "field_count": 4, "exact_type": "builtins.str",
            "lowercase_hex_length": 64, "str_subclasses_allowed": False,
            "caller_attestation_only": True, "evaluator_verifies_files": False,
        },
        "opaque_identifier_contract": {
            "fields": ["assignment_id", "sample_index_row_id"],
            "exact_type": "builtins.str", "ASCII_only": True,
            "minimum_length": 1, "maximum_length": 256,
            "surrounding_whitespace_allowed": False,
            "assignment_id_is_group_id": False,
        },
        "membership_contract": {
            "exact_type": "builtins.tuple", "tuple_subclasses_allowed": False,
            "minimum_members": 1, "member_exact_type": "builtins.str",
            "strict_ASCII_ascending": True, "unique": True,
            "automatic_sort_or_deduplicate": False,
            "sample_index_row_id_must_be_present": True,
            "member_count_exact_builtin_int": True, "bool_allowed": False,
            "member_count_equals_tuple_length": True,
        },
        "pre_split_evidence_contract": {
            "assignment_passed": True, "split_assignments_written": False,
            "pre_split_assignment_status": EXPECTED_STATUS,
            "split_artifact_reverse_proof_allowed": False,
        },
        "validation_precedence": [
            "leakage_group_id_exact_builtin_str", "empty_assignment_state", "ASCII",
            "canonical_grammar", "provenance_exact_committed_design_type",
            "contract_version", "candidate_and_historical_field_names",
            "field_mapping_rule", "assignment_policy", "assignment_policy_version",
            "assignment_stage_kind", "four_source_SHA256_fields", "assignment_id",
            "historical_leakage_group_id_grammar", "sample_index_row_id",
            "member_sample_index_row_ids", "member_count",
            "assignment_evidence_consistency", "candidate_historical_id_exact_equality",
            "sample_membership", "passed",
        ],
        "reason_vocabulary": list(EXPECTED_REASONS),
        "outcome_vocabulary": ["passed", "blocked", "invalid"],
        "blocks_candidate_invariant": "true_iff_outcome_not_passed",
        "design_oracle_name": "classify_admit_010_leakage_group_assignment_provenance_design",
        "design_oracle_is_formal_evaluator": False,
        "design_oracle_evaluator_io_used": False,
        "future_evaluator_name_reserved_only": "evaluate_admit_010",
        "future_result_name_reserved_only": "Admit010EvaluationResult",
        "historical_evidence_boundary": {
            "historical_group_count": 5, "historical_sample_count": 11,
            "historical_ids_are_general_grammar": False,
            "historical_assignment_and_sample_ids_are_opaque": True,
            "historical_final_group_status_in_exact19": False,
            "split_assignment_ids_in_exact19": False,
            "assigned_split_in_exact19": False,
        },
        "real_provider_mapping_validated": False,
        "real_provider_leakage_group_id_count": 0,
        "contract_row_count": 32,
        "mapping_grammar_row_count": 26,
        "truth_matrix_contract": "Exact71",
        "truth_row_count": 71,
        "truth_group_counts": dict(EXPECTED_GROUP_COUNTS),
        "source_boundary_name": "fixed_ordered_exact21_committed_source_boundary",
        "source_input_count": 21,
        "source_input_paths": list(EXPECTED_SOURCE_PATHS),
        "source_input_sha256": dict(EXPECTED_SOURCE_SHA256),
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "source_attestation_authenticity_checked_by_evaluator": False,
        "issue_inventory_row_count": 11,
        "issue_transition": {
            "issue_id": EXPECTED_BLOCKER, "from_status": "open", "to_status": "resolved",
            "from_integration_transition": "unchanged_open",
            "to_integration_transition": "leakage_group_assignment_provenance_contract_frozen_v1",
            "only_authorized_issue_change": True,
        },
        "coverage_issue_status": "open",
        "coverage_issue_affected_rules": "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        "readiness": readiness,
        **readiness,
        "output_file_count": 6,
        "output_files": list(EXPECTED_FILES),
        "output_sha256": {
            name: EXPECTED_OUTPUT_SHA256[name] for name in EXPECTED_FILES[:-1]
        },
        "output_sha256_excludes_manifest_self_hash": True,
        "output_materialization": {
            "preflight_before_first_write": True,
            "real_directory_non_symlink": True,
            "existing_inventory_allowlist_exact": True,
            "existing_entries_regular_non_symlink": True,
            "atomic_same_directory_mkstemp": True,
            "temporary_suffix": ".tmp", "fdopen_mode": "wb",
            "flush_and_fsync": True, "os_replace": True,
            "finally_cleanup": True, "postwrite_exact_inventory_reverified": True,
        },
        "stop_boundaries": [
            "no_formal_evaluator_or_result", "no_adapter_or_registration",
            "no_exact10_runtime", "no_provider_mapping_validation",
            "no_group_reassignment_or_split", "no_admit_011",
            "no_evaluate_all_rules_or_combined_verdict",
            "no_real_candidate_evaluation", "no_raw_network_download",
            "no_model_or_training",
        ],
        "recommended_next_step": EXPECTED_NEXT_STEP,
        "all_contract_checks_passed": True,
        "all_mapping_checks_passed": True,
        "all_truth_checks_passed": True,
        "all_source_boundary_checks_passed": True,
        "all_issue_checks_passed": True,
        "all_readiness_checks_passed": True,
        "all_attestations_passed": True,
        "validation_failures": [],
    }
    if len(expected) != 104:
        raise ValueError("independent expected manifest is not Exact104")
    return expected


def _validate_manifest(manifest: Mapping[str, Any], output_root: Path) -> None:
    del output_root
    expected = _expected_manifest()
    if type(manifest) is not dict or len(manifest) != 104 or manifest != expected:
        raise ValueError("manifest does not equal independent Exact104 expected value")


def _valid_context(**changes: object) -> LeakageGroupAssignmentProvenanceContractV1:
    value = LeakageGroupAssignmentProvenanceContractV1(
        EXPECTED_VERSION, EXPECTED_FIELD, EXPECTED_HISTORICAL_FIELD, EXPECTED_MAPPING,
        EXPECTED_POLICY, EXPECTED_POLICY_VERSION, EXPECTED_STAGE_KIND, "1" * 64,
        "2" * 64, "3" * 64, "4" * 64, "ASSIGNMENT_OPAQUE",
        "COVAPIE_LEAKAGE_GROUP_000001", "SAMPLE_ALPHA", ("SAMPLE_ALPHA",),
        1, True, False, EXPECTED_STATUS,
    )
    return replace(value, **changes)


def _expected_classifier(
    candidate: object, value: object,
) -> tuple[str, str, str, tuple[tuple[str, str], ...], tuple[str, ...]]:
    if type(candidate) is not str:
        return "invalid", "LEAKAGE_GROUP_ID_TYPE_INVALID", "", (), ()
    if candidate == "":
        return "blocked", EXPECTED_BLOCKED_REASON, "", (), ()
    if not candidate.isascii():
        return "invalid", "LEAKAGE_GROUP_ID_NON_ASCII", "", (), ()
    if re.fullmatch(EXPECTED_REGEX, candidate) is None:
        return "invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID", "", (), ()
    validated = ((EXPECTED_FIELD, candidate),)
    if type(value) is not LeakageGroupAssignmentProvenanceContractV1:
        return "invalid", "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_TYPE_INVALID", candidate, validated, (EXPECTED_CONTEXT,)
    checks = (
        (type(value.contract_version) is str and value.contract_version == EXPECTED_VERSION, "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_VERSION_INVALID"),
        (type(value.canonical_candidate_field_name) is str and value.canonical_candidate_field_name == EXPECTED_FIELD and type(value.historical_artifact_field_name) is str and value.historical_artifact_field_name == EXPECTED_HISTORICAL_FIELD, "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID"),
        (type(value.field_mapping_rule) is str and value.field_mapping_rule == EXPECTED_MAPPING, "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID"),
        (type(value.assignment_policy) is str and value.assignment_policy == EXPECTED_POLICY, "LEAKAGE_GROUP_ASSIGNMENT_POLICY_INVALID"),
        (type(value.assignment_policy_version) is str and value.assignment_policy_version == EXPECTED_POLICY_VERSION, "LEAKAGE_GROUP_ASSIGNMENT_POLICY_VERSION_INVALID"),
        (type(value.assignment_stage_kind) is str and value.assignment_stage_kind == EXPECTED_STAGE_KIND, "LEAKAGE_GROUP_ASSIGNMENT_STAGE_KIND_INVALID"),
        (all(type(item) is str and re.fullmatch(r"[0-9a-f]{64}", item) is not None for item in (value.assignment_manifest_sha256, value.assignment_artifact_sha256, value.group_inventory_sha256, value.sample_index_sha256)), "LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID"),
        (type(value.assignment_id) is str and 1 <= len(value.assignment_id) <= 256 and value.assignment_id.isascii() and value.assignment_id == value.assignment_id.strip(), "LEAKAGE_GROUP_ASSIGNMENT_ID_INVALID"),
        (type(value.historical_leakage_group_id) is str and value.historical_leakage_group_id.isascii() and re.fullmatch(EXPECTED_REGEX, value.historical_leakage_group_id) is not None, "LEAKAGE_GROUP_ASSIGNMENT_HISTORICAL_GROUP_ID_INVALID"),
        (type(value.sample_index_row_id) is str and 1 <= len(value.sample_index_row_id) <= 256 and value.sample_index_row_id.isascii() and value.sample_index_row_id == value.sample_index_row_id.strip(), "LEAKAGE_GROUP_ASSIGNMENT_SAMPLE_ID_INVALID"),
    )
    for passed, reason in checks:
        if not passed:
            return "invalid", reason, candidate, validated, (EXPECTED_CONTEXT,)
    members = value.member_sample_index_row_ids
    opaque = lambda item: type(item) is str and 1 <= len(item) <= 256 and item.isascii() and item == item.strip()
    if type(members) is not tuple or not members or any(not opaque(item) for item in members) or any(a >= b for a, b in zip(members, members[1:])):
        return "invalid", "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID", candidate, validated, (EXPECTED_CONTEXT,)
    if type(value.member_count) is not int or value.member_count <= 0 or value.member_count != len(members):
        return "invalid", "LEAKAGE_GROUP_ASSIGNMENT_MEMBER_COUNT_INVALID", candidate, validated, (EXPECTED_CONTEXT,)
    evidence = (
        type(value.assignment_passed) is bool and value.assignment_passed is True
        and type(value.split_assignments_written) is bool and value.split_assignments_written is False
        and type(value.pre_split_assignment_status) is str
        and value.pre_split_assignment_status == EXPECTED_STATUS
        and candidate == value.historical_leakage_group_id
        and value.sample_index_row_id in members
    )
    return (
        ("passed", "", candidate, validated, (EXPECTED_CONTEXT,)) if evidence
        else ("blocked", EXPECTED_BLOCKED_REASON, candidate, validated, (EXPECTED_CONTEXT,))
    )


def _validate_oracle() -> None:
    class StringSubclass(str):
        pass

    class ExplosiveVersion:
        comparisons = 0

        def __eq__(self, other: object) -> bool:
            type(self).comparisons += 1
            raise AssertionError("comparison must not run")

        def __ne__(self, other: object) -> bool:
            type(self).comparisons += 1
            raise AssertionError("comparison must not run")

    class ExplosiveString(str):
        comparisons = 0

        def __eq__(self, other: object) -> bool:
            type(self).comparisons += 1
            raise AssertionError("comparison must not run")

        def __ne__(self, other: object) -> bool:
            type(self).comparisons += 1
            raise AssertionError("comparison must not run")

    @dataclass(frozen=True)
    class ContractSubclass(LeakageGroupAssignmentProvenanceContractV1):
        pass

    candidate = "COVAPIE_LEAKAGE_GROUP_000001"
    valid = _valid_context()
    subclass = ContractSubclass(*(getattr(valid, name) for name in EXACT19_FIELDS))
    cases = (
        (None, valid), (7, valid), ("", valid), (StringSubclass(candidate), valid),
        ("COVAPIE_LEAKAGE_GROUP_00000é", valid), ("covapie_leakage_group_000001", valid),
        (candidate, None), (candidate, {}), (candidate, subclass),
        (candidate, _valid_context(contract_version=ExplosiveVersion())),
        (candidate, _valid_context(contract_version=ExplosiveString(EXPECTED_VERSION))),
        (candidate, _valid_context(contract_version="wrong")),
        (candidate, _valid_context(assignment_manifest_sha256="A" * 64)),
        (candidate, _valid_context(assignment_id=candidate)),
        (candidate, _valid_context(historical_leakage_group_id="ASSIGNMENT_OPAQUE")),
        (candidate, _valid_context(member_sample_index_row_ids=["SAMPLE_ALPHA"])),
        (candidate, _valid_context(member_count=True)),
        (candidate, _valid_context(assignment_passed=1)),
        (candidate, _valid_context(split_assignments_written=0)),
        (candidate, _valid_context(split_assignments_written=True)),
        (candidate, _valid_context(historical_leakage_group_id="COVAPIE_LEAKAGE_GROUP_000002")),
        (candidate, _valid_context(sample_index_row_id="SAMPLE_BETA")),
        (candidate, valid),
    )
    for scalar, context in cases:
        expected = _expected_classifier(scalar, context)
        observed = classify_admit_010_leakage_group_assignment_provenance_design(scalar, context)
        if tuple(observed) != (
            "outcome", "passed", "blocks_candidate", "reason", "canonical_leakage_group_id",
            "validated_candidate_fields", "consumed_candidate_fields", "consumed_context_items",
            "evaluator_io_used",
        ):
            raise ValueError("oracle return key/order mismatch")
        outcome, reason, canonical, validated, consumed_context = expected
        required = {
            "outcome": outcome, "passed": outcome == "passed",
            "blocks_candidate": outcome != "passed", "reason": reason,
            "canonical_leakage_group_id": canonical,
            "validated_candidate_fields": validated,
            "consumed_candidate_fields": (EXPECTED_FIELD,),
            "consumed_context_items": consumed_context, "evaluator_io_used": False,
        }
        if dict(observed) != required:
            raise ValueError("oracle behavior mismatch")
    if ExplosiveVersion.comparisons != 0 or ExplosiveString.comparisons != 0:
        raise ValueError("contract_version comparison ran before exact-type gate")
    fake_attestation = _valid_context(
        assignment_manifest_sha256="a" * 64, assignment_artifact_sha256="b" * 64,
        group_inventory_sha256="c" * 64, sample_index_sha256="d" * 64,
    )
    if classify_admit_010_leakage_group_assignment_provenance_design(candidate, fake_attestation)["outcome"] != "passed":
        raise ValueError("oracle incorrectly treats SHA as filesystem authenticity check")


def _validate_no_premature_api() -> None:
    path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    if "evaluate_admit_010" in functions or "Admit010EvaluationResult" in classes:
        raise ValueError("formal evaluator/result implemented prematurely")
    if any("adapter" in name or "exact10" in name or "admit_011" in name for name in functions):
        raise ValueError("later implementation present prematurely")


def _validate_materializer() -> None:
    with tempfile.TemporaryDirectory(prefix="covapie_admit010_checker_") as directory:
        parent = Path(directory)
        root = parent / "outputs"
        first = run_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(root)
        first_bytes = {name: (root / name).read_bytes() for name in EXPECTED_FILES}
        second = run_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(root)
        second_bytes = {name: (root / name).read_bytes() for name in EXPECTED_FILES}
        if first_bytes != second_bytes or first["output_sha256"] != second["output_sha256"]:
            raise ValueError("materialization is not deterministic")
        for entry in root.iterdir():
            metadata = os.lstat(entry)
            if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                raise ValueError("materialized output unsafe")
        unsafe = parent / "unsafe_extra"
        unsafe.mkdir()
        (unsafe / "unexpected.txt").write_text("sentinel", encoding="utf-8")
        try:
            run_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(unsafe)
        except ValueError:
            pass
        else:
            raise ValueError("unexpected output entry accepted")
        if {item.name for item in unsafe.iterdir()} != {"unexpected.txt"}:
            raise ValueError("unsafe preflight caused partial write")
        target = parent / "target"
        target.mkdir()
        symlink_root = parent / "symlink_root"
        symlink_root.symlink_to(target, target_is_directory=True)
        try:
            run_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(symlink_root)
        except ValueError:
            pass
        else:
            raise ValueError("symlink output root accepted")
        unsafe_entry = parent / "unsafe_entry"
        unsafe_entry.mkdir()
        (unsafe_entry / CONTRACT_FILE).symlink_to(target)
        try:
            run_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(unsafe_entry)
        except ValueError:
            pass
        else:
            raise ValueError("symlink output entry accepted")


def check_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(
    *, output_root: Path = EXPECTED_OUTPUT_ROOT, enforce_frozen_hashes: bool = True,
    exercise_materializer: bool = True,
) -> dict[str, Any]:
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    metadata = os.lstat(root)
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ValueError("output root unsafe")
    entries = tuple(root.iterdir())
    if {entry.name for entry in entries} != set(EXPECTED_FILES):
        raise ValueError("output inventory mismatch")
    for entry in entries:
        item = os.lstat(entry)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("output entry unsafe")
    if enforce_frozen_hashes:
        observed = {name: _sha(root / name) for name in EXPECTED_FILES}
        if observed != EXPECTED_OUTPUT_SHA256:
            raise ValueError("frozen output SHA mismatch")
    sources = _verified_sources()
    contract = _csv(root / CONTRACT_FILE, CONTRACT_HEADER)
    mapping = _csv(root / MAPPING_FILE, MAPPING_HEADER)
    truth = _csv(root / TRUTH_FILE, TRUTH_HEADER)
    source_rows = _csv(root / SOURCE_FILE, SOURCE_HEADER)
    issues = _csv(root / ISSUE_FILE, ISSUE_HEADER)
    manifest = json.loads((root / MANIFEST_FILE).read_text(encoding="utf-8"))
    _validate_contract(contract)
    _validate_mapping(mapping)
    _validate_truth(truth)
    _validate_source_rows(source_rows)
    _validate_issue_transition(issues, sources)
    _validate_manifest(manifest, root)
    if tuple(field.name for field in fields(LeakageGroupAssignmentProvenanceContractV1)) != EXACT19_FIELDS:
        raise ValueError("Exact19 class order mismatch")
    if hasattr(LeakageGroupAssignmentProvenanceContractV1, "__slots__"):
        raise ValueError("Exact19 class unexpectedly uses slots")
    _validate_oracle()
    _validate_no_premature_api()
    if exercise_materializer:
        _validate_materializer()
    return {
        "stage": EXPECTED_STAGE, "output_file_count": len(EXPECTED_FILES),
        "contract_row_count": len(contract), "mapping_grammar_row_count": len(mapping),
        "truth_row_count": len(truth), "source_row_count": len(source_rows),
        "issue_row_count": len(issues), "exact19_field_count": len(EXACT19_FIELDS),
        "source_input_count": len(sources), "frozen_hashes_enforced": enforce_frozen_hashes,
        "materializer_exercised": exercise_materializer,
        "ready_for_admit_010_standalone_evaluator_interface_implementation":
            manifest["ready_for_admit_010_standalone_evaluator_interface_implementation"],
    }


def main() -> int:
    result = check_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
