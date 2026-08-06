"""Read-only Current11 routing tensor-projection contract gate V1."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import subprocess
from collections import Counter
from pathlib import Path
from typing import Mapping, NoReturn, Sequence

from covalent_ext import (
    covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_formal_materializer_v2
    as _v2,
)


__all__ = (
    "build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1",
)

ERROR_TOKEN = (
    "COVAPIE_CURRENT11_DATASET_ROUTING_SIDECAR_TENSOR_PROJECTION_"
    "CONTRACT_GATE_V1_ERROR"
)
SCHEMA_VERSION = "covapie_current11_routing_tensor_projection_contract_v1"
GATE_REPORT_SCHEMA_VERSION = (
    "covapie_current11_routing_tensor_projection_contract_gate_report_v1"
)
UNIQUE_STRUCTURE = "task_major_typed_projection_bundle"
BASE_COMMIT = "2c9af439780a78c2fcbb10f5fe0d629bd1a57847"
BASE_TREE = "42ace949001bf3e99c5449a6e407177804dc69df"
BASE_PARENT = "6f3444df7e62517e2e9dfca646a8d8ce9ddc2e56"
BASE_SUBJECT = "add CovaPIE Current11 GPFS atomic alias routing sidecar materializer v2"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 routing tensor projection contract gate v1"
)
BRANCH = "main"
CANONICAL_RELATIVE = (
    "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
)
CANONICAL_READLINK = (
    ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-"
    "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c-"
    "1fd8cf5823427e941b11c7b2560a336f"
)
CANONICAL_IDENTITY = (49, 69442074366)
OBJECT_IDENTITY = (49, 69442074217)
FORMAL_AGGREGATE_SHA256 = (
    "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"
)
V2_MODULE_PATH = (
    "src/covalent_ext/covapie_current11_dataset_partial_supervision_routing_"
    "sidecar_gpfs_atomic_alias_formal_materializer_v2.py"
)
V2_MODULE_SHA256 = (
    "a0feaf4686d3eedda0b7e807a0471efa2aa5b6e952a3514e51170c62fe22e047"
)
BUILDER_COMMIT = "903c074805a22d7c899fd23c22ebfb3ac2e811e5"
BUILDER_MODULE_SHA256 = (
    "1be932e473107a2944cf916c288580b614c7b6710556ca54c099d742971344a5"
)
V1_MATERIALIZER_COMMIT = "6f3444df7e62517e2e9dfca646a8d8ce9ddc2e56"
V1_MATERIALIZER_SHA256 = (
    "5d189c0451a1aad515932bd4e537de9378b79fcbc2987f671d069e0db857aada"
)

MODULE_PATH = (
    "src/covalent_ext/"
    "covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1.py"
)
SCRIPT_PATH = (
    "scripts/"
    "check_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1.py"
)
TEST_PATH = (
    "tests/"
    "test_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1.py"
)
GUIDE_PATH = (
    "docs/"
    "covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1_guide.md"
)
CANDIDATE_PATHS = tuple(sorted((MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)))

ARTIFACT_NAMES = (
    "current11_routing_tensor_projection_contract_manifest.json",
    "current11_routing_tensor_projection_task_schema.csv",
    "current11_routing_tensor_projection_state_encoding.csv",
    "current11_routing_tensor_projection_gate_report.json",
)
CONTRACT_ARTIFACT_NAMES = ARTIFACT_NAMES[:3]
CONTRACT_DIGEST_DOMAIN_TAG = (
    b"COVAPIE_CURRENT11_ROUTING_TENSOR_PROJECTION_CONTRACT_GATE_V1\0"
)

FORMAL_ARTIFACTS = {
    "current11_dataset_partial_supervision_routing_records.csv": (
        69557,
        276,
        "751e32f46ab386604386167bdffd38f762472bbc9fdff4af7167a979ac68af03",
    ),
    "current11_dataset_partial_supervision_task_coverage.csv": (
        1883,
        26,
        "ee8bfe7f0bed65e6858ae318695470abc3a92de3ca72d2548e2d5c4e950aa2b7",
    ),
    "current11_dataset_partial_supervision_sample_coverage.csv": (
        1445,
        12,
        "7cd2ecd99caca09f94019d543793f70de6d9cb86ff431fbd49782b76b2814b5e",
    ),
    "current11_dataset_partial_supervision_routing_manifest.json": (
        43109,
        1044,
        "3a2c2e8170f20ed0a8ea97798a5945ec846cd36d81fe950aa58fee6311984a7d",
    ),
}

SAMPLE_ORDER = (
    ("CYS_SG_SAMPLE_INDEX_000001", "6BV6", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000002", "6BV8", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000003", "6BV5", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000004", "1AEC", "E64"),
    ("CYS_SG_SAMPLE_INDEX_000005", "1AIM", "ZYA"),
    ("CYS_SG_SAMPLE_INDEX_000006", "1AU3", "PCM"),
    ("CYS_SG_SAMPLE_INDEX_000007", "1AU4", "INP"),
    ("CYS_SG_SAMPLE_INDEX_000008", "1AYU", "INA"),
    ("CYS_SG_SAMPLE_INDEX_000009", "1AYV", "IN6"),
    ("CYS_SG_SAMPLE_INDEX_000010", "1AYW", "IN3"),
    ("CYS_SG_SAMPLE_INDEX_000011", "1B02", "UFP"),
)
TASK_ORDER = (
    "sample_identity_supervision",
    "explicit_covalent_event_supervision",
    "ligand_residue_atom_pair_supervision",
    "covalent_link_bond_order_supervision",
    "warhead_type_supervision",
    "reaction_family_supervision",
    "warhead_boundary_supervision",
    "canonical_mask_warhead_only",
    "canonical_mask_linker_plus_warhead",
    "canonical_mask_scaffold_plus_warhead",
    "canonical_mask_scaffold_only",
    "canonical_mask_scaffold_plus_linker_plus_warhead",
    "observed_complex_geometry_supervision",
    "pre_covalent_geometry_supervision",
    "post_covalent_geometry_supervision",
    "complete_post_state_graph_supervision",
    "reaction_atom_map_supervision",
    "formed_edge_supervision",
    "broken_edge_supervision",
    "bond_order_delta_supervision",
    "formal_charge_delta_supervision",
    "protonation_transfer_supervision",
    "leaving_group_supervision",
    "reversibility_supervision",
    "full_transformation_supervision",
)
ELIGIBILITY_STATES = (
    "admissible_now",
    "admissible_as_observed_geometry_only",
    "candidate_only_not_authoritative",
    "blocked_missing_evidence",
    "blocked_state_ambiguity",
    "blocked_missing_human_approval",
    "not_applicable",
)
STATE_COUNTS = {
    "admissible_now": 44,
    "admissible_as_observed_geometry_only": 11,
    "candidate_only_not_authoritative": 55,
    "blocked_missing_evidence": 103,
    "blocked_state_ambiguity": 7,
    "blocked_missing_human_approval": 55,
    "not_applicable": 0,
}
EVIDENCE_SCOPE_VOCABULARY = (
    "CANONICAL_SAMPLE_IDENTITY",
    "EXPLICIT_BINARY_COVALENT_EVENT",
    "EXPLICIT_LIGAND_RESIDUE_ATOM_PAIR",
    "AUTHORITATIVE_LINK_BOND_ORDER_ABSENT",
    "CANDIDATE_FAMILY_OR_WARHEAD_TYPE",
    "REVIEWED_WARHEAD_BOUNDARY_ONLY",
    "CANONICAL_MASK_CONTRACT_WITHOUT_PRIMARY_ROLES",
    "OBSERVED_COMPLEX_COORDINATE_DISTANCE",
    "PRE_COVALENT_GEOMETRY_ABSENT",
    "POST_COVALENT_STATE_UNRESOLVED",
    "COMPLETE_POST_STATE_GRAPH_UNRESOLVED",
    "REACTION_ATOM_MAP_ABSENT",
    "CANDIDATE_FORMED_EDGE",
    "CANDIDATE_OR_AMBIGUOUS_BROKEN_EDGE",
    "BOND_ORDER_DELTA_ABSENT",
    "FORMAL_CHARGE_DELTA_ABSENT",
    "PROTONATION_TRANSFER_ABSENT",
    "CANDIDATE_LEAVING_GROUP",
    "SAMPLE_REVERSIBILITY_UNRESOLVED",
    "FULL_TRANSFORMATION_UNRESOLVED",
)
BLOCKING_REASON_VOCABULARY = (
    "NONE",
    "OBSERVED_COMPLEX_GEOMETRY_ONLY",
    "AUTHORITATIVE_LINK_BOND_ORDER_MISSING",
    "CANDIDATE_LABEL_NOT_APPROVED",
    "PRIMARY_ROLE_AUTHORITY_INCOMPLETE",
    "PRE_COVALENT_GEOMETRY_MISSING",
    "DEDICATED_TRANSFORMATION_REVIEW_MISSING",
    "POST_STATE_AMBIGUOUS",
    "REACTION_ATOM_MAP_MISSING",
    "CANDIDATE_TRANSFORMATION_SEMANTICS_ONLY",
    "BOND_ORDER_DELTA_MISSING",
    "FORMAL_CHARGE_DELTA_MISSING",
    "PROTONATION_TRANSFER_MISSING",
    "SAMPLE_SPECIFIC_REVERSIBILITY_MISSING",
    "FULL_TRANSFORMATION_INCOMPLETE",
)
CANONICAL_MASKS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (
        4,
        "scaffold_plus_linker_plus_warhead",
        "C",
        ("scaffold", "linker", "warhead"),
        (),
    ),
)

RECORD_COLUMNS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "semantic_task_name",
    "eligibility_state",
    "direct_authority_found",
    "evidence_scope",
    "blocking_reason_code",
    "supporting_source_ids_json",
    "dedicated_transformation_review_available",
    "availability_mask_required",
    "current_runtime_consumer_available",
    "training_loss_authorized",
)
TASK_COVERAGE_COLUMNS = (
    "semantic_task_name",
    "admissible_now_sample_count",
    "observed_geometry_only_sample_count",
    "candidate_only_sample_count",
    "blocked_missing_evidence_sample_count",
    "blocked_state_ambiguity_sample_count",
    "blocked_missing_human_approval_sample_count",
    "not_applicable_sample_count",
    "total_sample_count",
    "current_runtime_consumer_available",
    "training_loss_authorized",
)
SAMPLE_COVERAGE_COLUMNS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "admissible_now_task_count",
    "observed_geometry_only_task_count",
    "candidate_only_task_count",
    "blocked_missing_evidence_task_count",
    "blocked_state_ambiguity_task_count",
    "blocked_missing_human_approval_task_count",
    "not_applicable_task_count",
    "total_task_count",
    "dedicated_transformation_review_available",
    "dataset_level_routing_derivable",
    "current_runtime_consumer_available",
    "training_loss_authorized",
    "ready_for_tensor_materialization",
    "ready_for_training",
)
FORMAL_MANIFEST_FIELDS = (
    "base_commit",
    "blocking_reason_vocabulary",
    "canonical_mask_semantics",
    "canonical_sample_identity",
    "dedicated_transformation_review_samples",
    "eligibility_state_vocabulary",
    "evidence_scope_vocabulary",
    "global_state_counts",
    "readiness",
    "repository_lifecycle",
    "routing_record_count",
    "sample_count",
    "sample_coverage_summary",
    "samples_missing_dedicated_transformation_review",
    "schema_version",
    "semantic_task_count",
    "semantic_task_names",
    "sidecar_files_excluding_manifest",
    "source_bindings",
    "task_coverage_summary",
    "unit_000001_parity",
)

TASK_SCHEMA_COLUMNS = (
    "task_index",
    "semantic_task_name",
    "task_family",
    "task_scope",
    "source_record_fields",
    "source_authority_type",
    "eligibility_states",
    "current11_state_distribution_json",
    "direct_authoritative_payload",
    "observed_geometry_only",
    "candidate_only",
    "missing_evidence",
    "missing_human_approval",
    "state_ambiguity",
    "data_availability_permitted_after_payload_validation",
    "semantic_training_label_permitted",
    "loss_allowed_now",
    "blocking_reason_summary",
    "provenance_requirement",
    "proposed_value_dtype",
    "proposed_logical_shape",
    "missing_representation",
    "applicability_representation",
    "downstream_consumer_boundary",
    "required_authority_or_audit",
)

# These rows explicitly freeze section 4 of the approved design report.  The eight
# boolean flags are, in order: direct, observed-only, candidate-only, missing
# evidence, missing approval, ambiguity, availability-permitted, semantic-label.
_TASK_SEMANTICS = (
    ("identity", "sample", "final-index sample_index_row_id,pdb_id,ligand_comp_id", "canonical final index", ("admissible_now",), {"admissible_now": 11}, (1,0,0,0,0,0,1,0), "NONE", "src+hash+record", "UTF-8 uint8 bytes + int64 offsets", "3 named strings x [S]", "empty UTF-8 byte range plus false validity", "bool[S]=true", "metadata/join only; never model/loss", "executable UTF-8 encoder and identity cross-check"),
    ("event", "sample binary", "event conn_id,conn_type_id,event_source,event_status,residue_atom_name,ligand_atom_name; pair/mapping validation flags", "validated explicit _struct_conn event", ("admissible_now",), {"admissible_now": 11}, (1,0,0,0,0,0,1,1), "NONE", "src+hash+record", "bool", "[S]", "finite false placeholder plus false validity", "bool[S]=true", "future auxiliary sidecar only", "executable payload extractor; separate loss authorization"),
    ("atom pair", "one or more pairs/sample", "pair residue_comp_id,residue_atom_name,ligand_atom_name,explicit_bond_authority_class,canonical_record_valid; mapping entity_role,mapping_outcome,matched_row_index_0based", "validated explicit bond plus exact-one atom-table mapping", ("admissible_now",), {"admissible_now": 11}, (1,0,0,0,0,0,1,1), "NONE", "src+hash+record plus locator namespace and atom-table SHA/order", "int64 values + offsets + bool entry validity", "values[P,2]; offsets[S+1]; current P=11", "empty ragged interval; -1 forbidden when valid", "bool[S]=true", "metadata row indices; explicit remap before model; no loss", "row-order/index-base/locator gate and downstream remap"),
    ("bond attribute", "positive covalent pair", "event lacks authoritative order; family formed_bond_order is candidate context", "no authoritative link-bond-order source", ("blocked_missing_evidence",), {"blocked_missing_evidence": 11}, (0,0,0,1,0,0,0,0), "AUTHORITATIVE_LINK_BOND_ORDER_MISSING", "src+hash+record", "int16 approved bond-order category ID", "[S]", "-1 plus false validity", "bool[S]=true", "future pair/edge head only", "authoritative sample-level link bond order and closed vocabulary"),
    ("chemical category", "sample", "candidate_warhead_type_semantic_name,review_status,training_label_status,training_label_approved; binding approval flags", "candidate assignment explicitly not approved", ("candidate_only_not_authoritative",), {"candidate_only_not_authoritative": 11}, (0,0,1,0,0,0,0,0), "CANDIDATE_LABEL_NOT_APPROVED", "src+hash+record; candidate provenance isolated", "authoritative int32; candidate UTF-8 bytes+offsets", "[S]", "-1 or empty UTF-8 plus false validity", "bool[S]=true", "candidate metadata only; never embedding lookup", "human approval, closed vocabulary, unknown policy, feature-semantics audit"),
    ("reaction category", "sample", "candidate_reaction_family_id,reaction_family_authority_status,reaction_family_identity_explicitly_attested", "candidate family/binding/worklist", ("candidate_only_not_authoritative",), {"candidate_only_not_authoritative": 11}, (0,0,1,0,0,0,0,0), "CANDIDATE_LABEL_NOT_APPROVED", "src+hash+record; candidate provenance isolated", "authoritative int32; candidate UTF-8 bytes+offsets", "[S]", "-1 or empty UTF-8 plus false validity", "bool[S]=true", "candidate metadata only", "human family attestation and closed vocabulary"),
    ("ligand boundary", "ligand-internal atom set/boundaries", "reviewed_warhead_atom_ids,exact_one_attachment_boundary_authority_available,exact_two_attachment_boundaries_authority_available,authority_status,sample_quarantined", "active unified human-reviewed boundary authority", ("admissible_now",), {"admissible_now": 11}, (1,0,0,0,0,0,1,1), "NONE", "src+hash+record plus authority-view record identity", "UTF-8 ragged uint8 bytes + int64 offsets + bool entry validity", "atom-ID tokens and boundary pairs [K,2] by sample", "empty ragged or UTF-8 range plus false validity", "bool[S]=true", "ligand-internal metadata; not ligand-protein pair/model input", "executable atom-ID namespace/mapping audit before numeric adapter"),
    ("generation mask", "retained ligand atoms", "Exact5 truth semantic_name,display_alias; role and boundary authority", "mask semantics authoritative; primary role authority incomplete", ("blocked_missing_human_approval",), {"blocked_missing_human_approval": 11}, (0,0,0,0,1,0,0,0), "PRIMARY_ROLE_AUTHORITY_INCOMPLETE", "src+hash+record plus role partition/version", "bool values + int64 sample offsets", "ragged [N_ligand_total]; offsets[S+1]", "empty ragged or finite false placeholder", "bool[S]=true", "future generation-mask adapter only; not availability/loss", "complete human-approved Exact3 roles and retained-atom mapping"),
    ("generation mask", "retained ligand atoms", "same Exact5 truth/role/boundary fields", "mask semantics authoritative; primary role authority incomplete", ("blocked_missing_human_approval",), {"blocked_missing_human_approval": 11}, (0,0,0,0,1,0,0,0), "PRIMARY_ROLE_AUTHORITY_INCOMPLETE", "src+hash+record plus role partition/version", "bool values + int64 sample offsets", "ragged [N_ligand_total]; offsets[S+1]", "empty ragged or finite false placeholder", "bool[S]=true", "generation-mask sidecar only", "complete human-approved Exact3 roles and retained-atom mapping"),
    ("generation mask", "retained ligand atoms", "same Exact5 truth/role/boundary fields", "mask semantics authoritative; primary role authority incomplete", ("blocked_missing_human_approval",), {"blocked_missing_human_approval": 11}, (0,0,0,0,1,0,0,0), "PRIMARY_ROLE_AUTHORITY_INCOMPLETE", "src+hash+record plus role partition/version", "bool values + int64 sample offsets", "ragged [N_ligand_total]; offsets[S+1]", "empty ragged or finite false placeholder", "bool[S]=true", "generation-mask sidecar only", "complete human-approved Exact3 roles and retained-atom mapping"),
    ("generation mask", "retained ligand atoms", "same Exact5 truth/role/boundary fields; B3 exact row", "mask semantics authoritative; B3 mandatory", ("blocked_missing_human_approval",), {"blocked_missing_human_approval": 11}, (0,0,0,0,1,0,0,0), "PRIMARY_ROLE_AUTHORITY_INCOMPLETE", "src+hash+record; long name authoritative", "bool values + int64 sample offsets", "ragged [N_ligand_total]; offsets[S+1]", "empty ragged or finite false placeholder", "bool[S]=true", "generation-mask sidecar only", "complete role authority and B3 regression"),
    ("generation mask", "retained ligand atoms", "same Exact5 fields; Task-C seed remains orthogonal", "mask semantics authoritative; primary role authority incomplete", ("blocked_missing_human_approval",), {"blocked_missing_human_approval": 11}, (0,0,0,0,1,0,0,0), "PRIMARY_ROLE_AUTHORITY_INCOMPLETE", "src+hash+record plus seed-sidecar lineage", "bool values + int64 sample offsets", "ragged [N_ligand_total]; offsets[S+1]", "empty ragged or finite false placeholder", "bool[S]=true", "generation-mask sidecar only; seed cannot alter base mask/loss", "roles plus separately approved minimal-seed/anchor authority"),
    ("geometry", "explicit observed pair", "bond_distance_angstrom,validation_status,residue_atom_name,ligand_atom_name; final-index distance cross-check", "recorded observed complex geometry", ("admissible_as_observed_geometry_only",), {"admissible_as_observed_geometry_only": 11}, (1,1,0,0,0,0,1,1), "OBSERVED_COMPLEX_GEOMETRY_ONLY", "src+hash+record plus units/pair identity", "float32", "[S,1] observed distance in angstrom", "finite zero placeholder plus false validity; zero is never a distance", "bool[S]=true", "geometry sidecar only; no bond/order/post-state inference", "finite positive unit/pair checks; no semantic promotion"),
    ("geometry", "explicit pair, pre state", "no payload source", "absent", ("blocked_missing_evidence",), {"blocked_missing_evidence": 11}, (0,0,0,1,0,0,0,0), "PRE_COVALENT_GEOMETRY_MISSING", "routing record and future direct authority", "float32", "[S,1] pre-state pair distance in angstrom", "finite zero placeholder plus false validity", "bool[S]=true", "future geometry sidecar only", "canonical pre-state structure/pair/frame/unit authority"),
    ("geometry", "explicit pair, post state", "post_reaction_authority_status,reviewed_transformation_version,transformation_review_decision,review_completed", "absent for 9; explicit ambiguity for 2", ("blocked_missing_evidence","blocked_state_ambiguity"), {"blocked_missing_evidence": 9,"blocked_state_ambiguity": 2}, (0,0,0,1,0,1,0,0), "DEDICATED_TRANSFORMATION_REVIEW_MISSING or POST_STATE_AMBIGUOUS", "src+hash+record plus review version", "float32", "[S,1] authoritative post-state pair distance in angstrom", "finite zero placeholder plus false validity", "bool[S]=true", "future geometry sidecar only", "resolved post-state authority; observed distance cannot satisfy"),
    ("graph", "full post-state molecular graph", "post-state/review fields; reviewed transformation fields empty", "absent or ambiguous", ("blocked_missing_evidence","blocked_state_ambiguity"), {"blocked_missing_evidence": 9,"blocked_state_ambiguity": 2}, (0,0,0,1,0,1,0,0), "DEDICATED_TRANSFORMATION_REVIEW_MISSING or POST_STATE_AMBIGUOUS", "src+hash+record plus graph schema/version", "typed ragged int64 node IDs/edge index + int16 attributes", "nodes[N], edges[E,2], node/edge offsets[S+1]", "empty ragged or -1 plus false validity", "bool[S]=true", "future graph auxiliary consumer only", "authoritative post graph, atom namespace, bond/charge vocabularies"),
    ("atom mapping", "pre-post atoms", "reviewed_atom_map_contract_json empty", "missing transformation authority", ("blocked_missing_evidence",), {"blocked_missing_evidence": 11}, (0,0,0,1,0,0,0,0), "REACTION_ATOM_MAP_MISSING", "src+hash+record plus pre/post atom namespace", "int64 values + offsets + bool entry validity", "values[M,2]; offsets[S+1]", "empty ragged or -1 plus false validity", "bool[S]=true", "future transformation sidecar only", "reviewed exact atom map and namespace contract"),
    ("edge change", "mapped atoms", "formed_bond_order,candidate_reaction_delta_class; canonical pair fields", "candidate transformation semantics", ("candidate_only_not_authoritative",), {"candidate_only_not_authoritative": 11}, (0,0,1,0,0,0,0,0), "CANDIDATE_TRANSFORMATION_SEMANTICS_ONLY", "src+hash+record; candidate buffer isolated", "authoritative int64[E,2]; candidate same typed buffer", "ragged edges + offsets[S+1]", "empty ragged or -1 plus false validity", "bool[S]=true", "candidate metadata only", "reviewed formed edges and atom map; bond order separate"),
    ("edge change", "mapped atoms", "candidate-broken-edge availability; reviewed_broken_edges_json empty", "candidate for 10; ambiguous for 1", ("candidate_only_not_authoritative","blocked_state_ambiguity"), {"candidate_only_not_authoritative": 10,"blocked_state_ambiguity": 1}, (0,0,1,0,0,1,0,0), "CANDIDATE_TRANSFORMATION_SEMANTICS_ONLY or POST_STATE_AMBIGUOUS", "src+hash+record; candidate buffer only for candidate state", "authoritative int64[E,2]; candidate same typed buffer", "ragged edges + offsets[S+1]", "empty ragged or -1 plus false validity", "bool[S]=true", "candidate metadata only; ambiguity retained separately", "reviewed broken edges, atom map, ambiguity resolution"),
    ("edge attribute delta", "mapped union edges", "transformation review fields absent", "missing", ("blocked_missing_evidence",), {"blocked_missing_evidence": 11}, (0,0,0,1,0,0,0,0), "BOND_ORDER_DELTA_MISSING", "src+hash+record plus edge identity", "int16 signed delta aligned to edge buffer", "[E] plus edge offsets[S+1]", "-1 plus false validity", "bool[S]=true", "future transformation sidecar only", "reviewed pre/post orders and closed bond-order vocabulary"),
    ("node attribute delta", "mapped atoms", "transformation review fields absent", "missing", ("blocked_missing_evidence",), {"blocked_missing_evidence": 11}, (0,0,0,1,0,0,0,0), "FORMAL_CHARGE_DELTA_MISSING", "src+hash+record plus atom-map identity", "int16 signed charge delta", "[N] plus atom offsets[S+1]", "-1 plus false validity", "bool[S]=true", "future transformation sidecar only", "reviewed pre/post formal charges and atom map"),
    ("node attribute delta", "mapped atoms", "transformation review fields absent", "missing", ("blocked_missing_evidence",), {"blocked_missing_evidence": 11}, (0,0,0,1,0,0,0,0), "PROTONATION_TRANSFER_MISSING", "src+hash+record plus atom-map/H semantics", "int16 signed hydrogen-count delta", "[N] plus atom offsets[S+1]", "-1 plus false validity", "bool[S]=true", "future transformation sidecar only", "explicit authority and H/implicit-H semantics"),
    ("atom subset", "pre-state mapped atoms", "candidate_leaving_group_summary,candidate_reaction_delta_class", "candidate only", ("candidate_only_not_authoritative",), {"candidate_only_not_authoritative": 11}, (0,0,1,0,0,0,0,0), "CANDIDATE_TRANSFORMATION_SEMANTICS_ONLY", "src+hash+record; candidate buffer isolated", "authoritative int64 atom IDs; candidate UTF-8 or mapped IDs", "ragged [L]; offsets[S+1]", "empty ragged or -1 plus false validity", "bool[S]=true", "candidate metadata only", "reviewed leaving atoms, atom map, approved atom namespace"),
    ("reaction category", "sample", "reviewed_reversibility_semantics,review_completed; UNIT provenance", "candidate for 1; missing for 10", ("candidate_only_not_authoritative","blocked_missing_evidence"), {"candidate_only_not_authoritative": 1,"blocked_missing_evidence": 10}, (0,0,1,1,0,0,0,0), "CANDIDATE_TRANSFORMATION_SEMANTICS_ONLY or SAMPLE_SPECIFIC_REVERSIBILITY_MISSING", "src+hash+record; candidate buffer only for candidate state", "authoritative int32; candidate UTF-8 bytes+offsets", "[S]", "-1 or empty UTF-8 plus false validity", "bool[S]=true", "candidate metadata only", "reviewed sample-specific semantics and closed vocabulary"),
    ("composite transformation", "full sample transformation", "reviewed atom-map/formed/broken/reversibility/decision fields incomplete", "absent or ambiguous", ("blocked_missing_evidence","blocked_state_ambiguity"), {"blocked_missing_evidence": 9,"blocked_state_ambiguity": 2}, (0,0,0,1,0,1,0,0), "FULL_TRANSFORMATION_INCOMPLETE or POST_STATE_AMBIGUOUS", "src+hash+record plus all component digests", "typed transformation sub-bundle", "component ragged buffers with shared [S+1] offsets/refs", "empty ragged or -1 plus false validity", "bool[S]=true", "future composite consumer only; no implicit derivation", "complete reviewed transformation and consistency audit across tasks 14-23"),
)

STATE_ENCODING_COLUMNS = (
    "code",
    "eligibility_state",
    "applicability_rule",
    "authoritative_payload_rule",
    "candidate_payload_rule",
    "observed_geometry_rule",
    "data_availability_rule",
    "state_ambiguity_rule",
    "human_approval_rule",
    "loss_rule",
)
STATE_ENCODING_RULES = (
    ("routing metadata only; never a label; applicability=true", "permitted only after authoritative payload validation", "forbidden", "no promotion", "permitted only after payload/source validation; code alone is insufficient", "false", "not applicable", "explicit authority only; current V1 false"),
    ("routing metadata only; never a label; applicability=true", "restricted observed-distance payload only", "forbidden", "only recorded observed geometry; no semantic promotion", "permitted only after restricted geometry validation; code alone is insufficient", "false", "not applicable", "explicit authority only; current V1 false"),
    ("routing metadata only; never a label; applicability=true", "forbidden", "permitted only in physically separate candidate payload", "cannot become authoritative geometry", "false", "false", "candidate cannot substitute for approval", "explicit authority only; current V1 false"),
    ("routing metadata only; never a label; applicability=true", "forbidden: missing evidence", "forbidden", "no promotion", "false", "false", "not applicable", "explicit authority only; current V1 false"),
    ("routing metadata only; never a label; applicability=true", "forbidden: state ambiguity; never normalize to missing", "forbidden", "no promotion", "false", "true; remains distinct from missing", "not applicable", "explicit authority only; current V1 false"),
    ("routing metadata only; never a label; applicability=true", "forbidden: human approval missing", "candidate cannot substitute for human authority", "no promotion", "false", "false", "true; explicit human approval required", "explicit authority only; current V1 false"),
    ("routing metadata only; never a label; applicability=false", "forbidden: task not applicable", "forbidden", "no promotion", "false; not encoded as missing or zero label", "false", "not applicable", "explicit authority only; current V1 false"),
)

PROJECTION_FIELD_NAMES = (
    "schema_version",
    "source_lineage",
    "sample_order",
    "task_order",
    "canonical_mask_semantics",
    "eligibility_state_code",
    "evidence_scope_code",
    "blocking_reason_code",
    "direct_authority_mask",
    "data_availability_mask",
    "applicability_mask",
    "candidate_only_mask",
    "observed_geometry_only_mask",
    "state_ambiguity_mask",
    "human_approval_missing_mask",
    "loss_authorization_mask",
    "runtime_consumer_available_mask",
    "task_payloads",
    "task_payload_validity",
    "task_payload_entry_validity",
    "candidate_payloads",
    "candidate_payload_validity",
    "task_payload_provenance",
    "projection_readiness",
)

_FIELD_CORE = (
    ("scalar", "UTF-8 scalar", 0, "scalar", (), [SCHEMA_VERSION], "none", "exact schema match", "projection contract", False, False),
    ("typed metadata record", "typed metadata container", "N/A", "scalar record", (), "closed lineage fields", "none", "all content identities verified before projection", "canonical/object/manifest/materializers", False, False),
    ("vector", "UTF-8 vector serialization", 1, "[S]", ("sample",), "Exact11 IDs", "none", "nonempty unique order equals formal manifest", "manifest canonical_sample_identity", False, False),
    ("vector", "UTF-8 vector serialization", 1, "[T]", ("task",), "Exact25 long semantic names", "none", "aliases forbidden as authority", "manifest semantic_task_names", False, False),
    ("typed record vector", "typed mask semantic record", 1, "[M]", ("canonical_mask",), "Exact5 long-name records", "none", "B3 index 3; no sixth mask; Exact3 primary roles", "manifest plus canonical truth contract", False, False),
    ("matrix", "uint8", 2, "[S,T]", ("sample","task"), "integers 0..6", "none", "reversible Exact7 mapping and exact counts", "records eligibility_state", False, False),
    ("matrix", "uint8", 2, "[S,T]", ("sample","task"), "closed evidence-scope codes", "none", "decode equals record value", "records plus manifest vocabulary", False, False),
    ("matrix", "uint8", 2, "[S,T]", ("sample","task"), "closed blocking-reason codes", "none", "decode equals record value", "records plus manifest vocabulary", False, False),
    ("matrix", "bool", 2, "[S,T]", ("sample","task"), [False,True], "none", "not sufficient for availability", "records direct_authority_found", False, False),
    ("matrix", "bool", 2, "[S,T]", ("sample","task"), [False,True], "false until future payload validation", "requires payload validity and code 0 or 1", "records plus validated payloads", False, False),
    ("matrix", "bool", 2, "[S,T]", ("sample","task"), [False,True], "false iff not applicable", "current Exact275 true; not materialized here", "eligibility code", False, False),
    ("matrix", "bool", 2, "[S,T]", ("sample","task"), [False,True], "false outside code 2", "true iff code 2", "eligibility code", False, False),
    ("matrix", "bool", 2, "[S,T]", ("sample","task"), [False,True], "false outside code 1", "true iff code 1; only task 12 now", "eligibility code", False, False),
    ("matrix", "bool", 2, "[S,T]", ("sample","task"), [False,True], "false outside code 4", "true iff code 4; never fold into missing", "eligibility code", False, False),
    ("matrix", "bool", 2, "[S,T]", ("sample","task"), [False,True], "false outside code 5", "true iff code 5; candidate cannot substitute", "eligibility code", False, False),
    ("matrix", "bool", 2, "[S,T]", ("sample","task"), [False], "current Exact275 false", "any true in V1 is fatal", "records training_loss_authorized", False, False),
    ("matrix", "bool", 2, "[S,T]", ("sample","task"), [False], "current Exact275 false", "any true in V1 is fatal", "records current_runtime_consumer_available", False, False),
    ("ordered typed map", "task-specific exact dtype", "N/A", "Exact25 task entries", ("task",), "authoritative or restricted observed typed buffers", "separate validity; finite placeholders never imply validity", "candidate values forbidden; exact dtype/shape per task", "bound authoritative sources", False, False),
    ("matrix", "bool", 2, "[S,T]", ("sample","task"), [False,True], "false until verified payload", "true only for validated code 0 or 1 payload", "payload validators plus eligibility", False, False),
    ("ordered bool-buffer map", "bool", "N/A", "aligned task buffers", ("task","entry"), [False,True], "empty when unavailable", "exact offset/value alignment", "payload validators", False, False),
    ("ordered typed map", "task-specific exact dtype", "N/A", "Exact25 task entries", ("task",), "candidate metadata buffers only", "empty outside candidate cells", "physically separate from authoritative payloads", "candidate sources", False, False),
    ("matrix", "bool", 2, "[S,T]", ("sample","task"), [False,True], "false until candidate extraction validation", "true implies code 2; not materialized here", "eligibility plus candidate validators", False, False),
    ("typed metadata map", "UTF-8 and integer metadata", "N/A", "[S,T] records plus source table", ("sample","task"), "closed source IDs and locators", "none for invalid payload", "every valid entry has bound provenance; no absolute paths", "records source IDs plus manifest bindings", False, False),
    ("exact status record", "bool and closed status", "N/A", "scalar record", (), "closed readiness values", "none", "no readiness inferred from counts", "contract gate", False, False),
)


def _fail() -> NoReturn:
    raise ValueError(ERROR_TOKEN)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object, *, compact: bool = False) -> bytes:
    separators = (",", ":") if compact else None
    text = json.dumps(
        value,
        sort_keys=True,
        indent=None if compact else 2,
        ensure_ascii=True,
        allow_nan=False,
        separators=separators,
    )
    return (text + "\n").encode("utf-8")


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=columns,
        extrasaction="raise",
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _require_root(path: Path) -> Path:
    if type(path) is not type(Path()) or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail()
    return path


def _read_regular(path: Path, *, expected: tuple[int, int, str]) -> bytes:
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    expected_bytes, expected_lines, expected_sha = expected
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or len(payload) != expected_bytes
        or payload.count(b"\n") != expected_lines
        or _sha256(payload) != expected_sha
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\0" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
    ):
        _fail()
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(ERROR_TOKEN) from error
    return payload


def _csv_rows(payload: bytes, expected_columns: Sequence[str]) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        rows = list(reader)
    except (csv.Error, UnicodeDecodeError) as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        tuple(reader.fieldnames or ()) != tuple(expected_columns)
        or not rows
        or any(None in row or tuple(row) != tuple(expected_columns) for row in rows)
    ):
        _fail()
    return rows


def _strict_bool(value: object) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    _fail()


def _strict_nonnegative_int(value: object) -> int:
    if type(value) is not str or not value.isascii() or not value.isdigit():
        _fail()
    parsed = int(value)
    if str(parsed) != value:
        _fail()
    return parsed


def _path_item(path: Path, *, follow: bool = False) -> tuple[object, ...]:
    metadata = path.stat() if follow else path.lstat()
    payload: bytes | None = None
    if stat.S_ISREG(metadata.st_mode):
        payload = path.read_bytes()
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_mtime_ns),
        None if payload is None else _sha256(payload),
    )


def _formal_snapshot(canonical: Path) -> dict[str, object]:
    try:
        parent = canonical.parent
        link_text = os.readlink(canonical)
        object_path = parent / link_text
        parent_inventory = tuple(sorted(os.listdir(parent)))
        object_inventory = tuple(sorted(os.listdir(object_path)))
        leaves = {name: _path_item(object_path / name) for name in object_inventory}
        return {
            "parent": _path_item(parent),
            "parent_inventory": parent_inventory,
            "canonical": _path_item(canonical),
            "readlink": link_text,
            "object": _path_item(object_path),
            "object_inventory": object_inventory,
            "leaves": leaves,
        }
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error


def _validate_v2_source(repo_root: Path) -> None:
    path = repo_root / V2_MODULE_PATH
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or _sha256(payload) != V2_MODULE_SHA256
    ):
        _fail()


def _validate_v2_summary(summary: object) -> None:
    expected_artifacts = {
        name: {"bytes": size, "lines": lines, "sha256": digest}
        for name, (size, lines, digest) in FORMAL_ARTIFACTS.items()
    }
    if (
        type(summary) is not dict
        or summary.get("operation") != "check"
        or summary.get("canonical_entry_type") != "relative_symlink"
        or summary.get("canonical_symlink_target") != CANONICAL_READLINK
        or summary.get("canonical_identity")
        != {"st_dev": CANONICAL_IDENTITY[0], "st_ino": CANONICAL_IDENTITY[1]}
        or summary.get("object_identity")
        != {"st_dev": OBJECT_IDENTITY[0], "st_ino": OBJECT_IDENTITY[1]}
        or summary.get("aggregate_sha256") != FORMAL_AGGREGATE_SHA256
        or summary.get("artifact_file_count") != 4
        or summary.get("artifacts") != expected_artifacts
        or summary.get("sample_count") != 11
        or summary.get("semantic_task_count") != 25
        or summary.get("routing_record_count") != 275
        or summary.get("global_state_counts") != STATE_COUNTS
        or summary.get("readiness", {}).get("training_loss_authorized") is not False
        or summary.get("readiness", {}).get("runtime_consumer_available") is not False
        or summary.get("readiness", {}).get("ready_for_training") is not False
    ):
        _fail()


def _read_formal(canonical: Path) -> dict[str, bytes]:
    try:
        if os.readlink(canonical) != CANONICAL_READLINK:
            _fail()
        canonical_metadata = canonical.lstat()
        object_path = canonical.parent / CANONICAL_READLINK
        object_metadata = object_path.lstat()
        if (
            not stat.S_ISLNK(canonical_metadata.st_mode)
            or (canonical_metadata.st_dev, canonical_metadata.st_ino)
            != CANONICAL_IDENTITY
            or stat.S_ISLNK(object_metadata.st_mode)
            or not stat.S_ISDIR(object_metadata.st_mode)
            or stat.S_IMODE(object_metadata.st_mode) != 0o755
            or (object_metadata.st_dev, object_metadata.st_ino) != OBJECT_IDENTITY
            or tuple(sorted(os.listdir(object_path)))
            != tuple(sorted(FORMAL_ARTIFACTS))
        ):
            _fail()
        return {
            name: _read_regular(object_path / name, expected=expected)
            for name, expected in FORMAL_ARTIFACTS.items()
        }
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error


def _validate_formal(payloads: Mapping[str, bytes]) -> dict[str, object]:
    if type(payloads) is not dict or tuple(payloads) != tuple(FORMAL_ARTIFACTS):
        _fail()
    records = _csv_rows(
        payloads["current11_dataset_partial_supervision_routing_records.csv"],
        RECORD_COLUMNS,
    )
    task_coverage = _csv_rows(
        payloads["current11_dataset_partial_supervision_task_coverage.csv"],
        TASK_COVERAGE_COLUMNS,
    )
    sample_coverage = _csv_rows(
        payloads["current11_dataset_partial_supervision_sample_coverage.csv"],
        SAMPLE_COVERAGE_COLUMNS,
    )
    try:
        manifest = json.loads(
            payloads[
                "current11_dataset_partial_supervision_routing_manifest.json"
            ].decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(ERROR_TOKEN) from error
    expected_samples = [
        {"sample_index_row_id": sample, "pdb_id": pdb, "ligand_comp_id": ligand}
        for sample, pdb, ligand in SAMPLE_ORDER
    ]
    expected_masks = [
        {"semantic_name": semantic, "display_alias": alias}
        for _index, semantic, alias, _generated, _fixed in CANONICAL_MASKS
    ]
    if (
        type(manifest) is not dict
        or tuple(manifest) != FORMAL_MANIFEST_FIELDS
        or manifest.get("schema_version")
        != "covapie_current11_dataset_partial_supervision_routing_sidecar_v1"
        or manifest.get("sample_count") != 11
        or manifest.get("semantic_task_count") != 25
        or manifest.get("routing_record_count") != 275
        or manifest.get("canonical_sample_identity") != expected_samples
        or manifest.get("semantic_task_names") != list(TASK_ORDER)
        or manifest.get("eligibility_state_vocabulary") != list(ELIGIBILITY_STATES)
        or manifest.get("evidence_scope_vocabulary")
        != list(EVIDENCE_SCOPE_VOCABULARY)
        or manifest.get("blocking_reason_vocabulary")
        != list(BLOCKING_REASON_VOCABULARY)
        or manifest.get("canonical_mask_semantics") != expected_masks
        or manifest.get("global_state_counts") != STATE_COUNTS
        or manifest.get("readiness", {}).get("training_loss_authorized") is not False
        or manifest.get("readiness", {}).get("runtime_consumer_available") is not False
        or manifest.get("readiness", {}).get("ready_for_tensor_materialization")
        is not False
        or manifest.get("readiness", {}).get("ready_for_training") is not False
    ):
        _fail()
    if len(CANONICAL_MASKS) != 5 or CANONICAL_MASKS[3][1:3] != (
        "scaffold_only",
        "B3",
    ):
        _fail()
    primary_roles = {role for row in CANONICAL_MASKS for role in row[3] + row[4]}
    if primary_roles != {"scaffold", "linker", "warhead"}:
        _fail()

    if len(records) != 275 or len(task_coverage) != 25 or len(sample_coverage) != 11:
        _fail()
    expected_keys = [
        (sample[0], task) for sample in SAMPLE_ORDER for task in TASK_ORDER
    ]
    actual_keys = [
        (row["sample_index_row_id"], row["semantic_task_name"]) for row in records
    ]
    if actual_keys != expected_keys or len(set(actual_keys)) != 275:
        _fail()
    source_ids = set(manifest["source_bindings"])
    state_counter: Counter[str] = Counter()
    per_task: dict[str, Counter[str]] = {task: Counter() for task in TASK_ORDER}
    per_sample: dict[str, Counter[str]] = {sample[0]: Counter() for sample in SAMPLE_ORDER}
    for index, row in enumerate(records):
        sample = SAMPLE_ORDER[index // 25]
        if tuple(row[key] for key in ("sample_index_row_id", "pdb_id", "ligand_comp_id")) != sample:
            _fail()
        state = row["eligibility_state"]
        if state not in ELIGIBILITY_STATES:
            _fail()
        if row["evidence_scope"] not in EVIDENCE_SCOPE_VOCABULARY:
            _fail()
        if row["blocking_reason_code"] not in BLOCKING_REASON_VOCABULARY:
            _fail()
        try:
            supporting = json.loads(row["supporting_source_ids_json"])
        except json.JSONDecodeError as error:
            raise ValueError(ERROR_TOKEN) from error
        if (
            type(supporting) is not list
            or any(type(item) is not str or item not in source_ids for item in supporting)
            or len(supporting) != len(set(supporting))
            or json.dumps(supporting, separators=(",", ":"), ensure_ascii=True)
            != row["supporting_source_ids_json"]
            or any(Path(item).is_absolute() for item in supporting)
        ):
            _fail()
        for field in (
            "direct_authority_found",
            "dedicated_transformation_review_available",
            "availability_mask_required",
            "current_runtime_consumer_available",
            "training_loss_authorized",
        ):
            value = _strict_bool(row[field])
            if field == "availability_mask_required" and value is not True:
                _fail()
            if field in (
                "current_runtime_consumer_available",
                "training_loss_authorized",
            ) and value is not False:
                _fail()
        state_counter[state] += 1
        per_task[row["semantic_task_name"]][state] += 1
        per_sample[row["sample_index_row_id"]][state] += 1
    if dict(state_counter) != {state: STATE_COUNTS[state] for state in ELIGIBILITY_STATES if STATE_COUNTS[state]}:
        _fail()

    task_count_fields = (
        ("admissible_now_sample_count", "admissible_now"),
        ("observed_geometry_only_sample_count", "admissible_as_observed_geometry_only"),
        ("candidate_only_sample_count", "candidate_only_not_authoritative"),
        ("blocked_missing_evidence_sample_count", "blocked_missing_evidence"),
        ("blocked_state_ambiguity_sample_count", "blocked_state_ambiguity"),
        ("blocked_missing_human_approval_sample_count", "blocked_missing_human_approval"),
        ("not_applicable_sample_count", "not_applicable"),
    )
    for index, row in enumerate(task_coverage):
        task = TASK_ORDER[index]
        if row["semantic_task_name"] != task or _strict_nonnegative_int(row["total_sample_count"]) != 11:
            _fail()
        for field, state in task_count_fields:
            if _strict_nonnegative_int(row[field]) != per_task[task][state]:
                _fail()
        if _strict_bool(row["current_runtime_consumer_available"]) or _strict_bool(row["training_loss_authorized"]):
            _fail()

    sample_count_fields = tuple(
        (field.replace("sample_count", "task_count"), state)
        for field, state in task_count_fields
    )
    for index, row in enumerate(sample_coverage):
        sample = SAMPLE_ORDER[index]
        if tuple(row[key] for key in ("sample_index_row_id", "pdb_id", "ligand_comp_id")) != sample or _strict_nonnegative_int(row["total_task_count"]) != 25:
            _fail()
        for field, state in sample_count_fields:
            if _strict_nonnegative_int(row[field]) != per_sample[sample[0]][state]:
                _fail()
        for field in (
            "current_runtime_consumer_available",
            "training_loss_authorized",
            "ready_for_tensor_materialization",
            "ready_for_training",
        ):
            if _strict_bool(row[field]):
                _fail()
        if not _strict_bool(row["dataset_level_routing_derivable"]):
            _fail()

    return {
        "manifest": manifest,
        "records": records,
        "task_coverage": task_coverage,
        "sample_coverage": sample_coverage,
        "state_counts": {state: state_counter[state] for state in ELIGIBILITY_STATES},
        "task_state_counts": per_task,
    }


def _task_schema_rows(validated: Mapping[str, object]) -> list[dict[str, str]]:
    if len(_TASK_SEMANTICS) != 25 or tuple(validated["task_state_counts"]) != TASK_ORDER:
        _fail()
    rows: list[dict[str, str]] = []
    for index, (task, semantic) in enumerate(zip(TASK_ORDER, _TASK_SEMANTICS, strict=True)):
        (
            family, scope, source_fields, authority_type, states, distribution,
            flags, blocking, provenance, dtype, shape, missing, applicability,
            consumer, required,
        ) = semantic
        actual_distribution = {
            state: validated["task_state_counts"][task][state]
            for state in ELIGIBILITY_STATES
            if validated["task_state_counts"][task][state]
        }
        if distribution != actual_distribution or any(state not in ELIGIBILITY_STATES for state in states):
            _fail()
        direct, observed, candidate, missing_evidence, missing_approval, ambiguity, availability, semantic_label = flags
        row = {
            "task_index": str(index),
            "semantic_task_name": task,
            "task_family": family,
            "task_scope": scope,
            "source_record_fields": source_fields,
            "source_authority_type": authority_type,
            "eligibility_states": ";".join(states),
            "current11_state_distribution_json": json.dumps(distribution, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
            "direct_authoritative_payload": str(bool(direct)).lower(),
            "observed_geometry_only": str(bool(observed)).lower(),
            "candidate_only": str(bool(candidate)).lower(),
            "missing_evidence": str(bool(missing_evidence)).lower(),
            "missing_human_approval": str(bool(missing_approval)).lower(),
            "state_ambiguity": str(bool(ambiguity)).lower(),
            "data_availability_permitted_after_payload_validation": str(bool(availability)).lower(),
            "semantic_training_label_permitted": str(bool(semantic_label)).lower(),
            "loss_allowed_now": "false",
            "blocking_reason_summary": blocking,
            "provenance_requirement": provenance,
            "proposed_value_dtype": dtype,
            "proposed_logical_shape": shape,
            "missing_representation": missing,
            "applicability_representation": applicability,
            "downstream_consumer_boundary": consumer,
            "required_authority_or_audit": required,
        }
        if tuple(row) != TASK_SCHEMA_COLUMNS:
            _fail()
        rows.append(row)
    return rows


def _state_encoding_rows() -> list[dict[str, str]]:
    rows = []
    for code, (state, rules) in enumerate(zip(ELIGIBILITY_STATES, STATE_ENCODING_RULES, strict=True)):
        row = dict(zip(STATE_ENCODING_COLUMNS, (str(code), state, *rules), strict=True))
        rows.append(row)
    return rows


def _validate_task_schema_rows(
    rows: object, validated: Mapping[str, object]
) -> None:
    expected = _task_schema_rows(validated)
    if (
        type(rows) is not list
        or rows != expected
        or len(rows) != 25
        or any(type(row) is not dict or tuple(row) != TASK_SCHEMA_COLUMNS for row in rows)
        or [row["task_index"] for row in rows] != [str(index) for index in range(25)]
        or [row["semantic_task_name"] for row in rows] != list(TASK_ORDER)
        or any(row["loss_allowed_now"] != "false" for row in rows)
        or any(
            row["candidate_only"] == "true"
            and row["data_availability_permitted_after_payload_validation"]
            != "false"
            for row in rows
        )
        or [row["semantic_task_name"] for row in rows if row["observed_geometry_only"] == "true"]
        != ["observed_complex_geometry_supervision"]
    ):
        _fail()


def _projection_fields() -> list[dict[str, object]]:
    if len(PROJECTION_FIELD_NAMES) != 24 or len(_FIELD_CORE) != 24:
        _fail()
    fields = []
    for name, core in zip(PROJECTION_FIELD_NAMES, _FIELD_CORE, strict=True):
        (
            container, dtype, rank, shape, axes, allowed, missing, invariants,
            source, model_allowed, loss_allowed,
        ) = core
        field = {
            "name": name,
            "container_kind": container,
            "dtype": dtype,
            "rank": rank,
            "logical_shape": shape,
            "axes": list(axes),
            "allowed_values": allowed,
            "missing_semantics": missing,
            "invariants": invariants,
            "formal_source": source,
            "model_input_allowed_now": model_allowed,
            "loss_participation_allowed_now": loss_allowed,
        }
        fields.append(field)
    return fields


def _contract_manifest() -> dict[str, object]:
    masks = [
        {
            "mask_index": index,
            "semantic_name": semantic,
            "display_alias": alias,
            "generated_roles": list(generated),
            "fixed_roles": list(fixed),
        }
        for index, semantic, alias, generated, fixed in CANONICAL_MASKS
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "unique_structure": UNIQUE_STRUCTURE,
        "dimensions": {"S": 11, "T": 25, "M": 5},
        "source_lineage": {
            "canonical_state_relative_path": CANONICAL_RELATIVE,
            "canonical_entry_kind": "one-component same-parent relative symlink",
            "canonical_readlink": CANONICAL_READLINK,
            "formal_aggregate_sha256": FORMAL_AGGREGATE_SHA256,
            "formal_exact4_sha256": {name: spec[2] for name, spec in FORMAL_ARTIFACTS.items()},
            "builder_commit": BUILDER_COMMIT,
            "builder_module_sha256": BUILDER_MODULE_SHA256,
            "v1_materializer_commit": V1_MATERIALIZER_COMMIT,
            "v1_materializer_module_sha256": V1_MATERIALIZER_SHA256,
            "v2_materializer_commit": BASE_COMMIT,
            "v2_materializer_module_sha256": V2_MODULE_SHA256,
            "implementation_lineage_report_sha256": "4521844114e89a862c1194c238d6b58c6e89210cda4099cfd1c3c16b14b1b161",
            "runtime_depends_on_implementation_lineage_report": False,
        },
        "sample_order": [
            {"sample_index": index, "sample_index_row_id": sample, "pdb_id": pdb, "ligand_comp_id": ligand}
            for index, (sample, pdb, ligand) in enumerate(SAMPLE_ORDER)
        ],
        "task_order": [
            {"task_index": index, "semantic_task_name": task}
            for index, task in enumerate(TASK_ORDER)
        ],
        "canonical_mask_semantics": masks,
        "primary_role_vocabulary": ["scaffold", "linker", "warhead"],
        "seed_anchor_is_orthogonal_to_exact5": True,
        "generation_mask_availability_loss_are_independent_axes": True,
        "eligibility_state_code_order": [
            {"code": index, "eligibility_state": state}
            for index, state in enumerate(ELIGIBILITY_STATES)
        ],
        "evidence_scope_code_order": [
            {"code": index, "evidence_scope": value}
            for index, value in enumerate(EVIDENCE_SCOPE_VOCABULARY)
        ],
        "blocking_reason_code_order": [
            {"code": index, "blocking_reason": value}
            for index, value in enumerate(BLOCKING_REASON_VOCABULARY)
        ],
        "current_eligibility_state_counts": dict(STATE_COUNTS),
        "projection_fields": _projection_fields(),
        "current_all_false_authority_contract": {
            "shape": [11, 25],
            "loss_authorization_true_count": 0,
            "runtime_consumer_available_true_count": 0,
            "loss_authorization_mask_materialized": False,
            "runtime_consumer_available_mask_materialized": False,
        },
        "projection_instance_contract": {
            "projection_instance_materialized": False,
            "tensor_materialized": False,
            "task_payloads_materialized": False,
            "candidate_payloads_materialized": False,
            "task_payload_validity_materialized": False,
            "data_availability_mask_materialized": False,
            "eligibility_permitted_authoritative_or_observed_count": 55,
            "candidate_eligible_count": 55,
            "counts_are_permissions_not_materialized_payloads": True,
        },
        "serialization_rules": {
            "finite_placeholders_never_imply_validity": True,
            "nan_or_infinity_forbidden": True,
            "implicit_casts_forbidden": True,
            "bool_as_integer_index_forbidden": True,
            "float_as_category_or_index_forbidden": True,
            "python_object_tensor_forbidden": True,
            "candidate_authority_promotion_forbidden": True,
            "observed_geometry_semantic_promotion_forbidden": True,
        },
        "future_projection_gate_requirements": [
            "validate every source binding and extractor version",
            "validate exact dtype rank shape axes offsets and entry validity",
            "validate task payload before data availability",
            "keep candidates physically separate from authoritative payloads",
            "require an explicit separately authorized downstream adapter",
            "require an explicit feature-semantics re-audit before training",
        ],
        "feature_semantics_boundary": {
            "step12d_smoke_legality_verified": True,
            "step12d_final_feature_semantics_contract": False,
            "step12d_training_readiness_authority": False,
            "unknown_atom_feature_policy": "UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED",
            "feature_semantics_known": False,
            "feature_semantics_reaudit_required_before_training": True,
        },
        "projection_readiness": {
            "tensor_projection_contract_designed": True,
            "tensor_projection_contract_gate_implemented": True,
            "projection_instance_materialized": False,
            "tensor_materialized": False,
            "ready_for_tensor_projection_materialization": False,
            "ready_for_tensor_materialization": False,
            "ready_for_dataloader_integration": False,
            "ready_for_model_integration": False,
            "ready_for_training": False,
        },
    }


def _validate_artifact_bytes(name: str, payload: bytes) -> None:
    if (
        type(name) is not str
        or type(payload) is not bytes
        or len(payload) >= 1024 * 1024
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
        or b"\r" in payload
        or b"\0" in payload
        or payload.startswith(b"\xef\xbb\xbf")
        or b"NaN" in payload
        or b"Infinity" in payload
    ):
        _fail()
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(ERROR_TOKEN) from error


def _build_contract_artifacts(validated: Mapping[str, object]) -> dict[str, bytes]:
    manifest = _canonical_json(_contract_manifest())
    task_rows = _task_schema_rows(validated)
    _validate_task_schema_rows(task_rows, validated)
    task_schema = _csv_bytes(TASK_SCHEMA_COLUMNS, task_rows)
    state_encoding = _csv_bytes(STATE_ENCODING_COLUMNS, _state_encoding_rows())
    artifacts = dict(zip(CONTRACT_ARTIFACT_NAMES, (manifest, task_schema, state_encoding), strict=True))
    if type(artifacts) is not dict or tuple(artifacts) != CONTRACT_ARTIFACT_NAMES:
        _fail()
    for name, payload in artifacts.items():
        _validate_artifact_bytes(name, payload)
    return artifacts


def _contract_digest(artifacts: Mapping[str, bytes]) -> str:
    if type(artifacts) is not dict or tuple(artifacts) != CONTRACT_ARTIFACT_NAMES:
        _fail()
    digest = hashlib.sha256()
    digest.update(CONTRACT_DIGEST_DOMAIN_TAG)
    for name in CONTRACT_ARTIFACT_NAMES:
        encoded_name = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded_name).to_bytes(8, "big", signed=False))
        digest.update(encoded_name)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _run_git(repo_root: Path, arguments: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            ("git", *arguments), cwd=repo_root, check=False, capture_output=True
        )
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    if completed.returncode != 0 or completed.stderr:
        _fail()
    try:
        return completed.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise ValueError(ERROR_TOKEN) from error


def _git_commit_facts(repo_root: Path, commit: str) -> dict[str, object]:
    parents = _run_git(repo_root, ("show", "-s", "--format=%P", commit)).split()
    subject = _run_git(repo_root, ("show", "-s", "--format=%s", commit))
    names = tuple(sorted(filter(None, _run_git(repo_root, ("diff-tree", "--no-commit-id", "--name-only", "-r", commit)).splitlines())))
    statuses = {}
    for line in filter(None, _run_git(repo_root, ("diff-tree", "--no-commit-id", "--name-status", "-r", commit)).splitlines()):
        status_text, name = line.split("\t", 1)
        statuses[name] = status_text
    modes = {}
    blobs = {}
    for line in filter(None, _run_git(repo_root, ("ls-tree", commit, "--", *CANDIDATE_PATHS)).splitlines()):
        head, name = line.split("\t", 1)
        mode, kind, blob = head.split()
        if kind != "blob":
            _fail()
        modes[name], blobs[name] = mode, blob
    return {"parents": parents, "subject": subject, "names": names, "statuses": statuses, "modes": modes, "blobs": blobs}


def _validate_candidate_files(
    repo_root: Path, *, expected_blobs: Mapping[str, str] | None
) -> None:
    for relative in CANDIDATE_PATHS:
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ValueError(ERROR_TOKEN) from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\0" in payload
            or any(
                line.rstrip(b"\r\n").endswith((b" ", b"\t"))
                for line in payload.splitlines(keepends=True)
            )
        ):
            _fail()
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(ERROR_TOKEN) from error
        if expected_blobs is not None:
            staged = _run_git(repo_root, ("ls-files", "--stage", "--", relative))
            parts = staged.split()
            if (
                len(parts) < 4
                or parts[0] != "100644"
                or parts[1] != expected_blobs.get(relative)
                or _run_git(repo_root, ("hash-object", "--", relative))
                != expected_blobs.get(relative)
            ):
                _fail()


def _repository_lifecycle(repo_root: Path) -> dict[str, object]:
    head = _run_git(repo_root, ("rev-parse", "HEAD"))
    origin = _run_git(repo_root, ("rev-parse", "origin/main"))
    branch = _run_git(repo_root, ("branch", "--show-current"))
    counts = _run_git(repo_root, ("rev-list", "--left-right", "--count", "HEAD...origin/main")).split()
    if branch != BRANCH or len(counts) != 2:
        _fail()
    ahead, behind = map(int, counts)
    status = tuple(sorted(filter(None, _run_git(repo_root, ("status", "--porcelain=v1", "--untracked-files=all")).splitlines())))
    commits = tuple(filter(None, _run_git(repo_root, ("log", "--format=%H", "--all", "--", *CANDIDATE_PATHS)).splitlines()))
    common = {
        "base_commit": BASE_COMMIT,
        "future_formal_subject": FORMAL_COMMIT_SUBJECT,
        "candidate_paths": list(CANDIDATE_PATHS),
    }
    if not commits:
        if (
            head != BASE_COMMIT or origin != BASE_COMMIT or (ahead, behind) != (0, 0)
            or status != tuple(sorted(f"?? {path}" for path in CANDIDATE_PATHS))
        ):
            _fail()
        _validate_candidate_files(repo_root, expected_blobs=None)
        return {
            **common,
            "lifecycle_profile": "current11_routing_tensor_projection_contract_gate_v1_precommit_candidate",
            "formal_candidate_commit": "",
            "head": head,
            "origin_main": origin,
            "ahead": 0,
            "behind": 0,
        }
    if len(commits) != 1:
        _fail()
    commit = commits[0]
    facts = _git_commit_facts(repo_root, commit)
    if (
        facts["parents"] != [BASE_COMMIT]
        or facts["subject"] != FORMAL_COMMIT_SUBJECT
        or facts["names"] != CANDIDATE_PATHS
        or facts["statuses"] != {path: "A" for path in CANDIDATE_PATHS}
        or facts["modes"] != {path: "100644" for path in CANDIDATE_PATHS}
        or status
    ):
        _fail()
    _validate_candidate_files(repo_root, expected_blobs=facts["blobs"])
    ancestor_origin = subprocess.run(("git", "merge-base", "--is-ancestor", commit, "origin/main"), cwd=repo_root, check=False, capture_output=True)
    if ancestor_origin.stderr or ancestor_origin.returncode not in (0, 1):
        _fail()
    profile: str
    if ancestor_origin.returncode == 0:
        profile = "current11_routing_tensor_projection_contract_gate_v1_published_successor"
    elif head == commit and origin == BASE_COMMIT and (ahead, behind) == (1, 0):
        profile = "current11_routing_tensor_projection_contract_gate_v1_committed_unpushed"
    else:
        _fail()
    return {
        **common,
        "lifecycle_profile": profile,
        "formal_candidate_commit": commit,
        "head": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
    }


def _gate_report(
    *,
    artifacts: Mapping[str, bytes],
    digest: str,
    lifecycle: Mapping[str, object],
    formal_summary: Mapping[str, object],
) -> dict[str, object]:
    identities = []
    for order, name in enumerate(ARTIFACT_NAMES):
        item: dict[str, object] = {
            "artifact_index": order,
            "artifact_name": name,
            "contract_digest_participation": name in CONTRACT_ARTIFACT_NAMES,
        }
        if name in artifacts:
            item.update({"bytes": len(artifacts[name]), "lines": artifacts[name].count(b"\n"), "sha256": _sha256(artifacts[name])})
        else:
            item.update({"content_identity": "self_excluded", "lifecycle_variant": True})
        identities.append(item)
    readiness = {
        "formal_sidecar_materialized": True,
        "formal_sidecar_check_passed": True,
        "tensor_projection_contract_designed": True,
        "tensor_projection_contract_gate_implemented": True,
        "tensor_projection_contract_gate_passed": True,
        "projection_instance_materialized": False,
        "tensor_materialized": False,
        "runtime_consumer_available": False,
        "training_loss_authorized": False,
        "training_performed": False,
        "ready_for_tensor_projection_contract_gate_execution": True,
        "ready_for_tensor_projection_materialization": False,
        "ready_for_tensor_materialization": False,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }
    return {
        "schema_version": GATE_REPORT_SCHEMA_VERSION,
        "gate_status": "PASS_CONTRACT_ONLY",
        "contract_digest": digest,
        "artifact_file_count": 4,
        "artifact_identities": identities,
        "formal_sidecar_check_passed": True,
        "formal_double_check_identical": True,
        "formal_canonical_identity": dict(formal_summary["canonical_identity"]),
        "formal_canonical_readlink": formal_summary["canonical_symlink_target"],
        "formal_object_identity": dict(formal_summary["object_identity"]),
        "formal_aggregate_sha256": formal_summary["aggregate_sha256"],
        "formal_exact4_sha256": {name: spec[2] for name, spec in FORMAL_ARTIFACTS.items()},
        "sample_count": 11,
        "task_count": 25,
        "routing_record_count": 275,
        "mask_count": 5,
        "eligibility_state_counts": dict(STATE_COUNTS),
        "eligibility_permitted_authoritative_or_observed_count": 55,
        "candidate_eligible_count": 55,
        "loss_authorized_true_count": 0,
        "runtime_consumer_available_true_count": 0,
        "projection_instance_materialized": False,
        "tensor_materialized": False,
        "task_payloads_materialized": False,
        "candidate_payloads_materialized": False,
        "task_payload_validity_materialized": False,
        "data_availability_mask_materialized": False,
        "repository_lifecycle": dict(lifecycle),
        "readiness": readiness,
    }


def _build_impl(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    repository = _require_root(repo_root)
    state = _require_root(state_root)
    canonical = state / CANONICAL_RELATIVE
    before = _formal_snapshot(canonical)
    _validate_v2_source(repository)
    first_summary = _v2._verify_existing(
        repo_root=repository, state_root=state, output_path=canonical
    )
    second_summary = _v2._verify_existing(
        repo_root=repository, state_root=state, output_path=canonical
    )
    if first_summary != second_summary:
        _fail()
    _validate_v2_summary(first_summary)
    formal_payloads = _read_formal(canonical)
    validated = _validate_formal(formal_payloads)
    first_contract = _build_contract_artifacts(validated)
    second_contract = _build_contract_artifacts(validated)
    if first_contract != second_contract:
        _fail()
    digest = _contract_digest(first_contract)
    lifecycle = _repository_lifecycle(repository)
    report = _canonical_json(
        _gate_report(
            artifacts=first_contract,
            digest=digest,
            lifecycle=lifecycle,
            formal_summary=first_summary,
        )
    )
    _validate_artifact_bytes(ARTIFACT_NAMES[3], report)
    artifacts = dict(first_contract)
    artifacts[ARTIFACT_NAMES[3]] = report
    if type(artifacts) is not dict or tuple(artifacts) != ARTIFACT_NAMES or len(artifacts) != 4:
        _fail()
    after = _formal_snapshot(canonical)
    if before != after:
        _fail()
    return artifacts


def build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
    *, repo_root: Path, state_root: Path
) -> dict[str, bytes]:
    """Validate formal routing and return the contract Exact4 only in memory."""

    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except BaseException as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error
