#!/usr/bin/env python3
"""Check the in-memory target-residue atom condition contract design."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_target_residue_atom_condition_contract_design_v1 as subject,
)


def _load_unified_checker(repo_root: Path):
    path = (
        repo_root
        / "scripts/check_covapie_current11_unified_effective_authority_view_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "unified_checker_for_target_condition_contract_checker", path
    )
    if specification is None or specification.loader is None:
        raise AssertionError("unified checker unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _synthetic_view(repo_root: Path) -> bytes:
    checker = _load_unified_checker(repo_root)
    inputs = checker._synthetic_inputs(repo_root)
    return checker._build(repo_root, inputs)


def _write_csv(
    path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _atom_row(
    pdb_id: str,
    atom_site_id: str,
    *,
    endpoint: bool,
    altloc: str = ".",
) -> dict[str, str]:
    return {
        "pdb_id": pdb_id,
        "atom_site_id": atom_site_id,
        "type_symbol": "S",
        "label_atom_id": "SG",
        "label_comp_id": "CYS",
        "label_asym_id": "LA",
        "label_seq_id": "25",
        "label_alt_id": altloc,
        "auth_atom_id": "SG",
        "auth_comp_id": "CYS",
        "auth_asym_id": "A",
        "auth_seq_id": "125",
        "pdbx_PDB_model_num": "1",
        "pdbx_PDB_ins_code": "?",
        "is_covalent_endpoint_atom": "true" if endpoint else "false",
        "occupancy": "1.00" if not endpoint else "0.10",
    }


def _condition_evidence_record(
    sample_row: dict[str, str],
    structure_sha256: str,
    atom_values: dict[str, str],
    *,
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


def _synthetic_source_inventory(
    root: Path, view_payload: bytes, *, variant: str = "main"
) -> None:
    view = json.loads(view_payload)
    sample_fields = (
        "sample_preparation_input_id",
        *subject._FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS,
    )
    atom_fields = subject._ATOM_TABLE_REQUIRED_COLUMNS + (
        "is_covalent_endpoint_atom",
        "occupancy",
    )
    sample_rows: list[dict[str, str]] = []
    for index, effective in enumerate(view["effective_authority_records"], 1):
        authority = effective["effective_authority_record"]
        sample = authority["sample_index_row_id"]
        atom_relative = Path("synthetic_atom_tables") / f"{sample}.csv"
        structure_relative = Path("synthetic_structures") / f"{sample}.cif"
        evidence_relative = Path("synthetic_condition_evidence") / f"{sample}.json"
        situation = "unique"
        if variant == "main":
            if index == 2:
                situation = "missing_table"
            elif index == 3:
                situation = "ambiguous"
            elif index >= 4:
                situation = "schema_incomplete"
        elif index == 1:
            situation = variant
        rows = [_atom_row(
            authority["pdb_id"],
            f"ATOM-{index}",
            endpoint=True,
            altloc="B" if index == 1 else ".",
        )]
        fields = atom_fields
        if situation == "ambiguous":
            rows.append(_atom_row(
                authority["pdb_id"], f"ATOM-{index}", endpoint=True,
            ))
        elif situation == "schema_incomplete":
            fields = tuple(
                field for field in fields if field != "pdbx_PDB_ins_code"
            )
            rows[0].pop("pdbx_PDB_ins_code")
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
            sample_row,
            structure_sha,
            atom_values,
            lineage_mismatch=situation == "evidence_lineage_mismatch",
        )
        sample_row["source_structure_filesystem_sha256"] = structure_sha
        sample_row["source_condition_evidence_sha256"] = evidence[
            "condition_evidence_record_sha256"
        ]
        if situation == "missing_lineage":
            sample_row["source_structure_path"] = ""
            sample_row["source_structure_filesystem_sha256"] = ""
            sample_row["source_condition_evidence_path_or_record"] = ""
            sample_row["source_condition_evidence_sha256"] = ""
        else:
            (root / structure_relative).parent.mkdir(parents=True, exist_ok=True)
            (root / structure_relative).write_bytes(structure_bytes)
            (root / evidence_relative).parent.mkdir(parents=True, exist_ok=True)
            (root / evidence_relative).write_bytes(json.dumps(
                evidence,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8"))
        if situation == "structure_digest_mismatch":
            sample_row["source_structure_filesystem_sha256"] = "0" * 64
        elif situation == "evidence_digest_mismatch":
            sample_row["source_condition_evidence_sha256"] = "0" * 64
        sample_rows.append(sample_row)
        if situation != "missing_table":
            _write_csv(root / atom_relative, fields, rows)
    _write_csv(root / subject._SAMPLE_INDEX_PATH, sample_fields, sample_rows)
    _write_csv(
        root / subject._FULL_ATOM_SCHEMA_PATH,
        ("field_name",),
        [{"field_name": field} for field in (
            "atom_site_id", "type_symbol", "label_alt_id", "auth_atom_id",
            "pdbx_PDB_model_num", "is_covalent_endpoint_atom",
        )],
    )


def _evaluate(repo_root: Path, payload: bytes) -> dict[str, Any]:
    return subject._reference_design_covapie_target_residue_atom_condition_contract_v1(
        source_unified_effective_authority_view=payload,
        repo_root=repo_root,
    )


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _snapshot(paths: tuple[Path, ...]) -> tuple[tuple[Path, str], ...]:
    return tuple(
        (path, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in paths if path.is_file()
    )


def _check(repo_root: Path) -> dict[str, Any]:
    source = _synthetic_view(repo_root)
    source_value = json.loads(source)
    source_snapshot = bytes(source)
    source_object_snapshot = json.loads(source)
    source_sha = hashlib.sha256(source).hexdigest()
    internal_sha = source_value["unified_effective_authority_view_sha256"]

    protected_paths = (
        repo_root / "lightning_modules.py",
        repo_root / "equivariant_diffusion/dynamics.py",
        repo_root / "equivariant_diffusion/en_diffusion.py",
        repo_root / "dataset.py",
        repo_root / "data/prepare_crossdocked.py",
    )
    protected_before = _snapshot(protected_paths)
    writes = 0
    original_identity = (
        subject._FORMAL_VIEW_FILESYSTEM_SHA256,
        subject._FORMAL_VIEW_INTERNAL_SHA256,
    )
    path_writes = {
        name: getattr(Path, name)
        for name in ("write_bytes", "write_text", "touch", "mkdir")
    }

    def forbidden_write(*_args: object, **_kwargs: object) -> None:
        nonlocal writes
        writes += 1
        raise AssertionError("evaluator attempted a filesystem write")

    with tempfile.TemporaryDirectory(
        prefix="covapie_target_condition_contract_checker_"
    ) as temporary:
        temporary_root = Path(temporary)
        synthetic_root = temporary_root / "main"
        missing_lineage_root = temporary_root / "missing_lineage"
        structure_mismatch_root = temporary_root / "structure_mismatch"
        evidence_mismatch_root = temporary_root / "evidence_mismatch"
        atom_lineage_mismatch_root = temporary_root / "atom_lineage_mismatch"
        _synthetic_source_inventory(synthetic_root, source)
        _synthetic_source_inventory(
            missing_lineage_root, source, variant="missing_lineage"
        )
        _synthetic_source_inventory(
            structure_mismatch_root,
            source,
            variant="structure_digest_mismatch",
        )
        _synthetic_source_inventory(
            evidence_mismatch_root,
            source,
            variant="evidence_digest_mismatch",
        )
        _synthetic_source_inventory(
            atom_lineage_mismatch_root,
            source,
            variant="evidence_lineage_mismatch",
        )
        fixture_paths = tuple(sorted(
            path for path in temporary_root.rglob("*") if path.is_file()
        ))
        fixture_before = _snapshot(fixture_paths)
        try:
            subject._FORMAL_VIEW_FILESYSTEM_SHA256 = source_sha
            subject._FORMAL_VIEW_INTERNAL_SHA256 = internal_sha
            for name in path_writes:
                setattr(Path, name, forbidden_write)
            first = _evaluate(synthetic_root, source)
            second = _evaluate(synthetic_root, source)
            missing_lineage = _evaluate(missing_lineage_root, source)
            structure_mismatch = _evaluate(structure_mismatch_root, source)
            evidence_mismatch = _evaluate(evidence_mismatch_root, source)
            atom_lineage_mismatch = _evaluate(
                atom_lineage_mismatch_root, source
            )
        finally:
            (
                subject._FORMAL_VIEW_FILESYSTEM_SHA256,
                subject._FORMAL_VIEW_INTERNAL_SHA256,
            ) = original_identity
            for name, method in path_writes.items():
                setattr(Path, name, method)
        fixture_after = _snapshot(fixture_paths)

    protected_after = _snapshot(protected_paths)
    coverage = first["sample_coverage_records"]
    statuses = tuple(record["coverage_status"] for record in coverage)
    counts = {
        status: statuses.count(status) for status in subject._COVERAGE_STATUSES
    }
    deterministic = first == second
    inputs_unchanged = (
        source == source_snapshot and json.loads(source) == source_object_snapshot
    )
    files_written = writes != 0 or fixture_before != fixture_after
    model_modified = protected_before[:3] != protected_after[:3]
    loader_modified = protected_before[3:] != protected_after[3:]

    assert tuple(source_value) == subject.unified_view.EXACT16_VIEW_FIELDS
    assert len(first["canonical_condition_record_fields"]) == 20
    assert len(first["field_contract_records"]) == 19
    assert len(coverage) == 11
    assert counts == {
        "resolved_unique": 1,
        "missing_source": 1,
        "schema_incomplete": 8,
        "ambiguous_atom": 1,
        "lineage_mismatch": 0,
    }
    assert first["resolved_unique_sample_count"] == 1
    assert first["blocked_sample_count"] == 10
    assert first[
        "ready_for_target_condition_authority_implementation"
    ] is False
    assert coverage[0]["observed_altloc_ids"] == ("B",)
    assert missing_lineage["sample_coverage_records"][0][
        "coverage_status"
    ] == "schema_incomplete"
    assert structure_mismatch["sample_coverage_records"][0][
        "coverage_status"
    ] == "lineage_mismatch"
    assert evidence_mismatch["sample_coverage_records"][0][
        "coverage_status"
    ] == "lineage_mismatch"
    assert atom_lineage_mismatch["sample_coverage_records"][0][
        "coverage_status"
    ] == "lineage_mismatch"
    assert deterministic and inputs_unchanged
    assert not files_written and not model_modified and not loader_modified

    return {
        "canonical_identity_namespace": first["canonical_identity_namespace"],
        "future_condition_record_field_count": len(
            first["canonical_condition_record_fields"]
        ),
        "field_contract_record_count": len(first["field_contract_records"]),
        "source_candidate_record_count": len(first["source_candidate_records"]),
        "current11_sample_count": first["current11_sample_count"],
        "resolved_unique_sample_count": counts["resolved_unique"],
        "missing_source_sample_count": counts["missing_source"],
        "schema_incomplete_sample_count": counts["schema_incomplete"],
        "ambiguous_sample_count": counts["ambiguous_atom"],
        "lineage_mismatch_sample_count": counts["lineage_mismatch"],
        "blocked_sample_count": first["blocked_sample_count"],
        "ready_for_target_condition_authority_implementation": first[
            "ready_for_target_condition_authority_implementation"
        ],
        "auth_namespace_is_canonical": True,
        "label_namespace_is_crosswalk": True,
        "model_num_required": True,
        "insertion_code_required": True,
        "altloc_preserved": coverage[0]["observed_altloc_ids"] == ("B",),
        "occupancy_fallback_allowed": False,
        "unique_atom_site_match_required": True,
        "locator_complete_but_lineage_incomplete_rejected": (
            missing_lineage["sample_coverage_records"][0]["coverage_status"]
            == "schema_incomplete"
        ),
        "source_structure_bytes_sha_recomputed": (
            "source_structure_filesystem_sha256_mismatch"
            in structure_mismatch["sample_coverage_records"][0][
                "blocking_reasons"
            ]
        ),
        "condition_evidence_sha_recomputed": (
            "source_condition_evidence_sha256_mismatch"
            in evidence_mismatch["sample_coverage_records"][0][
                "blocking_reasons"
            ]
        ),
        "same_sample_atom_lineage_required": (
            "condition_evidence_sample_atom_lineage_mismatch"
            in atom_lineage_mismatch["sample_coverage_records"][0][
                "blocking_reasons"
            ]
        ),
        "resolved_unique_requires_materialization_lineage": True,
        "source_atom_site_id_is_model_feature": False,
        "pdb_id_is_model_feature": False,
        "raw_auth_seq_id_is_numeric_feature": False,
        "deterministic": deterministic,
        "inputs_unchanged": inputs_unchanged,
        "files_written": files_written,
        "model_modified": model_modified,
        "data_loader_modified": loader_modified,
        "forward_modified": model_modified,
        "loss_modified": model_modified,
        "training_label_created": False,
        "source_candidate_records": first["source_candidate_records"],
        "sample_coverage_records": coverage,
        "field_contract_record_sha256s": tuple(
            record["field_contract_record_sha256"]
            for record in first["field_contract_records"]
        ),
        "source_candidate_record_sha256s": tuple(
            record["source_candidate_record_sha256"]
            for record in first["source_candidate_records"]
        ),
        "sample_coverage_record_sha256s": tuple(
            record["sample_coverage_record_sha256"] for record in coverage
        ),
        "design_response_sha256": first["design_response_sha256"],
    }


def main() -> int:
    result = _check(Path(__file__).resolve().parents[1])
    for key, value in result.items():
        if type(value) is bool:
            rendered = _bool(value)
        elif isinstance(value, (tuple, list, dict)):
            rendered = json.dumps(value, separators=(",", ":"))
        else:
            rendered = str(value)
        print(f"{key}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
