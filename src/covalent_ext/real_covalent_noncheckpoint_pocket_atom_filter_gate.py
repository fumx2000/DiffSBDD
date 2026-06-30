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
from covalent_ext.real_covalent_feature_semantics_audit import CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX
from covalent_ext.real_covalent_feature_semantics_audit_debug import (
    MANIFEST_JSON as STEP12G_MANIFEST_JSON,
    DEBUG_TABLE_CSV as STEP12G_DEBUG_TABLE_CSV,
    SUMMARY_MD as STEP12G_SUMMARY_MD,
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
STAGE = "real_covalent_noncheckpoint_pocket_atom_filter_gate_v0"
PREVIOUS_STAGE = "real_covalent_feature_semantics_audit_debug_v0"

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_noncheckpoint_pocket_atom_filter_gate_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_noncheckpoint_pocket_atom_filter_gate_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_noncheckpoint_pocket_atom_filter_gate_manifest.json"
FILTER_TABLE_CSV = OUTPUT_ROOT / "real_covalent_noncheckpoint_pocket_atom_filter_gate_table.csv"
SUMMARY_MD = Path("docs/real_covalent_noncheckpoint_pocket_atom_filter_gate_v0_summary.md")

FILTER_POLICY_NAME = "drop_non_checkpoint_vocab_pocket_atoms_before_checkpoint_compatible_one_hot"
ALLOWED_FILTERED_ATOMIC_NUMBERS_FOR_THIS_GATE = [12]
ALLOWED_FILTERED_ATOM_SYMBOLS_FOR_THIS_GATE = ["Mg"]
DIRECT_LIGAND_CONTACT_DISTANCE_A = 3.0
LIGAND_REACTIVE_CONTACT_DISTANCE_A = 4.0
CLOSE_TO_LIGAND_DISTANCE_A = 6.0
NON_CYS_SUPPORT_STATUS = "schema_supported_but_template_audit_pending"

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

ADAPTER_PATHS = [
    "src/covalent_ext/model_input_adapter.py",
    "src/covalent_ext/diffsbdd_input_adapter.py",
    "src/covalent_ext/npz_dataset.py",
]


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


def _mapping_as_jsonable(mapping: dict[int, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in sorted(mapping.items())}


def _atom_symbol(atomic_number: int) -> str:
    return ATOMIC_NUMBER_TO_SYMBOL.get(int(atomic_number), f"Z{int(atomic_number)}")


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


def _adapter_diff_exists() -> bool:
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *ADAPTER_PATHS],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *ADAPTER_PATHS],
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


def _known_mask(atomic_numbers: torch.Tensor) -> torch.Tensor:
    vocab = set(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX)
    values = [int(value) in vocab for value in atomic_numbers.detach().cpu().to(dtype=torch.long).view(-1).tolist()]
    return torch.tensor(values, dtype=torch.bool, device=atomic_numbers.device)


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


def _dataset_sample_lookup() -> dict[str, dict[str, Any]]:
    dataset = CovalentNPZDataset(SELECTED_REAL_SAMPLE_INDEX)
    return {str(sample["sample_id"]): sample for sample in dataset}


def _parse_reactive_residue_label(label: str) -> tuple[str | None, int | None]:
    parts = str(label).split(":")
    if len(parts) < 2:
        return None, None
    try:
        residue_id = int(parts[1])
    except ValueError:
        residue_id = None
    return parts[0] or None, residue_id


def _flat_protein_residue_metadata(diffsbdd_like: dict[str, Any]) -> tuple[list[int | None], list[str | None]]:
    lookup = _dataset_sample_lookup()
    residue_ids: list[int | None] = []
    chain_ids: list[str | None] = []
    for sample_id in diffsbdd_like["sample_id"]:
        sample = lookup.get(str(sample_id))
        if sample is None:
            continue
        residue_ids.extend(int(value) for value in sample["protein_residue_ids"].detach().cpu().tolist())
        chain_ids.extend(str(value) for value in sample["protein_chain_ids"])
    return residue_ids, chain_ids


