from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from covalent_ext import covapie_current11_pocket_atom_identity_alignment_v1 as alignment
from covalent_ext import covapie_target_residue_atom_condition_adapter_design_v1 as design
from covalent_ext import covapie_target_residue_atom_condition_adapter_v1 as adapter


REPO_ROOT = Path(__file__).resolve().parents[1]
_DATASET_SPEC = importlib.util.spec_from_file_location("covapie_base_dataset", REPO_ROOT / "dataset.py")
assert _DATASET_SPEC is not None and _DATASET_SPEC.loader is not None
_DATASET_MODULE = importlib.util.module_from_spec(_DATASET_SPEC)
_DATASET_SPEC.loader.exec_module(_DATASET_MODULE)
ProcessedLigandPocketDataset = _DATASET_MODULE.ProcessedLigandPocketDataset
STATE_ROOT = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-state/manual-review"
)
AUTHORITY_PATH = STATE_ROOT / (
    "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
)
ALIGNMENT_PATH = STATE_ROOT / "covapie_current11_pocket_atom_identity_alignment_bundle_v1.json"
FIELD = "pocket_target_residue_atom_condition_indicator"


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")


@pytest.fixture(scope="module")
def authority_bytes() -> bytes:
    return AUTHORITY_PATH.read_bytes()


@pytest.fixture(scope="module")
def alignment_bytes() -> bytes:
    return ALIGNMENT_PATH.read_bytes()


@pytest.fixture(scope="module")
def formal_alignment(authority_bytes: bytes) -> dict[str, Any]:
    return alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1(
        source_authority_bundle=authority_bytes, repo_root=REPO_ROOT
    )


@pytest.fixture(scope="module")
def formal_bundle(authority_bytes: bytes, alignment_bytes: bytes) -> dict[str, Any]:
    return adapter.build_covapie_target_residue_atom_condition_adapter_v1(
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        repo_root=REPO_ROOT,
    )


@pytest.fixture(scope="module")
def authority_records(authority_bytes: bytes) -> list[dict[str, Any]]:
    return json.loads(authority_bytes)["target_residue_atom_condition_records"]


def _resign_adapter_record(record: dict[str, Any]) -> None:
    record["target_residue_atom_condition_adapter_record_sha256"] = adapter._digest_record(
        record,
        adapter.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS,
        "target_residue_atom_condition_adapter_record_sha256",
    )


def _resign_bundle(bundle: dict[str, Any]) -> None:
    bundle["target_residue_atom_condition_adapter_bundle_sha256"] = adapter._digest_record(
        bundle,
        adapter.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS,
        "target_residue_atom_condition_adapter_bundle_sha256",
    )


def _assert_error(callable_: object, *args: object, **kwargs: object) -> None:
    with pytest.raises(ValueError, match=f"^{adapter._ERROR}$"):
        callable_(*args, **kwargs)  # type: ignore[operator]


def test_public_signature_all_and_silent_import() -> None:
    signature = inspect.signature(
        adapter.build_covapie_target_residue_atom_condition_adapter_v1
    )
    assert tuple(signature.parameters) == (
        "source_authority_bundle",
        "source_alignment_bundle",
        "repo_root",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert adapter.__all__ == (
        "build_covapie_target_residue_atom_condition_adapter_v1",
    )
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(REPO_ROOT / "src"))
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "import covalent_ext.covapie_target_residue_atom_condition_adapter_v1",
        ],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_frozen_source_lineage_and_exact_recompilation(
    authority_bytes: bytes,
    alignment_bytes: bytes,
    formal_alignment: dict[str, Any],
    formal_bundle: dict[str, Any],
) -> None:
    assert _sha(authority_bytes) == adapter._AUTHORITY_TRANSPORT_SHA256
    assert _sha(alignment_bytes) == adapter._ALIGNMENT_TRANSPORT_SHA256
    assert alignment._bundle_bytes(formal_alignment) == alignment_bytes
    assert _sha(Path(alignment.__file__).read_bytes()) == adapter._ALIGNMENT_PRODUCTION_SHA256
    assert _sha(Path(design.__file__).read_bytes()) == adapter._ADAPTER_DESIGN_PRODUCTION_SHA256
    assert formal_bundle["source_authority_bundle_sha256"] == adapter._AUTHORITY_INTERNAL_SHA256
    assert formal_bundle["source_alignment_bundle_sha256"] == adapter._ALIGNMENT_INTERNAL_SHA256
    assert (
        formal_bundle["source_adapter_design_response_sha256"]
        == adapter._ADAPTER_DESIGN_RESPONSE_SHA256
    )


