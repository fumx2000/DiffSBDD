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


def _patch_lifecycle_git(
    monkeypatch,
    *,
    tracked_paths: set[str],
    ordinary_untracked_paths: set[str],
) -> None:
    def fake_git(_repo_root, *args):
        if args == ("ls-files",):
            return "\n".join(sorted(tracked_paths))
        if args == ("ls-files", "--others", "--exclude-standard"):
            return "\n".join(sorted(ordinary_untracked_paths))
        raise AssertionError(args)

    monkeypatch.setattr(design, "_git", fake_git)


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


def test_design_lifecycle_accepts_current_published_design_profile():
    evidence = design._design_path_lifecycle_evidence(ROOT)
    profile = evidence["design_lifecycle_profile"]
    assert profile in {
        "design_successor_worktree",
        "published_design_with_known_future_task",
    }
    assert evidence["tracked_design_paths"] == sorted(design._DESIGN_PATHS)
    assert evidence["untracked_design_paths"] == []
    assert evidence["design_paths_all_tracked"] is True
    assert evidence["design_paths_all_untracked"] is False
    assert evidence["unknown_ordinary_untracked_count"] == 0
    assert evidence["known_future_task_untracked_paths_supported"] is True
    assert evidence["unknown_untracked_paths_rejected"] is True
    assert evidence["lifecycle_valid"] is True
    if profile == "design_successor_worktree":
        assert evidence["ordinary_untracked_count"] == 0
        assert evidence["known_future_task_untracked_count"] == 0
        assert evidence["ordinary_untracked_paths"] == []
        assert evidence["known_future_task_untracked_paths"] == []
    else:
        assert evidence["ordinary_untracked_count"] > 0
        assert evidence["ordinary_untracked_count"] == evidence[
            "known_future_task_untracked_count"
        ]
        assert evidence["ordinary_untracked_paths"] == evidence[
            "known_future_task_untracked_paths"
        ]
        assert set(evidence["ordinary_untracked_paths"]).issubset(
            design._KNOWN_FUTURE_TASK_NEW_PATHS
        )
    assert all(
        not isinstance(item, Path)
        for value in evidence.values()
        for item in (value if isinstance(value, list) else [value])
    )


def test_design_lifecycle_accepts_exact_precommit_untracked_profile(monkeypatch):
    design_paths = set(design._DESIGN_PATHS)
    tracked_paths = set(design._git(ROOT, "ls-files").splitlines()) - design_paths
    _patch_lifecycle_git(
        monkeypatch,
        tracked_paths=tracked_paths,
        ordinary_untracked_paths=design_paths,
    )
    evidence = design._design_path_lifecycle_evidence(ROOT)
    assert evidence["design_lifecycle_profile"] == "initial_design_precommit"
    assert evidence["tracked_design_paths"] == []
    assert evidence["untracked_design_paths"] == sorted(design_paths)
    assert evidence["design_paths_all_tracked"] is False
    assert evidence["design_paths_all_untracked"] is True
    assert evidence["ordinary_untracked_count"] == 4
    assert evidence["unknown_ordinary_untracked_count"] == 0
    assert evidence["lifecycle_valid"] is True


def test_design_lifecycle_rejects_mixed_tracked_and_untracked_design_paths(
    monkeypatch,
):
    design_paths = set(design._DESIGN_PATHS)
    tracked_paths = set(design._git(ROOT, "ls-files").splitlines()) - design_paths
    tracked_design_paths = set(design._DESIGN_PATHS[:3])
    untracked_design_paths = {design._DESIGN_PATHS[3]}
    _patch_lifecycle_git(
        monkeypatch,
        tracked_paths=tracked_paths | tracked_design_paths,
        ordinary_untracked_paths=untracked_design_paths,
    )
    _assert_canonical_error(lambda: design._design_path_lifecycle_evidence(ROOT))