def _unknown_pocket_atom_rows(diffsbdd_like: dict[str, Any]) -> list[dict[str, Any]]:
    protein_atomic = diffsbdd_like["protein_h"][diffsbdd_like["protein_mask"].to(dtype=torch.bool)].to(dtype=torch.long)
    pocket_keep = _known_mask(protein_atomic)
    unknown_indices = (~pocket_keep).nonzero(as_tuple=False).view(-1)
    pocket_coords = diffsbdd_like["pocket_coords"].detach().cpu().to(dtype=torch.float32)
    pocket_mask = diffsbdd_like["pocket_mask"].detach().cpu().to(dtype=torch.long)
    lig_coords = diffsbdd_like["lig_coords"].detach().cpu().to(dtype=torch.float32)
    lig_mask = diffsbdd_like["lig_mask"].detach().cpu().to(dtype=torch.long)
    ligand_x = diffsbdd_like["ligand_x"].detach().cpu().to(dtype=torch.float32)
    reactive = diffsbdd_like["ligand_reactive_atom_index"].detach().cpu().to(dtype=torch.long)
    residue_ids, chain_ids = _flat_protein_residue_metadata(diffsbdd_like)
    rows: list[dict[str, Any]] = []
    for flat_index_tensor in unknown_indices:
        flat_index = int(flat_index_tensor.item())
        sample_index = int(pocket_mask[flat_index].item())
        local_index = int((pocket_mask[: flat_index + 1] == sample_index).sum().item() - 1)
        atomic_number = int(protein_atomic[flat_index].item())
        coord = pocket_coords[flat_index]
        same_ligand = lig_mask == sample_index
        ligand_coords = lig_coords[same_ligand]
        distances = torch.linalg.norm(ligand_coords - coord, dim=1)
        min_distance_tensor, nearest_ligand_tensor = torch.min(distances, dim=0)
        reactive_idx = int(reactive[sample_index].item())
        reactive_distance = float(torch.linalg.norm(ligand_x[sample_index, reactive_idx] - coord).item())
        reactive_chain, reactive_residue_id = _parse_reactive_residue_label(
            diffsbdd_like["protein_reactive_residue_label"][sample_index]
        )
        residue_id = residue_ids[flat_index] if flat_index < len(residue_ids) else None
        chain_id = chain_ids[flat_index] if flat_index < len(chain_ids) else None
        is_reactive_residue_atom = bool(
            reactive_residue_id is not None
            and residue_id == reactive_residue_id
            and (reactive_chain is None or chain_id == reactive_chain)
        )
        rows.append(
            {
                "flat_pocket_atom_index": flat_index,
                "sample_index": sample_index,
                "sample_id": str(diffsbdd_like["sample_id"][sample_index]),
                "protein_atom_local_index": local_index,
                "atomic_number": atomic_number,
                "atom_symbol": _atom_symbol(atomic_number),
                "min_distance_to_any_ligand_atom": float(min_distance_tensor.item()),
                "nearest_ligand_atom_index": int(nearest_ligand_tensor.item()),
                "ligand_reactive_atom_distance": reactive_distance,
                "direct_ligand_contact_candidate": float(min_distance_tensor.item()) <= DIRECT_LIGAND_CONTACT_DISTANCE_A,
                "ligand_reactive_contact_candidate": reactive_distance <= LIGAND_REACTIVE_CONTACT_DISTANCE_A,
                "close_to_ligand_candidate": float(min_distance_tensor.item()) <= CLOSE_TO_LIGAND_DISTANCE_A,
                "is_reactive_residue_atom": is_reactive_residue_atom,
                "chain_id": chain_id or "unknown",
                "residue_id": residue_id if residue_id is not None else "unknown",
            }
        )
    return rows


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


