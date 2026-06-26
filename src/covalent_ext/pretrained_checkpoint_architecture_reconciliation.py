from __future__ import annotations

import hashlib
import json
import re
import subprocess
from argparse import Namespace
from collections import Counter
from pathlib import Path
from typing import Any

import torch

from covalent_ext.pretrained_checkpoint_load_smoke import (
    MANIFEST_JSON as STEP11A_MANIFEST_JSON,
    SUMMARY_MD as STEP11A_SUMMARY_MD,
    _sha256,
    instantiate_model_for_pretrained_load_v0,
)


STAGE = "pretrained_checkpoint_architecture_reconciliation_v0"
PREVIOUS_STAGE = "pretrained_checkpoint_load_smoke_v0"
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
MODEL_CONFIG_PATH = Path("configs/crossdock_fullatom_cond.yml")
OUTPUT_ROOT = Path("data/derived/covalent_small/pretrained_checkpoint_architecture_reconciliation_v0")
REPORT_CSV = OUTPUT_ROOT / "pretrained_checkpoint_architecture_reconciliation_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "pretrained_checkpoint_architecture_reconciliation_manifest.json"
MISMATCH_TABLE_CSV = OUTPUT_ROOT / "pretrained_checkpoint_shape_mismatch_table.csv"
SUMMARY_MD = Path("docs/pretrained_checkpoint_architecture_reconciliation_v0_summary.md")
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
RELEVANT_KEYWORDS = (
    "hidden",
    "hidden_nf",
    "nf",
    "n_layers",
    "layers",
    "n_dims",
    "in_node_nf",
    "context_node_nf",
    "atom",
    "atom_type",
    "atom_types",
    "ligand",
    "pocket",
    "feature",
    "features",
    "one_hot",
    "conditioning",
    "fullatom",
    "joint",
    "dynamics",
    "egnn",
    "decoder",
    "encoder",
    "mode",
    "representation",
)


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _text_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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


def _shape(value: Any) -> list[int]:
    return [int(dim) for dim in value.shape] if torch.is_tensor(value) else []


def _numel(shape: list[int] | None) -> int:
    if not shape:
        return 0
    total = 1
    for dim in shape:
        total *= int(dim)
    return total


def _safe_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _short_repr(value: Any, limit: int = 180) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def flatten_metadata_v0(value: Any, prefix: str = "", max_depth: int = 6) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    if max_depth < 0:
        flattened[prefix or "value"] = f"<max_depth:{type(value).__name__}>"
        return flattened
    if isinstance(value, Namespace):
        value = vars(value)
    if isinstance(value, dict):
        for key, child in value.items():
            child_key = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(flatten_metadata_v0(child, child_key, max_depth=max_depth - 1))
        return flattened
    if isinstance(value, (list, tuple)):
        key = prefix or "value"
        flattened[f"{key}.__len__"] = len(value)
        flattened[f"{key}.__sample_repr__"] = _short_repr(list(value[:5]))
        return flattened
    if _safe_scalar(value):
        flattened[prefix or "value"] = value
    else:
        flattened[prefix or "value"] = _short_repr(value)
    return flattened


def _relevant_fields(flattened: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in flattened.items()
        if any(keyword in key.lower() for keyword in RELEVANT_KEYWORDS)
    }


