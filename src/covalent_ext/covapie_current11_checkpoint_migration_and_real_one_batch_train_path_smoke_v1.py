"""Bounded legacy migration and one real Current11 train-path smoke V1."""

from __future__ import annotations

import contextlib
import hashlib
import io
import platform
import stat
from pathlib import Path
from typing import NoReturn

import torch
from torch import nn

from covalent_ext.biopython_compat import (
    patch_biopython_polypeptide_three_to_one,
)


patch_biopython_polypeptide_three_to_one()

import constants  # noqa: E402
import pytorch_lightning  # noqa: E402
from dataset import ProcessedLigandPocketDataset  # noqa: E402
from covalent_ext import (  # noqa: E402
    covapie_current11_checkpoint_migration_v1 as _checkpoint_migration,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_role_seed_human_gold_ingestion_compiler_v1
    as _human_gold_compiler,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as _context_bridge,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_task2_lightning_runtime_integration_v1
    as _runtime_integration,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_trainable_supervision_materializer_v1 as _materializer,
)
from covalent_ext.checkpoint_compatible_model_instantiation import (  # noqa: E402
    BEST_CONFIG_CANDIDATE_PATH,
    CONFIG_PREVIEW_PATH,
    _constructor_config_from_compatible_config,
    _temporary_10d_dataset_info,
    build_checkpoint_compatible_config_v0,
    load_config_preview_v0,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (  # noqa: E402
    AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1,
    CovapieCurrent11TrainingForwardOutputV1,
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from covalent_ext.diffsbdd_model_instantiation import (  # noqa: E402
    _constructor_kwargs,
)


__all__ = (
    "COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_AND_REAL_ONE_BATCH_TRAIN_PATH_SMOKE_V1_ERROR",
    "COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1",
    "COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1",
    "LEGACY_ALLOWED_NEW_EXACT_KEYS_V1",
    "LEGACY_ALLOWED_NEW_PREFIXES_V1",
    "load_covapie_current11_legacy_checkpoint_v1",
    "migrate_covapie_current11_legacy_checkpoint_state_dict_v1",
    "run_covapie_current11_real_one_batch_train_path_smoke_v1",
)


COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_AND_REAL_ONE_BATCH_TRAIN_PATH_SMOKE_V1_ERROR = (
    "COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_AND_REAL_ONE_BATCH_TRAIN_PATH_"
    "SMOKE_V1_ERROR"
)
COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1 = (
    _checkpoint_migration.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1
)
COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1 = (
    _checkpoint_migration.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1
)
LEGACY_ALLOWED_NEW_EXACT_KEYS_V1 = (
    _checkpoint_migration.LEGACY_ALLOWED_NEW_EXACT_KEYS_V1
)
LEGACY_ALLOWED_NEW_PREFIXES_V1 = (
    _checkpoint_migration.LEGACY_ALLOWED_NEW_PREFIXES_V1
)
_FORMAL_CARRIER_RELATIVE_PATH_V1 = Path(
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1/"
    "current11_runtime_sample_and_role_order_carrier.npz"
)
_FORMAL_CARRIER_EXPECTED_SHA256_V1 = (
    "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"
)
_DATASET_NAME_V1 = "covapie_current11_real_one_batch_train_path_smoke_v1_10d"


class _SmokeInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _SmokeInvariantError()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise _SmokeInvariantError() from error
    return digest.hexdigest()


def _safe_regular_file(path: Path) -> tuple[int, str]:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise _SmokeInvariantError() from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        _fail()
    return metadata.st_size, _sha256(path)


def _nonzero_finite_gradient(parameter: nn.Parameter) -> bool:
    gradient = parameter.grad
    return bool(
        gradient is not None
        and torch.isfinite(gradient).all().item()
        and torch.count_nonzero(gradient).item() > 0
    )


def _public_error(error: Exception) -> NoReturn:
    if (
        type(error) is ValueError
        and str(error)
        == COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_AND_REAL_ONE_BATCH_TRAIN_PATH_SMOKE_V1_ERROR
    ):
        raise error
    raise ValueError(
        COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_AND_REAL_ONE_BATCH_TRAIN_PATH_SMOKE_V1_ERROR
    ) from error


def load_covapie_current11_legacy_checkpoint_v1(
    *, checkpoint_path: Path,
) -> dict[str, object]:
    """Preserve the historical smoke API while delegating product policy."""

    try:
        return _checkpoint_migration.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=checkpoint_path
        )
    except Exception as error:
        _public_error(error)


def migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
    *,
    model: nn.Module,
    checkpoint_state_dict: object,
) -> dict[str, object]:
    """Preserve the historical smoke API while delegating product policy."""

    try:
        return _checkpoint_migration.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
            model=model,
            checkpoint_state_dict=checkpoint_state_dict,
        )
    except Exception as error:
        _public_error(error)


