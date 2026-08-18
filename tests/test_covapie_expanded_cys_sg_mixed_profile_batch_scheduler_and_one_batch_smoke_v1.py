from __future__ import annotations

import copy
import os
import shutil
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

import pytest
import torch

from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1
    as subject,
)
from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as mixed_tensorizer,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    canonical_task_id_for_covapie_current11_sample_v1,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
ERROR = (
    subject.COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_BATCH_SCHEDULER_AND_ONE_BATCH_SMOKE_V1_ERROR
)
EXPECTED_CURRENT11_EPOCH0 = (3, 2, 3, 0, 2, 4, 0, 0, 4, 4, 1)
EXPECTED_K36_EPOCH0 = (3, 0, 0, 0, 0)
EXPECTED_CURRENT11_SEED9_EPOCH0 = (1, 3, 0, 3, 0, 0, 3, 4, 3, 4, 3)
EXPECTED_K36_SEED9_EPOCH0 = (3, 0, 4, 0, 3)
FROZEN_BASELINE = "f690802c24b78ace19f9a47285ced7be73cfc55b"


def _assert_public_error(callable_object) -> None:
    with pytest.raises(ValueError) as error:
        callable_object()
    assert str(error.value).startswith(ERROR)


@pytest.fixture
def local_verification_tmp():
    path = Path(
        tempfile.mkdtemp(prefix="covapie-successor-verification.", dir=ROOT.parent)
    )
    try:
        yield path
    finally:
        shutil.rmtree(path)


@pytest.fixture(scope="module")
def real_current11_inputs(tmp_path_factory: pytest.TempPathFactory):
    from covalent_ext import (
        covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
        as current11_smoke,
    )

    temporary = tmp_path_factory.mktemp("covapie_exact16_collator")
    repository = temporary / "repository"
    subject._clone_head_v1(ROOT, repository)
    assert subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repository,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ).stdout.strip() == FROZEN_BASELINE
    return current11_smoke._build_real_current11_batch_v1(
        repo_root=repository,
        state_root=STATE,
    )


def _tensorize_exact16(real, *, epoch: int, task_schedule_seed: int):
    samples = []
    for identity in subject.EXACT16_MEMBER_IDENTITIES_V1:
        task_id = subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
            sample_identity=identity,
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
        )
        if identity in mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1:
            sample = mixed_tensorizer.tensorize_covapie_expanded_cys_sg_sample_v1(
                sample_identity=identity,
                task_id=task_id,
                device="cpu",
                epoch=epoch,
                task_schedule_seed=task_schedule_seed,
                current11_batch=real["model_batch"],
                current11_runtime_result=real["runtime"],
                current11_authoritative_supervision=(
                    real["authoritative_supervision"]
                ),
            )
        else:
            sample = mixed_tensorizer.tensorize_covapie_expanded_cys_sg_sample_v1(
                sample_identity=identity,
                task_id=task_id,
                device="cpu",
                repository_root=ROOT,
                state_root=STATE,
            )
        samples.append(sample)
    return tuple(samples)


@pytest.fixture(scope="module")
def exact16_samples(real_current11_inputs):
    return _tensorize_exact16(
        real_current11_inputs, epoch=0, task_schedule_seed=0
    )


@pytest.fixture(scope="module")
def exact16_mixed_batch(exact16_samples):
    return subject.collate_covapie_expanded_cys_sg_exact16_tensorized_samples_v1(
        exact16_samples,
        epoch=0,
        task_schedule_seed=0,
    )


def test_exact16_population_and_global_contract_remain_exact() -> None:
    assert subject.EXACT16_MEMBER_IDENTITIES_V1 == (
        tuple(
            f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
        )
        + ("4DCD/K36", "4F49/K36", "5WKJ/K36", "6L70/K36", "6WTT/K36")
    )
    assert len(subject.EXACT16_MEMBER_IDENTITIES_V1) == 16
    assert subject.EXACT16_STRICT_PROFILE_COUNT_V1 == 11
    assert subject.EXACT16_DIRECT_PROFILE_COUNT_V1 == 5
    assert subject.K36_VALID_TASK_IDS_V1 == (0, 3, 4)
    assert mixed_tensorizer.GLOBAL_ROLE_VOCABULARY_V1 == (
        (0, "scaffold"),
        (1, "linker"),
        (2, "warhead"),
    )
    assert tuple(item[:3] for item in mixed_tensorizer.GLOBAL_TASK_VOCABULARY_V1) == (
        (0, "warhead_only", "A"),
        (1, "linker_plus_warhead", "B"),
        (2, "scaffold_plus_warhead", "B2"),
        (3, "scaffold_only", "B3"),
        (4, "scaffold_plus_linker_plus_warhead", "C"),
    )


