from __future__ import annotations

from pathlib import Path

import pytest
import torch
from torch import nn

from covalent_ext import (
    covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
    as subject,
)
from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
ERROR = (
    "COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_AND_REAL_ONE_BATCH_TRAIN_PATH_"
    "SMOKE_V1_ERROR"
)
TARGET_RESIDUE_KEY = subject.LEGACY_ALLOWED_NEW_EXACT_KEYS_V1[0]
AUXILIARY_PREFIX = subject.LEGACY_ALLOWED_NEW_PREFIXES_V1[0]


class _ControlledDynamics(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.shared = nn.Linear(3, 2)
        self.target_residue_atom_condition_embedding = nn.Parameter(
            torch.zeros(2)
        )


class _ControlledDDPM(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.dynamics = _ControlledDynamics()


class _ControlledAuxiliary(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.role_embedding = nn.Embedding(3, 2)
        self.task_embedding = nn.Embedding(5, 2)
        self.generation_state_embedding = nn.Embedding(2, 2)
        self.seed_indicator_embedding = nn.Embedding(2, 2)
        self.anchor_distance_encoder = nn.Sequential(
            nn.Linear(1, 2), nn.SiLU(), nn.Linear(2, 2)
        )
        self.pair_logit = nn.Linear(2, 1)
        with torch.no_grad():
            self.role_embedding.weight.zero_()
            self.task_embedding.weight.zero_()
            self.generation_state_embedding.weight.zero_()
            self.seed_indicator_embedding.weight.zero_()
            self.anchor_distance_encoder[-1].weight.zero_()
            self.anchor_distance_encoder[-1].bias.zero_()


class _ControlledMigrationModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.ddpm = _ControlledDDPM()
        self.covapie_current11_auxiliary_model_v1 = _ControlledAuxiliary()


def _model_and_legacy_state(
) -> tuple[_ControlledMigrationModel, dict[str, torch.Tensor]]:
    torch.manual_seed(19)
    model = _ControlledMigrationModel()
    legacy = {
        key: value.detach().clone().add(0.25)
        for key, value in model.state_dict().items()
        if key != TARGET_RESIDUE_KEY and not key.startswith(AUXILIARY_PREFIX)
    }
    assert legacy
    return model, legacy


def _assert_public_error(callable_object) -> None:
    with pytest.raises(ValueError) as error:
        callable_object()
    assert str(error.value) == ERROR


def test_bounded_migration_preserves_new_initialization_and_loads_shared_exactly(
) -> None:
    model, legacy = _model_and_legacy_state()
    fresh_new = {
        key: value.detach().clone()
        for key, value in model.state_dict().items()
        if key == TARGET_RESIDUE_KEY or key.startswith(AUXILIARY_PREFIX)
    }
    result = subject.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
        model=model,
        checkpoint_state_dict=legacy,
    )
    migrated = model.state_dict()
    assert result["checkpoint_key_count"] == len(legacy)
    assert result["shared_key_count"] == len(legacy)
    assert result["checkpoint_only_key_count"] == 0
    assert result["shared_shape_mismatch_count"] == 0
    assert result["target_only_exact_keys"] == (TARGET_RESIDUE_KEY,)
    assert result["full_target_strict_load"] is True
    assert result["migration_missing_keys"] == ()
    assert result["migration_unexpected_keys"] == ()
    assert result["shared_checkpoint_tensor_equality_count"] == len(legacy)
    assert all(torch.equal(migrated[key], value) for key, value in legacy.items())
    assert all(
        torch.equal(migrated[key], value) for key, value in fresh_new.items()
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "extra_unexpected_key",
        "missing_historical_shared_key",
        "shared_shape_mismatch",
        "checkpoint_supplies_auxiliary_key",
        "non_tensor_state_value",
        "non_dict_state",
    ),
)
def test_legacy_migration_state_failures_are_closed(mutation: str) -> None:
    model, legacy = _model_and_legacy_state()
    state: object = dict(legacy)
    shared_key = sorted(legacy)[0]
    if mutation == "extra_unexpected_key":
        state["legacy.unexpected"] = torch.zeros(1)
    elif mutation == "missing_historical_shared_key":
        del state[shared_key]
    elif mutation == "shared_shape_mismatch":
        tensor = state[shared_key]
        state[shared_key] = torch.zeros(
            tensor.numel() + 1, dtype=tensor.dtype
        )
    elif mutation == "checkpoint_supplies_auxiliary_key":
        auxiliary_key = next(
            key for key in model.state_dict() if key.startswith(AUXILIARY_PREFIX)
        )
        state[auxiliary_key] = model.state_dict()[auxiliary_key].clone()
    elif mutation == "non_tensor_state_value":
        state[shared_key] = "not-a-tensor"
    else:
        state = tuple(legacy.items())
    _assert_public_error(
        lambda: subject.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
            model=model,
            checkpoint_state_dict=state,
        )
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "unapproved_target_only_key",
        "target_residue_singleton_missing",
        "wrong_allowed_prefix_spelling",
    ),
)
def test_legacy_migration_target_policy_drift_fails_closed(
    mutation: str,
) -> None:
    model, legacy = _model_and_legacy_state()
    if mutation == "unapproved_target_only_key":
        model.register_parameter("unapproved_target_only", nn.Parameter(
            torch.zeros(1)
        ))
    elif mutation == "target_residue_singleton_missing":
        del model.ddpm.dynamics.target_residue_atom_condition_embedding
    else:
        model.covapie_current11_auxiliary_model_vl = nn.Linear(1, 1)
    _assert_public_error(
        lambda: subject.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
            model=model,
            checkpoint_state_dict=legacy,
        )
    )


