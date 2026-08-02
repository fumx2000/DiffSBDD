from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import torch

from covalent_ext import covapie_target_residue_atom_condition_model_consumption_design_v1 as design
from covalent_ext import covapie_target_residue_atom_condition_runtime_bridge_gate_v1 as gate


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state/manual-review"
BUNDLE_PATH = STATE / "covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1.json"
ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_MODEL_CONSUMPTION_DESIGN_INVALID"


@pytest.fixture(scope="session")
def source_bundle() -> bytes:
    return BUNDLE_PATH.read_bytes()


@pytest.fixture(scope="session")
def response(source_bundle: bytes) -> dict[str, object]:
    return design.design_covapie_target_residue_atom_condition_model_consumption_v1(
        source_runtime_bridge_gate_bundle=source_bundle,
        repo_root=ROOT,
    )


def _error(action) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        action()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _inject(
    hidden: torch.Tensor, indicator: torch.Tensor, embedding: torch.Tensor,
) -> torch.Tensor:
    return hidden + indicator.to(dtype=hidden.dtype).unsqueeze(1) * embedding.unsqueeze(0)


def test_public_api_all_keyword_only_and_silent_import():
    function = design.design_covapie_target_residue_atom_condition_model_consumption_v1
    assert design.__all__ == (
        "design_covapie_target_residue_atom_condition_model_consumption_v1",
    )
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == (
        "source_runtime_bridge_gate_bundle", "repo_root",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    completed = subprocess.run(
        [
            sys.executable, "-B", "-c",
            "import covalent_ext.covapie_target_residue_atom_condition_model_consumption_design_v1",
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src"},
        check=False,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""


def test_runtime_bridge_gate_transport_internal_schema_and_canonical(source_bundle):
    assert hashlib.sha256(source_bundle).hexdigest() == design._GATE_BUNDLE_TRANSPORT_SHA256
    decoded = gate._strict_json(source_bundle)
    assert gate._canonical_json_bytes(decoded) == source_bundle
    assert gate._validate_bundle(decoded, require_field_order=False)
    assert decoded["runtime_bridge_gate_bundle_sha256"] == design._GATE_BUNDLE_INTERNAL_SHA256


def test_runtime_bridge_gate_current11_lineage_projection(source_bundle):
    decoded = gate._strict_json(source_bundle)
    projection = gate._current11_runtime_bridge_gate_record_lineage_projection(
        decoded["current11_records"]
    )
    assert hashlib.sha256(gate._canonical_json_bytes(projection)).hexdigest() == (
        design._CURRENT11_LINEAGE_PROJECTION_SHA256
    )
    assert decoded["current11_record_count"] == 11
    assert decoded["total_runtime_pocket_node_count"] == 2202
    assert decoded["total_runtime_indicator_true_count"] == 11


def test_gate_readiness_boundary_is_bound(source_bundle):
    decoded = gate._strict_json(source_bundle)
    assert decoded["ready_for_model_consumption_design"] is True
    assert decoded["recommended_next_step"] == (
        "design_covapie_target_residue_atom_condition_model_consumption_v1"
    )
    assert decoded["repository_cli_selector_forwarding_implemented"] is False
    assert decoded["indicator_consumed_by_model"] is False
    assert decoded["indicator_passed_into_dynamics"] is False
    assert decoded["feature_semantics_audit_required_before_training"] is True


def test_gate_production_sha_commit_parent_and_ancestry(response):
    path = ROOT / design._GATE_PRODUCTION_PATH
    assert hashlib.sha256(path.read_bytes()).hexdigest() == design._GATE_PRODUCTION_SHA256
    metadata = subprocess.run(
        ["git", "show", "-s", "--format=%H%n%P", design._GATE_COMMIT],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    assert metadata == [design._GATE_COMMIT, design._GATE_PARENT]
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", design._GATE_COMMIT, "HEAD"],
        cwd=ROOT, check=False, capture_output=True,
    ).returncode == 0
    assert response["source_runtime_bridge_gate_commit"] == design._GATE_COMMIT


def test_gate_commit_ancestor_helper_supports_uncommitted_post_commit_and_post_push_states(
    tmp_path,
):
    repository = tmp_path / "lifecycle-repository"
    repository.mkdir()

    def git(*arguments):
        return subprocess.run(
            ["git", *arguments],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    git("init", "-q")
    git("config", "user.name", "CovaPIE Test")
    git("config", "user.email", "covapie-test@example.invalid")
    marker = repository / "design.txt"
    marker.write_text("base\n", encoding="utf-8")
    git("add", "design.txt")
    git("commit", "-q", "-m", "base")
    base = git("rev-parse", "HEAD")
    git("update-ref", "refs/remotes/origin/main", base)

    assert design._git_commit_is_ancestor(
        repo_root=repository, base_commit=base, head_ref="HEAD"
    )
    assert design._git_commit_is_ancestor(
        repo_root=repository, base_commit=base, head_ref="origin/main"
    )

    marker.write_text("successor\n", encoding="utf-8")
    assert design._git_commit_is_ancestor(
        repo_root=repository, base_commit=base, head_ref="HEAD"
    )
    assert design._git_commit_is_ancestor(
        repo_root=repository, base_commit=base, head_ref="origin/main"
    )
    git("add", "design.txt")
    git("commit", "-q", "-m", "successor")
    successor = git("rev-parse", "HEAD")

    assert design._git_commit_is_ancestor(
        repo_root=repository, base_commit=base, head_ref="HEAD"
    )
    assert design._git_commit_is_ancestor(
        repo_root=repository, base_commit=base, head_ref="origin/main"
    )
    git("update-ref", "refs/remotes/origin/main", successor)
    assert design._git_commit_is_ancestor(
        repo_root=repository, base_commit=base, head_ref="HEAD"
    )
    assert design._git_commit_is_ancestor(
        repo_root=repository, base_commit=base, head_ref="origin/main"
    )
    assert not design._git_commit_is_ancestor(
        repo_root=repository, base_commit=successor, head_ref=base
    )


def test_design_production_has_no_exact_head_or_origin_tip_requirement():
    source = Path(design.__file__).read_text(encoding="utf-8")
    assert '_git(repo_root, "rev-parse", "HEAD")' not in source
    assert '_git(repo_root, "rev-parse", "origin/main")' not in source

    tree = ast.parse(source)
    validator = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_validate_formal_gate"
    )
    ancestor_calls = [
        node
        for node in ast.walk(validator)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_git_commit_is_ancestor"
    ]
    assert len(ancestor_calls) == 2
    head_refs = {
        keyword.value.value
        for call in ancestor_calls
        for keyword in call.keywords
        if keyword.arg == "head_ref" and isinstance(keyword.value, ast.Constant)
    }
    assert head_refs == {"HEAD", "origin/main"}
    assert all(
        any(
            keyword.arg == "base_commit"
            and isinstance(keyword.value, ast.Name)
            and keyword.value.id == "_GATE_COMMIT"
            for keyword in call.keywords
        )
        for call in ancestor_calls
    )


@pytest.mark.parametrize("relative_path,expected", tuple(design._SOURCE_SHA256.items()))
def test_five_model_source_hashes_and_committed_bytes(relative_path, expected):
    current = (ROOT / relative_path).read_bytes()
    committed = subprocess.run(
        ["git", "show", f"{design._GATE_COMMIT}:{relative_path}"],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout
    assert current == committed
    assert hashlib.sha256(current).hexdigest() == expected


def test_checkpoint_size_sha_and_top_level_metadata(response):
    path = ROOT / design._CHECKPOINT_PATH
    before = path.stat()
    assert before.st_size == design._CHECKPOINT_SIZE
    assert hashlib.sha256(path.read_bytes()).hexdigest() == design._CHECKPOINT_SHA256
    profile = response["checkpoint_profile"]
    assert profile["checkpoint_top_level_keys"] == [
        "epoch", "global_step", "pytorch-lightning_version", "state_dict",
        "loops", "callbacks", "optimizer_states", "lr_schedulers",
        "hparams_name", "hyper_parameters",
    ]
    assert path.stat() == before


def test_checkpoint_actual_mode_widths_and_time_condition(response):
    profile = response["checkpoint_profile"]
    assert profile["hyper_parameters_mode"] == "pocket_conditioning"
    assert profile["hyper_parameters_pocket_representation"] == "full-atom"
    assert profile["joint_nf"] == 32
    assert profile["atom_nf"] == 10
    assert profile["residue_nf"] == 10
    assert profile["condition_time"] is True
    assert profile["egnn_input_nf"] == 33


def test_checkpoint_state_key_and_shape_manifests(response):
    profile = response["checkpoint_profile"]
    tensor_manifest = profile["state_dict_tensor_shape_dtype_manifest"]
    ordered_keys = [record["key"] for record in tensor_manifest]
    assert len(ordered_keys) == profile["state_dict_key_count"] == 122
    assert hashlib.sha256(_canonical(ordered_keys)).hexdigest() == (
        profile["state_dict_ordered_key_manifest_sha256"]
    )
    assert profile["state_dict_ordered_key_manifest_sha256"] == (
        design._CHECKPOINT_KEY_MANIFEST_SHA256
    )
    assert hashlib.sha256(_canonical(tensor_manifest)).hexdigest() == (
        profile["state_dict_shape_dtype_manifest_sha256"]
    )
    assert profile["state_dict_shape_dtype_manifest_sha256"] == (
        design._CHECKPOINT_SHAPE_MANIFEST_SHA256
    )
    assert all(
        tuple(record) == ("key", "shape", "dtype")
        and isinstance(record["shape"], list)
        and record["dtype"].startswith("torch.")
        for record in tensor_manifest
    )


def test_checkpoint_dynamics_prefix_and_new_key_evidence(response):
    profile = response["checkpoint_profile"]
    assert profile["egnn_dynamics_state_key_prefix"] == "ddpm.dynamics."
    assert profile["egnn_dynamics_state_key_count"] == 120
    assert len(profile["egnn_dynamics_state_keys"]) == 120
    assert all(
        key.startswith("ddpm.dynamics.")
        for key in profile["egnn_dynamics_state_keys"]
    )
    assert profile["selected_enabled_parameter_full_state_key"] == design._NEW_STATE_KEY
    assert profile["selected_enabled_parameter_present_in_base_checkpoint"] is False
    assert profile["selected_enabled_parameter_actual_shape_for_checkpoint"] == [32]


def test_all_eight_dynamics_call_sites_are_exact_and_covered(response):
    records = response["audited_dynamics_call_site_records"]
    identities = {
        (r["source_path"], r["class"], r["method"], r["source_line"])
        for r in records
    }
    assert len(records) == 8
    assert identities == set(design._EXPECTED_DYNAMICS_SITES)
    assert all(r["covered"] is True and r["blocking_reason"] == [] for r in records)
    assert all(len(r["current_arguments"]) == 5 for r in records)


@pytest.mark.parametrize(
    "class_name,method,lines",
    [
        ("ConditionalDDPM", "forward", {253, 306}),
        ("ConditionalDDPM", "sample_p_zs_given_zt", {445}),
        ("ConditionalDDPM", "sample_p_xh_given_z0", {119}),
        ("EnVariationalDiffusion", "forward", {378, 436}),
        ("EnVariationalDiffusion", "sample_p_zs_given_zt", {516}),
        ("EnVariationalDiffusion", "sample_p_xh_given_z0", {270}),
    ],
)
def test_dynamics_training_eval_sampling_profiles(response, class_name, method, lines):
    selected = {
        record["source_line"]
        for record in response["audited_dynamics_call_site_records"]
        if record["class"] == class_name and record["method"] == method
    }
    assert selected == lines


def test_all_checkpoint_load_sites_are_discovered_and_classified(response):
    records = response["audited_checkpoint_load_site_records"]
    assert len(records) == 24
    identities = {
        (r["caller_path"], r["load_kind"], r["context"])
        for r in records
    }
    assert identities == design._EXPECTED_CHECKPOINT_SITE_IDENTITIES
    assert all(r["covered"] is True and r["blocking_reason"] == [] for r in records)
    assert sum(r["load_kind"] == "LigandPocketDDPM.load_from_checkpoint" for r in records) == 6
    assert sum(r["load_kind"] == "torch.load" for r in records) == 13
    assert sum(r["load_kind"] == "load_state_dict" for r in records) == 5


def test_cli_notebook_training_and_historical_checkpoint_surfaces(response):
    records = response["audited_checkpoint_load_site_records"]
    assert all(
        any(record["caller_path"] == path for record in records)
        for path in (
            "generate_ligands.py", "test.py", "optimize.py", "inpaint.py",
            "scripts/covalent_inpaint_demo.py", "train.py", "colab/DiffSBDD.ipynb",
        )
    )
    assert all(
        record["cli_impact"] is True
        for record in records
        if record["caller_path"] in design._MODEL_CLI_LOAD_PATHS
        or record["caller_path"] == "train.py"
    )


def test_existing_historical_strict_false_is_not_accepted_for_migration(response):
    records = response["audited_checkpoint_load_site_records"]
    strict_false = [r for r in records if "strict=False" in r["current_api"]]
    assert len(strict_false) == 1
    assert strict_false[0]["current_strict_semantics"] == (
        "explicit_strict_false_historical_smoke_only"
    )
    assert strict_false[0]["conditioned_profile"] == (
        "forbidden_for_base_to_conditioned_migration"
    )


def test_exact47_fields_order_and_response_digest(response):
    assert len(design.MODEL_CONSUMPTION_DESIGN_RESPONSE_FIELDS) == 47
    assert len(response) == 47
    assert tuple(response) == design.MODEL_CONSUMPTION_DESIGN_RESPONSE_FIELDS
    without_digest = {
        field: response[field]
        for field in design.MODEL_CONSUMPTION_DESIGN_RESPONSE_FIELDS
        if field != "model_consumption_design_response_sha256"
    }
    assert hashlib.sha256(_canonical(without_digest)).hexdigest() == (
        response["model_consumption_design_response_sha256"]
    )


def test_deterministic_and_inputs_unchanged(source_bundle, response):
    snapshot = bytes(source_bundle)
    second = design.design_covapie_target_residue_atom_condition_model_consumption_v1(
        source_runtime_bridge_gate_bundle=source_bundle,
        repo_root=ROOT,
    )
    assert source_bundle == snapshot
    assert second == response
    assert _canonical(second) == _canonical(response)


def test_zero_writes_and_no_path_objects(source_bundle):
    before = subprocess.run(
        ["git", "status", "--porcelain=v1", "-uall"],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout
    result = design.design_covapie_target_residue_atom_condition_model_consumption_v1(
        source_runtime_bridge_gate_bundle=source_bundle,
        repo_root=ROOT,
    )
    after = subprocess.run(
        ["git", "status", "--porcelain=v1", "-uall"],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout
    assert before == after
    assert not design._contains_path(result)


def test_frozen_condition_flag_argument_and_parameter_names(response):
    assert response["selected_condition_field_name"] == (
        "pocket_target_residue_atom_condition_indicator"
    )
    assert response["selected_enable_flag_name"] == "target_residue_atom_conditioning"
    assert response["selected_dynamics_argument_name"] == (
        "pocket_target_residue_atom_condition_indicator"
    )
    assert response["selected_parameter_name"] == (
        "target_residue_atom_condition_embedding"
    )


@pytest.mark.parametrize(
    "candidate,decision",
    [
        ("append_indicator_to_pocket_one_hot", "rejected"),
        ("append_indicator_to_time_channel", "rejected"),
        ("duplicate_target_coordinates_or_add_target_pseudo_node", "rejected"),
        ("expand_edge_type_embedding", "deferred"),
        ("fixed_nonlearnable_hidden_channel_shift", "rejected"),
        ("multi_layer_condition_encoder", "rejected_for_v1"),
        ("optional_zero_initialized_target_node_embedding_after_residue_encoder", "accepted"),
    ],
)
def test_candidate_decision_matrix(response, candidate, decision):
    matrix = {item["candidate"]: item for item in response["candidate_decisions"]}
    assert len(matrix) == 7
    assert matrix[candidate]["decision"] == decision
    assert matrix[candidate]["reasons"]


def test_selected_zero_init_embedding_and_precise_injection_point(response):
    assert response["selected_injection_module"] == "EGNNDynamics"
    assert response["selected_injection_point"] == (
        "after_residue_encoder_before_atom_residue_concatenation_and_before_time_concatenation"
    )
    assert response["selected_condition_representation"] == (
        "same_name_per_pocket_node_bool_sidecar"
    )
    assert response["selected_parameter_shape"] == ["joint_nf"]
    assert response["selected_parameter_initialization"] == "all_zeros"


def test_parameter_creation_disabled_and_enabled_profiles(response):
    policy = response["selected_parameter_creation_policy"]
    assert policy["flag_default"] is False
    assert policy["disabled"].endswith("_None")
    assert policy["enabled"] == (
        "create_exactly_one_Parameter_shape_joint_nf_initialized_all_zeros"
    )
    assert policy["additional_parameters"] == []
    assert policy["buffers_added"] == []


def test_legacy_disabled_state_dict_exact_and_strict(response):
    policy = response["legacy_disabled_state_dict_policy"]
    assert policy == {
        "enable_flag": False,
        "new_parameter_key_present": False,
        "existing_key_set_unchanged": True,
        "existing_tensor_shapes_unchanged": True,
        "legacy_strict_load": True,
        "missing_keys": [],
        "unexpected_keys": [],
    }


def test_base_to_conditioned_exact_one_missing_key_and_no_blanket_nonstrict(response):
    policy = response["base_to_conditioned_checkpoint_migration_policy"]
    assert policy["allowed_missing_keys_before_fill"] == [design._NEW_STATE_KEY]
    assert policy["allowed_unexpected_keys"] == []
    assert policy["fill_from_current_model_zero_initialized_tensor"] is True
    assert policy["final_load_state_dict_strict"] is True
    assert policy["final_missing_keys"] == []
    assert policy["final_unexpected_keys"] == []
    assert policy["blanket_strict_false"] is False
    assert policy["automatic_reshape"] is False
    assert policy["disk_checkpoint_modified"] is False


def test_conditioned_checkpoint_strict_contract(response):
    policy = response["conditioned_checkpoint_strict_load_policy"]
    assert policy["enable_flag"] is True
    assert policy["new_full_state_key_required"] == design._NEW_STATE_KEY
    assert policy["strict_load"] is True
    assert policy["fallback_to_nonstrict"] is False


def test_absent_present_all_false_and_enable_flag_semantics(response):
    semantics = response["condition_presence_semantics"]
    assert semantics["validation_boundary"] == (
        "top_level_validate_once_then_thread_static_tensor"
    )
    assert semantics["legacy_absent"]["allowed_enable_flags"] == [False, True]
    assert semantics["legacy_absent"]["legacy_output_preserved"] is True
    assert semantics["covalent_present"]["required_enable_flag"] is True
    assert semantics["covalent_present"]["flag_false_fail_closed"] is True
    assert semantics["present_all_false"]["accepted"] is False
    assert semantics["present_all_false"]["present_all_false_semantics_deferred"] is True


def test_mixed_batch_deferred_but_separate_profiles_supported(response):
    semantics = response["mixed_batch_semantics"]
    assert semantics["mixed_covalent_noncovalent_same_batch_supported"] is False
    assert semantics["mixed_noncovalent_zero_target_semantics_deferred"] is True
    assert semantics["reason"] == "no_formal_per_sample_condition_presence_mask"
    assert semantics["pure_covalent_batch_supported"] is True
    assert semantics["separate_legacy_batch_supported"] is True


@pytest.mark.parametrize(
    "field",
    [
        "indicator_normalized", "indicator_noised", "indicator_centered",
        "indicator_rotated", "indicator_decoded", "indicator_added_to_xh_pocket",
        "indicator_contributes_to_reconstruction_loss",
    ],
)
def test_indicator_is_not_a_diffusion_variable(response, field):
    assert response["normalization_and_noise_policy"][field] is False


def test_synthetic_zero_initialization_parity():
    hidden = torch.arange(20, dtype=torch.float32).reshape(5, 4)
    indicator = torch.tensor([False, False, True, False, False])
    zero_embedding = torch.zeros(4)
    assert torch.equal(_inject(hidden, indicator, zero_embedding), hidden)


def test_synthetic_nonzero_target_row_only_injection():
    hidden = torch.zeros((5, 4))
    indicator = torch.tensor([False, False, True, False, False])
    embedding = torch.tensor([1.0, -2.0, 3.0, -4.0])
    injected = _inject(hidden, indicator, embedding)
    assert torch.equal(injected[2], embedding)
    assert torch.equal(injected[~indicator], hidden[~indicator])


def test_synthetic_gradient_path_jacobian_exists_without_backward():
    indicator = torch.tensor([False, True, False])
    joint_nf = 4
    jacobian = indicator.to(torch.float32)[:, None, None] * torch.eye(joint_nf)[None]
    assert torch.equal(jacobian[1], torch.eye(joint_nf))
    assert torch.count_nonzero(jacobian[~indicator]) == 0


def test_translation_rotation_do_not_change_condition_embedding():
    hidden = torch.zeros((3, 2))
    indicator = torch.tensor([False, True, False])
    embedding = torch.tensor([2.0, -1.0])
    coordinates = torch.tensor([[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]])
    translation = torch.tensor([7.0, -3.0, 2.0])
    rotation = torch.tensor([[0.0, -1.0, 0], [1.0, 0, 0], [0, 0, 1.0]])
    base = _inject(hidden, indicator, embedding)
    translated = _inject(hidden, indicator, embedding)
    rotated = _inject(hidden, indicator, embedding)
    assert torch.equal(base, translated) and torch.equal(base, rotated)
    assert not torch.equal(coordinates, coordinates + translation)
    assert not torch.equal(coordinates, coordinates @ rotation.T)


def test_node_permutation_alignment_oracle():
    hidden = torch.arange(15, dtype=torch.float32).reshape(5, 3)
    indicator = torch.tensor([False, True, False, False, False])
    embedding = torch.tensor([0.5, -1.0, 2.0])
    permutation = torch.tensor([3, 1, 4, 0, 2])
    direct = _inject(hidden, indicator, embedding)[permutation]
    permuted = _inject(hidden[permutation], indicator[permutation], embedding)
    assert torch.equal(direct, permuted)


def test_equivariance_contract_has_no_direct_coordinate_edge_or_mask_change(response):
    contract = response["equivariance_contract"]
    assert contract["coordinate_injection"] is False
    assert contract["distance_change"] is False
    assert contract["edge_construction_change"] is False
    assert contract["coordinate_update_mask_change"] is False
    assert contract["translation_equivariance_preserved"] is True
    assert contract["rotation_equivariance_preserved"] is True
    assert contract["reflection_policy"] == "unchanged_from_original_model"
    assert contract["node_permutation_equivariance_preserved"] is True


@pytest.mark.parametrize(
    "field",
    [
        "conditional_training_path_contract", "conditional_eval_path_contract",
        "conditional_sampling_path_contract", "joint_training_path_contract",
        "inpainting_path_contract", "simple_conditional_path_contract",
    ],
)
def test_all_required_path_contracts_are_covered(response, field):
    assert response[field]["covered"] is True


def test_conditional_eval_and_sampling_thread_same_static_tensor(response):
    assert response["conditional_eval_path_contract"][
        "same_static_indicator_for_both_predictions"
    ] is True
    assert response["conditional_sampling_path_contract"][
        "same_static_indicator_reused_every_denoising_timestep"
    ] is True
    assert response["inpainting_path_contract"][
        "same_static_indicator_reused_during_resampling"
    ] is True


def test_simple_conditional_overrides_are_explicit_and_fail_closed(response):
    contract = response["simple_conditional_path_contract"]
    assert "explicitly_forward" in contract["forward_override"]
    assert "explicitly_forward" in contract["sample_given_pocket_override"]
    assert contract["inpaint"].startswith("inherits_ConditionalDDPM")
    assert "fail_closed" in contract["generate_ligands_exact_type_branch"]
    assert "silently_dropped" in contract["generate_ligands_exact_type_branch"]


def test_future_signature_matrix_is_complete_and_same_name(response):
    matrix = response["implementation_scope"]["future_signature_change_matrix"]
    identities = {(item["class"], item["method"]) for item in matrix}
    required = {
        ("EGNNDynamics", "forward"),
        ("ConditionalDDPM", "forward"),
        ("ConditionalDDPM", "sample_p_zs_given_zt"),
        ("ConditionalDDPM", "sample_p_xh_given_z0"),
        ("ConditionalDDPM", "sample_given_pocket"),
        ("ConditionalDDPM", "diversify"),
        ("ConditionalDDPM", "inpaint"),
        ("SimpleConditionalDDPM", "forward"),
        ("SimpleConditionalDDPM", "sample_given_pocket"),
        ("EnVariationalDiffusion", "forward"),
        ("EnVariationalDiffusion", "sample_p_zs_given_zt"),
        ("EnVariationalDiffusion", "sample_p_xh_given_z0"),
        ("EnVariationalDiffusion", "inpaint"),
    }
    assert required <= identities
    relevant = [item for item in matrix if item["method"] not in {"__init__", "sample"}]
    assert all(
        design._FIELD in item["future_change"]
        for item in relevant
    )


def test_no_global_mutable_state_or_side_channel(response):
    scope = response["implementation_scope"]
    assert scope["global_mutable_state_used"] is False
    assert set(scope["forbidden_threading_mechanisms"]) == {
        "global_variable", "module_mutable_current_mask_state",
        "hook_side_channel", "thread_local_state", "singleton",
        "kwargs_only_indicator_transport",
    }


def test_constructor_dispatch_audit_covers_all_models(response):
    records = response["implementation_scope"]["constructor_site_records"]
    assert {record["constructed_class"] for record in records} == {
        "EGNNDynamics", "EnVariationalDiffusion", "ConditionalDDPM",
        "SimpleConditionalDDPM",
    }
    assert all(record["covered"] is True for record in records)


def test_canonical_five_masks_include_scaffold_only_and_no_sixth(response):
    assert response["canonical_mask_semantic_names"] == [
        "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
        "scaffold_only", "scaffold_plus_linker_plus_warhead",
    ]
    assert len(response["canonical_mask_semantic_names"]) == 5
    assert "scaffold_only" in response["canonical_mask_semantic_names"]


def test_no_forward_loss_or_parameter_implementation_in_design_source(response):
    source_path = Path(design.__file__)
    tree = ast.parse(source_path.read_text())
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "forward" not in calls
    assert "backward" not in calls
    assert "step" not in calls
    assert "load_state_dict" not in calls
    assert "register_parameter" not in calls
    scope = response["implementation_scope"]
    assert scope["model_consumption_implemented"] is False
    assert scope["new_model_parameter_created"] is False
    assert scope["training_or_parameter_update"] is False


def test_readiness_is_derived_from_complete_evidence(response):
    expected = (
        not response["unresolved_blockers"]
        and all(r["covered"] for r in response["audited_dynamics_call_site_records"])
        and all(r["covered"] for r in response["audited_checkpoint_load_site_records"])
        and all(response[field]["covered"] for field in (
            "conditional_training_path_contract", "conditional_eval_path_contract",
            "conditional_sampling_path_contract", "joint_training_path_contract",
            "inpainting_path_contract", "simple_conditional_path_contract",
        ))
    )
    assert response["ready_for_model_consumption_implementation"] is expected is True
    assert response["recommended_next_step"] == (
        "implement_covapie_target_residue_atom_condition_model_consumption_v1"
    )
    assert response["feature_semantics_audit_required_before_training"] is True


@pytest.mark.parametrize(
    "parameter,bad_value",
    [
        ("source_runtime_bridge_gate_bundle", bytearray(b"x")),
        ("source_runtime_bridge_gate_bundle", "x"),
        ("repo_root", str(ROOT)),
        ("repo_root", None),
    ],
)
def test_public_api_wrong_types_fail_canonically(source_bundle, parameter, bad_value):
    arguments = {
        "source_runtime_bridge_gate_bundle": source_bundle,
        "repo_root": ROOT,
    }
    arguments[parameter] = bad_value
    _error(lambda: design.design_covapie_target_residue_atom_condition_model_consumption_v1(
        **arguments
    ))


def test_gate_bundle_byte_drift_fails_closed(source_bundle):
    drift = source_bundle[:-1] + bytes([source_bundle[-1] ^ 1])
    _error(lambda: design.design_covapie_target_residue_atom_condition_model_consumption_v1(
        source_runtime_bridge_gate_bundle=drift,
        repo_root=ROOT,
    ))


def test_model_source_drift_fails_closed(source_bundle, monkeypatch):
    original = design._read_regular

    def drift(path, **kwargs):
        payload = original(path, **kwargs)
        if path == ROOT / "equivariant_diffusion/dynamics.py":
            return payload + b"\n"
        return payload

    monkeypatch.setattr(design, "_read_regular", drift)
    _error(lambda: design.design_covapie_target_residue_atom_condition_model_consumption_v1(
        source_runtime_bridge_gate_bundle=source_bundle,
        repo_root=ROOT,
    ))


def test_checkpoint_drift_fails_closed(source_bundle, monkeypatch):
    original = design._read_regular

    def drift(path, **kwargs):
        payload = original(path, **kwargs)
        if path == ROOT / design._CHECKPOINT_PATH:
            return bytes([payload[0] ^ 1]) + payload[1:]
        return payload

    monkeypatch.setattr(design, "_read_regular", drift)
    _error(lambda: design.design_covapie_target_residue_atom_condition_model_consumption_v1(
        source_runtime_bridge_gate_bundle=source_bundle,
        repo_root=ROOT,
    ))


def test_resigned_response_tampering_changes_digest(response):
    tampered = deepcopy(response)
    tampered["ready_for_model_consumption_implementation"] = False
    assert design._response_digest(tampered) != response[
        "model_consumption_design_response_sha256"
    ]
