from __future__ import annotations

import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1 as design,
)


ERROR = design._ERROR
BUNDLE_PATH = (
    ROOT.parent
    / "covapie-state/manual-review/"
    "covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1.json"
)


def _assert_canonical_error(action) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        action()


@pytest.fixture(scope="session")
def bundle_bytes() -> bytes:
    return BUNDLE_PATH.read_bytes()


@pytest.fixture(scope="session")
def response_pair(bundle_bytes):
    before = bytes(bundle_bytes)
    rng_before = torch.random.get_rng_state().clone()
    first = design.design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1(
        source_model_consumption_gate_bundle=bundle_bytes,
        repo_root=ROOT,
    )
    rng_after_first = torch.random.get_rng_state().clone()
    second = design.design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1(
        source_model_consumption_gate_bundle=bundle_bytes,
        repo_root=ROOT,
    )
    rng_after_second = torch.random.get_rng_state().clone()
    assert bundle_bytes == before
    assert torch.equal(rng_before, rng_after_first)
    assert torch.equal(rng_before, rng_after_second)
    return first, second


@pytest.fixture(scope="session")
def response(response_pair):
    return response_pair[0]


def test_public_api_and_all_are_exact():
    assert design.__all__ == (
        "design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1",
    )
    assert callable(
        design.design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1
    )


def test_public_api_is_keyword_only():
    signature = inspect.signature(
        design.design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_import_is_silent_and_has_no_output_side_effect(tmp_path):
    environment = dict(os.environ)
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(ROOT / "src"),
            "PYTHONPYCACHEPREFIX": str(tmp_path / "pycache"),
        }
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "import covalent_ext.covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1",
        ],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_exact43_field_order(response):
    assert len(response) == 43
    assert tuple(response) == design.REPOSITORY_CLI_FORWARDING_DESIGN_RESPONSE_FIELDS


def test_response_digest_is_canonical_and_excludes_itself(response):
    digest_payload = dict(response)
    digest = digest_payload.pop("repository_cli_forwarding_design_response_sha256")
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode()
    assert digest == hashlib.sha256(encoded).hexdigest()


def test_public_api_is_deterministic_and_preserves_rng(response_pair):
    assert response_pair[0] == response_pair[1]


def test_response_contains_no_path_or_tensor_objects(response):
    def walk(value):
        assert not isinstance(value, (Path, torch.Tensor))
        if isinstance(value, dict):
            for key, child in value.items():
                walk(key)
                walk(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child)

    walk(response)


def test_gate_bundle_transport_internal_and_shape(bundle_bytes, response):
    assert len(bundle_bytes) == 6449
    assert hashlib.sha256(bundle_bytes).hexdigest() == design._BUNDLE_TRANSPORT_SHA256
    decoded = json.loads(bundle_bytes)
    assert len(decoded) == 43
    assert decoded["model_consumption_gate_response_sha256"] == design._BUNDLE_INTERNAL_SHA256
    assert response["source_model_consumption_gate_bundle_transport_sha256"] == design._BUNDLE_TRANSPORT_SHA256
    assert response["source_model_consumption_gate_bundle_sha256"] == design._BUNDLE_INTERNAL_SHA256


def test_gate_bundle_is_canonical_without_trailing_newline(bundle_bytes):
    assert not bundle_bytes.endswith((b"\n", b"\r"))
    assert design._canonical_json_bytes(json.loads(bundle_bytes)) == bundle_bytes


def test_gate_bundle_readiness_and_cli_state_are_bound(bundle_bytes):
    decoded = json.loads(bundle_bytes)
    assert decoded["model_consumption_gate_implemented"] is True
    assert decoded["ready_for_repository_cli_forwarding_design"] is True
    assert decoded["repository_cli_contract"][
        "repository_cli_selector_forwarding_implemented"
    ] is False
    assert decoded["training_or_parameter_update"] is False
    assert decoded["feature_semantics_audit_required_before_training"] is True


def test_gate_commit_ancestry_and_four_files_are_bound(response):
    evidence = design._gate_source_evidence(ROOT)
    assert all(evidence.values())
    assert response["source_model_consumption_gate_commit"] == design._GATE_COMMIT


def test_gate_design_uses_ancestor_semantics_not_head_equality():
    assert design._is_ancestor(ROOT, design._GATE_COMMIT, "HEAD") is True
    source = Path(design.__file__).read_text()
    assert '"gate_commit_is_head_ancestor"' in source
    assert "HEAD == _GATE_COMMIT" not in source


