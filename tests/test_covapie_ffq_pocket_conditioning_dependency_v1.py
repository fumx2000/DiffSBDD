from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, fields, replace
from functools import lru_cache
import gzip
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import shlex
import subprocess
from typing import Any, Mapping, Sequence

import pytest
import torch

from covalent_ext import (
    covapie_ffq_project_level_authority_ingestion_and_effective_supervision_successor_v1
    as ffq_successor,
)
from covalent_ext import covapie_ffq_real_structure_microbatch_alignment_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "c5cdc659c444f5a868c60b0d28d1fecbbaefd0ed"
STATE_ROOT_ENV = "COVAPIE_STATE_ROOT"
UNIT_REL = Path(
    "manual-review-aids/cumulative1000-high-yield-calibration-v1/"
    "FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D"
)
FIXED_ATOM_IDS = ("O2", "O3", "O4", "P1")
GENERATED_ATOM_IDS = ("C1", "C2", "C3", "O1")
EXACT8_ATOM_IDS = frozenset(FIXED_ATOM_IDS + GENERATED_ATOM_IDS)
PERTURBATIONS_ANGSTROM = (
    ("x_plus_1A", (1.0, 0.0, 0.0)),
    ("x_minus_1A", (-1.0, 0.0, 0.0)),
    ("y_plus_1A", (0.0, 1.0, 0.0)),
    ("y_minus_1A", (0.0, -1.0, 0.0)),
    ("z_plus_1A", (0.0, 0.0, 1.0)),
    ("z_minus_1A", (0.0, 0.0, -1.0)),
)
EXPECTED_POCKET_COUNTS = (218, 210, 199, 198)
EXPECTED_FIXED_POCKET_COUNTS = (164, 165, 176, 164)
EXPECTED_HASHES = {
    "delta": "fa93e448469b77f798bbcea483f2948cf49a77775f0fa02ba2130ca30939f70d",
    "alignment": "2497ce0600f41fb01ab8f0fcdbcd1aa9bccb21b659f077496d988307953928ef",
    "formal": "ba0670519064399b2ecb0c73631009c8c6c4d3c14512377ecfaad0d87388e149",
    "post_formal": "8f3297435525ab68501046f811aa32ae7dbd8ab30c6bcafcafc988aada89468d",
    "structure": "80f00b3dfd6a743ef4cb768cb2959261920a071d362cafa7ce083fc78194bc00",
}
BASELINE_PRODUCTION_SOURCE_SHA256 = (
    "e1f52c5037396bb51288cbdca9aa9e8e5f803f587d0e6eff20d04a6f9d63ea38"
)
BASELINE_SELECTOR_SOURCE_SHA256 = (
    "9f833301cb9c08fc49f2429596deca5ee97a734eef020cb4042f3a92e054f3ef"
)
CHECKER_PATH = ROOT / (
    "scripts/check_covapie_ffq_project_level_authority_ingestion_and_"
    "effective_supervision_successor_v1.py"
)
ATOM_SITE_COLUMNS = (
    "_atom_site.group_PDB",
    "_atom_site.id",
    "_atom_site.type_symbol",
    "_atom_site.label_atom_id",
    "_atom_site.label_alt_id",
    "_atom_site.label_comp_id",
    "_atom_site.label_asym_id",
    "_atom_site.label_seq_id",
    "_atom_site.Cartn_x",
    "_atom_site.Cartn_y",
    "_atom_site.Cartn_z",
    "_atom_site.occupancy",
    "_atom_site.auth_seq_id",
    "_atom_site.auth_comp_id",
    "_atom_site.auth_asym_id",
    "_atom_site.auth_atom_id",
    "_atom_site.pdbx_PDB_ins_code",
    "_atom_site.pdbx_PDB_model_num",
)
TARGET_ATOMS = (
    ("N", "N"),
    ("CA", "C"),
    ("C", "C"),
    ("O", "O"),
    ("CB", "C"),
    ("SG", "S"),
)
EVENT_A = "COVAPIE_CYS_SG_EVENT_V1:3VCY:A:CYS:116-:SG:E:FFQ:C1"
EVENT_4R7U_A = "COVAPIE_CYS_SG_EVENT_V1:4R7U:A:CYS:116-:SG:F:FFQ:C1"

checker_spec = importlib.util.spec_from_file_location(
    "ffq_pocket_dependency_effective_checker", CHECKER_PATH
)
assert checker_spec is not None and checker_spec.loader is not None
checker = importlib.util.module_from_spec(checker_spec)
checker_spec.loader.exec_module(checker)


class DependencyProbeInputError(RuntimeError):
    """Raised when a frozen input cannot be proven before it is consumed."""


@dataclass(frozen=True)
class SelectionSnapshot:
    atom_count: int
    residue_count: int
    source_identities: tuple[str, ...]
    target_residue_count: int
    target_residue_atom_count: int
    target_sg_count: int
    exact10_legal: bool
    source_order_deterministic: bool


def _state_root() -> Path:
    configured = os.environ.get(STATE_ROOT_ENV)
    return Path(configured) if configured else ROOT.parent / "covapie-state"


