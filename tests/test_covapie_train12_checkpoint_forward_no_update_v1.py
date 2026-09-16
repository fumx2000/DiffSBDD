"""Bounded train12 checkpoint-forward/no-update consumer validation.

The real checkpoint path is deliberately opt-in and is not exercised by the
implementation/preflight phase that publishes this test candidate.  Ordinary
tests cover fixed source identity, adapter-first imports, the train12 epoch-0
CPU carrier, reusable no-update helpers, and independent coordinate oracles.
"""

from __future__ import annotations

import ast
import contextlib
from dataclasses import fields
import hashlib
import importlib.util
import inspect
import io
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Callable, Iterator, Mapping
from unittest import mock

import pytest
import torch


TASK_ID_V1 = "validate_covapie_train12_checkpoint_forward_no_update_v1"
REAL_FORWARD_OPT_IN_V1 = (
    "COVAPIE_RUN_TRAIN12_CHECKPOINT_FORWARD_NO_UPDATE"
)
EXPECTED_REPOSITORY_BASELINE_V1 = (
    "b7c519ed9f6cb14f47d30fbabf2edac34d2398c8"
)
EXPECTED_CHECKPOINT_SIZE_BYTES_V1 = 17_861_341
EXPECTED_CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
MODEL_INITIALIZATION_SEED_V1 = 20_260_821
DIFFUSION_FORWARD_SEED_V1 = 11_030_037
DETERMINISM_ABSOLUTE_TOLERANCE_V1 = 1.0e-7
DETERMINISM_RELATIVE_TOLERANCE_V1 = 1.0e-7
COORDINATE_ABSOLUTE_TOLERANCE_V1 = 1.0e-5
COORDINATE_RELATIVE_TOLERANCE_V1 = 1.3e-6
POST_COMPONENT_V1 = 1
EXPECTED_EPOCH0_TASK_IDS_V1 = (4, 4, 2, 0, 4, 4, 0, 0, 4, 4, 3, 1)
EXPECTED_EPOCH0_HIDDEN_POST_ELIGIBLE_V1 = (0, 1, 2, 3, 4, 11)

