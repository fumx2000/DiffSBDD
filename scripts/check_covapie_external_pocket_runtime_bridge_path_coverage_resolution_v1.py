#!/usr/bin/env python3
"""Check the frozen external-pocket runtime-bridge path coverage design."""

from __future__ import annotations

import hashlib
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext.covapie_external_pocket_runtime_bridge_path_coverage_resolution_v1 import (
    EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS,
    _digest_record,
    _validate_response,
    resolve_covapie_external_pocket_runtime_bridge_path_coverage_v1,
)


STATE = ROOT.parent / "covapie-state" / "manual-review"
PATHS = (
    STATE / "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json",
    STATE / "covapie_current11_pocket_atom_identity_alignment_bundle_v1.json",
    STATE / "covapie_current11_target_residue_atom_condition_adapter_bundle_v1.json",
    STATE / "covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1.json",
)
EXPECTED_TRANSPORT = (
    "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096",
    "7f80a810ff35c4ea5d61262021379767a4d15202badd8ec6a6b846405147d842",
    "983c25ea8c52ca54f0c0292990a625e9a9cf0d2370cb517d66a84801d957b65a",
    "c7e2c9eec92d560fc55206399d9b27df511733821ce3233c3546da38d9992a9d",
)
ERROR = "COVAPIE_EXTERNAL_POCKET_RUNTIME_BRIDGE_PATH_COVERAGE_INVALID"


def _emit(name: str, value: object) -> None:
    if isinstance(value, bool):
        rendered = str(value).lower()
    else:
        rendered = str(value)
    print(f"{name}={rendered}")


def _resigned_drift_rejected(response: dict, mutate) -> bool:
    changed = deepcopy(response)
    mutate(changed)
    changed["external_path_coverage_resolution_sha256"] = _digest_record(
        changed,
        EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS,
        "external_path_coverage_resolution_sha256",
    )
    if changed["external_path_coverage_resolution_sha256"] == response["external_path_coverage_resolution_sha256"]:
        return False
    try:
        _validate_response(changed)
    except ValueError as error:
        return str(error) == ERROR
    return False


def _all_resigned_drifts_rejected(response: dict, mutations: tuple) -> bool:
    return all(_resigned_drift_rejected(response, mutate) for mutate in mutations)


