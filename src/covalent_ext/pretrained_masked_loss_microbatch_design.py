from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "pretrained_masked_loss_microbatch_design_v0"
PREVIOUS_STAGE = "pretrained_masked_loss_smoke_v0"
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
STEP11F_MANIFEST_JSON = Path(
    "data/derived/covalent_small/pretrained_masked_loss_smoke_v0/pretrained_masked_loss_smoke_manifest.json"
)
STEP11F_LOSS_TABLE_CSV = Path(
    "data/derived/covalent_small/pretrained_masked_loss_smoke_v0/pretrained_masked_loss_smoke_loss_table.csv"
)
STEP11F_SUMMARY_MD = Path("docs/pretrained_masked_loss_smoke_v0_summary.md")
OUTPUT_ROOT = Path("data/derived/covalent_small/pretrained_masked_loss_microbatch_design_v0")
REPORT_CSV = OUTPUT_ROOT / "pretrained_masked_loss_microbatch_design_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "pretrained_masked_loss_microbatch_design_manifest.json"
PROTOCOL_JSON = OUTPUT_ROOT / "pretrained_masked_loss_microbatch_protocol.json"
SUMMARY_MD = Path("docs/pretrained_masked_loss_microbatch_design_v0_summary.md")
MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
RECOMMENDED_MASK_SEQUENCE = [
    "A_warhead_only",
    "C_scaffold_linker_warhead",
    "B_linker_warhead",
    "B2_scaffold_warhead",
]
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _text_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


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


