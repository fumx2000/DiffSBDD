from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import stat
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import torch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_current11_pocket_atom_identity_alignment_v1 as alignment
from covalent_ext import covapie_target_residue_atom_condition_adapter_gate_v1 as gate


STATE = ROOT.parent / "covapie-state" / "manual-review"
AUTHORITY_PATH = STATE / "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
ALIGNMENT_PATH = STATE / "covapie_current11_pocket_atom_identity_alignment_bundle_v1.json"
ADAPTER_PATH = STATE / "covapie_current11_target_residue_atom_condition_adapter_bundle_v1.json"
EXPECTED_LOCAL = (49, 15, 12, 33, 31, 50, 48, 53, 52, 53, 84)
EXPECTED_FLAT = (49, 81, 182, 299, 505, 712, 988, 1260, 1516, 1766, 2058)
ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_INVALID"


@pytest.fixture(scope="session")
def sources() -> tuple[bytes, bytes, bytes]:
    return AUTHORITY_PATH.read_bytes(), ALIGNMENT_PATH.read_bytes(), ADAPTER_PATH.read_bytes()


@pytest.fixture(scope="session")
def formal_runs(sources):
    authority_bytes, alignment_bytes, adapter_bytes = sources
    snapshots = tuple(bytes(value) for value in sources)
    first = gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        source_adapter_bundle=adapter_bytes,
        repo_root=ROOT,
    )
    second = gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        source_adapter_bundle=adapter_bytes,
        repo_root=ROOT,
    )
    return first, second, snapshots, sources


def _assert_canonical_error(callable_):
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        callable_()


def _rehash_record(record: dict, fields: tuple[str, ...], digest_field: str) -> None:
    record[digest_field] = ""
    record[digest_field] = gate._digest_record(record, fields, digest_field)


