from __future__ import annotations

import ast
import csv
from dataclasses import FrozenInstanceError, replace
import hashlib
import io
import math
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
from torch import nn

from covalent_ext import (
    covapie_current11_formal_validation4_masked_vlb_nll_v1 as subject,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11AuxiliaryModelV1,
)
from scripts import (
    check_covapie_current11_formal_validation4_masked_vlb_nll_v1
    as checker_subject,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = REPOSITORY_ROOT.parent / "covapie-state"
CACHE_ROOT = STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
PRODUCT_PATH = REPOSITORY_ROOT / (
    "src/covalent_ext/"
    "covapie_current11_formal_validation4_masked_vlb_nll_v1.py"
)
CHECKER_PATH = REPOSITORY_ROOT / (
    "scripts/check_covapie_current11_formal_validation4_masked_vlb_nll_v1.py"
)
@pytest.fixture(scope="session")
def formal_authority():
    subject._verify_bound_sources(REPOSITORY_ROOT)
    return subject._audit_formal_authority(REPOSITORY_ROOT)


@pytest.fixture(scope="session")
def validation_records():
    records = subject.structural_owner.build_covapie_batch001_positive_structural_records_v1(
        repository_root=REPOSITORY_ROOT,
        cache_root=CACHE_ROOT,
    )
    by_event = {record.canonical_event_id: record for record in records}
    return tuple(by_event[event_id] for event_id in subject.FORMAL_VALIDATION_EVENT_IDS_V1)


@pytest.fixture(scope="session")
def task_batches(validation_records):
    return subject._task_batches(validation_records)


@pytest.fixture(scope="session")
def real_result():
    return subject.run_covapie_current11_formal_validation4_masked_vlb_nll_v1(
        repository_root=REPOSITORY_ROOT,
        state_root=STATE_ROOT,
        cache_root=CACHE_ROOT,
    )


def test_exact_dual_repository_profile_source_binding_and_candidate_boundary(
    formal_authority,
):
    snapshot = checker_subject.collect_repository_git_snapshot_v1(
        repository_root=REPOSITORY_ROOT,
    )
    profile = checker_subject.classify_repository_snapshot_v1(snapshot)
    assert profile in (
        checker_subject.CANDIDATE_PRECOMMIT_PROFILE_V1,
        checker_subject.PUBLISHED_SUCCESSOR_PROFILE_V1,
    )
    if profile == checker_subject.CANDIDATE_PRECOMMIT_PROFILE_V1:
        assert snapshot.head == subject.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.origin_main == subject.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.head_parent_ids == (checker_subject.EXPECTED_PARENT_V1,)
        assert snapshot.head_tree == checker_subject.EXPECTED_TREE_V1
        assert snapshot.head_subject == checker_subject.EXPECTED_SUBJECT_V1
        assert set(snapshot.status_entries) == {
            ("??", path)
            for path in checker_subject.AUTHORIZED_CANDIDATE_FILES_V1
        }
    else:
        assert snapshot.head == snapshot.origin_main
        assert snapshot.head != subject.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.head_parent_ids == (subject.EXPECTED_BASELINE_HEAD_V1,)
        assert snapshot.head_subject == checker_subject.PUBLISHED_SUCCESSOR_SUBJECT_V1
        assert snapshot.status_entries == ()
    assert snapshot.ahead_behind == (0, 0)
    assert snapshot.tracked_modified_paths == ()
    assert snapshot.staged_modified_paths == ()
    assert len(subject._verify_bound_sources(REPOSITORY_ROOT)) == 23
    assert len(formal_authority.validation_rows) == 4


def _valid_published_successor_snapshot():
    successor_head = "1" * 40
    return checker_subject.RepositoryGitSnapshotV1(
        branch="main",
        head=successor_head,
        origin_main=successor_head,
        ahead_behind=(0, 0),
        tracked_modified_paths=(),
        staged_modified_paths=(),
        status_entries=(),
        head_parent_ids=(subject.EXPECTED_BASELINE_HEAD_V1,),
        head_subject=checker_subject.PUBLISHED_SUCCESSOR_SUBJECT_V1,
        head_tree="2" * 40,
        head_changed_entries=tuple(
            ("A", path)
            for path in checker_subject.AUTHORIZED_CANDIDATE_FILES_V1
        ),
        head_candidate_path_modes=tuple(
            (path, "100644")
            for path in checker_subject.AUTHORIZED_CANDIDATE_FILES_V1
        ),
    )


def _assert_repository_profile_fails_closed(snapshot):
    with pytest.raises(ValueError) as captured:
        checker_subject.classify_repository_snapshot_v1(snapshot)
    assert str(captured.value) == checker_subject.CHECKER_ERROR_V1


def test_published_successor_profile_positive_simulation_passes():
    assert checker_subject.classify_repository_snapshot_v1(
        _valid_published_successor_snapshot()
    ) == checker_subject.PUBLISHED_SUCCESSOR_PROFILE_V1


def test_published_successor_wrong_parent_simulation_fails_closed():
    _assert_repository_profile_fails_closed(replace(
        _valid_published_successor_snapshot(),
        head_parent_ids=("3" * 40,),
    ))


def test_published_successor_wrong_subject_simulation_fails_closed():
    _assert_repository_profile_fails_closed(replace(
        _valid_published_successor_snapshot(),
        head_subject="wrong publication subject",
    ))


def test_published_successor_extra_changed_path_simulation_fails_closed():
    valid = _valid_published_successor_snapshot()
    _assert_repository_profile_fails_closed(replace(
        valid,
        head_changed_entries=valid.head_changed_entries + (("A", "extra.py"),),
    ))


def test_published_successor_executable_mode_simulation_fails_closed():
    valid = _valid_published_successor_snapshot()
    modes = list(valid.head_candidate_path_modes)
    modes[0] = (modes[0][0], "100755")
    _assert_repository_profile_fails_closed(replace(
        valid, head_candidate_path_modes=tuple(modes),
    ))


def test_published_successor_extra_untracked_path_simulation_fails_closed():
    _assert_repository_profile_fails_closed(replace(
        _valid_published_successor_snapshot(),
        status_entries=(("??", "extra.txt"),),
    ))


def test_published_successor_wrong_change_type_simulation_fails_closed():
    valid = _valid_published_successor_snapshot()
    changes = list(valid.head_changed_entries)
    changes[1] = ("M", changes[1][1])
    _assert_repository_profile_fails_closed(replace(
        valid, head_changed_entries=tuple(changes),
    ))


def test_source_sha_mismatch_fails_in_stable_public_namespace(monkeypatch):
    first_path, unused = subject.BOUND_SOURCE_AND_ARTIFACT_SHA256_V1[0]
    monkeypatch.setattr(
        subject,
        "BOUND_SOURCE_AND_ARTIFACT_SHA256_V1",
        ((first_path, "0" * 64),),
    )
    with pytest.raises(ValueError) as captured:
        subject.run_covapie_current11_formal_validation4_masked_vlb_nll_v1(
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
        )
    assert str(captured.value) == subject.FORMAL_VALIDATION4_MASKED_VLB_NLL_ERROR_V1


def test_keyboard_interrupt_and_system_exit_are_not_normalized(monkeypatch):
    monkeypatch.setattr(subject, "_verify_bound_sources", lambda unused: ())
    monkeypatch.setattr(subject, "_run_impl", lambda **unused: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        subject.run_covapie_current11_formal_validation4_masked_vlb_nll_v1(
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
        )
    monkeypatch.setattr(subject, "_run_impl", lambda **unused: (_ for _ in ()).throw(SystemExit(2)))
    with pytest.raises(SystemExit):
        subject.run_covapie_current11_formal_validation4_masked_vlb_nll_v1(
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
        )


def test_exact_formal_validation_and_leakage_identities(formal_authority):
    assert tuple(row[0] for row in formal_authority.validation_rows) == subject.FORMAL_VALIDATION_EVENT_IDS_V1
    assert tuple(row[0] for row in formal_authority.train_rows) == subject.FORMAL_TRAIN_EVENT_IDS_V1
    assert [row[1] for row in formal_authority.validation_rows] == ["LN5", "LN5", "PX5", "PX5"]
    validation_groups = {row[2] for row in formal_authority.validation_rows}
    train_groups = {row[2] for row in formal_authority.train_rows}
    assert validation_groups.isdisjoint(train_groups)
    assert not any(":NDU:" in row[0] for row in formal_authority.validation_rows)


def test_formal_authority_has_no_training_admission_or_non_target_member():
    payload = (REPOSITORY_ROOT / subject.FORMAL_SPLIT_RELATIVE_PATH_V1).read_text(encoding="utf-8")
    rows = tuple(csv.DictReader(io.StringIO(payload)))
    validation = set(subject.FORMAL_VALIDATION_EVENT_IDS_V1)
    assert all(row["sample_training_admitted"] == "false" for row in rows)
    assert all(row["model_training_activation_authorized"] == "false" for row in rows)
    registry = subject.json.loads(
        (REPOSITORY_ROOT / subject.FORMAL_REGISTRY_RELATIVE_PATH_V1).read_text(encoding="utf-8")
    )
    non_target = {
        event
        for component in registry["components"]
        for event in component["non_target_component_event_ids"]
    }
    assert validation.isdisjoint(non_target)


def test_exact_profiles_roles_atoms_and_applicable_task_domain(validation_records):
    observed = []
    for record in validation_records:
        observed.append((
            record.ligand_component_id,
            subject._profile_name(record),
            len(record.ligand_retained_heavy_atoms),
            len(record.scaffold_retained_local_indices),
            len(record.linker_retained_local_indices),
            len(record.warhead_retained_local_indices),
            record.applicable_canonical_task_ids,
        ))
    assert observed == [
        ("LN5", "STRICT_LINKER_PRESENT", 13, 5, 3, 5, (0, 1, 2, 3, 4)),
        ("LN5", "STRICT_LINKER_PRESENT", 13, 5, 3, 5, (0, 1, 2, 3, 4)),
        ("PX5", "DIRECT_ATTACHMENT_OPTIONAL_LINKER", 17, 9, 0, 8, (0, 3, 4)),
        ("PX5", "DIRECT_ATTACHMENT_OPTIONAL_LINKER", 17, 9, 0, 8, (0, 3, 4)),
    ]


def test_exact_16_event_task_pairs_and_no_schedule_dependency(task_batches):
    pairs = tuple(
        (event, task_id)
        for task_id, preview in task_batches
        for event in preview.sample_identities
    )
    assert len(pairs) == 16
    assert tuple(len(preview.sample_identities) for unused, preview in task_batches) == (4, 2, 2, 4, 4)
    assert all(preview.epoch == 0 for unused, preview in task_batches)
    assert all(
        preview.task_schedule_seed == subject.VALIDATION_TENSORIZATION_SENTINEL_SEED_V1
        for unused, preview in task_batches
    )
    assert all(preview.canonical_task_ids == (task_id,) * len(preview.sample_identities) for task_id, preview in task_batches)


def test_exact_validation_root_seeds_and_stable_child_seed_oracle():
    assert subject.FORMAL_VALIDATION_ROOT_SEEDS_V1 == (
        5475773696358545661,
        4502185737657980518,
        4471455199196535378,
        4502278954409160509,
    )
    event = subject.FORMAL_VALIDATION_EVENT_IDS_V1[0]
    root = subject.FORMAL_VALIDATION_ROOT_SEEDS_V1[0]
    observed = subject.derive_formal_validation_child_seed_v1(
        canonical_event_id=event, canonical_task_id=0,
        root_validation_seed=root, stochastic_stage="MAIN_NOISE",
    )
    payload = b"\0".join((
        b"COVAPIE_FORMAL_VALIDATION4_MASKED_VLB_NLL_V1\0",
        event.encode("ascii"), b"0", str(root).encode("ascii"), b"MAIN_NOISE",
    ))
    expected = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & (2**63 - 1)
    assert observed == expected
    stages = {
        subject.derive_formal_validation_child_seed_v1(
            canonical_event_id=event, canonical_task_id=0,
            root_validation_seed=root, stochastic_stage=stage,
        )
        for stage in ("MAIN_TIMESTEP", "MAIN_NOISE", "T0_NOISE")
    }
    assert len(stages) == 3


def test_rng_order_and_batch_packing_invariance(validation_records):
    root = subject.FORMAL_VALIDATION_ROOT_SEEDS_V1[1]

    def keyed(records):
        result = {}
        for record in records:
            generated = record.warhead_retained_local_indices
            draw = subject.build_formal_validation_keyed_draw_v1(
                canonical_event_id=record.canonical_event_id,
                canonical_task_id=0,
                root_validation_seed=root,
                generated_local_indices=generated,
                ligand_atom_count=len(record.ligand_retained_heavy_atoms),
                feature_dimension=13,
                timesteps=500,
            )
            result[record.canonical_event_id] = draw
        return result

    normal = keyed(validation_records)
    reversed_order = keyed(tuple(reversed(validation_records)))
    assert normal.keys() == reversed_order.keys()
    for event, left in normal.items():
        right = reversed_order[event]
        assert left.main_timestep_int == right.main_timestep_int
        assert torch.equal(left.main_generated_epsilon, right.main_generated_epsilon)
        assert torch.equal(left.t0_generated_epsilon, right.t0_generated_epsilon)


def test_exact_generated_fixed_counts_and_coordinate_dimensions(task_batches):
    expected = {
        ("LN5", 0): (5, 8, 15),
        ("LN5", 1): (8, 5, 24),
        ("LN5", 2): (10, 3, 30),
        ("LN5", 3): (5, 8, 15),
        ("LN5", 4): (13, 0, 36),
        ("PX5", 0): (8, 9, 24),
        ("PX5", 3): (9, 8, 27),
        ("PX5", 4): (17, 0, 48),
    }
    for task_id, preview in task_batches:
        supervision = preview.supervision
        ligand_mask = preview.model_input_batch["lig_mask"]
        for sample, event in enumerate(preview.sample_identities):
            component = event.split(":")[-2]
            active = int(supervision.ligand_base_generation_mask[ligand_mask == sample].sum().item())
            total = int(preview.model_input_batch["num_lig_atoms"][sample].item())
            dimension = subject.coordinate_dimension_for_masked_likelihood_v1(
                generated_atom_count=active, all_generated=task_id == 4,
            )
            assert (active, total - active, dimension) == expected[(component, task_id)]


class _NoisingStub:
    n_dims = 3

    @staticmethod
    def alpha(gamma, target):
        return torch.full((len(gamma), 1), 2.0, dtype=target.dtype)

    @staticmethod
    def sigma(gamma, target):
        return torch.full((len(gamma), 1), 3.0, dtype=target.dtype)


def test_partial_fixed_node_cleanliness_and_fixed_epsilon_perturbation_invariance():
    clean = torch.arange(28, dtype=torch.float32).reshape(4, 7)
    pocket = torch.zeros((2, 7), dtype=torch.float32)
    ligand_mask = torch.tensor([0, 0, 1, 1], dtype=torch.long)
    pocket_mask = torch.tensor([0, 1], dtype=torch.long)
    active = torch.tensor([True, False, True, False])
    epsilon = torch.ones_like(clean)
    perturbed = epsilon.clone()
    perturbed[~active] = 100000.0
    left, unused = subject._assemble_noised(
        ddpm=_NoisingStub(), clean_ligand=clean, clean_pocket=pocket,
        ligand_mask=ligand_mask, pocket_mask=pocket_mask, active=active,
        gamma=torch.zeros((2, 1)), epsilon=epsilon, task_id=0,
    )
    right, unused = subject._assemble_noised(
        ddpm=_NoisingStub(), clean_ligand=clean, clean_pocket=pocket,
        ligand_mask=ligand_mask, pocket_mask=pocket_mask, active=active,
        gamma=torch.zeros((2, 1)), epsilon=perturbed, task_id=0,
    )
    assert torch.equal(left[~active], clean[~active])
    assert torch.equal(right[~active], clean[~active])
    assert torch.equal(left, right)
    prediction = torch.zeros_like(clean)
    error_left = subject.masked_active_epsilon_error_v1(
        sampled_epsilon=epsilon, predicted_epsilon=prediction,
        active_mask=active, ligand_batch_index=ligand_mask, batch_size=2,
    )
    error_right = subject.masked_active_epsilon_error_v1(
        sampled_epsilon=perturbed, predicted_epsilon=prediction,
        active_mask=active, ligand_batch_index=ligand_mask, batch_size=2,
    )
    assert torch.equal(error_left, error_right)


def test_independent_main_active_error_snr_sign_and_scaling_oracle():
    epsilon = torch.tensor([[1.0, 2.0], [9.0, 9.0], [3.0, 4.0]])
    prediction = torch.tensor([[0.0, 0.0], [-50.0, 20.0], [1.0, 1.0]])
    active = torch.tensor([True, False, True])
    membership = torch.tensor([0, 0, 1], dtype=torch.long)
    observed = subject.masked_active_epsilon_error_v1(
        sampled_epsilon=epsilon, predicted_epsilon=prediction,
        active_mask=active, ligand_batch_index=membership, batch_size=2,
    )
    expected = torch.tensor([1.0**2 + 2.0**2, (3.0 - 1.0)**2 + (4.0 - 1.0)**2])
    assert torch.equal(observed, expected)
    gamma_s = torch.tensor([[-1.0], [-0.5]])
    gamma_t = torch.tensor([[0.0], [0.5]])
    snr, loss = subject.historical_eval_loss_t_v1(
        active_epsilon_error=observed, gamma_s=gamma_s,
        gamma_t=gamma_t, timesteps=500,
    )
    oracle_snr = 1.0 - torch.exp(-(gamma_s[:, 0] - gamma_t[:, 0]))
    oracle_loss = -500.0 * 0.5 * oracle_snr * expected
    assert torch.allclose(snr, oracle_snr)
    assert torch.allclose(loss, oracle_loss)
    assert bool((snr < 0).all().item())


def test_independent_t0_coordinate_generated_row_reduction_oracle():
    epsilon = torch.tensor([
        [1.0, 2.0, 3.0, 100.0],
        [90.0, 80.0, 70.0, 60.0],
        [4.0, 5.0, 6.0, 100.0],
    ])
    prediction = torch.zeros_like(epsilon)
    active = torch.tensor([True, False, True])
    membership = torch.tensor([0, 0, 1], dtype=torch.long)
    observed = subject.masked_t0_coordinate_loss_v1(
        sampled_epsilon=epsilon, predicted_epsilon=prediction,
        active_mask=active, ligand_batch_index=membership,
        batch_size=2, n_dims=3,
    )
    expected = torch.tensor([
        0.5 * (1.0 + 4.0 + 9.0),
        0.5 * (16.0 + 25.0 + 36.0),
    ])
    assert torch.equal(observed, expected)


class _CategoricalStub:
    n_dims = 3
    norm_values = (1.0, 4.0)
    norm_biases = (None, 0.0)

    @staticmethod
    def sigma(gamma, target_tensor):
        return torch.sqrt(torch.sigmoid(gamma)).reshape(len(gamma), 1)

    @staticmethod
    def cdf_standard_gaussian(value):
        return 0.5 * (1.0 + torch.erf(value / math.sqrt(2.0)))


def test_independent_t0_categorical_generated_row_reference_oracle():
    one_hot = torch.tensor([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ])
    normalized = one_hot / 4.0
    z = torch.cat((torch.zeros((3, 3)), torch.tensor([
        [0.20, 0.01, -0.02],
        [9.00, -9.00, 3.00],
        [-0.01, 0.02, 0.19],
    ])), dim=1)
    gamma = torch.tensor([[-2.0], [-1.0]])
    active = torch.tensor([True, False, True])
    membership = torch.tensor([0, 0, 1], dtype=torch.long)
    observed = subject._masked_categorical_loss(
        ddpm=_CategoricalStub(), normalized_true_one_hot=normalized,
        z_ligand=z, gamma_0=gamma, active=active,
        ligand_mask=membership, batch_size=2,
    )
    oracle_rows = []
    for row in (0, 2):
        sample = int(membership[row])
        sigma = math.sqrt(torch.sigmoid(gamma[sample, 0]).item()) * 4.0
        estimated = z[row, 3:] * 4.0
        centered = estimated - 1.0
        high = 0.5 * (1.0 + torch.erf((centered + 0.5) / sigma / math.sqrt(2.0)))
        low = 0.5 * (1.0 + torch.erf((centered - 0.5) / sigma / math.sqrt(2.0)))
        logs = torch.log(high - low + 1.0e-10)
        log_probs = logs - torch.logsumexp(logs, dim=0)
        oracle_rows.append(-log_probs[one_hot[row].bool()][0])
    expected = torch.stack(oracle_rows)
    assert torch.allclose(observed, expected, atol=1e-7, rtol=1e-7)


class _KlStub:
    n_dims = 3

    @staticmethod
    def gamma(t):
        return torch.zeros_like(t)

    @staticmethod
    def alpha(gamma, target):
        return torch.full((len(gamma), 1), math.sqrt(0.5), dtype=target.dtype)

    @staticmethod
    def sigma(gamma, target):
        return torch.full((len(gamma), 1), math.sqrt(0.5), dtype=target.dtype)

    @staticmethod
    def gaussian_KL(mu_norm, q_sigma, p_sigma, d):
        return d * torch.log(p_sigma / q_sigma) + 0.5 * (
            d * q_sigma.square() + mu_norm
        ) / p_sigma.square() - 0.5 * d


def test_independent_masked_kl_dimension_and_fixed_row_exclusion_oracle():
    clean = torch.tensor([
        [1.0, 2.0, 3.0, 1.0, 0.0],
        [50.0, 60.0, 70.0, 0.0, 1.0],
        [2.0, 3.0, 4.0, 0.0, 1.0],
    ])
    membership = torch.tensor([0, 0, 1], dtype=torch.long)
    active = torch.tensor([True, False, True])
    dimensions = torch.tensor([3, 6], dtype=torch.long)
    observed = subject._masked_kl_prior(
        ddpm=_KlStub(), clean_ligand=clean, ligand_mask=membership,
        active=active, coordinate_dimensions=dimensions, batch_size=2,
    )
    alpha = math.sqrt(0.5)
    sigma = math.sqrt(0.5)
    expected = []
    for row, dimension in ((0, 3), (2, 6)):
        mu_x_norm = float((alpha * clean[row, :3]).square().sum())
        mu_h_norm = float((alpha * clean[row, 3:]).square().sum())
        kl_x = dimension * math.log(1.0 / sigma) + 0.5 * (dimension * sigma**2 + mu_x_norm) - 0.5 * dimension
        kl_h = math.log(1.0 / sigma) + 0.5 * (sigma**2 + mu_h_norm) - 0.5
        expected.append(kl_x + kl_h)
    assert torch.allclose(observed, torch.tensor(expected), atol=1e-6, rtol=1e-6)
    perturbed = clean.clone()
    perturbed[1] *= 10000.0
    assert torch.equal(observed, subject._masked_kl_prior(
        ddpm=_KlStub(), clean_ligand=perturbed, ligand_mask=membership,
        active=active, coordinate_dimensions=dimensions, batch_size=2,
    ))


def test_independent_gaussian_constant_jacobian_and_primary_sign_oracle():
    gamma_0 = torch.tensor([-2.0, 0.5])
    dimensions = torch.tensor([15, 36])
    constant = subject.masked_gaussian_coordinate_constant_loss_v1(
        gamma_0=gamma_0, coordinate_dimensions=dimensions,
    )
    expected_constant = dimensions * (0.5 * gamma_0 + 0.5 * math.log(2.0 * math.pi))
    assert torch.allclose(constant, expected_constant)
    delta = subject.masked_normalization_delta_log_px_v1(
        coordinate_dimensions=dimensions, coordinate_normalization=2.0,
    )
    assert torch.allclose(delta, -dimensions.float() * math.log(2.0))
    components = [torch.tensor([float(index), float(index + 1)]) for index in range(1, 7)]
    primary = subject.compose_masked_conditional_vlb_nll_v1(
        loss_t=components[0], loss_0_x=components[1], loss_0_h=components[2],
        negative_log_coordinate_constant=components[3], kl_prior=components[4],
        masked_delta_log_px=components[5],
    )
    expected = sum(components[:5]) - components[5]
    assert torch.equal(primary, expected)


def test_pair_candidate_domain_and_validation_reducers_ignore_training_masks(task_batches):
    task_id, preview = task_batches[0]
    assert task_id == 0
    supervision = preview.supervision
    counts = tuple(int(supervision.pair_candidate_offsets[i + 1] - supervision.pair_candidate_offsets[i]) for i in range(4))
    assert counts == (78, 78, 102, 102)
    assert int(supervision.pair_candidate_is_positive.sum().item()) == 4
    assert not bool(supervision.sample_training_admitted.any().item())
    assert not bool(supervision.pair_head_candidate_loss_mask.any().item())
    assert not bool(supervision.pair_contrastive_sample_loss_mask.any().item())
    logits = torch.zeros(len(supervision.pair_candidate_batch_index))
    geometry = torch.ones((len(logits), 2))
    output = SimpleNamespace(
        pair_logits=logits,
        pre_post_geometry_predictions_angstrom=geometry,
    )
    reduced = subject._validation_auxiliary_reducers(
        model_output=output, supervision=supervision,
    )
    assert len(reduced) == 4
    for sample, (pair_bce, post_loss, prediction, target, contrastive) in enumerate(reduced):
        assert pair_bce.item() == pytest.approx(math.log(2.0))
        assert contrastive.item() == pytest.approx(math.log(counts[sample]))
        assert prediction.item() == 1.0
        delta = abs(1.0 - target.item())
        oracle_post = 0.5 * delta**2 if delta < 1.0 else delta - 0.5
        assert post_loss.item() == pytest.approx(oracle_post)
    assert supervision.pre_post_geometry_component_valid_mask.tolist() == [[False, True]] * 4
    assert not bool(supervision.pre_post_geometry_component_loss_mask.any().item())


class _DummyDdpm(nn.Module):
    def __init__(self):
        super().__init__()
        self.dynamics = nn.Linear(1, 1)


class _DummyOuter(nn.Module):
    def __init__(self):
        super().__init__()
        self.ddpm = _DummyDdpm()
        self.covapie_current11_auxiliary_model_v1 = CovapieCurrent11AuxiliaryModelV1(joint_nf=2)


def test_formal_module_api_fails_closed_on_training_mode():
    model = _DummyOuter()
    model.eval()
    assert subject.validate_formal_evaluation_module_state_v1(model=model)
    model.train()
    with pytest.raises(ValueError) as captured:
        subject.validate_formal_evaluation_module_state_v1(model=model)
    assert str(captured.value) == subject.FORMAL_VALIDATION4_MASKED_VLB_NLL_ERROR_V1


def test_real_64_estimate_execution_structure_and_finiteness(real_result):
    result = real_result
    assert result.implementation_status == "passed"
    assert result.primary_metric_name == "MASKED_CONDITIONAL_VLB_NLL_V1"
    assert result.formal_validation_event_count == 4
    assert result.formal_validation_task_event_count == 16
    assert result.formal_validation_estimate_count == 64
    assert len(result.per_estimate_rows) == 64
    assert len(result.per_event_task_seed_means) == 16
    assert len(result.per_event_means) == 4
    assert result.formal_validation_task_slice_evaluation_count == 20
    assert result.main_dynamics_task_slice_call_count == 20
    assert result.t0_dynamics_task_slice_call_count == 20
    assert result.total_dynamics_task_slice_call_count == 40
    assert result.actual_functional_dynamics_call_count == 40
    assert result.all_applicable_primary_metrics_finite
    assert result.all_applicable_auxiliary_metrics_finite
    assert all(math.isfinite(row.masked_conditional_vlb_nll) for row in result.per_estimate_rows)


def test_real_eval_modes_no_grad_parameter_buffer_grad_and_checkpoint_safety(real_result):
    assert real_result.model_eval_mode_verified
    assert real_result.ddpm_eval_mode_verified
    assert real_result.auxiliary_eval_mode_verified
    assert real_result.gradient_recording_disabled
    assert not real_result.metric_tensors_require_grad
    assert real_result.parameters_unchanged
    assert real_result.buffers_unchanged
    assert real_result.gradient_states_unchanged
    assert real_result.checkpoint_unchanged
    assert real_result.checkpoint_sha256_before == subject.CHECKPOINT_SHA256_V1
    assert real_result.checkpoint_sha256_after == subject.CHECKPOINT_SHA256_V1


def test_real_fixed_clean_timestep_t0_coordinate_and_target_indicator_contract(real_result):
    assert real_result.partial_tasks_fixed_ligand_clean
    assert real_result.partial_tasks_coordinate_dimension_exact
    assert real_result.task4_zero_com_coordinate_dimension_exact
    assert real_result.main_timestep_domain_exact_1_to_T
    assert real_result.separate_t0_forward_verified
    assert real_result.target_cys_sg_same_indicator_main_and_t0
    for row in real_result.per_estimate_rows:
        assert 1 <= row.main_timestep_int <= 500
        assert row.target_cys_sg_indicator_count == 1
        if row.canonical_task_id == 4:
            assert row.fixed_atom_count == 0
            assert row.coordinate_dimension == 3 * (row.generated_atom_count - 1)
        else:
            assert row.fixed_atom_count > 0
            assert row.fixed_ligand_clean_main and row.fixed_ligand_clean_t0
            assert row.coordinate_dimension == 3 * row.generated_atom_count


def test_real_pair_post_contrastive_and_pre_absence_contract(real_result):
    assert real_result.PRE_geometry_valid_count == 0
    assert real_result.POST_geometry_valid_count == 64
    assert not real_result.production_geometry_weight_finalized
    expected_candidates = {"LN5": 78, "PX5": 102}
    for row in real_result.per_estimate_rows:
        assert not row.PRE_geometry_valid
        assert row.pair_candidate_count == expected_candidates[row.ligand_component_id]
        assert row.pair_BCE >= 0 and math.isfinite(row.pair_BCE)
        assert row.POST_geometry_loss >= 0 and math.isfinite(row.POST_geometry_loss)
        assert row.POST_geometry_target_angstrom > 0
        assert row.pair_contrastive_loss >= 0 and math.isfinite(row.pair_contrastive_loss)


def test_primary_excludes_node_prior_and_task4_diagnostic_sign(real_result):
    assert not real_result.primary_includes_log_pN
    assert real_result.task4_historical_joint_nll_diagnostic_available
    task4_count = 0
    for row in real_result.per_estimate_rows:
        if row.canonical_task_id == 4:
            task4_count += 1
            assert row.task4_log_pN is not None
            assert row.task4_historical_joint_nll_with_node_prior_diagnostic == pytest.approx(
                row.masked_conditional_vlb_nll - row.task4_log_pN,
                abs=1e-5, rel=1e-6,
            )
        else:
            assert row.task4_log_pN is None
            assert row.task4_historical_joint_nll_with_node_prior_diagnostic is None
    assert task4_count == 16


def test_seed_then_task_then_event_and_profile_aggregation_oracles(real_result):
    task_oracle = {}
    for event in subject.FORMAL_VALIDATION_EVENT_IDS_V1:
        tasks = sorted({row.canonical_task_id for row in real_result.per_estimate_rows if row.canonical_event_id == event})
        for task in tasks:
            values = [
                row.masked_conditional_vlb_nll
                for row in real_result.per_estimate_rows
                if row.canonical_event_id == event and row.canonical_task_id == task
            ]
            assert len(values) == 4
            task_oracle[(event, task)] = math.fsum(values) / 4
    observed_task = {
        (row.canonical_event_id, row.canonical_task_id): row.masked_conditional_vlb_nll
        for row in real_result.per_event_task_seed_means
    }
    assert observed_task == pytest.approx(task_oracle)
    event_oracle = {}
    for event in subject.FORMAL_VALIDATION_EVENT_IDS_V1:
        values = [value for (candidate, unused), value in task_oracle.items() if candidate == event]
        event_oracle[event] = math.fsum(values) / len(values)
    observed_event = {row.canonical_event_id: row.masked_conditional_vlb_nll for row in real_result.per_event_means}
    assert observed_event == pytest.approx(event_oracle)
    assert real_result.event_macro_masked_conditional_vlb_nll == pytest.approx(
        math.fsum(event_oracle.values()) / 4
    )
    assert real_result.micro_masked_conditional_vlb_nll == pytest.approx(
        math.fsum(task_oracle.values()) / 16
    )
    profile_values = dict(real_result.profile_means)
    assert real_result.profile_balanced_masked_conditional_vlb_nll == pytest.approx(
        0.5 * (profile_values["STRICT_LINKER_PRESENT"] + profile_values["DIRECT_ATTACHMENT_OPTIONAL_LINKER"])
    )


def test_task4_historical_boundary_semantics(real_result):
    rows = [row for row in real_result.per_estimate_rows if row.canonical_task_id == 4]
    assert len(rows) == 16
    assert all(row.generated_atom_count in (13, 17) for row in rows)
    assert all(row.fixed_atom_count == 0 for row in rows)
    assert all(row.coordinate_dimension in (36, 48) for row in rows)
    assert real_result.main_dynamics_task_slice_call_count == real_result.t0_dynamics_task_slice_call_count
    assert all(row.task4_log_pN is not None for row in rows)


def test_result_schema_is_immutable_and_exposes_required_fields(real_result):
    estimate_names = {field.name for field in subject.fields(subject.FormalValidationEstimateV1)}
    assert {
        "canonical_event_id", "canonical_task_id", "root_validation_seed",
        "main_timestep_int", "main_active_epsilon_error", "SNR_weight",
        "loss_t", "t0_coordinate_loss", "t0_categorical_loss",
        "negative_log_coordinate_constant", "kl_prior", "masked_delta_log_px",
        "masked_conditional_vlb_nll", "pair_BCE", "POST_geometry_loss",
        "pair_contrastive_loss", "PRE_geometry_valid",
    } <= estimate_names
    with pytest.raises(FrozenInstanceError):
        real_result.per_estimate_rows[0].canonical_task_id = 99
    with pytest.raises(FrozenInstanceError):
        real_result.implementation_status = "changed"


def test_readiness_markers_are_precise_and_do_not_claim_training_or_lightning_integration(real_result):
    assert real_result.ready_for_lightning_validation_integration
    assert real_result.ready_for_gpt_review
    assert not real_result.full_training_authorized
    assert not real_result.training_performed
    assert not real_result.Trainer_used
    assert not real_result.optimizer_created
    assert not real_result.optimizer_step_performed
    assert not real_result.backward_performed
    assert real_result.CPU_only
    assert not real_result.GPU_used
    assert not real_result.network_used
    assert not real_result.reaction_family_authority_consumed


def _call_name(node: ast.Call) -> str:
    function = node.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        parts = [function.attr]
        value = function.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            parts.append(value.id)
        return ".".join(reversed(parts))
    return ""


def test_product_ast_has_no_training_optimizer_trainer_write_network_or_git_operation():
    tree = ast.parse(PRODUCT_PATH.read_text(encoding="utf-8"))
    calls = [_call_name(node) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    forbidden_suffixes = (
        ".backward", "autograd.grad", ".zero_grad", ".optimizer.step",
        ".step", "Trainer", "Trainer.fit", "Trainer.validate", "torch.save",
        "np.save", ".write_text", ".write_bytes", "requests.get",
        "requests.post", "subprocess.run", "subprocess.call", "os.system",
    )
    assert not any(
        call == suffix or call.endswith(suffix)
        for call in calls for suffix in forbidden_suffixes
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node) == "open" and len(node.args) >= 2:
            assert not isinstance(node.args[1], ast.Constant) or node.args[1].value not in {"w", "wb", "a", "ab", "x", "xb"}
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imports.isdisjoint({"requests", "urllib", "subprocess", "git"})


def test_product_does_not_call_training_only_formal_paths_or_toggle_train_mode():
    tree = ast.parse(PRODUCT_PATH.read_text(encoding="utf-8"))
    calls = {_call_name(node) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    assert not any(name.endswith("run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1") for name in calls)
    assert not any(name.endswith("CovapieCurrent11TrainingLigandPocketDDPM.forward") for name in calls)
    assert not any(name.endswith("train") for name in calls)
    assert any(name.endswith("run_covapie_current11_functional_dynamics_with_hidden_v1") for name in calls)


def test_import_has_no_output_side_effect_and_no_generated_repository_artifact():
    assert checker_subject.classify_repository_profile_v1(
        repository_root=REPOSITORY_ROOT,
    ) in (
        checker_subject.CANDIDATE_PRECOMMIT_PROFILE_V1,
        checker_subject.PUBLISHED_SUCCESSOR_PROFILE_V1,
    )
    forbidden = tuple(
        path for path in REPOSITORY_ROOT.rglob("*")
        if path.is_file() and path.suffix in {".tmp", ".part"}
    )
    assert forbidden == ()
