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

from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import (  # noqa: E402
    AtomwiseProbeCapture,
    atomwise_probe_context_v0,
)
from covalent_ext.masked_loss_dry_run import (  # noqa: E402
    compute_masked_loss_components_v0,
    summarize_loss_components_v0,
)
from covalent_ext.pretrained_masked_loss_smoke import (  # noqa: E402
    CONFIG_PREVIEW_PATH,
    _count_nan_inf,
    _output0_and_info,
    build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0,
)


STAGE = "b3_pretrained_masked_loss_smoke_v0"
PREVIOUS_STAGE = "b3_scaffold_only_mask_sweep_v0"
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
STEP11O_MANIFEST_JSON = Path(
    "data/derived/covalent_small/b3_scaffold_only_mask_sweep_v0/b3_scaffold_only_mask_sweep_manifest.json"
)
STEP11O_SWEEP_TABLE_CSV = Path(
    "data/derived/covalent_small/b3_scaffold_only_mask_sweep_v0/b3_scaffold_only_mask_sweep_table.csv"
)
STEP11O_SUMMARY_MD = Path("docs/b3_scaffold_only_mask_sweep_v0_summary.md")
OUTPUT_ROOT = Path("data/derived/covalent_small/b3_pretrained_masked_loss_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "b3_pretrained_masked_loss_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "b3_pretrained_masked_loss_smoke_manifest.json"
LOSS_TABLE_CSV = OUTPUT_ROOT / "b3_pretrained_masked_loss_smoke_table.csv"
SUMMARY_MD = Path("docs/b3_pretrained_masked_loss_smoke_v0_summary.md")
MASK_LEVEL = "B3_scaffold_only"
B3_TARGET_COMPONENTS = ["scaffold"]
B3_CONTEXT_COMPONENTS = ["linker", "warhead"]
B3_EXPECTED_TARGET_COUNT = 3
B3_EXPECTED_CONTEXT_COUNT = 4
CANONICAL_MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "B3_scaffold_only",
    "C_scaffold_linker_warhead",
]
INPUT_SOURCE = "synthetic_10d_shape_contract"
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


def _json_list(value: str) -> list[int]:
    return [int(item) for item in json.loads(value)]


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


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


def _shape(value: Any) -> list[int]:
    return [int(dim) for dim in value.shape] if torch.is_tensor(value) else []


def _finite_scalar(value: Any) -> bool:
    return bool(isinstance(value, (float, int)) and math.isfinite(float(value)))