def test_design_lifecycle_rejects_unrelated_ordinary_untracked_path(monkeypatch):
    tracked_paths = set(design._git(ROOT, "ls-files").splitlines())
    _patch_lifecycle_git(
        monkeypatch,
        tracked_paths=tracked_paths,
        ordinary_untracked_paths={"scratch.txt"},
    )
    _assert_canonical_error(lambda: design._design_path_lifecycle_evidence(ROOT))


def test_design_lifecycle_accepts_known_r1_future_test(tmp_path, monkeypatch):
    for relative_path in design._DESIGN_PATHS:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("design\n")
    future_path = design._KNOWN_FUTURE_TASK_NEW_PATHS[0]
    path = tmp_path / future_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("future test\n")
    _patch_lifecycle_git(
        monkeypatch,
        tracked_paths=set(design._DESIGN_PATHS),
        ordinary_untracked_paths={future_path},
    )
    evidence = design._design_path_lifecycle_evidence(tmp_path)
    assert evidence["design_lifecycle_profile"] == (
        "published_design_with_known_future_task"
    )
    assert evidence["known_future_task_untracked_paths"] == [future_path]
    assert evidence["known_future_task_untracked_paths_supported"] is True
    assert evidence["unknown_untracked_paths_rejected"] is True


def test_design_lifecycle_rejects_nonregular_known_future_path(
    tmp_path, monkeypatch
):
    for relative_path in design._DESIGN_PATHS:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("design\n")
    future_path = design._KNOWN_FUTURE_TASK_NEW_PATHS[0]
    path = tmp_path / future_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(tmp_path / design._DESIGN_PATHS[0])
    _patch_lifecycle_git(
        monkeypatch,
        tracked_paths=set(design._DESIGN_PATHS),
        ordinary_untracked_paths={future_path},
    )
    _assert_canonical_error(
        lambda: design._design_path_lifecycle_evidence(tmp_path)
    )


def test_design_lifecycle_rejects_missing_design_path(monkeypatch):
    tracked_paths = set(design._git(ROOT, "ls-files").splitlines())
    tracked_paths.remove(design._DESIGN_PATHS[-1])
    _patch_lifecycle_git(
        monkeypatch,
        tracked_paths=tracked_paths,
        ordinary_untracked_paths=set(),
    )
    _assert_canonical_error(lambda: design._design_path_lifecycle_evidence(ROOT))


def test_design_lifecycle_rejects_design_path_in_both_git_sets(monkeypatch):
    tracked_paths = set(design._git(ROOT, "ls-files").splitlines())
    _patch_lifecycle_git(
        monkeypatch,
        tracked_paths=tracked_paths,
        ordinary_untracked_paths={design._DESIGN_PATHS[0]},
    )
    _assert_canonical_error(lambda: design._design_path_lifecycle_evidence(ROOT))


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


def test_runtime_design_baseline_commit_metadata_and_ancestry_are_bound():
    evidence = design._runtime_design_baseline_source_evidence(ROOT)
    assert evidence["runtime_design_baseline_commit"] == (
        design._RUNTIME_DESIGN_BASELINE_COMMIT
    )
    assert evidence["runtime_design_baseline_commit_single_parent"] is True
    assert evidence["runtime_design_baseline_commit_is_head_ancestor"] is True
    assert evidence[
        "runtime_design_baseline_commit_is_origin_main_ancestor"
    ] is True
    assert evidence["snapshot_network_access"] is False
    assert evidence["snapshot_working_tree_independent"] is True
    assert evidence["snapshot_index_independent"] is True
    assert evidence["snapshot_regular_blob_required"] is True
    assert evidence["snapshot_nonempty_required"] is True
    assert evidence["snapshot_size_bounded"] is True
    assert evidence["snapshot_sha256_bound"] is True


