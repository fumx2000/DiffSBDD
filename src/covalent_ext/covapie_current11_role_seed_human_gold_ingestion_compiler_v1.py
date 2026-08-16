"""Compile reviewed Current11 Exact3 roles and seed authority into machine truth.

The compiler is pure and in-memory.  The separately named offline loader binds
the canonical Current11 V1 review artifact by relative path, physical mode, and
SHA256 before delegating to the compiler.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import re
import stat
from datetime import datetime
from pathlib import Path
from typing import NoReturn


__all__ = (
    "HUMAN_GOLD_INGESTION_SCHEMA_V1",
    "CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_SHA256_V1",
    "CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_RELATIVE_PATH_V1",
    "compile_covapie_current11_role_seed_human_gold_v1",
    "load_and_compile_covapie_current11_role_seed_human_gold_v1",
)


INGESTION_COMPILER_ERROR = (
    "COVAPIE_CURRENT11_ROLE_SEED_HUMAN_GOLD_INGESTION_COMPILER_V1_ERROR"
)
HUMAN_GOLD_INGESTION_SCHEMA_V1 = (
    "covapie_current11_role_seed_human_gold_ingestion_v1"
)
CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_SHA256_V1 = (
    "104cc3ec5c9cf6a250f07348695c0a52ca938ed3be082a61e4a983e6f1359ae4"
)
CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_RELATIVE_PATH_V1 = Path(
    "manual-review-aids/current11-trainable-supervision-role-seed-v1/"
    "current11_role_seed_review_decisions.csv"
)

_MACHINE_AUTHORITY_PAYLOAD_SCHEMA_V1 = (
    "covapie_current11_machine_authority_payload_v1"
)
_CURRENT11_SAMPLE_KEYS_V1 = tuple(
    f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
)
_DECISION_COLUMNS_V1 = (
    "sample_key",
    "pdb_id",
    "ligand_comp_id",
    "retained_heavy_ligand_local_index_0based",
    "atom_site_id",
    "atom_name",
    "role_decision",
    "minimal_seed_or_anchor_membership",
    "reviewer_id",
    "review_decision",
    "review_timestamp",
    "attestation",
    "review_notes",
)
_ROLE_NAME_TO_ID_V1 = {"scaffold": 0, "linker": 1, "warhead": 2}
_ROLE_AUTHORITY_FIELDS = frozenset((
    "authority_class",
    "role_ids",
    "role_valid",
    "candidate_role_names",
    "proposal_only",
    "human_approved",
    "review_disposition",
    "reviewer_id",
    "attestation",
))
_SEED_AUTHORITY_FIELDS = frozenset((
    "authority_class",
    "mask",
    "valid",
    "candidate_mask",
    "proposal_only",
    "human_approved",
    "review_disposition",
    "reviewer_id",
    "attestation",
))
_TIMESTAMP_UTC = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
_SELF_REVIEWER_IDS = frozenset(("codex", "openai", "chatgpt", "gpt"))


class _IngestionInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _IngestionInvariantError()


def _dict(value: object) -> dict[str, object]:
    if type(value) is not dict:
        _fail()
    return value  # type: ignore[return-value]


def _list(value: object, *, length: int | None = None) -> list[object]:
    if type(value) is not list or (length is not None and len(value) != length):
        _fail()
    return value  # type: ignore[return-value]


def _text(value: object, *, nonempty: bool = True) -> str:
    if type(value) is not str or (nonempty and not value):
        _fail()
    return value


def _review_text(value: object) -> str:
    text = _text(value)
    if not text.strip():
        _fail()
    return text


def _parse_decision_rows(decision_csv_bytes: object) -> tuple[bytes, list[dict[str, str]]]:
    if type(decision_csv_bytes) is not bytes:
        _fail()
    payload = decision_csv_bytes
    try:
        decoded = payload.decode("utf-8")
        parsed = list(csv.reader(io.StringIO(decoded, newline=""), strict=True))
    except (UnicodeDecodeError, csv.Error):
        _fail()
    if not parsed or tuple(parsed[0]) != _DECISION_COLUMNS_V1:
        _fail()
    data = parsed[1:]
    if not data or any(len(row) != len(_DECISION_COLUMNS_V1) for row in data):
        _fail()
    rows = [dict(zip(_DECISION_COLUMNS_V1, row, strict=True)) for row in data]
    identities = [tuple(row[name] for name in _DECISION_COLUMNS_V1[:6]) for row in rows]
    if len(identities) != len(set(identities)):
        _fail()
    return payload, rows


def _validate_timestamp(value: str) -> None:
    if _TIMESTAMP_UTC.fullmatch(value) is None:
        _fail()
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        _fail()


def _validate_human_provenance(rows: list[dict[str, str]]) -> tuple[str, str, str, str, str]:
    first = rows[0]
    reviewer = _review_text(first["reviewer_id"])
    decision = first["review_decision"]
    timestamp = first["review_timestamp"]
    attestation = _review_text(first["attestation"])
    notes = _review_text(first["review_notes"])
    folded = reviewer.casefold()
    if (
        decision != "APPROVE"
        or folded in _SELF_REVIEWER_IDS
        or "codex" in folded
        or "chatgpt" in folded
    ):
        _fail()
    _validate_timestamp(timestamp)
    expected = (reviewer, decision, timestamp, attestation, notes)
    for row in rows:
        if (
            row["review_decision"] != "APPROVE"
            or (
                row["reviewer_id"],
                row["review_decision"],
                row["review_timestamp"],
                row["attestation"],
                row["review_notes"],
            )
            != expected
        ):
            _fail()
    return expected


def _validate_preingestion_authority(sample: dict[str, object], *, ligand_count: int) -> None:
    role = _dict(sample.get("role_authority"))
    seed = _dict(sample.get("seed_authority"))
    if set(role) != _ROLE_AUTHORITY_FIELDS or set(seed) != _SEED_AUTHORITY_FIELDS:
        _fail()
    role_ids = _list(role["role_ids"], length=ligand_count)
    role_valid = _list(role["role_valid"], length=ligand_count)
    candidates = _list(role["candidate_role_names"], length=ligand_count)
    if (
        role["authority_class"] != "CANDIDATE_ONLY"
        or role["proposal_only"] is not True
        or role["human_approved"] is not False
        or any(type(value) is not int or value != -1 for value in role_ids)
        or any(type(value) is not bool or value for value in role_valid)
        or any(type(value) is not str or value not in ("", "scaffold", "linker", "warhead") for value in candidates)
        or type(role["review_disposition"]) is not str
        or not role["review_disposition"]
        or role["reviewer_id"] != ""
        or role["attestation"] != ""
    ):
        _fail()
    mask = _list(seed["mask"], length=ligand_count)
    candidate_mask = _list(seed["candidate_mask"], length=ligand_count)
    if (
        seed["authority_class"] != "MISSING"
        or seed["proposal_only"] is not True
        or seed["human_approved"] is not False
        or seed["valid"] is not False
        or any(type(value) is not bool or value for value in mask)
        or any(type(value) is not bool or value for value in candidate_mask)
        or type(seed["review_disposition"]) is not str
        or not seed["review_disposition"]
        or seed["reviewer_id"] != ""
        or seed["attestation"] != ""
    ):
        _fail()


def _compile_impl(
    *, machine_authority_payload: object, decision_csv_bytes: object
) -> dict[str, object]:
    payload = _dict(machine_authority_payload)
    if payload.get("schema_version") != _MACHINE_AUTHORITY_PAYLOAD_SCHEMA_V1:
        _fail()
    sample_order = _list(payload.get("sample_order"), length=11)
    if tuple(sample_order) != _CURRENT11_SAMPLE_KEYS_V1:
        _fail()
    samples = _list(payload.get("samples"), length=11)
    raw_bytes, decision_rows = _parse_decision_rows(decision_csv_bytes)

    cursor = 0
    compiled_rows: list[tuple[list[int], list[bool], tuple[str, str, str, str, str]]] = []
    review_records: list[dict[str, object]] = []
    totals = {"scaffold": 0, "linker": 0, "warhead": 0}
    seed_total = 0
    for sample_index, sample_key in enumerate(_CURRENT11_SAMPLE_KEYS_V1):
        sample = _dict(samples[sample_index])
        if sample.get("sample_key") != sample_key:
            _fail()
        pdb_id = _text(sample.get("pdb_id"))
        ligand_comp_id = _text(sample.get("ligand_comp_id"))
        nodes = _list(sample.get("ligand_nodes"))
        if not nodes:
            _fail()
        _validate_preingestion_authority(sample, ligand_count=len(nodes))
        end = cursor + len(nodes)
        if end > len(decision_rows):
            _fail()
        sample_rows = decision_rows[cursor:end]
        roles: list[int] = []
        seed: list[bool] = []
        counts = {"scaffold": 0, "linker": 0, "warhead": 0}
        for local_index, (node_value, row) in enumerate(zip(nodes, sample_rows, strict=True)):
            node = _dict(node_value)
            if (
                type(node.get("retained_local_index")) is not int
                or node["retained_local_index"] != local_index
                or row["sample_key"] != sample_key
                or row["pdb_id"] != pdb_id
                or row["ligand_comp_id"] != ligand_comp_id
                or row["retained_heavy_ligand_local_index_0based"] != str(local_index)
                or row["atom_site_id"] != _text(node.get("atom_site_id"))
                or row["atom_name"] != _text(node.get("atom_name"))
            ):
                _fail()
            role_name = row["role_decision"]
            if role_name not in _ROLE_NAME_TO_ID_V1:
                _fail()
            seed_token = row["minimal_seed_or_anchor_membership"]
            if seed_token not in ("true", "false"):
                _fail()
            roles.append(_ROLE_NAME_TO_ID_V1[role_name])
            seed.append(seed_token == "true")
            counts[role_name] += 1
        if set(roles) != {0, 1, 2} or not any(seed):
            _fail()
        provenance = _validate_human_provenance(sample_rows)
        for name in totals:
            totals[name] += counts[name]
        sample_seed_count = sum(seed)
        seed_total += sample_seed_count
        review_records.append({
            "sample_key": sample_key,
            "pdb_id": pdb_id,
            "ligand_comp_id": ligand_comp_id,
            "row_count": len(nodes),
            "scaffold_count": counts["scaffold"],
            "linker_count": counts["linker"],
            "warhead_count": counts["warhead"],
            "seed_count": sample_seed_count,
            "reviewer_id": provenance[0],
            "review_decision": provenance[1],
            "review_timestamp": provenance[2],
            "attestation": provenance[3],
            "review_notes": provenance[4],
        })
        compiled_rows.append((roles, seed, provenance))
        cursor = end
    if cursor != len(decision_rows):
        _fail()

    compiled = copy.deepcopy(payload)
    compiled_samples = _list(compiled["samples"], length=11)
    for sample, (roles, seed, provenance) in zip(compiled_samples, compiled_rows, strict=True):
        compiled_sample = _dict(sample)
        count = len(roles)
        compiled_sample["role_authority"] = {
            "authority_class": "AUTHORITATIVE_HUMAN_GOLD",
            "role_ids": roles,
            "role_valid": [True] * count,
            "candidate_role_names": [""] * count,
            "proposal_only": False,
            "human_approved": True,
            "review_disposition": "approved_human_gold_ingested_v1",
            "reviewer_id": provenance[0],
            "attestation": provenance[3],
        }
        compiled_sample["seed_authority"] = {
            "authority_class": "AUTHORITATIVE_HUMAN_GOLD",
            "mask": seed,
            "valid": True,
            "candidate_mask": [False] * count,
            "proposal_only": False,
            "human_approved": True,
            "review_disposition": "approved_human_gold_ingested_v1",
            "reviewer_id": provenance[0],
            "attestation": provenance[3],
        }
    return {
        "schema_version": HUMAN_GOLD_INGESTION_SCHEMA_V1,
        "decision_csv_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "decision_row_count": len(decision_rows),
        "human_review_complete_sample_count": len(review_records),
        "role_atom_counts": totals,
        "seed_membership_count": seed_total,
        "sample_review_records": review_records,
        "compiled_authority_payload": compiled,
    }


def compile_covapie_current11_role_seed_human_gold_v1(
    *,
    machine_authority_payload: object,
    decision_csv_bytes: object,
) -> dict[str, object]:
    """Validate explicit decisions and overlay a deep-copied machine payload."""

    try:
        return _compile_impl(
            machine_authority_payload=machine_authority_payload,
            decision_csv_bytes=decision_csv_bytes,
        )
    except Exception as error:
        raise ValueError(INGESTION_COMPILER_ERROR) from error


def load_and_compile_covapie_current11_role_seed_human_gold_v1(
    *,
    state_root: Path,
    machine_authority_payload: object,
) -> dict[str, object]:
    """Load the exact SHA-bound Current11 V1 decision artifact and compile it."""

    try:
        if not isinstance(state_root, Path):
            _fail()
        decision_path = state_root / CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_RELATIVE_PATH_V1
        metadata = decision_path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o644:
            _fail()
        decision_bytes = decision_path.read_bytes()
        if hashlib.sha256(decision_bytes).hexdigest() != CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_SHA256_V1:
            _fail()
        return _compile_impl(
            machine_authority_payload=machine_authority_payload,
            decision_csv_bytes=decision_bytes,
        )
    except Exception as error:
        raise ValueError(INGESTION_COMPILER_ERROR) from error
