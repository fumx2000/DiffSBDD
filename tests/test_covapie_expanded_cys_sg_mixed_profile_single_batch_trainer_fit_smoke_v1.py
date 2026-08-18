from __future__ import annotations

import hashlib
import inspect
import math
import os
import subprocess
import tempfile
from dataclasses import fields, replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import pytorch_lightning as pl
import torch
from Bio.PDB import Polypeptide as _polypeptide


if not hasattr(_polypeptide, "three_to_one"):
    _polypeptide.three_to_one = lambda name: (
        _polypeptide.protein_letters_3to1[name]
    )

import lightning_modules
from covalent_ext import (
    covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
    as current11_smoke,
)
from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1
    as mixed_scheduler,
)
from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_lightning_training_bridge_v1
    as mixed_bridge,
)
from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1
    as subject,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
ERROR = (
    subject
    .COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_SINGLE_BATCH_TRAINER_FIT_SMOKE_V1_ERROR
)
EXPECTED_HEAD = "ad009ef5274b8bd2fb8c9cc56276b34a16a27db3"
EXPECTED_PUBLICATION_SUBJECT = (
    "add CovaPIE expanded Cys-SG mixed-profile single-batch Trainer.fit smoke v1"
)
EXPECTED_CHECKPOINT_SHA256 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
EXPECTED_TASKS = (3, 2, 3, 0, 2, 4, 0, 0, 4, 4, 1, 3, 0, 0, 0, 0)
EXPECTED_METRIC_KEYS = {
    "loss",
    "loss_base_diffusion",
    "loss_covalent_pair_prediction",
    "loss_pre_post_geometry",
    "loss_covalent_pair_contrastive",
}


class _Params(SimpleNamespace):
    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *arguments),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


_RUN_A = "20300102T030405Z_0123abcd"
_RUN_B = "20311231T235959Z_deadbeef"


def _synthetic_run_directory(state: Path, run_id: str) -> Path:
    return state.joinpath(*subject._EXTERNAL_VOLATILE_STATE_RUNS_PARTS_V1, run_id)


def _create_synthetic_external_run(state: Path, run_id: str) -> Path:
    run = _synthetic_run_directory(state, run_id)
    run.mkdir(parents=True)
    for index, leaf_name in enumerate(
        subject._EXTERNAL_VOLATILE_STATE_LEAF_NAMES_V1
    ):
        (run / leaf_name).write_text(
            f"external-{index}-v1\n",
            encoding="utf-8",
            newline="\n",
        )
    return run


def _synthetic_state_tree(
    tmp_path: Path,
    *,
    run_ids: tuple[str, ...] = (_RUN_A,),
) -> tuple[Path, Path]:
    state = tmp_path / "state"
    protected = state / "formal-authority/protected.json"
    protected.parent.mkdir(parents=True)
    protected.write_text("protected-v1\n", encoding="utf-8", newline="\n")
    for run_id in run_ids:
        _create_synthetic_external_run(state, run_id)
    return state, protected


def _protected_fingerprint(snapshot: dict[str, object]) -> tuple[int, str]:
    value = snapshot["protected_state_fingerprint"]
    assert type(value) is tuple
    assert len(value) == 2
    assert type(value[0]) is int
    assert type(value[1]) is str
    return value


def _external_paths(snapshot: dict[str, object]) -> tuple[str, ...]:
    return tuple(
        item["relative_path"]
        for item in snapshot["external_volatile_state_observation"]
    )


def _reasonable_version(value: object) -> bool:
    if type(value) is not str or not value or not any(char.isdigit() for char in value):
        return False
    first = value.split(".", 1)[0]
    return first.isdigit() and int(first) >= 1


def test_run_id_grammar_is_exactly_launcher_generated_contract() -> None:
    assert subject._valid_external_run_id_v1(_RUN_A) is True
    assert subject._valid_external_run_id_v1(_RUN_B) is True
    for invalid in (
        "20300230T030405Z_0123abcd",
        "20300102T246000Z_0123abcd",
        "20300102T030405Z_0123ABCD",
        "20300102T030405X_0123abcd",
        "20300102T030405Z-0123abcd",
        "20300102T030405Z_0123abc",
        "not-a-run-id",
    ):
        assert subject._valid_external_run_id_v1(invalid) is False


def test_valid_run_a_heartbeat_change_preserves_protected_state_fingerprint(
    tmp_path: Path,
) -> None:
    state, unused_protected = _synthetic_state_tree(tmp_path)
    del unused_protected
    before = subject._state_integrity_snapshot_v1(state)
    heartbeat = _synthetic_run_directory(state, _RUN_A) / "heartbeat.json"
    heartbeat.write_text("external-heartbeat-v2\n", encoding="utf-8", newline="\n")
    after = subject._state_integrity_snapshot_v1(state)
    subject._assert_protected_state_unchanged_v1(
        _protected_fingerprint(before),
        _protected_fingerprint(after),
    )
    assert before["external_volatile_state_observation"] != after[
        "external_volatile_state_observation"
    ]
    assert before["external_gpu_writer_detected"] is False


def test_valid_run_a_launch_append_preserves_protected_state(tmp_path: Path) -> None:
    state, unused_protected = _synthetic_state_tree(tmp_path)
    del unused_protected
    before = subject._state_integrity_snapshot_v1(state)
    launch = (
        _synthetic_run_directory(state, _RUN_A)
        / "launch_acceptance_checks.jsonl"
    )
    launch.write_bytes(launch.read_bytes() + b"external-append\n")
    after = subject._state_integrity_snapshot_v1(state)
    subject._assert_protected_state_unchanged_v1(
        _protected_fingerprint(before),
        _protected_fingerprint(after),
    )


def test_zero_external_runs_are_valid(tmp_path: Path) -> None:
    state, unused_protected = _synthetic_state_tree(tmp_path, run_ids=())
    del unused_protected
    snapshot = subject._state_integrity_snapshot_v1(state)
    assert _external_paths(snapshot) == ()
    assert snapshot["external_volatile_state_observation"] == ()
    assert snapshot["external_gpu_writer_detected"] is False
    assert snapshot["external_active_run_id"] is None