def test_git_snapshot_reader_is_sha_bound_and_fails_closed():
    payload = design._git_snapshot_file_bytes(
        ROOT,
        commit=design._RUNTIME_DESIGN_BASELINE_COMMIT,
        relative_path="scripts/covalent_inpaint_demo.py",
        expected_sha256=design._CALLER_SHA256S[
            "scripts/covalent_inpaint_demo.py"
        ],
    )
    assert hashlib.sha256(payload).hexdigest() == design._CALLER_SHA256S[
        "scripts/covalent_inpaint_demo.py"
    ]
    _assert_canonical_error(
        lambda: design._git_snapshot_file_bytes(
            ROOT,
            commit=design._RUNTIME_DESIGN_BASELINE_COMMIT,
            relative_path="scripts/covalent_inpaint_demo.py",
            expected_sha256="0" * 64,
        )
    )
    _assert_canonical_error(
        lambda: design._git_snapshot_file_bytes(
            ROOT,
            commit=design._RUNTIME_DESIGN_BASELINE_COMMIT,
            relative_path="../outside",
            expected_sha256="0" * 64,
        )
    )


@pytest.mark.parametrize("relative_path,expected", list(design._CALLER_SHA256S.items()))
def test_all_six_caller_sha256s_are_frozen(relative_path, expected):
    payload = design._git_snapshot_file_bytes(
        ROOT,
        commit=design._RUNTIME_DESIGN_BASELINE_COMMIT,
        relative_path=relative_path,
        expected_sha256=expected,
    )
    assert hashlib.sha256(payload).hexdigest() == expected


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


def test_baseline_audits_do_not_use_live_mutable_runtime_files(
    bundle_bytes, response, monkeypatch
):
    mutable_baseline_paths = {
        *design._CALLER_SHA256S,
        "lightning_modules.py",
        "src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py",
        "src/covalent_ext/masking.py",
        "src/covalent_ext/dataset.py",
        "scripts/check_covalent_masking.py",
        "src/covalent_ext/b3_scaffold_only_mask_implementation.py",
        "scripts/check_b3_scaffold_only_mask_implementation_v0.py",
        "tests/test_b3_scaffold_only_mask_implementation_v0.py",
        "tests/test_real_covalent_feature_mapping_loader_gate_v0.py",
    }
    original = design._regular_file_bytes

    def guarded(repo_root, relative_path, **kwargs):
        if relative_path in mutable_baseline_paths:
            raise AssertionError(f"live read forbidden: {relative_path}")
        return original(repo_root, relative_path, **kwargs)

    monkeypatch.setattr(design, "_regular_file_bytes", guarded)
    actual = design.design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1(
        source_model_consumption_gate_bundle=bundle_bytes,
        repo_root=ROOT,
    )
    assert actual == response


def test_virtual_live_demo_migration_does_not_change_baseline_response(
    bundle_bytes, response, monkeypatch
):
    demo_path = ROOT / "scripts/covalent_inpaint_demo.py"
    original = Path.read_bytes

    def virtual_live_bytes(path):
        if path == demo_path:
            return b"from covalent_ext.masking import build_long_form_mask\n"
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", virtual_live_bytes)
    actual = design.design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1(
        source_model_consumption_gate_bundle=bundle_bytes,
        repo_root=ROOT,
    )
    assert actual == response


def test_known_r1_untracked_profile_does_not_change_baseline_response(
    bundle_bytes, response, monkeypatch
):
    evidence = dict(design._design_path_lifecycle_evidence(ROOT))
    future_path = design._KNOWN_FUTURE_TASK_NEW_PATHS[0]
    evidence.update(
        {
            "design_lifecycle_profile": (
                "published_design_with_known_future_task"
            ),
            "ordinary_untracked_paths": [future_path],
            "ordinary_untracked_count": 1,
            "known_future_task_untracked_paths": [future_path],
            "known_future_task_untracked_count": 1,
        }
    )
    monkeypatch.setattr(
        design,
        "_design_path_lifecycle_evidence",
        lambda _root: evidence,
    )
    actual = design.design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1(
        source_model_consumption_gate_bundle=bundle_bytes,
        repo_root=ROOT,
    )
    assert actual == response