def _instantiate_current11_model_v1(
    *, repo_root: Path, state_root: Path, device: str,
) -> CovapieCurrent11TrainingLigandPocketDDPM:
    if device != "cpu":
        _fail()
    preview_result = load_config_preview_v0(repo_root / CONFIG_PREVIEW_PATH)
    if preview_result.get("config_preview_loaded") is not True:
        _fail()
    compatible = build_checkpoint_compatible_config_v0(
        preview_result["preview"], repo_root / BEST_CONFIG_CANDIDATE_PATH
    )
    relevant = compatible.get("compatible_config_flattened_relevant_fields")
    if (
        compatible.get("compatible_config_built") is not True
        or type(relevant) is not dict
        or relevant.get("mode") != "pocket_conditioning"
        or relevant.get("pocket_representation") != "full-atom"
        or relevant.get("virtual_nodes") is not False
        or relevant.get("egnn_params.joint_nf") != 32
        or relevant.get("egnn_params.hidden_nf") != 128
        or relevant.get("egnn_params.n_layers") != 5
    ):
        _fail()
    config = _constructor_config_from_compatible_config(
        compatible, _DATASET_NAME_V1, device
    )
    config["batch_size"] = 11
    kwargs = _constructor_kwargs(config)
    kwargs.update({
        "target_residue_atom_conditioning": True,
        "covapie_current11_task2_runtime_enabled": True,
        "covapie_repository_root": str(repo_root),
        "covapie_state_root": str(state_root),
    })
    previous = constants.dataset_params.get(_DATASET_NAME_V1)
    constants.dataset_params[_DATASET_NAME_V1] = _temporary_10d_dataset_info()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            model = CovapieCurrent11TrainingLigandPocketDDPM(**kwargs)
    finally:
        if previous is None:
            constants.dataset_params.pop(_DATASET_NAME_V1, None)
        else:
            constants.dataset_params[_DATASET_NAME_V1] = previous
    model = model.to(torch.device(device))
    if (
        model.mode != "pocket_conditioning"
        or model.pocket_representation != "full-atom"
        or model.atom_nf != 10
        or model.aa_nf != 10
        or model.virtual_nodes is not False
        or model.auxiliary_loss is not False
        or model.target_residue_atom_conditioning is not True
        or model.covapie_current11_task2_runtime_enabled is not True
        or len(model.state_dict()) != 141
    ):
        _fail()
    return model