def test_removed_run_a_leaves_empty_runs_root_valid_and_directory_protected(
    tmp_path: Path,
) -> None:
    state, unused_protected = _synthetic_state_tree(tmp_path)
    del unused_protected
    before = subject._state_integrity_snapshot_v1(state)
    run = _synthetic_run_directory(state, _RUN_A)
    for leaf_name in subject._EXTERNAL_VOLATILE_STATE_LEAF_NAMES_V1:
        (run / leaf_name).unlink()
    run.rmdir()
    after = subject._state_integrity_snapshot_v1(state)
    assert _external_paths(after) == ()
    assert _protected_fingerprint(before) != _protected_fingerprint(after)


def test_future_run_b_works_without_source_change(
    tmp_path: Path,
) -> None:
    state, unused_protected = _synthetic_state_tree(tmp_path, run_ids=())
    del unused_protected
    _create_synthetic_external_run(state, _RUN_B)
    before = subject._state_integrity_snapshot_v1(state)
    heartbeat = _synthetic_run_directory(state, _RUN_B) / "heartbeat.json"
    heartbeat.write_text("future-heartbeat-v2\n", encoding="utf-8", newline="\n")
    after = subject._state_integrity_snapshot_v1(state)
    subject._assert_protected_state_unchanged_v1(
        _protected_fingerprint(before),
        _protected_fingerprint(after),
    )
    assert all(_RUN_B in relative for relative in _external_paths(after))


def test_same_basename_outside_exact_namespace_remains_protected(
    tmp_path: Path,
) -> None:
    state, unused_protected = _synthetic_state_tree(tmp_path)
    del unused_protected
    unrelated = state / "another-runtime/heartbeat.json"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("protected-v1\n", encoding="utf-8", newline="\n")
    before = subject._state_integrity_snapshot_v1(state)
    unrelated.write_text("protected-v2\n", encoding="utf-8", newline="\n")
    after = subject._state_integrity_snapshot_v1(state)
    with pytest.raises(subject._TrainerFitSmokeInvariantError):
        subject._assert_protected_state_unchanged_v1(
            _protected_fingerprint(before),
            _protected_fingerprint(after),
        )


def test_invalid_run_id_heartbeat_remains_protected(tmp_path: Path) -> None:
    state, unused_protected = _synthetic_state_tree(tmp_path, run_ids=())
    del unused_protected
    invalid_run = _synthetic_run_directory(state, "20300102T030405Z_NOTHEX00")
    invalid_run.mkdir(parents=True)
    heartbeat = invalid_run / "heartbeat.json"
    heartbeat.write_text("protected-v1\n", encoding="utf-8", newline="\n")
    before = subject._state_integrity_snapshot_v1(state)
    assert _external_paths(before) == ()
    heartbeat.write_text("protected-v2\n", encoding="utf-8", newline="\n")
    after = subject._state_integrity_snapshot_v1(state)
    with pytest.raises(subject._TrainerFitSmokeInvariantError):
        subject._assert_protected_state_unchanged_v1(
            _protected_fingerprint(before),
            _protected_fingerprint(after),
        )


def test_valid_run_unexpected_leaf_remains_protected(tmp_path: Path) -> None:
    state, unused_protected = _synthetic_state_tree(tmp_path)
    del unused_protected
    unexpected = _synthetic_run_directory(state, _RUN_A) / "unexpected-protected.json"
    unexpected.write_text("protected-v1\n", encoding="utf-8", newline="\n")
    before = subject._state_integrity_snapshot_v1(state)
    unexpected.write_text("protected-v2\n", encoding="utf-8", newline="\n")
    after = subject._state_integrity_snapshot_v1(state)
    with pytest.raises(subject._TrainerFitSmokeInvariantError):
        subject._assert_protected_state_unchanged_v1(
            _protected_fingerprint(before),
            _protected_fingerprint(after),
        )


def test_valid_run_symlink_heartbeat_fails_closed(
    tmp_path: Path,
) -> None:
    state, protected = _synthetic_state_tree(tmp_path)
    heartbeat = _synthetic_run_directory(state, _RUN_A) / "heartbeat.json"
    heartbeat.unlink()
    heartbeat.symlink_to(protected)
    with pytest.raises(subject._TrainerFitSmokeInvariantError):
        subject._state_integrity_snapshot_v1(state)


def test_new_protected_authority_file_fails_state_integrity(tmp_path: Path) -> None:
    state, unused_protected = _synthetic_state_tree(tmp_path)
    del unused_protected
    before = subject._state_integrity_snapshot_v1(state)
    new_authority = state / "formal-authority/new-protected.json"
    new_authority.write_text("protected-new\n", encoding="utf-8", newline="\n")
    after = subject._state_integrity_snapshot_v1(state)
    with pytest.raises(subject._TrainerFitSmokeInvariantError):
        subject._assert_protected_state_unchanged_v1(
            _protected_fingerprint(before),
            _protected_fingerprint(after),
        )


def test_removed_protected_authority_file_fails_state_integrity(
    tmp_path: Path,
) -> None:
    state, protected = _synthetic_state_tree(tmp_path)
    before = subject._state_integrity_snapshot_v1(state)
    protected.unlink()
    after = subject._state_integrity_snapshot_v1(state)
    with pytest.raises(subject._TrainerFitSmokeInvariantError):
        subject._assert_protected_state_unchanged_v1(
            _protected_fingerprint(before),
            _protected_fingerprint(after),
        )


def test_two_retained_runs_exclude_only_exact_three_leaves_each(
    tmp_path: Path,
) -> None:
    state, unused_protected = _synthetic_state_tree(
        tmp_path,
        run_ids=(_RUN_A, _RUN_B),
    )
    del unused_protected
    unrelated = _synthetic_run_directory(state, _RUN_B) / "model.pt"
    unrelated.write_bytes(b"protected-model-v1")
    before = subject._state_integrity_snapshot_v1(state)
    assert len(_external_paths(before)) == 6
    (_synthetic_run_directory(state, _RUN_A) / "heartbeat.json").write_text(
        "run-a-heartbeat-v2\n", encoding="utf-8", newline="\n"
    )
    (_synthetic_run_directory(state, _RUN_B) / "control_summary.json").write_text(
        "run-b-control-v2\n", encoding="utf-8", newline="\n"
    )
    exact_after = subject._state_integrity_snapshot_v1(state)
    subject._assert_protected_state_unchanged_v1(
        _protected_fingerprint(before),
        _protected_fingerprint(exact_after),
    )
    unrelated.write_bytes(b"protected-model-v2")
    unrelated_after = subject._state_integrity_snapshot_v1(state)
    with pytest.raises(subject._TrainerFitSmokeInvariantError):
        subject._assert_protected_state_unchanged_v1(
            _protected_fingerprint(exact_after),
            _protected_fingerprint(unrelated_after),
        )


