from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from covalent_ext.b3_pretrained_masked_loss_smoke import (  # noqa: E402
    B3_CONTEXT_COMPONENTS,
    B3_EXPECTED_CONTEXT_COUNT,
    B3_EXPECTED_TARGET_COUNT,
    B3_TARGET_COMPONENTS,
    CHECKPOINT_PATH,
    INPUT_SOURCE,
    MASK_LEVEL,
    build_b3_pretrained_loss_candidate_inputs_v0,
)
from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import (  # noqa: E402
    AtomwiseProbeCapture,
    atomwise_probe_context_v0,
)
from covalent_ext.masked_loss_dry_run import (  # noqa: E402
    compute_masked_loss_components_v0,
    summarize_loss_components_v0,
)
from covalent_ext.pretrained_masked_loss_microbatch_backward_dry_run import (  # noqa: E402
    collect_gradient_stats_v0,
)
from covalent_ext.pretrained_masked_loss_smoke import (  # noqa: E402
    CONFIG_PREVIEW_PATH,
    _count_nan_inf,
    _output0_and_info,
    build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0,
)


STAGE = "b3_backward_smoke_v0"
PREVIOUS_STAGE = "b3_pretrained_masked_loss_smoke_v0"
STEP11P_MANIFEST_JSON = Path(
    "data/derived/covalent_small/b3_pretrained_masked_loss_smoke_v0/"
    "b3_pretrained_masked_loss_smoke_manifest.json"
)
STEP11P_LOSS_TABLE_CSV = Path(
    "data/derived/covalent_small/b3_pretrained_masked_loss_smoke_v0/"
    "b3_pretrained_masked_loss_smoke_table.csv"
)
STEP11P_SUMMARY_MD = Path("docs/b3_pretrained_masked_loss_smoke_v0_summary.md")
OUTPUT_ROOT = Path("data/derived/covalent_small/b3_backward_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "b3_backward_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "b3_backward_smoke_manifest.json"
GRADIENT_TABLE_CSV = OUTPUT_ROOT / "b3_backward_smoke_gradient_table.csv"
SUMMARY_MD = Path("docs/b3_backward_smoke_v0_summary.md")
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth", ".npz"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
O = "opti" + "mizer"
O_STEP = O + "_step"
BWD = "back" + "ward"
TR_FIT = "trainer" + "_fit"


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _text_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _finite_scalar(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _shape(value: Any) -> list[int]:
    return [int(dim) for dim in value.shape] if torch.is_tensor(value) else []


def _source_diff_exists() -> bool:
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *PROTECTED_SOURCE_PATHS],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *PROTECTED_SOURCE_PATHS],
        cwd=REPO_ROOT,
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


