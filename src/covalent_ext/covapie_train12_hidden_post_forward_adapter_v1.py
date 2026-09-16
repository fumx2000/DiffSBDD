"""Opt-in train12 adapter for the Current11 hidden-POST forward route.

The adapter only organizes published owners.  It consumes one source-bound
train12 CPU carrier with its explicitly bound prepared context, preserves the
carrier's supervision object, and adds no model, loss, optimizer, checkpoint,
or training mathematics.
"""

from __future__ import annotations

from dataclasses import fields
import hashlib
from pathlib import Path
import stat
from typing import NoReturn

import torch

from covalent_ext.biopython_compat import (
    patch_biopython_polypeptide_three_to_one,
)


# This published compatibility entry point must run before the real model owner
# is imported.
BIOPYTHON_COMPAT_APPLIED_V1 = patch_biopython_polypeptide_three_to_one()

from covalent_ext import (  # noqa: E402
    covapie_train12_cpu_batch_composer_v1 as composer_owner,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (  # noqa: E402
    compute_covapie_current11_training_losses_v1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (  # noqa: E402
    CovapieCurrent11TrainingForwardOutputV1,
    CovapieCurrent11TrainingLigandPocketDDPM,
    run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1,
)


__all__ = (
    "COVAPIE_TRAIN12_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1",
    "TRAIN12_HIDDEN_POST_LOSS_PURPOSE_V1",
    "DIRECT_BOUND_SOURCE_SHA256_V1",
    "BIOPYTHON_COMPAT_APPLIED_V1",
    "verify_covapie_train12_hidden_post_forward_adapter_sources_v1",
    "CovapieTrain12HiddenPostForwardLigandPocketDDPMV1",
)


COVAPIE_TRAIN12_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1 = (
    "COVAPIE_TRAIN12_HIDDEN_POST_FORWARD_ADAPTER_V1_ERROR"
)
TRAIN12_HIDDEN_POST_LOSS_PURPOSE_V1 = (
    "independent_hidden_post_distance_v1"
)

# Fixed published source identities.  The train12 validator separately checks
# its complete train10/READY2 authority chain and both mutation seals per call.
DIRECT_BOUND_SOURCE_SHA256_V1 = (
    (
        "src/covalent_ext/biopython_compat.py",
        "629cb43f889cff04e1aaf4ffa228c4e4c158f1b07845ed0ac9456a40645dc975",
    ),
    (
        "src/covalent_ext/covapie_train12_cpu_batch_composer_v1.py",
        "4f67c695f50ca9d6e8cec30fd6a163db10fb05fd44647b2a189b9aeda6719722",
    ),
    (
        "src/covalent_ext/covapie_current11_training_lightning_module_v1.py",
        "a61041ef44e79c0622645965461bf4cc0275e5f3bec9a756fcf7d36a4c9c391b",
    ),
    (
        "src/covalent_ext/covapie_current11_task2_lightning_module_v1.py",
        "38ed7a2b272520720935021782547f01d1d2cf36b636ce7319e6751fb54dcd98",
    ),
    (
        "src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py",
        "bb797fdb0c96ce669a348a3ddf3975771398263cdfa2a22f3d9c55b0011271cd",
    ),
    (
        "lightning_modules.py",
        "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983",
    ),
)

# External candidates locate published sources through the installed composer,
# never through the candidate file's parents.
_PUBLISHED_REPOSITORY_ROOT = Path(composer_owner.__file__).resolve().parents[2]
_BATCH_SIZE_V1 = 12


def _fail(reason: str) -> NoReturn:
    raise ValueError(
        f"{COVAPIE_TRAIN12_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:{reason}"
    )


def _safe_sha256(path: Path) -> str:
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
            _fail("DIRECT_BOUND_SOURCE_NOT_REGULAR")
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except ValueError:
        raise
    except OSError as error:
        raise ValueError(
            f"{COVAPIE_TRAIN12_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:"
            "DIRECT_BOUND_SOURCE_UNREADABLE"
        ) from error


def _published_repository_root_v1(repository_root: object) -> Path:
    if (
        not isinstance(repository_root, Path)
        or not repository_root.is_absolute()
    ):
        _fail("REPOSITORY_ROOT_INVALID")
    try:
        resolved = repository_root.resolve(strict=True)
    except OSError as error:
        raise ValueError(
            f"{COVAPIE_TRAIN12_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:"
            "REPOSITORY_ROOT_INVALID"
        ) from error
    if (
        resolved != repository_root
        or not resolved.is_dir()
        or resolved != _PUBLISHED_REPOSITORY_ROOT
    ):
        _fail("REPOSITORY_ROOT_NOT_PUBLISHED_COMPOSER_ROOT")
    return resolved


def verify_covapie_train12_hidden_post_forward_adapter_sources_v1(
    *, repository_root: object = None
) -> tuple[tuple[str, str], ...]:
    """Fail closed on the fixed composer/model/loss/transport source set."""

    root = _published_repository_root_v1(
        _PUBLISHED_REPOSITORY_ROOT
        if repository_root is None
        else repository_root
    )
    observed = []
    for relative, expected in DIRECT_BOUND_SOURCE_SHA256_V1:
        actual = _safe_sha256(root / relative)
        if actual != expected:
            _fail("DIRECT_BOUND_SOURCE_SHA256_MISMATCH:" + relative)
        observed.append((relative, actual))
    return tuple(observed)


def _all_carrier_tensors_v1(
    carrier: composer_owner.CovapieTrain12CpuEpochBatchV1,
) -> tuple[torch.Tensor, ...]:
    supervision = carrier.supervision
    tensors = tuple(
        value
        for value in carrier.model_input_batch.values()
        if isinstance(value, torch.Tensor)
    )
    try:
        supervision_tensors = tuple(
            getattr(supervision, field.name) for field in fields(supervision)
        )
    except (TypeError, AttributeError) as error:
        raise ValueError(
            f"{COVAPIE_TRAIN12_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:"
            "CARRIER_SUPERVISION_TYPE_INVALID"
        ) from error
    if not supervision_tensors or any(
        not isinstance(value, torch.Tensor) for value in supervision_tensors
    ):
        _fail("CARRIER_SUPERVISION_TYPE_INVALID")
    return tensors + supervision_tensors


def _validated_prepared_context_v1(
    prepared: object,
) -> composer_owner.CovapieTrain12CpuBatchPreparedV1:
    if type(prepared) is not composer_owner.CovapieTrain12CpuBatchPreparedV1:
        _fail("PREPARED_CONTEXT_TYPE_INVALID")
    try:
        root = _published_repository_root_v1(prepared._repo)
        verify_covapie_train12_hidden_post_forward_adapter_sources_v1(
            repository_root=root
        )
        valid = composer_owner._validate_prepared(prepared)
    except ValueError as error:
        if str(error).startswith(
            COVAPIE_TRAIN12_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1
        ):
            raise
        raise ValueError(
            f"{COVAPIE_TRAIN12_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:"
            "PUBLISHED_PREPARED_VALIDATOR_REJECTED"
        ) from error
    if valid is not prepared:
        _fail("PREPARED_CONTEXT_IDENTITY_INVALID")
    return valid


def _bound_prepared_context_v1(
    owner: object,
) -> composer_owner.CovapieTrain12CpuBatchPreparedV1:
    prepared = getattr(owner, "_covapie_train12_bound_prepared_v1", None)
    if prepared is None:
        _fail("PREPARED_CONTEXT_REQUIRED")
    if (
        id(prepared)
        != getattr(
            owner, "_covapie_train12_bound_prepared_identity_v1", None
        )
        or getattr(prepared, "_seal", None)
        != getattr(owner, "_covapie_train12_bound_prepared_seal_v1", None)
    ):
        _fail("PREPARED_CONTEXT_IDENTITY_OR_SEAL_CHANGED")
    valid = _validated_prepared_context_v1(prepared)
    if (
        valid is not prepared
        or prepared._repo
        != getattr(owner, "_covapie_train12_bound_repository_root_v1", None)
    ):
        _fail("PREPARED_CONTEXT_IDENTITY_OR_ROOT_CHANGED")
    return valid


def _validate_train12_carrier_for_forward_v1(
    carrier: object,
    *,
    prepared: composer_owner.CovapieTrain12CpuBatchPreparedV1,
    training: object,
    current_epoch: object,
    task_schedule_seed: object,
) -> composer_owner.CovapieTrain12CpuEpochBatchV1:
    if type(carrier) is not composer_owner.CovapieTrain12CpuEpochBatchV1:
        _fail("CARRIER_BOUNDARY_TYPE_INVALID")
    if training is not True:
        _fail("LIFECYCLE_TRAINING_MODE_REQUIRED")
    if (
        type(current_epoch) is not int
        or not 0 <= current_epoch <= 4
        or current_epoch != carrier.epoch
    ):
        _fail("LIFECYCLE_EPOCH_MISMATCH")
    if (
        type(task_schedule_seed) is not int
        or task_schedule_seed != 0
        or task_schedule_seed != carrier.task_schedule_seed
    ):
        _fail("LIFECYCLE_TASK_SCHEDULE_SEED_MISMATCH")
    try:
        composer_owner.validate_covapie_train12_cpu_epoch_batch_v1(
            carrier, prepared
        )
    except ValueError as error:
        raise ValueError(
            f"{COVAPIE_TRAIN12_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:"
            "PUBLISHED_COMPOSER_VALIDATOR_REJECTED"
        ) from error
    tensors = _all_carrier_tensors_v1(carrier)
    if not tensors or any(value.device.type != "cpu" for value in tensors):
        _fail("CARRIER_BOUNDARY_CPU_ONLY")
    return carrier


def _validated_transport_side_v1(
    *,
    transported: object,
    model_input: dict[str, object],
    source_fields: tuple[str, str, str, str],
) -> dict[str, torch.Tensor]:
    if type(transported) is not dict:
        _fail("TRANSPORT_BOUNDARY_DICTIONARY_REQUIRED")
    names = ("x", "one_hot", "size", "mask")
    if any(not isinstance(transported.get(name), torch.Tensor) for name in names):
        _fail("TRANSPORT_BOUNDARY_TENSOR_FIELDS_INVALID")
    result = {name: transported[name] for name in names}
    x, one_hot, size, mask = (result[name] for name in names)
    if (
        x.device.type != "cpu"
        or one_hot.device.type != "cpu"
        or size.device.type != "cpu"
        or mask.device.type != "cpu"
        or x.dtype != torch.float32
        or one_hot.dtype != torch.float32
        or size.dtype != torch.long
        or mask.dtype != torch.long
        or x.ndim != 2
        or x.shape[1] != 3
        or one_hot.ndim != 2
        or len(one_hot) != len(x)
        or size.shape != (_BATCH_SIZE_V1,)
        or mask.ndim != 1
        or len(mask) != len(x)
        or bool((size <= 0).any().item())
        or bool(((mask < 0) | (mask >= _BATCH_SIZE_V1)).any().item())
        or int(size.sum().item()) != len(x)
        or not torch.equal(
            torch.bincount(mask, minlength=_BATCH_SIZE_V1), size
        )
    ):
        _fail("TRANSPORT_BOUNDARY_SHAPE_SIZE_OR_MEMBERSHIP_MISMATCH")
    for name, source_name in zip(names, source_fields):
        source = model_input.get(source_name)
        if not isinstance(source, torch.Tensor):
            _fail("TRANSPORT_BOUNDARY_SOURCE_TENSOR_INVALID")
        expected = source.to(device=torch.device("cpu"), dtype=result[name].dtype)
        if not torch.equal(result[name], expected):
            _fail("TRANSPORT_BOUNDARY_VALUE_MISMATCH:" + name)
    return transported


def _validate_transport_v1(
    carrier: composer_owner.CovapieTrain12CpuEpochBatchV1,
    *,
    ligand: object,
    pocket: object,
) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
    valid_ligand = _validated_transport_side_v1(
        transported=ligand,
        model_input=carrier.model_input_batch,
        source_fields=(
            "lig_coords",
            "lig_one_hot",
            "num_lig_atoms",
            "lig_mask",
        ),
    )
    valid_pocket = _validated_transport_side_v1(
        transported=pocket,
        model_input=carrier.model_input_batch,
        source_fields=(
            "pocket_coords",
            "pocket_one_hot",
            "num_pocket_nodes",
            "pocket_mask",
        ),
    )
    return valid_ligand, valid_pocket


class CovapieTrain12HiddenPostForwardLigandPocketDDPMV1(
    CovapieCurrent11TrainingLigandPocketDDPM
):
    """Explicitly enabled current-owner forward route for formal train12."""

    def __init__(
        self,
        *args: object,
        covapie_train12_hidden_post_forward_enabled: bool = False,
        **kwargs: object,
    ) -> None:
        if covapie_train12_hidden_post_forward_enabled is not True:
            _fail("EXPLICIT_OPT_IN_REQUIRED")
        verify_covapie_train12_hidden_post_forward_adapter_sources_v1()
        super().__init__(*args, **kwargs)
        self.covapie_train12_hidden_post_forward_enabled = True
        self._covapie_train12_bound_prepared_v1 = None
        self._covapie_train12_bound_prepared_identity_v1 = None
        self._covapie_train12_bound_prepared_seal_v1 = None
        self._covapie_train12_bound_repository_root_v1 = None

    def bind_covapie_train12_prepared_context_v1(
        self, prepared: object
    ) -> None:
        """Validate and bind exactly one published train12 prepared context."""

        if (
            getattr(
                self, "covapie_train12_hidden_post_forward_enabled", None
            )
            is not True
        ):
            _fail("EXPLICIT_OPT_IN_REQUIRED")
        if getattr(self, "_covapie_train12_bound_prepared_v1", None) is not None:
            _fail("PREPARED_CONTEXT_ALREADY_BOUND")
        valid = _validated_prepared_context_v1(prepared)
        self._covapie_train12_bound_prepared_v1 = valid
        self._covapie_train12_bound_prepared_identity_v1 = id(valid)
        self._covapie_train12_bound_prepared_seal_v1 = valid._seal
        self._covapie_train12_bound_repository_root_v1 = valid._repo

    def forward(self, data: object) -> CovapieCurrent11TrainingForwardOutputV1:
        if (
            getattr(
                self, "covapie_train12_hidden_post_forward_enabled", None
            )
            is not True
        ):
            _fail("EXPLICIT_OPT_IN_REQUIRED")
        if getattr(self, "device", None) != torch.device("cpu"):
            _fail("LIFECYCLE_CPU_DEVICE_REQUIRED")
        prepared = _bound_prepared_context_v1(self)
        carrier = _validate_train12_carrier_for_forward_v1(
            data,
            prepared=prepared,
            training=getattr(self, "training", None),
            current_epoch=getattr(self, "current_epoch", None),
            task_schedule_seed=getattr(
                self, "covapie_current11_task_schedule_seed", None
            ),
        )
        transported_ligand, transported_pocket = self.get_ligand_and_pocket(
            carrier.model_input_batch
        )
        ligand, pocket = _validate_transport_v1(
            carrier,
            ligand=transported_ligand,
            pocket=transported_pocket,
        )
        supervision = carrier.supervision
        indicator = supervision.target_residue_reactive_atom_mask
        if (
            indicator.dtype != torch.bool
            or indicator.device.type != "cpu"
            or indicator.shape != (len(pocket["x"]), 1)
        ):
            _fail("TARGET_RESIDUE_INDICATOR_INVALID")
        role_delta = (
            self.covapie_current11_auxiliary_model_v1.encode_role_mask_anchor_v1(
                supervision=supervision,
                ligand_batch_index=ligand["mask"],
            )
        )
        trace = run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
            ddpm=self.ddpm,
            ligand=ligand,
            pocket=pocket,
            supervision=supervision,
            role_mask_anchor_hidden_delta=role_delta,
            pocket_target_residue_atom_condition_indicator=indicator[:, 0],
        )
        model_output = self.covapie_current11_auxiliary_model_v1(
            diffusion_trace=trace,
            supervision=supervision,
            role_mask_anchor_hidden_delta=role_delta,
        )
        try:
            loss_output = compute_covapie_current11_training_losses_v1(
                model_output=model_output,
                supervision=supervision,
                diffusion_trace=trace,
                loss_weights=self.covapie_current11_loss_weights,
                pair_contrastive_temperature=(
                    self.covapie_current11_pair_contrastive_temperature
                ),
                geometry_smooth_l1_beta=1.0,
                post_geometry_loss_purpose=TRAIN12_HIDDEN_POST_LOSS_PURPOSE_V1,
                ligand_batch_index=ligand["mask"],
                pocket_batch_index=pocket["mask"],
            )
        except ValueError as error:
            raise ValueError(
                f"{COVAPIE_TRAIN12_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:"
                "PRODUCTION_LOSS_GATE_REJECTED"
            ) from error
        return CovapieCurrent11TrainingForwardOutputV1(
            model_output=model_output,
            loss_output=loss_output,
            supervision=supervision,
            diffusion_trace=trace,
        )