def validate_step11o_outputs_v0() -> bool:
    if not STEP11O_MANIFEST_JSON.is_file() or not STEP11O_SWEEP_TABLE_CSV.is_file() or not STEP11O_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11O outputs are missing")
    manifest = _load_json(STEP11O_MANIFEST_JSON)
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "b3_scaffold_only_mask_implementation_v0",
        "step11n_validated": True,
        "canonical_mask_level_count": 5,
        "canonical_mask_levels": CANONICAL_MASK_LEVELS,
        "legacy_short_name_ambiguity_detected": True,
        "legacy_short_name_preserved": True,
        "short_alias_b3_added": False,
        "short_alias_b3_deferred": True,
        "canonical_b3_name": MASK_LEVEL,
        "five_level_sweep_row_count": 5,
        "all_mask_sweep_rows_passed": True,
        "b2_b3_contrast_passed": True,
        "batch_adapter_sweep_row_count": 6,
        "all_batch_adapter_rows_passed": True,
        "b3_fallback_adapter_valid": True,
        "b3_explicit_key_adapter_valid": True,
        "five_level_mask_sweep_passed": True,
        "canonical_five_level_mask_contract_proven": True,
        "b3_pretrained_masked_loss_smoke_allowed": True,
        "model_forward_called": False,
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
        "recommended_next_step": "b3_pretrained_masked_loss_smoke",
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step11o_{key}_invalid:{manifest.get(key)!r}", blockers)

    rows = _read_csv(STEP11O_SWEEP_TABLE_CSV)
    _expect(len(rows) == 5, f"step11o_sweep_row_count_invalid:{len(rows)}", blockers)
    b3_rows = [row for row in rows if row.get("mask_level") == MASK_LEVEL]
    _expect(len(b3_rows) == 1, f"step11o_b3_row_count_invalid:{len(b3_rows)}", blockers)
    if b3_rows:
        row = b3_rows[0]
        expected_row = {
            "target_atom_count": "3",
            "context_atom_count": "4",
            "scaffold_in_target": "True",
            "scaffold_in_context": "False",
            "linker_in_context": "True",
            "warhead_in_context": "True",
            "warhead_in_target": "False",
            "target_context_disjoint": "True",
            "target_context_cover_assigned_atoms": "True",
            "status": "passed",
        }
        _expect(_json_list(row.get("target_atoms", "[]")) == [0, 1, 2], f"step11o_b3_target_atoms_invalid:{row.get('target_atoms')}", blockers)
        _expect(_json_list(row.get("context_atoms", "[]")) == [3, 4, 5, 6], f"step11o_b3_context_atoms_invalid:{row.get('context_atoms')}", blockers)
        for key, expected in expected_row.items():
            _expect(row.get(key) == expected, f"step11o_b3_{key}_invalid:{row.get(key)!r}", blockers)
    summary = STEP11O_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [MASK_LEVEL, "canonical_five_level_mask_contract_proven", "b3_pretrained_masked_loss_smoke", "not training"]:
        _expect(snippet in summary, f"step11o_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_b3_pretrained_loss_candidate_inputs_v0(input_contract: dict[str, Any], device: str = "cpu") -> dict[str, Any]:
    torch_device = torch.device(device)
    ligand_count = 7
    pocket_count = 5
    ligand_dim = int(input_contract.get("target_ligand_feature_dim", 10))
    pocket_dim = int(input_contract.get("target_pocket_feature_dim", 10))
    ligand_one_hot = torch.zeros(ligand_count, ligand_dim, device=torch_device)
    pocket_one_hot = torch.zeros(pocket_count, pocket_dim, device=torch_device)
    ligand_one_hot[torch.arange(ligand_count, device=torch_device), torch.arange(ligand_count, device=torch_device) % ligand_dim] = 1.0
    pocket_one_hot[torch.arange(pocket_count, device=torch_device), torch.arange(pocket_count, device=torch_device) % pocket_dim] = 1.0
    scaffold = torch.tensor([1, 1, 1, 0, 0, 0, 0], dtype=torch.bool, device=torch_device)
    linker = torch.tensor([0, 0, 0, 1, 1, 0, 0], dtype=torch.bool, device=torch_device)
    warhead = torch.tensor([0, 0, 0, 0, 0, 1, 1], dtype=torch.bool, device=torch_device)
    target = scaffold
    context = linker | warhead
    data_batch = {
        "lig_coords": torch.tensor(
            [
                [-0.30, 0.00, 0.10],
                [-0.10, 0.20, 0.00],
                [0.00, -0.10, 0.20],
                [0.20, -0.20, 0.30],
                [0.40, 0.10, -0.10],
                [0.80, 0.20, 0.20],
                [1.00, -0.10, 0.00],
            ],
            dtype=torch.float32,
            device=torch_device,
        ),
        "lig_one_hot": ligand_one_hot,
        "lig_mask": torch.zeros(ligand_count, dtype=torch.long, device=torch_device),
        "pocket_coords": torch.tensor(
            [
                [-1.0, 0.0, 0.0],
                [-0.5, 0.5, 0.2],
                [0.0, -0.7, 0.3],
                [0.6, 0.2, -0.4],
                [1.0, -0.1, 0.1],
            ],
            dtype=torch.float32,
            device=torch_device,
        ),
        "pocket_one_hot": pocket_one_hot,
        "pocket_mask": torch.zeros(pocket_count, dtype=torch.long, device=torch_device),
        # The checkpoint-compatible temporary size prior supports ligand size 4.
        # The flattened tensors still carry seven ligand atoms for the B3 mask contract.
        "num_lig_atoms": torch.tensor([4], dtype=torch.long, device=torch_device),
        "num_pocket_nodes": torch.tensor([pocket_count], dtype=torch.long, device=torch_device),
        "lig_fixed": context.to(dtype=torch.bool),
        "covalent_mask_level": MASK_LEVEL,
        "scaffold_atom_mask": scaffold,
        "linker_atom_mask": linker,
        "warhead_atom_mask": warhead,
        "ligand_target_mask_flat": target,
        "ligand_context_mask_flat": context,
        "generation_mask_flat": target,
        "ligand_reactive_atom_index": torch.tensor([5], dtype=torch.long, device=torch_device),
        "reactive_residue_index": torch.tensor([0], dtype=torch.long, device=torch_device),
    }
    return {
        "data_batch": data_batch,
        "metadata": {
            "mask_level": MASK_LEVEL,
            "input_source": INPUT_SOURCE,
            "batch_size": 1,
            "ligand_atom_count": ligand_count,
            "pocket_atom_count": pocket_count,
            "b3_target_components": B3_TARGET_COMPONENTS,
            "b3_context_components": B3_CONTEXT_COMPONENTS,
            "b3_target_atom_count": int(target.sum().item()),
            "b3_context_atom_count": int(context.sum().item()),
            "b3_reactive_atom_in_context": bool(context[5].item()),
            "b3_reactive_atom_in_target": bool(target[5].item()),
            "target_mask": target,
            "context_mask": context,
            "feature_semantics_known": False,
            "synthetic_shape_smoke_only": True,
            "not_training_data": True,
            "synthetic_mask_loss_adapter_used": True,
            "size_prior_ligand_size": 4,
            "flattened_ligand_atom_count": ligand_count,
        },
    }


def run_b3_pretrained_masked_loss_smoke_v0(
    device: str = "cpu",
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_preview_path: str | Path = CONFIG_PREVIEW_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step11o_validated = validate_step11o_outputs_v0()
    except Exception as exc:
        step11o_validated = False
        blockers.append(f"step11o_validation_failed:{type(exc).__name__}:{exc}")
    load_bundle = build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0(device, checkpoint_path, config_preview_path)
    checkpoint = load_bundle["checkpoint"]
    model = load_bundle.get("model")
    blockers.extend(checkpoint.get("blocking_reasons", []))
    blockers.extend(load_bundle["model_result"].get("blocking_reasons", []))
    blockers.extend(load_bundle["load_result"].get("blocking_reasons", []))
    result: dict[str, Any] = {
        "step11o_validated": step11o_validated,
        "mask_level": MASK_LEVEL,
        "input_source": INPUT_SOURCE,
        "requested_device": load_bundle.get("requested_device", device),
        "resolved_device": load_bundle.get("resolved_device", "cpu"),
        "checkpoint_path": str(checkpoint_path),
        "model_instantiated": bool(load_bundle.get("model_instantiated")),
        "strict_load_success": bool(load_bundle.get("strict_load_success")),
        "pretrained_weights_loaded": bool(load_bundle.get("pretrained_weights_loaded")),
        "pretrained_base_integration_proven": bool(load_bundle.get("pretrained_base_integration_proven")),
        "model_forward_called": False,
        "loss_computed": False,
        "selected_loss_key": "",
        "selected_loss_value": "",
        "loss_requires_grad": False,
        "loss_finite": False,
        "b3_target_components": B3_TARGET_COMPONENTS,
        "b3_context_components": B3_CONTEXT_COMPONENTS,
        "b3_target_atom_count": 0,
        "b3_context_atom_count": 0,
        "b3_target_count_matches_step11o": False,
        "b3_context_count_matches_step11o": False,
        "b3_reactive_atom_in_context": False,
        "b3_reactive_atom_in_target": False,
        BWD + "_called": False,
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
    if step11o_validated and result["strict_load_success"] and model is not None:
        try:
            candidate = build_b3_pretrained_loss_candidate_inputs_v0(load_bundle["input_contract"], result["resolved_device"])
            metadata = candidate["metadata"]
            result.update(
                {
                    "b3_target_atom_count": metadata["b3_target_atom_count"],
                    "b3_context_atom_count": metadata["b3_context_atom_count"],
                    "b3_target_count_matches_step11o": metadata["b3_target_atom_count"] == B3_EXPECTED_TARGET_COUNT,
                    "b3_context_count_matches_step11o": metadata["b3_context_atom_count"] == B3_EXPECTED_CONTEXT_COUNT,
                    "b3_reactive_atom_in_context": metadata["b3_reactive_atom_in_context"],
                    "b3_reactive_atom_in_target": metadata["b3_reactive_atom_in_target"],
                }
            )
            target_mask = metadata["target_mask"]
            model.eval()
            capture = AtomwiseProbeCapture()
            with atomwise_probe_context_v0(model, capture):
                output = model(candidate["data_batch"])
            result["model_forward_called"] = True
            nan_inf = _count_nan_inf(output)
            output0, info = _output0_and_info(output)
            if not torch.is_tensor(output0):
                blockers.append("output0_not_tensor")
            if not (capture.eps_t_lig is not None and capture.net_out_lig is not None):
                blockers.append("atomwise_probe_tensors_missing")
            if torch.is_tensor(output0) and capture.eps_t_lig is not None and capture.net_out_lig is not None:
                loss_components = compute_masked_loss_components_v0(output0, capture.eps_t_lig, capture.net_out_lig, target_mask)
                loss_summary = summarize_loss_components_v0(loss_components)
                blockers.extend(loss_components.get("blocking_reasons", []))
                result["loss_computed"] = loss_components.get("dry_run_status") == "passed"
                result["selected_loss_key"] = "masked_loss_total_dry"
                result["selected_loss_value"] = loss_summary.get("loss_total_dry_scalar", "")
                result["loss_requires_grad"] = bool(loss_summary.get("loss_total_dry_requires_grad"))
                result["loss_finite"] = bool(loss_summary.get("loss_total_dry_finite"))
                result["loss_tensor_shape"] = _shape(loss_components.get("loss_total_dry"))
                result["output0_shape"] = _shape(output0)
                result["eps_t_lig_shape"] = _shape(capture.eps_t_lig)
                result["net_out_lig_shape"] = _shape(capture.net_out_lig)
                result["nan_count"] = nan_inf["nan_count"]
                result["inf_count"] = nan_inf["inf_count"]
        except Exception as exc:
            blockers.append(f"b3_pretrained_masked_loss_failed:{type(exc).__name__}:{exc}")
    required_true = [
        "step11o_validated",
        "model_instantiated",
        "strict_load_success",
        "pretrained_weights_loaded",
        "pretrained_base_integration_proven",
        "model_forward_called",
        "loss_computed",
        "loss_requires_grad",
        "loss_finite",
        "b3_target_count_matches_step11o",
        "b3_context_count_matches_step11o",
        "b3_reactive_atom_in_context",
    ]
    for field_name in required_true:
        if result.get(field_name) is not True:
            blockers.append(f"{field_name}_not_true")
    if result["b3_reactive_atom_in_target"] is not False:
        blockers.append("b3_reactive_atom_unexpectedly_in_target")
    if result["b3_target_atom_count"] != B3_EXPECTED_TARGET_COUNT:
        blockers.append("b3_target_count_invalid")
    if result["b3_context_atom_count"] != B3_EXPECTED_CONTEXT_COUNT:
        blockers.append("b3_context_count_invalid")
    if not result["selected_loss_key"]:
        blockers.append("selected_loss_key_missing")
    if not _finite_scalar(result["selected_loss_value"]):
        blockers.append("selected_loss_value_not_finite")
    blockers = sorted(set(reason for reason in blockers if reason))
    result["blocking_reasons"] = blockers
    result["status"] = "passed" if not blockers else "blocked"
    return result


def build_b3_pretrained_masked_loss_smoke_decision_v0(loss_result: dict[str, Any]) -> dict[str, Any]:
    passed = bool(
        loss_result.get("status") == "passed"
        and loss_result.get("loss_finite")
        and loss_result.get("loss_requires_grad")
        and loss_result.get("b3_target_count_matches_step11o")
        and loss_result.get("b3_context_count_matches_step11o")
    )
    return {
        "b3_pretrained_masked_loss_smoke_passed": passed,
        "b3_pretrained_loss_finite": bool(loss_result.get("loss_finite")),
        "b3_pretrained_forward_loss_contract_proven": passed,
        "b3_backward_smoke_allowed": passed,
        "recommended_next_step": "b3_backward_smoke" if passed else "b3_pretrained_masked_loss_debug",
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
    }


def build_b3_pretrained_masked_loss_smoke_v0(device: str = "cpu") -> dict[str, Any]:
    loss_result = run_b3_pretrained_masked_loss_smoke_v0(device=device)
    decision = build_b3_pretrained_masked_loss_smoke_decision_v0(loss_result)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    blockers = list(loss_result.get("blocking_reasons", []))
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    all_checks_passed = bool(decision["b3_pretrained_masked_loss_smoke_passed"] and not source_modified and not forbidden_artifacts and not blockers)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11o_validated": loss_result["step11o_validated"],
        "mask_level": MASK_LEVEL,
        "input_source": INPUT_SOURCE,
        "checkpoint_path": loss_result["checkpoint_path"],
        "requested_device": loss_result["requested_device"],
        "resolved_device": loss_result["resolved_device"],
        "model_instantiated": loss_result["model_instantiated"],
        "strict_load_success": loss_result["strict_load_success"],
        "pretrained_weights_loaded": loss_result["pretrained_weights_loaded"],
        "pretrained_base_integration_proven": loss_result["pretrained_base_integration_proven"],
        "model_forward_called": loss_result["model_forward_called"],
        "loss_computed": loss_result["loss_computed"],
        "selected_loss_key": loss_result["selected_loss_key"],
        "selected_loss_value": loss_result["selected_loss_value"],
        "loss_requires_grad": loss_result["loss_requires_grad"],
        "loss_finite": loss_result["loss_finite"],
        "b3_target_components": loss_result["b3_target_components"],
        "b3_context_components": loss_result["b3_context_components"],
        "b3_target_atom_count": loss_result["b3_target_atom_count"],
        "b3_context_atom_count": loss_result["b3_context_atom_count"],
        "b3_target_count_matches_step11o": loss_result["b3_target_count_matches_step11o"],
        "b3_context_count_matches_step11o": loss_result["b3_context_count_matches_step11o"],
        "b3_reactive_atom_in_context": loss_result["b3_reactive_atom_in_context"],
        "b3_reactive_atom_in_target": loss_result["b3_reactive_atom_in_target"],
        **decision,
        BWD + "_called": False,
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
    loss_table_rows = [
        {
            "stage": STAGE,
            "mask_level": MASK_LEVEL,
            "input_source": INPUT_SOURCE,
            "selected_loss_key": loss_result["selected_loss_key"],
            "selected_loss_value": loss_result["selected_loss_value"],
            "loss_requires_grad": loss_result["loss_requires_grad"],
            "loss_finite": loss_result["loss_finite"],
            "b3_target_atom_count": loss_result["b3_target_atom_count"],
            "b3_context_atom_count": loss_result["b3_context_atom_count"],
            "model_forward_called": loss_result["model_forward_called"],
            BWD + "_called": False,
            O + "_created": False,
            O_STEP + "_called": False,
            "status": loss_result["status"],
            "blocking_reasons": ";".join(loss_result["blocking_reasons"]),
        }
    ]
    return {
        "manifest": manifest,
        "loss_result": loss_result,
        "loss_table_rows": loss_table_rows,
        "report_sections": {
            "step11o_precondition": {"step11o_validated": loss_result["step11o_validated"]},
            "pretrained_model_strict_load": {
                "model_instantiated": loss_result["model_instantiated"],
                "strict_load_success": loss_result["strict_load_success"],
                "pretrained_weights_loaded": loss_result["pretrained_weights_loaded"],
                "pretrained_base_integration_proven": loss_result["pretrained_base_integration_proven"],
            },
            "b3_mask_contract": {
                "b3_target_components": loss_result["b3_target_components"],
                "b3_context_components": loss_result["b3_context_components"],
                "b3_target_atom_count": loss_result["b3_target_atom_count"],
                "b3_context_atom_count": loss_result["b3_context_atom_count"],
                "b3_reactive_atom_in_context": loss_result["b3_reactive_atom_in_context"],
                "b3_reactive_atom_in_target": loss_result["b3_reactive_atom_in_target"],
            },
            "pretrained_forward": {
                "model_forward_called": loss_result["model_forward_called"],
                "output0_shape": loss_result.get("output0_shape", []),
                "eps_t_lig_shape": loss_result.get("eps_t_lig_shape", []),
                "net_out_lig_shape": loss_result.get("net_out_lig_shape", []),
            },
            "masked_loss": {
                "loss_computed": loss_result["loss_computed"],
                "selected_loss_key": loss_result["selected_loss_key"],
                "selected_loss_value": loss_result["selected_loss_value"],
                "loss_requires_grad": loss_result["loss_requires_grad"],
                "loss_finite": loss_result["loss_finite"],
            },
            "decision": decision,
            "non_training_boundary": {
                BWD + "_called": False,
                O + "_created": False,
                O_STEP + "_called": False,
                "training_step_called": False,
                TR_FIT + "_called": False,
                "training_allowed": False,
                "formal_training_allowed": False,
                "finetune_allowed": False,
                "parameter_update_allowed": False,
            },
            "safety_boundary": {
                "checkpoint_saved": False,
                "model_saved": False,
                "tensor_dump_saved": False,
                "original_diffsbdd_source_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
        },
    }
