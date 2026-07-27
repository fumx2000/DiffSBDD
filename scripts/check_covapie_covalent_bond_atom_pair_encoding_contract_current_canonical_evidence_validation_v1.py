#!/usr/bin/env python3
"""Independently check and optionally materialize atom-pair validation V1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1
    as gate,
)
from covalent_ext import (  # noqa: E402
    covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1 as contract,
)

BASE_COMMIT = gate.BASE_COMMIT
FORMAL_COMMIT_SUBJECT = gate.FORMAL_COMMIT_SUBJECT
EXACT10 = (
    Path("src/covalent_ext/covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1.py"),
    Path("tests/test_covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1.py"),
    Path("scripts/check_covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1.py"),
    Path("docs/covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1_summary.md"),
    *(gate.OUTPUT_ROOT / name for name in gate.OUTPUT_FILES),
)


def _show(path: str) -> bytes:
    subprocess.run(
        ("git", "cat-file", "-e", f"{BASE_COMMIT}:{path}"),
        cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return subprocess.run(
        ("git", "show", f"{BASE_COMMIT}:{path}"),
        cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode(), newline="")))


def _record_from_event(
    event: dict[str, str],
) -> contract.CovalentBondAtomPairCanonicalRecordDesign:
    def locator(prefix: str, role: str):
        return contract.CovalentAtomLocatorContractDesign(
            locator_schema_version=contract.LOCATOR_SCHEMA_VERSION,
            entity_role=role,
            event_id=event["sample_preparation_input_id"],
            pdb_id=event["pdb_id"],
            model_id="",
            auth_asym_id=event[f"{prefix}_auth_asym_id"],
            auth_seq_id=event[f"{prefix}_auth_seq_id"],
            insertion_code="",
            label_asym_id=event[f"{prefix}_label_asym_id"],
            label_seq_id=event[f"{prefix}_label_seq_id"],
            comp_id=event[f"{prefix}_comp_id"],
            atom_name=event[f"{prefix}_atom_name"],
            altloc="",
        )

    assert event["event_status"] == "validated"
    assert event["conn_type_id"] == "covale"
    assert "struct_conn" in event["event_source"] and event["conn_id"]
    return contract.CovalentBondAtomPairCanonicalRecordDesign(
        pair_record_schema_version=contract.PAIR_RECORD_SCHEMA_VERSION,
        residue_atom_locator=locator("residue", "target_residue_atom"),
        ligand_atom_locator=locator("ligand", "ligand_atom"),
        explicit_bond_authority_class="validated_struct_conn",
        explicit_bond_provenance_id=(
            f"{event['sample_preparation_input_id']}:{event['conn_id']}"
        ),
    )


def _independent_evidence_check() -> None:
    index = _rows(_show(gate.FINAL_DATASET_INDEX.as_posix()))
    assert len(index) == 11
    residue_count = ligand_count = site_count = coordinate_count = 0
    legacy_values: set[str] = set()
    exact_indices = []
    for sample in index:
        event_rows = _rows(_show(sample["covalent_event_table_path"]))
        pair_rows = _rows(_show(sample["ligand_residue_atom_pair_table_path"]))
        assert len(event_rows) == len(pair_rows) == 1
        event, pair = event_rows[0], pair_rows[0]
        assert event["sample_preparation_input_id"] == sample["sample_preparation_input_id"]
        assert pair["sample_preparation_input_id"] == sample["sample_preparation_input_id"]
        assert event["pdb_id"] == pair["pdb_id"] == sample["pdb_id"]
        assert event["expected_het_id"] == pair["expected_het_id"] == sample["expected_het_id"]
        record = _record_from_event(event)
        assert contract.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(record)
        legacy = contract.project_covapie_legacy_atom_name_pair_v1(record)
        assert legacy == event["covalent_bond_atom_pair"] == pair["covalent_bond_atom_pair"] == sample["covalent_bond_atom_pair"]
        assert event["event_status"] == "validated"
        assert event["conn_type_id"] == "covale"
        assert "struct_conn" in event["event_source"] and event["conn_id"]
        assert record.explicit_bond_provenance_id == f"{sample['sample_preparation_input_id']}:{event['conn_id']}"
        legacy_values.add(legacy)
        pocket_payloads = [_show(sample["pocket_atom_table_path"]) for _ in range(3)]
        ligand_payloads = [_show(sample["ligand_atom_table_path"]) for _ in range(3)]
        assert pocket_payloads[0] == pocket_payloads[1] == pocket_payloads[2]
        assert ligand_payloads[0] == ligand_payloads[1] == ligand_payloads[2]
        pocket, ligand = _rows(pocket_payloads[0]), _rows(ligand_payloads[0])
        assert len(pocket) == int(sample["pocket_atom_count"])
        assert len(ligand) == int(sample["ligand_atom_count"])
        observation = (
            gate.validate_covapie_covalent_bond_atom_pair_sample_evidence_bundle_v1(
                contract_precondition_verified=True,
                sample_row=sample,
                event_rows=event_rows,
                pair_rows=pair_rows,
                pocket_table_payload=pocket_payloads[0],
                pocket_table_rows=pocket,
                ligand_table_payload=ligand_payloads[0],
                ligand_table_rows=ligand,
                expected_pocket_table_sha256=hashlib.sha256(
                    pocket_payloads[0]
                ).hexdigest(),
                expected_ligand_table_sha256=hashlib.sha256(
                    ligand_payloads[0]
                ).hexdigest(),
                model_index_base=0,
            )
        )
        assert observation.outcome == "validated"
        assert observation.atom_site_crosscheck_valid is True
        assert observation.coordinate_crosscheck_valid is True
        exact_indices.append((
            observation.residue_row_index_0based,
            observation.ligand_row_index_0based,
        ))
        for role, table, locator, site_key, prefix in (
            ("residue", pocket, record.residue_atom_locator, "residue_atom_site_id", "residue"),
            ("ligand", ligand, record.ligand_atom_locator, "ligand_atom_site_id", "ligand"),
        ):
            count, index_0 = gate.validate_covapie_atom_table_locator_exact_one_v1(
                locator, table, expected_het_id=sample["expected_het_id"]
            )
            assert count == 1 and index_0 is not None and 0 <= index_0 < len(table)
            matched = table[index_0]
            assert matched["atom_site_id"] == pair[site_key]
            assert all(Decimal(matched[a]) == Decimal(pair[f"{prefix}_{a}"]) for a in ("x", "y", "z"))
            if role == "residue":
                residue_count += 1
            else:
                ligand_count += 1
        site_count += 1
        coordinate_count += 1
    assert residue_count == ligand_count == site_count == coordinate_count == 11
    assert exact_indices == [
        (88, 3), (25, 3), (19, 3), (39, 3), (37, 27), (50, 21),
        (48, 16), (53, 20), (52, 21), (53, 18), (84, 5),
    ]
    assert legacy_values == {"SG--C17", "SG--C2", "SG--C21", "SG--C22", "SG--C6", "SG--CAG", "SG--CM"}


def _independent_tamper_check() -> None:
    index = _rows(_show(gate.FINAL_DATASET_INDEX.as_posix()))
    sample = index[0]
    event = _rows(_show(sample["covalent_event_table_path"]))[0]
    pair = _rows(_show(sample["ligand_residue_atom_pair_table_path"]))[0]
    record = _record_from_event(event)
    pocket_payload = _show(sample["pocket_atom_table_path"])
    ligand_payload = _show(sample["ligand_atom_table_path"])
    pocket = _rows(pocket_payload)
    ligand = _rows(ligand_payload)
    residue_match = gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.residue_atom_locator, pocket,
        expected_het_id=sample["expected_het_id"],
    )[1]
    ligand_match = gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.ligand_atom_locator, ligand,
        expected_het_id=sample["expected_het_id"],
    )[1]
    assert residue_match is not None and ligand_match is not None
    optional_cases = (
        (replace(record.residue_atom_locator, model_id="1"), pocket),
        (replace(record.residue_atom_locator, altloc="A"), pocket),
        (replace(record.residue_atom_locator, insertion_code="A"), pocket),
        (replace(record.ligand_atom_locator, insertion_code="A"), ligand),
    )
    for locator, rows in optional_cases:
        assert gate.validate_covapie_atom_table_locator_exact_one_v1(
            locator, rows, expected_het_id=sample["expected_het_id"]
        ) == (0, None)
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.residue_atom_locator, pocket[:1],
        expected_het_id=sample["expected_het_id"],
    ) == (0, None)
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.ligand_atom_locator, ligand[:1],
        expected_het_id=sample["expected_het_id"],
    ) == (0, None)
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.residue_atom_locator, pocket + [dict(pocket[residue_match])],
        expected_het_id=sample["expected_het_id"],
    )[1] is None
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.ligand_atom_locator, ligand + [dict(ligand[ligand_match])],
        expected_het_id=sample["expected_het_id"],
    )[1] is None
    assert gate.validate_covapie_atom_table_locator_exact_one_v1(
        record.residue_atom_locator, pocket,
        expected_het_id=sample["expected_het_id"], model_index_base=1,
    ) == (0, None)

    def bundle(**overrides):
        values = {
            "contract_precondition_verified": True,
            "sample_row": deepcopy(sample),
            "event_rows": [deepcopy(event)],
            "pair_rows": [deepcopy(pair)],
            "pocket_table_payload": pocket_payload,
            "pocket_table_rows": deepcopy(pocket),
            "ligand_table_payload": ligand_payload,
            "ligand_table_rows": deepcopy(ligand),
            "expected_pocket_table_sha256": hashlib.sha256(
                pocket_payload
            ).hexdigest(),
            "expected_ligand_table_sha256": hashlib.sha256(
                ligand_payload
            ).hexdigest(),
            "model_index_base": 0,
        }
        values.update(overrides)
        return gate.validate_covapie_covalent_bond_atom_pair_sample_evidence_bundle_v1(
            **values
        )

    assert bundle().outcome == "validated"
    legacy_sample = deepcopy(sample)
    legacy_sample["covalent_bond_atom_pair"] = "SG--TAMPER"
    residue_site_pair = deepcopy(pair)
    residue_site_pair["residue_atom_site_id"] = "TAMPER"
    coordinate_pair = deepcopy(pair)
    coordinate_pair["residue_x"] = "999999"
    row_count_sample = deepcopy(sample)
    row_count_sample["pocket_atom_count"] = str(len(pocket) + 1)
    reversed_rows = list(reversed(deepcopy(pocket)))
    reversed_payload = gate._csv_bytes(tuple(pocket[0]), reversed_rows)
    observations = (
        bundle(sample_row=legacy_sample),
        bundle(pair_rows=[]),
        bundle(pair_rows=[deepcopy(pair), deepcopy(pair)]),
        bundle(pair_rows=[residue_site_pair]),
        bundle(pair_rows=[coordinate_pair]),
        bundle(sample_row=row_count_sample),
        bundle(
            pocket_table_payload=reversed_payload,
            pocket_table_rows=reversed_rows,
        ),
        bundle(
            pocket_table_payload=gate._csv_bytes(tuple(pocket[0]), []),
            pocket_table_rows=[],
        ),
    )
    assert all(
        observation.outcome == "invalid"
        and observation.record_retained is False
        and observation.mapping_retained is False
        for observation in observations
    )
    assert observations[6].source_binding_valid is False
    assert gate._overall_validation_success(
        precondition=True,
        all_canonical=True,
        all_mappings=True,
        row_order_ok=True,
        all_failure_cases_verified=False,
    ) is False


def check() -> dict[str, object]:
    for path, expected_sha in gate.FROZEN_SHA256.items():
        assert hashlib.sha256(_show(path.as_posix())).hexdigest() == expected_sha
    expected = gate.build_covapie_covalent_bond_atom_pair_encoding_contract_validation_artifacts_v1(ROOT)
    for name, payload in expected.items():
        assert (ROOT / gate.OUTPUT_ROOT / name).read_bytes() == payload
    first = gate.derive_covapie_covalent_bond_atom_pair_encoding_contract_validation_v1(ROOT)
    second = gate.derive_covapie_covalent_bond_atom_pair_encoding_contract_validation_v1(ROOT)
    assert gate.serialize_covapie_covalent_bond_atom_pair_encoding_contract_validation_decision_v1(first["decision"]) == gate.serialize_covapie_covalent_bond_atom_pair_encoding_contract_validation_decision_v1(second["decision"])
    assert expected == gate.build_covapie_covalent_bond_atom_pair_encoding_contract_validation_artifacts_v1(ROOT)
    _independent_evidence_check()
    _independent_tamper_check()
    manifest = json.loads(expected[gate.MANIFEST_FILE])
    source_rows = _rows(expected[gate.SOURCE_INVENTORY_FILE])
    assert len(source_rows) == 49
    for row in source_rows:
        payload = _show(row["source_path"])
        assert hashlib.sha256(payload).hexdigest() == row["source_sha256"]
        if row["source_role"] in {"pocket_table", "ligand_table"}:
            assert row["read_count"] == "3"
    assert manifest["validation_outcome"] == "validated"
    assert manifest["encoding_contract_validation_completed"] is True
    assert manifest["current_canonical_record_count"] == 11
    assert manifest["canonical_record_valid_count"] == 11
    assert manifest["exact_one_residue_mapping_count"] == 11
    assert manifest["exact_one_ligand_mapping_count"] == 11
    assert manifest["atom_table_mapping_row_count"] == 22
    assert manifest["pair_table_atom_site_crosscheck_count"] == 11
    assert manifest["pair_table_coordinate_crosscheck_count"] == 11
    assert manifest["failure_matrix_executable"] is True
    assert manifest["failure_matrix_all_cases_verified"] is True
    assert manifest["failure_matrix_required_for_issue_resolution"] is True
    assert manifest["legacy_projection_match_count"] == 11
    assert manifest["explicit_bond_authority_preserved_count"] == 11
    assert manifest["row_index_base"] == 0
    assert manifest["row_order_validation_completed"] is True
    assert manifest["distance_used_for_mapping_selection"] is False
    assert manifest["effective_open_issues"] == ["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]
    assert manifest["canonical_masks"] == [
        {"semantic_name": name, "display_alias": alias} for name, alias in gate.CANONICAL_MASKS
    ]
    failures = _rows(expected[gate.FAILURE_MATRIX_FILE])
    assert tuple(row["failure_case"] for row in failures) == gate.FAILURE_CASES
    assert len(failures) == 27
    assert all(
        row == {
            "failure_case": row["failure_case"],
            "expected_outcome": "invalid",
            "observed_outcome": "invalid",
            "fails_closed": "true",
            "record_retained": "false",
            "mapping_retained": "false",
            "issue_resolved": "false",
            "verified": "true",
        }
        for row in failures
    )
    predecessor_issues = _rows(_show(gate.PREDECESSOR_ISSUES.as_posix()))
    successor_issues = _rows(expected[gate.ISSUE_INVENTORY_FILE])
    assert len(predecessor_issues) == len(successor_issues) == 30
    changed = []
    for old, new in zip(predecessor_issues, successor_issues):
        assert old["issue_id"] == new["issue_id"]
        differences = {key for key in old if old[key] != new[key]}
        if differences:
            changed.append((old["issue_id"], differences))
    assert changed == [(
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        {
            "successor_effective_status", "successor_transition_stage",
            "successor_transition_action", "successor_transition_evidence",
        },
    )]
    assert [
        row["issue_id"] for row in successor_issues
        if row["successor_effective_status"] == "open"
    ] == ["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]
    for name, expected_sha in manifest["evidence_sha256"].items():
        assert hashlib.sha256(expected[name]).hexdigest() == expected_sha
    assert all(not manifest[key] for key in (
        "ready_for_tensorization", "pair_tensor_shape_defined",
        "negative_pair_construction_defined", "negative_sampling_defined",
        "pair_loss_mask_defined", "pair_head_implemented",
        "pair_contrastive_loss_implemented", "provider_used", "download_used",
        "raw_read", "raw_write", "checkpoint_access", "model_changed",
        "dataloader_changed", "forward_changed", "loss_changed", "training_used",
        "feature_semantics_audit_completed", "feature_semantics_known",
        "unknown_atom_feature_policy_resolved", "ready_for_training",
    ))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        artifacts = gate.build_covapie_covalent_bond_atom_pair_encoding_contract_validation_artifacts_v1(ROOT)
        output = ROOT / gate.OUTPUT_ROOT
        output.mkdir(parents=True, exist_ok=True)
        existing = {path.name for path in output.iterdir()}
        assert existing <= set(gate.OUTPUT_FILES)
        for name, payload in artifacts.items():
            (output / name).write_bytes(payload)
    manifest = check()
    for key in (
        "validation_outcome", "encoding_contract_validation_completed",
        "current_canonical_record_count", "canonical_record_valid_count",
        "exact_one_residue_mapping_count", "exact_one_ligand_mapping_count",
        "atom_table_mapping_row_count", "pair_table_atom_site_crosscheck_count",
        "pair_table_coordinate_crosscheck_count",
        "failure_matrix_executable", "failure_matrix_all_cases_verified",
        "failure_matrix_required_for_issue_resolution",
        "legacy_projection_match_count", "explicit_bond_authority_preserved_count",
        "row_index_base", "row_order_validation_completed",
        "distance_used_for_mapping_selection", "atom_pair_issue_resolved",
        "provider_issue_resolved", "effective_open_issue_count",
        "atom_pair_ready_for_downstream_contracts",
        "next_training_preparation_blocker", "ready_for_tensorization",
        "feature_semantics_audit_completed", "ready_for_training",
    ):
        value = manifest[key]
        if isinstance(value, bool):
            value = str(value).lower()
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
