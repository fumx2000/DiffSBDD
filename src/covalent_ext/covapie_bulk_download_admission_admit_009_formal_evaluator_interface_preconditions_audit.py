"""Read-only ADMIT_009 formal-evaluator interface preconditions audit v1.

This metadata-only gate proves which interface identities exist and which
duplicate-identity semantics do not.  It does not design a key, evaluate a
candidate, access raw data, or modify the Exact8 runtime.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "ADMIT_009 formal evaluator interface preconditions audit v1"
STAGE = "covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1"
EXPECTED_BASE_COMMIT = "8215c99edc93b4dcf50da87139917fae9ec46cc5"
EXPECTED_BASE_SUBJECT = "add CovaPIE unified admission runtime for ADMIT_001 to ADMIT_008 v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_009_formal_evaluator_preconditions_manifest_v1"
PRIMARY_BLOCKER = "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_009_duplicate_identity_key_contract_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

RUNTIME_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1")
DESIGN_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1")
IMPLEMENTATION_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1")
CANDIDATE_DESIGN_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1")
CANDIDATE_INTEGRATION_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1")
LIGAND_EVIDENCE_ROOT = Path("data/derived/covalent_small/covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke_v0")
LEAKAGE_ASSIGNMENT_ROOT = Path("data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0")
SPLIT_ROOT = Path("data/derived/covalent_small/covapie_unified_leakage_split_materialization_smoke_v0")
FINAL_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0")

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008.py",
    str(RUNTIME_ROOT / "covapie_admit_001_to_008_runtime_contract.csv"),
    str(RUNTIME_ROOT / "covapie_admit_001_to_008_runtime_manifest.json"),
    str(RUNTIME_ROOT / "covapie_admit_001_to_008_runtime_issue_inventory.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_schema_contract.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_design_gate_manifest.json"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_field_semantics_matrix.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_implementation_issue_inventory.csv"),
    str(CANDIDATE_DESIGN_ROOT / "covapie_candidate_record_id_semantics_contract.csv"),
    str(CANDIDATE_INTEGRATION_ROOT / "covapie_candidate_record_id_integrated_field_matrix.csv"),
    str(LIGAND_EVIDENCE_ROOT / "covapie_ligand_graph_scaffold_evidence.csv"),
    str(LEAKAGE_ASSIGNMENT_ROOT / "covapie_final_leakage_group_assignment.csv"),
    str(SPLIT_ROOT / "covapie_sample_split_assignment.csv"),
    str(FINAL_ROOT / "covapie_final_dataset_membership.csv"),
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "b5022ee4b6a4e965cf783abf15e70a5909860f4f500c89f983fb41b6b8fd87e2",
    "27d0c9d941698d99d045b367889ccd388f708353bcd342eb7f57729bb99940f9",
    "6047e110c29d8ca7300236f8af8dbce31a92f2a62576cbc2a8fa2d5d1baf32cf",
    "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "085cb2f2a6bfe9bebe9e503dd10aa0b4d6f9ad754ff99539b1bafb33c78b5444",
    "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "7c7707f5261461083bda7ab2177a423b608c725c070dafaff558bdf39256211e",
    "92f624705a611c0dac011229d13d6a3ba87fc1ab7a3e0bc9c090952a0838b318",
    "d7a198a9eb2bb5acd9887242eab3f81808db78b2fddd93720509897ea1578d7f",
    "982a9f89a89d3a4ad6a3e468cfd16d2fdfd5435cbf6d593e086fbd7fadd3ec73",
    "768c964f22e19a8fb6232b1fa26c531e53d023042abcd9b1bcca44df2b4f4416",
    "29ffff244e33e3ec93f2c2b3e5e42a09ce73d7f55019f833e97659301f6a388c",
    "ddf1705176c8680d90e0e216a9af3d1501c6a821764c3e7138a28269e687a977",
), strict=True))

(
    RUNTIME_SOURCE_PATH, RUNTIME_CONTRACT_PATH, RUNTIME_MANIFEST_PATH,
    RUNTIME_ISSUE_PATH, RULE_REGISTRY_PATH, SCHEMA_CONTRACT_PATH,
    DESIGN_MANIFEST_PATH, FIELD_SEMANTICS_PATH, RULE_EXECUTABILITY_PATH,
    EVALUATION_CONTEXT_PATH, IMPLEMENTATION_ISSUE_PATH,
    CANDIDATE_CONTRACT_PATH, CANDIDATE_INTEGRATED_FIELD_PATH,
    LIGAND_EVIDENCE_PATH, LEAKAGE_ASSIGNMENT_PATH, SPLIT_ASSIGNMENT_PATH,
    FINAL_MEMBERSHIP_PATH,
) = SOURCE_PATHS

MATCH_TERMS = (
    "ADMIT_009", "duplicate_identity_precheck", "duplicate_identity_key",
    "batch_duplicate_identity_keys", "duplicate_identity_key_contract",
    "duplicate_precheck_complete", "duplicate_identity_unresolved", PRIMARY_BLOCKER,
    "candidate_record_id", "leakage_group_id", "final_leakage_group_id",
    "ligand_graph_group_id", "ligand_scaffold_group_id", "sample_index_row_id",
    "assignment_id", "covalent_bond_atom_pair", "protein_exact_sequence_group_id",
)

PRECONDITION_FILENAME = "covapie_admit_009_evaluator_precondition_matrix.csv"
VOCABULARY_FILENAME = "covapie_admit_009_duplicate_identity_vocabulary_inventory.csv"
OCCURRENCE_FILENAME = "covapie_admit_009_field_occurrence_inventory.csv"
SOURCE_BOUNDARY_FILENAME = "covapie_admit_009_source_boundary_audit.csv"
ISSUE_FILENAME = "covapie_admit_009_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_009_formal_evaluator_preconditions_manifest.json"
CSV_OUTPUTS = (PRECONDITION_FILENAME, VOCABULARY_FILENAME, OCCURRENCE_FILENAME, SOURCE_BOUNDARY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

PRECONDITION_COLUMNS = (
    "precondition_id", "semantic_area", "required_contract", "observed_contract",
    "source_evidence", "semantics_complete", "blocker_id",
    "implementation_disposition", "precondition_passed",
)
VOCABULARY_COLUMNS = (
    "vocabulary_order", "source_relative_path", "source_sha256", "source_kind",
    "symbol_or_row_id", "observed_term", "observed_role", "semantic_category",
    "explicitly_declared_duplicate_key", "explicitly_declared_duplicate_key_component",
    "exact_duplicate_equivalence_declared", "safe_to_use_in_duplicate_key_contract_now",
    "promotion_blocker", "inventory_passed",
)
OCCURRENCE_COLUMNS = (
    "occurrence_order", "source_relative_path", "source_sha256", "source_kind",
    "symbol_or_row_id", "matched_term", "field_role", "rule_scope",
    "semantic_statement", "authoritative_for_admit009_formal_semantics", "occurrence_passed",
)
SOURCE_BOUNDARY_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256", "source_boundary_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

TRUE_READINESS = (
    "admit_009_admission_rule_identity_available",
    "admit_009_evaluation_phase_available",
    "admit_009_candidate_field_identity_available",
    "admit_009_batch_context_dependency_available",
    "admit_009_evaluation_policy_item_available",
    "admit_009_pure_in_memory_interface_possible",
    "admit_009_duplicate_identity_semantics_gap_confirmed",
    "ready_for_admit_009_duplicate_identity_key_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
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
    "ready_for_admit_009_standalone_evaluator_interface_implementation",
    "admit_009_standalone_evaluator_implemented",
    "admit_009_unified_adapter_contract_frozen", "admit_009_unified_adapter_implemented",
    "admit_009_registered_in_engine", "unified_dispatch_runtime_with_admit_001_to_009_implemented",
    "admit_010_standalone_evaluator_implemented", "admit_010_to_015_registered_in_engine",
    "all_15_rules_covered", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen", "real_provider_duplicate_identity_mapping_validated",
    "real_provider_duplicate_identity_key_count_nonzero", "real_candidate_evaluation",
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


def _validate_expected_base_lineage(repo_root: Path, *, head_ref: str = "HEAD") -> None:
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("head ref is invalid")
    base = _git(["cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"], repo_root)
    subject = _git(["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], repo_root)
    ancestor = _git(["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref], repo_root)
    if base.returncode != 0 or subject.returncode != 0:
        raise ValueError("expected base commit is unavailable")
    if subject.stdout.strip() != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base commit subject mismatch")
    if ancestor.returncode != 0:
        raise ValueError("expected base commit is not an ancestor of head")


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
    """Validate every source structurally before the first explicit byte read."""
    if len(SOURCE_PATHS) != 17 or len(set(SOURCE_PATHS)) != 17 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact17 source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref=head_ref)
    if not all(_structural_source_check(path, repo_root) for path in SOURCE_PATHS):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"], repo_root, text=False)
        if base.returncode != 0 or type(base.stdout) is not bytes:
            raise ValueError(f"base-tree source read failed: {path}")
        filesystem_bytes = (repo_root / path).read_bytes()
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem_bytes).hexdigest()
        if SOURCE_SHA256[path] != base_sha or base_sha != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, SOURCE_SHA256[path], base_sha, filesystem_sha, filesystem_bytes))
    snapshot = FrozenSourceSnapshot(tuple(records))
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("frozen source snapshot invalid")
    return snapshot


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot and len(value.records) == 17
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
    rule = _one(_csv_rows(snapshot, RULE_REGISTRY_PATH), "admission_rule_id", "ADMIT_009")
    schema = _one(_csv_rows(snapshot, SCHEMA_CONTRACT_PATH), "admission_field_name", "duplicate_identity_key")
    field = _one(_csv_rows(snapshot, FIELD_SEMANTICS_PATH), "field_name", "duplicate_identity_key")
    executable = _one(_csv_rows(snapshot, RULE_EXECUTABILITY_PATH), "admission_rule_id", "ADMIT_009")
    batch = _one(_csv_rows(snapshot, EVALUATION_CONTEXT_PATH), "context_item", "batch_duplicate_identity_keys")
    policy = _one(_csv_rows(snapshot, EVALUATION_CONTEXT_PATH), "context_item", "duplicate_identity_key_contract")
    implementation_issue = _one(_csv_rows(snapshot, IMPLEMENTATION_ISSUE_PATH), "issue_id", PRIMARY_BLOCKER)
    issues = _csv_rows(snapshot, RUNTIME_ISSUE_PATH)
    runtime_issue = _one(issues, "issue_id", PRIMARY_BLOCKER)
    coverage = _one(issues, "issue_id", "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    candidate_separation = _one(_csv_rows(snapshot, CANDIDATE_CONTRACT_PATH), "contract_item", "separate_from_duplicate_identity_key")
    integrated_duplicate = _one(_csv_rows(snapshot, CANDIDATE_INTEGRATED_FIELD_PATH), "field_name", "duplicate_identity_key")
    leakage_rows = _csv_rows(snapshot, LEAKAGE_ASSIGNMENT_PATH)
    split_rows = _csv_rows(snapshot, SPLIT_ASSIGNMENT_PATH)
    final_rows = _csv_rows(snapshot, FINAL_MEMBERSHIP_PATH)
    runtime_manifest = _json(snapshot, RUNTIME_MANIFEST_PATH)
    required = (
        rule == {"admission_rule_id": "ADMIT_009", "admission_rule_name": "duplicate_identity_precheck", "evidence_source": "future_candidate_record", "required_status": "duplicate_precheck_complete", "failure_severity": "blocking", "blocking_reason": "duplicate_identity_unresolved", "evaluation_phase": "pre_download", "network_required": "false", "raw_structure_required": "false", "ready_for_future_implementation": "true"},
        schema["value_contract"] == "pre-download deduplication key",
        field["candidate_record_field"] == "true" and field["dependent_rules"] == "ADMIT_009",
        field["evaluation_context_dependencies"] == "duplicate_identity_key_contract",
        field["allowed_values_defined"] == field["normalization_defined"] == field["exact_validation_defined"] == field["implementation_semantics_complete"] == "false",
        field["blocking_reasons"] == PRIMARY_BLOCKER,
        executable["candidate_field_dependencies"] == "duplicate_identity_key",
        executable["batch_context_dependencies"] == "batch_duplicate_identity_keys",
        executable["evaluation_context_dependencies"] == "duplicate_identity_key_contract",
        executable["pure_in_memory_interface_possible"] == "true",
        executable["semantics_complete"] == executable["deterministic_evaluation_possible_now"] == "false",
        batch["context_scope"] == "batch" and batch["provided_by_future_caller"] == "true",
        batch["filesystem_access_inside_evaluator"] == batch["network_access_inside_evaluator"] == "false",
        policy["context_scope"] == "evaluation_policy" and policy["exact_contract_defined"] == "false",
        policy["blocking_reasons"] == PRIMARY_BLOCKER,
        candidate_separation["exact_requirement"] == "not duplicate_identity_key",
        candidate_separation["forbidden_behavior"] == "replace_admit_009",
        candidate_separation["contract_passed"] == "true",
        integrated_duplicate["implementation_semantics_complete"] == "false" and integrated_duplicate["blocking_reasons"] == PRIMARY_BLOCKER,
        implementation_issue["status"] == runtime_issue["status"] == "open",
        runtime_issue["affected_fields"] == "duplicate_identity_key" and runtime_issue["affected_rules"] == "ADMIT_009",
        runtime_issue["integration_transition"] == "unchanged_open",
        len(issues) == 11 and hashlib.sha256(_record(snapshot, RUNTIME_ISSUE_PATH).content_bytes).hexdigest() == "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128",
        coverage["affected_rules"] == "|".join(f"ADMIT_{index:03d}" for index in range(9, 16)),
        coverage["integration_transition"] == "admit_008_implemented_and_removed_from_open_coverage_scope",
        runtime_manifest["registered_rule_count"] == 8,
        runtime_manifest["admit_009_standalone_evaluator_implemented"] is False,
        runtime_manifest["admit_009_registered_in_engine"] is False,
        runtime_manifest["ready_for_admit_009_formal_evaluator_interface_preconditions_audit"] is True,
        len(leakage_rows) == len(split_rows) == len(final_rows) == 11,
        all(row["assignment_policy"] == "conservative_union_of_ligand_graph_scaffold_and_protein_accession_sequence_clusters_v1" for row in leakage_rows),
        all(row["split_unit_type"] == "final_leakage_group_id" for row in split_rows),
        all(row["group_membership_consistent"] == "True" for row in final_rows),
    )
    if not all(required):
        raise ValueError("authoritative predecessor contract mismatch")


def _precondition_rows() -> tuple[dict[str, str], ...]:
    specs = (
        ("admission_rule_identity", "ADMIT_009 identity and formal name", "ADMIT_009 duplicate_identity_precheck", "rule registry", True, "", "identity frozen"),
        ("evaluation_phase", "exact evaluation phase", "pre_download", "rule registry and executability matrix", True, "", "phase frozen"),
        ("candidate_field_name", "candidate field identity", "duplicate_identity_key", "schema and field matrices", True, "", "field identity frozen"),
        ("batch_context_item_name", "batch dependency identity", "batch_duplicate_identity_keys", "executability and context contracts", True, "", "dependency identity frozen"),
        ("evaluation_policy_item_name", "evaluation-policy dependency identity", "duplicate_identity_key_contract", "executability and context contracts", True, "", "dependency identity frozen"),
        ("pure_in_memory_interface_possible", "filesystem/network-free evaluator feasibility", "future caller supplies dependencies; evaluator IO is false", "executability and context contracts", True, "", "pure interface is feasible after contract design"),
        ("scalar_exact_type", "exact scalar type", "no exact str, tuple, record, or digest type is frozen", "field semantics and fixed boundary", False, PRIMARY_BLOCKER, "freeze exact type"),
        ("scalar_syntax_and_length", "syntax, length, charset, escaping", "no key grammar is frozen", "fixed boundary", False, PRIMARY_BLOCKER, "freeze key grammar"),
        ("normalization_and_canonicalization", "trim, case, Unicode, alias, repair policies", "normalization_defined=false; no alias or repair contract", "field semantics matrix", False, PRIMARY_BLOCKER, "freeze normalization"),
        ("duplicate_key_component_set", "exact candidate component set", "candidate, ligand, protein, residue, atom and group evidence exists without key promotion", "identity inventories", False, PRIMARY_BLOCKER, "design component contract"),
        ("component_order_and_encoding", "component order, names, version, separator and empty policy", "no ordering or encoding contract", "fixed boundary", False, PRIMARY_BLOCKER, "freeze encoding"),
        ("duplicate_equivalence_domain", "exact duplicate equivalence domain", "record, ligand, grouping, leakage and materialization identities remain distinct", "identity and leakage evidence", False, PRIMARY_BLOCKER, "freeze equivalence domain"),
        ("collision_handling", "hash/key collision and version mismatch policy", "no collision policy", "fixed boundary", False, PRIMARY_BLOCKER, "freeze collision handling"),
        ("batch_container_exact_type", "exact batch container type and mutation/copy policy", "dependency exists; list/tuple/set/frozenset is not selected", "evaluation context contract", False, PRIMARY_BLOCKER, "freeze batch container"),
        ("batch_member_exact_type", "exact member type", "member type is not frozen", "fixed boundary", False, PRIMARY_BLOCKER, "freeze member type"),
        ("batch_membership_semantics", "equality, order, duplicates, normalization and malformed handling", "no membership comparison contract", "fixed boundary", False, PRIMARY_BLOCKER, "freeze membership semantics"),
        ("current_candidate_self_exclusion", "self-inclusion, exclusion and multiplicity policy", "current-candidate membership is unspecified", "fixed boundary", False, PRIMARY_BLOCKER, "freeze self-exclusion"),
        ("candidate_record_id_relationship", "candidate_record_id role in duplicate evaluation", "candidate_record_id is explicitly separate; self-exclusion use is not frozen", "candidate identity contract", False, PRIMARY_BLOCKER, "design relationship without identity substitution"),
        ("duplicate_vs_leakage_group_boundary", "exact duplicate versus broader must-link leakage group", "leakage group is a conservative multi-relation union; exact-duplicate boundary absent", "leakage assignment evidence", False, PRIMARY_BLOCKER, "freeze boundary"),
        ("outcome_vocabulary", "unique, duplicate, malformed and collision outcomes", "no ADMIT_009 outcome mapping", "fixed boundary", False, PRIMARY_BLOCKER, "freeze outcomes"),
        ("reason_vocabulary", "formal uppercase reason vocabulary", "only historical lowercase umbrella reason exists", "rule registry", False, PRIMARY_BLOCKER, "freeze reasons"),
        ("canonical_validated_state", "canonical and validated state for every path", "no state-retention contract", "fixed boundary", False, PRIMARY_BLOCKER, "freeze result state"),
        ("independent_semantic_oracle", "independent pure full-input semantic oracle", "no ADMIT_009 oracle exists", "Exact8 runtime and fixed boundary", False, PRIMARY_BLOCKER, "design oracle after key contract"),
        ("real_provider_and_implementation_readiness", "canonical provider mapping and complete standalone contract", "zero canonical duplicate keys; implementation remains prohibited", "fixed boundary and stop boundary", False, PRIMARY_BLOCKER, "design key contract next"),
    )
    return tuple({
        "precondition_id": f"PRE_{index:03d}", "semantic_area": area,
        "required_contract": required, "observed_contract": observed,
        "source_evidence": evidence, "semantics_complete": _bool(complete),
        "blocker_id": blocker, "implementation_disposition": disposition,
        "precondition_passed": "true",
    } for index, (area, required, observed, evidence, complete, blocker, disposition) in enumerate(specs, 1))


def _source_kind(path: Path) -> str:
    if path.suffix == ".py":
        return "production_source"
    if path.suffix == ".json":
        return "committed_manifest"
    return "committed_contract_csv"


def _vocabulary_rows() -> tuple[dict[str, str], ...]:
    specs = (
        (SCHEMA_CONTRACT_PATH, "admission_field_name", "duplicate_identity_key", "pre-download deduplication-key candidate field", "admission_candidate_field", True),
        (CANDIDATE_CONTRACT_PATH, "separate_from_duplicate_identity_key", "candidate_record_id", "opaque candidate-record identity explicitly separate from duplicate key", "record_identifier", False),
        (LIGAND_EVIDENCE_PATH, "column", "sample_index_row_id", "sample-index row identity", "sample_identifier", False),
        (LEAKAGE_ASSIGNMENT_PATH, "column", "assignment_id", "leakage assignment row identity", "assignment_identifier", False),
        (SCHEMA_CONTRACT_PATH, "admission_field_name", "pdb_id", "structure identifier", "record_identifier", False),
        (SCHEMA_CONTRACT_PATH, "admission_field_name", "ligand_comp_id", "ligand component identity", "ligand_identity", False),
        (SCHEMA_CONTRACT_PATH, "admission_field_name", "covalent_residue_name", "covalent residue locator component", "residue_identity", False),
        (SCHEMA_CONTRACT_PATH, "admission_field_name", "covalent_residue_chain_id", "covalent residue locator component", "residue_identity", False),
        (SCHEMA_CONTRACT_PATH, "admission_field_name", "covalent_residue_index", "covalent residue locator component", "residue_identity", False),
        (SCHEMA_CONTRACT_PATH, "admission_field_name", "covalent_residue_atom_name", "covalent residue locator component", "residue_identity", False),
        (SCHEMA_CONTRACT_PATH, "admission_field_name", "covalent_bond_atom_pair", "covalent atom-pair evidence", "atom_pair_identity", False),
        (LIGAND_EVIDENCE_PATH, "column", "ligand_graph_group_id", "ligand graph grouping identity", "ligand_graph_group", False),
        (LIGAND_EVIDENCE_PATH, "column", "ligand_scaffold_group_id", "ligand scaffold grouping identity", "ligand_scaffold_group", False),
        (LEAKAGE_ASSIGNMENT_PATH, "column", "protein_exact_sequence_group_id", "protein exact-sequence group", "protein_identity_group", False),
        (LEAKAGE_ASSIGNMENT_PATH, "column", "protein_accession_group_id", "protein accession group", "protein_identity_group", False),
        (LEAKAGE_ASSIGNMENT_PATH, "column", "protein_sequence_cluster_90_id", "protein 90-percent sequence cluster", "protein_identity_group", False),
        (LEAKAGE_ASSIGNMENT_PATH, "column", "protein_sequence_cluster_50_id", "protein 50-percent sequence cluster", "protein_identity_group", False),
        (LEAKAGE_ASSIGNMENT_PATH, "column", "final_leakage_group_id", "conservative multi-relation must-link group", "leakage_group", False),
        (SCHEMA_CONTRACT_PATH, "admission_field_name", "leakage_group_id", "pre-final-split leakage group candidate field", "leakage_group", False),
        (SPLIT_ASSIGNMENT_PATH, "column", "sample_split_assignment_id", "sample split assignment identity", "split_assignment", False),
        (FINAL_MEMBERSHIP_PATH, "column", "final_dataset_membership_id", "materialized final-dataset membership identity", "sample_identifier", False),
        (RULE_REGISTRY_PATH, "ADMIT_009.required_status", "duplicate_precheck_complete", "historical required status", "historical_required_status", False),
        (RULE_REGISTRY_PATH, "ADMIT_009.blocking_reason", "duplicate_identity_unresolved", "historical lowercase umbrella reason", "historical_blocking_reason", False),
        (RUNTIME_ISSUE_PATH, "issue_id", PRIMARY_BLOCKER, "open implementation blocker", "implementation_blocker", False),
    )
    return tuple({
        "vocabulary_order": str(index), "source_relative_path": path.as_posix(),
        "source_sha256": SOURCE_SHA256[path], "source_kind": _source_kind(path),
        "symbol_or_row_id": symbol, "observed_term": term, "observed_role": role,
        "semantic_category": category, "explicitly_declared_duplicate_key": _bool(declared),
        "explicitly_declared_duplicate_key_component": "false",
        "exact_duplicate_equivalence_declared": "false",
        "safe_to_use_in_duplicate_key_contract_now": "false",
        "promotion_blocker": PRIMARY_BLOCKER, "inventory_passed": "true",
    } for index, (path, symbol, term, role, category, declared) in enumerate(specs, 1))


def _occurrence_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    identity_terms = {"ADMIT_009", "duplicate_identity_precheck", "duplicate_identity_key", "batch_duplicate_identity_keys", "duplicate_identity_key_contract", "duplicate_precheck_complete", "duplicate_identity_unresolved"}
    authoritative_paths = {RULE_REGISTRY_PATH, SCHEMA_CONTRACT_PATH, FIELD_SEMANTICS_PATH, RULE_EXECUTABILITY_PATH, EVALUATION_CONTEXT_PATH, RUNTIME_ISSUE_PATH}
    rows: list[dict[str, str]] = []
    for record in snapshot.records:
        for line_number, line in enumerate(record.content_bytes.decode("utf-8").splitlines(), 1):
            for term in MATCH_TERMS:
                if term not in line:
                    continue
                if term in identity_terms:
                    role = "ADMIT_009 high-level identity or dependency"
                    statement = "the named interface element is evidence; its occurrence does not freeze duplicate-key semantics"
                    scope = "ADMIT_009"
                elif term == PRIMARY_BLOCKER:
                    role, scope, statement = "open semantics blocker", "ADMIT_009", "duplicate identity key semantics remain unresolved"
                else:
                    role = "distinct identity or grouping evidence"
                    scope = "candidate, ligand, protein, leakage, split, or materialization"
                    statement = "the observed identifier is not thereby a duplicate key or exact-duplicate equivalence"
                authoritative = term in identity_terms and record.relative_path in authoritative_paths
                rows.append({
                    "occurrence_order": str(len(rows) + 1),
                    "source_relative_path": record.relative_path.as_posix(),
                    "source_sha256": record.expected_sha256,
                    "source_kind": _source_kind(record.relative_path),
                    "symbol_or_row_id": f"line_{line_number}", "matched_term": term,
                    "field_role": role, "rule_scope": scope, "semantic_statement": statement,
                    "authoritative_for_admit009_formal_semantics": _bool(authoritative),
                    "occurrence_passed": "true",
                })
    if {row["matched_term"] for row in rows} != set(MATCH_TERMS):
        raise ValueError("field occurrence coverage incomplete")
    return tuple(rows)


def _source_boundary_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    return tuple({
        "source_order": str(index), "source_relative_path": record.relative_path.as_posix(),
        "source_kind": _source_kind(record.relative_path),
        "boundary_necessity": "minimal committed evidence for ADMIT_009 identity, unresolved semantics, identity separation, leakage boundary, or Exact11 preservation",
        "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true", "non_symlink": "true",
        "expected_sha256": record.expected_sha256, "base_tree_sha256": record.base_tree_sha256,
        "filesystem_sha256": record.filesystem_sha256, "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot.records, 1))


def _readiness() -> dict[str, bool]:
    return {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def build_audit_state(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root)
    _validate_predecessors(snapshot)
    return {
        "snapshot": snapshot, "precondition_rows": _precondition_rows(),
        "vocabulary_rows": _vocabulary_rows(), "occurrence_rows": _occurrence_rows(snapshot),
        "source_rows": _source_boundary_rows(snapshot),
        "issue_rows": _csv_rows(snapshot, RUNTIME_ISSUE_PATH),
        "issue_bytes": _record(snapshot, RUNTIME_ISSUE_PATH).content_bytes,
        "readiness": _readiness(),
    }


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _manifest(state: Mapping[str, Any], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    readiness = dict(state["readiness"])
    preconditions = state["precondition_rows"]
    manifest: dict[str, Any] = {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": "ADMIT_009", "admission_rule_name": "duplicate_identity_precheck",
        "evaluation_phase": "pre_download", "candidate_field": "duplicate_identity_key",
        "batch_context_item": "batch_duplicate_identity_keys",
        "evaluation_policy_context_item": "duplicate_identity_key_contract",
        "future_evaluator_name_reserved_only": "evaluate_admit_009",
        "future_result_name_reserved_only": "Admit009EvaluationResult",
        "historical_evidence_source": "future_candidate_record",
        "historical_required_status": "duplicate_precheck_complete",
        "historical_blocking_reason": "duplicate_identity_unresolved",
        "source_boundary_name": "fixed_ordered_minimal_exact17_committed_source_boundary",
        "source_input_count": len(SOURCE_PATHS),
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [{
            "source_order": int(row["source_order"]), "source_relative_path": row["source_relative_path"],
            "expected_sha256": row["expected_sha256"], "base_tree_sha256": row["base_tree_sha256"],
            "filesystem_sha256": row["filesystem_sha256"], "tracked": True,
            "base_tree_blob": True, "filesystem_regular": True, "non_symlink": True,
            "source_verified": True,
        } for row in state["source_rows"]],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "precondition_row_count": len(preconditions), "precondition_pass_count": len(preconditions),
        "semantics_complete_count": sum(row["semantics_complete"] == "true" for row in preconditions),
        "semantics_incomplete_count": sum(row["semantics_complete"] == "false" for row in preconditions),
        "vocabulary_inventory_row_count": len(state["vocabulary_rows"]),
        "field_occurrence_inventory_row_count": len(state["occurrence_rows"]),
        "real_provider_duplicate_identity_key_count": 0,
        "real_provider_mapping_observation": "historical grouping evidence exists, canonical duplicate-key provider mapping unvalidated",
        "high_level_precheck_evidence": {
            "admission_rule_identity_available": True,
            "evaluation_phase_available": True,
            "candidate_field_identity_available": True,
            "batch_context_dependency_available": True,
            "evaluation_policy_item_available": True,
            "pure_in_memory_interface_possible": True,
        },
        "identity_boundaries": {
            "candidate_record_id_is_duplicate_identity_key": False,
            "sample_index_row_id_is_duplicate_identity_key": False,
            "assignment_id_is_duplicate_identity_key": False,
            "ligand_comp_id_alone_is_duplicate_identity_key": False,
            "ligand_graph_group_id_is_duplicate_identity_key": False,
            "ligand_scaffold_group_id_is_duplicate_identity_key": False,
            "leakage_group_id_is_duplicate_identity_key": False,
            "final_leakage_group_id_is_duplicate_identity_key": False,
            "same_leakage_group_means_exact_duplicate": False,
        },
        "unresolved_semantic_areas": [
            "scalar_exact_type", "scalar_syntax_length_charset_and_escaping",
            "normalization_canonicalization_alias_and_repair", "duplicate_key_component_set",
            "component_order_names_version_separator_and_empty_policy", "duplicate_equivalence_domain",
            "collision_handling", "batch_container_exact_type_and_mutation_policy",
            "batch_member_exact_type", "batch_membership_semantics", "current_candidate_self_exclusion",
            "candidate_record_id_self_exclusion_relationship", "duplicate_vs_leakage_group_boundary",
            "outcome_vocabulary", "formal_uppercase_reason_vocabulary", "canonical_validated_state",
            "independent_semantic_oracle", "real_provider_mapping",
        ],
        "blocker_ids": [PRIMARY_BLOCKER],
        "issue_inventory_row_count": len(state["issue_rows"]),
        "issue_inventory_sha256": "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128",
        "issue_inventory_byte_identical_to_exact8_predecessor": True,
        "duplicate_identity_key_semantics_issue_status": "open",
        "coverage_issue_starts_with_admit_009": True,
        "readiness": readiness,
        "output_file_count": 6, "output_files": list(OUTPUT_FILES),
        "output_sha256": dict(output_sha256), "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "no_duplicate_identity_key_design", "no_component_selection", "no_separator_or_hash_selection",
            "no_batch_container_design", "no_self_exclusion_design", "no_evaluate_admit_009",
            "no_Admit009EvaluationResult", "no_adapter_design", "no_exact8_runtime_change",
            "no_admit_009_registration", "no_admit_010", "no_provider_mapping_validation",
            "no_real_candidate_evaluation", "no_raw_network_or_download", "no_training",
        ],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_source_boundary_checks_passed": True, "all_precondition_checks_passed": True,
        "all_vocabulary_inventory_checks_passed": True, "all_occurrence_checks_passed": True,
        "all_issue_checks_passed": True, "all_readiness_checks_passed": True,
        "all_attestations_passed": True, "validation_failures": [],
    }
    manifest.update(readiness)
    return manifest


def _validate_output_root(root: Path) -> None:
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("unsafe output root")
    if root.exists():
        names = {path.name for path in root.iterdir()}
        if not names.issubset(set(OUTPUT_FILES)):
            raise ValueError("unexpected output present")
        if any(path.is_symlink() or not path.is_file() for path in root.iterdir()):
            raise ValueError("unsafe existing output")


def run_covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    root = Path(output_root)
    _validate_output_root(root)
    state = build_audit_state()
    documents = {
        PRECONDITION_FILENAME: _csv_bytes(PRECONDITION_COLUMNS, state["precondition_rows"]),
        VOCABULARY_FILENAME: _csv_bytes(VOCABULARY_COLUMNS, state["vocabulary_rows"]),
        OCCURRENCE_FILENAME: _csv_bytes(OCCURRENCE_COLUMNS, state["occurrence_rows"]),
        SOURCE_BOUNDARY_FILENAME: _csv_bytes(SOURCE_BOUNDARY_COLUMNS, state["source_rows"]),
        ISSUE_FILENAME: state["issue_bytes"],
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
    result = run_covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1()
    manifest = result["manifest"]
    if manifest["ready_for_admit_009_standalone_evaluator_interface_implementation"]:
        raise AssertionError("ADMIT_009 standalone evaluator readiness must remain false")
    if not manifest["ready_for_admit_009_duplicate_identity_key_contract_design"]:
        raise AssertionError("duplicate identity key contract design readiness must be true")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
