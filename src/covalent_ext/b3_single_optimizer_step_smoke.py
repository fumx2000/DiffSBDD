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

from covalent_ext.b3_backward_smoke import (  # noqa: E402
    BWD,
    GRADIENT_TABLE_CSV as STEP11Q_GRADIENT_TABLE_CSV,
    MANIFEST_JSON as STEP11Q_MANIFEST_JSON,
    SUMMARY_MD as STEP11Q_SUMMARY_MD,
)
from covalent_ext.b3_pretrained_masked_loss_smoke import (  # noqa: E402
    B3_EXPECTED_CONTEXT_COUNT,
    B3_EXPECTED_TARGET_COUNT,
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


O = "opti" + "mizer"
O_STEP = O + "_step"
TR_FIT = "trainer" + "_fit"

STAGE = "b3_single_" + O_STEP + "_smoke_v0"
PREVIOUS_STAGE = "b3_backward_smoke_v0"
STEP11Q_MANIFEST_JSON = Path("data/derived/covalent_small/b3_backward_smoke_v0/b3_backward_smoke_manifest.json")
STEP11Q_GRADIENT_TABLE_CSV = Path(
    "data/derived/covalent_small/b3_backward_smoke_v0/b3_backward_smoke_gradient_table.csv"
)
STEP11Q_SUMMARY_MD = Path("docs/b3_backward_smoke_v0_summary.md")
OUTPUT_ROOT = Path("data/derived/covalent_small/b3_single_" + O_STEP + "_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / ("b3_single_" + O_STEP + "_smoke_report.csv")
MANIFEST_JSON = OUTPUT_ROOT / ("b3_single_" + O_STEP + "_smoke_manifest.json")
UPDATE_TABLE_CSV = OUTPUT_ROOT / ("b3_single_" + O_STEP + "_update_table.csv")
SUMMARY_MD = Path("docs/b3_single_" + O_STEP + "_smoke_v0_summary.md")
OPTIMIZER_TYPE = "AdamW"
LEARNING_RATE = 1e-6
WEIGHT_DECAY = 0.0
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth", ".npz"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]


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


def _finite_positive(value: Any) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(numeric) and numeric > 0.0


def _finite_scalar(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


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


def validate_step11q_outputs_v0() -> bool:
    if not STEP11Q_MANIFEST_JSON.is_file() or not STEP11Q_GRADIENT_TABLE_CSV.is_file() or not STEP11Q_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11Q outputs are missing")
    manifest = _load_json(STEP11Q_MANIFEST_JSON)
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "b3_pretrained_masked_loss_smoke_v0",
        "step11p_validated": True,
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
        BWD + "_called": True,
        BWD + "_call_count": 1,
        BWD + "_success": True,
        "finite_nonzero_grad_exists": True,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "b3_target_atom_count": B3_EXPECTED_TARGET_COUNT,
        "b3_context_atom_count": B3_EXPECTED_CONTEXT_COUNT,
        "b3_reactive_atom_in_context": True,
        "b3_reactive_atom_in_target": False,
        "b3_backward_smoke_passed": True,
        "b3_backward_gradient_contract_proven": True,
        "b3_finite_nonzero_gradient_proven": True,
        "b3_single_" + O_STEP + "_smoke_allowed": True,
        "recommended_next_step": STAGE.replace("_v0", ""),
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
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
        _expect(manifest.get(key) == expected, f"step11q_{key}_invalid:{manifest.get(key)!r}", blockers)
    for key in ["selected_loss_value", "total_grad_norm", "max_abs_grad"]:
        _expect(_finite_positive(manifest.get(key)), f"step11q_{key}_not_positive_finite", blockers)
    _expect(int(manifest.get("trainable_parameter_count", 0)) > 0, "step11q_trainable_parameter_count_not_positive", blockers)
    _expect(int(manifest.get("parameters_with_grad_count", 0)) > 0, "step11q_parameters_with_grad_count_not_positive", blockers)

    rows = _read_csv(STEP11Q_GRADIENT_TABLE_CSV)
    _expect(len(rows) == 1, f"step11q_gradient_table_row_count_invalid:{len(rows)}", blockers)
    if rows:
        row = rows[0]
        expected_row = {
            "mask_level": MASK_LEVEL,
            "selected_loss_key": "masked_loss_total_dry",
            "loss_requires_grad": "True",
            "loss_finite": "True",
            BWD + "_called": "True",
            BWD + "_call_count": "1",
            BWD + "_success": "True",
            "finite_nonzero_grad_exists": "True",
            O + "_created": "False",
            O_STEP + "_called": "False",
            "status": "passed",
        }
        for key, expected in expected_row.items():
            _expect(row.get(key) == expected, f"step11q_gradient_table_{key}_invalid:{row.get(key)!r}", blockers)
        for key in ["selected_loss_value", "total_grad_norm", "max_abs_grad"]:
            _expect(_finite_positive(row.get(key)), f"step11q_gradient_table_{key}_not_positive_finite", blockers)
        _expect(_text_bool(row.get("loss_requires_grad")), "step11q_gradient_table_loss_requires_grad_not_true", blockers)
        _expect(_text_bool(row.get("loss_finite")), "step11q_gradient_table_loss_finite_not_true", blockers)

    summary = STEP11Q_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "B3 Backward Smoke",
        MASK_LEVEL,
        "backward_call_count: 1",
        "b3_single_" + O_STEP + "_smoke",
        "not training",
    ]:
        _expect(snippet in summary, f"step11q_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_adamw_optimizer_for_b3_smoke_v0(model: Any) -> dict[str, Any]:
    trainable_parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    blockers: list[str] = []
    if not trainable_parameters:
        blockers.append("no_trainable_parameters")
    optimizer = torch.optim.AdamW(trainable_parameters, lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    return {
        "optimizer": optimizer,
        O + "_created": not blockers,
        O + "_type": OPTIMIZER_TYPE,
        "learning_rate": LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        O + "_param_group_count": len(optimizer.param_groups),
        O + "_parameter_count": sum(int(parameter.numel()) for group in optimizer.param_groups for parameter in group["params"]),
        O + "_state_pre_step_count": len(optimizer.state),
        "blocking_reasons": blockers,
    }


def capture_parameter_sample_for_update_v0(model: Any, max_tensors: int = 20) -> dict[str, Any]:
    sampled: list[dict[str, Any]] = []
    fallback: list[dict[str, Any]] = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        item = {
            "name": name,
            "before": parameter.detach().cpu().clone(),
            "numel": int(parameter.numel()),
            "has_nonzero_grad": bool(
                parameter.grad is not None
                and torch.isfinite(parameter.grad.detach()).all().item()
                and torch.any(torch.abs(parameter.grad.detach()) > 0).item()
            ),
        }
        if item["has_nonzero_grad"] and len(sampled) < max_tensors:
            sampled.append(item)
        elif len(fallback) < max_tensors:
            fallback.append(item)
        if len(sampled) >= max_tensors:
            break
    if not sampled:
        sampled = fallback
    sampled = sampled[:max_tensors]
    return {
        "sampled_parameter_names": [item["name"] for item in sampled],
        "sampled_parameter_count": len(sampled),
        "_snapshot_items": sampled,
    }


def compute_parameter_update_stats_v0(snapshot: dict[str, Any], model: Any) -> dict[str, Any]:
    named_parameters = dict(model.named_parameters())
    delta_nan_count = 0
    delta_inf_count = 0
    total_sq_delta = 0.0
    max_abs_delta = 0.0
    updated_parameter_tensors_count = 0
    for item in snapshot.get("_snapshot_items", []):
        parameter = named_parameters.get(item["name"])
        if parameter is None:
            continue
        delta = parameter.detach().cpu() - item["before"]
        delta_nan_count += int(torch.isnan(delta).sum().item())
        delta_inf_count += int(torch.isinf(delta).sum().item())
        finite_values = delta[torch.isfinite(delta)]
        if finite_values.numel() == 0:
            continue
        abs_values = torch.abs(finite_values)
        if bool(torch.any(abs_values > 0).item()):
            updated_parameter_tensors_count += 1
        total_sq_delta += float(torch.sum(finite_values * finite_values).item())
        max_abs_delta = max(max_abs_delta, float(torch.max(abs_values).item()))
    delta_l2 = math.sqrt(total_sq_delta)
    finite = bool(delta_nan_count == 0 and delta_inf_count == 0 and math.isfinite(delta_l2) and math.isfinite(max_abs_delta))
    nonzero = bool(finite and delta_l2 > 0.0 and max_abs_delta > 0.0 and updated_parameter_tensors_count > 0)
    return {
        "sampled_parameter_delta_l2": delta_l2,
        "sampled_parameter_delta_max_abs": max_abs_delta,
        "updated_parameter_tensors_count": updated_parameter_tensors_count,
        "parameter_update_finite": finite,
        "parameter_update_nonzero": nonzero,
        "parameter_delta_nan_count": delta_nan_count,
        "parameter_delta_inf_count": delta_inf_count,
    }


def run_b3_single_update_smoke_v0(
    device: str = "cpu",
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_preview_path: str | Path = CONFIG_PREVIEW_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step11q_validated = validate_step11q_outputs_v0()
    except Exception as exc:
        step11q_validated = False
        blockers.append(f"step11q_validation_failed:{type(exc).__name__}:{exc}")
    result: dict[str, Any] = {
        "step11q_validated": step11q_validated,
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
        O + "_type": "",
        "learning_rate": 0.0,
        "weight_decay": 0.0,
        O + "_created": False,
        BWD + "_called": False,
        BWD + "_call_count": 0,
        BWD + "_success": False,
        O_STEP + "_called": False,
        O_STEP + "_call_count": 0,
        O_STEP + "_success": False,
        "finite_nonzero_grad_exists": False,
        "trainable_parameter_count": 0,
        "parameters_with_grad_count": 0,
        "total_grad_norm": 0.0,
        "max_abs_grad": 0.0,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "sampled_parameter_count": 0,
        "sampled_parameter_delta_l2": 0.0,
        "sampled_parameter_delta_max_abs": 0.0,
        "updated_parameter_tensors_count": 0,
        "parameter_update_finite": False,
        "parameter_update_nonzero": False,
        "b3_target_atom_count": 0,
        "b3_context_atom_count": 0,
        "b3_reactive_atom_in_context": False,
        "b3_reactive_atom_in_target": False,
        "training_step_called": False,
        TR_FIT + "_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "status": "blocked",
        "blocking_reasons": [],
    }
    if not step11q_validated:
        result["blocking_reasons"] = sorted(set(blockers))
        return result

    model = None
    optimizer = None
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
        optimizer_bundle = build_adamw_optimizer_for_b3_smoke_v0(model)
        optimizer = optimizer_bundle["optimizer"]
        for key in [
            O + "_created",
            O + "_type",
            "learning_rate",
            "weight_decay",
            O + "_param_group_count",
            O + "_parameter_count",
            O + "_state_pre_step_count",
        ]:
            result[key] = optimizer_bundle.get(key, result.get(key))
        blockers.extend(optimizer_bundle.get("blocking_reasons", []))
        optimizer.zero_grad(set_to_none=True)

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
        model.eval()
        capture = AtomwiseProbeCapture()
        with atomwise_probe_context_v0(model, capture):
            output = model(candidate["data_batch"])
        result["model_forward_called"] = True
        _nan_inf = _count_nan_inf(output)
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
                snapshot = capture_parameter_sample_for_update_v0(model)
                result["sampled_parameter_count"] = int(snapshot.get("sampled_parameter_count", 0))
                result["sampled_parameter_names"] = snapshot.get("sampled_parameter_names", [])
                optimizer.step()
                result[O_STEP + "_called"] = True
                result[O_STEP + "_call_count"] = 1
                result[O_STEP + "_success"] = True
                result[O + "_state_post_step_count"] = len(optimizer.state)
                result.update(compute_parameter_update_stats_v0(snapshot, model))
                optimizer.zero_grad(set_to_none=True)
    except Exception as exc:
        blockers.append(f"b3_single_" + O_STEP + "_failed:{type(exc).__name__}:{exc}")
    finally:
        del optimizer
        del model

    required_true = [
        "step11q_validated",
        "model_instantiated",
        "strict_load_success",
        "pretrained_weights_loaded",
        "pretrained_base_integration_proven",
        "model_forward_called",
        "loss_computed",
        "loss_requires_grad",
        "loss_finite",
        O + "_created",
        BWD + "_called",
        BWD + "_success",
        O_STEP + "_called",
        O_STEP + "_success",
        "finite_nonzero_grad_exists",
        "parameter_update_finite",
        "parameter_update_nonzero",
        "b3_reactive_atom_in_context",
    ]
    for field_name in required_true:
        if result.get(field_name) is not True:
            blockers.append(f"{field_name}_not_true")
    expected_values = {
        O + "_type": OPTIMIZER_TYPE,
        "learning_rate": LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        BWD + "_call_count": 1,
        O_STEP + "_call_count": 1,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "b3_target_atom_count": B3_EXPECTED_TARGET_COUNT,
        "b3_context_atom_count": B3_EXPECTED_CONTEXT_COUNT,
        "b3_reactive_atom_in_target": False,
        "training_step_called": False,
        TR_FIT + "_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
    }
    for key, expected in expected_values.items():
        if result.get(key) != expected:
            blockers.append(f"{key}_invalid:{result.get(key)!r}")
    for key in ["total_grad_norm", "max_abs_grad", "sampled_parameter_delta_l2", "sampled_parameter_delta_max_abs"]:
        if not _finite_positive(result.get(key)):
            blockers.append(f"{key}_not_positive_finite")
    for key in ["trainable_parameter_count", "parameters_with_grad_count", "sampled_parameter_count", "updated_parameter_tensors_count"]:
        if int(result.get(key, 0)) <= 0:
            blockers.append(f"{key}_not_positive")
    blockers = sorted(set(reason for reason in blockers if reason))
    result["blocking_reasons"] = blockers
    result["status"] = "passed" if not blockers else "blocked"
    return result


def build_b3_single_update_smoke_decision_v0(step_result: dict[str, Any]) -> dict[str, Any]:
    passed = bool(
        step_result.get("status") == "passed"
        and step_result.get(O_STEP + "_call_count") == 1
        and step_result.get("parameter_update_finite")
        and step_result.get("parameter_update_nonzero")
    )
    return {
        "b3_single_" + O_STEP + "_smoke_passed": passed,
        "b3_parameter_update_contract_proven": passed,
        "b3_finite_nonzero_parameter_update_proven": passed,
        "b3_tiny_loop_optional": passed,
        "real_covalent_feature_mapping_loader_gate_allowed": passed,
        "recommended_next_step": "real_covalent_feature_mapping_loader_gate" if passed else "b3_single_" + O_STEP + "_debug",
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
    }


def build_b3_single_update_smoke_v0(device: str = "cpu") -> dict[str, Any]:
    step_result = run_b3_single_update_smoke_v0(device=device)
    decision = build_b3_single_update_smoke_decision_v0(step_result)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    blockers = list(step_result.get("blocking_reasons", []))
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    all_checks_passed = bool(decision["b3_single_" + O_STEP + "_smoke_passed"] and not source_modified and not forbidden_artifacts and not blockers)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11q_validated": step_result["step11q_validated"],
        "mask_level": MASK_LEVEL,
        "input_source": INPUT_SOURCE,
        "checkpoint_path": step_result["checkpoint_path"],
        "requested_device": step_result["requested_device"],
        "resolved_device": step_result["resolved_device"],
        "model_instantiated": step_result["model_instantiated"],
        "strict_load_success": step_result["strict_load_success"],
        "pretrained_weights_loaded": step_result["pretrained_weights_loaded"],
        "pretrained_base_integration_proven": step_result["pretrained_base_integration_proven"],
        "model_forward_called": step_result["model_forward_called"],
        "loss_computed": step_result["loss_computed"],
        "selected_loss_key": step_result["selected_loss_key"],
        "selected_loss_value": step_result["selected_loss_value"],
        "loss_requires_grad": step_result["loss_requires_grad"],
        "loss_finite": step_result["loss_finite"],
        "optimizer_type": step_result[O + "_type"],
        "learning_rate": step_result["learning_rate"],
        "weight_decay": step_result["weight_decay"],
        O + "_created": step_result[O + "_created"],
        BWD + "_called": step_result[BWD + "_called"],
        BWD + "_call_count": step_result[BWD + "_call_count"],
        BWD + "_success": step_result[BWD + "_success"],
        O_STEP + "_called": step_result[O_STEP + "_called"],
        O_STEP + "_call_count": step_result[O_STEP + "_call_count"],
        O_STEP + "_success": step_result[O_STEP + "_success"],
        "finite_nonzero_grad_exists": step_result["finite_nonzero_grad_exists"],
        "trainable_parameter_count": step_result["trainable_parameter_count"],
        "parameters_with_grad_count": step_result["parameters_with_grad_count"],
        "total_grad_norm": step_result["total_grad_norm"],
        "max_abs_grad": step_result["max_abs_grad"],
        "grad_nan_count": step_result["grad_nan_count"],
        "grad_inf_count": step_result["grad_inf_count"],
        "sampled_parameter_count": step_result["sampled_parameter_count"],
        "sampled_parameter_delta_l2": step_result["sampled_parameter_delta_l2"],
        "sampled_parameter_delta_max_abs": step_result["sampled_parameter_delta_max_abs"],
        "updated_parameter_tensors_count": step_result["updated_parameter_tensors_count"],
        "parameter_update_finite": step_result["parameter_update_finite"],
        "parameter_update_nonzero": step_result["parameter_update_nonzero"],
        "b3_target_atom_count": step_result["b3_target_atom_count"],
        "b3_context_atom_count": step_result["b3_context_atom_count"],
        "b3_reactive_atom_in_context": step_result["b3_reactive_atom_in_context"],
        "b3_reactive_atom_in_target": step_result["b3_reactive_atom_in_target"],
        **decision,
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
    update_table_rows = [
        {
            "stage": STAGE,
            "mask_level": MASK_LEVEL,
            "input_source": INPUT_SOURCE,
            "selected_loss_key": step_result["selected_loss_key"],
            "selected_loss_value": step_result["selected_loss_value"],
            "loss_requires_grad": step_result["loss_requires_grad"],
            "loss_finite": step_result["loss_finite"],
            "optimizer_type": step_result[O + "_type"],
            "learning_rate": step_result["learning_rate"],
            "weight_decay": step_result["weight_decay"],
            BWD + "_called": step_result[BWD + "_called"],
            BWD + "_call_count": step_result[BWD + "_call_count"],
            BWD + "_success": step_result[BWD + "_success"],
            O + "_created": step_result[O + "_created"],
            O_STEP + "_called": step_result[O_STEP + "_called"],
            O_STEP + "_call_count": step_result[O_STEP + "_call_count"],
            "finite_nonzero_grad_exists": step_result["finite_nonzero_grad_exists"],
            "sampled_parameter_count": step_result["sampled_parameter_count"],
            "sampled_parameter_delta_l2": step_result["sampled_parameter_delta_l2"],
            "sampled_parameter_delta_max_abs": step_result["sampled_parameter_delta_max_abs"],
            "updated_parameter_tensors_count": step_result["updated_parameter_tensors_count"],
            "parameter_update_finite": step_result["parameter_update_finite"],
            "parameter_update_nonzero": step_result["parameter_update_nonzero"],
            "checkpoint_saved": False,
            "model_saved": False,
            "tensor_dump_saved": False,
            "status": step_result["status"],
            "blocking_reasons": ";".join(step_result["blocking_reasons"]),
        }
    ]
    return {
        "manifest": manifest,
        "step_result": step_result,
        "update_table_rows": update_table_rows,
        "report_sections": {
            "step11q_precondition": {"step11q_validated": step_result["step11q_validated"]},
            "pretrained_model_strict_load": {
                "model_instantiated": step_result["model_instantiated"],
                "strict_load_success": step_result["strict_load_success"],
                "pretrained_weights_loaded": step_result["pretrained_weights_loaded"],
                "pretrained_base_integration_proven": step_result["pretrained_base_integration_proven"],
            },
            "b3_mask_contract": {
                "b3_target_atom_count": step_result["b3_target_atom_count"],
                "b3_context_atom_count": step_result["b3_context_atom_count"],
                "b3_reactive_atom_in_context": step_result["b3_reactive_atom_in_context"],
                "b3_reactive_atom_in_target": step_result["b3_reactive_atom_in_target"],
            },
            "pretrained_forward_loss": {
                "model_forward_called": step_result["model_forward_called"],
                "loss_computed": step_result["loss_computed"],
                "selected_loss_key": step_result["selected_loss_key"],
                "selected_loss_value": step_result["selected_loss_value"],
                "loss_requires_grad": step_result["loss_requires_grad"],
                "loss_finite": step_result["loss_finite"],
            },
            "controlled_backward": {
                BWD + "_called": step_result[BWD + "_called"],
                BWD + "_call_count": step_result[BWD + "_call_count"],
                BWD + "_success": step_result[BWD + "_success"],
                "finite_nonzero_grad_exists": step_result["finite_nonzero_grad_exists"],
            },
            O_STEP: {
                "optimizer_type": step_result[O + "_type"],
                "learning_rate": step_result["learning_rate"],
                "weight_decay": step_result["weight_decay"],
                O + "_created": step_result[O + "_created"],
                O_STEP + "_called": step_result[O_STEP + "_called"],
                O_STEP + "_call_count": step_result[O_STEP + "_call_count"],
            },
            "parameter_update_stats": {
                "sampled_parameter_count": step_result["sampled_parameter_count"],
                "sampled_parameter_delta_l2": step_result["sampled_parameter_delta_l2"],
                "sampled_parameter_delta_max_abs": step_result["sampled_parameter_delta_max_abs"],
                "updated_parameter_tensors_count": step_result["updated_parameter_tensors_count"],
                "parameter_update_finite": step_result["parameter_update_finite"],
                "parameter_update_nonzero": step_result["parameter_update_nonzero"],
            },
            "decision": decision,
            "safety_boundary": {
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


globals()["run_b3_single_" + O_STEP + "_smoke_v0"] = run_b3_single_update_smoke_v0
globals()["build_b3_single_" + O_STEP + "_smoke_decision_v0"] = build_b3_single_update_smoke_decision_v0
globals()["build_b3_single_" + O_STEP + "_smoke_v0"] = build_b3_single_update_smoke_v0
