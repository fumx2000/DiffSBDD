from __future__ import annotations

import copy
import csv
import hashlib
import inspect
import io
import json
import os
import stat
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import covapie_current11_pocket_atom_identity_alignment_v1 as alignment
from covalent_ext import covapie_target_residue_atom_condition_adapter_design_v1 as design


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-state/manual-review/"
    "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
)

CSV_FIELDS = (
    "sample_preparation_input_id",
    "pdb_id",
    "pocket_radius_angstrom",
    "atom_site_id",
    "group_pdb",
    "type_symbol",
    "atom_name",
    "residue_name",
    "chain_id",
    "residue_index",
    "auth_asym_id",
    "auth_seq_id",
    "label_asym_id",
    "label_seq_id",
    "x",
    "y",
    "z",
    "min_distance_to_ligand_angstrom",
    "source_raw_file",
)


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
def authority(authority_bytes: bytes) -> dict[str, object]:
    return json.loads(authority_bytes)["target_residue_atom_condition_records"][0]


@pytest.fixture(scope="module")
def formal_bundle(authority_bytes: bytes) -> dict[str, object]:
    return alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1(
        source_authority_bundle=authority_bytes,
        repo_root=REPO_ROOT,
    )


def _row(
    authority: dict[str, object],
    atom_site_id: str,
    symbol: str,
    *,
    target: bool = False,
    coordinates: tuple[str, str, str] = ("1.25", "-2.5", "3.75"),
) -> dict[str, str]:
    if target:
        atom_name = str(authority["protein_auth_atom_id"])
        residue_name = str(authority["protein_auth_comp_id"])
        auth_asym_id = str(authority["protein_auth_asym_id"])
        auth_seq_id = str(authority["protein_auth_seq_id"])
        label_asym_id = str(authority["protein_label_asym_id"])
        label_seq_id = str(authority["protein_label_seq_id"])
    else:
        atom_name = "CA"
        residue_name = "ALA"
        auth_asym_id = str(authority["protein_auth_asym_id"])
        auth_seq_id = "1"
        label_asym_id = str(authority["protein_label_asym_id"])
        label_seq_id = "1"
    return {
        "sample_preparation_input_id": "SYNTHETIC",
        "pdb_id": str(authority["pdb_id"]),
        "pocket_radius_angstrom": "8.0",
        "atom_site_id": atom_site_id,
        "group_pdb": "ATOM",
        "type_symbol": symbol,
        "atom_name": atom_name,
        "residue_name": residue_name,
        "chain_id": auth_asym_id,
        "residue_index": auth_seq_id,
        "auth_asym_id": auth_asym_id,
        "auth_seq_id": auth_seq_id,
        "label_asym_id": label_asym_id,
        "label_seq_id": label_seq_id,
        "x": coordinates[0],
        "y": coordinates[1],
        "z": coordinates[2],
        "min_distance_to_ligand_angstrom": "1.0",
        "source_raw_file": "synthetic/source.cif",
    }


def _csv(rows: list[dict[str, str]], fields: tuple[str, ...] = CSV_FIELDS) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _synthetic_record(
    authority: dict[str, object], rows: list[dict[str, str]], *, proposed: int
) -> dict[str, object]:
    payload = _csv(rows)
    predecessor = {
        "proposed_local_pocket_index": proposed,
    }
    return alignment._align_record(
        authority=authority,
        predecessor_mapping=predecessor,
        source_path="synthetic/pocket_atom_table.csv",
        expected_source_sha256=_sha(payload),
        source_payload=payload,
        symbol_to_index=alignment._checkpoint_symbol_to_index(),
    )


def _synthetic_rows(authority: dict[str, object]) -> list[dict[str, str]]:
    return [
        _row(authority, "known-before", "C"),
        _row(authority, "unknown-before", "H"),
        _row(authority, str(authority["source_atom_site_id"]), "S", target=True),
        _row(authority, "known-after", "O"),
    ]


