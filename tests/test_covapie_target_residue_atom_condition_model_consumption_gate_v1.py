from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_target_residue_atom_condition_model_consumption_gate_v1 as gate,
)


ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_MODEL_CONSUMPTION_GATE_INVALID"
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


def _evaluate():
    return gate.evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1(
        source_runtime_bridge_gate_bundle=RUNTIME_BUNDLE.read_bytes(),
        repo_root=ROOT,
    )


@pytest.fixture(scope="session")
def response():
    return _evaluate()


def _canonical(value) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode()


def _assert_error(action) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        action()


def _walk(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk(item)
    else:
        yield value


def test_public_api_all_and_keyword_only():
    assert gate.__all__ == (
        "evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1",
    )
    signature = inspect.signature(
        gate.evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_import_is_silent():
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "from covalent_ext import "
            "covapie_target_residue_atom_condition_model_consumption_gate_v1",
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""


@pytest.mark.parametrize("bad", [None, bytearray(b"{}"), "{}", b"", b"{}\n"])
def test_invalid_bundle_input_uses_canonical_error(bad):
    _assert_error(
        lambda: gate.evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1(
            source_runtime_bridge_gate_bundle=bad,
            repo_root=ROOT,
        )
    )


def test_positional_arguments_rejected_by_python():
    with pytest.raises(TypeError):
        gate.evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1(
            RUNTIME_BUNDLE.read_bytes(), ROOT
        )


def test_exact43_fields_and_order(response):
    assert len(response) == 43
    assert tuple(response) == gate.MODEL_CONSUMPTION_GATE_RESPONSE_FIELDS


def test_response_digest_excludes_itself(response):
    projected = {
        key: value
        for key, value in response.items()
        if key != "model_consumption_gate_response_sha256"
    }
    assert response["model_consumption_gate_response_sha256"] == hashlib.sha256(
        _canonical(projected)
    ).hexdigest()


def test_response_has_no_paths_or_tensors(response):
    values = tuple(_walk(response))
    assert not any(isinstance(value, Path) for value in values)
    assert not any(isinstance(value, torch.Tensor) for value in values)


def test_public_api_is_deterministic_and_restores_rng():
    before = torch.random.get_rng_state().clone()
    first = _evaluate()
    middle = torch.random.get_rng_state().clone()
    second = _evaluate()
    after = torch.random.get_rng_state().clone()
    assert first == second
    assert torch.equal(before, middle)
    assert torch.equal(before, after)


def test_public_api_does_not_change_inputs_or_repository_state():
    payload = RUNTIME_BUNDLE.read_bytes()
    payload_snapshot = bytes(payload)
    before = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    checkpoint = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
    checkpoint_stat = checkpoint.stat()
    gate.evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1(
        source_runtime_bridge_gate_bundle=payload,
        repo_root=ROOT,
    )
    after = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert payload == payload_snapshot
    assert before == after
    assert checkpoint.stat() == checkpoint_stat


def test_runtime_bridge_transport_and_internal_sha(response):
    payload = RUNTIME_BUNDLE.read_bytes()
    assert len(payload) == 12811
    assert hashlib.sha256(payload).hexdigest() == (
        "835032d1b0a9d9af9abe0839e9be798f0d4f178bcd9d4af3323592c5e59aa597"
    )
    assert response["source_runtime_bridge_gate_bundle_sha256"] == (
        "035d45fb50a15e29b367a6af71d9ca28019b5d77c5d5ed82d253b78570e5750d"
    )


def test_runtime_bundle_is_canonical_without_trailing_newline():
    payload = RUNTIME_BUNDLE.read_bytes()
    assert not payload.endswith((b"\n", b"\r"))
    assert _canonical(json.loads(payload)) == payload


def test_current11_lineage_projection(response):
    assert response["current11_lineage_projection_sha256"] == (
        "c4918fd0ee226de4bdee5aded27e06b615ca56c8f5085c044ef035cf172d71e9"
    )


def test_implementation_commit_identity_and_ancestry(response):
    assert response["source_model_consumption_implementation_commit"] == (
        "2c504ff2eac0864c146129f4011d902fae5bef69"
    )
    assert response["source_model_consumption_implementation_parent"] == (
        "99425693056cd8800b9f93a19ea79a1e3e77c68e"
    )
    assert response["source_model_consumption_implementation_tree"] == (
        "01a72bd9c3e313c2833cd22edae351a56abaec84"
    )
    assert response["dynamics_threading_contract"][
        "all_eight_sites_thread_long_semantic_keyword"
    ] is True


def test_exact_implementation_scope_and_frozen_bytes(response):
    assert response["implementation_source_scope"] == list(gate._IMPLEMENTATION_FILES)
    for path, expected in gate._IMPLEMENTATION_FILES.items():
        committed = gate._git_snapshot_file_bytes(
            ROOT,
            commit=gate._IMPLEMENTATION_COMMIT,
            relative_path=path,
            expected_sha256=expected,
        )
        assert hashlib.sha256(committed).hexdigest() == expected


def test_predecessor_snapshot_does_not_bind_live_successor_demo():
    source = inspect.getsource(gate._source_evidence)
    assert "_git_snapshot_file_bytes(" in source
    assert "commit=_IMPLEMENTATION_COMMIT" in source
    assert "_read_regular(repo_root / relative_path)" not in source
    assert gate._GATE_EVIDENCE_MODE == "frozen_predecessor_commit_snapshot"
    assert gate._GATE_CLAIMS_LIVE_SUCCESSOR_REPOSITORY_CALLERS is False
    assert gate._SUCCESSOR_RUNTIME_STATE_REQUIRES_PHASE_SPECIFIC_GATE is True


def test_live_demo_read_failure_does_not_change_formal_response(monkeypatch):
    original = gate._read_regular
    demo = ROOT / "scripts/covalent_inpaint_demo.py"

    def reject_live_demo(path, **kwargs):
        if path == demo:
            raise AssertionError("formal predecessor gate read live successor demo")
        return original(path, **kwargs)

    monkeypatch.setattr(gate, "_read_regular", reject_live_demo)
    response = _evaluate()
    assert response == json.loads(FORMAL_BUNDLE.read_bytes())
    assert response["model_consumption_gate_response_sha256"] == (
        "0ef97cdafe946fefd240c95a94efc8b12be977c899db3b1df4a56a580b53d842"
    )


@pytest.mark.parametrize(
    "relative_path",
    ["/absolute", "../outside", "nested/../outside", "nul\x00path"],
)
def test_git_snapshot_reader_rejects_invalid_paths(relative_path):
    _assert_error(
        lambda: gate._git_snapshot_file_bytes(
            ROOT,
            commit=gate._IMPLEMENTATION_COMMIT,
            relative_path=relative_path,
            expected_sha256="0" * 64,
        )
    )


@pytest.mark.parametrize("relative_path", ["missing-snapshot-blob", "."])
def test_git_snapshot_reader_rejects_missing_and_non_blob(relative_path):
    _assert_error(
        lambda: gate._git_snapshot_file_bytes(
            ROOT,
            commit=gate._IMPLEMENTATION_COMMIT,
            relative_path=relative_path,
            expected_sha256="0" * 64,
        )
    )


def test_git_snapshot_reader_rejects_oversize_and_sha_drift():
    relative_path = "scripts/covalent_inpaint_demo.py"
    expected = gate._CALLER_SHA256S[relative_path]
    source = inspect.getsource(gate._git_snapshot_file_bytes)
    assert 'run("cat-file", "-t", object_spec)' in source
    assert 'run("cat-file", "-s", object_spec)' in source
    assert 'run("show", object_spec)' in source
    assert all(token not in source for token in ("fetch", "checkout", "worktree"))
    _assert_error(
        lambda: gate._git_snapshot_file_bytes(
            ROOT,
            commit=gate._IMPLEMENTATION_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected,
            maximum=2,
        )
    )
    _assert_error(
        lambda: gate._git_snapshot_file_bytes(
            ROOT,
            commit=gate._IMPLEMENTATION_COMMIT,
            relative_path=relative_path,
            expected_sha256="0" * 64,
        )
    )


def test_successor_head_is_legal_not_exact_implementation_head():
    source = inspect.getsource(gate._source_evidence)
    assert '_is_ancestor(repo_root, _IMPLEMENTATION_COMMIT, "HEAD")' in source
    assert '["rev-parse", "HEAD"]' not in source


def test_disabled_profile_contract(response):
    contract = response["disabled_profile_contract"]
    assert contract == {
        "target_residue_atom_conditioning": False,
        "new_parameter_key_absent": True,
        "state_key_count": 120,
        "checkpoint_dynamics_strict_load": True,
        "missing_keys": [],
        "unexpected_keys": [],
    }


def test_enabled_profile_exact_one_parameter(response):
    contract = response["enabled_profile_contract"]
    assert contract["target_residue_atom_conditioning"] is True
    assert contract["exactly_one_new_parameter"] is True
    assert contract["parameter_name"] == "target_residue_atom_condition_embedding"


def test_enabled_parameter_shape_zero_and_requires_grad(response):
    contract = response["enabled_profile_contract"]
    assert contract["parameter_shape"] == [32]
    assert contract["parameter_all_zeros"] is True
    assert contract["parameter_requires_grad"] is True


def test_enabled_existing_state_compatibility(response):
    contract = response["enabled_profile_contract"]
    assert contract["existing_keys_unchanged"] is True
    assert contract["existing_shapes_unchanged"] is True


def test_migration_exactly_one_key_and_strict(response):
    contract = response["base_to_conditioned_migration_contract"]
    assert contract["exactly_one_key_filled"] is True
    assert contract["filled_key"] == (
        "ddpm.dynamics.target_residue_atom_condition_embedding"
    )
    assert contract["final_strict_load"] is True
    assert contract["missing_keys"] == contract["unexpected_keys"] == []
    assert contract["blanket_strict_false"] is False


@pytest.mark.parametrize(
    "field",
    [
        "additional_missing_rejected",
        "unexpected_rejected",
        "shape_drift_rejected",
        "dtype_drift_rejected",
        "nonzero_new_parameter_rejected",
    ],
)
def test_migration_negative_paths(response, field):
    assert response["base_to_conditioned_migration_contract"][field] is True


def test_migration_preserves_base_mapping_tensors_and_checkpoint(response):
    contract = response["base_to_conditioned_migration_contract"]
    assert contract["base_mapping_unchanged"] is True
    assert contract["shared_tensors_unchanged"] is True
    assert contract["disk_checkpoint_unchanged"] is True


def test_current11_validator_accepts_original_2202_indicator(response):
    contract = response["current11_condition_validation_contract"]
    assert contract["accepted"] is True
    assert contract["returned_object_is_original_indicator"] is True
    assert contract["pocket_x_shape"] == [2202, 3]
    assert contract["pocket_one_hot_shape"] == [2202, 10]
    assert contract["indicator_true_count"] == 11


def test_current11_one_target_per_sample_and_inputs_unchanged(response):
    contract = response["current11_condition_validation_contract"]
    assert contract["one_true_per_sample"] is True
    assert contract["inputs_unchanged"] is True
    assert contract["complete_egnn_forward_executed"] is False


@pytest.mark.parametrize(
    "field",
    [
        "float_mask_rejected",
        "bool_mask_rejected",
        "int32_mask_rejected",
        "float_size_rejected",
        "bool_size_rejected",
        "int32_size_rejected",
    ],
)
def test_mask_and_size_dtype_negative_paths(response, field):
    assert response["top_level_condition_validation_contract"][field] is True


@pytest.mark.parametrize(
    "field",
    [
        "present_all_false_rejected",
        "zero_target_sample_rejected",
        "multiple_target_sample_rejected",
    ],
)
def test_cardinality_negative_paths(response, field):
    assert response["top_level_condition_validation_contract"][field] is True


def test_dual_source_requires_exact_bool_semantics(response):
    contract = response["top_level_condition_validation_contract"]
    assert contract["bool_int_dual_source_pseudo_equality_rejected"] is True
    assert contract["bool_float_dual_source_pseudo_equality_rejected"] is True
    assert contract["dual_source_exact_bool_semantics_required"] is True


def test_all_eight_dynamics_calls_and_injection_point(response):
    contract = response["dynamics_threading_contract"]
    assert contract["dynamics_call_site_count"] == 8
    assert contract["all_eight_sites_thread_long_semantic_keyword"] is True
    assert contract["selected_injection_point_exact"] is True


@pytest.mark.parametrize(
    "field",
    [
        "lightning_only_authorized_change",
        "dynamics_only_authorized_changes",
        "conditional_only_authorized_changes",
        "en_diffusion_only_authorized_changes",
    ],
)
def test_authorized_ast_boundaries(response, field):
    assert response["dynamics_threading_contract"][field] is True


@pytest.mark.parametrize(
    "field",
    [
        "loss_computation_ast_unchanged",
        "normalization_ast_unchanged",
        "noise_representation_ast_unchanged",
        "unconditional_joint_sample_ast_unchanged",
        "egnn_new_unchanged",
        "dataset_unchanged",
    ],
)
def test_protected_ast_and_sources_unchanged(response, field):
    assert response["dynamics_threading_contract"][field] is True


@pytest.mark.parametrize(
    "field",
    [
        "zero_initialization_parity",
        "nonzero_target_row_changed",
        "non_target_pocket_rows_unchanged",
        "ligand_rows_not_directly_injected",
        "coordinates_unchanged",
        "direct_expected_complete_hidden_match",
    ],
)
def test_injection_contract(response, field):
    assert response["injection_contract"][field] is True


def test_direct_expected_hidden_oracle_is_16_seed_stable(response):
    oracle = response["deterministic_oracle_contract"]
    assert oracle["fixed_seed_count"] == 16
    assert oracle["fixed_seeds"] == list(range(16))
    assert oracle["multi_seed_stable"] is True
    assert oracle["direct_expected_hidden_used"] is True
    assert oracle["cpu_rng_state_restored"] is True


def test_no_backward_optimizer_or_parameter_update(response):
    oracle = response["deterministic_oracle_contract"]
    assert oracle["backward_executed"] is False
    assert oracle["optimizer_step_executed"] is False
    assert response["training_or_parameter_update"] is False
    tree = ast.parse(Path(gate.__file__).read_text())
    attributes = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    assert "backward" not in attributes
    assert "step" not in attributes
    assert "save_checkpoint" not in attributes


def test_checkpoint_identity_and_state_widths(response):
    assert response["checkpoint_size"] == 17861341
    assert response["checkpoint_sha256"] == (
        "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
    )
    state = response["state_dict_compatibility_contract"]
    assert (state["atom_nf"], state["residue_nf"], state["joint_nf"]) == (
        10,
        10,
        32,
    )
    assert state["condition_time"] is True


def test_repository_cli_boundary(response):
    contract = response["repository_cli_contract"]
    assert contract["repository_cli_paths_unchanged"] is True
    assert contract["repository_cli_selector_forwarding_implemented"] is False
    assert contract["caller_count"] == 6
    assert contract["caller_sha256s_bound"] is True


def test_canonical_five_masks_include_scaffold_only_without_sixth(response):
    assert response["canonical_mask_semantic_names"] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert len(response["canonical_mask_semantic_names"]) == 5


def test_readiness_is_derived_from_complete_evidence():
    source = inspect.getsource(
        gate.evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1
    )
    for name in (
        "source_ready",
        "disabled_ready",
        "enabled_ready",
        "migration_ready",
        "validation_ready",
        "threading_ready",
        "injection_ready",
        "oracle_ready",
        "state_ready",
    ):
        assert name in source
    assert "gate_implemented = all(" in source


def test_final_readiness_and_next_step(response):
    assert response["model_consumption_implemented"] is True
    assert response["indicator_passed_into_dynamics"] is True
    assert response["indicator_consumed_by_model"] is True
    assert response["model_consumption_gate_implemented"] is True
    assert response["ready_for_repository_cli_forwarding_design"] is True
    assert response["recommended_next_step"] == (
        "design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1"
    )
    assert response["feature_semantics_audit_required_before_training"] is True


def test_source_drift_fails_closed(monkeypatch):
    monkeypatch.setitem(gate._IMPLEMENTATION_FILES, "lightning_modules.py", "0" * 64)
    _assert_error(_evaluate)


def test_checkpoint_drift_fails_closed(monkeypatch):
    original = gate._read_regular

    def drift(path, **kwargs):
        payload = original(path, **kwargs)
        if path == ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt":
            return payload[:-1] + bytes([payload[-1] ^ 1])
        return payload

    monkeypatch.setattr(gate, "_read_regular", drift)
    _assert_error(_evaluate)


def test_gate_does_not_execute_current_implementation_checker():
    source = Path(gate.__file__).read_text()
    tree = ast.parse(source)
    subprocess_calls = [
        ast.unparse(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
    ]
    assert subprocess_calls
    assert all('"git"' in call or "['git'" in call for call in subprocess_calls)
    assert "_IMPLEMENTATION_FILES" in source
    assert gate._IMPLEMENTATION_FILES[
        "scripts/check_covapie_target_residue_atom_condition_model_consumption_v1.py"
    ] == "6c50f3c7630f161419256b06da8da5fb2904d921f70d7edb52a0f0c12ac95d55"


def test_materializer_new_then_idempotent(tmp_path):
    output = tmp_path / "bundle.json"
    kwargs = {
        "source_runtime_bridge_gate_bundle": RUNTIME_BUNDLE.read_bytes(),
        "repo_root": ROOT,
        "output_path": output,
    }
    first = gate._materialize_covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1(
        **kwargs
    )
    before = output.stat()
    payload = output.read_bytes()
    second = gate._materialize_covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1(
        **kwargs
    )
    after = output.stat()
    assert first["publication_mode"] == "published_new"
    assert second["publication_mode"] == "idempotent_existing"
    assert payload == output.read_bytes()
    assert before.st_ino == after.st_ino
    assert before.st_mtime_ns == after.st_mtime_ns
    assert stat.S_IMODE(after.st_mode) == 0o644
    assert after.st_nlink == 1


def test_materializer_rejects_existing_different(tmp_path):
    output = tmp_path / "bundle.json"
    output.write_bytes(b"different")
    output.chmod(0o644)
    _assert_error(
        lambda: gate._materialize_covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1(
            source_runtime_bridge_gate_bundle=RUNTIME_BUNDLE.read_bytes(),
            repo_root=ROOT,
            output_path=output,
        )
    )


def test_materialized_bundle_is_canonical(tmp_path):
    output = tmp_path / "bundle.json"
    gate._materialize_covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1(
        source_runtime_bridge_gate_bundle=RUNTIME_BUNDLE.read_bytes(),
        repo_root=ROOT,
        output_path=output,
    )
    payload = output.read_bytes()
    assert not payload.endswith((b"\n", b"\r"))
    assert _canonical(json.loads(payload)) == payload
    assert json.loads(payload)["model_consumption_gate_response_sha256"] == (
        _evaluate()["model_consumption_gate_response_sha256"]
    )


def test_formal_bundle_path_is_outside_repository():
    assert FORMAL_BUNDLE.parent == ROOT.parent / "covapie-state/manual-review"
    with pytest.raises(ValueError):
        FORMAL_BUNDLE.relative_to(ROOT)


def test_runtime_bridge_gate_commit_source_and_ancestry_are_bound():
    evidence = gate._runtime_bridge_gate_source_evidence(ROOT)
    assert evidence == {
        "runtime_gate_commit_exists": True,
        "runtime_gate_unique_parent_bound": True,
        "runtime_gate_subject_bound": True,
        "runtime_gate_working_sha256_bound": True,
        "runtime_gate_committed_sha256_bound": True,
        "runtime_gate_working_and_committed_bytes_equal": True,
        "runtime_gate_is_implementation_ancestor": True,
        "runtime_gate_is_head_ancestor": True,
        "runtime_gate_is_origin_main_ancestor": True,
        "runtime_gate_imported_module_path_bound": True,
    }
    assert gate._git(
        ROOT, ["show", "-s", "--format=%P", gate._RUNTIME_BRIDGE_GATE_COMMIT]
    ) == f"{gate._RUNTIME_BRIDGE_GATE_PARENT}\n".encode()
    assert gate._git(
        ROOT, ["show", "-s", "--format=%s", gate._RUNTIME_BRIDGE_GATE_COMMIT]
    ) == f"{gate._RUNTIME_BRIDGE_GATE_SUBJECT}\n".encode()
    production = ROOT / gate._RUNTIME_BRIDGE_GATE_PRODUCTION_PATH
    committed = gate._git(
        ROOT,
        [
            "show",
            f"{gate._RUNTIME_BRIDGE_GATE_COMMIT}:"
            f"{gate._RUNTIME_BRIDGE_GATE_PRODUCTION_PATH}",
        ],
    )
    assert production.read_bytes() == committed
    assert hashlib.sha256(committed).hexdigest() == (
        gate._RUNTIME_BRIDGE_GATE_PRODUCTION_SHA256
    )
    assert Path(gate.runtime_gate.__file__).resolve() == production.resolve()


def test_injection_evidence_restores_rng_before_return():
    rng_state_before = torch.random.get_rng_state().clone()
    _injection, oracle = gate._injection_evidence()
    rng_state_after = torch.random.get_rng_state().clone()
    assert torch.equal(rng_state_after, rng_state_before)
    assert oracle["cpu_rng_state_restored"] is True


def test_rng_restoration_contract_is_derived_not_hardcoded():
    injection_source = inspect.getsource(gate._injection_evidence)
    public_source = inspect.getsource(
        gate.evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1
    )
    assert '"cpu_rng_state_restored": True' not in injection_source
    assert "cpu_rng_state_restored = torch.equal(" in injection_source
    assert "finally:" in injection_source
    assert "torch.random.set_rng_state(rng_state_before)" in injection_source
    assert "if not cpu_rng_state_restored:" in injection_source
    assert "if not torch.equal(torch.random.get_rng_state()" not in public_source
    digest_index = public_source.index(
        'response["model_consumption_gate_response_sha256"] = _sha256('
    )
    after_digest = public_source[digest_index:]
    assert "oracle_contract[" not in after_digest
    assert "torch.random.set_rng_state(entry_rng_state)" in public_source
    assert "if not public_api_rng_state_restored:" in public_source


def test_lineage_and_rng_revision_preserves_exact43_and_formal_bundle():
    formal_before = FORMAL_BUNDLE.read_bytes()
    metadata_before = FORMAL_BUNDLE.stat()
    response = _evaluate()
    assert len(response) == 43
    assert tuple(response) == gate.MODEL_CONSUMPTION_GATE_RESPONSE_FIELDS
    assert response["model_consumption_gate_response_sha256"] == (
        "0ef97cdafe946fefd240c95a94efc8b12be977c899db3b1df4a56a580b53d842"
    )
    assert len(formal_before) == 6449
    assert hashlib.sha256(formal_before).hexdigest() == (
        "18edfbc312128315fd9c880e750aeccc41132b34c20c8e34d78a974e39a2c9aa"
    )
    assert gate._bundle_bytes(response) == formal_before
    publication = gate._materialize_covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1(
        source_runtime_bridge_gate_bundle=RUNTIME_BUNDLE.read_bytes(),
        repo_root=ROOT,
        output_path=FORMAL_BUNDLE,
    )
    metadata_after = FORMAL_BUNDLE.stat()
    assert publication["publication_mode"] == "idempotent_existing"
    assert FORMAL_BUNDLE.read_bytes() == formal_before
    assert metadata_after.st_ino == metadata_before.st_ino
    assert metadata_after.st_mtime_ns == metadata_before.st_mtime_ns
