#!/usr/bin/env python3
"""Check the CovaPIE target-residue model-consumption design V1."""

from __future__ import annotations

import hashlib
from pathlib import Path

import torch

from covalent_ext import covapie_target_residue_atom_condition_model_consumption_design_v1 as design
from covalent_ext import covapie_target_residue_atom_condition_runtime_bridge_gate_v1 as gate


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = (
    ROOT.parent
    / "covapie-state/manual-review"
    / "covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1.json"
)


def _emit(name: str, value: object) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    print(f"{name}={rendered}")


def _synthetic_oracles() -> dict[str, bool]:
    hidden = torch.arange(20, dtype=torch.float32).reshape(5, 4)
    indicator = torch.tensor([False, False, True, False, False])
    zero = torch.zeros(4)
    nonzero = torch.tensor([1.0, -2.0, 3.0, -4.0])
    zero_out = hidden + indicator[:, None] * zero[None]
    changed = hidden + indicator[:, None] * nonzero[None]
    permutation = torch.tensor([3, 1, 4, 0, 2])
    permuted = hidden[permutation] + indicator[permutation, None] * nonzero[None]
    jacobian = indicator.to(torch.float32)[:, None, None] * torch.eye(4)[None]
    return {
        "zero_initialization_parity": torch.equal(zero_out, hidden),
        "nonzero_target_row_changed": torch.equal(changed[2], hidden[2] + nonzero),
        "non_target_rows_unchanged": torch.equal(changed[~indicator], hidden[~indicator]),
        "synthetic_gradient_path_exists": (
            torch.equal(jacobian[2], torch.eye(4))
            and torch.count_nonzero(jacobian[~indicator]).item() == 0
        ),
        "node_permutation_alignment_preserved": torch.equal(
            changed[permutation], permuted
        ),
    }


