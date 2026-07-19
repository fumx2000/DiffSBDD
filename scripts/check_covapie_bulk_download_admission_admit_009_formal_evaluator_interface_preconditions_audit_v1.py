#!/usr/bin/env python3
"""Independent checker for the ADMIT_009 evaluator-precondition audit v1."""

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
    covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit as gate,
)


EXPECTED_BASE_COMMIT = "8215c99edc93b4dcf50da87139917fae9ec46cc5"
EXPECTED_BASE_SUBJECT = "add CovaPIE unified admission runtime for ADMIT_001 to ADMIT_008 v1"
EXPECTED_RULE_ID = "ADMIT_009"
EXPECTED_RULE_NAME = "duplicate_identity_precheck"
EXPECTED_FIELD = "duplicate_identity_key"
EXPECTED_BATCH_CONTEXT = "batch_duplicate_identity_keys"
EXPECTED_POLICY_CONTEXT = "duplicate_identity_key_contract"
EXPECTED_BLOCKER = "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"
EXPECTED_NEXT_STEP = "design_covapie_admit_009_duplicate_identity_key_contract_v1"
EXPECTED_STAGE = "covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1"
EXPECTED_OUTPUT_ROOT = Path("data/derived/covalent_small") / EXPECTED_STAGE
EXPECTED_FILES = (
    "covapie_admit_009_evaluator_precondition_matrix.csv",
    "covapie_admit_009_duplicate_identity_vocabulary_inventory.csv",
    "covapie_admit_009_field_occurrence_inventory.csv",
    "covapie_admit_009_source_boundary_audit.csv",
    "covapie_admit_009_issue_readiness_inventory.csv",
    "covapie_admit_009_formal_evaluator_preconditions_manifest.json",
)
EXPECTED_OUTPUT_SHA256 = {
    "covapie_admit_009_evaluator_precondition_matrix.csv": "f509c25ea5c9843da97cc0582189884b3df9074cbc209a8315e9695699739868",
    "covapie_admit_009_duplicate_identity_vocabulary_inventory.csv": "63126db3776eec209f2ea0f2517159889392762a89f609f246ba62ed3f6ac6cc",
    "covapie_admit_009_field_occurrence_inventory.csv": "feb35d0081c4489e6eb5900d72adc3458862f30195fc228a2806bda03d954e83",
    "covapie_admit_009_source_boundary_audit.csv": "a92dc8349722a3158ec4a3fc6b04eb86e95a2437f13c989c93679b7bff7e1065",
    "covapie_admit_009_issue_readiness_inventory.csv": "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128",
    "covapie_admit_009_formal_evaluator_preconditions_manifest.json": "5d1be882bc51c3fad5eefa5dc106dec43ba5842eda0696c06eb04473db33a37b",
}

