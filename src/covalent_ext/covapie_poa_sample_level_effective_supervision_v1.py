"""Compile frozen POA exact16 human decisions into sample-level metadata.

The public builder consumes in-memory bytes, delegates chemistry and training
routing to the published completed-decision reconciliation owner, and returns
immutable metadata records.  It performs no filesystem I/O, structure
projection, tensorization, admission, model execution, or state write.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping, NoReturn

from covalent_ext import (
    covapie_completed_human_decision_reconciliation_v1 as reconciliation,
)
from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as direct_runtime,
)


__all__ = (
    "POASampleLevelEffectiveSupervisionError",
    "POASampleLevelEffectiveSupervisionRecordV1",
    "POASampleLevelEffectiveSupervisionSummaryV1",
    "POASampleLevelEffectiveSupervisionSourceProvenanceV1",
    "POASampleLevelEffectiveSupervisionResultV1",
    "build_covapie_poa_sample_level_effective_supervision_v1",
    "validate_covapie_poa_sample_level_effective_supervision_v1",
)


ERROR_TOKEN = "COVAPIE_POA_SAMPLE_LEVEL_EFFECTIVE_SUPERVISION_V1_ERROR"
SCHEMA_VERSION = "covapie_poa_sample_level_effective_supervision_record_v1"

FORMAL_DECISION_PATH = (
    reconciliation.POA_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
)
FORMAL_DECISION_BYTE_COUNT = reconciliation.POA_FORMAL_DECISION_BYTE_COUNT
FORMAL_DECISION_SHA256 = reconciliation.POA_FORMAL_DECISION_SHA256
FORMAL_DECISION_SCHEMA = reconciliation.POA_FORMAL_DECISION_SCHEMA
REVIEW_UNIT_ID = reconciliation.POA_REVIEW_UNIT_ID

SOURCE_ROLE_PROFILE = "STRICT_LINKER_PRESENT"
RUNTIME_ROLE_PROFILE = direct_runtime.STRICT_LINKER_PRESENT_V1
_ROLE_PROFILE_MAPPING = {SOURCE_ROLE_PROFILE: RUNTIME_ROLE_PROFILE}

_EXACT_HEAVY_ATOM_IDS = ("C1", "C2", "O1P", "O2", "O2P", "O3P", "P")
_SCAFFOLD_ATOM_IDS = ("P", "O1P", "O2P", "O3P")
_LINKER_ATOM_IDS = ("C1",)
_WARHEAD_ATOM_IDS = ("C2", "O2")
_ROLE_BOUNDARIES = (
    ("warhead_to_linker", "C2", "C1", "SING"),
    ("linker_to_scaffold", "C1", "P", "SING"),
)
_EXPECTED_MASK_COUNTS = ((2, 5), (3, 4), (6, 1), (4, 3), (7, 0))
_VALID_TASK_IDS = (0, 1, 2, 3, 4)
_CANONICAL_TASKS = (
    (0, "warhead_only", "A"),
    (1, "linker_plus_warhead", "B"),
    (2, "scaffold_plus_warhead", "B2"),
    (3, "scaffold_only", "B3"),
    (4, "scaffold_plus_linker_plus_warhead", "C"),
)
_EVENT_ID = re.compile(
    r"^COVAPIE_CYS_SG_EVENT_V1:"
    r"(?P<pdb>[^:]+):(?P<protein_chain>[^:]+):CYS:291-:SG:"
    r"(?P<ligand_chain>[^:]+):POA:C2$"
)
_SUBGROUP_CONTRACT = {
    "4I3U": {
        "subgroup_id": "POA_SUBGROUP_G1_4I3U_THIOHEMIACETAL",
        "protein_chains": tuple("ABCDEFGH"),
        "ligand_chains": tuple("IJKLMNOP"),
        "human_chemistry_interpretation": (
            "CYS_SG_ALDEHYDE_ADDITION_THIOHEMIACETAL_STATE"
        ),
        "human_post_state_interpretation": "THIOHEMIACETAL_POST_STATE",
    },
    "4I3V": {
        "subgroup_id": "POA_SUBGROUP_G2_4I3V_THIOESTER",
        "protein_chains": tuple("ABCDEFGH"),
        "ligand_chains": ("J", "L", "N", "P", "R", "T", "V", "W"),
        "human_chemistry_interpretation": (
            "CYS_SG_NAD_DEPENDENT_THIOESTER_ACYL_ENZYME_STATE"
        ),
        "human_post_state_interpretation": "THIOESTER_POST_STATE",
    },
}
_RECONCILIATION_OWNER = (
    "covalent_ext.covapie_completed_human_decision_reconciliation_v1"
)
_RECONCILIATION_PROJECTION = "project_poa_formal_decision_v1"


class POASampleLevelEffectiveSupervisionError(ValueError):
    """Raised unless every POA exact16 sample-level invariant is proven."""


def _fail(reason: str) -> NoReturn:
    raise POASampleLevelEffectiveSupervisionError(f"{ERROR_TOKEN}:{reason}")


@dataclass(frozen=True, slots=True)
class POASampleLevelEffectiveSupervisionRecordV1:
    schema_version: str
    canonical_event_id: str
    review_unit_id: str
    pdb_id: str
    subgroup_id: str

    human_review_completed: bool
    legacy_completed_review_status: str
    task_relevance_disposition: str
    chemistry_disposition: str
    training_use_disposition: str
    human_training_excluded: bool
    nongeometry_future_candidate: bool
    chemistry_state_training_target_available: bool

    target_residue_name: str
    target_residue_atom_id: str
    ligand_component_id: str
    ligand_reactive_atom_id: str
    reactive_pair_authority_available: bool
    pair_candidate_domain_materialized: bool

    source_role_profile: str
    runtime_role_profile: str
    scaffold_atom_ids: tuple[str, ...]
    linker_atom_ids: tuple[str, ...]
    warhead_atom_ids: tuple[str, ...]
    role_partition_authority_available: bool

    valid_task_ids: tuple[int, ...]
    task_structural_mask_labels_available: bool
    task_C_role_mask_available: bool
    task_C_minimal_seed_authority_available: bool

    precursor_evidence_status: str
    PRE_reaction_graph_authority_available: bool
    PRE_reaction_bond_order_authority_available: bool
    PRE_geometry_training_authority_available: bool
    POST_geometry_training_authority_available: bool
    reaction_family_authority_available: bool
    reaction_family_target_available: bool
    warhead_rule_authority_available: bool
    warhead_rule_target_available: bool
    warhead_type_target_available: bool

    split_authoritative: bool
    training_admitted: bool

    @property
    def chemistry_positive(self) -> bool:
        return self.chemistry_disposition == reconciliation.CHEMISTRY_POSITIVE

    @property
    def chemistry_negative(self) -> bool:
        return self.chemistry_disposition == reconciliation.CHEMISTRY_NEGATIVE

    @property
    def not_applicable_task_ids(self) -> tuple[int, ...]:
        return tuple(task for task in range(5) if task not in self.valid_task_ids)

    @property
    def full_task_C_training_supervision_ready(self) -> bool:
        return (
            self.task_C_role_mask_available
            and self.task_C_minimal_seed_authority_available
            and self.training_admitted
        )

    @property
    def geometry_training_target_available(self) -> bool:
        return (
            self.PRE_geometry_training_authority_available
            or self.POST_geometry_training_authority_available
        )


@dataclass(frozen=True, slots=True)
class POASampleLevelEffectiveSupervisionSummaryV1:
    record_count: int
    chemistry_positive_count: int
    G1_count: int
    G2_count: int
    training_include_count: int
    training_excluded_positive_count: int
    reactive_pair_authority_count: int
    role_partition_authority_count: int
    exact5_structural_mask_label_count: int
    task_C_role_mask_available_count: int
    task_C_minimal_seed_authority_count: int
    PRE_geometry_authority_count: int
    POST_geometry_authority_count: int
    reaction_family_target_count: int
    warhead_rule_target_count: int
    warhead_type_target_count: int
    nongeometry_future_candidate_count: int
    split_authoritative_count: int
    training_admitted_count: int
    pair_candidate_domain_materialized_count: int
    chemistry_state_training_target_count: int

    sample_level_chemistry_authority_available: bool
    sample_level_reactive_pair_authority_available: bool
    sample_level_role_partition_authority_available: bool
    reusable_chemistry_rule_created: bool
    reusable_reactive_pair_rule_created: bool
    reusable_role_authority_created: bool
    reaction_family_authority_created: bool
    warhead_rule_authority_created: bool
    loss_active: bool
    training_dataset_changed: bool


@dataclass(frozen=True, slots=True)
class POASampleLevelEffectiveSupervisionSourceProvenanceV1:
    formal_decision_path: str
    formal_decision_path_namespace: str
    formal_decision_byte_count: int
    formal_decision_sha256: str
    formal_decision_schema: str
    review_unit_id: str
    reconciliation_owner: str
    reconciliation_projection: str


@dataclass(frozen=True, slots=True)
class POASampleLevelEffectiveSupervisionResultV1:
    records: tuple[POASampleLevelEffectiveSupervisionRecordV1, ...]
    summary: POASampleLevelEffectiveSupervisionSummaryV1
    source_provenance: POASampleLevelEffectiveSupervisionSourceProvenanceV1


def _mapping(value: object, reason: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(reason)
    return value


def _list(value: object, reason: str) -> list[Any]:
    if type(value) is not list:
        _fail(reason)
    return value


def _exact_role_profile(source_role_profile: object) -> str:
    if type(source_role_profile) is not str:
        _fail("SOURCE_ROLE_PROFILE_INVALID")
    runtime = _ROLE_PROFILE_MAPPING.get(source_role_profile)
    if runtime is None:
        _fail("SOURCE_ROLE_PROFILE_NOT_EXACTLY_MAPPED")
    return runtime


def _validate_role_and_task_contract(
    formal: Mapping[str, Any],
) -> tuple[str, tuple[int, ...]]:
    role = _mapping(formal.get("role_human_decision"), "ROLE_DECISION_INVALID")
    runtime_profile = _exact_role_profile(role.get("selected_role_profile"))
    scaffold = tuple(_list(role.get("scaffold_atom_ids"), "SCAFFOLD_INVALID"))
    linker = tuple(_list(role.get("linker_atom_ids"), "LINKER_INVALID"))
    warhead = tuple(_list(role.get("warhead_atom_ids"), "WARHEAD_INVALID"))
    heavy = tuple(
        _list(role.get("exact_ccd_heavy_atom_ids"), "HEAVY_SET_INVALID")
    )
    if (
        scaffold != _SCAFFOLD_ATOM_IDS
        or linker != _LINKER_ATOM_IDS
        or warhead != _WARHEAD_ATOM_IDS
        or heavy != _EXACT_HEAVY_ATOM_IDS
        or any(type(atom) is not str for atom in scaffold + linker + warhead + heavy)
    ):
        _fail("ROLE_ATOM_PARTITION_DRIFT")
    role_sets = tuple(map(set, (scaffold, linker, warhead)))
    if (
        any(not values for values in role_sets)
        or any(role_sets[i] & role_sets[j] for i in range(3) for j in range(i + 1, 3))
        or set().union(*role_sets) != set(heavy)
        or tuple(map(len, role_sets)) != (4, 1, 2)
    ):
        _fail("ROLE_PARTITION_INVALID")
    boundaries = tuple(
        (
            boundary.get("role_edge"),
            boundary.get("atom_id_1"),
            boundary.get("atom_id_2"),
            boundary.get("CCD_bond_order"),
        )
        for boundary in (
            _mapping(raw, "ROLE_BOUNDARY_INVALID")
            for raw in _list(role.get("boundaries"), "ROLE_BOUNDARIES_INVALID")
        )
    )
    if boundaries != _ROLE_BOUNDARIES:
        _fail("ROLE_BOUNDARY_DRIFT")
    partition_validation = _mapping(
        role.get("partition_validation"), "ROLE_PARTITION_VALIDATION_INVALID"
    )
    required_partition_flags = (
        "all_roles_nonempty",
        "pairwise_disjoint",
        "union_equals_exact_ccd_heavy_atom_set",
        "warhead_connected",
        "linker_connected",
        "scaffold_connected",
        "role_graph_connected",
        "role_partition_identical_for_all_exact16",
    )
    if (
        any(partition_validation.get(field) is not True for field in required_partition_flags)
        or role.get("sample_specific_role_decision_created") is not True
        or role.get("reusable_role_authority_created") is not False
    ):
        _fail("ROLE_AUTHORITY_BOUNDARY_INVALID")
    runtime_validation = direct_runtime.validate_role_partition_for_profile_v1(
        role_profile=runtime_profile,
        retained_heavy_atoms=heavy,
        scaffold_atoms=scaffold,
        linker_atoms=linker,
        warhead_atoms=warhead,
    )
    if (
        runtime_validation.valid is not True
        or runtime_validation.scaffold_count != 4
        or runtime_validation.linker_count != 1
        or runtime_validation.warhead_count != 2
    ):
        _fail("PUBLISHED_ROLE_RUNTIME_REJECTED")

    mask_contract = _mapping(
        formal.get("canonical_exact5_mask_boundary"), "EXACT5_CONTRACT_INVALID"
    )
    task_rows = _list(mask_contract.get("tasks"), "EXACT5_TASKS_INVALID")
    observed_tasks = tuple(
        (
            task.get("mask_index"),
            task.get("semantic_long_name"),
            task.get("display_alias"),
            task.get("structurally_applicable"),
        )
        for task in (
            _mapping(raw, "EXACT5_TASK_ROW_INVALID") for raw in task_rows
        )
    )
    expected_tasks = tuple((*task, True) for task in _CANONICAL_TASKS)
    if (
        mask_contract.get("role_profile") != SOURCE_ROLE_PROFILE
        or mask_contract.get("structurally_applicable_task_count") != 5
        or observed_tasks != expected_tasks
        or mask_contract.get("sixth_task_created") is not False
        or mask_contract.get("training_admission_granted") is not False
        or mask_contract.get("full_task_C_seed_authority_granted") is not False
        or mask_contract.get("geometry_supervision_granted") is not False
    ):
        _fail("EXACT5_CONTRACT_DRIFT")
    runtime_tasks = direct_runtime.valid_canonical_task_ids_for_role_profile_v1(
        runtime_profile
    )
    if runtime_tasks != _VALID_TASK_IDS:
        _fail("RUNTIME_VALID_TASK_IDS_DRIFT")
    published_tasks = tuple(
        (task_id, name, alias)
        for task_id, name, alias, *_rest in direct_runtime.CANONICAL_TASKS_V1
    )
    if published_tasks != _CANONICAL_TASKS:
        _fail("PUBLISHED_CANONICAL_TASKS_DRIFT")

    local_by_atom = {atom: index for index, atom in enumerate(heavy)}
    local_roles = tuple(
        tuple(local_by_atom[atom] for atom in atoms)
        for atoms in (scaffold, linker, warhead)
    )
    for task_id, expected_counts in zip(runtime_tasks, _EXPECTED_MASK_COUNTS):
        mask = direct_runtime.build_mask_for_role_profile_v1(
            role_profile=runtime_profile,
            canonical_task_id=task_id,
            scaffold_atoms=local_roles[0],
            linker_atoms=local_roles[1],
            warhead_atoms=local_roles[2],
            num_ligand_atoms=len(heavy),
        )
        if (len(mask.masked_atoms), len(mask.visible_atoms)) != expected_counts:
            _fail("EXACT5_MASK_COUNT_DRIFT")
    return runtime_profile, runtime_tasks


def _validate_global_authority_boundaries(formal: Mapping[str, Any]) -> None:
    unit = _mapping(
        formal.get("unit_level_human_decisions"), "UNIT_DECISION_INVALID"
    )
    if (
        unit.get("exact_event_count") != 16
        or unit.get("completed_human_review_event_count") != 16
        or unit.get("chemistry_positive_event_count") != 16
        or unit.get("chemistry_negative_event_count") != 0
        or unit.get("human_training_excluded_positive_event_count") != 8
        or unit.get("POA_HOMOGENEOUS_CHEMISTRY") is not False
        or unit.get("SUBGROUP_DECISIONS_SEPARATE") is not True
        or unit.get("subgroup_count") != 2
        or unit.get("training_admission_created") is not False
        or unit.get("training_dataset_changed") is not False
    ):
        _fail("UNIT_DECISION_DRIFT")

    reactive = _mapping(
        formal.get("reactive_pair_human_decision"), "REACTIVE_PAIR_INVALID"
    )
    if (
        reactive.get("applies_to_exact_event_count") != 16
        or reactive.get("protein_component_id") != "CYS"
        or reactive.get("protein_reactive_atom_id") != "SG"
        or reactive.get("ligand_component_id") != "POA"
        or reactive.get("ligand_reactive_atom_id") != "C2"
        or reactive.get("reactive_pair_human_decision_created") is not True
    ):
        _fail("REACTIVE_PAIR_AUTHORITY_DRIFT")

    precursor = _mapping(
        formal.get("precursor_mapping_context"), "PRECURSOR_BOUNDARY_INVALID"
    )
    if (
        precursor.get("precursor_evidence_status")
        != "PRECURSOR_EVIDENCE_NOT_ESTABLISHED"
        or precursor.get("PRE_REACTION_GRAPH_AUTHORITY") is not False
        or precursor.get("PRE_REACTION_BOND_ORDER_AUTHORITY") is not False
        or precursor.get("PRE_GEOMETRY_AUTHORITY") is not False
    ):
        _fail("PRECURSOR_AUTHORITY_PROMOTED")
    post = _mapping(
        formal.get("post_state_authority_boundary"), "POST_BOUNDARY_INVALID"
    )
    if (
        post.get("POST_GEOMETRY_TRAINING_AUTHORITY") != "UNCHANGED"
        or post.get("new_POST_geometry_training_target_created") is not False
    ):
        _fail("POST_GEOMETRY_AUTHORITY_PROMOTED")

    family = _mapping(
        formal.get("reaction_family_candidate_review_decision"),
        "REACTION_FAMILY_BOUNDARY_INVALID",
    )
    rule = _mapping(
        formal.get("warhead_rule_candidate_review_decision"),
        "WARHEAD_RULE_BOUNDARY_INVALID",
    )
    if (
        family.get("exact_signature_created") is not False
        or family.get("reaction_family_candidate_registered") is not False
        or family.get("reaction_family_authority_created") is not False
        or rule.get("warhead_rule_candidate_registered") is not False
        or rule.get("warhead_rule_authority_created") is not False
        or formal.get("reaction_family_target_available", False) is not False
        or formal.get("warhead_rule_target_available", False) is not False
        or formal.get("warhead_type_target_available", False) is not False
    ):
        _fail("FAMILY_RULE_OR_WARHEAD_TARGET_PROMOTED")

    existing = _mapping(
        formal.get("existing_authority_boundary"),
        "EXISTING_AUTHORITY_BOUNDARY_INVALID",
    )
    if (
        existing.get("EXISTING_EXACT_AUTHORITY_MATCH_COUNT") != 0
        or existing.get("exact_existing_authority_inherited_count") != 0
        or existing.get("FFQ_family_inherited") is not False
        or existing.get("FFQ_warhead_rule_inherited") is not False
        or existing.get("Current11_candidate_family_inherited") is not False
        or existing.get("recovered7_authority_inherited") is not False
        or existing.get("similarity_based_inheritance_used") is not False
    ):
        _fail("EXISTING_AUTHORITY_INHERITANCE_INVALID")

    authority = _mapping(
        formal.get("authority_boundary"), "AUTHORITY_BOUNDARY_INVALID"
    )
    required_true = (
        "human_sample_level_chemistry_decision_created",
        "human_sample_level_training_use_decision_created",
        "human_sample_level_reactive_pair_decision_created",
        "human_sample_level_role_decision_created",
    )
    required_false = (
        "reusable_chemistry_rule_created",
        "reaction_family_authority_created",
        "warhead_rule_authority_created",
        "reusable_role_authority_created",
        "auto_admission_created",
        "runtime_rule_created",
        "training_admission_created",
        "training_dataset_changed",
        "ready_for_training",
        "model_forward_executed",
        "loss_executed",
        "backward_executed",
        "optimizer_step_executed",
        "Trainer_fit_executed",
        "training_performed",
        "finetune_performed",
    )
    if (
        any(authority.get(field) is not True for field in required_true)
        or any(authority.get(field) is not False for field in required_false)
        or authority.get("auto_resolvable_events_created") != 0
        or formal.get("reusable_reactive_pair_rule_created", False) is not False
        or formal.get("training_admitted", False) is not False
    ):
        _fail("AUTHORITY_BOUNDARY_PROMOTED")


def _validated_subgroups(
    formal: Mapping[str, Any],
) -> tuple[tuple[Mapping[str, Any], tuple[str, ...]], ...]:
    groups = _list(formal.get("subgroup_human_decisions"), "SUBGROUPS_INVALID")
    if len(groups) != 2:
        _fail("EXACT2_SUBGROUPS_REQUIRED")
    by_pdb: dict[str, Mapping[str, Any]] = {}
    for raw in groups:
        group = _mapping(raw, "SUBGROUP_INVALID")
        pdb_id = group.get("pdb_id")
        if pdb_id not in _SUBGROUP_CONTRACT or pdb_id in by_pdb:
            _fail("SUBGROUP_PDB_IDENTITY_INVALID")
        by_pdb[str(pdb_id)] = group
    if set(by_pdb) != set(_SUBGROUP_CONTRACT):
        _fail("SUBGROUP_COVERAGE_INVALID")

    result: list[tuple[Mapping[str, Any], tuple[str, ...]]] = []
    all_ids: set[str] = set()
    for pdb_id in ("4I3U", "4I3V"):
        group = by_pdb[pdb_id]
        contract = _SUBGROUP_CONTRACT[pdb_id]
        event_ids = tuple(
            _list(group.get("canonical_event_ids"), "SUBGROUP_EVENT_IDS_INVALID")
        )
        if (
            group.get("subgroup_id") != contract["subgroup_id"]
            or group.get("event_count") != 8
            or len(event_ids) != 8
            or len(set(event_ids)) != 8
            or group.get("human_chemistry_interpretation")
            != contract["human_chemistry_interpretation"]
            or group.get("human_post_state_interpretation")
            != contract["human_post_state_interpretation"]
            or group.get("CHEMISTRY_POSITIVE") is not True
            or group.get("TASK_RELEVANT_COVALENT_EVENT") is not True
            or group.get("negative_chemistry") is not False
            or group.get("task_domain_negative") is not False
            or group.get("protein_component_id") != "CYS"
            or group.get("protein_reactive_atom_id") != "SG"
            or group.get("ligand_component_id") != "POA"
            or group.get("ligand_reactive_atom_id") != "C2"
            or group.get("training_admission_created") is not False
            or group.get("POST_GEOMETRY_TRAINING_AUTHORITY") != "UNCHANGED"
        ):
            _fail("SUBGROUP_SEMANTICS_DRIFT:" + pdb_id)
        protein_chains: list[str] = []
        ligand_chains: list[str] = []
        for event_id in event_ids:
            if type(event_id) is not str:
                _fail("CANONICAL_EVENT_ID_INVALID")
            match = _EVENT_ID.fullmatch(event_id)
            if match is None or match.group("pdb") != pdb_id:
                _fail("CANONICAL_EVENT_IDENTITY_INVALID:" + event_id)
            protein_chains.append(match.group("protein_chain"))
            ligand_chains.append(match.group("ligand_chain"))
        if (
            tuple(protein_chains) != contract["protein_chains"]
            or tuple(ligand_chains) != contract["ligand_chains"]
            or all_ids.intersection(event_ids)
        ):
            _fail("SUBGROUP_EVENT_ID_INVENTORY_INVALID:" + pdb_id)
        all_ids.update(event_ids)
        result.append((group, event_ids))
    if len(all_ids) != 16:
        _fail("EXACT16_UNIQUE_EVENT_IDS_REQUIRED")
    return tuple(result)


def _summary_from_records(
    records: tuple[POASampleLevelEffectiveSupervisionRecordV1, ...],
) -> POASampleLevelEffectiveSupervisionSummaryV1:
    record_count = len(records)
    chemistry_positive_count = sum(record.chemistry_positive for record in records)
    reactive_count = sum(
        record.reactive_pair_authority_available for record in records
    )
    role_count = sum(
        record.role_partition_authority_available for record in records
    )
    return POASampleLevelEffectiveSupervisionSummaryV1(
        record_count=record_count,
        chemistry_positive_count=chemistry_positive_count,
        G1_count=sum(record.pdb_id == "4I3U" for record in records),
        G2_count=sum(record.pdb_id == "4I3V" for record in records),
        training_include_count=sum(
            record.training_use_disposition == reconciliation.TRAINING_INCLUDE
            for record in records
        ),
        training_excluded_positive_count=sum(
            record.chemistry_positive
            and record.training_use_disposition == reconciliation.TRAINING_EXCLUDE
            and record.human_training_excluded
            for record in records
        ),
        reactive_pair_authority_count=reactive_count,
        role_partition_authority_count=role_count,
        exact5_structural_mask_label_count=sum(
            record.task_structural_mask_labels_available
            and record.valid_task_ids == _VALID_TASK_IDS
            for record in records
        ),
        task_C_role_mask_available_count=sum(
            record.task_C_role_mask_available for record in records
        ),
        task_C_minimal_seed_authority_count=sum(
            record.task_C_minimal_seed_authority_available for record in records
        ),
        PRE_geometry_authority_count=sum(
            record.PRE_geometry_training_authority_available for record in records
        ),
        POST_geometry_authority_count=sum(
            record.POST_geometry_training_authority_available for record in records
        ),
        reaction_family_target_count=sum(
            record.reaction_family_target_available for record in records
        ),
        warhead_rule_target_count=sum(
            record.warhead_rule_target_available for record in records
        ),
        warhead_type_target_count=sum(
            record.warhead_type_target_available for record in records
        ),
        nongeometry_future_candidate_count=sum(
            record.nongeometry_future_candidate for record in records
        ),
        split_authoritative_count=sum(record.split_authoritative for record in records),
        training_admitted_count=sum(record.training_admitted for record in records),
        pair_candidate_domain_materialized_count=sum(
            record.pair_candidate_domain_materialized for record in records
        ),
        chemistry_state_training_target_count=sum(
            record.chemistry_state_training_target_available for record in records
        ),
        sample_level_chemistry_authority_available=(
            record_count == 16 and chemistry_positive_count == record_count
        ),
        sample_level_reactive_pair_authority_available=(
            record_count == 16 and reactive_count == record_count
        ),
        sample_level_role_partition_authority_available=(
            record_count == 16 and role_count == record_count
        ),
        reusable_chemistry_rule_created=False,
        reusable_reactive_pair_rule_created=False,
        reusable_role_authority_created=False,
        reaction_family_authority_created=False,
        warhead_rule_authority_created=False,
        loss_active=False,
        training_dataset_changed=False,
    )


def _compile_mapping(
    formal: Mapping[str, Any],
    normalized: reconciliation.NormalizedDecisionSource,
) -> POASampleLevelEffectiveSupervisionResultV1:
    if (
        formal.get("schema_version") != FORMAL_DECISION_SCHEMA
        or formal.get("review_unit_id") != REVIEW_UNIT_ID
        or formal.get("record_role")
        != "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
        or formal.get("decision_status") != "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION"
        or formal.get("ligand_component_id") != "POA"
    ):
        _fail("FORMAL_DECISION_IDENTITY_INVALID")
    if type(normalized) is not reconciliation.NormalizedDecisionSource:
        _fail("NORMALIZED_SOURCE_TYPE_INVALID")
    if (
        normalized.binding.schema_version != FORMAL_DECISION_SCHEMA
        or normalized.binding.review_unit_id != REVIEW_UNIT_ID
        or len(normalized.facts) != 16
    ):
        _fail("NORMALIZED_SOURCE_IDENTITY_INVALID")

    _validate_global_authority_boundaries(formal)
    runtime_profile, valid_task_ids = _validate_role_and_task_contract(formal)
    subgroups = _validated_subgroups(formal)
    facts = {fact.canonical_event_id: fact for fact in normalized.facts}
    source_event_ids = tuple(
        event_id for _group, event_ids in subgroups for event_id in event_ids
    )
    if len(facts) != 16 or set(facts) != set(source_event_ids):
        _fail("NORMALIZED_AND_FORMAL_EVENT_INVENTORY_MISMATCH")

    records: list[POASampleLevelEffectiveSupervisionRecordV1] = []
    for group, event_ids in subgroups:
        pdb_id = str(group["pdb_id"])
        for event_id in event_ids:
            fact = facts[event_id]
            if (
                fact.review_unit_id != REVIEW_UNIT_ID
                or fact.human_review_completed is not True
                or fact.legacy_completed_review_status
                != reconciliation.COMPLETED_HUMAN_POSITIVE
                or fact.task_relevance_disposition != reconciliation.TASK_RELEVANT
                or fact.chemistry_disposition != reconciliation.CHEMISTRY_POSITIVE
                or fact.training_disposition
                not in {
                    reconciliation.TRAINING_INCLUDE,
                    reconciliation.TRAINING_EXCLUDE,
                }
                or (fact.training_disposition == reconciliation.TRAINING_EXCLUDE)
                != fact.human_training_excluded
                or fact.source_decision_schema != normalized.binding.schema_version
                or fact.source_decision_sha256 != normalized.binding.sha256
                or fact.source_binding_path != normalized.binding.source_path
            ):
                _fail("NORMALIZED_FACT_SEMANTICS_INVALID:" + event_id)
            include = fact.training_disposition == reconciliation.TRAINING_INCLUDE
            if include != (pdb_id == "4I3U"):
                _fail("SUBGROUP_NORMALIZED_ROUTING_MISMATCH:" + event_id)
            records.append(
                POASampleLevelEffectiveSupervisionRecordV1(
                    schema_version=SCHEMA_VERSION,
                    canonical_event_id=event_id,
                    review_unit_id=fact.review_unit_id,
                    pdb_id=pdb_id,
                    subgroup_id=str(group["subgroup_id"]),
                    human_review_completed=fact.human_review_completed,
                    legacy_completed_review_status=(
                        fact.legacy_completed_review_status
                    ),
                    task_relevance_disposition=fact.task_relevance_disposition,
                    chemistry_disposition=fact.chemistry_disposition,
                    training_use_disposition=fact.training_disposition,
                    human_training_excluded=fact.human_training_excluded,
                    nongeometry_future_candidate=(
                        include and not fact.human_training_excluded
                    ),
                    chemistry_state_training_target_available=False,
                    target_residue_name="CYS",
                    target_residue_atom_id="SG",
                    ligand_component_id="POA",
                    ligand_reactive_atom_id="C2",
                    reactive_pair_authority_available=True,
                    pair_candidate_domain_materialized=False,
                    source_role_profile=SOURCE_ROLE_PROFILE,
                    runtime_role_profile=runtime_profile,
                    scaffold_atom_ids=_SCAFFOLD_ATOM_IDS,
                    linker_atom_ids=_LINKER_ATOM_IDS,
                    warhead_atom_ids=_WARHEAD_ATOM_IDS,
                    role_partition_authority_available=True,
                    valid_task_ids=valid_task_ids,
                    task_structural_mask_labels_available=True,
                    task_C_role_mask_available=True,
                    task_C_minimal_seed_authority_available=False,
                    precursor_evidence_status=(
                        "PRECURSOR_EVIDENCE_NOT_ESTABLISHED"
                    ),
                    PRE_reaction_graph_authority_available=False,
                    PRE_reaction_bond_order_authority_available=False,
                    PRE_geometry_training_authority_available=False,
                    POST_geometry_training_authority_available=False,
                    reaction_family_authority_available=False,
                    reaction_family_target_available=False,
                    warhead_rule_authority_available=False,
                    warhead_rule_target_available=False,
                    warhead_type_target_available=False,
                    split_authoritative=False,
                    training_admitted=False,
                )
            )
    record_tuple = tuple(records)
    result = POASampleLevelEffectiveSupervisionResultV1(
        records=record_tuple,
        summary=_summary_from_records(record_tuple),
        source_provenance=POASampleLevelEffectiveSupervisionSourceProvenanceV1(
            formal_decision_path=normalized.binding.source_path,
            formal_decision_path_namespace=normalized.binding.path_namespace,
            formal_decision_byte_count=normalized.binding.byte_count,
            formal_decision_sha256=normalized.binding.sha256,
            formal_decision_schema=normalized.binding.schema_version,
            review_unit_id=normalized.binding.review_unit_id,
            reconciliation_owner=_RECONCILIATION_OWNER,
            reconciliation_projection=_RECONCILIATION_PROJECTION,
        ),
    )
    validate_covapie_poa_sample_level_effective_supervision_v1(result)
    return result


def _compile_synthetic_formal_decision_mapping_v1(
    formal_decision: object,
) -> POASampleLevelEffectiveSupervisionResultV1:
    """Private portable-test entry point; never used for real source binding."""

    try:
        formal = _mapping(formal_decision, "FORMAL_DECISION_MAPPING_REQUIRED")
        payload = json.dumps(
            formal,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("ascii")
        binding = reconciliation.SourceBinding(
            source_path="synthetic/poa_formal_human_decision_v1.json",
            path_namespace="synthetic",
            byte_count=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            schema_version=FORMAL_DECISION_SCHEMA,
            review_unit_id=REVIEW_UNIT_ID,
        )
        normalized = reconciliation._project_poa_decision_mapping_v1(
            formal, binding
        )
        return _compile_mapping(formal, normalized)
    except POASampleLevelEffectiveSupervisionError:
        raise
    except Exception as error:
        raise POASampleLevelEffectiveSupervisionError(
            f"{ERROR_TOKEN}:SYNTHETIC_SOURCE_REJECTED:{type(error).__name__}:{error}"
        ) from error


def validate_covapie_poa_sample_level_effective_supervision_v1(
    result: object,
) -> bool:
    """Fail closed unless ``result`` is a complete inactive exact16 carrier."""

    if type(result) is not POASampleLevelEffectiveSupervisionResultV1:
        _fail("RESULT_TYPE_INVALID")
    records = result.records
    if (
        type(records) is not tuple
        or len(records) != 16
        or any(type(record) is not POASampleLevelEffectiveSupervisionRecordV1 for record in records)
        or len({record.canonical_event_id for record in records}) != 16
    ):
        _fail("RESULT_EXACT16_RECORDS_INVALID")
    for record in records:
        if (
            record.schema_version != SCHEMA_VERSION
            or record.review_unit_id != REVIEW_UNIT_ID
            or record.pdb_id not in _SUBGROUP_CONTRACT
            or record.subgroup_id
            != _SUBGROUP_CONTRACT[record.pdb_id]["subgroup_id"]
            or record.human_review_completed is not True
            or record.legacy_completed_review_status
            != reconciliation.COMPLETED_HUMAN_POSITIVE
            or record.task_relevance_disposition != reconciliation.TASK_RELEVANT
            or record.chemistry_positive is not True
            or record.chemistry_negative is not False
            or record.training_use_disposition
            not in {
                reconciliation.TRAINING_INCLUDE,
                reconciliation.TRAINING_EXCLUDE,
            }
            or (record.training_use_disposition == reconciliation.TRAINING_EXCLUDE)
            != record.human_training_excluded
            or record.nongeometry_future_candidate
            != (
                record.training_use_disposition == reconciliation.TRAINING_INCLUDE
                and not record.human_training_excluded
            )
            or record.chemistry_state_training_target_available is not False
            or (
                record.target_residue_name,
                record.target_residue_atom_id,
                record.ligand_component_id,
                record.ligand_reactive_atom_id,
            )
            != ("CYS", "SG", "POA", "C2")
            or record.reactive_pair_authority_available is not True
            or record.pair_candidate_domain_materialized is not False
            or record.source_role_profile != SOURCE_ROLE_PROFILE
            or record.runtime_role_profile != RUNTIME_ROLE_PROFILE
            or record.scaffold_atom_ids != _SCAFFOLD_ATOM_IDS
            or record.linker_atom_ids != _LINKER_ATOM_IDS
            or record.warhead_atom_ids != _WARHEAD_ATOM_IDS
            or record.role_partition_authority_available is not True
            or record.valid_task_ids != _VALID_TASK_IDS
            or record.not_applicable_task_ids != ()
            or record.task_structural_mask_labels_available is not True
            or record.task_C_role_mask_available is not True
            or record.task_C_minimal_seed_authority_available is not False
            or record.full_task_C_training_supervision_ready is not False
            or record.precursor_evidence_status
            != "PRECURSOR_EVIDENCE_NOT_ESTABLISHED"
            or record.PRE_reaction_graph_authority_available is not False
            or record.PRE_reaction_bond_order_authority_available is not False
            or record.PRE_geometry_training_authority_available is not False
            or record.POST_geometry_training_authority_available is not False
            or record.geometry_training_target_available is not False
            or record.reaction_family_authority_available is not False
            or record.reaction_family_target_available is not False
            or record.warhead_rule_authority_available is not False
            or record.warhead_rule_target_available is not False
            or record.warhead_type_target_available is not False
            or record.split_authoritative is not False
            or record.training_admitted is not False
        ):
            _fail("RESULT_RECORD_SEMANTICS_INVALID:" + record.canonical_event_id)
    expected_summary = _summary_from_records(records)
    if result.summary != expected_summary:
        _fail("RESULT_SUMMARY_NOT_DERIVED_FROM_RECORDS")
    expected_counts = (
        result.summary.record_count,
        result.summary.chemistry_positive_count,
        result.summary.G1_count,
        result.summary.G2_count,
        result.summary.training_include_count,
        result.summary.training_excluded_positive_count,
        result.summary.reactive_pair_authority_count,
        result.summary.role_partition_authority_count,
        result.summary.exact5_structural_mask_label_count,
        result.summary.task_C_role_mask_available_count,
        result.summary.task_C_minimal_seed_authority_count,
        result.summary.PRE_geometry_authority_count,
        result.summary.POST_geometry_authority_count,
        result.summary.reaction_family_target_count,
        result.summary.warhead_rule_target_count,
        result.summary.warhead_type_target_count,
        result.summary.nongeometry_future_candidate_count,
        result.summary.split_authoritative_count,
        result.summary.training_admitted_count,
        result.summary.pair_candidate_domain_materialized_count,
        result.summary.chemistry_state_training_target_count,
    )
    if expected_counts != (
        16,
        16,
        8,
        8,
        8,
        8,
        16,
        16,
        16,
        16,
        0,
        0,
        0,
        0,
        0,
        0,
        8,
        0,
        0,
        0,
        0,
    ):
        _fail("RESULT_SUMMARY_COUNTS_INVALID")
    summary = result.summary
    if (
        summary.sample_level_chemistry_authority_available is not True
        or summary.sample_level_reactive_pair_authority_available is not True
        or summary.sample_level_role_partition_authority_available is not True
        or summary.reusable_chemistry_rule_created is not False
        or summary.reusable_reactive_pair_rule_created is not False
        or summary.reusable_role_authority_created is not False
        or summary.reaction_family_authority_created is not False
        or summary.warhead_rule_authority_created is not False
        or summary.loss_active is not False
        or summary.training_dataset_changed is not False
    ):
        _fail("RESULT_AUTHORITY_BOUNDARY_INVALID")
    provenance = result.source_provenance
    if (
        type(provenance)
        is not POASampleLevelEffectiveSupervisionSourceProvenanceV1
        or not provenance.formal_decision_path
        or provenance.formal_decision_path_namespace
        not in {"repository_parent_relative", "synthetic"}
        or type(provenance.formal_decision_byte_count) is not int
        or provenance.formal_decision_byte_count <= 0
        or not re.fullmatch(r"[0-9a-f]{64}", provenance.formal_decision_sha256)
        or provenance.formal_decision_schema != FORMAL_DECISION_SCHEMA
        or provenance.review_unit_id != REVIEW_UNIT_ID
        or provenance.reconciliation_owner != _RECONCILIATION_OWNER
        or provenance.reconciliation_projection != _RECONCILIATION_PROJECTION
    ):
        _fail("RESULT_SOURCE_PROVENANCE_INVALID")
    return True


def build_covapie_poa_sample_level_effective_supervision_v1(
    formal_decision_payload: bytes,
) -> POASampleLevelEffectiveSupervisionResultV1:
    """Build the exact16 read-only carrier from the frozen real payload."""

    try:
        normalized = reconciliation.project_poa_formal_decision_v1(
            formal_decision_payload
        )
        formal = json.loads(formal_decision_payload.decode("utf-8"))
        if type(formal) is not dict:
            _fail("FORMAL_DECISION_OBJECT_REQUIRED")
        result = _compile_mapping(formal, normalized)
        provenance = result.source_provenance
        if (
            provenance.formal_decision_path != FORMAL_DECISION_PATH
            or provenance.formal_decision_path_namespace
            != "repository_parent_relative"
            or provenance.formal_decision_byte_count != FORMAL_DECISION_BYTE_COUNT
            or provenance.formal_decision_sha256 != FORMAL_DECISION_SHA256
        ):
            _fail("PUBLIC_REAL_SOURCE_PROVENANCE_INVALID")
        return result
    except POASampleLevelEffectiveSupervisionError:
        raise
    except Exception as error:
        raise POASampleLevelEffectiveSupervisionError(
            f"{ERROR_TOKEN}:PUBLIC_SOURCE_REJECTED:{type(error).__name__}:{error}"
        ) from error
