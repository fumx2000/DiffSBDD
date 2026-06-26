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

from covalent_ext.checkpoint_original_config_instantiation_design import (  # noqa: E402
    CONFIG_PREVIEW_JSON,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_checkpoint_original_config_instantiation_design_v0,
)


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


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _list_text(values: Any) -> str:
    if isinstance(values, list):
        return ";".join(str(value) for value in values)
    return "" if values is None else str(values)


def write_csv(rows: list[dict[str, str]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    sections = result["report_sections"]
    recommended = manifest["recommended_next_step"]
    checkpoint = sections["checkpoint_hparams"]
    current = sections["current_config"]
    candidate = sections["best_candidate"]
    paths = sections["instantiation_paths"]
    wrapper = sections["wrapper_design"]
    decision = sections["decision"]
    safety = sections["safety"]
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11b_precondition",
            "status": "passed" if manifest["step11b_validated"] else "blocked",
            "evidence": _json_text(sections["step11b"]),
            "decision": "Step 11B reconciliation is accepted as design input.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "checkpoint_hparams_for_design",
            "status": "passed" if checkpoint["checkpoint_hparams_complete_for_instantiation"] else "blocked",
            "evidence": _json_text(
                {
                    "checkpoint_sha256": checkpoint["checkpoint_sha256"],
                    "hparams_keys": checkpoint["hyper_parameters_keys"],
                    "target_joint_nf": checkpoint["checkpoint_target_joint_nf"],
                    "target_hidden_nf": checkpoint["checkpoint_target_hidden_nf"],
                    "target_n_layers": checkpoint["checkpoint_target_n_layers"],
                    "target_mode": checkpoint["checkpoint_target_mode"],
                    "target_pocket_representation": checkpoint["checkpoint_target_pocket_representation"],
                    "target_atom_feature_dim": checkpoint["checkpoint_target_atom_feature_dim"],
                    "target_residue_feature_dim": checkpoint["checkpoint_target_residue_feature_dim"],
                }
            ),
            "decision": "Checkpoint hparams are complete enough to design a compatible instantiation path.",
            "blocking_reasons": _list_text(checkpoint["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "current_and_candidate_config_review",
            "status": "passed" if current["config_loaded"] and candidate["config_loaded"] else "blocked",
            "evidence": _json_text(
                {
                    "current_config": {
                        "path": current["config_path"],
                        "joint_nf": current["joint_nf"],
                        "hidden_nf": current["hidden_nf"],
                        "n_layers": current["n_layers"],
                        "mode": current["mode"],
                        "pocket_representation": current["pocket_representation"],
                    },
                    "best_candidate": {
                        "path": candidate["config_path"],
                        "joint_nf": candidate["joint_nf"],
                        "hidden_nf": candidate["hidden_nf"],
                        "n_layers": candidate["n_layers"],
                        "mode": candidate["mode"],
                        "pocket_representation": candidate["pocket_representation"],
                    },
                }
            ),
            "decision": "Candidate config is dimension-close but still needs mode override.",
            "blocking_reasons": _list_text(current["blocking_reasons"] + candidate["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "existing_instantiation_path_review",
            "status": "passed",
            "evidence": _json_text(
                {
                    "helpers": paths["helper_function_names"],
                    "signatures": paths["helper_signature_summaries"],
                    "config_path_hardcoded_or_defaulted": paths["config_path_hardcoded_or_defaulted"],
                    "safe_config_override_supported": paths["safe_config_override_supported"],
                    "safe_config_override_blockers": paths["safe_config_override_blockers"],
                }
            ),
            "decision": "Existing helper path does not expose a safe config override.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "checkpoint_original_config_preview",
            "status": "passed" if manifest["config_preview_written"] else "blocked",
            "evidence": _json_text(
                {
                    "config_preview_path": manifest["config_preview_path"],
                    "expected_shape_match_goal": manifest["expected_shape_match_goal"],
                    "target_joint_nf": manifest["checkpoint_target_joint_nf"],
                    "target_hidden_nf": manifest["checkpoint_target_hidden_nf"],
                    "target_n_layers": manifest["checkpoint_target_n_layers"],
                }
            ),
            "decision": "A JSON preview records the checkpoint-compatible target config without editing configs.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "wrapper_design",
            "status": "passed",
            "evidence": _json_text(wrapper),
            "decision": "A covalent_ext wrapper should prototype checkpoint-compatible instantiation next.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "design_decision",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(decision),
            "decision": "Design remains pre-training and blocks masked loss smoke for now.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(safety),
            "decision": "No training, optimizer, checkpoint save, or model save occurred.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
    ]


def write_summary(manifest: dict[str, Any], preview: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Checkpoint Original Config Instantiation Design v0 Summary",
        "",
        "Step 11C is a design step, not training.",
        "Step 11B showed that the current config and checkpoint original config are inconsistent.",
        "",
        "## Checkpoint Target Config",
        f"- joint_nf: {manifest['checkpoint_target_joint_nf']}",
        f"- hidden_nf: {manifest['checkpoint_target_hidden_nf']}",
        f"- n_layers: {manifest['checkpoint_target_n_layers']}",
        f"- mode: {manifest['checkpoint_target_mode']}",
        f"- pocket_representation: {manifest['checkpoint_target_pocket_representation']}",
        f"- atom feature dim: {manifest['checkpoint_target_atom_feature_dim']}",
        f"- residue feature dim: {manifest['checkpoint_target_residue_feature_dim']}",
        "",
        "## Current Config",
        f"- joint_nf: {manifest['current_config_joint_nf']}",
        f"- hidden_nf: {manifest['current_config_hidden_nf']}",
        f"- n_layers: {manifest['current_config_n_layers']}",
        "- atom feature dim: 11",
        "",
        "The current model must not proceed directly to pretrained masked loss smoke.",
        f"The checkpoint original config preview is written to `{manifest['config_preview_path']}`.",
        f"Wrapper needed: {not manifest['safe_config_override_supported']}",
        f"Proposed wrapper: `{manifest['proposed_wrapper_name']}` in `{manifest['proposed_wrapper_location']}`.",
        "",
        "## Design Decision",
        f"- design_status: {manifest['design_status']}",
        f"- checkpoint_compatible_instantiation_feasible: {manifest['checkpoint_compatible_instantiation_feasible']}",
        f"- expected_shape_match_goal: {json.dumps(manifest['expected_shape_match_goal'], sort_keys=True)}",
        f"- recommended_next_step: {manifest['recommended_next_step']}",
        "",
        "Training, fine-tuning, and masked loss smoke remain forbidden until checkpoint-compatible instantiation is proven.",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def run() -> int:
    result = build_checkpoint_original_config_instantiation_design_v0()
    manifest = result["manifest"]
    preview = result["config_preview"]
    write_json(preview, CONFIG_PREVIEW_JSON)
    write_json(manifest, MANIFEST_JSON)
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_summary(manifest, preview, SUMMARY_MD)
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    code = run()
    print(
        "checkpoint_original_config_instantiation_design_v0_passed"
        if code == 0
        else "checkpoint_original_config_instantiation_design_v0_blocked"
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
