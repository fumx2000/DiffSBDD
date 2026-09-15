"""Scoped, data-only train10 atom-feature rejection-chain regression.

The session fixture performs exactly one real published CPU prepare.  This
file never constructs a neural model, opens a checkpoint, or runs a forward:
the adapter forward is interrupted at its pre-transport sentinel.
"""

from __future__ import annotations

import ast
import copy
import csv
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest


BASELINE = "b3f803b985e6d023277ad2a4313eb69219a91eeb"
EXPECTED_CHANNELS = ("C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F")
EXPECTED_MASKS = (
    "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
    "scaffold_only", "scaffold_plus_linker_plus_warhead",
)
SOURCE_SHA = {
    "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py": "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241",
    "src/covalent_ext/covapie_batch001_positive_structural_input_v1.py": "c4cada3c5d3e8e86176b097cc5546854122162055437e4667288ba2f82629067",
    "src/covalent_ext/covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py": "c95bac177ba2ef1dd519bb5659cb97a8367484b1e41553be56fe3b2789ceb932",
    "src/covalent_ext/covapie_train10_cpu_batch_composer_v1.py": "5c5e7fee4804586e0c6d2a9bdf39a301dd154da92ff2d029f971d6b2b77d2ddd",
    "src/covalent_ext/covapie_train10_epoch_datamodule_v1.py": "84ea24ddfaa442be6a2b3ef9e29363d6e62f2d1aa3d5b847d5f6247c01548eda",
    "src/covalent_ext/covapie_train10_hidden_post_forward_adapter_v1.py": "5beaa700e2e5af87265c022a919dddfe1c8054114a45415adc416e5fe25fa40d",
    "src/covalent_ext/covapie_train10_bounded_training_session_v1.py": "328cac5496f2e59a15d712bc6055dd2469d79c8f6d08973dd7713bedc2ba591d",
    "data/derived/covalent_small/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_manifest.json": "24cb60ca4f080a72e8c60aef63d105d82ec2f432eecc9b90f3341f52576bb6e0",
}


def _roots():
    repository = Path(os.environ["COVAPIE_TEST_REPOSITORY_ROOT"])
    state = Path(os.environ["COVAPIE_TEST_STATE_ROOT"])
    cache = Path(os.environ["COVAPIE_TEST_CACHE_ROOT"])
    assert repository.is_absolute() and state.is_absolute() and cache.is_absolute()
    assert repository.resolve(strict=True) == repository
    return repository, state, cache


def _owners():
    # Maintain the published adapter-first Biopython compatibility import order.
    from covalent_ext import covapie_train10_hidden_post_forward_adapter_v1 as adapter
    from covalent_ext import covapie_train10_bounded_training_session_v1 as bounded
    from covalent_ext import covapie_train10_epoch_datamodule_v1 as data
    from covalent_ext import covapie_train10_cpu_batch_composer_v1 as composer
    from covalent_ext import covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1 as policy
    from covalent_ext import covapie_batch001_positive_structural_input_v1 as structural
    from covalent_ext import covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as mixed
    return SimpleNamespace(adapter=adapter, bounded=bounded, data=data,
                           composer=composer, policy=policy, structural=structural,
                           mixed=mixed)


@pytest.fixture(scope="session")
def owners():
    return _owners()


def _pin_assertions(repository):
    manifest_name = next(name for name in SOURCE_SHA if name.endswith("resolution_manifest.json"))
    for relative, expected in SOURCE_SHA.items():
        blob = subprocess.run(
            ("git", "show", f"{BASELINE}:{relative}"), cwd=repository,
            capture_output=True, check=True,
        ).stdout
        actual = (repository / relative).read_bytes()
        assert actual == blob
        assert hashlib.sha256(blob).hexdigest() == expected
    manifest = json.loads((repository / manifest_name).read_text())
    assert manifest["checkpoint_channel_order"] == "|".join(
        f"{token}:{index}" for index, token in enumerate(EXPECTED_CHANNELS)
    )
    assert manifest["unknown_atom_runtime_enforcement_integrated"] is False
    assert tuple(item["semantic_name"] for item in manifest["canonical_masks"]) == EXPECTED_MASKS
    assert manifest["ready_for_training"] is False