CANONICAL_EXACT5_V1 = (
    (0, "warhead_only", "A", (2,)),
    (1, "linker_plus_warhead", "B", (1, 2)),
    (2, "scaffold_plus_warhead", "B2", (0, 2)),
    (3, "scaffold_only", "B3", (0,)),
    (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
)


def _required_canonical_directory_v1(environment_name: str) -> Path:
    configured = os.environ.get(environment_name)
    assert configured is not None, environment_name
    path = Path(configured)
    assert path.is_absolute(), environment_name
    metadata = path.lstat()
    assert stat.S_ISDIR(metadata.st_mode) and not path.is_symlink()
    assert path.resolve(strict=True) == path
    return path


# The external candidate never infers repository/state roots from __file__.
ROOT = _required_canonical_directory_v1("COVAPIE_TEST_REPOSITORY_ROOT")
STATE_ROOT = _required_canonical_directory_v1("COVAPIE_TEST_STATE_ROOT")
CACHE_ROOT = _required_canonical_directory_v1("COVAPIE_TEST_CACHE_ROOT")
assert CACHE_ROOT == STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"


# Fixed baseline identities: path, bytes, SHA256, Git blob OID.  A future
# tracked successor may advance HEAD, but these consumed sources may not drift.
BOUND_SOURCE_IDENTITIES_V1 = (
    (
        "src/covalent_ext/covapie_train12_hidden_post_forward_adapter_v1.py",
        16_701,
        "3d4ee01e0a2db0f64d22c5922b07506cea7133c8c442a08cc9ffa00f921ef294",
        "185369aba7555b93600fbb7a37aafed2eb91589f",
    ),
    (
        "src/covalent_ext/covapie_train12_cpu_batch_composer_v1.py",
        32_288,
        "4f67c695f50ca9d6e8cec30fd6a163db10fb05fd44647b2a189b9aeda6719722",
        "0b4a456592887e686ef984a862d703581b6056d7",
    ),
    (
        "tests/test_covapie_train10_checkpoint_forward_no_update_v1.py",
        127_015,
        "d602987f0a4d76799427213e62205cb70505064c93e126fd3c8a3bae80b46b79",
        "576f5afaf2e64059a8bf3a620aefb88d6eb7b0f5",
    ),
    (
        "tests/test_covapie_batch001_checkpoint_forward_no_update_v1.py",
        51_136,
        "2bac1568af875b200829f9854497a07587339c2587b501bf3d54ef7720bc2bdb",
        "1314ac24d6675e4a1c2b4271cae5b4404b000be6",
    ),
    (
        "src/covalent_ext/covapie_current11_checkpoint_migration_v1.py",
        14_953,
        "fc36fb23844e6e5d2be2e1e43fcd0afe580d8b86faacca31bd69b8fe70f75ef3",
        "b9d83c4c25a802cd918cf8d2757e519fec66b7cd",
    ),
    (
        "src/covalent_ext/"
        "covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1.py",
        29_303,
        "e92d68fc7126eb2c3e20341ad1a3ae3dd48509533761694c482edca01d70df61",
        "d87f97e1c2fbe4043f7179258d6890fb2889fdc0",
    ),
    (
        "src/covalent_ext/checkpoint_compatible_model_instantiation.py",
        39_301,
        "dfd9957465460f66bc08ac12c264040fae0e2a300eb7359929c780dfa85d3024",
        "ae4cc3e924adfaafa7b75e02e889c36395fefd49",
    ),
    (
        "src/covalent_ext/diffsbdd_model_instantiation.py",
        12_536,
        "5bc98bad19bad27a4260ce01d68194fbfe46096bd3955b7ff5e5efa4c70d5613",
        "1155162b532fc90c781ae9b5354820b2276f8ea0",
    ),
    (
        "src/covalent_ext/"
        "covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1.py",
        51_490,
        "3f19d39148f374d14744fa714a2e7d648a37099168d539c14e7e2320d390ec21",
        "ff74ee8407f67741d725fe335f85e55d94f3145c",
    ),
    (
        "src/covalent_ext/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py",
        64_861,
        "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241",
        "61c057af51fcb0bc9dd4ab83f917e1eece2be799",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_manifest.json",
        6_395,
        "24cb60ca4f080a72e8c60aef63d105d82ec2f432eecc9b90f3341f52576bb6e0",
        "1c0fc43040df00d903e8395c62571ce9dc711217",
    ),
    (
        "configs/crossdock_fullatom_joint.yml",
        1_435,
        "155ac1b9dba8af71946e1f4e17ca9176bd05acba0a6132e50b6929f2dbf3b0ea",
        "e40443bdadd15f783a5fa3f1975b29c30d0da7b9",
    ),
    (
        "data/derived/covalent_small/"
        "checkpoint_original_config_instantiation_design_v0/"
        "checkpoint_original_config_preview.json",
        2_187,
        "6960de3ebb1fa408b6188dac5fdade5e2b1fc1505408ca9142b1748e305d7f4a",
        "011b3cbc19b078d1176bc7a40f9da0862e906ccf",
    ),
)


def _sha256_v1(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file_identity_v1(path: Path) -> tuple[int, str]:
    metadata = path.lstat()
    assert stat.S_ISREG(metadata.st_mode) and not path.is_symlink()
    return metadata.st_size, _sha256_v1(path)


def _git_bytes_v1(*arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    return completed.stdout


def _verify_bound_sources_v1() -> tuple[tuple[str, int, str, str], ...]:
    ancestry = subprocess.run(
        (
            "git",
            "merge-base",
            "--is-ancestor",
            EXPECTED_REPOSITORY_BASELINE_V1,
            "HEAD",
        ),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert ancestry.returncode == 0, "fixed baseline is not an ancestor of HEAD"
    observed = []
    for relative, expected_size, expected_sha, expected_blob in (
        BOUND_SOURCE_IDENTITIES_V1
    ):
        path = ROOT / relative
        size, sha = _safe_file_identity_v1(path)
        assert (size, sha) == (expected_size, expected_sha), relative
        blob = _git_bytes_v1("hash-object", "--", relative).decode().strip()
        assert blob == expected_blob, relative
        assert _git_bytes_v1("cat-file", "blob", expected_blob) == path.read_bytes()
        observed.append((relative, size, sha, blob))
    return tuple(observed)


def _evidence_v1(message: str) -> None:
    print(f"COVAPIE_EVIDENCE {message}", flush=True)


def _load_published_train10_tools_v1() -> object:
    """Load fixed helper definitions only; never invoke an old test or runner."""

    relative = "tests/test_covapie_train10_checkpoint_forward_no_update_v1.py"
    expected = next(
        row for row in BOUND_SOURCE_IDENTITIES_V1 if row[0] == relative
    )
    path = ROOT / relative
    assert _safe_file_identity_v1(path) == expected[1:3]
    name = "_covapie_published_train10_forward_test_tools_for_train12_v1"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        specification.loader.exec_module(module)
    assert stdout.getvalue() == "" and stderr.getvalue() == ""
    assert Path(module.__file__).resolve(strict=True) == path
    for helper in (
        "_compare_replay_value_v1",
        "_new_call_stats_v1",
        "_transparent_observer_v1",
        "_capture_model_snapshot_v1",
        "_assert_model_snapshot_unchanged_v1",
        "_hidden_post_eligibility_oracle_v1",
        "_carrier_measurements_v1",
        "_validate_forward_output_v1",
        "_assert_train10_centering_and_fixed_node_contract_v1",
        "_synthetic_centering_contract_fixture_v1",
        "_install_no_training_tripwires_v1",
        "_patch_observer_v1",
        "_clone_transport_v1",
        "_call_count_view_v1",
        "_report_primary_failure_v1",
    ):
        assert callable(getattr(module, helper))
    # Fixed-ten validators/factories and every test_* remain uncalled.
    return module


def _fingerprint_supported_v1(value: object) -> str:
    return _load_published_train10_tools_v1()._fingerprint_value_v1(value)


def _prepared_snapshot_v1(prepared: object, composer: object) -> tuple[object, ...]:
    valid = composer._validate_prepared(prepared)
    return (
        id(valid),
        valid._seal,
        valid._repo,
        valid._state,
        valid._cache,
        valid._groups,
        valid._gjj_profile,
        valid._helper_bindings,
        composer.train10._prepared_seal_v1(valid._train10),
        composer.ready2._seal(valid._ready2),
        valid.sample_identities,
        valid.canonical_event_ids,
        valid.leakage_group_ids,
        valid.ready_for_training,
        valid.feature_semantics_audit_required_later,
        valid.step12d_is_only_smoke_legality_check,
    )


def _carrier_fingerprint_v1(carrier: object) -> str:
    """Fingerprint supported tensors/metadata; source objects stay owner-validated."""

    source_blocks = tuple(
        (
            block.source_kind,
            block.sample_start,
            block.sample_end,
            block.native_owner,
            block.sample_identities,
            block.canonical_event_ids,
            block.leakage_group_ids,
            block.formal_splits,
            block.scheduled_task_ids,
            block.scheduler_binding,
            block.native_source_bindings,
            block.core_snapshot,
            block.supervision_snapshot,
            block.offsets_slpq,
            block.payload_sha256,
        )
        for block in carrier.source_audit_blocks
    )
    supported = (
        carrier.schema_version,
        carrier.sample_identities,
        carrier.canonical_event_ids,
        carrier.leakage_group_ids,
        carrier.formal_splits,
        carrier.batch_positions,
        carrier.role_profiles,
        carrier.scheduled_task_ids,
        carrier.epoch,
        carrier.task_schedule_seed,
        carrier.model_input_batch,
        carrier.supervision,
        source_blocks,
        carrier.prepared_source_seal,
        carrier.direct_helper_bindings,
        carrier.training_session_active,
        carrier.model_consumer_integrated,
        carrier.datamodule_integrated,
        carrier.trainer_integrated,
        carrier.real_model_executed,
        carrier.parameter_update_performed,
        carrier.ready_for_training,
        carrier.feature_semantics_audit_required_later,
        carrier.step12d_is_only_smoke_legality_check,
        carrier.payload_sha256,
    )
    return _fingerprint_supported_v1(supported)


def _hidden_post_eligibility_oracle_v1(carrier: object) -> tuple[int, ...]:
    # The published helper is an independent scalar rule and does not call the
    # production effective-mask implementation.  It loops over actual length.
    return _load_published_train10_tools_v1()._hidden_post_eligibility_oracle_v1(
        carrier
    )


def _assert_train12_carrier_contract_v1(
    carrier: object, prepared: object, composer: object
) -> dict[str, object]:
    from covalent_ext.covapie_current11_training_tensorizer_v1 import (
        CANONICAL_TASKS_V1,
    )

    assert type(carrier) is composer.CovapieTrain12CpuEpochBatchV1
    assert composer.validate_covapie_train12_cpu_epoch_batch_v1(carrier, prepared)
    assert carrier.epoch == 0 and carrier.task_schedule_seed == 0
    assert tuple(CANONICAL_TASKS_V1) == CANONICAL_EXACT5_V1
    assert len(carrier.sample_identities) == 12
    assert carrier.sample_identities == composer.TRAIN12_SAMPLE_IDENTITIES_V1
    assert carrier.canonical_event_ids == composer.TRAIN12_CANONICAL_EVENT_IDS_V1
    assert len(set(carrier.leakage_group_ids)) == 5
    assert carrier.scheduled_task_ids == EXPECTED_EPOCH0_TASK_IDS_V1
    assert set(carrier.scheduled_task_ids) == set(range(5))
    assert tuple(carrier.supervision.canonical_task_id.tolist()) == (
        carrier.scheduled_task_ids
    )
    assert set(carrier.model_input_batch) == set(
        composer.train10._MODEL_CORE_FIELDS_V1
    )
    assert carrier.model_input_batch["lig_one_hot"].shape[1] == 10
    assert carrier.model_input_batch["pocket_one_hot"].shape[1] == 10
    assert tuple(block.sample_start for block in carrier.source_audit_blocks) == (
        0,
        10,
        11,
    )
    assert tuple(block.sample_end for block in carrier.source_audit_blocks) == (
        10,
        11,
        12,
    )
    assert carrier.source_audit_blocks[1].sample_identities == (
        carrier.sample_identities[10],
    )
    assert carrier.source_audit_blocks[2].sample_identities == (
        carrier.sample_identities[11],
    )
    assert carrier.scheduled_task_ids[10] == 3  # JUG is scaffold_only/B3.
    assert carrier.scheduled_task_ids[11] == 1  # GJJ is linker_plus_warhead.
    assert carrier.training_session_active is False
    assert carrier.model_consumer_integrated is False
    assert carrier.datamodule_integrated is False
    assert carrier.trainer_integrated is False
    assert carrier.real_model_executed is False
    assert carrier.parameter_update_performed is False
    assert carrier.ready_for_training is False
    assert carrier.feature_semantics_audit_required_later is True
    assert carrier.step12d_is_only_smoke_legality_check is True

    supervision = carrier.supervision
    assert not bool(
        supervision.pre_post_geometry_component_valid_mask[:, 0].any().item()
    )
    assert not bool(
        supervision.pre_post_geometry_component_loss_mask[:, 0].any().item()
    )
    assert bool(
        torch.isnan(supervision.pre_post_geometry_target_angstrom[:, 0])
        .all()
        .item()
    )
    assert supervision.pre_post_geometry_component_valid_mask[10].tolist() == [
        False,
        False,
    ]
    assert supervision.pre_post_geometry_component_loss_mask[10].tolist() == [
        False,
        False,
    ]
    assert torch.isnan(
        supervision.pre_post_geometry_target_angstrom[10]
    ).all()
    assert supervision.pre_post_geometry_component_valid_mask[11].tolist() == [
        False,
        True,
    ]
    assert supervision.pre_post_geometry_component_loss_mask[11].tolist() == [
        False,
        True,
    ]
    assert torch.isfinite(
        supervision.pre_post_geometry_target_angstrom[11, POST_COMPONENT_V1]
    )

    ligand_mask = carrier.model_input_batch["lig_mask"]
    pocket_mask = carrier.model_input_batch["pocket_mask"]
    assert int(ligand_mask.min()) == int(pocket_mask.min()) == 0
    assert int(ligand_mask.max()) == int(pocket_mask.max()) == 11
    assert tuple(supervision.pair_candidate_offsets.shape) == (13,)
    assert bool(supervision.pair_positive_candidate_valid.all().item())
    for sample in range(12):
        positive = int(supervision.pair_positive_candidate_index[sample].item())
        assert int(supervision.pair_candidate_offsets[sample]) <= positive
        assert positive < int(supervision.pair_candidate_offsets[sample + 1])
        assert int(supervision.pair_candidate_batch_index[positive]) == sample
        ligand_flat = int(
            supervision.pair_candidate_ligand_flat_index[positive].item()
        )
        pocket_flat = int(
            supervision.pair_candidate_pocket_flat_index[positive].item()
        )
        assert int(ligand_mask[ligand_flat]) == sample
        assert int(pocket_mask[pocket_flat]) == sample
        assert pocket_flat == int(
            supervision.target_residue_reactive_atom_flat_index[sample]
        )

    eligible = _hidden_post_eligibility_oracle_v1(carrier)
    assert eligible == EXPECTED_EPOCH0_HIDDEN_POST_ELIGIBLE_V1
    assert 10 not in eligible and 11 in eligible
    first_source_task_c = 0
    second_source_task_c = 0
    for sample, task in enumerate(carrier.scheduled_task_ids[:10]):
        if task != 4:
            continue
        rows = ligand_mask == sample
        fixed = supervision.ligand_base_fixed_mask[rows, 0]
        seed_valid = bool(
            supervision.ligand_minimal_seed_or_anchor_valid[sample].item()
        )
        seed_count = int(
            supervision.ligand_minimal_seed_or_anchor_mask[rows].sum().item()
        )
        assert int(fixed.sum().item()) == 0
        if sample < 5:
            first_source_task_c += 1
            assert seed_valid is False and seed_count == 0
        else:
            second_source_task_c += 1
            assert seed_valid is True and seed_count > 0
    assert first_source_task_c > 0 and second_source_task_c > 0

    measurements = _load_published_train10_tools_v1()._carrier_measurements_v1(
        carrier
    )
    assert measurements["tasks"] == EXPECTED_EPOCH0_TASK_IDS_V1
    assert measurements["hidden_post_eligible"] == eligible
    return measurements


def _instantiate_train12_model_v1(
    *, checkpoint: dict[str, object], runtime_root: Path
) -> object:
    """Apply only batch-size/class/explicit train12 differences to owners."""

    import constants

    dependencies = _load_real_path_dependencies_v1()
    adapter = dependencies["adapter"]
    compatible_owner = dependencies["compatible_owner"]
    constructor_owner = dependencies["constructor_owner"]

    legacy = checkpoint["legacy_constructor"]
    preview_result = compatible_owner.load_config_preview_v0(
        ROOT / compatible_owner.CONFIG_PREVIEW_PATH
    )
    assert preview_result["config_preview_loaded"] is True
    compatible = compatible_owner.build_checkpoint_compatible_config_v0(
        preview_result["preview"],
        ROOT / compatible_owner.BEST_CONFIG_CANDIDATE_PATH,
    )
    assert compatible["compatible_config_built"] is True
    config = compatible_owner._constructor_config_from_compatible_config(
        compatible,
        constructor_owner._DATASET_NAME_V1,
        "cpu",
        node_histogram=legacy["node_histogram"],
    )
    assert config["egnn_params"] == dict(legacy["egnn_params"], device="cpu")
    assert config["diffusion_params"] == legacy["diffusion_params"]
    assert config["eval_params"] == legacy["eval_params"]
    assert config["loss_params"] == legacy["loss_params"]
    for key in (
        "lr",
        "num_workers",
        "augment_noise",
        "augment_rotation",
        "eval_epochs",
        "visualize_sample_epoch",
        "visualize_chain_epoch",
        "auxiliary_loss",
        "mode",
        "pocket_representation",
        "virtual_nodes",
    ):
        assert config[key] == legacy[key], key
    assert config["node_histogram"] == legacy["node_histogram"]
    assert config["clip_grad"] is False and legacy["clip_grad"] is True

    legacy_setup = runtime_root / "legacy_setup_data"
    legacy_setup.mkdir(mode=0o700)
    config.update(
        {
            "outdir": runtime_root / "model_output_not_persisted",
            "datadir": str(legacy_setup),
            "batch_size": 12,
        }
    )
    kwargs = constructor_owner._constructor_kwargs(config)
    kwargs.update(
        {
            "target_residue_atom_conditioning": True,
            "covapie_current11_task2_runtime_enabled": True,
            "covapie_repository_root": str(ROOT),
            "covapie_state_root": str(STATE_ROOT),
            "covapie_current11_training_enabled": True,
            "covapie_current11_task_schedule_seed": 0,
            "covapie_current11_pair_contrastive_temperature": 1.0,
            "covapie_train12_hidden_post_forward_enabled": True,
        }
    )
    assert "covapie_train10_hidden_post_forward_enabled" not in kwargs
    assert "covapie_batch001_hidden_post_forward_enabled" not in kwargs
    assert "covapie_current11_loss_weights" not in kwargs

    torch.random.default_generator.manual_seed(MODEL_INITIALIZATION_SEED_V1)
    dataset_name = config["dataset"]
    previous = constants.dataset_params.get(dataset_name)
    constants.dataset_params[dataset_name] = (
        compatible_owner._temporary_10d_dataset_info()
    )
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            model = (
                adapter.CovapieTrain12HiddenPostForwardLigandPocketDDPMV1(
                    **kwargs
                )
            )
    finally:
        if previous is None:
            constants.dataset_params.pop(dataset_name, None)
        else:
            constants.dataset_params[dataset_name] = previous
    return model.to(torch.device("cpu"))


def _load_real_path_dependencies_v1() -> dict[str, object]:
    """Import every real-path owner through the adapter-first compat entry."""

    # This is intentionally the first CovaPIE real-owner import in this helper.
    from covalent_ext import (
        covapie_train12_hidden_post_forward_adapter_v1 as adapter,
    )
    from Bio.PDB import Polypeptide

    assert hasattr(Polypeptide, "three_to_one")
    from covalent_ext import (
        checkpoint_compatible_model_instantiation as compatible_owner,
    )
    from covalent_ext import (
        covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
        as checkpoint_locator,
    )
    from covalent_ext import (
        covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
        as constructor_owner,
    )
    from covalent_ext import (
        covapie_current11_checkpoint_migration_v1 as migration_owner,
    )
    from covalent_ext import (
        covapie_current11_training_lightning_module_v1 as training_owner,
    )
    from covalent_ext import (
        covapie_current11_training_tensorizer_v1 as tensorizer_owner,
    )
    from covalent_ext import (
        covapie_train12_cpu_batch_composer_v1 as composer_owner,
    )
    from covalent_ext import diffsbdd_model_instantiation as kwargs_owner

    return {
        "adapter": adapter,
        "checkpoint_locator": checkpoint_locator,
        "compatible_owner": compatible_owner,
        "constructor_owner": constructor_owner,
        "migration_owner": migration_owner,
        "training_owner": training_owner,
        "tensorizer_owner": tensorizer_owner,
        "composer_owner": composer_owner,
        "kwargs_owner": kwargs_owner,
    }


def _contains_identity_v1(value: object, target: object) -> bool:
    if value is target:
        return True
    if isinstance(value, Mapping):
        return any(
            _contains_identity_v1(key, target)
            or _contains_identity_v1(item, target)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list, set, frozenset)):
        return any(_contains_identity_v1(item, target) for item in value)
    return False


def _run_real_checkpoint_validation_v1() -> None:
    """One load, one model/migration/carrier/bind, two same-RNG forwards."""

    tools = _load_published_train10_tools_v1()
    phase = "dependency_import"
    observations = {
        name: tools._new_call_stats_v1()
        for name in (
            "checkpoint_deserialization",
            "model_initialization",
            "migration",
            "composer_prepare",
            "carrier_build",
            "prepared_bind",
            "model_forward",
            "transport",
            "role_encoding",
            "diffusion_bridge",
            "functional_dynamics",
            "egnn",
            "atom_encoder",
            "residue_encoder",
            "anchor_encoder",
            "pair_encoder",
            "auxiliary",
            "production_loss",
            "secondary_tensorization",
        )
    }
    rng_before_validation = torch.random.get_rng_state().clone()
    try:
        dependencies = _load_real_path_dependencies_v1()
        adapter = dependencies["adapter"]
        checkpoint_locator = dependencies["checkpoint_locator"]
        compatible_owner = dependencies["compatible_owner"]
        migration_owner = dependencies["migration_owner"]
        training_owner = dependencies["training_owner"]
        tensorizer_owner = dependencies["tensorizer_owner"]
        composer_owner = dependencies["composer_owner"]

        phase = "fixed_source_verification"
        fixed_sources_before = _verify_bound_sources_v1()
        adapter_sources_before = (
            adapter.verify_covapie_train12_hidden_post_forward_adapter_sources_v1(
                repository_root=ROOT
            )
        )
        assert checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1 == (
            compatible_owner.CHECKPOINT_PATH
        )
        assert not checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1.is_absolute()
        checkpoint_path = ROOT / checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1

        phase = "checkpoint_identity_before_deserialization"
        checkpoint_size, checkpoint_sha = _safe_file_identity_v1(checkpoint_path)
        assert checkpoint_size == EXPECTED_CHECKPOINT_SIZE_BYTES_V1
        assert checkpoint_sha == EXPECTED_CHECKPOINT_SHA256_V1
        assert checkpoint_size == (
            migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1
        )
        assert checkpoint_sha == (
            migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1
        )
        _evidence_v1(
            "checkpoint_identity=PASS "
            f"relative_path={checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1} "
            f"bytes={checkpoint_size} sha256={checkpoint_sha} deserialized=false"
        )

        with contextlib.ExitStack() as stack:
            phase = "install_no_training_tripwires"
            tripwire_calls = tools._install_no_training_tripwires_v1(stack)
            tools._patch_observer_v1(
                stack,
                owner=migration_owner.torch,
                attribute="load",
                stats=observations["checkpoint_deserialization"],
                projector=lambda _args, _kwargs, result: {
                    "payload_type": type(result).__name__
                },
            )
            tools._patch_observer_v1(
                stack,
                owner=adapter.CovapieTrain12HiddenPostForwardLigandPocketDDPMV1,
                attribute="__init__",
                stats=observations["model_initialization"],
                projector=lambda _args, kwargs, _result: {
                    "batch_size": kwargs.get("batch_size"),
                    "train12_enabled": kwargs.get(
                        "covapie_train12_hidden_post_forward_enabled"
                    ),
                },
            )

            phase = "checkpoint_load"
            checkpoint = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
                checkpoint_path=checkpoint_path
            )
            assert observations["checkpoint_deserialization"]["requested"] == 1
            assert observations["checkpoint_deserialization"]["returned"] == 1
            checkpoint_state = checkpoint["state_dict"]
            assert checkpoint["checkpoint_size_bytes"] == checkpoint_size
            assert checkpoint["checkpoint_sha256"] == checkpoint_sha
            assert checkpoint["checkpoint_state_dict_key_count"] == len(
                checkpoint_state
            )
            _evidence_v1(
                "checkpoint_load=PASS "
                f"payload_type={checkpoint['checkpoint_payload_type']} "
                f"actual_legacy_state_keys={len(checkpoint_state)} loader_calls=1"
            )

            phase = "runtime_directory_creation"
            runtime_root = Path(
                tempfile.mkdtemp(
                    prefix=TASK_ID_V1 + "-",
                    dir=STATE_ROOT / "review-scratch",
                )
            )
            assert runtime_root.is_absolute() and runtime_root.is_dir()
            assert runtime_root.resolve(strict=True) == runtime_root
            _evidence_v1(f"runtime_preserved_path={runtime_root}")

            phase = "single_train12_model_initialization"
            model = _instantiate_train12_model_v1(
                checkpoint=checkpoint, runtime_root=runtime_root
            )
            assert observations["model_initialization"]["requested"] == 1
            assert observations["model_initialization"]["returned"] == 1
            model_tripwire_calls = tools._install_no_training_tripwires_v1(
                stack, model=model
            )

            phase = "strict_checkpoint_migration"
            target_state_before_migration = model.state_dict()
            target_keys = set(target_state_before_migration)
            checkpoint_keys = set(checkpoint_state)
            shared_keys = target_keys & checkpoint_keys
            target_only = target_keys - checkpoint_keys
            fresh_target_only = {
                key: target_state_before_migration[key].detach().clone()
                for key in target_only
            }
            observations["migration"]["requested"] = 1
            migration = (
                migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
                    model=model,
                    checkpoint_state_dict=checkpoint_state,
                )
            )
            observations["migration"]["returned"] = 1
            migrated_state = model.state_dict()
            assert migration["checkpoint_key_count"] == len(checkpoint_keys)
            assert migration["target_model_key_count"] == len(target_keys)
            assert migration["shared_key_count"] == len(shared_keys)
            assert migration["target_only_key_count"] == len(target_only)
            assert migration["checkpoint_only_key_count"] == 0
            assert migration["shared_shape_mismatch_count"] == 0
            assert migration["migration_missing_keys"] == ()
            assert migration["migration_unexpected_keys"] == ()
            assert migration["full_target_strict_load"] is True
            assert migration["shared_checkpoint_tensor_equality_count"] == len(
                shared_keys
            )
            assert set(migration["target_only_exact_keys"]) == set(
                migration_owner.LEGACY_ALLOWED_NEW_EXACT_KEYS_V1
            )
            assert set(migration["target_only_auxiliary_keys"]) == {
                key
                for key in target_only
                if key.startswith(migration_owner.LEGACY_ALLOWED_NEW_PREFIXES_V1)
            }
            assert target_only == (
                set(migration["target_only_exact_keys"])
                | set(migration["target_only_auxiliary_keys"])
            )
            for key in shared_keys:
                assert migrated_state[key].detach().cpu().equal(
                    checkpoint_state[key].detach().cpu()
                ), key
            for key in target_only:
                assert migrated_state[key].detach().cpu().equal(
                    fresh_target_only[key].detach().cpu()
                ), key
            _evidence_v1(
                "checkpoint_migration=PASS "
                f"actual_checkpoint_keys={len(checkpoint_keys)} "
                f"actual_target_keys={len(target_keys)} "
                f"actual_shared_keys={len(shared_keys)} "
                f"actual_target_only={len(target_only)} "
                f"actual_new_exact={len(migration['target_only_exact_keys'])} "
                f"actual_new_auxiliary={len(migration['target_only_auxiliary_keys'])} "
                "checkpoint_only=0 shape_mismatch=0 strict=true"
            )

            phase = "model_configuration_validation"
            legacy = checkpoint["legacy_constructor"]
            dynamics = model.ddpm.dynamics
            assert type(model) is (
                adapter.CovapieTrain12HiddenPostForwardLigandPocketDDPMV1
            )
            assert model.device == torch.device("cpu")
            assert model.batch_size == 12
            assert model.mode == legacy["mode"] == "pocket_conditioning"
            assert model.pocket_representation == "full-atom"
            assert model.atom_nf == model.aa_nf == 10
            assert model.virtual_nodes is False
            assert model.auxiliary_loss is False
            assert model.ddpm.loss_type == legacy["diffusion_params"][
                "diffusion_loss_type"
            ]
            assert model.ddpm.T == 500 == legacy["diffusion_params"][
                "diffusion_steps"
            ]
            assert model.ddpm.norm_values == legacy["diffusion_params"][
                "normalize_factors"
            ]
            assert dynamics.target_residue_atom_conditioning is True
            assert dynamics.egnn.hidden_nf == legacy["egnn_params"]["hidden_nf"]
            assert dynamics.egnn.n_layers == legacy["egnn_params"]["n_layers"]
            assert model._trainer is None and model.current_epoch == 0
            assert model.covapie_current11_task_schedule_seed == 0
            assert model.ddpm.size_distribution.prob.shape == (
                len(legacy["node_histogram"]),
                len(legacy["node_histogram"][0]),
            )
            model.train()
            assert model.training is True and model.ddpm.training is True
            _evidence_v1(
                "model_configuration=PASS "
                f"class={type(model).__name__} batch_size=12 diffusion_steps=500 "
                f"normalization={model.ddpm.norm_values} "
                f"node_prior_shape={tuple(model.ddpm.size_distribution.prob.shape)} "
                "full_atom=true target_residue_conditioning=true virtual_nodes=false "
                "training_mode=true trainer_attached=false"
            )

            phase = "single_epoch0_seed0_carrier_build"
            observations["composer_prepare"]["requested"] = 1
            prepared = composer_owner.prepare_covapie_train12_cpu_batch_composer_v1(
                ROOT, STATE_ROOT, CACHE_ROOT
            )
            observations["composer_prepare"]["returned"] = 1
            prepared_before = _prepared_snapshot_v1(prepared, composer_owner)
            observations["carrier_build"]["requested"] = 1
            carrier = composer_owner.build_covapie_train12_cpu_epoch_batch_v1(
                prepared, 0, 0
            )
            observations["carrier_build"]["returned"] = 1
            carrier_measurements = _assert_train12_carrier_contract_v1(
                carrier, prepared, composer_owner
            )
            carrier_fingerprint = _carrier_fingerprint_v1(carrier)
            _evidence_v1(
                "train12_carrier=PASS "
                + json.dumps(carrier_measurements, sort_keys=True)
                + f" carrier_fingerprint={carrier_fingerprint}"
            )

            phase = "single_prepared_context_binding"
            prebind_parameter_ids = tuple(
                (name, id(value)) for name, value in model.named_parameters()
            )
            prebind_buffer_ids = tuple(
                (name, id(value)) for name, value in model.named_buffers()
            )
            prebind_state_keys = tuple(model.state_dict())
            observations["prepared_bind"]["requested"] = 1
            model.bind_covapie_train12_prepared_context_v1(prepared)
            observations["prepared_bind"]["returned"] = 1
            assert model._covapie_train12_bound_prepared_v1 is prepared
            assert model._covapie_train12_bound_prepared_identity_v1 == id(prepared)
            assert model._covapie_train12_bound_prepared_seal_v1 == prepared._seal
            assert model._covapie_train12_bound_repository_root_v1 == ROOT
            assert tuple(
                (name, id(value)) for name, value in model.named_parameters()
            ) == prebind_parameter_ids
            assert tuple(
                (name, id(value)) for name, value in model.named_buffers()
            ) == prebind_buffer_ids
            assert tuple(model.state_dict()) == prebind_state_keys
            assert not _contains_identity_v1(dict(model.hparams), prepared)
            assert all(value is not prepared for value in model.parameters())
            assert all(value is not prepared for value in model.buffers())
            assert _prepared_snapshot_v1(prepared, composer_owner) == prepared_before
            _evidence_v1(
                "prepared_binding=PASS calls=1 identity=true seal=true native_context=true "
                "hparams=false state_dict=false parameter=false buffer=false "
                "registered_state_unchanged=true"
            )

            # No-update baseline starts after migration, train mode, carrier,
            # and the single prepared-context binding.
            phase = "post_migration_post_bind_snapshot"
            model_snapshot = tools._capture_model_snapshot_v1(model)
            _evidence_v1(
                "post_bind_snapshot=PASS "
                f"parameter_count={len(model_snapshot.parameter_values)} "
                f"buffer_count={len(model_snapshot.buffer_values)} "
                f"state_key_count={len(model_snapshot.state_dict_keys)} "
                f"state_fingerprint={model_snapshot.state_fingerprint} "
                f"configuration_fingerprint={model_snapshot.configuration_fingerprint} "
                f"carrier_fingerprint={carrier_fingerprint}"
            )

            phase = "transparent_observer_installation"
            tools._patch_observer_v1(
                stack,
                owner=model,
                attribute="forward",
                stats=observations["model_forward"],
                projector=lambda args, kwargs, result: {
                    "carrier_identity": args[0] is carrier,
                    "no_keywords": kwargs == {},
                    "supervision_identity": result.supervision
                    is carrier.supervision,
                },
            )
            tools._patch_observer_v1(
                stack,
                owner=model,
                attribute="get_ligand_and_pocket",
                stats=observations["transport"],
                projector=lambda args, _kwargs, result: {
                    "model_input_identity": args[0] is carrier.model_input_batch,
                    "transported": tools._clone_transport_v1(result),
                },
            )
            tools._patch_observer_v1(
                stack,
                owner=model.covapie_current11_auxiliary_model_v1,
                attribute="encode_role_mask_anchor_v1",
                stats=observations["role_encoding"],
                projector=lambda _args, kwargs, result: {
                    "supervision_identity": kwargs["supervision"]
                    is carrier.supervision,
                    "ligand_batch_identity": kwargs["ligand_batch_index"]
                    is carrier.model_input_batch["lig_mask"],
                    "output_shape": tuple(result.shape),
                },
            )
            tools._patch_observer_v1(
                stack,
                owner=adapter,
                attribute="run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1",
                stats=observations["diffusion_bridge"],
                projector=lambda _args, kwargs, result: {
                    "supervision_identity": kwargs["supervision"]
                    is carrier.supervision,
                    "role_shape": tuple(
                        kwargs["role_mask_anchor_hidden_delta"].shape
                    ),
                    "timestep_shape": tuple(result.diffusion_timestep_int.shape),
                },
            )
            tools._patch_observer_v1(
                stack,
                owner=training_owner,
                attribute="run_covapie_current11_functional_dynamics_with_hidden_v1",
                stats=observations["functional_dynamics"],
                projector=lambda _args, kwargs, result: {
                    "ligand_xh_shape": tuple(kwargs["xh_atoms"].shape),
                    "pocket_xh_shape": tuple(kwargs["xh_residues"].shape),
                    "coordinate_mask_equal": result.coordinate_update_mask[
                        : len(kwargs["mask_atoms"])
                    ].equal(kwargs["ligand_coordinate_update_mask"]),
                },
            )
            tools._patch_observer_v1(
                stack,
                owner=dynamics.egnn,
                attribute="forward",
                stats=observations["egnn"],
                projector=lambda args, _kwargs, result: {
                    "hidden_input_shape": tuple(args[0].shape),
                    "coordinate_input_shape": tuple(args[1].shape),
                    "hidden_output_shape": tuple(result[0].shape),
                    "coordinate_output_shape": tuple(result[1].shape),
                },
            )
            for owner, name in (
                (dynamics.atom_encoder, "atom_encoder"),
                (dynamics.residue_encoder, "residue_encoder"),
                (
                    model.covapie_current11_auxiliary_model_v1.anchor_distance_encoder[
                        0
                    ],
                    "anchor_encoder",
                ),
                (
                    model.covapie_current11_auxiliary_model_v1.pair_embedding[0],
                    "pair_encoder",
                ),
            ):
                tools._patch_observer_v1(
                    stack,
                    owner=owner,
                    attribute="forward",
                    stats=observations[name],
                    projector=lambda args, _kwargs, result: {
                        "input_shape": tuple(args[0].shape),
                        "output_shape": tuple(result.shape),
                    },
                )
            tools._patch_observer_v1(
                stack,
                owner=model.covapie_current11_auxiliary_model_v1,
                attribute="forward",
                stats=observations["auxiliary"],
                projector=lambda _args, kwargs, result: {
                    "supervision_identity": kwargs["supervision"]
                    is carrier.supervision,
                    "pair_shape": tuple(result.pair_logits.shape),
                    "geometry_shape": tuple(
                        result.pre_post_geometry_predictions_angstrom.shape
                    ),
                },
            )
            tools._patch_observer_v1(
                stack,
                owner=adapter,
                attribute="compute_covapie_current11_training_losses_v1",
                stats=observations["production_loss"],
                projector=lambda _args, kwargs, result: {
                    "purpose": kwargs["post_geometry_loss_purpose"],
                    "supervision_identity": kwargs["supervision"]
                    is carrier.supervision,
                    "valid_counts": {
                        "base": result.base_diffusion_valid_sample_count,
                        "pair": result.covalent_pair_prediction_valid_sample_count,
                        "geometry": result.pre_post_geometry_valid_sample_count,
                        "contrastive": result.covalent_pair_contrastive_valid_sample_count,
                    },
                },
            )

            def forbidden_tensorization(*_args: object, **_kwargs: object) -> None:
                observations["secondary_tensorization"]["requested"] = int(
                    observations["secondary_tensorization"]["requested"]
                ) + 1
                raise AssertionError("secondary tensorization invoked during forward")

            stack.enter_context(
                mock.patch.object(
                    tensorizer_owner,
                    "tensorize_covapie_current11_training_supervision_v1",
                    new=forbidden_tensorization,
                )
            )
            stack.enter_context(
                mock.patch.object(
                    training_owner,
                    "tensorize_covapie_current11_training_supervision_v1",
                    new=forbidden_tensorization,
                )
            )

            weights = model.covapie_current11_loss_weights
            actual_weights = {
                field.name: getattr(weights, field.name) for field in fields(weights)
            }
            assert all(
                type(value) is float and math.isfinite(value)
                for value in actual_weights.values()
            )
            assert actual_weights["pre_post_geometry"] == 0.0
            _evidence_v1(
                "production_default_loss_weights="
                + json.dumps(actual_weights, sort_keys=True)
            )

            phase = "first_real_forward"
            torch.manual_seed(DIFFUSION_FORWARD_SEED_V1)
            forward_rng_state = torch.random.get_rng_state().clone()
            _evidence_v1(
                "forward_seed_state=CAPTURED "
                f"model_initialization_seed={MODEL_INITIALIZATION_SEED_V1} "
                f"forward_seed={DIFFUSION_FORWARD_SEED_V1}"
            )
            _evidence_v1("full_forward_1=START requested_budget=1/2")
            with torch.no_grad():
                first = model(carrier)
            _evidence_v1("full_forward_1=RETURNED returned_count=1/2")
            first_measurements = tools._validate_forward_output_v1(
                round_index=1, output=first, carrier=carrier, model=model
            )
            tools._assert_model_snapshot_unchanged_v1(model_snapshot, model)
            assert composer_owner.validate_covapie_train12_cpu_epoch_batch_v1(
                carrier, prepared
            )
            assert _carrier_fingerprint_v1(carrier) == carrier_fingerprint
            assert _prepared_snapshot_v1(prepared, composer_owner) == prepared_before
            _evidence_v1(
                "post_forward_1_invariance=PASS parameters=true buffers=true "
                "parameter_identity=true state_keys=true requires_grad=true "
                "gradients_none=true carrier_complete=true prepared=true "
                "config_and_prior=true"
            )

            phase = "same_rng_replay_forward"
            torch.random.set_rng_state(forward_rng_state)
            _evidence_v1(
                "full_forward_2=START requested_budget=2/2 cpu_rng_restored=true "
                "model_reloaded=false carrier_rebuilt=false"
            )
            with torch.no_grad():
                second = model(carrier)
            _evidence_v1("full_forward_2=RETURNED returned_count=2/2")
            second_measurements = tools._validate_forward_output_v1(
                round_index=2, output=second, carrier=carrier, model=model
            )
            tools._assert_model_snapshot_unchanged_v1(model_snapshot, model)
            assert composer_owner.validate_covapie_train12_cpu_epoch_batch_v1(
                carrier, prepared
            )
            assert _carrier_fingerprint_v1(carrier) == carrier_fingerprint
            assert _prepared_snapshot_v1(prepared, composer_owner) == prepared_before
            _evidence_v1(
                "post_forward_2_invariance=PASS parameters=true buffers=true "
                "parameter_identity=true state_keys=true requires_grad=true "
                "gradients_none=true carrier_complete=true prepared=true "
                "config_and_prior=true"
            )

            phase = "replay_comparison"
            replay_maximum_difference = tools._compare_replay_value_v1(
                first, second
            )
            assert first_measurements["timesteps"] == second_measurements[
                "timesteps"
            ]
            _evidence_v1(
                "rng_replay_comparison=PASS "
                f"maximum_finite_absolute_difference={replay_maximum_difference} "
                f"atol={DETERMINISM_ABSOLUTE_TOLERANCE_V1} "
                f"rtol={DETERMINISM_RELATIVE_TOLERANCE_V1} "
                "nan_positions_equal=true dtype_shape_discrete_metadata_equal=true"
            )

            phase = "observer_and_neural_path_validation"
            twice = (
                "model_forward",
                "transport",
                "role_encoding",
                "diffusion_bridge",
                "functional_dynamics",
                "egnn",
                "atom_encoder",
                "residue_encoder",
                "anchor_encoder",
                "pair_encoder",
                "auxiliary",
                "production_loss",
            )
            for name in twice:
                assert observations[name]["requested"] == 2, name
                assert observations[name]["returned"] == 2, name
                assert observations[name]["secondary_errors"] == [], name
            assert observations["secondary_tensorization"]["requested"] == 0
            assert all(
                record["carrier_identity"]
                and record["no_keywords"]
                and record["supervision_identity"]
                for record in observations["model_forward"]["records"]
            )
            assert all(
                record["model_input_identity"]
                for record in observations["transport"]["records"]
            )
            assert all(
                record["purpose"] == "independent_hidden_post_distance_v1"
                and record["supervision_identity"]
                for record in observations["production_loss"]["records"]
            )
            ligand_count = len(carrier.model_input_batch["lig_mask"])
            pocket_count = len(carrier.model_input_batch["pocket_mask"])
            candidate_count = len(
                carrier.supervision.pair_candidate_batch_index
            )
            expected_anchor_rows = int(
                (
                    carrier.supervision.ligand_anchor_distance_valid
                    & carrier.supervision.ligand_base_fixed_mask
                    & ~carrier.supervision.ligand_base_generation_mask
                )
                .sum()
                .item()
            )
            assert expected_anchor_rows > 0
            assert all(
                record["input_shape"] == (ligand_count, 10)
                for record in observations["atom_encoder"]["records"]
            )
            assert all(
                record["input_shape"] == (pocket_count, 10)
                for record in observations["residue_encoder"]["records"]
            )
            assert all(
                record["hidden_input_shape"] == (ligand_count + pocket_count, 33)
                for record in observations["egnn"]["records"]
            )
            assert all(
                record["input_shape"] == (expected_anchor_rows, 1)
                for record in observations["anchor_encoder"]["records"]
            )
            assert all(
                record["input_shape"] == (candidate_count, 129)
                for record in observations["pair_encoder"]["records"]
            )
            call_counts = tools._call_count_view_v1(observations)
            _evidence_v1(
                "observed_real_neural_path=PASS "
                + json.dumps(call_counts, sort_keys=True)
            )

            phase = "coordinate_and_fixed_node_oracle"
            transported = observations["transport"]["records"][0]["transported"]
            tools._assert_train10_centering_and_fixed_node_contract_v1(
                model=model,
                carrier=carrier,
                transported=transported,
                output=first,
            )
            _evidence_v1(
                "train12_coordinate_and_fixed_node_contract=PASS "
                "scatter_centering=true task_c_second_common_translation=true "
                "pocket_common_translation=true feature_channels_unchanged=true "
                "fixed_noise_zero=true update_mask=true fixed_restore=true"
            )

            phase = "final_source_checkpoint_and_state_validation"
            assert _verify_bound_sources_v1() == fixed_sources_before
            assert (
                adapter.verify_covapie_train12_hidden_post_forward_adapter_sources_v1(
                    repository_root=ROOT
                )
                == adapter_sources_before
            )
            assert _safe_file_identity_v1(checkpoint_path) == (
                checkpoint_size,
                checkpoint_sha,
            )
            tools._assert_model_snapshot_unchanged_v1(model_snapshot, model)
            assert _carrier_fingerprint_v1(carrier) == carrier_fingerprint
            assert _prepared_snapshot_v1(prepared, composer_owner) == prepared_before
            assert tripwire_calls == [] and model_tripwire_calls == []
            assert observations["checkpoint_deserialization"]["requested"] == 1
            assert observations["model_initialization"]["requested"] == 1
            assert observations["migration"]["requested"] == 1
            assert observations["composer_prepare"]["requested"] == 1
            assert observations["carrier_build"]["requested"] == 1
            assert observations["prepared_bind"]["requested"] == 1
            _evidence_v1(
                "final_integrity=PASS sources=true checkpoint=true parameters=true "
                "buffers=true carrier=true prepared=true hooks_pending_cleanup=true "
                "backward=false optimizer=false trainer=false save=false"
            )

        phase = "completed"
        print(f"TASK_ID={TASK_ID_V1}")
        print(f"RUNTIME_PRESERVED={runtime_root}")
        print(
            "CHECKPOINT="
            f"bytes:{checkpoint_size},sha256:{checkpoint_sha},"
            f"legacy_keys:{migration['checkpoint_key_count']},"
            f"target_keys:{migration['target_model_key_count']},"
            f"target_only:{migration['target_only_key_count']},strict:true"
        )
        print(
            "TRAIN12="
            f"tasks:{carrier_measurements['tasks']},"
            f"hidden_post:{carrier_measurements['hidden_post_eligible']},"
            f"generated:{carrier_measurements['generated_counts']},"
            f"fixed:{carrier_measurements['fixed_counts']},"
            f"task_c_seeds:{carrier_measurements['task_c_seed_counts']}"
        )
        print(f"TIMESTEPS={first_measurements['timesteps']}")
        print(
            "RAW_LOSSES="
            + json.dumps(first_measurements["raw_losses"], sort_keys=True)
        )
        print(
            "VALID_COUNTS="
            + json.dumps(first_measurements["valid_counts"], sort_keys=True)
        )
        print("LOSS_WEIGHTS=" + json.dumps(actual_weights, sort_keys=True))
        print("CALL_COUNTS=" + json.dumps(call_counts, sort_keys=True))
        print(
            "RNG_REPLAY="
            f"pass:true,atol:{DETERMINISM_ABSOLUTE_TOLERANCE_V1},"
            f"rtol:{DETERMINISM_RELATIVE_TOLERANCE_V1},"
            f"maximum_finite_absolute_difference:{replay_maximum_difference}"
        )
        print(
            "NO_UPDATE=parameters:true,buffers:true,identity:true,state_keys:true,"
            "requires_grad_flags:true,gradients_none:true,carrier:true,prepared:true,"
            "node_prior:true"
        )
        print(
            "TRAINING_OPERATIONS=backward:false,autograd_grad:false,"
            "optimizer_created:false,optimizer_step:false,trainer:false,"
            "checkpoint_saved:false"
        )
    except BaseException as primary:
        tools._report_primary_failure_v1(
            primary=primary,
            phase=phase,
            call_counts=tools._call_count_view_v1(observations),
        )
        raise
    finally:
        # Cleanup restores only caller CPU RNG and observer patches.  It never
        # reloads/copies parameters or retries a failed model stage.
        torch.random.set_rng_state(rng_before_validation)


def _execute_real_path_if_enabled_v1() -> None:
    if os.environ.get(REAL_FORWARD_OPT_IN_V1) != "1":
        pytest.skip(
            f"set {REAL_FORWARD_OPT_IN_V1}=1 for the bounded real checkpoint path"
        )
    _evidence_v1(
        "real_opt_in=1 one_checkpoint_load=true one_model=true one_migration=true "
        "one_epoch0_seed0_carrier=true one_prepared_bind=true "
        "maximum_forward_count=2"
    )
    _run_real_checkpoint_validation_v1()


@pytest.fixture(autouse=True)
def _non_model_execution_tripwires_v1(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Iterator[list[str]]:
    """All default tests fail closed at checkpoint/model/training boundaries."""

    calls: list[str] = []
    if (
        request.node.name
        == "test_real_checkpoint_train12_forward_and_same_rng_replay_no_update"
        and os.environ.get(REAL_FORWARD_OPT_IN_V1) == "1"
    ):
        yield calls
        return

    dependencies = _load_real_path_dependencies_v1()
    adapter = dependencies["adapter"]
    training_owner = dependencies["training_owner"]
    import pytorch_lightning as pl
    from covalent_ext import (
        covapie_current11_auxiliary_model_and_loss_v1 as loss_owner,
    )
    from equivariant_diffusion.conditional_model import ConditionalDDPM
    from equivariant_diffusion.dynamics import EGNNDynamics
    from lightning_modules import LigandPocketDDPM

    def forbidden(name: str) -> Callable[..., None]:
        def tripwire(*_args: object, **_kwargs: object) -> None:
            calls.append(name)
            raise AssertionError(f"non-model test reached forbidden boundary: {name}")

        return tripwire

    targets = (
        (torch, "load", "torch.load"),
        (torch, "save", "torch.save"),
        (torch.jit, "load", "torch.jit.load"),
        (torch.jit, "save", "torch.jit.save"),
        (torch.Tensor, "backward", "Tensor.backward"),
        (torch.autograd, "backward", "torch.autograd.backward"),
        (torch.autograd, "grad", "torch.autograd.grad"),
        (torch.optim.Optimizer, "__init__", "Optimizer.__init__"),
        (torch.optim.Optimizer, "step", "Optimizer.step"),
        (torch.optim.AdamW, "__init__", "AdamW.__init__"),
        (torch.optim.AdamW, "step", "AdamW.step"),
        (pl.Trainer, "__init__", "Trainer.__init__"),
        (pl.Trainer, "fit", "Trainer.fit"),
        (pl.Trainer, "validate", "Trainer.validate"),
        (pl.Trainer, "test", "Trainer.test"),
        (pl.Trainer, "predict", "Trainer.predict"),
        (pl.Trainer, "save_checkpoint", "Trainer.save_checkpoint"),
        (LigandPocketDDPM, "__init__", "LigandPocketDDPM.__init__"),
        (LigandPocketDDPM, "forward", "LigandPocketDDPM.forward"),
        (LigandPocketDDPM, "training_step", "LigandPocketDDPM.training_step"),
        (
            LigandPocketDDPM,
            "configure_optimizers",
            "LigandPocketDDPM.configure_optimizers",
        ),
        (ConditionalDDPM, "__init__", "ConditionalDDPM.__init__"),
        (ConditionalDDPM, "forward", "ConditionalDDPM.forward"),
        (EGNNDynamics, "__init__", "EGNNDynamics.__init__"),
        (EGNNDynamics, "forward", "EGNNDynamics.forward"),
        (
            loss_owner.CovapieCurrent11AuxiliaryModelV1,
            "__init__",
            "CovapieCurrent11AuxiliaryModelV1.__init__",
        ),
        (
            loss_owner.CovapieCurrent11AuxiliaryModelV1,
            "forward",
            "CovapieCurrent11AuxiliaryModelV1.forward",
        ),
        (
            adapter.CovapieTrain12HiddenPostForwardLigandPocketDDPMV1,
            "__init__",
            "Train12Adapter.__init__",
        ),
        (
            adapter.CovapieTrain12HiddenPostForwardLigandPocketDDPMV1,
            "forward",
            "Train12Adapter.forward",
        ),
        (
            adapter,
            "run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1",
            "train12_diffusion_bridge",
        ),
        (
            training_owner,
            "run_covapie_current11_functional_dynamics_with_hidden_v1",
            "functional_dynamics",
        ),
        (
            adapter,
            "compute_covapie_current11_training_losses_v1",
            "train12_production_loss",
        ),
        (
            loss_owner,
            "compute_covapie_current11_training_losses_v1",
            "production_loss",
        ),
    )
    for owner, attribute, name in targets:
        monkeypatch.setattr(owner, attribute, forbidden(name))
    yield calls
    assert calls == []


def test_fixed_published_sources_config_locator_and_train12_factory() -> None:
    dependencies = _load_real_path_dependencies_v1()
    adapter = dependencies["adapter"]
    checkpoint_locator = dependencies["checkpoint_locator"]
    compatible_owner = dependencies["compatible_owner"]
    constructor_owner = dependencies["constructor_owner"]
    migration_owner = dependencies["migration_owner"]
    composer = dependencies["composer_owner"]
    kwargs_owner = dependencies["kwargs_owner"]

    observed = _verify_bound_sources_v1()
    assert len(observed) == len(BOUND_SOURCE_IDENTITIES_V1)
    assert adapter.verify_covapie_train12_hidden_post_forward_adapter_sources_v1(
        repository_root=ROOT
    ) == adapter.DIRECT_BOUND_SOURCE_SHA256_V1
    assert composer._verify_direct_helpers(ROOT) == composer._SOURCE_SPECS
    assert tuple(composer.CANONICAL_TASKS_V1) == CANONICAL_EXACT5_V1
    assert CANONICAL_EXACT5_V1[3][1:3] == ("scaffold_only", "B3")
    assert len(CANONICAL_EXACT5_V1) == 5
    assert checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1 == (
        compatible_owner.CHECKPOINT_PATH
    )
    assert not checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1.is_absolute()
    assert migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1 == (
        EXPECTED_CHECKPOINT_SIZE_BYTES_V1
    )
    assert migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1 == (
        EXPECTED_CHECKPOINT_SHA256_V1
    )
    assert constructor_owner._constructor_kwargs is kwargs_owner._constructor_kwargs
    assert compatible_owner._constructor_kwargs is kwargs_owner._constructor_kwargs

    adapter_source = (
        ROOT
        / "src/covalent_ext/covapie_train12_hidden_post_forward_adapter_v1.py"
    ).read_text(encoding="utf-8")
    assert "super().forward" not in adapter_source
    assert "tensorize_covapie_current11_training_supervision_v1" not in (
        adapter_source
    )
    assert "post_geometry_loss_purpose=TRAIN12_HIDDEN_POST_LOSS_PURPOSE_V1" in (
        adapter_source
    )
    constructor_source = inspect.getsource(_instantiate_train12_model_v1)
    assert "CovapieTrain12HiddenPostForwardLigandPocketDDPMV1" in constructor_source
    assert '"batch_size": 12' in constructor_source
    assert '"covapie_train12_hidden_post_forward_enabled": True' in (
        constructor_source
    )
    assert "CovapieTrain10HiddenPostForwardLigandPocketDDPMV1" not in (
        constructor_source
    )
    assert "_instantiate_train10_model_v1" not in constructor_source


def test_default_opt_in_gate_precedes_entire_real_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched = []

    def forbidden_real_path() -> None:
        touched.append("real_path")
        raise AssertionError("default-disabled path was reached")

    monkeypatch.delenv(REAL_FORWARD_OPT_IN_V1, raising=False)
    monkeypatch.setattr(
        sys.modules[__name__],
        "_run_real_checkpoint_validation_v1",
        forbidden_real_path,
    )
    with pytest.raises(pytest.skip.Exception, match=REAL_FORWARD_OPT_IN_V1):
        _execute_real_path_if_enabled_v1()
    assert touched == []


def test_wrong_checkpoint_identity_rejects_before_deserialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    migration = _load_real_path_dependencies_v1()["migration_owner"]
    candidate = tmp_path / "identity-mismatch.bin"
    candidate.write_bytes(b"not-the-published-checkpoint")
    assert candidate.suffix == ".bin"
    deserialization_calls = []

    def forbidden_load(*_args: object, **_kwargs: object) -> None:
        deserialization_calls.append("torch.load")
        raise AssertionError("mismatched checkpoint reached torch.load")

    monkeypatch.setattr(migration.torch, "load", forbidden_load)
    with pytest.raises(
        ValueError,
        match="^COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_V1_ERROR$",
    ):
        migration.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=candidate
        )
    assert deserialization_calls == []


def test_reused_helpers_are_length_generic_nan_aware_and_no_update() -> None:
    tools = _load_published_train10_tools_v1()
    generic_helpers = (
        tools._compare_replay_value_v1,
        tools._hidden_post_eligibility_oracle_v1,
        tools._carrier_measurements_v1,
        tools._capture_model_snapshot_v1,
        tools._assert_model_snapshot_unchanged_v1,
        tools._assert_train10_centering_and_fixed_node_contract_v1,
    )
    for helper in generic_helpers:
        source = inspect.getsource(helper)
        assert "range(10)" not in source
        assert "len(carrier.sample_identities) == 10" not in source

    first = {
        "values": torch.tensor([1.0, float("nan"), float("inf")]),
        "task_ids": torch.arange(12, dtype=torch.long),
    }
    second = {
        "values": torch.tensor([1.0, float("nan"), float("inf")]),
        "task_ids": torch.arange(12, dtype=torch.long),
    }
    assert tools._compare_replay_value_v1(first, second) == 0.0
    second["values"][0] = 1.1
    with pytest.raises(AssertionError):
        tools._compare_replay_value_v1(first, second)

    calls = []

    def original(value: int, *, scale: int = 1) -> int:
        calls.append((value, scale))
        return value * scale

    stats = tools._new_call_stats_v1()
    observed = tools._transparent_observer_v1(
        original,
        stats=stats,
        projector=lambda args, kwargs, result: (args, kwargs, result),
    )
    assert inspect.signature(observed) == inspect.signature(original)
    assert observed(3, scale=4) == 12
    assert calls == [(3, 4)]
    assert stats["requested"] == stats["returned"] == 1

    class TinyModel(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.weight = torch.nn.Parameter(torch.tensor([1.0]))
            self.register_buffer("counter", torch.tensor([2.0]))

    tiny = TinyModel()
    batch_tools = tools._load_published_legacy_tools_v1()
    parameter_snapshot = batch_tools._snapshot_named_tensors(
        iter(tuple(tiny.named_parameters()))
    )
    buffer_snapshot = batch_tools._snapshot_named_tensors(
        iter(tuple(tiny.named_buffers()))
    )
    batch_tools._assert_snapshot_unchanged(
        parameter_snapshot, iter(tuple(tiny.named_parameters()))
    )
    batch_tools._assert_snapshot_unchanged(
        buffer_snapshot, iter(tuple(tiny.named_buffers()))
    )
    tiny.counter.add_(1.0)
    with pytest.raises(AssertionError):
        batch_tools._assert_snapshot_unchanged(
            buffer_snapshot, iter(tuple(tiny.named_buffers()))
        )


def test_real_budget_tripwire_and_failure_reporting_regressions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    execute = functions["_execute_real_path_if_enabled_v1"]
    run = functions["_run_real_checkpoint_validation_v1"]
    factory = functions["_instantiate_train12_model_v1"]
    assert isinstance(execute.body[0], ast.If)

    def call_count(function: ast.AST, name: str) -> int:
        return sum(
            1
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id == name)
                or (isinstance(node.func, ast.Attribute) and node.func.attr == name)
            )
        )

    assert call_count(run, "load_covapie_current11_legacy_checkpoint_v1") == 1
    assert call_count(run, "_instantiate_train12_model_v1") == 1
    assert call_count(run, "migrate_covapie_current11_legacy_checkpoint_state_dict_v1") == 1
    assert call_count(run, "prepare_covapie_train12_cpu_batch_composer_v1") == 1
    assert call_count(run, "build_covapie_train12_cpu_epoch_batch_v1") == 1
    assert call_count(run, "bind_covapie_train12_prepared_context_v1") == 1
    assert call_count(run, "mkdtemp") == 1
    assert sum(
        1
        for node in ast.walk(run)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "model"
    ) == 2
    assert call_count(factory, "CovapieTrain12HiddenPostForwardLigandPocketDDPMV1") == 1
    forbidden_calls = {
        "backward",
        "grad",
        "step",
        "training_step",
        "fit",
        "validate",
        "test",
        "eval",
        "load_from_checkpoint",
        "load_state_dict",
        "save",
        "save_checkpoint",
    }
    assert not {
        node.func.attr
        for node in ast.walk(run)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in forbidden_calls
    }

    tools = _load_published_train10_tools_v1()
    with contextlib.ExitStack() as stack:
        tripwire_calls = tools._install_no_training_tripwires_v1(stack)
        with pytest.raises(AssertionError, match="forbidden operation invoked"):
            torch.autograd.grad(torch.tensor(1.0), torch.tensor(1.0))
        assert tripwire_calls == ["torch.autograd.grad"]

    root_cause = LookupError("synthetic root cause")
    stats = tools._new_call_stats_v1()

    def original() -> None:
        raise RuntimeError("synthetic primary failure") from root_cause

    def secondary_reporter(_error: BaseException) -> None:
        raise ValueError("synthetic secondary observer failure")

    wrapper = tools._transparent_observer_v1(
        original,
        stats=stats,
        projector=lambda _args, _kwargs, result: result,
        failure_reporter=secondary_reporter,
    )
    with pytest.raises(RuntimeError, match="synthetic primary failure") as caught:
        wrapper()
    assert caught.value.__cause__ is root_cause
    assert stats["requested"] == 1 and stats["returned"] == 0
    assert stats["secondary_errors"] == [
        "ValueError:synthetic secondary observer failure"
    ]

    def broken_emitter(_message: str) -> None:
        raise OSError("synthetic report sink failure")

    tools._report_primary_failure_v1(
        primary=caught.value,
        phase="synthetic_failure_regression",
        call_counts={"production": {"requested": 1, "returned": 0}},
        emitter=broken_emitter,
    )
    stderr = capsys.readouterr().err
    assert "RuntimeError" in stderr and "synthetic primary failure" in stderr
    assert "LookupError" in stderr and "synthetic root cause" in stderr
    assert "SECONDARY_REPORTING_ERROR" in stderr
    assert any(
        "secondary_reporting_error=OSError:synthetic report sink failure" in note
        for note in caught.value.__notes__
    )


