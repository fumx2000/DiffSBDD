"""Metadata-only CovaPIE ligand-role and minimal-seed annotation contract V1."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import subprocess
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


BASE_COMMIT = "335a0320e8bd8ee125e51f927e6cd26d0c05707e"
BASE_PARENT = "160cdbda8800a535b5c0a81d501babfae9a8615b"
BASE_TREE = "6581ab0d6e28385300eaa0f6262b4b3ad5be8cfa"
BASE_SUBJECT = "add CovaPIE tensor label and loss-mask contract v1"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE ligand role and minimal seed annotation contract v1"
)
SCHEMA_VERSION = "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION

SOURCE_INVENTORY_FILE = "covapie_ligand_role_annotation_source_inventory.csv"
CONTRACT_REGISTRY_FILE = "covapie_ligand_role_and_seed_contract_registry.csv"
RULE_REGISTRY_FILE = "covapie_ligand_role_annotation_rule_registry.csv"
READINESS_MATRIX_FILE = "covapie_current11_role_annotation_input_readiness_matrix.csv"
FAILURE_MATRIX_FILE = "covapie_ligand_role_and_seed_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_INVENTORY_FILE,
    CONTRACT_REGISTRY_FILE,
    RULE_REGISTRY_FILE,
    READINESS_MATRIX_FILE,
    FAILURE_MATRIX_FILE,
    MANIFEST_FILE,
)

EXACT3_ROLES = ("scaffold", "linker", "warhead")
CANONICAL_TASKS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (
        4,
        "scaffold_plus_linker_plus_warhead",
        "C",
        ("scaffold", "linker", "warhead"),
        ("minimal_seed",),
    ),
)
ANNOTATION_STATUSES = (
    "proposal_only",
    "auto_exact",
    "gold_curated",
    "ambiguous_blocked",
)
HUMAN_REVIEW_DECISIONS = ("approve_gold", "revise", "quarantine")
PIPELINE = (
    "known_covalent_ligand_reactive_atom",
    "approved_reaction_family_warhead_rule",
    "exact_warhead_atom_set_proposal",
    "murcko_scaffold_core_proposal",
    "brics_supporting_boundary_evidence",
    "graph_connectivity_linker_proposal",
    "scaffold_role_remainder",
    "exit_vector_minimal_seed_proposal",
    "partition_gate",
    "ambiguity_quarantine",
    "current11_human_gold_review",
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
REVIEW_PACKAGE_FIELDS = (
    "sample_index_row_id",
    "ligand_atom_identity_table",
    "known_ligand_reactive_atom",
    "reaction_family_id",
    "warhead_rule_id",
    "warhead_atom_indices",
    "scaffold_core_proposal_indices",
    "scaffold_atom_indices",
    "linker_atom_indices",
    "scaffold_linker_boundary_bond",
    "linker_warhead_boundary_bond",
    "minimal_seed_atom_indices",
    "primary_anchor_atom",
    "direction_anchor_atom",
    "optional_plane_anchor_atom",
    "partition_gate_passed",
    "ambiguity_reasons",
    "annotation_status",
    "human_reviewer",
    "human_review_decision",
    "human_review_notes",
)
VISUALIZATION_LAYERS = (
    "scaffold",
    "linker",
    "warhead",
    "minimal_seed",
    "ligand_reactive_atom",
    "Cys_SG",
    "scaffold_linker_boundary_bond",
    "linker_warhead_boundary_bond",
)

PREDECESSOR_SOURCE = Path(
    "src/covalent_ext/covapie_tensor_label_and_loss_mask_contract_design_v1.py"
)
PREDECESSOR_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_tensor_label_and_loss_mask_contract_design_v1"
)
PREDECESSOR_MANIFEST = PREDECESSOR_ROOT / (
    "covapie_tensor_label_and_loss_mask_contract_design_manifest.json"
)
PREDECESSOR_REGISTRY = PREDECESSOR_ROOT / (
    "covapie_tensor_label_loss_mask_contract_registry.csv"
)
PREDECESSOR_ISSUES = PREDECESSOR_ROOT / (
    "covapie_tensor_label_loss_mask_issue_readiness_inventory.csv"
)
MASKING_SOURCE = Path("src/covalent_ext/masking.py")
SCHEMA_SOURCE = Path("src/covalent_ext/schema.py")
SCHEMA_DOC = Path("docs/covalent_data_schema.md")
B3_PROTOCOL = Path(
    "data/derived/covalent_small/b3_scaffold_only_mask_design_v0/"
    "b3_scaffold_only_mask_protocol.json"
)
FINAL_DATASET_INDEX = Path(
    "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/"
    "final_dataset_index.csv"
)
ATOM_MAPPING = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1/covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
HEAVY_DISPOSITION = Path(
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
    "covapie_heavy_atom_disposition_and_index_projection_matrix.csv"
)
SAMPLE_PROJECTION = Path(
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
    "covapie_sample_heavy_atom_projection_validation_matrix.csv"
)
TOPOLOGY_POLICY = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_restoration_policy_"
    "design_gate_v0/ligand_topology_restoration_policy_design_gate_report.csv"
)
TOPOLOGY_SUMMARY = Path(
    "docs/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_"
    "design_gate_v0_summary.md"
)
TOPOLOGY_DISPOSITION = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_008_topology_restoration_"
    "disposition_enum_contract_design_gate_v1/"
    "covapie_admit_008_topology_restoration_disposition_enum_registry.csv"
)
LIGAND_GRAPH_SCAFFOLD_EVIDENCE = Path(
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_batch_independence_evidence_"
    "materialization_smoke_v0/covapie_ligand_graph_scaffold_evidence.csv"
)

FROZEN_SHA256 = {
    PREDECESSOR_SOURCE: "3d2d03cda56dfb4a54370444f255f9bb0ab433aaeb837901e769098272ff51ac",
    Path("docs/covapie_tensor_label_and_loss_mask_contract_design_v1_summary.md"):
        "87b32f37c0514ab86067ffb3c07f5a3e6f4991a05797a93eb1ece3dbb2c437b6",
    PREDECESSOR_MANIFEST: "c0611d39074321744156c7ac3a527c54d4a84bd76c798a74fdbc1260b1bc6bcc",
    PREDECESSOR_REGISTRY: "dde4a96d1b38f1aa095fb8285616ff2877f91b2274be8bbf7a2e53e1250ec933",
    PREDECESSOR_ISSUES: "5a9dfcf4e9ebeba82adda99e72f956f16420424169ffbc8f6c3e85834e6ceaf8",
    MASKING_SOURCE: "48bfba93c95222da4d889a9e9e788826ca3577b9126aa9260e26e0e948bb59c5",
    SCHEMA_SOURCE: "71d05490e558c8618c13ca2c23d31d4b5c31789e476920fbaeb8344ac007a9b1",
    SCHEMA_DOC: "d0f11a805ef314273ab9291d68dc9a8260a1885efdb8a89a168edab628983f1f",
    B3_PROTOCOL: "21023f93a15204c2c3cd377af9d2e81fcde9f90fc5442e59b5d883e842985175",
    FINAL_DATASET_INDEX: "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
    ATOM_MAPPING: "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45",
    HEAVY_DISPOSITION: "b53f438edffab32f78d07df839b8c8437ec4223e31bd8a8885deedf32497b4be",
    SAMPLE_PROJECTION: "63f1df49d9a6f4e0efbee6c8bb474deabaedea9cef91f27d2cf49f7caeee6f96",
    TOPOLOGY_POLICY: "e10301238d5da3e81820a091381c3d105a4544dea1c481bb1cfda134efc7138f",
    TOPOLOGY_SUMMARY: "e061c748fe7553c0545181225795d1d052922adff327e5e78a323ba2a168f7bd",
    TOPOLOGY_DISPOSITION: "38e41ef09b62848e55e6d43fa2ee65ecc3b24378fd8ac9ca72fd2e313261556a",
    LIGAND_GRAPH_SCAFFOLD_EVIDENCE:
        "982a9f89a89d3a4ad6a3e468cfd16d2fdfd5435cbf6d593e086fbd7fadd3ec73",
}

SOURCE_COLUMNS = (
    "source_path",
    "sha256",
    "source_role",
    "evidence_class",
    "provides_actual_current11_value",
    "schema_only",
    "scope_note",
    "verified",
)
CONTRACT_COLUMNS = (
    "contract_id",
    "semantic_name",
    "contract_category",
    "input_authority",
    "derivation_rule",
    "value_type",
    "index_space",
    "cardinality",
    "validity_semantics",
    "ambiguity_semantics",
    "current11_availability",
    "status",
    "blocking_reason",
    "verified",
)
RULE_COLUMNS = (
    "rule_id",
    "rule_name",
    "priority",
    "rule_status",
    "rule_semantics",
    "failure_reason",
    "fails_closed",
    "verified",
)
READINESS_COLUMNS = (
    "sample_index_row_id",
    "retained_heavy_atom_mapping_available",
    "ligand_reactive_atom_available",
    "residue_reactive_atom_available",
    "pre_reaction_connectivity_available",
    "pre_reaction_bond_order_available",
    "reaction_family_label_available",
    "approved_warhead_rule_available",
    "murcko_input_ready",
    "brics_input_ready",
    "role_proposal_generation_ready",
    "minimal_seed_proposal_generation_ready",
    "human_gold_review_completed",
    "blocking_reasons",
    "verified",
)
FAILURE_COLUMNS = (
    "failure_case",
    "mutation_signature",
    "mutated_fields",
    "expected_reasons",
    "observed_reasons",
    "expected_reasons_verified",
    "fails_closed",
    "ready_for_role_annotation_proposal_generation",
    "ready_for_mask_materialization",
    "ready_for_model_integration",
    "ready_for_training",
    "verified",
)


@dataclass(frozen=True)
class AnnotationScenario:
    reactive_atom_present: bool = True
    reactive_atom_in_ligand: bool = True
    pre_reaction_graph_present: bool = True
    bond_orders_present: bool = True
    reaction_family_present: bool = True
    approved_warhead_rule_present: bool = True
    warhead_match_count: int = 1
    warhead_distinct_set_count: int = 1
    warhead_match_includes_reactive_atom: bool = True
    warhead_nonempty: bool = True
    warhead_boundary_count: int = 1
    scaffold_core_or_fallback_present: bool = True
    scaffold_proposals_unique: bool = True
    ringless_fallback_used: bool = False
    ringless_review_completed: bool = True
    linker_bridge_count: int = 1
    direct_attachment_present: bool = False
    direct_attachment_admitted: bool = False
    warhead_side_component_explained: bool = True
    disconnected_residual_present: bool = False
    partition_disjoint: bool = True
    partition_exhaustive: bool = True
    scaffold_nonempty: bool = True
    linker_nonempty: bool = True
    scaffold_linker_boundary_count: int = 1
    seed_subset_scaffold: bool = True
    seed_overlaps_linker: bool = False
    seed_overlaps_warhead: bool = False
    seed_connected: bool = True
    seed_has_primary_anchor: bool = True
    seed_size: int = 2
    canonical_ranking_deterministic: bool = True
    annotation_status: str = "gold_curated"
    training_eligible: bool = False
    human_review_completed: bool = True
    current11_marked_gold: bool = False
    canonical_masks: tuple[str, ...] = tuple(task[1] for task in CANONICAL_TASKS)
    execution_boundary_crossed: bool = False


@dataclass(frozen=True)
class ScenarioObservation:
    valid: bool
    reasons: tuple[str, ...]
    ready_for_role_annotation_proposal_generation: bool
    ready_for_mask_materialization: bool
    ready_for_model_integration: bool
    ready_for_training: bool


@dataclass(frozen=True)
class ContractDecision:
    schema_version: str
    design_outcome: str
    contract_design_completed: bool
    ready_for_current11_role_annotation_proposal_generation: bool
    ready_for_current11_minimal_seed_proposal_generation: bool
    ready_for_mask_materialization: bool
    ready_for_tensorization: bool
    ready_for_model_integration: bool
    ready_for_training: bool
    recommended_next_step: str


BASELINE_SCENARIO = AnnotationScenario()

SCENARIO_BOOL_FIELDS = (
    "reactive_atom_present",
    "reactive_atom_in_ligand",
    "pre_reaction_graph_present",
    "bond_orders_present",
    "reaction_family_present",
    "approved_warhead_rule_present",
    "warhead_match_includes_reactive_atom",
    "warhead_nonempty",
    "scaffold_core_or_fallback_present",
    "scaffold_proposals_unique",
    "ringless_fallback_used",
    "ringless_review_completed",
    "direct_attachment_present",
    "direct_attachment_admitted",
    "warhead_side_component_explained",
    "disconnected_residual_present",
    "partition_disjoint",
    "partition_exhaustive",
    "scaffold_nonempty",
    "linker_nonempty",
    "seed_subset_scaffold",
    "seed_overlaps_linker",
    "seed_overlaps_warhead",
    "seed_connected",
    "seed_has_primary_anchor",
    "canonical_ranking_deterministic",
    "training_eligible",
    "human_review_completed",
    "current11_marked_gold",
    "execution_boundary_crossed",
)
SCENARIO_NONNEGATIVE_INT_FIELDS = (
    "warhead_match_count",
    "warhead_distinct_set_count",
    "warhead_boundary_count",
    "linker_bridge_count",
    "scaffold_linker_boundary_count",
    "seed_size",
)

FAILURE_MUTATIONS: dict[str, dict[str, Any]] = {
    "reactive atom missing": {
        "fields": {"reactive_atom_present": False},
        "expected_reasons": ("known_reactive_atom_missing",),
    },
    "reactive atom outside ligand": {
        "fields": {"reactive_atom_in_ligand": False},
        "expected_reasons": ("reactive_atom_outside_ligand",),
    },
    "pre-reaction graph missing": {
        "fields": {"pre_reaction_graph_present": False},
        "expected_reasons": ("pre_reaction_graph_missing",),
    },
    "bond order missing": {
        "fields": {"bond_orders_present": False},
        "expected_reasons": ("pre_reaction_bond_orders_missing",),
    },
    "reaction family missing": {
        "fields": {"reaction_family_present": False},
        "expected_reasons": ("reaction_family_missing",),
    },
    "approved warhead rule missing": {
        "fields": {"approved_warhead_rule_present": False},
        "expected_reasons": ("approved_warhead_rule_missing",),
    },
    "warhead SMARTS no match": {
        "fields": {"warhead_match_count": 0},
        "expected_reasons": ("warhead_match_not_exact_one",),
    },
    "warhead SMARTS multiple distinct matches": {
        "fields": {
            "warhead_match_count": 2,
            "warhead_distinct_set_count": 2,
        },
        "expected_reasons": (
            "warhead_match_not_exact_one",
            "warhead_atom_set_not_exact_one",
        ),
    },
    "warhead match excludes known reactive atom": {
        "fields": {"warhead_match_includes_reactive_atom": False},
        "expected_reasons": ("warhead_match_excludes_reactive_atom",),
    },
    "warhead empty": {
        "fields": {"warhead_nonempty": False},
        "expected_reasons": ("warhead_empty",),
    },
    "warhead boundary missing": {
        "fields": {"warhead_boundary_count": 0},
        "expected_reasons": ("warhead_attachment_boundary_not_exact_one",),
    },
    "warhead boundary multiple": {
        "fields": {"warhead_boundary_count": 2},
        "expected_reasons": ("warhead_attachment_boundary_not_exact_one",),
    },
    "Murcko empty without fallback": {
        "fields": {"scaffold_core_or_fallback_present": False},
        "expected_reasons": ("scaffold_core_proposal_missing",),
    },
    "multiple scaffold proposals unresolved": {
        "fields": {"scaffold_proposals_unique": False},
        "expected_reasons": ("multiple_scaffold_proposals_unresolved",),
    },
    "ringless fallback marked auto-exact without review": {
        "fields": {
            "ringless_fallback_used": True,
            "ringless_review_completed": False,
            "annotation_status": "auto_exact",
        },
        "expected_reasons": (
            "ringless_fallback_review_missing",
            "ringless_fallback_auto_exact_forbidden",
        ),
    },
    "no linker bridge": {
        "fields": {"linker_bridge_count": 0},
        "expected_reasons": ("linker_bridge_not_exact_one",),
    },
    "multiple linker bridges": {
        "fields": {"linker_bridge_count": 2},
        "expected_reasons": ("linker_bridge_not_exact_one",),
    },
    "direct attachment no linker admitted in V1": {
        "fields": {
            "linker_bridge_count": 0,
            "linker_nonempty": False,
            "direct_attachment_present": True,
            "direct_attachment_admitted": True,
        },
        "expected_reasons": ("direct_attachment_no_linker_v1_quarantine",),
    },
    "warhead-only-side component unexplained": {
        "fields": {"warhead_side_component_explained": False},
        "expected_reasons": ("warhead_side_component_unexplained",),
    },
    "disconnected residual component": {
        "fields": {"disconnected_residual_present": True},
        "expected_reasons": ("disconnected_graph_blocked",),
    },
    "partition overlap": {
        "fields": {"partition_disjoint": False},
        "expected_reasons": ("partition_overlap",),
    },
    "partition incomplete": {
        "fields": {"partition_exhaustive": False},
        "expected_reasons": ("partition_incomplete",),
    },
    "scaffold empty": {
        "fields": {"scaffold_nonempty": False},
        "expected_reasons": ("scaffold_empty",),
    },
    "linker empty": {
        "fields": {"linker_nonempty": False},
        "expected_reasons": ("linker_empty",),
    },
    "boundary bond missing": {
        "fields": {"scaffold_linker_boundary_count": 0},
        "expected_reasons": ("scaffold_linker_boundary_not_exact_one",),
    },
    "boundary bond multiple": {
        "fields": {"scaffold_linker_boundary_count": 2},
        "expected_reasons": ("scaffold_linker_boundary_not_exact_one",),
    },
    "seed outside scaffold": {
        "fields": {"seed_subset_scaffold": False},
        "expected_reasons": ("seed_outside_scaffold",),
    },
    "seed overlaps linker": {
        "fields": {"seed_overlaps_linker": True},
        "expected_reasons": ("seed_overlaps_linker",),
    },
    "seed overlaps warhead": {
        "fields": {"seed_overlaps_warhead": True},
        "expected_reasons": ("seed_overlaps_warhead",),
    },
    "seed disconnected": {
        "fields": {"seed_connected": False},
        "expected_reasons": ("seed_disconnected",),
    },
    "seed missing primary anchor": {
        "fields": {"seed_has_primary_anchor": False},
        "expected_reasons": ("seed_missing_primary_anchor",),
    },
    "seed size outside 2-3": {
        "fields": {"seed_size": 4},
        "expected_reasons": ("seed_size_not_2_or_3",),
    },
    "canonical ranking nondeterministic": {
        "fields": {"canonical_ranking_deterministic": False},
        "expected_reasons": ("canonical_ranking_nondeterministic",),
    },
    "ambiguous annotation marked training eligible": {
        "fields": {
            "annotation_status": "ambiguous_blocked",
            "training_eligible": True,
        },
        "expected_reasons": (
            "non_gold_annotation_training_eligible",
            "ambiguous_annotation_training_eligible",
        ),
    },
    "proposal_only marked gold": {
        "fields": {
            "annotation_status": "proposal_only",
            "current11_marked_gold": True,
        },
        "expected_reasons": ("non_gold_status_marked_gold",),
    },
    "human review missing but current11 marked gold": {
        "fields": {
            "human_review_completed": False,
            "current11_marked_gold": True,
        },
        "expected_reasons": (
            "gold_curated_without_human_review",
            "current11_gold_without_human_review",
        ),
    },
    "B3 omitted": {
        "fields": {
            "canonical_masks": (
                "warhead_only",
                "linker_plus_warhead",
                "scaffold_plus_warhead",
                "scaffold_plus_linker_plus_warhead",
            )
        },
        "expected_reasons": (
            "scaffold_only_b3_missing",
            "canonical_exact5_masks_drift",
        ),
    },
    "sixth mask introduced": {
        "fields": {
            "canonical_masks": tuple(task[1] for task in CANONICAL_TASKS)
            + ("forbidden_sixth_mask",)
        },
        "expected_reasons": ("canonical_exact5_masks_drift",),
    },
    "execution boundary crossed": {
        "fields": {"execution_boundary_crossed": True},
        "expected_reasons": ("metadata_only_execution_boundary_crossed",),
    },
    "gold curated without human review": {
        "fields": {"human_review_completed": False},
        "expected_reasons": ("gold_curated_without_human_review",),
    },
    "auto exact marked training eligible": {
        "fields": {
            "annotation_status": "auto_exact",
            "training_eligible": True,
        },
        "expected_reasons": ("non_gold_annotation_training_eligible",),
    },
    "ringless fallback auto exact after review": {
        "fields": {
            "ringless_fallback_used": True,
            "annotation_status": "auto_exact",
        },
        "expected_reasons": ("ringless_fallback_auto_exact_forbidden",),
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
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace").strip())
    return result.stdout


def _base_bytes(repo_root: Path, path: Path) -> bytes:
    forbidden = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".npz",
        ".tar", ".zip", ".tgz", ".tmp", ".part",
    }
    if path.as_posix().startswith(("data/raw/", "checkpoints/")):
        raise ValueError(f"forbidden BASE source: {path}")
    if path.suffix.lower() in forbidden:
        raise ValueError(f"forbidden BASE suffix: {path}")
    return _git(repo_root, "show", f"{BASE_COMMIT}:{path.as_posix()}")


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _csv_bytes(columns: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                column: (
                    "true" if row.get(column) is True
                    else "false" if row.get(column) is False
                    else row.get(column, "")
                )
                for column in columns
            }
        )
    return stream.getvalue().encode("utf-8")


def mutation_signature(fields: Mapping[str, Any]) -> str:
    return "|".join(
        f"{key}={json.dumps(fields[key], sort_keys=True, separators=(',', ':'))}"
        for key in sorted(fields)
    )


def canonical_task_regions() -> dict[str, dict[str, tuple[str, ...] | bool]]:
    return {
        semantic_name: {
            "target": target,
            "context": context,
            "minimal_seed_context_override": semantic_name
            == "scaffold_plus_linker_plus_warhead",
        }
        for _, semantic_name, _, target, context in CANONICAL_TASKS
    }


def validate_annotation_scenario_exact_types(
    scenario: AnnotationScenario,
) -> tuple[str, ...]:
    """Validate every scenario field before any value-level comparison."""

    if type(scenario) is not AnnotationScenario:
        raise TypeError("scenario must be exact AnnotationScenario")
    reasons: list[str] = []
    for field_name in SCENARIO_BOOL_FIELDS:
        if type(getattr(scenario, field_name)) is not bool:
            reasons.append(f"scenario_field_type_invalid:{field_name}")
    for field_name in SCENARIO_NONNEGATIVE_INT_FIELDS:
        value = getattr(scenario, field_name)
        if type(value) is not int:
            reasons.append(f"scenario_field_type_invalid:{field_name}")
        elif value < 0:
            reasons.append(f"scenario_field_value_invalid:{field_name}")
    if type(scenario.annotation_status) is not str:
        reasons.append("scenario_field_type_invalid:annotation_status")
    if (
        type(scenario.canonical_masks) is not tuple
        or any(type(value) is not str for value in scenario.canonical_masks)
    ):
        reasons.append("scenario_field_type_invalid:canonical_masks")
    return tuple(reasons)


def _index_sequence_diagnostics(
    value: object,
    *,
    container_reason: str,
    index_reason: str,
    duplicate_reason: str,
) -> tuple[tuple[int, ...] | None, tuple[str, ...]]:
    if type(value) not in (tuple, list, range):
        return None, (container_reason,)
    values = tuple(value)
    if any(type(index) is not int or index < 0 for index in values):
        return None, (index_reason,)
    if len(values) != len(set(values)):
        return None, (duplicate_reason,)
    return values, ()


def _append_unique(reasons: list[str], new_reasons: Iterable[str]) -> None:
    for reason in new_reasons:
        if reason not in reasons:
            reasons.append(reason)


def validate_exact3_partition(
    retained_heavy_atoms: Sequence[int],
    scaffold_atoms: Sequence[int],
    linker_atoms: Sequence[int],
    warhead_atoms: Sequence[int],
    *,
    hydrogen_atoms: Sequence[int] = (),
) -> tuple[str, ...]:
    reasons: list[str] = []
    validated: list[tuple[int, ...]] = []
    for value in (
        retained_heavy_atoms,
        scaffold_atoms,
        linker_atoms,
        warhead_atoms,
        hydrogen_atoms,
    ):
        indices, diagnostics = _index_sequence_diagnostics(
            value,
            container_reason="partition_container_invalid",
            index_reason="partition_index_type_invalid",
            duplicate_reason="partition_duplicate_index",
        )
        _append_unique(reasons, diagnostics)
        if indices is not None:
            validated.append(indices)
    if reasons:
        return tuple(reasons)
    retained_values, scaffold_values, linker_values, warhead_values, hydrogen_values = (
        validated
    )
    retained = set(retained_values)
    scaffold = set(scaffold_values)
    linker = set(linker_values)
    warhead = set(warhead_values)
    hydrogens = set(hydrogen_values)
    if scaffold & linker or scaffold & warhead or linker & warhead:
        reasons.append("partition_overlap")
    if scaffold | linker | warhead != retained:
        reasons.append("partition_not_exhaustive")
    if (scaffold | linker | warhead) & hydrogens:
        reasons.append("hydrogen_in_role_partition")
    if not scaffold:
        reasons.append("scaffold_empty")
    if not linker:
        reasons.append("linker_empty")
    if not warhead:
        reasons.append("warhead_empty")
    return tuple(reasons)


def classify_linker_components(
    vertices: Sequence[int],
    edges: Sequence[tuple[int, int]],
    warhead: Sequence[int],
    scaffold_core: Sequence[int],
) -> dict[str, Any]:
    vertex_values, reasons = _index_sequence_diagnostics(
        vertices,
        container_reason="graph_vertices_container_invalid",
        index_reason="graph_vertex_index_type_invalid",
        duplicate_reason="graph_duplicate_vertex",
    )
    if reasons:
        raise ValueError(reasons[0])
    assert vertex_values is not None
    if not vertex_values:
        raise ValueError("graph_vertices_empty")
    warhead_values, reasons = _index_sequence_diagnostics(
        warhead,
        container_reason="graph_warhead_container_invalid",
        index_reason="graph_warhead_index_type_invalid",
        duplicate_reason="graph_duplicate_warhead_index",
    )
    if reasons:
        raise ValueError(reasons[0])
    core_values, reasons = _index_sequence_diagnostics(
        scaffold_core,
        container_reason="graph_scaffold_core_container_invalid",
        index_reason="graph_scaffold_core_index_type_invalid",
        duplicate_reason="graph_duplicate_scaffold_core_index",
    )
    if reasons:
        raise ValueError(reasons[0])
    assert warhead_values is not None and core_values is not None
    if not warhead_values:
        raise ValueError("graph_warhead_empty")
    if not core_values:
        raise ValueError("graph_scaffold_core_empty")
    vertex_set = set(vertex_values)
    warhead_set = set(warhead_values)
    core_set = set(core_values)
    if not warhead_set <= vertex_set:
        raise ValueError("graph_warhead_outside_vertices")
    if not core_set <= vertex_set:
        raise ValueError("graph_scaffold_core_outside_vertices")
    if warhead_set & core_set:
        raise ValueError("graph_warhead_scaffold_core_overlap")
    if type(edges) not in (tuple, list):
        raise ValueError("graph_edges_container_invalid")
    residual = vertex_set - warhead_set - core_set
    adjacency = {vertex: set() for vertex in vertex_set}
    normalized_edges: set[tuple[int, int]] = set()
    for raw_edge in edges:
        if type(raw_edge) is not tuple or len(raw_edge) != 2:
            raise ValueError("graph_edge_not_exact_pair")
        left, right = raw_edge
        if (
            type(left) is not int
            or type(right) is not int
            or left < 0
            or right < 0
        ):
            raise ValueError("graph_edge_index_type_invalid")
        if left not in vertex_set or right not in vertex_set:
            raise ValueError("graph_edge_outside_vertices")
        if left == right:
            raise ValueError("graph_edge_self_loop")
        edge = (min(left, right), max(left, right))
        if edge in normalized_edges:
            raise ValueError("graph_duplicate_edge")
        normalized_edges.add(edge)
        adjacency[left].add(right)
        adjacency[right].add(left)
    components: list[tuple[int, ...]] = []
    remaining = set(residual)
    while remaining:
        start = min(remaining)
        queue: deque[int] = deque([start])
        component: set[int] = set()
        while queue:
            atom = queue.popleft()
            if atom in component:
                continue
            component.add(atom)
            queue.extend(sorted(adjacency[atom] & residual - component))
        remaining -= component
        components.append(tuple(sorted(component)))
    classified: list[dict[str, Any]] = []
    for component in sorted(components):
        neighbors = set().union(*(adjacency[atom] for atom in component))
        touches_core = bool(neighbors & core_set)
        touches_warhead = bool(neighbors & warhead_set)
        if touches_core and touches_warhead:
            classification = "linker_bridge_component_candidate"
        elif touches_core:
            classification = "scaffold_side_substituent"
        elif touches_warhead:
            classification = "warhead_side_component_requires_family_rule"
        else:
            classification = "disconnected_graph_blocked"
        classified.append(
            {
                "atoms": component,
                "touches_scaffold_core": touches_core,
                "touches_warhead": touches_warhead,
                "classification": classification,
            }
        )
    bridge_count = sum(
        row["classification"] == "linker_bridge_component_candidate"
        for row in classified
    )
    direct_attachment = any(
        (left in core_set and right in warhead_set)
        or (right in core_set and left in warhead_set)
        for left, right in normalized_edges
    )
    return {
        "components": tuple(classified),
        "bridge_count": bridge_count,
        "direct_attachment": direct_attachment,
        "multiple_bridge_ambiguous": bridge_count > 1,
    }


def validate_minimal_seed(
    seed: Sequence[int],
    scaffold: Sequence[int],
    linker: Sequence[int],
    warhead: Sequence[int],
    scaffold_edges: Sequence[tuple[int, int]],
    primary_anchor: int,
) -> tuple[str, ...]:
    reasons: list[str] = []
    validated: list[tuple[int, ...]] = []
    for value in (seed, scaffold, linker, warhead):
        indices, diagnostics = _index_sequence_diagnostics(
            value,
            container_reason="seed_container_invalid",
            index_reason="seed_index_type_invalid",
            duplicate_reason="seed_duplicate_index",
        )
        _append_unique(reasons, diagnostics)
        if indices is not None:
            validated.append(indices)
    if type(primary_anchor) is not int or primary_anchor < 0:
        _append_unique(reasons, ("primary_anchor_type_invalid",))
    if reasons:
        return tuple(reasons)
    seed_values, scaffold_values, linker_values, warhead_values = validated
    seed_set = set(seed_values)
    scaffold_set = set(scaffold_values)
    linker_set = set(linker_values)
    warhead_set = set(warhead_values)
    if type(scaffold_edges) not in (tuple, list):
        return ("scaffold_edge_container_invalid",)
    normalized_edges: set[tuple[int, int]] = set()
    for raw_edge in scaffold_edges:
        if type(raw_edge) is not tuple or len(raw_edge) != 2:
            return ("scaffold_edge_not_exact_pair",)
        left, right = raw_edge
        if (
            type(left) is not int
            or type(right) is not int
            or left < 0
            or right < 0
        ):
            return ("scaffold_edge_index_type_invalid",)
        if left not in scaffold_set or right not in scaffold_set:
            return ("scaffold_edge_outside_scaffold",)
        if left == right:
            return ("scaffold_edge_self_loop",)
        edge = (min(left, right), max(left, right))
        if edge in normalized_edges:
            return ("scaffold_edge_duplicate",)
        normalized_edges.add(edge)
    if not seed_set <= scaffold_set:
        reasons.append("seed_outside_scaffold")
    if seed_set & linker_set:
        reasons.append("seed_overlaps_linker")
    if seed_set & warhead_set:
        reasons.append("seed_overlaps_warhead")
    if primary_anchor not in seed_set:
        reasons.append("seed_missing_primary_anchor")
    if len(seed_set) not in (2, 3):
        reasons.append("seed_size_not_2_or_3")
    adjacency = {atom: set() for atom in seed_set}
    for left, right in normalized_edges:
        if left in seed_set and right in seed_set:
            adjacency[left].add(right)
            adjacency[right].add(left)
    visited: set[int] = set()
    if seed_set:
        queue: deque[int] = deque([min(seed_set)])
        while queue:
            atom = queue.popleft()
            if atom not in visited:
                visited.add(atom)
                queue.extend(sorted(adjacency[atom] - visited))
    if visited != seed_set:
        reasons.append("seed_disconnected")
    return tuple(reasons)


def evaluate_annotation_scenario(
    scenario: AnnotationScenario,
) -> ScenarioObservation:
    type_reasons = validate_annotation_scenario_exact_types(scenario)
    if type_reasons:
        return ScenarioObservation(
            valid=False,
            reasons=type_reasons,
            ready_for_role_annotation_proposal_generation=False,
            ready_for_mask_materialization=False,
            ready_for_model_integration=False,
            ready_for_training=False,
        )
    reasons: list[str] = []
    if scenario.warhead_match_count != 1:
        reasons.append("warhead_match_not_exact_one")
    if scenario.warhead_distinct_set_count != 1:
        reasons.append("warhead_atom_set_not_exact_one")
    if not scenario.reactive_atom_present:
        reasons.append("known_reactive_atom_missing")
    if not scenario.reactive_atom_in_ligand:
        reasons.append("reactive_atom_outside_ligand")
    if not scenario.pre_reaction_graph_present:
        reasons.append("pre_reaction_graph_missing")
    if not scenario.bond_orders_present:
        reasons.append("pre_reaction_bond_orders_missing")
    if not scenario.reaction_family_present:
        reasons.append("reaction_family_missing")
    if not scenario.approved_warhead_rule_present:
        reasons.append("approved_warhead_rule_missing")
    if not scenario.warhead_match_includes_reactive_atom:
        reasons.append("warhead_match_excludes_reactive_atom")
    if not scenario.warhead_nonempty:
        reasons.append("warhead_empty")
    if scenario.warhead_boundary_count != 1:
        reasons.append("warhead_attachment_boundary_not_exact_one")
    if not scenario.scaffold_core_or_fallback_present:
        reasons.append("scaffold_core_proposal_missing")
    if not scenario.scaffold_proposals_unique:
        reasons.append("multiple_scaffold_proposals_unresolved")
    if (
        scenario.ringless_fallback_used
        and not scenario.ringless_review_completed
    ):
        reasons.append("ringless_fallback_review_missing")
    if (
        scenario.ringless_fallback_used
        and scenario.annotation_status == "auto_exact"
    ):
        reasons.append("ringless_fallback_auto_exact_forbidden")
    if scenario.linker_bridge_count != 1:
        reasons.append("linker_bridge_not_exact_one")
    if scenario.direct_attachment_present and scenario.direct_attachment_admitted:
        reasons.append("direct_attachment_no_linker_v1_quarantine")
    if not scenario.warhead_side_component_explained:
        reasons.append("warhead_side_component_unexplained")
    if scenario.disconnected_residual_present:
        reasons.append("disconnected_graph_blocked")
    if not scenario.partition_disjoint:
        reasons.append("partition_overlap")
    if not scenario.partition_exhaustive:
        reasons.append("partition_incomplete")
    if not scenario.scaffold_nonempty:
        reasons.append("scaffold_empty")
    if not scenario.linker_nonempty:
        reasons.append("linker_empty")
    if scenario.scaffold_linker_boundary_count != 1:
        reasons.append("scaffold_linker_boundary_not_exact_one")
    if not scenario.seed_subset_scaffold:
        reasons.append("seed_outside_scaffold")
    if scenario.seed_overlaps_linker:
        reasons.append("seed_overlaps_linker")
    if scenario.seed_overlaps_warhead:
        reasons.append("seed_overlaps_warhead")
    if not scenario.seed_connected:
        reasons.append("seed_disconnected")
    if not scenario.seed_has_primary_anchor:
        reasons.append("seed_missing_primary_anchor")
    if scenario.seed_size not in (2, 3):
        reasons.append("seed_size_not_2_or_3")
    if not scenario.canonical_ranking_deterministic:
        reasons.append("canonical_ranking_nondeterministic")
    if scenario.annotation_status not in ANNOTATION_STATUSES:
        reasons.append("annotation_status_outside_closed_vocabulary")
    if (
        scenario.annotation_status == "gold_curated"
        and not scenario.human_review_completed
    ):
        reasons.append("gold_curated_without_human_review")
    if scenario.training_eligible and not (
        scenario.annotation_status == "gold_curated"
        and scenario.human_review_completed
    ):
        reasons.append("non_gold_annotation_training_eligible")
    if (
        scenario.annotation_status == "ambiguous_blocked"
        and scenario.training_eligible
    ):
        reasons.append("ambiguous_annotation_training_eligible")
    if (
        scenario.current11_marked_gold
        and scenario.annotation_status != "gold_curated"
    ):
        reasons.append("non_gold_status_marked_gold")
    if scenario.current11_marked_gold and not scenario.human_review_completed:
        reasons.append("current11_gold_without_human_review")
    expected_masks = tuple(task[1] for task in CANONICAL_TASKS)
    if "scaffold_only" not in scenario.canonical_masks:
        reasons.append("scaffold_only_b3_missing")
    if scenario.canonical_masks != expected_masks:
        reasons.append("canonical_exact5_masks_drift")
    if scenario.execution_boundary_crossed:
        reasons.append("metadata_only_execution_boundary_crossed")
    valid = not reasons
    return ScenarioObservation(
        valid=valid,
        reasons=tuple(reasons),
        ready_for_role_annotation_proposal_generation=valid,
        ready_for_mask_materialization=False,
        ready_for_model_integration=False,
        ready_for_training=False,
    )


def validate_failure_mutation_registry(
    registry: Mapping[str, Mapping[str, Any]],
) -> tuple[str, ...]:
    """Fail closed on duplicate, ill-typed, or non-mutating failure evidence."""

    baseline_fields = {
        field.name: getattr(BASELINE_SCENARIO, field.name)
        for field in dataclasses.fields(BASELINE_SCENARIO)
    }
    signatures: list[str] = []
    for case, specification in registry.items():
        if type(case) is not str or not case:
            raise ValueError("failure_case_identity_invalid")
        if type(specification) is not dict or set(specification) != {
            "fields",
            "expected_reasons",
        }:
            raise ValueError(f"failure_specification_invalid:{case}")
        fields = specification["fields"]
        expected_reasons = specification["expected_reasons"]
        if type(fields) is not dict or not fields:
            raise ValueError(f"failure_mutation_fields_invalid:{case}")
        for field_name, value in fields.items():
            if field_name not in baseline_fields:
                raise ValueError(f"failure_mutation_field_unknown:{field_name}")
            baseline_value = baseline_fields[field_name]
            if type(value) is not type(baseline_value):
                raise ValueError(f"failure_mutation_field_type_invalid:{field_name}")
            if value == baseline_value:
                raise ValueError(f"failure_mutation_does_not_change_baseline:{field_name}")
        if (
            type(expected_reasons) is not tuple
            or not expected_reasons
            or any(type(reason) is not str or not reason for reason in expected_reasons)
        ):
            raise ValueError(f"failure_expected_reasons_invalid:{case}")
        signature = mutation_signature(fields)
        if signature in signatures:
            raise ValueError(f"failure_mutation_signature_duplicate:{signature}")
        signatures.append(signature)
    return tuple(signatures)


def build_failure_matrix_rows() -> list[dict[str, Any]]:
    signatures = validate_failure_mutation_registry(FAILURE_MUTATIONS)
    if len(FAILURE_MUTATIONS) != 42 or len(signatures) != 42:
        raise ValueError("failure_mutation_registry_not_exact42")
    rows: list[dict[str, Any]] = []
    for case, specification in FAILURE_MUTATIONS.items():
        fields = specification["fields"]
        expected_reasons = specification["expected_reasons"]
        scenario = dataclasses.replace(BASELINE_SCENARIO, **fields)
        observation = evaluate_annotation_scenario(scenario)
        expected_reasons_verified = all(
            reason in observation.reasons for reason in expected_reasons
        )
        rows.append(
            {
                "failure_case": case,
                "mutation_signature": mutation_signature(fields),
                "mutated_fields": json.dumps(
                    fields, sort_keys=True, separators=(",", ":")
                ),
                "expected_reasons": ";".join(expected_reasons),
                "observed_reasons": ";".join(observation.reasons),
                "expected_reasons_verified": expected_reasons_verified,
                "fails_closed": not observation.valid,
                "ready_for_role_annotation_proposal_generation":
                    observation.ready_for_role_annotation_proposal_generation,
                "ready_for_mask_materialization":
                    observation.ready_for_mask_materialization,
                "ready_for_model_integration":
                    observation.ready_for_model_integration,
                "ready_for_training": observation.ready_for_training,
                "verified": expected_reasons_verified
                and not observation.valid
                and not observation.ready_for_role_annotation_proposal_generation
                and not observation.ready_for_mask_materialization
                and not observation.ready_for_model_integration
                and not observation.ready_for_training,
            }
        )
    return rows


def _verify_base(repo_root: Path) -> None:
    identity = _git(
        repo_root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).decode().splitlines()
    expected = [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]
    if identity != expected:
        raise ValueError("formal BASE identity drift")


def _load_sources(repo_root: Path) -> dict[Path, bytes]:
    _verify_base(repo_root)
    payloads = {path: _base_bytes(repo_root, path) for path in FROZEN_SHA256}
    for path, expected in FROZEN_SHA256.items():
        if _sha(payloads[path]) != expected:
            raise ValueError(f"frozen source SHA drift: {path}")
    return payloads


def _source_inventory(payloads: Mapping[Path, bytes]) -> list[dict[str, Any]]:
    specs = {
        PREDECESSOR_SOURCE: (
            "predecessor_contract_implementation", "authoritative", False, False,
            "Exact5 and current11 role-authority blocker",
        ),
        Path("docs/covapie_tensor_label_and_loss_mask_contract_design_v1_summary.md"): (
            "predecessor_summary", "supporting", False, False,
            "human-readable predecessor boundary",
        ),
        PREDECESSOR_MANIFEST: (
            "predecessor_decision", "authoritative", True, False,
            "current11 role and minimal-seed authority absent",
        ),
        PREDECESSOR_REGISTRY: (
            "predecessor_tensor_registry", "authoritative", True, False,
            "Exact5 tensor prerequisites and blockers",
        ),
        PREDECESSOR_ISSUES: (
            "predecessor_open_issue_lineage", "authoritative", True, False,
            "condition/task-mask blocker remains open",
        ),
        MASKING_SOURCE: (
            "existing_mask_semantics", "authoritative", False, False,
            "read-only Exact5 implementation",
        ),
        SCHEMA_SOURCE: (
            "schema_field_declarations", "gap_evidence", False, True,
            "field existence is not current11 value evidence",
        ),
        SCHEMA_DOC: (
            "schema_documentation", "gap_evidence", False, True,
            "pre-reaction graph documented but not current11 materialized",
        ),
        B3_PROTOCOL: (
            "b3_nonempty_mask_contract", "authoritative", False, False,
            "B3 target scaffold; context linker plus warhead",
        ),
        FINAL_DATASET_INDEX: (
            "current11_sample_identity_and_reactive_atoms", "authoritative",
            True, False, "11 canonical rows and reactive atom names",
        ),
        ATOM_MAPPING: (
            "current11_reactive_atom_mapping", "authoritative", True, False,
            "exact-one ligand and residue atom-table mappings",
        ),
        HEAVY_DISPOSITION: (
            "retained_heavy_projection_rows", "authoritative", True, False,
            "source-to-retained-heavy disposition evidence",
        ),
        SAMPLE_PROJECTION: (
            "current11_retained_heavy_projection", "authoritative", True, False,
            "11 sample-level heavy-atom projection validations",
        ),
        TOPOLOGY_POLICY: (
            "historical_topology_restoration_design", "supporting", False, False,
            "three-candidate design only; no topology table written",
        ),
        TOPOLOGY_SUMMARY: (
            "historical_topology_scope_summary", "supporting", False, False,
            "restoration is residue-warhead-specific and review-gated",
        ),
        TOPOLOGY_DISPOSITION: (
            "topology_restoration_quarantine_policy", "supporting", False, False,
            "unapproved restoration requires review or quarantine",
        ),
        LIGAND_GRAPH_SCAFFOLD_EVIDENCE: (
            "current11_ccd_graph_and_murcko_support", "supporting", True, False,
            "SMILES/Murcko support lacks frozen atom-indexed pre-reaction edge mapping",
        ),
    }
    return [
        {
            "source_path": path.as_posix(),
            "sha256": _sha(payloads[path]),
            "source_role": specs[path][0],
            "evidence_class": specs[path][1],
            "provides_actual_current11_value": specs[path][2],
            "schema_only": specs[path][3],
            "scope_note": specs[path][4],
            "verified": True,
        }
        for path in specs
    ]


def _contract_row(
    contract_id: str,
    semantic_name: str,
    category: str,
    authority: str,
    rule: str,
    value_type: str,
    index_space: str,
    cardinality: str,
    validity: str,
    ambiguity: str,
    availability: str,
    status: str,
    blocker: str = "",
) -> dict[str, Any]:
    return {
        "contract_id": contract_id,
        "semantic_name": semantic_name,
        "contract_category": category,
        "input_authority": authority,
        "derivation_rule": rule,
        "value_type": value_type,
        "index_space": index_space,
        "cardinality": cardinality,
        "validity_semantics": validity,
        "ambiguity_semantics": ambiguity,
        "current11_availability": availability,
        "status": status,
        "blocking_reason": blocker,
        "verified": True,
    }


def _contract_registry() -> list[dict[str, Any]]:
    unavailable = "not_frozen_for_current11"
    blocker = "atom_indexed_pre_reaction_graph_and_approved_warhead_rules_missing"
    rows = [
        ("LRMSC_001", "role_vocabulary", "role", "contract", "Exact3 closed set scaffold|linker|warhead", "enum", "retained_heavy_local_index_0based", "exact3", "no fourth role", "outside vocabulary blocked"),
        ("LRMSC_002", "role_atom_set_partition", "role", "retained heavy atoms", "disjoint exhaustive partition", "three index sets", "retained_heavy_local_index_0based", "all retained heavy atoms", "no H; all roles nonempty", "overlap or gap blocked"),
        ("LRMSC_003", "warhead_match_contract", "warhead", "approved reaction-family rule", "exact-one set including known reactive atom", "index set", "retained_heavy_local_index_0based", "nonempty", "pre-reaction topology only", "zero or multiple sets blocked"),
        ("LRMSC_004", "scaffold_core_proposal", "scaffold", "curated or Murcko/BRICS/fallback proposal", "proposal metadata only", "index set", "retained_heavy_local_index_0based", "one proposal", "not a fourth role", "incomparable proposals blocked"),
        ("LRMSC_005", "linker_bridge", "linker", "accepted W and S_core plus graph", "unique residual component touching both", "index set", "retained_heavy_local_index_0based", "nonempty exact-one component", "unique bridge", "none or multiple blocked"),
        ("LRMSC_006", "scaffold_remainder", "scaffold", "V W linker", "V minus warhead minus linker", "index set", "retained_heavy_local_index_0based", "nonempty", "S_core subset scaffold", "empty blocked"),
        ("LRMSC_007", "scaffold_linker_boundary", "boundary", "accepted roles and graph", "exact-one cross-role bond", "atom pair", "retained_heavy_local_index_0based", "exact1", "scaffold-to-linker", "zero or multiple blocked"),
        ("LRMSC_008", "linker_warhead_boundary", "boundary", "accepted roles and graph", "exact-one frozen attachment", "atom pair", "retained_heavy_local_index_0based", "exact1", "linker-to-warhead", "zero or multiple blocked"),
        ("LRMSC_009", "minimal_seed", "seed", "unique scaffold-linker boundary", "s0 plus canonical scaffold neighbor and optional plane anchor", "index set", "retained_heavy_local_index_0based", "2 or 3", "connected subset scaffold", "tie or invalid seed blocked"),
        ("LRMSC_010", "primary_direction_plane_anchors", "seed", "canonical ranks and explicit tie-break", "s0 s1 optional s2", "atom indices", "retained_heavy_local_index_0based", "2 required plus 1 optional", "input numbering independent", "unbreakable tie blocked"),
        ("LRMSC_011", "annotation_status", "review", "proposal and review gates", "closed status transition", "enum", "sample", "exact1", "proposal_only|auto_exact|gold_curated|ambiguous_blocked", "ambiguity forces blocked"),
        ("LRMSC_012", "ambiguity_reasons", "review", "all gate failures", "stable reason list", "string list", "sample", "zero or more", "empty only when exact", "unresolved reason blocks"),
        ("LRMSC_013", "human_review_decision", "review", "future gold package", "approve_gold|revise|quarantine", "enum", "sample", "exact1 when reviewed", "gold requires completed reviewer", "missing review blocks current11 gold"),
        ("LRMSC_014", "five_mask_derivation_prerequisites", "mask", "gold Exact3 roles and C seed", "preserve Exact5 and B3", "contract", "sample", "exact5", "C seed context override only", "sixth mask or missing B3 blocked"),
    ]
    return [
        _contract_row(
            *row,
            unavailable,
            "designed_with_input_authority_gap",
            blocker,
        )
        for row in rows
    ]


def _rule_registry() -> list[dict[str, Any]]:
    rules = (
        ("LRMSR_001", "known reactive atom required", 10, "required", "exact known ligand reactive atom", "known_reactive_atom_missing"),
        ("LRMSR_002", "approved reaction family required", 20, "required", "frozen family and version", "approved_warhead_rule_missing"),
        ("LRMSR_003", "warhead exact-one match", 30, "required", "deduplicated atom set exact-one", "warhead_atom_set_not_exact_one"),
        ("LRMSR_004", "warhead includes reactive atom", 40, "required", "mapped reactive atom is in match", "warhead_match_excludes_reactive_atom"),
        ("LRMSR_005", "warhead attachment boundary exact-one", 50, "required", "one attachment to rest of ligand", "warhead_attachment_boundary_not_exact_one"),
        ("LRMSR_006", "Murcko proposal only", 60, "proposal_only", "core metadata never final role", "murcko_direct_label_forbidden"),
        ("LRMSR_007", "BRICS supporting evidence only", 70, "supporting_only", "boundary support never final authority", "brics_direct_label_forbidden"),
        ("LRMSR_008", "ringless fallback requires review", 80, "review_required", "deterministic fallback cannot be auto-exact", "ringless_fallback_review_missing"),
        ("LRMSR_009", "unique linker bridge component", 90, "required", "one component touches S_core and W", "linker_bridge_not_exact_one"),
        ("LRMSR_010", "scaffold-side substituent assignment", 100, "required", "core-only component joins scaffold", "scaffold_side_unassigned"),
        ("LRMSR_011", "warhead-only-side component explained", 110, "required", "family rule must explain component", "warhead_side_component_unexplained"),
        ("LRMSR_012", "multiple bridge components blocked", 120, "required", "no silent path selection", "multi_path_linker_ambiguous_blocked"),
        ("LRMSR_013", "partition disjoint", 130, "required", "pairwise disjoint Exact3", "partition_overlap"),
        ("LRMSR_014", "partition exhaustive", 140, "required", "union equals retained heavy atoms", "partition_incomplete"),
        ("LRMSR_015", "all three roles nonempty", 150, "required", "V1 scaffold linker warhead nonempty", "empty_role"),
        ("LRMSR_016", "boundary bond exact-one", 160, "required", "unique scaffold-linker and linker-warhead bonds", "boundary_not_exact_one"),
        ("LRMSR_017", "minimal seed subset of scaffold", 170, "required", "seed never fourth role", "seed_outside_scaffold"),
        ("LRMSR_018", "minimal seed connected", 180, "required", "seed induced subgraph connected", "seed_disconnected"),
        ("LRMSR_019", "minimal seed size 2 or 3", 190, "required", "s0 s1 optional s2", "seed_size_not_2_or_3"),
        ("LRMSR_020", "canonical-rank deterministic selection", 200, "required", "stable chemical identity tie-break", "canonical_ranking_nondeterministic"),
        ("LRMSR_021", "current11 human gold review required", 210, "required", "training authority is gold_curated only", "current11_gold_without_human_review"),
    )
    return [
        {
            "rule_id": rule_id,
            "rule_name": name,
            "priority": priority,
            "rule_status": status,
            "rule_semantics": semantics,
            "failure_reason": reason,
            "fails_closed": True,
            "verified": True,
        }
        for rule_id, name, priority, status, semantics, reason in rules
    ]


def _readiness_matrix(payloads: Mapping[Path, bytes]) -> list[dict[str, Any]]:
    index_rows = _csv_rows(payloads[FINAL_DATASET_INDEX])
    mapping_rows = _csv_rows(payloads[ATOM_MAPPING])
    projection_rows = _csv_rows(payloads[SAMPLE_PROJECTION])
    graph_rows = _csv_rows(payloads[LIGAND_GRAPH_SCAFFOLD_EVIDENCE])
    if len(index_rows) != 11 or len(projection_rows) != 11 or len(graph_rows) != 11:
        raise ValueError("current11 evidence cardinality drift")
    mapping_by_sample: dict[str, list[dict[str, str]]] = {}
    for row in mapping_rows:
        mapping_by_sample.setdefault(row["sample_index_row_id"], []).append(row)
    projection = {row["sample_index_row_id"]: row for row in projection_rows}
    graph = {row["sample_index_row_id"]: row for row in graph_rows}
    rows: list[dict[str, Any]] = []
    for index_row in index_rows:
        sample_id = index_row["sample_index_row_id"]
        sample_mappings = mapping_by_sample.get(sample_id, [])
        entities = {row["entity_role"] for row in sample_mappings}
        mapping_ok = (
            entities == {"ligand_atom", "target_residue_atom"}
            and all(
                row["mapping_outcome"] == "mapped"
                and _truth(row["verified"])
                and row["candidate_match_count"] == "1"
                for row in sample_mappings
            )
            and _truth(projection[sample_id]["pair_projection_exact_one"])
            and _truth(projection[sample_id]["verified"])
        )
        ligand_reactive = bool(index_row["ligand_covalent_atom_name"]) and (
            "ligand_atom" in entities
        )
        residue_reactive = bool(index_row["covalent_residue_atom_name"]) and (
            "target_residue_atom" in entities
        )
        graph_support = _truth(graph[sample_id]["ligand_graph_evidence_passed"])
        blockers = (
            "atom_indexed_pre_reaction_connectivity_not_frozen",
            "atom_indexed_pre_reaction_bond_orders_not_frozen",
            "reaction_family_label_missing",
            "approved_warhead_rule_missing",
            "human_gold_review_missing",
        )
        rows.append(
            {
                "sample_index_row_id": sample_id,
                "retained_heavy_atom_mapping_available": mapping_ok,
                "ligand_reactive_atom_available": ligand_reactive,
                "residue_reactive_atom_available": residue_reactive,
                "pre_reaction_connectivity_available": False,
                "pre_reaction_bond_order_available": False,
                "reaction_family_label_available": False,
                "approved_warhead_rule_available": False,
                "murcko_input_ready": False,
                "brics_input_ready": False,
                "role_proposal_generation_ready": False,
                "minimal_seed_proposal_generation_ready": False,
                "human_gold_review_completed": False,
                "blocking_reasons": ";".join(blockers)
                + (
                    ";ccd_smiles_and_murcko_support_present_but_not_atom_index_authority"
                    if graph_support else ";ccd_graph_support_missing"
                ),
                "verified": mapping_ok
                and ligand_reactive
                and residue_reactive
                and graph_support,
            }
        )
    return rows


def derive_contract_design(repo_root: Path) -> dict[str, Any]:
    payloads = _load_sources(repo_root)
    readiness_rows = _readiness_matrix(payloads)
    role_ready = all(
        row["role_proposal_generation_ready"] for row in readiness_rows
    )
    seed_ready = all(
        row["minimal_seed_proposal_generation_ready"] for row in readiness_rows
    )
    decision = ContractDecision(
        schema_version=SCHEMA_VERSION,
        design_outcome="designed_contract_with_input_authority_gaps",
        contract_design_completed=True,
        ready_for_current11_role_annotation_proposal_generation=role_ready,
        ready_for_current11_minimal_seed_proposal_generation=seed_ready,
        ready_for_mask_materialization=False,
        ready_for_tensorization=False,
        ready_for_model_integration=False,
        ready_for_training=False,
        recommended_next_step="resolve_covapie_role_annotation_input_authority_gaps_v1",
    )
    return {
        "decision": decision,
        "source_rows": _source_inventory(payloads),
        "contract_rows": _contract_registry(),
        "rule_rows": _rule_registry(),
        "readiness_rows": readiness_rows,
        "failure_rows": build_failure_matrix_rows(),
    }


def serialize_decision(decision: ContractDecision) -> bytes:
    return (
        json.dumps(dataclasses.asdict(decision), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _non_manifest_artifacts(result: Mapping[str, Any]) -> dict[str, bytes]:
    return {
        SOURCE_INVENTORY_FILE: _csv_bytes(SOURCE_COLUMNS, result["source_rows"]),
        CONTRACT_REGISTRY_FILE: _csv_bytes(
            CONTRACT_COLUMNS, result["contract_rows"]
        ),
        RULE_REGISTRY_FILE: _csv_bytes(RULE_COLUMNS, result["rule_rows"]),
        READINESS_MATRIX_FILE: _csv_bytes(
            READINESS_COLUMNS, result["readiness_rows"]
        ),
        FAILURE_MATRIX_FILE: _csv_bytes(
            FAILURE_COLUMNS, result["failure_rows"]
        ),
    }


def build_artifacts(repo_root: Path) -> dict[str, bytes]:
    result = derive_contract_design(repo_root)
    artifacts = _non_manifest_artifacts(result)
    decision: ContractDecision = result["decision"]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "formal_base": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "formal_commit_subject": FORMAL_COMMIT_SUBJECT,
        "design_outcome": decision.design_outcome,
        "contract_design_completed": True,
        "canonical_roles": list(EXACT3_ROLES),
        "canonical_role_count": 3,
        "canonical_tasks": [
            {
                "task_id": task_id,
                "semantic_name": semantic_name,
                "alias": alias,
                "target": list(target),
                "context": list(context),
            }
            for task_id, semantic_name, alias, target, context in CANONICAL_TASKS
        ],
        "canonical_task_count": 5,
        "b3_target": ["scaffold"],
        "b3_context": ["linker", "warhead"],
        "pipeline": list(PIPELINE),
        "annotation_statuses": list(ANNOTATION_STATUSES),
        "warhead_rule_fields": list(WARHEAD_RULE_FIELDS),
        "review_package_fields": list(REVIEW_PACKAGE_FIELDS),
        "future_visualization_layers": list(VISUALIZATION_LAYERS),
        "source_inventory_row_count": len(result["source_rows"]),
        "contract_registry_row_count": len(result["contract_rows"]),
        "rule_registry_row_count": len(result["rule_rows"]),
        "current11_readiness_row_count": len(result["readiness_rows"]),
        "failure_matrix_row_count": len(result["failure_rows"]),
        "annotation_scenario_exact_scalar_types_verified": True,
        "boundary_and_bridge_counts_exact_int_verified": True,
        "gold_curated_requires_human_review": True,
        "training_eligibility_requires_gold_curated": True,
        "ringless_fallback_auto_exact_forbidden": True,
        "public_role_atom_index_helpers_exact_types_verified": True,
        "boolean_rejected_for_role_atom_indices": True,
        "duplicate_role_atom_indices_rejected": True,
        "failure_mutation_signature_count": len(result["failure_rows"]),
        "failure_mutation_signatures_unique": len(
            {row["mutation_signature"] for row in result["failure_rows"]}
        ) == len(result["failure_rows"]),
        "failure_expected_reasons_verified": all(
            row["expected_reasons_verified"] for row in result["failure_rows"]
        ),
        "failure_mutation_exact_types_verified": True,
        "current11_pre_reaction_connectivity_available_count": 0,
        "current11_pre_reaction_bond_order_available_count": 0,
        "current11_reaction_family_label_available_count": 0,
        "current11_approved_warhead_rule_available_count": 0,
        "current11_role_proposal_generation_ready_count": 0,
        "current11_minimal_seed_proposal_generation_ready_count": 0,
        "current11_human_gold_review_completed_count": 0,
        "role_annotation_materialized": False,
        "minimal_seed_materialized": False,
        "current11_gold_review_completed": False,
        "masking_code_changed": False,
        "schema_changed": False,
        "dataloader_changed": False,
        "model_changed": False,
        "forward_changed": False,
        "loss_changed": False,
        "checkpoint_access": False,
        "raw_read": False,
        "npz_read": False,
        "lmdb_read": False,
        "compressed_archive_read": False,
        "rdkit_current11_segmentation_run": False,
        "image_generated": False,
        "structure_file_written": False,
        "tensor_materialized": False,
        "training_used": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "ready_for_current11_role_annotation_proposal_generation":
            decision.ready_for_current11_role_annotation_proposal_generation,
        "ready_for_current11_minimal_seed_proposal_generation":
            decision.ready_for_current11_minimal_seed_proposal_generation,
        "ready_for_mask_materialization": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "remaining_readiness_blockers": [
            "atom_indexed_pre_reaction_connectivity_not_frozen",
            "atom_indexed_pre_reaction_bond_orders_not_frozen",
            "reaction_family_labels_missing",
            "approved_warhead_rules_missing",
            "current11_human_gold_review_missing",
            "COVALENT_CONDITION_AND_TASK_MASK_TENSOR_CONTRACT_UNRESOLVED",
            "COVALENT_GEOMETRY_AND_AUXILIARY_LABEL_CONTRACT_UNRESOLVED",
        ],
        "recommended_next_step": decision.recommended_next_step,
        "evidence_sha256": {
            name: _sha(payload) for name, payload in sorted(artifacts.items())
        },
    }
    artifacts[MANIFEST_FILE] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return artifacts