def _calls_function(repository, relative, caller, callee):
    """AST linkage only: proves source call sites, not that arbitrary inputs reach them."""
    tree = ast.parse((repository / relative).read_text())
    selected = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == caller)
    return any(isinstance(node, ast.Call) and (
        isinstance(node.func, ast.Name) and node.func.id == callee
        or isinstance(node.func, ast.Attribute) and node.func.attr == callee
    ) for node in ast.walk(selected))


def test_published_source_and_callsite_contract(owners):
    repository, _, _ = _roots()
    _pin_assertions(repository)
    src = "src/covalent_ext/"
    edges = (
        ("covapie_batch001_positive_structural_input_v1.py", "_project_rows", "project_type_symbols_to_checkpoint_heavy_v1"),
        ("covapie_batch001_positive_structural_input_v1.py", "_build_record", "_project_rows"),
        ("covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py", "_validated_exact10_rows", "project_type_symbols_to_checkpoint_heavy_v1"),
        ("covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py", "_validated_k36_sample_sources_v1", "_validated_exact10_rows"),
        ("covapie_train10_cpu_batch_composer_v1.py", "_build_impl_v1", "build_covapie_batch001_model_usable_split_batch_v1"),
        ("covapie_train10_cpu_batch_composer_v1.py", "_validate_batch_impl_v1", "_validate_collated_domains_v1"),
        ("covapie_train10_epoch_datamodule_v1.py", "validate_covapie_train10_epoch_datamodule_carrier_v1", "validate_covapie_train10_cpu_epoch_batch_v1"),
        ("covapie_train10_hidden_post_forward_adapter_v1.py", "_validate_train10_carrier_for_forward_v1", "validate_covapie_train10_cpu_epoch_batch_v1"),
        ("covapie_train10_bounded_training_session_v1.py", "_audit_prepared", "validate_covapie_train10_epoch_datamodule_carrier_v1"),
    )
    for relative, caller, callee in edges:
        assert _calls_function(repository, src + relative, caller, callee), (caller, callee)
    assert tuple(row[1] for row in owners.bounded.CANONICAL_MASK_CONTRACT_V1) == EXPECTED_MASKS
    print("CALLSITE_LINKS_FROM_BASELINE=9 HISTORICAL_POLICY_MANIFEST_UNCHANGED=true")


def test_policy_whole_sequence_and_hydrogen_before_projection(owners):
    policy = owners.policy
    for index, token in enumerate(EXPECTED_CHANNELS):
        projection = policy.project_type_symbols_to_checkpoint_heavy_v1(("H", token, "H"))
        assert projection.outcome == "passed" and not projection.sample_rejected
        assert projection.source_to_projected_index == (None, 0, None)
        assert projection.checkpoint_channel_indices == (None, index, None)
    for symbol in ("Se", "Zn", "Ca", None, "", "?", "CA", "1", "c", " H ", 2):
        rejected = policy.project_type_symbols_to_checkpoint_heavy_v1(("C", symbol, "O"))
        assert rejected.sample_rejected and rejected.outcome == "invalid"
        assert rejected.keep_mask == (False,) * 3
        assert rejected.checkpoint_channel_indices == (None,) * 3
        assert rejected.source_to_projected_index == (None,) * 3
    assert policy.classify_type_symbol_v1("Ca") == "unsupported_nonhydrogen"
    print("SOURCE_SYMBOL_REJECTION_TESTS_PASS=policy_whole_sample H_filter_before_remap=true")


def _atom(symbol, atom, index):
    return {
        "_atom_site.type_symbol": symbol,
        "_atom_site.id": str(index + 100),
        "_atom_site.label_atom_id": atom,
        "_atom_site.auth_atom_id": atom,
        "_atom_site.Cartn_x": "1.0", "_atom_site.Cartn_y": "2.0",
        "_atom_site.Cartn_z": "3.0", "_atom_site.occupancy": "1.0",
    }


