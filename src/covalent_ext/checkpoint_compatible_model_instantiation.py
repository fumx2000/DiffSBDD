from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib
import io
import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any

import torch
import yaml

from covalent_ext.diffsbdd_forward_shape_smoke import _inspect_forward_output
from covalent_ext.diffsbdd_model_instantiation import (
    MODEL_CLASS_NAME,
    MODEL_MODULE_NAME,
    _constructor_kwargs,
)
from covalent_ext.biopython_compat import patch_biopython_polypeptide_three_to_one
from covalent_ext.pretrained_checkpoint_architecture_reconciliation import (
    infer_architecture_from_state_shapes_v0,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STAGE = "checkpoint_compatible_instantiation_wrapper_v0"
PREVIOUS_STAGE = "checkpoint_original_config_instantiation_design_v0"
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
CONFIG_PREVIEW_PATH = Path(
    "data/derived/covalent_small/checkpoint_original_config_instantiation_design_v0/checkpoint_original_config_preview.json"
)
STEP11C_MANIFEST_JSON = Path(
    "data/derived/covalent_small/checkpoint_original_config_instantiation_design_v0/checkpoint_original_config_instantiation_design_manifest.json"
)
STEP11C_SUMMARY_MD = Path("docs/checkpoint_original_config_instantiation_design_v0_summary.md")
BEST_CONFIG_CANDIDATE_PATH = Path("configs/crossdock_fullatom_joint.yml")
OUTPUT_ROOT = Path("data/derived/covalent_small/checkpoint_compatible_instantiation_wrapper_v0")
REPORT_CSV = OUTPUT_ROOT / "checkpoint_compatible_instantiation_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "checkpoint_compatible_instantiation_manifest.json"
SHAPE_MATCH_TABLE_CSV = OUTPUT_ROOT / "checkpoint_compatible_shape_match_table.csv"
INPUT_CONTRACT_PREVIEW_JSON = OUTPUT_ROOT / "checkpoint_compatible_input_contract_preview.json"
SUMMARY_MD = Path("docs/checkpoint_compatible_instantiation_wrapper_v0_summary.md")
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
SHAPE_MATCH_GOAL = 0.8
PREVIOUS_SHAPE_MATCH_RATIO = 0.05737704918032787
TEMP_DATASET_NAME = "crossdock_checkpoint_10d_fullatom_shape_smoke"


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _shape(value: Any) -> list[int]:
    return [int(dim) for dim in value.shape] if torch.is_tensor(value) else []


def _numel(shape: list[int] | None) -> int:
    if not shape:
        return 0
    total = 1
    for dim in shape:
        total *= int(dim)
    return total


def _source_diff_exists() -> bool:
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *PROTECTED_SOURCE_PATHS],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *PROTECTED_SOURCE_PATHS],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return unstaged.returncode != 0 or staged.returncode != 0


def _forbidden_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES for path in root_path.rglob("*"))