def test_current11_native_complete_state_uses_ordinary_strict_restore() -> None:
    source_model, unused_legacy = _model_and_legacy_state()
    target_model, unused_legacy_2 = _model_and_legacy_state()
    del unused_legacy, unused_legacy_2
    full_state = {
        key: value.detach().clone()
        for key, value in source_model.state_dict().items()
    }
    result = target_model.load_state_dict(full_state, strict=True)
    assert result.missing_keys == []
    assert result.unexpected_keys == []


def test_product_source_has_no_non_strict_migration_fallback() -> None:
    source = Path(migration.__file__).read_text(encoding="utf-8")
    smoke_source = Path(subject.__file__).read_text(encoding="utf-8")
    prohibited = "strict" + "=False"
    assert prohibited not in source
    assert "load_state_dict(complete_target_state, strict=True)" in source
    assert "_checkpoint_migration.load_covapie_current11_legacy_checkpoint_v1" in smoke_source
    assert (
        "_checkpoint_migration."
        "migrate_covapie_current11_legacy_checkpoint_state_dict_v1"
        in smoke_source
    )


@pytest.fixture(scope="module")
def real_smoke_result() -> dict[str, object]:
    return subject.run_covapie_current11_real_one_batch_train_path_smoke_v1(
        repo_root=ROOT,
        state_root=STATE,
        checkpoint_path=CHECKPOINT,
        device="cpu",
    )


def test_real_current11_checkpoint_migration_and_one_batch_train_path(
    real_smoke_result: dict[str, object],
) -> None:
    result = real_smoke_result
    assert result["implementation_status"] == "passed"
    assert result["checkpoint_sha256"] == (
        subject.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1
    )
    assert result["checkpoint_size_bytes"] == 17_861_341
    assert result["checkpoint_state_dict_key_count"] == 122
    assert result["target_model_state_dict_key_count"] == 141
    assert result["shared_checkpoint_key_count"] == 122
    assert result["target_only_key_count"] == 19
    assert result["checkpoint_only_key_count"] == 0
    assert result["shared_shape_mismatch_count"] == 0
    assert result["actual_target_only_exact_keys"] == (TARGET_RESIDUE_KEY,)
    assert result["actual_target_only_auxiliary_key_count"] == 18
    assert result["legacy_migration_policy_exact"] is True
    assert result["strict_false_used"] is False
    assert result["full_target_strict_load"] is True
    assert result["migration_missing_keys"] == ()
    assert result["migration_unexpected_keys"] == ()
    assert result["shared_checkpoint_tensor_equality_count"] == 122
    assert result["target_residue_embedding_preserved_zero_after_migration"] is True
    assert result["auxiliary_zero_delta_initialization_preserved"] is True
    assert result["current11_native_full_state_strict_restore"] is True
    assert result["training_forward_indicator_owner"] == (
        "tensorizer_derived_target_residue_reactive_atom_mask"
    )
    assert result["raw_target_indicator_present"] is False
    assert result["raw_target_indicator_injected"] is False
    assert result["real_sample_count"] == 11
    assert result["real_ligand_node_count"] == 323
    assert result["real_pocket_node_count"] == 2202
    assert result["real_admitted_count"] == 11
    assert result["runtime_status"] == "full_success"
    assert result["feature_binding_verified"] is True
    assert result["production_monkeypatch_used"] is False
    assert result["real_task_id_vector"] == [3, 2, 3, 0, 2, 4, 0, 0, 4, 4, 1]
    assert result["real_task_id_counts"] == {0: 3, 1: 1, 2: 2, 3: 2, 4: 3}
    assert result["all_five_task_ids_present"] is True
    assert result["model_forward_success"] is True
    assert result["all_enabled_losses_finite"] is True
    assert result["base_valid_sample_count"] == 11
    assert result["pair_valid_sample_count"] == 11
    assert result["geometry_valid_sample_count"] == 0
    assert result["contrastive_valid_sample_count"] == 11
    assert result["pre_post_geometry_loss"] == 0.0
    assert result["pair_positive_count"] == 11
    assert result["all_pair_negative_count_positive"] is True
    assert result["no_cross_sample_candidates"] is True
    assert result["geometry_head_forward"] is True
    assert result["geometry_predictions_finite"] is True
    assert result["geometry_loss_zero_due_missing_authority"] is True
    assert result["backward_success"] is True
    assert result["all_existing_gradients_finite"] is True
    assert result["shared_pretrained_nonzero_gradient"] is True
    assert result["target_residue_embedding_nonzero_gradient"] is True
    assert result["role_mask_anchor_group_nonzero_gradient"] is True
    assert result["pair_head_nonzero_gradient"] is True
    assert result["optimizer_type"] == "AdamW"
    assert result["optimizer_parameter_unique"] is True
    assert result["optimizer_parameter_set_exact"] is True
    assert result["optimizer_step_count"] == 1
    assert result["shared_pretrained_parameter_changed"] is True
    assert result["new_covapie_parameter_changed"] is True
    assert result["target_residue_embedding_changed"] is True
    assert result["all_parameters_finite_after_step"] is True
    assert result["checkpoint_file_unchanged"] is True
    assert result["decision_file_unchanged"] is True
    assert result["formal_carrier_unchanged"] is True
    assert result["new_independent_blocker_detected"] is False
    assert result["checkpoint_bytes_read"] is True
    assert result["model_forward"] is True
    assert result["auxiliary_forward"] is True
    assert result["loss_forward"] is True
    assert result["backward"] is True
    assert result["optimizer_created"] is True
    assert result["optimizer_step"] is True
    assert result["GPU_training"] is False
    assert result["RL"] is False
    assert result["checkpoint_saved"] is False
    assert result["model_saved"] is False
    assert result["tensor_dump_saved"] is False
    assert result["Trainer_fit"] is False
    assert result["ready_for_training"] is False
