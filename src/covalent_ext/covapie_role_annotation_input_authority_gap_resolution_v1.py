"""Audit Current11 role-proposal input authority without molecular execution.

The gate reads only committed text blobs plus two SHA-bound formal state JSON
artifacts.  It never reads raw structures, imports RDKit/Torch, runs topology
restoration, executes Murcko/BRICS, or writes output.
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


__all__ = ("evaluate_covapie_role_annotation_input_authority_gap_resolution_v1",)


_ERROR = "COVAPIE_ROLE_ANNOTATION_INPUT_AUTHORITY_GAP_RESOLUTION_INVALID"
_VERSION = "covapie_role_annotation_input_authority_gap_resolution_v1"
_REPOSITORY = "fumx2000/DiffSBDD"
_REMOTE = "git@github.com:fumx2000/DiffSBDD.git"
_BRANCH = "main"
_BASE = "e206a732d1a72ac1a45002a3bf9c5ae8d659f692"
_BASE_SUBJECT = "add CovaPIE canonical five-level role and task mask materialization contract v1"
_FORMAL_COMMIT_SUBJECT = "add CovaPIE role annotation input authority gap resolution v1"
_RECOMMENDED_NEXT = (
    "bind_covapie_current11_reaction_family_and_approved_warhead_rule_authority_v1"
)

_STATUSES = (
    "authoritative_resolved", "candidate_only", "missing", "conflicted",
    "not_applicable",
)
_DIMENSIONS = (
    "retained_heavy_atom_mapping", "ligand_reactive_atom",
    "residue_reactive_atom", "pre_reaction_connectivity",
    "pre_reaction_bond_orders", "reaction_family_label",
    "approved_warhead_rule", "murcko_input", "brics_input",
)
_CORE_DIMENSIONS = _DIMENSIONS[:7]
_STATUS_FIELD_BY_DIMENSION = {
    "retained_heavy_atom_mapping": "retained_heavy_atom_mapping_status",
    "ligand_reactive_atom": "ligand_reactive_atom_status",
    "residue_reactive_atom": "residue_reactive_atom_status",
    "pre_reaction_connectivity": "pre_reaction_connectivity_status",
    "pre_reaction_bond_orders": "pre_reaction_bond_order_status",
    "reaction_family_label": "reaction_family_status",
    "approved_warhead_rule": "approved_warhead_rule_status",
    "murcko_input": "murcko_input_status",
    "brics_input": "brics_input_status",
}
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)
_EXPECTED_SAMPLE_AUTHORITY = (
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
    "covapie_role_annotation_input_authority_gap_resolution_v1"
)
_SOURCE_PATH = f"{_DATA_ROOT}/covapie_role_input_authority_source_inventory.csv"
_MATRIX_PATH = f"{_DATA_ROOT}/covapie_current11_role_input_authority_matrix.csv"
_SEMANTICS_PATH = f"{_DATA_ROOT}/covapie_role_input_authority_semantics_registry.csv"
_FAILURE_PATH = f"{_DATA_ROOT}/covapie_role_input_authority_failure_matrix.csv"
_MANIFEST_PATH = f"{_DATA_ROOT}/covapie_role_input_authority_gap_resolution_manifest.json"
_CANDIDATE_PATHS = tuple(sorted((
    _SOURCE_PATH,
    _MATRIX_PATH,
    _SEMANTICS_PATH,
    _FAILURE_PATH,
    _MANIFEST_PATH,
    "docs/covapie_role_annotation_input_authority_gap_resolution_v1_guide.md",
    "scripts/check_covapie_role_annotation_input_authority_gap_resolution_v1.py",
    "src/covalent_ext/covapie_role_annotation_input_authority_gap_resolution_v1.py",
    "tests/test_covapie_role_annotation_input_authority_gap_resolution_v1.py",
)))
_GENERATED_PATHS = (
    _SOURCE_PATH, _MATRIX_PATH, _SEMANTICS_PATH, _FAILURE_PATH, _MANIFEST_PATH,
)
_FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
    ".tgz", ".npz", ".tmp", ".part", ".pdb", ".sdf",
)

_FINAL_INDEX = (
    "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/"
    "final_dataset_index.csv"
)
_ATOM_PAIR = (
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1/covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
_HEAVY_MAPPING = (
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
    "covapie_heavy_atom_disposition_and_index_projection_matrix.csv"
)
_OBS_ROOT = (
    "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1"
)
_OBS_MAPPING = f"{_OBS_ROOT}/covapie_current11_observed_to_parent_atom_mapping_authority.csv"
_OBS_BONDS = f"{_OBS_ROOT}/covapie_current11_parent_and_observed_projected_bond_authority.csv"
_OBS_READY = f"{_OBS_ROOT}/covapie_current11_observed_projection_readiness_matrix.csv"
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

# id, commit, path, sha256, authority class, purpose
_GIT_EVIDENCE = (
    ("E01", _BASE, "data/derived/covalent_small/covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1/covapie_role_task_mask_contract_manifest.json", "f5f51d77b2bc347fc9eaf36b61fb9ab1561fb8542cb1a80df54f1474daf33f9f", "contract", "latest_canonical_role_task_mask_contract"),
    ("E02", "0fda7b9e8fc56941e005f3e8b5e67fa2ceaa4ca1", "src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py", "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b", "contract", "role_seed_predecessor"),
    ("E03", "0fda7b9e8fc56941e005f3e8b5e67fa2ceaa4ca1", "data/derived/covalent_small/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1/covapie_ligand_role_and_seed_contract_registry.csv", "872ecd0754ff941bee207161a54eecd1dd256d382044c38075b1c8ede89dba3d", "contract", "role_seed_semantics"),
    ("E04", "0fda7b9e8fc56941e005f3e8b5e67fa2ceaa4ca1", "data/derived/covalent_small/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1/covapie_current11_role_annotation_input_readiness_matrix.csv", "6def11ca3c1ec974479c3fa96d3f2c985b994eed86d6132008236fb18bca3d4b", "historical_gap_evidence", "predecessor_current11_readiness"),
    ("E05", "51e6d187a66e11b1ced5ba17d3835773f8c0f2a4", _FINAL_INDEX, "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d", "authoritative_resolved", "current11_sample_identity"),
    ("E06", "e5563ed50db6e56cbdfb6cc629e5eb4fe9137edf", _ATOM_PAIR, "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45", "authoritative_resolved", "ligand_and_residue_reactive_atom_mapping"),
    ("E07", "160cdbda8800a535b5c0a81d501babfae9a8615b", _HEAVY_MAPPING, "b53f438edffab32f78d07df839b8c8437ec4223e31bd8a8885deedf32497b4be", "authoritative_resolved", "retained_heavy_index_projection"),
    ("E08", "68c5ca5cf1ce5b20be5db9ce0b37e10830c09288", _OBS_MAPPING, "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e", "authoritative_resolved", "observed_to_parent_atom_mapping"),
    ("E09", "68c5ca5cf1ce5b20be5db9ce0b37e10830c09288", _OBS_BONDS, "bd31b7c074c3d4226c26bfe0210b9c3460f38c5087f1157b1167749f91bfffe0", "authoritative_resolved", "pre_reaction_connectivity_and_bond_orders"),
    ("E10", "68c5ca5cf1ce5b20be5db9ce0b37e10830c09288", _OBS_READY, "ec7bb2c203a7b13f525c413171b734fdd9f8af934b6e7e8eaf3fc6ae141128a0", "authoritative_resolved", "graph_readiness"),
    ("E11", "dc1222503dcec83220a28df2abdae898a0855864", _RULE_REGISTRY, "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309", "candidate_only", "unapproved_rule_registry"),
    ("E12", "0c8d1d10260a028360357b8c309f22676fc81645", _ASSIGNMENT, "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9", "candidate_only", "sample_candidate_family_rule_assignments"),
    ("E13", "51810f19e0bbb96171a7dd3aebd72ef08eda0200", "src/covalent_ext/covapie_current11_unified_effective_authority_view_v1.py", "c8f2af8fc0d5dd2f8c42e527cc3db34620b2992f567d59f32a19842254dac4f4", "contract", "unified_effective_authority_builder"),
    ("E14", "1cdbca345483022ece967b24de37013b77349cd4", "src/covalent_ext/covapie_current11_five_auxiliary_module_label_consumption_readiness_design_v1.py", "6e4b2b26545c039e61acc3821deaee86859eff0ed44b5deaca4290f187ee7681", "sha_bound_formal_state", "unified_view_transport_sha_binding"),
    ("E15", "1613c5efbb833f11ac3161d0d960c1342694cd4d", "src/covalent_ext/covapie_current11_target_residue_atom_condition_authority_v1.py", "1cf8839382bccfb595a841493a0e22c550578c02f2592dc7481ff67b078d7248", "authority_builder", "target_residue_atom_authority_builder"),
)
_GIT_BY_ID = {row[0]: row for row in _GIT_EVIDENCE}

# id, state-relative path, transport sha, binding commit, purpose
_STATE_EVIDENCE = (
    ("S01", "manual-review/covapie_current11_unified_effective_authority_view_v1.json", "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774", "1cdbca345483022ece967b24de37013b77349cd4", "warhead_boundary_unified_effective_authority"),
    ("S02", "manual-review/covapie_current11_target_residue_atom_condition_authority_bundle_v1.json", "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096", "b1fa272fc918a4c3a81c1c49bde0337b50450553", "target_residue_reactive_atom_authority"),
)

_SOURCE_COLUMNS = (
    "evidence_id", "source_namespace", "source_commit", "source_path",
    "source_sha256", "authority_class", "provides_dimensions", "lineage_note",
    "verified",
)
_MATRIX_COLUMNS = (
    "sample_index_row_id", "pdb_id", "ligand_identity",
    "retained_heavy_atom_count", "retained_heavy_atom_mapping_status",
    "retained_heavy_atom_mapping_source", "ligand_reactive_atom_status",
    "ligand_reactive_atom_id", "residue_reactive_atom_status",
    "residue_reactive_atom_id", "pre_reaction_connectivity_status",
    "pre_reaction_connectivity_source", "pre_reaction_connectivity_index_space",
    "pre_reaction_edge_count", "pre_reaction_bond_order_status",
    "pre_reaction_bond_order_source", "bond_order_vocabulary",
    "reaction_family_status", "reaction_family_id", "reaction_family_source",
    "approved_warhead_rule_status", "warhead_rule_id", "warhead_rule_source",
    "murcko_input_status", "brics_input_status", "murcko_proposal_method_ready",
    "brics_support_method_ready", "warhead_boundary_human_review_completed",
    "role_seed_human_gold_review_completed",
    "role_proposal_input_authority_ready",
    "minimal_seed_proposal_input_authority_ready", "blocking_reasons", "verified",
)
_SEMANTIC_COLUMNS = (
    "dimension_id", "semantic_name", "authoritative_resolved_definition",
    "candidate_only_boundary", "current11_status", "current11_coverage",
    "proposal_input", "verified",
)
_FAILURE_COLUMNS = (
    "case_id", "failure_case", "mutation_signature", "validator_target",
    "test_node_id", "expected_error", "fails_closed", "verified",
)
_FAILURE_MUTATIONS = {
    "X01": {"failure_case": "current11_sample_count_not_11", "mutation_signature": "sample_count=10", "validator_target": "matrix", "mutation": ("delete_matrix_row", 10), "expected_failure": _ERROR},
    "X02": {"failure_case": "duplicate_sample_identity", "mutation_signature": "duplicate_sample_index_row_id", "validator_target": "matrix", "mutation": ("copy_matrix_field", 1, 0, "sample_index_row_id"), "expected_failure": _ERROR},
    "X03": {"failure_case": "retained_heavy_mapping_missing", "mutation_signature": "mapping_status=missing", "validator_target": "matrix", "mutation": ("set_matrix_field", 0, "retained_heavy_atom_mapping_status", "missing"), "expected_failure": _ERROR},
    "X04": {"failure_case": "source_full_index_as_retained_index", "mutation_signature": "index_space=source_full_atom_row_index", "validator_target": "matrix", "mutation": ("set_matrix_field", 0, "pre_reaction_connectivity_index_space", "source_full_atom_row_index"), "expected_failure": _ERROR},
    "X05": {"failure_case": "pre_reaction_graph_missing", "mutation_signature": "connectivity_status=missing", "validator_target": "matrix", "mutation": ("set_matrix_field", 0, "pre_reaction_connectivity_status", "missing"), "expected_failure": _ERROR},
    "X06": {"failure_case": "post_reaction_graph_substitution", "mutation_signature": "connectivity_source=post_covalent_graph", "validator_target": "matrix", "mutation": ("set_matrix_field", 0, "pre_reaction_connectivity_source", "post_covalent_graph"), "expected_failure": _ERROR},
    "X07": {"failure_case": "connectivity_schema_without_values", "mutation_signature": "edge_count=0", "validator_target": "matrix", "mutation": ("clear_graph_edges", 0), "expected_failure": _ERROR},
    "X08": {"failure_case": "unmapped_smiles_atom_order", "mutation_signature": "index_space=smiles_atom_order", "validator_target": "matrix", "mutation": ("set_matrix_field", 0, "pre_reaction_connectivity_index_space", "smiles_atom_order"), "expected_failure": _ERROR},
    "X09": {"failure_case": "edge_self_loop", "mutation_signature": "graph_self_loop=true", "validator_target": "matrix", "mutation": ("graph_self_loop", 0), "expected_failure": _ERROR},
    "X10": {"failure_case": "duplicate_edge", "mutation_signature": "graph_duplicate_edge=true", "validator_target": "matrix", "mutation": ("graph_duplicate_edge", 0), "expected_failure": _ERROR},
    "X11": {"failure_case": "edge_out_of_range", "mutation_signature": "graph_edge_out_of_range=true", "validator_target": "matrix", "mutation": ("graph_edge_out_of_range", 0), "expected_failure": _ERROR},
    "X12": {"failure_case": "disconnected_graph_without_policy", "mutation_signature": "graph_disconnected=true", "validator_target": "matrix", "mutation": ("graph_disconnected", 0), "expected_failure": _ERROR},
    "X13": {"failure_case": "bond_order_missing", "mutation_signature": "bond_order_status=missing", "validator_target": "matrix", "mutation": ("set_matrix_field", 0, "pre_reaction_bond_order_status", "missing"), "expected_failure": _ERROR},
    "X14": {"failure_case": "distance_inferred_bond_order", "mutation_signature": "bond_order_source=distance_inference", "validator_target": "matrix", "mutation": ("set_matrix_field", 0, "pre_reaction_bond_order_source", "distance_inference"), "expected_failure": _ERROR},
    "X15": {"failure_case": "silent_all_single_bonds", "mutation_signature": "bond_order_vocabulary=single", "validator_target": "matrix", "mutation": ("set_matrix_field", 0, "bond_order_vocabulary", "single"), "expected_failure": _ERROR},
    "X16": {"failure_case": "connectivity_implies_bond_order", "mutation_signature": "bond_order_status=authoritative_resolved_without_evidence", "validator_target": "matrix", "mutation": ("set_matrix_field", 0, "pre_reaction_bond_order_source", ""), "expected_failure": _ERROR},
    "X17": {"failure_case": "reaction_family_missing", "mutation_signature": "reaction_family_status=missing_and_ready=true", "validator_target": "matrix", "mutation": ("set_two_matrix_fields", 0, "reaction_family_status", "missing", "role_proposal_input_authority_ready", "true"), "expected_failure": _ERROR},
    "X18": {"failure_case": "project_family_as_sample_family", "mutation_signature": "reaction_family_source=project_scope", "validator_target": "matrix", "mutation": ("set_matrix_field", 0, "reaction_family_source", "project_scope"), "expected_failure": _ERROR},
    "X19": {"failure_case": "reaction_family_conflict", "mutation_signature": "reaction_family_status=conflicted", "validator_target": "matrix", "mutation": ("set_matrix_field", 0, "reaction_family_status", "conflicted"), "expected_failure": _ERROR},
    "X20": {"failure_case": "warhead_rule_missing", "mutation_signature": "warhead_rule_status=missing_and_ready=true", "validator_target": "matrix", "mutation": ("set_two_matrix_fields", 0, "approved_warhead_rule_status", "missing", "minimal_seed_proposal_input_authority_ready", "true"), "expected_failure": _ERROR},
    "X21": {"failure_case": "rule_family_mismatch", "mutation_signature": "warhead_rule_reaction_family_mismatch=true", "validator_target": "matrix", "mutation": ("set_candidate_fact", 0, "rule_reaction_family_id", "COVAPIE_CYS_SG_REACTION_FAMILY_MISMATCH"), "expected_failure": _ERROR},
    "X22": {"failure_case": "rule_reactive_atom_mismatch", "mutation_signature": "warhead_rule_reactive_atom_mismatch=true", "validator_target": "matrix", "mutation": ("set_candidate_fact", 0, "rule_ligand_reactive_atom_id", "retained_heavy_local_index_0based:0|atom_name:WRONG"), "expected_failure": _ERROR},
    "X23": {"failure_case": "rule_warhead_atom_set_mismatch", "mutation_signature": "warhead_rule_atom_set_mismatch=true", "validator_target": "matrix", "mutation": ("set_candidate_fact", 0, "warhead_atom_set_consistent", False), "expected_failure": _ERROR},
    "X24": {"failure_case": "candidate_rule_as_approved", "mutation_signature": "candidate_rule_promoted=true", "validator_target": "matrix", "mutation": ("set_candidate_fact", 0, "approved", True), "expected_failure": _ERROR},
    "X25": {"failure_case": "ccd_smiles_implies_murcko_ready", "mutation_signature": "murcko_source=unmapped_ccd_smiles", "validator_target": "matrix", "mutation": ("set_candidate_fact", 0, "murcko_source", "unmapped_ccd_smiles"), "expected_failure": _ERROR},
    "X26": {"failure_case": "brics_evidence_as_gold_role", "mutation_signature": "role_seed_gold_source=brics", "validator_target": "matrix", "mutation": ("set_candidate_fact", 0, "role_seed_gold_source", "brics"), "expected_failure": _ERROR},
    "X27": {"failure_case": "warhead_review_as_role_seed_gold", "mutation_signature": "role_seed_gold_from_warhead_review=true", "validator_target": "matrix", "mutation": ("set_candidate_fact", 0, "role_seed_gold_from_warhead_review", True), "expected_failure": _ERROR},
    "X28": {"failure_case": "core_gap_but_role_ready", "mutation_signature": "role_ready=true_with_candidate_core", "validator_target": "matrix", "mutation": ("set_matrix_field", 0, "role_proposal_input_authority_ready", "true"), "expected_failure": _ERROR},
    "X29": {"failure_case": "seed_input_ready_means_seed_generated", "mutation_signature": "minimal_seed_generated=true", "validator_target": "execution_boundary", "mutation": ("set_response_field", "minimal_seed_proposal_generated", True), "expected_failure": _ERROR},
    "X30": {"failure_case": "role_or_seed_materialized", "mutation_signature": "role_or_seed_materialized=true", "validator_target": "execution_boundary", "mutation": ("set_response_field", "role_annotation_materialized", True), "expected_failure": _ERROR},
    "X31": {"failure_case": "training_ready", "mutation_signature": "ready_for_training=true", "validator_target": "execution_boundary", "mutation": ("set_response_field", "ready_for_training", True), "expected_failure": _ERROR},
    "X32": {"failure_case": "execution_boundary_crossed", "mutation_signature": "raw_network_rdkit_or_topology=true", "validator_target": "execution_boundary", "mutation": ("set_response_field", "raw_structure_read", True), "expected_failure": _ERROR},
    "X33": {"failure_case": "critical_response_tampering", "mutation_signature": "critical_field_changed_digest_recomputed", "validator_target": "response", "mutation": ("set_response_field_and_rehash", "source_records", ()), "expected_failure": _ERROR},
    "X34": {"failure_case": "candidate_lifecycle_not_survivable", "mutation_signature": "lifecycle_invalid=true", "validator_target": "lifecycle", "mutation": ("set_lifecycle_parent", "0" * 40), "expected_failure": _ERROR},
    "X35": {"failure_case": "index_hides_worktree_drift", "mutation_signature": "actual_blob_differs_from_index_blob", "validator_target": "lifecycle", "mutation": ("set_actual_blob", 0, "a" * 40), "expected_failure": _ERROR},
    "X36": {"failure_case": "recommended_next_mismatch", "mutation_signature": "recommended_next_increment=wrong", "validator_target": "response", "mutation": ("set_response_field_and_rehash", "recommended_next_increment", "wrong"), "expected_failure": _ERROR},
}
_FAILURES = tuple(
    (case_id, item["failure_case"], item["mutation_signature"])
    for case_id, item in _FAILURE_MUTATIONS.items()
)

_SEMANTICS = (
    ("D01", "retained_heavy_atom_mapping", "committed exact atom rows map source full-atom identity to contiguous retained_heavy_local_index_0based", "schema or unprojected source index", "authoritative_resolved", "11/11", "true"),
    ("D02", "ligand_reactive_atom", "sample-level exact-one atom-pair row maps to a retained-heavy local index and atom name", "project-level or unmapped name", "authoritative_resolved", "11/11", "true"),
    ("D03", "residue_reactive_atom", "sample-level resolved_authoritative target atom has exact atom_site identity", "residue class without sample atom identity", "authoritative_resolved", "11/11", "true"),
    ("D04", "pre_reaction_connectivity", "connected pre-covalent ligand internal edge table is projected to retained_heavy_local_index_0based", "schema post-covalent distance-inferred or unvalidated topology", "authoritative_resolved", "11/11", "true"),
    ("D05", "pre_reaction_bond_orders", "every projected ligand-internal edge carries committed normalized single double triple or aromatic authority", "missing distance-inferred post-reaction or silent-single values", "authoritative_resolved", "11/11", "true"),
    ("D06", "reaction_family_label", "approved sample-level family identity with frozen namespace version and lineage", "machine-derived unreviewed sample candidate or project scope", "candidate_only", "11/11 candidate", "true"),
    ("D07", "approved_warhead_rule", "approved family-matched versioned rule binds target and ligand reactive atoms warhead set expected bonds match count and priority", "unreviewed rule without approved SMARTS", "candidate_only", "11/11 candidate", "true"),
    ("D08", "murcko_input", "authoritative atom-indexed pre-reaction graph bond orders exact retained mapping and legal connected component", "unmapped CCD SMILES or proposal output", "authoritative_resolved", "11/11", "true"),
    ("D09", "brics_input", "authoritative atom-indexed pre-reaction graph bond orders exact retained mapping and legal connected component", "unmapped CCD SMILES or BRICS-derived role authority", "authoritative_resolved", "11/11", "true"),
    ("D10", "role_seed_human_gold_review_completed", "future role and minimal-seed gold review completed for the exact sample", "warhead-boundary review is a distinct predecessor authority", "missing", "0/11", "false"),
)

_RESPONSE_FIELDS = (
    "resolution_version", "error_contract", "repository", "branch", "base_head",
    "base_head_subject", "origin_main", "ahead", "behind",
    "authority_lifecycle_profile", "authority_commit", "authority_committed",
    "authority_published", "ready_for_authority_commit_review", "candidate_paths",
    "source_records", "authority_dimensions", "authority_status_vocabulary",
    "current11_authority_matrix", "authority_dimension_coverage",
    "warhead_boundary_human_review_completed_count",
    "role_seed_human_gold_review_completed_count",
    "current11_role_proposal_input_ready_count",
    "current11_minimal_seed_input_ready_count", "murcko_proposal_method_ready_count",
    "brics_support_method_ready_count",
    "ready_for_current11_role_annotation_proposal_generation",
    "ready_for_current11_minimal_seed_proposal_generation",
    "authority_gap_resolution_completed", "unresolved_dimensions",
    "role_proposal_generated", "minimal_seed_proposal_generated",
    "role_annotation_materialized", "minimal_seed_materialized",
    "tensor_materialized", "review_package_generated", "ready_for_training",
    "raw_structure_read", "network_accessed", "rdkit_imported",
    "topology_restoration_executed", "murcko_executed", "brics_executed",
    "checkpoint_accessed", "forward_executed", "training_executed",
    "reward_or_rl_executed", "failure_matrix_case_count", "failure_matrix_cases",
    "generated_evidence_files", "recommended_next_increment", "commit_created",
    "push_performed", "response_field_count", "response_sha256",
)
_SAFETY_FIELDS = (
    "role_proposal_generated", "minimal_seed_proposal_generated",
    "role_annotation_materialized", "minimal_seed_materialized",
    "tensor_materialized", "review_package_generated", "ready_for_training",
    "raw_structure_read", "network_accessed", "rdkit_imported",
    "topology_restoration_executed", "murcko_executed", "brics_executed",
    "checkpoint_accessed", "forward_executed", "training_executed",
    "reward_or_rl_executed", "commit_created", "push_performed",
)
_LIFECYCLE_PROFILES = (
    "authority_precommit_candidate", "authority_committed_unpushed",
    "authority_published_successor",
)
_RESPONSE_LIFECYCLE_FIELDS = (
    "origin_main", "ahead", "behind", "authority_lifecycle_profile",
    "authority_commit", "authority_committed", "authority_published",
    "ready_for_authority_commit_review",
)
_DERIVED_LIFECYCLE_FIELDS = _RESPONSE_LIFECYCLE_FIELDS[3:]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                          separators=(",", ":")).encode("utf-8")
    except Exception as error:
        raise ValueError(_ERROR) from error


def _strict_csv(payload: bytes, columns: Sequence[str]) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        rows = list(reader)
    except Exception as error:
        raise ValueError(_ERROR) from error
    if (not text.endswith("\n") or tuple(reader.fieldnames or ()) != tuple(columns)
            or any(None in row for row in rows)):
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


def _run_git(repo_root: Path, arguments: Sequence[str], *, allow_one: bool = False) -> tuple[int, bytes, bytes]:
    try:
        result = subprocess.run(["git", *arguments], cwd=repo_root,
                                env={**os.environ, "LC_ALL": "C", "LANG": "C"},
                                check=False, capture_output=True, timeout=30)
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
        _id, commit, path, digest, _authority, _purpose = _GIT_BY_ID[evidence_id]
    except Exception as error:
        raise ValueError(_ERROR) from error
    payload = _git(repo_root, ["show", f"{commit}:{path}"])
    if not payload or _sha256(payload) != digest:
        raise ValueError(_ERROR)
    return payload


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    rc, out, err = _run_git(repo_root, ["merge-base", "--is-ancestor", ancestor, descendant], allow_one=True)
    if out or err:
        raise ValueError(_ERROR)
    return rc == 0


def _state_root(repo_root: Path) -> Path:
    common = _git_text(repo_root, ["rev-parse", "--path-format=absolute", "--git-common-dir"]).strip()
    path = Path(common)
    candidate = path.parent.parent / "covapie-state"
    if not candidate.is_dir():
        candidate = repo_root.parent / "covapie-state"
    if not candidate.is_dir():
        raise ValueError(_ERROR)
    return candidate


def _read_state_evidence(repo_root: Path) -> dict[str, bytes]:
    root = _state_root(repo_root)
    result: dict[str, bytes] = {}
    for evidence_id, relative, digest, _commit, _purpose in _STATE_EVIDENCE:
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


def _validate_formal_state(
    state: Mapping[str, bytes],
) -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    unified = _strict_json(state["S01"])
    target = _strict_json(state["S02"])
    if (unified.get("effective_authority_record_count") != 11
            or unified.get("effective_legacy_exact_one_count") != 6
            or unified.get("effective_multi_boundary_exact_two_count") != 5
            or tuple(unified.get("sample_order", ())) != _EXPECTED_SAMPLES
            or type(unified.get("effective_authority_records")) is not list
            or len(unified["effective_authority_records"]) != 11
            or target.get("all_records_resolved_authoritative") is not True
            or target.get("resolved_authoritative_count") != 11
            or tuple(target.get("sample_order", ())) != _EXPECTED_SAMPLES
            or type(target.get("target_residue_atom_condition_records")) is not list
            or len(target["target_residue_atom_condition_records"]) != 11):
        raise ValueError(_ERROR)
    boundary_candidate_ids: dict[str, tuple[str, str]] = {}
    for wrapper, sample in zip(unified["effective_authority_records"], _EXPECTED_SAMPLES):
        authority = wrapper.get("effective_authority_record", {})
        cardinality = wrapper.get("effective_boundary_cardinality")
        if (wrapper.get("sample_index_row_id") != sample
                or wrapper.get("effective_authority_namespace") not in
                ("legacy_exact_one_boundary_v1", "exact_two_boundaries_multi_boundary_v1")
                or cardinality not in (1, 2)
                or authority.get("authority_status") != "active"
                or authority.get("sample_quarantined") is not False
                or authority.get("complete_warhead_atom_set_authority_available") is not True
                or (cardinality == 1 and authority.get("exact_one_attachment_boundary_authority_available") is not True)
                or (cardinality == 2 and authority.get("exact_two_attachment_boundaries_authority_available") is not True)
                or not authority.get("review_decision")
                or not authority.get("reaction_family_id")
                or not authority.get("warhead_rule_id")):
            raise ValueError(_ERROR)
        boundary_candidate_ids[sample] = (
            authority["reaction_family_id"], authority["warhead_rule_id"]
        )
    target_ids: dict[str, str] = {}
    for record, sample in zip(target["target_residue_atom_condition_records"], _EXPECTED_SAMPLES):
        if (record.get("sample_index_row_id") != sample
                or record.get("condition_authority_status") != "resolved_authoritative"
                or record.get("protein_auth_comp_id") != "CYS"
                or record.get("protein_auth_atom_id") != "SG"
                or not str(record.get("source_atom_site_id", "")).isdigit()):
            raise ValueError(_ERROR)
        target_ids[sample] = str(record["source_atom_site_id"])
    return target_ids, boundary_candidate_ids


def _derive_matrix(repo_root: Path, state: Mapping[str, bytes]) -> tuple[dict[str, str], ...]:
    final_rows = _strict_csv(_git_blob(repo_root, "E05"), (
        "sample_index_row_id", "sample_preparation_input_id", "sample_execution_id",
        "sample_qa_id", "pdb_id", "expected_het_id", "sample_artifact_root",
        "protein_atom_table_path", "ligand_atom_table_path", "pocket_atom_table_path",
        "covalent_event_table_path", "ligand_residue_atom_pair_table_path",
        "sample_preparation_audit_path", "protein_atom_count", "ligand_atom_count",
        "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count",
        "covalent_residue_name", "covalent_residue_chain_id", "covalent_residue_index",
        "covalent_residue_atom_name", "ligand_comp_id", "ligand_covalent_atom_name",
        "covalent_bond_atom_pair", "conn_id", "conn_type_id", "bond_distance_angstrom",
        "sample_index_status", "eligible_for_final_dataset_design",
        "ready_for_training_current_step", "feature_semantics_audit_required_before_training",
        "leakage_split_design_required_before_training",
    ))
    pair_rows = list(csv.DictReader(io.StringIO(_git_blob(repo_root, "E06").decode("utf-8"))))
    mapping_rows = list(csv.DictReader(io.StringIO(_git_blob(repo_root, "E08").decode("utf-8"))))
    bond_rows = list(csv.DictReader(io.StringIO(_git_blob(repo_root, "E09").decode("utf-8"))))
    ready_rows = list(csv.DictReader(io.StringIO(_git_blob(repo_root, "E10").decode("utf-8"))))
    assignment_rows = list(csv.DictReader(io.StringIO(_git_blob(repo_root, "E12").decode("utf-8"))))
    rule_rows = list(csv.DictReader(io.StringIO(_git_blob(repo_root, "E11").decode("utf-8"))))
    target_ids, boundary_candidate_ids = _validate_formal_state(state)
    if tuple(row["sample_index_row_id"] for row in final_rows) != _EXPECTED_SAMPLES:
        raise ValueError(_ERROR)
    by_pair: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in pair_rows:
        by_pair[row["sample_index_row_id"]][row["entity_role"]] = row
    by_mapping: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in mapping_rows:
        by_mapping[row["sample_index_row_id"]].append(row)
    by_bonds: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in bond_rows:
        if row["projected_to_observed_graph"] == "true":
            by_bonds[row["sample_index_row_id"]].append(row)
    ready = {row["sample_index_row_id"]: row for row in ready_rows}
    assignments = {row["sample_index_row_id"]: row for row in assignment_rows}
    rules = {row["warhead_rule_id"]: row for row in rule_rows}
    result: list[dict[str, str]] = []
    for final in final_rows:
        sample = final["sample_index_row_id"]
        atoms = by_mapping[sample]
        bonds = by_bonds[sample]
        graph = ready.get(sample, {})
        assignment = assignments.get(sample, {})
        ligand_pair = by_pair[sample].get("ligand_atom", {})
        target_pair = by_pair[sample].get("target_residue_atom", {})
        rule = rules.get(assignment.get("candidate_warhead_rule_id", ""), {})
        indices = sorted(int(row["retained_heavy_local_index_0based"]) for row in atoms)
        reactive = [row for row in atoms if row["reactive_ligand_atom"] == "true"]
        vocab = sorted({row["normalized_bond_order"] for row in bonds})
        undirected_edges: set[tuple[int, int]] = set()
        adjacency: dict[int, set[int]] = {index: set() for index in indices}
        for bond in bonds:
            left = int(bond["retained_heavy_local_index_1"])
            right = int(bond["retained_heavy_local_index_2"])
            edge = tuple(sorted((left, right)))
            if left == right or left not in adjacency or right not in adjacency or edge in undirected_edges:
                raise ValueError(_ERROR)
            undirected_edges.add(edge)
            adjacency[left].add(right)
            adjacency[right].add(left)
        visited: set[int] = set()
        pending = [indices[0]] if indices else []
        while pending:
            node = pending.pop()
            if node in visited:
                continue
            visited.add(node)
            pending.extend(sorted(adjacency[node] - visited))
        if (not atoms or indices != list(range(len(atoms))) or len(reactive) != 1
                or ligand_pair.get("mapping_outcome") != "mapped"
                or ligand_pair.get("matched_row_index_0based") != reactive[0]["retained_heavy_local_index_0based"]
                or reactive[0]["observed_atom_name"] != final["ligand_covalent_atom_name"]
                or target_pair.get("mapping_outcome") != "mapped"
                or target_pair.get("matched_atom_site_id") != target_ids[sample]
                or graph.get("observed_graph_valid") != "true"
                or graph.get("pre_reaction_connectivity_available") != "true"
                or graph.get("pre_reaction_bond_order_available") != "true"
                or int(graph.get("observed_atom_count", "-1")) != len(atoms)
                or int(graph.get("projected_bond_count", "-1")) != len(bonds)
                or any(row["retained_heavy_local_index_1_valid"] != "true"
                       or row["retained_heavy_local_index_2_valid"] != "true" for row in bonds)
                or visited != set(indices)
                or not vocab or vocab == ["single"]
                or not set(vocab) <= {"single", "double", "triple", "aromatic"}
                or assignment.get("assignment_status") != "machine_derived_candidate_assignment_materialized"
                or assignment.get("review_status") != "not_reviewed"
                or assignment.get("formal_reaction_family_label_available") != "false"
                or assignment.get("approved_warhead_rule_available") != "false"
                or assignment.get("ligand_reactive_atom_name") != reactive[0]["observed_atom_name"]
                or assignment.get("target_residue_name") != "CYS"
                or assignment.get("target_residue_atom_name") != "SG"
                or boundary_candidate_ids.get(sample) != (
                    assignment.get("candidate_reaction_family_id"),
                    assignment.get("candidate_warhead_rule_id"),
                )
                or rule.get("reaction_family_id") != assignment.get("candidate_reaction_family_id")
                or rule.get("target_residue_name") != "CYS"
                or rule.get("target_residue_atom_name") != "SG"
                or rule.get("formed_bond_order") != "single"
                or rule.get("candidate_rule_assignment_ready") != "true"
                or rule.get("exact_match_unique") != "true"
                or rule.get("approved") != "false"
                or rule.get("human_gold_review_completed") != "false"
                or rule.get("approved_warhead_smarts") != ""
                or rule.get("SMARTS_status") != "not_materialized_in_design_stage"):
            raise ValueError(_ERROR)
        result.append({
            "sample_index_row_id": sample,
            "pdb_id": final["pdb_id"],
            "ligand_identity": final["ligand_comp_id"],
            "retained_heavy_atom_count": str(len(atoms)),
            "retained_heavy_atom_mapping_status": "authoritative_resolved",
            "retained_heavy_atom_mapping_source": "E07|E08",
            "ligand_reactive_atom_status": "authoritative_resolved",
            "ligand_reactive_atom_id": f"retained_heavy_local_index_0based:{reactive[0]['retained_heavy_local_index_0based']}|atom_name:{reactive[0]['observed_atom_name']}",
            "residue_reactive_atom_status": "authoritative_resolved",
            "residue_reactive_atom_id": f"atom_site_id:{target_ids[sample]}|CYS:SG",
            "pre_reaction_connectivity_status": "authoritative_resolved",
            "pre_reaction_connectivity_source": "E08|E09|E10",
            "pre_reaction_connectivity_index_space": "retained_heavy_local_index_0based",
            "pre_reaction_edge_count": str(len(bonds)),
            "pre_reaction_bond_order_status": "authoritative_resolved",
            "pre_reaction_bond_order_source": "E09",
            "bond_order_vocabulary": "|".join(vocab),
            "reaction_family_status": "candidate_only",
            "reaction_family_id": assignment["candidate_reaction_family_id"],
            "reaction_family_source": "E12",
            "approved_warhead_rule_status": "candidate_only",
            "warhead_rule_id": assignment["candidate_warhead_rule_id"],
            "warhead_rule_source": "E11|E12",
            "murcko_input_status": "authoritative_resolved",
            "brics_input_status": "authoritative_resolved",
            "murcko_proposal_method_ready": "true",
            "brics_support_method_ready": "true",
            "warhead_boundary_human_review_completed": "true",
            "role_seed_human_gold_review_completed": "false",
            "role_proposal_input_authority_ready": "false",
            "minimal_seed_proposal_input_authority_ready": "false",
            "blocking_reasons": "reaction_family_label_candidate_only;approved_warhead_rule_candidate_only",
            "verified": "true",
        })
    return tuple(result)


def _validate_authority_matrix_v1(matrix: object) -> None:
    """Validate the complete Current11 authority matrix and its boundaries."""

    try:
        if type(matrix) is not tuple or len(matrix) != len(_EXPECTED_SAMPLES):
            raise ValueError(_ERROR)
        if tuple(_STATUS_FIELD_BY_DIMENSION) != _DIMENSIONS:
            raise ValueError(_ERROR)
        for row, expected in zip(matrix, _EXPECTED_SAMPLE_AUTHORITY):
            sample, pdb_id, ligand, family_id, rule_id = expected
            if (type(row) is not dict or tuple(row) != _MATRIX_COLUMNS
                    or any(type(value) is not str for value in row.values())
                    or (row["sample_index_row_id"], row["pdb_id"],
                        row["ligand_identity"], row["reaction_family_id"],
                        row["warhead_rule_id"]) != expected
                    or any(row[field] not in _STATUSES
                           for field in _STATUS_FIELD_BY_DIMENSION.values())):
                raise ValueError(_ERROR)
            atom_count_text = row["retained_heavy_atom_count"]
            edge_count_text = row["pre_reaction_edge_count"]
            if (re.fullmatch(r"[1-9][0-9]*", atom_count_text) is None
                    or re.fullmatch(r"[1-9][0-9]*", edge_count_text) is None):
                raise ValueError(_ERROR)
            atom_count = int(atom_count_text)
            edge_count = int(edge_count_text)
            ligand_match = re.fullmatch(
                r"retained_heavy_local_index_0based:([0-9]+)\|atom_name:([^|]+)",
                row["ligand_reactive_atom_id"],
            )
            residue_match = re.fullmatch(
                r"atom_site_id:([1-9][0-9]*)\|CYS:SG",
                row["residue_reactive_atom_id"],
            )
            vocabulary = tuple(row["bond_order_vocabulary"].split("|"))
            if (ligand_match is None or int(ligand_match.group(1)) >= atom_count
                    or residue_match is None or edge_count < atom_count - 1
                    or edge_count > atom_count * (atom_count - 1) // 2
                    or vocabulary != tuple(sorted(set(vocabulary)))
                    or not vocabulary or vocabulary == ("single",)
                    or not set(vocabulary) <= {"single", "double", "triple", "aromatic"}
                    or row["retained_heavy_atom_mapping_status"] != "authoritative_resolved"
                    or row["retained_heavy_atom_mapping_source"] != "E07|E08"
                    or row["ligand_reactive_atom_status"] != "authoritative_resolved"
                    or row["residue_reactive_atom_status"] != "authoritative_resolved"
                    or row["pre_reaction_connectivity_status"] != "authoritative_resolved"
                    or row["pre_reaction_connectivity_source"] != "E08|E09|E10"
                    or row["pre_reaction_connectivity_index_space"] != "retained_heavy_local_index_0based"
                    or row["pre_reaction_bond_order_status"] != "authoritative_resolved"
                    or row["pre_reaction_bond_order_source"] != "E09"
                    or row["reaction_family_status"] != "candidate_only"
                    or row["reaction_family_source"] != "E12"
                    or re.fullmatch(r"COVAPIE_CYS_SG_REACTION_FAMILY_[0-9A-F]{16}", family_id) is None
                    or row["approved_warhead_rule_status"] != "candidate_only"
                    or row["warhead_rule_source"] != "E11|E12"
                    or re.fullmatch(r"COVAPIE_CYS_SG_WARHEAD_RULE_[0-9A-F]{16}", rule_id) is None
                    or row["murcko_input_status"] != "authoritative_resolved"
                    or row["brics_input_status"] != "authoritative_resolved"
                    or row["murcko_proposal_method_ready"] != "true"
                    or row["brics_support_method_ready"] != "true"
                    or row["warhead_boundary_human_review_completed"] != "true"
                    or row["role_seed_human_gold_review_completed"] != "false"
                    or row["role_proposal_input_authority_ready"] != "false"
                    or row["minimal_seed_proposal_input_authority_ready"] != "false"
                    or row["blocking_reasons"] != "reaction_family_label_candidate_only;approved_warhead_rule_candidate_only"
                    or row["verified"] != "true"):
                raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _canonical_graph_edges_v1(atom_count: int, edge_count: int) -> tuple[tuple[int, int], ...]:
    if atom_count < 1 or not atom_count - 1 <= edge_count <= atom_count * (atom_count - 1) // 2:
        raise ValueError(_ERROR)
    edges = [(index, index + 1) for index in range(atom_count - 1)]
    present = set(edges)
    for left in range(atom_count):
        for right in range(left + 1, atom_count):
            if len(edges) == edge_count:
                return tuple(edges)
            if (left, right) not in present:
                edges.append((left, right))
                present.add((left, right))
    if len(edges) != edge_count:
        raise ValueError(_ERROR)
    return tuple(edges)


def _build_matrix_failure_state_v1(matrix: tuple[dict[str, str], ...]) -> dict[str, object]:
    _validate_authority_matrix_v1(matrix)
    graph_facts = tuple({
        "sample_index_row_id": row["sample_index_row_id"],
        "atom_count": int(row["retained_heavy_atom_count"]),
        "edges": _canonical_graph_edges_v1(
            int(row["retained_heavy_atom_count"]), int(row["pre_reaction_edge_count"])
        ),
    } for row in matrix)
    candidate_facts = tuple({
        "sample_index_row_id": row["sample_index_row_id"],
        "rule_reaction_family_id": row["reaction_family_id"],
        "rule_ligand_reactive_atom_id": row["ligand_reactive_atom_id"],
        "warhead_atom_set_consistent": True,
        "approved": False,
        "murcko_source": "authoritative_pre_reaction_graph",
        "role_seed_gold_source": "none",
        "role_seed_gold_from_warhead_review": False,
    } for row in matrix)
    return {"matrix": copy.deepcopy(matrix), "graph_facts": graph_facts,
            "candidate_facts": candidate_facts}


def _validate_failure_matrix_state_v1(value: object) -> None:
    try:
        if type(value) is not dict or tuple(value) != ("matrix", "graph_facts", "candidate_facts"):
            raise ValueError(_ERROR)
        matrix = value["matrix"]
        graph_facts = value["graph_facts"]
        candidate_facts = value["candidate_facts"]
        _validate_authority_matrix_v1(matrix)
        if (type(graph_facts) is not tuple or type(candidate_facts) is not tuple
                or len(graph_facts) != 11 or len(candidate_facts) != 11):
            raise ValueError(_ERROR)
        for row, graph, candidate in zip(matrix, graph_facts, candidate_facts):
            if (type(graph) is not dict
                    or tuple(graph) != ("sample_index_row_id", "atom_count", "edges")
                    or graph["sample_index_row_id"] != row["sample_index_row_id"]
                    or type(graph["atom_count"]) is not int
                    or graph["atom_count"] != int(row["retained_heavy_atom_count"])
                    or type(graph["edges"]) is not tuple
                    or len(graph["edges"]) != int(row["pre_reaction_edge_count"])):
                raise ValueError(_ERROR)
            atom_count = graph["atom_count"]
            edges = graph["edges"]
            normalized: list[tuple[int, int]] = []
            adjacency: dict[int, set[int]] = {index: set() for index in range(atom_count)}
            for edge in edges:
                if (type(edge) is not tuple or len(edge) != 2
                        or any(type(index) is not int for index in edge)):
                    raise ValueError(_ERROR)
                left, right = edge
                if left == right or not 0 <= left < atom_count or not 0 <= right < atom_count:
                    raise ValueError(_ERROR)
                normalized_edge = tuple(sorted((left, right)))
                if normalized_edge in normalized:
                    raise ValueError(_ERROR)
                normalized.append(normalized_edge)
                adjacency[left].add(right)
                adjacency[right].add(left)
            visited: set[int] = set()
            pending = [0]
            while pending:
                node = pending.pop()
                if node not in visited:
                    visited.add(node)
                    pending.extend(sorted(adjacency[node] - visited))
            if visited != set(range(atom_count)):
                raise ValueError(_ERROR)
            expected_candidate = {
                "sample_index_row_id": row["sample_index_row_id"],
                "rule_reaction_family_id": row["reaction_family_id"],
                "rule_ligand_reactive_atom_id": row["ligand_reactive_atom_id"],
                "warhead_atom_set_consistent": True,
                "approved": False,
                "murcko_source": "authoritative_pre_reaction_graph",
                "role_seed_gold_source": "none",
                "role_seed_gold_from_warhead_review": False,
            }
            if candidate != expected_candidate:
                raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _source_records() -> tuple[dict[str, str], ...]:
    records = []
    dimensions = {
        "E01": "readiness_boundary", "E02": "all_contract_semantics",
        "E03": "all_contract_semantics", "E04": "historical_all_nine",
        "E05": "sample_identity", "E06": "ligand_reactive_atom|residue_reactive_atom",
        "E07": "retained_heavy_atom_mapping", "E08": "retained_heavy_atom_mapping|pre_reaction_connectivity|murcko_input|brics_input",
        "E09": "pre_reaction_connectivity|pre_reaction_bond_orders|murcko_input|brics_input",
        "E10": "pre_reaction_connectivity|pre_reaction_bond_orders",
        "E11": "approved_warhead_rule_candidate", "E12": "reaction_family_label_candidate|approved_warhead_rule_candidate",
        "E13": "warhead_boundary_human_review", "E14": "warhead_boundary_human_review",
        "E15": "residue_reactive_atom", "S01": "warhead_boundary_human_review",
        "S02": "residue_reactive_atom",
    }
    for evidence_id, commit, path, digest, authority, purpose in _GIT_EVIDENCE:
        records.append({"evidence_id": evidence_id, "source_namespace": "git_object",
                        "source_commit": commit, "source_path": path,
                        "source_sha256": digest, "authority_class": authority,
                        "provides_dimensions": dimensions[evidence_id],
                        "lineage_note": purpose, "verified": "true"})
    for evidence_id, path, digest, commit, purpose in _STATE_EVIDENCE:
        records.append({"evidence_id": evidence_id, "source_namespace": "sha_bound_formal_state",
                        "source_commit": commit, "source_path": f"state://{path}",
                        "source_sha256": digest, "authority_class": "authoritative_resolved",
                        "provides_dimensions": dimensions[evidence_id],
                        "lineage_note": purpose, "verified": "true"})
    return tuple(records)


def _validate_candidate_artifacts(repo_root: Path, matrix: tuple[dict[str, str], ...]) -> tuple[dict[str, Any], tuple[dict[str, str], ...]]:
    _validate_authority_matrix_v1(matrix)
    try:
        payloads = {path: (repo_root / path).read_bytes() for path in _GENERATED_PATHS}
    except OSError as error:
        raise ValueError(_ERROR) from error
    source_rows = _strict_csv(payloads[_SOURCE_PATH], _SOURCE_COLUMNS)
    matrix_rows = _strict_csv(payloads[_MATRIX_PATH], _MATRIX_COLUMNS)
    semantics = _strict_csv(payloads[_SEMANTICS_PATH], _SEMANTIC_COLUMNS)
    failures = _strict_csv(payloads[_FAILURE_PATH], _FAILURE_COLUMNS)
    manifest = _strict_json(payloads[_MANIFEST_PATH])
    expected_sources = _source_records()
    expected_semantics = tuple(dict(zip(_SEMANTIC_COLUMNS, (*row, "true"))) for row in _SEMANTICS)
    expected_failures = tuple({
        "case_id": case, "failure_case": name, "mutation_signature": mutation,
        "validator_target": _FAILURE_MUTATIONS[case]["validator_target"],
        "test_node_id": f"tests/test_covapie_role_annotation_input_authority_gap_resolution_v1.py::test_failure_matrix_case_fails_closed[{case}]",
        "expected_error": _ERROR, "fails_closed": "true", "verified": "true",
    } for case, name, mutation in _FAILURES)
    if (tuple(source_rows) != expected_sources or tuple(matrix_rows) != matrix
            or tuple(semantics) != expected_semantics or tuple(failures) != expected_failures
            or tuple(_FAILURE_MUTATIONS) != tuple(f"X{number:02d}" for number in range(1, 37))
            or len({item["mutation"] for item in _FAILURE_MUTATIONS.values()}) != 36
            or set(item["validator_target"] for item in _FAILURE_MUTATIONS.values())
            != {"matrix", "response", "lifecycle", "execution_boundary"}
            or any(item["expected_failure"] != _ERROR
                   for item in _FAILURE_MUTATIONS.values())):
        raise ValueError(_ERROR)
    expected_hashes = {
        Path(path).name: _sha256(payloads[path])
        for path in (_SOURCE_PATH, _MATRIX_PATH, _SEMANTICS_PATH, _FAILURE_PATH)
    }
    if (manifest.get("resolution_version") != _VERSION
            or manifest.get("base_commit") != _BASE
            or manifest.get("source_inventory_row_count") != len(expected_sources)
            or manifest.get("current11_matrix_row_count") != 11
            or manifest.get("semantics_registry_row_count") != 10
            or manifest.get("failure_matrix_row_count") != len(_FAILURES)
            or manifest.get("evidence_sha256") != expected_hashes
            or manifest.get("authority_gap_resolution_completed") is not False
            or manifest.get("ready_for_current11_role_annotation_proposal_generation") is not False
            or manifest.get("ready_for_current11_minimal_seed_proposal_generation") is not False
            or manifest.get("recommended_next_increment") != _RECOMMENDED_NEXT
            or manifest.get("role_proposal_generated") is not False
            or manifest.get("minimal_seed_proposal_generated") is not False
            or manifest.get("role_annotation_materialized") is not False
            or manifest.get("minimal_seed_materialized") is not False
            or manifest.get("ready_for_training") is not False):
        raise ValueError(_ERROR)
    return manifest, tuple(failures)


def _validate_candidate_changes(*, tracked: object, staged: object, untracked: object) -> None:
    if type(tracked) is not tuple or type(staged) is not tuple or type(untracked) is not tuple or tracked or staged or untracked != _CANDIDATE_PATHS:
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


def _derive_authority_lifecycle_v1(facts: object) -> dict[str, object]:
    if type(facts) is not dict:
        raise ValueError(_ERROR)
    try:
        commits, live = facts["path_commits"], facts["live_paths"]
        tracked, staged, untracked = facts["tracked"], facts["staged"], facts["untracked"]
        if (facts["base_ancestor_head"] is not True or facts["base_ancestor_origin"] is not True
                or type(commits) is not list or len(commits) > 1 or type(live) is not dict
                or tuple(live) != _CANDIDATE_PATHS):
            raise ValueError(_ERROR)
        if not commits:
            _validate_candidate_changes(tracked=tracked, staged=staged, untracked=untracked)
            if (facts["head"] != _BASE or facts["origin"] != _BASE
                    or (facts["ahead"], facts["behind"]) != (0, 0)
                    or any(item.get("tracked") is not False or item.get("mode") != "100644"
                           for item in live.values())):
                raise ValueError(_ERROR)
            return {"authority_lifecycle_profile": "authority_precommit_candidate",
                    "authority_commit": None, "authority_committed": False,
                    "authority_published": False, "ready_for_authority_commit_review": True}
        commit = commits[0]
        if (re.fullmatch(r"[0-9a-f]{40}", str(commit.get("commit", ""))) is None
                or commit.get("parents") != [_BASE] or commit.get("subject") != _FORMAL_COMMIT_SUBJECT
                or tuple(commit.get("changed_paths", ())) != _CANDIDATE_PATHS
                or commit.get("changed_statuses") != {path: "A" for path in _CANDIDATE_PATHS}
                or set(commit.get("path_modes", ())) != set(_CANDIDATE_PATHS)
                or set(commit.get("path_blobs", ())) != set(_CANDIDATE_PATHS)
                or any(commit["path_modes"].get(path) != "100644" for path in _CANDIDATE_PATHS)
                or any(re.fullmatch(r"[0-9a-f]{40}", str(commit["path_blobs"].get(path, ""))) is None
                       for path in _CANDIDATE_PATHS)
                or any(live[path] != {"tracked": True, "mode": "100644",
                                      "index_blob": commit["path_blobs"][path],
                                      "blob": commit["path_blobs"][path]}
                       for path in _CANDIDATE_PATHS)
                or commit.get("ancestor_head") is not True
                or any(path in tracked or path in staged or path in untracked for path in _CANDIDATE_PATHS)):
            raise ValueError(_ERROR)
        if commit.get("ancestor_origin") is True:
            return {"authority_lifecycle_profile": "authority_published_successor",
                    "authority_commit": commit["commit"], "authority_committed": True,
                    "authority_published": True, "ready_for_authority_commit_review": False}
        if (facts["head"] != commit["commit"] or facts["origin"] != _BASE
                or (facts["ahead"], facts["behind"]) != (1, 0) or facts["repository_clean"] is not True):
            raise ValueError(_ERROR)
        return {"authority_lifecycle_profile": "authority_committed_unpushed",
                "authority_commit": commit["commit"], "authority_committed": True,
                "authority_published": False, "ready_for_authority_commit_review": False}
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _collect_lifecycle(repo_root: Path, head: str, origin: str, ahead: int, behind: int) -> dict[str, object]:
    tracked = tuple(sorted(_git_text(repo_root, ["diff", "--name-only"]).splitlines()))
    staged = tuple(sorted(_git_text(repo_root, ["diff", "--cached", "--name-only"]).splitlines()))
    untracked = tuple(sorted(_git_text(repo_root, ["ls-files", "--others", "--exclude-standard"]).splitlines()))
    revisions = set(_git_text(repo_root, ["rev-list", f"{_BASE}..{head}"]).splitlines())
    revisions.update(_git_text(repo_root, ["rev-list", f"{_BASE}..{origin}"]).splitlines())
    path_commits = []
    for commit_hash in sorted(revisions):
        lines = _git_text(repo_root, ["diff-tree", "--root", "--no-commit-id", "--name-status", "-r", commit_hash]).splitlines()
        statuses = {parts[1]: parts[0] for parts in (line.split("\t") for line in lines) if len(parts) == 2}
        if not set(statuses).intersection(_CANDIDATE_PATHS):
            continue
        modes, blobs = {}, {}
        for path in _CANDIDATE_PATHS:
            line = _git_text(repo_root, ["ls-tree", commit_hash, "--", path]).strip()
            if line:
                metadata, listed = line.split("\t", 1)
                mode, kind, blob = metadata.split()
                if listed != path or kind != "blob":
                    raise ValueError(_ERROR)
                modes[path], blobs[path] = mode, blob
        path_commits.append({"commit": commit_hash,
            "parents": _git_text(repo_root, ["show", "-s", "--format=%P", commit_hash]).split(),
            "subject": _git_text(repo_root, ["show", "-s", "--format=%s", commit_hash]).strip(),
            "changed_paths": tuple(sorted(statuses)),
            "changed_statuses": {path: statuses[path] for path in sorted(statuses)},
            "path_modes": {path: modes[path] for path in sorted(modes)},
            "path_blobs": {path: blobs[path] for path in sorted(blobs)},
            "ancestor_head": _is_ancestor(repo_root, commit_hash, head),
            "ancestor_origin": _is_ancestor(repo_root, commit_hash, origin)})
    return {"head": head, "origin": origin, "ahead": ahead, "behind": behind,
            "base_ancestor_head": _is_ancestor(repo_root, _BASE, head),
            "base_ancestor_origin": _is_ancestor(repo_root, _BASE, origin),
            "tracked": tracked, "staged": staged, "untracked": untracked,
            "repository_clean": not tracked and not staged and not untracked,
            "path_commits": path_commits,
            "live_paths": {path: _collect_live_identity(repo_root, path) for path in _CANDIDATE_PATHS}}


def _response_lifecycle_projection_v1(
    response: Mapping[str, object],
) -> dict[str, object]:
    """Project Exact8 lifecycle fields from a response without deriving facts."""

    try:
        if not isinstance(response, Mapping):
            raise ValueError(_ERROR)
        projection = {field: response[field] for field in _RESPONSE_LIFECYCLE_FIELDS}
        if (tuple(projection) != _RESPONSE_LIFECYCLE_FIELDS
                or type(projection["origin_main"]) is not str
                or type(projection["ahead"]) is not int
                or type(projection["behind"]) is not int
                or type(projection["authority_lifecycle_profile"]) is not str
                or (projection["authority_commit"] is not None
                    and type(projection["authority_commit"]) is not str)
                or any(type(projection[field]) is not bool for field in (
                    "authority_committed", "authority_published",
                    "ready_for_authority_commit_review",
                ))):
            raise ValueError(_ERROR)
        return projection
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _build_expected_response_lifecycle_v1(
    *, origin_main: str, ahead: int, behind: int,
    lifecycle: Mapping[str, object],
) -> dict[str, object]:
    """Build the external response witness from Git facts and derived lifecycle."""

    try:
        if (type(origin_main) is not str or type(ahead) is not int
                or type(behind) is not int or type(lifecycle) is not dict
                or tuple(lifecycle) != _DERIVED_LIFECYCLE_FIELDS):
            raise ValueError(_ERROR)
        witness = {
            "origin_main": origin_main, "ahead": ahead, "behind": behind,
            **{field: lifecycle[field] for field in _DERIVED_LIFECYCLE_FIELDS},
        }
        if tuple(witness) != _RESPONSE_LIFECYCLE_FIELDS:
            raise ValueError(_ERROR)
        _validate_response_lifecycle_v1(witness)
        return witness
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_response_lifecycle_v1(response: object) -> None:
    """Validate Exact3 response lifecycle fields without freezing a live profile."""

    try:
        projection = _response_lifecycle_projection_v1(response)
        profile = projection["authority_lifecycle_profile"]
        commit = projection["authority_commit"]
        origin = projection["origin_main"]
        ahead = projection["ahead"]
        behind = projection["behind"]
        if (profile not in _LIFECYCLE_PROFILES
                or re.fullmatch(r"[0-9a-f]{40}", str(origin)) is None
                or type(ahead) is not int or ahead < 0
                or type(behind) is not int or behind < 0
                or type(projection["authority_committed"]) is not bool
                or type(projection["authority_published"]) is not bool
                or type(projection["ready_for_authority_commit_review"]) is not bool):
            raise ValueError(_ERROR)
        if profile == "authority_precommit_candidate":
            expected = (None, False, False, True, _BASE, 0, 0)
        elif profile == "authority_committed_unpushed":
            if (re.fullmatch(r"[0-9a-f]{40}", str(commit)) is None
                    or commit == _BASE):
                raise ValueError(_ERROR)
            expected = (commit, True, False, False, _BASE, 1, 0)
        else:
            if (re.fullmatch(r"[0-9a-f]{40}", str(commit)) is None
                    or commit == _BASE):
                raise ValueError(_ERROR)
            expected = (commit, True, True, False, origin, ahead, behind)
        actual = (
            commit, projection["authority_committed"], projection["authority_published"],
            projection["ready_for_authority_commit_review"], origin, ahead, behind,
        )
        if actual != expected:
            raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_execution_boundary_v1(response: object) -> None:
    try:
        if type(response) is not dict or any(
            field not in response or type(response[field]) is not bool
            or response[field] is not False for field in _SAFETY_FIELDS
        ):
            raise ValueError(_ERROR)
        if (type(response.get("ready_for_current11_role_annotation_proposal_generation")) is not bool
                or response["ready_for_current11_role_annotation_proposal_generation"] is not False
                or type(response.get("ready_for_current11_minimal_seed_proposal_generation")) is not bool
                or response["ready_for_current11_minimal_seed_proposal_generation"] is not False):
            raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_response_v1(
    response: object, matrix: tuple[dict[str, str], ...], *,
    expected_lifecycle: Mapping[str, object],
) -> None:
    """Cross-validate response identity, aggregates, lifecycle, safety, and digest."""

    try:
        _validate_authority_matrix_v1(matrix)
        if type(response) is not dict or tuple(response) != _RESPONSE_FIELDS:
            raise ValueError(_ERROR)
        if (any(type(response[field]) is not str for field in (
                    "resolution_version", "error_contract", "repository", "branch",
                    "base_head", "base_head_subject", "origin_main",
                    "authority_lifecycle_profile", "recommended_next_increment",
                    "response_sha256"))
                or any(type(response[field]) is not int for field in (
                    "ahead", "behind", "warhead_boundary_human_review_completed_count",
                    "role_seed_human_gold_review_completed_count",
                    "current11_role_proposal_input_ready_count",
                    "current11_minimal_seed_input_ready_count",
                    "murcko_proposal_method_ready_count", "brics_support_method_ready_count",
                    "failure_matrix_case_count", "response_field_count"))
                or any(type(response[field]) is not bool for field in (
                    "authority_committed", "authority_published",
                    "ready_for_authority_commit_review",
                    "ready_for_current11_role_annotation_proposal_generation",
                    "ready_for_current11_minimal_seed_proposal_generation",
                    "authority_gap_resolution_completed", *_SAFETY_FIELDS))
                or (response["authority_commit"] is not None
                    and type(response["authority_commit"]) is not str)):
            raise ValueError(_ERROR)
        fixed_identity = (
            response["resolution_version"], response["error_contract"],
            response["repository"], response["branch"], response["base_head"],
            response["base_head_subject"], response["candidate_paths"],
            response["source_records"], response["authority_dimensions"],
            response["authority_status_vocabulary"],
        )
        expected_identity = (
            _VERSION, _ERROR, _REPOSITORY, _BRANCH, _BASE, _BASE_SUBJECT,
            _CANDIDATE_PATHS, _source_records(), _DIMENSIONS, _STATUSES,
        )
        if fixed_identity != expected_identity or response["current11_authority_matrix"] != matrix:
            raise ValueError(_ERROR)
        coverage = {
            dimension: {
                status: sum(
                    row[_STATUS_FIELD_BY_DIMENSION[dimension]] == status for row in matrix
                ) for status in _STATUSES
            } for dimension in _DIMENSIONS
        }
        response_coverage = response["authority_dimension_coverage"]
        if (type(response_coverage) is not dict
                or tuple(response_coverage) != _DIMENSIONS
                or any(type(response_coverage[dimension]) is not dict
                       or tuple(response_coverage[dimension]) != _STATUSES
                       or any(type(response_coverage[dimension][status]) is not int
                              for status in _STATUSES)
                       for dimension in _DIMENSIONS)):
            raise ValueError(_ERROR)
        warhead_review_count = sum(
            row["warhead_boundary_human_review_completed"] == "true" for row in matrix
        )
        role_seed_gold_count = sum(
            row["role_seed_human_gold_review_completed"] == "true" for row in matrix
        )
        role_ready_count = sum(
            row["role_proposal_input_authority_ready"] == "true" for row in matrix
        )
        seed_ready_count = sum(
            row["minimal_seed_proposal_input_authority_ready"] == "true" for row in matrix
        )
        murcko_count = sum(row["murcko_proposal_method_ready"] == "true" for row in matrix)
        brics_count = sum(row["brics_support_method_ready"] == "true" for row in matrix)
        unresolved = tuple(
            dimension for dimension in _CORE_DIMENSIONS
            if any(row[_STATUS_FIELD_BY_DIMENSION[dimension]] != "authoritative_resolved"
                   for row in matrix)
        )
        completed = not unresolved
        aggregates = (
            response_coverage,
            response["warhead_boundary_human_review_completed_count"],
            response["role_seed_human_gold_review_completed_count"],
            response["current11_role_proposal_input_ready_count"],
            response["current11_minimal_seed_input_ready_count"],
            response["murcko_proposal_method_ready_count"],
            response["brics_support_method_ready_count"],
            response["ready_for_current11_role_annotation_proposal_generation"],
            response["ready_for_current11_minimal_seed_proposal_generation"],
            response["unresolved_dimensions"],
            response["authority_gap_resolution_completed"],
        )
        expected_aggregates = (
            coverage, warhead_review_count, role_seed_gold_count, role_ready_count,
            seed_ready_count, murcko_count, brics_count,
            role_ready_count == len(matrix), seed_ready_count == len(matrix),
            unresolved, completed,
        )
        if aggregates != expected_aggregates:
            raise ValueError(_ERROR)
        if (type(expected_lifecycle) is not dict
                or tuple(expected_lifecycle) != _RESPONSE_LIFECYCLE_FIELDS):
            raise ValueError(_ERROR)
        _validate_response_lifecycle_v1(expected_lifecycle)
        _validate_response_lifecycle_v1(response)
        if _response_lifecycle_projection_v1(response) != expected_lifecycle:
            raise ValueError(_ERROR)
        _validate_execution_boundary_v1(response)
        exact_failure_cases = tuple(f"X{number:02d}" for number in range(1, 37))
        if (response["failure_matrix_case_count"] != 36
                or response["failure_matrix_cases"] != exact_failure_cases
                or response["generated_evidence_files"] != _GENERATED_PATHS
                or unresolved != ("reaction_family_label", "approved_warhead_rule")
                or response["recommended_next_increment"] != _RECOMMENDED_NEXT
                or response["response_field_count"] != len(_RESPONSE_FIELDS)
                or response["response_sha256"] != _sha256(_canonical_json_bytes({
                    field: response[field] for field in _RESPONSE_FIELDS
                    if field != "response_sha256"
                }))):
            raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_response(
    response: object, matrix: tuple[dict[str, str], ...], *,
    expected_lifecycle: Mapping[str, object],
) -> None:
    _validate_response_v1(
        response, matrix, expected_lifecycle=expected_lifecycle,
    )


def _synthetic_lifecycle_facts_v1(profile: str) -> dict[str, object]:
    if profile not in _LIFECYCLE_PROFILES:
        raise ValueError(_ERROR)
    blobs = {
        path: f"{position + 1:040x}"
        for position, path in enumerate(_CANDIDATE_PATHS)
    }
    facts: dict[str, object] = {
        "head": _BASE, "origin": _BASE, "ahead": 0, "behind": 0,
        "base_ancestor_head": True, "base_ancestor_origin": True,
        "tracked": (), "staged": (), "untracked": _CANDIDATE_PATHS,
        "repository_clean": False, "path_commits": [],
        "live_paths": {
            path: {"tracked": False, "mode": "100644", "blob": blobs[path]}
            for path in _CANDIDATE_PATHS
        },
    }
    if profile == "authority_precommit_candidate":
        return facts
    commit_hash = "f" * 40
    facts.update({
        "head": commit_hash, "ahead": 1, "untracked": (), "repository_clean": True,
        "live_paths": {
            path: {"tracked": True, "mode": "100644",
                   "index_blob": blobs[path], "blob": blobs[path]}
            for path in _CANDIDATE_PATHS
        },
        "path_commits": [{
            "commit": commit_hash, "parents": [_BASE],
            "subject": _FORMAL_COMMIT_SUBJECT, "changed_paths": _CANDIDATE_PATHS,
            "changed_statuses": {path: "A" for path in _CANDIDATE_PATHS},
            "path_modes": {path: "100644" for path in _CANDIDATE_PATHS},
            "path_blobs": blobs, "ancestor_head": True,
            "ancestor_origin": profile == "authority_published_successor",
        }],
    })
    if profile == "authority_published_successor":
        facts.update({"head": "e" * 40, "origin": "d" * 40,
                      "ahead": 2, "behind": 3, "repository_clean": True})
    return facts


def _failure_baseline_v1(
    target: str, response: dict[str, object], matrix: tuple[dict[str, str], ...], *,
    expected_lifecycle: Mapping[str, object],
) -> object:
    if target == "matrix":
        return _build_matrix_failure_state_v1(matrix)
    if target == "lifecycle":
        return _synthetic_lifecycle_facts_v1("authority_committed_unpushed")
    if target == "response":
        _validate_response_v1(
            response, matrix, expected_lifecycle=expected_lifecycle,
        )
        return copy.deepcopy(response)
    if target == "execution_boundary":
        return copy.deepcopy(response)
    raise ValueError(_ERROR)


def _rehash_response_v1(response: dict[str, object]) -> None:
    response["response_sha256"] = _sha256(_canonical_json_bytes({
        field: response[field] for field in _RESPONSE_FIELDS
        if field != "response_sha256"
    }))


def _apply_failure_mutation_v1(case_id: str, value: object) -> None:
    try:
        operation = _FAILURE_MUTATIONS[case_id]["mutation"]
        name = operation[0]
        if name == "delete_matrix_row":
            index = operation[1]
            value["matrix"] = value["matrix"][:index] + value["matrix"][index + 1:]
        elif name == "copy_matrix_field":
            target, source, field = operation[1:]
            value["matrix"][target][field] = value["matrix"][source][field]
        elif name == "set_matrix_field":
            index, field, replacement = operation[1:]
            value["matrix"][index][field] = replacement
        elif name == "set_two_matrix_fields":
            index, field_a, value_a, field_b, value_b = operation[1:]
            value["matrix"][index][field_a] = value_a
            value["matrix"][index][field_b] = value_b
        elif name == "clear_graph_edges":
            value["graph_facts"][operation[1]]["edges"] = ()
        elif name == "graph_self_loop":
            graph = value["graph_facts"][operation[1]]
            graph["edges"] = ((0, 0),) + graph["edges"][1:]
        elif name == "graph_duplicate_edge":
            graph = value["graph_facts"][operation[1]]
            graph["edges"] = (graph["edges"][0], graph["edges"][0]) + graph["edges"][2:]
        elif name == "graph_edge_out_of_range":
            graph = value["graph_facts"][operation[1]]
            graph["edges"] = ((0, graph["atom_count"]),) + graph["edges"][1:]
        elif name == "graph_disconnected":
            graph = value["graph_facts"][operation[1]]
            pairs = tuple(
                (left, right) for left in range(graph["atom_count"] - 1)
                for right in range(left + 1, graph["atom_count"] - 1)
            )
            graph["edges"] = pairs[:len(graph["edges"])]
        elif name == "set_candidate_fact":
            index, field, replacement = operation[1:]
            value["candidate_facts"][index][field] = replacement
        elif name in ("set_response_field", "set_response_field_and_rehash"):
            field, replacement = operation[1:]
            value[field] = replacement
            if name.endswith("and_rehash"):
                _rehash_response_v1(value)
        elif name == "set_lifecycle_parent":
            value["path_commits"][0]["parents"] = [operation[1]]
        elif name == "set_actual_blob":
            path = _CANDIDATE_PATHS[operation[1]]
            value["live_paths"][path]["blob"] = operation[2]
        else:
            raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_failure_target_v1(
    target: str, value: object, matrix: tuple[dict[str, str], ...], *,
    expected_lifecycle: Mapping[str, object],
) -> None:
    if target == "matrix":
        _validate_failure_matrix_state_v1(value)
    elif target == "response":
        _validate_response_v1(
            value, matrix, expected_lifecycle=expected_lifecycle,
        )
    elif target == "lifecycle":
        _derive_authority_lifecycle_v1(value)
    elif target == "execution_boundary":
        _validate_execution_boundary_v1(value)
    else:
        raise ValueError(_ERROR)


def _validate_failure_registry_bindings_v1(
    response: dict[str, object], matrix: tuple[dict[str, str], ...], *,
    expected_lifecycle: Mapping[str, object],
) -> None:
    for case_id, item in _FAILURE_MUTATIONS.items():
        target = item["validator_target"]
        baseline = _failure_baseline_v1(
            target, response, matrix, expected_lifecycle=expected_lifecycle,
        )
        _validate_failure_target_v1(
            target, baseline, matrix, expected_lifecycle=expected_lifecycle,
        )
        baseline_bytes = _canonical_json_bytes(baseline)
        mutated = copy.deepcopy(baseline)
        _apply_failure_mutation_v1(case_id, mutated)
        if _canonical_json_bytes(mutated) == baseline_bytes:
            raise ValueError(_ERROR)
        try:
            _validate_failure_target_v1(
                target, mutated, matrix, expected_lifecycle=expected_lifecycle,
            )
        except ValueError as error:
            if str(error) != item["expected_failure"]:
                raise ValueError(_ERROR) from error
        else:
            raise ValueError(_ERROR)


def evaluate_covapie_role_annotation_input_authority_gap_resolution_v1(*, repo_root: Path) -> dict[str, object]:
    """Return the deterministic, fail-closed Current11 authority audit."""

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
        ahead_text, behind_text = _git_text(repo_root, ["rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"]).split()
        ahead, behind = int(ahead_text), int(behind_text)
        if (branch != _BRANCH
                or _git_text(repo_root, ["show", "-s", "--format=%s", _BASE]).strip() != _BASE_SUBJECT
                or not _is_ancestor(repo_root, _BASE, head)
                or not _is_ancestor(repo_root, _BASE, origin)):
            raise ValueError(_ERROR)
        for evidence_id, commit, _path, _digest, _authority, _purpose in _GIT_EVIDENCE:
            if not _is_ancestor(repo_root, commit, head):
                raise ValueError(_ERROR)
            _git_blob(repo_root, evidence_id)
        for _evidence_id, _path, _digest, binding_commit, _purpose in _STATE_EVIDENCE:
            if not _is_ancestor(repo_root, binding_commit, head):
                raise ValueError(_ERROR)
        state = _read_state_evidence(repo_root)
        matrix = _derive_matrix(repo_root, state)
        _manifest, failures = _validate_candidate_artifacts(repo_root, matrix)
        lifecycle = _derive_authority_lifecycle_v1(_collect_lifecycle(repo_root, head, origin, ahead, behind))
        expected_lifecycle = _build_expected_response_lifecycle_v1(
            origin_main=origin, ahead=ahead, behind=behind, lifecycle=lifecycle,
        )
        coverage = {
            dimension: {status: sum(row[_STATUS_FIELD_BY_DIMENSION[dimension]] == status for row in matrix)
                        for status in _STATUSES}
            for dimension in _DIMENSIONS
        }
        response: dict[str, object] = {
            "resolution_version": _VERSION, "error_contract": _ERROR,
            "repository": _REPOSITORY, "branch": branch, "base_head": _BASE,
            "base_head_subject": _BASE_SUBJECT, "origin_main": origin,
            "ahead": ahead, "behind": behind, **lifecycle,
            "candidate_paths": _CANDIDATE_PATHS, "source_records": _source_records(),
            "authority_dimensions": _DIMENSIONS,
            "authority_status_vocabulary": _STATUSES,
            "current11_authority_matrix": matrix,
            "authority_dimension_coverage": coverage,
            "warhead_boundary_human_review_completed_count": sum(row["warhead_boundary_human_review_completed"] == "true" for row in matrix),
            "role_seed_human_gold_review_completed_count": sum(row["role_seed_human_gold_review_completed"] == "true" for row in matrix),
            "current11_role_proposal_input_ready_count": sum(row["role_proposal_input_authority_ready"] == "true" for row in matrix),
            "current11_minimal_seed_input_ready_count": sum(row["minimal_seed_proposal_input_authority_ready"] == "true" for row in matrix),
            "murcko_proposal_method_ready_count": sum(row["murcko_proposal_method_ready"] == "true" for row in matrix),
            "brics_support_method_ready_count": sum(row["brics_support_method_ready"] == "true" for row in matrix),
            "ready_for_current11_role_annotation_proposal_generation": all(row["role_proposal_input_authority_ready"] == "true" for row in matrix),
            "ready_for_current11_minimal_seed_proposal_generation": all(row["minimal_seed_proposal_input_authority_ready"] == "true" for row in matrix),
            "authority_gap_resolution_completed": all(all(row[_STATUS_FIELD_BY_DIMENSION[dimension]] == "authoritative_resolved" for dimension in _CORE_DIMENSIONS) for row in matrix),
            "unresolved_dimensions": tuple(dimension for dimension in _CORE_DIMENSIONS if any(row[_STATUS_FIELD_BY_DIMENSION[dimension]] != "authoritative_resolved" for row in matrix)),
            "role_proposal_generated": False, "minimal_seed_proposal_generated": False,
            "role_annotation_materialized": False, "minimal_seed_materialized": False,
            "tensor_materialized": False, "review_package_generated": False,
            "ready_for_training": False, "raw_structure_read": False,
            "network_accessed": False, "rdkit_imported": False,
            "topology_restoration_executed": False, "murcko_executed": False,
            "brics_executed": False, "checkpoint_accessed": False,
            "forward_executed": False, "training_executed": False,
            "reward_or_rl_executed": False,
            "failure_matrix_case_count": len(failures),
            "failure_matrix_cases": tuple(row["case_id"] for row in failures),
            "generated_evidence_files": _GENERATED_PATHS,
            "recommended_next_increment": _RECOMMENDED_NEXT,
            "commit_created": False, "push_performed": False,
            "response_field_count": len(_RESPONSE_FIELDS), "response_sha256": "",
        }
        if tuple(response) != _RESPONSE_FIELDS:
            raise ValueError(_ERROR)
        response["response_sha256"] = _sha256(_canonical_json_bytes({
            field: response[field] for field in _RESPONSE_FIELDS if field != "response_sha256"
        }))
        _validate_response_v1(
            response, matrix, expected_lifecycle=expected_lifecycle,
        )
        _validate_failure_registry_bindings_v1(
            response, matrix, expected_lifecycle=expected_lifecycle,
        )
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