def test_public_api_signature_all_and_silent_import():
    assert gate.__all__ == (
        "evaluate_covapie_target_residue_atom_condition_adapter_gate_v1",
    )
    signature = inspect.signature(
        gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1
    )
    assert tuple(signature.parameters) == (
        "source_authority_bundle",
        "source_alignment_bundle",
        "source_adapter_bundle",
        "repo_root",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    command = (
        "import covalent_ext."
        "covapie_target_residue_atom_condition_adapter_gate_v1"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1"},
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout == completed.stderr == ""


def test_formal_source_transport_and_runtime_bindings(formal_runs):
    bundle = formal_runs[0]
    expected = {
        "source_authority_bundle_transport_sha256": "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096",
        "source_alignment_bundle_transport_sha256": "7f80a810ff35c4ea5d61262021379767a4d15202badd8ec6a6b846405147d842",
        "source_adapter_bundle_transport_sha256": "983c25ea8c52ca54f0c0292990a625e9a9cf0d2370cb517d66a84801d957b65a",
        "source_adapter_bundle_sha256": "7e6475d45dcf3ee95982d8bfbf7a5e707aef8359cee2fc9af15a7eafeee7d1c7",
        "source_adapter_production_sha256": "ff65146ab97f5ea03330766d4517ca9f3f25a5e496529a0c2e2b4aa1479d255d",
        "source_dataset_module_sha256": "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99",
        "source_lightning_module_sha256": "2b771068eda19b6f783e12ff483a02ab6ef8264108f3af5e486d3381fb1e7fb6",
        "source_checkpoint_sha256": "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c",
    }
    assert {key: bundle[key] for key in expected} == expected
    assert bundle["source_adapter_bundle_recompiled_exact"] is True


def test_canonical_five_mask_contract_is_exact(formal_runs):
    assert tuple(formal_runs[0]["canonical_mask_semantic_names"]) == (
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    )


def test_exact21_records_and_exact29_bundle(formal_runs):
    bundle = formal_runs[0]
    assert len(bundle) == 29
    assert tuple(bundle) == gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_BUNDLE_FIELDS
    assert tuple(bundle["target_residue_atom_condition_adapter_gate_record_fields"]) == (
        gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS
    )
    for record in bundle["target_residue_atom_condition_adapter_gate_records"]:
        assert len(record) == 21
        assert tuple(record) == gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS


def test_record_and_bundle_digests_are_canonical(formal_runs):
    bundle = formal_runs[0]
    for record in bundle["target_residue_atom_condition_adapter_gate_records"]:
        assert record["target_residue_atom_condition_adapter_gate_record_sha256"] == (
            gate._digest_record(
                record,
                gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS,
                "target_residue_atom_condition_adapter_gate_record_sha256",
            )
        )
    assert bundle["target_residue_atom_condition_adapter_gate_bundle_sha256"] == (
        gate._digest_record(
            bundle,
            gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_BUNDLE_FIELDS,
            "target_residue_atom_condition_adapter_gate_bundle_sha256",
        )
    )


def test_formal_gate_is_deterministic_and_inputs_are_unchanged(formal_runs):
    first, second, snapshots, original_sources = formal_runs
    assert first == second
    assert gate._bundle_bytes(first) == gate._bundle_bytes(second)
    assert original_sources == snapshots


def test_result_has_no_path_objects(formal_runs):
    assert not any(isinstance(value, Path) for value in gate._walk_values(formal_runs[0]))


def test_all_current11_runtime_sample_contract(formal_runs):
    bundle = formal_runs[0]
    records = bundle["target_residue_atom_condition_adapter_gate_records"]
    assert bundle["sample_order"] == [
        f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
    ]
    assert bundle["target_residue_atom_condition_adapter_gate_record_count"] == 11
    assert bundle["runtime_dataset_sample_count"] == 11
    assert bundle["total_runtime_pocket_node_count"] == 2202
    assert bundle["total_runtime_indicator_true_count"] == 11
    assert [record["target_retained_model_local_index"] for record in records] == list(
        EXPECTED_LOCAL
    )
    assert all(record["runtime_loaded_indicator_torch_dtype"] == "torch.bool" for record in records)
    assert all(record["runtime_loaded_indicator_true_count"] == 1 for record in records)
    assert all(record["runtime_pocket_one_hot_width"] == 10 for record in records)
    assert all(record["runtime_target_atom_feature_index"] == 3 for record in records)


def test_real_collate_flat_indices_and_order(formal_runs):
    bundle = formal_runs[0]
    records = bundle["target_residue_atom_condition_adapter_gate_records"]
    prefix = 0
    derived = []
    for record in records:
        assert record["collated_flat_start_index"] == prefix
        prefix += record["retained_pocket_node_count"]
        assert record["collated_flat_end_index_exclusive"] == prefix
        derived.append(
            record["collated_flat_start_index"]
            + record["target_retained_model_local_index"]
        )
    assert tuple(derived) == EXPECTED_FLAT
    assert [record["collated_flat_true_index"] for record in records] == list(EXPECTED_FLAT)
    assert bundle["collated_indicator_length"] == 2202
    assert bundle["collated_indicator_true_count"] == 11


def test_centered_indicator_and_temporary_npz_contract(formal_runs):
    bundle = formal_runs[0]
    assert all(
        record["centered_runtime_indicator_unchanged"] is True
        for record in bundle["target_residue_atom_condition_adapter_gate_records"]
    )
    assert bundle["temporary_npz_created"] is True
    assert bundle["temporary_npz_cleaned"] is True
    assert bundle["persistent_npz_created"] is False


def test_retained_tables_coordinates_one_hot_and_sulfur_are_rebuilt(sources):
    authority_bytes, alignment_bytes, _adapter_bytes = sources
    compiled = alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1(
        source_authority_bundle=authority_bytes, repo_root=ROOT
    )
    assert alignment._bundle_bytes(compiled) == alignment_bytes
    symbol_to_index = alignment._checkpoint_symbol_to_index()
    assert symbol_to_index["S"] == 3
    for record in compiled["pocket_atom_identity_alignment_records"]:
        payload = alignment._read_regular(ROOT, record["source_pocket_atom_table_path"])
        assert hashlib.sha256(payload).hexdigest() == record["source_pocket_atom_table_sha256"]
        _fields, rows = alignment._csv_rows(payload)
        indices = record["retained_source_pocket_row_indices"]
        assert indices == sorted(indices)
        retained = [rows[index] for index in indices]
        coordinate_bytes = alignment._float32_bytes(retained)
        one_hot_bytes = alignment._one_hot_float32_bytes(retained, symbol_to_index)
        assert hashlib.sha256(coordinate_bytes).hexdigest() == (
            record["retained_pocket_coordinate_float32_bytes_sha256"]
        )
        assert hashlib.sha256(one_hot_bytes).hexdigest() == (
            record["retained_pocket_one_hot_bytes_sha256"]
        )
        matrix = np.frombuffer(one_hot_bytes, dtype="<f4").reshape(-1, 10)
        target = record["target_retained_model_local_index"]
        assert retained[target]["type_symbol"] == "S"
        assert matrix[target, 3] == 1.0


def test_transport_drift_fails_closed(sources):
    authority_bytes, alignment_bytes, adapter_bytes = sources
    variants = (
        (authority_bytes + b" ", alignment_bytes, adapter_bytes),
        (authority_bytes, alignment_bytes + b" ", adapter_bytes),
        (authority_bytes, alignment_bytes, adapter_bytes + b" "),
    )
    for authority_variant, alignment_variant, adapter_variant in variants:
        _assert_canonical_error(
            lambda a=authority_variant, l=alignment_variant, d=adapter_variant: (
                gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
                    source_authority_bundle=a,
                    source_alignment_bundle=l,
                    source_adapter_bundle=d,
                    repo_root=ROOT,
                )
            )
        )


def test_adapter_exact_bytes_mismatch_fails_closed(monkeypatch, sources):
    authority_bytes, alignment_bytes, adapter_bytes = sources
    changed = adapter_bytes + b" "
    monkeypatch.setattr(gate, "_ADAPTER_TRANSPORT_SHA256", hashlib.sha256(changed).hexdigest())
    _assert_canonical_error(
        lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
            source_authority_bundle=authority_bytes,
            source_alignment_bundle=alignment_bytes,
            source_adapter_bundle=changed,
            repo_root=ROOT,
        )
    )


