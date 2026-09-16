"""Exact2 external candidate: genuine CPU owner reuse, five semantic tasks."""

from __future__ import annotations

import copy
import csv
from dataclasses import fields
from dataclasses import replace
import hashlib
import importlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import subprocess

import pytest
import torch


BASELINE = "2562b03709a8ab3267d7023c80fe29c4a13ac8a3"
STATS = {"prepare": 0, "current11_build": 0, "positive_build": 0,
         "target_event_objects": 0, "event_task_constructions": [], "supervision_validity": {}}


def _roots():
    return (Path(os.environ["COVAPIE_TEST_REPOSITORY_ROOT"]),
            Path(os.environ["COVAPIE_TEST_STATE_ROOT"]),
            Path(os.environ["COVAPIE_TEST_CACHE_ROOT"]))


def _assert_fixed_source_baseline_in_head_history(repo):
    """The immutable source commit must exist and precede the current HEAD."""
    try:
        commit = subprocess.run(("git", "cat-file", "-e", f"{BASELINE}^{{commit}}"),
                                cwd=repo, stdin=subprocess.DEVNULL,
                                capture_output=True, check=False)
    except OSError as error:
        raise AssertionError("FIXED_SOURCE_BASELINE_GIT_COMMAND_ERROR") from error
    if commit.returncode != 0:
        reason = ("FIXED_SOURCE_BASELINE_COMMIT_MISSING" if commit.returncode == 1
                  else "FIXED_SOURCE_BASELINE_COMMIT_QUERY_ERROR")
        raise AssertionError(reason)
    try:
        ancestry = subprocess.run(("git", "merge-base", "--is-ancestor", BASELINE, "HEAD"),
                                  cwd=repo, stdin=subprocess.DEVNULL,
                                  capture_output=True, check=False)
    except OSError as error:
        raise AssertionError("FIXED_SOURCE_BASELINE_GIT_COMMAND_ERROR") from error
    if ancestry.returncode == 0:
        return
    if ancestry.returncode == 1:
        raise AssertionError("FIXED_SOURCE_BASELINE_NOT_HEAD_ANCESTOR")
    raise AssertionError("FIXED_SOURCE_BASELINE_ANCESTRY_QUERY_ERROR")


def _adapter():
    candidate = os.environ.get("COVAPIE_READY2_TEST_PRODUCTION_PATH")
    if candidate:
        location = Path(candidate)
        assert location.name == "covapie_jug_gjj_ready2_data_adapter_v1.py"
        spec = importlib.util.spec_from_file_location("covapie_jug_gjj_ready2_data_adapter_v1", location)
        module = importlib.util.module_from_spec(spec)
        import sys
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    return importlib.import_module("covalent_ext.covapie_jug_gjj_ready2_data_adapter_v1")


@pytest.fixture(scope="session")
def owner():
    from covalent_ext import covapie_current11_legacy_train5_data_adapter_v1 as old
    from covalent_ext import covapie_existing_positive_runtime_and_split_closure_v1 as positive
    from covalent_ext import covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as mixed
    from covalent_ext import covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1 as policy
    from covalent_ext import covapie_train10_cpu_batch_composer_v1 as train10
    return old, positive, mixed, policy, train10


@pytest.fixture(scope="session")
def prepared(owner):
    adapter = _adapter()
    repo, state, cache = _roots()
    _assert_fixed_source_baseline_in_head_history(repo)
    prepared = adapter.prepare_covapie_jug_gjj_ready2_data_adapter_v1(
        repository_root=repo, state_root=state, cache_root=cache)
    STATS["prepare"] += 1
    STATS["current11_build"] += 1
    STATS["positive_build"] += 1
    STATS["target_event_objects"] = 2
    yield adapter, prepared
    print("READY2_SESSION_ACTUAL prepare={prepare} current11_upstream_calls={current11_build} "
          "positive_closure_upstream_calls={positive_build} target_event_objects={target_event_objects} "
          "event_task_constructions={event_task_constructions} supervision_validity={supervision_validity}"
          .format(**STATS))


def _equal(left, right):
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        assert left.shape == right.shape and left.dtype == right.dtype
        torch.testing.assert_close(left, right, rtol=0, atol=0, equal_nan=True)
    elif type(left) is dict and type(right) is dict:
        assert left.keys() == right.keys()
        for name in left:
            _equal(left[name], right[name])
    elif type(left) in (list, tuple) and type(right) is type(left):
        assert len(left) == len(right)
        for a, b in zip(left, right):
            _equal(a, b)
    elif isinstance(left, float) and isinstance(right, float) and math.isnan(left) and math.isnan(right):
        return
    else:
        assert left == right