def test_current11_scheduler_delegates_with_exact_numerical_parity() -> None:
    for seed in (0, 1, 9, 10, 16, 18, 2**63 - 1):
        for epoch in range(5):
            for identity in mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1:
                assert (
                    subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
                        sample_identity=identity,
                        epoch=epoch,
                        task_schedule_seed=seed,
                    )
                    == canonical_task_id_for_covapie_current11_sample_v1(
                        sample_key=identity,
                        epoch=epoch,
                        task_schedule_seed=seed,
                    )
                )
    assert tuple(
        subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
            sample_identity=identity,
            epoch=0,
            task_schedule_seed=0,
        )
        for identity in mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1
    ) == EXPECTED_CURRENT11_EPOCH0


def test_k36_scheduler_exact_rotation_and_never_invalid_tasks() -> None:
    for seed in (0, 9, 10, 16, 18, 71, 2**63 - 1):
        for identity in mixed_tensorizer.K36_MEMBER_IDENTITIES_V1:
            observed = tuple(
                subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
                    sample_identity=identity,
                    epoch=epoch,
                    task_schedule_seed=seed,
                )
                for epoch in range(9)
            )
            assert set(observed) == {0, 3, 4}
            assert not set(observed) & {1, 2}
            for start in range(7):
                assert set(observed[start : start + 3]) == {0, 3, 4}
    assert tuple(
        subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
            sample_identity=identity,
            epoch=0,
            task_schedule_seed=0,
        )
        for identity in mixed_tensorizer.K36_MEMBER_IDENTITIES_V1
    ) == EXPECTED_K36_EPOCH0


@pytest.mark.parametrize("seed", (9, 10, 16, 18))
def test_single_batch_exact5_coverage_is_not_a_scheduler_contract(
    seed: int,
) -> None:
    current11_tasks = tuple(
        subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
            sample_identity=identity,
            epoch=0,
            task_schedule_seed=seed,
        )
        for identity in mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1
    )
    k36_tasks = tuple(
        subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
            sample_identity=identity,
            epoch=0,
            task_schedule_seed=seed,
        )
        for identity in mixed_tensorizer.K36_MEMBER_IDENTITIES_V1
    )
    assert set(current11_tasks + k36_tasks) != set(range(5))
    assert set(current11_tasks) <= {0, 1, 2, 3, 4}
    assert set(k36_tasks) <= {0, 3, 4}
    assert not set(k36_tasks) & {1, 2}


def test_task_coverage_is_temporal_per_sample_not_batch_level() -> None:
    for seed in (0, 9, 10, 16, 18, 2**63 - 1):
        for identity in mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1:
            tasks = {
                subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
                    sample_identity=identity,
                    epoch=epoch,
                    task_schedule_seed=seed,
                )
                for epoch in range(5)
            }
            assert tasks == {0, 1, 2, 3, 4}
        for identity in mixed_tensorizer.K36_MEMBER_IDENTITIES_V1:
            tasks = {
                subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
                    sample_identity=identity,
                    epoch=epoch,
                    task_schedule_seed=seed,
                )
                for epoch in range(3)
            }
            assert tasks == {0, 3, 4}


def test_scheduler_is_order_independent_and_repeated_results_are_exact() -> None:
    forward = {
        identity: subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
            sample_identity=identity,
            epoch=23,
            task_schedule_seed=991,
        )
        for identity in subject.EXACT16_MEMBER_IDENTITIES_V1
    }
    reverse = {
        identity: subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
            sample_identity=identity,
            epoch=23,
            task_schedule_seed=991,
        )
        for identity in reversed(subject.EXACT16_MEMBER_IDENTITIES_V1)
    }
    repeated = {
        identity: subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
            sample_identity=identity,
            epoch=23,
            task_schedule_seed=991,
        )
        for identity in subject.EXACT16_MEMBER_IDENTITIES_V1
    }
    assert forward == reverse == repeated