@pytest.fixture(scope="module")
def normalized_repository(tmp_path_factory: pytest.TempPathFactory) -> Path:
    temporary = tmp_path_factory.mktemp("covapie_trainer_fit_normalized")
    normalized = temporary / "repository"
    mixed_scheduler._clone_head_v1(ROOT, normalized)
    return normalized


@pytest.fixture(scope="module")
def exact16_mixed_batch(normalized_repository: Path):
    return subject._build_real_exact16_batch_v1(
        normalized_repository_root=normalized_repository,
        repository_root=ROOT,
        state_root=STATE,
    )


@pytest.fixture(scope="module")
def positive_result() -> dict[str, object]:
    return (
        subject
        .run_covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1(
            repository_root=ROOT,
            state_root=STATE,
            checkpoint_path=CHECKPOINT,
            device="cpu",
        )
    )


@pytest.fixture(scope="module")
def publication_lifecycle_profiles(
    request: pytest.FixtureRequest,
) -> dict[str, object]:
    temporary_owner = tempfile.TemporaryDirectory(
        prefix="covapie_publication_lifecycle_", dir=ROOT.parent
    )
    request.addfinalizer(temporary_owner.cleanup)
    temporary = Path(temporary_owner.name)
    repository = temporary / "repository"
    clone = subprocess.run(
        ("git", "clone", "--local", "--no-hardlinks", str(ROOT), str(repository)),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    assert clone.returncode == 0, clone.stderr
    assert (
        _git(repository, "rev-parse", "--verify", f"{EXPECTED_HEAD}^{{commit}}")
        == EXPECTED_HEAD
    )
    _git(repository, "checkout", "--force", "-B", "main", EXPECTED_HEAD)
    _git(repository, "update-ref", "refs/remotes/origin/main", EXPECTED_HEAD)
    assert _git(repository, "branch", "--show-current") == "main"
    assert _git(repository, "rev-parse", "HEAD") == EXPECTED_HEAD
    assert _git(repository, "rev-parse", "refs/remotes/origin/main") == EXPECTED_HEAD
    assert not _git(repository, "status", "--porcelain=v1", "--untracked-files=all")
    _git(repository, "config", "user.name", "CovaPIE lifecycle test")
    _git(repository, "config", "user.email", "covapie-lifecycle@example.invalid")
    for relative in sorted(subject._CANDIDATE_RELATIVE_PATHS_V1):
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    for pdb_id in ("4dcd", "4f49", "5wkj", "6l70", "6wtt"):
        relative = Path(
            "data/raw/covalent_sources/covpdb/"
            f"future_struct_conn_crosscheck_raw_v0/{pdb_id}.cif"
        )
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(ROOT / relative, target)

    precommit = subject._git_snapshot(repository)
    _git(repository, "add", *sorted(subject._CANDIDATE_RELATIVE_PATHS_V1))
    _git(repository, "commit", "-m", EXPECTED_PUBLICATION_SUBJECT)
    publication_commit = _git(repository, "rev-parse", "HEAD")
    committed = subject._git_snapshot(repository)
    committed_full_smoke = (
        subject
        .run_covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1(
            repository_root=repository,
            state_root=STATE,
            checkpoint_path=CHECKPOINT,
            device="cpu",
        )
    )

    _git(
        repository,
        "update-ref",
        "refs/remotes/origin/main",
        publication_commit,
    )
    published = subject._git_snapshot(repository)

    marker = repository / "publication_lifecycle_descendant_marker.txt"
    marker.write_text("temporary descendant\n", encoding="utf-8", newline="\n")
    _git(repository, "add", marker.name)
    _git(repository, "commit", "-m", "temporary unrelated descendant")
    descendant_commit = _git(repository, "rev-parse", "HEAD")
    _git(
        repository,
        "update-ref",
        "refs/remotes/origin/main",
        descendant_commit,
    )
    descendant = subject._git_snapshot(repository)
    return {
        "precommit": precommit,
        "committed": committed,
        "committed_full_smoke": committed_full_smoke,
        "published": published,
        "descendant": descendant,
        "publication_commit": publication_commit,
        "descendant_commit": descendant_commit,
    }


def _patch_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        lightning_modules, "BasicMolecularMetrics", lambda *unused: object()
    )
    monkeypatch.setattr(
        lightning_modules, "MoleculeProperties", lambda: object()
    )
    monkeypatch.setattr(
        lightning_modules, "CategoricalDistribution", lambda *unused: object()
    )


def _small_compatibility_model(
    monkeypatch: pytest.MonkeyPatch,
    *,
    temporary_root: Path,
    normalized_repository: Path,
):
    _patch_metrics(monkeypatch)
    setup_data = temporary_root / "legacy_setup_data"
    setup_data.mkdir()
    carrier = STATE / subject.formal_trainer.FORMAL_CARRIER_RELATIVE_PATH_V1
    for split in ("train", "val"):
        (setup_data / f"{split}.npz").symlink_to(carrier)
    return subject._PrivateMixedTrainerFitCompatibilityModel(
        outdir=temporary_root / "output",
        dataset="crossdock",
        datadir=str(setup_data),
        batch_size=16,
        lr=1e-3,
        egnn_params=_Params(
            joint_nf=4,
            device="cpu",
            hidden_nf=8,
            n_layers=1,
            attention=False,
            tanh=False,
            norm_constant=1,
            inv_sublayers=1,
            sin_embedding=False,
            normalization_factor=1,
            aggregation_method="sum",
            edge_cutoff_ligand=None,
            edge_cutoff_pocket=None,
            edge_cutoff_interaction=None,
            reflection_equivariant=True,
            edge_embedding_dim=None,
        ),
        diffusion_params=_Params(
            diffusion_loss_type="l2",
            diffusion_steps=4,
            diffusion_noise_schedule="polynomial_2",
            diffusion_noise_precision=1e-4,
            normalize_factors=[1.0, 1.0],
        ),
        num_workers=0,
        augment_noise=0,
        augment_rotation=False,
        clip_grad=False,
        eval_epochs=1,
        eval_params=_Params(eval_batch_size=16, smiles_file=None),
        visualize_sample_epoch=1,
        visualize_chain_epoch=1,
        auxiliary_loss=False,
        loss_params=_Params(),
        mode="pocket_conditioning",
        node_histogram=[[1] * 8 for _ in range(8)],
        pocket_representation="full-atom",
        virtual_nodes=False,
        target_residue_atom_conditioning=True,
        covapie_current11_task2_runtime_enabled=True,
        covapie_repository_root=str(normalized_repository),
        covapie_state_root=str(STATE),
    )