def _build_real_current11_batch_v1(
    *, repo_root: Path, state_root: Path,
) -> dict[str, object]:
    from scripts import (  # noqa: PLC0415
        check_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
        as _bridge_checker,
    )

    remap_context, acquisition = _bridge_checker._acquire_remap_context(
        lifecycle="precommit-untracked",
        repo_root=repo_root,
        state_root=state_root,
    )
    if (
        acquisition.get("test_harness_only") is not True
        or acquisition.get("real_public_remap_context_build_performed")
        is not False
        or acquisition.get("predecessor_public_call_counts")
        != {"reconciliation": 1, "successor": 1, "B2": 1}
        or acquisition.get("formal_before_after_call_count") != 2
        or acquisition.get("production_monkeypatch_used") is not False
    ):
        _fail()
    compiler_context = (
        _context_bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
            remap_context=remap_context,
        )
    )
    formal_carrier_path = state_root / _FORMAL_CARRIER_RELATIVE_PATH_V1
    formal_size_before, formal_digest_before = _safe_regular_file(
        formal_carrier_path
    )
    if formal_digest_before != _FORMAL_CARRIER_EXPECTED_SHA256_V1:
        _fail()
    dataset = ProcessedLigandPocketDataset(formal_carrier_path, center=False)
    if len(dataset) != 11:
        _fail()
    raw_batch = dataset.collate_fn([dataset[index] for index in range(11)])
    indicator_field = "pocket_target_residue_atom_condition_indicator"
    if indicator_field in raw_batch:
        _fail()
    batch = (
        _runtime_integration.attach_covapie_current11_task2_lightning_runtime_result_v1(
            enabled=True,
            batch=raw_batch,
            remap_context=remap_context,
            compiler_context=compiler_context,
        )
    )
    runtime = batch.get(_runtime_integration.SIDECAR_FIELD)
    if (
        type(runtime) is not dict
        or runtime.get("runtime_status") != "full_success"
        or indicator_field in batch
    ):
        _fail()
    payload = _materializer.load_covapie_current11_machine_authority_payload_v1(
        repo_root=repo_root,
        state_root=state_root,
        runtime_output17=runtime.get("remap_output17_or_none"),
    )
    compiled = (
        _human_gold_compiler.load_and_compile_covapie_current11_role_seed_human_gold_v1(
            state_root=state_root,
            machine_authority_payload=payload,
        )
    )
    supervision_bundle = _materializer.build_current11_training_supervision_v1(
        authority_payload=compiled.get("compiled_authority_payload")
    )
    summary = supervision_bundle.get("summary")
    supervision = supervision_bundle.get("authoritative_supervision")
    if (
        type(summary) is not dict
        or summary.get("exact3_role_human_gold_count") != 11
        or summary.get("minimal_seed_human_gold_count") != 11
        or summary.get("real_admitted_sample_count") != 11
        or type(supervision) is not dict
        or supervision.get("sample_training_admitted") != [True] * 11
        or supervision.get("ligand_node_offsets", [None])[-1] != 323
        or supervision.get("pocket_node_offsets", [None])[-1] != 2202
        or type(supervision.get("formal_carrier_feature_binding")) is not dict
    ):
        _fail()
    model_batch = {
        **batch,
        AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1: supervision,
    }
    if (
        any(model_batch[key] is not value for key, value in batch.items())
        or model_batch[_runtime_integration.SIDECAR_FIELD] is not runtime
        or indicator_field in model_batch
    ):
        _fail()
    formal_size_after, formal_digest_after = _safe_regular_file(
        formal_carrier_path
    )
    if (
        formal_size_after != formal_size_before
        or formal_digest_after != formal_digest_before
    ):
        _fail()
    return {
        "model_batch": model_batch,
        "runtime": runtime,
        "authoritative_supervision": supervision,
        "formal_carrier_path": formal_carrier_path,
        "formal_carrier_sha256": formal_digest_before,
        "real_sample_count": 11,
        "real_ligand_node_count": 323,
        "real_pocket_node_count": 2202,
        "real_admitted_count": 11,
        "raw_target_indicator_present": False,
        "raw_target_indicator_injected": False,
        "feature_binding_verified": True,
        "runtime_status": runtime["runtime_status"],
        "production_monkeypatch_used": False,
    }


