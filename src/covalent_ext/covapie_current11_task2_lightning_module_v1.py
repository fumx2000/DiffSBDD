"""Opt-in Lightning module for Current11 Task 2 runtime transport V1."""

from __future__ import annotations

from argparse import Namespace

from lightning_modules import LigandPocketDDPM
from covalent_ext import (
    covapie_current11_task2_lightning_runtime_integration_v1 as _integration,
)


__all__ = (
    "CovapieCurrent11Task2LigandPocketDDPM",
)


class CovapieCurrent11Task2LigandPocketDDPM(LigandPocketDDPM):
    """Add opt-in Current11 transport while preserving the frozen base owner."""

    def __init__(
            self,
            outdir,
            dataset,
            datadir,
            batch_size,
            lr,
            egnn_params: Namespace,
            diffusion_params,
            num_workers,
            augment_noise,
            augment_rotation,
            clip_grad,
            eval_epochs,
            eval_params,
            visualize_sample_epoch,
            visualize_chain_epoch,
            auxiliary_loss,
            loss_params,
            mode,
            node_histogram,
            pocket_representation='CA',
            virtual_nodes=False,
            target_residue_atom_conditioning=False,
            *,
            covapie_current11_task2_runtime_enabled=False,
            covapie_repository_root=None,
            covapie_state_root=None,
    ):
        _integration.validate_covapie_current11_task2_lightning_runtime_configuration_v1(
            enabled=covapie_current11_task2_runtime_enabled,
            repository_root=covapie_repository_root,
            state_root=covapie_state_root,
            virtual_nodes=virtual_nodes,
        )
        super().__init__(
            outdir=outdir,
            dataset=dataset,
            datadir=datadir,
            batch_size=batch_size,
            lr=lr,
            egnn_params=egnn_params,
            diffusion_params=diffusion_params,
            num_workers=num_workers,
            augment_noise=augment_noise,
            augment_rotation=augment_rotation,
            clip_grad=clip_grad,
            eval_epochs=eval_epochs,
            eval_params=eval_params,
            visualize_sample_epoch=visualize_sample_epoch,
            visualize_chain_epoch=visualize_chain_epoch,
            auxiliary_loss=auxiliary_loss,
            loss_params=loss_params,
            mode=mode,
            node_histogram=node_histogram,
            pocket_representation=pocket_representation,
            virtual_nodes=virtual_nodes,
            target_residue_atom_conditioning=(
                target_residue_atom_conditioning
            ),
        )
        self.covapie_current11_task2_runtime_enabled = \
            covapie_current11_task2_runtime_enabled
        self.covapie_repository_root = covapie_repository_root
        self.covapie_state_root = covapie_state_root
        self._covapie_current11_task2_remap_context_v1 = None
        self._covapie_current11_task2_compiler_context_v1 = None
        self.save_hyperparameters(
            "covapie_current11_task2_runtime_enabled",
            "covapie_repository_root",
            "covapie_state_root",
        )

    def setup(self, stage=None):
        if (
            stage in ("fit", "test")
            and self.covapie_current11_task2_runtime_enabled is True
        ):
            (
                self._covapie_current11_task2_remap_context_v1,
                self._covapie_current11_task2_compiler_context_v1,
            ) = _integration.build_or_reuse_covapie_current11_task2_lightning_runtime_context_pair_v1(
                repository_root=self.covapie_repository_root,
                state_root=self.covapie_state_root,
                remap_context=(
                    self._covapie_current11_task2_remap_context_v1
                ),
                compiler_context=(
                    self._covapie_current11_task2_compiler_context_v1
                ),
            )
        return super().setup(stage)

    def on_before_batch_transfer(self, batch, dataloader_idx):
        return _integration.attach_covapie_current11_task2_lightning_runtime_result_v1(
            enabled=self.covapie_current11_task2_runtime_enabled,
            batch=batch,
            remap_context=self._covapie_current11_task2_remap_context_v1,
            compiler_context=(
                self._covapie_current11_task2_compiler_context_v1
            ),
        )
