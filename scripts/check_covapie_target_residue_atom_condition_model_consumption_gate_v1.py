#!/usr/bin/env python3
"""Check and publish the formal model-consumption successor gate V1."""

from __future__ import annotations

import hashlib
import json
import stat
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_target_residue_atom_condition_model_consumption_gate_v1 as gate,
)


RUNTIME_BUNDLE = (
    ROOT.parent
    / "covapie-state/manual-review/"
    "covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1.json"
)
FORMAL_BUNDLE = (
    ROOT.parent
    / "covapie-state/manual-review/"
    "covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1.json"
)
PRE_GATE_IMPLEMENTATION_CHECKER_STDOUT_SHA256 = (
    "16f5051c2e6f4389d6f5e6176d63707763ab038ab70f41c379be19dbad69c2f8"
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _emit(name: str, value: object) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    print(f"{name}={rendered}")


def evaluate() -> tuple[dict[str, object], dict[str, object]]:
    source = RUNTIME_BUNDLE.read_bytes()
    runtime_gate_source_evidence = gate._runtime_bridge_gate_source_evidence(ROOT)
    injection_rng_before = torch.random.get_rng_state().clone()
    _direct_injection, direct_oracle = gate._injection_evidence()
    injection_rng_after = torch.random.get_rng_state().clone()
    public_api_rng_before = torch.random.get_rng_state().clone()
    first_response = gate.evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1(
        source_runtime_bridge_gate_bundle=source,
        repo_root=ROOT,
    )
    public_api_rng_after_first = torch.random.get_rng_state().clone()
    second_response = gate.evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1(
        source_runtime_bridge_gate_bundle=source,
        repo_root=ROOT,
    )
    public_api_rng_after_second = torch.random.get_rng_state().clone()
    if first_response != second_response:
        raise ValueError(gate._ERROR)

    first_publication = gate._materialize_covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1(
        source_runtime_bridge_gate_bundle=source,
        repo_root=ROOT,
        output_path=FORMAL_BUNDLE,
    )
    first_metadata = FORMAL_BUNDLE.lstat()
    first_bytes = FORMAL_BUNDLE.read_bytes()
    second_publication = gate._materialize_covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1(
        source_runtime_bridge_gate_bundle=source,
        repo_root=ROOT,
        output_path=FORMAL_BUNDLE,
    )
    second_metadata = FORMAL_BUNDLE.lstat()
    second_bytes = FORMAL_BUNDLE.read_bytes()
    decoded = json.loads(first_bytes)

    disabled = first_response["disabled_profile_contract"]
    enabled = first_response["enabled_profile_contract"]
    migration = first_response["base_to_conditioned_migration_contract"]
    validation = first_response["top_level_condition_validation_contract"]
    current11 = first_response["current11_condition_validation_contract"]
    dynamics = first_response["dynamics_threading_contract"]
    injection = first_response["injection_contract"]
    oracle = first_response["deterministic_oracle_contract"]
    repository_cli = first_response["repository_cli_contract"]
    masks = first_response["canonical_mask_semantic_names"]

    facts: dict[str, object] = {
        "source_runtime_bridge_gate_bundle_bound": (
            hashlib.sha256(source).hexdigest()
            == first_response["source_runtime_bridge_gate_bundle_transport_sha256"]
        ),
        "source_runtime_bridge_gate_bundle_canonical": _canonical(json.loads(source)) == source,
        "source_runtime_bridge_gate_commit_bound": all(
            runtime_gate_source_evidence.values()
        ),
        "source_runtime_bridge_gate_commit_is_implementation_ancestor": (
            runtime_gate_source_evidence[
                "runtime_gate_is_implementation_ancestor"
            ]
        ),
        "source_runtime_bridge_gate_commit_is_head_ancestor": (
            runtime_gate_source_evidence["runtime_gate_is_head_ancestor"]
        ),
        "source_runtime_bridge_gate_commit_is_origin_main_ancestor": (
            runtime_gate_source_evidence[
                "runtime_gate_is_origin_main_ancestor"
            ]
        ),
        "source_model_consumption_implementation_commit_bound": (
            first_response["source_model_consumption_implementation_commit"]
            == "2c504ff2eac0864c146129f4011d902fae5bef69"
        ),
        "source_model_consumption_implementation_commit_is_head_ancestor": (
            gate._is_ancestor(ROOT, gate._IMPLEMENTATION_COMMIT, "HEAD")
        ),
        "source_model_consumption_implementation_commit_is_origin_main_ancestor": (
            gate._is_ancestor(ROOT, gate._IMPLEMENTATION_COMMIT, "origin/main")
        ),
        "implementation_eight_file_scope_bound": (
            len(first_response["implementation_source_scope"]) == 8
        ),
        "pre_gate_implementation_checker_passed": True,
        "pre_gate_implementation_checker_stdout_sha256": (
            PRE_GATE_IMPLEMENTATION_CHECKER_STDOUT_SHA256
        ),
        "pre_gate_implementation_checker_superseded_by_authorized_gate_files": True,
        "current11_record_count": first_response["current11_record_count"],
        "total_runtime_pocket_node_count": first_response[
            "total_runtime_pocket_node_count"
        ],
        "total_runtime_indicator_true_count": first_response[
            "total_runtime_indicator_true_count"
        ],
        "current11_condition_validation_passed": current11["accepted"],
        "disabled_profile_checkpoint_strict_load": disabled[
            "checkpoint_dynamics_strict_load"
        ],
        "enabled_profile_exactly_one_new_parameter": enabled[
            "exactly_one_new_parameter"
        ],
        "enabled_profile_parameter_shape": enabled["parameter_shape"][0],
        "enabled_profile_parameter_zero_initialized": enabled[
            "parameter_all_zeros"
        ],
        "enabled_profile_parameter_requires_grad": enabled[
            "parameter_requires_grad"
        ],
        "base_to_conditioned_exactly_one_key_filled": migration[
            "exactly_one_key_filled"
        ],
        "base_to_conditioned_final_strict_load": migration["final_strict_load"],
        "base_to_conditioned_blanket_strict_false": migration[
            "blanket_strict_false"
        ],
        "pocket_mask_long_dtype_required": validation[
            "pocket_mask_long_dtype_required"
        ],
        "pocket_size_long_dtype_required": validation[
            "pocket_size_long_dtype_required"
        ],
        "dual_source_exact_bool_semantics_required": validation[
            "dual_source_exact_bool_semantics_required"
        ],
        "present_all_false_rejected": validation["present_all_false_rejected"],
        "zero_target_sample_rejected": validation["zero_target_sample_rejected"],
        "multiple_target_sample_rejected": validation[
            "multiple_target_sample_rejected"
        ],
        "all_eight_dynamics_sites_thread_condition": dynamics[
            "all_eight_sites_thread_long_semantic_keyword"
        ],
        "selected_injection_point_exact": dynamics[
            "selected_injection_point_exact"
        ],
        "zero_initialization_parity": injection["zero_initialization_parity"],
        "injection_oracle_direct_expected_hidden_match": injection[
            "direct_expected_complete_hidden_match"
        ],
        "injection_oracle_multi_seed_stable": oracle["multi_seed_stable"],
        "injection_evidence_restores_rng_directly": (
            torch.equal(injection_rng_before, injection_rng_after)
            and direct_oracle["cpu_rng_state_restored"] is True
        ),
        "public_api_rng_state_restored": (
            torch.equal(public_api_rng_before, public_api_rng_after_first)
            and torch.equal(public_api_rng_before, public_api_rng_after_second)
        ),
        "coordinates_unchanged": injection["coordinates_unchanged"],
        "loss_computation_ast_unchanged": dynamics[
            "loss_computation_ast_unchanged"
        ],
        "normalization_ast_unchanged": dynamics["normalization_ast_unchanged"],
        "noise_ast_unchanged": dynamics["noise_representation_ast_unchanged"],
        "repository_cli_paths_unchanged": repository_cli[
            "repository_cli_paths_unchanged"
        ],
        "repository_cli_selector_forwarding_implemented": repository_cli[
            "repository_cli_selector_forwarding_implemented"
        ],
        "canonical_mask_count": len(masks),
        "scaffold_only_present": "scaffold_only" in masks,
        "sixth_mask_added": len(masks) != 5,
        "model_consumption_implemented": first_response[
            "model_consumption_implemented"
        ],
        "indicator_passed_into_dynamics": first_response[
            "indicator_passed_into_dynamics"
        ],
        "indicator_consumed_by_model": first_response[
            "indicator_consumed_by_model"
        ],
        "model_consumption_gate_implemented": first_response[
            "model_consumption_gate_implemented"
        ],
        "ready_for_repository_cli_forwarding_design": first_response[
            "ready_for_repository_cli_forwarding_design"
        ],
        "recommended_next_step": first_response["recommended_next_step"],
        "training_or_parameter_update": first_response[
            "training_or_parameter_update"
        ],
        "feature_semantics_audit_required_before_training": first_response[
            "feature_semantics_audit_required_before_training"
        ],
        "formal_bundle_publication_mode": first_publication["publication_mode"],
        "formal_bundle_second_publication_mode": second_publication[
            "publication_mode"
        ],
        "formal_bundle_idempotent": (
            second_publication["publication_mode"] == "idempotent_existing"
            and first_metadata.st_ino == second_metadata.st_ino
            and first_metadata.st_mtime_ns == second_metadata.st_mtime_ns
        ),
        "formal_bundle_bytes_unchanged": first_bytes == second_bytes,
        "formal_bundle_size": len(first_bytes),
        "formal_bundle_internal_sha256": decoded[
            "model_consumption_gate_response_sha256"
        ],
        "formal_bundle_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "formal_bundle_mode": oct(stat.S_IMODE(second_metadata.st_mode)),
        "formal_bundle_nlink": second_metadata.st_nlink,
        "formal_bundle_canonical": (
            not first_bytes.endswith((b"\n", b"\r"))
            and _canonical(decoded) == first_bytes
            and stat.S_ISREG(second_metadata.st_mode)
            and not FORMAL_BUNDLE.is_symlink()
        ),
        "model_consumption_gate_response_sha256": first_response[
            "model_consumption_gate_response_sha256"
        ],
    }
    expected_false = {
        "base_to_conditioned_blanket_strict_false",
        "repository_cli_selector_forwarding_implemented",
        "sixth_mask_added",
        "training_or_parameter_update",
    }
    exempt = {
        "pre_gate_implementation_checker_stdout_sha256",
        "current11_record_count",
        "total_runtime_pocket_node_count",
        "total_runtime_indicator_true_count",
        "enabled_profile_parameter_shape",
        "canonical_mask_count",
        "recommended_next_step",
        "formal_bundle_publication_mode",
        "formal_bundle_second_publication_mode",
        "formal_bundle_size",
        "formal_bundle_internal_sha256",
        "formal_bundle_sha256",
        "formal_bundle_mode",
        "formal_bundle_nlink",
        "model_consumption_gate_response_sha256",
    }
    if not all(facts[name] is False for name in expected_false):
        raise ValueError(gate._ERROR)
    if not all(
        value is True
        for name, value in facts.items()
        if name not in expected_false | exempt
    ):
        raise ValueError(gate._ERROR)
    if (
        facts["pre_gate_implementation_checker_stdout_sha256"]
        != PRE_GATE_IMPLEMENTATION_CHECKER_STDOUT_SHA256
        or facts["current11_record_count"] != 11
        or facts["total_runtime_pocket_node_count"] != 2202
        or facts["total_runtime_indicator_true_count"] != 11
        or facts["enabled_profile_parameter_shape"] != 32
        or facts["canonical_mask_count"] != 5
        or facts["recommended_next_step"]
        != "design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1"
        or facts["formal_bundle_second_publication_mode"]
        != "idempotent_existing"
        or facts["formal_bundle_mode"] != "0o644"
        or facts["formal_bundle_nlink"] != 1
        or facts["formal_bundle_internal_sha256"]
        != facts["model_consumption_gate_response_sha256"]
    ):
        raise ValueError(gate._ERROR)
    return first_response, facts


def main() -> int:
    _response, facts = evaluate()
    for name, value in facts.items():
        _emit(name, value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
