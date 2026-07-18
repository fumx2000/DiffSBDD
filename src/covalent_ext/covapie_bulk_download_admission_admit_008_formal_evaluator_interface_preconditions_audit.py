"""Read-only ADMIT_008 formal-evaluator interface preconditions audit v1.

This metadata-only gate inventories committed contracts.  It deliberately does
not define a topology-disposition enum, evaluator, adapter, runtime entry, real
provider mapping, or candidate evaluation.
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
STEP = "ADMIT_008 formal evaluator interface preconditions audit v1"
STAGE = "covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1"
EXPECTED_BASE_COMMIT = "5dd745ddb3e70d0a4150d2a54ca5531a63b83e9e"
EXPECTED_BASE_SUBJECT = "add CovaPIE unified admission runtime for ADMIT_001 to ADMIT_007 v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_008_formal_evaluator_preconditions_manifest_v1"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_008_topology_restoration_disposition_enum_contract_v1"
PRIMARY_BLOCKER = "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

RUNTIME_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1")
DESIGN_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1")
IMPLEMENTATION_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1")
STEP13M_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0")
STEP13N_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0")

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007.py",
    str(RUNTIME_ROOT / "covapie_admit_001_to_007_runtime_manifest.json"),
    str(RUNTIME_ROOT / "covapie_admit_001_to_007_runtime_issue_inventory.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_schema_contract.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_field_semantics_matrix.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_implementation_issue_inventory.csv"),
    "src/covalent_ext/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate.py",
    str(STEP13M_ROOT / "covalent_restoration_rule_registry_contract.csv"),
    str(STEP13M_ROOT / "ligand_topology_restoration_candidate_contract.csv"),
    str(STEP13M_ROOT / "ligand_topology_restoration_policy_design_gate_manifest.json"),
    "src/covalent_ext/real_covalent_confirmed_candidate_ligand_topology_policy_review_gate.py",
    str(STEP13N_ROOT / "ligand_topology_policy_review_decision_contract.csv"),
    str(STEP13N_ROOT / "ligand_topology_policy_review_gate_manifest.json"),
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "d9fb64a473de1c456115c871a10b06d16f80dac9dc04f87302e43cc01a40a0cd",
    "0a4cb44812ff5398ffba9a077f1217db3da3624d870922eec87848b60091c96e",
    "47de07417697808b044d30260f153ec7e5d46fb7c5b0e2c1f41187bcb09b89a0",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "7c7707f5261461083bda7ab2177a423b608c725c070dafaff558bdf39256211e",
    "466a323e2e38547b93dde4e78fe91975075f5a3ca173c5a6f1c845f999300670",
    "61e00e08ca5d32b2508f0bec3e296bef0edd79fad220e4014a1ac32f5c86f92c",
    "7d506c058e5d4dc49b0c6397db1bb35d11520d157ef1805971acf44283a22751",
    "c104908df85b3a026e5aa83d72483d5698b25b5ed94f35c11b6d15cb4c5c57fc",
    "cf6e3c608be29faeb5c7ffc2f247aafee3863ab483357ad3fcae1d7250741136",
    "5b5bb3d4dec353c8dbeb4fce7aa840846464721d9fbd960835c052eaa4ed8a6a",
    "c1e24b4e583fa10c5338a6a9907b0fd683b51b34c8e26aaa5275ad5afb899bb9",
), strict=True))

(
    RUNTIME_SOURCE_PATH, RUNTIME_MANIFEST_PATH, RUNTIME_ISSUE_PATH,
    RULE_REGISTRY_PATH, SCHEMA_CONTRACT_PATH, FIELD_SEMANTICS_PATH,
    RULE_EXECUTABILITY_PATH, IMPLEMENTATION_ISSUE_PATH, STEP13M_SOURCE_PATH,
    RESTORATION_RULE_PATH, CANDIDATE_CONTRACT_PATH, STEP13M_MANIFEST_PATH,
    STEP13N_SOURCE_PATH, REVIEW_DECISION_PATH, STEP13N_MANIFEST_PATH,
) = SOURCE_PATHS

MATCH_TERMS = (
    "ADMIT_008", "topology_restoration_disposition",
    "approved_template_or_manual_review", "approved_or_manual_review",
    "topology_restoration_unapproved", "restoration_rule_id",
    "restoration_rule_scope", "restoration_rule_source",
    "restoration_rule_validated_for_current_sample",
    "restoration_rule_validated_for_residue_warhead_class",
    "manual_visual_review_required_for_new_rule",
    "quarantine_if_restoration_rule_unknown",
    "unknown_residue_warhead_pair_quarantined",
    "topology_smoke_must_not_auto_restore_ligand",
    "topology_smoke_must_not_generalize_to_non_cys", "v1_train_ready_scope",
    PRIMARY_BLOCKER,
)

PRECONDITION_FILENAME = "covapie_admit_008_evaluator_precondition_matrix.csv"
VOCABULARY_FILENAME = "covapie_admit_008_disposition_vocabulary_inventory.csv"
OCCURRENCE_FILENAME = "covapie_admit_008_field_occurrence_inventory.csv"
SOURCE_BOUNDARY_FILENAME = "covapie_admit_008_source_boundary_audit.csv"
ISSUE_FILENAME = "covapie_admit_008_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_008_formal_evaluator_preconditions_manifest.json"
CSV_OUTPUTS = (PRECONDITION_FILENAME, VOCABULARY_FILENAME, OCCURRENCE_FILENAME, SOURCE_BOUNDARY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

PRECONDITION_COLUMNS = (
    "precondition_id", "semantic_area", "required_contract", "observed_contract",
    "source_evidence", "semantics_complete", "blocker_id",
    "implementation_disposition", "precondition_passed",
)
VOCABULARY_COLUMNS = (
    "vocabulary_order", "source_relative_path", "source_sha256", "source_kind",
    "symbol_or_row_id", "observed_string", "observed_role", "semantic_category",
    "candidate_scalar_value_explicitly_declared", "canonical_enum_member_explicitly_declared",
    "safe_to_promote_to_canonical_enum_now", "promotion_blocker", "inventory_passed",
)
OCCURRENCE_COLUMNS = (
    "occurrence_order", "source_relative_path", "source_sha256", "source_kind",
    "symbol_or_row_id", "matched_term", "field_role", "rule_scope",
    "semantic_statement", "authoritative_for_admit008_formal_semantics", "occurrence_passed",
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
    "admit_008_admission_rule_identity_available",
    "admit_008_candidate_field_contract_available",
    "admit_008_high_level_topology_policy_evidence_available",
    "admit_008_step13m_restoration_policy_evidence_available",
    "admit_008_step13n_policy_review_evidence_available",
    "admit_008_topology_disposition_enum_gap_confirmed",
    "ready_for_admit_008_topology_restoration_disposition_enum_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_008_scalar_exact_type_contract_available",
    "admit_008_null_empty_missing_contract_available",
    "admit_008_canonicalization_contract_available",
    "admit_008_topology_disposition_enum_contract_available",
    "admit_008_category_mapping_contract_available",
    "admit_008_provenance_coherence_contract_available",
    "admit_008_reason_outcome_contract_available",
    "admit_008_canonical_state_contract_available",
    "admit_008_independent_semantic_oracle_available",
    "admit_008_standalone_evaluator_preconditions_complete",
    "ready_for_admit_008_standalone_evaluator_interface_implementation",
    "admit_008_standalone_evaluator_implemented",
    "admit_008_unified_adapter_contract_frozen", "admit_008_unified_adapter_implemented",
    "admit_008_registered_in_engine", "admit_009_standalone_evaluator_implemented",
    "admit_009_to_015_registered_in_engine", "all_15_rules_covered",
    "evaluate_all_rules_implemented", "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented", "cross_rule_precedence_frozen",
    "real_provider_topology_disposition_mapping_validated", "real_candidate_evaluation",
    "exact11_real_rows_evaluated", "ready_for_bulk_download_now", "ready_for_training",
    "ready_to_train_now",
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
    if base.returncode != 0:
        raise ValueError("expected base commit object is missing")
    if subject.returncode != 0 or subject.stdout.strip() != EXPECTED_BASE_SUBJECT:
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
    """Complete every structural check before any explicit source-byte read."""
    if len(SOURCE_PATHS) != 15 or len(set(SOURCE_PATHS)) != 15 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact15 source boundary shape invalid")
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
        expected = SOURCE_SHA256[path]
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, expected, base_sha, filesystem_sha, filesystem_bytes))
    snapshot = FrozenSourceSnapshot(tuple(records))
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("frozen source snapshot invalid")
    return snapshot


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot and len(value.records) == 15
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
    runtime_manifest = _json(snapshot, RUNTIME_MANIFEST_PATH)
    runtime_issues = _csv_rows(snapshot, RUNTIME_ISSUE_PATH)
    design_rule = _one(_csv_rows(snapshot, RULE_REGISTRY_PATH), "admission_rule_id", "ADMIT_008")
    schema_field = _one(_csv_rows(snapshot, SCHEMA_CONTRACT_PATH), "admission_field_name", "topology_restoration_disposition")
    field = _one(_csv_rows(snapshot, FIELD_SEMANTICS_PATH), "field_name", "topology_restoration_disposition")
    executable = _one(_csv_rows(snapshot, RULE_EXECUTABILITY_PATH), "admission_rule_id", "ADMIT_008")
    implementation_issue = _one(_csv_rows(snapshot, IMPLEMENTATION_ISSUE_PATH), "issue_id", PRIMARY_BLOCKER)
    runtime_issue = _one(runtime_issues, "issue_id", PRIMARY_BLOCKER)
    coverage = _one(runtime_issues, "issue_id", "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    rules = _csv_rows(snapshot, RESTORATION_RULE_PATH)
    candidates = _csv_rows(snapshot, CANDIDATE_CONTRACT_PATH)
    decisions = _csv_rows(snapshot, REVIEW_DECISION_PATH)
    step13m = _json(snapshot, STEP13M_MANIFEST_PATH)
    step13n = _json(snapshot, STEP13N_MANIFEST_PATH)
    required = (
        design_rule["admission_rule_name"] == "topology_restoration_disposition",
        design_rule["evidence_source"] == "approved_template_or_manual_review",
        design_rule["required_status"] == "approved_or_manual_review",
        design_rule["blocking_reason"] == "topology_restoration_unapproved",
        design_rule["evaluation_phase"] == "pre_download",
        schema_field["value_contract"] == "approved template or explicit manual review",
        field["candidate_record_field"] == "true" and field["dependent_rules"] == "ADMIT_008",
        field["allowed_values_defined"] == field["normalization_defined"] == field["exact_validation_defined"] == "false",
        field["implementation_semantics_complete"] == "false" and field["blocking_reasons"] == PRIMARY_BLOCKER,
        executable["candidate_field_dependencies"] == "topology_restoration_disposition",
        executable["evaluation_context_dependencies"] == "allowed_topology_restoration_dispositions",
        executable["semantics_complete"] == executable["deterministic_evaluation_possible_now"] == "false",
        implementation_issue["status"] == "open" and runtime_issue["status"] == "open",
        runtime_issue["affected_fields"] == "topology_restoration_disposition" and runtime_issue["affected_rules"] == "ADMIT_008",
        runtime_issue["blocking_scope"] == "admission_evaluator_rule_logic" and runtime_issue["integration_transition"] == "unchanged_open",
        coverage["affected_rules"].split("|")[0] == "ADMIT_008",
        len(runtime_issues) == 11 and runtime_manifest["admit_008_standalone_evaluator_implemented"] is False,
        len(rules) == 7 and len(candidates) == 3 and len(decisions) == 8,
        step13m["topology_schema_residue_agnostic"] is True,
        step13m["restoration_rules_residue_warhead_specific"] is True,
        step13m["unknown_residue_warhead_pair_quarantined"] is True,
        step13m["manual_visual_review_required_for_new_restoration_rule"] is True,
        step13m["ready_to_train_now"] is False,
        step13n["topology_smoke_must_not_auto_restore_ligand"] is True,
        step13n["topology_smoke_must_not_generalize_to_non_cys"] is True,
        step13n["topology_smoke_must_not_claim_training_ready"] is True,
        step13n["feature_semantics_audit_required_before_training"] is True,
    )
    if not all(required):
        raise ValueError("authoritative predecessor contract mismatch")


def _precondition_rows() -> tuple[dict[str, str], ...]:
    specs = (
        ("admission_rule_identity", "ADMIT_008 identity, name, phase, historical evidence/status/reason", "ADMIT_008 topology_restoration_disposition; pre_download; historical policy phrases frozen", "rule registry", True, "", "identity frozen"),
        ("candidate_field_name", "formal candidate field name", "topology_restoration_disposition is required pre-download candidate field", "schema and field matrices", True, "", "field name frozen"),
        ("standalone_input_projection", "standalone direct-scalar projection", "candidate-record dependency exists; standalone scalar interface is not declared", "field and executability matrices", False, PRIMARY_BLOCKER, "design enum/interface contract first"),
        ("scalar_exact_type", "exact scalar type", "no built-in str, enum-token, or structured-record type is frozen", "field semantics matrix", False, PRIMARY_BLOCKER, "freeze scalar type"),
        ("null_empty_missing_boundary", "None, exact empty, and missing-key classifications", "no ADMIT_008 boundary or adapter ownership is frozen", "fixed source boundary", False, PRIMARY_BLOCKER, "freeze null/empty/missing contract"),
        ("canonicalization_policy", "trim, case, alias, canonicalization, and repair policy", "normalization_defined=false; no alias or repair contract", "field semantics matrix", False, PRIMARY_BLOCKER, "freeze canonicalization policy"),
        ("canonical_disposition_enum", "exact ordered canonical disposition members and syntax", "allowed_values_defined=false; issue remains open", "field semantics and Exact11 issues", False, PRIMARY_BLOCKER, "design canonical enum contract"),
        ("approved_template_category", "exact approved-template scalar and outcome", "approved-template policy exists but no candidate scalar member is declared", "admission and Step13M policy", False, PRIMARY_BLOCKER, "freeze approved-template mapping"),
        ("explicit_manual_review_category", "exact explicit-manual-review scalar and outcome", "manual-review policy exists but no candidate scalar member is declared", "admission and Step13M/N policy", False, PRIMARY_BLOCKER, "freeze manual-review mapping"),
        ("unapproved_unknown_quarantine_categories", "exact unapproved, unknown, quarantine, deferred and N/A mapping", "quarantine/deferred policy exists without scalar members or category collapse rules", "Step13M/N policy", False, PRIMARY_BLOCKER, "freeze remaining category mapping"),
        ("restoration_rule_provenance_coherence", "disposition-to-rule/provenance/current-sample/quarantine coherence", "separate policy fields exist; no unified coherence contract", "Step13M candidate and rule contracts", False, PRIMARY_BLOCKER, "freeze provenance coherence"),
        ("outcome_vocabulary", "passed, blocked, invalid classification for every class", "generic runtime outcomes exist but ADMIT_008 mapping is not frozen", "Exact7 runtime and topology policy", False, PRIMARY_BLOCKER, "freeze ADMIT_008 outcomes"),
        ("reason_vocabulary", "formal uppercase reason for every non-pass outcome", "historical lowercase blocking reason only; no formal reason vocabulary", "admission rule registry", False, PRIMARY_BLOCKER, "freeze formal reasons"),
        ("canonical_validated_state", "canonical and validated state on blocked/invalid paths", "no ADMIT_008 state-retention contract", "fixed source boundary", False, PRIMARY_BLOCKER, "freeze result state"),
        ("runtime_context_dependency", "standalone-versus-context dependency and exact context contract", "allowed_topology_restoration_dispositions is named but undefined", "rule executability matrix", False, PRIMARY_BLOCKER, "freeze context ownership"),
        ("independent_semantic_oracle", "independent pure full-input outcome/reason/state oracle", "Step13M/N builders are policy builders, not an ADMIT_008 semantic oracle", "Step13M/N sources", False, PRIMARY_BLOCKER, "design an independent oracle"),
        ("real_provider_values", "committed real provider scalar values and mapping", "no real topology_restoration_disposition values in fixed metadata boundary", "vocabulary inventory", False, "REAL_PROVIDER_TOPOLOGY_DISPOSITION_MAPPING_UNVALIDATED", "validate only after contract and authorization"),
        ("real_candidate_authorization", "explicit authorization for real candidate evaluation", "audit is metadata-only and real evaluation is prohibited", "stop boundary", False, "REAL_CANDIDATE_EVALUATION_NOT_AUTHORIZED", "remain metadata-only"),
        ("bulk_download_readiness", "all rule coverage, aggregation, provider, raw and download gates", "coverage begins at ADMIT_008; aggregation/provider and other blockers remain open", "Exact11 issues", False, "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE", "bulk download remains prohibited"),
        ("training_readiness", "feature-semantics audit and all training gates", "Step12D is smoke legality only; feature semantics audit remains mandatory", "Step13M/N manifests", False, "FEATURE_SEMANTICS_AUDIT_REQUIRED", "training remains prohibited"),
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
        (RULE_REGISTRY_PATH, "ADMIT_008.evidence_source", "approved_template_or_manual_review", "historical evidence-source description", "admission_evidence_source_phrase"),
        (RULE_REGISTRY_PATH, "ADMIT_008.required_status", "approved_or_manual_review", "historical required-status description", "admission_required_status_phrase"),
        (RULE_REGISTRY_PATH, "ADMIT_008.blocking_reason", "topology_restoration_unapproved", "historical lowercase blocking reason", "historical_blocking_reason"),
        (RESTORATION_RULE_PATH, "CYS rule_id", "CYS_SG_ACRYLAMIDE_LIKE_STEP8_MANUAL_REVIEWED_V1", "restoration rule identity", "restoration_rule_id"),
        (RESTORATION_RULE_PATH, "unknown rule_id", "UNKNOWN_RESIDUE_WARHEAD_PAIR_QUARANTINE", "quarantine rule identity", "restoration_rule_id"),
        (RESTORATION_RULE_PATH, "SER rule_id", "SER_OG_DEFERRED_MANUAL_REVIEW_REQUIRED", "deferred rule identity", "restoration_rule_id"),
        (RESTORATION_RULE_PATH, "LYS rule_id", "LYS_NZ_DEFERRED_MANUAL_REVIEW_REQUIRED", "deferred rule identity", "restoration_rule_id"),
        (RESTORATION_RULE_PATH, "TYR rule_id", "TYR_OH_DEFERRED_MANUAL_REVIEW_REQUIRED", "deferred rule identity", "restoration_rule_id"),
        (RESTORATION_RULE_PATH, "THR rule_id", "THR_OG1_DEFERRED_MANUAL_REVIEW_REQUIRED", "deferred rule identity", "restoration_rule_id"),
        (RESTORATION_RULE_PATH, "HIS rule_id", "HIS_NE2_DEFERRED_MANUAL_REVIEW_REQUIRED", "deferred rule identity", "restoration_rule_id"),
        (RESTORATION_RULE_PATH, "CYS scope", "current_cys_sg_golden_samples_only", "validated rule scope", "restoration_rule_scope"),
        (RESTORATION_RULE_PATH, "unknown scope", "quarantine_only", "quarantine rule scope", "restoration_rule_scope"),
        (RESTORATION_RULE_PATH, "deferred scope", "deferred_not_v1_train_ready", "deferred rule scope", "restoration_rule_scope"),
        (RESTORATION_RULE_PATH, "CYS source", "step8_manual_reviewed_pre_reaction_sdf_and_graph_preview", "manual-review provenance source", "restoration_rule_source"),
        (RESTORATION_RULE_PATH, "unknown source", "no_validated_restoration_rule", "absence-of-rule source marker", "restoration_rule_source"),
        (RESTORATION_RULE_PATH, "deferred source", "future_manual_visual_review_required", "future manual-review policy", "manual_review_policy"),
        (CANDIDATE_CONTRACT_PATH, "observed_topology_design_status", "policy_defined_no_ligand_topology_table_written", "observed-topology design status", "policy_status"),
        (CANDIDATE_CONTRACT_PATH, "training_ready_reason", "design_gate_only_no_ligand_topology_table_written", "training boundary reason", "training_status"),
        (REVIEW_DECISION_PATH, "decision", "accepted", "policy review decision", "review_decision"),
        (REVIEW_DECISION_PATH, "training_use_status", "not_training_input_yet", "review-stage training status", "training_status"),
        (STEP13M_MANIFEST_PATH, "v1_train_ready_scope", "cys_sg_with_known_restoration_template_only", "narrow policy scope", "restoration_rule_scope"),
        (STEP13N_MANIFEST_PATH, "topology_smoke_input_source_policy", "use_step8_manual_reviewed_pre_reaction_provenance_or_existing_graph_preview_only", "topology smoke source policy", "policy_status"),
    )
    return tuple({
        "vocabulary_order": str(index), "source_relative_path": path.as_posix(),
        "source_sha256": SOURCE_SHA256[path], "source_kind": _source_kind(path),
        "symbol_or_row_id": symbol, "observed_string": value, "observed_role": role,
        "semantic_category": category, "candidate_scalar_value_explicitly_declared": "false",
        "canonical_enum_member_explicitly_declared": "false",
        "safe_to_promote_to_canonical_enum_now": "false", "promotion_blocker": PRIMARY_BLOCKER,
        "inventory_passed": "true",
    } for index, (path, symbol, value, role, category) in enumerate(specs, 1))


def _occurrence_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    statements = {
        "ADMIT_008": ("admission rule identity or coverage reference", "ADMIT_008", "identity authoritative only where declared; not enum semantics"),
        "topology_restoration_disposition": ("candidate field reference", "ADMIT_008", "field name is frozen; scalar semantics are not"),
        "approved_template_or_manual_review": ("historical evidence-source phrase", "ADMIT_008", "high-level evidence phrase is not a canonical scalar member"),
        "approved_or_manual_review": ("historical required-status phrase", "ADMIT_008", "high-level status phrase is not a canonical scalar member"),
        "topology_restoration_unapproved": ("historical blocking reason", "ADMIT_008", "lowercase historical reason is not a formal reason vocabulary"),
        PRIMARY_BLOCKER: ("open semantics blocker", "ADMIT_008", "canonical disposition enum remains unresolved"),
    }
    rows: list[dict[str, str]] = []
    for record in snapshot.records:
        text = record.content_bytes.decode("utf-8")
        for line_number, line in enumerate(text.splitlines(), 1):
            for term in MATCH_TERMS:
                if term not in line:
                    continue
                role, scope, statement = statements.get(term, (
                    "topology policy evidence", "Step13M/Step13N policy scope",
                    "policy evidence constrains safety but does not freeze the candidate scalar interface",
                ))
                authoritative = (
                    term in ("ADMIT_008", "topology_restoration_disposition")
                    and record.relative_path in (RULE_REGISTRY_PATH, SCHEMA_CONTRACT_PATH, FIELD_SEMANTICS_PATH, RULE_EXECUTABILITY_PATH)
                )
                rows.append({
                    "occurrence_order": str(len(rows) + 1),
                    "source_relative_path": record.relative_path.as_posix(),
                    "source_sha256": record.expected_sha256, "source_kind": _source_kind(record.relative_path),
                    "symbol_or_row_id": f"line_{line_number}", "matched_term": term,
                    "field_role": role, "rule_scope": scope, "semantic_statement": statement,
                    "authoritative_for_admit008_formal_semantics": _bool(authoritative),
                    "occurrence_passed": "true",
                })
    if {row["matched_term"] for row in rows} != set(MATCH_TERMS):
        raise ValueError("field occurrence coverage incomplete")
    return tuple(rows)


def _source_boundary_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    return tuple({
        "source_order": str(index), "source_relative_path": record.relative_path.as_posix(),
        "source_kind": _source_kind(record.relative_path),
        "boundary_necessity": "minimal committed evidence for identity, unresolved formal semantics, policy safety, or issue preservation",
        "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true", "non_symlink": "true",
        "expected_sha256": record.expected_sha256, "base_tree_sha256": record.base_tree_sha256,
        "filesystem_sha256": record.filesystem_sha256, "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot.records, 1))


def _readiness() -> dict[str, bool]:
    return {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def build_audit_state(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root)
    _validate_predecessors(snapshot)
    issue_bytes = _record(snapshot, RUNTIME_ISSUE_PATH).content_bytes
    issue_rows = _csv_rows(snapshot, RUNTIME_ISSUE_PATH)
    return {
        "snapshot": snapshot, "precondition_rows": _precondition_rows(),
        "vocabulary_rows": _vocabulary_rows(), "occurrence_rows": _occurrence_rows(snapshot),
        "source_rows": _source_boundary_rows(snapshot), "issue_rows": issue_rows,
        "issue_bytes": issue_bytes, "readiness": _readiness(),
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
        "admission_rule_id": "ADMIT_008", "admission_rule_name": "topology_restoration_disposition",
        "candidate_field": "topology_restoration_disposition", "evaluation_phase": "pre_download",
        "historical_evidence_source": "approved_template_or_manual_review",
        "historical_required_status": "approved_or_manual_review",
        "historical_blocking_reason": "topology_restoration_unapproved",
        "source_boundary_name": "fixed_ordered_minimal_exact15_committed_source_boundary",
        "source_input_count": len(SOURCE_PATHS), "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [{
            "source_order": int(row["source_order"]), "source_relative_path": row["source_relative_path"],
            "expected_sha256": row["expected_sha256"], "base_tree_sha256": row["base_tree_sha256"],
            "filesystem_sha256": row["filesystem_sha256"], "tracked": True, "base_tree_blob": True,
            "filesystem_regular": True, "non_symlink": True, "source_verified": True,
        } for row in state["source_rows"]],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "precondition_row_count": len(preconditions), "precondition_pass_count": len(preconditions),
        "semantics_complete_count": sum(row["semantics_complete"] == "true" for row in preconditions),
        "semantics_incomplete_count": sum(row["semantics_complete"] == "false" for row in preconditions),
        "vocabulary_inventory_row_count": len(state["vocabulary_rows"]),
        "field_occurrence_inventory_row_count": len(state["occurrence_rows"]),
        "real_provider_value_count": 0,
        "high_level_policy_evidence": {
            "topology_schema_residue_agnostic": True,
            "restoration_rules_residue_warhead_specific": True,
            "current_v1_scope_current_cys_sg_golden_samples_only": True,
            "current_cys_rule_has_manual_review_provenance": True,
            "unknown_residue_warhead_pair_quarantined": True,
            "new_residue_auto_generalization_forbidden": True,
            "new_warhead_auto_generalization_forbidden": True,
            "new_rule_manual_visual_review_required": True,
            "topology_smoke_must_not_auto_restore_ligand": True,
            "topology_smoke_must_not_claim_training_ready": True,
            "feature_semantics_audit_required_before_training": True,
        },
        "unresolved_semantic_areas": [
            "standalone_input_projection", "scalar_exact_type", "null_empty_missing_boundary",
            "canonicalization_policy", "canonical_disposition_enum", "category_mapping",
            "restoration_rule_provenance_coherence", "outcome_vocabulary", "reason_vocabulary",
            "canonical_validated_state", "runtime_context_dependency", "independent_semantic_oracle",
            "real_provider_mapping",
        ],
        "blocker_ids": [PRIMARY_BLOCKER, "REAL_PROVIDER_TOPOLOGY_DISPOSITION_MAPPING_UNVALIDATED", "REAL_CANDIDATE_EVALUATION_NOT_AUTHORIZED", "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE", "FEATURE_SEMANTICS_AUDIT_REQUIRED"],
        "issue_inventory_row_count": len(state["issue_rows"]),
        "issue_inventory_byte_identical_to_exact7_predecessor": True,
        "topology_disposition_enum_issue_status": "open",
        "coverage_issue_starts_with_admit_008": True,
        "readiness": readiness,
        "output_file_count": 6, "output_files": list(OUTPUT_FILES),
        "output_sha256": dict(output_sha256), "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "no_topology_disposition_enum", "no_evaluate_admit_008", "no_Admit008EvaluationResult",
            "no_adapter", "no_exact8_runtime", "no_issue_transition", "no_real_provider_values",
            "no_real_candidate_evaluation", "no_raw_or_network", "no_training",
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


def run_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1(
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
    result = run_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1()
    manifest = result["manifest"]
    if manifest["ready_for_admit_008_standalone_evaluator_interface_implementation"]:
        raise AssertionError("ADMIT_008 evaluator readiness must remain false")
    if not manifest["ready_for_admit_008_topology_restoration_disposition_enum_contract_design"]:
        raise AssertionError("enum contract design readiness must be true")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
