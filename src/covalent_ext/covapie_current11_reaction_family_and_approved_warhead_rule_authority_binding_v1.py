"""Bind Current11 family/rule authority, or report the exact closed gaps.

This gate reads only committed metadata blobs and SHA-bound review-state text.
It does not read structures, execute chemistry, import Torch/RDKit, or write.
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
from typing import Any, Mapping, Sequence


__all__ = (
    "evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1",
)


_ERROR = "COVAPIE_CURRENT11_FAMILY_RULE_AUTHORITY_BINDING_INVALID"
_VERSION = (
    "covapie_current11_reaction_family_and_approved_warhead_rule_"
    "authority_binding_v1"
)
_REPOSITORY = "fumx2000/DiffSBDD"
_REMOTE = "git@github.com:fumx2000/DiffSBDD.git"
_BRANCH = "main"
_BASE = "0e36e3131750dcb99f806ec635afeae2b0b0dc88"
_BASE_SUBJECT = "add CovaPIE role annotation input authority gap resolution v1"
_FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 reaction family and approved warhead rule "
    "authority binding v1"
)
_RECOMMENDED_NEXT = (
    "materialize_covapie_current11_reaction_family_and_warhead_rule_"
    "approval_review_package_v1"
)
_STATUSES = ("authoritative_resolved", "candidate_only", "missing", "conflicted")
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)
_EXPECTED_IDENTITIES = (
    ("CYS_SG_SAMPLE_INDEX_000001", "6BV6", "JUG", "COVAPIE_CYS_SG_REACTION_FAMILY_6A5C7B2B614B5F52", "COVAPIE_CYS_SG_WARHEAD_RULE_8B640E1A031138F0"),
    ("CYS_SG_SAMPLE_INDEX_000002", "6BV8", "JUG", "COVAPIE_CYS_SG_REACTION_FAMILY_6A5C7B2B614B5F52", "COVAPIE_CYS_SG_WARHEAD_RULE_8B640E1A031138F0"),
    ("CYS_SG_SAMPLE_INDEX_000003", "6BV5", "JUG", "COVAPIE_CYS_SG_REACTION_FAMILY_6A5C7B2B614B5F52", "COVAPIE_CYS_SG_WARHEAD_RULE_8B640E1A031138F0"),
    ("CYS_SG_SAMPLE_INDEX_000004", "1AEC", "E64", "COVAPIE_CYS_SG_REACTION_FAMILY_4C9251579704AD85", "COVAPIE_CYS_SG_WARHEAD_RULE_3B7FB1395768B690"),
    ("CYS_SG_SAMPLE_INDEX_000005", "1AIM", "ZYA", "COVAPIE_CYS_SG_REACTION_FAMILY_DC230CD72B1283D2", "COVAPIE_CYS_SG_WARHEAD_RULE_EE022EB419200D14"),
    ("CYS_SG_SAMPLE_INDEX_000006", "1AU3", "PCM", "COVAPIE_CYS_SG_REACTION_FAMILY_E02CDE030B1009B1", "COVAPIE_CYS_SG_WARHEAD_RULE_1D1D9C797859191F"),
    ("CYS_SG_SAMPLE_INDEX_000007", "1AU4", "INP", "COVAPIE_CYS_SG_REACTION_FAMILY_E02CDE030B1009B1", "COVAPIE_CYS_SG_WARHEAD_RULE_1D1D9C797859191F"),
    ("CYS_SG_SAMPLE_INDEX_000008", "1AYU", "INA", "COVAPIE_CYS_SG_REACTION_FAMILY_11AA213C661B48E3", "COVAPIE_CYS_SG_WARHEAD_RULE_106441A31FA4F951"),
    ("CYS_SG_SAMPLE_INDEX_000009", "1AYV", "IN6", "COVAPIE_CYS_SG_REACTION_FAMILY_888A8E40AB92B0F8", "COVAPIE_CYS_SG_WARHEAD_RULE_DF48FCEE8872B92A"),
    ("CYS_SG_SAMPLE_INDEX_000010", "1AYW", "IN3", "COVAPIE_CYS_SG_REACTION_FAMILY_11AA213C661B48E3", "COVAPIE_CYS_SG_WARHEAD_RULE_106441A31FA4F951"),
    ("CYS_SG_SAMPLE_INDEX_000011", "1B02", "UFP", "COVAPIE_CYS_SG_REACTION_FAMILY_9869A5B1C585A27C", "COVAPIE_CYS_SG_WARHEAD_RULE_CEAC766EEE61D251"),
)

_DATA_ROOT = (
    "data/derived/covalent_small/"
    "covapie_current11_reaction_family_and_approved_warhead_rule_"
    "authority_binding_v1"
)
_SOURCE_PATH = f"{_DATA_ROOT}/covapie_family_rule_binding_source_inventory.csv"
_MATRIX_PATH = f"{_DATA_ROOT}/covapie_current11_family_rule_authority_binding_matrix.csv"
_REGISTRY_PATH = f"{_DATA_ROOT}/covapie_family_and_warhead_rule_authority_registry.csv"
_FAILURE_PATH = f"{_DATA_ROOT}/covapie_family_rule_authority_failure_matrix.csv"
_MANIFEST_PATH = f"{_DATA_ROOT}/covapie_family_rule_authority_binding_manifest.json"
_GENERATED_PATHS = (
    _SOURCE_PATH, _MATRIX_PATH, _REGISTRY_PATH, _FAILURE_PATH, _MANIFEST_PATH,
)
_CANDIDATE_PATHS = tuple(sorted((
    *_GENERATED_PATHS,
    "docs/covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1_guide.md",
    "scripts/check_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1.py",
    "src/covalent_ext/covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1.py",
    "tests/test_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1.py",
)))
_FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part", ".pdb", ".sdf",
)

_GAP_ROOT = (
    "data/derived/covalent_small/"
    "covapie_role_annotation_input_authority_gap_resolution_v1"
)
_ASSIGNMENT = (
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1/"
    "covapie_current11_cys_sg_candidate_assignment_authority.csv"
)
_RULE_REGISTRY = (
    "data/derived/covalent_small/"
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1/"
    "covapie_cys_sg_warhead_rule_registry.csv"
)
_OBS_ROOT = (
    "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1"
)
_PREDECESSOR_ROOT = (
    "data/derived/covalent_small/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1"
)

# id, commit, path, SHA256, authority class, lineage note
_GIT_EVIDENCE = (
    ("E01", _BASE, f"{_GAP_ROOT}/covapie_current11_role_input_authority_matrix.csv", "fc7897121bf216488c239ecd2ad678bc23501f72db1fea85212b083c5af7b06b", "predecessor_result", "latest_gap_matrix"),
    ("E02", _BASE, f"{_GAP_ROOT}/covapie_role_input_authority_semantics_registry.csv", "6e08352146376bc3a4635b9c2a3155246e4a69dbc1a560c580573548a2479adb", "predecessor_contract", "latest_gap_semantics"),
    ("E03", _BASE, f"{_GAP_ROOT}/covapie_role_input_authority_gap_resolution_manifest.json", "a9a21691c553d07df8632eaa1f307f659e3aae4584af11914e9297fea0e9bcce", "predecessor_result", "latest_gap_manifest"),
    ("E04", "0c8d1d10260a028360357b8c309f22676fc81645", _ASSIGNMENT, "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9", "candidate_only", "sample_candidate_assignments"),
    ("E05", "dc1222503dcec83220a28df2abdae898a0855864", _RULE_REGISTRY, "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309", "candidate_only", "unapproved_candidate_rule_registry"),
    ("E06", "68c5ca5cf1ce5b20be5db9ce0b37e10830c09288", f"{_OBS_ROOT}/covapie_current11_observed_to_parent_atom_mapping_authority.csv", "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e", "structural_authority", "observed_parent_mapping"),
    ("E07", "68c5ca5cf1ce5b20be5db9ce0b37e10830c09288", f"{_OBS_ROOT}/covapie_current11_parent_and_observed_projected_bond_authority.csv", "bd31b7c074c3d4226c26bfe0210b9c3460f38c5087f1157b1167749f91bfffe0", "structural_authority", "pre_reaction_bonds_and_orders"),
    ("E08", "68c5ca5cf1ce5b20be5db9ce0b37e10830c09288", f"{_OBS_ROOT}/covapie_current11_observed_projection_readiness_matrix.csv", "ec7bb2c203a7b13f525c413171b734fdd9f8af934b6e7e8eaf3fc6ae141128a0", "structural_authority", "graph_readiness_and_sha"),
    ("E09", "0fda7b9e8fc56941e005f3e8b5e67fa2ceaa4ca1", "src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py", "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b", "contract", "role_seed_predecessor_rule_contract"),
    ("E10", "0fda7b9e8fc56941e005f3e8b5e67fa2ceaa4ca1", f"{_PREDECESSOR_ROOT}/covapie_ligand_role_and_minimal_seed_annotation_contract_design_manifest.json", "cf79865f91ef140b6c69010ce2e56c2ff24937a5aa7fa3eac0f8c53bc907764a", "contract", "predecessor_warhead_rule_fields"),
    ("E11", "51810f19e0bbb96171a7dd3aebd72ef08eda0200", "src/covalent_ext/covapie_current11_unified_effective_authority_view_v1.py", "c8f2af8fc0d5dd2f8c42e527cc3db34620b2992f567d59f32a19842254dac4f4", "contract", "unified_effective_authority_builder"),
    ("E12", "b917bf16ae4e08f35c20074300142e3c7cedbabf", "src/covalent_ext/covapie_current11_real_human_review_submission_bundle_compiler_v1.py", "d9d76dd1538e4e929d988f3ad39f11bf390b2ffbb9158ed93238604f4457791d", "review_contract", "legacy_worklist_frozen_and_human_fields"),
    ("E13", "7bf2d25bfcef55b8de2a064d6b20d9206b1e5298", "src/covalent_ext/covapie_current11_real_human_review_ingestion_execution_bundle_v1.py", "78d0124c7fba182f75542a128ee7a2707580e7f05dcbdc24103eae5bebbb969c", "review_contract", "legacy_ingestion_semantics"),
    ("E14", "433e4c3e95a13a02e8cfefbecd28d79d62df37c1", "src/covalent_ext/covapie_current11_multi_boundary_human_review_submission_bundle_compiler_v1.py", "951b872f46e9e404f9f403776dad8096ef38d9412e813f2a06bfa6ad2aeb844a", "review_contract", "multi_boundary_frozen_and_human_fields"),
    ("E15", "ab7eff978e97823d3205f919584893dc87c544f2", "src/covalent_ext/covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1.py", "ca6baf51becd354f7d78763b34c122e66a13b1f51fc7ba16cd896832a573e422", "review_contract", "multi_boundary_ingestion_semantics"),
    ("E16", "ddf3852519cac5eb0d0e50ef919c15ca36fc127a", "src/covalent_ext/covapie_current11_multi_boundary_authority_bundle_v1.py", "1c270d4a0402445220f5735ca875c065e6d5051c0317fa3ef96d74e2741d8d90", "authority_builder", "multi_boundary_authority_bundle"),
    ("E17", "51810f19e0bbb96171a7dd3aebd72ef08eda0200", "docs/covapie_current11_unified_effective_authority_view_v1_guide.md", "7ec4104f6501c09ec93fdf4a3d4c67350b37169c23829f3b5aeee661cd02acad", "contract", "unified_scope_and_precedence"),
    ("E18", "0fda7b9e8fc56941e005f3e8b5e67fa2ceaa4ca1", "docs/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1_summary.md", "a3cf85a476a97e564e192963d23476f14c79af428046677a5c9a5b8a9ca1453c", "contract", "mapped_smarts_requirement"),
)
_GIT_BY_ID = {row[0]: row for row in _GIT_EVIDENCE}

# id, state-relative path, exact filesystem SHA256, lineage note
_STATE_EVIDENCE = (
    ("S01", "manual-review/covapie_current11_unified_effective_authority_view_v1.json", "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774", "unified_effective_authority"),
    ("S02", "manual-review/covapie_current11_real_human_review_submission_bundle_v1.json", "b40c7fad5eedfd5208dd3bc8919cf0aedfe4c22887c27e49475c29a9fcd2b0f3", "legacy_submission"),
    ("S03", "manual-review/covapie_current11_real_human_review_ingestion_execution_bundle_v1.json", "e7099dd28ba51c6935aa4b534815abd1a9f6f46f60be3553d1bb54f1dd4d8dfb", "legacy_ingestion"),
    ("S04", "manual-review/covapie_current11_multi_boundary_human_review_submission_bundle_v1.json", "1e59537e6802d5500f4adce418a481a5b730968f4ecdfa73b8c90c7946e2ee24", "multi_boundary_submission"),
    ("S05", "manual-review/covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1.json", "d837ee22f9fa39fcc9f70ebd1a639e4abd899af4b2c4fd5995c436ceefe7b018", "multi_boundary_ingestion"),
    ("S06", "manual-review/covapie_current11_multi_boundary_authority_bundle_v1.json", "631f134390abd29311a5a8a5ff20b42e4ddd73fd0c37b5f2b9b5f899d055ea41", "multi_boundary_authority"),
    ("S07", "manual-review/current11-warhead-boundary-v1/README.md", "a987c68f3ddd3fffdf7e4f21fd45cc666e065e33a1a588e4698ef508c95a941c", "legacy_review_guide"),
    ("S08", "manual-review/current11-warhead-boundary-v1/review_worklist.csv", "b1c26b28182fa40fcaf8bb2b8f0ffb7ed43455c0ea11833ac2657be9b9282c1c", "legacy_completed_worklist"),
    ("S09", "manual-review/current11-multi-boundary-review-v1-r2-human-completed/README.md", "a69ca7603f2931a22955729ca482793f1c2583f6e641465a77bfe5aa583ae30d", "multi_boundary_review_guide"),
    ("S10", "manual-review/current11-multi-boundary-review-v1-r2-human-completed/multi_boundary_review_worklist.csv", "4e5faea03242714060ef681566741f8dfc1e14268b7cf6b7a75b8cbf92144e88", "multi_boundary_completed_worklist"),
)
_STATE_DIRECT_PRODUCER_COMMITS = {
    "S01": "51810f19e0bbb96171a7dd3aebd72ef08eda0200",
    "S02": "b917bf16ae4e08f35c20074300142e3c7cedbabf",
    "S03": "7bf2d25bfcef55b8de2a064d6b20d9206b1e5298",
    "S04": "433e4c3e95a13a02e8cfefbecd28d79d62df37c1",
    "S05": "ab7eff978e97823d3205f919584893dc87c544f2",
    "S06": "ddf3852519cac5eb0d0e50ef919c15ca36fc127a",
}
_TRANSITIVE_STATE_BINDER_COMMIT = "1cdbca345483022ece967b24de37013b77349cd4"
_SOURCE_COMMIT_SEMANTICS = (
    "state source_commit is the final transitive binder; direct producer "
    "lineage remains explicit in lineage_note"
)

_SOURCE_COLUMNS = (
    "evidence_id", "source_namespace", "source_commit", "source_path",
    "source_sha256", "authority_class", "provides_dimensions", "lineage_note",
    "verified",
)
_MATRIX_COLUMNS = (
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
_REGISTRY_COLUMNS = (
    "reaction_family_id", "reaction_family_version",
    "reaction_family_semantic_name", "reaction_family_structural_basis",
    "reaction_family_authority_status", "warhead_rule_id",
    "warhead_rule_version", "warhead_rule_semantic_name",
    "target_residue_types", "target_residue_reactive_atom",
    "ligand_reactive_atom_contract", "warhead_atom_set_contract",
    "attachment_boundary_contract", "expected_pre_reaction_bond_orders",
    "leaving_group_contract", "formed_bond_order",
    "allowed_formal_charge_pattern", "allowed_match_count", "priority",
    "structural_representation_type", "structural_representation",
    "approval_scope", "approval_status", "authority_source", "sample_count",
    "blocking_fields", "verified",
)
_FAILURE_COLUMNS = (
    "case_id", "failure_case", "mutation_signature", "validator_target",
    "test_node_id", "expected_error", "fails_closed", "verified",
)
_BLOCKERS = (
    "reaction_family_version_missing;"
    "reaction_family_structural_basis_not_formally_approved;"
    "reaction_family_identity_attestation_missing;"
    "warhead_rule_version_missing;"
    "warhead_rule_identity_attestation_missing;"
    "warhead_rule_full_semantics_attestation_missing;"
    "approved_structural_representation_missing;"
    "warhead_rule_required_fields_incomplete;"
    "warhead_rule_approval_missing"
)
_REGISTRY_BLOCKERS = (
    "reaction_family_version;reaction_family_structural_basis;"
    "reaction_family_identity_attestation;warhead_rule_version;"
    "ligand_reactive_atom_contract;warhead_atom_set_contract;"
    "attachment_boundary_contract;expected_pre_reaction_bond_orders;"
    "leaving_group_contract;allowed_formal_charge_pattern;allowed_match_count;"
    "priority_tie_policy;approved_structural_representation;"
    "warhead_rule_identity_attestation;full_rule_semantics_attestation;"
    "approval_authority"
)
_REQUIRED_WARHEAD_RULE_FIELDS = (
    "reaction_family_id", "reaction_family_version", "target_residue_types",
    "target_residue_reactive_atom_name", "warhead_smarts",
    "ligand_reactive_atom_map_number", "warhead_atom_map_numbers",
    "warhead_attachment_atom_map_number", "expected_pre_reaction_bond_orders",
    "allowed_formal_charge_pattern", "allowed_match_count", "priority",
)

_FAILURE_SPECS = (
    ("X01", "current11_row_count_not_11", "matrix_row_deleted", "binding_state"),
    ("X02", "duplicate_sample", "sample_identity_duplicated", "binding_state"),
    ("X03", "family_candidate_missing", "candidate_family_id_empty", "binding_state"),
    ("X04", "rule_candidate_missing", "candidate_rule_id_empty", "binding_state"),
    ("X05", "multiple_family_candidates", "family_candidate_count=2", "binding_state"),
    ("X06", "multiple_rule_candidates", "rule_candidate_count=2", "binding_state"),
    ("X07", "family_effective_boundary_mismatch", "effective_family_id_mismatch", "binding_state"),
    ("X08", "rule_effective_boundary_mismatch", "effective_rule_id_mismatch", "binding_state"),
    ("X09", "family_rule_mapping_mismatch", "registry_family_id_mismatch", "binding_state"),
    ("X10", "rule_reactive_ligand_atom_mismatch", "reactive_atom_match=false", "binding_state"),
    ("X11", "rule_target_cys_sg_mismatch", "target_atom=NZ", "binding_state"),
    ("X12", "graph_sha_mismatch", "graph_sha_match=false", "binding_state"),
    ("X13", "reaction_delta_mismatch", "reaction_delta_match=false", "binding_state"),
    ("X14", "leaving_group_disposition_mismatch", "leaving_group_match=false", "binding_state"),
    ("X15", "warhead_atom_set_mismatch", "warhead_atom_set_match=false", "binding_state"),
    ("X16", "attachment_boundary_mismatch", "attachment_boundary_match=false", "binding_state"),
    ("X17", "boundary_review_impersonates_family_approval", "family_attested=true_without_schema", "binding_state"),
    ("X18", "selected_candidate_impersonates_full_rule_approval", "full_rule_attested=true_without_schema", "binding_state"),
    ("X19", "family_attestation_schema_invented", "schema_family_attestation_field=true", "binding_state"),
    ("X20", "rule_attestation_schema_invented", "schema_rule_attestation_field=true", "binding_state"),
    ("X21", "approved_false_renamed_approved", "registry_approved=true", "binding_state"),
    ("X22", "human_review_false_ignored", "registry_human_review_completed=true", "binding_state"),
    ("X23", "approved_smarts_missing_but_complete", "smarts_complete_claim=true", "binding_state"),
    ("X24", "graph_signature_impersonates_approved_smarts", "graph_equivalence_contract=true", "binding_state"),
    ("X25", "rule_version_missing_ignored", "rule_version_complete_claim=true", "binding_state"),
    ("X26", "family_version_missing_ignored", "family_version_complete_claim=true", "binding_state"),
    ("X27", "expected_bond_orders_missing_ignored", "bond_orders_complete_claim=true", "binding_state"),
    ("X28", "formal_charge_policy_missing_ignored", "charge_complete_claim=true", "binding_state"),
    ("X29", "allowed_match_count_missing_ignored", "match_count_complete_claim=true", "binding_state"),
    ("X30", "priority_tie_policy_missing_ignored", "priority_complete_claim=true", "binding_state"),
    ("X31", "conflicted_repeated_rule_definition", "repeated_rule_consistent=false", "binding_state"),
    ("X32", "role_seed_readiness_opened_early", "role_proposal_readiness=true", "response"),
    ("X33", "materialization_or_training_opened_early", "ready_for_training=true", "response"),
    ("X34", "recommended_next_mismatches_blocker", "recommended_next=wrong", "response"),
    ("X35", "response_tampering_with_recomputed_digest", "bound_count=1_rehashed", "response"),
    ("X36", "lifecycle_not_commit_survivable", "formal_parent_mismatch", "lifecycle"),
    ("X37", "index_hides_actual_worktree_drift", "actual_blob_differs_from_index", "lifecycle"),
    ("X38", "valid_looking_external_witness_substitution", "origin_sha_substituted", "response"),
    ("X39", "legacy_submission_ingestion_transport_mismatch", "legacy_submission_filesystem_sha_substituted", "review_lineage"),
    ("X40", "multi_submission_ingestion_transport_mismatch", "multi_submission_filesystem_sha_substituted", "review_lineage"),
    ("X41", "multi_ingestion_authority_transport_mismatch", "multi_ingestion_filesystem_sha_substituted", "review_lineage"),
)

_SAFETY_FIELDS = (
    "role_proposal_generated", "minimal_seed_proposal_generated",
    "role_annotation_materialized", "minimal_seed_materialized",
    "tensor_materialized", "review_package_generated", "ready_for_training",
    "raw_structure_read", "network_accessed", "rdkit_imported",
    "smarts_matching_executed", "topology_restoration_executed",
    "murcko_executed", "brics_executed", "checkpoint_accessed",
    "forward_executed", "backward_executed", "training_executed",
    "reward_or_rl_executed", "commit_created", "push_performed",
)
_LIFECYCLE_PROFILES = (
    "binding_precommit_candidate", "binding_committed_unpushed",
    "binding_published_successor",
)
_RESPONSE_LIFECYCLE_FIELDS = (
    "origin_main", "ahead", "behind", "binding_lifecycle_profile",
    "binding_commit", "binding_committed", "binding_published",
    "ready_for_binding_commit_review",
)
_DERIVED_LIFECYCLE_FIELDS = _RESPONSE_LIFECYCLE_FIELDS[3:]
_MISSING_AUTHORITY_FIELDS = (
    "reaction_family_version", "reaction_family_structural_basis",
    "reaction_family_identity_attestation", "warhead_rule_version",
    "warhead_rule_identity_attestation", "ligand_reactive_atom_contract",
    "warhead_atom_set_contract", "attachment_boundary_contract",
    "expected_pre_reaction_bond_orders", "leaving_group_contract",
    "allowed_formal_charge_pattern", "allowed_match_count",
    "priority_tie_policy", "approved_structural_representation",
    "warhead_rule_full_semantics_attestation", "approval_authority",
)
_RESPONSE_FIELDS = (
    "binding_version", "error_contract", "repository", "branch", "base_head",
    "base_head_subject", *_RESPONSE_LIFECYCLE_FIELDS, "candidate_paths",
    "source_records", "authority_status_vocabulary",
    "current11_family_rule_authority_binding_matrix",
    "family_and_warhead_rule_authority_registry", "current11_sample_count",
    "unique_reaction_family_count", "unique_warhead_rule_count",
    "boundary_review_completed_count",
    "selected_candidate_identity_attested_count",
    "reaction_family_identity_explicitly_attested_count",
    "warhead_rule_identity_explicitly_attested_count",
    "warhead_rule_full_semantics_explicitly_attested_count",
    "approved_structural_pattern_attested_count",
    "reaction_family_authority_bound_count",
    "approved_warhead_rule_authority_bound_count",
    "binding_conclusion", "missing_authority_fields",
    "ready_for_current11_role_annotation_proposal_generation",
    "ready_for_current11_minimal_seed_proposal_generation", *_SAFETY_FIELDS,
    "failure_matrix_case_count", "failure_matrix_cases",
    "generated_evidence_files", "recommended_next_increment",
    "response_field_count", "response_unsigned_canonical_json_byte_count",
    "response_unsigned_canonical_json_sha256",
)
_RESPONSE_INT_FIELDS = (
    "ahead", "behind", "current11_sample_count",
    "unique_reaction_family_count", "unique_warhead_rule_count",
    "boundary_review_completed_count",
    "selected_candidate_identity_attested_count",
    "reaction_family_identity_explicitly_attested_count",
    "warhead_rule_identity_explicitly_attested_count",
    "warhead_rule_full_semantics_explicitly_attested_count",
    "approved_structural_pattern_attested_count",
    "reaction_family_authority_bound_count",
    "approved_warhead_rule_authority_bound_count",
    "failure_matrix_case_count", "response_field_count",
    "response_unsigned_canonical_json_byte_count",
)
_RESPONSE_BOOL_FIELDS = (
    "binding_committed", "binding_published",
    "ready_for_binding_commit_review",
    "ready_for_current11_role_annotation_proposal_generation",
    "ready_for_current11_minimal_seed_proposal_generation",
    *_SAFETY_FIELDS,
)
_RESPONSE_STRING_FIELDS = (
    "binding_version", "error_contract", "repository", "branch",
    "base_head", "base_head_subject", "origin_main",
    "binding_lifecycle_profile", "binding_conclusion",
    "recommended_next_increment", "response_unsigned_canonical_json_sha256",
)
_RESPONSE_TUPLE_FIELDS = (
    "candidate_paths", "source_records", "authority_status_vocabulary",
    "current11_family_rule_authority_binding_matrix",
    "family_and_warhead_rule_authority_registry", "missing_authority_fields",
    "failure_matrix_cases", "generated_evidence_files",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, ensure_ascii=True, allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except Exception as error:
        raise ValueError(_ERROR) from error


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        rows = list(reader)
    except Exception as error:
        raise ValueError(_ERROR) from error
    if not text.endswith("\n") or not reader.fieldnames or any(None in row for row in rows):
        raise ValueError(_ERROR)
    return rows


def _strict_csv(payload: bytes, columns: Sequence[str]) -> list[dict[str, str]]:
    rows = _csv_rows(payload)
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != tuple(columns):
        raise ValueError(_ERROR)
    return rows


def _strict_json(payload: bytes) -> dict[str, Any]:
    if (not payload or payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload
            or len(payload) >= 4 * 1024 * 1024):
        raise ValueError(_ERROR)
    try:
        value = json.loads(payload.decode("utf-8"))
    except Exception as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict:
        raise ValueError(_ERROR)
    return value


def _run_git(
    repo_root: Path, arguments: Sequence[str], *, allow_one: bool = False,
) -> tuple[int, bytes, bytes]:
    try:
        result = subprocess.run(
            ["git", *arguments], cwd=repo_root,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
            check=False, capture_output=True, timeout=30,
        )
    except Exception as error:
        raise ValueError(_ERROR) from error
    if result.returncode not in ((0, 1) if allow_one else (0,)):
        raise ValueError(_ERROR)
    return result.returncode, result.stdout, result.stderr


def _git(repo_root: Path, arguments: Sequence[str]) -> bytes:
    rc, out, err = _run_git(repo_root, arguments)
    if rc or err:
        raise ValueError(_ERROR)
    return out


def _git_text(repo_root: Path, arguments: Sequence[str]) -> str:
    try:
        return _git(repo_root, arguments).decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(_ERROR) from error


def _git_blob(repo_root: Path, evidence_id: str) -> bytes:
    try:
        _id, commit, path, digest, _authority, _note = _GIT_BY_ID[evidence_id]
    except Exception as error:
        raise ValueError(_ERROR) from error
    payload = _git(repo_root, ["show", f"{commit}:{path}"])
    if not payload or _sha256(payload) != digest:
        raise ValueError(_ERROR)
    return payload


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    rc, out, err = _run_git(
        repo_root, ["merge-base", "--is-ancestor", ancestor, descendant],
        allow_one=True,
    )
    if out or err:
        raise ValueError(_ERROR)
    return rc == 0


def _state_root(repo_root: Path) -> Path:
    common = _git_text(
        repo_root, ["rev-parse", "--path-format=absolute", "--git-common-dir"],
    ).strip()
    candidate = Path(common).parent.parent / "covapie-state"
    if not candidate.is_dir():
        candidate = repo_root.parent / "covapie-state"
    if not candidate.is_dir():
        raise ValueError(_ERROR)
    return candidate


def _read_state_evidence(repo_root: Path) -> dict[str, bytes]:
    root = _state_root(repo_root)
    result: dict[str, bytes] = {}
    for evidence_id, relative, digest, _note in _STATE_EVIDENCE:
        path = root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ValueError(_ERROR) from error
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_size != len(payload)
                or _sha256(payload) != digest):
            raise ValueError(_ERROR)
        result[evidence_id] = payload
    return result


def _source_records() -> tuple[dict[str, str], ...]:
    dimensions = {
        "E01": "candidate_status_baseline", "E02": "authority_semantics",
        "E03": "predecessor_readiness", "E04": "sample_candidate_identity",
        "E05": "candidate_rule_semantics", "E06": "reactive_atom_and_graph",
        "E07": "bond_order_and_reaction_delta", "E08": "graph_sha",
        "E09": "complete_rule_contract", "E10": "complete_rule_fields",
        "E11": "effective_boundary_precedence", "E12": "legacy_review_scope",
        "E13": "legacy_ingestion_scope", "E14": "multi_review_scope",
        "E15": "multi_ingestion_scope", "E16": "multi_authority_scope",
        "E17": "unified_scope", "E18": "approved_smarts_requirement",
    }
    records: list[dict[str, str]] = []
    for evidence_id, commit, path, digest, authority, note in _GIT_EVIDENCE:
        records.append({
            "evidence_id": evidence_id, "source_namespace": "git_object",
            "source_commit": commit, "source_path": path,
            "source_sha256": digest, "authority_class": authority,
            "provides_dimensions": dimensions[evidence_id],
            "lineage_note": note, "verified": "true",
        })
    for evidence_id, path, digest, note in _STATE_EVIDENCE:
        workspace_witness = evidence_id in {"S07", "S08", "S09", "S10"}
        formal_state = evidence_id in _STATE_DIRECT_PRODUCER_COMMITS
        records.append({
            "evidence_id": evidence_id,
            "source_namespace": (
                "filesystem_review_scope_witness" if workspace_witness
                else "sha_bound_formal_state"
            ),
            "source_commit": (
                "b917bf16ae4e08f35c20074300142e3c7cedbabf"
                if evidence_id in {"S07", "S08"}
                else "433e4c3e95a13a02e8cfefbecd28d79d62df37c1"
                if evidence_id in {"S09", "S10"}
                else _TRANSITIVE_STATE_BINDER_COMMIT
            ),
            "source_path": f"state://{path}", "source_sha256": digest,
            "authority_class": (
                "review_scope_witness" if workspace_witness
                else "formal_state"
            ),
            "provides_dimensions": (
                "review_schema_and_attestation_scope" if workspace_witness
                else "effective_boundary_authority_and_lineage"
            ),
            "lineage_note": (
                f"{note};transitively bound through unified effective authority "
                f"view;direct_producer_commit={_STATE_DIRECT_PRODUCER_COMMITS[evidence_id]}"
                if formal_state else note
            ),
            "verified": "true",
        })
    return tuple(records)


def _validate_embedded_record_digest_v1(
    record: Mapping[str, Any], digest_field: str,
) -> None:
    digest = record.get(digest_field)
    if (type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or digest != _sha256(_canonical_json_bytes({
                field: value for field, value in record.items()
                if field != digest_field
            }))):
        raise ValueError(_ERROR)


def _validate_review_transport_lineage_v1(
    state: Mapping[str, bytes],
) -> None:
    """Validate direct filesystem and internal-digest lineage through S01--S06."""

    try:
        if (type(state) is not dict
                or tuple(state) != tuple(row[0] for row in _STATE_EVIDENCE)
                or any(type(state[evidence_id]) is not bytes
                       for evidence_id, *_rest in _STATE_EVIDENCE)):
            raise ValueError(_ERROR)
        records = {evidence_id: _strict_json(state[evidence_id])
                   for evidence_id in ("S01", "S02", "S03", "S04", "S05", "S06")}
        unified = records["S01"]
        legacy_submission = records["S02"]
        legacy_ingestion = records["S03"]
        multi_submission = records["S04"]
        multi_ingestion = records["S05"]
        multi_authority = records["S06"]

        filesystem_sha = {
            evidence_id: _sha256(state[evidence_id])
            for evidence_id in ("S02", "S03", "S04", "S05", "S06")
        }
        if (legacy_ingestion.get("source_submission_bundle_sha256")
                != filesystem_sha["S02"]
                or legacy_ingestion.get("source_canonical_bundle_sha256")
                != _sha256(_canonical_json_bytes(legacy_submission))):
            raise ValueError(_ERROR)
        _validate_embedded_record_digest_v1(
            legacy_ingestion, "ingestion_execution_bundle_sha256",
        )

        if (multi_submission.get("source_submission_bundle_sha256")
                != filesystem_sha["S02"]
                or multi_submission.get(
                    "source_ingestion_execution_bundle_filesystem_sha256"
                ) != filesystem_sha["S03"]
                or multi_submission.get("source_ingestion_execution_bundle_sha256")
                != legacy_ingestion["ingestion_execution_bundle_sha256"]):
            raise ValueError(_ERROR)
        _validate_embedded_record_digest_v1(
            multi_submission, "multi_boundary_submission_bundle_sha256",
        )

        if (multi_ingestion.get("source_v1_submission_bundle_sha256")
                != filesystem_sha["S02"]
                or multi_ingestion.get(
                    "source_v1_ingestion_execution_bundle_filesystem_sha256"
                ) != filesystem_sha["S03"]
                or multi_ingestion.get("source_v1_ingestion_execution_bundle_sha256")
                != legacy_ingestion["ingestion_execution_bundle_sha256"]
                or multi_ingestion.get(
                    "source_multi_boundary_submission_bundle_filesystem_sha256"
                ) != filesystem_sha["S04"]
                or multi_ingestion.get("source_multi_boundary_submission_bundle_sha256")
                != multi_submission["multi_boundary_submission_bundle_sha256"]):
            raise ValueError(_ERROR)
        _validate_embedded_record_digest_v1(
            multi_ingestion,
            "multi_boundary_ingestion_execution_bundle_sha256",
        )

        if (multi_authority.get(
                "source_v1_ingestion_execution_bundle_filesystem_sha256"
                ) != filesystem_sha["S03"]
                or multi_authority.get("source_v1_ingestion_execution_bundle_sha256")
                != legacy_ingestion["ingestion_execution_bundle_sha256"]
                or multi_authority.get(
                    "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256"
                ) != filesystem_sha["S05"]
                or multi_authority.get(
                    "source_multi_boundary_ingestion_execution_bundle_sha256"
                ) != multi_ingestion[
                    "multi_boundary_ingestion_execution_bundle_sha256"
                ]):
            raise ValueError(_ERROR)
        _validate_embedded_record_digest_v1(
            multi_authority, "multi_boundary_authority_bundle_sha256",
        )

        if (unified.get("source_v1_submission_bundle_filesystem_sha256")
                != filesystem_sha["S02"]
                or unified.get(
                    "source_v1_ingestion_execution_bundle_filesystem_sha256"
                ) != filesystem_sha["S03"]
                or unified.get("source_v1_ingestion_execution_bundle_sha256")
                != legacy_ingestion["ingestion_execution_bundle_sha256"]
                or unified.get(
                    "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256"
                ) != filesystem_sha["S05"]
                or unified.get("source_multi_boundary_ingestion_execution_bundle_sha256")
                != multi_ingestion[
                    "multi_boundary_ingestion_execution_bundle_sha256"
                ]
                or unified.get(
                    "source_multi_boundary_authority_bundle_filesystem_sha256"
                ) != filesystem_sha["S06"]
                or unified.get("source_multi_boundary_authority_bundle_sha256")
                != multi_authority["multi_boundary_authority_bundle_sha256"]):
            raise ValueError(_ERROR)
        _validate_embedded_record_digest_v1(
            unified, "unified_effective_authority_view_sha256",
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_review_scope(
    state: Mapping[str, bytes],
) -> dict[str, dict[str, Any]]:
    _validate_review_transport_lineage_v1(state)
    unified = _strict_json(state["S01"])
    legacy_submission = _strict_json(state["S02"])
    legacy_ingestion = _strict_json(state["S03"])
    multi_submission = _strict_json(state["S04"])
    multi_ingestion = _strict_json(state["S05"])
    multi_authority = _strict_json(state["S06"])
    if (unified.get("effective_authority_record_count") != 11
            or unified.get("effective_legacy_exact_one_count") != 6
            or unified.get("effective_multi_boundary_exact_two_count") != 5
            or tuple(unified.get("sample_order", ())) != _EXPECTED_SAMPLES
            or legacy_ingestion.get("batch_passed") is not True
            or multi_ingestion.get("batch_passed") is not True
            or multi_authority.get("active_authority_count") != 5
            or unified.get("source_v1_submission_bundle_filesystem_sha256")
            != _sha256(state["S02"])
            or unified.get("source_v1_ingestion_execution_bundle_filesystem_sha256")
            != _sha256(state["S03"])
            or unified.get("source_multi_boundary_ingestion_execution_bundle_filesystem_sha256")
            != _sha256(state["S05"])
            or unified.get("source_multi_boundary_authority_bundle_filesystem_sha256")
            != _sha256(state["S06"])
            or len(legacy_submission.get("submission_items", ())) != 11
            or len(multi_submission.get("submission_items", ())) != 5):
        raise ValueError(_ERROR)
    forbidden_attestations = {
        "reaction_family_identity_explicitly_attested",
        "warhead_rule_identity_explicitly_attested",
        "warhead_rule_full_semantics_explicitly_attested",
        "approved_structural_pattern_attested",
    }
    for item in legacy_submission["submission_items"]:
        payload = item.get("review_record_payload")
        if (type(payload) is not dict
                or payload.get("review_unit_type")
                != "sample_warhead_atom_set_and_attachment_boundary"
                or forbidden_attestations.intersection(payload)
                or item.get("reviewer_provenance_attested") is not True):
            raise ValueError(_ERROR)
    for item in multi_submission["submission_items"]:
        if (type(item) is not dict or forbidden_attestations.intersection(item)
                or item.get("reviewer_provenance_attested") is not True
                or item.get("review_completed") is not True):
            raise ValueError(_ERROR)
    compiler_legacy = _git_blob_cached("E12")
    compiler_multi = _git_blob_cached("E14")
    if (b"_WORKLIST_IDENTITY_FIELDS" not in compiler_legacy
            or b"_WORKLIST_HUMAN_FIELDS" not in compiler_legacy
            or b"_FROZEN_WORKLIST_FIELDS" not in compiler_multi
            or any(token.encode("ascii") in compiler_legacy + compiler_multi
                   for token in forbidden_attestations)):
        raise ValueError(_ERROR)
    records = unified.get("effective_authority_records")
    if type(records) is not list or len(records) != 11:
        raise ValueError(_ERROR)
    result: dict[str, dict[str, Any]] = {}
    for wrapper, sample in zip(records, _EXPECTED_SAMPLES):
        authority = wrapper.get("effective_authority_record", {})
        cardinality = wrapper.get("effective_boundary_cardinality")
        boundaries = (
            [authority.get("reviewed_boundary_bond_id")]
            if cardinality == 1 else authority.get("reviewed_boundary_records")
        )
        if (wrapper.get("sample_index_row_id") != sample
                or wrapper.get("effective_authority_namespace") not in {
                    "legacy_exact_one_boundary_v1",
                    "exact_two_boundaries_multi_boundary_v1",
                }
                or cardinality not in (1, 2)
                or authority.get("authority_status") != "active"
                or authority.get("sample_quarantined") is not False
                or authority.get("complete_warhead_atom_set_authority_available") is not True
                or not authority.get("review_decision")
                or not authority.get("reviewed_warhead_atom_ids")
                or type(boundaries) is not list or len(boundaries) != cardinality
                or not authority.get("reaction_family_id")
                or not authority.get("warhead_rule_id")):
            raise ValueError(_ERROR)
        result[sample] = {
            "family_id": authority["reaction_family_id"],
            "rule_id": authority["warhead_rule_id"],
            "namespace": wrapper["effective_authority_namespace"],
            "cardinality": cardinality,
            "decision": authority["review_decision"],
            "active": True,
        }
    return result


_BLOB_CACHE: dict[str, bytes] = {}


def _git_blob_cached(evidence_id: str) -> bytes:
    try:
        return _BLOB_CACHE[evidence_id]
    except KeyError as error:
        raise ValueError(_ERROR) from error


def _derive_binding(
    repo_root: Path, state: Mapping[str, bytes],
) -> tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...], tuple[dict[str, object], ...]]:
    assignments = _csv_rows(_git_blob(repo_root, "E04"))
    rule_rows = _csv_rows(_git_blob(repo_root, "E05"))
    mapping_rows = _csv_rows(_git_blob(repo_root, "E06"))
    bond_rows = _csv_rows(_git_blob(repo_root, "E07"))
    ready_rows = _csv_rows(_git_blob(repo_root, "E08"))
    gap_rows = _csv_rows(_git_blob(repo_root, "E01"))
    gap_manifest = _strict_json(_git_blob(repo_root, "E03"))
    predecessor = _strict_json(_git_blob(repo_root, "E10"))
    _BLOB_CACHE["E12"] = _git_blob(repo_root, "E12")
    _BLOB_CACHE["E14"] = _git_blob(repo_root, "E14")
    effective = _validate_review_scope(state)
    if (tuple(row.get("sample_index_row_id") for row in assignments) != _EXPECTED_SAMPLES
            or tuple(row.get("sample_index_row_id") for row in gap_rows) != _EXPECTED_SAMPLES
            or gap_manifest.get("current11_role_proposal_input_ready_count") != 0
            or gap_manifest.get("current11_minimal_seed_input_ready_count") != 0
            or gap_manifest.get("authority_coverage", {}).get("reaction_family_label")
            != "0/11 authoritative_resolved;11/11 candidate_only"
            or gap_manifest.get("authority_coverage", {}).get("approved_warhead_rule")
            != "0/11 authoritative_resolved;11/11 candidate_only"
            or tuple(predecessor.get("warhead_rule_fields", ()))
            != _REQUIRED_WARHEAD_RULE_FIELDS):
        raise ValueError(_ERROR)
    assignment_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in assignments:
        assignment_groups[row["sample_index_row_id"]].append(row)
    rules_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rule_rows:
        rules_by_id[row["warhead_rule_id"]].append(row)
    mappings: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in mapping_rows:
        mappings[row["sample_index_row_id"]].append(row)
    bonds: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in bond_rows:
        bonds[row["sample_index_row_id"]].append(row)
    ready = {row["sample_index_row_id"]: row for row in ready_rows}
    matrix: list[dict[str, str]] = []
    facts: list[dict[str, object]] = []
    for expected in _EXPECTED_IDENTITIES:
        sample, pdb_id, ligand, family_id, rule_id = expected
        group = assignment_groups.get(sample, [])
        if len(group) != 1 or len(rules_by_id.get(rule_id, [])) != 1:
            raise ValueError(_ERROR)
        assignment = group[0]
        rule = rules_by_id[rule_id][0]
        reactive = [row for row in mappings[sample] if row["reactive_ligand_atom"] == "true"]
        graph = ready.get(sample, {})
        relevant_bonds = [row for row in bonds[sample]
                          if row["projected_to_observed_graph"] == "true"]
        try:
            local_contract = json.loads(rule["canonical_local_graph_rule_json"])
        except Exception as error:
            raise ValueError(_ERROR) from error
        reaction_delta = local_contract.get("reaction_delta", {})
        graph_match = (
            assignment.get("observed_graph_sha256") == graph.get("observed_graph_sha256")
            and assignment.get("component_parent_graph_sha256")
            == relevant_bonds[0].get("component_parent_graph_sha256")
            and graph.get("pre_reaction_connectivity_available") == "true"
            and graph.get("pre_reaction_bond_order_available") == "true"
            and int(graph.get("projected_bond_count", "-1")) == len(relevant_bonds)
        ) if relevant_bonds else False
        delta_match = (
            str(reaction_delta.get("leaving_group_count"))
            == rule.get("required_leaving_group_count")
            and "|".join(reaction_delta.get("leaving_group_elements", []))
            == rule.get("allowed_leaving_group_elements")
            and reaction_delta.get("reaction_delta_class")
            == rule.get("required_reaction_delta_class")
        )
        reactive_match = (
            len(reactive) == 1
            and assignment.get("ligand_reactive_atom_name")
            == reactive[0].get("observed_atom_name")
            and assignment.get("target_residue_name") == "CYS"
            and assignment.get("target_residue_atom_name") == "SG"
            and rule.get("target_residue_name") == "CYS"
            and rule.get("target_residue_atom_name") == "SG"
            and local_contract.get("center_atom", {}).get("element")
            == assignment.get("ligand_reactive_atom_element")
        )
        authority = effective.get(sample, {})
        exact = (
            assignment.get("candidate_family_assignment_exact_one") == "true"
            and assignment.get("candidate_rule_assignment_exact_one") == "true"
            and assignment.get("assignment_status")
            == "machine_derived_candidate_assignment_materialized"
        )
        boundary_match = (
            authority.get("family_id") == family_id
            and authority.get("rule_id") == rule_id
        )
        if ((assignment.get("pdb_id"), assignment.get("ligand_comp_id"),
             assignment.get("candidate_reaction_family_id"),
             assignment.get("candidate_warhead_rule_id"))
                != (pdb_id, ligand, family_id, rule_id)
                or rule.get("reaction_family_id") != family_id
                or rule.get("candidate_rule_assignment_ready") != "true"
                or rule.get("exact_match_unique") != "true"
                or rule.get("approved") != "false"
                or rule.get("human_gold_review_completed") != "false"
                or rule.get("approved_warhead_smarts") != ""
                or rule.get("SMARTS_status") != "not_materialized_in_design_stage"
                or not exact or not boundary_match or not graph_match
                or not delta_match or not reactive_match):
            raise ValueError(_ERROR)
        matrix.append({
            "sample_index_row_id": sample, "pdb_id": pdb_id,
            "ligand_identity": ligand,
            "candidate_reaction_family_id": family_id,
            "candidate_warhead_rule_id": rule_id,
            "candidate_assignment_exact_one": "true",
            "candidate_matches_effective_boundary_authority": "true",
            "candidate_matches_pre_reaction_graph": "true",
            "candidate_matches_reaction_delta": "true",
            "candidate_matches_reactive_atoms": "true",
            "boundary_review_completed": "true",
            "selected_candidate_identity_attested": "true",
            "reaction_family_identity_explicitly_attested": "false",
            "warhead_rule_identity_explicitly_attested": "false",
            "warhead_rule_full_semantics_explicitly_attested": "false",
            "approved_structural_pattern_attested": "false",
            "reaction_family_version": "",
            "reaction_family_structural_basis": "",
            "reaction_family_authority_status": "candidate_only",
            "reaction_family_authority_source": "E04|E05|S01",
            "warhead_rule_version": "",
            "warhead_rule_structural_representation_type": "",
            "warhead_rule_structural_representation_id": "",
            "warhead_rule_required_fields_complete": "false",
            "warhead_rule_approval_status": "candidate_only",
            "warhead_rule_authority_source": "E04|E05|E09|E10|S01",
            "binding_conflicts": "", "binding_blockers": _BLOCKERS,
            "verified": "true",
        })
        facts.append({
            "sample_index_row_id": sample, "family_candidate_count": 1,
            "rule_candidate_count": 1, "effective_family_id": family_id,
            "effective_rule_id": rule_id, "registry_family_id": family_id,
            "reactive_atom_match": True, "target_residue_name": "CYS",
            "target_residue_atom": "SG", "graph_sha_match": True,
            "reaction_delta_match": True, "leaving_group_match": True,
            "warhead_atom_set_match": True, "attachment_boundary_match": True,
            "review_schema_family_attestation_field": False,
            "review_schema_rule_attestation_field": False,
            "registry_approved": False,
            "registry_human_review_completed": False,
            "approved_smarts": "", "graph_signature_equivalence_contract": False,
            "smarts_complete_claim": False, "rule_version_complete_claim": False,
            "family_version_complete_claim": False,
            "bond_orders_complete_claim": False, "charge_complete_claim": False,
            "match_count_complete_claim": False, "priority_complete_claim": False,
            "repeated_rule_definition_consistent": True,
        })
    counts = Counter(row["candidate_warhead_rule_id"] for row in matrix)
    registry: list[dict[str, str]] = []
    for rule_id in sorted(rules_by_id):
        group = rules_by_id[rule_id]
        if len(group) != 1 or rule_id not in counts:
            raise ValueError(_ERROR)
        rule = group[0]
        registry.append({
            "reaction_family_id": rule["reaction_family_id"],
            "reaction_family_version": "", "reaction_family_semantic_name": "",
            "reaction_family_structural_basis": "",
            "reaction_family_authority_status": "candidate_only",
            "warhead_rule_id": rule_id, "warhead_rule_version": "",
            "warhead_rule_semantic_name": "", "target_residue_types": "CYS",
            "target_residue_reactive_atom": "SG",
            "ligand_reactive_atom_contract": "", "warhead_atom_set_contract": "",
            "attachment_boundary_contract": "",
            "expected_pre_reaction_bond_orders": "", "leaving_group_contract": "",
            "formed_bond_order": rule["formed_bond_order"],
            "allowed_formal_charge_pattern": "", "allowed_match_count": "",
            "priority": "", "structural_representation_type": "",
            "structural_representation": "",
            "approval_scope": "boundary_only_not_family_or_rule",
            "approval_status": "candidate_only",
            "authority_source": "E04|E05|E09|E10|S01",
            "sample_count": str(counts[rule_id]),
            "blocking_fields": _REGISTRY_BLOCKERS, "verified": "true",
        })
    return tuple(matrix), tuple(registry), tuple(facts)


def _validate_matrix_registry_v1(
    matrix: object, registry: object,
) -> None:
    try:
        if (type(matrix) is not tuple or len(matrix) != 11
                or type(registry) is not tuple or len(registry) != 7):
            raise ValueError(_ERROR)
        for row, expected in zip(matrix, _EXPECTED_IDENTITIES):
            if (type(row) is not dict or tuple(row) != _MATRIX_COLUMNS
                    or any(type(value) is not str for value in row.values())
                    or (row["sample_index_row_id"], row["pdb_id"],
                        row["ligand_identity"], row["candidate_reaction_family_id"],
                        row["candidate_warhead_rule_id"]) != expected
                    or row["reaction_family_authority_status"] != "candidate_only"
                    or row["warhead_rule_approval_status"] != "candidate_only"
                    or row["reaction_family_version"] != ""
                    or row["reaction_family_structural_basis"] != ""
                    or row["warhead_rule_version"] != ""
                    or row["warhead_rule_structural_representation_type"] != ""
                    or row["warhead_rule_structural_representation_id"] != ""
                    or row["warhead_rule_required_fields_complete"] != "false"
                    or any(row[field] != "true" for field in (
                        "candidate_assignment_exact_one",
                        "candidate_matches_effective_boundary_authority",
                        "candidate_matches_pre_reaction_graph",
                        "candidate_matches_reaction_delta",
                        "candidate_matches_reactive_atoms",
                        "boundary_review_completed",
                        "selected_candidate_identity_attested",
                    ))
                    or any(row[field] != "false" for field in (
                        "reaction_family_identity_explicitly_attested",
                        "warhead_rule_identity_explicitly_attested",
                        "warhead_rule_full_semantics_explicitly_attested",
                        "approved_structural_pattern_attested",
                    ))
                    or row["binding_conflicts"] != ""
                    or row["binding_blockers"] != _BLOCKERS
                    or row["verified"] != "true"):
                raise ValueError(_ERROR)
        rules = [row["warhead_rule_id"] for row in registry]
        if rules != sorted(rules) or len(rules) != len(set(rules)):
            raise ValueError(_ERROR)
        counts = Counter(row["candidate_warhead_rule_id"] for row in matrix)
        family_by_rule = {
            row["candidate_warhead_rule_id"]: row["candidate_reaction_family_id"]
            for row in matrix
        }
        for row in registry:
            if (type(row) is not dict or tuple(row) != _REGISTRY_COLUMNS
                    or any(type(value) is not str for value in row.values())
                    or row["reaction_family_id"]
                    != family_by_rule.get(row["warhead_rule_id"])
                    or row["sample_count"] != str(counts[row["warhead_rule_id"]])
                    or row["reaction_family_authority_status"] != "candidate_only"
                    or row["approval_status"] != "candidate_only"
                    or row["reaction_family_version"] != ""
                    or row["warhead_rule_version"] != ""
                    or row["reaction_family_semantic_name"] != ""
                    or row["warhead_rule_semantic_name"] != ""
                    or row["structural_representation"] != ""
                    or row["structural_representation_type"] != ""
                    or row["allowed_match_count"] != ""
                    or row["priority"] != ""
                    or row["blocking_fields"] != _REGISTRY_BLOCKERS
                    or row["verified"] != "true"):
                raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _build_failure_state_v1(
    matrix: tuple[dict[str, str], ...], registry: tuple[dict[str, str], ...],
    facts: tuple[dict[str, object], ...],
) -> dict[str, object]:
    _validate_matrix_registry_v1(matrix, registry)
    return {
        "matrix": copy.deepcopy(matrix), "registry": copy.deepcopy(registry),
        "facts": copy.deepcopy(facts),
    }


def _validate_binding_state_v1(value: object) -> None:
    try:
        if type(value) is not dict or tuple(value) != ("matrix", "registry", "facts"):
            raise ValueError(_ERROR)
        matrix, registry, facts = value["matrix"], value["registry"], value["facts"]
        _validate_matrix_registry_v1(matrix, registry)
        if type(facts) is not tuple or len(facts) != 11:
            raise ValueError(_ERROR)
        registry_families = {row["warhead_rule_id"]: row["reaction_family_id"]
                             for row in registry}
        for row, fact in zip(matrix, facts):
            expected = {
                "sample_index_row_id": row["sample_index_row_id"],
                "family_candidate_count": 1, "rule_candidate_count": 1,
                "effective_family_id": row["candidate_reaction_family_id"],
                "effective_rule_id": row["candidate_warhead_rule_id"],
                "registry_family_id": row["candidate_reaction_family_id"],
                "reactive_atom_match": True, "target_residue_name": "CYS",
                "target_residue_atom": "SG", "graph_sha_match": True,
                "reaction_delta_match": True, "leaving_group_match": True,
                "warhead_atom_set_match": True,
                "attachment_boundary_match": True,
                "review_schema_family_attestation_field": False,
                "review_schema_rule_attestation_field": False,
                "registry_approved": False,
                "registry_human_review_completed": False,
                "approved_smarts": "",
                "graph_signature_equivalence_contract": False,
                "smarts_complete_claim": False,
                "rule_version_complete_claim": False,
                "family_version_complete_claim": False,
                "bond_orders_complete_claim": False,
                "charge_complete_claim": False,
                "match_count_complete_claim": False,
                "priority_complete_claim": False,
                "repeated_rule_definition_consistent": True,
            }
            if fact != expected or registry_families.get(row["candidate_warhead_rule_id"]) != fact["registry_family_id"]:
                raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_candidate_changes(*, tracked: object, staged: object, untracked: object) -> None:
    if (type(tracked) is not tuple or type(staged) is not tuple
            or type(untracked) is not tuple or tracked or staged
            or untracked != _CANDIDATE_PATHS):
        raise ValueError(_ERROR)


def _collect_live_identity(repo_root: Path, path: str) -> dict[str, object]:
    candidate = repo_root / path
    try:
        metadata = candidate.lstat()
    except OSError as error:
        raise ValueError(_ERROR) from error
    blob = _git_text(repo_root, ["hash-object", "--no-filters", "--", path]).strip()
    if re.fullmatch(r"[0-9a-f]{40}", blob) is None:
        raise ValueError(_ERROR)
    line = _git_text(repo_root, ["ls-files", "--stage", "--", path]).strip()
    if line:
        metadata_text, listed = line.split("\t", 1)
        mode, index_blob, stage = metadata_text.split()
        if listed != path or stage != "0":
            raise ValueError(_ERROR)
        return {"tracked": True, "mode": mode, "index_blob": index_blob, "blob": blob}
    return {"tracked": False, "mode": f"100{stat.S_IMODE(metadata.st_mode):03o}", "blob": blob}


def _derive_binding_lifecycle_v1(facts: object) -> dict[str, object]:
    try:
        if type(facts) is not dict:
            raise ValueError(_ERROR)
        commits, live = facts["path_commits"], facts["live_paths"]
        tracked, staged, untracked = facts["tracked"], facts["staged"], facts["untracked"]
        if (facts["base_ancestor_head"] is not True
                or facts["base_ancestor_origin"] is not True
                or type(commits) is not list or len(commits) > 1
                or type(live) is not dict or tuple(live) != _CANDIDATE_PATHS):
            raise ValueError(_ERROR)
        if not commits:
            _validate_candidate_changes(tracked=tracked, staged=staged, untracked=untracked)
            if (facts["head"] != _BASE or facts["origin"] != _BASE
                    or (facts["ahead"], facts["behind"]) != (0, 0)
                    or any(item.get("tracked") is not False
                           or item.get("mode") != "100644" for item in live.values())):
                raise ValueError(_ERROR)
            return {
                "binding_lifecycle_profile": "binding_precommit_candidate",
                "binding_commit": None, "binding_committed": False,
                "binding_published": False,
                "ready_for_binding_commit_review": True,
            }
        commit = commits[0]
        if (re.fullmatch(r"[0-9a-f]{40}", str(commit.get("commit", ""))) is None
                or commit.get("parents") != [_BASE]
                or commit.get("subject") != _FORMAL_COMMIT_SUBJECT
                or tuple(commit.get("changed_paths", ())) != _CANDIDATE_PATHS
                or commit.get("changed_statuses")
                != {path: "A" for path in _CANDIDATE_PATHS}
                or set(commit.get("path_modes", ())) != set(_CANDIDATE_PATHS)
                or set(commit.get("path_blobs", ())) != set(_CANDIDATE_PATHS)
                or any(commit["path_modes"].get(path) != "100644"
                       for path in _CANDIDATE_PATHS)
                or any(re.fullmatch(r"[0-9a-f]{40}", str(commit["path_blobs"].get(path, ""))) is None
                       for path in _CANDIDATE_PATHS)
                or any(live[path] != {
                    "tracked": True, "mode": "100644",
                    "index_blob": commit["path_blobs"][path],
                    "blob": commit["path_blobs"][path],
                } for path in _CANDIDATE_PATHS)
                or commit.get("ancestor_head") is not True
                or any(path in tracked or path in staged or path in untracked
                       for path in _CANDIDATE_PATHS)):
            raise ValueError(_ERROR)
        if commit.get("ancestor_origin") is True:
            return {
                "binding_lifecycle_profile": "binding_published_successor",
                "binding_commit": commit["commit"], "binding_committed": True,
                "binding_published": True,
                "ready_for_binding_commit_review": False,
            }
        if (facts["head"] != commit["commit"] or facts["origin"] != _BASE
                or (facts["ahead"], facts["behind"]) != (1, 0)
                or facts["repository_clean"] is not True):
            raise ValueError(_ERROR)
        return {
            "binding_lifecycle_profile": "binding_committed_unpushed",
            "binding_commit": commit["commit"], "binding_committed": True,
            "binding_published": False,
            "ready_for_binding_commit_review": False,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _collect_lifecycle(
    repo_root: Path, head: str, origin: str, ahead: int, behind: int,
) -> dict[str, object]:
    tracked = tuple(sorted(_git_text(repo_root, ["diff", "--name-only"]).splitlines()))
    staged = tuple(sorted(_git_text(repo_root, ["diff", "--cached", "--name-only"]).splitlines()))
    untracked = tuple(sorted(_git_text(repo_root, ["ls-files", "--others", "--exclude-standard"]).splitlines()))
    revisions = set(_git_text(repo_root, ["rev-list", f"{_BASE}..{head}"]).splitlines())
    revisions.update(_git_text(repo_root, ["rev-list", f"{_BASE}..{origin}"]).splitlines())
    path_commits: list[dict[str, object]] = []
    for commit_hash in sorted(revisions):
        lines = _git_text(repo_root, ["diff-tree", "--root", "--no-commit-id", "--name-status", "-r", commit_hash]).splitlines()
        statuses = {parts[1]: parts[0] for parts in (line.split("\t") for line in lines)
                    if len(parts) == 2}
        if not set(statuses).intersection(_CANDIDATE_PATHS):
            continue
        modes: dict[str, str] = {}
        blobs: dict[str, str] = {}
        for path in _CANDIDATE_PATHS:
            line = _git_text(repo_root, ["ls-tree", commit_hash, "--", path]).strip()
            if line:
                metadata, listed = line.split("\t", 1)
                mode, kind, blob = metadata.split()
                if listed != path or kind != "blob":
                    raise ValueError(_ERROR)
                modes[path], blobs[path] = mode, blob
        path_commits.append({
            "commit": commit_hash,
            "parents": _git_text(repo_root, ["show", "-s", "--format=%P", commit_hash]).split(),
            "subject": _git_text(repo_root, ["show", "-s", "--format=%s", commit_hash]).strip(),
            "changed_paths": tuple(sorted(statuses)),
            "changed_statuses": {path: statuses[path] for path in sorted(statuses)},
            "path_modes": {path: modes[path] for path in sorted(modes)},
            "path_blobs": {path: blobs[path] for path in sorted(blobs)},
            "ancestor_head": _is_ancestor(repo_root, commit_hash, head),
            "ancestor_origin": _is_ancestor(repo_root, commit_hash, origin),
        })
    return {
        "head": head, "origin": origin, "ahead": ahead, "behind": behind,
        "base_ancestor_head": _is_ancestor(repo_root, _BASE, head),
        "base_ancestor_origin": _is_ancestor(repo_root, _BASE, origin),
        "tracked": tracked, "staged": staged, "untracked": untracked,
        "repository_clean": not tracked and not staged and not untracked,
        "path_commits": path_commits,
        "live_paths": {path: _collect_live_identity(repo_root, path)
                       for path in _CANDIDATE_PATHS},
    }


def _response_lifecycle_projection_v1(response: Mapping[str, object]) -> dict[str, object]:
    try:
        projection = {field: response[field] for field in _RESPONSE_LIFECYCLE_FIELDS}
        if (tuple(projection) != _RESPONSE_LIFECYCLE_FIELDS
                or type(projection["origin_main"]) is not str
                or type(projection["ahead"]) is not int
                or type(projection["behind"]) is not int
                or type(projection["binding_lifecycle_profile"]) is not str
                or (projection["binding_commit"] is not None
                    and type(projection["binding_commit"]) is not str)
                or any(type(projection[field]) is not bool for field in (
                    "binding_committed", "binding_published",
                    "ready_for_binding_commit_review",
                ))):
            raise ValueError(_ERROR)
        return projection
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_response_lifecycle_v1(response: Mapping[str, object]) -> None:
    projection = _response_lifecycle_projection_v1(response)
    profile, commit = projection["binding_lifecycle_profile"], projection["binding_commit"]
    origin, ahead, behind = projection["origin_main"], projection["ahead"], projection["behind"]
    if (profile not in _LIFECYCLE_PROFILES
            or re.fullmatch(r"[0-9a-f]{40}", origin) is None
            or ahead < 0 or behind < 0):
        raise ValueError(_ERROR)
    if profile == "binding_precommit_candidate":
        expected = (None, False, False, True, _BASE, 0, 0)
    elif profile == "binding_committed_unpushed":
        if re.fullmatch(r"[0-9a-f]{40}", str(commit)) is None or commit == _BASE:
            raise ValueError(_ERROR)
        expected = (commit, True, False, False, _BASE, 1, 0)
    else:
        if re.fullmatch(r"[0-9a-f]{40}", str(commit)) is None or commit == _BASE:
            raise ValueError(_ERROR)
        expected = (commit, True, True, False, origin, ahead, behind)
    actual = (
        commit, projection["binding_committed"], projection["binding_published"],
        projection["ready_for_binding_commit_review"], origin, ahead, behind,
    )
    if actual != expected:
        raise ValueError(_ERROR)


def _expected_response_lifecycle(
    *, origin: str, ahead: int, behind: int, lifecycle: Mapping[str, object],
) -> dict[str, object]:
    witness = {
        "origin_main": origin, "ahead": ahead, "behind": behind,
        **{field: lifecycle[field] for field in _DERIVED_LIFECYCLE_FIELDS},
    }
    if tuple(witness) != _RESPONSE_LIFECYCLE_FIELDS:
        raise ValueError(_ERROR)
    _validate_response_lifecycle_v1(witness)
    return witness


def _validate_response_v1(
    response: object, matrix: tuple[dict[str, str], ...],
    registry: tuple[dict[str, str], ...], *,
    expected_lifecycle: Mapping[str, object],
) -> None:
    try:
        _validate_matrix_registry_v1(matrix, registry)
        if type(response) is not dict or tuple(response) != _RESPONSE_FIELDS:
            raise ValueError(_ERROR)
        if (any(type(response[field]) is not int for field in _RESPONSE_INT_FIELDS)
                or any(type(response[field]) is not bool
                       for field in _RESPONSE_BOOL_FIELDS)
                or any(type(response[field]) is not str
                       for field in _RESPONSE_STRING_FIELDS)
                or any(type(response[field]) is not tuple
                       for field in _RESPONSE_TUPLE_FIELDS)
                or (response["binding_commit"] is not None
                    and type(response["binding_commit"]) is not str)
                or _response_lifecycle_projection_v1(response) != expected_lifecycle
                or response["binding_version"] != _VERSION
                or response["error_contract"] != _ERROR
                or response["repository"] != _REPOSITORY
                or response["branch"] != _BRANCH
                or response["base_head"] != _BASE
                or response["base_head_subject"] != _BASE_SUBJECT
                or response["candidate_paths"] != _CANDIDATE_PATHS
                or response["source_records"] != _source_records()
                or response["authority_status_vocabulary"] != _STATUSES
                or response["current11_family_rule_authority_binding_matrix"] != matrix
                or response["family_and_warhead_rule_authority_registry"] != registry
                or response["current11_sample_count"] != 11
                or response["unique_reaction_family_count"] != 7
                or response["unique_warhead_rule_count"] != 7
                or response["boundary_review_completed_count"] != 11
                or response["selected_candidate_identity_attested_count"] != 11
                or response["reaction_family_identity_explicitly_attested_count"] != 0
                or response["warhead_rule_identity_explicitly_attested_count"] != 0
                or response["warhead_rule_full_semantics_explicitly_attested_count"] != 0
                or response["approved_structural_pattern_attested_count"] != 0
                or response["reaction_family_authority_bound_count"] != 0
                or response["approved_warhead_rule_authority_bound_count"] != 0
                or response["binding_conclusion"] != "family_and_rule_not_authoritative"
                or response["missing_authority_fields"] != _MISSING_AUTHORITY_FIELDS
                or response["ready_for_current11_role_annotation_proposal_generation"] is not False
                or response["ready_for_current11_minimal_seed_proposal_generation"] is not False
                or any(response[field] is not False for field in _SAFETY_FIELDS)
                or response["failure_matrix_case_count"] != 41
                or response["failure_matrix_cases"]
                != tuple(f"X{number:02d}" for number in range(1, 42))
                or response["generated_evidence_files"] != _GENERATED_PATHS
                or response["recommended_next_increment"] != _RECOMMENDED_NEXT
                or response["response_field_count"] != len(_RESPONSE_FIELDS)):
            raise ValueError(_ERROR)
        _validate_response_lifecycle_v1(response)
        unsigned = {
            field: response[field] for field in _RESPONSE_FIELDS
            if field != "response_unsigned_canonical_json_sha256"
        }
        payload = _canonical_json_bytes(unsigned)
        if (response["response_unsigned_canonical_json_byte_count"] != len(payload)
                or response["response_unsigned_canonical_json_sha256"] != _sha256(payload)):
            raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _synthetic_lifecycle_facts_v1(profile: str) -> dict[str, object]:
    if profile not in _LIFECYCLE_PROFILES:
        raise ValueError(_ERROR)
    blobs = {path: f"{index + 1:040x}" for index, path in enumerate(_CANDIDATE_PATHS)}
    facts: dict[str, object] = {
        "head": _BASE, "origin": _BASE, "ahead": 0, "behind": 0,
        "base_ancestor_head": True, "base_ancestor_origin": True,
        "tracked": (), "staged": (), "untracked": _CANDIDATE_PATHS,
        "repository_clean": False, "path_commits": [],
        "live_paths": {path: {"tracked": False, "mode": "100644", "blob": blobs[path]}
                       for path in _CANDIDATE_PATHS},
    }
    if profile == "binding_precommit_candidate":
        return facts
    commit_hash = "f" * 40
    facts.update({
        "head": commit_hash, "ahead": 1, "untracked": (),
        "repository_clean": True,
        "live_paths": {path: {"tracked": True, "mode": "100644",
                              "index_blob": blobs[path], "blob": blobs[path]}
                       for path in _CANDIDATE_PATHS},
        "path_commits": [{
            "commit": commit_hash, "parents": [_BASE],
            "subject": _FORMAL_COMMIT_SUBJECT, "changed_paths": _CANDIDATE_PATHS,
            "changed_statuses": {path: "A" for path in _CANDIDATE_PATHS},
            "path_modes": {path: "100644" for path in _CANDIDATE_PATHS},
            "path_blobs": blobs, "ancestor_head": True,
            "ancestor_origin": profile == "binding_published_successor",
        }],
    })
    if profile == "binding_published_successor":
        facts.update({"head": "e" * 40, "origin": "d" * 40,
                      "ahead": 2, "behind": 3})
    return facts


def _rehash_response_v1(response: dict[str, object]) -> None:
    for _iteration in range(8):
        unsigned = {field: response[field] for field in _RESPONSE_FIELDS
                    if field != "response_unsigned_canonical_json_sha256"}
        payload = _canonical_json_bytes(unsigned)
        if response["response_unsigned_canonical_json_byte_count"] == len(payload):
            break
        response["response_unsigned_canonical_json_byte_count"] = len(payload)
    else:
        raise ValueError(_ERROR)
    unsigned = {field: response[field] for field in _RESPONSE_FIELDS
                if field != "response_unsigned_canonical_json_sha256"}
    payload = _canonical_json_bytes(unsigned)
    if response["response_unsigned_canonical_json_byte_count"] != len(payload):
        raise ValueError(_ERROR)
    response["response_unsigned_canonical_json_sha256"] = _sha256(payload)


def _mutate_review_transport_sha_v1(
    state: dict[str, bytes], evidence_id: str, source_field: str,
    digest_field: str,
) -> None:
    record = _strict_json(state[evidence_id])
    original = state[evidence_id]
    record[source_field] = "a" * 64
    record[digest_field] = _sha256(_canonical_json_bytes({
        field: value for field, value in record.items()
        if field != digest_field
    }))
    state[evidence_id] = _canonical_json_bytes(record)
    if state[evidence_id] == original:
        raise ValueError(_ERROR)


def _apply_failure_mutation_v1(case_id: str, value: object) -> None:
    if case_id == "X01":
        value["matrix"] = value["matrix"][:-1]
    elif case_id == "X02":
        value["matrix"][1]["sample_index_row_id"] = value["matrix"][0]["sample_index_row_id"]
    elif case_id == "X03":
        value["matrix"][0]["candidate_reaction_family_id"] = ""
    elif case_id == "X04":
        value["matrix"][0]["candidate_warhead_rule_id"] = ""
    elif case_id == "X05": value["facts"][0]["family_candidate_count"] = 2
    elif case_id == "X06": value["facts"][0]["rule_candidate_count"] = 2
    elif case_id == "X07": value["facts"][0]["effective_family_id"] = "MISMATCH"
    elif case_id == "X08": value["facts"][0]["effective_rule_id"] = "MISMATCH"
    elif case_id == "X09": value["facts"][0]["registry_family_id"] = "MISMATCH"
    elif case_id == "X10": value["facts"][0]["reactive_atom_match"] = False
    elif case_id == "X11": value["facts"][0]["target_residue_atom"] = "NZ"
    elif case_id == "X12": value["facts"][0]["graph_sha_match"] = False
    elif case_id == "X13": value["facts"][0]["reaction_delta_match"] = False
    elif case_id == "X14": value["facts"][0]["leaving_group_match"] = False
    elif case_id == "X15": value["facts"][0]["warhead_atom_set_match"] = False
    elif case_id == "X16": value["facts"][0]["attachment_boundary_match"] = False
    elif case_id == "X17": value["matrix"][0]["reaction_family_identity_explicitly_attested"] = "true"
    elif case_id == "X18": value["matrix"][0]["warhead_rule_full_semantics_explicitly_attested"] = "true"
    elif case_id == "X19": value["facts"][0]["review_schema_family_attestation_field"] = True
    elif case_id == "X20": value["facts"][0]["review_schema_rule_attestation_field"] = True
    elif case_id == "X21": value["facts"][0]["registry_approved"] = True
    elif case_id == "X22": value["facts"][0]["registry_human_review_completed"] = True
    elif case_id == "X23": value["facts"][0]["smarts_complete_claim"] = True
    elif case_id == "X24": value["facts"][0]["graph_signature_equivalence_contract"] = True
    elif case_id == "X25": value["facts"][0]["rule_version_complete_claim"] = True
    elif case_id == "X26": value["facts"][0]["family_version_complete_claim"] = True
    elif case_id == "X27": value["facts"][0]["bond_orders_complete_claim"] = True
    elif case_id == "X28": value["facts"][0]["charge_complete_claim"] = True
    elif case_id == "X29": value["facts"][0]["match_count_complete_claim"] = True
    elif case_id == "X30": value["facts"][0]["priority_complete_claim"] = True
    elif case_id == "X31": value["facts"][0]["repeated_rule_definition_consistent"] = False
    elif case_id == "X32":
        value["ready_for_current11_role_annotation_proposal_generation"] = True
        _rehash_response_v1(value)
    elif case_id == "X33":
        value["ready_for_training"] = True
        _rehash_response_v1(value)
    elif case_id == "X34":
        value["recommended_next_increment"] = "wrong_next"
        _rehash_response_v1(value)
    elif case_id == "X35":
        value["reaction_family_authority_bound_count"] = 1
        _rehash_response_v1(value)
    elif case_id == "X36":
        value["path_commits"][0]["parents"] = ["a" * 40]
    elif case_id == "X37":
        path = _CANDIDATE_PATHS[0]
        value["live_paths"][path]["blob"] = "a" * 40
    elif case_id == "X38":
        value["origin_main"] = "a" * 40
        _rehash_response_v1(value)
    elif case_id == "X39":
        _mutate_review_transport_sha_v1(
            value, "S03", "source_submission_bundle_sha256",
            "ingestion_execution_bundle_sha256",
        )
    elif case_id == "X40":
        _mutate_review_transport_sha_v1(
            value, "S05",
            "source_multi_boundary_submission_bundle_filesystem_sha256",
            "multi_boundary_ingestion_execution_bundle_sha256",
        )
    elif case_id == "X41":
        _mutate_review_transport_sha_v1(
            value, "S06",
            "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256",
            "multi_boundary_authority_bundle_sha256",
        )
    else:
        raise ValueError(_ERROR)


def _validate_candidate_artifacts(
    repo_root: Path, matrix: tuple[dict[str, str], ...],
    registry: tuple[dict[str, str], ...],
) -> tuple[dict[str, Any], tuple[dict[str, str], ...]]:
    try:
        payloads = {path: (repo_root / path).read_bytes() for path in _GENERATED_PATHS}
    except OSError as error:
        raise ValueError(_ERROR) from error
    sources = _strict_csv(payloads[_SOURCE_PATH], _SOURCE_COLUMNS)
    matrix_rows = _strict_csv(payloads[_MATRIX_PATH], _MATRIX_COLUMNS)
    registry_rows = _strict_csv(payloads[_REGISTRY_PATH], _REGISTRY_COLUMNS)
    failures = _strict_csv(payloads[_FAILURE_PATH], _FAILURE_COLUMNS)
    manifest = _strict_json(payloads[_MANIFEST_PATH])
    expected_failures = tuple({
        "case_id": case, "failure_case": name, "mutation_signature": mutation,
        "validator_target": target,
        "test_node_id": (
            "tests/test_covapie_current11_reaction_family_and_approved_warhead_rule_"
            f"authority_binding_v1.py::test_failure_matrix_case_fails_closed[{case}]"
        ),
        "expected_error": _ERROR, "fails_closed": "true", "verified": "true",
    } for case, name, mutation, target in _FAILURE_SPECS)
    hashes = {Path(path).name: _sha256(payloads[path])
              for path in (_SOURCE_PATH, _MATRIX_PATH, _REGISTRY_PATH, _FAILURE_PATH)}
    if (tuple(sources) != _source_records() or tuple(matrix_rows) != matrix
            or tuple(registry_rows) != registry or tuple(failures) != expected_failures
            or manifest.get("binding_version") != _VERSION
            or manifest.get("base_commit") != _BASE
            or manifest.get("source_inventory_row_count") != len(_source_records())
            or manifest.get("current11_matrix_row_count") != 11
            or manifest.get("unique_family_rule_registry_row_count") != 7
            or manifest.get("failure_matrix_row_count") != 41
            or manifest.get("reaction_family_authority_bound_count") != 0
            or manifest.get("approved_warhead_rule_authority_bound_count") != 0
            or manifest.get("ready_for_current11_role_annotation_proposal_generation") is not False
            or manifest.get("ready_for_current11_minimal_seed_proposal_generation") is not False
            or manifest.get("recommended_next_increment") != _RECOMMENDED_NEXT
            or manifest.get("evidence_sha256") != hashes
            or any(manifest.get(field) is not False for field in (
                "role_proposal_generated", "minimal_seed_proposal_generated",
                "role_annotation_materialized", "minimal_seed_materialized",
                "tensor_materialized", "review_package_generated", "ready_for_training",
            ))):
        raise ValueError(_ERROR)
    return manifest, tuple(failures)


def _validate_failure_registry_bindings_v1(
    response: dict[str, object], matrix: tuple[dict[str, str], ...],
    registry: tuple[dict[str, str], ...], facts: tuple[dict[str, object], ...],
    state: dict[str, bytes], *, expected_lifecycle: Mapping[str, object],
) -> None:
    for case_id, _name, _signature, target in _FAILURE_SPECS:
        if target == "binding_state":
            baseline: object = _build_failure_state_v1(matrix, registry, facts)
            validator = _validate_binding_state_v1
        elif target == "lifecycle":
            baseline = _synthetic_lifecycle_facts_v1("binding_committed_unpushed")
            validator = _derive_binding_lifecycle_v1
        elif target == "review_lineage":
            baseline = copy.deepcopy(state)
            validator = _validate_review_transport_lineage_v1
        else:
            baseline = copy.deepcopy(response)
            validator = lambda value: _validate_response_v1(
                value, matrix, registry, expected_lifecycle=expected_lifecycle,
            )
        validator(baseline)
        mutated = copy.deepcopy(baseline)
        _apply_failure_mutation_v1(case_id, mutated)
        if mutated == baseline:
            raise ValueError(_ERROR)
        try:
            validator(mutated)
        except ValueError as error:
            if str(error) != _ERROR:
                raise ValueError(_ERROR) from error
        else:
            raise ValueError(_ERROR)


def evaluate_covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1(
    *, repo_root: Path,
) -> dict[str, object]:
    """Return the deterministic Current11 family/rule authority decision."""

    try:
        if type(repo_root) is not type(Path()) or not repo_root.is_absolute():
            raise ValueError(_ERROR)
        if Path(_git_text(repo_root, ["rev-parse", "--show-toplevel"]).strip()) != repo_root:
            raise ValueError(_ERROR)
        if _git_text(repo_root, ["remote", "get-url", "origin"]).strip() != _REMOTE:
            raise ValueError(_ERROR)
        head = _git_text(repo_root, ["rev-parse", "HEAD"]).strip()
        origin = _git_text(repo_root, ["rev-parse", "refs/remotes/origin/main"]).strip()
        branch = _git_text(repo_root, ["branch", "--show-current"]).strip()
        ahead_text, behind_text = _git_text(
            repo_root, ["rev-list", "--left-right", "--count",
                        "HEAD...refs/remotes/origin/main"],
        ).split()
        ahead, behind = int(ahead_text), int(behind_text)
        if (branch != _BRANCH
                or _git_text(repo_root, ["show", "-s", "--format=%s", _BASE]).strip()
                != _BASE_SUBJECT
                or not _is_ancestor(repo_root, _BASE, head)
                or not _is_ancestor(repo_root, _BASE, origin)):
            raise ValueError(_ERROR)
        for evidence_id, commit, _path, _digest, _authority, _note in _GIT_EVIDENCE:
            if not _is_ancestor(repo_root, commit, head):
                raise ValueError(_ERROR)
            _git_blob(repo_root, evidence_id)
        state = _read_state_evidence(repo_root)
        matrix, registry, facts = _derive_binding(repo_root, state)
        _validate_matrix_registry_v1(matrix, registry)
        _manifest, failures = _validate_candidate_artifacts(repo_root, matrix, registry)
        lifecycle = _derive_binding_lifecycle_v1(
            _collect_lifecycle(repo_root, head, origin, ahead, behind)
        )
        expected_lifecycle = _expected_response_lifecycle(
            origin=origin, ahead=ahead, behind=behind, lifecycle=lifecycle,
        )
        response: dict[str, object] = {
            "binding_version": _VERSION, "error_contract": _ERROR,
            "repository": _REPOSITORY, "branch": branch, "base_head": _BASE,
            "base_head_subject": _BASE_SUBJECT, **expected_lifecycle,
            "candidate_paths": _CANDIDATE_PATHS,
            "source_records": _source_records(),
            "authority_status_vocabulary": _STATUSES,
            "current11_family_rule_authority_binding_matrix": matrix,
            "family_and_warhead_rule_authority_registry": registry,
            "current11_sample_count": len(matrix),
            "unique_reaction_family_count": len({row["candidate_reaction_family_id"] for row in matrix}),
            "unique_warhead_rule_count": len(registry),
            "boundary_review_completed_count": sum(row["boundary_review_completed"] == "true" for row in matrix),
            "selected_candidate_identity_attested_count": sum(row["selected_candidate_identity_attested"] == "true" for row in matrix),
            "reaction_family_identity_explicitly_attested_count": 0,
            "warhead_rule_identity_explicitly_attested_count": 0,
            "warhead_rule_full_semantics_explicitly_attested_count": 0,
            "approved_structural_pattern_attested_count": 0,
            "reaction_family_authority_bound_count": 0,
            "approved_warhead_rule_authority_bound_count": 0,
            "binding_conclusion": "family_and_rule_not_authoritative",
            "missing_authority_fields": _MISSING_AUTHORITY_FIELDS,
            "ready_for_current11_role_annotation_proposal_generation": False,
            "ready_for_current11_minimal_seed_proposal_generation": False,
            **{field: False for field in _SAFETY_FIELDS},
            "failure_matrix_case_count": len(failures),
            "failure_matrix_cases": tuple(row["case_id"] for row in failures),
            "generated_evidence_files": _GENERATED_PATHS,
            "recommended_next_increment": _RECOMMENDED_NEXT,
            "response_field_count": len(_RESPONSE_FIELDS),
            "response_unsigned_canonical_json_byte_count": 0,
            "response_unsigned_canonical_json_sha256": "",
        }
        if tuple(response) != _RESPONSE_FIELDS:
            raise ValueError(_ERROR)
        _rehash_response_v1(response)
        _validate_response_v1(
            response, matrix, registry, expected_lifecycle=expected_lifecycle,
        )
        _validate_failure_registry_bindings_v1(
            response, matrix, registry, facts, state,
            expected_lifecycle=expected_lifecycle,
        )
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