def test_inventory_uses_baseline_tree_not_live_text(monkeypatch):
    def reject_live_text(_path, *args, **kwargs):
        raise AssertionError("inventory attempted a live text read")

    monkeypatch.setattr(Path, "read_text", reject_live_text)
    inventory = design._legacy_mask_reference_inventory(ROOT)
    assert inventory["evidence_mode"] == "frozen_runtime_baseline_snapshot"
    assert inventory["runtime_design_baseline_commit"] == (
        design._RUNTIME_DESIGN_BASELINE_COMMIT
    )
    assert inventory["inventory_claims_live_runtime_state"] is False
    assert inventory["baseline_reference_count"] == 45
    assert inventory["baseline_active_legacy_reference_count"] == 14


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
    assert contract["baseline_covalent_demo_sha256"] == (
        design._CALLER_SHA256S["scripts/covalent_inpaint_demo.py"]
    )
    assert contract["baseline_source_commit"] == (
        design._RUNTIME_DESIGN_BASELINE_COMMIT
    )
    assert contract["contract_claims_live_demo_sha256"] is False
    assert contract["forward_path"][-1] == "model.prepare_pocket"
    assert contract["prepare_pocket_selector_forwarding_site_count"] == 1
    assert contract["manual_indicator_creation_allowed"] is False


def test_existing_model_entry_points_already_consume_selector():
    evidence = design._model_and_mask_source_audit(ROOT)
    assert evidence["generate_ligands_selector_parameter_present"] is True
    assert evidence["generate_ligands_forwards_selector_to_prepare_pocket"] is True
    assert evidence["prepare_pocket_selector_parameter_present"] is True
    assert evidence["prepare_pocket_builds_indicator"] is True


def test_baseline_runtime_is_not_retired_but_retirement_target_is_selected(response):
    contract = response["selected_mask_semantic_normalization_contract"]
    assert contract["canonical_five_level_target_selected"] is True
    assert contract["canonical_five_level_contract_complete"] is True
    assert contract["legacy_four_level_retirement_selected"] is True
    assert contract["legacy_four_level_retirement_implemented"] is False
    assert contract["baseline_legacy_four_level_runtime_present"] is True
    assert contract["baseline_legacy_four_level_cli_input_present"] is True
    assert contract["baseline_legacy_four_level_schema_present"] is True
    assert contract["design_checker_claims_live_runtime_state"] is False


def test_baseline_and_target_active_residual_counts_are_distinct(response):
    contract = response["selected_mask_semantic_normalization_contract"]
    assert contract["baseline_reference_count"] == 45
    assert contract["baseline_active_legacy_reference_count"] == 14
    assert contract["baseline_active_legacy_reference_path_count"] == 5
    assert contract["target_active_legacy_reference_count"] == 0
    assert contract["target_active_legacy_reference_path_count"] == 0
    assert contract["live_active_legacy_reference_count_claimed"] is False


def test_baseline_provider_and_consumers_are_proven_from_ast(response):
    evidence = response["selected_mask_semantic_normalization_contract"][
        "retirement_dependency_order_evidence"
    ]
    assert evidence["legacy_provider_path"] == "src/covalent_ext/masking.py"
    assert evidence["provider_symbol"] == design._LEGACY_MASK_SYMBOLS[0]
    assert evidence["provider_symbols_present"] is True
    assert evidence["active_consumer_paths"] == [
        "scripts/check_covalent_masking.py",
        "scripts/covalent_inpaint_demo.py",
        "src/covalent_ext/dataset.py",
    ]
    assert evidence["consumer_import_count"] == 2
    assert evidence["consumer_call_count"] == 2
    assert evidence["legacy_provider_has_active_consumers"] is True
    assert evidence["provider_removal_before_consumer_migration_safe"] is False
    assert evidence["evidence_mode"] == "frozen_runtime_baseline_snapshot"
    assert evidence["runtime_design_baseline_commit"] == (
        design._RUNTIME_DESIGN_BASELINE_COMMIT
    )