@pytest.mark.parametrize("relative_path,expected", list(design._CALLER_SHA256S.items()))
def test_all_six_caller_sha256s_are_frozen(relative_path, expected):
    assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected


def test_audited_caller_count_is_six(response):
    assert response["audited_caller_count"] == 6


def test_all_checkpoint_load_sites_are_audited(response):
    assert response["audited_checkpoint_load_site_count"] == 6


def test_all_generate_ligands_sites_are_audited(response):
    assert response["audited_model_generate_ligands_call_count"] == 3


def test_all_direct_prepare_pocket_sites_are_audited(response):
    assert response["audited_prepare_pocket_direct_call_count"] == 3


def test_all_direct_inpaint_and_diversify_sites_are_audited(response):
    assert response["audited_ddpm_inpaint_direct_call_count"] == 3
    assert response["audited_ddpm_diversify_direct_call_count"] == 1


def test_notebook_is_audited_from_json_code_cell_sources():
    audit = design._caller_audit(ROOT)
    assert audit["notebook_json_cell_source_audited"] is True
    assert audit["notebook_code_cell_count"] == 8
    assert audit["by_caller"]["colab/DiffSBDD.ipynb"][
        "LigandPocketDDPM.load_from_checkpoint"
    ] == 1


def test_selected_v1_callers_are_exactly_two(response):
    assert response["selected_v1_supported_callers"] == [
        "generate_ligands.py",
        "scripts/covalent_inpaint_demo.py",
    ]


def test_deferred_callers_are_exactly_four_and_out_of_scope(response):
    deferred = response["deferred_callers"]
    assert [item["caller"] for item in deferred] == [
        "test.py",
        "optimize.py",
        "inpaint.py",
        "colab/DiffSBDD.ipynb",
    ]
    assert all(item["deferred"] is True for item in deferred)
    assert not set(response["selected_v1_supported_callers"]) & {
        item["caller"] for item in deferred
    }


def test_test_py_deferral_requires_per_sample_manifest(response):
    contract = response["selected_test_manifest_deferral_contract"]
    assert contract["caller"] == "test.py"
    assert contract["required_successor_contract"] == "canonical_per_sample_target_manifest"
    assert contract["global_selector_reuse_allowed"] is False


def test_optimize_and_generic_inpaint_deferrals_are_explicit(response):
    contracts = {item["caller"]: item for item in response["deferred_callers"]}
    assert "population_generation" in contracts["optimize.py"][
        "required_successor_contract"
    ]
    assert "single_shared_selector_parser" in contracts["inpaint.py"][
        "required_successor_contract"
    ]


def test_notebook_deferral_binds_distribution_and_checkpoint_mismatch(response):
    contract = response["selected_notebook_deferral_contract"]
    assert contract["caller"] == "colab/DiffSBDD.ipynb"
    assert contract["reason"] == "notebook_clones_upstream_and_uses_a_different_checkpoint"
    assert contract["ui_only_change_cannot_claim_support"] is True


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {
            "target_residue_atom_conditioning": False,
            "target_chain_id": None,
            "target_residue_sequence_number": None,
        },
    ],
)
def test_legacy_target_arguments_are_accepted(arguments):
    assert design._resolve_target_arguments_contract_v1(arguments) is None


def test_complete_conditioned_arguments_compile_exact6():
    selector = design._resolve_target_arguments_contract_v1(
        {
            "target_residue_atom_conditioning": True,
            "target_chain_id": "A",
            "target_residue_sequence_number": 42,
        }
    )
    assert selector == {
        "chain_id": "A",
        "residue_sequence_number": 42,
        "residue_insertion_code": " ",
        "residue_name": "CYS",
        "atom_name": "SG",
        "element": "S",
    }