def test_gate_bundle_rejects_record_digest_order_and_sample_drift(formal_runs):
    source = formal_runs[0]
    mutations = []
    record_digest = deepcopy(source)
    record_digest["target_residue_atom_condition_adapter_gate_records"][0][
        "source_adapter_record_sha256"
    ] = "0" * 64
    mutations.append(record_digest)
    alignment_digest = deepcopy(source)
    alignment_digest["target_residue_atom_condition_adapter_gate_records"][0][
        "source_alignment_record_sha256"
    ] = "0" * 64
    mutations.append(alignment_digest)
    sample_order = deepcopy(source)
    sample_order["sample_order"][0], sample_order["sample_order"][1] = (
        sample_order["sample_order"][1],
        sample_order["sample_order"][0],
    )
    mutations.append(sample_order)
    for mutation in mutations:
        _assert_canonical_error(lambda value=mutation: gate._validate_gate_bundle(value, require_field_order=True))


def test_record_validator_rejects_indicator_runtime_faults(formal_runs):
    source = formal_runs[0]["target_residue_atom_condition_adapter_gate_records"][0]
    changes = (
        ("runtime_loaded_indicator_length", source["runtime_loaded_indicator_length"] - 1),
        ("runtime_loaded_indicator_true_count", 0),
        ("runtime_loaded_indicator_true_count", 2),
        ("runtime_loaded_indicator_torch_dtype", "torch.uint8"),
        ("runtime_loaded_indicator_true_index", 0),
        ("runtime_target_atom_feature_index", 2),
        ("runtime_pocket_one_hot_width", 9),
    )
    for field, value in changes:
        record = deepcopy(source)
        record[field] = value
        _rehash_record(
            record,
            gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS,
            "target_residue_atom_condition_adapter_gate_record_sha256",
        )
        _assert_canonical_error(lambda item=record: gate._validate_gate_record(item, require_field_order=True))


def test_runtime_source_sha_drifts_fail_closed(monkeypatch, sources):
    authority_bytes, alignment_bytes, adapter_bytes = sources
    for constant in (
        "_DATASET_MODULE_SHA256",
        "_LIGHTNING_MODULE_SHA256",
        "_CHECKPOINT_SHA256",
        "_ADAPTER_PRODUCTION_SHA256",
    ):
        with monkeypatch.context() as patch:
            patch.setattr(gate, constant, "0" * 64)
            _assert_canonical_error(
                lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
                    source_authority_bundle=authority_bytes,
                    source_alignment_bundle=alignment_bytes,
                    source_adapter_bundle=adapter_bytes,
                    repo_root=ROOT,
                )
            )


def test_all_failures_use_the_canonical_value_error(sources, tmp_path):
    authority_bytes, alignment_bytes, adapter_bytes = sources
    invalid_calls = (
        lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
            source_authority_bundle=bytearray(authority_bytes),
            source_alignment_bundle=alignment_bytes,
            source_adapter_bundle=adapter_bytes,
            repo_root=ROOT,
        ),
        lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
            source_authority_bundle=authority_bytes,
            source_alignment_bundle=alignment_bytes,
            source_adapter_bundle=adapter_bytes,
            repo_root=str(ROOT),
        ),
        lambda: gate._materialize_covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1(
            source_authority_bundle=authority_bytes,
            source_alignment_bundle=alignment_bytes,
            source_adapter_bundle=adapter_bytes,
            repo_root=ROOT,
            output_path=str(tmp_path / "bad.json"),
        ),
    )
    for invalid_call in invalid_calls:
        _assert_canonical_error(invalid_call)