def validate_step11f_outputs_v0() -> bool:
    if not STEP11F_MANIFEST_JSON.is_file() or not STEP11F_LOSS_TABLE_CSV.is_file() or not STEP11F_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11F outputs are missing")
    manifest = _load_json(STEP11F_MANIFEST_JSON)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "checkpoint_compatible_pretrained_load_smoke_v0",
        "step11e_validated": True,
        "pretrained_weights_loaded": True,
        "pretrained_base_integration_proven": True,
        "model_instantiated": True,
        "strict_load_success": True,
        "all_mask_levels_passed": True,
        "finite_loss_level_count": 4,
        "failed_mask_levels": [],
        "synthetic_shape_smoke_only": True,
        "feature_semantics_known": False,
        "synthetic_mask_loss_adapter_used": True,
        "pretrained_masked_loss_smoke_passed": True,
        "pretrained_model_mask_hook_integration_proven": True,
        "masked_loss_smoke_status": "pretrained_masked_loss_smoke_passed",
        "microbatch_dry_run_allowed": True,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "optimizer_allowed": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "original_source_files_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "pretrained_masked_loss_microbatch_dry_run_design",
    }
    for key, expected_value in expected.items():
        _expect(manifest.get(key) == expected_value, f"step11f_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(set(manifest.get("mask_levels_attempted", [])) == set(MASK_LEVELS), "step11f_attempted_masks_invalid", blockers)
    _expect(set(manifest.get("mask_levels_passed", [])) == set(MASK_LEVELS), "step11f_passed_masks_invalid", blockers)

    rows = _rows_from_csv(STEP11F_LOSS_TABLE_CSV)
    _expect(len(rows) == 4, f"step11f_loss_table_row_count_invalid:{len(rows)}", blockers)
    _expect({row.get("mask_level") for row in rows} == set(MASK_LEVELS), "step11f_loss_table_masks_invalid", blockers)
    for row in rows:
        mask_level = row.get("mask_level", "")
        _expect(row.get("status") == "passed", f"step11f_loss_table_status_invalid:{mask_level}:{row.get('status')!r}", blockers)
        _expect(_text_bool(row.get("finite_loss")), f"step11f_loss_table_finite_invalid:{mask_level}", blockers)
        _expect(bool(row.get("selected_primary_loss_key")), f"step11f_loss_key_missing:{mask_level}", blockers)
        try:
            value = float(row.get("selected_primary_loss_value", "nan"))
        except ValueError:
            value = math.nan
        _expect(math.isfinite(value), f"step11f_loss_value_not_finite:{mask_level}:{row.get('selected_primary_loss_value')!r}", blockers)
    summary = STEP11F_SUMMARY_MD.read_text(encoding="utf-8")
    _expect("not training" in summary, "step11f_summary_training_boundary_missing", blockers)
    _expect(
        "pretrained_masked_loss_microbatch_dry_run_design" in summary,
        "step11f_summary_recommended_next_step_missing",
        blockers,
    )
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def load_step11f_loss_evidence_v0() -> dict[str, Any]:
    rows = _rows_from_csv(STEP11F_LOSS_TABLE_CSV)
    loss_values_by_level: dict[str, float] = {}
    mask_levels: list[str] = []
    for row in rows:
        mask_level = row["mask_level"]
        mask_levels.append(mask_level)
        loss_values_by_level[mask_level] = float(row["selected_primary_loss_value"])
    values = list(loss_values_by_level.values())
    max_loss = max(values) if values else 0.0
    min_loss = min(values) if values else 0.0
    return {
        "loss_table_present": STEP11F_LOSS_TABLE_CSV.is_file(),
        "loss_table_row_count": len(rows),
        "mask_levels": mask_levels,
        "loss_values_by_level": loss_values_by_level,
        "min_loss": min_loss,
        "max_loss": max_loss,
        "finite_loss_count": sum(1 for value in values if math.isfinite(value)),
        "all_loss_values_positive": all(value > 0 for value in values),
        "loss_value_scale_warning": "monitor_gradient_norm_for_large_C_level_loss" if max_loss > 100.0 else "",
    }


def _existing_paths(paths: list[Path]) -> list[str]:
    return [str(path) for path in paths if path.exists()]


def inspect_microbatch_data_sources_v0() -> dict[str, Any]:
    materialized_root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    real_package_root = Path("data/derived/covalent_small/real_training_dataset_package_review_only")
    packaged_root = Path("data/derived/covalent_small/packaging_real_review_only")
    fixture_root = Path("tests/fixtures")
    example_root = Path("example")
    real_candidates = _existing_paths(
        [
            materialized_root / "sample_index.csv",
            materialized_root / "manifest.json",
            real_package_root / "real_training_dataset_manifest.json",
            real_package_root / "real_training_dataset_sample_index.csv",
            real_package_root / "real_training_dataset_file_index.csv",
            packaged_root,
        ]
    )
    npz_candidates = sorted(str(path) for path in (materialized_root / "samples").glob("*.npz"))
    fixture_candidates = []
    if fixture_root.exists():
        fixture_candidates.extend(str(path) for path in sorted(fixture_root.rglob("*")) if path.is_file())
    if example_root.exists():
        fixture_candidates.extend(str(path) for path in sorted(example_root.rglob("*")) if path.is_file())
    schema_sources = _existing_paths([Path("src/covalent_ext/schema.py"), Path("src/covalent_ext/masking.py")])
    real_sample_available = bool(real_candidates and npz_candidates)
    checkpoint_compatible_real_sample_available = False
    synthetic_contract_available = True
    if checkpoint_compatible_real_sample_available:
        recommendation = "real_covalent_small_fixture"
    elif synthetic_contract_available:
        recommendation = "synthetic_10d_shape_contract"
    else:
        recommendation = "schema_gap_debug"
    return {
        "real_covalent_sample_candidates": real_candidates + npz_candidates,
        "fixture_candidates": fixture_candidates,
        "schema_sources": schema_sources,
        "real_covalent_sample_available": real_sample_available,
        "real_covalent_sample_checkpoint_compatible": checkpoint_compatible_real_sample_available,
        "synthetic_contract_available": synthetic_contract_available,
        "synthetic_10d_contract_available": synthetic_contract_available,
        "recommended_microbatch_input_source": recommendation,
        "input_source_rationale": (
            "Real covalent artifacts exist, but the checkpoint-compatible pretrained model currently uses the "
            "Step 11F synthetic 10D shape-only contract; real covalent feature semantics are not reconciled yet."
        ),
    }


def build_microbatch_dry_run_protocol_v0(
    step11f_evidence: dict[str, Any],
    data_source_evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "proposed_next_stage": "pretrained_masked_loss_microbatch_dry_run_v0",
        "allowed_device_default": "cpu",
        "optional_device": "cuda:0 only if explicitly requested later",
        "allowed_mask_levels": MASK_LEVELS,
        "recommended_mask_level_sequence": RECOMMENDED_MASK_SEQUENCE,
        "mask_levels_for_backward_dry_run": MASK_LEVELS,
        "microbatch_backward_policy": "isolated_backward_per_mask_level",
        "fresh_model_per_mask_level": True,
        "strict_load_fresh_model_per_mask_level": True,
        "microbatch_input_source": data_source_evidence["recommended_microbatch_input_source"],
        "loss_source": "Step 11F masked_loss_total_dry scalar per mask level",
        "backward_allowed_next_step": True,
        "reverse_pass_invocations_per_mask_level": 1,
        "optimizer_allowed_next_step": False,
        "optimizer_step_allowed_next_step": False,
        "trainer_fit_allowed_next_step": False,
        "training_step_allowed_next_step": False,
        "checkpoint_save_allowed_next_step": False,
        "model_save_allowed_next_step": False,
        "formal_training_allowed_next_step": False,
        "finetune_allowed_next_step": False,
        "zero_grad_after_measurement": True,
        "delete_model_after_each_mask_level": True,
        "required_gradient_stats": [
            "parameter_count",
            "parameters_with_grad_count",
            "parameters_with_finite_grad_count",
            "grad_nan_count",
            "grad_inf_count",
            "total_grad_norm",
            "max_abs_grad",
            "zero_grad_parameter_count",
            "selected_loss_value",
        ],
        "pass_conditions": [
            "loss finite",
            "loss requires grad",
            "reverse pass invoked exactly once",
            "no optimizer object",
            "no optimizer step",
            "at least one parameter has finite nonzero grad",
            "grad_nan_count equals 0",
            "grad_inf_count equals 0",
        ],
        "non_claims": [
            "loss decrease is not required",
            "gradient coverage of every parameter is not required",
            "training quality is not proven",
            "generation quality is not proven",
        ],
        "step11f_loss_scale_reference": step11f_evidence.get("loss_values_by_level", {}),
    }


def build_microbatch_risk_register_v0(
    step11f_evidence: dict[str, Any],
    data_source_evidence: dict[str, Any],
    protocol: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "risk_id": "R1_synthetic_10d_semantics",
            "description": "Synthetic 10D contract is not the same as real covalent data feature semantics.",
            "severity": "high",
            "mitigation": "Use Step 11H only for gradient plumbing; keep real feature mapping as a later gate.",
            "blocks_11H": False,
        },
        {
            "risk_id": "R2_reverse_pass_surface",
            "description": "The microbatch dry run may expose detached loss or in-place operation issues.",
            "severity": "medium",
            "mitigation": "Require loss.requires_grad, finite gradients, and isolated fresh model per mask level.",
            "blocks_11H": False,
        },
        {
            "risk_id": "R3_large_C_level_loss_scale",
            "description": "C mask loss scale is larger than other mask levels and may amplify gradients.",
            "severity": "medium",
            "mitigation": "Log total grad norm and max absolute grad for every mask level.",
            "blocks_11H": False,
        },
        {
            "risk_id": "R4_no_parameter_update_claim",
            "description": "No optimizer step means 11H cannot prove parameter update behavior.",
            "severity": "low",
            "mitigation": "Keep 11H as backward-only; require a later explicit optimizer smoke gate.",
            "blocks_11H": False,
        },
        {
            "risk_id": "R5_fresh_model_runtime",
            "description": "Fresh model per mask level is slower but reduces gradient contamination.",
            "severity": "low",
            "mitigation": "Accept slower runtime for the first pretrained microbatch dry run.",
            "blocks_11H": False,
        },
        {
            "risk_id": "R6_real_covalent_loader_gap",
            "description": "Real covalent feature mapping and loader integration remain unresolved for checkpoint-compatible 10D inputs.",
            "severity": "high",
            "mitigation": "Do not claim real-data training readiness until a real feature mapping gate passes.",
            "blocks_11H": False,
        },
    ]