@pytest.mark.parametrize(
    "identity",
    (
        "2R9F/K2Z",
        "2DJF/1ZB",
        "CYS_SG_SAMPLE_INDEX_000000",
        "CYS_SG_SAMPLE_INDEX_000012",
        "future/generic",
        "",
    ),
)
def test_scheduler_invalid_identity_fails_closed(identity: str) -> None:
    _assert_public_error(
        lambda: subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
            sample_identity=identity,
            epoch=0,
            task_schedule_seed=0,
        )
    )


@pytest.mark.parametrize(
    "epoch,seed",
    (
        (True, 0),
        (-1, 0),
        (0.0, 0),
        (0, True),
        (0, -1),
        (0, 2**63),
        (0, 0.0),
    ),
)
def test_scheduler_invalid_epoch_or_seed_fails_closed(epoch, seed) -> None:
    _assert_public_error(
        lambda: subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
            sample_identity="4DCD/K36",
            epoch=epoch,
            task_schedule_seed=seed,
        )
    )


@pytest.mark.parametrize("exception_type", (KeyboardInterrupt, SystemExit))
def test_process_control_exceptions_propagate(
    monkeypatch: pytest.MonkeyPatch,
    exception_type: type[BaseException],
) -> None:
    def interrupt(**unused):
        del unused
        raise exception_type()

    monkeypatch.setattr(
        subject,
        "canonical_task_id_for_covapie_current11_sample_v1",
        interrupt,
    )
    with pytest.raises(exception_type):
        subject.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
            sample_identity="CYS_SG_SAMPLE_INDEX_000001",
            epoch=0,
            task_schedule_seed=0,
        )


def test_real_exact16_collation_shapes_offsets_and_profiles(
    exact16_mixed_batch,
) -> None:
    batch = exact16_mixed_batch
    subject.validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1(batch)
    model = batch.model_input_batch
    supervision = batch.supervision
    assert batch.sample_identities == subject.EXACT16_MEMBER_IDENTITIES_V1
    assert batch.current11_batch_indices == tuple(range(11))
    assert batch.k36_batch_indices == tuple(range(11, 16))
    assert batch.scheduled_task_ids == EXPECTED_CURRENT11_EPOCH0 + EXPECTED_K36_EPOCH0
    assert len(model["names"]) == len(model["receptors"]) == 16
    assert len(model["lig_coords"]) == 468
    assert len(model["pocket_coords"]) == 3335
    assert len(supervision.pair_candidate_batch_index) == 2808
    assert model["num_lig_atoms"].shape == (16,)
    assert model["num_pocket_nodes"].shape == (16,)
    assert int(model["num_lig_atoms"].sum().item()) == 468
    assert int(model["num_pocket_nodes"].sum().item()) == 3335
    assert torch.equal(
        torch.bincount(model["lig_mask"], minlength=16),
        model["num_lig_atoms"],
    )
    assert torch.equal(
        torch.bincount(model["pocket_mask"], minlength=16),
        model["num_pocket_nodes"],
    )
    assert supervision.pair_candidate_offsets.shape == (17,)
    assert supervision.pair_candidate_offsets[0].item() == 0
    assert supervision.pair_candidate_offsets[-1].item() == 2808
    assert supervision.pair_candidate_is_positive.sum().item() == 16
    assert supervision.pair_positive_candidate_valid.tolist() == [True] * 16
    assert bool((supervision.pair_negative_count > 0).all().item())
    assert torch.equal(
        model["lig_mask"][supervision.pair_candidate_ligand_flat_index],
        supervision.pair_candidate_batch_index,
    )
    assert torch.equal(
        model["pocket_mask"][supervision.pair_candidate_pocket_flat_index],
        supervision.pair_candidate_batch_index,
    )
    assert not supervision.pre_post_geometry_component_valid_mask.any()
    assert not supervision.pre_post_geometry_component_loss_mask.any()
    assert torch.isnan(supervision.pre_post_geometry_target_angstrom).all()