def _load_yaml_config(path: Path) -> dict[str, Any]:
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def validate_step11a_outputs_v0() -> bool:
    blockers: list[str] = []
    if not STEP11A_MANIFEST_JSON.is_file() or not STEP11A_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11A outputs are missing")
    manifest = _load_json(STEP11A_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "first_checkpointed_training_dry_run_review_v0",
        "step10x_review_passed": True,
        "pretrained_checkpoint_present": True,
        "checkpoint_loaded": True,
        "checkpoint_payload_type": "dict",
        "has_state_dict": True,
        "state_dict_key_count": 122,
        "matched_key_count": 122,
        "shape_matched_key_count": 7,
        "shape_matched_ratio": 0.05737704918032787,
        "incompatible_shape_count": 115,
        "strict_load_success": False,
        "nonstrict_load_success": True,
        "pretrained_partial_shape_load_success": True,
        "pretrained_full_architecture_compatible": False,
        "pretrained_weights_loaded": False,
        "shape_mismatch_detected": True,
        "architecture_config_mismatch_suspected": True,
        "forward_smoke_success": True,
        "output_finite": True,
        "all_checks_passed": True,
        "all_checks_passed_meaning": "smoke_completed_and_mismatch_detected",
        "recommended_next_step": "pretrained_checkpoint_architecture_config_reconciliation",
    }
    for key, expected_value in expected.items():
        actual = manifest.get(key)
        if actual != expected_value:
            blockers.append(f"step11a_{key}_invalid:{actual!r}")
    summary = STEP11A_SUMMARY_MD.read_text(encoding="utf-8")
    if "- pretrained_masked_loss_smoke" in summary:
        blockers.append("step11a_summary_recommends_pretrained_masked_loss_smoke")
    if manifest.get("recommended_next_step") == "pretrained_masked_loss_smoke":
        blockers.append("step11a_manifest_recommends_pretrained_masked_loss_smoke")
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def infer_architecture_from_state_shapes_v0(shape_map: dict[str, list[int]], source_name: str) -> dict[str, Any]:
    block_indices = sorted(
        {
            int(match.group(1))
            for key in shape_map
            for match in [re.search(r"e_block_(\d+)", key)]
            if match
        }
    )

    def shape_for(suffix: str) -> list[int]:
        key = f"ddpm.dynamics.{suffix}"
        return shape_map.get(key, [])

    def first_dim_values(pattern: str) -> list[int]:
        values = []
        for key, shape in shape_map.items():
            if pattern in key and shape:
                values.append(int(shape[0]))
        return sorted(set(values))

    def second_dim_values(pattern: str) -> list[int]:
        values = []
        for key, shape in shape_map.items():
            if pattern in key and len(shape) >= 2:
                values.append(int(shape[1]))
        return sorted(set(values))

    atom_encoder_0 = shape_for("atom_encoder.0.weight")
    atom_encoder_2 = shape_for("atom_encoder.2.weight")
    atom_decoder_0 = shape_for("atom_decoder.0.weight")
    atom_decoder_2 = shape_for("atom_decoder.2.weight")
    residue_encoder_0 = shape_for("residue_encoder.0.weight")
    residue_encoder_2 = shape_for("residue_encoder.2.weight")
    embedding = shape_for("egnn.embedding.weight")
    embedding_out = shape_map.get("ddpm.dynamics.egnn.embedding_out.weight", [])

    architecture = {
        "source_name": source_name,
        "atom_encoder_input_dim": atom_encoder_0[1] if len(atom_encoder_0) >= 2 else None,
        "atom_encoder_hidden_dim_1": atom_encoder_0[0] if atom_encoder_0 else None,
        "atom_encoder_output_dim": atom_encoder_2[0] if atom_encoder_2 else None,
        "atom_decoder_input_dim": atom_decoder_0[1] if len(atom_decoder_0) >= 2 else None,
        "atom_decoder_hidden_dim": atom_decoder_0[0] if atom_decoder_0 else None,
        "atom_decoder_output_dim": atom_decoder_2[0] if atom_decoder_2 else None,
        "residue_encoder_input_dim": residue_encoder_0[1] if len(residue_encoder_0) >= 2 else None,
        "residue_encoder_hidden_dim_1": residue_encoder_0[0] if residue_encoder_0 else None,
        "residue_encoder_output_dim": residue_encoder_2[0] if residue_encoder_2 else None,
        "egnn_embedding_input_dim": embedding[1] if len(embedding) >= 2 else None,
        "egnn_embedding_output_dim": embedding[0] if embedding else None,
        "egnn_embedding_out_input_dim": embedding_out[1] if len(embedding_out) >= 2 else None,
        "egnn_embedding_out_output_dim": embedding_out[0] if embedding_out else None,
        "egnn_block_indices": block_indices,
        "egnn_block_count": len(block_indices),
        "egnn_hidden_dim_candidates": sorted(
            set(
                first_dim_values("egnn.embedding.weight")
                + first_dim_values("edge_mlp.0.weight")
                + first_dim_values("node_mlp.0.weight")
                + first_dim_values("coord_mlp.0.weight")
            )
        ),
        "edge_mlp_input_dim_candidates": second_dim_values("edge_mlp.0.weight"),
        "edge_mlp_hidden_dim_candidates": first_dim_values("edge_mlp.0.weight"),
        "node_mlp_input_dim_candidates": second_dim_values("node_mlp.0.weight"),
        "node_mlp_hidden_dim_candidates": first_dim_values("node_mlp.0.weight"),
        "coord_mlp_input_dim_candidates": second_dim_values("coord_mlp.0.weight"),
        "coord_mlp_hidden_dim_candidates": first_dim_values("coord_mlp.0.weight"),
        "context_or_edge_feature_dim_candidates": second_dim_values("edge_mlp.0.weight")
        + second_dim_values("coord_mlp.0.weight"),
        "known_unparsed_keys_count": len(
            [
                key
                for key in shape_map
                if not any(
                    token in key
                    for token in [
                        "atom_encoder",
                        "atom_decoder",
                        "residue_encoder",
                        "residue_decoder",
                        "egnn",
                        "gamma",
                        "buffer",
                    ]
                )
            ]
        ),
    }
    return architecture