def test_batch001_projection_parser_normalization_and_rejection(owners, monkeypatch):
    original = owners.policy.project_type_symbols_to_checkpoint_heavy_v1
    called = []

    def spy(symbols):
        called.append(tuple(symbols))
        return original(symbols)

    monkeypatch.setattr(owners.policy, "project_type_symbols_to_checkpoint_heavy_v1", spy)
    for role in ("ligand", "pocket"):
        rows = [_atom(" H ", "H1", 0), _atom(" c ", "CA", 1),
                _atom("CL", "Cl1", 2), _atom("H", "H2", 3),
                _atom("BR", "Br1", 4)]
        indices = {id(row): index for index, row in enumerate(rows)}
        projected = owners.structural._project_rows(rows, indices)
        assert tuple(row.source_atom_site_row_index_0based for row in projected) == (1, 2, 4)
        assert tuple(row.type_symbol for row in projected) == ("C", "Cl", "Br")
        assert tuple(row.checkpoint_channel_index for row in projected) == (0, 6, 5)
        assert called[-1] == ("C", "Cl", "Br")
        for value in ("Se", "Zn", "Ca", None, "", "?", "12", "C+", "CA"):
            bad = [_atom("C", "CA", 0), _atom(value, "CA", 1), _atom("O", "OG", 2)]
            with pytest.raises(owners.structural._StructuralInvariantError, match="UNSUPPORTED_NON_H_FEATURE_PROJECTION"):
                owners.structural._project_rows(bad, {id(row): i for i, row in enumerate(bad)})
        missing = [_atom("C", "CA", 0), _atom("O", "O", 1)]
        del missing[0]["_atom_site.type_symbol"]
        with pytest.raises(owners.structural._StructuralInvariantError, match="UNSUPPORTED_NON_H_FEATURE_PROJECTION"):
            owners.structural._project_rows(missing, {id(row): i for i, row in enumerate(missing)})
        # Artificial caller-supplied indices are NOT the formal mmCIF path:
        # _build_record itself enumerates parsed atom_rows by object identity.
        duplicate = [_atom("C", "C1", 0), _atom("O", "O2", 1)]
        rows_with_bad_source = owners.structural._project_rows(
            duplicate, {id(row): -1 for row in duplicate}
        )
        assert tuple(row.source_atom_site_row_index_0based for row in rows_with_bad_source) == (-1, -1)
    print("BATCH001_PROJECTION=parser_normalizes_then_policy_rejects; ARTIFICIAL_SOURCE_MAP_UNIT_UNVALIDATED=true")


def test_mixed_model_bound_type_channel_and_index_rejections(owners):
    mixed = owners.mixed
    rows = [dict(type_symbol=token, exact10_channel_index=index,
                 source_atom_site_row_index_0based=index, label_atom_id=f"A{index}")
            for index, token in enumerate(EXPECTED_CHANNELS)]
    normalized, channels = mixed._validated_exact10_rows(rows, expected_count=10)
    assert len(normalized) == 10 and channels == tuple(range(10))
    hot = mixed._one_hot(channels)
    assert tuple(hot.shape) == (10, 10)
    for i in range(10):
        assert hot[i].tolist() == [float(j == i) for j in range(10)]
    for symbol in ("H", "Se", "Zn", "Ca", None, "", "?", "CA", 4):
        bad = copy.deepcopy(rows)
        bad[4]["type_symbol"] = symbol
        with pytest.raises(mixed._MixedProfileInvariantError, match="EXACT10_MODEL_BOUND_PROJECTION_INVALID"):
            mixed._validated_exact10_rows(bad)
    for index in (9, 10, -1, True):
        bad = copy.deepcopy(rows)
        bad[0]["exact10_channel_index"] = index
        with pytest.raises(mixed._MixedProfileInvariantError, match="EXACT10_CHANNEL_BINDING_INVALID"):
            mixed._validated_exact10_rows(bad)
    for source_index in (-1, None, "0", True, 1):
        bad = copy.deepcopy(rows)
        bad[0]["source_atom_site_row_index_0based"] = source_index
        with pytest.raises(mixed._MixedProfileInvariantError, match="MODEL_BOUND_ATOM_ORDER_MAPPING_AMBIGUOUS"):
            mixed._validated_exact10_rows(bad)
    for channels in ((10,), (-1,), (True,)):
        with pytest.raises(mixed._MixedProfileInvariantError, match="EXACT10_CHANNEL_INVALID"):
            mixed._one_hot(channels)
    print("EXACT10_CHANNEL_SEMANTICS_TESTS_PASS=mixed_type_channel_source_index_H_rejected")