@pytest.mark.parametrize(
    "arguments",
    [
        {"target_residue_atom_conditioning": True},
        {
            "target_residue_atom_conditioning": True,
            "target_chain_id": "A",
        },
        {
            "target_residue_atom_conditioning": True,
            "target_residue_sequence_number": 42,
        },
        {"target_chain_id": "A", "target_residue_sequence_number": 42},
        {
            "target_residue_atom_conditioning": True,
            "target_chain_id": "",
            "target_residue_sequence_number": 42,
        },
        {
            "target_residue_atom_conditioning": True,
            "target_chain_id": " ",
            "target_residue_sequence_number": 42,
        },
        {
            "target_residue_atom_conditioning": True,
            "target_chain_id": " A ",
            "target_residue_sequence_number": 42,
        },
        {
            "target_residue_atom_conditioning": True,
            "target_chain_id": "\tA",
            "target_residue_sequence_number": 42,
        },
        {
            "target_residue_atom_conditioning": True,
            "target_chain_id": "A",
            "target_residue_sequence_number": True,
        },
        {
            "target_residue_atom_conditioning": True,
            "target_chain_id": "A",
            "target_residue_sequence_number": "42",
        },
        {
            "target_residue_atom_conditioning": True,
            "target_chain_id": "A",
            "target_residue_sequence_number": 42.0,
        },
        {"target_unknown": None},
    ],
)
def test_partial_invalid_or_unknown_target_arguments_fail_closed(arguments):
    _assert_canonical_error(
        lambda: design._resolve_target_arguments_contract_v1(arguments)
    )


@pytest.mark.parametrize(
    "enabled",
    [0, 1, None, "false", "true", torch.tensor(False), torch.tensor(True)],
)
def test_target_enable_flag_requires_exact_bool(enabled):
    _assert_canonical_error(
        lambda: design._resolve_target_arguments_contract_v1(
            {
                "target_residue_atom_conditioning": enabled,
                "target_chain_id": None,
                "target_residue_sequence_number": None,
            }
        )
    )


def test_exact6_contract_forbids_target_guessing(response):
    contract = response["selected_exact6_compilation_contract"]
    assert contract["automatic_target_inference_sources"] == []
    assert contract["resi_list_inference_allowed"] is False
    assert contract["ref_ligand_inference_allowed"] is False
    assert contract["distance_or_nearest_s_inference_allowed"] is False


def test_legacy_loader_strategy_is_unchanged(response):
    contract = response["selected_legacy_mode_contract"]
    assert contract["generate_ligands_non_mask_behavior_unchanged"] is True
    assert contract["existing_checkpoint_loader_path_retained"] is True
    assert "load_from_checkpoint" in contract["loader_call"]
    assert contract["legacy_mask_compatibility_claimed"] is False


def test_checkpoint_payload_and_hyperparameters_are_audited(response):
    contract = response["selected_conditioned_checkpoint_load_strategy"]
    assert contract["checkpoint_size"] == 17861341
    assert contract["checkpoint_sha256"] == design._CHECKPOINT_SHA256
    assert contract["hyper_parameters_type"] == "dict"
    assert len(contract["hyper_parameters_keys"]) == 21
    assert contract["state_dict_key_count"] == 122
    assert contract["mode"] == "pocket_conditioning"
    assert contract["pocket_representation"] == "full-atom"
    assert contract["joint_nf"] == 32


def test_conditioned_model_and_single_key_migration_are_proven(response):
    contract = response["selected_conditioned_checkpoint_load_strategy"]
    assert contract["enabled_model_constructed"] is True
    assert contract["exactly_one_key_filled"] is True
    assert contract["filled_state_keys"] == [design._NEW_STATE_KEY]
    assert contract["new_parameter_zero_initialized"] is True


def test_conditioned_migration_finishes_with_strict_load(response):
    contract = response["selected_conditioned_checkpoint_load_strategy"]
    assert contract["final_strict_load"] is True
    assert contract["missing_keys"] == []
    assert contract["unexpected_keys"] == []
    assert contract["blanket_strict_false"] is False


def test_checkpoint_mapping_tensors_and_disk_are_unchanged(response):
    contract = response["selected_conditioned_checkpoint_load_strategy"]
    assert contract["base_mapping_unchanged"] is True
    assert contract["base_tensors_unchanged"] is True
    assert contract["checkpoint_file_modified"] is False
    assert hashlib.sha256((ROOT / design._CHECKPOINT_PATH).read_bytes()).hexdigest() == design._CHECKPOINT_SHA256


def test_central_helper_owns_arguments_selector_loader_and_errors(response):
    contract = response["selected_checkpoint_migration_helper"]
    assert len(contract["public_apis"]) == 3
    assert set(contract["responsibilities"]) == {
        "argument_definition",
        "Exact6_compilation",
        "conditioned_checkpoint_loading",
        "canonical_error_normalization",
    }
    assert contract["duplicate_parser_or_loader_logic_allowed"] is False