def _parameters_before(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: parameter.detach().clone()
        for name, parameter in model.named_parameters()
    }


def _assert_parameters_unchanged(
    model: torch.nn.Module, before: dict[str, torch.Tensor]
) -> None:
    assert all(
        torch.equal(parameter.detach(), before[name])
        for name, parameter in model.named_parameters()
    )


def _synthetic_trainer_signature(sampler_parameter: str) -> inspect.Signature:
    names = (
        "accelerator",
        "devices",
        "num_nodes",
        "precision",
        "max_epochs",
        "min_epochs",
        "max_steps",
        "limit_train_batches",
        "limit_val_batches",
        "limit_test_batches",
        "num_sanity_val_steps",
        "enable_checkpointing",
        "callbacks",
        "logger",
        "gradient_clip_val",
        "accumulate_grad_batches",
        "deterministic",
        "enable_progress_bar",
        "default_root_dir",
        sampler_parameter,
    )
    return inspect.Signature((
        inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        *(
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
            )
            for name in names
        ),
    ))


def test_public_smoke_environment_baseline_and_checkpoint(
    positive_result: dict[str, object],
) -> None:
    result = positive_result
    live = subject._git_snapshot(ROOT)
    assert result["implementation_status"] == "passed"
    assert _reasonable_version(result["active_python_version"])
    assert _reasonable_version(result["active_torch_version"])
    assert _reasonable_version(result["active_lightning_version"])
    assert type(result["active_environment_matches_repository_declared"]) is bool
    assert result["declared_python_version"] == "3.10.4"
    assert result["declared_torch_version"] == "2.0.1+cu118"
    assert result["declared_lightning_version"] == "1.8.4"
    assert result["repository_branch"] == live["branch"] == "main"
    assert result["repository_lifecycle"] == live["lifecycle"]
    assert result["baseline_HEAD"] == live["baseline_HEAD"] == EXPECTED_HEAD
    assert result["repository_HEAD"] == live["HEAD"]
    assert result["repository_origin_main"] == live["origin_main"]
    assert result["repository_ahead"] == live["ahead"]
    assert result["repository_behind"] == live["behind"]
    assert result["repository_status"] == live["status"]
    assert result["repository_staged"] == live["staged"]
    assert result["candidate_publication_commit"] == live["publication_commit"]
    assert _sha256(CHECKPOINT) == EXPECTED_CHECKPOINT_SHA256
    assert result["legacy_checkpoint_SHA256_before"] == EXPECTED_CHECKPOINT_SHA256
    assert result["legacy_checkpoint_SHA256_after"] == EXPECTED_CHECKPOINT_SHA256
    fit_parameters = set(inspect.signature(pl.Trainer.fit).parameters)
    assert {"model", "datamodule", "ckpt_path"} <= fit_parameters
    assert {"model", "datamodule", "ckpt_path"} <= set(
        result["trainer_fit_signature_parameters"]
    )


def test_publication_lifecycle_precommit_and_committed_unpushed(
    publication_lifecycle_profiles: dict[str, object],
) -> None:
    profiles = publication_lifecycle_profiles
    precommit = profiles["precommit"]
    committed = profiles["committed"]
    publication_commit = profiles["publication_commit"]
    assert precommit["lifecycle"] == "precommit-untracked"
    assert precommit["baseline_HEAD"] == EXPECTED_HEAD
    assert precommit["HEAD"] == EXPECTED_HEAD
    assert precommit["origin_main"] == EXPECTED_HEAD
    assert (precommit["ahead"], precommit["behind"]) == (0, 0)
    assert precommit["publication_commit"] is None
    assert committed["lifecycle"] == "committed-unpushed"
    assert committed["HEAD"] == publication_commit
    assert committed["origin_main"] == EXPECTED_HEAD
    assert (committed["ahead"], committed["behind"]) == (1, 0)
    contract = committed["publication_contract"]
    assert contract["parent"] == EXPECTED_HEAD
    assert contract["subject"] == EXPECTED_PUBLICATION_SUBJECT
    assert contract["changed_paths"] == tuple(
        sorted(subject._CANDIDATE_RELATIVE_PATHS_V1)
    )
    assert contract["changed_statuses"] == ("A", "A")
    assert set(contract["git_modes"].values()) == {"100644"}


def test_clean_tracked_successor_runs_full_public_trainer_fit_smoke(
    publication_lifecycle_profiles: dict[str, object],
) -> None:
    result = publication_lifecycle_profiles["committed_full_smoke"]
    assert result["implementation_status"] == "passed"
    assert result["repository_lifecycle"] == "committed-unpushed"
    assert result["baseline_HEAD"] == EXPECTED_HEAD
    assert result["candidate_publication_commit"] == (
        publication_lifecycle_profiles["publication_commit"]
    )
    assert result["Trainer_fit"] is True
    assert result["trainer_fit_train_batch_count"] == 1
    assert result["trainer_fit_optimizer_step_count"] == 1
    assert result["trainer_global_step"] == 1


def test_publication_lifecycle_published_successor_and_durable_descendant(
    publication_lifecycle_profiles: dict[str, object],
) -> None:
    profiles = publication_lifecycle_profiles
    published = profiles["published"]
    descendant = profiles["descendant"]
    assert published["lifecycle"] == "published-successor"
    assert published["HEAD"] == profiles["publication_commit"]
    assert published["origin_main"] == profiles["publication_commit"]
    assert (published["ahead"], published["behind"]) == (0, 0)
    assert descendant["lifecycle"] == "published-descendant"
    assert descendant["HEAD"] == profiles["descendant_commit"]
    assert descendant["origin_main"] == profiles["descendant_commit"]
    assert descendant["publication_commit"] == profiles["publication_commit"]
    assert descendant["publication_contract"]["blobs"] == published[
        "publication_contract"
    ]["blobs"]