@pytest.fixture(scope="session")
def published(owners):
    repository, state, cache = _roots()
    _pin_assertions(repository)
    count = {"bounded_prepare": 0, "datamodule_prepare": 0,
             "composer_prepare": 0, "carrier_build": 0,
             "batch001_build": 0, "projector_calls": 0}
    batch001_records = []
    patches = []

    def wrap(module, name, key, capture=False):
        original = getattr(module, name)

        def tracked(*args, **kwargs):
            count[key] += 1
            result = original(*args, **kwargs)
            if capture and not batch001_records:
                batch001_records.extend(result.structural_records)
            return result

        patches.append((module, name, original))
        setattr(module, name, tracked)

    wrap(owners.bounded, "prepare_covapie_train10_bounded_training_session_v1", "bounded_prepare")
    wrap(owners.bounded.data_owner, "prepare_covapie_train10_epoch_datamodule_v1", "datamodule_prepare")
    wrap(owners.data.composer, "prepare_covapie_train10_cpu_batch_composer_v1", "composer_prepare")
    wrap(owners.data.composer, "build_covapie_train10_cpu_epoch_batch_v1", "carrier_build")
    wrap(owners.composer._batch001_owner, "build_covapie_batch001_model_usable_split_batch_v1", "batch001_build", True)
    wrap(owners.policy, "project_type_symbols_to_checkpoint_heavy_v1", "projector_calls")
    try:
        prepared = owners.bounded.prepare_covapie_train10_bounded_training_session_v1(
            repository_root=repository, state_root=state, cache_root=cache
        )
    finally:
        for module, name, original in reversed(patches):
            setattr(module, name, original)
    assert count["bounded_prepare"] == count["datamodule_prepare"] == count["composer_prepare"] == 1
    assert count["carrier_build"] == count["batch001_build"] == 5
    assert count["projector_calls"] > 0 and len(batch001_records) == 5
    print("REAL_PREPARE_AND_CARRIER_COUNTS=" + json.dumps(count, sort_keys=True))
    return SimpleNamespace(prepared=prepared, records=tuple(batch001_records), count=count)


def _assert_rows_match(one_hot, source_indices, retained, policy):
    assert len(one_hot) == len(source_indices) == len(retained)
    projection = policy.project_type_symbols_to_checkpoint_heavy_v1(
        tuple(row.type_symbol for row in retained)
    )
    assert not projection.sample_rejected and all(projection.keep_mask)
    assert tuple(row.checkpoint_channel_index for row in retained) == projection.checkpoint_channel_indices
    for i, row in enumerate(retained):
        assert source_indices[i] == row.source_atom_site_row_index_0based
        channel = projection.checkpoint_channel_indices[i]
        assert one_hot[i].tolist() == [float(j == channel) for j in range(10)]


def test_current_train10_batch001_source_to_carrier(published, owners):
    for carrier in published.prepared.carriers:
        assert owners.composer.validate_covapie_train10_cpu_epoch_batch_v1(carrier)
        assert owners.data.validate_covapie_train10_epoch_datamodule_carrier_v1(
            carrier, current_epoch=carrier.epoch
        )
        assert len(carrier.source_audit_blocks) == 6
        block = carrier.source_audit_blocks[0]
        assert block.sample_identities == tuple(row.sample_identity for row in published.records)
        model = block.model_input_batch
        ligand_rows = tuple(row for record in published.records for row in record.ligand_retained_heavy_atoms)
        pocket_rows = tuple(row for record in published.records for row in record.pocket_retained_heavy_atoms)
        _assert_rows_match(model["lig_one_hot"], model["lig_source_row_index"].tolist(), ligand_rows, owners.policy)
        _assert_rows_match(model["pocket_one_hot"], model["pocket_source_row_index"].tolist(), pocket_rows, owners.policy)
        assert tuple(int(value) for value in carrier.supervision.canonical_task_id.tolist()) == carrier.scheduled_task_ids
        assert carrier.payload_sha256 and all(block.payload_sha256 for block in carrier.source_audit_blocks)
        assert len(carrier.direct_source_bindings) > 0 and len(carrier.batch001_source_authority_bindings) > 0
        assert len(carrier.legacy_source_bindings) == 27
    assert published.prepared.plan.event_count == 10
    assert published.prepared.plan.leakage_group_count == 3
    assert published.prepared.plan.event_epoch_rows == 50
    assert published.prepared.plan.exact5_task_counts == (10,) * 5
    print("CURRENT_TRAIN10_BATCH001=5_source_bound_structural_records_5_epochs Exact10_and_seals PASS")


