#!/usr/bin/env python3
"""Independent checker for the ADMIT_008 evaluator-precondition audit v1."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit as gate,
)


# Every expectation below is checker-owned. Production builders and production
# constants are used only for the final equivalence cross-check.
EXPECTED_BASE_COMMIT = "5dd745ddb3e70d0a4150d2a54ca5531a63b83e9e"
EXPECTED_BASE_SUBJECT = "add CovaPIE unified admission runtime for ADMIT_001 to ADMIT_007 v1"
EXPECTED_RULE_ID = "ADMIT_008"
EXPECTED_RULE_NAME = "topology_restoration_disposition"
EXPECTED_FIELD = "topology_restoration_disposition"
EXPECTED_BLOCKER = "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"
EXPECTED_NEXT_STEP = "design_covapie_admit_008_topology_restoration_disposition_enum_contract_v1"
EXPECTED_STAGE = "covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1"
EXPECTED_OUTPUT_ROOT = Path("data/derived/covalent_small") / EXPECTED_STAGE

EXPECTED_FILES = (
    "covapie_admit_008_evaluator_precondition_matrix.csv",
    "covapie_admit_008_disposition_vocabulary_inventory.csv",
    "covapie_admit_008_field_occurrence_inventory.csv",
    "covapie_admit_008_source_boundary_audit.csv",
    "covapie_admit_008_issue_readiness_inventory.csv",
    "covapie_admit_008_formal_evaluator_preconditions_manifest.json",
)
EXPECTED_OUTPUT_SHA256 = {
    "covapie_admit_008_evaluator_precondition_matrix.csv": "8d9f0dca15b8c851787f3808498f811f72f73f07caa70f4a51b5c88aaf314455",
    "covapie_admit_008_disposition_vocabulary_inventory.csv": "45407488815876ebf2029027dcb42d65e3eeb18f53ece0b9f1454be10887ff71",
    "covapie_admit_008_field_occurrence_inventory.csv": "81e66d754444e4d7400ead64449b826d2e65cc23d4fbc7fa2515e21fc34d7e31",
    "covapie_admit_008_source_boundary_audit.csv": "c9a0a4ea8b16391270570695160a7af3a26cd453b088fd3bb28496c2894259a5",
    "covapie_admit_008_issue_readiness_inventory.csv": "47de07417697808b044d30260f153ec7e5d46fb7c5b0e2c1f41187bcb09b89a0",
    "covapie_admit_008_formal_evaluator_preconditions_manifest.json": "e93c43df4f64b6ce70c19c526546d3b1090c55f9150a944a76109ed0038cc136",
}

EXPECTED_SOURCE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_issue_inventory.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_implementation_issue_inventory.csv",
    "src/covalent_ext/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate.py",
    "data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0/covalent_restoration_rule_registry_contract.csv",
    "data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0/ligand_topology_restoration_candidate_contract.csv",
    "data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0/ligand_topology_restoration_policy_design_gate_manifest.json",
    "src/covalent_ext/real_covalent_confirmed_candidate_ligand_topology_policy_review_gate.py",
    "data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0/ligand_topology_policy_review_decision_contract.csv",
    "data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0/ligand_topology_policy_review_gate_manifest.json",
)
EXPECTED_SOURCE_SHA256 = dict(zip(EXPECTED_SOURCE_PATHS, (
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

PRECONDITION_HEADER = (
    "precondition_id", "semantic_area", "required_contract", "observed_contract",
    "source_evidence", "semantics_complete", "blocker_id",
    "implementation_disposition", "precondition_passed",
)
VOCABULARY_HEADER = (
    "vocabulary_order", "source_relative_path", "source_sha256", "source_kind",
    "symbol_or_row_id", "observed_string", "observed_role", "semantic_category",
    "candidate_scalar_value_explicitly_declared", "canonical_enum_member_explicitly_declared",
    "safe_to_promote_to_canonical_enum_now", "promotion_blocker", "inventory_passed",
)
OCCURRENCE_HEADER = (
    "occurrence_order", "source_relative_path", "source_sha256", "source_kind",
    "symbol_or_row_id", "matched_term", "field_role", "rule_scope",
    "semantic_statement", "authoritative_for_admit008_formal_semantics", "occurrence_passed",
)
SOURCE_HEADER = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256", "source_boundary_passed",
)
ISSUE_HEADER = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

MATCH_TERMS = (
    "ADMIT_008", "topology_restoration_disposition",
    "approved_template_or_manual_review", "approved_or_manual_review",
    "topology_restoration_unapproved", "restoration_rule_id", "restoration_rule_scope",
    "restoration_rule_source", "restoration_rule_validated_for_current_sample",
    "restoration_rule_validated_for_residue_warhead_class",
    "manual_visual_review_required_for_new_rule", "quarantine_if_restoration_rule_unknown",
    "unknown_residue_warhead_pair_quarantined", "topology_smoke_must_not_auto_restore_ligand",
    "topology_smoke_must_not_generalize_to_non_cys", "v1_train_ready_scope", EXPECTED_BLOCKER,
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


def _sha_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _git(arguments: Sequence[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT, text=text, capture_output=True, check=False
    )


def _source_kind(path: str) -> str:
    suffix = Path(path).suffix
    return "production_source" if suffix == ".py" else "committed_manifest" if suffix == ".json" else "committed_contract_csv"


def _csv(path: Path, header: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    assert tuple(reader.fieldnames or ()) == header
    rows = [dict(row) for row in reader]
    assert all(tuple(row) == header and all(value is not None for value in row.values()) for row in rows)
    return rows


def _read_verified_sources() -> dict[str, bytes]:
    subject = _git(["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"])
    assert subject.returncode == 0 and subject.stdout.strip() == EXPECTED_BASE_SUBJECT
    assert ancestor.returncode == 0
    for path in EXPECTED_SOURCE_PATHS:
        metadata = os.lstat(REPO_ROOT / path)
        tracked = _git(["ls-files", "--error-unmatch", "--", path])
        tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path])
        fields = tree.stdout.split("\t", 1)[0].split()
        assert tracked.returncode == 0 and tree.returncode == 0
        assert len(fields) == 3 and fields[0] in ("100644", "100755") and fields[1] == "blob"
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        assert not path.startswith("data/raw/") and not path.startswith("checkpoints/")
    result: dict[str, bytes] = {}
    for path in EXPECTED_SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path}"], text=False)
        assert base.returncode == 0 and type(base.stdout) is bytes
        filesystem = (REPO_ROOT / path).read_bytes()
        assert _sha_bytes(base.stdout) == _sha_bytes(filesystem) == EXPECTED_SOURCE_SHA256[path]
        result[path] = filesystem
    return result


def _expected_preconditions() -> list[dict[str, str]]:
    specs = (
        ("admission_rule_identity", "ADMIT_008 identity, name, phase, historical evidence/status/reason", "ADMIT_008 topology_restoration_disposition; pre_download; historical policy phrases frozen", "rule registry", True, "", "identity frozen"),
        ("candidate_field_name", "formal candidate field name", "topology_restoration_disposition is required pre-download candidate field", "schema and field matrices", True, "", "field name frozen"),
        ("standalone_input_projection", "standalone direct-scalar projection", "candidate-record dependency exists; standalone scalar interface is not declared", "field and executability matrices", False, EXPECTED_BLOCKER, "design enum/interface contract first"),
        ("scalar_exact_type", "exact scalar type", "no built-in str, enum-token, or structured-record type is frozen", "field semantics matrix", False, EXPECTED_BLOCKER, "freeze scalar type"),
        ("null_empty_missing_boundary", "None, exact empty, and missing-key classifications", "no ADMIT_008 boundary or adapter ownership is frozen", "fixed source boundary", False, EXPECTED_BLOCKER, "freeze null/empty/missing contract"),
        ("canonicalization_policy", "trim, case, alias, canonicalization, and repair policy", "normalization_defined=false; no alias or repair contract", "field semantics matrix", False, EXPECTED_BLOCKER, "freeze canonicalization policy"),
        ("canonical_disposition_enum", "exact ordered canonical disposition members and syntax", "allowed_values_defined=false; issue remains open", "field semantics and Exact11 issues", False, EXPECTED_BLOCKER, "design canonical enum contract"),
        ("approved_template_category", "exact approved-template scalar and outcome", "approved-template policy exists but no candidate scalar member is declared", "admission and Step13M policy", False, EXPECTED_BLOCKER, "freeze approved-template mapping"),
        ("explicit_manual_review_category", "exact explicit-manual-review scalar and outcome", "manual-review policy exists but no candidate scalar member is declared", "admission and Step13M/N policy", False, EXPECTED_BLOCKER, "freeze manual-review mapping"),
        ("unapproved_unknown_quarantine_categories", "exact unapproved, unknown, quarantine, deferred and N/A mapping", "quarantine/deferred policy exists without scalar members or category collapse rules", "Step13M/N policy", False, EXPECTED_BLOCKER, "freeze remaining category mapping"),
        ("restoration_rule_provenance_coherence", "disposition-to-rule/provenance/current-sample/quarantine coherence", "separate policy fields exist; no unified coherence contract", "Step13M candidate and rule contracts", False, EXPECTED_BLOCKER, "freeze provenance coherence"),
        ("outcome_vocabulary", "passed, blocked, invalid classification for every class", "generic runtime outcomes exist but ADMIT_008 mapping is not frozen", "Exact7 runtime and topology policy", False, EXPECTED_BLOCKER, "freeze ADMIT_008 outcomes"),
        ("reason_vocabulary", "formal uppercase reason for every non-pass outcome", "historical lowercase blocking reason only; no formal reason vocabulary", "admission rule registry", False, EXPECTED_BLOCKER, "freeze formal reasons"),
        ("canonical_validated_state", "canonical and validated state on blocked/invalid paths", "no ADMIT_008 state-retention contract", "fixed source boundary", False, EXPECTED_BLOCKER, "freeze result state"),
        ("runtime_context_dependency", "standalone-versus-context dependency and exact context contract", "allowed_topology_restoration_dispositions is named but undefined", "rule executability matrix", False, EXPECTED_BLOCKER, "freeze context ownership"),
        ("independent_semantic_oracle", "independent pure full-input outcome/reason/state oracle", "Step13M/N builders are policy builders, not an ADMIT_008 semantic oracle", "Step13M/N sources", False, EXPECTED_BLOCKER, "design an independent oracle"),
        ("real_provider_values", "committed real provider scalar values and mapping", "no real topology_restoration_disposition values in fixed metadata boundary", "vocabulary inventory", False, "REAL_PROVIDER_TOPOLOGY_DISPOSITION_MAPPING_UNVALIDATED", "validate only after contract and authorization"),
        ("real_candidate_authorization", "explicit authorization for real candidate evaluation", "audit is metadata-only and real evaluation is prohibited", "stop boundary", False, "REAL_CANDIDATE_EVALUATION_NOT_AUTHORIZED", "remain metadata-only"),
        ("bulk_download_readiness", "all rule coverage, aggregation, provider, raw and download gates", "coverage begins at ADMIT_008; aggregation/provider and other blockers remain open", "Exact11 issues", False, "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE", "bulk download remains prohibited"),
        ("training_readiness", "feature-semantics audit and all training gates", "Step12D is smoke legality only; feature semantics audit remains mandatory", "Step13M/N manifests", False, "FEATURE_SEMANTICS_AUDIT_REQUIRED", "training remains prohibited"),
    )
    return [{
        "precondition_id": f"PRE_{index:03d}", "semantic_area": area,
        "required_contract": required, "observed_contract": observed,
        "source_evidence": evidence, "semantics_complete": str(complete).lower(),
        "blocker_id": blocker, "implementation_disposition": disposition,
        "precondition_passed": "true",
    } for index, (area, required, observed, evidence, complete, blocker, disposition) in enumerate(specs, 1)]


def _expected_vocabulary() -> list[dict[str, str]]:
    rule = EXPECTED_SOURCE_PATHS[3]
    restoration = EXPECTED_SOURCE_PATHS[9]
    candidate = EXPECTED_SOURCE_PATHS[10]
    step13m = EXPECTED_SOURCE_PATHS[11]
    decision = EXPECTED_SOURCE_PATHS[13]
    step13n = EXPECTED_SOURCE_PATHS[14]
    specs = (
        (rule, "ADMIT_008.evidence_source", "approved_template_or_manual_review", "historical evidence-source description", "admission_evidence_source_phrase"),
        (rule, "ADMIT_008.required_status", "approved_or_manual_review", "historical required-status description", "admission_required_status_phrase"),
        (rule, "ADMIT_008.blocking_reason", "topology_restoration_unapproved", "historical lowercase blocking reason", "historical_blocking_reason"),
        (restoration, "CYS rule_id", "CYS_SG_ACRYLAMIDE_LIKE_STEP8_MANUAL_REVIEWED_V1", "restoration rule identity", "restoration_rule_id"),
        (restoration, "unknown rule_id", "UNKNOWN_RESIDUE_WARHEAD_PAIR_QUARANTINE", "quarantine rule identity", "restoration_rule_id"),
        (restoration, "SER rule_id", "SER_OG_DEFERRED_MANUAL_REVIEW_REQUIRED", "deferred rule identity", "restoration_rule_id"),
        (restoration, "LYS rule_id", "LYS_NZ_DEFERRED_MANUAL_REVIEW_REQUIRED", "deferred rule identity", "restoration_rule_id"),
        (restoration, "TYR rule_id", "TYR_OH_DEFERRED_MANUAL_REVIEW_REQUIRED", "deferred rule identity", "restoration_rule_id"),
        (restoration, "THR rule_id", "THR_OG1_DEFERRED_MANUAL_REVIEW_REQUIRED", "deferred rule identity", "restoration_rule_id"),
        (restoration, "HIS rule_id", "HIS_NE2_DEFERRED_MANUAL_REVIEW_REQUIRED", "deferred rule identity", "restoration_rule_id"),
        (restoration, "CYS scope", "current_cys_sg_golden_samples_only", "validated rule scope", "restoration_rule_scope"),
        (restoration, "unknown scope", "quarantine_only", "quarantine rule scope", "restoration_rule_scope"),
        (restoration, "deferred scope", "deferred_not_v1_train_ready", "deferred rule scope", "restoration_rule_scope"),
        (restoration, "CYS source", "step8_manual_reviewed_pre_reaction_sdf_and_graph_preview", "manual-review provenance source", "restoration_rule_source"),
        (restoration, "unknown source", "no_validated_restoration_rule", "absence-of-rule source marker", "restoration_rule_source"),
        (restoration, "deferred source", "future_manual_visual_review_required", "future manual-review policy", "manual_review_policy"),
        (candidate, "observed_topology_design_status", "policy_defined_no_ligand_topology_table_written", "observed-topology design status", "policy_status"),
        (candidate, "training_ready_reason", "design_gate_only_no_ligand_topology_table_written", "training boundary reason", "training_status"),
        (decision, "decision", "accepted", "policy review decision", "review_decision"),
        (decision, "training_use_status", "not_training_input_yet", "review-stage training status", "training_status"),
        (step13m, "v1_train_ready_scope", "cys_sg_with_known_restoration_template_only", "narrow policy scope", "restoration_rule_scope"),
        (step13n, "topology_smoke_input_source_policy", "use_step8_manual_reviewed_pre_reaction_provenance_or_existing_graph_preview_only", "topology smoke source policy", "policy_status"),
    )
    return [{
        "vocabulary_order": str(index), "source_relative_path": path,
        "source_sha256": EXPECTED_SOURCE_SHA256[path], "source_kind": _source_kind(path),
        "symbol_or_row_id": symbol, "observed_string": value, "observed_role": role,
        "semantic_category": category, "candidate_scalar_value_explicitly_declared": "false",
        "canonical_enum_member_explicitly_declared": "false",
        "safe_to_promote_to_canonical_enum_now": "false",
        "promotion_blocker": EXPECTED_BLOCKER, "inventory_passed": "true",
    } for index, (path, symbol, value, role, category) in enumerate(specs, 1)]


def _expected_occurrences(sources: Mapping[str, bytes]) -> list[dict[str, str]]:
    statements = {
        "ADMIT_008": ("admission rule identity or coverage reference", "ADMIT_008", "identity authoritative only where declared; not enum semantics"),
        "topology_restoration_disposition": ("candidate field reference", "ADMIT_008", "field name is frozen; scalar semantics are not"),
        "approved_template_or_manual_review": ("historical evidence-source phrase", "ADMIT_008", "high-level evidence phrase is not a canonical scalar member"),
        "approved_or_manual_review": ("historical required-status phrase", "ADMIT_008", "high-level status phrase is not a canonical scalar member"),
        "topology_restoration_unapproved": ("historical blocking reason", "ADMIT_008", "lowercase historical reason is not a formal reason vocabulary"),
        EXPECTED_BLOCKER: ("open semantics blocker", "ADMIT_008", "canonical disposition enum remains unresolved"),
    }
    authoritative_paths = set(EXPECTED_SOURCE_PATHS[3:7])
    rows: list[dict[str, str]] = []
    for path in EXPECTED_SOURCE_PATHS:
        for line_number, line in enumerate(sources[path].decode("utf-8").splitlines(), 1):
            for term in MATCH_TERMS:
                if term not in line:
                    continue
                role, scope, statement = statements.get(term, (
                    "topology policy evidence", "Step13M/Step13N policy scope",
                    "policy evidence constrains safety but does not freeze the candidate scalar interface",
                ))
                authoritative = term in ("ADMIT_008", EXPECTED_FIELD) and path in authoritative_paths
                rows.append({
                    "occurrence_order": str(len(rows) + 1), "source_relative_path": path,
                    "source_sha256": EXPECTED_SOURCE_SHA256[path], "source_kind": _source_kind(path),
                    "symbol_or_row_id": f"line_{line_number}", "matched_term": term,
                    "field_role": role, "rule_scope": scope, "semantic_statement": statement,
                    "authoritative_for_admit008_formal_semantics": str(authoritative).lower(),
                    "occurrence_passed": "true",
                })
    assert {row["matched_term"] for row in rows} == set(MATCH_TERMS)
    return rows


def _expected_source_rows() -> list[dict[str, str]]:
    return [{
        "source_order": str(index), "source_relative_path": path,
        "source_kind": _source_kind(path),
        "boundary_necessity": "minimal committed evidence for identity, unresolved formal semantics, policy safety, or issue preservation",
        "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true",
        "non_symlink": "true", "expected_sha256": EXPECTED_SOURCE_SHA256[path],
        "base_tree_sha256": EXPECTED_SOURCE_SHA256[path],
        "filesystem_sha256": EXPECTED_SOURCE_SHA256[path], "source_boundary_passed": "true",
    } for index, path in enumerate(EXPECTED_SOURCE_PATHS, 1)]


def _readiness() -> dict[str, bool]:
    return {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def _expected_manifest(
    preconditions: list[dict[str, str]], vocabulary: list[dict[str, str]],
    occurrences: list[dict[str, str]], sources: list[dict[str, str]],
    issues: list[dict[str, str]], output_sha256: Mapping[str, str],
) -> dict[str, Any]:
    readiness = _readiness()
    manifest: dict[str, Any] = {
        "project": "CovaPIE", "step": "ADMIT_008 formal evaluator interface preconditions audit v1",
        "stage": EXPECTED_STAGE,
        "manifest_schema_version": "covapie_admit_008_formal_evaluator_preconditions_manifest_v1",
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": EXPECTED_RULE_ID, "admission_rule_name": EXPECTED_RULE_NAME,
        "candidate_field": EXPECTED_FIELD, "evaluation_phase": "pre_download",
        "historical_evidence_source": "approved_template_or_manual_review",
        "historical_required_status": "approved_or_manual_review",
        "historical_blocking_reason": "topology_restoration_unapproved",
        "source_boundary_name": "fixed_ordered_minimal_exact15_committed_source_boundary",
        "source_input_count": 15, "source_input_paths": list(EXPECTED_SOURCE_PATHS),
        "source_input_sha256": dict(EXPECTED_SOURCE_SHA256),
        "source_input_verification": [{
            "source_order": index, "source_relative_path": path,
            "expected_sha256": EXPECTED_SOURCE_SHA256[path],
            "base_tree_sha256": EXPECTED_SOURCE_SHA256[path],
            "filesystem_sha256": EXPECTED_SOURCE_SHA256[path], "tracked": True,
            "base_tree_blob": True, "filesystem_regular": True, "non_symlink": True,
            "source_verified": True,
        } for index, path in enumerate(EXPECTED_SOURCE_PATHS, 1)],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "precondition_row_count": 20, "precondition_pass_count": 20,
        "semantics_complete_count": 2, "semantics_incomplete_count": 18,
        "vocabulary_inventory_row_count": len(vocabulary),
        "field_occurrence_inventory_row_count": len(occurrences), "real_provider_value_count": 0,
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
        "blocker_ids": [
            EXPECTED_BLOCKER, "REAL_PROVIDER_TOPOLOGY_DISPOSITION_MAPPING_UNVALIDATED",
            "REAL_CANDIDATE_EVALUATION_NOT_AUTHORIZED", "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
            "FEATURE_SEMANTICS_AUDIT_REQUIRED",
        ],
        "issue_inventory_row_count": len(issues),
        "issue_inventory_byte_identical_to_exact7_predecessor": True,
        "topology_disposition_enum_issue_status": "open",
        "coverage_issue_starts_with_admit_008": True, "readiness": readiness,
        "output_file_count": 6, "output_files": list(EXPECTED_FILES),
        "output_sha256": dict(output_sha256), "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "no_topology_disposition_enum", "no_evaluate_admit_008", "no_Admit008EvaluationResult",
            "no_adapter", "no_exact8_runtime", "no_issue_transition", "no_real_provider_values",
            "no_real_candidate_evaluation", "no_raw_or_network", "no_training",
        ],
        "recommended_next_step": EXPECTED_NEXT_STEP,
        "all_source_boundary_checks_passed": True, "all_precondition_checks_passed": True,
        "all_vocabulary_inventory_checks_passed": True, "all_occurrence_checks_passed": True,
        "all_issue_checks_passed": True, "all_readiness_checks_passed": True,
        "all_attestations_passed": True, "validation_failures": [],
    }
    manifest.update(readiness)
    return manifest


def _validate_entries(root: Path) -> None:
    metadata = os.lstat(root)
    assert stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    assert tuple(sorted(path.name for path in root.iterdir())) == tuple(sorted(EXPECTED_FILES))
    for name in EXPECTED_FILES:
        metadata = os.lstat(root / name)
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)


def _validate_production_equivalence(root: Path) -> None:
    state = gate.build_audit_state()
    expected = {
        EXPECTED_FILES[0]: gate._csv_bytes(gate.PRECONDITION_COLUMNS, state["precondition_rows"]),
        EXPECTED_FILES[1]: gate._csv_bytes(gate.VOCABULARY_COLUMNS, state["vocabulary_rows"]),
        EXPECTED_FILES[2]: gate._csv_bytes(gate.OCCURRENCE_COLUMNS, state["occurrence_rows"]),
        EXPECTED_FILES[3]: gate._csv_bytes(gate.SOURCE_BOUNDARY_COLUMNS, state["source_rows"]),
        EXPECTED_FILES[4]: state["issue_bytes"],
    }
    assert all((root / name).read_bytes() == content for name, content in expected.items())


def _validate_disk(root: Path, *, enforce_frozen_hashes: bool = True) -> dict[str, Any]:
    _validate_entries(root)
    source_bytes = _read_verified_sources()
    preconditions = _csv(root / EXPECTED_FILES[0], PRECONDITION_HEADER)
    vocabulary = _csv(root / EXPECTED_FILES[1], VOCABULARY_HEADER)
    occurrences = _csv(root / EXPECTED_FILES[2], OCCURRENCE_HEADER)
    sources = _csv(root / EXPECTED_FILES[3], SOURCE_HEADER)
    issues = _csv(root / EXPECTED_FILES[4], ISSUE_HEADER)
    manifest = json.loads((root / EXPECTED_FILES[5]).read_text(encoding="utf-8"))
    assert type(manifest) is dict

    assert preconditions == _expected_preconditions()
    assert vocabulary == _expected_vocabulary()
    assert occurrences == _expected_occurrences(source_bytes)
    assert sources == _expected_source_rows()
    predecessor_issue_bytes = source_bytes[EXPECTED_SOURCE_PATHS[2]]
    assert (root / EXPECTED_FILES[4]).read_bytes() == predecessor_issue_bytes
    assert len(issues) == 11
    enum_issue = next(row for row in issues if row["issue_id"] == EXPECTED_BLOCKER)
    coverage = next(row for row in issues if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert enum_issue["status"] == "open" and enum_issue["affected_fields"] == EXPECTED_FIELD
    assert enum_issue["affected_rules"] == EXPECTED_RULE_ID and enum_issue["integration_transition"] == "unchanged_open"
    assert coverage["status"] == "open"
    assert coverage["affected_rules"] == "|".join(f"ADMIT_{index:03d}" for index in range(8, 16))
    assert coverage["integration_transition"] == "admit_007_implemented_and_removed_from_open_coverage_scope"
    output_sha = {name: _sha(root / name) for name in EXPECTED_FILES[:-1]}
    assert manifest == _expected_manifest(preconditions, vocabulary, occurrences, sources, issues, output_sha)
    serialized = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in serialized.lower() and "/home/" not in serialized
    _validate_production_equivalence(root)
    if enforce_frozen_hashes:
        assert {name: _sha(root / name) for name in EXPECTED_FILES} == EXPECTED_OUTPUT_SHA256
    return manifest


def _raises(function: Any, *args: Any, **kwargs: Any) -> None:
    try:
        function(*args, **kwargs)
    except (AssertionError, ValueError, FileNotFoundError):
        return
    raise AssertionError("expected fail-closed rejection")


def _refresh_hash(root: Path, name: str) -> None:
    path = root / EXPECTED_FILES[5]
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["output_sha256"][name] = _sha(root / name)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _negative_checks(root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="covapie_admit008_checker_") as temporary:
        temp = Path(temporary)
        promoted = temp / "promoted"
        shutil.copytree(root, promoted)
        path = promoted / EXPECTED_FILES[1]
        text = path.read_text(encoding="utf-8").replace(
            "admission_evidence_source_phrase,false,false,false",
            "admission_evidence_source_phrase,true,true,true", 1,
        )
        path.write_text(text, encoding="utf-8")
        _refresh_hash(promoted, EXPECTED_FILES[1])
        _raises(_validate_disk, promoted, enforce_frozen_hashes=False)

        overclaim = temp / "overclaim"
        shutil.copytree(root, overclaim)
        path = overclaim / EXPECTED_FILES[5]
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["ready_for_admit_008_standalone_evaluator_interface_implementation"] = True
        manifest["readiness"]["ready_for_admit_008_standalone_evaluator_interface_implementation"] = True
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _raises(_validate_disk, overclaim, enforce_frozen_hashes=False)

        extra = temp / "extra"
        shutil.copytree(root, extra)
        (extra / "unexpected.txt").write_text("unexpected", encoding="utf-8")
        _raises(_validate_disk, extra, enforce_frozen_hashes=False)


def main() -> int:
    root = REPO_ROOT / EXPECTED_OUTPUT_ROOT
    first = gate.run_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1(root)
    first_hashes = {name: _sha(root / name) for name in EXPECTED_FILES}
    second = gate.run_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1(root)
    second_hashes = {name: _sha(root / name) for name in EXPECTED_FILES}
    assert first["manifest"] == second["manifest"] and first_hashes == second_hashes
    manifest = _validate_disk(root)
    _negative_checks(root)
    print(f"stage={EXPECTED_STAGE}")
    print("all_checks_passed=true")
    print("source_boundary_exact15=true")
    print("precondition_exact20_passed=true")
    print("semantics_complete_count=2")
    print("semantics_incomplete_count=18")
    print(f"vocabulary_inventory_row_count={manifest['vocabulary_inventory_row_count']}")
    print(f"field_occurrence_inventory_row_count={manifest['field_occurrence_inventory_row_count']}")
    print("real_provider_value_count=0")
    print("issue_inventory_exact11_byte_identical=true")
    print("topology_disposition_enum_issue_status=open")
    print("ready_for_admit_008_standalone_evaluator_interface_implementation=false")
    print("ready_for_admit_008_topology_restoration_disposition_enum_contract_design=true")
    print(f"recommended_next_step={EXPECTED_NEXT_STEP}")
    print("outputs_byte_identical=true")
    print("covapie_admit_008_formal_evaluator_interface_preconditions_audit_v1_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