def test_public_signature_all_and_silent_import() -> None:
    signature = inspect.signature(
        alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1
    )
    assert tuple(signature.parameters) == ("source_authority_bundle", "repo_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert alignment.__all__ == (
        "compile_covapie_current11_pocket_atom_identity_alignment_v1",
    )
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(REPO_ROOT / "src"))
    completed = subprocess.run(
        [sys.executable, "-B", "-c", "import covalent_ext.covapie_current11_pocket_atom_identity_alignment_v1"],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_frozen_predecessor_authority_and_policy_bindings(authority_bytes: bytes) -> None:
    assert _sha(
        (REPO_ROOT / "src/covalent_ext/covapie_target_residue_atom_condition_adapter_design_v1.py").read_bytes()
    ) == alignment._ADAPTER_DESIGN_PRODUCTION_SHA256
    assert _sha(
        (REPO_ROOT / alignment._VOCAB_POLICY_PATH).read_bytes()
    ) == alignment._VOCAB_POLICY_SHA256
    assert _sha(
        (REPO_ROOT / alignment._FILTER_POLICY_PATH).read_bytes()
    ) == alignment._FILTER_POLICY_SHA256
    assert _sha(
        (REPO_ROOT / alignment._FLATTEN_POLICY_PATH).read_bytes()
    ) == alignment._FLATTEN_POLICY_SHA256
    response = design._reference_design_covapie_target_residue_atom_condition_adapter_v1(
        source_authority_bundle=authority_bytes, repo_root=REPO_ROOT
    )
    assert response["adapter_design_response_sha256"] == alignment._ADAPTER_DESIGN_RESPONSE_SHA256
    assert response["current11_unique_mapping_count"] == 0
    assert response["current11_blocked_mapping_count"] == 11
    assert alignment._validate_predecessor(response)


def test_checkpoint_vocab_is_exact_width_and_keeps_target_s() -> None:
    symbol_to_index = alignment._checkpoint_symbol_to_index()
    assert len(symbol_to_index) == 10
    assert set(symbol_to_index.values()) == set(range(10))
    assert symbol_to_index["S"] == 3
    assert "H" not in symbol_to_index


def test_exact29_records_exact20_bundle_and_digests(formal_bundle: dict[str, object]) -> None:
    assert len(alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS) == 29
    assert len(alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS) == 20
    assert tuple(formal_bundle) == alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS
    unsigned_bundle = dict(formal_bundle)
    digest = unsigned_bundle.pop("pocket_atom_identity_alignment_bundle_sha256")
    assert digest == _sha(_canonical(unsigned_bundle))
    for record in formal_bundle["pocket_atom_identity_alignment_records"]:  # type: ignore[index]
        assert tuple(record) == alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS
        unsigned_record = dict(record)
        record_digest = unsigned_record.pop("pocket_atom_identity_alignment_record_sha256")
        assert record_digest == _sha(_canonical(unsigned_record))


def test_formal_counts_sample_order_and_readiness(formal_bundle: dict[str, object]) -> None:
    assert formal_bundle["pocket_atom_identity_alignment_record_count"] == 11
    assert formal_bundle["aligned_unique_count"] == 11
    assert formal_bundle["blocked_alignment_count"] == 0
    assert formal_bundle["ready_for_adapter_implementation"] is True
    assert formal_bundle["recommended_next_step"] == "implement_covapie_target_residue_atom_condition_adapter_v1"
    assert formal_bundle["feature_semantics_audit_required_before_training"] is True
    assert len(formal_bundle["sample_order"]) == 11  # type: ignore[arg-type]


def test_compile_is_deterministic_zero_write_input_unchanged_and_json_only(
    authority_bytes: bytes,
) -> None:
    before_status = subprocess.run(
        ["git", "status", "--short"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout
    snapshot = bytes(authority_bytes)
    first = alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1(
        source_authority_bundle=authority_bytes, repo_root=REPO_ROOT
    )
    second = alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1(
        source_authority_bundle=authority_bytes, repo_root=REPO_ROOT
    )
    after_status = subprocess.run(
        ["git", "status", "--short"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout
    assert first == second
    assert authority_bytes == snapshot
    assert before_status == after_status

    def walk(value: object) -> None:
        assert not isinstance(value, Path)
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(first)


def test_physical_csv_order_and_keep_drop_projection_are_preserved(
    authority: dict[str, object],
) -> None:
    record = _synthetic_record(authority, _synthetic_rows(authority), proposed=2)
    assert record["retained_source_pocket_row_indices"] == [0, 2, 3]
    assert record["source_row_to_retained_model_local_index"] == [0, None, 1, 2]
    assert record["retained_source_atom_site_ids"] == [
        "known-before",
        authority["source_atom_site_id"],
        "known-after",
    ]
    assert record["retained_pocket_node_count"] == 3
    assert record["dropped_pocket_node_count"] == 1


def test_target_before_drop_index_shift(authority: dict[str, object]) -> None:
    record = _synthetic_record(authority, _synthetic_rows(authority), proposed=2)
    assert record["target_source_pocket_row_index"] == 2
    assert record["target_retained_model_local_index"] == 1
    assert record["target_retained"] is True
    assert record["target_indicator_true_count"] == 1


def test_target_after_drop_does_not_shift(authority: dict[str, object]) -> None:
    rows = [
        _row(authority, "known-before", "C"),
        _row(authority, str(authority["source_atom_site_id"]), "S", target=True),
        _row(authority, "unknown-after", "H"),
    ]
    record = _synthetic_record(authority, rows, proposed=1)
    assert record["target_source_pocket_row_index"] == 1
    assert record["target_retained_model_local_index"] == 1


def test_non_target_unknown_atom_is_dropped(authority: dict[str, object]) -> None:
    record = _synthetic_record(authority, _synthetic_rows(authority), proposed=2)
    assert record["checkpoint_projection_policy"] == alignment._PROJECTION_POLICY
    assert record["alignment_status"] == "alignment_ready_unique"
    assert record["pocket_row_order_binding_status"] == alignment._BOUND


def test_target_dropped_by_checkpoint_projection_is_rejected(authority: dict[str, object]) -> None:
    changed = copy.deepcopy(authority)
    changed["protein_type_symbol"] = "H"
    rows = [_row(changed, str(changed["source_atom_site_id"]), "H", target=True)]
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        _synthetic_record(changed, rows, proposed=0)


def test_zero_and_multiple_target_matches_are_rejected(authority: dict[str, object]) -> None:
    zero = [_row(authority, "other", "C")]
    target = _row(authority, str(authority["source_atom_site_id"]), "S", target=True)
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        _synthetic_record(authority, zero, proposed=0)
    duplicate_payload = _csv([target, copy.deepcopy(target)])
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        alignment._align_record(
            authority=authority,
            predecessor_mapping={"proposed_local_pocket_index": 0},
            source_path="synthetic/pocket.csv",
            expected_source_sha256=_sha(duplicate_payload),
            source_payload=duplicate_payload,
            symbol_to_index=alignment._checkpoint_symbol_to_index(),
        )


def test_authority_identity_and_predecessor_index_drift_are_rejected(
    authority: dict[str, object],
) -> None:
    rows = _synthetic_rows(authority)
    drifted = copy.deepcopy(rows)
    drifted[2]["auth_seq_id"] = "999"
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        _synthetic_record(authority, drifted, proposed=2)
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        _synthetic_record(authority, rows, proposed=1)


def test_table_sha_schema_and_invalid_identity_are_rejected(authority: dict[str, object]) -> None:
    rows = _synthetic_rows(authority)
    payload = _csv(rows)
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        alignment._align_record(
            authority=authority,
            predecessor_mapping={"proposed_local_pocket_index": 2},
            source_path="synthetic/pocket.csv",
            expected_source_sha256="0" * 64,
            source_payload=payload,
            symbol_to_index=alignment._checkpoint_symbol_to_index(),
        )
    incomplete_fields = tuple(field for field in CSV_FIELDS if field != "z")
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        alignment._align_record(
            authority=authority,
            predecessor_mapping={"proposed_local_pocket_index": 2},
            source_path="synthetic/pocket.csv",
            expected_source_sha256=_sha(_csv(rows, incomplete_fields)),
            source_payload=_csv(rows, incomplete_fields),
            symbol_to_index=alignment._checkpoint_symbol_to_index(),
        )
    blank = copy.deepcopy(rows)
    blank[0]["atom_name"] = ""
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        _synthetic_record(authority, blank, proposed=2)


@pytest.mark.parametrize("token", ["nan", "inf", "-inf", "1e1000", "not-a-number"])
def test_nonfinite_or_non_float32_coordinate_is_rejected(
    authority: dict[str, object], token: str
) -> None:
    rows = _synthetic_rows(authority)
    rows[0]["x"] = token
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        _synthetic_record(authority, rows, proposed=2)


def test_coordinate_and_one_hot_byte_digests_are_exact(authority: dict[str, object]) -> None:
    rows = _synthetic_rows(authority)
    record = _synthetic_record(authority, rows, proposed=2)
    retained = [rows[index] for index in (0, 2, 3)]
    coordinate_bytes = b"".join(
        struct.pack("<f", float(row[field]))
        for row in retained
        for field in ("x", "y", "z")
    )
    mapping = alignment._checkpoint_symbol_to_index()
    one_hot = bytearray()
    for row in retained:
        values = [0.0] * 10
        values[mapping[row["type_symbol"]]] = 1.0
        one_hot.extend(struct.pack("<10f", *values))
    assert record["retained_pocket_coordinate_float32_bytes_sha256"] == _sha(coordinate_bytes)
    assert record["retained_pocket_one_hot_bytes_sha256"] == _sha(bytes(one_hot))
    unpacked = struct.unpack(f"<{len(retained) * 10}f", one_hot)
    assert all(sum(unpacked[start : start + 10]) == 1.0 for start in range(0, len(unpacked), 10))


def test_source_and_retained_sequence_digests_are_order_sensitive(
    authority: dict[str, object],
) -> None:
    rows = _synthetic_rows(authority)
    first = _synthetic_record(authority, rows, proposed=2)
    reordered = [rows[3], rows[1], rows[2], rows[0]]
    second = _synthetic_record(authority, reordered, proposed=2)
    assert first["source_pocket_identity_sequence_sha256"] != second["source_pocket_identity_sequence_sha256"]
    assert first["source_pocket_coordinate_sequence_sha256"] == second["source_pocket_coordinate_sequence_sha256"]
    assert first["source_pocket_type_sequence_sha256"] != second["source_pocket_type_sequence_sha256"]
    assert first["retained_pocket_identity_sequence_sha256"] != second["retained_pocket_identity_sequence_sha256"]


def test_coordinate_matching_is_not_used(authority: dict[str, object]) -> None:
    same_coordinates = ("9.0", "9.0", "9.0")
    rows = [
        _row(authority, "not-target", "C", coordinates=same_coordinates),
        _row(
            authority,
            str(authority["source_atom_site_id"]),
            "S",
            target=True,
            coordinates=same_coordinates,
        ),
    ]
    record = _synthetic_record(authority, rows, proposed=1)
    assert record["target_source_pocket_row_index"] == 1
    assert record["target_indicator_true_count"] == 1


def test_projection_validator_accepts_exact_map_and_fails_closed() -> None:
    assert alignment._validate_projection(
        source_count=4,
        retained_indices=[0, 2, 3],
        source_to_retained=[0, None, 1, 2],
    )
    invalid = (
        ([2, 0], [1, None, 0, None]),
        ([0, 2, 2], [0, None, 1, None]),
        ([0, 4], [0, None, None, None]),
        ([0, 2], [0, None, 2, None]),
    )
    for retained, mapping in invalid:
        with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
            alignment._validate_projection(
                source_count=4,
                retained_indices=retained,
                source_to_retained=mapping,
            )


def test_public_bad_calls_use_canonical_value_error(authority_bytes: bytes) -> None:
    tampered = bytearray(authority_bytes)
    tampered[20] ^= 1
    bad_calls = (
        {"source_authority_bundle": bytes(tampered), "repo_root": REPO_ROOT},
        {"source_authority_bundle": bytearray(authority_bytes), "repo_root": REPO_ROOT},
        {"source_authority_bundle": authority_bytes, "repo_root": str(REPO_ROOT)},
    )
    for kwargs in bad_calls:
        with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
            alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1(**kwargs)  # type: ignore[arg-type]


def test_bundle_bytes_are_strict_canonical_and_under_limit(formal_bundle: dict[str, object]) -> None:
    payload = alignment._bundle_bytes(formal_bundle)
    assert payload == _canonical(formal_bundle)
    assert not payload.startswith(b"\xef\xbb\xbf")
    assert b"\x00" not in payload
    assert not payload.endswith((b"\n", b"\r"))
    assert len(payload) < 2 * 1024 * 1024


def test_resigned_top_level_lineage_drift_is_rejected(
    formal_bundle: dict[str, object],
) -> None:
    drift_values = {
        "source_authority_bundle_transport_sha256": "0" * 64,
        "source_authority_bundle_sha256": "0" * 64,
        "source_authority_production_sha256": "0" * 64,
        "source_adapter_design_production_sha256": "0" * 64,
        "source_adapter_design_response_sha256": "0" * 64,
        "source_checkpoint_vocab_policy_path": "synthetic/drifted_vocab_policy.py",
        "source_checkpoint_vocab_policy_sha256": "0" * 64,
        "source_checkpoint_path": "synthetic/drifted_checkpoint.ckpt",
        "source_checkpoint_sha256": "0" * 64,
    }
    for field, value in drift_values.items():
        drifted = copy.deepcopy(formal_bundle)
        drifted[field] = value
        drifted["pocket_atom_identity_alignment_bundle_sha256"] = alignment._digest_record(
            drifted,
            alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS,
            "pocket_atom_identity_alignment_bundle_sha256",
        )
        with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
            alignment._bundle_bytes(drifted)


def test_resigned_sample_and_record_order_drift_is_rejected(
    formal_bundle: dict[str, object],
) -> None:
    sample_only = copy.deepcopy(formal_bundle)
    sample_only["sample_order"][0], sample_only["sample_order"][1] = (  # type: ignore[index]
        sample_only["sample_order"][1],  # type: ignore[index]
        sample_only["sample_order"][0],  # type: ignore[index]
    )
    sample_only["pocket_atom_identity_alignment_bundle_sha256"] = alignment._digest_record(
        sample_only,
        alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS,
        "pocket_atom_identity_alignment_bundle_sha256",
    )
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        alignment._bundle_bytes(sample_only)

    sample_and_records = copy.deepcopy(formal_bundle)
    sample_and_records["sample_order"][0], sample_and_records["sample_order"][1] = (  # type: ignore[index]
        sample_and_records["sample_order"][1],  # type: ignore[index]
        sample_and_records["sample_order"][0],  # type: ignore[index]
    )
    records = sample_and_records["pocket_atom_identity_alignment_records"]
    records[0], records[1] = records[1], records[0]  # type: ignore[index]
    sample_and_records[
        "pocket_atom_identity_alignment_bundle_sha256"
    ] = alignment._digest_record(
        sample_and_records,
        alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS,
        "pocket_atom_identity_alignment_bundle_sha256",
    )
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        alignment._bundle_bytes(sample_and_records)


def test_resigned_record_lineage_sha_format_drift_is_rejected(
    formal_bundle: dict[str, object],
) -> None:
    drifted = copy.deepcopy(formal_bundle)
    record = drifted["pocket_atom_identity_alignment_records"][0]  # type: ignore[index]
    record["source_authority_record_sha256"] = "invalid"  # type: ignore[index]
    record["pocket_atom_identity_alignment_record_sha256"] = alignment._digest_record(  # type: ignore[index]
        record,
        alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS,
        "pocket_atom_identity_alignment_record_sha256",
    )
    drifted["pocket_atom_identity_alignment_bundle_sha256"] = alignment._digest_record(
        drifted,
        alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS,
        "pocket_atom_identity_alignment_bundle_sha256",
    )
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        alignment._bundle_bytes(drifted)


def test_resigned_valid_format_cross_sample_record_drift_is_rejected(
    formal_bundle: dict[str, object],
) -> None:
    lineage_swap = copy.deepcopy(formal_bundle)
    records = lineage_swap["pocket_atom_identity_alignment_records"]  # type: ignore[assignment]
    first_record, second_record = records[0], records[1]  # type: ignore[index]
    first_record["source_authority_record_sha256"], second_record[
        "source_authority_record_sha256"
    ] = (
        second_record["source_authority_record_sha256"],
        first_record["source_authority_record_sha256"],
    )
    authority_sha256s = [
        record["source_authority_record_sha256"] for record in records  # type: ignore[union-attr]
    ]
    assert all(alignment._SHA256_RE.fullmatch(value) for value in authority_sha256s)
    assert len(set(authority_sha256s)) == 11
    for record in (first_record, second_record):
        record["pocket_atom_identity_alignment_record_sha256"] = alignment._digest_record(
            record,
            alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS,
            "pocket_atom_identity_alignment_record_sha256",
        )
    lineage_swap[
        "pocket_atom_identity_alignment_bundle_sha256"
    ] = alignment._digest_record(
        lineage_swap,
        alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS,
        "pocket_atom_identity_alignment_bundle_sha256",
    )
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        alignment._bundle_bytes(lineage_swap)

    payload_drift = copy.deepcopy(formal_bundle)
    record = payload_drift["pocket_atom_identity_alignment_records"][0]  # type: ignore[index]
    replacement = _sha(b"valid-format-record-payload-drift")
    assert replacement != record["retained_pocket_coordinate_float32_bytes_sha256"]  # type: ignore[index]
    assert alignment._SHA256_RE.fullmatch(replacement)
    record["retained_pocket_coordinate_float32_bytes_sha256"] = replacement  # type: ignore[index]
    record["pocket_atom_identity_alignment_record_sha256"] = alignment._digest_record(  # type: ignore[index]
        record,
        alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS,
        "pocket_atom_identity_alignment_record_sha256",
    )
    payload_drift[
        "pocket_atom_identity_alignment_bundle_sha256"
    ] = alignment._digest_record(
        payload_drift,
        alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS,
        "pocket_atom_identity_alignment_bundle_sha256",
    )
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        alignment._bundle_bytes(payload_drift)


def test_formal_bundle_internal_and_transport_digests_are_frozen(
    formal_bundle: dict[str, object],
) -> None:
    records = formal_bundle["pocket_atom_identity_alignment_records"]  # type: ignore[assignment]
    assert tuple(
        record["pocket_atom_identity_alignment_record_sha256"]
        for record in records  # type: ignore[union-attr]
    ) == alignment._EXPECTED_ALIGNMENT_RECORD_SHA256S
    assert (
        formal_bundle["pocket_atom_identity_alignment_bundle_sha256"]
        == alignment._FORMAL_ALIGNMENT_BUNDLE_INTERNAL_SHA256
    )
    assert (
        _sha(alignment._bundle_bytes(formal_bundle))
        == alignment._FORMAL_ALIGNMENT_BUNDLE_TRANSPORT_SHA256
    )


def test_materializer_exact_existing_is_idempotent(formal_bundle: dict[str, object], tmp_path: Path) -> None:
    output = tmp_path / "bundle.json"
    first = alignment._materialize_covapie_current11_pocket_atom_identity_alignment_bundle_v1(
        bundle=formal_bundle, output_path=output
    )
    before = output.stat()
    second = alignment._materialize_covapie_current11_pocket_atom_identity_alignment_bundle_v1(
        bundle=formal_bundle, output_path=output
    )
    after = output.stat()
    assert first["publication_mode"] == "published_new"
    assert second["publication_mode"] == "idempotent_existing"
    assert before.st_ino == after.st_ino
    assert before.st_mtime_ns == after.st_mtime_ns
    assert output.read_bytes() == alignment._bundle_bytes(formal_bundle)
    assert stat.S_IMODE(after.st_mode) == 0o644 and after.st_nlink == 1


def test_materializer_rejects_symlink_and_conflict(formal_bundle: dict[str, object], tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_bytes(b"unknown")
    symlink = tmp_path / "bundle.json"
    symlink.symlink_to(target)
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        alignment._materialize_covapie_current11_pocket_atom_identity_alignment_bundle_v1(
            bundle=formal_bundle, output_path=symlink
        )
    symlink.unlink()
    symlink.write_bytes(b"conflict")
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        alignment._materialize_covapie_current11_pocket_atom_identity_alignment_bundle_v1(
            bundle=formal_bundle, output_path=symlink
        )
    assert symlink.read_bytes() == b"conflict"
    assert target.read_bytes() == b"unknown"


def test_publication_failure_does_not_delete_unknown_file(
    formal_bundle: dict[str, object], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "bundle.json"
    unknown = tmp_path / "keep.me"
    unknown.write_bytes(b"keep")

    def fail_link(*_args: object, **_kwargs: object) -> None:
        raise OSError("synthetic publication failure")

    monkeypatch.setattr(alignment.os, "link", fail_link)
    with pytest.raises(ValueError, match=f"^{alignment._ERROR}$"):
        alignment._materialize_covapie_current11_pocket_atom_identity_alignment_bundle_v1(
            bundle=formal_bundle, output_path=output
        )
    assert not output.exists()
    assert unknown.read_bytes() == b"keep"
    assert list(tmp_path.glob(".*.tmp")) == []


def test_five_masks_orthogonal_and_no_training_critical_source_changed() -> None:
    assert design.CANONICAL_MASK_SEMANTIC_NAMES == (
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    )
    protected = (
        "dataset.py",
        "lightning_modules.py",
        "equivariant_diffusion",
        "data/prepare_crossdocked.py",
        "src/covalent_ext/diffsbdd_input_adapter.py",
    )
    assert subprocess.run(
        ["git", "diff", "--quiet", "--", *protected], cwd=REPO_ROOT, check=False
    ).returncode == 0
    assert subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *protected],
        cwd=REPO_ROOT,
        check=False,
    ).returncode == 0


def test_no_npz_tensor_or_training_label_created_by_task() -> None:
    task_paths = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert not any(Path(path).suffix in {".npz", ".pt", ".ckpt", ".pth", ".pkl"} for path in task_paths)
    production_text = (
        REPO_ROOT / "src/covalent_ext/covapie_current11_pocket_atom_identity_alignment_v1.py"
    ).read_text(encoding="utf-8")
    assert "training_label" not in production_text
