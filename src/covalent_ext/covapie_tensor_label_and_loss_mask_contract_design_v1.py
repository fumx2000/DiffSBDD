"""Metadata-only CovaPIE tensor, label, and loss-mask contract design V1.

The module reads committed evidence exclusively through ``git show BASE:path``.
It never reads raw structures, checkpoints, or tensor archives and never
materializes tensors or changes a dataloader, model, forward path, or loss.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import math
import subprocess
from collections.abc import Sequence
from dataclasses import asdict, dataclass, fields as dataclass_fields, replace
from pathlib import Path
from typing import Any, Mapping


__all__ = (
    "BASE_COMMIT",
    "CANONICAL_TASKS",
    "EXACT_INDEX_SPACES",
    "FORMAL_COMMIT_SUBJECT",
    "PAIR_POLICY_CASES",
    "PAIR_POLICY_MUTATIONS",
    "FAILURE_CASES",
    "FAILURE_MUTATIONS",
    "BASELINE_PAIR_POLICY_SCENARIO",
    "BASELINE_SCENARIO",
    "PairCandidatePolicyScenario",
    "PairCandidatePolicyObservation",
    "PairCandidateSampleSpec",
    "PairCandidateRecord",
    "PairCandidateProjection",
    "TensorLabelAndLossMaskContractDesignDecision",
    "TensorLabelAndLossMaskContractScenario",
    "TensorLabelAndLossMaskContractScenarioObservation",
    "build_pair_candidate_records_v1",
    "build_covapie_tensor_label_and_loss_mask_contract_design_artifacts_v1",
    "build_failure_matrix_rows_v1",
    "build_pair_candidate_and_negative_policy_matrix_rows_v1",
    "canonical_task_regions_v1",
    "derive_covapie_tensor_label_and_loss_mask_contract_design_v1",
    "evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1",
    "flatten_local_index_v1",
    "mutation_signature_v1",
    "serialize_covapie_tensor_label_and_loss_mask_contract_design_decision_v1",
    "validate_auxiliary_label_and_loss_mask_contract_v1",
    "validate_checkpoint_sidecar_boundary_v1",
    "validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1",
    "validate_geometry_component_contract_v1",
    "validate_mutation_registry_exact_types_v1",
    "validate_offsets_v1",
    "validate_pair_candidate_policy_scenario_exact_types_v1",
    "validate_pair_candidate_sample_spec_exact_types_v1",
    "validate_sentinel_with_validity_v1",
    "validate_target_residue_condition_contract_v1",
    "validate_task_mask_partition_v1",
    "validate_tensor_label_loss_mask_scenario_exact_types_v1",
)

BASE_COMMIT = "160cdbda8800a535b5c0a81d501babfae9a8615b"
BASE_PARENT = "5b2013281b03d7bd3e0c59b9985e52494263c69f"
BASE_TREE = "cecb5fe5cb70162bc1c41162d4503ec73fea2968"
BASE_SUBJECT = "add CovaPIE training unknown-atom policy resolution v1"
FORMAL_COMMIT_SUBJECT = "add CovaPIE tensor label and loss-mask contract v1"
SCHEMA_VERSION = "covapie_tensor_label_and_loss_mask_contract_design_v1"
STAGE = SCHEMA_VERSION
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

SOURCE_INVENTORY_FILE = "covapie_tensor_label_loss_mask_source_inventory.csv"
CONTRACT_REGISTRY_FILE = "covapie_tensor_label_loss_mask_contract_registry.csv"
PAIR_POLICY_FILE = "covapie_pair_candidate_and_negative_policy_matrix.csv"
FAILURE_MATRIX_FILE = "covapie_tensor_label_loss_mask_failure_matrix.csv"
ISSUE_INVENTORY_FILE = (
    "covapie_tensor_label_loss_mask_issue_readiness_inventory.csv"
)
MANIFEST_FILE = (
    "covapie_tensor_label_and_loss_mask_contract_design_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_INVENTORY_FILE,
    CONTRACT_REGISTRY_FILE,
    PAIR_POLICY_FILE,
    FAILURE_MATRIX_FILE,
    ISSUE_INVENTORY_FILE,
    MANIFEST_FILE,
)

PREDECESSOR_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py"
)
PREDECESSOR_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1"
)
PREDECESSOR_MANIFEST = PREDECESSOR_ROOT / (
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_"
    "manifest.json"
)
PREDECESSOR_ISSUES = PREDECESSOR_ROOT / (
    "covapie_unknown_atom_policy_resolution_issue_readiness_inventory.csv"
)
HEAVY_DISPOSITION = PREDECESSOR_ROOT / (
    "covapie_heavy_atom_disposition_and_index_projection_matrix.csv"
)
SAMPLE_PROJECTION = PREDECESSOR_ROOT / (
    "covapie_sample_heavy_atom_projection_validation_matrix.csv"
)
FINAL_DATASET_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
ATOM_PAIR_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1"
)
ATOM_PAIR_MAPPING = ATOM_PAIR_ROOT / (
    "covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
ATOM_PAIR_MANIFEST = ATOM_PAIR_ROOT / (
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_manifest.json"
)

FROZEN_SHA256 = {
    PREDECESSOR_SOURCE: (
        "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241"
    ),
    PREDECESSOR_MANIFEST: (
        "24cb60ca4f080a72e8c60aef63d105d82ec2f432eecc9b90f3341f52576bb6e0"
    ),
    PREDECESSOR_ISSUES: (
        "133e380feb5f21687b6e196101e0a19fcb46a21dc736e47ba0665a067d593e13"
    ),
    HEAVY_DISPOSITION: (
        "b53f438edffab32f78d07df839b8c8437ec4223e31bd8a8885deedf32497b4be"
    ),
    SAMPLE_PROJECTION: (
        "63f1df49d9a6f4e0efbee6c8bb474deabaedea9cef91f27d2cf49f7caeee6f96"
    ),
    FINAL_DATASET_INDEX: (
        "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d"
    ),
    ATOM_PAIR_MAPPING: (
        "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45"
    ),
    ATOM_PAIR_MANIFEST: (
        "229f5430feb3b5c147edce6c80dce684703b614e3764c7c18afd8344c25c3152"
    ),
}

ROLE_MASK_SOURCE = Path("src/covalent_ext/masking.py")
ROLE_SCHEMA_SOURCE = Path("src/covalent_ext/schema.py")
B3_PROTOCOL = Path(
    "data/derived/covalent_small/b3_scaffold_only_mask_design_v0/"
    "b3_scaffold_only_mask_protocol.json"
)
ROLE_SCHEMA_DOC = Path("docs/covalent_data_schema.md")
COORDINATE_GEOMETRY_AUDIT = Path(
    "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/"
    "covapie_coordinate_geometry_semantics_audit.csv"
)
AUXILIARY_LABEL_AUDIT = Path(
    "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/"
    "covapie_auxiliary_label_semantics_audit.csv"
)
FINAL_DATASET_SCHEMA = Path(
    "data/derived/covalent_small/covapie_final_dataset_design_gate_v0/"
    "covapie_final_dataset_schema_contract.csv"
)
CHECKPOINT_CONFIG = Path("configs/crossdock_fullatom_cond.yml")
CONSTANTS_SOURCE = Path("constants.py")
NPZ_ADAPTER = Path("src/covalent_ext/npz_dataset.py")
BATCH_ADAPTER = Path("src/covalent_ext/batch_adapter.py")
DIFFSBDD_ADAPTER = Path("src/covalent_ext/diffsbdd_input_adapter.py")
MODEL_INPUT_ADAPTER = Path("src/covalent_ext/model_input_adapter.py")
LIGHTNING_CONSUMER = Path("lightning_modules.py")
DYNAMICS_CONSUMER = Path("equivariant_diffusion/dynamics.py")
DIFFUSION_CONSUMER = Path("equivariant_diffusion/en_diffusion.py")
STEP12D_LINEAGE = Path(
    "src/covalent_ext/real_covalent_pretrained_forward_loss_smoke.py"
)

CANONICAL_TASKS = (
    (0, "warhead_only", "A"),
    (1, "linker_plus_warhead", "B"),
    (2, "scaffold_plus_warhead", "B2"),
    (3, "scaffold_only", "B3"),
    (4, "scaffold_plus_linker_plus_warhead", "C"),
)
EXACT_INDEX_SPACES = (
    "source_full_atom_row_index_0based",
    "retained_heavy_local_index_0based",
    "flattened_ligand_index_0based",
    "flattened_pocket_index_0based",
    "pair_candidate_index_0based",
    "batch_sample_index_0based",
)
CONTRACT_CATEGORIES = (
    "current_checkpoint_input",
    "batch_index_structure",
    "covalent_sidecar_condition",
    "canonical_task_mask",
    "auxiliary_training_label",
    "auxiliary_loss_mask",
    "reserved_metadata_only",
)
CONTRACT_STATUSES = (
    "designed",
    "designed_with_blocker",
    "not_applicable",
)
PLANNED_COVALENT_MODEL_MODULES = (
    "target residue/atom condition adapter",
    "role/mask/anchor-distance encoding",
    "ligand atom ↔ residue atom pair prediction head",
    "covalent geometry prediction head",
    "pair contrastive loss",
)
SUPPORTED_HEAVY_SYMBOLS = ("C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F")

SOURCE_COLUMNS = (
    "source_role",
    "source_path",
    "source_sha256",
    "committed_in_base",
    "source_kind",
    "selector_or_symbol",
    "referenced_contract_count",
    "referenced_sample_count",
    "verified",
)
CONTRACT_COLUMNS = (
    "contract_id",
    "contract_category",
    "semantic_name",
    "module_consumer",
    "contract_status",
    "source_fields_or_contract",
    "derivation_rule",
    "dtype",
    "rank",
    "shape",
    "width_or_component_count",
    "index_space",
    "local_or_flat",
    "padding_semantics",
    "sentinel_semantics",
    "value_domain_or_vocabulary",
    "unit",
    "coordinate_frame",
    "normalization_or_scaling",
    "label_availability_semantics",
    "loss_mask_semantics",
    "sidecar_only",
    "changes_checkpoint_input_width",
    "materialized_current_step",
    "geometry_component_id",
    "pre_post_or_delta",
    "periodic_or_nonperiodic",
    "canonical_range",
    "target_representation",
    "current_valid_sample_count",
    "evidence_status",
    "blocking_reason",
    "verified",
)
PAIR_POLICY_COLUMNS = (
    "case_id",
    "input_condition",
    "mutation_signature",
    "candidate_allowed",
    "label_semantics",
    "negative_semantics",
    "loss_mask_semantics",
    "fails_closed",
    "reason",
    "verified",
)
FAILURE_COLUMNS = (
    "failure_case",
    "expected_outcome",
    "observed_outcome",
    "expected_primary_reason",
    "observed_reasons",
    "mutation_signature",
    "failure_detected",
    "condition_contract_resolved",
    "pair_contract_resolved",
    "geometry_and_auxiliary_label_contract_resolved",
    "tensor_label_loss_mask_contract_designed",
    "ready_for_tensor_materialization_smoke",
    "ready_for_tensorization",
    "ready_for_model_integration",
    "ready_for_training",
    "fails_closed",
    "verified",
)

PAIR_POLICY_CASES = (
    "valid_same_sample_positive",
    "valid_same_sample_negative",
    "cross_sample_pair",
    "h_containing_pair",
    "padding_containing_pair",
    "non_target_residue_protein_atom",
    "full_table_index_used_as_heavy_index",
    "duplicate_positive",
    "missing_positive",
    "multiple_positives",
    "no_negative_candidate",
    "local_flat_index_mismatch",
    "offset_mismatch",
    "candidate_order_drift",
    "random_negative_sampling_requested",
    "hard_negative_mining_requested",
)
PAIR_POLICY_CONDITIONS = {
    "valid_same_sample_positive": "valid same-sample exact positive candidate",
    "valid_same_sample_negative": "valid same-sample non-positive candidate",
    "cross_sample_pair": "candidate joins atoms from different samples",
    "h_containing_pair": "candidate contains an explicit hydrogen",
    "padding_containing_pair": "candidate contains padding",
    "non_target_residue_protein_atom": "pocket atom is outside the target residue",
    "full_table_index_used_as_heavy_index": "source full-table index is used as retained-heavy index",
    "duplicate_positive": "the exact positive candidate is duplicated",
    "missing_positive": "no positive candidate is labeled",
    "multiple_positives": "more than one distinct candidate is positive",
    "no_negative_candidate": "exactly one positive exists but no negative candidate exists",
    "local_flat_index_mismatch": "local and flattened indices disagree",
    "offset_mismatch": "node offset and flattened node count disagree",
    "candidate_order_drift": "candidate enumeration order differs from the frozen order",
    "random_negative_sampling_requested": "random negative subsampling is requested",
    "hard_negative_mining_requested": "hard-negative mining is requested",
}

FAILURE_CASES = (
    "predecessor_sha_drift",
    "predecessor_not_contract_design_ready",
    "predecessor_effective_open_issue_unexpectedly_present",
    "checkpoint_width_changed_from_10",
    "sidecar_concatenated_into_checkpoint_10d_input",
    "explicit_h_included_in_model_bound_tensor",
    "unsupported_non_h_accepted",
    "missing_or_invalid_type_symbol_accepted",
    "source_full_table_index_used_as_heavy_index",
    "index_space_omitted",
    "local_flat_index_ambiguity",
    "ligand_offsets_missing",
    "pocket_offsets_missing",
    "offset_terminal_count_mismatch",
    "canonical_task_count_not_5",
    "b3_omitted",
    "short_alias_used_as_sole_semantics",
    "role_vocabulary_unresolved_but_marked_designed",
    "generation_fixed_masks_overlap",
    "generation_fixed_masks_incomplete",
    "target_context_masks_overlap",
    "c_minimal_seed_or_anchor_incorrectly_generated",
    "target_residue_membership_empty",
    "reactive_residue_atom_outside_target_residue",
    "pair_candidate_includes_cross_sample_atoms",
    "pair_candidate_includes_h",
    "pair_candidate_includes_non_target_residue_pocket_atom",
    "candidate_ordering_nondeterministic",
    "positive_pair_count_zero",
    "positive_pair_count_greater_than_one",
    "cross_sample_negatives_enabled",
    "random_negative_sampling_enabled",
    "pair_local_flat_index_mismatch",
    "pair_loss_mask_includes_invalid_sample",
    "contrastive_loss_enabled_with_no_negative",
    "geometry_component_semantics_undefined",
    "geometry_unit_or_periodicity_missing",
    "missing_geometry_label_participates_in_loss",
    "warhead_vocabulary_unresolved_but_marked_designed",
    "execution_boundary_crossed",
)


@dataclass(frozen=True)
class TensorLabelAndLossMaskContractDesignDecision:
    schema_version: str
    outcome: str
    predecessor_verified: bool
    contract_registry_row_count: int
    current_checkpoint_input_contract_count: int
    sidecar_condition_contract_count: int
    auxiliary_label_contract_count: int
    auxiliary_loss_mask_contract_count: int
    index_space_contract_count: int
    canonical_task_count: int
    role_vocabulary_frozen: bool
    pair_candidate_policy_frozen: bool
    pair_negative_policy_frozen: bool
    pair_positive_exact_one_verified: bool
    warhead_type_vocabulary_frozen: bool
    geometry_component_count: int
    geometry_contract_frozen: bool
    checkpoint_input_width_preserved: bool
    new_covalent_tensors_are_sidecars: bool
    tensor_label_loss_mask_contract_designed: bool
    tensor_materialization_used: bool
    runtime_enforcement_integrated: bool
    ready_for_tensor_materialization_smoke: bool
    ready_for_tensorization: bool
    ready_for_model_integration: bool
    ready_for_training: bool
    model_changed: bool
    dataloader_changed: bool
    forward_changed: bool
    loss_changed: bool
    checkpoint_access: bool
    training_used: bool
    recommended_next_step: str


@dataclass(frozen=True)
class TensorLabelAndLossMaskContractScenario:
    predecessor_sha_valid: bool = True
    predecessor_contract_design_ready: bool = True
    predecessor_effective_open_issue_count: int = 0

    checkpoint_atom_feature_width: int = 10
    covalent_sidecars_separate: bool = True
    explicit_h_excluded: bool = True
    unsupported_non_h_rejected: bool = True
    missing_or_invalid_symbol_rejected: bool = True

    source_full_table_index_model_or_loss_used: bool = False
    exact_index_spaces_present: bool = True
    index_space_annotations_complete: bool = True
    ligand_offsets_present: bool = True
    pocket_offsets_present: bool = True
    pair_offsets_present: bool = True
    offsets_valid: bool = True
    local_flat_relations_valid: bool = True

    canonical_task_count: int = 5
    b3_present: bool = True
    long_semantic_names_authoritative: bool = True
    role_vocabulary_frozen: bool = True
    role_assignments_complete: bool = False
    role_dependent_masks_marked_designed: bool = False
    minimal_seed_authority_present: bool = False
    c_seed_override_marked_resolved: bool = False
    generation_equals_target: bool = True
    fixed_equals_context: bool = True
    generation_fixed_masks_disjoint: bool = True
    generation_fixed_masks_exhaustive: bool = True
    target_context_masks_disjoint: bool = True
    target_context_masks_exhaustive: bool = True

    target_residue_membership_nonempty: bool = True
    reactive_atom_inside_target_residue: bool = True

    pair_candidate_domain_valid: bool = True
    pair_candidates_same_sample: bool = True
    pair_candidates_retained_heavy: bool = True
    pair_candidates_target_residue_only: bool = True
    pair_candidate_order_valid: bool = True
    pair_candidate_offsets_valid: bool = True
    pair_local_flat_indices_valid: bool = True
    pair_positive_count: int = 1
    pair_negative_count: int = 1
    cross_sample_negatives_allowed: bool = False
    random_negative_sampling: bool = False
    hard_negative_mining: bool = False
    pair_loss_masks_exclude_invalid_samples: bool = True
    contrastive_sample_loss_mask_enabled: bool = True

    warhead_vocabulary_frozen: bool = False
    warhead_contract_marked_resolved: bool = False
    geometry_components_semantically_complete: bool = False
    geometry_contract_marked_resolved: bool = False
    geometry_units_and_periodicity_valid: bool = True
    missing_geometry_excluded_from_loss: bool = True

    tensor_materialization_requested: bool = False
    dataloader_changed: bool = False
    model_changed: bool = False
    forward_changed: bool = False
    loss_changed: bool = False
    checkpoint_accessed: bool = False
    training_used: bool = False


@dataclass(frozen=True)
class TensorLabelAndLossMaskContractScenarioObservation:
    outcome: str
    reasons: tuple[str, ...]
    condition_contract_resolved: bool
    pair_contract_resolved: bool
    geometry_and_auxiliary_label_contract_resolved: bool
    tensor_label_loss_mask_contract_designed: bool
    ready_for_tensor_materialization_smoke: bool
    ready_for_tensorization: bool
    ready_for_model_integration: bool
    ready_for_training: bool
    fails_closed: bool


@dataclass(frozen=True)
class ContractSubvalidation:
    valid: bool
    resolved: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class PairCandidatePolicyScenario:
    candidate_is_positive: bool = True
    same_sample: bool = True
    ligand_retained_heavy: bool = True
    residue_retained_heavy: bool = True
    residue_is_target_member: bool = True
    contains_explicit_h: bool = False
    contains_padding: bool = False
    source_full_table_index_used: bool = False
    local_flat_consistent: bool = True
    offsets_valid: bool = True
    positive_count: int = 1
    negative_count: int = 1
    positive_candidate_duplicated: bool = False
    deterministic_order: bool = True
    cross_sample_negatives_allowed: bool = False
    random_negative_sampling: bool = False
    hard_negative_mining: bool = False
    invalid_sample_excluded_from_loss: bool = True
    contrastive_sample_loss_mask_enabled: bool = True


@dataclass(frozen=True)
class PairCandidatePolicyObservation:
    candidate_allowed: bool
    label_semantics: str
    negative_semantics: str
    loss_mask_semantics: str
    fails_closed: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class PairCandidateSampleSpec:
    batch_sample_index_0based: int
    retained_ligand_count: int
    retained_pocket_count: int
    target_residue_pocket_local_indices: tuple[int, ...]
    positive_ligand_local_index: int
    positive_pocket_local_index: int


@dataclass(frozen=True)
class PairCandidateRecord:
    pair_candidate_index_0based: int
    pair_candidate_batch_index: int
    pair_candidate_ligand_local_index: int
    pair_candidate_residue_local_index: int
    pair_candidate_ligand_flat_index: int
    pair_candidate_pocket_flat_index: int
    pair_candidate_is_positive: bool
    pair_candidate_is_negative: bool


@dataclass(frozen=True)
class PairCandidateProjection:
    records: tuple[PairCandidateRecord, ...]
    pair_candidate_offsets: tuple[int, ...]
    pair_candidate_batch_index: tuple[int, ...]
    pair_candidate_ligand_local_index: tuple[int, ...]
    pair_candidate_residue_local_index: tuple[int, ...]
    pair_candidate_ligand_flat_index: tuple[int, ...]
    pair_candidate_pocket_flat_index: tuple[int, ...]
    pair_candidate_is_positive: tuple[bool, ...]
    pair_candidate_is_negative: tuple[bool, ...]
    pair_positive_candidate_index: tuple[int, ...]
    pair_positive_candidate_valid: tuple[bool, ...]
    pair_negative_count: tuple[int, ...]
    pair_contrastive_sample_loss_mask: tuple[bool, ...]


BASELINE_SCENARIO = TensorLabelAndLossMaskContractScenario()
BASELINE_PAIR_POLICY_SCENARIO = PairCandidatePolicyScenario()

PAIR_POLICY_MUTATIONS: dict[str, dict[str, Any]] = {
    "valid_same_sample_positive": {
        "fields": {},
        "expected_reason": "valid_exact_positive_in_frozen_candidate_domain",
    },
    "valid_same_sample_negative": {
        "fields": {"candidate_is_positive": False},
        "expected_reason": "valid_deterministic_same_sample_negative",
    },
    "cross_sample_pair": {
        "fields": {"same_sample": False},
        "expected_reason": "cross_sample_candidates_forbidden",
    },
    "h_containing_pair": {
        "fields": {
            "contains_explicit_h": True,
            "ligand_retained_heavy": False,
        },
        "expected_reason": "explicit_hydrogen_forbidden",
    },
    "padding_containing_pair": {
        "fields": {"contains_padding": True},
        "expected_reason": "padding_forbidden",
    },
    "non_target_residue_protein_atom": {
        "fields": {"residue_is_target_member": False},
        "expected_reason": "residue_side_domain_is_target_residue_only",
    },
    "full_table_index_used_as_heavy_index": {
        "fields": {"source_full_table_index_used": True},
        "expected_reason": "source_index_cannot_enter_model_or_loss",
    },
    "duplicate_positive": {
        "fields": {"positive_candidate_duplicated": True},
        "expected_reason": "positive_candidate_must_not_be_duplicated",
    },
    "missing_positive": {
        "fields": {"positive_count": 0},
        "expected_reason": "positive_pair_count_zero",
    },
    "multiple_positives": {
        "fields": {"positive_count": 2},
        "expected_reason": "positive_pair_count_greater_than_one",
    },
    "no_negative_candidate": {
        "fields": {"negative_count": 0},
        "expected_reason": "contrastive_loss_requires_at_least_one_negative",
    },
    "local_flat_index_mismatch": {
        "fields": {"local_flat_consistent": False},
        "expected_reason": "local_to_flat_formula_must_hold",
    },
    "offset_mismatch": {
        "fields": {"offsets_valid": False},
        "expected_reason": "offset_contract_must_hold",
    },
    "candidate_order_drift": {
        "fields": {"deterministic_order": False},
        "expected_reason": "candidate_order_must_be_deterministic",
    },
    "random_negative_sampling_requested": {
        "fields": {"random_negative_sampling": True},
        "expected_reason": "random_negative_sampling_forbidden_v1",
    },
    "hard_negative_mining_requested": {
        "fields": {"hard_negative_mining": True},
        "expected_reason": "hard_negative_mining_forbidden_v1",
    },
}

FAILURE_MUTATIONS: dict[str, dict[str, Any]] = {
    "predecessor_sha_drift": {
        "fields": {"predecessor_sha_valid": False},
        "expected_reason": "predecessor_sha_invalid",
    },
    "predecessor_not_contract_design_ready": {
        "fields": {"predecessor_contract_design_ready": False},
        "expected_reason": "predecessor_contract_design_not_ready",
    },
    "predecessor_effective_open_issue_unexpectedly_present": {
        "fields": {"predecessor_effective_open_issue_count": 1},
        "expected_reason": "predecessor_effective_open_issue_count_not_zero",
    },
    "checkpoint_width_changed_from_10": {
        "fields": {"checkpoint_atom_feature_width": 11},
        "expected_reason": "checkpoint_atom_feature_width_not_10",
    },
    "sidecar_concatenated_into_checkpoint_10d_input": {
        "fields": {"covalent_sidecars_separate": False},
        "expected_reason": "covalent_sidecars_not_separate",
    },
    "explicit_h_included_in_model_bound_tensor": {
        "fields": {"explicit_h_excluded": False},
        "expected_reason": "explicit_hydrogen_not_excluded",
    },
    "unsupported_non_h_accepted": {
        "fields": {"unsupported_non_h_rejected": False},
        "expected_reason": "unsupported_non_hydrogen_not_rejected",
    },
    "missing_or_invalid_type_symbol_accepted": {
        "fields": {"missing_or_invalid_symbol_rejected": False},
        "expected_reason": "missing_or_invalid_symbol_not_rejected",
    },
    "source_full_table_index_used_as_heavy_index": {
        "fields": {"source_full_table_index_model_or_loss_used": True},
        "expected_reason": "source_full_table_index_used_as_heavy_index",
    },
    "index_space_omitted": {
        "fields": {"exact_index_spaces_present": False},
        "expected_reason": "exact_index_spaces_missing",
    },
    "local_flat_index_ambiguity": {
        "fields": {"index_space_annotations_complete": False},
        "expected_reason": "index_space_annotations_incomplete",
    },
    "ligand_offsets_missing": {
        "fields": {"ligand_offsets_present": False},
        "expected_reason": "ligand_node_offsets_missing",
    },
    "pocket_offsets_missing": {
        "fields": {"pocket_offsets_present": False},
        "expected_reason": "pocket_node_offsets_missing",
    },
    "offset_terminal_count_mismatch": {
        "fields": {"offsets_valid": False},
        "expected_reason": "offsets_invalid",
    },
    "canonical_task_count_not_5": {
        "fields": {"canonical_task_count": 4},
        "expected_reason": "canonical_task_count_not_5",
    },
    "b3_omitted": {
        "fields": {"b3_present": False},
        "expected_reason": "scaffold_only_b3_missing",
    },
    "short_alias_used_as_sole_semantics": {
        "fields": {"long_semantic_names_authoritative": False},
        "expected_reason": "long_semantic_names_not_authoritative",
    },
    "role_vocabulary_unresolved_but_marked_designed": {
        "fields": {
            "role_vocabulary_frozen": False,
            "role_dependent_masks_marked_designed": True,
        },
        "expected_reason": "unresolved_role_vocabulary_marked_designed",
    },
    "generation_fixed_masks_overlap": {
        "fields": {"generation_fixed_masks_disjoint": False},
        "expected_reason": "generation_fixed_masks_overlap",
    },
    "generation_fixed_masks_incomplete": {
        "fields": {"generation_fixed_masks_exhaustive": False},
        "expected_reason": "generation_fixed_masks_not_exhaustive",
    },
    "target_context_masks_overlap": {
        "fields": {"target_context_masks_disjoint": False},
        "expected_reason": "target_context_masks_overlap",
    },
    "c_minimal_seed_or_anchor_incorrectly_generated": {
        "fields": {"c_seed_override_marked_resolved": True},
        "expected_reason": (
            "c_minimal_seed_or_anchor_resolved_without_authority"
        ),
    },
    "target_residue_membership_empty": {
        "fields": {"target_residue_membership_nonempty": False},
        "expected_reason": "target_residue_membership_empty",
    },
    "reactive_residue_atom_outside_target_residue": {
        "fields": {"reactive_atom_inside_target_residue": False},
        "expected_reason": "reactive_atom_outside_target_residue",
    },
    "pair_candidate_includes_cross_sample_atoms": {
        "fields": {"pair_candidates_same_sample": False},
        "expected_reason": "cross_sample_candidates_forbidden",
    },
    "pair_candidate_includes_h": {
        "fields": {"pair_candidates_retained_heavy": False},
        "expected_reason": "explicit_hydrogen_forbidden",
    },
    "pair_candidate_includes_non_target_residue_pocket_atom": {
        "fields": {"pair_candidates_target_residue_only": False},
        "expected_reason": "residue_side_domain_is_target_residue_only",
    },
    "candidate_ordering_nondeterministic": {
        "fields": {"pair_candidate_order_valid": False},
        "expected_reason": "candidate_order_must_be_deterministic",
    },
    "positive_pair_count_zero": {
        "fields": {"pair_positive_count": 0},
        "expected_reason": "positive_pair_count_zero",
    },
    "positive_pair_count_greater_than_one": {
        "fields": {"pair_positive_count": 2},
        "expected_reason": "positive_pair_count_greater_than_one",
    },
    "cross_sample_negatives_enabled": {
        "fields": {"cross_sample_negatives_allowed": True},
        "expected_reason": "cross_sample_negatives_forbidden",
    },
    "random_negative_sampling_enabled": {
        "fields": {"random_negative_sampling": True},
        "expected_reason": "random_negative_sampling_forbidden_v1",
    },
    "pair_local_flat_index_mismatch": {
        "fields": {"pair_local_flat_indices_valid": False},
        "expected_reason": "local_to_flat_formula_must_hold",
    },
    "pair_loss_mask_includes_invalid_sample": {
        "fields": {"pair_loss_masks_exclude_invalid_samples": False},
        "expected_reason": "pair_loss_mask_includes_invalid_sample",
    },
    "contrastive_loss_enabled_with_no_negative": {
        "fields": {"pair_negative_count": 0},
        "expected_reason": "contrastive_loss_requires_at_least_one_negative",
    },
    "geometry_component_semantics_undefined": {
        "fields": {"geometry_contract_marked_resolved": True},
        "expected_reason": "incomplete_geometry_marked_resolved",
    },
    "geometry_unit_or_periodicity_missing": {
        "fields": {"geometry_units_and_periodicity_valid": False},
        "expected_reason": "geometry_units_or_periodicity_invalid",
    },
    "missing_geometry_label_participates_in_loss": {
        "fields": {"missing_geometry_excluded_from_loss": False},
        "expected_reason": "missing_geometry_included_in_loss",
    },
    "warhead_vocabulary_unresolved_but_marked_designed": {
        "fields": {"warhead_contract_marked_resolved": True},
        "expected_reason": "unresolved_warhead_vocabulary_marked_resolved",
    },
    "execution_boundary_crossed": {
        "fields": {"tensor_materialization_requested": True},
        "expected_reason": "execution_boundary_crossed",
    },
}


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() == "true"


def _git(repo_root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise ValueError(
            f"BASE-bound git read failed: {args!r}: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}"
        )
    return result.stdout


def _base_bytes(repo_root: Path, path: Path) -> bytes:
    name = path.as_posix()
    forbidden = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
        ".tgz", ".npz", ".tmp", ".part",
    }
    if name.startswith("data/raw/"):
        raise ValueError(f"raw source access forbidden: {name}")
    if path.suffix.lower() in forbidden:
        raise ValueError(f"artifact source access forbidden: {name}")
    _git(repo_root, "cat-file", "-e", f"{BASE_COMMIT}:{name}")
    return _git(repo_root, "show", f"{BASE_COMMIT}:{name}")


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _json(payload: bytes) -> dict[str, Any]:
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def _csv_scalar(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (tuple, list, dict)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


def _csv_bytes(
    columns: tuple[str, ...],
    rows: Sequence[dict[str, Any]],
) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=columns,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _csv_scalar(row.get(key, "")) for key in columns})
    return buffer.getvalue().encode("utf-8")


def _literal_assignment(source: bytes, name: str) -> Any:
    tree = ast.parse(source.decode("utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(
                isinstance(target, ast.Name) and target.id == name
                for target in targets
            ):
                return ast.literal_eval(node.value)
    raise ValueError(f"literal assignment missing: {name}")


def _is_ordered_offset_sequence_v1(offsets: object) -> bool:
    return (
        isinstance(offsets, Sequence)
        and not isinstance(
            offsets,
            (str, bytes, bytearray, memoryview),
        )
    )


def validate_offsets_v1(
    offsets: Sequence[int],
    flattened_node_count: int,
) -> bool:
    if (
        type(flattened_node_count) is not int
        or flattened_node_count < 0
        or not _is_ordered_offset_sequence_v1(offsets)
    ):
        return False
    try:
        values = tuple(offsets)
    except Exception:
        return False
    return (
        bool(values)
        and all(
            type(value) is int and value >= 0
            for value in values
        )
        and values[0] == 0
        and all(left <= right for left, right in zip(values, values[1:]))
        and values[-1] == flattened_node_count
    )


def flatten_local_index_v1(
    offsets: Sequence[int],
    batch_sample_index_0based: int,
    retained_heavy_local_index_0based: int,
) -> int:
    if type(batch_sample_index_0based) is not int:
        raise ValueError("batch sample index exact int required")
    if type(retained_heavy_local_index_0based) is not int:
        raise ValueError("retained-heavy local index exact int required")
    if not _is_ordered_offset_sequence_v1(offsets):
        raise ValueError("offset contract invalid")
    try:
        values = tuple(offsets)
    except Exception as error:
        raise ValueError("offset contract invalid") from error
    if not values or not validate_offsets_v1(values, values[-1]):
        raise ValueError("offset contract invalid")
    if (
        batch_sample_index_0based < 0
        or batch_sample_index_0based + 1 >= len(values)
    ):
        raise ValueError("batch sample index outside offsets")
    count = (
        values[batch_sample_index_0based + 1]
        - values[batch_sample_index_0based]
    )
    if (
        retained_heavy_local_index_0based < 0
        or retained_heavy_local_index_0based >= count
    ):
        raise ValueError("retained-heavy local index outside sample")
    return (
        values[batch_sample_index_0based]
        + retained_heavy_local_index_0based
    )


def validate_sentinel_with_validity_v1(value: int, valid: bool) -> bool:
    if type(value) is not int or type(valid) is not bool:
        return False
    return value >= 0 if valid else value == -1


def canonical_task_regions_v1(
    canonical_task_id: int,
) -> dict[str, tuple[str, ...] | bool]:
    if type(canonical_task_id) is not int:
        raise ValueError("canonical task id exact int required")
    rows = {
        0: {
            "target": ("warhead",),
            "context": ("scaffold", "linker"),
            "minimal_seed_or_anchor_context_override": False,
        },
        1: {
            "target": ("linker", "warhead"),
            "context": ("scaffold",),
            "minimal_seed_or_anchor_context_override": False,
        },
        2: {
            "target": ("scaffold", "warhead"),
            "context": ("linker",),
            "minimal_seed_or_anchor_context_override": False,
        },
        3: {
            "target": ("scaffold",),
            "context": ("linker", "warhead"),
            "minimal_seed_or_anchor_context_override": False,
        },
        4: {
            "target": ("scaffold", "linker", "warhead"),
            "context": ("minimal_seed_or_anchor",),
            "minimal_seed_or_anchor_context_override": True,
        },
    }
    if canonical_task_id not in rows:
        raise ValueError("canonical task id outside Exact5")
    return rows[canonical_task_id]


def mutation_signature_v1(fields: Mapping[str, Any]) -> str:
    if not fields:
        return "baseline"
    return "|".join(
        f"{name}={json.dumps(fields[name], sort_keys=True, separators=(',', ':'))}"
        for name in sorted(fields)
    )


def validate_pair_candidate_sample_spec_exact_types_v1(
    spec: PairCandidateSampleSpec,
) -> tuple[bool, tuple[str, ...]]:
    if type(spec) is not PairCandidateSampleSpec:
        return (
            False,
            ("pair_candidate_sample_spec_type_invalid",),
        )
    reasons: list[str] = []
    integer_fields = (
        "batch_sample_index_0based",
        "retained_ligand_count",
        "retained_pocket_count",
        "positive_ligand_local_index",
        "positive_pocket_local_index",
    )
    for name in integer_fields:
        if type(getattr(spec, name)) is not int:
            reasons.append(
                f"pair_candidate_sample_spec_field_type_invalid:{name}"
            )
    membership = spec.target_residue_pocket_local_indices
    if type(membership) is not tuple:
        reasons.append(
            "pair_candidate_sample_spec_field_type_invalid:"
            "target_residue_pocket_local_indices"
        )
    else:
        for ordinal, member in enumerate(membership):
            if type(member) is not int:
                reasons.append(
                    "pair_candidate_sample_spec_member_type_invalid:"
                    f"target_residue_pocket_local_indices[{ordinal}]"
                )
    return not reasons, tuple(reasons)


def _validate_dataclass_exact_scalar_types_v1(
    value: Any,
    baseline: Any,
    *,
    reason_prefix: str,
) -> tuple[bool, tuple[str, ...]]:
    if type(value) is not type(baseline):
        return False, (f"{reason_prefix}_type_invalid",)
    reasons: list[str] = []
    for field in dataclass_fields(baseline):
        expected_type = type(getattr(baseline, field.name))
        observed = getattr(value, field.name)
        if expected_type not in {bool, int} or type(observed) is not expected_type:
            reasons.append(
                f"{reason_prefix}_field_type_invalid:{field.name}"
            )
    return not reasons, tuple(reasons)


def validate_tensor_label_loss_mask_scenario_exact_types_v1(
    scenario: TensorLabelAndLossMaskContractScenario,
) -> tuple[bool, tuple[str, ...]]:
    return _validate_dataclass_exact_scalar_types_v1(
        scenario,
        BASELINE_SCENARIO,
        reason_prefix="scenario",
    )


def validate_pair_candidate_policy_scenario_exact_types_v1(
    scenario: PairCandidatePolicyScenario,
) -> tuple[bool, tuple[str, ...]]:
    return _validate_dataclass_exact_scalar_types_v1(
        scenario,
        BASELINE_PAIR_POLICY_SCENARIO,
        reason_prefix="pair_policy_scenario",
    )


def validate_mutation_registry_exact_types_v1(
    baseline: Any,
    mutations: Mapping[str, Mapping[str, Any]],
    *,
    registry_name: str,
) -> tuple[bool, tuple[str, ...]]:
    baseline_fields = {
        field.name: getattr(baseline, field.name)
        for field in dataclass_fields(baseline)
    }
    reasons: list[str] = []
    for case_id, mutation in mutations.items():
        mutation_fields = mutation.get("fields")
        if type(mutation_fields) is not dict:
            reasons.append(
                f"{registry_name}_mutation_fields_type_invalid:{case_id}"
            )
            continue
        for name, value in mutation_fields.items():
            if name not in baseline_fields:
                reasons.append(
                    f"{registry_name}_mutation_field_missing:"
                    f"{case_id}:{name}"
                )
            elif type(value) is not type(baseline_fields[name]):
                reasons.append(
                    f"{registry_name}_mutation_field_type_invalid:"
                    f"{case_id}:{name}"
                )
    return not reasons, tuple(reasons)


def build_pair_candidate_records_v1(
    sample_specs: Sequence[PairCandidateSampleSpec],
    ligand_node_offsets: Sequence[int],
    pocket_node_offsets: Sequence[int],
) -> PairCandidateProjection:
    specs = tuple(sample_specs)
    if not _is_ordered_offset_sequence_v1(ligand_node_offsets):
        raise ValueError("ligand node offsets invalid")
    if not _is_ordered_offset_sequence_v1(pocket_node_offsets):
        raise ValueError("pocket node offsets invalid")
    try:
        ligand_offsets = tuple(ligand_node_offsets)
        pocket_offsets = tuple(pocket_node_offsets)
    except Exception as error:
        raise ValueError("node offsets invalid") from error
    if not specs:
        raise ValueError("pair candidate sample specs must be nonempty")
    for spec in specs:
        exact_types_valid, type_reasons = (
            validate_pair_candidate_sample_spec_exact_types_v1(spec)
        )
        if not exact_types_valid:
            raise ValueError(";".join(type_reasons))
    if len(ligand_offsets) != len(specs) + 1:
        raise ValueError("ligand offsets must have shape [B+1]")
    if len(pocket_offsets) != len(specs) + 1:
        raise ValueError("pocket offsets must have shape [B+1]")
    ligand_total = sum(spec.retained_ligand_count for spec in specs)
    pocket_total = sum(spec.retained_pocket_count for spec in specs)
    if not validate_offsets_v1(ligand_offsets, ligand_total):
        raise ValueError("ligand node offsets invalid")
    if not validate_offsets_v1(pocket_offsets, pocket_total):
        raise ValueError("pocket node offsets invalid")

    records: list[PairCandidateRecord] = []
    pair_offsets = [0]
    positive_indices: list[int] = []
    positive_valid: list[bool] = []
    negative_counts: list[int] = []
    for batch_index, spec in enumerate(specs):
        if spec.batch_sample_index_0based != batch_index:
            raise ValueError("sample specs must follow batch order")
        if (
            type(spec.retained_ligand_count) is not int
            or spec.retained_ligand_count <= 0
            or type(spec.retained_pocket_count) is not int
            or spec.retained_pocket_count <= 0
        ):
            raise ValueError("retained-heavy sample counts must be positive")
        if (
            ligand_offsets[batch_index + 1] - ligand_offsets[batch_index]
            != spec.retained_ligand_count
            or pocket_offsets[batch_index + 1] - pocket_offsets[batch_index]
            != spec.retained_pocket_count
        ):
            raise ValueError("node offset delta does not match sample count")
        target_local = spec.target_residue_pocket_local_indices
        if (
            not target_local
            or target_local != tuple(sorted(set(target_local)))
            or any(
                type(index) is not int
                or index < 0
                or index >= spec.retained_pocket_count
                for index in target_local
            )
        ):
            raise ValueError(
                "target residue membership must be sorted unique pocket-local indices"
            )
        if (
            spec.positive_ligand_local_index < 0
            or spec.positive_ligand_local_index >= spec.retained_ligand_count
            or spec.positive_pocket_local_index not in target_local
        ):
            raise ValueError("positive pair is outside candidate domain")
        sample_start = len(records)
        target_member_ordinal = target_local.index(
            spec.positive_pocket_local_index
        )
        expected_positive_index = (
            sample_start
            + spec.positive_ligand_local_index * len(target_local)
            + target_member_ordinal
        )
        for ligand_local in range(spec.retained_ligand_count):
            for pocket_local in target_local:
                candidate_index = len(records)
                is_positive = (
                    ligand_local == spec.positive_ligand_local_index
                    and pocket_local == spec.positive_pocket_local_index
                )
                records.append(PairCandidateRecord(
                    pair_candidate_index_0based=candidate_index,
                    pair_candidate_batch_index=batch_index,
                    pair_candidate_ligand_local_index=ligand_local,
                    pair_candidate_residue_local_index=pocket_local,
                    pair_candidate_ligand_flat_index=(
                        ligand_offsets[batch_index] + ligand_local
                    ),
                    pair_candidate_pocket_flat_index=(
                        pocket_offsets[batch_index] + pocket_local
                    ),
                    pair_candidate_is_positive=is_positive,
                    pair_candidate_is_negative=not is_positive,
                ))
        sample_records = records[sample_start:]
        observed_positive = [
            row.pair_candidate_index_0based
            for row in sample_records
            if row.pair_candidate_is_positive
        ]
        if observed_positive != [expected_positive_index]:
            raise ValueError("positive global candidate index formula failed")
        positive_count = sum(
            row.pair_candidate_is_positive for row in sample_records
        )
        negative_count = len(sample_records) - positive_count
        if type(negative_count) is not int or negative_count < 0:
            raise ValueError("derived pair negative count must be nonnegative")
        pair_offsets.append(len(records))
        positive_indices.append(expected_positive_index)
        positive_valid.append(True)
        negative_counts.append(negative_count)

    record_tuple = tuple(records)
    if not validate_offsets_v1(pair_offsets, len(record_tuple)):
        raise ValueError("pair candidate offsets invalid")
    return PairCandidateProjection(
        records=record_tuple,
        pair_candidate_offsets=tuple(pair_offsets),
        pair_candidate_batch_index=tuple(
            row.pair_candidate_batch_index for row in record_tuple
        ),
        pair_candidate_ligand_local_index=tuple(
            row.pair_candidate_ligand_local_index for row in record_tuple
        ),
        pair_candidate_residue_local_index=tuple(
            row.pair_candidate_residue_local_index for row in record_tuple
        ),
        pair_candidate_ligand_flat_index=tuple(
            row.pair_candidate_ligand_flat_index for row in record_tuple
        ),
        pair_candidate_pocket_flat_index=tuple(
            row.pair_candidate_pocket_flat_index for row in record_tuple
        ),
        pair_candidate_is_positive=tuple(
            row.pair_candidate_is_positive for row in record_tuple
        ),
        pair_candidate_is_negative=tuple(
            row.pair_candidate_is_negative for row in record_tuple
        ),
        pair_positive_candidate_index=tuple(positive_indices),
        pair_positive_candidate_valid=tuple(positive_valid),
        pair_negative_count=tuple(negative_counts),
        pair_contrastive_sample_loss_mask=tuple(
            is_valid and negative_count >= 1
            for is_valid, negative_count in zip(
                positive_valid,
                negative_counts,
            )
        ),
    )


def evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
    scenario: PairCandidatePolicyScenario,
) -> PairCandidatePolicyObservation:
    exact_types_valid, type_reasons = (
        validate_pair_candidate_policy_scenario_exact_types_v1(scenario)
    )
    if not exact_types_valid:
        return PairCandidatePolicyObservation(
            candidate_allowed=False,
            label_semantics="invalid",
            negative_semantics="not_constructed",
            loss_mask_semantics="all_related_loss_masks_false",
            fails_closed=True,
            reasons=type_reasons,
        )
    reasons: list[str] = []
    if not scenario.same_sample:
        reasons.append("cross_sample_candidates_forbidden")
    if (
        scenario.contains_explicit_h
        or not scenario.ligand_retained_heavy
        or not scenario.residue_retained_heavy
    ):
        reasons.append("explicit_hydrogen_forbidden")
    if scenario.contains_padding:
        reasons.append("padding_forbidden")
    if not scenario.residue_is_target_member:
        reasons.append("residue_side_domain_is_target_residue_only")
    if scenario.source_full_table_index_used:
        reasons.append("source_index_cannot_enter_model_or_loss")
    if scenario.positive_candidate_duplicated:
        reasons.append("positive_candidate_must_not_be_duplicated")
    if scenario.positive_count < 0:
        reasons.append("positive_pair_count_negative")
    elif scenario.positive_count == 0:
        reasons.append("positive_pair_count_zero")
    elif scenario.positive_count > 1:
        reasons.append("positive_pair_count_greater_than_one")
    if not scenario.local_flat_consistent:
        reasons.append("local_to_flat_formula_must_hold")
    if not scenario.offsets_valid:
        reasons.append("offset_contract_must_hold")
    if not scenario.deterministic_order:
        reasons.append("candidate_order_must_be_deterministic")
    if scenario.cross_sample_negatives_allowed:
        reasons.append("cross_sample_negatives_forbidden")
    if scenario.random_negative_sampling:
        reasons.append("random_negative_sampling_forbidden_v1")
    if scenario.hard_negative_mining:
        reasons.append("hard_negative_mining_forbidden_v1")
    if not scenario.invalid_sample_excluded_from_loss:
        reasons.append("pair_loss_mask_includes_invalid_sample")
    if scenario.negative_count < 0:
        reasons.append("negative_pair_count_negative")
    elif (
        scenario.negative_count == 0
        and scenario.contrastive_sample_loss_mask_enabled
    ):
        reasons.append("contrastive_loss_requires_at_least_one_negative")

    contrastive_only = reasons == [
        "contrastive_loss_requires_at_least_one_negative"
    ]
    candidate_allowed = not reasons or contrastive_only
    if not candidate_allowed:
        label_semantics = "invalid"
        negative_semantics = "not_constructed"
        loss_mask_semantics = "all_related_loss_masks_false"
    elif scenario.candidate_is_positive:
        label_semantics = (
            "exact_positive_only" if contrastive_only else "exact_positive"
        )
        negative_semantics = (
            "empty_negative_set" if contrastive_only else "not_negative"
        )
        loss_mask_semantics = (
            "pair_head_may_be_valid_but_contrastive_sample_mask_false"
            if contrastive_only
            else "eligible_if_sample_admitted_and_indices_valid"
        )
    else:
        label_semantics = "non_positive"
        negative_semantics = "all_same_sample_non_positive_candidates"
        loss_mask_semantics = (
            "eligible_if_sample_admitted_and_indices_valid"
        )
    if not reasons:
        reasons.append(
            "valid_exact_positive_in_frozen_candidate_domain"
            if scenario.candidate_is_positive
            else "valid_deterministic_same_sample_negative"
        )
    return PairCandidatePolicyObservation(
        candidate_allowed=candidate_allowed,
        label_semantics=label_semantics,
        negative_semantics=negative_semantics,
        loss_mask_semantics=loss_mask_semantics,
        fails_closed=contrastive_only or not candidate_allowed,
        reasons=tuple(reasons),
    )


def build_pair_candidate_and_negative_policy_matrix_rows_v1(
) -> list[dict[str, Any]]:
    if tuple(PAIR_POLICY_MUTATIONS) != PAIR_POLICY_CASES:
        raise ValueError("pair policy mutation registry identity drift")
    registry_valid, registry_reasons = (
        validate_mutation_registry_exact_types_v1(
            BASELINE_PAIR_POLICY_SCENARIO,
            PAIR_POLICY_MUTATIONS,
            registry_name="pair_policy",
        )
    )
    if not registry_valid:
        raise ValueError(";".join(registry_reasons))
    rows: list[dict[str, Any]] = []
    for case_id, mutation in PAIR_POLICY_MUTATIONS.items():
        fields = mutation["fields"]
        scenario = replace(BASELINE_PAIR_POLICY_SCENARIO, **fields)
        observation = (
            evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
                scenario
            )
        )
        expected_reason = mutation["expected_reason"]
        verified = expected_reason in observation.reasons
        rows.append({
            "case_id": case_id,
            "input_condition": PAIR_POLICY_CONDITIONS[case_id],
            "mutation_signature": mutation_signature_v1(fields),
            "candidate_allowed": observation.candidate_allowed,
            "label_semantics": observation.label_semantics,
            "negative_semantics": observation.negative_semantics,
            "loss_mask_semantics": observation.loss_mask_semantics,
            "fails_closed": observation.fails_closed,
            "reason": expected_reason,
            "verified": verified,
        })
    return rows


def validate_checkpoint_sidecar_boundary_v1(
    scenario: TensorLabelAndLossMaskContractScenario,
) -> ContractSubvalidation:
    reasons: list[str] = []
    if scenario.checkpoint_atom_feature_width != 10:
        reasons.append("checkpoint_atom_feature_width_not_10")
    if not scenario.covalent_sidecars_separate:
        reasons.append("covalent_sidecars_not_separate")
    if not scenario.explicit_h_excluded:
        reasons.append("explicit_hydrogen_not_excluded")
    if not scenario.unsupported_non_h_rejected:
        reasons.append("unsupported_non_hydrogen_not_rejected")
    if not scenario.missing_or_invalid_symbol_rejected:
        reasons.append("missing_or_invalid_symbol_not_rejected")
    return ContractSubvalidation(not reasons, not reasons, tuple(reasons))


def _validate_index_and_offset_contract_v1(
    scenario: TensorLabelAndLossMaskContractScenario,
) -> ContractSubvalidation:
    reasons: list[str] = []
    if scenario.source_full_table_index_model_or_loss_used:
        reasons.append("source_full_table_index_used_as_heavy_index")
    if not scenario.exact_index_spaces_present:
        reasons.append("exact_index_spaces_missing")
    if not scenario.index_space_annotations_complete:
        reasons.append("index_space_annotations_incomplete")
    if not scenario.ligand_offsets_present:
        reasons.append("ligand_node_offsets_missing")
    if not scenario.pocket_offsets_present:
        reasons.append("pocket_node_offsets_missing")
    if not scenario.pair_offsets_present:
        reasons.append("pair_candidate_offsets_missing")
    if not scenario.offsets_valid:
        reasons.append("offsets_invalid")
    if not scenario.local_flat_relations_valid:
        reasons.append("local_flat_relations_invalid")
    return ContractSubvalidation(not reasons, not reasons, tuple(reasons))


def validate_task_mask_partition_v1(
    scenario: TensorLabelAndLossMaskContractScenario,
) -> ContractSubvalidation:
    reasons: list[str] = []
    if scenario.canonical_task_count != 5:
        reasons.append("canonical_task_count_not_5")
    if not scenario.b3_present:
        reasons.append("scaffold_only_b3_missing")
    if not scenario.long_semantic_names_authoritative:
        reasons.append("long_semantic_names_not_authoritative")
    if (
        not scenario.role_vocabulary_frozen
        and scenario.role_dependent_masks_marked_designed
    ):
        reasons.append("unresolved_role_vocabulary_marked_designed")
    if (
        not scenario.role_assignments_complete
        and scenario.role_dependent_masks_marked_designed
    ):
        reasons.append("incomplete_role_assignments_marked_designed")
    if not scenario.generation_equals_target:
        reasons.append("generation_mask_not_equal_target_mask")
    if not scenario.fixed_equals_context:
        reasons.append("fixed_mask_not_equal_context_mask")
    if not scenario.generation_fixed_masks_disjoint:
        reasons.append("generation_fixed_masks_overlap")
    if not scenario.generation_fixed_masks_exhaustive:
        reasons.append("generation_fixed_masks_not_exhaustive")
    if not scenario.target_context_masks_disjoint:
        reasons.append("target_context_masks_overlap")
    if not scenario.target_context_masks_exhaustive:
        reasons.append("target_context_masks_not_exhaustive")
    if (
        scenario.c_seed_override_marked_resolved
        and not scenario.minimal_seed_authority_present
    ):
        reasons.append(
            "c_minimal_seed_or_anchor_resolved_without_authority"
        )
    resolved = (
        not reasons
        and scenario.role_vocabulary_frozen
        and scenario.role_assignments_complete
        and scenario.role_dependent_masks_marked_designed
        and scenario.minimal_seed_authority_present
        and scenario.c_seed_override_marked_resolved
    )
    return ContractSubvalidation(not reasons, resolved, tuple(reasons))


def validate_target_residue_condition_contract_v1(
    scenario: TensorLabelAndLossMaskContractScenario,
) -> ContractSubvalidation:
    reasons: list[str] = []
    if not scenario.target_residue_membership_nonempty:
        reasons.append("target_residue_membership_empty")
    if not scenario.reactive_atom_inside_target_residue:
        reasons.append("reactive_atom_outside_target_residue")
    return ContractSubvalidation(not reasons, not reasons, tuple(reasons))


def _validate_pair_candidate_contract_v1(
    scenario: TensorLabelAndLossMaskContractScenario,
) -> ContractSubvalidation:
    reasons: list[str] = []
    if not scenario.pair_candidate_domain_valid:
        reasons.append("pair_candidate_domain_invalid")
    pair_scenario = PairCandidatePolicyScenario(
        same_sample=scenario.pair_candidates_same_sample,
        ligand_retained_heavy=scenario.pair_candidates_retained_heavy,
        residue_retained_heavy=scenario.pair_candidates_retained_heavy,
        residue_is_target_member=(
            scenario.pair_candidates_target_residue_only
        ),
        contains_explicit_h=not scenario.pair_candidates_retained_heavy,
        local_flat_consistent=scenario.pair_local_flat_indices_valid,
        offsets_valid=scenario.pair_candidate_offsets_valid,
        positive_count=scenario.pair_positive_count,
        negative_count=scenario.pair_negative_count,
        deterministic_order=scenario.pair_candidate_order_valid,
        cross_sample_negatives_allowed=(
            scenario.cross_sample_negatives_allowed
        ),
        random_negative_sampling=scenario.random_negative_sampling,
        hard_negative_mining=scenario.hard_negative_mining,
        invalid_sample_excluded_from_loss=(
            scenario.pair_loss_masks_exclude_invalid_samples
        ),
        contrastive_sample_loss_mask_enabled=(
            scenario.contrastive_sample_loss_mask_enabled
        ),
    )
    observation = (
        evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
            pair_scenario
        )
    )
    valid_success_reasons = {
        "valid_exact_positive_in_frozen_candidate_domain",
        "valid_deterministic_same_sample_negative",
    }
    reasons.extend(
        reason for reason in observation.reasons
        if reason not in valid_success_reasons
    )
    return ContractSubvalidation(not reasons, not reasons, tuple(reasons))


def validate_geometry_component_contract_v1(
    scenario: TensorLabelAndLossMaskContractScenario,
) -> ContractSubvalidation:
    reasons: list[str] = []
    if (
        not scenario.geometry_components_semantically_complete
        and scenario.geometry_contract_marked_resolved
    ):
        reasons.append("incomplete_geometry_marked_resolved")
    if not scenario.geometry_units_and_periodicity_valid:
        reasons.append("geometry_units_or_periodicity_invalid")
    if not scenario.missing_geometry_excluded_from_loss:
        reasons.append("missing_geometry_included_in_loss")
    resolved = (
        not reasons
        and scenario.geometry_components_semantically_complete
        and scenario.geometry_contract_marked_resolved
    )
    return ContractSubvalidation(not reasons, resolved, tuple(reasons))


def validate_auxiliary_label_and_loss_mask_contract_v1(
    scenario: TensorLabelAndLossMaskContractScenario,
) -> ContractSubvalidation:
    geometry = validate_geometry_component_contract_v1(scenario)
    reasons = list(geometry.reasons)
    if (
        not scenario.warhead_vocabulary_frozen
        and scenario.warhead_contract_marked_resolved
    ):
        reasons.append("unresolved_warhead_vocabulary_marked_resolved")
    resolved = (
        not reasons
        and scenario.warhead_vocabulary_frozen
        and scenario.warhead_contract_marked_resolved
        and geometry.resolved
    )
    return ContractSubvalidation(not reasons, resolved, tuple(reasons))


def validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
    scenario: TensorLabelAndLossMaskContractScenario,
) -> TensorLabelAndLossMaskContractScenarioObservation:
    exact_types_valid, type_reasons = (
        validate_tensor_label_loss_mask_scenario_exact_types_v1(scenario)
    )
    if not exact_types_valid:
        return TensorLabelAndLossMaskContractScenarioObservation(
            outcome="invalid",
            reasons=type_reasons,
            condition_contract_resolved=False,
            pair_contract_resolved=False,
            geometry_and_auxiliary_label_contract_resolved=False,
            tensor_label_loss_mask_contract_designed=False,
            ready_for_tensor_materialization_smoke=False,
            ready_for_tensorization=False,
            ready_for_model_integration=False,
            ready_for_training=False,
            fails_closed=True,
        )
    predecessor_reasons: list[str] = []
    if not scenario.predecessor_sha_valid:
        predecessor_reasons.append("predecessor_sha_invalid")
    if not scenario.predecessor_contract_design_ready:
        predecessor_reasons.append("predecessor_contract_design_not_ready")
    if scenario.predecessor_effective_open_issue_count != 0:
        predecessor_reasons.append(
            "predecessor_effective_open_issue_count_not_zero"
        )
    checkpoint = validate_checkpoint_sidecar_boundary_v1(scenario)
    indices = _validate_index_and_offset_contract_v1(scenario)
    task = validate_task_mask_partition_v1(scenario)
    target = validate_target_residue_condition_contract_v1(scenario)
    pair = _validate_pair_candidate_contract_v1(scenario)
    auxiliary = validate_auxiliary_label_and_loss_mask_contract_v1(scenario)
    execution_boundary_crossed = any((
        scenario.tensor_materialization_requested,
        scenario.dataloader_changed,
        scenario.model_changed,
        scenario.forward_changed,
        scenario.loss_changed,
        scenario.checkpoint_accessed,
        scenario.training_used,
    ))
    invalid_reasons = tuple(dict.fromkeys(
        predecessor_reasons
        + list(checkpoint.reasons)
        + list(indices.reasons)
        + list(task.reasons)
        + list(target.reasons)
        + list(pair.reasons)
        + list(auxiliary.reasons)
        + (
            ["execution_boundary_crossed"]
            if execution_boundary_crossed else []
        )
    ))
    condition_resolved = (
        task.resolved and target.resolved and indices.resolved
    )
    pair_resolved = pair.resolved and indices.resolved
    auxiliary_resolved = auxiliary.resolved
    designed = (
        not invalid_reasons
        and condition_resolved
        and pair_resolved
        and auxiliary_resolved
    )
    if invalid_reasons:
        outcome = "invalid"
        reasons = invalid_reasons
    elif designed:
        outcome = "designed_contract"
        reasons = ()
    else:
        outcome = "designed_with_blockers"
        blockers: list[str] = []
        if not condition_resolved:
            blockers.append(
                "current11_per_atom_role_and_minimal_seed_authority_missing"
            )
        if not scenario.warhead_vocabulary_frozen:
            blockers.append("current11_warhead_type_vocabulary_missing")
        if not scenario.geometry_components_semantically_complete:
            blockers.append("complete_pre_post_geometry_contract_missing")
        reasons = tuple(blockers)
    return TensorLabelAndLossMaskContractScenarioObservation(
        outcome=outcome,
        reasons=reasons,
        condition_contract_resolved=condition_resolved,
        pair_contract_resolved=pair_resolved,
        geometry_and_auxiliary_label_contract_resolved=(
            auxiliary_resolved
        ),
        tensor_label_loss_mask_contract_designed=designed,
        ready_for_tensor_materialization_smoke=designed,
        ready_for_tensorization=False,
        ready_for_model_integration=False,
        ready_for_training=False,
        fails_closed=True,
    )


def build_failure_matrix_rows_v1() -> list[dict[str, Any]]:
    if tuple(FAILURE_MUTATIONS) != FAILURE_CASES:
        raise ValueError("failure mutation registry identity drift")
    registry_valid, registry_reasons = (
        validate_mutation_registry_exact_types_v1(
            BASELINE_SCENARIO,
            FAILURE_MUTATIONS,
            registry_name="failure",
        )
    )
    if not registry_valid:
        raise ValueError(";".join(registry_reasons))
    rows: list[dict[str, Any]] = []
    signatures: set[str] = set()
    for case_id, mutation in FAILURE_MUTATIONS.items():
        fields = mutation["fields"]
        if not fields or any(
            getattr(BASELINE_SCENARIO, name) == value
            for name, value in fields.items()
        ):
            raise ValueError(f"failure mutation does not change state: {case_id}")
        signature = mutation_signature_v1(fields)
        if signature in signatures:
            raise ValueError(f"failure mutation signature duplicated: {case_id}")
        signatures.add(signature)
        scenario = replace(BASELINE_SCENARIO, **fields)
        observation = (
            validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
                scenario
            )
        )
        expected_reason = mutation["expected_reason"]
        failure_detected = (
            observation.outcome == "invalid"
            and expected_reason in observation.reasons
        )
        rows.append({
            "failure_case": case_id,
            "expected_outcome": "invalid",
            "observed_outcome": observation.outcome,
            "expected_primary_reason": expected_reason,
            "observed_reasons": list(observation.reasons),
            "mutation_signature": signature,
            "failure_detected": failure_detected,
            "condition_contract_resolved": (
                observation.condition_contract_resolved
            ),
            "pair_contract_resolved": observation.pair_contract_resolved,
            "geometry_and_auxiliary_label_contract_resolved": (
                observation.geometry_and_auxiliary_label_contract_resolved
            ),
            "tensor_label_loss_mask_contract_designed": (
                observation.tensor_label_loss_mask_contract_designed
            ),
            "ready_for_tensor_materialization_smoke": (
                observation.ready_for_tensor_materialization_smoke
            ),
            "ready_for_tensorization": observation.ready_for_tensorization,
            "ready_for_model_integration": (
                observation.ready_for_model_integration
            ),
            "ready_for_training": observation.ready_for_training,
            "fails_closed": observation.fails_closed,
            "verified": (
                failure_detected
                and observation.fails_closed
                and not observation.ready_for_tensor_materialization_smoke
                and not observation.ready_for_tensorization
                and not observation.ready_for_model_integration
                and not observation.ready_for_training
            ),
        })
    return rows


def _verify_predecessor(
    repo_root: Path,
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    payloads = {path: _base_bytes(repo_root, path) for path in FROZEN_SHA256}
    for path, expected in FROZEN_SHA256.items():
        if _sha(payloads[path]) != expected:
            raise ValueError(f"frozen predecessor SHA drift: {path}")
    manifest = _json(payloads[PREDECESSOR_MANIFEST])
    expected = {
        "policy_resolution_completed": True,
        "resolution_outcome": "resolved_policy_contract",
        "source_atom_row_count": 2870,
        "retained_heavy_atom_row_count": 2525,
        "excluded_explicit_hydrogen_row_count": 345,
        "unsupported_nonhydrogen_row_count": 0,
        "missing_or_invalid_symbol_row_count": 0,
        "feature_semantics_known": True,
        "unknown_atom_feature_policy_resolved": True,
        "unknown_atom_policy_contract_resolved": True,
        "unknown_atom_runtime_enforcement_integrated": False,
        "effective_open_issue_count": 0,
        "effective_open_issues": [],
        "checkpoint_categorical_width": 10,
        "checkpoint_channel_order_preserved": True,
        "preview_11d_checkpoint_authority": False,
        "silent_zero_vector_fallback_allowed": False,
        "ready_for_tensor_label_loss_mask_contract_design": True,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
    }
    drift = {
        key: (manifest.get(key), value)
        for key, value in expected.items()
        if manifest.get(key) != value
    }
    if drift:
        raise ValueError(f"predecessor manifest contract drift: {drift!r}")
    issue_rows = _csv_rows(payloads[PREDECESSOR_ISSUES])
    effective_open = [
        row["issue_id"]
        for row in issue_rows
        if row["successor_effective_status"] == "open"
    ]
    if len(issue_rows) != 32 or effective_open:
        raise ValueError("predecessor effective issue set drift")
    return payloads, manifest


def _static_source_specs(
) -> tuple[tuple[Path, str, str, str, int], ...]:
    return (
        (PREDECESSOR_SOURCE, "unknown_policy_resolution_source", "python", "frozen predecessor source", 8),
        (PREDECESSOR_MANIFEST, "unknown_policy_resolution_manifest", "json", "resolved feature and unknown-atom policy", 18),
        (PREDECESSOR_ISSUES, "unknown_policy_resolution_issue_inventory", "csv", "Exact32 inherited issue rows", 3),
        (HEAVY_DISPOSITION, "heavy_atom_disposition_and_projection", "csv", "2870 explicit type_symbol dispositions", 11),
        (SAMPLE_PROJECTION, "sample_heavy_atom_projection", "csv", "11 retained-heavy sample projections and pair remaps", 19),
        (FINAL_DATASET_INDEX, "final_dataset_index", "csv", "11 canonical sample paths, residue locators, and bond distances", 18),
        (ATOM_PAIR_MAPPING, "atom_pair_mapping_authority", "csv", "22 exact-one source-row mappings", 14),
        (ATOM_PAIR_MANIFEST, "canonical_task_and_pair_authority", "json", "Exact5 masks and 11 validated pairs", 11),
        (ROLE_MASK_SOURCE, "canonical_role_and_mask_authority", "python", "LONG_FORM_MASK_COMPONENTS and build_long_form_mask", 7),
        (ROLE_SCHEMA_SOURCE, "legacy_role_warhead_schema_boundary", "python", "CovalentSample role lists and warhead_type field", 4),
        (B3_PROTOCOL, "b3_role_mask_authority", "json", "B3 scaffold target and linker+warhead context", 4),
        (ROLE_SCHEMA_DOC, "role_mask_documentation_authority", "markdown", "canonical long-form role/mask table", 4),
        (COORDINATE_GEOMETRY_AUDIT, "pre_post_geometry_authority", "csv", "post bond distance present; pre geometry absent", 5),
        (AUXILIARY_LABEL_AUDIT, "warhead_and_geometry_label_gap_authority", "csv", "warhead not materialized; post geometry audit required", 5),
        (FINAL_DATASET_SCHEMA, "final_dataset_schema_authority", "csv", "current canonical field boundary", 8),
        (CHECKPOINT_CONFIG, "checkpoint_training_config", "yaml", "crossdock noH full-atom 10D lineage", 6),
        (CONSTANTS_SOURCE, "checkpoint_categorical_vocabulary", "python", "dataset_params crossdock atom_encoder", 2),
        (NPZ_ADAPTER, "current_collate_adapter", "python", "covalent_npz_collate_fn reference only", 8),
        (BATCH_ADAPTER, "current_batch_adapter", "python", "mask and centering adapter reference only", 12),
        (DIFFSBDD_ADAPTER, "current_diffsbdd_input_adapter", "python", "flatten and batch-membership reference only", 10),
        (MODEL_INPUT_ADAPTER, "current_model_input_adapter", "python", "10D model input builder reference only", 6),
        (LIGHTNING_CONSUMER, "current_model_input_consumer", "python", "LigandPocketDDPM.forward reference only", 6),
        (DYNAMICS_CONSUMER, "current_dynamics_consumer", "python", "EGNNDynamics.forward reference only", 6),
        (DIFFUSION_CONSUMER, "current_diffusion_consumer", "python", "normalize/forward/inpaint reference only", 6),
        (STEP12D_LINEAGE, "step12d_checkpoint_10d_lineage", "python", "smoke legality lineage; not final feature contract", 6),
    )


def _load_sources(
    repo_root: Path,
    fixed_payloads: dict[Path, bytes],
) -> dict[str, Any]:
    payloads = dict(fixed_payloads)
    specs: dict[Path, tuple[str, str, str, int, int]] = {}
    for path, role, kind, selector, count in _static_source_specs():
        if path not in payloads:
            payloads[path] = _base_bytes(repo_root, path)
        specs[path] = (role, kind, selector, count, 0)
    final_rows = _csv_rows(payloads[FINAL_DATASET_INDEX])
    if len(final_rows) != 11:
        raise ValueError("canonical current sample count drift")
    table_payloads: dict[Path, bytes] = {}
    table_rows: dict[Path, list[dict[str, str]]] = {}
    for sample in final_rows:
        dynamic = (
            ("current11_ligand_atom_table", "ligand_atom_table_path", 15),
            ("current11_pocket_atom_table", "pocket_atom_table_path", 17),
            ("current11_positive_pair_table", "ligand_residue_atom_pair_table_path", 8),
            ("current11_covalent_event_table", "covalent_event_table_path", 4),
        )
        for role, column, contract_count in dynamic:
            path = Path(sample[column])
            name = path.as_posix()
            if not name.startswith("data/derived/covalent_small/"):
                raise ValueError(f"current source escaped derived boundary: {path}")
            if path not in table_payloads:
                payload = _base_bytes(repo_root, path)
                rows = _csv_rows(payload)
                if not rows:
                    raise ValueError(f"empty current11 source: {path}")
                table_payloads[path] = payload
                table_rows[path] = rows
                payloads[path] = payload
                specs[path] = (
                    role,
                    "csv",
                    "BASE-bound current11 committed derived table",
                    contract_count,
                    1,
                )
    return {
        "payloads": payloads,
        "specs": specs,
        "final_rows": final_rows,
        "table_rows": table_rows,
    }


def _discover_role_contract(payloads: dict[Path, bytes]) -> dict[str, Any]:
    components = _literal_assignment(
        payloads[ROLE_MASK_SOURCE], "LONG_FORM_MASK_COMPONENTS"
    )
    expected_keys = (
        "A_warhead_only",
        "B_linker_warhead",
        "B2_scaffold_warhead",
        "B3_scaffold_only",
        "C_scaffold_linker_warhead",
    )
    if tuple(components) != expected_keys:
        raise ValueError("committed role/mask authority task order drift")
    tree = ast.parse(payloads[ROLE_MASK_SOURCE].decode("utf-8"))
    role_vocabulary: tuple[str, ...] | None = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            node.name == "build_long_form_mask"
        ):
            names = [argument.arg for argument in node.args.args]
            role_vocabulary = tuple(
                name.removesuffix("_atoms") for name in names[1:4]
            )
            break
    if role_vocabulary != ("scaffold", "linker", "warhead"):
        raise ValueError("role vocabulary could not be frozen from authority")
    expected_regions = {
        0: (("warhead",), ("scaffold", "linker")),
        1: (("linker", "warhead"), ("scaffold",)),
        2: (("scaffold", "warhead"), ("linker",)),
        3: (("scaffold",), ("linker", "warhead")),
        4: (("scaffold", "linker", "warhead"), ()),
    }
    for task_id, key in enumerate(expected_keys):
        row = components[key]
        if (
            tuple(row["target"]),
            tuple(row["context"]),
        ) != expected_regions[task_id]:
            raise ValueError("role-to-mask truth table drift")
    return {
        "role_vocabulary": role_vocabulary,
        "role_vocabulary_frozen": True,
        "role_to_task_truth_table_frozen": True,
        "minimal_seed_or_anchor_authority_present": False,
    }


def _retained_projection(
    rows: Sequence[dict[str, str]],
) -> tuple[tuple[bool, ...], tuple[int | None, ...]]:
    keep = tuple(row.get("type_symbol") in SUPPORTED_HEAVY_SYMBOLS for row in rows)
    mapping: list[int | None] = []
    next_index = 0
    for retained in keep:
        mapping.append(next_index if retained else None)
        if retained:
            next_index += 1
    return keep, tuple(mapping)


def _analyze_current_samples(
    source_data: dict[str, Any],
    fixed_payloads: dict[Path, bytes],
) -> dict[str, Any]:
    final_rows = source_data["final_rows"]
    table_rows = source_data["table_rows"]
    projection_rows = {
        row["sample_index_row_id"]: row
        for row in _csv_rows(fixed_payloads[SAMPLE_PROJECTION])
    }
    mapping_rows = _csv_rows(fixed_payloads[ATOM_PAIR_MAPPING])
    mapping_by_identity = {
        (row["sample_index_row_id"], row["entity_role"]): row
        for row in mapping_rows
    }
    if len(mapping_by_identity) != 22:
        raise ValueError("atom-pair mapping identity drift")
    sample_evidence: list[dict[str, Any]] = []
    sample_specs: list[PairCandidateSampleSpec] = []
    ligand_node_offsets = [0]
    pocket_node_offsets = [0]
    pair_candidate_total = 0
    pair_offset = 0
    ligand_offset = 0
    pocket_offset = 0
    role_fields_present: set[str] = set()
    warhead_fields_present: set[str] = set()
    geometry_fields_present: set[str] = set()
    for batch_index, sample in enumerate(final_rows):
        sample_id = sample["sample_index_row_id"]
        ligand_path = Path(sample["ligand_atom_table_path"])
        pocket_path = Path(sample["pocket_atom_table_path"])
        pair_path = Path(sample["ligand_residue_atom_pair_table_path"])
        event_path = Path(sample["covalent_event_table_path"])
        ligand_rows = table_rows[ligand_path]
        pocket_rows = table_rows[pocket_path]
        pair_rows = table_rows[pair_path]
        event_rows = table_rows[event_path]
        all_fields = set(ligand_rows[0]) | set(pocket_rows[0])
        role_fields_present.update({
            field for field in all_fields
            if field in {
                "ligand_role", "atom_role", "scaffold_atoms",
                "linker_atoms", "warhead_atoms", "minimal_seed_atoms",
                "anchor_atoms",
            }
        })
        warhead_fields_present.update({
            field for field in all_fields | set(pair_rows[0]) | set(event_rows[0])
            if field in {"warhead_type", "warhead_class", "warhead_type_label"}
        })
        geometry_fields_present.update({
            field
            for field in set(pair_rows[0]) | set(event_rows[0]) | set(sample)
            if any(
                token in field.lower()
                for token in ("distance", "angle", "dihedral", "geometry")
            )
        })
        ligand_keep, ligand_map = _retained_projection(ligand_rows)
        pocket_keep, pocket_map = _retained_projection(pocket_rows)
        retained_ligand_count = sum(ligand_keep)
        retained_pocket_count = sum(pocket_keep)
        projection = projection_rows[sample_id]
        if (
            retained_ligand_count
            != int(projection["retained_ligand_heavy_count"])
            or retained_pocket_count
            != int(projection["retained_pocket_heavy_count"])
        ):
            raise ValueError("retained-heavy count drift")
        target_source_indices = [
            index
            for index, row in enumerate(pocket_rows)
            if (
                row["residue_name"] == sample["covalent_residue_name"]
                and row["chain_id"] == sample["covalent_residue_chain_id"]
                and row["residue_index"] == sample["covalent_residue_index"]
                and pocket_keep[index]
            )
        ]
        target_pocket_local_indices = tuple(
            int(pocket_map[index]) for index in target_source_indices
            if pocket_map[index] is not None
        )
        if not target_pocket_local_indices:
            raise ValueError("target residue retained-heavy membership empty")
        residue_mapping = mapping_by_identity[
            (sample_id, "target_residue_atom")
        ]
        ligand_mapping = mapping_by_identity[(sample_id, "ligand_atom")]
        residue_source_index = int(residue_mapping["matched_row_index_0based"])
        ligand_source_index = int(ligand_mapping["matched_row_index_0based"])
        residue_local = pocket_map[residue_source_index]
        ligand_local = ligand_map[ligand_source_index]
        if (
            residue_local is None
            or ligand_local is None
            or int(residue_local) not in target_pocket_local_indices
            or int(residue_local)
            != int(projection["projected_residue_pair_row_index_0based"])
            or int(ligand_local)
            != int(projection["projected_ligand_pair_row_index_0based"])
        ):
            raise ValueError("positive retained-heavy remap drift")
        target_position = target_pocket_local_indices.index(int(residue_local))
        candidate_count = (
            retained_ligand_count * len(target_pocket_local_indices)
        )
        positive_candidate_index = (
            pair_offset
            + int(ligand_local) * len(target_pocket_local_indices)
            + target_position
        )
        positive_count = sum(
            1
            for ligand_candidate in range(retained_ligand_count)
            for pocket_candidate in target_pocket_local_indices
            if (
                ligand_candidate == int(ligand_local)
                and pocket_candidate == int(residue_local)
            )
        )
        if positive_count != 1:
            raise ValueError("positive candidate count is not exact-one")
        if len(pair_rows) != 1:
            raise ValueError("positive pair table count drift")
        pair_distance = float(pair_rows[0]["bond_distance_angstrom"])
        index_distance = float(sample["bond_distance_angstrom"])
        if (
            not math.isfinite(pair_distance)
            or not math.isclose(pair_distance, index_distance, abs_tol=1e-6)
        ):
            raise ValueError("post-covalent bond distance drift")
        for coordinate_fields, row in (
            (("x", "y", "z"), ligand_rows[ligand_source_index]),
            (("x", "y", "z"), pocket_rows[residue_source_index]),
        ):
            if not all(
                math.isfinite(float(row[field])) for field in coordinate_fields
            ):
                raise ValueError("reactive atom coordinate is not finite")
        sample_evidence.append({
            "sample_index_row_id": sample_id,
            "batch_sample_index_0based": batch_index,
            "retained_ligand_heavy_count": retained_ligand_count,
            "retained_pocket_heavy_count": retained_pocket_count,
            "target_residue_retained_heavy_count": (
                len(target_pocket_local_indices)
            ),
            "target_residue_pocket_local_indices": (
                target_pocket_local_indices
            ),
            "positive_ligand_local_index": int(ligand_local),
            "positive_pocket_local_index": int(residue_local),
            "positive_candidate_index": positive_candidate_index,
            "candidate_count": candidate_count,
            "negative_count": candidate_count - 1,
            "ligand_node_offset": ligand_offset,
            "pocket_node_offset": pocket_offset,
            "post_covalent_bond_distance_angstrom": index_distance,
        })
        sample_specs.append(PairCandidateSampleSpec(
            batch_sample_index_0based=batch_index,
            retained_ligand_count=retained_ligand_count,
            retained_pocket_count=retained_pocket_count,
            target_residue_pocket_local_indices=(
                target_pocket_local_indices
            ),
            positive_ligand_local_index=int(ligand_local),
            positive_pocket_local_index=int(residue_local),
        ))
        pair_candidate_total += candidate_count
        pair_offset += candidate_count
        ligand_offset += retained_ligand_count
        pocket_offset += retained_pocket_count
        ligand_node_offsets.append(ligand_offset)
        pocket_node_offsets.append(pocket_offset)
    if (
        pair_candidate_total != 1938
        or ligand_offset != 323
        or pocket_offset != 2202
        or any(row["negative_count"] < 1 for row in sample_evidence)
    ):
        raise ValueError("current11 pair candidate aggregate drift")
    pair_projection = build_pair_candidate_records_v1(
        sample_specs,
        ligand_node_offsets,
        pocket_node_offsets,
    )
    if (
        len(pair_projection.records) != pair_candidate_total
        or tuple(
            row["positive_candidate_index"] for row in sample_evidence
        ) != pair_projection.pair_positive_candidate_index
        or tuple(
            row["negative_count"] for row in sample_evidence
        ) != pair_projection.pair_negative_count
        or not all(pair_projection.pair_positive_candidate_valid)
        or pair_projection.pair_contrastive_sample_loss_mask
        != (True,) * len(sample_specs)
    ):
        raise ValueError("pair candidate projection drift")
    return {
        "sample_evidence": sample_evidence,
        "pair_candidate_sample_specs": tuple(sample_specs),
        "ligand_node_offsets": tuple(ligand_node_offsets),
        "pocket_node_offsets": tuple(pocket_node_offsets),
        "pair_candidate_offsets": pair_projection.pair_candidate_offsets,
        "pair_projection": pair_projection,
        "pair_candidate_total": pair_candidate_total,
        "pair_positive_exact_one_verified": True,
        "pair_candidate_policy_frozen": True,
        "pair_negative_policy_frozen": True,
        "pair_candidate_offsets_contract_frozen": True,
        "pair_local_to_flat_relations_verified": all(
            row.pair_candidate_ligand_flat_index
            == ligand_node_offsets[row.pair_candidate_batch_index]
            + row.pair_candidate_ligand_local_index
            and row.pair_candidate_pocket_flat_index
            == pocket_node_offsets[row.pair_candidate_batch_index]
            + row.pair_candidate_residue_local_index
            for row in pair_projection.records
        ),
        "pair_positive_global_index_formula_verified": True,
        "pair_contrastive_sample_loss_mask": (
            pair_projection.pair_contrastive_sample_loss_mask
        ),
        "target_residue_condition_current_valid_sample_count": 11,
        "role_fields_present": tuple(sorted(role_fields_present)),
        "warhead_fields_present": tuple(sorted(warhead_fields_present)),
        "geometry_fields_present": tuple(sorted(geometry_fields_present)),
        "warhead_type_vocabulary": (),
        "warhead_type_current_valid_sample_count": 0,
        "geometry_component_count": 1,
        "geometry_current_valid_sample_count": 11,
        "geometry_contract_frozen": False,
    }


def _contract_row(
    contract_id: str,
    category: str,
    semantic_name: str,
    module_consumer: str,
    *,
    status: str = "designed",
    source: str,
    derivation: str,
    dtype: str,
    rank: int,
    shape: str,
    width: str | int = 1,
    index_space: str = "not_applicable",
    local_or_flat: str = "not_applicable",
    padding: str = "no_padding_admitted",
    sentinel: str = "not_applicable",
    domain: str = "contract_defined",
    unit: str = "not_applicable",
    frame: str = "not_applicable",
    scaling: str = "none",
    availability: str = "always_for_admitted_sample",
    loss_mask: str = "not_a_loss_mask",
    sidecar: bool = True,
    geometry_component_id: str = "",
    pre_post_or_delta: str = "",
    periodicity: str = "",
    canonical_range: str = "",
    representation: str = "",
    valid_count: int | str = "",
    evidence_status: str = "BASE_bound_verified",
    blocker: str = "",
) -> dict[str, Any]:
    if category not in CONTRACT_CATEGORIES or status not in CONTRACT_STATUSES:
        raise ValueError("contract registry closed vocabulary violation")
    return {
        "contract_id": contract_id,
        "contract_category": category,
        "semantic_name": semantic_name,
        "module_consumer": module_consumer,
        "contract_status": status,
        "source_fields_or_contract": source,
        "derivation_rule": derivation,
        "dtype": dtype,
        "rank": rank,
        "shape": shape,
        "width_or_component_count": width,
        "index_space": index_space,
        "local_or_flat": local_or_flat,
        "padding_semantics": padding,
        "sentinel_semantics": sentinel,
        "value_domain_or_vocabulary": domain,
        "unit": unit,
        "coordinate_frame": frame,
        "normalization_or_scaling": scaling,
        "label_availability_semantics": availability,
        "loss_mask_semantics": loss_mask,
        "sidecar_only": sidecar,
        "changes_checkpoint_input_width": False,
        "materialized_current_step": False,
        "geometry_component_id": geometry_component_id,
        "pre_post_or_delta": pre_post_or_delta,
        "periodic_or_nonperiodic": periodicity,
        "canonical_range": canonical_range,
        "target_representation": representation,
        "current_valid_sample_count": valid_count,
        "evidence_status": evidence_status,
        "blocking_reason": blocker,
        "verified": True,
    }


def _contract_registry(
    role_contract: dict[str, Any],
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current = (
        ("ligand_heavy_atom_one_hot_10d", "float32", 2, "[N_ligand,10]", 10, "flattened_ligand_index_0based", "checkpoint one-hot C|N|O|S|B|Br|Cl|P|I|F"),
        ("pocket_heavy_atom_one_hot_10d", "float32", 2, "[N_pocket,10]", 10, "flattened_pocket_index_0based", "checkpoint one-hot C|N|O|S|B|Br|Cl|P|I|F"),
        ("ligand_heavy_coordinates", "float32", 2, "[N_ligand,3]", 3, "flattened_ligand_index_0based", "retained-heavy ligand x|y|z"),
        ("pocket_heavy_coordinates", "float32", 2, "[N_pocket,3]", 3, "flattened_pocket_index_0based", "retained-heavy pocket x|y|z"),
        ("ligand_batch_membership", "int64", 1, "[N_ligand]", 1, "batch_sample_index_0based", "flattened retained ligand row to sample"),
        ("pocket_batch_membership", "int64", 1, "[N_pocket]", 1, "batch_sample_index_0based", "flattened retained pocket row to sample"),
    )
    for name, dtype, rank, shape, width, space, source in current:
        rows.append(_contract_row(
            name, "current_checkpoint_input", name, "existing DiffSBDD checkpoint path",
            source=source,
            derivation="shared explicit-H filter then checkpoint-compatible projection",
            dtype=dtype, rank=rank, shape=shape, width=width,
            index_space=space,
            local_or_flat="flattened" if "flattened" in space else "per_node_value",
            sidecar=False,
            frame="joint_centered_retained_ligand_plus_pocket_frame" if "coordinates" in name else "not_applicable",
            unit="angstrom" if "coordinates" in name else "not_applicable",
            availability="current checkpoint input contract; not materialized this step",
        ))
    for domain in ("ligand", "pocket"):
        flat_space = (
            "flattened_ligand_index_0based"
            if domain == "ligand" else "flattened_pocket_index_0based"
        )
        rows.append(_contract_row(
            f"{domain}_node_count", "batch_index_structure",
            f"{domain}_node_count", "future tensor materialization adapter",
            source=f"retained {domain} heavy atom count per sample",
            derivation="count retained-heavy rows after shared H filter",
            dtype="int64", rank=1, shape="[B]", width=1,
            index_space="batch_sample_index_0based",
            local_or_flat="per_sample",
            domain="positive integer",
            sidecar=True,
        ))
        rows.append(_contract_row(
            f"{domain}_node_offsets", "batch_index_structure",
            f"{domain}_node_offsets", "future tensor materialization adapter",
            source=f"{domain}_node_count",
            derivation="exclusive prefix sum; starts 0; monotone; terminal equals flattened node count",
            dtype="int64", rank=1, shape="[B+1]", width=1,
            index_space=flat_space,
            local_or_flat="batch_boundary_to_flattened",
            domain="nonnegative monotone offsets",
            sidecar=True,
        ))
    rows.extend([
        _contract_row(
            "source_to_retained_heavy_index_map",
            "reserved_metadata_only",
            "source_to_retained_heavy_index_map",
            "future tensor materialization adapter",
            source="heavy-atom disposition and sample projection matrices",
            derivation="one shared source-row to retained-heavy local-index projection",
            dtype="int64", rank=1, shape="[N_source]", width=1,
            index_space="source_full_atom_row_index_0based",
            local_or_flat="source_to_local_projection",
            sentinel="-1 only when source_to_retained_heavy_index_valid is false",
            domain="retained_heavy_local_index_0based or -1",
            availability="metadata projection only; source index forbidden from model/loss",
        ),
        _contract_row(
            "source_to_retained_heavy_index_valid",
            "reserved_metadata_only",
            "source_to_retained_heavy_index_valid",
            "future tensor materialization adapter",
            source="heavy-atom disposition matrix",
            derivation="true exactly for retained supported heavy rows",
            dtype="bool", rank=1, shape="[N_source]", width=1,
            index_space="source_full_atom_row_index_0based",
            local_or_flat="source_row_validity",
            domain="false|true",
            availability="required companion for -1 sentinel",
        ),
    ])
    task_vocab = "|".join(
        f"{task_id}:{name}" for task_id, name, _alias in CANONICAL_TASKS
    )
    rows.append(_contract_row(
        "canonical_task_id", "canonical_task_mask", "canonical_task_id",
        "future role/mask/anchor-distance encoding",
        source="atom-pair validation manifest Exact5 long semantic names",
        derivation="one canonical task id per admitted sample",
        dtype="int64", rank=1, shape="[B]", width=1,
        index_space="batch_sample_index_0based", local_or_flat="per_sample",
        domain=task_vocab,
    ))
    role_blocker = (
        "current11 has no per-atom scaffold/linker/warhead assignments"
    )
    for name in (
        "ligand_generation_mask",
        "ligand_fixed_mask",
        "ligand_target_mask",
        "ligand_context_mask",
    ):
        rows.append(_contract_row(
            name, "canonical_task_mask", name,
            "future role/mask/anchor-distance encoding",
            status="designed_with_blocker",
            source="dynamic role vocabulary and Exact5 role-to-task truth table",
            derivation=(
                "generation==target; fixed==context; target/context disjoint and exhaustive; "
                "C minimal-seed-or-anchor context override applies"
            ),
            dtype="bool", rank=2, shape="[N_ligand,1]", width=1,
            index_space="flattened_ligand_index_0based",
            local_or_flat="flattened",
            domain="false|true",
            availability="requires complete current11 retained-heavy per-atom role assignments",
            blocker=role_blocker,
            evidence_status="vocabulary_frozen_assignments_missing",
        ))
    rows.append(_contract_row(
        "ligand_minimal_seed_or_anchor_mask",
        "canonical_task_mask",
        "ligand_minimal_seed_or_anchor_mask",
        "future role/mask/anchor-distance encoding",
        status="designed_with_blocker",
        source="C task rule requires minimal seed/anchor to remain context",
        derivation="true atoms override C target role and remain context",
        dtype="bool", rank=2, shape="[N_ligand,1]", width=1,
        index_space="flattened_ligand_index_0based",
        local_or_flat="flattened",
        domain="false|true",
        availability="no committed current11 minimal-seed/anchor locator authority",
        blocker="minimal_seed_or_anchor_authority_missing",
        evidence_status="required_semantics_not_currently_locatable",
    ))
    target_rows = (
        ("target_residue_membership_mask", "bool", 2, "[N_pocket,1]", "flattened_pocket_index_0based", "all retained heavy atoms of specified target residue", "not_applicable"),
        ("target_residue_reactive_atom_mask", "bool", 2, "[N_pocket,1]", "flattened_pocket_index_0based", "exactly one true per valid sample and subset of membership", "not_applicable"),
        ("target_residue_reactive_atom_local_index", "int64", 1, "[B]", "retained_heavy_local_index_0based", "remapped pocket-local retained-heavy reactive atom index", "-1 iff condition valid is false"),
        ("target_residue_reactive_atom_flat_index", "int64", 1, "[B]", "flattened_pocket_index_0based", "pocket_node_offsets[batch]+reactive local index", "-1 iff condition valid is false"),
        ("target_residue_condition_valid", "bool", 1, "[B]", "batch_sample_index_0based", "label and remapped index validity", "not_applicable"),
    )
    for name, dtype, rank, shape, space, derivation, sentinel in target_rows:
        rows.append(_contract_row(
            name, "covalent_sidecar_condition", name,
            "future target residue/atom condition adapter",
            source="final dataset residue locator + exact-one atom-pair remap",
            derivation=derivation,
            dtype=dtype, rank=rank, shape=shape, width=1,
            index_space=space,
            local_or_flat=(
                "local" if "local" in name
                else "flat" if "flat" in name or "mask" in name
                else "per_sample"
            ),
            sentinel=sentinel,
            domain="false|true" if dtype == "bool" else "nonnegative index or -1",
            availability="11/11 current samples valid",
            valid_count=11,
        ))
    role_vocab = "|".join(
        f"{index}:{role}"
        for index, role in enumerate(role_contract["role_vocabulary"])
    )
    for name, dtype in (("ligand_role_id", "int64"), ("ligand_role_valid", "bool")):
        rows.append(_contract_row(
            name, "covalent_sidecar_condition", name,
            "future role/mask/anchor-distance encoding",
            status="designed_with_blocker",
            source="masking.py build_long_form_mask argument order",
            derivation="per retained ligand heavy atom role assignment",
            dtype=dtype, rank=1, shape="[N_ligand]", width=1,
            index_space="flattened_ligand_index_0based",
            local_or_flat="flattened",
            sentinel=(
                "-1 iff ligand_role_valid is false"
                if dtype == "int64" else "not_applicable"
            ),
            domain=role_vocab if dtype == "int64" else "false|true",
            availability="current11 role fields absent",
            blocker=role_blocker,
            evidence_status="vocabulary_frozen_assignments_missing",
        ))
    for name, dtype in (
        ("ligand_anchor_distance_angstrom", "float32"),
        ("ligand_anchor_distance_valid", "bool"),
    ):
        rows.append(_contract_row(
            name, "covalent_sidecar_condition", name,
            "future role/mask/anchor-distance encoding",
            source="retained-heavy ligand coordinates + target reactive pocket atom",
            derivation=(
                "Euclidean distance from each retained ligand heavy atom to target "
                "residue reactive atom after H filter"
            ),
            dtype=dtype, rank=2, shape="[N_ligand,1]", width=1,
            index_space="flattened_ligand_index_0based",
            local_or_flat="flattened",
            domain="finite nonnegative" if dtype == "float32" else "false|true",
            unit="angstrom" if dtype == "float32" else "not_applicable",
            frame="centering_invariant_euclidean_distance",
            availability="false when target atom is unavailable",
            valid_count=11,
        ))
    rows.append(_contract_row(
        "pair_candidate_offsets", "batch_index_structure",
        "pair_candidate_offsets",
        "future pair prediction head and pair contrastive loss",
        source=(
            "retained_ligand_count and target_residue_retained_heavy_count"
        ),
        derivation=(
            "exclusive candidate prefix sum; offsets[0]=0; monotone; "
            "offsets[-1]=P; offsets[b+1]-offsets[b]="
            "retained_ligand_count[b]*"
            "target_residue_retained_heavy_count[b]"
        ),
        dtype="int64", rank=1, shape="[B+1]", width=1,
        index_space="pair_candidate_index_0based",
        local_or_flat="batch_boundary_to_global_candidate",
        domain="nonnegative monotone offsets",
        availability="P=1938 for current11 metadata evidence",
        valid_count=1938,
    ))
    pair_index_rows = (
        ("pair_candidate_batch_index", "batch_sample_index_0based", "per_candidate_value"),
        ("pair_candidate_ligand_local_index", "retained_heavy_local_index_0based", "ligand_local"),
        ("pair_candidate_residue_local_index", "retained_heavy_local_index_0based", "pocket_retained_heavy_local_within_sample"),
        ("pair_candidate_ligand_flat_index", "flattened_ligand_index_0based", "ligand_flat"),
        ("pair_candidate_pocket_flat_index", "flattened_pocket_index_0based", "pocket_flat"),
    )
    for name, space, local_or_flat in pair_index_rows:
        derivation = (
            "sample then ligand-local ascending then target-residue membership "
            "ordered by pocket retained-heavy local index ascending"
        )
        if name == "pair_candidate_residue_local_index":
            derivation += (
                "; value is the pocket retained-heavy local index within the "
                "whole sample, never target-residue member ordinal"
            )
        elif name == "pair_candidate_ligand_flat_index":
            derivation += (
                "; ligand_node_offsets[batch]+"
                "pair_candidate_ligand_local_index"
            )
        elif name == "pair_candidate_pocket_flat_index":
            derivation += (
                "; pocket_node_offsets[batch]+"
                "pair_candidate_residue_local_index"
            )
        rows.append(_contract_row(
            name, "batch_index_structure", name,
            "future pair prediction head and pair contrastive loss",
            source="retained ligand heavy atoms × target-residue retained heavy atoms",
            derivation=derivation,
            dtype="int64", rank=1, shape="[P]", width=1,
            index_space=space,
            local_or_flat=local_or_flat,
            domain="nonnegative valid index",
            availability="P=1938 for current11 metadata evidence",
            valid_count=1938,
        ))
    for name, meaning in (
        ("pair_candidate_is_positive", "true only for remapped ligand↔target-residue covalent pair"),
        ("pair_candidate_is_negative", "true for every same-sample non-positive candidate"),
    ):
        rows.append(_contract_row(
            name, "auxiliary_training_label", name,
            "future pair prediction head and pair contrastive loss",
            source="exact-one remapped positive and deterministic complement",
            derivation=meaning,
            dtype="bool", rank=1, shape="[P]", width=1,
            index_space="pair_candidate_index_0based",
            local_or_flat="per_candidate",
            domain="false|true",
            availability="11/11 samples exact-one positive and at least one negative",
            valid_count=1938,
        ))
    rows.extend([
        _contract_row(
            "pair_positive_candidate_index", "batch_index_structure",
            "pair_positive_candidate_index",
            "future pair prediction head and pair contrastive loss",
            source="pair_candidate_is_positive",
            derivation=(
                "pair_candidate_offsets[b]+positive_ligand_local_index[b]*"
                "target_residue_retained_heavy_count[b]+"
                "positive_target_residue_member_ordinal[b]; ordinal is "
                "enumeration-only, not a formal model index space"
            ),
            dtype="int64", rank=1, shape="[B]", width=1,
            index_space="pair_candidate_index_0based",
            local_or_flat="per_sample_to_global_candidate",
            sentinel="-1 iff pair_positive_candidate_valid is false",
            domain="nonnegative candidate index or -1",
            availability="11/11 current samples valid",
            valid_count=11,
        ),
        _contract_row(
            "pair_positive_candidate_valid", "auxiliary_training_label",
            "pair_positive_candidate_valid",
            "future pair prediction head and pair contrastive loss",
            source="exact-one positive validation",
            derivation="true iff exactly one positive has valid retained-heavy indices",
            dtype="bool", rank=1, shape="[B]", width=1,
            index_space="batch_sample_index_0based",
            local_or_flat="per_sample",
            domain="false|true",
            availability="11/11 current samples valid",
            valid_count=11,
        ),
        _contract_row(
            "pair_negative_count", "auxiliary_training_label",
            "pair_negative_count",
            "future pair contrastive loss",
            source="pair candidate count minus exact-one positive",
            derivation="all valid same-sample non-positive candidates; no sampling",
            dtype="int64", rank=1, shape="[B]", width=1,
            index_space="batch_sample_index_0based",
            local_or_flat="per_sample",
            domain="nonnegative integer",
            availability="11/11 current samples have at least one negative",
            valid_count=11,
        ),
    ])
    warhead_blocker = "current11 has no committed warhead-type label field or vocabulary"
    for name, dtype in (
        ("warhead_type_id", "int64"),
        ("warhead_type_label_valid", "bool"),
    ):
        rows.append(_contract_row(
            name, "auxiliary_training_label", name,
            "future auxiliary warhead-type head (not a sixth module)",
            status="designed_with_blocker",
            source="legacy schema field exists; current11 field absent",
            derivation="deterministically ordered committed vocabulary required before ids",
            dtype=dtype, rank=1, shape="[B]", width=1,
            index_space="batch_sample_index_0based",
            local_or_flat="per_sample",
            sentinel="-1 iff warhead_type_label_valid is false" if dtype == "int64" else "not_applicable",
            domain="unfrozen vocabulary" if dtype == "int64" else "false|true",
            availability="0/11 current samples labeled",
            blocker=warhead_blocker,
            evidence_status="current11_label_vocabulary_missing",
            valid_count=0,
        ))
    geometry_blocker = (
        "only post-covalent bond distance is frozen; complete pre/post/delta "
        "geometry and angle/dihedral authority are absent"
    )
    rows.extend([
        _contract_row(
            "geometry_target", "auxiliary_training_label", "geometry_target",
            "future covalent geometry prediction head",
            status="designed_with_blocker",
            source="final_dataset_index.bond_distance_angstrom and positive pair table",
            derivation="component 0 is post-covalent positive-pair bond distance",
            dtype="float32", rank=2, shape="[B,G]", width=1,
            index_space="batch_sample_index_0based",
            local_or_flat="per_sample_component",
            sentinel="numeric sentinel never authorizes loss; validity mask required",
            domain="finite component values",
            availability="component 0 valid for 11/11; full requested geometry incomplete",
            blocker=geometry_blocker,
            evidence_status="partial_geometry_component_authority",
            valid_count=11,
        ),
        _contract_row(
            "geometry_component_valid_mask", "auxiliary_training_label",
            "geometry_component_valid_mask",
            "future covalent geometry prediction head",
            status="designed_with_blocker",
            source="per-component label availability",
            derivation="true only for present, finite, semantically frozen component",
            dtype="bool", rank=2, shape="[B,G]", width=1,
            index_space="batch_sample_index_0based",
            local_or_flat="per_sample_component",
            domain="false|true",
            availability="missing components must be false and never zero-filled into loss",
            blocker=geometry_blocker,
            evidence_status="partial_geometry_component_authority",
            valid_count=11,
        ),
        _contract_row(
            "geometry_component_0_post_covalent_bond_distance_angstrom",
            "reserved_metadata_only",
            "post_covalent_positive_pair_bond_distance_angstrom",
            "future geometry_target component 0",
            source="final_dataset_index.bond_distance_angstrom crosschecked to pair table",
            derivation="distance for the remapped exact positive retained-heavy pair",
            dtype="float32", rank=1, shape="[B]", width=1,
            index_space="batch_sample_index_0based",
            local_or_flat="per_sample_component",
            domain="finite positive real",
            unit="angstrom",
            frame="centering_invariant_euclidean_distance",
            availability="11/11 current samples valid",
            geometry_component_id="0",
            pre_post_or_delta="post_covalent",
            periodicity="nonperiodic",
            canonical_range="[0,+inf)",
            representation="scalar_distance",
            valid_count=11,
        ),
    ])
    loss_rows = (
        ("warhead_type_loss_mask", "[B]", "batch_sample_index_0based", "sample admitted AND warhead label available AND id valid", "designed_with_blocker", warhead_blocker, 0),
        ("pair_head_candidate_loss_mask", "[P]", "pair_candidate_index_0based", "sample admitted AND candidate label available AND all indices valid AND no H/padding", "designed", "", 1938),
        ("pair_contrastive_sample_loss_mask", "[B]", "batch_sample_index_0based", "sample admitted AND exactly one positive AND at least one negative AND indices valid", "designed", "", 11),
        ("geometry_component_loss_mask", "[B,G]", "batch_sample_index_0based", "sample admitted AND component label available AND positive indices valid", "designed_with_blocker", geometry_blocker, 11),
        ("geometry_sample_loss_mask", "[B]", "batch_sample_index_0based", "sample admitted AND at least one geometry component loss mask true", "designed_with_blocker", geometry_blocker, 11),
    )
    for name, shape, space, derivation, status, blocker, valid_count in loss_rows:
        rows.append(_contract_row(
            name, "auxiliary_loss_mask", name,
            "future auxiliary supervision only",
            status=status,
            source="sample admission + label availability + index validity + contract prerequisites",
            derivation=derivation,
            dtype="bool", rank=2 if "," in shape else 1,
            shape=shape, width=1,
            index_space=space,
            local_or_flat="per_candidate" if shape == "[P]" else "per_sample",
            domain="false|true",
            availability="distinct from canonical generation and padding masks",
            loss_mask="this row is the explicit auxiliary loss availability mask",
            blocker=blocker,
            evidence_status="BASE_bound_verified" if not blocker else "designed_with_known_blocker",
            valid_count=valid_count,
        ))
    identities = [row["contract_id"] for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate normalized contract row")
    if any(
        row["contract_category"] not in CONTRACT_CATEGORIES
        or row["contract_status"] not in CONTRACT_STATUSES
        or row["changes_checkpoint_input_width"]
        or row["materialized_current_step"]
        or not row["verified"]
        for row in rows
    ):
        raise ValueError("registry invariant drift")
    return rows


def _issue_artifact(
    predecessor_payload: bytes,
    *,
    condition_resolved: bool,
    pair_resolved: bool,
    auxiliary_resolved: bool,
) -> tuple[bytes, list[dict[str, str]]]:
    predecessor_rows = _csv_rows(predecessor_payload)
    if len(predecessor_rows) != 32:
        raise ValueError("predecessor issue row count drift")
    columns = tuple(predecessor_rows[0])
    issue_specs = (
        (
            "COVALENT_CONDITION_AND_TASK_MASK_TENSOR_CONTRACT_UNRESOLVED",
            condition_resolved,
            "condition_and_task_mask_tensor_contract",
            "current11 per-atom role and minimal-seed/anchor authority missing",
        ),
        (
            "COVALENT_PAIR_LABEL_AND_NEGATIVE_POLICY_UNRESOLVED",
            pair_resolved,
            "pair_label_and_negative_policy",
            "pair candidate, positive, negative, index, and loss-mask policy frozen",
        ),
        (
            "COVALENT_GEOMETRY_AND_AUXILIARY_LABEL_CONTRACT_UNRESOLVED",
            auxiliary_resolved,
            "geometry_and_auxiliary_label_contract",
            "warhead vocabulary and complete pre/post geometry authority missing",
        ),
    )
    appended: list[dict[str, Any]] = []
    for offset, (issue_id, resolved, scope, evidence) in enumerate(
        issue_specs, start=33
    ):
        status = "resolved" if resolved else "open"
        appended.append({
            "inherited_order": offset,
            "issue_id": issue_id,
            "issue_type": "training_tensor_contract_gap",
            "affected_fields": scope,
            "affected_rules": SCHEMA_VERSION,
            "severity": "blocking",
            "status": status,
            "blocking_scope": scope,
            "blocking_reason": "" if resolved else evidence,
            "issue_origin": STAGE,
            "integration_transition": "new_design_issue",
            "issue_count": 0 if resolved else 1,
            "inherited_effective_status": "",
            "inherited_transition_stage": "",
            "inherited_transition_action": "not_applicable_new_issue",
            "inherited_transition_evidence": "new tensor contract design issue",
            "successor_effective_status": status,
            "successor_transition_stage": STAGE,
            "successor_transition_action": (
                "resolved_by_metadata_only_contract_design_v1"
                if resolved else "unchanged_open_fail_closed"
            ),
            "successor_transition_evidence": evidence,
        })
    appended_payload = _csv_bytes(columns, appended)
    payload = (
        predecessor_payload
        + appended_payload.split(b"\n", 1)[1]
    )
    rows = _csv_rows(payload)
    if rows[:32] != predecessor_rows or len(rows) != 35:
        raise ValueError("issue inheritance is not byte/order equivalent")
    return payload, rows


def _source_inventory(
    source_data: dict[str, Any],
) -> list[dict[str, Any]]:
    payloads = source_data["payloads"]
    specs = source_data["specs"]
    rows: list[dict[str, Any]] = []
    for path in sorted(specs, key=lambda item: item.as_posix()):
        role, kind, selector, contract_count, sample_count = specs[path]
        if path in {FINAL_DATASET_INDEX, ATOM_PAIR_MAPPING, ATOM_PAIR_MANIFEST, SAMPLE_PROJECTION}:
            sample_count = 11
        rows.append({
            "source_role": role,
            "source_path": path.as_posix(),
            "source_sha256": _sha(payloads[path]),
            "committed_in_base": True,
            "source_kind": kind,
            "selector_or_symbol": selector,
            "referenced_contract_count": contract_count,
            "referenced_sample_count": sample_count,
            "verified": True,
        })
    return rows


def _verify_v3_hardening_contracts_v1() -> dict[str, bool]:
    single_spec = PairCandidateSampleSpec(
        batch_sample_index_0based=0,
        retained_ligand_count=1,
        retained_pocket_count=1,
        target_residue_pocket_local_indices=(0,),
        positive_ligand_local_index=0,
        positive_pocket_local_index=0,
    )
    single = build_pair_candidate_records_v1(
        (single_spec,),
        (0, 1),
        (0, 1),
    )
    zero_negative_supported = (
        len(single.records) == 1
        and single.pair_candidate_is_positive == (True,)
        and single.pair_candidate_is_negative == (False,)
        and single.pair_positive_candidate_valid == (True,)
        and single.pair_negative_count == (0,)
        and single.pair_contrastive_sample_loss_mask == (False,)
    )
    if not zero_negative_supported:
        raise ValueError("zero-negative pair-head projection contract drift")
    zero_negative_scenario = (
        validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            replace(
                BASELINE_SCENARIO,
                pair_negative_count=0,
                contrastive_sample_loss_mask_enabled=False,
            )
        )
    )
    if (
        zero_negative_scenario.outcome != "designed_with_blockers"
        or not zero_negative_scenario.pair_contract_resolved
        or zero_negative_scenario.ready_for_tensor_materialization_smoke
    ):
        raise ValueError("zero-negative scenario policy contract drift")

    invalid_specs = (
        replace(single_spec, batch_sample_index_0based=False),
        replace(single_spec, batch_sample_index_0based=True),
        replace(single_spec, retained_ligand_count=True),
        replace(single_spec, retained_pocket_count=True),
        replace(single_spec, positive_ligand_local_index=True),
        replace(single_spec, positive_pocket_local_index=True),
        replace(
            single_spec,
            target_residue_pocket_local_indices=(False, 0),
        ),
        replace(
            single_spec,
            target_residue_pocket_local_indices=[0],  # type: ignore[arg-type]
        ),
    )
    sample_spec_types_verified = all(
        not validate_pair_candidate_sample_spec_exact_types_v1(spec)[0]
        for spec in invalid_specs
    )
    invalid_contract_scenarios = (
        replace(
            BASELINE_SCENARIO,
            predecessor_effective_open_issue_count=False,
        ),
        replace(BASELINE_SCENARIO, checkpoint_atom_feature_width=True),
        replace(BASELINE_SCENARIO, canonical_task_count=True),
        replace(BASELINE_SCENARIO, pair_positive_count=True),
        replace(BASELINE_SCENARIO, pair_negative_count=True),
        replace(BASELINE_SCENARIO, pair_positive_count=1.0),
        replace(BASELINE_SCENARIO, pair_negative_count="1"),
    )
    contract_scenario_types_verified = all(
        validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            scenario
        ).outcome == "invalid"
        for scenario in invalid_contract_scenarios
    )
    invalid_pair_policy_scenarios = (
        replace(BASELINE_PAIR_POLICY_SCENARIO, positive_count=True),
        replace(BASELINE_PAIR_POLICY_SCENARIO, negative_count=True),
    )
    pair_policy_types_verified = all(
        (
            not evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
                scenario
            ).candidate_allowed
            and any(
                reason.startswith(
                    "pair_policy_scenario_field_type_invalid:"
                )
                for reason in (
                    evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
                        scenario
                    ).reasons
                )
            )
        )
        for scenario in invalid_pair_policy_scenarios
    )
    failure_registry_valid, _failure_registry_reasons = (
        validate_mutation_registry_exact_types_v1(
            BASELINE_SCENARIO,
            FAILURE_MUTATIONS,
            registry_name="failure",
        )
    )
    pair_registry_valid, _pair_registry_reasons = (
        validate_mutation_registry_exact_types_v1(
            BASELINE_PAIR_POLICY_SCENARIO,
            PAIR_POLICY_MUTATIONS,
            registry_name="pair_policy",
        )
    )
    if not all((
        sample_spec_types_verified,
        contract_scenario_types_verified,
        pair_policy_types_verified,
        failure_registry_valid,
        pair_registry_valid,
    )):
        raise ValueError("V3 exact scalar-type hardening verification failed")
    return {
        "pair_builder_zero_negative_pair_head_supported": True,
        "pair_contrastive_mask_false_when_zero_negative": True,
        "pair_candidate_sample_spec_exact_types_verified": True,
        "contract_scenario_exact_scalar_types_verified": True,
        "pair_policy_scenario_exact_scalar_types_verified": True,
        "boolean_rejected_for_integer_index_and_count_fields": True,
        "failure_mutation_registry_exact_types_verified": True,
        "pair_policy_mutation_registry_exact_types_verified": True,
    }


def _verify_v4_public_index_helpers_v1() -> dict[str, bool]:
    valid_offsets = (
        validate_offsets_v1((0, 1), 1)
        and validate_offsets_v1((0,), 0)
    )
    invalid_offsets = (
        ((0, 1), True),
        ((0, 1), False),
        ((0, 1), 1.0),
        ((0, 1), "1"),
        ((0, True), 1),
        ((False, 1), 1),
        ((0, 1.0), 1),
        (None, 0),
        ((), 0),
    )
    offsets_exact = valid_offsets and all(
        not validate_offsets_v1(offsets, terminal)
        for offsets, terminal in invalid_offsets
    )
    if (
        flatten_local_index_v1((0, 2), 0, 0) != 0
        or flatten_local_index_v1((0, 2), 0, 1) != 1
        or type(flatten_local_index_v1((0, 2), 0, 0)) is not int
    ):
        raise ValueError("valid flatten-local index contract drift")
    invalid_flatten = (
        ((0, 2), False, 0, "batch sample index exact int required"),
        ((0, 2), True, 0, "batch sample index exact int required"),
        ((0, 2), 0.0, 0, "batch sample index exact int required"),
        ((0, 2), "0", 0, "batch sample index exact int required"),
        ((0, 2), 0, False, "retained-heavy local index exact int required"),
        ((0, 2), 0, True, "retained-heavy local index exact int required"),
        ((0, 2), 0, 1.0, "retained-heavy local index exact int required"),
        ((0, 2), 0, "1", "retained-heavy local index exact int required"),
    )
    for offsets, batch, local, expected_reason in invalid_flatten:
        try:
            flatten_local_index_v1(offsets, batch, local)
        except ValueError as error:
            if str(error) != expected_reason:
                raise ValueError(
                    "flatten-local deterministic reason drift"
                ) from error
        else:
            raise ValueError("flatten-local exact int accepted invalid input")
    expected_targets = (
        ("warhead",),
        ("linker", "warhead"),
        ("scaffold", "warhead"),
        ("scaffold",),
        ("scaffold", "linker", "warhead"),
    )
    if tuple(
        canonical_task_regions_v1(task_id)["target"]
        for task_id in range(5)
    ) != expected_targets:
        raise ValueError("Exact5 canonical task region drift")
    for invalid_task_id in (True, False, 0.0, 1.0, "0", None):
        try:
            canonical_task_regions_v1(invalid_task_id)
        except ValueError as error:
            if str(error) != "canonical task id exact int required":
                raise ValueError(
                    "canonical task deterministic reason drift"
                ) from error
        else:
            raise ValueError("canonical task exact int accepted invalid input")
    sentinel_exact = (
        validate_sentinel_with_validity_v1(0, True)
        and validate_sentinel_with_validity_v1(-1, False)
        and not validate_sentinel_with_validity_v1(True, True)
        and not validate_sentinel_with_validity_v1(0, 1)
    )
    zero_spec = PairCandidateSampleSpec(
        batch_sample_index_0based=0,
        retained_ligand_count=1,
        retained_pocket_count=1,
        target_residue_pocket_local_indices=(0,),
        positive_ligand_local_index=0,
        positive_pocket_local_index=0,
    )
    sample_spec_exact = (
        validate_pair_candidate_sample_spec_exact_types_v1(zero_spec)[0]
        and not validate_pair_candidate_sample_spec_exact_types_v1(
            replace(zero_spec, positive_ligand_local_index=True)
        )[0]
    )
    if not all((offsets_exact, sentinel_exact, sample_spec_exact)):
        raise ValueError("public index helper exact scalar-type audit failed")
    return {
        "offset_terminal_count_exact_int_verified": True,
        "offset_elements_exact_int_verified": True,
        "flatten_local_index_exact_int_verified": True,
        "canonical_task_id_exact_int_verified": True,
        "public_index_helpers_exact_scalar_types_verified": True,
        "boolean_rejected_across_all_public_index_helpers": True,
    }


def _verify_v5_nonnegative_counts_and_ordered_offsets_v1(
) -> dict[str, bool]:
    invalid_contract_cases = (
        (
            replace(
                BASELINE_SCENARIO,
                pair_positive_count=-1,
            ),
            "positive_pair_count_negative",
        ),
        (
            replace(
                BASELINE_SCENARIO,
                pair_negative_count=-1,
                contrastive_sample_loss_mask_enabled=False,
            ),
            "negative_pair_count_negative",
        ),
    )
    for scenario, expected_reason in invalid_contract_cases:
        observation = (
            validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
                scenario
            )
        )
        if (
            observation.outcome != "invalid"
            or observation.reasons != (expected_reason,)
        ):
            raise ValueError("nonnegative top-level pair-count audit failed")

    invalid_policy_cases = (
        (
            replace(
                BASELINE_PAIR_POLICY_SCENARIO,
                positive_count=-1,
            ),
            "positive_pair_count_negative",
        ),
        (
            replace(
                BASELINE_PAIR_POLICY_SCENARIO,
                negative_count=-1,
                contrastive_sample_loss_mask_enabled=False,
            ),
            "negative_pair_count_negative",
        ),
    )
    for scenario, expected_reason in invalid_policy_cases:
        observation = (
            evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
                scenario
            )
        )
        if (
            observation.candidate_allowed
            or observation.reasons != (expected_reason,)
        ):
            raise ValueError("nonnegative pair-policy count audit failed")

    zero_disabled = (
        evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
            replace(
                BASELINE_PAIR_POLICY_SCENARIO,
                negative_count=0,
                contrastive_sample_loss_mask_enabled=False,
            )
        )
    )
    zero_enabled = (
        evaluate_covapie_pair_candidate_and_negative_policy_scenario_v1(
            replace(
                BASELINE_PAIR_POLICY_SCENARIO,
                negative_count=0,
                contrastive_sample_loss_mask_enabled=True,
            )
        )
    )
    if (
        not zero_disabled.candidate_allowed
        or zero_disabled.reasons != (
            "valid_exact_positive_in_frozen_candidate_domain",
        )
        or not zero_enabled.candidate_allowed
        or zero_enabled.reasons != (
            "contrastive_loss_requires_at_least_one_negative",
        )
        or zero_enabled.loss_mask_semantics
        != "pair_head_may_be_valid_but_contrastive_sample_mask_false"
    ):
        raise ValueError("zero-negative V3 contract regression")

    single_spec = PairCandidateSampleSpec(
        batch_sample_index_0based=0,
        retained_ligand_count=1,
        retained_pocket_count=1,
        target_residue_pocket_local_indices=(0,),
        positive_ligand_local_index=0,
        positive_pocket_local_index=0,
    )
    single = build_pair_candidate_records_v1(
        (single_spec,),
        (0, 1),
        (0, 1),
    )
    if (
        len(single.records) != 1
        or single.pair_candidate_is_positive != (True,)
        or single.pair_candidate_is_negative != (False,)
        or single.pair_positive_candidate_valid != (True,)
        or single.pair_negative_count != (0,)
        or single.pair_contrastive_sample_loss_mask != (False,)
        or any(value < 0 for value in single.pair_negative_count)
    ):
        raise ValueError("pair-builder nonnegative derivation audit failed")

    valid_offsets = (
        ((0, 1), 1),
        ([0, 1], 1),
        (range(0, 2), 1),
    )
    invalid_offsets = (
        ({0: "x", 1: "y"}, 1),
        ({0, 1}, 1),
        (frozenset({0, 1}), 1),
        (iter([0, 1]), 1),
        ((value for value in [0, 1]), 1),
        ("01", 1),
        (b"\x00\x01", 1),
        (bytearray([0, 1]), 1),
        (memoryview(b"\x00\x01"), 1),
        (None, 0),
    )
    if (
        not all(
            validate_offsets_v1(offsets, terminal)
            for offsets, terminal in valid_offsets
        )
        or any(
            validate_offsets_v1(offsets, terminal)
            for offsets, terminal in invalid_offsets
        )
    ):
        raise ValueError("ordered offset Sequence audit failed")

    valid_flatten = (
        flatten_local_index_v1((0, 2), 0, 0),
        flatten_local_index_v1([0, 2], 0, 1),
        flatten_local_index_v1(range(0, 3, 2), 0, 1),
    )
    if valid_flatten != (0, 1, 1) or any(
        type(value) is not int for value in valid_flatten
    ):
        raise ValueError("ordered offset flatten audit failed")
    for offsets in (
        {0: "x", 1: "y"},
        {0, 1},
        frozenset({0, 1}),
        iter([0, 2]),
        (value for value in [0, 2]),
        "02",
        b"\x00\x02",
        bytearray([0, 2]),
        memoryview(b"\x00\x02"),
    ):
        try:
            flatten_local_index_v1(offsets, 0, 0)
        except ValueError as error:
            if str(error) != "offset contract invalid":
                raise ValueError(
                    "unordered flatten deterministic reason drift"
                ) from error
        else:
            raise ValueError("unordered offset container accepted")

    return {
        "pair_positive_count_nonnegative_verified": True,
        "pair_negative_count_nonnegative_verified": True,
        "negative_pair_count_rejected_when_contrastive_disabled": True,
        "negative_count_reason_semantics_frozen": True,
        "offset_container_ordered_sequence_verified": True,
        "unordered_offset_containers_rejected": True,
        "single_pass_offset_iterables_rejected": True,
        "binary_offset_containers_rejected": True,
    }


def serialize_covapie_tensor_label_and_loss_mask_contract_design_decision_v1(
    decision: TensorLabelAndLossMaskContractDesignDecision,
) -> bytes:
    return (
        json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def derive_covapie_tensor_label_and_loss_mask_contract_design_v1(
    repo_root: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    fixed_payloads, predecessor_manifest = _verify_predecessor(repo_root)
    source_data = _load_sources(repo_root, fixed_payloads)
    pair_manifest = _json(fixed_payloads[ATOM_PAIR_MANIFEST])
    observed_tasks = tuple(
        (
            index,
            row.get("semantic_name"),
            row.get("display_alias"),
        )
        for index, row in enumerate(pair_manifest.get("canonical_masks", []))
    )
    if observed_tasks != CANONICAL_TASKS:
        raise ValueError("Exact5 canonical task authority drift")
    role_contract = _discover_role_contract(source_data["payloads"])
    analysis = _analyze_current_samples(source_data, fixed_payloads)
    hardening = _verify_v3_hardening_contracts_v1()
    public_helper_hardening = _verify_v4_public_index_helpers_v1()
    count_and_offset_hardening = (
        _verify_v5_nonnegative_counts_and_ordered_offsets_v1()
    )
    if analysis["role_fields_present"]:
        raise ValueError("unexpected current11 role authority requires review")
    if analysis["warhead_fields_present"]:
        raise ValueError("unexpected current11 warhead authority requires review")
    registry_rows = _contract_registry(role_contract, analysis)
    pair_rows = build_pair_candidate_and_negative_policy_matrix_rows_v1()
    failure_rows = build_failure_matrix_rows_v1()
    baseline_observation = (
        validate_covapie_tensor_label_and_loss_mask_contract_scenario_v1(
            BASELINE_SCENARIO
        )
    )
    if baseline_observation != TensorLabelAndLossMaskContractScenarioObservation(
        outcome="designed_with_blockers",
        reasons=(
            "current11_per_atom_role_and_minimal_seed_authority_missing",
            "current11_warhead_type_vocabulary_missing",
            "complete_pre_post_geometry_contract_missing",
        ),
        condition_contract_resolved=False,
        pair_contract_resolved=True,
        geometry_and_auxiliary_label_contract_resolved=False,
        tensor_label_loss_mask_contract_designed=False,
        ready_for_tensor_materialization_smoke=False,
        ready_for_tensorization=False,
        ready_for_model_integration=False,
        ready_for_training=False,
        fails_closed=True,
    ):
        raise ValueError("baseline executable scenario truthfulness drift")
    if (
        len(pair_rows) != 16
        or not all(row["verified"] for row in pair_rows)
        or len(failure_rows) != 40
        or not all(row["verified"] for row in failure_rows)
    ):
        raise ValueError("executable policy/failure evidence drift")
    condition_resolved = False
    pair_resolved = (
        analysis["pair_candidate_policy_frozen"]
        and analysis["pair_negative_policy_frozen"]
        and analysis["pair_positive_exact_one_verified"]
    )
    auxiliary_resolved = (
        bool(analysis["warhead_type_vocabulary"])
        and analysis["geometry_contract_frozen"]
    )
    issue_payload, issue_rows = _issue_artifact(
        fixed_payloads[PREDECESSOR_ISSUES],
        condition_resolved=condition_resolved,
        pair_resolved=pair_resolved,
        auxiliary_resolved=auxiliary_resolved,
    )
    effective_open_issues = [
        row["issue_id"]
        for row in issue_rows
        if row["successor_effective_status"] == "open"
    ]
    expected_open = [
        "COVALENT_CONDITION_AND_TASK_MASK_TENSOR_CONTRACT_UNRESOLVED",
        "COVALENT_GEOMETRY_AND_AUXILIARY_LABEL_CONTRACT_UNRESOLVED",
    ]
    if effective_open_issues != expected_open:
        raise ValueError("effective design issue set drift")
    designed = not effective_open_issues
    recommended_next_step = (
        "materialize_covapie_tensor_label_and_loss_mask_contract_smoke_v1"
        if designed
        else "resolve_covapie_condition_and_task_mask_tensor_contract_gaps_v1"
    )
    category_counts = {
        category: sum(
            row["contract_category"] == category for row in registry_rows
        )
        for category in CONTRACT_CATEGORIES
    }
    referenced_index_spaces = {
        row["index_space"]
        for row in registry_rows
        if row["index_space"] in EXACT_INDEX_SPACES
    }
    if referenced_index_spaces != set(EXACT_INDEX_SPACES):
        raise ValueError("registry does not cover Exact6 index spaces")
    index_count = len(referenced_index_spaces)
    decision = TensorLabelAndLossMaskContractDesignDecision(
        schema_version=SCHEMA_VERSION,
        outcome="designed_contract" if designed else "designed_with_blockers",
        predecessor_verified=True,
        contract_registry_row_count=len(registry_rows),
        current_checkpoint_input_contract_count=category_counts[
            "current_checkpoint_input"
        ],
        sidecar_condition_contract_count=category_counts[
            "covalent_sidecar_condition"
        ],
        auxiliary_label_contract_count=category_counts[
            "auxiliary_training_label"
        ],
        auxiliary_loss_mask_contract_count=category_counts[
            "auxiliary_loss_mask"
        ],
        index_space_contract_count=index_count,
        canonical_task_count=len(CANONICAL_TASKS),
        role_vocabulary_frozen=role_contract["role_vocabulary_frozen"],
        pair_candidate_policy_frozen=analysis[
            "pair_candidate_policy_frozen"
        ],
        pair_negative_policy_frozen=analysis["pair_negative_policy_frozen"],
        pair_positive_exact_one_verified=analysis[
            "pair_positive_exact_one_verified"
        ],
        warhead_type_vocabulary_frozen=bool(
            analysis["warhead_type_vocabulary"]
        ),
        geometry_component_count=analysis["geometry_component_count"],
        geometry_contract_frozen=analysis["geometry_contract_frozen"],
        checkpoint_input_width_preserved=True,
        new_covalent_tensors_are_sidecars=True,
        tensor_label_loss_mask_contract_designed=designed,
        tensor_materialization_used=False,
        runtime_enforcement_integrated=False,
        ready_for_tensor_materialization_smoke=designed,
        ready_for_tensorization=False,
        ready_for_model_integration=False,
        ready_for_training=False,
        model_changed=False,
        dataloader_changed=False,
        forward_changed=False,
        loss_changed=False,
        checkpoint_access=False,
        training_used=False,
        recommended_next_step=recommended_next_step,
    )
    source_rows = _source_inventory(source_data)
    return {
        "decision": decision,
        "predecessor_manifest": predecessor_manifest,
        "role_contract": role_contract,
        "analysis": analysis,
        "source_rows": source_rows,
        "registry_rows": registry_rows,
        "pair_rows": pair_rows,
        "failure_rows": failure_rows,
        "issue_payload": issue_payload,
        "issue_rows": issue_rows,
        "effective_open_issues": effective_open_issues,
        "category_counts": category_counts,
        "baseline_observation": baseline_observation,
        "hardening": hardening,
        "public_helper_hardening": public_helper_hardening,
        "count_and_offset_hardening": count_and_offset_hardening,
    }


def _non_manifest_artifacts(result: dict[str, Any]) -> dict[str, bytes]:
    return {
        SOURCE_INVENTORY_FILE: _csv_bytes(
            SOURCE_COLUMNS, result["source_rows"]
        ),
        CONTRACT_REGISTRY_FILE: _csv_bytes(
            CONTRACT_COLUMNS, result["registry_rows"]
        ),
        PAIR_POLICY_FILE: _csv_bytes(PAIR_POLICY_COLUMNS, result["pair_rows"]),
        FAILURE_MATRIX_FILE: _csv_bytes(
            FAILURE_COLUMNS, result["failure_rows"]
        ),
        ISSUE_INVENTORY_FILE: result["issue_payload"],
    }


def _manifest(
    result: dict[str, Any],
    evidence: dict[str, bytes],
) -> dict[str, Any]:
    decision = result["decision"]
    analysis = result["analysis"]
    role_contract = result["role_contract"]
    hardening = result["hardening"]
    public_helper_hardening = result["public_helper_hardening"]
    count_and_offset_hardening = result["count_and_offset_hardening"]
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "contract_design_completed": True,
        "design_outcome": decision.outcome,
        "base_checkpoint_atom_feature_width": 10,
        "base_checkpoint_atom_feature_width_changed": False,
        "new_covalent_tensors_are_sidecars": True,
        "future_adapter_required": True,
        "canonical_task_count": 5,
        "canonical_tasks": [
            {
                "canonical_task_id": task_id,
                "semantic_name": name,
                "display_alias": alias,
            }
            for task_id, name, alias in CANONICAL_TASKS
        ],
        "index_spaces": list(EXACT_INDEX_SPACES),
        "index_space_semantics_frozen": True,
        "offsets_start_at_zero": True,
        "offsets_monotone_nondecreasing": True,
        "offset_terminal_equals_flattened_node_count": True,
        "ligand_local_to_flat_formula": (
            "ligand_node_offsets[batch]+retained_ligand_local_index"
        ),
        "pocket_local_to_flat_formula": (
            "pocket_node_offsets[batch]+retained_pocket_local_index"
        ),
        "source_full_table_index_model_or_loss_allowed": False,
        "sentinel_requires_validity_mask": True,
        "zero_means_missing": False,
        "role_vocabulary": list(role_contract["role_vocabulary"]),
        "role_vocabulary_frozen": role_contract["role_vocabulary_frozen"],
        "role_assignments_current11_complete": False,
        "minimal_seed_or_anchor_authority_present": False,
        "pair_candidate_domain": (
            "retained_ligand_heavy_atoms_x_target_residue_retained_heavy_atoms"
        ),
        "pair_candidate_order": (
            "sample_then_ligand_local_then_target_residue_local"
        ),
        "pair_candidate_count_current11": analysis["pair_candidate_total"],
        "ligand_node_offsets_current11": list(
            analysis["ligand_node_offsets"]
        ),
        "pocket_node_offsets_current11": list(
            analysis["pocket_node_offsets"]
        ),
        "pair_candidate_offsets_current11": list(
            analysis["pair_candidate_offsets"]
        ),
        "pair_candidate_offsets_contract_frozen": (
            analysis["pair_candidate_offsets_contract_frozen"]
        ),
        "pair_candidate_residue_local_index_semantics": (
            "pocket_retained_heavy_local_within_sample"
        ),
        "target_residue_member_ordinal_is_enumeration_only": True,
        "target_residue_member_ordinal_is_formal_index_space": False,
        "pair_local_to_flat_relations_verified": (
            analysis["pair_local_to_flat_relations_verified"]
        ),
        "pair_positive_global_index_formula_verified": (
            analysis["pair_positive_global_index_formula_verified"]
        ),
        "pair_candidate_record_count_current11": len(
            analysis["pair_projection"].records
        ),
        "pair_contrastive_sample_loss_mask_current11": list(
            analysis["pair_contrastive_sample_loss_mask"]
        ),
        "pair_contrastive_mask_true_count_current11": sum(
            analysis["pair_contrastive_sample_loss_mask"]
        ),
        "pair_negative_policy": (
            "all_valid_same_sample_non_positive_candidates"
        ),
        "cross_sample_negatives_allowed": False,
        "random_negative_sampling_allowed": False,
        "hard_negative_mining_allowed": False,
        "pair_positive_exact_one_verified": (
            analysis["pair_positive_exact_one_verified"]
        ),
        "pair_positive_valid_sample_count": 11,
        "pair_candidate_policy_frozen": (
            analysis["pair_candidate_policy_frozen"]
        ),
        "pair_negative_policy_frozen": (
            analysis["pair_negative_policy_frozen"]
        ),
        "warhead_type_vocabulary": list(
            analysis["warhead_type_vocabulary"]
        ),
        "warhead_type_vocabulary_frozen": False,
        "warhead_type_valid_sample_count": 0,
        "geometry_component_count": analysis["geometry_component_count"],
        "geometry_components": [
            {
                "geometry_component_id": 0,
                "semantic_name": (
                    "post_covalent_positive_pair_bond_distance_angstrom"
                ),
                "pre_post_or_delta": "post_covalent",
                "source_fields": (
                    "final_dataset_index.bond_distance_angstrom|"
                    "ligand_residue_atom_pair_table.bond_distance_angstrom"
                ),
                "unit": "angstrom",
                "periodic_or_nonperiodic": "nonperiodic",
                "canonical_range": "[0,+inf)",
                "target_representation": "scalar_distance",
                "normalization": "none",
                "missing_value_semantics": (
                    "component_valid=false; never zero-fill into loss"
                ),
                "loss_mask_semantics": (
                    "sample admitted AND label available AND positive indices valid"
                ),
                "current_valid_sample_count": 11,
            }
        ],
        "geometry_contract_frozen": False,
        "complete_pre_post_geometry_available": False,
        "generation_masks_are_not_loss_masks": True,
        "padding_masks_are_not_label_availability_masks": True,
        "pair_candidate_loss_mask_alias": "pair_head_candidate_loss_mask",
        "contract_registry_row_count": len(result["registry_rows"]),
        "current_checkpoint_input_contract_count": (
            decision.current_checkpoint_input_contract_count
        ),
        "sidecar_condition_contract_count": (
            decision.sidecar_condition_contract_count
        ),
        "auxiliary_label_contract_count": (
            decision.auxiliary_label_contract_count
        ),
        "auxiliary_loss_mask_contract_count": (
            decision.auxiliary_loss_mask_contract_count
        ),
        "index_space_contract_count": decision.index_space_contract_count,
        "source_inventory_row_count": len(result["source_rows"]),
        "pair_policy_matrix_row_count": len(result["pair_rows"]),
        "failure_matrix_row_count": len(result["failure_rows"]),
        "failure_matrix_all_cases_verified": all(
            row["verified"] for row in result["failure_rows"]
        ),
        "failure_matrix_uses_explicit_state_mutations": True,
        "failure_matrix_string_driven_invalid_fallback": False,
        "failure_matrix_expected_reasons_verified": all(
            row["expected_primary_reason"]
            in row["observed_reasons"]
            for row in result["failure_rows"]
        ),
        **hardening,
        **public_helper_hardening,
        **count_and_offset_hardening,
        "issue_inventory_row_count": len(result["issue_rows"]),
        "effective_open_issue_count": len(result["effective_open_issues"]),
        "effective_open_issues": result["effective_open_issues"],
        "tensor_label_loss_mask_contract_designed": (
            decision.tensor_label_loss_mask_contract_designed
        ),
        "ready_for_tensor_materialization_smoke": (
            decision.ready_for_tensor_materialization_smoke
        ),
        "tensor_materialized": False,
        "npz_created": False,
        "tensor_materialization_used": False,
        "runtime_enforcement_integrated": False,
        "checkpoint_access": False,
        "model_changed": False,
        "dataloader_changed": False,
        "forward_changed": False,
        "loss_changed": False,
        "training_used": False,
        "raw_read": False,
        "raw_write": False,
        "provider_used": False,
        "network_used": False,
        "download_used": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "planned_covalent_model_module_count": 5,
        "planned_covalent_model_modules": list(
            PLANNED_COVALENT_MODEL_MODULES
        ),
        "integrated_covalent_model_module_count": 0,
        "evidence_sha256": {
            name: _sha(payload) for name, payload in evidence.items()
        },
        "recommended_next_step": decision.recommended_next_step,
    }


def build_covapie_tensor_label_and_loss_mask_contract_design_artifacts_v1(
    repo_root: Path,
) -> dict[str, bytes]:
    result = derive_covapie_tensor_label_and_loss_mask_contract_design_v1(
        repo_root
    )
    artifacts = _non_manifest_artifacts(result)
    artifacts[MANIFEST_FILE] = (
        json.dumps(_manifest(result, artifacts), indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    return artifacts
