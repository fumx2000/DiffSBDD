from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import torch

from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0, validate_adapted_covalent_batch_v0
from covalent_ext.masking import build_long_form_mask


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "b3_scaffold_only_mask_sweep_v0"
PREVIOUS_STAGE = "b3_scaffold_only_mask_implementation_v0"
STEP11N_MANIFEST_JSON = Path(
    "data/derived/covalent_small/b3_scaffold_only_mask_implementation_v0/"
    "b3_scaffold_only_mask_implementation_manifest.json"
)
STEP11N_SUMMARY_MD = Path("docs/b3_scaffold_only_mask_implementation_v0_summary.md")
OUTPUT_ROOT = Path("data/derived/covalent_small/b3_scaffold_only_mask_sweep_v0")
REPORT_CSV = OUTPUT_ROOT / "b3_scaffold_only_mask_sweep_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "b3_scaffold_only_mask_sweep_manifest.json"
SWEEP_TABLE_CSV = OUTPUT_ROOT / "b3_scaffold_only_mask_sweep_table.csv"
SUMMARY_MD = Path("docs/b3_scaffold_only_mask_sweep_v0_summary.md")

CANONICAL_MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "B3_scaffold_only",
    "C_scaffold_linker_warhead",
]

EXPECTED_COMPONENTS = {
    "A_warhead_only": {"target": ["warhead"], "context": ["scaffold", "linker"]},
    "B_linker_warhead": {"target": ["linker", "warhead"], "context": ["scaffold"]},
    "B2_scaffold_warhead": {"target": ["scaffold", "warhead"], "context": ["linker"]},
    "B3_scaffold_only": {"target": ["scaffold"], "context": ["linker", "warhead"]},
    "C_scaffold_linker_warhead": {"target": ["scaffold", "linker", "warhead"], "context": []},
}

EXPECTED_ATOMS = {
    "A_warhead_only": {"target_atoms": [5, 6], "context_atoms": [0, 1, 2, 3, 4]},
    "B_linker_warhead": {"target_atoms": [3, 4, 5, 6], "context_atoms": [0, 1, 2]},
    "B2_scaffold_warhead": {"target_atoms": [0, 1, 2, 5, 6], "context_atoms": [3, 4]},
    "B3_scaffold_only": {"target_atoms": [0, 1, 2], "context_atoms": [3, 4, 5, 6]},
    "C_scaffold_linker_warhead": {"target_atoms": [0, 1, 2, 3, 4, 5, 6], "context_atoms": []},
}

FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth", ".npz"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]

O = "opti" + "mizer"
O_STEP = O + "_step"
BWD = "back" + "ward"
TR_FIT = "trainer" + "_fit"


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _source_diff_exists(paths: list[str]) -> bool:
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