def test_batch001_published_record_validator_binds_symbols_to_channels(published, owners):
    for record in published.records:
        assert owners.structural.validate_covapie_batch001_positive_structural_record_v1(record)
        for side in ("ligand_retained_heavy_atoms", "pocket_retained_heavy_atoms"):
            atoms = getattr(record, side)
            for replacement in (
                replace(atoms[0], checkpoint_channel_index=(atoms[0].checkpoint_channel_index + 1) % 10),
                replace(atoms[0], type_symbol="Se"),
                replace(atoms[0], type_symbol="H"),
            ):
                forged = replace(record, **{side: (replacement,) + atoms[1:]})
                with pytest.raises(ValueError, match="STRUCTURAL_RECORD_FEATURE_PROJECTION_INVALID"):
                    owners.structural.validate_covapie_batch001_positive_structural_record_v1(forged)
    print("BATCH001_PUBLISHED_RECORD_VALIDATOR=ligand_and_pocket_symbol_channel_H_fail_closed")


def test_current_train10_legacy_historical_symbol_binding(published, owners):
    """Historical published CSV is a source-bound cross-check, not a raw reparse."""
    repository, _, _ = _roots()
    relative = ("data/derived/covalent_small/"
                "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
                "covapie_heavy_atom_disposition_and_index_projection_matrix.csv")
    raw = (repository / relative).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "b53f438edffab32f78d07df839b8c8437ec4223e31bd8a8885deedf32497b4be"
    assert subprocess.run(("git", "show", f"{BASELINE}:{relative}"), cwd=repository,
                          capture_output=True, check=True).stdout == raw
    inventory = list(csv.DictReader(io.StringIO(raw.decode())))
    for block in published.prepared.carriers[0].source_audit_blocks[1:]:
        sample = block.sample_identities[0]
        model = block.model_input_batch
        for domain, prefix in (("ligand_atom", "lig"), ("protein_or_pocket_atom", "pocket")):
            symbols = {int(row["projected_heavy_atom_row_index_0based"]): row
                       for row in inventory if row["sample_index_row_id"] == sample
                       and row["domain"] == domain and row["retained_for_checkpoint_model"] == "true"}
            assert len(symbols) == len(model[f"{prefix}_one_hot"]), (sample, domain, len(symbols))
            for local, hot in zip(model[f"{prefix}_parser_local_index"].tolist(),
                                  model[f"{prefix}_one_hot"]):
                source = symbols[local]
                symbol = source["type_symbol"]
                projection = owners.policy.project_type_symbols_to_checkpoint_heavy_v1((symbol,))
                assert not projection.sample_rejected
                assert source["checkpoint_channel_index"] == str(projection.checkpoint_channel_indices[0])
                assert hot.tolist() == [float(j == projection.checkpoint_channel_indices[0]) for j in range(10)]
    print("CURRENT_TRAIN10_LEGACY=5_materialized_source_bound_rows_vs_historical_disposition_EXACT10 PASS; RAW_REPARSE=not_run")


