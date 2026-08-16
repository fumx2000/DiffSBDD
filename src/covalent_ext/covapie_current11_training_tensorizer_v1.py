"""Pure in-memory Current11 training-supervision tensorization V1.

The tensorizer is deliberately downstream of the published Task2 runtime
caller.  It accepts already-admitted authority, derives the epoch task and
F03--F09 tensors, and never attempts to recover missing authority.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, fields
from typing import NoReturn

import torch


__all__ = (
    "AUTHORITATIVE_SUPERVISION_SCHEMA_V1",
    "CANONICAL_TASKS_V1",
    "CovapieCurrent11TrainingSupervisionTensorsV1",
    "canonical_task_id_for_covapie_current11_sample_v1",
    "tensorize_covapie_current11_training_supervision_v1",
)


TENSORIZER_ERROR = "COVAPIE_CURRENT11_TRAINING_TENSORIZER_V1_ERROR"
AUTHORITATIVE_SUPERVISION_SCHEMA_V1 = (
    "covapie_current11_authoritative_training_supervision_v1"
)
TASK_SCHEDULE_DOMAIN_V1 = (
    b"COVAPIE_CURRENT11_CANONICAL_TASK_SCHEDULE_V1\0"
)
CANONICAL_TASKS_V1 = (
    (0, "warhead_only", "A", (2,)),
    (1, "linker_plus_warhead", "B", (1, 2)),
    (2, "scaffold_plus_warhead", "B2", (0, 2)),
    (3, "scaffold_only", "B3", (0,)),
    (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
)
_SAMPLE_KEY = re.compile(r"^CYS_SG_SAMPLE_INDEX_[0-9]{6}$")
_SIDECAR_FIELD = "covapie_current11_task2_runtime_result_v1"
_RUNTIME_DERIVED_FORBIDDEN_INPUTS = frozenset((
    "canonical_task_id",
    "canonical_task_valid",
    "canonical_task_alias",
    "canonical_task_name",
    "task_id",
    "task_alias",
    "task_name",
    "ligand_base_generation_mask",
    "ligand_base_fixed_mask",
    "ligand_base_target_mask",
    "ligand_base_context_mask",
    "ligand_active_diffusion_loss_mask",
    "ligand_anchor_distance_angstrom",
    "ligand_anchor_distance_valid",
))
_REQUIRED_AUTHORITY_FIELDS = frozenset((
    "schema_version",
    "sample_keys",
    "ligand_node_offsets",
    "pocket_node_offsets",
    "ligand_role_id",
    "ligand_role_valid",
    "ligand_minimal_seed_or_anchor_mask",
    "ligand_minimal_seed_or_anchor_valid",
    "sample_training_admitted",
    "target_residue_membership_mask",
    "observed_complex_pair_distance_angstrom",
    "observed_complex_pair_distance_valid",
    "pre_post_geometry_target_angstrom",
    "pre_post_geometry_component_valid_mask",
    "pre_post_geometry_component_loss_mask",
))


@dataclass(frozen=True)
class CovapieCurrent11TrainingSupervisionTensorsV1:
    sample_training_admitted: torch.Tensor
    canonical_task_id: torch.Tensor
    canonical_task_valid: torch.Tensor

    ligand_role_id: torch.Tensor
    ligand_role_valid: torch.Tensor

    ligand_base_generation_mask: torch.Tensor
    ligand_base_fixed_mask: torch.Tensor
    ligand_base_target_mask: torch.Tensor
    ligand_base_context_mask: torch.Tensor
    ligand_active_diffusion_loss_mask: torch.Tensor

    ligand_minimal_seed_or_anchor_mask: torch.Tensor
    ligand_minimal_seed_or_anchor_valid: torch.Tensor
    ligand_anchor_distance_angstrom: torch.Tensor
    ligand_anchor_distance_valid: torch.Tensor

    target_residue_membership_mask: torch.Tensor
    target_residue_reactive_atom_mask: torch.Tensor
    target_residue_reactive_atom_local_index: torch.Tensor
    target_residue_reactive_atom_flat_index: torch.Tensor
    target_residue_condition_valid: torch.Tensor

    pair_candidate_offsets: torch.Tensor
    pair_candidate_batch_index: torch.Tensor
    pair_candidate_ligand_local_index: torch.Tensor
    pair_candidate_residue_local_index: torch.Tensor
    pair_candidate_ligand_flat_index: torch.Tensor
    pair_candidate_pocket_flat_index: torch.Tensor

    pair_candidate_is_positive: torch.Tensor
    pair_candidate_is_negative: torch.Tensor
    pair_positive_candidate_index: torch.Tensor
    pair_positive_candidate_valid: torch.Tensor
    pair_negative_count: torch.Tensor
    pair_head_candidate_loss_mask: torch.Tensor
    pair_contrastive_sample_loss_mask: torch.Tensor

    observed_complex_pair_distance_angstrom: torch.Tensor
    observed_complex_pair_distance_valid: torch.Tensor
    pre_post_geometry_target_angstrom: torch.Tensor
    pre_post_geometry_component_valid_mask: torch.Tensor
    pre_post_geometry_component_loss_mask: torch.Tensor

    def __post_init__(self) -> None:
        if any(not isinstance(getattr(self, field.name), torch.Tensor)
               for field in fields(self)):
            raise ValueError(TENSORIZER_ERROR)


class _TensorizerInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _TensorizerInvariantError()


def canonical_task_id_for_covapie_current11_sample_v1(
    *, sample_key: object, epoch: object, task_schedule_seed: object
) -> int:
    """Return the domain-separated, order/rank-independent Exact5 task id."""

    try:
        if (
            type(task_schedule_seed) is not int
            or not 0 <= task_schedule_seed <= 2**63 - 1
            or type(epoch) is not int
            or epoch < 0
            or type(sample_key) is not str
            or _SAMPLE_KEY.fullmatch(sample_key) is None
        ):
            _fail()
        try:
            encoded_key = sample_key.encode("ascii")
        except UnicodeEncodeError:
            _fail()
        payload = (
            TASK_SCHEDULE_DOMAIN_V1
            + str(task_schedule_seed).encode("ascii")
            + b"\0"
            + encoded_key
        )
        base = int.from_bytes(
            hashlib.sha256(payload).digest()[:8],
            byteorder="big",
            signed=False,
        ) % 5
        return (base + epoch) % 5
    except _TensorizerInvariantError as error:
        raise ValueError(TENSORIZER_ERROR) from error


def _sequence(value: object, *, length: int | None = None) -> tuple[object, ...]:
    if type(value) not in (list, tuple):
        _fail()
    result = tuple(value)
    if length is not None and len(result) != length:
        _fail()
    return result


def _exact_ints(value: object, *, length: int | None = None) -> tuple[int, ...]:
    result = _sequence(value, length=length)
    if any(type(item) is not int for item in result):
        _fail()
    return result  # type: ignore[return-value]


def _exact_bools(value: object, *, length: int | None = None) -> tuple[bool, ...]:
    result = _sequence(value, length=length)
    if any(type(item) is not bool for item in result):
        _fail()
    return result  # type: ignore[return-value]


def _exact_floats(value: object, *, length: int | None = None) -> tuple[float, ...]:
    result = _sequence(value, length=length)
    if any(type(item) is not float for item in result):
        _fail()
    return result  # type: ignore[return-value]


def _matrix(
    value: object,
    *,
    rows: int,
    columns: int,
    scalar_type: type,
) -> tuple[tuple[object, ...], ...]:
    outer = _sequence(value, length=rows)
    result: list[tuple[object, ...]] = []
    for row in outer:
        values = _sequence(row, length=columns)
        if any(type(item) is not scalar_type for item in values):
            _fail()
        result.append(values)
    return tuple(result)


def _validated_offsets(
    value: object, *, batch_size: int, total: int
) -> tuple[int, ...]:
    offsets = _exact_ints(value, length=batch_size + 1)
    if (
        not offsets
        or offsets[0] != 0
        or offsets[-1] != total
        or any(left >= right for left, right in zip(offsets, offsets[1:]))
    ):
        _fail()
    return offsets


def _require_batch_tensor(
    batch: dict[str, object],
    name: str,
    *,
    ndim: int,
    length: int | None = None,
) -> torch.Tensor:
    value = batch.get(name)
    if (
        not isinstance(value, torch.Tensor)
        or value.ndim != ndim
        or (length is not None and len(value) != length)
    ):
        _fail()
    return value


def _validate_one_hot(value: torch.Tensor, *, rows: int) -> None:
    if (
        value.ndim != 2
        or value.shape != (rows, 10)
        or not value.dtype.is_floating_point
        or not bool(torch.isfinite(value).all().item())
        or not bool(((value == 0) | (value == 1)).all().item())
        or not bool((value.sum(dim=1) == 1).all().item())
    ):
        _fail()


def _expected_membership_mask(
    offsets: tuple[int, ...], *, device: torch.device
) -> torch.Tensor:
    lengths = torch.tensor(
        [right - left for left, right in zip(offsets, offsets[1:])],
        dtype=torch.long,
        device=device,
    )
    return torch.repeat_interleave(
        torch.arange(len(lengths), device=device, dtype=torch.long), lengths
    )


def _validate_numeric_authority(
    *,
    observed: tuple[float, ...],
    observed_valid: tuple[bool, ...],
    geometry: tuple[tuple[object, ...], ...],
    geometry_valid: tuple[tuple[object, ...], ...],
    geometry_loss: tuple[tuple[object, ...], ...],
) -> None:
    for value, valid in zip(observed, observed_valid):
        if valid:
            if not math.isfinite(value) or value < 0:
                _fail()
        elif not math.isnan(value):
            _fail()
    for target_row, valid_row, loss_row in zip(
        geometry, geometry_valid, geometry_loss
    ):
        for target, valid, loss in zip(target_row, valid_row, loss_row):
            if loss and not valid:
                _fail()
            if valid:
                if not math.isfinite(target) or target < 0:
                    _fail()
            elif not math.isnan(target):
                # This is the mechanical guard against observed-distance or
                # zero/mean substitution into unavailable pre/post labels.
                _fail()


def _tensorize_impl(
    *,
    batch: object,
    runtime_result: object,
    authoritative_supervision: object,
    device: object,
    epoch: object,
    task_schedule_seed: object,
) -> CovapieCurrent11TrainingSupervisionTensorsV1:
    if type(batch) is not dict or type(runtime_result) is not dict:
        _fail()
    if batch.get(_SIDECAR_FIELD) is not runtime_result:
        _fail()
    if runtime_result.get("runtime_status") != "full_success":
        _fail()
    if type(authoritative_supervision) is not dict:
        _fail()
    if not _REQUIRED_AUTHORITY_FIELDS.issubset(authoritative_supervision):
        _fail()
    if _RUNTIME_DERIVED_FORBIDDEN_INPUTS & set(authoritative_supervision):
        _fail()
    if (
        authoritative_supervision.get("schema_version")
        != AUTHORITATIVE_SUPERVISION_SCHEMA_V1
    ):
        _fail()
    try:
        model_device = torch.device(device)
    except (TypeError, RuntimeError):
        _fail()

    sample_keys_raw = _sequence(authoritative_supervision["sample_keys"])
    if (
        not sample_keys_raw
        or any(
            type(key) is not str or _SAMPLE_KEY.fullmatch(key) is None
            for key in sample_keys_raw
        )
        or len(set(sample_keys_raw)) != len(sample_keys_raw)
    ):
        _fail()
    sample_keys = tuple(sample_keys_raw)  # type: ignore[assignment]
    batch_size = len(sample_keys)
    runtime_keys = runtime_result.get("batch_sample_keys_or_none")
    output17 = runtime_result.get("remap_output17_or_none")
    if (
        type(runtime_keys) is not list
        or tuple(runtime_keys) != sample_keys
        or type(output17) is not dict
        or output17.get("remap_status") != "REMAPPED_EXACT"
        or output17.get("failure_reason") != "NONE"
        or tuple(output17.get("batch_sample_order", ())) != sample_keys
    ):
        _fail()

    lig_coords = _require_batch_tensor(batch, "lig_coords", ndim=2)
    pocket_coords = _require_batch_tensor(batch, "pocket_coords", ndim=2)
    if (
        lig_coords.shape[1:] != (3,)
        or pocket_coords.shape[1:] != (3,)
        or not lig_coords.dtype.is_floating_point
        or not pocket_coords.dtype.is_floating_point
        or not bool(torch.isfinite(lig_coords).all().item())
        or not bool(torch.isfinite(pocket_coords).all().item())
    ):
        _fail()
    ligand_total = len(lig_coords)
    pocket_total = len(pocket_coords)
    ligand_offsets = _validated_offsets(
        authoritative_supervision["ligand_node_offsets"],
        batch_size=batch_size,
        total=ligand_total,
    )
    pocket_offsets = _validated_offsets(
        authoritative_supervision["pocket_node_offsets"],
        batch_size=batch_size,
        total=pocket_total,
    )

    lig_mask = _require_batch_tensor(batch, "lig_mask", ndim=1, length=ligand_total)
    pocket_mask = _require_batch_tensor(
        batch, "pocket_mask", ndim=1, length=pocket_total
    )
    lig_sizes = _require_batch_tensor(
        batch, "num_lig_atoms", ndim=1, length=batch_size
    )
    pocket_sizes = _require_batch_tensor(
        batch, "num_pocket_nodes", ndim=1, length=batch_size
    )
    expected_lig_mask = _expected_membership_mask(
        ligand_offsets, device=lig_mask.device
    )
    expected_pocket_mask = _expected_membership_mask(
        pocket_offsets, device=pocket_mask.device
    )
    expected_lig_sizes = torch.tensor(
        [right - left for left, right in zip(ligand_offsets, ligand_offsets[1:])],
        dtype=lig_sizes.dtype,
        device=lig_sizes.device,
    )
    expected_pocket_sizes = torch.tensor(
        [right - left for left, right in zip(pocket_offsets, pocket_offsets[1:])],
        dtype=pocket_sizes.dtype,
        device=pocket_sizes.device,
    )
    if (
        lig_mask.dtype != torch.long
        or pocket_mask.dtype != torch.long
        or lig_sizes.dtype != torch.long
        or pocket_sizes.dtype != torch.long
        or not torch.equal(lig_mask, expected_lig_mask)
        or not torch.equal(pocket_mask, expected_pocket_mask)
        or not torch.equal(lig_sizes, expected_lig_sizes)
        or not torch.equal(pocket_sizes, expected_pocket_sizes)
    ):
        _fail()
    lig_one_hot = _require_batch_tensor(
        batch, "lig_one_hot", ndim=2, length=ligand_total
    )
    pocket_one_hot = _require_batch_tensor(
        batch, "pocket_one_hot", ndim=2, length=pocket_total
    )
    _validate_one_hot(lig_one_hot, rows=ligand_total)
    _validate_one_hot(pocket_one_hot, rows=pocket_total)

    roles = _exact_ints(
        authoritative_supervision["ligand_role_id"], length=ligand_total
    )
    role_valid = _exact_bools(
        authoritative_supervision["ligand_role_valid"], length=ligand_total
    )
    admitted = _exact_bools(
        authoritative_supervision["sample_training_admitted"],
        length=batch_size,
    )
    source_seed = _exact_bools(
        authoritative_supervision["ligand_minimal_seed_or_anchor_mask"],
        length=ligand_total,
    )
    source_seed_valid = _exact_bools(
        authoritative_supervision["ligand_minimal_seed_or_anchor_valid"],
        length=batch_size,
    )
    membership = _exact_bools(
        authoritative_supervision["target_residue_membership_mask"],
        length=pocket_total,
    )
    for sample in range(batch_size):
        lig_slice = slice(ligand_offsets[sample], ligand_offsets[sample + 1])
        sample_roles = roles[lig_slice]
        sample_valid = role_valid[lig_slice]
        if any(
            (valid and role not in (0, 1, 2))
            or (not valid and role != -1)
            for role, valid in zip(sample_roles, sample_valid)
        ):
            _fail()
        if admitted[sample] and (
            not all(sample_valid)
            or set(sample_roles) != {0, 1, 2}
        ):
            _fail()
        seed_slice = source_seed[lig_slice]
        if source_seed_valid[sample] != any(seed_slice):
            _fail()
        pocket_slice = membership[
            pocket_offsets[sample]:pocket_offsets[sample + 1]
        ]
        if admitted[sample] and not any(pocket_slice):
            _fail()

    task_ids = tuple(
        canonical_task_id_for_covapie_current11_sample_v1(
            sample_key=key,
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
        )
        for key in sample_keys
    )
    canonical_task_id = torch.tensor(
        task_ids, dtype=torch.long, device=model_device
    )
    canonical_task_valid = torch.ones(
        batch_size, dtype=torch.bool, device=model_device
    )
    sample_training_admitted = torch.tensor(
        admitted, dtype=torch.bool, device=model_device
    )
    ligand_role_id = torch.tensor(roles, dtype=torch.long, device=model_device)
    ligand_role_valid = torch.tensor(
        role_valid, dtype=torch.bool, device=model_device
    )
    ligand_batch = _expected_membership_mask(ligand_offsets, device=model_device)
    pocket_batch = _expected_membership_mask(pocket_offsets, device=model_device)

    generated_by_task = torch.tensor(
        [
            [role in set(task[3]) for role in range(3)]
            for task in CANONICAL_TASKS_V1
        ],
        dtype=torch.bool,
        device=model_device,
    )
    safe_roles = ligand_role_id.clamp(min=0, max=2)
    generation = (
        generated_by_task[canonical_task_id[ligand_batch], safe_roles]
        & ligand_role_valid
    )
    fixed = ligand_role_valid & ~generation
    active = (
        generation
        & canonical_task_valid[ligand_batch]
        & sample_training_admitted[ligand_batch]
    )
    for sample in range(batch_size):
        sample_nodes = ligand_batch == sample
        if sample_training_admitted[sample] and (
            not bool(generation[sample_nodes].any().item())
            or (
                task_ids[sample] != 4
                and not bool(fixed[sample_nodes].any().item())
            )
        ):
            _fail()

    source_seed_tensor = torch.tensor(
        source_seed, dtype=torch.bool, device=model_device
    )
    source_seed_valid_tensor = torch.tensor(
        source_seed_valid, dtype=torch.bool, device=model_device
    )
    task_c = canonical_task_id == 4
    runtime_seed_valid = task_c & source_seed_valid_tensor
    runtime_seed = source_seed_tensor & runtime_seed_valid[ligand_batch]

    target_membership = torch.tensor(
        membership, dtype=torch.bool, device=model_device
    )
    indicator = batch.get("pocket_target_residue_atom_condition_indicator")
    if (
        not isinstance(indicator, torch.Tensor)
        or indicator.dtype != torch.bool
        or indicator.ndim != 1
        or len(indicator) != pocket_total
    ):
        _fail()
    indicator = indicator.to(device=model_device)
    if bool((indicator & ~target_membership).any().item()):
        _fail()
    target_local: list[int] = []
    target_flat: list[int] = []
    target_valid: list[bool] = []
    for sample in range(batch_size):
        start, end = pocket_offsets[sample], pocket_offsets[sample + 1]
        positions = torch.nonzero(indicator[start:end], as_tuple=False).flatten()
        if positions.numel() != 1:
            _fail()
        local = int(positions[0].item())
        target_local.append(local)
        target_flat.append(start + local)
        target_valid.append(True)
    target_condition_valid = torch.tensor(
        target_valid, dtype=torch.bool, device=model_device
    )
    target_flat_tensor = torch.tensor(
        target_flat, dtype=torch.long, device=model_device
    )

    # F13/F14 are derived from admitted model-index-space coordinates.  Both
    # coordinate buffers are moved once to the requested model device.
    lig_coords_device = lig_coords.to(device=model_device, dtype=torch.float32)
    pocket_coords_device = pocket_coords.to(
        device=model_device, dtype=torch.float32
    )
    anchor_distance = torch.linalg.vector_norm(
        lig_coords_device
        - pocket_coords_device[target_flat_tensor[ligand_batch]],
        dim=1,
        keepdim=True,
    )
    anchor_valid = (
        target_condition_valid[ligand_batch]
        & sample_training_admitted[ligand_batch]
    ).unsqueeze(1)
    anchor_distance = torch.where(
        anchor_valid,
        anchor_distance,
        torch.full_like(anchor_distance, float("nan")),
    )

    pairs = _matrix(
        output17.get("pair_values_batch_indices"),
        rows=len(output17.get("pair_values_batch_indices", ())),
        columns=2,
        scalar_type=int,
    )
    pair_samples = _exact_ints(output17.get("pair_sample_indices"))
    pair_offsets_source = _exact_ints(
        output17.get("sample_pair_offsets"), length=batch_size + 1
    )
    entry_validity = _exact_bools(
        output17.get("entry_validity"), length=len(pairs)
    )
    sample_validity = _exact_bools(
        output17.get("sample_validity"), length=batch_size
    )
    parser_pairs = _matrix(
        output17.get("pair_values_parser_local_indices"),
        rows=len(pairs),
        columns=2,
        scalar_type=int,
    )
    joint_pairs_raw = output17.get("pair_values_joint_global_indices")
    joint_pairs = None
    if joint_pairs_raw is not None:
        joint_pairs = _matrix(
            joint_pairs_raw,
            rows=len(pairs),
            columns=2,
            scalar_type=int,
        )
    if (
        len(pair_samples) != len(pairs)
        or pair_offsets_source[0] != 0
        or pair_offsets_source[-1] != len(pairs)
        or any(
            left > right
            for left, right in zip(pair_offsets_source, pair_offsets_source[1:])
        )
        or not all(entry_validity)
        or not all(sample_validity)
    ):
        _fail()
    positive_by_sample: list[tuple[int, int]] = []
    for sample in range(batch_size):
        start, end = pair_offsets_source[sample], pair_offsets_source[sample + 1]
        if admitted[sample] and end - start != 1:
            _fail()
        if end - start != 1:
            _fail()
        ordinal = start
        if pair_samples[ordinal] != sample:
            _fail()
        pocket_flat, ligand_flat = pairs[ordinal]
        if (
            not ligand_offsets[sample] <= ligand_flat < ligand_offsets[sample + 1]
            or not pocket_offsets[sample] <= pocket_flat < pocket_offsets[sample + 1]
            or parser_pairs[ordinal]
            != (
                pocket_flat - pocket_offsets[sample],
                ligand_flat - ligand_offsets[sample],
            )
            or pocket_flat != target_flat[sample]
        ):
            _fail()
        if joint_pairs is not None and joint_pairs[ordinal] != (
            ligand_total + pocket_flat,
            ligand_flat,
        ):
            _fail()
        if admitted[sample] and not membership[pocket_flat]:
            _fail()
        positive_by_sample.append((ligand_flat, pocket_flat))

    candidate_batches: list[torch.Tensor] = []
    candidate_lig_local: list[torch.Tensor] = []
    candidate_pocket_local: list[torch.Tensor] = []
    candidate_lig_flat: list[torch.Tensor] = []
    candidate_pocket_flat: list[torch.Tensor] = []
    candidate_positive: list[torch.Tensor] = []
    candidate_offsets = [0]
    positive_candidate_index: list[int] = []
    positive_candidate_valid: list[bool] = []
    negative_count: list[int] = []
    for sample in range(batch_size):
        lig_start, lig_end = ligand_offsets[sample], ligand_offsets[sample + 1]
        pocket_start, pocket_end = (
            pocket_offsets[sample], pocket_offsets[sample + 1]
        )
        member_local = torch.nonzero(
            target_membership[pocket_start:pocket_end], as_tuple=False
        ).flatten()
        if member_local.numel() == 0:
            if admitted[sample]:
                _fail()
            candidate_offsets.append(candidate_offsets[-1])
            positive_candidate_index.append(-1)
            positive_candidate_valid.append(False)
            negative_count.append(0)
            continue
        lig_local = torch.arange(
            lig_end - lig_start, device=model_device, dtype=torch.long
        ).repeat_interleave(member_local.numel())
        pocket_local = member_local.repeat(lig_end - lig_start)
        lig_flat = lig_local + lig_start
        pocket_flat = pocket_local + pocket_start
        positive_lig, positive_pocket = positive_by_sample[sample]
        positive = (lig_flat == positive_lig) & (pocket_flat == positive_pocket)
        if admitted[sample] and int(positive.sum().item()) != 1:
            _fail()
        count = len(lig_flat)
        start = candidate_offsets[-1]
        candidate_batches.append(torch.full(
            (count,), sample, dtype=torch.long, device=model_device
        ))
        candidate_lig_local.append(lig_local)
        candidate_pocket_local.append(pocket_local)
        candidate_lig_flat.append(lig_flat)
        candidate_pocket_flat.append(pocket_flat)
        candidate_positive.append(positive)
        candidate_offsets.append(start + count)
        if admitted[sample]:
            positive_index = start + int(
                torch.nonzero(positive, as_tuple=False)[0, 0].item()
            )
            positive_candidate_index.append(positive_index)
            positive_candidate_valid.append(True)
            negative_count.append(count - 1)
        else:
            positive_candidate_index.append(-1)
            positive_candidate_valid.append(False)
            negative_count.append(count - int(positive.sum().item()))

    def _cat_or_empty(parts: list[torch.Tensor]) -> torch.Tensor:
        if parts:
            return torch.cat(parts, dim=0)
        return torch.empty(0, dtype=torch.long, device=model_device)

    pair_candidate_batch_index = _cat_or_empty(candidate_batches)
    pair_candidate_ligand_local_index = _cat_or_empty(candidate_lig_local)
    pair_candidate_residue_local_index = _cat_or_empty(candidate_pocket_local)
    pair_candidate_ligand_flat_index = _cat_or_empty(candidate_lig_flat)
    pair_candidate_pocket_flat_index = _cat_or_empty(candidate_pocket_flat)
    if candidate_positive:
        pair_candidate_is_positive = torch.cat(candidate_positive, dim=0)
    else:
        pair_candidate_is_positive = torch.empty(
            0, dtype=torch.bool, device=model_device
        )
    pair_candidate_is_negative = ~pair_candidate_is_positive
    pair_positive_valid_tensor = torch.tensor(
        positive_candidate_valid, dtype=torch.bool, device=model_device
    )
    pair_negative_count = torch.tensor(
        negative_count, dtype=torch.long, device=model_device
    )
    pair_head_candidate_loss_mask = (
        sample_training_admitted[pair_candidate_batch_index]
        if len(pair_candidate_batch_index)
        else torch.empty(0, dtype=torch.bool, device=model_device)
    )
    pair_contrastive_sample_loss_mask = (
        pair_positive_valid_tensor & (pair_negative_count > 0)
    )

    observed = _exact_floats(
        authoritative_supervision["observed_complex_pair_distance_angstrom"],
        length=batch_size,
    )
    observed_valid = _exact_bools(
        authoritative_supervision["observed_complex_pair_distance_valid"],
        length=batch_size,
    )
    geometry = _matrix(
        authoritative_supervision["pre_post_geometry_target_angstrom"],
        rows=batch_size,
        columns=2,
        scalar_type=float,
    )
    geometry_valid = _matrix(
        authoritative_supervision["pre_post_geometry_component_valid_mask"],
        rows=batch_size,
        columns=2,
        scalar_type=bool,
    )
    geometry_loss = _matrix(
        authoritative_supervision["pre_post_geometry_component_loss_mask"],
        rows=batch_size,
        columns=2,
        scalar_type=bool,
    )
    _validate_numeric_authority(
        observed=observed,
        observed_valid=observed_valid,
        geometry=geometry,
        geometry_valid=geometry_valid,
        geometry_loss=geometry_loss,
    )
    geometry_valid_tensor = torch.tensor(
        geometry_valid, dtype=torch.bool, device=model_device
    )
    geometry_loss_tensor = torch.tensor(
        geometry_loss, dtype=torch.bool, device=model_device
    )
    geometry_loss_tensor = (
        geometry_loss_tensor
        & geometry_valid_tensor
        & sample_training_admitted.unsqueeze(1)
        & pair_positive_valid_tensor.unsqueeze(1)
    )

    return CovapieCurrent11TrainingSupervisionTensorsV1(
        sample_training_admitted=sample_training_admitted,
        canonical_task_id=canonical_task_id,
        canonical_task_valid=canonical_task_valid,
        ligand_role_id=ligand_role_id,
        ligand_role_valid=ligand_role_valid,
        ligand_base_generation_mask=generation.unsqueeze(1),
        ligand_base_fixed_mask=fixed.unsqueeze(1),
        ligand_base_target_mask=generation.unsqueeze(1),
        ligand_base_context_mask=fixed.unsqueeze(1),
        ligand_active_diffusion_loss_mask=active.unsqueeze(1),
        ligand_minimal_seed_or_anchor_mask=runtime_seed.unsqueeze(1),
        ligand_minimal_seed_or_anchor_valid=runtime_seed_valid,
        ligand_anchor_distance_angstrom=anchor_distance,
        ligand_anchor_distance_valid=anchor_valid,
        target_residue_membership_mask=target_membership.unsqueeze(1),
        target_residue_reactive_atom_mask=indicator.unsqueeze(1),
        target_residue_reactive_atom_local_index=torch.tensor(
            target_local, dtype=torch.long, device=model_device
        ),
        target_residue_reactive_atom_flat_index=target_flat_tensor,
        target_residue_condition_valid=target_condition_valid,
        pair_candidate_offsets=torch.tensor(
            candidate_offsets, dtype=torch.long, device=model_device
        ),
        pair_candidate_batch_index=pair_candidate_batch_index,
        pair_candidate_ligand_local_index=pair_candidate_ligand_local_index,
        pair_candidate_residue_local_index=pair_candidate_residue_local_index,
        pair_candidate_ligand_flat_index=pair_candidate_ligand_flat_index,
        pair_candidate_pocket_flat_index=pair_candidate_pocket_flat_index,
        pair_candidate_is_positive=pair_candidate_is_positive,
        pair_candidate_is_negative=pair_candidate_is_negative,
        pair_positive_candidate_index=torch.tensor(
            positive_candidate_index, dtype=torch.long, device=model_device
        ),
        pair_positive_candidate_valid=pair_positive_valid_tensor,
        pair_negative_count=pair_negative_count,
        pair_head_candidate_loss_mask=pair_head_candidate_loss_mask,
        pair_contrastive_sample_loss_mask=pair_contrastive_sample_loss_mask,
        observed_complex_pair_distance_angstrom=torch.tensor(
            observed, dtype=torch.float32, device=model_device
        ).unsqueeze(1),
        observed_complex_pair_distance_valid=torch.tensor(
            observed_valid, dtype=torch.bool, device=model_device
        ).unsqueeze(1),
        pre_post_geometry_target_angstrom=torch.tensor(
            geometry, dtype=torch.float32, device=model_device
        ),
        pre_post_geometry_component_valid_mask=geometry_valid_tensor,
        pre_post_geometry_component_loss_mask=geometry_loss_tensor,
    )


def tensorize_covapie_current11_training_supervision_v1(
    *,
    batch: object,
    runtime_result: object,
    authoritative_supervision: object,
    device: object,
    epoch: object,
    task_schedule_seed: object,
) -> CovapieCurrent11TrainingSupervisionTensorsV1:
    """Validate source/runtime identity and create the complete device bundle."""

    try:
        return _tensorize_impl(
            batch=batch,
            runtime_result=runtime_result,
            authoritative_supervision=authoritative_supervision,
            device=device,
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == TENSORIZER_ERROR:
            raise
        raise ValueError(TENSORIZER_ERROR) from error