def _required_bytes(path: Path, expected_sha256: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise DependencyProbeInputError(
            f"BLOCKED: required regular non-symlink input is missing: {path}"
        )
    payload = path.read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected_sha256:
        raise DependencyProbeInputError(
            f"BLOCKED: frozen input SHA256 mismatch for {path}: {actual}"
        )
    return payload


def _json_from_frozen(path: Path, expected_sha256: str) -> dict[str, Any]:
    payload = _required_bytes(path, expected_sha256)
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DependencyProbeInputError(
            f"BLOCKED: frozen JSON cannot be decoded: {path}"
        ) from error
    if type(value) is not dict:
        raise DependencyProbeInputError(f"BLOCKED: frozen JSON is not an object: {path}")
    return value


def _load_frozen_inputs(state_root: Path | None = None) -> dict[str, Any]:
    state = _state_root() if state_root is None else state_root
    delta_path = (
        state
        / "local-tools/ffq-exact4-scoped-post-use-semantics-delta-v1/"
        "ffq_exact4_scoped_post_use_semantics_delta_v1.json"
    )
    alignment_path = (
        state
        / "local-tools/ffq-exact4-warhead-only-input-alignment-v1/"
        "ffq_exact4_input_alignment_report_v1.json"
    )
    formal_path = (
        state / UNIT_REL / "formal-human-decision-v1/ffq_formal_human_decision_v1.json"
    )
    post_formal_path = (
        state
        / UNIT_REL
        / "post-distance-label-use-formal-human-decision-v1/"
        "ffq_post_label_use_formal_human_decision_v1.json"
    )
    delta = _json_from_frozen(delta_path, EXPECTED_HASHES["delta"])
    alignment = _json_from_frozen(alignment_path, EXPECTED_HASHES["alignment"])
    formal = _json_from_frozen(formal_path, EXPECTED_HASHES["formal"])
    post_formal = _json_from_frozen(post_formal_path, EXPECTED_HASHES["post_formal"])

    structure_binding = alignment.get("source_fingerprints", {}).get(
        "real_structure_source"
    )
    if type(structure_binding) is not dict:
        raise DependencyProbeInputError(
            "BLOCKED: alignment report has no real structure source binding"
        )
    if (
        structure_binding.get("path_namespace") != "project_root_relative"
        or structure_binding.get("sha256") != EXPECTED_HASHES["structure"]
        or structure_binding.get("decompressed_copy_written") is not False
        or structure_binding.get("decompressed_in_memory") is not True
    ):
        raise DependencyProbeInputError(
            "BLOCKED: alignment report real structure binding is not the frozen contract"
        )
    relative_structure = structure_binding.get("path")
    if type(relative_structure) is not str or not relative_structure.startswith(
        "covapie-state/"
    ):
        raise DependencyProbeInputError(
            "BLOCKED: real structure source path namespace is invalid"
        )
    structure_path = state.parent / relative_structure
    structure_payload = _required_bytes(structure_path, EXPECTED_HASHES["structure"])
    if len(structure_payload) != 353235:
        raise DependencyProbeInputError(
            "BLOCKED: frozen real structure compressed byte count changed"
        )

    return {
        "delta": delta,
        "alignment": alignment,
        "formal": formal,
        "post_formal": post_formal,
        "structure_payload": structure_payload,
    }


def _git(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _field(row: Mapping[str, Any], name: str) -> str:
    return subject._atom_value(row, name)


def _source_identity(source_index: int, row: Mapping[str, Any]) -> str:
    insertion = _field(row, "pdbx_PDB_ins_code") or "NONE"
    altloc = _field(row, "label_alt_id") or "blank"
    return ":".join(
        (
            str(source_index),
            _field(row, "id"),
            _field(row, "pdbx_PDB_model_num") or "1",
            _field(row, "auth_asym_id") or _field(row, "label_asym_id"),
            _field(row, "auth_seq_id") or _field(row, "label_seq_id"),
            insertion,
            subject._preferred_component(row),
            subject._preferred_atom_name(row),
            altloc,
        )
    )


def _residue_identity(row: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    key = subject._checkpoint_residue_key_v1(row)
    assert key is not None
    return key


def _target_counts(
    pocket: Sequence[tuple[int, Mapping[str, Any]]], identity: Mapping[str, str]
) -> tuple[int, int, int]:
    matching_rows = [
        row
        for _, row in pocket
        if subject._preferred_component(row) == identity["residue"]
        and (_field(row, "auth_asym_id") or _field(row, "label_asym_id"))
        == identity["protein_chain"]
        and (_field(row, "auth_seq_id") or _field(row, "label_seq_id"))
        == identity["sequence"]
        and (_field(row, "pdbx_PDB_ins_code") or "NONE")
        == identity["insertion"]
    ]
    residue_keys = {_residue_identity(row) for row in matching_rows}
    sg_count = sum(
        subject._preferred_atom_name(row) == identity["protein_atom"]
        for row in matching_rows
    )
    return len(residue_keys), len(matching_rows), sg_count


def _snapshot(
    indexed_atom_rows: Sequence[tuple[int, Mapping[str, Any]]],
    ligand_heavy_rows: Sequence[tuple[int, Mapping[str, Any]]],
    identity: Mapping[str, str],
) -> SelectionSnapshot:
    first = subject._build_checkpoint_model_input_pocket_v1(
        indexed_atom_rows, ligand_heavy_rows
    )
    second = subject._build_checkpoint_model_input_pocket_v1(
        indexed_atom_rows, ligand_heavy_rows
    )
    first_identities = tuple(_source_identity(*item) for item in first)
    second_identities = tuple(_source_identity(*item) for item in second)
    assert first_identities == second_identities
    assert [index for index, _ in first] == sorted(index for index, _ in first)

    retained, channels, _ = subject._projection(first, domain="pocket")
    assert tuple(_source_identity(*item) for item in retained) == first_identities
    assert len(channels) == len(retained)
    assert all(channel in range(10) for channel in channels)
    target_residue_count, target_atom_count, target_sg_count = _target_counts(
        retained, identity
    )
    return SelectionSnapshot(
        atom_count=len(retained),
        residue_count=len({_residue_identity(row) for _, row in retained}),
        source_identities=first_identities,
        target_residue_count=target_residue_count,
        target_residue_atom_count=target_atom_count,
        target_sg_count=target_sg_count,
        exact10_legal=True,
        source_order_deterministic=True,
    )


def _set_delta(
    before: Sequence[str], after: Sequence[str]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    before_set = set(before)
    after_set = set(after)
    added = tuple(identity for identity in after if identity not in before_set)
    removed = tuple(identity for identity in before if identity not in after_set)
    return added, removed


def _synthetic_row(
    *,
    site_id: int,
    group: str,
    atom_id: str,
    symbol: str,
    component: str,
    chain: str,
    sequence: str,
    xyz: tuple[float | str, float | str, float | str],
    altloc: str = ".",
    auth_chain: str | None = None,
) -> dict[str, str]:
    return {
        "_atom_site.group_PDB": group,
        "_atom_site.id": str(site_id),
        "_atom_site.type_symbol": symbol,
        "_atom_site.label_atom_id": atom_id,
        "_atom_site.label_alt_id": altloc,
        "_atom_site.label_comp_id": component,
        "_atom_site.label_asym_id": chain,
        "_atom_site.label_seq_id": sequence,
        "_atom_site.Cartn_x": str(xyz[0]),
        "_atom_site.Cartn_y": str(xyz[1]),
        "_atom_site.Cartn_z": str(xyz[2]),
        "_atom_site.occupancy": "1.00",
        "_atom_site.auth_seq_id": sequence,
        "_atom_site.auth_comp_id": component,
        "_atom_site.auth_asym_id": auth_chain or chain,
        "_atom_site.auth_atom_id": atom_id,
        "_atom_site.pdbx_PDB_ins_code": ".",
        "_atom_site.pdbx_PDB_model_num": "1",
    }


def _synthetic_case() -> tuple[
    list[tuple[int, dict[str, str]]],
    list[tuple[int, dict[str, str]]],
    list[tuple[int, dict[str, str]]],
]:
    rows = [
        _synthetic_row(
            site_id=1,
            group="ATOM",
            atom_id="CA",
            symbol="C",
            component="ALA",
            chain="A",
            sequence="1",
            xyz=(-1.0, 0.0, 0.0),
        ),
        _synthetic_row(
            site_id=2,
            group="ATOM",
            atom_id="CB",
            symbol="C",
            component="ALA",
            chain="A",
            sequence="2",
            xyz=(8.5, 0.0, 0.0),
        ),
    ]
    for atom_id in FIXED_ATOM_IDS:
        rows.append(
            _synthetic_row(
                site_id=len(rows) + 1,
                group="HETATM",
                atom_id=atom_id,
                symbol="P" if atom_id == "P1" else "O",
                component="FFQ",
                chain="E",
                sequence="500",
                xyz=(0.0, 0.0, 0.0),
            )
        )
    for atom_id in GENERATED_ATOM_IDS:
        rows.append(
            _synthetic_row(
                site_id=len(rows) + 1,
                group="HETATM",
                atom_id=atom_id,
                symbol="O" if atom_id == "O1" else "C",
                component="FFQ",
                chain="E",
                sequence="500",
                xyz=(0.0, 0.0, 0.0),
            )
        )
    indexed = list(enumerate(rows))
    fixed = [item for item in indexed if subject._preferred_atom_name(item[1]) in FIXED_ATOM_IDS]
    generated = [
        item
        for item in indexed
        if subject._preferred_atom_name(item[1]) in GENERATED_ATOM_IDS
    ]
    return indexed, fixed, generated


@lru_cache(maxsize=1)
def _real_effective_records() -> tuple[dict[str, Any], ...]:
    inputs = checker._read_inputs(ROOT)
    checker._validate_receipts_and_canonical_authorities(inputs)
    build_inputs = {
        key: value
        for key, value in inputs.items()
        if key not in ("family_receipt", "rule_receipt")
    }
    result = ffq_successor.build_covapie_ffq_project_level_authority_effective_supervision_v1(
        **build_inputs
    )
    ffq_successor.validate_covapie_ffq_project_level_authority_effective_supervision_v1(
        result
    )
    records = result.get("effective_supervision_records")
    assert type(records) is list and len(records) == 8
    assert all(type(record) is dict for record in records)
    return tuple(records)


def _record_by_event_id(event_id: str) -> dict[str, Any]:
    matches = [
        record
        for record in _real_effective_records()
        if record.get("canonical_event_id") == event_id
    ]
    assert len(matches) == 1
    return matches[0]


def _synthetic_payload(
    event_id: str,
    *,
    ligand_order: tuple[str, ...] = (
        "H1",
        "O3",
        "C2",
        "P1",
        "O1",
        "C1",
        "O4",
        "C3",
        "O2",
    ),
    omit_sg: bool = False,
    generated_delta: tuple[float, float, float] = (0.0, 0.0, 0.0),
    generated_nan: bool = False,
    alternate_near_generated_only: bool = False,
) -> bytes:
    identity = _event_identity(event_id)
    rows: list[dict[str, str]] = []
    for index, (atom_id, symbol) in enumerate(TARGET_ATOMS):
        if atom_id == "SG" and omit_sg:
            continue
        rows.append(
            _synthetic_row(
                site_id=len(rows) + 1,
                group="ATOM",
                atom_id=atom_id,
                symbol=symbol,
                component="CYS",
                chain=identity["protein_chain"],
                sequence=identity["sequence"],
                xyz=(1.0 + 0.1 * index, 0.0, 0.0),
            )
        )
    rows.append(
        _synthetic_row(
            site_id=len(rows) + 1,
            group="ATOM",
            atom_id="CB",
            symbol="C",
            component="ALA",
            chain=identity["protein_chain"],
            sequence="120",
            xyz=(8.5, 0.0, 0.0),
        )
    )
    if alternate_near_generated_only:
        for altloc in ("A", "B"):
            rows.append(
                _synthetic_row(
                    site_id=len(rows) + 1,
                    group="ATOM",
                    atom_id="ALT",
                    symbol="C",
                    component="ALA",
                    chain=identity["protein_chain"],
                    sequence="121",
                    xyz=(10.0, 0.0, 0.0),
                    altloc=altloc,
                )
            )
    for atom_id in ligand_order:
        generated = atom_id in GENERATED_ATOM_IDS
        xyz: tuple[float | str, float | str, float | str]
        if generated_nan and generated:
            xyz = ("nan", generated_delta[1], generated_delta[2])
        elif alternate_near_generated_only and generated:
            xyz = (10.0, 0.0, 0.0)
        else:
            xyz = generated_delta if generated else (0.0, 0.0, 0.0)
        rows.append(
            _synthetic_row(
                site_id=len(rows) + 1,
                group="HETATM",
                atom_id=atom_id,
                symbol=(
                    "H"
                    if atom_id.startswith("H")
                    else "P"
                    if atom_id == "P1"
                    else "O"
                    if atom_id.startswith("O")
                    else "C"
                ),
                component="FFQ",
                chain=identity["ligand_asym"],
                auth_chain=identity["protein_chain"],
                sequence="500",
                xyz=xyz,
            )
        )
    rows.append(
        _synthetic_row(
            site_id=len(rows) + 1,
            group="ATOM",
            atom_id="CA",
            symbol="C",
            component="GLY",
            chain=identity["protein_chain"],
            sequence="999",
            xyz=(30.0, 0.0, 0.0),
        )
    )
    lines = [
        f"data_{identity['pdb']}",
        f"_entry.id {identity['pdb']}",
        "#",
        "loop_",
        *ATOM_SITE_COLUMNS,
    ]
    lines.extend(" ".join(row[column] for column in ATOM_SITE_COLUMNS) for row in rows)
    lines.append("#")
    return gzip.compress(("\n".join(lines) + "\n").encode(), mtime=0)


def _sample(event_id: str, payload: bytes, task_id: object = 0) -> dict[str, object]:
    return {
        "cif_gz_payload": payload,
        "effective_supervision_record": _record_by_event_id(event_id),
        "canonical_task_id": task_id,
    }


def _seed_inputs(
    event_id: str, payload: bytes
) -> tuple[
    dict[str, Any],
    tuple[dict[str, object], ...],
    list[tuple[int, Mapping[str, Any]]],
    tuple[int | None, ...],
    object,
]:
    record = _record_by_event_id(event_id)
    identity = subject._event_identity(record)
    ligand_rows = subject.ligand_owner.extract_covapie_ligand_atom_identity_rows_from_cif_gz_v1(
        cif_gz_payload=payload,
        ligand_component_id=identity["ligand"],
        label_asym_id=identity["ligand_asym"],
        model_num=1,
    )
    role = subject.role_owner.tensorize_covapie_ffq_direct_profile_role_masks_v1(
        effective_supervision_record=record,
        ligand_atom_rows=ligand_rows,
        canonical_task_id=0,
        device="cpu",
    )
    atom_rows = subject._parse_and_crosscheck_atom_site(payload, expected_pdb_id=identity["pdb"])
    preprojection = subject._crosscheck_ligand_rows(ligand_rows, atom_rows)
    retained, _channels, source_to_projected = subject._projection(
        preprojection, domain="ligand"
    )
    return record, ligand_rows, retained, source_to_projected, role


def _assert_public_results_identical(left: object, right: object) -> None:
    assert type(left) is type(right)
    for field in fields(left):
        left_value = getattr(left, field.name)
        right_value = getattr(right, field.name)
        if type(left_value) is dict:
            assert left_value.keys() == right_value.keys(), field.name
            assert all(
                torch.equal(left_value[key], right_value[key])
                for key in left_value
            ), field.name
        elif isinstance(left_value, torch.Tensor):
            assert torch.equal(left_value, right_value), field.name
        else:
            assert left_value == right_value, field.name


def _translate_atom_site_rows_in_memory(
    payload: bytes,
    source_indices: set[int],
    delta: tuple[float, float, float],
) -> bytes:
    lines = gzip.decompress(payload).decode("utf-8").splitlines()
    loop_start = next(
        index
        for index, line in enumerate(lines)
        if line.strip() == "loop_"
        and index + 1 < len(lines)
        and lines[index + 1].strip().startswith("_atom_site.")
    )
    cursor = loop_start + 1
    headers: list[str] = []
    while cursor < len(lines) and lines[cursor].strip().startswith("_atom_site."):
        headers.append(lines[cursor].strip())
        cursor += 1
    coordinate_positions = [headers.index("_atom_site." + axis) for axis in ("Cartn_x", "Cartn_y", "Cartn_z")]
    observed: set[int] = set()
    source_index = 0
    while cursor < len(lines) and lines[cursor].strip() != "#":
        stripped = lines[cursor].strip()
        if not stripped:
            cursor += 1
            continue
        tokens = shlex.split(stripped, posix=True)
        assert len(tokens) == len(headers)
        if source_index in source_indices:
            for position, increment in zip(coordinate_positions, delta):
                tokens[position] = repr(float(tokens[position]) + increment)
            lines[cursor] = " ".join(tokens)
            observed.add(source_index)
        source_index += 1
        cursor += 1
    assert observed == source_indices
    return gzip.compress(("\n".join(lines) + "\n").encode("utf-8"), mtime=0)


def _move_rows(
    indexed_atom_rows: Sequence[tuple[int, Mapping[str, Any]]],
    source_indices: set[int],
    delta: tuple[float, float, float],
) -> list[tuple[int, dict[str, Any]]]:
    moved = copy.deepcopy(indexed_atom_rows)
    for source_index, row in moved:
        if source_index not in source_indices:
            continue
        for axis, increment in zip(("Cartn_x", "Cartn_y", "Cartn_z"), delta):
            field = "_atom_site." + axis
            row[field] = repr(float(row[field]) + increment)
    return moved


def _event_identity(event_id: str) -> dict[str, str]:
    match = subject._EVENT_ID.fullmatch(event_id)
    assert match is not None
    identity = match.groupdict()
    locator = subject._RESIDUE_LOCATOR.fullmatch(identity["residue_locator"])
    assert locator is not None
    identity["sequence"] = locator.group("sequence")
    identity["insertion"] = (
        "NONE" if locator.group("insertion") == "-" else locator.group("insertion")
    )
    return identity


def _event_ligand_rows(
    atom_rows: Sequence[Mapping[str, Any]],
    event: Mapping[str, Any],
    formal_fixed: set[str],
    formal_generated: set[str],
) -> tuple[list[tuple[int, Mapping[str, Any]]], list[tuple[int, Mapping[str, Any]]]]:
    event_id = event["canonical_event_id"]
    identity = _event_identity(event_id)
    report_identity = event["identity"]
    assert identity["pdb"] == report_identity["pdb_id"] == "3VCY"
    assert identity["protein_chain"] == report_identity["protein_auth_asym_id"]
    assert identity["ligand_asym"] == report_identity["ligand_label_asym_id"]
    assert identity["ligand"] == report_identity["ligand_component_id"] == "FFQ"

    projection = event["ligand_exact8_role_projection"]
    assert {item["atom_id"] for item in projection} == EXACT8_ATOM_IDS
    selected: list[tuple[int, Mapping[str, Any]]] = []
    for item in projection:
        source_index = item["source_atom_site_row_index_0based"]
        row = atom_rows[source_index]
        atom_id = item["atom_id"]
        assert _field(row, "id") == item["source_atom_site_id"]
        assert _field(row, "label_atom_id") == atom_id
        assert _field(row, "label_comp_id") == "FFQ"
        assert _field(row, "label_asym_id") == identity["ligand_asym"]
        assert _field(row, "auth_asym_id") == report_identity["ligand_auth_asym_id"]
        assert (_field(row, "pdbx_PDB_model_num") or "1") == "1"
        expected_role = "scaffold" if atom_id in formal_fixed else "warhead"
        assert item["role_semantic_name"] == expected_role
        assert item["fixed"] is (atom_id in formal_fixed)
        assert item["generated"] is (atom_id in formal_generated)
        selected.append((source_index, row))
    assert [index for index, _ in selected] == sorted(index for index, _ in selected)
    retained, channels, _ = subject._projection(selected, domain="ligand")
    assert retained == selected
    assert len(channels) == 8 and all(channel in range(10) for channel in channels)
    fixed = [item for item in selected if subject._preferred_atom_name(item[1]) in formal_fixed]
    assert {subject._preferred_atom_name(row) for _, row in fixed} == formal_fixed
    return selected, fixed


@lru_cache(maxsize=1)
def analyze_real_exact4() -> list[dict[str, Any]]:
    """Return deterministic test-only observations for documentation."""

    frozen = _load_frozen_inputs()
    alignment = frozen["alignment"]
    formal = frozen["formal"]
    post_formal = frozen["post_formal"]
    assert alignment["selected_task"] == {
        "display_alias": "A",
        "semantic_name": "warhead_only",
        "task_id": 0,
    }
    assert [task["semantic_name"] for task in alignment["canonical_V1_task_contract"]] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]

    formal_events = [
        item
        for item in formal["event_level_human_decisions"]
        if item["pdb_id"] == "3VCY"
    ]
    formal_event_ids = [item["canonical_event_id"] for item in formal_events]
    post_event_ids = [
        item["canonical_event_id"] for item in post_formal["formal_event_decisions"]
    ]
    report_events = alignment["events"]
    report_event_ids = [item["canonical_event_id"] for item in report_events]
    assert formal_event_ids == post_event_ids == report_event_ids
    assert len(formal_event_ids) == 4

    role = formal["role_human_decision"]
    assert tuple(role["scaffold_atom_ids"]) == FIXED_ATOM_IDS
    assert tuple(role["warhead_atom_ids"]) == GENERATED_ATOM_IDS
    assert role["linker_atom_ids"] == []
    formal_fixed = set(role["scaffold_atom_ids"])
    formal_generated = set(role["warhead_atom_ids"])

    atom_rows = subject._parse_and_crosscheck_atom_site(
        frozen["structure_payload"], expected_pdb_id="3VCY"
    )
    indexed_atom_rows = list(enumerate(atom_rows))
    results: list[dict[str, Any]] = []
    event_ligand_source_sets: list[set[int]] = []
    for ordinal, (event, expected_count) in enumerate(
        zip(report_events, EXPECTED_POCKET_COUNTS)
    ):
        assert event["event_ordinal"] == ordinal
        identity = _event_identity(event["canonical_event_id"])
        full_ligand, fixed_ligand = _event_ligand_rows(
            atom_rows, event, formal_fixed, formal_generated
        )
        event_ligand_source_sets.append({index for index, _ in full_ligand})

        full = _snapshot(indexed_atom_rows, full_ligand, identity)
        fixed = _snapshot(indexed_atom_rows, fixed_ligand, identity)
        assert full.atom_count == expected_count
        assert event["node_counts"]["checkpoint_pocket_heavy_nodes"] == expected_count
        assert full.target_residue_count == full.target_sg_count == 1
        assert fixed.target_residue_count == fixed.target_sg_count == 1
        fixed_added, fixed_removed = _set_delta(
            full.source_identities, fixed.source_identities
        )

        generated_source_indices = {
            index
            for index, row in full_ligand
            if subject._preferred_atom_name(row) in formal_generated
        }
        perturbations: list[dict[str, Any]] = []
        for name, delta in PERTURBATIONS_ANGSTROM:
            moved_rows = _move_rows(indexed_atom_rows, generated_source_indices, delta)
            moved_by_index = dict(moved_rows)
            moved_full = [(index, moved_by_index[index]) for index, _ in full_ligand]
            moved_fixed = [(index, moved_by_index[index]) for index, _ in fixed_ligand]
            perturbed_full = _snapshot(moved_rows, moved_full, identity)
            perturbed_fixed = _snapshot(moved_rows, moved_fixed, identity)
            assert perturbed_fixed.source_identities == fixed.source_identities
            assert perturbed_fixed.target_residue_count == 1
            assert perturbed_fixed.target_sg_count == 1
            full_added, full_removed = _set_delta(
                full.source_identities, perturbed_full.source_identities
            )
            perturbations.append(
                {
                    "name": name,
                    "full_atom_count": perturbed_full.atom_count,
                    "full_residue_count": perturbed_full.residue_count,
                    "full_membership_changed": bool(full_added or full_removed),
                    "full_added": full_added,
                    "full_removed": full_removed,
                    "fixed_membership_unchanged": True,
                    "full_target_sg_count": perturbed_full.target_sg_count,
                    "fixed_target_sg_count": perturbed_fixed.target_sg_count,
                }
            )

        results.append(
            {
                "event_id": event["canonical_event_id"],
                "full": asdict(full),
                "fixed": asdict(fixed),
                "fixed_added_vs_full": fixed_added,
                "fixed_removed_vs_full": fixed_removed,
                "perturbations": perturbations,
            }
        )

    assert all(
        left.isdisjoint(right)
        for index, left in enumerate(event_ligand_source_sets)
        for right in event_ligand_source_sets[index + 1 :]
    )
    return results


def test_frozen_input_loader_fails_closed_instead_of_skipping(tmp_path: Path) -> None:
    with pytest.raises(DependencyProbeInputError, match=r"^BLOCKED: required"):
        _load_frozen_inputs(tmp_path)


def test_synthetic_boundary_controls_use_the_real_selector() -> None:
    indexed, fixed, generated = _synthetic_case()
    full = fixed + generated

    full_baseline = subject._build_checkpoint_model_input_pocket_v1(indexed, full)
    fixed_baseline = subject._build_checkpoint_model_input_pocket_v1(indexed, fixed)
    assert tuple(_source_identity(*item) for item in full_baseline) == (
        _source_identity(*indexed[0]),
    )
    assert tuple(_source_identity(*item) for item in fixed_baseline) == (
        _source_identity(*indexed[0]),
    )

    generated_indices = {index for index, _ in generated}
    generated_moved = _move_rows(indexed, generated_indices, (1.0, 0.0, 0.0))
    generated_moved_by_index = dict(generated_moved)
    full_after_generated_move = subject._build_checkpoint_model_input_pocket_v1(
        generated_moved,
        [(index, generated_moved_by_index[index]) for index, _ in full],
    )
    fixed_after_generated_move = subject._build_checkpoint_model_input_pocket_v1(
        generated_moved,
        [(index, generated_moved_by_index[index]) for index, _ in fixed],
    )
    assert tuple(_source_identity(*item) for item in full_after_generated_move) == tuple(
        _source_identity(*item) for item in indexed[:2]
    )
    assert tuple(_source_identity(*item) for item in fixed_after_generated_move) == tuple(
        _source_identity(*item) for item in fixed_baseline
    )

    fixed_indices = {index for index, _ in fixed}
    fixed_moved = _move_rows(indexed, fixed_indices, (1.0, 0.0, 0.0))
    fixed_moved_by_index = dict(fixed_moved)
    fixed_after_fixed_move = subject._build_checkpoint_model_input_pocket_v1(
        fixed_moved,
        [(index, fixed_moved_by_index[index]) for index, _ in fixed],
    )
    assert tuple(_source_identity(*item) for item in fixed_after_fixed_move) == tuple(
        _source_identity(*item) for item in indexed[:2]
    )

    generated_nan = copy.deepcopy(indexed)
    generated_nan_by_index = dict(generated_nan)
    for index in generated_indices:
        generated_nan_by_index[index]["_atom_site.Cartn_x"] = "nan"
    fixed_with_generated_nan = subject._build_checkpoint_model_input_pocket_v1(
        generated_nan,
        [(index, generated_nan_by_index[index]) for index, _ in fixed],
    )
    assert tuple(_source_identity(*item) for item in fixed_with_generated_nan) == tuple(
        _source_identity(*item) for item in fixed_baseline
    )
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":LIGAND_COORDINATES_INVALID$",
    ):
        subject._build_checkpoint_model_input_pocket_v1(
            generated_nan,
            [(index, generated_nan_by_index[index]) for index, _ in full],
        )

    fixed_nan = copy.deepcopy(indexed)
    fixed_nan_by_index = dict(fixed_nan)
    fixed_nan_by_index[fixed[0][0]]["_atom_site.Cartn_x"] = "nan"
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":LIGAND_COORDINATES_INVALID$",
    ):
        subject._build_checkpoint_model_input_pocket_v1(
            fixed_nan,
            [(index, fixed_nan_by_index[index]) for index, _ in fixed],
        )


def test_authorized_source_lifecycle_preserves_the_old_selector() -> None:
    source_path = (
        ROOT / "src/covalent_ext/covapie_ffq_real_structure_microbatch_alignment_v1.py"
    )
    baseline_source = subprocess.run(
        (
            "git",
            "show",
            f"{BASELINE}:src/covalent_ext/"
            "covapie_ffq_real_structure_microbatch_alignment_v1.py",
        ),
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    assert hashlib.sha256(baseline_source).hexdigest() == (
        BASELINE_PRODUCTION_SOURCE_SHA256
    )
    assert hashlib.sha256(
        inspect.getsource(subject._build_checkpoint_model_input_pocket_v1).encode()
    ).hexdigest() == BASELINE_SELECTOR_SOURCE_SHA256
    assert _git(
        "rev-parse",
        f"{BASELINE}:src/covalent_ext/"
        "covapie_ffq_real_structure_microbatch_alignment_v1.py",
    ) == "fb4cd8c81ad499869e5a6728b63fc58621c2a654"
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() != (
        BASELINE_PRODUCTION_SOURCE_SHA256
    )
    signature = inspect.signature(
        subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1
    )
    policy = signature.parameters["pocket_seed_policy"]
    assert policy.kind is inspect.Parameter.KEYWORD_ONLY
    assert policy.default == "full_ligand_v1"


@pytest.mark.parametrize(
    "policy",
    [
        pytest.param(None, id="none"),
        pytest.param(True, id="bool-true"),
        pytest.param(False, id="bool-false"),
        pytest.param(1, id="integer"),
        pytest.param(
            type("PolicyString", (str,), {})("full_ligand_v1"), id="str-subclass"
        ),
    ],
)
def test_nonexact_pocket_seed_policy_types_fail_closed(policy: object) -> None:
    payload = _synthetic_payload(EVENT_A)
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":POCKET_SEED_POLICY_EXACT_STRING_REQUIRED$",
    ):
        subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
            samples=[_sample(EVENT_A, payload)], pocket_seed_policy=policy
        )