def main() -> int:
    payloads = tuple(path.read_bytes() for path in PATHS)
    bound = tuple(hashlib.sha256(payload).hexdigest() for payload in payloads) == EXPECTED_TRANSPORT
    if not bound:
        raise ValueError("COVAPIE_EXTERNAL_POCKET_RUNTIME_BRIDGE_PATH_COVERAGE_INVALID")
    response = resolve_covapie_external_pocket_runtime_bridge_path_coverage_v1(
        source_authority_bundle=payloads[0],
        source_alignment_bundle=payloads[1],
        source_adapter_bundle=payloads[2],
        source_adapter_gate_bundle=payloads[3],
        repo_root=ROOT,
    )
    selector = response["target_selector_validation_contract"]
    fixed = response["target_selector_fixed_v1_semantics"]
    representation = response["pocket_representation_policy"]
    membership = response["target_membership_policy"]
    order = response["target_atom_order_binding_policy"]
    repeat = response["repeated_indicator_policy"]
    sidecar = response["prepared_pocket_sidecar_contract"]
    legacy = response["legacy_external_path_policy"]
    conditional = response["conditional_generation_path_contract"]
    inpainting = response["inpainting_path_contract"]
    callers = response["cli_or_public_caller_forwarding_contract"]
    checkpoint = response["checkpoint_compatibility_decision"]
    masks = response["canonical_mask_semantic_names"]
    covalent = response["covalent_external_path_policy"]

    resigned_selector_semantics_drift_rejected = _all_resigned_drifts_rejected(
        response,
        (
            lambda value: value["target_selector_fixed_v1_semantics"].__setitem__("residue_name", "ALA"),
            lambda value: value["target_selector_validation_contract"].__setitem__("schema_exact6", False),
        ),
    )
    resigned_atom_order_repeat_sidecar_drift_rejected = _all_resigned_drifts_rejected(
        response,
        (
            lambda value: value["target_atom_order_binding_policy"].__setitem__("coordinates_used_for_identity", True),
            lambda value: value["repeated_indicator_policy"].__setitem__("per_sample_true_count", 99),
            lambda value: value["prepared_pocket_sidecar_contract"].__setitem__("field_name", "wrong"),
        ),
    )
    resigned_checkpoint_candidate_drift_rejected = _all_resigned_drifts_rejected(
        response,
        (
            lambda value: value["checkpoint_compatibility_decision"].__setitem__("append_to_pocket_one_hot", True),
            lambda value: value["candidate_decisions"][3].__setitem__("decision", "accepted"),
        ),
    )
    resigned_source_lineage_drift_rejected = _all_resigned_drifts_rejected(
        response,
        (
            lambda value: value.__setitem__("source_authority_bundle_transport_sha256", "0" * 64),
            lambda value: value.__setitem__("source_runtime_bridge_design_production_sha256", "0" * 64),
            lambda value: value["audited_runtime_source_records"][0].__setitem__("source_sha256", "0" * 64),
        ),
    )
    resigned_caller_contract_drift_rejected = _all_resigned_drifts_rejected(
        response,
        (
            lambda value: value["generate_ligands_call_site_records"][0].__setitem__("caller_path", "wrong.py"),
            lambda value: value["generate_ligands_call_site_records"][0].__setitem__("future_selector_forwarding_surface", "wrong_surface"),
            lambda value: value["cli_or_public_caller_forwarding_contract"]["prepare_pocket_call_site_records"][0].__setitem__("future_selector_forwarding_surface", "wrong_surface"),
        ),
    )

    assertions = {
        "source_runtime_bridge_design_bound": response["source_runtime_bridge_design_production_sha256"] == "045aeaa16d91dfe10d1cdec9cfa789e637b5eba41a0d0a45313d20617e72bf67",
        "source_runtime_bridge_design_response_bound": response["source_runtime_bridge_design_response_sha256"] == "1c90069e6d64916504f6a6e1e0d852e95351dc261e36ea3eab3d0ef4880ec6f2",
        "source_runtime_bridge_blocker_reproduced": response["source_runtime_bridge_blocker"] == "generate_ligands->prepare_pocket->ConditionalDDPM.sample_given_pocket_or_inpaint",
        "generate_ligands_interface_audited": response["generate_ligands_current_interface"]["calls_prepare_pocket"] is True,
        "prepare_pocket_interface_audited": response["prepare_pocket_current_interface"]["full_atom_base_sequence"] == "pocket_atoms",
        "all_generate_ligands_call_sites_audited": callers["all_generate_ligands_call_sites_audited"] is True,
        "all_prepare_pocket_call_sites_audited": callers["all_prepare_pocket_call_sites_audited"] is True,
        "selector_schema_exact6": selector["schema_exact6"] is True and len(response["target_selector_fields"]) == 6,
        "selector_requires_chain": fixed["chain_id"] == "nonempty_string_exact_match",
        "selector_requires_residue_number": fixed["residue_sequence_number"] == "int_non_bool_exact_match",
        "selector_requires_blank_v1_insertion_code": fixed["residue_insertion_code"] == "exactly_one_character_and_V1_value_blank",
        "selector_requires_cys_sg_s": (fixed["residue_name"], fixed["atom_name"], fixed["element"]) == ("CYS", "SG", "S"),
        "full_atom_required_when_selector_present": representation["full_atom_required_when_selector_present"] is True,
        "ca_selector_present_rejected": representation["CA_selector_present_rejected"] is True,
        "target_must_already_be_in_pocket": membership["target_must_already_be_in_selected_pocket"] is True,
        "target_absent_rejected": membership["target_absent_rejected"] is True,
        "target_duplicate_rejected": membership["target_duplicate_rejected"] is True,
        "disordered_target_rejected": selector["disordered_target_atom_allowed"] is False,
        "coordinate_matching_used": order["coordinates_used_for_identity"],
        "auto_append_target_residue": membership["auto_append_target_residue"],
        "target_index_bound_to_actual_pocket_atom_order": order["binding_sequence"] == "actual_prepare_pocket_full_atom_pocket_atoms",
        "base_indicator_bool": repeat["base_dtype"] == "torch.bool",
        "base_indicator_true_count_one": repeat["base_true_count"] == 1,
        "repeated_indicator_sample_blocks_aligned": repeat["repeat_order"] == "same_sample_block_order_as_pocket_coord.repeat_and_pocket_one_hot.repeat",
        "repeated_indicator_one_true_per_sample": repeat["per_sample_true_count"] == 1,
        "legacy_selector_absent_passthrough": legacy["selector_absent_preserves_behavior_exactly"] is True,
        "legacy_selector_absent_creates_indicator": not sidecar["selector_absent_key_absent"],
        "conditional_generation_path_covered": conditional["covered"] is True,
        "inpainting_path_covered": inpainting["covered"] is True,
        "all_public_callers_have_forwarding_contract": callers["all_public_callers_have_forwarding_contract"] is True,
        "append_to_pocket_one_hot": checkpoint["append_to_pocket_one_hot"],
        "base_state_dict_change": checkpoint["base_state_dict_key_change"],
        "checkpoint_tensor_shape_change": checkpoint["base_checkpoint_tensor_shape_change"],
        "indicator_consumed_by_model": conditional["indicator_consumed_by_model"] or inpainting["indicator_consumed_by_model"],
        "indicator_passed_into_dynamics": conditional["indicator_passed_into_dynamics"] or inpainting["indicator_passed_into_dynamics"],
        "scaffold_only_present": "scaffold_only" in masks,
        "sixth_mask_added": len(masks) != 5,
        "resigned_selector_semantics_drift_rejected": resigned_selector_semantics_drift_rejected,
        "resigned_atom_order_repeat_sidecar_drift_rejected": resigned_atom_order_repeat_sidecar_drift_rejected,
        "resigned_checkpoint_candidate_drift_rejected": resigned_checkpoint_candidate_drift_rejected,
        "resigned_source_lineage_drift_rejected": resigned_source_lineage_drift_rejected,
        "resigned_caller_contract_drift_rejected": resigned_caller_contract_drift_rejected,
        "external_path_coverage_resolved": covalent["external_path_coverage_designed"] is True,
        "ready_for_runtime_bridge_implementation": response["ready_for_runtime_bridge_implementation"] is True,
        "deterministic": resolve_covapie_external_pocket_runtime_bridge_path_coverage_v1(
            source_authority_bundle=payloads[0], source_alignment_bundle=payloads[1],
            source_adapter_bundle=payloads[2], source_adapter_gate_bundle=payloads[3], repo_root=ROOT,
        ) == response,
        "inputs_unchanged": payloads == tuple(path.read_bytes() for path in PATHS),
        "files_written": False,
        "runtime_bridge_implemented": covalent["runtime_bridge_implemented"],
        "lightning_modified": False,
        "model_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "training_or_parameter_update": False,
        "feature_semantics_audit_required_before_training": response["feature_semantics_audit_required_before_training"] is True,
    }
    required_true = {
        key for key in assertions
        if key not in {
            "coordinate_matching_used", "auto_append_target_residue",
            "legacy_selector_absent_creates_indicator", "append_to_pocket_one_hot",
            "base_state_dict_change", "checkpoint_tensor_shape_change",
            "indicator_consumed_by_model", "indicator_passed_into_dynamics",
            "sixth_mask_added", "files_written", "runtime_bridge_implemented",
            "lightning_modified", "model_modified", "forward_modified",
            "loss_modified", "training_or_parameter_update",
        }
    }
    if not all(assertions[key] is True for key in required_true):
        raise ValueError("COVAPIE_EXTERNAL_POCKET_RUNTIME_BRIDGE_PATH_COVERAGE_INVALID")
    required_false = set(assertions) - required_true
    if not all(assertions[key] is False for key in required_false):
        raise ValueError("COVAPIE_EXTERNAL_POCKET_RUNTIME_BRIDGE_PATH_COVERAGE_INVALID")

    for name in (
        "source_authority_bundle_bound", "source_alignment_bundle_bound",
        "source_adapter_bundle_bound", "source_adapter_gate_bundle_bound",
    ):
        _emit(name, True)
    for name, value in assertions.items():
        if name in {"external_path_coverage_resolved", "ready_for_runtime_bridge_implementation"}:
            continue
        _emit(name, value)
    _emit("selected_external_selector_argument_name", response["selected_external_selector_argument_name"])
    _emit("selected_prepare_pocket_argument_name", response["selected_prepare_pocket_argument_name"])
    _emit("canonical_mask_count", len(masks))
    _emit("external_path_coverage_resolved", assertions["external_path_coverage_resolved"])
    _emit("ready_for_runtime_bridge_implementation", assertions["ready_for_runtime_bridge_implementation"])
    _emit("recommended_next_step", response["recommended_next_step"])
    _emit("external_path_coverage_resolution_sha256", response["external_path_coverage_resolution_sha256"])
    blockers = response["unresolved_path_blockers"]
    _emit("unresolved_path_blocker_count", len(blockers))
    for blocker in blockers:
        _emit("unresolved_path_blocker", blocker)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
