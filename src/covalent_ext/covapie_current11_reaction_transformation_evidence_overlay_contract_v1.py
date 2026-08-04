"""Validate the metadata-only Current11 reaction-transformation overlay design.

The overlay describes evidence that a future human review must provide.  It
does not infer a post-reaction graph, parse chemistry, approve a rule, or write
any repository or external-workspace file.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


__all__ = (
    "evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1",
)


SCHEMA_VERSION = (
    "covapie_current11_reaction_transformation_evidence_overlay_contract_v1"
)
ERROR = f"{SCHEMA_VERSION}_validation_failed"
BASE_COMMIT = "35a87a46b08b1362c990c10e95b7ab03d1865af5"
REVIEW_PACKAGE_COMMIT = BASE_COMMIT
BRANCH = "main"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 reaction transformation evidence overlay contract v1"
)
PARENT_REVIEW_UNIT_ID = "CURRENT11_FAMILY_RULE_APPROVAL_REVIEW_UNIT_000001"
TRANSFORMATION_REVIEW_UNIT_ID = (
    "CURRENT11_REACTION_TRANSFORMATION_REVIEW_UNIT_000001"
)
REACTION_FAMILY_ID = "COVAPIE_CYS_SG_REACTION_FAMILY_11AA213C661B48E3"
WARHEAD_RULE_ID = "COVAPIE_CYS_SG_WARHEAD_RULE_106441A31FA4F951"
CANDIDATE_LOCAL_GRAPH_SHA256 = (
    "106441a31fa4f9516c174c5a0fa89709e820ebeeff419ba30883ea34a1c26bb6"
)
SAMPLE_IDS = (
    "CYS_SG_SAMPLE_INDEX_000008",
    "CYS_SG_SAMPLE_INDEX_000010",
)
SAMPLE_FACTS = {
    SAMPLE_IDS[0]: {"pdb_id": "1AYU", "ligand_identity": "INA"},
    SAMPLE_IDS[1]: {"pdb_id": "1AYW", "ligand_identity": "IN3"},
}

DATA_ROOT = (
    "data/derived/covalent_small/"
    "covapie_current11_reaction_transformation_evidence_overlay_contract_v1"
)
SOURCE_INVENTORY_PATH = (
    f"{DATA_ROOT}/covapie_reaction_transformation_overlay_source_inventory.csv"
)
FIELD_CONTRACT_PATH = (
    f"{DATA_ROOT}/covapie_reaction_transformation_overlay_field_contract.csv"
)
GAP_MATRIX_PATH = (
    f"{DATA_ROOT}/covapie_current11_unit_000001_transformation_gap_matrix.csv"
)
FAILURE_MATRIX_PATH = (
    f"{DATA_ROOT}/covapie_reaction_transformation_overlay_failure_matrix.csv"
)
MANIFEST_PATH = (
    f"{DATA_ROOT}/covapie_reaction_transformation_overlay_manifest.json"
)
MODULE_PATH = (
    "src/covalent_ext/"
    "covapie_current11_reaction_transformation_evidence_overlay_contract_v1.py"
)
CHECKER_PATH = (
    "scripts/"
    "check_covapie_current11_reaction_transformation_evidence_overlay_contract_v1.py"
)
TEST_PATH = (
    "tests/"
    "test_covapie_current11_reaction_transformation_evidence_overlay_contract_v1.py"
)
GUIDE_PATH = (
    "docs/covapie_current11_reaction_transformation_evidence_overlay_contract_v1_guide.md"
)
CANDIDATE_PATHS = tuple(sorted((
    MODULE_PATH,
    CHECKER_PATH,
    TEST_PATH,
    GUIDE_PATH,
    SOURCE_INVENTORY_PATH,
    FIELD_CONTRACT_PATH,
    GAP_MATRIX_PATH,
    FAILURE_MATRIX_PATH,
    MANIFEST_PATH,
)))
ARTIFACT_PATHS = (
    SOURCE_INVENTORY_PATH,
    FIELD_CONTRACT_PATH,
    GAP_MATRIX_PATH,
    FAILURE_MATRIX_PATH,
    MANIFEST_PATH,
)

WORKSPACE_NAME = "current11-family-rule-approval-v1"
WORKSPACE_TARGET = ".current11-family-rule-approval-v1.object-jv1g5u8t"
WORKSPACE_IDENTITY = {
    "canonical_st_dev": 49,
    "canonical_st_ino": 177964064880,
    "object_st_dev": 49,
    "object_st_ino": 177964064865,
    "object_mode": "0755",
}
WORKSPACE_SHA256 = {
    "README.md": "937549dd849dc7ca6bd3f67bad45f4620eedc8658afda3406e939a0b934b7a65",
    "family_rule_approval_worklist.csv": "9a85c03384a09620a1c168b023d3a1de2ebb1fed57589e55449ec1672d6c3add",
    "family_rule_candidate_evidence.json": "e0e3e4f2a8e30eea630756579d59fcde7c4ca3fe8dc36e86f6405bc79f3b16d1",
    "sample_support_evidence.csv": "efff4ad3e51c4bbbd043db53483db8496e16c20f29a252aef5ce947b37eb1169",
    "review_package_manifest.json": "538bf50d3989f4629a4a5b2b709df322789b2e9f892260408817f4ac11416d91",
}
DOSSIER_RELATIVE = (
    "manual-review-aids/current11-family-rule-approval-v1/"
    f"{PARENT_REVIEW_UNIT_ID}"
)
DOSSIER_IDENTITY = {"st_dev": 49, "st_ino": 177964065463, "mode": "0755"}
DOSSIER_SHA256 = {
    "README.md": "0e03596699e9389f5e867b4999361d846cff2b207ee0430be070ec831df17fa9",
    "dossier_manifest.json": "842585ab0eb2209933c02f2337ea602a06b463fba265c499fd8c6d5e5f2b727b",
    "frozen_review_unit_summary.json": "18a63b5c8e85e25c5d16eae9b08b7fdb9ba8b64be63ab6947636919346b63041",
    "candidate_local_graph.svg": "2daad45b6d2b1b35bdfb38ddfc1f5cb38cdf58eabbe31c591273714a6dafdc96",
    "sample_support_evidence.csv": "2a83a71a313a8f0d542ec84ea46a8a4e1943b327181b7a2227fdbee199062c35",
    "human_review_questionnaire.md": "3e451ce14a89652e179fa2a0cde83daf617240fa4043b9b9674e307b10527eda",
}

FROZEN_FIELDS = (
    "transformation_review_unit_id",
    "parent_review_unit_id",
    "reaction_family_id",
    "warhead_rule_id",
    "sample_index_row_ids_json",
    "sample_count",
    "target_residue_types_json",
    "target_residue_reactive_atom_name",
    "ligand_reactive_atom_ids_by_sample_json",
    "effective_attachment_boundaries_by_sample_json",
    "candidate_local_graph_rule_sha256",
    "candidate_formed_bond_order",
    "pre_reaction_center_bond_order_sum",
    "conditional_post_bond_order_sum_if_internal_bonds_unchanged",
    "post_reaction_authority_status",
    "schema_gap_detected",
)
FUTURE_FIELDS = (
    "reviewed_transformation_version",
    "reviewed_transformation_class",
    "reviewed_transformation_scope",
    "reviewed_atom_map_contract_json",
    "reviewed_attachment_boundary_map_numbers_by_sample_json",
    "reviewed_pre_atom_state_contract_json",
    "reviewed_post_atom_state_contract_json",
    "reviewed_formed_edges_json",
    "reviewed_broken_edges_json",
    "reviewed_bond_order_changes_json",
    "reviewed_formal_charge_changes_json",
    "reviewed_protonation_transfer_contract_json",
    "reviewed_leaving_group_contract_json",
    "reviewed_reversibility_semantics",
    "reviewed_post_state_evidence_type",
    "reviewed_post_state_evidence_source",
    "reviewed_post_state_evidence_sha256",
    "transformation_identity_explicitly_attested",
    "transformation_full_semantics_explicitly_attested",
    "transformation_review_decision",
    "review_rationale",
    "review_notes",
    "reviewer_id",
    "attestor_id",
    "review_completed",
)
ALL_FIELDS = FROZEN_FIELDS + FUTURE_FIELDS
TRANSFORMATION_CLASSES = (
    "formed_bond_only",
    "formed_bond_plus_internal_bond_order_change",
    "formed_bond_plus_broken_bond",
    "formed_bond_plus_broken_and_bond_order_change",
    "other_explicit_graph_delta",
)
TRANSFORMATION_SCOPES = (
    "shared_exact2_sample_transformation",
    "sample_specific_transformations",
)
REVERSIBILITY_VALUES = ("reversible", "irreversible", "not_claimed")
POST_STATE_EVIDENCE_TYPES = (
    "curated_post_graph",
    "curated_graph_delta",
    "formally_attested_equivalent_contract",
)
TRANSFORMATION_DECISIONS = (
    "approve_reaction_transformation_contract",
    "revise_reaction_transformation_contract",
    "quarantine_reaction_transformation_contract",
)
BOOL_STRINGS = ("true", "false")
FIELD_SCOPES = (
    "frozen_identity",
    "frozen_candidate_evidence",
    "frozen_gap_fact",
    "future_transformation_structure",
    "future_transformation_state",
    "future_evidence_authority",
    "future_attestation",
    "future_decision",
    "future_provenance",
)
AUTHORITY_SCOPES = (
    "formal_pre_reaction_graph",
    "formal_reactive_atom_identity",
    "formal_covalent_atom_pair_identity",
    "formal_pair_geometry_only",
    "formal_boundary_partition",
    "candidate_local_graph",
    "candidate_reaction_delta",
    "formal_review_schema",
    "non_authoritative_review_aid",
)

HISTORICAL_HUMAN_FIELDS = (
    "reviewed_reaction_family_version",
    "reviewed_reaction_family_semantic_name",
    "reviewed_reaction_family_structural_basis",
    "reaction_family_identity_explicitly_attested",
    "reaction_family_review_decision",
    "reviewed_warhead_rule_version",
    "reviewed_warhead_rule_semantic_name",
    "reviewed_target_residue_types",
    "reviewed_target_residue_reactive_atom_name",
    "reviewed_warhead_smarts",
    "reviewed_ligand_reactive_atom_map_number",
    "reviewed_warhead_atom_map_numbers",
    "reviewed_warhead_attachment_atom_map_number",
    "reviewed_expected_pre_reaction_bond_orders",
    "reviewed_allowed_formal_charge_pattern",
    "reviewed_allowed_match_count",
    "reviewed_priority",
    "reviewed_leaving_group_contract",
    "reviewed_formed_bond_order",
    "reviewed_ambiguity_policy",
    "reviewed_tie_policy",
    "warhead_rule_identity_explicitly_attested",
    "warhead_rule_full_semantics_explicitly_attested",
    "approved_structural_pattern_attested",
    "warhead_rule_review_decision",
    "review_rationale",
    "review_notes",
    "reviewer_id",
    "attestor_id",
    "review_completed",
)

SOURCE_INVENTORY_COLUMNS = (
    "evidence_id",
    "source_namespace",
    "source_commit_or_direct_producer",
    "source_path",
    "source_sha256",
    "authority_scope",
    "used_fields",
    "authoritative_for_transformation",
    "lineage_note",
    "verified",
)
FIELD_CONTRACT_COLUMNS = (
    "field_order_0based",
    "field_name",
    "field_scope",
    "value_type",
    "cardinality",
    "frozen",
    "human_or_authority_fillable",
    "initial_value",
    "prefilled",
    "allowed_values",
    "required_for_approval",
    "current_coverage",
    "semantic_note",
    "verified",
)
GAP_MATRIX_COLUMNS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_identity",
    "parent_review_unit_id",
    "transformation_review_unit_id",
    "reaction_family_id",
    "warhead_rule_id",
    "ligand_reactive_atom_id",
    "target_residue_atom",
    "candidate_local_graph_rule_sha256",
    "pre_reaction_center_bond_order_sum",
    "candidate_formed_bond_order",
    "conditional_post_bond_order_sum_if_internal_bonds_unchanged",
    "effective_boundary_cardinality",
    "pre_reaction_graph_authority",
    "covalent_atom_pair_authority",
    "pair_geometry_authority",
    "post_reaction_graph_authority",
    "post_internal_bond_delta_authority",
    "post_formal_charge_authority",
    "post_protonation_authority",
    "complete_atom_map_contract_available",
    "plural_attachment_map_contract_available",
    "current_schema_coverage",
    "family_identity_evidence_ready_for_human_decision",
    "complete_rule_evidence_ready_for_human_decision",
    "blocking_reasons",
    "verified",
)
FAILURE_MATRIX_COLUMNS = (
    "case_id",
    "failure_case",
    "mutation_signature",
    "validator_target",
    "test_node_id",
    "expected_error",
    "fails_closed",
    "verified",
)

BLOCKING_REASONS = (
    "approved_structural_pattern_missing",
    "complete_atom_mapping_missing",
    "plural_attachment_mapping_missing",
    "post_internal_bond_delta_missing",
    "post_formal_charge_semantics_missing",
    "post_protonation_semantics_missing",
    "conditional_center_bond_order_conflict_unresolved",
    "reaction_transformation_schema_gap",
)


@dataclass(frozen=True)
class EvidenceSource:
    evidence_id: str
    namespace: str
    producer: str
    path: str
    sha256: str
    authority_scope: str
    used_fields: str
    authoritative_for_transformation: bool
    lineage_note: str


def _source(
    evidence_id: str,
    namespace: str,
    producer: str,
    path: str,
    sha256: str,
    scope: str,
    used_fields: str,
    note: str,
) -> EvidenceSource:
    return EvidenceSource(
        evidence_id,
        namespace,
        producer,
        path,
        sha256,
        scope,
        used_fields,
        False,
        note,
    )


REVIEW_PACKAGE_EXACT9 = (
    ("R01", "data/derived/covalent_small/covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1/covapie_family_rule_review_unit_matrix.csv", "1d1a61aecd983b156ac97059a087237fb36fc630b5df77fc8a03b1d2ab881d2b"),
    ("R02", "data/derived/covalent_small/covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1/covapie_review_package_failure_matrix.csv", "d8706c5f82f6d9e3c4c9d6d8617d7034f2175d76eb31f4f84ffa6eb4de6733bb"),
    ("R03", "data/derived/covalent_small/covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1/covapie_review_package_field_contract.csv", "9b277e2cdc6bfd066d067c6ff9af16c5b8b5ffe51cfcb5080ab83966d0538989"),
    ("R04", "data/derived/covalent_small/covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1/covapie_review_package_manifest.json", "4051ad07b0bcf934533bde03a064fd84ab3d6de30ab1413988a57ed75ca933bb"),
    ("R05", "data/derived/covalent_small/covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1/covapie_review_package_source_inventory.csv", "70ee45efbbe2b9076ce27ef39aaab934f2456ab1c6c8df5b0b68ceb0e8949304"),
    ("R06", "docs/covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1_guide.md", "7c45325c588cc1187be05d26391e594b78e6e4c62852c11205b78ea921def44d"),
    ("R07", "scripts/materialize_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1.py", "454dee10a5558e904f2313f4923668d3ee6b762bc92857278e0e0b961438b60f"),
    ("R08", "src/covalent_ext/covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1.py", "e395ef8730d7cfff756ec87f8d724ae8ff976426be41fbd7e35af37cad7230df"),
    ("R09", "tests/test_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1.py", "e5e8dec283ea32c315f998672ed5f505db4bd88adf62d2ee9dce04d590328158"),
)


SOURCE_EVIDENCE = tuple(
    _source(
        evidence_id,
        "git_object",
        REVIEW_PACKAGE_COMMIT,
        path,
        digest,
        "formal_review_schema",
        "review_package_exact9",
        "formal review-package candidate tree; no post-state authority",
    )
    for evidence_id, path, digest in REVIEW_PACKAGE_EXACT9
) + (
    _source("B01", "git_object", "2e07b7b094e2dccc69eaf29b5f51db0f9af2e81b", "data/derived/covalent_small/covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1/covapie_current11_family_rule_authority_binding_matrix.csv", "7064c1d0153ba1399bfdae8affcf21ead3f27e8a933987cd025ba5101a92bb61", "formal_review_schema", "binding_conclusion;sample_identity", "formal binding matrix is not transformation authority"),
    _source("B02", "git_object", "2e07b7b094e2dccc69eaf29b5f51db0f9af2e81b", "data/derived/covalent_small/covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1/covapie_family_and_warhead_rule_authority_registry.csv", "4899d4664acf45d5ee90283e7977d62385b3a70fe41e082f4d060388be7e106b", "formal_review_schema", "family_id;rule_id;authority_status", "binding registry"),
    _source("B03", "git_object", "2e07b7b094e2dccc69eaf29b5f51db0f9af2e81b", "data/derived/covalent_small/covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1/covapie_family_rule_binding_source_inventory.csv", "9e1533d8135d253b3360954b218f0219c56bc21aee424b4fce7ba8bc2672eae7", "formal_review_schema", "binding_source_lineage", "binding source inventory"),
    _source("B04", "git_object", "2e07b7b094e2dccc69eaf29b5f51db0f9af2e81b", "data/derived/covalent_small/covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1/covapie_family_rule_authority_binding_manifest.json", "0a6f6228e6397d3ccaef87a93a8c45dcab5e3c505cf0091a08c2bec335712dcc", "formal_review_schema", "binding_manifest", "binding predecessor manifest"),
    _source("A01", "git_object", "0c8d1d10260a028360357b8c309f22676fc81645", "data/derived/covalent_small/covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1/covapie_current11_cys_sg_candidate_assignment_authority.csv", "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9", "formal_reactive_atom_identity", "sample_ids;pdb_ids;ligand_ids;C21;CYS:SG", "candidate assignment identity evidence"),
    _source("G01", "git_object", "dc1222503dcec83220a28df2abdae898a0855864", "data/derived/covalent_small/covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1/covapie_cys_sg_warhead_rule_registry.csv", "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309", "candidate_local_graph", "canonical_local_graph_rule_json;formed_bond_order", "candidate graph is not an approved structural pattern"),
    _source("G02", "git_object", "dc1222503dcec83220a28df2abdae898a0855864", "data/derived/covalent_small/covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1/covapie_cys_sg_reaction_family_registry.csv", "230dc6da03beee55e53df75cba887151c23b703e10dce18de4ff6304d05b6353", "candidate_reaction_delta", "candidate_family;mechanism_not_claimed", "candidate reaction family registry"),
    _source("G03", "git_object", "dc1222503dcec83220a28df2abdae898a0855864", "data/derived/covalent_small/covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1/covapie_current11_reaction_family_and_warhead_rule_design_matrix.csv", "24ae0fbd2dc1454574d9ed17145ba71d3b3132ffecfb84a1a831eceb77efab03", "formal_pre_reaction_graph", "parent_local_bonds_json;observed_local_bonds_json", "pre-reaction local graph only"),
    _source("P01", "git_object", "68c5ca5cf1ce5b20be5db9ce0b37e10830c09288", "data/derived/covalent_small/covapie_current11_observed_to_parent_atom_projection_authority_v1/covapie_current11_observed_to_parent_atom_mapping_authority.csv", "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e", "formal_pre_reaction_graph", "observed_to_parent_atom_mapping", "observed-to-parent identity projection"),
    _source("P02", "git_object", "68c5ca5cf1ce5b20be5db9ce0b37e10830c09288", "data/derived/covalent_small/covapie_current11_observed_to_parent_atom_projection_authority_v1/covapie_current11_parent_and_observed_projected_bond_authority.csv", "bd31b7c074c3d4226c26bfe0210b9c3460f38c5087f1157b1167749f91bfffe0", "formal_pre_reaction_graph", "projected_parent_and_observed_bonds", "pre-reaction bond authority"),
    _source("C01", "git_object", "e5563ed50db6e56cbdfb6cc629e5eb4fe9137edf", "data/derived/covalent_small/covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1/covapie_atom_pair_atom_table_mapping_validation_matrix.csv", "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45", "formal_covalent_atom_pair_identity", "atom_table_mapping", "exact identity mapping without transformation semantics"),
    _source("C02", "git_object", "e5563ed50db6e56cbdfb6cc629e5eb4fe9137edf", "data/derived/covalent_small/covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1/covapie_atom_pair_canonical_record_validation_matrix.csv", "c756e6ce601bad1d10cfba5cac6129f9f688d00451cc1d805edff938ccee6ca0", "formal_covalent_atom_pair_identity", "CYS_SG_to_C21_pair", "explicit pair identity is not bond-order or transformation authority"),
    _source("Y01", "git_object", "e6a2e0e4cd00efc4635f7fb9ee7bb2008220348e", "data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AYU_INA/ligand_residue_atom_pair_table.csv", "bf68477bccf748c347f4198f71fa95a65899f684a510b73d17ae9e566917bc5e", "formal_pair_geometry_only", "SG_C21_pair_distance", "geometry only; not bond order or transformation"),
    _source("Y02", "git_object", "e6a2e0e4cd00efc4635f7fb9ee7bb2008220348e", "data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AYW_IN3/ligand_residue_atom_pair_table.csv", "58148a7ea77024eee27f871d618d4e257d3649bfd6a420b2ea6d4050dbcffe8f", "formal_pair_geometry_only", "SG_C21_pair_distance", "geometry only; not bond order or transformation"),
    _source("U01", "sha_bound_formal_state", "51810f19e0bbb96171a7dd3aebd72ef08eda0200", "state://manual-review/covapie_current11_unified_effective_authority_view_v1.json", "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774", "formal_boundary_partition", "Exact2_effective_attachment_boundaries", "formal boundary partition only"),
) + tuple(
    _source(
        f"W{index:02d}",
        "sha_bound_formal_state",
        REVIEW_PACKAGE_COMMIT,
        f"state://manual-review/{WORKSPACE_NAME}/{name}",
        digest,
        "formal_review_schema",
        "formal_30_field_review_contract" if name == "family_rule_approval_worklist.csv" else "formal_review_package_exact5",
        "formal review workspace; no transformation authority",
    )
    for index, (name, digest) in enumerate(WORKSPACE_SHA256.items(), start=1)
) + tuple(
    _source(
        f"D{index:02d}",
        "non_authoritative_state_aid",
        "prepare_covapie_current11_family_rule_approval_review_unit_000001_dossier_v1",
        f"state-aid://{DOSSIER_RELATIVE}/{name}",
        digest,
        "non_authoritative_review_aid",
        "crosscheck_only",
        "non_authoritative_human_review_aid_crosscheck",
    )
    for index, (name, digest) in enumerate(DOSSIER_SHA256.items(), start=1)
)


FAILURE_SPECS = (
    ("X01", "source_commit_drift", "source_commit=substituted_sha", "source_inventory"),
    ("X02", "source_sha_drift", "source_sha256=substituted_sha", "source_inventory"),
    ("X03", "formal_workspace_identity_drift", "workspace_inode+=1", "state"),
    ("X04", "dossier_identity_drift", "dossier_inode+=1", "state"),
    ("X05", "parent_review_unit_drift", "parent_review_unit_id=substituted", "state"),
    ("X06", "reaction_family_id_drift", "reaction_family_id=substituted", "state"),
    ("X07", "warhead_rule_id_drift", "warhead_rule_id=substituted", "state"),
    ("X08", "exact2_sample_set_drift", "sample_deleted", "state"),
    ("X09", "ligand_reactive_atom_drift", "C21=C20", "state"),
    ("X10", "target_residue_atom_drift", "CYS:SG=CYS:CB", "state"),
    ("X11", "candidate_graph_sha_drift", "candidate_graph_sha=substituted", "state"),
    ("X12", "pre_bond_order_sum_drift", "pre_sum=3", "state"),
    ("X13", "conditional_post_sum_drift", "conditional_sum=4", "state"),
    ("X14", "post_authority_prematurely_present", "post_authority_status=present", "state"),
    ("X15", "schema_gap_changed_false", "schema_gap_detected=false", "state"),
    ("X16", "singular_attachment_mapping_accepted", "boundary_count=1", "future_contract"),
    ("X17", "pre_atom_state_contract_missing", "pre_atom_state=empty", "future_contract"),
    ("X18", "post_atom_state_contract_missing", "post_atom_state=empty", "future_contract"),
    ("X19", "formed_edge_contract_missing", "formed_edges=empty", "future_contract"),
    ("X20", "bond_order_change_unreviewed", "bond_order_changes=empty_string", "future_contract"),
    ("X21", "formal_charge_change_unreviewed", "formal_charge_changes=empty_string", "future_contract"),
    ("X22", "protonation_transfer_unreviewed", "protonation_contract=empty_string", "future_contract"),
    ("X23", "future_field_prefilled", "reviewed_transformation_version=v1", "field_contract"),
    ("X24", "decision_prefilled", "transformation_review_decision=approve", "field_contract"),
    ("X25", "approved_smarts_generated", "approved_smarts_generated=true", "state"),
    ("X26", "formal_worklist_or_authority_changed", "authority_changed=true", "state"),
    ("X27", "ready_for_training_true", "ready_for_training=true", "state"),
    ("X28", "valid_looking_witness_substitution", "artifact_sha256=substituted_valid_sha", "response"),
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_hex(value: object, length: int) -> bool:
    return (
        type(value) is str
        and len(value) == length
        and value == value.lower()
        and set(value) <= set("0123456789abcdef")
    )


def _canonical_json_bytes(value: object, *, pretty: bool = False) -> bytes:
    if pretty:
        text = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            indent=2,
        )
    else:
        text = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    return (text + "\n").encode("utf-8")


def _canonical_json_text(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    )


def _csv_bytes(
    fields: Sequence[str], rows: Sequence[Mapping[str, object]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(fields):
            raise ValueError(ERROR)
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _strict_csv(payload: bytes, fields: Sequence[str]) -> list[dict[str, str]]:
    try:
        if (
            type(payload) is not bytes
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
            or not payload.endswith(b"\n")
        ):
            raise ValueError(ERROR)
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if tuple(reader.fieldnames or ()) != tuple(fields):
            raise ValueError(ERROR)
        rows = list(reader)
        if any(None in row or tuple(row) != tuple(fields) for row in rows):
            raise ValueError(ERROR)
        if _csv_bytes(fields, rows) != payload:
            raise ValueError(ERROR)
        return rows
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _strict_json(payload: bytes, expected_type: type) -> Any:
    try:
        if (
            type(payload) is not bytes
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
            or not payload.endswith(b"\n")
        ):
            raise ValueError(ERROR)
        value = json.loads(payload)
        if type(value) is not expected_type:
            raise ValueError(ERROR)
        if _canonical_json_bytes(value, pretty=True) != payload:
            raise ValueError(ERROR)
        return value
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _run_git(repo_root: Path, args: Sequence[str], *, check: bool = True) -> bytes:
    try:
        result = subprocess.run(
            ("git", "-C", str(repo_root), *args),
            check=False,
            stdin=subprocess.DEVNULL,
            capture_output=True,
        )
    except OSError as error:
        raise ValueError(ERROR) from error
    if check and (result.returncode != 0 or result.stderr):
        raise ValueError(ERROR)
    return result.stdout


def _git_text(repo_root: Path, args: Sequence[str]) -> str:
    try:
        return _run_git(repo_root, args).decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(ERROR) from error


def _git_blob(repo_root: Path, commit: str, path: str) -> bytes:
    if not _is_hex(commit, 40) or path.startswith("/") or ".." in Path(path).parts:
        raise ValueError(ERROR)
    return _run_git(repo_root, ("show", f"{commit}:{path}"))


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ("git", "-C", str(repo_root), "merge-base", "--is-ancestor", ancestor, descendant),
        check=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
    )
    if result.stderr or result.returncode not in (0, 1):
        raise ValueError(ERROR)
    return result.returncode == 0


def _source_inventory_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for source in SOURCE_EVIDENCE:
        rows.append({
            "evidence_id": source.evidence_id,
            "source_namespace": source.namespace,
            "source_commit_or_direct_producer": source.producer,
            "source_path": source.path,
            "source_sha256": source.sha256,
            "authority_scope": source.authority_scope,
            "used_fields": source.used_fields,
            "authoritative_for_transformation": (
                "true" if source.authoritative_for_transformation else "false"
            ),
            "lineage_note": source.lineage_note,
            "verified": "true",
        })
    return tuple(rows)


def _frozen_initial_values() -> dict[str, str]:
    boundaries = {
        "samples": {
            SAMPLE_IDS[0]: [
                {
                    "boundary_bond_id": "C11|C16|single",
                    "boundary_bond_order": "single",
                    "nonwarhead_boundary_atom_id": "C11",
                    "warhead_attachment_atom_id": "C16",
                },
                {
                    "boundary_bond_id": "C33|C38|single",
                    "boundary_bond_order": "single",
                    "nonwarhead_boundary_atom_id": "C33",
                    "warhead_attachment_atom_id": "C38",
                },
            ],
            SAMPLE_IDS[1]: [
                {
                    "boundary_bond_id": "C11|C17|single",
                    "boundary_bond_order": "single",
                    "nonwarhead_boundary_atom_id": "C11",
                    "warhead_attachment_atom_id": "C17",
                },
                {
                    "boundary_bond_id": "CB'|CH'|single",
                    "boundary_bond_order": "single",
                    "nonwarhead_boundary_atom_id": "CB'",
                    "warhead_attachment_atom_id": "CH'",
                },
            ],
        }
    }
    return {
        "transformation_review_unit_id": TRANSFORMATION_REVIEW_UNIT_ID,
        "parent_review_unit_id": PARENT_REVIEW_UNIT_ID,
        "reaction_family_id": REACTION_FAMILY_ID,
        "warhead_rule_id": WARHEAD_RULE_ID,
        "sample_index_row_ids_json": _canonical_json_text(list(SAMPLE_IDS)),
        "sample_count": "2",
        "target_residue_types_json": _canonical_json_text(["CYS"]),
        "target_residue_reactive_atom_name": "SG",
        "ligand_reactive_atom_ids_by_sample_json": _canonical_json_text({
            "samples": {sample_id: "C21" for sample_id in SAMPLE_IDS}
        }),
        "effective_attachment_boundaries_by_sample_json": _canonical_json_text(
            boundaries
        ),
        "candidate_local_graph_rule_sha256": CANDIDATE_LOCAL_GRAPH_SHA256,
        "candidate_formed_bond_order": "single",
        "pre_reaction_center_bond_order_sum": "4",
        "conditional_post_bond_order_sum_if_internal_bonds_unchanged": "5",
        "post_reaction_authority_status": "absent",
        "schema_gap_detected": "true",
    }


_FIELD_METADATA: dict[str, tuple[str, str, str, str, str, str]] = {
    "transformation_review_unit_id": ("frozen_identity", "string", "exactly_one", "", "false", "overlay unit identity"),
    "parent_review_unit_id": ("frozen_identity", "string", "exactly_one", "", "false", "formal parent review unit"),
    "reaction_family_id": ("frozen_identity", "string", "exactly_one", "", "false", "candidate family identity"),
    "warhead_rule_id": ("frozen_identity", "string", "exactly_one", "", "false", "candidate rule identity"),
    "sample_index_row_ids_json": ("frozen_identity", "canonical_json", "exactly_two_samples", "", "false", "ordered Exact2 sample scope"),
    "sample_count": ("frozen_identity", "positive_integer", "exactly_one", "2", "false", "Exact2 cardinality"),
    "target_residue_types_json": ("frozen_candidate_evidence", "canonical_json", "nonempty_list", "", "false", "formal target residue type"),
    "target_residue_reactive_atom_name": ("frozen_candidate_evidence", "string", "exactly_one", "SG", "false", "formal target residue atom"),
    "ligand_reactive_atom_ids_by_sample_json": ("frozen_candidate_evidence", "canonical_json", "one_per_sample", "", "false", "formal ligand reactive atom identity"),
    "effective_attachment_boundaries_by_sample_json": ("frozen_candidate_evidence", "canonical_json", "per_sample_exact_two_boundaries", "", "false", "formal boundary partition; not transformation"),
    "candidate_local_graph_rule_sha256": ("frozen_candidate_evidence", "sha256", "exactly_one", "", "false", "candidate graph digest; not approved pattern"),
    "candidate_formed_bond_order": ("frozen_candidate_evidence", "normalized_bond_order", "exactly_one", "single", "false", "candidate SG-C formed bond order"),
    "pre_reaction_center_bond_order_sum": ("frozen_gap_fact", "nonnegative_integer", "exactly_one", "4", "false", "pre-state C-N single plus C-N single plus C-O double"),
    "conditional_post_bond_order_sum_if_internal_bonds_unchanged": ("frozen_gap_fact", "nonnegative_integer", "exactly_one", "5", "false", "conditional ledger only; no post-state claim"),
    "post_reaction_authority_status": ("frozen_gap_fact", "enum", "exactly_one", "absent", "false", "formal post-reaction authority is absent"),
    "schema_gap_detected": ("frozen_gap_fact", "boolean_string", "exactly_one", "true", "false", "formal review schema is insufficient"),
    "reviewed_transformation_version": ("future_transformation_structure", "string", "exactly_one", "", "true", "future reviewed contract version"),
    "reviewed_transformation_class": ("future_transformation_structure", "enum", "exactly_one", ";".join(TRANSFORMATION_CLASSES), "true", "class must agree with explicit graph delta"),
    "reviewed_transformation_scope": ("future_transformation_structure", "enum", "exactly_one", ";".join(TRANSFORMATION_SCOPES), "true", "shared or sample-specific transformation scope"),
    "reviewed_atom_map_contract_json": ("future_transformation_structure", "canonical_json", "all_samples", "", "true", "schema=atom_map_contract_v1; positive unique map numbers"),
    "reviewed_attachment_boundary_map_numbers_by_sample_json": ("future_transformation_structure", "canonical_json", "per_sample_exact_two_boundaries", "", "true", "schema=plural_attachment_boundary_map_v1; singular mapping is insufficient"),
    "reviewed_pre_atom_state_contract_json": ("future_transformation_state", "canonical_json", "all_mapped_atoms", "", "true", "schema=atom_state_contract_v1; pre state"),
    "reviewed_post_atom_state_contract_json": ("future_transformation_state", "canonical_json", "all_mapped_atoms", "", "true", "schema=atom_state_contract_v1; post state"),
    "reviewed_formed_edges_json": ("future_transformation_state", "canonical_json", "per_sample_explicit_list", "", "true", "map-number endpoints; formed SG-C edge required"),
    "reviewed_broken_edges_json": ("future_transformation_state", "canonical_json", "per_sample_explicit_list", "", "true", "explicit empty list differs from unreviewed empty string"),
    "reviewed_bond_order_changes_json": ("future_transformation_state", "canonical_json", "per_sample_explicit_list", "", "true", "map endpoints plus pre and post bond order"),
    "reviewed_formal_charge_changes_json": ("future_transformation_state", "canonical_json", "per_sample_explicit_list", "", "true", "map number plus pre and post formal charge"),
    "reviewed_protonation_transfer_contract_json": ("future_transformation_state", "canonical_json", "all_samples", "explicitly_attested;not_claimed", "true", "missing data must not become not_claimed"),
    "reviewed_leaving_group_contract_json": ("future_transformation_state", "canonical_json", "all_samples", "explicitly_attested;not_claimed", "true", "explicit reviewed leaving-group semantics"),
    "reviewed_reversibility_semantics": ("future_transformation_state", "enum", "exactly_one", ";".join(REVERSIBILITY_VALUES), "true", "no mechanism default"),
    "reviewed_post_state_evidence_type": ("future_evidence_authority", "enum", "exactly_one", ";".join(POST_STATE_EVIDENCE_TYPES), "true", "formal post-state evidence type"),
    "reviewed_post_state_evidence_source": ("future_evidence_authority", "string", "exactly_one", "", "true", "independent curated or formally attested source"),
    "reviewed_post_state_evidence_sha256": ("future_evidence_authority", "sha256", "exactly_one", "", "true", "SHA-bound post-state evidence"),
    "transformation_identity_explicitly_attested": ("future_attestation", "boolean_string", "exactly_one", ";".join(BOOL_STRINGS), "true", "must equal true for approval"),
    "transformation_full_semantics_explicitly_attested": ("future_attestation", "boolean_string", "exactly_one", ";".join(BOOL_STRINGS), "true", "must equal true for approval"),
    "transformation_review_decision": ("future_decision", "enum", "exactly_one", ";".join(TRANSFORMATION_DECISIONS), "true", "decision cannot be prefilled"),
    "review_rationale": ("future_provenance", "string", "exactly_one", "", "true", "required human rationale"),
    "review_notes": ("future_provenance", "string", "zero_or_one", "", "false", "optional notes"),
    "reviewer_id": ("future_provenance", "string", "exactly_one", "", "true", "reviewer provenance"),
    "attestor_id": ("future_provenance", "string", "exactly_one", "", "true", "attestor provenance"),
    "review_completed": ("future_provenance", "boolean_string", "exactly_one", ";".join(BOOL_STRINGS), "true", "must equal true for approval"),
}


def _field_contract_rows() -> tuple[dict[str, str], ...]:
    initial = _frozen_initial_values()
    rows = []
    for order, field in enumerate(ALL_FIELDS):
        scope, value_type, cardinality, allowed, required, note = _FIELD_METADATA[field]
        future = field in FUTURE_FIELDS
        rows.append({
            "field_order_0based": str(order),
            "field_name": field,
            "field_scope": scope,
            "value_type": value_type,
            "cardinality": cardinality,
            "frozen": "false" if future else "true",
            "human_or_authority_fillable": "true" if future else "false",
            "initial_value": "" if future else initial[field],
            "prefilled": "false",
            "allowed_values": allowed,
            "required_for_approval": required,
            "current_coverage": "missing" if future else "complete",
            "semantic_note": note,
            "verified": "true",
        })
    return tuple(rows)


def _gap_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for sample_id in SAMPLE_IDS:
        facts = SAMPLE_FACTS[sample_id]
        rows.append({
            "sample_index_row_id": sample_id,
            "pdb_id": facts["pdb_id"],
            "ligand_identity": facts["ligand_identity"],
            "parent_review_unit_id": PARENT_REVIEW_UNIT_ID,
            "transformation_review_unit_id": TRANSFORMATION_REVIEW_UNIT_ID,
            "reaction_family_id": REACTION_FAMILY_ID,
            "warhead_rule_id": WARHEAD_RULE_ID,
            "ligand_reactive_atom_id": "C21",
            "target_residue_atom": "CYS:SG",
            "candidate_local_graph_rule_sha256": CANDIDATE_LOCAL_GRAPH_SHA256,
            "pre_reaction_center_bond_order_sum": "4",
            "candidate_formed_bond_order": "single",
            "conditional_post_bond_order_sum_if_internal_bonds_unchanged": "5",
            "effective_boundary_cardinality": "2",
            "pre_reaction_graph_authority": "authoritative_resolved",
            "covalent_atom_pair_authority": "authoritative_resolved",
            "pair_geometry_authority": "geometry_only_not_bond_order_or_transformation",
            "post_reaction_graph_authority": "missing",
            "post_internal_bond_delta_authority": "missing",
            "post_formal_charge_authority": "missing",
            "post_protonation_authority": "missing",
            "complete_atom_map_contract_available": "false",
            "plural_attachment_map_contract_available": "false",
            "current_schema_coverage": "insufficient_for_complete_transformation_review",
            "family_identity_evidence_ready_for_human_decision": "true",
            "complete_rule_evidence_ready_for_human_decision": "false",
            "blocking_reasons": ";".join(BLOCKING_REASONS),
            "verified": "true",
        })
    return tuple(rows)


def _failure_rows() -> tuple[dict[str, str], ...]:
    return tuple({
        "case_id": case_id,
        "failure_case": name,
        "mutation_signature": mutation,
        "validator_target": target,
        "test_node_id": (
            "tests/test_covapie_current11_reaction_transformation_"
            f"evidence_overlay_contract_v1.py::test_failure_mutations_exact28[{case_id}]"
        ),
        "expected_error": ERROR,
        "fails_closed": "true",
        "verified": "true",
    } for case_id, name, mutation, target in FAILURE_SPECS)


def _manifest(expected_four: Mapping[str, bytes]) -> dict[str, object]:
    expected_names = ARTIFACT_PATHS[:-1]
    if tuple(expected_four) != expected_names:
        raise ValueError(ERROR)
    return {
        "schema_version": SCHEMA_VERSION,
        "base_commit": BASE_COMMIT,
        "review_package_commit": REVIEW_PACKAGE_COMMIT,
        "parent_review_unit_id": PARENT_REVIEW_UNIT_ID,
        "transformation_review_unit_id": TRANSFORMATION_REVIEW_UNIT_ID,
        "reaction_family_id": REACTION_FAMILY_ID,
        "warhead_rule_id": WARHEAD_RULE_ID,
        "sample_count": 2,
        "source_inventory_row_count": len(SOURCE_EVIDENCE),
        "field_contract_row_count": 41,
        "frozen_field_count": 16,
        "future_field_count": 25,
        "gap_matrix_row_count": 2,
        "failure_case_count": 28,
        "schema_gap_detected": True,
        "formal_post_reaction_authority_count": 0,
        "family_identity_evidence_ready_for_human_decision": True,
        "complete_rule_evidence_ready_for_human_decision": False,
        "post_reaction_internal_bond_order_authority": "absent",
        "post_reaction_formal_charge_authority": "absent",
        "post_reaction_protonation_authority": "absent",
        "candidate_valence_ledger_is_gap_signal_only": True,
        "candidate_valence_ledger_is_reaction_authority": False,
        "human_fields_prefilled": False,
        "approved_smarts_generated": False,
        "approval_decision_generated": False,
        "formal_worklist_modified": False,
        "authority_changed": False,
        "review_submission_compiled": False,
        "review_ingested": False,
        "authority_bundle_generated": False,
        "role_or_seed_generated": False,
        "tensor_materialized": False,
        "model_changed": False,
        "training_used": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "recommended_next_step": (
            "materialize_covapie_current11_unit_000001_reaction_"
            "transformation_evidence_acquisition_template_v1"
        ),
        "candidate_paths": list(CANDIDATE_PATHS),
        "evidence_sha256": {
            Path(path).name: _sha256(expected_four[path]) for path in expected_names
        },
    }


def _expected_artifacts() -> dict[str, bytes]:
    artifacts = {
        SOURCE_INVENTORY_PATH: _csv_bytes(
            SOURCE_INVENTORY_COLUMNS, _source_inventory_rows()
        ),
        FIELD_CONTRACT_PATH: _csv_bytes(
            FIELD_CONTRACT_COLUMNS, _field_contract_rows()
        ),
        GAP_MATRIX_PATH: _csv_bytes(GAP_MATRIX_COLUMNS, _gap_rows()),
        FAILURE_MATRIX_PATH: _csv_bytes(
            FAILURE_MATRIX_COLUMNS, _failure_rows()
        ),
    }
    artifacts[MANIFEST_PATH] = _canonical_json_bytes(
        _manifest(artifacts), pretty=True
    )
    return artifacts


def _source_by_id(evidence_id: str) -> EvidenceSource:
    matches = [source for source in SOURCE_EVIDENCE if source.evidence_id == evidence_id]
    if len(matches) != 1:
        raise ValueError(ERROR)
    return matches[0]


def _read_state_source(state_root: Path, source: EvidenceSource) -> bytes:
    if source.namespace == "sha_bound_formal_state":
        prefix = "state://"
    elif source.namespace == "non_authoritative_state_aid":
        prefix = "state-aid://"
    else:
        raise ValueError(ERROR)
    if not source.path.startswith(prefix):
        raise ValueError(ERROR)
    relative = Path(source.path[len(prefix):])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(ERROR)
    path = state_root / relative
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise ValueError(ERROR) from error
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
        raise ValueError(ERROR)
    return payload


def _validate_source_inventory(repo_root: Path, state_root: Path) -> None:
    ids = [source.evidence_id for source in SOURCE_EVIDENCE]
    if (
        len(ids) != len(set(ids))
        or set(source.authority_scope for source in SOURCE_EVIDENCE)
        - set(AUTHORITY_SCOPES)
        or any(source.authoritative_for_transformation for source in SOURCE_EVIDENCE)
        or any(
            source.authority_scope == "formal_post_reaction_transformation_authority"
            for source in SOURCE_EVIDENCE
        )
    ):
        raise ValueError(ERROR)
    for source in SOURCE_EVIDENCE:
        if not _is_hex(source.sha256, 64):
            raise ValueError(ERROR)
        if source.namespace == "git_object":
            if not _is_hex(source.producer, 40):
                raise ValueError(ERROR)
            payload = _git_blob(repo_root, source.producer, source.path)
        else:
            payload = _read_state_source(state_root, source)
        if _sha256(payload) != source.sha256:
            raise ValueError(ERROR)


def _validate_workspace(state_root: Path) -> dict[str, bytes]:
    canonical = state_root / "manual-review" / WORKSPACE_NAME
    object_directory = canonical.parent / WORKSPACE_TARGET
    try:
        canonical_meta = canonical.lstat()
        object_meta = object_directory.lstat()
        target = str(canonical.readlink())
        entries = tuple(sorted(object_directory.iterdir(), key=lambda path: path.name))
    except OSError as error:
        raise ValueError(ERROR) from error
    if (
        not stat.S_ISLNK(canonical_meta.st_mode)
        or target != WORKSPACE_TARGET
        or canonical_meta.st_dev != WORKSPACE_IDENTITY["canonical_st_dev"]
        or canonical_meta.st_ino != WORKSPACE_IDENTITY["canonical_st_ino"]
        or not stat.S_ISDIR(object_meta.st_mode)
        or object_directory.is_symlink()
        or object_meta.st_dev != WORKSPACE_IDENTITY["object_st_dev"]
        or object_meta.st_ino != WORKSPACE_IDENTITY["object_st_ino"]
        or f"{stat.S_IMODE(object_meta.st_mode):04o}" != WORKSPACE_IDENTITY["object_mode"]
        or tuple(path.name for path in entries) != tuple(sorted(WORKSPACE_SHA256))
    ):
        raise ValueError(ERROR)
    payloads: dict[str, bytes] = {}
    for path in entries:
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ValueError(ERROR) from error
        if (
            not stat.S_ISREG(metadata.st_mode)
            or path.is_symlink()
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or _sha256(payload) != WORKSPACE_SHA256[path.name]
        ):
            raise ValueError(ERROR)
        payloads[path.name] = payload
    return payloads


def _validate_dossier(state_root: Path) -> dict[str, bytes]:
    dossier = state_root / DOSSIER_RELATIVE
    try:
        metadata = dossier.lstat()
        entries = tuple(sorted(dossier.iterdir(), key=lambda path: path.name))
    except OSError as error:
        raise ValueError(ERROR) from error
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or dossier.is_symlink()
        or metadata.st_dev != DOSSIER_IDENTITY["st_dev"]
        or metadata.st_ino != DOSSIER_IDENTITY["st_ino"]
        or f"{stat.S_IMODE(metadata.st_mode):04o}" != DOSSIER_IDENTITY["mode"]
        or tuple(path.name for path in entries) != tuple(sorted(DOSSIER_SHA256))
    ):
        raise ValueError(ERROR)
    payloads: dict[str, bytes] = {}
    for path in entries:
        try:
            child = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ValueError(ERROR) from error
        if (
            not stat.S_ISREG(child.st_mode)
            or path.is_symlink()
            or stat.S_IMODE(child.st_mode) != 0o644
            or _sha256(payload) != DOSSIER_SHA256[path.name]
        ):
            raise ValueError(ERROR)
        payloads[path.name] = payload
    questionnaire = payloads["human_review_questionnaire.md"].decode("utf-8")
    lines = questionnaire.splitlines()
    if any(lines.count(f"{field}:") != 1 for field in HISTORICAL_HUMAN_FIELDS):
        raise ValueError(ERROR)
    return payloads


def _csv_rows_unbound(payload: bytes) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(ERROR)
        rows = list(reader)
        if any(None in row for row in rows):
            raise ValueError(ERROR)
        return rows
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _load_formal_state(
    repo_root: Path,
    state_root: Path,
    workspace: Mapping[str, bytes],
    dossier: Mapping[str, bytes],
) -> dict[str, Any]:
    try:
        worklist = _csv_rows_unbound(workspace["family_rule_approval_worklist.csv"])
        if len(worklist) != 7:
            raise ValueError(ERROR)
        unit_rows = [row for row in worklist if row.get("review_unit_id") == PARENT_REVIEW_UNIT_ID]
        if len(unit_rows) != 1:
            raise ValueError(ERROR)
        unit = unit_rows[0]
        if any(field not in unit for field in HISTORICAL_HUMAN_FIELDS):
            raise ValueError(ERROR)
        if any(row[field] != "" for row in worklist for field in HISTORICAL_HUMAN_FIELDS):
            raise ValueError(ERROR)
        if (
            unit["reaction_family_id"] != REACTION_FAMILY_ID
            or unit["warhead_rule_id"] != WARHEAD_RULE_ID
            or unit["sample_count"] != "2"
            or json.loads(unit["sample_index_row_ids"]) != list(SAMPLE_IDS)
            or unit["candidate_local_graph_rule_sha256"] != CANDIDATE_LOCAL_GRAPH_SHA256
            or unit["formed_bond_order"] != "single"
            or unit["approved_warhead_smarts_currently_available"] != "false"
            or unit["formal_equivalent_structural_contract_currently_available"] != "false"
        ):
            raise ValueError(ERROR)

        evidence = json.loads(workspace["family_rule_candidate_evidence.json"])
        if type(evidence) is not list or len(evidence) != 7:
            raise ValueError(ERROR)
        evidence_rows = [row for row in evidence if row.get("review_unit_id") == PARENT_REVIEW_UNIT_ID]
        if len(evidence_rows) != 1:
            raise ValueError(ERROR)
        candidate = evidence_rows[0]
        approval = candidate["current_approval_state"]
        if (
            candidate["approved_authority"] is not False
            or candidate["evidence_status"] != "candidate_supporting_evidence_only"
            or candidate["canonical_local_graph_rule_sha256"] != CANDIDATE_LOCAL_GRAPH_SHA256
            or approval["candidate_local_graph_is_approved_structural_pattern"] is not False
            or approval["formal_equivalent_structural_contract_currently_available"] is not False
        ):
            raise ValueError(ERROR)

        support = _csv_rows_unbound(workspace["sample_support_evidence.csv"])
        selected = [row for row in support if row.get("review_unit_id") == PARENT_REVIEW_UNIT_ID]
        if (
            len(selected) != 2
            or tuple(row["sample_index_row_id"] for row in selected) != SAMPLE_IDS
            or any(row["ligand_reactive_atom"] != "C21" for row in selected)
            or any(row["target_residue_atom"] != "CYS:SG" for row in selected)
            or any(row["effective_boundary_cardinality"] != "2" for row in selected)
            or any(row["sample_attests_full_family_or_rule_semantics"] != "false" for row in selected)
        ):
            raise ValueError(ERROR)

        assignment_source = _source_by_id("A01")
        assignments = _csv_rows_unbound(
            _git_blob(repo_root, assignment_source.producer, assignment_source.path)
        )
        assignment_rows = [
            row for row in assignments if row.get("sample_index_row_id") in SAMPLE_IDS
        ]
        if (
            tuple(row["sample_index_row_id"] for row in assignment_rows) != SAMPLE_IDS
            or any(row["candidate_reaction_family_id"] != REACTION_FAMILY_ID for row in assignment_rows)
            or any(row["candidate_warhead_rule_id"] != WARHEAD_RULE_ID for row in assignment_rows)
            or any(row["ligand_reactive_atom_name"] != "C21" for row in assignment_rows)
            or any(row["target_residue_atom_name"] != "SG" for row in assignment_rows)
            or any(row["target_residue_name"] != "CYS" for row in assignment_rows)
            or [(row["pdb_id"], row["ligand_comp_id"]) for row in assignment_rows]
            != [("1AYU", "INA"), ("1AYW", "IN3")]
        ):
            raise ValueError(ERROR)

        rule_source = _source_by_id("G01")
        rule_rows = _csv_rows_unbound(
            _git_blob(repo_root, rule_source.producer, rule_source.path)
        )
        rules = [row for row in rule_rows if row.get("warhead_rule_id") == WARHEAD_RULE_ID]
        if len(rules) != 1:
            raise ValueError(ERROR)
        rule = rules[0]
        graph = json.loads(rule["canonical_local_graph_rule_json"])
        order_values = {"single": 1, "double": 2, "triple": 3, "aromatic": 1.5}
        local_orders = [bond["normalized_bond_order"] for bond in graph["local_bonds"]]
        pre_sum = sum(order_values[order] for order in local_orders)
        if (
            rule["canonical_local_graph_rule_sha256"] != CANDIDATE_LOCAL_GRAPH_SHA256
            or rule["formed_bond_order"] != "single"
            or rule["approved"] != "false"
            or rule["approved_warhead_smarts"] != ""
            or local_orders != ["single", "single", "double"]
            or pre_sum != 4
        ):
            raise ValueError(ERROR)

        design_source = _source_by_id("G03")
        design_rows = _csv_rows_unbound(
            _git_blob(repo_root, design_source.producer, design_source.path)
        )
        designs = [row for row in design_rows if row.get("sample_index_row_id") in SAMPLE_IDS]
        if len(designs) != 2:
            raise ValueError(ERROR)
        for row in designs:
            bonds = json.loads(row["parent_local_bonds_json"])
            if (
                row["ligand_reactive_atom_name"] != "C21"
                or [bond["normalized_bond_order"] for bond in bonds]
                != ["single", "single", "double"]
                or row["ready_for_training"] != "false"
            ):
                raise ValueError(ERROR)

        pair_source = _source_by_id("C02")
        pair_rows = _csv_rows_unbound(
            _git_blob(repo_root, pair_source.producer, pair_source.path)
        )
        pairs = [row for row in pair_rows if row.get("sample_index_row_id") in SAMPLE_IDS]
        if (
            len(pairs) != 2
            or any(row["residue_comp_id"] != "CYS" for row in pairs)
            or any(row["residue_atom_name"] != "SG" for row in pairs)
            or any(row["ligand_atom_name"] != "C21" for row in pairs)
            or any(row["canonical_record_valid"] != "true" for row in pairs)
            or any(row["explicit_authority_preserved"] != "true" for row in pairs)
        ):
            raise ValueError(ERROR)

        for evidence_id, pdb_id, ligand in (("Y01", "1AYU", "INA"), ("Y02", "1AYW", "IN3")):
            geometry_source = _source_by_id(evidence_id)
            geometry = _csv_rows_unbound(
                _git_blob(repo_root, geometry_source.producer, geometry_source.path)
            )
            if (
                len(geometry) != 1
                or geometry[0]["pdb_id"] != pdb_id
                or geometry[0]["expected_het_id"] != ligand
                or geometry[0]["residue_atom_name"] != "SG"
                or geometry[0]["ligand_atom_name"] != "C21"
                or geometry[0]["covalent_bond_atom_pair"] != "SG--C21"
            ):
                raise ValueError(ERROR)

        unified_payload = _read_state_source(state_root, _source_by_id("U01"))
        unified = json.loads(unified_payload)
        boundary_rows = [
            row for row in unified["effective_authority_records"]
            if row.get("sample_index_row_id") in SAMPLE_IDS
        ]
        expected_boundaries = json.loads(
            _frozen_initial_values()["effective_attachment_boundaries_by_sample_json"]
        )["samples"]
        actual_boundaries: dict[str, list[dict[str, str]]] = {}
        for row in boundary_rows:
            record = row["effective_authority_record"]
            sample_id = row["sample_index_row_id"]
            actual_boundaries[sample_id] = record["reviewed_boundary_records"]
            if (
                row["effective_boundary_cardinality"] != 2
                or row["effective_authority_namespace"]
                != "exact_two_boundaries_multi_boundary_v1"
                or record["exact_two_attachment_boundaries_authority_available"] is not True
                or len(record["reviewed_boundary_records"]) != 2
            ):
                raise ValueError(ERROR)
        if actual_boundaries != expected_boundaries:
            raise ValueError(ERROR)

        dossier_manifest = json.loads(dossier["dossier_manifest.json"])
        if (
            dossier_manifest["review_unit_id"] != PARENT_REVIEW_UNIT_ID
            or dossier_manifest["reaction_family_id"] != REACTION_FAMILY_ID
            or dossier_manifest["warhead_rule_id"] != WARHEAD_RULE_ID
            or dossier_manifest["human_answers_prefilled"] is not False
            or dossier_manifest["formal_worklist_modified"] is not False
            or dossier_manifest["approved_smarts_generated"] is not False
            or dossier_manifest["approval_decision_generated"] is not False
            or dossier_manifest["authority_changed"] is not False
            or dossier_manifest["ready_for_training"] is not False
        ):
            raise ValueError(ERROR)

        return {
            "parent_review_unit_id": PARENT_REVIEW_UNIT_ID,
            "reaction_family_id": REACTION_FAMILY_ID,
            "warhead_rule_id": WARHEAD_RULE_ID,
            "sample_ids": list(SAMPLE_IDS),
            "ligand_reactive_atoms": {sample_id: "C21" for sample_id in SAMPLE_IDS},
            "target_residue_atom": "CYS:SG",
            "candidate_graph_sha256": CANDIDATE_LOCAL_GRAPH_SHA256,
            "pre_bond_order_sum": int(pre_sum),
            "conditional_post_sum": int(pre_sum) + 1,
            "post_authority_status": "absent",
            "schema_gap_detected": True,
            "boundary_counts": {sample_id: 2 for sample_id in SAMPLE_IDS},
            "workspace_inode": WORKSPACE_IDENTITY["canonical_st_ino"],
            "dossier_inode": DOSSIER_IDENTITY["st_ino"],
            "approved_smarts_generated": False,
            "approval_decision_generated": False,
            "formal_worklist_modified": False,
            "authority_changed": False,
            "ready_for_training": False,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _validate_artifacts(repo_root: Path) -> tuple[dict[str, bytes], dict[str, object]]:
    expected = _expected_artifacts()
    actual: dict[str, bytes] = {}
    for path in ARTIFACT_PATHS:
        candidate = repo_root / path
        try:
            metadata = candidate.lstat()
            payload = candidate.read_bytes()
        except OSError as error:
            raise ValueError(ERROR) from error
        if (
            not stat.S_ISREG(metadata.st_mode)
            or candidate.is_symlink()
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
            or payload != expected[path]
        ):
            raise ValueError(ERROR)
        actual[path] = payload
    source_rows = _strict_csv(actual[SOURCE_INVENTORY_PATH], SOURCE_INVENTORY_COLUMNS)
    field_rows = _strict_csv(actual[FIELD_CONTRACT_PATH], FIELD_CONTRACT_COLUMNS)
    gap_rows = _strict_csv(actual[GAP_MATRIX_PATH], GAP_MATRIX_COLUMNS)
    failure_rows = _strict_csv(actual[FAILURE_MATRIX_PATH], FAILURE_MATRIX_COLUMNS)
    manifest = _strict_json(actual[MANIFEST_PATH], dict)
    if (
        len(source_rows) != len(SOURCE_EVIDENCE)
        or len(field_rows) != 41
        or len(gap_rows) != 2
        or len(failure_rows) != 28
        or manifest != _manifest({path: actual[path] for path in ARTIFACT_PATHS[:-1]})
        or sum(
            row["authority_scope"] == "formal_post_reaction_transformation_authority"
            for row in source_rows
        ) != 0
    ):
        raise ValueError(ERROR)
    return actual, manifest


_LIFECYCLE_FIELDS = (
    "origin_main",
    "ahead",
    "behind",
    "lifecycle_profile",
    "formal_candidate_commit",
)


def _collect_live_identity(repo_root: Path, path: str) -> dict[str, object]:
    candidate = repo_root / path
    try:
        metadata = candidate.lstat()
    except OSError as error:
        raise ValueError(ERROR) from error
    if not stat.S_ISREG(metadata.st_mode) or candidate.is_symlink():
        raise ValueError(ERROR)
    blob = _git_text(
        repo_root, ("hash-object", "--no-filters", "--", path)
    ).strip()
    line = _git_text(repo_root, ("ls-files", "--stage", "--", path)).strip()
    if not _is_hex(blob, 40):
        raise ValueError(ERROR)
    if line:
        metadata_text, listed = line.split("\t", 1)
        mode, index_blob, stage = metadata_text.split()
        if listed != path or stage != "0" or not _is_hex(index_blob, 40):
            raise ValueError(ERROR)
        return {
            "tracked": True,
            "mode": mode,
            "index_blob": index_blob,
            "blob": blob,
        }
    return {
        "tracked": False,
        "mode": f"100{stat.S_IMODE(metadata.st_mode):03o}",
        "blob": blob,
    }


def _collect_lifecycle(repo_root: Path) -> dict[str, object]:
    head = _git_text(repo_root, ("rev-parse", "HEAD")).strip()
    origin = _git_text(
        repo_root, ("rev-parse", "refs/remotes/origin/main")
    ).strip()
    ahead_text, behind_text = _git_text(
        repo_root,
        ("rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"),
    ).split()
    revisions = set(
        _git_text(repo_root, ("rev-list", f"{BASE_COMMIT}..{head}")).splitlines()
    )
    revisions.update(
        _git_text(repo_root, ("rev-list", f"{BASE_COMMIT}..{origin}")).splitlines()
    )
    path_commits: list[dict[str, object]] = []
    for commit in sorted(revisions):
        status_lines = _git_text(
            repo_root,
            (
                "diff-tree",
                "--root",
                "--no-commit-id",
                "--name-status",
                "-r",
                commit,
            ),
        ).splitlines()
        statuses = {
            parts[1]: parts[0]
            for parts in (line.split("\t") for line in status_lines)
            if len(parts) == 2
        }
        if not set(statuses).intersection(CANDIDATE_PATHS):
            continue
        modes: dict[str, str] = {}
        blobs: dict[str, str] = {}
        for path in CANDIDATE_PATHS:
            line = _git_text(repo_root, ("ls-tree", commit, "--", path)).strip()
            if line:
                metadata_text, listed = line.split("\t", 1)
                mode, kind, blob = metadata_text.split()
                if listed != path or kind != "blob":
                    raise ValueError(ERROR)
                modes[path] = mode
                blobs[path] = blob
        path_commits.append({
            "commit": commit,
            "parents": _git_text(
                repo_root, ("show", "-s", "--format=%P", commit)
            ).split(),
            "subject": _git_text(
                repo_root, ("show", "-s", "--format=%s", commit)
            ).strip(),
            "changed_paths": tuple(sorted(statuses)),
            "changed_statuses": {path: statuses[path] for path in sorted(statuses)},
            "path_modes": modes,
            "path_blobs": blobs,
            "ancestor_head": _is_ancestor(repo_root, commit, head),
            "ancestor_origin": _is_ancestor(repo_root, commit, origin),
        })
    tracked = tuple(sorted(
        _git_text(repo_root, ("diff", "--name-only")).splitlines()
    ))
    staged = tuple(sorted(
        _git_text(repo_root, ("diff", "--cached", "--name-only")).splitlines()
    ))
    untracked = tuple(sorted(
        _git_text(
            repo_root, ("ls-files", "--others", "--exclude-standard")
        ).splitlines()
    ))
    porcelain = tuple(sorted(
        _git_text(
            repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
        ).splitlines()
    ))
    return {
        "head": head,
        "origin": origin,
        "ahead": int(ahead_text),
        "behind": int(behind_text),
        "branch": _git_text(repo_root, ("branch", "--show-current")).strip(),
        "base_ancestor_head": _is_ancestor(repo_root, BASE_COMMIT, head),
        "base_ancestor_origin": _is_ancestor(repo_root, BASE_COMMIT, origin),
        "tracked": tracked,
        "staged": staged,
        "untracked": untracked,
        "porcelain": porcelain,
        "path_commits": path_commits,
        "live_paths": {
            path: _collect_live_identity(repo_root, path) for path in CANDIDATE_PATHS
        },
    }


def _derive_lifecycle(facts: object) -> dict[str, object]:
    try:
        if type(facts) is not dict:
            raise ValueError(ERROR)
        if (
            facts["branch"] != BRANCH
            or facts["base_ancestor_head"] is not True
            or facts["base_ancestor_origin"] is not True
            or type(facts["path_commits"]) is not list
            or len(facts["path_commits"]) > 1
            or type(facts["porcelain"]) is not tuple
            or tuple(facts["live_paths"]) != CANDIDATE_PATHS
        ):
            raise ValueError(ERROR)
        commits = facts["path_commits"]
        if not commits:
            if (
                facts["head"] != BASE_COMMIT
                or facts["origin"] != BASE_COMMIT
                or (facts["ahead"], facts["behind"]) != (0, 0)
                or facts["tracked"]
                or facts["staged"]
                or facts["untracked"] != CANDIDATE_PATHS
                or facts["porcelain"]
                != tuple(sorted(f"?? {path}" for path in CANDIDATE_PATHS))
                or any(
                    item["tracked"] is not False or item["mode"] != "100644"
                    for item in facts["live_paths"].values()
                )
            ):
                raise ValueError(ERROR)
            return {
                "origin_main": BASE_COMMIT,
                "ahead": 0,
                "behind": 0,
                "lifecycle_profile": "transformation_overlay_precommit_candidate",
                "formal_candidate_commit": "",
            }
        commit = commits[0]
        if (
            not _is_hex(commit["commit"], 40)
            or commit["parents"] != [BASE_COMMIT]
            or commit["subject"] != FORMAL_COMMIT_SUBJECT
            or commit["changed_paths"] != CANDIDATE_PATHS
            or commit["changed_statuses"]
            != {path: "A" for path in CANDIDATE_PATHS}
            or any(
                commit["path_modes"].get(path) != "100644"
                for path in CANDIDATE_PATHS
            )
            or any(
                facts["live_paths"][path]
                != {
                    "tracked": True,
                    "mode": "100644",
                    "index_blob": commit["path_blobs"].get(path),
                    "blob": commit["path_blobs"].get(path),
                }
                for path in CANDIDATE_PATHS
            )
            or commit["ancestor_head"] is not True
            or any(
                path in facts["tracked"]
                or path in facts["staged"]
                or path in facts["untracked"]
                for path in CANDIDATE_PATHS
            )
        ):
            raise ValueError(ERROR)
        if commit["ancestor_origin"] is True:
            return {
                "origin_main": facts["origin"],
                "ahead": facts["ahead"],
                "behind": facts["behind"],
                "lifecycle_profile": "transformation_overlay_published_successor",
                "formal_candidate_commit": commit["commit"],
            }
        if (
            facts["head"] != commit["commit"]
            or facts["origin"] != BASE_COMMIT
            or (facts["ahead"], facts["behind"]) != (1, 0)
            or facts["tracked"]
            or facts["staged"]
            or facts["untracked"]
            or facts["porcelain"]
        ):
            raise ValueError(ERROR)
        return {
            "origin_main": BASE_COMMIT,
            "ahead": 1,
            "behind": 0,
            "lifecycle_profile": "transformation_overlay_committed_unpushed",
            "formal_candidate_commit": commit["commit"],
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _validate_lifecycle_witness(witness: object) -> None:
    try:
        if (
            type(witness) is not dict
            or tuple(witness) != _LIFECYCLE_FIELDS
            or type(witness["origin_main"]) is not str
            or not _is_hex(witness["origin_main"], 40)
            or type(witness["ahead"]) is not int
            or type(witness["behind"]) is not int
            or witness["ahead"] < 0
            or witness["behind"] < 0
            or type(witness["lifecycle_profile"]) is not str
            or type(witness["formal_candidate_commit"]) is not str
        ):
            raise ValueError(ERROR)
        profile = witness["lifecycle_profile"]
        commit = witness["formal_candidate_commit"]
        if profile == "transformation_overlay_precommit_candidate":
            if (
                witness["origin_main"] != BASE_COMMIT
                or (witness["ahead"], witness["behind"]) != (0, 0)
                or commit != ""
            ):
                raise ValueError(ERROR)
        elif profile == "transformation_overlay_committed_unpushed":
            if (
                witness["origin_main"] != BASE_COMMIT
                or (witness["ahead"], witness["behind"]) != (1, 0)
                or not _is_hex(commit, 40)
                or commit == BASE_COMMIT
            ):
                raise ValueError(ERROR)
        elif profile == "transformation_overlay_published_successor":
            if not _is_hex(commit, 40) or commit == BASE_COMMIT:
                raise ValueError(ERROR)
        else:
            raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


EXECUTION_BOUNDARY_FIELDS = (
    "human_fields_prefilled",
    "approved_smarts_generated",
    "approval_decision_generated",
    "formal_worklist_modified",
    "authority_changed",
    "review_submission_compiled",
    "review_ingested",
    "authority_bundle_generated",
    "role_or_seed_generated",
    "tensor_materialized",
    "model_changed",
    "training_used",
)
RESPONSE_FIELDS = (
    "schema_version",
    "base_commit",
    *_LIFECYCLE_FIELDS,
    "unit_count",
    "sample_count",
    "field_count",
    "gap_count",
    "failure_count",
    "schema_gap_detected",
    "formal_post_reaction_authority_count",
    "family_identity_evidence_ready",
    "complete_rule_evidence_ready",
    "artifact_sha256",
    "candidate_valence_ledger_is_gap_signal_only",
    "candidate_valence_ledger_is_reaction_authority",
    *EXECUTION_BOUNDARY_FIELDS,
    "feature_semantics_reaudit_required_before_training",
    "ready_for_training",
    "response_sha256",
)
_RESPONSE_INT_FIELDS = (
    "ahead",
    "behind",
    "unit_count",
    "sample_count",
    "field_count",
    "gap_count",
    "failure_count",
    "formal_post_reaction_authority_count",
)
_RESPONSE_BOOL_FIELDS = (
    "schema_gap_detected",
    "family_identity_evidence_ready",
    "complete_rule_evidence_ready",
    "candidate_valence_ledger_is_gap_signal_only",
    "candidate_valence_ledger_is_reaction_authority",
    *EXECUTION_BOUNDARY_FIELDS,
    "feature_semantics_reaudit_required_before_training",
    "ready_for_training",
)


def _artifact_sha_witness(artifacts: Mapping[str, bytes]) -> dict[str, str]:
    if type(artifacts) is not dict or tuple(artifacts) != ARTIFACT_PATHS:
        raise ValueError(ERROR)
    witness = {
        Path(path).name: _sha256(artifacts[path]) for path in ARTIFACT_PATHS
    }
    if any(not _is_hex(value, 64) for value in witness.values()):
        raise ValueError(ERROR)
    return witness


def _validate_response(
    response: object,
    *,
    expected_lifecycle: Mapping[str, object],
    expected_artifact_sha256: Mapping[str, str],
) -> None:
    try:
        _validate_lifecycle_witness(expected_lifecycle)
        if (
            type(response) is not dict
            or tuple(response) != RESPONSE_FIELDS
            or any(type(response[field]) is not int for field in _RESPONSE_INT_FIELDS)
            or any(type(response[field]) is not bool for field in _RESPONSE_BOOL_FIELDS)
            or any(
                type(response[field]) is not str
                for field in (
                    "schema_version",
                    "base_commit",
                    "origin_main",
                    "lifecycle_profile",
                    "formal_candidate_commit",
                    "response_sha256",
                )
            )
            or type(response["artifact_sha256"]) is not dict
        ):
            raise ValueError(ERROR)
        lifecycle = {field: response[field] for field in _LIFECYCLE_FIELDS}
        _validate_lifecycle_witness(lifecycle)
        if (
            lifecycle != expected_lifecycle
            or response["schema_version"] != SCHEMA_VERSION
            or response["base_commit"] != BASE_COMMIT
            or response["unit_count"] != 1
            or response["sample_count"] != 2
            or response["field_count"] != 41
            or response["gap_count"] != 2
            or response["failure_count"] != 28
            or response["schema_gap_detected"] is not True
            or response["formal_post_reaction_authority_count"] != 0
            or response["family_identity_evidence_ready"] is not True
            or response["complete_rule_evidence_ready"] is not False
            or response["artifact_sha256"] != expected_artifact_sha256
            or response["candidate_valence_ledger_is_gap_signal_only"] is not True
            or response["candidate_valence_ledger_is_reaction_authority"] is not False
            or any(response[field] is not False for field in EXECUTION_BOUNDARY_FIELDS)
            or response["feature_semantics_reaudit_required_before_training"] is not True
            or response["ready_for_training"] is not False
        ):
            raise ValueError(ERROR)
        unsigned = {
            field: response[field] for field in RESPONSE_FIELDS
            if field != "response_sha256"
        }
        if response["response_sha256"] != _sha256(_canonical_json_bytes(unsigned)):
            raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _build_response(
    lifecycle: Mapping[str, object], artifacts: Mapping[str, bytes]
) -> dict[str, object]:
    external_lifecycle = {field: lifecycle[field] for field in _LIFECYCLE_FIELDS}
    external_artifact_sha = _artifact_sha_witness(artifacts)
    _validate_lifecycle_witness(external_lifecycle)
    response: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "base_commit": BASE_COMMIT,
        **external_lifecycle,
        "unit_count": 1,
        "sample_count": 2,
        "field_count": 41,
        "gap_count": 2,
        "failure_count": 28,
        "schema_gap_detected": True,
        "formal_post_reaction_authority_count": 0,
        "family_identity_evidence_ready": True,
        "complete_rule_evidence_ready": False,
        "artifact_sha256": dict(external_artifact_sha),
        "candidate_valence_ledger_is_gap_signal_only": True,
        "candidate_valence_ledger_is_reaction_authority": False,
        **{field: False for field in EXECUTION_BOUNDARY_FIELDS},
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "response_sha256": "",
    }
    response["response_sha256"] = _sha256(_canonical_json_bytes({
        field: response[field] for field in RESPONSE_FIELDS
        if field != "response_sha256"
    }))
    if tuple(response) != RESPONSE_FIELDS:
        raise ValueError(ERROR)
    _validate_response(
        response,
        expected_lifecycle=external_lifecycle,
        expected_artifact_sha256=external_artifact_sha,
    )
    return response


_STRUCTURED_JSON_SCHEMA_NAMES = (
    "reviewed_atom_map_contract_json",
    "reviewed_attachment_boundary_map_numbers_by_sample_json",
    "reviewed_pre_or_post_atom_state_contract_json",
    "reviewed_edge_list_json",
    "reviewed_bond_order_changes_json",
    "reviewed_formal_charge_changes_json",
    "reviewed_protonation_transfer_contract_json",
    "reviewed_leaving_group_contract_json",
)

STRUCTURED_JSON_SCHEMAS = {
    "reviewed_atom_map_contract_json": {
        "samples": {
            "<sample_id>": {
                "target_residue_atom_map_number": "<positive int>",
                "ligand_reactive_atom_map_number": "<positive int>",
                "warhead_atom_map_numbers": ["<positive int>", "..."],
                "atom_records": [{
                    "map_number": "<positive int>",
                    "sample_atom_id": "<string>",
                    "element": "<string>",
                }],
            }
        }
    },
    "reviewed_attachment_boundary_map_numbers_by_sample_json": {
        "samples": {
            "<sample_id>": [{
                "warhead_attachment_atom_map_number": "<positive int>",
                "nonwarhead_boundary_atom_map_number": "<positive int>",
                "bond_order": "<normalized order>",
            }, {
                "warhead_attachment_atom_map_number": "<positive int>",
                "nonwarhead_boundary_atom_map_number": "<positive int>",
                "bond_order": "<normalized order>",
            }]
        }
    },
    "reviewed_pre_or_post_atom_state_contract_json": {
        "samples": {
            "<sample_id>": [{
                "map_number": "<positive int>",
                "element": "<string>",
                "formal_charge": "<int>",
                "explicit_hydrogen_count": "<nonnegative int or null>",
            }]
        }
    },
    "reviewed_edge_list_json": {
        "samples": {
            "<sample_id>": [{
                "map_number_1": "<positive int>",
                "map_number_2": "<positive int>",
                "bond_order": "<normalized order>",
            }]
        }
    },
    "reviewed_bond_order_changes_json": {
        "samples": {
            "<sample_id>": [{
                "map_number_1": "<positive int>",
                "map_number_2": "<positive int>",
                "pre_bond_order": "<normalized order>",
                "post_bond_order": "<normalized order>",
            }]
        }
    },
    "reviewed_formal_charge_changes_json": {
        "samples": {
            "<sample_id>": [{
                "map_number": "<positive int>",
                "pre_formal_charge": "<int>",
                "post_formal_charge": "<int>",
            }]
        }
    },
    "reviewed_protonation_transfer_contract_json": {
        "samples": {
            "<sample_id>": {
                "status": "<explicitly_attested or not_claimed>",
                "transfers": "<explicit list when attested>",
            }
        }
    },
    "reviewed_leaving_group_contract_json": {
        "samples": {
            "<sample_id>": {
                "status": "<explicitly_attested or not_claimed>",
                "leaving_group_records": [{
                    "leaving_atom_map_numbers": ["<positive int>"],
                    "broken_edge": {
                        "map_number_1": "<positive int>",
                        "map_number_2": "<positive int>",
                        "pre_bond_order": "<normalized order>",
                    },
                }],
            }
        }
    },
}


def _validate_structured_json_schema_contracts_v1(
    schemas: object | None = None,
) -> None:
    """Fail closed on drift in the future structured-JSON schema templates."""

    try:
        value = STRUCTURED_JSON_SCHEMAS if schemas is None else schemas
        if type(value) is not dict or tuple(value) != _STRUCTURED_JSON_SCHEMA_NAMES:
            raise ValueError(ERROR)

        def validate_placeholder_tree(node: object) -> None:
            if type(node) is dict:
                for child in node.values():
                    validate_placeholder_tree(child)
                return
            if type(node) is list:
                for child in node:
                    validate_placeholder_tree(child)
                return
            if not (
                type(node) is str
                and (node == "..." or (node.startswith("<") and node.endswith(">")))
            ):
                raise ValueError(ERROR)

        for schema in value.values():
            if (
                type(schema) is not dict
                or tuple(schema) != ("samples",)
                or type(schema["samples"]) is not dict
                or tuple(schema["samples"]) != ("<sample_id>",)
            ):
                raise ValueError(ERROR)
            validate_placeholder_tree(schema)

        attachment = value[
            "reviewed_attachment_boundary_map_numbers_by_sample_json"
        ]["samples"]["<sample_id>"]
        attachment_keys = (
            "warhead_attachment_atom_map_number",
            "nonwarhead_boundary_atom_map_number",
            "bond_order",
        )
        if (
            type(attachment) is not list
            or len(attachment) != 2
            or any(type(record) is not dict for record in attachment)
            or any(tuple(record) != attachment_keys for record in attachment)
            or attachment[0] != attachment[1]
        ):
            raise ValueError(ERROR)

        protonation = value[
            "reviewed_protonation_transfer_contract_json"
        ]["samples"]["<sample_id>"]
        leaving_group = value[
            "reviewed_leaving_group_contract_json"
        ]["samples"]["<sample_id>"]
        leaving_records = leaving_group.get("leaving_group_records")
        if (
            type(protonation) is not dict
            or protonation.get("status")
            != "<explicitly_attested or not_claimed>"
            or type(leaving_group) is not dict
            or tuple(leaving_group) != ("status", "leaving_group_records")
            or leaving_group["status"]
            != "<explicitly_attested or not_claimed>"
            or type(leaving_records) is not list
            or len(leaving_records) != 1
            or type(leaving_records[0]) is not dict
            or tuple(leaving_records[0])
            != ("leaving_atom_map_numbers", "broken_edge")
            or type(leaving_records[0]["leaving_atom_map_numbers"]) is not list
            or leaving_records[0]["leaving_atom_map_numbers"]
            != ["<positive int>"]
            or type(leaving_records[0]["broken_edge"]) is not dict
            or tuple(leaving_records[0]["broken_edge"])
            != ("map_number_1", "map_number_2", "pre_bond_order")
        ):
            raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error

APPROVAL_INVARIANTS = (
    "family_identity_authority_formally_exists",
    "exact2_sample_scope_explicit",
    "atom_map_contract_complete",
    "map_numbers_positive_and_unique_per_sample",
    "target_SG_and_ligand_C21_mapped",
    "two_attachment_boundaries_per_sample_plural_mapped",
    "pre_atom_state_complete",
    "post_atom_state_complete",
    "formed_edge_complete",
    "broken_edges_explicitly_reviewed_allowing_explicit_empty_list",
    "bond_order_changes_explicitly_reviewed_allowing_explicit_empty_list",
    "formal_charge_changes_explicitly_reviewed_allowing_explicit_empty_list",
    "protonation_transfer_explicitly_reviewed",
    "leaving_group_contract_explicitly_reviewed",
    "reversibility_semantics_explicitly_reviewed",
    "post_state_evidence_type_source_sha_complete",
    "all_edge_endpoints_exist_in_atom_map",
    "formed_edge_exactly_covers_CYS_SG_to_ligand_reactive_center",
    "transformation_class_matches_explicit_delta",
    "bond_order_change_class_requires_nonempty_change_list",
    "broken_bond_class_requires_nonempty_broken_edge_list",
    "conditional_center_bond_order_conflict_explicitly_resolved",
    "identity_attestation_true",
    "full_semantics_attestation_true",
    "reviewer_attestor_rationale_and_review_completed_complete",
    "review_completed_true",
    "approved_smarts_not_derived_from_candidate_graph",
    "formal_worklist_and_historical_authority_unchanged",
)


def _reviewed_list_state(value: object) -> str:
    """Distinguish an unreviewed blank from a canonical explicit empty list."""

    if value == "":
        return "unreviewed_empty_string"
    if type(value) is not str:
        raise ValueError(ERROR)
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError) as error:
        raise ValueError(ERROR) from error
    if _canonical_json_text(parsed) != value:
        raise ValueError(ERROR)
    if type(parsed) is list and parsed == []:
        return "explicit_canonical_empty_list"
    if type(parsed) is not dict or tuple(parsed) != ("samples",):
        raise ValueError(ERROR)
    samples = parsed["samples"]
    if (
        type(samples) is not dict
        or tuple(samples) != SAMPLE_IDS
        or any(type(samples[sample_id]) is not list for sample_id in SAMPLE_IDS)
    ):
        raise ValueError(ERROR)
    if all(samples[sample_id] == [] for sample_id in SAMPLE_IDS):
        return "explicit_canonical_empty_list"
    return "explicit_canonical_nonempty_list"


def _failure_baseline() -> dict[str, object]:
    artifacts = _expected_artifacts()
    return {
        "source_inventory": [
            {
                "producer": source.producer,
                "sha256": source.sha256,
            }
            for source in SOURCE_EVIDENCE
        ],
        "workspace_inode": WORKSPACE_IDENTITY["canonical_st_ino"],
        "dossier_inode": DOSSIER_IDENTITY["st_ino"],
        "parent_review_unit_id": PARENT_REVIEW_UNIT_ID,
        "reaction_family_id": REACTION_FAMILY_ID,
        "warhead_rule_id": WARHEAD_RULE_ID,
        "sample_ids": list(SAMPLE_IDS),
        "ligand_reactive_atoms": {sample_id: "C21" for sample_id in SAMPLE_IDS},
        "target_residue_atom": "CYS:SG",
        "candidate_graph_sha256": CANDIDATE_LOCAL_GRAPH_SHA256,
        "pre_bond_order_sum": 4,
        "conditional_post_sum": 5,
        "post_authority_status": "absent",
        "schema_gap_detected": True,
        "boundary_counts": {sample_id: 2 for sample_id in SAMPLE_IDS},
        "future_contract": {
            "attachment_boundary_list_lengths": {
                sample_id: 2 for sample_id in SAMPLE_IDS
            },
            "pre_atom_state_contract_explicit": True,
            "post_atom_state_contract_explicit": True,
            "formed_edge_contract_explicit": True,
            "bond_order_change_review_state": "explicit_list_field",
            "formal_charge_change_review_state": "explicit_list_field",
            "protonation_transfer_review_state": "explicit_contract_field",
        },
        "field_contract": [dict(row) for row in _field_contract_rows()],
        "approved_smarts_generated": False,
        "approval_decision_generated": False,
        "formal_worklist_modified": False,
        "authority_changed": False,
        "ready_for_training": False,
        "artifact_sha256": _artifact_sha_witness(artifacts),
    }


def _validate_failure_baseline(value: object) -> None:
    try:
        if type(value) is not dict:
            raise ValueError(ERROR)
        expected = _failure_baseline()
        if tuple(value) != tuple(expected):
            raise ValueError(ERROR)
        if (
            type(value["source_inventory"]) is not list
            or len(value["source_inventory"]) != len(SOURCE_EVIDENCE)
            or any(
                row != expected["source_inventory"][index]
                for index, row in enumerate(value["source_inventory"])
            )
            or value["workspace_inode"] != WORKSPACE_IDENTITY["canonical_st_ino"]
            or value["dossier_inode"] != DOSSIER_IDENTITY["st_ino"]
            or value["parent_review_unit_id"] != PARENT_REVIEW_UNIT_ID
            or value["reaction_family_id"] != REACTION_FAMILY_ID
            or value["warhead_rule_id"] != WARHEAD_RULE_ID
            or value["sample_ids"] != list(SAMPLE_IDS)
            or value["ligand_reactive_atoms"]
            != {sample_id: "C21" for sample_id in SAMPLE_IDS}
            or value["target_residue_atom"] != "CYS:SG"
            or value["candidate_graph_sha256"] != CANDIDATE_LOCAL_GRAPH_SHA256
            or type(value["pre_bond_order_sum"]) is not int
            or value["pre_bond_order_sum"] != 4
            or type(value["conditional_post_sum"]) is not int
            or value["conditional_post_sum"] != 5
            or value["post_authority_status"] != "absent"
            or value["schema_gap_detected"] is not True
            or value["future_contract"] != expected["future_contract"]
            or value["field_contract"] != expected["field_contract"]
            or value["approved_smarts_generated"] is not False
            or value["approval_decision_generated"] is not False
            or value["formal_worklist_modified"] is not False
            or value["authority_changed"] is not False
            or value["ready_for_training"] is not False
            or value["artifact_sha256"] != expected["artifact_sha256"]
        ):
            raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _clone_json(value: object) -> Any:
    return json.loads(_canonical_json_text(value))


def _apply_failure_mutation(case_id: str, value: object) -> None:
    if type(value) is not dict:
        raise ValueError(ERROR)
    if case_id == "X01":
        value["source_inventory"][0]["producer"] = "a" * 40
    elif case_id == "X02":
        value["source_inventory"][0]["sha256"] = "a" * 64
    elif case_id == "X03":
        value["workspace_inode"] += 1
    elif case_id == "X04":
        value["dossier_inode"] += 1
    elif case_id == "X05":
        value["parent_review_unit_id"] = "CURRENT11_FAMILY_RULE_APPROVAL_REVIEW_UNIT_999999"
    elif case_id == "X06":
        value["reaction_family_id"] = "COVAPIE_CYS_SG_REACTION_FAMILY_SUBSTITUTED"
    elif case_id == "X07":
        value["warhead_rule_id"] = "COVAPIE_CYS_SG_WARHEAD_RULE_SUBSTITUTED"
    elif case_id == "X08":
        value["sample_ids"].pop()
    elif case_id == "X09":
        value["ligand_reactive_atoms"][SAMPLE_IDS[0]] = "C20"
    elif case_id == "X10":
        value["target_residue_atom"] = "CYS:CB"
    elif case_id == "X11":
        value["candidate_graph_sha256"] = "a" * 64
    elif case_id == "X12":
        value["pre_bond_order_sum"] = 3
    elif case_id == "X13":
        value["conditional_post_sum"] = 4
    elif case_id == "X14":
        value["post_authority_status"] = "present"
    elif case_id == "X15":
        value["schema_gap_detected"] = False
    elif case_id == "X16":
        value["future_contract"]["attachment_boundary_list_lengths"][SAMPLE_IDS[0]] = 1
    elif case_id == "X17":
        value["future_contract"]["pre_atom_state_contract_explicit"] = False
    elif case_id == "X18":
        value["future_contract"]["post_atom_state_contract_explicit"] = False
    elif case_id == "X19":
        value["future_contract"]["formed_edge_contract_explicit"] = False
    elif case_id == "X20":
        value["future_contract"]["bond_order_change_review_state"] = "unreviewed_empty_string"
    elif case_id == "X21":
        value["future_contract"]["formal_charge_change_review_state"] = "unreviewed_empty_string"
    elif case_id == "X22":
        value["future_contract"]["protonation_transfer_review_state"] = "unreviewed_empty_string"
    elif case_id == "X23":
        row = next(
            row for row in value["field_contract"]
            if row["field_name"] == "reviewed_transformation_version"
        )
        row["initial_value"] = "v1"
        row["prefilled"] = "true"
    elif case_id == "X24":
        row = next(
            row for row in value["field_contract"]
            if row["field_name"] == "transformation_review_decision"
        )
        row["initial_value"] = "approve_reaction_transformation_contract"
        row["prefilled"] = "true"
    elif case_id == "X25":
        value["approved_smarts_generated"] = True
    elif case_id == "X26":
        value["authority_changed"] = True
    elif case_id == "X27":
        value["ready_for_training"] = True
    elif case_id == "X28":
        first = next(iter(value["artifact_sha256"]))
        value["artifact_sha256"][first] = "a" * 64
    else:
        raise ValueError(ERROR)


def evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, object]:
    """Read and fail-closed validate the Current11 UNIT_000001 overlay."""

    try:
        if not isinstance(repo_root, Path) or not isinstance(state_root, Path):
            raise ValueError(ERROR)
        _validate_structured_json_schema_contracts_v1()
        repository = repo_root.resolve(strict=True)
        state = state_root.resolve(strict=True)
        if (
            _git_text(repository, ("rev-parse", "--show-toplevel")).strip()
            != str(repository)
        ):
            raise ValueError(ERROR)
        workspace = _validate_workspace(state)
        dossier = _validate_dossier(state)
        _validate_source_inventory(repository, state)
        formal_state = _load_formal_state(
            repository, state, workspace, dossier
        )
        if formal_state != {
            key: value for key, value in _failure_baseline().items()
            if key in formal_state
        }:
            raise ValueError(ERROR)
        artifacts, manifest = _validate_artifacts(repository)
        if (
            manifest["formal_post_reaction_authority_count"] != 0
            or manifest["candidate_valence_ledger_is_gap_signal_only"] is not True
            or manifest["candidate_valence_ledger_is_reaction_authority"] is not False
            or manifest["ready_for_training"] is not False
        ):
            raise ValueError(ERROR)
        lifecycle = _derive_lifecycle(_collect_lifecycle(repository))
        return _build_response(lifecycle, artifacts)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error