@pytest.mark.parametrize(
    "policy",
    ["", "unknown", " full_ligand_v1", "full_ligand_v1 ", "FULL_LIGAND_V1"],
)
def test_unknown_or_normalized_policy_spellings_fail_closed(policy: str) -> None:
    payload = _synthetic_payload(EVENT_A)
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":POCKET_SEED_POLICY_INVALID$",
    ):
        subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
            samples=[_sample(EVENT_A, payload)], pocket_seed_policy=policy
        )


@pytest.mark.parametrize("task_id", [1, 2, 3, 4, True, None])
def test_fixed_scaffold_policy_rejects_every_non_warhead_only_task(
    task_id: object,
) -> None:
    payload = _synthetic_payload(EVENT_A)
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":SAMPLE_0_FIXED_SCAFFOLD_POCKET_SEED_REQUIRES_TASK_ID_0$",
    ):
        subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
            samples=[_sample(EVENT_A, payload, task_id)],
            pocket_seed_policy="fixed_scaffold_warhead_only_v1",
        )


def test_public_fixed_branch_uses_identity_after_permutation_and_h_removal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _synthetic_payload(EVENT_A)
    sample = _sample(EVENT_A, payload)
    implicit = subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=[sample]
    )
    explicit = subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=[sample], pocket_seed_policy="full_ligand_v1"
    )
    _assert_public_results_identical(implicit, explicit)

    observed_seeds: list[tuple[str, ...]] = []
    real_selector = subject._build_checkpoint_model_input_pocket_v1

    def observe_seed(
        indexed_atom_rows: Sequence[tuple[int, Mapping[str, Any]]],
        ligand_heavy_rows: Sequence[tuple[int, Mapping[str, Any]]],
    ) -> list[tuple[int, Mapping[str, Any]]]:
        observed_seeds.append(
            tuple(subject._preferred_atom_name(row) for _, row in ligand_heavy_rows)
        )
        return real_selector(indexed_atom_rows, ligand_heavy_rows)

    monkeypatch.setattr(subject, "_build_checkpoint_model_input_pocket_v1", observe_seed)
    fixed = subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=[sample], pocket_seed_policy="fixed_scaffold_warhead_only_v1"
    )
    assert observed_seeds == [("O3", "P1", "O4", "O2")]
    assert fixed.model_input_batch["num_lig_atoms"].tolist() == [8]
    assert fixed.model_input_batch["num_pocket_nodes"].tolist() == [6]
    assert fixed.target_residue_membership_mask.sum().item() == 6
    assert fixed.target_residue_reactive_atom_mask.sum().item() == 1