def test_public_smoke_model_compatibility_and_migration_are_exact(
    positive_result: dict[str, object],
) -> None:
    result = positive_result
    if result["legacy_validation_epoch_end_compat_shim_used"]:
        assert result["trainer_fit_model_is_exact_published_bridge"] is False
        assert result["smoke_only_legacy_hook_compatibility_subclass"] is True
        assert result["compatibility_subclass_parent_exact_published_bridge"] is True
        assert result["compatibility_subclass_overridden_members"] == (
            "validation_epoch_end",
            "configure_gradient_clipping",
        )
        assert "validation_epoch_end" in result[
            "direct_published_bridge_rejection_message"
        ]
    else:
        assert result["trainer_fit_model_is_exact_published_bridge"] is True
        assert result["smoke_only_legacy_hook_compatibility_subclass"] is False
        assert result["compatibility_subclass_overridden_members"] == ()
        assert result["direct_published_bridge_rejection_message"] is None
    assert result["compatibility_state_dict_exact_parity"] is True
    assert result["compatibility_named_parameter_exact_parity"] is True
    assert result["compatibility_named_buffer_exact_parity"] is True
    assert result["checkpoint_key_count"] == 122
    assert result["target_model_key_count"] == 141
    assert result["shared_exact_key_count"] == 122
    assert result["checkpoint_only_key_count"] == 0
    assert result["shape_mismatch_count"] == 0
    assert result["full_target_strict_load"] is True
    assert result["migration_missing_keys"] == ()
    assert result["migration_unexpected_keys"] == ()

    owner = subject._PrivateMixedTrainerFitCompatibilityModel
    published = (
        mixed_bridge
        .CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1
    )
    assert owner.__bases__ == (published,)
    assert set(owner.__dict__) & {
        "forward",
        "training_step",
        "transfer_batch_to_device",
        "configure_optimizers",
    } == set()
    assert owner.forward is published.forward
    assert owner.training_step is published.training_step
    assert owner.transfer_batch_to_device is published.transfer_batch_to_device
    assert owner.configure_optimizers is published.configure_optimizers


def test_direct_published_bridge_path_is_allowed_when_hooks_are_compatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    published = (
        mixed_bridge
        .CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1
    )
    monkeypatch.setattr(published, "validation_epoch_end", None)
    monkeypatch.setattr(
        published,
        "configure_gradient_clipping",
        subject._PrivateMixedTrainerFitCompatibilityModel.configure_gradient_clipping,
    )
    result = (
        subject
        .run_covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1(
            repository_root=ROOT,
            state_root=STATE,
            checkpoint_path=CHECKPOINT,
            device="cpu",
        )
    )
    assert result["Trainer_fit"] is True
    assert result["trainer_global_step"] == 1
    assert result["trainer_fit_model_is_exact_published_bridge"] is True
    assert result["legacy_validation_epoch_end_compat_shim_used"] is False
    assert result["smoke_only_legacy_hook_compatibility_subclass"] is False
    assert result["compatibility_subclass_overridden_members"] == ()
    assert result["direct_published_bridge_rejection_message"] is None


def test_public_smoke_real_batch_dataloader_and_transfer(
    positive_result: dict[str, object],
) -> None:
    result = positive_result
    assert result["mixed_batch_sample_count"] == 16
    assert result["mixed_batch_current11_count"] == 11
    assert result["mixed_batch_k36_count"] == 5
    assert result["mixed_batch_ligand_node_count"] == 468
    assert result["mixed_batch_pocket_node_count"] == 3335
    assert result["mixed_batch_pair_candidate_count"] == 2808
    assert result["mixed_batch_positive_pair_count"] == 16
    assert result["mixed_batch_task_vector"] == EXPECTED_TASKS
    assert result["k36_actual_batch_indices"] == (11, 12, 13, 14, 15)
    assert result["k36_scheduled_task_ids"] == (3, 0, 0, 0, 0)
    assert result["mixed_batch_epoch"] == 0
    assert result["mixed_batch_task_schedule_seed"] == 0
    assert result["DataLoader_dataset_length"] == 1
    assert result["DataLoader_batch_count"] == 1
    assert result["DataLoader_batch_exact_type"] is True
    assert result["DataLoader_batch_size"] == 1
    assert result["DataLoader_num_workers"] == 0
    assert result["DataLoader_sequential_sampler"] is True
    assert result["DataLoader_drop_last"] is False
    assert result["DataLoader_pin_memory"] is False
    assert result["DataLoader_persistent_workers"] is False
    assert result["before_batch_transfer_call_count"] == 1
    assert result["after_batch_transfer_call_count"] == 1
    assert result["published_transfer_method_identity_exact"] is True
    assert result["trainer_fit_device_transfer_pipeline_pass"] is True
    assert result["transferred_batch_rebuilt"] is True
    assert result["transferred_metadata_unchanged"] is True
    assert result["nested_tensors_on_model_device"] is True


def test_single_item_loader_yields_exact_batch_and_preserves_tensors(
    exact16_mixed_batch,
) -> None:
    model_tensors = {
        name: value.detach().clone()
        for name, value in exact16_mixed_batch.model_input_batch.items()
        if isinstance(value, torch.Tensor)
    }
    supervision_tensors = {
        field.name: getattr(exact16_mixed_batch.supervision, field.name)
        .detach()
        .clone()
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    }
    datamodule = subject._Exact16MixedTrainerFitDataModuleV1(
        exact16_mixed_batch
    )
    loader = datamodule.train_dataloader()
    iterator = iter(loader)
    yielded = next(iterator)
    assert yielded is exact16_mixed_batch
    with pytest.raises(StopIteration):
        next(iterator)
    assert datamodule.dataset.getitem_call_count == 1
    assert datamodule.collator.call_count == 1
    assert yielded.sample_identities is exact16_mixed_batch.sample_identities
    assert yielded.role_profiles is exact16_mixed_batch.role_profiles
    assert yielded.scheduled_task_ids is exact16_mixed_batch.scheduled_task_ids
    for name, expected in model_tensors.items():
        assert torch.equal(yielded.model_input_batch[name], expected)
    for name, expected in supervision_tensors.items():
        actual = getattr(yielded.supervision, name)
        if actual.dtype.is_floating_point:
            torch.testing.assert_close(
                actual, expected, rtol=0, atol=0, equal_nan=True
            )
        else:
            assert torch.equal(actual, expected)


