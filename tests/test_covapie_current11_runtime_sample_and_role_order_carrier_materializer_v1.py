from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import io
import json
import os
import shutil
import stat
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest
import torch

from covalent_ext import covapie_current11_runtime_sample_and_role_order_carrier_materializer_v1 as materializer


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_STATE = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/covapie-state"
)
ROUTING_NAME = "current11-dataset-partial-supervision-routing-sidecar-v1"
EXPECTED_NPZ_SHA256 = "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"
EXPECTED_AGGREGATE = "ef426a6d8dee9678ac15dd62b191e9ef9cfb436a01660bd941bd24392dfa9a18"
EXPECTED_LENGTHS = {
    "lig": [13, 13, 13, 25, 28, 43, 42, 42, 43, 40, 21],
    "pocket": [66, 104, 96, 208, 188, 278, 267, 257, 249, 261, 228],
}


def _copy_regular(source: Path, target: Path) -> None:
    assert source.is_file() and not source.is_symlink()
    with source.open("rb") as reader, target.open("xb") as writer:
        shutil.copyfileobj(reader, writer)
    target.chmod(stat.S_IMODE(source.stat().st_mode))
    assert source.stat().st_ino != target.stat().st_ino


def _state_mirror(root: Path) -> Path:
    state = root / "state-mirror"
    formal = state / "formal-sidecars"
    formal.mkdir(parents=True, mode=0o755)
    source_canonical = REAL_STATE / "formal-sidecars" / ROUTING_NAME
    link = os.readlink(source_canonical)
    source_object = source_canonical.parent / link
    target_object = formal / link
    target_object.mkdir(mode=stat.S_IMODE(source_object.stat().st_mode))
    for source in source_object.iterdir():
        _copy_regular(source, target_object / source.name)
    os.symlink(link, formal / ROUTING_NAME, target_is_directory=True)
    assert not (formal / materializer._CANONICAL_BASENAME).exists()
    assert not (formal / materializer._CANONICAL_BASENAME).is_symlink()
    return state


@pytest.fixture(scope="session")
def candidate() -> dict[str, bytes]:
    return materializer._build_candidate_bundle(
        repo_root=REPO_ROOT, state_root=REAL_STATE
    )


def _candidate_arrays(candidate: dict[str, bytes]) -> dict[str, np.ndarray]:
    with np.load(io.BytesIO(candidate[materializer._NPZ]), allow_pickle=False) as archive:
        return {name: archive[name].copy() for name in archive.files}


def _manifest_validation_inputs(
    candidate: dict[str, bytes],
) -> tuple[dict[str, object], dict[str, object], dict[str, np.ndarray], list[dict[str, str]]]:
    manifest = json.loads(candidate[materializer._MANIFEST])
    schema = materializer._expected_published_carrier_schema()
    arrays = _candidate_arrays(candidate)
    samples = [
        {"sample_index_row_id": sample, "pdb_id": receptor}
        for sample, receptor in zip(
            materializer._EXPECTED_SAMPLE_IDS, materializer._EXPECTED_RECEPTORS
        )
    ]
    return manifest, schema, arrays, samples


def _validate_manifest_inputs(
    manifest: dict[str, object],
    schema: dict[str, object],
    arrays: dict[str, np.ndarray],
    samples: list[dict[str, str]],
) -> None:
    materializer._validate_manifest_instance_against_published_schema(
        manifest=manifest,
        carrier_schema=schema,
        arrays=arrays,
        samples=samples,
        expected_runtime_artifact_sha256=EXPECTED_NPZ_SHA256,
    )


def _publish_with_candidate(
    monkeypatch: pytest.MonkeyPatch,
    state: Path,
    candidate: dict[str, bytes],
) -> dict[str, object]:
    monkeypatch.setattr(
        materializer,
        "_build_candidate_bundle",
        lambda *, repo_root, state_root: dict(candidate),
    )
    return materializer.materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
        repo_root=REPO_ROOT, state_root=state
    )