def _run_smoke_impl(
    *,
    repo_root: Path,
    state_root: Path,
    checkpoint_path: Path,
    device: str,
) -> dict[str, object]:
    if (
        type(repo_root) is not type(Path())
        or type(state_root) is not type(Path())
        or type(checkpoint_path) is not type(Path())
        or not repo_root.is_absolute()
        or not state_root.is_absolute()
        or not checkpoint_path.is_absolute()
        or repo_root.resolve(strict=True) != repo_root
        or state_root.resolve(strict=True) != state_root
        or device != "cpu"
    ):
        _fail()
    decision_path = (
        state_root
        / _human_gold_compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_RELATIVE_PATH_V1
    )
    decision_size_before, decision_digest_before = _safe_regular_file(
        decision_path
    )
    if (
        decision_digest_before
        != _human_gold_compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_SHA256_V1
    ):
        _fail()

    checkpoint = load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=checkpoint_path
    )
    checkpoint_state = checkpoint["state_dict"]
    torch.manual_seed(20260816)
    model = _instantiate_current11_model_v1(
        repo_root=repo_root, state_root=state_root, device=device
    )
    migration = migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
        model=model,
        checkpoint_state_dict=checkpoint_state,
    )
    if (
        migration["checkpoint_key_count"] != 122
        or migration["target_model_key_count"] != 141
        or migration["shared_key_count"] != 122
        or migration["target_only_key_count"] != 19
        or migration["checkpoint_only_key_count"] != 0
        or migration["shared_shape_mismatch_count"] != 0
        or len(migration["target_only_auxiliary_keys"]) != 18
    ):
        _fail()

    full_current11_state = {
        key: value.detach().clone() for key, value in model.state_dict().items()
    }
    torch.manual_seed(20260816)
    native_model = _instantiate_current11_model_v1(
        repo_root=repo_root, state_root=state_root, device=device
    )
    native_result = native_model.load_state_dict(
        full_current11_state, strict=True
    )
    if native_result.missing_keys or native_result.unexpected_keys:
        _fail()
    del native_model, full_current11_state

    real = _build_real_current11_batch_v1(
        repo_root=repo_root, state_root=state_root
    )
    model.train()
    if model.training is not True or model.ddpm.training is not True:
        _fail()
    torch.manual_seed(20260816)
    output = model.forward(real["model_batch"])
    if not isinstance(output, CovapieCurrent11TrainingForwardOutputV1):
        _fail()
    losses = output.loss_output
    model_output = output.model_output
    supervision = output.supervision
    loss_tensors = (
        losses.loss_base_diffusion,
        losses.loss_covalent_pair_prediction,
        losses.loss_pre_post_geometry,
        losses.loss_covalent_pair_contrastive,
        losses.loss_total,
    )
    forward_tensors = (
        model_output.pair_logits,
        model_output.pair_embeddings,
        model_output.pre_post_geometry_predictions_angstrom,
    )
    task_ids = supervision.canonical_task_id.tolist()
    task_counts = {
        task_id: task_ids.count(task_id) for task_id in range(5)
    }
    batch = real["model_batch"]
    pair_ligand_samples = batch["lig_mask"][
        supervision.pair_candidate_ligand_flat_index
    ]
    pair_pocket_samples = batch["pocket_mask"][
        supervision.pair_candidate_pocket_flat_index
    ]
    if (
        task_ids != [3, 2, 3, 0, 2, 4, 0, 0, 4, 4, 1]
        or set(task_ids) != set(range(5))
        or any(not torch.isfinite(value).all().item() for value in loss_tensors)
        or any(
            not torch.isfinite(value).all().item() for value in forward_tensors
        )
        or losses.base_diffusion_valid_sample_count != 11
        or losses.covalent_pair_prediction_valid_sample_count != 11
        or losses.pre_post_geometry_valid_sample_count != 0
        or losses.covalent_pair_contrastive_valid_sample_count != 11
        or losses.loss_pre_post_geometry.item() != 0.0
        or supervision.pair_positive_candidate_valid.tolist() != [True] * 11
        or supervision.pair_candidate_is_positive.sum().item() != 11
        or not bool((supervision.pair_negative_count > 0).all().item())
        or not torch.equal(
            supervision.pair_candidate_batch_index, pair_ligand_samples
        )
        or not torch.equal(
            supervision.pair_candidate_batch_index, pair_pocket_samples
        )
    ):
        _fail()

    optimizer = model.configure_optimizers()
    named_parameters = dict(model.named_parameters())
    model_parameters = list(model.parameters())
    model_parameter_ids = [id(parameter) for parameter in model_parameters]
    optimizer_parameters = [
        parameter
        for group in optimizer.param_groups
        for parameter in group["params"]
    ]
    optimizer_parameter_ids = [
        id(parameter) for parameter in optimizer_parameters
    ]
    if (
        not isinstance(optimizer, torch.optim.AdamW)
        or len(model_parameter_ids) != len(set(model_parameter_ids))
        or len(optimizer_parameter_ids) != len(set(optimizer_parameter_ids))
        or set(optimizer_parameter_ids) != set(model_parameter_ids)
    ):
        _fail()

    parameter_before = {
        name: parameter.detach().clone()
        for name, parameter in named_parameters.items()
    }
    shared_parameter_names = {
        name for name in named_parameters if name in checkpoint_state
    }
    new_parameter_names = {
        name
        for name in named_parameters
        if name in set(migration["target_only_exact_keys"])
        or name in set(migration["target_only_auxiliary_keys"])
    }
    target_name = LEGACY_ALLOWED_NEW_EXACT_KEYS_V1[0]
    role_group_names = {
        name
        for name in named_parameters
        if name.startswith((
            "covapie_current11_auxiliary_model_v1.role_embedding.",
            "covapie_current11_auxiliary_model_v1.task_embedding.",
            "covapie_current11_auxiliary_model_v1.generation_state_embedding.",
            "covapie_current11_auxiliary_model_v1.seed_indicator_embedding.",
            "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.",
        ))
    }
    pair_group_names = {
        name
        for name in named_parameters
        if name.startswith((
            "covapie_current11_auxiliary_model_v1.pair_embedding.",
            "covapie_current11_auxiliary_model_v1.pair_logit.",
        ))
    }
    geometry_group_names = {
        name
        for name in named_parameters
        if name.startswith(
            "covapie_current11_auxiliary_model_v1.pre_post_geometry_head."
        )
    }
    if (
        "ddpm.dynamics.egnn.embedding.weight" not in shared_parameter_names
        or target_name not in named_parameters
        or not role_group_names
        or not pair_group_names
        or not geometry_group_names
    ):
        _fail()

    optimizer.zero_grad(set_to_none=True)
    losses.loss_total.backward()
    existing_gradients = [
        parameter.grad
        for parameter in model_parameters
        if parameter.grad is not None
    ]
    shared_nonzero_gradient = any(
        _nonzero_finite_gradient(named_parameters[name])
        for name in shared_parameter_names
    )
    target_nonzero_gradient = _nonzero_finite_gradient(
        named_parameters[target_name]
    )
    role_nonzero_gradient = any(
        _nonzero_finite_gradient(named_parameters[name])
        for name in role_group_names
    )
    pair_nonzero_gradient = any(
        _nonzero_finite_gradient(named_parameters[name])
        for name in pair_group_names
    )
    geometry_nonzero_gradient = any(
        _nonzero_finite_gradient(named_parameters[name])
        for name in geometry_group_names
    )
    if (
        not existing_gradients
        or any(
            not torch.isfinite(gradient).all().item()
            for gradient in existing_gradients
        )
        or not shared_nonzero_gradient
        or not target_nonzero_gradient
        or not role_nonzero_gradient
        or not pair_nonzero_gradient
    ):
        _fail()

    optimizer.step()
    changed_names = {
        name
        for name, parameter in named_parameters.items()
        if not torch.equal(parameter.detach(), parameter_before[name])
    }
    shared_changed = bool(changed_names & shared_parameter_names)
    new_changed = bool(changed_names & new_parameter_names)
    target_changed = target_name in changed_names
    geometry_changed = bool(changed_names & geometry_group_names)
    all_parameters_finite = all(
        torch.isfinite(parameter).all().item()
        for parameter in model_parameters
    )
    if (
        not shared_changed
        or not new_changed
        or not target_changed
        or not all_parameters_finite
    ):
        _fail()

    checkpoint_size_after, checkpoint_digest_after = _safe_regular_file(
        checkpoint_path
    )
    decision_size_after, decision_digest_after = _safe_regular_file(
        decision_path
    )
    formal_size_after, formal_digest_after = _safe_regular_file(
        real["formal_carrier_path"]
    )
    if (
        checkpoint_size_after != checkpoint["checkpoint_size_bytes"]
        or checkpoint_digest_after != checkpoint["checkpoint_sha256"]
        or decision_size_after != decision_size_before
        or decision_digest_after != decision_digest_before
        or formal_digest_after != real["formal_carrier_sha256"]
        or formal_size_after <= 0
    ):
        _fail()

    return {
        "implementation_status": "passed",
        "active_python_version": platform.python_version(),
        "active_torch_version": torch.__version__,
        "active_lightning_version": pytorch_lightning.__version__,
        "declared_historical_lightning_version": checkpoint[
            "historical_pytorch_lightning_version"
        ],
        "checkpoint_path": checkpoint["checkpoint_path"],
        "checkpoint_sha256": checkpoint["checkpoint_sha256"],
        "checkpoint_size_bytes": checkpoint["checkpoint_size_bytes"],
        "checkpoint_state_dict_key_count": checkpoint[
            "checkpoint_state_dict_key_count"
        ],
        "target_model_state_dict_key_count": migration[
            "target_model_key_count"
        ],
        "shared_checkpoint_key_count": migration["shared_key_count"],
        "target_only_key_count": migration["target_only_key_count"],
        "checkpoint_only_key_count": migration["checkpoint_only_key_count"],
        "shared_shape_mismatch_count": migration[
            "shared_shape_mismatch_count"
        ],
        "legacy_allowed_new_exact_keys": LEGACY_ALLOWED_NEW_EXACT_KEYS_V1,
        "legacy_allowed_new_prefixes": LEGACY_ALLOWED_NEW_PREFIXES_V1,
        "actual_target_only_exact_keys": migration[
            "target_only_exact_keys"
        ],
        "actual_target_only_auxiliary_key_count": len(
            migration["target_only_auxiliary_keys"]
        ),
        "legacy_migration_policy_exact": True,
        "strict_false_used": False,
        "full_target_strict_load": migration["full_target_strict_load"],
        "migration_missing_keys": migration["migration_missing_keys"],
        "migration_unexpected_keys": migration[
            "migration_unexpected_keys"
        ],
        "shared_checkpoint_tensor_equality_count": migration[
            "shared_checkpoint_tensor_equality_count"
        ],
        "target_residue_embedding_preserved_zero_after_migration": migration[
            "target_residue_embedding_preserved_zero_after_migration"
        ],
        "auxiliary_zero_delta_initialization_preserved": migration[
            "auxiliary_zero_delta_initialization_preserved"
        ],
        "current11_native_full_state_strict_restore": True,
        "training_forward_indicator_owner": (
            "tensorizer_derived_target_residue_reactive_atom_mask"
        ),
        "raw_target_indicator_present": False,
        "raw_target_indicator_injected": False,
        "real_sample_count": real["real_sample_count"],
        "real_ligand_node_count": real["real_ligand_node_count"],
        "real_pocket_node_count": real["real_pocket_node_count"],
        "real_admitted_count": real["real_admitted_count"],
        "feature_binding_verified": real["feature_binding_verified"],
        "runtime_status": real["runtime_status"],
        "production_monkeypatch_used": real["production_monkeypatch_used"],
        "real_task_id_vector": task_ids,
        "real_task_id_counts": task_counts,
        "all_five_task_ids_present": set(task_ids) == set(range(5)),
        "model_forward_success": True,
        "base_loss": float(losses.loss_base_diffusion.detach().item()),
        "pair_prediction_loss": float(
            losses.loss_covalent_pair_prediction.detach().item()
        ),
        "pre_post_geometry_loss": float(
            losses.loss_pre_post_geometry.detach().item()
        ),
        "contrastive_loss": float(
            losses.loss_covalent_pair_contrastive.detach().item()
        ),
        "total_loss": float(losses.loss_total.detach().item()),
        "all_enabled_losses_finite": True,
        "base_valid_sample_count": losses.base_diffusion_valid_sample_count,
        "pair_valid_sample_count": (
            losses.covalent_pair_prediction_valid_sample_count
        ),
        "geometry_valid_sample_count": (
            losses.pre_post_geometry_valid_sample_count
        ),
        "contrastive_valid_sample_count": (
            losses.covalent_pair_contrastive_valid_sample_count
        ),
        "pair_positive_count": int(
            supervision.pair_candidate_is_positive.sum().item()
        ),
        "all_pair_negative_count_positive": True,
        "no_cross_sample_candidates": True,
        "geometry_head_forward": True,
        "geometry_predictions_finite": True,
        "geometry_loss_zero_due_missing_authority": True,
        "backward_success": True,
        "all_existing_gradients_finite": True,
        "shared_pretrained_nonzero_gradient": shared_nonzero_gradient,
        "target_residue_embedding_nonzero_gradient": target_nonzero_gradient,
        "role_mask_anchor_group_nonzero_gradient": role_nonzero_gradient,
        "pair_head_nonzero_gradient": pair_nonzero_gradient,
        "geometry_head_nonzero_gradient": geometry_nonzero_gradient,
        "optimizer_type": type(optimizer).__name__,
        "model_parameter_tensor_count": len(model_parameters),
        "optimizer_parameter_tensor_count": len(optimizer_parameters),
        "optimizer_unique_parameter_count": len(
            set(optimizer_parameter_ids)
        ),
        "optimizer_parameter_unique": True,
        "optimizer_parameter_set_exact": True,
        "optimizer_step_count": 1,
        "shared_pretrained_parameter_changed": shared_changed,
        "new_covapie_parameter_changed": new_changed,
        "target_residue_embedding_changed": target_changed,
        "geometry_head_changed": geometry_changed,
        "all_parameters_finite_after_step": all_parameters_finite,
        "checkpoint_file_unchanged": True,
        "decision_file_unchanged": True,
        "formal_carrier_unchanged": True,
        "legacy_checkpoint_migration_proved": True,
        "real_current11_model_forward_proved": True,
        "real_current11_loss_path_proved": True,
        "real_current11_backward_proved": True,
        "real_current11_optimizer_ownership_proved": True,
        "real_current11_single_optimizer_step_proved": True,
        "current11_feature_semantics_known": True,
        "new_independent_blocker_detected": False,
        "checkpoint_bytes_read": True,
        "model_forward": True,
        "auxiliary_forward": True,
        "loss_forward": True,
        "backward": True,
        "optimizer_created": True,
        "optimizer_step": True,
        "GPU_training": False,
        "RL": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "Trainer_fit": False,
        "ready_for_training": False,
    }


def run_covapie_current11_real_one_batch_train_path_smoke_v1(
    *,
    repo_root: Path,
    state_root: Path,
    checkpoint_path: Path,
    device: str = "cpu",
) -> dict[str, object]:
    """Run one real forward, one backward, and one optimizer step on CPU."""

    try:
        return _run_smoke_impl(
            repo_root=repo_root,
            state_root=state_root,
            checkpoint_path=checkpoint_path,
            device=device,
        )
    except Exception as error:
        _public_error(error)
