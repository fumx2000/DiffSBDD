"""Assemble real FFQ structures into an index-aligned in-memory micro-batch.

Ligand identity and supervision sidecars reuse published CovaPIE owners.  The
model-input pocket and coordinates instead follow the bound DiffSBDD
CrossDocked full-atom checkpoint preprocessing path: standard-amino-acid
residue-level 8 A selection followed by per-sample retained ligand+pocket
centering.  This module performs no filesystem access, geometry-label
construction, model execution, training admission, or parameter update.
"""

from __future__ import annotations

import gzip
import math
import re
from dataclasses import dataclass
from typing import Any, Mapping, NoReturn, Sequence

import torch
from Bio.PDB.Polypeptide import is_aa

from covalent_ext import (
    covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1
    as pocket_owner,
)
from covalent_ext import (
    covapie_ffq_direct_profile_role_mask_tensorizer_v1 as role_owner,
)
from covalent_ext import (
    covapie_mmcif_ligand_atom_identity_extractor_v1 as ligand_owner,
)
from covalent_ext import (
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as feature_owner,
)
from covalent_ext import (
    real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun
    as atom_site_owner,
)


__all__ = (
    "FFQRealStructureMicrobatchAlignmentError",
    "FFQRealStructureMicrobatchAlignmentV1",
    "assemble_covapie_ffq_real_structure_microbatch_alignment_v1",
)


_ERROR = "COVAPIE_FFQ_REAL_STRUCTURE_MICROBATCH_ALIGNMENT_V1_ERROR"
_INPUT_FIELDS = frozenset(
    {"cif_gz_payload", "effective_supervision_record", "canonical_task_id"}
)
_EVENT_ID = re.compile(
    r"^COVAPIE_CYS_SG_EVENT_V1:"
    r"(?P<pdb>[^:]+):(?P<protein_chain>[^:]+):(?P<residue>[^:]+):"
    r"(?P<residue_locator>[^:]+):(?P<protein_atom>[^:]+):"
    r"(?P<ligand_asym>[^:]+):(?P<ligand>[^:]+):(?P<ligand_atom>[^:]+)$"
)
_RESIDUE_LOCATOR = re.compile(r"^(?P<sequence>-?[0-9]+)(?P<insertion>-|[A-Za-z0-9])$")

# The radius is shared, but the two owners have distinct responsibilities.
# ``pocket_owner.build_canonical_pocket_v1`` remains the CovaPIE atom-level
# structural-evidence owner.  Model inputs here are governed by the checkpoint
# preprocessing owner ``process_crossdock.process_ligand_and_pocket``.
POCKET_RADIUS_ANGSTROM_V1 = pocket_owner.POCKET_RADIUS_ANGSTROM
STRUCTURAL_EVIDENCE_POCKET_OWNER_V1 = (
    "covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1."
    "build_canonical_pocket_v1"
)
CHECKPOINT_MODEL_INPUT_POCKET_OWNER_V1 = (
    "process_crossdock.process_ligand_and_pocket"
)
ALTLOC_COMPATIBILITY_NOTE_V1 = (
    "Bio.PDB may choose one disordered-atom child by occupancy; V1 accepts blank/A "
    "protein rows but fails closed when a checkpoint-relevant standard-AA residue "
    "has any non-A alternate row, rather than claiming full altloc equivalence"
)
POCKET_SELECTION_SEMANTICS_V1 = (
    "checkpoint_CrossDocked_8A_strict_less_than_standard_amino_acid_"
    "residue_level_full_atom_model1_blank_or_A_altloc_source_atom_site_order"
)


class FFQRealStructureMicrobatchAlignmentError(ValueError):
    """Raised unless every structural and batch-index invariant is proven."""


