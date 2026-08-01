from __future__ import annotations

import gzip
import importlib.util
import inspect
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pytest

from covalent_ext import (
    covapie_current11_target_residue_atom_condition_authority_v1 as subject,
)
from covalent_ext import (
    covapie_current11_target_residue_atom_condition_source_evidence_compiler_v1
    as evidence_compiler,
)
from covalent_ext import (
    covapie_target_residue_atom_condition_contract_design_v1 as contract_design,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_checker():
    path = REPO_ROOT / (
        "scripts/check_covapie_current11_target_residue_atom_condition_"
        "authority_v1.py"
    )
    spec = importlib.util.spec_from_file_location("authority_checker", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECKER = _load_checker()


def _setup(
    tmp_path: Path,
) -> tuple[bytes, dict[str, Any], bytes, dict[str, Any]]:
    return CHECKER._ready_fixture(tmp_path)


def _build(inventory: bytes, evidence: bytes, root: Path) -> dict[str, Any]:
    return subject.build_covapie_current11_target_residue_atom_condition_authority_v1(
        source_formal_inventory=inventory,
        source_evidence_bundle=evidence,
        repo_root=root,
    )


def _assert_canonical_error(call) -> None:
    with pytest.raises(ValueError) as captured:
        call()
    assert str(captured.value) == subject._ERROR


def _contains_path(value: object) -> bool:
    if isinstance(value, Path):
        return True
    if isinstance(value, Mapping):
        return any(_contains_path(item) for item in value.values())
    if isinstance(value, (tuple, list)):
        return any(_contains_path(item) for item in value)
    return False


def _first_raw(tmp_path: Path, response: Mapping[str, Any]) -> Path:
    locator = response["offline_source_recovery_records"][0]["selected_raw_locator"]
    return tmp_path / locator


def _raw_bytes(
    *,
    changes: Mapping[str, str] | None = None,
    omit: str | None = None,
    data_block: str = "T001",
    duplicate: bool = False,
) -> bytes:
    values = CHECKER.OFFLINE_CHECKER._raw_values(0)
    values["pdbx_PDB_ins_code"] = "?"
    values.update(changes or {})
    names = (
        "group_PDB",
        "id",
        "type_symbol",
        "label_atom_id",
        "label_alt_id",
        "label_comp_id",
        "label_asym_id",
        "label_seq_id",
        "Cartn_x",
        "Cartn_y",
        "Cartn_z",
        "occupancy",
        "auth_seq_id",
        "auth_comp_id",
        "auth_asym_id",
        "auth_atom_id",
        "pdbx_PDB_model_num",
        "pdbx_PDB_ins_code",
    )
    names = tuple(name for name in names if name != omit)
    row = {"group_PDB": "ATOM", **values}
    tokens = " ".join(row[name] for name in names)
    lines = [
        f"data_{data_block}",
        "#",
        "loop_",
        *(f"_atom_site.{name}" for name in names),
        tokens,
    ]
    if duplicate:
        lines.append(tokens)
    lines.append("#")
    return gzip.compress(("\n".join(lines) + "\n").encode(), mtime=0)


def _mutate_raw(case: str, tmp_path: Path, response: Mapping[str, Any]) -> None:
    path = _first_raw(tmp_path, response)
    if case == "missing":
        path.unlink()
        return
    if case == "symlink":
        outside = tmp_path / "outside.cif.gz"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
        return
    if case == "sha":
        path.write_bytes(path.read_bytes() + b"drift")
        return
    if case == "malformed":
        path.write_bytes(gzip.compress(b"not_mmcif", mtime=0))
        return
    specifications: dict[str, tuple[dict[str, str], str | None, str, bool]] = {
        "atom_missing": ({"id": "999999"}, None, "T001", False),
        "atom_ambiguous": ({}, None, "T001", True),
        "data_block": ({}, None, "WRONG", False),
        "model": ({"pdbx_PDB_model_num": "2"}, None, "T001", False),
        "auth_chain": ({"auth_asym_id": "B"}, None, "T001", False),
        "auth_residue": ({"auth_comp_id": "MSE"}, None, "T001", False),
        "auth_sequence": ({"auth_seq_id": "999"}, None, "T001", False),
        "auth_atom": ({"auth_atom_id": "SD"}, None, "T001", False),
        "insertion": ({"pdbx_PDB_ins_code": "A"}, None, "T001", False),
        "type": ({"type_symbol": "C"}, None, "T001", False),
        "label_component": ({"label_comp_id": "MSE"}, None, "T001", False),
        "label_atom": ({"label_atom_id": "SD"}, None, "T001", False),
        "label_asym_missing": ({"label_asym_id": "?"}, None, "T001", False),
        "label_seq_missing": ({"label_seq_id": "?"}, None, "T001", False),
        "altloc_column_missing": ({}, "label_alt_id", "T001", False),
    }
    changes, omit, data_block, duplicate = specifications[case]
    path.write_bytes(
        _raw_bytes(
            changes=changes,
            omit=omit,
            data_block=data_block,
            duplicate=duplicate,
        )
    )


def test_public_signature_all_and_silent_import() -> None:
    assert subject.__all__ == (
        "build_covapie_current11_target_residue_atom_condition_authority_v1",
    )
    signature = inspect.signature(
        subject.build_covapie_current11_target_residue_atom_condition_authority_v1
    )
    assert tuple(signature.parameters) == (
        "source_formal_inventory",
        "source_evidence_bundle",
        "repo_root",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert signature.return_annotation == "dict[str, Any]"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "from covalent_ext import covapie_current11_target_residue_atom_condition_authority_v1",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(REPO_ROOT / "src"),
        },
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_exact20_exact20_record_fields_order_uniqueness_and_lineage(
    tmp_path: Path,
) -> None:
    inventory, evidence, evidence_bytes, response = _setup(tmp_path)
    bundle = _build(inventory, evidence_bytes, tmp_path)
    assert tuple(bundle) == subject.TARGET_RESIDUE_ATOM_CONDITION_AUTHORITY_BUNDLE_FIELDS
    assert len(bundle) == 20
    assert tuple(contract_design._FUTURE_CONDITION_RECORD_FIELDS) == (
        subject.TARGET_RESIDUE_ATOM_CONDITION_RECORD_FIELDS
    )
    records = bundle["target_residue_atom_condition_records"]
    assert len(records) == bundle["target_residue_atom_condition_record_count"] == 11
    assert all(tuple(record) == subject.TARGET_RESIDUE_ATOM_CONDITION_RECORD_FIELDS for record in records)
    assert [record["sample_index_row_id"] for record in records] == list(
        bundle["sample_order"]
    )
    assert len({record["source_condition_evidence_sha256"] for record in records}) == 11
    assert bundle["source_offline_recovery_design_response_sha256"] == response[
        "design_response_sha256"
    ]
    assert bundle["source_evidence_bundle_sha256"] == evidence[
        "source_evidence_bundle_sha256"
    ]
    inventory_value = json.loads(inventory)
    assert bundle["source_condition_contract_design_production_sha256"] == inventory_value[
        "source_contract_design_production_sha256"
    ]
    assert bundle["source_condition_contract_design_response_sha256"] == inventory_value[
        "source_contract_design_response_sha256"
    ]


def test_exact_raw_type_altloc_label_crosswalk_and_selector_observed(
    tmp_path: Path,
) -> None:
    inventory, evidence, evidence_bytes, response = _setup(tmp_path)
    records = _build(inventory, evidence_bytes, tmp_path)[
        "target_residue_atom_condition_records"
    ]
    assert records[0]["protein_label_alt_id"] == "B"
    assert all(record["protein_type_symbol"] == "S" for record in records)
    assert all(record["protein_label_comp_id"] == "CYS" for record in records)
    assert all(record["protein_label_atom_id"] == "SG" for record in records)
    assert all(record["protein_label_asym_id"] for record in records)
    assert all(record["protein_label_seq_id"] for record in records)
    assert [record["source_atom_site_id"] for record in records] == [
        str(1000 + index) for index in range(11)
    ]
    recovery = response["offline_source_recovery_records"][0]
    locator = recovery["selected_raw_locator"]
    path = _first_raw(tmp_path, response)
    _, _, rows = CHECKER.offline_recovery._parse_atom_site(
        CHECKER.offline_recovery._decode_raw(path.read_bytes(), locator)
    )
    row = dict(next(row for row in rows if row["_atom_site.id"] == "1000"))
    for raw_altloc, expected in ((".", ""), ("?", ""), ("A", "A"), ("B", "B")):
        row["_atom_site.label_alt_id"] = raw_altloc
        assert subject._authority_record(
            evidence["condition_evidence_records"][0], row
        )["protein_label_alt_id"] == expected


def test_deterministic_zero_write_inputs_unchanged_and_no_path(
    tmp_path: Path,
) -> None:
    inventory, _, evidence_bytes, _ = _setup(tmp_path)
    before = CHECKER._tree_snapshot(tmp_path)
    inventory_snapshot = bytes(inventory)
    evidence_snapshot = bytes(evidence_bytes)
    first = _build(inventory, evidence_bytes, tmp_path)
    second = _build(inventory, evidence_bytes, tmp_path)
    assert first == second
    assert CHECKER._tree_snapshot(tmp_path) == before
    assert inventory == inventory_snapshot and evidence_bytes == evidence_snapshot
    assert not _contains_path(first)


def test_record_bundle_digests_and_strict_canonical_transport(tmp_path: Path) -> None:
    inventory, _, evidence_bytes, _ = _setup(tmp_path)
    bundle = _build(inventory, evidence_bytes, tmp_path)
    for record in bundle["target_residue_atom_condition_records"]:
        assert record["target_residue_atom_condition_record_sha256"] == subject._record_sha256(
            record,
            subject.TARGET_RESIDUE_ATOM_CONDITION_RECORD_FIELDS,
            "target_residue_atom_condition_record_sha256",
        )
    assert bundle["target_residue_atom_condition_authority_bundle_sha256"] == subject._record_sha256(
        bundle,
        subject.TARGET_RESIDUE_ATOM_CONDITION_AUTHORITY_BUNDLE_FIELDS,
        "target_residue_atom_condition_authority_bundle_sha256",
    )
    payload = subject._bundle_bytes(bundle)
    assert not payload.startswith(b"\xef\xbb\xbf")
    assert b"\x00" not in payload and not payload.endswith((b"\n", b"\r"))
    assert json.dumps(
        json.loads(payload),
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode() == payload


def test_authority_is_not_adapter_label_tensor_or_training_feature(
    tmp_path: Path,
) -> None:
    inventory, _, evidence_bytes, _ = _setup(tmp_path)
    bundle = _build(inventory, evidence_bytes, tmp_path)
    serialized = subject._bundle_bytes(bundle).lower()
    assert bundle["feature_semantics_audit_required_before_training"] is True
    assert bundle["ready_for_target_residue_atom_condition_adapter_design"] is True
    for forbidden in (b"ligand_comp_id", b"warhead", b"mask", b"tensor", b"training_label"):
        assert forbidden not in serialized


@pytest.mark.parametrize(
    "mutation",
    (
        lambda payload: payload + b"\n",
        lambda payload: b"\xef\xbb\xbf" + payload,
        lambda payload: payload + b"\x00",
        lambda payload: payload[:-1],
        lambda payload: payload[:-1] + b"0",
        lambda payload: b"{}",
        lambda payload: b"[]",
    ),
)
def test_evidence_transport_internal_and_exact_recompile_drift_rejected(
    tmp_path: Path, mutation,
) -> None:
    inventory, _, evidence_bytes, _ = _setup(tmp_path)
    _assert_canonical_error(lambda: _build(inventory, mutation(evidence_bytes), tmp_path))


@pytest.mark.parametrize(
    "name,replacement",
    (
        ("_SOURCE_EVIDENCE_COMPILER_PRODUCTION_SHA256", "0" * 64),
        ("_CONTRACT_DESIGN_MODULE_SHA256", "0" * 64),
        ("_CONTRACT_DESIGN_PRODUCTION_SHA256", "0" * 64),
        ("_CONTRACT_DESIGN_RESPONSE_SHA256", "0" * 64),
        ("_OFFLINE_RECOVERY_PRODUCTION_SHA256", "0" * 64),
        ("_OFFLINE_RECOVERY_RESPONSE_SHA256", "0" * 64),
        ("_EXPECTED_RECOVERY_RECORD_SHA256S", ("0" * 64,) * 11),
        ("_EXPECTED_EVIDENCE_RECORD_SHA256S", ("0" * 64,) * 11),
    ),
)
def test_frozen_lineage_drift_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    replacement: object,
) -> None:
    inventory, _, evidence_bytes, _ = _setup(tmp_path)
    monkeypatch.setattr(subject, name, replacement)
    _assert_canonical_error(lambda: _build(inventory, evidence_bytes, tmp_path))


@pytest.mark.parametrize(
    "case",
    (
        "missing",
        "symlink",
        "sha",
        "malformed",
        "atom_missing",
        "atom_ambiguous",
        "data_block",
        "model",
        "auth_chain",
        "auth_residue",
        "auth_sequence",
        "auth_atom",
        "insertion",
        "type",
        "label_component",
        "label_atom",
        "label_asym_missing",
        "label_seq_missing",
        "altloc_column_missing",
    ),
)
def test_raw_exact_row_fail_closed_and_no_partial_authority(
    tmp_path: Path, case: str,
) -> None:
    inventory, _, evidence_bytes, response = _setup(tmp_path)
    _mutate_raw(case, tmp_path, response)
    _assert_canonical_error(lambda: _build(inventory, evidence_bytes, tmp_path))
    assert not tuple(tmp_path.rglob("*authority*"))


@pytest.mark.parametrize(
    "field,value",
    (
        ("_atom_site.pdbx_PDB_model_num", "2"),
        ("_atom_site.auth_asym_id", "B"),
        ("_atom_site.auth_comp_id", "MSE"),
        ("_atom_site.auth_seq_id", "999"),
        ("_atom_site.pdbx_PDB_ins_code", "A"),
        ("_atom_site.auth_atom_id", "SD"),
        ("_atom_site.type_symbol", "C"),
        ("_atom_site.label_asym_id", "?"),
        ("_atom_site.label_comp_id", "MSE"),
        ("_atom_site.label_seq_id", "?"),
        ("_atom_site.label_atom_id", "SD"),
    ),
)
def test_exact_row_semantic_drift_rejected_by_record_gate(
    tmp_path: Path, field: str, value: str,
) -> None:
    inventory, evidence, _, response = _setup(tmp_path)
    recovery = response["offline_source_recovery_records"][0]
    locator = recovery["selected_raw_locator"]
    path = _first_raw(tmp_path, response)
    data_block, headers, rows = CHECKER.offline_recovery._parse_atom_site(
        CHECKER.offline_recovery._decode_raw(path.read_bytes(), locator)
    )
    assert data_block == "T001" and headers
    row = dict(next(row for row in rows if row["_atom_site.id"] == "1000"))
    row[field] = value
    _assert_canonical_error(
        lambda: subject._authority_record(evidence["condition_evidence_records"][0], row)
    )


@pytest.mark.parametrize("raw_altloc", ("", " "))
def test_empty_or_whitespace_altloc_source_token_rejected_directly(
    tmp_path: Path, raw_altloc: str,
) -> None:
    _, evidence, _, response = _setup(tmp_path)
    recovery = response["offline_source_recovery_records"][0]
    locator = recovery["selected_raw_locator"]
    path = _first_raw(tmp_path, response)
    _, _, rows = CHECKER.offline_recovery._parse_atom_site(
        CHECKER.offline_recovery._decode_raw(path.read_bytes(), locator)
    )
    row = dict(next(row for row in rows if row["_atom_site.id"] == "1000"))
    row["_atom_site.label_alt_id"] = raw_altloc
    _assert_canonical_error(
        lambda: subject._authority_record(evidence["condition_evidence_records"][0], row)
    )


def test_output_symlink_and_conflict_rejected_without_overwrite(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    inventory, _, evidence_bytes, _ = _setup(fixture)
    bundle = _build(inventory, evidence_bytes, fixture)
    expected = subject._bundle_bytes(bundle)
    target = tmp_path / "authority.json"
    backing = tmp_path / "backing.json"
    backing.write_bytes(expected)
    target.symlink_to(backing)
    _assert_canonical_error(
        lambda: subject._materialize_target_residue_atom_condition_authority_bundle_v1(
            bundle=bundle, output_path=target
        )
    )
    assert backing.read_bytes() == expected
    target.unlink()
    target.write_bytes(b"conflict")
    before = target.read_bytes()
    _assert_canonical_error(
        lambda: subject._materialize_target_residue_atom_condition_authority_bundle_v1(
            bundle=bundle, output_path=target
        )
    )
    assert target.read_bytes() == before


def test_publication_new_then_exact_existing_is_idempotent(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    inventory, _, evidence_bytes, _ = _setup(fixture)
    bundle = _build(inventory, evidence_bytes, fixture)
    target = tmp_path / "authority.json"
    first = subject._materialize_target_residue_atom_condition_authority_bundle_v1(
        bundle=bundle, output_path=target
    )
    before = target.lstat()
    payload = target.read_bytes()
    second = subject._materialize_target_residue_atom_condition_authority_bundle_v1(
        bundle=bundle, output_path=target
    )
    after = target.lstat()
    assert first["publication_mode"] == "published_new"
    assert second["publication_mode"] == "idempotent_existing"
    assert (before.st_ino, before.st_mtime_ns) == (after.st_ino, after.st_mtime_ns)
    assert target.read_bytes() == payload == subject._bundle_bytes(bundle)
    assert stat.S_IMODE(after.st_mode) == 0o644 and after.st_nlink == 1
    assert not target.is_symlink()


def test_publication_failure_preserves_unknown_file_and_cleans_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    inventory, _, evidence_bytes, _ = _setup(fixture)
    bundle = _build(inventory, evidence_bytes, fixture)
    unknown = tmp_path / "unknown.keep"
    unknown.write_bytes(b"keep")

    def fail_link(*args, **kwargs):
        raise PermissionError("synthetic")

    monkeypatch.setattr(subject.os, "link", fail_link)
    _assert_canonical_error(
        lambda: subject._materialize_target_residue_atom_condition_authority_bundle_v1(
            bundle=bundle, output_path=tmp_path / "authority.json"
        )
    )
    assert unknown.read_bytes() == b"keep"
    assert not tuple(tmp_path.glob(".authority.json.*.tmp"))


@pytest.mark.parametrize(
    "arguments",
    (
        {"source_formal_inventory": bytearray(), "source_evidence_bundle": b"x", "repo_root": Path(".")},
        {"source_formal_inventory": b"x", "source_evidence_bundle": bytearray(), "repo_root": Path(".")},
        {"source_formal_inventory": b"x", "source_evidence_bundle": b"x", "repo_root": "."},
    ),
)
def test_invalid_public_argument_types_use_canonical_value_error(arguments) -> None:
    _assert_canonical_error(
        lambda: subject.build_covapie_current11_target_residue_atom_condition_authority_v1(
            **arguments
        )
    )


def test_checker_executes_and_reports_required_flags() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(REPO_ROOT / "scripts/check_covapie_current11_target_residue_atom_condition_authority_v1.py")],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(REPO_ROOT / "src"),
        },
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    output = dict(line.split("=", 1) for line in completed.stdout.splitlines())
    for key in (
        "source_evidence_bundle_recompiled_exact",
        "missing_raw_rejected",
        "raw_sha_drift_rejected",
        "atom_site_missing_rejected",
        "atom_site_ambiguous_rejected",
        "auth_identity_drift_rejected",
        "type_symbol_drift_rejected",
        "label_crosswalk_drift_rejected",
        "source_evidence_drift_rejected",
        "contract_production_drift_rejected",
        "partial_authority_rejected",
        "deterministic",
        "inputs_unchanged",
        "all_records_resolved_authoritative",
        "ready_for_target_residue_atom_condition_adapter_design",
    ):
        assert output[key] == "true"
    assert output["files_written"] == "false"
    assert output["target_residue_atom_condition_record_count"] == "11"
    assert len(json.loads(output["target_residue_atom_condition_record_sha256s"])) == 11
