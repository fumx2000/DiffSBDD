from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import inspect
import io
import json
import math
import os
import struct
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_current11_tensor_projection_payload_builder_v1 as builder,
)


STATE_ROOT = (ROOT.parent / "covapie-state").resolve(strict=True)
SCRIPT = ROOT / "scripts/check_covapie_current11_tensor_projection_payload_builder_v1.py"
EXPECTED_DIGEST = "95e9ed091566bbc547a8f75b975a40c27ce318e95df1553b1f1ac448a91b1f9d"
EXPECTED_PAIRS = [
    [88, 3], [25, 3], [19, 3], [39, 3], [37, 27], [50, 21],
    [48, 16], [53, 20], [52, 21], [53, 18], [84, 5],
]
EXPECTED_DISTANCES = [
    "1.670", "1.800", "1.718", "1.802", "1.809", "1.762",
    "1.807", "1.799", "1.806", "1.794", "1.717",
]


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return builder.build_covapie_current11_tensor_projection_payload_bundle_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )


@pytest.fixture(scope="module")
def parsed(artifacts: dict[str, bytes]) -> dict[str, dict[str, object]]:
    return {name: json.loads(payload) for name, payload in artifacts.items()}


def _decode_strings(buffer: dict[str, object]) -> list[str]:
    raw = bytes(buffer["bytes_uint8"])
    offsets = buffer["offsets_int64"]
    return [
        raw[offsets[index] : offsets[index + 1]].decode("utf-8")
        for index in range(len(offsets) - 1)
    ]