def load_checkpoint_architecture_evidence_v0(checkpoint_path: str | Path = CHECKPOINT_PATH) -> dict[str, Any]:
    path = Path(checkpoint_path)
    result: dict[str, Any] = {
        "checkpoint_path": str(path),
        "checkpoint_present": path.is_file(),
        "checkpoint_sha256": _sha256(path) if path.is_file() else "",
        "checkpoint_size_bytes": path.stat().st_size if path.is_file() else 0,
        "payload_type": "",
        "top_level_keys": [],
        "has_state_dict": False,
        "has_hyper_parameters": False,
        "hyper_parameters_type": "",
        "hyper_parameters_keys": [],
        "hyper_parameters_flattened": {},
        "hyper_parameters_relevant_fields": {},
        "state_dict_key_count": 0,
        "state_dict_shape_map": {},
        "checkpoint_architecture_inferred": {},
        "blocking_reasons": [],
    }
    if not path.is_file():
        result["blocking_reasons"].append("checkpoint_missing")
        return result

    try:
        payload = torch.load(path, map_location="cpu")
        result["payload_type"] = type(payload).__name__
        if not isinstance(payload, dict):
            result["blocking_reasons"].append("checkpoint_payload_not_dict")
            return result
        result["top_level_keys"] = list(payload.keys())
        hparams = payload.get("hyper_parameters")
        result["has_hyper_parameters"] = isinstance(hparams, dict)
        result["hyper_parameters_type"] = type(hparams).__name__
        result["hyper_parameters_keys"] = list(hparams.keys()) if isinstance(hparams, dict) else []
        result["hyper_parameters_flattened"] = flatten_metadata_v0(hparams or {})
        result["hyper_parameters_relevant_fields"] = _relevant_fields(result["hyper_parameters_flattened"])
        state_dict = payload.get("state_dict")
        if not isinstance(state_dict, dict):
            result["blocking_reasons"].append("state_dict_missing")
            return result
        result["has_state_dict"] = True
        shape_map = {key: _shape(value) for key, value in state_dict.items() if torch.is_tensor(value)}
        result["state_dict_key_count"] = len(shape_map)
        result["state_dict_shape_map"] = shape_map
        result["checkpoint_architecture_inferred"] = infer_architecture_from_state_shapes_v0(
            shape_map, "checkpoint"
        )
    except Exception as exc:
        result["blocking_reasons"].append(f"checkpoint_architecture_load_failed:{type(exc).__name__}:{exc}")
    return result