@dataclass(frozen=True)
class FFQRealStructureMicrobatchAlignmentV1:
    model_input_batch: dict[str, torch.Tensor]
    sample_identities: tuple[str, ...]

    ligand_node_offsets: tuple[int, ...]
    pocket_node_offsets: tuple[int, ...]

    ligand_role_id: torch.Tensor
    ligand_role_valid: torch.Tensor
    ligand_generation_mask: torch.Tensor
    ligand_fixed_mask: torch.Tensor
    ligand_target_mask: torch.Tensor
    ligand_context_mask: torch.Tensor

    target_residue_membership_mask: torch.Tensor
    target_residue_reactive_atom_mask: torch.Tensor
    target_reactive_local_indices: torch.Tensor
    target_reactive_flat_indices: torch.Tensor
    ligand_reactive_local_indices: torch.Tensor
    ligand_reactive_flat_indices: torch.Tensor

    positive_pair_batch_indices: torch.Tensor
    positive_pair_ligand_local_indices: torch.Tensor
    positive_pair_pocket_local_indices: torch.Tensor
    positive_pair_ligand_flat_indices: torch.Tensor
    positive_pair_pocket_flat_indices: torch.Tensor

    canonical_task_ids: torch.Tensor
    sample_training_admitted: torch.Tensor
    human_training_exclusion_preserved: torch.Tensor
    task_C_role_mask_supported: torch.Tensor
    task_C_minimal_seed_supervision_available: torch.Tensor
    full_task_C_training_supervision_ready: torch.Tensor
    geometry_target_available: torch.Tensor
    warhead_type_target_available: torch.Tensor

    # Only model_input_batch coordinates are checkpoint-preprocessing centered;
    # source atom identities and row indices still refer to the raw mmCIF frame.
    structural_coordinates_centered: bool = True
    model_forward: bool = False
    training_performed: bool = False


def _fail(reason: str) -> NoReturn:
    raise FFQRealStructureMicrobatchAlignmentError(f"{_ERROR}:{reason}")


def _exact_mapping(value: object, *, reason: str) -> Mapping[str, object]:
    if type(value) is not dict:
        _fail(reason)
    return value  # type: ignore[return-value]


def _atom_value(row: Mapping[str, Any], field: str) -> str:
    value = row.get("_atom_site." + field, "")
    text = str(value or "")
    return "" if text in {".", "?", "NONE"} else text


def _preferred_atom_name(row: Mapping[str, Any]) -> str:
    return _atom_value(row, "auth_atom_id") or _atom_value(row, "label_atom_id")


def _preferred_component(row: Mapping[str, Any]) -> str:
    return _atom_value(row, "auth_comp_id") or _atom_value(row, "label_comp_id")


def _event_identity(record: Mapping[str, object]) -> dict[str, str]:
    event_id = record.get("canonical_event_id")
    if type(event_id) is not str:
        _fail("CANONICAL_EVENT_ID_EXACT_STRING_REQUIRED")
    match = _EVENT_ID.fullmatch(event_id)
    if match is None:
        _fail("CANONICAL_EVENT_ID_GRAMMAR_INVALID")
    identity = match.groupdict()
    locator = _RESIDUE_LOCATOR.fullmatch(identity["residue_locator"])
    if locator is None:
        _fail("TARGET_RESIDUE_LOCATOR_GRAMMAR_INVALID")
    identity["sequence"] = locator.group("sequence")
    identity["insertion"] = (
        "NONE" if locator.group("insertion") == "-" else locator.group("insertion")
    )
    if (
        record.get("pdb_id") != identity["pdb"]
        or record.get("target_residue_name") != identity["residue"]
        or record.get("target_residue_atom_id") != identity["protein_atom"]
        or record.get("ligand_component_id") != identity["ligand"]
        or record.get("ligand_reactive_atom_id") != identity["ligand_atom"]
    ):
        _fail("EVENT_ID_EFFECTIVE_SUPERVISION_BINDING_INVALID")
    return identity


def _single_mmcif_scalar(value: object, *, reason: str) -> str:
    if type(value) is list:
        if len(value) != 1:
            _fail(reason)
        value = value[0]
    if type(value) is not str or not value or value in {".", "?"}:
        _fail(reason)
    return value


def _parse_and_crosscheck_atom_site(
    payload: bytes, *, expected_pdb_id: str
) -> list[dict[str, str]]:
    # Reuse both published parsers and prove their row indices agree before any
    # source-row identity is converted to a model-local index.
    parsed = ligand_owner._parse_cif_gz_payload(payload)
    columns = ligand_owner._validated_atom_site_columns(parsed)
    entry_id = _single_mmcif_scalar(
        parsed.get("_entry.id"), reason="MMCIF_ENTRY_ID_EXACTLY_ONE_REQUIRED"
    )
    if entry_id.upper() != expected_pdb_id.upper():
        _fail("MMCIF_ENTRY_EVENT_PDB_MISMATCH")
    try:
        text = gzip.decompress(payload).decode("utf-8")
    except (EOFError, OSError, UnicodeDecodeError) as error:
        raise FFQRealStructureMicrobatchAlignmentError(
            f"{_ERROR}:MMCIF_TEXT_DECODE_FAILED"
        ) from error
    atom_rows = atom_site_owner.extract_atom_site_loop_rows_v0(text)
    if not atom_rows or len(atom_rows) != len(columns["_atom_site.id"]):
        _fail("PUBLISHED_ATOM_SITE_PARSER_ROW_COUNT_MISMATCH")
    if any(
        _atom_value(row, "id") != columns["_atom_site.id"][index]
        for index, row in enumerate(atom_rows)
    ):
        _fail("PUBLISHED_ATOM_SITE_SOURCE_ORDER_MISMATCH")
    return atom_rows