def test_current_demo_legacy_import_call_flag_and_choices_are_ast_evidence(response):
    evidence = response["selected_mask_semantic_normalization_contract"][
        "retirement_dependency_order_evidence"
    ]
    assert evidence["legacy_demo_imports_four_level_builder"] is True
    assert evidence["legacy_demo_calls_four_level_builder"] is True
    assert evidence["legacy_demo_mask_level_flag_present"] is True
    assert evidence["legacy_demo_exact_A_B_B2_C_choices_present"] is True


def test_other_core_consumers_are_ast_evidence(response):
    evidence = response["selected_mask_semantic_normalization_contract"][
        "retirement_dependency_order_evidence"
    ]
    assert evidence["dataset_imports_four_level_builder"] is True
    assert evidence["dataset_imports_MaskType"] is True
    assert evidence["dataset_build_all_masks_uses_A_B_B2_C"] is True
    assert evidence["checker_imports_MASK_BUILDERS"] is True
    assert evidence["checker_iterates_A_B_B2_C"] is True


def test_dependency_order_has_no_intermediate_missing_import_state(response):
    evidence = response["selected_mask_semantic_normalization_contract"][
        "retirement_dependency_order_evidence"
    ]
    assert evidence["consumer_migration_step"] == "R1"
    assert evidence["provider_removal_step"] == "R2"
    assert evidence["consumer_migration_precedes_provider_removal"] is True
    assert evidence["provider_removal_precedes_consumer_migration"] is False
    assert evidence["R1_migrates_demo_and_keeps_provider"] is True
    assert evidence[
        "R2_removes_provider_and_migrates_remaining_consumers"
    ] is True
    assert evidence["no_intermediate_missing_import_state"] is True


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
    assert inventory["baseline_reference_count"] == len(inventory["records"])
    assert inventory["baseline_reference_count"] == 45
    assert inventory["classification_counts"] == {
        "active_runtime": 14,
        "test_only": 7,
        "documentation_only": 8,
        "historical_freeze_only": 8,
        "design_evidence_only": 8,
    }
    assert inventory["baseline_active_legacy_reference_count"] == 14
    assert inventory["baseline_active_legacy_reference_path_count"] == 5
    assert inventory["baseline_unresolved_active_reference_count"] == 0
    assert inventory["baseline_active_legacy_reference_paths"] == [
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


def test_post_commit_inventory_retains_exact_45_records():
    inventory = design._legacy_mask_reference_inventory(ROOT)
    assert inventory["baseline_reference_count"] == 45
    assert inventory["classification_counts"] == {
        "active_runtime": 14,
        "test_only": 7,
        "documentation_only": 8,
        "historical_freeze_only": 8,
        "design_evidence_only": 8,
    }
    assert inventory["baseline_active_legacy_reference_count"] == 14
    assert inventory["baseline_active_legacy_reference_path_count"] == 5
    assert inventory["baseline_active_legacy_reference_paths"] == [
        "scripts/check_covalent_masking.py",
        "scripts/covalent_inpaint_demo.py",
        "src/covalent_ext/dataset.py",
        "src/covalent_ext/masking.py",
        "src/covalent_ext/schema.py",
    ]
    assert inventory["baseline_unresolved_active_reference_count"] == 0


def test_precommit_inventory_retains_exact_45_records(monkeypatch):
    design_paths = set(design._DESIGN_PATHS)
    original_git = design._git
    tracked_paths = set(original_git(ROOT, "ls-files").splitlines()) - design_paths

    def fake_git(repo_root, *args):
        if args == ("ls-files",):
            return "\n".join(sorted(tracked_paths))
        if args == ("ls-files", "--others", "--exclude-standard"):
            return "\n".join(sorted(design_paths))
        return original_git(repo_root, *args)

    monkeypatch.setattr(design, "_git", fake_git)
    inventory = design._legacy_mask_reference_inventory(ROOT)
    assert inventory["baseline_reference_count"] == 45
    assert inventory["classification_counts"] == {
        "active_runtime": 14,
        "test_only": 7,
        "documentation_only": 8,
        "historical_freeze_only": 8,
        "design_evidence_only": 8,
    }
    assert inventory["baseline_active_legacy_reference_count"] == 14
    assert inventory["baseline_active_legacy_reference_path_count"] == 5
    assert inventory["baseline_unresolved_active_reference_count"] == 0


def test_snapshot_stability_fix_preserves_exact43_and_recomputes_digest(response):
    assert len(response) == 43
    assert tuple(response) == design.REPOSITORY_CLI_FORWARDING_DESIGN_RESPONSE_FIELDS
    assert response["repository_cli_forwarding_design_response_sha256"] == (
        "c20cd01a1c6c5e4e6e7bc36883d2c131b56f622451100eee68be181971e6a875"
    )


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
        == ("R1" if item["path"] == "scripts/covalent_inpaint_demo.py" else "R2")
        for item in active
    )