def test_generate_ligands_future_forwarding_point_is_unique(response):
    contract = response["selected_generate_ligands_forwarding_contract"]
    assert contract["caller"] == "generate_ligands.py"
    assert contract["forward_to"] == "model.generate_ligands"
    assert contract["forward_keyword"] == "target_residue_atom_condition_spec"
    assert contract["selector_forwarding_site_count"] == 1


def test_demo_future_prepare_pocket_forwarding_point_is_unique(response):
    contract = response["selected_covalent_inpaint_forwarding_contract"]
    assert contract["caller"] == "scripts/covalent_inpaint_demo.py"
    assert contract["forward_path"][-1] == "model.prepare_pocket"
    assert contract["prepare_pocket_selector_forwarding_site_count"] == 1
    assert contract["manual_indicator_creation_allowed"] is False


def test_existing_model_entry_points_already_consume_selector():
    evidence = design._model_and_mask_source_audit(ROOT)
    assert evidence["generate_ligands_selector_parameter_present"] is True
    assert evidence["generate_ligands_forwards_selector_to_prepare_pocket"] is True
    assert evidence["prepare_pocket_selector_parameter_present"] is True
    assert evidence["prepare_pocket_builds_indicator"] is True


def test_current_runtime_is_not_retired_but_retirement_target_is_selected(response):
    contract = response["selected_mask_semantic_normalization_contract"]
    assert contract["canonical_five_level_target_selected"] is True
    assert contract["canonical_five_level_contract_complete"] is True
    assert contract["legacy_four_level_retirement_selected"] is True
    assert contract["legacy_four_level_retirement_implemented"] is False
    assert contract["current_legacy_four_level_runtime_present"] is True
    assert contract["current_legacy_four_level_cli_input_present"] is True
    assert contract["current_legacy_four_level_schema_present"] is True


def test_current_and_target_active_residual_counts_are_distinct(response):
    contract = response["selected_mask_semantic_normalization_contract"]
    assert contract["current_active_legacy_reference_count"] == 14
    assert contract["current_active_legacy_reference_path_count"] == 5
    assert contract["target_active_legacy_reference_count"] == 0
    assert contract["target_active_legacy_reference_path_count"] == 0


@pytest.mark.parametrize(
    "canonical_name,internal,display_alias",
    [
        ("warhead_only", "A_warhead_only", "A"),
        ("linker_plus_warhead", "B_linker_warhead", "B"),
        ("scaffold_plus_warhead", "B2_scaffold_warhead", "B2"),
        ("scaffold_only", "B3_scaffold_only", "B3"),
        (
            "scaffold_plus_linker_plus_warhead",
            "C_scaffold_linker_warhead",
            "C",
        ),
    ],
)
def test_five_canonical_mask_inputs_map_to_internal_and_display(
    canonical_name, internal, display_alias
):
    assert design._resolve_canonical_mask_semantic_contract_v1(canonical_name) == {
        "canonical_semantic_name": canonical_name,
        "internal_long_form_mask": internal,
        "display_alias": display_alias,
    }


@pytest.mark.parametrize("legacy_alias", ["A", "B", "B2", "B3", "C"])
def test_short_aliases_are_rejected_as_runtime_input(legacy_alias):
    _assert_canonical_error(
        lambda: design._resolve_canonical_mask_semantic_contract_v1(legacy_alias)
    )


@pytest.mark.parametrize("internal_name", design._LEGACY_INTERNAL_LONG_FORM_NAMES)
def test_internal_long_form_names_are_rejected_as_cli_input(internal_name):
    _assert_canonical_error(
        lambda: design._resolve_canonical_mask_semantic_contract_v1(internal_name)
    )


@pytest.mark.parametrize("bad_value", ["", "unknown", None, 0, True])
def test_unknown_empty_or_non_string_mask_fails_closed(bad_value):
    _assert_canonical_error(
        lambda: design._resolve_canonical_mask_semantic_contract_v1(bad_value)
    )


def test_only_mask_semantic_flag_is_selected_without_dual_surface(response):
    contract = response["selected_mask_semantic_normalization_contract"]
    inpaint = response["selected_covalent_inpaint_forwarding_contract"]
    assert contract["canonical_input_flag"] == "--mask_semantic"
    assert contract["legacy_input_flag"] is None
    assert inpaint["canonical_mask_flag"] == "--mask_semantic"
    assert inpaint["legacy_mask_flag"] is None


