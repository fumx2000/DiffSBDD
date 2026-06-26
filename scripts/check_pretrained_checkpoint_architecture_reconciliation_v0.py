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

from covalent_ext.pretrained_checkpoint_architecture_reconciliation import (  # noqa: E402
    CHECKPOINT_PATH,
    MANIFEST_JSON,
    MISMATCH_TABLE_CSV,
    MODEL_CONFIG_PATH,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_pretrained_checkpoint_architecture_reconciliation_v0,
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

MISMATCH_COLUMNS = [
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
        writer.writerows(rows)


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _brief_architecture(architecture: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "atom_encoder_input_dim",
        "atom_encoder_hidden_dim_1",
        "atom_encoder_output_dim",
        "atom_decoder_output_dim",
        "residue_encoder_input_dim",
        "egnn_embedding_input_dim",
        "egnn_embedding_output_dim",
        "egnn_block_count",
        "egnn_hidden_dim_candidates",
        "edge_mlp_input_dim_candidates",
        "node_mlp_input_dim_candidates",
    ]
    return {key: architecture.get(key) for key in keys}


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    sections = result["report_sections"]
    recommended = manifest["recommended_next_step"]
    comparison = sections["comparison"]
    checkpoint = sections["checkpoint"]
    config = sections["config"]
    current = sections["current_model"]
    config_search = sections["config_search"]
    candidate = sections["candidate_smoke"]
    safety = sections["safety"]
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11a_precondition",
            "status": "passed" if manifest["step11a_validated"] else "blocked",
            "evidence": _json_text({"step11a_validated": manifest["step11a_validated"]}),
            "decision": "Step 11A mismatch conclusion is accepted as the precondition.",
            "blocking_reasons": _list_text(sections["step11a"].get("blocking_reasons", [])),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "checkpoint_hyperparameters",
            "status": "passed" if checkpoint["has_hyper_parameters"] else "blocked",
            "evidence": _json_text(
                {
                    "checkpoint_sha256": checkpoint["checkpoint_sha256"],
                    "checkpoint_size_bytes": checkpoint["checkpoint_size_bytes"],
                    "top_level_keys": checkpoint["top_level_keys"],
                    "hyper_parameters_keys": checkpoint["hyper_parameters_keys"],
                    "relevant_fields": checkpoint["hyper_parameters_relevant_fields"],
                }
            ),
            "decision": "Checkpoint hyper_parameters were read without saving or mutating the checkpoint.",
            "blocking_reasons": _list_text(checkpoint["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "current_config",
            "status": "passed" if config["config_present"] else "blocked",
            "evidence": _json_text(
                {
                    "config_path": config["config_path"],
                    "config_text_sha256": config["config_text_sha256"],
                    "config_top_level_keys": config["config_top_level_keys"],
                    "relevant_config_candidates": config["relevant_config_candidates"],
                }
            ),
            "decision": "Current config was read for comparison only.",
            "blocking_reasons": _list_text(config["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "checkpoint_architecture_inference",
            "status": "passed" if checkpoint["state_dict_key_count"] > 0 else "blocked",
            "evidence": _json_text(_brief_architecture(checkpoint["checkpoint_architecture_inferred"])),
            "decision": "Checkpoint architecture was inferred from tensor shapes only.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "current_model_architecture_inference",
            "status": "passed" if current.get("model_instantiated") else "blocked",
            "evidence": _json_text(
                {
                    "model_class": current.get("model_class"),
                    "requested_device": current.get("requested_device"),
                    "resolved_device": current.get("resolved_device"),
                    "state_dict_key_count": current.get("model_state_dict_key_count"),
                    "architecture": _brief_architecture(current.get("current_architecture_inferred", {})),
                }
            ),
            "decision": "Current model was instantiated for state_dict shape inspection only.",
            "blocking_reasons": _list_text(current.get("blocking_reasons", [])),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "shape_mismatch_analysis",
            "status": "passed" if manifest["incompatible_shape_count"] > 0 else "blocked",
            "evidence": _json_text(
                {
                    "matched_key_count": manifest["matched_key_count"],
                    "shape_matched_key_count": manifest["shape_matched_key_count"],
                    "shape_matched_ratio": manifest["shape_matched_ratio"],
                    "incompatible_shape_count": manifest["incompatible_shape_count"],
                    "missing_key_count": manifest["missing_key_count"],
                    "unexpected_key_count": manifest["unexpected_key_count"],
                    "mismatch_category_counts": manifest["mismatch_category_counts"],
                }
            ),
            "decision": "Shape mismatch is broad and architecture/config reconciliation is required.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "repo_config_candidate_search",
            "status": "passed" if config_search["config_candidate_count"] > 0 else "blocked",
            "evidence": _json_text(
                {
                    "config_candidate_count": config_search["config_candidate_count"],
                    "best_config_candidate_path": config_search["best_config_candidate_path"],
                    "best_config_candidate_score": config_search["best_config_candidate_score"],
                    "best_config_candidate_reasons": config_search["best_config_candidate_reasons"],
                }
            ),
            "decision": "Repo configs were searched by metadata only; no config was modified.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "optional_candidate_instantiation",
            "status": "passed",
            "evidence": _json_text(candidate),
            "decision": "Candidate instantiation was skipped because safe config override is not available.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "reconciliation_decision",
            "status": "passed" if manifest["reconciliation_status"] else "blocked",
            "evidence": _json_text(
                {
                    "likely_root_causes": comparison["likely_root_causes"],
                    "confidence_by_root_cause": comparison["confidence_by_root_cause"],
                    "current_config_not_checkpoint_config": comparison["current_config_not_checkpoint_config"],
                    "checkpoint_config_recovery_required": comparison["checkpoint_config_recovery_required"],
                    "reconciliation_status": manifest["reconciliation_status"],
                    "pretrained_masked_loss_smoke_allowed": manifest[
                        "pretrained_masked_loss_smoke_allowed"
                    ],
                }
            ),
            "decision": "Current model must not proceed to pretrained masked loss smoke.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(safety),
            "decision": "Reconciliation stayed read-only with respect to model code and checkpoints.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
    ]


def write_summary(manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_arch = manifest["checkpoint_inferred_architecture"]
    current_arch = manifest["current_inferred_architecture"]
    lines = [
        "# Pretrained Checkpoint Architecture Reconciliation v0 Summary",
        "",
        "Step 11B is architecture/config reconciliation, not training.",
        "Step 11A proved the checkpoint is readable, but it did not prove current-model pretrained integration.",
        "",
        "## Checkpoint Hyperparameters",
        f"- checkpoint_path: `{manifest['checkpoint_path']}`",
        f"- checkpoint_sha256: `{manifest['checkpoint_sha256']}`",
        f"- checkpoint_size_bytes: {manifest['checkpoint_size_bytes']}",
        f"- checkpoint_hyper_parameters_keys: {', '.join(manifest['checkpoint_hyper_parameters_keys'])}",
        "",
        "## Current Config",
        f"- current_config_path: `{manifest['current_config_path']}`",
        f"- current_config_present: {manifest['current_config_present']}",
        f"- current_config_not_checkpoint_config: {manifest['current_config_not_checkpoint_config']}",
        "",
        "## Inferred Architectures",
        f"- checkpoint atom feature dim: {checkpoint_arch.get('atom_encoder_input_dim')}",
        f"- current atom feature dim: {current_arch.get('atom_encoder_input_dim')}",
        f"- checkpoint EGNN hidden candidates: {checkpoint_arch.get('egnn_hidden_dim_candidates')}",
        f"- current EGNN hidden candidates: {current_arch.get('egnn_hidden_dim_candidates')}",
        f"- checkpoint EGNN block count: {checkpoint_arch.get('egnn_block_count')}",
        f"- current EGNN block count: {current_arch.get('egnn_block_count')}",
        "",
        "## Mismatch Summary",
        f"- matched_key_count: {manifest['matched_key_count']}",
        f"- shape_matched_key_count: {manifest['shape_matched_key_count']}",
        f"- shape_matched_ratio: {manifest['shape_matched_ratio']}",
        f"- incompatible_shape_count: {manifest['incompatible_shape_count']}",
        f"- mismatch_category_counts: {json.dumps(manifest['mismatch_category_counts'], sort_keys=True)}",
        f"- likely_root_causes: {', '.join(manifest['likely_root_causes'])}",
        f"- confidence_by_root_cause: {json.dumps(manifest['confidence_by_root_cause'], sort_keys=True)}",
        "",
        "## Config Candidate Search",
        f"- best_config_candidate_path: `{manifest['best_config_candidate_path']}`",
        f"- best_config_candidate_score: {manifest['best_config_candidate_score']}",
        f"- candidate_instantiation_attempted: {manifest['candidate_instantiation_attempted']}",
        "",
        "## Decision",
        f"- reconciliation_status: {manifest['reconciliation_status']}",
        f"- pretrained_masked_loss_smoke_allowed: {manifest['pretrained_masked_loss_smoke_allowed']}",
        f"- formal_training_allowed: {manifest['formal_training_allowed']}",
        f"- finetune_allowed: {manifest['finetune_allowed']}",
        f"- quality_claim_allowed: {manifest['quality_claim_allowed']}",
        f"- recommended_next_step: {manifest['recommended_next_step']}",
        "",
        "Formal training, fine-tuning, and pretrained masked loss smoke remain forbidden until a checkpoint-compatible model is proven.",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reconcile pretrained checkpoint and current DiffSBDD config.")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--checkpoint-path", default=str(CHECKPOINT_PATH))
    parser.add_argument("--config-path", default=str(MODEL_CONFIG_PATH))
    return parser.parse_args()


def run(
    device: str = "cpu",
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_path: str | Path = MODEL_CONFIG_PATH,
) -> int:
    result = build_pretrained_checkpoint_architecture_reconciliation_v0(
        device=device,
        checkpoint_path=checkpoint_path,
        config_path=config_path,
    )
    manifest = result["manifest"]
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["mismatch_table"], MISMATCH_TABLE_CSV, MISMATCH_COLUMNS)
    write_json(manifest, MANIFEST_JSON)
    write_summary(manifest, SUMMARY_MD)
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    args = parse_args()
    code = run(device=args.device, checkpoint_path=args.checkpoint_path, config_path=args.config_path)
    print(
        "pretrained_checkpoint_architecture_reconciliation_v0_passed"
        if code == 0
        else "pretrained_checkpoint_architecture_reconciliation_v0_blocked"
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