def test_seed9_real_tensorization_and_collation_accepts_non_exact5_complete_batch(
    real_current11_inputs,
) -> None:
    samples = _tensorize_exact16(
        real_current11_inputs,
        epoch=0,
        task_schedule_seed=9,
    )
    mixed = (
        subject.collate_covapie_expanded_cys_sg_exact16_tensorized_samples_v1(
            samples,
            epoch=0,
            task_schedule_seed=9,
        )
    )
    subject.validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1(mixed)
    assert mixed.scheduled_task_ids[:11] == EXPECTED_CURRENT11_SEED9_EPOCH0
    assert mixed.scheduled_task_ids[11:] == EXPECTED_K36_SEED9_EPOCH0
    assert set(mixed.scheduled_task_ids) == {0, 1, 3, 4}
    assert 2 not in mixed.scheduled_task_ids
    assert mixed.current11_batch_indices == tuple(range(11))
    assert mixed.k36_batch_indices == tuple(range(11, 16))
    assert mixed.supervision.pair_candidate_is_positive.sum().item() == 16
    assert bool((mixed.supervision.pair_negative_count > 0).all().item())


def test_k36_positive_pairs_remain_c21_to_target_cys_sg(
    exact16_mixed_batch,
) -> None:
    supervision = exact16_mixed_batch.supervision
    for index in exact16_mixed_batch.k36_batch_indices:
        positive = int(
            supervision.pair_positive_candidate_index[index].item()
        )
        assert supervision.pair_candidate_ligand_local_index[positive].item() == 20
        assert (
            supervision.pair_candidate_residue_local_index[positive].item()
            == supervision.target_residue_reactive_atom_local_index[index].item()
        )
        assert (
            supervision.pair_candidate_pocket_flat_index[positive].item()
            == supervision.target_residue_reactive_atom_flat_index[index].item()
        )


def _mutated_singleton(samples, mutation: str):
    result = list(copy.deepcopy(samples))
    sample_index = 11 if mutation == "k36_task_1" else 0
    sample = result[sample_index]
    model = sample.model_input_batch
    supervision = sample.supervision
    if mutation == "wrong_task":
        supervision = replace(
            supervision,
            canonical_task_id=torch.tensor([4], dtype=torch.long),
        )
    elif mutation == "k36_task_1":
        supervision = replace(
            supervision,
            canonical_task_id=torch.tensor([1], dtype=torch.long),
        )
    elif mutation == "wrong_order_metadata":
        model["names"] = ["CYS_SG_SAMPLE_INDEX_000002"]
    elif mutation == "ligand_mask":
        model["lig_mask"][0] = 1
    elif mutation == "pocket_mask":
        model["pocket_mask"][0] = 1
    elif mutation == "ligand_count":
        model["num_lig_atoms"][0] += 1
    elif mutation == "pocket_count":
        model["num_pocket_nodes"][0] += 1
    elif mutation == "target_flat":
        supervision = replace(
            supervision,
            target_residue_reactive_atom_flat_index=(
                supervision.target_residue_reactive_atom_flat_index + 1
            ),
        )
    elif mutation == "pair_ligand_flat":
        value = supervision.pair_candidate_ligand_flat_index.clone()
        value[0] = (value[0] + 1) % int(model["num_lig_atoms"][0].item())
        supervision = replace(
            supervision, pair_candidate_ligand_flat_index=value
        )
    elif mutation == "pair_pocket_flat":
        value = supervision.pair_candidate_pocket_flat_index.clone()
        value[0] = (value[0] + 1) % int(
            model["num_pocket_nodes"][0].item()
        )
        supervision = replace(
            supervision, pair_candidate_pocket_flat_index=value
        )
    elif mutation == "pair_batch":
        value = supervision.pair_candidate_batch_index.clone()
        value[0] = 1
        supervision = replace(supervision, pair_candidate_batch_index=value)
    elif mutation == "candidate_offsets":
        value = supervision.pair_candidate_offsets.clone()
        value[-1] -= 1
        supervision = replace(supervision, pair_candidate_offsets=value)
    elif mutation == "positive_index":
        value = supervision.pair_positive_candidate_index.clone()
        value[0] = int(supervision.pair_candidate_offsets[-1].item())
        supervision = replace(
            supervision, pair_positive_candidate_index=value
        )
    else:
        raise AssertionError(mutation)
    result[sample_index] = replace(
        sample,
        model_input_batch=model,
        supervision=supervision,
    )
    return tuple(result)


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong_task",
        "k36_task_1",
        "wrong_order_metadata",
        "ligand_mask",
        "pocket_mask",
        "ligand_count",
        "pocket_count",
        "target_flat",
        "pair_ligand_flat",
        "pair_pocket_flat",
        "pair_batch",
        "candidate_offsets",
        "positive_index",
    ),
)
def test_collator_corruptions_fail_closed(exact16_samples, mutation: str) -> None:
    corrupted = _mutated_singleton(exact16_samples, mutation)
    _assert_public_error(
        lambda: subject.collate_covapie_expanded_cys_sg_exact16_tensorized_samples_v1(
            corrupted,
            epoch=0,
            task_schedule_seed=0,
        )
    )


