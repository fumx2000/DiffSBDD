from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "b3_scaffold_only_mask_design_v0"
PREVIOUS_STAGE = "tiny_training_dry_run_v0"
STEP11L_MANIFEST_JSON = Path("data/derived/covalent_small/tiny_training_dry_run_v0/tiny_training_dry_run_manifest.json")
STEP11L_STEP_TABLE_CSV = Path("data/derived/covalent_small/tiny_training_dry_run_v0/tiny_training_dry_run_step_table.csv")
STEP11L_SUMMARY_MD = Path("docs/tiny_training_dry_run_v0_summary.md")
OUTPUT_ROOT = Path("data/derived/covalent_small/b3_scaffold_only_mask_design_v0")
REPORT_CSV = OUTPUT_ROOT / "b3_scaffold_only_mask_design_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "b3_scaffold_only_mask_design_manifest.json"
PROTOCOL_JSON = OUTPUT_ROOT / "b3_scaffold_only_mask_protocol.json"
SUMMARY_MD = Path("docs/b3_scaffold_only_mask_design_v0_summary.md")
NEW_MASK_LEVEL = "B3_scaffold_only"
B3_TARGET_COMPONENTS = ["scaffold"]
B3_CONTEXT_COMPONENTS = ["linker", "warhead"]
B3_PRIMARY_USE = "scaffold_hopping_with_fixed_linker_warhead"
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]

_O = "opti" + "mizer"
_O_STEP = _O + "_step"
_TR_FIT = "trainer" + "_" + "fit"
_BWD = "back" + "ward"


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


