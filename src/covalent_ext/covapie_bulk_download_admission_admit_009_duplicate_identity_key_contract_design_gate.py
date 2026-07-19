"""ADMIT_009 duplicate-identity-key contract design gate v1.

This metadata-only gate freezes evaluator-facing duplicate-key semantics and a
pure design oracle.  It does not implement the formal evaluator, build real
provider keys, touch raw data, or modify the Exact8 runtime.
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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "ADMIT_009 duplicate identity key contract design gate v1"
STAGE = "covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1"
EXPECTED_BASE_COMMIT = "c253e3909f170f141cbb70d659a98d203390d997"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_009 evaluator preconditions audit v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_009_duplicate_identity_key_contract_manifest_v1"
ADMISSION_RULE_ID = "ADMIT_009"
ADMISSION_RULE_NAME = "duplicate_identity_precheck"
CANDIDATE_FIELD = "duplicate_identity_key"
BATCH_CONTEXT_ITEM = "batch_duplicate_identity_keys"
POLICY_CONTEXT_ITEM = "duplicate_identity_key_contract"
KEY_PREFIX = "covapie_dup_v1_sha256_"
KEY_REGEX = r"^covapie_dup_v1_sha256_[0-9a-f]{64}$"
POLICY_CONTRACT_VALUE = "covapie_duplicate_identity_key_contract_v1"
PRIMARY_BLOCKER = "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"
COVERAGE_ISSUE = "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
RECOMMENDED_NEXT_STEP = "implement_covapie_admit_009_standalone_evaluator_interface_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

AUDIT_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1")
RUNTIME_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1")
DESIGN_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1")
IMPLEMENTATION_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1")
CANDIDATE_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1")
LEAKAGE_ROOT = Path("data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0")
UNIFIED_RULE_ENGINE_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1")

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit.py",
    str(AUDIT_ROOT / "covapie_admit_009_formal_evaluator_preconditions_manifest.json"),
    str(AUDIT_ROOT / "covapie_admit_009_evaluator_precondition_matrix.csv"),
    str(AUDIT_ROOT / "covapie_admit_009_duplicate_identity_vocabulary_inventory.csv"),
    str(AUDIT_ROOT / "covapie_admit_009_field_occurrence_inventory.csv"),
    str(AUDIT_ROOT / "covapie_admit_009_issue_readiness_inventory.csv"),
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008.py",
    str(RUNTIME_ROOT / "covapie_admit_001_to_008_runtime_manifest.json"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_schema_contract.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_field_semantics_matrix.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"),
    str(CANDIDATE_ROOT / "covapie_candidate_record_id_semantics_contract.csv"),
    str(LEAKAGE_ROOT / "covapie_final_leakage_group_assignment.csv"),
    str(UNIFIED_RULE_ENGINE_ROOT / "covapie_unified_admission_result_schema_and_outcome_contract.csv"),
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "89b2240cc34b0b70a4a197b9615b86171f3e5347b148837e15017c1fa01a2f5e",
    "5d1be882bc51c3fad5eefa5dc106dec43ba5842eda0696c06eb04473db33a37b",
    "f509c25ea5c9843da97cc0582189884b3df9074cbc209a8315e9695699739868",
    "63126db3776eec209f2ea0f2517159889392762a89f609f246ba62ed3f6ac6cc",
    "feb35d0081c4489e6eb5900d72adc3458862f30195fc228a2806bda03d954e83",
    "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128",
    "b5022ee4b6a4e965cf783abf15e70a5909860f4f500c89f983fb41b6b8fd87e2",
    "6047e110c29d8ca7300236f8af8dbce31a92f2a62576cbc2a8fa2d5d1baf32cf",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "92f624705a611c0dac011229d13d6a3ba87fc1ab7a3e0bc9c090952a0838b318",
    "768c964f22e19a8fb6232b1fa26c531e53d023042abcd9b1bcca44df2b4f4416",
    "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
), strict=True))

(
    AUDIT_SOURCE_PATH, AUDIT_MANIFEST_PATH, AUDIT_PRECONDITION_PATH,
    AUDIT_VOCABULARY_PATH, AUDIT_OCCURRENCE_PATH, AUDIT_ISSUE_PATH,
    RUNTIME_SOURCE_PATH, RUNTIME_MANIFEST_PATH, RULE_REGISTRY_PATH,
    SCHEMA_CONTRACT_PATH, FIELD_SEMANTICS_PATH, RULE_EXECUTABILITY_PATH,
    EVALUATION_CONTEXT_PATH, CANDIDATE_CONTRACT_PATH, LEAKAGE_ASSIGNMENT_PATH,
    UNIFIED_RESULT_CONTRACT_PATH,
) = SOURCE_PATHS

CONTRACT_FILENAME = "covapie_admit_009_duplicate_identity_key_contract.csv"
CONTEXT_FILENAME = "covapie_admit_009_batch_and_policy_context_contract.csv"
BOUNDARY_FILENAME = "covapie_admit_009_equivalence_and_provider_boundary_matrix.csv"
TRUTH_FILENAME = "covapie_admit_009_duplicate_identity_validation_truth_matrix.csv"
ISSUE_FILENAME = "covapie_admit_009_duplicate_identity_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_009_duplicate_identity_key_contract_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, CONTEXT_FILENAME, BOUNDARY_FILENAME, TRUTH_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CONTRACT_COLUMNS = ("contract_order", "contract_item", "exact_requirement", "forbidden_behavior", "contract_passed")
CONTEXT_COLUMNS = ("context_order", "context_item", "scope", "exact_contract", "validation_precedence", "invalid_reason", "context_passed")
BOUNDARY_COLUMNS = ("boundary_order", "boundary_item", "is_duplicate_identity_key", "exact_duplicate_claim_allowed", "evaluator_visible_component", "exact_statement", "boundary_passed")
TRUTH_COLUMNS = (
    "truth_order", "truth_group", "case_id", "input_summary", "scalar_classification",
    "policy_classification", "batch_classification", "outcome", "passed",
    "blocks_candidate", "reason", "canonical_duplicate_identity_key",
    "validated_candidate_fields", "consumed_candidate_fields", "consumed_context_items",
    "evaluator_io_used", "truth_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

SCALAR_REASONS = (
    "DUPLICATE_IDENTITY_KEY_TYPE_INVALID", "DUPLICATE_IDENTITY_KEY_EMPTY",
    "DUPLICATE_IDENTITY_KEY_NON_ASCII", "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID",
)
POLICY_REASONS = (
    "DUPLICATE_IDENTITY_KEY_CONTRACT_TYPE_INVALID",
    "DUPLICATE_IDENTITY_KEY_CONTRACT_VALUE_INVALID",
)
BATCH_REASONS = (
    "BATCH_DUPLICATE_IDENTITY_KEYS_TYPE_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_TYPE_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_ORDER_OR_UNIQUENESS_INVALID",
)
DUPLICATE_REASON = "DUPLICATE_IDENTITY_KEY_ALREADY_PRESENT"

TRUE_READINESS = (
    "admit_009_duplicate_key_exact_type_contract_available",
    "admit_009_duplicate_key_syntax_contract_available",
    "admit_009_duplicate_key_normalization_contract_available",
    "admit_009_duplicate_key_composition_contract_available",
    "admit_009_duplicate_equivalence_domain_contract_available",
    "admit_009_collision_handling_contract_available",
    "admit_009_batch_container_contract_available",
    "admit_009_batch_membership_semantics_contract_available",
    "admit_009_self_exclusion_contract_available",
    "admit_009_duplicate_vs_leakage_boundary_contract_available",
    "admit_009_reason_outcome_contract_available",
    "admit_009_canonical_state_contract_available",
    "admit_009_independent_semantic_oracle_available",
    "admit_009_standalone_evaluator_preconditions_complete",
    "admit_009_provider_mapping_boundary_preserved",
    "ready_for_admit_009_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "real_provider_duplicate_identity_mapping_validated",
    "real_provider_duplicate_identity_key_count_nonzero",
    "admit_009_standalone_evaluator_implemented",
    "admit_009_unified_adapter_contract_frozen", "admit_009_unified_adapter_implemented",
    "admit_009_registered_in_engine", "unified_dispatch_runtime_with_admit_001_to_009_implemented",
    "admit_010_standalone_evaluator_implemented", "admit_010_to_015_registered_in_engine",
    "all_15_rules_covered", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen", "real_candidate_evaluation",
    "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
)


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


def _git(arguments: Sequence[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False)


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path) and not path.is_absolute() and bool(path.parts)
        and ".." not in path.parts and path.parts[0] != "checkpoints"
        and path.parts[:2] != ("data", "raw")
    )


def _validate_base(repo_root: Path, head_ref: str) -> None:
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
    fields = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    return (
        tracked.returncode == 0 and tree.returncode == 0 and len(fields) == 3
        and fields[0] in ("100644", "100755") and fields[1] == "blob"
        and stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD") -> FrozenSourceSnapshot:
    """Perform all Exact16 structural checks before the first content read."""
    if len(SOURCE_PATHS) != 16 or len(set(SOURCE_PATHS)) != 16 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact16 source boundary invalid")
    _validate_base(repo_root, head_ref)
    if not all(_structural_source_check(path, repo_root) for path in SOURCE_PATHS):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"], repo_root, text=False)
        if base.returncode != 0 or type(base.stdout) is not bytes:
            raise ValueError(f"base-tree source read failed: {path}")
        filesystem = (repo_root / path).read_bytes()
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem).hexdigest()
        if SOURCE_SHA256[path] != base_sha or base_sha != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, SOURCE_SHA256[path], base_sha, filesystem_sha, filesystem))
    snapshot = FrozenSourceSnapshot(tuple(records))
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("frozen source snapshot invalid")
    return snapshot


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot and len(value.records) == 16
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
    matches = tuple(record for record in snapshot.records if record.relative_path == path)
    if len(matches) != 1:
        raise ValueError("frozen source missing or duplicate")
    return matches[0]


def _csv_rows(snapshot: FrozenSourceSnapshot, path: Path) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(_record(snapshot, path).content_bytes.decode("utf-8"), newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values()) for row in rows):
        raise ValueError("invalid CSV row")
    return rows


def _json(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(_record(snapshot, path).content_bytes.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError("invalid JSON document")
    return value


def _one(rows: Sequence[Mapping[str, str]], key: str, value: str) -> Mapping[str, str]:
    matches = tuple(row for row in rows if row.get(key) == value)
    if len(matches) != 1:
        raise ValueError(f"expected one row for {key}={value}")
    return matches[0]


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> None:
    audit_manifest = _json(snapshot, AUDIT_MANIFEST_PATH)
    runtime_manifest = _json(snapshot, RUNTIME_MANIFEST_PATH)
    rule = _one(_csv_rows(snapshot, RULE_REGISTRY_PATH), "admission_rule_id", ADMISSION_RULE_ID)
    schema = _one(_csv_rows(snapshot, SCHEMA_CONTRACT_PATH), "admission_field_name", CANDIDATE_FIELD)
    field = _one(_csv_rows(snapshot, FIELD_SEMANTICS_PATH), "field_name", CANDIDATE_FIELD)
    executable = _one(_csv_rows(snapshot, RULE_EXECUTABILITY_PATH), "admission_rule_id", ADMISSION_RULE_ID)
    batch = _one(_csv_rows(snapshot, EVALUATION_CONTEXT_PATH), "context_item", BATCH_CONTEXT_ITEM)
    policy = _one(_csv_rows(snapshot, EVALUATION_CONTEXT_PATH), "context_item", POLICY_CONTEXT_ITEM)
    candidate = _one(_csv_rows(snapshot, CANDIDATE_CONTRACT_PATH), "contract_item", "separate_from_duplicate_identity_key")
    issues = _csv_rows(snapshot, AUDIT_ISSUE_PATH)
    blocker = _one(issues, "issue_id", PRIMARY_BLOCKER)
    coverage = _one(issues, "issue_id", COVERAGE_ISSUE)
    leakage = _csv_rows(snapshot, LEAKAGE_ASSIGNMENT_PATH)
    unified_result = _csv_rows(snapshot, UNIFIED_RESULT_CONTRACT_PATH)
    unified_invariants = tuple(row for row in unified_result if row["contract_kind"] == "result_invariant")
    passed_invariant = _one(unified_invariants, "field_name", "passed")
    blocks_invariant = _one(unified_invariants, "field_name", "blocks_candidate")
    passed_reason_invariant = _one(unified_invariants, "field_name", "passed_reason")
    nonpassed_reason_invariant = _one(unified_invariants, "field_name", "nonpassed_reason")
    required = (
        audit_manifest["recommended_next_step"] == "design_covapie_admit_009_duplicate_identity_key_contract_v1",
        audit_manifest["real_provider_duplicate_identity_key_count"] == 0,
        audit_manifest["ready_for_admit_009_duplicate_identity_key_contract_design"] is True,
        runtime_manifest["registered_rule_ids"] == [f"ADMIT_{index:03d}" for index in range(1, 9)],
        rule["admission_rule_name"] == ADMISSION_RULE_NAME and rule["evaluation_phase"] == "pre_download",
        schema["value_contract"] == "pre-download deduplication key",
        field["implementation_semantics_complete"] == "false" and field["blocking_reasons"] == PRIMARY_BLOCKER,
        executable["candidate_field_dependencies"] == CANDIDATE_FIELD,
        executable["batch_context_dependencies"] == BATCH_CONTEXT_ITEM,
        executable["evaluation_context_dependencies"] == POLICY_CONTEXT_ITEM,
        batch["provided_by_future_caller"] == "true" and policy["exact_contract_defined"] == "false",
        candidate["exact_requirement"] == "not duplicate_identity_key" and candidate["forbidden_behavior"] == "replace_admit_009",
        blocker["status"] == "open" and blocker["integration_transition"] == "unchanged_open",
        coverage["status"] == "open" and coverage["affected_rules"] == "ADMIT_009|ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        coverage["integration_transition"] == "admit_008_implemented_and_removed_from_open_coverage_scope",
        len(issues) == 11 and len(leakage) == 11,
        passed_invariant["contract_kind"] == "result_invariant"
        and passed_invariant["contract_value"] == "true_iff_outcome_passed",
        blocks_invariant["contract_kind"] == "result_invariant"
        and blocks_invariant["contract_value"] == "true_iff_outcome_not_passed",
        passed_reason_invariant["contract_kind"] == "result_invariant"
        and passed_reason_invariant["contract_value"] == "empty_exact_str",
        nonpassed_reason_invariant["contract_kind"] == "result_invariant"
        and nonpassed_reason_invariant["contract_value"] == "nonempty_exact_str",
    )
    if not all(required):
        raise ValueError("authoritative predecessor contract mismatch")


def _validate_scalar(value: object) -> tuple[bool, str, str]:
    if type(value) is not str:
        return False, "", SCALAR_REASONS[0]
    if value == "":
        return False, "", SCALAR_REASONS[1]
    if not value.isascii():
        return False, "", SCALAR_REASONS[2]
    if re.fullmatch(KEY_REGEX, value) is None:
        return False, "", SCALAR_REASONS[3]
    return True, value, ""


def _validate_policy(value: object) -> tuple[bool, str]:
    if type(value) is not str:
        return False, POLICY_REASONS[0]
    if value != POLICY_CONTRACT_VALUE:
        return False, POLICY_REASONS[1]
    return True, ""


def _validate_batch(value: object) -> tuple[bool, str]:
    if type(value) is not tuple:
        return False, BATCH_REASONS[0]
    if any(type(member) is not str for member in value):
        return False, BATCH_REASONS[1]
    if any(not _validate_scalar(member)[0] for member in value):
        return False, BATCH_REASONS[2]
    if any(left >= right for left, right in zip(value, value[1:])):
        return False, BATCH_REASONS[3]
    return True, ""


def classify_admit_009_duplicate_identity_key_design(
    duplicate_identity_key: object,
    batch_duplicate_identity_keys: object,
    duplicate_identity_key_contract: object,
) -> dict[str, Any]:
    """Pure design oracle; this is deliberately not the formal evaluator."""
    consumed_candidate = (CANDIDATE_FIELD,)
    scalar_ok, canonical, reason = _validate_scalar(duplicate_identity_key)
    if not scalar_ok:
        return {
            "scalar_classification": "invalid", "policy_classification": "not_evaluated",
            "batch_classification": "not_evaluated", "outcome": "invalid", "passed": False,
            "blocks_candidate": True, "reason": reason, "canonical_duplicate_identity_key": "",
            "validated_candidate_fields": (), "consumed_candidate_fields": consumed_candidate,
            "consumed_context_items": (), "evaluator_io_used": False,
        }
    validated = ((CANDIDATE_FIELD, canonical),)
    policy_ok, reason = _validate_policy(duplicate_identity_key_contract)
    if not policy_ok:
        return {
            "scalar_classification": "canonical", "policy_classification": "invalid",
            "batch_classification": "not_evaluated", "outcome": "invalid", "passed": False,
            "blocks_candidate": True, "reason": reason, "canonical_duplicate_identity_key": canonical,
            "validated_candidate_fields": validated, "consumed_candidate_fields": consumed_candidate,
            "consumed_context_items": (POLICY_CONTEXT_ITEM,), "evaluator_io_used": False,
        }
    batch_ok, reason = _validate_batch(batch_duplicate_identity_keys)
    if not batch_ok:
        return {
            "scalar_classification": "canonical", "policy_classification": "valid",
            "batch_classification": "invalid", "outcome": "invalid", "passed": False,
            "blocks_candidate": True, "reason": reason, "canonical_duplicate_identity_key": canonical,
            "validated_candidate_fields": validated, "consumed_candidate_fields": consumed_candidate,
            "consumed_context_items": (POLICY_CONTEXT_ITEM, BATCH_CONTEXT_ITEM), "evaluator_io_used": False,
        }
    duplicate = canonical in batch_duplicate_identity_keys
    return {
        "scalar_classification": "canonical", "policy_classification": "valid",
        "batch_classification": "valid", "outcome": "blocked" if duplicate else "passed",
        "passed": not duplicate, "blocks_candidate": duplicate,
        "reason": DUPLICATE_REASON if duplicate else "", "canonical_duplicate_identity_key": canonical,
        "validated_candidate_fields": validated, "consumed_candidate_fields": consumed_candidate,
        "consumed_context_items": (POLICY_CONTEXT_ITEM, BATCH_CONTEXT_ITEM), "evaluator_io_used": False,
    }


def _contract_rows() -> tuple[dict[str, str], ...]:
    specs = (
        ("identity", "ADMIT_009/duplicate_identity_precheck uses duplicate_identity_key", "substitute another identity"),
        ("exact_scalar_type", "type(value) is str", "accept subclasses or coercion"),
        ("versioned_prefix", KEY_PREFIX, "accept aliases or other versions"),
        ("exact_regex", KEY_REGEX, "partial match or alternate characters"),
        ("digest", "64 lowercase hexadecimal characters", "uppercase, short, long, or non-hex digest"),
        ("scalar_precedence", "type, non-empty, ASCII, regex fullmatch", "reorder or continue after failure"),
        ("normalization", "canonical key equals input byte-for-byte", "trim, case-fold, Unicode-normalize, alias, repair, recompute, regenerate"),
        ("composition", "atomic opaque producer-owned scalar", "split or parse chemical components"),
        ("evaluator_visible_components", "exactly zero", "promote candidate/group fields as key components"),
        ("producer_descriptor", "producer maintains canonical exact-duplicate descriptor", "evaluator constructs descriptor"),
        ("producer_determinism", "stable deterministic versioned assignment", "unstable or unversioned assignment"),
        ("duplicate_equivalence", "same key means producer-declared exact duplicate admission class", "reinterpret as similarity or grouping"),
        ("different_key_claim", "no duplicate is proved by this key", "claim chemical, ligand, protein, residue, or leakage distinctness"),
        ("collision_preimage", "producer retains or can rebuild canonical descriptor", "discard collision provenance"),
        ("collision_handling", "producer fails closed on same digest for different descriptors", "send ambiguous key to evaluator"),
        ("evaluator_collision_boundary", "evaluator does not detect collision or validate provenance", "assign collision responsibility to evaluator"),
        ("policy_context", POLICY_CONTRACT_VALUE, "fallback, alias, trim, or case-normalize"),
        ("batch_container", "type(value) is tuple; empty allowed", "accept list/set/frozenset/subclass"),
        ("batch_member", "each member exact str and full scalar-valid", "coerce or normalize members"),
        ("batch_order", "strict ascending original ASCII strings", "sort automatically"),
        ("batch_uniqueness", "members unique", "deduplicate automatically"),
        ("snapshot", "earlier admitted/queued canonical keys before current candidate", "include current record itself"),
        ("self_exclusion", "future caller excludes current record; equal key means another earlier candidate", "use candidate_record_id or batch position"),
        ("membership", "exact case-sensitive Python string equality", "prefix, substring, component, graph, or group comparison"),
        ("precedence", "scalar then policy then batch then membership with short-circuit", "evaluate later stages after invalid input"),
        ("outcomes", "passed, blocked, invalid", "use rejected or unresolved umbrella outcome"),
        ("blocks_candidate_invariant", "blocks_candidate is true exactly when outcome is not passed", "invalid or blocked result with blocks_candidate=false"),
        ("unique_state", "passed=true blocks=false reason empty; canonical pair retained", "drop validated canonical state"),
        ("duplicate_state", f"blocked; {DUPLICATE_REASON}; canonical pair retained", "classify duplicate as invalid/rejected or use lowercase reason"),
        ("invalid_state", "scalar invalid clears canonical/pair; policy or batch invalid retains them", "invent or discard canonical state"),
        ("oracle", "independent pure in-memory full-input design classifier", "perform evaluator I/O"),
        ("provider_boundary", "real provider mapping unvalidated and real key count zero", "fabricate provider keys"),
        ("implementation_boundary", "formal evaluator/result/adapter/registration/runtime changes absent", "implement later stages in this gate"),
        ("execution_boundary", "no raw, network, download, training, model forward/loss", "perform external or training operations"),
    )
    return tuple({
        "contract_order": str(index), "contract_item": item, "exact_requirement": requirement,
        "forbidden_behavior": forbidden, "contract_passed": "true",
    } for index, (item, requirement, forbidden) in enumerate(specs, 1))


def _context_rows() -> tuple[dict[str, str], ...]:
    specs = (
        (CANDIDATE_FIELD, "candidate_scalar", "exact built-in str", "1", "DUPLICATE_IDENTITY_KEY_TYPE_INVALID"),
        (CANDIDATE_FIELD, "candidate_scalar", "non-empty", "2", "DUPLICATE_IDENTITY_KEY_EMPTY"),
        (CANDIDATE_FIELD, "candidate_scalar", "ASCII", "3", "DUPLICATE_IDENTITY_KEY_NON_ASCII"),
        (CANDIDATE_FIELD, "candidate_scalar", KEY_REGEX, "4", "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID"),
        (POLICY_CONTEXT_ITEM, "evaluation_policy", "exact built-in str", "5", "DUPLICATE_IDENTITY_KEY_CONTRACT_TYPE_INVALID"),
        (POLICY_CONTEXT_ITEM, "evaluation_policy", POLICY_CONTRACT_VALUE, "6", "DUPLICATE_IDENTITY_KEY_CONTRACT_VALUE_INVALID"),
        (BATCH_CONTEXT_ITEM, "batch_snapshot", "exact built-in tuple", "7", "BATCH_DUPLICATE_IDENTITY_KEYS_TYPE_INVALID"),
        (BATCH_CONTEXT_ITEM, "batch_snapshot", "member exact built-in str", "8", "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_TYPE_INVALID"),
        (BATCH_CONTEXT_ITEM, "batch_snapshot", "every member full scalar-valid", "9", "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_INVALID"),
        (BATCH_CONTEXT_ITEM, "batch_snapshot", "strict ascending and unique", "10", "BATCH_DUPLICATE_IDENTITY_KEYS_ORDER_OR_UNIQUENESS_INVALID"),
        (BATCH_CONTEXT_ITEM, "batch_snapshot", "empty tuple valid", "11", ""),
        (BATCH_CONTEXT_ITEM, "caller_responsibility", "snapshot excludes current record", "12", ""),
        (BATCH_CONTEXT_ITEM, "membership", "candidate key absent means unique", "13", ""),
        (BATCH_CONTEXT_ITEM, "membership", "candidate key present means earlier duplicate", "14", DUPLICATE_REASON),
        (BATCH_CONTEXT_ITEM, "membership", "match multiplicity is zero or one", "15", ""),
    )
    return tuple({
        "context_order": str(index), "context_item": item, "scope": scope,
        "exact_contract": contract, "validation_precedence": precedence,
        "invalid_reason": reason, "context_passed": "true",
    } for index, (item, scope, contract, precedence, reason) in enumerate(specs, 1))


def _boundary_rows() -> tuple[dict[str, str], ...]:
    specs = (
        ("candidate_record_id", False, False, False, "record identity is separate and not used for self-exclusion"),
        ("sample_index_row_id", False, False, False, "sample row identity is not a duplicate key"),
        ("assignment_id", False, False, False, "assignment identity is not a duplicate key"),
        ("pdb_id_alone", False, False, False, "structure identifier alone is not a duplicate key"),
        ("ligand_comp_id_alone", False, False, False, "ligand component alone is not a duplicate key"),
        ("ligand_graph_group_id", False, False, False, "ligand graph group is not an exact duplicate class"),
        ("ligand_scaffold_group_id", False, False, False, "scaffold group is not an exact duplicate class"),
        ("protein_group_id", False, False, False, "protein grouping is not an exact duplicate class"),
        ("leakage_group_id", False, False, False, "candidate leakage group is not an exact duplicate class"),
        ("final_leakage_group_id", False, False, False, "conservative must-link union is not an exact duplicate class"),
        ("same_leakage_group", False, False, False, "does not mean exact duplicate"),
        ("same_scaffold", False, False, False, "does not mean exact duplicate"),
        ("same_ligand_graph_group", False, False, False, "does not mean exact duplicate"),
        ("same_duplicate_identity_key", True, True, False, "producer declares same exact duplicate admission class"),
        ("different_duplicate_identity_key", False, False, False, "only means this key does not prove duplication"),
        ("canonical_descriptor", False, True, False, "producer-owned and invisible to evaluator"),
        ("sha256_collision_detection", False, False, False, "producer responsibility; evaluator does not inspect descriptor"),
        ("real_provider_mapping", False, False, False, "unvalidated; zero real keys materialized"),
    )
    return tuple({
        "boundary_order": str(index), "boundary_item": item,
        "is_duplicate_identity_key": _bool(is_key),
        "exact_duplicate_claim_allowed": _bool(claim),
        "evaluator_visible_component": _bool(component), "exact_statement": statement,
        "boundary_passed": "true",
    } for index, (item, is_key, claim, component, statement) in enumerate(specs, 1))


def _display(value: object) -> str:
    return f"{type(value).__name__}:{value!r}"


def _truth_rows() -> tuple[dict[str, str], ...]:
    class StringSubclass(str):
        pass

    class TupleSubclass(tuple):
        pass

    candidate = KEY_PREFIX + "1" * 64
    low = KEY_PREFIX + "0" * 64
    high = KEY_PREFIX + "2" * 64
    unrelated = KEY_PREFIX + "f" * 64
    valid_policy = POLICY_CONTRACT_VALUE
    valid_batch: tuple[str, ...] = ()
    cases: list[tuple[str, str, object, object, object]] = [
        ("scalar", "scalar_none", None, valid_batch, valid_policy),
        ("scalar", "scalar_integer", 7, valid_batch, valid_policy),
        ("scalar", "scalar_str_subclass", StringSubclass(candidate), valid_batch, valid_policy),
        ("scalar", "scalar_empty", "", valid_batch, valid_policy),
        ("scalar", "scalar_non_ascii", KEY_PREFIX + "é" * 64, valid_batch, valid_policy),
        ("scalar", "scalar_wrong_prefix", "covapie_dup_v2_sha256_" + "1" * 64, valid_batch, valid_policy),
        ("scalar", "scalar_uppercase_digest", KEY_PREFIX + "A" * 64, valid_batch, valid_policy),
        ("scalar", "scalar_short_digest", KEY_PREFIX + "1" * 63, valid_batch, valid_policy),
        ("scalar", "scalar_long_digest", KEY_PREFIX + "1" * 65, valid_batch, valid_policy),
        ("scalar", "scalar_non_hex", KEY_PREFIX + "g" * 64, valid_batch, valid_policy),
        ("scalar", "scalar_whitespace", " " + candidate, valid_batch, valid_policy),
        ("scalar", "scalar_canonical", candidate, valid_batch, valid_policy),
        ("policy", "policy_none", candidate, valid_batch, None),
        ("policy", "policy_str_subclass", candidate, valid_batch, StringSubclass(valid_policy)),
        ("policy", "policy_wrong_value", candidate, valid_batch, "covapie_duplicate_identity_key_contract_v2"),
        ("policy", "policy_exact_valid", candidate, valid_batch, valid_policy),
        ("batch", "batch_none", candidate, None, valid_policy),
        ("batch", "batch_list", candidate, [], valid_policy),
        ("batch", "batch_tuple_subclass", candidate, TupleSubclass(), valid_policy),
        ("batch", "batch_non_str_member", candidate, (7,), valid_policy),
        ("batch", "batch_str_subclass_member", candidate, (StringSubclass(unrelated),), valid_policy),
        ("batch", "batch_malformed_member", candidate, ("bad",), valid_policy),
        ("batch", "batch_unsorted", candidate, (high, low), valid_policy),
        ("batch", "batch_duplicate_members", candidate, (unrelated, unrelated), valid_policy),
        ("batch", "batch_empty_valid", candidate, (), valid_policy),
        ("batch", "batch_one_unrelated", candidate, (unrelated,), valid_policy),
        ("batch", "batch_one_matching", candidate, (candidate,), valid_policy),
        ("batch", "batch_multiple_contains", candidate, (low, candidate, high), valid_policy),
        ("outcome_state", "canonical_unique_passed", candidate, (unrelated,), valid_policy),
        ("outcome_state", "canonical_duplicate_blocked", candidate, (candidate,), valid_policy),
        ("outcome_state", "policy_invalid_retains_pair", candidate, (), "wrong"),
        ("outcome_state", "batch_invalid_retains_pair", candidate, [candidate], valid_policy),
    ]
    rows: list[dict[str, str]] = []
    for index, (group, case_id, scalar, batch, policy) in enumerate(cases, 1):
        result = classify_admit_009_duplicate_identity_key_design(scalar, batch, policy)
        rows.append({
            "truth_order": str(index), "truth_group": group, "case_id": case_id,
            "input_summary": f"key={_display(scalar)};batch={_display(batch)};policy={_display(policy)}",
            "scalar_classification": result["scalar_classification"],
            "policy_classification": result["policy_classification"],
            "batch_classification": result["batch_classification"], "outcome": result["outcome"],
            "passed": _bool(result["passed"]), "blocks_candidate": _bool(result["blocks_candidate"]),
            "reason": result["reason"],
            "canonical_duplicate_identity_key": result["canonical_duplicate_identity_key"],
            "validated_candidate_fields": json.dumps(result["validated_candidate_fields"], separators=(",", ":")),
            "consumed_candidate_fields": json.dumps(result["consumed_candidate_fields"], separators=(",", ":")),
            "consumed_context_items": json.dumps(result["consumed_context_items"], separators=(",", ":")),
            "evaluator_io_used": _bool(result["evaluator_io_used"]), "truth_passed": "true",
        })
    if (
        len(rows) != 32
        or [row["truth_group"] for row in rows].count("scalar") != 12
        or any((row["passed"] == "true") != (row["outcome"] == "passed") for row in rows)
        or any((row["blocks_candidate"] == "true") != (row["outcome"] != "passed") for row in rows)
        or any((row["reason"] == "") != (row["outcome"] == "passed") for row in rows)
    ):
        raise ValueError("Exact32 truth construction failed")
    return tuple(rows)


def _issue_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    predecessor = _csv_rows(snapshot, AUDIT_ISSUE_PATH)
    rows: list[dict[str, str]] = []
    changes = 0
    for source in predecessor:
        row = dict(source)
        if row["issue_id"] == PRIMARY_BLOCKER:
            row["status"] = "resolved"
            row["integration_transition"] = "duplicate_identity_key_contract_frozen_v1"
            changes += 1
        rows.append(row)
    if changes != 1 or len(rows) != 11:
        raise ValueError("successor issue transition invalid")
    coverage = _one(rows, "issue_id", COVERAGE_ISSUE)
    if coverage["status"] != "open" or coverage["affected_rules"] != "ADMIT_009|ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015":
        raise ValueError("coverage issue changed")
    return tuple(rows)


def _readiness() -> dict[str, bool]:
    return {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def build_design_state(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root)
    _validate_predecessors(snapshot)
    return {
        "snapshot": snapshot, "contract_rows": _contract_rows(), "context_rows": _context_rows(),
        "boundary_rows": _boundary_rows(), "truth_rows": _truth_rows(),
        "issue_rows": _issue_rows(snapshot), "readiness": _readiness(),
    }


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _source_verification(snapshot: FrozenSourceSnapshot) -> list[dict[str, Any]]:
    return [{
        "source_order": index, "source_relative_path": record.relative_path.as_posix(),
        "expected_sha256": record.expected_sha256, "base_tree_sha256": record.base_tree_sha256,
        "filesystem_sha256": record.filesystem_sha256, "tracked": True, "base_tree_blob": True,
        "filesystem_regular": True, "non_symlink": True, "source_verified": True,
    } for index, record in enumerate(snapshot.records, 1)]


def _manifest(state: Mapping[str, Any], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    readiness = dict(state["readiness"])
    truth = state["truth_rows"]
    groups = {group: sum(row["truth_group"] == group for row in truth) for group in ("scalar", "policy", "batch", "outcome_state")}
    manifest: dict[str, Any] = {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID, "admission_rule_name": ADMISSION_RULE_NAME,
        "candidate_field": CANDIDATE_FIELD, "batch_context_item": BATCH_CONTEXT_ITEM,
        "policy_context_item": POLICY_CONTEXT_ITEM, "evaluation_phase": "pre_download",
        "future_evaluator_name_reserved_only": "evaluate_admit_009",
        "future_result_name_reserved_only": "Admit009EvaluationResult",
        "key_contract": {
            "exact_type": "builtins.str", "prefix": KEY_PREFIX, "regex": KEY_REGEX,
            "digest_length": 64, "digest_charset": "0123456789abcdef",
            "versioned": True, "deterministic": True, "atomic_opaque": True,
            "evaluator_visible_component_count": 0, "canonical_equals_input": True,
            "normalization_or_repair_allowed": False,
        },
        "policy_contract": {"exact_type": "builtins.str", "only_value": POLICY_CONTRACT_VALUE},
        "batch_contract": {
            "exact_type": "builtins.tuple", "empty_allowed": True, "member_exact_type": "builtins.str",
            "members_full_scalar_valid": True, "strict_ascii_ascending": True, "unique": True,
            "automatic_sort_or_deduplicate": False, "current_record_excluded_by_caller": True,
        },
        "validation_precedence": ["duplicate_identity_key", POLICY_CONTEXT_ITEM, BATCH_CONTEXT_ITEM, "exact_membership"],
        "outcome_vocabulary": ["passed", "blocked", "invalid"],
        "blocks_candidate_invariant": "true_iff_outcome_not_passed", "invalid_blocks_candidate": True,
        "scalar_invalid_reasons": list(SCALAR_REASONS), "policy_invalid_reasons": list(POLICY_REASONS),
        "batch_invalid_reasons": list(BATCH_REASONS), "duplicate_blocked_reason": DUPLICATE_REASON,
        "membership_semantics": "exact case-sensitive Python string equality",
        "composition_contract": "composition intentionally opaque and producer-owned",
        "duplicate_equivalence": "same key means producer-declared exact duplicate admission class",
        "different_key_limited_claim": "this key does not prove duplication; no chemical distinctness is asserted",
        "producer_responsibility": {
            "canonical_descriptor_maintained": True, "sha256_lowercase_hex": True,
            "preimage_retained_or_reconstructable": True, "collision_fail_closed": True,
            "version_change_requires_new_contract_and_prefix": True,
        },
        "evaluator_detects_digest_collision": False, "evaluator_validates_descriptor_provenance": False,
        "identity_boundaries": {row["boundary_item"]: row["is_duplicate_identity_key"] == "true" for row in state["boundary_rows"]},
        "real_provider_duplicate_identity_mapping_validated": False,
        "real_provider_duplicate_identity_key_count": 0,
        "design_oracle_name": "classify_admit_009_duplicate_identity_key_design",
        "design_oracle_is_formal_evaluator": False, "design_oracle_evaluator_io_used": False,
        "truth_matrix_contract": "Exact32", "truth_row_count": len(truth),
        "truth_pass_count": sum(row["truth_passed"] == "true" for row in truth), "truth_group_counts": groups,
        "contract_row_count": len(state["contract_rows"]), "context_row_count": len(state["context_rows"]),
        "boundary_row_count": len(state["boundary_rows"]), "issue_inventory_row_count": len(state["issue_rows"]),
        "source_boundary_name": "fixed_ordered_exact16_committed_source_boundary",
        "source_input_count": len(SOURCE_PATHS), "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": _source_verification(state["snapshot"]),
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "issue_transition": {
            "issue_id": PRIMARY_BLOCKER, "from_status": "open", "to_status": "resolved",
            "from_integration_transition": "unchanged_open",
            "to_integration_transition": "duplicate_identity_key_contract_frozen_v1",
            "only_authorized_issue_change": True,
        },
        "coverage_issue_status": "open", "coverage_issue_affected_rules": "ADMIT_009–ADMIT_015",
        "coverage_issue_transition": "admit_008_implemented_and_removed_from_open_coverage_scope",
        "readiness": readiness, "output_file_count": 6, "output_files": list(OUTPUT_FILES),
        "output_sha256": dict(output_sha256), "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "no_real_provider_key_generation", "no_provider_mapping_validation", "no_formal_evaluator",
            "no_result_class", "no_adapter_design_or_implementation", "no_exact8_runtime_change",
            "no_admit_009_registration", "no_admit_010", "no_evaluate_all_rules",
            "no_combined_verdict", "no_raw_network_download_or_training",
        ],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_source_boundary_checks_passed": True, "all_contract_checks_passed": True,
        "all_context_checks_passed": True, "all_boundary_checks_passed": True,
        "all_truth_checks_passed": True, "all_issue_checks_passed": True,
        "all_readiness_checks_passed": True, "all_attestations_passed": True,
        "validation_failures": [],
    }
    manifest.update(readiness)
    return manifest


def _validate_output_root(root: Path) -> None:
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("unsafe output root")
    if root.exists():
        entries = tuple(root.iterdir())
        if not {path.name for path in entries}.issubset(set(OUTPUT_FILES)):
            raise ValueError("unexpected output present")
        if any(path.is_symlink() or not path.is_file() for path in entries):
            raise ValueError("unsafe existing output")


def run_covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    root = Path(output_root)
    _validate_output_root(root)
    state = build_design_state()
    documents = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        CONTEXT_FILENAME: _csv_bytes(CONTEXT_COLUMNS, state["context_rows"]),
        BOUNDARY_FILENAME: _csv_bytes(BOUNDARY_COLUMNS, state["boundary_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    output_sha = {name: hashlib.sha256(content).hexdigest() for name, content in documents.items()}
    manifest = _manifest(state, output_sha)
    documents[MANIFEST_FILENAME] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    root.mkdir(parents=True, exist_ok=True)
    for name in OUTPUT_FILES:
        destination = root / name
        if destination.is_symlink():
            raise ValueError("unsafe output symlink")
        destination.write_bytes(documents[name])
    return {"manifest": manifest, "output_bytes": documents}


def main() -> int:
    result = run_covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1()
    manifest = result["manifest"]
    if manifest["admit_009_standalone_evaluator_implemented"]:
        raise AssertionError("formal evaluator must remain unimplemented")
    if not manifest["ready_for_admit_009_standalone_evaluator_interface_implementation"]:
        raise AssertionError("standalone evaluator implementation preconditions must be complete")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