def _manual_digest(artifacts: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    digest.update(b"COVAPIE_CURRENT11_TENSOR_PROJECTION_PAYLOAD_BUNDLE_V1\0")
    for name in builder._STABLE_ARTIFACT_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _run_checker(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (sys.executable, "-B", os.fspath(SCRIPT), *arguments),
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        capture_output=True,
        check=False,
    )


def _primary_context() -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    formal = builder._read_formal(STATE_ROOT / builder._FORMAL_RELATIVE)
    routing = builder._validate_routing(formal)
    sources = builder._resolve_sources(ROOT, STATE_ROOT, routing)
    return routing, sources


def _mutate_csv(payload: bytes, row_index: int, field: str, value: str) -> bytes:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    columns = tuple(reader.fieldnames or ())
    rows = list(reader)
    rows[row_index][field] = value
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def test_unique_keyword_only_public_api() -> None:
    assert builder.__all__ == (
        "build_covapie_current11_tensor_projection_payload_bundle_v1",
    )
    signature = inspect.signature(
        builder.build_covapie_current11_tensor_projection_payload_bundle_v1
    )
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    with pytest.raises(TypeError):
        builder.build_covapie_current11_tensor_projection_payload_bundle_v1(  # type: ignore[misc]
            ROOT, STATE_ROOT
        )


def test_exact_builtin_dict_and_exact8_order(artifacts: dict[str, bytes]) -> None:
    assert type(artifacts) is dict
    assert tuple(artifacts) == builder._ARTIFACT_NAMES
    assert len(artifacts) == 8
    assert all(type(payload) is bytes for payload in artifacts.values())


def test_silent_import() -> None:
    completed = subprocess.run(
        (sys.executable, "-B", "-c", f"import {builder.__name__}"),
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""


def test_stdlib_and_local_import_boundary() -> None:
    source = (ROOT / builder._REPOSITORY_EXACT4[2]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported <= set(sys.stdlib_module_names) | {"covalent_ext", "__future__"}
    assert imported.isdisjoint({"torch", "numpy", "rdkit", "openbabel"})


def test_import_has_no_output_side_effects() -> None:
    module = importlib.reload(builder)
    assert module.__all__ == (
        "build_covapie_current11_tensor_projection_payload_bundle_v1",
    )


def test_artifacts_are_canonical_json(artifacts: dict[str, bytes]) -> None:
    for payload in artifacts.values():
        assert len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload and b"\r" not in payload
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        value = json.loads(payload, parse_constant=lambda value: pytest.fail(value))
        expected = (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode()
        assert payload == expected


def test_published_gate_and_frozen_lineage(parsed: dict[str, dict[str, object]]) -> None:
    manifest = parsed[builder._ARTIFACT_NAMES[0]]
    report = parsed[builder._ARTIFACT_NAMES[7]]
    lineage = manifest["source_contract_lineage"]
    assert lineage["published_gate_module_sha256"] == builder._GATE_MODULE_SHA256
    assert lineage["published_contract_digest"] == builder._CONTRACT_DIGEST
    assert report["published_contract_gate_passed"] is True
    assert report["published_contract_gate_double_build_identical"] is True


def test_gate_public_api_called_twice(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    original = (
        builder._contract_gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1
    )

    def counted(**arguments: object) -> dict[str, bytes]:
        nonlocal calls
        calls += 1
        return original(**arguments)  # type: ignore[arg-type]

    monkeypatch.setattr(
        builder._contract_gate,
        "build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1",
        counted,
    )
    builder._published_gate(ROOT, STATE_ROOT)
    assert calls == 2


def test_formal_snapshot_unchanged_by_build() -> None:
    canonical = STATE_ROOT / builder._FORMAL_RELATIVE
    before = builder._formal_snapshot(canonical)
    builder.build_covapie_current11_tensor_projection_payload_bundle_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )
    assert builder._formal_snapshot(canonical) == before


def test_runtime_does_not_read_audit_markdown(monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.read_bytes

    def guarded(path: Path) -> bytes:
        if path.as_posix().endswith(builder._AUDIT_RELATIVE):
            pytest.fail("audit Markdown was read")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    builder.build_covapie_current11_tensor_projection_payload_bundle_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )


def test_exact11_and_task_order(parsed: dict[str, dict[str, object]]) -> None:
    manifest = parsed[builder._ARTIFACT_NAMES[0]]
    assert [
        (row["sample_index_row_id"], row["pdb_id"], row["ligand_comp_id"])
        for row in manifest["sample_order"]
    ] == list(builder._SAMPLES)
    assert [row["task_index"] for row in manifest["audited_task_order"]] == [
        0, 1, 2, 6, 12
    ]
    assert [row["semantic_task_name"] for row in manifest["audited_task_order"]] == [
        task[1] for task in builder._TASKS
    ]


def test_source_inventory_and_counts(parsed: dict[str, dict[str, object]]) -> None:
    manifest = parsed[builder._ARTIFACT_NAMES[0]]
    report = parsed[builder._ARTIFACT_NAMES[7]]
    inventory = manifest["source_binding_inventory"]
    assert len(inventory) == report["source_binding_count"] == 27
    assert [row["source_id"] for row in inventory] == list(builder._SOURCE_IDS)
    assert len({row["sha256"] for row in inventory}) == 27
    assert report["secondary_atom_table_count"] == 22
    assert all(not Path(row["relative_path"]).is_absolute() for row in inventory)


def test_selected_cell_counts_and_states(parsed: dict[str, dict[str, object]]) -> None:
    provenance = parsed[builder._ARTIFACT_NAMES[6]]["cell_provenance_records"]
    assert len(provenance) == 55
    assert sum(row["eligibility_state"] == "admissible_now" for row in provenance) == 44
    assert sum(
        row["eligibility_state"] == "admissible_as_observed_geometry_only"
        for row in provenance
    ) == 11


def test_task0_utf8_roundtrip_and_independent_buffers(
    parsed: dict[str, dict[str, object]],
) -> None:
    value = parsed[builder._ARTIFACT_NAMES[1]]
    fields = ("sample_index_row_id", "pdb_id", "ligand_comp_id")
    expected = list(zip(*builder._SAMPLES, strict=True))
    for field, values in zip(fields, expected, strict=True):
        buffer = value[field]
        assert buffer["dtype"] == "uint8" and buffer["encoding"] == "utf-8"
        assert buffer["logical_shape"] == [11]
        assert len(buffer["offsets_int64"]) == 12
        assert buffer["offsets_int64"][0] == 0
        assert buffer["offsets_int64"][-1] == len(buffer["bytes_uint8"])
        assert _decode_strings(buffer) == list(values)
    assert value[fields[0]] is not value[fields[1]]
    assert value["sample_validity_bool"] == [True] * 11


def test_task0_metadata_boundary(parsed: dict[str, dict[str, object]]) -> None:
    value = parsed[builder._ARTIFACT_NAMES[1]]
    assert value["metadata_only"] is True
    assert value["model_input_allowed_now"] is False
    assert value["loss_participation_allowed_now"] is False
    assert len(value["source_record_locators"]) == 11


def test_task1_values_validity_and_metadata(parsed: dict[str, dict[str, object]]) -> None:
    value = parsed[builder._ARTIFACT_NAMES[2]]
    assert value["values_bool"] == value["sample_validity_bool"] == [True] * 11
    assert value["logical_shape"] == [11]
    assert len(value["event_semantic_metadata"]) == 11
    required = {
        "sample_index_row_id", "conn_id", "conn_type_id", "event_source",
        "event_status", "residue_comp_id", "residue_atom_name", "ligand_comp_id",
        "ligand_atom_name", "explicit_authority_class", "canonical_record_valid",
    }
    assert all(set(row) == required for row in value["event_semantic_metadata"])
    assert all(row["conn_id"] == "covale1" for row in value["event_semantic_metadata"])
    assert all(row["conn_type_id"] == "covale" for row in value["event_semantic_metadata"])
    assert all(row["canonical_record_valid"] is True for row in value["event_semantic_metadata"])


def test_task1_explicit_semantic_boundaries(parsed: dict[str, dict[str, object]]) -> None:
    value = parsed[builder._ARTIFACT_NAMES[2]]
    assert value["explicit_struct_conn_authority"] is True
    assert value["distance_inferred"] is False
    assert value["candidate_event"] is False
    assert value["bond_order_encoded"] is False
    assert value["pre_or_post_state_encoded"] is False
    assert value["loss_participation_allowed_now"] is False


def test_task1_task2_pair_parity(parsed: dict[str, dict[str, object]]) -> None:
    events = parsed[builder._ARTIFACT_NAMES[2]]["event_semantic_metadata"]
    provenance = parsed[builder._ARTIFACT_NAMES[6]]["cell_provenance_records"]
    task1 = [row for row in provenance if row["semantic_task_name"] == builder._TASKS[1][1]]
    task2 = [row for row in provenance if row["semantic_task_name"] == builder._TASKS[2][1]]
    assert [row["sample_index_row_id"] for row in task1] == [
        row["sample_index_row_id"] for row in task2
    ] == [row["sample_index_row_id"] for row in events]


def test_task2_exact_values_offsets_and_validity(
    parsed: dict[str, dict[str, object]],
) -> None:
    value = parsed[builder._ARTIFACT_NAMES[3]]
    assert value["values_int64"] == EXPECTED_PAIRS
    assert value["values_logical_shape"] == [11, 2]
    assert value["sample_offsets_int64"] == list(range(12))
    assert value["entry_validity_bool"] == [True] * 11
    assert value["sample_validity_bool"] == [True] * 11
    assert value["column_semantics"] == [
        "pocket_atom_table_row_index_0based",
        "ligand_atom_table_row_index_0based",
    ]


def test_task2_secondary_hashes_and_locators(parsed: dict[str, dict[str, object]]) -> None:
    provenance = parsed[builder._ARTIFACT_NAMES[6]]["cell_provenance_records"]
    task2 = [row for row in provenance if row["semantic_task_name"] == builder._TASKS[2][1]]
    secondary = [item for row in task2 for item in row["secondary_source_bindings"]]
    assert len(secondary) == 22
    assert len({item["relative_path"] for item in secondary}) == 22
    assert all(item["matched_row_index_0based"] >= 0 for item in secondary)
    assert all(len(item["sha256"]) == 64 for item in secondary)
    assert all(item["matched_atom_site_id"] for item in secondary)


def test_task2_batch_remap_boundary(parsed: dict[str, dict[str, object]]) -> None:
    value = parsed[builder._ARTIFACT_NAMES[3]]
    assert value["locator_semantics"] == (
        "derived_row_index_bound_to_exact_atom_table_bytes_and_order"
    )
    assert value["permanent_chemical_identifier"] is False
    assert value["model_input_allowed_now"] is False
    assert value["batch_index_remap_required"] is True
    assert value["loss_participation_allowed_now"] is False


def test_task6_counts_and_validity(parsed: dict[str, dict[str, object]]) -> None:
    value = parsed[builder._ARTIFACT_NAMES[4]]
    assert value["sample_count"] == 11
    assert value["reviewed_warhead_atom_entry_count"] == 102
    assert value["boundary_pair_count"] == 16
    assert value["global_local_token_count"] == 118
    assert value["exact_one_boundary_sample_count"] == 6
    assert value["exact_two_boundary_sample_count"] == 5
    assert value["warhead_entry_validity_bool"] == [True] * 102
    assert value["boundary_entry_validity_bool"] == [True] * 16
    assert value["token_validity_bool"] == [True] * 118
    assert value["sample_validity_bool"] == [True] * 11


def test_task6_deterministic_token_order_and_indices(
    parsed: dict[str, dict[str, object]],
) -> None:
    value = parsed[builder._ARTIFACT_NAMES[4]]
    raw = bytes(value["token_bytes_uint8"])
    offsets = value["token_offsets_int64"]
    tokens = [
        raw[offsets[index] : offsets[index + 1]].decode("utf-8")
        for index in range(len(offsets) - 1)
    ]
    assert len(tokens) == 118
    assert tokens[:13] == [
        "CAD", "CAE", "CAF", "CAG", "CAH", "CAI", "CAJ", "CAK",
        "CAL", "CAM", "OAA", "OAB", "OAC",
    ]
    assert all(
        0 <= index < len(tokens)
        for pair in value["boundary_pairs_token_indices_int64"]
        for index in pair
    )
    assert value["sample_token_offsets_int64"][-1] == 118
    assert value["sample_warhead_offsets_int64"][-1] == 102
    assert value["sample_boundary_offsets_int64"][-1] == 16


def test_task6_f1_and_concept_boundaries(parsed: dict[str, dict[str, object]]) -> None:
    value = parsed[builder._ARTIFACT_NAMES[4]]
    raw = bytes(value["token_bytes_uint8"])
    offsets = value["token_offsets_int64"]
    tokens = [raw[offsets[i] : offsets[i + 1]].decode() for i in range(118)]
    assert "F1" in tokens
    assert value["F1_numeric_ligand_atom_mapping_available"] is False
    assert value["F1_raw_token_payload_valid"] is True
    assert value["reviewed_warhead_atom_set_semantics"] == "reviewed_warhead_atom_set"
    assert value["attachment_boundary_semantics"] == "ligand_internal_attachment_boundary"
    assert value["covalent_pair_semantics"] == "separate_ligand_protein_covalent_pair_task"
    assert value["generation_mask_sample_labels_materialized"] is False


def test_task12_decimal_and_float32_payload(parsed: dict[str, dict[str, object]]) -> None:
    value = parsed[builder._ARTIFACT_NAMES[5]]
    assert value["source_decimal_strings"] == EXPECTED_DISTANCES
    packed = bytes.fromhex(value["values_float32_le_hex"])
    assert len(packed) == 44
    assert value["values_float32_le_hex"] == value["values_float32_le_hex"].lower()
    unpacked = struct.unpack("<11f", packed)
    assert all(math.isfinite(item) and item > 0 for item in unpacked)
    assert unpacked == pytest.approx([float(item) for item in EXPECTED_DISTANCES])
    assert value["logical_shape"] == [11, 1]
    assert value["units"] == "angstrom"
    assert value["sample_validity_bool"] == [True] * 11


def test_task12_coordinate_check_and_observed_only(
    parsed: dict[str, dict[str, object]],
) -> None:
    value = parsed[builder._ARTIFACT_NAMES[5]]
    check = value["coordinate_consistency_check"]
    assert check["passed"] is True
    assert check["coordinate_values_used_as_payload"] is False
    assert check["maximum_absolute_difference_angstrom"] <= 0.000481732266
    for key in (
        "pre_covalent_geometry", "post_covalent_geometry", "bond_authority_inferred",
        "bond_order_inferred", "transformation_inferred", "post_state_inferred",
        "angle_materialized", "dihedral_materialized",
    ):
        assert value[key] is False
    assert value["observed_complex_only"] is True
    assert value["loss_participation_allowed_now"] is False


def test_provenance_exact55_order_and_flags(parsed: dict[str, dict[str, object]]) -> None:
    records = parsed[builder._ARTIFACT_NAMES[6]]["cell_provenance_records"]
    expected = [
        (sample_index * 5 + task_minor, sample[0], task[1])
        for sample_index, sample in enumerate(builder._SAMPLES)
        for task_minor, task in enumerate(builder._TASKS)
    ]
    assert [
        (row["cell_index"], row["sample_index_row_id"], row["semantic_task_name"])
        for row in records
    ] == expected
    assert all(row["payload_valid"] is True for row in records)
    assert all(row["provenance_complete"] is True for row in records)
    assert all(row["candidate_promotion_used"] is False for row in records)
    assert all(row["inference_used"] is False for row in records)
    assert all(row["semantic_promotion_used"] is False for row in records)


def test_provenance_relative_sources_and_hashes(parsed: dict[str, dict[str, object]]) -> None:
    records = parsed[builder._ARTIFACT_NAMES[6]]["cell_provenance_records"]
    for record in records:
        assert len(record["source_bindings"]) == len(record["supporting_source_ids"])
        assert len(record["source_sha256"]) == len(record["supporting_source_ids"])
        for binding in record["source_bindings"] + record["secondary_source_bindings"]:
            assert not Path(binding["relative_path"]).is_absolute()
            assert ".." not in Path(binding["relative_path"]).parts
            assert len(binding["sha256"]) == 64


def test_task6_provenance_authority_record(parsed: dict[str, dict[str, object]]) -> None:
    records = parsed[builder._ARTIFACT_NAMES[6]]["cell_provenance_records"]
    task6 = [row for row in records if row["semantic_task_name"] == builder._TASKS[3][1]]
    assert len(task6) == 11
    assert [row["source_record_locators"]["effective_authority_record_index_0based"] for row in task6] == list(range(11))
    assert all(len(row["source_record_locators"]["source_authority_record_sha256"]) == 64 for row in task6)


def test_task12_provenance_consistency_checks(parsed: dict[str, dict[str, object]]) -> None:
    records = parsed[builder._ARTIFACT_NAMES[6]]["cell_provenance_records"]
    task12 = [row for row in records if row["semantic_task_name"] == builder._TASKS[4][1]]
    assert len(task12) == 11
    assert all(row["consistency_check"]["passed"] is True for row in task12)
    assert all(row["consistency_check"]["coordinate_derived_distance_used_as_payload"] is False for row in task12)


def test_stable_digest_manual_parity(
    artifacts: dict[str, bytes], parsed: dict[str, dict[str, object]]
) -> None:
    report = parsed[builder._ARTIFACT_NAMES[7]]
    assert _manual_digest(artifacts) == report["payload_bundle_digest"] == EXPECTED_DIGEST


def test_digest_known_vector_fixture() -> None:
    vector = {name: bytes([index, 10]) for index, name in enumerate(builder._STABLE_ARTIFACT_NAMES)}
    expected = "2e7aaf8950c58943761380f4900e62daf0d1976609614691535b2bac73458835"
    assert _manual_digest(vector) == expected
    assert builder._stable_digest(vector) == expected


def test_report_excluded_from_digest(artifacts: dict[str, bytes]) -> None:
    changed = dict(artifacts)
    changed[builder._ARTIFACT_NAMES[7]] = b"different report\n"
    assert _manual_digest(changed) == _manual_digest(artifacts)


def test_double_build_is_byte_identical(artifacts: dict[str, bytes]) -> None:
    second = builder.build_covapie_current11_tensor_projection_payload_bundle_v1(
        repo_root=ROOT, state_root=STATE_ROOT
    )
    assert second == artifacts


def test_no_absolute_paths_or_git_lifecycle_in_stable_artifacts(
    artifacts: dict[str, bytes],
) -> None:
    stable = b"".join(artifacts[name] for name in builder._STABLE_ARTIFACT_NAMES)
    assert os.fspath(ROOT).encode() not in stable
    assert os.fspath(STATE_ROOT).encode() not in stable
    for forbidden in (b'"head"', b'"origin_main"', b'"ahead"', b'"behind"', b'"lifecycle_profile"'):
        assert forbidden not in stable


def test_report_status_counts_and_readiness(parsed: dict[str, dict[str, object]]) -> None:
    report = parsed[builder._ARTIFACT_NAMES[7]]
    assert report["builder_status"] == "PASS_IN_MEMORY_PAYLOAD_BUNDLE_ONLY"
    assert report["artifact_file_count"] == 8
    assert report["sample_count"] == 11
    assert report["audited_task_count"] == 5
    assert report["payload_cell_count"] == report["valid_payload_cell_count"] == 55
    assert report["candidate_payload_cell_count"] == 0
    assert report["loss_authorized_cell_count"] == 0
    assert report["runtime_consumer_available_cell_count"] == 0
    assert set(report["task_validity_counts"].values()) == {11}


def test_report_materialization_boundaries(parsed: dict[str, dict[str, object]]) -> None:
    report = parsed[builder._ARTIFACT_NAMES[7]]
    readiness = report["readiness"]
    assert readiness["payload_builder_implemented"] is True
    assert readiness["payload_builder_passed"] is True
    assert readiness["audited_exact5_task_payload_bundle_built_in_memory"] is True
    for key in (
        "full_exact25_projection_instance_materialized",
        "formal_payload_bundle_materialized", "tensor_materialized",
        "data_availability_matrix_materialized", "candidate_payloads_materialized",
        "runtime_consumer_available", "training_loss_authorized", "training_performed",
        "ready_for_formal_payload_materialization",
        "ready_for_tensor_projection_materialization", "ready_for_tensor_materialization",
        "ready_for_dataloader_integration", "ready_for_model_integration",
        "ready_for_training",
    ):
        assert readiness[key] is False
    assert readiness["feature_semantics_reaudit_required_before_training"] is True


def test_source_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = builder._read_regular

    def drift(path: Path, **arguments: object) -> bytes:
        payload = original(path, **arguments)
        if path.name == "final_dataset_index.csv":
            return payload.replace(b"CYS_SG_SAMPLE_INDEX_000001", b"CYS_SG_SAMPLE_INDEX_999999", 1)
        return payload

    monkeypatch.setattr(builder, "_read_regular", drift)
    with pytest.raises(ValueError, match=f"^{builder._ERROR}$"):
        builder.build_covapie_current11_tensor_projection_payload_bundle_v1(
            repo_root=ROOT, state_root=STATE_ROOT
        )


def test_source_hash_mismatch_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = builder._read_regular

    def mismatch(path: Path, **arguments: object) -> bytes:
        if path.name == "covalent_event_table.csv":
            raise ValueError(builder._ERROR)
        return original(path, **arguments)

    monkeypatch.setattr(builder, "_read_regular", mismatch)
    with pytest.raises(ValueError, match=f"^{builder._ERROR}$"):
        builder.build_covapie_current11_tensor_projection_payload_bundle_v1(
            repo_root=ROOT, state_root=STATE_ROOT
        )


def test_path_escape_and_symlink_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "regular").write_text("x")
    (root / "link").symlink_to(root / "regular")
    with pytest.raises(ValueError, match=f"^{builder._ERROR}$"):
        builder._safe_bound_path(root, "../escape")
    with pytest.raises(ValueError, match=f"^{builder._ERROR}$"):
        builder._safe_bound_path(root, "link")


def test_duplicate_mapping_fails_closed() -> None:
    rows = [{"sample": "x"}, {"sample": "x"}]
    with pytest.raises(ValueError, match=f"^{builder._ERROR}$"):
        builder._exact_one(rows, "sample", "x")


def test_cross_sample_mapping_fails_closed() -> None:
    _, sources = _primary_context()
    copied = {key: dict(value) for key, value in sources.items()}
    copied["atom_table_mapping_matrix"]["payload"] = _mutate_csv(
        copied["atom_table_mapping_matrix"]["payload"],
        0,
        "sample_index_row_id",
        builder._SAMPLES[1][0],
    )
    with pytest.raises(ValueError, match=f"^{builder._ERROR}$"):
        builder._parse_primary_sources(ROOT, copied)


def test_candidate_event_source_fails_closed() -> None:
    _, sources = _primary_context()
    copied = {key: dict(value) for key, value in sources.items()}
    source_id = f"event_table_{builder._SAMPLES[0][0]}"
    copied[source_id]["payload"] = _mutate_csv(
        copied[source_id]["payload"], 0, "event_source", "distance_candidate"
    )
    with pytest.raises(ValueError, match=f"^{builder._ERROR}$"):
        builder._parse_primary_sources(ROOT, copied)


def test_unexpected_source_id_fails_closed() -> None:
    formal = builder._read_formal(STATE_ROOT / builder._FORMAL_RELATIVE)
    copied = dict(formal)
    name = "current11_dataset_partial_supervision_routing_records.csv"
    copied[name] = _mutate_csv(
        copied[name], 0, "supporting_source_ids_json", '["unexpected_source"]'
    ).replace(b"\r\n", b"\n")
    with pytest.raises(ValueError, match=f"^{builder._ERROR}$"):
        builder._validate_routing(copied)


def test_cli_success_prints_report_only() -> None:
    completed = _run_checker(
        "--repo-root", os.fspath(ROOT), "--state-root", os.fspath(STATE_ROOT)
    )
    assert completed.returncode == 0
    assert completed.stderr == b""
    assert completed.stdout.count(b"\n") == 1
    report = json.loads(completed.stdout)
    assert report["builder_status"] == "PASS_IN_MEMORY_PAYLOAD_BUNDLE_ONLY"
    assert "cell_provenance_records" not in report
    assert completed.stdout == (
        json.dumps(
            report,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()


@pytest.mark.parametrize(
    "arguments",
    [
        (), ("-h",), ("--help",), ("--output", "x"), ("--output-dir", "x"),
        ("--write",), ("--materialize",), ("--tensorize",), ("--numpy",),
        ("--payload-override", "x"), ("--task", "0"), ("--source", "x"),
        ("--availability",), ("--loss",), ("--train",),
        ("--schema-override", "x"), ("extra",),
        ("--repo-root", os.fspath(ROOT)),
        ("--state-root", os.fspath(STATE_ROOT)),
    ],
)
def test_cli_rejects_unauthorized_interfaces(arguments: tuple[str, ...]) -> None:
    completed = _run_checker(*arguments)
    assert completed.returncode == 1
    assert completed.stdout == b""
    assert completed.stderr == (builder._ERROR + "\n").encode()


def test_cli_does_not_write_formal_sidecar() -> None:
    canonical = STATE_ROOT / builder._FORMAL_RELATIVE
    before = builder._formal_snapshot(canonical)
    completed = _run_checker(
        "--repo-root", os.fspath(ROOT), "--state-root", os.fspath(STATE_ROOT)
    )
    assert completed.returncode == 0
    assert builder._formal_snapshot(canonical) == before
