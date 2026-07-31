from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import inspect
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

from covalent_ext import (
    covapie_current11_target_residue_atom_condition_offline_source_recovery_design_v1
    as subject,
)
from covalent_ext import (
    covapie_target_residue_atom_condition_contract_design_v1 as contract_design,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_checker():
    path = REPO_ROOT / "scripts/check_covapie_current11_target_residue_atom_condition_offline_source_recovery_design_v1.py"
    spec = importlib.util.spec_from_file_location("offline_source_recovery_checker", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECKER = _load_checker()


def _accept(monkeypatch: pytest.MonkeyPatch, inventory: bytes, sample: bytes, locator: bytes) -> None:
    value = json.loads(inventory)
    monkeypatch.setattr(subject, "_FORMAL_INVENTORY_TRANSPORT_SHA256", hashlib.sha256(inventory).hexdigest())
    monkeypatch.setattr(subject, "_FORMAL_INVENTORY_INTERNAL_SHA256", value["source_inventory_bundle_sha256"])
    monkeypatch.setattr(subject, "_SAMPLE_INDEX_SHA256", hashlib.sha256(sample).hexdigest())
    monkeypatch.setattr(subject, "_LOCATOR_SIDECAR_SHA256", hashlib.sha256(locator).hexdigest())


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[bytes, dict[str, bytes]]:
    files = CHECKER._fixture_repo(tmp_path)
    inventory = CHECKER._synthetic_inventory(
        files["sample"], files["locator"], files
    )
    _accept(monkeypatch, inventory, files["sample"], files["locator"])
    return inventory, files


def _evaluate(inventory: bytes, root: Path) -> dict[str, Any]:
    return subject._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1(
        source_formal_inventory=inventory, repo_root=root
    )


def _csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), [dict(row) for row in reader]


def _rewrite_csv(path: Path, transform: Callable[[list[dict[str, str]]], None]) -> bytes:
    fields, rows = _csv(path)
    transform(rows)
    payload = CHECKER._csv_bytes(fields, rows)
    path.write_bytes(payload)
    return payload


def _rebind(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> bytes:
    sample = (tmp_path / "inputs/sample.csv").read_bytes()
    locator = (tmp_path / "inputs/locator.csv").read_bytes()
    reader = csv.DictReader(io.StringIO(sample.decode("utf-8"), newline=""))
    table_payloads = {
        row["protein_atom_table_path"]:
        (tmp_path / row["protein_atom_table_path"]).read_bytes()
        for row in reader
    }
    inventory = CHECKER._synthetic_inventory(sample, locator, table_payloads)
    _accept(monkeypatch, inventory, sample, locator)
    return inventory


def _resign_inventory(value: dict[str, Any]) -> bytes:
    value["source_inventory_bundle_sha256"] = subject._record_sha256(
        value, subject._FORMAL_FIELDS, "source_inventory_bundle_sha256"
    )
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")


def _first_table_artifact(value: dict[str, Any]) -> dict[str, Any]:
    return next(
        artifact
        for artifact in value["source_inventory_records"][0][
            "source_artifact_status_records"
        ]
        if artifact["artifact_role"] == "protein_atom_table"
    )


def _resign_first_sample(value: dict[str, Any], artifact: dict[str, Any]) -> bytes:
    artifact["artifact_status_record_sha256"] = subject._record_sha256(
        artifact, subject._ARTIFACT_FIELDS, "artifact_status_record_sha256"
    )
    sample = value["source_inventory_records"][0]
    sample["source_inventory_record_sha256"] = subject._record_sha256(
        sample, subject._SAMPLE_INVENTORY_FIELDS,
        "source_inventory_record_sha256",
    )
    return _resign_inventory(value)


def _first(response: dict[str, Any]) -> dict[str, Any]:
    return response["offline_source_recovery_records"][0]


def test_private_signature_constants_and_silent_import() -> None:
    assert subject.__all__ == ()
    signature = inspect.signature(
        subject._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1
    )
    assert tuple(signature.parameters) == ("source_formal_inventory", "repo_root")
    assert all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in signature.parameters.values())
    assert signature.parameters["source_formal_inventory"].annotation == "bytes"
    assert signature.parameters["repo_root"].annotation == "Path"
    assert signature.return_annotation == "dict[str, Any]"
    completed = subprocess.run(
        [sys.executable, "-B", "-c", "from covalent_ext import covapie_current11_target_residue_atom_condition_offline_source_recovery_design_v1"],
        cwd=REPO_ROOT, check=False, capture_output=True, text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_formal_inventory_exact_validation_response_shapes_and_digests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    response = _evaluate(inventory, tmp_path)
    assert tuple(response) == subject._RESPONSE_FIELDS
    assert len(response) == 14
    assert response["source_snapshot_binding_verified"] is True
    assert response["sample_order"] == subject._EXPECTED_SAMPLES
    assert response["sample_count"] == 11
    assert response["design_response_sha256"] == subject._record_sha256(
        response, subject._RESPONSE_FIELDS, "design_response_sha256"
    )
    for record in response["offline_source_recovery_records"]:
        assert tuple(record) == subject._RECORD_FIELDS
        assert len(record) == 20
        assert record["offline_source_recovery_record_sha256"] == subject._record_sha256(
            record, subject._RECORD_FIELDS, "offline_source_recovery_record_sha256"
        )
        assert all(type(record[field]) is tuple for field in (
            "raw_locator_candidates", "claimed_raw_sha256s", "matched_atom_site_ids",
            "recovered_source_inventory_fields", "unrecovered_source_inventory_fields",
            "blocking_reasons",
        ))


def test_formal_inventory_strict_transport_internal_order_and_record_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory, files = _setup(tmp_path, monkeypatch)
    for malformed in (inventory + b"\n", b'\xef\xbb\xbf{}', b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":"\x00"}'):
        monkeypatch.setattr(subject, "_FORMAL_INVENTORY_TRANSPORT_SHA256", hashlib.sha256(malformed).hexdigest())
        with pytest.raises(ValueError, match=subject._ERROR):
            _evaluate(malformed, tmp_path)
    value = json.loads(inventory)
    value["source_inventory_records"][0]["source_inventory_record_sha256"] = "0" * 64
    value["source_inventory_bundle_sha256"] = subject._record_sha256(value, subject._FORMAL_FIELDS, "source_inventory_bundle_sha256")
    tampered = json.dumps(value, separators=(",", ":")).encode()
    _accept(monkeypatch, tampered, files["sample"], files["locator"])
    with pytest.raises(ValueError, match=subject._ERROR):
        _evaluate(tampered, tmp_path)


def test_source_snapshot_binding_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    path = tmp_path / "inputs/sample.csv"
    path.write_bytes(path.read_bytes() + b"#changed\n")
    with pytest.raises(ValueError, match=subject._ERROR):
        _evaluate(inventory, tmp_path)


def test_protein_table_bytes_changed_after_formal_inventory_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    table = tmp_path / "tables/t001_protein.csv"
    table.write_bytes(table.read_bytes() + b"# changed after formal inventory\n")
    with pytest.raises(ValueError, match=subject._ERROR):
        _evaluate(inventory, tmp_path)


def test_stale_formal_table_sha_and_locator_drift_are_rejected_after_resigning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory, files = _setup(tmp_path, monkeypatch)
    for mutation in ("sha", "locator"):
        value = json.loads(inventory)
        artifact = _first_table_artifact(value)
        if mutation == "sha":
            artifact["recomputed_sha256"] = "f" * 64
        else:
            artifact["declared_locator"] = "tables/drifted_protein.csv"
        tampered = _resign_first_sample(value, artifact)
        _accept(monkeypatch, tampered, files["sample"], files["locator"])
        with pytest.raises(ValueError, match=subject._ERROR):
            _evaluate(tampered, tmp_path)


@pytest.mark.parametrize(("source_index", "replacement_role"), ((2, "protein_atom_table"), (1, "condition_evidence")))
def test_formal_artifact_roles_duplicate_or_missing_are_rejected(
    source_index: int, replacement_role: str, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory, files = _setup(tmp_path, monkeypatch)
    value = json.loads(inventory)
    artifact = value["source_inventory_records"][0][
        "source_artifact_status_records"
    ][source_index]
    artifact["artifact_role"] = replacement_role
    tampered = _resign_first_sample(value, artifact)
    _accept(monkeypatch, tampered, files["sample"], files["locator"])
    with pytest.raises(ValueError, match=subject._ERROR):
        _evaluate(tampered, tmp_path)


def test_safe_relative_path_absolute_traversal_backslash_and_symlink(
    tmp_path: Path,
) -> None:
    tmp_path.mkdir(exist_ok=True)
    assert subject._safe_relative(tmp_path, "/absolute/raw.cif")[2] == "unsafe"
    assert subject._safe_relative(tmp_path, "../raw.cif")[2] == "unsafe"
    assert subject._safe_relative(tmp_path, "raw\\escape.cif")[2] == "unsafe"
    target = tmp_path / "target"
    target.mkdir()
    (tmp_path / "linked").symlink_to(target, target_is_directory=True)
    assert subject._safe_relative(tmp_path, "linked/raw.cif")[2] == "symlink_rejected"


def test_checker_scenarios_cover_raw_sha_gzip_schema_identity_and_ambiguity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    response = _evaluate(inventory, tmp_path)
    assert response["recovery_status_counts"] == {
        "recoverable_offline_unique": 1, "blocked_raw_not_declared": 0,
        "blocked_raw_source_missing": 1, "blocked_raw_locator_conflict": 0,
        "blocked_raw_unsafe": 0, "blocked_raw_sha_mismatch": 1,
        "blocked_raw_decode_invalid": 0, "blocked_mmcif_schema_incomplete": 6,
        "blocked_atom_site_row_missing": 0, "blocked_atom_site_row_ambiguous": 1,
        "blocked_identity_mismatch": 1, "blocked_cys_sg_identity_mismatch": 0,
        "blocked_insertion_provenance": 0,
    }
    record = _first(response)
    assert record["raw_filesystem_status"] == "available_regular"
    assert record["claimed_raw_sha256s"] == (record["recomputed_raw_sha256"],)
    assert record["matched_atom_site_ids"] == ("1000",)
    assert record["raw_atom_site_match_count"] == 1
    assert record["ready_for_offline_source_evidence_compiler"] is True
    assert response["ready_for_offline_source_evidence_compiler"] is False
    assert response["recommended_next_step"] == "resolve_covapie_current11_missing_raw_structure_sources_v1"


def test_raw_locator_conflict_and_symlink_are_not_hidden(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    table = tmp_path / "tables/t001_protein.csv"
    _rewrite_csv(table, lambda rows: rows[0].update(source_raw_file="raw/different.cif.gz"))
    inventory = _rebind(tmp_path, monkeypatch)
    assert _first(_evaluate(inventory, tmp_path))["recovery_status"] == "blocked_raw_locator_conflict"

    inventory, _ = _setup(tmp_path / "second", monkeypatch)
    root = tmp_path / "second"
    raw = root / "raw/t001.cif.gz"
    target = root / "target.cif.gz"
    target.write_bytes(raw.read_bytes())
    raw.unlink()
    raw.symlink_to(target)
    record = _first(_evaluate(inventory, root))
    assert record["recovery_status"] == "blocked_raw_unsafe"
    assert record["raw_filesystem_status"] == "symlink_rejected"


def test_gzip_decode_limit_and_mmcif_tokenizer_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._decode_raw(b"not-gzip", "raw.cif.gz")
    monkeypatch.setattr(subject, "_MAX_DECOMPRESSED_BYTES", 16)
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._decode_raw(gzip.compress(b"x" * 17, mtime=0), "raw.cif.gz")
    valid = "data_TEST\nloop_\n_atom_site.id\n_atom_site.auth_atom_id\n1 'S G'\n#\n"
    block, fields, rows = subject._parse_atom_site(valid)
    assert (block, fields, rows[0]["_atom_site.auth_atom_id"]) == (
        "TEST", ("_atom_site.id", "_atom_site.auth_atom_id"), "S G"
    )
    for malformed in (
        "data_X\nloop_\n_atom_site.id\n_atom_site.id\n1 1\n#\n",
        "data_X\nloop_\n_atom_site.id\n_atom_site.type_symbol\n1\n#\n",
        "data_X\n#\n",
    ):
        with pytest.raises(ValueError, match=subject._ERROR):
            subject._parse_atom_site(malformed)


def test_matched_atom_site_id_is_only_selector_without_occupancy_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch)
    locator_path = tmp_path / "inputs/locator.csv"
    _rewrite_csv(locator_path, lambda rows: rows[0].update(matched_atom_site_id="ABSENT"))
    inventory = _rebind(tmp_path, monkeypatch)
    record = _first(_evaluate(inventory, tmp_path))
    assert record["recovery_status"] == "blocked_atom_site_row_missing"
    assert record["raw_atom_site_match_count"] == 0
    assert record["proposed_condition_evidence_record"] == {}


@pytest.mark.parametrize(
    ("field", "value", "table_field", "sample_field", "locator_field"),
    (
        ("auth_comp_id", "ALA", "residue_name", "covalent_residue_name", None),
        ("auth_atom_id", "CB", "atom_name", "covalent_residue_atom_name", "matched_residue_atom_name"),
        ("type_symbol", "C", "type_symbol", None, None),
    ),
)
def test_cys_sg_s_must_be_observed_not_defaulted(
    field: str, value: str, table_field: str, sample_field: str | None,
    locator_field: str | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _setup(tmp_path, monkeypatch)
    values = CHECKER._raw_values(0)
    values[field] = value
    compressed = gzip.compress(CHECKER._mmcif("T001", values, "recoverable"), mtime=0)
    (tmp_path / "raw/t001.cif.gz").write_bytes(compressed)
    _rewrite_csv(tmp_path / "tables/t001_protein.csv", lambda rows: rows[0].update({table_field: value}))
    if sample_field:
        _rewrite_csv(tmp_path / "inputs/sample.csv", lambda rows: rows[0].update({sample_field: value}))
    digest = hashlib.sha256(compressed).hexdigest()
    def update_locator(rows: list[dict[str, str]]) -> None:
        rows[0]["expected_raw_sha256"] = digest
        rows[0]["observed_raw_sha256"] = digest
        if locator_field:
            rows[0][locator_field] = value
    _rewrite_csv(tmp_path / "inputs/locator.csv", update_locator)
    inventory = _rebind(tmp_path, monkeypatch)
    assert _first(_evaluate(inventory, tmp_path))["recovery_status"] == "blocked_cys_sg_identity_mismatch"


def test_protein_coordinates_and_namespaces_are_crosschecked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    _rewrite_csv(tmp_path / "tables/t001_protein.csv", lambda rows: rows[0].update(x="999.0"))
    inventory = _rebind(tmp_path, monkeypatch)
    record = _first(_evaluate(inventory, tmp_path))
    assert record["recovery_status"] == "blocked_identity_mismatch"
    assert "sample_locator_or_protein_table_identity_mismatch" in record["blocking_reasons"]


def test_insertion_and_altloc_raw_provenance_and_model_are_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch)
    _rewrite_csv(tmp_path / "inputs/locator.csv", lambda rows: rows[0].update(insertion_evidence_agreement="false"))
    inventory = _rebind(tmp_path, monkeypatch)
    record = _first(_evaluate(inventory, tmp_path))
    assert record["recovery_status"] == "blocked_insertion_provenance"
    assert "protein_pdbx_PDB_ins_code" in record["unrecovered_source_inventory_fields"]
    assert "protein_label_alt_id" in record["recovered_source_inventory_fields"]


def test_proposed_evidence_uses_committed_contract_and_is_not_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    evidence = _first(_evaluate(inventory, tmp_path))["proposed_condition_evidence_record"]
    assert tuple(evidence) == contract_design._CONDITION_EVIDENCE_RECORD_FIELDS
    assert evidence["condition_evidence_version"] == contract_design._CONDITION_EVIDENCE_VERSION
    assert evidence["protein_pdbx_PDB_ins_code"] == ""
    assert evidence["condition_evidence_record_sha256"] == subject._record_sha256(
        evidence, contract_design._CONDITION_EVIDENCE_RECORD_FIELDS,
        "condition_evidence_record_sha256",
    )
    assert "authority" not in evidence


def test_deterministic_inputs_unchanged_zero_writes_and_training_sources_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory, _ = _setup(tmp_path, monkeypatch)
    before = CHECKER._tree_snapshot(tmp_path)
    protected = {
        path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
        for path in ("lightning_modules.py", "dataset.py")
    }
    first = _evaluate(inventory, tmp_path)
    second = _evaluate(inventory, tmp_path)
    assert first == second
    assert CHECKER._tree_snapshot(tmp_path) == before
    assert protected == {
        path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
        for path in protected
    }
    assert not any(path.name.endswith((".tmp", ".part")) for path in tmp_path.rglob("*"))


def test_malformed_csv_json_and_canonical_serialization_fail_closed() -> None:
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._strict_csv(b'a,a\n"unterminated\n')
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._strict_json(b'{"x":1,"x":2}')
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._canonical_json_bytes({"bad": {1, 2}})
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._canonical_json_bytes({"bad": float("nan")})


def test_checker_executes_and_reports_required_safety_flags() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(REPO_ROOT / "scripts/check_covapie_current11_target_residue_atom_condition_offline_source_recovery_design_v1.py")],
        cwd=REPO_ROOT, check=False, capture_output=True, text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src"},
    )
    assert completed.returncode == 0, completed.stderr
    for line in (
        "source_snapshot_binding_verified=true", "raw_filesystem_sha_recomputed=true",
        "gzip_decoded_in_memory=true", "matched_atom_site_id_used_as_only_selector=true",
        "occupancy_fallback_allowed=false", "altloc_b_preserved=true",
        "insertion_raw_provenance_preserved=true", "cys_sg_identity_observed_not_defaulted=true",
        "condition_evidence_file_written=false", "deterministic=true", "inputs_unchanged=true",
        "protein_atom_tables_bound_to_formal_inventory=true",
        "protein_atom_table_artifact_roles_unique=true",
        "protein_atom_table_snapshot_drift_rejected=true",
        "formal_inventory_to_table_snapshot_chain_verified=true",
        "files_written=false", "model_modified=false", "data_loader_modified=false",
        "forward_modified=false", "loss_modified=false", "training_label_created=false",
    ):
        assert line in completed.stdout
