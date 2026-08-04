"""Build the unfilled Current11 family/rule approval review package v1.

This module reads SHA-bound metadata only.  It does not read structures,
execute chemistry, approve semantics, or write the external workspace.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from covalent_ext.covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1 import (
    evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1,
)


__all__ = (
    "build_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1",
)

ERROR = "COVAPIE_CURRENT11_FAMILY_RULE_APPROVAL_REVIEW_PACKAGE_INVALID"
VERSION = (
    "covapie_current11_reaction_family_and_warhead_rule_"
    "approval_review_package_v1"
)
REPOSITORY = "fumx2000/DiffSBDD"
REMOTE = "git@github.com:fumx2000/DiffSBDD.git"
BRANCH = "main"
BASE_COMMIT = "2e07b7b094e2dccc69eaf29b5f51db0f9af2e81b"
BINDING_COMMIT = BASE_COMMIT
BINDING_PARENT = "0e36e3131750dcb99f806ec635afeae2b0b0dc88"
BINDING_SUBJECT = (
    "add CovaPIE Current11 reaction family and approved warhead rule "
    "authority binding v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 family and rule approval review package v1"
)
WORKSPACE_NAME = "current11-family-rule-approval-v1"
PUBLICATION_SCHEME = "relative_symlink_to_immutable_sibling_v1"
OBJECT_DIRECTORY_PREFIX = f".{WORKSPACE_NAME}.object-"

DATA_ROOT = (
    "data/derived/covalent_small/"
    "covapie_current11_reaction_family_and_warhead_rule_"
    "approval_review_package_v1"
)
SOURCE_INVENTORY_PATH = f"{DATA_ROOT}/covapie_review_package_source_inventory.csv"
FIELD_CONTRACT_PATH = f"{DATA_ROOT}/covapie_review_package_field_contract.csv"
REVIEW_UNIT_MATRIX_PATH = f"{DATA_ROOT}/covapie_family_rule_review_unit_matrix.csv"
FAILURE_MATRIX_PATH = f"{DATA_ROOT}/covapie_review_package_failure_matrix.csv"
REPO_MANIFEST_PATH = f"{DATA_ROOT}/covapie_review_package_manifest.json"

CANDIDATE_PATHS = tuple(sorted((
    SOURCE_INVENTORY_PATH,
    FIELD_CONTRACT_PATH,
    REVIEW_UNIT_MATRIX_PATH,
    FAILURE_MATRIX_PATH,
    REPO_MANIFEST_PATH,
    "docs/covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1_guide.md",
    "scripts/materialize_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1.py",
    "src/covalent_ext/covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1.py",
    "tests/test_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1.py",
)))

WORKSPACE_FILES = (
    "README.md",
    "family_rule_approval_worklist.csv",
    "family_rule_candidate_evidence.json",
    "sample_support_evidence.csv",
    "review_package_manifest.json",
)

BINDING_ROOT = (
    "data/derived/covalent_small/"
    "covapie_current11_reaction_family_and_approved_warhead_rule_"
    "authority_binding_v1"
)
ASSIGNMENT_PATH = (
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1/"
    "covapie_current11_cys_sg_candidate_assignment_authority.csv"
)
RULE_REGISTRY_PATH = (
    "data/derived/covalent_small/"
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1/"
    "covapie_cys_sg_warhead_rule_registry.csv"
)

# Evidence id, namespace, commit/direct producer, path, filesystem SHA, lineage.
SOURCE_EVIDENCE = (
    ("B01", "git_object", BINDING_COMMIT, f"{BINDING_ROOT}/covapie_current11_family_rule_authority_binding_matrix.csv", "7064c1d0153ba1399bfdae8affcf21ead3f27e8a933987cd025ba5101a92bb61", "formal_binding_matrix"),
    ("B02", "git_object", BINDING_COMMIT, f"{BINDING_ROOT}/covapie_family_and_warhead_rule_authority_registry.csv", "4899d4664acf45d5ee90283e7977d62385b3a70fe41e082f4d060388be7e106b", "formal_binding_registry"),
    ("B03", "git_object", BINDING_COMMIT, f"{BINDING_ROOT}/covapie_family_rule_binding_source_inventory.csv", "9e1533d8135d253b3360954b218f0219c56bc21aee424b4fce7ba8bc2672eae7", "binding_source_lineage"),
    ("B04", "git_object", BINDING_COMMIT, f"{BINDING_ROOT}/covapie_family_rule_authority_binding_manifest.json", "0a6f6228e6397d3ccaef87a93a8c45dcab5e3c505cf0091a08c2bec335712dcc", "binding_conclusion"),
    ("C01", "git_object", "0c8d1d10260a028360357b8c309f22676fc81645", ASSIGNMENT_PATH, "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9", "candidate_sample_assignments"),
    ("C02", "git_object", "dc1222503dcec83220a28df2abdae898a0855864", RULE_REGISTRY_PATH, "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309", "candidate_local_graph_rules"),
    ("S01", "sha_bound_formal_state", "51810f19e0bbb96171a7dd3aebd72ef08eda0200", "manual-review/covapie_current11_unified_effective_authority_view_v1.json", "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774", "unified_effective_authority;transitive_binder=1cdbca345483022ece967b24de37013b77349cd4;direct_producer=51810f19e0bbb96171a7dd3aebd72ef08eda0200"),
    ("S02", "sha_bound_formal_state", "b917bf16ae4e08f35c20074300142e3c7cedbabf", "manual-review/covapie_current11_real_human_review_submission_bundle_v1.json", "b40c7fad5eedfd5208dd3bc8919cf0aedfe4c22887c27e49475c29a9fcd2b0f3", "legacy_submission;transitive_binder=1cdbca345483022ece967b24de37013b77349cd4"),
    ("S03", "sha_bound_formal_state", "7bf2d25bfcef55b8de2a064d6b20d9206b1e5298", "manual-review/covapie_current11_real_human_review_ingestion_execution_bundle_v1.json", "e7099dd28ba51c6935aa4b534815abd1a9f6f46f60be3553d1bb54f1dd4d8dfb", "legacy_ingestion;directly_consumes=S02;transitive_binder=1cdbca345483022ece967b24de37013b77349cd4"),
    ("S04", "sha_bound_formal_state", "433e4c3e95a13a02e8cfefbecd28d79d62df37c1", "manual-review/covapie_current11_multi_boundary_human_review_submission_bundle_v1.json", "1e59537e6802d5500f4adce418a481a5b730968f4ecdfa73b8c90c7946e2ee24", "multi_boundary_submission;directly_consumes=S02|S03;transitive_binder=1cdbca345483022ece967b24de37013b77349cd4"),
    ("S05", "sha_bound_formal_state", "ab7eff978e97823d3205f919584893dc87c544f2", "manual-review/covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1.json", "d837ee22f9fa39fcc9f70ebd1a639e4abd899af4b2c4fd5995c436ceefe7b018", "multi_boundary_ingestion;directly_consumes=S03|S04;transitive_binder=1cdbca345483022ece967b24de37013b77349cd4"),
    ("S06", "sha_bound_formal_state", "ddf3852519cac5eb0d0e50ef919c15ca36fc127a", "manual-review/covapie_current11_multi_boundary_authority_bundle_v1.json", "631f134390abd29311a5a8a5ff20b42e4ddd73fd0c37b5f2b9b5f899d055ea41", "multi_boundary_authority;directly_consumes=S03|S05;transitive_binder=1cdbca345483022ece967b24de37013b77349cd4"),
)

BINDING_MATRIX_COLUMNS = (
    "sample_index_row_id", "pdb_id", "ligand_identity",
    "candidate_reaction_family_id", "candidate_warhead_rule_id",
    "candidate_assignment_exact_one",
    "candidate_matches_effective_boundary_authority",
    "candidate_matches_pre_reaction_graph", "candidate_matches_reaction_delta",
    "candidate_matches_reactive_atoms", "boundary_review_completed",
    "selected_candidate_identity_attested",
    "reaction_family_identity_explicitly_attested",
    "warhead_rule_identity_explicitly_attested",
    "warhead_rule_full_semantics_explicitly_attested",
    "approved_structural_pattern_attested", "reaction_family_version",
    "reaction_family_structural_basis", "reaction_family_authority_status",
    "reaction_family_authority_source", "warhead_rule_version",
    "warhead_rule_structural_representation_type",
    "warhead_rule_structural_representation_id",
    "warhead_rule_required_fields_complete", "warhead_rule_approval_status",
    "warhead_rule_authority_source", "binding_conflicts", "binding_blockers",
    "verified",
)
ASSIGNMENT_COLUMNS = (
    "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "target_residue_name", "target_residue_number",
    "target_residue_atom_name", "ligand_reactive_atom_name",
    "ligand_reactive_atom_element", "ligand_reactive_parent_ccd_atom_id",
    "component_parent_graph_sha256", "observed_graph_sha256",
    "radius_1_signature_sha256", "candidate_reaction_family_id",
    "candidate_reaction_family_semantic_name", "candidate_warhead_rule_id",
    "candidate_warhead_type_semantic_name",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id", "assignment_source_design_matrix_sha256",
    "assignment_source_rule_registry_sha256",
    "assignment_source_family_registry_sha256",
    "candidate_rule_assignment_exact_one",
    "candidate_family_assignment_exact_one", "class_vocabulary_join_exact_one",
    "assignment_status", "review_status", "training_label_status",
    "candidate_reaction_family_assignment_materialized",
    "candidate_warhead_rule_assignment_materialized",
    "warhead_type_candidate_label_available",
    "formal_reaction_family_label_available", "approved_warhead_rule_available",
    "human_gold_review_completed", "training_label_approved",
    "ready_for_assignment_human_review", "ready_for_role_proposal_generation",
    "ready_for_minimal_seed_proposal_generation",
    "ready_for_mask_materialization", "ready_for_tensorization",
    "ready_for_model_integration", "ready_for_training",
    "assignment_record_sha256", "blocking_reasons", "verified",
)
RULE_COLUMNS = (
    "warhead_rule_id", "warhead_type_semantic_name", "reaction_family_id",
    "rule_kind", "selected_signature_radius", "center_atom_element",
    "center_atom_formal_charge", "target_residue_name",
    "target_residue_atom_name", "formed_bond_order",
    "canonical_local_graph_rule_json", "canonical_local_graph_rule_sha256",
    "required_leaving_group_count", "allowed_leaving_group_elements",
    "required_reaction_delta_class", "Current11_match_count",
    "Current11_unique_component_count", "exact_match_unique",
    "candidate_rule_assignment_ready", "approved_warhead_smarts",
    "SMARTS_status", "human_gold_review_completed", "approved",
    "blocking_reasons", "verified",
)

FROZEN_FIELDS = (
    "review_unit_id", "reaction_family_id", "warhead_rule_id",
    "sample_count", "sample_index_row_ids", "pdb_ligand_pairs",
    "candidate_reaction_family_semantic_name",
    "candidate_warhead_rule_semantic_name", "target_residue_types",
    "target_residue_reactive_atom", "formed_bond_order",
    "candidate_local_graph_rule_sha256", "candidate_reaction_delta_class",
    "candidate_leaving_group_summary", "boundary_review_completed_count",
    "selected_candidate_identity_attested_count",
    "effective_boundary_cardinalities",
    "approved_warhead_smarts_currently_available",
    "formal_equivalent_structural_contract_currently_available",
    "current_binding_conclusion", "current_blocking_fields",
    "frozen_evidence_sha256",
)
FAMILY_HUMAN_FIELDS = (
    "reviewed_reaction_family_version",
    "reviewed_reaction_family_semantic_name",
    "reviewed_reaction_family_structural_basis",
    "reaction_family_identity_explicitly_attested",
    "reaction_family_review_decision",
)
RULE_HUMAN_FIELDS = (
    "reviewed_warhead_rule_version", "reviewed_warhead_rule_semantic_name",
    "reviewed_target_residue_types",
    "reviewed_target_residue_reactive_atom_name", "reviewed_warhead_smarts",
    "reviewed_ligand_reactive_atom_map_number",
    "reviewed_warhead_atom_map_numbers",
    "reviewed_warhead_attachment_atom_map_number",
    "reviewed_expected_pre_reaction_bond_orders",
    "reviewed_allowed_formal_charge_pattern", "reviewed_allowed_match_count",
    "reviewed_priority", "reviewed_leaving_group_contract",
    "reviewed_formed_bond_order", "reviewed_ambiguity_policy",
    "reviewed_tie_policy", "warhead_rule_identity_explicitly_attested",
    "warhead_rule_full_semantics_explicitly_attested",
    "approved_structural_pattern_attested", "warhead_rule_review_decision",
)
PROVENANCE_HUMAN_FIELDS = (
    "review_rationale", "review_notes", "reviewer_id", "attestor_id",
    "review_completed",
)
HUMAN_FIELDS = FAMILY_HUMAN_FIELDS + RULE_HUMAN_FIELDS + PROVENANCE_HUMAN_FIELDS
WORKLIST_FIELDS = FROZEN_FIELDS + HUMAN_FIELDS

SAMPLE_SUPPORT_FIELDS = (
    "sample_index_row_id", "pdb_id", "ligand_identity", "review_unit_id",
    "reaction_family_id", "warhead_rule_id", "ligand_reactive_atom",
    "target_residue_atom", "pre_reaction_graph_sha256",
    "reaction_delta_class", "effective_boundary_cardinality",
    "boundary_review_completed", "selected_candidate_identity_attested",
    "sample_supports_candidate_identity",
    "sample_attests_full_family_or_rule_semantics", "verified",
)
FAMILY_DECISIONS = (
    "approve_reaction_family_identity", "revise_reaction_family_identity",
    "quarantine_reaction_family",
)
RULE_DECISIONS = (
    "approve_complete_warhead_rule", "revise_warhead_rule",
    "quarantine_warhead_rule",
)

SOURCE_INVENTORY_COLUMNS = (
    "evidence_id", "source_namespace", "source_commit_or_direct_producer",
    "source_path", "source_sha256", "lineage_note", "verified",
)
FIELD_CONTRACT_COLUMNS = (
    "field_order_0based", "field_name", "field_scope", "frozen",
    "human_fillable", "initial_value", "allowed_values",
    "future_approval_requirement", "semantic_note", "verified",
)
REVIEW_UNIT_MATRIX_COLUMNS = FROZEN_FIELDS
FAILURE_MATRIX_COLUMNS = (
    "case_id", "failure_case", "mutation_signature", "validator_target",
    "test_node_id", "expected_error", "fails_closed", "verified",
)

FAILURE_SPECS = (
    ("X01", "binding_predecessor_not_formal_commit", "binding_commit=substituted_sha", "source_state"),
    ("X02", "binding_conclusion_not_C", "binding_conclusion=authoritative", "source_state"),
    ("X03", "unique_review_unit_count_not_7", "review_unit_deleted", "semantic_state"),
    ("X04", "sample_support_count_not_11", "sample_support_deleted", "semantic_state"),
    ("X05", "duplicate_review_unit", "review_unit_duplicated", "semantic_state"),
    ("X06", "duplicate_sample", "sample_duplicated", "semantic_state"),
    ("X07", "sample_not_covered", "sample_id_replaced", "semantic_state"),
    ("X08", "sample_maps_to_multiple_units", "sample_added_to_second_unit", "semantic_state"),
    ("X09", "rule_maps_to_multiple_families", "family_id_changed_for_repeated_rule", "semantic_state"),
    ("X10", "sample_count_sum_not_11", "sample_count_incremented", "semantic_state"),
    ("X11", "candidate_family_id_drift", "family_id=substituted", "semantic_state"),
    ("X12", "candidate_rule_id_drift", "rule_id=substituted", "semantic_state"),
    ("X13", "candidate_semantic_evidence_drift", "candidate_semantic_name=changed", "semantic_state"),
    ("X14", "local_graph_sha_drift", "local_graph_sha=zero", "semantic_state"),
    ("X15", "boundary_authority_drift", "boundary_cardinality=3", "semantic_state"),
    ("X16", "candidate_graph_in_approved_smarts", "reviewed_warhead_smarts=candidate_json", "package_payloads"),
    ("X17", "candidate_name_in_reviewed_name", "reviewed_semantic_name=candidate_name", "package_payloads"),
    ("X18", "human_family_field_prefilled", "family_version=v1", "package_payloads"),
    ("X19", "human_rule_field_prefilled", "rule_version=v1", "package_payloads"),
    ("X20", "attestation_field_prefilled", "family_attestation=false", "package_payloads"),
    ("X21", "decision_prefilled", "family_decision=pending", "package_payloads"),
    ("X22", "reviewer_or_attestor_prefilled", "reviewer_id=machine", "package_payloads"),
    ("X23", "review_completed_prefilled", "review_completed=false", "package_payloads"),
    ("X24", "package_file_count_not_5", "manifest_file_count=4", "package_payloads"),
    ("X25", "extra_package_file", "extra.txt=bytes", "package_payloads"),
    ("X26", "missing_package_file", "README_deleted", "package_payloads"),
    ("X27", "manifest_sha_mismatch", "worklist_sha=zero", "package_payloads"),
    ("X28", "worklist_field_order_drift", "first_two_fields_swapped", "package_payloads"),
    ("X29", "sample_evidence_field_order_drift", "first_two_fields_swapped", "package_payloads"),
    ("X30", "candidate_evidence_order_drift", "first_two_records_swapped", "package_payloads"),
    ("X31", "existing_target_directory", "precreate_target_directory", "publication"),
    ("X32", "existing_arbitrary_target_symlink", "precreate_target_symlink", "publication"),
    ("X33", "parent_path_escape", "target_outside_expected_parent", "publication"),
    ("X34", "partial_object_write", "write_failure_after_first_file", "publication"),
    ("X35", "canonical_symlink_publication_failure", "os_symlink_raises", "publication"),
    ("X36", "created_file_inode_replaced_during_cleanup", "created_object_file_replaced", "publication"),
    ("X37", "object_directory_inode_replaced_during_cleanup", "created_object_directory_replaced", "publication"),
    ("X38", "file_mode_not_0644", "workspace_file_mode=0600", "workspace"),
    ("X39", "forbidden_structure_file_in_package", "sample.pdb=bytes", "package_payloads"),
    ("X40", "execution_boundary_crossed", "raw_structure_read=true", "response"),
    ("X41", "response_summary_tampering", "review_unit_count=6_rehashed", "response"),
    ("X42", "candidate_lifecycle_not_commit_survivable", "formal_parent_mismatch", "lifecycle"),
    ("X43", "index_hides_actual_worktree_drift", "actual_blob_differs_from_index", "lifecycle"),
    ("X44", "valid_looking_lifecycle_witness_substitution", "origin_sha=substituted", "response"),
    ("X45", "canonical_symlink_absolute_or_path_escape", "canonical_link_target=../escape", "canonical_workspace"),
    ("X46", "canonical_symlink_wrong_sibling_or_prefix", "canonical_link_target=wrong_object", "canonical_workspace"),
    ("X47", "canonical_symlink_broken", "canonical_link_target=missing_valid_object", "canonical_workspace"),
    ("X48", "published_object_directory_inode_or_type_drift", "object_directory_replaced_with_file", "canonical_workspace"),
    ("X49", "workspace_file_sha256_valid_looking_substitution", "workspace_file_sha256[README.md]=different_valid_sha", "response"),
)

FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part", ".pdb", ".sdf",
)
EXECUTION_BOUNDARY_FIELDS = (
    "raw_structure_read", "network_accessed", "rdkit_imported",
    "smarts_matching_executed", "murcko_executed", "brics_executed",
    "topology_restoration_executed", "approval_decision_executed",
    "review_submission_compiled", "review_ingested",
    "authority_bundle_generated", "role_proposal_generated",
    "minimal_seed_generated", "tensor_materialized", "checkpoint_accessed",
    "forward_executed", "backward_executed", "training_executed",
    "reward_or_rl_executed", "commit_created", "push_performed",
)

_RESPONSE_LIFECYCLE_FIELDS = (
    "origin_main", "ahead", "behind", "review_package_lifecycle_profile",
    "review_package_commit", "review_package_committed",
    "review_package_published", "ready_for_review_package_commit_review",
)
_RESPONSE_FIELDS = (
    "review_package_version", "base_commit", "binding_commit",
    *_RESPONSE_LIFECYCLE_FIELDS,
    "review_unit_count", "sample_support_count", "package_file_count",
    "publication_scheme", "workspace_file_sha256",
    *EXECUTION_BOUNDARY_FIELDS, "response_sha256",
)
_RESPONSE_INT_FIELDS = (
    "ahead", "behind", "review_unit_count", "sample_support_count",
    "package_file_count",
)
_RESPONSE_BOOL_FIELDS = (
    "review_package_committed", "review_package_published",
    "ready_for_review_package_commit_review", *EXECUTION_BOUNDARY_FIELDS,
)
_RESPONSE_STRING_FIELDS = (
    "review_package_version", "base_commit", "binding_commit", "origin_main",
    "review_package_lifecycle_profile", "publication_scheme",
    "response_sha256",
)
_RESPONSE_TUPLE_OR_DICT_FIELDS = ("workspace_file_sha256",)

README_TEXT = """# CovaPIE Current11 family/rule approval review workspace v1