def load_current_config_evidence_v0(config_path: str | Path = MODEL_CONFIG_PATH) -> dict[str, Any]:
    path = Path(config_path)
    result = {
        "config_path": str(path),
        "config_present": path.is_file(),
        "config_top_level_keys": [],
        "config_flattened": {},
        "config_text_sha256": _text_sha256(path) if path.is_file() else "",
        "relevant_config_candidates": {},
        "blocking_reasons": [],
    }
    if not path.is_file():
        result["blocking_reasons"].append("current_config_missing")
        return result
    data = _load_yaml_config(path)
    if not data:
        result["blocking_reasons"].append("current_config_parse_failed")
    flattened = flatten_metadata_v0(data)
    result["config_top_level_keys"] = list(data.keys())
    result["config_flattened"] = flattened
    result["relevant_config_candidates"] = _relevant_fields(flattened)
    return result


def inspect_current_model_architecture_v0(device: str = "cpu") -> dict[str, Any]:
    result = instantiate_model_for_pretrained_load_v0(device=device)
    model = result.get("model")
    shape_map: dict[str, list[int]] = {}
    if model is not None:
        shape_map = {key: _shape(value) for key, value in model.state_dict().items() if torch.is_tensor(value)}
    result["model_state_dict_key_count"] = len(shape_map)
    result["model_state_dict_shape_map"] = shape_map
    result["current_architecture_inferred"] = infer_architecture_from_state_shapes_v0(shape_map, "current_model")
    if model is not None:
        del model
        result["model"] = None
    if result.get("resolved_device", "").startswith("cuda") and torch.cuda.is_available():
        torch.cuda.empty_cache()
    return result


def categorize_state_key_v0(key: str) -> str:
    if "atom_encoder" in key:
        return "atom_encoder"
    if "atom_decoder" in key:
        return "atom_decoder"
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


def infer_shape_mismatch_reason_v0(key: str, checkpoint_shape: list[int], model_shape: list[int]) -> str:
    category = categorize_state_key_v0(key)
    if category in {"atom_encoder", "atom_decoder"}:
        if checkpoint_shape and model_shape and checkpoint_shape[-1] != model_shape[-1]:
            return "ligand_atom_feature_dim_mismatch"
        if checkpoint_shape and model_shape and checkpoint_shape[0] != model_shape[0]:
            return "atom_hidden_dim_mismatch"
        return "output_atom_type_dim_mismatch"
    if category.startswith("egnn"):
        if checkpoint_shape and model_shape and checkpoint_shape[0] != model_shape[0]:
            return "egnn_hidden_dim_mismatch"
        if len(checkpoint_shape) > 1 and len(model_shape) > 1 and checkpoint_shape[1] != model_shape[1]:
            return "edge_feature_or_hidden_dim_mismatch"
    return "unknown_shape_mismatch"