def build_microbatch_design_decision_v0(
    step11f_evidence: dict[str, Any],
    data_source_evidence: dict[str, Any],
    protocol: dict[str, Any],
    step11f_validated: bool = True,
) -> dict[str, Any]:
    protocol_complete = bool(
        protocol.get("microbatch_backward_policy")
        and set(protocol.get("mask_levels_for_backward_dry_run", [])) == set(MASK_LEVELS)
        and protocol.get("fresh_model_per_mask_level") is True
    )
    source_available = bool(data_source_evidence.get("synthetic_10d_contract_available"))
    if step11f_validated and protocol_complete and source_available:
        design_status = "microbatch_dry_run_design_ready"
        allowed = True
        next_step = "pretrained_masked_loss_microbatch_backward_dry_run"
    elif step11f_validated:
        design_status = "microbatch_input_source_blocked"
        allowed = False
        next_step = "microbatch_input_contract_debug"
    else:
        design_status = "step11f_precondition_failed"
        allowed = False
        next_step = "pretrained_masked_loss_smoke_debug"
    return {
        "design_status": design_status,
        "microbatch_backward_dry_run_allowed": allowed,
        "recommended_next_step": next_step,
        "this_design_executes_backward": False,
        "this_design_creates_optimizer": False,
        "this_design_saves_model": False,
        "this_design_saves_checkpoint": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "optimizer_step_allowed": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
    }