def test_build_long_form_mask_is_only_future_builder_without_fallback(response):
    contract = response["selected_mask_semantic_normalization_contract"]
    inpaint = response["selected_covalent_inpaint_forwarding_contract"]
    assert contract["target_internal_builder"] == "build_long_form_mask"
    assert contract["target_legacy_builder_fallback_allowed"] is False
    assert inpaint["mask_builder"] == "build_long_form_mask"
    assert inpaint["legacy_four_level_fallback_allowed"] is False


def test_legacy_tokens_are_not_runtime_training_or_automatic_migration_inputs(response):
    contract = response["selected_mask_semantic_normalization_contract"]
    failure = response["selected_failure_contract"]
    assert contract["target_legacy_four_level_runtime_supported"] is False
    assert contract["target_legacy_four_level_cli_input_supported"] is False
    assert contract["target_legacy_short_alias_input_supported"] is False
    assert contract["target_legacy_short_mask_tokens_training_accepted"] is False
    assert contract["target_legacy_automatic_translation_allowed"] is False
    assert failure["legacy_mask_token_automatic_migration"] is False
    assert failure["historical_B2_automatic_interpretation"] is None


def test_canonical_b2_and_b3_are_unambiguous(response):
    contract = response["selected_mask_semantic_normalization_contract"]
    assert contract["canonical_B2_semantic"] == "scaffold_plus_warhead"
    assert contract["canonical_B3_semantic"] == "scaffold_only"
    assert contract["ambiguous_legacy_B2_reinterpretation_allowed"] is False


def test_scaffold_only_exists_and_no_sixth_mask(response):
    names = response["canonical_mask_semantic_names"]
    contract = response["selected_mask_semantic_normalization_contract"]
    assert len(names) == 5
    assert "scaffold_plus_warhead" in names
    assert "scaffold_only" in names
    assert contract["sixth_mask_added"] is False


def test_repository_legacy_reference_inventory_is_complete(response):
    inventory = response["selected_mask_semantic_normalization_contract"][
        "legacy_reference_inventory"
    ]
    assert inventory["inventory_complete"] is True
    assert inventory["notebook_json_cell_source_audited"] is True
    assert inventory["reference_count"] == len(inventory["records"])
    assert inventory["reference_count"] == 45
    assert inventory["classification_counts"] == {
        "active_runtime": 14,
        "test_only": 7,
        "documentation_only": 8,
        "historical_freeze_only": 8,
        "design_evidence_only": 8,
    }
    assert inventory["active_legacy_reference_count"] == 14
    assert inventory["active_legacy_reference_path_count"] == 5
    assert inventory["unresolved_active_reference_count"] == 0
    assert inventory["active_legacy_reference_paths"] == [
        "scripts/check_covalent_masking.py",
        "scripts/covalent_inpaint_demo.py",
        "src/covalent_ext/dataset.py",
        "src/covalent_ext/masking.py",
        "src/covalent_ext/schema.py",
    ]
    assert all(inventory["classification_counts"][name] > 0 for name in (
        "active_runtime",
        "test_only",
        "documentation_only",
        "historical_freeze_only",
        "design_evidence_only",
    ))


def test_every_active_legacy_reference_has_a_future_action_and_scope(response):
    inventory = response["selected_mask_semantic_normalization_contract"][
        "legacy_reference_inventory"
    ]
    active = [item for item in inventory["records"] if item["active_runtime"]]
    scoped = {
        path
        for step in inventory["future_retirement_implementation_scope"][
            "ordered_steps"
        ]
        if step["step"] in {"R1", "R2"}
        for path in step["paths"]
    }
    assert all(
        item["required_future_action"]
        != "UNRESOLVED_ACTIVE_LEGACY_REFERENCE"
        for item in active
    )
    assert all(item["path"] in scoped for item in active)
    assert inventory["all_active_legacy_references_in_future_scope"] is True
    assert inventory["all_active_references_have_future_actions"] is True
    assert inventory["unresolved_legacy_mask_references"] == []
    assert all(
        item["retirement_increment"]
        == ("R2" if item["path"] == "scripts/covalent_inpaint_demo.py" else "R1")
        for item in active
    )