def build_shape_mismatch_table_v0(
    checkpoint_shape_map: dict[str, list[int]],
    model_shape_map: dict[str, list[int]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(set(checkpoint_shape_map) | set(model_shape_map)):
        checkpoint_shape = checkpoint_shape_map.get(key)
        model_shape = model_shape_map.get(key)
        if checkpoint_shape is None:
            status = "missing_in_checkpoint"
            inferred_reason = "egnn_layer_count_mismatch" if "e_block_" in key else "model_key_absent_from_checkpoint"
        elif model_shape is None:
            status = "unexpected_in_checkpoint"
            inferred_reason = "checkpoint_key_absent_from_current_model"
        elif checkpoint_shape == model_shape:
            status = "shape_matched"
            inferred_reason = "shape_matched"
        else:
            status = "shape_mismatched"
            inferred_reason = infer_shape_mismatch_reason_v0(key, checkpoint_shape, model_shape)
        rows.append(
            {
                "key": key,
                "category": categorize_state_key_v0(key),
                "checkpoint_shape": json.dumps(checkpoint_shape or []),
                "model_shape": json.dumps(model_shape or []),
                "status": status,
                "inferred_reason": inferred_reason,
                "checkpoint_numel": _numel(checkpoint_shape),
                "model_numel": _numel(model_shape),
            }
        )
    return rows


def compare_checkpoint_config_current_architecture_v0(
    checkpoint_evidence: dict[str, Any],
    config_evidence: dict[str, Any],
    current_model_evidence: dict[str, Any],
) -> dict[str, Any]:
    checkpoint_arch = checkpoint_evidence["checkpoint_architecture_inferred"]
    current_arch = current_model_evidence["current_architecture_inferred"]
    hparams = checkpoint_evidence["hyper_parameters_relevant_fields"]
    config = config_evidence["relevant_config_candidates"]

    direct_diffs = []
    for key in sorted(set(hparams) & set(config)):
        if hparams[key] != config[key]:
            direct_diffs.append({"key": key, "checkpoint_hparams": hparams[key], "current_config": config[key]})

    likely_root_causes: list[str] = []
    confidence: dict[str, str] = {}
    if checkpoint_arch.get("egnn_hidden_dim_candidates") != current_arch.get("egnn_hidden_dim_candidates"):
        likely_root_causes.append("hidden_dim_mismatch")
        confidence["hidden_dim_mismatch"] = "high"
    if checkpoint_arch.get("atom_encoder_input_dim") != current_arch.get("atom_encoder_input_dim"):
        likely_root_causes.append("atom_feature_dim_mismatch")
        confidence["atom_feature_dim_mismatch"] = "high"
    if checkpoint_arch.get("egnn_block_count") != current_arch.get("egnn_block_count"):
        likely_root_causes.append("egnn_layer_count_mismatch")
        confidence["egnn_layer_count_mismatch"] = "high"
    if checkpoint_arch.get("atom_encoder_hidden_dim_1") != current_arch.get("atom_encoder_hidden_dim_1"):
        likely_root_causes.append("atom_encoder_decoder_dim_mismatch")
        confidence["atom_encoder_decoder_dim_mismatch"] = "medium"

    current_config_not_checkpoint_config = any(
        diff["key"] in {"egnn_params.hidden_nf", "egnn_params.joint_nf", "egnn_params.n_layers"}
        for diff in direct_diffs
    )
    checkpoint_config_recovery_required = bool(likely_root_causes)
    return {
        "checkpoint_inferred_architecture": checkpoint_arch,
        "current_inferred_architecture": current_arch,
        "config_relevant_fields": config,
        "hyper_parameters_relevant_fields": hparams,
        "direct_config_vs_hparams_diffs": direct_diffs,
        "inferred_mismatch_summary": {
            "checkpoint_hidden_candidates": checkpoint_arch.get("egnn_hidden_dim_candidates", []),
            "current_hidden_candidates": current_arch.get("egnn_hidden_dim_candidates", []),
            "checkpoint_atom_feature_dim": checkpoint_arch.get("atom_encoder_input_dim"),
            "current_atom_feature_dim": current_arch.get("atom_encoder_input_dim"),
            "checkpoint_egnn_block_count": checkpoint_arch.get("egnn_block_count"),
            "current_egnn_block_count": current_arch.get("egnn_block_count"),
        },
        "likely_root_causes": likely_root_causes,
        "confidence_by_root_cause": confidence,
        "current_config_not_checkpoint_config": current_config_not_checkpoint_config,
        "checkpoint_config_recovery_required": checkpoint_config_recovery_required,
    }


def search_repo_config_candidates_v0(
    checkpoint_evidence: dict[str, Any] | None = None,
    config_root: str | Path = "configs",
) -> dict[str, Any]:
    checkpoint_fields = (checkpoint_evidence or {}).get("hyper_parameters_relevant_fields", {})
    target = {
        "dataset": checkpoint_fields.get("dataset"),
        "mode": checkpoint_fields.get("mode"),
        "pocket_representation": checkpoint_fields.get("pocket_representation"),
        "egnn_params.joint_nf": checkpoint_fields.get("egnn_params.joint_nf"),
        "egnn_params.hidden_nf": checkpoint_fields.get("egnn_params.hidden_nf"),
        "egnn_params.n_layers": checkpoint_fields.get("egnn_params.n_layers"),
    }
    candidates = []
    for path in sorted(Path(config_root).glob("*.yml")) + sorted(Path(config_root).glob("*.yaml")):
        data = _load_yaml_config(path)
        flattened = flatten_metadata_v0(data)
        relevant = _relevant_fields(flattened)
        score = 0
        reasons = []
        for key, value in target.items():
            if value is None:
                continue
            if flattened.get(key) == value:
                score += 1
                reasons.append(f"matches:{key}")
            else:
                reasons.append(f"differs:{key}:{flattened.get(key)!r}!={value!r}")
        candidates.append(
            {
                "path": str(path),
                "score": score,
                "reasons": reasons,
                "relevant_fields": relevant,
            }
        )
    ranked = sorted(candidates, key=lambda item: (-item["score"], item["path"]))
    best = ranked[0] if ranked else {}
    return {
        "config_candidate_count": len(ranked),
        "config_candidates_ranked": ranked,
        "best_config_candidate_path": best.get("path", ""),
        "best_config_candidate_score": best.get("score", 0),
        "best_config_candidate_reasons": best.get("reasons", []),
    }


def optional_candidate_instantiation_smoke_v0(
    best_config_candidate_path: str | None = None,
    checkpoint_hparams: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "candidate_instantiation_attempted": False,
        "candidate_model_instantiated": False,
        "candidate_shape_matched_key_count": 0,
        "candidate_shape_matched_ratio": None,
        "candidate_incompatible_shape_count": None,
        "candidate_strict_load_potential": False,
        "candidate_config_source": best_config_candidate_path or "",
        "reason": "existing_factory_does_not_support_safe_config_override",
    }


def build_reconciliation_decision_v0(
    comparison: dict[str, Any],
    config_search: dict[str, Any],
    candidate_smoke: dict[str, Any],
) -> dict[str, Any]:
    root_causes = set(comparison["likely_root_causes"])
    if candidate_smoke.get("candidate_model_instantiated") and candidate_smoke.get("candidate_shape_matched_ratio", 0) >= 0.8:
        status = "actionable_config_mismatch_identified"
        next_step = "checkpoint_compatible_model_instantiation_smoke"
    elif root_causes == {"atom_feature_dim_mismatch"}:
        status = "controlled_feature_expansion_needed"
        next_step = "pretrained_weight_expansion_policy_design"
    elif comparison["checkpoint_config_recovery_required"]:
        status = "checkpoint_original_config_recovery_needed"
        next_step = "checkpoint_original_config_model_instantiation_design"
    else:
        status = "manual_checkpoint_config_recovery_required"
        next_step = "manual_pretrained_checkpoint_config_recovery"
    return {
        "reconciliation_status": status,
        "recommended_next_step": next_step,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "masked_loss_smoke_allowed": False,
        "pretrained_masked_loss_smoke_allowed": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
    }


def build_pretrained_checkpoint_architecture_reconciliation_v0(
    device: str = "cpu",
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_path: str | Path = MODEL_CONFIG_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step11a_validated = validate_step11a_outputs_v0()
    except Exception as exc:
        step11a_validated = False
        blockers.append(f"step11a_validation_failed:{type(exc).__name__}:{exc}")
    checkpoint_evidence = load_checkpoint_architecture_evidence_v0(checkpoint_path)
    config_evidence = load_current_config_evidence_v0(config_path)
    current_model = inspect_current_model_architecture_v0(device=device) if step11a_validated else {}
    if checkpoint_evidence["blocking_reasons"]:
        blockers.extend(checkpoint_evidence["blocking_reasons"])
    if config_evidence["blocking_reasons"]:
        blockers.extend(config_evidence["blocking_reasons"])
    if current_model.get("blocking_reasons"):
        blockers.extend(current_model["blocking_reasons"])

    mismatch_table = build_shape_mismatch_table_v0(
        checkpoint_evidence.get("state_dict_shape_map", {}),
        current_model.get("model_state_dict_shape_map", {}),
    )
    status_counts = Counter(row["status"] for row in mismatch_table)
    category_counts = Counter(row["category"] for row in mismatch_table if row["status"] == "shape_mismatched")
    comparison = compare_checkpoint_config_current_architecture_v0(
        checkpoint_evidence, config_evidence, current_model
    )
    config_search = search_repo_config_candidates_v0(checkpoint_evidence)
    candidate_smoke = optional_candidate_instantiation_smoke_v0(
        config_search["best_config_candidate_path"],
        checkpoint_evidence.get("hyper_parameters_relevant_fields", {}),
    )
    decision = build_reconciliation_decision_v0(comparison, config_search, candidate_smoke)

    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_source_files_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")

    shape_matched_key_count = status_counts.get("shape_matched", 0)
    checkpoint_key_count = checkpoint_evidence.get("state_dict_key_count", 0)
    shape_matched_ratio = shape_matched_key_count / checkpoint_key_count if checkpoint_key_count else 0.0
    all_checks_passed = bool(
        step11a_validated
        and checkpoint_evidence.get("has_state_dict")
        and checkpoint_evidence.get("has_hyper_parameters")
        and config_evidence.get("config_present")
        and current_model.get("model_instantiated")
        and mismatch_table
        and decision["reconciliation_status"]
        and not source_modified
        and not forbidden_artifacts
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11a_validated": step11a_validated,
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": checkpoint_evidence.get("checkpoint_sha256", ""),
        "checkpoint_size_bytes": checkpoint_evidence.get("checkpoint_size_bytes", 0),
        "checkpoint_has_hyper_parameters": checkpoint_evidence.get("has_hyper_parameters", False),
        "checkpoint_hyper_parameters_keys": checkpoint_evidence.get("hyper_parameters_keys", []),
        "checkpoint_state_dict_key_count": checkpoint_key_count,
        "current_config_path": str(config_path),
        "current_config_present": config_evidence.get("config_present", False),
        "current_model_instantiated": current_model.get("model_instantiated", False),
        "model_class": current_model.get("model_class", "LigandPocketDDPM"),
        "checkpoint_inferred_architecture": checkpoint_evidence.get("checkpoint_architecture_inferred", {}),
        "current_inferred_architecture": current_model.get("current_architecture_inferred", {}),
        "matched_key_count": status_counts.get("shape_matched", 0) + status_counts.get("shape_mismatched", 0),
        "shape_matched_key_count": shape_matched_key_count,
        "shape_matched_ratio": shape_matched_ratio,
        "incompatible_shape_count": status_counts.get("shape_mismatched", 0),
        "missing_key_count": status_counts.get("missing_in_checkpoint", 0),
        "unexpected_key_count": status_counts.get("unexpected_in_checkpoint", 0),
        "mismatch_category_counts": dict(category_counts),
        "likely_root_causes": comparison["likely_root_causes"],
        "confidence_by_root_cause": comparison["confidence_by_root_cause"],
        "current_config_not_checkpoint_config": comparison["current_config_not_checkpoint_config"],
        "checkpoint_config_recovery_required": comparison["checkpoint_config_recovery_required"],
        "best_config_candidate_path": config_search["best_config_candidate_path"],
        "best_config_candidate_score": config_search["best_config_candidate_score"],
        "candidate_instantiation_attempted": candidate_smoke["candidate_instantiation_attempted"],
        "candidate_shape_matched_ratio": candidate_smoke["candidate_shape_matched_ratio"],
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
        "blocking_reasons": sorted(set(blockers)),
    }
    return {
        "manifest": manifest,
        "report_sections": {
            "step11a": {"step11a_validated": step11a_validated, "blocking_reasons": blockers},
            "checkpoint": checkpoint_evidence,
            "config": config_evidence,
            "current_model": current_model,
            "comparison": comparison,
            "config_search": config_search,
            "candidate_smoke": candidate_smoke,
            "decision": decision,
            "safety": {
                "original_source_files_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
                "backward_called": False,
                "optimizer_created": False,
                "optimizer_step_called": False,
                "training_step_called": False,
                "trainer_fit_called": False,
                "checkpoint_saved": False,
                "model_saved": False,
            },
        },
        "mismatch_table": mismatch_table,
    }
