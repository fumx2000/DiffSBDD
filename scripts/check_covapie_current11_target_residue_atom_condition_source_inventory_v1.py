#!/usr/bin/env python3
"""Check the pure in-memory Current11 target-condition source inventory."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_current11_multi_boundary_authority_bundle_v1 as multi_authority,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_adapter_v1 as adapter,
)
from covalent_ext import (
    covapie_current11_unified_effective_authority_view_v1 as unified_view,
)
from covalent_ext import (
    covapie_target_residue_atom_condition_contract_design_v1 as contract_design,
)
from covalent_ext import (
    covapie_current11_target_residue_atom_condition_source_inventory_v1 as subject,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _ordered_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _load_unified_checker(repo_root: Path):
    path = repo_root / "scripts/check_covapie_current11_unified_effective_authority_view_v1.py"
    specification = importlib.util.spec_from_file_location(
        "unified_checker_for_source_inventory", path
    )
    if specification is None or specification.loader is None:
        raise AssertionError("unified checker unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _synthetic_view(repo_root: Path) -> bytes:
    checker = _load_unified_checker(repo_root)
    return checker._build(repo_root, checker._synthetic_inputs(repo_root))


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
    index: int,
    *,
    atom_site_id: str | None = None,
    altloc: str = ".",
    insertion: str = "?",
) -> dict[str, str]:
    return {
        "pdb_id": pdb_id,
        "atom_site_id": atom_site_id or f"ATOM-{index}",
        "type_symbol": "S",
        "label_atom_id": "SG",
        "label_comp_id": "CYS",
        "label_asym_id": "LA",
        "label_seq_id": str(20 + index),
        "label_alt_id": altloc,
        "auth_atom_id": "SG",
        "auth_comp_id": "CYS",
        "auth_asym_id": "A",
        "auth_seq_id": str(120 + index),
        "pdbx_PDB_model_num": "1",
        "pdbx_PDB_ins_code": insertion,
        "is_covalent_endpoint_atom": "true",
    }


def _atom_values(row: dict[str, str]) -> dict[str, str]:
    return contract_design._selected_atom_inventory_values(row)


def _evidence(
    sample_row: dict[str, str], structure_sha: str, atom: dict[str, str]
) -> dict[str, str]:
    record = {
        "condition_evidence_version": contract_design._CONDITION_EVIDENCE_VERSION,
        "sample_index_row_id": sample_row["sample_index_row_id"],
        "pdb_id": sample_row["pdb_id"],
        "ligand_comp_id": sample_row["ligand_comp_id"],
        "source_structure_filesystem_sha256": structure_sha,
        "source_atom_site_id": atom["source_atom_site_id"],
        "protein_model_num": atom["protein_model_num"],
        "protein_auth_asym_id": atom["protein_auth_asym_id"],
        "protein_auth_comp_id": atom["protein_auth_comp_id"],
        "protein_auth_seq_id": atom["protein_auth_seq_id"],
        "protein_pdbx_PDB_ins_code": atom[
            "protein_pdbx_PDB_ins_code"
        ],
        "protein_auth_atom_id": atom["protein_auth_atom_id"],
        "condition_evidence_record_sha256": "",
    }
    record["condition_evidence_record_sha256"] = subject._record_sha256(
        record,
        contract_design._CONDITION_EVIDENCE_RECORD_FIELDS,
        "condition_evidence_record_sha256",
    )
    return record


def _fixture_repo(
    root: Path,
    view_payload: bytes,
    situations: dict[int, str] | None = None,
) -> None:
    situations = situations or {}
    view = json.loads(view_payload)
    sample_fields = (
        "sample_preparation_input_id",
        *contract_design._FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS,
    )
    atom_fields = contract_design._ATOM_TABLE_REQUIRED_COLUMNS + (
        "is_covalent_endpoint_atom",
    )
    locator_fields = (
        "sample_preparation_input_id",
        "pdb_id",
        "matched_atom_site_id",
        "atom_site_insertion_raw_value",
    )
    sample_rows: list[dict[str, str]] = []
    locator_rows: list[dict[str, str]] = []
    for index, effective in enumerate(view["effective_authority_records"], 1):
        authority = effective["effective_authority_record"]
        sample = authority["sample_index_row_id"]
        situation = situations.get(index, "complete")
        table_relative = Path("synthetic/atom") / f"{sample}.csv"
        structure_relative = Path("synthetic/structure") / f"{sample}.cif"
        evidence_relative = Path("synthetic/evidence") / f"{sample}.json"
        first_atom = _atom_row(
            authority["pdb_id"],
            index,
            altloc="B" if index == 1 else ".",
        )
        atom_rows = [first_atom]
        if situation == "ambiguous":
            atom_rows.append(
                _atom_row(
                    authority["pdb_id"],
                    index,
                    atom_site_id=first_atom["atom_site_id"],
                    altloc="A",
                )
            )
        atom = _atom_values(first_atom)
        row = {
            "sample_index_row_id": sample,
            "sample_preparation_input_id": f"SYNTHETIC_PREP_{index:06d}",
            "pdb_id": authority["pdb_id"],
            "ligand_comp_id": authority["ligand_comp_id"],
            "source_structure_path": structure_relative.as_posix(),
            "source_structure_filesystem_sha256": "",
            "protein_atom_table_path": table_relative.as_posix(),
            "source_atom_site_id": atom["source_atom_site_id"],
            "source_condition_evidence_path_or_record": evidence_relative.as_posix(),
            "source_condition_evidence_sha256": "",
            "protein_model_num": atom["protein_model_num"],
            "protein_auth_asym_id": atom["protein_auth_asym_id"],
            "protein_auth_comp_id": atom["protein_auth_comp_id"],
            "protein_auth_seq_id": atom["protein_auth_seq_id"],
            "protein_pdbx_PDB_ins_code": "",
            "protein_auth_atom_id": atom["protein_auth_atom_id"],
            "protein_type_symbol": atom["protein_type_symbol"],
            "protein_label_alt_id": atom["protein_label_alt_id"],
            "protein_label_asym_id": atom["protein_label_asym_id"],
            "protein_label_comp_id": atom["protein_label_comp_id"],
            "protein_label_seq_id": atom["protein_label_seq_id"],
            "protein_label_atom_id": atom["protein_label_atom_id"],
        }
        structure = f"data_{authority['pdb_id']}\n# synthetic bytes\n".encode("ascii")
        structure_sha = _sha256(structure)
        evidence = _evidence(row, structure_sha, atom)
        row["source_structure_filesystem_sha256"] = structure_sha
        row["source_condition_evidence_sha256"] = evidence[
            "condition_evidence_record_sha256"
        ]
        if situation == "schema_incomplete":
            row["source_structure_path"] = ""
            row["source_structure_filesystem_sha256"] = ""
            row["source_condition_evidence_path_or_record"] = ""
            row["source_condition_evidence_sha256"] = ""
        else:
            if situation != "missing_structure":
                (root / structure_relative).parent.mkdir(parents=True, exist_ok=True)
                (root / structure_relative).write_bytes(structure)
            (root / evidence_relative).parent.mkdir(parents=True, exist_ok=True)
            (root / evidence_relative).write_bytes(_ordered_bytes(evidence))
        if situation == "structure_digest_mismatch":
            row["source_structure_filesystem_sha256"] = "0" * 64
        sample_rows.append(row)
        locator_rows.append(
            {
                "sample_preparation_input_id": row[
                    "sample_preparation_input_id"
                ],
                "pdb_id": row["pdb_id"],
                "matched_atom_site_id": first_atom["atom_site_id"],
                "atom_site_insertion_raw_value": "?",
            }
        )
        _write_csv(root / table_relative, atom_fields, atom_rows)
    _write_csv(root / contract_design._SAMPLE_INDEX_PATH, sample_fields, sample_rows)
    _write_csv(
        root / contract_design._LOCATOR_SIDECAR_PATH,
        locator_fields,
        locator_rows,
    )


def _accept_synthetic_view(payload: bytes) -> tuple[str, str]:
    previous = (
        contract_design._FORMAL_VIEW_FILESYSTEM_SHA256,
        contract_design._FORMAL_VIEW_INTERNAL_SHA256,
    )
    view = json.loads(payload)
    contract_design._FORMAL_VIEW_FILESYSTEM_SHA256 = _sha256(payload)
    contract_design._FORMAL_VIEW_INTERNAL_SHA256 = view[
        "unified_effective_authority_view_sha256"
    ]
    return previous


def _tree_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def _check(repo_root: Path) -> dict[str, Any]:
    source_view = _synthetic_view(repo_root)
    previous_hashes = _accept_synthetic_view(source_view)
    situations = {
        1: "complete",
        2: "missing_structure",
        3: "structure_digest_mismatch",
        4: "ambiguous",
        **{index: "schema_incomplete" for index in range(5, 12)},
    }
    with tempfile.TemporaryDirectory(prefix="covapie_source_inventory_") as temporary:
        fixture_root = Path(temporary)
        _fixture_repo(fixture_root, source_view, situations)
        before = _tree_snapshot(fixture_root)
        source_snapshot = bytes(source_view)

        design_calls = 0
        unified_calls = 0
        authority_calls = 0
        adapter_calls = 0
        original_design = contract_design._reference_design_covapie_target_residue_atom_condition_contract_v1
        original_unified = unified_view.build_covapie_current11_unified_effective_authority_view_v1
        original_authority = multi_authority.build_covapie_current11_multi_boundary_authority_bundle_v1
        original_adapter = adapter.adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1

        def counted_design(**kwargs: Any) -> dict[str, Any]:
            nonlocal design_calls
            design_calls += 1
            return original_design(**kwargs)

        def forbidden_unified(**kwargs: Any) -> bytes:
            nonlocal unified_calls
            unified_calls += 1
            raise AssertionError("unified view builder called")

        def forbidden_authority(**kwargs: Any) -> bytes:
            nonlocal authority_calls
            authority_calls += 1
            raise AssertionError("authority builder called")

        def forbidden_adapter(**kwargs: Any) -> bytes:
            nonlocal adapter_calls
            adapter_calls += 1
            raise AssertionError("adapter called")

        contract_design._reference_design_covapie_target_residue_atom_condition_contract_v1 = counted_design
        unified_view.build_covapie_current11_unified_effective_authority_view_v1 = forbidden_unified
        multi_authority.build_covapie_current11_multi_boundary_authority_bundle_v1 = forbidden_authority
        adapter.adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = forbidden_adapter
        try:
            first = subject.build_covapie_current11_target_residue_atom_condition_source_inventory_v1(
                source_unified_effective_authority_view=source_view,
                repo_root=fixture_root,
            )
            first_decoded = json.loads(first)
            first_decoded["source_inventory_records"][0]["pdb_id"] = "MUTATED"
            second = subject.build_covapie_current11_target_residue_atom_condition_source_inventory_v1(
                source_unified_effective_authority_view=source_view,
                repo_root=fixture_root,
            )
            sample_path = fixture_root / contract_design._SAMPLE_INDEX_PATH
            sample_before_drift = sample_path.read_bytes()
            design_source_snapshot_drift_rejected = False

            def drift_after_design(**kwargs: Any) -> dict[str, Any]:
                response = original_design(**kwargs)
                sample_path.write_bytes(sample_before_drift + b"\n")
                return response

            contract_design._reference_design_covapie_target_residue_atom_condition_contract_v1 = drift_after_design
            try:
                subject.build_covapie_current11_target_residue_atom_condition_source_inventory_v1(
                    source_unified_effective_authority_view=source_view,
                    repo_root=fixture_root,
                )
            except ValueError as error:
                design_source_snapshot_drift_rejected = (
                    str(error) == subject._ERROR
                )
            finally:
                sample_path.write_bytes(sample_before_drift)
                contract_design._reference_design_covapie_target_residue_atom_condition_contract_v1 = counted_design
        finally:
            contract_design._reference_design_covapie_target_residue_atom_condition_contract_v1 = original_design
            unified_view.build_covapie_current11_unified_effective_authority_view_v1 = original_unified
            multi_authority.build_covapie_current11_multi_boundary_authority_bundle_v1 = original_authority
            adapter.adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = original_adapter
            (
                contract_design._FORMAL_VIEW_FILESYSTEM_SHA256,
                contract_design._FORMAL_VIEW_INTERNAL_SHA256,
            ) = previous_hashes

        after = _tree_snapshot(fixture_root)
        value = json.loads(second)
        records = value["source_inventory_records"]
        observations = [
            observation
            for record in records
            for observation in record["field_observation_records"]
        ]
        artifacts = [
            artifact
            for record in records
            for artifact in record["source_artifact_status_records"]
        ]
        by_role = {artifact["artifact_role"]: artifact for artifact in records[0]["source_artifact_status_records"]}
        altloc = next(
            item
            for item in records[0]["field_observation_records"]
            if item["field_name"] == "protein_label_alt_id"
        )
        insertion = next(
            item
            for item in records[0]["field_observation_records"]
            if item["field_name"] == "protein_pdbx_PDB_ins_code"
        )
        candidate_records = value["source_candidate_records"]
        candidates_by_name = {
            item["source_candidate_name"]: item for item in candidate_records
        }
        source_candidate_names_unique = (
            len(candidates_by_name) == len(candidate_records)
        )
        sample_candidate = candidates_by_name[
            "current11_sample_index_and_referenced_protein_atom_tables"
        ]
        locator_candidate = candidates_by_name[
            "current11_residue_locator_provider_sidecar"
        ]
        sample_index_bound_to_design_snapshot = (
            sample_candidate["source_path_or_commit"]
            == str(contract_design._SAMPLE_INDEX_PATH)
            and sample_candidate["source_sha256"]
            == _sha256(
                (fixture_root / contract_design._SAMPLE_INDEX_PATH).read_bytes()
            )
            and sample_candidate["current11_sample_coverage"] == 11
            and sample_candidate["direct_lineage_to_unified_view"] is True
        )
        locator_sidecar_bound_to_design_snapshot = (
            locator_candidate["source_path_or_commit"]
            == str(contract_design._LOCATOR_SIDECAR_PATH)
            and locator_candidate["source_sha256"]
            == _sha256(
                (fixture_root / contract_design._LOCATOR_SIDECAR_PATH).read_bytes()
            )
            and locator_candidate["authority_level"]
            == "blocking_locator_evidence_non_authoritative"
            and locator_candidate["can_uniquely_resolve_target_atom"] is False
        )
        round_trip = _ordered_bytes(value) == second
        results: dict[str, Any] = {
            "inventory_version": value["target_residue_atom_condition_source_inventory_version"],
            "inventory_field_count": len(value),
            "field_observation_version": observations[0]["field_observation_version"],
            "artifact_status_version": artifacts[0]["artifact_status_version"],
            "sample_record_version": records[0]["source_inventory_record_version"],
            "required_field_count": len(value["future_source_inventory_required_fields"]),
            "condition_evidence_field_count": len(value["condition_evidence_record_fields"]),
            "source_candidate_record_count": value["source_candidate_record_count"],
            "sample_inventory_record_count": len(records),
            "resolved_unique_sample_count": value["resolved_unique_sample_count"],
            "missing_source_sample_count": value["missing_source_sample_count"],
            "schema_incomplete_sample_count": value["schema_incomplete_sample_count"],
            "ambiguous_atom_sample_count": value["ambiguous_atom_sample_count"],
            "lineage_mismatch_sample_count": value["lineage_mismatch_sample_count"],
            "ready_for_target_condition_authority_implementation": value["ready_for_target_condition_authority_implementation"],
            "field_observation_record_count_total": len(observations),
            "artifact_status_record_count_total": len(artifacts),
            "structure_sha_recomputed": bool(by_role["source_structure"]["recomputed_sha256"]),
            "condition_evidence_sha_recomputed": bool(by_role["condition_evidence"]["recomputed_sha256"]),
            "atom_table_sha_recorded": bool(by_role["protein_atom_table"]["recomputed_sha256"]),
            "normalised_empty_requires_explicit_provenance": insertion["observation_status"] == "present_normalised_empty_with_explicit_provenance",
            "altloc_b_preserved": altloc["normalised_value"] == "B",
            "locator_sidecar_is_not_authority": records[4]["locator_sidecar_match_count"] == 1 and not records[4]["ready_for_authority_materialization"],
            "sample_index_bound_to_design_snapshot": sample_index_bound_to_design_snapshot,
            "locator_sidecar_bound_to_design_snapshot": locator_sidecar_bound_to_design_snapshot,
            "source_candidate_names_unique": source_candidate_names_unique,
            "design_source_snapshot_drift_rejected": design_source_snapshot_drift_rejected,
            "contract_design_calls_per_build": design_calls // 2,
            "unified_view_builder_calls_per_build": unified_calls // 2,
            "authority_builder_calls_per_build": authority_calls // 2,
            "adapter_calls_per_build": adapter_calls // 2,
            "filesystem_writes": before != after,
            "deterministic": first == second,
            "round_trip_valid": round_trip,
            "inputs_unchanged": source_view == source_snapshot and before == after,
            "responses_isolated": json.loads(second)["source_inventory_records"][0]["pdb_id"] != "MUTATED",
            "field_observation_record_sha256s": [item["field_observation_record_sha256"] for item in observations],
            "artifact_status_record_sha256s": [item["artifact_status_record_sha256"] for item in artifacts],
            "sample_inventory_record_sha256s": [item["source_inventory_record_sha256"] for item in records],
            "inventory_bundle_sha256": value["source_inventory_bundle_sha256"],
            "transport_sha256": _sha256(second),
            "transport_size": len(second),
            "formal_inventory_file_created": False,
            "condition_authority_created": False,
            "training_label_created": False,
            "model_modified": False,
        }
        expected = {
            "inventory_field_count": 24,
            "required_field_count": 21,
            "sample_inventory_record_count": 11,
            "resolved_unique_sample_count": 1,
            "missing_source_sample_count": 1,
            "schema_incomplete_sample_count": 7,
            "ambiguous_atom_sample_count": 1,
            "lineage_mismatch_sample_count": 1,
            "ready_for_target_condition_authority_implementation": False,
            "field_observation_record_count_total": 231,
            "artifact_status_record_count_total": 33,
            "structure_sha_recomputed": True,
            "condition_evidence_sha_recomputed": True,
            "atom_table_sha_recorded": True,
            "normalised_empty_requires_explicit_provenance": True,
            "altloc_b_preserved": True,
            "locator_sidecar_is_not_authority": True,
            "sample_index_bound_to_design_snapshot": True,
            "locator_sidecar_bound_to_design_snapshot": True,
            "source_candidate_names_unique": True,
            "design_source_snapshot_drift_rejected": True,
            "contract_design_calls_per_build": 1,
            "unified_view_builder_calls_per_build": 0,
            "authority_builder_calls_per_build": 0,
            "adapter_calls_per_build": 0,
            "filesystem_writes": False,
            "deterministic": True,
            "round_trip_valid": True,
            "inputs_unchanged": True,
            "responses_isolated": True,
            "inventory_bundle_sha256": "eacc45c53f80aad984e9d6c2a4f1b094982e9a01a6f8539ea160bc5b8311ab87",
            "transport_sha256": "55041fe228e45d6b14a0ed323b151928ac162a9f487778ee6abcec0975f51595",
            "transport_size": 139903,
            "formal_inventory_file_created": False,
            "condition_authority_created": False,
            "training_label_created": False,
            "model_modified": False,
        }
        for key, expected_value in expected.items():
            if results[key] != expected_value:
                raise AssertionError(f"{key}: {results[key]!r} != {expected_value!r}")
        return results


def main() -> int:
    results = _check(REPO_ROOT)
    for key, value in results.items():
        if isinstance(value, (dict, list, tuple)):
            rendered = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
        elif isinstance(value, bool):
            rendered = str(value).lower()
        else:
            rendered = str(value)
        print(f"{key}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