def _crosscheck_ligand_rows(
    ligand_rows: Sequence[Mapping[str, object]],
    atom_rows: Sequence[Mapping[str, Any]],
) -> list[tuple[int, Mapping[str, Any]]]:
    selected: list[tuple[int, Mapping[str, Any]]] = []
    for expected_parser_index, identity in enumerate(ligand_rows):
        source_index = identity.get("source_atom_site_row_index_0based")
        if (
            type(source_index) is not int
            or not 0 <= source_index < len(atom_rows)
            or identity.get("parser_local_index") != expected_parser_index
        ):
            _fail("LIGAND_SOURCE_OR_PARSER_INDEX_INVALID")
        source_row = atom_rows[source_index]
        if (
            _atom_value(source_row, "id") != identity.get("atom_site_id")
            or _atom_value(source_row, "label_atom_id") != identity.get("atom_id")
            or _atom_value(source_row, "type_symbol") != identity.get("type_symbol")
            or _atom_value(source_row, "label_comp_id")
            != identity.get("label_comp_id")
            or _atom_value(source_row, "label_asym_id") != identity.get("label_asym_id")
            or (_atom_value(source_row, "pdbx_PDB_model_num") or "1")
            != identity.get("model_num")
        ):
            _fail("LIGAND_IDENTITY_SOURCE_ROW_BINDING_INVALID")
        selected.append((source_index, source_row))
    return selected


def _projection(
    indexed_rows: Sequence[tuple[int, Mapping[str, Any]]], *, domain: str
) -> tuple[
    list[tuple[int, Mapping[str, Any]]], tuple[int, ...], tuple[int | None, ...]
]:
    symbols = tuple(
        pocket_owner._canonical_type_symbol(_atom_value(row, "type_symbol"))
        for _, row in indexed_rows
    )
    projection = feature_owner.project_type_symbols_to_checkpoint_heavy_v1(symbols)
    if projection.sample_rejected or projection.outcome != "passed":
        detail = ";".join(projection.reasons) or "UNSPECIFIED"
        _fail(f"{domain.upper()}_EXACT10_SAMPLE_REJECTED:{detail}")
    retained = [
        indexed_row
        for indexed_row, keep in zip(indexed_rows, projection.keep_mask)
        if keep
    ]
    channels = tuple(
        channel
        for channel in projection.checkpoint_channel_indices
        if type(channel) is int
    )
    if (
        not retained
        or len(retained) != len(channels)
        or any(channel not in range(10) for channel in channels)
    ):
        _fail(f"{domain.upper()}_EXACT10_RETAINED_MAPPING_INVALID")
    return retained, channels, projection.source_to_projected_index


def _raw_coordinates(
    row: Mapping[str, Any], *, reason: str
) -> tuple[float, float, float]:
    try:
        coordinates = tuple(
            float(_atom_value(row, axis))
            for axis in ("Cartn_x", "Cartn_y", "Cartn_z")
        )
    except (TypeError, ValueError, OverflowError) as error:
        raise FFQRealStructureMicrobatchAlignmentError(
            f"{_ERROR}:{reason}"
        ) from error
    if len(coordinates) != 3 or any(not math.isfinite(value) for value in coordinates):
        _fail(reason)
    return coordinates  # type: ignore[return-value]


def _checkpoint_standard_aa_residue_identity_v1(
    row: Mapping[str, Any],
) -> tuple[str, str, str, str, str] | None:
    """Map one model-1 standard-AA row without discarding alternate children."""

    model = _atom_value(row, "pdbx_PDB_model_num") or "1"
    if model != "1":
        return None
    component = _preferred_component(row)
    if not component or not is_aa(component, standard=True):
        return None
    chain = _atom_value(row, "auth_asym_id") or _atom_value(row, "label_asym_id")
    sequence = _atom_value(row, "auth_seq_id") or _atom_value(row, "label_seq_id")
    insertion = _atom_value(row, "pdbx_PDB_ins_code") or "NONE"
    if not chain or not sequence:
        _fail("CHECKPOINT_STANDARD_AA_RESIDUE_IDENTITY_INVALID")
    return model, chain, sequence, insertion, component


