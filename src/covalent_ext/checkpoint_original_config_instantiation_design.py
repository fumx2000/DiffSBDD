from __future__ import annotations

import inspect
import json
import subprocess
from pathlib import Path
from typing import Any

import torch

from covalent_ext import diffsbdd_forward_shape_smoke, diffsbdd_model_instantiation
from covalent_ext.pretrained_checkpoint_architecture_reconciliation import (
    MANIFEST_JSON as STEP11B_MANIFEST_JSON,
    SUMMARY_MD as STEP11B_SUMMARY_MD,
    _load_yaml_config,
    _relevant_fields,
    _sha256,
    flatten_metadata_v0,
    infer_architecture_from_state_shapes_v0,
    search_repo_config_candidates_v0,
)


STAGE = "checkpoint_original_config_instantiation_design_v0"
PREVIOUS_STAGE = "pretrained_checkpoint_architecture_reconciliation_v0"
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
CURRENT_CONFIG_PATH = Path("configs/crossdock_fullatom_cond.yml")
BEST_CONFIG_CANDIDATE_PATH = Path("configs/crossdock_fullatom_joint.yml")
OUTPUT_ROOT = Path("data/derived/covalent_small/checkpoint_original_config_instantiation_design_v0")
REPORT_CSV = OUTPUT_ROOT / "checkpoint_original_config_instantiation_design_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "checkpoint_original_config_instantiation_design_manifest.json"
CONFIG_PREVIEW_JSON = OUTPUT_ROOT / "checkpoint_original_config_preview.json"
SUMMARY_MD = Path("docs/checkpoint_original_config_instantiation_design_v0_summary.md")
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


def _get_nested(value: Any, dotted_key: str, default: Any = None) -> Any:
    current = value
    for part in dotted_key.split("."):
        if isinstance(current, dict):
            current = current.get(part, default)
        else:
            current = getattr(current, part, default)
        if current is default:
            return default
    return current