def test_missing_duplicate_and_reordered_members_fail_closed(
    exact16_samples,
) -> None:
    _assert_public_error(
        lambda: subject.collate_covapie_expanded_cys_sg_exact16_tensorized_samples_v1(
            exact16_samples[:-1], epoch=0, task_schedule_seed=0
        )
    )
    duplicate = exact16_samples[:-1] + (exact16_samples[-2],)
    _assert_public_error(
        lambda: subject.collate_covapie_expanded_cys_sg_exact16_tensorized_samples_v1(
            duplicate, epoch=0, task_schedule_seed=0
        )
    )
    reordered = list(exact16_samples)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    _assert_public_error(
        lambda: subject.collate_covapie_expanded_cys_sg_exact16_tensorized_samples_v1(
            reordered, epoch=0, task_schedule_seed=0
        )
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "target_flat_cross_sample",
        "pair_ligand_cross_sample",
        "pair_pocket_cross_sample",
        "pair_batch_index",
        "candidate_offsets",
        "positive_index",
        "num_lig_atoms",
        "num_pocket_nodes",
    ),
)
def test_post_collation_cross_sample_and_offset_corruptions_fail_closed(
    exact16_mixed_batch,
    mutation: str,
) -> None:
    mixed = copy.deepcopy(exact16_mixed_batch)
    batch = mixed.model_input_batch
    supervision = mixed.supervision
    first_candidate = int(supervision.pair_candidate_offsets[0].item())
    if mutation == "target_flat_cross_sample":
        value = supervision.target_residue_reactive_atom_flat_index.clone()
        value[0] = int(batch["num_pocket_nodes"][0].item())
        supervision = replace(
            supervision, target_residue_reactive_atom_flat_index=value
        )
    elif mutation == "pair_ligand_cross_sample":
        value = supervision.pair_candidate_ligand_flat_index.clone()
        value[first_candidate] = int(batch["num_lig_atoms"][0].item())
        supervision = replace(
            supervision, pair_candidate_ligand_flat_index=value
        )
    elif mutation == "pair_pocket_cross_sample":
        value = supervision.pair_candidate_pocket_flat_index.clone()
        value[first_candidate] = int(batch["num_pocket_nodes"][0].item())
        supervision = replace(
            supervision, pair_candidate_pocket_flat_index=value
        )
    elif mutation == "pair_batch_index":
        value = supervision.pair_candidate_batch_index.clone()
        value[first_candidate] = 1
        supervision = replace(supervision, pair_candidate_batch_index=value)
    elif mutation == "candidate_offsets":
        value = supervision.pair_candidate_offsets.clone()
        value[1] += 1
        supervision = replace(supervision, pair_candidate_offsets=value)
    elif mutation == "positive_index":
        value = supervision.pair_positive_candidate_index.clone()
        value[0] = int(supervision.pair_candidate_offsets[1].item())
        supervision = replace(
            supervision, pair_positive_candidate_index=value
        )
    elif mutation == "num_lig_atoms":
        batch["num_lig_atoms"][0] += 1
    elif mutation == "num_pocket_nodes":
        batch["num_pocket_nodes"][0] += 1
    else:
        raise AssertionError(mutation)
    mixed = replace(
        mixed,
        model_input_batch=batch,
        supervision=supervision,
    )
    _assert_public_error(
        lambda: subject.validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1(
            mixed
        )
    )


def test_source_repository_profile_resolves_frozen_baseline_without_live_head_assumption(
    tmp_path: Path,
) -> None:
    frozen = tmp_path / "frozen_predecessor"
    subject._clone_head_v1(ROOT, frozen)
    resolved = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=frozen,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
    )
    assert resolved.stdout.strip() == FROZEN_BASELINE