def test_public_smoke_trainer_lifecycle_is_exactly_one_automatic_step(
    positive_result: dict[str, object],
) -> None:
    result = positive_result
    assert result["Trainer_fit"] is True
    assert result["single_batch_single_epoch_trainer_fit_smoke"] is True
    assert result["trainer_fit_train_batch_count"] == 1
    assert result["training_step_call_count"] == 1
    assert result["trainer_fit_optimizer_step_count"] == 1
    assert result["trainer_global_step"] == 1
    assert result["trainer_fit_current_epoch_during_batch"] == 0
    assert result["trainer_fit_device_transfer_pipeline_pass"] is True
    assert result["trainer_fit_training_step_executed"] is True
    assert result["trainer_fit_automatic_backward_executed"] is True
    assert result["automatic_backward_call_count"] == 1
    assert result["trainer_fit_optimizer_step_executed"] is True
    assert result["zero_grad_lifecycle_call_count"] == 1
    assert result["automatic_optimization"] is True
    assert "CPU" in result["trainer_accelerator"].upper()
    assert type(result["trainer_strategy"]) is str
    assert result["trainer_strategy"]
    assert result["trainer_num_devices"] == 1
    assert result["trainer_max_epochs"] == 1
    assert result["trainer_max_steps"] == 1
    assert result["trainer_limit_train_batches"] == 1
    assert result["trainer_limit_val_batches"] == 0
    assert result["trainer_limit_test_batches"] == 0
    assert result["trainer_num_sanity_val_steps"] == 0
    assert result["trainer_accumulate_grad_batches"] == 1
    assert result["trainer_checkpointing_enabled"] is False
    assert result["logger_enabled"] is False
    assert result["validation_step_call_count"] == 0
    assert result["test_step_call_count"] == 0


@pytest.mark.parametrize(
    "sampler_parameter,expected_family,expected_precision",
    (
        ("replace_sampler_ddp", "lightning-1.x", 32),
        ("use_distributed_sampler", "lightning-2.x", "32-true"),
    ),
)
def test_trainer_configuration_is_capability_based_for_both_api_families(
    tmp_path: Path,
    sampler_parameter: str,
    expected_family: str,
    expected_precision: object,
) -> None:
    signature = _synthetic_trainer_signature(sampler_parameter)
    kwargs, metadata = subject._trainer_configuration_for_signature_v1(
        signature=signature,
        callbacks=[],
        default_root_dir=tmp_path,
    )
    assert metadata == {
        "trainer_api_family": expected_family,
        "sampler_control_parameter": sampler_parameter,
        "precision_argument": expected_precision,
    }
    assert kwargs[sampler_parameter] is False
    assert kwargs["precision"] == expected_precision
    assert kwargs["accelerator"] == "cpu"
    assert kwargs["devices"] == 1
    assert kwargs["max_epochs"] == 1
    assert kwargs["max_steps"] == 1
    assert kwargs["limit_train_batches"] == 1
    assert kwargs["limit_val_batches"] == 0
    assert kwargs["limit_test_batches"] == 0
    assert kwargs["enable_checkpointing"] is False
    assert kwargs["logger"] is False
    assert kwargs["gradient_clip_val"] is None
    assert set(kwargs) <= set(signature.parameters)


def test_active_trainer_configuration_records_selected_capabilities(
    positive_result: dict[str, object],
) -> None:
    result = positive_result
    sampler = result["trainer_sampler_control_parameter"]
    assert sampler in ("replace_sampler_ddp", "use_distributed_sampler")
    if sampler == "replace_sampler_ddp":
        assert result["trainer_api_family"] == "lightning-1.x"
        assert result["trainer_precision_argument"] == 32
    else:
        assert result["trainer_api_family"] == "lightning-2.x"
        assert result["trainer_precision_argument"] == "32-true"
    selected = result["trainer_configuration_selected"]
    assert selected[sampler] is False
    assert selected["precision"] == result["trainer_precision_argument"]
    assert "callbacks" not in selected


def test_gradient_clipping_compatibility_accepts_1x_and_2x_disabled_shapes(
) -> None:
    method = subject._PrivateMixedTrainerFitCompatibilityModel.configure_gradient_clipping
    model = object()
    optimizer = object()
    assert method(model, optimizer, None, None) is None
    assert method(model, optimizer, 0, None, None) is None
    assert method(
        model,
        optimizer,
        0,
        gradient_clip_val=None,
        gradient_clip_algorithm=None,
    ) is None
    assert method(
        model,
        optimizer,
        gradient_clip_val=None,
        gradient_clip_algorithm=None,
    ) is None
    assert method(
        model,
        optimizer,
        optimizer_idx=0,
        gradient_clip_val=None,
        gradient_clip_algorithm=None,
    ) is None
    with pytest.raises(Exception):
        method(model, optimizer, 1, None, None)
    with pytest.raises(Exception):
        method(model, optimizer, optimizer_idx=None)
    with pytest.raises(Exception):
        method(model, optimizer, gradient_clip_val=1.0)


def test_callback_optimizer_hook_accepts_missing_or_zero_optimizer_index(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    normalized_repository: Path,
    exact16_mixed_batch,
) -> None:
    model = _small_compatibility_model(
        monkeypatch,
        temporary_root=tmp_path,
        normalized_repository=normalized_repository,
    )
    named_parameters = dict(model.named_parameters())
    shared_name = "ddpm.dynamics.egnn.embedding.weight"
    assert shared_name in named_parameters
    for name, parameter in named_parameters.items():
        parameter.grad = torch.ones_like(parameter)
        if name.startswith(
            "covapie_current11_auxiliary_model_v1.pre_post_geometry_head."
        ):
            parameter.grad.zero_()
    observer = subject._TrainerFitObserverV1(
        original_batch=exact16_mixed_batch,
        checkpoint_state={shared_name: named_parameters[shared_name].detach()},
    )
    optimizer = model.configure_optimizers()
    observer.on_before_optimizer_step(None, model, optimizer)
    observer.on_before_optimizer_step(None, model, optimizer, 0)
    assert observer.before_optimizer_step_count == 2
    with pytest.raises(Exception):
        observer.on_before_optimizer_step(None, model, optimizer, 1)


