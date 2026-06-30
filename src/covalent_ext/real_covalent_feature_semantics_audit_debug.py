from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import torch

from covalent_ext.model_input_adapter import expected_reactive_atom_region_for_mask_level_v0
from covalent_ext.npz_dataset import CovalentNPZDataset
from covalent_ext.real_covalent_feature_semantics_audit import (
    CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX,
    CHECKPOINT_10D_INDEX_TO_ATOM_SYMBOL,
)
from covalent_ext.real_covalent_pretrained_forward_loss_smoke import (
    CANONICAL_MASK_LEVELS,
    CHECKPOINT_PATH,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    INPUT_SOURCE,
    PROTECTED_SOURCE_PATHS,
    SELECTED_REAL_SAMPLE_INDEX,
    build_real_covalent_forward_loss_batch_bundle_v0,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_feature_semantics_audit_debug_v0"
PREVIOUS_STAGE = "real_covalent_feature_semantics_audit_v0"

STEP12F_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_feature_semantics_audit_v0/"
    "real_covalent_feature_semantics_audit_manifest.json"
)
STEP12F_AUDIT_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_feature_semantics_audit_v0/"
    "real_covalent_feature_semantics_audit_table.csv"
)
STEP12F_SUMMARY_MD = Path("docs/real_covalent_feature_semantics_audit_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_feature_semantics_audit_debug_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_feature_semantics_audit_debug_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_feature_semantics_audit_debug_manifest.json"
DEBUG_TABLE_CSV = OUTPUT_ROOT / "real_covalent_feature_semantics_audit_debug_table.csv"
SUMMARY_MD = Path("docs/real_covalent_feature_semantics_audit_debug_v0_summary.md")

UNKNOWN_PROTEIN_ATOMIC_NUMBER = 12
UNKNOWN_PROTEIN_ATOM_SYMBOL = "Mg"
FILTER_POLICY_NAME = "drop_non_checkpoint_vocab_pocket_atoms_before_checkpoint_compatible_one_hot"
DIRECT_LIGAND_CONTACT_DISTANCE_A = 3.0
LIGAND_REACTIVE_CONTACT_DISTANCE_A = 4.0
CLOSE_TO_LIGAND_DISTANCE_A = 6.0

ATOMIC_NUMBER_TO_SYMBOL = {
    5: "B",
    6: "C",
    7: "N",
    8: "O",
    9: "F",
    12: "Mg",
    15: "P",
    16: "S",
    17: "Cl",
    35: "Br",
    53: "I",
}


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


def _finite_scalar(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


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


def _mapping_as_jsonable(mapping: dict[int, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in sorted(mapping.items())}


def _atom_symbol(atomic_number: int) -> str:
    return ATOMIC_NUMBER_TO_SYMBOL.get(int(atomic_number), f"Z{int(atomic_number)}")


def _json_list(values: list[Any]) -> str:
    return json.dumps(values, sort_keys=True)


def validate_step12b_validator_behavior_v0() -> bool:
    expected_regions = {
        "A_warhead_only": "target",
        "B_linker_warhead": "target",
        "B2_scaffold_warhead": "target",
        "B3_scaffold_only": "context",
        "C_scaffold_linker_warhead": "target",
    }
    blockers: list[str] = []
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
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def validate_step12f_clean_block_v0() -> bool:
    if not STEP12F_MANIFEST_JSON.is_file() or not STEP12F_AUDIT_TABLE_CSV.is_file() or not STEP12F_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12F outputs are missing")
    manifest = _load_json(STEP12F_MANIFEST_JSON)
    rows = _read_csv(STEP12F_AUDIT_TABLE_CSV)
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_backward_smoke_v0",
        "step12e_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_ligand_feature_dim": 10,
        "checkpoint_pocket_feature_dim": 10,
        "checkpoint_feature_semantics_source": "repo_dataset_info_or_config",
        "checkpoint_feature_semantics_directly_encoded": True,
        "checkpoint_10d_mapping_matches_project_mapping": True,
        "sample_count": 3,
        "ligand_unknown_atom_count": 0,
        "protein_unknown_atom_count": 2,
        "protein_unknown_atom_numbers": [UNKNOWN_PROTEIN_ATOMIC_NUMBER],
        "unknown_atom_policy_triggered": True,
        "zero_vector_unknown_atom_policy_safe": False,
        "audited_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "passed_mask_level_count": 0,
        "failed_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "all_checkpoint_compatible_batches_constructed": True,
        "all_ligand_one_hot_row_sums_valid": True,
        "all_pocket_one_hot_row_sums_valid": False,
        "all_ligand_unknown_atom_count_zero": True,
        "all_pocket_unknown_atom_count_zero": False,
        "feature_semantics_dimension_contract_passed": False,
        "feature_semantics_mapping_confirmed": True,
        "feature_semantics_known_after_audit": False,
        "real_covalent_feature_semantics_audit_passed": False,
        "real_covalent_cuda_forward_backward_smoke_allowed": False,
        "real_covalent_single_optimizer_step_smoke_allowed": False,
        "recommended_next_step": "real_covalent_feature_semantics_audit_debug",
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": False,
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step12f_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect("protein_unknown_atoms_present" in manifest.get("blocking_reasons", []), "step12f_missing_protein_unknown_blocker", blockers)

    row_types = [row.get("row_type") for row in rows]
    conversion_rows = [row for row in rows if row.get("row_type") == "mask_level_conversion"]
    _expect("checkpoint_feature_contract" in row_types, "step12f_checkpoint_contract_row_missing", blockers)
    _expect("real_atom_vocabulary" in row_types, "step12f_real_vocab_row_missing", blockers)
    _expect("decision" in row_types, "step12f_decision_row_missing", blockers)
    _expect(len(conversion_rows) == len(CANONICAL_MASK_LEVELS), "step12f_conversion_row_count_invalid", blockers)
    _expect([row.get("mask_level") for row in conversion_rows] == CANONICAL_MASK_LEVELS, "step12f_conversion_order_invalid", blockers)
    for row in conversion_rows:
        _expect(row.get("status") == "blocked", f"step12f_conversion_not_blocked:{row.get('mask_level')}", blockers)
        _expect(row.get("pocket_one_hot_row_sums_valid") == "False", "step12f_expected_pocket_row_sum_block", blockers)
    summary = STEP12F_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "UNKNOWN_ATOM_FEATURE_POLICY",
        "feature_semantics_known=False",
        "recommended_next_step: real_covalent_feature_semantics_audit_debug",
    ]:
        _expect(snippet in summary, f"step12f_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def locate_unknown_protein_atoms_v0() -> dict[str, Any]:
    dataset = CovalentNPZDataset(SELECTED_REAL_SAMPLE_INDEX)
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for sample_index, sample in enumerate(dataset):
        protein_atomic = sample["protein_atomic_numbers"].detach().cpu().to(dtype=torch.long)
        unknown_indices = (protein_atomic == UNKNOWN_PROTEIN_ATOMIC_NUMBER).nonzero(as_tuple=False).view(-1)
        for local_index_tensor in unknown_indices:
            local_index = int(local_index_tensor.item())
            row_blockers: list[str] = []
            protein_coords = sample["protein_atom_coords"].detach().cpu().to(dtype=torch.float32)
            ligand_coords = sample["ligand_atom_coords"].detach().cpu().to(dtype=torch.float32)
            ligand_atomic = sample["ligand_atomic_numbers"].detach().cpu().to(dtype=torch.long)
            if local_index < 0 or local_index >= protein_coords.shape[0]:
                row_blockers.append("protein_atom_index_out_of_range")
                mg_coord = torch.full((3,), float("nan"))
            else:
                mg_coord = protein_coords[local_index]
            if protein_coords.numel() == 0 or ligand_coords.numel() == 0 or not torch.isfinite(mg_coord).all():
                row_blockers.append("coords_unavailable")
                min_distance = float("nan")
                nearest_ligand_idx = -1
                nearest_ligand_atomic_number = -1
                reactive_distance = float("nan")
                centroid_distance = float("nan")
            else:
                distances = torch.linalg.norm(ligand_coords - mg_coord, dim=1)
                min_distance_tensor, nearest_idx_tensor = torch.min(distances, dim=0)
                min_distance = float(min_distance_tensor.item())
                nearest_ligand_idx = int(nearest_idx_tensor.item())
                nearest_ligand_atomic_number = int(ligand_atomic[nearest_ligand_idx].item())
                reactive_index = int(sample["ligand_reactive_atom_index"].item())
                if 0 <= reactive_index < ligand_coords.shape[0]:
                    reactive_distance = float(torch.linalg.norm(ligand_coords[reactive_index] - mg_coord).item())
                else:
                    reactive_distance = float("nan")
                    row_blockers.append("ligand_reactive_atom_index_invalid")
                centroid_distance = float(torch.linalg.norm(ligand_coords.mean(dim=0) - mg_coord).item())
            protein_reactive_distance = float("nan")
            nearest_protein_reactive_atom_index = -1
            reactive_label = str(sample.get("protein_reactive_residue_label", ""))
            residue_ids = sample.get("protein_residue_ids")
            if torch.is_tensor(residue_ids) and reactive_label:
                label_parts = reactive_label.split(":")
                reactive_residue_number = None
                if len(label_parts) >= 2:
                    try:
                        reactive_residue_number = int(label_parts[1])
                    except ValueError:
                        reactive_residue_number = None
                if reactive_residue_number is not None:
                    residue_mask = residue_ids.detach().cpu().to(dtype=torch.long) == reactive_residue_number
                    if residue_mask.any() and torch.isfinite(mg_coord).all():
                        reactive_coords = protein_coords[residue_mask]
                        reactive_distances = torch.linalg.norm(reactive_coords - mg_coord, dim=1)
                        protein_reactive_distance = float(reactive_distances.min().item())
                        absolute_indices = residue_mask.nonzero(as_tuple=False).view(-1)
                        nearest_local = int(torch.argmin(reactive_distances).item())
                        nearest_protein_reactive_atom_index = int(absolute_indices[nearest_local].item())
            metadata_fields_available: list[str] = []
            chain_id = "unknown"
            residue_id = "unknown"
            if "protein_chain_ids" in sample and local_index < len(sample["protein_chain_ids"]):
                metadata_fields_available.append("protein_chain_ids")
                chain_id = str(sample["protein_chain_ids"][local_index])
            if torch.is_tensor(residue_ids) and local_index < residue_ids.shape[0]:
                metadata_fields_available.append("protein_residue_ids")
                residue_id = str(int(residue_ids[local_index].item()))
            if reactive_label:
                metadata_fields_available.append("protein_reactive_residue_label")
            direct_contact = bool(_finite_scalar(min_distance) and min_distance <= DIRECT_LIGAND_CONTACT_DISTANCE_A)
            close_to_ligand = bool(_finite_scalar(min_distance) and min_distance <= CLOSE_TO_LIGAND_DISTANCE_A)
            likely_filterable = bool(not direct_contact)
            row = {
                "row_type": "unknown_protein_atom",
                "sample_id": str(sample["sample_id"]),
                "sample_index": sample_index,
                "protein_atom_local_index": local_index,
                "atomic_number": UNKNOWN_PROTEIN_ATOMIC_NUMBER,
                "atom_symbol": UNKNOWN_PROTEIN_ATOM_SYMBOL,
                "protein_coord_x": float(mg_coord[0].item()),
                "protein_coord_y": float(mg_coord[1].item()),
                "protein_coord_z": float(mg_coord[2].item()),
                "ligand_atom_count": int(sample["ligand_atomic_numbers"].shape[0]),
                "protein_atom_count": int(protein_atomic.shape[0]),
                "ligand_reactive_atom_index": int(sample["ligand_reactive_atom_index"].item()),
                "ligand_reactive_atom_distance": reactive_distance,
                "min_distance_to_any_ligand_atom": min_distance,
                "nearest_ligand_atom_index": nearest_ligand_idx,
                "nearest_ligand_atomic_number": nearest_ligand_atomic_number,
                "nearest_ligand_atom_symbol": _atom_symbol(nearest_ligand_atomic_number),
                "distance_to_ligand_centroid": centroid_distance,
                "protein_reactive_residue_atom_distance_min": protein_reactive_distance,
                "nearest_protein_reactive_atom_index": nearest_protein_reactive_atom_index,
                "direct_ligand_contact_candidate": direct_contact,
                "close_to_ligand_candidate": close_to_ligand,
                "likely_metal_cofactor_or_crystal_ion": likely_filterable,
                "metadata_available": bool(metadata_fields_available),
                "metadata_fields_available": metadata_fields_available,
                "chain_id": chain_id,
                "residue_name": "unknown",
                "residue_id": residue_id,
                "residue_number": residue_id,
                "resseq": residue_id,
                "insertion_code": "unknown",
                "atom_name": "unknown",
                "hetero_flag": "unknown",
                "status": "passed" if not row_blockers else "blocked",
                "blocking_reasons": sorted(set(row_blockers)),
            }
            rows.append(row)
            blockers.extend(f"{row['sample_id']}:{reason}" for reason in row_blockers)
    if not rows:
        blockers.append("unknown_protein_atom_not_found")
    if any(not _finite_scalar(row["min_distance_to_any_ligand_atom"]) for row in rows):
        blockers.append("mg_ligand_distance_not_finite")
    if any(not _finite_scalar(row["ligand_reactive_atom_distance"]) for row in rows):
        blockers.append("mg_ligand_reactive_distance_not_finite")
    distances = [float(row["min_distance_to_any_ligand_atom"]) for row in rows if _finite_scalar(row["min_distance_to_any_ligand_atom"])]
    reactive_distances = [
        float(row["ligand_reactive_atom_distance"]) for row in rows if _finite_scalar(row["ligand_reactive_atom_distance"])
    ]
    return {
        "rows": rows,
        "unknown_protein_atom_localization_passed": bool(rows and not blockers),
        "mg_localization_passed": bool(rows and not blockers),
        "mg_atom_count": len(rows),
        "mg_sample_ids": sorted({str(row["sample_id"]) for row in rows}),
        "mg_all_coords_available": all(
            _finite_scalar(row["protein_coord_x"])
            and _finite_scalar(row["protein_coord_y"])
            and _finite_scalar(row["protein_coord_z"])
            for row in rows
        ),
        "mg_min_distance_to_ligand": min(distances) if distances else float("nan"),
        "mg_max_distance_to_ligand": max(distances) if distances else float("nan"),
        "mg_mean_distance_to_ligand": (sum(distances) / len(distances)) if distances else float("nan"),
        "mg_min_distance_to_ligand_reactive_atom": min(reactive_distances) if reactive_distances else float("nan"),
        "mg_direct_ligand_contact_detected": any(bool(row["direct_ligand_contact_candidate"]) for row in rows),
        "mg_close_to_ligand_detected": any(bool(row["close_to_ligand_candidate"]) for row in rows),
        "mg_likely_filterable": all(bool(row["likely_metal_cofactor_or_crystal_ion"]) for row in rows),
        "metadata_available_for_all_mg": all(bool(row["metadata_available"]) for row in rows) if rows else False,
        "metadata_available_for_any_mg": any(bool(row["metadata_available"]) for row in rows),
        "status": "passed" if rows and not blockers else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def _one_hot_known_only(atomic_numbers: torch.Tensor) -> tuple[torch.Tensor, dict[str, Any]]:
    flat_numbers = atomic_numbers.detach().cpu().to(dtype=torch.long).view(-1).tolist()
    one_hot = torch.zeros((len(flat_numbers), len(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX)), dtype=torch.float32)
    unknown_numbers: list[int] = []
    for row_idx, value in enumerate(flat_numbers):
        feature_idx = CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX.get(int(value))
        if feature_idx is None:
            unknown_numbers.append(int(value))
        else:
            one_hot[row_idx, feature_idx] = 1.0
    return one_hot.to(device=atomic_numbers.device), {
        "unknown_atom_numbers": sorted(set(unknown_numbers)),
        "unknown_atom_count": len(unknown_numbers),
    }


def _row_sums_valid(one_hot: torch.Tensor) -> bool:
    if one_hot.ndim != 2 or one_hot.shape[0] == 0:
        return False
    row_sums = one_hot.detach().cpu().sum(dim=1)
    return bool(torch.allclose(row_sums, torch.ones_like(row_sums)))


def _known_mask(atomic_numbers: torch.Tensor) -> torch.Tensor:
    vocab = set(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX)
    values = [int(value) in vocab for value in atomic_numbers.detach().cpu().to(dtype=torch.long).view(-1).tolist()]
    return torch.tensor(values, dtype=torch.bool, device=atomic_numbers.device)


def _reactive_region_preserved(diffsbdd_like: dict[str, Any], mask_level: str) -> bool:
    expected_region = expected_reactive_atom_region_for_mask_level_v0(mask_level)
    reactive = diffsbdd_like["ligand_reactive_atom_index"]
    for idx in range(int(diffsbdd_like["batch_size"])):
        atom_idx = int(reactive[idx].item())
        in_target = bool(diffsbdd_like["ligand_target_mask"][idx, atom_idx].item())
        in_context = bool(diffsbdd_like["ligand_context_mask"][idx, atom_idx].item())
        if expected_region == "target" and not (in_target and not in_context):
            return False
        if expected_region == "context" and not (in_context and not in_target):
            return False
    return True


def build_checkpoint_compatible_real_model_batch_with_projection_filter_debug_v0(
    diffsbdd_like: dict[str, Any],
    mask_level: str,
    device: str = "cpu",
) -> dict[str, Any]:
    blockers: list[str] = []
    if mask_level not in CANONICAL_MASK_LEVELS:
        blockers.append(f"unsupported_mask_level:{mask_level}")
    ligand_mask = diffsbdd_like["ligand_mask"].to(dtype=torch.long)
    pocket_mask = diffsbdd_like["pocket_mask"].to(dtype=torch.long)
    ligand_atomic = diffsbdd_like["ligand_h"][diffsbdd_like["ligand_mask"].to(dtype=torch.bool)].to(dtype=torch.long)
    protein_atomic = diffsbdd_like["protein_h"][diffsbdd_like["protein_mask"].to(dtype=torch.bool)].to(dtype=torch.long)
    pocket_keep = _known_mask(protein_atomic)
    removed_indices = (~pocket_keep).nonzero(as_tuple=False).view(-1)
    removed_numbers = protein_atomic[removed_indices].detach().cpu().to(dtype=torch.long).tolist()
    filtered_protein_atomic = protein_atomic[pocket_keep]
    ligand_one_hot, ligand_unknown = _one_hot_known_only(ligand_atomic)
    pocket_one_hot, pocket_unknown = _one_hot_known_only(filtered_protein_atomic)
    filtered_pocket_coords = diffsbdd_like["pocket_coords"][pocket_keep].to(device=torch.device(device), dtype=torch.float32)
    filtered_pocket_mask = pocket_mask[pocket_keep].to(device=torch.device(device), dtype=torch.long)
    original_num_pocket_nodes = diffsbdd_like["num_pocket_nodes"].detach().cpu().to(dtype=torch.long)
    removed_per_sample = torch.bincount(
        pocket_mask[removed_indices].detach().cpu().to(dtype=torch.long),
        minlength=int(diffsbdd_like["batch_size"]),
    )
    filtered_num_pocket_nodes = (original_num_pocket_nodes - removed_per_sample).to(device=torch.device(device), dtype=torch.long)
    target_mask = diffsbdd_like["ligand_target_mask_flat"].to(device=torch.device(device), dtype=torch.bool)
    context_mask = diffsbdd_like["ligand_context_mask_flat"].to(device=torch.device(device), dtype=torch.bool)
    ligand_masks_unchanged = bool(
        torch.equal(target_mask.cpu(), diffsbdd_like["ligand_target_mask_flat"].detach().cpu())
        and torch.equal(context_mask.cpu(), diffsbdd_like["ligand_context_mask_flat"].detach().cpu())
    )
    reactive_preserved = _reactive_region_preserved(diffsbdd_like, mask_level)
    data_batch = {
        "lig_coords": diffsbdd_like["lig_coords"].to(device=torch.device(device), dtype=torch.float32),
        "lig_one_hot": ligand_one_hot.to(device=torch.device(device)),
        "lig_mask": ligand_mask.to(device=torch.device(device)),
        "pocket_coords": filtered_pocket_coords,
        "pocket_one_hot": pocket_one_hot.to(device=torch.device(device)),
        "pocket_mask": filtered_pocket_mask,
        "num_lig_atoms": diffsbdd_like["num_lig_atoms"].to(device=torch.device(device), dtype=torch.long),
        "num_pocket_nodes": filtered_num_pocket_nodes,
        "lig_fixed": diffsbdd_like["lig_fixed"].to(device=torch.device(device), dtype=torch.bool).view(-1),
    }
    ligand_rows_equal_coords = int(data_batch["lig_one_hot"].shape[0]) == int(data_batch["lig_coords"].shape[0])
    pocket_rows_equal_coords = int(data_batch["pocket_one_hot"].shape[0]) == int(data_batch["pocket_coords"].shape[0])
    ligand_row_sums_valid = _row_sums_valid(data_batch["lig_one_hot"])
    pocket_row_sums_valid = _row_sums_valid(data_batch["pocket_one_hot"])
    if data_batch["lig_one_hot"].shape[1] != 10:
        blockers.append("ligand_feature_dim_not_10")
    if data_batch["pocket_one_hot"].shape[1] != 10:
        blockers.append("pocket_feature_dim_not_10")
    if not ligand_rows_equal_coords:
        blockers.append("ligand_one_hot_row_count_mismatch")
    if not pocket_rows_equal_coords:
        blockers.append("pocket_one_hot_row_count_mismatch")
    if not ligand_row_sums_valid:
        blockers.append("ligand_one_hot_row_sums_invalid")
    if not pocket_row_sums_valid:
        blockers.append("pocket_one_hot_row_sums_invalid")
    if int(ligand_unknown["unknown_atom_count"]) != 0:
        blockers.append("ligand_unknown_atom_count_nonzero")
    if int(pocket_unknown["unknown_atom_count"]) != 0:
        blockers.append("pocket_unknown_atom_count_nonzero")
    if any(int(number) != UNKNOWN_PROTEIN_ATOMIC_NUMBER for number in removed_numbers):
        blockers.append("removed_non_mg_atom")
    if not ligand_masks_unchanged:
        blockers.append("ligand_masks_changed_after_filter")
    if not reactive_preserved:
        blockers.append("ligand_reactive_atom_region_not_preserved")
    constructed = not blockers
    return {
        "data_batch": data_batch,
        "target_mask": target_mask,
        "context_mask": context_mask,
        "metadata": {
            "mask_level": mask_level,
            "input_source": INPUT_SOURCE,
            "real_sample_ids": list(diffsbdd_like["sample_id"]),
            "expected_reactive_atom_region": expected_reactive_atom_region_for_mask_level_v0(mask_level),
            "checkpoint_compatible_batch_constructed_after_filter": constructed,
            "ligand_feature_dim": int(data_batch["lig_one_hot"].shape[1]),
            "pocket_feature_dim": int(data_batch["pocket_one_hot"].shape[1]),
            "ligand_one_hot_rows_equal_ligand_coords_rows": ligand_rows_equal_coords,
            "pocket_one_hot_rows_equal_pocket_coords_rows": pocket_rows_equal_coords,
            "ligand_one_hot_row_sums_valid_after_filter": ligand_row_sums_valid,
            "pocket_one_hot_row_sums_valid_after_filter": pocket_row_sums_valid,
            "ligand_unknown_atom_count_after_filter": int(ligand_unknown["unknown_atom_count"]),
            "pocket_unknown_atom_count_after_filter": int(pocket_unknown["unknown_atom_count"]),
            "removed_pocket_atom_count": int(len(removed_numbers)),
            "removed_pocket_atom_numbers": sorted(set(int(number) for number in removed_numbers)),
            "removed_pocket_atom_symbols": sorted({_atom_symbol(int(number)) for number in removed_numbers}),
            "removed_pocket_atom_indices": [int(index) for index in removed_indices.detach().cpu().tolist()],
            "target_atom_count": int(target_mask.sum().item()),
            "context_atom_count": int(context_mask.sum().item()),
            "ligand_masks_unchanged_after_filter": ligand_masks_unchanged,
            "ligand_reactive_atom_region_preserved": reactive_preserved,
            "no_synthetic_fallback_used": True,
            "projection_filter_only_debug": True,
            "production_adapter_modified": False,
            "blocking_reasons": sorted(set(blockers)),
        },
        "status": "passed" if constructed else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def _sample_filter_projection_rows_v0() -> dict[str, Any]:
    dataset = CovalentNPZDataset(SELECTED_REAL_SAMPLE_INDEX)
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    total_removed = 0
    filtered_numbers: set[int] = set()
    for sample_index, sample in enumerate(dataset):
        ligand_atomic = sample["ligand_atomic_numbers"].detach().cpu().to(dtype=torch.long)
        protein_atomic = sample["protein_atomic_numbers"].detach().cpu().to(dtype=torch.long)
        ligand_known = _known_mask(ligand_atomic)
        protein_known = _known_mask(protein_atomic)
        removed_indices = (~protein_known).nonzero(as_tuple=False).view(-1).detach().cpu().to(dtype=torch.long).tolist()
        removed_numbers = [int(protein_atomic[index].item()) for index in removed_indices]
        filtered_numbers.update(removed_numbers)
        total_removed += len(removed_indices)
        row_blockers: list[str] = []
        if ligand_known.sum().item() != ligand_atomic.shape[0]:
            row_blockers.append("ligand_unknown_atom_present")
        if any(number != UNKNOWN_PROTEIN_ATOMIC_NUMBER for number in removed_numbers):
            row_blockers.append("removed_non_mg_atom")
        post_filter_unknown_protein = int((~_known_mask(protein_atomic[protein_known])).sum().item())
        post_filter_unknown_ligand = int((~ligand_known).sum().item())
        if post_filter_unknown_protein != 0:
            row_blockers.append("post_filter_protein_unknown_nonzero")
        row = {
            "row_type": "sample_filter_projection",
            "sample_id": str(sample["sample_id"]),
            "sample_index": sample_index,
            "original_protein_atom_count": int(protein_atomic.shape[0]),
            "filtered_protein_atom_count": int(protein_known.sum().item()),
            "removed_protein_atom_count": int(len(removed_indices)),
            "removed_atomic_numbers": sorted(set(removed_numbers)),
            "removed_atom_symbols": sorted({_atom_symbol(number) for number in removed_numbers}),
            "removed_atom_indices": removed_indices,
            "ligand_atom_count": int(ligand_atomic.shape[0]),
            "ligand_atom_count_changed": False,
            "all_remaining_protein_atoms_in_checkpoint_10d_vocab": post_filter_unknown_protein == 0,
            "all_ligand_atoms_in_checkpoint_10d_vocab": bool(ligand_known.all().item()),
            "post_filter_unknown_protein_atom_count": post_filter_unknown_protein,
            "post_filter_unknown_ligand_atom_count": post_filter_unknown_ligand,
            "status": "passed" if not row_blockers else "blocked",
            "blocking_reasons": sorted(set(row_blockers)),
        }
        rows.append(row)
        blockers.extend(f"{row['sample_id']}:{reason}" for reason in row_blockers)
    return {
        "rows": rows,
        "sample_count": len(dataset),
        "sample_ids": [row["sample_id"] for row in rows],
        "total_removed_pocket_atom_count": total_removed,
        "filtered_atom_numbers": sorted(filtered_numbers),
        "filtered_atom_symbols": sorted({_atom_symbol(number) for number in filtered_numbers}),
        "post_filter_protein_unknown_atom_count": sum(int(row["post_filter_unknown_protein_atom_count"]) for row in rows),
        "post_filter_ligand_unknown_atom_count": sum(int(row["post_filter_unknown_ligand_atom_count"]) for row in rows),
        "all_remaining_protein_atoms_in_checkpoint_10d_vocab": all(
            bool(row["all_remaining_protein_atoms_in_checkpoint_10d_vocab"]) for row in rows
        ),
        "all_ligand_atoms_in_checkpoint_10d_vocab": all(bool(row["all_ligand_atoms_in_checkpoint_10d_vocab"]) for row in rows),
        "status": "passed" if not blockers else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def simulate_noncheckpoint_pocket_atom_filter_projection_v0() -> dict[str, Any]:
    sample_projection = _sample_filter_projection_rows_v0()
    mask_rows: list[dict[str, Any]] = []
    blockers: list[str] = list(sample_projection["blocking_reasons"])
    for mask_level in CANONICAL_MASK_LEVELS:
        level_blockers: list[str] = []
        expected_region = expected_reactive_atom_region_for_mask_level_v0(mask_level)
        try:
            bundle = build_real_covalent_forward_loss_batch_bundle_v0(mask_level, "cpu")
            filtered_batch = build_checkpoint_compatible_real_model_batch_with_projection_filter_debug_v0(
                bundle["diffsbdd_like"], mask_level, "cpu"
            )
            metadata = filtered_batch["metadata"]
            level_blockers.extend(filtered_batch.get("blocking_reasons", []))
            row = {
                "row_type": "mask_level_filter_projection",
                "mask_level": mask_level,
                "expected_reactive_atom_region": expected_region,
                "checkpoint_compatible_batch_constructed_after_filter": bool(
                    metadata["checkpoint_compatible_batch_constructed_after_filter"]
                ),
                "ligand_feature_dim": int(metadata["ligand_feature_dim"]),
                "pocket_feature_dim": int(metadata["pocket_feature_dim"]),
                "ligand_one_hot_rows_equal_ligand_coords_rows": bool(
                    metadata["ligand_one_hot_rows_equal_ligand_coords_rows"]
                ),
                "pocket_one_hot_rows_equal_pocket_coords_rows": bool(
                    metadata["pocket_one_hot_rows_equal_pocket_coords_rows"]
                ),
                "ligand_one_hot_row_sums_valid_after_filter": bool(
                    metadata["ligand_one_hot_row_sums_valid_after_filter"]
                ),
                "pocket_one_hot_row_sums_valid_after_filter": bool(
                    metadata["pocket_one_hot_row_sums_valid_after_filter"]
                ),
                "ligand_unknown_atom_count_after_filter": int(metadata["ligand_unknown_atom_count_after_filter"]),
                "pocket_unknown_atom_count_after_filter": int(metadata["pocket_unknown_atom_count_after_filter"]),
                "removed_pocket_atom_count": int(metadata["removed_pocket_atom_count"]),
                "removed_pocket_atom_numbers": metadata["removed_pocket_atom_numbers"],
                "removed_pocket_atom_symbols": metadata["removed_pocket_atom_symbols"],
                "removed_pocket_atom_indices": metadata["removed_pocket_atom_indices"],
                "no_synthetic_fallback_used": bool(metadata["no_synthetic_fallback_used"]),
                "ligand_masks_unchanged_after_filter": bool(metadata["ligand_masks_unchanged_after_filter"]),
                "ligand_reactive_atom_region_preserved": bool(metadata["ligand_reactive_atom_region_preserved"]),
                "status": "passed" if not level_blockers else "blocked",
                "blocking_reasons": sorted(set(level_blockers)),
            }
        except Exception as exc:
            level_blockers.append(f"projection_filter_failed:{type(exc).__name__}:{exc}")
            row = {
                "row_type": "mask_level_filter_projection",
                "mask_level": mask_level,
                "expected_reactive_atom_region": expected_region,
                "checkpoint_compatible_batch_constructed_after_filter": False,
                "ligand_feature_dim": 0,
                "pocket_feature_dim": 0,
                "ligand_one_hot_rows_equal_ligand_coords_rows": False,
                "pocket_one_hot_rows_equal_pocket_coords_rows": False,
                "ligand_one_hot_row_sums_valid_after_filter": False,
                "pocket_one_hot_row_sums_valid_after_filter": False,
                "ligand_unknown_atom_count_after_filter": -1,
                "pocket_unknown_atom_count_after_filter": -1,
                "removed_pocket_atom_count": -1,
                "removed_pocket_atom_numbers": [],
                "removed_pocket_atom_symbols": [],
                "removed_pocket_atom_indices": [],
                "no_synthetic_fallback_used": False,
                "ligand_masks_unchanged_after_filter": False,
                "ligand_reactive_atom_region_preserved": False,
                "status": "blocked",
                "blocking_reasons": sorted(set(level_blockers)),
            }
        mask_rows.append(row)
        blockers.extend(f"{mask_level}:{reason}" for reason in row["blocking_reasons"])
    return {
        "sample_rows": sample_projection["rows"],
        "mask_rows": mask_rows,
        "sample_count": sample_projection["sample_count"],
        "sample_ids": sample_projection["sample_ids"],
        "filter_policy_name": FILTER_POLICY_NAME,
        "projection_filter_only_debug": True,
        "production_adapter_modified": False,
        "original_data_modified": False,
        "filtered_atom_numbers": sample_projection["filtered_atom_numbers"],
        "filtered_atom_symbols": sample_projection["filtered_atom_symbols"],
        "total_removed_pocket_atom_count": sample_projection["total_removed_pocket_atom_count"],
        "post_filter_protein_unknown_atom_count": sample_projection["post_filter_protein_unknown_atom_count"],
        "post_filter_ligand_unknown_atom_count": sample_projection["post_filter_ligand_unknown_atom_count"],
        "all_remaining_protein_atoms_in_checkpoint_10d_vocab": sample_projection[
            "all_remaining_protein_atoms_in_checkpoint_10d_vocab"
        ],
        "all_ligand_atoms_in_checkpoint_10d_vocab": sample_projection["all_ligand_atoms_in_checkpoint_10d_vocab"],
        "audited_mask_level_count": len(mask_rows),
        "passed_mask_level_count": sum(1 for row in mask_rows if row["status"] == "passed"),
        "failed_mask_level_count": sum(1 for row in mask_rows if row["status"] != "passed"),
        "all_checkpoint_compatible_batches_constructed_after_filter": all(
            bool(row["checkpoint_compatible_batch_constructed_after_filter"]) for row in mask_rows
        ),
        "all_ligand_one_hot_row_sums_valid_after_filter": all(
            bool(row["ligand_one_hot_row_sums_valid_after_filter"]) for row in mask_rows
        ),
        "all_pocket_one_hot_row_sums_valid_after_filter": all(
            bool(row["pocket_one_hot_row_sums_valid_after_filter"]) for row in mask_rows
        ),
        "all_pocket_unknown_atom_count_zero_after_filter": all(
            int(row["pocket_unknown_atom_count_after_filter"]) == 0 for row in mask_rows
        ),
        "all_ligand_unknown_atom_count_zero_after_filter": all(
            int(row["ligand_unknown_atom_count_after_filter"]) == 0 for row in mask_rows
        ),
        "ligand_masks_unchanged_after_filter": all(bool(row["ligand_masks_unchanged_after_filter"]) for row in mask_rows),
        "ligand_reactive_atom_region_preserved": all(
            bool(row["ligand_reactive_atom_region_preserved"]) for row in mask_rows
        ),
        "no_synthetic_fallback_used": all(bool(row["no_synthetic_fallback_used"]) for row in mask_rows),
        "status": "passed" if not blockers else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def decide_noncheckpoint_pocket_atom_filter_policy_v0(
    step12f_validated: bool,
    localization: dict[str, Any],
    projection: dict[str, Any],
    source_modified: bool,
    forbidden_artifacts: bool,
) -> dict[str, Any]:
    blockers: list[str] = []
    manual_review_reasons: list[str] = []
    if not step12f_validated:
        blockers.append("step12f_clean_block_not_validated")
    if not localization["mg_localization_passed"]:
        blockers.append("mg_localization_failed")
    if localization["mg_direct_ligand_contact_detected"]:
        manual_review_reasons.append("mg_direct_ligand_contact_detected")
    if _finite_scalar(localization["mg_min_distance_to_ligand_reactive_atom"]) and (
        float(localization["mg_min_distance_to_ligand_reactive_atom"]) <= LIGAND_REACTIVE_CONTACT_DISTANCE_A
    ):
        manual_review_reasons.append("mg_ligand_reactive_atom_contact_detected")
    if projection["filtered_atom_numbers"] != [UNKNOWN_PROTEIN_ATOMIC_NUMBER]:
        blockers.append("unexpected_filtered_atom_numbers")
    if projection["total_removed_pocket_atom_count"] != 2:
        blockers.append("unexpected_removed_pocket_atom_count")
    for key in [
        "all_remaining_protein_atoms_in_checkpoint_10d_vocab",
        "all_ligand_atoms_in_checkpoint_10d_vocab",
        "all_checkpoint_compatible_batches_constructed_after_filter",
        "all_ligand_one_hot_row_sums_valid_after_filter",
        "all_pocket_one_hot_row_sums_valid_after_filter",
        "all_pocket_unknown_atom_count_zero_after_filter",
        "all_ligand_unknown_atom_count_zero_after_filter",
        "ligand_masks_unchanged_after_filter",
        "ligand_reactive_atom_region_preserved",
        "no_synthetic_fallback_used",
    ]:
        if not projection[key]:
            blockers.append(key)
    if projection["post_filter_protein_unknown_atom_count"] != 0:
        blockers.append("post_filter_protein_unknown_atom_count_nonzero")
    if projection["post_filter_ligand_unknown_atom_count"] != 0:
        blockers.append("post_filter_ligand_unknown_atom_count_nonzero")
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    if manual_review_reasons:
        return {
            "real_covalent_feature_semantics_audit_debug_passed": False,
            "noncheckpoint_pocket_atom_filter_policy_recommended": False,
            "projection_filter_debug_passed": False,
            "real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed": False,
            "real_covalent_cuda_forward_backward_smoke_allowed": False,
            "real_covalent_single_optimizer_step_smoke_allowed": False,
            "recommended_next_step": "real_covalent_mg_manual_structure_review",
            "blocking_reasons": sorted(set(manual_review_reasons + blockers)),
        }
    passed = bool(not blockers)
    return {
        "real_covalent_feature_semantics_audit_debug_passed": passed,
        "noncheckpoint_pocket_atom_filter_policy_recommended": passed,
        "projection_filter_debug_passed": passed,
        "real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed": passed,
        "real_covalent_cuda_forward_backward_smoke_allowed": False,
        "real_covalent_single_optimizer_step_smoke_allowed": False,
        "recommended_next_step": "real_covalent_noncheckpoint_pocket_atom_filter_gate"
        if passed
        else "real_covalent_feature_semantics_audit_debug_fix",
        "blocking_reasons": sorted(set(blockers)),
    }


def build_real_covalent_feature_semantics_audit_debug_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12f_validated = validate_step12f_clean_block_v0()
    except Exception as exc:
        step12f_validated = False
        blockers.append(f"step12f_clean_block_validation_failed:{type(exc).__name__}:{exc}")
    try:
        step12b_validated = validate_step12b_validator_behavior_v0()
    except Exception as exc:
        step12b_validated = False
        blockers.append(f"step12b_validation_failed:{type(exc).__name__}:{exc}")
    localization = locate_unknown_protein_atoms_v0()
    projection = simulate_noncheckpoint_pocket_atom_filter_projection_v0()
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    decision = decide_noncheckpoint_pocket_atom_filter_policy_v0(
        step12f_validated,
        localization,
        projection,
        source_modified,
        forbidden_artifacts,
    )
    blockers.extend(localization.get("blocking_reasons", []))
    blockers.extend(projection.get("blocking_reasons", []))
    blockers.extend(decision.get("blocking_reasons", []))
    blockers = sorted(set(reason for reason in blockers if reason))
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12f_clean_block_validated": step12f_validated,
        "step12b_mask_level_aware_validator_validated": step12b_validated,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "checkpoint_10d_mapping_project": _mapping_as_jsonable(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX),
        "sample_count": projection["sample_count"],
        "sample_ids": projection["sample_ids"],
        "pre_debug_protein_unknown_atom_numbers": [UNKNOWN_PROTEIN_ATOMIC_NUMBER],
        "pre_debug_protein_unknown_atom_count": 2,
        "pre_debug_ligand_unknown_atom_count": 0,
        "unknown_protein_atom_symbol": UNKNOWN_PROTEIN_ATOM_SYMBOL,
        "unknown_protein_atom_atomic_number": UNKNOWN_PROTEIN_ATOMIC_NUMBER,
        "unknown_protein_atom_localization_passed": localization["unknown_protein_atom_localization_passed"],
        "mg_localization_passed": localization["mg_localization_passed"],
        "mg_atom_count": localization["mg_atom_count"],
        "mg_sample_ids": localization["mg_sample_ids"],
        "mg_all_coords_available": localization["mg_all_coords_available"],
        "mg_min_distance_to_ligand": localization["mg_min_distance_to_ligand"],
        "mg_max_distance_to_ligand": localization["mg_max_distance_to_ligand"],
        "mg_mean_distance_to_ligand": localization["mg_mean_distance_to_ligand"],
        "mg_min_distance_to_ligand_reactive_atom": localization["mg_min_distance_to_ligand_reactive_atom"],
        "mg_direct_ligand_contact_detected": localization["mg_direct_ligand_contact_detected"],
        "mg_close_to_ligand_detected": localization["mg_close_to_ligand_detected"],
        "mg_likely_filterable": localization["mg_likely_filterable"],
        "metadata_available_for_all_mg": localization["metadata_available_for_all_mg"],
        "metadata_available_for_any_mg": localization["metadata_available_for_any_mg"],
        "filter_policy_name": FILTER_POLICY_NAME,
        "projection_filter_only_debug": True,
        "production_adapter_modified": False,
        "original_data_modified": False,
        "filtered_atom_numbers": projection["filtered_atom_numbers"],
        "filtered_atom_symbols": projection["filtered_atom_symbols"],
        "total_removed_pocket_atom_count": projection["total_removed_pocket_atom_count"],
        "post_filter_protein_unknown_atom_count": projection["post_filter_protein_unknown_atom_count"],
        "post_filter_ligand_unknown_atom_count": projection["post_filter_ligand_unknown_atom_count"],
        "all_remaining_protein_atoms_in_checkpoint_10d_vocab": projection[
            "all_remaining_protein_atoms_in_checkpoint_10d_vocab"
        ],
        "all_ligand_atoms_in_checkpoint_10d_vocab": projection["all_ligand_atoms_in_checkpoint_10d_vocab"],
        "audited_mask_level_count": projection["audited_mask_level_count"],
        "passed_mask_level_count": projection["passed_mask_level_count"],
        "failed_mask_level_count": projection["failed_mask_level_count"],
        "all_checkpoint_compatible_batches_constructed_after_filter": projection[
            "all_checkpoint_compatible_batches_constructed_after_filter"
        ],
        "all_ligand_one_hot_row_sums_valid_after_filter": projection["all_ligand_one_hot_row_sums_valid_after_filter"],
        "all_pocket_one_hot_row_sums_valid_after_filter": projection["all_pocket_one_hot_row_sums_valid_after_filter"],
        "all_pocket_unknown_atom_count_zero_after_filter": projection["all_pocket_unknown_atom_count_zero_after_filter"],
        "all_ligand_unknown_atom_count_zero_after_filter": projection["all_ligand_unknown_atom_count_zero_after_filter"],
        "ligand_masks_unchanged_after_filter": projection["ligand_masks_unchanged_after_filter"],
        "ligand_reactive_atom_region_preserved": projection["ligand_reactive_atom_region_preserved"],
        "no_synthetic_fallback_used": projection["no_synthetic_fallback_used"],
        "noncheckpoint_pocket_atom_filter_policy_recommended": decision[
            "noncheckpoint_pocket_atom_filter_policy_recommended"
        ],
        "projection_filter_debug_passed": decision["projection_filter_debug_passed"],
        "real_covalent_feature_semantics_audit_debug_passed": decision[
            "real_covalent_feature_semantics_audit_debug_passed"
        ],
        "real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed": decision[
            "real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed"
        ],
        "real_covalent_cuda_forward_backward_smoke_allowed": False,
        "real_covalent_single_optimizer_step_smoke_allowed": False,
        "recommended_next_step": decision["recommended_next_step"],
        "model_forward_called": False,
        "loss_compute_called": False,
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
        "parameter_update_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": bool(
            step12f_validated
            and step12b_validated
            and decision["real_covalent_feature_semantics_audit_debug_passed"]
            and not source_modified
            and not forbidden_artifacts
            and not blockers
        ),
        "blocking_reasons": blockers,
    }
    debug_table_rows: list[dict[str, Any]] = [
        {
            "row_type": "step12f_precondition",
            "status": "passed" if step12f_validated and step12b_validated else "blocked",
            "step12f_clean_block_validated": step12f_validated,
            "step12b_mask_level_aware_validator_validated": step12b_validated,
            "blocking_reasons": blockers if not (step12f_validated and step12b_validated) else [],
        }
    ]
    debug_table_rows.extend(localization["rows"])
    debug_table_rows.extend(projection["sample_rows"])
    debug_table_rows.extend(projection["mask_rows"])
    debug_table_rows.append(
        {
            "row_type": "filter_policy_decision",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "filter_policy_name": FILTER_POLICY_NAME,
            "noncheckpoint_pocket_atom_filter_policy_recommended": manifest[
                "noncheckpoint_pocket_atom_filter_policy_recommended"
            ],
            "real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed": manifest[
                "real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed"
            ],
            "real_covalent_single_optimizer_step_smoke_allowed": False,
            "recommended_next_step": manifest["recommended_next_step"],
            "blocking_reasons": manifest["blocking_reasons"],
        }
    )
    return {
        "manifest": manifest,
        "debug_table_rows": debug_table_rows,
        "report_sections": {
            "step12f_precondition": {
                "step12f_clean_block_validated": step12f_validated,
                "step12b_mask_level_aware_validator_validated": step12b_validated,
            },
            "unknown_protein_atom_localization": {
                "mg_atom_count": manifest["mg_atom_count"],
                "mg_sample_ids": manifest["mg_sample_ids"],
                "mg_all_coords_available": manifest["mg_all_coords_available"],
            },
            "mg_ligand_distance_assessment": {
                "mg_min_distance_to_ligand": manifest["mg_min_distance_to_ligand"],
                "mg_max_distance_to_ligand": manifest["mg_max_distance_to_ligand"],
                "mg_min_distance_to_ligand_reactive_atom": manifest["mg_min_distance_to_ligand_reactive_atom"],
                "mg_direct_ligand_contact_detected": manifest["mg_direct_ligand_contact_detected"],
                "mg_close_to_ligand_detected": manifest["mg_close_to_ligand_detected"],
            },
            "sample_filter_projection": {
                "total_removed_pocket_atom_count": manifest["total_removed_pocket_atom_count"],
                "filtered_atom_numbers": manifest["filtered_atom_numbers"],
                "post_filter_protein_unknown_atom_count": manifest["post_filter_protein_unknown_atom_count"],
            },
            "mask_level_filter_projection": {
                "audited_mask_level_count": manifest["audited_mask_level_count"],
                "passed_mask_level_count": manifest["passed_mask_level_count"],
                "all_pocket_one_hot_row_sums_valid_after_filter": manifest[
                    "all_pocket_one_hot_row_sums_valid_after_filter"
                ],
            },
            "filter_policy_decision": {
                "noncheckpoint_pocket_atom_filter_policy_recommended": manifest[
                    "noncheckpoint_pocket_atom_filter_policy_recommended"
                ],
                "real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed": manifest[
                    "real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed"
                ],
            },
            "safety_boundary": {
                "model_forward_called": False,
                "loss_compute_called": False,
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
            "next_step_decision": {
                "recommended_next_step": manifest["recommended_next_step"],
                "real_covalent_single_optimizer_step_smoke_allowed": False,
            },
        },
    }