def test_public_surface_and_import_boundary() -> None:
    assert materializer.__all__ == (
        "materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1",
    )
    assert callable(
        materializer.materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1
    )
    assert materializer._build_candidate_bundle.__name__.startswith("_")
    assert materializer._verify_existing.__name__.startswith("_")
    source = (REPO_ROOT / materializer._MODULE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert not imports.intersection(
        {"torch", "rdkit", "openbabel", "subprocess", "requests", "lightning_modules", "dataset"}
    )
    assert "np.savez" not in source
    assert "np.savez_compressed" not in source
    assert 'if len(rows) != record.get("source_row_count"):' in source
    assert 'coords_float32 = np.ascontiguousarray(np.asarray(coordinates, dtype="<f4"))' in source
    assert "if not np.all(np.isfinite(coords_float32)):" in source


def test_precommit_compatibility_exact_commands_and_restore(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = materializer._gate._adapter._projection_contract_gate
    exact_lines = "\n".join(f"?? {path}" for path in materializer._REPOSITORY_EXACT4)
    fifth = "?? fifth_untracked_file"

    def original(_root: Path, arguments: tuple[str, ...]) -> str:
        if tuple(arguments) in {
            ("status", "--porcelain=v1", "--untracked-files=all"),
            ("status", "--short"),
        }:
            return exact_lines + "\n" + fifth + "\n"
        return "unchanged"

    monkeypatch.setattr(owner, "_run_git", original)
    with materializer._precommit_compatibility():
        wrapped = owner._run_git
        assert wrapped(REPO_ROOT, ("status", "--short")) == fifth
        assert wrapped(
            REPO_ROOT, ("status", "--porcelain=v1", "--untracked-files=all")
        ) == fifth
        assert wrapped(REPO_ROOT, ("diff", "--name-only")) == "unchanged"
    assert owner._run_git is original


@pytest.mark.parametrize("status", [" M", "M ", "A ", "D ", "R ", "T ", "UU"])
def test_precommit_never_filters_non_untracked_status(
    monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    owner = materializer._gate._adapter._projection_contract_gate
    path = materializer._REPOSITORY_EXACT4[0]
    line = f"{status} {path}"
    monkeypatch.setattr(owner, "_run_git", lambda _root, _arguments: line)
    with materializer._precommit_compatibility():
        assert owner._run_git(REPO_ROOT, ("status", "--short")) == line


def test_candidate_double_build_is_byte_identical(candidate: dict[str, bytes]) -> None:
    second = materializer._build_candidate_bundle(
        repo_root=REPO_ROOT, state_root=REAL_STATE
    )
    assert candidate == second
    assert tuple(candidate) == materializer._ARTIFACT_NAMES
    assert materializer._aggregate_sha256(candidate) == EXPECTED_AGGREGATE


def test_candidate_exact4_identities(candidate: dict[str, bytes]) -> None:
    expected = {
        materializer._NPZ: (196172, EXPECTED_NPZ_SHA256),
        materializer._MANIFEST: (
            31910, "b8a210a06c758ebaf16887a0e7ce18a9199c2dffcda61e814143d5f157801b54"
        ),
        materializer._INVENTORY: (
            3319, "37aaa88566594aa36674b4864f7884c28426a923ca8d0e04bb136b63b84105cb"
        ),
        materializer._REPORT: (
            1654, "596d0b2d5464942b21ca1379c1458de750c786f1d990114c72f0f1aee4586fc0"
        ),
    }
    assert {
        name: (len(payload), hashlib.sha256(payload).hexdigest())
        for name, payload in candidate.items()
    } == expected


def test_npz_exact12_shapes_dtypes_and_values(candidate: dict[str, bytes]) -> None:
    arrays = _candidate_arrays(candidate)
    assert tuple(arrays) == materializer._ARRAY_NAMES
    expected = {
        "names": ((11,), "<U27"), "receptors": ((11,), "<U4"),
        "lig_mask": ((323,), "<i8"), "pocket_mask": ((2202,), "<i8"),
        "lig_coords": ((323, 3), "<f4"), "pocket_coords": ((2202, 3), "<f4"),
        "lig_one_hot": ((323, 10), "<f4"), "pocket_one_hot": ((2202, 10), "<f4"),
        "lig_source_row_index": ((323,), "<i8"),
        "pocket_source_row_index": ((2202,), "<i8"),
        "lig_parser_local_index": ((323,), "<i8"),
        "pocket_parser_local_index": ((2202,), "<i8"),
    }
    assert {name: (array.shape, array.dtype.str) for name, array in arrays.items()} == expected
    assert arrays["names"].tolist() == list(materializer._EXPECTED_SAMPLE_IDS)
    assert arrays["receptors"].tolist() == [
        "6BV6", "6BV8", "6BV5", "1AEC", "1AIM", "1AU3", "1AU4", "1AYU", "1AYV", "1AYW", "1B02"
    ]
    for role in ("lig", "pocket"):
        mask = arrays[f"{role}_mask"]
        assert np.bincount(mask).tolist() == EXPECTED_LENGTHS[role]
        assert np.all(np.isfinite(arrays[f"{role}_coords"]))
        one_hot = arrays[f"{role}_one_hot"]
        assert np.array_equal(one_hot.sum(1), np.ones(len(one_hot), dtype="<f4"))
        sections = np.cumsum(EXPECTED_LENGTHS[role])[:-1]
        locals_by_sample = np.split(arrays[f"{role}_parser_local_index"], sections)
        assert all(np.array_equal(values, np.arange(len(values))) for values in locals_by_sample)


def test_zip_and_npy_metadata_manual_central_directory(candidate: dict[str, bytes]) -> None:
    payload = candidate[materializer._NPZ]
    offsets: list[int] = []
    cursor = 0
    while True:
        cursor = payload.find(b"PK\x01\x02", cursor)
        if cursor < 0:
            break
        offsets.append(cursor)
        cursor += 4
    assert len(offsets) == 12
    names: list[str] = []
    for offset in offsets:
        fields = struct.unpack_from("<4s6H3I5H2I", payload, offset)
        signature, made_by, needed, flags, method, mod_time, mod_date = fields[:7]
        name_length, extra_length, comment_length = fields[10:13]
        external_attr = fields[15]
        name_start = offset + 46
        name = payload[name_start:name_start + name_length].decode("ascii")
        names.append(name)
        assert signature == b"PK\x01\x02"
        assert made_by >> 8 == 3
        assert needed == 20
        assert flags == 0 and method == 0 and mod_time == 0 and mod_date == 33
        assert extra_length == 0 and comment_length == 0
        assert stat.S_IFMT(external_attr >> 16) == stat.S_IFREG
        assert stat.S_IMODE(external_attr >> 16) == 0o644
    assert names == [f"{name}.npy" for name in materializer._ARRAY_NAMES]
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert archive.comment == b""
        for name in materializer._ARRAY_NAMES:
            npy = archive.read(f"{name}.npy")
            assert npy[:8] == b"\x93NUMPY\x01\x00"


def test_inventory_exact12_recomputes_raw_and_npy_hashes(candidate: dict[str, bytes]) -> None:
    arrays = _candidate_arrays(candidate)
    reader = csv.DictReader(io.StringIO(candidate[materializer._INVENTORY].decode(), newline=""))
    rows = list(reader)
    assert tuple(reader.fieldnames or ()) == materializer._INVENTORY_FIELDS
    assert [row["array_name"] for row in rows] == list(materializer._ARRAY_NAMES)
    with zipfile.ZipFile(io.BytesIO(candidate[materializer._NPZ])) as archive:
        for index, row in enumerate(rows):
            name = row["array_name"]
            raw = arrays[name].tobytes(order="C")
            npy = archive.read(row["npz_entry_name"])
            assert int(row["array_index"]) == index
            assert int(row["raw_c_order_bytes"]) == len(raw)
            assert row["raw_c_order_sha256"] == hashlib.sha256(raw).hexdigest()
            assert int(row["npy_bytes"]) == len(npy)
            assert row["npy_sha256"] == hashlib.sha256(npy).hexdigest()
            assert row["identity_selection_authorized"] == ("true" if name == "names" else "false")


def test_manifest_exact18_and_binding_report(candidate: dict[str, bytes]) -> None:
    manifest = json.loads(candidate[materializer._MANIFEST])
    report = json.loads(candidate[materializer._REPORT])
    assert set(manifest) == set(materializer._MANIFEST_FIELDS)
    assert manifest["schema_version"] == materializer._MANIFEST_SCHEMA
    assert manifest["runtime_artifact_sha256"] == EXPECTED_NPZ_SHA256
    assert manifest["runtime_artifact_relative_path"] == materializer._RUNTIME_ARTIFACT_RELATIVE
    assert manifest["materialization_provenance"]["source_table_count"] == 22
    assert manifest["materialization_provenance"]["array_count"] == 12
    assert manifest["materialization_provenance"]["checkpoint_bytes_read"] is False
    assert manifest["materialization_provenance"]["design_markdown_read"] is False
    assert manifest["materialization_provenance"]["placeholder_ligand_used"] is False
    assert manifest["names_binding"] == {
        "field_name": "names",
        "sample_key_schema_version": materializer._SAMPLE_KEY_SCHEMA,
        "sample_order": list(materializer._EXPECTED_SAMPLE_IDS),
        "array_dtype_family": "unicode_string",
        "array_rank": 1,
        "array_length": 11,
        "array_values_digest": materializer._NAMES_SEMANTIC_DIGEST,
        "array_values_digest_framing": "canonical compact JSON exact string array",
        "exact_values_required": True,
    }
    assert manifest["receptors_binding"] == {
        "field_name": "receptors",
        "identity_authority": False,
        "consistency_only": True,
        "recommended_exact_values": list(materializer._EXPECTED_RECEPTORS),
    }
    for role in ("ligand", "pocket"):
        binding = manifest[f"{role}_buffer_binding"]
        assert binding["padding_present"] is False
        assert binding["crop_present"] is False
        assert binding["virtual_nodes_present"] is False
        assert binding["atom_reorder_present"] is False
        assert len(binding["per_sample_role_order_record_digests"]) == 11
    assert report["status"] == "PASS_FORMAL_RUNTIME_CARRIER_BUNDLE_EXACT"
    assert report["source_table_count_verified"] == 22
    assert report["coordinates_from_source_tables"] is True
    assert report["one_hot_from_source_type_symbols"] is True
    assert report["placeholder_ligand_used"] is False
    assert report["ready_for_training"] is False


def test_manifest_instance_exactly_satisfies_published_schema(
    candidate: dict[str, bytes],
) -> None:
    manifest, schema, arrays, samples = _manifest_validation_inputs(candidate)
    _validate_manifest_inputs(manifest, schema, arrays, samples)


def test_canonical_candidate_new_manifest_passes_bundle_validation(
    candidate: dict[str, bytes],
) -> None:
    validated = materializer._validate_candidate_bundle(dict(candidate))
    assert validated["manifest"]["names_binding"]["array_values_digest"] == (
        materializer._NAMES_SEMANTIC_DIGEST
    )


def test_manifest_names_binding_missing_field_fails_closed(
    candidate: dict[str, bytes],
) -> None:
    manifest, schema, arrays, samples = _manifest_validation_inputs(candidate)
    manifest["names_binding"].pop("array_values_digest_framing")
    with pytest.raises(ValueError, match=materializer._ERROR):
        _validate_manifest_inputs(manifest, schema, arrays, samples)


def test_manifest_names_binding_wrong_digest_fails_closed(
    candidate: dict[str, bytes],
) -> None:
    manifest, schema, arrays, samples = _manifest_validation_inputs(candidate)
    manifest["names_binding"]["array_values_digest"] = "0" * 64
    with pytest.raises(ValueError, match=materializer._ERROR):
        _validate_manifest_inputs(manifest, schema, arrays, samples)


@pytest.mark.parametrize(
    ("field", "value"), (("array_rank", 2), ("array_length", 10))
)
def test_manifest_names_binding_wrong_rank_or_length_fails_closed(
    candidate: dict[str, bytes], field: str, value: int
) -> None:
    manifest, schema, arrays, samples = _manifest_validation_inputs(candidate)
    manifest["names_binding"][field] = value
    with pytest.raises(ValueError, match=materializer._ERROR):
        _validate_manifest_inputs(manifest, schema, arrays, samples)


def test_manifest_receptors_identity_authority_fails_closed(
    candidate: dict[str, bytes],
) -> None:
    manifest, schema, arrays, samples = _manifest_validation_inputs(candidate)
    manifest["receptors_binding"]["identity_authority"] = True
    with pytest.raises(ValueError, match=materializer._ERROR):
        _validate_manifest_inputs(manifest, schema, arrays, samples)


def test_manifest_role_required_field_missing_fails_closed(
    candidate: dict[str, bytes],
) -> None:
    manifest, schema, arrays, samples = _manifest_validation_inputs(candidate)
    manifest["ligand_buffer_binding"].pop("flat_atom_identity_sequence_digest")
    with pytest.raises(ValueError, match=materializer._ERROR):
        _validate_manifest_inputs(manifest, schema, arrays, samples)


@pytest.mark.parametrize(
    "field", ("padding_present", "virtual_nodes_present", "atom_reorder_present")
)
def test_manifest_role_required_false_constraint_fails_closed(
    candidate: dict[str, bytes], field: str
) -> None:
    manifest, schema, arrays, samples = _manifest_validation_inputs(candidate)
    manifest["pocket_buffer_binding"][field] = True
    with pytest.raises(ValueError, match=materializer._ERROR):
        _validate_manifest_inputs(manifest, schema, arrays, samples)


def test_published_schema_artifact_drift_fails_closed(
    candidate: dict[str, bytes],
) -> None:
    manifest, schema, arrays, samples = _manifest_validation_inputs(candidate)
    schema["top_level_fields"]["names_binding"]["array_length"] = 10
    with pytest.raises(ValueError, match=materializer._ERROR):
        _validate_manifest_inputs(manifest, schema, arrays, samples)


def test_raw_c_order_sha_cannot_replace_names_semantic_digest(
    candidate: dict[str, bytes],
) -> None:
    manifest, schema, arrays, samples = _manifest_validation_inputs(candidate)
    raw_digest = hashlib.sha256(arrays["names"].tobytes(order="C")).hexdigest()
    assert raw_digest != materializer._NAMES_SEMANTIC_DIGEST
    manifest["names_binding"]["array_values_digest"] = raw_digest
    with pytest.raises(ValueError, match=materializer._ERROR):
        _validate_manifest_inputs(manifest, schema, arrays, samples)


def test_dataset_center_false_true_collate_permutation_subset(
    candidate: dict[str, bytes], tmp_path: Path
) -> None:
    assert torch.__name__ == "torch"
    spec = importlib.util.spec_from_file_location("covapie_runtime_dataset_test", REPO_ROOT / "dataset.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / "candidate.npz"
    path.write_bytes(candidate[materializer._NPZ])
    artifact_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    arrays = _candidate_arrays(candidate)
    plain = module.ProcessedLigandPocketDataset(path, center=False)
    centered = module.ProcessedLigandPocketDataset(path, center=True)
    assert len(plain) == len(centered) == 11
    for index in range(11):
        start_lig = sum(EXPECTED_LENGTHS["lig"][:index])
        stop_lig = start_lig + EXPECTED_LENGTHS["lig"][index]
        start_pocket = sum(EXPECTED_LENGTHS["pocket"][:index])
        stop_pocket = start_pocket + EXPECTED_LENGTHS["pocket"][index]
        item = plain[index]
        shifted = centered[index]
        assert str(item["names"]) == materializer._EXPECTED_SAMPLE_IDS[index]
        assert str(item["receptors"]) == arrays["receptors"][index]
        assert int(item["num_lig_atoms"]) == EXPECTED_LENGTHS["lig"][index]
        assert int(item["num_pocket_nodes"]) == EXPECTED_LENGTHS["pocket"][index]
        for role, start, stop in (("lig", start_lig, stop_lig), ("pocket", start_pocket, stop_pocket)):
            for suffix in ("one_hot", "source_row_index", "parser_local_index"):
                assert np.array_equal(item[f"{role}_{suffix}"].numpy(), arrays[f"{role}_{suffix}"][start:stop])
                assert np.array_equal(shifted[f"{role}_{suffix}"].numpy(), item[f"{role}_{suffix}"].numpy())
            delta = shifted[f"{role}_coords"].numpy() - item[f"{role}_coords"].numpy()
            assert np.allclose(delta, delta[0], rtol=0, atol=2e-6)
            assert not np.array_equal(shifted[f"{role}_coords"].numpy(), item[f"{role}_coords"].numpy())
    permutation = [7, 0, 10, 3]
    batch = plain.collate_fn([plain[index] for index in permutation])
    assert [str(value) for value in batch["names"]] == [materializer._EXPECTED_SAMPLE_IDS[index] for index in permutation]
    assert batch["num_lig_atoms"].tolist() == [EXPECTED_LENGTHS["lig"][index] for index in permutation]
    assert batch["num_pocket_nodes"].tolist() == [EXPECTED_LENGTHS["pocket"][index] for index in permutation]
    for role in ("lig", "pocket"):
        expected_mask = np.repeat(np.arange(len(permutation)), [EXPECTED_LENGTHS[role][index] for index in permutation])
        assert np.array_equal(batch[f"{role}_mask"].numpy(), expected_mask)
        expected_source = np.concatenate([plain[index][f"{role}_source_row_index"].numpy() for index in permutation])
        assert np.array_equal(batch[f"{role}_source_row_index"].numpy(), expected_source)
    subset = plain.collate_fn([plain[2], plain[9]])
    assert [str(value) for value in subset["names"]] == [materializer._EXPECTED_SAMPLE_IDS[2], materializer._EXPECTED_SAMPLE_IDS[9]]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact_sha == EXPECTED_NPZ_SHA256


def test_temp_publication_verify_duplicate_and_relative_alias(
    candidate: dict[str, bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state_mirror(tmp_path)
    result = _publish_with_candidate(monkeypatch, state, candidate)
    canonical = state / materializer._CANONICAL_RELATIVE
    target = os.readlink(canonical)
    assert not os.path.isabs(target)
    aggregate, nonce = materializer._parse_object_name(target)
    assert aggregate == EXPECTED_AGGREGATE and len(nonce) == 32
    object_path = canonical.parent / target
    assert stat.S_IMODE(object_path.stat().st_mode) == 0o755
    assert sorted(path.name for path in object_path.iterdir()) == sorted(materializer._ARTIFACT_NAMES)
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o644 for path in object_path.iterdir())
    assert result["aggregate_sha256"] == EXPECTED_AGGREGATE
    checked = materializer._verify_existing(repo_root=REPO_ROOT, state_root=state)
    assert checked["operation"] == "check"
    with pytest.raises(ValueError, match=materializer._ERROR):
        materializer.materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
            repo_root=REPO_ROOT, state_root=state
        )
    assert canonical.is_symlink() and object_path.is_dir()


def test_public_materialize_and_fresh_verify_without_candidate_monkeypatch(
    tmp_path: Path,
) -> None:
    real_canonical = REAL_STATE / materializer._CANONICAL_RELATIVE
    with pytest.raises(FileNotFoundError):
        real_canonical.lstat()
    materializer._validate_routing_object(REAL_STATE)
    state = _state_mirror(tmp_path)

    result = materializer.materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
        repo_root=REPO_ROOT, state_root=state
    )
    checked = materializer._verify_existing(repo_root=REPO_ROOT, state_root=state)

    canonical = state / materializer._CANONICAL_RELATIVE
    target = os.readlink(canonical)
    object_path = canonical.parent / target
    assert not os.path.isabs(target)
    assert result["operation"] == "materialize"
    assert checked["operation"] == "check"
    assert result["aggregate_sha256"] == checked["aggregate_sha256"] == EXPECTED_AGGREGATE
    expected_identities = {
        materializer._NPZ: (196172, EXPECTED_NPZ_SHA256),
        materializer._MANIFEST: (
            31910, "b8a210a06c758ebaf16887a0e7ce18a9199c2dffcda61e814143d5f157801b54"
        ),
        materializer._INVENTORY: (
            3319, "37aaa88566594aa36674b4864f7884c28426a923ca8d0e04bb136b63b84105cb"
        ),
        materializer._REPORT: (
            1654, "596d0b2d5464942b21ca1379c1458de750c786f1d990114c72f0f1aee4586fc0"
        ),
    }
    assert result["artifacts"] == {
        name: {"bytes": size, "sha256": digest}
        for name, (size, digest) in expected_identities.items()
    }
    assert expected_identities[materializer._NPZ] == (196172, EXPECTED_NPZ_SHA256)
    assert stat.S_IMODE(object_path.stat().st_mode) == 0o755
    assert sorted(path.name for path in object_path.iterdir()) == sorted(
        materializer._ARTIFACT_NAMES
    )
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o644 for path in object_path.iterdir())
    materializer._validate_routing_object(REAL_STATE)
    with pytest.raises(FileNotFoundError):
        real_canonical.lstat()


def test_tamper_fails_closed(
    candidate: dict[str, bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state_mirror(tmp_path)
    _publish_with_candidate(monkeypatch, state, candidate)
    canonical = state / materializer._CANONICAL_RELATIVE
    leaf = canonical.parent / os.readlink(canonical) / materializer._REPORT
    leaf.write_bytes(leaf.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match=materializer._ERROR):
        materializer._verify_existing(repo_root=REPO_ROOT, state_root=state)


def test_prepublication_failure_cleans_owned_object(
    candidate: dict[str, bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state_mirror(tmp_path)
    monkeypatch.setattr(materializer, "_build_candidate_bundle", lambda **_kwargs: dict(candidate))
    original_symlink = materializer.os.symlink

    def fail_carrier_symlink(source: str, target: str, **kwargs: object) -> None:
        if target == materializer._CANONICAL_BASENAME:
            raise OSError("injected prepublication failure")
        original_symlink(source, target, **kwargs)

    monkeypatch.setattr(materializer.os, "symlink", fail_carrier_symlink)
    with pytest.raises(ValueError, match=materializer._ERROR):
        materializer.materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
            repo_root=REPO_ROOT, state_root=state
        )
    formal = state / "formal-sidecars"
    assert not (formal / materializer._CANONICAL_BASENAME).is_symlink()
    assert not any(path.name.startswith(materializer._OBJECT_PREFIX) for path in formal.iterdir())


def test_prepublication_unrelated_canonical_cleans_only_owned_object(
    candidate: dict[str, bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state_mirror(tmp_path)
    monkeypatch.setattr(materializer, "_build_candidate_bundle", lambda **_kwargs: dict(candidate))
    original_symlink = materializer.os.symlink

    def publish_unrelated_then_fail(source: str, target: str, **kwargs: object) -> None:
        if target == materializer._CANONICAL_BASENAME:
            original_symlink(ROUTING_NAME, target, **kwargs)
            raise FileExistsError("injected concurrent unrelated canonical")
        original_symlink(source, target, **kwargs)

    monkeypatch.setattr(materializer.os, "symlink", publish_unrelated_then_fail)
    with pytest.raises(ValueError, match=materializer._ERROR):
        materializer.materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
            repo_root=REPO_ROOT, state_root=state
        )
    formal = state / "formal-sidecars"
    canonical = formal / materializer._CANONICAL_BASENAME
    assert canonical.is_symlink() and os.readlink(canonical) == ROUTING_NAME
    assert not any(path.name.startswith(materializer._OBJECT_PREFIX) for path in formal.iterdir())


def test_prepublication_concurrent_canonical_points_to_object_preserves_object(
    candidate: dict[str, bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state_mirror(tmp_path)
    monkeypatch.setattr(materializer, "_build_candidate_bundle", lambda **_kwargs: dict(candidate))
    original_symlink = materializer.os.symlink

    def publish_owned_then_fail(source: str, target: str, **kwargs: object) -> None:
        if target == materializer._CANONICAL_BASENAME:
            original_symlink(source, target, **kwargs)
            raise FileExistsError("injected concurrent canonical to owned object")
        original_symlink(source, target, **kwargs)

    monkeypatch.setattr(materializer.os, "symlink", publish_owned_then_fail)
    with pytest.raises(ValueError, match=materializer._ERROR):
        materializer.materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
            repo_root=REPO_ROOT, state_root=state
        )
    canonical = state / materializer._CANONICAL_RELATIVE
    target = os.readlink(canonical)
    object_path = canonical.parent / target
    assert target.startswith(materializer._OBJECT_PREFIX)
    assert object_path.is_dir()
    assert sorted(path.name for path in object_path.iterdir()) == sorted(
        materializer._ARTIFACT_NAMES
    )


def test_postpublication_failure_keeps_published_object(
    candidate: dict[str, bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state_mirror(tmp_path)
    monkeypatch.setattr(materializer, "_build_candidate_bundle", lambda **_kwargs: dict(candidate))
    original_read = materializer._read_object
    calls = 0

    def fail_second(*args: object, **kwargs: object) -> dict[str, bytes]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected postpublication failure")
        return original_read(*args, **kwargs)

    monkeypatch.setattr(materializer, "_read_object", fail_second)
    with pytest.raises(ValueError, match=materializer._ERROR):
        materializer.materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
            repo_root=REPO_ROOT, state_root=state
        )
    canonical = state / materializer._CANONICAL_RELATIVE
    assert canonical.is_symlink()
    assert (canonical.parent / os.readlink(canonical)).is_dir()


def test_postpublication_alias_replacement_fails_final_revalidation_without_cleanup(
    candidate: dict[str, bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state_mirror(tmp_path)
    monkeypatch.setattr(materializer, "_build_candidate_bundle", lambda **_kwargs: dict(candidate))
    original_read = materializer._read_object
    original_symlink = materializer.os.symlink
    calls = 0

    def replace_alias_after_final_read(*args: object, **kwargs: object) -> dict[str, bytes]:
        nonlocal calls
        calls += 1
        result = original_read(*args, **kwargs)
        if calls == 2:
            canonical = state / materializer._CANONICAL_RELATIVE
            canonical.unlink()
            original_symlink(ROUTING_NAME, canonical, target_is_directory=True)
        return result

    monkeypatch.setattr(materializer, "_read_object", replace_alias_after_final_read)
    with pytest.raises(ValueError, match=materializer._ERROR):
        materializer.materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
            repo_root=REPO_ROOT, state_root=state
        )
    formal = state / "formal-sidecars"
    canonical = formal / materializer._CANONICAL_BASENAME
    assert canonical.is_symlink() and os.readlink(canonical) == ROUTING_NAME
    owned = [path for path in formal.iterdir() if path.name.startswith(materializer._OBJECT_PREFIX)]
    assert len(owned) == 1 and owned[0].is_dir()


def test_postpublication_parent_identity_drift_fails_closed_without_cleanup(
    candidate: dict[str, bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state_mirror(tmp_path)
    monkeypatch.setattr(materializer, "_build_candidate_bundle", lambda **_kwargs: dict(candidate))
    original_read = materializer._read_object
    calls = 0

    def replace_parent_path_after_final_read(*args: object, **kwargs: object) -> dict[str, bytes]:
        nonlocal calls
        calls += 1
        result = original_read(*args, **kwargs)
        if calls == 2:
            formal = state / "formal-sidecars"
            formal.rename(state / "formal-sidecars-published")
            formal.mkdir(mode=0o755)
        return result

    monkeypatch.setattr(materializer, "_read_object", replace_parent_path_after_final_read)
    with pytest.raises(ValueError, match=materializer._ERROR):
        materializer.materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
            repo_root=REPO_ROOT, state_root=state
        )
    published = state / "formal-sidecars-published"
    canonical = published / materializer._CANONICAL_BASENAME
    assert canonical.is_symlink()
    assert (published / os.readlink(canonical)).is_dir()


def test_cleanup_failure_uses_independent_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state_mirror(tmp_path)
    dummy = {name: b"candidate" for name in materializer._ARTIFACT_NAMES}
    monkeypatch.setattr(
        materializer, "_build_candidate_bundle", lambda **_kwargs: dict(dummy)
    )
    monkeypatch.setattr(
        materializer.os,
        "symlink",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("injected publication failure")
        ),
    )
    monkeypatch.setattr(
        materializer,
        "_cleanup",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("injected cleanup failure")
        ),
    )
    with pytest.raises(materializer._CleanupFailure) as captured:
        materializer.materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
            repo_root=REPO_ROOT, state_root=state
        )
    assert str(captured.value) == materializer._CLEANUP_ERROR


@pytest.mark.parametrize("attack", ["canonical_directory", "canonical_foreign_symlink", "parent_symlink"])
def test_symlink_and_path_attacks_fail_closed(
    candidate: dict[str, bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, attack: str
) -> None:
    state = _state_mirror(tmp_path)
    formal = state / "formal-sidecars"
    canonical = formal / materializer._CANONICAL_BASENAME
    if attack == "canonical_directory":
        canonical.mkdir()
    elif attack == "canonical_foreign_symlink":
        os.symlink(ROUTING_NAME, canonical)
    else:
        real_formal = tmp_path / "real-formal"
        formal.rename(real_formal)
        os.symlink(real_formal, formal, target_is_directory=True)
    monkeypatch.setattr(materializer, "_build_candidate_bundle", lambda **_kwargs: dict(candidate))
    with pytest.raises(ValueError, match=materializer._ERROR):
        materializer.materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
            repo_root=REPO_ROOT, state_root=state
        )


def test_checker_absent_state_and_rejections(
    candidate: dict[str, bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    script_path = REPO_ROOT / materializer._SCRIPT_PATH
    spec = importlib.util.spec_from_file_location("covapie_materializer_checker_test", script_path)
    assert spec is not None and spec.loader is not None
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    state = _state_mirror(tmp_path)
    monkeypatch.setattr(checker._materializer, "_build_candidate_bundle", lambda **_kwargs: dict(candidate))
    monkeypatch.setattr(
        sys, "argv", [str(script_path), "--repo-root", str(REPO_ROOT), "--state-root", str(state)]
    )
    assert checker.main() == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    output = json.loads(captured.out)
    assert output["status"] == "PASS_MATERIALIZER_IMPLEMENTATION_ONLY"
    assert output["readiness"]["formal_runtime_carrier_materialized"] is False
    for bad in (
        ["--help"], ["--output", "x", "--repo-root", str(REPO_ROOT)],
        ["--repo-root", str(REPO_ROOT), "--extra", str(state)], [],
    ):
        monkeypatch.setattr(sys, "argv", [str(script_path), *bad])
        assert checker.main() == 1
        failed = capsys.readouterr()
        assert failed.out == ""
        assert failed.err == checker._ERROR + "\n"


def test_real_state_carrier_remains_absent() -> None:
    canonical = REAL_STATE / materializer._CANONICAL_RELATIVE
    with pytest.raises(FileNotFoundError):
        canonical.lstat()