def validate_step11b_outputs_v0() -> bool:
    blockers: list[str] = []
    if not STEP11B_MANIFEST_JSON.is_file() or not STEP11B_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11B outputs are missing")
    manifest = _load_json(STEP11B_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "pretrained_checkpoint_load_smoke_v0",
        "step11a_validated": True,
        "checkpoint_has_hyper_parameters": True,
        "checkpoint_state_dict_key_count": 122,
        "current_config_present": True,
        "current_model_instantiated": True,
        "matched_key_count": 122,
        "shape_matched_key_count": 7,
        "shape_matched_ratio": 0.05737704918032787,
        "incompatible_shape_count": 115,
        "current_config_not_checkpoint_config": True,
        "checkpoint_config_recovery_required": True,
        "reconciliation_status": "checkpoint_original_config_recovery_needed",
        "pretrained_masked_loss_smoke_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
        "recommended_next_step": "checkpoint_original_config_model_instantiation_design",
        "all_checks_passed": True,
    }
    for key, expected_value in expected.items():
        actual = manifest.get(key)
        if actual != expected_value:
            blockers.append(f"step11b_{key}_invalid:{actual!r}")
    if manifest.get("pretrained_masked_loss_smoke_allowed") is True:
        blockers.append("step11b_allows_pretrained_masked_loss_smoke")
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_checkpoint_hparams_for_design_v0(checkpoint_path: str | Path = CHECKPOINT_PATH) -> dict[str, Any]:
    path = Path(checkpoint_path)
    result: dict[str, Any] = {
        "checkpoint_path": str(path),
        "checkpoint_present": path.is_file(),
        "checkpoint_sha256": _sha256(path) if path.is_file() else "",
        "checkpoint_size_bytes": path.stat().st_size if path.is_file() else 0,
        "top_level_keys": [],
        "checkpoint_hparams_loaded": False,
        "checkpoint_hparams_complete_for_instantiation": False,
        "hyper_parameters_keys": [],
        "hyper_parameters_flattened": {},
        "hyper_parameters_relevant_fields": {},
        "state_dict_key_count": 0,
        "state_dict_shape_summary": {},
        "checkpoint_target_joint_nf": None,
        "checkpoint_target_hidden_nf": None,
        "checkpoint_target_n_layers": None,
        "checkpoint_target_mode": "",
        "checkpoint_target_pocket_representation": "",
        "checkpoint_target_virtual_nodes": None,
        "checkpoint_target_atom_feature_dim": None,
        "checkpoint_target_residue_feature_dim": None,
        "checkpoint_target_egnn_embedding_input_dim": None,
        "checkpoint_target_egnn_embedding_output_dim": None,
        "checkpoint_target_egnn_blocks": None,
        "blocking_reasons": [],
    }
    if not path.is_file():
        result["blocking_reasons"].append("checkpoint_missing")
        return result
    try:
        payload = torch.load(path, map_location="cpu")
        if not isinstance(payload, dict):
            result["blocking_reasons"].append("checkpoint_payload_not_dict")
            return result
        result["top_level_keys"] = list(payload.keys())
        hparams = payload.get("hyper_parameters")
        if not isinstance(hparams, dict):
            result["blocking_reasons"].append("checkpoint_hyper_parameters_missing")
            return result
        result["checkpoint_hparams_loaded"] = True
        result["hyper_parameters_keys"] = list(hparams.keys())
        result["hyper_parameters_flattened"] = flatten_metadata_v0(hparams)
        result["hyper_parameters_relevant_fields"] = _relevant_fields(result["hyper_parameters_flattened"])
        state_dict = payload.get("state_dict")
        if not isinstance(state_dict, dict):
            result["blocking_reasons"].append("checkpoint_state_dict_missing")
            return result
        shape_map = {key: _shape(value) for key, value in state_dict.items() if torch.is_tensor(value)}
        architecture = infer_architecture_from_state_shapes_v0(shape_map, "checkpoint")
        result["state_dict_key_count"] = len(shape_map)
        result["state_dict_shape_summary"] = architecture
        result["checkpoint_target_joint_nf"] = _get_nested(hparams, "egnn_params.joint_nf")
        result["checkpoint_target_hidden_nf"] = _get_nested(hparams, "egnn_params.hidden_nf")
        result["checkpoint_target_n_layers"] = _get_nested(hparams, "egnn_params.n_layers")
        result["checkpoint_target_mode"] = str(hparams.get("mode", ""))
        result["checkpoint_target_pocket_representation"] = str(hparams.get("pocket_representation", ""))
        result["checkpoint_target_virtual_nodes"] = hparams.get("virtual_nodes")
        result["checkpoint_target_atom_feature_dim"] = architecture.get("atom_encoder_input_dim")
        result["checkpoint_target_residue_feature_dim"] = architecture.get("residue_encoder_input_dim")
        result["checkpoint_target_egnn_embedding_input_dim"] = architecture.get("egnn_embedding_input_dim")
        result["checkpoint_target_egnn_embedding_output_dim"] = architecture.get("egnn_embedding_output_dim")
        result["checkpoint_target_egnn_blocks"] = architecture.get("egnn_block_count")
        required = [
            "checkpoint_target_joint_nf",
            "checkpoint_target_hidden_nf",
            "checkpoint_target_n_layers",
            "checkpoint_target_mode",
            "checkpoint_target_pocket_representation",
            "checkpoint_target_atom_feature_dim",
            "checkpoint_target_residue_feature_dim",
            "checkpoint_target_egnn_blocks",
        ]
        missing = [key for key in required if result.get(key) in {None, ""}]
        result["checkpoint_hparams_complete_for_instantiation"] = not missing
        if missing:
            result["blocking_reasons"].append(f"checkpoint_hparams_incomplete:{','.join(missing)}")
    except Exception as exc:
        result["blocking_reasons"].append(f"checkpoint_hparams_load_failed:{type(exc).__name__}:{exc}")
    return result


