"""Tensorize published FFQ direct-profile atom roles and canonical masks.

The caller supplies one published FFQ effective-supervision record and ligand
atom identity rows.  This module performs no filesystem access, training
admission, geometry tensorization, model integration, or parameter update.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NoReturn

import torch

from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as direct_runtime,
)
from covalent_ext import (
    covapie_ffq_project_level_authority_ingestion_and_effective_supervision_successor_v1
    as ffq_successor,
)
from covalent_ext import (
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as feature_policy,
)


__all__ = (
    "FFQDirectProfileRoleMaskTensorizerError",
    "FFQDirectProfileRoleMaskTensorsV1",
    "tensorize_covapie_ffq_direct_profile_role_masks_v1",
)


_ERROR = "COVAPIE_FFQ_DIRECT_PROFILE_ROLE_MASK_TENSORIZER_V1_ERROR"
_ROLE_PROFILE = direct_runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1

# These are aliases of the published successor semantics, not a new authority.
_FFQ_EVENT_IDS = ffq_successor._CANONICAL_EVENT_IDS
_FFQ_SCAFFOLD_ATOM_IDS = ffq_successor._SCAFFOLD_ATOM_IDS
_FFQ_LINKER_ATOM_IDS = ffq_successor._LINKER_ATOM_IDS
_FFQ_WARHEAD_ATOM_IDS = ffq_successor._WARHEAD_ATOM_IDS
_FFQ_HEAVY_ATOM_IDS = frozenset(
    _FFQ_SCAFFOLD_ATOM_IDS
    + _FFQ_LINKER_ATOM_IDS
    + _FFQ_WARHEAD_ATOM_IDS
)
_ROLE_ID_BY_NAME = dict(
    zip(
        direct_runtime.CANONICAL_ROLE_NAMES_V1,
        direct_runtime.CANONICAL_ROLE_IDS_V1,
    )
)


class FFQDirectProfileRoleMaskTensorizerError(ValueError):
    """Raised unless exact published FFQ role-mask semantics are proven."""


@dataclass(frozen=True)
class FFQDirectProfileRoleMaskTensorsV1:
    canonical_event_id: str
    canonical_task_id: int

    ligand_role_id: torch.Tensor
    ligand_role_valid: torch.Tensor

    ligand_base_generation_mask: torch.Tensor
    ligand_base_fixed_mask: torch.Tensor
    ligand_base_target_mask: torch.Tensor
    ligand_base_context_mask: torch.Tensor

    scaffold_parser_local_indices: tuple[int, ...]
    linker_parser_local_indices: tuple[int, ...]
    warhead_parser_local_indices: tuple[int, ...]

    task_applicable: bool
    task_C_role_mask_supported: bool
    task_C_minimal_seed_supervision_available: bool
    full_task_C_training_supervision_ready: bool
    ffq_direct_profile_unknown_atom_policy_enforced: bool


def _fail(reason: str) -> NoReturn:
    raise FFQDirectProfileRoleMaskTensorizerError(f"{_ERROR}:{reason}")


def _validate_effective_supervision_record(record: object) -> dict[str, object]:
    if type(record) is not dict:
        _fail("EFFECTIVE_SUPERVISION_RECORD_EXACT_DICT_REQUIRED")

    if record.get("effective_supervision_schema_version") != (
        ffq_successor.EFFECTIVE_SUPERVISION_RECORD_SCHEMA_VERSION
    ):
        _fail("EFFECTIVE_SUPERVISION_SCHEMA_VERSION_INVALID")
    event_id = record.get("canonical_event_id")
    if type(event_id) is not str or event_id not in _FFQ_EVENT_IDS:
        _fail("CANONICAL_EVENT_ID_NOT_PUBLISHED_FFQ_EVENT")
    if record.get("ligand_component_id") != "FFQ":
        _fail("LIGAND_COMPONENT_NOT_FFQ")
    if record.get("role_profile") != _ROLE_PROFILE:
        _fail("ROLE_PROFILE_INVALID")
    if record.get("reviewed_scaffold_atom_ids") != list(
        _FFQ_SCAFFOLD_ATOM_IDS
    ):
        _fail("SCAFFOLD_ATOM_INVENTORY_DRIFT")
    if record.get("reviewed_linker_atom_ids") != list(_FFQ_LINKER_ATOM_IDS):
        _fail("LINKER_ATOM_INVENTORY_DRIFT")
    if record.get("reviewed_warhead_atom_ids") != list(_FFQ_WARHEAD_ATOM_IDS):
        _fail("WARHEAD_ATOM_INVENTORY_DRIFT")
    if record.get("project_level_chemistry_authority_linkage_complete") is not True:
        _fail("PROJECT_CHEMISTRY_AUTHORITY_LINKAGE_INCOMPLETE")
    if record.get("reaction_family_authority_id") != (
        ffq_successor.REACTION_FAMILY_AUTHORITY_ID
    ):
        _fail("REACTION_FAMILY_AUTHORITY_ID_DRIFT")
    if record.get("warhead_rule_authority_id") != (
        ffq_successor.WARHEAD_RULE_AUTHORITY_ID
    ):
        _fail("WARHEAD_RULE_AUTHORITY_ID_DRIFT")

    pdb_id = record.get("pdb_id")
    expected_pdb_id = "3VCY" if ":3VCY:" in event_id else "4R7U"
    if pdb_id != expected_pdb_id:
        _fail("EVENT_PDB_BINDING_INVALID")
    expected_record = ffq_successor._expected_record(
        {
            "canonical_event_id": event_id,
            "pdb_id": expected_pdb_id,
            "completed_lane": (
                "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"
                if expected_pdb_id == "3VCY"
                else "COMPLETED_HUMAN_CHEMISTRY_POSITIVE_TRAINING_EXCLUDED"
            ),
        }
    )
    if record != expected_record:
        _fail("EFFECTIVE_SUPERVISION_RECORD_NOT_EXACT_PUBLISHED_SUCCESSOR")
    return record


def _parser_local_role_indices(
    ligand_atom_rows: object,
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    if type(ligand_atom_rows) not in (list, tuple) or not ligand_atom_rows:
        _fail("LIGAND_ATOM_ROWS_NONEMPTY_LIST_OR_TUPLE_REQUIRED")

    atom_ids: list[str] = []
    parser_local_indices: list[int] = []
    for row in ligand_atom_rows:
        if type(row) is not dict:
            _fail("LIGAND_ATOM_ROW_EXACT_DICT_REQUIRED")
        atom_id = row.get("atom_id")
        parser_local_index = row.get("parser_local_index")
        if (
            type(atom_id) is not str
            or not atom_id
            or atom_id.strip() != atom_id
        ):
            _fail("ATOM_ID_NONEMPTY_EXACT_STRING_REQUIRED")
        if type(parser_local_index) is not int or parser_local_index < 0:
            _fail("PARSER_LOCAL_INDEX_EXACT_NONNEGATIVE_INT_REQUIRED")
        atom_ids.append(atom_id)
        parser_local_indices.append(parser_local_index)

    if len(set(atom_ids)) != len(atom_ids):
        _fail("DUPLICATE_ATOM_ID")
    if len(set(parser_local_indices)) != len(parser_local_indices):
        _fail("DUPLICATE_PARSER_LOCAL_INDEX")
    if set(parser_local_indices) != set(range(len(parser_local_indices))):
        _fail("PARSER_LOCAL_INDICES_NOT_CONTIGUOUS_ZERO_BASED")

    # Row position is deliberately not used as parser-local identity.
    ordered_rows = sorted(
        ligand_atom_rows, key=lambda row: row["parser_local_index"]
    )
    projection = feature_policy.project_type_symbols_to_checkpoint_heavy_v1(
        tuple(row.get("type_symbol") for row in ordered_rows)
    )
    if projection.sample_rejected or projection.outcome != "passed":
        detail = ";".join(projection.reasons) or "UNSPECIFIED"
        _fail("UNKNOWN_ATOM_POLICY_REJECTED_SAMPLE:" + detail)
    if not (
        len(projection.keep_mask)
        == len(projection.source_to_projected_index)
        == len(projection.checkpoint_channel_indices)
        == len(ordered_rows)
    ):
        _fail("UNKNOWN_ATOM_POLICY_PROJECTION_SHAPE_INVALID")

    retained_atom_id_to_index: dict[str, int] = {}
    for source_index, (row, keep) in enumerate(
        zip(ordered_rows, projection.keep_mask)
    ):
        projected_index = projection.source_to_projected_index[source_index]
        channel_index = projection.checkpoint_channel_indices[source_index]
        if keep:
            if (
                type(projected_index) is not int
                or type(channel_index) is not int
                or channel_index not in range(10)
            ):
                _fail("CHECKPOINT_HEAVY_PROJECTION_INVALID")
            retained_atom_id_to_index[row["atom_id"]] = projected_index
        elif (
            projection.symbol_classes[source_index] != "explicit_hydrogen"
            or projected_index is not None
            or channel_index is not None
        ):
            _fail("NON_HYDROGEN_EXCLUSION_OR_FALLBACK_DETECTED")

    retained_ids = frozenset(retained_atom_id_to_index)
    if len(retained_atom_id_to_index) != 8 or retained_ids != _FFQ_HEAVY_ATOM_IDS:
        missing = sorted(_FFQ_HEAVY_ATOM_IDS - retained_ids)
        extra = sorted(retained_ids - _FFQ_HEAVY_ATOM_IDS)
        _fail(
            "FFQ_EXACT8_HEAVY_ATOM_IDENTITY_INVALID:"
            f"missing={missing!r}:extra={extra!r}"
        )
    if set(retained_atom_id_to_index.values()) != set(range(8)):
        _fail("RETAINED_HEAVY_PARSER_LOCAL_INDICES_INVALID")

    scaffold = tuple(
        retained_atom_id_to_index[atom_id]
        for atom_id in _FFQ_SCAFFOLD_ATOM_IDS
    )
    linker = tuple(
        retained_atom_id_to_index[atom_id]
        for atom_id in _FFQ_LINKER_ATOM_IDS
    )
    warhead = tuple(
        retained_atom_id_to_index[atom_id]
        for atom_id in _FFQ_WARHEAD_ATOM_IDS
    )
    role_ids = [-1] * 8
    for index in scaffold:
        role_ids[index] = _ROLE_ID_BY_NAME["scaffold"]
    for index in linker:
        role_ids[index] = _ROLE_ID_BY_NAME["linker"]
    for index in warhead:
        role_ids[index] = _ROLE_ID_BY_NAME["warhead"]
    if set(role_ids) != {0, 2}:
        _fail("FFQ_DIRECT_PROFILE_ROLE_IDS_INVALID")
    return scaffold, linker, warhead, tuple(role_ids)


def tensorize_covapie_ffq_direct_profile_role_masks_v1(
    *,
    effective_supervision_record: object,
    ligand_atom_rows: object,
    canonical_task_id: object,
    device: object = "cpu",
) -> FFQDirectProfileRoleMaskTensorsV1:
    """Map exact FFQ atom identities to parser-local role and mask tensors."""

    record = _validate_effective_supervision_record(effective_supervision_record)
    if type(canonical_task_id) is not int:
        _fail("CANONICAL_TASK_ID_EXACT_INT_REQUIRED")
    valid_task_ids = direct_runtime.valid_canonical_task_ids_for_role_profile_v1(
        _ROLE_PROFILE
    )
    if canonical_task_id in (1, 2):
        _fail("TASK_NOT_APPLICABLE")
    if canonical_task_id not in valid_task_ids:
        _fail("CANONICAL_TASK_ID_INVALID")

    scaffold, linker, warhead, role_ids = _parser_local_role_indices(
        ligand_atom_rows
    )
    try:
        mask_result = direct_runtime.build_mask_for_role_profile_v1(
            role_profile=_ROLE_PROFILE,
            canonical_task_id=canonical_task_id,
            scaffold_atoms=scaffold,
            linker_atoms=linker,
            warhead_atoms=warhead,
            num_ligand_atoms=8,
        )
    except ValueError as error:
        raise FFQDirectProfileRoleMaskTensorizerError(
            f"{_ERROR}:DIRECT_PROFILE_MASK_RUNTIME_REJECTED:{error}"
        ) from error
    compatibility = direct_runtime.validate_current_lightning_structural_expectations_v1(
        role_profile=_ROLE_PROFILE,
        canonical_task_id=canonical_task_id,
        ligand_role_ids=role_ids,
        mask_result=mask_result,
    )
    if compatibility.valid is not True:
        _fail(
            "CURRENT_LIGHTNING_STRUCTURAL_EXPECTATIONS_INVALID:"
            + ";".join(compatibility.reasons)
        )

    tensor_device = torch.device(device)
    generation = torch.zeros(8, dtype=torch.bool, device=tensor_device)
    if mask_result.masked_atoms:
        generation[list(mask_result.masked_atoms)] = True
    fixed = ~generation
    expected_fixed = mask_result.lig_fixed.to(
        device=tensor_device, dtype=torch.bool
    )
    if not torch.equal(fixed, expected_fixed):
        _fail("MASK_RUNTIME_FIXED_COMPLEMENT_INVALID")

    return FFQDirectProfileRoleMaskTensorsV1(
        canonical_event_id=record["canonical_event_id"],  # type: ignore[arg-type]
        canonical_task_id=canonical_task_id,
        ligand_role_id=torch.tensor(
            role_ids, dtype=torch.long, device=tensor_device
        ),
        ligand_role_valid=torch.ones(8, dtype=torch.bool, device=tensor_device),
        ligand_base_generation_mask=generation.unsqueeze(1),
        ligand_base_fixed_mask=fixed.unsqueeze(1),
        ligand_base_target_mask=generation.clone().unsqueeze(1),
        ligand_base_context_mask=fixed.clone().unsqueeze(1),
        scaffold_parser_local_indices=scaffold,
        linker_parser_local_indices=linker,
        warhead_parser_local_indices=warhead,
        task_applicable=True,
        task_C_role_mask_supported=True,
        task_C_minimal_seed_supervision_available=False,
        full_task_C_training_supervision_ready=False,
        ffq_direct_profile_unknown_atom_policy_enforced=True,
    )