def test_public_smoke_loss_k36_gradient_and_parameter_evidence(
    positive_result: dict[str, object],
) -> None:
    result = positive_result
    assert set(result["training_step_metrics"]) == EXPECTED_METRIC_KEYS
    assert all(
        math.isfinite(math_value)
        for math_value in result["training_step_metrics"].values()
    )
    assert result["total_loss"] == result["training_step_metrics"]["loss"]
    assert result["base_loss"] == result["training_step_metrics"][
        "loss_base_diffusion"
    ]
    assert result["pair_prediction_loss"] == result["training_step_metrics"][
        "loss_covalent_pair_prediction"
    ]
    assert result["geometry_loss"] == 0.0
    assert result["contrastive_loss"] == result["training_step_metrics"][
        "loss_covalent_pair_contrastive"
    ]
    assert result["base_valid_sample_count"] == 16
    assert result["pair_valid_sample_count"] == 16
    assert result["geometry_valid_sample_count"] == 0
    assert result["contrastive_valid_sample_count"] == 16
    assert result["trainer_training_step_exposes_per_sample_contributions"] is False
    assert result["K36_participated_in_actual_trainer_fit_objective"] is True
    assert result["optimizer_type"] == "AdamW"
    assert result["optimizer_parameter_unique"] is True
    assert result["optimizer_parameter_set_exact"] is True
    assert result["all_existing_gradients_finite"] is True
    assert result["shared_pretrained_nonzero_gradient"] is True
    assert result["target_residue_embedding_nonzero_gradient"] is True
    assert result["role_mask_anchor_group_nonzero_gradient"] is True
    assert result["pair_head_nonzero_gradient"] is True
    assert result["geometry_head_nonzero_gradient"] is False
    assert result["shared_pretrained_parameter_changed"] is True
    assert result["new_covapie_parameter_changed"] is True
    assert result["target_residue_parameter_changed"] is True
    assert result["all_parameters_finite_after_fit"] is True


def test_public_smoke_safety_and_readiness_are_bounded(
    positive_result: dict[str, object],
) -> None:
    result = positive_result
    assert result["checkpoint_saved"] is False
    assert result["checkpoint_byte_unchanged"] is True
    assert result["published_protected_sources_byte_unchanged"] is True
    assert result["state_modified"] is False
    assert result["whole_state_fingerprint_replaced"] is True
    assert result["protected_state_entry_count"] > 0
    assert result["protected_state_SHA256_before"] == result[
        "protected_state_SHA256_after"
    ]
    assert result["protected_state_unchanged"] is True
    external_paths = result["external_volatile_state_paths"]
    assert tuple(
        item["relative_path"]
        for item in result["external_volatile_state_before"]
    ) == external_paths
    assert tuple(
        item["relative_path"]
        for item in result["external_volatile_state_after"]
    ) == external_paths
    for relative in external_paths:
        pure = Path(relative)
        assert pure.parts[:3] == subject._EXTERNAL_VOLATILE_STATE_RUNS_PARTS_V1
        assert len(pure.parts) == 5
        assert subject._valid_external_run_id_v1(pure.parts[3]) is True
        assert pure.parts[4] in subject._EXTERNAL_VOLATILE_STATE_LEAF_NAMES_V1
    assert type(result["external_volatile_state_changed_during_smoke"]) is bool
    assert result["external_volatile_state_exclusion_exact"] is True
    assert result["basename_or_glob_ignore_used"] is False
    assert result["whole_gpu_directory_ignored"] is False
    assert type(result["external_gpu_writer_detected"]) is bool
    if result["external_gpu_writer_detected"]:
        assert subject._valid_external_run_id_v1(
            result["external_active_run_id"]
        ) is True
    else:
        assert result["external_active_run_id"] is None
    assert result["external_run_id_grammar"] == (
        "YYYYMMDDTHHMMSSZ_<8 lowercase hexadecimal digits>"
    )
    assert "start_formal.sh" in result["external_ownership_rule_source"]
    assert "gpu_steady_load.py" in result["external_ownership_rule_source"]
    assert result["zero_external_run_supported"] is True
    assert result["future_run_id_supported_without_code_change"] is True
    assert result["multiple_retained_runs_supported"] is True
    assert result["state_modified_semantics"] == (
        "CovaPIE-protected state excluding explicitly declared externally-owned "
        "volatile runtime files was unchanged."
    )
    assert "state_tree_entry_count" not in result
    assert "state_tree_SHA256_before" not in result
    assert "state_tree_SHA256_after" not in result
    assert result["raw_diff_zero"] is True
    assert result["raw_tree_SHA256_before"] == result["raw_tree_SHA256_after"]
    assert result["persistent_output_created"] is False
    assert result["persistent_generated_file_count"] == 0
    assert result["temporary_trainer_root_removed"] is True
    assert result["commit_created"] is False
    assert result["push_performed"] is False
    assert result["PRE_geometry_supervision_authority_complete"] is False
    assert result["EXPANDED_MIXED_PROFILE_TRAINER_FIT_SMOKE_ABSENT"] is False
    assert result[
        "MULTI_EPOCH_MIXED_BATCH_SCHEDULE_REFRESH_NOT_YET_VALIDATED"
    ] is True
    assert result["ready_for_single_batch_trainer_fit"] is True
    assert result["single_batch_trainer_fit_pass"] is True
    assert result["ready_for_multi_epoch_schedule_refresh_design"] is True
    assert result["ready_for_training"] is False
    assert result["ready_for_gpt_review"] is True


@pytest.mark.parametrize("device", ("cuda", "gpu", "cpu:0"))
def test_wrong_device_fails_before_trainer_creation(
    monkeypatch: pytest.MonkeyPatch, device: str
) -> None:
    def forbidden_trainer(*unused, **unused_kwargs):
        raise AssertionError("wrong device created Trainer")

    monkeypatch.setattr(subject.pl, "Trainer", forbidden_trainer)
    with pytest.raises(ValueError) as error:
        subject.run_covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1(
            repository_root=ROOT,
            state_root=STATE,
            checkpoint_path=CHECKPOINT,
            device=device,
        )
    assert str(error.value) == ERROR


def test_wrong_checkpoint_identity_fails_before_trainer_creation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wrong = tmp_path / "wrong.ckpt"
    wrong.write_bytes(b"not the authorized checkpoint")

    def forbidden_trainer(*unused, **unused_kwargs):
        raise AssertionError("wrong checkpoint created Trainer")

    monkeypatch.setattr(subject.pl, "Trainer", forbidden_trainer)
    with pytest.raises(ValueError) as error:
        subject.run_covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1(
            repository_root=ROOT,
            state_root=STATE,
            checkpoint_path=wrong,
        )
    assert str(error.value) == ERROR


