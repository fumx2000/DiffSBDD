"""Task-A-only supervised forward adapter for the published FFQ microbatch.

This module deliberately stops at raw auxiliary predictions.  It does not
enter the Current11 training forward, construct a loss, or mutate parameters.
"""

from __future__ import annotations

import contextlib
import copy
import io
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, NoReturn, Sequence

import torch
from torch import Tensor
from torch_scatter import scatter_mean

from covalent_ext.biopython_compat import patch_biopython_polypeptide_three_to_one

patch_biopython_polypeptide_three_to_one()

import constants  # noqa: E402
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (  # noqa: E402
    CovapieCurrent11ModelOutputV1,
)
from covalent_ext.covapie_current11_checkpoint_migration_v1 import (  # noqa: E402
    load_covapie_current11_legacy_checkpoint_v1,
    migrate_covapie_current11_legacy_checkpoint_state_dict_v1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (  # noqa: E402
    CovapieCurrent11FunctionalDynamicsOutputV1,
    CovapieCurrent11TrainingLigandPocketDDPM,
    run_covapie_current11_functional_dynamics_with_hidden_v1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (  # noqa: E402
    CovapieCurrent11TrainingSupervisionTensorsV1,
)
from covalent_ext.diffsbdd_model_instantiation import _constructor_kwargs  # noqa: E402
from covalent_ext.covapie_ffq_real_structure_microbatch_alignment_v1 import (  # noqa: E402
    FFQRealStructureMicrobatchAlignmentV1,
    assemble_covapie_ffq_real_structure_microbatch_alignment_v1,
)
from covalent_ext.covapie_tensor_label_and_loss_mask_contract_design_v1 import (  # noqa: E402
    PairCandidateSampleSpec,
    build_pair_candidate_records_v1,
)
ERROR_PREFIX_V1 = "COVAPIE_FFQ_SUPERVISED_FORWARD_ADAPTER_V1_ERROR"
TASK_NOT_SUPPORTED_BY_FFQ_SUPERVISED_FORWARD_V1 = (
    "TASK_NOT_SUPPORTED_BY_FFQ_SUPERVISED_FORWARD_V1"
)
MODEL_INIT_SEED_V1 = 20260824
FORWARD_NOISE_SEED_V1 = 20260824
TIMESTEP_INT_V1 = 250
DIFFUSION_TIMESTEP_INT_V1 = TIMESTEP_INT_V1
_EXPECTED_LIGAND_COUNT_V1 = 8
_EXPECTED_TARGET_RESIDUE_COUNT_V1 = 6
_EXPECTED_FIXED_LIGAND_COUNT_V1 = 4
_EXPECTED_SAMPLE_IDENTITIES_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:3VCY:A:CYS:116-:SG:E:FFQ:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4R7U:A:CYS:116-:SG:F:FFQ:C1",
)
_EXPECTED_CHECKPOINT_KEY_COUNT_V1 = 122
_EXPECTED_TARGET_MODEL_KEY_COUNT_V1 = 141
_EXPECTED_TARGET_ONLY_KEY_COUNT_V1 = 19
_EXACT10_TOKENS_V1 = ("C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F")
_MODEL_CONSTRUCTOR_FIELDS_V1 = (
    "outdir",
    "dataset",
    "datadir",
    "batch_size",
    "lr",
    "egnn_params",
    "diffusion_params",
    "num_workers",
    "augment_noise",
    "augment_rotation",
    "clip_grad",
    "eval_epochs",
    "eval_params",
    "visualize_sample_epoch",
    "visualize_chain_epoch",
    "auxiliary_loss",
    "loss_params",
    "mode",
    "node_histogram",
    "pocket_representation",
    "virtual_nodes",
)


class FFQSupervisedForwardAdapterError(ValueError):
    """Fail-closed public error for the bounded adapter."""


def _fail(reason: str) -> NoReturn:
    raise FFQSupervisedForwardAdapterError(f"{ERROR_PREFIX_V1}:{reason}")


@dataclass(frozen=True)
class _FFQAuxiliaryTraceV1:
    """The exact seven trace attributes consumed by the auxiliary module."""

    diffusion_epsilon_prediction_ligand: Tensor
    denoised_ligand_xh: Tensor
    diffusion_timestep_int: Tensor
    ligand_node_hidden: Tensor
    pocket_node_hidden: Tensor
    clean_centered_pocket_xh: Tensor
    coordinate_normalization: float


@dataclass(frozen=True)
class FFQTaskASupervisedForwardResultV1:
    """Auditable result of one deterministic, loss-free supervised forward."""

    sample_identities: tuple[str, ...]
    structural_alignment: FFQRealStructureMicrobatchAlignmentV1
    structural_batch_summary: Mapping[str, object]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1
    migration_summary: Mapping[str, object]
    functional_dynamics_output: CovapieCurrent11FunctionalDynamicsOutputV1
    model_output: CovapieCurrent11ModelOutputV1
    clean_ligand_xh: Tensor
    clean_pocket_xh: Tensor
    noised_ligand_xh: Tensor
    sampled_epsilon_ligand: Tensor
    timestep_int: Tensor
    role_mask_anchor_hidden_delta: Tensor
    role_mask_anchor_hidden_delta_exact_zero: bool
    target_residue_embedding_max_abs: float
    state_tensor_changed_count: int
    input_tensor_changed_count: int
    all_parameter_grads_none: bool
    model_eval_mode_verified: bool
    ddpm_eval_mode_verified: bool
    auxiliary_eval_mode_verified: bool
    gradient_recording_disabled: bool
    joint_objective_loss_executed: bool
    base_diffusion_loss_executed: bool
    pair_loss_executed: bool
    geometry_loss_executed: bool
    contrastive_loss_executed: bool
    current11_runtime_executed: bool
    training_performed: bool
    backward_performed: bool
    optimizer_step_performed: bool
    parameter_update_performed: bool
    raw_pair_prediction_available: bool
    raw_geometry_prediction_available: bool
    geometry_authority_available: bool

    @property
    def joint_loss_evaluated(self) -> bool:
        return self.joint_objective_loss_executed

    @property
    def base_training_loss_evaluated(self) -> bool:
        return self.base_diffusion_loss_executed

    @property
    def pair_loss_evaluated(self) -> bool:
        return self.pair_loss_executed

    @property
    def geometry_loss_evaluated(self) -> bool:
        return self.geometry_loss_executed

    @property
    def contrastive_loss_evaluated(self) -> bool:
        return self.contrastive_loss_executed

    @property
    def optimizer_created(self) -> bool:
        return False

    @property
    def training_step_executed(self) -> bool:
        return False

    @property
    def trainer_fit_executed(self) -> bool:
        return False

    @property
    def finetune_performed(self) -> bool:
        return False

    @property
    def ready_for_training(self) -> bool:
        return False

    @property
    def raw_geometry_head_forward_only(self) -> bool:
        return self.raw_geometry_prediction_available and not self.geometry_authority_available

    @property
    def geometry_supervision_established(self) -> bool:
        return self.geometry_authority_available

    @property
    def node_histogram_public_successor_required_now(self) -> bool:
        return False

    @property
    def target_residue_condition_path_executed(self) -> bool:
        return True

    @property
    def task_a_masked_functional_dynamics_executed(self) -> bool:
        return True

    @property
    def auxiliary_pair_head_forward_executed(self) -> bool:
        return self.raw_pair_prediction_available


# Descriptive compatibility alias; the Task-A name is the canonical V1 result.
FFQSupervisedForwardAdapterResultV1 = FFQTaskASupervisedForwardResultV1


def _require_seed(value: int, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail(f"INVALID_{name}")
    return value


def _require_absolute_file(path: Path, *, name: str) -> Path:
    if not isinstance(path, Path) or not path.is_absolute() or not path.is_file():
        _fail(f"INVALID_{name}")
    return path


def _require_absolute_directory(path: Path, *, name: str) -> Path:
    if not isinstance(path, Path) or not path.is_absolute() or not path.is_dir():
        _fail(f"INVALID_{name}")
    return path


def _precheck_task_a_only(samples: Sequence[Mapping[str, object]]) -> None:
    if isinstance(samples, (str, bytes, bytearray)) or not isinstance(samples, Sequence):
        _fail("INVALID_SAMPLES")
    for sample in samples:
        if not isinstance(sample, Mapping):
            continue
        task_id = sample.get("canonical_task_id")
        if task_id is not None and (isinstance(task_id, bool) or task_id != 0):
            _fail(TASK_NOT_SUPPORTED_BY_FFQ_SUPERVISED_FORWARD_V1)


def _snapshot_tensor_mapping(values: Mapping[str, object]) -> dict[str, Tensor]:
    return {
        key: value.detach().clone()
        for key, value in values.items()
        if isinstance(value, Tensor)
    }


def _changed_tensor_count(
    before: Mapping[str, Tensor], after: Mapping[str, Tensor]
) -> int:
    if set(before) != set(after):
        _fail("TENSOR_MAPPING_KEYS_CHANGED")
    return sum(
        int(
            before[key].shape != after[key].shape
            or before[key].dtype != after[key].dtype
            or not torch.equal(before[key], after[key])
        )
        for key in before
    )


def _as_long(values: Sequence[int], *, device: torch.device) -> Tensor:
    return torch.tensor(tuple(values), dtype=torch.long, device=device)


def _as_bool(values: Sequence[bool], *, device: torch.device) -> Tensor:
    return torch.tensor(tuple(values), dtype=torch.bool, device=device)


def _assemble_supervision_v1(
    structural: FFQRealStructureMicrobatchAlignmentV1,
    *,
    device: torch.device,
) -> CovapieCurrent11TrainingSupervisionTensorsV1:
    batch_size = len(structural.sample_identities)
    ligand_count = int(structural.model_input_batch["lig_coords"].shape[0])
    pocket_count = int(structural.model_input_batch["pocket_coords"].shape[0])
    ligand_counts = tuple(
        right - left
        for left, right in zip(
            structural.ligand_node_offsets,
            structural.ligand_node_offsets[1:],
        )
    )
    pocket_counts = tuple(
        right - left
        for left, right in zip(
            structural.pocket_node_offsets,
            structural.pocket_node_offsets[1:],
        )
    )
    if structural.sample_identities != _EXPECTED_SAMPLE_IDENTITIES_V1:
        _fail("EXACT_FFQ_SAMPLE_ORDER_REQUIRED")
    if not bool((structural.canonical_task_ids == 0).all().item()):
        _fail(TASK_NOT_SUPPORTED_BY_FFQ_SUPERVISED_FORWARD_V1)
    if bool(structural.sample_training_admitted.any().item()):
        _fail("FFQ_SAMPLE_ADMISSION_MUST_REMAIN_FALSE")
    if structural.human_training_exclusion_preserved.tolist() != [False, True]:
        _fail("FFQ_HUMAN_EXCLUSION_BOUNDARY_DRIFT")
    if (
        bool(structural.geometry_target_available.any().item())
        or bool(structural.warhead_type_target_available.any().item())
        or structural.structural_coordinates_centered is not True
        or structural.model_forward
        or structural.training_performed
    ):
        _fail("FFQ_AUTHORITY_BOUNDARY_DRIFT")
    if any(count != _EXPECTED_LIGAND_COUNT_V1 for count in ligand_counts):
        _fail("UNEXPECTED_FFQ_LIGAND_NODE_COUNT")
    membership = structural.target_residue_membership_mask[:, 0]
    target_members_by_sample = tuple(
        tuple(
            int(index)
            for index in torch.nonzero(
                membership[left:right], as_tuple=False
            ).flatten().tolist()
        )
        for left, right in zip(
            structural.pocket_node_offsets,
            structural.pocket_node_offsets[1:],
        )
    )
    if any(len(indices) != _EXPECTED_TARGET_RESIDUE_COUNT_V1 for indices in target_members_by_sample):
        _fail("UNEXPECTED_TARGET_RESIDUE_ATOM_COUNT")

    pair_specs = tuple(
        PairCandidateSampleSpec(
            batch_sample_index_0based=index,
            retained_ligand_count=ligand_counts[index],
            retained_pocket_count=pocket_counts[index],
            target_residue_pocket_local_indices=target_members_by_sample[index],
            positive_ligand_local_index=int(
                structural.ligand_reactive_local_indices[index].item()
            ),
            positive_pocket_local_index=int(
                structural.target_reactive_local_indices[index].item()
            ),
        )
        for index in range(batch_size)
    )
    pair_projection = build_pair_candidate_records_v1(
        pair_specs,
        structural.ligand_node_offsets,
        structural.pocket_node_offsets,
    )
    if any(
        count != _EXPECTED_LIGAND_COUNT_V1 * _EXPECTED_TARGET_RESIDUE_COUNT_V1
        for count in (
            right - left
            for left, right in zip(
                pair_projection.pair_candidate_offsets,
                pair_projection.pair_candidate_offsets[1:],
            )
        )
    ):
        _fail("UNEXPECTED_PAIR_CANDIDATE_COUNT")
    if not all(pair_projection.pair_positive_candidate_valid):
        _fail("PAIR_POSITIVE_MUST_BE_UNIQUE")

    ligand_mask = structural.model_input_batch["lig_mask"].to(device=device)
    ligand_coords = structural.model_input_batch["lig_coords"].to(device=device)
    target_flat_index = structural.target_reactive_flat_indices.to(device=device)
    reactive_ligand_flat_index = structural.ligand_reactive_flat_indices.to(
        device=device
    )
    pocket_coords = structural.model_input_batch["pocket_coords"].to(device=device)
    anchor_distance = torch.linalg.vector_norm(
        ligand_coords - pocket_coords[target_flat_index[ligand_mask]], dim=1
    ).unsqueeze(1)
    if not bool(torch.isfinite(anchor_distance).all().item()) or bool(
        (anchor_distance < 0).any().item()
    ):
        _fail("ANCHOR_DISTANCE_INVALID")

    float_dtype = ligand_coords.dtype
    pair_count = len(pair_projection.records)
    supervision = CovapieCurrent11TrainingSupervisionTensorsV1(
        sample_training_admitted=structural.sample_training_admitted.to(device=device),
        canonical_task_id=structural.canonical_task_ids.to(device=device),
        canonical_task_valid=torch.ones(batch_size, dtype=torch.bool, device=device),
        ligand_role_id=structural.ligand_role_id.to(device=device),
        ligand_role_valid=structural.ligand_role_valid.to(device=device),
        ligand_base_generation_mask=structural.ligand_generation_mask.to(device=device),
        ligand_base_fixed_mask=structural.ligand_fixed_mask.to(device=device),
        ligand_base_target_mask=structural.ligand_target_mask.to(device=device),
        ligand_base_context_mask=structural.ligand_context_mask.to(device=device),
        ligand_active_diffusion_loss_mask=torch.zeros(
            (ligand_count, 1), dtype=torch.bool, device=device
        ),
        ligand_minimal_seed_or_anchor_mask=torch.zeros(
            (ligand_count, 1), dtype=torch.bool, device=device
        ),
        ligand_minimal_seed_or_anchor_valid=torch.zeros(
            batch_size, dtype=torch.bool, device=device
        ),
        ligand_anchor_distance_angstrom=anchor_distance,
        ligand_anchor_distance_valid=torch.ones(
            (ligand_count, 1), dtype=torch.bool, device=device
        ),
        target_residue_membership_mask=structural.target_residue_membership_mask.to(
            device=device
        ),
        target_residue_reactive_atom_mask=structural.target_residue_reactive_atom_mask.to(
            device=device
        ),
        target_residue_reactive_atom_local_index=(
            structural.target_reactive_local_indices.to(device=device)
        ),
        target_residue_reactive_atom_flat_index=target_flat_index,
        target_residue_condition_valid=torch.ones(
            batch_size, dtype=torch.bool, device=device
        ),
        pair_candidate_offsets=_as_long(
            pair_projection.pair_candidate_offsets, device=device
        ),
        pair_candidate_batch_index=_as_long(
            pair_projection.pair_candidate_batch_index, device=device
        ),
        pair_candidate_ligand_local_index=_as_long(
            pair_projection.pair_candidate_ligand_local_index, device=device
        ),
        pair_candidate_ligand_flat_index=_as_long(
            pair_projection.pair_candidate_ligand_flat_index, device=device
        ),
        pair_candidate_residue_local_index=_as_long(
            pair_projection.pair_candidate_residue_local_index, device=device
        ),
        pair_candidate_pocket_flat_index=_as_long(
            pair_projection.pair_candidate_pocket_flat_index, device=device
        ),
        pair_candidate_is_positive=_as_bool(
            pair_projection.pair_candidate_is_positive, device=device
        ),
        pair_candidate_is_negative=_as_bool(
            pair_projection.pair_candidate_is_negative, device=device
        ),
        pair_positive_candidate_index=_as_long(
            pair_projection.pair_positive_candidate_index, device=device
        ),
        pair_positive_candidate_valid=_as_bool(
            pair_projection.pair_positive_candidate_valid, device=device
        ),
        pair_negative_count=_as_long(
            pair_projection.pair_negative_count, device=device
        ),
        pair_head_candidate_loss_mask=torch.zeros(
            pair_count, dtype=torch.bool, device=device
        ),
        pair_contrastive_sample_loss_mask=torch.zeros(
            batch_size, dtype=torch.bool, device=device
        ),
        observed_complex_pair_distance_angstrom=anchor_distance[
            reactive_ligand_flat_index
        ].reshape(batch_size, 1),
        observed_complex_pair_distance_valid=torch.ones(
            (batch_size, 1), dtype=torch.bool, device=device
        ),
        pre_post_geometry_target_angstrom=torch.full(
            (batch_size, 2), math.nan, dtype=float_dtype, device=device
        ),
        pre_post_geometry_component_valid_mask=torch.zeros(
            (batch_size, 2), dtype=torch.bool, device=device
        ),
        pre_post_geometry_component_loss_mask=torch.zeros(
            (batch_size, 2), dtype=torch.bool, device=device
        ),
    )
    return supervision


def _instantiate_augmented_model_v1(
    *,
    legacy_constructor: Mapping[str, object],
    repo_root: Path,
    state_root: Path,
    model_init_seed: int,
    device: torch.device,
) -> CovapieCurrent11TrainingLigandPocketDDPM:
    if (
        type(legacy_constructor) is not dict
        or legacy_constructor.get("schema_version")
        != "covapie_current11_validated_legacy_constructor_contract_v1"
        or legacy_constructor.get("node_histogram_source")
        != "exact_legacy_checkpoint_hyperparameters"
        or legacy_constructor.get("synthetic_node_histogram_used") is not False
    ):
        _fail("VALIDATED_LEGACY_CONSTRUCTOR_REQUIRED")
    constructor_config = copy.deepcopy(
        {
            key: legacy_constructor[key]
            for key in _MODEL_CONSTRUCTOR_FIELDS_V1
        }
    )
    egnn_params = constructor_config.get("egnn_params")
    if type(egnn_params) is not dict or egnn_params.get("device") != "cuda":
        _fail("LEGACY_CONSTRUCTOR_DEVICE_SOURCE_INVALID")
    egnn_params["device"] = "cpu"

    dataset_name = constructor_config.get("dataset")
    dataset_info = constants.dataset_params.get(dataset_name)
    expected_encoder = {
        token: index for index, token in enumerate(_EXACT10_TOKENS_V1)
    }
    if (
        dataset_name != "crossdock"
        or type(dataset_info) is not dict
        or dataset_info.get("atom_encoder") != expected_encoder
        or dataset_info.get("atom_decoder") != list(_EXACT10_TOKENS_V1)
        or constructor_config.get("pocket_representation") != "full-atom"
    ):
        _fail("CROSSDOCK_EXACT10_FULL_ATOM_DATASET_REQUIRED")

    constructor_kwargs = _constructor_kwargs(constructor_config)
    constructor_kwargs.update(
        {
            "target_residue_atom_conditioning": True,
            "covapie_current11_task2_runtime_enabled": True,
            "covapie_repository_root": str(repo_root),
            "covapie_state_root": str(state_root),
        }
    )
    with torch.random.fork_rng(devices=[], enabled=True):
        torch.manual_seed(model_init_seed)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            model = CovapieCurrent11TrainingLigandPocketDDPM(
                **constructor_kwargs,
            )
    model.to(device=device)
    model.eval()
    if (
        model.dataset_name != "crossdock"
        or model.batch_size != 16
        or model.mode != "pocket_conditioning"
        or model.pocket_representation != "full-atom"
        or model.atom_nf != 10
        or model.aa_nf != 10
        or model.virtual_nodes is not False
        or model.auxiliary_loss is not False
        or model.target_residue_atom_conditioning is not True
        or model.covapie_current11_task2_runtime_enabled is not True
        or len(model.state_dict()) != _EXPECTED_TARGET_MODEL_KEY_COUNT_V1
    ):
        _fail("AUGMENTED_MODEL_CONTRACT_MISMATCH")
    return model


def _verify_migration_summary_v1(summary: Mapping[str, object]) -> None:
    exact_counts = {
        "checkpoint_key_count": _EXPECTED_CHECKPOINT_KEY_COUNT_V1,
        "target_model_key_count": _EXPECTED_TARGET_MODEL_KEY_COUNT_V1,
        "shared_key_count": _EXPECTED_CHECKPOINT_KEY_COUNT_V1,
        "target_only_key_count": _EXPECTED_TARGET_ONLY_KEY_COUNT_V1,
        "checkpoint_only_key_count": 0,
        "shared_shape_mismatch_count": 0,
        "shared_checkpoint_tensor_equality_count": _EXPECTED_CHECKPOINT_KEY_COUNT_V1,
    }
    if any(summary.get(key) != value for key, value in exact_counts.items()):
        _fail("CHECKPOINT_MIGRATION_COUNT_MISMATCH")
    if summary.get("full_target_strict_load") is not True:
        _fail("CHECKPOINT_MIGRATION_NOT_STRICT")
    if summary.get("legacy_migration_policy_exact") is not True:
        _fail("CHECKPOINT_MIGRATION_POLICY_MISMATCH")
    if summary.get("migration_missing_keys") != ():
        _fail("CHECKPOINT_MIGRATION_MISSING_KEYS")
    if summary.get("migration_unexpected_keys") != ():
        _fail("CHECKPOINT_MIGRATION_UNEXPECTED_KEYS")
    if summary.get("target_residue_embedding_preserved_zero_after_migration") is not True:
        _fail("TARGET_RESIDUE_CONDITIONING_NOT_ZERO_INITIALIZED")
    if summary.get("auxiliary_zero_delta_initialization_preserved") is not True:
        _fail("AUXILIARY_HEAD_NOT_ZERO_INITIALIZED")


def _require_finite_tensor(value: Tensor, *, name: str) -> None:
    if not torch.is_floating_point(value) or not bool(torch.isfinite(value).all().item()):
        _fail(f"NONFINITE_{name}")


def _run_loss_free_forward_v1(
    *,
    model: CovapieCurrent11TrainingLigandPocketDDPM,
    structural: FFQRealStructureMicrobatchAlignmentV1,
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
    forward_noise_seed: int,
    diffusion_timestep_int: int,
    device: torch.device,
) -> tuple[
    CovapieCurrent11FunctionalDynamicsOutputV1,
    CovapieCurrent11ModelOutputV1,
    Tensor,
    Tensor,
    Tensor,
    Tensor,
    Tensor,
]:
    if torch.is_grad_enabled():
        _fail("GRADIENT_RECORDING_MUST_BE_DISABLED")
    if (
        model.training
        or model.ddpm.training
        or model.covapie_current11_auxiliary_model_v1.training
    ):
        _fail("EVAL_MODE_REQUIRED")
    batch = {
        key: value.detach().clone().to(device=device)
        if isinstance(value, Tensor)
        else copy.deepcopy(value)
        for key, value in structural.model_input_batch.items()
    }
    ligand, pocket = model.get_ligand_and_pocket(batch)
    ligand = {key: value.detach().clone() for key, value in ligand.items()}
    pocket = {key: value.detach().clone() for key, value in pocket.items()}
    model.ddpm.normalize(ligand, pocket)
    clean_ligand_xh = torch.cat((ligand["x"], ligand["one_hot"]), dim=1)
    clean_pocket_xh = torch.cat((pocket["x"], pocket["one_hot"]), dim=1)

    active_ligand_mask = supervision.ligand_base_generation_mask[:, 0]
    fixed_ligand_mask = supervision.ligand_base_fixed_mask[:, 0]
    if not torch.equal(active_ligand_mask, ~fixed_ligand_mask):
        _fail("TASK_A_GENERATION_FIXED_PARTITION_INVALID")
    batch_size = len(structural.sample_identities)
    fixed_count = torch.bincount(
        ligand["mask"][fixed_ligand_mask], minlength=batch_size
    )
    if not torch.equal(
        fixed_count,
        torch.full_like(fixed_count, _EXPECTED_FIXED_LIGAND_COUNT_V1),
    ):
        _fail("UNEXPECTED_FIXED_LIGAND_COUNT")
    reference = scatter_mean(
        clean_ligand_xh[fixed_ligand_mask, :3],
        ligand["mask"][fixed_ligand_mask],
        dim=0,
        dim_size=batch_size,
    )
    clean_ligand_xh = clean_ligand_xh.clone()
    clean_pocket_xh = clean_pocket_xh.clone()
    clean_ligand_xh[:, :3] -= reference[ligand["mask"]]
    clean_pocket_xh[:, :3] -= reference[pocket["mask"]]

    timestep_int = torch.full(
        (batch_size,),
        diffusion_timestep_int,
        dtype=torch.long,
        device=device,
    )
    timestep = timestep_int.to(dtype=clean_ligand_xh.dtype).reshape(-1, 1)
    timestep = timestep / float(model.ddpm.T)
    gamma = model.ddpm.inflate_batch_array(model.ddpm.gamma(timestep), ligand["x"])
    alpha = model.ddpm.alpha(gamma, clean_ligand_xh)
    sigma = model.ddpm.sigma(gamma, clean_ligand_xh)

    noise_generator = torch.Generator(device="cpu")
    noise_generator.manual_seed(forward_noise_seed)
    sampled_epsilon_ligand = torch.zeros_like(clean_ligand_xh)
    sampled_epsilon_ligand[active_ligand_mask] = torch.randn(
        (int(active_ligand_mask.sum().item()), clean_ligand_xh.shape[1]),
        dtype=clean_ligand_xh.dtype,
        device=device,
        generator=noise_generator,
    )
    generated_noised = (
        alpha[ligand["mask"]] * clean_ligand_xh
        + sigma[ligand["mask"]] * sampled_epsilon_ligand
    )
    noised_ligand_xh = torch.where(
        active_ligand_mask.unsqueeze(1), generated_noised, clean_ligand_xh
    )
    if not torch.equal(
        noised_ligand_xh[fixed_ligand_mask], clean_ligand_xh[fixed_ligand_mask]
    ):
        _fail("FIXED_LIGAND_NOISING_DRIFT")

    target_residue_condition_indicator = (
        supervision.target_residue_reactive_atom_mask[:, 0]
    )
    target_count = torch.bincount(
        pocket["mask"][target_residue_condition_indicator], minlength=batch_size
    )
    if target_count.tolist() != [1] * batch_size:
        _fail("TARGET_RESIDUE_CONDITION_INDICATOR_MISMATCH")

    role_mask_anchor_hidden_delta = (
        model.covapie_current11_auxiliary_model_v1.encode_role_mask_anchor_v1(
            supervision=supervision,
            ligand_batch_index=ligand["mask"],
        )
    )
    if not torch.equal(
        role_mask_anchor_hidden_delta,
        torch.zeros_like(role_mask_anchor_hidden_delta),
    ):
        _fail("ZERO_INITIAL_ROLE_ENCODING_DELTA_DRIFT")

    functional_output = run_covapie_current11_functional_dynamics_with_hidden_v1(
        ddpm=model.ddpm,
        xh_atoms=noised_ligand_xh,
        xh_residues=clean_pocket_xh,
        t=timestep,
        mask_atoms=ligand["mask"],
        mask_residues=pocket["mask"],
        ligand_coordinate_update_mask=active_ligand_mask.unsqueeze(1),
        role_mask_anchor_hidden_delta=role_mask_anchor_hidden_delta,
        pocket_target_residue_atom_condition_indicator=(
            target_residue_condition_indicator
        ),
    )
    expected_update_mask = torch.cat(
        (
            active_ligand_mask.unsqueeze(1).long(),
            torch.zeros(
                (clean_pocket_xh.shape[0], 1), dtype=torch.long, device=device
            ),
        ),
        dim=0,
    )
    if not torch.equal(functional_output.coordinate_update_mask, expected_update_mask):
        _fail("COORDINATE_UPDATE_MASK_MISMATCH")
    epsilon_prediction = functional_output.decoded_ligand_dynamics
    if not torch.equal(
        epsilon_prediction[fixed_ligand_mask, :3],
        torch.zeros_like(epsilon_prediction[fixed_ligand_mask, :3]),
    ):
        _fail("FIXED_LIGAND_COORDINATE_VELOCITY_NONZERO")
    if not torch.equal(
        functional_output.decoded_pocket_dynamics[:, :3],
        torch.zeros_like(functional_output.decoded_pocket_dynamics[:, :3]),
    ):
        _fail("POCKET_COORDINATE_VELOCITY_NONZERO")

    denoised_candidate = model.ddpm.xh_given_zt_and_epsilon(
        noised_ligand_xh,
        epsilon_prediction,
        gamma,
        ligand["mask"],
    )
    denoised_ligand_xh = torch.where(
        active_ligand_mask.unsqueeze(1), denoised_candidate, clean_ligand_xh
    )
    if not torch.equal(
        denoised_ligand_xh[fixed_ligand_mask], clean_ligand_xh[fixed_ligand_mask]
    ):
        _fail("FIXED_LIGAND_DENOISING_DRIFT")

    trace = _FFQAuxiliaryTraceV1(
        diffusion_epsilon_prediction_ligand=epsilon_prediction,
        denoised_ligand_xh=denoised_ligand_xh,
        diffusion_timestep_int=timestep_int,
        ligand_node_hidden=functional_output.ligand_node_hidden,
        pocket_node_hidden=functional_output.pocket_node_hidden,
        clean_centered_pocket_xh=clean_pocket_xh,
        coordinate_normalization=float(model.ddpm.norm_values[0]),
    )
    model_output = model.covapie_current11_auxiliary_model_v1(
        diffusion_trace=trace,
        supervision=supervision,
        role_mask_anchor_hidden_delta=role_mask_anchor_hidden_delta,
    )

    finite_tensors = {
        "FUNCTIONAL_DECODED_LIGAND_DYNAMICS": functional_output.decoded_ligand_dynamics,
        "FUNCTIONAL_DECODED_POCKET_DYNAMICS": functional_output.decoded_pocket_dynamics,
        "FUNCTIONAL_LIGAND_HIDDEN": functional_output.ligand_node_hidden,
        "FUNCTIONAL_POCKET_HIDDEN": functional_output.pocket_node_hidden,
        "DENOISED_LIGAND_XH": denoised_ligand_xh,
        "PAIR_LOGITS": model_output.pair_logits,
        "GEOMETRY_PREDICTION": model_output.pre_post_geometry_predictions_angstrom,
    }
    for name, value in finite_tensors.items():
        _require_finite_tensor(value, name=name)
    if model_output.pair_logits.shape != supervision.pair_candidate_is_positive.shape:
        _fail("PAIR_LOGIT_SHAPE_MISMATCH")
    if model_output.pre_post_geometry_predictions_angstrom.shape != (
        len(supervision.pair_candidate_is_positive),
        2,
    ):
        _fail("GEOMETRY_PREDICTION_SHAPE_MISMATCH")
    if not bool(model_output.target_pair_consistency.all().item()):
        _fail("TARGET_RESIDUE_CONDITION_INCONSISTENT")
    return (
        functional_output,
        model_output,
        clean_ligand_xh,
        clean_pocket_xh,
        noised_ligand_xh,
        sampled_epsilon_ligand,
        role_mask_anchor_hidden_delta,
    )


def _run_covapie_ffq_supervised_forward_adapter_v1(
    *,
    samples: Sequence[Mapping[str, object]],
    checkpoint_path: Path,
    repository_root: Path,
    state_root: Path,
    device: str,
    model_init_seed: int,
    forward_noise_seed: int,
    diffusion_timestep_int: int,
) -> FFQSupervisedForwardAdapterResultV1:
    if type(device) is not str or device != "cpu":
        _fail("CPU_DEVICE_REQUIRED")
    cpu_device = torch.device(device)
    model_init_seed = _require_seed(model_init_seed, name="MODEL_INIT_SEED")
    forward_noise_seed = _require_seed(forward_noise_seed, name="FORWARD_NOISE_SEED")
    if (
        isinstance(diffusion_timestep_int, bool)
        or not isinstance(diffusion_timestep_int, int)
        or diffusion_timestep_int <= 0
    ):
        _fail("INVALID_DIFFUSION_TIMESTEP_INT")
    checkpoint_path = _require_absolute_file(checkpoint_path, name="CHECKPOINT_PATH")
    repository_root = _require_absolute_directory(
        repository_root, name="REPOSITORY_ROOT"
    )
    state_root = _require_absolute_directory(state_root, name="STATE_ROOT")

    _precheck_task_a_only(samples)
    legacy = load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=checkpoint_path
    )
    legacy_constructor = legacy.get("legacy_constructor")
    if type(legacy_constructor) is not dict:
        _fail("VALIDATED_LEGACY_CONSTRUCTOR_MISSING")
    node_histogram = legacy_constructor.get("node_histogram")
    if not isinstance(node_histogram, list):
        _fail("CHECKPOINT_AUTHENTIC_NODE_HISTOGRAM_MISSING")

    structural = assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=samples
    )
    input_snapshot = _snapshot_tensor_mapping(structural.model_input_batch)
    supervision = _assemble_supervision_v1(structural, device=cpu_device)

    model = _instantiate_augmented_model_v1(
        legacy_constructor=legacy_constructor,
        repo_root=repository_root,
        state_root=state_root,
        model_init_seed=model_init_seed,
        device=cpu_device,
    )
    if legacy_constructor["egnn_params"]["device"] != "cuda":
        _fail("LEGACY_CONSTRUCTOR_MUTATED")
    if diffusion_timestep_int > model.ddpm.T:
        _fail("DIFFUSION_TIMESTEP_OUT_OF_RANGE")
    migration_summary_raw = migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
        model=model,
        checkpoint_state_dict=legacy["state_dict"],
    )
    _verify_migration_summary_v1(migration_summary_raw)
    target_embedding = (
        model.ddpm.dynamics.target_residue_atom_condition_embedding.detach()
    )
    target_residue_embedding_max_abs = float(target_embedding.abs().max().item())
    if target_residue_embedding_max_abs != 0.0:
        _fail("TARGET_RESIDUE_EMBEDDING_NOT_EXACT_ZERO")

    state_snapshot = {
        key: value.detach().clone() for key, value in model.state_dict().items()
    }
    if any(parameter.grad is not None for parameter in model.parameters()):
        _fail("PARAMETER_GRAD_PRESENT_BEFORE_FORWARD")
    with torch.no_grad():
        (
            functional_output,
            model_output,
            clean_ligand_xh,
            clean_pocket_xh,
            noised_ligand_xh,
            sampled_epsilon_ligand,
            role_mask_anchor_hidden_delta,
        ) = _run_loss_free_forward_v1(
            model=model,
            structural=structural,
            supervision=supervision,
            forward_noise_seed=forward_noise_seed,
            diffusion_timestep_int=diffusion_timestep_int,
            device=cpu_device,
        )

    state_after = {
        key: value.detach().clone() for key, value in model.state_dict().items()
    }
    state_tensor_changed_count = _changed_tensor_count(state_snapshot, state_after)
    input_tensor_changed_count = _changed_tensor_count(
        input_snapshot, _snapshot_tensor_mapping(structural.model_input_batch)
    )
    all_parameter_grads_none = all(
        parameter.grad is None for parameter in model.parameters()
    )
    if state_tensor_changed_count != 0:
        _fail("MODEL_STATE_MUTATED_DURING_FORWARD")
    if input_tensor_changed_count != 0:
        _fail("STRUCTURAL_INPUT_MUTATED_DURING_FORWARD")
    if not all_parameter_grads_none:
        _fail("PARAMETER_GRAD_CREATED_DURING_FORWARD")

    migration_summary = dict(migration_summary_raw)
    migration_summary.update(
        {
            "checkpoint_path": str(checkpoint_path),
            "checkpoint_sha256": legacy["checkpoint_sha256"],
            "checkpoint_size_bytes": legacy["checkpoint_size_bytes"],
            "node_histogram_source": "legacy_constructor.node_histogram",
            "node_histogram_shape": (
                len(node_histogram),
                len(node_histogram[0]) if node_histogram else 0,
            ),
            "model_constructor_source": "validated_legacy_checkpoint_constructor",
            "current_yaml_model_semantics_consumed": False,
            "legacy_constructor_node_histogram_shape": (
                len(node_histogram),
                len(node_histogram[0]) if node_histogram else 0,
            ),
            "runtime_device_override": ("egnn_params.device",),
            "constructor_dataset": "crossdock",
            "constructor_batch_size": 16,
            "crossdock_exact10_full_atom_mapping_verified": True,
            "crossdock_exact10_tokens": _EXACT10_TOKENS_V1,
            "model_init_seed": model_init_seed,
            "forward_noise_seed": forward_noise_seed,
            "diffusion_timestep_int": diffusion_timestep_int,
        }
    )
    structural_batch_summary = {
        "ligand_node_count_by_sample": tuple(
            right - left
            for left, right in zip(
                structural.ligand_node_offsets,
                structural.ligand_node_offsets[1:],
            )
        ),
        "pocket_node_count_by_sample": tuple(
            right - left
            for left, right in zip(
                structural.pocket_node_offsets,
                structural.pocket_node_offsets[1:],
            )
        ),
        "ligand_offsets": structural.ligand_node_offsets,
        "pocket_offsets": structural.pocket_node_offsets,
        "reactive_ligand_flat_index_by_sample": tuple(
            int(value) for value in structural.ligand_reactive_flat_indices.tolist()
        ),
        "reactive_pocket_flat_index_by_sample": tuple(
            int(value) for value in structural.target_reactive_flat_indices.tolist()
        ),
        "target_residue_atom_count_by_sample": tuple(
            int(
                structural.target_residue_membership_mask[left:right]
                .sum()
                .item()
            )
            for left, right in zip(
                structural.pocket_node_offsets,
                structural.pocket_node_offsets[1:],
            )
        ),
        "sample_admission": tuple(
            bool(value) for value in structural.sample_training_admitted.tolist()
        ),
        "exclusion_preserved": tuple(
            bool(value)
            for value in structural.human_training_exclusion_preserved.tolist()
        ),
    }
    return FFQTaskASupervisedForwardResultV1(
        sample_identities=structural.sample_identities,
        structural_alignment=structural,
        structural_batch_summary=structural_batch_summary,
        supervision=supervision,
        migration_summary=migration_summary,
        functional_dynamics_output=functional_output,
        model_output=model_output,
        clean_ligand_xh=clean_ligand_xh,
        clean_pocket_xh=clean_pocket_xh,
        noised_ligand_xh=noised_ligand_xh,
        sampled_epsilon_ligand=sampled_epsilon_ligand,
        timestep_int=torch.full(
            (len(structural.sample_identities),),
            diffusion_timestep_int,
            dtype=torch.long,
            device=cpu_device,
        ),
        role_mask_anchor_hidden_delta=role_mask_anchor_hidden_delta,
        role_mask_anchor_hidden_delta_exact_zero=True,
        target_residue_embedding_max_abs=target_residue_embedding_max_abs,
        state_tensor_changed_count=state_tensor_changed_count,
        input_tensor_changed_count=input_tensor_changed_count,
        all_parameter_grads_none=all_parameter_grads_none,
        model_eval_mode_verified=True,
        ddpm_eval_mode_verified=True,
        auxiliary_eval_mode_verified=True,
        gradient_recording_disabled=True,
        joint_objective_loss_executed=False,
        base_diffusion_loss_executed=False,
        pair_loss_executed=False,
        geometry_loss_executed=False,
        contrastive_loss_executed=False,
        current11_runtime_executed=False,
        training_performed=False,
        backward_performed=False,
        optimizer_step_performed=False,
        parameter_update_performed=False,
        raw_pair_prediction_available=True,
        raw_geometry_prediction_available=True,
        geometry_authority_available=False,
    )