def _model_and_supervision_equal(result, native):
    _equal(result.model_input_batch, native.model_input_batch)
    assert tuple(f.name for f in fields(result.supervision)) == tuple(f.name for f in fields(native.supervision))
    for f in fields(native.supervision):
        _equal(getattr(result.supervision, f.name), getattr(native.supervision, f.name))


def _csv_pin(repo, name, expected):
    payload = (repo / name).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == expected
    assert subprocess.run(("git", "show", f"{BASELINE}:{name}"), cwd=repo,
                          capture_output=True, check=True).stdout == payload
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def test_published_formal_authority_not_census(prepared, owner):
    adapter, component = prepared
    repo, _, _ = _roots()
    positives = _csv_pin(repo, adapter._BASE + "covapie_current_runtime_model_usable_positive_index_v1.csv",
                         "5485305a750129e437ef68b43c758f9f0586add41fe54ee1d621b6c5bde62410")
    leakage = _csv_pin(repo, adapter._BASE + "covapie_existing_positive_leakage_split_closure_inventory_v1.csv",
                       "2f673a8ca76217af1517d8254de79799d4fea333d9892af13a3ab0eeb90d8259")
    old, positive, _, _, train10 = owner
    assert component.upstream_construction_scope == {
        "current11_runtime_samples": 11, "positive_closure_runtime_samples": 7,
        "positive_closure_task_checks": 35, "positive_closure_default_task_builds": 7,
        "returned_target_events": 2,
    }
    assert old.CANONICAL_TARGETS_V1[0][0] != adapter.TARGETS_V1[0][1]
    assert adapter.TARGETS_V1[1][0] in positive.RUNTIME_TARGET_EVENT_IDS_V1
    assert set(train10.TRAIN10_CANONICAL_EVENT_IDS_V1).isdisjoint(x[0] for x in adapter.TARGETS_V1)
    groups = {row["leakage_group_id_after"] for row in leakage
              if row["sample_identity"] in train10.TRAIN10_SAMPLE_IDENTITIES_V1}
    assert len(groups) == 3 and groups.isdisjoint(x[2] for x in adapter.TARGETS_V1)
    heldout = {row["leakage_group_id_after"] for row in leakage
               if row["formal_split_authoritative_after"] == "true" and row["formal_split_after"] in ("validation", "test")}
    assert heldout.isdisjoint(x[2] for x in adapter.TARGETS_V1)
    for event, identity, group in adapter.TARGETS_V1:
        p = next(r for r in positives if r["canonical_event_id"] == event)
        l = next(r for r in leakage if r["canonical_event_id"] == event)
        assert p["sample_identity"] == l["sample_identity"] == identity
        assert p["leakage_group_id"] == l["leakage_group_id_after"] == group
        assert p["formal_split"] == l["formal_split_after"] == "train"
        assert p["training_admission_readiness"] == l["training_admission_readiness"] == "FORMAL_TRAIN_ADMITTED"
        assert p["runtime_binding_status"] == "CURRENT_RUNTIME_BINDING_CLOSED"
        assert p["positive_authority_status"] == "FULL_POSITIVE_SUPERVISION_AUTHORITY"


