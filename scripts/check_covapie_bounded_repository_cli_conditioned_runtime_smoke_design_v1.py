#!/usr/bin/env python3
"""Check the lifecycle-neutral bounded repository CLI runtime-smoke design."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1 as design,
)


_CHECK_ERROR = (
    "COVAPIE_BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_DESIGN_CHECK_INVALID"
)


def _emit(name: str, value: object) -> None:
    if isinstance(value, bool):
        rendered = str(value).lower()
    elif isinstance(value, (dict, list)):
        rendered = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    else:
        rendered = str(value)
    print(f"{name}={rendered}")


def _assert_contract(response: Mapping[str, object]) -> None:
    fields = design.BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_DESIGN_RESPONSE_FIELDS
    if (
        type(response) is not dict
        or tuple(response) != fields
        or len(response) != len(fields)
        or not design._validate_response(response)
        or json.loads(design._canonical_json_bytes(response)) != response
    ):
        raise ValueError(_CHECK_ERROR)
    unsigned = {field: response[field] for field in fields[:-1]}
    if response[fields[-1]] != hashlib.sha256(
        design._canonical_json_bytes(unsigned)
    ).hexdigest():
        raise ValueError(_CHECK_ERROR)

    c4 = response["C4_published_response_binding"]
    c2 = response["C2_generate_ligands_ast_evidence"]
    checkpoint = response["real_checkpoint_binding"]
    pdb = response["temporary_PDB_contract"]
    selector = response["Exact6_runtime_contract"]
    cli = response["CLI_argument_semantics"]
    resources = response["resource_bounds"]
    observers = response["transparent_observer_contract"]
    forward_probe = observers["forward_probe"]
    runtime_sources = response["runtime_source_bindings"]
    evidence = response["runtime_evidence_schema"]
    output = response["output_acceptance_contract"]
    workspace = response["temporary_workspace_contract"]
    timeout = response["timeout_contract"]
    if (
        response["C4_published_bound"] is not True
        or response["bounded_runtime_smoke_design_complete"] is not True
        or response["bounded_runtime_smoke_implementation_deferred"] is not False
        or response[
            "fresh_runtime_source_revalidation_required_before_implementation"
        ]
        is not True
        or response["current_mainline_priority"]
        != "implement_and_execute_bounded_covapie_repository_cli_conditioned_runtime_smoke_v1"
        or c4["lifecycle_profile"] != "c4_published_successor"
        or c4["exact_field_count"] != 62
        or response["selected_runtime_smoke_caller"] != "generate_ligands.py"
        or response["deferred_runtime_smoke_callers"]
        != ["scripts/covalent_inpaint_demo.py"]
        or response["deferred_runtime_smoke_caller_count"] != 1
        or checkpoint["size"] != 17_861_341
        or checkpoint["deserialized_by_design"] is not False
        or c2["resolver_call_count"] != 1
        or c2["conditioned_loader_call_count"] != 1
        or c2["legacy_loader_call_count"] != 1
        or c2["selector_forwarded_to_every_batch"] is not True
        or runtime_sources["snapshot_commit"]
        != "011b9558d4a59824e3ba51a0d896ec13100b2b1b"
        or runtime_sources["snapshot_is_ancestor_of_HEAD"] is not True
        or runtime_sources["snapshot_is_ancestor_of_origin_main"] is not True
        or runtime_sources["source_count"] != 3
        or runtime_sources["all_live_bytes_match_snapshot"] is not True
        or runtime_sources["all_non_executable"] is not True
        or selector["selector"]
        != {
            "chain_id": "A",
            "residue_sequence_number": 1,
            "residue_insertion_code": " ",
            "residue_name": "CYS",
            "atom_name": "SG",
            "element": "S",
        }
        or pdb["atom_count"] != 6
        or pdb["SG_count"] != 1
        or cli["pocket_ids"] != ["A:1"]
        or cli["ref_ligand"] is not None
        or resources["device"] != "cpu"
        or resources["n_samples"] != 1
        or resources["num_nodes_lig"] != 4
        or resources["timesteps"] != 1
        or observers["each_calls_original_exactly_once_per_observed_call"] is not True
        or observers["model_replaced"] is not False
        or forward_probe["hook_target"] != "model.ddpm.dynamics"
        or forward_probe["ddpm_type"] != "ConditionalDDPM"
        or forward_probe["expected_dynamics_forward_call_count"] != 2
        or evidence["required_field_count"] != 67
        or output["generated_molecule_count_allowed"] != [0, 1]
        or output["chemical_generation_quality_is_acceptance_condition"] is not False
        or workspace["cleanup_only_if_st_dev_and_st_ino_match"] is not True
        or timeout["parent_timeout_seconds"] != 300
        or response["real_runtime_smoke_executed"] is not False
        or response["model_forward_executed"] is not False
        or response["training_or_parameter_update"] is not False
        or response["RL_implementation_started"] is not False
        or response["subprocess_execution_contract"]["one_time_execution_only"]
        is not True
        or response["subprocess_execution_contract"][
            "repeat_without_new_user_authorization"
        ]
        is not False
        or response["subprocess_execution_contract"]["post_smoke_mainline_priority"]
        != "audit_covapie_five_module_training_path_completion_gaps_v1"
        or response["ready_for_bounded_runtime_smoke_implementation"] is not True
        or response["recommended_next_step"]
        != "implement_and_execute_bounded_covapie_repository_cli_conditioned_runtime_smoke_v1"
    ):
        raise ValueError(_CHECK_ERROR)


def main() -> int:
    first = design.evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1(
        repo_root=ROOT
    )
    second = design.evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1(
        repo_root=ROOT
    )
    if first != second or design._canonical_json_bytes(first) != design._canonical_json_bytes(
        second
    ):
        raise ValueError(_CHECK_ERROR)
    _assert_contract(first)

    _emit("C4_published_bound", first["C4_published_bound"])
    _emit(
        "bounded_runtime_smoke_design_complete",
        first["bounded_runtime_smoke_design_complete"],
    )
    _emit(
        "bounded_runtime_smoke_implementation_deferred",
        first["bounded_runtime_smoke_implementation_deferred"],
    )
    _emit(
        "fresh_runtime_source_revalidation_required_before_implementation",
        first["fresh_runtime_source_revalidation_required_before_implementation"],
    )
    _emit("current_mainline_priority", first["current_mainline_priority"])
    _emit(
        "runtime_source_snapshot_commit",
        first["runtime_source_bindings"]["snapshot_commit"],
    )
    _emit(
        "snapshot_is_ancestor_of_HEAD",
        first["runtime_source_bindings"]["snapshot_is_ancestor_of_HEAD"],
    )
    _emit(
        "snapshot_is_ancestor_of_origin_main",
        first["runtime_source_bindings"][
            "snapshot_is_ancestor_of_origin_main"
        ],
    )
    _emit("selected_runtime_smoke_caller", first["selected_runtime_smoke_caller"])
    _emit(
        "deferred_runtime_smoke_caller_count",
        first["deferred_runtime_smoke_caller_count"],
    )
    _emit("real_checkpoint_bound", first["real_checkpoint_binding"]["regular_file"])
    _emit("target_selector", first["Exact6_runtime_contract"]["selector"])
    _emit("PDB_atom_count", first["temporary_PDB_contract"]["atom_count"])
    _emit("target_SG_count", first["temporary_PDB_contract"]["SG_count"])
    _emit("n_samples", first["resource_bounds"]["n_samples"])
    _emit("num_nodes_lig", first["resource_bounds"]["num_nodes_lig"])
    _emit("timesteps", first["resource_bounds"]["timesteps"])
    _emit("device", first["resource_bounds"]["device"])
    _emit("timeout_seconds", first["timeout_contract"]["parent_timeout_seconds"])
    _emit(
        "forward_hook_target",
        first["transparent_observer_contract"]["forward_probe"]["hook_target"],
    )
    _emit(
        "expected_dynamics_forward_call_count",
        first["transparent_observer_contract"]["forward_probe"][
            "expected_dynamics_forward_call_count"
        ],
    )
    _emit(
        "runtime_evidence_required_field_count",
        first["runtime_evidence_schema"]["required_field_count"],
    )
    _emit(
        "one_time_execution_only",
        first["subprocess_execution_contract"]["one_time_execution_only"],
    )
    _emit(
        "post_smoke_mainline_priority",
        first["subprocess_execution_contract"]["post_smoke_mainline_priority"],
    )
    _emit(
        "chemical_quality_required",
        first["output_acceptance_contract"][
            "chemical_generation_quality_is_acceptance_condition"
        ],
    )
    _emit("real_runtime_smoke_executed", first["real_runtime_smoke_executed"])
    _emit("model_forward_executed", first["model_forward_executed"])
    _emit("training_or_parameter_update", first["training_or_parameter_update"])
    _emit("RL_implementation_started", first["RL_implementation_started"])
    _emit(
        "ready_for_bounded_runtime_smoke_implementation",
        first["ready_for_bounded_runtime_smoke_implementation"],
    )
    _emit("recommended_next_step", first["recommended_next_step"])
    _emit(
        "bounded_runtime_smoke_design_response_sha256",
        first["bounded_runtime_smoke_design_response_sha256"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