def test_corrupted_cross_sample_pair_fails_in_trainer_before_step(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    normalized_repository: Path,
    exact16_mixed_batch,
) -> None:
    supervision = exact16_mixed_batch.supervision
    ligand_flat = supervision.pair_candidate_ligand_flat_index.clone()
    ligand_flat[0] = int(exact16_mixed_batch.model_input_batch["num_lig_atoms"][0])
    corrupted = replace(
        exact16_mixed_batch,
        supervision=replace(
            supervision, pair_candidate_ligand_flat_index=ligand_flat
        ),
    )
    model = _small_compatibility_model(
        monkeypatch,
        temporary_root=tmp_path,
        normalized_repository=normalized_repository,
    )
    before = _parameters_before(model)
    runtime = subject._build_fit_runtime_v1(
        batch=corrupted,
        checkpoint_state={},
        default_root_dir=tmp_path / "trainer",
    )
    with pytest.raises(ValueError):
        subject._invoke_trainer_fit_v1(model=model, runtime=runtime)
    assert runtime.trainer.global_step == 0
    assert runtime.observer.before_optimizer_step_count == 0
    _assert_parameters_unchanged(model, before)


@pytest.mark.parametrize("field,value", (("epoch", 1), ("task_schedule_seed", 7)))
def test_epoch_or_seed_mismatch_fails_through_trainer_before_step(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    normalized_repository: Path,
    exact16_mixed_batch,
    field: str,
    value: int,
) -> None:
    corrupted = replace(exact16_mixed_batch, **{field: value})
    model = _small_compatibility_model(
        monkeypatch,
        temporary_root=tmp_path,
        normalized_repository=normalized_repository,
    )
    before = _parameters_before(model)
    runtime = subject._build_fit_runtime_v1(
        batch=corrupted,
        checkpoint_state={},
        default_root_dir=tmp_path / "trainer",
        validate_collated_batch=False,
        enforce_expected_schedule_observation=False,
    )
    with pytest.raises(ValueError) as error:
        subject._invoke_trainer_fit_v1(model=model, runtime=runtime)
    assert str(error.value) == (
        mixed_bridge
        .COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_LIGHTNING_TRAINING_BRIDGE_V1_ERROR
    )
    assert runtime.trainer.global_step == 0
    assert runtime.observer.train_batch_start_count == 1
    assert runtime.observer.before_backward_count == 0
    assert runtime.observer.before_optimizer_step_count == 0
    _assert_parameters_unchanged(model, before)


@pytest.mark.parametrize("exception_type", (KeyboardInterrupt, SystemExit))
def test_process_control_exception_from_training_path_propagates_exact_type(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    normalized_repository: Path,
    exact16_mixed_batch,
    exception_type: type[BaseException],
) -> None:
    model = _small_compatibility_model(
        monkeypatch,
        temporary_root=tmp_path,
        normalized_repository=normalized_repository,
    )
    before = _parameters_before(model)
    runtime = subject._build_fit_runtime_v1(
        batch=exact16_mixed_batch,
        checkpoint_state={},
        default_root_dir=tmp_path / "trainer",
    )

    def interrupt(*unused, **unused_kwargs):
        raise exception_type()

    monkeypatch.setattr(runtime.observer, "on_train_batch_start", interrupt)
    with pytest.raises(exception_type):
        subject._invoke_trainer_fit_v1(model=model, runtime=runtime)
    assert runtime.trainer.global_step == 0
    assert runtime.observer.before_backward_count == 0
    assert runtime.observer.before_optimizer_step_count == 0
    _assert_parameters_unchanged(model, before)


def test_import_has_no_stdout_stderr_or_persistent_write(tmp_path: Path) -> None:
    before = tuple(tmp_path.rglob("*"))
    completed = subprocess.run(
        (
            os.environ.get("PYTHON", "python"),
            "-W",
            "ignore::SyntaxWarning",
            "-c",
            (
                "import covalent_ext."
                "covapie_expanded_cys_sg_mixed_profile_"
                "single_batch_trainer_fit_smoke_v1"
            ),
        ),
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": f"{ROOT}:{ROOT / 'src'}",
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
    assert tuple(tmp_path.rglob("*")) == before


def test_source_is_bounded_to_trainer_orchestration_and_observation() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    assert "runtime.trainer" + ".fit(" in source
    assert "ckpt_path=None" in source
    assert "strict" + "=False" not in source
    assert "manual_backward" not in source
    assert ".backward(" not in source
    assert "optimizer" + ".step(" not in source
    assert "torch.save(" not in source
    assert ".save_checkpoint(" not in source
    assert "nn.Parameter" not in source
    assert "register_buffer" not in source
    assert "Wand" + "b" not in source
    assert "Model" + "Checkpoint" not in source
    assert "except BaseException" not in source
    assert "binary_cross_entropy" not in source
    assert "smooth_l1_loss" not in source
    assert "class EGNNDynamics" not in source
    assert "tensorize_covapie_current11_training_supervision_v1(" not in source
    assert "_data_connector" not in source
    assert "_datahook_selector" not in source
    assert '"transfer_batch_to_device_call_count"' not in source
    assert '"transfer_batch_to_device_owner_is_model"' not in source
    assert '"3.12.0"' not in source
    assert '"2.5.1+cu124"' not in source
    assert '"2.6.5"' not in source
    assert "weights_only" not in source
    assert subject._EXTERNAL_VOLATILE_STATE_RUNS_PARTS_V1 == (
        "local-tools",
        "gpu_steady_30pct_20h_v4",
        "runs",
    )
    assert subject._EXTERNAL_VOLATILE_STATE_LEAF_NAMES_V1 == (
        "heartbeat.json",
        "control_summary.json",
        "launch_acceptance_checks.jsonl",
    )
    assert _RUN_A not in source
    assert _RUN_B not in source
    assert "_EXTERNAL_VOLATILE_STATE_RELATIVE_PATHS_V1" not in source
    classifier = inspect.getsource(
        subject._validated_external_volatile_state_paths_v1
    )
    assert "fnmatch" not in classifier
    assert ".glob(" not in classifier
    assert ".rglob(" not in classifier
    for write_token in (
        '.open("w',
        '.open("a',
        '.open("x',
        ".write_text(",
        ".write_bytes(",
        ".unlink(",
        ".rename(",
        ".replace(",
        ".chmod(",
        ".truncate(",
        "os.unlink(",
        "os.rename(",
        "os.replace(",
        "os.chmod(",
    ):
        assert write_token not in source
    declared = (ROOT / "environment.yaml").read_text(encoding="utf-8")
    assert "python=3.10.4" in declared
    assert "pytorch=2.0.1=*cuda11.8*" in declared
    assert "pytorch-lightning=1.8.4" in declared