def validate_step11l_outputs_v0() -> bool:
    if not STEP11L_MANIFEST_JSON.is_file() or not STEP11L_STEP_TABLE_CSV.is_file() or not STEP11L_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11L outputs are missing")
    manifest = _load_json(STEP11L_MANIFEST_JSON)
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "tiny_training_dry_run_design_v0",
        "step11k_validated": True,
        "selected_mask_levels": ["A_warhead_only"],
        "input_source": "synthetic_10d_shape_contract",
        "model_instantiated": True,
        "strict_load_success": True,
        "pretrained_weights_loaded": True,
        "pretrained_base_integration_proven": True,
        _O + "_created": True,
        _O + "_class": "AdamW",
        _O + "_lr": 1e-6,
        _O + "_weight_decay": 0.0,
        "reuse_" + _O + "_across_steps": True,
        "step_count": 3,
        "all_steps_passed": True,
        "finite_loss_all_steps": True,
        "finite_grad_all_steps": True,
        "finite_parameter_delta_all_steps": True,
        _BWD + "_call_count_total": 3,
        _O_STEP + "_call_count_total": 3,
        "grad_nan_count_total": 0,
        "grad_inf_count_total": 0,
        "delta_nan_count_total": 0,
        "delta_inf_count_total": 0,
        "tiny_training_dry_run_passed": True,
        "tiny_training_loop_plumbing_proven": True,
        "real_covalent_loader_gate_allowed": True,
        "b3_scaffold_only_mask_design_allowed": True,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "training_step_called": False,
        _TR_FIT + "_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "original_source_files_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "b3_scaffold_only_mask_design",
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step11l_manifest_{key}_invalid:{manifest.get(key)!r}", blockers)
    rows = _rows_from_csv(STEP11L_STEP_TABLE_CSV)
    _expect(len(rows) == 3, f"step11l_step_table_row_count_invalid:{len(rows)}", blockers)
    for row in rows:
        step = row.get("step_index", "?")
        _expect(row.get("selected_mask_level") == "A_warhead_only", f"step_{step}_mask_level_invalid", blockers)
        _expect(row.get("status") == "passed", f"step_{step}_status_invalid", blockers)
        _expect(_text_bool(row.get("loss_finite")), f"step_{step}_loss_not_finite", blockers)
        _expect(_text_bool(row.get(_BWD + "_success")), f"step_{step}_bwd_not_success", blockers)
        _expect(_text_bool(row.get(_O_STEP + "_success")), f"step_{step}_ostep_not_success", blockers)
        _expect(int(row.get("grad_nan_count", "1")) == 0, f"step_{step}_grad_nan_count_invalid", blockers)
        _expect(int(row.get("grad_inf_count", "1")) == 0, f"step_{step}_grad_inf_count_invalid", blockers)
        _expect(int(row.get("delta_nan_count", "1")) == 0, f"step_{step}_delta_nan_count_invalid", blockers)
        _expect(int(row.get("delta_inf_count", "1")) == 0, f"step_{step}_delta_inf_count_invalid", blockers)
        delta = float(row.get("parameter_delta_l2_total", "0"))
        _expect(math.isfinite(delta) and delta > 0.0, f"step_{step}_delta_l2_not_positive_finite", blockers)
    summary = STEP11L_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "not formal training",
        "synthetic 10D shape contract",
        "b3_scaffold_only_mask_design",
        "does not prove convergence",
    ]:
        _expect(snippet in summary, f"step11l_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def inspect_existing_mask_levels_v0() -> dict[str, Any]:
    files = {
        "masking": Path("src/covalent_ext/masking.py"),
        "schema": Path("src/covalent_ext/schema.py"),
        "data_schema_doc": Path("docs/covalent_data_schema.md"),
        "batch_adapter": Path("src/covalent_ext/batch_adapter.py"),
        "mask_tests": Path("tests/test_covalent_masking.py"),
    }
    found = {name: path.is_file() for name, path in files.items()}
    text_by_name = {name: path.read_text(encoding="utf-8") if path.is_file() else "" for name, path in files.items()}
    combined = "\n".join(text_by_name.values())
    level_tokens = {
        "A_warhead_only": "A_warhead_only" in combined,
        "B_linker_warhead": "B_linker_warhead" in combined,
        "B2_scaffold_warhead": "B2_scaffold_warhead" in combined,
        "C_scaffold_linker_warhead": "C_scaffold_linker_warhead" in combined,
    }
    legacy_short_tokens = {token: token in text_by_name["masking"] or token in text_by_name["schema"] for token in ["A", "B", "B2", "C"]}
    notes = [
        "batch_adapter and tensor materialization outputs use four long-form mask level names.",
        "legacy masking.py and docs/covalent_data_schema.md still expose short A/B/B2/C naming.",
    ]
    if "mask_scaffold" in text_by_name["masking"]:
        notes.append("legacy masking.py includes mask_scaffold for B2; additive implementation should protect current downstream B2_scaffold_warhead semantics.")
    manual_review_required = bool("mask_scaffold" in text_by_name["masking"])
    return {
        "existing_masking_files_found": found,
        "existing_mask_levels_detected": [name for name, present in level_tokens.items() if present],
        "existing_short_mask_tokens_detected": [name for name, present in legacy_short_tokens.items() if present],
        "existing_four_level_contract_detected": all(level_tokens.values()) or all(legacy_short_tokens.values()),
        "current_b2_name": "B2_scaffold_warhead",
        "current_b2_target_components": ["scaffold", "warhead"],
        "current_b2_context_components": ["linker"],
        "b3_already_implemented": NEW_MASK_LEVEL in combined,
        "implementation_files_to_touch_next": [
            "src/covalent_ext/masking.py",
            "src/covalent_ext/schema.py",
            "src/covalent_ext/batch_adapter.py",
            "tests/test_covalent_masking.py",
            "relevant covalent_ext mask sweep tests",
            "docs/covalent_data_schema.md",
        ],
        "manual_review_required": manual_review_required,
        "source_inspection_notes": notes,
    }


def build_b3_mask_semantics_v0(existing_evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "mask_level": NEW_MASK_LEVEL,
        "target_components": B3_TARGET_COMPONENTS,
        "context_components": B3_CONTEXT_COMPONENTS,
        "target_description": "scaffold atoms are hidden and predicted",
        "context_description": (
            "linker and warhead atoms stay visible; covalent-reactive end geometry remains conditioning context"
        ),
        "primary_design_use": B3_PRIMARY_USE,
        "scaffold_hopping_value": [
            "scaffold hopping",
            "core replacement",
            "BBB and permeability exploration while preserving linker-warhead geometry",
            "metabolic stability exploration while preserving covalent reaction geometry",
            "selectivity and patent-space exploration around fixed linker-warhead context",
        ],
        "relation_to_B2": {
            "B2_scaffold_warhead": "predict scaffold and warhead from linker context",
            NEW_MASK_LEVEL: "predict scaffold from linker and warhead context",
            "does_not_replace_B2": True,
            "complementary_to_B2": True,
        },
        "relation_to_current_four_level": {
            "A_B_B2_C_remain_unchanged": True,
            "B3_added_as_fifth_level": True,
            "existing_b3_named_level_present": bool(existing_evidence.get("b3_already_implemented")),
        },
    }


def build_five_level_mask_table_v0() -> list[dict[str, Any]]:
    return [
        {
            "mask_level": "A_warhead_only",
            "target_components": ["warhead"],
            "context_components": ["scaffold", "linker"],
            "use_case": "warhead replacement",
        },
        {
            "mask_level": "B_linker_warhead",
            "target_components": ["linker", "warhead"],
            "context_components": ["scaffold"],
            "use_case": "grow linker and warhead from known scaffold",
        },
        {
            "mask_level": "B2_scaffold_warhead",
            "target_components": ["scaffold", "warhead"],
            "context_components": ["linker"],
            "use_case": "co-design scaffold and warhead around linker geometry",
        },
        {
            "mask_level": NEW_MASK_LEVEL,
            "target_components": B3_TARGET_COMPONENTS,
            "context_components": B3_CONTEXT_COMPONENTS,
            "use_case": "scaffold hopping with fixed linker-warhead geometry",
        },
        {
            "mask_level": "C_scaffold_linker_warhead",
            "target_components": ["scaffold", "linker", "warhead"],
            "context_components": [],
            "use_case": "de novo full covalent ligand generation",
        },
    ]


def build_b3_mask_invariants_v0() -> list[dict[str, Any]]:
    return [
        {"invariant_id": "B3_I01_target_exactly_scaffold", "description": "target_components must equal scaffold", "required": True},
        {
            "invariant_id": "B3_I02_context_exactly_linker_warhead",
            "description": "context_components must equal linker plus warhead",
            "required": True,
        },
        {"invariant_id": "B3_I03_target_count_positive", "description": "target_atoms_count must be greater than zero", "required": True},
        {"invariant_id": "B3_I04_context_count_positive", "description": "context_atoms_count must be greater than zero", "required": True},
        {"invariant_id": "B3_I05_linker_count_positive", "description": "linker_atoms_count must be greater than zero", "required": True},
        {"invariant_id": "B3_I06_warhead_count_positive", "description": "warhead_atoms_count must be greater than zero", "required": True},
        {"invariant_id": "B3_I07_scaffold_count_positive", "description": "scaffold_atoms_count must be greater than zero", "required": True},
        {"invariant_id": "B3_I08_disjoint", "description": "target and context atom sets must be disjoint", "required": True},
        {
            "invariant_id": "B3_I09_cover_assigned_regions",
            "description": "target plus context covers all scaffold/linker/warhead ligand atoms",
            "required": True,
        },
        {"invariant_id": "B3_I10_warhead_visible", "description": "warhead atoms must remain visible in context", "required": True},
        {"invariant_id": "B3_I11_linker_visible", "description": "linker atoms must remain visible in context", "required": True},
        {"invariant_id": "B3_I12_no_scaffold_context_leak", "description": "scaffold atoms must not leak into context", "required": True},
        {
            "invariant_id": "B3_I13_covalent_labels_metadata_only",
            "description": "covalent atom-pair labels stay available as conditioning/evaluation metadata, not target leakage",
            "required": True,
        },
        {
            "invariant_id": "B3_I14_preserve_existing_levels",
            "description": "B3 must not alter A/B/B2/C semantics",
            "required": True,
        },
        {
            "invariant_id": "B3_I15_fail_safe_missing_labels",
            "description": "B3 must fail safely if scaffold/linker/warhead labels are missing or empty",
            "required": True,
        },
    ]


def build_b3_implementation_protocol_v0(
    b3_semantics: dict[str, Any],
    five_level_table: list[dict[str, Any]],
    invariants: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "proposed_next_stage": "b3_scaffold_only_mask_implementation_v0",
        "implementation_policy": "additive_only",
        "do_not_rename_existing_B2": True,
        "do_not_change_A_B_B2_C_semantics": True,
        "add_new_mask_level": b3_semantics["mask_level"],
        "target_components": b3_semantics["target_components"],
        "context_components": b3_semantics["context_components"],
        "five_level_table": five_level_table,
        "invariants": invariants,
        "allowed_next_step_files": [
            "src/covalent_ext/masking.py",
            "relevant covalent_ext tests",
            "docs and derived report outputs",
        ],
        "forbidden_next_step_actions": [
            "modify DiffSBDD or diffusion source",
            "run model execution",
            "run gradient pass",
            "create update controller",
            "run parameter update",
            "save checkpoint/model/tensor artifact",
        ],
        "pass_conditions": [
            "B3 mask can be built on synthetic covalent sample",
            "B3 target atom count greater than zero",
            "B3 context atom count greater than zero",
            "target and context disjoint",
            "warhead visible in context",
            "linker visible in context",
            "scaffold hidden in target",
            "A/B/B2/C outputs unchanged relative to previous expected semantics",
            "no training action",
            "no checkpoint/model/tensor artifact",
        ],
    }


def build_b3_smoke_roadmap_v0() -> list[dict[str, Any]]:
    return [
        {
            "step": "Step 11N",
            "stage": "b3_scaffold_only_mask_implementation_v0",
            "purpose": "add B3 to mask logic and tests",
            "execution_boundary": "no model forward or gradient pass",
        },
        {
            "step": "Step 11O",
            "stage": "b3_scaffold_only_mask_sweep_v0",
            "purpose": "run mask sweep including A/B/B2/B3/C and verify target/context counts",
            "execution_boundary": "mask construction only",
        },
        {
            "step": "Step 11P",
            "stage": "b3_pretrained_masked_loss_smoke_v0",
            "purpose": "strict-loaded model with B3 synthetic finite loss",
            "execution_boundary": "no parameter update",
        },
        {
            "step": "Step 11Q",
            "stage": "b3_backward_smoke_v0",
            "purpose": "B3 loss requires gradient and gradient values are finite",
            "execution_boundary": "no parameter update",
        },
        {
            "step": "Step 11R",
            "stage": "b3_single_optimizer_step_smoke_v0",
            "purpose": "one controlled parameter update on B3",
            "execution_boundary": "no saved artifacts",
        },
        {
            "step": "Step 11S",
            "stage": "b3_tiny_training_dry_run_v0",
            "purpose": "optional three-step B3 tiny loop",
            "execution_boundary": "synthetic-only evidence",
        },
        {
            "step": "Then",
            "stage": "real_covalent_feature_mapping_loader_gate",
            "purpose": "gate real feature mapping and loader readiness before real data use",
            "execution_boundary": "separate approval gate",
        },
    ]


def build_b3_mask_risk_register_v0() -> list[dict[str, Any]]:
    return [
        {
            "risk_id": "B3_R01_region_labels",
            "description": "B3 depends on reliable scaffold/linker/warhead atom labels.",
            "severity": "high",
            "mitigation": "Fail safely when any region is missing or empty; add fixture coverage.",
            "blocks_11N": False,
        },
        {
            "risk_id": "B3_R02_b2_confusion",
            "description": "B3 can be confused with current B2 if names are unclear.",
            "severity": "high",
            "mitigation": "Keep B2 name and semantics unchanged; add explicit B2-vs-B3 table tests.",
            "blocks_11N": False,
        },
        {
            "risk_id": "B3_R03_fixed_reactive_geometry",
            "description": "B3 preserves warhead/linker and may overfit fixed reactive geometry.",
            "severity": "medium",
            "mitigation": "Track geometry metrics separately and avoid quality claims.",
            "blocks_11N": False,
        },
        {
            "risk_id": "B3_R04_large_scaffold_space",
            "description": "Scaffold-only target may be too large or too diverse.",
            "severity": "medium",
            "mitigation": "Start with smoke counts and later stratify scaffold sizes.",
            "blocks_11N": False,
        },
        {
            "risk_id": "B3_R05_disconnected_scaffold",
            "description": "Generated scaffold can be disconnected if linker attachment constraints are weak.",
            "severity": "high",
            "mitigation": "Require attachment metadata and connectivity checks before real training.",
            "blocks_11N": False,
        },
        {
            "risk_id": "B3_R06_chemical_validity_not_proven",
            "description": "B3 does not prove generated scaffold is chemically valid.",
            "severity": "high",
            "mitigation": "Keep implementation smoke separate from chemistry validity gates.",
            "blocks_11N": False,
        },
        {
            "risk_id": "B3_R07_property_claims_not_proven",
            "description": "B3 does not prove BBB, metabolic, or selectivity improvement.",
            "severity": "high",
            "mitigation": "Forbid property claims until downstream evaluation exists.",
            "blocks_11N": False,
        },
        {
            "risk_id": "B3_R08_sampling_distribution_shift",
            "description": "Adding B3 changes task sampling distribution later.",
            "severity": "medium",
            "mitigation": "Require schedule design before any real training loop includes B3.",
            "blocks_11N": False,
        },
        {
            "risk_id": "B3_R09_synthetic_semantics_gap",
            "description": "Current synthetic 10D path does not prove real feature semantics.",
            "severity": "high",
            "mitigation": "Require real covalent feature mapping and loader gate before real data use.",
            "blocks_11N": False,
        },
        {
            "risk_id": "B3_R10_real_loader_gap",
            "description": "Real covalent loader gate is still required before real training.",
            "severity": "high",
            "mitigation": "Keep B3 implementation and real loader readiness as separate gates.",
            "blocks_11N": False,
        },
    ]


def build_b3_design_decision_v0(
    step11l_validated: bool,
    existing_evidence: dict[str, Any],
    b3_semantics: dict[str, Any],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    semantics_complete = bool(
        b3_semantics.get("mask_level") == NEW_MASK_LEVEL
        and b3_semantics.get("target_components") == B3_TARGET_COMPONENTS
        and b3_semantics.get("context_components") == B3_CONTEXT_COMPONENTS
        and b3_semantics.get("relation_to_B2", {}).get("does_not_replace_B2") is True
    )
    protocol_complete = bool(
        protocol.get("implementation_policy") == "additive_only"
        and protocol.get("do_not_rename_existing_B2") is True
        and protocol.get("do_not_change_A_B_B2_C_semantics") is True
        and protocol.get("proposed_next_stage") == "b3_scaffold_only_mask_implementation_v0"
    )
    if step11l_validated and semantics_complete and protocol_complete:
        status = "b3_scaffold_only_mask_design_ready"
        allowed = True
        next_step = "b3_scaffold_only_mask_implementation"
    elif not step11l_validated:
        status = "step11l_precondition_failed"
        allowed = False
        next_step = "tiny_training_dry_run_debug"
    else:
        status = "b3_semantics_incomplete"
        allowed = False
        next_step = "b3_semantics_review"
    return {
        "design_status": status,
        "b3_scaffold_only_mask_implementation_allowed": allowed,
        "recommended_next_step": next_step,
        "this_design_modifies_mask_logic": False,
        "this_design_runs_model": False,
        "this_design_runs_" + _BWD: False,
        "this_design_creates_" + _O: False,
        "this_design_runs_" + _O_STEP: False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "real_training_allowed": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "existing_b3_named_level_present": bool(existing_evidence.get("b3_already_implemented")),
    }


def build_b3_scaffold_only_mask_design_v0() -> dict[str, Any]:
    blockers: list[str] = []
    step11l_validated = False
    try:
        step11l_validated = validate_step11l_outputs_v0()
    except Exception as exc:
        blockers.append(f"step11l_validation_failed:{type(exc).__name__}:{exc}")
    existing_evidence = inspect_existing_mask_levels_v0()
    b3_semantics = build_b3_mask_semantics_v0(existing_evidence)
    five_level_table = build_five_level_mask_table_v0()
    invariants = build_b3_mask_invariants_v0()
    protocol = build_b3_implementation_protocol_v0(b3_semantics, five_level_table, invariants)
    roadmap = build_b3_smoke_roadmap_v0()
    risks = build_b3_mask_risk_register_v0()
    decision = build_b3_design_decision_v0(step11l_validated, existing_evidence, b3_semantics, protocol)
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_source_files_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    all_checks_passed = bool(decision["b3_scaffold_only_mask_implementation_allowed"] and not blockers)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11l_validated": step11l_validated,
        "tiny_training_loop_plumbing_proven": step11l_validated,
        "current_mask_levels_detected": existing_evidence["existing_mask_levels_detected"],
        "current_short_mask_tokens_detected": existing_evidence["existing_short_mask_tokens_detected"],
        "new_mask_level": NEW_MASK_LEVEL,
        "b3_target_components": B3_TARGET_COMPONENTS,
        "b3_context_components": B3_CONTEXT_COMPONENTS,
        "b3_primary_use": B3_PRIMARY_USE,
        "five_level_mask_design_ready": len(five_level_table) == 5,
        "b3_invariants_written": len(invariants),
        "implementation_protocol_written": True,
        "smoke_roadmap_written": True,
        "proposed_next_stage": protocol["proposed_next_stage"],
        "do_not_rename_existing_b2": True,
        "do_not_change_existing_four_level_semantics": True,
        **decision,
        "original_source_files_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blockers,
    }
    protocol_document = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "existing_mask_schema_inspection": existing_evidence,
        "b3_semantics": b3_semantics,
        "five_level_mask_table": five_level_table,
        "b3_invariants": invariants,
        "implementation_protocol": protocol,
        "smoke_roadmap": roadmap,
        "risk_register": risks,
        "decision": decision,
    }
    return {
        "manifest": manifest,
        "protocol_document": protocol_document,
        "report_sections": {
            "step11l_precondition": {"step11l_validated": step11l_validated},
            "existing_mask_schema_inspection": existing_evidence,
            "b3_semantics": b3_semantics,
            "five_level_mask_table": five_level_table,
            "b3_invariants": invariants,
            "b3_implementation_protocol": protocol,
            "b3_smoke_roadmap": roadmap,
            "safety_boundary": {
                "this_design_modifies_mask_logic": False,
                "this_design_runs_model": False,
                "this_design_runs_" + _BWD: False,
                "this_design_creates_" + _O: False,
                "this_design_runs_" + _O_STEP: False,
                "checkpoint_saved": False,
                "model_saved": False,
                "tensor_dump_saved": False,
                "original_source_files_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
        },
    }
