from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext.model_input_adapter import expected_reactive_atom_region_for_mask_level_v0


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_pretraining_smoke_design_v0"
PREVIOUS_STAGE = "real_covalent_feature_mapping_loader_gate_v0"
PLANNED_NEXT_STAGE = "real_covalent_pretrained_forward_loss_smoke_v0"

STEP12A_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_feature_mapping_loader_gate_v0/"
    "real_covalent_feature_mapping_loader_gate_manifest.json"
)
STEP12A_SAMPLE_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_feature_mapping_loader_gate_v0/"
    "real_covalent_feature_mapping_loader_gate_sample_table.csv"
)
STEP12A_SUMMARY_MD = Path("docs/real_covalent_feature_mapping_loader_gate_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_pretraining_smoke_design_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_pretraining_smoke_design_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_pretraining_smoke_design_manifest.json"
PLAN_TABLE_CSV = OUTPUT_ROOT / "real_covalent_pretraining_smoke_design_plan_table.csv"
SUMMARY_MD = Path("docs/real_covalent_pretraining_smoke_design_v0_summary.md")

CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
SELECTED_REAL_SAMPLE_INDEX = Path("data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv")

CANONICAL_MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "B3_scaffold_only",
    "C_scaffold_linker_warhead",
]

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


def _source_diff_exists(paths: list[str] = PROTECTED_SOURCE_PATHS) -> bool:
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *paths],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *paths],
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


