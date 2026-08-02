"""Strict in-memory checkpoint migration for target-residue conditioning V1."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import torch


__all__ = (
    "load_covapie_base_state_dict_into_target_residue_conditioned_model_v1",
)


_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_MODEL_CONSUMPTION_INVALID"
_NEW_STATE_KEY = (
    "ddpm.dynamics.target_residue_atom_condition_embedding"
)


def load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
    *,
    model: torch.nn.Module,
    base_state_dict: Mapping[str, torch.Tensor],
) -> dict[str, Any]:
    """Load a base state dict after filling the single conditioned parameter."""

    try:
        if (
            not isinstance(model, torch.nn.Module)
            or not isinstance(base_state_dict, Mapping)
            or any(
                type(key) is not str or not isinstance(value, torch.Tensor)
                for key, value in base_state_dict.items()
            )
        ):
            raise ValueError(_ERROR)

        model_state_dict = model.state_dict()
        model_keys = set(model_state_dict)
        base_keys = set(base_state_dict)
        if (
            model_keys - base_keys != {_NEW_STATE_KEY}
            or base_keys - model_keys
        ):
            raise ValueError(_ERROR)

        dynamics = getattr(getattr(model, "ddpm", None), "dynamics", None)
        if (
            dynamics is None
            or getattr(
                dynamics,
                "target_residue_atom_conditioning",
                False,
            ) is not True
        ):
            raise ValueError(_ERROR)

        new_tensor = model_state_dict[_NEW_STATE_KEY]
        named_parameters = dict(model.named_parameters())
        if (
            _NEW_STATE_KEY not in named_parameters
            or list(new_tensor.shape) != [32]
            or not new_tensor.is_floating_point()
            or int(torch.count_nonzero(new_tensor).item()) != 0
        ):
            raise ValueError(_ERROR)

        for key in base_state_dict:
            base_tensor = base_state_dict[key]
            model_tensor = model_state_dict[key]
            if (
                base_tensor.shape != model_tensor.shape
                or base_tensor.dtype != model_tensor.dtype
            ):
                raise ValueError(_ERROR)

        migrated_state_dict = dict(base_state_dict)
        migrated_state_dict[_NEW_STATE_KEY] = new_tensor.detach().clone()
        incompatible = model.load_state_dict(migrated_state_dict, strict=True)
        missing_keys = list(incompatible.missing_keys)
        unexpected_keys = list(incompatible.unexpected_keys)
        if missing_keys or unexpected_keys:
            raise ValueError(_ERROR)

        return {
            "base_state_key_count": len(base_state_dict),
            "model_state_key_count": len(model_state_dict),
            "shared_state_key_count": len(base_state_dict),
            "filled_state_keys": [_NEW_STATE_KEY],
            "missing_keys": missing_keys,
            "unexpected_keys": unexpected_keys,
            "strict_load": True,
            "base_state_dict_modified": False,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
