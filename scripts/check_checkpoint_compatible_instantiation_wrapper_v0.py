#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext.checkpoint_compatible_model_instantiation import (  # noqa: E402
    CHECKPOINT_PATH,
    CONFIG_PREVIEW_PATH,
    INPUT_CONTRACT_PREVIEW_JSON,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    SHAPE_MATCH_TABLE_CSV,
    STAGE,
    SUMMARY_MD,
    build_checkpoint_compatible_instantiation_wrapper_v0,
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

SHAPE_TABLE_COLUMNS = [
    "key",
    "category",
    "checkpoint_shape",
    "model_shape",
    "status",
    "inferred_reason",
    "checkpoint_numel",
    "model_numel",
]


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _list_text(values: Any) -> str:
    if isinstance(values, list):
        return ";".join(str(value) for value in values)
    return "" if values is None else str(values)


def write_csv(rows: list[dict[str, Any]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _compact_model_instantiation_evidence(section: dict[str, Any]) -> dict[str, Any]:
    return {
        "model_instantiation_attempted": section["model_instantiation_attempted"],
        "model_instantiated": section["model_instantiated"],
        "model_class": section["model_class"],
        "requested_device": section["requested_device"],
        "resolved_device": section["resolved_device"],
        "model_state_dict_key_count": section["model_state_dict_key_count"],
        "trainable_parameter_count": section["trainable_parameter_count"],
        "wrapper_status": section["wrapper_status"],
        "blocking_reasons": section["blocking_reasons"],
    }


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    sections = result["report_sections"]
    recommended = manifest["recommended_next_step"]
    checkpoint = sections["checkpoint_reference"]
    preview = sections["config_preview"]
    compatible_config = sections["compatible_config"]
    input_contract = sections["input_contract"]
    instantiation = sections["model_instantiation"]
    shape = sections["shape_match_analysis"]
    forward = sections["optional_forward_smoke"]
    decision = sections["decision"]
    safety = sections["safety_boundary"]
    blockers = manifest["blocking_reasons"]
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11c_precondition",
            "status": "passed" if manifest["step11c_validated"] else "blocked",
            "evidence": _json_text(sections["step11c"]),
            "decision": "Step 11C design outputs are accepted as wrapper inputs.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "checkpoint_reference",
            "status": "passed" if checkpoint["has_state_dict"] else "blocked",
            "evidence": _json_text(
                {
                    "checkpoint_sha256": checkpoint["checkpoint_sha256"],
                    "checkpoint_size_bytes": checkpoint["checkpoint_size_bytes"],
                    "state_dict_key_count": checkpoint["state_dict_key_count"],
                    "target_fields": checkpoint["checkpoint_target_fields"],
                }
            ),
            "decision": "Checkpoint state_dict shapes and target hparams are readable.",
            "blocking_reasons": _list_text(checkpoint["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "config_preview",
            "status": "passed" if preview["config_preview_loaded"] else "blocked",
            "evidence": _json_text(
                {
                    "target_egnn_params": preview["preview"].get("target_egnn_params"),
                    "target_mode": preview["preview"].get("target_mode"),
                    "target_pocket_representation": preview["preview"].get("target_pocket_representation"),
                    "target_atom_feature_dim": preview["preview"].get("target_atom_feature_dim"),
                    "target_residue_feature_dim": preview["preview"].get("target_residue_feature_dim"),
                }
            ),
            "decision": "Step 11C preview supplies checkpoint original architecture targets.",
            "blocking_reasons": _list_text(preview["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "compatible_config_build",
            "status": "passed" if compatible_config["compatible_config_built"] else "blocked",
            "evidence": _json_text(
                {
                    "source": compatible_config.get("compatible_config_source"),
                    "overrides": compatible_config.get("compatible_config_overrides"),
                    "relevant_fields": compatible_config.get("compatible_config_flattened_relevant_fields"),
                    "unresolved_fields": compatible_config.get("unresolved_fields"),
                }
            ),
            "decision": "In-memory config overrides are built without editing repo config files.",
            "blocking_reasons": _list_text(compatible_config["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "input_contract",
            "status": "passed" if input_contract["input_contract_built"] else "blocked",
            "evidence": _json_text(input_contract),
            "decision": "A 10D shape-only input contract is recorded for constructor compatibility.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "model_instantiation",
            "status": "passed" if instantiation["model_instantiated"] else "blocked",
            "evidence": _json_text(_compact_model_instantiation_evidence(instantiation)),
            "decision": "Checkpoint-compatible LigandPocketDDPM constructor path was exercised in memory.",
            "blocking_reasons": _list_text(instantiation["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "shape_match_analysis",
            "status": "passed" if shape["reached_shape_match_goal"] else "blocked",
            "evidence": _json_text(shape),
            "decision": "Shape match improved over Step 11A and determines whether checkpoint load smoke is allowed.",
            "blocking_reasons": _list_text(blockers),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "optional_forward_smoke",
            "status": "skipped" if not forward["forward_smoke_attempted"] else ("passed" if forward["forward_smoke_success"] else "blocked"),
            "evidence": _json_text(forward),
            "decision": "No-grad forward smoke remains deferred because this step is a shape compatibility prototype.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "decision",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(decision),
            "decision": "Checkpoint-compatible pretrained load smoke is allowed only after shape compatibility is proven.",
            "blocking_reasons": _list_text(blockers),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(safety),
            "decision": "No training, optimizer, checkpoint save, model save, or source modification occurred.",
            "blocking_reasons": _list_text(blockers),
            "recommended_next_step": recommended,
        },
    ]


def write_summary(manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Checkpoint-Compatible Instantiation Wrapper v0 Summary",
        "",
        "Step 11D is a checkpoint-compatible instantiation wrapper prototype, not training.",
        "It does not load checkpoint weights into the model, does not run masked loss smoke, and does not save model artifacts.",
        "",
        "## Target Architecture",
        f"- joint_nf: {manifest['target_joint_nf']}",
        f"- hidden_nf: {manifest['target_hidden_nf']}",
        f"- n_layers: {manifest['target_n_layers']}",
        f"- mode: {manifest['target_mode']}",
        f"- pocket_representation: {manifest['target_pocket_representation']}",
        f"- atom/residue feature dim: {manifest['target_atom_feature_dim']} / {manifest['target_residue_feature_dim']}",
        "",
        "## Result",
        f"- model_instantiated: {str(manifest['model_instantiated']).lower()}",
        f"- model_class: {manifest['model_class']}",
        f"- shape match: {manifest['shape_matched_key_count']}/{manifest['checkpoint_state_dict_key_count']} = {manifest['shape_matched_ratio']}",
        f"- previous Step 11A shape match: {manifest['previous_shape_matched_ratio']}",
        f"- reached_shape_match_goal: {str(manifest['reached_shape_match_goal']).lower()}",
        f"- wrapper_status: {manifest['wrapper_status']}",
        f"- checkpoint_load_smoke_allowed: {str(manifest['checkpoint_load_smoke_allowed']).lower()}",
        f"- recommended_next_step: {manifest['recommended_next_step']}",
        "",
        "## Boundaries",
        f"- forward_smoke_attempted: {str(manifest['forward_smoke_attempted']).lower()}",
        f"- masked_loss_smoke_allowed: {str(manifest['masked_loss_smoke_allowed']).lower()}",
        f"- formal_training_allowed: {str(manifest['formal_training_allowed']).lower()}",
        f"- finetune_allowed: {str(manifest['finetune_allowed']).lower()}",
        f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
        f"- model_saved: {str(manifest['model_saved']).lower()}",
        f"- original_source_files_modified: {str(manifest['original_source_files_modified']).lower()}",
        "",
        "## Conclusion",
        "The in-memory wrapper instantiates a checkpoint-compatible model without editing DiffSBDD source or config files.",
        "The result permits a checkpoint-compatible pretrained load smoke next, not training.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(device: str = "cpu", checkpoint_path: str | Path = CHECKPOINT_PATH, config_preview_path: str | Path = CONFIG_PREVIEW_PATH) -> int:
    result = build_checkpoint_compatible_instantiation_wrapper_v0(
        device=device,
        checkpoint_path=checkpoint_path,
        config_preview_path=config_preview_path,
    )
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["shape_table"], SHAPE_MATCH_TABLE_CSV, SHAPE_TABLE_COLUMNS)
    write_json(result["input_contract"], INPUT_CONTRACT_PREVIEW_JSON)
    write_json(result["manifest"], MANIFEST_JSON)
    write_summary(result["manifest"], SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Build checkpoint-compatible instantiation wrapper evidence v0.")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--checkpoint-path", default=str(CHECKPOINT_PATH))
    parser.add_argument("--config-preview-path", default=str(CONFIG_PREVIEW_PATH))
    args = parser.parse_args()
    return run(args.device, args.checkpoint_path, args.config_preview_path)


if __name__ == "__main__":
    raise SystemExit(main())
