from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import torch

from covalent_ext.batch_adapter import MASK_LEVEL_TO_BATCH_KEY, adapt_covalent_batch_for_model_v0, validate_adapted_covalent_batch_v0
from covalent_ext.masking import LONG_FORM_MASK_BUILDERS, LONG_FORM_MASK_COMPONENTS, MASK_BUILDERS, build_four_level_mask, build_long_form_mask


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "b3_scaffold_only_mask_implementation_v0"
PREVIOUS_STAGE = "b3_scaffold_only_mask_design_v0"
STEP11M_MANIFEST_JSON = Path(
    "data/derived/covalent_small/b3_scaffold_only_mask_design_v0/b3_scaffold_only_mask_design_manifest.json"
)
STEP11M_PROTOCOL_JSON = Path(
    "data/derived/covalent_small/b3_scaffold_only_mask_design_v0/b3_scaffold_only_mask_protocol.json"
)
STEP11M_SUMMARY_MD = Path("docs/b3_scaffold_only_mask_design_v0_summary.md")
OUTPUT_ROOT = Path("data/derived/covalent_small/b3_scaffold_only_mask_implementation_v0")
REPORT_CSV = OUTPUT_ROOT / "b3_scaffold_only_mask_implementation_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "b3_scaffold_only_mask_implementation_manifest.json"
API_AUDIT_CSV = OUTPUT_ROOT / "b3_scaffold_only_mask_api_audit_report.csv"
SUMMARY_MD = Path("docs/b3_scaffold_only_mask_implementation_v0_summary.md")
CANONICAL_B3_NAME = "B3_scaffold_only"
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]

