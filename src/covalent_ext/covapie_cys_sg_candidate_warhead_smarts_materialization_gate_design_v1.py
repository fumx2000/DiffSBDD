"""Design the CovaPIE Cys-SG candidate-warhead SMARTS materialization gate V1.

This metadata-only stage freezes contracts and reports evidence readiness.  It
does not create or parse SMARTS, decide a complete warhead atom set, perform
human review, approve a rule, assign ligand roles, create masks/tensors, change
models, or train.
"""

from __future__ import annotations

import ast
import csv
import dataclasses
import hashlib
import io
import json
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


BASE_COMMIT = "77e2d11135da4b3f07ee64411ad3c4634ba60693"
BASE_PARENT = "c0de1003ec1de9dd05e3c4204b458d1f3757d95d"
BASE_TREE = "ed9c6dc692dafe4ed69c528d4f1ea8a90bec4a6c"
BASE_SUBJECT = (
    "add CovaPIE Current11 Cys SG reaction family and warhead rule review "
    "packages v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Cys SG candidate warhead SMARTS materialization gate design v1"
)
SCHEMA_VERSION = (
    "covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION
REQUIRED_SMARTS_TOOLKIT = "rdkit"
REQUIRED_SMARTS_TOOLKIT_VERSION = "2022.03.2"

REVIEW_PACKAGE_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1.py"
)
REVIEW_PACKAGE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1"
)
REVIEW_PACKAGE_MANIFEST = REVIEW_PACKAGE_ROOT / (
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_"
    "manifest.json"
)
REVIEW_PACKAGE_INDEX = REVIEW_PACKAGE_ROOT / "covapie_review_package_index.csv"
CLASS_REVIEW_TEMPLATES = (
    REVIEW_PACKAGE_ROOT / "covapie_cys_sg_candidate_class_review_record_templates.csv"
)
SAMPLE_REVIEW_TEMPLATES = (
    REVIEW_PACKAGE_ROOT
    / "covapie_current11_sample_assignment_review_record_templates.csv"
)
REVIEW_GATE_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_gate_design_v1.py"
)
ASSIGNMENT_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1.py"
)
ASSIGNMENT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1"
)
ASSIGNMENT_AUTHORITY = (
    ASSIGNMENT_ROOT / "covapie_current11_cys_sg_candidate_assignment_authority.csv"
)
CLASS_VOCABULARY = (
    ASSIGNMENT_ROOT / "covapie_cys_sg_warhead_type_candidate_class_vocabulary.csv"
)
REGISTRY_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1"
)
FAMILY_REGISTRY = REGISTRY_ROOT / "covapie_cys_sg_reaction_family_registry.csv"
RULE_REGISTRY = REGISTRY_ROOT / "covapie_cys_sg_warhead_rule_registry.csv"
ROLE_CONTRACT_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
PARENT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_exact9_audited_local_ccd_parent_graph_authority_v1"
)
PARENT_ATOM_AUTHORITY = PARENT_ROOT / "covapie_exact9_parent_heavy_atom_authority.csv"
PARENT_BOND_AUTHORITY = PARENT_ROOT / "covapie_exact9_parent_heavy_bond_authority.csv"
ATOM_MAPPING_AUTHORITY = Path(
    "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1/"
    "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
)

FROZEN_BASE_SHA256 = {
    REVIEW_PACKAGE_SOURCE:
        "052be7badc65a7eaeec1568e5954a2141a29c08bd0ef85c203e758daaa8b78ec",
    REVIEW_PACKAGE_MANIFEST:
        "677034c0b8822e0b1476e28d00bb8dda5c8e53f5f42fcda790d9c4a81fa8a90b",
    REVIEW_PACKAGE_INDEX:
        "b62a9d884b08b3b5132f64ca33531497343f208925e3a64eadd7980eee0d341f",
    CLASS_REVIEW_TEMPLATES:
        "596e218d1d29e16d65edfa1c804b63a528668ffc4083d4089427eda556f37ce1",
    SAMPLE_REVIEW_TEMPLATES:
        "662e95d3403a694da15dedd60dbdb81f98a9e404533693643b3721cd83a18bc1",
    REVIEW_GATE_SOURCE:
        "08b7d7aeacfcd7065e6ea8aa2ae27b2cc4959d476fbb1568a5231307d7e308a1",
    ASSIGNMENT_SOURCE:
        "fe6c67940efef89290b2f276f9fb4c39245468181d52b219951a6f9ca7f454aa",
    ASSIGNMENT_AUTHORITY:
        "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    CLASS_VOCABULARY:
        "e78b83340d9df0afa6bbffd5dc56708ee47023680367f7a8acd9883e7c21602d",
    FAMILY_REGISTRY:
        "230dc6da03beee55e53df75cba887151c23b703e10dce18de4ff6304d05b6353",
    RULE_REGISTRY:
        "3311aaca925e29036b702822bd85fbaf4e2c3a02c9b7882d255956c65cd02309",
    ROLE_CONTRACT_SOURCE:
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
    PARENT_ATOM_AUTHORITY:
        "d50b052c2ed2573ccfdcf66470a077744ad11f4a083daee11f20d794b3b23fe7",
    PARENT_BOND_AUTHORITY:
        "26957b9f78217c808d2dc021cfab1a2bf78dd1708c46c49f220ae32a3a09ebbf",
    ATOM_MAPPING_AUTHORITY:
        "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
}
SOURCE_PATHS = tuple(FROZEN_BASE_SHA256)

SOURCE_FILE = "covapie_candidate_smarts_gate_source_inventory.csv"
CONTRACT_FILE = "covapie_candidate_warhead_smarts_contract_registry.csv"
READINESS_FILE = (
    "covapie_current7_candidate_warhead_smarts_materialization_readiness_matrix.csv"
)
GAP_FILE = "covapie_candidate_warhead_smarts_input_authority_gap_matrix.csv"
FAILURE_FILE = "covapie_candidate_warhead_smarts_materialization_gate_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_candidate_warhead_smarts_materialization_gate_design_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_FILE,
    CONTRACT_FILE,
    READINESS_FILE,
    GAP_FILE,
    FAILURE_FILE,
    MANIFEST_FILE,
)
EXACT10_PATHS = (
    Path(
        "src/covalent_ext/"
        "covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1.py"
    ),
    Path(
        "scripts/"
        "check_covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1.py"
    ),
    Path(
        "docs/"
        "covapie_cys_sg_candidate_warhead_smarts_materialization_gate_design_v1_summary.md"
    ),
    *(OUTPUT_ROOT / name for name in OUTPUT_FILES),
)

WARHEAD_RULE_FIELDS = (
    "reaction_family_id",
    "reaction_family_version",
    "target_residue_types",
    "target_residue_reactive_atom_name",
    "warhead_smarts",
    "ligand_reactive_atom_map_number",
    "warhead_atom_map_numbers",
    "warhead_attachment_atom_map_number",
    "expected_pre_reaction_bond_orders",
    "allowed_formal_charge_pattern",
    "allowed_match_count",
    "priority",
)
PROPOSAL_FIELDS = (
    "proposal_version",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "component_parent_graph_sha256",
    "ligand_reactive_parent_atom_id",
    "local_reaction_center_atom_ids",
    "local_reaction_center_bond_ids",
    "proposed_pre_reaction_warhead_atom_ids",
    "proposed_warhead_attachment_atom_id",
    "proposed_nonwarhead_boundary_atom_id",
    "proposed_attachment_boundary_bond_order",
    "required_leaving_group_atom_ids",
    "proposal_method",
    "proposal_status",
    "ambiguity_reasons",
    "source_assignment_record_sha256",
    "proposal_record_sha256",
)
PROPOSAL_STATUSES = (
    "not_materialized",
    "auto_exact_candidate",
    "ambiguous_candidate",
    "quarantined",
)
PROPOSAL_ATOM_ID_NAMESPACE = "parent_ccd_atom_id"
PROPOSAL_BOND_ID_ENCODING = (
    "canonical_parent_ccd_endpoint_pair_and_normalized_order_v1"
)
PARENT_NORMALIZED_BOND_ORDERS = ("aromatic", "double", "single")
PROPOSAL_FIELD_TYPE_CONTRACT = {
    field: (
        "exact_int"
        if field == "warhead_type_candidate_class_index_0based"
        else "exact_list_str"
        if field
        in {
            "local_reaction_center_atom_ids",
            "local_reaction_center_bond_ids",
            "proposed_pre_reaction_warhead_atom_ids",
            "required_leaving_group_atom_ids",
            "ambiguity_reasons",
        }
        else "exact_str"
    )
    for field in PROPOSAL_FIELDS
}
PROPOSAL_HASH_EXCLUDED_FIELD = "proposal_record_sha256"
PROPOSAL_HASH_CANONICAL_JSON_CONTRACT = {
    "sort_keys": True,
    "separators": [",", ":"],
    "ensure_ascii": True,
    "encoding": "UTF-8",
    "excluded_field": PROPOSAL_HASH_EXCLUDED_FIELD,
    "included_field_count": 21,
}