def test_fixed_seed_mapping_contract_fails_closed_on_corruption() -> None:
    payload = _synthetic_payload(EVENT_A)
    record, ligand_rows, retained, source_to_projected, role = _seed_inputs(
        EVENT_A, payload
    )
    kwargs = {
        "effective_supervision_record": record,
        "ligand_rows": ligand_rows,
        "ligand_retained": retained,
        "ligand_source_to_projected": source_to_projected,
        "role": role,
        "sample_ordinal": 0,
    }

    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":SAMPLE_0_FIXED_SCAFFOLD_ROLE_BINDING_INVALID$",
    ):
        subject._fixed_scaffold_warhead_only_pocket_seed_v1(
            **{**kwargs, "role": replace(role, canonical_task_id=3)}
        )

    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":SAMPLE_0_FIXED_SCAFFOLD_SEED_EMPTY$",
    ):
        subject._fixed_scaffold_warhead_only_pocket_seed_v1(
            **{**kwargs, "role": replace(role, scaffold_parser_local_indices=())}
        )

    scaffold = role.scaffold_parser_local_indices
    for bad_indices in (
        (scaffold[0], scaffold[0], scaffold[2], scaffold[3]),
        (scaffold[0], scaffold[1], scaffold[2], len(retained)),
    ):
        with pytest.raises(
            subject.FFQRealStructureMicrobatchAlignmentError,
            match=r":SAMPLE_0_FIXED_SCAFFOLD_SEED_INDICES_INVALID$",
        ):
            subject._fixed_scaffold_warhead_only_pocket_seed_v1(
                **{
                    **kwargs,
                    "role": replace(role, scaffold_parser_local_indices=bad_indices),
                }
            )

    invalid_dtype = replace(
        role, ligand_role_valid=role.ligand_role_valid.to(dtype=torch.int64)
    )
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":SAMPLE_0_FIXED_SCAFFOLD_ROLE_TENSOR_SCHEMA_INVALID$",
    ):
        subject._fixed_scaffold_warhead_only_pocket_seed_v1(
            **{**kwargs, "role": invalid_dtype}
        )

    fixed_mask = role.ligand_base_fixed_mask.clone()
    fixed_mask[scaffold[0]] = False
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":SAMPLE_0_FIXED_SCAFFOLD_ROLE_MASK_INVALID$",
    ):
        subject._fixed_scaffold_warhead_only_pocket_seed_v1(
            **{**kwargs, "role": replace(role, ligand_base_fixed_mask=fixed_mask)}
        )

    generation_mask = role.ligand_base_generation_mask.clone()
    generation_mask[scaffold[0]] = True
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":SAMPLE_0_FIXED_GENERATED_MASK_CONFLICT$",
    ):
        subject._fixed_scaffold_warhead_only_pocket_seed_v1(
            **{
                **kwargs,
                "role": replace(role, ligand_base_generation_mask=generation_mask),
            }
        )

    swapped = list(retained)
    swapped[0], swapped[1] = swapped[1], swapped[0]
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":SAMPLE_0_PROJECTED_LIGAND_ORDER_INVALID$",
    ):
        subject._fixed_scaffold_warhead_only_pocket_seed_v1(
            **{**kwargs, "ligand_retained": swapped}
        )

    corrupted_rows = copy.deepcopy(ligand_rows)
    parser_index = next(
        index
        for index, projected in enumerate(source_to_projected)
        if projected == scaffold[0]
    )
    corrupted_rows[parser_index]["atom_id"] = "C1"
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":SAMPLE_0_PROJECTED_LIGAND_IDENTITY_INVALID$",
    ):
        subject._fixed_scaffold_warhead_only_pocket_seed_v1(
            **{**kwargs, "ligand_rows": tuple(corrupted_rows)}
        )


