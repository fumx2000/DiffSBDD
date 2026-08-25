"""Build the inactive POA exact16 real-structure tensor preview V1.

The public entry point accepts caller-owned gzip mmCIF bytes, the published
POA sample-level metadata carrier, and explicit Exact5 task ids.  It reuses
the checkpoint-compatible FFQ structural primitives and the existing
``CovapieCurrent11TrainingSupervisionTensorsV1`` schema.  It performs no
filesystem access, model execution, loss execution, admission, or training.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import hashlib
import math
import re
from typing import Mapping, NoReturn, Sequence

import torch

from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as direct_runtime,
)
from covalent_ext import (
    covapie_ffq_real_structure_microbatch_alignment_v1 as structural_owner,
)
from covalent_ext import (
    covapie_mmcif_ligand_atom_identity_extractor_v1 as ligand_owner,
)
from covalent_ext import (
    covapie_poa_sample_level_effective_supervision_v1 as metadata_owner,
)
from covalent_ext import (
    covapie_tensor_label_and_loss_mask_contract_design_v1 as pair_owner,
)
from covalent_ext import (
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as feature_owner,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1,
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


__all__ = (
    "POAExact16RealStructureTensorPreviewError",
    "POARealStructureSourceBindingV1",
    "POAExact16RealStructureTensorPreviewSummaryV1",
    "POAExact16RealStructureTensorPreviewV1",
    "assemble_covapie_poa_exact16_real_structure_tensor_preview_v1",
    "validate_covapie_poa_exact16_real_structure_tensor_preview_v1",
)


ERROR_TOKEN = "COVAPIE_POA_EXACT16_REAL_STRUCTURE_TENSOR_PREVIEW_V1_ERROR"
CHECKPOINT_FEATURE_WIDTH_V1 = 10
EXPECTED_REAL_STRUCTURE_BINDINGS_V1 = {
    "4I3U": (
        763278,
        "518c56586f11896b1dd080d867a5bf9d231f6c1362db24c436a7ef2cb11c9a28",
    ),
    "4I3V": (
        783383,
        "6d9ed0e7d5888318cf9a9f1715b46ded461a2936dae0cff3323bbf54a3a6d1de",
    ),
}
EXPECTED_REAL_PDB_IDS_V1 = tuple(EXPECTED_REAL_STRUCTURE_BINDINGS_V1)
EXPECTED_LIGAND_MODEL_ORDER_V1 = (
    "C1",
    "C2",
    "O2",
    "O1P",
    "O2P",
    "O3P",
    "P",
)
EXPECTED_LIGAND_CHANNELS_V1 = (0, 0, 2, 2, 2, 2, 7)
EXPECTED_TARGET_CYS_MODEL_ORDER_V1 = ("N", "CA", "C", "O", "CB", "SG")
EXPECTED_TARGET_CYS_CHANNELS_V1 = (1, 0, 0, 2, 0, 3)
EXPECTED_ROLE_ID_MODEL_ORDER_V1 = (1, 2, 2, 0, 0, 0, 0)
EXPECTED_MASK_COUNTS_V1 = ((2, 5), (3, 4), (6, 1), (4, 3), (7, 0))
EXPECTED_MODEL_INPUT_FIELDS_V1 = frozenset(
    (
        "names",
        "receptors",
        "lig_coords",
        "pocket_coords",
        "lig_one_hot",
        "pocket_one_hot",
        "lig_source_row_index",
        "pocket_source_row_index",
        "lig_parser_local_index",
        "pocket_parser_local_index",
        "num_lig_atoms",
        "num_pocket_nodes",
        "lig_mask",
        "pocket_mask",
    )
)
_EVENT_ID = re.compile(
    r"^COVAPIE_CYS_SG_EVENT_V1:"
    r"(?P<pdb>4I3[UV]):(?P<protein_chain>[A-H]):CYS:291-:SG:"
    r"(?P<ligand_asym>[A-Z0-9]+):POA:C2$"
)
_EXPECTED_LIGAND_ASYMS = {
    "4I3U": tuple("IJKLMNOP"),
    "4I3V": ("J", "L", "N", "P", "R", "T", "V", "W"),
}
_EXPECTED_SUBGROUPS = {
    "4I3U": "POA_SUBGROUP_G1_4I3U_THIOHEMIACETAL",
    "4I3V": "POA_SUBGROUP_G2_4I3V_THIOESTER",
}


class POAExact16RealStructureTensorPreviewError(ValueError):
    """Raised unless every POA structural/tensor preview invariant holds."""


def _fail(reason: str) -> NoReturn:
    raise POAExact16RealStructureTensorPreviewError(f"{ERROR_TOKEN}:{reason}")


@dataclass(frozen=True, slots=True)
class POARealStructureSourceBindingV1:
    pdb_id: str
    byte_count: int
    sha256: str


@dataclass(frozen=True, slots=True)
class POAExact16RealStructureTensorPreviewSummaryV1:
    sample_count: int
    ligand_node_count_per_sample: tuple[int, ...]
    pocket_node_count_per_sample: tuple[int, ...]
    total_ligand_node_count: int
    total_pocket_node_count: int
    pair_candidate_count: int
    pair_positive_count: int
    pair_negative_count: int
    G1_include_count: int
    G2_training_excluded_positive_count: int
    sample_training_admitted_count: int
    active_diffusion_loss_count: int
    active_pair_loss_count: int
    active_geometry_loss_count: int
    observed_pair_distance_valid_count: int
    PRE_geometry_target_valid_count: int
    POST_geometry_target_valid_count: int
    task_C_minimal_seed_authority_count: int


@dataclass(frozen=True)
class POAExact16RealStructureTensorPreviewV1:
    sample_identities: tuple[str, ...]
    structure_source_bindings: tuple[POARealStructureSourceBindingV1, ...]
    canonical_task_ids: tuple[int, ...]
    training_use_dispositions: tuple[str, ...]
    human_training_excluded: tuple[bool, ...]
    nongeometry_future_candidate: tuple[bool, ...]

    ligand_node_offsets: tuple[int, ...]
    pocket_node_offsets: tuple[int, ...]
    ligand_reactive_atom_local_index: torch.Tensor
    ligand_reactive_atom_flat_index: torch.Tensor

    model_input_batch: dict[str, object]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1
    summary: POAExact16RealStructureTensorPreviewSummaryV1

    structural_coordinates_centered: bool = True
    feature_semantics_audit_already_completed: bool = True
    feature_semantics_redesigned: bool = False
    model_architecture_change_required: bool = False
    model_forward_executed: bool = False
    loss_executed: bool = False
    backward_executed: bool = False
    optimizer_created: bool = False
    optimizer_step_executed: bool = False
    trainer_fit_executed: bool = False
    training_admission_created: bool = False
    training_dataset_changed: bool = False
    training_performed: bool = False
    finetune_performed: bool = False
    ready_for_training: bool = False


def _actual_structure_bindings_v1(
    structure_payloads_by_pdb: Mapping[str, bytes],
) -> tuple[POARealStructureSourceBindingV1, ...]:
    return tuple(
        POARealStructureSourceBindingV1(
            pdb_id=pdb_id,
            byte_count=len(structure_payloads_by_pdb[pdb_id]),
            sha256=hashlib.sha256(structure_payloads_by_pdb[pdb_id]).hexdigest(),
        )
        for pdb_id in structure_payloads_by_pdb
    )


def _validate_structure_payload_bindings_v1(
    structure_payloads_by_pdb: object,
    *,
    expected_bindings: Mapping[str, tuple[int, str]],
) -> tuple[POARealStructureSourceBindingV1, ...]:
    """Validate exact caller bytes; private expected bindings aid portable tests."""

    if not isinstance(structure_payloads_by_pdb, Mapping):
        _fail("STRUCTURE_PAYLOAD_MAPPING_REQUIRED")
    if set(structure_payloads_by_pdb) != set(expected_bindings):
        _fail("STRUCTURE_PAYLOAD_MAPPING_KEYS_INVALID")
    ordered_payloads: dict[str, bytes] = {}
    for pdb_id in expected_bindings:
        payload = structure_payloads_by_pdb[pdb_id]
        expected_bytes, expected_sha256 = expected_bindings[pdb_id]
        if type(payload) is not bytes:
            _fail(f"STRUCTURE_PAYLOAD_EXACT_BYTES_REQUIRED:{pdb_id}")
        actual_sha256 = hashlib.sha256(payload).hexdigest()
        if len(payload) != expected_bytes or actual_sha256 != expected_sha256:
            _fail(f"STRUCTURE_PAYLOAD_SOURCE_BINDING_INVALID:{pdb_id}")
        ordered_payloads[pdb_id] = payload
    return _actual_structure_bindings_v1(ordered_payloads)


def _validate_effective_record_v1(
    record: object,
) -> metadata_owner.POASampleLevelEffectiveSupervisionRecordV1:
    if type(record) is not metadata_owner.POASampleLevelEffectiveSupervisionRecordV1:
        _fail("EFFECTIVE_SUPERVISION_RECORD_TYPE_INVALID")
    match = _EVENT_ID.fullmatch(record.canonical_event_id)
    if match is None:
        _fail("METADATA_EVENT_ID_INVALID")
    identity = match.groupdict()
    pdb_id = identity["pdb"]
    chain_ordinal = ord(identity["protein_chain"]) - ord("A")
    if (
        record.pdb_id != pdb_id
        or identity["ligand_asym"] != _EXPECTED_LIGAND_ASYMS[pdb_id][chain_ordinal]
        or record.subgroup_id != _EXPECTED_SUBGROUPS[pdb_id]
        or record.chemistry_positive is not True
        or record.chemistry_negative is not False
        or (
            record.target_residue_name,
            record.target_residue_atom_id,
            record.ligand_component_id,
            record.ligand_reactive_atom_id,
        )
        != ("CYS", "SG", "POA", "C2")
        or record.reactive_pair_authority_available is not True
        or record.scaffold_atom_ids != ("P", "O1P", "O2P", "O3P")
        or record.linker_atom_ids != ("C1",)
        or record.warhead_atom_ids != ("C2", "O2")
        or record.role_partition_authority_available is not True
        or record.runtime_role_profile != direct_runtime.STRICT_LINKER_PRESENT_V1
        or record.valid_task_ids != (0, 1, 2, 3, 4)
        or record.task_structural_mask_labels_available is not True
        or record.task_C_role_mask_available is not True
        or record.task_C_minimal_seed_authority_available is not False
        or record.PRE_geometry_training_authority_available is not False
        or record.POST_geometry_training_authority_available is not False
        or record.training_admitted is not False
    ):
        _fail("METADATA_RECORD_SEMANTICS_INVALID:" + record.canonical_event_id)
    excluded = pdb_id == "4I3V"
    if (
        record.human_training_excluded is not excluded
        or record.nongeometry_future_candidate is not (not excluded)
        or record.training_use_disposition
        != ("EXCLUDE_FROM_TRAINING_ONLY" if excluded else "INCLUDE")
    ):
        _fail("METADATA_ROUTING_INVALID:" + record.canonical_event_id)
    return record


def _task_ids_for_records_v1(
    records: Sequence[metadata_owner.POASampleLevelEffectiveSupervisionRecordV1],
    canonical_task_ids_by_event: object,
) -> tuple[int, ...]:
    if not isinstance(canonical_task_ids_by_event, Mapping):
        _fail("CANONICAL_TASK_MAPPING_REQUIRED")
    identities = tuple(record.canonical_event_id for record in records)
    if set(canonical_task_ids_by_event) != set(identities):
        _fail("CANONICAL_TASK_MAPPING_KEYS_INVALID")
    tasks = tuple(canonical_task_ids_by_event[event_id] for event_id in identities)
    if any(type(task) is not int or task not in (0, 1, 2, 3, 4) for task in tasks):
        _fail("CANONICAL_TASK_ID_INVALID")
    return tasks  # type: ignore[return-value]


def _role_projection_v1(
    record: metadata_owner.POASampleLevelEffectiveSupervisionRecordV1,
    ligand_rows: Sequence[Mapping[str, object]],
    source_to_projected: Sequence[int | None],
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    def project(atom_ids: Sequence[str]) -> tuple[int, ...]:
        projected: list[int] = []
        for atom_id in atom_ids:
            matches = tuple(
                index
                for index, row in enumerate(ligand_rows)
                if row.get("atom_id") == atom_id
            )
            if len(matches) != 1:
                _fail("ROLE_ATOM_ID_NOT_EXACTLY_ONE:" + atom_id)
            local_index = source_to_projected[matches[0]]
            if type(local_index) is not int:
                _fail("ROLE_ATOM_MISSING_AFTER_PROJECTION:" + atom_id)
            projected.append(local_index)
        return tuple(projected)

    scaffold = project(record.scaffold_atom_ids)
    linker = project(record.linker_atom_ids)
    warhead = project(record.warhead_atom_ids)
    role_ids = [-1] * len(EXPECTED_LIGAND_MODEL_ORDER_V1)
    for role_id, local_indices in enumerate((scaffold, linker, warhead)):
        for local_index in local_indices:
            if not 0 <= local_index < len(role_ids) or role_ids[local_index] != -1:
                _fail("ROLE_PROJECTION_OVERLAP_OR_RANGE_INVALID")
            role_ids[local_index] = role_id
    if tuple(role_ids) != EXPECTED_ROLE_ID_MODEL_ORDER_V1:
        _fail("ROLE_PROJECTION_MODEL_ORDER_INVALID")
    return scaffold, linker, warhead, tuple(role_ids)


def _offsets_v1(counts: Sequence[int]) -> tuple[int, ...]:
    result = [0]
    for count in counts:
        if type(count) is not int or count <= 0:
            _fail("NODE_COUNT_INVALID")
        result.append(result[-1] + count)
    return tuple(result)


def _summary_v1(
    preview: POAExact16RealStructureTensorPreviewV1,
) -> POAExact16RealStructureTensorPreviewSummaryV1:
    supervision = preview.supervision
    ligand_counts = tuple(
        int(value) for value in preview.model_input_batch["num_lig_atoms"].tolist()
    )
    pocket_counts = tuple(
        int(value)
        for value in preview.model_input_batch["num_pocket_nodes"].tolist()
    )
    return POAExact16RealStructureTensorPreviewSummaryV1(
        sample_count=len(preview.sample_identities),
        ligand_node_count_per_sample=ligand_counts,
        pocket_node_count_per_sample=pocket_counts,
        total_ligand_node_count=sum(ligand_counts),
        total_pocket_node_count=sum(pocket_counts),
        pair_candidate_count=len(supervision.pair_candidate_batch_index),
        pair_positive_count=int(supervision.pair_candidate_is_positive.sum().item()),
        pair_negative_count=int(supervision.pair_candidate_is_negative.sum().item()),
        G1_include_count=sum(
            disposition == "INCLUDE" and not excluded
            for disposition, excluded in zip(
                preview.training_use_dispositions,
                preview.human_training_excluded,
            )
        ),
        G2_training_excluded_positive_count=sum(
            disposition == "EXCLUDE_FROM_TRAINING_ONLY" and excluded
            for disposition, excluded in zip(
                preview.training_use_dispositions,
                preview.human_training_excluded,
            )
        ),
        sample_training_admitted_count=int(
            supervision.sample_training_admitted.sum().item()
        ),
        active_diffusion_loss_count=int(
            supervision.ligand_active_diffusion_loss_mask.sum().item()
        ),
        active_pair_loss_count=int(
            supervision.pair_head_candidate_loss_mask.sum().item()
            + supervision.pair_contrastive_sample_loss_mask.sum().item()
        ),
        active_geometry_loss_count=int(
            supervision.pre_post_geometry_component_loss_mask.sum().item()
        ),
        observed_pair_distance_valid_count=int(
            supervision.observed_complex_pair_distance_valid.sum().item()
        ),
        PRE_geometry_target_valid_count=int(
            supervision.pre_post_geometry_component_valid_mask[:, 0].sum().item()
        ),
        POST_geometry_target_valid_count=int(
            supervision.pre_post_geometry_component_valid_mask[:, 1].sum().item()
        ),
        task_C_minimal_seed_authority_count=int(
            supervision.ligand_minimal_seed_or_anchor_valid.sum().item()
        ),
    )


def _assemble_core_v1(
    *,
    structure_payloads_by_pdb: object,
    records: object,
    canonical_task_ids_by_event: object,
    device: object = "cpu",
    expected_structure_bindings: Mapping[str, tuple[int, str]] | None = None,
    require_real_exact16: bool = False,
) -> POAExact16RealStructureTensorPreviewV1:
    """Private synthetic-capable core; only exact source SHA binding is optional."""

    try:
        if type(records) not in (tuple, list) or not records:
            _fail("EFFECTIVE_SUPERVISION_RECORDS_NONEMPTY_REQUIRED")
        record_tuple = tuple(_validate_effective_record_v1(record) for record in records)
        identities = tuple(record.canonical_event_id for record in record_tuple)
        if len(identities) != len(set(identities)):
            _fail("CROSS_SAMPLE_DUPLICATE_EVENT")
        pdb_ids = tuple(dict.fromkeys(record.pdb_id for record in record_tuple))
        if not isinstance(structure_payloads_by_pdb, Mapping):
            _fail("STRUCTURE_PAYLOAD_MAPPING_REQUIRED")
        if set(structure_payloads_by_pdb) != set(pdb_ids):
            _fail("STRUCTURE_PAYLOAD_MAPPING_KEYS_INVALID")
        ordered_payloads: dict[str, bytes] = {}
        for pdb_id in pdb_ids:
            payload = structure_payloads_by_pdb[pdb_id]
            if type(payload) is not bytes:
                _fail(f"STRUCTURE_PAYLOAD_EXACT_BYTES_REQUIRED:{pdb_id}")
            ordered_payloads[pdb_id] = payload
        if expected_structure_bindings is not None:
            bindings = _validate_structure_payload_bindings_v1(
                ordered_payloads,
                expected_bindings=expected_structure_bindings,
            )
        else:
            bindings = _actual_structure_bindings_v1(ordered_payloads)
        tasks = _task_ids_for_records_v1(
            record_tuple, canonical_task_ids_by_event
        )
        try:
            tensor_device = torch.device(device)
        except (TypeError, RuntimeError) as error:
            raise POAExact16RealStructureTensorPreviewError(
                f"{ERROR_TOKEN}:TORCH_DEVICE_INVALID"
            ) from error

        ligand_coordinates: list[torch.Tensor] = []
        pocket_coordinates: list[torch.Tensor] = []
        ligand_one_hot: list[torch.Tensor] = []
        pocket_one_hot: list[torch.Tensor] = []
        ligand_sources: list[torch.Tensor] = []
        pocket_sources: list[torch.Tensor] = []
        ligand_parser_indices: list[torch.Tensor] = []
        pocket_parser_indices: list[torch.Tensor] = []
        role_parts: list[torch.Tensor] = []
        generation_parts: list[torch.Tensor] = []
        fixed_parts: list[torch.Tensor] = []
        membership_parts: list[torch.Tensor] = []
        reactive_parts: list[torch.Tensor] = []
        anchor_parts: list[torch.Tensor] = []
        ligand_counts: list[int] = []
        pocket_counts: list[int] = []
        target_members_by_sample: list[tuple[int, ...]] = []
        target_reactive_local: list[int] = []
        ligand_reactive_local: list[int] = []
        observed_distances: list[float] = []

        for sample, (record, task_id) in enumerate(zip(record_tuple, tasks)):
            payload = ordered_payloads[record.pdb_id]
            try:
                identity = structural_owner._event_identity(asdict(record))
                ligand_rows = (
                    ligand_owner.extract_covapie_ligand_atom_identity_rows_from_cif_gz_v1(
                        cif_gz_payload=payload,
                        ligand_component_id=identity["ligand"],
                        label_asym_id=identity["ligand_asym"],
                        model_num=1,
                    )
                )
                atom_rows = structural_owner._parse_and_crosscheck_atom_site(
                    payload, expected_pdb_id=identity["pdb"]
                )
                ligand_preprojection = structural_owner._crosscheck_ligand_rows(
                    ligand_rows, atom_rows
                )
                (
                    ligand_retained,
                    ligand_channels,
                    ligand_source_to_projected,
                ) = structural_owner._projection(
                    ligand_preprojection, domain="ligand"
                )
                scaffold, linker, warhead, role_ids = _role_projection_v1(
                    record, ligand_rows, ligand_source_to_projected
                )
                retained_atom_ids = tuple(
                    structural_owner._atom_value(row, "label_atom_id")
                    for _, row in ligand_retained
                )
                if (
                    retained_atom_ids != EXPECTED_LIGAND_MODEL_ORDER_V1
                    or ligand_channels != EXPECTED_LIGAND_CHANNELS_V1
                ):
                    _fail("LIGAND_RETAINED_MODEL_ORDER_OR_CHANNEL_INVALID")
                mask = direct_runtime.build_mask_for_role_profile_v1(
                    role_profile=record.runtime_role_profile,
                    canonical_task_id=task_id,
                    scaffold_atoms=scaffold,
                    linker_atoms=linker,
                    warhead_atoms=warhead,
                    num_ligand_atoms=len(ligand_retained),
                )
                pocket_preprojection = (
                    structural_owner._build_checkpoint_model_input_pocket_v1(
                        list(enumerate(atom_rows)), ligand_retained
                    )
                )
                pocket_retained, pocket_channels, _ = structural_owner._projection(
                    pocket_preprojection, domain="pocket"
                )
                target_members, target_reactive = structural_owner._target_indices(
                    pocket_retained, identity
                )
                target_atom_ids = tuple(
                    structural_owner._preferred_atom_name(
                        pocket_retained[index][1]
                    )
                    for index in target_members
                )
                target_channels = tuple(
                    pocket_channels[index] for index in target_members
                )
                if (
                    target_atom_ids != EXPECTED_TARGET_CYS_MODEL_ORDER_V1
                    or target_channels != EXPECTED_TARGET_CYS_CHANNELS_V1
                    or target_members[-1] != target_reactive
                ):
                    _fail("TARGET_CYS_EXACT6_MODEL_ORDER_OR_CHANNEL_INVALID")
                ligand_reactive = structural_owner._ligand_reactive_index(
                    ligand_rows,
                    ligand_source_to_projected,
                    record.ligand_reactive_atom_id,
                )
                if ligand_reactive != 1:
                    _fail("LIGAND_C2_RETAINED_LOCAL_INDEX_NOT_ONE")
                raw_ligand = structural_owner._coordinates(
                    ligand_retained, domain="ligand", device=tensor_device
                )
                raw_pocket = structural_owner._coordinates(
                    pocket_retained, domain="pocket", device=tensor_device
                )
                centered_ligand, centered_pocket = (
                    structural_owner._checkpoint_center_coordinates_v1(
                        raw_ligand, raw_pocket
                    )
                )
            except POAExact16RealStructureTensorPreviewError:
                raise
            except Exception as error:
                _fail(
                    f"SAMPLE_{sample}_STRUCTURAL_OWNER_REJECTED:"
                    f"{type(error).__name__}:{error}"
                )

            ligand_count = len(ligand_retained)
            pocket_count = len(pocket_retained)
            generation = torch.zeros(
                ligand_count, dtype=torch.bool, device=tensor_device
            )
            generation[list(mask.masked_atoms)] = True
            fixed = ~generation
            if (int(generation.sum().item()), int(fixed.sum().item())) != (
                EXPECTED_MASK_COUNTS_V1[task_id]
            ):
                _fail(f"SAMPLE_{sample}_EXACT5_MASK_COUNTS_INVALID")
            membership = torch.zeros(
                pocket_count, dtype=torch.bool, device=tensor_device
            )
            membership[list(target_members)] = True
            reactive = torch.zeros(
                pocket_count, dtype=torch.bool, device=tensor_device
            )
            reactive[target_reactive] = True
            target_coordinate = centered_pocket[target_reactive]
            anchor = torch.linalg.vector_norm(
                centered_ligand - target_coordinate, dim=1, keepdim=True
            )
            observed = float(anchor[ligand_reactive, 0].item())
            if not math.isfinite(observed) or observed < 0:
                _fail(f"SAMPLE_{sample}_OBSERVED_PAIR_DISTANCE_INVALID")

            ligand_coordinates.append(centered_ligand)
            pocket_coordinates.append(centered_pocket)
            ligand_one_hot.append(
                structural_owner._one_hot(ligand_channels, device=tensor_device)
            )
            pocket_one_hot.append(
                structural_owner._one_hot(pocket_channels, device=tensor_device)
            )
            ligand_sources.append(
                torch.tensor(
                    tuple(index for index, _ in ligand_retained),
                    dtype=torch.long,
                    device=tensor_device,
                )
            )
            pocket_sources.append(
                torch.tensor(
                    tuple(index for index, _ in pocket_retained),
                    dtype=torch.long,
                    device=tensor_device,
                )
            )
            ligand_parser_indices.append(
                torch.arange(ligand_count, dtype=torch.long, device=tensor_device)
            )
            pocket_parser_indices.append(
                torch.arange(pocket_count, dtype=torch.long, device=tensor_device)
            )
            role_parts.append(
                torch.tensor(role_ids, dtype=torch.long, device=tensor_device)
            )
            generation_parts.append(generation)
            fixed_parts.append(fixed)
            membership_parts.append(membership)
            reactive_parts.append(reactive)
            anchor_parts.append(anchor)
            ligand_counts.append(ligand_count)
            pocket_counts.append(pocket_count)
            target_members_by_sample.append(target_members)
            target_reactive_local.append(target_reactive)
            ligand_reactive_local.append(ligand_reactive)
            observed_distances.append(observed)

        ligand_offsets = _offsets_v1(ligand_counts)
        pocket_offsets = _offsets_v1(pocket_counts)
        ligand_total = ligand_offsets[-1]
        pocket_total = pocket_offsets[-1]
        target_reactive_flat = tuple(
            pocket_offsets[sample] + local
            for sample, local in enumerate(target_reactive_local)
        )
        ligand_reactive_flat = tuple(
            ligand_offsets[sample] + local
            for sample, local in enumerate(ligand_reactive_local)
        )
        pair_specs = tuple(
            pair_owner.PairCandidateSampleSpec(
                batch_sample_index_0based=sample,
                retained_ligand_count=ligand_counts[sample],
                retained_pocket_count=pocket_counts[sample],
                target_residue_pocket_local_indices=target_members_by_sample[sample],
                positive_ligand_local_index=ligand_reactive_local[sample],
                positive_pocket_local_index=target_reactive_local[sample],
            )
            for sample in range(len(record_tuple))
        )
        try:
            pair_projection = pair_owner.build_pair_candidate_records_v1(
                pair_specs, ligand_offsets, pocket_offsets
            )
        except ValueError as error:
            raise POAExact16RealStructureTensorPreviewError(
                f"{ERROR_TOKEN}:PAIR_CANDIDATE_PROJECTION_INVALID:{error}"
            ) from error
        if (
            any(
                pair_projection.pair_candidate_offsets[index + 1]
                - pair_projection.pair_candidate_offsets[index]
                != 42
                for index in range(len(record_tuple))
            )
            or not all(pair_projection.pair_positive_candidate_valid)
            or any(count != 41 for count in pair_projection.pair_negative_count)
        ):
            _fail("PAIR_CANDIDATE_EXACT42_DOMAIN_INVALID")

        batch_size = len(record_tuple)
        lig_mask = torch.repeat_interleave(
            torch.arange(batch_size, dtype=torch.long, device=tensor_device),
            torch.tensor(ligand_counts, dtype=torch.long, device=tensor_device),
        )
        pocket_mask = torch.repeat_interleave(
            torch.arange(batch_size, dtype=torch.long, device=tensor_device),
            torch.tensor(pocket_counts, dtype=torch.long, device=tensor_device),
        )
        model_input_batch: dict[str, object] = {
            "names": list(identities),
            "receptors": [record.pdb_id for record in record_tuple],
            "lig_coords": torch.cat(ligand_coordinates),
            "pocket_coords": torch.cat(pocket_coordinates),
            "lig_one_hot": torch.cat(ligand_one_hot),
            "pocket_one_hot": torch.cat(pocket_one_hot),
            "lig_source_row_index": torch.cat(ligand_sources),
            "pocket_source_row_index": torch.cat(pocket_sources),
            "lig_parser_local_index": torch.cat(ligand_parser_indices),
            "pocket_parser_local_index": torch.cat(pocket_parser_indices),
            "num_lig_atoms": torch.tensor(
                ligand_counts, dtype=torch.long, device=tensor_device
            ),
            "num_pocket_nodes": torch.tensor(
                pocket_counts, dtype=torch.long, device=tensor_device
            ),
            "lig_mask": lig_mask,
            "pocket_mask": pocket_mask,
        }
        pair_count = len(pair_projection.records)
        supervision = CovapieCurrent11TrainingSupervisionTensorsV1(
            sample_training_admitted=torch.zeros(
                batch_size, dtype=torch.bool, device=tensor_device
            ),
            canonical_task_id=torch.tensor(
                tasks, dtype=torch.long, device=tensor_device
            ),
            canonical_task_valid=torch.ones(
                batch_size, dtype=torch.bool, device=tensor_device
            ),
            ligand_role_id=torch.cat(role_parts),
            ligand_role_valid=torch.ones(
                ligand_total, dtype=torch.bool, device=tensor_device
            ),
            ligand_base_generation_mask=torch.cat(generation_parts).unsqueeze(1),
            ligand_base_fixed_mask=torch.cat(fixed_parts).unsqueeze(1),
            ligand_base_target_mask=torch.cat(generation_parts).unsqueeze(1),
            ligand_base_context_mask=torch.cat(fixed_parts).unsqueeze(1),
            ligand_active_diffusion_loss_mask=torch.zeros(
                (ligand_total, 1), dtype=torch.bool, device=tensor_device
            ),
            ligand_minimal_seed_or_anchor_mask=torch.zeros(
                (ligand_total, 1), dtype=torch.bool, device=tensor_device
            ),
            ligand_minimal_seed_or_anchor_valid=torch.zeros(
                batch_size, dtype=torch.bool, device=tensor_device
            ),
            ligand_anchor_distance_angstrom=torch.cat(anchor_parts),
            ligand_anchor_distance_valid=torch.ones(
                (ligand_total, 1), dtype=torch.bool, device=tensor_device
            ),
            target_residue_membership_mask=torch.cat(membership_parts).unsqueeze(1),
            target_residue_reactive_atom_mask=torch.cat(reactive_parts).unsqueeze(1),
            target_residue_reactive_atom_local_index=torch.tensor(
                target_reactive_local, dtype=torch.long, device=tensor_device
            ),
            target_residue_reactive_atom_flat_index=torch.tensor(
                target_reactive_flat, dtype=torch.long, device=tensor_device
            ),
            target_residue_condition_valid=torch.ones(
                batch_size, dtype=torch.bool, device=tensor_device
            ),
            pair_candidate_offsets=torch.tensor(
                pair_projection.pair_candidate_offsets,
                dtype=torch.long,
                device=tensor_device,
            ),
            pair_candidate_batch_index=torch.tensor(
                pair_projection.pair_candidate_batch_index,
                dtype=torch.long,
                device=tensor_device,
            ),
            pair_candidate_ligand_local_index=torch.tensor(
                pair_projection.pair_candidate_ligand_local_index,
                dtype=torch.long,
                device=tensor_device,
            ),
            pair_candidate_residue_local_index=torch.tensor(
                pair_projection.pair_candidate_residue_local_index,
                dtype=torch.long,
                device=tensor_device,
            ),
            pair_candidate_ligand_flat_index=torch.tensor(
                pair_projection.pair_candidate_ligand_flat_index,
                dtype=torch.long,
                device=tensor_device,
            ),
            pair_candidate_pocket_flat_index=torch.tensor(
                pair_projection.pair_candidate_pocket_flat_index,
                dtype=torch.long,
                device=tensor_device,
            ),
            pair_candidate_is_positive=torch.tensor(
                pair_projection.pair_candidate_is_positive,
                dtype=torch.bool,
                device=tensor_device,
            ),
            pair_candidate_is_negative=torch.tensor(
                pair_projection.pair_candidate_is_negative,
                dtype=torch.bool,
                device=tensor_device,
            ),
            pair_positive_candidate_index=torch.tensor(
                pair_projection.pair_positive_candidate_index,
                dtype=torch.long,
                device=tensor_device,
            ),
            pair_positive_candidate_valid=torch.tensor(
                pair_projection.pair_positive_candidate_valid,
                dtype=torch.bool,
                device=tensor_device,
            ),
            pair_negative_count=torch.tensor(
                pair_projection.pair_negative_count,
                dtype=torch.long,
                device=tensor_device,
            ),
            pair_head_candidate_loss_mask=torch.zeros(
                pair_count, dtype=torch.bool, device=tensor_device
            ),
            pair_contrastive_sample_loss_mask=torch.zeros(
                batch_size, dtype=torch.bool, device=tensor_device
            ),
            observed_complex_pair_distance_angstrom=torch.tensor(
                observed_distances, dtype=torch.float32, device=tensor_device
            ).unsqueeze(1),
            observed_complex_pair_distance_valid=torch.ones(
                (batch_size, 1), dtype=torch.bool, device=tensor_device
            ),
            pre_post_geometry_target_angstrom=torch.zeros(
                (batch_size, 2), dtype=torch.float32, device=tensor_device
            ),
            pre_post_geometry_component_valid_mask=torch.zeros(
                (batch_size, 2), dtype=torch.bool, device=tensor_device
            ),
            pre_post_geometry_component_loss_mask=torch.zeros(
                (batch_size, 2), dtype=torch.bool, device=tensor_device
            ),
        )
        preview = POAExact16RealStructureTensorPreviewV1(
            sample_identities=identities,
            structure_source_bindings=bindings,
            canonical_task_ids=tasks,
            training_use_dispositions=tuple(
                record.training_use_disposition for record in record_tuple
            ),
            human_training_excluded=tuple(
                record.human_training_excluded for record in record_tuple
            ),
            nongeometry_future_candidate=tuple(
                record.nongeometry_future_candidate for record in record_tuple
            ),
            ligand_node_offsets=ligand_offsets,
            pocket_node_offsets=pocket_offsets,
            ligand_reactive_atom_local_index=torch.tensor(
                ligand_reactive_local, dtype=torch.long, device=tensor_device
            ),
            ligand_reactive_atom_flat_index=torch.tensor(
                ligand_reactive_flat, dtype=torch.long, device=tensor_device
            ),
            model_input_batch=model_input_batch,
            supervision=supervision,
            summary=POAExact16RealStructureTensorPreviewSummaryV1(
                sample_count=0,
                ligand_node_count_per_sample=(),
                pocket_node_count_per_sample=(),
                total_ligand_node_count=0,
                total_pocket_node_count=0,
                pair_candidate_count=0,
                pair_positive_count=0,
                pair_negative_count=0,
                G1_include_count=0,
                G2_training_excluded_positive_count=0,
                sample_training_admitted_count=0,
                active_diffusion_loss_count=0,
                active_pair_loss_count=0,
                active_geometry_loss_count=0,
                observed_pair_distance_valid_count=0,
                PRE_geometry_target_valid_count=0,
                POST_geometry_target_valid_count=0,
                task_C_minimal_seed_authority_count=0,
            ),
        )
        object.__setattr__(preview, "summary", _summary_v1(preview))
        _validate_preview_impl_v1(
            preview,
            expected_sample_count=len(record_tuple),
            require_real_exact16=require_real_exact16,
        )
        return preview
    except POAExact16RealStructureTensorPreviewError:
        raise
    except Exception as error:
        raise POAExact16RealStructureTensorPreviewError(
            f"{ERROR_TOKEN}:ASSEMBLY_REJECTED:{type(error).__name__}:{error}"
        ) from error


def _require_tensor_v1(
    value: object,
    *,
    name: str,
    dtype: torch.dtype,
    shape: tuple[int, ...],
    device: torch.device,
) -> torch.Tensor:
    if (
        not isinstance(value, torch.Tensor)
        or value.dtype != dtype
        or tuple(value.shape) != shape
        or value.device != device
    ):
        _fail("TENSOR_SHAPE_DTYPE_OR_DEVICE_INVALID:" + name)
    return value


def _validate_preview_impl_v1(
    preview: object,
    *,
    expected_sample_count: int,
    require_real_exact16: bool,
) -> bool:
    if type(preview) is not POAExact16RealStructureTensorPreviewV1:
        _fail("PREVIEW_TYPE_INVALID")
    batch_size = len(preview.sample_identities)
    if (
        batch_size != expected_sample_count
        or batch_size <= 0
        or len(set(preview.sample_identities)) != batch_size
        or len(preview.canonical_task_ids) != batch_size
        or len(preview.training_use_dispositions) != batch_size
        or len(preview.human_training_excluded) != batch_size
        or len(preview.nongeometry_future_candidate) != batch_size
    ):
        _fail("PREVIEW_SAMPLE_METADATA_INVALID")
    if require_real_exact16 and (
        batch_size != 16
        or tuple(identity.split(":")[1] for identity in preview.sample_identities)
        != ("4I3U",) * 8 + ("4I3V",) * 8
        or preview.structure_source_bindings
        != tuple(
            POARealStructureSourceBindingV1(pdb_id, byte_count, sha256)
            for pdb_id, (byte_count, sha256) in EXPECTED_REAL_STRUCTURE_BINDINGS_V1.items()
        )
    ):
        _fail("PUBLIC_REAL_EXACT16_POPULATION_OR_BINDING_INVALID")
    expected_binding_pdbs = tuple(
        dict.fromkeys(identity.split(":")[1] for identity in preview.sample_identities)
    )
    if (
        tuple(binding.pdb_id for binding in preview.structure_source_bindings)
        != expected_binding_pdbs
        or any(
            type(binding) is not POARealStructureSourceBindingV1
            or type(binding.byte_count) is not int
            or binding.byte_count <= 0
            or re.fullmatch(r"[0-9a-f]{64}", binding.sha256) is None
            for binding in preview.structure_source_bindings
        )
    ):
        _fail("STRUCTURE_SOURCE_BINDING_PROVENANCE_INVALID")
    for sample, event_id in enumerate(preview.sample_identities):
        match = _EVENT_ID.fullmatch(event_id)
        if (
            match is None
            or preview.model_input_batch.get("receptors", [None] * batch_size)[sample]
            != match.group("pdb")
            or preview.training_use_dispositions[sample]
            != (
                "EXCLUDE_FROM_TRAINING_ONLY"
                if match.group("pdb") == "4I3V"
                else "INCLUDE"
            )
            or preview.human_training_excluded[sample]
            is not (match.group("pdb") == "4I3V")
            or preview.nongeometry_future_candidate[sample]
            is not (match.group("pdb") == "4I3U")
        ):
            _fail("PREVIEW_EVENT_OR_ROUTING_INVALID")
    if (
        type(preview.model_input_batch) is not dict
        or set(preview.model_input_batch) != EXPECTED_MODEL_INPUT_FIELDS_V1
        or preview.model_input_batch.get("names") != list(preview.sample_identities)
        or type(preview.model_input_batch.get("receptors")) is not list
    ):
        _fail("MODEL_INPUT_BATCH_SCHEMA_OR_IDENTITY_INVALID")

    model = preview.model_input_batch
    lig_counts_tensor = model.get("num_lig_atoms")
    pocket_counts_tensor = model.get("num_pocket_nodes")
    if not isinstance(lig_counts_tensor, torch.Tensor):
        _fail("MODEL_INPUT_LIGAND_COUNTS_TENSOR_REQUIRED")
    device = lig_counts_tensor.device
    lig_counts = tuple(int(value) for value in lig_counts_tensor.tolist())
    if not isinstance(pocket_counts_tensor, torch.Tensor):
        _fail("MODEL_INPUT_POCKET_COUNTS_TENSOR_REQUIRED")
    pocket_counts = tuple(int(value) for value in pocket_counts_tensor.tolist())
    if (
        lig_counts != (7,) * batch_size
        or len(pocket_counts) != batch_size
        or any(count <= 0 for count in pocket_counts)
        or preview.ligand_node_offsets != _offsets_v1(lig_counts)
        or preview.pocket_node_offsets != _offsets_v1(pocket_counts)
    ):
        _fail("MODEL_INPUT_NODE_COUNTS_OR_OFFSETS_INVALID")
    ligand_total = sum(lig_counts)
    pocket_total = sum(pocket_counts)
    _require_tensor_v1(
        lig_counts_tensor,
        name="num_lig_atoms",
        dtype=torch.long,
        shape=(batch_size,),
        device=device,
    )
    _require_tensor_v1(
        pocket_counts_tensor,
        name="num_pocket_nodes",
        dtype=torch.long,
        shape=(batch_size,),
        device=device,
    )
    lig_coords = _require_tensor_v1(
        model.get("lig_coords"),
        name="lig_coords",
        dtype=torch.float32,
        shape=(ligand_total, 3),
        device=device,
    )
    pocket_coords = _require_tensor_v1(
        model.get("pocket_coords"),
        name="pocket_coords",
        dtype=torch.float32,
        shape=(pocket_total, 3),
        device=device,
    )
    lig_one_hot = _require_tensor_v1(
        model.get("lig_one_hot"),
        name="lig_one_hot",
        dtype=torch.float32,
        shape=(ligand_total, CHECKPOINT_FEATURE_WIDTH_V1),
        device=device,
    )
    pocket_one_hot = _require_tensor_v1(
        model.get("pocket_one_hot"),
        name="pocket_one_hot",
        dtype=torch.float32,
        shape=(pocket_total, CHECKPOINT_FEATURE_WIDTH_V1),
        device=device,
    )
    if (
        not bool(torch.isfinite(lig_coords).all().item())
        or not bool(torch.isfinite(pocket_coords).all().item())
        or not torch.equal(
            lig_one_hot.sum(1), torch.ones(ligand_total, device=device)
        )
        or not torch.equal(
            pocket_one_hot.sum(1), torch.ones(pocket_total, device=device)
        )
        or tuple(
            tuple(int(value) for value in row)
            for row in lig_one_hot.argmax(1).reshape(batch_size, 7).tolist()
        )
        != (EXPECTED_LIGAND_CHANNELS_V1,) * batch_size
    ):
        _fail("MODEL_INPUT_COORDINATE_OR_EXACT10_FEATURE_INVALID")
    for name, total in (
        ("lig_source_row_index", ligand_total),
        ("pocket_source_row_index", pocket_total),
        ("lig_parser_local_index", ligand_total),
        ("pocket_parser_local_index", pocket_total),
        ("lig_mask", ligand_total),
        ("pocket_mask", pocket_total),
    ):
        _require_tensor_v1(
            model.get(name),
            name=name,
            dtype=torch.long,
            shape=(total,),
            device=device,
        )
    expected_lig_mask = torch.repeat_interleave(
        torch.arange(batch_size, dtype=torch.long, device=device),
        lig_counts_tensor,
    )
    expected_pocket_mask = torch.repeat_interleave(
        torch.arange(batch_size, dtype=torch.long, device=device),
        pocket_counts_tensor,
    )
    if (
        not torch.equal(model["lig_mask"], expected_lig_mask)
        or not torch.equal(model["pocket_mask"], expected_pocket_mask)
    ):
        _fail("MODEL_INPUT_BATCH_MEMBERSHIP_INVALID")
    for sample in range(batch_size):
        lig_slice = slice(
            preview.ligand_node_offsets[sample],
            preview.ligand_node_offsets[sample + 1],
        )
        pocket_slice = slice(
            preview.pocket_node_offsets[sample],
            preview.pocket_node_offsets[sample + 1],
        )
        combined = torch.cat((lig_coords[lig_slice], pocket_coords[pocket_slice]))
        if not torch.allclose(
            combined.mean(0), torch.zeros(3, device=device), atol=1e-4, rtol=0
        ):
            _fail("PER_SAMPLE_JOINT_CENTERING_INVALID")
        if model["lig_parser_local_index"][lig_slice].tolist() != list(range(7)):
            _fail("LIGAND_PARSER_LOCAL_INDEX_INVALID")
        if model["pocket_parser_local_index"][pocket_slice].tolist() != list(
            range(pocket_counts[sample])
        ):
            _fail("POCKET_PARSER_LOCAL_INDEX_INVALID")
        if model["lig_source_row_index"][lig_slice].tolist() != sorted(
            model["lig_source_row_index"][lig_slice].tolist()
        ) or model["pocket_source_row_index"][pocket_slice].tolist() != sorted(
            model["pocket_source_row_index"][pocket_slice].tolist()
        ):
            _fail("SOURCE_ATOM_SITE_ORDER_INVALID")

    supervision = preview.supervision
    if type(supervision) is not CovapieCurrent11TrainingSupervisionTensorsV1:
        _fail("EXISTING_SUPERVISION_DATACLASS_NOT_REUSED")
    if any(
        not isinstance(getattr(supervision, field.name), torch.Tensor)
        or getattr(supervision, field.name).device != device
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    ):
        _fail("SUPERVISION_FIELD_TENSOR_OR_DEVICE_INVALID")
    _require_tensor_v1(
        supervision.sample_training_admitted,
        name="sample_training_admitted",
        dtype=torch.bool,
        shape=(batch_size,),
        device=device,
    )
    _require_tensor_v1(
        supervision.canonical_task_id,
        name="canonical_task_id",
        dtype=torch.long,
        shape=(batch_size,),
        device=device,
    )
    _require_tensor_v1(
        supervision.canonical_task_valid,
        name="canonical_task_valid",
        dtype=torch.bool,
        shape=(batch_size,),
        device=device,
    )
    if (
        bool(supervision.sample_training_admitted.any().item())
        or supervision.canonical_task_id.tolist() != list(preview.canonical_task_ids)
        or any(
            type(task) is not int or task not in range(5)
            for task in preview.canonical_task_ids
        )
        or not bool(supervision.canonical_task_valid.all().item())
    ):
        _fail("SUPERVISION_SAMPLE_ADMISSION_OR_TASK_INVALID")
    role_id = _require_tensor_v1(
        supervision.ligand_role_id,
        name="ligand_role_id",
        dtype=torch.long,
        shape=(ligand_total,),
        device=device,
    )
    role_valid = _require_tensor_v1(
        supervision.ligand_role_valid,
        name="ligand_role_valid",
        dtype=torch.bool,
        shape=(ligand_total,),
        device=device,
    )
    if (
        tuple(
            tuple(int(value) for value in row)
            for row in role_id.reshape(batch_size, 7).tolist()
        )
        != (EXPECTED_ROLE_ID_MODEL_ORDER_V1,) * batch_size
        or not bool(role_valid.all().item())
    ):
        _fail("SUPERVISION_ROLE_PROJECTION_INVALID")
    mask_fields = (
        supervision.ligand_base_generation_mask,
        supervision.ligand_base_fixed_mask,
        supervision.ligand_base_target_mask,
        supervision.ligand_base_context_mask,
        supervision.ligand_active_diffusion_loss_mask,
        supervision.ligand_minimal_seed_or_anchor_mask,
        supervision.ligand_anchor_distance_valid,
    )
    if any(
        tensor.dtype != torch.bool or tuple(tensor.shape) != (ligand_total, 1)
        for tensor in mask_fields
    ):
        _fail("SUPERVISION_LIGAND_MASK_SHAPE_INVALID")
    if (
        not torch.equal(
            supervision.ligand_base_generation_mask,
            supervision.ligand_base_target_mask,
        )
        or not torch.equal(
            supervision.ligand_base_fixed_mask,
            supervision.ligand_base_context_mask,
        )
        or not torch.equal(
            supervision.ligand_base_fixed_mask,
            ~supervision.ligand_base_generation_mask,
        )
        or bool(supervision.ligand_active_diffusion_loss_mask.any().item())
        or bool(supervision.ligand_minimal_seed_or_anchor_mask.any().item())
        or bool(supervision.ligand_minimal_seed_or_anchor_valid.any().item())
        or not bool(supervision.ligand_anchor_distance_valid.all().item())
    ):
        _fail("LABEL_AVAILABLE_LOSS_OR_MINIMAL_SEED_BOUNDARY_INVALID")
    _require_tensor_v1(
        supervision.ligand_minimal_seed_or_anchor_valid,
        name="ligand_minimal_seed_or_anchor_valid",
        dtype=torch.bool,
        shape=(batch_size,),
        device=device,
    )
    for sample, task_id in enumerate(preview.canonical_task_ids):
        lig_slice = slice(sample * 7, sample * 7 + 7)
        generated = supervision.ligand_base_generation_mask[lig_slice, 0]
        generated_roles = set(CANONICAL_TASKS_V1[task_id][3])
        expected = torch.tensor(
            tuple(role in generated_roles for role in EXPECTED_ROLE_ID_MODEL_ORDER_V1),
            dtype=torch.bool,
            device=device,
        )
        if (
            not torch.equal(generated, expected)
            or (int(generated.sum().item()), int((~generated).sum().item()))
            != EXPECTED_MASK_COUNTS_V1[task_id]
        ):
            _fail("EXACT5_ROLE_MASK_INVALID")

    target_membership = _require_tensor_v1(
        supervision.target_residue_membership_mask,
        name="target_residue_membership_mask",
        dtype=torch.bool,
        shape=(pocket_total, 1),
        device=device,
    )[:, 0]
    target_reactive = _require_tensor_v1(
        supervision.target_residue_reactive_atom_mask,
        name="target_residue_reactive_atom_mask",
        dtype=torch.bool,
        shape=(pocket_total, 1),
        device=device,
    )[:, 0]
    target_local = _require_tensor_v1(
        supervision.target_residue_reactive_atom_local_index,
        name="target_residue_reactive_atom_local_index",
        dtype=torch.long,
        shape=(batch_size,),
        device=device,
    )
    target_flat = _require_tensor_v1(
        supervision.target_residue_reactive_atom_flat_index,
        name="target_residue_reactive_atom_flat_index",
        dtype=torch.long,
        shape=(batch_size,),
        device=device,
    )
    _require_tensor_v1(
        supervision.target_residue_condition_valid,
        name="target_residue_condition_valid",
        dtype=torch.bool,
        shape=(batch_size,),
        device=device,
    )
    ligand_reactive_local = _require_tensor_v1(
        preview.ligand_reactive_atom_local_index,
        name="ligand_reactive_atom_local_index",
        dtype=torch.long,
        shape=(batch_size,),
        device=device,
    )
    ligand_reactive_flat = _require_tensor_v1(
        preview.ligand_reactive_atom_flat_index,
        name="ligand_reactive_atom_flat_index",
        dtype=torch.long,
        shape=(batch_size,),
        device=device,
    )
    if (
        ligand_reactive_local.tolist() != [1] * batch_size
        or ligand_reactive_flat.tolist()
        != [preview.ligand_node_offsets[sample] + 1 for sample in range(batch_size)]
        or not bool(supervision.target_residue_condition_valid.all().item())
    ):
        _fail("REACTIVE_LOCAL_OR_FLAT_INDEX_INVALID")
    target_member_locals: list[tuple[int, ...]] = []
    for sample in range(batch_size):
        start, end = (
            preview.pocket_node_offsets[sample],
            preview.pocket_node_offsets[sample + 1],
        )
        members = tuple(
            int(value)
            for value in torch.nonzero(
                target_membership[start:end], as_tuple=False
            ).flatten().tolist()
        )
        reactive_local = tuple(
            int(value)
            for value in torch.nonzero(
                target_reactive[start:end], as_tuple=False
            ).flatten().tolist()
        )
        if (
            len(members) != 6
            or reactive_local != (int(target_local[sample].item()),)
            or target_local[sample].item() not in members
            or target_flat[sample].item()
            != start + target_local[sample].item()
            or pocket_one_hot[target_flat[sample]].argmax().item() != 3
        ):
            _fail("TARGET_CYS_EXACT6_OR_SG_INDEX_INVALID")
        target_member_locals.append(members)

    anchor = _require_tensor_v1(
        supervision.ligand_anchor_distance_angstrom,
        name="ligand_anchor_distance_angstrom",
        dtype=torch.float32,
        shape=(ligand_total, 1),
        device=device,
    )
    observed = _require_tensor_v1(
        supervision.observed_complex_pair_distance_angstrom,
        name="observed_complex_pair_distance_angstrom",
        dtype=torch.float32,
        shape=(batch_size, 1),
        device=device,
    )
    observed_valid = _require_tensor_v1(
        supervision.observed_complex_pair_distance_valid,
        name="observed_complex_pair_distance_valid",
        dtype=torch.bool,
        shape=(batch_size, 1),
        device=device,
    )
    for sample in range(batch_size):
        lig_start, lig_end = (
            preview.ligand_node_offsets[sample],
            preview.ligand_node_offsets[sample + 1],
        )
        expected_anchor = torch.linalg.vector_norm(
            lig_coords[lig_start:lig_end] - pocket_coords[target_flat[sample]],
            dim=1,
            keepdim=True,
        )
        if (
            not torch.allclose(anchor[lig_start:lig_end], expected_anchor, atol=1e-6)
            or not torch.allclose(observed[sample, 0], expected_anchor[1, 0], atol=1e-6)
        ):
            _fail("ANCHOR_OR_OBSERVED_PAIR_DISTANCE_INVALID")
    if (
        not bool(torch.isfinite(anchor).all().item())
        or not bool(torch.isfinite(observed).all().item())
        or not bool(observed_valid.all().item())
    ):
        _fail("OBSERVED_PAIR_DISTANCE_VALIDITY_INVALID")

    pair_specs = tuple(
        pair_owner.PairCandidateSampleSpec(
            batch_sample_index_0based=sample,
            retained_ligand_count=7,
            retained_pocket_count=pocket_counts[sample],
            target_residue_pocket_local_indices=target_member_locals[sample],
            positive_ligand_local_index=1,
            positive_pocket_local_index=int(target_local[sample].item()),
        )
        for sample in range(batch_size)
    )
    expected_pair = pair_owner.build_pair_candidate_records_v1(
        pair_specs, preview.ligand_node_offsets, preview.pocket_node_offsets
    )
    pair_fields = (
        ("pair_candidate_offsets", expected_pair.pair_candidate_offsets, torch.long),
        ("pair_candidate_batch_index", expected_pair.pair_candidate_batch_index, torch.long),
        (
            "pair_candidate_ligand_local_index",
            expected_pair.pair_candidate_ligand_local_index,
            torch.long,
        ),
        (
            "pair_candidate_residue_local_index",
            expected_pair.pair_candidate_residue_local_index,
            torch.long,
        ),
        (
            "pair_candidate_ligand_flat_index",
            expected_pair.pair_candidate_ligand_flat_index,
            torch.long,
        ),
        (
            "pair_candidate_pocket_flat_index",
            expected_pair.pair_candidate_pocket_flat_index,
            torch.long,
        ),
        ("pair_candidate_is_positive", expected_pair.pair_candidate_is_positive, torch.bool),
        ("pair_candidate_is_negative", expected_pair.pair_candidate_is_negative, torch.bool),
        (
            "pair_positive_candidate_index",
            expected_pair.pair_positive_candidate_index,
            torch.long,
        ),
        (
            "pair_positive_candidate_valid",
            expected_pair.pair_positive_candidate_valid,
            torch.bool,
        ),
        ("pair_negative_count", expected_pair.pair_negative_count, torch.long),
    )
    for name, expected, dtype in pair_fields:
        tensor = getattr(supervision, name)
        if tensor.dtype != dtype or tensor.tolist() != list(expected):
            _fail("PAIR_CANDIDATE_PROJECTION_INVALID:" + name)
    pair_count = len(expected_pair.records)
    _require_tensor_v1(
        supervision.pair_head_candidate_loss_mask,
        name="pair_head_candidate_loss_mask",
        dtype=torch.bool,
        shape=(pair_count,),
        device=device,
    )
    _require_tensor_v1(
        supervision.pair_contrastive_sample_loss_mask,
        name="pair_contrastive_sample_loss_mask",
        dtype=torch.bool,
        shape=(batch_size,),
        device=device,
    )
    if (
        pair_count != 42 * batch_size
        or bool(supervision.pair_head_candidate_loss_mask.any().item())
        or bool(supervision.pair_contrastive_sample_loss_mask.any().item())
    ):
        _fail("PAIR_CANDIDATE_COUNT_OR_LOSS_BOUNDARY_INVALID")

    geometry = _require_tensor_v1(
        supervision.pre_post_geometry_target_angstrom,
        name="pre_post_geometry_target_angstrom",
        dtype=torch.float32,
        shape=(batch_size, 2),
        device=device,
    )
    geometry_valid = _require_tensor_v1(
        supervision.pre_post_geometry_component_valid_mask,
        name="pre_post_geometry_component_valid_mask",
        dtype=torch.bool,
        shape=(batch_size, 2),
        device=device,
    )
    geometry_loss = _require_tensor_v1(
        supervision.pre_post_geometry_component_loss_mask,
        name="pre_post_geometry_component_loss_mask",
        dtype=torch.bool,
        shape=(batch_size, 2),
        device=device,
    )
    if (
        not bool(torch.isfinite(geometry).all().item())
        or bool(geometry.any().item())
        or bool(geometry_valid.any().item())
        or bool(geometry_loss.any().item())
    ):
        _fail("PRE_POST_GEOMETRY_AUTHORITY_BOUNDARY_INVALID")
    if preview.summary != _summary_v1(preview):
        _fail("PREVIEW_SUMMARY_NOT_DERIVED")
    if (
        preview.structural_coordinates_centered is not True
        or preview.feature_semantics_audit_already_completed is not True
        or preview.feature_semantics_redesigned is not False
        or preview.model_architecture_change_required is not False
        or preview.model_forward_executed is not False
        or preview.loss_executed is not False
        or preview.backward_executed is not False
        or preview.optimizer_created is not False
        or preview.optimizer_step_executed is not False
        or preview.trainer_fit_executed is not False
        or preview.training_admission_created is not False
        or preview.training_dataset_changed is not False
        or preview.training_performed is not False
        or preview.finetune_performed is not False
        or preview.ready_for_training is not False
        or feature_owner.CHECKPOINT_CHANNEL_ORDER
        != "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"
        or len(feature_owner.CHECKPOINT_TOKEN_TO_INDEX) != CHECKPOINT_FEATURE_WIDTH_V1
    ):
        _fail("EXECUTION_TRAINING_OR_FEATURE_SEMANTICS_BOUNDARY_INVALID")
    return True


def assemble_covapie_poa_exact16_real_structure_tensor_preview_v1(
    *,
    structure_payloads_by_pdb: Mapping[str, bytes],
    effective_supervision: metadata_owner.POASampleLevelEffectiveSupervisionResultV1,
    canonical_task_ids_by_event: Mapping[str, int],
    device: str = "cpu",
) -> POAExact16RealStructureTensorPreviewV1:
    """Assemble exact real POA bytes into an inactive model-bound preview."""

    try:
        metadata_owner.validate_covapie_poa_sample_level_effective_supervision_v1(
            effective_supervision
        )
        if set(structure_payloads_by_pdb) != set(EXPECTED_REAL_PDB_IDS_V1):
            _fail("STRUCTURE_PAYLOAD_MAPPING_KEYS_INVALID")
        return _assemble_core_v1(
            structure_payloads_by_pdb=structure_payloads_by_pdb,
            records=effective_supervision.records,
            canonical_task_ids_by_event=canonical_task_ids_by_event,
            device=device,
            expected_structure_bindings=EXPECTED_REAL_STRUCTURE_BINDINGS_V1,
            require_real_exact16=True,
        )
    except POAExact16RealStructureTensorPreviewError:
        raise
    except Exception as error:
        raise POAExact16RealStructureTensorPreviewError(
            f"{ERROR_TOKEN}:PUBLIC_ASSEMBLY_REJECTED:{type(error).__name__}:{error}"
        ) from error


def validate_covapie_poa_exact16_real_structure_tensor_preview_v1(
    preview: object,
) -> bool:
    """Fail closed unless ``preview`` is the complete inactive real exact16."""

    try:
        return _validate_preview_impl_v1(
            preview, expected_sample_count=16, require_real_exact16=True
        )
    except POAExact16RealStructureTensorPreviewError:
        raise
    except Exception as error:
        raise POAExact16RealStructureTensorPreviewError(
            f"{ERROR_TOKEN}:PUBLIC_VALIDATION_REJECTED:{type(error).__name__}:{error}"
        ) from error
