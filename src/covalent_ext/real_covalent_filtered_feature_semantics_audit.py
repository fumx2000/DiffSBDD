from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import torch

from covalent_ext.model_input_adapter import expected_reactive_atom_region_for_mask_level_v0
from covalent_ext.npz_dataset import CovalentNPZDataset
from covalent_ext.real_covalent_feature_semantics_audit import (
    CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX,
    audit_checkpoint_feature_contract_v0,
)
from covalent_ext.real_covalent_noncheckpoint_pocket_atom_filter_gate import (
    ALLOWED_FILTERED_ATOM_SYMBOLS_FOR_THIS_GATE,
    ALLOWED_FILTERED_ATOMIC_NUMBERS_FOR_THIS_GATE,
    DIRECT_LIGAND_CONTACT_DISTANCE_A,
    FILTER_POLICY_NAME,
    FILTER_TABLE_CSV as STEP12H_FILTER_TABLE_CSV,
    LIGAND_REACTIVE_CONTACT_DISTANCE_A,
    MANIFEST_JSON as STEP12H_MANIFEST_JSON,
    SUMMARY_MD as STEP12H_SUMMARY_MD,
    filter_noncheckpoint_vocab_pocket_atoms_v0,
    validate_step12b_validator_behavior_v0,
)
from covalent_ext.real_covalent_pretrained_forward_loss_smoke import (
    CANONICAL_MASK_LEVELS,
    CHECKPOINT_PATH,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    INPUT_SOURCE,
    PROTECTED_SOURCE_PATHS,
    SELECTED_REAL_SAMPLE_INDEX,
    UNKNOWN_ATOM_FEATURE_POLICY,
    build_real_covalent_forward_loss_batch_bundle_v0,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_filtered_feature_semantics_audit_v0"
PREVIOUS_STAGE = "real_covalent_noncheckpoint_pocket_atom_filter_gate_v0"

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_filtered_feature_semantics_audit_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_filtered_feature_semantics_audit_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_filtered_feature_semantics_audit_manifest.json"
AUDIT_TABLE_CSV = OUTPUT_ROOT / "real_covalent_filtered_feature_semantics_audit_table.csv"
SUMMARY_MD = Path("docs/real_covalent_filtered_feature_semantics_audit_v0_summary.md")

NON_CYS_SUPPORT_STATUS = "schema_supported_but_template_audit_pending"
NON_CYS_DATA_BULK_CLEANING_POLICY = "identify_classify_defer_until_template_gate"
TRAIN_READY_SCOPE_V1 = "cys_with_known_reconstruction_template_only"

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


def _mapping_as_jsonable(mapping: dict[int, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in sorted(mapping.items())}


def _symbol_counts(counter: Counter[int]) -> dict[str, int]:
    return {ATOMIC_NUMBER_TO_SYMBOL.get(int(key), f"Z{int(key)}"): int(value) for key, value in sorted(counter.items())}


def _atom_symbol(atomic_number: int) -> str:
    return ATOMIC_NUMBER_TO_SYMBOL.get(int(atomic_number), f"Z{int(atomic_number)}")


def _known_mask(values: torch.Tensor) -> torch.Tensor:
    vocab = set(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX)
    known = [int(value) in vocab for value in values.detach().cpu().to(dtype=torch.long).view(-1).tolist()]
    return torch.tensor(known, dtype=torch.bool)


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


def validate_step12h_filter_gate_v0() -> bool:
    if not STEP12H_MANIFEST_JSON.is_file() or not STEP12H_FILTER_TABLE_CSV.is_file() or not STEP12H_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12H outputs are missing")
    manifest = _load_json(STEP12H_MANIFEST_JSON)
    rows = _read_csv(STEP12H_FILTER_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_feature_semantics_audit_debug_v0",
        "step12g_filter_policy_debug_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "filter_policy_name": FILTER_POLICY_NAME,
        "allowed_filtered_atomic_numbers_for_this_gate": [12],
        "allowed_filtered_atom_symbols_for_this_gate": ["Mg"],
        "pre_filter_ligand_unknown_atom_count": 0,
        "pre_filter_pocket_unknown_atom_count": 2,
        "pre_filter_unknown_pocket_atom_numbers": [12],
        "pre_filter_unknown_pocket_atom_symbols": ["Mg"],
        "total_filtered_pocket_atom_count": 2,
        "filtered_pocket_atom_numbers": [12],
        "filtered_pocket_atom_symbols": ["Mg"],
        "filtered_atoms_direct_ligand_contact_detected": False,
        "filtered_atoms_ligand_reactive_contact_detected": False,
        "post_filter_ligand_unknown_atom_count": 0,
        "post_filter_pocket_unknown_atom_count": 0,
        "all_remaining_pocket_atoms_in_checkpoint_10d_vocab": True,
        "all_ligand_atoms_in_checkpoint_10d_vocab": True,
        "production_filter_helper_created": True,
        "production_filter_helper_validated": True,
        "production_adapter_modified": False,
        "original_data_modified": False,
        "audited_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "passed_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "failed_mask_level_count": 0,
        "all_checkpoint_compatible_batches_constructed_after_filter": True,
        "all_ligand_one_hot_row_sums_valid_after_filter": True,
        "all_pocket_one_hot_row_sums_valid_after_filter": True,
        "all_ligand_unknown_atom_count_zero_after_filter": True,
        "all_pocket_unknown_atom_count_zero_after_filter": True,
        "ligand_masks_unchanged_after_filter": True,
        "ligand_reactive_atom_region_preserved": True,
        "no_synthetic_fallback_used": True,
        "non_cys_reactive_residue_support_status": NON_CYS_SUPPORT_STATUS,
        "reaction_family_template_audit_required_before_broad_covalent_training": True,
        "ligand_reconstruction_template_gate_required": True,
        "real_covalent_noncheckpoint_pocket_atom_filter_gate_passed": True,
        "real_covalent_filtered_feature_semantics_audit_allowed": True,
        "real_covalent_cuda_forward_backward_smoke_allowed": False,
        "real_covalent_single_optimizer_step_smoke_allowed": False,
        "recommended_next_step": "real_covalent_filtered_feature_semantics_audit",
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
        _expect(manifest.get(key) == value, f"step12h_{key}_invalid:{manifest.get(key)!r}", blockers)
    row_types = [row.get("row_type") for row in rows]
    _expect(row_types.count("sample_filter_projection") == 3, "step12h_sample_projection_row_count_invalid", blockers)
    _expect(
        row_types.count("mask_level_filtered_conversion") == len(CANONICAL_MASK_LEVELS),
        "step12h_mask_conversion_row_count_invalid",
        blockers,
    )
    mask_rows = [row for row in rows if row.get("row_type") == "mask_level_filtered_conversion"]
    _expect([row.get("mask_level") for row in mask_rows] == CANONICAL_MASK_LEVELS, "step12h_mask_order_invalid", blockers)
    for row in mask_rows:
        _expect(row.get("status") == "passed", f"step12h_mask_row_not_passed:{row.get('mask_level')}", blockers)
        _expect(_text_bool(row.get("no_synthetic_fallback_used")), f"step12h_synthetic_fallback:{row.get('mask_level')}", blockers)
    summary = STEP12H_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "projection-level filter policy",
        "Original data is unchanged",
        "not optimizer step",
        "template audit is pending",
        "recommended_next_step: real_covalent_filtered_feature_semantics_audit",
    ]:
        _expect(snippet in summary, f"step12h_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def audit_filtered_checkpoint_feature_contract_v0() -> dict[str, Any]:
    return audit_checkpoint_feature_contract_v0()


def audit_filtered_real_covalent_atom_vocabulary_v0() -> dict[str, Any]:
    dataset = CovalentNPZDataset(SELECTED_REAL_SAMPLE_INDEX)
    blockers: list[str] = []
    sample_ids: list[str] = []
    ligand_counts: Counter[int] = Counter()
    pocket_counts_before: Counter[int] = Counter()
    pocket_counts_after: Counter[int] = Counter()
    filtered_numbers: list[int] = []
    filtered_symbols: list[str] = []
    direct_contact = False
    reactive_contact = False
    ligand_atom_count_total = 0
    pocket_atom_count_total_before = 0
    pocket_atom_count_total_after = 0
    for sample in dataset:
        sample_ids.append(str(sample["sample_id"]))
        ligand_atomic = sample["ligand_atomic_numbers"].detach().cpu().to(dtype=torch.long)
        pocket_atomic = sample["protein_atomic_numbers"].detach().cpu().to(dtype=torch.long)
        ligand_coords = sample["ligand_atom_coords"].detach().cpu().to(dtype=torch.float32)
        pocket_coords = sample["protein_atom_coords"].detach().cpu().to(dtype=torch.float32)
        reactive_index = int(sample["ligand_reactive_atom_index"].item())
        ligand_known = _known_mask(ligand_atomic)
        pocket_known = _known_mask(pocket_atomic)
        ligand_counts.update(int(value) for value in ligand_atomic.tolist())
        pocket_counts_before.update(int(value) for value in pocket_atomic.tolist())
        pocket_counts_after.update(int(value) for value in pocket_atomic[pocket_known].tolist())
        ligand_atom_count_total += int(ligand_atomic.shape[0])
        pocket_atom_count_total_before += int(pocket_atomic.shape[0])
        pocket_atom_count_total_after += int(pocket_known.sum().item())
        if int((~ligand_known).sum().item()):
            blockers.append(f"ligand_unknown_atom_present:{sample['sample_id']}")
        removed_indices = (~pocket_known).nonzero(as_tuple=False).view(-1).tolist()
        for index in removed_indices:
            atomic_number = int(pocket_atomic[index].item())
            filtered_numbers.append(atomic_number)
            filtered_symbols.append(_atom_symbol(atomic_number))
            if atomic_number not in ALLOWED_FILTERED_ATOMIC_NUMBERS_FOR_THIS_GATE:
                blockers.append(f"filtered_atomic_number_not_allowed:{atomic_number}")
            coord = pocket_coords[index]
            distances = torch.linalg.norm(ligand_coords - coord, dim=1)
            min_distance = float(distances.min().item())
            reactive_distance = float(torch.linalg.norm(ligand_coords[reactive_index] - coord).item())
            direct_contact = direct_contact or min_distance <= DIRECT_LIGAND_CONTACT_DISTANCE_A
            reactive_contact = reactive_contact or reactive_distance <= LIGAND_REACTIVE_CONTACT_DISTANCE_A
    vocab = set(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX)
    ligand_unique = sorted(ligand_counts)
    pocket_unique_before = sorted(pocket_counts_before)
    pocket_unique_after = sorted(pocket_counts_after)
    ligand_unknown_before = [value for value in ligand_unique if value not in vocab]
    pocket_unknown_before = [value for value in pocket_unique_before if value not in vocab]
    ligand_unknown_after = ligand_unknown_before
    pocket_unknown_after = [value for value in pocket_unique_after if value not in vocab]
    ligand_unknown_count_before = sum(ligand_counts[value] for value in ligand_unknown_before)
    pocket_unknown_count_before = sum(pocket_counts_before[value] for value in pocket_unknown_before)
    ligand_unknown_count_after = ligand_unknown_count_before
    pocket_unknown_count_after = sum(pocket_counts_after[value] for value in pocket_unknown_after)
    if direct_contact:
        blockers.append("filtered_atoms_direct_ligand_contact_detected")
    if reactive_contact:
        blockers.append("filtered_atoms_ligand_reactive_contact_detected")
    if pocket_unknown_count_after:
        blockers.append("post_filter_pocket_unknown_atoms_present")
    return {
        "sample_count": len(dataset),
        "sample_ids": sample_ids,
        "ligand_atom_count_total": ligand_atom_count_total,
        "pocket_atom_count_total_before_filter": pocket_atom_count_total_before,
        "pocket_atom_count_total_after_filter": pocket_atom_count_total_after,
        "ligand_atomic_numbers_unique": ligand_unique,
        "pocket_atomic_numbers_unique_before_filter": pocket_unique_before,
        "pocket_atomic_numbers_unique_after_filter": pocket_unique_after,
        "ligand_atom_symbol_counts": _symbol_counts(ligand_counts),
        "pocket_atom_symbol_counts_before_filter": _symbol_counts(pocket_counts_before),
        "pocket_atom_symbol_counts_after_filter": _symbol_counts(pocket_counts_after),
        "ligand_unknown_atom_numbers_before_filter": ligand_unknown_before,
        "pocket_unknown_atom_numbers_before_filter": pocket_unknown_before,
        "ligand_unknown_atom_count_before_filter": int(ligand_unknown_count_before),
        "pocket_unknown_atom_count_before_filter": int(pocket_unknown_count_before),
        "filtered_pocket_atom_count": int(len(filtered_numbers)),
        "filtered_pocket_atom_numbers": sorted(set(filtered_numbers)),
        "filtered_pocket_atom_symbols": sorted(set(filtered_symbols)),
        "filtered_atoms_direct_ligand_contact_detected": direct_contact,
        "filtered_atoms_ligand_reactive_contact_detected": reactive_contact,
        "ligand_unknown_atom_numbers_after_filter": ligand_unknown_after,
        "pocket_unknown_atom_numbers_after_filter": pocket_unknown_after,
        "ligand_unknown_atom_count_after_filter": int(ligand_unknown_count_after),
        "pocket_unknown_atom_count_after_filter": int(pocket_unknown_count_after),
        "all_ligand_atoms_in_checkpoint_10d_vocab_after_filter": ligand_unknown_count_after == 0,
        "all_pocket_atoms_in_checkpoint_10d_vocab_after_filter": pocket_unknown_count_after == 0,
        "unknown_atom_policy_name": UNKNOWN_ATOM_FEATURE_POLICY,
        "unknown_atom_policy_triggered_before_filter": ligand_unknown_count_before > 0 or pocket_unknown_count_before > 0,
        "unknown_atom_policy_triggered_after_filter": ligand_unknown_count_after > 0 or pocket_unknown_count_after > 0,
        "zero_vector_unknown_atom_policy_safe_after_filter": ligand_unknown_count_after == 0
        and pocket_unknown_count_after == 0,
        "status": "passed" if not blockers else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def audit_filtered_checkpoint_compatible_conversion_semantics_v0() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for mask_level in CANONICAL_MASK_LEVELS:
        level_blockers: list[str] = []
        expected_region = expected_reactive_atom_region_for_mask_level_v0(mask_level)
        try:
            bundle = build_real_covalent_forward_loss_batch_bundle_v0(mask_level, "cpu")
            filtered = filter_noncheckpoint_vocab_pocket_atoms_v0(bundle["diffsbdd_like"], mask_level, "cpu")
            metadata = filtered["metadata"]
            data_batch = filtered["data_batch"]
            ligand_rows_equal = int(data_batch["lig_one_hot"].shape[0]) == int(data_batch["lig_coords"].shape[0])
            pocket_rows_equal = int(data_batch["pocket_one_hot"].shape[0]) == int(data_batch["pocket_coords"].shape[0])
            if filtered["status"] != "passed":
                level_blockers.extend(filtered.get("blocking_reasons", []))
            if metadata["expected_reactive_atom_region"] != expected_region:
                level_blockers.append("expected_reactive_atom_region_invalid")
            if not bool(metadata["checkpoint_compatible_batch_constructed_after_filter"]):
                level_blockers.append("checkpoint_compatible_batch_not_constructed_after_filter")
            if int(metadata["ligand_feature_dim"]) != 10:
                level_blockers.append("ligand_feature_dim_not_10")
            if int(metadata["pocket_feature_dim"]) != 10:
                level_blockers.append("pocket_feature_dim_not_10")
            if not bool(metadata["ligand_one_hot_row_sums_valid_after_filter"]):
                level_blockers.append("ligand_one_hot_row_sums_invalid_after_filter")
            if not bool(metadata["pocket_one_hot_row_sums_valid_after_filter"]):
                level_blockers.append("pocket_one_hot_row_sums_invalid_after_filter")
            if int(metadata["ligand_unknown_atom_count"]) != 0:
                level_blockers.append("ligand_unknown_atom_count_nonzero_after_filter")
            if int(metadata["pocket_unknown_atom_count_after_filter"]) != 0:
                level_blockers.append("pocket_unknown_atom_count_nonzero_after_filter")
            if not bool(metadata["ligand_masks_unchanged_after_filter"]):
                level_blockers.append("ligand_masks_changed_after_filter")
            if not bool(metadata["ligand_reactive_atom_region_preserved"]):
                level_blockers.append("ligand_reactive_atom_region_not_preserved")
            row = {
                "row_type": "mask_level_filtered_conversion",
                "mask_level": mask_level,
                "expected_reactive_atom_region": expected_region,
                "checkpoint_compatible_batch_constructed_after_filter": bool(
                    metadata["checkpoint_compatible_batch_constructed_after_filter"]
                ),
                "ligand_feature_dim": int(metadata["ligand_feature_dim"]),
                "pocket_feature_dim": int(metadata["pocket_feature_dim"]),
                "ligand_one_hot_rows_equal_ligand_coords_rows": ligand_rows_equal,
                "pocket_one_hot_rows_equal_pocket_coords_rows": pocket_rows_equal,
                "ligand_one_hot_row_sums_valid_after_filter": bool(
                    metadata["ligand_one_hot_row_sums_valid_after_filter"]
                ),
                "pocket_one_hot_row_sums_valid_after_filter": bool(
                    metadata["pocket_one_hot_row_sums_valid_after_filter"]
                ),
                "ligand_unknown_atom_count_after_filter": int(metadata["ligand_unknown_atom_count"]),
                "pocket_unknown_atom_count_after_filter": int(metadata["pocket_unknown_atom_count_after_filter"]),
                "all_ligand_unknown_atom_count_zero_after_filter": int(metadata["ligand_unknown_atom_count"]) == 0,
                "all_pocket_unknown_atom_count_zero_after_filter": int(
                    metadata["pocket_unknown_atom_count_after_filter"]
                )
                == 0,
                "filtered_pocket_atom_count": int(metadata["filtered_pocket_atom_count"]),
                "filtered_pocket_atom_numbers": metadata["filtered_pocket_atom_numbers"],
                "filtered_pocket_atom_symbols": metadata["filtered_pocket_atom_symbols"],
                "ligand_masks_unchanged_after_filter": bool(metadata["ligand_masks_unchanged_after_filter"]),
                "ligand_reactive_atom_region_preserved": bool(metadata["ligand_reactive_atom_region_preserved"]),
                "no_synthetic_fallback_used": bool(metadata["no_synthetic_fallback_used"]),
                "production_filter_helper_used": bool(metadata["production_filter_helper"]),
                "production_adapter_modified": bool(metadata["production_adapter_modified"]),
                "original_data_modified": bool(metadata["original_data_modified"]),
                "status": "passed" if not level_blockers else "blocked",
                "blocking_reasons": sorted(set(level_blockers)),
            }
        except Exception as exc:
            level_blockers.append(f"filtered_conversion_audit_failed:{type(exc).__name__}:{exc}")
            row = {
                "row_type": "mask_level_filtered_conversion",
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
                "all_ligand_unknown_atom_count_zero_after_filter": False,
                "all_pocket_unknown_atom_count_zero_after_filter": False,
                "filtered_pocket_atom_count": -1,
                "filtered_pocket_atom_numbers": [],
                "filtered_pocket_atom_symbols": [],
                "ligand_masks_unchanged_after_filter": False,
                "ligand_reactive_atom_region_preserved": False,
                "no_synthetic_fallback_used": False,
                "production_filter_helper_used": False,
                "production_adapter_modified": False,
                "original_data_modified": False,
                "status": "blocked",
                "blocking_reasons": sorted(set(level_blockers)),
            }
        rows.append(row)
        blockers.extend(f"{mask_level}:{reason}" for reason in row["blocking_reasons"])
    return {
        "rows": rows,
        "audited_mask_level_count": len(rows),
        "passed_mask_level_count": sum(1 for row in rows if row["status"] == "passed"),
        "failed_mask_level_count": sum(1 for row in rows if row["status"] != "passed"),
        "all_checkpoint_compatible_batches_constructed_after_filter": all(
            row["checkpoint_compatible_batch_constructed_after_filter"] for row in rows
        ),
        "all_ligand_one_hot_row_sums_valid_after_filter": all(
            row["ligand_one_hot_row_sums_valid_after_filter"] for row in rows
        ),
        "all_pocket_one_hot_row_sums_valid_after_filter": all(
            row["pocket_one_hot_row_sums_valid_after_filter"] for row in rows
        ),
        "all_ligand_unknown_atom_count_zero_after_filter": all(
            row["all_ligand_unknown_atom_count_zero_after_filter"] for row in rows
        ),
        "all_pocket_unknown_atom_count_zero_after_filter": all(
            row["all_pocket_unknown_atom_count_zero_after_filter"] for row in rows
        ),
        "ligand_masks_unchanged_after_filter": all(row["ligand_masks_unchanged_after_filter"] for row in rows),
        "ligand_reactive_atom_region_preserved": all(row["ligand_reactive_atom_region_preserved"] for row in rows),
        "no_synthetic_fallback_used": all(row["no_synthetic_fallback_used"] for row in rows),
        "production_filter_helper_used": all(row["production_filter_helper_used"] for row in rows),
        "production_adapter_modified": any(row["production_adapter_modified"] for row in rows),
        "original_data_modified": any(row["original_data_modified"] for row in rows),
        "status": "passed" if not blockers else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def build_real_covalent_filtered_feature_semantics_audit_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12h_validated = validate_step12h_filter_gate_v0()
    except Exception as exc:
        step12h_validated = False
        blockers.append(f"step12h_validation_failed:{type(exc).__name__}:{exc}")
    try:
        step12b_validated = validate_step12b_validator_behavior_v0()
    except Exception as exc:
        step12b_validated = False
        blockers.append(f"step12b_validation_failed:{type(exc).__name__}:{exc}")

    checkpoint_contract = audit_filtered_checkpoint_feature_contract_v0()
    filtered_vocab = audit_filtered_real_covalent_atom_vocabulary_v0()
    conversion = audit_filtered_checkpoint_compatible_conversion_semantics_v0()
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    blockers.extend(checkpoint_contract.get("blocking_reasons", []))
    blockers.extend(filtered_vocab.get("blocking_reasons", []))
    blockers.extend(conversion.get("blocking_reasons", []))
    if conversion["production_adapter_modified"]:
        blockers.append("production_adapter_modified")
    if conversion["original_data_modified"]:
        blockers.append("original_data_modified")
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))

    dimension_contract_passed_after_filter = bool(
        checkpoint_contract["ligand_feature_dim_is_10"]
        and checkpoint_contract["pocket_feature_dim_is_10"]
        and checkpoint_contract["checkpoint_10d_feature_contract_detected"]
        and conversion["all_checkpoint_compatible_batches_constructed_after_filter"]
        and conversion["all_ligand_one_hot_row_sums_valid_after_filter"]
        and conversion["all_pocket_one_hot_row_sums_valid_after_filter"]
    )
    mapping_confirmed = bool(
        checkpoint_contract["checkpoint_feature_semantics_directly_encoded"]
        and checkpoint_contract["checkpoint_10d_mapping_matches_project_mapping"]
    )
    hard_pass = bool(
        step12h_validated
        and step12b_validated
        and dimension_contract_passed_after_filter
        and mapping_confirmed
        and filtered_vocab["all_ligand_atoms_in_checkpoint_10d_vocab_after_filter"]
        and filtered_vocab["all_pocket_atoms_in_checkpoint_10d_vocab_after_filter"]
        and not filtered_vocab["unknown_atom_policy_triggered_after_filter"]
        and filtered_vocab["zero_vector_unknown_atom_policy_safe_after_filter"]
        and conversion["audited_mask_level_count"] == len(CANONICAL_MASK_LEVELS)
        and conversion["passed_mask_level_count"] == len(CANONICAL_MASK_LEVELS)
        and conversion["all_ligand_unknown_atom_count_zero_after_filter"]
        and conversion["all_pocket_unknown_atom_count_zero_after_filter"]
        and conversion["ligand_masks_unchanged_after_filter"]
        and conversion["ligand_reactive_atom_region_preserved"]
        and conversion["no_synthetic_fallback_used"]
        and conversion["production_filter_helper_used"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12h_filter_gate_validated": step12h_validated,
        "step12b_mask_level_aware_validator_validated": step12b_validated,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "checkpoint_ligand_feature_dim": checkpoint_contract["checkpoint_ligand_feature_dim"],
        "checkpoint_pocket_feature_dim": checkpoint_contract["checkpoint_pocket_feature_dim"],
        "ligand_feature_dim_is_10": checkpoint_contract["ligand_feature_dim_is_10"],
        "pocket_feature_dim_is_10": checkpoint_contract["pocket_feature_dim_is_10"],
        "checkpoint_10d_feature_contract_detected": checkpoint_contract["checkpoint_10d_feature_contract_detected"],
        "checkpoint_feature_semantics_source": checkpoint_contract["checkpoint_feature_semantics_source"],
        "checkpoint_feature_semantics_directly_encoded": checkpoint_contract[
            "checkpoint_feature_semantics_directly_encoded"
        ],
        "checkpoint_10d_mapping_project": checkpoint_contract["checkpoint_10d_mapping_project"],
        "checkpoint_10d_index_to_atom_symbol": checkpoint_contract["checkpoint_10d_index_to_atom_symbol"],
        "checkpoint_10d_mapping_matches_project_mapping": checkpoint_contract[
            "checkpoint_10d_mapping_matches_project_mapping"
        ],
        "filter_policy_name": FILTER_POLICY_NAME,
        "allowed_filtered_atomic_numbers_for_this_gate": list(ALLOWED_FILTERED_ATOMIC_NUMBERS_FOR_THIS_GATE),
        "allowed_filtered_atom_symbols_for_this_gate": list(ALLOWED_FILTERED_ATOM_SYMBOLS_FOR_THIS_GATE),
        "production_filter_helper_used": conversion["production_filter_helper_used"],
        "production_adapter_modified": conversion["production_adapter_modified"],
        "original_data_modified": conversion["original_data_modified"],
        "sample_count": filtered_vocab["sample_count"],
        "sample_ids": filtered_vocab["sample_ids"],
        "ligand_atom_count_total": filtered_vocab["ligand_atom_count_total"],
        "pocket_atom_count_total_before_filter": filtered_vocab["pocket_atom_count_total_before_filter"],
        "pocket_atom_count_total_after_filter": filtered_vocab["pocket_atom_count_total_after_filter"],
        "ligand_atomic_numbers_unique": filtered_vocab["ligand_atomic_numbers_unique"],
        "pocket_atomic_numbers_unique_before_filter": filtered_vocab["pocket_atomic_numbers_unique_before_filter"],
        "pocket_atomic_numbers_unique_after_filter": filtered_vocab["pocket_atomic_numbers_unique_after_filter"],
        "ligand_atom_symbol_counts": filtered_vocab["ligand_atom_symbol_counts"],
        "pocket_atom_symbol_counts_before_filter": filtered_vocab["pocket_atom_symbol_counts_before_filter"],
        "pocket_atom_symbol_counts_after_filter": filtered_vocab["pocket_atom_symbol_counts_after_filter"],
        "ligand_unknown_atom_numbers_before_filter": filtered_vocab["ligand_unknown_atom_numbers_before_filter"],
        "pocket_unknown_atom_numbers_before_filter": filtered_vocab["pocket_unknown_atom_numbers_before_filter"],
        "ligand_unknown_atom_count_before_filter": filtered_vocab["ligand_unknown_atom_count_before_filter"],
        "pocket_unknown_atom_count_before_filter": filtered_vocab["pocket_unknown_atom_count_before_filter"],
        "filtered_pocket_atom_count": filtered_vocab["filtered_pocket_atom_count"],
        "filtered_pocket_atom_numbers": filtered_vocab["filtered_pocket_atom_numbers"],
        "filtered_pocket_atom_symbols": filtered_vocab["filtered_pocket_atom_symbols"],
        "filtered_atoms_direct_ligand_contact_detected": filtered_vocab[
            "filtered_atoms_direct_ligand_contact_detected"
        ],
        "filtered_atoms_ligand_reactive_contact_detected": filtered_vocab[
            "filtered_atoms_ligand_reactive_contact_detected"
        ],
        "ligand_unknown_atom_numbers_after_filter": filtered_vocab["ligand_unknown_atom_numbers_after_filter"],
        "pocket_unknown_atom_numbers_after_filter": filtered_vocab["pocket_unknown_atom_numbers_after_filter"],
        "ligand_unknown_atom_count_after_filter": filtered_vocab["ligand_unknown_atom_count_after_filter"],
        "pocket_unknown_atom_count_after_filter": filtered_vocab["pocket_unknown_atom_count_after_filter"],
        "all_ligand_atoms_in_checkpoint_10d_vocab_after_filter": filtered_vocab[
            "all_ligand_atoms_in_checkpoint_10d_vocab_after_filter"
        ],
        "all_pocket_atoms_in_checkpoint_10d_vocab_after_filter": filtered_vocab[
            "all_pocket_atoms_in_checkpoint_10d_vocab_after_filter"
        ],
        "unknown_atom_policy_name": filtered_vocab["unknown_atom_policy_name"],
        "unknown_atom_policy_triggered_before_filter": filtered_vocab["unknown_atom_policy_triggered_before_filter"],
        "unknown_atom_policy_triggered_after_filter": filtered_vocab["unknown_atom_policy_triggered_after_filter"],
        "zero_vector_unknown_atom_policy_safe_after_filter": filtered_vocab[
            "zero_vector_unknown_atom_policy_safe_after_filter"
        ],
        "canonical_mask_levels": list(CANONICAL_MASK_LEVELS),
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "audited_mask_level_count": conversion["audited_mask_level_count"],
        "passed_mask_level_count": conversion["passed_mask_level_count"],
        "failed_mask_level_count": conversion["failed_mask_level_count"],
        "all_checkpoint_compatible_batches_constructed_after_filter": conversion[
            "all_checkpoint_compatible_batches_constructed_after_filter"
        ],
        "all_ligand_one_hot_row_sums_valid_after_filter": conversion["all_ligand_one_hot_row_sums_valid_after_filter"],
        "all_pocket_one_hot_row_sums_valid_after_filter": conversion["all_pocket_one_hot_row_sums_valid_after_filter"],
        "all_ligand_unknown_atom_count_zero_after_filter": conversion["all_ligand_unknown_atom_count_zero_after_filter"],
        "all_pocket_unknown_atom_count_zero_after_filter": conversion["all_pocket_unknown_atom_count_zero_after_filter"],
        "ligand_masks_unchanged_after_filter": conversion["ligand_masks_unchanged_after_filter"],
        "ligand_reactive_atom_region_preserved": conversion["ligand_reactive_atom_region_preserved"],
        "no_synthetic_fallback_used": conversion["no_synthetic_fallback_used"],
        "feature_semantics_dimension_contract_passed_after_filter": dimension_contract_passed_after_filter,
        "feature_semantics_mapping_confirmed": mapping_confirmed,
        "feature_semantics_known_after_filter": hard_pass,
        "real_covalent_filtered_feature_semantics_audit_passed": hard_pass,
        "real_covalent_filtered_cuda_forward_backward_smoke_allowed": hard_pass,
        "real_covalent_single_optimizer_step_smoke_allowed": False,
        "cys_first_training_strategy_recommended": True,
        "non_cys_reactive_residue_support_status": NON_CYS_SUPPORT_STATUS,
        "reaction_family_template_audit_required_before_broad_covalent_training": True,
        "ligand_reconstruction_template_gate_required": True,
        "non_cys_data_bulk_cleaning_policy": NON_CYS_DATA_BULK_CLEANING_POLICY,
        "train_ready_scope_v1": TRAIN_READY_SCOPE_V1,
        "recommended_next_step": "real_covalent_filtered_cuda_forward_backward_smoke"
        if hard_pass
        else "real_covalent_filtered_feature_semantics_audit_debug",
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
        "all_checks_passed": hard_pass,
        "blocking_reasons": blockers,
    }
    audit_table_rows = [
        {
            "row_type": "step12h_precondition",
            "status": "passed" if step12h_validated and step12b_validated else "blocked",
            "step12h_filter_gate_validated": step12h_validated,
            "step12b_mask_level_aware_validator_validated": step12b_validated,
            "blocking_reasons": [] if step12h_validated and step12b_validated else blockers,
        },
        {
            "row_type": "checkpoint_feature_contract",
            "checkpoint_ligand_feature_dim": checkpoint_contract["checkpoint_ligand_feature_dim"],
            "checkpoint_pocket_feature_dim": checkpoint_contract["checkpoint_pocket_feature_dim"],
            "checkpoint_feature_semantics_source": checkpoint_contract["checkpoint_feature_semantics_source"],
            "checkpoint_feature_semantics_directly_encoded": checkpoint_contract[
                "checkpoint_feature_semantics_directly_encoded"
            ],
            "checkpoint_10d_mapping_project": checkpoint_contract["checkpoint_10d_mapping_project"],
            "checkpoint_10d_mapping_matches_project_mapping": checkpoint_contract[
                "checkpoint_10d_mapping_matches_project_mapping"
            ],
            "status": checkpoint_contract["status"],
            "blocking_reasons": checkpoint_contract["blocking_reasons"],
        },
        {
            "row_type": "filtered_real_atom_vocabulary",
            "sample_count": filtered_vocab["sample_count"],
            "ligand_atomic_numbers_unique": filtered_vocab["ligand_atomic_numbers_unique"],
            "pocket_atomic_numbers_unique_before_filter": filtered_vocab["pocket_atomic_numbers_unique_before_filter"],
            "pocket_atomic_numbers_unique_after_filter": filtered_vocab["pocket_atomic_numbers_unique_after_filter"],
            "ligand_unknown_atom_count_before_filter": filtered_vocab["ligand_unknown_atom_count_before_filter"],
            "pocket_unknown_atom_count_before_filter": filtered_vocab["pocket_unknown_atom_count_before_filter"],
            "filtered_pocket_atom_count": filtered_vocab["filtered_pocket_atom_count"],
            "filtered_pocket_atom_numbers": filtered_vocab["filtered_pocket_atom_numbers"],
            "filtered_pocket_atom_symbols": filtered_vocab["filtered_pocket_atom_symbols"],
            "ligand_unknown_atom_count_after_filter": filtered_vocab["ligand_unknown_atom_count_after_filter"],
            "pocket_unknown_atom_count_after_filter": filtered_vocab["pocket_unknown_atom_count_after_filter"],
            "unknown_atom_policy_triggered_after_filter": filtered_vocab["unknown_atom_policy_triggered_after_filter"],
            "zero_vector_unknown_atom_policy_safe_after_filter": filtered_vocab[
                "zero_vector_unknown_atom_policy_safe_after_filter"
            ],
            "status": filtered_vocab["status"],
            "blocking_reasons": filtered_vocab["blocking_reasons"],
        },
    ]
    audit_table_rows.extend(conversion["rows"])
    audit_table_rows.extend(
        [
            {
                "row_type": "non_cys_training_scope_boundary",
                "cys_first_training_strategy_recommended": True,
                "non_cys_reactive_residue_support_status": NON_CYS_SUPPORT_STATUS,
                "reaction_family_template_audit_required_before_broad_covalent_training": True,
                "ligand_reconstruction_template_gate_required": True,
                "non_cys_data_bulk_cleaning_policy": NON_CYS_DATA_BULK_CLEANING_POLICY,
                "train_ready_scope_v1": TRAIN_READY_SCOPE_V1,
                "status": "passed",
                "blocking_reasons": [],
            },
            {
                "row_type": "decision",
                "feature_semantics_dimension_contract_passed_after_filter": dimension_contract_passed_after_filter,
                "feature_semantics_mapping_confirmed": mapping_confirmed,
                "feature_semantics_known_after_filter": hard_pass,
                "real_covalent_filtered_feature_semantics_audit_passed": hard_pass,
                "real_covalent_filtered_cuda_forward_backward_smoke_allowed": hard_pass,
                "real_covalent_single_optimizer_step_smoke_allowed": False,
                "recommended_next_step": manifest["recommended_next_step"],
                "status": "passed" if hard_pass else "blocked",
                "blocking_reasons": blockers,
            },
        ]
    )
    return {
        "manifest": manifest,
        "audit_table_rows": audit_table_rows,
        "report_sections": {
            "step12h_precondition": {
                "step12h_filter_gate_validated": step12h_validated,
                "step12b_mask_level_aware_validator_validated": step12b_validated,
            },
            "checkpoint_feature_contract": {
                "checkpoint_ligand_feature_dim": checkpoint_contract["checkpoint_ligand_feature_dim"],
                "checkpoint_pocket_feature_dim": checkpoint_contract["checkpoint_pocket_feature_dim"],
                "checkpoint_10d_mapping_matches_project_mapping": checkpoint_contract[
                    "checkpoint_10d_mapping_matches_project_mapping"
                ],
            },
            "filtered_real_atom_vocabulary": {
                "pocket_unknown_atom_count_before_filter": filtered_vocab["pocket_unknown_atom_count_before_filter"],
                "pocket_unknown_atom_count_after_filter": filtered_vocab["pocket_unknown_atom_count_after_filter"],
                "filtered_pocket_atom_count": filtered_vocab["filtered_pocket_atom_count"],
            },
            "mask_level_filtered_conversion": {
                "audited_mask_level_count": conversion["audited_mask_level_count"],
                "passed_mask_level_count": conversion["passed_mask_level_count"],
                "all_pocket_one_hot_row_sums_valid_after_filter": conversion[
                    "all_pocket_one_hot_row_sums_valid_after_filter"
                ],
            },
            "feature_semantics_decision": {
                "feature_semantics_dimension_contract_passed_after_filter": dimension_contract_passed_after_filter,
                "feature_semantics_mapping_confirmed": mapping_confirmed,
                "feature_semantics_known_after_filter": hard_pass,
            },
            "non_cys_training_scope_boundary": {
                "cys_first_training_strategy_recommended": True,
                "train_ready_scope_v1": TRAIN_READY_SCOPE_V1,
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
                "real_covalent_filtered_feature_semantics_audit_passed": hard_pass,
                "real_covalent_filtered_cuda_forward_backward_smoke_allowed": hard_pass,
                "real_covalent_single_optimizer_step_smoke_allowed": False,
                "recommended_next_step": manifest["recommended_next_step"],
            },
        },
    }