def test_test_only_references_are_assigned_by_validation_object(response):
    inventory = response["selected_mask_semantic_normalization_contract"][
        "legacy_reference_inventory"
    ]
    test_records = [item for item in inventory["records"] if item["test_only"]]
    assert len(test_records) == 7
    assert all(item["retirement_increment"] == "R1" for item in test_records)
    assert all(item["post_increment_expected_status"] for item in test_records)


def test_uncovered_active_legacy_reference_forces_readiness_false(response):
    inventory = dict(
        response["selected_mask_semantic_normalization_contract"][
            "legacy_reference_inventory"
        ]
    )
    inventory["all_active_legacy_references_in_future_scope"] = False
    inventory["unresolved_legacy_mask_references"] = [
        {"path": "unknown.py", "required_future_action": "UNRESOLVED"}
    ]
    inventory["unresolved_active_reference_count"] = 1
    assert design._ready_for_legacy_four_level_mask_retirement_implementation(
        inventory,
        canonical_five_level_contract_complete=True,
    ) is False


def test_future_order_is_exactly_r1_r2_r3_then_c1_through_c4(response):
    scope = response["selected_mask_semantic_normalization_contract"][
        "future_retirement_implementation_scope"
    ]
    assert scope["incremental_commits_required"] is True
    assert scope["single_commit_for_all_increments_allowed"] is False
    assert scope["cli_forwarding_may_begin_before_R3"] is False
    assert [item["step"] for item in scope["ordered_steps"]] == [
        "R1", "R2", "R3", "C1", "C2", "C3", "C4"
    ]


def test_r1_scope_retires_core_but_not_full_runtime(response):
    steps = response["selected_mask_semantic_normalization_contract"][
        "future_retirement_implementation_scope"
    ]["ordered_steps"]
    r1 = steps[0]
    assert r1["objective"] == "remove_legacy_four_level_core_runtime_interfaces"
    assert {
        "src/covalent_ext/masking.py",
        "src/covalent_ext/schema.py",
        "src/covalent_ext/dataset.py",
        "scripts/check_covalent_masking.py",
        "tests/test_covalent_masking.py",
    }.issubset(set(r1["paths"]))
    assert r1["completion_contract"]["legacy_four_level_core_api_retired"] is True
    assert r1["completion_contract"]["legacy_four_level_full_runtime_retired"] is False


def test_r2_scope_removes_final_demo_dependency_but_still_requires_r3(response):
    steps = response["selected_mask_semantic_normalization_contract"][
        "future_retirement_implementation_scope"
    ]["ordered_steps"]
    r2 = steps[1]
    assert r2["objective"] == (
        "remove_final_active_cli_caller_dependency_on_legacy_four_level_masks"
    )
    assert "scripts/covalent_inpaint_demo.py" in r2["paths"]
    assert r2["completion_contract"]["legacy_mask_flag_removed"] == (
        design._LEGACY_MASK_SYMBOLS[-1]
    )
    assert r2["completion_contract"]["only_canonical_mask_flag_added"] == "--mask_semantic"
    assert r2["completion_contract"][
        "candidate_full_runtime_retirement_requires_R3_gate"
    ] is True


def test_r3_zero_residual_gate_contract_is_complete(response):
    contract = response["selected_mask_semantic_normalization_contract"][
        "zero_active_legacy_reference_retirement_gate_contract"
    ]
    assert contract["gate_step"] == "R3"
    assert contract["post_retirement_active_legacy_reference_count"] == 0
    assert contract["post_retirement_unresolved_legacy_reference_count"] == 0
    assert all(
        value is False
        for value in contract["required_negative_runtime_evidence"].values()
    )
    assert contract["canonical_five_level_runtime_complete"] is True
    assert set(contract["scan_methods"]) == {
        "python_ast",
        "notebook_json_cell_source_ast",
        "structured_schema_inspection",
        "controlled_text_search",
    }
    assert contract["broad_ignore_docs_allowed"] is False
    assert contract["broad_ignore_data_allowed"] is False
    assert contract["gate_must_pass_and_be_committed_before_C1"] is True


def test_zero_residual_means_active_zero_not_textual_zero(response):
    contract = response["selected_mask_semantic_normalization_contract"][
        "zero_active_legacy_reference_retirement_gate_contract"
    ]
    assert contract["repository_text_must_contain_zero_legacy_strings"] is False
    assert contract["correct_terminal_condition"] == (
        "zero_active_legacy_references_with_explicit_read_only_historical_evidence_retained"
    )