def test_public_fixed_branch_uses_seed_for_altloc_and_keeps_full_coordinate_checks() -> None:
    altloc_payload = _synthetic_payload(EVENT_A, alternate_near_generated_only=True)
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":CHECKPOINT_POCKET_ALTLOC_SEMANTICS_AMBIGUOUS_V1$",
    ):
        subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
            samples=[_sample(EVENT_A, altloc_payload)],
            pocket_seed_policy="full_ligand_v1",
        )
    fixed = subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=[_sample(EVENT_A, altloc_payload)],
        pocket_seed_policy="fixed_scaffold_warhead_only_v1",
    )
    assert fixed.model_input_batch["num_pocket_nodes"].tolist() == [6]

    generated_nan_payload = _synthetic_payload(EVENT_A, generated_nan=True)
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":LIGAND_COORDINATES_INVALID$",
    ):
        subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
            samples=[_sample(EVENT_A, generated_nan_payload)],
            pocket_seed_policy="fixed_scaffold_warhead_only_v1",
        )


def test_public_fixed_branch_keeps_target_sg_and_4r7u_exclusion_fail_closed() -> None:
    missing_sg = _synthetic_payload(EVENT_A, omit_sg=True)
    with pytest.raises(
        subject.FFQRealStructureMicrobatchAlignmentError,
        match=r":TARGET_RESIDUE_REACTIVE_ATOM_NOT_EXACTLY_ONE$",
    ):
        subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
            samples=[_sample(EVENT_A, missing_sg)],
            pocket_seed_policy="fixed_scaffold_warhead_only_v1",
        )

    excluded_payload = _synthetic_payload(EVENT_4R7U_A)
    excluded = subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=[_sample(EVENT_4R7U_A, excluded_payload)],
        pocket_seed_policy="fixed_scaffold_warhead_only_v1",
    )
    assert excluded.human_training_exclusion_preserved.tolist() == [True]
    assert excluded.sample_training_admitted.tolist() == [False]
    assert excluded.geometry_target_available.tolist() == [False]