def validate_step12a_outputs_v0() -> bool:
    if not STEP12A_MANIFEST_JSON.is_file() or not STEP12A_SAMPLE_TABLE_CSV.is_file() or not STEP12A_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12A outputs are missing")
    manifest = _load_json(STEP12A_MANIFEST_JSON)
    rows = _read_csv(STEP12A_SAMPLE_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "b3_single_optimizer_step_smoke_v0",
        "step11r_validated": True,
        "selected_real_data_root": "data/derived/covalent_small/training_tensor_materialized_v0",
        "selected_loader_or_tensor_artifact": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "audited_real_sample_count": 3,
        "passed_real_sample_count": 3,
        "failed_real_sample_count": 0,
        "all_five_level_masks_available": True,
        "real_five_level_mask_contract_proven": True,
        "real_b3_target_is_scaffold": True,
        "real_b3_context_is_linker_warhead": True,
        "real_b3_reactive_atom_in_context": True,
        "real_b3_reactive_atom_in_target": False,
        "real_b2_b3_contrast_passed": True,
        "dataset_created": True,
        "dataloader_created": True,
        "batch_size": 2,
        "real_batch_adapter_gate_passed": True,
        "real_model_input_mapping_gate_passed": True,
        "real_covalent_feature_mapping_loader_gate_passed": True,
        "real_covalent_sample_field_contract_proven": True,
        "real_b3_loader_contract_proven": True,
        "real_covalent_pretraining_smoke_allowed": True,
        "recommended_next_step": "real_covalent_pretraining_smoke_design",
        "model_forward_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "all_checks_passed": True,
    }
    for key, value in expected.items():
        _expect(manifest.get(key) == value, f"step12a_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(manifest.get("canonical_mask_levels") == CANONICAL_MASK_LEVELS, "step12a_canonical_mask_levels_invalid", blockers)
    _expect(len(rows) == 3, f"step12a_sample_table_row_count_invalid:{len(rows)}", blockers)
    _expect({row.get("status") for row in rows} == {"passed"}, "step12a_sample_table_not_all_passed", blockers)

    expected_regions = {
        "A_warhead_only": "target",
        "B_linker_warhead": "target",
        "B2_scaffold_warhead": "target",
        "B3_scaffold_only": "context",
        "C_scaffold_linker_warhead": "target",
    }
    for mask_level, expected_region in expected_regions.items():
        _expect(
            expected_reactive_atom_region_for_mask_level_v0(mask_level) == expected_region,
            f"step12b_region_invalid:{mask_level}",
            blockers,
        )
    try:
        expected_reactive_atom_region_for_mask_level_v0("B3")
    except ValueError:
        short_b3_rejected = True
    else:
        short_b3_rejected = False
    _expect(short_b3_rejected, "step12b_short_alias_b3_accepted", blockers)
    summary = STEP12A_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "Real Covalent Feature Mapping Loader Gate",
        "not training",
        "recommended_next_step: real_covalent_pretraining_smoke_design",
    ]:
        _expect(snippet in summary, f"step12a_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_real_covalent_pretraining_smoke_plan_v0() -> dict[str, Any]:
    success_criteria = [
        "Step 12A validated",
        "Step 12B mask-level-aware validator behavior validated",
        "selected artifact is real covalent and not synthetic-only",
        "read-only Dataset/DataLoader created with batch_size=2 and num_workers=0",
        "adapted batch valid for each canonical mask level",
        "model input valid with mask_level-aware validator for each canonical mask level",
        "DiffSBDD-like input valid for each canonical mask level",
        "checkpoint-compatible real model batch constructed",
        "fresh pretrained model strict-loaded",
        "model forward called exactly once per mask level",
        "masked loss computed and finite for each mask level",
        "selected loss requires_grad=true",
        "no backward or optimizer",
        "no training_step or trainer.fit",
        "no checkpoint/model/tensor dump or forbidden artifact",
        "no protected source modification",
    ]
    blocking_criteria = [
        "Step 12A or Step 12B validation fails",
        "selected artifact is missing, synthetic-only, or not real covalent",
        "real batch cannot be converted into checkpoint-compatible model input",
        "any canonical mask level fails adapted batch, model input, or DiffSBDD-like input validation",
        "fresh pretrained strict load fails",
        "model forward or masked loss is not finite",
        "synthetic fallback is required",
        "any forbidden execution or output occurs",
    ]
    planned_outputs = [
        "real_covalent_pretrained_forward_loss_smoke_report.csv",
        "real_covalent_pretrained_forward_loss_smoke_manifest.json",
        "real_covalent_pretrained_forward_loss_smoke_loss_table.csv",
        "docs/real_covalent_pretrained_forward_loss_smoke_v0_summary.md",
    ]
    plan_table_rows = []
    for mask_level in CANONICAL_MASK_LEVELS:
        plan_table_rows.append(
            {
                "planned_stage": PLANNED_NEXT_STAGE,
                "mask_level": mask_level,
                "expected_reactive_atom_region": expected_reactive_atom_region_for_mask_level_v0(mask_level),
                "planned_batch_size": 2,
                "planned_allow_model_forward": True,
                "planned_allow_loss_compute": True,
                "planned_allow_backward": False,
                "planned_allow_optimizer": False,
                "planned_allow_optimizer_step": False,
                "planned_use_synthetic_fallback": False,
                "status": "planned",
            }
        )
    return {
        "planned_stage": PLANNED_NEXT_STAGE,
        "planned_input_source": "real_covalent_training_tensor_materialized_v0",
        "planned_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "planned_checkpoint_path": str(CHECKPOINT_PATH),
        "planned_device_default": "cpu",
        "planned_batch_size": 2,
        "planned_num_workers": 0,
        "planned_mask_levels": list(CANONICAL_MASK_LEVELS),
        "planned_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "planned_use_mask_level_aware_validator": True,
        "planned_use_synthetic_fallback": False,
        "planned_allow_model_forward": True,
        "planned_allow_loss_compute": True,
        "planned_allow_backward": False,
        "planned_allow_optimizer": False,
        "planned_allow_optimizer_step": False,
        "planned_allow_training_step": False,
        "planned_allow_trainer_fit": False,
        "planned_allow_checkpoint_save": False,
        "planned_allow_model_save": False,
        "planned_allow_tensor_dump": False,
        "planned_forbidden_artifact_suffixes": sorted(FORBIDDEN_ARTIFACT_SUFFIXES),
        "planned_success_criteria": success_criteria,
        "planned_blocking_criteria": blocking_criteria,
        "planned_outputs": planned_outputs,
        "plan_table_rows": plan_table_rows,
    }


def build_real_covalent_pretraining_smoke_design_decision_v0(plan: dict[str, Any]) -> dict[str, Any]:
    passed = bool(
        plan["planned_stage"] == PLANNED_NEXT_STAGE
        and plan["planned_input_source"] == "real_covalent_training_tensor_materialized_v0"
        and plan["planned_mask_levels"] == CANONICAL_MASK_LEVELS
        and plan["planned_use_mask_level_aware_validator"] is True
        and plan["planned_use_synthetic_fallback"] is False
        and plan["planned_allow_model_forward"] is True
        and plan["planned_allow_loss_compute"] is True
        and plan["planned_allow_backward"] is False
        and plan["planned_allow_optimizer"] is False
        and plan["planned_allow_optimizer_step"] is False
        and plan["planned_allow_training_step"] is False
        and plan["planned_allow_trainer_fit"] is False
        and plan["planned_allow_checkpoint_save"] is False
        and plan["planned_allow_model_save"] is False
        and plan["planned_allow_tensor_dump"] is False
    )
    return {
        "real_covalent_pretraining_smoke_design_passed": passed,
        "real_covalent_forward_loss_smoke_plan_ready": passed,
        "real_covalent_forward_loss_smoke_allowed": passed,
        "recommended_next_step": "real_covalent_pretrained_forward_loss_smoke"
        if passed
        else "real_covalent_pretraining_smoke_design_debug",
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
    }


def build_real_covalent_pretraining_smoke_design_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12a_validated = validate_step12a_outputs_v0()
        step12b_validated = True
    except Exception as exc:
        step12a_validated = False
        step12b_validated = False
        blockers.append(f"step12a_or_step12b_validation_failed:{type(exc).__name__}:{exc}")
    step12a_manifest = _load_json(STEP12A_MANIFEST_JSON) if STEP12A_MANIFEST_JSON.is_file() else {}
    plan = build_real_covalent_pretraining_smoke_plan_v0()
    decision = build_real_covalent_pretraining_smoke_design_decision_v0(plan)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    all_checks_passed = bool(
        step12a_validated
        and step12b_validated
        and decision["real_covalent_pretraining_smoke_design_passed"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12a_validated": step12a_validated,
        "step12b_mask_level_aware_validator_validated": step12b_validated,
        "selected_real_data_root": step12a_manifest.get("selected_real_data_root", ""),
        "selected_sample_index": step12a_manifest.get("selected_loader_or_tensor_artifact", ""),
        "selected_artifact_is_real_covalent": bool(step12a_manifest.get("selected_artifact_is_real_covalent")),
        "selected_artifact_is_synthetic_only": bool(step12a_manifest.get("selected_artifact_is_synthetic_only")),
        "planned_next_stage": plan["planned_stage"],
        "planned_input_source": plan["planned_input_source"],
        "planned_sample_index": plan["planned_sample_index"],
        "planned_checkpoint_path": plan["planned_checkpoint_path"],
        "planned_device_default": plan["planned_device_default"],
        "planned_batch_size": plan["planned_batch_size"],
        "planned_num_workers": plan["planned_num_workers"],
        "planned_mask_levels": plan["planned_mask_levels"],
        "planned_mask_level_count": plan["planned_mask_level_count"],
        "planned_use_mask_level_aware_validator": plan["planned_use_mask_level_aware_validator"],
        "planned_use_synthetic_fallback": plan["planned_use_synthetic_fallback"],
        "planned_allow_model_forward": plan["planned_allow_model_forward"],
        "planned_allow_loss_compute": plan["planned_allow_loss_compute"],
        "planned_allow_backward": plan["planned_allow_backward"],
        "planned_allow_optimizer": plan["planned_allow_optimizer"],
        "planned_allow_optimizer_step": plan["planned_allow_optimizer_step"],
        "planned_allow_training_step": plan["planned_allow_training_step"],
        "planned_allow_trainer_fit": plan["planned_allow_trainer_fit"],
        "planned_allow_checkpoint_save": plan["planned_allow_checkpoint_save"],
        "planned_allow_model_save": plan["planned_allow_model_save"],
        "planned_allow_tensor_dump": plan["planned_allow_tensor_dump"],
        "planned_forbidden_artifact_suffixes": plan["planned_forbidden_artifact_suffixes"],
        "planned_success_criteria": plan["planned_success_criteria"],
        "planned_blocking_criteria": plan["planned_blocking_criteria"],
        "planned_outputs": plan["planned_outputs"],
        **decision,
        "model_forward_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blockers,
    }
    return {
        "manifest": manifest,
        "plan": plan,
        "plan_table_rows": plan["plan_table_rows"],
        "report_sections": {
            "step12a_precondition": {"step12a_validated": step12a_validated},
            "step12b_validator_contract": {
                "step12b_mask_level_aware_validator_validated": step12b_validated,
                "expected_reactive_atom_regions": {
                    mask_level: expected_reactive_atom_region_for_mask_level_v0(mask_level)
                    for mask_level in CANONICAL_MASK_LEVELS
                },
                "short_alias_b3_rejected": True,
            },
            "selected_real_artifact": {
                "selected_real_data_root": manifest["selected_real_data_root"],
                "selected_sample_index": manifest["selected_sample_index"],
                "selected_artifact_is_real_covalent": manifest["selected_artifact_is_real_covalent"],
                "selected_artifact_is_synthetic_only": manifest["selected_artifact_is_synthetic_only"],
            },
            "planned_mask_levels": {
                "planned_mask_levels": plan["planned_mask_levels"],
                "planned_mask_level_count": plan["planned_mask_level_count"],
            },
            "planned_forward_loss_smoke_scope": {
                key: plan[key]
                for key in [
                    "planned_stage",
                    "planned_input_source",
                    "planned_sample_index",
                    "planned_checkpoint_path",
                    "planned_batch_size",
                    "planned_num_workers",
                    "planned_use_mask_level_aware_validator",
                    "planned_use_synthetic_fallback",
                    "planned_allow_model_forward",
                    "planned_allow_loss_compute",
                ]
            },
            "planned_safety_boundary": {
                key: plan[key]
                for key in [
                    "planned_allow_backward",
                    "planned_allow_optimizer",
                    "planned_allow_optimizer_step",
                    "planned_allow_training_step",
                    "planned_allow_trainer_fit",
                    "planned_allow_checkpoint_save",
                    "planned_allow_model_save",
                    "planned_allow_tensor_dump",
                ]
            },
            "decision": decision,
            "artifact_safety": {
                "original_diffsbdd_source_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
        },
    }