EXPECTED_SOURCE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_issue_inventory.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_design_gate_manifest.json",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_implementation_issue_inventory.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1/covapie_candidate_record_id_semantics_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1/covapie_candidate_record_id_integrated_field_matrix.csv",
    "data/derived/covalent_small/covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke_v0/covapie_ligand_graph_scaffold_evidence.csv",
    "data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/covapie_final_leakage_group_assignment.csv",
    "data/derived/covalent_small/covapie_unified_leakage_split_materialization_smoke_v0/covapie_sample_split_assignment.csv",
    "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/covapie_final_dataset_membership.csv",
)
EXPECTED_SOURCE_SHA256 = dict(zip(EXPECTED_SOURCE_PATHS, (
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

PRECONDITION_HEADER = (
    "precondition_id", "semantic_area", "required_contract", "observed_contract",
    "source_evidence", "semantics_complete", "blocker_id",
    "implementation_disposition", "precondition_passed",
)
VOCABULARY_HEADER = (
    "vocabulary_order", "source_relative_path", "source_sha256", "source_kind",
    "symbol_or_row_id", "observed_term", "observed_role", "semantic_category",
    "explicitly_declared_duplicate_key", "explicitly_declared_duplicate_key_component",
    "exact_duplicate_equivalence_declared", "safe_to_use_in_duplicate_key_contract_now",
    "promotion_blocker", "inventory_passed",
)
OCCURRENCE_HEADER = (
    "occurrence_order", "source_relative_path", "source_sha256", "source_kind",
    "symbol_or_row_id", "matched_term", "field_role", "rule_scope",
    "semantic_statement", "authoritative_for_admit009_formal_semantics", "occurrence_passed",
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
    "ADMIT_009", "duplicate_identity_precheck", "duplicate_identity_key",
    "batch_duplicate_identity_keys", "duplicate_identity_key_contract",
    "duplicate_precheck_complete", "duplicate_identity_unresolved", EXPECTED_BLOCKER,
    "candidate_record_id", "leakage_group_id", "final_leakage_group_id",
    "ligand_graph_group_id", "ligand_scaffold_group_id", "sample_index_row_id",
    "assignment_id", "covalent_bond_atom_pair", "protein_exact_sequence_group_id",
)
TRUE_READINESS = (
    "admit_009_admission_rule_identity_available", "admit_009_evaluation_phase_available",
    "admit_009_candidate_field_identity_available", "admit_009_batch_context_dependency_available",
    "admit_009_evaluation_policy_item_available", "admit_009_pure_in_memory_interface_possible",
    "admit_009_duplicate_identity_semantics_gap_confirmed",
    "ready_for_admit_009_duplicate_identity_key_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_009_duplicate_key_exact_type_contract_available", "admit_009_duplicate_key_syntax_contract_available",
    "admit_009_duplicate_key_normalization_contract_available", "admit_009_duplicate_key_composition_contract_available",
    "admit_009_duplicate_equivalence_domain_contract_available", "admit_009_collision_handling_contract_available",
    "admit_009_batch_container_contract_available", "admit_009_batch_membership_semantics_contract_available",
    "admit_009_self_exclusion_contract_available", "admit_009_duplicate_vs_leakage_boundary_contract_available",
    "admit_009_reason_outcome_contract_available", "admit_009_canonical_state_contract_available",
    "admit_009_independent_semantic_oracle_available", "admit_009_standalone_evaluator_preconditions_complete",
    "ready_for_admit_009_standalone_evaluator_interface_implementation",
    "admit_009_standalone_evaluator_implemented", "admit_009_unified_adapter_contract_frozen",
    "admit_009_unified_adapter_implemented", "admit_009_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_009_implemented", "admit_010_standalone_evaluator_implemented",
    "admit_010_to_015_registered_in_engine", "all_15_rules_covered", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen", "real_provider_duplicate_identity_mapping_validated",
    "real_provider_duplicate_identity_key_count_nonzero", "real_candidate_evaluation",
    "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
)


def _sha_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _git(arguments: Sequence[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, text=text, capture_output=True, check=False)


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
    assert ancestor.returncode == 0 and len(EXPECTED_SOURCE_PATHS) == len(set(EXPECTED_SOURCE_PATHS)) == 17
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
        filesystem = (REPO_ROOT / path).read_bytes()
        assert base.returncode == 0 and type(base.stdout) is bytes
        assert _sha_bytes(base.stdout) == _sha_bytes(filesystem) == EXPECTED_SOURCE_SHA256[path]
        result[path] = filesystem
    return result


def _expected_preconditions() -> list[dict[str, str]]:
    specs = (
        ("admission_rule_identity", "ADMIT_009 identity and formal name", "ADMIT_009 duplicate_identity_precheck", "rule registry", True, "", "identity frozen"),
        ("evaluation_phase", "exact evaluation phase", "pre_download", "rule registry and executability matrix", True, "", "phase frozen"),
        ("candidate_field_name", "candidate field identity", "duplicate_identity_key", "schema and field matrices", True, "", "field identity frozen"),
        ("batch_context_item_name", "batch dependency identity", "batch_duplicate_identity_keys", "executability and context contracts", True, "", "dependency identity frozen"),
        ("evaluation_policy_item_name", "evaluation-policy dependency identity", "duplicate_identity_key_contract", "executability and context contracts", True, "", "dependency identity frozen"),
        ("pure_in_memory_interface_possible", "filesystem/network-free evaluator feasibility", "future caller supplies dependencies; evaluator IO is false", "executability and context contracts", True, "", "pure interface is feasible after contract design"),
        ("scalar_exact_type", "exact scalar type", "no exact str, tuple, record, or digest type is frozen", "field semantics and fixed boundary", False, EXPECTED_BLOCKER, "freeze exact type"),
        ("scalar_syntax_and_length", "syntax, length, charset, escaping", "no key grammar is frozen", "fixed boundary", False, EXPECTED_BLOCKER, "freeze key grammar"),
        ("normalization_and_canonicalization", "trim, case, Unicode, alias, repair policies", "normalization_defined=false; no alias or repair contract", "field semantics matrix", False, EXPECTED_BLOCKER, "freeze normalization"),
        ("duplicate_key_component_set", "exact candidate component set", "candidate, ligand, protein, residue, atom and group evidence exists without key promotion", "identity inventories", False, EXPECTED_BLOCKER, "design component contract"),
        ("component_order_and_encoding", "component order, names, version, separator and empty policy", "no ordering or encoding contract", "fixed boundary", False, EXPECTED_BLOCKER, "freeze encoding"),
        ("duplicate_equivalence_domain", "exact duplicate equivalence domain", "record, ligand, grouping, leakage and materialization identities remain distinct", "identity and leakage evidence", False, EXPECTED_BLOCKER, "freeze equivalence domain"),
        ("collision_handling", "hash/key collision and version mismatch policy", "no collision policy", "fixed boundary", False, EXPECTED_BLOCKER, "freeze collision handling"),
        ("batch_container_exact_type", "exact batch container type and mutation/copy policy", "dependency exists; list/tuple/set/frozenset is not selected", "evaluation context contract", False, EXPECTED_BLOCKER, "freeze batch container"),
        ("batch_member_exact_type", "exact member type", "member type is not frozen", "fixed boundary", False, EXPECTED_BLOCKER, "freeze member type"),
        ("batch_membership_semantics", "equality, order, duplicates, normalization and malformed handling", "no membership comparison contract", "fixed boundary", False, EXPECTED_BLOCKER, "freeze membership semantics"),
        ("current_candidate_self_exclusion", "self-inclusion, exclusion and multiplicity policy", "current-candidate membership is unspecified", "fixed boundary", False, EXPECTED_BLOCKER, "freeze self-exclusion"),
        ("candidate_record_id_relationship", "candidate_record_id role in duplicate evaluation", "candidate_record_id is explicitly separate; self-exclusion use is not frozen", "candidate identity contract", False, EXPECTED_BLOCKER, "design relationship without identity substitution"),
        ("duplicate_vs_leakage_group_boundary", "exact duplicate versus broader must-link leakage group", "leakage group is a conservative multi-relation union; exact-duplicate boundary absent", "leakage assignment evidence", False, EXPECTED_BLOCKER, "freeze boundary"),
        ("outcome_vocabulary", "unique, duplicate, malformed and collision outcomes", "no ADMIT_009 outcome mapping", "fixed boundary", False, EXPECTED_BLOCKER, "freeze outcomes"),
        ("reason_vocabulary", "formal uppercase reason vocabulary", "only historical lowercase umbrella reason exists", "rule registry", False, EXPECTED_BLOCKER, "freeze reasons"),
        ("canonical_validated_state", "canonical and validated state for every path", "no state-retention contract", "fixed boundary", False, EXPECTED_BLOCKER, "freeze result state"),
        ("independent_semantic_oracle", "independent pure full-input semantic oracle", "no ADMIT_009 oracle exists", "Exact8 runtime and fixed boundary", False, EXPECTED_BLOCKER, "design oracle after key contract"),
        ("real_provider_and_implementation_readiness", "canonical provider mapping and complete standalone contract", "zero canonical duplicate keys; implementation remains prohibited", "fixed boundary and stop boundary", False, EXPECTED_BLOCKER, "design key contract next"),
    )
    return [{
        "precondition_id": f"PRE_{index:03d}", "semantic_area": area,
        "required_contract": required, "observed_contract": observed,
        "source_evidence": evidence, "semantics_complete": str(complete).lower(),
        "blocker_id": blocker, "implementation_disposition": disposition,
        "precondition_passed": "true",
    } for index, (area, required, observed, evidence, complete, blocker, disposition) in enumerate(specs, 1)]


def _expected_vocabulary() -> list[dict[str, str]]:
    p = EXPECTED_SOURCE_PATHS
    specs = (
        (p[5], "admission_field_name", "duplicate_identity_key", "pre-download deduplication-key candidate field", "admission_candidate_field", True),
        (p[11], "separate_from_duplicate_identity_key", "candidate_record_id", "opaque candidate-record identity explicitly separate from duplicate key", "record_identifier", False),
        (p[13], "column", "sample_index_row_id", "sample-index row identity", "sample_identifier", False),
        (p[14], "column", "assignment_id", "leakage assignment row identity", "assignment_identifier", False),
        (p[5], "admission_field_name", "pdb_id", "structure identifier", "record_identifier", False),
        (p[5], "admission_field_name", "ligand_comp_id", "ligand component identity", "ligand_identity", False),
        (p[5], "admission_field_name", "covalent_residue_name", "covalent residue locator component", "residue_identity", False),
        (p[5], "admission_field_name", "covalent_residue_chain_id", "covalent residue locator component", "residue_identity", False),
        (p[5], "admission_field_name", "covalent_residue_index", "covalent residue locator component", "residue_identity", False),
        (p[5], "admission_field_name", "covalent_residue_atom_name", "covalent residue locator component", "residue_identity", False),
        (p[5], "admission_field_name", "covalent_bond_atom_pair", "covalent atom-pair evidence", "atom_pair_identity", False),
        (p[13], "column", "ligand_graph_group_id", "ligand graph grouping identity", "ligand_graph_group", False),
        (p[13], "column", "ligand_scaffold_group_id", "ligand scaffold grouping identity", "ligand_scaffold_group", False),
        (p[14], "column", "protein_exact_sequence_group_id", "protein exact-sequence group", "protein_identity_group", False),
        (p[14], "column", "protein_accession_group_id", "protein accession group", "protein_identity_group", False),
        (p[14], "column", "protein_sequence_cluster_90_id", "protein 90-percent sequence cluster", "protein_identity_group", False),
        (p[14], "column", "protein_sequence_cluster_50_id", "protein 50-percent sequence cluster", "protein_identity_group", False),
        (p[14], "column", "final_leakage_group_id", "conservative multi-relation must-link group", "leakage_group", False),
        (p[5], "admission_field_name", "leakage_group_id", "pre-final-split leakage group candidate field", "leakage_group", False),
        (p[15], "column", "sample_split_assignment_id", "sample split assignment identity", "split_assignment", False),
        (p[16], "column", "final_dataset_membership_id", "materialized final-dataset membership identity", "sample_identifier", False),
        (p[4], "ADMIT_009.required_status", "duplicate_precheck_complete", "historical required status", "historical_required_status", False),
        (p[4], "ADMIT_009.blocking_reason", "duplicate_identity_unresolved", "historical lowercase umbrella reason", "historical_blocking_reason", False),
        (p[3], "issue_id", EXPECTED_BLOCKER, "open implementation blocker", "implementation_blocker", False),
    )
    return [{
        "vocabulary_order": str(index), "source_relative_path": path,
        "source_sha256": EXPECTED_SOURCE_SHA256[path], "source_kind": _source_kind(path),
        "symbol_or_row_id": symbol, "observed_term": term, "observed_role": role,
        "semantic_category": category, "explicitly_declared_duplicate_key": str(declared).lower(),
        "explicitly_declared_duplicate_key_component": "false",
        "exact_duplicate_equivalence_declared": "false",
        "safe_to_use_in_duplicate_key_contract_now": "false",
        "promotion_blocker": EXPECTED_BLOCKER, "inventory_passed": "true",
    } for index, (path, symbol, term, role, category, declared) in enumerate(specs, 1)]


def _expected_occurrences(sources: Mapping[str, bytes]) -> list[dict[str, str]]:
    identity_terms = {"ADMIT_009", "duplicate_identity_precheck", "duplicate_identity_key", "batch_duplicate_identity_keys", "duplicate_identity_key_contract", "duplicate_precheck_complete", "duplicate_identity_unresolved"}
    authoritative_paths = set(EXPECTED_SOURCE_PATHS[3:6]) | set(EXPECTED_SOURCE_PATHS[7:10])
    rows: list[dict[str, str]] = []
    for path in EXPECTED_SOURCE_PATHS:
        for line_number, line in enumerate(sources[path].decode("utf-8").splitlines(), 1):
            for term in MATCH_TERMS:
                if term not in line:
                    continue
                if term in identity_terms:
                    role, scope = "ADMIT_009 high-level identity or dependency", "ADMIT_009"
                    statement = "the named interface element is evidence; its occurrence does not freeze duplicate-key semantics"
                elif term == EXPECTED_BLOCKER:
                    role, scope, statement = "open semantics blocker", "ADMIT_009", "duplicate identity key semantics remain unresolved"
                else:
                    role = "distinct identity or grouping evidence"
                    scope = "candidate, ligand, protein, leakage, split, or materialization"
                    statement = "the observed identifier is not thereby a duplicate key or exact-duplicate equivalence"
                rows.append({
                    "occurrence_order": str(len(rows) + 1), "source_relative_path": path,
                    "source_sha256": EXPECTED_SOURCE_SHA256[path], "source_kind": _source_kind(path),
                    "symbol_or_row_id": f"line_{line_number}", "matched_term": term,
                    "field_role": role, "rule_scope": scope, "semantic_statement": statement,
                    "authoritative_for_admit009_formal_semantics": str(term in identity_terms and path in authoritative_paths).lower(),
                    "occurrence_passed": "true",
                })
    assert len(rows) == 103 and {row["matched_term"] for row in rows} == set(MATCH_TERMS)
    return rows


def _expected_source_rows() -> list[dict[str, str]]:
    return [{
        "source_order": str(index), "source_relative_path": path, "source_kind": _source_kind(path),
        "boundary_necessity": "minimal committed evidence for ADMIT_009 identity, unresolved semantics, identity separation, leakage boundary, or Exact11 preservation",
        "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true", "non_symlink": "true",
        "expected_sha256": EXPECTED_SOURCE_SHA256[path], "base_tree_sha256": EXPECTED_SOURCE_SHA256[path],
        "filesystem_sha256": EXPECTED_SOURCE_SHA256[path], "source_boundary_passed": "true",
    } for index, path in enumerate(EXPECTED_SOURCE_PATHS, 1)]


def _readiness() -> dict[str, bool]:
    return {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def _expected_manifest(preconditions: list[dict[str, str]], vocabulary: list[dict[str, str]], occurrences: list[dict[str, str]], sources: list[dict[str, str]], issues: list[dict[str, str]], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    readiness = _readiness()
    manifest: dict[str, Any] = {
        "project": "CovaPIE", "step": "ADMIT_009 formal evaluator interface preconditions audit v1",
        "stage": EXPECTED_STAGE, "manifest_schema_version": "covapie_admit_009_formal_evaluator_preconditions_manifest_v1",
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": EXPECTED_RULE_ID, "admission_rule_name": EXPECTED_RULE_NAME,
        "evaluation_phase": "pre_download", "candidate_field": EXPECTED_FIELD,
        "batch_context_item": EXPECTED_BATCH_CONTEXT, "evaluation_policy_context_item": EXPECTED_POLICY_CONTEXT,
        "future_evaluator_name_reserved_only": "evaluate_admit_009", "future_result_name_reserved_only": "Admit009EvaluationResult",
        "historical_evidence_source": "future_candidate_record", "historical_required_status": "duplicate_precheck_complete",
        "historical_blocking_reason": "duplicate_identity_unresolved",
        "source_boundary_name": "fixed_ordered_minimal_exact17_committed_source_boundary",
        "source_input_count": 17, "source_input_paths": list(EXPECTED_SOURCE_PATHS),
        "source_input_sha256": dict(EXPECTED_SOURCE_SHA256),
        "source_input_verification": [{
            "source_order": index, "source_relative_path": path,
            "expected_sha256": EXPECTED_SOURCE_SHA256[path], "base_tree_sha256": EXPECTED_SOURCE_SHA256[path],
            "filesystem_sha256": EXPECTED_SOURCE_SHA256[path], "tracked": True, "base_tree_blob": True,
            "filesystem_regular": True, "non_symlink": True, "source_verified": True,
        } for index, path in enumerate(EXPECTED_SOURCE_PATHS, 1)],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "precondition_row_count": 24, "precondition_pass_count": 24,
        "semantics_complete_count": 6, "semantics_incomplete_count": 18,
        "vocabulary_inventory_row_count": 24, "field_occurrence_inventory_row_count": 103,
        "real_provider_duplicate_identity_key_count": 0,
        "real_provider_mapping_observation": "historical grouping evidence exists, canonical duplicate-key provider mapping unvalidated",
        "high_level_precheck_evidence": {
            "admission_rule_identity_available": True, "evaluation_phase_available": True,
            "candidate_field_identity_available": True, "batch_context_dependency_available": True,
            "evaluation_policy_item_available": True, "pure_in_memory_interface_possible": True,
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
        "blocker_ids": [EXPECTED_BLOCKER], "issue_inventory_row_count": len(issues),
        "issue_inventory_sha256": "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128",
        "issue_inventory_byte_identical_to_exact8_predecessor": True,
        "duplicate_identity_key_semantics_issue_status": "open", "coverage_issue_starts_with_admit_009": True,
        "readiness": readiness, "output_file_count": 6, "output_files": list(EXPECTED_FILES),
        "output_sha256": dict(output_sha256), "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "no_duplicate_identity_key_design", "no_component_selection", "no_separator_or_hash_selection",
            "no_batch_container_design", "no_self_exclusion_design", "no_evaluate_admit_009",
            "no_Admit009EvaluationResult", "no_adapter_design", "no_exact8_runtime_change",
            "no_admit_009_registration", "no_admit_010", "no_provider_mapping_validation",
            "no_real_candidate_evaluation", "no_raw_network_or_download", "no_training",
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
    assert (root / EXPECTED_FILES[4]).read_bytes() == source_bytes[EXPECTED_SOURCE_PATHS[3]]
    assert len(issues) == 11
    blocker = next(row for row in issues if row["issue_id"] == EXPECTED_BLOCKER)
    coverage = next(row for row in issues if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert blocker["status"] == "open" and blocker["affected_fields"] == EXPECTED_FIELD
    assert blocker["affected_rules"] == EXPECTED_RULE_ID and blocker["integration_transition"] == "unchanged_open"
    assert coverage["status"] == "open"
    assert coverage["affected_rules"] == "|".join(f"ADMIT_{index:03d}" for index in range(9, 16))
    assert coverage["integration_transition"] == "admit_008_implemented_and_removed_from_open_coverage_scope"
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
    with tempfile.TemporaryDirectory(prefix="covapie_admit009_checker_") as temporary:
        temp = Path(temporary)
        promoted = temp / "promoted"
        shutil.copytree(root, promoted)
        path = promoted / EXPECTED_FILES[1]
        text = path.read_text(encoding="utf-8").replace(
            "record_identifier,false,false,false,false",
            "record_identifier,true,true,true,true", 1,
        )
        path.write_text(text, encoding="utf-8")
        _refresh_hash(promoted, EXPECTED_FILES[1])
        _raises(_validate_disk, promoted, enforce_frozen_hashes=False)

        overclaim = temp / "overclaim"
        shutil.copytree(root, overclaim)
        path = overclaim / EXPECTED_FILES[5]
        manifest = json.loads(path.read_text(encoding="utf-8"))
        key = "ready_for_admit_009_standalone_evaluator_interface_implementation"
        manifest[key] = True
        manifest["readiness"][key] = True
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _raises(_validate_disk, overclaim, enforce_frozen_hashes=False)

        issue = temp / "issue"
        shutil.copytree(root, issue)
        path = issue / EXPECTED_FILES[4]
        path.write_text(path.read_text(encoding="utf-8").replace(f"{EXPECTED_BLOCKER},implementation_semantics_gap,duplicate_identity_key,ADMIT_009,blocking,open,", f"{EXPECTED_BLOCKER},implementation_semantics_gap,duplicate_identity_key,ADMIT_009,blocking,resolved,"), encoding="utf-8")
        _refresh_hash(issue, EXPECTED_FILES[4])
        _raises(_validate_disk, issue, enforce_frozen_hashes=False)

        extra = temp / "extra"
        shutil.copytree(root, extra)
        (extra / "unexpected.txt").write_text("unexpected", encoding="utf-8")
        _raises(_validate_disk, extra, enforce_frozen_hashes=False)


def main() -> int:
    root = REPO_ROOT / EXPECTED_OUTPUT_ROOT
    first = gate.run_covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1(root)
    first_hashes = {name: _sha(root / name) for name in EXPECTED_FILES}
    second = gate.run_covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1(root)
    second_hashes = {name: _sha(root / name) for name in EXPECTED_FILES}
    assert first["manifest"] == second["manifest"] and first_hashes == second_hashes
    manifest = _validate_disk(root)
    _negative_checks(root)
    print(f"stage={EXPECTED_STAGE}")
    print("all_checks_passed=true")
    print("source_boundary_exact17=true")
    print("precondition_exact24_passed=true")
    print("semantics_complete_count=6")
    print("semantics_incomplete_count=18")
    print("vocabulary_inventory_row_count=24")
    print("field_occurrence_inventory_row_count=103")
    print("real_provider_duplicate_identity_key_count=0")
    print("issue_inventory_exact11_byte_identical=true")
    print("duplicate_identity_key_semantics_issue_status=open")
    print("ready_for_admit_009_standalone_evaluator_interface_implementation=false")
    print("ready_for_admit_009_duplicate_identity_key_contract_design=true")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    print("outputs_byte_identical=true")
    print("covapie_admit_009_formal_evaluator_interface_preconditions_audit_v1_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
