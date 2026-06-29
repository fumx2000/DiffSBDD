from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader

from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0, validate_adapted_covalent_batch_v0
from covalent_ext.diffsbdd_input_adapter import (
    build_diffsbdd_like_input_from_covalent_v0,
    validate_diffsbdd_like_input_v0,
)
from covalent_ext.model_input_adapter import build_covalent_model_input_v0, validate_covalent_model_input_v0
from covalent_ext.npz_dataset import CovalentNPZDataset, NPZ_REQUIRED_KEYS, covalent_npz_collate_fn


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_feature_mapping_loader_gate_v0"
PREVIOUS_STAGE = "b3_single_optimizer_step_smoke_v0"
STEP11R_MANIFEST_JSON = Path(
    "data/derived/covalent_small/b3_single_optimizer_step_smoke_v0/b3_single_optimizer_step_smoke_manifest.json"
)
STEP11R_SUMMARY_MD = Path("docs/b3_single_optimizer_step_smoke_v0_summary.md")
OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_feature_mapping_loader_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_feature_mapping_loader_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_feature_mapping_loader_gate_manifest.json"
SAMPLE_TABLE_CSV = OUTPUT_ROOT / "real_covalent_feature_mapping_loader_gate_sample_table.csv"
SUMMARY_MD = Path("docs/real_covalent_feature_mapping_loader_gate_v0_summary.md")

CANONICAL_MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "B3_scaffold_only",
    "C_scaffold_linker_warhead",
]

KNOWN_REAL_COVALENT_ROOTS = [
    Path("data/derived/covalent_small/training_tensor_materialized_v0"),
    Path("data/derived/covalent_small/training_tensor_npz_dataloader_v0"),
    Path("data/derived/covalent_small/training_tensor_model_input_mapping_v0"),
    Path("data/derived/covalent_small/dataset_index_build_v0"),
    Path("data/derived/covalent_small/actual_dataset_index_build_v0"),
    Path("data/derived/covalent_small/real_training_dataset_packaging_v0"),
    Path("data/derived/covalent_small/read_only_training_dataset_loader_dry_run_v0"),
    Path("data/derived/covalent_small/real_packaging_execution_v0"),
]

CHECKPOINT_COMPATIBLE_LIGAND_FEATURE_DIM = 10
CHECKPOINT_COMPATIBLE_ATOM_NUMBERS = {
    5: "B",
    6: "C",
    7: "N",
    8: "O",
    9: "F",
    15: "P",
    16: "S",
    17: "Cl",
    35: "Br",
    53: "I",
}
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


def _finite_positive(value: Any) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(numeric) and numeric > 0.0


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