def test_test_only_references_are_assigned_by_validation_object(response):
    inventory = response["selected_mask_semantic_normalization_contract"][
        "legacy_reference_inventory"
    ]
    test_records = [item for item in inventory["records"] if item["test_only"]]
    assert len(test_records) == 7
    negative = [
        item
        for item in test_records
        if item["required_future_action"]
        == "retain_negative_legacy_token_evidence"
    ]
    positive = [item for item in test_records if item not in negative]
    assert len(negative) == 1
    assert negative[0]["retirement_increment"] is None
    assert negative[0]["active_runtime"] is False
    assert negative[0]["positive_legacy_behavior_required"] is False
    assert all(item["retirement_increment"] == "R2" for item in positive)
    assert all(item["positive_legacy_behavior_required"] is True for item in positive)
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
    inventory["baseline_unresolved_active_reference_count"] = 1
    dependency = design._retirement_dependency_order_evidence(ROOT)
    assert design._ready_for_covalent_demo_canonical_mask_migration_R1(
        inventory,
        dependency,
        canonical_five_level_contract_complete=True,
    ) is False


def test_future_order_is_exactly_r1_r2_r3_then_c1_through_c4(response):
    scope = response["selected_mask_semantic_normalization_contract"][
        "future_retirement_implementation_scope"
    ]
    assert scope["incremental_commits_required"] is True
    assert scope["single_commit_for_all_increments_allowed"] is False
    assert scope["cli_forwarding_may_begin_before_R3"] is False
    assert scope["C1_before_committed_R3_allowed"] is False
    assert scope["consumer_migration_precedes_provider_removal"] is True
    assert scope["provider_removal_precedes_consumer_migration"] is False
    assert [item["step"] for item in scope["ordered_steps"]] == [
        "R1", "R2", "R3", "C1", "C2", "C3", "C4"
    ]


def test_r1_scope_migrates_only_demo_mask_surface(response):
    steps = response["selected_mask_semantic_normalization_contract"][
        "future_retirement_implementation_scope"
    ]["ordered_steps"]
    r1 = steps[0]
    assert r1["task_name"] == (
        "implement_covapie_covalent_demo_canonical_five_level_mask_migration_r1_v1"
    )
    assert r1["paths"] == [
        "scripts/covalent_inpaint_demo.py",
        "tests/test_covalent_inpaint_demo_mask_semantic_v1.py",
    ]
    assert set(r1["forbidden_paths"]) == {
        "src/covalent_ext/masking.py",
        "src/covalent_ext/schema.py",
        "src/covalent_ext/dataset.py",
        "scripts/check_covalent_masking.py",
    }
    assert r1["completion_contract"][
        "legacy_four_level_demo_consumer_removed"
    ] is True
    assert r1["completion_contract"][
        "legacy_four_level_core_provider_still_present"
    ] is True
    assert r1["completion_contract"]["legacy_four_level_core_api_retired"] is False
    assert r1["completion_contract"]["legacy_four_level_full_runtime_retired"] is False
    assert r1["completion_contract"]["R2_still_required"] is True
    assert r1["completion_contract"]["R3_gate_still_required"] is True
    assert r1["mask_surface_contract"]["target_residue_cli_arguments_added"] is False
    assert r1["mask_surface_contract"]["checkpoint_loader_modified"] is False
    assert r1["mask_surface_contract"]["model_forward_executed"] is False


