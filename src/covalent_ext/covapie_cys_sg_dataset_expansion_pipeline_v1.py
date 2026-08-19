"""Resumable, fail-closed CovaPIE Cys-SG dataset expansion pipeline V1.

The module is an additive orchestrator.  It does not weaken the historical
Current11 review policy and it never invents chemistry.  Exact matches to a
human-approved, exact-signature reusable authority may replace a repeated
human sample click with deterministic per-sample QA.  Novel, ambiguous, or
unsupported candidates remain routed to human review or a precise mechanical
blocker.

Importing this module performs no I/O.  The default real-population entry point
is dry-run/review-only and does not mutate Exact16, raw data, state, checkpoints,
or tensor artifacts.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
import re
import shutil
from dataclasses import asdict, dataclass, fields, replace
from fractions import Fraction
from itertools import product
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from covalent_ext import (
    covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1
    as historical_review_policy,
)
from covalent_ext import (
    covapie_cys_sg_exact12_targeted_structural_evidence_acquisition_execution_v1
    as acquisition_owner,
)
from covalent_ext import (
    covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1
    as structural_recovery_owner,
)
from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as role_profile_owner,
)
from covalent_ext import (
    covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke
    as independence_evidence_owner,
)
from covalent_ext import (
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as feature_semantics_owner,
)
from covalent_ext import (
    covapie_unified_leakage_split_materialization_smoke as split_owner,
)


PIPELINE_VERSION = "covapie_cys_sg_dataset_expansion_pipeline_v1"
SUCCESSOR_POLICY_ID = "APPROVED_REUSABLE_SIGNATURE_AUTO_ADMISSION_V1"
REUSABLE_AUTHORITY_REGISTRY_SCHEMA_V1 = (
    "covapie_cys_sg_reusable_chemistry_authority_registry_v1"
)
CUMULATIVE_EXPANSION_LEAKAGE_REGISTRY_SCHEMA_V1 = (
    "covapie_cys_sg_cumulative_expansion_leakage_registry_v1"
)
CUMULATIVE_EXPANSION_LEAKAGE_POLICY_ID_V1 = (
    "COVAPIE_CUMULATIVE_EXPANSION_LEAKAGE_MEMBERSHIP_AND_SPLIT_V1"
)
CUMULATIVE_EXPANSION_LEAKAGE_REGISTRY_FILENAME_V1 = (
    "cumulative_leakage_registry_v1.json"
)
MATERIALIZATION_SCHEMA_V1 = (
    "covapie_cys_sg_authorized_expansion_materialization_v1"
)
TENSORIZATION_SCHEMA_V1 = (
    "covapie_cys_sg_authorized_expansion_tensorization_v1"
)
REVIEW_ONLY = "review-only"
MATERIALIZE_APPROVED = "materialize-approved"
CURRENT_POLICY_REQUIRES_EVERY_NEW_SAMPLE_HUMAN_ASSIGNMENT = True
CURRENT_POLICY_OWNER = (
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_"
    "review_gate_design_v1/"
    "covapie_reaction_family_and_warhead_rule_review_policy_registry.csv"
    "#REVIEW_POLICY_008;REVIEW_POLICY_010;REVIEW_POLICY_011"
)

PHASES = (
    "PHASE_01_DISCOVER_OR_LOAD_CANDIDATES",
    "PHASE_02_ACQUIRE_OR_VERIFY_SOURCE",
    "PHASE_03_STRUCTURAL_RECOVERY",
    "PHASE_04_CANONICAL_MODEL_ELIGIBILITY",
    "PHASE_05_CHEMISTRY_AUTHORITY_MATCH",
    "PHASE_06_REVIEW_QUEUE_OR_AUTO_ADMISSION",
    "PHASE_07_PROFILE_ASSIGNMENT",
    "PHASE_08_LEAKAGE_AND_SPLIT",
    "PHASE_09_POST_PRE_AUTHORITY",
    "PHASE_10_MATERIALIZATION_READINESS",
)

STRICT_PROFILE = role_profile_owner.STRICT_LINKER_PRESENT_V1
DIRECT_PROFILE = role_profile_owner.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
SUPPORTED_PROFILES = role_profile_owner.ROLE_PROFILES_V1

AUTO_ADMITTED = "AUTO_ADMITTED_MATERIALIZATION_READY"
HUMAN_APPROVED = "HUMAN_APPROVED_MATERIALIZATION_READY"
HUMAN_REQUIRED = "HUMAN_REVIEW_REQUIRED"
RUNTIME_EXTENSION = "NEEDS_RUNTIME_PROFILE_EXTENSION"
MISSING_SOURCE = "MISSING_SOURCE_AUTHORITY"
SOURCE_SHA_MISMATCH = "SOURCE_SHA_MISMATCH"
REJECTED = "REJECTED"
LEAKAGE_CONFLICT = "LEAKAGE_CONFLICT"
PIPELINE_INPUT_INVALID = "PIPELINE_INPUT_INVALID"
POST_AUTHORITY_INVALID = "POST_AUTHORITY_INVALID"

REVIEW_PACKET_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_training_dataset_expansion_v1/"
    "covapie_cys_sg_near_ready_human_review_packet_v1.md"
)
REVIEW_PACKET_SHA256 = (
    "7d35fcaf254cf23a07c9f469173871acc63bcb89f6c76794e69bc72796ca496f"
)
INVENTORY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_training_dataset_expansion_v1/"
    "covapie_cys_sg_non_exact16_candidate_inventory.csv"
)
INVENTORY_SHA256 = (
    "182d0bcff8e1dea1f29eb4977e0908510f6b8594db83b39efed1580e9f6f2946"
)
EXPANDED_CANDIDATE_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_"
    "eligibility_v1/covapie_cys_sg_expanded_candidate_inventory_and_"
    "eligibility.csv"
)
RECOVERED7_EVIDENCE_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1/"
    "covapie_cys_sg_recovered7_canonical_model_graph_and_pocket_evidence.json"
)
DIRECT_LIGAND_ATOMS_RELATIVE = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_"
    "exported_step8_topology_v0/ligand_observed_atom_topology_smoke_table.csv"
)
DIRECT_LIGAND_BONDS_RELATIVE = DIRECT_LIGAND_ATOMS_RELATIVE.with_name(
    "ligand_observed_bond_topology_smoke_table.csv"
)
DIRECT_POCKET_ATOMS_RELATIVE = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_pocket_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_pocket_atom_table.csv"
)
DIRECT_CONFIRMED_EVENTS_RELATIVE = Path(
    "data/derived/covalent_small/"
    "real_covalent_struct_conn_candidate_manual_review_fill_validation_v0/"
    "real_covalent_struct_conn_confirmed_candidate_table.csv"
)
DIRECT_COORDINATE_PAIRS_RELATIVE = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_"
    "altloc_aware/real_covalent_confirmed_candidate_coordinate_pair_"
    "sanity_table_v1_altloc_aware.csv"
)
DIRECT_FULL_LIGAND_ATOMS_RELATIVE = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_ligand_full_atom_table.csv"
)
DIRECT_PRE_WRITEBACK_RELATIVE = Path(
    "data/derived/covalent_small/pre_reaction_graph/"
    "pre_reaction_transform_manual_write_back_report.csv"
)
DIRECT_PRE_QA_RELATIVE = Path(
    "data/derived/covalent_small/pre_reaction_graph/"
    "pre_reaction_training_readiness_gate_report.csv"
)
BASELINE_LIGAND_EVIDENCE_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_batch_independence_evidence_"
    "materialization_smoke_v0/covapie_ligand_graph_scaffold_evidence.csv"
)
BASELINE_PROTEIN_EVIDENCE_RELATIVE = BASELINE_LIGAND_EVIDENCE_RELATIVE.with_name(
    "covapie_protein_sequence_accession_evidence.csv"
)
BASELINE_FINAL_GROUP_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_unified_independence_group_assignment_and_sample_index_merge_"
    "smoke_v0/covapie_final_leakage_group_assignment.csv"
)
REVIEW_TEMPLATE_V2_RELATIVE = REVIEW_PACKET_RELATIVE.with_name(
    "covapie_cys_sg_near_ready_human_review_decision_template_v2.json"
)
REVIEW_TEMPLATE_V2_SCHEMA = (
    "covapie_cys_sg_near_ready_human_review_decision_template_v2"
)

EVIDENCE_SHA256_V1 = {
    RECOVERED7_EVIDENCE_RELATIVE: "c0a5196f94284bc78c49f1a981798c85b1fd5869237d54f30ba239321c3eb799",
    DIRECT_CONFIRMED_EVENTS_RELATIVE: "981c59f1131ae8c5f1bb17680986eccda9d85a44caf0f44d1711246283f04186",
    DIRECT_COORDINATE_PAIRS_RELATIVE: "0293909b9a3ab96063eda3e5eed12609793cc8837ed7e2cd33d8681d0f8249c9",
    DIRECT_LIGAND_ATOMS_RELATIVE: "b47d03598a077e6201e21585c683fe46a7423d99fae231b47c303657bad89c59",
    DIRECT_LIGAND_BONDS_RELATIVE: "007d3b7a57b5878389e1229ceeec999442a532923e475f32cf7bcaea0e580d7f",
    DIRECT_POCKET_ATOMS_RELATIVE: "77dc7777d44ec48ecc985c9c7d66d603756781455b7b3d5c9151dd5800ceaee9",
    DIRECT_FULL_LIGAND_ATOMS_RELATIVE: "0eeeab569545dc3e3c1ec7f12edb3a18d604bbbac9444b79f4d9e2a40c4d3b0f",
    DIRECT_PRE_WRITEBACK_RELATIVE: "32e7a66e8b2c1b1f87cacdd2c57d1b1dc868e3dc83cf7c843ef1585efed54aca",
    DIRECT_PRE_QA_RELATIVE: "a2cc8ddab41e6439e1d0b2577fdb3514aefb617881975226d6e6bd73ecad8c2d",
    BASELINE_LIGAND_EVIDENCE_RELATIVE: "982a9f89a89d3a4ad6a3e468cfd16d2fdfd5435cbf6d593e086fbd7fadd3ec73",
    BASELINE_PROTEIN_EVIDENCE_RELATIVE: "51f208c2582bc41c265fa35fa18e71e0e0d0634babe63b9735f084aa486a0d30",
    BASELINE_FINAL_GROUP_RELATIVE: "768c964f22e19a8fb6232b1fa26c531e53d023042abcd9b1bcca44df2b4f4416",
}

DIRECT_ROLE_PROPOSAL_RELATIVE_V1 = {
    "6DI9": Path("data/raw/covalent_small/metadata/BTK_C481_6DI9_GJJ_annotation_template.csv"),
    "5F2E": Path("data/raw/covalent_small/metadata/KRAS_G12C_5F2E_5UT_annotation_template.csv"),
    "6OIM": Path("data/raw/covalent_small/metadata/KRAS_G12C_6OIM_MOV_annotation_template.csv"),
}
DIRECT_ROLE_PROPOSAL_SHA256_V1 = {
    "6DI9": "f993728c5d605bbf9e17f9db0e9dc2e7d5b0bcebe9f561e54727ca46b8249f40",
    "5F2E": "3d81e379d086662398aebb77750e3dfacd3a4b11acbe11f23abdf0f20cbeabad",
    "6OIM": "c718277ba5ec2cb09edd36dbb841f4210c467fc94521fec036eb42594f95c14c",
}
PUBLISHED_GROUP_SPLIT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_unified_leakage_split_materialization_smoke_v0/"
    "covapie_leakage_group_split_assignment.csv"
)
PUBLISHED_GROUP_SPLIT_SHA256 = (
    "ed62fcf56ad87d8a49743517329c97aa98d3a781562fa403b4b43a9b9ea3ffc3"
)

_LOWER_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ID = re.compile(r"^[A-Z0-9][A-Z0-9_.:-]*$")
_LEAKAGE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_SAMPLE_IDENTITY = re.compile(
    r"^[A-Z0-9][A-Z0-9_.:-]*/[A-Z0-9][A-Z0-9_.:-]*$"
)
_CUMULATIVE_PROVENANCE_PATH_SCOPES_V1 = frozenset((
    "REPOSITORY_ROOT_RELATIVE", "REGISTRY_DIRECTORY_RELATIVE",
))
_CUMULATIVE_PROVENANCE_ARTIFACT_ROLES_V1 = frozenset((
    "PUBLISHED_EXPANSION_PIPELINE_RUN",
    "PUBLISHED_EXPANSION_MATERIALIZED_SAMPLE",
    "PUBLISHED_LEAKAGE_SPLIT_POLICY",
    "SUCCESSOR_EXPANSION_PIPELINE_RUN",
    "SUCCESSOR_EXPANSION_MATERIALIZED_SAMPLE",
))
_FORBIDDEN_REVIEWERS = {
    "auto", "chatgpt", "codex", "none", "placeholder", "synthetic",
    "system", "unknown",
}


@dataclass(frozen=True)
class AutomationOwnerV1:
    stage: str
    existing_owner: str
    pipeline_invoked: bool
    automatic: bool
    human_decision_possible: bool
    remaining_gap: str
    pipeline_consumes_published_artifact: bool = False


AUTOMATION_OWNER_MAP_V1 = (
    AutomationOwnerV1(
        "candidate discovery",
        "covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_v1.build_covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_artifacts_v1",
        False, True, False, "loads the SHA-bound published candidate inventory",
        True,
    ),
    AutomationOwnerV1(
        "download/acquisition",
        "covapie_cys_sg_exact12_targeted_structural_evidence_acquisition_execution_v1._execute_request_v1",
        True, True, False, "invoked only through the explicit bounded acquisition entry point",
    ),
    AutomationOwnerV1(
        "source verification",
        "covapie_cys_sg_exact12_targeted_structural_evidence_acquisition_execution_v1.validate_raw_mmcif_payload_v1",
        False, True, False, "main batch verifies immutable bytes; acquisition entry point invokes owner",
        True,
    ),
    AutomationOwnerV1(
        "event extraction",
        "covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1.recover_exact_struct_conn_event_v1",
        False, True, True, "batch consumes published event evidence; acquisition entry point invokes owner",
        True,
    ),
    AutomationOwnerV1(
        "endpoint mapping",
        "covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1.select_ligand_instance_atoms_v1",
        False, True, True, "consumes published unique endpoint mapping evidence",
        True,
    ),
    AutomationOwnerV1(
        "topology",
        "covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1.load_component_topology_authorities_v1",
        False, True, True, "consumes published canonical/pre-reaction graph evidence",
        True,
    ),
    AutomationOwnerV1(
        "pocket",
        "covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1.build_canonical_pocket_v1",
        False, True, False, "consumes published pocket atoms and coordinates",
        True,
    ),
    AutomationOwnerV1(
        "feature semantics",
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.project_type_symbols_to_checkpoint_heavy_v1",
        True, True, False, "unsupported non-H atoms reject the sample",
    ),
    AutomationOwnerV1(
        "POST",
        "covapie_exact16_post_geometry_partial_supervision_authority_v1",
        False, True, False, "expansion successor reuses its tolerance and source-derived invariants",
        True,
    ),
    AutomationOwnerV1(
        "role",
        "covapie_direct_attachment_optional_linker_runtime_v1.validate_role_profile_v1",
        True, True, True, "novel or ambiguous partitions require human gold",
    ),
    AutomationOwnerV1(
        "seed",
        "covapie_direct_attachment_optional_linker_runtime_v1.validate_minimal_seed_for_role_profile_v1",
        True, True, True, "ambiguous seed/anchors require human gold",
    ),
    AutomationOwnerV1(
        "family",
        "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1.approved_reaction_family_available",
        True, True, True, "new family identity always requires human approval",
    ),
    AutomationOwnerV1(
        "warhead rule",
        "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1.approved_warhead_rule_available",
        True, True, True, "new SMARTS always requires human approval",
    ),
    AutomationOwnerV1(
        "profile",
        "covapie_direct_attachment_optional_linker_runtime_v1.ROLE_PROFILES_V1",
        True, True, True, "unsupported profiles require a runtime extension",
    ),
    AutomationOwnerV1(
        "leakage",
        "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke.groups",
        False, True, False, "consumes complete leakage evidence and frozen group assignments",
        True,
    ),
    AutomationOwnerV1(
        "split",
        "covapie_unified_leakage_split_materialization_smoke_v0 policy semantics",
        False, True, False, "successor freezes existing splits and reuses ratio objective/tie-break",
        True,
    ),
    AutomationOwnerV1(
        "geometry authority",
        "covapie_exact16_post_geometry_partial_supervision_authority_v1",
        False, True, False, "source pair is recomputed by the expansion successor; PRE stays masked",
        True,
    ),
    AutomationOwnerV1(
        "materialization",
        "covapie_cys_sg_dataset_expansion_pipeline_v1.materialize_approved_successor_v1",
        True, True, False, "only explicit materialize-approved mode writes additive artifacts",
    ),
    AutomationOwnerV1(
        "tensorization",
        "covapie_cys_sg_dataset_expansion_pipeline_v1.tensorize_covapie_expanded_population_successor_v1",
        True, True, False, "identity-frozen Exact16 owner is not called for new identities",
    ),
)


@dataclass(frozen=True)
class ExpansionCandidateV1:
    candidate_identity: str
    pdb_id: str
    ligand_comp_id: str
    source_identity: str
    source_path: Path
    expected_source_sha256: str
    explicit_event_authoritative: bool
    conflicting_explicit_event: bool
    protein_endpoint_exact_cys_sg: bool
    ligand_endpoint_mapping_count: int
    retained_endpoint_mapping_count: int
    canonical_topology_valid: bool
    pocket_valid: bool
    atom_symbols: tuple[str, ...]
    chemistry_signature_sha256: str
    chemistry_signature_authoritative: bool
    canonical_ligand_smiles: str
    smarts_atom_ids: tuple[int | str, ...]
    reactive_ligand_atom_id: int | str | None
    reactive_atom_mapping_count: int
    retained_heavy_atoms: tuple[int | str, ...]
    scaffold_atoms: tuple[int | str, ...]
    linker_atoms: tuple[int | str, ...]
    warhead_atoms: tuple[int | str, ...]
    explicit_graph_bonds: tuple[tuple[int | str, int | str, str], ...]
    seed_atoms: tuple[int | str, ...]
    primary_anchor_atom: int | str | None
    direction_anchor_atom: int | str | None
    optional_plane_anchor_atom: int | str | None
    role_profile: str
    role_rule_id: str
    role_rule_version: str
    role_rule_match_count: int
    role_authority_published: bool
    baseline_leakage_evidence_complete: bool
    leakage_key: str
    leakage_conflict: bool
    duplicate_identity: bool
    post_distance_angstrom: float | None
    pre_reaction_graph_authoritative: bool = False
    formal_charge_authoritative: bool = False
    atom_map_numbers: tuple[tuple[int | str, int], ...] = ()
    atom_formal_charges: tuple[tuple[int | str, int], ...] = ()
    pre_reaction_bonds: tuple[tuple[int | str, int | str, str], ...] = ()
    protein_endpoint_atom_id: int | str | None = None
    source_event_protein_atom_id: int | str | None = None
    source_event_ligand_atom_id: int | str | None = None
    retained_reactive_atom_id: int | str | None = None
    ligand_atom_coordinates: tuple[
        tuple[int | str, str, float, float, float], ...
    ] = ()
    pocket_atom_coordinates: tuple[
        tuple[int | str, str, float, float, float], ...
    ] = ()
    prior_disposition: str = ""
    prior_blocking_reasons: tuple[str, ...] = ()
    pre_review_evidence_digest: str = ""
    machine_evidence_bindings: tuple[tuple[str, str], ...] = ()
    leakage_ligand_graph_sha256: str = ""
    leakage_ligand_scaffold_sha256: str = ""
    leakage_protein_accession: str = ""
    leakage_protein_sequence_sha256: str = ""
    leakage_protein_sequence: str = ""
    leakage_axis_keys: tuple[str, ...] = ()
    leakage_baseline_group_ids: tuple[str, ...] = ()
    source_event_protein_endpoint_descriptor: str = ""
    source_event_ligand_endpoint_descriptor: str = ""


@dataclass(frozen=True)
class ReusableChemistryAuthorityV1:
    authority_id: str
    authority_version: str
    approval_scope: str
    approved: bool
    cross_signature_propagation_allowed: bool
    chemistry_signature_sha256: str
    reaction_family_id: str
    reaction_family_version: str
    warhead_rule_id: str
    warhead_rule_version: str
    approved_warhead_smarts: str
    role_rule_id: str
    role_rule_version: str
    role_profile: str
    source_human_review_record_sha256: str
    pre_review_evidence_digest: str
    source_identity: str
    source_sha256: str
    reviewer_id: str
    review_rationale: str
    ligand_reactive_atom_map_number: int = 0
    warhead_atom_map_numbers: tuple[int, ...] = ()
    expected_pre_reaction_bond_orders: tuple[tuple[int, int, str], ...] = ()
    allowed_formal_charge_pattern: tuple[tuple[int, int], ...] = ()
    attachment_boundary_bond_order: str = ""
    source_human_review_record_canonical_json: str = ""


@dataclass(frozen=True)
class CandidateOutcomeV1:
    candidate_identity: str
    terminal_disposition: str
    blocking_reasons: tuple[str, ...]
    phase_statuses: tuple[tuple[str, str], ...]
    source_verified: bool
    mechanically_eligible: bool
    admitted_by: str
    chemistry_authority_id: str
    human_sample_decision_consumed: bool
    role_profile: str
    leakage_group_id: str
    assigned_split: str
    post_geometry_authority: bool
    pre_geometry_authority: bool
    pre_geometry_masked: bool
    materialization_ready: bool
    tensorization_ready: bool
    tensorization_owner: str
    materialization_performed: bool
    tensorization_performed: bool
    materialization_artifact_sha256: str
    tensorization_artifact_sha256: str


@dataclass(frozen=True)
class PipelineRunV1:
    pipeline_version: str
    successor_policy_id: str
    execution_mode: str
    dry_run: bool
    current_policy_requires_every_new_sample_human_assignment: bool
    outcomes: tuple[CandidateOutcomeV1, ...]
    aggregate: Mapping[str, int]
    authority_bindings: tuple[Mapping[str, Any], ...]
    automation_coverage: tuple[Mapping[str, Any], ...]
    review_queue_identities: tuple[str, ...]
    admitted_identities: tuple[str, ...]
    reusable_authority_registry_sha256: str


@dataclass(frozen=True)
class LeakageGroupAssignmentV1:
    leakage_key: str
    final_leakage_group_id: str
    member_count: int
    assigned_split: str
    frozen: bool
    member_identities: tuple[str, ...] = ()


@dataclass(frozen=True)
class CumulativeLeakageSourceArtifactV1:
    artifact_role: str
    path: str
    path_scope: str
    sha256: str


@dataclass(frozen=True)
class CumulativeExpansionLeakageGroupV1:
    leakage_key: str
    final_leakage_group_id: str
    assigned_split: str
    member_identities: tuple[str, ...]
    member_count: int


@dataclass(frozen=True)
class CumulativeExpansionLeakageRegistryV1:
    schema_version: str
    policy_id: str
    source_artifacts: tuple[CumulativeLeakageSourceArtifactV1, ...]
    groups: tuple[CumulativeExpansionLeakageGroupV1, ...]


@dataclass(frozen=True)
class SourceAcquisitionResultV1:
    candidate_identity: str
    source_status: str
    source_sha256: str
    network_attempted: bool
    atomic_promotion_performed: bool
    exact_event_recovered: bool
    explicit_connection_evidence_status: str
    event_status: str


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_sha(value: object) -> bool:
    return type(value) is str and _LOWER_SHA256.fullmatch(value) is not None


def _is_id(value: object) -> bool:
    return type(value) is str and _ID.fullmatch(value) is not None


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sha_bound_csv_rows_v1(repo_root: Path, relative: Path) -> list[dict[str, str]]:
    path = repo_root / relative
    expected = EVIDENCE_SHA256_V1.get(relative)
    if expected is None or _sha256(path.read_bytes()) != expected:
        raise ValueError("REAL_EXACT4_EVIDENCE_SHA256_MISMATCH:" + relative.as_posix())
    return _csv_rows(path)


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")


def automation_coverage_v1() -> tuple[Mapping[str, Any], ...]:
    return tuple(asdict(owner) for owner in AUTOMATION_OWNER_MAP_V1)


_BOND_ORDERS_V1 = frozenset(("single", "double", "triple", "aromatic"))


def _normalized_bond_v1(
    bond: Sequence[object], atom_identity: Mapping[int | str, int],
) -> tuple[int, int, str]:
    if len(bond) != 3 or bond[0] not in atom_identity or bond[1] not in atom_identity:
        raise ValueError("CHEMISTRY_BOND_ENDPOINT_INVALID")
    order = str(bond[2]).lower()
    if order not in _BOND_ORDERS_V1:
        raise ValueError("CHEMISTRY_BOND_ORDER_INVALID")
    left, right = atom_identity[bond[0]], atom_identity[bond[1]]
    return (min(left, right), max(left, right), order)


def build_exact_chemistry_signature_v1(
    candidate: ExpansionCandidateV1,
) -> str:
    """Build an identity-independent exact chemistry fingerprint.

    Sample/PDB/source/path fields are deliberately absent.  Atom-map authority
    is preferred; otherwise RDKit canonical ranks provide a candidate-only
    canonical identity that cannot itself create reusable approval authority.
    """

    try:
        from rdkit import Chem
    except ImportError as error:
        raise ValueError("RDKIT_CHEMISTRY_SIGNATURE_BUILDER_UNAVAILABLE") from error
    molecule = Chem.MolFromSmiles(candidate.canonical_ligand_smiles)
    if molecule is None or len(candidate.smarts_atom_ids) != molecule.GetNumAtoms():
        raise ValueError("CANONICAL_LIGAND_GRAPH_INVALID_FOR_SIGNATURE")
    if len(set(candidate.smarts_atom_ids)) != len(candidate.smarts_atom_ids):
        raise ValueError("CANONICAL_LIGAND_ATOM_IDS_NOT_UNIQUE")
    map_by_atom = dict(candidate.atom_map_numbers)
    if len(map_by_atom) != len(candidate.atom_map_numbers):
        raise ValueError("ATOM_MAP_NUMBER_AUTHORITY_DUPLICATE_ATOM")
    mapped = (
        set(map_by_atom) == set(candidate.smarts_atom_ids)
        and all(type(value) is int and value > 0 for value in map_by_atom.values())
        and len(set(map_by_atom.values())) == len(map_by_atom)
    )
    if mapped:
        atom_identity = map_by_atom
        identity_scheme = "authoritative_atom_map_number"
    else:
        ranks = tuple(int(value) + 1 for value in Chem.CanonicalRankAtoms(
            molecule, breakTies=True,
        ))
        atom_identity = dict(zip(candidate.smarts_atom_ids, ranks))
        identity_scheme = "candidate_only_rdkit_canonical_rank"
    canonical_molecule = Chem.Mol(molecule)
    for atom in canonical_molecule.GetAtoms():
        atom.SetAtomMapNum(0)
    canonical_smiles = Chem.MolToSmiles(
        canonical_molecule, canonical=True, isomericSmiles=True,
    )
    pre_source = (
        candidate.pre_reaction_bonds
        if candidate.pre_reaction_bonds else candidate.explicit_graph_bonds
    )
    pre_bonds = tuple(sorted(
        (_normalized_bond_v1(bond, atom_identity) for bond in pre_source),
        key=repr,
    ))
    charges_by_atom = dict(candidate.atom_formal_charges)
    if len(charges_by_atom) != len(candidate.atom_formal_charges):
        raise ValueError("FORMAL_CHARGE_AUTHORITY_DUPLICATE_ATOM")
    if charges_by_atom and set(charges_by_atom) != set(candidate.smarts_atom_ids):
        raise ValueError("FORMAL_CHARGE_AUTHORITY_NOT_EXHAUSTIVE")
    formal_charges = tuple(sorted(
        (
            atom_identity[atom_id],
            int(charges_by_atom.get(atom_id, molecule.GetAtomWithIdx(index).GetFormalCharge())),
        )
        for index, atom_id in enumerate(candidate.smarts_atom_ids)
    ))
    if candidate.reactive_ligand_atom_id not in atom_identity:
        reactive_identity: int | str = "UNRESOLVED"
    else:
        reactive_identity = atom_identity[candidate.reactive_ligand_atom_id]
    if not set(candidate.warhead_atoms).issubset(atom_identity):
        raise ValueError("WARHEAD_ATOM_NOT_IN_CANONICAL_GRAPH")
    scaffold_linker, linker_warhead, direct_boundary = _cross_role_boundaries_v1(
        candidate
    )
    attachment = direct_boundary if candidate.role_profile == DIRECT_PROFILE else linker_warhead
    attachment_semantics = tuple(sorted(
        (_normalized_bond_v1(bond, atom_identity) for bond in attachment),
        key=repr,
    ))
    payload = {
        "schema": "covapie_exact_chemistry_signature_v1",
        "canonical_pre_reaction_ligand_smiles": canonical_smiles,
        "atom_identity_scheme": identity_scheme,
        "atoms": tuple(sorted(
            (
                atom_identity[atom_id],
                molecule.GetAtomWithIdx(index).GetSymbol(),
                int(charges_by_atom.get(
                    atom_id, molecule.GetAtomWithIdx(index).GetFormalCharge()
                )),
            )
            for index, atom_id in enumerate(candidate.smarts_atom_ids)
        )),
        "pre_reaction_bonds": pre_bonds,
        "pre_reaction_graph_authoritative": candidate.pre_reaction_graph_authoritative,
        "formal_charge_semantics": formal_charges,
        "formal_charge_authoritative": candidate.formal_charge_authoritative,
        "reactive_ligand_atom": reactive_identity,
        "scaffold_atom_set": tuple(sorted(atom_identity[item] for item in candidate.scaffold_atoms)),
        "linker_atom_set": tuple(sorted(atom_identity[item] for item in candidate.linker_atoms)),
        "warhead_atom_set": tuple(sorted(atom_identity[item] for item in candidate.warhead_atoms)),
        "attachment_boundary": attachment_semantics,
        "role_profile": candidate.role_profile,
        "minimal_seed_atom_set": tuple(sorted(atom_identity[item] for item in candidate.seed_atoms)),
        "primary_anchor_atom": (
            atom_identity[candidate.primary_anchor_atom]
            if candidate.primary_anchor_atom in atom_identity else "UNRESOLVED"
        ),
        "direction_anchor_atom": (
            atom_identity[candidate.direction_anchor_atom]
            if candidate.direction_anchor_atom in atom_identity else "UNRESOLVED"
        ),
        "optional_plane_anchor_atom": (
            atom_identity[candidate.optional_plane_anchor_atom]
            if candidate.optional_plane_anchor_atom in atom_identity else None
        ),
    }
    return _sha256(_canonical_json(payload))


def build_pre_review_evidence_digest_v1(
    candidate: ExpansionCandidateV1,
) -> str:
    """Bind a review to immutable machine evidence, never to reviewed chemistry."""

    bindings = tuple(sorted(candidate.machine_evidence_bindings))
    if (
        len(bindings) != len(set(bindings))
        or any(not name or not _is_sha(digest) for name, digest in bindings)
    ):
        raise ValueError("PRE_REVIEW_MACHINE_EVIDENCE_BINDINGS_INVALID")
    payload = {
        "schema": "covapie_pre_review_evidence_binding_v1",
        "candidate_identity": candidate.candidate_identity,
        "source_identity": candidate.source_identity,
        "source_sha256": candidate.expected_source_sha256,
        "event_endpoints": {
            "protein": candidate.source_event_protein_atom_id,
            "ligand": candidate.source_event_ligand_atom_id,
            "retained_ligand": candidate.retained_reactive_atom_id,
            "protein_descriptor": (
                candidate.source_event_protein_endpoint_descriptor
            ),
            "ligand_descriptor": candidate.source_event_ligand_endpoint_descriptor,
        },
        "canonical_ligand_atom_namespace": candidate.smarts_atom_ids,
        "atom_map_numbers": candidate.atom_map_numbers,
        "machine_pre_reaction_graph_authoritative": (
            candidate.pre_reaction_graph_authoritative
        ),
        "machine_formal_charge_authoritative": candidate.formal_charge_authoritative,
        "machine_pre_reaction_bonds": candidate.pre_reaction_bonds,
        "machine_formal_charges": candidate.atom_formal_charges,
        "coordinate_evidence_sha256": _sha256(_canonical_json({
            "ligand": candidate.ligand_atom_coordinates,
            "pocket": candidate.pocket_atom_coordinates,
            "observed_post_distance_angstrom": candidate.post_distance_angstrom,
        })),
        "leakage_evidence": {
            "ligand_graph_sha256": candidate.leakage_ligand_graph_sha256,
            "ligand_scaffold_sha256": candidate.leakage_ligand_scaffold_sha256,
            "protein_accession": candidate.leakage_protein_accession,
            "protein_sequence_sha256": candidate.leakage_protein_sequence_sha256,
            "axis_keys": candidate.leakage_axis_keys,
            "baseline_group_ids": candidate.leakage_baseline_group_ids,
        },
        "machine_evidence_bindings": bindings,
    }
    return _sha256(_canonical_json(payload))


def with_pre_review_evidence_digest_v1(
    candidate: ExpansionCandidateV1,
) -> ExpansionCandidateV1:
    return replace(
        candidate,
        pre_review_evidence_digest=build_pre_review_evidence_digest_v1(candidate),
    )


def with_computed_chemistry_signature_v1(
    candidate: ExpansionCandidateV1, *, authoritative: bool,
) -> ExpansionCandidateV1:
    if type(authoritative) is not bool:
        raise ValueError("CHEMISTRY_SIGNATURE_AUTHORITY_FLAG_INVALID")
    if authoritative and (
        candidate.pre_reaction_graph_authoritative is not True
        or candidate.formal_charge_authoritative is not True
    ):
        raise ValueError("AUTHORITATIVE_SIGNATURE_REQUIRES_PRE_GRAPH_AND_CHARGE_AUTHORITY")
    return replace(
        candidate,
        chemistry_signature_sha256=build_exact_chemistry_signature_v1(candidate),
        chemistry_signature_authoritative=authoritative,
    )


def approval_record_digest_v1(record: Mapping[str, Any]) -> str:
    if type(record) is not dict:
        record = dict(record)
    canonical = {
        key: value for key, value in record.items()
        if key != "source_human_review_record_sha256"
    }
    return _sha256(_canonical_json(canonical))


def _approval_record_canonical_text_v1(record: Mapping[str, Any]) -> str:
    canonical = {
        key: value for key, value in record.items()
        if key != "source_human_review_record_sha256"
    }
    return _canonical_json(canonical).decode("utf-8").removesuffix("\n")


def _authority_mapping_v1(
    authority: ReusableChemistryAuthorityV1,
) -> Mapping[str, Any]:
    return asdict(authority)


def serialize_reusable_authority_registry_v1(
    authorities: Sequence[ReusableChemistryAuthorityV1],
) -> bytes:
    normalized = _validated_authority_registry_v1(authorities)
    return _canonical_json({
        "schema_version": REUSABLE_AUTHORITY_REGISTRY_SCHEMA_V1,
        "successor_policy_id": SUCCESSOR_POLICY_ID,
        "authorities": tuple(_authority_mapping_v1(item) for item in normalized),
    })


def _authority_from_mapping_v1(value: Mapping[str, Any]) -> ReusableChemistryAuthorityV1:
    expected = {item.name for item in fields(ReusableChemistryAuthorityV1)}
    if type(value) is not dict or set(value) != expected:
        raise ValueError("REUSABLE_AUTHORITY_REGISTRY_RECORD_SCHEMA_INVALID")
    converted = dict(value)
    for field_name in (
        "warhead_atom_map_numbers", "expected_pre_reaction_bond_orders",
        "allowed_formal_charge_pattern",
    ):
        raw = converted[field_name]
        if type(raw) not in (list, tuple):
            raise ValueError(f"REUSABLE_AUTHORITY_{field_name.upper()}_INVALID")
        converted[field_name] = tuple(
            tuple(item) if type(item) in (list, tuple) else item for item in raw
        )
    return ReusableChemistryAuthorityV1(**converted)


def load_reusable_authority_registry_v1(
    path: Path,
) -> tuple[ReusableChemistryAuthorityV1, ...]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("REUSABLE_AUTHORITY_REGISTRY_UNREADABLE") from error
    if (
        type(parsed) is not dict
        or set(parsed) != {"schema_version", "successor_policy_id", "authorities"}
        or parsed.get("schema_version") != REUSABLE_AUTHORITY_REGISTRY_SCHEMA_V1
        or parsed.get("successor_policy_id") != SUCCESSOR_POLICY_ID
        or type(parsed.get("authorities")) is not list
    ):
        raise ValueError("REUSABLE_AUTHORITY_REGISTRY_SCHEMA_INVALID")
    return _validated_authority_registry_v1(tuple(
        _authority_from_mapping_v1(item) for item in parsed["authorities"]
    ))


def _valid_cumulative_provenance_path_v1(value: object) -> bool:
    if type(value) is not str or not value or value.strip() != value:
        return False
    path = Path(value)
    return (
        not path.is_absolute()
        and value == path.as_posix()
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _validated_cumulative_expansion_leakage_registry_v1(
    registry: CumulativeExpansionLeakageRegistryV1,
) -> CumulativeExpansionLeakageRegistryV1:
    if type(registry) is not CumulativeExpansionLeakageRegistryV1:
        raise ValueError("CUMULATIVE_LEAKAGE_REGISTRY_TYPE_INVALID")
    if registry.schema_version != CUMULATIVE_EXPANSION_LEAKAGE_REGISTRY_SCHEMA_V1:
        raise ValueError("CUMULATIVE_LEAKAGE_REGISTRY_SCHEMA_INVALID")
    if registry.policy_id != CUMULATIVE_EXPANSION_LEAKAGE_POLICY_ID_V1:
        raise ValueError("CUMULATIVE_LEAKAGE_REGISTRY_POLICY_INVALID")
    if not registry.source_artifacts:
        raise ValueError("CUMULATIVE_LEAKAGE_PROVENANCE_EMPTY")
    artifacts: list[CumulativeLeakageSourceArtifactV1] = []
    seen_artifacts: set[tuple[str, str]] = set()
    policy_owner_count = 0
    run_artifact_count = 0
    materialized_artifact_count = 0
    for artifact in registry.source_artifacts:
        if type(artifact) is not CumulativeLeakageSourceArtifactV1:
            raise ValueError("CUMULATIVE_LEAKAGE_PROVENANCE_RECORD_TYPE_INVALID")
        if artifact.artifact_role not in _CUMULATIVE_PROVENANCE_ARTIFACT_ROLES_V1:
            raise ValueError("CUMULATIVE_LEAKAGE_PROVENANCE_ROLE_INVALID")
        if artifact.path_scope not in _CUMULATIVE_PROVENANCE_PATH_SCOPES_V1:
            raise ValueError("CUMULATIVE_LEAKAGE_PROVENANCE_PATH_SCOPE_INVALID")
        if not _valid_cumulative_provenance_path_v1(artifact.path):
            raise ValueError("CUMULATIVE_LEAKAGE_PROVENANCE_PATH_INVALID")
        if not _is_sha(artifact.sha256):
            raise ValueError("CUMULATIVE_LEAKAGE_PROVENANCE_SHA256_INVALID")
        identity = (artifact.path_scope, artifact.path)
        if identity in seen_artifacts:
            raise ValueError("CUMULATIVE_LEAKAGE_PROVENANCE_DUPLICATE_ARTIFACT")
        seen_artifacts.add(identity)
        policy_owner_count += artifact.artifact_role == "PUBLISHED_LEAKAGE_SPLIT_POLICY"
        run_artifact_count += artifact.artifact_role.endswith("PIPELINE_RUN")
        materialized_artifact_count += artifact.artifact_role.endswith(
            "MATERIALIZED_SAMPLE"
        )
        artifacts.append(artifact)
    if policy_owner_count != 1:
        raise ValueError("CUMULATIVE_LEAKAGE_POLICY_OWNER_NOT_EXACT_ONE")
    if run_artifact_count < 1 or materialized_artifact_count < 1:
        raise ValueError("CUMULATIVE_LEAKAGE_MEMBERSHIP_PROVENANCE_INCOMPLETE")

    if not registry.groups:
        raise ValueError("CUMULATIVE_LEAKAGE_GROUPS_EMPTY")
    groups: list[CumulativeExpansionLeakageGroupV1] = []
    seen_keys: set[str] = set()
    prior_group_by_key: dict[str, CumulativeExpansionLeakageGroupV1] = {}
    group_id_to_key: dict[str, str] = {}
    member_to_key: dict[str, str] = {}
    for group in registry.groups:
        if type(group) is not CumulativeExpansionLeakageGroupV1:
            raise ValueError("CUMULATIVE_LEAKAGE_GROUP_RECORD_TYPE_INVALID")
        if (
            type(group.leakage_key) is not str
            or _LEAKAGE_KEY.fullmatch(group.leakage_key) is None
        ):
            raise ValueError("CUMULATIVE_LEAKAGE_KEY_INVALID")
        if not _is_id(group.final_leakage_group_id):
            raise ValueError("CUMULATIVE_LEAKAGE_GROUP_ID_INVALID")
        if group.assigned_split not in split_owner.SPLITS:
            raise ValueError("CUMULATIVE_LEAKAGE_SPLIT_UNSUPPORTED")
        if group.leakage_key in seen_keys:
            prior_group = prior_group_by_key[group.leakage_key]
            if prior_group.final_leakage_group_id != group.final_leakage_group_id:
                raise ValueError("CUMULATIVE_LEAKAGE_KEY_GROUP_ID_CONFLICT")
            if prior_group.assigned_split != group.assigned_split:
                raise ValueError("CUMULATIVE_LEAKAGE_KEY_SPLIT_CONFLICT")
            raise ValueError("CUMULATIVE_LEAKAGE_DUPLICATE_KEY")
        seen_keys.add(group.leakage_key)
        prior_group_by_key[group.leakage_key] = group
        prior_key = group_id_to_key.get(group.final_leakage_group_id)
        if prior_key is not None and prior_key != group.leakage_key:
            raise ValueError("CUMULATIVE_LEAKAGE_GROUP_ID_KEY_CONFLICT")
        group_id_to_key[group.final_leakage_group_id] = group.leakage_key
        if (
            type(group.member_identities) is not tuple
            or not group.member_identities
            or tuple(sorted(group.member_identities)) != group.member_identities
            or len(set(group.member_identities)) != len(group.member_identities)
            or any(
                type(identity) is not str
                or _SAMPLE_IDENTITY.fullmatch(identity) is None
                for identity in group.member_identities
            )
        ):
            raise ValueError("CUMULATIVE_LEAKAGE_MEMBER_IDENTITIES_INVALID")
        if type(group.member_count) is not int or group.member_count != len(
            group.member_identities
        ):
            raise ValueError("CUMULATIVE_LEAKAGE_MEMBER_COUNT_MISMATCH")
        for identity in group.member_identities:
            prior_member_key = member_to_key.get(identity)
            if prior_member_key is not None and prior_member_key != group.leakage_key:
                raise ValueError("CUMULATIVE_LEAKAGE_MEMBER_GROUP_CONFLICT")
            member_to_key[identity] = group.leakage_key
        groups.append(group)
    return CumulativeExpansionLeakageRegistryV1(
        schema_version=registry.schema_version,
        policy_id=registry.policy_id,
        source_artifacts=tuple(sorted(
            artifacts,
            key=lambda item: (
                item.path_scope, item.path, item.artifact_role, item.sha256,
            ),
        )),
        groups=tuple(sorted(
            groups,
            key=lambda item: (item.final_leakage_group_id, item.leakage_key),
        )),
    )


def serialize_cumulative_expansion_leakage_registry_v1(
    registry: CumulativeExpansionLeakageRegistryV1,
) -> bytes:
    normalized = _validated_cumulative_expansion_leakage_registry_v1(registry)
    return _canonical_json({
        "schema_version": normalized.schema_version,
        "policy_id": normalized.policy_id,
        "provenance": {
            "source_artifacts": tuple(
                asdict(item) for item in normalized.source_artifacts
            ),
        },
        "groups": tuple(asdict(item) for item in normalized.groups),
    })


def _cumulative_source_artifact_from_mapping_v1(
    value: object,
) -> CumulativeLeakageSourceArtifactV1:
    if type(value) is not dict or set(value) != {
        "artifact_role", "path", "path_scope", "sha256",
    }:
        raise ValueError("CUMULATIVE_LEAKAGE_PROVENANCE_RECORD_SCHEMA_INVALID")
    return CumulativeLeakageSourceArtifactV1(**value)


def _cumulative_group_from_mapping_v1(
    value: object,
) -> CumulativeExpansionLeakageGroupV1:
    if type(value) is not dict or set(value) != {
        "leakage_key", "final_leakage_group_id", "assigned_split",
        "member_identities", "member_count",
    } or type(value.get("member_identities")) is not list:
        raise ValueError("CUMULATIVE_LEAKAGE_GROUP_RECORD_SCHEMA_INVALID")
    converted = dict(value)
    converted["member_identities"] = tuple(converted["member_identities"])
    return CumulativeExpansionLeakageGroupV1(**converted)


def _record_cumulative_provenance_claim_v1(
    claims: dict[str, tuple[str, str]],
    *,
    identity: object,
    group_id: object,
    split: object,
) -> None:
    if (
        type(identity) is not str
        or _SAMPLE_IDENTITY.fullmatch(identity) is None
        or type(group_id) is not str
        or not _is_id(group_id)
        or split not in split_owner.SPLITS
    ):
        raise ValueError("CUMULATIVE_LEAKAGE_PROVENANCE_CLAIM_INVALID")
    claim = (group_id, split)
    if identity in claims and claims[identity] != claim:
        raise ValueError("CUMULATIVE_LEAKAGE_PROVENANCE_CLAIM_CONFLICT")
    claims[identity] = claim


def _verify_cumulative_expansion_leakage_provenance_v1(
    registry: CumulativeExpansionLeakageRegistryV1,
    *,
    registry_path: Path,
    repo_root: Path,
) -> None:
    repo_root = repo_root.resolve()
    registry_directory = registry_path.resolve().parent
    run_claims: dict[str, tuple[str, str]] = {}
    materialized_claims: dict[str, tuple[str, str]] = {}
    for artifact in registry.source_artifacts:
        base = (
            repo_root
            if artifact.path_scope == "REPOSITORY_ROOT_RELATIVE"
            else registry_directory
        )
        source_path = (base / artifact.path).resolve()
        if not source_path.is_relative_to(base) or not source_path.is_file():
            raise ValueError("CUMULATIVE_LEAKAGE_PROVENANCE_SOURCE_MISSING")
        payload = source_path.read_bytes()
        if _sha256(payload) != artifact.sha256:
            raise ValueError("CUMULATIVE_LEAKAGE_PROVENANCE_SOURCE_SHA256_MISMATCH")
        if artifact.artifact_role == "PUBLISHED_LEAKAGE_SPLIT_POLICY":
            if (
                artifact.path_scope != "REPOSITORY_ROOT_RELATIVE"
                or artifact.path != PUBLISHED_GROUP_SPLIT_RELATIVE.as_posix()
                or artifact.sha256 != PUBLISHED_GROUP_SPLIT_SHA256
            ):
                raise ValueError("CUMULATIVE_LEAKAGE_POLICY_OWNER_INVALID")
            continue
        try:
            parsed = json.loads(payload)
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(
                "CUMULATIVE_LEAKAGE_PROVENANCE_ARTIFACT_UNREADABLE"
            ) from error
        if artifact.artifact_role.endswith("PIPELINE_RUN"):
            if (
                type(parsed) is not dict
                or parsed.get("pipeline_version") != PIPELINE_VERSION
                or type(parsed.get("outcomes")) is not list
            ):
                raise ValueError(
                    "CUMULATIVE_LEAKAGE_PIPELINE_RUN_PROVENANCE_INVALID"
                )
            for outcome in parsed["outcomes"]:
                if (
                    type(outcome) is dict
                    and outcome.get("leakage_group_id") not in (None, "", "NONE")
                    and outcome.get("assigned_split") not in (None, "", "NONE")
                ):
                    _record_cumulative_provenance_claim_v1(
                        run_claims,
                        identity=outcome.get("candidate_identity"),
                        group_id=outcome.get("leakage_group_id"),
                        split=outcome.get("assigned_split"),
                    )
        else:
            if (
                type(parsed) is not dict
                or parsed.get("schema_version") != MATERIALIZATION_SCHEMA_V1
                or parsed.get("materialization_performed") is not True
            ):
                raise ValueError(
                    "CUMULATIVE_LEAKAGE_MATERIALIZED_PROVENANCE_INVALID"
                )
            _record_cumulative_provenance_claim_v1(
                materialized_claims,
                identity=parsed.get("candidate_identity"),
                group_id=parsed.get("leakage_group_id"),
                split=parsed.get("assigned_split"),
            )
    for group in registry.groups:
        expected = (group.final_leakage_group_id, group.assigned_split)
        for identity in group.member_identities:
            if (
                run_claims.get(identity) != expected
                or materialized_claims.get(identity) != expected
            ):
                raise ValueError(
                    "CUMULATIVE_LEAKAGE_MEMBER_PROVENANCE_MISMATCH"
                )


def load_cumulative_expansion_leakage_registry_v1(
    path: Path,
    *,
    repo_root: Path,
) -> CumulativeExpansionLeakageRegistryV1:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("CUMULATIVE_LEAKAGE_REGISTRY_UNREADABLE") from error
    if (
        type(parsed) is not dict
        or set(parsed) != {"schema_version", "policy_id", "provenance", "groups"}
        or type(parsed.get("provenance")) is not dict
        or set(parsed["provenance"]) != {"source_artifacts"}
        or type(parsed["provenance"].get("source_artifacts")) is not list
        or type(parsed.get("groups")) is not list
    ):
        raise ValueError("CUMULATIVE_LEAKAGE_REGISTRY_SCHEMA_INVALID")
    registry = _validated_cumulative_expansion_leakage_registry_v1(
        CumulativeExpansionLeakageRegistryV1(
            schema_version=parsed["schema_version"],
            policy_id=parsed["policy_id"],
            source_artifacts=tuple(
                _cumulative_source_artifact_from_mapping_v1(item)
                for item in parsed["provenance"]["source_artifacts"]
            ),
            groups=tuple(
                _cumulative_group_from_mapping_v1(item)
                for item in parsed["groups"]
            ),
        )
    )
    _verify_cumulative_expansion_leakage_provenance_v1(
        registry, registry_path=path, repo_root=repo_root,
    )
    return registry


def merge_published_and_cumulative_leakage_groups_v1(
    published_groups: Sequence[LeakageGroupAssignmentV1],
    cumulative_registry: CumulativeExpansionLeakageRegistryV1,
) -> tuple[LeakageGroupAssignmentV1, ...]:
    registry = _validated_cumulative_expansion_leakage_registry_v1(
        cumulative_registry
    )
    if type(published_groups) not in (tuple, list) or not published_groups:
        raise ValueError("PUBLISHED_LEAKAGE_GROUPS_INVALID")
    published_keys: set[str] = set()
    published_ids: set[str] = set()
    normalized_published: list[LeakageGroupAssignmentV1] = []
    for group in published_groups:
        if (
            type(group) is not LeakageGroupAssignmentV1
            or group.frozen is not True
            or group.assigned_split not in split_owner.SPLITS
            or group.member_count <= 0
            or not group.leakage_key
            or not group.final_leakage_group_id
            or group.leakage_key in published_keys
            or group.final_leakage_group_id in published_ids
        ):
            raise ValueError("PUBLISHED_LEAKAGE_GROUPS_INVALID")
        published_keys.add(group.leakage_key)
        published_ids.add(group.final_leakage_group_id)
        normalized_published.append(group)
    cumulative_keys = {group.leakage_key for group in registry.groups}
    cumulative_ids = {group.final_leakage_group_id for group in registry.groups}
    if published_keys & cumulative_keys or published_ids & cumulative_ids:
        raise ValueError("CUMULATIVE_LEAKAGE_HISTORICAL_BASELINE_OVERLAP")
    combined = [*normalized_published, *(
        LeakageGroupAssignmentV1(
            leakage_key=group.leakage_key,
            final_leakage_group_id=group.final_leakage_group_id,
            member_count=group.member_count,
            assigned_split=group.assigned_split,
            frozen=True,
            member_identities=group.member_identities,
        )
        for group in registry.groups
    )]
    return tuple(sorted(
        combined,
        key=lambda item: (item.final_leakage_group_id, item.leakage_key),
    ))


def verify_existing_source_v1(path: Path, expected_sha256: str) -> str:
    if not path.is_file():
        return MISSING_SOURCE
    if not _is_sha(expected_sha256):
        return SOURCE_SHA_MISMATCH
    return (
        "SOURCE_ALREADY_PRESENT_AND_VERIFIED"
        if _sha256(path.read_bytes()) == expected_sha256
        else SOURCE_SHA_MISMATCH
    )


def _published_acquisition_request_v1(
    candidate_identity: str, repo_root: Path,
) -> tuple[acquisition_owner.PublishedAuthority, Mapping[str, str]]:
    authority = acquisition_owner.load_and_validate_published_authority_v1(repo_root)
    matches = [
        row for row in authority.request_rows
        if f"{row['pdb_id']}/{row['expected_ligand_component_id']}"
        == candidate_identity
    ]
    if len(matches) != 1:
        raise ValueError("ACQUISITION_IDENTITY_NOT_EXACT_PUBLISHED_REQUEST")
    return authority, matches[0]


def acquire_or_verify_published_source_v1(
    *,
    candidate_identity: str,
    destination_root: Path,
    authority_repo_root: Path,
    expected_source_sha256: str | None = None,
    transport: Callable[[str, int], acquisition_owner.TransportResponse] | None = None,
) -> SourceAcquisitionResultV1:
    """Invoke the exact published atomic acquisition and Stage-B0 event owners."""

    _, request = _published_acquisition_request_v1(
        candidate_identity, authority_repo_root
    )
    selected_transport = transport or acquisition_owner._urllib_transport_v1
    record = acquisition_owner._execute_request_v1(
        request, repo_root=destination_root, transport=selected_transport
    )
    source_status = {
        "REUSED_EXISTING_VALID": "SOURCE_ALREADY_PRESENT_AND_VERIFIED",
        "DOWNLOADED_AND_VERIFIED": "ACQUIRED_AND_VERIFIED",
        "FAILED_TRANSPORT": "ACQUISITION_REQUIRED_BUT_UNAVAILABLE",
        "FAILED_EXISTING_INVALID_NO_OVERWRITE": SOURCE_SHA_MISMATCH,
    }.get(str(record["action_taken"]), "ACQUISITION_FAILED")
    final_path = destination_root / str(request["destination_identity"])
    actual_sha = str(record.get("final_sha256", "NONE"))
    if (
        source_status in {
            "SOURCE_ALREADY_PRESENT_AND_VERIFIED", "ACQUIRED_AND_VERIFIED"
        }
        and expected_source_sha256 is not None
        and actual_sha != expected_source_sha256
    ):
        source_status = SOURCE_SHA_MISMATCH

    recovered = False
    evidence_status = "NOT_EVALUATED_ACQUISITION_INVALID"
    event_status = "ACQUISITION_INVALID"
    if source_status in {
        "SOURCE_ALREADY_PRESENT_AND_VERIFIED", "ACQUIRED_AND_VERIFIED"
    }:
        stage_rows = _csv_rows(authority_repo_root / EXPANDED_CANDIDATE_RELATIVE)
        pdb_id, ligand = candidate_identity.split("/", 1)
        stage_matches = [
            row for row in stage_rows
            if row["pdb_id"] == pdb_id and row["ligand_component_id"] == ligand
        ]
        if len(stage_matches) != 1:
            raise ValueError("ACQUIRED_CANDIDATE_STAGE_A_ROW_NOT_EXACT_ONE")
        decision = structural_recovery_owner.recover_exact_struct_conn_event_v1(
            final_path.read_text(encoding="utf-8"), stage_matches[0]
        )
        recovered = decision.recovered
        evidence_status = decision.explicit_connection_evidence_status
        event_status = decision.status
    return SourceAcquisitionResultV1(
        candidate_identity=candidate_identity,
        source_status=source_status,
        source_sha256=actual_sha,
        network_attempted=bool(record["network_attempted"]),
        atomic_promotion_performed=bool(record["atomic_promotion_performed"]),
        exact_event_recovered=recovered,
        explicit_connection_evidence_status=evidence_status,
        event_status=event_status,
    )


def _authority_schema_reasons_v1(
    authority: ReusableChemistryAuthorityV1,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not _is_id(authority.authority_id) or not _is_id(authority.authority_version):
        reasons.append("AUTHORITY_ID_OR_VERSION_INVALID")
    if authority.approval_scope != "EXACT_CHEMISTRY_SIGNATURE_REUSABLE":
        reasons.append("AUTHORITY_SCOPE_NOT_EXACT_SIGNATURE_REUSABLE")
    if authority.approved is not True:
        reasons.append("AUTHORITY_NOT_HUMAN_APPROVED")
    if authority.cross_signature_propagation_allowed is not False:
        reasons.append("CROSS_SIGNATURE_PROPAGATION_FORBIDDEN")
    if not _is_sha(authority.chemistry_signature_sha256):
        reasons.append("AUTHORITY_CHEMISTRY_SIGNATURE_INVALID")
    for value, reason in (
        (authority.reaction_family_id, "REACTION_FAMILY_ID_INVALID"),
        (authority.reaction_family_version, "REACTION_FAMILY_VERSION_INVALID"),
        (authority.warhead_rule_id, "WARHEAD_RULE_ID_INVALID"),
        (authority.warhead_rule_version, "WARHEAD_RULE_VERSION_INVALID"),
        (authority.role_rule_id, "ROLE_RULE_ID_INVALID"),
        (authority.role_rule_version, "ROLE_RULE_VERSION_INVALID"),
    ):
        if not _is_id(value):
            reasons.append(reason)
    if authority.role_profile not in SUPPORTED_PROFILES:
        reasons.append("AUTHORITY_PROFILE_UNSUPPORTED")
    if not authority.approved_warhead_smarts.strip():
        reasons.append("APPROVED_WARHEAD_SMARTS_MISSING")
    if not _is_sha(authority.source_human_review_record_sha256):
        reasons.append("HUMAN_REVIEW_RECORD_SHA_INVALID")
    if not _is_sha(authority.pre_review_evidence_digest):
        reasons.append("AUTHORITY_PRE_REVIEW_EVIDENCE_DIGEST_INVALID")
    if not authority.source_identity.strip():
        reasons.append("AUTHORITY_SOURCE_IDENTITY_INVALID")
    if not _is_sha(authority.source_sha256):
        reasons.append("AUTHORITY_SOURCE_SHA256_INVALID")
    if (
        not authority.reviewer_id.strip()
        or authority.reviewer_id.strip().lower() in _FORBIDDEN_REVIEWERS
    ):
        reasons.append("HUMAN_REVIEWER_ID_INVALID")
    if not authority.review_rationale.strip():
        reasons.append("HUMAN_REVIEW_RATIONALE_MISSING")
    if (
        type(authority.ligand_reactive_atom_map_number) is not int
        or authority.ligand_reactive_atom_map_number <= 0
    ):
        reasons.append("AUTHORITY_REACTIVE_ATOM_MAP_NUMBER_INVALID")
    if (
        not authority.warhead_atom_map_numbers
        or any(type(value) is not int or value <= 0 for value in authority.warhead_atom_map_numbers)
        or len(set(authority.warhead_atom_map_numbers)) != len(authority.warhead_atom_map_numbers)
        or authority.ligand_reactive_atom_map_number not in authority.warhead_atom_map_numbers
    ):
        reasons.append("AUTHORITY_WARHEAD_ATOM_MAP_NUMBERS_INVALID")
    if (
        not authority.expected_pre_reaction_bond_orders
        or any(
            len(item) != 3
            or type(item[0]) is not int or type(item[1]) is not int
            or item[0] <= 0 or item[1] <= 0 or item[0] == item[1]
            or str(item[2]).lower() not in _BOND_ORDERS_V1
            for item in authority.expected_pre_reaction_bond_orders
        )
    ):
        reasons.append("AUTHORITY_PRE_REACTION_BOND_ORDERS_INVALID")
    if (
        not authority.allowed_formal_charge_pattern
        or any(
            len(item) != 2 or type(item[0]) is not int or item[0] <= 0
            or type(item[1]) is not int
            for item in authority.allowed_formal_charge_pattern
        )
    ):
        reasons.append("AUTHORITY_FORMAL_CHARGE_PATTERN_INVALID")
    if authority.attachment_boundary_bond_order not in _BOND_ORDERS_V1:
        reasons.append("AUTHORITY_ATTACHMENT_BOUNDARY_BOND_ORDER_INVALID")
    try:
        review_record = json.loads(authority.source_human_review_record_canonical_json)
    except (TypeError, json.JSONDecodeError):
        review_record = None
    if (
        type(review_record) is not dict
        or _approval_record_canonical_text_v1(review_record)
        != authority.source_human_review_record_canonical_json
        or approval_record_digest_v1(review_record)
        != authority.source_human_review_record_sha256
    ):
        reasons.append("AUTHORITY_HUMAN_REVIEW_RECORD_PROVENANCE_INVALID")
    elif any((
        review_record.get("review_status") != "APPROVE",
        review_record.get("review_scope") != authority.approval_scope,
        review_record.get("pre_review_evidence_digest")
        != authority.pre_review_evidence_digest,
        review_record.get("bound_source_identity") != authority.source_identity,
        review_record.get("bound_source_sha256") != authority.source_sha256,
        review_record.get("expected_final_chemistry_signature_sha256")
        not in (None, "", authority.chemistry_signature_sha256),
        review_record.get("reaction_family_id") != authority.reaction_family_id,
        review_record.get("reaction_family_version") != authority.reaction_family_version,
        review_record.get("warhead_rule_id") != authority.warhead_rule_id,
        review_record.get("warhead_rule_version") != authority.warhead_rule_version,
        review_record.get("approved_warhead_smarts") != authority.approved_warhead_smarts,
        review_record.get("role_rule_id") != authority.role_rule_id,
        review_record.get("role_rule_version") != authority.role_rule_version,
        review_record.get("role_profile") != authority.role_profile,
        review_record.get("reviewer_id") != authority.reviewer_id,
        review_record.get("review_rationale") != authority.review_rationale,
    )):
        reasons.append("AUTHORITY_HUMAN_REVIEW_RECORD_SEMANTICS_MISMATCH")
    return tuple(dict.fromkeys(reasons))


def _validated_authority_registry_v1(
    authorities: Sequence[ReusableChemistryAuthorityV1],
) -> tuple[ReusableChemistryAuthorityV1, ...]:
    if type(authorities) not in (list, tuple):
        raise ValueError("REUSABLE_AUTHORITY_REGISTRY_CONTAINER_INVALID")
    normalized = tuple(sorted(
        authorities,
        key=lambda item: (item.authority_id, item.authority_version),
    ))
    seen_identity: dict[tuple[str, str], ReusableChemistryAuthorityV1] = {}
    for authority in normalized:
        if type(authority) is not ReusableChemistryAuthorityV1:
            raise ValueError("REUSABLE_AUTHORITY_REGISTRY_RECORD_TYPE_INVALID")
        reasons = _authority_schema_reasons_v1(authority)
        if reasons:
            raise ValueError("REUSABLE_AUTHORITY_REGISTRY_RECORD_INVALID:" + ";".join(reasons))
        identity = (authority.authority_id, authority.authority_version)
        if identity in seen_identity:
            raise ValueError("REUSABLE_AUTHORITY_REGISTRY_DUPLICATE_IDENTITY")
        seen_identity[identity] = authority
    return normalized


def _smarts_match_v1(
    candidate: ExpansionCandidateV1, approved_smarts: str,
) -> tuple[int, tuple[int | str, ...], str]:
    if not candidate.canonical_ligand_smiles or not approved_smarts.strip():
        return 0, (), "SMARTS_OR_CANONICAL_SMILES_MISSING"
    try:
        from rdkit import Chem
    except ImportError:
        return 0, (), "RDKIT_SMARTS_MATCHER_UNAVAILABLE"
    molecule = Chem.MolFromSmiles(candidate.canonical_ligand_smiles)
    query = Chem.MolFromSmarts(approved_smarts)
    if molecule is None:
        return 0, (), "CANONICAL_LIGAND_SMILES_INVALID"
    if query is None:
        return 0, (), "APPROVED_WARHEAD_SMARTS_INVALID"
    if len(candidate.smarts_atom_ids) != molecule.GetNumAtoms():
        return 0, (), "SMARTS_ATOM_ID_MAPPING_INVALID"
    matches = tuple(molecule.GetSubstructMatches(query, uniquify=True))
    if len(matches) != 1:
        return len(matches), (), "APPROVED_SMARTS_MATCH_NOT_EXACT_ONE"
    return 1, tuple(candidate.smarts_atom_ids[index] for index in matches[0]), "NONE"


def _cross_role_boundaries_v1(
    candidate: ExpansionCandidateV1,
) -> tuple[
    tuple[tuple[int | str, int | str, str], ...],
    tuple[tuple[int | str, int | str, str], ...],
    tuple[tuple[int | str, int | str, str], ...],
]:
    scaffold = set(candidate.scaffold_atoms)
    linker = set(candidate.linker_atoms)
    warhead = set(candidate.warhead_atoms)
    scaffold_linker: list[tuple[int | str, int | str, str]] = []
    linker_warhead: list[tuple[int | str, int | str, str]] = []
    scaffold_warhead: list[tuple[int | str, int | str, str]] = []
    for left, right, order in candidate.explicit_graph_bonds:
        if left in scaffold and right in linker:
            scaffold_linker.append((left, right, order))
        elif right in scaffold and left in linker:
            scaffold_linker.append((right, left, order))
        elif left in linker and right in warhead:
            linker_warhead.append((left, right, order))
        elif right in linker and left in warhead:
            linker_warhead.append((right, left, order))
        elif left in scaffold and right in warhead:
            scaffold_warhead.append((left, right, order))
        elif right in scaffold and left in warhead:
            scaffold_warhead.append((right, left, order))
    return (
        tuple(sorted(scaffold_linker, key=repr)),
        tuple(sorted(linker_warhead, key=repr)),
        tuple(sorted(scaffold_warhead, key=repr)),
    )


def _validate_role_seed_profile_v1(
    candidate: ExpansionCandidateV1,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if candidate.role_profile not in SUPPORTED_PROFILES:
        return ("UNSUPPORTED_PROFILE",)
    _, _, direct_boundaries = _cross_role_boundaries_v1(candidate)
    role = role_profile_owner.validate_role_profile_v1(
        role_profile=candidate.role_profile,
        retained_heavy_atoms=candidate.retained_heavy_atoms,
        scaffold_atoms=candidate.scaffold_atoms,
        linker_atoms=candidate.linker_atoms,
        warhead_atoms=candidate.warhead_atoms,
        reactive_atom_id=candidate.reactive_ligand_atom_id,
        direct_scaffold_warhead_boundaries=direct_boundaries,
        explicit_graph_bonds=candidate.explicit_graph_bonds,
    )
    reasons.extend(f"ROLE_{reason.upper()}" for reason in role.reasons)
    scaffold_linker, linker_warhead, _ = _cross_role_boundaries_v1(candidate)
    if candidate.role_profile == STRICT_PROFILE:
        if len(scaffold_linker) != 1:
            reasons.append("SCAFFOLD_LINKER_BOUNDARY_NOT_EXACT_ONE")
        if len(linker_warhead) != 1:
            reasons.append("LINKER_WARHEAD_BOUNDARY_NOT_EXACT_ONE")
    seed = role_profile_owner.validate_minimal_seed_for_role_profile_v1(
        role_profile=candidate.role_profile,
        seed_atoms=candidate.seed_atoms,
        scaffold_atoms=candidate.scaffold_atoms,
        linker_atoms=candidate.linker_atoms,
        warhead_atoms=candidate.warhead_atoms,
        explicit_graph_bonds=candidate.explicit_graph_bonds,
        primary_anchor_atom_id=candidate.primary_anchor_atom,
        direct_boundary=role.direct_scaffold_warhead_boundary,
    )
    reasons.extend(f"SEED_{reason.upper()}" for reason in seed.reasons)
    seed_set = set(candidate.seed_atoms)
    if candidate.primary_anchor_atom not in seed_set:
        reasons.append("PRIMARY_ANCHOR_OUTSIDE_SEED")
    if candidate.direction_anchor_atom not in seed_set:
        reasons.append("DIRECTION_ANCHOR_OUTSIDE_SEED")
    if candidate.direction_anchor_atom == candidate.primary_anchor_atom:
        reasons.append("DIRECTION_ANCHOR_NOT_DISTINCT")
    if (
        candidate.optional_plane_anchor_atom is not None
        and candidate.optional_plane_anchor_atom not in seed_set
    ):
        reasons.append("PLANE_ANCHOR_OUTSIDE_SEED")
    if (
        candidate.optional_plane_anchor_atom is not None
        and candidate.optional_plane_anchor_atom
        in {candidate.primary_anchor_atom, candidate.direction_anchor_atom}
    ):
        reasons.append("PLANE_ANCHOR_NOT_DISTINCT")
    return tuple(dict.fromkeys(reasons))


def _mechanical_eligibility_reasons_v1(
    candidate: ExpansionCandidateV1,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if candidate.explicit_event_authoritative is not True:
        reasons.append("AUTHORITATIVE_EXPLICIT_COVALENT_EVENT_MISSING")
    if candidate.conflicting_explicit_event is not False:
        reasons.append("CONFLICTING_EXPLICIT_EVENT")
    if candidate.protein_endpoint_exact_cys_sg is not True:
        reasons.append("PROTEIN_ENDPOINT_NOT_EXACT_CYS_SG")
    if candidate.ligand_endpoint_mapping_count != 1:
        reasons.append("LIGAND_ENDPOINT_MAPPING_NOT_EXACT_ONE")
    if candidate.retained_endpoint_mapping_count != 1:
        reasons.append("RETAINED_ENDPOINT_MAPPING_NOT_EXACT_ONE")
    if candidate.canonical_topology_valid is not True:
        reasons.append("CANONICAL_TOPOLOGY_INVALID")
    if candidate.pocket_valid is not True:
        reasons.append("POCKET_INVALID")
    if not candidate.atom_symbols:
        reasons.append("MODEL_ATOM_SYMBOLS_MISSING")
    else:
        projection = feature_semantics_owner.project_type_symbols_to_checkpoint_heavy_v1(
            candidate.atom_symbols
        )
        if projection.sample_rejected:
            reasons.append("UNSUPPORTED_NONHYDROGEN_MODEL_ATOM")
        if any(
            symbol_class not in {
                "supported_checkpoint_heavy_atom", "explicit_hydrogen"
            }
            for symbol_class in projection.symbol_classes
        ):
            reasons.append("UNKNOWN_OR_OTHER_FEATURE_CHANNEL_PRESENT")
    if (
        type(candidate.post_distance_angstrom) is not float
        or not math.isfinite(candidate.post_distance_angstrom)
        or candidate.post_distance_angstrom <= 0
    ):
        reasons.append("POST_COORDINATE_PAIR_NOT_FINITE_SOURCE_DERIVED")
    return tuple(dict.fromkeys(reasons))


def _candidate_assignment_sha256_v1(candidate: ExpansionCandidateV1) -> str:
    return _sha256(
        _canonical_json({
            "candidate_identity": candidate.candidate_identity,
            "source_identity": candidate.source_identity,
            "source_sha256": candidate.expected_source_sha256,
            "pre_review_evidence_digest": candidate.pre_review_evidence_digest,
        })
    )


def _atom_tuple_v1(value: object, field: str, *, allow_empty: bool = False) -> tuple[Any, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field}_CONTAINER_INVALID")
    result = tuple(value)
    if not allow_empty and not result:
        raise ValueError(f"{field}_EMPTY")
    if len(result) != len(set(result)):
        raise ValueError(f"{field}_DUPLICATE")
    if any(type(atom) not in (int, str) or type(atom) is bool for atom in result):
        raise ValueError(f"{field}_ATOM_ID_INVALID")
    return result


def _approval_pre_bonds_v1(value: object) -> tuple[tuple[int, int, str], ...]:
    if type(value) not in (list, tuple) or not value:
        raise ValueError("EXPECTED_PRE_REACTION_BOND_ORDERS_INVALID")
    result: list[tuple[int, int, str]] = []
    for item in value:
        if (
            type(item) not in (list, tuple) or len(item) != 3
            or type(item[0]) is not int or type(item[1]) is not int
            or item[0] <= 0 or item[1] <= 0 or item[0] == item[1]
            or str(item[2]).lower() not in _BOND_ORDERS_V1
        ):
            raise ValueError("EXPECTED_PRE_REACTION_BOND_ORDERS_INVALID")
        result.append((min(item[0], item[1]), max(item[0], item[1]), str(item[2]).lower()))
    if len(result) != len(set(result)):
        raise ValueError("EXPECTED_PRE_REACTION_BOND_ORDERS_DUPLICATE")
    return tuple(sorted(result))


def _approval_formal_charges_v1(value: object) -> tuple[tuple[int, int], ...]:
    if type(value) is not dict or not value:
        raise ValueError("ALLOWED_FORMAL_CHARGE_PATTERN_INVALID")
    result: list[tuple[int, int]] = []
    for key, charge in value.items():
        try:
            atom_map = int(key)
        except (TypeError, ValueError) as error:
            raise ValueError("ALLOWED_FORMAL_CHARGE_PATTERN_INVALID") from error
        if atom_map <= 0 or type(charge) is not int:
            raise ValueError("ALLOWED_FORMAL_CHARGE_PATTERN_INVALID")
        result.append((atom_map, charge))
    if len(result) != len({item[0] for item in result}):
        raise ValueError("ALLOWED_FORMAL_CHARGE_PATTERN_DUPLICATE_MAP")
    return tuple(sorted(result))


def _reviewed_pre_graph_candidate_fields_v1(
    candidate: ExpansionCandidateV1,
    approved_pre_bonds: tuple[tuple[int, int, str], ...],
    approved_charges: tuple[tuple[int, int], ...],
) -> Mapping[str, Any]:
    """Validate reviewed PRE chemistry without replacing authoritative representation."""

    if (
        candidate.pre_reaction_graph_authoritative is True
        and candidate.formal_charge_authoritative is True
    ):
        retained_atoms = tuple(candidate.retained_heavy_atoms)
        map_by_atom = dict(candidate.atom_map_numbers)
        if (
            len(set(retained_atoms)) != len(retained_atoms)
            or len(set(candidate.smarts_atom_ids)) != len(candidate.smarts_atom_ids)
            or set(candidate.smarts_atom_ids) != set(retained_atoms)
            or len(map_by_atom) != len(candidate.atom_map_numbers)
            or set(map_by_atom) != set(retained_atoms)
            or any(type(value) is not int or value <= 0 for value in map_by_atom.values())
            or len(set(map_by_atom.values())) != len(map_by_atom)
        ):
            raise ValueError("MACHINE_AUTHORITATIVE_PRE_ATOM_MAP_COVERAGE_INVALID")
        try:
            candidate_pre_bonds = tuple(sorted(
                _normalized_bond_v1(bond, map_by_atom)
                for bond in candidate.pre_reaction_bonds
            ))
        except ValueError as error:
            raise ValueError("MACHINE_AUTHORITATIVE_PRE_GRAPH_INVALID") from error
        if approved_pre_bonds != candidate_pre_bonds:
            raise ValueError("MACHINE_AUTHORITATIVE_PRE_GRAPH_REVIEW_MISMATCH")
        charges_by_atom = dict(candidate.atom_formal_charges)
        if (
            len(charges_by_atom) != len(candidate.atom_formal_charges)
            or set(charges_by_atom) != set(retained_atoms)
            or any(type(value) is not int for value in charges_by_atom.values())
        ):
            raise ValueError("MACHINE_AUTHORITATIVE_FORMAL_CHARGE_COVERAGE_INVALID")
        candidate_charges = tuple(sorted(
            (map_by_atom[atom_id], charges_by_atom[atom_id])
            for atom_id in retained_atoms
        ))
        if approved_charges != candidate_charges:
            raise ValueError("MACHINE_AUTHORITATIVE_FORMAL_CHARGE_REVIEW_MISMATCH")
        return {
            "canonical_ligand_smiles": candidate.canonical_ligand_smiles,
            "smarts_atom_ids": candidate.smarts_atom_ids,
            "explicit_graph_bonds": candidate.explicit_graph_bonds,
            "pre_reaction_bonds": candidate.pre_reaction_bonds,
            "atom_formal_charges": candidate.atom_formal_charges,
            "pre_reaction_graph_authoritative": True,
            "formal_charge_authoritative": True,
        }

    try:
        from rdkit import Chem
    except ImportError as error:
        raise ValueError("RDKIT_REVIEWED_PRE_GRAPH_VALIDATOR_UNAVAILABLE") from error
    atom_by_map = {map_number: atom_id for atom_id, map_number in candidate.atom_map_numbers}
    if (
        len(atom_by_map) != len(candidate.atom_map_numbers)
        or set(atom_by_map) != {item[0] for item in approved_charges}
        or any(left not in atom_by_map or right not in atom_by_map for left, right, _ in approved_pre_bonds)
    ):
        raise ValueError("REVIEWED_PRE_GRAPH_ATOM_MAP_COVERAGE_INVALID")
    charge_by_map = dict(approved_charges)
    symbol_by_atom = {row[0]: row[1] for row in candidate.ligand_atom_coordinates}
    if set(symbol_by_atom) != set(candidate.retained_heavy_atoms):
        raise ValueError("REVIEWED_PRE_GRAPH_LIGAND_SYMBOL_COVERAGE_INVALID")
    rw_molecule = Chem.RWMol()
    index_by_atom: dict[int | str, int] = {}
    aromatic_atoms = {
        atom_by_map[value]
        for left, right, order in approved_pre_bonds if order == "aromatic"
        for value in (left, right)
    }
    for atom_id in candidate.retained_heavy_atoms:
        map_number = dict(candidate.atom_map_numbers)[atom_id]
        atom = Chem.Atom(symbol_by_atom[atom_id])
        atom.SetFormalCharge(charge_by_map[map_number])
        atom.SetAtomMapNum(map_number)
        atom.SetIsAromatic(atom_id in aromatic_atoms)
        index_by_atom[atom_id] = rw_molecule.AddAtom(atom)
    bond_types = {
        "single": Chem.BondType.SINGLE,
        "double": Chem.BondType.DOUBLE,
        "triple": Chem.BondType.TRIPLE,
        "aromatic": Chem.BondType.AROMATIC,
    }
    projected_bonds = tuple(
        (atom_by_map[left], atom_by_map[right], order)
        for left, right, order in approved_pre_bonds
    )
    try:
        for left, right, order in projected_bonds:
            rw_molecule.AddBond(index_by_atom[left], index_by_atom[right], bond_types[order])
        molecule = rw_molecule.GetMol()
        Chem.SanitizeMol(molecule)
        smiles = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
        parsed = Chem.MolFromSmiles(smiles)
    except (RuntimeError, ValueError) as error:
        raise ValueError("REVIEWED_PRE_GRAPH_CHEMICAL_VALIDATION_FAILED") from error
    if parsed is None or parsed.GetNumAtoms() != len(candidate.retained_heavy_atoms):
        raise ValueError("REVIEWED_PRE_GRAPH_CANONICALIZATION_FAILED")
    atom_ids = tuple(atom_by_map[atom.GetAtomMapNum()] for atom in parsed.GetAtoms())
    return {
        "canonical_ligand_smiles": smiles,
        "smarts_atom_ids": atom_ids,
        "explicit_graph_bonds": projected_bonds,
        "pre_reaction_bonds": projected_bonds,
        "atom_formal_charges": tuple(
            (atom_by_map[map_number], charge) for map_number, charge in approved_charges
        ),
        "pre_reaction_graph_authoritative": True,
        "formal_charge_authoritative": True,
    }


def _smarts_atom_map_numbers_v1(smarts: object) -> tuple[int, ...]:
    if type(smarts) is not str or not smarts.strip():
        raise ValueError("APPROVED_WARHEAD_SMARTS_INVALID")
    try:
        from rdkit import Chem
    except ImportError as error:
        raise ValueError("RDKIT_SMARTS_MATCHER_UNAVAILABLE") from error
    query = Chem.MolFromSmarts(smarts)
    if query is None:
        raise ValueError("APPROVED_WARHEAD_SMARTS_INVALID")
    maps = tuple(atom.GetAtomMapNum() for atom in query.GetAtoms())
    if not maps or any(value <= 0 for value in maps) or len(set(maps)) != len(maps):
        raise ValueError("APPROVED_WARHEAD_SMARTS_MAP_NUMBERS_INVALID")
    return tuple(sorted(maps))


def _resolve_existing_authority_action_v1(
    *,
    kind: str,
    authority_id: str,
    authority_version: str,
    chemistry_signature_sha256: str,
    approved_smarts: str,
    authorities: Sequence[ReusableChemistryAuthorityV1],
) -> tuple[ReusableChemistryAuthorityV1 | None, tuple[str, ...]]:
    if kind not in {"REACTION_FAMILY", "WARHEAD_RULE"}:
        raise ValueError("BIND_EXISTING_KIND_INVALID")
    id_field = "reaction_family_id" if kind == "REACTION_FAMILY" else "warhead_rule_id"
    version_field = (
        "reaction_family_version" if kind == "REACTION_FAMILY"
        else "warhead_rule_version"
    )
    same_id = [item for item in authorities if getattr(item, id_field) == authority_id]
    if not same_id:
        return None, (f"{kind}_BIND_EXISTING_UNKNOWN_ID",)
    same_version = [
        item for item in same_id if getattr(item, version_field) == authority_version
    ]
    if not same_version:
        return None, (f"{kind}_BIND_EXISTING_WRONG_VERSION",)
    if any(item.approved is not True for item in same_version):
        return None, (f"{kind}_BIND_EXISTING_CANDIDATE_ONLY",)
    compatible = [
        item for item in same_version
        if not _authority_schema_reasons_v1(item)
        and item.approval_scope == "EXACT_CHEMISTRY_SIGNATURE_REUSABLE"
        and item.chemistry_signature_sha256 == chemistry_signature_sha256
        and (
            kind == "REACTION_FAMILY"
            or item.approved_warhead_smarts == approved_smarts
        )
    ]
    if not compatible:
        return None, (f"{kind}_BIND_EXISTING_SIGNATURE_OR_SMARTS_MISMATCH",)
    if len(compatible) != 1:
        return None, (f"{kind}_BIND_EXISTING_AMBIGUOUS",)
    return compatible[0], ()


def _approval_effective_candidate_and_authority_v1(
    candidate: ExpansionCandidateV1,
    record: Mapping[str, Any],
    existing_authorities: Sequence[ReusableChemistryAuthorityV1] = (),
) -> tuple[
    ExpansionCandidateV1 | None,
    ReusableChemistryAuthorityV1 | None,
    tuple[str, ...],
]:
    reasons: list[str] = []
    required = {
        "candidate_identity", "review_status", "review_scope",
        "independent_sample_assignment_decision",
        "reaction_family_authority_action", "reaction_family_id",
        "reaction_family_version", "warhead_rule_authority_action",
        "warhead_rule_id", "warhead_rule_version", "approved_warhead_smarts",
        "ligand_reactive_atom_map_number", "warhead_atom_map_numbers",
        "expected_pre_reaction_bond_orders", "allowed_formal_charge_pattern",
        "reviewed_warhead_atom_ids", "reviewed_warhead_attachment_atom_id",
        "reviewed_nonwarhead_boundary_atom_id",
        "reviewed_attachment_boundary_bond_order",
        "reviewed_scaffold_atom_ids", "reviewed_linker_atom_ids",
        "reviewed_warhead_role_atom_ids", "reviewed_minimal_seed_atom_ids",
        "reviewed_scaffold_linker_boundary_bond",
        "reviewed_linker_warhead_boundary_bond",
        "primary_anchor_atom", "direction_anchor_atom",
        "optional_plane_anchor_atom", "role_profile", "role_rule_id",
        "role_rule_version", "bound_source_identity", "bound_source_sha256",
        "pre_review_evidence_digest", "source_assignment_record_sha256",
        "reviewer_id", "review_rationale", "review_notes",
    }
    missing = sorted(required - set(record))
    if missing:
        return None, None, tuple(f"APPROVAL_FIELD_MISSING:{field}" for field in missing)
    if record["candidate_identity"] != candidate.candidate_identity:
        reasons.append("APPROVAL_CANDIDATE_IDENTITY_MISMATCH")
    if record["review_status"] != "APPROVE":
        reasons.append("APPROVAL_STATUS_NOT_APPROVE")
    if record["review_scope"] not in {
        "EXACT_CHEMISTRY_SIGNATURE_REUSABLE", "SAMPLE_BOUND_ONLY"
    }:
        reasons.append("APPROVAL_SCOPE_INVALID")
    if record["independent_sample_assignment_decision"] != "APPROVE":
        reasons.append("INDEPENDENT_SAMPLE_ASSIGNMENT_NOT_APPROVED")
    for field in ("reaction_family_authority_action", "warhead_rule_authority_action"):
        if record[field] not in {"BIND_EXISTING", "NEW_AUTHORITY_REQUIRED"}:
            reasons.append(f"{field.upper()}_INVALID")
    for field in (
        "reaction_family_id", "reaction_family_version", "warhead_rule_id",
        "warhead_rule_version", "role_rule_id", "role_rule_version",
    ):
        if not _is_id(record[field]):
            reasons.append(f"{field.upper()}_INVALID")
    reviewer = record["reviewer_id"]
    if (
        type(reviewer) is not str
        or not reviewer.strip()
        or reviewer.strip().lower() in _FORBIDDEN_REVIEWERS
    ):
        reasons.append("HUMAN_REVIEWER_ID_INVALID")
    if type(record["review_rationale"]) is not str or not record["review_rationale"].strip():
        reasons.append("HUMAN_REVIEW_RATIONALE_MISSING")
    if record["bound_source_identity"] != candidate.source_identity:
        reasons.append("APPROVAL_SOURCE_IDENTITY_MISMATCH")
    if record["bound_source_sha256"] != candidate.expected_source_sha256:
        reasons.append("APPROVAL_SOURCE_SHA256_MISMATCH")
    for field in (
        "bound_source_sha256", "pre_review_evidence_digest",
        "source_assignment_record_sha256",
    ):
        if not _is_sha(record[field]):
            reasons.append(f"{field.upper()}_INVALID")
    try:
        computed_pre_review_digest = build_pre_review_evidence_digest_v1(candidate)
    except ValueError as error:
        reasons.append(str(error))
        computed_pre_review_digest = ""
    if (
        candidate.pre_review_evidence_digest != computed_pre_review_digest
        or record["pre_review_evidence_digest"] != computed_pre_review_digest
    ):
        reasons.append("APPROVAL_PRE_REVIEW_EVIDENCE_BINDING_MISMATCH")
    if record["source_assignment_record_sha256"] != _candidate_assignment_sha256_v1(candidate):
        reasons.append("APPROVAL_ASSIGNMENT_BINDING_MISMATCH")
    computed_review_digest = approval_record_digest_v1(record)
    claimed_review_digest = record.get("source_human_review_record_sha256")
    if claimed_review_digest is not None and (
        not _is_sha(claimed_review_digest)
        or claimed_review_digest != computed_review_digest
    ):
        reasons.append("HUMAN_REVIEW_RECORD_DIGEST_MISMATCH")
    try:
        scaffold = _atom_tuple_v1(record["reviewed_scaffold_atom_ids"], "SCAFFOLD")
        linker = _atom_tuple_v1(
            record["reviewed_linker_atom_ids"], "LINKER",
            allow_empty=record["role_profile"] == DIRECT_PROFILE,
        )
        warhead = _atom_tuple_v1(record["reviewed_warhead_role_atom_ids"], "WARHEAD")
        chemistry_warhead = _atom_tuple_v1(
            record["reviewed_warhead_atom_ids"], "CHEMISTRY_WARHEAD"
        )
        seed = _atom_tuple_v1(record["reviewed_minimal_seed_atom_ids"], "MINIMAL_SEED")
    except ValueError as error:
        reasons.append(str(error))
        scaffold = linker = warhead = chemistry_warhead = seed = ()
    if set(chemistry_warhead) != set(warhead):
        reasons.append("CHEMISTRY_AND_ROLE_WARHEAD_ATOM_SET_MISMATCH")
    map_by_atom = dict(candidate.atom_map_numbers)
    if (
        len(map_by_atom) != len(candidate.atom_map_numbers)
        or set(map_by_atom) != set(candidate.retained_heavy_atoms)
        or any(type(value) is not int or value <= 0 for value in map_by_atom.values())
        or len(set(map_by_atom.values())) != len(map_by_atom)
    ):
        reasons.append("AUTHORITATIVE_ATOM_MAP_NUMBER_SET_INVALID")
    reactive_map = record["ligand_reactive_atom_map_number"]
    if (
        type(reactive_map) is not int
        or map_by_atom.get(candidate.reactive_ligand_atom_id) != reactive_map
    ):
        reasons.append("LIGAND_REACTIVE_ATOM_MAP_NUMBER_MISMATCH")
    try:
        approved_warhead_maps = tuple(sorted(_atom_tuple_v1(
            record["warhead_atom_map_numbers"], "WARHEAD_ATOM_MAP_NUMBERS"
        )))
    except ValueError as error:
        reasons.append(str(error))
        approved_warhead_maps = ()
    candidate_warhead_maps = tuple(sorted(
        map_by_atom[item] for item in warhead if item in map_by_atom
    ))
    if approved_warhead_maps != candidate_warhead_maps:
        reasons.append("WARHEAD_ATOM_MAP_NUMBERS_MISMATCH")
    try:
        smarts_maps = _smarts_atom_map_numbers_v1(record["approved_warhead_smarts"])
    except ValueError as error:
        reasons.append(str(error))
        smarts_maps = ()
    if smarts_maps != approved_warhead_maps:
        reasons.append("SMARTS_AND_WARHEAD_MAP_NUMBERS_MISMATCH")
    try:
        approved_pre_bonds = _approval_pre_bonds_v1(
            record["expected_pre_reaction_bond_orders"]
        )
    except ValueError as error:
        reasons.append(str(error))
        approved_pre_bonds = ()
    try:
        approved_charges = _approval_formal_charges_v1(
            record["allowed_formal_charge_pattern"]
        )
    except ValueError as error:
        reasons.append(str(error))
        approved_charges = ()
    if candidate.pre_reaction_graph_authoritative is True:
        try:
            expected_pre_bonds = tuple(sorted(
                _normalized_bond_v1(item, map_by_atom)
                for item in candidate.pre_reaction_bonds
            ))
        except ValueError as error:
            reasons.append(str(error))
            expected_pre_bonds = ()
        if approved_pre_bonds != expected_pre_bonds:
            reasons.append("EXPECTED_PRE_REACTION_BOND_ORDERS_MISMATCH")
    if candidate.formal_charge_authoritative is True:
        charge_by_atom = dict(candidate.atom_formal_charges)
        expected_charges = tuple(sorted(
            (map_by_atom[item], charge_by_atom[item])
            for item in candidate.retained_heavy_atoms
            if item in map_by_atom and item in charge_by_atom
        ))
        if (
            len(charge_by_atom) != len(candidate.atom_formal_charges)
            or set(charge_by_atom) != set(candidate.retained_heavy_atoms)
            or approved_charges != expected_charges
        ):
            reasons.append("ALLOWED_FORMAL_CHARGE_PATTERN_MISMATCH")
    try:
        reviewed_pre_fields = _reviewed_pre_graph_candidate_fields_v1(
            candidate, approved_pre_bonds, approved_charges,
        )
    except ValueError as error:
        reasons.append(str(error))
        reviewed_pre_fields = {}
    if record["reviewed_attachment_boundary_bond_order"] not in _BOND_ORDERS_V1:
        reasons.append("REVIEWED_ATTACHMENT_BOUNDARY_BOND_ORDER_INVALID")
    effective = replace(
        candidate,
        scaffold_atoms=scaffold,
        linker_atoms=linker,
        warhead_atoms=warhead,
        seed_atoms=seed,
        primary_anchor_atom=record["primary_anchor_atom"],
        direction_anchor_atom=record["direction_anchor_atom"],
        optional_plane_anchor_atom=record["optional_plane_anchor_atom"],
        role_profile=record["role_profile"],
        role_rule_id=record["role_rule_id"],
        role_rule_version=record["role_rule_version"],
        role_rule_match_count=1,
        role_authority_published=True,
        chemistry_signature_authoritative=False,
        **reviewed_pre_fields,
    )
    try:
        effective = with_computed_chemistry_signature_v1(effective, authoritative=True)
    except ValueError as error:
        reasons.append(str(error))
    expected_final_signature = record.get("expected_final_chemistry_signature_sha256")
    if expected_final_signature not in (None, "") and (
        not _is_sha(expected_final_signature)
        or expected_final_signature != effective.chemistry_signature_sha256
    ):
        reasons.append("APPROVAL_EXPECTED_FINAL_CHEMISTRY_SIGNATURE_MISMATCH")
    match_count, match_atoms, match_reason = _smarts_match_v1(
        effective, str(record["approved_warhead_smarts"])
    )
    family_bound = rule_bound = None
    if record["reaction_family_authority_action"] == "BIND_EXISTING":
        family_bound, binding_reasons = _resolve_existing_authority_action_v1(
            kind="REACTION_FAMILY",
            authority_id=str(record["reaction_family_id"]),
            authority_version=str(record["reaction_family_version"]),
            chemistry_signature_sha256=effective.chemistry_signature_sha256,
            approved_smarts=str(record["approved_warhead_smarts"]),
            authorities=existing_authorities,
        )
        reasons.extend(binding_reasons)
        family_available = family_bound is not None
    else:
        family_available = historical_review_policy.approved_reaction_family_available(
            decision="approve", reviewer_id=str(record["reviewer_id"]),
            review_rationale=str(record["review_rationale"]),
            canonical_identity_sha256=effective.chemistry_signature_sha256,
            source_identity_sha256=effective.chemistry_signature_sha256,
        )
    if record["warhead_rule_authority_action"] == "BIND_EXISTING":
        rule_bound, binding_reasons = _resolve_existing_authority_action_v1(
            kind="WARHEAD_RULE", authority_id=str(record["warhead_rule_id"]),
            authority_version=str(record["warhead_rule_version"]),
            chemistry_signature_sha256=effective.chemistry_signature_sha256,
            approved_smarts=str(record["approved_warhead_smarts"]),
            authorities=existing_authorities,
        )
        reasons.extend(binding_reasons)
        rule_available = rule_bound is not None and family_available
    else:
        rule_available = historical_review_policy.approved_warhead_rule_available(
            family_available=family_available, topology_decision="approve",
            approved_smarts=str(record["approved_warhead_smarts"]),
            smarts_review_status="approved", smarts_match_count=match_count,
            smarts_includes_reactive_atom=(
                effective.reactive_atom_mapping_count == 1
                and effective.reactive_ligand_atom_id in set(match_atoms)
            ),
            warhead_atom_count=len(match_atoms),
            attachment_boundary_count=len(
                _cross_role_boundaries_v1(effective)[2]
                if effective.role_profile == DIRECT_PROFILE
                else _cross_role_boundaries_v1(effective)[1]
            ), reviewer_id=str(record["reviewer_id"]),
            review_rationale=str(record["review_rationale"]),
            identities_unchanged=(
                record["bound_source_sha256"] == effective.expected_source_sha256
                and record["pre_review_evidence_digest"]
                == effective.pre_review_evidence_digest
            ),
        )
    if family_bound is not None and rule_bound is not None and family_bound != rule_bound:
        reasons.append("BIND_EXISTING_FAMILY_RULE_AUTHORITY_MISMATCH")
    gold = historical_review_policy.human_gold_review_completed(
        sample_decision="approve",
        family_available=family_available,
        rule_available=rule_available,
        assignment_record_sha256=_candidate_assignment_sha256_v1(effective),
        source_assignment_record_sha256=str(record["source_assignment_record_sha256"]),
        reviewer_id=str(record["reviewer_id"]),
        review_rationale=str(record["review_rationale"]),
    )
    if match_reason != "NONE":
        reasons.append(match_reason)
    if set(match_atoms) != set(effective.warhead_atoms):
        reasons.append("APPROVED_SMARTS_WARHEAD_ATOM_SET_MISMATCH")
    scaffold_linker, linker_warhead, direct_boundary = (
        _cross_role_boundaries_v1(effective)
    )
    for field, expected in (
        ("reviewed_scaffold_linker_boundary_bond", scaffold_linker),
        ("reviewed_linker_warhead_boundary_bond", linker_warhead),
    ):
        value = record[field]
        if (
            effective.role_profile == DIRECT_PROFILE
            and not expected
            and type(value) in (list, tuple)
            and len(value) == 0
        ):
            continue
        if (
            type(value) not in (list, tuple)
            or len(value) != 2
            or len(expected) != 1
            or frozenset(value) != frozenset(expected[0][:2])
        ):
            reasons.append(f"{field.upper()}_MISMATCH")
    attachment_boundaries = (
        direct_boundary if effective.role_profile == DIRECT_PROFILE
        else linker_warhead
    )
    if (
        len(attachment_boundaries) != 1
        or frozenset((
            record["reviewed_warhead_attachment_atom_id"],
            record["reviewed_nonwarhead_boundary_atom_id"],
        )) != frozenset(attachment_boundaries[0][:2])
        or record["reviewed_attachment_boundary_bond_order"]
        != attachment_boundaries[0][2]
    ):
        reasons.append("REVIEWED_WARHEAD_ATTACHMENT_BOUNDARY_MISMATCH")
    if not family_available:
        reasons.append("HUMAN_REACTION_FAMILY_APPROVAL_INVALID")
    if not rule_available:
        reasons.append("HUMAN_WARHEAD_RULE_APPROVAL_INVALID")
    if not gold:
        reasons.append("HUMAN_GOLD_SAMPLE_APPROVAL_INVALID")
    reasons.extend(_validate_role_seed_profile_v1(effective))
    bound_authority = family_bound if family_bound is not None else rule_bound
    authority = ReusableChemistryAuthorityV1(
        authority_id=(bound_authority.authority_id if bound_authority is not None else
            "COVAPIE_REUSABLE_CHEMISTRY_" + effective.chemistry_signature_sha256[:16].upper()),
        authority_version="V1",
        approval_scope=str(record["review_scope"]),
        approved=True,
        cross_signature_propagation_allowed=False,
        chemistry_signature_sha256=effective.chemistry_signature_sha256,
        reaction_family_id=str(record["reaction_family_id"]),
        reaction_family_version=str(record["reaction_family_version"]),
        warhead_rule_id=str(record["warhead_rule_id"]),
        warhead_rule_version=str(record["warhead_rule_version"]),
        approved_warhead_smarts=str(record["approved_warhead_smarts"]),
        role_rule_id=str(record["role_rule_id"]),
        role_rule_version=str(record["role_rule_version"]),
        role_profile=str(record["role_profile"]),
        source_human_review_record_sha256=computed_review_digest,
        pre_review_evidence_digest=str(record["pre_review_evidence_digest"]),
        source_identity=str(record["bound_source_identity"]),
        source_sha256=str(record["bound_source_sha256"]),
        reviewer_id=str(record["reviewer_id"]),
        review_rationale=str(record["review_rationale"]),
        ligand_reactive_atom_map_number=int(reactive_map) if type(reactive_map) is int else 0,
        warhead_atom_map_numbers=approved_warhead_maps,
        expected_pre_reaction_bond_orders=approved_pre_bonds,
        allowed_formal_charge_pattern=approved_charges,
        attachment_boundary_bond_order=str(record["reviewed_attachment_boundary_bond_order"]),
        source_human_review_record_canonical_json=(
            _approval_record_canonical_text_v1(record)
        ),
    )
    if (
        family_bound is not None and rule_bound is not None
        and family_bound == rule_bound
        and record["reaction_family_authority_action"] == "BIND_EXISTING"
        and record["warhead_rule_authority_action"] == "BIND_EXISTING"
    ):
        authority = family_bound
    if record["review_scope"] == "EXACT_CHEMISTRY_SIGNATURE_REUSABLE":
        reasons.extend(_authority_schema_reasons_v1(authority))
    return effective, authority, tuple(dict.fromkeys(reasons))


def ingest_completed_human_approval_v1(
    candidate: ExpansionCandidateV1,
    record: Mapping[str, Any],
    *,
    existing_authorities: Sequence[ReusableChemistryAuthorityV1] = (),
) -> tuple[ExpansionCandidateV1, ReusableChemistryAuthorityV1 | None]:
    """Validate one completed decision and return its effective authority.

    ``None`` authority means a valid sample-bound approval.  An exact-signature
    reusable approval returns a registry-ready in-memory authority record.
    """

    effective, authority, reasons = _approval_effective_candidate_and_authority_v1(
        candidate, record, existing_authorities
    )
    if reasons or effective is None or authority is None:
        raise ValueError("INVALID_COMPLETED_HUMAN_APPROVAL:" + ";".join(reasons))
    return effective, (
        authority
        if authority.approval_scope == "EXACT_CHEMISTRY_SIGNATURE_REUSABLE"
        else None
    )


def _candidate_authority_qa_reasons_v1(
    candidate: ExpansionCandidateV1,
    authority: ReusableChemistryAuthorityV1,
    *,
    allow_sample_bound_human_approval: bool = False,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not allow_sample_bound_human_approval:
        reasons.extend(_authority_schema_reasons_v1(authority))
    if candidate.chemistry_signature_authoritative is not True:
        reasons.append("CHEMISTRY_SIGNATURE_NOT_AUTHORITATIVE")
    try:
        recomputed_signature = build_exact_chemistry_signature_v1(candidate)
    except ValueError as error:
        reasons.append(str(error))
        recomputed_signature = ""
    if recomputed_signature != candidate.chemistry_signature_sha256:
        reasons.append("CANDIDATE_CHEMISTRY_SIGNATURE_RECOMPUTATION_MISMATCH")
    if candidate.chemistry_signature_sha256 != authority.chemistry_signature_sha256:
        reasons.append("CHEMISTRY_SIGNATURE_EXACT_MATCH_REQUIRED")
    if authority.cross_signature_propagation_allowed is not False:
        reasons.append("CROSS_SIGNATURE_PROPAGATION_FORBIDDEN")
    if candidate.reactive_atom_mapping_count != 1:
        reasons.append("REACTIVE_ATOM_MAPPING_NOT_EXACT_ONE")
    match_count, match_atoms, match_reason = _smarts_match_v1(
        candidate, authority.approved_warhead_smarts
    )
    if match_reason != "NONE":
        reasons.append(match_reason)
    if match_count != 1:
        reasons.append("APPROVED_SMARTS_MATCH_NOT_EXACT_ONE")
    if candidate.reactive_ligand_atom_id not in set(match_atoms):
        reasons.append("APPROVED_SMARTS_EXCLUDES_REACTIVE_ATOM")
    if set(match_atoms) != set(candidate.warhead_atoms):
        reasons.append("APPROVED_SMARTS_WARHEAD_ATOM_SET_MISMATCH")
    map_by_atom = dict(candidate.atom_map_numbers)
    if map_by_atom.get(candidate.reactive_ligand_atom_id) != authority.ligand_reactive_atom_map_number:
        reasons.append("AUTHORITY_REACTIVE_ATOM_MAP_NUMBER_MISMATCH")
    if tuple(sorted(map_by_atom.get(item, -1) for item in candidate.warhead_atoms)) != tuple(
        sorted(authority.warhead_atom_map_numbers)
    ):
        reasons.append("AUTHORITY_WARHEAD_ATOM_MAP_NUMBERS_MISMATCH")
    try:
        pre_bonds = tuple(sorted(
            _normalized_bond_v1(item, map_by_atom) for item in candidate.pre_reaction_bonds
        ))
    except ValueError as error:
        reasons.append(str(error))
        pre_bonds = ()
    if pre_bonds != tuple(sorted(authority.expected_pre_reaction_bond_orders)):
        reasons.append("AUTHORITY_PRE_REACTION_BOND_ORDERS_MISMATCH")
    charge_by_atom = dict(candidate.atom_formal_charges)
    charges = tuple(sorted(
        (map_by_atom[item], charge_by_atom[item])
        for item in candidate.retained_heavy_atoms
        if item in map_by_atom and item in charge_by_atom
    ))
    if charges != tuple(sorted(authority.allowed_formal_charge_pattern)):
        reasons.append("AUTHORITY_FORMAL_CHARGE_PATTERN_MISMATCH")
    if (
        candidate.role_authority_published is not True
        or candidate.role_rule_match_count != 1
        or candidate.role_rule_id != authority.role_rule_id
        or candidate.role_rule_version != authority.role_rule_version
    ):
        reasons.append("PUBLISHED_DETERMINISTIC_ROLE_RULE_EXACT_MATCH_REQUIRED")
    if candidate.role_profile != authority.role_profile:
        reasons.append("ROLE_PROFILE_AUTHORITY_MISMATCH")
    reasons.extend(_validate_role_seed_profile_v1(candidate))
    if candidate.duplicate_identity:
        reasons.append("DUPLICATE_IDENTITY")
    if candidate.baseline_leakage_evidence_complete is not True:
        reasons.append("BASELINE_LEAKAGE_EVIDENCE_INCOMPLETE")
    if not candidate.leakage_key.strip():
        reasons.append("LEAKAGE_KEY_MISSING")
    if candidate.leakage_conflict:
        reasons.append("LEAKAGE_INVARIANT_VIOLATION")
    return tuple(dict.fromkeys(reasons))


def load_published_leakage_group_population_v1(
    repo_root: Path,
) -> tuple[LeakageGroupAssignmentV1, ...]:
    path = repo_root / PUBLISHED_GROUP_SPLIT_RELATIVE
    payload = path.read_bytes()
    if _sha256(payload) != PUBLISHED_GROUP_SPLIT_SHA256:
        raise ValueError("PUBLISHED_GROUP_SPLIT_ASSIGNMENT_SHA256_MISMATCH")
    rows = _csv_rows(path)
    result: list[LeakageGroupAssignmentV1] = []
    for row in rows:
        if (
            row.get("split_policy") != split_owner.POLICY
            or row.get("assigned_split") not in split_owner.SPLITS
            or row.get("group_split_assignment_passed") != "True"
        ):
            raise ValueError("PUBLISHED_GROUP_SPLIT_ASSIGNMENT_SEMANTICS_INVALID")
        result.append(LeakageGroupAssignmentV1(
            leakage_key=row["final_leakage_group_id"],
            final_leakage_group_id=row["final_leakage_group_id"],
            member_count=int(row["member_count"]),
            assigned_split=row["assigned_split"],
            frozen=True,
        ))
    if len(result) != 5 or len({item.final_leakage_group_id for item in result}) != 5:
        raise ValueError("PUBLISHED_GROUP_SPLIT_ASSIGNMENT_POPULATION_INVALID")
    return tuple(result)


def assign_expansion_leakage_splits_v1(
    candidates: Sequence[ExpansionCandidateV1],
    *,
    existing_groups: Sequence[LeakageGroupAssignmentV1],
) -> Mapping[str, tuple[str, str]]:
    """Freeze published groups and optimize only new groups over full population."""

    existing = {item.leakage_key: item for item in existing_groups}
    if len(existing) != len(existing_groups):
        raise ValueError("LEAKAGE_GROUP_REGISTRY_DUPLICATE_KEY")
    group_id_to_key: dict[str, str] = {}
    prior_member_to_key: dict[str, str] = {}
    for item in existing_groups:
        if (
            type(item) is not LeakageGroupAssignmentV1
            or item.frozen is not True
            or item.assigned_split not in split_owner.SPLITS
            or item.member_count <= 0
            or not item.leakage_key.strip()
            or not item.final_leakage_group_id.strip()
        ):
            raise ValueError("LEAKAGE_GROUP_REGISTRY_INVALID")
        prior_key = group_id_to_key.get(item.final_leakage_group_id)
        if prior_key is not None and prior_key != item.leakage_key:
            raise ValueError("LEAKAGE_GROUP_REGISTRY_GROUP_ID_KEY_CONFLICT")
        group_id_to_key[item.final_leakage_group_id] = item.leakage_key
        if item.member_identities:
            if (
                tuple(sorted(item.member_identities)) != item.member_identities
                or len(set(item.member_identities)) != len(item.member_identities)
                or item.member_count != len(item.member_identities)
                or any(
                    _SAMPLE_IDENTITY.fullmatch(identity) is None
                    for identity in item.member_identities
                )
            ):
                raise ValueError("LEAKAGE_GROUP_REGISTRY_MEMBER_IDENTITIES_INVALID")
            for identity in item.member_identities:
                prior_member_key = prior_member_to_key.get(identity)
                if (
                    prior_member_key is not None
                    and prior_member_key != item.leakage_key
                ):
                    raise ValueError("LEAKAGE_GROUP_REGISTRY_MEMBER_GROUP_CONFLICT")
                prior_member_to_key[identity] = item.leakage_key
    members_by_key: dict[str, set[str]] = {}
    candidate_key_by_identity: dict[str, str] = {}
    for candidate in candidates:
        if not candidate.leakage_key.strip():
            raise ValueError("LEAKAGE_KEY_MISSING")
        prior_candidate_key = candidate_key_by_identity.get(
            candidate.candidate_identity
        )
        if (
            prior_candidate_key is not None
            and prior_candidate_key != candidate.leakage_key
        ):
            raise ValueError("CANDIDATE_IDENTITY_LEAKAGE_KEY_CONFLICT")
        registered_key = prior_member_to_key.get(candidate.candidate_identity)
        if registered_key is not None and registered_key != candidate.leakage_key:
            raise ValueError("REGISTERED_IDENTITY_LEAKAGE_KEY_CONFLICT")
        candidate_key_by_identity[candidate.candidate_identity] = (
            candidate.leakage_key
        )
        members_by_key.setdefault(candidate.leakage_key, set()).add(
            candidate.candidate_identity
        )
    groups: list[dict[str, Any]] = []
    new_keys: list[str] = []
    for item in existing_groups:
        new_members = members_by_key.get(item.leakage_key, set()) - set(
            item.member_identities
        )
        groups.append({
            "key": item.leakage_key,
            "id": item.final_leakage_group_id,
            "member_count": item.member_count + len(new_members),
            "fixed_rank": split_owner.RANK[item.assigned_split],
        })
    for key in sorted(set(members_by_key) - set(existing)):
        group_id = "COVAPIE_EXPANSION_LEAKAGE_GROUP_" + _sha256(
            _canonical_json({
                "policy": "conservative_union_final_leakage_group_v1",
                "leakage_key": key,
            })
        )[:16].upper()
        groups.append({
            "key": key, "id": group_id,
            "member_count": len(members_by_key[key]), "fixed_rank": None,
        })
        new_keys.append(key)
    groups.sort(key=lambda item: item["id"])
    new_keys = sorted(new_keys, key=lambda key: next(
        item["id"] for item in groups if item["key"] == key
    ))
    if len(new_keys) > 10:
        raise ValueError("SPLIT_SUCCESSOR_EXHAUSTIVE_NEW_GROUP_LIMIT_EXCEEDED")
    target = split_owner.TARGET
    total_samples = sum(item["member_count"] for item in groups)
    group_count = len(groups)
    best: tuple[tuple[Any, ...], Mapping[str, int]] | None = None
    for ranks in product(range(3), repeat=len(new_keys)):
        new_rank = dict(zip(new_keys, ranks))
        full_signature = tuple(
            item["fixed_rank"] if item["fixed_rank"] is not None
            else new_rank[item["key"]]
            for item in groups
        )
        sample_counts = tuple(sum(
            item["member_count"] for item, rank in zip(groups, full_signature)
            if rank == split_rank
        ) for split_rank in range(3))
        group_counts = tuple(full_signature.count(rank) for rank in range(3))
        if min(group_counts) < 1 or sample_counts[0] < sample_counts[1] or sample_counts[0] < sample_counts[2]:
            continue
        objective = (
            sum(abs(Fraction(sample_counts[index]) - target[split_owner.SPLITS[index]] * total_samples) for index in range(3)),
            max(abs(Fraction(sample_counts[index]) - target[split_owner.SPLITS[index]] * total_samples) for index in range(3)),
            sum(abs(Fraction(group_counts[index]) - target[split_owner.SPLITS[index]] * group_count) for index in range(3)),
            full_signature,
        )
        if best is None or objective < best[0]:
            best = (objective, new_rank)
    if best is None:
        raise ValueError("SPLIT_SUCCESSOR_NO_VALID_FROZEN_ASSIGNMENT")
    selected = best[1]
    assignment: dict[str, tuple[str, str]] = {}
    for item in groups:
        rank = item["fixed_rank"] if item["fixed_rank"] is not None else selected[item["key"]]
        assignment[item["key"]] = (item["id"], split_owner.SPLITS[rank])
    return assignment


def validate_post_geometry_authority_v1(
    candidate: ExpansionCandidateV1,
) -> tuple[bool, tuple[str, ...], float | None]:
    reasons: list[str] = []
    if candidate.explicit_event_authoritative is not True:
        reasons.append("POST_EXPLICIT_EVENT_AUTHORITY_MISSING")
    if candidate.protein_endpoint_exact_cys_sg is not True:
        reasons.append("POST_PROTEIN_ENDPOINT_NOT_EXACT_CYS_SG")
    if candidate.ligand_endpoint_mapping_count != 1 or candidate.retained_endpoint_mapping_count != 1:
        reasons.append("POST_ENDPOINT_MAPPING_NOT_UNIQUE_RETAINED")
    if (
        candidate.protein_endpoint_atom_id is None
        or candidate.source_event_protein_atom_id != candidate.protein_endpoint_atom_id
        or candidate.source_event_ligand_atom_id != candidate.reactive_ligand_atom_id
        or candidate.retained_reactive_atom_id != candidate.reactive_ligand_atom_id
    ):
        reasons.append("POST_POSITIVE_REACTIVE_PAIR_IDENTITY_MISMATCH")
    ligand_rows = [
        row for row in candidate.ligand_atom_coordinates
        if row[0] == candidate.reactive_ligand_atom_id
    ]
    protein_rows = [
        row for row in candidate.pocket_atom_coordinates
        if row[0] == candidate.protein_endpoint_atom_id
    ]
    if len(ligand_rows) != 1 or len(protein_rows) != 1:
        reasons.append("POST_ENDPOINT_COORDINATE_ROW_NOT_EXACT_ONE")
        return False, tuple(dict.fromkeys(reasons)), None
    if str(protein_rows[0][1]) != "S":
        reasons.append("POST_PROTEIN_ENDPOINT_ELEMENT_NOT_SULFUR")
    coordinates = (*ligand_rows[0][2:], *protein_rows[0][2:])
    if any(type(value) not in (int, float) or type(value) is bool or not math.isfinite(float(value)) for value in coordinates):
        reasons.append("POST_ENDPOINT_COORDINATES_NOT_FINITE")
        return False, tuple(dict.fromkeys(reasons)), None
    recomputed = math.dist(
        tuple(float(value) for value in ligand_rows[0][2:]),
        tuple(float(value) for value in protein_rows[0][2:]),
    )
    try:
        from covalent_ext import (
            covapie_exact16_post_geometry_partial_supervision_authority_v1 as post_owner,
        )
        tolerance = post_owner.OBSERVED_DISTANCE_AGREEMENT_TOLERANCE_ANGSTROM_V1
    except ImportError:
        tolerance = 0.0015
    if (
        type(candidate.post_distance_angstrom) is not float
        or not math.isfinite(candidate.post_distance_angstrom)
        or abs(recomputed - candidate.post_distance_angstrom) > tolerance
    ):
        reasons.append("POST_RECORDED_DISTANCE_RECOMPUTATION_MISMATCH")
    return not reasons, tuple(dict.fromkeys(reasons)), recomputed


def _empty_phase_statuses_v1() -> dict[str, str]:
    return {phase: "NOT_REACHED" for phase in PHASES}


def _outcome_v1(
    candidate: ExpansionCandidateV1,
    *,
    disposition: str,
    reasons: Sequence[str],
    phases: Mapping[str, str],
    source_verified: bool,
    mechanically_eligible: bool = False,
    admitted_by: str = "NONE",
    authority_id: str = "NONE",
    human_decision: bool = False,
    group_id: str = "NONE",
    split: str = "NONE",
    post_geometry_authority: bool = False,
    materialization_ready: bool = False,
    materialization_performed: bool = False,
    tensorization_performed: bool = False,
    materialization_artifact_sha256: str = "NONE",
    tensorization_artifact_sha256: str = "NONE",
) -> CandidateOutcomeV1:
    return CandidateOutcomeV1(
        candidate_identity=candidate.candidate_identity,
        terminal_disposition=disposition,
        blocking_reasons=tuple(dict.fromkeys(str(reason) for reason in reasons)),
        phase_statuses=tuple((phase, phases[phase]) for phase in PHASES),
        source_verified=source_verified,
        mechanically_eligible=mechanically_eligible,
        admitted_by=admitted_by,
        chemistry_authority_id=authority_id,
        human_sample_decision_consumed=human_decision,
        role_profile=candidate.role_profile or "NONE",
        leakage_group_id=group_id,
        assigned_split=split,
        post_geometry_authority=post_geometry_authority,
        pre_geometry_authority=False,
        pre_geometry_masked=post_geometry_authority,
        materialization_ready=materialization_ready,
        tensorization_ready=materialization_ready,
        tensorization_owner=(
            "covapie_cys_sg_dataset_expansion_pipeline_v1."
            "tensorize_approved_expansion_sample_v1"
            if materialization_ready else "NONE"
        ),
        materialization_performed=materialization_performed,
        tensorization_performed=tensorization_performed,
        materialization_artifact_sha256=materialization_artifact_sha256,
        tensorization_artifact_sha256=tensorization_artifact_sha256,
    )


def _evaluate_candidate_v1(
    candidate: ExpansionCandidateV1,
    authorities: Sequence[ReusableChemistryAuthorityV1],
    approval_validation: tuple[
        ExpansionCandidateV1 | None,
        ReusableChemistryAuthorityV1 | None,
        tuple[str, ...],
    ] | None,
    split_assignments: Mapping[str, tuple[str, str]],
) -> tuple[CandidateOutcomeV1, Mapping[str, Any] | None]:
    phases = _empty_phase_statuses_v1()
    phases[PHASES[0]] = "CANDIDATE_LOADED"
    source_status = verify_existing_source_v1(
        candidate.source_path, candidate.expected_source_sha256
    )
    phases[PHASES[1]] = source_status
    if source_status == MISSING_SOURCE:
        return _outcome_v1(
            candidate, disposition=MISSING_SOURCE,
            reasons=("SOURCE_FILE_MISSING",), phases=phases,
            source_verified=False,
        ), None
    if source_status == SOURCE_SHA_MISMATCH:
        return _outcome_v1(
            candidate, disposition=SOURCE_SHA_MISMATCH,
            reasons=("IMMUTABLE_SOURCE_SHA256_MISMATCH",), phases=phases,
            source_verified=False,
        ), None

    if candidate.prior_disposition == "REJECT":
        phases[PHASES[2]] = "PUBLISHED_REJECT_PRESERVED"
        return _outcome_v1(
            candidate, disposition=REJECTED,
            reasons=candidate.prior_blocking_reasons or ("PUBLISHED_REJECT",),
            phases=phases, source_verified=True,
        ), None
    if candidate.prior_disposition == "MISSING_SOURCE_AUTHORITY":
        phases[PHASES[2]] = "STRUCTURAL_SOURCE_AUTHORITY_INCOMPLETE"
        return _outcome_v1(
            candidate, disposition=MISSING_SOURCE,
            reasons=candidate.prior_blocking_reasons,
            phases=phases, source_verified=True,
        ), None
    if candidate.prior_disposition == "NEEDS_RUNTIME_PROFILE_EXTENSION":
        phases[PHASES[2]] = "EXACT_EVENT_RECOVERED"
        phases[PHASES[3]] = "CANONICAL_MODEL_ELIGIBLE"
        phases[PHASES[6]] = "UNSUPPORTED_EMBEDDED_MULTI_BOUNDARY_PROFILE"
        return _outcome_v1(
            candidate, disposition=RUNTIME_EXTENSION,
            reasons=candidate.prior_blocking_reasons,
            phases=phases, source_verified=True, mechanically_eligible=True,
        ), None

    mechanical_reasons = _mechanical_eligibility_reasons_v1(candidate)
    phases[PHASES[2]] = (
        "EXACT_EVENT_AND_ENDPOINTS_VALID"
        if not any("EVENT" in reason or "ENDPOINT" in reason for reason in mechanical_reasons)
        else "STRUCTURAL_RECOVERY_FAILED_CLOSED"
    )
    phases[PHASES[3]] = (
        "CANONICAL_MODEL_ELIGIBLE" if not mechanical_reasons
        else "CANONICAL_MODEL_INELIGIBLE"
    )
    if mechanical_reasons:
        disposition = (
            REJECTED if any(
                reason in {
                    "UNSUPPORTED_NONHYDROGEN_MODEL_ATOM",
                    "UNKNOWN_OR_OTHER_FEATURE_CHANNEL_PRESENT",
                    "ZERO_VECTOR_FEATURE_FALLBACK_FORBIDDEN",
                }
                for reason in mechanical_reasons
            ) else HUMAN_REQUIRED
        )
        return _outcome_v1(
            candidate, disposition=disposition, reasons=mechanical_reasons,
            phases=phases, source_verified=True,
        ), None

    valid_authorities = [
        authority for authority in authorities
        if not _authority_schema_reasons_v1(authority)
        and authority.chemistry_signature_sha256
        == candidate.chemistry_signature_sha256
    ]
    authority: ReusableChemistryAuthorityV1 | None = None
    effective = candidate
    admitted_by = "NONE"
    human_decision = False
    binding: Mapping[str, Any] | None = None
    if approval_validation is not None:
        effective, authority, approval_reasons = approval_validation
        phases[PHASES[4]] = "COMPLETED_HUMAN_APPROVAL_INGESTION"
        if approval_reasons or effective is None or authority is None:
            phases[PHASES[5]] = "MALFORMED_OR_INCOMPLETE_APPROVAL_FAILED_CLOSED"
            return _outcome_v1(
                candidate, disposition=HUMAN_REQUIRED,
                reasons=approval_reasons or ("APPROVAL_INGESTION_INVALID",),
                phases=phases, source_verified=True, mechanically_eligible=True,
            ), None
        admitted_by = "VALID_COMPLETED_HUMAN_APPROVAL"
        human_decision = True
        phases[PHASES[5]] = "HUMAN_APPROVAL_VALIDATED"
        if authority.approval_scope == "EXACT_CHEMISTRY_SIGNATURE_REUSABLE":
            binding = _authority_mapping_v1(authority)
    elif len(valid_authorities) == 1 and candidate.chemistry_signature_authoritative:
        authority = valid_authorities[0]
        admitted_by = SUCCESSOR_POLICY_ID
        phases[PHASES[4]] = "APPROVED_REUSABLE_SIGNATURE_EXACT_MATCH"
        phases[PHASES[5]] = "DETERMINISTIC_MACHINE_SAMPLE_QA"
    elif len(valid_authorities) > 1:
        phases[PHASES[4]] = "APPROVED_REUSABLE_SIGNATURE_MATCH_AMBIGUOUS"
        phases[PHASES[5]] = HUMAN_REQUIRED
        return _outcome_v1(
            candidate, disposition=HUMAN_REQUIRED,
            reasons=("MULTIPLE_APPROVED_REUSABLE_AUTHORITIES_MATCH",),
            phases=phases, source_verified=True, mechanically_eligible=True,
        ), None
    else:
        phases[PHASES[4]] = "NO_APPROVED_REUSABLE_SIGNATURE_EXACT_MATCH"
        phases[PHASES[5]] = HUMAN_REQUIRED
        reasons = ["NEW_CHEMISTRY_SIGNATURE_OR_APPROVED_REUSABLE_SIGNATURE_NO_MATCH"]
        reasons.extend(candidate.prior_blocking_reasons)
        return _outcome_v1(
            candidate, disposition=HUMAN_REQUIRED, reasons=reasons,
            phases=phases, source_verified=True, mechanically_eligible=True,
        ), None

    assert authority is not None
    qa_reasons = _candidate_authority_qa_reasons_v1(
        effective,
        authority,
        allow_sample_bound_human_approval=(
            human_decision and authority.approval_scope == "SAMPLE_BOUND_ONLY"
        ),
    )
    if "UNSUPPORTED_PROFILE" in qa_reasons or "AUTHORITY_PROFILE_UNSUPPORTED" in qa_reasons:
        phases[PHASES[6]] = "UNSUPPORTED_PROFILE"
        return _outcome_v1(
            effective, disposition=RUNTIME_EXTENSION, reasons=qa_reasons,
            phases=phases, source_verified=True, mechanically_eligible=True,
            admitted_by=admitted_by, authority_id=authority.authority_id,
            human_decision=human_decision,
        ), binding
    if "LEAKAGE_INVARIANT_VIOLATION" in qa_reasons:
        phases[PHASES[7]] = "LEAKAGE_INVARIANT_VIOLATION"
        return _outcome_v1(
            effective, disposition=LEAKAGE_CONFLICT, reasons=qa_reasons,
            phases=phases, source_verified=True, mechanically_eligible=True,
            admitted_by=admitted_by, authority_id=authority.authority_id,
            human_decision=human_decision,
        ), binding
    if qa_reasons:
        phases[PHASES[6]] = "ROLE_SEED_RULE_OR_PROFILE_QA_FAILED_CLOSED"
        return _outcome_v1(
            effective, disposition=HUMAN_REQUIRED, reasons=qa_reasons,
            phases=phases, source_verified=True, mechanically_eligible=True,
            admitted_by=admitted_by, authority_id=authority.authority_id,
            human_decision=human_decision,
        ), binding

    phases[PHASES[6]] = "EXACT_EXISTING_PROFILE_VALIDATED"
    if effective.leakage_key not in split_assignments:
        phases[PHASES[7]] = "SPLIT_SUCCESSOR_ASSIGNMENT_MISSING"
        return _outcome_v1(
            effective, disposition=LEAKAGE_CONFLICT,
            reasons=("SPLIT_SUCCESSOR_ASSIGNMENT_MISSING",), phases=phases,
            source_verified=True, mechanically_eligible=True,
            admitted_by=admitted_by, authority_id=authority.authority_id,
            human_decision=human_decision,
        ), binding
    group_id, split = split_assignments[effective.leakage_key]
    phases[PHASES[7]] = "PUBLISHED_COMPATIBLE_FROZEN_SPLIT_SUCCESSOR_ASSIGNED"
    post_valid, post_reasons, _recomputed = validate_post_geometry_authority_v1(
        effective
    )
    if not post_valid:
        phases[PHASES[8]] = "POST_SOURCE_AUTHORITY_FAILED_CLOSED"
        return _outcome_v1(
            effective, disposition=POST_AUTHORITY_INVALID, reasons=post_reasons,
            phases=phases, source_verified=True, mechanically_eligible=True,
            admitted_by=admitted_by, authority_id=authority.authority_id,
            human_decision=human_decision, group_id=group_id, split=split,
        ), binding
    phases[PHASES[8]] = "POST_SOURCE_DERIVED_RECOMPUTED_PRE_MISSING_MASKED"
    phases[PHASES[9]] = "MATERIALIZATION_READY_TENSORIZER_OWNER_BOUND"
    disposition = HUMAN_APPROVED if human_decision else AUTO_ADMITTED
    return _outcome_v1(
        effective, disposition=disposition, reasons=(), phases=phases,
        source_verified=True, mechanically_eligible=True,
        admitted_by=admitted_by, authority_id=authority.authority_id,
        human_decision=human_decision, group_id=group_id, split=split,
        post_geometry_authority=True, materialization_ready=True,
    ), binding


def _canonical_smiles_and_atom_ids_from_graph_v1(
    atoms: Sequence[tuple[int | str, str]],
    bonds: Sequence[tuple[int | str, int | str, str]],
) -> tuple[str, tuple[int | str, ...]]:
    try:
        from rdkit import Chem
    except ImportError:
        return "", ()
    if not atoms or len({atom_id for atom_id, _ in atoms}) != len(atoms):
        return "", ()
    index_by_id: dict[int | str, int] = {}
    molecule = Chem.RWMol()
    aromatic_ids: set[int | str] = set()
    for left, right, order in bonds:
        if order == "aromatic":
            aromatic_ids.update((left, right))
    for ordinal, (atom_id, element) in enumerate(atoms, 1):
        atom = Chem.Atom(element)
        atom.SetAtomMapNum(ordinal)
        if atom_id in aromatic_ids:
            atom.SetIsAromatic(True)
        index_by_id[atom_id] = molecule.AddAtom(atom)
    bond_types = {
        "single": Chem.BondType.SINGLE,
        "double": Chem.BondType.DOUBLE,
        "triple": Chem.BondType.TRIPLE,
        "aromatic": Chem.BondType.AROMATIC,
    }
    try:
        for left, right, order in bonds:
            molecule.AddBond(index_by_id[left], index_by_id[right], bond_types[order])
        frozen = molecule.GetMol()
        Chem.SanitizeMol(frozen)
        smiles = Chem.MolToSmiles(frozen, canonical=True)
        parsed = Chem.MolFromSmiles(smiles)
    except (KeyError, RuntimeError, ValueError):
        return "", ()
    if parsed is None:
        return "", ()
    original_ids = tuple(atom_id for atom_id, _ in atoms)
    mapped: list[int | str] = []
    for atom in parsed.GetAtoms():
        map_number = atom.GetAtomMapNum()
        if map_number < 1 or map_number > len(original_ids):
            return "", ()
        mapped.append(original_ids[map_number - 1])
    return smiles, tuple(mapped)


def _canonical_smiles_and_atom_ids_from_pre_sdf_v1(
    path: Path, expected_atom_ids: tuple[int | str, ...],
) -> tuple[str, tuple[int | str, ...]]:
    try:
        from rdkit import Chem
    except ImportError as error:
        raise ValueError("RDKIT_PRE_SDF_CANONICALIZER_UNAVAILABLE") from error
    molecule = Chem.MolFromMolFile(str(path), removeHs=True)
    if molecule is None or molecule.GetNumAtoms() != len(expected_atom_ids):
        raise ValueError("APPROVED_PRE_SDF_ATOM_INVENTORY_MISMATCH")
    for index, atom in enumerate(molecule.GetAtoms(), 1):
        atom.SetAtomMapNum(index)
    smiles = Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
    parsed = Chem.MolFromSmiles(smiles)
    if parsed is None or parsed.GetNumAtoms() != len(expected_atom_ids):
        raise ValueError("APPROVED_PRE_SDF_CANONICALIZATION_FAILED")
    atom_ids = tuple(
        expected_atom_ids[atom.GetAtomMapNum() - 1] for atom in parsed.GetAtoms()
    )
    if len(set(atom_ids)) != len(expected_atom_ids):
        raise ValueError("APPROVED_PRE_SDF_ATOM_NAMESPACE_INVALID")
    return smiles, atom_ids


def _source_mmcif_text_v1(path: Path) -> str:
    payload = path.read_bytes()
    if path.suffix == ".gz":
        try:
            payload = gzip.decompress(payload)
        except (OSError, EOFError) as error:
            raise ValueError("REAL_EXACT4_SOURCE_GZIP_INVALID") from error
    return payload.decode("utf-8", "replace")


def _protein_leakage_facts_v1(
    source_path: Path, protein_label_asym_id: str,
) -> Mapping[str, str | bool]:
    text = _source_mmcif_text_v1(source_path)
    _, asym_rows = independence_evidence_owner.parse_loop(text, "_struct_asym.")
    _, sequence_rows = independence_evidence_owner.parse_loop(
        text, "_entity_poly_seq."
    )
    asym_to_entity = {
        row.get("_struct_asym.id", ""): row.get("_struct_asym.entity_id", "")
        for row in asym_rows
    }
    entity_id = asym_to_entity.get(protein_label_asym_id, "")
    entity_rows, numbering = independence_evidence_owner._validate_entity_poly_sequence([
        row for row in sequence_rows
        if row.get("_entity_poly_seq.entity_id", "") == entity_id
    ])
    monomers = [row.get("_entity_poly_seq.mon_id", "") for row in entity_rows]
    one_letter, unknown_count, _unknown_codes = (
        independence_evidence_owner._seq_to_one_letter(monomers)
    )
    accession, _isoform, _label, accession_status, crosscheck = (
        independence_evidence_owner._extract_accession(
            text, entity_id, protein_label_asym_id
        )
    )
    monomer_sequence = ";".join(monomers)
    complete = bool(
        entity_rows
        and numbering["sequence_numbering_status"] == "continuous_from_1"
        and crosscheck != "struct_ref_seq_crosscheck_mismatch"
        and unknown_count == 0
        and one_letter
    )
    return {
        "complete": complete,
        "accession": accession if accession_status == "unique_uniprot_accession" else "",
        "monomer_sequence_sha256": (
            _sha256(monomer_sequence.encode("utf-8")) if monomer_sequence else ""
        ),
        "one_letter_sequence": one_letter,
    }


def _ligand_leakage_facts_v1(canonical_smiles: str) -> Mapping[str, str | bool]:
    try:
        from rdkit import Chem
        from rdkit.Chem.Scaffolds import MurckoScaffold
    except ImportError:
        return {"complete": False, "graph_sha256": "", "scaffold_sha256": ""}
    molecule = Chem.MolFromSmiles(canonical_smiles)
    if molecule is None:
        return {"complete": False, "graph_sha256": "", "scaffold_sha256": ""}
    molecule = Chem.RemoveHs(molecule)
    for atom in molecule.GetAtoms():
        atom.SetAtomMapNum(0)
    canonical = Chem.MolToSmiles(
        molecule, isomericSmiles=True, canonical=True,
    )
    scaffold = MurckoScaffold.GetScaffoldForMol(molecule)
    scaffold_smiles = (
        Chem.MolToSmiles(scaffold, isomericSmiles=True, canonical=True)
        if scaffold.GetNumHeavyAtoms() else ""
    )
    return {
        "complete": bool(canonical),
        "graph_sha256": _sha256(canonical.encode("utf-8")),
        "scaffold_sha256": (
            _sha256(scaffold_smiles.encode("utf-8")) if scaffold_smiles else ""
        ),
    }


def _real_exact4_pair_must_link_v1(
    left: ExpansionCandidateV1, right: ExpansionCandidateV1,
) -> bool:
    ligand_related = (
        left.leakage_ligand_graph_sha256 == right.leakage_ligand_graph_sha256
        or bool(
            left.leakage_ligand_scaffold_sha256
            and left.leakage_ligand_scaffold_sha256
            == right.leakage_ligand_scaffold_sha256
        )
    )
    protein_related = (
        bool(
            left.leakage_protein_accession
            and left.leakage_protein_accession == right.leakage_protein_accession
        )
        or left.leakage_protein_sequence_sha256
        == right.leakage_protein_sequence_sha256
        or independence_evidence_owner.global_identity(
            left.leakage_protein_sequence, right.leakage_protein_sequence
        ) >= 0.5
    )
    return ligand_related or protein_related


def _apply_real_exact4_leakage_v1(
    candidates: Sequence[ExpansionCandidateV1], repo_root: Path,
) -> tuple[ExpansionCandidateV1, ...]:
    exact4 = [
        candidate for candidate in candidates
        if candidate.candidate_identity in {
            "2DJF/1ZB", "6DI9/GJJ", "5F2E/5UT", "6OIM/MOV",
        }
    ]
    ligand_rows = _sha_bound_csv_rows_v1(
        repo_root, BASELINE_LIGAND_EVIDENCE_RELATIVE
    )
    protein_rows = _sha_bound_csv_rows_v1(
        repo_root, BASELINE_PROTEIN_EVIDENCE_RELATIVE
    )
    group_rows = _sha_bound_csv_rows_v1(repo_root, BASELINE_FINAL_GROUP_RELATIVE)
    ligand_by_id = {row["sample_index_row_id"]: row for row in ligand_rows}
    protein_by_id = {row["sample_index_row_id"]: row for row in protein_rows}
    group_by_id = {
        row["sample_index_row_id"]: row["final_leakage_group_id"]
        for row in group_rows
    }
    baseline_ids = sorted(group_by_id)
    baseline_complete = (
        len(baseline_ids) == 11
        and set(ligand_by_id) == set(protein_by_id) == set(group_by_id)
        and all(row.get("ligand_graph_evidence_passed") == "True" for row in ligand_rows)
        and all(row.get("protein_sequence_evidence_passed") == "True" for row in protein_rows)
    )
    parent = {item: item for item in (*baseline_ids, *(c.candidate_identity for c in exact4))}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)

    for left in baseline_ids:
        for right in baseline_ids:
            if left < right and group_by_id[left] == group_by_id[right]:
                union(left, right)
    candidate_complete: dict[str, bool] = {}
    for candidate in exact4:
        complete = bool(
            baseline_complete
            and candidate.leakage_ligand_graph_sha256
            and candidate.leakage_protein_sequence_sha256
            and candidate.leakage_protein_sequence
        )
        candidate_complete[candidate.candidate_identity] = complete
        if not complete:
            continue
        for sample_id in baseline_ids:
            ligand = ligand_by_id[sample_id]
            protein = protein_by_id[sample_id]
            same_graph = (
                candidate.leakage_ligand_graph_sha256
                == ligand["canonical_graph_sha256"]
            )
            same_scaffold = bool(
                candidate.leakage_ligand_scaffold_sha256
                and candidate.leakage_ligand_scaffold_sha256
                == ligand["murcko_scaffold_sha256"]
            )
            same_accession = bool(
                candidate.leakage_protein_accession
                and candidate.leakage_protein_accession
                == protein["protein_accession"]
            )
            same_exact_sequence = (
                candidate.leakage_protein_sequence_sha256
                == protein["full_polymer_monomer_sequence_sha256"]
            )
            sequence_related = independence_evidence_owner.global_identity(
                candidate.leakage_protein_sequence,
                protein["full_polymer_one_letter_sequence"],
            ) >= 0.5
            if any((same_graph, same_scaffold, same_accession, same_exact_sequence, sequence_related)):
                union(candidate.candidate_identity, sample_id)
    for index, left in enumerate(exact4):
        if not candidate_complete[left.candidate_identity]:
            continue
        for right in exact4[index + 1:]:
            if (
                candidate_complete[right.candidate_identity]
                and _real_exact4_pair_must_link_v1(left, right)
            ):
                union(left.candidate_identity, right.candidate_identity)

    bindings = tuple(sorted(
        (relative.as_posix(), EVIDENCE_SHA256_V1[relative])
        for relative in (
            BASELINE_LIGAND_EVIDENCE_RELATIVE,
            BASELINE_PROTEIN_EVIDENCE_RELATIVE,
            BASELINE_FINAL_GROUP_RELATIVE,
        )
    ))
    updated: dict[str, ExpansionCandidateV1] = {}
    for candidate in exact4:
        identity = candidate.candidate_identity
        if not candidate_complete[identity]:
            updated[identity] = candidate
            continue
        component = {item for item in parent if find(item) == find(identity)}
        baseline_groups = tuple(sorted({
            group_by_id[item] for item in component if item in group_by_id
        }))
        exact_members = sorted(item for item in component if "/" in item)
        conflict = len(baseline_groups) > 1
        if len(baseline_groups) == 1:
            leakage_key = baseline_groups[0]
        else:
            leakage_key = "COVAPIE_REAL_EXACT4_LEAKAGE_V1:" + _sha256(
                _canonical_json({
                    "policy": (
                        "conservative_union_of_ligand_graph_scaffold_and_"
                        "protein_accession_sequence_clusters_v1"
                    ),
                    "component_evidence": tuple(sorted(
                        (
                            member.leakage_ligand_graph_sha256,
                            member.leakage_ligand_scaffold_sha256,
                            member.leakage_protein_accession,
                            member.leakage_protein_sequence_sha256,
                        )
                        for member in exact4
                        if member.candidate_identity in exact_members
                    )),
                })
            )
        updated[identity] = replace(
            candidate,
            baseline_leakage_evidence_complete=True,
            leakage_key=leakage_key,
            leakage_conflict=conflict,
            leakage_baseline_group_ids=baseline_groups,
            machine_evidence_bindings=tuple(sorted({
                *candidate.machine_evidence_bindings, *bindings,
            })),
        )
    return tuple(updated.get(candidate.candidate_identity, candidate) for candidate in candidates)


def parse_human_review_packet_v1(payload: bytes) -> tuple[Mapping[str, str], ...]:
    """Parse the simple quoted scalar decision blocks without filling them."""

    text = payload.decode("utf-8")
    blocks = re.findall(r"```yaml\n(.*?)```", text, flags=re.DOTALL)
    records: list[Mapping[str, str]] = []
    for block in blocks:
        record: dict[str, str] = {}
        for line in block.splitlines():
            match = re.fullmatch(r'([a-z_]+): "([^"]*)"(?:\s+#.*)?', line)
            if match:
                record[match.group(1)] = match.group(2)
        if "candidate_identity" in record:
            records.append(record)
    identities = tuple(record["candidate_identity"] for record in records)
    if identities != ("2DJF/1ZB", "6DI9/GJJ", "5F2E/5UT", "6OIM/MOV"):
        raise ValueError("REVIEW_PACKET_EXACT4_IDENTITY_ORDER_INVALID")
    return tuple(records)


def _truth(value: str) -> bool:
    if value not in {"true", "false"}:
        raise ValueError("CSV_BOOLEAN_NOT_EXACT_LOWERCASE")
    return value == "true"


def load_current_non_exact16_candidates_v1(
    repo_root: Path,
) -> tuple[ExpansionCandidateV1, ...]:
    inventory_path = repo_root / INVENTORY_RELATIVE
    packet_path = repo_root / REVIEW_PACKET_RELATIVE
    inventory_payload = inventory_path.read_bytes()
    packet_payload = packet_path.read_bytes()
    if _sha256(inventory_payload) != INVENTORY_SHA256:
        raise ValueError("CURRENT_NON_EXACT16_INVENTORY_SHA256_MISMATCH")
    if _sha256(packet_payload) != REVIEW_PACKET_SHA256:
        raise ValueError("CURRENT_EXACT4_REVIEW_PACKET_SHA256_MISMATCH")
    packet_records = parse_human_review_packet_v1(packet_payload)
    if any(
        record.get("review_status")
        or record.get("independent_sample_assignment_decision")
        for record in packet_records
    ):
        raise ValueError("CURRENT_EXACT4_PACKET_MUST_REMAIN_BLANK")
    rows = _csv_rows(inventory_path)
    if len(rows) != 12 or len({row["candidate_identity"] for row in rows}) != 12:
        raise ValueError("CURRENT_NON_EXACT16_POPULATION_INVALID")

    recovered_path = repo_root / RECOVERED7_EVIDENCE_RELATIVE
    recovered_payload = recovered_path.read_bytes()
    if _sha256(recovered_payload) != EVIDENCE_SHA256_V1[RECOVERED7_EVIDENCE_RELATIVE]:
        raise ValueError("RECOVERED7_REAL_EXACT4_EVIDENCE_SHA256_MISMATCH")
    recovered = json.loads(recovered_payload)
    recovered_samples = {
        f"{sample['pdb_id']}/{sample['ligand_component_id']}": sample
        for sample in recovered["samples"]
    }
    topology_by_component = recovered["component_topology_authorities"]
    direct_ligand_rows = _sha_bound_csv_rows_v1(repo_root, DIRECT_LIGAND_ATOMS_RELATIVE)
    direct_bond_rows = _sha_bound_csv_rows_v1(repo_root, DIRECT_LIGAND_BONDS_RELATIVE)
    direct_pocket_rows = _sha_bound_csv_rows_v1(repo_root, DIRECT_POCKET_ATOMS_RELATIVE)
    direct_event_rows = _sha_bound_csv_rows_v1(repo_root, DIRECT_CONFIRMED_EVENTS_RELATIVE)
    direct_pair_rows = _sha_bound_csv_rows_v1(repo_root, DIRECT_COORDINATE_PAIRS_RELATIVE)
    direct_full_ligand_rows = _sha_bound_csv_rows_v1(
        repo_root, DIRECT_FULL_LIGAND_ATOMS_RELATIVE
    )
    direct_writeback_rows = _sha_bound_csv_rows_v1(repo_root, DIRECT_PRE_WRITEBACK_RELATIVE)
    direct_pre_qa_rows = _sha_bound_csv_rows_v1(repo_root, DIRECT_PRE_QA_RELATIVE)
    direct_identity_by_pdb = {"6DI9": "GJJ", "5F2E": "5UT", "6OIM": "MOV"}
    direct_sample_by_pdb = {
        "6DI9": "BTK_C481_6DI9",
        "5F2E": "KRAS_G12C_5F2E",
        "6OIM": "KRAS_G12C_6OIM",
    }

    candidates: list[ExpansionCandidateV1] = []
    for row in rows:
        identity = row["candidate_identity"]
        pdb_id = row["pdb_id"]
        ligand = row["ligand_comp_id"]
        symbols: tuple[str, ...] = ()
        retained: tuple[int | str, ...] = ()
        bonds: tuple[tuple[int | str, int | str, str], ...] = ()
        smiles = ""
        leakage_smiles = ""
        smarts_atom_ids: tuple[int | str, ...] = ()
        reactive: int | str | None = None
        atom_maps: tuple[tuple[int | str, int], ...] = ()
        formal_charges: tuple[tuple[int | str, int], ...] = ()
        pre_bonds: tuple[tuple[int | str, int | str, str], ...] = ()
        pre_graph_authoritative = False
        formal_charge_authoritative = False
        protein_endpoint: int | str | None = None
        source_event_protein: int | str | None = None
        source_event_ligand: int | str | None = None
        retained_reactive: int | str | None = None
        ligand_coordinates: tuple[tuple[int | str, str, float, float, float], ...] = ()
        pocket_coordinates: tuple[tuple[int | str, str, float, float, float], ...] = ()
        machine_bindings: tuple[tuple[str, str], ...] = (
            (INVENTORY_RELATIVE.as_posix(), INVENTORY_SHA256),
            (REVIEW_PACKET_RELATIVE.as_posix(), REVIEW_PACKET_SHA256),
        )
        protein_label_asym = ""
        protein_endpoint_descriptor = ""
        ligand_endpoint_descriptor = ""
        observed_post_distance = (
            float(row["observed_complex_distance_angstrom"])
            if row["observed_complex_distance_available"] == "true" else None
        )
        if identity in recovered_samples:
            sample = recovered_samples[identity]
            ligand_atoms = sample["canonical_model_bound_ligand_atoms"]
            pocket_atoms = sample["canonical_pocket"]["retained_atoms"]
            symbols = tuple(
                atom["type_symbol"] for atom in (*ligand_atoms, *pocket_atoms)
            )
            retained = tuple(atom["auth_atom_id"] for atom in ligand_atoms)
            reactive = sample["explicit_event"]["ligand_endpoint"]["auth_atom_id"]
            atom_maps = tuple((atom_id, index) for index, atom_id in enumerate(retained, 1))
            ligand_coordinates = tuple(
                (
                    atom["auth_atom_id"], atom["type_symbol"],
                    float(atom["x"]), float(atom["y"]), float(atom["z"]),
                )
                for atom in ligand_atoms
            )
            pocket_coordinates = tuple(
                (
                    int(atom["atom_site_id"]), atom["type_symbol"],
                    float(atom["x"]), float(atom["y"]), float(atom["z"]),
                )
                for atom in pocket_atoms
            )
            protein_endpoint = int(
                sample["explicit_event"]["protein_endpoint"]["atom_site_id"]
            )
            recovered_protein_endpoint = sample["explicit_event"]["protein_endpoint"]
            recovered_ligand_endpoint = sample["explicit_event"]["ligand_endpoint"]
            protein_endpoint_descriptor = ":".join((
                recovered_protein_endpoint["auth_asym_id"],
                recovered_protein_endpoint["auth_comp_id"],
                recovered_protein_endpoint["auth_seq_id"],
                recovered_protein_endpoint["auth_atom_id"],
            ))
            ligand_endpoint_descriptor = ":".join((
                recovered_ligand_endpoint["auth_asym_id"],
                recovered_ligand_endpoint["auth_comp_id"],
                recovered_ligand_endpoint["auth_seq_id"],
                recovered_ligand_endpoint["auth_atom_id"],
            ))
            source_event_protein = protein_endpoint
            source_event_ligand = reactive
            retained_reactive = reactive
            protein_label_asym = sample["explicit_event"]["protein_endpoint"][
                "label_asym_id"
            ]
            machine_bindings = tuple(sorted({
                *machine_bindings,
                (
                    RECOVERED7_EVIDENCE_RELATIVE.as_posix(),
                    EVIDENCE_SHA256_V1[RECOVERED7_EVIDENCE_RELATIVE],
                ),
            }))
            topology = topology_by_component[ligand]
            element_by_id = {
                atom["atom_id"]: atom["type_symbol"]
                for atom in topology["component_atoms"]
                if not atom["explicit_hydrogen"]
            }
            retained_set = set(retained)
            bonds = tuple(
                (
                    bond["atom_id_1"], bond["atom_id_2"],
                    bond["normalized_bond_order"],
                )
                for bond in topology["component_internal_bonds"]
                if bond["atom_id_1"] in retained_set
                and bond["atom_id_2"] in retained_set
            )
            smiles, smarts_atom_ids = _canonical_smiles_and_atom_ids_from_graph_v1(
                tuple((atom_id, element_by_id[atom_id]) for atom_id in retained),
                bonds,
            )
            leakage_smiles = smiles
        elif pdb_id in direct_identity_by_pdb:
            ligand_atoms = sorted(
                (item for item in direct_ligand_rows if item["pdb_id"] == pdb_id),
                key=lambda item: int(item["rdkit_atom_idx"]),
            )
            pocket_atoms = [
                item for item in direct_pocket_rows if item["pdb_id"] == pdb_id
            ]
            symbols = tuple(
                [item["atom_symbol"] for item in ligand_atoms]
                + [item["type_symbol"] for item in pocket_atoms]
            )
            retained = tuple(int(item["rdkit_atom_idx"]) for item in ligand_atoms)
            reactive_matches = [
                int(item["rdkit_atom_idx"])
                for item in ligand_atoms
                if item["is_covalent_ligand_endpoint_atom"] == "True"
            ]
            reactive = reactive_matches[0] if len(reactive_matches) == 1 else None
            atom_maps = tuple(
                (int(item["rdkit_atom_idx"]), int(item["rdkit_atom_idx"]) + 1)
                for item in ligand_atoms
            )
            formal_charges = tuple(
                (int(item["rdkit_atom_idx"]), int(item["formal_charge"]))
                for item in ligand_atoms
            )
            order_map = {
                "SINGLE": "single", "DOUBLE": "double", "TRIPLE": "triple",
                "AROMATIC": "aromatic",
            }
            bonds = tuple(
                (
                    int(item["begin_rdkit_atom_idx"]),
                    int(item["end_rdkit_atom_idx"]),
                    order_map[item["bond_type"]],
                )
                for item in direct_bond_rows if item["pdb_id"] == pdb_id
            )
            smiles, smarts_atom_ids = _canonical_smiles_and_atom_ids_from_graph_v1(
                tuple((int(item["rdkit_atom_idx"]), item["atom_symbol"]) for item in ligand_atoms),
                bonds,
            )
            sample_name = direct_sample_by_pdb[pdb_id]
            writeback = [
                item for item in direct_writeback_rows
                if item["sample_id"] == sample_name
            ]
            pre_qa = [
                item for item in direct_pre_qa_rows
                if item["sample_id"] == sample_name
            ]
            sdf_paths = {item["source_pre_reaction_sdf_path"] for item in ligand_atoms}
            sdf_shas = {item["source_pre_reaction_sdf_sha256"] for item in ligand_atoms}
            if (
                len(writeback) != 1
                or writeback[0]["reviewer_decision"] != "approved"
                or writeback[0]["review_status"] != "reviewed"
                or writeback[0]["write_back_status"]
                != "written_after_explicit_human_approval"
                or len(pre_qa) != 1
                or pre_qa[0]["pre_reaction_sdf_qa_passed"] != "true"
                or pre_qa[0]["safe_as_derived_pre_reaction_artifact"] != "true"
                or len(sdf_paths) != 1 or len(sdf_shas) != 1
                or pre_qa[0]["output_pre_reaction_sdf"] != next(iter(sdf_paths))
            ):
                raise ValueError("DIRECT3_APPROVED_PRE_GRAPH_AUTHORITY_INVALID:" + pdb_id)
            sdf_relative = Path(next(iter(sdf_paths)))
            sdf_sha = next(iter(sdf_shas))
            if not _is_sha(sdf_sha) or _sha256((repo_root / sdf_relative).read_bytes()) != sdf_sha:
                raise ValueError("DIRECT3_APPROVED_PRE_SDF_SHA256_MISMATCH:" + pdb_id)
            smiles, smarts_atom_ids = _canonical_smiles_and_atom_ids_from_pre_sdf_v1(
                repo_root / sdf_relative, retained,
            )
            leakage_smiles = smiles
            pre_bonds = bonds
            pre_graph_authoritative = True
            formal_charge_authoritative = True

            proposal_relative = DIRECT_ROLE_PROPOSAL_RELATIVE_V1[pdb_id]
            proposal_path = repo_root / proposal_relative
            proposal_sha = DIRECT_ROLE_PROPOSAL_SHA256_V1[pdb_id]
            if _sha256(proposal_path.read_bytes()) != proposal_sha:
                raise ValueError("DIRECT3_ROLE_PROPOSAL_SHA256_MISMATCH:" + pdb_id)
            proposal_rows = _csv_rows(proposal_path)
            proposal_by_index = {
                int(item["sdf_atom_index"]): item for item in proposal_rows
            }
            full_ligand = [
                item for item in direct_full_ligand_rows if item["pdb_id"] == pdb_id
            ]
            if (
                len(proposal_by_index) != len(ligand_atoms)
                or len(full_ligand) != len(ligand_atoms)
            ):
                raise ValueError("DIRECT3_LIGAND_COORDINATE_NAMESPACE_INCOMPLETE:" + pdb_id)
            coordinate_rows: list[tuple[int, str, float, float, float]] = []
            atom_site_by_index: dict[int, str] = {}
            for atom in ligand_atoms:
                index = int(atom["rdkit_atom_idx"])
                proposal = proposal_by_index.get(index)
                matches = [
                    item for item in full_ligand
                    if proposal is not None
                    and item["auth_atom_id"] == proposal["pdb_atom_name"]
                ]
                if (
                    proposal is None or len(matches) != 1
                    or matches[0]["type_symbol"].upper()
                    != atom["atom_symbol"].upper()
                ):
                    raise ValueError("DIRECT3_LIGAND_COORDINATE_MAPPING_INVALID:" + pdb_id)
                selected = matches[0]
                coordinate_rows.append((
                    index, atom["atom_symbol"], float(selected["Cartn_x"]),
                    float(selected["Cartn_y"]), float(selected["Cartn_z"]),
                ))
                atom_site_by_index[index] = selected["atom_site_id"]
            ligand_coordinates = tuple(coordinate_rows)

            events = [item for item in direct_event_rows if item["pdb_id"] == pdb_id]
            pairs = [item for item in direct_pair_rows if item["pdb_id"] == pdb_id]
            if (
                len(events) != 1 or events[0]["manual_review_validated"] != "True"
                or len(pairs) != 1 or pairs[0]["coordinate_pair_sanity_passed"] != "True"
                or reactive is None
                or events[0]["manual_confirmed_ligand_atom_id"]
                != proposal_by_index[reactive]["pdb_atom_name"]
                or pairs[0]["ligand_selected_atom_site_id"]
                != atom_site_by_index[reactive]
            ):
                raise ValueError("DIRECT3_EXACT_EVENT_COORDINATE_AUTHORITY_INVALID:" + pdb_id)
            pair = pairs[0]
            observed_post_distance = float(pair["computed_endpoint_distance_angstrom"])
            protein_endpoint_descriptor = ":".join((
                pair["protein_selected_auth_asym_id"],
                pair["protein_selected_auth_comp_id"],
                pair["protein_selected_auth_seq_id"],
                pair["protein_selected_auth_atom_id"],
            ))
            ligand_endpoint_descriptor = ":".join((
                pair["ligand_selected_auth_asym_id"],
                pair["ligand_selected_auth_comp_id"],
                pair["ligand_selected_auth_seq_id"],
                pair["ligand_selected_auth_atom_id"],
            ))
            protein_endpoint = int(pair["protein_selected_atom_site_id"])
            source_event_protein = protein_endpoint
            source_event_ligand = reactive
            retained_reactive = reactive
            pocket_coordinates = tuple(
                (
                    int(item["atom_site_id"]), item["type_symbol"],
                    float(item["Cartn_x"]), float(item["Cartn_y"]),
                    float(item["Cartn_z"]),
                )
                for item in pocket_atoms
            )
            if sum(item[0] == protein_endpoint for item in pocket_coordinates) != 1:
                raise ValueError("DIRECT3_POCKET_ENDPOINT_NOT_EXACT_ONE:" + pdb_id)
            protein_label_asym = pair["protein_selected_label_asym_id"]
            machine_bindings = tuple(sorted({
                *machine_bindings,
                *((relative.as_posix(), EVIDENCE_SHA256_V1[relative]) for relative in (
                    DIRECT_CONFIRMED_EVENTS_RELATIVE,
                    DIRECT_COORDINATE_PAIRS_RELATIVE,
                    DIRECT_LIGAND_ATOMS_RELATIVE,
                    DIRECT_LIGAND_BONDS_RELATIVE,
                    DIRECT_POCKET_ATOMS_RELATIVE,
                    DIRECT_FULL_LIGAND_ATOMS_RELATIVE,
                    DIRECT_PRE_WRITEBACK_RELATIVE,
                    DIRECT_PRE_QA_RELATIVE,
                )),
                (proposal_relative.as_posix(), proposal_sha),
                (sdf_relative.as_posix(), sdf_sha),
            }))

        final = row["final_classification"]
        prior = (
            final if final in {
                "REJECT", "MISSING_SOURCE_AUTHORITY",
                "NEEDS_RUNTIME_PROFILE_EXTENSION",
            } else ""
        )
        signature = _sha256(_canonical_json({
            "schema": "covapie_candidate_only_chemistry_unavailable_v1",
            "ligand_component_id": ligand,
            "canonical_graph_available": bool(smiles),
        }))
        blockers = tuple(filter(None, row["blocking_reasons"].split(";")))
        if identity == "6DI9/GJJ" and (
            "DRAFT_ROLE_PARTITION_HAS_TWO_SCAFFOLD_LINKER_BOUNDARIES"
            not in blockers
        ):
            raise ValueError("6DI9_DRAFT_BOUNDARY_MULTIPLICITY_NOT_PRESERVED")
        ligand_leakage = {
            "complete": False, "graph_sha256": "", "scaffold_sha256": "",
        }
        protein_leakage = {
            "complete": False, "accession": "",
            "monomer_sequence_sha256": "", "one_letter_sequence": "",
        }
        if identity in {"2DJF/1ZB", "6DI9/GJJ", "5F2E/5UT", "6OIM/MOV"}:
            source_path = repo_root / row["source_relative_path"]
            if verify_existing_source_v1(source_path, row["source_SHA256"]) == "SOURCE_ALREADY_PRESENT_AND_VERIFIED":
                ligand_leakage = _ligand_leakage_facts_v1(
                    leakage_smiles or smiles
                )
                protein_leakage = _protein_leakage_facts_v1(
                    source_path, protein_label_asym,
                )
        leakage_axes = tuple(sorted(filter(None, (
            "LIGAND_GRAPH:" + str(ligand_leakage["graph_sha256"])
            if ligand_leakage["graph_sha256"] else "",
            "LIGAND_SCAFFOLD:" + str(ligand_leakage["scaffold_sha256"])
            if ligand_leakage["scaffold_sha256"] else "",
            "PROTEIN_ACCESSION:" + str(protein_leakage["accession"])
            if protein_leakage["accession"] else "",
            "PROTEIN_EXACT_SEQUENCE:"
            + str(protein_leakage["monomer_sequence_sha256"])
            if protein_leakage["monomer_sequence_sha256"] else "",
        ))))
        candidate = ExpansionCandidateV1(
            candidate_identity=identity,
            pdb_id=pdb_id,
            ligand_comp_id=ligand,
            source_identity=row["source_relative_path"],
            source_path=repo_root / row["source_relative_path"],
            expected_source_sha256=row["source_SHA256"],
            explicit_event_authoritative=_truth(row["explicit_covalent_event_available"]),
            conflicting_explicit_event=False,
            protein_endpoint_exact_cys_sg=_truth(row["protein_endpoint_exact_CYS_SG"]),
            ligand_endpoint_mapping_count=1 if _truth(row["endpoint_mapping_unique"]) else 0,
            retained_endpoint_mapping_count=(
                1 if _truth(row["endpoint_retained_in_model_projection"]) else 0
            ),
            canonical_topology_valid=_truth(row["checkpoint_feature_semantics_valid"]),
            pocket_valid=_truth(row["POST_authority_eligible"]),
            atom_symbols=symbols,
            chemistry_signature_sha256=signature,
            chemistry_signature_authoritative=False,
            canonical_ligand_smiles=smiles,
            smarts_atom_ids=smarts_atom_ids,
            reactive_ligand_atom_id=reactive,
            reactive_atom_mapping_count=1 if reactive is not None else 0,
            retained_heavy_atoms=retained,
            scaffold_atoms=(),
            linker_atoms=(),
            warhead_atoms=(),
            explicit_graph_bonds=bonds,
            seed_atoms=(),
            primary_anchor_atom=None,
            direction_anchor_atom=None,
            optional_plane_anchor_atom=None,
            role_profile=(
                "UNSUPPORTED_EMBEDDED_MULTI_BOUNDARY_PROFILE"
                if identity == "2R9F/K2Z" else STRICT_PROFILE
            ),
            role_rule_id="NONE",
            role_rule_version="NONE",
            role_rule_match_count=0,
            role_authority_published=False,
            baseline_leakage_evidence_complete=False,
            leakage_key="",
            leakage_conflict=False,
            duplicate_identity=False,
            post_distance_angstrom=(
                observed_post_distance
            ),
            pre_reaction_graph_authoritative=pre_graph_authoritative,
            formal_charge_authoritative=formal_charge_authoritative,
            atom_map_numbers=atom_maps,
            atom_formal_charges=formal_charges,
            pre_reaction_bonds=pre_bonds,
            protein_endpoint_atom_id=protein_endpoint,
            source_event_protein_atom_id=source_event_protein,
            source_event_ligand_atom_id=source_event_ligand,
            retained_reactive_atom_id=retained_reactive,
            ligand_atom_coordinates=ligand_coordinates,
            pocket_atom_coordinates=pocket_coordinates,
            prior_disposition=prior,
            prior_blocking_reasons=blockers,
            machine_evidence_bindings=machine_bindings,
            leakage_ligand_graph_sha256=str(ligand_leakage["graph_sha256"]),
            leakage_ligand_scaffold_sha256=str(ligand_leakage["scaffold_sha256"]),
            leakage_protein_accession=str(protein_leakage["accession"]),
            leakage_protein_sequence_sha256=str(
                protein_leakage["monomer_sequence_sha256"]
            ),
            leakage_protein_sequence=str(protein_leakage["one_letter_sequence"]),
            leakage_axis_keys=leakage_axes,
            source_event_protein_endpoint_descriptor=protein_endpoint_descriptor,
            source_event_ligand_endpoint_descriptor=ligand_endpoint_descriptor,
        )
        if smiles:
            candidate = replace(
                candidate,
                chemistry_signature_sha256=build_exact_chemistry_signature_v1(candidate),
            )
        candidates.append(candidate)
    candidates_with_leakage = _apply_real_exact4_leakage_v1(candidates, repo_root)
    finalized: list[ExpansionCandidateV1] = []
    for candidate in candidates_with_leakage:
        candidate = with_pre_review_evidence_digest_v1(candidate)
        if (
            candidate.candidate_identity
            in {"2DJF/1ZB", "6DI9/GJJ", "5F2E/5UT", "6OIM/MOV"}
            and not _mechanical_eligibility_reasons_v1(candidate)
        ):
            post_valid, post_reasons, _ = validate_post_geometry_authority_v1(candidate)
            if not post_valid:
                raise ValueError(
                    "REAL_EXACT4_POST_MACHINE_EVIDENCE_INVALID:"
                    + candidate.candidate_identity + ":" + ";".join(post_reasons)
                )
        finalized.append(candidate)
    return tuple(finalized)


def _direct_role_proposal_v1(
    candidate: ExpansionCandidateV1, repo_root: Path,
) -> Mapping[str, Any]:
    relative = DIRECT_ROLE_PROPOSAL_RELATIVE_V1.get(candidate.pdb_id)
    if relative is None:
        return {
            "status": "NONE_PUBLISHED",
            "scaffold_atom_ids": (), "linker_atom_ids": (),
            "warhead_atom_ids": (), "scaffold_linker_boundaries": (),
            "linker_warhead_boundaries": (), "proposed_warhead_smarts": "",
        }
    expected_sha = DIRECT_ROLE_PROPOSAL_SHA256_V1[candidate.pdb_id]
    path = repo_root / relative
    if _sha256(path.read_bytes()) != expected_sha:
        raise ValueError("DIRECT3_ROLE_PROPOSAL_SHA256_MISMATCH:" + candidate.pdb_id)
    rows = _csv_rows(path)
    by_role: dict[str, tuple[int, ...]] = {}
    for role in ("scaffold", "linker", "warhead"):
        by_role[role] = tuple(sorted(
            int(row["sdf_atom_index"]) for row in rows
            if row["final_role"] == role
        ))
    if set().union(*(set(value) for value in by_role.values())) != set(
        candidate.retained_heavy_atoms
    ):
        raise ValueError("DIRECT3_ROLE_PROPOSAL_PARTITION_INCOMPLETE")
    proposed = replace(
        candidate,
        scaffold_atoms=by_role["scaffold"], linker_atoms=by_role["linker"],
        warhead_atoms=by_role["warhead"],
    )
    scaffold_linker, linker_warhead, _direct = _cross_role_boundaries_v1(proposed)
    try:
        from rdkit import Chem
        molecule = Chem.MolFromSmiles(candidate.canonical_ligand_smiles)
        selected = [
            index for index, atom_id in enumerate(candidate.smarts_atom_ids)
            if atom_id in set(by_role["warhead"])
        ]
        proposed_smarts = (
            Chem.MolFragmentToSmarts(molecule, atomsToUse=selected, isomericSmarts=True)
            if molecule is not None and selected else ""
        )
    except (ImportError, RuntimeError, ValueError):
        proposed_smarts = ""
    return {
        "status": "DRAFT_PROPOSAL_ONLY_NOT_AUTHORITY",
        "source_path": relative.as_posix(),
        "source_sha256": expected_sha,
        "scaffold_atom_ids": by_role["scaffold"],
        "linker_atom_ids": by_role["linker"],
        "warhead_atom_ids": by_role["warhead"],
        "scaffold_linker_boundaries": scaffold_linker,
        "linker_warhead_boundaries": linker_warhead,
        "proposed_warhead_smarts": proposed_smarts,
        "atom_labels": tuple(
            {
                "atom_id": int(row["sdf_atom_index"]),
                "pdb_atom_name": row["pdb_atom_name"],
                "element": row["element"],
                "proposed_role": row["final_role"],
            }
            for row in sorted(rows, key=lambda row: int(row["sdf_atom_index"]))
        ),
    }


def build_real_exact4_human_review_decision_template_v2(
    repo_root: Path,
) -> bytes:
    candidates = {
        candidate.candidate_identity: candidate
        for candidate in load_current_non_exact16_candidates_v1(repo_root)
        if candidate.candidate_identity
        in {"2DJF/1ZB", "6DI9/GJJ", "5F2E/5UT", "6OIM/MOV"}
    }
    identities = ("2DJF/1ZB", "6DI9/GJJ", "5F2E/5UT", "6OIM/MOV")
    if tuple(candidates) != identities:
        raise ValueError("REAL_EXACT4_TEMPLATE_POPULATION_INVALID")
    records: list[Mapping[str, Any]] = []
    for identity in identities:
        candidate = candidates[identity]
        proposal = _direct_role_proposal_v1(candidate, repo_root)
        map_by_atom = dict(candidate.atom_map_numbers)
        machine_pre_bonds = tuple(sorted(
            _normalized_bond_v1(item, map_by_atom)
            for item in candidate.pre_reaction_bonds
        )) if candidate.pre_reaction_graph_authoritative else ()
        machine_charges = {
            str(map_by_atom[atom_id]): charge
            for atom_id, charge in candidate.atom_formal_charges
        } if candidate.formal_charge_authoritative else {}
        warnings = list(candidate.prior_blocking_reasons)
        if identity == "2DJF/1ZB":
            warnings.append(
                "HUMAN_MUST_ESTABLISH_PRE_REACTION_GRAPH_AND_FORMAL_CHARGES"
            )
        if identity == "6DI9/GJJ":
            warnings.append(
                "DRAFT_HAS_TWO_SCAFFOLD_LINKER_BOUNDARIES_DO_NOT_APPROVE_UNCHANGED"
            )
        records.append({
            "candidate_identity": identity,
            "bound_source_identity": candidate.source_identity,
            "bound_source_sha256": candidate.expected_source_sha256,
            "pre_review_evidence_digest": candidate.pre_review_evidence_digest,
            "source_assignment_record_sha256": _candidate_assignment_sha256_v1(candidate),
            "expected_final_chemistry_signature_sha256": "",
            "machine_evidence": {
                "binding_status": "IMMUTABLE_MACHINE_EVIDENCE_PREFILLED",
                "exact_event_endpoints": {
                    "protein_endpoint_atom_id": candidate.source_event_protein_atom_id,
                    "ligand_endpoint_atom_id": candidate.source_event_ligand_atom_id,
                    "retained_reactive_atom_id": candidate.retained_reactive_atom_id,
                    "protein_endpoint_descriptor": (
                        candidate.source_event_protein_endpoint_descriptor
                    ),
                    "ligand_endpoint_descriptor": (
                        candidate.source_event_ligand_endpoint_descriptor
                    ),
                },
                "canonical_ligand_atom_namespace": tuple(
                    {
                        "atom_id": atom_id,
                        "atom_map_number": map_by_atom[atom_id],
                        "element": next(
                            row[1] for row in candidate.ligand_atom_coordinates
                            if row[0] == atom_id
                        ),
                    }
                    for atom_id in candidate.retained_heavy_atoms
                ),
                "observed_post_distance_angstrom": candidate.post_distance_angstrom,
                "post_endpoint_coordinates": {
                    "ligand": next(
                        row for row in candidate.ligand_atom_coordinates
                        if row[0] == candidate.reactive_ligand_atom_id
                    ),
                    "protein": next(
                        row for row in candidate.pocket_atom_coordinates
                        if row[0] == candidate.protein_endpoint_atom_id
                    ),
                },
                "pre_reaction_graph_authoritative": (
                    candidate.pre_reaction_graph_authoritative
                ),
                "formal_charge_authoritative": candidate.formal_charge_authoritative,
                "available_pre_reaction_bond_orders": machine_pre_bonds,
                "available_formal_charge_pattern": machine_charges,
                "existing_role_warhead_proposal": proposal,
                "leakage_evidence": {
                    "machine_derived": candidate.baseline_leakage_evidence_complete,
                    "ligand_graph_scope": (
                        "PUBLISHED_RETAINED_COMPONENT_TOPOLOGY_FOR_LEAKAGE_ONLY_NOT_PRE_CHEMISTRY"
                        if identity == "2DJF/1ZB"
                        else "HUMAN_APPROVED_PRE_REACTION_GRAPH"
                    ),
                    "policy": (
                        "conservative_union_of_ligand_graph_scaffold_and_"
                        "protein_accession_sequence_clusters_v1"
                    ),
                    "ligand_graph_sha256": candidate.leakage_ligand_graph_sha256,
                    "ligand_scaffold_sha256": candidate.leakage_ligand_scaffold_sha256,
                    "protein_accession": candidate.leakage_protein_accession,
                    "protein_sequence_sha256": candidate.leakage_protein_sequence_sha256,
                    "leakage_key": candidate.leakage_key,
                },
                "source_evidence_bindings": candidate.machine_evidence_bindings,
                "candidate_warnings": tuple(dict.fromkeys(warnings)),
            },
            "review_status": "",
            "review_scope": "",
            "independent_sample_assignment_decision": "",
            "reaction_family_authority_action": "",
            "reaction_family_id": "",
            "reaction_family_version": "",
            "warhead_rule_authority_action": "",
            "warhead_rule_id": "",
            "warhead_rule_version": "",
            "approved_warhead_smarts": "",
            "ligand_reactive_atom_map_number": map_by_atom[candidate.reactive_ligand_atom_id],
            "warhead_atom_map_numbers": [],
            "expected_pre_reaction_bond_orders": machine_pre_bonds,
            "allowed_formal_charge_pattern": machine_charges,
            "reviewed_warhead_atom_ids": [],
            "reviewed_warhead_attachment_atom_id": None,
            "reviewed_nonwarhead_boundary_atom_id": None,
            "reviewed_attachment_boundary_bond_order": "",
            "reviewed_scaffold_atom_ids": [],
            "reviewed_linker_atom_ids": [],
            "reviewed_warhead_role_atom_ids": [],
            "reviewed_minimal_seed_atom_ids": [],
            "reviewed_scaffold_linker_boundary_bond": [],
            "reviewed_linker_warhead_boundary_bond": [],
            "primary_anchor_atom": None,
            "direction_anchor_atom": None,
            "optional_plane_anchor_atom": None,
            "role_profile": "",
            "role_rule_id": "",
            "role_rule_version": "",
            "reviewer_id": "",
            "review_rationale": "",
            "review_notes": "",
        })
    return _canonical_json({
        "schema_version": REVIEW_TEMPLATE_V2_SCHEMA,
        "pipeline_version": PIPELINE_VERSION,
        "template_status": "BLANK_HUMAN_DECISIONS_NOT_APPROVAL",
        "approval_records": records,
    })


def write_real_exact4_human_review_decision_template_v2(
    repo_root: Path,
) -> Path:
    destination = repo_root / REVIEW_TEMPLATE_V2_RELATIVE
    payload = build_real_exact4_human_review_decision_template_v2(repo_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != payload:
            raise ValueError("EXISTING_REAL_EXACT4_TEMPLATE_V2_BYTES_DIFFER")
        return destination
    temporary = destination.with_name(destination.name + ".tmp")
    if temporary.exists():
        raise ValueError("PREEXISTING_REAL_EXACT4_TEMPLATE_V2_TEMPORARY_PRESENT")
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination


def serialize_candidate_batch_v1(
    candidates: Sequence[ExpansionCandidateV1],
) -> bytes:
    records = []
    for candidate in candidates:
        record = asdict(candidate)
        record["source_path"] = str(candidate.source_path)
        records.append(record)
    return _canonical_json({
        "schema_version": "covapie_cys_sg_expansion_candidate_batch_v1",
        "candidates": records,
    })


def load_candidate_batch_v1(path: Path) -> tuple[ExpansionCandidateV1, ...]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("EXPANSION_CANDIDATE_BATCH_UNREADABLE") from error
    if (
        type(parsed) is not dict
        or set(parsed) != {"schema_version", "candidates"}
        or parsed["schema_version"] != "covapie_cys_sg_expansion_candidate_batch_v1"
        or type(parsed["candidates"]) is not list
    ):
        raise ValueError("EXPANSION_CANDIDATE_BATCH_SCHEMA_INVALID")
    expected = {item.name for item in fields(ExpansionCandidateV1)}
    tuple_fields = {
        "atom_symbols", "smarts_atom_ids", "retained_heavy_atoms",
        "scaffold_atoms", "linker_atoms", "warhead_atoms",
        "explicit_graph_bonds", "seed_atoms", "prior_blocking_reasons",
        "atom_map_numbers", "atom_formal_charges", "pre_reaction_bonds",
        "ligand_atom_coordinates", "pocket_atom_coordinates",
        "machine_evidence_bindings", "leakage_axis_keys",
        "leakage_baseline_group_ids",
    }
    records: list[ExpansionCandidateV1] = []
    for raw in parsed["candidates"]:
        if type(raw) is not dict or set(raw) != expected:
            raise ValueError("EXPANSION_CANDIDATE_RECORD_SCHEMA_INVALID")
        value = dict(raw)
        if type(value["source_path"]) is not str or not Path(value["source_path"]).is_absolute():
            raise ValueError("EXPANSION_CANDIDATE_SOURCE_PATH_INVALID")
        value["source_path"] = Path(value["source_path"])
        for field_name in tuple_fields:
            if type(value[field_name]) is not list:
                raise ValueError(f"EXPANSION_CANDIDATE_{field_name.upper()}_INVALID")
            value[field_name] = tuple(
                tuple(item) if type(item) is list else item for item in value[field_name]
            )
        records.append(ExpansionCandidateV1(**value))
    return tuple(records)


def tensorize_approved_expansion_sample_v1(
    candidate: ExpansionCandidateV1,
) -> Mapping[str, Any]:
    """Actually construct bounded expansion tensors without model execution."""

    import torch

    ligand_by_id = {row[0]: row for row in candidate.ligand_atom_coordinates}
    if len(ligand_by_id) != len(candidate.ligand_atom_coordinates):
        raise ValueError("TENSORIZATION_LIGAND_COORDINATE_ID_DUPLICATE")
    if set(ligand_by_id) != set(candidate.retained_heavy_atoms):
        raise ValueError("TENSORIZATION_LIGAND_COORDINATE_COVERAGE_INVALID")
    if not candidate.pocket_atom_coordinates:
        raise ValueError("TENSORIZATION_POCKET_COORDINATES_EMPTY")
    ligand_rows = tuple(ligand_by_id[item] for item in candidate.retained_heavy_atoms)
    pocket_rows = candidate.pocket_atom_coordinates
    ligand_projection = feature_semantics_owner.project_type_symbols_to_checkpoint_heavy_v1(
        tuple(row[1] for row in ligand_rows)
    )
    pocket_projection = feature_semantics_owner.project_type_symbols_to_checkpoint_heavy_v1(
        tuple(row[1] for row in pocket_rows)
    )
    if ligand_projection.sample_rejected or pocket_projection.sample_rejected:
        raise ValueError("TENSORIZATION_FEATURE_PROJECTION_REJECTED")
    if not all(ligand_projection.keep_mask) or not all(pocket_projection.keep_mask):
        raise ValueError("TENSORIZATION_EXPLICIT_H_COORDINATE_ROWS_FORBIDDEN")
    ligand_coordinates = torch.tensor(
        tuple(tuple(float(value) for value in row[2:]) for row in ligand_rows),
        dtype=torch.float32,
    )
    pocket_coordinates = torch.tensor(
        tuple(tuple(float(value) for value in row[2:]) for row in pocket_rows),
        dtype=torch.float32,
    )
    if ligand_coordinates.ndim != 2 or ligand_coordinates.shape[1] != 3:
        raise ValueError("TENSORIZATION_LIGAND_COORDINATE_SHAPE_INVALID")
    if pocket_coordinates.ndim != 2 or pocket_coordinates.shape[1] != 3:
        raise ValueError("TENSORIZATION_POCKET_COORDINATE_SHAPE_INVALID")
    joint_centroid = torch.cat((ligand_coordinates, pocket_coordinates), dim=0).mean(dim=0)
    ligand_coordinates = ligand_coordinates - joint_centroid
    pocket_coordinates = pocket_coordinates - joint_centroid
    ligand_channels = torch.tensor(
        ligand_projection.checkpoint_channel_indices, dtype=torch.long,
    )
    pocket_channels = torch.tensor(
        pocket_projection.checkpoint_channel_indices, dtype=torch.long,
    )
    ligand_one_hot = torch.nn.functional.one_hot(ligand_channels, num_classes=10).to(torch.float32)
    pocket_one_hot = torch.nn.functional.one_hot(pocket_channels, num_classes=10).to(torch.float32)
    scaffold, linker, warhead = set(candidate.scaffold_atoms), set(candidate.linker_atoms), set(candidate.warhead_atoms)
    role_ids = torch.tensor(tuple(
        0 if item in scaffold else 1 if item in linker else 2 if item in warhead else -1
        for item in candidate.retained_heavy_atoms
    ), dtype=torch.long)
    if bool(torch.any(role_ids < 0)):
        raise ValueError("TENSORIZATION_ROLE_PARTITION_NOT_EXHAUSTIVE")
    task_masks = torch.stack((
        role_ids == 2,
        (role_ids == 1) | (role_ids == 2),
        (role_ids == 0) | (role_ids == 2),
        role_ids == 0,
        torch.ones_like(role_ids, dtype=torch.bool),
    ))
    ligand_endpoint_index = candidate.retained_heavy_atoms.index(candidate.reactive_ligand_atom_id)
    pocket_ids = tuple(row[0] for row in pocket_rows)
    if pocket_ids.count(candidate.protein_endpoint_atom_id) != 1:
        raise ValueError("TENSORIZATION_PROTEIN_ENDPOINT_INDEX_INVALID")
    pocket_endpoint_index = pocket_ids.index(candidate.protein_endpoint_atom_id)
    post_valid, post_reasons, recomputed = validate_post_geometry_authority_v1(candidate)
    if not post_valid or recomputed is None:
        raise ValueError("TENSORIZATION_POST_AUTHORITY_INVALID:" + ";".join(post_reasons))
    geometry_values = torch.tensor((0.0, recomputed), dtype=torch.float32)
    geometry_mask = torch.tensor((False, True), dtype=torch.bool)
    return {
        "schema_version": TENSORIZATION_SCHEMA_V1,
        "sample_identity": candidate.candidate_identity,
        "role_profile": candidate.role_profile,
        "checkpoint_channel_order": feature_semantics_owner.CHECKPOINT_CHANNEL_ORDER,
        "ligand_coordinates_centered": ligand_coordinates.tolist(),
        "pocket_coordinates_centered": pocket_coordinates.tolist(),
        "ligand_one_hot_10d": ligand_one_hot.tolist(),
        "pocket_one_hot_10d": pocket_one_hot.tolist(),
        "role_ids": role_ids.tolist(),
        "canonical_task_masks": task_masks.tolist(),
        "canonical_task_names": tuple(name for name, _alias in feature_semantics_owner.CANONICAL_MASKS),
        "positive_reactive_pair_indices": (ligand_endpoint_index, pocket_endpoint_index),
        "geometry_component_values_angstrom": geometry_values.tolist(),
        "geometry_component_authority_mask": geometry_mask.tolist(),
        "pre_geometry_authority": False,
        "pre_geometry_masked": True,
        "post_geometry_authority": True,
        "tensorization_performed": True,
    }


def tensorize_covapie_expanded_population_successor_v1(
    *,
    sample_identity: str,
    approved_expansion_candidate: ExpansionCandidateV1 | None = None,
    historical_tensorizer_kwargs: Mapping[str, Any] | None = None,
) -> Any:
    """Add expansion identities while preserving the historical Exact16 owner."""

    from covalent_ext import (
        covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as historical_owner,
    )

    historical_identities = frozenset((
        *historical_owner.CURRENT11_MEMBER_IDENTITIES_V1,
        *historical_owner.K36_MEMBER_IDENTITIES_V1,
    ))
    if sample_identity in historical_identities:
        if approved_expansion_candidate is not None or type(historical_tensorizer_kwargs) is not dict:
            raise ValueError("HISTORICAL_EXACT16_TENSORIZER_INPUT_INVALID")
        return historical_owner.tensorize_covapie_expanded_cys_sg_sample_v1(
            sample_identity=sample_identity, **historical_tensorizer_kwargs,
        )
    if (
        type(approved_expansion_candidate) is not ExpansionCandidateV1
        or approved_expansion_candidate.candidate_identity != sample_identity
        or historical_tensorizer_kwargs is not None
    ):
        raise ValueError("APPROVED_EXPANSION_TENSORIZER_INPUT_INVALID")
    return tensorize_approved_expansion_sample_v1(approved_expansion_candidate)


def _materialized_sample_payload_v1(
    candidate: ExpansionCandidateV1,
    outcome: CandidateOutcomeV1,
) -> bytes:
    return _canonical_json({
        "schema_version": MATERIALIZATION_SCHEMA_V1,
        "candidate_identity": candidate.candidate_identity,
        "source_identity": candidate.source_identity,
        "source_sha256": candidate.expected_source_sha256,
        "chemistry_signature_sha256": candidate.chemistry_signature_sha256,
        "chemistry_authority_id": outcome.chemistry_authority_id,
        "admitted_by": outcome.admitted_by,
        "human_sample_decision_consumed": outcome.human_sample_decision_consumed,
        "role_profile": candidate.role_profile,
        "leakage_group_id": outcome.leakage_group_id,
        "assigned_split": outcome.assigned_split,
        "post_geometry_authority": outcome.post_geometry_authority,
        "pre_geometry_authority": False,
        "pre_geometry_masked": True,
        "materialization_performed": True,
    })


def _validated_materialization_root_v1(output_root: Path) -> Path:
    if type(output_root) is not type(Path()) or not output_root.is_absolute():
        raise ValueError("MATERIALIZATION_OUTPUT_ROOT_MUST_BE_ABSOLUTE_PATH")
    repo_root = Path(__file__).resolve().parents[2]
    resolved_parent = output_root.parent.resolve()
    if output_root.name in {"", ".", ".."}:
        raise ValueError("MATERIALIZATION_OUTPUT_ROOT_INVALID")
    candidate = resolved_parent / output_root.name
    protected = (
        repo_root / "data/raw", repo_root / "checkpoints",
        repo_root.parent / "covapie-state",
    )
    if any(candidate == item or candidate.is_relative_to(item) for item in protected):
        raise ValueError("MATERIALIZATION_OUTPUT_ROOT_PROTECTED")
    if candidate.is_relative_to(repo_root):
        allowed = repo_root / "data/derived/covalent_small" / PIPELINE_VERSION
        if candidate != allowed and not candidate.is_relative_to(allowed):
            raise ValueError("MATERIALIZATION_REPOSITORY_OUTPUT_NOT_TASK_OWNED")
    return candidate


def _portable_prior_cumulative_provenance_v1(
    registry: CumulativeExpansionLeakageRegistryV1,
    *,
    prior_registry_path: Path | None,
    repo_root: Path,
) -> tuple[CumulativeLeakageSourceArtifactV1, ...]:
    portable: list[CumulativeLeakageSourceArtifactV1] = []
    for artifact in registry.source_artifacts:
        if artifact.path_scope == "REPOSITORY_ROOT_RELATIVE":
            portable.append(artifact)
            continue
        if prior_registry_path is None:
            raise ValueError(
                "CUMULATIVE_LEAKAGE_PRIOR_REGISTRY_PATH_REQUIRED_FOR_PROVENANCE"
            )
        resolved = (prior_registry_path.resolve().parent / artifact.path).resolve()
        if not resolved.is_relative_to(repo_root):
            raise ValueError(
                "CUMULATIVE_LEAKAGE_SUCCESSOR_PROVENANCE_NOT_PORTABLE"
            )
        portable.append(replace(
            artifact,
            path=resolved.relative_to(repo_root).as_posix(),
            path_scope="REPOSITORY_ROOT_RELATIVE",
        ))
    return tuple(portable)


def build_successor_cumulative_expansion_leakage_registry_v1(
    prior_registry: CumulativeExpansionLeakageRegistryV1,
    *,
    completed_outcomes: Sequence[CandidateOutcomeV1],
    effective_candidates: Mapping[str, ExpansionCandidateV1],
    current_source_artifacts: Sequence[CumulativeLeakageSourceArtifactV1],
    prior_registry_path: Path | None = None,
) -> CumulativeExpansionLeakageRegistryV1:
    prior = _validated_cumulative_expansion_leakage_registry_v1(prior_registry)
    repo_root = Path(__file__).resolve().parents[2]
    groups = {group.leakage_key: group for group in prior.groups}
    group_id_to_key = {
        group.final_leakage_group_id: group.leakage_key for group in prior.groups
    }
    member_to_key = {
        identity: group.leakage_key
        for group in prior.groups
        for identity in group.member_identities
    }
    for outcome in completed_outcomes:
        if not outcome.materialization_performed:
            continue
        candidate = effective_candidates.get(outcome.candidate_identity)
        if candidate is None or not candidate.leakage_key:
            raise ValueError("CUMULATIVE_LEAKAGE_SUCCESSOR_CANDIDATE_MISSING")
        registered_key = member_to_key.get(candidate.candidate_identity)
        if registered_key is not None and registered_key != candidate.leakage_key:
            raise ValueError("CUMULATIVE_LEAKAGE_SUCCESSOR_MEMBER_GROUP_CONFLICT")
        group = groups.get(candidate.leakage_key)
        if group is not None:
            if (
                group.final_leakage_group_id != outcome.leakage_group_id
                or group.assigned_split != outcome.assigned_split
            ):
                raise ValueError("CUMULATIVE_LEAKAGE_SUCCESSOR_GROUP_SPLIT_CONFLICT")
            members = tuple(sorted({
                *group.member_identities, candidate.candidate_identity,
            }))
            groups[candidate.leakage_key] = replace(
                group, member_identities=members, member_count=len(members),
            )
        else:
            prior_key = group_id_to_key.get(outcome.leakage_group_id)
            if prior_key is not None and prior_key != candidate.leakage_key:
                raise ValueError("CUMULATIVE_LEAKAGE_SUCCESSOR_GROUP_ID_CONFLICT")
            groups[candidate.leakage_key] = CumulativeExpansionLeakageGroupV1(
                leakage_key=candidate.leakage_key,
                final_leakage_group_id=outcome.leakage_group_id,
                assigned_split=outcome.assigned_split,
                member_identities=(candidate.candidate_identity,),
                member_count=1,
            )
            group_id_to_key[outcome.leakage_group_id] = candidate.leakage_key
        member_to_key[candidate.candidate_identity] = candidate.leakage_key
    if not any(item.materialization_performed for item in completed_outcomes):
        raise ValueError("CUMULATIVE_LEAKAGE_SUCCESSOR_HAS_NO_MATERIALIZED_MEMBER")
    artifacts = (
        *_portable_prior_cumulative_provenance_v1(
            prior,
            prior_registry_path=prior_registry_path,
            repo_root=repo_root,
        ),
        *current_source_artifacts,
    )
    return _validated_cumulative_expansion_leakage_registry_v1(
        CumulativeExpansionLeakageRegistryV1(
            schema_version=CUMULATIVE_EXPANSION_LEAKAGE_REGISTRY_SCHEMA_V1,
            policy_id=CUMULATIVE_EXPANSION_LEAKAGE_POLICY_ID_V1,
            source_artifacts=tuple(artifacts),
            groups=tuple(groups.values()),
        )
    )


def materialize_approved_successor_v1(
    output_root: Path,
    run: PipelineRunV1,
    effective_candidates: Mapping[str, ExpansionCandidateV1],
    authorities: Sequence[ReusableChemistryAuthorityV1],
    cumulative_leakage_registry: (
        CumulativeExpansionLeakageRegistryV1 | None
    ) = None,
    cumulative_leakage_registry_source_path: Path | None = None,
) -> PipelineRunV1:
    output_root = _validated_materialization_root_v1(output_root)
    admitted = [item for item in run.outcomes if item.materialization_ready]
    if not admitted:
        raise ValueError("NO_APPROVED_SAMPLES_TO_MATERIALIZE")
    expected_files: dict[str, bytes] = {}
    updated: list[CandidateOutcomeV1] = []
    for outcome in run.outcomes:
        if not outcome.materialization_ready:
            updated.append(outcome)
            continue
        candidate = effective_candidates[outcome.candidate_identity]
        materialized = _materialized_sample_payload_v1(candidate, outcome)
        tensorized = _canonical_json(tensorize_covapie_expanded_population_successor_v1(
            sample_identity=candidate.candidate_identity,
            approved_expansion_candidate=candidate,
        ))
        token = _sha256(outcome.candidate_identity.encode("utf-8"))[:16]
        expected_files[f"samples/{token}.materialized.json"] = materialized
        expected_files[f"samples/{token}.tensorized.json"] = tensorized
        updated.append(replace(
            outcome,
            materialization_performed=True,
            tensorization_performed=True,
            materialization_artifact_sha256=_sha256(materialized),
            tensorization_artifact_sha256=_sha256(tensorized),
        ))
    registry_payload = serialize_reusable_authority_registry_v1(authorities)
    completed = replace(
        run, outcomes=tuple(updated),
        reusable_authority_registry_sha256=_sha256(registry_payload),
    )
    pipeline_payload = serialize_pipeline_run_v1(completed)
    expected_files["reusable_authority_registry_v1.json"] = registry_payload
    expected_files["pipeline_run_v1.json"] = pipeline_payload
    if cumulative_leakage_registry is not None:
        current_sources = [CumulativeLeakageSourceArtifactV1(
            artifact_role="SUCCESSOR_EXPANSION_PIPELINE_RUN",
            path="pipeline_run_v1.json",
            path_scope="REGISTRY_DIRECTORY_RELATIVE",
            sha256=_sha256(pipeline_payload),
        )]
        for outcome in completed.outcomes:
            if not outcome.materialization_performed:
                continue
            token = _sha256(outcome.candidate_identity.encode("utf-8"))[:16]
            relative = f"samples/{token}.materialized.json"
            current_sources.append(CumulativeLeakageSourceArtifactV1(
                artifact_role="SUCCESSOR_EXPANSION_MATERIALIZED_SAMPLE",
                path=relative,
                path_scope="REGISTRY_DIRECTORY_RELATIVE",
                sha256=_sha256(expected_files[relative]),
            ))
        successor_registry = (
            build_successor_cumulative_expansion_leakage_registry_v1(
                cumulative_leakage_registry,
                completed_outcomes=completed.outcomes,
                effective_candidates=effective_candidates,
                current_source_artifacts=tuple(current_sources),
                prior_registry_path=cumulative_leakage_registry_source_path,
            )
        )
        expected_files[CUMULATIVE_EXPANSION_LEAKAGE_REGISTRY_FILENAME_V1] = (
            serialize_cumulative_expansion_leakage_registry_v1(
                successor_registry
            )
        )
    if output_root.exists():
        if not output_root.is_dir() or output_root.is_symlink():
            raise ValueError("MATERIALIZATION_EXISTING_OUTPUT_INVALID")
        actual = {
            path.relative_to(output_root).as_posix(): path.read_bytes()
            for path in output_root.rglob("*") if path.is_file() and not path.is_symlink()
        }
        if actual != expected_files:
            raise ValueError("EXISTING_MATERIALIZATION_BYTES_DIFFER")
        return completed
    output_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_root.with_name(output_root.name + ".tmp")
    if temporary.exists():
        raise ValueError("PREEXISTING_MATERIALIZATION_TEMPORARY_PRESENT")
    try:
        temporary.mkdir()
        for relative, payload in sorted(expected_files.items()):
            destination = temporary / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
        os.replace(temporary, output_root)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return completed


def _aggregate_v1(outcomes: Sequence[CandidateOutcomeV1]) -> dict[str, int]:
    missing_statuses = {MISSING_SOURCE, SOURCE_SHA_MISMATCH}
    rejected_statuses = {
        REJECTED, LEAKAGE_CONFLICT, PIPELINE_INPUT_INVALID,
        POST_AUTHORITY_INVALID,
    }
    return {
        "candidate_count": len(outcomes),
        "source_verified_count": sum(item.source_verified for item in outcomes),
        "mechanically_eligible_count": sum(item.mechanically_eligible for item in outcomes),
        "auto_admitted_count": sum(item.terminal_disposition == AUTO_ADMITTED for item in outcomes),
        "human_review_required_count": sum(item.terminal_disposition == HUMAN_REQUIRED for item in outcomes),
        "runtime_extension_required_count": sum(item.terminal_disposition == RUNTIME_EXTENSION for item in outcomes),
        "missing_source_authority_count": sum(item.terminal_disposition in missing_statuses for item in outcomes),
        "rejected_count": sum(item.terminal_disposition in rejected_statuses for item in outcomes),
        "materialization_ready_count": sum(item.materialization_ready for item in outcomes),
    }


def run_covapie_cys_sg_dataset_expansion_pipeline_v1(
    candidates: Sequence[ExpansionCandidateV1],
    *,
    reusable_authorities: Sequence[ReusableChemistryAuthorityV1] = (),
    approval_records: Mapping[str, Mapping[str, Any]] | None = None,
    execution_mode: str = REVIEW_ONLY,
    output_root: Path | None = None,
    leakage_groups: Sequence[LeakageGroupAssignmentV1] | None = None,
    cumulative_leakage_registry: (
        CumulativeExpansionLeakageRegistryV1 | None
    ) = None,
    cumulative_leakage_registry_source_path: Path | None = None,
) -> PipelineRunV1:
    if execution_mode not in {REVIEW_ONLY, MATERIALIZE_APPROVED}:
        raise ValueError("PIPELINE_EXECUTION_MODE_INVALID")
    if execution_mode == REVIEW_ONLY and output_root is not None:
        raise ValueError("REVIEW_ONLY_MODE_FORBIDS_MATERIALIZATION_OUTPUT_ROOT")
    if execution_mode == MATERIALIZE_APPROVED and output_root is None:
        raise ValueError("MATERIALIZE_APPROVED_MODE_REQUIRES_OUTPUT_ROOT")
    if leakage_groups is not None and cumulative_leakage_registry is not None:
        raise ValueError(
            "EXPLICIT_LEAKAGE_GROUPS_AND_CUMULATIVE_REGISTRY_MUTUALLY_EXCLUSIVE"
        )
    if (
        cumulative_leakage_registry_source_path is not None
        and cumulative_leakage_registry is None
    ):
        raise ValueError("CUMULATIVE_LEAKAGE_REGISTRY_SOURCE_WITHOUT_REGISTRY")
    if (
        cumulative_leakage_registry is not None
        and cumulative_leakage_registry_source_path is None
    ):
        raise ValueError("CUMULATIVE_LEAKAGE_REGISTRY_SOURCE_PATH_REQUIRED")
    if cumulative_leakage_registry is not None:
        assert cumulative_leakage_registry_source_path is not None
        source_registry = load_cumulative_expansion_leakage_registry_v1(
            cumulative_leakage_registry_source_path,
            repo_root=Path(__file__).resolve().parents[2],
        )
        if source_registry != _validated_cumulative_expansion_leakage_registry_v1(
            cumulative_leakage_registry
        ):
            raise ValueError("CUMULATIVE_LEAKAGE_REGISTRY_SOURCE_CONTENT_MISMATCH")
    if type(candidates) not in (list, tuple):
        raise ValueError("CANDIDATE_BATCH_CONTAINER_INVALID")
    approvals = dict(approval_records or {})
    identity_counts: dict[str, int] = {}
    for candidate in candidates:
        identity_counts[candidate.candidate_identity] = (
            identity_counts.get(candidate.candidate_identity, 0) + 1
        )
    unknown_approvals = sorted(set(approvals) - set(identity_counts))
    if unknown_approvals:
        raise ValueError("APPROVAL_RECORD_CANDIDATE_NOT_IN_BATCH:" + ";".join(unknown_approvals))
    effective_authorities = list(_validated_authority_registry_v1(reusable_authorities))
    approval_validations: dict[str, tuple[
        ExpansionCandidateV1 | None,
        ReusableChemistryAuthorityV1 | None,
        tuple[str, ...],
    ]] = {}
    effective_candidates: dict[str, ExpansionCandidateV1] = {
        candidate.candidate_identity: candidate for candidate in candidates
    }
    for candidate in sorted(candidates, key=lambda item: item.candidate_identity):
        record = approvals.get(candidate.candidate_identity)
        if record is None:
            continue
        pre_reasons: list[str] = []
        if identity_counts[candidate.candidate_identity] != 1:
            pre_reasons.append("APPROVAL_CANDIDATE_IDENTITY_DUPLICATE_IN_BATCH")
        if verify_existing_source_v1(candidate.source_path, candidate.expected_source_sha256) != "SOURCE_ALREADY_PRESENT_AND_VERIFIED":
            pre_reasons.append("APPROVAL_SOURCE_NOT_PRESENT_AND_VERIFIED")
        if candidate.prior_disposition or _mechanical_eligibility_reasons_v1(candidate):
            pre_reasons.append("APPROVAL_CANDIDATE_MECHANICALLY_INELIGIBLE")
        if pre_reasons:
            approval_validations[candidate.candidate_identity] = (
                None, None, tuple(pre_reasons),
            )
            continue
        validation = _approval_effective_candidate_and_authority_v1(
            candidate, record, tuple(effective_authorities)
        )
        effective, new_authority, validation_reasons = validation
        if not validation_reasons and effective is not None and new_authority is not None:
            effective_candidates[candidate.candidate_identity] = effective
            if new_authority.approval_scope == "EXACT_CHEMISTRY_SIGNATURE_REUSABLE":
                same_identity = [
                    item for item in effective_authorities
                    if (item.authority_id, item.authority_version)
                    == (new_authority.authority_id, new_authority.authority_version)
                ]
                if same_identity and same_identity[0] != new_authority:
                    validation_reasons = ("REUSABLE_AUTHORITY_REGISTRY_CONFLICT",)
                    validation = (None, None, validation_reasons)
                elif not same_identity:
                    effective_authorities.append(new_authority)
        approval_validations[candidate.candidate_identity] = validation
    effective_authorities = list(_validated_authority_registry_v1(tuple(effective_authorities)))

    potentially_admitted: list[ExpansionCandidateV1] = []
    for candidate in sorted(candidates, key=lambda item: item.candidate_identity):
        effective = effective_candidates[candidate.candidate_identity]
        validation = approval_validations.get(candidate.candidate_identity)
        authority: ReusableChemistryAuthorityV1 | None = None
        human = validation is not None
        if validation is not None:
            if validation[2] or validation[0] is None or validation[1] is None:
                continue
            effective, authority = validation[0], validation[1]
        else:
            matches = [
                item for item in effective_authorities
                if item.chemistry_signature_sha256 == effective.chemistry_signature_sha256
                and not _authority_schema_reasons_v1(item)
            ]
            if len(matches) != 1 or effective.chemistry_signature_authoritative is not True:
                continue
            authority = matches[0]
        if (
            authority is not None
            and not _mechanical_eligibility_reasons_v1(effective)
            and verify_existing_source_v1(effective.source_path, effective.expected_source_sha256)
            == "SOURCE_ALREADY_PRESENT_AND_VERIFIED"
            and not effective.prior_disposition
            and not _candidate_authority_qa_reasons_v1(
                effective, authority,
                allow_sample_bound_human_approval=(
                    human and authority.approval_scope == "SAMPLE_BOUND_ONLY"
                ),
            )
        ):
            potentially_admitted.append(effective)
    if leakage_groups is not None:
        groups = tuple(leakage_groups)
    else:
        published_groups = load_published_leakage_group_population_v1(
            Path(__file__).resolve().parents[2]
        )
        groups = (
            merge_published_and_cumulative_leakage_groups_v1(
                published_groups, cumulative_leakage_registry,
            )
            if cumulative_leakage_registry is not None
            else published_groups
        )
    split_assignments = (
        assign_expansion_leakage_splits_v1(
            potentially_admitted, existing_groups=groups,
        ) if potentially_admitted else {}
    )
    outcomes: list[CandidateOutcomeV1] = []
    bindings: list[Mapping[str, Any]] = []
    for candidate in sorted(candidates, key=lambda item: item.candidate_identity):
        candidate_local = (
            replace(candidate, duplicate_identity=True)
            if identity_counts[candidate.candidate_identity] != 1 else candidate
        )
        try:
            outcome, binding = _evaluate_candidate_v1(
                candidate_local,
                tuple(effective_authorities),
                approval_validations.get(candidate.candidate_identity),
                split_assignments,
            )
        except Exception as error:
            phases = _empty_phase_statuses_v1()
            phases[PHASES[0]] = "CANDIDATE_LOCAL_EXCEPTION_FAILED_CLOSED"
            outcome = _outcome_v1(
                candidate_local,
                disposition=PIPELINE_INPUT_INVALID,
                reasons=(f"{type(error).__name__}:{error}",),
                phases=phases,
                source_verified=False,
            )
            binding = None
        outcomes.append(outcome)
        if binding is not None:
            bindings.append(binding)
    aggregate = _aggregate_v1(outcomes)
    if (
        aggregate["auto_admitted_count"]
        + aggregate["human_review_required_count"]
        + aggregate["runtime_extension_required_count"]
        + aggregate["missing_source_authority_count"]
        + aggregate["rejected_count"]
        + sum(item.terminal_disposition == HUMAN_APPROVED for item in outcomes)
        != aggregate["candidate_count"]
    ):
        raise ValueError("TERMINAL_DISPOSITION_COUNTS_DO_NOT_PARTITION_BATCH")
    run = PipelineRunV1(
        pipeline_version=PIPELINE_VERSION,
        successor_policy_id=SUCCESSOR_POLICY_ID,
        execution_mode=execution_mode,
        dry_run=execution_mode == REVIEW_ONLY,
        current_policy_requires_every_new_sample_human_assignment=(
            CURRENT_POLICY_REQUIRES_EVERY_NEW_SAMPLE_HUMAN_ASSIGNMENT
        ),
        outcomes=tuple(outcomes),
        aggregate=aggregate,
        authority_bindings=tuple(
            sorted(bindings, key=lambda item: str(item["authority_id"]))
        ),
        automation_coverage=automation_coverage_v1(),
        review_queue_identities=tuple(
            item.candidate_identity for item in outcomes
            if item.terminal_disposition == HUMAN_REQUIRED
        ),
        admitted_identities=tuple(
            item.candidate_identity for item in outcomes
            if item.materialization_ready
        ),
        reusable_authority_registry_sha256=_sha256(
            serialize_reusable_authority_registry_v1(tuple(effective_authorities))
        ),
    )
    if execution_mode == MATERIALIZE_APPROVED:
        assert output_root is not None
        return materialize_approved_successor_v1(
            output_root, run, effective_candidates, tuple(effective_authorities),
            cumulative_leakage_registry=cumulative_leakage_registry,
            cumulative_leakage_registry_source_path=(
                cumulative_leakage_registry_source_path
            ),
        )
    return run


def run_current_non_exact16_replay_v1(
    repo_root: Path,
    *,
    approval_records: Mapping[str, Mapping[str, Any]] | None = None,
) -> PipelineRunV1:
    return run_covapie_cys_sg_dataset_expansion_pipeline_v1(
        load_current_non_exact16_candidates_v1(repo_root),
        reusable_authorities=(),
        approval_records=approval_records,
        execution_mode=REVIEW_ONLY,
    )


def serialize_pipeline_run_v1(run: PipelineRunV1) -> bytes:
    return _canonical_json(asdict(run))


def pipeline_output_sha256_v1(run: PipelineRunV1) -> str:
    return _sha256(serialize_pipeline_run_v1(run))


def atomic_write_review_only_report_v1(path: Path, run: PipelineRunV1) -> None:
    """Write only a non-authoritative dry-run report with atomic finalization."""

    if run.dry_run is not True:
        raise ValueError("ONLY_DRY_RUN_REPORT_MAY_BE_WRITTEN")
    forbidden_parts = {"data/raw", "covapie-state", "checkpoints"}
    normalized = path.as_posix()
    if any(part in normalized for part in forbidden_parts):
        raise ValueError("REVIEW_REPORT_PATH_PROTECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise ValueError("PREEXISTING_TEMPORARY_REPORT_PRESENT")
    try:
        temporary.write_bytes(serialize_pipeline_run_v1(run))
        if path.exists():
            if path.read_bytes() == temporary.read_bytes():
                temporary.unlink()
                return
            raise ValueError("EXISTING_REVIEW_REPORT_BYTES_DIFFER")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