def load_config_for_design_v0(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    result = {
        "config_path": str(config_path),
        "config_present": config_path.is_file(),
        "config_loaded": False,
        "config_text_sha256": _sha256(config_path) if config_path.is_file() else "",
        "config_top_level_keys": [],
        "config_flattened": {},
        "relevant_fields": {},
        "joint_nf": None,
        "hidden_nf": None,
        "n_layers": None,
        "mode": "",
        "pocket_representation": "",
        "blocking_reasons": [],
    }
    if not config_path.is_file():
        result["blocking_reasons"].append("config_missing")
        return result
    data = _load_yaml_config(config_path)
    result["config_loaded"] = bool(data)
    result["config_top_level_keys"] = list(data.keys())
    result["config_flattened"] = flatten_metadata_v0(data)
    result["relevant_fields"] = _relevant_fields(result["config_flattened"])
    result["joint_nf"] = result["config_flattened"].get("egnn_params.joint_nf")
    result["hidden_nf"] = result["config_flattened"].get("egnn_params.hidden_nf")
    result["n_layers"] = result["config_flattened"].get("egnn_params.n_layers")
    result["mode"] = str(result["config_flattened"].get("mode", ""))
    result["pocket_representation"] = str(result["config_flattened"].get("pocket_representation", ""))
    if not data:
        result["blocking_reasons"].append("config_parse_failed")
    return result


def inspect_existing_instantiation_paths_v0() -> dict[str, Any]:
    helpers = [
        diffsbdd_forward_shape_smoke._instantiate_model_for_forward,
        diffsbdd_model_instantiation.build_minimal_diffsbdd_instantiation_config_v0,
        diffsbdd_model_instantiation._constructor_kwargs,
        diffsbdd_model_instantiation.try_instantiate_diffsbdd_model_without_checkpoint_v0,
    ]
    helper_signatures = {helper.__name__: str(inspect.signature(helper)) for helper in helpers}
    source_files = [
        "src/covalent_ext/diffsbdd_forward_shape_smoke.py",
        "src/covalent_ext/diffsbdd_model_instantiation.py",
        "src/covalent_ext/pretrained_checkpoint_load_smoke.py",
        "configs/crossdock_fullatom_cond.yml",
    ]
    source_text = "\n".join(
        Path(path).read_text(encoding="utf-8", errors="replace") for path in source_files if Path(path).is_file()
    )
    config_path_defaulted = "CONFIG_SOURCE = \"configs/crossdock_fullatom_cond.yml\"" in source_text
    safe_override_supported = False
    blockers = [
        "build_minimal_diffsbdd_instantiation_config_v0_has_no_config_path_argument",
        "_instantiate_model_for_forward_has_no_config_override_argument",
        "CONFIG_SOURCE_defaults_to_configs/crossdock_fullatom_cond.yml",
        "current_wrapper_uses_constants.dataset_params['crossdock_full']_for_11_dim_full_atom_fields",
    ]
    return {
        "instantiation_helpers_found": True,
        "helper_function_names": [helper.__name__ for helper in helpers],
        "helper_source_files": source_files,
        "helper_signature_summaries": helper_signatures,
        "config_path_hardcoded_or_defaulted": config_path_defaulted,
        "candidate_inputs_dependency": True,
        "model_factory_dependency": "LigandPocketDDPM plus _constructor_kwargs",
        "safe_config_override_supported": safe_override_supported,
        "safe_config_override_blockers": blockers,
        "minimal_required_changes_for_safe_override": [
            "add covalent_ext wrapper that accepts checkpoint hparams or config preview as in-memory config",
            "reuse LigandPocketDDPM constructor and _constructor_kwargs without editing DiffSBDD source",
            "choose dataset_info/atom_encoder consistent with 10-dimensional checkpoint features",
            "compare state_dict shapes before load attempt",
        ],
    }


def build_checkpoint_original_config_preview_v0(
    checkpoint_hparams: dict[str, Any],
    best_candidate_config: dict[str, Any],
    current_config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source": "checkpoint_hyper_parameters_plus_repo_config_template",
        "checkpoint_path": checkpoint_hparams["checkpoint_path"],
        "checkpoint_sha256": checkpoint_hparams["checkpoint_sha256"],
        "base_template_candidate": best_candidate_config["config_path"],
        "current_config_reference": current_config["config_path"],
        "target_mode": checkpoint_hparams["checkpoint_target_mode"],
        "target_pocket_representation": checkpoint_hparams["checkpoint_target_pocket_representation"],
        "target_egnn_params": {
            "joint_nf": checkpoint_hparams["checkpoint_target_joint_nf"],
            "hidden_nf": checkpoint_hparams["checkpoint_target_hidden_nf"],
            "n_layers": checkpoint_hparams["checkpoint_target_n_layers"],
        },
        "target_atom_feature_dim": checkpoint_hparams["checkpoint_target_atom_feature_dim"],
        "target_residue_feature_dim": checkpoint_hparams["checkpoint_target_residue_feature_dim"],
        "target_egnn_embedding_input_dim": checkpoint_hparams["checkpoint_target_egnn_embedding_input_dim"],
        "target_egnn_embedding_output_dim": checkpoint_hparams["checkpoint_target_egnn_embedding_output_dim"],
        "target_egnn_blocks": checkpoint_hparams["checkpoint_target_egnn_blocks"],
        "expected_checkpoint_state_dict_key_count": checkpoint_hparams["state_dict_key_count"],
        "expected_shape_match_goal": {
            "shape_matched_ratio_minimum": 0.8,
            "ideal_strict_load_success": True,
            "acceptable_nonstrict_load_success_condition": "only after shape table documents known minor mismatches",
        },
        "config_fields_to_override": {
            "mode": checkpoint_hparams["checkpoint_target_mode"],
            "egnn_params.joint_nf": checkpoint_hparams["checkpoint_target_joint_nf"],
            "egnn_params.hidden_nf": checkpoint_hparams["checkpoint_target_hidden_nf"],
            "egnn_params.n_layers": checkpoint_hparams["checkpoint_target_n_layers"],
            "pocket_representation": checkpoint_hparams["checkpoint_target_pocket_representation"],
            "virtual_nodes": checkpoint_hparams["checkpoint_target_virtual_nodes"],
        },
        "config_fields_to_keep_from_candidate": [
            "diffusion_params",
            "loss_params",
            "eval_params",
            "batch_size",
            "lr",
            "edge_cutoff_ligand",
            "edge_cutoff_pocket",
            "edge_cutoff_interaction",
            "attention",
            "tanh",
            "normalization_factor",
        ],
        "config_fields_requiring_manual_resolution": [
            "dataset and dataset_info mapping for 10-dimensional full-atom checkpoint features",
            "atom_encoder / atom_decoder feature contract",
            "residue feature contract",
            "node_histogram source and shape",
            "mode mismatch between checkpoint hparams and best repo template",
        ],
        "risks": [
            "repo candidate config matches EGNN dimensions but has mode=joint rather than pocket_conditioning",
            "current constants crossdock_full atom encoder is 11-dimensional while checkpoint tensors are 10-dimensional",
            "safe instantiation requires in-memory wrapper rather than editing original config files",
        ],
    }


def design_checkpoint_compatible_instantiation_wrapper_v0(
    config_preview: dict[str, Any],
    instantiation_paths: dict[str, Any],
) -> dict[str, Any]:
    return {
        "proposed_wrapper_name": "instantiate_checkpoint_compatible_model_v0",
        "proposed_location": "src/covalent_ext/checkpoint_compatible_model_instantiation.py",
        "input_arguments": {
            "checkpoint_path": "Path",
            "config_preview_path": "Path",
            "device": "str",
            "allow_source_modification": False,
        },
        "steps": [
            "load checkpoint hparams",
            "build in-memory config from candidate template plus checkpoint overrides",
            "instantiate LigandPocketDDPM with checkpoint-compatible egnn_params",
            "compare state_dict shapes before loading",
            "attempt strict load",
            "if strict load fails, attempt non-strict load only after shape table",
            "run no-grad forward smoke only if shape_match_ratio is above threshold",
            "do not serialize checkpoint or model objects",
        ],
        "safety": {
            "no_optimizer": True,
            "no_gradient_pass": True,
            "no_lightning_trainer": True,
            "no_constructor_source_edits": True,
            "no_checkpoint_or_model_serialization": True,
        },
        "expected_output_next_step": [
            "shape match table",
            "strict/nonstrict load result",
            "no-grad forward finite status",
        ],
        "requires_wrapper": not instantiation_paths["safe_config_override_supported"],
        "config_preview_source": config_preview["source"],
    }


def build_instantiation_design_decision_v0(
    checkpoint_hparams: dict[str, Any],
    instantiation_paths: dict[str, Any],
    config_candidates_ambiguous: bool = False,
) -> dict[str, Any]:
    if config_candidates_ambiguous:
        design_status = "config_candidate_ambiguity_review"
        next_step = "manual_config_candidate_review"
    elif not checkpoint_hparams["checkpoint_hparams_complete_for_instantiation"]:
        design_status = "manual_checkpoint_hparams_recovery_required"
        next_step = "manual_checkpoint_hparams_recovery"
    elif instantiation_paths["safe_config_override_supported"]:
        design_status = "ready_for_checkpoint_compatible_instantiation_smoke"
        next_step = "checkpoint_compatible_model_instantiation_smoke"
    else:
        design_status = "wrapper_needed_for_checkpoint_compatible_instantiation"
        next_step = "checkpoint_compatible_instantiation_wrapper_prototype"
    return {
        "design_status": design_status,
        "checkpoint_compatible_instantiation_feasible": checkpoint_hparams[
            "checkpoint_hparams_complete_for_instantiation"
        ],
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "masked_loss_smoke_allowed": False,
        "pretrained_masked_loss_smoke_allowed": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
        "recommended_next_step": next_step,
    }


def build_checkpoint_original_config_instantiation_design_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step11b_validated = validate_step11b_outputs_v0()
    except Exception as exc:
        step11b_validated = False
        blockers.append(f"step11b_validation_failed:{type(exc).__name__}:{exc}")

    checkpoint_hparams = load_checkpoint_hparams_for_design_v0(CHECKPOINT_PATH)
    current_config = load_config_for_design_v0(CURRENT_CONFIG_PATH)
    best_candidate = load_config_for_design_v0(BEST_CONFIG_CANDIDATE_PATH)
    config_search = search_repo_config_candidates_v0(
        {
            "hyper_parameters_relevant_fields": checkpoint_hparams.get(
                "hyper_parameters_relevant_fields", {}
            )
        }
    )
    instantiation_paths = inspect_existing_instantiation_paths_v0()
    config_preview = build_checkpoint_original_config_preview_v0(
        checkpoint_hparams, best_candidate, current_config
    )
    wrapper_design = design_checkpoint_compatible_instantiation_wrapper_v0(
        config_preview, instantiation_paths
    )
    decision = build_instantiation_design_decision_v0(checkpoint_hparams, instantiation_paths)

    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_source_files_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    for section in [checkpoint_hparams, current_config, best_candidate]:
        blockers.extend(section.get("blocking_reasons", []))

    config_preview_written = True
    all_checks_passed = bool(
        step11b_validated
        and checkpoint_hparams["checkpoint_hparams_loaded"]
        and checkpoint_hparams["checkpoint_hparams_complete_for_instantiation"]
        and current_config["config_loaded"]
        and best_candidate["config_loaded"]
        and instantiation_paths["instantiation_helpers_found"]
        and decision["design_status"]
        and not source_modified
        and not forbidden_artifacts
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11b_validated": step11b_validated,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "checkpoint_sha256": checkpoint_hparams["checkpoint_sha256"],
        "checkpoint_hparams_loaded": checkpoint_hparams["checkpoint_hparams_loaded"],
        "checkpoint_hparams_complete_for_instantiation": checkpoint_hparams[
            "checkpoint_hparams_complete_for_instantiation"
        ],
        "checkpoint_target_joint_nf": checkpoint_hparams["checkpoint_target_joint_nf"],
        "checkpoint_target_hidden_nf": checkpoint_hparams["checkpoint_target_hidden_nf"],
        "checkpoint_target_n_layers": checkpoint_hparams["checkpoint_target_n_layers"],
        "checkpoint_target_mode": checkpoint_hparams["checkpoint_target_mode"],
        "checkpoint_target_pocket_representation": checkpoint_hparams[
            "checkpoint_target_pocket_representation"
        ],
        "checkpoint_target_atom_feature_dim": checkpoint_hparams[
            "checkpoint_target_atom_feature_dim"
        ],
        "checkpoint_target_residue_feature_dim": checkpoint_hparams[
            "checkpoint_target_residue_feature_dim"
        ],
        "checkpoint_target_egnn_blocks": checkpoint_hparams["checkpoint_target_egnn_blocks"],
        "current_config_path": str(CURRENT_CONFIG_PATH),
        "current_config_joint_nf": current_config["joint_nf"],
        "current_config_hidden_nf": current_config["hidden_nf"],
        "current_config_n_layers": current_config["n_layers"],
        "best_config_candidate_path": str(BEST_CONFIG_CANDIDATE_PATH),
        "best_config_candidate_loaded": best_candidate["config_loaded"],
        "best_config_candidate_score": config_search["best_config_candidate_score"],
        "safe_config_override_supported": instantiation_paths["safe_config_override_supported"],
        "safe_config_override_blockers": instantiation_paths["safe_config_override_blockers"],
        "config_preview_written": config_preview_written,
        "config_preview_path": str(CONFIG_PREVIEW_JSON),
        "proposed_wrapper_name": wrapper_design["proposed_wrapper_name"],
        "proposed_wrapper_location": wrapper_design["proposed_location"],
        "checkpoint_compatible_instantiation_feasible": decision[
            "checkpoint_compatible_instantiation_feasible"
        ],
        "expected_shape_match_goal": config_preview["expected_shape_match_goal"],
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
        "config_preview": config_preview,
        "report_sections": {
            "step11b": {"step11b_validated": step11b_validated},
            "checkpoint_hparams": checkpoint_hparams,
            "current_config": current_config,
            "best_candidate": best_candidate,
            "config_search": config_search,
            "instantiation_paths": instantiation_paths,
            "wrapper_design": wrapper_design,
            "decision": decision,
            "safety": {
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