def test_canonical_five_mask_contract(formal_bundle: dict[str, Any]) -> None:
    expected = (
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    )
    assert adapter.CANONICAL_MASK_SEMANTIC_NAMES == expected
    assert tuple(formal_bundle["canonical_mask_semantic_names"]) == expected
    assert design.CANONICAL_MASK_SEMANTIC_NAMES == expected


def test_exact20_indicator_and_record_digests(formal_bundle: dict[str, Any]) -> None:
    records = formal_bundle["target_residue_atom_condition_adapter_records"]
    assert len(records) == 11
    expected_indices = (49, 15, 12, 33, 31, 50, 48, 53, 52, 53, 84)
    for record, expected_index in zip(records, expected_indices):
        assert tuple(record) == adapter.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS
        assert len(record) == 20
        indicator = record[FIELD]
        assert type(indicator) is list
        assert all(type(value) is bool for value in indicator)
        assert len(indicator) == record["retained_pocket_node_count"]
        assert record["indicator_length"] == len(indicator)
        assert record["indicator_true_count"] == 1
        assert [index for index, value in enumerate(indicator) if value] == [expected_index]
        assert record["target_retained_model_local_index"] == expected_index
        assert record["indicator_uint8_bytes_sha256"] == _sha(
            bytes(1 if value else 0 for value in indicator)
        )
        unsigned = {
            key: value
            for key, value in record.items()
            if key != "target_residue_atom_condition_adapter_record_sha256"
        }
        assert record["target_residue_atom_condition_adapter_record_sha256"] == _sha(
            _canonical(unsigned)
        )
        assert not {"pocket_coords", "pocket_one_hot", "target_xyz", "target_atom_one_hot"} & set(record)


def test_record_lineage_matches_authority_and_alignment(
    formal_bundle: dict[str, Any],
    formal_alignment: dict[str, Any],
    authority_records: list[dict[str, Any]],
) -> None:
    records = formal_bundle["target_residue_atom_condition_adapter_records"]
    alignment_records = formal_alignment["pocket_atom_identity_alignment_records"]
    for record, authority_record, alignment_record in zip(
        records, authority_records, alignment_records
    ):
        assert record["sample_index_row_id"] == authority_record["sample_index_row_id"]
        assert record["pdb_id"] == authority_record["pdb_id"]
        assert record["source_authority_record_sha256"] == authority_record[
            "target_residue_atom_condition_record_sha256"
        ]
        assert record["source_condition_evidence_sha256"] == authority_record[
            "source_condition_evidence_sha256"
        ]
        assert record["source_alignment_record_sha256"] == alignment_record[
            "pocket_atom_identity_alignment_record_sha256"
        ]
        assert record["source_atom_site_id"] == authority_record["source_atom_site_id"]


def test_exact21_bundle_aggregates_and_digest(formal_bundle: dict[str, Any]) -> None:
    assert tuple(formal_bundle) == adapter.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS
    assert len(formal_bundle) == 21
    assert formal_bundle["target_residue_atom_condition_adapter_record_count"] == 11
    assert formal_bundle["total_indicator_length"] == 2202
    assert formal_bundle["total_indicator_true_count"] == 11
    assert formal_bundle["all_records_adapter_ready_unique"] is True
    assert formal_bundle["ready_for_adapter_gate"] is True
    assert formal_bundle["recommended_next_step"] == (
        "implement_covapie_target_residue_atom_condition_adapter_gate_v1"
    )
    assert formal_bundle["feature_semantics_audit_required_before_training"] is True
    unsigned = {
        key: value
        for key, value in formal_bundle.items()
        if key != "target_residue_atom_condition_adapter_bundle_sha256"
    }
    assert formal_bundle["target_residue_atom_condition_adapter_bundle_sha256"] == _sha(
        _canonical(unsigned)
    )
    assert adapter._bundle_bytes(formal_bundle) == _canonical(formal_bundle)