def _load_yaml(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _namespace(value: dict[str, Any]) -> Namespace:
    return Namespace(**value)


def _get_child(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _resolve_device(device: str) -> str:
    if device == "auto":
        return "cuda:0" if torch.cuda.is_available() else "cpu"
    if device.startswith("cuda") and not torch.cuda.is_available():
        return "cpu"
    return device


def validate_step11c_outputs_v0() -> bool:
    if not STEP11C_MANIFEST_JSON.is_file() or not CONFIG_PREVIEW_PATH.is_file() or not STEP11C_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11C outputs are missing")
    manifest = _load_json(STEP11C_MANIFEST_JSON)
    preview = _load_json(CONFIG_PREVIEW_PATH)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "pretrained_checkpoint_architecture_reconciliation_v0",
        "step11b_validated": True,
        "checkpoint_hparams_loaded": True,
        "checkpoint_hparams_complete_for_instantiation": True,
        "checkpoint_target_joint_nf": 32,
        "checkpoint_target_hidden_nf": 128,
        "checkpoint_target_n_layers": 5,
        "checkpoint_target_mode": "pocket_conditioning",
        "checkpoint_target_pocket_representation": "full-atom",
        "checkpoint_target_atom_feature_dim": 10,
        "checkpoint_target_residue_feature_dim": 10,
        "checkpoint_target_egnn_blocks": 5,
        "current_config_joint_nf": 128,
        "current_config_hidden_nf": 256,
        "current_config_n_layers": 6,
        "best_config_candidate_path": str(BEST_CONFIG_CANDIDATE_PATH),
        "best_config_candidate_loaded": True,
        "safe_config_override_supported": False,
        "config_preview_written": True,
        "checkpoint_compatible_instantiation_feasible": True,
        "design_status": "wrapper_needed_for_checkpoint_compatible_instantiation",
        "recommended_next_step": "checkpoint_compatible_instantiation_wrapper_prototype",
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "masked_loss_smoke_allowed": False,
        "pretrained_masked_loss_smoke_allowed": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
        "all_checks_passed": True,
    }
    blockers = [f"step11c_{key}_invalid:{manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    preview_expected = {
        "target_mode": "pocket_conditioning",
        "target_pocket_representation": "full-atom",
        "target_atom_feature_dim": 10,
        "target_residue_feature_dim": 10,
        "target_egnn_blocks": 5,
        "expected_checkpoint_state_dict_key_count": 122,
    }
    blockers.extend(
        f"step11c_preview_{key}_invalid:{preview.get(key)!r}"
        for key, value in preview_expected.items()
        if preview.get(key) != value
    )
    target_egnn = preview.get("target_egnn_params", {})
    if target_egnn != {"joint_nf": 32, "hidden_nf": 128, "n_layers": 5}:
        blockers.append(f"step11c_preview_target_egnn_invalid:{target_egnn!r}")
    if preview.get("expected_shape_match_goal", {}).get("shape_matched_ratio_minimum") != SHAPE_MATCH_GOAL:
        blockers.append("step11c_preview_shape_goal_invalid")
    if any(manifest.get(key) is True for key in ["formal_training_allowed", "finetune_allowed", "masked_loss_smoke_allowed"]):
        blockers.append("step11c_allows_forbidden_next_stage")
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_checkpoint_shape_reference_v0(checkpoint_path: str | Path = CHECKPOINT_PATH) -> dict[str, Any]:
    path = Path(checkpoint_path)
    result: dict[str, Any] = {
        "checkpoint_present": path.is_file(),
        "checkpoint_path": str(path),
        "checkpoint_sha256": _sha256(path) if path.is_file() else "",
        "checkpoint_size_bytes": path.stat().st_size if path.is_file() else 0,
        "checkpoint_payload_type": "",
        "has_state_dict": False,
        "has_hyper_parameters": False,
        "state_dict_key_count": 0,
        "checkpoint_shape_map": {},
        "checkpoint_inferred_architecture": {},
        "checkpoint_target_fields": {},
        "blocking_reasons": [],
    }
    if not path.is_file():
        result["blocking_reasons"].append("checkpoint_missing")
        return result
    try:
        payload = torch.load(path, map_location="cpu")
    except Exception as exc:
        result["blocking_reasons"].append(f"checkpoint_read_failed:{type(exc).__name__}:{exc}")
        return result
    result["checkpoint_payload_type"] = type(payload).__name__
    if not isinstance(payload, dict):
        result["blocking_reasons"].append("checkpoint_payload_not_dict")
        return result
    state_dict = payload.get("state_dict")
    hparams = payload.get("hyper_parameters")
    result["has_state_dict"] = isinstance(state_dict, dict)
    result["has_hyper_parameters"] = isinstance(hparams, dict)
    if not isinstance(state_dict, dict):
        result["blocking_reasons"].append("checkpoint_state_dict_missing")
        return result
    shape_map = {key: _shape(value) for key, value in state_dict.items() if torch.is_tensor(value)}
    architecture = infer_architecture_from_state_shapes_v0(shape_map, "checkpoint")
    result["state_dict_key_count"] = len(shape_map)
    result["checkpoint_shape_map"] = shape_map
    result["checkpoint_inferred_architecture"] = architecture
    egnn_params = _get_child(hparams, "egnn_params", {}) if isinstance(hparams, dict) else {}
    result["checkpoint_target_fields"] = {
        "joint_nf": _get_child(egnn_params, "joint_nf"),
        "hidden_nf": _get_child(egnn_params, "hidden_nf"),
        "n_layers": _get_child(egnn_params, "n_layers"),
        "mode": hparams.get("mode") if isinstance(hparams, dict) else "",
        "pocket_representation": hparams.get("pocket_representation") if isinstance(hparams, dict) else "",
        "atom_feature_dim": architecture.get("atom_encoder_input_dim"),
        "residue_feature_dim": architecture.get("residue_encoder_input_dim"),
        "egnn_blocks": architecture.get("egnn_block_count"),
    }
    return result


def load_config_preview_v0(config_preview_path: str | Path = CONFIG_PREVIEW_PATH) -> dict[str, Any]:
    preview = _load_json(config_preview_path)
    blockers = []
    if preview.get("target_egnn_params", {}).get("joint_nf") != 32:
        blockers.append("preview_joint_nf_not_32")
    if preview.get("target_egnn_params", {}).get("hidden_nf") != 128:
        blockers.append("preview_hidden_nf_not_128")
    if preview.get("target_egnn_params", {}).get("n_layers") != 5:
        blockers.append("preview_n_layers_not_5")
    if preview.get("target_mode") != "pocket_conditioning":
        blockers.append("preview_mode_not_pocket_conditioning")
    if preview.get("target_pocket_representation") != "full-atom":
        blockers.append("preview_pocket_representation_not_full_atom")
    if preview.get("target_atom_feature_dim") != 10:
        blockers.append("preview_atom_feature_dim_not_10")
    if preview.get("target_residue_feature_dim") != 10:
        blockers.append("preview_residue_feature_dim_not_10")
    if preview.get("target_egnn_blocks") != 5:
        blockers.append("preview_egnn_blocks_not_5")
    if preview.get("expected_checkpoint_state_dict_key_count") != 122:
        blockers.append("preview_expected_key_count_not_122")
    if preview.get("expected_shape_match_goal", {}).get("shape_matched_ratio_minimum") != SHAPE_MATCH_GOAL:
        blockers.append("preview_shape_goal_not_0_8")
    return {"config_preview_loaded": not blockers, "preview": preview, "blocking_reasons": blockers}


def build_checkpoint_compatible_config_v0(
    preview: dict[str, Any],
    best_candidate_config_path: str | Path = BEST_CONFIG_CANDIDATE_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    path = Path(best_candidate_config_path)
    candidate = _load_yaml(path) if path.is_file() else {}
    if not candidate:
        blockers.append("best_candidate_config_missing_or_empty")
    config = copy.deepcopy(candidate)
    overrides = {
        "mode": preview["target_mode"],
        "pocket_representation": preview["target_pocket_representation"],
        "virtual_nodes": False,
        "egnn_params.joint_nf": preview["target_egnn_params"]["joint_nf"],
        "egnn_params.hidden_nf": preview["target_egnn_params"]["hidden_nf"],
        "egnn_params.n_layers": preview["target_egnn_params"]["n_layers"],
    }
    config["mode"] = overrides["mode"]
    config["pocket_representation"] = overrides["pocket_representation"]
    config["virtual_nodes"] = overrides["virtual_nodes"]
    config.setdefault("egnn_params", {})
    config["egnn_params"]["joint_nf"] = overrides["egnn_params.joint_nf"]
    config["egnn_params"]["hidden_nf"] = overrides["egnn_params.hidden_nf"]
    config["egnn_params"]["n_layers"] = overrides["egnn_params.n_layers"]
    config["egnn_params"]["device"] = "cpu"
    flattened = {
        "mode": config.get("mode"),
        "pocket_representation": config.get("pocket_representation"),
        "virtual_nodes": config.get("virtual_nodes"),
        "egnn_params.joint_nf": config.get("egnn_params", {}).get("joint_nf"),
        "egnn_params.hidden_nf": config.get("egnn_params", {}).get("hidden_nf"),
        "egnn_params.n_layers": config.get("egnn_params", {}).get("n_layers"),
        "diffusion_params.diffusion_steps": config.get("diffusion_params", {}).get("diffusion_steps"),
        "diffusion_params.diffusion_loss_type": config.get("diffusion_params", {}).get("diffusion_loss_type"),
    }
    unresolved_fields = [
        "dataset_info mapping for 10-dim full-atom",
        "atom_encoder / decoder feature contract",
        "residue feature contract",
        "node_histogram source and shape",
    ]
    required = [
        ("mode", "pocket_conditioning"),
        ("pocket_representation", "full-atom"),
        ("egnn_params.joint_nf", 32),
        ("egnn_params.hidden_nf", 128),
        ("egnn_params.n_layers", 5),
    ]
    for key, expected in required:
        if flattened.get(key) != expected:
            blockers.append(f"compatible_config_{key}_invalid:{flattened.get(key)!r}")
    return {
        "compatible_config_built": not blockers,
        "compatible_config_source": str(path),
        "compatible_config": config,
        "compatible_config_overrides": overrides,
        "compatible_config_flattened_relevant_fields": flattened,
        "unresolved_fields": unresolved_fields,
        "blocking_reasons": blockers,
    }


def build_checkpoint_compatible_input_contract_v0(
    checkpoint_reference: dict[str, Any],
    preview: dict[str, Any],
    compatible_config: dict[str, Any],
) -> dict[str, Any]:
    target_atom_dim = int(preview["target_atom_feature_dim"])
    target_residue_dim = int(preview["target_residue_feature_dim"])
    return {
        "input_contract_built": True,
        "target_atom_feature_dim": target_atom_dim,
        "target_residue_feature_dim": target_residue_dim,
        "target_ligand_feature_dim": target_atom_dim,
        "target_pocket_feature_dim": target_residue_dim,
        "current_default_atom_feature_dim": 11,
        "current_default_crossdock_full_contract_used": False,
        "contract_source": "checkpoint_state_dict_shape_inference",
        "feature_semantics_known": False,
        "feature_semantics_status": "shape_only_contract_for_instantiation_smoke",
        "dataset_info_strategy": "build_minimal_10d_shape_contract_in_memory",
        "one_hot_strategy": "synthetic_10d_one_hot_for_shape_smoke",
        "node_histogram_strategy": "synthetic_placeholder_for_constructor_compatibility",
        "synthetic_forward_candidate_safe": True,
        "synthetic_forward_candidate_scope": "shape_and_finiteness_only",
        "checkpoint_state_dict_key_count": checkpoint_reference["state_dict_key_count"],
        "compatible_config_mode": compatible_config["compatible_config_flattened_relevant_fields"].get("mode"),
        "risks": [
            "10d feature semantics may not match current 11d constants",
            "shape smoke is not training data smoke",
            "strict load may still fail if constructor has hidden assumptions",
        ],
    }


def _constructor_config_from_compatible_config(
    compatible_config: dict[str, Any],
    dataset_name: str,
    device: str,
    node_histogram: list[list[float]] | None = None,
) -> dict[str, Any]:
    config = compatible_config["compatible_config"]
    egnn_params = dict(config.get("egnn_params", {}), device=device)
    eval_params = dict(config.get("eval_params", {}), smiles_file=None)
    return {
        "outdir": "data/derived/covalent_small/checkpoint_compatible_instantiation_wrapper_v0/no_model_outputs",
        "dataset": dataset_name,
        "datadir": "data/derived/covalent_small/checkpoint_compatible_instantiation_wrapper_v0/no_training_data_dir_used",
        "batch_size": 3,
        "lr": float(config.get("lr", 1.0e-3)),
        "egnn_params": egnn_params,
        "diffusion_params": dict(config.get("diffusion_params", {})),
        "num_workers": 0,
        "augment_noise": 0,
        "augment_rotation": False,
        "clip_grad": False,
        "eval_epochs": int(config.get("eval_epochs", 50)),
        "eval_params": eval_params,
        "visualize_sample_epoch": int(config.get("visualize_sample_epoch", 50)),
        "visualize_chain_epoch": int(config.get("visualize_chain_epoch", 50)),
        "auxiliary_loss": False,
        "loss_params": dict(config.get("loss_params", {})),
        "mode": config.get("mode", "pocket_conditioning"),
        "node_histogram": node_histogram or [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        ],
        "pocket_representation": config.get("pocket_representation", "full-atom"),
        "virtual_nodes": False,
    }


def _temporary_10d_dataset_info() -> dict[str, Any]:
    constants = importlib.import_module("constants")
    dataset_info = copy.deepcopy(constants.dataset_params["crossdock"])
    dataset_info["aa_encoder"] = dict(dataset_info["atom_encoder"])
    dataset_info["aa_decoder"] = list(dataset_info["atom_decoder"])
    dataset_info["aa_hist"] = dict(dataset_info["atom_hist"])
    return dataset_info


def _instantiate_model_with_temp_dataset(config_dict: dict[str, Any], dataset_info: dict[str, Any], device: str) -> Any:
    constants = importlib.import_module("constants")
    previous = constants.dataset_params.get(config_dict["dataset"])
    constants.dataset_params[config_dict["dataset"]] = dataset_info
    try:
        patch_biopython_polypeptide_three_to_one()
        module = importlib.import_module(MODEL_MODULE_NAME)
        model_class = getattr(module, MODEL_CLASS_NAME)
        with contextlib.redirect_stdout(io.StringIO()):
            model = model_class(**_constructor_kwargs(config_dict))
        model = model.to(torch.device(device))
        model.eval()
        return model
    finally:
        if previous is None:
            constants.dataset_params.pop(config_dict["dataset"], None)
        else:
            constants.dataset_params[config_dict["dataset"]] = previous


def _shape_map_from_model(model: Any) -> dict[str, list[int]]:
    return {key: _shape(value) for key, value in model.state_dict().items() if torch.is_tensor(value)}


def _category_for_key(key: str) -> str:
    if "atom_encoder" in key:
        return "atom_encoder"
    if "atom_decoder" in key:
        return "atom_decoder"
    if "residue_encoder" in key:
        return "residue_encoder"
    if "residue_decoder" in key:
        return "residue_decoder"
    if "edge_mlp" in key:
        return "egnn_edge_mlp"
    if "node_mlp" in key:
        return "egnn_node_mlp"
    if "coord_mlp" in key:
        return "egnn_coord_mlp"
    if "att_mlp" in key:
        return "egnn_att_mlp"
    if "cross_product_mlp" in key:
        return "egnn_cross_product_mlp"
    if "egnn" in key:
        return "egnn_other"
    return "other"


def build_checkpoint_compatible_shape_match_table_v0(
    checkpoint_shape_map: dict[str, list[int]],
    model_shape_map: dict[str, list[int]],
) -> list[dict[str, Any]]:
    rows = []
    for key in sorted(set(checkpoint_shape_map) | set(model_shape_map)):
        checkpoint_shape = checkpoint_shape_map.get(key)
        model_shape = model_shape_map.get(key)
        if checkpoint_shape is None:
            status = "missing_in_checkpoint"
            reason = "model_key_absent_from_checkpoint"
        elif model_shape is None:
            status = "unexpected_in_checkpoint"
            reason = "checkpoint_key_absent_from_model"
        elif list(checkpoint_shape) == list(model_shape):
            status = "shape_matched"
            reason = "same_shape"
        else:
            status = "shape_mismatched"
            reason = "different_shape"
        rows.append(
            {
                "key": key,
                "category": _category_for_key(key),
                "checkpoint_shape": json.dumps(checkpoint_shape or []),
                "model_shape": json.dumps(model_shape or []),
                "status": status,
                "inferred_reason": reason,
                "checkpoint_numel": _numel(checkpoint_shape),
                "model_numel": _numel(model_shape),
            }
        )
    return rows


def _shape_counts(checkpoint_shape_map: dict[str, list[int]], model_shape_map: dict[str, list[int]]) -> dict[str, Any]:
    matched_keys = sorted(set(checkpoint_shape_map) & set(model_shape_map))
    shape_matched = [key for key in matched_keys if checkpoint_shape_map[key] == model_shape_map[key]]
    incompatible = [key for key in matched_keys if checkpoint_shape_map[key] != model_shape_map[key]]
    missing = [key for key in model_shape_map if key not in checkpoint_shape_map]
    unexpected = [key for key in checkpoint_shape_map if key not in model_shape_map]
    denominator = len(checkpoint_shape_map) or 1
    return {
        "matched_key_count": len(matched_keys),
        "shape_matched_key_count": len(shape_matched),
        "shape_matched_ratio": len(shape_matched) / denominator,
        "incompatible_shape_count": len(incompatible),
        "missing_key_count": len(missing),
        "unexpected_key_count": len(unexpected),
    }


def optional_checkpoint_compatible_forward_smoke_v0(model: Any, input_contract: dict[str, Any], device: str) -> dict[str, Any]:
    if not input_contract.get("synthetic_forward_candidate_safe"):
        return {
            "forward_smoke_attempted": False,
            "forward_smoke_success": False,
            "output_finite": False,
            "forward_smoke_skip_reason": "synthetic_candidate_inputs_not_approved_for_shape_smoke",
        }
    try:
        lig_count = 4
        pocket_count = 5
        ligand_one_hot = torch.zeros(lig_count, input_contract["target_ligand_feature_dim"], device=device)
        pocket_one_hot = torch.zeros(pocket_count, input_contract["target_pocket_feature_dim"], device=device)
        ligand_one_hot[torch.arange(lig_count, device=device), torch.arange(lig_count, device=device)] = 1.0
        pocket_one_hot[torch.arange(pocket_count, device=device), torch.arange(pocket_count, device=device)] = 1.0
        batch = {
            "lig_coords": torch.randn(lig_count, 3, device=device),
            "lig_one_hot": ligand_one_hot,
            "lig_mask": torch.zeros(lig_count, dtype=torch.long, device=device),
            "pocket_coords": torch.randn(pocket_count, 3, device=device),
            "pocket_one_hot": pocket_one_hot,
            "pocket_mask": torch.zeros(pocket_count, dtype=torch.long, device=device),
            "num_lig_atoms": torch.tensor([lig_count], dtype=torch.long, device=device),
            "num_pocket_nodes": torch.tensor([pocket_count], dtype=torch.long, device=device),
            "lig_fixed": torch.zeros(lig_count, dtype=torch.bool, device=device),
        }
        model.eval()
        with torch.no_grad():
            output = model(batch)
        inspected = _inspect_forward_output(output)
        return {
            "forward_smoke_attempted": True,
            "forward_smoke_success": bool(inspected["finite_tensor_outputs"]),
            "output_finite": bool(inspected["finite_tensor_outputs"]),
            "forward_output_type": inspected["output_type"],
            "forward_tensor_output_shapes": inspected["tensor_output_shapes"],
            "forward_smoke_skip_reason": "",
        }
    except Exception as exc:
        return {
            "forward_smoke_attempted": True,
            "forward_smoke_success": False,
            "output_finite": False,
            "forward_smoke_skip_reason": f"forward_smoke_failed:{type(exc).__name__}:{exc}",
        }


def build_checkpoint_compatible_instantiation_decision_v0(
    wrapper_result: dict[str, Any],
    forward_result: dict[str, Any],
) -> dict[str, Any]:
    model_instantiated = bool(wrapper_result.get("model_instantiated"))
    ratio = float(wrapper_result.get("shape_matched_ratio", 0.0))
    if model_instantiated and ratio >= 0.95:
        instantiation_status = "checkpoint_compatible_model_instantiated"
        checkpoint_load_smoke_allowed = True
        next_step = "checkpoint_compatible_pretrained_load_smoke"
    elif model_instantiated and ratio >= SHAPE_MATCH_GOAL:
        instantiation_status = "mostly_checkpoint_compatible_model_instantiated"
        checkpoint_load_smoke_allowed = True
        next_step = "checkpoint_compatible_pretrained_load_smoke_with_known_mismatches"
    elif model_instantiated:
        instantiation_status = "partial_checkpoint_compatible_instantiation"
        checkpoint_load_smoke_allowed = False
        next_step = "checkpoint_compatible_wrapper_repair"
    else:
        instantiation_status = "checkpoint_compatible_instantiation_blocked"
        checkpoint_load_smoke_allowed = False
        next_step = "checkpoint_compatible_wrapper_debug"
    return {
        "instantiation_status": instantiation_status,
        "checkpoint_load_smoke_allowed": checkpoint_load_smoke_allowed,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "masked_loss_smoke_allowed": False,
        "pretrained_masked_loss_smoke_allowed": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
        "recommended_next_step": next_step,
    }


def instantiate_checkpoint_compatible_model_v0(
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_preview_path: str | Path = CONFIG_PREVIEW_PATH,
    device: str = "cpu",
) -> dict[str, Any]:
    blockers: list[str] = []
    requested_device = device
    resolved_device = _resolve_device(device)
    try:
        step11c_validated = validate_step11c_outputs_v0()
    except Exception as exc:
        step11c_validated = False
        blockers.append(f"step11c_validation_failed:{type(exc).__name__}:{exc}")
    checkpoint_reference = load_checkpoint_shape_reference_v0(checkpoint_path)
    preview_result = load_config_preview_v0(config_preview_path)
    preview = preview_result.get("preview", {})
    compatible_config = (
        build_checkpoint_compatible_config_v0(preview, BEST_CONFIG_CANDIDATE_PATH)
        if preview
        else {"compatible_config_built": False, "blocking_reasons": ["config_preview_missing"]}
    )
    input_contract = (
        build_checkpoint_compatible_input_contract_v0(checkpoint_reference, preview, compatible_config)
        if compatible_config.get("compatible_config_built")
        else {"input_contract_built": False, "blocking_reasons": ["compatible_config_not_built"]}
    )
    blockers.extend(checkpoint_reference.get("blocking_reasons", []))
    blockers.extend(preview_result.get("blocking_reasons", []))
    blockers.extend(compatible_config.get("blocking_reasons", []))
    blockers.extend(input_contract.get("blocking_reasons", []))

    result: dict[str, Any] = {
        "wrapper_invoked": True,
        "step11c_validated": step11c_validated,
        "checkpoint_reference_loaded": checkpoint_reference["has_state_dict"],
        "config_preview_loaded": preview_result.get("config_preview_loaded", False),
        "compatible_config_built": compatible_config.get("compatible_config_built", False),
        "input_contract_built": input_contract.get("input_contract_built", False),
        "model_instantiation_attempted": False,
        "model_instantiated": False,
        "model_class": MODEL_CLASS_NAME,
        "requested_device": requested_device,
        "resolved_device": resolved_device,
        "trainable_parameter_count": 0,
        "model_state_dict_key_count": 0,
        "matched_key_count": 0,
        "shape_matched_key_count": 0,
        "shape_matched_ratio": 0.0,
        "incompatible_shape_count": 0,
        "missing_key_count": 0,
        "unexpected_key_count": 0,
        "checkpoint_inferred_architecture": checkpoint_reference.get("checkpoint_inferred_architecture", {}),
        "instantiated_inferred_architecture": {},
        "target_joint_nf": preview.get("target_egnn_params", {}).get("joint_nf"),
        "target_hidden_nf": preview.get("target_egnn_params", {}).get("hidden_nf"),
        "target_n_layers": preview.get("target_egnn_params", {}).get("n_layers"),
        "target_atom_feature_dim": preview.get("target_atom_feature_dim"),
        "target_residue_feature_dim": preview.get("target_residue_feature_dim"),
        "target_egnn_blocks": preview.get("target_egnn_blocks"),
        "reached_shape_match_goal": False,
        "wrapper_status": "checkpoint_compatible_instantiation_blocked",
        "blocking_reasons": blockers,
        "model_shape_map": {},
        "checkpoint_shape_map": checkpoint_reference.get("checkpoint_shape_map", {}),
        "input_contract": input_contract,
        "compatible_config": compatible_config,
        "checkpoint_reference": checkpoint_reference,
    }
    model = None
    if step11c_validated and result["checkpoint_reference_loaded"] and result["config_preview_loaded"] and result["compatible_config_built"]:
        result["model_instantiation_attempted"] = True
        config_dict = _constructor_config_from_compatible_config(compatible_config, TEMP_DATASET_NAME, resolved_device)
        try:
            model = _instantiate_model_with_temp_dataset(config_dict, _temporary_10d_dataset_info(), resolved_device)
            model_shape_map = _shape_map_from_model(model)
            counts = _shape_counts(result["checkpoint_shape_map"], model_shape_map)
            result.update(counts)
            result["model_instantiated"] = True
            result["model_state_dict_key_count"] = len(model_shape_map)
            result["trainable_parameter_count"] = int(sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad))
            result["instantiated_inferred_architecture"] = infer_architecture_from_state_shapes_v0(model_shape_map, "checkpoint_compatible_wrapper")
            result["model_shape_map"] = model_shape_map
            result["_model_for_optional_forward"] = model
            result["reached_shape_match_goal"] = result["shape_matched_ratio"] >= SHAPE_MATCH_GOAL
            if result["shape_matched_ratio"] >= SHAPE_MATCH_GOAL:
                result["wrapper_status"] = "checkpoint_compatible_instantiation_proven"
            else:
                result["wrapper_status"] = "checkpoint_compatible_instantiation_partial"
        except Exception as exc:
            result["blocking_reasons"].append(f"model_instantiation_failed:{type(exc).__name__}:{exc}")
            if any("feature" in reason for reason in result["blocking_reasons"]):
                result["wrapper_status"] = "feature_contract_wrapper_repair_needed"
    return result


def build_checkpoint_compatible_instantiation_wrapper_v0(
    device: str = "cpu",
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_preview_path: str | Path = CONFIG_PREVIEW_PATH,
) -> dict[str, Any]:
    wrapper_result = instantiate_checkpoint_compatible_model_v0(checkpoint_path, config_preview_path, device)
    shape_table = build_checkpoint_compatible_shape_match_table_v0(
        wrapper_result.get("checkpoint_shape_map", {}),
        wrapper_result.get("model_shape_map", {}),
    )
    forward_result = {
        "forward_smoke_attempted": False,
        "forward_smoke_success": False,
        "output_finite": False,
        "forward_smoke_skip_reason": "deferred_until_shape_match_goal_reached",
    }
    model_for_forward = wrapper_result.pop("_model_for_optional_forward", None)
    if (
        model_for_forward is not None
        and wrapper_result.get("model_instantiated")
        and wrapper_result.get("shape_matched_ratio", 0.0) >= SHAPE_MATCH_GOAL
    ):
        forward_result = optional_checkpoint_compatible_forward_smoke_v0(
            model_for_forward,
            wrapper_result["input_contract"],
            wrapper_result["resolved_device"],
        )
    decision = build_checkpoint_compatible_instantiation_decision_v0(wrapper_result, forward_result)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    blocking_reasons = sorted(set(wrapper_result.get("blocking_reasons", [])))
    if source_modified:
        blocking_reasons.append("original_source_files_modified")
    if forbidden_artifacts:
        blocking_reasons.append("forbidden_artifacts_created")
    all_checks_passed = bool(
        wrapper_result.get("step11c_validated")
        and wrapper_result.get("checkpoint_reference_loaded")
        and wrapper_result.get("config_preview_loaded")
        and wrapper_result.get("compatible_config_built")
        and wrapper_result.get("input_contract_built")
        and wrapper_result.get("model_instantiation_attempted")
        and wrapper_result.get("model_instantiated")
        and wrapper_result.get("shape_matched_ratio", 0.0) > PREVIOUS_SHAPE_MATCH_RATIO
        and not source_modified
        and not forbidden_artifacts
    )
    checkpoint_reference = wrapper_result["checkpoint_reference"]
    compatible_config = wrapper_result["compatible_config"]
    input_contract = wrapper_result["input_contract"]
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11c_validated": wrapper_result["step11c_validated"],
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": checkpoint_reference.get("checkpoint_sha256", ""),
        "config_preview_path": str(config_preview_path),
        "compatible_config_built": wrapper_result["compatible_config_built"],
        "compatible_config_source": compatible_config.get("compatible_config_source", ""),
        "input_contract_built": wrapper_result["input_contract_built"],
        "target_joint_nf": wrapper_result["target_joint_nf"],
        "target_hidden_nf": wrapper_result["target_hidden_nf"],
        "target_n_layers": wrapper_result["target_n_layers"],
        "target_mode": input_contract.get("compatible_config_mode", "pocket_conditioning"),
        "target_pocket_representation": "full-atom",
        "target_atom_feature_dim": wrapper_result["target_atom_feature_dim"],
        "target_residue_feature_dim": wrapper_result["target_residue_feature_dim"],
        "target_egnn_blocks": wrapper_result["target_egnn_blocks"],
        "model_instantiation_attempted": wrapper_result["model_instantiation_attempted"],
        "model_instantiated": wrapper_result["model_instantiated"],
        "model_class": wrapper_result["model_class"],
        "requested_device": wrapper_result["requested_device"],
        "resolved_device": wrapper_result["resolved_device"],
        "model_state_dict_key_count": wrapper_result["model_state_dict_key_count"],
        "checkpoint_state_dict_key_count": checkpoint_reference.get("state_dict_key_count", 0),
        "matched_key_count": wrapper_result["matched_key_count"],
        "shape_matched_key_count": wrapper_result["shape_matched_key_count"],
        "shape_matched_ratio": wrapper_result["shape_matched_ratio"],
        "previous_shape_matched_ratio": PREVIOUS_SHAPE_MATCH_RATIO,
        "shape_match_improved_over_step11a": wrapper_result["shape_matched_ratio"] > PREVIOUS_SHAPE_MATCH_RATIO,
        "incompatible_shape_count": wrapper_result["incompatible_shape_count"],
        "missing_key_count": wrapper_result["missing_key_count"],
        "unexpected_key_count": wrapper_result["unexpected_key_count"],
        "checkpoint_inferred_architecture": wrapper_result["checkpoint_inferred_architecture"],
        "instantiated_inferred_architecture": wrapper_result["instantiated_inferred_architecture"],
        "reached_shape_match_goal": wrapper_result["reached_shape_match_goal"],
        "wrapper_status": wrapper_result["wrapper_status"],
        "forward_smoke_attempted": forward_result["forward_smoke_attempted"],
        "forward_smoke_success": forward_result["forward_smoke_success"],
        "output_finite": forward_result["output_finite"],
        "forward_smoke_skip_reason": forward_result["forward_smoke_skip_reason"],
        **decision,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "original_source_files_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blocking_reasons,
    }
    return {
        "manifest": manifest,
        "shape_table": shape_table,
        "input_contract": input_contract,
        "report_sections": {
            "step11c": {"step11c_validated": wrapper_result["step11c_validated"]},
            "checkpoint_reference": checkpoint_reference,
            "config_preview": load_config_preview_v0(config_preview_path),
            "compatible_config": compatible_config,
            "input_contract": input_contract,
            "model_instantiation": wrapper_result,
            "shape_match_analysis": {
                "shape_table_row_count": len(shape_table),
                "matched_key_count": wrapper_result["matched_key_count"],
                "shape_matched_key_count": wrapper_result["shape_matched_key_count"],
                "shape_matched_ratio": wrapper_result["shape_matched_ratio"],
                "reached_shape_match_goal": wrapper_result["reached_shape_match_goal"],
            },
            "optional_forward_smoke": forward_result,
            "decision": decision,
            "safety_boundary": {
                "backward_called": False,
                "optimizer_created": False,
                "optimizer_step_called": False,
                "training_step_called": False,
                "trainer_fit_called": False,
                "checkpoint_saved": False,
                "model_saved": False,
                "original_source_files_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
        },
    }