def test_publication_new_then_exact_existing_is_metadata_stable(sources, tmp_path):
    authority_bytes, alignment_bytes, adapter_bytes = sources
    target = tmp_path / "gate.json"
    first = gate._materialize_covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1(
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        source_adapter_bundle=adapter_bytes,
        repo_root=ROOT,
        output_path=target,
    )
    before = target.stat()
    payload = target.read_bytes()
    second = gate._materialize_covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1(
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        source_adapter_bundle=adapter_bytes,
        repo_root=ROOT,
        output_path=target,
    )
    after = target.stat()
    assert first["publication_mode"] == "published_new"
    assert second["publication_mode"] == "idempotent_existing"
    assert before.st_ino == after.st_ino
    assert before.st_mtime_ns == after.st_mtime_ns
    assert target.read_bytes() == payload
    assert stat.S_IMODE(after.st_mode) == 0o644
    assert after.st_nlink == 1
    assert not target.is_symlink()
    assert not payload.endswith(b"\n")
    assert gate._canonical_json_bytes(json.loads(payload)) == payload


def test_publication_rejects_symlink_and_conflict_without_overwrite(sources, tmp_path):
    authority_bytes, alignment_bytes, adapter_bytes = sources
    unknown = tmp_path / "unknown.txt"
    unknown.write_bytes(b"unknown")
    symlink = tmp_path / "symlink.json"
    symlink.symlink_to(unknown)
    conflict = tmp_path / "conflict.json"
    conflict.write_bytes(b"conflict")
    before_unknown = unknown.read_bytes()
    before_conflict = conflict.read_bytes()
    for target in (symlink, conflict):
        _assert_canonical_error(
            lambda path=target: gate._materialize_covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1(
                source_authority_bundle=authority_bytes,
                source_alignment_bundle=alignment_bytes,
                source_adapter_bundle=adapter_bytes,
                repo_root=ROOT,
                output_path=path,
            )
        )
    assert unknown.read_bytes() == before_unknown
    assert conflict.read_bytes() == before_conflict
    assert symlink.is_symlink()


def test_runtime_bridge_and_training_boundaries_remain_closed(formal_runs):
    bundle = formal_runs[0]
    assert bundle["ready_for_runtime_bridge_design"] is True
    assert bundle["recommended_next_step"] == (
        "design_covapie_target_residue_atom_condition_runtime_bridge_v1"
    )
    assert bundle["feature_semantics_audit_required_before_training"] is True
    assert b"pocket_target_residue_atom_condition_indicator" not in (
        ROOT / "lightning_modules.py"
    ).read_bytes()


def test_collated_pocket_node_order_drift_is_rejected(monkeypatch, sources):
    authority_bytes, alignment_bytes, adapter_bytes = sources
    runtime_dataset_class = gate._load_dataset_class(ROOT)

    def reordered_dataset_class(*, reverse_coordinates: bool):
        class ReorderedCollateDataset(runtime_dataset_class):
            @staticmethod
            def collate_fn(batch):
                collated = runtime_dataset_class.collate_fn(batch)
                original_indicator = collated[gate._FIELD].clone()
                original_names = list(collated["names"])
                original_receptors = list(collated["receptors"])
                original_counts = collated["num_pocket_nodes"].clone()
                if reverse_coordinates:
                    collated["pocket_coords"] = torch.flip(
                        collated["pocket_coords"], dims=(0,)
                    )
                collated["pocket_one_hot"] = torch.flip(
                    collated["pocket_one_hot"], dims=(0,)
                )
                assert torch.equal(collated[gate._FIELD], original_indicator)
                assert collated["names"] == original_names
                assert collated["receptors"] == original_receptors
                assert torch.equal(collated["num_pocket_nodes"], original_counts)
                return collated

        return ReorderedCollateDataset

    for reverse_coordinates in (True, False):
        with monkeypatch.context() as patch:
            wrapper = reordered_dataset_class(reverse_coordinates=reverse_coordinates)
            patch.setattr(gate, "_load_dataset_class", lambda _repo_root: wrapper)
            _assert_canonical_error(
                lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
                    source_authority_bundle=authority_bytes,
                    source_alignment_bundle=alignment_bytes,
                    source_adapter_bundle=adapter_bytes,
                    repo_root=ROOT,
                )
            )


def test_checker_runs_the_formal_public_gate_and_reports_required_boundaries():
    completed = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "scripts/check_covapie_target_residue_atom_condition_adapter_gate_v1.py"
            ),
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stderr == ""
    required = (
        "source_adapter_bundle_recompiled_exact=true",
        "gate_record_count=11",
        "total_runtime_pocket_node_count=2202",
        "collated_flat_true_indices_valid=true",
        "collated_pocket_coords_order_preserved=true",
        "collated_pocket_one_hot_order_preserved=true",
        "collated_true_indices_target_s_feature_valid=true",
        "centered_pocket_one_hot_unchanged=true",
        "collated_pocket_node_order_drift_rejected=true",
        "centered_indicator_unchanged_count=11",
        "temporary_npz_cleaned=true",
        "persistent_files_written=false",
        "indicator_passed_into_model=false",
        "training_or_parameter_update=false",
        "target_residue_atom_condition_adapter_gate_bundle_sha256=",
    )
    assert all(line in completed.stdout for line in required)