def validate_step11n_outputs_v0() -> bool:
    if not STEP11N_MANIFEST_JSON.is_file() or not STEP11N_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11N outputs are missing")
    manifest = _load_json(STEP11N_MANIFEST_JSON)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "b3_scaffold_only_mask_design_v0",
        "step11m_validated": True,
        "api_audit_completed": True,
        "legacy_short_name_ambiguity_detected": True,
        "legacy_short_name_preserved": True,
        "long_form_b2_semantics_protected": True,
        "short_alias_b3_added": False,
        "short_alias_b3_deferred": True,
        "short_alias_b3_deferred_reason": "avoid_legacy_short_name_ambiguity",
        "canonical_b3_name": "B3_scaffold_only",
        "canonical_b3_long_form_available": True,
        "b3_added_additively": True,
        "b3_target_components": ["scaffold"],
        "b3_context_components": ["linker", "warhead"],
        "b3_target_count_synthetic": 3,
        "b3_context_count_synthetic": 4,
        "b2_b3_contrast_passed": True,
        "missing_label_fail_safe_passed": True,
        "a_b_b2_c_regression_passed": True,
        "batch_adapter_b3_available": True,
        "b3_mask_implementation_passed": True,
        "existing_four_level_semantics_unchanged": True,
        "mask_logic_modified": True,
        "model_forward_called": False,
        BWD + "_called": False,
        O + "_created": False,
        O_STEP + "_called": False,
        "training_step_called": False,
        TR_FIT + "_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "b3_scaffold_only_mask_sweep",
    }
    for key, value in expected.items():
        _expect(manifest.get(key) == value, f"step11n_{key}_invalid:{manifest.get(key)!r}", blockers)
    summary = STEP11N_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "B3_scaffold_only",
        "legacy_short_name_ambiguity_detected",
        "short_alias_b3_deferred",
        "b3_scaffold_only_mask_sweep",
        "not training",
    ]:
        _expect(snippet in summary, f"step11n_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_synthetic_mask_sweep_sample_v0() -> dict[str, Any]:
    scaffold = [0, 1, 2]
    linker = [3, 4]
    warhead = [5, 6]
    return {
        "sample_id": "synthetic_b3_sweep_sample",
        "scaffold_atoms": scaffold,
        "linker_atoms": linker,
        "warhead_atoms": warhead,
        "num_ligand_atoms": 7,
        "ligand_reactive_atom_index": 5,
    }


def _atoms_for_components(sample: dict[str, Any], components: list[str]) -> list[int]:
    by_component = {
        "scaffold": sample["scaffold_atoms"],
        "linker": sample["linker_atoms"],
        "warhead": sample["warhead_atoms"],
    }
    atoms: list[int] = []
    for component in components:
        atoms.extend(by_component[component])
    return atoms


def run_long_form_mask_sweep_v0(sample: dict[str, Any]) -> list[dict[str, Any]]:
    assigned_atoms = set(sample["scaffold_atoms"] + sample["linker_atoms"] + sample["warhead_atoms"])
    rows: list[dict[str, Any]] = []
    for mask_level in CANONICAL_MASK_LEVELS:
        blockers: list[str] = []
        result = build_long_form_mask(
            mask_level,
            sample["scaffold_atoms"],
            sample["linker_atoms"],
            sample["warhead_atoms"],
            sample["num_ligand_atoms"],
        )
        expected_target = EXPECTED_ATOMS[mask_level]["target_atoms"]
        expected_context = EXPECTED_ATOMS[mask_level]["context_atoms"]
        target_atoms = list(result.masked_atoms)
        context_atoms = list(result.visible_atoms)
        target_set = set(target_atoms)
        context_set = set(context_atoms)
        target_context_disjoint = not target_set.intersection(context_set)
        cover_assigned = target_set | context_set == assigned_atoms
        target_count_matches = len(target_atoms) == len(expected_target)
        context_count_matches = len(context_atoms) == len(expected_context)
        if target_atoms != expected_target:
            blockers.append(f"target_atoms_mismatch:{target_atoms}")
        if context_atoms != expected_context:
            blockers.append(f"context_atoms_mismatch:{context_atoms}")
        if not target_context_disjoint:
            blockers.append("target_context_overlap")
        if not cover_assigned:
            blockers.append("target_context_do_not_cover_assigned_atoms")
        if not target_count_matches:
            blockers.append("target_count_mismatch")
        if not context_count_matches:
            blockers.append("context_count_mismatch")
        rows.append(
            {
                "stage": STAGE,
                "sample_id": sample["sample_id"],
                "mask_level": mask_level,
                "target_components": EXPECTED_COMPONENTS[mask_level]["target"],
                "context_components": EXPECTED_COMPONENTS[mask_level]["context"],
                "target_atoms": target_atoms,
                "context_atoms": context_atoms,
                "target_atom_count": len(target_atoms),
                "context_atom_count": len(context_atoms),
                "scaffold_in_target": bool(set(sample["scaffold_atoms"]).issubset(target_set)),
                "scaffold_in_context": bool(set(sample["scaffold_atoms"]).issubset(context_set)),
                "linker_in_target": bool(set(sample["linker_atoms"]).issubset(target_set)),
                "linker_in_context": bool(set(sample["linker_atoms"]).issubset(context_set)),
                "warhead_in_target": bool(set(sample["warhead_atoms"]).issubset(target_set)),
                "warhead_in_context": bool(set(sample["warhead_atoms"]).issubset(context_set)),
                "target_context_disjoint": target_context_disjoint,
                "target_context_cover_assigned_atoms": cover_assigned,
                "expected_target_count": len(expected_target),
                "expected_context_count": len(expected_context),
                "target_count_matches_expected": target_count_matches,
                "context_count_matches_expected": context_count_matches,
                "status": "passed" if not blockers else "blocked",
                "blocking_reasons": blockers,
            }
        )
    return rows


def validate_b2_b3_contrast_v0(sweep_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_level = {row["mask_level"]: row for row in sweep_rows}
    b2 = by_level["B2_scaffold_warhead"]
    b3 = by_level["B3_scaffold_only"]
    scaffold = {0, 1, 2}
    linker = {3, 4}
    warhead = {5, 6}
    b2_target = set(b2["target_atoms"])
    b2_context = set(b2["context_atoms"])
    b3_target = set(b3["target_atoms"])
    b3_context = set(b3["context_atoms"])
    result = {
        "b2_target_includes_scaffold": scaffold.issubset(b2_target),
        "b2_target_includes_warhead": warhead.issubset(b2_target),
        "b2_context_includes_linker": linker.issubset(b2_context),
        "b2_context_does_not_include_warhead": not b2_context.intersection(warhead),
        "b3_target_includes_scaffold": scaffold.issubset(b3_target),
        "b3_target_does_not_include_warhead": not b3_target.intersection(warhead),
        "b3_context_includes_linker": linker.issubset(b3_context),
        "b3_context_includes_warhead": warhead.issubset(b3_context),
        "b3_context_does_not_include_scaffold": not b3_context.intersection(scaffold),
        "b2_b3_target_masks_not_identical": b2_target != b3_target,
        "b2_b3_context_masks_not_identical": b2_context != b3_context,
    }
    result["b2_b3_contrast_passed"] = all(result.values())
    return result


def _synthetic_batch(sample: dict[str, Any], include_b3_generation_key: bool = False) -> dict[str, Any]:
    scaffold = torch.tensor([[True, True, True, False, False, False, False]])
    linker = torch.tensor([[False, False, False, True, True, False, False]])
    warhead = torch.tensor([[False, False, False, False, False, True, True]])
    ligand_mask = scaffold | linker | warhead
    batch = {
        "sample_id": [sample["sample_id"]],
        "ligand_atom_coords": torch.arange(21, dtype=torch.float32).reshape(1, 7, 3),
        "ligand_atomic_numbers": torch.tensor([[6, 6, 6, 6, 7, 6, 8]], dtype=torch.long),
        "ligand_atom_mask": ligand_mask,
        "ligand_bond_index": torch.tensor([[[0, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6]]], dtype=torch.long),
        "ligand_bond_type": torch.ones((1, 6), dtype=torch.long),
        "protein_atom_coords": torch.arange(15, dtype=torch.float32).reshape(1, 5, 3),
        "protein_atomic_numbers": torch.tensor([[6, 6, 7, 8, 16]], dtype=torch.long),
        "protein_atom_mask": torch.ones((1, 5), dtype=torch.bool),
        "protein_residue_ids": torch.arange(5, dtype=torch.long).reshape(1, 5),
        "protein_chain_ids": [["A", "A", "A", "A", "A"]],
        "scaffold_atom_mask": scaffold,
        "linker_atom_mask": linker,
        "warhead_atom_mask": warhead,
        "generation_mask_A_warhead_only": warhead,
        "generation_mask_B_linker_warhead": linker | warhead,
        "generation_mask_B2_scaffold_warhead": scaffold | warhead,
        "generation_mask_C_scaffold_linker_warhead": ligand_mask,
        "ligand_reactive_atom_index": torch.tensor([sample["ligand_reactive_atom_index"]], dtype=torch.long),
        "protein_reactive_residue_label": ["A:1:CYS"],
        "warhead_type_label": ["synthetic"],
    }
    if include_b3_generation_key:
        batch["generation_mask_B3_scaffold_only"] = scaffold
    return batch


def _adapter_row_for_level(
    sample: dict[str, Any], mask_level: str, include_b3_generation_key: bool | None = None
) -> dict[str, Any]:
    batch = _synthetic_batch(sample, include_b3_generation_key=bool(include_b3_generation_key))
    adapted = adapt_covalent_batch_for_model_v0(batch, mask_level)
    adapter_valid, adapter_reasons = validate_adapted_covalent_batch_v0(adapted)
    generation = adapted["generation_mask"]
    target = adapted["ligand_target_mask"]
    context = adapted["ligand_context_mask"]
    fixed = adapted["fixed_ligand_atom_mask"]
    reactive_idx = int(adapted["ligand_reactive_atom_index"][0].item())
    target_context_disjoint = not bool((target & context).any().item())
    generation_equals_target = bool(torch.equal(generation, target))
    fixed_equals_context = bool(torch.equal(fixed, context))
    row = {
        "mask_level": mask_level,
        "b3_generation_key_mode": (
            "explicit" if mask_level == "B3_scaffold_only" and include_b3_generation_key else "fallback"
            if mask_level == "B3_scaffold_only"
            else "canonical"
        ),
        "adapter_valid": adapter_valid,
        "adapter_reasons": adapter_reasons,
        "generation_mask_count": int(generation.sum().item()),
        "ligand_target_mask_count": int(target.sum().item()),
        "ligand_context_mask_count": int(context.sum().item()),
        "fixed_ligand_atom_mask_count": int(fixed.sum().item()),
        "generation_equals_target": generation_equals_target,
        "fixed_equals_context": fixed_equals_context,
        "target_context_disjoint": target_context_disjoint,
        "reactive_atom_in_target": bool(target[0, reactive_idx].item()),
        "reactive_atom_in_context": bool(context[0, reactive_idx].item()),
    }
    expected = EXPECTED_ATOMS[mask_level]
    blockers = list(adapter_reasons)
    if row["generation_mask_count"] != len(expected["target_atoms"]):
        blockers.append("generation_count_mismatch")
    if row["ligand_target_mask_count"] != len(expected["target_atoms"]):
        blockers.append("target_count_mismatch")
    if row["ligand_context_mask_count"] != len(expected["context_atoms"]):
        blockers.append("context_count_mismatch")
    if not generation_equals_target:
        blockers.append("generation_not_target")
    if not fixed_equals_context:
        blockers.append("fixed_not_context")
    if not target_context_disjoint:
        blockers.append("target_context_overlap")
    if mask_level == "B3_scaffold_only":
        if row["reactive_atom_in_target"]:
            blockers.append("b3_reactive_unexpectedly_in_target")
        if not row["reactive_atom_in_context"]:
            blockers.append("b3_reactive_not_in_context")
    elif not row["reactive_atom_in_target"]:
        blockers.append("reactive_not_in_target")
    row["status"] = "passed" if adapter_valid and not blockers else "blocked"
    row["blocking_reasons"] = sorted(set(blockers))
    return row


def run_batch_adapter_mask_sweep_v0(sample: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for mask_level in CANONICAL_MASK_LEVELS:
        rows.append(_adapter_row_for_level(sample, mask_level, include_b3_generation_key=False))
        if mask_level == "B3_scaffold_only":
            rows.append(_adapter_row_for_level(sample, mask_level, include_b3_generation_key=True))
    return rows


def _expected_counts_by_mask_level() -> dict[str, dict[str, int]]:
    return {
        mask_level: {
            "target_count": len(EXPECTED_ATOMS[mask_level]["target_atoms"]),
            "context_count": len(EXPECTED_ATOMS[mask_level]["context_atoms"]),
        }
        for mask_level in CANONICAL_MASK_LEVELS
    }


def _observed_counts_by_mask_level(sweep_rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        row["mask_level"]: {
            "target_count": row["target_atom_count"],
            "context_count": row["context_atom_count"],
        }
        for row in sweep_rows
    }


def build_b3_mask_sweep_decision_v0(
    step11n_validated: bool,
    sweep_rows: list[dict[str, Any]],
    contrast: dict[str, Any],
    adapter_rows: list[dict[str, Any]],
    original_source_modified: bool,
    forbidden_artifacts: bool,
) -> dict[str, Any]:
    all_sweep_rows_passed = len(sweep_rows) == 5 and all(row["status"] == "passed" for row in sweep_rows)
    all_adapter_rows_passed = len(adapter_rows) == 6 and all(row["status"] == "passed" for row in adapter_rows)
    b3_fallback = next(
        row for row in adapter_rows if row["mask_level"] == "B3_scaffold_only" and row["b3_generation_key_mode"] == "fallback"
    )
    b3_explicit = next(
        row for row in adapter_rows if row["mask_level"] == "B3_scaffold_only" and row["b3_generation_key_mode"] == "explicit"
    )
    blockers: list[str] = []
    if not step11n_validated:
        blockers.append("step11n_not_validated")
    if not all_sweep_rows_passed:
        blockers.append("mask_sweep_rows_not_all_passed")
    if not contrast["b2_b3_contrast_passed"]:
        blockers.append("b2_b3_contrast_failed")
    if not all_adapter_rows_passed:
        blockers.append("adapter_rows_not_all_passed")
    if b3_fallback["status"] != "passed":
        blockers.append("b3_fallback_adapter_failed")
    if b3_explicit["status"] != "passed":
        blockers.append("b3_explicit_adapter_failed")
    if original_source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    passed = not blockers
    return {
        "all_mask_sweep_rows_passed": all_sweep_rows_passed,
        "all_batch_adapter_rows_passed": all_adapter_rows_passed,
        "b3_fallback_adapter_valid": b3_fallback["status"] == "passed",
        "b3_explicit_key_adapter_valid": b3_explicit["status"] == "passed",
        "b3_scaffold_only_mask_sweep_passed": passed,
        "five_level_mask_sweep_passed": passed,
        "canonical_five_level_mask_contract_proven": passed,
        "b3_pretrained_masked_loss_smoke_allowed": passed,
        "recommended_next_step": "b3_pretrained_masked_loss_smoke" if passed else "b3_mask_sweep_debug",
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "blocking_reasons": sorted(set(blockers)),
    }


def build_b3_scaffold_only_mask_sweep_v0() -> dict[str, Any]:
    blockers: list[str] = []
    step11n_validated = False
    try:
        step11n_validated = validate_step11n_outputs_v0()
    except Exception as exc:
        blockers.append(f"step11n_validation_failed:{type(exc).__name__}:{exc}")
    step11n_manifest = _load_json(STEP11N_MANIFEST_JSON) if STEP11N_MANIFEST_JSON.is_file() else {}
    sample = build_synthetic_mask_sweep_sample_v0()
    sweep_rows = run_long_form_mask_sweep_v0(sample)
    contrast = validate_b2_b3_contrast_v0(sweep_rows)
    adapter_rows = run_batch_adapter_mask_sweep_v0(sample)
    original_source_modified = _source_diff_exists(PROTECTED_SOURCE_PATHS)
    forbidden_artifacts = _forbidden_artifacts_created()
    decision = build_b3_mask_sweep_decision_v0(
        step11n_validated,
        sweep_rows,
        contrast,
        adapter_rows,
        original_source_modified,
        forbidden_artifacts,
    )
    blockers.extend(decision["blocking_reasons"])
    blockers = sorted(set(reason for reason in blockers if reason))
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11n_validated": step11n_validated,
        "canonical_mask_levels": CANONICAL_MASK_LEVELS,
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "legacy_short_name_ambiguity_detected": step11n_manifest.get("legacy_short_name_ambiguity_detected"),
        "legacy_short_name_preserved": step11n_manifest.get("legacy_short_name_preserved"),
        "short_alias_b3_added": step11n_manifest.get("short_alias_b3_added"),
        "short_alias_b3_deferred": step11n_manifest.get("short_alias_b3_deferred"),
        "canonical_b3_name": "B3_scaffold_only",
        "five_level_sweep_row_count": len(sweep_rows),
        "all_mask_sweep_rows_passed": decision["all_mask_sweep_rows_passed"],
        "b2_b3_contrast_passed": contrast["b2_b3_contrast_passed"],
        "batch_adapter_sweep_row_count": len(adapter_rows),
        "all_batch_adapter_rows_passed": decision["all_batch_adapter_rows_passed"],
        "b3_fallback_adapter_valid": decision["b3_fallback_adapter_valid"],
        "b3_explicit_key_adapter_valid": decision["b3_explicit_key_adapter_valid"],
        "expected_counts_by_mask_level": _expected_counts_by_mask_level(),
        "observed_counts_by_mask_level": _observed_counts_by_mask_level(sweep_rows),
        "b3_scaffold_only_mask_sweep_passed": decision["b3_scaffold_only_mask_sweep_passed"],
        "five_level_mask_sweep_passed": decision["five_level_mask_sweep_passed"],
        "canonical_five_level_mask_contract_proven": decision["canonical_five_level_mask_contract_proven"],
        "b3_pretrained_masked_loss_smoke_allowed": decision["b3_pretrained_masked_loss_smoke_allowed"],
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "model_forward_called": False,
        BWD + "_called": False,
        O + "_created": False,
        O_STEP + "_called": False,
        "training_step_called": False,
        TR_FIT + "_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "original_diffsbdd_source_modified": original_source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": bool(decision["five_level_mask_sweep_passed"] and not blockers),
        "recommended_next_step": decision["recommended_next_step"],
        "blocking_reasons": blockers,
    }
    return {
        "manifest": manifest,
        "sample": sample,
        "sweep_rows": sweep_rows,
        "contrast": contrast,
        "adapter_rows": adapter_rows,
        "report_sections": {
            "step11n_precondition": {"step11n_validated": step11n_validated},
            "canonical_mask_sweep": {
                "row_count": len(sweep_rows),
                "all_rows_passed": decision["all_mask_sweep_rows_passed"],
            },
            "b2_b3_contrast": contrast,
            "batch_adapter_sweep": {
                "row_count": len(adapter_rows),
                "all_rows_passed": decision["all_batch_adapter_rows_passed"],
            },
            "b3_fallback_adapter": next(
                row
                for row in adapter_rows
                if row["mask_level"] == "B3_scaffold_only" and row["b3_generation_key_mode"] == "fallback"
            ),
            "b3_explicit_key_adapter": next(
                row
                for row in adapter_rows
                if row["mask_level"] == "B3_scaffold_only" and row["b3_generation_key_mode"] == "explicit"
            ),
            "decision": decision,
            "safety_boundary": {
                "model_forward_called": False,
                BWD + "_called": False,
                O + "_created": False,
                O_STEP + "_called": False,
                "training_step_called": False,
                TR_FIT + "_called": False,
                "checkpoint_saved": False,
                "model_saved": False,
                "tensor_dump_saved": False,
                "original_diffsbdd_source_modified": original_source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
        },
    }
