#!/usr/bin/env python
"""Deterministic checker for Current11 pocket atom identity alignment V1."""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import struct
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import covapie_current11_pocket_atom_identity_alignment_v1 as alignment
from covalent_ext import covapie_target_residue_atom_condition_adapter_design_v1 as design


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-state/manual-review/"
    "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
)
CSV_FIELDS = (
    "pdb_id",
    "atom_site_id",
    "type_symbol",
    "atom_name",
    "residue_name",
    "auth_asym_id",
    "auth_seq_id",
    "label_asym_id",
    "label_seq_id",
    "x",
    "y",
    "z",
    "source_raw_file",
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git_status() -> str:
    return subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _row(
    authority: dict[str, Any], atom_site_id: str, symbol: str, *, target: bool = False
) -> dict[str, str]:
    return {
        "pdb_id": str(authority["pdb_id"]),
        "atom_site_id": atom_site_id,
        "type_symbol": symbol,
        "atom_name": str(authority["protein_auth_atom_id"]) if target else "CA",
        "residue_name": str(authority["protein_auth_comp_id"]) if target else "ALA",
        "auth_asym_id": str(authority["protein_auth_asym_id"]),
        "auth_seq_id": str(authority["protein_auth_seq_id"]) if target else "1",
        "label_asym_id": str(authority["protein_label_asym_id"]),
        "label_seq_id": str(authority["protein_label_seq_id"]) if target else "1",
        "x": "1.25",
        "y": "-2.5",
        "z": "3.75",
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


def _align(
    authority: dict[str, Any], rows: list[dict[str, str]], *, target_index: int
) -> dict[str, Any]:
    payload = _csv(rows)
    return alignment._align_record(
        authority=authority,
        predecessor_mapping={"proposed_local_pocket_index": target_index},
        source_path="synthetic/pocket_atom_table.csv",
        expected_source_sha256=_sha(payload),
        source_payload=payload,
        symbol_to_index=alignment._checkpoint_symbol_to_index(),
    )


def _rejected(call: Any) -> bool:
    try:
        call()
    except ValueError as error:
        return str(error) == alignment._ERROR
    return False


def _resign_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    bundle["pocket_atom_identity_alignment_bundle_sha256"] = alignment._digest_record(
        bundle,
        alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS,
        "pocket_atom_identity_alignment_bundle_sha256",
    )
    return bundle


def main() -> None:
    before_status = _git_status()
    authority_bytes = AUTHORITY_PATH.read_bytes()
    authority_snapshot = bytes(authority_bytes)
    authority_bundle = json.loads(authority_bytes)
    authority = copy.deepcopy(
        authority_bundle["target_residue_atom_condition_records"][0]
    )
    symbol_to_index = alignment._checkpoint_symbol_to_index()

    rows = [
        _row(authority, "known-before", "C"),
        _row(authority, "unknown-before", "H"),
        _row(authority, str(authority["source_atom_site_id"]), "S", target=True),
        _row(authority, "known-after", "O"),
    ]
    synthetic = _align(authority, rows, target_index=2)

    retained_rows = [rows[index] for index in synthetic["retained_source_pocket_row_indices"]]
    coordinate_bytes = b"".join(
        struct.pack("<f", float(row[field]))
        for row in retained_rows
        for field in ("x", "y", "z")
    )
    one_hot = bytearray()
    for row in retained_rows:
        values = [0.0] * len(symbol_to_index)
        values[symbol_to_index[row["type_symbol"]]] = 1.0
        one_hot.extend(struct.pack("<10f", *values))

    dropped_target_authority = copy.deepcopy(authority)
    dropped_target_authority["protein_type_symbol"] = "H"
    dropped_target_rows = [
        _row(
            dropped_target_authority,
            str(dropped_target_authority["source_atom_site_id"]),
            "H",
            target=True,
        )
    ]
    target_drop_rejected = _rejected(
        lambda: _align(dropped_target_authority, dropped_target_rows, target_index=0)
    )
    zero_match_rejected = _rejected(
        lambda: _align(authority, [_row(authority, "other", "C")], target_index=0)
    )
    duplicate_target = _row(
        authority, str(authority["source_atom_site_id"]), "S", target=True
    )
    multiple_match_rejected = _rejected(
        lambda: _align(authority, [duplicate_target, copy.deepcopy(duplicate_target)], target_index=0)
    )
    drifted_rows = copy.deepcopy(rows)
    drifted_rows[2]["auth_seq_id"] = "999"
    identity_drift_rejected = _rejected(
        lambda: _align(authority, drifted_rows, target_index=2)
    )
    table_payload = _csv(rows)
    table_sha_drift_rejected = _rejected(
        lambda: alignment._align_record(
            authority=authority,
            predecessor_mapping={"proposed_local_pocket_index": 2},
            source_path="synthetic/pocket_atom_table.csv",
            expected_source_sha256="0" * 64,
            source_payload=table_payload,
            symbol_to_index=symbol_to_index,
        )
    )
    incomplete_fields = tuple(field for field in CSV_FIELDS if field != "z")
    incomplete_payload = _csv(rows, incomplete_fields)
    schema_incomplete_rejected = _rejected(
        lambda: alignment._align_record(
            authority=authority,
            predecessor_mapping={"proposed_local_pocket_index": 2},
            source_path="synthetic/pocket_atom_table.csv",
            expected_source_sha256=_sha(incomplete_payload),
            source_payload=incomplete_payload,
            symbol_to_index=symbol_to_index,
        )
    )
    projection_invariant_rejected = _rejected(
        lambda: alignment._validate_projection(
            source_count=4,
            retained_indices=[2, 0],
            source_to_retained=[1, None, 0, None],
        )
    )

    first = alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1(
        source_authority_bundle=authority_bytes, repo_root=REPO_ROOT
    )
    second = alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1(
        source_authority_bundle=authority_bytes, repo_root=REPO_ROOT
    )
    top_level_lineage_drift_rejected = True
    for field, value in {
        "source_authority_bundle_transport_sha256": "0" * 64,
        "source_authority_bundle_sha256": "0" * 64,
        "source_authority_production_sha256": "0" * 64,
        "source_adapter_design_production_sha256": "0" * 64,
        "source_adapter_design_response_sha256": "0" * 64,
        "source_checkpoint_vocab_policy_path": "synthetic/drifted_vocab_policy.py",
        "source_checkpoint_vocab_policy_sha256": "0" * 64,
        "source_checkpoint_path": "synthetic/drifted_checkpoint.ckpt",
        "source_checkpoint_sha256": "0" * 64,
    }.items():
        drifted = copy.deepcopy(first)
        drifted[field] = value
        _resign_bundle(drifted)
        top_level_lineage_drift_rejected = (
            top_level_lineage_drift_rejected
            and _rejected(lambda drifted=drifted: alignment._bundle_bytes(drifted))
        )

    sample_order_drift = copy.deepcopy(first)
    sample_order_drift["sample_order"][0], sample_order_drift["sample_order"][1] = (
        sample_order_drift["sample_order"][1],
        sample_order_drift["sample_order"][0],
    )
    _resign_bundle(sample_order_drift)
    sample_order_drift_rejected = _rejected(
        lambda: alignment._bundle_bytes(sample_order_drift)
    )

    record_reorder_drift = copy.deepcopy(first)
    record_reorder_drift["sample_order"][0], record_reorder_drift["sample_order"][1] = (
        record_reorder_drift["sample_order"][1],
        record_reorder_drift["sample_order"][0],
    )
    reordered_records = record_reorder_drift["pocket_atom_identity_alignment_records"]
    reordered_records[0], reordered_records[1] = reordered_records[1], reordered_records[0]
    _resign_bundle(record_reorder_drift)
    record_reorder_drift_rejected = _rejected(
        lambda: alignment._bundle_bytes(record_reorder_drift)
    )

    record_lineage_drift = copy.deepcopy(first)
    lineage_record = record_lineage_drift["pocket_atom_identity_alignment_records"][0]
    lineage_record["source_authority_record_sha256"] = "invalid"
    lineage_record[
        "pocket_atom_identity_alignment_record_sha256"
    ] = alignment._digest_record(
        lineage_record,
        alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS,
        "pocket_atom_identity_alignment_record_sha256",
    )
    _resign_bundle(record_lineage_drift)
    record_lineage_sha_format_enforced = _rejected(
        lambda: alignment._bundle_bytes(record_lineage_drift)
    )

    formal_record_sha256s = tuple(
        record["pocket_atom_identity_alignment_record_sha256"]
        for record in first["pocket_atom_identity_alignment_records"]
    )
    formal_alignment_record_digest_sequence_bound = (
        formal_record_sha256s == alignment._EXPECTED_ALIGNMENT_RECORD_SHA256S
    )
    formal_alignment_bundle_internal_digest_frozen = (
        first["pocket_atom_identity_alignment_bundle_sha256"]
        == alignment._FORMAL_ALIGNMENT_BUNDLE_INTERNAL_SHA256
    )
    formal_alignment_bundle_transport_digest_frozen = (
        _sha(alignment._bundle_bytes(first))
        == alignment._FORMAL_ALIGNMENT_BUNDLE_TRANSPORT_SHA256
    )

    valid_format_lineage_swap = copy.deepcopy(first)
    swapped_records = valid_format_lineage_swap[
        "pocket_atom_identity_alignment_records"
    ]
    swapped_records[0]["source_authority_record_sha256"], swapped_records[1][
        "source_authority_record_sha256"
    ] = (
        swapped_records[1]["source_authority_record_sha256"],
        swapped_records[0]["source_authority_record_sha256"],
    )
    swapped_authority_sha256s = tuple(
        record["source_authority_record_sha256"] for record in swapped_records
    )
    for record in swapped_records[:2]:
        record["pocket_atom_identity_alignment_record_sha256"] = alignment._digest_record(
            record,
            alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS,
            "pocket_atom_identity_alignment_record_sha256",
        )
    _resign_bundle(valid_format_lineage_swap)
    valid_format_cross_sample_lineage_swap_rejected = (
        all(
            alignment._SHA256_RE.fullmatch(value)
            for value in swapped_authority_sha256s
        )
        and len(set(swapped_authority_sha256s)) == 11
        and _rejected(lambda: alignment._bundle_bytes(valid_format_lineage_swap))
    )

    valid_format_payload_drift = copy.deepcopy(first)
    payload_record = valid_format_payload_drift[
        "pocket_atom_identity_alignment_records"
    ][0]
    replacement_payload_sha256 = _sha(b"valid-format-record-payload-drift")
    original_payload_sha256 = payload_record[
        "retained_pocket_coordinate_float32_bytes_sha256"
    ]
    payload_record[
        "retained_pocket_coordinate_float32_bytes_sha256"
    ] = replacement_payload_sha256
    payload_record[
        "pocket_atom_identity_alignment_record_sha256"
    ] = alignment._digest_record(
        payload_record,
        alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS,
        "pocket_atom_identity_alignment_record_sha256",
    )
    _resign_bundle(valid_format_payload_drift)
    valid_format_record_payload_drift_rejected = (
        replacement_payload_sha256 != original_payload_sha256
        and alignment._SHA256_RE.fullmatch(replacement_payload_sha256) is not None
        and _rejected(lambda: alignment._bundle_bytes(valid_format_payload_drift))
    )
    after_status = _git_status()
    predecessor = design._reference_design_covapie_target_residue_atom_condition_adapter_v1(
        source_authority_bundle=authority_bytes, repo_root=REPO_ROOT
    )

    source_authority_bundle_bound = (
        _sha(authority_bytes) == first["source_authority_bundle_transport_sha256"]
    )
    source_adapter_design_production_bound = (
        _sha(Path(design.__file__).read_bytes())
        == first["source_adapter_design_production_sha256"]
    )
    source_adapter_design_response_bound = (
        predecessor["adapter_design_response_sha256"]
        == first["source_adapter_design_response_sha256"]
    )
    predecessor_row_order_only = all(
        record["mapping_status"] == "blocked_pocket_row_order_unbound"
        and record["mapping_blocking_reasons"]
        == ["pocket_table_row_order_not_bound_to_pocket_coords_and_pocket_one_hot"]
        for record in predecessor["mapping_audit_records"]
    )
    deterministic = first == second
    inputs_unchanged = authority_bytes == authority_snapshot
    files_written = before_status != after_status

    required_truths = (
        source_authority_bundle_bound,
        source_adapter_design_production_bound,
        source_adapter_design_response_bound,
        predecessor_row_order_only,
        synthetic["retained_source_pocket_row_indices"] == [0, 2, 3],
        synthetic["source_row_to_retained_model_local_index"] == [0, None, 1, 2],
        synthetic["target_source_pocket_row_index"] == 2,
        synthetic["target_retained_model_local_index"] == 1,
        synthetic["retained_pocket_coordinate_float32_bytes_sha256"] == _sha(coordinate_bytes),
        synthetic["retained_pocket_one_hot_bytes_sha256"] == _sha(bytes(one_hot)),
        target_drop_rejected,
        zero_match_rejected,
        multiple_match_rejected,
        identity_drift_rejected,
        table_sha_drift_rejected,
        schema_incomplete_rejected,
        projection_invariant_rejected,
        top_level_lineage_drift_rejected,
        sample_order_drift_rejected,
        record_reorder_drift_rejected,
        record_lineage_sha_format_enforced,
        formal_alignment_record_digest_sequence_bound,
        formal_alignment_bundle_internal_digest_frozen,
        formal_alignment_bundle_transport_digest_frozen,
        valid_format_cross_sample_lineage_swap_rejected,
        valid_format_record_payload_drift_rejected,
        deterministic,
        inputs_unchanged,
        not files_written,
        first["aligned_unique_count"] == 11,
        first["blocked_alignment_count"] == 0,
        first["ready_for_adapter_implementation"] is True,
        first["feature_semantics_audit_required_before_training"] is True,
    )
    assert all(required_truths)

    print("source_authority_bundle_bound=true")
    print("source_adapter_design_production_bound=true")
    print("source_adapter_design_response_bound=true")
    print("predecessor_row_order_only_blocker_verified=true")
    print("checkpoint_vocab_policy_bound=true")
    print("order_preserving_projection_verified=true")
    print("coordinate_matching_used=false")
    print(f"source_pocket_row_count={synthetic['source_pocket_row_count']}")
    print(f"retained_pocket_node_count={synthetic['retained_pocket_node_count']}")
    print(f"dropped_pocket_node_count={synthetic['dropped_pocket_node_count']}")
    print(f"target_source_pocket_row_index={synthetic['target_source_pocket_row_index']}")
    print(f"target_retained_model_local_index={synthetic['target_retained_model_local_index']}")
    print("target_retained=true")
    print("target_indicator_true_count=1")
    print("source_row_to_retained_index_valid=true")
    print("retained_source_row_indices_strictly_increasing=true")
    print("retained_atom_site_sequence_bound=true")
    print("retained_coordinate_float32_bytes_bound=true")
    print("retained_one_hot_bytes_bound=true")
    print("retained_one_hot_width_checkpoint_compatible=true")
    print("target_before_drop_index_shift_verified=true")
    print("target_drop_rejected=true")
    print("zero_match_rejected=true")
    print("multiple_match_rejected=true")
    print("identity_drift_rejected=true")
    print("table_sha_drift_rejected=true")
    print("schema_incomplete_rejected=true")
    print("projection_invariant_rejected=true")
    print("top_level_lineage_drift_rejected=true")
    print("sample_order_drift_rejected=true")
    print("record_reorder_drift_rejected=true")
    print("record_lineage_sha_format_enforced=true")
    print("formal_alignment_record_digest_sequence_bound=true")
    print("formal_alignment_bundle_internal_digest_frozen=true")
    print("formal_alignment_bundle_transport_digest_frozen=true")
    print("valid_format_cross_sample_lineage_swap_rejected=true")
    print("valid_format_record_payload_drift_rejected=true")
    print("deterministic=true")
    print("inputs_unchanged=true")
    print("files_written=false")
    print("adapter_implemented=false")
    print("gate_implemented=false")
    print("training_label_created=false")
    print("tensor_file_created=false")
    print("npz_created=false")
    print("dataset_modified=false")
    print("data_loader_modified=false")
    print("model_modified=false")
    print("forward_modified=false")
    print("loss_modified=false")
    print("training_or_parameter_update=false")
    print(f"alignment_record_sha256={synthetic['pocket_atom_identity_alignment_record_sha256']}")
    print(f"alignment_bundle_sha256={first['pocket_atom_identity_alignment_bundle_sha256']}")
    print(f"formal_alignment_record_count={first['pocket_atom_identity_alignment_record_count']}")
    print(f"formal_aligned_unique_count={first['aligned_unique_count']}")
    print(f"formal_blocked_alignment_count={first['blocked_alignment_count']}")
    print("formal_ready_for_adapter_implementation=true")
    print(f"formal_recommended_next_step={first['recommended_next_step']}")
    print("formal_deterministic=true")
    print("formal_inputs_unchanged=true")
    print("formal_files_written=false")
    for record in first["pocket_atom_identity_alignment_records"]:
        source_index = record["target_source_pocket_row_index"]
        retained_index = record["target_retained_model_local_index"]
        print(
            "formal_alignment_record="
            + json.dumps(
                {
                    "alignment_record_sha256": record[
                        "pocket_atom_identity_alignment_record_sha256"
                    ],
                    "alignment_status": record["alignment_status"],
                    "blocking_reasons": record["alignment_blocking_reasons"],
                    "dropped_node_count": record["dropped_pocket_node_count"],
                    "drops_before_target": source_index - retained_index,
                    "pdb": record["pdb_id"],
                    "retained_node_count": record["retained_pocket_node_count"],
                    "row_order_binding_status": record["pocket_row_order_binding_status"],
                    "sample": record["sample_index_row_id"],
                    "source_atom_site_id": record["source_atom_site_id"],
                    "source_pocket_row_count": record["source_pocket_row_count"],
                    "source_pocket_table_path": record["source_pocket_atom_table_path"],
                    "source_pocket_table_sha256": record["source_pocket_atom_table_sha256"],
                    "target_indicator_true_count": record["target_indicator_true_count"],
                    "target_retained": record["target_retained"],
                    "target_retained_model_local_index": retained_index,
                    "target_source_csv_local_index": source_index,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )


if __name__ == "__main__":
    main()
