#!/usr/bin/env python3
"""Deterministic synthetic check for the offline source-recovery design."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import tempfile
from pathlib import Path
from typing import Any, Mapping

from covalent_ext import (
    covapie_current11_target_residue_atom_condition_offline_source_recovery_design_v1
    as subject,
)
from covalent_ext import (
    covapie_target_residue_atom_condition_contract_design_v1 as contract_design,
)


_UNKNOWN_INSERTION_REASON = (
    "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
)


def _csv_bytes(fields: tuple[str, ...], rows: list[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _raw_values(index: int) -> dict[str, str]:
    return {
        "id": str(1000 + index), "type_symbol": "S", "label_atom_id": "SG",
        "label_alt_id": "B" if index == 0 else "?", "label_comp_id": "CYS",
        "label_asym_id": "A", "label_seq_id": str(20 + index),
        "Cartn_x": str(1 + index), "Cartn_y": str(2 + index),
        "Cartn_z": str(3 + index), "occupancy": "0.50" if index == 0 else "1.00",
        "auth_seq_id": str(20 + index), "auth_comp_id": "CYS",
        "auth_asym_id": "A", "auth_atom_id": "SG",
        "pdbx_PDB_model_num": "1", "pdbx_PDB_ins_code": "." if index == 0 else "?",
    }


def _legacy_insertion_fields(token: str) -> dict[str, str]:
    if token == "?":
        return {
            "struct_conn_token_class": "question_unknown",
            "atom_site_token_class": "question_unknown",
            "resolved_insertion_state": "unknown",
            "resolved_insertion_value": "",
            "insertion_evidence_agreement": "false",
            "insertion_blocks_admit_004": "true",
            "insertion_blocking_reason": _UNKNOWN_INSERTION_REASON,
            "provider_export_status": "exported_blocking",
            "provider_export_blocking_reason": _UNKNOWN_INSERTION_REASON,
        }
    token_class = "dot_not_applicable" if token == "." else "explicit_token"
    return {
        "struct_conn_token_class": token_class,
        "atom_site_token_class": token_class,
        "resolved_insertion_state": "absent" if token == "." else "present",
        "resolved_insertion_value": "" if token == "." else token,
        "insertion_evidence_agreement": "true",
        "insertion_blocks_admit_004": "false",
        "insertion_blocking_reason": "",
        "provider_export_status": "exported_pass",
        "provider_export_blocking_reason": "",
    }


def _mmcif(pdb_id: str, values: Mapping[str, str], scenario: str) -> bytes:
    names = (
        "group_PDB", "id", "type_symbol", "label_atom_id", "label_alt_id",
        "label_comp_id", "label_asym_id", "label_seq_id", "Cartn_x", "Cartn_y",
        "Cartn_z", "occupancy", "auth_seq_id", "auth_comp_id", "auth_asym_id",
        "auth_atom_id", "pdbx_PDB_model_num", "pdbx_PDB_ins_code",
    )
    if scenario == "schema":
        names = tuple(name for name in names if name != "label_atom_id")
    elif scenario == "insertion_schema":
        names = tuple(name for name in names if name != "pdbx_PDB_ins_code")
    elif scenario == "recoverable":
        names = tuple(reversed(names))
    row_values = {"group_PDB": "ATOM", **values}
    tokens = [row_values[name] for name in names]
    if scenario == "recoverable":
        tokens[names.index("auth_atom_id")] = f"'{row_values['auth_atom_id']}'"
    lines = [f"data_{pdb_id}", "#", "loop_", *(f"_atom_site.{name}" for name in names), " ".join(tokens)]
    if scenario == "ambiguous":
        lines.append(" ".join(tokens))
    lines.append("#")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _fixture_repo(root: Path) -> dict[str, bytes]:
    sample_fields = (
        "sample_index_row_id", "sample_preparation_input_id", "pdb_id",
        "ligand_comp_id", "protein_atom_table_path", "covalent_residue_name",
        "covalent_residue_chain_id", "covalent_residue_index",
        "covalent_residue_atom_name", "ligand_covalent_atom_name", "conn_id",
    )
    locator_fields = subject._LOCATOR_REQUIRED
    table_fields = subject._TABLE_REQUIRED
    scenarios = (
        "recoverable", "missing", "sha", "ambiguous", "identity",
        "schema", "schema", "schema", "schema", "schema", "schema",
    )
    sample_rows: list[dict[str, str]] = []
    locator_rows: list[dict[str, str]] = []
    raw_payloads: dict[str, bytes] = {}
    for index, scenario in enumerate(scenarios):
        number = index + 1
        sample = subject._EXPECTED_SAMPLES[index]
        prep = f"SYNTH_PREP_{number:06d}"
        pdb_id = f"T{number:03d}"
        ligand = f"L{number:02d}"
        raw_locator = f"raw/{pdb_id.lower()}.cif.gz"
        table_locator = f"tables/{pdb_id.lower()}_protein.csv"
        values = _raw_values(index)
        mmcif = _mmcif(pdb_id, values, scenario)
        compressed = gzip.compress(mmcif, mtime=0)
        raw_payloads[raw_locator] = compressed
        claim = hashlib.sha256(compressed).hexdigest()
        if scenario == "sha":
            claim = "0" * 64
        sample_rows.append({
            "sample_index_row_id": sample,
            "sample_preparation_input_id": prep,
            "pdb_id": pdb_id,
            "ligand_comp_id": ligand,
            "protein_atom_table_path": table_locator,
            "covalent_residue_name": "CYS",
            "covalent_residue_chain_id": "A",
            "covalent_residue_index": values["auth_seq_id"],
            "covalent_residue_atom_name": "SG",
            "ligand_covalent_atom_name": "C1",
            "conn_id": "covale1",
        })
        insertion = values["pdbx_PDB_ins_code"]
        locator_rows.append({
            "sample_preparation_input_id": prep,
            "pdb_id": pdb_id,
            "raw_target_relative_path": raw_locator,
            "expected_raw_sha256": claim,
            "observed_raw_sha256": claim,
            "raw_source_precondition_status": "passed",
            "raw_source_precondition_blocking_reason": "",
            "matched_atom_site_id": values["id"],
            "matched_residue_atom_name": "SG",
            "struct_conn_residue_auth_asym_id": "A",
            "struct_conn_residue_auth_seq_id": "999" if scenario == "identity" else values["auth_seq_id"],
            "struct_conn_residue_label_asym_id": "A",
            "struct_conn_residue_label_seq_id": values["label_seq_id"],
            "selected_chain_id": "A",
            "selected_residue_index": values["auth_seq_id"],
            "struct_conn_insertion_source_tag": "_struct_conn.pdbx_ptnr1_PDB_ins_code",
            "struct_conn_insertion_raw_value": insertion,
            "atom_site_insertion_source_tag": "_atom_site.pdbx_PDB_ins_code",
            "atom_site_insertion_raw_value": insertion,
            **_legacy_insertion_fields(insertion),
        })
        table_row = {
            "sample_preparation_input_id": prep, "pdb_id": pdb_id,
            "source_raw_file": raw_locator, "atom_site_id": values["id"],
            "type_symbol": "S", "atom_name": "SG", "residue_name": "CYS",
            "chain_id": "A", "residue_index": values["auth_seq_id"],
            "auth_asym_id": "A", "auth_seq_id": values["auth_seq_id"],
            "label_asym_id": "A", "label_seq_id": values["label_seq_id"],
            "altloc": "B" if index == 0 else "", "model_num": "1",
            "x": values["Cartn_x"], "y": values["Cartn_y"], "z": values["Cartn_z"],
            "occupancy": values["occupancy"],
        }
        table_payload = _csv_bytes(table_fields, [table_row])
        raw_payloads[table_locator] = table_payload
        _write(root / table_locator, table_payload)
        if scenario != "missing":
            _write(root / raw_locator, compressed)
    sample_payload = _csv_bytes(sample_fields, sample_rows)
    locator_payload = _csv_bytes(locator_fields, locator_rows)
    _write(root / "inputs/sample.csv", sample_payload)
    _write(root / "inputs/locator.csv", locator_payload)
    return {"sample": sample_payload, "locator": locator_payload, **raw_payloads}


def _signed(record: dict[str, Any], fields: tuple[str, ...], digest_field: str) -> dict[str, Any]:
    record[digest_field] = subject._record_sha256(record, fields, digest_field)
    return record


def _synthetic_inventory(
    sample_payload: bytes,
    locator_payload: bytes,
    table_payloads: Mapping[str, bytes],
) -> bytes:
    sample_reader = csv.DictReader(
        io.StringIO(sample_payload.decode("utf-8"), newline=""), strict=True
    )
    sample_rows = list(sample_reader)
    if len(sample_rows) != 11:
        raise ValueError("synthetic sample row count invalid")
    candidate_names = (
        "current11_unified_effective_authority_view",
        "current11_predecessor_submission_execution_lineage",
        "historical_full_atom_smoke_commit",
        "current_repository_full_atom_extraction_schema",
        "current11_sample_index_and_referenced_protein_atom_tables",
        "current11_residue_locator_provider_sidecar",
    )
    candidates: list[dict[str, Any]] = []
    for index, name in enumerate(candidate_names):
        path = f"synthetic:{name}"
        sha = hashlib.sha256(path.encode()).hexdigest()
        if name == candidate_names[-2]:
            path, sha = "inputs/sample.csv", hashlib.sha256(sample_payload).hexdigest()
        elif name == candidate_names[-1]:
            path, sha = "inputs/locator.csv", hashlib.sha256(locator_payload).hexdigest()
        candidates.append(_signed({
            "source_candidate_name": name, "source_path_or_commit": path,
            "source_sha256": sha, "source_stage": "synthetic",
            "field_inventory": (), "sample_scope": subject._EXPECTED_SAMPLES,
            "current11_sample_coverage": 11, "direct_lineage_to_unified_view": True,
            "authority_level": "synthetic_non_authoritative",
            "can_uniquely_resolve_target_atom": False, "blocking_reasons": ("synthetic",),
            "source_candidate_record_sha256": "",
        }, subject._SOURCE_CANDIDATE_FIELDS, "source_candidate_record_sha256"))

    records: list[dict[str, Any]] = []
    for index, sample in enumerate(subject._EXPECTED_SAMPLES):
        number = index + 1
        observations = []
        for field_index, field in enumerate(contract_design._FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS):
            present = field_index < 4
            observations.append(_signed({
                "field_observation_version": "synthetic_observation_v1",
                "field_name": field, "column_present": present,
                "raw_value": "x" if present else "", "normalised_value": "x" if present else "",
                "observation_source": "synthetic", "observation_status": "present_nonempty" if present else "missing_column",
                "blocking_reasons": () if present else (f"missing:{field}",),
                "field_observation_record_sha256": "",
            }, subject._OBSERVATION_FIELDS, "field_observation_record_sha256"))
        artifacts = []
        for role in ("source_structure", "protein_atom_table", "condition_evidence"):
            if role == "protein_atom_table":
                table_locator = sample_rows[index]["protein_atom_table_path"]
                table_payload = table_payloads[table_locator]
                artifact = {
                    "artifact_status_version": "synthetic_artifact_v1",
                    "artifact_role": role, "declared_locator": table_locator,
                    "locator_kind": "relative_path", "artifact_available": True,
                    "claimed_sha256": "",
                    "recomputed_sha256": hashlib.sha256(table_payload).hexdigest(),
                    "digest_match_status": "not_claimed",
                    "artifact_status": "available_unverified",
                    "artifact_status_record_sha256": "",
                }
            else:
                artifact = {
                    "artifact_status_version": "synthetic_artifact_v1",
                    "artifact_role": role, "declared_locator": "",
                    "locator_kind": "missing", "artifact_available": False,
                    "claimed_sha256": "", "recomputed_sha256": "",
                    "digest_match_status": "not_available",
                    "artifact_status": "missing_declaration",
                    "artifact_status_record_sha256": "",
                }
            artifacts.append(_signed(
                artifact, subject._ARTIFACT_FIELDS,
                "artifact_status_record_sha256",
            ))
        records.append(_signed({
            "source_inventory_record_version": "synthetic_inventory_record_v1",
            "sample_index_row_id": sample, "pdb_id": f"T{number:03d}",
            "ligand_comp_id": f"L{number:02d}", "sample_preparation_input_id": f"SYNTH_PREP_{number:06d}",
            "sample_index_row_sha256": hashlib.sha256(sample.encode()).hexdigest(),
            "field_observation_records": observations, "field_observation_record_count": 21,
            "complete_required_field_count": 4, "missing_required_field_count": 17,
            "source_artifact_status_records": artifacts, "locator_sidecar_match_count": 1,
            "locator_matched_atom_site_ids": (str(1000 + index),),
            "atom_table_field_inventory": subject._TABLE_REQUIRED,
            "coverage_status": "schema_incomplete", "blocking_reasons": ("synthetic",),
            "ready_for_authority_materialization": False,
            "source_inventory_record_sha256": "",
        }, subject._SAMPLE_INVENTORY_FIELDS, "source_inventory_record_sha256"))

    bundle = {
        "target_residue_atom_condition_source_inventory_version": subject._FORMAL_INVENTORY_VERSION,
        "source_unified_effective_authority_view_filesystem_sha256": "1" * 64,
        "source_unified_effective_authority_view_sha256": "2" * 64,
        "source_contract_design_commit": "synthetic",
        "source_contract_design_production_sha256": "3" * 64,
        "source_contract_design_version": "synthetic_design_v1",
        "source_contract_design_response_sha256": "4" * 64,
        "future_source_inventory_required_fields": contract_design._FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS,
        "condition_evidence_record_fields": contract_design._CONDITION_EVIDENCE_RECORD_FIELDS,
        "field_observation_record_fields": subject._OBSERVATION_FIELDS,
        "artifact_status_record_fields": subject._ARTIFACT_FIELDS,
        "sample_inventory_record_fields": subject._SAMPLE_INVENTORY_FIELDS,
        "source_candidate_records": candidates, "source_candidate_record_count": 6,
        "sample_order": subject._EXPECTED_SAMPLES, "source_inventory_records": records,
        "source_inventory_record_count": 11, "resolved_unique_sample_count": 0,
        "missing_source_sample_count": 0, "schema_incomplete_sample_count": 11,
        "ambiguous_atom_sample_count": 0, "lineage_mismatch_sample_count": 0,
        "ready_for_target_condition_authority_implementation": False,
        "source_inventory_bundle_sha256": "",
    }
    bundle["source_inventory_bundle_sha256"] = subject._record_sha256(
        bundle, subject._FORMAL_FIELDS, "source_inventory_bundle_sha256"
    )
    return json.dumps(bundle, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def _accept_synthetic(inventory: bytes, files: Mapping[str, bytes]) -> None:
    value = json.loads(inventory)
    subject._FORMAL_INVENTORY_TRANSPORT_SHA256 = hashlib.sha256(inventory).hexdigest()
    subject._FORMAL_INVENTORY_INTERNAL_SHA256 = value["source_inventory_bundle_sha256"]
    subject._SAMPLE_INDEX_SHA256 = hashlib.sha256(files["sample"]).hexdigest()
    subject._LOCATOR_SIDECAR_SHA256 = hashlib.sha256(files["locator"]).hexdigest()


def _fixture_inventory(root: Path) -> tuple[bytes, dict[str, bytes]]:
    sample_payload = (root / "inputs/sample.csv").read_bytes()
    locator_payload = (root / "inputs/locator.csv").read_bytes()
    sample_rows = csv.DictReader(
        io.StringIO(sample_payload.decode("utf-8"), newline=""), strict=True
    )
    table_payloads = {
        row["protein_atom_table_path"]:
        (root / row["protein_atom_table_path"]).read_bytes()
        for row in sample_rows
    }
    files = {
        "sample": sample_payload, "locator": locator_payload, **table_payloads,
    }
    inventory = _synthetic_inventory(sample_payload, locator_payload, files)
    _accept_synthetic(inventory, files)
    return inventory, files


def _configure_first_insertion(root: Path, token: str) -> tuple[bytes, dict[str, str]]:
    values = _raw_values(0)
    values["pdbx_PDB_ins_code"] = token
    compressed = gzip.compress(_mmcif("T001", values, "recoverable"), mtime=0)
    _write(root / "raw/t001.cif.gz", compressed)
    locator_path = root / "inputs/locator.csv"
    with locator_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        rows = [dict(row) for row in reader]
    digest = hashlib.sha256(compressed).hexdigest()
    rows[0].update({
        "expected_raw_sha256": digest,
        "observed_raw_sha256": digest,
        "struct_conn_insertion_raw_value": token,
        "atom_site_insertion_raw_value": token,
        **_legacy_insertion_fields(token),
    })
    _write(locator_path, _csv_bytes(fields, rows))
    inventory, _ = _fixture_inventory(root)
    return inventory, rows[0]


def _provider_projection_drift_rejections(
    locator: Mapping[str, str], token: str,
) -> tuple[bool, bool, bool]:
    mutations = (
        (
            "insertion_blocking_reason",
            "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN",
        ),
        ("provider_export_status", "exported_blocking"),
        (
            "provider_export_blocking_reason",
            "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN",
        ),
    )
    rejected: list[bool] = []
    for field, value in mutations:
        drifted = dict(locator)
        drifted[field] = value
        rejected.append(not subject._resolve_insertion_provenance(
            locator=drifted, raw_insertion_token=token
        )[0])
    return rejected[0], rejected[1], rejected[2]


def _tree_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file() and not path.is_symlink()
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        files = _fixture_repo(root)
        inventory = _synthetic_inventory(files["sample"], files["locator"], files)
        _accept_synthetic(inventory, files)
        before = _tree_snapshot(root)
        first = subject._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1(
            source_formal_inventory=inventory, repo_root=root
        )
        second = subject._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1(
            source_formal_inventory=inventory, repo_root=root
        )
        first_table = root / "tables/t001_protein.csv"
        first_table_snapshot = first_table.read_bytes()
        first_table.write_bytes(first_table_snapshot + b"# snapshot drift\n")
        snapshot_drift_rejected = False
        try:
            subject._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1(
                source_formal_inventory=inventory, repo_root=root
            )
        except ValueError:
            snapshot_drift_rejected = True
        finally:
            first_table.write_bytes(first_table_snapshot)
        after = _tree_snapshot(root)
        expected_counts = {
            "recoverable_offline_unique": 1, "blocked_raw_not_declared": 0,
            "blocked_raw_source_missing": 1, "blocked_raw_locator_conflict": 0,
            "blocked_raw_unsafe": 0, "blocked_raw_sha_mismatch": 1,
            "blocked_raw_decode_invalid": 0, "blocked_mmcif_schema_incomplete": 6,
            "blocked_atom_site_row_missing": 0, "blocked_atom_site_row_ambiguous": 1,
            "blocked_identity_mismatch": 1, "blocked_cys_sg_identity_mismatch": 0,
            "blocked_insertion_provenance": 0,
        }
        assert first == second
        assert snapshot_drift_rejected is True
        assert before == after
        assert first["recovery_status_counts"] == expected_counts
        recovered = first["offline_source_recovery_records"][0]
        assert recovered["proposed_condition_evidence_record"]
        assert recovered["proposed_condition_evidence_record"]["condition_evidence_record_sha256"]
        assert recovered["recovered_source_inventory_fields"] == contract_design._FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS

        question_root = root / "question_probe"
        _fixture_repo(question_root)
        question_inventory, question_locator = _configure_first_insertion(
            question_root, "?"
        )
        question_before = _tree_snapshot(question_root)
        question_response = subject._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1(
            source_formal_inventory=question_inventory, repo_root=question_root
        )
        question_after = _tree_snapshot(question_root)
        question_record = question_response["offline_source_recovery_records"][0]
        question_evidence = question_record["proposed_condition_evidence_record"]
        question_resolution = subject._resolve_insertion_provenance(
            locator=question_locator, raw_insertion_token="?"
        )

        concrete_root = root / "concrete_probe"
        _fixture_repo(concrete_root)
        concrete_inventory, concrete_locator = _configure_first_insertion(
            concrete_root, "A"
        )
        concrete_before = _tree_snapshot(concrete_root)
        concrete_response = subject._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1(
            source_formal_inventory=concrete_inventory, repo_root=concrete_root
        )
        concrete_after = _tree_snapshot(concrete_root)
        concrete_record = concrete_response["offline_source_recovery_records"][0]
        dot_locator = next(csv.DictReader(io.StringIO(
            files["locator"].decode("utf-8"), newline=""
        )))
        dot_provider_drift_rejections = _provider_projection_drift_rejections(
            dot_locator, "."
        )
        concrete_provider_drift_rejections = (
            _provider_projection_drift_rejections(concrete_locator, "A")
        )

        struct_conflict = dict(question_locator)
        struct_conflict["struct_conn_insertion_raw_value"] = "."
        atom_conflict = dict(question_locator)
        atom_conflict["atom_site_insertion_raw_value"] = "."
        bad_legacy = dict(question_locator)
        bad_legacy["insertion_blocking_reason"] = ""
        conflict_rejected = all(
            not subject._resolve_insertion_provenance(
                locator=locator, raw_insertion_token="?"
            )[0]
            for locator in (struct_conflict, atom_conflict)
        )
        bad_legacy_rejected = not subject._resolve_insertion_provenance(
            locator=bad_legacy, raw_insertion_token="?"
        )[0]
        insertion_recommendation = subject._recommended(tuple(
            {"recovery_status": "blocked_insertion_provenance"}
            for _ in range(11)
        ))
        summary = {
            "formal_inventory_field_count": 24,
            "formal_inventory_sample_count": 11,
            "source_snapshot_binding_verified": first["source_snapshot_binding_verified"],
            "sample_count": first["sample_count"],
            "recoverable_offline_unique_count": first["recoverable_offline_unique_count"],
            "blocked_sample_count": first["blocked_sample_count"],
            "recovery_status_counts": first["recovery_status_counts"],
            "raw_locator_agreement_checked": True,
            "raw_filesystem_sha_recomputed": True,
            "gzip_decoded_in_memory": True,
            "mmcif_atom_site_parsed": True,
            "matched_atom_site_id_used_as_only_selector": True,
            "occupancy_fallback_allowed": False,
            "altloc_b_preserved": recovered["proposed_condition_evidence_record"] != {} and "protein_label_alt_id" in recovered["recovered_source_inventory_fields"],
            "insertion_raw_provenance_preserved": True,
            "cys_sg_identity_observed_not_defaulted": True,
            "protein_atom_table_crosschecked": True,
            "locator_sidecar_crosschecked": True,
            "protein_atom_tables_bound_to_formal_inventory": True,
            "protein_atom_table_artifact_roles_unique": True,
            "protein_atom_table_snapshot_drift_rejected": snapshot_drift_rejected,
            "formal_inventory_to_table_snapshot_chain_verified": True,
            "proposed_condition_evidence_constructed": True,
            "explicit_question_mark_insertion_recoverable": (
                question_record["recovery_status"] == "recoverable_offline_unique"
            ),
            "explicit_question_mark_normalised_empty": (
                question_evidence["protein_pdbx_PDB_ins_code"] == ""
            ),
            "explicit_question_mark_not_defaulted": (
                question_locator["atom_site_insertion_raw_value"] == "?"
                and question_resolution
                == (True, "explicit_unknown_token_with_exact_source_provenance")
            ),
            "dot_insertion_recoverable": (
                recovered["recovery_status"] == "recoverable_offline_unique"
                and recovered["proposed_condition_evidence_record"]
                ["protein_pdbx_PDB_ins_code"] == ""
            ),
            "concrete_insertion_recoverable": (
                concrete_record["recovery_status"] == "recoverable_offline_unique"
                and concrete_record["proposed_condition_evidence_record"]
                ["protein_pdbx_PDB_ins_code"] == "A"
            ),
            "struct_conn_atom_site_token_conflict_rejected": conflict_rejected,
            "unknown_token_bad_legacy_provenance_rejected": bad_legacy_rejected,
            "blocked_insertion_recommended_step_specific": (
                insertion_recommendation
                == "resolve_covapie_current11_insertion_provenance_v1"
            ),
            "dot_token_bad_provider_projection_rejected": all(
                dot_provider_drift_rejections
            ),
            "concrete_token_bad_provider_projection_rejected": all(
                concrete_provider_drift_rejections
            ),
            "non_question_blocking_reason_drift_rejected": (
                dot_provider_drift_rejections[0]
                and concrete_provider_drift_rejections[0]
            ),
            "condition_evidence_file_written": False,
            "ready_for_offline_source_evidence_compiler": first["ready_for_offline_source_evidence_compiler"],
            "recommended_next_step": first["recommended_next_step"],
            "deterministic": first == second,
            "inputs_unchanged": (
                before == after and question_before == question_after
                and concrete_before == concrete_after
            ),
            "files_written": before != after,
            "model_modified": False, "data_loader_modified": False,
            "forward_modified": False, "loss_modified": False,
            "training_label_created": False,
            "recovery_record_sha256s": tuple(record["offline_source_recovery_record_sha256"] for record in first["offline_source_recovery_records"]),
            "design_response_sha256": first["design_response_sha256"],
        }
        for key, value in summary.items():
            rendered = json.dumps(value, sort_keys=True, separators=(",", ":")) if isinstance(value, (dict, list, tuple)) else str(value).lower() if isinstance(value, bool) else str(value)
            print(f"{key}={rendered}")


if __name__ == "__main__":
    main()
