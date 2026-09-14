from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import os
import sys
from collections import Counter
from dataclasses import fields
from pathlib import Path

import pytest
import torch

from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as mixed_tensorizer,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1,
    CovapieCurrent11TrainingSupervisionTensorsV1,
    canonical_task_id_for_covapie_current11_sample_v1,
)


def _load_subject():
    candidate = os.environ.get("COVAPIE_ADAPTER_CANDIDATE")
    if candidate is None:
        from covalent_ext import (  # noqa: PLC0415
            covapie_current11_legacy_train5_data_adapter_v1 as installed,
        )

        return installed
    path = Path(candidate)
    specification = importlib.util.spec_from_file_location(
        "covapie_current11_legacy_train5_data_adapter_v1_candidate", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


subject = _load_subject()
ERROR = subject.ADAPTER_ERROR_V1


@pytest.fixture(scope="session")
def repository_root() -> Path:
    configured = os.environ.get("COVAPIE_TEST_REPOSITORY_ROOT")
    root = Path(configured) if configured is not None else Path(__file__).resolve().parents[1]
    return root.resolve(strict=True)


@pytest.fixture(scope="session")
def state_root(repository_root: Path) -> Path:
    configured = os.environ.get("COVAPIE_TEST_STATE_ROOT")
    root = Path(configured) if configured is not None else repository_root.parent / "covapie-state"
    return root.resolve(strict=True)


@pytest.fixture(scope="session")
def prepared(repository_root: Path, state_root: Path):
    return subject.prepare_covapie_current11_legacy_train5_data_adapter_v1(
        repository_root,
        state_root,
    )


@pytest.fixture(scope="session")
def epoch0_4(prepared):
    return tuple(
        subject.tensorize_covapie_current11_legacy_train5_epoch_v1(prepared, epoch)
        for epoch in range(5)
    )


def _assert_tensor_exact(left: torch.Tensor, right: torch.Tensor) -> None:
    assert left.dtype == right.dtype
    assert left.shape == right.shape
    assert left.device == right.device
    torch.testing.assert_close(left, right, rtol=0, atol=0, equal_nan=True)


def _assert_result_exact(left, right) -> None:
    assert type(left) is type(right) is mixed_tensorizer.CovapieExpandedCysSgTensorizedSampleV1
    assert left.sample_identity == right.sample_identity
    assert left.role_profile == right.role_profile
    assert left.valid_task_ids == right.valid_task_ids
    assert set(left.model_input_batch) == set(right.model_input_batch)
    for name in left.model_input_batch:
        left_value = left.model_input_batch[name]
        right_value = right.model_input_batch[name]
        if isinstance(left_value, torch.Tensor):
            assert isinstance(right_value, torch.Tensor)
            _assert_tensor_exact(left_value, right_value)
        else:
            digest_left = hashlib.sha256(subject._SEAL_DOMAIN)
            digest_right = hashlib.sha256(subject._SEAL_DOMAIN)
            subject._digest_value(digest_left, left_value)
            subject._digest_value(digest_right, right_value)
            assert digest_left.digest() == digest_right.digest()
    assert isinstance(left.supervision, CovapieCurrent11TrainingSupervisionTensorsV1)
    assert isinstance(right.supervision, CovapieCurrent11TrainingSupervisionTensorsV1)
    for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
        _assert_tensor_exact(
            getattr(left.supervision, field.name),
            getattr(right.supervision, field.name),
        )


def _expect_public_failure(call) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}"):
        call()