def test_fresh_process_dependency_helper_adapter_first_no_model() -> None:
    child_code = r'''
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
from unittest import mock

candidate = Path(os.environ["COVAPIE_FRESH_PROCESS_CANDIDATE"])
repo = Path(os.environ["COVAPIE_TEST_REPOSITORY_ROOT"])
state = Path(os.environ["COVAPIE_TEST_STATE_ROOT"])
assert candidate.is_absolute() and candidate.resolve(strict=True) == candidate
assert repo.is_absolute() and repo.resolve(strict=True) == repo
assert state.is_absolute() and state.resolve(strict=True) == state
assert "COVAPIE_RUN_TRAIN12_CHECKPOINT_FORWARD_NO_UPDATE" not in os.environ
runtime_parent = state / "review-scratch"
runtime_pattern = "validate_covapie_train12_checkpoint_forward_no_update_v1-*"
runtime_before = tuple(sorted(runtime_parent.glob(runtime_pattern)))

adapter_name = "covalent_ext.covapie_train12_hidden_post_forward_adapter_v1"
training_name = "covalent_ext.covapie_current11_training_lightning_module_v1"
assert adapter_name not in sys.modules
assert training_name not in sys.modules
spec = importlib.util.spec_from_file_location(
    "covapie_train12_checkpoint_fresh_dependency_candidate", candidate
)
assert spec is not None and spec.loader is not None
subject = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = subject
spec.loader.exec_module(subject)
assert adapter_name not in sys.modules
assert training_name not in sys.modules

import Bio
from Bio.PDB import Polypeptide
compat_before = hasattr(Polypeptide, "three_to_one")
assert compat_before is False
import pytorch_lightning as pl
import torch

tripwire_calls = []
def forbidden(name):
    def tripwire(*_args, **_kwargs):
        tripwire_calls.append(name)
        raise AssertionError("fresh dependency helper crossed boundary: " + name)
    return tripwire

profile_targets = {
    "CovapieTrain12HiddenPostForwardLigandPocketDDPMV1.__init__",
    "CovapieTrain12HiddenPostForwardLigandPocketDDPMV1.forward",
    "CovapieCurrent11TrainingLigandPocketDDPM.__init__",
    "CovapieCurrent11TrainingLigandPocketDDPM.forward",
    "LigandPocketDDPM.__init__",
    "LigandPocketDDPM.forward",
    "compute_covapie_current11_training_losses_v1",
    "run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1",
    "run_covapie_current11_functional_dynamics_with_hidden_v1",
}
def profiler(frame, event, _arg):
    if event == "call" and frame.f_code.co_qualname in profile_targets:
        tripwire_calls.append("profile:" + frame.f_code.co_qualname)
        raise AssertionError("fresh dependency helper executed " + frame.f_code.co_qualname)

def audit_hook(event, arguments):
    if event == "open" and arguments:
        path = arguments[0]
        if isinstance(path, (str, bytes, os.PathLike)):
            rendered = os.fsdecode(path)
            if "/checkpoints/" in rendered or rendered.endswith(".ckpt"):
                tripwire_calls.append("checkpoint_open:" + rendered)
                raise AssertionError("fresh dependency helper opened checkpoint")
    if event == "os.mkdir" and arguments:
        path = arguments[0]
        if isinstance(path, (str, bytes, os.PathLike)):
            created = Path(os.fsdecode(path))
            if not created.is_absolute():
                created = Path.cwd() / created
            if created.parent == runtime_parent and created.match(runtime_pattern):
                tripwire_calls.append("model_runtime_mkdir:" + str(created))
                raise AssertionError("fresh dependency helper created runtime")

sys.addaudithook(audit_hook)
with contextlib.ExitStack() as stack:
    for owner, attribute, name in (
        (torch, "load", "torch.load"),
        (torch, "save", "torch.save"),
        (torch.jit, "load", "torch.jit.load"),
        (torch.jit, "save", "torch.jit.save"),
        (torch.Tensor, "backward", "Tensor.backward"),
        (torch.autograd, "backward", "torch.autograd.backward"),
        (torch.autograd, "grad", "torch.autograd.grad"),
        (torch.optim.Optimizer, "__init__", "Optimizer.__init__"),
        (torch.optim.Optimizer, "step", "Optimizer.step"),
        (torch.optim.AdamW, "__init__", "AdamW.__init__"),
        (torch.optim.AdamW, "step", "AdamW.step"),
        (pl.Trainer, "__init__", "Trainer.__init__"),
        (pl.Trainer, "fit", "Trainer.fit"),
        (pl.Trainer, "validate", "Trainer.validate"),
        (pl.Trainer, "test", "Trainer.test"),
        (pl.Trainer, "predict", "Trainer.predict"),
        (pl.Trainer, "save_checkpoint", "Trainer.save_checkpoint"),
    ):
        stack.enter_context(mock.patch.object(owner, attribute, new=forbidden(name)))
    sys.setprofile(profiler)
    try:
        first = subject._load_real_path_dependencies_v1()
        second = subject._load_real_path_dependencies_v1()
    finally:
        sys.setprofile(None)

assert tripwire_calls == []
assert tuple(sorted(runtime_parent.glob(runtime_pattern))) == runtime_before
assert first.keys() == second.keys()
assert all(first[key] is second[key] for key in first)
adapter = first["adapter"]
training = first["training_owner"]
assert adapter is sys.modules[adapter_name]
assert training is sys.modules[training_name]
assert Path(adapter.__file__).resolve(strict=True) == (
    repo / "src/covalent_ext/covapie_train12_hidden_post_forward_adapter_v1.py"
)
assert Path(training.__file__).resolve(strict=True) == (
    repo / "src/covalent_ext/covapie_current11_training_lightning_module_v1.py"
)
assert hasattr(Polypeptide, "three_to_one")
assert adapter.BIOPYTHON_COMPAT_APPLIED_V1 is True
print("FRESH_PROCESS_REAL_DEPENDENCY_IMPORT=" + json.dumps({
    "adapter_path": str(Path(adapter.__file__).resolve(strict=True)),
    "training_owner_path": str(Path(training.__file__).resolve(strict=True)),
    "compat_before": compat_before,
    "compat_after": hasattr(Polypeptide, "three_to_one"),
    "helper_second_call_same_modules": True,
    "python_version": platform.python_version(),
    "torch_version": torch.__version__,
    "lightning_version": pl.__version__,
    "biopython_version": Bio.__version__,
    "tripwire_call_count": len(tripwire_calls),
    "checkpoint_read": False,
    "carrier_built": False,
    "runtime_created": False,
    "model_instantiated": False,
    "forward_executed": False,
}, sort_keys=True))
'''
    environment = os.environ.copy()
    for name in (
        REAL_FORWARD_OPT_IN_V1,
        "COVAPIE_RUN_BATCH001_CHECKPOINT_FORWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_BACKWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_SINGLE_OPTIMIZER_STEP",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_FIT",
        "COVAPIE_RUN_TRAIN10_CHECKPOINT_FORWARD_NO_UPDATE",
        "COVAPIE_RUN_TRAIN10_CHECKPOINT_BACKWARD_NO_UPDATE",
        "COVAPIE_RUN_TRAIN10_CHECKPOINT_SINGLE_OPTIMIZER_STEP",
        "COVAPIE_RUN_TRAIN10_CHECKPOINT_FIT",
        "COVAPIE_TRAIN12_FORWARD_ADAPTER_CANDIDATE",
        "COVAPIE_TRAIN12_COMPOSER_CANDIDATE",
        "COVAPIE_TRAIN10_FORWARD_ADAPTER_CANDIDATE",
        "COVAPIE_TRAIN10_COMPOSER_CANDIDATE",
        "COVAPIE_CURRENT11_LEGACY_TRAIN5_DATA_ADAPTER_CANDIDATE",
        "COVAPIE_LEGACY_TRAIN5_ADAPTER_CANDIDATE",
        "COVAPIE_ADAPTER_CANDIDATE",
    ):
        environment.pop(name, None)
    environment.update(
        {
            "COVAPIE_FRESH_PROCESS_CANDIDATE": str(
                Path(__file__).resolve(strict=True)
            ),
            "COVAPIE_TEST_REPOSITORY_ROOT": str(ROOT),
            "COVAPIE_TEST_STATE_ROOT": str(STATE_ROOT),
            "COVAPIE_TEST_CACHE_ROOT": str(CACHE_ROOT),
            "PYTHONPATH": f"{ROOT / 'src'}:{ROOT}",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
        }
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", child_code],
        cwd=ROOT,
        env=environment,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    assert len(lines) == 1, completed.stdout
    assert lines[0].startswith("FRESH_PROCESS_REAL_DEPENDENCY_IMPORT=")
    result = json.loads(lines[0].split("=", 1)[1])
    assert result["compat_before"] is False
    assert result["compat_after"] is True
    assert result["helper_second_call_same_modules"] is True
    assert result["tripwire_call_count"] == 0
    assert result["checkpoint_read"] is False
    assert result["carrier_built"] is False
    assert result["runtime_created"] is False
    assert result["model_instantiated"] is False
    assert result["forward_executed"] is False
    assert all(
        type(result[name]) is str and result[name]
        for name in (
            "python_version",
            "torch_version",
            "lightning_version",
            "biopython_version",
        )
    )
    print(lines[0], flush=True)


def test_scatter_centering_and_fixed_node_oracle_fail_closed_probes() -> None:
    tools = _load_published_train10_tools_v1()
    model, carrier, transported, output = (
        tools._synthetic_centering_contract_fixture_v1()
    )
    tools._assert_train10_centering_and_fixed_node_contract_v1(
        model=model, carrier=carrier, transported=transported, output=output
    )

    def wrong_center(trace: object, transport: object) -> None:
        ligand = transport[0]
        raw = torch.cat((ligand["x"], ligand["one_hot"] / 4.0), dim=1)
        references = torch.tensor(
            [[3.0, 0.0, 0.0], [0.0, 4.0, 0.0]]
        ).flip(0)
        raw[:, :3] -= references[ligand["mask"]]
        trace.clean_centered_ligand_xh = raw

    def omit_pocket_translation(trace: object, transport: object) -> None:
        rows = transport[1]["mask"] == 1
        trace.clean_centered_pocket_xh[rows, 0] += 3.0

    def omit_task_c_second_translation(trace: object, transport: object) -> None:
        ligand_rows = transport[0]["mask"] == 1
        pocket_rows = transport[1]["mask"] == 1
        trace.noised_ligand_xh[ligand_rows, 0] += 3.0
        trace.clean_centered_pocket_xh[pocket_rows, 0] += 3.0

    def modify_feature(trace: object, _transport: object) -> None:
        trace.clean_centered_ligand_xh[0, 3] += 1.0

    def add_fixed_noise(trace: object, _transport: object) -> None:
        trace.sampled_epsilon_ligand[0, 0] = 1.0

    def change_fixed_output(trace: object, _transport: object) -> None:
        trace.denoised_ligand_xh[0, 0] += 1.0

    def wrong_update_mask(trace: object, _transport: object) -> None:
        trace.ligand_coordinate_update_mask[0, 0] = True

    probes = (
        ("wrong_center", wrong_center),
        ("pocket_translation_omitted", omit_pocket_translation),
        ("task_c_second_translation_omitted", omit_task_c_second_translation),
        ("feature_channel_modified", modify_feature),
        ("fixed_node_noise", add_fixed_noise),
        ("fixed_node_output_changed", change_fixed_output),
        ("wrong_update_mask", wrong_update_mask),
    )
    rejected = []
    for name, mutate in probes:
        probe_model, probe_carrier, probe_transport, probe_output = (
            tools._synthetic_centering_contract_fixture_v1()
        )
        mutate(probe_output.diffusion_trace, probe_transport)
        with contextlib.redirect_stdout(io.StringIO()):
            with pytest.raises(AssertionError):
                tools._assert_train10_centering_and_fixed_node_contract_v1(
                    model=probe_model,
                    carrier=probe_carrier,
                    transported=probe_transport,
                    output=probe_output,
                )
        rejected.append(name)
    assert tuple(rejected) == tuple(name for name, _mutate in probes)
    print(
        "SCATTER_CENTERING_AND_FIXED_NODE_ORACLE_REGRESSION="
        + json.dumps(
            {
                "positive_contract": "PASS",
                "negative_probes_rejected": rejected,
                "coordinate_atol": COORDINATE_ABSOLUTE_TOLERANCE_V1,
                "coordinate_rtol": COORDINATE_RELATIVE_TOLERANCE_V1,
                "real_model_executed": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def test_single_epoch0_seed0_cpu_carrier_preflight_data_only() -> None:
    composer = _load_real_path_dependencies_v1()["composer_owner"]
    prepared = composer.prepare_covapie_train12_cpu_batch_composer_v1(
        ROOT, STATE_ROOT, CACHE_ROOT
    )
    prepared_before = _prepared_snapshot_v1(prepared, composer)
    carrier = composer.build_covapie_train12_cpu_epoch_batch_v1(prepared, 0, 0)
    before = _carrier_fingerprint_v1(carrier)
    measurements = _assert_train12_carrier_contract_v1(
        carrier, prepared, composer
    )
    assert composer.validate_covapie_train12_cpu_epoch_batch_v1(carrier, prepared)
    assert _carrier_fingerprint_v1(carrier) == before
    assert _prepared_snapshot_v1(prepared, composer) == prepared_before
    print(
        "CPU_CARRIER_PREFLIGHT="
        + json.dumps(measurements, sort_keys=True),
        flush=True,
    )
    print("TRAIN12_PREPARE_COUNT_THIS_TEST=1", flush=True)
    print("TRAIN12_EPOCH0_CARRIER_BUILD_COUNT_THIS_TEST=1", flush=True)
    print("REAL_MODEL_EXECUTION_COUNT_THIS_TEST=0", flush=True)
    print("PENDING_REAL_EXECUTION=true", flush=True)


def test_real_checkpoint_train12_forward_and_same_rng_replay_no_update() -> None:
    """Run only under the new independent explicit technical opt-in."""

    _execute_real_path_if_enabled_v1()