def test_clean_tracked_successor_resolves_and_builds_frozen_predecessor(
    local_verification_tmp: Path,
) -> None:
    candidate_paths = (
        Path(
            "src/covalent_ext/"
            "covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_"
            "one_batch_smoke_v1.py"
        ),
        Path(
            "tests/"
            "test_covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_"
            "one_batch_smoke_v1.py"
        ),
    )
    successor = local_verification_tmp / "clean_tracked_successor"
    completed = subprocess.run(
        (
            "git",
            "clone",
            "--local",
            "--no-hardlinks",
            str(ROOT),
            str(successor),
        ),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    subprocess.run(
        (
            "git",
            "-c",
            "advice.detachedHead=false",
            "checkout",
            "--detach",
            FROZEN_BASELINE,
        ),
        cwd=successor,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for relative_path in candidate_paths:
        destination = successor / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative_path, destination)
    subprocess.run(
        ("git", "add", *(str(path) for path in candidate_paths)),
        cwd=successor,
        check=True,
    )
    subprocess.run(
        (
            "git",
            "-c",
            "user.name=CovaPIE Publication Test",
            "-c",
            "user.email=covapie-publication-test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            "temporary Exact2 tracked successor simulation",
        ),
        cwd=successor,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    successor_parent = subprocess.run(
        ("git", "rev-parse", "HEAD^"),
        cwd=successor,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ).stdout.strip()
    successor_status = subprocess.run(
        ("git", "status", "--porcelain"),
        cwd=successor,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ).stdout
    assert successor_parent == FROZEN_BASELINE
    assert successor_status == ""
    raw_fixture_root = Path(
        "data/raw/covalent_sources/covpdb/"
        "future_struct_conn_crosscheck_raw_v0"
    )
    for pdb_id in ("4dcd", "4f49", "5wkj", "6l70", "6wtt"):
        relative_fixture = raw_fixture_root / f"{pdb_id}.cif"
        destination = successor / relative_fixture
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.link(ROOT / relative_fixture, destination)
    frozen = local_verification_tmp / "successor_frozen_predecessor"
    subject._clone_head_v1(successor, frozen)
    frozen_head = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=frozen,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ).stdout.strip()
    assert frozen_head == FROZEN_BASELINE
    successor_smoke = (
        subject.run_covapie_expanded_cys_sg_mixed_profile_one_batch_smoke_v1(
            repository_root=successor,
            state_root=STATE,
            checkpoint_path=CHECKPOINT,
            device="cpu",
        )
    )
    assert successor_smoke["implementation_status"] == "passed"
    assert successor_smoke["baseline_HEAD"] == FROZEN_BASELINE
    assert successor_smoke["mixed_profile_one_batch_smoke_pass"] is True
    assert successor_smoke["geometry_head_nonzero_gradient"] is False
    assert successor_smoke["Trainer_fit"] is False
    assert successor_smoke["ready_for_training"] is False
    assert subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=frozen,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ).stdout.strip() == FROZEN_BASELINE
    assert subprocess.run(
        ("git", "status", "--porcelain"),
        cwd=frozen,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ).stdout == ""
    assert subprocess.run(
        ("git", "rev-parse", "HEAD^"),
        cwd=successor,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ).stdout.strip() == FROZEN_BASELINE
    assert subprocess.run(
        ("git", "status", "--porcelain"),
        cwd=successor,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ).stdout == ""


@pytest.fixture(scope="module")
def real_mixed_smoke_result() -> dict[str, object]:
    return subject.run_covapie_expanded_cys_sg_mixed_profile_one_batch_smoke_v1(
        repository_root=ROOT,
        state_root=STATE,
        checkpoint_path=CHECKPOINT,
        device="cpu",
    )