def test_public_surface_is_thin_data_only_and_preview_independent() -> None:
    assert subject.__all__ == (
        "ADAPTER_ERROR_V1",
        "CANONICAL_TARGETS_V1",
        "CovapieCurrent11LegacyTrain5PreparedV1",
        "SourceBindingV1",
        "prepare_covapie_current11_legacy_train5_data_adapter_v1",
        "tensorize_covapie_current11_legacy_train5_epoch_v1",
    )
    source = Path(subject.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert "current11_legacy_train5_reuse_preview" not in source
    assert "runpy" not in source
    forbidden_modules = {"lightning_modules", "equivariant_diffusion", "pytorch_lightning"}
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not (forbidden_modules & imported)
    called_names = {
        node.func.id.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not ({"trainer", "optimizer", "backward", "forward", "fit"} & called_names)


def test_real_prepare_binds_exact_five_formal_sources_and_owner_output17(prepared) -> None:
    expected_samples = tuple(item[0] for item in subject.CANONICAL_TARGETS_V1)
    expected_events = tuple(item[1] for item in subject.CANONICAL_TARGETS_V1)
    assert type(prepared) is subject.CovapieCurrent11LegacyTrain5PreparedV1
    assert prepared.schema_version == "covapie_current11_legacy_train5_data_adapter_v1"
    assert prepared.sample_order == expected_samples
    assert prepared.canonical_event_ids == expected_events
    assert prepared.formal_splits == ("train",) * 5
    assert len(prepared.source_bindings) == 27
    assert len(set(prepared.source_bindings)) == 27
    assert prepared.owner_generated_output17_used is True
    assert prepared.post_supervision_overlay_applied is False
    assert prepared.post_authority_source_traceable is True
    assert prepared.training_session_active is False
    assert prepared.ready_for_training is False
    assert prepared.feature_semantics_audit_required_later is True
    assert prepared.step12d_is_only_smoke_legality_check is True
    runtime = prepared._runtime_batch[subject._SIDECAR_FIELD]
    assert runtime["runtime_status"] == "full_success"
    assert runtime["compiler_status"] == "COMPILED_EXACT"
    assert runtime["remap_status"] == "REMAPPED_EXACT"
    output17 = runtime["remap_output17_or_none"]
    assert output17["remap_status"] == "REMAPPED_EXACT"
    assert tuple(
        item["sample_index_row_id"] for item in output17["batch_sample_order"]
    ) == tuple(f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12))


def test_duplicate_non_target_split_and_event_identity_tampering_rejected(prepared) -> None:
    mutations = (
        ("_sample_order", prepared.sample_order[:-1] + (prepared.sample_order[0],)),
        ("_sample_order", prepared.sample_order[:-1] + ("CYS_SG_SAMPLE_INDEX_000011",)),
        ("_canonical_event_ids", prepared.canonical_event_ids[:-1] + (prepared.canonical_event_ids[0],)),
        ("_formal_splits", ("validation",) + ("train",) * 4),
        ("_formal_splits", ("test",) + ("train",) * 4),
    )
    for attribute, replacement in mutations:
        original = getattr(prepared, attribute)
        object.__setattr__(prepared, attribute, replacement)
        try:
            _expect_public_failure(
                lambda: subject.tensorize_covapie_current11_legacy_train5_epoch_v1(
                    prepared, 0
                )
            )
        finally:
            object.__setattr__(prepared, attribute, original)


def test_missing_and_drifted_source_bindings_fail_closed(
    repository_root: Path, tmp_path: Path
) -> None:
    missing = subject.SourceBindingV1("state", "missing.csv", 1, "0" * 64)
    with pytest.raises(subject._AdapterInvariantError, match="SOURCE_UNAVAILABLE"):
        subject._read_bound_source(
            repository=repository_root,
            state=tmp_path,
            binding=missing,
        )
    drifted_path = tmp_path / "drifted.csv"
    drifted_path.write_bytes(b"x")
    drifted = subject.SourceBindingV1("state", "drifted.csv", 1, "0" * 64)
    with pytest.raises(subject._AdapterInvariantError, match="SOURCE_BINDING_DRIFT"):
        subject._read_bound_source(
            repository=repository_root,
            state=tmp_path,
            binding=drifted,
        )


def test_prepare_rejects_non_owner_runtime_before_authority_loading(
    repository_root: Path,
    state_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subject._runtime_integration,
        "build_or_reuse_covapie_current11_task2_lightning_runtime_context_pair_v1",
        lambda **unused: (object(), object()),
    )

    def fake_attach(**arguments):
        batch = dict(arguments["batch"])
        batch[subject._SIDECAR_FIELD] = {
            "runtime_status": "full_success",
            "compiler_status": "COMPILED_EXACT",
            "remap_status": "REMAPPED_EXACT",
            "remap_output17_or_none": {"remap_status": "FORGED"},
        }
        return batch

    monkeypatch.setattr(
        subject._runtime_integration,
        "attach_covapie_current11_task2_lightning_runtime_result_v1",
        fake_attach,
    )
    monkeypatch.setattr(
        subject._materializer,
        "load_covapie_current11_machine_authority_payload_v1",
        lambda **unused: pytest.fail("invalid output17 reached the authority loader"),
    )
    _expect_public_failure(
        lambda: subject.prepare_covapie_current11_legacy_train5_data_adapter_v1(
            repository_root, state_root
        )
    )


def test_epoch0_4_returns_25_real_rows_with_exact5_and_b3(epoch0_4) -> None:
    assert all(type(epoch_rows) is tuple and len(epoch_rows) == 5 for epoch_rows in epoch0_4)
    flattened = [item for epoch_rows in epoch0_4 for item in epoch_rows]
    assert len(flattened) == 25
    expected_order = tuple(item[0] for item in subject.CANONICAL_TARGETS_V1)
    assert all(tuple(item.sample_identity for item in rows) == expected_order for rows in epoch0_4)
    task_counts = Counter(int(item.supervision.canonical_task_id.item()) for item in flattened)
    assert task_counts == Counter({0: 5, 1: 5, 2: 5, 3: 5, 4: 5})
    assert sum(int(item.supervision.canonical_task_id.item()) == 3 for item in flattened) == 5
    assert tuple(CANONICAL_TASKS_V1) == (
        (0, "warhead_only", "A", (2,)),
        (1, "linker_plus_warhead", "B", (1, 2)),
        (2, "scaffold_plus_warhead", "B2", (0, 2)),
        (3, "scaffold_only", "B3", (0,)),
        (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
    )


def test_real_tensor_shapes_roles_pairs_seed_indices_and_geometry(epoch0_4) -> None:
    task_roles = {task_id: set(role_ids) for task_id, _, _, role_ids in CANONICAL_TASKS_V1}
    for epoch_rows in epoch0_4:
        for item in epoch_rows:
            batch = item.model_input_batch
            supervision = item.supervision
            tensors = [
                value for value in batch.values() if isinstance(value, torch.Tensor)
            ] + [getattr(supervision, field.name) for field in fields(supervision)]
            assert tensors and all(value.device.type == "cpu" for value in tensors)
            ligand_count = int(batch["num_lig_atoms"].item())
            pocket_count = int(batch["num_pocket_nodes"].item())
            assert batch["lig_coords"].shape == (ligand_count, 3)
            assert batch["pocket_coords"].shape == (pocket_count, 3)
            assert batch["lig_one_hot"].shape == (ligand_count, 10)
            assert batch["pocket_one_hot"].shape == (pocket_count, 10)
            for one_hot in (batch["lig_one_hot"], batch["pocket_one_hot"]):
                assert bool(((one_hot == 0) | (one_hot == 1)).all().item())
                assert bool((one_hot.sum(dim=1) == 1).all().item())
            assert batch["lig_parser_local_index"].tolist() == list(range(ligand_count))
            assert batch["pocket_parser_local_index"].tolist() == list(range(pocket_count))
            assert batch["lig_source_row_index"].tolist() == sorted(
                set(batch["lig_source_row_index"].tolist())
            )
            assert batch["pocket_source_row_index"].tolist() == sorted(
                set(batch["pocket_source_row_index"].tolist())
            )
            assert batch["lig_mask"].tolist() == [0] * ligand_count
            assert batch["pocket_mask"].tolist() == [0] * pocket_count
            assert bool(supervision.sample_training_admitted.item())
            assert bool(supervision.canonical_task_valid.item())
            task_id = int(supervision.canonical_task_id.item())
            roles = supervision.ligand_role_id
            assert bool(supervision.ligand_role_valid.all().item())
            assert set(roles.tolist()) == {0, 1, 2}
            expected_generation = torch.tensor(
                [int(role) in task_roles[task_id] for role in roles], dtype=torch.bool
            )
            generation = supervision.ligand_base_generation_mask[:, 0]
            fixed = supervision.ligand_base_fixed_mask[:, 0]
            assert torch.equal(generation, expected_generation)
            assert torch.equal(fixed, ~generation)
            assert torch.equal(supervision.ligand_base_target_mask[:, 0], generation)
            assert torch.equal(supervision.ligand_base_context_mask[:, 0], fixed)
            assert torch.equal(supervision.ligand_active_diffusion_loss_mask[:, 0], generation)
            target_membership = supervision.target_residue_membership_mask[:, 0]
            target_reactive = supervision.target_residue_reactive_atom_mask[:, 0]
            target_local = int(supervision.target_residue_reactive_atom_local_index.item())
            assert bool(supervision.target_residue_condition_valid.item())
            assert int(target_membership.sum().item()) > 0
            assert int(target_reactive.sum().item()) == 1
            assert bool(target_membership[target_local].item())
            assert bool(target_reactive[target_local].item())
            positive = int(supervision.pair_positive_candidate_index.item())
            candidate_count = supervision.pair_candidate_is_positive.numel()
            assert bool(supervision.pair_positive_candidate_valid.item())
            assert int(supervision.pair_candidate_is_positive.sum().item()) == 1
            assert bool(supervision.pair_candidate_is_positive[positive].item())
            assert int(supervision.pair_negative_count.item()) == candidate_count - 1
            assert torch.equal(
                supervision.pair_candidate_is_negative,
                ~supervision.pair_candidate_is_positive,
            )
            ligand_local = int(
                supervision.pair_candidate_ligand_local_index[positive].item()
            )
            pocket_local = int(
                supervision.pair_candidate_residue_local_index[positive].item()
            )
            assert int(
                supervision.pair_candidate_ligand_flat_index[positive].item()
            ) == ligand_local
            assert int(
                supervision.pair_candidate_pocket_flat_index[positive].item()
            ) == pocket_local
            observed_from_coordinates = torch.linalg.vector_norm(
                batch["lig_coords"][ligand_local]
                - batch["pocket_coords"][pocket_local]
            )
            assert abs(
                float(observed_from_coordinates.item())
                - float(supervision.observed_complex_pair_distance_angstrom.item())
            ) <= 0.0015
            runtime_seed_count = int(
                supervision.ligand_minimal_seed_or_anchor_mask.sum().item()
            )
            if task_id == 4:
                assert bool(supervision.ligand_minimal_seed_or_anchor_valid.item())
                assert runtime_seed_count > 0
            else:
                assert not bool(supervision.ligand_minimal_seed_or_anchor_valid.item())
                assert runtime_seed_count == 0
            assert bool(supervision.ligand_anchor_distance_valid.all().item())
            assert bool(torch.isfinite(supervision.ligand_anchor_distance_angstrom).all().item())
            assert bool(supervision.observed_complex_pair_distance_valid.item())
            assert bool(torch.isfinite(supervision.observed_complex_pair_distance_angstrom).all().item())
            assert not bool(supervision.pre_post_geometry_component_valid_mask.any().item())
            assert not bool(supervision.pre_post_geometry_component_loss_mask.any().item())
            assert bool(torch.isnan(supervision.pre_post_geometry_target_angstrom).all().item())


def test_deterministic_same_epoch_seed_and_direct_mixed_tensorizer_equivalence(prepared) -> None:
    epoch = 3
    seed = 7
    first = subject.tensorize_covapie_current11_legacy_train5_epoch_v1(prepared, epoch, seed)
    second = subject.tensorize_covapie_current11_legacy_train5_epoch_v1(prepared, epoch, seed)
    for left, right in zip(first, second):
        _assert_result_exact(left, right)

    runtime_batch = copy.deepcopy(prepared._runtime_batch)
    runtime_result = runtime_batch[subject._SIDECAR_FIELD]
    authoritative = copy.deepcopy(prepared._authoritative_supervision)
    for expected in first:
        task_id = canonical_task_id_for_covapie_current11_sample_v1(
            sample_key=expected.sample_identity,
            epoch=epoch,
            task_schedule_seed=seed,
        )
        direct = mixed_tensorizer.tensorize_covapie_expanded_cys_sg_sample_v1(
            sample_identity=expected.sample_identity,
            task_id=task_id,
            device="cpu",
            epoch=epoch,
            task_schedule_seed=seed,
            current11_batch=runtime_batch,
            current11_runtime_result=runtime_result,
            current11_authoritative_supervision=authoritative,
        )
        _assert_result_exact(expected, direct)


def test_return_and_prepared_mutation_cannot_silently_pollute(prepared) -> None:
    baseline = subject.tensorize_covapie_current11_legacy_train5_epoch_v1(prepared, 0)
    expected_coordinate = baseline[0].model_input_batch["lig_coords"].clone()
    expected_roles = baseline[0].supervision.ligand_role_id.clone()
    baseline[0].model_input_batch["lig_coords"].add_(1000)
    baseline[0].supervision.ligand_role_id.fill_(-1)
    rebuilt = subject.tensorize_covapie_current11_legacy_train5_epoch_v1(prepared, 0)
    _assert_tensor_exact(rebuilt[0].model_input_batch["lig_coords"], expected_coordinate)
    _assert_tensor_exact(rebuilt[0].supervision.ligand_role_id, expected_roles)

    stored = prepared._runtime_batch["lig_coords"]
    original = stored[0, 0].item()
    stored[0, 0] += 1
    try:
        _expect_public_failure(
            lambda: subject.tensorize_covapie_current11_legacy_train5_epoch_v1(
                prepared, 0
            )
        )
    finally:
        stored[0, 0] = original
    assert len(subject.tensorize_covapie_current11_legacy_train5_epoch_v1(prepared, 0)) == 5


@pytest.mark.parametrize("epoch", [True, -1, 1.5, "0", None])
def test_invalid_epochs_rejected_without_new_schedule(epoch, prepared) -> None:
    _expect_public_failure(
        lambda: subject.tensorize_covapie_current11_legacy_train5_epoch_v1(
            prepared, epoch
        )
    )


@pytest.mark.parametrize("seed", [True, -1, 2**63, 1.5, "0", None])
def test_invalid_schedule_seeds_rejected(seed, prepared) -> None:
    _expect_public_failure(
        lambda: subject.tensorize_covapie_current11_legacy_train5_epoch_v1(
            prepared, 0, seed
        )
    )