SOURCE_COLUMNS = (
    "source_path",
    "BASE_SHA256",
    "source_row_count",
    "Current11_coverage",
    "fields_actually_used",
    "authority_class",
    "provides_current_value",
    "verified",
)
CONTRACT_COLUMNS = (
    "contract_id",
    "semantic_name",
    "contract_scope",
    "required_inputs",
    "validation_rule",
    "success_effect",
    "failure_effect",
    "reason_code",
    "fails_closed",
    "verified",
)
READINESS_COLUMNS = (
    "warhead_type_candidate_class_index_0based",
    "warhead_type_candidate_class_id",
    "reaction_family_id",
    "warhead_rule_id",
    "canonical_local_graph_rule_sha256",
    "Current11_match_count",
    "Current11_unique_component_count",
    "supporting_sample_ids",
    "supporting_component_ids",
    "local_reaction_center_rule_available",
    "parent_heavy_atom_authority_available",
    "parent_heavy_bond_authority_available",
    "parent_graph_SHA_verified",
    "reactive_parent_atom_mapping_available",
    "pre_reaction_leaving_group_semantics_available",
    "complete_warhead_atom_set_available",
    "exact_one_attachment_boundary_available",
    "deterministic_atom_map_policy_available",
    "SMARTS_query_semantics_frozen",
    "class_wide_exact_one_match_validation_available",
    "candidate_warhead_smarts",
    "candidate_warhead_smarts_status",
    "candidate_warhead_smarts_materialized",
    "ready_for_warhead_atom_set_and_attachment_boundary_proposal_materialization",
    "ready_for_candidate_warhead_smarts_materialization",
    "ready_for_SMARTS_human_review",
    "approved_warhead_rule_available",
    "ready_for_role_proposal_generation",
    "ready_for_mask_materialization",
    "ready_for_model_integration",
    "ready_for_training",
    "blocking_reasons",
    "verified",
)
GAP_COLUMNS = (
    "warhead_type_candidate_class_id",
    "missing_authority",
    "current_evidence",
    "why_required",
    "would_block_atom_set_proposal",
    "would_block_SMARTS_materialization",
    "would_block_SMARTS_review",
    "resolution_owner",
    "recommended_resolution_step",
    "verified",
)
FAILURE_COLUMNS = (
    "failure_case",
    "mutation_signature",
    "mutated_field",
    "mutated_value_json",
    "expected_reason",
    "observed_reasons",
    "expected_reason_verified",
    "fails_closed",
    "contract_registry_row_count",
    "readiness_matrix_row_count",
    "authority_gap_row_count",
    "proposal_materialization_ready",
    "SMARTS_materialization_ready",
    "role_proposal_generation_ready",
    "mask_materialization_ready",
    "model_integration_ready",
    "training_ready",
    "verified",
)

CONTRACT_DEFINITIONS = (
    ("local reaction-center graph is not complete warhead", "evidence_boundary", "canonical_local_graph_rule_json", "treat radius-1 graph only as lower-bound reaction-center evidence", "complete-warhead proposal remains required", "block SMARTS materialization", "local_graph_not_complete_warhead"),
    ("pre-reaction parent graph is authoritative", "graph_authority", "parent atom and bond authorities", "derive ligand-side topology only from SHA-verified pre-reaction parent graph", "pre-reaction proposal input admitted", "block proposal and SMARTS materialization", "pre_reaction_parent_graph_unavailable"),
    ("known reactive atom must be included", "atom_set", "observed-to-parent reactive mapping", "complete warhead atom set contains the known reactive parent atom", "reactive atom inclusion verified", "block SMARTS materialization", "reactive_atom_missing_from_warhead"),
    ("leaving-group evidence uses pre-reaction parent graph", "atom_set", "parent atom and bond authorities; reaction delta", "retain every atom belonging to the pre-reaction warhead including leaving group atoms", "leaving-group evidence preserved", "block SMARTS materialization", "pre_reaction_leaving_group_evidence_missing"),
    ("complete warhead atom set is required", "atom_set", "reviewable per-sample atom-set proposal", "require an exact complete pre-reaction warhead atom set", "atom-set prerequisite satisfied", "block SMARTS materialization", "complete_warhead_atom_set_missing"),
    ("warhead atom set must be connected", "atom_set", "complete warhead atom set; parent bonds", "induced warhead subgraph is connected", "connected query may be designed", "block SMARTS materialization", "warhead_atom_set_disconnected"),
    ("attachment boundary must be exact-one", "boundary", "warhead atom set; complete parent graph", "exactly one bond crosses warhead to nonwarhead", "single attachment boundary verified", "block SMARTS materialization", "attachment_boundary_not_exact_one"),
    ("attachment atom must be inside warhead set", "boundary", "attachment boundary; warhead atom set", "warhead-side boundary atom is a member of the warhead atom set", "attachment atom admitted", "block SMARTS materialization", "attachment_atom_outside_warhead"),
    ("atom-map policy must be deterministic", "atom_map", "complete atom set; reactive and attachment atoms", "assign sorted unique positive exact integer maps deterministically", "map fields may be populated", "block SMARTS materialization", "atom_map_policy_unfrozen"),
    ("bond-order query semantics must be frozen", "query_semantics", "parent bond authority; query policy", "freeze expected pre-reaction bond-order query encoding", "bond queries may be emitted", "block SMARTS materialization", "bond_order_query_semantics_unfrozen"),
    ("formal-charge query semantics must be frozen", "query_semantics", "parent formal charges; query policy", "freeze formal-charge query encoding", "charge queries may be emitted", "block SMARTS materialization", "formal_charge_query_semantics_unfrozen"),
    ("aromaticity/H/chirality semantics must be frozen", "query_semantics", "explicit query policy", "freeze aromaticity hydrogen-count and chirality query semantics", "remaining atom queries may be emitted", "block SMARTS materialization", "aromaticity_H_chirality_semantics_unfrozen"),
    ("class-wide exact-one match validation is required", "validation", "candidate query; every supporting parent graph", "RDKit 2022.03.2 yields exactly one complete-warhead match per supporting graph", "candidate may enter human review", "block SMARTS review", "class_wide_exact_one_validation_missing"),
    ("candidate SMARTS is not approved SMARTS", "approval_boundary", "materialized candidate query", "candidate status is candidate_not_reviewed and never auto-approved", "candidate remains reviewable only", "block downstream approval", "candidate_misdeclared_approved"),
    ("SMARTS human review remains independent", "human_review", "validated candidate SMARTS; blank review record", "a real human review decision is required independently", "approved or revised state may be recorded by a later authorized step", "block approved rule", "SMARTS_human_review_missing"),
    ("downstream role/mask/model/training gates remain closed", "downstream_boundary", "approved rule and later human-gold prerequisites", "keep role mask model and training readiness false", "design remains metadata-only", "fail the transaction", "downstream_gate_opened"),
)

GAP_DEFINITIONS = (
    ("complete_warhead_atom_set_authority", "radius-1 local reaction-center signature and full parent graph only", "a candidate SMARTS must cover the reviewed complete warhead, not only its center", "materialize and review per-sample pre-reaction warhead atom-set proposals"),
    ("attachment_boundary_authority", "full parent graph exists but no warhead/nonwarhead partition exists", "a ligand-side query needs an exact-one external attachment boundary", "materialize and review per-sample attachment-boundary proposals"),
    ("deterministic_atom_map_policy", "reactive parent atom identity exists; query atom maps do not", "WARHEAD_RULE_FIELDS require deterministic reactive, attachment, and atom-set maps", "freeze deterministic atom-map assignment after atom-set review"),
    ("bond_order_query_semantics", "normalized parent bond orders exist without SMARTS query policy", "parent values do not uniquely determine SMARTS bond query syntax", "freeze RDKit bond-order query semantics"),
    ("formal_charge_query_semantics", "parent atom formal charges exist without SMARTS query policy", "parent values do not uniquely determine charge query constraints", "freeze RDKit formal-charge query semantics"),
    ("aromaticity_and_hydrogen_query_semantics", "normalized parent bond authority includes aromatic bond disposition, while atom-level aromaticity/H/chirality SMARTS query policy remains unfrozen", "query specificity and class-wide behavior depend on explicit aromaticity/H/chirality policy", "freeze RDKit aromaticity hydrogen-count and chirality semantics"),
    ("class_wide_exact_one_complete_warhead_match_validation", "exact-one radius-1 local-rule assignments exist only", "local-rule uniqueness is not complete-warhead query uniqueness", "validate the later candidate against every supporting parent graph"),
)


@dataclass(frozen=True)
class GateScenario:
    base_source_present: bool = True
    base_source_sha_matches: bool = True
    review_package_transaction_succeeded: bool = True
    review_package_materialized: bool = True
    class_count: int = 7
    sample_count: int = 11
    duplicate_class_identity: bool = False
    duplicate_sample_identity: bool = False
    class_rule_family_links_match: bool = True
    sample_class_rule_family_links_match: bool = True
    local_graph_json_sha_matches: bool = True
    local_center_reactive_flag_present: bool = True
    target_is_cys_sg: bool = True
    parent_atom_authority_present: bool = True
    parent_bond_authority_present: bool = True
    parent_graph_sha_matches: bool = True
    reactive_parent_atom_mapping_present: bool = True
    local_graph_declared_complete_warhead: bool = False
    class_support_lists_match: bool = True
    contract_count: int = 16
    readiness_row_order_matches: bool = True
    unresolved_authority_declared_available: bool = False
    candidate_smarts_prefilled: bool = False
    candidate_smarts_status: str = "not_materialized"
    smarts_materialization_readiness_open: bool = False
    smarts_review_readiness_open: bool = False
    approved_rule_open: bool = False
    downstream_readiness_open: bool = False
    partial_materialization_attempted: bool = False
    execution_boundary_crossed: bool = False
    leaving_group_rule_contract_matches: bool = True
    parent_leaving_group_evidence_matches: bool = True


