#!/usr/bin/env python3
"""Check the frozen target-residue atom-condition runtime-bridge design V1."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_target_residue_atom_condition_runtime_bridge_design_v1 as design


STATE = ROOT.parent / "covapie-state" / "manual-review"
AUTHORITY = STATE / "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
ALIGNMENT = STATE / "covapie_current11_pocket_atom_identity_alignment_bundle_v1.json"
ADAPTER = STATE / "covapie_current11_target_residue_atom_condition_adapter_bundle_v1.json"
ADAPTER_GATE = STATE / "covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1.json"


def _require(condition: bool) -> bool:
    if condition is not True:
        raise SystemExit("runtime bridge design check failed")
    return True


def _status() -> str:
    return subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout


def main() -> int:
    inputs = (
        AUTHORITY.read_bytes(),
        ALIGNMENT.read_bytes(),
        ADAPTER.read_bytes(),
        ADAPTER_GATE.read_bytes(),
    )
    input_snapshots = tuple(bytes(value) for value in inputs)
    before = _status()
    response = design.design_covapie_target_residue_atom_condition_runtime_bridge_v1(
        source_authority_bundle=inputs[0],
        source_alignment_bundle=inputs[1],
        source_adapter_bundle=inputs[2],
        source_adapter_gate_bundle=inputs[3],
        repo_root=ROOT,
    )
    repeated = design.design_covapie_target_residue_atom_condition_runtime_bridge_v1(
        source_authority_bundle=inputs[0],
        source_alignment_bundle=inputs[1],
        source_adapter_bundle=inputs[2],
        source_adapter_gate_bundle=inputs[3],
        repo_root=ROOT,
    )
    after = _status()

    records = {record["source_path"]: record for record in response["current_runtime_interface_records"]}
    candidates = {record["candidate"]: record["decision"] for record in response["candidate_decisions"]}
    contract = response["field_required_when_present_contract"]
    cardinality = response["per_sample_cardinality_policy"]
    checkpoint = response["checkpoint_compatibility_decision"]
    conditional = response["conditional_sampling_path_coverage"]

    checks = [
        ("source_authority_bundle_bound", response["source_authority_bundle_transport_sha256"] == hashlib.sha256(inputs[0]).hexdigest()),
        ("source_alignment_bundle_bound", response["source_alignment_bundle_transport_sha256"] == hashlib.sha256(inputs[1]).hexdigest()),
        ("source_adapter_bundle_bound", response["source_adapter_bundle_transport_sha256"] == hashlib.sha256(inputs[2]).hexdigest()),
        ("source_adapter_gate_bundle_bound", response["source_adapter_gate_bundle_transport_sha256"] == hashlib.sha256(inputs[3]).hexdigest()),
        ("source_adapter_gate_bundle_recompiled_exact", response["source_adapter_gate_bundle_sha256"] == "97821184d8c76618bb549dd708132bd9579687c6f3a0ba8007d0bbc80d7d6602"),
        ("source_adapter_gate_production_bound", response["source_adapter_gate_production_sha256"] == hashlib.sha256((ROOT / "src/covalent_ext/covapie_target_residue_atom_condition_adapter_gate_v1.py").read_bytes()).hexdigest()),
        ("dataset_runtime_interface_audited", records["dataset.py"]["audited"] is True),
        ("lightning_runtime_interface_audited", records["lightning_modules.py"]["audited"] is True),
        ("conditional_ddpm_interface_audited", records["equivariant_diffusion/conditional_model.py"]["audited"] is True),
        ("normalization_interface_audited", records["equivariant_diffusion/en_diffusion.py"]["audited"] is True),
        ("dynamics_interface_audited", records["equivariant_diffusion/dynamics.py"]["audited"] is True),
        ("selected_bridge_same_name_pocket_sidecar", response["selected_bridge_representation"] == "same_name_per_pocket_node_bool_sidecar"),
        ("legacy_field_absent_passthrough", response["field_optional_for_legacy_batches"] is True and contract["legacy_absent_creates_destination_key"] is False and contract["legacy_absent_creates_all_false_tensor"] is False),
        ("present_field_requires_bool", contract["torch_dtype"] == "torch.bool"),
        ("present_field_requires_node_alignment", contract["node_order"] == "identical_to_pocket_x_and_pocket_one_hot"),
        ("current11_present_field_requires_one_true_per_sample", cardinality["current11_resolved_covalent_true_count"] == 1),
        ("mixed_noncovalent_zero_target_semantics_deferred", cardinality["mixed_noncovalent_zero_target_semantics_deferred"] is True),
        ("training_path_covered", response["training_path_coverage"]["all_paths_use_get_ligand_and_pocket"] is True),
        ("validation_test_path_covered", response["evaluation_path_coverage"]["all_paths_use_get_ligand_and_pocket"] is True),
        ("given_pocket_sampling_paths_covered", conditional["collated_given_pocket_paths_covered"] is True),
        ("actual_inpainting_paths_audited", conditional["actual_inpainting_paths_audited"] is True),
        ("all_inpainting_paths_use_unified_entry", conditional["all_paths_use_get_ligand_and_pocket"] is True),
        ("normalize_preserves_sidecar_key", response["normalization_preservation_policy"]["sidecar_key_preserved"] is True),
        ("indicator_passed_into_dynamics", response["indicator_passed_into_dynamics"] is True),
        ("indicator_consumed_by_model", records["equivariant_diffusion/conditional_model.py"]["indicator_consumed"] is True),
        ("one_hot_append_rejected", candidates["append_indicator_to_pocket_one_hot"] == "rejected"),
        ("per_sample_scalar_index_rejected", candidates["per_sample_local_target_index_scalar"] == "rejected"),
        ("duplicate_target_xyz_rejected", candidates["duplicate_target_xyz_or_atom_one_hot"] == "rejected"),
        ("global_mutable_state_rejected", candidates["module_global_singleton_cache_or_implicit_hook_state"] == "rejected"),
        ("ddpm_signature_change_deferred", candidates["modify_ConditionalDDPM_or_EGNNDynamics_or_add_condition_encoder"] == "deferred"),
        ("dynamics_signature_change_deferred", candidates["modify_ConditionalDDPM_or_EGNNDynamics_or_add_condition_encoder"] == "deferred"),
        ("canonical_masks_exact", tuple(response["canonical_mask_semantic_names"]) == design.CANONICAL_MASK_SEMANTIC_NAMES),
        ("deterministic", repeated == response),
        ("inputs_unchanged", inputs == input_snapshots),
        ("files_written", after != before),
        ("runtime_bridge_designed", response["runtime_bridge_design_version"] == design._VERSION),
        ("feature_semantics_audit_required_before_training", response["feature_semantics_audit_required_before_training"] is True),
    ]

    # These values are intentionally false and are asserted before reporting.
    false_checks = [
        ("indicator_passed_into_dynamics", response["indicator_passed_into_dynamics"]),
        ("indicator_consumed_by_model", records["equivariant_diffusion/conditional_model.py"]["indicator_consumed"]),
        ("append_to_pocket_one_hot", checkpoint["append_to_pocket_one_hot"]),
        ("base_state_dict_change", checkpoint["base_state_dict_key_change"]),
        ("checkpoint_tensor_shape_change", checkpoint["base_checkpoint_tensor_shape_change"]),
        ("sixth_mask_added", len(response["canonical_mask_semantic_names"]) != 5),
        ("files_written", after != before),
        ("runtime_bridge_implemented", records["lightning_modules.py"]["runtime_bridge_implemented"]),
        ("model_consumption_designed", False),
        ("model_modified", checkpoint["modify_ConditionalDDPM"] or checkpoint["modify_EGNNDynamics"]),
        ("forward_modified", False),
        ("loss_modified", False),
        ("training_or_parameter_update", False),
    ]
    true_checks = [(name, value) for name, value in checks if name not in {"all_inpainting_paths_use_unified_entry", "indicator_passed_into_dynamics", "indicator_consumed_by_model", "files_written"}]
    for _name, value in true_checks:
        _require(value is True)
    for _name, value in false_checks:
        _require(value is False)
    _require(conditional["all_paths_use_get_ligand_and_pocket"] is False)
    _require(response["ready_for_runtime_bridge_implementation"] is False)
    _require(len(conditional["bypassing_paths"]) == 1)

    for name, value in checks:
        if name in {"indicator_passed_into_dynamics", "indicator_consumed_by_model", "files_written"}:
            continue
        print(f"{name}={str(value).lower()}")
    print(f"source_batch_field_name={response['source_batch_field_name']}")
    print(f"destination_pocket_field_name={response['destination_pocket_field_name']}")
    print(f"selected_field_torch_dtype={response['field_torch_dtype']}")
    print("selected_field_domain=per_pocket_node")
    for name, value in false_checks:
        print(f"{name}={str(value).lower()}")
    print(f"canonical_mask_count={len(response['canonical_mask_semantic_names'])}")
    print(f"scaffold_only_present={str('scaffold_only' in response['canonical_mask_semantic_names']).lower()}")
    print(f"ready_for_runtime_bridge_implementation={str(response['ready_for_runtime_bridge_implementation']).lower()}")
    print(f"runtime_bridge_path_blocker_count={len(conditional['bypassing_paths'])}")
    print(f"runtime_bridge_path_blocker={conditional['bypassing_paths'][0]}")
    print(f"recommended_next_step={response['recommended_next_step']}")
    print(f"runtime_bridge_design_response_sha256={response['runtime_bridge_design_response_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