def validate_step12g_filter_policy_debug_v0() -> bool:
    if not STEP12G_MANIFEST_JSON.is_file() or not STEP12G_DEBUG_TABLE_CSV.is_file() or not STEP12G_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12G outputs are missing")
    manifest = _load_json(STEP12G_MANIFEST_JSON)
    rows = _read_csv(STEP12G_DEBUG_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_feature_semantics_audit_v0",
        "step12f_clean_block_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "pre_debug_protein_unknown_atom_numbers": [12],
        "pre_debug_protein_unknown_atom_count": 2,
        "pre_debug_ligand_unknown_atom_count": 0,
        "unknown_protein_atom_symbol": "Mg",
        "unknown_protein_atom_atomic_number": 12,
        "unknown_protein_atom_localization_passed": True,
        "mg_localization_passed": True,
        "mg_atom_count": 2,
        "mg_sample_ids": ["KRAS_G12C_5F2E_pre_reaction", "KRAS_G12C_6OIM_pre_reaction"],
        "mg_all_coords_available": True,
        "mg_direct_ligand_contact_detected": False,
        "mg_close_to_ligand_detected": True,
        "mg_likely_filterable": True,
        "metadata_available_for_all_mg": True,
        "metadata_available_for_any_mg": True,
        "filter_policy_name": FILTER_POLICY_NAME,
        "projection_filter_only_debug": True,
        "production_adapter_modified": False,
        "original_data_modified": False,
        "filtered_atom_numbers": [12],
        "filtered_atom_symbols": ["Mg"],
        "total_removed_pocket_atom_count": 2,
        "post_filter_protein_unknown_atom_count": 0,
        "post_filter_ligand_unknown_atom_count": 0,
        "all_remaining_protein_atoms_in_checkpoint_10d_vocab": True,
        "all_ligand_atoms_in_checkpoint_10d_vocab": True,
        "audited_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "passed_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "failed_mask_level_count": 0,
        "all_checkpoint_compatible_batches_constructed_after_filter": True,
        "all_ligand_one_hot_row_sums_valid_after_filter": True,
        "all_pocket_one_hot_row_sums_valid_after_filter": True,
        "all_pocket_unknown_atom_count_zero_after_filter": True,
        "all_ligand_unknown_atom_count_zero_after_filter": True,
        "ligand_masks_unchanged_after_filter": True,
        "ligand_reactive_atom_region_preserved": True,
        "no_synthetic_fallback_used": True,
        "noncheckpoint_pocket_atom_filter_policy_recommended": True,
        "projection_filter_debug_passed": True,
        "real_covalent_feature_semantics_audit_debug_passed": True,
        "real_covalent_noncheckpoint_pocket_atom_filter_gate_allowed": True,
        "real_covalent_cuda_forward_backward_smoke_allowed": False,
        "real_covalent_single_optimizer_step_smoke_allowed": False,
        "recommended_next_step": STAGE.replace("_v0", ""),
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
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    for key, value in expected.items():
        _expect(manifest.get(key) == value, f"step12g_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(
        math.isclose(float(manifest.get("mg_min_distance_to_ligand", 0)), 4.454363822937012, rel_tol=0, abs_tol=1e-9),
        "step12g_mg_min_distance_invalid",
        blockers,
    )
    _expect(
        math.isclose(float(manifest.get("mg_max_distance_to_ligand", 0)), 4.893711090087891, rel_tol=0, abs_tol=1e-9),
        "step12g_mg_max_distance_invalid",
        blockers,
    )
    _expect(
        math.isclose(
            float(manifest.get("mg_mean_distance_to_ligand", 0)), 4.674037456512451, rel_tol=0, abs_tol=1e-9
        ),
        "step12g_mg_mean_distance_invalid",
        blockers,
    )
    reactive_distance = float(manifest.get("mg_min_distance_to_ligand_reactive_atom", 0))
    _expect(
        math.isclose(reactive_distance, 5.612326145172119, rel_tol=0, abs_tol=1e-9)
        and reactive_distance > LIGAND_REACTIVE_CONTACT_DISTANCE_A,
        "step12g_mg_reactive_distance_invalid",
        blockers,
    )
    row_types = [row.get("row_type") for row in rows]
    _expect(row_types.count("unknown_protein_atom") == 2, "step12g_unknown_row_count_invalid", blockers)
    _expect(row_types.count("sample_filter_projection") == 3, "step12g_sample_row_count_invalid", blockers)
    _expect(row_types.count("mask_level_filter_projection") == 5, "step12g_mask_row_count_invalid", blockers)
    mask_rows = [row for row in rows if row.get("row_type") == "mask_level_filter_projection"]
    _expect([row.get("mask_level") for row in mask_rows] == CANONICAL_MASK_LEVELS, "step12g_mask_order_invalid", blockers)
    for row in mask_rows:
        _expect(row.get("status") == "passed", f"step12g_mask_row_not_passed:{row.get('mask_level')}", blockers)
    summary = STEP12G_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "projection-level filter",
        "not an optimizer step",
        "recommended_next_step: real_covalent_noncheckpoint_pocket_atom_filter_gate",
    ]:
        _expect(snippet in summary, f"step12g_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def filter_noncheckpoint_vocab_pocket_atoms_v0(
    diffsbdd_like: dict[str, Any],
    mask_level: str,
    device: str = "cpu",
) -> dict[str, Any]:
    blockers: list[str] = []
    if mask_level not in CANONICAL_MASK_LEVELS:
        blockers.append(f"unsupported_mask_level:{mask_level}")
    ligand_atomic = diffsbdd_like["ligand_h"][diffsbdd_like["ligand_mask"].to(dtype=torch.bool)].to(dtype=torch.long)
    protein_atomic = diffsbdd_like["protein_h"][diffsbdd_like["protein_mask"].to(dtype=torch.bool)].to(dtype=torch.long)
    ligand_keep = _known_mask(ligand_atomic)
    pocket_keep = _known_mask(protein_atomic)
    ligand_unknown_count = int((~ligand_keep).sum().item())
    if ligand_unknown_count:
        blockers.append("ligand_unknown_atom_present")
    unknown_rows = _unknown_pocket_atom_rows(diffsbdd_like)
    for row in unknown_rows:
        if int(row["atomic_number"]) not in ALLOWED_FILTERED_ATOMIC_NUMBERS_FOR_THIS_GATE:
            blockers.append(f"filtered_atomic_number_not_allowed:{row['atomic_number']}")
        if bool(row["direct_ligand_contact_candidate"]):
            blockers.append(f"filtered_atom_direct_ligand_contact:{row['sample_id']}:{row['protein_atom_local_index']}")
        if bool(row["ligand_reactive_contact_candidate"]):
            blockers.append(f"filtered_atom_ligand_reactive_contact:{row['sample_id']}:{row['protein_atom_local_index']}")
        if bool(row["is_reactive_residue_atom"]):
            blockers.append(f"filtered_atom_is_reactive_residue_atom:{row['sample_id']}:{row['protein_atom_local_index']}")
    filtered_protein_atomic = protein_atomic[pocket_keep]
    ligand_one_hot, ligand_unknown = _one_hot_known_only(ligand_atomic)
    pocket_one_hot, pocket_unknown = _one_hot_known_only(filtered_protein_atomic)
    pocket_mask = diffsbdd_like["pocket_mask"].to(dtype=torch.long)
    removed_indices = (~pocket_keep).nonzero(as_tuple=False).view(-1)
    removed_per_sample = torch.bincount(
        pocket_mask[removed_indices].detach().cpu().to(dtype=torch.long),
        minlength=int(diffsbdd_like["batch_size"]),
    )
    filtered_num_pocket_nodes = (
        diffsbdd_like["num_pocket_nodes"].detach().cpu().to(dtype=torch.long) - removed_per_sample
    ).to(device=torch.device(device), dtype=torch.long)
    target_mask = diffsbdd_like["ligand_target_mask_flat"].to(device=torch.device(device), dtype=torch.bool)
    context_mask = diffsbdd_like["ligand_context_mask_flat"].to(device=torch.device(device), dtype=torch.bool)
    ligand_masks_unchanged = bool(
        torch.equal(target_mask.cpu(), diffsbdd_like["ligand_target_mask_flat"].detach().cpu())
        and torch.equal(context_mask.cpu(), diffsbdd_like["ligand_context_mask_flat"].detach().cpu())
        and torch.equal(
            diffsbdd_like["lig_fixed"].detach().cpu().view(-1).to(dtype=torch.bool),
            diffsbdd_like["fixed_ligand_atom_mask"][diffsbdd_like["ligand_mask"].to(dtype=torch.bool)]
            .detach()
            .cpu()
            .view(-1)
            .to(dtype=torch.bool),
        )
    )
    reactive_preserved = _reactive_region_preserved(diffsbdd_like, mask_level)
    data_batch = {
        "lig_coords": diffsbdd_like["lig_coords"].to(device=torch.device(device), dtype=torch.float32),
        "lig_one_hot": ligand_one_hot.to(device=torch.device(device)),
        "lig_mask": diffsbdd_like["lig_mask"].to(device=torch.device(device), dtype=torch.long),
        "pocket_coords": diffsbdd_like["pocket_coords"][pocket_keep].to(device=torch.device(device), dtype=torch.float32),
        "pocket_one_hot": pocket_one_hot.to(device=torch.device(device)),
        "pocket_mask": pocket_mask[pocket_keep].to(device=torch.device(device), dtype=torch.long),
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
    if not ligand_masks_unchanged:
        blockers.append("ligand_masks_changed_after_filter")
    if not reactive_preserved:
        blockers.append("ligand_reactive_atom_region_not_preserved")
    constructed = not blockers
    metadata = {
        "filter_policy_name": FILTER_POLICY_NAME,
        "mask_level": mask_level,
        "expected_reactive_atom_region": expected_reactive_atom_region_for_mask_level_v0(mask_level),
        "filtered_pocket_atom_count": len(unknown_rows),
        "filtered_pocket_atom_numbers": sorted({int(row["atomic_number"]) for row in unknown_rows}),
        "filtered_pocket_atom_symbols": sorted({_atom_symbol(int(row["atomic_number"])) for row in unknown_rows}),
        "filtered_pocket_atom_indices": [int(row["flat_pocket_atom_index"]) for row in unknown_rows],
        "filtered_pocket_atom_min_ligand_distances": [float(row["min_distance_to_any_ligand_atom"]) for row in unknown_rows],
        "filtered_pocket_atom_ligand_reactive_distances": [float(row["ligand_reactive_atom_distance"]) for row in unknown_rows],
        "filtered_atoms_direct_ligand_contact_detected": any(bool(row["direct_ligand_contact_candidate"]) for row in unknown_rows),
        "filtered_atoms_ligand_reactive_contact_detected": any(
            bool(row["ligand_reactive_contact_candidate"]) for row in unknown_rows
        ),
        "filtered_atoms_reactive_residue_contact_detected": any(bool(row["is_reactive_residue_atom"]) for row in unknown_rows),
        "ligand_unknown_atom_count": ligand_unknown_count,
        "pocket_unknown_atom_count_before_filter": len(unknown_rows),
        "pocket_unknown_atom_count_after_filter": int(pocket_unknown["unknown_atom_count"]),
        "all_remaining_pocket_atoms_in_checkpoint_10d_vocab": int(pocket_unknown["unknown_atom_count"]) == 0,
        "ligand_atoms_in_checkpoint_10d_vocab": ligand_unknown_count == 0,
        "ligand_feature_dim": int(data_batch["lig_one_hot"].shape[1]),
        "pocket_feature_dim": int(data_batch["pocket_one_hot"].shape[1]),
        "ligand_one_hot_rows_equal_ligand_coords_rows": ligand_rows_equal_coords,
        "pocket_one_hot_rows_equal_pocket_coords_rows": pocket_rows_equal_coords,
        "ligand_one_hot_row_sums_valid_after_filter": ligand_row_sums_valid,
        "pocket_one_hot_row_sums_valid_after_filter": pocket_row_sums_valid,
        "ligand_masks_unchanged_after_filter": ligand_masks_unchanged,
        "ligand_reactive_atom_region_preserved": reactive_preserved,
        "checkpoint_compatible_batch_constructed_after_filter": constructed,
        "no_synthetic_fallback_used": True,
        "production_filter_helper": True,
        "production_filter_helper_created": True,
        "original_data_modified": False,
        "production_adapter_modified": False,
        "blocking_reasons": sorted(set(blockers)),
    }
    return {
        "data_batch": data_batch,
        "target_mask": target_mask,
        "context_mask": context_mask,
        "metadata": metadata,
        "status": "passed" if constructed else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def _sample_filter_projection_rows_v0() -> dict[str, Any]:
    dataset = CovalentNPZDataset(SELECTED_REAL_SAMPLE_INDEX)
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    filtered_numbers: set[int] = set()
    total_removed = 0
    direct_contact = False
    reactive_contact = False
    pre_ligand_unknown_count = 0
    pre_pocket_unknown_count = 0
    for sample_index, sample in enumerate(dataset):
        ligand_atomic = sample["ligand_atomic_numbers"].detach().cpu().to(dtype=torch.long)
        protein_atomic = sample["protein_atomic_numbers"].detach().cpu().to(dtype=torch.long)
        ligand_known = _known_mask(ligand_atomic)
        protein_known = _known_mask(protein_atomic)
        removed_indices = (~protein_known).nonzero(as_tuple=False).view(-1).detach().cpu().to(dtype=torch.long).tolist()
        removed_numbers = [int(protein_atomic[index].item()) for index in removed_indices]
        removed_symbols = [_atom_symbol(number) for number in removed_numbers]
        removed_min_distances: list[float] = []
        removed_reactive_distances: list[float] = []
        ligand_coords = sample["ligand_atom_coords"].detach().cpu().to(dtype=torch.float32)
        protein_coords = sample["protein_atom_coords"].detach().cpu().to(dtype=torch.float32)
        reactive_index = int(sample["ligand_reactive_atom_index"].item())
        for index in removed_indices:
            coord = protein_coords[index]
            distances = torch.linalg.norm(ligand_coords - coord, dim=1)
            min_distance = float(distances.min().item())
            reactive_distance = float(torch.linalg.norm(ligand_coords[reactive_index] - coord).item())
            removed_min_distances.append(min_distance)
            removed_reactive_distances.append(reactive_distance)
            direct_contact = direct_contact or min_distance <= DIRECT_LIGAND_CONTACT_DISTANCE_A
            reactive_contact = reactive_contact or reactive_distance <= LIGAND_REACTIVE_CONTACT_DISTANCE_A
        row_blockers: list[str] = []
        ligand_unknown = int((~ligand_known).sum().item())
        pocket_unknown = int((~protein_known).sum().item())
        pre_ligand_unknown_count += ligand_unknown
        pre_pocket_unknown_count += pocket_unknown
        filtered_numbers.update(removed_numbers)
        total_removed += len(removed_indices)
        if ligand_unknown:
            row_blockers.append("ligand_unknown_atom_present")
        if any(number not in ALLOWED_FILTERED_ATOMIC_NUMBERS_FOR_THIS_GATE for number in removed_numbers):
            row_blockers.append("filtered_atomic_number_not_allowed")
        if any(distance <= DIRECT_LIGAND_CONTACT_DISTANCE_A for distance in removed_min_distances):
            row_blockers.append("filtered_atom_direct_ligand_contact")
        if any(distance <= LIGAND_REACTIVE_CONTACT_DISTANCE_A for distance in removed_reactive_distances):
            row_blockers.append("filtered_atom_ligand_reactive_contact")
        post_filter_pocket_unknown = int((~_known_mask(protein_atomic[protein_known])).sum().item())
        post_filter_ligand_unknown = ligand_unknown
        row = {
            "row_type": "sample_filter_projection",
            "sample_id": str(sample["sample_id"]),
            "sample_index": sample_index,
            "original_pocket_atom_count": int(protein_atomic.shape[0]),
            "filtered_pocket_atom_count": int(protein_known.sum().item()),
            "removed_pocket_atom_count": int(len(removed_indices)),
            "removed_pocket_atom_numbers": sorted(set(removed_numbers)),
            "removed_pocket_atom_symbols": sorted(set(removed_symbols)),
            "removed_pocket_atom_indices": removed_indices,
            "removed_pocket_atom_min_ligand_distances": removed_min_distances,
            "removed_pocket_atom_ligand_reactive_distances": removed_reactive_distances,
            "ligand_atom_count": int(ligand_atomic.shape[0]),
            "ligand_atom_count_changed": False,
            "post_filter_pocket_unknown_atom_count": post_filter_pocket_unknown,
            "post_filter_ligand_unknown_atom_count": post_filter_ligand_unknown,
            "all_remaining_pocket_atoms_in_checkpoint_10d_vocab": post_filter_pocket_unknown == 0,
            "all_ligand_atoms_in_checkpoint_10d_vocab": ligand_unknown == 0,
            "status": "passed" if not row_blockers else "blocked",
            "blocking_reasons": sorted(set(row_blockers)),
        }
        rows.append(row)
        blockers.extend(f"{row['sample_id']}:{reason}" for reason in row_blockers)
    return {
        "rows": rows,
        "sample_count": len(dataset),
        "sample_ids": [row["sample_id"] for row in rows],
        "pre_filter_ligand_unknown_atom_count": pre_ligand_unknown_count,
        "pre_filter_pocket_unknown_atom_count": pre_pocket_unknown_count,
        "pre_filter_unknown_pocket_atom_numbers": sorted(filtered_numbers),
        "pre_filter_unknown_pocket_atom_symbols": sorted({_atom_symbol(number) for number in filtered_numbers}),
        "total_filtered_pocket_atom_count": total_removed,
        "filtered_pocket_atom_numbers": sorted(filtered_numbers),
        "filtered_pocket_atom_symbols": sorted({_atom_symbol(number) for number in filtered_numbers}),
        "post_filter_ligand_unknown_atom_count": sum(int(row["post_filter_ligand_unknown_atom_count"]) for row in rows),
        "post_filter_pocket_unknown_atom_count": sum(int(row["post_filter_pocket_unknown_atom_count"]) for row in rows),
        "all_remaining_pocket_atoms_in_checkpoint_10d_vocab": all(
            bool(row["all_remaining_pocket_atoms_in_checkpoint_10d_vocab"]) for row in rows
        ),
        "all_ligand_atoms_in_checkpoint_10d_vocab": all(bool(row["all_ligand_atoms_in_checkpoint_10d_vocab"]) for row in rows),
        "filtered_atoms_direct_ligand_contact_detected": direct_contact,
        "filtered_atoms_ligand_reactive_contact_detected": reactive_contact,
        "status": "passed" if not blockers else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def run_noncheckpoint_pocket_atom_filter_gate_v0() -> dict[str, Any]:
    sample_projection = _sample_filter_projection_rows_v0()
    mask_rows: list[dict[str, Any]] = []
    blockers: list[str] = list(sample_projection["blocking_reasons"])
    for mask_level in CANONICAL_MASK_LEVELS:
        level_blockers: list[str] = []
        expected_region = expected_reactive_atom_region_for_mask_level_v0(mask_level)
        try:
            bundle = build_real_covalent_forward_loss_batch_bundle_v0(mask_level, "cpu")
            filtered = filter_noncheckpoint_vocab_pocket_atoms_v0(bundle["diffsbdd_like"], mask_level, "cpu")
            metadata = filtered["metadata"]
            level_blockers.extend(filtered.get("blocking_reasons", []))
            row = {
                "row_type": "mask_level_filtered_conversion",
                "mask_level": mask_level,
                "expected_reactive_atom_region": expected_region,
                "checkpoint_compatible_batch_constructed_after_filter": bool(
                    metadata["checkpoint_compatible_batch_constructed_after_filter"]
                ),
                "ligand_feature_dim": int(metadata["ligand_feature_dim"]),
                "pocket_feature_dim": int(metadata["pocket_feature_dim"]),
                "ligand_one_hot_row_sums_valid_after_filter": bool(
                    metadata["ligand_one_hot_row_sums_valid_after_filter"]
                ),
                "pocket_one_hot_row_sums_valid_after_filter": bool(
                    metadata["pocket_one_hot_row_sums_valid_after_filter"]
                ),
                "ligand_unknown_atom_count_after_filter": int(metadata["ligand_unknown_atom_count"]),
                "pocket_unknown_atom_count_after_filter": int(metadata["pocket_unknown_atom_count_after_filter"]),
                "filtered_pocket_atom_count": int(metadata["filtered_pocket_atom_count"]),
                "filtered_pocket_atom_numbers": metadata["filtered_pocket_atom_numbers"],
                "filtered_pocket_atom_symbols": metadata["filtered_pocket_atom_symbols"],
                "no_synthetic_fallback_used": bool(metadata["no_synthetic_fallback_used"]),
                "ligand_masks_unchanged_after_filter": bool(metadata["ligand_masks_unchanged_after_filter"]),
                "ligand_reactive_atom_region_preserved": bool(metadata["ligand_reactive_atom_region_preserved"]),
                "status": "passed" if not level_blockers else "blocked",
                "blocking_reasons": sorted(set(level_blockers)),
            }
        except Exception as exc:
            level_blockers.append(f"filtered_conversion_failed:{type(exc).__name__}:{exc}")
            row = {
                "row_type": "mask_level_filtered_conversion",
                "mask_level": mask_level,
                "expected_reactive_atom_region": expected_region,
                "checkpoint_compatible_batch_constructed_after_filter": False,
                "ligand_feature_dim": 0,
                "pocket_feature_dim": 0,
                "ligand_one_hot_row_sums_valid_after_filter": False,
                "pocket_one_hot_row_sums_valid_after_filter": False,
                "ligand_unknown_atom_count_after_filter": -1,
                "pocket_unknown_atom_count_after_filter": -1,
                "filtered_pocket_atom_count": -1,
                "filtered_pocket_atom_numbers": [],
                "filtered_pocket_atom_symbols": [],
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
        **{key: value for key, value in sample_projection.items() if key not in {"rows", "blocking_reasons", "status"}},
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
        "all_ligand_unknown_atom_count_zero_after_filter": all(
            int(row["ligand_unknown_atom_count_after_filter"]) == 0 for row in mask_rows
        ),
        "all_pocket_unknown_atom_count_zero_after_filter": all(
            int(row["pocket_unknown_atom_count_after_filter"]) == 0 for row in mask_rows
        ),
        "ligand_masks_unchanged_after_filter": all(bool(row["ligand_masks_unchanged_after_filter"]) for row in mask_rows),
        "ligand_reactive_atom_region_preserved": all(
            bool(row["ligand_reactive_atom_region_preserved"]) for row in mask_rows
        ),
        "no_synthetic_fallback_used": all(bool(row["no_synthetic_fallback_used"]) for row in mask_rows),
        "status": "passed" if not blockers else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def build_real_covalent_noncheckpoint_pocket_atom_filter_gate_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12g_validated = validate_step12g_filter_policy_debug_v0()
    except Exception as exc:
        step12g_validated = False
        blockers.append(f"step12g_validation_failed:{type(exc).__name__}:{exc}")
    try:
        step12b_validated = validate_step12b_validator_behavior_v0()
    except Exception as exc:
        step12b_validated = False
        blockers.append(f"step12b_validation_failed:{type(exc).__name__}:{exc}")
    filter_gate = run_noncheckpoint_pocket_atom_filter_gate_v0()
    production_adapter_modified = _adapter_diff_exists()
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    blockers.extend(filter_gate["blocking_reasons"])
    if production_adapter_modified:
        blockers.append("production_adapter_modified")
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    helper_validated = bool(
        filter_gate["passed_mask_level_count"] == len(CANONICAL_MASK_LEVELS)
        and filter_gate["all_checkpoint_compatible_batches_constructed_after_filter"]
        and filter_gate["all_ligand_one_hot_row_sums_valid_after_filter"]
        and filter_gate["all_pocket_one_hot_row_sums_valid_after_filter"]
        and filter_gate["all_ligand_unknown_atom_count_zero_after_filter"]
        and filter_gate["all_pocket_unknown_atom_count_zero_after_filter"]
        and filter_gate["ligand_masks_unchanged_after_filter"]
        and filter_gate["ligand_reactive_atom_region_preserved"]
        and filter_gate["no_synthetic_fallback_used"]
    )
    gate_passed = bool(step12g_validated and step12b_validated and helper_validated and not blockers)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12g_filter_policy_debug_validated": step12g_validated,
        "step12b_mask_level_aware_validator_validated": step12b_validated,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "checkpoint_10d_mapping_project": _mapping_as_jsonable(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX),
        "filter_policy_name": FILTER_POLICY_NAME,
        "allowed_filtered_atomic_numbers_for_this_gate": list(ALLOWED_FILTERED_ATOMIC_NUMBERS_FOR_THIS_GATE),
        "allowed_filtered_atom_symbols_for_this_gate": list(ALLOWED_FILTERED_ATOM_SYMBOLS_FOR_THIS_GATE),
        "direct_ligand_contact_distance_a": DIRECT_LIGAND_CONTACT_DISTANCE_A,
        "ligand_reactive_contact_distance_a": LIGAND_REACTIVE_CONTACT_DISTANCE_A,
        "sample_count": filter_gate["sample_count"],
        "sample_ids": filter_gate["sample_ids"],
        "pre_filter_ligand_unknown_atom_count": filter_gate["pre_filter_ligand_unknown_atom_count"],
        "pre_filter_pocket_unknown_atom_count": filter_gate["pre_filter_pocket_unknown_atom_count"],
        "pre_filter_unknown_pocket_atom_numbers": filter_gate["pre_filter_unknown_pocket_atom_numbers"],
        "pre_filter_unknown_pocket_atom_symbols": filter_gate["pre_filter_unknown_pocket_atom_symbols"],
        "total_filtered_pocket_atom_count": filter_gate["total_filtered_pocket_atom_count"],
        "filtered_pocket_atom_numbers": filter_gate["filtered_pocket_atom_numbers"],
        "filtered_pocket_atom_symbols": filter_gate["filtered_pocket_atom_symbols"],
        "post_filter_ligand_unknown_atom_count": filter_gate["post_filter_ligand_unknown_atom_count"],
        "post_filter_pocket_unknown_atom_count": filter_gate["post_filter_pocket_unknown_atom_count"],
        "all_remaining_pocket_atoms_in_checkpoint_10d_vocab": filter_gate[
            "all_remaining_pocket_atoms_in_checkpoint_10d_vocab"
        ],
        "all_ligand_atoms_in_checkpoint_10d_vocab": filter_gate["all_ligand_atoms_in_checkpoint_10d_vocab"],
        "filtered_atoms_direct_ligand_contact_detected": filter_gate["filtered_atoms_direct_ligand_contact_detected"],
        "filtered_atoms_ligand_reactive_contact_detected": filter_gate[
            "filtered_atoms_ligand_reactive_contact_detected"
        ],
        "production_filter_helper_created": True,
        "production_filter_helper_validated": helper_validated,
        "production_adapter_modified": production_adapter_modified,
        "original_data_modified": False,
        "audited_mask_level_count": filter_gate["audited_mask_level_count"],
        "passed_mask_level_count": filter_gate["passed_mask_level_count"],
        "failed_mask_level_count": filter_gate["failed_mask_level_count"],
        "all_checkpoint_compatible_batches_constructed_after_filter": filter_gate[
            "all_checkpoint_compatible_batches_constructed_after_filter"
        ],
        "all_ligand_one_hot_row_sums_valid_after_filter": filter_gate["all_ligand_one_hot_row_sums_valid_after_filter"],
        "all_pocket_one_hot_row_sums_valid_after_filter": filter_gate["all_pocket_one_hot_row_sums_valid_after_filter"],
        "all_ligand_unknown_atom_count_zero_after_filter": filter_gate["all_ligand_unknown_atom_count_zero_after_filter"],
        "all_pocket_unknown_atom_count_zero_after_filter": filter_gate["all_pocket_unknown_atom_count_zero_after_filter"],
        "ligand_masks_unchanged_after_filter": filter_gate["ligand_masks_unchanged_after_filter"],
        "ligand_reactive_atom_region_preserved": filter_gate["ligand_reactive_atom_region_preserved"],
        "no_synthetic_fallback_used": filter_gate["no_synthetic_fallback_used"],
        "non_cys_reactive_residue_support_status": NON_CYS_SUPPORT_STATUS,
        "reaction_family_template_audit_required_before_broad_covalent_training": True,
        "ligand_reconstruction_template_gate_required": True,
        "real_covalent_noncheckpoint_pocket_atom_filter_gate_passed": gate_passed,
        "real_covalent_filtered_feature_semantics_audit_allowed": gate_passed,
        "real_covalent_cuda_forward_backward_smoke_allowed": False,
        "real_covalent_single_optimizer_step_smoke_allowed": False,
        "recommended_next_step": "real_covalent_filtered_feature_semantics_audit"
        if gate_passed
        else "real_covalent_noncheckpoint_pocket_atom_filter_gate_debug",
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
        "all_checks_passed": gate_passed,
        "blocking_reasons": blockers,
    }
    filter_table_rows: list[dict[str, Any]] = [
        {
            "row_type": "step12g_precondition",
            "status": "passed" if step12g_validated and step12b_validated else "blocked",
            "step12g_filter_policy_debug_validated": step12g_validated,
            "step12b_mask_level_aware_validator_validated": step12b_validated,
            "blocking_reasons": [] if step12g_validated and step12b_validated else blockers,
        },
        {
            "row_type": "filter_policy_contract",
            "status": "passed",
            "filter_policy_name": FILTER_POLICY_NAME,
            "allowed_filtered_atomic_numbers_for_this_gate": ALLOWED_FILTERED_ATOMIC_NUMBERS_FOR_THIS_GATE,
            "allowed_filtered_atom_symbols_for_this_gate": ALLOWED_FILTERED_ATOM_SYMBOLS_FOR_THIS_GATE,
            "direct_ligand_contact_distance_a": DIRECT_LIGAND_CONTACT_DISTANCE_A,
            "ligand_reactive_contact_distance_a": LIGAND_REACTIVE_CONTACT_DISTANCE_A,
            "production_filter_helper_created": True,
            "production_adapter_modified": production_adapter_modified,
            "original_data_modified": False,
            "blocking_reasons": [],
        },
    ]
    filter_table_rows.extend(filter_gate["sample_rows"])
    filter_table_rows.extend(filter_gate["mask_rows"])
    filter_table_rows.append(
        {
            "row_type": "non_cys_reaction_scope_boundary",
            "status": "passed",
            "non_cys_reactive_residue_support_status": NON_CYS_SUPPORT_STATUS,
            "reaction_family_template_audit_required_before_broad_covalent_training": True,
            "ligand_reconstruction_template_gate_required": True,
            "blocking_reasons": [],
        }
    )
    filter_table_rows.append(
        {
            "row_type": "decision",
            "status": "passed" if gate_passed else "blocked",
            "real_covalent_noncheckpoint_pocket_atom_filter_gate_passed": gate_passed,
            "real_covalent_filtered_feature_semantics_audit_allowed": gate_passed,
            "real_covalent_single_optimizer_step_smoke_allowed": False,
            "recommended_next_step": manifest["recommended_next_step"],
            "blocking_reasons": blockers,
        }
    )
    return {
        "manifest": manifest,
        "filter_table_rows": filter_table_rows,
        "report_sections": {
            "step12g_precondition": {
                "step12g_filter_policy_debug_validated": step12g_validated,
                "step12b_mask_level_aware_validator_validated": step12b_validated,
            },
            "filter_policy_contract": {
                "filter_policy_name": FILTER_POLICY_NAME,
                "allowed_filtered_atomic_numbers_for_this_gate": ALLOWED_FILTERED_ATOMIC_NUMBERS_FOR_THIS_GATE,
                "production_filter_helper_created": True,
            },
            "sample_filter_projection": {
                "sample_count": filter_gate["sample_count"],
                "total_filtered_pocket_atom_count": filter_gate["total_filtered_pocket_atom_count"],
                "post_filter_pocket_unknown_atom_count": filter_gate["post_filter_pocket_unknown_atom_count"],
            },
            "mask_level_filtered_conversion": {
                "audited_mask_level_count": filter_gate["audited_mask_level_count"],
                "passed_mask_level_count": filter_gate["passed_mask_level_count"],
                "all_pocket_one_hot_row_sums_valid_after_filter": filter_gate[
                    "all_pocket_one_hot_row_sums_valid_after_filter"
                ],
            },
            "ligand_integrity": {
                "all_ligand_atoms_in_checkpoint_10d_vocab": filter_gate["all_ligand_atoms_in_checkpoint_10d_vocab"],
                "ligand_masks_unchanged_after_filter": filter_gate["ligand_masks_unchanged_after_filter"],
                "ligand_reactive_atom_region_preserved": filter_gate["ligand_reactive_atom_region_preserved"],
            },
            "non_cys_reaction_scope_boundary": {
                "non_cys_reactive_residue_support_status": NON_CYS_SUPPORT_STATUS,
                "reaction_family_template_audit_required_before_broad_covalent_training": True,
                "ligand_reconstruction_template_gate_required": True,
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
                "production_adapter_modified": production_adapter_modified,
                "original_diffsbdd_source_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
            "next_step_decision": {
                "real_covalent_noncheckpoint_pocket_atom_filter_gate_passed": gate_passed,
                "real_covalent_filtered_feature_semantics_audit_allowed": gate_passed,
                "recommended_next_step": manifest["recommended_next_step"],
            },
        },
    }
