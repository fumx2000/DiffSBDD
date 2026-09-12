"""Opt-in Batch001 train5 adapter for the Current11 hidden-POST loss route.

The adapter only organizes published owners.  It consumes the current formal
train5 carrier directly and does not tensorize a second data protocol, alter
supervision masks, or implement model/loss mathematics.
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


# The compatibility entry point must run before importing the real model owner.
BIOPYTHON_COMPAT_APPLIED_V1 = patch_biopython_polypeptide_three_to_one()

from covalent_ext import (  # noqa: E402
    covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as activation_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_batch001_feature_post_use_preflight_v1 as preflight_owner,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (  # noqa: E402
    compute_covapie_current11_training_losses_v1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (  # noqa: E402
    CovapieCurrent11TrainingForwardOutputV1,
    CovapieCurrent11TrainingLigandPocketDDPM,
    run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (  # noqa: E402
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


__all__ = (
    "COVAPIE_BATCH001_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1",
    "BATCH001_HIDDEN_POST_LOSS_PURPOSE_V1",
    "DIRECT_BOUND_SOURCE_SHA256_V1",
    "BIOPYTHON_COMPAT_APPLIED_V1",
    "verify_covapie_batch001_hidden_post_forward_adapter_sources_v1",
    "CovapieBatch001HiddenPostForwardLigandPocketDDPMV1",
)


COVAPIE_BATCH001_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1 = (
    "COVAPIE_BATCH001_HIDDEN_POST_FORWARD_ADAPTER_V1_ERROR"
)
BATCH001_HIDDEN_POST_LOSS_PURPOSE_V1 = (
    "independent_hidden_post_distance_v1"
)

# The published preflight binds the activation, tensorizer, Current11 model/loss
# owners, and their predecessor boundary.  These two direct imports are outside
# that inventory and are therefore pinned explicitly here.
DIRECT_BOUND_SOURCE_SHA256_V1 = (
    (
        "src/covalent_ext/biopython_compat.py",
        "629cb43f889cff04e1aaf4ffa228c4e4c158f1b07845ed0ac9456a40645dc975",
    ),
    (
        "src/covalent_ext/covapie_batch001_feature_post_use_preflight_v1.py",
        "9e91e119a63867e7eda4ac76e0e8080ec774b2ee66e6b2ed8b4f4d9b07a6bf7c",
    ),
)

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _fail(reason: str) -> NoReturn:
    raise ValueError(
        f"{COVAPIE_BATCH001_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:{reason}"
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
            f"{COVAPIE_BATCH001_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:"
            "DIRECT_BOUND_SOURCE_UNREADABLE"
        ) from error


def verify_covapie_batch001_hidden_post_forward_adapter_sources_v1(
    *, repository_root: object = None
) -> tuple[tuple[str, str], ...]:
    """Fail closed on the published preflight and extra direct source pins."""

    root = _DEFAULT_REPOSITORY_ROOT if repository_root is None else repository_root
    if (
        not isinstance(root, Path)
        or not root.is_absolute()
        or not root.is_dir()
    ):
        _fail("REPOSITORY_ROOT_INVALID")
    observed = []
    for relative, expected in DIRECT_BOUND_SOURCE_SHA256_V1:
        actual = _safe_sha256(root / relative)
        if actual != expected:
            _fail("DIRECT_BOUND_SOURCE_SHA256_MISMATCH:" + relative)
        observed.append((relative, actual))
    try:
        preflight_owner.verify_covapie_batch001_feature_post_use_preflight_sources_v1(
            repository_root=root
        )
    except ValueError as error:
        raise ValueError(
            f"{COVAPIE_BATCH001_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:"
            "PUBLISHED_PREFLIGHT_SOURCE_BINDING_REJECTED"
        ) from error
    return tuple(observed)


def _all_carrier_tensors(
    carrier: activation_owner.CovapieBatch001ModelUsableSplitBatchV1,
) -> tuple[torch.Tensor, ...]:
    tensors = tuple(
        value
        for value in carrier.model_input_batch.values()
        if isinstance(value, torch.Tensor)
    )
    supervision = carrier.supervision
    if not isinstance(supervision, CovapieCurrent11TrainingSupervisionTensorsV1):
        _fail("CARRIER_BOUNDARY_SUPERVISION_TYPE_INVALID")
    return tensors + tuple(
        getattr(supervision, field.name)
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    )


def _validate_train5_carrier_for_forward_v1(
    carrier: object,
    *,
    training: object,
    current_epoch: object,
    task_schedule_seed: object,
) -> activation_owner.CovapieBatch001ModelUsableSplitBatchV1:
    if type(carrier) is not activation_owner.CovapieBatch001ModelUsableSplitBatchV1:
        _fail("CARRIER_BOUNDARY_TYPE_INVALID")
    if training is not True:
        _fail("LIFECYCLE_TRAINING_MODE_REQUIRED")
    if carrier.formal_split != "train":
        _fail("LIFECYCLE_FORMAL_TRAIN_ONLY")
    if type(current_epoch) is not int or carrier.epoch != current_epoch:
        _fail("LIFECYCLE_EPOCH_MISMATCH")
    if (
        type(task_schedule_seed) is not int
        or carrier.task_schedule_seed != task_schedule_seed
    ):
        _fail("LIFECYCLE_TASK_SCHEDULE_SEED_MISMATCH")
    try:
        activation_owner.validate_covapie_batch001_training_activation_population_v1(
            sample_identities=carrier.sample_identities,
            formal_splits=(carrier.formal_split,) * len(carrier.sample_identities),
        )
    except ValueError as error:
        raise ValueError(
            f"{COVAPIE_BATCH001_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:"
            "CARRIER_BOUNDARY_EXACT_TRAIN5_IDENTITY_REJECTED"
        ) from error
    if (
        carrier.sample_training_admitted != (True,) * 5
        or carrier.model_training_activation_authorized != (True,) * 5
        or carrier.optimizer_population_eligible != (True,) * 5
        or carrier.training_scheduler_eligible != (True,) * 5
        or carrier.formal_validation_population_member != (False,) * 5
        or carrier.formal_test_population_member != (False,) * 5
    ):
        _fail("CARRIER_BOUNDARY_ACTIVATION_INVALID")
    try:
        preflight_owner.audit_covapie_batch001_feature_post_use_carrier_v1(carrier)
    except ValueError as error:
        raise ValueError(
            f"{COVAPIE_BATCH001_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:"
            "CARRIER_BOUNDARY_PUBLISHED_PREFLIGHT_REJECTED"
        ) from error
    tensors = _all_carrier_tensors(carrier)
    if not tensors or any(tensor.device.type != "cpu" for tensor in tensors):
        _fail("CARRIER_BOUNDARY_CPU_ONLY")
    return carrier


def _validate_transport_membership_v1(
    carrier: activation_owner.CovapieBatch001ModelUsableSplitBatchV1,
    *,
    ligand: object,
    pocket: object,
) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
    if type(ligand) is not dict or type(pocket) is not dict:
        _fail("TRANSPORT_BOUNDARY_DICTIONARY_REQUIRED")
    required = ("x", "one_hot", "size", "mask")
    if any(not isinstance(ligand.get(name), torch.Tensor) for name in required) or any(
        not isinstance(pocket.get(name), torch.Tensor) for name in required
    ):
        _fail("TRANSPORT_BOUNDARY_TENSOR_FIELDS_INVALID")
    ligand_tensors = {name: ligand[name] for name in required}
    pocket_tensors = {name: pocket[name] for name in required}
    ligand_mask = ligand_tensors["mask"]
    pocket_mask = pocket_tensors["mask"]
    source_ligand_mask = carrier.model_input_batch.get("lig_mask")
    source_pocket_mask = carrier.model_input_batch.get("pocket_mask")
    if (
        any(value.device.type != "cpu" for value in ligand_tensors.values())
        or any(value.device.type != "cpu" for value in pocket_tensors.values())
        or ligand_mask.dtype != torch.long
        or pocket_mask.dtype != torch.long
        or ligand_mask.ndim != 1
        or pocket_mask.ndim != 1
        or len(ligand_tensors["x"]) != len(ligand_mask)
        or len(pocket_tensors["x"]) != len(pocket_mask)
        or not isinstance(source_ligand_mask, torch.Tensor)
        or not isinstance(source_pocket_mask, torch.Tensor)
        or not torch.equal(ligand_mask, source_ligand_mask)
        or not torch.equal(pocket_mask, source_pocket_mask)
    ):
        _fail("TRANSPORT_BOUNDARY_MEMBERSHIP_MISMATCH")
    return ligand, pocket


class CovapieBatch001HiddenPostForwardLigandPocketDDPMV1(
    CovapieCurrent11TrainingLigandPocketDDPM
):
    """Explicitly enabled current-owner forward route for formal train5 only."""

    def __init__(
        self,
        *args: object,
        covapie_batch001_hidden_post_forward_enabled: bool = False,
        **kwargs: object,
    ) -> None:
        if covapie_batch001_hidden_post_forward_enabled is not True:
            _fail("EXPLICIT_OPT_IN_REQUIRED")
        verify_covapie_batch001_hidden_post_forward_adapter_sources_v1()
        super().__init__(*args, **kwargs)
        self.covapie_batch001_hidden_post_forward_enabled = True

    def forward(
        self, data: object
    ) -> CovapieCurrent11TrainingForwardOutputV1:
        verify_covapie_batch001_hidden_post_forward_adapter_sources_v1()
        if getattr(self, "covapie_batch001_hidden_post_forward_enabled", None) is not True:
            _fail("EXPLICIT_OPT_IN_REQUIRED")
        if getattr(self, "device", None) != torch.device("cpu"):
            _fail("LIFECYCLE_CPU_DEVICE_REQUIRED")
        carrier = _validate_train5_carrier_for_forward_v1(
            data,
            training=getattr(self, "training", None),
            current_epoch=getattr(self, "current_epoch", None),
            task_schedule_seed=getattr(
                self, "covapie_current11_task_schedule_seed", None
            ),
        )
        transported_ligand, transported_pocket = self.get_ligand_and_pocket(
            carrier.model_input_batch
        )
        ligand, pocket = _validate_transport_membership_v1(
            carrier,
            ligand=transported_ligand,
            pocket=transported_pocket,
        )
        supervision = carrier.supervision
        indicator = supervision.target_residue_reactive_atom_mask
        if indicator.dtype != torch.bool or indicator.shape != (len(pocket["x"]), 1):
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
                post_geometry_loss_purpose=BATCH001_HIDDEN_POST_LOSS_PURPOSE_V1,
                ligand_batch_index=ligand["mask"],
                pocket_batch_index=pocket["mask"],
            )
        except ValueError as error:
            raise ValueError(
                f"{COVAPIE_BATCH001_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1}:"
                "PRODUCTION_LOSS_GATE_REJECTED"
            ) from error
        return CovapieCurrent11TrainingForwardOutputV1(
            model_output=model_output,
            loss_output=loss_output,
            supervision=supervision,
            diffusion_trace=trace,
        )