def check() -> dict[str, object]:
    source_bundle = BUNDLE.read_bytes()
    source_snapshot = bytes(source_bundle)
    decoded = gate._strict_json(source_bundle)
    first = design.design_covapie_target_residue_atom_condition_model_consumption_v1(
        source_runtime_bridge_gate_bundle=source_bundle,
        repo_root=ROOT,
    )
    second = design.design_covapie_target_residue_atom_condition_model_consumption_v1(
        source_runtime_bridge_gate_bundle=source_bundle,
        repo_root=ROOT,
    )
    if first != second or source_bundle != source_snapshot:
        raise ValueError(design._ERROR)

    gate_commit_is_head_ancestor = design._git_commit_is_ancestor(
        repo_root=ROOT,
        base_commit=design._GATE_COMMIT,
        head_ref="HEAD",
    )
    gate_commit_is_origin_main_ancestor = design._git_commit_is_ancestor(
        repo_root=ROOT,
        base_commit=design._GATE_COMMIT,
        head_ref="origin/main",
    )

    profile = first["checkpoint_profile"]
    compatibility = first["existing_state_dict_compatibility_decision"]
    presence = first["condition_presence_semantics"]
    mixed = first["mixed_batch_semantics"]
    diffusion = first["normalization_and_noise_policy"]
    equivariance = first["equivariance_contract"]
    scope = first["implementation_scope"]
    migration = first["base_to_conditioned_checkpoint_migration_policy"]
    conditioned = first["conditioned_checkpoint_strict_load_policy"]
    legacy = first["legacy_disabled_state_dict_policy"]
    candidates = {
        item["candidate"]: item for item in first["candidate_decisions"]
    }
    oracles = _synthetic_oracles()

    facts: dict[str, object] = {
        "source_runtime_bridge_gate_bundle_bound": (
            hashlib.sha256(source_bundle).hexdigest()
            == design._GATE_BUNDLE_TRANSPORT_SHA256
            == first["source_runtime_bridge_gate_bundle_transport_sha256"]
        ),
        "source_runtime_bridge_gate_bundle_canonical": (
            gate._canonical_json_bytes(decoded) == source_bundle
            and gate._validate_bundle(decoded, require_field_order=False)
            and decoded["runtime_bridge_gate_bundle_sha256"]
            == design._GATE_BUNDLE_INTERNAL_SHA256
        ),
        "source_runtime_bridge_gate_production_bound": (
            hashlib.sha256((ROOT / design._GATE_PRODUCTION_PATH).read_bytes()).hexdigest()
            == design._GATE_PRODUCTION_SHA256
            == first["source_runtime_bridge_gate_production_sha256"]
        ),
        "source_runtime_bridge_gate_commit_bound": (
            first["source_runtime_bridge_gate_commit"] == design._GATE_COMMIT
        ),
        "source_runtime_bridge_gate_commit_is_head_ancestor": (
            gate_commit_is_head_ancestor
        ),
        "source_runtime_bridge_gate_commit_is_origin_main_ancestor": (
            gate_commit_is_origin_main_ancestor
        ),
        "design_checker_post_commit_safe": (
            gate_commit_is_head_ancestor and gate_commit_is_origin_main_ancestor
        ),
        "runtime_bridge_gate_implemented": True,
        "lightning_interface_audited": (
            first["source_lightning_module_sha256"]
            == design._SOURCE_SHA256["lightning_modules.py"]
        ),
        "conditional_model_interface_audited": (
            first["source_conditional_model_sha256"]
            == design._SOURCE_SHA256["equivariant_diffusion/conditional_model.py"]
        ),
        "en_diffusion_interface_audited": (
            first["source_en_diffusion_sha256"]
            == design._SOURCE_SHA256["equivariant_diffusion/en_diffusion.py"]
        ),
        "dynamics_interface_audited": (
            first["source_dynamics_sha256"]
            == design._SOURCE_SHA256["equivariant_diffusion/dynamics.py"]
        ),
        "egnn_interface_audited": (
            first["source_egnn_sha256"]
            == design._SOURCE_SHA256["equivariant_diffusion/egnn_new.py"]
        ),
        "all_dynamics_call_sites_audited": (
            len(first["audited_dynamics_call_site_records"]) == 8
            and all(
                record["covered"]
                for record in first["audited_dynamics_call_site_records"]
            )
        ),
        "all_checkpoint_load_sites_audited": (
            len(first["audited_checkpoint_load_site_records"]) == 24
            and all(
                record["covered"]
                for record in first["audited_checkpoint_load_site_records"]
            )
        ),
        "checkpoint_bound": (
            (ROOT / design._CHECKPOINT_PATH).stat().st_size == design._CHECKPOINT_SIZE
            and hashlib.sha256(
                (ROOT / design._CHECKPOINT_PATH).read_bytes()
            ).hexdigest() == design._CHECKPOINT_SHA256
        ),
        "checkpoint_mode": profile["hyper_parameters_mode"],
        "checkpoint_state_key_count": profile["state_dict_key_count"],
        "checkpoint_state_manifest_sha256": (
            profile["state_dict_ordered_key_manifest_sha256"]
        ),
        "checkpoint_shape_manifest_sha256": (
            profile["state_dict_shape_dtype_manifest_sha256"]
        ),
        "selected_condition_field_name": first["selected_condition_field_name"],
        "selected_enable_flag_name": first["selected_enable_flag_name"],
        "selected_dynamics_argument_name": first["selected_dynamics_argument_name"],
        "selected_injection_module": first["selected_injection_module"],
        "selected_injection_point": first["selected_injection_point"],
        "selected_parameter_name": first["selected_parameter_name"],
        "selected_parameter_shape": "[joint_nf]",
        "selected_parameter_zero_initialized": (
            first["selected_parameter_initialization"] == "all_zeros"
        ),
        "append_to_pocket_one_hot": (
            candidates["append_indicator_to_pocket_one_hot"]["decision"]
            != "rejected"
        ),
        "change_atom_nf": not compatibility["atom_nf_changed"] is False,
        "change_residue_nf": not compatibility["residue_nf_changed"] is False,
        "change_joint_nf": not compatibility["joint_nf_changed"] is False,
        "change_existing_checkpoint_tensor_shape": (
            not compatibility["existing_tensor_shapes_unchanged_in_all_profiles"]
        ),
        "disabled_profile_existing_state_dict_exact": (
            legacy["existing_key_set_unchanged"]
            and legacy["existing_tensor_shapes_unchanged"]
            and not legacy["new_parameter_key_present"]
        ),
        "base_to_conditioned_exactly_one_new_key": (
            migration["allowed_missing_keys_before_fill"] == [design._NEW_STATE_KEY]
            and migration["allowed_unexpected_keys"] == []
        ),
        "base_to_conditioned_blanket_strict_false": migration["blanket_strict_false"],
        "conditioned_checkpoint_strict_load": conditioned["strict_load"],
        "legacy_absent_supported": presence["legacy_absent"]["legacy_output_preserved"],
        "covalent_present_supported": (
            presence["covalent_present"]["required_enable_flag"] is True
        ),
        "present_condition_requires_enable_flag": (
            presence["covalent_present"]["flag_false_fail_closed"]
        ),
        "present_all_false_rejected": (
            presence["present_all_false"]["accepted"] is False
        ),
        "mixed_noncovalent_zero_target_semantics_deferred": (
            mixed["mixed_noncovalent_zero_target_semantics_deferred"]
        ),
        "indicator_normalized": diffusion["indicator_normalized"],
        "indicator_noised": diffusion["indicator_noised"],
        "indicator_centered": diffusion["indicator_centered"],
        "indicator_rotated": diffusion["indicator_rotated"],
        "indicator_added_to_xh_pocket": diffusion["indicator_added_to_xh_pocket"],
        "indicator_contributes_to_reconstruction_loss": (
            diffusion["indicator_contributes_to_reconstruction_loss"]
        ),
        "equivariance_contract_preserved": (
            equivariance["translation_equivariance_preserved"]
            and equivariance["rotation_equivariance_preserved"]
            and not equivariance["coordinate_injection"]
        ),
        "node_permutation_alignment_preserved": (
            equivariance["node_permutation_equivariance_preserved"]
            and oracles["node_permutation_alignment_preserved"]
        ),
        "zero_initialization_parity": oracles["zero_initialization_parity"],
        "nonzero_target_row_changed": oracles["nonzero_target_row_changed"],
        "non_target_rows_unchanged": oracles["non_target_rows_unchanged"],
        "synthetic_gradient_path_exists": oracles["synthetic_gradient_path_exists"],
        "conditional_training_path_covered": first[
            "conditional_training_path_contract"
        ]["covered"],
        "conditional_eval_path_covered": first["conditional_eval_path_contract"][
            "covered"
        ],
        "conditional_sampling_path_covered": first[
            "conditional_sampling_path_contract"
        ]["covered"],
        "joint_training_path_covered": first["joint_training_path_contract"][
            "covered"
        ],
        "inpainting_path_covered": first["inpainting_path_contract"]["covered"],
        "simple_conditional_path_covered": first[
            "simple_conditional_path_contract"
        ]["covered"],
        "global_mutable_state_used": scope["global_mutable_state_used"],
        "model_consumption_designed": scope["model_consumption_designed"],
        "model_consumption_implemented": scope["model_consumption_implemented"],
        "new_model_parameter_created": scope["new_model_parameter_created"],
        "indicator_consumed_by_model": scope["indicator_consumed_by_model"],
        "indicator_passed_into_dynamics": scope["indicator_passed_into_dynamics"],
        "model_modified": scope["model_modified"],
        "forward_modified": scope["forward_modified"],
        "loss_modified": scope["loss_modified"],
        "training_or_parameter_update": scope["training_or_parameter_update"],
        "canonical_mask_count": len(first["canonical_mask_semantic_names"]),
        "scaffold_only_present": (
            "scaffold_only" in first["canonical_mask_semantic_names"]
        ),
        "sixth_mask_added": len(first["canonical_mask_semantic_names"]) != 5,
        "ready_for_model_consumption_implementation": first[
            "ready_for_model_consumption_implementation"
        ],
        "recommended_next_step": first["recommended_next_step"],
        "feature_semantics_audit_required_before_training": first[
            "feature_semantics_audit_required_before_training"
        ],
        "model_consumption_design_response_sha256": first[
            "model_consumption_design_response_sha256"
        ],
    }

    expected_false = {
        "append_to_pocket_one_hot",
        "change_atom_nf",
        "change_residue_nf",
        "change_joint_nf",
        "change_existing_checkpoint_tensor_shape",
        "base_to_conditioned_blanket_strict_false",
        "indicator_normalized",
        "indicator_noised",
        "indicator_centered",
        "indicator_rotated",
        "indicator_added_to_xh_pocket",
        "indicator_contributes_to_reconstruction_loss",
        "global_mutable_state_used",
        "model_consumption_implemented",
        "new_model_parameter_created",
        "indicator_consumed_by_model",
        "indicator_passed_into_dynamics",
        "model_modified",
        "forward_modified",
        "loss_modified",
        "training_or_parameter_update",
        "sixth_mask_added",
    }
    non_boolean = {
        "checkpoint_mode", "checkpoint_state_key_count",
        "checkpoint_state_manifest_sha256", "checkpoint_shape_manifest_sha256",
        "selected_condition_field_name", "selected_enable_flag_name",
        "selected_dynamics_argument_name", "selected_injection_module",
        "selected_injection_point", "selected_parameter_name",
        "selected_parameter_shape", "canonical_mask_count",
        "recommended_next_step", "model_consumption_design_response_sha256",
    }
    if not all(facts[name] is False for name in expected_false):
        raise ValueError(design._ERROR)
    if not all(
        value is True
        for name, value in facts.items()
        if name not in expected_false | non_boolean
    ):
        raise ValueError(design._ERROR)
    if (
        facts["checkpoint_mode"] != "pocket_conditioning"
        or facts["checkpoint_state_key_count"] != 122
        or facts["checkpoint_state_manifest_sha256"]
        != design._CHECKPOINT_KEY_MANIFEST_SHA256
        or facts["checkpoint_shape_manifest_sha256"]
        != design._CHECKPOINT_SHAPE_MANIFEST_SHA256
        or facts["selected_condition_field_name"] != design._FIELD
        or facts["selected_enable_flag_name"] != design._ENABLE_FLAG
        or facts["selected_dynamics_argument_name"] != design._FIELD
        or facts["selected_injection_module"] != "EGNNDynamics"
        or facts["selected_injection_point"] != design._INJECTION_POINT
        or facts["selected_parameter_name"] != design._PARAMETER
        or facts["selected_parameter_shape"] != "[joint_nf]"
        or facts["canonical_mask_count"] != 5
        or facts["recommended_next_step"]
        != "implement_covapie_target_residue_atom_condition_model_consumption_v1"
    ):
        raise ValueError(design._ERROR)
    return facts


def main() -> None:
    facts = check()
    for name, value in facts.items():
        _emit(name, value)


if __name__ == "__main__":
    main()