def build_pretrained_masked_loss_microbatch_design_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step11f_validated = validate_step11f_outputs_v0()
    except Exception as exc:
        step11f_validated = False
        blockers.append(f"step11f_validation_failed:{type(exc).__name__}:{exc}")
    loss_evidence = load_step11f_loss_evidence_v0() if STEP11F_LOSS_TABLE_CSV.is_file() else {}
    data_sources = inspect_microbatch_data_sources_v0()
    protocol = build_microbatch_dry_run_protocol_v0(loss_evidence, data_sources)
    risk_register = build_microbatch_risk_register_v0(loss_evidence, data_sources, protocol)
    decision = build_microbatch_design_decision_v0(loss_evidence, data_sources, protocol, step11f_validated)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_source_files_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    all_checks_passed = bool(
        step11f_validated
        and loss_evidence.get("finite_loss_count") == 4
        and decision["microbatch_backward_dry_run_allowed"]
        and not source_modified
        and not forbidden_artifacts
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11f_validated": step11f_validated,
        "step11f_all_mask_levels_passed": step11f_validated,
        "step11f_finite_loss_level_count": loss_evidence.get("finite_loss_count", 0),
        "recommended_microbatch_input_source": data_sources["recommended_microbatch_input_source"],
        "real_covalent_sample_available": data_sources["real_covalent_sample_available"],
        "synthetic_10d_contract_available": data_sources["synthetic_10d_contract_available"],
        "protocol_written": True,
        "protocol_path": str(PROTOCOL_JSON),
        "proposed_next_stage": protocol["proposed_next_stage"],
        "microbatch_backward_policy": protocol["microbatch_backward_policy"],
        "mask_levels_for_backward_dry_run": protocol["mask_levels_for_backward_dry_run"],
        "fresh_model_per_mask_level": protocol["fresh_model_per_mask_level"],
        "backward_allowed_next_step": protocol["backward_allowed_next_step"],
        "optimizer_step_allowed_next_step": protocol["optimizer_step_allowed_next_step"],
        "optimizer_allowed_next_step": protocol["optimizer_allowed_next_step"],
        "checkpoint_save_allowed_next_step": protocol["checkpoint_save_allowed_next_step"],
        "model_save_allowed_next_step": protocol["model_save_allowed_next_step"],
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
        "blocking_reasons": blockers,
    }
    protocol_document = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "loss_evidence": loss_evidence,
        "data_source_evidence": data_sources,
        "protocol": protocol,
        "risk_register": risk_register,
        "decision": decision,
    }
    return {
        "manifest": manifest,
        "protocol_document": protocol_document,
        "report_sections": {
            "step11f_precondition": {"step11f_validated": step11f_validated},
            "step11f_loss_evidence": loss_evidence,
            "microbatch_data_source_inspection": data_sources,
            "microbatch_protocol": protocol,
            "risk_register": risk_register,
            "design_decision": decision,
            "safety_boundary": {
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