def test_real_exact2_exact5_native_tensor_field_equivalence(prepared, owner):
    adapter, component = prepared
    old, positive, mixed, _, _ = owner
    before_old = old._prepared_seal(component._legacy)
    before_gjj = adapter._seal(component)
    assert adapter.TASK_NAMES_V1 == tuple(task[1] for task in adapter._EXPECTED_TASKS)
    assert adapter.TASK_NAMES_V1[3] == "scaffold_only"
    assert len(fields(component._gjj.supervision)) == 37
    for event, identity, group in adapter.TARGETS_V1:
        for name in adapter.TASK_NAMES_V1:
            item = adapter.build_covapie_jug_gjj_ready2_canonical_task_data_v1(
                component, canonical_event_id=event, canonical_task_name=name)
            task = next(task[0] for task in adapter._EXPECTED_TASKS if task[1] == name)
            if identity == adapter.TARGETS_V1[0][1]:
                batch = copy.deepcopy(component._legacy._runtime_batch)
                authority = copy.deepcopy(component._legacy._authoritative_supervision)
                native = mixed.tensorize_covapie_expanded_cys_sg_sample_v1(
                    sample_identity=identity, task_id=task, device="cpu", epoch=None,
                    task_schedule_seed=0, current11_batch=batch,
                    current11_runtime_result=batch[old._SIDECAR_FIELD],
                    current11_authoritative_supervision=authority)
            else:
                model, supervision = positive._model_batch_and_supervision(
                    copy.deepcopy(component._gjj.payload), task_id=task,
                    training_admitted=True)
                native = type("Native", (), {"model_input_batch": model, "supervision": supervision})()
            _model_and_supervision_equal(item, native)
            assert (item.canonical_event_id, item.sample_identity, item.formal_leakage_group_id,
                    item.formal_split, item.canonical_task_name) == (event, identity, group, "train", name)
            assert item.source_bindings == component._bindings
            if identity == adapter.TARGETS_V1[0][1]:
                assert item.native_source_bindings == tuple((binding.root, binding.relative_path,
                                                            binding.byte_count, binding.sha256)
                                                           for binding in component._legacy.source_bindings)
                assert len(item.native_source_bindings) == 27
            else:
                assert item.native_source_bindings == component._gjj_source_bindings
                assert len(item.native_source_bindings) >= 18
            assert item.model_input_batch["names"] == [identity]
            s = item.supervision
            assert s.sample_training_admitted.item() and s.canonical_task_valid.item()
            assert int(s.canonical_task_id.item()) == task
            assert s.ligand_base_generation_mask.any().item()
            assert int(s.pair_candidate_is_positive.sum().item()) == 1
            assert int(s.pair_positive_candidate_index.item()) >= 0
            assert not s.pre_post_geometry_component_valid_mask[0, 0].item()
            assert not s.pre_post_geometry_component_loss_mask[0, 0].item()
            assert bool(torch.isnan(s.pre_post_geometry_target_angstrom[0, 0]).item())
            assert s.observed_complex_pair_distance_valid.item()
            assert s.target_residue_condition_valid.item()
            assert item.model_input_batch["lig_one_hot"].shape[1] == 10
            assert item.model_input_batch["pocket_one_hot"].shape[1] == 10
            assert int(s.target_residue_membership_mask.sum().item()) > 0
            STATS["event_task_constructions"].append((identity, name))
            STATS["supervision_validity"].setdefault(identity, []).append({
                "task": name, "PRE_valid": bool(s.pre_post_geometry_component_valid_mask[0, 0]),
                "POST_valid": bool(s.pre_post_geometry_component_valid_mask[0, 1]),
                "observed_valid": bool(s.observed_complex_pair_distance_valid.item()),
                "positive_pair_valid": bool(s.pair_positive_candidate_valid.item()),
            })
    assert len(set(STATS["event_task_constructions"])) == 10
    assert before_old == old._prepared_seal(component._legacy)
    assert before_gjj == adapter._seal(component)


