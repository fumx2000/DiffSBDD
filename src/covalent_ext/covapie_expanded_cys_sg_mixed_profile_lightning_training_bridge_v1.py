"""Additive Lightning training bridge for the published Exact16 mixed batch."""

from __future__ import annotations

from dataclasses import fields
from typing import NoReturn

import torch

from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    compute_covapie_current11_training_losses_v1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11TrainingForwardOutputV1,
    CovapieCurrent11TrainingLigandPocketDDPM,
    run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)
from covalent_ext.covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1 import (
    CovapieExpandedCysSgMixedBatchV1,
    validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1,
)


__all__ = (
    "COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_LIGHTNING_TRAINING_BRIDGE_V1_ERROR",
    "CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1",
)


COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_LIGHTNING_TRAINING_BRIDGE_V1_ERROR = (
    "COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_LIGHTNING_TRAINING_BRIDGE_V1_ERROR"
)


class _MixedProfileLightningBridgeInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _MixedProfileLightningBridgeInvariantError()


def _public_error(error: Exception) -> NoReturn:
    if (
        type(error) is ValueError
        and str(error)
        == COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_LIGHTNING_TRAINING_BRIDGE_V1_ERROR
    ):
        raise error
    raise ValueError(
        COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_LIGHTNING_TRAINING_BRIDGE_V1_ERROR
    ) from error


class CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1(
    CovapieCurrent11TrainingLigandPocketDDPM
):
    """Route one validated Exact16 mixed batch through the published owner."""

    def transfer_batch_to_device(
        self,
        batch: object,
        device: torch.device,
        dataloader_idx: int,
    ) -> CovapieExpandedCysSgMixedBatchV1:
        """Rebuild the frozen batch dataclasses while moving only tensors."""

        if type(batch) is not CovapieExpandedCysSgMixedBatchV1:
            raise ValueError(
                COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_LIGHTNING_TRAINING_BRIDGE_V1_ERROR
            )
        try:
            parent_transfer = super().transfer_batch_to_device
            model_input_batch = parent_transfer(
                batch.model_input_batch, device, dataloader_idx
            )
            supervision_values: dict[str, torch.Tensor] = {}
            for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
                value = getattr(batch.supervision, field.name)
                if not isinstance(value, torch.Tensor):
                    _fail()
                transferred = parent_transfer(value, device, dataloader_idx)
                if not isinstance(transferred, torch.Tensor):
                    _fail()
                supervision_values[field.name] = transferred
            supervision = CovapieCurrent11TrainingSupervisionTensorsV1(
                **supervision_values
            )
            if type(model_input_batch) is not dict:
                _fail()
            return CovapieExpandedCysSgMixedBatchV1(
                model_input_batch=model_input_batch,
                supervision=supervision,
                sample_identities=batch.sample_identities,
                role_profiles=batch.role_profiles,
                scheduled_task_ids=batch.scheduled_task_ids,
                epoch=batch.epoch,
                task_schedule_seed=batch.task_schedule_seed,
                current11_batch_indices=batch.current11_batch_indices,
                k36_batch_indices=batch.k36_batch_indices,
            )
        except Exception as error:
            _public_error(error)

    def forward(
        self, data: object
    ) -> CovapieCurrent11TrainingForwardOutputV1:
        """Execute the training-only lower-level path on canonical supervision."""

        if self.training is not True:
            raise ValueError(
                COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_LIGHTNING_TRAINING_BRIDGE_V1_ERROR
            )
        if type(data) is not CovapieExpandedCysSgMixedBatchV1:
            raise ValueError(
                COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_LIGHTNING_TRAINING_BRIDGE_V1_ERROR
            )
        try:
            if (
                data.epoch != int(self.current_epoch)
                or data.task_schedule_seed
                != self.covapie_current11_task_schedule_seed
            ):
                _fail()
            validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1(data)

            ligand, pocket = self.get_ligand_and_pocket(
                data.model_input_batch
            )
            supervision = data.supervision
            canonical_indicator = (
                supervision.target_residue_reactive_atom_mask
            )
            pocket_x = pocket.get("x") if type(pocket) is dict else None
            if (
                not isinstance(canonical_indicator, torch.Tensor)
                or canonical_indicator.dtype != torch.bool
                or canonical_indicator.ndim != 2
                or not isinstance(pocket_x, torch.Tensor)
                or canonical_indicator.shape != (len(pocket_x), 1)
            ):
                _fail()
            canonical_indicator = canonical_indicator[:, 0]
            role_delta = (
                self.covapie_current11_auxiliary_model_v1
                .encode_role_mask_anchor_v1(
                    supervision=supervision,
                    ligand_batch_index=ligand["mask"],
                )
            )
            trace = (
                run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
                    ddpm=self.ddpm,
                    ligand=ligand,
                    pocket=pocket,
                    supervision=supervision,
                    role_mask_anchor_hidden_delta=role_delta,
                    pocket_target_residue_atom_condition_indicator=(
                        canonical_indicator
                    ),
                )
            )
            model_output = self.covapie_current11_auxiliary_model_v1(
                diffusion_trace=trace,
                supervision=supervision,
                role_mask_anchor_hidden_delta=role_delta,
            )
            loss_output = compute_covapie_current11_training_losses_v1(
                model_output=model_output,
                supervision=supervision,
                diffusion_trace=trace,
                loss_weights=self.covapie_current11_loss_weights,
                pair_contrastive_temperature=(
                    self.covapie_current11_pair_contrastive_temperature
                ),
                geometry_smooth_l1_beta=1.0,
            )
            return CovapieCurrent11TrainingForwardOutputV1(
                model_output=model_output,
                loss_output=loss_output,
                supervision=supervision,
                diffusion_trace=trace,
            )
        except Exception as error:
            _public_error(error)
