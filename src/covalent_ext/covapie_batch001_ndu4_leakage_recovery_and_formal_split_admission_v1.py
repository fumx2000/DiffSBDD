"""Recover NDU4 leakage evidence and inherit/assign a formal split in memory.

This additive DATA SCALE successor starts from the published batch001 formal
split owner.  It recovers only evidence that is already present in SHA-bound
local RCSB payloads, reruns the published 527-event read-only predictor, and
admits the complete recovered component without changing any prior owner.
It never performs network access, human review, tensorization, model work, or
training activation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import copy
import csv
from fractions import Fraction
import gzip
import hashlib
import io
from itertools import product
import json
import os
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
from typing import Any, Mapping, NoReturn, Sequence

from covalent_ext import covapie_batch001_formal_split_leakage_admission_v1 as formal_owner
from covalent_ext import covapie_bulk_500_event_executor_v1 as executor_owner
from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as bulk_owner
from covalent_ext import covapie_cys_sg_dataset_expansion_pipeline_v1 as split_owner


__all__ = (
    "BATCH001_NDU4_LEAKAGE_RECOVERY_ERROR_V1",
    "OUTPUT_ROOT_RELATIVE_V1",
    "OUTPUT_FILENAMES_V1",
    "Batch001NDU4LeakageRecoveryComputationV1",
    "compute_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1",
    "validate_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1",
    "build_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_artifacts_v1",
    "materialize_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_artifacts_v1",
)


BATCH001_NDU4_LEAKAGE_RECOVERY_ERROR_V1 = (
    "COVAPIE_BATCH001_NDU4_LEAKAGE_RECOVERY_AND_FORMAL_SPLIT_ADMISSION_V1_ERROR"
)
BASELINE_HEAD_V1 = "8fcaea02805eb27fb370e3f4b8d5915e52aa8240"
ROOT_CAUSE_V1 = (
    "LEGACY_SOURCE_LOCAL_PROTEIN_SEQUENCE_PROJECTION_MAPPED_CXM_TO_X_"
    "AND_SET_LEAKAGE_EVIDENCE_COMPLETE_FALSE_DESPITE_SHA_BOUND_LOCAL_"
    "MMCIF_CANONICAL_M_AND_UNIPROT_SEQUENCE_AUTHORITY"
)

OUTPUT_ROOT_RELATIVE_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1"
)
RECOVERY_EVIDENCE_V1 = "covapie_batch001_ndu4_leakage_recovery_evidence_v1.csv"
COMPONENT_REGISTRY_V1 = "covapie_batch001_ndu4_full_component_registry_v1.json"
EVENT_ADMISSION_V1 = "covapie_batch001_ndu4_formal_event_split_admission_v1.csv"
SOURCE_BINDING_INVENTORY_V1 = "covapie_batch001_ndu4_source_binding_inventory_v1.csv"
MANIFEST_V1 = (
    "covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_manifest_v1.json"
)
OUTPUT_FILENAMES_V1 = (
    RECOVERY_EVIDENCE_V1,
    COMPONENT_REGISTRY_V1,
    EVENT_ADMISSION_V1,
    SOURCE_BINDING_INVENTORY_V1,
    MANIFEST_V1,
)

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_PATH_TYPE = type(Path())
_CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT_V1 = Path(
    "covapie-state/bulk-multisource-cys-sg-v1/rcsb"
)
_ATTEMPT_RELATIVE_TO_REPOSITORY_PARENT_V1 = Path(
    "covapie-state/bulk-500-controlled-execution-v1/attempt-001/"
    "incremental_processing_outcomes_v1.json"
)
_FORMAL_ROOT_V1 = Path(
    "data/derived/covalent_small/covapie_batch001_formal_split_leakage_admission_v1"
)
_FORMAL_EVENT_V1 = _FORMAL_ROOT_V1 / formal_owner.EVENT_ADMISSION_V1
_FORMAL_COMPONENT_V1 = _FORMAL_ROOT_V1 / formal_owner.COMPONENT_REGISTRY_V1
_FORMAL_SOURCE_V1 = _FORMAL_ROOT_V1 / formal_owner.SOURCE_BINDING_INVENTORY_V1
_FORMAL_MANIFEST_V1 = _FORMAL_ROOT_V1 / formal_owner.MANIFEST_V1
_BRIDGE_STRUCTURAL_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1/"
    "covapie_batch001_model_bound_structural_evidence_v1.json"
)

_PUBLISHED_FORMAL_BINDINGS_V1: tuple[tuple[str, str, str], ...] = (
    (
        "src/covalent_ext/covapie_batch001_formal_split_leakage_admission_v1.py",
        "9841cb03ef67a6e8bbcffe1cbe0d7332a575da0e2ce5e3208a965afa45ad0d0c",
        "published formal split computation owner",
    ),
    (
        _FORMAL_EVENT_V1.as_posix(),
        "d3416ed382e6f208f79f2285138893dde3bf627653606fed8a4c3c73666001c7",
        "published complete batch001 13-event formal state",
    ),
    (
        _FORMAL_COMPONENT_V1.as_posix(),
        "76e6ecae7dfde7c9e5081a0164f9a72628e4f30550e831a8f8ba5cd3d1d16544",
        "published four-component closure and formal assignments",
    ),
    (
        _FORMAL_SOURCE_V1.as_posix(),
        "946d1b4cce5c4785a20cca1be557d071015b11e89311282bf4814a6c22e91fdc",
        "published formal split source lineage",
    ),
    (
        _FORMAL_MANIFEST_V1.as_posix(),
        "79fb2889a38016f2526adfb0f3c531a14f1bb32acc825b5c989c55217c0925dd",
        "published formal split manifest",
    ),
)

_CANONICAL_AXES_V1 = (
    "LIGAND_GRAPH",
    "LIGAND_SCAFFOLD",
    "PROTEIN_ACCESSION",
    "PROTEIN_EXACT_SEQUENCE",
    "PROTEIN_SEQUENCE_IDENTITY_GE_0.5",
)
_EXACT_AXIS_FIELDS_V1 = {
    "LIGAND_GRAPH": "ligand_graph_sha256",
    "LIGAND_SCAFFOLD": "ligand_scaffold_sha256",
    "PROTEIN_ACCESSION": "protein_accession",
    "PROTEIN_EXACT_SEQUENCE": "protein_sequence_sha256",
}
_STANDARD_AA_V1 = frozenset("ACDEFGHIKLMNPQRSTVWY")


@dataclass(frozen=True)
class Batch001NDU4LeakageRecoveryComputationV1:
    source_bindings: tuple[Mapping[str, object], ...]
    recovery_evidence_rows: tuple[Mapping[str, str], ...]
    context_counts: Mapping[str, int]
    target_event_ids: tuple[str, ...]
    target_pdb_ligand_identities: tuple[str, ...]
    pre_recovery_blocker: str
    leakage_gap_root_cause: str
    recovered_components: tuple[Mapping[str, object], ...]
    formal_split_oracle: Mapping[str, object]
    event_rows: tuple[Mapping[str, str], ...]
    published_existing_event_rows: tuple[Mapping[str, str], ...]
    published_event_header: tuple[str, ...]
    existing_published_group_assignments_unchanged: bool
    cross_split_leakage_violations: tuple[Mapping[str, object], ...]
    sample_training_admitted_count: int
    model_training_activation_authorized_count: int
    new_human_review_required_count: int
    input_state_unchanged: bool
    network_used: bool


class _RecoveryInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _RecoveryInvariantError(reason)


def _public_error(error: Exception) -> NoReturn:
    if isinstance(error, _RecoveryInvariantError):
        raise ValueError(
            f"{BATCH001_NDU4_LEAKAGE_RECOVERY_ERROR_V1}:{error.reason}"
        ) from error
    if type(error) is ValueError and str(error).startswith(
        BATCH001_NDU4_LEAKAGE_RECOVERY_ERROR_V1
    ):
        raise error
    raise ValueError(
        f"{BATCH001_NDU4_LEAKAGE_RECOVERY_ERROR_V1}:"
        f"REUSED_OWNER_REJECTED:{str(error)}"
    ) from error


def _require_repository_root(value: object) -> Path:
    path = _DEFAULT_REPOSITORY_ROOT if value is None else value
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail("REPOSITORY_ROOT_INVALID")
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _RecoveryInvariantError("REPOSITORY_ROOT_INVALID") from error
    if resolved != path or not path.is_dir() or path.is_symlink():
        _fail("REPOSITORY_ROOT_INVALID")
    return path


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object, *, ensure_ascii: bool = False) -> bytes:
    return (
        json.dumps(value, ensure_ascii=ensure_ascii, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=tuple(header), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in header})
    return buffer.getvalue().encode("utf-8")


def _read_sha_bound(path: Path, expected_sha256: str, reason: str) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise _RecoveryInvariantError(reason + "_UNREADABLE") from error
    if _sha256(payload) != expected_sha256:
        _fail(reason + "_SHA256_MISMATCH")
    return payload


def _json(payload: bytes, reason: str) -> Any:
    try:
        return json.loads(payload)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise _RecoveryInvariantError(reason + "_INVALID") from error


def _csv_rows(payload: bytes, reason: str) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        rows = list(reader)
    except (UnicodeError, csv.Error) as error:
        raise _RecoveryInvariantError(reason + "_INVALID") from error
    if not reader.fieldnames or any(None in row for row in rows):
        _fail(reason + "_INVALID")
    return tuple(reader.fieldnames), rows


def _binding_row(
    *, category: str, root_kind: str, relative_path: str,
    expected_sha256: str, payload: bytes, consumed_for: str,
) -> dict[str, object]:
    actual = _sha256(payload)
    if actual != expected_sha256:
        _fail("SOURCE_BINDING_SHA256_MISMATCH:" + relative_path)
    return {
        "source_category": category,
        "source_root_kind": root_kind,
        "relative_path": relative_path,
        "expected_sha256": expected_sha256,
        "actual_sha256": actual,
        "byte_count": len(payload),
        "consumed_for": consumed_for,
        "sha256_verified": True,
    }


def _binding_path(repo: Path, row: Mapping[str, object]) -> Path:
    root_kind = str(row["source_root_kind"])
    relative = Path(str(row["relative_path"]))
    if root_kind == "REPOSITORY_ROOT":
        return repo / relative
    if root_kind == "REPOSITORY_PARENT":
        return repo.parent / relative
    if root_kind == "CACHE_ROOT":
        return repo.parent / _CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT_V1 / relative
    _fail("SOURCE_BINDING_ROOT_KIND_INVALID:" + root_kind)


def _binding_snapshot(
    repo: Path, rows: Sequence[Mapping[str, object]],
) -> tuple[tuple[str, str, str], ...]:
    result = []
    for row in rows:
        path = _binding_path(repo, row)
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise _RecoveryInvariantError("BOUND_INPUT_UNREADABLE") from error
        result.append((
            str(row["source_root_kind"]), str(row["relative_path"]), _sha256(payload),
        ))
    return tuple(sorted(result))


def _published_inputs_v1(repo: Path) -> tuple[
    tuple[str, ...], list[dict[str, str]], Mapping[str, Any], Mapping[str, Any],
]:
    payloads: dict[str, bytes] = {}
    for relative, expected, _consumed in _PUBLISHED_FORMAL_BINDINGS_V1:
        payloads[relative] = _read_sha_bound(
            repo / relative, expected, "PUBLISHED_FORMAL_BINDING:" + relative,
        )
    event_header, event_rows = _csv_rows(
        payloads[_FORMAL_EVENT_V1.as_posix()], "PUBLISHED_FORMAL_EVENT_CSV",
    )
    component = _json(
        payloads[_FORMAL_COMPONENT_V1.as_posix()], "PUBLISHED_FORMAL_COMPONENT_JSON",
    )
    manifest = _json(
        payloads[_FORMAL_MANIFEST_V1.as_posix()], "PUBLISHED_FORMAL_MANIFEST_JSON",
    )
    if (
        type(component) is not dict
        or component.get("component_count") != 4
        or type(component.get("components")) is not list
        or type(manifest) is not dict
        or manifest.get("population_counts", {}).get(
            "formal_split_admission_event_count"
        ) != 9
    ):
        _fail("PUBLISHED_FORMAL_ARTIFACT_SCHEMA_INVALID")
    return event_header, event_rows, component, manifest


def _target_authority_v1(
    bridge_rows: Sequence[Mapping[str, str]],
    formal_rows: Sequence[Mapping[str, str]],
    outcomes: Sequence[Mapping[str, Any]],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    target_ids = tuple(sorted(formal_owner._EXPECTED_NDU_EVENT_IDS_V1))
    bridge_by_id = {row["canonical_event_id"]: row for row in bridge_rows}
    formal_by_id = {row["canonical_event_id"]: row for row in formal_rows}
    outcome_by_id = {str(row["canonical_event_id"]): row for row in outcomes}
    if (
        len(target_ids) != 4
        or not set(target_ids) <= set(bridge_by_id)
        or not set(target_ids) <= set(formal_by_id)
        or not set(target_ids) <= set(outcome_by_id)
    ):
        _fail("NDU_TARGET_IDENTITY_MISSING")
    required_true = (
        "structural_input_ready", "feature_projection_ready",
        "target_condition_ready", "reactive_pair_ready", "role_partition_ready",
        "anchor_distance_ready", "POST_geometry_ready",
        "pair_prediction_label_ready", "pair_contrastive_label_ready",
        "model_integration_preview_ready",
    )
    identities: set[str] = set()
    for event_id in target_ids:
        bridge = bridge_by_id[event_id]
        formal = formal_by_id[event_id]
        outcome = outcome_by_id[event_id]
        if (
            bridge.get("review_unit_id") != "COVAPIE_BULK_REVIEW_UNIT_3F001AD5FD754F45"
            or bridge.get("role_profile") != "STRICT_LINKER_PRESENT_V1"
            or bridge.get("applicable_task_ids") != "0|1|2|3|4"
            or any(bridge.get(field) != "true" for field in required_true)
            or bridge.get("minimal_seed_ready") != "false"
            or bridge.get("split_admission_authoritative") != "false"
            or bridge.get("sample_training_admitted") != "false"
        ):
            _fail("NDU_MODEL_LABEL_READINESS_INVALID:" + event_id)
        if (
            formal.get("leakage_evidence_complete") != "false"
            or formal.get("leakage_classification") != "LEAKAGE_EVIDENCE_INCOMPLETE"
            or formal.get("leakage_key") != ""
            or formal.get("read_only_group_id") != ""
            or formal.get("read_only_split") != "UNASSIGNED_READ_ONLY"
            or formal.get("formal_leakage_group_id") != ""
            or formal.get("assigned_split") != ""
            or formal.get("split_admission_authoritative") != "false"
            or formal.get("split_admission_status") != "UNRESOLVED_FAIL_CLOSED"
            or formal.get("split_admission_reason") != "LEAKAGE_EVIDENCE_INCOMPLETE"
        ):
            _fail("NDU_CURRENT_BLOCKER_MISMATCH:" + event_id)
        evidence = outcome.get("structural_processing", {}).get("leakage_evidence", {})
        if (
            evidence.get("complete") is not False
            or outcome.get("leakage_classification") != "LEAKAGE_EVIDENCE_INCOMPLETE"
            or outcome.get("leakage_key") is not None
            or outcome.get("predicted_group_id") is not None
            or outcome.get("predicted_split") != "UNASSIGNED_READ_ONLY"
        ):
            _fail("NDU_ATTEMPT_BLOCKER_MISMATCH:" + event_id)
        identities.add(str(outcome["pdb_id"]) + "/" + str(outcome["ligand_component_id"]))
    result = tuple(sorted(identities))
    if len(result) != 3:
        _fail("NDU_UNIQUE_PDB_LIGAND_IDENTITY_COUNT_INVALID")
    return target_ids, result


def _cache_authority_v1(
    repo: Path, identities: Sequence[str],
) -> tuple[dict[str, tuple[str, str]], Mapping[str, Any]]:
    formal_sha = next(
        expected for relative, expected, _ in _PUBLISHED_FORMAL_BINDINGS_V1
        if relative == _FORMAL_COMPONENT_V1.as_posix()
    )
    if not formal_sha:
        _fail("PUBLISHED_FORMAL_COMPONENT_BINDING_MISSING")
    bridge_sha = next(
        str(row[2]) for row in formal_owner._FIXED_REPOSITORY_BINDINGS_V1
        if row[1] == _BRIDGE_STRUCTURAL_V1.as_posix()
    )
    bridge = _json(
        _read_sha_bound(
            repo / _BRIDGE_STRUCTURAL_V1, bridge_sha,
            "PUBLISHED_BRIDGE_STRUCTURAL_EVIDENCE",
        ),
        "PUBLISHED_BRIDGE_STRUCTURAL_EVIDENCE",
    )
    rows = bridge.get("source_sha_bindings") if type(bridge) is dict else None
    if type(rows) is not list:
        _fail("PUBLISHED_BRIDGE_CACHE_BINDINGS_INVALID")
    by_path = {
        str(row.get("relative_path")): row for row in rows
        if type(row) is dict and row.get("source_root_kind") == "STRUCTURAL_SOURCE_ROOT"
    }
    result: dict[str, tuple[str, str]] = {}
    for identity in identities:
        pdb_id = identity.split("/", 1)[0]
        relative = "structures/" + pdb_id + ".cif.gz"
        row = by_path.get(relative)
        if (
            row is None
            or row.get("source_category") != "RCSB_MMCIF_PAYLOAD"
            or row.get("sha256_verified") != "true"
            or not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", "")))
        ):
            _fail("NDU_CACHE_AUTHORITY_BINDING_MISSING:" + identity)
        result[identity] = (relative, str(row["sha256"]))
    return result, bridge


def _source_bindings_v1(
    repo: Path, formal_rows: Sequence[Mapping[str, object]],
    cache_authority: Mapping[str, tuple[str, str]],
) -> tuple[Mapping[str, object], ...]:
    rows: dict[tuple[str, str], dict[str, object]] = {
        (str(row["source_root_kind"]), str(row["relative_path"])): dict(row)
        for row in formal_rows
    }
    for relative, expected, consumed in _PUBLISHED_FORMAL_BINDINGS_V1:
        payload = _read_sha_bound(
            repo / relative, expected, "PUBLISHED_FORMAL_BINDING:" + relative,
        )
        rows[("REPOSITORY_ROOT", relative)] = _binding_row(
            category="PUBLISHED_FORMAL_SPLIT_AUTHORITY",
            root_kind="REPOSITORY_ROOT",
            relative_path=relative,
            expected_sha256=expected,
            payload=payload,
            consumed_for=consumed,
        )
    for identity, (relative, expected) in sorted(cache_authority.items()):
        path = repo.parent / _CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT_V1 / relative
        payload = _read_sha_bound(path, expected, "NDU_CACHE:" + relative)
        rows[("CACHE_ROOT", relative)] = _binding_row(
            category="PUBLISHED_BRIDGE_BOUND_RCSB_MMCIF",
            root_kind="CACHE_ROOT",
            relative_path=relative,
            expected_sha256=expected,
            payload=payload,
            consumed_for="canonical protein sequence recovery for " + identity,
        )
    return tuple(rows[key] for key in sorted(rows))


def _single_token_value(tokens: Sequence[str], tag: str) -> str:
    indices = [index for index, value in enumerate(tokens) if value == tag]
    if len(indices) != 1 or indices[0] + 1 >= len(tokens):
        _fail("MMCIF_CANONICAL_SEQUENCE_TAG_INVALID:" + tag)
    value = str(tokens[indices[0] + 1])
    if value in {"", ".", "?"}:
        _fail("MMCIF_CANONICAL_SEQUENCE_VALUE_MISSING:" + tag)
    return re.sub(r"\s+", "", value)


def _recover_identity_evidence_v1(
    repo: Path, identity: str, members: Sequence[dict[str, Any]],
    cache_binding: tuple[str, str],
) -> Mapping[str, object]:
    relative, expected_sha = cache_binding
    path = repo.parent / _CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT_V1 / relative
    compressed = _read_sha_bound(path, expected_sha, "NDU_CACHE:" + relative)
    try:
        text = gzip.decompress(compressed).decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise _RecoveryInvariantError("NDU_CACHE_DECOMPRESSION_INVALID:" + identity) from error
    tokens = bulk_owner.leakage_evidence_owner.tokenize_mmcif(text)
    canonical_sequence = _single_token_value(
        tokens, "_entity_poly.pdbx_seq_one_letter_code_can",
    )
    modified_sequence = _single_token_value(
        tokens, "_entity_poly.pdbx_seq_one_letter_code",
    )
    uniprot_sequence = _single_token_value(
        tokens, "_struct_ref.pdbx_seq_one_letter_code",
    )
    _, asym_rows = bulk_owner.leakage_evidence_owner.parse_loop(text, "_struct_asym.")
    _, sequence_rows = bulk_owner.leakage_evidence_owner.parse_loop(
        text, "_entity_poly_seq.",
    )
    canonical_sha = _sha256(canonical_sequence.encode("utf-8"))
    legacy_sequences: set[str] = set()
    for event in members:
        parts = str(event["canonical_event_id"]).split(":")
        if len(parts) < 3:
            _fail("NDU_CANONICAL_EVENT_GRAMMAR_INVALID")
        protein_asym = parts[2]
        asym_to_entity = {
            row.get("_struct_asym.id", ""): row.get("_struct_asym.entity_id", "")
            for row in asym_rows
        }
        entity_id = asym_to_entity.get(protein_asym, "")
        entity_rows, numbering = (
            bulk_owner.leakage_evidence_owner._validate_entity_poly_sequence([
                row for row in sequence_rows
                if row.get("_entity_poly_seq.entity_id", "") == entity_id
            ])
        )
        monomers = [row.get("_entity_poly_seq.mon_id", "") for row in entity_rows]
        legacy_sequence, unknown_count, unknown_codes = (
            bulk_owner.leakage_evidence_owner._seq_to_one_letter(monomers)
        )
        evidence = event["structural_processing"]["leakage_evidence"]
        reproduced = bulk_owner.build_source_local_leakage_evidence_v1(
            mmcif_text=text,
            protein_label_asym_id=protein_asym,
            ccd=event["structural_processing"]["ccd_component_graph"],
        )
        if reproduced != evidence:
            _fail("PUBLISHED_HELPER_PRE_RECOVERY_REPRODUCTION_MISMATCH:" + identity)
        if (
            numbering.get("sequence_numbering_status") != "continuous_from_1"
            or len(monomers) != len(canonical_sequence)
            or unknown_count != 1
            or unknown_codes != "CXM"
            or monomers[0] != "CXM"
            or legacy_sequence != evidence.get("protein_sequence")
            or legacy_sequence[:1] != "X"
            or legacy_sequence[1:] != canonical_sequence[1:]
            or canonical_sequence[:1] != "M"
            or canonical_sequence != uniprot_sequence
            or not canonical_sequence
            or any(symbol not in _STANDARD_AA_V1 for symbol in canonical_sequence)
            or modified_sequence != "(CXM)" + canonical_sequence[1:]
        ):
            _fail("CXM_CANONICAL_SEQUENCE_RECOVERY_NOT_AUTHORITATIVE:" + identity)
        legacy_sequences.add(legacy_sequence)
        evidence["protein_sequence"] = canonical_sequence
        evidence["complete"] = True
    if len(legacy_sequences) != 1:
        _fail("IDENTITY_EVENT_PROTEIN_SEQUENCE_CONFLICT:" + identity)
    first = members[0]["structural_processing"]["leakage_evidence"]
    return {
        "identity": identity,
        "cache_relative_path": relative,
        "cache_sha256": expected_sha,
        "canonical_sequence": canonical_sequence,
        "canonical_sequence_sha256": canonical_sha,
        "legacy_sequence": next(iter(legacy_sequences)),
        "ligand_graph_sha256": str(first["ligand_graph_sha256"]),
        "ligand_scaffold_sha256": str(first["ligand_scaffold_sha256"]),
        "protein_accession": str(first["protein_accession"]),
        "protein_sequence_sha256": str(first["protein_sequence_sha256"]),
    }


def _shared_axis_values(
    left: Mapping[str, Any], right: Mapping[str, Any], axes: Sequence[str],
) -> tuple[str, ...]:
    result: list[str] = []
    for axis in axes:
        field = _EXACT_AXIS_FIELDS_V1.get(axis)
        if field is not None:
            if not left.get(field) or left.get(field) != right.get(field):
                _fail("SPANNING_EDGE_EXACT_AXIS_VALUE_INVALID:" + axis)
            result.append(axis + ":" + str(left[field]))
        elif axis == "PROTEIN_SEQUENCE_IDENTITY_GE_0.5":
            left_sequence = str(left.get("protein_sequence", ""))
            right_sequence = str(right.get("protein_sequence", ""))
            if not bulk_owner._policy_global_identity_at_least_half_v1(
                left_sequence, right_sequence,
            ):
                _fail("SPANNING_EDGE_SEQUENCE_IDENTITY_INVALID")
            result.append(
                axis + ":left_sequence_sha256="
                + _sha256(left_sequence.encode("utf-8"))
                + "|right_sequence_sha256="
                + _sha256(right_sequence.encode("utf-8"))
                + "|threshold=0.5|passed=true"
            )
        else:
            _fail("UNEXPECTED_CANONICAL_LINKING_AXIS:" + axis)
    return tuple(sorted(result))


def _spanning_edges_v1(
    members: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, object], ...]:
    by_id = {str(item["canonical_event_id"]): item for item in members}
    if len(by_id) != len(members) or not by_id:
        _fail("COMPONENT_EVENT_IDENTITY_INVALID")
    connected = {min(by_id)}
    remaining = set(by_id) - connected
    edges: list[Mapping[str, object]] = []
    while remaining:
        candidates = []
        for left_id in sorted(connected):
            left = by_id[left_id]["structural_processing"]["leakage_evidence"]
            for right_id in sorted(remaining):
                right = by_id[right_id]["structural_processing"]["leakage_evidence"]
                axes = tuple(bulk_owner._leakage_linking_axes_v1(left, right))
                if axes:
                    candidates.append((right_id, left_id, axes, left, right))
        if not candidates:
            _fail("COMPONENT_SPANNING_TREE_INCOMPLETE")
        right_id, left_id, axes, left, right = min(candidates, key=lambda item: item[:2])
        edges.append({
            "left_event_id": left_id,
            "right_event_id": right_id,
            "linking_axes": list(axes),
            "shared_axis_values": list(_shared_axis_values(left, right, axes)),
        })
        connected.add(right_id)
        remaining.remove(right_id)
    return tuple(edges)


def _all_pair_axes_v1(
    members: Sequence[Mapping[str, Any]],
) -> tuple[tuple[str, ...], Mapping[str, set[str]]]:
    axes: set[str] = set()
    by_identity: dict[str, set[str]] = {}
    for index, left_event in enumerate(members):
        left_evidence = left_event["structural_processing"]["leakage_evidence"]
        left_identity = str(left_event["pdb_id"]) + "/" + str(left_event["ligand_component_id"])
        for right_event in members[index + 1:]:
            right_evidence = right_event["structural_processing"]["leakage_evidence"]
            edge_axes = set(bulk_owner._leakage_linking_axes_v1(
                left_evidence, right_evidence,
            ))
            if edge_axes:
                right_identity = (
                    str(right_event["pdb_id"]) + "/"
                    + str(right_event["ligand_component_id"])
                )
                axes.update(edge_axes)
                by_identity.setdefault(left_identity, set()).update(edge_axes)
                by_identity.setdefault(right_identity, set()).update(edge_axes)
    return tuple(sorted(axes)), by_identity


def _reference_hits_v1(
    members: Sequence[Mapping[str, Any]], references: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, object], ...]:
    hits: dict[tuple[str, str, str, str], set[str]] = {}
    for event in members:
        evidence = event["structural_processing"]["leakage_evidence"]
        for reference in references:
            axes = bulk_owner._leakage_linking_axes_v1(evidence, reference)
            if axes:
                key = (
                    str(reference["identity"]), str(reference["leakage_key"]),
                    str(reference["group_id"]), str(reference["split"]),
                )
                hits.setdefault(key, set()).update(axes)
    return tuple({
        "reference_identity": key[0],
        "leakage_key": key[1],
        "formal_group_id": key[2],
        "formal_split": key[3],
        "linking_axes": sorted(axes),
    } for key, axes in sorted(hits.items()))


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else (
        str(value.numerator) + "/" + str(value.denominator)
    )


def _independent_new_component_oracle_v1(
    proxies: Sequence[Any], *, existing_groups: Sequence[Any],
) -> Mapping[str, object]:
    members_by_key: dict[str, set[str]] = {}
    for proxy in proxies:
        members_by_key.setdefault(str(proxy.leakage_key), set()).add(
            str(proxy.candidate_identity)
        )
    existing_by_key = {str(group.leakage_key): group for group in existing_groups}
    new_keys = sorted(set(members_by_key) - set(existing_by_key))
    if not new_keys:
        _fail("NEW_COMPONENT_ORACLE_CALLED_WITHOUT_NEW_COMPONENT")
    groups: list[dict[str, Any]] = []
    for group in existing_groups:
        groups.append({
            "key": str(group.leakage_key),
            "id": str(group.final_leakage_group_id),
            "member_count": int(group.member_count),
            "fixed_rank": split_owner.split_owner.RANK[str(group.assigned_split)],
        })
    for key in new_keys:
        group_id = "COVAPIE_EXPANSION_LEAKAGE_GROUP_" + _sha256(
            _canonical_json_bytes({
                "policy": "conservative_union_final_leakage_group_v1",
                "leakage_key": key,
            }, ensure_ascii=True)
        )[:16].upper()
        groups.append({
            "key": key,
            "id": group_id,
            "member_count": len(members_by_key[key]),
            "fixed_rank": None,
        })
    groups.sort(key=lambda item: item["id"])
    new_keys = sorted(new_keys, key=lambda key: next(
        item["id"] for item in groups if item["key"] == key
    ))
    splits = split_owner.split_owner.SPLITS
    target = split_owner.split_owner.TARGET
    total_samples = sum(int(item["member_count"]) for item in groups)
    group_count = len(groups)
    valid: list[tuple[tuple[Any, ...], tuple[int, int, int], tuple[int, int, int]]] = []
    for ranks in product(range(len(splits)), repeat=len(new_keys)):
        new_rank = dict(zip(new_keys, ranks))
        signature = tuple(
            int(item["fixed_rank"]) if item["fixed_rank"] is not None
            else new_rank[str(item["key"])]
            for item in groups
        )
        sample_counts = tuple(sum(
            int(item["member_count"])
            for item, rank in zip(groups, signature) if rank == split_rank
        ) for split_rank in range(len(splits)))
        group_counts = tuple(signature.count(rank) for rank in range(len(splits)))
        if (
            min(group_counts) < 1
            or sample_counts[0] < sample_counts[1]
            or sample_counts[0] < sample_counts[2]
        ):
            continue
        pre_signature = (
            sum(abs(
                Fraction(sample_counts[index]) - target[splits[index]] * total_samples
            ) for index in range(len(splits))),
            max(abs(
                Fraction(sample_counts[index]) - target[splits[index]] * total_samples
            ) for index in range(len(splits))),
            sum(abs(
                Fraction(group_counts[index]) - target[splits[index]] * group_count
            ) for index in range(len(splits))),
        )
        valid.append((pre_signature + (signature,), sample_counts, group_counts))
    if not valid:
        _fail("INDEPENDENT_SPLIT_ORACLE_NO_VALID_ASSIGNMENT")
    selected = min(valid, key=lambda item: item[0])
    signature = selected[0][3]
    assignment = tuple(sorted((
        str(item["key"]), str(item["id"]), splits[signature[index]],
    ) for index, item in enumerate(groups)))
    tied = [item for item in valid if item[0][:3] == selected[0][:3]]
    return {
        "mode": "INDEPENDENT_FINITE_FROZEN_EXTENSION_ENUMERATION",
        "candidate_assignment_count": len(splits) ** len(new_keys),
        "valid_assignment_count": len(valid),
        "new_key_order": list(new_keys),
        "selected_assignment": [list(item) for item in assignment],
        "selected_sample_counts": list(selected[1]),
        "selected_group_counts": list(selected[2]),
        "selected_objective_fractions": [
            _fraction_text(value) for value in selected[0][:3]
        ],
        "tie_count_before_signature": len(tied),
        "selected_full_signature": list(signature),
        "lexicographic_minimum_tie_break_applied": (
            tuple(signature) == min(tuple(item[0][3]) for item in tied)
        ),
    }


def _published_batch_groups_v1(
    component_artifact: Mapping[str, Any],
) -> tuple[split_owner.LeakageGroupAssignmentV1, ...]:
    result = []
    for item in component_artifact["components"]:
        identities = tuple(sorted(str(value) for value in item["full_member_pdb_ligand_identities"]))
        result.append(split_owner.LeakageGroupAssignmentV1(
            leakage_key=str(item["leakage_key"]),
            final_leakage_group_id=str(item["formal_group_id"]),
            member_count=len(identities),
            assigned_split=str(item["formal_split"]),
            frozen=True,
            member_identities=identities,
        ))
    return tuple(result)


def _formal_component_v1(item: Mapping[str, Any]) -> formal_owner.FormalComponentAdmissionV1:
    return formal_owner.FormalComponentAdmissionV1(
        component_name=str(item.get("component_name", "NDU_RECOVERED_COMPONENT")),
        leakage_key=str(item["leakage_key"]),
        classification=str(item["classification"]),
        linking_axes=tuple(str(value) for value in item["linking_axes"]),
        source_evidence_linking_axis_values=tuple(
            str(value) for value in item["source_evidence_linking_axis_values"]
        ),
        full_member_pdb_ligand_identities=tuple(
            str(value) for value in item["full_member_pdb_ligand_identities"]
        ),
        full_member_canonical_event_ids=tuple(
            str(value) for value in item["full_member_canonical_event_ids"]
        ),
        batch001_target_event_ids=tuple(
            str(value) for value in item["batch001_target_event_ids"]
        ),
        non_target_component_event_ids=tuple(
            str(value) for value in item["non_target_component_event_ids"]
        ),
        read_only_group_id=str(item["read_only_group_id"]),
        read_only_split=str(item["read_only_split"]),
        formal_group_id=str(item["formal_group_id"]),
        formal_split=str(item["formal_split"]),
        group_parity=bool(item["group_parity"]),
        split_parity=bool(item["split_parity"]),
        formal_assignment_status=str(item["formal_assignment_status"]),
        formal_assignment_is_authority_candidate=bool(
            item["formal_assignment_is_authority_candidate"]
        ),
    )


def _recovery_evidence_rows_v1(
    target_ids: Sequence[str], outcomes: Sequence[Mapping[str, Any]],
    diagnostics: Mapping[str, Mapping[str, object]],
    identity_axes: Mapping[str, set[str]], attempt_sha: str,
) -> tuple[Mapping[str, str], ...]:
    events_by_identity: dict[str, list[str]] = {}
    for event in outcomes:
        event_id = str(event["canonical_event_id"])
        if event_id in target_ids:
            identity = str(event["pdb_id"]) + "/" + str(event["ligand_component_id"])
            events_by_identity.setdefault(identity, []).append(event_id)
    rows: list[Mapping[str, str]] = []
    for identity in sorted(diagnostics):
        diagnostic = diagnostics[identity]
        cache_path = str(diagnostic["cache_relative_path"])
        cache_sha = str(diagnostic["cache_sha256"])
        values = {
            "LIGAND_GRAPH": str(diagnostic["ligand_graph_sha256"]),
            "LIGAND_SCAFFOLD": str(diagnostic["ligand_scaffold_sha256"]),
            "PROTEIN_ACCESSION": str(diagnostic["protein_accession"]),
            "PROTEIN_EXACT_SEQUENCE": str(diagnostic["protein_sequence_sha256"]),
        }
        for axis in _CANONICAL_AXES_V1:
            sequence_axis = axis == "PROTEIN_SEQUENCE_IDENTITY_GE_0.5"
            source_path = (
                cache_path if axis.startswith("PROTEIN_")
                else _ATTEMPT_RELATIVE_TO_REPOSITORY_PARENT_V1.as_posix()
            )
            source_root = "CACHE_ROOT" if axis.startswith("PROTEIN_") else "REPOSITORY_PARENT"
            source_sha = cache_sha if axis.startswith("PROTEIN_") else attempt_sha
            pre_value = (
                "LEGACY_PROJECTED_SEQUENCE_SHA256:"
                + _sha256(str(diagnostic["legacy_sequence"]).encode("utf-8"))
                if sequence_axis else values[axis]
            )
            recovered = (
                "CANONICAL_SEQUENCE_SHA256:"
                + str(diagnostic["canonical_sequence_sha256"])
                if sequence_axis else values[axis]
            )
            rows.append({
                "target_scope": "NDU4",
                "pdb_ligand_identity": identity,
                "canonical_event_ids": "|".join(sorted(events_by_identity[identity])),
                "evidence_axis": axis,
                "pre_recovery_availability": "false" if sequence_axis else "true",
                "pre_recovery_status": (
                    "CANONICAL_SEQUENCE_BLOCKED_BY_SINGLE_UNKNOWN_CXM"
                    if sequence_axis else "AVAILABLE_CANONICAL"
                ),
                "pre_recovery_value": pre_value,
                "failure_reason": ROOT_CAUSE_V1 if sequence_axis else "NONE",
                "recovery_source_root_kind": source_root,
                "recovery_source_path": source_path,
                "recovery_source_sha256": source_sha,
                "recovery_source_authority": (
                    "PUBLISHED_BRIDGE_BOUND_RCSB_MMCIF"
                    if source_root == "CACHE_ROOT"
                    else "PUBLISHED_ATTEMPT001_OUTCOMES_BOUND_BY_FORMAL_OWNER"
                ),
                "recovery_method_owner": (
                    "bulk_owner.leakage_evidence_owner.tokenize_mmcif+"
                    "official_mmcif_entity_poly_canonical_and_struct_ref_sequence"
                    if sequence_axis
                    else "bulk_owner.build_source_local_leakage_evidence_v1"
                ),
                "recovered_value": recovered,
                "canonical_value_validation": (
                    "OFFICIAL_MMCIF_CANONICAL_SEQUENCE_EQUALS_LOCAL_UNIPROT_REFERENCE_"
                    "AND_RESOLVES_SINGLE_CXM_TO_M"
                    if sequence_axis
                    else "PUBLISHED_HELPER_REPRODUCED_PRE_RECOVERY_VALUE_EXACTLY"
                ),
                "used_for_component_linking": (
                    "true" if axis in identity_axes.get(identity, set()) else "false"
                ),
            })
    return tuple(rows)


def _event_rows_v1(
    published_header: Sequence[str], published_rows: Sequence[Mapping[str, str]],
    target_ids: Sequence[str], outcomes: Sequence[Mapping[str, Any]],
    components: Sequence[Mapping[str, object]],
) -> tuple[tuple[Mapping[str, str], ...], tuple[Mapping[str, str], ...]]:
    target_set = set(target_ids)
    outcome_by_id = {str(item["canonical_event_id"]): item for item in outcomes}
    component_by_target = {
        event_id: component
        for component in components
        for event_id in component["batch001_target_event_ids"]
    }
    result: list[Mapping[str, str]] = []
    published_existing: list[Mapping[str, str]] = []
    for published in published_rows:
        event_id = published["canonical_event_id"]
        row = dict(published)
        if event_id not in target_set:
            published_existing.append(dict(published))
            row.update({
                "formal_assignment_method": "PUBLISHED_FORMAL_JOINT_ASSIGNMENT",
                "recovery_provenance_status": "NOT_APPLICABLE_PUBLISHED_ROW",
                "new_human_review_required": "false",
            })
        else:
            event = outcome_by_id[event_id]
            component = component_by_target[event_id]
            evidence = event["structural_processing"]["leakage_evidence"]
            is_new = not bool(component["group_existed_pre_recovery"])
            row.update({
                "model_integration_preview_ready": "true",
                "leakage_evidence_complete": "true" if evidence.get("complete") is True else "false",
                "leakage_classification": str(component["classification"]),
                "leakage_key": str(component["leakage_key"]),
                "read_only_group_id": str(component["read_only_group_id"]),
                "read_only_split": str(component["read_only_split"]),
                "formal_leakage_group_id": str(component["formal_group_id"]),
                "assigned_split": str(component["formal_split"]),
                "group_parity": str(component["group_parity"]).lower(),
                "split_parity": str(component["split_parity"]).lower(),
                "read_only_prediction_is_authority": "false",
                "formal_joint_assignment_is_authority_candidate": (
                    "true" if is_new else "false"
                ),
                "split_admission_authoritative": "true",
                "split_admission_status": (
                    "FORMALLY_ADMITTED_TO_NEW_FROZEN_SPLIT"
                    if is_new else "FORMALLY_ADMITTED_TO_EXISTING_FROZEN_SPLIT"
                ),
                "split_admission_reason": (
                    "FORMAL_FROZEN_EXTENSION_ASSIGNMENT_WITH_OWNER_ORACLE_PARITY"
                    if is_new else "INHERITED_EXISTING_LEAKAGE_GROUP_SPLIT_AUTHORITY"
                ),
                "sample_training_admitted": "false",
                "model_training_activation_authorized": "false",
                "formal_assignment_method": (
                    "FROZEN_EXTENSION_POLICY_ASSIGNMENT"
                    if is_new else "INHERIT_EXISTING_FROZEN_GROUP_SPLIT"
                ),
                "recovery_provenance_status": "EXISTING_LOCAL_AUTHORITY_RECOVERY_COMPLETE",
                "new_human_review_required": "false",
            })
        result.append(row)
    if len(published_existing) != 9:
        _fail("PUBLISHED_EXISTING_EVENT_COUNT_INVALID")
    return tuple(result), tuple(published_existing)


def _validate_computation_v1(
    computation: Batch001NDU4LeakageRecoveryComputationV1,
) -> None:
    if type(computation) is not Batch001NDU4LeakageRecoveryComputationV1:
        _fail("COMPUTATION_TYPE_INVALID")
    if dict(computation.context_counts) != {
        "historical_frozen_outcome_count": 250,
        "known_control_outcome_count": 27,
        "incremental_attempt_outcome_count": 250,
        "full_predictor_population_count": 527,
        "frozen_reference_record_count": 14,
        "frozen_leakage_group_count": 7,
        "frozen_historical_group_count": 5,
        "frozen_cumulative_group_count": 2,
    }:
        _fail("CONTROLLED_527_CONTEXT_INVALID")
    if (
        len(computation.target_event_ids) != 4
        or len(set(computation.target_event_ids)) != 4
        or len(computation.target_pdb_ligand_identities) != 3
        or computation.pre_recovery_blocker != "LEAKAGE_EVIDENCE_INCOMPLETE"
        or computation.leakage_gap_root_cause != ROOT_CAUSE_V1
    ):
        _fail("TARGET_OR_ROOT_CAUSE_INVALID")
    if (
        len(computation.recovery_evidence_rows)
        != len(computation.target_pdb_ligand_identities) * len(_CANONICAL_AXES_V1)
    ):
        _fail("RECOVERY_EVIDENCE_MATRIX_SIZE_INVALID")
    binding_by_path = {
        (str(row["source_root_kind"]), str(row["relative_path"])): row
        for row in computation.source_bindings
    }
    if len(binding_by_path) != len(computation.source_bindings):
        _fail("SOURCE_BINDING_DUPLICATE")
    for row in computation.source_bindings:
        if (
            row.get("sha256_verified") is not True
            or row.get("actual_sha256") != row.get("expected_sha256")
        ):
            _fail("SOURCE_BINDING_INVALID")
    recovery_axes_by_identity: dict[str, set[str]] = {}
    canonical_sequence_by_identity: dict[str, str] = {}
    for row in computation.recovery_evidence_rows:
        identity = row["pdb_ligand_identity"]
        axis = row["evidence_axis"]
        recovery_axes_by_identity.setdefault(identity, set()).add(axis)
        binding = binding_by_path.get((
            row["recovery_source_root_kind"], row["recovery_source_path"],
        ))
        if binding is None or binding["actual_sha256"] != row["recovery_source_sha256"]:
            _fail("RECOVERY_SOURCE_BINDING_INVALID")
        if axis == "PROTEIN_SEQUENCE_IDENTITY_GE_0.5":
            if (
                row["failure_reason"] != ROOT_CAUSE_V1
                or not row["recovered_value"].startswith("CANONICAL_SEQUENCE_SHA256:")
            ):
                _fail("RECOVERED_CANONICAL_SEQUENCE_ROW_INVALID")
            canonical_sequence_by_identity[identity] = row["recovered_value"].split(":", 1)[1]
        elif row["pre_recovery_value"] != row["recovered_value"]:
            _fail("NONMISSING_CANONICAL_AXIS_CHANGED")
    if (
        set(recovery_axes_by_identity) != set(computation.target_pdb_ligand_identities)
        or any(axes != set(_CANONICAL_AXES_V1) for axes in recovery_axes_by_identity.values())
    ):
        _fail("RECOVERY_AXIS_POPULATION_INVALID")
    all_component_targets: list[str] = []
    for component in computation.recovered_components:
        events = tuple(str(value) for value in component["full_member_canonical_event_ids"])
        targets = tuple(str(value) for value in component["batch001_target_event_ids"])
        non_targets = tuple(str(value) for value in component["non_target_component_event_ids"])
        identities = tuple(str(value) for value in component["full_member_pdb_ligand_identities"])
        edges = tuple(component["connectivity_spanning_edges"])
        edge_nodes = {
            str(edge[field]) for edge in edges
            for field in ("left_event_id", "right_event_id")
        }
        if (
            not events
            or len(events) != len(set(events))
            or len(identities) != len(set(identities))
            or set(targets) | set(non_targets) != set(events)
            or set(targets) & set(non_targets)
            or len(edges) != len(events) - 1
            or edge_nodes != set(events)
            or component["cross_split_leakage_status"] != "PASSED_ZERO_VIOLATIONS"
            or component["non_target_members_are_training_samples"] is not False
            or component["non_target_members_inherit_split_reservation_only"] is not True
        ):
            _fail("RECOVERED_COMPONENT_CLOSURE_INVALID")
        target_sequence_map = component["target_identity_canonical_sequence_sha256"]
        if dict(target_sequence_map) != {
            identity: canonical_sequence_by_identity[identity]
            for identity in target_sequence_map
        }:
            _fail("COMPONENT_CANONICAL_SEQUENCE_BINDING_INVALID")
        if component["group_existed_pre_recovery"]:
            lineage = component["authority_lineage"]
            if (
                len(lineage) != 1
                or component["formal_group_id"] != component["read_only_group_id"]
                or component["formal_split"] != component["read_only_split"]
                or lineage[0]["formal_group_id"] != component["formal_group_id"]
                or lineage[0]["formal_split"] != component["formal_split"]
            ):
                _fail("EXISTING_GROUP_INHERITANCE_INVALID")
        all_component_targets.extend(targets)
    if sorted(all_component_targets) != sorted(computation.target_event_ids):
        _fail("TARGET_COMPONENT_ASSIGNMENT_INVALID")
    if computation.cross_split_leakage_violations:
        _fail("CROSS_SPLIT_LEAKAGE_VIOLATION")
    oracle = computation.formal_split_oracle
    if (
        oracle.get("production_owner_independent_oracle_parity") is not True
        or oracle.get("selected_assignment") != oracle.get("independent_selected_assignment")
    ):
        _fail("FORMAL_SPLIT_POLICY_ORACLE_PARITY_INVALID")
    if (
        len(computation.event_rows) != 13
        or len({row["canonical_event_id"] for row in computation.event_rows}) != 13
        or len(computation.published_existing_event_rows) != 9
    ):
        _fail("SUCCESSOR_EVENT_POPULATION_INVALID")
    published_by_id = {
        row["canonical_event_id"]: row for row in computation.published_existing_event_rows
    }
    for row in computation.event_rows:
        event_id = row["canonical_event_id"]
        if event_id in published_by_id and any(
            row.get(field) != published_by_id[event_id].get(field)
            for field in computation.published_event_header
        ):
            _fail("PUBLISHED_EXISTING_EVENT_SEMANTICS_CHANGED")
        if (
            row.get("sample_training_admitted") != "false"
            or row.get("model_training_activation_authorized") != "false"
        ):
            _fail("TRAINING_ACTIVATION_BOUNDARY_VIOLATED")
    target_rows = [
        row for row in computation.event_rows
        if row["canonical_event_id"] in computation.target_event_ids
    ]
    if (
        len(target_rows) != 4
        or any(row["leakage_evidence_complete"] != "true" for row in target_rows)
        or any(row["split_admission_authoritative"] != "true" for row in target_rows)
    ):
        _fail("NDU_FORMAL_ADMISSION_INVALID")
    if (
        computation.existing_published_group_assignments_unchanged is not True
        or computation.sample_training_admitted_count != 0
        or computation.model_training_activation_authorized_count != 0
        or computation.new_human_review_required_count != 0
        or computation.input_state_unchanged is not True
        or computation.network_used is not False
    ):
        _fail("SUCCESSOR_SAFETY_STATE_INVALID")


def compute_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1(
    *, repository_root: object = None,
) -> Batch001NDU4LeakageRecoveryComputationV1:
    """Recompute the recovery and formal admission entirely in memory."""

    try:
        repo = _require_repository_root(repository_root)
        published_header, published_rows, published_components, _published_manifest = (
            _published_inputs_v1(repo)
        )
        (
            outcomes, bridge_rows, leakage_context, _leakage_registry,
            frozen_snapshot, context_counts, formal_source_rows,
        ) = formal_owner._reproduce_read_only_context_v1(repo)
        target_ids, target_identities = _target_authority_v1(
            bridge_rows, published_rows, outcomes,
        )
        cache_authority, _bridge_structural = _cache_authority_v1(
            repo, target_identities,
        )
        source_bindings = _source_bindings_v1(
            repo, formal_source_rows, cache_authority,
        )
        input_before = _binding_snapshot(repo, source_bindings)
        by_identity: dict[str, list[dict[str, Any]]] = {}
        for event in outcomes:
            if event["canonical_event_id"] in target_ids:
                identity = str(event["pdb_id"]) + "/" + str(event["ligand_component_id"])
                by_identity.setdefault(identity, []).append(event)
        if set(by_identity) != set(target_identities):
            _fail("NDU_TARGET_IDENTITY_MISMATCH")
        diagnostics = {
            identity: _recover_identity_evidence_v1(
                repo, identity, by_identity[identity], cache_authority[identity],
            )
            for identity in target_identities
        }
        processing_context = executor_owner.build_processing_context_v1(repo)
        bulk_owner.apply_leakage_predictions_read_only_v1(
            outcomes,
            historical=processing_context.historical_identities,
            context=leakage_context,
        )
        outcome_by_id = {str(item["canonical_event_id"]): item for item in outcomes}
        for event_id in target_ids:
            event = outcome_by_id[event_id]
            if (
                event["structural_processing"]["leakage_evidence"].get("complete") is not True
                or event.get("leakage_classification") == "LEAKAGE_EVIDENCE_INCOMPLETE"
                or not event.get("leakage_key")
                or not event.get("predicted_group_id")
                or event.get("predicted_split") not in split_owner.split_owner.SPLITS
            ):
                _fail("CANONICAL_READ_ONLY_PREDICTION_DID_NOT_RECOVER:" + event_id)
        independent = formal_owner._independent_complete_components_v1(outcomes)
        root_by_event = {
            str(item["canonical_event_id"]): root
            for root, members in independent.items() for item in members
        }
        roots = tuple(sorted({root_by_event[event_id] for event_id in target_ids}))
        lane_by_event = {
            str(item["canonical_event_id"]): (
                "historical" if index < 250
                else "control" if index < 277
                else "incremental"
            )
            for index, item in enumerate(outcomes)
        }
        existing_by_group = {
            str(item["final_leakage_group_id"]): item for item in frozen_snapshot
        }
        recovered_components: list[dict[str, object]] = []
        identity_axes: dict[str, set[str]] = {}
        for component_index, root in enumerate(roots, start=1):
            members = independent[root]
            event_ids = tuple(str(item["canonical_event_id"]) for item in members)
            component_targets = tuple(sorted(set(event_ids) & set(target_ids)))
            identities = tuple(sorted({
                str(item["pdb_id"]) + "/" + str(item["ligand_component_id"])
                for item in members
            }))
            target_predictions = {
                (
                    str(outcome_by_id[event_id]["leakage_classification"]),
                    str(outcome_by_id[event_id]["leakage_key"]),
                    str(outcome_by_id[event_id]["predicted_group_id"]),
                    str(outcome_by_id[event_id]["predicted_split"]),
                )
                for event_id in component_targets
            }
            if len(target_predictions) != 1:
                _fail("TARGET_COMPONENT_PREDICTION_CONFLICT")
            classification, leakage_key, read_only_group, read_only_split = next(
                iter(target_predictions)
            )
            pair_axes, per_identity_axes = _all_pair_axes_v1(members)
            for identity, axes in per_identity_axes.items():
                identity_axes.setdefault(identity, set()).update(axes)
            source_values = tuple(sorted({
                str(axis)
                for member in members
                for axis in member["structural_processing"]["leakage_evidence"].get(
                    "linking_axes", ()
                )
            }))
            reference_hits = _reference_hits_v1(
                members, tuple(leakage_context["references"]),
            )
            existing = existing_by_group.get(read_only_group)
            group_existed = existing is not None
            if group_existed:
                if (
                    existing["leakage_key"] != leakage_key
                    or existing["assigned_split"] != read_only_split
                    or classification not in {
                        "HISTORICAL_BASELINE_COMPONENT",
                        "SAME_EXISTING_EXPANSION_COMPONENT",
                    }
                    or {str(item["formal_group_id"]) for item in reference_hits}
                    != {read_only_group}
                ):
                    _fail("EXISTING_GROUP_AUTHORITY_LINEAGE_INVALID")
                formal_group = read_only_group
                formal_split = read_only_split
                assignment_status = "EXISTING_FROZEN_GROUP_SPLIT_INHERITED"
                authority_lineage = [{
                    "leakage_key": str(existing["leakage_key"]),
                    "formal_group_id": str(existing["final_leakage_group_id"]),
                    "formal_split": str(existing["assigned_split"]),
                    "frozen": bool(existing["frozen"]),
                    "published_member_count": int(existing["member_count"]),
                    "published_member_identities": list(existing["member_identities"]),
                    "matching_reference_identities": [
                        str(item["reference_identity"]) for item in reference_hits
                    ],
                }]
            else:
                if classification != "NEW_EXPANSION_COMPONENT":
                    _fail("NONEXISTING_COMPONENT_CLASSIFICATION_INVALID")
                formal_group = ""
                formal_split = ""
                assignment_status = "PENDING_FROZEN_EXTENSION_POLICY"
                authority_lineage = []
            target_sequence_map = {
                identity: str(diagnostics[identity]["canonical_sequence_sha256"])
                for identity in identities if identity in diagnostics
            }
            recovered_components.append({
                "component_name": "NDU_RECOVERED_COMPONENT_" + str(component_index).zfill(3),
                "classification": classification,
                "leakage_key": leakage_key,
                "read_only_group_id": read_only_group,
                "read_only_split": read_only_split,
                "formal_group_id": formal_group,
                "formal_split": formal_split,
                "group_parity": bool(formal_group and formal_group == read_only_group),
                "split_parity": bool(formal_split and formal_split == read_only_split),
                "formal_assignment_status": assignment_status,
                "formal_assignment_is_authority_candidate": not group_existed,
                "group_existed_pre_recovery": group_existed,
                "linking_axes": list(pair_axes),
                "source_evidence_linking_axis_values": list(source_values),
                "full_identity_count": len(identities),
                "full_member_pdb_ligand_identities": list(identities),
                "full_event_count": len(event_ids),
                "full_member_canonical_event_ids": list(event_ids),
                "batch001_target_event_count": len(component_targets),
                "batch001_target_event_ids": list(component_targets),
                "non_target_component_event_count": len(event_ids) - len(component_targets),
                "non_target_component_event_ids": sorted(set(event_ids) - set(component_targets)),
                "non_target_members_are_training_samples": False,
                "non_target_members_inherit_split_reservation_only": True,
                "event_source_lanes": {
                    event_id: lane_by_event[event_id] for event_id in event_ids
                },
                "target_identity_canonical_sequence_sha256": target_sequence_map,
                "connectivity_spanning_edges": list(_spanning_edges_v1(members)),
                "reference_hits": list(reference_hits),
                "authority_lineage": authority_lineage,
                "cross_split_leakage_status": "PENDING_AUDIT",
            })
        existing_groups = tuple(leakage_context["existing_groups"])
        frozen_extension_groups = (
            *existing_groups, *_published_batch_groups_v1(published_components),
        )
        new_components = [
            item for item in recovered_components
            if not item["group_existed_pre_recovery"]
        ]
        if new_components:
            proxies = tuple(
                SimpleNamespace(candidate_identity=identity, leakage_key=item["leakage_key"])
                for item in new_components
                for identity in item["full_member_pdb_ligand_identities"]
            )
            owner_map = split_owner.assign_expansion_leakage_splits_v1(
                proxies, existing_groups=frozen_extension_groups,
            )
            oracle_detail = _independent_new_component_oracle_v1(
                proxies, existing_groups=frozen_extension_groups,
            )
            owner_assignment = tuple(sorted(
                (str(key), str(group), str(split))
                for key, (group, split) in owner_map.items()
            ))
            oracle_assignment = tuple(
                tuple(str(value) for value in item)
                for item in oracle_detail["selected_assignment"]
            )
            if owner_assignment != oracle_assignment:
                _fail("FORMAL_SPLIT_OWNER_ORACLE_MISMATCH")
            for item in new_components:
                group, split = owner_map[str(item["leakage_key"])]
                item.update({
                    "formal_group_id": group,
                    "formal_split": split,
                    "group_parity": group == item["read_only_group_id"],
                    "split_parity": split == item["read_only_split"],
                    "formal_assignment_status": "NEW_COMPONENT_FROZEN_EXTENSION_ASSIGNED",
                    "formal_assignment_is_authority_candidate": True,
                    "authority_lineage": [{
                        "leakage_key": str(item["leakage_key"]),
                        "formal_group_id": group,
                        "formal_split": split,
                        "frozen": True,
                        "assignment_owner": (
                            "split_owner.assign_expansion_leakage_splits_v1"
                        ),
                    }],
                })
            formal_oracle = {
                **oracle_detail,
                "production_owner": "split_owner.assign_expansion_leakage_splits_v1",
                "selected_assignment": [list(item) for item in owner_assignment],
                "independent_selected_assignment": [list(item) for item in oracle_assignment],
                "production_owner_independent_oracle_parity": True,
                "existing_groups_fixed": True,
            }
        else:
            inherited = tuple(sorted((
                str(item["leakage_key"]), str(item["formal_group_id"]),
                str(item["formal_split"]),
            ) for item in recovered_components))
            formal_oracle = {
                "mode": "INDEPENDENT_EXISTING_FROZEN_GROUP_INHERITANCE_ORACLE",
                "candidate_assignment_count": 1,
                "valid_assignment_count": 1,
                "new_component_count": 0,
                "policy_enumeration_required": False,
                "allowed_assignment_domain_by_key": {
                    key: [split] for key, _group, split in inherited
                },
                "production_owner": "PUBLISHED_FROZEN_GROUP_SPLIT_AUTHORITY",
                "selected_assignment": [list(item) for item in inherited],
                "independent_selected_assignment": [list(item) for item in inherited],
                "production_owner_independent_oracle_parity": True,
                "existing_groups_fixed": True,
                "tie_break_required": False,
            }
        cross_components = [
            _formal_component_v1(item) for item in published_components["components"]
        ] + [_formal_component_v1(item) for item in recovered_components]
        violations = formal_owner._cross_component_leakage_violations_v1(
            outcomes, cross_components, tuple(leakage_context["references"]),
        )
        if violations:
            _fail("CROSS_SPLIT_LEAKAGE_VIOLATION")
        for item in recovered_components:
            item["cross_split_leakage_status"] = "PASSED_ZERO_VIOLATIONS"
        event_rows, existing_event_rows = _event_rows_v1(
            published_header, published_rows, target_ids, outcomes, recovered_components,
        )
        attempt_binding = next(
            row for row in source_bindings
            if row["source_root_kind"] == "REPOSITORY_PARENT"
            and row["relative_path"]
            == _ATTEMPT_RELATIVE_TO_REPOSITORY_PARENT_V1.as_posix()
        )
        recovery_rows = _recovery_evidence_rows_v1(
            target_ids, outcomes, diagnostics, identity_axes,
            str(attempt_binding["actual_sha256"]),
        )
        input_after = _binding_snapshot(repo, source_bindings)
        if input_before != input_after:
            _fail("BOUND_INPUT_MUTATED_DURING_COMPUTATION")
        computation = Batch001NDU4LeakageRecoveryComputationV1(
            source_bindings=source_bindings,
            recovery_evidence_rows=recovery_rows,
            context_counts=dict(context_counts),
            target_event_ids=target_ids,
            target_pdb_ligand_identities=target_identities,
            pre_recovery_blocker="LEAKAGE_EVIDENCE_INCOMPLETE",
            leakage_gap_root_cause=ROOT_CAUSE_V1,
            recovered_components=tuple(recovered_components),
            formal_split_oracle=formal_oracle,
            event_rows=event_rows,
            published_existing_event_rows=existing_event_rows,
            published_event_header=published_header,
            existing_published_group_assignments_unchanged=True,
            cross_split_leakage_violations=violations,
            sample_training_admitted_count=sum(
                row["sample_training_admitted"] == "true" for row in event_rows
            ),
            model_training_activation_authorized_count=sum(
                row["model_training_activation_authorized"] == "true"
                for row in event_rows
            ),
            new_human_review_required_count=sum(
                row["new_human_review_required"] == "true" for row in event_rows
            ),
            input_state_unchanged=True,
            network_used=False,
        )
        _validate_computation_v1(computation)
        return computation
    except Exception as error:
        _public_error(error)


def validate_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1(
    computation: object,
) -> bool:
    try:
        _validate_computation_v1(computation)  # type: ignore[arg-type]
        return True
    except Exception as error:
        _public_error(error)


_RECOVERY_HEADER_V1 = (
    "target_scope", "pdb_ligand_identity", "canonical_event_ids",
    "evidence_axis", "pre_recovery_availability", "pre_recovery_status",
    "pre_recovery_value", "failure_reason", "recovery_source_root_kind",
    "recovery_source_path", "recovery_source_sha256",
    "recovery_source_authority", "recovery_method_owner", "recovered_value",
    "canonical_value_validation", "used_for_component_linking",
)
_SOURCE_HEADER_V1 = (
    "source_category", "source_root_kind", "relative_path", "expected_sha256",
    "actual_sha256", "byte_count", "consumed_for", "sha256_verified",
)
_EVENT_EXTRA_HEADER_V1 = (
    "formal_assignment_method", "recovery_provenance_status",
    "new_human_review_required",
)


def build_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_artifacts_v1(
    *, repository_root: object = None,
) -> dict[str, bytes]:
    """Build the exact five deterministic output artifacts."""

    try:
        computation = (
            compute_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1(
                repository_root=repository_root,
            )
        )
        recovery_payload = _csv_bytes(
            _RECOVERY_HEADER_V1, computation.recovery_evidence_rows,
        )
        component_artifact = {
            "schema_version": "covapie_batch001_ndu4_full_component_registry_v1",
            "artifact_role": (
                "COMPLETE_527_CONTEXT_NDU_COMPONENT_CLOSURE_AND_SPLIT_RESERVATION"
            ),
            "component_count": len(computation.recovered_components),
            "components": list(computation.recovered_components),
        }
        component_payload = _canonical_json_bytes(component_artifact)
        event_header = (*computation.published_event_header, *_EVENT_EXTRA_HEADER_V1)
        event_payload = _csv_bytes(event_header, computation.event_rows)
        source_payload = _csv_bytes(_SOURCE_HEADER_V1, computation.source_bindings)
        output_payloads = {
            RECOVERY_EVIDENCE_V1: recovery_payload,
            COMPONENT_REGISTRY_V1: component_payload,
            EVENT_ADMISSION_V1: event_payload,
            SOURCE_BINDING_INVENTORY_V1: source_payload,
        }
        target_rows = [
            row for row in computation.event_rows
            if row["canonical_event_id"] in computation.target_event_ids
        ]
        manifest = {
            "schema_version": (
                "covapie_batch001_ndu4_leakage_recovery_and_formal_split_"
                "admission_manifest_v1"
            ),
            "stage": (
                "batch001_ndu4_leakage_recovery_and_formal_split_admission_v1"
            ),
            "artifact_role": (
                "LEAKAGE_AND_SPLIT_AUTHORITY_SUCCESSOR_NOT_MODEL_TRAINING_ACTIVATION"
            ),
            "baseline_head": BASELINE_HEAD_V1,
            "artifact_bindings": {
                name: {"sha256": _sha256(payload)}
                for name, payload in sorted(output_payloads.items())
            },
            "input_bindings": [{
                "source_root_kind": str(row["source_root_kind"]),
                "relative_path": str(row["relative_path"]),
                "sha256": str(row["actual_sha256"]),
            } for row in computation.source_bindings],
            "target_ndu4_event_ids": list(computation.target_event_ids),
            "target_pdb_ligand_identities": list(
                computation.target_pdb_ligand_identities
            ),
            "pre_recovery_blocker": computation.pre_recovery_blocker,
            "leakage_gap_root_cause": computation.leakage_gap_root_cause,
            "recovery_success": True,
            "recovered_evidence_axes": list(_CANONICAL_AXES_V1),
            "context_counts": dict(computation.context_counts),
            "full_component_count": len(computation.recovered_components),
            "full_component_memberships": [{
                "leakage_key": item["leakage_key"],
                "formal_group_id": item["formal_group_id"],
                "formal_split": item["formal_split"],
                "full_member_pdb_ligand_identities": item[
                    "full_member_pdb_ligand_identities"
                ],
                "full_member_canonical_event_ids": item[
                    "full_member_canonical_event_ids"
                ],
            } for item in computation.recovered_components],
            "formal_assignment": {
                "method": computation.formal_split_oracle["mode"],
                "owner_oracle_parity": True,
                "detail": dict(computation.formal_split_oracle),
                "read_only_prediction_is_authority": False,
            },
            "existing_split_assignments_preserved": True,
            "cross_split_leakage_violation_count": len(
                computation.cross_split_leakage_violations
            ),
            "ndu_formal_splits": sorted({row["assigned_split"] for row in target_rows}),
            "population_counts": {
                "batch001_positive_event_count": 13,
                "existing_authoritative_event_count": 9,
                "newly_authoritative_ndu_event_count": 4,
                "successor_split_authoritative_event_count": 13,
                "sample_training_admitted_count": 0,
                "model_training_activation_authorized_count": 0,
                "new_human_review_required_count": 0,
            },
            "safety": {
                "network_used": False,
                "new_human_review_required": False,
                "training_performed": False,
                "Trainer_used": False,
                "backward_performed": False,
                "optimizer_step_performed": False,
                "model_training_activation_authorized": False,
                "original_state_mutated": False,
                "cache_mutated": False,
                "published_formal_split_artifacts_mutated": False,
            },
            "ready_for_gpt_review": True,
            "ready_for_publication": True,
            "ready_for_training": False,
            "full_training_authorized": False,
            "recommended_next_step_exactly": (
                "gpt_review_then_publish_and_build_next_model_usable_dataset_"
                "admission_materialization_successor"
            ),
        }
        manifest_payload = _canonical_json_bytes(manifest)
        return {**output_payloads, MANIFEST_V1: manifest_payload}
    except Exception as error:
        _public_error(error)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_artifacts_v1(
    *, repository_root: object = None,
) -> dict[str, bytes]:
    """Write only the five authorized files under the new successor root."""

    try:
        repo = _require_repository_root(repository_root)
        artifacts = (
            build_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_artifacts_v1(
                repository_root=repo,
            )
        )
        output_root = repo / OUTPUT_ROOT_RELATIVE_V1
        if output_root.exists():
            unexpected = {
                path.name for path in output_root.iterdir()
                if path.name not in OUTPUT_FILENAMES_V1
            }
            if unexpected:
                _fail("OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES")
        for name in OUTPUT_FILENAMES_V1:
            _atomic_write(output_root / name, artifacts[name])
        return artifacts
    except Exception as error:
        _public_error(error)