def _real_exact4_samples(frozen: Mapping[str, Any]) -> list[dict[str, object]]:
    event_ids = [event["canonical_event_id"] for event in frozen["alignment"]["events"]]
    records = [_record_by_event_id(event_id) for event_id in event_ids]
    assert [record["effective_supervision_record_sha256"] for record in records] == frozen[
        "alignment"
    ]["effective_supervision_replay"]["selected_record_sha256"]
    return [
        {
            "cif_gz_payload": frozen["structure_payload"],
            "effective_supervision_record": record,
            "canonical_task_id": 0,
        }
        for record in records
    ]


def test_real_exact4_public_default_full_and_fixed_microbatches() -> None:
    frozen = _load_frozen_inputs()
    samples = _real_exact4_samples(frozen)
    implicit_full = subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=samples
    )
    explicit_full = subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=samples, pocket_seed_policy="full_ligand_v1"
    )
    _assert_public_results_identical(implicit_full, explicit_full)
    assert implicit_full.model_input_batch["num_pocket_nodes"].tolist() == list(
        EXPECTED_POCKET_COUNTS
    )

    fixed = subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=samples, pocket_seed_policy="fixed_scaffold_warhead_only_v1"
    )
    direct_probe = analyze_real_exact4()
    assert fixed.model_input_batch["num_lig_atoms"].tolist() == [8, 8, 8, 8]
    assert fixed.model_input_batch["num_pocket_nodes"].tolist() == list(
        EXPECTED_FIXED_POCKET_COUNTS
    )
    assert fixed.ligand_node_offsets == (0, 8, 16, 24, 32)
    assert fixed.pocket_node_offsets == (0, 164, 329, 505, 669)
    assert fixed.ligand_reactive_local_indices.tolist() == [0, 0, 0, 0]
    assert fixed.ligand_reactive_flat_indices.tolist() == [0, 8, 16, 24]
    assert fixed.target_reactive_local_indices.tolist() == [64, 84, 84, 83]
    assert fixed.target_reactive_flat_indices.tolist() == [64, 248, 413, 588]
    assert fixed.model_input_batch["pocket_one_hot"].shape == (669, 10)
    assert torch.equal(
        fixed.model_input_batch["pocket_one_hot"].sum(dim=1), torch.ones(669)
    )
    assert fixed.positive_pair_batch_indices.tolist() == [0, 1, 2, 3]
    assert fixed.positive_pair_ligand_local_indices.tolist() == [0, 0, 0, 0]
    assert fixed.positive_pair_ligand_flat_indices.tolist() == [0, 8, 16, 24]
    assert fixed.positive_pair_pocket_local_indices.tolist() == (
        fixed.target_reactive_local_indices.tolist()
    )
    assert fixed.positive_pair_pocket_flat_indices.tolist() == (
        fixed.target_reactive_flat_indices.tolist()
    )
    assert fixed.target_residue_membership_mask.sum().item() == 24
    assert fixed.target_residue_reactive_atom_mask.sum().item() == 4
    assert fixed.sample_training_admitted.tolist() == [False] * 4
    assert fixed.geometry_target_available.tolist() == [False] * 4
    assert fixed.warhead_type_target_available.tolist() == [False] * 4

    pocket_sources = fixed.model_input_batch["pocket_source_row_index"]
    sulfur_channels = fixed.model_input_batch["pocket_one_hot"].argmax(dim=1)
    for ordinal, item in enumerate(direct_probe):
        start, end = fixed.pocket_node_offsets[ordinal : ordinal + 2]
        expected_sources = [
            int(identity.split(":", 1)[0])
            for identity in item["fixed"]["source_identities"]
        ]
        assert pocket_sources[start:end].tolist() == expected_sources
        assert fixed.model_input_batch["pocket_mask"][start:end].tolist() == [
            ordinal
        ] * (end - start)
        local_sg = fixed.target_reactive_local_indices[ordinal].item()
        flat_sg = fixed.target_reactive_flat_indices[ordinal].item()
        assert flat_sg == start + local_sg
        assert sulfur_channels[flat_sg].item() == 3
        assert pocket_sources[flat_sg].item() == frozen["alignment"]["events"][ordinal][
            "endpoints"
        ]["SG"]["source_atom_site_row_index_0based"]