def test_source_to_exact10_feature_and_indices(prepared, owner):
    adapter, component = prepared
    repo, _, _ = _roots()
    _, positive, _, policy, _ = owner
    disposition = _csv_pin(repo, "data/derived/covalent_small/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/covapie_heavy_atom_disposition_and_index_projection_matrix.csv",
                           "b53f438edffab32f78d07df839b8c8437ec4223e31bd8a8885deedf32497b4be")
    jug = adapter.build_covapie_jug_gjj_ready2_canonical_task_data_v1(
        component, canonical_event_id=adapter.TARGETS_V1[0][0], canonical_task_name="scaffold_only")
    for side, prefix in (("ligand_atom", "lig"), ("protein_or_pocket_atom", "pocket")):
        rows = {int(r["projected_heavy_atom_row_index_0based"]): r for r in disposition
                if r["sample_index_row_id"] == adapter.TARGETS_V1[0][1] and r["domain"] == side
                and r["retained_for_checkpoint_model"] == "true"}
        hot = jug.model_input_batch[f"{prefix}_one_hot"]
        assert len(rows) == len(hot)
        for idx, vector in enumerate(hot):
            record = rows[idx]
            projection = policy.project_type_symbols_to_checkpoint_heavy_v1((record["type_symbol"],))
            assert not projection.sample_rejected
            channel = projection.checkpoint_channel_indices[0]
            assert channel == int(record["checkpoint_channel_index"])
            assert vector.tolist() == [float(i == channel) for i in range(10)]
            assert int(jug.model_input_batch[f"{prefix}_parser_local_index"][idx]) == idx
            assert int(jug.model_input_batch[f"{prefix}_source_row_index"][idx]) == int(record["source_atom_row_index_0based"])
    gjj = adapter.build_covapie_jug_gjj_ready2_canonical_task_data_v1(
        component, canonical_event_id=adapter.TARGETS_V1[1][0], canonical_task_name="scaffold_only")
    payload = component._gjj.payload
    positive.validate_runtime_adapter_payload_v1(payload)
    runtime = _csv_pin(repo, adapter._BASE + "covapie_existing_positive_runtime_binding_inventory_v1.csv",
                       "b8a0f4c2bc8ca46141775f0a5fa54322d12db685b37c930659f6f4a1ca3b4052")
    row = next(r for r in runtime if r["canonical_event_id"] == adapter.TARGETS_V1[1][0])
    assert row == positive._runtime_row(component._gjj)
    for prefix, table, field in (("lig", positive.DIRECT_LIGAND_ROWS_V1, "atom_symbol"),
                                 ("pocket", positive.DIRECT_POCKET_ROWS_V1, "type_symbol")):
        source = _csv_pin(repo, table.as_posix(), positive.FIXED_REPOSITORY_INPUT_SHA256_V1[table])
        retained = [r for r in source if r["pdb_id"] == "6DI9"]
        if prefix == "lig":
            retained.sort(key=lambda r: int(r["rdkit_atom_idx"]))
        assert len(retained) == len(gjj.model_input_batch[f"{prefix}_source_row_index"])
        for local, record in enumerate(retained):
            projected = policy.project_type_symbols_to_checkpoint_heavy_v1((record[field],))
            assert not projected.sample_rejected
            channel = projected.checkpoint_channel_indices[0]
            assert gjj.model_input_batch[f"{prefix}_one_hot"][local].tolist() == [float(i == channel) for i in range(10)]
            assert int(gjj.model_input_batch[f"{prefix}_source_row_index"][local]) == source.index(record)
            assert int(gjj.model_input_batch[f"{prefix}_parser_local_index"][local]) == local
    assert tuple(payload["positive_reactive_pair_indices"]) == tuple(json.loads(row["positive_reactive_pair_indices_json"]))
    assert int(gjj.supervision.target_residue_reactive_atom_local_index.item()) == int(payload["target_reactive_pocket_local_index"])
    assert gjj.supervision.target_residue_membership_mask[int(payload["target_reactive_pocket_local_index"])].item()
    assert (int(gjj.supervision.pair_candidate_ligand_local_index[gjj.supervision.pair_positive_candidate_index.item()]),
            int(gjj.supervision.pair_candidate_residue_local_index[gjj.supervision.pair_positive_candidate_index.item()])) == tuple(payload["positive_reactive_pair_indices"])


def test_bad_identity_task_source_and_native_payload_fail_closed(prepared, owner, monkeypatch):
    adapter, component = prepared
    event = adapter.TARGETS_V1[0][0]
    for invalid in ("COVAPIE_CYS_SG_EVENT_V1:6BV6:A:CYS:353-:SG:B:JUG:CAG", "6DI9/GJJ", "", None):
        with pytest.raises(ValueError, match="NON_TARGET_EVENT_REJECTED"):
            adapter.build_covapie_jug_gjj_ready2_canonical_task_data_v1(
                component, canonical_event_id=invalid, canonical_task_name="scaffold_only")
    for invalid in ("B3", "warhead", "wrong", None, 3):
        with pytest.raises(ValueError, match="CANONICAL_TASK_NOT_IN_EXACT5"):
            adapter.build_covapie_jug_gjj_ready2_canonical_task_data_v1(
                component, canonical_event_id=event, canonical_task_name=invalid)
    before = adapter._seal(component)
    copied = copy.deepcopy(component._gjj.payload)
    copied["source_bindings_verified"] = False
    with pytest.raises(ValueError, match="SOURCE_SHA_DRIFT"):
        owner[1].validate_runtime_adapter_payload_v1(copied)
    copied = copy.deepcopy(component._gjj.payload)
    copied["positive_reactive_pair_indices"] = (0, 0)
    with pytest.raises(ValueError, match="REACTIVE_PAIR_MISMATCH"):
        owner[1].validate_runtime_adapter_payload_v1(copied)
    old_native = component._gjj
    tampered = copy.deepcopy(old_native)
    tampered.payload["source_bindings_verified"] = False
    component._gjj = tampered
    try:
        with pytest.raises(ValueError):
            adapter.build_covapie_jug_gjj_ready2_canonical_task_data_v1(
                component, canonical_event_id=adapter.TARGETS_V1[1][0], canonical_task_name="scaffold_only")
    finally:
        component._gjj = old_native
    assert before == adapter._seal(component)
    mismatched = replace(old_native, sample_identity="6DI9/MOV")
    component._gjj = mismatched
    try:
        with pytest.raises(ValueError, match="GJJ_NATIVE_IDENTITY_DRIFT"):
            adapter.build_covapie_jug_gjj_ready2_canonical_task_data_v1(
                component, canonical_event_id=adapter.TARGETS_V1[1][0], canonical_task_name="scaffold_only")
    finally:
        component._gjj = old_native
    repo, _, _ = _roots()
    relative = adapter._BASE + "covapie_current_runtime_model_usable_positive_index_v1.csv"
    exact_path = repo / relative
    original_read = Path.read_bytes
    def forged_read(path):
        raw = original_read(path)
        return raw + b"forged" if path == exact_path else raw
    with monkeypatch.context() as patched:
        patched.setattr(Path, "read_bytes", forged_read)
        with pytest.raises(ValueError, match="SOURCE_SHA_DRIFT"):
            adapter.build_covapie_jug_gjj_ready2_canonical_task_data_v1(
                component, canonical_event_id=event, canonical_task_name="scaffold_only")
    assert before == adapter._seal(component)