This workspace contains exactly seven reaction-family/warhead-rule review
units covering the eleven Current11 samples. It is unfilled supporting
material for real human review. Creating it approves nothing.

## Files

- `family_rule_approval_worklist.csv` contains frozen evidence columns followed
  by human-fillable columns. Do not edit any frozen column.
- `family_rule_candidate_evidence.json` contains candidate-only local-graph,
  reaction-delta, reactive-atom, and effective-boundary evidence.
- `sample_support_evidence.csv` maps every Current11 sample exactly once to a
  review unit. Sample boundary review supports candidate identity only; it does
  not attest complete family or rule semantics.
- `review_package_manifest.json` binds this initial Exact5 package.

Every human-fillable field is intentionally an empty string. Empty means no
human has reviewed the field; it is not `false`, `pending`, or a negative
decision. Never copy a candidate value into a reviewed field without real
human review. In particular, canonical candidate local-graph JSON is not
approved SMARTS and is not a formally equivalent approved structural pattern.

## Family decision contract

The closed decision vocabulary is `approve_reaction_family_identity`,
`revise_reaction_family_identity`, and `quarantine_reaction_family`.
Future use of `approve_reaction_family_identity` requires a non-empty reviewed
family version, semantic name, and structural basis;
`reaction_family_identity_explicitly_attested=true`; and complete rationale,
reviewer, attestor, and `review_completed` provenance.

