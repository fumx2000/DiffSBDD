#!/usr/bin/env python3
"""Fail-closed checker for the batch-001 mixed-profile preview bridge V1."""

from __future__ import annotations

from dataclasses import fields
import csv
import io
import json
from pathlib import Path
import sys

import torch


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from covalent_ext import covapie_batch001_positive_structural_input_v1 as structural
from covalent_ext import covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1 as bridge
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


CHECK_ERROR = (
    "COVAPIE_BATCH001_TO_EXISTING_MIXED_PROFILE_SUPERVISION_BRIDGE_CHECK_ERROR"
)


def _fail(reason: str) -> None:
    raise ValueError(f"{CHECK_ERROR}:{reason}")


def _same_tensor(left: torch.Tensor, right: torch.Tensor) -> bool:
    if left.dtype != right.dtype or left.shape != right.shape:
        return False
    if left.dtype.is_floating_point:
        return bool(
            torch.equal(torch.isnan(left), torch.isnan(right))
            and torch.equal(torch.nan_to_num(left), torch.nan_to_num(right))
        )
    return bool(torch.equal(left, right))


def check_v1() -> dict[str, object]:
    records_first = structural.build_covapie_batch001_positive_structural_records_v1()
    records_second = structural.build_covapie_batch001_positive_structural_records_v1()
    if records_first != records_second:
        _fail("STRUCTURAL_RECORD_DETERMINISM_FAILED")
    if (
        len(records_first) != 13
        or sum(row.role_profile == structural.STRICT_LINKER_PRESENT_V1 for row in records_first) != 11
        or sum(
            row.role_profile == structural.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
            for row in records_first
        ) != 2
    ):
        _fail("EXACT13_ROLE_PROFILE_COUNTS_INVALID")

    batch_first = bridge.collate_covapie_batch001_preview_population_v1(
        epoch=0, task_schedule_seed=0
    )
    batch_second = bridge.collate_covapie_batch001_preview_population_v1(
        epoch=0, task_schedule_seed=0
    )
    if not bridge.validate_covapie_batch001_preview_batch_v1(
        batch_first, require_exact13_population=True
    ):
        _fail("PREVIEW_BATCH_VALIDATION_FAILED")
    for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
        if not _same_tensor(
            getattr(batch_first.supervision, field.name),
            getattr(batch_second.supervision, field.name),
        ):
            _fail("SUPERVISION_TENSOR_DETERMINISM_FAILED:" + field.name)
    for name, value in batch_first.model_input_batch.items():
        repeated = batch_second.model_input_batch[name]
        if isinstance(value, torch.Tensor):
            if not isinstance(repeated, torch.Tensor) or not _same_tensor(value, repeated):
                _fail("MODEL_INPUT_DETERMINISM_FAILED:" + name)
        elif value != repeated:
            _fail("MODEL_INPUT_DETERMINISM_FAILED:" + name)

    artifacts_first = bridge.build_covapie_batch001_bridge_artifacts_v1()
    artifacts_second = bridge.build_covapie_batch001_bridge_artifacts_v1()
    if artifacts_first != artifacts_second or tuple(artifacts_first) != bridge.OUTPUT_FILENAMES_V1:
        _fail("ARTIFACT_DETERMINISM_OR_EXACT4_FAILED")
    output_root = REPOSITORY_ROOT / bridge.OUTPUT_ROOT_RELATIVE_V1
    if not output_root.is_dir() or {
        path.name for path in output_root.iterdir() if path.is_file()
    } != set(bridge.OUTPUT_FILENAMES_V1):
        _fail("PERSISTED_EXACT4_OUTPUT_SET_INVALID")
    for name, expected in artifacts_first.items():
        if (output_root / name).read_bytes() != expected:
            _fail("PERSISTED_ARTIFACT_MISMATCH:" + name)

    readiness = list(csv.DictReader(io.StringIO(
        artifacts_first[bridge.EVENT_READINESS_V1].decode("utf-8")
    )))
    source_rows = list(csv.DictReader(io.StringIO(
        artifacts_first[bridge.SOURCE_BINDING_INVENTORY_V1].decode("utf-8")
    )))
    evidence = json.loads(artifacts_first[bridge.STRUCTURAL_EVIDENCE_V1])
    manifest = json.loads(artifacts_first[bridge.MANIFEST_V1])
    counts = manifest.get("population_counts", {})
    if (
        len(readiness) != 13
        or {row["canonical_event_id"] for row in readiness}
        != set(structural.BATCH001_POSITIVE_EVENT_IDS_V1)
        or any(row["model_integration_preview_ready"] != "true" for row in readiness)
        or any(row["sample_training_admitted"] != "false" for row in readiness)
        or any(row["minimal_seed_ready"] != "false" for row in readiness)
        or any(row["anchor_distance_ready"] != "true" for row in readiness)
        or any(row["POST_geometry_ready"] != "true" for row in readiness)
        or not source_rows
        or any(row["sha256_verified"] != "true" for row in source_rows)
        or evidence.get("event_count") != 13
        or len(evidence.get("events", ())) != 13
    ):
        _fail("PERSISTED_EVIDENCE_RECONCILIATION_FAILED")
    expected_counts = {
        "positive_event_count": 13,
        "strict_profile_event_count": 11,
        "direct_profile_event_count": 2,
        "structural_input_ready_event_count": 13,
        "feature_projection_ready_event_count": 13,
        "target_condition_ready_event_count": 13,
        "reactive_pair_ready_event_count": 13,
        "role_partition_ready_event_count": 13,
        "minimal_seed_ready_event_count": 0,
        "anchor_distance_ready_event_count": 13,
        "POST_geometry_ready_event_count": 13,
        "pair_prediction_label_ready_event_count": 13,
        "pair_contrastive_label_ready_event_count": 13,
        "model_integration_preview_ready_event_count": 13,
        "in_memory_supervision_tensorized_event_count": 13,
        "split_admitted_event_count": 0,
        "sample_training_admitted_event_count": 0,
        "family_target_ready_event_count": 0,
    }
    if any(counts.get(name) != value for name, value in expected_counts.items()):
        _fail("QUANTITATIVE_ACCEPTANCE_INVALID")
    if (
        manifest.get("architecture_impact", {}).get("supervision_dataclass_reused")
        is not True
        or manifest.get("architecture_impact", {}).get(
            "core_model_architecture_change_required"
        ) is not False
        or manifest.get("safety", {}).get("network_used") is not False
        or manifest.get("safety", {}).get("model_forward_performed") is not False
        or manifest.get("safety", {}).get("loss_performed") is not False
    ):
        _fail("ARCHITECTURE_OR_SAFETY_CONTRACT_INVALID")
    return {
        **expected_counts,
        "pair_candidate_count": len(
            batch_first.supervision.pair_candidate_batch_index
        ),
        "ligand_retained_heavy_total": len(batch_first.model_input_batch["lig_coords"]),
        "pocket_retained_heavy_total": len(batch_first.model_input_batch["pocket_coords"]),
        "artifact_count": len(artifacts_first),
        "source_binding_count": len(source_rows),
        "supervision_dataclass_reused": True,
        "core_model_architecture_change_required": False,
        "masking_py_change_required": False,
        "lightning_modules_change_required": False,
        "network_used": False,
        "GPU_used": False,
        "model_forward_performed": False,
        "loss_performed": False,
        "training_performed": False,
        "ready_for_gpt_review": True,
    }


def main() -> int:
    result = check_v1()
    for name, value in result.items():
        print(f"{name}={str(value).lower() if isinstance(value, bool) else value}")
    print("batch001_existing_mixed_profile_supervision_bridge_implemented=true")
    print("PX5_applicable_task_ids=(0,3,4)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