def _checkpoint_residue_key_v1(
    row: Mapping[str, Any],
) -> tuple[str, str, str, str, str] | None:
    """Map one currently supported blank/A atom to checkpoint residue identity."""

    key = _checkpoint_standard_aa_residue_identity_v1(row)
    if key is None or _atom_value(row, "label_alt_id") not in {"", "A"}:
        return None
    return key


def _validate_checkpoint_pocket_altloc_compatibility_v1(
    indexed_atom_rows: Sequence[tuple[int, Mapping[str, Any]]],
    ligand_heavy_rows: Sequence[tuple[int, Mapping[str, Any]]],
) -> None:
    """Reject only non-A protein altlocs that can affect checkpoint pocket rows."""

    if not ligand_heavy_rows:
        _fail("EMPTY_LIGAND_POCKET_SEED")
    ligand_coordinates = tuple(
        _raw_coordinates(row, reason="LIGAND_COORDINATES_INVALID")
        for _, row in ligand_heavy_rows
    )
    residue_rows: dict[
        tuple[str, str, str, str, str],
        list[tuple[Mapping[str, Any], tuple[float, float, float]]],
    ] = {}
    for _, row in indexed_atom_rows:
        key = _checkpoint_standard_aa_residue_identity_v1(row)
        if key is None:
            continue
        residue_rows.setdefault(key, []).append(
            (
                row,
                _raw_coordinates(
                    row,
                    reason="CHECKPOINT_POCKET_PROTEIN_COORDINATES_INVALID",
                ),
            )
        )

    for rows in residue_rows.values():
        has_unsupported_alternate = any(
            _atom_value(row, "label_alt_id") not in {"", "A"}
            for row, _ in rows
        )
        if not has_unsupported_alternate:
            continue
        checkpoint_relevant = min(
            math.dist(protein_xyz, ligand_xyz)
            for _, protein_xyz in rows
            for ligand_xyz in ligand_coordinates
        ) < POCKET_RADIUS_ANGSTROM_V1
        if checkpoint_relevant:
            _fail("CHECKPOINT_POCKET_ALTLOC_SEMANTICS_AMBIGUOUS_V1")


def _build_checkpoint_model_input_pocket_v1(
    indexed_atom_rows: Sequence[tuple[int, Mapping[str, Any]]],
    ligand_heavy_rows: Sequence[tuple[int, Mapping[str, Any]]],
) -> list[tuple[int, Mapping[str, Any]]]:
    """Pure-mmCIF bridge for ``process_ligand_and_pocket`` pocket semantics.

    The original PDBParser path selects standard amino-acid residues when the
    minimum atom-pair distance is strictly less than ``dist_cutoff``, then
    emits every atom in each selected residue.  Here model 1 and blank/A
    altloc rows are retained deterministically in mmCIF source order.  This is
    intentionally not the atom-level CovaPIE structural-evidence selection.
    """

    if not ligand_heavy_rows:
        _fail("EMPTY_LIGAND_POCKET_SEED")
    _validate_checkpoint_pocket_altloc_compatibility_v1(
        indexed_atom_rows, ligand_heavy_rows
    )
    ligand_coordinates = tuple(
        _raw_coordinates(row, reason="LIGAND_COORDINATES_INVALID")
        for _, row in ligand_heavy_rows
    )
    residue_rows: dict[
        tuple[str, str, str, str, str],
        list[tuple[int, Mapping[str, Any], tuple[float, float, float]]],
    ] = {}
    eligible_in_source_order: list[
        tuple[int, Mapping[str, Any], tuple[str, str, str, str, str]]
    ] = []
    for source_index, row in indexed_atom_rows:
        key = _checkpoint_residue_key_v1(row)
        if key is None:
            continue
        coordinates = _raw_coordinates(
            row, reason="CHECKPOINT_POCKET_PROTEIN_COORDINATES_INVALID"
        )
        residue_rows.setdefault(key, []).append((source_index, row, coordinates))
        eligible_in_source_order.append((source_index, row, key))

    selected_residues = {
        key
        for key, rows in residue_rows.items()
        if min(
            math.dist(protein_xyz, ligand_xyz)
            for _, _, protein_xyz in rows
            for ligand_xyz in ligand_coordinates
        )
        < POCKET_RADIUS_ANGSTROM_V1
    }
    pocket = [
        (source_index, row)
        for source_index, row, key in eligible_in_source_order
        if key in selected_residues
    ]
    if not pocket:
        _fail("EMPTY_CHECKPOINT_MODEL_INPUT_POCKET")
    source_indices = [source_index for source_index, _ in pocket]
    if len(source_indices) != len(set(source_indices)):
        _fail("CHECKPOINT_POCKET_SOURCE_IDENTITY_NOT_UNIQUE")
    return pocket