def _mutated(carrier, kind, side, torch):
    model = carrier.model_input_batch.copy()
    hot_name = "lig_one_hot" if side == "ligand" else "pocket_one_hot"
    source_name = "lig_source_row_index" if side == "ligand" else "pocket_source_row_index"
    mask_name = "lig_mask" if side == "ligand" else "pocket_mask"
    name = source_name if kind == "source_index" else mask_name if kind == "membership" else hot_name
    model[name] = model[name].clone()
    value = model[name]
    if kind == "zero":
        value[0] = 0
    elif kind == "multi":
        value[0, 1] = 1
        value[0, 2] = 1
    elif kind == "nonbinary":
        value[0, 0] = 0.5
    elif kind == "nan":
        value[0, 0] = float("nan")
    elif kind == "inf":
        value[0, 0] = float("inf")
    elif kind in ("width9", "width11"):
        model[name] = torch.cat((value, torch.zeros((len(value), 1))), dim=1) if kind == "width11" else value[:, :-1]
    elif kind == "wrong_channel":
        channel = int(value[0].argmax().item())
        value[0] = 0
        value[0, (channel + 1) % 10] = 1
    elif kind == "source_index":
        value[0] = -1
    elif kind == "membership":
        value[0] = 99
    else:
        raise AssertionError(kind)
    return replace(carrier, model_input_batch=model), model


class TransportBoundaryReached(Exception):
    pass


def _receiver(torch):
    def sentinel(_batch):
        raise TransportBoundaryReached("MODEL_ENTRY_PREFLIGHT_WITH_SENTINEL")

    return SimpleNamespace(
        covapie_train10_hidden_post_forward_enabled=True,
        device=torch.device("cpu"), training=True, current_epoch=0,
        covapie_current11_task_schedule_seed=0,
        get_ligand_and_pocket=sentinel,
    )


def test_real_delivery_transfer_and_adapter_sentinel_positive(published, owners):
    import torch
    carrier = published.prepared.carriers[0]
    module = published.prepared.datamodule
    module.setup("fit")
    loader = module.build_train_dataloader_for_epoch_v1(0)
    assert next(iter(loader)) is carrier
    assert module.on_before_batch_transfer(carrier, 0) is carrier
    assert module.transfer_batch_to_device(carrier, torch.device("cpu"), 0) is carrier
    assert module.on_after_batch_transfer(carrier, 0) is carrier
    with pytest.raises(TransportBoundaryReached, match="MODEL_ENTRY_PREFLIGHT_WITH_SENTINEL"):
        owners.adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1.forward(_receiver(torch), carrier)
    assert published.count["bounded_prepare"] == published.count["composer_prepare"] == 1
    assert published.count["carrier_build"] == 5
    print("MODEL_ENTRY_PREFLIGHT_WITH_SENTINEL=positive_reached_transport_boundary; NEURAL_FORWARD=0")


@pytest.mark.parametrize("side", ("ligand", "pocket"))
@pytest.mark.parametrize("kind", ("zero", "multi", "nonbinary", "nan", "inf", "width9", "width11", "wrong_channel", "source_index", "membership"))
def test_bad_carrier_rejected_before_model_compute(published, owners, side, kind):
    import torch
    carrier = published.prepared.carriers[0]
    bad, model = _mutated(carrier, kind, side, torch)
    # A standalone owner core check proves one-hot and source-index/membership
    # rules independently of the generic carrier mutation seal.
    if kind != "wrong_channel":
        expected = ("MODEL_ONE_HOT_INVALID" if kind in ("zero", "multi", "nonbinary", "nan", "inf")
                    else "MODEL_NODE_TENSOR_INVALID" if kind in ("width9", "width11")
                    else "MODEL_SOURCE_OR_LOCAL_INDEX_INVALID" if kind == "source_index"
                    else "MODEL_MEMBERSHIP_INVALID")
        with pytest.raises(owners.composer._ComposerInvariantError, match=expected):
            owners.composer._validate_model_core_v1(model)
        independent = expected
    else:
        assert owners.composer._validate_model_core_v1(model)
        independent = "ONE_HOT_SHAPE_ONLY_NOT_SYMBOL_BINDING; A_LAYER_BINDS_SYMBOL"
    with pytest.raises(ValueError, match="BATCH_METADATA_STATUS_OR_SEAL_INVALID") as composer_error:
        owners.composer.validate_covapie_train10_cpu_epoch_batch_v1(bad)
    assert "BATCH_METADATA_STATUS_OR_SEAL_INVALID" in str(composer_error.value)
    with pytest.raises(ValueError, match="PUBLISHED_COMPOSER_VALIDATOR_REJECTED"):
        owners.data.validate_covapie_train10_epoch_datamodule_carrier_v1(bad, current_epoch=0)
    isolated_module = copy.copy(published.prepared.datamodule)
    isolated_module.carriers = (bad,) + published.prepared.carriers[1:]
    isolated_module._selected_epoch = 0
    with pytest.raises(ValueError, match="PUBLISHED_COMPOSER_VALIDATOR_REJECTED"):
        isolated_module._delivery(bad)
    with pytest.raises(ValueError, match="PUBLISHED_COMPOSER_VALIDATOR_REJECTED"):
        isolated_module.on_before_batch_transfer(bad, 0)
    with pytest.raises(ValueError, match="PUBLISHED_COMPOSER_VALIDATOR_REJECTED"):
        isolated_module.transfer_batch_to_device(bad, torch.device("cpu"), 0)
    with pytest.raises(ValueError, match="PUBLISHED_COMPOSER_VALIDATOR_REJECTED"):
        owners.adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1.forward(_receiver(torch), bad)
    print(f"MUTATION_SEAL_REJECTION side={side} kind={kind} owner=composer/DataModule/adapter "
          f"independent_core={independent} next_transport_boundary=false")