FAILURE_MUTATIONS = (
    ("BASE source missing", "base_source_present", False, "BASE_source_missing"),
    ("BASE source SHA mismatch", "base_source_sha_matches", False, "BASE_source_SHA_mismatch"),
    ("review-package transaction not succeeded", "review_package_transaction_succeeded", False, "review_package_transaction_not_succeeded"),
    ("review-package materialized false", "review_package_materialized", False, "review_package_materialized_false"),
    ("class count not 7", "class_count", 6, "class_count_not_7"),
    ("sample count not 11", "sample_count", 10, "sample_count_not_11"),
    ("duplicate class identity", "duplicate_class_identity", True, "duplicate_class_identity"),
    ("duplicate sample identity", "duplicate_sample_identity", True, "duplicate_sample_identity"),
    ("class-rule-family link mismatch", "class_rule_family_links_match", False, "class_rule_family_link_mismatch"),
    ("sample-class-rule-family link mismatch", "sample_class_rule_family_links_match", False, "sample_class_rule_family_link_mismatch"),
    ("canonical local graph JSON/SHA mismatch", "local_graph_json_sha_matches", False, "canonical_local_graph_JSON_SHA_mismatch"),
    ("local center reactive flag missing", "local_center_reactive_flag_present", False, "local_center_reactive_flag_missing"),
    ("target condition not CYS SG", "target_is_cys_sg", False, "target_condition_not_CYS_SG"),
    ("parent atom authority missing", "parent_atom_authority_present", False, "parent_atom_authority_missing"),
    ("parent bond authority missing", "parent_bond_authority_present", False, "parent_bond_authority_missing"),
    ("parent graph SHA mismatch", "parent_graph_sha_matches", False, "parent_graph_SHA_mismatch"),
    ("reactive parent atom mapping missing", "reactive_parent_atom_mapping_present", False, "reactive_parent_atom_mapping_missing"),
    ("local graph incorrectly declared complete warhead", "local_graph_declared_complete_warhead", True, "local_graph_incorrectly_declared_complete_warhead"),
    ("class support list mismatch", "class_support_lists_match", False, "class_support_list_mismatch"),
    ("contract count not 16", "contract_count", 15, "contract_count_not_16"),
    ("readiness row count/order mismatch", "readiness_row_order_matches", False, "readiness_row_count_or_order_mismatch"),
    ("unresolved authority incorrectly declared available", "unresolved_authority_declared_available", True, "unresolved_authority_incorrectly_declared_available"),
    ("candidate SMARTS prefilled", "candidate_smarts_prefilled", True, "candidate_SMARTS_prefilled"),
    ("candidate SMARTS status prematurely advanced", "candidate_smarts_status", "candidate_not_reviewed", "candidate_SMARTS_status_prematurely_advanced"),
    ("SMARTS materialization readiness prematurely opened", "smarts_materialization_readiness_open", True, "SMARTS_materialization_readiness_prematurely_opened"),
    ("SMARTS review readiness prematurely opened", "smarts_review_readiness_open", True, "SMARTS_review_readiness_prematurely_opened"),
    ("approved rule prematurely opened", "approved_rule_open", True, "approved_rule_prematurely_opened"),
    ("role/mask/model/training readiness opened", "downstream_readiness_open", True, "downstream_readiness_opened"),
    ("partial materialization attempted", "partial_materialization_attempted", True, "partial_materialization_attempted"),
    ("execution boundary crossed", "execution_boundary_crossed", True, "execution_boundary_crossed"),
    ("reaction delta / rule-registry leaving-group contract mismatch", "leaving_group_rule_contract_matches", False, "leaving_group_rule_contract_mismatch"),
    ("parent leaving-group atom/bond evidence mismatch", "parent_leaving_group_evidence_matches", False, "parent_leaving_group_evidence_mismatch"),
)


@dataclass(frozen=True)
class LeavingGroupSampleEvidence:
    sample_index_row_id: str
    ligand_comp_id: str
    reactive_parent_atom_id: str
    leaving_group_parent_atom_ids: tuple[str, ...]
    leaving_group_bond_ids: tuple[str, ...]


@dataclass(frozen=True)
class LeavingGroupSemanticsValidation:
    warhead_rule_id: str
    available: bool
    leaving_group_count: int
    leaving_group_elements: tuple[str, ...]
    sample_evidence: tuple[LeavingGroupSampleEvidence, ...]


@dataclass(frozen=True)
class BuildResult:
    source_rows: tuple[Mapping[str, Any], ...]
    contract_rows: tuple[Mapping[str, Any], ...]
    readiness_rows: tuple[Mapping[str, Any], ...]
    gap_rows: tuple[Mapping[str, Any], ...]
    failure_rows: tuple[Mapping[str, Any], ...]
    transaction_succeeded: bool
    blocking_reasons: tuple[str, ...]
    leaving_group_class_count: int
    zero_leaving_group_class_count: int
    required_leaving_group_total_atom_count: int


