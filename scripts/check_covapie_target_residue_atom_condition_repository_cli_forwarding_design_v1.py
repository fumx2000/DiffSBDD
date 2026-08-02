#!/usr/bin/env python3
"""Check the repository CLI forwarding design V1 without publishing files."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1 as design,
)


SOURCE_BUNDLE = (
    ROOT.parent
    / "covapie-state/manual-review/"
    "covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1.json"
)


def _emit(name: str, value: object) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    print(f"{name}={rendered}")


def evaluate() -> tuple[dict[str, object], dict[str, object]]:
    source = SOURCE_BUNDLE.read_bytes()
    response = design.design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1(
        source_model_consumption_gate_bundle=source,
        repo_root=ROOT,
    )
    gate = design._gate_source_evidence(ROOT)
    audit = design._caller_audit(ROOT)
    checkpoint = response["selected_conditioned_checkpoint_load_strategy"]
    helper = response["selected_checkpoint_migration_helper"]
    generate = response["selected_generate_ligands_forwarding_contract"]
    inpaint = response["selected_covalent_inpaint_forwarding_contract"]
    masks = response["selected_mask_semantic_normalization_contract"]
    inventory = masks["legacy_reference_inventory"]
    dependency = masks["retirement_dependency_order_evidence"]
    baseline = masks["runtime_design_baseline_source_evidence"]
    lifecycle = design._design_path_lifecycle_evidence(ROOT)
    ordered_steps = {
        item["step"]: item
        for item in masks["future_retirement_implementation_scope"][
            "ordered_steps"
        ]
    }
    deferrals = {
        item["caller"]: item for item in response["deferred_callers"]
    }

    facts: dict[str, object] = {
        "source_model_consumption_gate_bundle_bound": (
            hashlib.sha256(source).hexdigest()
            == response[
                "source_model_consumption_gate_bundle_transport_sha256"
            ]
        ),
        "source_model_consumption_gate_commit_bound": gate[
            "gate_commit_metadata_bound"
        ]
        and gate["gate_four_file_identity_bound"],
        "source_model_consumption_gate_commit_is_head_ancestor": gate[
            "gate_commit_is_head_ancestor"
        ],
        "source_model_consumption_gate_commit_is_origin_main_ancestor": gate[
            "gate_commit_is_origin_main_ancestor"
        ],
        "all_six_callers_bound": len(audit["by_caller"]) == 6,
        "audited_caller_count": response["audited_caller_count"],
        "audited_checkpoint_load_site_count": response[
            "audited_checkpoint_load_site_count"
        ],
        "audited_model_generate_ligands_call_count": response[
            "audited_model_generate_ligands_call_count"
        ],
        "audited_prepare_pocket_direct_call_count": response[
            "audited_prepare_pocket_direct_call_count"
        ],
        "audited_ddpm_inpaint_direct_call_count": response[
            "audited_ddpm_inpaint_direct_call_count"
        ],
        "audited_ddpm_diversify_direct_call_count": response[
            "audited_ddpm_diversify_direct_call_count"
        ],
        "notebook_json_cell_source_audited": audit[
            "notebook_json_cell_source_audited"
        ],
        "selected_v1_supported_caller_count": len(
            response["selected_v1_supported_callers"]
        ),
        "selected_generate_ligands_cli": (
            response["selected_v1_supported_callers"][0]
            == "generate_ligands.py"
        ),
        "selected_covalent_inpaint_demo_cli": (
            response["selected_v1_supported_callers"][1]
            == "scripts/covalent_inpaint_demo.py"
        ),
        "deferred_caller_count": len(deferrals),
        "test_manifest_required": (
            deferrals["test.py"]["required_successor_contract"]
            == "canonical_per_sample_target_manifest"
        ),
        "optimize_deferred": deferrals["optimize.py"]["deferred"],
        "generic_inpaint_deferred": deferrals["inpaint.py"]["deferred"],
        "colab_distribution_strategy_required": (
            deferrals["colab/DiffSBDD.ipynb"]["ui_only_change_cannot_claim_support"]
            is True
        ),
        "exact6_selector_contract_defined": (
            response["selected_exact6_compilation_contract"]["selector_type"]
            == "Exact6"
        ),
        "legacy_mode_contract_defined": response["selected_legacy_mode_contract"][
            "generate_ligands_non_mask_behavior_unchanged"
        ],
        "conditioned_mode_contract_defined": response[
            "selected_conditioned_mode_contract"
        ]["conditioned_mode"],
        "conditioned_checkpoint_hyperparameters_audited": (
            checkpoint["hyper_parameters_type"] == "dict"
            and len(checkpoint["hyper_parameters_keys"]) == 21
            and checkpoint["state_dict_key_count"] == 122
            and checkpoint["mode"] == "pocket_conditioning"
            and checkpoint["pocket_representation"] == "full-atom"
            and checkpoint["joint_nf"] == 32
        ),
        "conditioned_checkpoint_enabled_model_constructed": checkpoint[
            "enabled_model_constructed"
        ],
        "base_to_conditioned_exactly_one_key_filled": checkpoint[
            "exactly_one_key_filled"
        ],
        "base_to_conditioned_final_strict_load": checkpoint[
            "final_strict_load"
        ],
        "base_to_conditioned_blanket_strict_false": checkpoint[
            "blanket_strict_false"
        ],
        "checkpoint_file_modified": checkpoint["checkpoint_file_modified"],
        "central_cli_helper_selected": helper["central_module"].endswith(
            "covapie_target_residue_atom_condition_repository_cli_v1.py"
        ),
        "duplicate_loader_logic_allowed": helper[
            "duplicate_parser_or_loader_logic_allowed"
        ],
        "generate_ligands_forwarding_contract_defined": (
            generate["selector_forwarding_site_count"] == 1
            and generate["forward_keyword"]
            == "target_residue_atom_condition_spec"
        ),
        "covalent_inpaint_forwarding_contract_defined": (
            inpaint["prepare_pocket_selector_forwarding_site_count"] == 1
            and inpaint["manual_indicator_creation_allowed"] is False
        ),
        "canonical_five_level_target_selected": masks[
            "canonical_five_level_target_selected"
        ],
        "legacy_four_level_retirement_selected": masks[
            "legacy_four_level_retirement_selected"
        ],
        "legacy_four_level_retirement_implemented": masks[
            "legacy_four_level_retirement_implemented"
        ],
        "design_evidence_mode": masks["design_evidence_mode"],
        "runtime_design_baseline_commit": masks[
            "runtime_design_baseline_commit"
        ],
        "runtime_design_baseline_commit_is_head_ancestor": baseline[
            "runtime_design_baseline_commit_is_head_ancestor"
        ],
        "runtime_design_baseline_commit_is_origin_main_ancestor": baseline[
            "runtime_design_baseline_commit_is_origin_main_ancestor"
        ],
        "design_checker_claims_live_runtime_state": masks[
            "design_checker_claims_live_runtime_state"
        ],
        "implementation_phase_live_state_requires_phase_specific_gate": masks[
            "implementation_phase_live_state_requires_phase_specific_gate"
        ],
        "recommended_next_step_is_design_baseline_recommendation": masks[
            "recommended_next_step_is_design_baseline_recommendation"
        ],
        "R1_candidate_will_not_invalidate_design_tests": masks[
            "R1_candidate_will_not_invalidate_design_tests"
        ],
        "baseline_legacy_provider_has_active_consumers": dependency[
            "legacy_provider_has_active_consumers"
        ],
        "baseline_legacy_demo_imports_four_level_builder": dependency[
            "legacy_demo_imports_four_level_builder"
        ],
        "baseline_legacy_demo_calls_four_level_builder": dependency[
            "legacy_demo_calls_four_level_builder"
        ],
        "baseline_legacy_demo_mask_level_flag_present": dependency[
            "legacy_demo_mask_level_flag_present"
        ],
        "consumer_migration_step": dependency["consumer_migration_step"],
        "provider_removal_step": dependency["provider_removal_step"],
        "consumer_migration_precedes_provider_removal": dependency[
            "consumer_migration_precedes_provider_removal"
        ],
        "provider_removal_precedes_consumer_migration": dependency[
            "provider_removal_precedes_consumer_migration"
        ],
        "no_intermediate_missing_import_state": dependency[
            "no_intermediate_missing_import_state"
        ],
        "retirement_dependency_order_valid": masks[
            "retirement_dependency_order_valid"
        ],
        "baseline_reference_count": masks["baseline_reference_count"],
        "baseline_active_legacy_reference_count": masks[
            "baseline_active_legacy_reference_count"
        ],
        "baseline_active_legacy_reference_path_count": masks[
            "baseline_active_legacy_reference_path_count"
        ],
        "target_active_legacy_reference_count": masks[
            "target_active_legacy_reference_count"
        ],
        "target_active_legacy_reference_path_count": masks[
            "target_active_legacy_reference_path_count"
        ],
        "historical_read_only_legacy_evidence_retained": masks[
            "historical_read_only_legacy_evidence_retained"
        ],
        "target_legacy_four_level_cli_input_supported": masks[
            "target_legacy_four_level_cli_input_supported"
        ],
        "target_legacy_automatic_translation_allowed": masks[
            "target_legacy_automatic_translation_allowed"
        ],
        "canonical_mask_input_flag": masks["canonical_input_flag"],
        "legacy_mask_input_flag": masks["legacy_input_flag"],
        "target_short_alias_input_supported": masks[
            "target_legacy_short_alias_input_supported"
        ],
        "short_alias_report_only": masks["short_alias_report_only"],
        "canonical_mask_count": masks["canonical_mask_count"],
        "scaffold_plus_warhead_present": masks[
            "scaffold_plus_warhead_present"
        ],
        "scaffold_only_present": masks["scaffold_only_present"],
        "sixth_mask_added": masks["sixth_mask_added"],
        "canonical_B2_is_scaffold_plus_warhead": masks[
            "canonical_B2_semantic"
        ]
        == "scaffold_plus_warhead",
        "canonical_B3_is_scaffold_only": masks["canonical_B3_semantic"]
        == "scaffold_only",
        "ambiguous_legacy_B2_reinterpretation_allowed": masks[
            "ambiguous_legacy_B2_reinterpretation_allowed"
        ],
        "legacy_reference_inventory_complete": inventory[
            "inventory_complete"
        ],
        "design_lifecycle_profile": lifecycle["design_lifecycle_profile"],
        "design_paths_all_tracked": lifecycle["design_paths_all_tracked"],
        "design_paths_all_untracked": lifecycle[
            "design_paths_all_untracked"
        ],
        "ordinary_untracked_count": lifecycle["ordinary_untracked_count"],
        "known_future_task_untracked_count": lifecycle[
            "known_future_task_untracked_count"
        ],
        "unknown_ordinary_untracked_count": lifecycle[
            "unknown_ordinary_untracked_count"
        ],
        "known_future_task_untracked_paths_supported": lifecycle[
            "known_future_task_untracked_paths_supported"
        ],
        "unknown_untracked_paths_rejected": lifecycle[
            "unknown_untracked_paths_rejected"
        ],
        "post_commit_inventory_supported": (
            lifecycle["design_lifecycle_profile"]
            in {
                "design_successor_worktree",
                "published_design_with_known_future_task",
            }
            and lifecycle["design_paths_all_tracked"] is True
            and lifecycle["ordinary_untracked_paths"]
            == lifecycle["known_future_task_untracked_paths"]
            and lifecycle["unknown_ordinary_untracked_count"] == 0
            and inventory["baseline_reference_count"] == 45
            and inventory["baseline_active_legacy_reference_count"] == 14
            and inventory["baseline_unresolved_active_reference_count"] == 0
        ),
        "inventory_baseline_reference_count": inventory[
            "baseline_reference_count"
        ],
        "inventory_baseline_active_reference_count": inventory[
            "baseline_active_legacy_reference_count"
        ],
        "inventory_baseline_unresolved_active_reference_count": inventory[
            "baseline_unresolved_active_reference_count"
        ],
        "all_active_legacy_references_in_future_scope": inventory[
            "all_active_legacy_references_in_future_scope"
        ],
        "retirement_R1_scope_complete": {
            "scripts/covalent_inpaint_demo.py",
            "tests/test_covalent_inpaint_demo_mask_semantic_v1.py",
        } == set(ordered_steps["R1"]["paths"])
        and ordered_steps["R1"]["completion_contract"][
            "legacy_four_level_core_provider_still_present"
        ]
        is True,
        "retirement_R2_scope_complete": (
            {
                "src/covalent_ext/masking.py",
                "src/covalent_ext/schema.py",
                "src/covalent_ext/dataset.py",
                "scripts/check_covalent_masking.py",
                "tests/test_covalent_masking.py",
                "tests/test_b3_scaffold_only_mask_implementation_v0.py",
            }
            == set(ordered_steps["R2"]["paths"])
            and ordered_steps["R2"]["completion_contract"][
                "R3_independent_gate_required"
            ]
            is True
        ),
        "retirement_R3_gate_required": masks[
            "zero_active_legacy_reference_retirement_gate_contract"
        ]["gate_must_pass_and_be_committed_before_C1"],
        "ready_for_covalent_demo_canonical_mask_migration_R1": masks[
            "ready_for_covalent_demo_canonical_mask_migration_R1"
        ],
        "ready_for_legacy_core_api_retirement_R2": masks[
            "ready_for_legacy_core_api_retirement_R2"
        ],
        "target_enable_flag_exact_bool_required": response[
            "selected_conditioned_mode_contract"
        ]["target_enable_flag_exact_bool_required"],
        "repository_cli_selector_forwarding_implemented": response[
            "repository_cli_selector_forwarding_implemented"
        ],
        "ready_for_repository_cli_forwarding_implementation": response[
            "ready_for_repository_cli_forwarding_implementation"
        ],
        "recommended_next_step": response["recommended_next_step"],
        "training_or_parameter_update": response[
            "training_or_parameter_update"
        ],
        "feature_semantics_audit_required_before_training": response[
            "feature_semantics_audit_required_before_training"
        ],
        "repository_cli_forwarding_design_response_sha256": response[
            "repository_cli_forwarding_design_response_sha256"
        ],
    }

    required_true = {
        "source_model_consumption_gate_bundle_bound",
        "source_model_consumption_gate_commit_bound",
        "source_model_consumption_gate_commit_is_head_ancestor",
        "source_model_consumption_gate_commit_is_origin_main_ancestor",
        "all_six_callers_bound",
        "notebook_json_cell_source_audited",
        "selected_generate_ligands_cli",
        "selected_covalent_inpaint_demo_cli",
        "test_manifest_required",
        "optimize_deferred",
        "generic_inpaint_deferred",
        "colab_distribution_strategy_required",
        "exact6_selector_contract_defined",
        "legacy_mode_contract_defined",
        "conditioned_mode_contract_defined",
        "conditioned_checkpoint_hyperparameters_audited",
        "conditioned_checkpoint_enabled_model_constructed",
        "base_to_conditioned_exactly_one_key_filled",
        "base_to_conditioned_final_strict_load",
        "central_cli_helper_selected",
        "generate_ligands_forwarding_contract_defined",
        "covalent_inpaint_forwarding_contract_defined",
        "canonical_five_level_target_selected",
        "legacy_four_level_retirement_selected",
        "runtime_design_baseline_commit_is_head_ancestor",
        "runtime_design_baseline_commit_is_origin_main_ancestor",
        "implementation_phase_live_state_requires_phase_specific_gate",
        "recommended_next_step_is_design_baseline_recommendation",
        "R1_candidate_will_not_invalidate_design_tests",
        "baseline_legacy_provider_has_active_consumers",
        "baseline_legacy_demo_imports_four_level_builder",
        "baseline_legacy_demo_calls_four_level_builder",
        "baseline_legacy_demo_mask_level_flag_present",
        "consumer_migration_precedes_provider_removal",
        "no_intermediate_missing_import_state",
        "retirement_dependency_order_valid",
        "historical_read_only_legacy_evidence_retained",
        "short_alias_report_only",
        "scaffold_plus_warhead_present",
        "scaffold_only_present",
        "canonical_B2_is_scaffold_plus_warhead",
        "canonical_B3_is_scaffold_only",
        "legacy_reference_inventory_complete",
        "design_paths_all_tracked",
        "known_future_task_untracked_paths_supported",
        "unknown_untracked_paths_rejected",
        "post_commit_inventory_supported",
        "all_active_legacy_references_in_future_scope",
        "retirement_R1_scope_complete",
        "retirement_R2_scope_complete",
        "retirement_R3_gate_required",
        "ready_for_covalent_demo_canonical_mask_migration_R1",
        "target_enable_flag_exact_bool_required",
        "feature_semantics_audit_required_before_training",
    }
    if not all(facts[name] is True for name in required_true):
        raise ValueError(design._ERROR)
    expected_counts = {
        "audited_caller_count": 6,
        "audited_checkpoint_load_site_count": 6,
        "audited_model_generate_ligands_call_count": 3,
        "audited_prepare_pocket_direct_call_count": 3,
        "audited_ddpm_inpaint_direct_call_count": 3,
        "audited_ddpm_diversify_direct_call_count": 1,
        "selected_v1_supported_caller_count": 2,
        "deferred_caller_count": 4,
        "canonical_mask_count": 5,
        "baseline_reference_count": 45,
        "baseline_active_legacy_reference_count": 14,
        "baseline_active_legacy_reference_path_count": 5,
        "target_active_legacy_reference_count": 0,
        "target_active_legacy_reference_path_count": 0,
        "unknown_ordinary_untracked_count": 0,
        "inventory_baseline_reference_count": 45,
        "inventory_baseline_active_reference_count": 14,
        "inventory_baseline_unresolved_active_reference_count": 0,
    }
    if any(facts[name] != expected for name, expected in expected_counts.items()):
        raise ValueError(design._ERROR)
    required_false = {
        "base_to_conditioned_blanket_strict_false",
        "checkpoint_file_modified",
        "duplicate_loader_logic_allowed",
        "legacy_four_level_retirement_implemented",
        "design_checker_claims_live_runtime_state",
        "provider_removal_precedes_consumer_migration",
        "ready_for_legacy_core_api_retirement_R2",
        "target_legacy_four_level_cli_input_supported",
        "target_legacy_automatic_translation_allowed",
        "target_short_alias_input_supported",
        "ambiguous_legacy_B2_reinterpretation_allowed",
        "sixth_mask_added",
        "design_paths_all_untracked",
        "repository_cli_selector_forwarding_implemented",
        "ready_for_repository_cli_forwarding_implementation",
        "training_or_parameter_update",
    }
    if not all(facts[name] is False for name in required_false):
        raise ValueError(design._ERROR)
    if facts["recommended_next_step"] != (
        "implement_covapie_covalent_demo_canonical_five_level_mask_migration_r1_v1"
    ):
        raise ValueError(design._ERROR)
    if (
        facts["consumer_migration_step"] != "R1"
        or facts["provider_removal_step"] != "R2"
    ):
        raise ValueError(design._ERROR)
    if facts["design_evidence_mode"] != "frozen_runtime_baseline_snapshot":
        raise ValueError(design._ERROR)
    if facts["runtime_design_baseline_commit"] != (
        design._RUNTIME_DESIGN_BASELINE_COMMIT
    ):
        raise ValueError(design._ERROR)
    if facts["design_lifecycle_profile"] not in {
        "design_successor_worktree",
        "published_design_with_known_future_task",
    }:
        raise ValueError(design._ERROR)
    if facts["ordinary_untracked_count"] != facts[
        "known_future_task_untracked_count"
    ]:
        raise ValueError(design._ERROR)
    if (
        facts["canonical_mask_input_flag"] != "--mask_semantic"
        or facts["legacy_mask_input_flag"] is not None
    ):
        raise ValueError(design._ERROR)
    return response, facts


def main() -> int:
    _response, facts = evaluate()
    for name, value in facts.items():
        _emit(name, value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