def test_r2_scope_removes_core_provider_and_migrates_remaining_consumers(response):
    steps = response["selected_mask_semantic_normalization_contract"][
        "future_retirement_implementation_scope"
    ]["ordered_steps"]
    r2 = steps[1]
    assert r2["task_name"] == (
        "implement_covapie_legacy_four_level_core_api_retirement_r2_v1"
    )
    assert set(r2["paths"]) == {
        "src/covalent_ext/masking.py",
        "src/covalent_ext/schema.py",
        "src/covalent_ext/dataset.py",
        "scripts/check_covalent_masking.py",
        "tests/test_covalent_masking.py",
        "tests/test_b3_scaffold_only_mask_implementation_v0.py",
    }
    assert r2["completion_contract"]["legacy_core_provider_removed"] is True
    assert r2["completion_contract"]["remaining_core_consumers_migrated"] is True
    assert r2["completion_contract"]["candidate_active_legacy_reference_count"] == 0
    assert r2["completion_contract"][
        "legacy_four_level_full_runtime_retirement_candidate"
    ] is True
    assert r2["completion_contract"]["legacy_four_level_full_runtime_retired"] is False
    assert r2["completion_contract"]["R3_independent_gate_required"] is True
    canonical = r2["canonical_core_migration_contract"]
    assert canonical["schema_accepts_legacy_short_tokens"] is False
    assert canonical["dataset_API_uses_canonical_long_semantic_names"] is True
    assert canonical["dataset_build_all_masks_exactly_five"] is True
    assert canonical["dataset_build_all_masks_semantics"] == list(
        design.CANONICAL_MASK_SEMANTIC_NAMES
    )
    assert canonical["checker_validates_canonical_five_level_contract"] is True
    assert canonical["current_tests_require_positive_legacy_behavior"] is False


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


def test_r2_historical_b3_test_becomes_read_only_evidence(response):
    r2 = response["selected_mask_semantic_normalization_contract"][
        "future_retirement_implementation_scope"
    ]["ordered_steps"][1]
    boundary = r2["historical_B3_boundary"]
    assert boundary["source_modified"] is False
    assert hashlib.sha256((ROOT / boundary["source_path"]).read_bytes()).hexdigest() == boundary[
        "source_sha256"
    ]
    assert boundary["source_read_only"] is True
    assert boundary["source_active_runtime"] is False
    assert boundary["source_current_runtime_importable_required"] is False
    assert boundary["historical_checker_modified_or_run"] is False
    assert boundary["historical_checker_sha256"] == design._HISTORICAL_B3_CHECKER_SHA256
    assert boundary["test_imports_historical_module_after_R2"] is False
    assert boundary["test_runs_historical_checker_after_R2"] is False
    assert boundary["test_requires_positive_legacy_behavior_after_R2"] is False
    assert boundary["test_preserves_history_by_read_only_bytes_or_sha"] is True
    assert boundary["test_independently_checks_canonical_B2_and_B3"] is True
    assert boundary["current_test_sha256"] == design._CURRENT_B3_TEST_SHA256