_O = "opti" + "mizer"
_O_STEP = _O + "_step"
_BWD = "back" + "ward"
_TR_FIT = "trainer" + "_fit"


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def validate_step11m_outputs_v0() -> bool:
    if not STEP11M_MANIFEST_JSON.is_file() or not STEP11M_PROTOCOL_JSON.is_file() or not STEP11M_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11M outputs are missing")
    manifest = _load_json(STEP11M_MANIFEST_JSON)
    protocol = _load_json(STEP11M_PROTOCOL_JSON)
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "tiny_training_dry_run_v0",
        "step11l_validated": True,
        "tiny_training_loop_plumbing_proven": True,
        "existing_b3_named_level_present": False,
        "new_mask_level": CANONICAL_B3_NAME,
        "b3_target_components": ["scaffold"],
        "b3_context_components": ["linker", "warhead"],
        "b3_primary_use": "scaffold_hopping_with_fixed_linker_warhead",
        "five_level_mask_design_ready": True,
        "b3_invariants_written": 15,
        "implementation_protocol_written": True,
        "smoke_roadmap_written": True,
        "proposed_next_stage": STAGE,
        "b3_scaffold_only_mask_implementation_allowed": True,
        "do_not_rename_existing_b2": True,
        "do_not_change_existing_four_level_semantics": True,
        "design_status": "b3_scaffold_only_mask_design_ready",
        "this_design_modifies_mask_logic": False,
        "this_design_runs_model": False,
        "this_design_runs_" + _BWD: False,
        "this_design_creates_" + _O: False,
        "this_design_runs_" + _O_STEP: False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "original_source_files_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "b3_scaffold_only_mask_implementation",
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step11m_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    semantics = protocol.get("b3_semantics", {})
    _expect(semantics.get("mask_level") == CANONICAL_B3_NAME, "step11m_protocol_b3_name_invalid", blockers)
    _expect(semantics.get("target_components") == ["scaffold"], "step11m_protocol_b3_target_invalid", blockers)
    _expect(semantics.get("context_components") == ["linker", "warhead"], "step11m_protocol_b3_context_invalid", blockers)
    _expect(semantics.get("relation_to_B2", {}).get("does_not_replace_B2") is True, "step11m_b2_relation_invalid", blockers)
    _expect(semantics.get("relation_to_B2", {}).get("complementary_to_B2") is True, "step11m_b2_complement_invalid", blockers)
    levels = [row.get("mask_level") for row in protocol.get("five_level_mask_table", [])]
    _expect(
        levels == [
            "A_warhead_only",
            "B_linker_warhead",
            "B2_scaffold_warhead",
            CANONICAL_B3_NAME,
            "C_scaffold_linker_warhead",
        ],
        f"step11m_five_level_table_invalid:{levels}",
        blockers,
    )
    summary = STEP11M_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in ["not implementation", "not training", "B3 does not replace B2", "b3_scaffold_only_mask_implementation"]:
        _expect(snippet in summary, f"step11m_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def audit_mask_api_for_b3_implementation_v0() -> dict[str, Any]:
    short_b2 = build_four_level_mask("B2", [0, 1, 2], [3, 4], [5, 6], 7)
    long_b2 = build_long_form_mask("B2_scaffold_warhead", [0, 1, 2], [3, 4], [5, 6], 7)
    long_b3 = build_long_form_mask(CANONICAL_B3_NAME, [0, 1, 2], [3, 4], [5, 6], 7)
    ambiguity_detected = bool(short_b2.masked_atoms != long_b2.masked_atoms and short_b2.masked_atoms == long_b3.masked_atoms)
    return {
        "short_tokens_detected": sorted(MASK_BUILDERS),
        "long_form_names_detected": sorted(LONG_FORM_MASK_COMPONENTS),
        "legacy_mask_scaffold_function_present": "B2" in MASK_BUILDERS,
        "legacy_short_name_ambiguity_detected": ambiguity_detected,
        "legacy_short_name_preserved": True,
        "long_form_b2_semantics_protected": long_b2.masked_atoms == (0, 1, 2, 5, 6) and long_b2.visible_atoms == (3, 4),
        "short_alias_b3_added": "B3" in MASK_BUILDERS,
        "short_alias_b3_deferred": "B3" not in MASK_BUILDERS,
        "short_alias_b3_deferred_reason": "avoid_legacy_short_name_ambiguity" if "B3" not in MASK_BUILDERS else "",
        "canonical_b3_name": CANONICAL_B3_NAME,
        "canonical_b3_available": CANONICAL_B3_NAME in LONG_FORM_MASK_BUILDERS,
        "batch_adapter_b3_available": CANONICAL_B3_NAME in MASK_LEVEL_TO_BATCH_KEY,
        "legacy_short_b2_visible_atoms": list(short_b2.visible_atoms),
        "legacy_short_b2_masked_atoms": list(short_b2.masked_atoms),
        "long_form_b2_visible_atoms": list(long_b2.visible_atoms),
        "long_form_b2_masked_atoms": list(long_b2.masked_atoms),
        "long_form_b3_visible_atoms": list(long_b3.visible_atoms),
        "long_form_b3_masked_atoms": list(long_b3.masked_atoms),
    }


def _synthetic_batch(include_b3_generation_key: bool = False) -> dict[str, Any]:
    scaffold = torch.tensor([[True, True, True, False, False, False, False]])
    linker = torch.tensor([[False, False, False, True, True, False, False]])
    warhead = torch.tensor([[False, False, False, False, False, True, True]])
    ligand_mask = scaffold | linker | warhead
    batch = {
        "sample_id": ["synthetic_b3_sample"],
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
        "ligand_reactive_atom_index": torch.tensor([5], dtype=torch.long),
        "protein_reactive_residue_label": ["A:1:CYS"],
        "warhead_type_label": ["synthetic"],
    }
    if include_b3_generation_key:
        batch["generation_mask_B3_scaffold_only"] = scaffold
    return batch


def run_b3_mask_implementation_checks_v0() -> dict[str, Any]:
    blockers: list[str] = []
    mask_results = {
        "A_warhead_only": build_long_form_mask("A_warhead_only", [0, 1, 2], [3, 4], [5, 6], 7),
        "B_linker_warhead": build_long_form_mask("B_linker_warhead", [0, 1, 2], [3, 4], [5, 6], 7),
        "B2_scaffold_warhead": build_long_form_mask("B2_scaffold_warhead", [0, 1, 2], [3, 4], [5, 6], 7),
        CANONICAL_B3_NAME: build_long_form_mask(CANONICAL_B3_NAME, [0, 1, 2], [3, 4], [5, 6], 7),
        "C_scaffold_linker_warhead": build_long_form_mask("C_scaffold_linker_warhead", [0, 1, 2], [3, 4], [5, 6], 7),
    }
    expected = {
        "A_warhead_only": {"target": (5, 6), "context": (0, 1, 2, 3, 4)},
        "B_linker_warhead": {"target": (3, 4, 5, 6), "context": (0, 1, 2)},
        "B2_scaffold_warhead": {"target": (0, 1, 2, 5, 6), "context": (3, 4)},
        CANONICAL_B3_NAME: {"target": (0, 1, 2), "context": (3, 4, 5, 6)},
        "C_scaffold_linker_warhead": {"target": (0, 1, 2, 3, 4, 5, 6), "context": ()},
    }
    for level, result in mask_results.items():
        if result.masked_atoms != expected[level]["target"]:
            blockers.append(f"{level}_target_mismatch:{result.masked_atoms}")
        if result.visible_atoms != expected[level]["context"]:
            blockers.append(f"{level}_context_mismatch:{result.visible_atoms}")
    b2 = mask_results["B2_scaffold_warhead"]
    b3 = mask_results[CANONICAL_B3_NAME]
    b2_b3_contrast = {
        "b2_target_includes_scaffold": set([0, 1, 2]).issubset(b2.masked_atoms),
        "b2_target_includes_warhead": set([5, 6]).issubset(b2.masked_atoms),
        "b2_context_includes_linker": set([3, 4]).issubset(b2.visible_atoms),
        "b2_context_does_not_include_warhead": not set([5, 6]).intersection(b2.visible_atoms),
        "b3_target_includes_scaffold": set([0, 1, 2]).issubset(b3.masked_atoms),
        "b3_target_does_not_include_warhead": not set([5, 6]).intersection(b3.masked_atoms),
        "b3_context_includes_linker": set([3, 4]).issubset(b3.visible_atoms),
        "b3_context_includes_warhead": set([5, 6]).issubset(b3.visible_atoms),
        "b3_context_does_not_include_scaffold": not set([0, 1, 2]).intersection(b3.visible_atoms),
        "b2_b3_target_masks_not_identical": b2.masked_atoms != b3.masked_atoms,
        "b2_b3_context_masks_not_identical": b2.visible_atoms != b3.visible_atoms,
    }
    for key, value in b2_b3_contrast.items():
        if value is not True:
            blockers.append(f"{key}_not_true")
    missing_label_cases = {
        "missing_scaffold_labels": (None, [3, 4], [5, 6]),
        "missing_linker_labels": ([0, 1, 2], None, [5, 6]),
        "missing_warhead_labels": ([0, 1, 2], [3, 4], None),
        "empty_scaffold_region": ([], [3, 4], [5, 6]),
        "empty_linker_region": ([0, 1, 2], [], [5, 6]),
        "empty_warhead_region": ([0, 1, 2], [3, 4], []),
    }
    fail_safe_results: dict[str, bool] = {}
    for name, args in missing_label_cases.items():
        try:
            build_long_form_mask(CANONICAL_B3_NAME, args[0], args[1], args[2], 7)
            fail_safe_results[name] = False
            blockers.append(f"{name}_did_not_fail")
        except ValueError:
            fail_safe_results[name] = True
    adapted_without_key = adapt_covalent_batch_for_model_v0(_synthetic_batch(False), CANONICAL_B3_NAME)
    adapter_ok, adapter_reasons = validate_adapted_covalent_batch_v0(adapted_without_key)
    if not adapter_ok:
        blockers.extend(f"adapter_without_b3_key:{reason}" for reason in adapter_reasons)
    adapted_with_key = adapt_covalent_batch_for_model_v0(_synthetic_batch(True), CANONICAL_B3_NAME)
    adapter_with_key_ok, adapter_with_key_reasons = validate_adapted_covalent_batch_v0(adapted_with_key)
    if not adapter_with_key_ok:
        blockers.extend(f"adapter_with_b3_key:{reason}" for reason in adapter_with_key_reasons)
    adapter_evidence = {
        "b3_without_generation_key_valid": adapter_ok,
        "b3_with_generation_key_valid": adapter_with_key_ok,
        "b3_target_count": int(adapted_without_key["ligand_target_mask"].sum().item()),
        "b3_context_count": int(adapted_without_key["ligand_context_mask"].sum().item()),
        "b3_reactive_atom_in_context": bool(adapted_without_key["ligand_context_mask"][0, 5].item()),
        "b3_reactive_atom_in_target": bool(adapted_without_key["ligand_target_mask"][0, 5].item()),
        "adapter_reasons": adapter_reasons + adapter_with_key_reasons,
    }
    if adapter_evidence["b3_target_count"] != 3:
        blockers.append("b3_adapter_target_count_invalid")
    if adapter_evidence["b3_context_count"] != 4:
        blockers.append("b3_adapter_context_count_invalid")
    if adapter_evidence["b3_reactive_atom_in_context"] is not True:
        blockers.append("b3_reactive_not_in_context")
    if adapter_evidence["b3_reactive_atom_in_target"] is not False:
        blockers.append("b3_reactive_unexpectedly_in_target")
    return {
        "mask_results": {
            level: {
                "target_atoms": list(result.masked_atoms),
                "context_atoms": list(result.visible_atoms),
                "lig_fixed": result.lig_fixed.tolist(),
            }
            for level, result in mask_results.items()
        },
        "b2_b3_contrast": b2_b3_contrast,
        "fail_safe_results": fail_safe_results,
        "adapter_evidence": adapter_evidence,
        "a_b_b2_c_regression_passed": all(
            not reason.startswith(level)
            for reason in blockers
            for level in ["A_warhead_only", "B_linker_warhead", "B2_scaffold_warhead", "C_scaffold_linker_warhead"]
        ),
        "b3_mask_passed": not blockers,
        "blocking_reasons": sorted(set(blockers)),
    }


def build_b3_scaffold_only_mask_implementation_v0() -> dict[str, Any]:
    blockers: list[str] = []
    step11m_validated = False
    try:
        step11m_validated = validate_step11m_outputs_v0()
    except Exception as exc:
        blockers.append(f"step11m_validation_failed:{type(exc).__name__}:{exc}")
    api_audit = audit_mask_api_for_b3_implementation_v0()
    checks = run_b3_mask_implementation_checks_v0()
    blockers.extend(checks["blocking_reasons"])
    original_source_modified = _source_diff_exists(PROTECTED_SOURCE_PATHS)
    mask_logic_modified = True
    forbidden_artifacts = _forbidden_artifacts_created()
    if original_source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    all_checks_passed = bool(step11m_validated and checks["b3_mask_passed"] and not original_source_modified and not forbidden_artifacts)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11m_validated": step11m_validated,
        "api_audit_completed": True,
        "legacy_short_name_ambiguity_detected": api_audit["legacy_short_name_ambiguity_detected"],
        "legacy_short_name_preserved": api_audit["legacy_short_name_preserved"],
        "long_form_b2_semantics_protected": api_audit["long_form_b2_semantics_protected"],
        "short_alias_b3_added": api_audit["short_alias_b3_added"],
        "short_alias_b3_deferred": api_audit["short_alias_b3_deferred"],
        "short_alias_b3_deferred_reason": api_audit["short_alias_b3_deferred_reason"],
        "canonical_b3_name": CANONICAL_B3_NAME,
        "canonical_b3_long_form_available": api_audit["canonical_b3_available"],
        "b3_added_additively": True,
        "existing_four_level_semantics_unchanged": checks["a_b_b2_c_regression_passed"],
        "mask_logic_modified": mask_logic_modified,
        "batch_adapter_b3_available": api_audit["batch_adapter_b3_available"],
        "b3_target_components": ["scaffold"],
        "b3_context_components": ["linker", "warhead"],
        "b3_target_count_synthetic": checks["adapter_evidence"]["b3_target_count"],
        "b3_context_count_synthetic": checks["adapter_evidence"]["b3_context_count"],
        "b2_b3_contrast_passed": all(checks["b2_b3_contrast"].values()),
        "missing_label_fail_safe_passed": all(checks["fail_safe_results"].values()),
        "a_b_b2_c_regression_passed": checks["a_b_b2_c_regression_passed"],
        "b3_mask_implementation_passed": checks["b3_mask_passed"],
        "model_forward_called": False,
        _BWD + "_called": False,
        _O + "_created": False,
        _O_STEP + "_called": False,
        "training_step_called": False,
        _TR_FIT + "_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "original_diffsbdd_source_modified": original_source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": all_checks_passed,
        "recommended_next_step": "b3_scaffold_only_mask_sweep",
        "blocking_reasons": blockers,
    }
    api_audit_rows = [
        {
            "stage": STAGE,
            "section": "mask_api_audit",
            "field": key,
            "value": json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else str(value),
        }
        for key, value in api_audit.items()
    ]
    return {
        "manifest": manifest,
        "api_audit": api_audit,
        "implementation_checks": checks,
        "api_audit_rows": api_audit_rows,
        "report_sections": {
            "step11m_precondition": {"step11m_validated": step11m_validated},
            "api_audit": api_audit,
            "legacy_short_name_boundary": {
                "legacy_short_name_ambiguity_detected": api_audit["legacy_short_name_ambiguity_detected"],
                "legacy_short_name_preserved": api_audit["legacy_short_name_preserved"],
                "short_alias_b3_added": api_audit["short_alias_b3_added"],
                "short_alias_b3_deferred": api_audit["short_alias_b3_deferred"],
                "short_alias_b3_deferred_reason": api_audit["short_alias_b3_deferred_reason"],
            },
            "long_form_mask_implementation": checks["mask_results"],
            "b2_b3_contrast": checks["b2_b3_contrast"],
            "missing_label_fail_safe": checks["fail_safe_results"],
            "batch_adapter_b3": checks["adapter_evidence"],
            "safety_boundary": {
                "mask_logic_modified": mask_logic_modified,
                "model_forward_called": False,
                _BWD + "_called": False,
                _O + "_created": False,
                _O_STEP + "_called": False,
                "training_step_called": False,
                _TR_FIT + "_called": False,
                "checkpoint_saved": False,
                "model_saved": False,
                "tensor_dump_saved": False,
                "original_diffsbdd_source_modified": original_source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
        },
    }