def test_bounded_prepared_gate_no_build(published, owners):
    prepared = published.prepared
    assert owners.bounded._audit_prepared(prepared) is prepared
    # A forged carrier is not in the actual prepared datamodule; this is a
    # gate on prepared identity, not a run of build/runtime/checkpoint.
    bad, _ = _mutated(prepared.carriers[0], "zero", "ligand", __import__("torch"))
    forged = replace(prepared, carriers=(bad,) + prepared.carriers[1:])
    with pytest.raises(ValueError, match="PUBLISHED_DATAMODULE_OR_CARRIER_IDENTITY_REQUIRED"):
        owners.bounded._audit_prepared(forged)
    print("BOUNDED_PREPARED_GATE=identity_and_five_composer_validated; RUNTIME_BUILD=not_run")


def test_scoped_runtime_audit_stdout_summary(published, owners):
    """This conclusion covers only actual bounded train10 source/data entry."""
    assert published.count["bounded_prepare"] == published.count["composer_prepare"] == 1
    assert published.count["carrier_build"] == published.count["batch001_build"] == 5
    assert published.count["projector_calls"] > 0
    assert all(owners.composer.validate_covapie_train10_cpu_epoch_batch_v1(item)
               for item in published.prepared.carriers)
    print("SCOPED_RUNTIME_ATOM_FEATURE_ENFORCEMENT_VERIFIED=true "
          "SCOPE=published_bounded_train10_formal_sources_and_CPU_consumption_only")
    print("SOURCE_SYMBOL_REJECTION_TESTS_PASS=true EXACT10_CHANNEL_SEMANTICS_TESTS_PASS=true "
          "CURRENT_TRAIN10_SOURCE_TO_CARRIER_BINDING_VERIFIED=true")
    print("BAD_CARRIER_REJECTED_BEFORE_MODEL_COMPUTE=true "
          "GENERIC_SEAL_VS_SEMANTIC_REJECTION_DISTINGUISHED=true "
          "PRODUCTION_IMPLEMENTATION_GAP_FOUND=false_IN_SCOPED_FORMAL_PATH")
    print("EXACT_REMAINING_GAPS=standalone_Batch001__project_rows_accepts_artificial_duplicate_or_negative_source_map_outside_formal_enumerated_mmcif_caller; "
          "legacy_original_structure_not_reparsed_this_round; wider_final_feature_semantics_audit_pending")
    print("CHECKPOINT_ACCESSED=false REAL_NEURAL_FORWARD_EXECUTED=false "
          "PARAMETER_UPDATE_PERFORMED_THIS_ROUND=false READY_FOR_TRAINING=false "
          "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER=true STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK=true")