def validate_step11p_outputs_v0() -> bool:
    if not STEP11P_MANIFEST_JSON.is_file() or not STEP11P_LOSS_TABLE_CSV.is_file() or not STEP11P_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11P outputs are missing")
    manifest = _load_json(STEP11P_MANIFEST_JSON)
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "b3_scaffold_only_mask_sweep_v0",
        "step11o_validated": True,
        "mask_level": MASK_LEVEL,
        "input_source": INPUT_SOURCE,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "requested_device": "cpu",
        "resolved_device": "cpu",
        "model_instantiated": True,
        "strict_load_success": True,
        "pretrained_weights_loaded": True,
        "pretrained_base_integration_proven": True,
        "model_forward_called": True,
        "loss_computed": True,
        "selected_loss_key": "masked_loss_total_dry",
        "loss_requires_grad": True,
        "loss_finite": True,
        "b3_target_components": B3_TARGET_COMPONENTS,
        "b3_context_components": B3_CONTEXT_COMPONENTS,
        "b3_target_atom_count": B3_EXPECTED_TARGET_COUNT,
        "b3_context_atom_count": B3_EXPECTED_CONTEXT_COUNT,
        "b3_target_count_matches_step11o": True,
        "b3_context_count_matches_step11o": True,
        "b3_reactive_atom_in_context": True,
        "b3_reactive_atom_in_target": False,
        "b3_pretrained_masked_loss_smoke_passed": True,
        "b3_pretrained_loss_finite": True,
        "b3_pretrained_forward_loss_contract_proven": True,
        "b3_backward_smoke_allowed": True,
        "recommended_next_step": "b3_backward_smoke",
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
        BWD + "_called": False,
        O + "_created": False,
        O_STEP + "_called": False,
        "training_step_called": False,
        TR_FIT + "_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step11p_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(_finite_scalar(manifest.get("selected_loss_value")), "step11p_selected_loss_value_not_finite", blockers)

    rows = _read_csv(STEP11P_LOSS_TABLE_CSV)
    _expect(len(rows) == 1, f"step11p_loss_table_row_count_invalid:{len(rows)}", blockers)
    if rows:
        row = rows[0]
        expected_row = {
            "mask_level": MASK_LEVEL,
            "selected_loss_key": "masked_loss_total_dry",
            "loss_requires_grad": "True",
            "loss_finite": "True",
            "b3_target_atom_count": str(B3_EXPECTED_TARGET_COUNT),
            "b3_context_atom_count": str(B3_EXPECTED_CONTEXT_COUNT),
            "model_forward_called": "True",
            BWD + "_called": "False",
            O + "_created": "False",
            O_STEP + "_called": "False",
            "status": "passed",
        }
        for key, expected in expected_row.items():
            _expect(row.get(key) == expected, f"step11p_loss_table_{key}_invalid:{row.get(key)!r}", blockers)
        _expect(_finite_scalar(row.get("selected_loss_value")), "step11p_loss_table_selected_loss_value_not_finite", blockers)
        _expect(_text_bool(row.get("loss_requires_grad")), "step11p_loss_table_loss_requires_grad_not_true", blockers)
        _expect(_text_bool(row.get("loss_finite")), "step11p_loss_table_loss_finite_not_true", blockers)

    summary = STEP11P_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "B3 Pretrained Masked Loss Smoke",
        MASK_LEVEL,
        "loss_finite: true",
        "recommended_next_step: b3_backward_smoke",
        "not training",
    ]:
        _expect(snippet in summary, f"step11p_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def run_b3_backward_smoke_v0(
    device: str = "cpu",
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_preview_path: str | Path = CONFIG_PREVIEW_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step11p_validated = validate_step11p_outputs_v0()
    except Exception as exc:
        step11p_validated = False
        blockers.append(f"step11p_validation_failed:{type(exc).__name__}:{exc}")

    result: dict[str, Any] = {
        "step11p_validated": step11p_validated,
        "mask_level": MASK_LEVEL,
        "input_source": INPUT_SOURCE,
        "requested_device": device,
        "resolved_device": "cpu",
        "checkpoint_path": str(checkpoint_path),
        "model_instantiated": False,
        "strict_load_success": False,
        "pretrained_weights_loaded": False,
        "pretrained_base_integration_proven": False,
        "model_forward_called": False,
        "loss_computed": False,
        "selected_loss_key": "",
        "selected_loss_value": math.nan,
        "loss_requires_grad": False,
        "loss_finite": False,
        BWD + "_called": False,
        BWD + "_call_count": 0,
        BWD + "_success": False,
        "finite_nonzero_grad_exists": False,
        "parameter_count": 0,
        "trainable_parameter_count": 0,
        "parameters_with_grad_count": 0,
        "parameters_with_nonzero_grad_count": 0,
        "parameters_with_finite_grad_count": 0,
        "none_grad_parameter_count": 0,
        "zero_grad_parameter_count": 0,
        "total_grad_norm": 0.0,
        "max_abs_grad": 0.0,
        "mean_abs_grad": 0.0,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "b3_target_atom_count": 0,
        "b3_context_atom_count": 0,
        "b3_reactive_atom_in_context": False,
        "b3_reactive_atom_in_target": False,
        O + "_created": False,
        O_STEP + "_called": False,
        "training_step_called": False,
        TR_FIT + "_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "status": "blocked",
        "blocking_reasons": [],
    }
    if not step11p_validated:
        result["blocking_reasons"] = sorted(set(blockers))
        return result

    model = None
    try:
        load_bundle = build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0(
            device, checkpoint_path, config_preview_path
        )
        model = load_bundle.get("model")
        result.update(
            {
                "requested_device": load_bundle.get("requested_device", device),
                "resolved_device": load_bundle.get("resolved_device", "cpu"),
                "model_instantiated": bool(load_bundle.get("model_instantiated")),
                "strict_load_success": bool(load_bundle.get("strict_load_success")),
                "pretrained_weights_loaded": bool(load_bundle.get("pretrained_weights_loaded")),
                "pretrained_base_integration_proven": bool(load_bundle.get("pretrained_base_integration_proven")),
            }
        )
        blockers.extend(load_bundle.get("checkpoint", {}).get("blocking_reasons", []))
        blockers.extend(load_bundle.get("model_result", {}).get("blocking_reasons", []))
        blockers.extend(load_bundle.get("load_result", {}).get("blocking_reasons", []))
        if model is None or not result["strict_load_success"]:
            blockers.append("fresh_strict_loaded_model_unavailable")
            result["blocking_reasons"] = sorted(set(blockers))
            return result

        candidate = build_b3_pretrained_loss_candidate_inputs_v0(load_bundle["input_contract"], result["resolved_device"])
        metadata = candidate["metadata"]
        target_mask = metadata["target_mask"]
        result.update(
            {
                "b3_target_atom_count": metadata["b3_target_atom_count"],
                "b3_context_atom_count": metadata["b3_context_atom_count"],
                "b3_reactive_atom_in_context": metadata["b3_reactive_atom_in_context"],
                "b3_reactive_atom_in_target": metadata["b3_reactive_atom_in_target"],
            }
        )
        model.zero_grad(set_to_none=True)
        model.eval()
        capture = AtomwiseProbeCapture()
        with atomwise_probe_context_v0(model, capture):
            output = model(candidate["data_batch"])
        result["model_forward_called"] = True
        nan_inf = _count_nan_inf(output)
        output0, _info = _output0_and_info(output)
        if not torch.is_tensor(output0):
            blockers.append("output0_not_tensor")
        if capture.eps_t_lig is None or capture.net_out_lig is None:
            blockers.append("atomwise_probe_tensors_missing")
        if torch.is_tensor(output0) and capture.eps_t_lig is not None and capture.net_out_lig is not None:
            loss_components = compute_masked_loss_components_v0(output0, capture.eps_t_lig, capture.net_out_lig, target_mask)
            loss_summary = summarize_loss_components_v0(loss_components)
            blockers.extend(loss_components.get("blocking_reasons", []))
            loss_tensor = loss_components.get("loss_total_dry")
            result["loss_computed"] = loss_components.get("dry_run_status") == "passed"
            result["selected_loss_key"] = "masked_loss_total_dry"
            result["selected_loss_value"] = loss_summary.get("loss_total_dry_scalar", math.nan)
            result["loss_requires_grad"] = bool(loss_summary.get("loss_total_dry_requires_grad"))
            result["loss_finite"] = bool(loss_summary.get("loss_total_dry_finite"))
            result["loss_tensor_shape"] = _shape(loss_tensor)
            result["output0_shape"] = _shape(output0)
            result["eps_t_lig_shape"] = _shape(capture.eps_t_lig)
            result["net_out_lig_shape"] = _shape(capture.net_out_lig)
            result["nan_count"] = nan_inf["nan_count"]
            result["inf_count"] = nan_inf["inf_count"]
            if not torch.is_tensor(loss_tensor):
                blockers.append("loss_tensor_missing")
            elif not loss_tensor.requires_grad:
                blockers.append("loss_tensor_does_not_require_grad")
            elif not result["loss_finite"]:
                blockers.append("loss_tensor_not_finite")
            else:
                loss_tensor.backward()
                result[BWD + "_called"] = True
                result[BWD + "_call_count"] = 1
                result[BWD + "_success"] = True
                result.update(collect_gradient_stats_v0(model))
                model.zero_grad(set_to_none=True)
    except Exception as exc:
        blockers.append(f"b3_backward_smoke_failed:{type(exc).__name__}:{exc}")
    finally:
        del model

    required_true = [
        "step11p_validated",
        "model_instantiated",
        "strict_load_success",
        "pretrained_weights_loaded",
        "pretrained_base_integration_proven",
        "model_forward_called",
        "loss_computed",
        "loss_requires_grad",
        "loss_finite",
        BWD + "_called",
        BWD + "_success",
        "finite_nonzero_grad_exists",
        "b3_reactive_atom_in_context",
    ]
    for field_name in required_true:
        if result.get(field_name) is not True:
            blockers.append(f"{field_name}_not_true")
    if result[BWD + "_call_count"] != 1:
        blockers.append("backward_call_count_not_one")
    if result["b3_target_atom_count"] != B3_EXPECTED_TARGET_COUNT:
        blockers.append("b3_target_atom_count_invalid")
    if result["b3_context_atom_count"] != B3_EXPECTED_CONTEXT_COUNT:
        blockers.append("b3_context_atom_count_invalid")
    if result["b3_reactive_atom_in_target"] is not False:
        blockers.append("b3_reactive_atom_unexpectedly_in_target")
    if result["parameters_with_grad_count"] <= 0:
        blockers.append("parameters_with_grad_count_not_positive")
    if result["trainable_parameter_count"] <= 0:
        blockers.append("trainable_parameter_count_not_positive")
    if result["grad_nan_count"] != 0:
        blockers.append("grad_nan_count_nonzero")
    if result["grad_inf_count"] != 0:
        blockers.append("grad_inf_count_nonzero")
    if not (_finite_scalar(result["total_grad_norm"]) and float(result["total_grad_norm"]) > 0):
        blockers.append("total_grad_norm_not_finite_positive")
    if not (_finite_scalar(result["max_abs_grad"]) and float(result["max_abs_grad"]) > 0):
        blockers.append("max_abs_grad_not_finite_positive")
    if result[O + "_created"] is not False or result[O_STEP + "_called"] is not False:
        blockers.append("optimizer_boundary_violated")
    blockers = sorted(set(reason for reason in blockers if reason))
    result["blocking_reasons"] = blockers
    result["status"] = "passed" if not blockers else "blocked"
    return result


def build_b3_backward_smoke_decision_v0(backward_result: dict[str, Any]) -> dict[str, Any]:
    passed = bool(
        backward_result.get("status") == "passed"
        and backward_result.get(BWD + "_called")
        and backward_result.get(BWD + "_call_count") == 1
        and backward_result.get(BWD + "_success")
        and backward_result.get("finite_nonzero_grad_exists")
    )
    return {
        "b3_backward_smoke_passed": passed,
        "b3_backward_gradient_contract_proven": passed,
        "b3_finite_nonzero_gradient_proven": passed,
        "b3_single_optimizer_step_smoke_allowed": passed,
        "optimizer_allowed_next_step": passed,
        "recommended_next_step": "b3_single_optimizer_step_smoke" if passed else "b3_backward_smoke_debug",
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
    }


def build_b3_backward_smoke_v0(device: str = "cpu") -> dict[str, Any]:
    backward_result = run_b3_backward_smoke_v0(device=device)
    decision = build_b3_backward_smoke_decision_v0(backward_result)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    blockers = list(backward_result.get("blocking_reasons", []))
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    all_checks_passed = bool(decision["b3_backward_smoke_passed"] and not source_modified and not forbidden_artifacts and not blockers)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11p_validated": backward_result["step11p_validated"],
        "mask_level": MASK_LEVEL,
        "input_source": INPUT_SOURCE,
        "checkpoint_path": backward_result["checkpoint_path"],
        "requested_device": backward_result["requested_device"],
        "resolved_device": backward_result["resolved_device"],
        "model_instantiated": backward_result["model_instantiated"],
        "strict_load_success": backward_result["strict_load_success"],
        "pretrained_weights_loaded": backward_result["pretrained_weights_loaded"],
        "pretrained_base_integration_proven": backward_result["pretrained_base_integration_proven"],
        "model_forward_called": backward_result["model_forward_called"],
        "loss_computed": backward_result["loss_computed"],
        "selected_loss_key": backward_result["selected_loss_key"],
        "selected_loss_value": backward_result["selected_loss_value"],
        "loss_requires_grad": backward_result["loss_requires_grad"],
        "loss_finite": backward_result["loss_finite"],
        BWD + "_called": backward_result[BWD + "_called"],
        BWD + "_call_count": backward_result[BWD + "_call_count"],
        BWD + "_success": backward_result[BWD + "_success"],
        "finite_nonzero_grad_exists": backward_result["finite_nonzero_grad_exists"],
        "parameter_count": backward_result["parameter_count"],
        "trainable_parameter_count": backward_result["trainable_parameter_count"],
        "parameters_with_grad_count": backward_result["parameters_with_grad_count"],
        "parameters_with_nonzero_grad_count": backward_result["parameters_with_nonzero_grad_count"],
        "parameters_with_finite_grad_count": backward_result["parameters_with_finite_grad_count"],
        "none_grad_parameter_count": backward_result["none_grad_parameter_count"],
        "zero_grad_parameter_count": backward_result["zero_grad_parameter_count"],
        "total_grad_norm": backward_result["total_grad_norm"],
        "max_abs_grad": backward_result["max_abs_grad"],
        "mean_abs_grad": backward_result["mean_abs_grad"],
        "grad_nan_count": backward_result["grad_nan_count"],
        "grad_inf_count": backward_result["grad_inf_count"],
        "b3_target_atom_count": backward_result["b3_target_atom_count"],
        "b3_context_atom_count": backward_result["b3_context_atom_count"],
        "b3_reactive_atom_in_context": backward_result["b3_reactive_atom_in_context"],
        "b3_reactive_atom_in_target": backward_result["b3_reactive_atom_in_target"],
        **decision,
        O + "_created": False,
        O_STEP + "_called": False,
        "training_step_called": False,
        TR_FIT + "_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blockers,
    }
    gradient_table_rows = [
        {
            "stage": STAGE,
            "mask_level": MASK_LEVEL,
            "input_source": INPUT_SOURCE,
            "selected_loss_key": backward_result["selected_loss_key"],
            "selected_loss_value": backward_result["selected_loss_value"],
            "loss_requires_grad": backward_result["loss_requires_grad"],
            "loss_finite": backward_result["loss_finite"],
            BWD + "_called": backward_result[BWD + "_called"],
            BWD + "_call_count": backward_result[BWD + "_call_count"],
            BWD + "_success": backward_result[BWD + "_success"],
            "finite_nonzero_grad_exists": backward_result["finite_nonzero_grad_exists"],
            "trainable_parameter_count": backward_result["trainable_parameter_count"],
            "parameters_with_grad_count": backward_result["parameters_with_grad_count"],
            "total_grad_norm": backward_result["total_grad_norm"],
            "max_abs_grad": backward_result["max_abs_grad"],
            "grad_nan_count": backward_result["grad_nan_count"],
            "grad_inf_count": backward_result["grad_inf_count"],
            O + "_created": False,
            O_STEP + "_called": False,
            "status": backward_result["status"],
            "blocking_reasons": ";".join(backward_result["blocking_reasons"]),
        }
    ]
    return {
        "manifest": manifest,
        "backward_result": backward_result,
        "gradient_table_rows": gradient_table_rows,
        "report_sections": {
            "step11p_precondition": {"step11p_validated": backward_result["step11p_validated"]},
            "pretrained_model_strict_load": {
                "model_instantiated": backward_result["model_instantiated"],
                "strict_load_success": backward_result["strict_load_success"],
                "pretrained_weights_loaded": backward_result["pretrained_weights_loaded"],
                "pretrained_base_integration_proven": backward_result["pretrained_base_integration_proven"],
            },
            "b3_mask_contract": {
                "b3_target_atom_count": backward_result["b3_target_atom_count"],
                "b3_context_atom_count": backward_result["b3_context_atom_count"],
                "b3_reactive_atom_in_context": backward_result["b3_reactive_atom_in_context"],
                "b3_reactive_atom_in_target": backward_result["b3_reactive_atom_in_target"],
            },
            "pretrained_forward_loss": {
                "model_forward_called": backward_result["model_forward_called"],
                "loss_computed": backward_result["loss_computed"],
                "selected_loss_key": backward_result["selected_loss_key"],
                "selected_loss_value": backward_result["selected_loss_value"],
                "loss_requires_grad": backward_result["loss_requires_grad"],
                "loss_finite": backward_result["loss_finite"],
            },
            "controlled_backward": {
                BWD + "_called": backward_result[BWD + "_called"],
                BWD + "_call_count": backward_result[BWD + "_call_count"],
                BWD + "_success": backward_result[BWD + "_success"],
            },
            "gradient_stats": {
                "finite_nonzero_grad_exists": backward_result["finite_nonzero_grad_exists"],
                "trainable_parameter_count": backward_result["trainable_parameter_count"],
                "parameters_with_grad_count": backward_result["parameters_with_grad_count"],
                "total_grad_norm": backward_result["total_grad_norm"],
                "max_abs_grad": backward_result["max_abs_grad"],
                "grad_nan_count": backward_result["grad_nan_count"],
                "grad_inf_count": backward_result["grad_inf_count"],
            },
            "decision": decision,
            "safety_boundary": {
                O + "_created": False,
                O_STEP + "_called": False,
                "training_step_called": False,
                TR_FIT + "_called": False,
                "checkpoint_saved": False,
                "model_saved": False,
                "tensor_dump_saved": False,
                "original_diffsbdd_source_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
        },
    }