def test_real_dataloader_model_core_backward_and_one_optimizer_step(
    real_mixed_smoke_result: dict[str, object],
) -> None:
    result = real_mixed_smoke_result
    assert result["implementation_status"] == "passed"
    assert result["baseline_HEAD"] == "f690802c24b78ace19f9a47285ced7be73cfc55b"
    assert result["scheduler_current11_exact_parity"] is True
    assert result["scheduler_k36_valid_tasks_exact_0_3_4"] is True
    assert result["scheduler_order_independent"] is True
    assert result["scheduler_deterministic"] is True
    assert result["integration_population_exact16"] is True
    assert result["mixed_batch_sample_count"] == 16
    assert result["mixed_batch_current11_count"] == 11
    assert result["mixed_batch_k36_count"] == 5
    assert result["mixed_batch_ligand_node_count"] == 468
    assert result["mixed_batch_pocket_node_count"] == 3335
    assert result["mixed_batch_pair_candidate_count"] == 2808
    assert result["mixed_batch_positive_pair_count"] == 16
    assert result["no_cross_sample_pair_candidates"] is True
    assert result["current11_supervision_preserved_in_mixed_batch"] is True
    assert result["k36_supervision_preserved_in_mixed_batch"] is True
    assert result["K36_participated_in_actual_mixed_objective"] is True
    assert result["k36_actual_batch_indices"] == tuple(range(11, 16))
    assert result["k36_scheduled_task_ids"] == EXPECTED_K36_EPOCH0
    assert result["DataLoader_executed"] is True
    assert result["DataLoader_batch_count"] == 1
    assert result["legacy_checkpoint_SHA256"] == (
        "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
    )
    assert result["legacy_checkpoint_size_bytes"] == 17_861_341
    assert result["checkpoint_key_count"] == 122
    assert result["target_model_key_count"] == 141
    assert result["shared_exact_key_count"] == 122
    assert result["checkpoint_only_key_count"] == 0
    assert result["shape_mismatch_count"] == 0
    assert result["checkpoint_migration_exact"] is True
    assert result["model_core_forward"] is True
    for name in (
        "base_loss",
        "pair_prediction_loss",
        "geometry_loss",
        "contrastive_loss",
        "total_loss",
    ):
        assert torch.isfinite(torch.tensor(result[name]))
    assert result["geometry_loss"] == 0.0
    assert result["base_valid_sample_count"] == 16
    assert result["pair_valid_sample_count"] == 16
    assert result["geometry_valid_sample_count"] == 0
    assert result["contrastive_valid_sample_count"] == 16
    assert result["all_enabled_losses_finite"] is True
    assert result["backward"] is True
    assert result["all_existing_gradients_finite"] is True
    assert result["shared_pretrained_nonzero_gradient"] is True
    assert result["target_residue_embedding_nonzero_gradient"] is True
    assert result["role_mask_anchor_group_nonzero_gradient"] is True
    assert result["pair_head_nonzero_gradient"] is True
    assert result["geometry_head_nonzero_gradient"] is False
    assert result["optimizer_type"] == "AdamW"
    assert result["optimizer_parameter_unique"] is True
    assert result["optimizer_parameter_set_exact"] is True
    assert result["optimizer_step"] is True
    assert result["optimizer_step_count"] == 1
    assert result["shared_parameter_changed"] is True
    assert result["new_covapie_parameter_changed"] is True
    assert result["target_residue_parameter_changed"] is True
    assert result["all_parameters_finite_after_step"] is True
    assert result["PRE_geometry_supervision_authority_complete"] is False
    assert result["exact10_feature_semantics_reopened"] is False
    assert result["exact10_feature_semantics_status"] == "RESOLVED_AND_CLOSED"
    assert result["protected_sources_byte_unchanged"] is True
    assert result["checkpoint_byte_unchanged"] is True
    assert result["state_modified"] is False
    assert result["mixed_profile_batch_scheduling_tested"] is True
    assert result["mixed_profile_collation_tested"] is True
    assert result["mixed_profile_exact16_one_batch_built"] is True
    assert result["mixed_profile_losses_computed"] is True
    assert result["mixed_profile_one_batch_smoke_pass"] is True
    assert result["existing_Current11_Lightning_forward_used_for_mixed"] is False
    assert result["published_lower_level_CovaPIE_model_bridge_used"] is True
    assert result["ready_for_mixed_profile_lightning_training_bridge"] is True
    assert result["Trainer_fit"] is False
    assert result["ready_for_training"] is False
    assert result["remaining_blockers"] == (
        "EXPANDED_MIXED_PROFILE_LIGHTNING_FORWARD_NOT_IMPLEMENTED",
        "EXPANDED_MIXED_PROFILE_TRAINER_FIT_SMOKE_ABSENT",
        "PRE_GEOMETRY_SUPERVISION_AUTHORITY_NOT_ESTABLISHED",
    )


def test_import_has_no_output_side_effects() -> None:
    completed = subprocess.run(
        (
            os.environ.get("PYTHON", "python"),
            "-c",
            "import covalent_ext.covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1",
        ),
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": ".:src",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_source_delegates_current11_and_has_no_non_strict_load_or_baseexception() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    assert "canonical_task_id_for_covapie_current11_sample_v1(" in source
    assert "torch.utils.data" in source
    assert "DataLoader(" in source
    assert "strict" + "=False" not in source
    assert "except BaseException" not in source
    assert "model.forward(" not in source