def validate_step11r_outputs_v0() -> bool:
    if not STEP11R_MANIFEST_JSON.is_file() or not STEP11R_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11R outputs are missing")
    manifest = _load_json(STEP11R_MANIFEST_JSON)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "b3_backward_smoke_v0",
        "step11q_validated": True,
        "mask_level": "B3_scaffold_only",
        "input_source": "synthetic_10d_shape_contract",
        "strict_load_success": True,
        "pretrained_weights_loaded": True,
        "pretrained_base_integration_proven": True,
        "model_forward_called": True,
        "loss_computed": True,
        "loss_requires_grad": True,
        "loss_finite": True,
        "optimizer_type": "AdamW",
        "learning_rate": 1e-06,
        "weight_decay": 0.0,
        "optimizer_created": True,
        "backward_called": True,
        "backward_call_count": 1,
        "backward_success": True,
        "optimizer_step_called": True,
        "optimizer_step_call_count": 1,
        "finite_nonzero_grad_exists": True,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "parameter_update_finite": True,
        "parameter_update_nonzero": True,
        "b3_target_atom_count": 3,
        "b3_context_atom_count": 4,
        "b3_reactive_atom_in_context": True,
        "b3_reactive_atom_in_target": False,
        "b3_single_optimizer_step_smoke_passed": True,
        "b3_parameter_update_contract_proven": True,
        "b3_finite_nonzero_parameter_update_proven": True,
        "b3_tiny_loop_optional": True,
        "real_covalent_feature_mapping_loader_gate_allowed": True,
        "recommended_next_step": "real_covalent_feature_mapping_loader_gate",
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
    }
    for key, value in expected.items():
        _expect(manifest.get(key) == value, f"step11r_{key}_invalid:{manifest.get(key)!r}", blockers)
    for key in [
        "sampled_parameter_count",
        "sampled_parameter_delta_l2",
        "sampled_parameter_delta_max_abs",
        "updated_parameter_tensors_count",
    ]:
        _expect(_finite_positive(manifest.get(key)), f"step11r_{key}_not_positive_finite", blockers)
    summary = STEP11R_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "B3 Single Optimizer Step Smoke",
        "not training",
        "B3 tiny loop is optional",
        "recommended_next_step: real_covalent_feature_mapping_loader_gate",
    ]:
        _expect(snippet in summary, f"step11r_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def discover_existing_real_covalent_artifacts_v0() -> dict[str, Any]:
    base = Path("data/derived/covalent_small")
    known_existing_roots = [path for path in KNOWN_REAL_COVALENT_ROOTS if path.exists()]
    output_root_resolved = (REPO_ROOT / OUTPUT_ROOT).resolve()

    def outside_current_output(path: Path) -> bool:
        try:
            path.resolve().relative_to(output_root_resolved)
            return False
        except ValueError:
            return True

    manifest_paths = (
        sorted(path for path in base.rglob("*manifest*.json") if path.is_file() and outside_current_output(path))
        if base.exists()
        else []
    )
    tensor_json_paths = (
        sorted(path for path in base.rglob("*training*tensor*.json") if path.is_file() and outside_current_output(path))
        if base.exists()
        else []
    )
    npz_paths = sorted(path for path in base.rglob("*.npz") if path.is_file() and outside_current_output(path)) if base.exists() else []
    loader_json_paths = (
        sorted(path for path in base.rglob("*loader*.json") if path.is_file() and outside_current_output(path))
        if base.exists()
        else []
    )
    model_input_json_paths = (
        sorted(path for path in base.rglob("*model_input*.json") if path.is_file() and outside_current_output(path))
        if base.exists()
        else []
    )
    candidates: list[dict[str, Any]] = []

    materialized_root = Path("data/derived/covalent_small/training_tensor_materialized_v0")
    materialized_manifest = materialized_root / "manifest.json"
    materialized_sample_index = materialized_root / "sample_index.csv"
    materialized_samples = sorted((materialized_root / "samples").glob("*.npz")) if (materialized_root / "samples").exists() else []
    if materialized_manifest.is_file() and materialized_sample_index.is_file() and materialized_samples:
        manifest = _load_json(materialized_manifest)
        synthetic_only = "synthetic" in json.dumps(manifest, sort_keys=True).lower()
        real_covalent = (
            manifest.get("npz_count") == len(materialized_samples)
            and "covalent_small" in str(manifest.get("dataset_name", ""))
            and "actual_minimal_tensor_like_materialization" in str(manifest.get("materialization_stage", ""))
            and not synthetic_only
        )
        candidates.append(
            {
                "root": str(materialized_root),
                "manifest_json": str(materialized_manifest),
                "sample_index_csv": str(materialized_sample_index),
                "sample_npz_count": len(materialized_samples),
                "artifact_kind": "training_tensor_materialized_npz_v0",
                "is_real_covalent": bool(real_covalent),
                "is_synthetic_only": bool(synthetic_only),
                "selection_priority": 0 if real_covalent else 100,
            }
        )

    candidates.sort(key=lambda item: (int(item["selection_priority"]), item["root"]))
    selected = next((candidate for candidate in candidates if candidate["is_real_covalent"] and not candidate["is_synthetic_only"]), None)
    return {
        "known_existing_roots": [str(path) for path in known_existing_roots],
        "discovered_artifact_count": len(candidates),
        "discovered_manifest_count": len(manifest_paths),
        "discovered_npz_count": len(npz_paths),
        "discovered_training_tensor_json_count": len(tensor_json_paths),
        "discovered_loader_json_count": len(loader_json_paths),
        "discovered_model_input_json_count": len(model_input_json_paths),
        "candidates": candidates,
        "selected": selected,
        "selected_real_data_root": selected["root"] if selected else "",
        "selected_loader_or_tensor_artifact": selected["sample_index_csv"] if selected else "",
        "selected_artifact_is_real_covalent": bool(selected and selected["is_real_covalent"]),
        "selected_artifact_is_synthetic_only": bool(selected["is_synthetic_only"]) if selected else False,
        "artifact_discovery_status": "passed" if selected else "blocked",
        "blocking_reasons": [] if selected else ["real_covalent_artifact_not_found"],
    }


def _bool_array(data: np.ndarray) -> np.ndarray:
    return np.asarray(data, dtype=bool)


def _indices(mask: np.ndarray) -> list[int]:
    return [int(value) for value in np.where(mask)[0].tolist()]


def _ligand_feature_10d_available(atomic_numbers: np.ndarray) -> bool:
    return all(int(value) in CHECKPOINT_COMPATIBLE_ATOM_NUMBERS for value in atomic_numbers.tolist())


def audit_real_covalent_sample_fields_v0(selected_artifact: dict[str, Any] | None, max_samples: int = 3) -> list[dict[str, Any]]:
    if not selected_artifact:
        return []
    rows = _read_csv(selected_artifact["sample_index_csv"])[:max_samples]
    sample_rows: list[dict[str, Any]] = []
    for row in rows:
        blockers: list[str] = []
        npz_path = Path(row["npz_path"])
        sample_id = row.get("sample_id", "")
        audit: dict[str, Any] = {
            "sample_id": sample_id,
            "npz_path": str(npz_path),
            "selected_artifact_is_real_covalent": True,
            "selected_artifact_is_synthetic_only": False,
            "status": "blocked",
            "blocking_reasons": "",
        }
        if not sample_id:
            blockers.append("sample_id_missing")
        if not npz_path.is_file():
            blockers.append("npz_missing")
            audit["blocking_reasons"] = ";".join(blockers)
            sample_rows.append(audit)
            continue
        with np.load(npz_path, allow_pickle=False) as data:
            missing = sorted(set(NPZ_REQUIRED_KEYS) - set(data.files))
            if missing:
                blockers.append("missing_npz_keys:" + ",".join(missing))
            ligand_coords = np.asarray(data["ligand_atom_coords"], dtype=np.float32)
            protein_coords = np.asarray(data["protein_atom_coords"], dtype=np.float32)
            ligand_atomic = np.asarray(data["ligand_atomic_numbers"])
            protein_atomic = np.asarray(data["protein_atomic_numbers"])
            scaffold = _bool_array(data["scaffold_atom_mask"])
            linker = _bool_array(data["linker_atom_mask"])
            warhead = _bool_array(data["warhead_atom_mask"])
            reactive = int(np.asarray(data["ligand_reactive_atom_index"]).item())
            ligand_count = int(ligand_coords.shape[0]) if ligand_coords.ndim == 2 else 0
            protein_count = int(protein_coords.shape[0]) if protein_coords.ndim == 2 else 0
            assigned = scaffold | linker | warhead
            mask_lengths_valid = all(mask.shape == (ligand_count,) for mask in [scaffold, linker, warhead])
            masks_disjoint = not bool((scaffold & linker).any() or (scaffold & warhead).any() or (linker & warhead).any())
            masks_cover_ligand = bool(mask_lengths_valid and int(assigned.sum()) == ligand_count)
            ligand_feature_available = ligand_atomic.shape == (ligand_count,)
            ligand_feature_dim = CHECKPOINT_COMPATIBLE_LIGAND_FEATURE_DIM if _ligand_feature_10d_available(ligand_atomic) else 0
            if ligand_count <= 0:
                blockers.append("ligand_atom_count_not_positive")
            if protein_count <= 0:
                blockers.append("protein_atom_count_not_positive")
            if ligand_coords.shape != (ligand_count, 3):
                blockers.append("ligand_coords_shape_invalid")
            if protein_coords.shape != (protein_count, 3):
                blockers.append("protein_coords_shape_invalid")
            if not ligand_feature_available:
                blockers.append("ligand_feature_missing")
            if ligand_feature_dim != CHECKPOINT_COMPATIBLE_LIGAND_FEATURE_DIM:
                blockers.append("ligand_feature_dim_not_checkpoint_compatible_10d")
            if not mask_lengths_valid:
                blockers.append("region_mask_length_invalid")
            if not masks_disjoint:
                blockers.append("region_masks_overlap")
            if not masks_cover_ligand:
                blockers.append("region_masks_do_not_cover_ligand")
            if int(scaffold.sum()) == 0:
                blockers.append("empty_scaffold_region")
            if int(linker.sum()) == 0:
                blockers.append("empty_linker_region")
            if int(warhead.sum()) == 0:
                blockers.append("empty_warhead_region")
            if reactive < 0 or reactive >= ligand_count:
                blockers.append("reactive_atom_out_of_range")
            if not bool(np.isfinite(ligand_coords).all() and np.isfinite(protein_coords).all()):
                blockers.append("coords_not_finite")
            if not bool(np.isfinite(ligand_atomic.astype(np.float32)).all() and np.isfinite(protein_atomic.astype(np.float32)).all()):
                blockers.append("features_not_finite")
            audit.update(
                {
                    "ligand_atom_count": ligand_count,
                    "protein_atom_count": protein_count,
                    "ligand_coords_shape": list(ligand_coords.shape),
                    "protein_coords_shape": list(protein_coords.shape),
                    "ligand_feature_source": "ligand_atomic_numbers_read_only",
                    "ligand_feature_dim": ligand_feature_dim,
                    "scaffold_atom_count": int(scaffold.sum()),
                    "linker_atom_count": int(linker.sum()),
                    "warhead_atom_count": int(warhead.sum()),
                    "masks_disjoint": masks_disjoint,
                    "masks_cover_assigned_ligand_atoms": masks_cover_ligand,
                    "ligand_reactive_atom_index": reactive,
                    "reactive_atom_in_range": reactive >= 0 and reactive < ligand_count,
                    "reactive_atom_in_warhead": bool(reactive >= 0 and reactive < ligand_count and warhead[reactive]),
                    "coords_finite": bool(np.isfinite(ligand_coords).all() and np.isfinite(protein_coords).all()),
                    "features_finite": bool(np.isfinite(ligand_atomic.astype(np.float32)).all() and np.isfinite(protein_atomic.astype(np.float32)).all()),
                }
            )
        audit["blocking_reasons"] = ";".join(sorted(set(blockers)))
        audit["status"] = "passed" if not blockers else "blocked"
        sample_rows.append(audit)
    return sample_rows


def derive_and_validate_five_level_masks_for_real_sample_v0(sample_row: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    with np.load(sample_row["npz_path"], allow_pickle=False) as data:
        scaffold = _bool_array(data["scaffold_atom_mask"])
        linker = _bool_array(data["linker_atom_mask"])
        warhead = _bool_array(data["warhead_atom_mask"])
        reactive = int(np.asarray(data["ligand_reactive_atom_index"]).item())
    assigned = scaffold | linker | warhead
    targets = {
        "A_warhead_only": warhead,
        "B_linker_warhead": linker | warhead,
        "B2_scaffold_warhead": scaffold | warhead,
        "B3_scaffold_only": scaffold,
        "C_scaffold_linker_warhead": assigned,
    }
    contexts = {
        "A_warhead_only": scaffold | linker,
        "B_linker_warhead": scaffold,
        "B2_scaffold_warhead": linker,
        "B3_scaffold_only": linker | warhead,
        "C_scaffold_linker_warhead": np.zeros_like(assigned, dtype=bool),
    }
    per_level: dict[str, Any] = {}
    for level in CANONICAL_MASK_LEVELS:
        target = targets[level]
        context = contexts[level]
        level_ok = True
        if bool((target & context).any()):
            blockers.append(f"{level}_target_context_overlap")
            level_ok = False
        if not bool(np.array_equal(target | context, assigned)):
            blockers.append(f"{level}_target_context_do_not_cover_assigned")
            level_ok = False
        if int(target.sum()) == 0:
            blockers.append(f"{level}_empty_target")
            level_ok = False
        per_level[level] = {
            "target_atom_count": int(target.sum()),
            "context_atom_count": int(context.sum()),
            "target_context_disjoint": not bool((target & context).any()),
            "target_context_cover_assigned": bool(np.array_equal(target | context, assigned)),
            "status": "passed" if level_ok else "blocked",
        }
    b2_target = targets["B2_scaffold_warhead"]
    b2_context = contexts["B2_scaffold_warhead"]
    b3_target = targets["B3_scaffold_only"]
    b3_context = contexts["B3_scaffold_only"]
    b3_reactive_in_context = bool(reactive >= 0 and reactive < b3_context.shape[0] and b3_context[reactive])
    b3_reactive_in_target = bool(reactive >= 0 and reactive < b3_target.shape[0] and b3_target[reactive])
    checks = {
        "all_five_level_masks_available": set(per_level) == set(CANONICAL_MASK_LEVELS),
        "real_b3_target_is_scaffold": bool(np.array_equal(b3_target, scaffold)),
        "real_b3_context_is_linker_warhead": bool(np.array_equal(b3_context, linker | warhead)),
        "real_b3_reactive_atom_in_context": b3_reactive_in_context,
        "real_b3_reactive_atom_in_target": b3_reactive_in_target,
        "real_b2_target_includes_scaffold": bool(np.all(b2_target[scaffold])),
        "real_b2_target_includes_warhead": bool(np.all(b2_target[warhead])),
        "real_b2_context_is_linker": bool(np.array_equal(b2_context, linker)),
        "real_b2_b3_target_masks_not_identical": not bool(np.array_equal(b2_target, b3_target)),
        "real_b2_b3_context_masks_not_identical": not bool(np.array_equal(b2_context, b3_context)),
    }
    if not checks["real_b3_target_is_scaffold"]:
        blockers.append("b3_target_not_scaffold")
    if not checks["real_b3_context_is_linker_warhead"]:
        blockers.append("b3_context_not_linker_warhead")
    if not checks["real_b3_reactive_atom_in_context"]:
        blockers.append("b3_reactive_atom_not_in_context")
    if checks["real_b3_reactive_atom_in_target"]:
        blockers.append("b3_reactive_atom_in_target")
    if not checks["real_b2_b3_target_masks_not_identical"] or not checks["real_b2_b3_context_masks_not_identical"]:
        blockers.append("b2_b3_contrast_failed")
    return {
        "sample_id": sample_row["sample_id"],
        "per_level": per_level,
        **checks,
        "real_b2_b3_contrast_passed": bool(
            checks["real_b2_target_includes_scaffold"]
            and checks["real_b2_target_includes_warhead"]
            and checks["real_b2_context_is_linker"]
            and checks["real_b2_b3_target_masks_not_identical"]
            and checks["real_b2_b3_context_masks_not_identical"]
        ),
        "status": "passed" if not blockers else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def run_real_covalent_batch_adapter_gate_v0(selected_artifact: dict[str, Any] | None) -> dict[str, Any]:
    if not selected_artifact:
        return {
            "dataset_created": False,
            "dataloader_created": False,
            "real_batch_adapter_gate_passed": False,
            "real_model_input_mapping_gate_passed": False,
            "blocking_reasons": ["selected_artifact_missing"],
            "level_results": {},
        }
    blockers: list[str] = []
    dataset = CovalentNPZDataset(selected_artifact["sample_index_csv"])
    batch_size = min(2, len(dataset))
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0, collate_fn=covalent_npz_collate_fn)
    batch = next(iter(dataloader))
    level_results: dict[str, Any] = {}
    for level in CANONICAL_MASK_LEVELS:
        adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=level)
        adapted_valid, adapted_reasons = validate_adapted_covalent_batch_v0(adapted)
        model_input = build_covalent_model_input_v0(adapted)
        model_input_valid_raw, model_input_reasons_raw = validate_covalent_model_input_v0(model_input)
        b3_aware_override = False
        model_input_reasons = list(model_input_reasons_raw)
        if level == "B3_scaffold_only" and not model_input_valid_raw:
            allowed = {f"reactive_not_in_target:{idx}" for idx in range(int(model_input["batch_size"]))}
            reactive_in_context = True
            reactive_not_in_target = True
            for idx in range(int(model_input["batch_size"])):
                atom_idx = int(model_input["ligand_reactive_atom_index"][idx].item())
                reactive_in_context = reactive_in_context and bool(model_input["ligand_context_mask"][idx, atom_idx].item())
                reactive_not_in_target = reactive_not_in_target and not bool(model_input["ligand_target_mask"][idx, atom_idx].item())
            if set(model_input_reasons_raw).issubset(allowed) and reactive_in_context and reactive_not_in_target:
                b3_aware_override = True
                model_input_reasons = []
        model_input_valid = bool(model_input_valid_raw or b3_aware_override)
        diffsbdd_like = build_diffsbdd_like_input_from_covalent_v0(model_input)
        diffsbdd_valid, diffsbdd_reasons = validate_diffsbdd_like_input_v0(diffsbdd_like)
        level_passed = bool(adapted_valid and model_input_valid and diffsbdd_valid)
        if not level_passed:
            blockers.append(f"{level}_gate_failed")
        level_results[level] = {
            "adapted_valid": adapted_valid,
            "adapted_reasons": adapted_reasons,
            "model_input_valid_raw": model_input_valid_raw,
            "model_input_b3_aware_override": b3_aware_override,
            "model_input_valid": model_input_valid,
            "model_input_reasons": model_input_reasons,
            "diffsbdd_like_valid": diffsbdd_valid,
            "diffsbdd_like_reasons": diffsbdd_reasons,
            "target_atom_count": int(model_input["ligand_target_mask"].sum().item()),
            "context_atom_count": int(model_input["ligand_context_mask"].sum().item()),
            "ligand_feature_dim": int(diffsbdd_like["ligand"]["one_hot"].shape[1]),
            "pocket_feature_dim": int(diffsbdd_like["pocket"]["one_hot"].shape[1]),
            "status": "passed" if level_passed else "blocked",
        }
    return {
        "dataset_created": True,
        "dataloader_created": True,
        "dataset_len": len(dataset),
        "batch_size": batch_size,
        "batch_sample_ids": list(batch["sample_id"]),
        "level_results": level_results,
        "real_batch_adapter_gate_passed": all(result["adapted_valid"] for result in level_results.values()),
        "real_model_input_mapping_gate_passed": all(
            result["model_input_valid"] and result["diffsbdd_like_valid"] for result in level_results.values()
        ),
        "blocking_reasons": sorted(set(blockers)),
    }


def build_real_covalent_feature_mapping_loader_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step11r_validated = validate_step11r_outputs_v0()
    except Exception as exc:
        step11r_validated = False
        blockers.append(f"step11r_validation_failed:{type(exc).__name__}:{exc}")
    discovery = discover_existing_real_covalent_artifacts_v0()
    blockers.extend(discovery.get("blocking_reasons", []))
    selected = discovery.get("selected")
    sample_rows = audit_real_covalent_sample_fields_v0(selected)
    passed_samples = [row for row in sample_rows if row.get("status") == "passed"]
    failed_samples = [row for row in sample_rows if row.get("status") != "passed"]
    if not sample_rows:
        blockers.append("no_real_samples_audited")
    if not passed_samples:
        blockers.append("no_real_samples_passed_field_audit")
    mask_results = [derive_and_validate_five_level_masks_for_real_sample_v0(row) for row in passed_samples]
    if not mask_results:
        blockers.append("no_five_level_mask_derivation_results")
    batch_gate = run_real_covalent_batch_adapter_gate_v0(selected)
    blockers.extend(batch_gate.get("blocking_reasons", []))
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")

    all_five_level_masks_available = bool(mask_results and all(result["all_five_level_masks_available"] for result in mask_results))
    real_five_level_mask_contract_proven = bool(mask_results and all(result["status"] == "passed" for result in mask_results))
    real_b3_target_is_scaffold = bool(mask_results and all(result["real_b3_target_is_scaffold"] for result in mask_results))
    real_b3_context_is_linker_warhead = bool(mask_results and all(result["real_b3_context_is_linker_warhead"] for result in mask_results))
    real_b3_reactive_atom_in_context = bool(mask_results and all(result["real_b3_reactive_atom_in_context"] for result in mask_results))
    real_b3_reactive_atom_in_target = bool(mask_results and any(result["real_b3_reactive_atom_in_target"] for result in mask_results))
    real_b2_b3_contrast_passed = bool(mask_results and all(result["real_b2_b3_contrast_passed"] for result in mask_results))
    real_batch_adapter_gate_passed = bool(batch_gate.get("real_batch_adapter_gate_passed"))
    real_model_input_mapping_gate_passed = bool(batch_gate.get("real_model_input_mapping_gate_passed"))
    real_covalent_sample_field_contract_proven = bool(passed_samples)
    real_b3_loader_contract_proven = bool(
        real_b3_target_is_scaffold
        and real_b3_context_is_linker_warhead
        and real_b3_reactive_atom_in_context
        and not real_b3_reactive_atom_in_target
        and real_batch_adapter_gate_passed
    )
    passed = bool(
        step11r_validated
        and discovery["selected_artifact_is_real_covalent"]
        and not discovery["selected_artifact_is_synthetic_only"]
        and real_covalent_sample_field_contract_proven
        and real_five_level_mask_contract_proven
        and real_b3_loader_contract_proven
        and real_b2_b3_contrast_passed
        and real_model_input_mapping_gate_passed
        and not source_modified
        and not forbidden_artifacts
    )
    if not passed and not blockers:
        blockers.append("real_covalent_feature_mapping_loader_gate_failed")
    blockers = sorted(set(reason for reason in blockers if reason))
    recommended = "real_covalent_pretraining_smoke_design" if passed else "real_covalent_feature_mapping_loader_gate_debug"
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11r_validated": step11r_validated,
        "discovered_artifact_count": discovery["discovered_artifact_count"],
        "discovered_manifest_count": discovery["discovered_manifest_count"],
        "discovered_npz_count": discovery["discovered_npz_count"],
        "selected_real_data_root": discovery["selected_real_data_root"],
        "selected_loader_or_tensor_artifact": discovery["selected_loader_or_tensor_artifact"],
        "selected_artifact_is_real_covalent": discovery["selected_artifact_is_real_covalent"],
        "selected_artifact_is_synthetic_only": discovery["selected_artifact_is_synthetic_only"],
        "audited_real_sample_count": len(sample_rows),
        "passed_real_sample_count": len(passed_samples),
        "failed_real_sample_count": len(failed_samples),
        "canonical_mask_levels": list(CANONICAL_MASK_LEVELS),
        "all_five_level_masks_available": all_five_level_masks_available,
        "real_five_level_mask_contract_proven": real_five_level_mask_contract_proven,
        "real_b3_target_is_scaffold": real_b3_target_is_scaffold,
        "real_b3_context_is_linker_warhead": real_b3_context_is_linker_warhead,
        "real_b3_reactive_atom_in_context": real_b3_reactive_atom_in_context,
        "real_b3_reactive_atom_in_target": real_b3_reactive_atom_in_target,
        "real_b2_b3_contrast_passed": real_b2_b3_contrast_passed,
        "dataset_created": bool(batch_gate.get("dataset_created")),
        "dataloader_created": bool(batch_gate.get("dataloader_created")),
        "batch_size": int(batch_gate.get("batch_size", 0) or 0),
        "real_batch_adapter_gate_passed": real_batch_adapter_gate_passed,
        "real_model_input_mapping_gate_passed": real_model_input_mapping_gate_passed,
        "real_covalent_feature_mapping_loader_gate_passed": passed,
        "real_covalent_sample_field_contract_proven": real_covalent_sample_field_contract_proven,
        "real_b3_loader_contract_proven": real_b3_loader_contract_proven,
        "real_covalent_pretraining_smoke_allowed": passed,
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
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        "parameter_update_allowed": False,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": passed,
        "recommended_next_step": recommended,
        "blocking_reasons": blockers,
    }
    sample_table_rows = []
    for row in sample_rows:
        mask_result = next((result for result in mask_results if result["sample_id"] == row["sample_id"]), {})
        sample_table_rows.append(
            {
                **row,
                "all_five_level_masks_available": mask_result.get("all_five_level_masks_available", False),
                "real_b3_target_is_scaffold": mask_result.get("real_b3_target_is_scaffold", False),
                "real_b3_context_is_linker_warhead": mask_result.get("real_b3_context_is_linker_warhead", False),
                "real_b3_reactive_atom_in_context": mask_result.get("real_b3_reactive_atom_in_context", False),
                "real_b3_reactive_atom_in_target": mask_result.get("real_b3_reactive_atom_in_target", False),
                "real_b2_b3_contrast_passed": mask_result.get("real_b2_b3_contrast_passed", False),
                "mask_derivation_status": mask_result.get("status", "blocked"),
                "mask_derivation_blocking_reasons": ";".join(mask_result.get("blocking_reasons", [])),
            }
        )
    return {
        "manifest": manifest,
        "discovery": discovery,
        "sample_table_rows": sample_table_rows,
        "mask_results": mask_results,
        "batch_gate": batch_gate,
        "report_sections": {
            "step11r_precondition": {"step11r_validated": step11r_validated},
            "artifact_discovery": discovery,
            "selected_artifact_gate": {
                "selected_real_data_root": discovery["selected_real_data_root"],
                "selected_loader_or_tensor_artifact": discovery["selected_loader_or_tensor_artifact"],
                "selected_artifact_is_real_covalent": discovery["selected_artifact_is_real_covalent"],
                "selected_artifact_is_synthetic_only": discovery["selected_artifact_is_synthetic_only"],
            },
            "real_sample_field_audit": {
                "audited_real_sample_count": len(sample_rows),
                "passed_real_sample_count": len(passed_samples),
                "failed_real_sample_count": len(failed_samples),
            },
            "five_level_mask_derivation": {
                "canonical_mask_levels": list(CANONICAL_MASK_LEVELS),
                "all_five_level_masks_available": all_five_level_masks_available,
                "real_five_level_mask_contract_proven": real_five_level_mask_contract_proven,
            },
            "b3_real_contract": {
                "real_b3_target_is_scaffold": real_b3_target_is_scaffold,
                "real_b3_context_is_linker_warhead": real_b3_context_is_linker_warhead,
                "real_b3_reactive_atom_in_context": real_b3_reactive_atom_in_context,
                "real_b3_reactive_atom_in_target": real_b3_reactive_atom_in_target,
                "real_b2_b3_contrast_passed": real_b2_b3_contrast_passed,
            },
            "batch_adapter_gate": batch_gate,
            "model_input_mapping_gate": {
                "real_model_input_mapping_gate_passed": real_model_input_mapping_gate_passed,
                "level_results": batch_gate.get("level_results", {}),
            },
            "safety_boundary": {
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
            },
        },
    }