def test_negative_legacy_token_evidence_is_retained_without_modification(response):
    masks = response["selected_mask_semantic_normalization_contract"]
    r2 = masks["future_retirement_implementation_scope"]["ordered_steps"][1]
    boundary = r2["negative_legacy_token_evidence_boundary"]
    assert hashlib.sha256((ROOT / boundary["path"]).read_bytes()).hexdigest() == boundary[
        "current_sha256"
    ]
    assert boundary["modified_in_R1"] is False
    assert boundary["modified_in_R2"] is False
    assert boundary["retirement_increment"] is None
    assert boundary["required_future_action"] == (
        "retain_negative_legacy_token_evidence"
    )
    assert boundary["active_runtime"] is False
    assert boundary["positive_legacy_behavior_required"] is False
    assert boundary["negative_legacy_token_rejection_evidence_retained"] is True
    assert masks[
        "test_real_covalent_feature_mapping_loader_gate_v0_modified_in_R1"
    ] is False
    assert masks[
        "test_real_covalent_feature_mapping_loader_gate_v0_modified_in_R2"
    ] is False


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


def test_baseline_callers_and_model_sources_are_snapshot_bound(response):
    for relative_path, expected in design._CALLER_SHA256S.items():
        payload = design._git_snapshot_file_bytes(
            ROOT,
            commit=design._RUNTIME_DESIGN_BASELINE_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected,
        )
        assert hashlib.sha256(payload).hexdigest() == expected
    for relative_path, expected in (
        ("lightning_modules.py", response["source_lightning_module_sha256"]),
        (
            "src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py",
            response["source_checkpoint_migration_sha256"],
        ),
    ):
        payload = design._git_snapshot_file_bytes(
            ROOT,
            commit=design._RUNTIME_DESIGN_BASELINE_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected,
        )
        assert hashlib.sha256(payload).hexdigest() == expected


def test_no_forward_training_or_parameter_update_was_executed(response):
    contract = response["selected_conditioned_checkpoint_load_strategy"]
    assert contract["model_forward_executed"] is False
    assert response["training_or_parameter_update"] is False
    assert response["repository_cli_selector_forwarding_implemented"] is False


def test_readiness_is_derived_from_complete_evidence(response):
    mask_contract = response["selected_mask_semantic_normalization_contract"]
    assert mask_contract["design_evidence_mode"] == (
        "frozen_runtime_baseline_snapshot"
    )
    assert mask_contract["design_baseline_snapshot_immutable"] is True
    assert mask_contract["design_checker_claims_live_runtime_state"] is False
    assert mask_contract[
        "implementation_phase_live_state_requires_phase_specific_gate"
    ] is True
    assert mask_contract[
        "recommended_next_step_is_design_baseline_recommendation"
    ] is True
    assert mask_contract["R1_candidate_will_not_invalidate_design_tests"] is True
    assert mask_contract["retirement_dependency_order_valid"] is True
    assert mask_contract[
        "ready_for_covalent_demo_canonical_mask_migration_R1"
    ] is True
    assert mask_contract["ready_for_legacy_core_api_retirement_R2"] is False
    assert mask_contract["legacy_four_level_retirement_implemented"] is False
    assert mask_contract["retirement_R3_gate_passed"] is False
    assert mask_contract["retirement_R3_gate_committed"] is False
    assert response["ready_for_repository_cli_forwarding_implementation"] is False
    assert response["recommended_next_step"] == (
        "implement_covapie_covalent_demo_canonical_five_level_mask_migration_r1_v1"
    )
    assert response["feature_semantics_audit_required_before_training"] is True
    assert response["selected_failure_contract"]["fail_closed"] is True
    assert len(response["selected_failure_contract"]["rejected_conditions"]) == 18
    assert response["selected_conditioned_mode_contract"][
        "target_enable_flag_exact_bool_required"
    ] is True


def test_r2_readiness_fails_closed_until_r1_is_committed(response):
    evidence = response["selected_mask_semantic_normalization_contract"][
        "retirement_dependency_order_evidence"
    ]
    assert design._ready_for_legacy_core_api_retirement_R2(
        evidence,
        R1_committed=False,
    ) is False
    assert design._ready_for_legacy_core_api_retirement_R2(
        evidence,
        R1_committed=True,
    ) is False
