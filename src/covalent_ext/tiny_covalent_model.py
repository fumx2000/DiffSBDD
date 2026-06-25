from __future__ import annotations

import math
from typing import Any

import torch
from torch import nn


def resolve_training_smoke_device_v0(device: str = "auto") -> dict[str, Any]:
    cuda_available = torch.cuda.is_available()
    cuda_device_count = torch.cuda.device_count() if cuda_available else 0
    cuda_device_name = torch.cuda.get_device_name(0) if cuda_available and cuda_device_count > 0 else ""
    requested_device = str(device)
    fallback_reason = ""
    if device == "auto":
        resolved_device = "cuda:0" if cuda_available else "cpu"
        if not cuda_available:
            fallback_reason = "cuda_unavailable_auto_fallback_to_cpu"
    else:
        try:
            parsed_device = torch.device(device)
        except (RuntimeError, TypeError) as exc:
            parsed_device = torch.device("cpu")
            fallback_reason = f"invalid_device_fallback_to_cpu:{device}:{exc}"
        if parsed_device.type == "cuda" and not cuda_available:
            resolved_device = "cpu"
            fallback_reason = f"cuda_unavailable_fallback_to_cpu:{device}"
        else:
            resolved_device = str(parsed_device)
    return {
        "requested_device": requested_device,
        "resolved_device": resolved_device,
        "cuda_available": cuda_available,
        "cuda_device_count": int(cuda_device_count),
        "cuda_device_name": cuda_device_name,
        "device_fallback_reason": fallback_reason,
    }


def move_model_input_for_tiny_smoke_v0(model_input: dict[str, Any], device: torch.device) -> dict[str, Any]:
    moved: dict[str, Any] = {}
    for key, value in model_input.items():
        if isinstance(value, torch.Tensor):
            moved[key] = value.to(device)
        else:
            moved[key] = value
    return moved


class TinyCovalentDenoiserV0(nn.Module):
    def __init__(self, hidden_dim: int = 64, max_atomic_number: int = 128):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.max_atomic_number = max_atomic_number
        self.ligand_embedding = nn.Embedding(max_atomic_number + 1, hidden_dim, padding_idx=0)
        self.protein_embedding = nn.Embedding(max_atomic_number + 1, hidden_dim, padding_idx=0)
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim * 2 + 5, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, 4),
        )

    def forward(self, model_input: dict[str, Any]) -> dict[str, torch.Tensor]:
        ligand_h = model_input["ligand_h"].clamp(min=0, max=self.max_atomic_number).to(dtype=torch.long)
        protein_h = model_input["protein_h"].clamp(min=0, max=self.max_atomic_number).to(dtype=torch.long)
        ligand_emb = self.ligand_embedding(ligand_h)
        protein_emb = self.protein_embedding(protein_h)
        protein_mask = model_input["protein_mask"].to(dtype=protein_emb.dtype).unsqueeze(-1)
        protein_denom = protein_mask.sum(dim=1).clamp_min(1.0)
        protein_summary = (protein_emb * protein_mask).sum(dim=1) / protein_denom
        protein_summary = protein_summary[:, None, :].expand(-1, ligand_emb.shape[1], -1)
        context_mask = model_input["ligand_context_mask"].to(dtype=ligand_emb.dtype).unsqueeze(-1)
        target_mask = model_input["ligand_target_mask"].to(dtype=ligand_emb.dtype).unsqueeze(-1)
        features = torch.cat(
            [
                model_input["ligand_context_x"].to(dtype=torch.float32),
                ligand_emb,
                context_mask,
                target_mask,
                protein_summary,
            ],
            dim=-1,
        )
        raw = self.mlp(features)
        return {
            "pred_target_x": raw[..., :3],
            "pred_target_h": raw[..., 3],
        }


def compute_tiny_covalent_loss_v0(model_output: dict[str, torch.Tensor], model_input: dict[str, Any]) -> dict[str, Any]:
    target_mask = model_input["ligand_target_mask"].to(dtype=torch.bool)
    target_atom_count = int(target_mask.sum().item())
    if target_atom_count == 0:
        x_loss = model_output["pred_target_x"].sum() * 0 + torch.tensor(float("nan"), device=model_output["pred_target_x"].device)
        h_loss = model_output["pred_target_h"].sum() * 0 + torch.tensor(float("nan"), device=model_output["pred_target_h"].device)
    else:
        x_delta = model_output["pred_target_x"][target_mask] - model_input["mock_target_x"][target_mask]
        h_delta = model_output["pred_target_h"][target_mask] - model_input["mock_target_h"].to(dtype=torch.float32)[target_mask]
        x_loss = x_delta.square().mean()
        h_loss = h_delta.square().mean()
    total_loss = x_loss + 0.01 * h_loss
    return {
        "x_loss": x_loss,
        "h_loss": h_loss,
        "total_loss": total_loss,
        "x_loss_value": float(x_loss.detach().item()),
        "h_loss_value": float(h_loss.detach().item()),
        "total_loss_value": float(total_loss.detach().item()),
        "target_atom_count": target_atom_count,
        "total_loss_finite": bool(torch.isfinite(total_loss.detach()).item()),
    }


def _gradient_summary(parameters) -> tuple[float, bool, bool]:
    total_sq = 0.0
    any_nonzero = False
    finite = True
    for parameter in parameters:
        if parameter.grad is None:
            continue
        grad = parameter.grad.detach()
        finite = finite and bool(torch.isfinite(grad).all().item())
        total_sq += float(grad.square().sum().item())
        any_nonzero = any_nonzero or bool((grad != 0).any().item())
    return math.sqrt(total_sq), finite, any_nonzero


def run_tiny_training_step_v0(model_input: dict[str, Any], seed: int = 0, lr: float = 1e-3, device: str = "auto") -> dict[str, Any]:
    torch.manual_seed(seed)
    device_info = resolve_training_smoke_device_v0(device)
    resolved_device = torch.device(device_info["resolved_device"])
    moved_input = move_model_input_for_tiny_smoke_v0(model_input, resolved_device)
    model = TinyCovalentDenoiserV0().to(resolved_device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    model.train()
    optimizer.zero_grad(set_to_none=True)
    initial_output = model(moved_input)
    initial_loss = compute_tiny_covalent_loss_v0(initial_output, moved_input)
    initial_loss["total_loss"].backward()
    gradient_norm, gradient_norm_finite, any_gradient_nonzero = _gradient_summary(model.parameters())
    optimizer.step()
    with torch.no_grad():
        post_output = model(moved_input)
        post_loss = compute_tiny_covalent_loss_v0(post_output, moved_input)
    return {
        **device_info,
        "initial_total_loss": initial_loss["total_loss_value"],
        "post_step_total_loss": post_loss["total_loss_value"],
        "initial_loss_finite": bool(initial_loss["total_loss_finite"]),
        "post_step_loss_finite": bool(post_loss["total_loss_finite"]),
        "gradient_norm": gradient_norm,
        "gradient_norm_finite": gradient_norm_finite and math.isfinite(gradient_norm),
        "any_gradient_nonzero": any_gradient_nonzero,
        "target_atom_count": int(initial_loss["target_atom_count"]),
        "optimizer_step_executed": True,
        "tiny_model_initialized": True,
        "diffsbdd_model_initialized": False,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "real_training_executed": False,
        "tiny_training_step_executed": True,
    }
