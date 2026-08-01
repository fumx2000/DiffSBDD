from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from covalent_ext import (
    covapie_current11_target_residue_atom_condition_offline_source_recovery_design_v1
    as offline_recovery,
)
from covalent_ext import (
    covapie_current11_target_residue_atom_condition_source_evidence_compiler_v1
    as subject,
)
from covalent_ext import (
    covapie_target_residue_atom_condition_contract_design_v1 as contract_design,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_checker():
    path = REPO_ROOT / (
        "scripts/check_covapie_current11_target_residue_atom_condition_"
        "source_evidence_compiler_v1.py"
    )
    spec = importlib.util.spec_from_file_location(
        "source_evidence_compiler_checker", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECKER = _load_checker()


def _setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> tuple[bytes, dict[str, Any]]:
    inventory, files = CHECKER._ready_fixture(tmp_path)
    value = json.loads(inventory)
    monkeypatch.setattr(
        offline_recovery,
        "_FORMAL_INVENTORY_TRANSPORT_SHA256",
        hashlib.sha256(inventory).hexdigest(),
    )
    monkeypatch.setattr(
        offline_recovery,
        "_FORMAL_INVENTORY_INTERNAL_SHA256",
        value["source_inventory_bundle_sha256"],
    )
    monkeypatch.setattr(
        offline_recovery,
        "_SAMPLE_INDEX_SHA256",
        hashlib.sha256(files["sample"]).hexdigest(),
    )
    monkeypatch.setattr(
        offline_recovery,
        "_LOCATOR_SIDECAR_SHA256",
        hashlib.sha256(files["locator"]).hexdigest(),
    )
    response = offline_recovery._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1(
        source_formal_inventory=inventory, repo_root=tmp_path
    )
    monkeypatch.setattr(
        subject,
        "_FORMAL_INVENTORY_TRANSPORT_SHA256",
        hashlib.sha256(inventory).hexdigest(),
    )
    monkeypatch.setattr(
        subject,
        "_FORMAL_INVENTORY_INTERNAL_SHA256",
        value["source_inventory_bundle_sha256"],
    )
    monkeypatch.setattr(
        subject,
        "_EXPECTED_DESIGN_RESPONSE_SHA256",
        response["design_response_sha256"],
    )
    monkeypatch.setattr(
        subject,
        "_EXPECTED_RECOVERY_RECORD_SHA256S",
        tuple(
            record["offline_source_recovery_record_sha256"]
            for record in response["offline_source_recovery_records"]
        ),
    )
    monkeypatch.setattr(
        subject,
        "_EXPECTED_EVIDENCE_RECORD_SHA256S",
        tuple(
            record["proposed_condition_evidence_record"]
            ["condition_evidence_record_sha256"]
            for record in response["offline_source_recovery_records"]
        ),
    )
    return inventory, response


def _compile(inventory: bytes, root: Path) -> dict[str, Any]:
    return subject.compile_covapie_current11_target_residue_atom_condition_source_evidence_v1(
        source_formal_inventory=inventory, repo_root=root
    )


def _fake_response(
    monkeypatch: pytest.MonkeyPatch, response: dict[str, Any]
) -> None:
    monkeypatch.setattr(
        offline_recovery,
        "_reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1",
        lambda **_: response,
    )


def _resign_response(response: dict[str, Any]) -> None:
    response["design_response_sha256"] = subject._record_sha256(
        response, subject._RESPONSE_FIELDS, "design_response_sha256"
    )


def _resign_recovery(record: dict[str, Any]) -> None:
    record["offline_source_recovery_record_sha256"] = subject._record_sha256(
        record,
        subject._RECOVERY_RECORD_FIELDS,
        "offline_source_recovery_record_sha256",
    )


def test_public_signature_all_and_silent_import() -> None:
    assert subject.__all__ == (
        "compile_covapie_current11_target_residue_atom_condition_source_evidence_v1",
    )
    signature = inspect.signature(
        subject.compile_covapie_current11_target_residue_atom_condition_source_evidence_v1
    )
    assert tuple(signature.parameters) == ("source_formal_inventory", "repo_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert signature.parameters["source_formal_inventory"].annotation == "bytes"
    assert signature.parameters["repo_root"].annotation == "Path"
    assert signature.return_annotation == "dict[str, Any]"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "from covalent_ext import covapie_current11_target_residue_atom_condition_source_evidence_compiler_v1",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": "src",
        },
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_exact15_records_lineage_flags_and_not_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, response = _setup(tmp_path, monkeypatch)
    bundle = _compile(inventory, tmp_path)
    assert tuple(bundle) == subject.SOURCE_EVIDENCE_BUNDLE_FIELDS
    assert len(bundle) == 15
    assert bundle["condition_evidence_record_count"] == 11
    assert bundle["all_source_recovery_records_ready"] is True
    assert bundle[
        "ready_for_target_residue_atom_condition_authority_materialization"
    ] is True
    assert bundle["feature_semantics_audit_required_before_training"] is True
    assert bundle["source_offline_recovery_design_response_sha256"] == response[
        "design_response_sha256"
    ]
    assert tuple(bundle["condition_evidence_record_fields"]) == (
        contract_design._CONDITION_EVIDENCE_RECORD_FIELDS
    )
    assert tuple(bundle["condition_evidence_records"]) == tuple(
        record["proposed_condition_evidence_record"]
        for record in response["offline_source_recovery_records"]
    )
    assert not any(
        "authority" in field
        for record in bundle["condition_evidence_records"]
        for field in record
    )


def test_record_and_bundle_digests_sample_order_and_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    bundle = _compile(inventory, tmp_path)
    assert tuple(bundle["sample_order"]) == subject._EXPECTED_SAMPLES
    identities = set()
    for index, record in enumerate(bundle["condition_evidence_records"]):
        assert tuple(record) == subject._CONDITION_EVIDENCE_RECORD_FIELDS
        assert record["sample_index_row_id"] == subject._EXPECTED_SAMPLES[index]
        assert record["condition_evidence_record_sha256"] == subject._record_sha256(
            record,
            subject._CONDITION_EVIDENCE_RECORD_FIELDS,
            "condition_evidence_record_sha256",
        )
        assert record["protein_auth_comp_id"] == "CYS"
        assert record["protein_auth_atom_id"] == "SG"
        identities.add((record["pdb_id"], record["ligand_comp_id"]))
    assert len(identities) == 11
    assert bundle["source_evidence_bundle_sha256"] == subject._record_sha256(
        bundle,
        subject.SOURCE_EVIDENCE_BUNDLE_FIELDS,
        "source_evidence_bundle_sha256",
    )


def test_deterministic_compile_zero_writes_and_input_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    before = CHECKER._tree_snapshot(tmp_path)
    snapshot = bytes(inventory)
    first = _compile(inventory, tmp_path)
    second = _compile(inventory, tmp_path)
    assert first == second
    assert subject._bundle_bytes(first) == subject._bundle_bytes(second)
    assert inventory == snapshot
    assert CHECKER._tree_snapshot(tmp_path) == before
    assert not any(
        path.name.endswith((".tmp", ".part")) for path in tmp_path.rglob("*")
    )


def test_explicit_question_token_normalised_empty_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    first = _compile(inventory, tmp_path)["condition_evidence_records"][0]
    assert first["protein_pdbx_PDB_ins_code"] == ""


def test_canonical_transport_is_strict_round_trip_without_newline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    bundle = _compile(inventory, tmp_path)
    payload = subject._bundle_bytes(bundle)
    assert payload == json.dumps(
        bundle,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    assert not payload.startswith(b"\xef\xbb\xbf")
    assert b"\x00" not in payload
    assert not payload.endswith((b"\n", b"\r"))
    assert subject._canonical_json_bytes(subject._strict_json_object(payload)) == payload


def test_non_ready_predecessor_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, response = _setup(tmp_path, monkeypatch)
    drifted = copy.deepcopy(response)
    drifted["recoverable_offline_unique_count"] = 10
    drifted["blocked_sample_count"] = 1
    drifted["ready_for_offline_source_evidence_compiler"] = False
    _fake_response(monkeypatch, drifted)
    with pytest.raises(ValueError, match=subject._ERROR):
        _compile(inventory, tmp_path)


def test_blocked_record_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, response = _setup(tmp_path, monkeypatch)
    drifted = copy.deepcopy(response)
    record = drifted["offline_source_recovery_records"][0]
    record["recovery_status"] = "blocked_identity_mismatch"
    record["blocking_reasons"] = ("synthetic_block",)
    record["ready_for_offline_source_evidence_compiler"] = False
    _resign_recovery(record)
    _resign_response(drifted)
    monkeypatch.setattr(
        subject, "_EXPECTED_DESIGN_RESPONSE_SHA256", drifted["design_response_sha256"]
    )
    _fake_response(monkeypatch, drifted)
    with pytest.raises(ValueError, match=subject._ERROR):
        _compile(inventory, tmp_path)


def test_empty_evidence_rejected_after_valid_recovery_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, response = _setup(tmp_path, monkeypatch)
    drifted = copy.deepcopy(response)
    record = drifted["offline_source_recovery_records"][0]
    record["proposed_condition_evidence_record"] = {}
    _resign_recovery(record)
    _resign_response(drifted)
    recovery_sha = list(subject._EXPECTED_RECOVERY_RECORD_SHA256S)
    recovery_sha[0] = record["offline_source_recovery_record_sha256"]
    monkeypatch.setattr(subject, "_EXPECTED_RECOVERY_RECORD_SHA256S", tuple(recovery_sha))
    monkeypatch.setattr(
        subject, "_EXPECTED_DESIGN_RESPONSE_SHA256", drifted["design_response_sha256"]
    )
    _fake_response(monkeypatch, drifted)
    with pytest.raises(ValueError, match=subject._ERROR):
        _compile(inventory, tmp_path)


@pytest.mark.parametrize("mutation", ("duplicate", "reordered"))
def test_duplicate_or_reordered_samples_rejected(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, response = _setup(tmp_path, monkeypatch)
    drifted = copy.deepcopy(response)
    if mutation == "duplicate":
        drifted["offline_source_recovery_records"][1]["sample_index_row_id"] = (
            subject._EXPECTED_SAMPLES[0]
        )
    else:
        records = list(drifted["offline_source_recovery_records"])
        records[0], records[1] = records[1], records[0]
        drifted["offline_source_recovery_records"] = tuple(records)
    _resign_response(drifted)
    monkeypatch.setattr(
        subject, "_EXPECTED_DESIGN_RESPONSE_SHA256", drifted["design_response_sha256"]
    )
    _fake_response(monkeypatch, drifted)
    with pytest.raises(ValueError, match=subject._ERROR):
        _compile(inventory, tmp_path)


@pytest.mark.parametrize(
    "mutation", ("recovery_digest", "evidence_digest", "response_digest")
)
def test_predecessor_digest_drift_rejected(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, response = _setup(tmp_path, monkeypatch)
    drifted = copy.deepcopy(response)
    if mutation == "recovery_digest":
        drifted["offline_source_recovery_records"][0][
            "offline_source_recovery_record_sha256"
        ] = "0" * 64
    elif mutation == "evidence_digest":
        drifted["offline_source_recovery_records"][0][
            "proposed_condition_evidence_record"
        ]["condition_evidence_record_sha256"] = "0" * 64
    else:
        drifted["design_response_sha256"] = "0" * 64
    _fake_response(monkeypatch, drifted)
    with pytest.raises(ValueError, match=subject._ERROR):
        _compile(inventory, tmp_path)


def test_inventory_transport_and_predecessor_production_drift_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match=subject._ERROR):
        _compile(inventory + b" ", tmp_path)
    monkeypatch.setattr(subject, "_OFFLINE_RECOVERY_PRODUCTION_SHA256", "0" * 64)
    with pytest.raises(ValueError, match=subject._ERROR):
        _compile(inventory, tmp_path)


@pytest.mark.parametrize("mutation", ("extra", "missing"))
def test_bundle_schema_extra_or_missing_field_rejected(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    bundle = _compile(inventory, tmp_path)
    if mutation == "extra":
        bundle["authority"] = False
    else:
        bundle.pop("sample_order")
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._bundle_bytes(bundle)


@pytest.mark.parametrize(
    "payload",
    (
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"unterminated":',
        b"\xef\xbb\xbf{}",
        b'{"x":"\x00"}',
        b"{}\n",
    ),
)
def test_malformed_json_nan_duplicate_key_bom_nul_and_newline_rejected(
    payload: bytes,
) -> None:
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._strict_json_object(payload)


def test_output_symlink_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "fixture"
    root.mkdir()
    inventory, _ = _setup(root, monkeypatch)
    bundle = _compile(inventory, root)
    target = tmp_path / "real.json"
    target.write_bytes(b"sentinel")
    output = tmp_path / "bundle.json"
    output.symlink_to(target)
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._materialize_source_evidence_bundle_v1(
            bundle=bundle, output_path=output
        )
    assert target.read_bytes() == b"sentinel"


def test_output_conflict_is_not_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "fixture"
    root.mkdir()
    inventory, _ = _setup(root, monkeypatch)
    bundle = _compile(inventory, root)
    output = tmp_path / "bundle.json"
    output.write_bytes(b"conflict")
    output.chmod(0o644)
    before = output.read_bytes(), output.lstat().st_ino, output.lstat().st_mtime_ns
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._materialize_source_evidence_bundle_v1(
            bundle=bundle, output_path=output
        )
    assert (output.read_bytes(), output.lstat().st_ino, output.lstat().st_mtime_ns) == before


def test_temp_publication_failure_does_not_delete_unknown_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "fixture"
    root.mkdir()
    inventory, _ = _setup(root, monkeypatch)
    bundle = _compile(inventory, root)
    sentinel = tmp_path / "unknown.keep"
    sentinel.write_bytes(b"keep")
    output = tmp_path / "bundle.json"

    def fail_link(*args: object, **kwargs: object) -> None:
        raise PermissionError("synthetic publication failure")

    monkeypatch.setattr(subject.os, "link", fail_link)
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._materialize_source_evidence_bundle_v1(
            bundle=bundle, output_path=output
        )
    assert sentinel.read_bytes() == b"keep"
    assert not output.exists()
    assert tuple(path.name for path in tmp_path.iterdir()) == (
        "fixture", "unknown.keep"
    )


def test_exact_existing_bundle_is_idempotent_with_inode_mtime_and_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "fixture"
    root.mkdir()
    inventory, _ = _setup(root, monkeypatch)
    bundle = _compile(inventory, root)
    output = tmp_path / "bundle.json"
    first = subject._materialize_source_evidence_bundle_v1(
        bundle=bundle, output_path=output
    )
    before = output.lstat(), output.read_bytes()
    second = subject._materialize_source_evidence_bundle_v1(
        bundle=bundle, output_path=output
    )
    after = output.lstat(), output.read_bytes()
    assert first["publication_mode"] == "published_new"
    assert second["publication_mode"] == "idempotent_existing"
    assert before[0].st_ino == after[0].st_ino
    assert before[0].st_mtime_ns == after[0].st_mtime_ns
    assert before[1] == after[1] == subject._bundle_bytes(bundle)
    assert after[0].st_nlink == 1
    assert after[0].st_mode & 0o777 == 0o644
    assert not output.is_symlink()


def test_compile_failure_creates_no_authority_label_or_tensor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, response = _setup(tmp_path, monkeypatch)
    before = CHECKER._tree_snapshot(tmp_path)
    drifted = copy.deepcopy(response)
    drifted["ready_for_offline_source_evidence_compiler"] = False
    _fake_response(monkeypatch, drifted)
    with pytest.raises(ValueError, match=subject._ERROR):
        _compile(inventory, tmp_path)
    assert CHECKER._tree_snapshot(tmp_path) == before
    names = tuple(path.name.lower() for path in tmp_path.rglob("*"))
    assert not any(
        token in name
        for name in names
        for token in ("authority", "label", "tensor", ".pt", ".ckpt")
    )


def test_checker_executes_and_reports_required_flags() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(
                REPO_ROOT
                / "scripts/check_covapie_current11_target_residue_atom_condition_source_evidence_compiler_v1.py"
            ),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": "src",
        },
    )
    assert completed.returncode == 0, completed.stderr
    for line in (
        "source_formal_inventory_bound=true",
        "source_offline_recovery_production_bound=true",
        "source_offline_recovery_response_bound=true",
        "source_recovery_record_count=11",
        "condition_evidence_record_count=11",
        "condition_evidence_digest_valid_count=11",
        "sample_order_verified=true",
        "question_mark_insertion_normalised_empty_preserved=true",
        "condition_evidence_is_not_authority=true",
        "blocked_predecessor_rejected=true",
        "empty_evidence_rejected=true",
        "duplicate_sample_rejected=true",
        "reordered_sample_rejected=true",
        "recovery_digest_drift_rejected=true",
        "evidence_digest_drift_rejected=true",
        "predecessor_response_drift_rejected=true",
        "predecessor_production_drift_rejected=true",
        "deterministic=true",
        "inputs_unchanged=true",
        "files_written=false",
        "condition_authority_created=false",
        "adapter_implemented=false",
        "training_label_created=false",
        "tensor_created=false",
        "model_modified=false",
        "data_loader_modified=false",
        "forward_modified=false",
        "loss_modified=false",
        "training_or_parameter_update=false",
    ):
        assert line in completed.stdout
