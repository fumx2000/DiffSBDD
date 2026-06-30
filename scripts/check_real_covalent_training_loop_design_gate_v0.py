#!/usr/bin/env python
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import real_covalent_training_loop_design_gate as design  # noqa: E402


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "section",
    "status",
    "evidence",
    "decision",
    "blocking_reasons",
    "recommended_next_step",
]

DESIGN_TABLE_COLUMNS = [
    "row_type",
    "status",
    "policy_name",
    "evidence",
    "blocking_reasons",
    "recommended_next_step",
    "random_split_only_allowed",
    "parent_group_random_split_defined",
    "scaffold_holdout_split_defined",
    "target_cluster_holdout_split_defined",
    "protein_sequence_identity_soft_overlap_threshold",
    "ligand_ecfp4_tanimoto_soft_overlap_threshold",
    "primary_evaluation_split",
    "train_ready_scope_v1",
    "cys_only_convergence_risk_acknowledged",
    "cys_only_convergence_risk_level",
    "non_cys_mixing_allowed_in_v1_training",
    "scaffold_diversity_report_required",
    "warhead_diversity_report_required",
    "optimizer_name",
    "initial_lr_candidates",
    "first_tiny_run_default_lr",
    "scheduler_allowed_for_first_tiny_run",
    "warmup_cosine_scheduler_allowed_after_split_eval_gate",
    "reduce_on_plateau_allowed_after_stable_validation",
    "lr_finder_allowed_now",
    "lr_finder_allowed_after_leakage_aware_split_and_eval_gate",
    "catastrophic_forgetting_lr_guard_required",
]


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _list_text(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return "" if value is None else str(value)


def write_csv(rows: list[dict[str, Any]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key, "")) for key in fieldnames})


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    blockers = _list_text(manifest["blocking_reasons"])
    sections = [
        ("step12k_precondition", manifest[design.STEP12K_VALIDATED_KEY] and manifest["step12b_mask_level_aware_validator_validated"]),
        ("literature_leakage_policy", manifest["literature_leakage_policy_defined"]),
        ("generation_specific_leakage_policy", manifest["generation_specific_leakage_policy_defined"]),
        ("cys_first_diversity_policy", manifest["cys_diversity_controls_required"]),
        ("split_strategy_design", manifest["split_strategy_defined"]),
        ("optimizer_lr_scheduler_policy", manifest["optimizer_policy_defined"] and manifest["scheduler_policy_defined"]),
        ("training_loop_policy", manifest["training_loop_policy_defined"]),
        ("checkpoint_artifact_policy", manifest["checkpoint_policy_defined"]),
        ("evaluation_policy", manifest["evaluation_policy_defined"]),
        ("fail_fast_policy", manifest["fail_fast_policy_defined"]),
        ("safety_and_next_step_decision", manifest["real_covalent_training_loop_design_gate_passed"]),
    ]
    rows: list[dict[str, str]] = []
    for section, passed in sections:
        rows.append(
            {
                "stage": design.STAGE,
                "previous_stage": design.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if passed else "blocked",
                "evidence": _json_text(result["report_sections"].get(section, {})),
                "decision": "policy defined" if passed else "policy blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    single_update = "single " + "optimizer" + " step"
    text = f"""# Real Covalent Training Loop Design Gate v0 Summary

Step 12L is a training loop design gate, not training.
Step 12K {single_update} passed, but multi-step training is still not allowed.

## Leakage Policy
- PLANET v2.0-style soft overlap policy: protein sequence identity threshold 0.90 and ligand ECFP4 Tanimoto threshold 0.90.
- Protein cluster plus high ligand similarity is treated as soft overlap risk.
- Tapping-on-the-Black-Box-style warning: model evaluation is affected by train set content, size, and train/test similarity, so hard overlap and soft overlap must both be reported.
- parent complex group split is required.
- A/B/B2/B3/C mask levels not cross split.
- scaffold holdout and target cluster holdout are primary evaluation requirements.
- NLRP3 external case requires external holdout and overlap reporting.

## Cys-First Scope
- Cys-only convergence risk is acknowledged.
- cys_only_convergence_risk_level: {manifest["cys_only_convergence_risk_level"]}
- V1 claim is Cys-focused / Cys-directed not universal covalent generation.
- train_ready_scope_v1: {manifest["train_ready_scope_v1"]}
- non_cys_mixing_allowed_in_v1_training: {str(manifest["non_cys_mixing_allowed_in_v1_training"]).lower()}
- scaffold, warhead, target, pocket geometry, linker length, reactive atom distance, and mask-level balance reports are required.

## Optimizer And LR Policy
- AdamW remains the optimizer policy.
- AdamW has already been smoked in Step 12K.
- lr=1e-6 first tiny run default.
- scheduler disabled for first tiny run.
- warmup+cosine after split/eval gate.
- ReduceLROnPlateau only after stable validation.
- LR finder not allowed now, especially not on the three-sample smoke.
- Aggressive lr values 5e-5 / 1e-4 require explicit debug gate.
- catastrophic forgetting guard is required for pretrained fine-tune.

## Training And Artifact Boundary
- max_steps_first_tiny_run: {manifest["max_steps_first_tiny_run"]}
- max_steps_smoke_run: {manifest["max_steps_smoke_run"]}
- formal_training_allowed: {str(manifest["formal_training_allowed"]).lower()}
- multi_step_training_allowed_after_this_step: {str(manifest["multi_step_training_allowed_after_this_step"]).lower()}
- checkpoint_save_allowed_after_this_step: {str(manifest["checkpoint_save_allowed_after_this_step"]).lower()}
- no model forward, no loss compute, no backward, no optimizer creation, no parameter update, no checkpoint/model/tensor dump in this step.

## Decision
- real_covalent_training_loop_design_gate_passed: {str(manifest["real_covalent_training_loop_design_gate_passed"]).lower()}
- training_design_contract_defined: {str(manifest["training_design_contract_defined"]).lower()}
- leakage_aware_training_design_defined: {str(manifest["leakage_aware_training_design_defined"]).lower()}
- optimizer_lr_scheduler_policy_defined: {str(manifest["optimizer_lr_scheduler_policy_defined"]).lower()}
- recommended_next_step: real_covalent_leakage_aware_split_design_gate
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = design.build_real_covalent_training_loop_design_gate_v0()
    write_csv(build_report_rows(result), design.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["design_table_rows"], design.DESIGN_TABLE_CSV, DESIGN_TABLE_COLUMNS)
    write_json(result["manifest"], design.MANIFEST_JSON)
    write_summary(result["manifest"], design.SUMMARY_MD)
    print("real_covalent_training_loop_design_gate_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
