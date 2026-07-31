from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from covalent_ext import (
    covapie_target_residue_atom_condition_contract_design_v1 as subject,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_unified_checker():
    path = (
        REPO_ROOT
        / "scripts/check_covapie_current11_unified_effective_authority_view_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "unified_checker_for_target_condition_contract_tests", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def synthetic_view() -> bytes:
    checker = _load_unified_checker()
    inputs = checker._synthetic_inputs(REPO_ROOT)
    return checker._build(REPO_ROOT, inputs)


@pytest.fixture(autouse=True)
def synthetic_view_identity(
    monkeypatch: pytest.MonkeyPatch, synthetic_view: bytes
) -> None:
    value = json.loads(synthetic_view)
    monkeypatch.setattr(
        subject,
        "_FORMAL_VIEW_FILESYSTEM_SHA256",
        hashlib.sha256(synthetic_view).hexdigest(),
    )
    monkeypatch.setattr(
        subject,
        "_FORMAL_VIEW_INTERNAL_SHA256",
        value["unified_effective_authority_view_sha256"],
    )


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _atom_row(
    pdb_id: str,
    *,
    atom_site_id: str = "ATOM-SG",
    endpoint: str = "true",
    altloc: str = ".",
    insertion: str = "?",
    auth_comp: str = "CYS",
    label_comp: str = "CYS",
    auth_atom: str = "SG",
    label_atom: str = "SG",
    type_symbol: str = "S",
    occupancy: str = "0.10",
) -> dict[str, str]:
    return {
        "pdb_id": pdb_id,
        "atom_site_id": atom_site_id,
        "type_symbol": type_symbol,
        "label_atom_id": label_atom,
        "label_comp_id": label_comp,
        "label_asym_id": "LA",
        "label_seq_id": "25",
        "label_alt_id": altloc,
        "auth_atom_id": auth_atom,
        "auth_comp_id": auth_comp,
        "auth_asym_id": "A",
        "auth_seq_id": "125",
        "pdbx_PDB_model_num": "1",
        "pdbx_PDB_ins_code": insertion,
        "is_covalent_endpoint_atom": endpoint,
        "occupancy": occupancy,
    }


def _condition_evidence_record(
    *,
    sample_row: dict[str, str],
    structure_sha256: str,
    atom_values: dict[str, str],
    lineage_mismatch: bool,
) -> dict[str, str]:
    record = {
        "condition_evidence_version": subject._CONDITION_EVIDENCE_VERSION,
        "sample_index_row_id": sample_row["sample_index_row_id"],
        "pdb_id": sample_row["pdb_id"],
        "ligand_comp_id": sample_row["ligand_comp_id"],
        "source_structure_filesystem_sha256": structure_sha256,
        "source_atom_site_id": atom_values["source_atom_site_id"],
        "protein_model_num": atom_values["protein_model_num"],
        "protein_auth_asym_id": atom_values["protein_auth_asym_id"],
        "protein_auth_comp_id": atom_values["protein_auth_comp_id"],
        "protein_auth_seq_id": atom_values["protein_auth_seq_id"],
        "protein_pdbx_PDB_ins_code": atom_values[
            "protein_pdbx_PDB_ins_code"
        ],
        "protein_auth_atom_id": atom_values["protein_auth_atom_id"],
        "condition_evidence_record_sha256": "",
    }
    if lineage_mismatch:
        record["source_atom_site_id"] = "WRONG-ATOM-SITE"
    unsigned = {
        field: record[field]
        for field in subject._CONDITION_EVIDENCE_RECORD_FIELDS
        if field != "condition_evidence_record_sha256"
    }
    canonical = json.dumps(
        unsigned,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    record["condition_evidence_record_sha256"] = hashlib.sha256(
        canonical
    ).hexdigest()
    return record


def _fixture_repo(
    root: Path,
    view_payload: bytes,
    situations: dict[int, str] | None = None,
) -> None:
    situations = situations or {}
    value = json.loads(view_payload)
    sample_fields = (
        "sample_preparation_input_id",
        *subject._FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS,
    )
    atom_fields = subject._ATOM_TABLE_REQUIRED_COLUMNS + (
        "is_covalent_endpoint_atom",
        "occupancy",
    )
    sample_rows: list[dict[str, str]] = []
    for index, effective in enumerate(value["effective_authority_records"], 1):
        authority = effective["effective_authority_record"]
        sample = authority["sample_index_row_id"]
        atom_relative = Path("synthetic_atom_tables") / f"{sample}.csv"
        structure_relative = Path("synthetic_structures") / f"{sample}.cif"
        evidence_relative = Path("synthetic_condition_evidence") / f"{sample}.json"
        situation = situations.get(index, "unique")
        rows = [_atom_row(
            authority["pdb_id"],
            atom_site_id=f"ATOM-{index}",
            altloc="B" if index == 1 else ".",
        )]
        fields = atom_fields
        if situation == "ambiguous":
            rows.append(_atom_row(
                authority["pdb_id"],
                atom_site_id=f"ATOM-{index}",
                altloc="A",
            ))
        elif situation == "zero_match":
            rows[0]["is_covalent_endpoint_atom"] = "false"
            rows[0]["occupancy"] = "1.00"
        elif situation == "schema_incomplete":
            fields = tuple(
                field for field in fields if field != "pdbx_PDB_ins_code"
            )
            rows[0].pop("pdbx_PDB_ins_code")
        elif situation == "identity_mismatch":
            rows[0]["label_comp_id"] = "MET"
        elif situation == "scope_only":
            rows[0]["is_covalent_endpoint_atom"] = "false"
            rows[0]["auth_comp_id"] = ""
            rows[0]["auth_atom_id"] = ""

        atom_values = subject._selected_atom_inventory_values(rows[0])
        sample_row = {
            "sample_index_row_id": sample,
            "sample_preparation_input_id": f"SYNTHETIC_PREP_{index:06d}",
            "pdb_id": authority["pdb_id"],
            "ligand_comp_id": authority["ligand_comp_id"],
            "source_structure_path": structure_relative.as_posix(),
            "source_structure_filesystem_sha256": "",
            "protein_atom_table_path": atom_relative.as_posix(),
            "source_condition_evidence_path_or_record": evidence_relative.as_posix(),
            "source_condition_evidence_sha256": "",
            **atom_values,
        }
        structure_bytes = (
            f"data_{authority['pdb_id']}\n# exact synthetic structure bytes\n"
        ).encode("ascii")
        structure_sha = hashlib.sha256(structure_bytes).hexdigest()
        evidence = _condition_evidence_record(
            sample_row=sample_row,
            structure_sha256=structure_sha,
            atom_values=atom_values,
            lineage_mismatch=situation == "evidence_lineage_mismatch",
        )
        evidence_sha = evidence["condition_evidence_record_sha256"]
        sample_row["source_structure_filesystem_sha256"] = structure_sha
        sample_row["source_condition_evidence_sha256"] = evidence_sha
        if situation == "missing_lineage":
            sample_row["source_structure_path"] = ""
            sample_row["source_structure_filesystem_sha256"] = ""
            sample_row["source_condition_evidence_path_or_record"] = ""
            sample_row["source_condition_evidence_sha256"] = ""
        else:
            if situation != "missing_structure_file":
                (root / structure_relative).parent.mkdir(
                    parents=True, exist_ok=True
                )
                (root / structure_relative).write_bytes(structure_bytes)
            if situation != "missing_evidence_file":
                (root / evidence_relative).parent.mkdir(
                    parents=True, exist_ok=True
                )
                (root / evidence_relative).write_bytes(_ordered_bytes(evidence))
        if situation == "structure_digest_mismatch":
            sample_row["source_structure_filesystem_sha256"] = "0" * 64
        elif situation == "evidence_digest_mismatch":
            sample_row["source_condition_evidence_sha256"] = "0" * 64
        sample_rows.append(sample_row)
        if situation != "missing_table":
            _write_csv(root / atom_relative, fields, rows)
    _write_csv(root / subject._SAMPLE_INDEX_PATH, sample_fields, sample_rows)


def _evaluate(payload: bytes, repo_root: Path) -> dict[str, Any]:
    return subject._reference_design_covapie_target_residue_atom_condition_contract_v1(
        source_unified_effective_authority_view=payload,
        repo_root=repo_root,
    )


def _ordered_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _rehash_view(value: dict[str, Any]) -> bytes:
    for record in value["effective_authority_records"]:
        record["unified_effective_authority_record_sha256"] = subject._record_sha256(
            record,
            subject.unified_view.EXACT10_EFFECTIVE_RECORD_FIELDS,
            "unified_effective_authority_record_sha256",
        )
    value["unified_effective_authority_view_sha256"] = subject._record_sha256(
        value,
        subject.unified_view.EXACT16_VIEW_FIELDS,
        "unified_effective_authority_view_sha256",
    )
    return _ordered_bytes(value)


def _accept_identity(
    monkeypatch: pytest.MonkeyPatch, payload: bytes
) -> None:
    value = json.loads(payload)
    monkeypatch.setattr(
        subject,
        "_FORMAL_VIEW_FILESYSTEM_SHA256",
        hashlib.sha256(payload).hexdigest(),
    )
    monkeypatch.setattr(
        subject,
        "_FORMAL_VIEW_INTERNAL_SHA256",
        value["unified_effective_authority_view_sha256"],
    )


def test_private_module_import_is_silent_and_exports_nothing() -> None:
    assert subject.__all__ == ()
    assert not hasattr(
        subject, "design_covapie_target_residue_atom_condition_contract_v1"
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            (
                "from covalent_ext import "
                "covapie_target_residue_atom_condition_contract_design_v1"
            ),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_exact20_exact12_exact10_exact14_and_digests(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(tmp_path, synthetic_view)
    response = _evaluate(synthetic_view, tmp_path)
    assert tuple(response) == subject._RESPONSE_FIELDS
    assert len(response) == 14
    assert response["canonical_condition_record_fields"] == (
        subject._FUTURE_CONDITION_RECORD_FIELDS
    )
    assert len(response["canonical_condition_record_fields"]) == 20
    assert subject._FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS[:9] == (
        "sample_index_row_id",
        "pdb_id",
        "ligand_comp_id",
        "source_structure_path",
        "source_structure_filesystem_sha256",
        "protein_atom_table_path",
        "source_atom_site_id",
        "source_condition_evidence_path_or_record",
        "source_condition_evidence_sha256",
    )
    assert response["design_response_sha256"] == subject._record_sha256(
        response, subject._RESPONSE_FIELDS, "design_response_sha256"
    )
    assert len(response["field_contract_records"]) == 19
    assert len(response["sample_coverage_records"]) == 11
    for record in response["field_contract_records"]:
        assert tuple(record) == subject._FIELD_CONTRACT_FIELDS
        assert len(record) == 12
        assert record["field_contract_record_sha256"] == subject._record_sha256(
            record, subject._FIELD_CONTRACT_FIELDS, "field_contract_record_sha256"
        )
    for record in response["source_candidate_records"]:
        assert tuple(record) == subject._SOURCE_CANDIDATE_FIELDS
        assert len(record) == 12
        assert record["source_candidate_record_sha256"] == subject._record_sha256(
            record,
            subject._SOURCE_CANDIDATE_FIELDS,
            "source_candidate_record_sha256",
        )
    for record in response["sample_coverage_records"]:
        assert tuple(record) == subject._SAMPLE_COVERAGE_FIELDS
        assert len(record) == 10
        assert record["sample_coverage_record_sha256"] == subject._record_sha256(
            record,
            subject._SAMPLE_COVERAGE_FIELDS,
            "sample_coverage_record_sha256",
        )


def test_canonical_auth_namespace_label_crosswalk_and_locator_consumers(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(tmp_path, synthetic_view)
    response = _evaluate(synthetic_view, tmp_path)
    assert response["canonical_identity_namespace"] == "mmcif_auth_namespace"
    assert subject._CANONICAL_AUTH_IDENTITY_FIELDS == (
        "protein_auth_asym_id",
        "protein_auth_comp_id",
        "protein_auth_seq_id",
        "protein_pdbx_PDB_ins_code",
        "protein_auth_atom_id",
    )
    assert subject._LABEL_CROSSWALK_FIELDS == (
        "protein_label_asym_id",
        "protein_label_comp_id",
        "protein_label_seq_id",
        "protein_label_atom_id",
    )
    by_field = {
        record["field_name"]: record
        for record in response["field_contract_records"]
    }
    assert {
        name for name, record in by_field.items() if not record["audit_only"]
    } == set(subject._ADAPTER_LOCATOR_FIELDS)
    assert all(
        by_field[name]["allowed_future_consumers"]
        == ("target_residue_atom_condition_adapter",)
        for name in subject._ADAPTER_LOCATOR_FIELDS
    )
    assert "cannot substitute" in by_field["protein_auth_asym_id"][
        "missing_value_policy"
    ]


def test_model_insertion_altloc_atom_site_and_feature_semantics(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(tmp_path, synthetic_view)
    response = _evaluate(synthetic_view, tmp_path)
    by_field = {
        record["field_name"]: record
        for record in response["field_contract_records"]
    }
    assert "never default to 1" in by_field["protein_model_num"][
        "normalization_policy"
    ]
    assert "dot or question-mark" in by_field[
        "protein_pdbx_PDB_ins_code"
    ]["normalization_policy"]
    assert "preserve A/B/etc" in by_field["protein_label_alt_id"][
        "normalization_policy"
    ]
    assert "no occupancy fallback" in by_field["protein_label_alt_id"][
        "missing_value_policy"
    ]
    assert by_field["source_atom_site_id"]["audit_only"] is True
    assert by_field["pdb_id"]["audit_only"] is True
    assert by_field["protein_auth_seq_id"]["python_type_contract"] == "exact_str"
    assert "not a numeric feature" in by_field["protein_auth_seq_id"][
        "semantic_definition"
    ]


def test_unique_resolution_normalises_insertion_and_preserves_altloc_b(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(tmp_path, synthetic_view)
    response = _evaluate(synthetic_view, tmp_path)
    assert response["resolved_unique_sample_count"] == 11
    assert response["blocked_sample_count"] == 0
    assert response[
        "ready_for_target_condition_authority_implementation"
    ] is True
    assert response["recommended_next_step"] == subject._RECOMMENDED_AUTHORITY_STEP
    first = response["sample_coverage_records"][0]
    assert first["coverage_status"] == "resolved_unique"
    assert first["unique_atom_match_count"] == 1
    assert first["observed_altloc_ids"] == ("B",)
    assert subject._normalise_mmcif_optional("?") == ""
    assert subject._normalise_mmcif_optional(".") == ""
    assert subject._normalise_mmcif_optional("B") == "B"


def test_locator_complete_but_materialization_lineage_missing_is_rejected(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(tmp_path, synthetic_view, {1: "missing_lineage"})
    response = _evaluate(synthetic_view, tmp_path)
    first = response["sample_coverage_records"][0]
    assert first["complete_identity_candidate_count"] == 1
    assert first["unique_atom_match_count"] == 1
    assert first["coverage_status"] == "schema_incomplete"
    assert first["ready_for_authority_materialization"] is False
    assert {
        "source_structure_path_or_bytes_missing",
        "source_structure_filesystem_sha256_missing",
        "source_condition_evidence_missing",
        "source_condition_evidence_sha256_missing",
    }.issubset(first["blocking_reasons"])
    sample_source = next(
        record for record in response["source_candidate_records"]
        if record["source_candidate_name"].startswith("current11_sample_index")
    )
    assert sample_source["can_uniquely_resolve_target_atom"] is True
    assert response[
        "ready_for_target_condition_authority_implementation"
    ] is False


def test_structure_and_condition_evidence_digests_are_independently_recomputed(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    structure_root = tmp_path / "structure_mismatch"
    evidence_root = tmp_path / "evidence_mismatch"
    _fixture_repo(
        structure_root, synthetic_view, {1: "structure_digest_mismatch"}
    )
    _fixture_repo(
        evidence_root, synthetic_view, {1: "evidence_digest_mismatch"}
    )
    structure = _evaluate(synthetic_view, structure_root)[
        "sample_coverage_records"
    ][0]
    evidence = _evaluate(synthetic_view, evidence_root)[
        "sample_coverage_records"
    ][0]
    assert structure["coverage_status"] == "lineage_mismatch"
    assert "source_structure_filesystem_sha256_mismatch" in structure[
        "blocking_reasons"
    ]
    assert evidence["coverage_status"] == "lineage_mismatch"
    assert "source_condition_evidence_sha256_mismatch" in evidence[
        "blocking_reasons"
    ]


def test_condition_evidence_must_close_same_sample_atom_lineage(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(tmp_path, synthetic_view, {1: "evidence_lineage_mismatch"})
    first = _evaluate(synthetic_view, tmp_path)["sample_coverage_records"][0]
    assert first["coverage_status"] == "lineage_mismatch"
    assert first["ready_for_authority_materialization"] is False
    assert "condition_evidence_sample_atom_lineage_mismatch" in first[
        "blocking_reasons"
    ]


def test_claimed_structure_or_evidence_file_missing_is_missing_source(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    structure_root = tmp_path / "missing_structure"
    evidence_root = tmp_path / "missing_evidence"
    _fixture_repo(
        structure_root, synthetic_view, {1: "missing_structure_file"}
    )
    _fixture_repo(
        evidence_root, synthetic_view, {1: "missing_evidence_file"}
    )
    structure = _evaluate(synthetic_view, structure_root)[
        "sample_coverage_records"
    ][0]
    evidence = _evaluate(synthetic_view, evidence_root)[
        "sample_coverage_records"
    ][0]
    assert structure["coverage_status"] == "missing_source"
    assert "source_structure_file_missing" in structure["blocking_reasons"]
    assert evidence["coverage_status"] == "missing_source"
    assert "source_condition_evidence_file_missing" in evidence[
        "blocking_reasons"
    ]


def test_unique_missing_ambiguous_and_schema_incomplete_are_distinct(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(
        tmp_path,
        synthetic_view,
        {2: "missing_table", 3: "ambiguous", 4: "schema_incomplete"},
    )
    response = _evaluate(synthetic_view, tmp_path)
    statuses = tuple(
        record["coverage_status"]
        for record in response["sample_coverage_records"][:4]
    )
    assert statuses == (
        "resolved_unique",
        "missing_source",
        "ambiguous_atom",
        "schema_incomplete",
    )
    assert response["resolved_unique_sample_count"] == 8
    assert response["blocked_sample_count"] == 3
    assert response[
        "ready_for_target_condition_authority_implementation"
    ] is False
    assert response["recommended_next_step"] == (
        subject._RECOMMENDED_SOURCE_INVENTORY_STEP
    )


def test_zero_match_and_highest_occupancy_do_not_select_an_atom(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(tmp_path, synthetic_view, {1: "zero_match"})
    first = _evaluate(synthetic_view, tmp_path)["sample_coverage_records"][0]
    assert first["coverage_status"] == "missing_source"
    assert first["unique_atom_match_count"] == 0
    assert "target_atom_site_row_not_found" in first["blocking_reasons"]


def test_project_scope_does_not_fill_missing_cys_sg_evidence(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(tmp_path, synthetic_view, {1: "scope_only"})
    first = _evaluate(synthetic_view, tmp_path)["sample_coverage_records"][0]
    assert first["coverage_status"] == "missing_source"
    assert first["complete_identity_candidate_count"] == 0


def test_cys_sg_type_and_auth_label_identity_mismatch_blocks_lineage(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(tmp_path, synthetic_view, {1: "identity_mismatch"})
    first = _evaluate(synthetic_view, tmp_path)["sample_coverage_records"][0]
    assert first["coverage_status"] == "lineage_mismatch"
    assert first["complete_identity_candidate_count"] == 1
    assert first["blocking_reasons"] == (
        "cys_sg_auth_label_type_identity_mismatch",
    )


def test_historical_full_atom_smoke_is_capability_only_and_unrelated(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(tmp_path, synthetic_view)
    response = _evaluate(synthetic_view, tmp_path)
    historical = next(
        record for record in response["source_candidate_records"]
        if record["source_candidate_name"] == "historical_full_atom_smoke_commit"
    )
    assert historical["source_path_or_commit"] == (
        "commit:efe213bae26d30b98272973ff557e7fbf3dc577d"
    )
    assert historical["current11_sample_coverage"] == 0
    assert historical["direct_lineage_to_unified_view"] is False
    assert historical["can_uniquely_resolve_target_atom"] is False
    assert "altloc_B_must_be_preserved_in_successor_policy" in historical[
        "blocking_reasons"
    ]
    assert "pdbx_PDB_ins_code" not in historical["field_inventory"]


def test_source_candidate_sha_is_from_actual_file(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(tmp_path, synthetic_view)
    response = _evaluate(synthetic_view, tmp_path)
    candidate = next(
        record for record in response["source_candidate_records"]
        if record["source_candidate_name"].startswith("current11_sample_index")
    )
    path = tmp_path / candidate["source_path_or_commit"]
    assert path.is_file()
    assert candidate["source_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert candidate["direct_lineage_to_unified_view"] is True


def test_input_exact_types_determinism_input_unchanged_and_zero_writes(
    synthetic_view: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fixture_repo(tmp_path, synthetic_view)
    before_payload = bytes(synthetic_view)
    before_files = {
        path.relative_to(tmp_path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in tmp_path.rglob("*") if path.is_file()
    }
    writes = 0

    def forbidden_write(*_args: object, **_kwargs: object) -> None:
        nonlocal writes
        writes += 1
        raise AssertionError("evaluator attempted a write")

    for name in ("write_bytes", "write_text", "touch", "mkdir"):
        monkeypatch.setattr(Path, name, forbidden_write)
    first = _evaluate(synthetic_view, tmp_path)
    second = _evaluate(synthetic_view, tmp_path)
    after_files = {
        path.relative_to(tmp_path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in tmp_path.rglob("*") if path.is_file()
    }
    assert first == second
    assert synthetic_view == before_payload
    assert before_files == after_files
    assert writes == 0
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._reference_design_covapie_target_residue_atom_condition_contract_v1(
            source_unified_effective_authority_view=bytearray(synthetic_view),
            repo_root=tmp_path,
        )
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._reference_design_covapie_target_residue_atom_condition_contract_v1(
            source_unified_effective_authority_view=synthetic_view,
            repo_root=str(tmp_path),
        )


@pytest.mark.parametrize(
    "bad_payload",
    [b"{}", b'{"a":1,"a":2}', b'{"x":NaN}', b"\xff"],
)
def test_malformed_or_digest_drifted_unified_view_is_rejected(
    synthetic_view: bytes, tmp_path: Path, bad_payload: bytes
) -> None:
    _fixture_repo(tmp_path, synthetic_view)
    with pytest.raises(ValueError, match=subject._ERROR):
        _evaluate(bad_payload, tmp_path)
    with pytest.raises(ValueError, match=subject._ERROR):
        _evaluate(synthetic_view + b" ", tmp_path)


def test_embedded_authority_and_sample_pdb_ligand_identity_are_validated(
    synthetic_view: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fixture_repo(tmp_path, synthetic_view)
    value = json.loads(synthetic_view)
    value["effective_authority_records"][0]["effective_authority_record"][
        "pdb_id"
    ] = "XXXX"
    payload = _rehash_view(value)
    _accept_identity(monkeypatch, payload)
    with pytest.raises(ValueError, match=subject._ERROR):
        _evaluate(payload, tmp_path)


def test_sample_index_pdb_ligand_lineage_mismatch_fails_closed(
    synthetic_view: bytes, tmp_path: Path
) -> None:
    _fixture_repo(tmp_path, synthetic_view)
    path = tmp_path / subject._SAMPLE_INDEX_PATH
    fields, rows = subject._strict_csv(path)
    mutable = [dict(row) for row in rows]
    mutable[0]["pdb_id"] = "XXXX"
    _write_csv(path, fields, mutable)
    first = _evaluate(synthetic_view, tmp_path)["sample_coverage_records"][0]
    assert first["coverage_status"] == "lineage_mismatch"
    assert first["blocking_reasons"] == ("sample_pdb_ligand_identity_mismatch",)


def test_illegal_status_vocabulary_is_rejected() -> None:
    with pytest.raises(ValueError, match=subject._ERROR):
        subject._sample_coverage_record(
            sample_index_row_id=subject._EXPECTED_SAMPLES[0],
            pdb_id="6BV6",
            candidate_source_count=0,
            complete_identity_candidate_count=0,
            unique_atom_match_count=0,
            observed_altloc_ids=(),
            coverage_status="guessed_from_nearest_neighbor",
            blocking_reasons=(),
        )
    assert subject._CONDITION_AUTHORITY_STATUSES == (
        "resolved_authoritative",
        "blocked_missing_source",
        "blocked_ambiguous_atom",
        "blocked_lineage_mismatch",
        "blocked_schema_incomplete",
    )


def test_canonical_serialization_failure_is_standardised(
    synthetic_view: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fixture_repo(tmp_path, synthetic_view)

    def broken_dumps(*_args: object, **_kwargs: object) -> str:
        raise TypeError("synthetic serializer failure")

    monkeypatch.setattr(subject.json, "dumps", broken_dumps)
    with pytest.raises(ValueError, match=subject._ERROR):
        _evaluate(synthetic_view, tmp_path)


def test_no_adapter_encoder_materializer_training_label_or_model_api() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    assert "def design_covapie" not in source
    assert "def encode" not in source
    assert "def materialize" not in source
    assert "torch" not in source
    assert "optimizer" not in source
    assert "backward(" not in source
    assert "occupancy" not in source.split("def _audit_sample_coverage", 1)[1]