def test_deterministic_inputs_unchanged_zero_writes_and_no_paths(
    authority_bytes: bytes, alignment_bytes: bytes, formal_bundle: dict[str, Any]
) -> None:
    authority_before = bytes(authority_bytes)
    alignment_before = bytes(alignment_bytes)
    untracked_before = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    second = adapter.build_covapie_target_residue_atom_condition_adapter_v1(
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        repo_root=REPO_ROOT,
    )
    untracked_after = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert second == formal_bundle
    assert authority_bytes == authority_before and alignment_bytes == alignment_before
    assert untracked_after == untracked_before

    def contains_path(value: object) -> bool:
        if isinstance(value, Path):
            return True
        if isinstance(value, dict):
            return any(contains_path(item) for item in value.values())
        if isinstance(value, (list, tuple)):
            return any(contains_path(item) for item in value)
        return False

    assert not contains_path(second)


def test_authority_and_alignment_transport_drift_rejected(
    authority_bytes: bytes, alignment_bytes: bytes
) -> None:
    _assert_error(
        adapter.build_covapie_target_residue_atom_condition_adapter_v1,
        source_authority_bundle=authority_bytes + b" ",
        source_alignment_bundle=alignment_bytes,
        repo_root=REPO_ROOT,
    )
    _assert_error(
        adapter.build_covapie_target_residue_atom_condition_adapter_v1,
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes + b" ",
        repo_root=REPO_ROOT,
    )