def run_covapie_ffq_task_a_supervised_forward_v1(
    *,
    samples: Sequence[Mapping[str, object]],
    checkpoint_path: Path,
    repository_root: Path,
    state_root: Path,
    device: str = "cpu",
    model_init_seed: int = MODEL_INIT_SEED_V1,
    forward_noise_seed: int = FORWARD_NOISE_SEED_V1,
    timestep_int: int = TIMESTEP_INT_V1,
) -> FFQTaskASupervisedForwardResultV1:
    """Run the bounded Task-A FFQ supervised forward on CPU, without losses."""

    try:
        return _run_covapie_ffq_supervised_forward_adapter_v1(
            samples=samples,
            checkpoint_path=checkpoint_path,
            repository_root=repository_root,
            state_root=state_root,
            device=device,
            model_init_seed=model_init_seed,
            forward_noise_seed=forward_noise_seed,
            diffusion_timestep_int=timestep_int,
        )
    except FFQSupervisedForwardAdapterError:
        raise
    except Exception as error:
        raise FFQSupervisedForwardAdapterError(
            f"{ERROR_PREFIX_V1}:INVARIANT_VIOLATION:{type(error).__name__}:{error}"
        ) from error


# Keep the module-name API as a thin alias; both names execute the same Task-A-only path.
run_covapie_ffq_supervised_forward_adapter_v1 = (
    run_covapie_ffq_task_a_supervised_forward_v1
)


__all__ = [
    "DIFFUSION_TIMESTEP_INT_V1",
    "ERROR_PREFIX_V1",
    "FFQSupervisedForwardAdapterError",
    "FFQSupervisedForwardAdapterResultV1",
    "FFQTaskASupervisedForwardResultV1",
    "FORWARD_NOISE_SEED_V1",
    "MODEL_INIT_SEED_V1",
    "TASK_NOT_SUPPORTED_BY_FFQ_SUPERVISED_FORWARD_V1",
    "TIMESTEP_INT_V1",
    "run_covapie_ffq_task_a_supervised_forward_v1",
    "run_covapie_ffq_supervised_forward_adapter_v1",
]