def test_historical_legacy_artifacts_remain_read_only(response):
    contract = response["selected_mask_semantic_normalization_contract"]
    inventory = contract["legacy_reference_inventory"]
    assert contract["historical_read_only_legacy_evidence_retained"] is True
    assert inventory["classification_counts"]["historical_freeze_only"] > 0
    assert all(
        item["required_future_action"] == "preserve_read_only_historical_evidence"
        for item in inventory["records"]
        if item["historical_freeze_only"]
    )
    assert all(
        item["active_runtime"] is False
        for item in inventory["records"]
        if item["historical_freeze_only"]
    )
    whitelist = contract[
        "zero_active_legacy_reference_retirement_gate_contract"
    ]["historical_whitelist_paths"]
    assert whitelist
    assert "docs/" not in whitelist
    assert "data/" not in whitelist
    whitelist_contract = contract[
        "zero_active_legacy_reference_retirement_gate_contract"
    ]["whitelist_entry_contract"]
    assert whitelist_contract["active_runtime"] is False
    assert whitelist_contract["runtime_importable"] is False
    assert whitelist_contract["runtime_callable"] is False
    assert whitelist_contract["schema_admissible"] is False
    assert whitelist_contract["training_admissible"] is False


def test_source_drift_fails_closed():
    _assert_canonical_error(
        lambda: design._regular_file_bytes(
            ROOT,
            "generate_ligands.py",
            expected_sha256="0" * 64,
        )
    )


def test_checkpoint_drift_fails_closed():
    _assert_canonical_error(
        lambda: design._regular_file_bytes(
            ROOT,
            design._CHECKPOINT_PATH,
            expected_sha256="0" * 64,
            expected_size=design._CHECKPOINT_SIZE,
            max_size=design._MAX_CHECKPOINT_BYTES,
        )
    )


def test_corrupt_bundle_fails_with_only_canonical_value_error(bundle_bytes):
    corrupt = bytearray(bundle_bytes)
    corrupt[-2] ^= 1
    _assert_canonical_error(
        lambda: design.design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1(
            source_model_consumption_gate_bundle=bytes(corrupt),
            repo_root=ROOT,
        )
    )


def test_public_api_rejects_positional_arguments(bundle_bytes):
    with pytest.raises(TypeError):
        design.design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1(
            bundle_bytes, ROOT
        )


def test_real_callers_and_model_sources_have_not_been_modified(response):
    for relative_path, expected in design._CALLER_SHA256S.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected
    assert hashlib.sha256((ROOT / "lightning_modules.py").read_bytes()).hexdigest() == response[
        "source_lightning_module_sha256"
    ]
    assert hashlib.sha256(
        (
            ROOT
            / "src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py"
        ).read_bytes()
    ).hexdigest() == response["source_checkpoint_migration_sha256"]
    protected = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--",
            "generate_ligands.py",
            "test.py",
            "optimize.py",
            "inpaint.py",
            "scripts/covalent_inpaint_demo.py",
            "colab/DiffSBDD.ipynb",
            "src/covalent_ext/masking.py",
            "src/covalent_ext/schema.py",
            "lightning_modules.py",
            "equivariant_diffusion",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert protected.stdout == ""


def test_no_forward_training_or_parameter_update_was_executed(response):
    contract = response["selected_conditioned_checkpoint_load_strategy"]
    assert contract["model_forward_executed"] is False
    assert response["training_or_parameter_update"] is False
    assert response["repository_cli_selector_forwarding_implemented"] is False


def test_readiness_is_derived_from_complete_evidence(response):
    mask_contract = response["selected_mask_semantic_normalization_contract"]
    assert mask_contract[
        "ready_for_legacy_four_level_mask_retirement_implementation"
    ] is True
    assert mask_contract["legacy_four_level_retirement_implemented"] is False
    assert mask_contract["retirement_R3_gate_passed"] is False
    assert mask_contract["retirement_R3_gate_committed"] is False
    assert response["ready_for_repository_cli_forwarding_implementation"] is False
    assert response["recommended_next_step"] == (
        "implement_covapie_legacy_four_level_mask_retirement_v1"
    )
    assert response["feature_semantics_audit_required_before_training"] is True
    assert response["selected_failure_contract"]["fail_closed"] is True
    assert len(response["selected_failure_contract"]["rejected_conditions"]) == 18
    assert response["selected_conditioned_mode_contract"][
        "target_enable_flag_exact_bool_required"
    ] is True