def _coordinates(
    indexed_rows: Sequence[tuple[int, Mapping[str, Any]]], *, domain: str,
    device: torch.device,
) -> torch.Tensor:
    try:
        values = [
            [float(_atom_value(row, axis)) for axis in ("Cartn_x", "Cartn_y", "Cartn_z")]
            for _, row in indexed_rows
        ]
    except (TypeError, ValueError, OverflowError) as error:
        raise FFQRealStructureMicrobatchAlignmentError(
            f"{_ERROR}:{domain.upper()}_COORDINATES_INVALID"
        ) from error
    if not values or any(not math.isfinite(value) for xyz in values for value in xyz):
        _fail(f"{domain.upper()}_COORDINATES_INVALID")
    return torch.tensor(values, dtype=torch.float32, device=device)


def _checkpoint_center_coordinates_v1(
    ligand_coordinates: torch.Tensor,
    pocket_coordinates: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Match ``ProcessedLigandPocketDataset(center=True)`` for one sample."""

    node_count = len(ligand_coordinates) + len(pocket_coordinates)
    if node_count <= 0:
        _fail("CHECKPOINT_CENTERING_NODE_SET_EMPTY")
    combined_mean = (
        ligand_coordinates.sum(dim=0) + pocket_coordinates.sum(dim=0)
    ) / node_count
    return ligand_coordinates - combined_mean, pocket_coordinates - combined_mean


def _one_hot(channels: Sequence[int], *, device: torch.device) -> torch.Tensor:
    return torch.eye(10, dtype=torch.float32, device=device)[
        torch.tensor(tuple(channels), dtype=torch.long, device=device)
    ]


def _target_indices(
    pocket_rows: Sequence[tuple[int, Mapping[str, Any]]],
    identity: Mapping[str, str],
) -> tuple[tuple[int, ...], int]:
    members = tuple(
        local_index
        for local_index, (_, row) in enumerate(pocket_rows)
        if _preferred_component(row) == identity["residue"]
        and _atom_value(row, "auth_asym_id") == identity["protein_chain"]
        and _atom_value(row, "auth_seq_id") == identity["sequence"]
        and (_atom_value(row, "pdbx_PDB_ins_code") or "NONE")
        == identity["insertion"]
    )
    reactive = tuple(
        local_index
        for local_index in members
        if _preferred_atom_name(pocket_rows[local_index][1])
        == identity["protein_atom"]
    )
    if not members:
        _fail("TARGET_RESIDUE_NOT_IN_MODEL_BOUND_POCKET")
    if len(reactive) != 1:
        _fail("TARGET_RESIDUE_REACTIVE_ATOM_NOT_EXACTLY_ONE")
    return members, reactive[0]


def _ligand_reactive_index(
    ligand_rows: Sequence[Mapping[str, object]],
    source_to_projected: Sequence[int | None],
    reactive_atom_id: str,
) -> int:
    matches = [
        index for index, row in enumerate(ligand_rows)
        if row.get("atom_id") == reactive_atom_id
    ]
    if len(matches) != 1:
        _fail("LIGAND_REACTIVE_ATOM_NOT_EXACTLY_ONE")
    projected = source_to_projected[matches[0]]
    if type(projected) is not int:
        _fail("LIGAND_REACTIVE_ATOM_NOT_RETAINED_HEAVY")
    return projected


def assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
    *, samples: object, device: object = "cpu"
) -> FFQRealStructureMicrobatchAlignmentV1:
    """Build an N-sample FFQ structural batch with local/flat pair alignment."""

    if type(samples) not in (list, tuple) or not samples:
        _fail("SAMPLES_NONEMPTY_LIST_OR_TUPLE_REQUIRED")
    try:
        tensor_device = torch.device(device)
    except (TypeError, RuntimeError) as error:
        raise FFQRealStructureMicrobatchAlignmentError(
            f"{_ERROR}:TORCH_DEVICE_INVALID"
        ) from error

    ligand_coordinates: list[torch.Tensor] = []
    pocket_coordinates: list[torch.Tensor] = []
    ligand_one_hot: list[torch.Tensor] = []
    pocket_one_hot: list[torch.Tensor] = []
    ligand_sources: list[torch.Tensor] = []
    pocket_sources: list[torch.Tensor] = []
    ligand_parser_indices: list[torch.Tensor] = []
    pocket_parser_indices: list[torch.Tensor] = []
    role_ids: list[torch.Tensor] = []
    role_valid: list[torch.Tensor] = []
    generation_masks: list[torch.Tensor] = []
    fixed_masks: list[torch.Tensor] = []
    target_masks: list[torch.Tensor] = []
    context_masks: list[torch.Tensor] = []
    target_membership_masks: list[torch.Tensor] = []
    target_reactive_masks: list[torch.Tensor] = []

    sample_identities: list[str] = []
    task_ids: list[int] = []
    training_admitted: list[bool] = []
    exclusions_preserved: list[bool] = []
    task_c_role_supported: list[bool] = []
    task_c_seed_available: list[bool] = []
    task_c_full_ready: list[bool] = []
    geometry_available: list[bool] = []
    warhead_type_available: list[bool] = []
    ligand_counts: list[int] = []
    pocket_counts: list[int] = []
    target_local_indices: list[int] = []
    ligand_reactive_local_indices: list[int] = []

    for sample_ordinal, raw_sample in enumerate(samples):
        sample = _exact_mapping(
            raw_sample, reason=f"SAMPLE_{sample_ordinal}_EXACT_DICT_REQUIRED"
        )
        if frozenset(sample) != _INPUT_FIELDS:
            _fail(f"SAMPLE_{sample_ordinal}_FIELDS_INVALID")
        payload = sample["cif_gz_payload"]
        if type(payload) is not bytes:
            _fail(f"SAMPLE_{sample_ordinal}_CIF_GZ_PAYLOAD_EXACT_BYTES_REQUIRED")
        record = _exact_mapping(
            sample["effective_supervision_record"],
            reason=f"SAMPLE_{sample_ordinal}_EFFECTIVE_RECORD_EXACT_DICT_REQUIRED",
        )
        task_id = sample["canonical_task_id"]

        try:
            identity = _event_identity(record)
            ligand_rows = ligand_owner.extract_covapie_ligand_atom_identity_rows_from_cif_gz_v1(
                cif_gz_payload=payload,
                ligand_component_id=identity["ligand"],
                label_asym_id=identity["ligand_asym"],
                model_num=1,
            )
            role = role_owner.tensorize_covapie_ffq_direct_profile_role_masks_v1(
                effective_supervision_record=record,
                ligand_atom_rows=ligand_rows,
                canonical_task_id=task_id,
                device=tensor_device,
            )
            atom_rows = _parse_and_crosscheck_atom_site(
                payload, expected_pdb_id=identity["pdb"]
            )
            ligand_preprojection = _crosscheck_ligand_rows(ligand_rows, atom_rows)
            ligand_retained, ligand_channels, ligand_source_to_projected = _projection(
                ligand_preprojection, domain="ligand"
            )
            pocket_preprojection = _build_checkpoint_model_input_pocket_v1(
                list(enumerate(atom_rows)), ligand_retained
            )
            pocket_retained, pocket_channels, _ = _projection(
                pocket_preprojection, domain="pocket"
            )
        except FFQRealStructureMicrobatchAlignmentError:
            raise
        except Exception as error:
            raise FFQRealStructureMicrobatchAlignmentError(
                f"{_ERROR}:SAMPLE_{sample_ordinal}_PUBLISHED_OWNER_REJECTED:"
                f"{type(error).__name__}:{error}"
            ) from error

        if type(task_id) is not int or role.canonical_task_id != task_id:
            _fail(f"SAMPLE_{sample_ordinal}_CANONICAL_TASK_ID_INVALID")
        if len(ligand_retained) != len(role.ligand_role_id):
            _fail(f"SAMPLE_{sample_ordinal}_ROLE_MODEL_ORDER_LENGTH_MISMATCH")
        target_members, target_reactive = _target_indices(
            pocket_retained, identity
        )
        if pocket_channels[target_reactive] != feature_owner.CHECKPOINT_TOKEN_TO_INDEX["S"]:
            _fail(f"SAMPLE_{sample_ordinal}_TARGET_REACTIVE_CHANNEL_NOT_SULFUR")
        ligand_reactive = _ligand_reactive_index(
            ligand_rows, ligand_source_to_projected, identity["ligand_atom"]
        )

        ligand_count = len(ligand_retained)
        pocket_count = len(pocket_retained)
        membership = torch.zeros(
            pocket_count, dtype=torch.bool, device=tensor_device
        )
        membership[list(target_members)] = True
        reactive_mask = torch.zeros(
            pocket_count, dtype=torch.bool, device=tensor_device
        )
        reactive_mask[target_reactive] = True

        raw_ligand_coordinates = _coordinates(
            ligand_retained, domain="ligand", device=tensor_device
        )
        raw_pocket_coordinates = _coordinates(
            pocket_retained, domain="pocket", device=tensor_device
        )
        centered_ligand, centered_pocket = _checkpoint_center_coordinates_v1(
            raw_ligand_coordinates, raw_pocket_coordinates
        )
        ligand_coordinates.append(centered_ligand)
        pocket_coordinates.append(centered_pocket)
        ligand_one_hot.append(_one_hot(ligand_channels, device=tensor_device))
        pocket_one_hot.append(_one_hot(pocket_channels, device=tensor_device))
        ligand_sources.append(torch.tensor(
            [index for index, _ in ligand_retained],
            dtype=torch.long,
            device=tensor_device,
        ))
        pocket_sources.append(torch.tensor(
            [index for index, _ in pocket_retained],
            dtype=torch.long,
            device=tensor_device,
        ))
        ligand_parser_indices.append(torch.arange(
            ligand_count, dtype=torch.long, device=tensor_device
        ))
        pocket_parser_indices.append(torch.arange(
            pocket_count, dtype=torch.long, device=tensor_device
        ))
        role_ids.append(role.ligand_role_id)
        role_valid.append(role.ligand_role_valid)
        generation_masks.append(role.ligand_base_generation_mask)
        fixed_masks.append(role.ligand_base_fixed_mask)
        target_masks.append(role.ligand_base_target_mask)
        context_masks.append(role.ligand_base_context_mask)
        target_membership_masks.append(membership.unsqueeze(1))
        target_reactive_masks.append(reactive_mask.unsqueeze(1))

        sample_identities.append(role.canonical_event_id)
        task_ids.append(task_id)
        if record.get("training_admitted") is not False:
            _fail(f"SAMPLE_{sample_ordinal}_TRAINING_ADMISSION_FORBIDDEN")
        training_admitted.append(False)
        exclusions_preserved.append(
            record.get("human_training_exclusion_preserved") is True
        )
        task_c_role_supported.append(role.task_C_role_mask_supported)
        task_c_seed_available.append(
            role.task_C_minimal_seed_supervision_available
        )
        task_c_full_ready.append(role.full_task_C_training_supervision_ready)
        if (
            record.get("POST_geometry_training_label_available_now") is not False
            or record.get("POST_geometry_supervision_authority_status")
            != "NOT_ESTABLISHED"
            or record.get("PRE_geometry_supervision_authority_status")
            != "NOT_ESTABLISHED"
        ):
            _fail(f"SAMPLE_{sample_ordinal}_GEOMETRY_BOUNDARY_INVALID")
        geometry_available.append(False)
        if record.get("warhead_type_target_available") is not False:
            _fail(f"SAMPLE_{sample_ordinal}_WARHEAD_TYPE_BOUNDARY_INVALID")
        warhead_type_available.append(False)
        ligand_counts.append(ligand_count)
        pocket_counts.append(pocket_count)
        target_local_indices.append(target_reactive)
        ligand_reactive_local_indices.append(ligand_reactive)

    ligand_offsets = [0]
    pocket_offsets = [0]
    for ligand_count, pocket_count in zip(ligand_counts, pocket_counts):
        ligand_offsets.append(ligand_offsets[-1] + ligand_count)
        pocket_offsets.append(pocket_offsets[-1] + pocket_count)

    target_flat = [
        pocket_offsets[index] + local
        for index, local in enumerate(target_local_indices)
    ]
    ligand_reactive_flat = [
        ligand_offsets[index] + local
        for index, local in enumerate(ligand_reactive_local_indices)
    ]
    if any(
        not ligand_offsets[index] <= ligand_flat < ligand_offsets[index + 1]
        or not pocket_offsets[index] <= pocket_flat < pocket_offsets[index + 1]
        for index, (ligand_flat, pocket_flat) in enumerate(
            zip(ligand_reactive_flat, target_flat)
        )
    ):
        _fail("POSITIVE_PAIR_CROSSES_SAMPLE_BOUNDARY")

    batch_size = len(samples)
    lig_mask = torch.repeat_interleave(
        torch.arange(batch_size, dtype=torch.long, device=tensor_device),
        torch.tensor(ligand_counts, dtype=torch.long, device=tensor_device),
    )
    pocket_mask = torch.repeat_interleave(
        torch.arange(batch_size, dtype=torch.long, device=tensor_device),
        torch.tensor(pocket_counts, dtype=torch.long, device=tensor_device),
    )
    model_input_batch = {
        "lig_coords": torch.cat(ligand_coordinates, dim=0),
        "pocket_coords": torch.cat(pocket_coordinates, dim=0),
        "lig_one_hot": torch.cat(ligand_one_hot, dim=0),
        "pocket_one_hot": torch.cat(pocket_one_hot, dim=0),
        "lig_source_row_index": torch.cat(ligand_sources, dim=0),
        "pocket_source_row_index": torch.cat(pocket_sources, dim=0),
        "lig_parser_local_index": torch.cat(ligand_parser_indices, dim=0),
        "pocket_parser_local_index": torch.cat(pocket_parser_indices, dim=0),
        "num_lig_atoms": torch.tensor(
            ligand_counts, dtype=torch.long, device=tensor_device
        ),
        "num_pocket_nodes": torch.tensor(
            pocket_counts, dtype=torch.long, device=tensor_device
        ),
        "lig_mask": lig_mask,
        "pocket_mask": pocket_mask,
    }

    return FFQRealStructureMicrobatchAlignmentV1(
        model_input_batch=model_input_batch,
        sample_identities=tuple(sample_identities),
        ligand_node_offsets=tuple(ligand_offsets),
        pocket_node_offsets=tuple(pocket_offsets),
        ligand_role_id=torch.cat(role_ids, dim=0),
        ligand_role_valid=torch.cat(role_valid, dim=0),
        ligand_generation_mask=torch.cat(generation_masks, dim=0),
        ligand_fixed_mask=torch.cat(fixed_masks, dim=0),
        ligand_target_mask=torch.cat(target_masks, dim=0),
        ligand_context_mask=torch.cat(context_masks, dim=0),
        target_residue_membership_mask=torch.cat(
            target_membership_masks, dim=0
        ),
        target_residue_reactive_atom_mask=torch.cat(
            target_reactive_masks, dim=0
        ),
        target_reactive_local_indices=torch.tensor(
            target_local_indices, dtype=torch.long, device=tensor_device
        ),
        target_reactive_flat_indices=torch.tensor(
            target_flat, dtype=torch.long, device=tensor_device
        ),
        ligand_reactive_local_indices=torch.tensor(
            ligand_reactive_local_indices,
            dtype=torch.long,
            device=tensor_device,
        ),
        ligand_reactive_flat_indices=torch.tensor(
            ligand_reactive_flat, dtype=torch.long, device=tensor_device
        ),
        positive_pair_batch_indices=torch.arange(
            batch_size, dtype=torch.long, device=tensor_device
        ),
        positive_pair_ligand_local_indices=torch.tensor(
            ligand_reactive_local_indices,
            dtype=torch.long,
            device=tensor_device,
        ),
        positive_pair_pocket_local_indices=torch.tensor(
            target_local_indices, dtype=torch.long, device=tensor_device
        ),
        positive_pair_ligand_flat_indices=torch.tensor(
            ligand_reactive_flat, dtype=torch.long, device=tensor_device
        ),
        positive_pair_pocket_flat_indices=torch.tensor(
            target_flat, dtype=torch.long, device=tensor_device
        ),
        canonical_task_ids=torch.tensor(
            task_ids, dtype=torch.long, device=tensor_device
        ),
        sample_training_admitted=torch.tensor(
            training_admitted, dtype=torch.bool, device=tensor_device
        ),
        human_training_exclusion_preserved=torch.tensor(
            exclusions_preserved, dtype=torch.bool, device=tensor_device
        ),
        task_C_role_mask_supported=torch.tensor(
            task_c_role_supported, dtype=torch.bool, device=tensor_device
        ),
        task_C_minimal_seed_supervision_available=torch.tensor(
            task_c_seed_available, dtype=torch.bool, device=tensor_device
        ),
        full_task_C_training_supervision_ready=torch.tensor(
            task_c_full_ready, dtype=torch.bool, device=tensor_device
        ),
        geometry_target_available=torch.tensor(
            geometry_available, dtype=torch.bool, device=tensor_device
        ),
        warhead_type_target_available=torch.tensor(
            warhead_type_available, dtype=torch.bool, device=tensor_device
        ),
    )