## Rule decision contract

The closed decision vocabulary is `approve_complete_warhead_rule`,
`revise_warhead_rule`, and `quarantine_warhead_rule`. Future use of
`approve_complete_warhead_rule` requires all predecessor fields: family ID and
version, target residue types and reactive atom, mapped warhead SMARTS, ligand
reactive atom map number, warhead atom map numbers, attachment atom map number,
expected pre-reaction bond orders, allowed formal-charge pattern, allowed match
count, and priority. It additionally requires a leaving-group contract, formed
bond order, ambiguity policy, tie policy, explicit rule-identity attestation,
full-rule-semantics attestation, approved-structural-pattern attestation, and
complete reviewer/attestor/rationale/review-completed provenance.

These are future validation rules only. This materialization does not execute
them and does not fill any value.

## Boundary and next step

The frozen candidate evidence may guide review but is not approval authority.
Do not add this external workspace to Git. After real humans complete and sign
all seven units, a separately authorized future increment may compile a review
submission. This package does not compile a submission, ingest review results,
create an authority bundle, propose roles or minimal seeds, tensorize data, load
a checkpoint, run a model, or train.
"""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object, *, pretty: bool = False) -> bytes:
    try:
        if pretty:
            text = json.dumps(
                value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                indent=2,
            ) + "\n"
        else:
            text = json.dumps(
                value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                separators=(",", ":"),
            )
        return text.encode("utf-8")
    except Exception as error:
        raise ValueError(ERROR) from error


def _csv_bytes(fields: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(
        handle, fieldnames=fields, extrasaction="raise", lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


def _strict_csv(payload: bytes, fields: Sequence[str]) -> list[dict[str, str]]:
    try:
        if (not payload or len(payload) >= 1024 * 1024
                or payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload
                or not payload.endswith(b"\n") or payload.endswith(b"\n\n")):
            raise ValueError(ERROR)
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if tuple(reader.fieldnames or ()) != tuple(fields):
            raise ValueError(ERROR)
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values())
               for row in rows):
            raise ValueError(ERROR)
        return rows
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _strict_json(payload: bytes, expected_type: type) -> Any:
    try:
        if (not payload or len(payload) >= 1024 * 1024
                or payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload
                or not payload.endswith(b"\n")):
            raise ValueError(ERROR)
        value = json.loads(payload.decode("utf-8"))
        if type(value) is not expected_type:
            raise ValueError(ERROR)
        return value
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _run_git(
    repo_root: Path, args: Sequence[str], *, allow_one: bool = False,
) -> tuple[int, bytes, bytes]:
    try:
        result = subprocess.run(
            ["git", *args], cwd=repo_root,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
            check=False, capture_output=True, timeout=30,
        )
    except Exception as error:
        raise ValueError(ERROR) from error
    if result.returncode not in ((0, 1) if allow_one else (0,)):
        raise ValueError(ERROR)
    return result.returncode, result.stdout, result.stderr


def _git(repo_root: Path, args: Sequence[str]) -> bytes:
    rc, out, err = _run_git(repo_root, args)
    if rc or err:
        raise ValueError(ERROR)
    return out


def _git_text(repo_root: Path, args: Sequence[str]) -> str:
    try:
        return _git(repo_root, args).decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(ERROR) from error


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    rc, out, err = _run_git(
        repo_root, ["merge-base", "--is-ancestor", ancestor, descendant],
        allow_one=True,
    )
    if out or err:
        raise ValueError(ERROR)
    return rc == 0


def _git_blob(
    repo_root: Path, commit: str, path: str, expected_sha: str,
) -> bytes:
    payload = _git(repo_root, ["show", f"{commit}:{path}"])
    if not payload or _sha256(payload) != expected_sha:
        raise ValueError(ERROR)
    return payload


def _state_root(repo_root: Path) -> Path:
    common = _git_text(
        repo_root, ["rev-parse", "--path-format=absolute", "--git-common-dir"],
    ).strip()
    candidate = Path(common).parent.parent / "covapie-state"
    if not candidate.is_dir():
        candidate = repo_root.parent / "covapie-state"
    if not candidate.is_dir():
        raise ValueError(ERROR)
    return candidate


def _source_inventory_rows() -> tuple[dict[str, str], ...]:
    return tuple({
        "evidence_id": evidence_id,
        "source_namespace": namespace,
        "source_commit_or_direct_producer": producer,
        "source_path": (f"state://{path}" if namespace != "git_object" else path),
        "source_sha256": digest,
        "lineage_note": note,
        "verified": "true",
    } for evidence_id, namespace, producer, path, digest, note in SOURCE_EVIDENCE)


def _validate_binding_predecessor(repo_root: Path) -> None:
    subject = _git_text(
        repo_root, ["show", "-s", "--format=%s", BINDING_COMMIT],
    ).strip()
    parents = _git_text(
        repo_root, ["show", "-s", "--format=%P", BINDING_COMMIT],
    ).split()
    changed = tuple(sorted(_git_text(
        repo_root,
        ["diff-tree", "--root", "--no-commit-id", "--name-only", "-r", BINDING_COMMIT],
    ).splitlines()))
    if (subject != BINDING_SUBJECT or parents != [BINDING_PARENT]
            or len(changed) != 9
            or not all(path.startswith(("data/derived/covalent_small/", "docs/", "scripts/", "src/", "tests/")) for path in changed)):
        raise ValueError(ERROR)


def _load_source_state(repo_root: Path) -> dict[str, Any]:
    _validate_binding_predecessor(repo_root)
    response = evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1(
        repo_root=repo_root,
    )
    if (response["binding_conclusion"] != "family_and_rule_not_authoritative"
            or response["current11_sample_count"] != 11
            or response["unique_warhead_rule_count"] != 7
            or response["reaction_family_authority_bound_count"] != 0
            or response["approved_warhead_rule_authority_bound_count"] != 0):
        raise ValueError(ERROR)

    blobs: dict[str, bytes] = {}
    for evidence_id, namespace, producer, path, digest, _note in SOURCE_EVIDENCE:
        if namespace == "git_object":
            blobs[evidence_id] = _git_blob(repo_root, producer, path, digest)
        else:
            state_path = _state_root(repo_root) / path
            try:
                metadata = state_path.lstat()
                payload = state_path.read_bytes()
            except OSError as error:
                raise ValueError(ERROR) from error
            if (not stat.S_ISREG(metadata.st_mode) or metadata.st_size != len(payload)
                    or _sha256(payload) != digest):
                raise ValueError(ERROR)
            blobs[evidence_id] = payload

    binding_manifest = json.loads(blobs["B04"].decode("utf-8"))
    if (binding_manifest.get("current11_matrix_row_count") != 11
            or binding_manifest.get("unique_family_rule_registry_row_count") != 7
            or binding_manifest.get("reaction_family_authority_bound_count") != 0
            or binding_manifest.get("approved_warhead_rule_authority_bound_count") != 0
            or binding_manifest.get("binding_conclusion")
            != "family_and_rule_not_authoritative"):
        raise ValueError(ERROR)
    return {
        "binding_commit": BINDING_COMMIT,
        "binding_conclusion": binding_manifest["binding_conclusion"],
        "binding_matrix": _strict_csv(blobs["B01"], BINDING_MATRIX_COLUMNS),
        "assignments": _strict_csv(blobs["C01"], ASSIGNMENT_COLUMNS),
        "rules": _strict_csv(blobs["C02"], RULE_COLUMNS),
        "effective_authority": json.loads(blobs["S01"].decode("utf-8")),
        "binding_response_digest": response["response_unsigned_canonical_json_sha256"],
    }


def _boundary_evidence(row: Mapping[str, Any]) -> dict[str, Any]:
    authority = row["effective_authority_record"]
    cardinality = row["effective_boundary_cardinality"]
    if cardinality == 1:
        boundaries = [{
            "boundary_bond_id": authority["reviewed_boundary_bond_id"],
            "boundary_bond_order": authority["reviewed_attachment_boundary_bond_order"],
            "warhead_attachment_atom_id": authority["reviewed_warhead_attachment_atom_id"],
            "nonwarhead_boundary_atom_id": authority["reviewed_nonwarhead_boundary_atom_id"],
        }]
        complete = authority.get("complete_warhead_atom_set_authority_available") is True
        exact = authority.get("exact_one_attachment_boundary_authority_available") is True
    elif cardinality == 2:
        boundaries = copy.deepcopy(authority["reviewed_boundary_records"])
        complete = authority.get("complete_warhead_atom_set_authority_available") is True
        exact = authority.get("exact_two_attachment_boundaries_authority_available") is True
    else:
        raise ValueError(ERROR)
    if (not complete or not exact or len(boundaries) != cardinality
            or authority.get("authority_status") != "active"
            or authority.get("sample_quarantined") is not False
            or len(authority.get("reviewed_warhead_atom_ids", ())) == 0):
        raise ValueError(ERROR)
    return {
        "effective_authority_namespace": row["effective_authority_namespace"],
        "effective_boundary_cardinality": cardinality,
        "precedence_reason": row["precedence_reason"],
        "reviewed_warhead_atom_ids": authority["reviewed_warhead_atom_ids"],
        "reviewed_attachment_boundaries": boundaries,
        "source_authority_record_sha256": row["source_authority_record_sha256"],
        "source_resolution_record_sha256": row["source_resolution_record_sha256"],
        "unified_effective_authority_record_sha256": row[
            "unified_effective_authority_record_sha256"
        ],
    }


def _derive_semantic_state(source: Mapping[str, Any]) -> dict[str, Any]:
    try:
        binding = source["binding_matrix"]
        assignments = source["assignments"]
        rules = source["rules"]
        effective = source["effective_authority"]["effective_authority_records"]
        if (len(binding) != 11 or len(assignments) != 11 or len(rules) != 7
                or len(effective) != 11):
            raise ValueError(ERROR)
        binding_by_sample = {row["sample_index_row_id"]: row for row in binding}
        assignment_by_sample = {row["sample_index_row_id"]: row for row in assignments}
        effective_by_sample = {row["sample_index_row_id"]: row for row in effective}
        rules_by_id = {row["warhead_rule_id"]: row for row in rules}
        sample_ids = tuple(row["sample_index_row_id"] for row in binding)
        if (len(binding_by_sample) != 11 or len(assignment_by_sample) != 11
                or len(effective_by_sample) != 11 or len(rules_by_id) != 7
                or set(sample_ids) != set(assignment_by_sample)
                or set(sample_ids) != set(effective_by_sample)):
            raise ValueError(ERROR)

        groups: dict[str, list[str]] = defaultdict(list)
        sample_support: list[dict[str, Any]] = []
        sample_details: dict[str, dict[str, Any]] = {}
        for sample in sample_ids:
            bound = binding_by_sample[sample]
            assignment = assignment_by_sample[sample]
            effective_row = effective_by_sample[sample]
            family_id = assignment["candidate_reaction_family_id"]
            rule_id = assignment["candidate_warhead_rule_id"]
            rule = rules_by_id.get(rule_id)
            authority = effective_row["effective_authority_record"]
            if (rule is None
                    or (bound["candidate_reaction_family_id"], bound["candidate_warhead_rule_id"])
                    != (family_id, rule_id)
                    or (rule["reaction_family_id"], authority["reaction_family_id"], authority["warhead_rule_id"])
                    != (family_id, family_id, rule_id)
                    or (bound["pdb_id"], bound["ligand_identity"])
                    != (assignment["pdb_id"], assignment["ligand_comp_id"])
                    or (authority["pdb_id"], authority["ligand_comp_id"])
                    != (assignment["pdb_id"], assignment["ligand_comp_id"])
                    or assignment["target_residue_name"] != "CYS"
                    or assignment["target_residue_atom_name"] != "SG"
                    or rule["target_residue_name"] != "CYS"
                    or rule["target_residue_atom_name"] != "SG"
                    or rule["formed_bond_order"] != "single"
                    or bound["boundary_review_completed"] != "true"
                    or bound["selected_candidate_identity_attested"] != "true"
                    or bound["reaction_family_identity_explicitly_attested"] != "false"
                    or bound["warhead_rule_identity_explicitly_attested"] != "false"
                    or bound["warhead_rule_full_semantics_explicitly_attested"] != "false"
                    or bound["approved_structural_pattern_attested"] != "false"
                    or rule["approved_warhead_smarts"] != ""
                    or rule["approved"] != "false"):
                raise ValueError(ERROR)
            boundary = _boundary_evidence(effective_row)
            groups[rule_id].append(sample)
            sample_details[sample] = {
                "binding": bound, "assignment": assignment, "rule": rule,
                "boundary": boundary,
            }

        review_units: list[dict[str, Any]] = []
        candidate_evidence: list[dict[str, Any]] = []
        lineage = list(_source_inventory_rows())
        for index, rule_id in enumerate(sorted(groups), start=1):
            covered = groups[rule_id]
            details = [sample_details[sample] for sample in covered]
            rule = details[0]["rule"]
            assignments_for_unit = [item["assignment"] for item in details]
            names = {row["candidate_reaction_family_semantic_name"] for row in assignments_for_unit}
            rule_names = {row["candidate_warhead_type_semantic_name"] for row in assignments_for_unit}
            if len(names) != 1 or rule_names != {rule["warhead_type_semantic_name"]}:
                raise ValueError(ERROR)
            graph_json = json.loads(rule["canonical_local_graph_rule_json"])
            if _sha256(_canonical_json_bytes(graph_json)) != rule["canonical_local_graph_rule_sha256"]:
                raise ValueError(ERROR)
            family_id = rule["reaction_family_id"]
            review_unit_id = f"CURRENT11_FAMILY_RULE_APPROVAL_REVIEW_UNIT_{index:06d}"
            cardinalities = Counter(item["boundary"]["effective_boundary_cardinality"] for item in details)
            frozen: dict[str, Any] = {
                "review_unit_id": review_unit_id,
                "reaction_family_id": family_id,
                "warhead_rule_id": rule_id,
                "sample_count": len(covered),
                "sample_index_row_ids": _canonical_json_bytes(covered).decode("utf-8"),
                "pdb_ligand_pairs": _canonical_json_bytes([
                    {"pdb_id": row["pdb_id"], "ligand_identity": row["ligand_comp_id"]}
                    for row in assignments_for_unit
                ]).decode("utf-8"),
                "candidate_reaction_family_semantic_name": next(iter(names)),
                "candidate_warhead_rule_semantic_name": rule["warhead_type_semantic_name"],
                "target_residue_types": "CYS",
                "target_residue_reactive_atom": "SG",
                "formed_bond_order": rule["formed_bond_order"],
                "candidate_local_graph_rule_sha256": rule["canonical_local_graph_rule_sha256"],
                "candidate_reaction_delta_class": rule["required_reaction_delta_class"],
                "candidate_leaving_group_summary": _canonical_json_bytes({
                    "allowed_elements": [item for item in rule["allowed_leaving_group_elements"].split(";") if item],
                    "required_count": int(rule["required_leaving_group_count"]),
                }).decode("utf-8"),
                "boundary_review_completed_count": sum(item["binding"]["boundary_review_completed"] == "true" for item in details),
                "selected_candidate_identity_attested_count": sum(item["binding"]["selected_candidate_identity_attested"] == "true" for item in details),
                "effective_boundary_cardinalities": _canonical_json_bytes({str(key): cardinalities[key] for key in sorted(cardinalities)}).decode("utf-8"),
                "approved_warhead_smarts_currently_available": "false",
                "formal_equivalent_structural_contract_currently_available": "false",
                "current_binding_conclusion": source["binding_conclusion"],
                "current_blocking_fields": details[0]["binding"]["binding_blockers"],
            }
            frozen["frozen_evidence_sha256"] = _sha256(_canonical_json_bytes(frozen))
            review_units.append(frozen)

            candidate_evidence.append({
                "review_unit_id": review_unit_id,
                "reaction_family_id": family_id,
                "warhead_rule_id": rule_id,
                "candidate_reaction_family_semantic_name": next(iter(names)),
                "candidate_warhead_rule_semantic_name": rule["warhead_type_semantic_name"],
                "canonical_local_graph_rule_json": graph_json,
                "canonical_local_graph_rule_sha256": rule["canonical_local_graph_rule_sha256"],
                "candidate_reaction_delta": {
                    "reaction_delta_class": rule["required_reaction_delta_class"],
                    "formed_bond_order": rule["formed_bond_order"],
                },
                "leaving_group_evidence": {
                    "required_leaving_group_count": int(rule["required_leaving_group_count"]),
                    "allowed_leaving_group_elements": [item for item in rule["allowed_leaving_group_elements"].split(";") if item],
                },
                "target_residue_types": [rule["target_residue_name"]],
                "target_residue_reactive_atom": rule["target_residue_atom_name"],
                "ligand_reactive_atom_evidence": [{
                    "sample_index_row_id": row["sample_index_row_id"],
                    "ligand_reactive_atom_name": row["ligand_reactive_atom_name"],
                    "ligand_reactive_atom_element": row["ligand_reactive_atom_element"],
                    "ligand_reactive_parent_ccd_atom_id": row["ligand_reactive_parent_ccd_atom_id"],
                } for row in assignments_for_unit],
                "formed_bond_order": rule["formed_bond_order"],
                "sample_index_row_ids": covered,
                "sample_graph_sha256s": [{
                    "sample_index_row_id": row["sample_index_row_id"],
                    "pre_reaction_graph_sha256": row["component_parent_graph_sha256"],
                    "observed_graph_sha256": row["observed_graph_sha256"],
                    "radius_1_signature_sha256": row["radius_1_signature_sha256"],
                } for row in assignments_for_unit],
                "effective_boundary_evidence": [{
                    "sample_index_row_id": item["assignment"]["sample_index_row_id"],
                    **item["boundary"],
                } for item in details],
                "source_commit_path_sha_lineage": lineage,
                "current_approval_state": {
                    "reaction_family_authority_bound": False,
                    "approved_warhead_rule_authority_bound": False,
                    "approved_warhead_smarts_currently_available": False,
                    "formal_equivalent_structural_contract_currently_available": False,
                    "candidate_local_graph_is_approved_structural_pattern": False,
                },
                "blockers": details[0]["binding"]["binding_blockers"].split(";"),
                "evidence_status": "candidate_supporting_evidence_only",
                "approved_authority": False,
            })

        unit_by_rule = {row["warhead_rule_id"]: row for row in review_units}
        for sample in sample_ids:
            item = sample_details[sample]
            assignment, rule, bound = item["assignment"], item["rule"], item["binding"]
            sample_support.append({
                "sample_index_row_id": sample,
                "pdb_id": assignment["pdb_id"],
                "ligand_identity": assignment["ligand_comp_id"],
                "review_unit_id": unit_by_rule[rule["warhead_rule_id"]]["review_unit_id"],
                "reaction_family_id": rule["reaction_family_id"],
                "warhead_rule_id": rule["warhead_rule_id"],
                "ligand_reactive_atom": assignment["ligand_reactive_atom_name"],
                "target_residue_atom": "CYS:SG",
                "pre_reaction_graph_sha256": assignment["component_parent_graph_sha256"],
                "reaction_delta_class": rule["required_reaction_delta_class"],
                "effective_boundary_cardinality": item["boundary"]["effective_boundary_cardinality"],
                "boundary_review_completed": bound["boundary_review_completed"],
                "selected_candidate_identity_attested": bound["selected_candidate_identity_attested"],
                "sample_supports_candidate_identity": "true",
                "sample_attests_full_family_or_rule_semantics": "false",
                "verified": "true",
            })
        state = {
            "binding_commit": source["binding_commit"],
            "binding_conclusion": source["binding_conclusion"],
            "review_units": review_units,
            "sample_support": sample_support,
            "candidate_evidence": candidate_evidence,
        }
        _validate_semantic_state(state)
        return state
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _validate_semantic_state(state: object) -> None:
    try:
        if type(state) is not dict:
            raise ValueError(ERROR)
        units = state["review_units"]
        samples = state["sample_support"]
        evidence = state["candidate_evidence"]
        if (state["binding_commit"] != BINDING_COMMIT
                or state["binding_conclusion"] != "family_and_rule_not_authoritative"
                or type(units) is not list or len(units) != 7
                or type(samples) is not list or len(samples) != 11
                or type(evidence) is not list or len(evidence) != 7):
            raise ValueError(ERROR)
        rule_ids = [row["warhead_rule_id"] for row in units]
        unit_ids = [row["review_unit_id"] for row in units]
        sample_ids = [row["sample_index_row_id"] for row in samples]
        if (rule_ids != sorted(rule_ids) or len(set(rule_ids)) != 7
                or len(set(unit_ids)) != 7 or len(set(sample_ids)) != 11
                or [row["warhead_rule_id"] for row in evidence] != rule_ids
                or [row["review_unit_id"] for row in evidence] != unit_ids
                or sum(int(row["sample_count"]) for row in units) != 11):
            raise ValueError(ERROR)
        membership: list[str] = []
        family_by_rule: dict[str, str] = {}
        samples_by_unit = {row["review_unit_id"]: [] for row in units}
        for row in samples:
            samples_by_unit.get(row["review_unit_id"], []).append(row["sample_index_row_id"])
            if (row["sample_supports_candidate_identity"] != "true"
                    or row["sample_attests_full_family_or_rule_semantics"] != "false"
                    or row["boundary_review_completed"] != "true"
                    or row["selected_candidate_identity_attested"] != "true"
                    or row["effective_boundary_cardinality"] not in (1, 2)
                    or row["target_residue_atom"] != "CYS:SG"):
                raise ValueError(ERROR)
        for row in units:
            covered = json.loads(row["sample_index_row_ids"])
            membership.extend(covered)
            if (covered != samples_by_unit[row["review_unit_id"]]
                    or len(covered) != int(row["sample_count"])
                    or row["boundary_review_completed_count"] != len(covered)
                    or row["selected_candidate_identity_attested_count"] != len(covered)
                    or row["approved_warhead_smarts_currently_available"] != "false"
                    or row["formal_equivalent_structural_contract_currently_available"] != "false"):
                raise ValueError(ERROR)
            frozen = {field: row[field] for field in FROZEN_FIELDS if field != "frozen_evidence_sha256"}
            if row["frozen_evidence_sha256"] != _sha256(_canonical_json_bytes(frozen)):
                raise ValueError(ERROR)
            rule = row["warhead_rule_id"]
            family = row["reaction_family_id"]
            if rule in family_by_rule and family_by_rule[rule] != family:
                raise ValueError(ERROR)
            family_by_rule[rule] = family
        if Counter(membership) != Counter(sample_ids):
            raise ValueError(ERROR)
        for row in evidence:
            if (row["evidence_status"] != "candidate_supporting_evidence_only"
                    or row["approved_authority"] is not False
                    or row["current_approval_state"]["candidate_local_graph_is_approved_structural_pattern"] is not False
                    or _sha256(_canonical_json_bytes(row["canonical_local_graph_rule_json"]))
                    != row["canonical_local_graph_rule_sha256"]
                    or any(boundary["effective_boundary_cardinality"] not in (1, 2)
                           for boundary in row["effective_boundary_evidence"])):
                raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _field_contract_rows() -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for order, field in enumerate(WORKLIST_FIELDS):
        frozen = field in FROZEN_FIELDS
        allowed = (
            ";".join(FAMILY_DECISIONS) if field == "reaction_family_review_decision"
            else ";".join(RULE_DECISIONS) if field == "warhead_rule_review_decision"
            else "true|false" if field.endswith("attested") or field == "review_completed"
            else ""
        )
        family_required = field in {
            "reviewed_reaction_family_version", "reviewed_reaction_family_semantic_name",
            "reviewed_reaction_family_structural_basis",
            "reaction_family_identity_explicitly_attested", "review_rationale",
            "reviewer_id", "attestor_id", "review_completed",
        }
        rule_required = field in set(RULE_HUMAN_FIELDS) - {
            "reviewed_warhead_rule_semantic_name", "warhead_rule_review_decision",
        } or field in {"review_rationale", "reviewer_id", "attestor_id", "review_completed"}
        rows.append({
            "field_order_0based": str(order), "field_name": field,
            "field_scope": "frozen_identity_or_evidence" if frozen else (
                "human_family" if field in FAMILY_HUMAN_FIELDS else
                "human_rule" if field in RULE_HUMAN_FIELDS else "human_provenance"
            ),
            "frozen": str(frozen).lower(), "human_fillable": str(not frozen).lower(),
            "initial_value": "derived_from_sha_bound_evidence" if frozen else "",
            "allowed_values": allowed,
            "future_approval_requirement": (
                "family_approve" if family_required and not rule_required else
                "rule_approve" if rule_required and not family_required else
                "family_approve|rule_approve" if family_required and rule_required else ""
            ),
            "semantic_note": (
                "must_remain_blank_at_materialization" if not frozen else
                "candidate_evidence_not_human_approval"
            ),
            "verified": "true",
        })
    return tuple(rows)


def _failure_rows() -> tuple[dict[str, str], ...]:
    return tuple({
        "case_id": case_id, "failure_case": name,
        "mutation_signature": mutation, "validator_target": target,
        "test_node_id": (
            "tests/test_covapie_current11_reaction_family_and_warhead_rule_"
            f"approval_review_package_v1.py::test_failure_matrix_case_fails_closed[{case_id}]"
        ),
        "expected_error": ERROR, "fails_closed": "true", "verified": "true",
    } for case_id, name, mutation, target in FAILURE_SPECS)


def _build_workspace_payloads_from_state(state: Mapping[str, Any]) -> dict[str, bytes]:
    _validate_semantic_state(state)
    worklist_rows = []
    for frozen in state["review_units"]:
        row = dict(frozen)
        row.update({field: "" for field in HUMAN_FIELDS})
        worklist_rows.append(row)
    payloads: dict[str, bytes] = {
        "README.md": README_TEXT.encode("utf-8"),
        "family_rule_approval_worklist.csv": _csv_bytes(WORKLIST_FIELDS, worklist_rows),
        "family_rule_candidate_evidence.json": _canonical_json_bytes(state["candidate_evidence"], pretty=True),
        "sample_support_evidence.csv": _csv_bytes(SAMPLE_SUPPORT_FIELDS, state["sample_support"]),
    }
    manifest = {
        "review_package_version": VERSION,
        "base_commit": BASE_COMMIT,
        "binding_commit": BINDING_COMMIT,
        "review_unit_count": 7,
        "sample_support_count": 11,
        "package_file_count": 5,
        "pending_review_unit_count": 7,
        "completed_review_unit_count": 0,
        "family_approved_count": 0,
        "rule_approved_count": 0,
        "quarantined_count": 0,
        "human_fields_initially_blank": True,
        "approved_smarts_materialized": False,
        "formal_equivalent_structural_contract_materialized": False,
        "review_package_materialized": True,
        "review_submission_compiled": False,
        "review_ingested": False,
        "authority_bundle_generated": False,
        "role_proposal_generated": False,
        "minimal_seed_generated": False,
        "ready_for_training": False,
        "package_file_sha256": {name: _sha256(payloads[name]) for name in WORKSPACE_FILES[:-1]},
    }
    payloads["review_package_manifest.json"] = _canonical_json_bytes(manifest, pretty=True)
    _validate_package_payloads(payloads)
    return payloads


def _validate_package_payloads(payloads: object) -> None:
    try:
        if type(payloads) is not dict or tuple(payloads) != WORKSPACE_FILES:
            raise ValueError(ERROR)
        if any(type(value) is not bytes or not value or len(value) >= 1024 * 1024
               or value.startswith(b"\xef\xbb\xbf") or b"\x00" in value
               for value in payloads.values()):
            raise ValueError(ERROR)
        if any(name.lower().endswith(FORBIDDEN_SUFFIXES) for name in payloads):
            raise ValueError(ERROR)
        if payloads["README.md"] != README_TEXT.encode("utf-8"):
            raise ValueError(ERROR)
        worklist = _strict_csv(payloads["family_rule_approval_worklist.csv"], WORKLIST_FIELDS)
        samples = _strict_csv(payloads["sample_support_evidence.csv"], SAMPLE_SUPPORT_FIELDS)
        evidence = _strict_json(payloads["family_rule_candidate_evidence.json"], list)
        manifest = _strict_json(payloads["review_package_manifest.json"], dict)
        if (len(worklist) != 7 or len(samples) != 11 or len(evidence) != 7
                or [row["warhead_rule_id"] for row in worklist] != sorted(row["warhead_rule_id"] for row in worklist)
                or [row["warhead_rule_id"] for row in evidence] != [row["warhead_rule_id"] for row in worklist]
                or any(row[field] != "" for row in worklist for field in HUMAN_FIELDS)
                or any(row["sample_supports_candidate_identity"] != "true"
                       or row["sample_attests_full_family_or_rule_semantics"] != "false"
                       for row in samples)):
            raise ValueError(ERROR)
        candidate_jsons = {
            _canonical_json_bytes(row["canonical_local_graph_rule_json"]).decode("utf-8")
            for row in evidence
        }
        if any(row["reviewed_warhead_smarts"] in candidate_jsons and row["reviewed_warhead_smarts"]
               for row in worklist):
            raise ValueError(ERROR)
        expected_manifest = {
            "review_package_version": VERSION, "base_commit": BASE_COMMIT,
            "binding_commit": BINDING_COMMIT, "review_unit_count": 7,
            "sample_support_count": 11, "package_file_count": 5,
            "pending_review_unit_count": 7, "completed_review_unit_count": 0,
            "family_approved_count": 0, "rule_approved_count": 0,
            "quarantined_count": 0, "human_fields_initially_blank": True,
            "approved_smarts_materialized": False,
            "formal_equivalent_structural_contract_materialized": False,
            "review_package_materialized": True,
            "review_submission_compiled": False, "review_ingested": False,
            "authority_bundle_generated": False, "role_proposal_generated": False,
            "minimal_seed_generated": False, "ready_for_training": False,
            "package_file_sha256": {
                name: _sha256(payloads[name]) for name in WORKSPACE_FILES[:-1]
            },
        }
        if manifest != expected_manifest:
            raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _repository_contract_payloads(state: Mapping[str, Any]) -> dict[str, bytes]:
    _validate_semantic_state(state)
    payloads: dict[str, bytes] = {
        SOURCE_INVENTORY_PATH: _csv_bytes(SOURCE_INVENTORY_COLUMNS, _source_inventory_rows()),
        FIELD_CONTRACT_PATH: _csv_bytes(FIELD_CONTRACT_COLUMNS, _field_contract_rows()),
        REVIEW_UNIT_MATRIX_PATH: _csv_bytes(REVIEW_UNIT_MATRIX_COLUMNS, state["review_units"]),
        FAILURE_MATRIX_PATH: _csv_bytes(FAILURE_MATRIX_COLUMNS, _failure_rows()),
    }
    manifest = {
        "review_package_version": VERSION,
        "base_commit": BASE_COMMIT,
        "binding_commit": BINDING_COMMIT,
        "source_inventory_row_count": len(SOURCE_EVIDENCE),
        "field_contract_row_count": len(WORKLIST_FIELDS),
        "review_unit_count": 7,
        "sample_support_count": 11,
        "failure_matrix_case_count": len(FAILURE_SPECS),
        "workspace_file_count": 5,
        "repository_candidate_file_count": 9,
        "publication_scheme": PUBLICATION_SCHEME,
        "canonical_workspace_entry_type": "symlink",
        "workspace_object_directory_mode": "0755",
        "workspace_internal_symlink_count": 0,
        "candidate_paths": list(CANDIDATE_PATHS),
        "lifecycle_profiles": [
            "review_package_precommit_candidate",
            "review_package_committed_unpushed",
            "review_package_published_successor",
        ],
        "formal_commit_subject": FORMAL_COMMIT_SUBJECT,
        "human_fields_initially_blank": True,
        "approved_smarts_materialized": False,
        "formal_equivalent_structural_contract_materialized": False,
        "review_submission_compiled": False,
        "review_ingested": False,
        "authority_bundle_generated": False,
        "role_proposal_generated": False,
        "minimal_seed_generated": False,
        "ready_for_training": False,
        "evidence_sha256": {Path(path).name: _sha256(payloads[path]) for path in (
            SOURCE_INVENTORY_PATH, FIELD_CONTRACT_PATH, REVIEW_UNIT_MATRIX_PATH,
            FAILURE_MATRIX_PATH,
        )},
    }
    payloads[REPO_MANIFEST_PATH] = _canonical_json_bytes(manifest, pretty=True)
    return payloads


def _validate_repository_contract_artifacts(repo_root: Path, state: Mapping[str, Any]) -> None:
    expected = _repository_contract_payloads(state)
    try:
        actual = {path: (repo_root / path).read_bytes() for path in expected}
    except OSError as error:
        raise ValueError(ERROR) from error
    if actual != expected:
        raise ValueError(ERROR)


def _collect_live_identity(repo_root: Path, path: str) -> dict[str, object]:
    candidate = repo_root / path
    try:
        metadata = candidate.lstat()
    except OSError as error:
        raise ValueError(ERROR) from error
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(ERROR)
    blob = _git_text(repo_root, ["hash-object", "--no-filters", "--", path]).strip()
    line = _git_text(repo_root, ["ls-files", "--stage", "--", path]).strip()
    if re.fullmatch(r"[0-9a-f]{40}", blob) is None:
        raise ValueError(ERROR)
    if line:
        metadata_text, listed = line.split("\t", 1)
        mode, index_blob, stage = metadata_text.split()
        if listed != path or stage != "0":
            raise ValueError(ERROR)
        return {"tracked": True, "mode": mode, "index_blob": index_blob, "blob": blob}
    return {"tracked": False, "mode": f"100{stat.S_IMODE(metadata.st_mode):03o}", "blob": blob}


def _collect_lifecycle(repo_root: Path) -> dict[str, object]:
    head = _git_text(repo_root, ["rev-parse", "HEAD"]).strip()
    origin = _git_text(repo_root, ["rev-parse", "refs/remotes/origin/main"]).strip()
    ahead_text, behind_text = _git_text(
        repo_root, ["rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"],
    ).split()
    revisions = set(_git_text(repo_root, ["rev-list", f"{BASE_COMMIT}..{head}"]).splitlines())
    revisions.update(_git_text(repo_root, ["rev-list", f"{BASE_COMMIT}..{origin}"]).splitlines())
    path_commits: list[dict[str, object]] = []
    for commit in sorted(revisions):
        status_lines = _git_text(
            repo_root, ["diff-tree", "--root", "--no-commit-id", "--name-status", "-r", commit],
        ).splitlines()
        statuses = {parts[1]: parts[0] for parts in (line.split("\t") for line in status_lines) if len(parts) == 2}
        if not set(statuses).intersection(CANDIDATE_PATHS):
            continue
        modes, blobs = {}, {}
        for path in CANDIDATE_PATHS:
            line = _git_text(repo_root, ["ls-tree", commit, "--", path]).strip()
            if line:
                metadata, listed = line.split("\t", 1)
                mode, kind, blob = metadata.split()
                if listed != path or kind != "blob":
                    raise ValueError(ERROR)
                modes[path], blobs[path] = mode, blob
        path_commits.append({
            "commit": commit,
            "parents": _git_text(repo_root, ["show", "-s", "--format=%P", commit]).split(),
            "subject": _git_text(repo_root, ["show", "-s", "--format=%s", commit]).strip(),
            "changed_paths": tuple(sorted(statuses)),
            "changed_statuses": {path: statuses[path] for path in sorted(statuses)},
            "path_modes": modes, "path_blobs": blobs,
            "ancestor_head": _is_ancestor(repo_root, commit, head),
            "ancestor_origin": _is_ancestor(repo_root, commit, origin),
        })
    tracked = tuple(sorted(_git_text(repo_root, ["diff", "--name-only"]).splitlines()))
    staged = tuple(sorted(_git_text(repo_root, ["diff", "--cached", "--name-only"]).splitlines()))
    untracked = tuple(sorted(_git_text(repo_root, ["ls-files", "--others", "--exclude-standard"]).splitlines()))
    porcelain = tuple(_git_text(
        repo_root, ["status", "--porcelain=v1", "--untracked-files=all"],
    ).splitlines())
    return {
        "head": head, "origin": origin, "ahead": int(ahead_text), "behind": int(behind_text),
        "branch": _git_text(repo_root, ["branch", "--show-current"]).strip(),
        "remote": _git_text(repo_root, ["remote", "get-url", "origin"]).strip(),
        "base_ancestor_head": _is_ancestor(repo_root, BASE_COMMIT, head),
        "base_ancestor_origin": _is_ancestor(repo_root, BASE_COMMIT, origin),
        "tracked": tracked, "staged": staged, "untracked": untracked,
        "porcelain": porcelain,
        "path_commits": path_commits,
        "live_paths": {path: _collect_live_identity(repo_root, path) for path in CANDIDATE_PATHS},
    }


def _derive_lifecycle(facts: object) -> dict[str, object]:
    try:
        if type(facts) is not dict:
            raise ValueError(ERROR)
        if (facts["branch"] != BRANCH or facts["remote"] != REMOTE
                or facts["base_ancestor_head"] is not True
                or facts["base_ancestor_origin"] is not True
                or type(facts["path_commits"]) is not list
                or len(facts["path_commits"]) > 1
                or type(facts["porcelain"]) is not tuple
                or tuple(facts["live_paths"]) != CANDIDATE_PATHS):
            raise ValueError(ERROR)
        commits = facts["path_commits"]
        if not commits:
            if (facts["head"] != BASE_COMMIT or facts["origin"] != BASE_COMMIT
                    or (facts["ahead"], facts["behind"]) != (0, 0)
                    or facts["tracked"] or facts["staged"]
                    or facts["untracked"] != CANDIDATE_PATHS
                    or facts["porcelain"] != tuple(f"?? {path}" for path in CANDIDATE_PATHS)
                    or any(item != {"tracked": False, "mode": "100644", "blob": item["blob"]}
                           for item in facts["live_paths"].values())):
                raise ValueError(ERROR)
            return {
                "origin_main": BASE_COMMIT, "ahead": 0, "behind": 0,
                "review_package_lifecycle_profile": "review_package_precommit_candidate",
                "review_package_commit": None, "review_package_committed": False,
                "review_package_published": False,
                "ready_for_review_package_commit_review": True,
            }
        commit = commits[0]
        if (re.fullmatch(r"[0-9a-f]{40}", str(commit["commit"])) is None
                or commit["parents"] != [BASE_COMMIT]
                or commit["subject"] != FORMAL_COMMIT_SUBJECT
                or commit["changed_paths"] != CANDIDATE_PATHS
                or commit["changed_statuses"] != {path: "A" for path in CANDIDATE_PATHS}
                or any(commit["path_modes"].get(path) != "100644" for path in CANDIDATE_PATHS)
                or any(facts["live_paths"][path] != {
                    "tracked": True, "mode": "100644",
                    "index_blob": commit["path_blobs"].get(path),
                    "blob": commit["path_blobs"].get(path),
                } for path in CANDIDATE_PATHS)
                or commit["ancestor_head"] is not True
                or any(path in facts["tracked"] or path in facts["staged"] or path in facts["untracked"] for path in CANDIDATE_PATHS)):
            raise ValueError(ERROR)
        if commit["ancestor_origin"] is True:
            return {
                "origin_main": facts["origin"], "ahead": facts["ahead"], "behind": facts["behind"],
                "review_package_lifecycle_profile": "review_package_published_successor",
                "review_package_commit": commit["commit"], "review_package_committed": True,
                "review_package_published": True,
                "ready_for_review_package_commit_review": False,
            }
        if (facts["head"] != commit["commit"] or facts["origin"] != BASE_COMMIT
                or (facts["ahead"], facts["behind"]) != (1, 0)
                or facts["tracked"] or facts["staged"] or facts["untracked"]
                or facts["porcelain"]):
            raise ValueError(ERROR)
        return {
            "origin_main": BASE_COMMIT, "ahead": 1, "behind": 0,
            "review_package_lifecycle_profile": "review_package_committed_unpushed",
            "review_package_commit": commit["commit"], "review_package_committed": True,
            "review_package_published": False,
            "ready_for_review_package_commit_review": False,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _validate_lifecycle_witness(expected_lifecycle: object) -> None:
    try:
        if (type(expected_lifecycle) is not dict
                or tuple(expected_lifecycle) != _RESPONSE_LIFECYCLE_FIELDS
                or any(type(expected_lifecycle[field]) is not int
                       for field in ("ahead", "behind"))
                or any(type(expected_lifecycle[field]) is not bool for field in (
                    "review_package_committed", "review_package_published",
                    "ready_for_review_package_commit_review",
                ))
                or type(expected_lifecycle["origin_main"]) is not str
                or type(expected_lifecycle["review_package_lifecycle_profile"]) is not str
                or (expected_lifecycle["review_package_commit"] is not None
                    and type(expected_lifecycle["review_package_commit"]) is not str)):
            raise ValueError(ERROR)
        profile = expected_lifecycle["review_package_lifecycle_profile"]
        commit = expected_lifecycle["review_package_commit"]
        origin = expected_lifecycle["origin_main"]
        ahead, behind = expected_lifecycle["ahead"], expected_lifecycle["behind"]
        if (re.fullmatch(r"[0-9a-f]{40}", origin) is None
                or ahead < 0 or behind < 0):
            raise ValueError(ERROR)
        if profile == "review_package_precommit_candidate":
            expected = (None, False, False, True, BASE_COMMIT, 0, 0)
        elif profile == "review_package_committed_unpushed":
            if (type(commit) is not str
                    or re.fullmatch(r"[0-9a-f]{40}", commit) is None
                    or commit == BASE_COMMIT):
                raise ValueError(ERROR)
            expected = (commit, True, False, False, BASE_COMMIT, 1, 0)
        elif profile == "review_package_published_successor":
            if (type(commit) is not str
                    or re.fullmatch(r"[0-9a-f]{40}", commit) is None
                    or commit == BASE_COMMIT):
                raise ValueError(ERROR)
            expected = (commit, True, True, False, origin, ahead, behind)
        else:
            raise ValueError(ERROR)
        actual = (
            commit, expected_lifecycle["review_package_committed"],
            expected_lifecycle["review_package_published"],
            expected_lifecycle["ready_for_review_package_commit_review"],
            origin, ahead, behind,
        )
        if actual != expected:
            raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _validate_workspace_hash_witness_v1(
    expected_workspace_file_sha256: object,
) -> None:
    try:
        if (type(expected_workspace_file_sha256) is not dict
                or tuple(expected_workspace_file_sha256) != WORKSPACE_FILES
                or any(type(digest) is not str
                       for digest in expected_workspace_file_sha256.values())
                or any(re.fullmatch(r"[0-9a-f]{64}", digest) is None
                       for digest in expected_workspace_file_sha256.values())):
            raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _workspace_file_sha256_witness_v1(
    payloads: Mapping[str, bytes],
) -> dict[str, str]:
    try:
        if (type(payloads) is not dict
                or tuple(payloads) != WORKSPACE_FILES
                or any(type(payload) is not bytes
                       for payload in payloads.values())
                or any(not payload or len(payload) >= 1024 * 1024
                       for payload in payloads.values())):
            raise ValueError(ERROR)
        witness = {
            name: _sha256(payloads[name]) for name in WORKSPACE_FILES
        }
        _validate_workspace_hash_witness_v1(witness)
        return witness
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _validate_response(
    response: object, *, expected_lifecycle: Mapping[str, object],
    expected_workspace_file_sha256: Mapping[str, str],
) -> None:
    try:
        _validate_lifecycle_witness(expected_lifecycle)
        _validate_workspace_hash_witness_v1(
            expected_workspace_file_sha256,
        )
        if (type(response) is not dict or tuple(response) != _RESPONSE_FIELDS
                or any(type(response[field]) is not int
                       for field in _RESPONSE_INT_FIELDS)
                or any(type(response[field]) is not bool
                       for field in _RESPONSE_BOOL_FIELDS)
                or any(type(response[field]) is not str
                       for field in _RESPONSE_STRING_FIELDS)
                or any(type(response[field]) is not dict
                       for field in _RESPONSE_TUPLE_OR_DICT_FIELDS)
                or (response["review_package_commit"] is not None
                    and type(response["review_package_commit"]) is not str)):
            raise ValueError(ERROR)
        _validate_workspace_hash_witness_v1(
            response["workspace_file_sha256"],
        )
        projection = {
            field: response[field] for field in _RESPONSE_LIFECYCLE_FIELDS
        }
        _validate_lifecycle_witness(projection)
        if (projection != expected_lifecycle
                or response["review_package_version"] != VERSION
                or response["base_commit"] != BASE_COMMIT
                or response["binding_commit"] != BINDING_COMMIT
                or response["review_unit_count"] != 7
                or response["sample_support_count"] != 11
                or response["package_file_count"] != 5
                or response["publication_scheme"] != PUBLICATION_SCHEME
                or response["workspace_file_sha256"]
                != expected_workspace_file_sha256
                or any(response[field] is not False for field in EXECUTION_BOUNDARY_FIELDS)):
            raise ValueError(ERROR)
        unsigned = {key: value for key, value in response.items() if key != "response_sha256"}
        if response["response_sha256"] != _sha256(_canonical_json_bytes(unsigned)):
            raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _build_response(lifecycle: Mapping[str, object], payloads: Mapping[str, bytes]) -> dict[str, object]:
    external_lifecycle_witness = {
        field: lifecycle[field] for field in _RESPONSE_LIFECYCLE_FIELDS
    }
    external_workspace_hash_witness = _workspace_file_sha256_witness_v1(
        payloads,
    )
    _validate_lifecycle_witness(external_lifecycle_witness)
    response: dict[str, object] = {
        "review_package_version": VERSION,
        "base_commit": BASE_COMMIT,
        "binding_commit": BINDING_COMMIT,
        **external_lifecycle_witness,
        "review_unit_count": 7,
        "sample_support_count": 11,
        "package_file_count": 5,
        "publication_scheme": PUBLICATION_SCHEME,
        "workspace_file_sha256": dict(external_workspace_hash_witness),
        **{field: False for field in EXECUTION_BOUNDARY_FIELDS},
        "response_sha256": "",
    }
    response["response_sha256"] = _sha256(_canonical_json_bytes({
        key: value for key, value in response.items() if key != "response_sha256"
    }))
    if tuple(response) != _RESPONSE_FIELDS:
        raise ValueError(ERROR)
    _validate_response(
        response,
        expected_lifecycle=external_lifecycle_witness,
        expected_workspace_file_sha256=external_workspace_hash_witness,
    )
    return response


def _build_for_validation(repo_root: Path, *, validate_candidate: bool) -> tuple[dict[str, bytes], dict[str, Any], dict[str, object]]:
    source = _load_source_state(repo_root)
    state = _derive_semantic_state(source)
    if validate_candidate:
        _validate_repository_contract_artifacts(repo_root, state)
        lifecycle = _derive_lifecycle(_collect_lifecycle(repo_root))
    else:
        lifecycle = {
            "origin_main": BASE_COMMIT, "ahead": 0, "behind": 0,
            "review_package_lifecycle_profile": "review_package_precommit_candidate",
            "review_package_commit": None, "review_package_committed": False,
            "review_package_published": False,
            "ready_for_review_package_commit_review": True,
        }
    payloads = _build_workspace_payloads_from_state(state)
    response = _build_response(lifecycle, payloads)
    return payloads, state, response


def build_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1(
    *, repo_root: Path,
) -> dict[str, bytes]:
    """Return the deterministic, unfilled Exact5 review workspace in memory."""

    try:
        if type(repo_root) is not type(Path()) or not repo_root.is_absolute():
            raise ValueError(ERROR)
        if Path(_git_text(repo_root, ["rev-parse", "--show-toplevel"]).strip()) != repo_root:
            raise ValueError(ERROR)
        payloads, _state, _response = _build_for_validation(
            repo_root, validate_candidate=True,
        )
        second = _build_workspace_payloads_from_state(_derive_semantic_state(_load_source_state(repo_root)))
        if payloads != second:
            raise ValueError(ERROR)
        return payloads
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _synthetic_lifecycle_facts(profile: str) -> dict[str, object]:
    blob = "1" * 40
    live_untracked = {path: {"tracked": False, "mode": "100644", "blob": blob} for path in CANDIDATE_PATHS}
    base = {
        "head": BASE_COMMIT, "origin": BASE_COMMIT, "ahead": 0, "behind": 0,
        "branch": BRANCH, "remote": REMOTE, "base_ancestor_head": True,
        "base_ancestor_origin": True, "tracked": (), "staged": (),
        "untracked": CANDIDATE_PATHS,
        "porcelain": tuple(f"?? {path}" for path in CANDIDATE_PATHS),
        "path_commits": [], "live_paths": live_untracked,
    }
    if profile == "review_package_precommit_candidate":
        return base
    commit = "a" * 40
    blobs = {path: blob for path in CANDIDATE_PATHS}
    base.update({
        "head": commit, "ahead": 1, "untracked": (), "porcelain": (),
        "path_commits": [{
            "commit": commit, "parents": [BASE_COMMIT], "subject": FORMAL_COMMIT_SUBJECT,
            "changed_paths": CANDIDATE_PATHS,
            "changed_statuses": {path: "A" for path in CANDIDATE_PATHS},
            "path_modes": {path: "100644" for path in CANDIDATE_PATHS},
            "path_blobs": blobs, "ancestor_head": True, "ancestor_origin": False,
        }],
        "live_paths": {path: {"tracked": True, "mode": "100644", "index_blob": blob, "blob": blob} for path in CANDIDATE_PATHS},
    })
    return base


def _failure_baseline(case_id: str, state: Mapping[str, Any], payloads: Mapping[str, bytes], response: Mapping[str, Any]) -> tuple[object, Callable[[object], None]]:
    target = {case: target for case, _name, _mutation, target in FAILURE_SPECS}[case_id]
    if target in {"source_state", "semantic_state"}:
        return copy.deepcopy(state), _validate_semantic_state
    if target in {"package_payloads", "workspace"}:
        return copy.deepcopy(dict(payloads)), _validate_package_payloads
    if target == "lifecycle":
        return _synthetic_lifecycle_facts("review_package_committed_unpushed"), lambda value: _derive_lifecycle(value) and None
    if target == "response":
        external_lifecycle_witness = {
            field: copy.deepcopy(response[field])
            for field in _RESPONSE_LIFECYCLE_FIELDS
        }
        external_workspace_hash_witness = (
            _workspace_file_sha256_witness_v1(payloads)
        )
        return (
            copy.deepcopy(dict(response)),
            lambda value: _validate_response(
                value,
                expected_lifecycle=external_lifecycle_witness,
                expected_workspace_file_sha256=(
                    external_workspace_hash_witness
                ),
            ),
        )
    raise ValueError(ERROR)


def _rehash_response(response: dict[str, Any]) -> None:
    response["response_sha256"] = _sha256(_canonical_json_bytes({
        key: value for key, value in response.items() if key != "response_sha256"
    }))


def _rewrite_worklist(payloads: dict[str, bytes], rows: list[dict[str, str]], fields: Sequence[str] = WORKLIST_FIELDS) -> None:
    payloads["family_rule_approval_worklist.csv"] = _csv_bytes(fields, rows)
    manifest = _strict_json(payloads["review_package_manifest.json"], dict)
    manifest["package_file_sha256"]["family_rule_approval_worklist.csv"] = _sha256(payloads["family_rule_approval_worklist.csv"])
    payloads["review_package_manifest.json"] = _canonical_json_bytes(manifest, pretty=True)


def _apply_failure_mutation(case_id: str, value: object) -> None:
    if case_id in {f"X{number:02d}" for number in range(1, 16)}:
        state = value
        assert isinstance(state, dict)
        units, samples, evidence = state["review_units"], state["sample_support"], state["candidate_evidence"]
        if case_id == "X01": state["binding_commit"] = "f" * 40
        elif case_id == "X02": state["binding_conclusion"] = "authoritative"
        elif case_id == "X03": units.pop()
        elif case_id == "X04": samples.pop()
        elif case_id == "X05": units[-1] = copy.deepcopy(units[0])
        elif case_id == "X06": samples[-1] = copy.deepcopy(samples[0])
        elif case_id == "X07": samples[0]["sample_index_row_id"] = "MISSING_SAMPLE"
        elif case_id == "X08":
            covered = json.loads(units[1]["sample_index_row_ids"])
            covered.append(json.loads(units[0]["sample_index_row_ids"])[0])
            units[1]["sample_index_row_ids"] = _canonical_json_bytes(covered).decode()
        elif case_id == "X09": units[0]["warhead_rule_id"] = units[1]["warhead_rule_id"]
        elif case_id == "X10": units[0]["sample_count"] += 1
        elif case_id == "X11": units[0]["reaction_family_id"] = "COVAPIE_CHANGED_FAMILY"
        elif case_id == "X12": units[0]["warhead_rule_id"] = "COVAPIE_CHANGED_RULE"
        elif case_id == "X13": units[0]["candidate_reaction_family_semantic_name"] += "_changed"
        elif case_id == "X14": evidence[0]["canonical_local_graph_rule_sha256"] = "0" * 64
        elif case_id == "X15": evidence[0]["effective_boundary_evidence"][0]["effective_boundary_cardinality"] = 3
        return
    if case_id in {f"X{number:02d}" for number in range(16, 31)} | {"X38", "X39"}:
        payloads = value
        assert isinstance(payloads, dict)
        if case_id in {"X16", "X17", "X18", "X19", "X20", "X21", "X22", "X23"}:
            rows = _strict_csv(payloads["family_rule_approval_worklist.csv"], WORKLIST_FIELDS)
            evidence = _strict_json(payloads["family_rule_candidate_evidence.json"], list)
            field_value = {
                "X16": ("reviewed_warhead_smarts", _canonical_json_bytes(evidence[0]["canonical_local_graph_rule_json"]).decode()),
                "X17": ("reviewed_reaction_family_semantic_name", rows[0]["candidate_reaction_family_semantic_name"]),
                "X18": ("reviewed_reaction_family_version", "v1"),
                "X19": ("reviewed_warhead_rule_version", "v1"),
                "X20": ("reaction_family_identity_explicitly_attested", "false"),
                "X21": ("reaction_family_review_decision", "pending"),
                "X22": ("reviewer_id", "machine"),
                "X23": ("review_completed", "false"),
            }[case_id]
            rows[0][field_value[0]] = field_value[1]
            _rewrite_worklist(payloads, rows)
        elif case_id == "X24":
            manifest = _strict_json(payloads["review_package_manifest.json"], dict)
            manifest["package_file_count"] = 4
            payloads["review_package_manifest.json"] = _canonical_json_bytes(manifest, pretty=True)
        elif case_id == "X25": payloads["extra.txt"] = b"extra\n"
        elif case_id == "X26": del payloads["README.md"]
        elif case_id == "X27":
            manifest = _strict_json(payloads["review_package_manifest.json"], dict)
            manifest["package_file_sha256"]["README.md"] = "0" * 64
            payloads["review_package_manifest.json"] = _canonical_json_bytes(manifest, pretty=True)
        elif case_id == "X28":
            rows = _strict_csv(payloads["family_rule_approval_worklist.csv"], WORKLIST_FIELDS)
            fields = (WORKLIST_FIELDS[1], WORKLIST_FIELDS[0], *WORKLIST_FIELDS[2:])
            _rewrite_worklist(payloads, rows, fields)
        elif case_id == "X29":
            rows = _strict_csv(payloads["sample_support_evidence.csv"], SAMPLE_SUPPORT_FIELDS)
            fields = (SAMPLE_SUPPORT_FIELDS[1], SAMPLE_SUPPORT_FIELDS[0], *SAMPLE_SUPPORT_FIELDS[2:])
            payloads["sample_support_evidence.csv"] = _csv_bytes(fields, rows)
        elif case_id == "X30":
            evidence = _strict_json(payloads["family_rule_candidate_evidence.json"], list)
            evidence[0], evidence[1] = evidence[1], evidence[0]
            payloads["family_rule_candidate_evidence.json"] = _canonical_json_bytes(evidence, pretty=True)
        elif case_id == "X38":
            payloads["README.md"] += b"mode=0600\n"
        elif case_id == "X39": payloads["sample.pdb"] = b"HEADER\n"
        return
    if case_id in {"X40", "X41", "X44", "X49"}:
        response = value
        assert isinstance(response, dict)
        if case_id == "X40": response["raw_structure_read"] = True
        elif case_id == "X41": response["review_unit_count"] = 6
        elif case_id == "X44": response["origin_main"] = "b" * 40
        else:
            replacement = "f" * 64
            assert response["workspace_file_sha256"]["README.md"] != replacement
            response["workspace_file_sha256"]["README.md"] = replacement
        _rehash_response(response)
        return
    if case_id in {"X42", "X43"}:
        facts = value
        assert isinstance(facts, dict)
        if case_id == "X42": facts["path_commits"][0]["parents"] = ["b" * 40]
        else:
            path = CANDIDATE_PATHS[0]
            facts["live_paths"][path]["blob"] = "c" * 40
        return
    raise ValueError(ERROR)