def test_alignment_must_equal_compiler_canonical_bytes(
    authority_bytes: bytes,
    alignment_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    drift = alignment_bytes + b" "
    monkeypatch.setattr(adapter, "_ALIGNMENT_TRANSPORT_SHA256", _sha(drift))
    _assert_error(
        adapter.build_covapie_target_residue_atom_condition_adapter_v1,
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=drift,
        repo_root=REPO_ROOT,
    )


def test_alignment_record_digest_sequence_drift_rejected(
    authority_bytes: bytes,
    alignment_bytes: bytes,
    formal_alignment: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    drifted = copy.deepcopy(formal_alignment)
    drifted["pocket_atom_identity_alignment_records"][0][
        "pocket_atom_identity_alignment_record_sha256"
    ] = _sha(b"drift")
    monkeypatch.setattr(
        adapter.alignment,
        "compile_covapie_current11_pocket_atom_identity_alignment_v1",
        lambda **_kwargs: drifted,
    )
    monkeypatch.setattr(adapter.alignment, "_bundle_bytes", lambda _bundle: alignment_bytes)
    _assert_error(
        adapter.build_covapie_target_residue_atom_condition_adapter_v1,
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        repo_root=REPO_ROOT,
    )


def test_source_production_hash_drift_rejected(
    authority_bytes: bytes,
    alignment_bytes: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    drift = tmp_path / "drift.py"
    drift.write_bytes(b"drift")
    monkeypatch.setattr(adapter.adapter_design, "__file__", str(drift))
    _assert_error(
        adapter.build_covapie_target_residue_atom_condition_adapter_v1,
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        repo_root=REPO_ROOT,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("retained_pocket_node_count", 0),
        ("target_retained_model_local_index", -1),
        ("target_retained", False),
        ("target_indicator_true_count", 0),
        ("alignment_status", "blocked_projection_invariant"),
        ("pocket_row_order_binding_status", "unbound"),
    ),
)
def test_alignment_preconditions_fail_closed(
    field: str,
    value: object,
    authority_records: list[dict[str, Any]],
    formal_alignment: dict[str, Any],
) -> None:
    record = copy.deepcopy(formal_alignment["pocket_atom_identity_alignment_records"][0])
    record[field] = value
    _assert_error(
        adapter._build_adapter_record,
        authority_record=authority_records[0],
        alignment_record=record,
    )


def test_target_index_out_of_range_rejected(
    authority_records: list[dict[str, Any]], formal_alignment: dict[str, Any]
) -> None:
    record = copy.deepcopy(formal_alignment["pocket_atom_identity_alignment_records"][0])
    record["target_retained_model_local_index"] = record["retained_pocket_node_count"]
    _assert_error(
        adapter._build_adapter_record,
        authority_record=authority_records[0],
        alignment_record=record,
    )


@pytest.mark.parametrize("kind", ("zero", "multiple", "non_bool"))
def test_invalid_indicator_values_rejected(kind: str, formal_bundle: dict[str, Any]) -> None:
    record = copy.deepcopy(formal_bundle["target_residue_atom_condition_adapter_records"][0])
    indicator = record[FIELD]
    true_index = record["target_retained_model_local_index"]
    if kind == "zero":
        indicator[true_index] = False
    elif kind == "multiple":
        indicator[0 if true_index != 0 else 1] = True
    else:
        indicator[0 if true_index != 0 else 1] = 0
    _assert_error(adapter._validate_adapter_record, record, require_field_order=True)


def test_sample_order_duplicate_sample_and_duplicate_alignment_lineage_rejected(
    formal_bundle: dict[str, Any]
) -> None:
    sample_order = copy.deepcopy(formal_bundle)
    sample_order["sample_order"][0], sample_order["sample_order"][1] = (
        sample_order["sample_order"][1],
        sample_order["sample_order"][0],
    )
    _resign_bundle(sample_order)
    _assert_error(adapter._validate_adapter_bundle, sample_order, require_field_order=True)

    duplicate_sample = copy.deepcopy(formal_bundle)
    duplicate_sample["target_residue_atom_condition_adapter_records"][1][
        "sample_index_row_id"
    ] = duplicate_sample["target_residue_atom_condition_adapter_records"][0][
        "sample_index_row_id"
    ]
    _resign_adapter_record(duplicate_sample["target_residue_atom_condition_adapter_records"][1])
    _resign_bundle(duplicate_sample)
    _assert_error(adapter._validate_adapter_bundle, duplicate_sample, require_field_order=True)

    duplicate_lineage = copy.deepcopy(formal_bundle)
    duplicate_lineage["target_residue_atom_condition_adapter_records"][1][
        "source_alignment_record_sha256"
    ] = duplicate_lineage["target_residue_atom_condition_adapter_records"][0][
        "source_alignment_record_sha256"
    ]
    _resign_adapter_record(duplicate_lineage["target_residue_atom_condition_adapter_records"][1])
    _resign_bundle(duplicate_lineage)
    _assert_error(adapter._validate_adapter_bundle, duplicate_lineage, require_field_order=True)


def test_temporary_npz_dataset_split_and_collate_contract(tmp_path: Path) -> None:
    npz_path = tmp_path / "synthetic_adapter_runtime.npz"
    indicator = np.array([False, True, False, True, False, False, False], dtype=np.bool_)
    pocket_one_hot = np.zeros((7, 10), dtype=np.float32)
    pocket_one_hot[np.arange(7), np.arange(7)] = 1.0
    np.savez(
        npz_path,
        names=np.array(["sample-a", "sample-b"]),
        receptors=np.array(["receptor-a", "receptor-b"]),
        lig_mask=np.array([0, 0, 1, 1], dtype=np.int64),
        pocket_mask=np.array([0, 0, 0, 1, 1, 1, 1], dtype=np.int64),
        lig_coords=np.zeros((4, 3), dtype=np.float32),
        pocket_coords=np.zeros((7, 3), dtype=np.float32),
        lig_one_hot=np.zeros((4, 10), dtype=np.float32),
        pocket_one_hot=pocket_one_hot,
        pocket_target_residue_atom_condition_indicator=indicator,
    )
    dataset = ProcessedLigandPocketDataset(npz_path, center=False)
    first, second = dataset[0], dataset[1]
    assert first[FIELD].dtype == second[FIELD].dtype == torch.bool
    assert first[FIELD].tolist() == [False, True, False]
    assert second[FIELD].tolist() == [True, False, False, False]
    assert first["num_pocket_nodes"].item() == len(first[FIELD]) == 3
    assert second["num_pocket_nodes"].item() == len(second[FIELD]) == 4
    collated = ProcessedLigandPocketDataset.collate_fn([first, second])
    assert collated[FIELD].dtype == torch.bool
    assert tuple(collated[FIELD].shape) == (7,)
    assert collated[FIELD].tolist() == indicator.tolist()
    assert collated[FIELD].tolist() != [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]
    assert tuple(collated["pocket_one_hot"].shape) == (7, 10)
    assert collated["num_pocket_nodes"].tolist() == [3, 4]
    npz_path.unlink()
    assert not npz_path.exists()


def test_field_naming_checkpoint_and_model_compatibility() -> None:
    assert "lig" not in FIELD and "mask" not in FIELD
    assert _sha((REPO_ROOT / "dataset.py").read_bytes()) == (
        "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99"
    )
    lightning = (REPO_ROOT / "lightning_modules.py").read_bytes()
    assert _sha(lightning) == "2b771068eda19b6f783e12ff483a02ab6ef8264108f3af5e486d3381fb1e7fb6"
    assert FIELD.encode() not in lightning
    decision = design._checkpoint_decision()
    assert decision["append_to_pocket_one_hot"] is False
    assert decision["change_atom_nf"] is False
    assert decision["change_residue_nf"] is False
    assert decision["change_joint_nf"] is False
    assert decision["modify_EGNNDynamics"] is False
    assert decision["modify_ConditionalDDPM"] is False
    assert decision["modify_LigandPocketDDPM"] is False
    assert decision["new_base_model_parameter"] is False
    assert decision["base_state_dict_key_change"] is False
    assert decision["base_checkpoint_tensor_shape_change"] is False


def test_materializer_published_new_then_exact_existing_idempotent(
    authority_bytes: bytes, alignment_bytes: bytes, tmp_path: Path
) -> None:
    output = tmp_path / "bundle.json"
    first = adapter._materialize_covapie_current11_target_residue_atom_condition_adapter_bundle_v1(
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        repo_root=REPO_ROOT,
        output_path=output,
    )
    before = output.stat()
    first_bytes = output.read_bytes()
    second = adapter._materialize_covapie_current11_target_residue_atom_condition_adapter_bundle_v1(
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        repo_root=REPO_ROOT,
        output_path=output,
    )
    after = output.stat()
    assert first["publication_mode"] == "published_new"
    assert second["publication_mode"] == "idempotent_existing"
    assert before.st_ino == after.st_ino
    assert before.st_mtime_ns == after.st_mtime_ns
    assert output.read_bytes() == first_bytes
    assert stat.S_IMODE(after.st_mode) == 0o644 and after.st_nlink == 1
    assert first_bytes == _canonical(json.loads(first_bytes))
    assert not first_bytes.startswith(b"\xef\xbb\xbf")
    assert b"\x00" not in first_bytes and not first_bytes.endswith((b"\n", b"\r"))


def test_materializer_rejects_symlink_and_conflict_without_overwrite(
    authority_bytes: bytes, alignment_bytes: bytes, tmp_path: Path
) -> None:
    unknown = tmp_path / "unknown"
    unknown.write_bytes(b"unknown")
    output = tmp_path / "bundle.json"
    output.symlink_to(unknown)
    _assert_error(
        adapter._materialize_covapie_current11_target_residue_atom_condition_adapter_bundle_v1,
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        repo_root=REPO_ROOT,
        output_path=output,
    )
    output.unlink()
    output.write_bytes(b"conflict")
    _assert_error(
        adapter._materialize_covapie_current11_target_residue_atom_condition_adapter_bundle_v1,
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        repo_root=REPO_ROOT,
        output_path=output,
    )
    assert output.read_bytes() == b"conflict"
    assert unknown.read_bytes() == b"unknown"


def test_publication_failure_does_not_delete_unknown_file(
    authority_bytes: bytes,
    alignment_bytes: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "bundle.json"
    unknown = tmp_path / "keep.me"
    unknown.write_bytes(b"keep")

    def fail_link(*_args: object, **_kwargs: object) -> None:
        raise OSError("synthetic publication failure")

    monkeypatch.setattr(adapter.os, "link", fail_link)
    _assert_error(
        adapter._materialize_covapie_current11_target_residue_atom_condition_adapter_bundle_v1,
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        repo_root=REPO_ROOT,
        output_path=output,
    )
    assert not output.exists()
    assert unknown.read_bytes() == b"keep"
    assert list(tmp_path.glob(".*.tmp")) == []


def test_no_training_tensor_npz_label_or_protected_source_change() -> None:
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert not any(
        Path(path).suffix
        in {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz"}
        for path in untracked
    )
    protected = (
        "dataset.py",
        "lightning_modules.py",
        "equivariant_diffusion",
        "data/prepare_crossdocked.py",
    )
    assert subprocess.run(
        ["git", "diff", "--quiet", "--", *protected], cwd=REPO_ROOT, check=False
    ).returncode == 0
    assert subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *protected],
        cwd=REPO_ROOT,
        check=False,
    ).returncode == 0