def test_real_public_fixed_branch_membership_ignores_one_finite_generated_move() -> None:
    frozen = _load_frozen_inputs()
    sample = _real_exact4_samples(frozen)[0]
    event = frozen["alignment"]["events"][0]
    generated_indices = {
        item["source_atom_site_row_index_0based"]
        for item in event["ligand_exact8_role_projection"]
        if item["role_semantic_name"] == "warhead"
    }
    moved_payload = _translate_atom_site_rows_in_memory(
        frozen["structure_payload"], generated_indices, (1.0, 0.0, 0.0)
    )
    moved_sample = {**sample, "cif_gz_payload": moved_payload}

    baseline_fixed = subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=[sample], pocket_seed_policy="fixed_scaffold_warhead_only_v1"
    )
    moved_fixed = subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=[moved_sample], pocket_seed_policy="fixed_scaffold_warhead_only_v1"
    )
    assert torch.equal(
        baseline_fixed.model_input_batch["pocket_source_row_index"],
        moved_fixed.model_input_batch["pocket_source_row_index"],
    )
    assert not torch.equal(
        baseline_fixed.model_input_batch["lig_coords"],
        moved_fixed.model_input_batch["lig_coords"],
    )

    baseline_full = subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=[sample], pocket_seed_policy="full_ligand_v1"
    )
    moved_full = subject.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
        samples=[moved_sample], pocket_seed_policy="full_ligand_v1"
    )
    assert baseline_full.model_input_batch["num_pocket_nodes"].tolist() == [218]
    assert moved_full.model_input_batch["num_pocket_nodes"].tolist() == [226]
    assert not torch.equal(
        baseline_full.model_input_batch["pocket_source_row_index"],
        moved_full.model_input_batch["pocket_source_row_index"],
    )


def test_real_exact4_low_level_probe_remains_the_24_intervention_evidence() -> None:
    results = analyze_real_exact4()
    assert len(results) == 4
    assert [item["full"]["atom_count"] for item in results] == list(
        EXPECTED_POCKET_COUNTS
    )
    assert all(item["fixed"]["target_sg_count"] == 1 for item in results)
    assert all(
        perturbation["fixed_membership_unchanged"]
        for item in results
        for perturbation in item["perturbations"]
    )