def _git(
    repo_root: Path, *arguments: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ("git", *arguments),
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check and result.returncode:
        raise RuntimeError(
            "git_command_failed:"
            + " ".join(arguments)
            + ":"
            + result.stderr.decode("utf-8", "replace")
        )
    return result


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _meaningful(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def _utf8_sorted(values: Sequence[str]) -> list[str]:
    return sorted(values, key=lambda value: value.encode("utf-8"))


def canonical_parent_bond_id(
    atom_id_1: str, atom_id_2: str, normalized_bond_order: str
) -> str:
    if (
        not _meaningful(atom_id_1)
        or not _meaningful(atom_id_2)
        or "|" in atom_id_1
        or "|" in atom_id_2
        or atom_id_1 == atom_id_2
    ):
        raise ValueError("proposal_bond_endpoint_invalid")
    if (
        type(normalized_bond_order) is not str
        or normalized_bond_order not in PARENT_NORMALIZED_BOND_ORDERS
    ):
        raise ValueError("proposal_bond_order_invalid")
    low, high = _utf8_sorted((atom_id_1, atom_id_2))
    return f"{low}|{high}|{normalized_bond_order}"


def _validate_proposal_field_types(record: Mapping[str, Any]) -> None:
    if type(record) is not dict or tuple(record) != PROPOSAL_FIELDS:
        raise ValueError("proposal_field_inventory_or_order_mismatch")
    for field in PROPOSAL_FIELDS:
        value = record[field]
        contract = PROPOSAL_FIELD_TYPE_CONTRACT[field]
        if contract == "exact_int":
            if type(value) is not int:
                raise ValueError(f"proposal_field_type_invalid:{field}")
        elif contract == "exact_list_str":
            if type(value) is not list or any(type(item) is not str for item in value):
                raise ValueError(f"proposal_field_type_invalid:{field}")
        elif contract == "exact_str":
            if type(value) is not str:
                raise ValueError(f"proposal_field_type_invalid:{field}")
        else:
            raise AssertionError(f"unknown_proposal_type_contract:{contract}")


def proposal_hash_input(record: Mapping[str, Any]) -> dict[str, Any]:
    _validate_proposal_field_types(record)
    return {
        field: record[field]
        for field in PROPOSAL_FIELDS
        if field != PROPOSAL_HASH_EXCLUDED_FIELD
    }


def proposal_record_sha256(record: Mapping[str, Any]) -> str:
    return sha256(canonical_json(proposal_hash_input(record)).encode("utf-8"))


def validate_proposal_record(
    record: Mapping[str, Any],
    parent_atom_ids: Sequence[str],
    *,
    require_materialized_hash: bool,
) -> None:
    _validate_proposal_field_types(record)
    if (
        type(parent_atom_ids) not in (list, tuple)
        or any(not _meaningful(item) for item in parent_atom_ids)
        or len(parent_atom_ids) != len(set(parent_atom_ids))
    ):
        raise ValueError("proposal_parent_atom_authority_invalid")
    parent_ids = set(parent_atom_ids)
    if (
        not _meaningful(record["proposal_version"])
        or not _meaningful(record["sample_index_row_id"])
        or not _meaningful(record["pdb_id"])
        or not _meaningful(record["ligand_comp_id"])
        or not _meaningful(record["warhead_type_candidate_class_id"])
        or not _meaningful(record["reaction_family_id"])
        or not _meaningful(record["warhead_rule_id"])
        or not _meaningful(record["component_parent_graph_sha256"])
        or not _meaningful(record["proposal_method"])
    ):
        raise ValueError("proposal_required_string_empty")
    if record["warhead_type_candidate_class_index_0based"] < 0:
        raise ValueError("proposal_class_index_negative")
    if record["proposal_status"] not in PROPOSAL_STATUSES:
        raise ValueError("proposal_status_invalid")
    atom_list_fields = (
        "local_reaction_center_atom_ids",
        "proposed_pre_reaction_warhead_atom_ids",
        "required_leaving_group_atom_ids",
    )
    for field in atom_list_fields:
        values = record[field]
        if (
            values != _utf8_sorted(values)
            or len(values) != len(set(values))
            or any(not _meaningful(item) or item not in parent_ids for item in values)
        ):
            raise ValueError(f"proposal_atom_list_invalid:{field}")
    for field in (
        "ligand_reactive_parent_atom_id",
        "proposed_warhead_attachment_atom_id",
        "proposed_nonwarhead_boundary_atom_id",
    ):
        value = record[field]
        if field == "ligand_reactive_parent_atom_id" and not _meaningful(value):
            raise ValueError(f"proposal_atom_id_invalid:{field}")
        if value and value not in parent_ids:
            raise ValueError(f"proposal_atom_id_invalid:{field}")
    bond_ids = record["local_reaction_center_bond_ids"]
    if bond_ids != _utf8_sorted(bond_ids) or len(bond_ids) != len(set(bond_ids)):
        raise ValueError("proposal_bond_id_list_invalid")
    for bond_id in bond_ids:
        if type(bond_id) is not str:
            raise ValueError("proposal_bond_id_invalid")
        pieces = bond_id.split("|")
        if len(pieces) != 3:
            raise ValueError("proposal_bond_id_invalid")
        atom_1, atom_2, order = pieces
        if (
            atom_1 not in parent_ids
            or atom_2 not in parent_ids
            or canonical_parent_bond_id(atom_1, atom_2, order) != bond_id
        ):
            raise ValueError("proposal_bond_id_invalid")
    boundary_order = record["proposed_attachment_boundary_bond_order"]
    if boundary_order and boundary_order not in PARENT_NORMALIZED_BOND_ORDERS:
        raise ValueError("proposal_attachment_boundary_bond_order_invalid")
    ambiguity = record["ambiguity_reasons"]
    if (
        ambiguity != _utf8_sorted(ambiguity)
        or len(ambiguity) != len(set(ambiguity))
        or any(not _meaningful(item) for item in ambiguity)
    ):
        raise ValueError("proposal_ambiguity_reasons_invalid")
    if require_materialized_hash:
        digest = record["proposal_record_sha256"]
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("proposal_record_SHA_invalid")
        if digest != proposal_record_sha256(record):
            raise ValueError("proposal_record_SHA_mismatch")


def _rule_contract_failure(detail: str) -> None:
    raise ValueError(f"leaving_group_rule_contract_mismatch:{detail}")


def _parent_evidence_failure(detail: str) -> None:
    raise ValueError(f"parent_leaving_group_evidence_mismatch:{detail}")


def _csv_nonnegative_int(value: object, field: str) -> int:
    if type(value) is not str or re.fullmatch(r"0|[1-9][0-9]*", value) is None:
        _rule_contract_failure(f"{field}_invalid")
    return int(value)


def _csv_element_list(value: object) -> list[str]:
    if type(value) is not str:
        _rule_contract_failure("allowed_leaving_group_elements_not_str")
    if value == "":
        return []
    values = value.split(";")
    if (
        any(not _meaningful(item) for item in values)
        or values != sorted(values)
        or len(values) != len(set(values))
    ):
        _rule_contract_failure("allowed_leaving_group_elements_invalid")
    return values


def validate_pre_reaction_leaving_group_semantics(
    rule: Mapping[str, Any],
    supporting_samples: Sequence[Mapping[str, Any]],
    parent_atoms: Sequence[Mapping[str, Any]],
    parent_bonds: Sequence[Mapping[str, Any]],
    observed_to_parent_mappings: Sequence[Mapping[str, Any]],
) -> LeavingGroupSemanticsValidation:
    """Rebuild one rule's leaving-group meaning from immutable parent evidence."""

    try:
        local = json.loads(rule["canonical_local_graph_rule_json"])
    except (KeyError, TypeError, json.JSONDecodeError):
        _rule_contract_failure("canonical_local_graph_rule_JSON_invalid")
    delta = local.get("reaction_delta")
    if type(delta) is not dict or set(delta) != {
        "leaving_group_count",
        "leaving_group_elements",
        "reaction_delta_class",
    }:
        _rule_contract_failure("reaction_delta_field_inventory_invalid")
    count = delta["leaving_group_count"]
    elements = delta["leaving_group_elements"]
    delta_class = delta["reaction_delta_class"]
    if type(count) is not int or count < 0:
        _rule_contract_failure("leaving_group_count_invalid")
    if (
        type(elements) is not list
        or any(type(item) is not str or not item.strip() for item in elements)
        or elements != sorted(elements)
        or len(elements) != len(set(elements))
    ):
        _rule_contract_failure("leaving_group_elements_invalid")
    if not _meaningful(delta_class):
        _rule_contract_failure("reaction_delta_class_invalid")
    csv_count = _csv_nonnegative_int(
        rule.get("required_leaving_group_count"), "required_leaving_group_count"
    )
    csv_elements = _csv_element_list(rule.get("allowed_leaving_group_elements"))
    if count != csv_count:
        _rule_contract_failure("JSON_CSV_leaving_group_count_mismatch")
    if elements != csv_elements:
        _rule_contract_failure("JSON_CSV_leaving_group_elements_mismatch")
    if delta_class != rule.get("required_reaction_delta_class"):
        _rule_contract_failure("JSON_CSV_reaction_delta_class_mismatch")

    center = local.get("center_atom")
    local_atoms = local.get("local_atoms")
    local_bonds = local.get("local_bonds")
    if type(center) is not dict or not _meaningful(center.get("canonical_local_atom_id")):
        _rule_contract_failure("local_center_invalid")
    if type(local_atoms) is not list or any(type(item) is not dict for item in local_atoms):
        _rule_contract_failure("local_atoms_invalid")
    if type(local_bonds) is not list or any(type(item) is not dict for item in local_bonds):
        _rule_contract_failure("local_bonds_invalid")
    leaving_atoms = []
    for atom in local_atoms:
        flag = atom.get("is_leaving_group")
        retained = atom.get("is_retained_observed")
        if type(flag) is not bool or type(retained) is not bool:
            _rule_contract_failure("local_atom_boolean_invalid")
        if flag:
            leaving_atoms.append(atom)
    if len(leaving_atoms) != count:
        _rule_contract_failure("local_leaving_atom_count_mismatch")
    local_elements = sorted(atom.get("element") for atom in leaving_atoms)
    if local_elements != elements:
        _rule_contract_failure("local_leaving_atom_elements_mismatch")
    center_id = center["canonical_local_atom_id"]
    leaving_specs: list[tuple[str, str, str]] = []
    for atom in leaving_atoms:
        atom_id = atom.get("canonical_local_atom_id")
        element = atom.get("element")
        if not _meaningful(atom_id) or not _meaningful(element):
            _rule_contract_failure("local_leaving_atom_identity_invalid")
        if atom["is_retained_observed"] is not False:
            _rule_contract_failure("local_leaving_atom_retained")
        matching_bonds = [
            bond
            for bond in local_bonds
            if {bond.get("canonical_endpoint_1"), bond.get("canonical_endpoint_2")}
            == {center_id, atom_id}
        ]
        if len(matching_bonds) != 1:
            _rule_contract_failure("local_leaving_group_bond_missing_or_ambiguous")
        bond = matching_bonds[0]
        if (
            bond.get("projected_disposition")
            != "verified_leaving_group_endpoint_missing"
        ):
            _rule_contract_failure("local_leaving_group_bond_disposition_invalid")
        order = bond.get("normalized_bond_order")
        if order not in PARENT_NORMALIZED_BOND_ORDERS:
            _rule_contract_failure("local_leaving_group_bond_order_invalid")
        leaving_specs.append((atom_id, element, order))
    missing_disposition_bonds = [
        bond
        for bond in local_bonds
        if bond.get("projected_disposition")
        == "verified_leaving_group_endpoint_missing"
    ]
    if count == 0 and missing_disposition_bonds:
        _rule_contract_failure("zero_leaving_group_missing_disposition_present")
    if count != len(missing_disposition_bonds):
        _rule_contract_failure("leaving_group_disposition_count_mismatch")

    evidence_rows = []
    for sample in sorted(
        supporting_samples, key=lambda row: row["sample_index_row_id"]
    ):
        sample_id = sample["sample_index_row_id"]
        component = sample["ligand_comp_id"]
        graph_sha = sample["component_parent_graph_sha256"]
        reactive_rows = [
            row
            for row in observed_to_parent_mappings
            if row.get("sample_index_row_id") == sample_id
            and row.get("reactive_ligand_atom") == "true"
            and row.get("verified") == "true"
        ]
        if len(reactive_rows) != 1:
            _parent_evidence_failure("reactive_parent_mapping_not_exact_one")
        reactive_mapping = reactive_rows[0]
        reactive_id = reactive_mapping.get("parent_ccd_atom_id")
        if (
            reactive_id != sample.get("ligand_reactive_parent_ccd_atom_id")
            or reactive_mapping.get("ligand_comp_id") != component
            or reactive_mapping.get("component_parent_graph_sha256") != graph_sha
        ):
            _parent_evidence_failure("reactive_parent_mapping_chain_mismatch")
        component_atoms = [
            row
            for row in parent_atoms
            if row.get("ligand_comp_id") == component
            and row.get("component_parent_graph_sha256") == graph_sha
            and row.get("verified") == "true"
        ]
        atom_by_id = {row.get("ccd_atom_id"): row for row in component_atoms}
        if len(atom_by_id) != len(component_atoms) or reactive_id not in atom_by_id:
            _parent_evidence_failure("reactive_or_parent_atom_missing")
        reactive_atom = atom_by_id[reactive_id]
        try:
            reactive_charge = int(reactive_atom["ccd_formal_charge"])
        except (KeyError, TypeError, ValueError):
            _parent_evidence_failure("reactive_parent_formal_charge_invalid")
        if (
            reactive_atom.get("ccd_type_symbol") != center.get("element")
            or reactive_charge != center.get("formal_charge")
        ):
            _parent_evidence_failure("reactive_parent_center_semantics_mismatch")
        component_bonds = [
            row
            for row in parent_bonds
            if row.get("ligand_comp_id") == component
            and row.get("component_parent_graph_sha256") == graph_sha
            and row.get("verified") == "true"
            and reactive_id
            in {row.get("parent_ccd_atom_id_1"), row.get("parent_ccd_atom_id_2")}
        ]
        for bond in component_bonds:
            other = (
                bond.get("parent_ccd_atom_id_2")
                if bond.get("parent_ccd_atom_id_1") == reactive_id
                else bond.get("parent_ccd_atom_id_1")
            )
            if other not in atom_by_id:
                _parent_evidence_failure("adjacent_parent_atom_missing")
        used_atoms: set[str] = set()
        found_atoms: list[str] = []
        found_bonds: list[str] = []
        for _local_id, element, order in sorted(leaving_specs):
            candidates = []
            for bond in component_bonds:
                other = (
                    bond["parent_ccd_atom_id_2"]
                    if bond["parent_ccd_atom_id_1"] == reactive_id
                    else bond["parent_ccd_atom_id_1"]
                )
                if (
                    atom_by_id[other].get("ccd_type_symbol") == element
                    and bond.get("normalized_bond_order") == order
                ):
                    candidates.append((other, bond))
            if len(candidates) != 1:
                _parent_evidence_failure(
                    "leaving_group_parent_candidate_not_exact_one"
                )
            other, bond = candidates[0]
            if other in used_atoms:
                _parent_evidence_failure("leaving_group_parent_candidate_reused")
            used_atoms.add(other)
            found_atoms.append(other)
            found_bonds.append(
                canonical_parent_bond_id(reactive_id, other, bond["normalized_bond_order"])
            )
        if len(found_atoms) != count:
            _parent_evidence_failure("leaving_group_parent_count_mismatch")
        evidence_rows.append(
            LeavingGroupSampleEvidence(
                sample_index_row_id=sample_id,
                ligand_comp_id=component,
                reactive_parent_atom_id=reactive_id,
                leaving_group_parent_atom_ids=tuple(_utf8_sorted(found_atoms)),
                leaving_group_bond_ids=tuple(_utf8_sorted(found_bonds)),
            )
        )
    return LeavingGroupSemanticsValidation(
        warhead_rule_id=rule["warhead_rule_id"],
        available=True,
        leaving_group_count=count,
        leaving_group_elements=tuple(elements),
        sample_evidence=tuple(evidence_rows),
    )


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _csv_bytes(
    columns: Sequence[str], rows: Iterable[Mapping[str, Any]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _cell(row.get(field, "")) for field in columns})
    return stream.getvalue().encode("utf-8")


def _cell(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return ""
    if type(value) in (list, dict, tuple):
        return canonical_json(value)
    return str(value)


def validate_execution_boundary_v1(repo_root: Path) -> str:
    identity = _git(
        repo_root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).stdout.decode().splitlines()
    if identity != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("formal_BASE_identity_mismatch")
    head = _git(repo_root, "rev-parse", "HEAD").stdout.decode().strip()
    if head == BASE_COMMIT:
        return "pre_commit"
    raw = _git(repo_root, "cat-file", "commit", head).stdout
    headers, separator, message = raw.partition(b"\n\n")
    if not separator:
        raise ValueError("successor_commit_object_malformed")
    parents = tuple(
        line[7:].decode() for line in headers.splitlines() if line.startswith(b"parent ")
    )
    if parents != (BASE_COMMIT,):
        raise ValueError("successor_parent_not_exact_BASE")
    subject, newline, body = message.partition(b"\n")
    if not newline or subject.decode() != FORMAL_COMMIT_SUBJECT:
        raise ValueError("successor_subject_mismatch")
    if body:
        raise ValueError("successor_commit_body_nonempty")
    changed = {
        item.decode()
        for item in _git(
            repo_root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head
        ).stdout.split(b"\0")
        if item
    }
    if changed != {path.as_posix() for path in EXACT10_PATHS}:
        raise ValueError("successor_changed_path_inventory_mismatch")
    modes = [
        item.partition(b"\t")[0]
        for item in _git(
            repo_root,
            "ls-tree",
            "-r",
            "-z",
            head,
            "--",
            *(path.as_posix() for path in EXACT10_PATHS),
        ).stdout.split(b"\0")
        if item
    ]
    if len(modes) != 10 or any(not item.startswith(b"100644 blob ") for item in modes):
        raise ValueError("successor_exact10_file_mode_invalid")
    branch = _git(
        repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False
    )
    if branch.returncode:
        return "detached_candidate_post_commit"
    if branch.stdout.decode().strip() != "main":
        raise ValueError("successor_formal_branch_not_main")
    origin = _git(
        repo_root, "rev-parse", "--verify", "refs/remotes/origin/main", check=False
    )
    if origin.returncode:
        raise ValueError("successor_origin_main_missing")
    origin_oid = origin.stdout.decode().strip()
    if origin_oid == BASE_COMMIT:
        return "formal_main_post_commit_unpushed"
    if origin_oid == head:
        return "formal_main_post_push"
    raise ValueError("successor_origin_main_lifecycle_mismatch")


def base_bytes(repo_root: Path, path: Path) -> bytes:
    result = _git(
        repo_root, "show", f"{BASE_COMMIT}:{path.as_posix()}", check=False
    )
    if result.returncode or not result.stdout:
        raise ValueError(f"BASE_source_missing:{path.as_posix()}")
    return result.stdout


def load_frozen_sources(repo_root: Path) -> dict[Path, bytes]:
    validate_execution_boundary_v1(repo_root)
    payloads = {}
    for path, expected in FROZEN_BASE_SHA256.items():
        payload = base_bytes(repo_root, path)
        if sha256(payload) != expected:
            raise ValueError(f"BASE_source_SHA_mismatch:{path.as_posix()}")
        payloads[path] = payload
    return payloads


def _literal_tuple(source: bytes, name: str) -> tuple[str, ...]:
    tree = ast.parse(source.decode("utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                value = ast.literal_eval(node.value)
                if type(value) is tuple and all(type(item) is str for item in value):
                    return value
    raise ValueError(f"literal_tuple_missing:{name}")


def _source_metadata(path: Path) -> tuple[str, str, str, bool]:
    values = {
        REVIEW_PACKAGE_SOURCE: ("11/11", "lifecycle and review-package production contract", "predecessor_production_contract", False),
        REVIEW_PACKAGE_MANIFEST: ("11/11", "transaction; counts; review and downstream state", "review_package_manifest", True),
        REVIEW_PACKAGE_INDEX: ("18/18", "package identities and readiness", "review_package_index_authority", True),
        CLASS_REVIEW_TEMPLATES: ("7/7", "class links and blank review state", "blank_class_review_templates", True),
        SAMPLE_REVIEW_TEMPLATES: ("11/11", "sample links and blank review state", "blank_sample_review_templates", True),
        REVIEW_GATE_SOURCE: ("11/11", "review status and schema contracts", "review_gate_production_contract", False),
        ASSIGNMENT_SOURCE: ("11/11", "assignment contract and candidate-only boundary", "assignment_production_contract", False),
        ASSIGNMENT_AUTHORITY: ("11/11", "sample/class/rule/family/reactive atom/graph links", "Current11_assignment_authority", True),
        CLASS_VOCABULARY: ("7/7", "class identities and support counts", "candidate_class_vocabulary", True),
        FAMILY_REGISTRY: ("7/7", "family identity and target condition", "candidate_family_registry", True),
        RULE_REGISTRY: ("7/7", "radius-1 local graph JSON/SHA and reaction delta", "candidate_local_rule_registry", True),
        ROLE_CONTRACT_SOURCE: ("11/11", "WARHEAD_RULE_FIELDS exact12 and downstream prerequisites", "downstream_role_contract", False),
        PARENT_ATOM_AUTHORITY: ("11/11;9/9 components", "pre-reaction heavy atoms; charges; graph SHA", "pre_reaction_parent_atom_authority", True),
        PARENT_BOND_AUTHORITY: ("11/11;9/9 components", "pre-reaction heavy bonds; bond orders; graph SHA", "pre_reaction_parent_bond_authority", True),
        ATOM_MAPPING_AUTHORITY: ("11/11", "known reactive observed-to-parent atom mapping", "reactive_parent_atom_mapping_authority", True),
    }
    return values[path]


def _source_inventory(
    payloads: Mapping[Path, bytes],
) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for path in SOURCE_PATHS:
        coverage, fields, authority, provides = _source_metadata(path)
        payload = payloads[path]
        count = (
            len(_csv_rows(payload))
            if path.suffix == ".csv"
            else 1
            if path.suffix == ".json"
            else len(payload.decode("utf-8").splitlines())
        )
        rows.append(
            {
                "source_path": path.as_posix(),
                "BASE_SHA256": sha256(payload),
                "source_row_count": count,
                "Current11_coverage": coverage,
                "fields_actually_used": fields,
                "authority_class": authority,
                "provides_current_value": provides,
                "verified": True,
            }
        )
    return tuple(rows)


def _require(condition: bool, reason: str, reasons: list[str]) -> None:
    if not condition:
        reasons.append(reason)


def _phase_a(
    payloads: Mapping[Path, bytes],
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    dict[str, LeavingGroupSemanticsValidation],
    list[str],
]:
    reasons: list[str] = []
    manifest = json.loads(payloads[REVIEW_PACKAGE_MANIFEST])
    packages = _csv_rows(payloads[REVIEW_PACKAGE_INDEX])
    class_templates = _csv_rows(payloads[CLASS_REVIEW_TEMPLATES])
    sample_templates = _csv_rows(payloads[SAMPLE_REVIEW_TEMPLATES])
    assignments = _csv_rows(payloads[ASSIGNMENT_AUTHORITY])
    classes = _csv_rows(payloads[CLASS_VOCABULARY])
    families = _csv_rows(payloads[FAMILY_REGISTRY])
    rules = _csv_rows(payloads[RULE_REGISTRY])
    parent_atoms = _csv_rows(payloads[PARENT_ATOM_AUTHORITY])
    parent_bonds = _csv_rows(payloads[PARENT_BOND_AUTHORITY])
    mappings = _csv_rows(payloads[ATOM_MAPPING_AUTHORITY])

    _require(manifest.get("transaction_succeeded") is True, "review_package_transaction_not_succeeded", reasons)
    _require(manifest.get("review_package_materialized") is True, "review_package_materialized_false", reasons)
    _require(len(classes) == len(class_templates) == 7, "class_count_not_7", reasons)
    _require(len(assignments) == len(sample_templates) == 11, "sample_count_not_11", reasons)
    _require(len(packages) == 18, "review_package_count_not_18", reasons)
    _require(
        manifest.get("ready_for_family_identity_review_execution") is True
        and manifest.get("ready_for_rule_topology_review_execution") is True
        and manifest.get("ready_for_sample_assignment_review_execution") is True
        and manifest.get("ready_for_SMARTS_review_execution") is False
        and manifest.get("ready_for_complete_human_review_execution") is False
        and manifest.get("human_review_execution_completed") is False,
        "review_package_readiness_state_mismatch",
        reasons,
    )
    _require(
        manifest.get("approved_reaction_family_available_count") == 0
        and manifest.get("approved_warhead_rule_available_count") == 0
        and manifest.get("approved_warhead_smarts_count") == 0
        and manifest.get("human_gold_review_completed_count") == 0
        and manifest.get("training_label_approved_count") == 0
        and manifest.get("integrated_covalent_model_module_count") == 0,
        "predecessor_approval_or_training_state_open",
        reasons,
    )
    _require(
        all(
            row["package_item_materialized"] == "true"
            and row["verified"] == "true"
            and row["review_record_sha256_populated"] == "false"
            and row["human_review_execution_completed"] == "false"
            for row in packages
        ),
        "review_package_index_state_mismatch",
        reasons,
    )
    _require(
        all(
            row["reaction_family_identity_review_decision"] == "not_reviewed"
            and row["warhead_rule_topology_review_decision"] == "not_reviewed"
            and row["warhead_smarts_review_status"] == "not_materialized"
            and row["candidate_warhead_smarts"] == ""
            and row["reviewer_id"] == row["review_rationale"] == row["review_notes"] == ""
            and row["review_record_sha256"] == ""
            for row in class_templates
        ),
        "class_review_state_not_blank",
        reasons,
    )
    _require(
        all(
            row["sample_assignment_review_decision"] == "not_reviewed"
            and row["reviewer_id"] == row["review_rationale"] == row["review_notes"] == ""
            and row["review_record_sha256"] == ""
            for row in sample_templates
        ),
        "sample_review_state_not_blank",
        reasons,
    )
    _require(
        _literal_tuple(payloads[ROLE_CONTRACT_SOURCE], "WARHEAD_RULE_FIELDS")
        == WARHEAD_RULE_FIELDS,
        "inherited_WARHEAD_RULE_FIELDS_mismatch",
        reasons,
    )

    class_ids = [row["warhead_type_candidate_class_id"] for row in classes]
    sample_ids = [row["sample_index_row_id"] for row in assignments]
    _require(len(set(class_ids)) == 7, "duplicate_class_identity", reasons)
    _require(len(set(sample_ids)) == 11, "duplicate_sample_identity", reasons)
    _require(
        [int(row["warhead_type_candidate_class_index_0based"]) for row in classes]
        == list(range(7)),
        "class_order_mismatch",
        reasons,
    )
    family_by_id = {row["reaction_family_id"]: row for row in families}
    rule_by_id = {row["warhead_rule_id"]: row for row in rules}
    class_by_id = {row["warhead_type_candidate_class_id"]: row for row in classes}
    _require(len(family_by_id) == len(rule_by_id) == 7, "registry_identity_count_mismatch", reasons)

    for row in classes:
        rule = rule_by_id.get(row["warhead_rule_id"])
        family = family_by_id.get(row["reaction_family_id"])
        _require(
            rule is not None
            and family is not None
            and rule["reaction_family_id"] == row["reaction_family_id"],
            "class_rule_family_link_mismatch",
            reasons,
        )
        if rule is None:
            continue
        try:
            local = json.loads(rule["canonical_local_graph_rule_json"])
            digest = sha256(canonical_json(local).encode("utf-8"))
        except (KeyError, TypeError, json.JSONDecodeError):
            digest = ""
            local = {}
        _require(
            digest == rule["canonical_local_graph_rule_sha256"]
            == row["canonical_local_graph_rule_sha256"],
            "canonical_local_graph_JSON_SHA_mismatch",
            reasons,
        )
        _require(
            local.get("center_atom", {}).get("reactive") is True,
            "local_center_reactive_flag_missing",
            reasons,
        )
        _require(
            local.get("selected_signature_radius") == 1
            and local.get("rule_kind") == "canonical_local_graph_exact_match_v1",
            "local_graph_incorrectly_declared_complete_warhead",
            reasons,
        )
        target = local.get("target_condition", {})
        _require(
            target.get("residue") == "CYS"
            and target.get("residue_atom") == "SG"
            and row["target_residue_name"] == "CYS"
            and row["target_residue_atom_name"] == "SG",
            "target_condition_not_CYS_SG",
            reasons,
        )
        _require(
            rule["approved_warhead_smarts"] == ""
            and rule["approved"] == "false"
            and rule["human_gold_review_completed"] == "false",
            "candidate_rule_prematurely_approved",
            reasons,
        )

    atom_graphs: dict[str, set[str]] = defaultdict(set)
    bond_graphs: dict[str, set[str]] = defaultdict(set)
    for row in parent_atoms:
        if row["verified"] == "true":
            atom_graphs[row["ligand_comp_id"]].add(row["component_parent_graph_sha256"])
    for row in parent_bonds:
        if row["verified"] == "true":
            bond_graphs[row["ligand_comp_id"]].add(row["component_parent_graph_sha256"])
    reactive_by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in mappings:
        if row["reactive_ligand_atom"] == "true" and row["verified"] == "true":
            reactive_by_sample[row["sample_index_row_id"]].append(row)

    support: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in assignments:
        support[row["warhead_type_candidate_class_id"]].append(row)
        cls = class_by_id.get(row["warhead_type_candidate_class_id"])
        _require(
            cls is not None
            and row["candidate_reaction_family_id"] == cls["reaction_family_id"]
            and row["candidate_warhead_rule_id"] == cls["warhead_rule_id"]
            and row["warhead_type_candidate_class_index_0based"]
            == cls["warhead_type_candidate_class_index_0based"],
            "sample_class_rule_family_link_mismatch",
            reasons,
        )
        _require(
            row["target_residue_name"] == "CYS"
            and row["target_residue_atom_name"] == "SG",
            "target_condition_not_CYS_SG",
            reasons,
        )
        component = row["ligand_comp_id"]
        graph_sha = row["component_parent_graph_sha256"]
        _require(bool(atom_graphs.get(component)), "parent_atom_authority_missing", reasons)
        _require(bool(bond_graphs.get(component)), "parent_bond_authority_missing", reasons)
        _require(
            atom_graphs.get(component) == {graph_sha}
            and bond_graphs.get(component) == {graph_sha},
            "parent_graph_SHA_mismatch",
            reasons,
        )
        reactive = reactive_by_sample.get(row["sample_index_row_id"], [])
        _require(
            len(reactive) == 1
            and reactive[0]["pdb_id"] == row["pdb_id"]
            and reactive[0]["ligand_comp_id"] == component
            and reactive[0]["parent_ccd_atom_id"]
            == row["ligand_reactive_parent_ccd_atom_id"]
            and reactive[0]["component_parent_graph_sha256"] == graph_sha,
            "reactive_parent_atom_mapping_missing",
            reasons,
        )

    for row in classes:
        rows = support[row["warhead_type_candidate_class_id"]]
        _require(
            len(rows) == int(row["Current11_match_count"])
            and len({item["ligand_comp_id"] for item in rows})
            == int(row["Current11_unique_component_count"]),
            "class_support_list_mismatch",
            reasons,
        )
    class_template_by_id = {
        row["warhead_type_candidate_class_id"]: row for row in class_templates
    }
    sample_template_by_id = {
        row["sample_index_row_id"]: row for row in sample_templates
    }
    _require(
        all(
            class_template_by_id.get(row["warhead_type_candidate_class_id"], {}).get(
                "reaction_family_id"
            )
            == row["reaction_family_id"]
            and class_template_by_id[row["warhead_type_candidate_class_id"]][
                "warhead_rule_id"
            ]
            == row["warhead_rule_id"]
            for row in classes
        ),
        "class_review_template_link_mismatch",
        reasons,
    )
    _require(
        all(
            sample_template_by_id.get(row["sample_index_row_id"], {}).get(
                "warhead_type_candidate_class_id"
            )
            == row["warhead_type_candidate_class_id"]
            and sample_template_by_id[row["sample_index_row_id"]]["reaction_family_id"]
            == row["candidate_reaction_family_id"]
            and sample_template_by_id[row["sample_index_row_id"]]["warhead_rule_id"]
            == row["candidate_warhead_rule_id"]
            for row in assignments
        ),
        "sample_review_template_link_mismatch",
        reasons,
    )
    leaving_group_validations: dict[str, LeavingGroupSemanticsValidation] = {}
    for cls in classes:
        rule = rule_by_id.get(cls["warhead_rule_id"])
        if rule is None:
            continue
        try:
            validation = validate_pre_reaction_leaving_group_semantics(
                rule,
                support[cls["warhead_type_candidate_class_id"]],
                parent_atoms,
                parent_bonds,
                mappings,
            )
        except ValueError as exc:
            reasons.append(str(exc))
        else:
            leaving_group_validations[cls["warhead_rule_id"]] = validation
    return classes, assignments, rules, leaving_group_validations, reasons


def contract_rows() -> tuple[Mapping[str, Any], ...]:
    return tuple(
        {
            "contract_id": f"SMARTS_GATE_{index:03d}",
            "semantic_name": definition[0],
            "contract_scope": definition[1],
            "required_inputs": definition[2],
            "validation_rule": definition[3],
            "success_effect": definition[4],
            "failure_effect": definition[5],
            "reason_code": definition[6],
            "fails_closed": True,
            "verified": True,
        }
        for index, definition in enumerate(CONTRACT_DEFINITIONS, 1)
    )


def _readiness_rows(
    classes: Sequence[Mapping[str, str]],
    assignments: Sequence[Mapping[str, str]],
    leaving_group_validations: Mapping[str, LeavingGroupSemanticsValidation],
) -> tuple[Mapping[str, Any], ...]:
    support: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in assignments:
        support[row["warhead_type_candidate_class_id"]].append(row)
    blockers = ";".join(
        (
            "complete_warhead_atom_set_authority_missing",
            "attachment_boundary_authority_missing",
            "deterministic_atom_map_policy_missing",
            "bond_order_query_semantics_unfrozen",
            "formal_charge_query_semantics_unfrozen",
            "aromaticity_H_chirality_query_semantics_unfrozen",
            "class_wide_exact_one_complete_warhead_match_validation_missing",
            "candidate_warhead_SMARTS_not_materialized",
            "SMARTS_human_review_not_ready",
        )
    )
    rows = []
    for cls in classes:
        leaving_group_validation = leaving_group_validations.get(
            cls["warhead_rule_id"]
        )
        leaving_group_semantics_available = (
            leaving_group_validation is not None
            and leaving_group_validation.available is True
        )
        supporting = sorted(
            support[cls["warhead_type_candidate_class_id"]],
            key=lambda row: row["sample_index_row_id"],
        )
        rows.append(
            {
                "warhead_type_candidate_class_index_0based": int(
                    cls["warhead_type_candidate_class_index_0based"]
                ),
                "warhead_type_candidate_class_id": cls[
                    "warhead_type_candidate_class_id"
                ],
                "reaction_family_id": cls["reaction_family_id"],
                "warhead_rule_id": cls["warhead_rule_id"],
                "canonical_local_graph_rule_sha256": cls[
                    "canonical_local_graph_rule_sha256"
                ],
                "Current11_match_count": int(cls["Current11_match_count"]),
                "Current11_unique_component_count": int(
                    cls["Current11_unique_component_count"]
                ),
                "supporting_sample_ids": ";".join(
                    row["sample_index_row_id"] for row in supporting
                ),
                "supporting_component_ids": ";".join(
                    sorted({row["ligand_comp_id"] for row in supporting})
                ),
                "local_reaction_center_rule_available": True,
                "parent_heavy_atom_authority_available": True,
                "parent_heavy_bond_authority_available": True,
                "parent_graph_SHA_verified": True,
                "reactive_parent_atom_mapping_available": True,
                "pre_reaction_leaving_group_semantics_available": leaving_group_semantics_available,
                "complete_warhead_atom_set_available": False,
                "exact_one_attachment_boundary_available": False,
                "deterministic_atom_map_policy_available": False,
                "SMARTS_query_semantics_frozen": False,
                "class_wide_exact_one_match_validation_available": False,
                "candidate_warhead_smarts": "",
                "candidate_warhead_smarts_status": "not_materialized",
                "candidate_warhead_smarts_materialized": False,
                "ready_for_warhead_atom_set_and_attachment_boundary_proposal_materialization": leaving_group_semantics_available,
                "ready_for_candidate_warhead_smarts_materialization": False,
                "ready_for_SMARTS_human_review": False,
                "approved_warhead_rule_available": False,
                "ready_for_role_proposal_generation": False,
                "ready_for_mask_materialization": False,
                "ready_for_model_integration": False,
                "ready_for_training": False,
                "blocking_reasons": blockers,
                "verified": True,
            }
        )
    return tuple(rows)


def _gap_rows(
    classes: Sequence[Mapping[str, str]],
) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for cls in classes:
        for authority, evidence, why, step in GAP_DEFINITIONS:
            rows.append(
                {
                    "warhead_type_candidate_class_id": cls[
                        "warhead_type_candidate_class_id"
                    ],
                    "missing_authority": authority,
                    "current_evidence": evidence,
                    "why_required": why,
                    "would_block_atom_set_proposal": False,
                    "would_block_SMARTS_materialization": True,
                    "would_block_SMARTS_review": True,
                    "resolution_owner": "engineering_then_human_review",
                    "recommended_resolution_step": step,
                    "verified": True,
                }
            )
    return tuple(rows)


def observe_failure_scenario(scenario: GateScenario) -> tuple[str, ...]:
    checks = (
        (not scenario.base_source_present, "BASE_source_missing"),
        (not scenario.base_source_sha_matches, "BASE_source_SHA_mismatch"),
        (not scenario.review_package_transaction_succeeded, "review_package_transaction_not_succeeded"),
        (not scenario.review_package_materialized, "review_package_materialized_false"),
        (scenario.class_count != 7, "class_count_not_7"),
        (scenario.sample_count != 11, "sample_count_not_11"),
        (scenario.duplicate_class_identity, "duplicate_class_identity"),
        (scenario.duplicate_sample_identity, "duplicate_sample_identity"),
        (not scenario.class_rule_family_links_match, "class_rule_family_link_mismatch"),
        (not scenario.sample_class_rule_family_links_match, "sample_class_rule_family_link_mismatch"),
        (not scenario.local_graph_json_sha_matches, "canonical_local_graph_JSON_SHA_mismatch"),
        (not scenario.local_center_reactive_flag_present, "local_center_reactive_flag_missing"),
        (not scenario.target_is_cys_sg, "target_condition_not_CYS_SG"),
        (not scenario.parent_atom_authority_present, "parent_atom_authority_missing"),
        (not scenario.parent_bond_authority_present, "parent_bond_authority_missing"),
        (not scenario.parent_graph_sha_matches, "parent_graph_SHA_mismatch"),
        (not scenario.reactive_parent_atom_mapping_present, "reactive_parent_atom_mapping_missing"),
        (scenario.local_graph_declared_complete_warhead, "local_graph_incorrectly_declared_complete_warhead"),
        (not scenario.class_support_lists_match, "class_support_list_mismatch"),
        (scenario.contract_count != 16, "contract_count_not_16"),
        (not scenario.readiness_row_order_matches, "readiness_row_count_or_order_mismatch"),
        (scenario.unresolved_authority_declared_available, "unresolved_authority_incorrectly_declared_available"),
        (scenario.candidate_smarts_prefilled, "candidate_SMARTS_prefilled"),
        (scenario.candidate_smarts_status != "not_materialized", "candidate_SMARTS_status_prematurely_advanced"),
        (scenario.smarts_materialization_readiness_open, "SMARTS_materialization_readiness_prematurely_opened"),
        (scenario.smarts_review_readiness_open, "SMARTS_review_readiness_prematurely_opened"),
        (scenario.approved_rule_open, "approved_rule_prematurely_opened"),
        (scenario.downstream_readiness_open, "downstream_readiness_opened"),
        (scenario.partial_materialization_attempted, "partial_materialization_attempted"),
        (scenario.execution_boundary_crossed, "execution_boundary_crossed"),
        (not scenario.leaving_group_rule_contract_matches, "leaving_group_rule_contract_mismatch"),
        (not scenario.parent_leaving_group_evidence_matches, "parent_leaving_group_evidence_mismatch"),
    )
    return tuple(reason for failed, reason in checks if failed)


def build_failure_rows() -> tuple[Mapping[str, Any], ...]:
    baseline = GateScenario()
    rows = []
    signatures = set()
    for case, field, value, expected in FAILURE_MUTATIONS:
        original = getattr(baseline, field)
        if type(value) is not type(original):
            raise AssertionError(f"mutation_type_not_exact:{case}")
        if value == original:
            raise AssertionError(f"mutation_does_not_change_baseline:{case}")
        scenario = dataclasses.replace(baseline, **{field: value})
        observed = observe_failure_scenario(scenario)
        signature = f"{field}={canonical_json(value)}"
        if signature in signatures:
            raise AssertionError(f"duplicate_mutation_signature:{signature}")
        signatures.add(signature)
        verified = expected in observed
        rows.append(
            {
                "failure_case": case,
                "mutation_signature": signature,
                "mutated_field": field,
                "mutated_value_json": canonical_json(value),
                "expected_reason": expected,
                "observed_reasons": ";".join(observed),
                "expected_reason_verified": verified,
                "fails_closed": bool(observed),
                "contract_registry_row_count": 0,
                "readiness_matrix_row_count": 0,
                "authority_gap_row_count": 0,
                "proposal_materialization_ready": False,
                "SMARTS_materialization_ready": False,
                "role_proposal_generation_ready": False,
                "mask_materialization_ready": False,
                "model_integration_ready": False,
                "training_ready": False,
                "verified": verified and bool(observed),
            }
        )
    if len(rows) != len(signatures) or len(rows) != 32:
        raise AssertionError("failure_matrix_not_Exact32")
    return tuple(rows)


def transaction_tables(
    blocking_reasons: Sequence[str],
    contracts: Sequence[Mapping[str, Any]],
    readiness: Sequence[Mapping[str, Any]],
    gaps: Sequence[Mapping[str, Any]],
) -> tuple[
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
]:
    if blocking_reasons:
        return (), (), ()
    return tuple(contracts), tuple(readiness), tuple(gaps)


def build_result(repo_root: Path) -> BuildResult:
    payloads = load_frozen_sources(repo_root)
    classes, assignments, _rules, leaving_group_validations, reasons = _phase_a(
        payloads
    )
    contracts = contract_rows()
    readiness = (
        _readiness_rows(classes, assignments, leaving_group_validations)
        if not reasons
        else ()
    )
    gaps = _gap_rows(classes) if not reasons else ()
    if not reasons:
        _require(len(contracts) == 16, "contract_count_not_16", reasons)
        _require(
            len(leaving_group_validations) == 7
            and sum(
                value.leaving_group_count > 0
                for value in leaving_group_validations.values()
            )
            == 1
            and sum(
                value.leaving_group_count == 0
                for value in leaving_group_validations.values()
            )
            == 6
            and sum(
                value.leaving_group_count
                for value in leaving_group_validations.values()
            )
            == 1,
            "leaving_group_baseline_count_mismatch",
            reasons,
        )
        _require(
            len(readiness) == 7
            and [row["warhead_type_candidate_class_index_0based"] for row in readiness]
            == list(range(7)),
            "readiness_row_count_or_order_mismatch",
            reasons,
        )
        _require(len(gaps) == 49, "authority_gap_matrix_count_mismatch", reasons)
        _require(
            all(
                row["candidate_warhead_smarts"] == ""
                and row["candidate_warhead_smarts_status"] == "not_materialized"
                and row["ready_for_warhead_atom_set_and_attachment_boundary_proposal_materialization"]
                and not row["ready_for_candidate_warhead_smarts_materialization"]
                and not row["ready_for_SMARTS_human_review"]
                and not row["approved_warhead_rule_available"]
                and not row["ready_for_role_proposal_generation"]
                and not row["ready_for_mask_materialization"]
                and not row["ready_for_model_integration"]
                and not row["ready_for_training"]
                for row in readiness
            ),
            "readiness_truthfulness_mismatch",
            reasons,
        )
    contracts, readiness, gaps = transaction_tables(
        reasons, contracts, readiness, gaps
    )
    return BuildResult(
        source_rows=_source_inventory(payloads),
        contract_rows=contracts,
        readiness_rows=readiness,
        gap_rows=gaps,
        failure_rows=build_failure_rows(),
        transaction_succeeded=not reasons,
        blocking_reasons=tuple(sorted(set(reasons))),
        leaving_group_class_count=(
            sum(
                validation.leaving_group_count > 0
                for validation in leaving_group_validations.values()
            )
            if not reasons
            else 0
        ),
        zero_leaving_group_class_count=(
            sum(
                validation.leaving_group_count == 0
                for validation in leaving_group_validations.values()
            )
            if not reasons
            else 0
        ),
        required_leaving_group_total_atom_count=(
            sum(
                validation.leaving_group_count
                for validation in leaving_group_validations.values()
            )
            if not reasons
            else 0
        ),
    )


def _manifest(
    result: BuildResult, payloads_without_manifest: Mapping[str, bytes]
) -> dict[str, Any]:
    success = result.transaction_succeeded
    rows = result.readiness_rows
    count = lambda field: sum(row[field] is True for row in rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "formal_base": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "formal_future_commit_subject": FORMAL_COMMIT_SUBJECT,
        "source_count": 15,
        "source_sha256": {
            row["source_path"]: row["BASE_SHA256"] for row in result.source_rows
        },
        "required_smarts_toolkit": REQUIRED_SMARTS_TOOLKIT,
        "required_smarts_toolkit_version": REQUIRED_SMARTS_TOOLKIT_VERSION,
        "inherited_warhead_rule_field_count": 12,
        "inherited_warhead_rule_fields": list(WARHEAD_RULE_FIELDS),
        "proposal_field_count": len(PROPOSAL_FIELDS),
        "proposal_fields": list(PROPOSAL_FIELDS),
        "proposal_statuses": list(PROPOSAL_STATUSES),
        "proposal_atom_id_namespace": PROPOSAL_ATOM_ID_NAMESPACE,
        "proposal_bond_id_encoding": PROPOSAL_BOND_ID_ENCODING,
        "proposal_field_type_contract": PROPOSAL_FIELD_TYPE_CONTRACT,
        "proposal_hash_excluded_field": PROPOSAL_HASH_EXCLUDED_FIELD,
        "proposal_hash_canonical_json_contract": PROPOSAL_HASH_CANONICAL_JSON_CONTRACT,
        "proposal_record_count": 0,
        "contract_count": len(result.contract_rows),
        "candidate_class_count": len(rows),
        "current11_sample_count": 11 if success else 0,
        "authority_gap_row_count": len(result.gap_rows),
        "local_reaction_center_rule_available_count": count("local_reaction_center_rule_available"),
        "parent_heavy_atom_authority_available_count": count("parent_heavy_atom_authority_available"),
        "parent_heavy_bond_authority_available_count": count("parent_heavy_bond_authority_available"),
        "reactive_parent_atom_mapping_available_count": count("reactive_parent_atom_mapping_available"),
        "pre_reaction_leaving_group_semantics_available_count": count(
            "pre_reaction_leaving_group_semantics_available"
        ),
        "leaving_group_class_count": result.leaving_group_class_count,
        "zero_leaving_group_class_count": result.zero_leaving_group_class_count,
        "required_leaving_group_total_atom_count": result.required_leaving_group_total_atom_count,
        "complete_warhead_atom_set_available_count": count("complete_warhead_atom_set_available"),
        "exact_one_attachment_boundary_available_count": count("exact_one_attachment_boundary_available"),
        "deterministic_atom_map_policy_available_count": count("deterministic_atom_map_policy_available"),
        "SMARTS_query_semantics_frozen_count": count("SMARTS_query_semantics_frozen"),
        "candidate_warhead_smarts_materialized_count": count("candidate_warhead_smarts_materialized"),
        "warhead_atom_set_and_boundary_proposal_materialization_ready_count": count(
            "ready_for_warhead_atom_set_and_attachment_boundary_proposal_materialization"
        ),
        "candidate_warhead_smarts_materialization_ready_count": count(
            "ready_for_candidate_warhead_smarts_materialization"
        ),
        "SMARTS_human_review_ready_count": count("ready_for_SMARTS_human_review"),
        "candidate_smarts_gate_design_completed": success,
        "candidate_smarts_materialized": False,
        "review_package_materialized": success,
        "ready_for_family_identity_review_execution": success,
        "ready_for_rule_topology_review_execution": success,
        "ready_for_sample_assignment_review_execution": success,
        "ready_for_warhead_atom_set_and_attachment_boundary_proposal_materialization": success,
        "ready_for_candidate_warhead_smarts_materialization": False,
        "ready_for_SMARTS_review_execution": False,
        "ready_for_complete_human_review_execution": False,
        "approved_reaction_family_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "approved_warhead_smarts_count": 0,
        "human_gold_review_completed_count": 0,
        "training_label_approved_count": 0,
        "ready_for_role_proposal_generation": False,
        "ready_for_minimal_seed_proposal_generation": False,
        "ready_for_mask_materialization": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "role_annotation_materialized": False,
        "minimal_seed_materialized": False,
        "mask_materialized": False,
        "tensor_materialized": False,
        "model_changed": False,
        "training_used": False,
        "warhead_type_model_head_integrated": False,
        "warhead_type_loss_integrated": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "phase_a_predecessor_and_authority_validation_passed": success,
        "phase_b_contract_readiness_and_gap_validation_passed": success,
        "transaction_succeeded": success,
        "failure_mutation_count": len(result.failure_rows),
        "failure_mutations_all_fail_closed": all(
            row["fails_closed"] and row["verified"] for row in result.failure_rows
        ),
        "local_reaction_center_semantics": "radius_1_reaction_center_lower_bound_only",
        "complete_warhead_semantics": "not_available",
        "blocking_reasons": list(result.blocking_reasons),
        "recommended_manual_action": (
            "perform_real_human_review_of_materialized_family_topology_and_sample_assignment_packages"
            if success
            else "resolve_covapie_cys_sg_candidate_smarts_gate_design_blockers_v1"
        ),
        "recommended_engineering_next_step": (
            "materialize_covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1"
            if success
            else "resolve_covapie_cys_sg_candidate_smarts_gate_design_blockers_v1"
        ),
        "recommended_next_step": (
            "materialize_covapie_current11_pre_reaction_warhead_atom_set_and_attachment_boundary_proposals_v1"
            if success
            else "resolve_covapie_cys_sg_candidate_smarts_gate_design_blockers_v1"
        ),
        "output_sha256": {
            name: sha256(payload) for name, payload in payloads_without_manifest.items()
        },
    }


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    result = build_result(repo_root)
    payloads = {
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, result.source_rows),
        CONTRACT_FILE: _csv_bytes(CONTRACT_COLUMNS, result.contract_rows),
        READINESS_FILE: _csv_bytes(READINESS_COLUMNS, result.readiness_rows),
        GAP_FILE: _csv_bytes(GAP_COLUMNS, result.gap_rows),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, result.failure_rows),
    }
    payloads[MANIFEST_FILE] = (
        json.dumps(_manifest(result, payloads), sort_keys=True, indent=2, ensure_ascii=True)
        + "\n"
    ).encode("utf-8")
    return payloads


def materialize(repo_root: Path) -> dict[str, bytes]:
    payloads = build_evidence_payloads(repo_root)
    destination = repo_root / OUTPUT_ROOT
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (destination / name).write_bytes(payload)
    return payloads


def main() -> int:
    materialize(Path(__file__).resolve().parents[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
