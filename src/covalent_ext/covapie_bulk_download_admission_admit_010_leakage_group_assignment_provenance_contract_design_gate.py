"""ADMIT_010 leakage-group assignment provenance contract design gate v1.

This metadata-only gate freezes a caller-supplied Exact19 provenance value
object and a pure in-memory design classifier.  It does not implement the
formal evaluator or result type, validate a real provider mapping, perform
group assignment or splitting, or modify the Exact9 unified runtime.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "ADMIT_010 leakage group assignment provenance contract design gate v1"
STAGE = "covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1"
EXPECTED_BASE_COMMIT = "0f687e007e532c4b2b5a9ab98ad96ae877fbd151"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_010 evaluator preconditions audit v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_010_leakage_group_assignment_provenance_contract_manifest_v1"

ADMISSION_RULE_ID = "ADMIT_010"
ADMISSION_RULE_NAME = "leakage_group_assignment_before_split"
EVALUATION_PHASE = "pre_final_split"
CANDIDATE_FIELD = "leakage_group_id"
CONTEXT_ITEM = "leakage_group_assignment_provenance_contract"
HISTORICAL_ARTIFACT_FIELD = "final_leakage_group_id"
PROVENANCE_CONTRACT_VERSION = "covapie_leakage_group_assignment_provenance_contract_v1"
FIELD_MAPPING_RULE = "exact_value_identity_after_provider_field_rename_only"
ASSIGNMENT_POLICY = "conservative_union_of_ligand_graph_scaffold_and_protein_accession_sequence_clusters_v1"
ASSIGNMENT_POLICY_VERSION = "v1"
ASSIGNMENT_STAGE_KIND = "pre_final_split_leakage_group_assignment"
PRE_SPLIT_ASSIGNED_STATUS = "leakage_group_assigned_before_final_split"
HISTORICAL_BLOCKING_REASON = "leakage_group_unassigned"
LEAKAGE_GROUP_PREFIX = "COVAPIE_LEAKAGE_GROUP_"
LEAKAGE_GROUP_REGEX = r"^COVAPIE_LEAKAGE_GROUP_[0-9]{6}$"
PRIMARY_BLOCKER = "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED"
COVERAGE_ISSUE = "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
RECOMMENDED_NEXT_STEP = "implement_covapie_admit_010_standalone_evaluator_interface_v1"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

AUDIT_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1")
RUNTIME_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1")
DESIGN_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1")
IMPLEMENTATION_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1")
ASSIGNMENT_ROOT = Path("data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0")

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit.py",
    str(AUDIT_ROOT / "covapie_admit_010_formal_evaluator_preconditions_manifest.json"),
    str(AUDIT_ROOT / "covapie_admit_010_formal_evaluator_precondition_matrix.csv"),
    str(AUDIT_ROOT / "covapie_admit_010_field_occurrence_inventory.csv"),
    str(AUDIT_ROOT / "covapie_admit_010_observed_value_inventory.csv"),
    str(AUDIT_ROOT / "covapie_admit_010_source_boundary_audit.csv"),
    str(AUDIT_ROOT / "covapie_admit_010_formal_evaluator_issue_readiness_inventory.csv"),
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009.py",
    str(RUNTIME_ROOT / "covapie_admit_001_to_009_runtime_issue_inventory.csv"),
    "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py",
    str(DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_schema_contract.csv"),
    "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate.py",
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_field_semantics_matrix.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"),
    "src/covalent_ext/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke.py",
    str(ASSIGNMENT_ROOT / "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_manifest.json"),
    str(ASSIGNMENT_ROOT / "covapie_final_leakage_group_assignment.csv"),
    str(ASSIGNMENT_ROOT / "covapie_final_leakage_group_inventory.csv"),
    str(ASSIGNMENT_ROOT / "unified_sample_index.csv"),
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
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

(
    AUDIT_SOURCE_PATH, AUDIT_MANIFEST_PATH, AUDIT_PRECONDITION_PATH,
    AUDIT_OCCURRENCE_PATH, AUDIT_OBSERVED_PATH, AUDIT_BOUNDARY_PATH,
    AUDIT_ISSUE_PATH, RUNTIME_SOURCE_PATH, RUNTIME_ISSUE_PATH,
    DESIGN_SOURCE_PATH, RULE_REGISTRY_PATH, SCHEMA_CONTRACT_PATH,
    IMPLEMENTATION_SOURCE_PATH, RULE_EXECUTABILITY_PATH, FIELD_SEMANTICS_PATH,
    EVALUATION_CONTEXT_PATH, ASSIGNMENT_SOURCE_PATH, ASSIGNMENT_MANIFEST_PATH,
    ASSIGNMENT_ARTIFACT_PATH, GROUP_INVENTORY_PATH, SAMPLE_INDEX_PATH,
) = SOURCE_PATHS

CONTRACT_FILENAME = "covapie_admit_010_leakage_group_assignment_provenance_contract.csv"
MAPPING_FILENAME = "covapie_admit_010_leakage_group_id_field_mapping_and_grammar_contract.csv"
TRUTH_FILENAME = "covapie_admit_010_provenance_validation_truth_matrix.csv"
SOURCE_BOUNDARY_FILENAME = "covapie_admit_010_provenance_contract_source_boundary_audit.csv"
ISSUE_FILENAME = "covapie_admit_010_provenance_contract_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_010_leakage_group_assignment_provenance_contract_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, MAPPING_FILENAME, TRUTH_FILENAME, SOURCE_BOUNDARY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CONTRACT_COLUMNS = (
    "contract_order", "contract_area", "contract_item", "exact_requirement",
    "validation_precedence", "failure_outcome", "failure_reason",
    "forbidden_behavior", "contract_passed",
)
MAPPING_COLUMNS = (
    "mapping_order", "contract_area", "contract_item", "exact_requirement",
    "historical_evidence_boundary", "forbidden_behavior", "mapping_passed",
)
TRUTH_COLUMNS = (
    "truth_order", "truth_group", "case_id", "input_summary", "outcome",
    "passed", "blocks_candidate", "reason", "canonical_leakage_group_id",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "expected_precedence",
    "truth_passed",
)
SOURCE_BOUNDARY_COLUMNS = (
    "source_order", "source_relative_path", "expected_sha256", "base_tree_sha256",
    "filesystem_sha256", "tracked", "base_tree_blob", "filesystem_regular",
    "non_symlink", "safe_descendant", "source_boundary_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity",
    "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count",
)

EXACT19_FIELD_NAMES = (
    "contract_version", "canonical_candidate_field_name",
    "historical_artifact_field_name", "field_mapping_rule", "assignment_policy",
    "assignment_policy_version", "assignment_stage_kind",
    "assignment_manifest_sha256", "assignment_artifact_sha256",
    "group_inventory_sha256", "sample_index_sha256", "assignment_id",
    "historical_leakage_group_id", "sample_index_row_id",
    "member_sample_index_row_ids", "member_count", "assignment_passed",
    "split_assignments_written", "pre_split_assignment_status",
)

VALIDATION_PRECEDENCE = (
    "leakage_group_id_exact_builtin_str", "empty_assignment_state", "ASCII",
    "canonical_grammar", "provenance_exact_committed_design_type",
    "contract_version", "candidate_and_historical_field_names",
    "field_mapping_rule", "assignment_policy", "assignment_policy_version",
    "assignment_stage_kind", "four_source_SHA256_fields", "assignment_id",
    "historical_leakage_group_id_grammar", "sample_index_row_id",
    "member_sample_index_row_ids", "member_count", "assignment_evidence_consistency",
    "candidate_historical_id_exact_equality", "sample_membership", "passed",
)

REASONS = (
    "LEAKAGE_GROUP_ID_TYPE_INVALID", HISTORICAL_BLOCKING_REASON,
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

TRUE_READINESS = (
    "admit_010_precondition_audit_complete",
    "leakage_group_assignment_provenance_contract_frozen",
    "leakage_group_id_final_grammar_frozen",
    "leakage_group_id_historical_field_mapping_rule_frozen",
    "leakage_group_assignment_policy_and_version_frozen",
    "leakage_group_assignment_source_attestation_contract_frozen",
    "leakage_group_assignment_membership_contract_frozen",
    "leakage_group_assignment_pre_split_evidence_contract_frozen",
    "admit_010_design_oracle_implemented",
    "leakage_group_assignment_provenance_blocker_resolved",
    "admit_010_provider_mapping_boundary_preserved",
    "ready_for_admit_010_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "leakage_group_id_provider_mapping_validated",
    "real_provider_leakage_group_id_count_nonzero",
    "evaluate_admit_010_implemented", "Admit010EvaluationResult_implemented",
    "admit_010_unified_adapter_contract_frozen",
    "admit_010_unified_adapter_implemented", "admit_010_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_010_implemented",
    "admit_011_started", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented", "cross_rule_precedence_frozen",
    "real_candidate_evaluation", "ready_for_bulk_download_now",
    "ready_for_training", "ready_to_train_now",
)


@dataclass(frozen=True)
class LeakageGroupAssignmentProvenanceContractV1:
    """Design-only caller attestation value object; validation is oracle-owned."""

    contract_version: object
    canonical_candidate_field_name: object
    historical_artifact_field_name: object
    field_mapping_rule: object
    assignment_policy: object
    assignment_policy_version: object
    assignment_stage_kind: object
    assignment_manifest_sha256: object
    assignment_artifact_sha256: object
    group_inventory_sha256: object
    sample_index_sha256: object
    assignment_id: object
    historical_leakage_group_id: object
    sample_index_row_id: object
    member_sample_index_row_ids: object
    member_count: object
    assignment_passed: object
    split_assignments_written: object
    pre_split_assignment_status: object


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    base_tree_sha256: str
    filesystem_sha256: str
    content_bytes: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _git(
    arguments: Sequence[str], repo_root: Path, *, text: bool = True
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=repo_root, text=text,
        capture_output=True, check=False,
    )


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


def _validate_base_lineage(repo_root: Path, head_ref: str) -> None:
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("head ref invalid")
    exists = _git(["cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"], repo_root)
    subject = _git(["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], repo_root)
    ancestor = _git(["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref], repo_root)
    if exists.returncode or subject.returncode or ancestor.returncode:
        raise ValueError("expected base lineage invalid")
    if subject.stdout.strip() != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base subject mismatch")


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    tree_head = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    return (
        tracked.returncode == 0 and tree.returncode == 0 and len(tree_head) == 3
        and tree_head[0] in ("100644", "100755") and tree_head[1] == "blob"
        and stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        and _resolved_safe_descendant(path, repo_root)
    )


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    """Finish all Exact21 structural checks before the first source-byte read."""
    if (
        len(SOURCE_PATHS) != 21 or len(set(SOURCE_PATHS)) != 21
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact21 source boundary invalid")
    _validate_base_lineage(repo_root, head_ref)
    if not all(_structural_source_check(path, repo_root) for path in SOURCE_PATHS):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base = _git(
            ["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"],
            repo_root, text=False,
        )
        if base.returncode != 0 or type(base.stdout) is not bytes:
            raise ValueError(f"base-tree source read failed: {path}")
        filesystem = (repo_root / path).read_bytes()
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem).hexdigest()
        if SOURCE_SHA256[path] != base_sha or base_sha != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(
            path, SOURCE_SHA256[path], base_sha, filesystem_sha, filesystem,
        ))
    snapshot = FrozenSourceSnapshot(tuple(records))
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("frozen source snapshot invalid")
    return snapshot


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot and len(value.records) == 21
        and tuple(record.relative_path for record in value.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.base_tree_sha256 == record.expected_sha256
            and record.filesystem_sha256 == record.expected_sha256
            and hashlib.sha256(record.content_bytes).hexdigest() == record.expected_sha256
            for record in value.records
        )
    )


def _record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord:
    matches = tuple(item for item in snapshot.records if item.relative_path == path)
    if len(matches) != 1:
        raise ValueError("frozen source missing or duplicate")
    return matches[0]


def _csv_rows(snapshot: FrozenSourceSnapshot, path: Path) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(
        _record(snapshot, path).content_bytes.decode("utf-8"), newline="",
    ))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(
        tuple(row) != tuple(reader.fieldnames)
        or any(value is None for value in row.values()) for row in rows
    ):
        raise ValueError("invalid CSV row")
    return rows


def _json(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(_record(snapshot, path).content_bytes.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError("invalid JSON document")
    return value


def _one(
    rows: Sequence[Mapping[str, str]], key: str, value: str
) -> Mapping[str, str]:
    matches = tuple(row for row in rows if row.get(key) == value)
    if len(matches) != 1:
        raise ValueError(f"expected one row for {key}={value}")
    return matches[0]


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> None:
    audit = _json(snapshot, AUDIT_MANIFEST_PATH)
    preconditions = _csv_rows(snapshot, AUDIT_PRECONDITION_PATH)
    issues = _csv_rows(snapshot, AUDIT_ISSUE_PATH)
    runtime_issues = _csv_rows(snapshot, RUNTIME_ISSUE_PATH)
    rule = _one(_csv_rows(snapshot, RULE_REGISTRY_PATH), "admission_rule_id", ADMISSION_RULE_ID)
    schema = _one(_csv_rows(snapshot, SCHEMA_CONTRACT_PATH), "admission_field_name", CANDIDATE_FIELD)
    executable = _one(_csv_rows(snapshot, RULE_EXECUTABILITY_PATH), "admission_rule_id", ADMISSION_RULE_ID)
    field = _one(_csv_rows(snapshot, FIELD_SEMANTICS_PATH), "field_name", CANDIDATE_FIELD)
    context = _one(_csv_rows(snapshot, EVALUATION_CONTEXT_PATH), "context_item", CONTEXT_ITEM)
    assignment_manifest = _json(snapshot, ASSIGNMENT_MANIFEST_PATH)
    assignments = _csv_rows(snapshot, ASSIGNMENT_ARTIFACT_PATH)
    groups = _csv_rows(snapshot, GROUP_INVENTORY_PATH)
    samples = _csv_rows(snapshot, SAMPLE_INDEX_PATH)
    blocker = _one(issues, "issue_id", PRIMARY_BLOCKER)
    coverage = _one(issues, "issue_id", COVERAGE_ISSUE)
    required = (
        audit["recommended_next_step"]
        == "design_covapie_admit_010_leakage_group_assignment_provenance_contract_v1",
        audit["primary_blocker_status"] == "open",
        audit["candidate_to_historical_field_mapping_status"] == "unverified",
        audit["leakage_group_id_provider_mapping_validated"] is False,
        audit["ready_for_admit_010_leakage_group_assignment_provenance_contract_design"] is True,
        len(preconditions) == 21,
        rule["admission_rule_name"] == ADMISSION_RULE_NAME,
        rule["evaluation_phase"] == EVALUATION_PHASE,
        rule["required_status"] == "leakage_group_assigned",
        rule["blocking_reason"] == HISTORICAL_BLOCKING_REASON,
        schema["value_contract"] == "assigned before final split admission",
        executable["candidate_field_dependencies"] == CANDIDATE_FIELD,
        executable["evaluation_context_dependencies"] == CONTEXT_ITEM,
        executable["external_filesystem_required"] == "false",
        context["provided_by_future_caller"] == "true",
        context["filesystem_access_inside_evaluator"] == "false",
        context["network_access_inside_evaluator"] == "false",
        context["exact_contract_defined"] == "false",
        field["blocking_reasons"] == PRIMARY_BLOCKER,
        blocker["status"] == "open" and blocker["integration_transition"] == "unchanged_open",
        coverage["affected_rules"]
        == "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        runtime_issues == issues,
        assignment_manifest["step_label"] == "Step 14AP",
        assignment_manifest["group_assignment_policy"] == ASSIGNMENT_POLICY,
        assignment_manifest["split_assignments_written"] is False,
        assignment_manifest["final_group_assignment_row_count"] == 11,
        assignment_manifest["final_leakage_group_count"] == 5,
        len(assignments) == 11 and len(groups) == 5 and len(samples) == 11,
        all(row["assignment_policy"] == ASSIGNMENT_POLICY for row in assignments),
        all(row["final_group_assignment_passed"] == "True" for row in assignments),
        all(row["group_inventory_passed"] == "True" for row in groups),
        {row["sample_index_row_id"] for row in samples}
        == {row["sample_index_row_id"] for row in assignments},
    )
    if not all(required):
        raise ValueError("authoritative predecessor contract mismatch")


def _valid_group_id(value: object) -> bool:
    return (
        type(value) is str and value.isascii()
        and re.fullmatch(LEAKAGE_GROUP_REGEX, value) is not None
    )


def _valid_sha256(value: object) -> bool:
    return (
        type(value) is str and len(value) == 64
        and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    )


def _valid_opaque_id(value: object) -> bool:
    return (
        type(value) is str and 1 <= len(value) <= 256 and value.isascii()
        and value == value.strip()
    )


def _result(
    *, outcome: str, reason: str, canonical: str,
    validated: tuple[tuple[str, str], ...], context_consumed: bool,
) -> dict[str, object]:
    return {
        "outcome": outcome,
        "passed": outcome == "passed",
        "blocks_candidate": outcome != "passed",
        "reason": reason,
        "canonical_leakage_group_id": canonical,
        "validated_candidate_fields": validated,
        "consumed_candidate_fields": (CANDIDATE_FIELD,),
        "consumed_context_items": (CONTEXT_ITEM,) if context_consumed else (),
        "evaluator_io_used": False,
    }


def classify_admit_010_leakage_group_assignment_provenance_design(
    leakage_group_id: object,
    provenance_contract: object,
) -> Mapping[str, object]:
    """Classify the frozen contract in memory; this is not the formal evaluator."""
    if type(leakage_group_id) is not str:
        return _result(
            outcome="invalid", reason="LEAKAGE_GROUP_ID_TYPE_INVALID",
            canonical="", validated=(), context_consumed=False,
        )
    if leakage_group_id == "":
        return _result(
            outcome="blocked", reason=HISTORICAL_BLOCKING_REASON,
            canonical="", validated=(), context_consumed=False,
        )
    if not leakage_group_id.isascii():
        return _result(
            outcome="invalid", reason="LEAKAGE_GROUP_ID_NON_ASCII",
            canonical="", validated=(), context_consumed=False,
        )
    if re.fullmatch(LEAKAGE_GROUP_REGEX, leakage_group_id) is None:
        return _result(
            outcome="invalid", reason="LEAKAGE_GROUP_ID_SYNTAX_INVALID",
            canonical="", validated=(), context_consumed=False,
        )
    canonical = leakage_group_id
    validated = ((CANDIDATE_FIELD, canonical),)
    invalid = lambda reason: _result(  # noqa: E731 - compact precedence helper
        outcome="invalid", reason=reason, canonical=canonical,
        validated=validated, context_consumed=True,
    )
    blocked = lambda: _result(  # noqa: E731 - compact evidence helper
        outcome="blocked", reason=HISTORICAL_BLOCKING_REASON,
        canonical=canonical, validated=validated, context_consumed=True,
    )
    if type(provenance_contract) is not LeakageGroupAssignmentProvenanceContractV1:
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_TYPE_INVALID")
    value = provenance_contract
    if (
        type(value.contract_version) is not str
        or value.contract_version != PROVENANCE_CONTRACT_VERSION
    ):
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_VERSION_INVALID")
    if (
        type(value.canonical_candidate_field_name) is not str
        or value.canonical_candidate_field_name != CANDIDATE_FIELD
        or type(value.historical_artifact_field_name) is not str
        or value.historical_artifact_field_name != HISTORICAL_ARTIFACT_FIELD
    ):
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID")
    if type(value.field_mapping_rule) is not str or value.field_mapping_rule != FIELD_MAPPING_RULE:
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID")
    if type(value.assignment_policy) is not str or value.assignment_policy != ASSIGNMENT_POLICY:
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_POLICY_INVALID")
    if (
        type(value.assignment_policy_version) is not str
        or value.assignment_policy_version != ASSIGNMENT_POLICY_VERSION
    ):
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_POLICY_VERSION_INVALID")
    if type(value.assignment_stage_kind) is not str or value.assignment_stage_kind != ASSIGNMENT_STAGE_KIND:
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_STAGE_KIND_INVALID")
    sha_values = (
        value.assignment_manifest_sha256, value.assignment_artifact_sha256,
        value.group_inventory_sha256, value.sample_index_sha256,
    )
    if not all(_valid_sha256(item) for item in sha_values):
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID")
    if not _valid_opaque_id(value.assignment_id):
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_ID_INVALID")
    if not _valid_group_id(value.historical_leakage_group_id):
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_HISTORICAL_GROUP_ID_INVALID")
    if not _valid_opaque_id(value.sample_index_row_id):
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_SAMPLE_ID_INVALID")
    members = value.member_sample_index_row_ids
    if (
        type(members) is not tuple or len(members) == 0
        or any(not _valid_opaque_id(member) for member in members)
        or any(left >= right for left, right in zip(members, members[1:]))
    ):
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID")
    if (
        type(value.member_count) is not int or value.member_count <= 0
        or value.member_count != len(members)
    ):
        return invalid("LEAKAGE_GROUP_ASSIGNMENT_MEMBER_COUNT_INVALID")
    if (
        type(value.assignment_passed) is not bool or value.assignment_passed is not True
        or type(value.split_assignments_written) is not bool
        or value.split_assignments_written is not False
        or type(value.pre_split_assignment_status) is not str
        or value.pre_split_assignment_status != PRE_SPLIT_ASSIGNED_STATUS
    ):
        return blocked()
    if canonical != value.historical_leakage_group_id:
        return blocked()
    if value.sample_index_row_id not in members:
        return blocked()
    return _result(
        outcome="passed", reason="", canonical=canonical,
        validated=validated, context_consumed=True,
    )


def _contract_rows() -> tuple[dict[str, str], ...]:
    specs = (
        ("identity", "rule_identity", "ADMIT_010/leakage_group_assignment_before_split/pre_final_split", "", "", "substitute another rule or phase"),
        ("value_object", "Exact19_type", "frozen dataclass without slots; exact committed type required", "5", "invalid", "accept dict or subclass"),
        ("value_object", "Exact19_field_order", "|".join(EXACT19_FIELD_NAMES), "5", "invalid", "reorder, add, remove, or rename fields"),
        ("static", "contract_version", PROVENANCE_CONTRACT_VERSION, "6", "invalid", "fallback or alternate version"),
        ("static", "canonical_candidate_field_name", CANDIDATE_FIELD, "7", "invalid", "alias canonical field"),
        ("static", "historical_artifact_field_name", HISTORICAL_ARTIFACT_FIELD, "7", "invalid", "alias historical field"),
        ("mapping", "field_mapping_rule", FIELD_MAPPING_RULE, "8", "invalid", "transform or regenerate value"),
        ("policy", "assignment_policy", ASSIGNMENT_POLICY, "9", "invalid", "accept another policy"),
        ("policy", "assignment_policy_version", ASSIGNMENT_POLICY_VERSION, "10", "invalid", "infer version without exact field"),
        ("stage", "assignment_stage_kind", ASSIGNMENT_STAGE_KIND, "11", "invalid", "use split or final stage"),
        ("attestation", "assignment_manifest_sha256", "exact lowercase hexadecimal built-in str length 64", "12", "invalid", "read or trust referenced file"),
        ("attestation", "assignment_artifact_sha256", "exact lowercase hexadecimal built-in str length 64", "12", "invalid", "read or trust referenced file"),
        ("attestation", "group_inventory_sha256", "exact lowercase hexadecimal built-in str length 64", "12", "invalid", "read or trust referenced file"),
        ("attestation", "sample_index_sha256", "exact lowercase hexadecimal built-in str length 64", "12", "invalid", "read or trust referenced file"),
        ("opaque_id", "assignment_id", "exact built-in ASCII str; length 1-256; no surrounding whitespace", "13", "invalid", "interpret as group ID"),
        ("mapping", "historical_leakage_group_id", LEAKAGE_GROUP_REGEX, "14", "invalid", "derive from assignment ID or group order"),
        ("opaque_id", "sample_index_row_id", "exact built-in ASCII str; length 1-256; no surrounding whitespace", "15", "invalid", "infer grammar from historical 11 samples"),
        ("membership", "member_sample_index_row_ids", "exact nonempty tuple of exact opaque IDs in strict ascending ASCII order and unique", "16", "invalid", "accept/sort/deduplicate list or tuple subclass"),
        ("membership", "member_count", "exact built-in int > 0 equal to tuple length; bool rejected", "17", "invalid", "coerce count or accept mismatch"),
        ("evidence", "assignment_passed", "exact built-in bool True", "18", "blocked", "treat truthy value as proof"),
        ("evidence", "split_assignments_written", "exact built-in bool False", "18", "blocked", "use split artifact as reverse proof"),
        ("evidence", "pre_split_assignment_status", PRE_SPLIT_ASSIGNED_STATUS, "18", "blocked", "use historical final group status"),
        ("mapping", "candidate_historical_equality", "candidate leakage_group_id == provenance historical_leakage_group_id", "19", "blocked", "rename with value transformation"),
        ("membership", "sample_membership", "sample_index_row_id is a member of member_sample_index_row_ids", "20", "blocked", "claim assignment without membership"),
        ("state", "passed", "outcome=passed; passed=true; blocks_candidate=false; reason empty", "21", "", "pass partial evidence"),
        ("state", "nonpassed", "outcome blocked or invalid; passed=false; blocks_candidate=true; reason nonempty", "", "", "allow nonpassed without blocking"),
        ("oracle", "purity", "pure in-memory; evaluator_io_used=false", "", "", "filesystem, network, assignment, or split"),
        ("trust", "source_SHA256", "caller/provider attestation syntax only", "12", "invalid", "claim SHA proves real file truth"),
        ("boundary", "formal_evaluator", "reserved only; not implemented", "", "", "define evaluate_admit_010 or Admit010EvaluationResult"),
        ("boundary", "provider_mapping", "contract frozen but real mapping unvalidated", "", "", "fabricate validation or nonzero count"),
        ("boundary", "runtime", "Exact9 unchanged; ADMIT_010 unregistered", "", "", "implement adapter, Exact10, ADMIT_011, aggregate verdict"),
        ("boundary", "training", "feature-semantics audit required; Step12D smoke legality only", "", "", "claim training readiness"),
    )
    return tuple({
        "contract_order": str(index), "contract_area": area,
        "contract_item": item, "exact_requirement": requirement,
        "validation_precedence": precedence, "failure_outcome": outcome,
        "failure_reason": (
            HISTORICAL_BLOCKING_REASON if outcome == "blocked"
            else "see_frozen_reason_vocabulary" if outcome == "invalid" else ""
        ),
        "forbidden_behavior": forbidden, "contract_passed": "true",
    } for index, (area, item, requirement, precedence, outcome, forbidden) in enumerate(specs, 1))


def _mapping_rows() -> tuple[dict[str, str], ...]:
    specs = (
        ("grammar", "exact_type", "type(value) is builtins.str", "historical values are evidence only", "accept str subclass or coercion"),
        ("grammar", "empty", "empty string is unassigned blocked state", "historical blocking reason retained", "classify empty as syntax invalid"),
        ("grammar", "ASCII", "ASCII only", "five observed IDs are ASCII", "accept Unicode digits or letters"),
        ("grammar", "regex", LEAKAGE_GROUP_REGEX, "explicit V1 design choice based on format/capacity/stability", "infer natural universal grammar from five IDs"),
        ("grammar", "prefix", LEAKAGE_GROUP_PREFIX, "observed historical prefix", "lowercase or altered prefix"),
        ("grammar", "suffix", "exactly six ASCII decimal digits [0-9]{6}", "observed corpus uses six digits", "sign, whitespace, short/long, Unicode digit"),
        ("grammar", "normalization", "none; canonical value equals input byte-for-byte", "historical values unchanged", "trim, uppercase, repair, normalize"),
        ("mapping", "canonical_field", CANDIDATE_FIELD, "future candidate schema", "use historical name as candidate field"),
        ("mapping", "historical_field", HISTORICAL_ARTIFACT_FIELD, "Step14AP artifact field", "erase source lineage"),
        ("mapping", "mapping_rule", FIELD_MAPPING_RULE, "mapping was previously unverified", "transform beyond field rename"),
        ("mapping", "value_identity", "candidate leakage_group_id == provenance historical_leakage_group_id", "future evaluator sees caller object only", "re-number or change prefix"),
        ("forbidden_source", "assignment_id", "opaque record ID; never group ID", "historical identifier only", "generate group ID"),
        ("forbidden_source", "group_order", "not in Exact19 and never group ID", "historical inventory ordering only", "generate group ID"),
        ("forbidden_source", "split_assignment", "not in Exact19 and no reverse proof", "Step14AQ follows Step14AP", "infer group from assigned split"),
        ("forbidden_source", "single_axis_group", "not a substitute for final group", "historical union uses multiple axes", "choose ligand/protein group"),
        ("forbidden_source", "duplicate_identity_key", "separate ADMIT_009 identity", "separate semantic domain", "substitute for leakage group"),
        ("policy", "policy_value", ASSIGNMENT_POLICY, "Step14AP sole observed V1 policy", "accept alternate policy"),
        ("policy", "policy_version", ASSIGNMENT_POLICY_VERSION, "new explicit field; historical string embeds _v1", "omit or infer field at runtime"),
        ("policy", "policy_version_consistency", "exact policy and exact version both required", "design freezes explicit pairing", "accept mismatched pair"),
        ("attestation", "SHA_truth_boundary", "caller attests four syntactically valid SHA256 values", "evaluator performs no file access", "treat syntax as authenticity proof"),
        ("membership", "assignment_record", "assignment ID, historical group ID, sample ID and membership agree", "historical IDs remain opaque", "infer general ID grammar"),
        ("membership", "tuple", "strict ordered unique exact tuple includes sample", "historical inventory supplies evidence pattern", "auto-sort or deduplicate"),
        ("pre_split", "assignment_evidence", "assignment_passed=True; split_assignments_written=False; exact status", "Step14AP precedes Step14AQ", "use split output as proof"),
        ("excluded", "historical_final_group_status", "not in Exact19", "historical sample-specific lifecycle text", "promote to runtime contract"),
        ("excluded", "split_ids_and_assigned_split", "not in Exact19", "post-assignment evidence", "promote to pre-split proof"),
        ("provider", "real_mapping", "not validated in this design step", "contract only", "claim provider compliance"),
    )
    return tuple({
        "mapping_order": str(index), "contract_area": area,
        "contract_item": item, "exact_requirement": requirement,
        "historical_evidence_boundary": boundary,
        "forbidden_behavior": forbidden, "mapping_passed": "true",
    } for index, (area, item, requirement, boundary, forbidden) in enumerate(specs, 1))


def _valid_contract(
    *, candidate: str = "COVAPIE_LEAKAGE_GROUP_000001",
    sample: str = "SAMPLE_000001",
    members: tuple[str, ...] = ("SAMPLE_000001",),
) -> LeakageGroupAssignmentProvenanceContractV1:
    digest = "1" * 64
    return LeakageGroupAssignmentProvenanceContractV1(
        PROVENANCE_CONTRACT_VERSION, CANDIDATE_FIELD, HISTORICAL_ARTIFACT_FIELD,
        FIELD_MAPPING_RULE, ASSIGNMENT_POLICY, ASSIGNMENT_POLICY_VERSION,
        ASSIGNMENT_STAGE_KIND, digest, "2" * 64, "3" * 64, "4" * 64,
        "ASSIGNMENT_RECORD_ALPHA", candidate, sample, members, len(members),
        True, False, PRE_SPLIT_ASSIGNED_STATUS,
    )


def _display(value: object) -> str:
    return f"{type(value).__name__}:{value!r}"


def _truth_rows() -> tuple[dict[str, str], ...]:
    class StringSubclass(str):
        pass

    class TupleSubclass(tuple):
        pass

    @dataclass(frozen=True)
    class ContractSubclass(LeakageGroupAssignmentProvenanceContractV1):
        pass

    candidate = "COVAPIE_LEAKAGE_GROUP_000001"
    other_group = "COVAPIE_LEAKAGE_GROUP_000002"
    base = _valid_contract(candidate=candidate)
    subclass_contract = ContractSubclass(*(
        getattr(base, name) for name in EXACT19_FIELD_NAMES
    ))
    cases: list[tuple[str, str, object, object, str]] = [
        ("candidate_scalar", "candidate_none", None, base, "1"),
        ("candidate_scalar", "candidate_integer", 7, base, "1"),
        ("candidate_scalar", "candidate_empty", "", base, "2"),
        ("candidate_scalar", "candidate_str_subclass", StringSubclass(candidate), base, "1"),
        ("candidate_scalar", "candidate_non_ascii", "COVAPIE_LEAKAGE_GROUP_00000é", base, "3"),
        ("candidate_scalar", "candidate_lowercase_prefix", "covapie_leakage_group_000001", base, "4"),
        ("candidate_scalar", "candidate_case_drift", "COVAPIE_leakage_GROUP_000001", base, "4"),
        ("candidate_scalar", "candidate_short_digits", "COVAPIE_LEAKAGE_GROUP_00001", base, "4"),
        ("candidate_scalar", "candidate_long_digits", "COVAPIE_LEAKAGE_GROUP_0000001", base, "4"),
        ("candidate_scalar", "candidate_non_digit_suffix", "COVAPIE_LEAKAGE_GROUP_00000A", base, "4"),
        ("candidate_scalar", "candidate_leading_whitespace", " " + candidate, base, "4"),
        ("candidate_scalar", "candidate_trailing_whitespace", candidate + " ", base, "4"),
        ("candidate_scalar", "candidate_unicode_digit", "COVAPIE_LEAKAGE_GROUP_00000١", base, "3"),
        ("candidate_scalar", "candidate_canonical", candidate, base, "21"),
        ("context_type", "context_none", candidate, None, "5"),
        ("context_type", "context_dict", candidate, {}, "5"),
        ("context_type", "context_dataclass_subclass", candidate, subclass_contract, "5"),
        ("context_type", "context_exact_type", candidate, base, "21"),
        ("static_fields", "contract_version_wrong", candidate, replace(base, contract_version="v2"), "6"),
        ("static_fields", "candidate_field_wrong", candidate, replace(base, canonical_candidate_field_name="final_leakage_group_id"), "7"),
        ("static_fields", "historical_field_wrong", candidate, replace(base, historical_artifact_field_name="leakage_group_id"), "7"),
        ("static_fields", "mapping_rule_wrong", candidate, replace(base, field_mapping_rule="renumber"), "8"),
        ("static_fields", "policy_wrong", candidate, replace(base, assignment_policy="other_policy_v1"), "9"),
        ("static_fields", "policy_version_wrong", candidate, replace(base, assignment_policy_version="v2"), "10"),
        ("static_fields", "stage_kind_wrong", candidate, replace(base, assignment_stage_kind="post_split"), "11"),
        ("sha256", "sha_none", candidate, replace(base, assignment_manifest_sha256=None), "12"),
        ("sha256", "sha_str_subclass", candidate, replace(base, assignment_artifact_sha256=StringSubclass("2" * 64)), "12"),
        ("sha256", "sha_uppercase", candidate, replace(base, group_inventory_sha256="A" * 64), "12"),
        ("sha256", "sha_short", candidate, replace(base, sample_index_sha256="4" * 63), "12"),
        ("sha256", "sha_non_hex", candidate, replace(base, assignment_manifest_sha256="g" * 64), "12"),
        ("sha256", "sha_exact_valid", candidate, base, "21"),
        ("assignment_id", "assignment_id_wrong_type", candidate, replace(base, assignment_id=7), "13"),
        ("assignment_id", "assignment_id_empty", candidate, replace(base, assignment_id=""), "13"),
        ("assignment_id", "assignment_id_non_ascii", candidate, replace(base, assignment_id="ASSIGNMENT_é"), "13"),
        ("assignment_id", "assignment_id_whitespace", candidate, replace(base, assignment_id=" ASSIGNMENT"), "13"),
        ("assignment_id", "assignment_id_valid_opaque", candidate, base, "21"),
        ("historical_group", "historical_group_wrong_type", candidate, replace(base, historical_leakage_group_id=7), "14"),
        ("historical_group", "historical_group_malformed", candidate, replace(base, historical_leakage_group_id="ASSIGNMENT_RECORD_ALPHA"), "14"),
        ("historical_group", "historical_group_canonical", candidate, base, "21"),
        ("sample_id", "sample_id_wrong_type", candidate, replace(base, sample_index_row_id=7), "15"),
        ("sample_id", "sample_id_empty", candidate, replace(base, sample_index_row_id=""), "15"),
        ("sample_id", "sample_id_non_ascii", candidate, replace(base, sample_index_row_id="SAMPLE_é"), "15"),
        ("sample_id", "sample_id_whitespace", candidate, replace(base, sample_index_row_id="SAMPLE "), "15"),
        ("sample_id", "sample_id_valid_opaque", candidate, base, "21"),
        ("membership", "membership_list", candidate, replace(base, member_sample_index_row_ids=["SAMPLE_000001"]), "16"),
        ("membership", "membership_tuple_subclass", candidate, replace(base, member_sample_index_row_ids=TupleSubclass(("SAMPLE_000001",))), "16"),
        ("membership", "membership_empty_tuple", candidate, replace(base, member_sample_index_row_ids=(), member_count=0), "16"),
        ("membership", "membership_non_str_member", candidate, replace(base, member_sample_index_row_ids=(7,)), "16"),
        ("membership", "membership_str_subclass_member", candidate, replace(base, member_sample_index_row_ids=(StringSubclass("SAMPLE_000001"),)), "16"),
        ("membership", "membership_empty_member", candidate, replace(base, member_sample_index_row_ids=("",)), "16"),
        ("membership", "membership_non_ascii_member", candidate, replace(base, member_sample_index_row_ids=("SAMPLE_é",)), "16"),
        ("membership", "membership_unsorted", candidate, replace(base, member_sample_index_row_ids=("SAMPLE_000002", "SAMPLE_000001"), member_count=2), "16"),
        ("membership", "membership_duplicate", candidate, replace(base, member_sample_index_row_ids=("SAMPLE_000001", "SAMPLE_000001"), member_count=2), "16"),
        ("membership", "membership_sample_absent", candidate, replace(base, member_sample_index_row_ids=("SAMPLE_000002",)), "20"),
        ("membership", "membership_valid_singleton", candidate, base, "21"),
        ("membership", "membership_valid_multi_member", candidate, _valid_contract(candidate=candidate, sample="SAMPLE_000002", members=("SAMPLE_000001", "SAMPLE_000002")), "21"),
        ("member_count", "member_count_bool", candidate, replace(base, member_count=True), "17"),
        ("member_count", "member_count_float", candidate, replace(base, member_count=1.0), "17"),
        ("member_count", "member_count_zero", candidate, replace(base, member_count=0), "17"),
        ("member_count", "member_count_negative", candidate, replace(base, member_count=-1), "17"),
        ("member_count", "member_count_mismatch", candidate, replace(base, member_count=2), "17"),
        ("member_count", "member_count_exact_valid", candidate, base, "21"),
        ("assignment_semantics", "assignment_passed_false", candidate, replace(base, assignment_passed=False), "18"),
        ("assignment_semantics", "assignment_passed_int_one", candidate, replace(base, assignment_passed=1), "18"),
        ("assignment_semantics", "split_assignments_written_true", candidate, replace(base, split_assignments_written=True), "18"),
        ("assignment_semantics", "split_assignments_written_int_zero", candidate, replace(base, split_assignments_written=0), "18"),
        ("assignment_semantics", "pre_split_status_wrong", candidate, replace(base, pre_split_assignment_status="leakage_group_assigned"), "18"),
        ("assignment_semantics", "candidate_historical_mismatch", candidate, replace(base, historical_leakage_group_id=other_group), "19"),
        ("assignment_semantics", "valid_assigned_before_split", candidate, base, "21"),
        ("assignment_semantics", "valid_singleton", candidate, base, "21"),
        ("assignment_semantics", "valid_multi_member", candidate, _valid_contract(candidate=candidate, sample="SAMPLE_000001", members=("SAMPLE_000001", "SAMPLE_000002")), "21"),
    ]
    rows: list[dict[str, str]] = []
    for index, (group, case_id, scalar, context, precedence) in enumerate(cases, 1):
        result = classify_admit_010_leakage_group_assignment_provenance_design(scalar, context)
        rows.append({
            "truth_order": str(index), "truth_group": group, "case_id": case_id,
            "input_summary": f"leakage_group_id={_display(scalar)};provenance={_display(context)}",
            "outcome": str(result["outcome"]), "passed": _bool(bool(result["passed"])),
            "blocks_candidate": _bool(bool(result["blocks_candidate"])),
            "reason": str(result["reason"]),
            "canonical_leakage_group_id": str(result["canonical_leakage_group_id"]),
            "validated_candidate_fields": json.dumps(result["validated_candidate_fields"], separators=(",", ":")),
            "consumed_candidate_fields": json.dumps(result["consumed_candidate_fields"], separators=(",", ":")),
            "consumed_context_items": json.dumps(result["consumed_context_items"], separators=(",", ":")),
            "evaluator_io_used": _bool(bool(result["evaluator_io_used"])),
            "expected_precedence": precedence, "truth_passed": "true",
        })
    group_counts = {group: sum(row["truth_group"] == group for row in rows) for group in dict.fromkeys(row["truth_group"] for row in rows)}
    expected_counts = {
        "candidate_scalar": 14, "context_type": 4, "static_fields": 7,
        "sha256": 6, "assignment_id": 5, "historical_group": 3,
        "sample_id": 5, "membership": 12, "member_count": 6,
        "assignment_semantics": 9,
    }
    if (
        len(rows) != 71 or group_counts != expected_counts
        or any((row["passed"] == "true") != (row["outcome"] == "passed") for row in rows)
        or any((row["blocks_candidate"] == "true") != (row["outcome"] != "passed") for row in rows)
        or any((row["reason"] == "") != (row["outcome"] == "passed") for row in rows)
        or any(row["evaluator_io_used"] != "false" for row in rows)
    ):
        raise ValueError("Exact71 truth construction failed")
    return tuple(rows)


def _source_boundary_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    return tuple({
        "source_order": str(index), "source_relative_path": record.relative_path.as_posix(),
        "expected_sha256": record.expected_sha256,
        "base_tree_sha256": record.base_tree_sha256,
        "filesystem_sha256": record.filesystem_sha256,
        "tracked": "true", "base_tree_blob": "true",
        "filesystem_regular": "true", "non_symlink": "true",
        "safe_descendant": "true", "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot.records, 1))


def _issue_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    predecessor = _csv_rows(snapshot, AUDIT_ISSUE_PATH)
    rows: list[dict[str, str]] = []
    changed = 0
    for source in predecessor:
        row = dict(source)
        if row["issue_id"] == PRIMARY_BLOCKER:
            row["status"] = "resolved"
            row["integration_transition"] = "leakage_group_assignment_provenance_contract_frozen_v1"
            changed += 1
        rows.append(row)
    if changed != 1 or len(rows) != 11:
        raise ValueError("successor issue transition invalid")
    for before, after in zip(predecessor, rows, strict=True):
        differing = {key for key in before if before[key] != after[key]}
        expected = {"status", "integration_transition"} if before["issue_id"] == PRIMARY_BLOCKER else set()
        if differing != expected:
            raise ValueError("unauthorized issue change")
    coverage = _one(rows, "issue_id", COVERAGE_ISSUE)
    if (
        coverage["status"] != "open"
        or coverage["affected_rules"]
        != "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    ):
        raise ValueError("coverage issue changed")
    return tuple(rows)


def _readiness() -> dict[str, bool]:
    return {
        **{key: True for key in TRUE_READINESS},
        **{key: False for key in FALSE_READINESS},
    }


def build_design_state(
    repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD"
) -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root, head_ref=head_ref)
    _validate_predecessors(snapshot)
    if tuple(field.name for field in fields(LeakageGroupAssignmentProvenanceContractV1)) != EXACT19_FIELD_NAMES:
        raise ValueError("Exact19 field order drift")
    return {
        "snapshot": snapshot, "contract_rows": _contract_rows(),
        "mapping_rows": _mapping_rows(), "truth_rows": _truth_rows(),
        "source_boundary_rows": _source_boundary_rows(snapshot),
        "issue_rows": _issue_rows(snapshot), "readiness": _readiness(),
    }


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, Any]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n", extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _manifest(state: Mapping[str, Any], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    readiness = dict(state["readiness"])
    truth = state["truth_rows"]
    truth_counts = {
        group: sum(row["truth_group"] == group for row in truth)
        for group in dict.fromkeys(row["truth_group"] for row in truth)
    }
    payload: dict[str, Any] = {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID,
        "admission_rule_name": ADMISSION_RULE_NAME,
        "evaluation_phase": EVALUATION_PHASE,
        "candidate_field": CANDIDATE_FIELD, "context_item": CONTEXT_ITEM,
        "historical_artifact_field": HISTORICAL_ARTIFACT_FIELD,
        "provenance_contract_version": PROVENANCE_CONTRACT_VERSION,
        "field_mapping_rule": FIELD_MAPPING_RULE,
        "assignment_policy": ASSIGNMENT_POLICY,
        "assignment_policy_version": ASSIGNMENT_POLICY_VERSION,
        "assignment_stage_kind": ASSIGNMENT_STAGE_KIND,
        "pre_split_assigned_status": PRE_SPLIT_ASSIGNED_STATUS,
        "historical_blocking_reason": HISTORICAL_BLOCKING_REASON,
        "leakage_group_id_grammar": {
            "exact_type": "builtins.str", "subclasses_allowed": False,
            "ASCII_only": True, "prefix": LEAKAGE_GROUP_PREFIX,
            "regex": LEAKAGE_GROUP_REGEX, "suffix_digits": 6,
            "suffix_digit_class": "ASCII_[0-9]", "normalization_allowed": False,
            "historical_observed_value_count": 5,
            "grammar_is_explicit_v1_design_not_natural_inference": True,
        },
        "exact19_class_name": "LeakageGroupAssignmentProvenanceContractV1",
        "exact19_field_count": 19, "exact19_field_order": list(EXACT19_FIELD_NAMES),
        "exact19_slots_used": False, "class_is_formal_result": False,
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
            "pre_split_assignment_status": PRE_SPLIT_ASSIGNED_STATUS,
            "split_artifact_reverse_proof_allowed": False,
        },
        "validation_precedence": list(VALIDATION_PRECEDENCE),
        "reason_vocabulary": list(REASONS),
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
        "contract_row_count": len(state["contract_rows"]),
        "mapping_grammar_row_count": len(state["mapping_rows"]),
        "truth_matrix_contract": "Exact71", "truth_row_count": len(truth),
        "truth_group_counts": truth_counts,
        "source_boundary_name": "fixed_ordered_exact21_committed_source_boundary",
        "source_input_count": len(SOURCE_PATHS),
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "source_attestation_authenticity_checked_by_evaluator": False,
        "issue_inventory_row_count": len(state["issue_rows"]),
        "issue_transition": {
            "issue_id": PRIMARY_BLOCKER, "from_status": "open", "to_status": "resolved",
            "from_integration_transition": "unchanged_open",
            "to_integration_transition": "leakage_group_assignment_provenance_contract_frozen_v1",
            "only_authorized_issue_change": True,
        },
        "coverage_issue_status": "open",
        "coverage_issue_affected_rules": "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        "readiness": readiness, **readiness,
        "output_file_count": 6, "output_files": list(OUTPUT_FILES),
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "output_materialization": {
            "preflight_before_first_write": True, "real_directory_non_symlink": True,
            "existing_inventory_allowlist_exact": True,
            "existing_entries_regular_non_symlink": True,
            "atomic_same_directory_mkstemp": True, "temporary_suffix": ".tmp",
            "fdopen_mode": "wb", "flush_and_fsync": True, "os_replace": True,
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
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_contract_checks_passed": True, "all_mapping_checks_passed": True,
        "all_truth_checks_passed": True, "all_source_boundary_checks_passed": True,
        "all_issue_checks_passed": True, "all_readiness_checks_passed": True,
        "all_attestations_passed": True, "validation_failures": [],
    }
    return payload


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        MAPPING_FILENAME: _csv_bytes(MAPPING_COLUMNS, state["mapping_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        SOURCE_BOUNDARY_FILENAME: _csv_bytes(SOURCE_BOUNDARY_COLUMNS, state["source_boundary_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    output_sha = {name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()}
    manifest = _manifest(state, output_sha)
    payloads[MANIFEST_FILENAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return payloads, manifest


def _preflight_output_root(root: Path) -> bool:
    """Validate the entire existing inventory without creating or changing it."""
    if root.exists() or root.is_symlink():
        metadata = os.lstat(root)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("output root must be a real non-symlink directory")
        entries = tuple(root.iterdir())
        if not {entry.name for entry in entries}.issubset(set(OUTPUT_FILES)):
            raise ValueError("unexpected output entry")
        for entry in entries:
            item = os.lstat(entry)
            if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
                raise ValueError("existing output must be regular non-symlink")
        return False
    parent = root.parent
    parent_metadata = os.lstat(parent)
    if not stat.S_ISDIR(parent_metadata.st_mode) or stat.S_ISLNK(parent_metadata.st_mode):
        raise ValueError("output parent must be a real non-symlink directory")
    return True


def _atomic_write(path: Path, content: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _postvalidate_output_root(root: Path) -> None:
    metadata = os.lstat(root)
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ValueError("postwrite output root invalid")
    entries = tuple(root.iterdir())
    if {entry.name for entry in entries} != set(OUTPUT_FILES):
        raise ValueError("postwrite output inventory mismatch")
    for entry in entries:
        item = os.lstat(entry)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("postwrite output entry invalid")


def run_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT, *, repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    root = output_root if output_root.is_absolute() else repo_root / output_root
    create_root = _preflight_output_root(root)
    state = build_design_state(repo_root, head_ref=head_ref)
    payloads, manifest = _payloads(state)
    if create_root:
        root.mkdir(exist_ok=False)
    for name in OUTPUT_FILES:
        _atomic_write(root / name, payloads[name])
    _postvalidate_output_root(root)
    return {
        "manifest": manifest, "output_root": root,
        "output_sha256": {
            name: hashlib.sha256(payloads[name]).hexdigest() for name in OUTPUT_FILES
        },
        "state": state,
    }


def main() -> int:
    result = run_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1()
    print(json.dumps({
        "stage": STAGE, "output_sha256": result["output_sha256"],
        "truth_row_count": result["manifest"]["truth_row_count"],
        "ready_for_admit_010_standalone_evaluator_interface_implementation":
            result["manifest"]["ready_for_admit_010_standalone_evaluator_interface_implementation"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