def test_import_and_runtime_boundary_ast(prepared):
    adapter, _ = prepared
    path = Path(adapter.__file__)
    import ast
    tree = ast.parse(path.read_text())
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id in ("prepare_covapie_jug_gjj_ready2_data_adapter_v1",)
                   for node in tree.body)
    assert set(adapter.TASK_NAMES_V1) == {"warhead_only", "linker_plus_warhead",
                                           "scaffold_plus_warhead", "scaffold_only",
                                           "scaffold_plus_linker_plus_warhead"}
    assert "checkpoint" not in " ".join(node.func.id for node in ast.walk(tree)
                                      if isinstance(node, ast.Call) and isinstance(node.func, ast.Name))


@pytest.mark.parametrize("scenario,commit_rc,ancestry_rc,launch_error,expected_error", (
    ("SIMULATED_HEAD_EQUALS_BASELINE", 0, 0, False, None),
    ("SIMULATED_HEAD_DESCENDS_FROM_BASELINE", 0, 0, False, None),
    ("SIMULATED_UNRELATED_HEAD", 0, 1, False, "NOT_HEAD_ANCESTOR"),
    ("SIMULATED_MISSING_FIXED_COMMIT", 1, None, False, "COMMIT_MISSING"),
    ("SIMULATED_COMMIT_QUERY_GIT_FAILURE", 128, None, False, "COMMIT_QUERY_ERROR"),
    ("SIMULATED_ANCESTRY_QUERY_GIT_FAILURE", 0, 128, False, "ANCESTRY_QUERY_ERROR"),
    ("SIMULATED_GIT_LAUNCH_FAILURE", 0, None, True, "GIT_COMMAND_ERROR"),
))
def test_simulated_baseline_head_relation_fail_closed(
    monkeypatch, scenario, commit_rc, ancestry_rc, launch_error, expected_error,
):
    """Isolated Git-return stubs; these are NOT a real postcommit data test."""
    repo = Path("/simulated/ready2/repository")
    called = []

    def simulated_git(args, *, cwd, stdin, capture_output, check):
        assert cwd == repo and stdin is subprocess.DEVNULL
        assert capture_output is True and check is False
        called.append(tuple(args))
        if launch_error:
            raise OSError("simulated missing git executable")
        if args == ("git", "cat-file", "-e", f"{BASELINE}^{{commit}}"):
            return subprocess.CompletedProcess(args, commit_rc, b"", b"")
        assert args == ("git", "merge-base", "--is-ancestor", BASELINE, "HEAD")
        return subprocess.CompletedProcess(args, ancestry_rc, b"", b"")

    with monkeypatch.context() as patched:
        patched.setattr(subprocess, "run", simulated_git)
        if expected_error is None:
            _assert_fixed_source_baseline_in_head_history(repo)
            assert len(called) == 2
        else:
            with pytest.raises(AssertionError, match=expected_error):
                _assert_fixed_source_baseline_in_head_history(repo)
            assert len(called) == (1 if commit_rc != 0 or launch_error else 2)
    assert scenario.startswith("SIMULATED_")
