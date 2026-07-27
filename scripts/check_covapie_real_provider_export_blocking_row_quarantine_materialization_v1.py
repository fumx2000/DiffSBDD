from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

from covalent_ext import (
    covapie_real_provider_export_blocking_row_quarantine_materialization_v1
    as gate,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / gate.OUTPUT_ROOT
EXACT10 = (
    Path(
        "src/covalent_ext/covapie_real_provider_export_blocking_row_"
        "quarantine_materialization_v1.py"
    ),
    Path(
        "tests/test_covapie_real_provider_export_blocking_row_"
        "quarantine_materialization_v1.py"
    ),
    Path(
        "scripts/check_covapie_real_provider_export_blocking_row_"
        "quarantine_materialization_v1.py"
    ),
    Path(
        "docs/covapie_real_provider_export_blocking_row_"
        "quarantine_materialization_v1_summary.md"
    ),
    gate.OUTPUT_ROOT / gate.SOURCE_INVENTORY_FILE,
    gate.OUTPUT_ROOT / gate.QUARANTINE_INVENTORY_FILE,
    gate.OUTPUT_ROOT / gate.EXCLUSION_MATRIX_FILE,
    gate.OUTPUT_ROOT / gate.FAILURE_MATRIX_FILE,
    gate.OUTPUT_ROOT / gate.ISSUE_INVENTORY_FILE,
    gate.OUTPUT_ROOT / gate.MANIFEST_FILE,
)
_SHA_RE = re.compile(r"[0-9a-f]{64}", re.ASCII)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _base(path: Path) -> bytes:
    if path.parts[:2] == ("data", "raw"):
        raise AssertionError("raw reads are forbidden")
    spec = f"{gate.BASE_COMMIT}:{path.as_posix()}"
    subprocess.run(
        ("git", "cat-file", "-e", spec), cwd=ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return subprocess.run(
        ("git", "show", spec), cwd=ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def _rows(payload: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode(), newline=""))
    assert reader.fieldnames is not None
    assert len(reader.fieldnames) == len(set(reader.fieldnames))
    return [dict(row) for row in reader]


def _keyed(
    rows: list[dict[str, str]], key: str
) -> dict[str, dict[str, str]]:
    result = {}
    for row in rows:
        value = row[key]
        assert value and value not in result
        result[value] = row
    return result


def _read_outputs() -> dict[str, bytes]:
    return {
        name: (OUTPUT_ROOT / name).read_bytes() for name in gate.OUTPUT_FILES
    }


def _independent_expected_quarantine_row(
    index: int,
    audit: dict[str, str],
    provider: dict[str, str],
) -> dict[str, object]:
    identity = f"REAL_LOCATOR_BINDING_{index:06d}"
    assert audit["blocking_row_identity"] == identity
    assert audit["provider_export_row_identity"] == identity
    assert provider["binding_row_id"] == identity
    assert audit["observed_insertion_code_state"] == provider[
        "covalent_residue_insertion_code_state"
    ]
    assert audit["observed_insertion_code"] == provider[
        "covalent_residue_insertion_code"
    ]
    values = (
        str(index),
        f"REAL_PROVIDER_EXPORT_QUARANTINE_{index:06d}",
        identity,
        identity,
        audit["candidate_identity"],
        audit["pdb_id"],
        audit["ligand_identity"],
        audit["residue_name"],
        audit["residue_chain_or_asym_id"],
        audit["residue_sequence_id"],
        audit["observed_insertion_code_state"],
        audit["observed_insertion_code"],
        "ADMIT_004",
        "blocked",
        gate.UNKNOWN_REASON,
        gate.AUDIT_DISPOSITION,
        audit["audit_reason"],
        gate.QUARANTINE_STATUS,
        provider["provider_export_status"],
        gate.PROVIDER_SIDECAR.as_posix(),
        gate.FROZEN_SHA256[gate.PROVIDER_SIDECAR],
        f"binding_row_id={identity}",
        provider["covalent_residue_locator_provenance_source_id"],
        provider["covalent_residue_locator_provenance_sha256"],
        "false", "false", "true", "false", "false", "false", "false",
        "false", "true",
    )
    row = dict(zip(gate.QUARANTINE_COLUMNS, values, strict=True))
    assert tuple(row) == gate.QUARANTINE_COLUMNS
    assert all(type(value) is str for value in row.values())
    return row


def _independent_expected_exclusion_row(
    quarantine: dict[str, str], scope: str
) -> dict[str, str]:
    values = (
        quarantine["quarantine_id"],
        quarantine["blocking_row_identity"],
        quarantine["candidate_identity"],
        scope,
        "false",
        "false",
        gate.EXCLUSION_REASON,
        gate.QUARANTINE_STATUS,
        "true",
        "true",
    )
    row = dict(zip(gate.EXCLUSION_COLUMNS, values, strict=True))
    assert tuple(row) == gate.EXCLUSION_COLUMNS
    assert all(type(value) is str for value in row.values())
    return row


def _verify_base_and_sources(outputs: dict[str, bytes]) -> None:
    shown = subprocess.run(
        (
            "git", "show", "-s", "--format=%H%n%P%n%T%n%s",
            gate.BASE_COMMIT,
        ),
        cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE,
    ).stdout.splitlines()
    assert shown == [
        gate.BASE_COMMIT, gate.BASE_PARENT, gate.BASE_TREE, gate.BASE_SUBJECT
    ]
    base_payloads = {}
    for path, digest in gate.FROZEN_SHA256.items():
        payload = _base(path)
        assert _sha(payload) == digest
        base_payloads[path] = payload
    sources = _rows(outputs[gate.SOURCE_INVENTORY_FILE])
    assert len(sources) == 12
    assert [row["source_role"] for row in sources] == [
        role for role, _, _ in gate.SOURCE_ROLES
    ]
    for row in sources:
        path = Path(row["source_path"])
        assert row["source_sha256"] == _sha(base_payloads[path])
        assert row["committed_in_base"] == "true"
        assert row["verified"] == "true"
        assert not row["source_path"].startswith("data/raw/")


def _verify_scope_and_reconstruct_rows(outputs: dict[str, bytes]) -> None:
    final_rows = _rows(_base(gate.FINAL_DATASET_INDEX))
    atom_pair = json.loads(_base(gate.ATOM_PAIR_MANIFEST))
    assert len(final_rows) == 11
    assert atom_pair["validation_outcome"] == "validated"
    assert atom_pair["current_canonical_record_count"] == 11
    assert atom_pair["canonical_record_valid_count"] == 11
    assert atom_pair["atom_pair_issue_resolved"] is True
    assert atom_pair["provider_issue_resolved"] is False
    assert atom_pair["effective_open_issues"] == [gate.ISSUE_ID]

    audits = _rows(_base(gate.POLICY_BLOCKING_MATRIX))
    sidecars = _keyed(_rows(_base(gate.PROVIDER_SIDECAR)), "binding_row_id")
    quarantines = _rows(outputs[gate.QUARANTINE_INVENTORY_FILE])
    assert len(audits) == len(sidecars) == len(quarantines) == 11
    for index, (audit, quarantine) in enumerate(zip(audits, quarantines), 1):
        identity = f"REAL_LOCATOR_BINDING_{index:06d}"
        quarantine_id = f"REAL_PROVIDER_EXPORT_QUARANTINE_{index:06d}"
        source = sidecars[identity]
        assert audit["blocking_row_identity"] == identity
        assert audit["audit_disposition"] == gate.AUDIT_DISPOSITION
        assert audit["admit_004_outcome"] == "blocked"
        assert audit["admit_004_reason"] == gate.UNKNOWN_REASON
        assert audit["source_selector"] == f"binding_row_id={identity}"
        assert audit["source_sha256"] == gate.FROZEN_SHA256[
            gate.PROVIDER_SIDECAR
        ]
        assert source["provider_export_status"] == "exported_blocking"
        assert source["covalent_residue_insertion_code_state"] == "unknown"
        assert source["covalent_residue_insertion_code"] == ""
        assert source["insertion_blocks_admit_004"] == "true"
        assert source["insertion_blocking_reason"] == gate.UNKNOWN_REASON
        assert quarantine["quarantine_id"] == quarantine_id
        assert quarantine["blocking_row_identity"] == identity
        assert quarantine["candidate_identity"] == audit["candidate_identity"]
        assert quarantine["observed_insertion_code_state"] == "unknown"
        assert quarantine["observed_insertion_code"] == ""
        assert quarantine["admit_004_outcome"] == "blocked"
        assert quarantine["audit_disposition"] == gate.AUDIT_DISPOSITION
        assert quarantine["quarantine_status"] == gate.QUARANTINE_STATUS
        assert quarantine["original_provider_row_selector"] == (
            f"binding_row_id={identity}"
        )
        assert quarantine["original_provider_row_source_sha256"] == (
            gate.FROZEN_SHA256[gate.PROVIDER_SIDECAR]
        )
        assert quarantine["provider_provenance_source_id"] == source[
            "covalent_residue_locator_provenance_source_id"
        ]
        assert quarantine["provider_provenance_sha256"] == source[
            "covalent_residue_locator_provenance_sha256"
        ]
        assert quarantine == _independent_expected_quarantine_row(
            index, audit, source
        )
        assert tuple(quarantine) == gate.QUARANTINE_COLUMNS
        assert _SHA_RE.fullmatch(quarantine["provider_provenance_sha256"])
        for field, expected in (
            ("provider_row_mutated", "false"),
            ("provider_value_resolved", "false"),
            ("provider_reexport_required", "true"),
            ("provider_admitted_membership", "false"),
            ("provider_passed_membership", "false"),
            ("future_canonical_materialization_membership", "false"),
            ("tensorization_membership", "false"),
            ("training_membership", "false"),
            ("verified", "true"),
        ):
            assert quarantine[field] == expected

    exclusions = _rows(outputs[gate.EXCLUSION_MATRIX_FILE])
    expected_pairs = {
        (f"REAL_PROVIDER_EXPORT_QUARANTINE_{index:06d}", scope)
        for index in range(1, 12)
        for scope in gate.EXCLUSION_SCOPES
    }
    assert len(exclusions) == 55
    assert {
        (row["quarantine_id"], row["exclusion_scope"]) for row in exclusions
    } == expected_pairs
    quarantine_map = {
        row["quarantine_id"]: row for row in quarantines
    }
    for row in exclusions:
        assert row == _independent_expected_exclusion_row(
            quarantine_map[row["quarantine_id"]], row["exclusion_scope"]
        )
        assert tuple(row) == gate.EXCLUSION_COLUMNS
        assert row["expected_membership"] == "false"
        assert row["observed_membership"] == "false"
        assert row["source_quarantine_status"] == gate.QUARANTINE_STATUS
        assert row["fails_closed"] == row["verified"] == "true"


def _verify_failures_and_issues(outputs: dict[str, bytes]) -> None:
    baseline = gate._baseline_state(ROOT)
    assert gate._quarantine_inventory_exact_schema_valid(
        baseline["quarantine_rows"]
    )
    assert gate._quarantine_inventory_exact_types_valid(
        baseline["quarantine_rows"]
    )
    assert gate._exclusion_inventory_exact_schema_valid(
        baseline["exclusion_rows"]
    )
    assert gate._exclusion_inventory_exact_types_valid(
        baseline["exclusion_rows"]
    )
    assert gate._provider_issue_effective_status(
        baseline["candidate_issue_rows"]
    ) == "open"
    assert baseline["candidate_issue_rows"] == baseline[
        "predecessor_issue_rows"
    ]
    assert gate._core_materialization_valid(baseline) is False
    baseline["failure_matrix_complete"] = True
    assert gate._core_materialization_valid(baseline) is True
    success_evaluation = gate._materialization_evaluation(baseline)
    assert success_evaluation["core_materialization_valid"] is True
    assert success_evaluation["provider_issue_transition_applied"] is True
    assert success_evaluation["provider_issue_effective_status"] == "resolved"
    rejected = gate._apply_provider_issue_transition_after_success_v1(
        baseline["predecessor_issue_rows"], materialization_success=False
    )
    assert rejected == baseline["predecessor_issue_rows"]
    assert gate._provider_issue_effective_status(rejected) == "open"

    failures = _rows(outputs[gate.FAILURE_MATRIX_FILE])
    assert [row["failure_case"] for row in failures] == list(
        gate.FAILURE_CASES
    )
    assert len(failures) == 36
    for row in failures:
        observed = (
            gate.evaluate_covapie_real_provider_export_quarantine_failure_case_v1(
                ROOT, row["failure_case"]
            )
        )
        assert observed.outcome == row["observed_outcome"] == "invalid"
        assert observed.failure_detected is True
        assert observed.provider_issue_transition_applied is False
        assert observed.provider_issue_effective_status == "open"
        assert observed.ready_for_feature_semantics_audit is False
        assert observed.ready_for_tensorization is False
        assert observed.ready_for_training is False
        assert row["failure_detected"] == "true"
        assert row["candidate_quarantine_registry_valid"] == (
            "true"
            if observed.candidate_quarantine_registry_valid
            else "false"
        )
        assert row["candidate_exclusion_registry_valid"] == (
            "true"
            if observed.candidate_exclusion_registry_valid
            else "false"
        )
        assert row["provider_issue_transition_applied"] == "false"
        assert row["provider_issue_effective_status"] == "open"
        assert row["ready_for_feature_semantics_audit"] == "false"
        assert row["ready_for_tensorization"] == "false"
        assert row["ready_for_training"] == "false"
        assert row["fails_closed"] == "true"
        assert row["verified"] == "true"
        tampered = gate._baseline_state(ROOT)
        tampered["failure_matrix_complete"] = True
        gate._apply_failure_case(tampered, row["failure_case"])
        assert gate._candidate_quarantine_registry_valid(tampered) is (
            observed.candidate_quarantine_registry_valid
        )
        assert gate._candidate_exclusion_registry_valid(tampered) is (
            observed.candidate_exclusion_registry_valid
        )

    expected_validity = {
        "missing_quarantine_row": (False, False),
        "duplicate_quarantine_id": (False, False),
        "provider_issue_resolved_before_exact11_quarantine": (False, False),
        "provider_issue_resolved_before_exact55_exclusions": (True, False),
        "predecessor_sha_drift": (True, True),
        "provider_admitted_membership_true": (False, False),
        "quarantine_provider_export_identity_mismatch": (False, False),
        "quarantine_pdb_or_ligand_projection_mismatch": (False, False),
        "quarantine_residue_projection_mismatch": (False, False),
        "quarantine_insertion_state_or_code_mismatch": (False, False),
        "quarantine_admit_004_projection_mismatch": (False, False),
        "quarantine_reason_mismatch": (False, False),
        "exclusion_reason_mismatch": (True, False),
    }
    failure_map = {row["failure_case"]: row for row in failures}
    for case, (quarantine_valid, exclusion_valid) in expected_validity.items():
        assert failure_map[case]["candidate_quarantine_registry_valid"] == (
            "true" if quarantine_valid else "false"
        )
        assert failure_map[case]["candidate_exclusion_registry_valid"] == (
            "true" if exclusion_valid else "false"
        )
    for case in (
        "provider_issue_resolved_before_exact11_quarantine",
        "provider_issue_resolved_before_exact55_exclusions",
    ):
        tampered = gate._baseline_state(ROOT)
        tampered["failure_matrix_complete"] = True
        gate._apply_failure_case(tampered, case)
        assert gate._provider_issue_effective_status(
            tampered["candidate_issue_rows"]
        ) == "resolved"
        evaluation = gate._materialization_evaluation(tampered)
        assert evaluation["provider_issue_transition_applied"] is False
        assert evaluation["provider_issue_effective_status"] == "open"
        assert evaluation["issue_rows"] == tampered["predecessor_issue_rows"]

    for field in (
        "provider_export_row_identity", "pdb_id", "ligand_identity",
        "residue_name", "residue_chain_or_asym_id", "residue_sequence_id",
        "observed_insertion_code_state", "observed_insertion_code",
        "admission_rule_id", "admit_004_outcome", "admit_004_reason",
        "quarantine_reason",
    ):
        tampered = gate._baseline_state(ROOT)
        tampered["failure_matrix_complete"] = True
        tampered["quarantine_rows"][0][field] = "TAMPERED"
        assert gate._candidate_quarantine_registry_valid(tampered) is False
        assert gate._candidate_exclusion_registry_valid(tampered) is False
        evaluation = gate._materialization_evaluation(tampered)
        assert evaluation["provider_issue_transition_applied"] is False
        assert evaluation["provider_issue_effective_status"] == "open"
    tampered = gate._baseline_state(ROOT)
    tampered["failure_matrix_complete"] = True
    tampered["exclusion_rows"][0]["exclusion_reason"] = "TAMPERED"
    assert gate._candidate_quarantine_registry_valid(tampered) is True
    assert gate._candidate_exclusion_registry_valid(tampered) is False
    evaluation = gate._materialization_evaluation(tampered)
    assert evaluation["provider_issue_transition_applied"] is False
    assert evaluation["provider_issue_effective_status"] == "open"

    predecessor = _keyed(_rows(_base(gate.POLICY_ISSUES)), "issue_id")
    current = _keyed(_rows(outputs[gate.ISSUE_INVENTORY_FILE]), "issue_id")
    transition_fields = {
        "successor_effective_status", "successor_transition_stage",
        "successor_transition_action", "successor_transition_evidence",
    }
    assert set(current) == set(predecessor)
    for issue_id, original in predecessor.items():
        changed = {
            key for key in original if original[key] != current[issue_id][key]
        }
        assert changed == (
            transition_fields if issue_id == gate.ISSUE_ID else set()
        )
    provider = current[gate.ISSUE_ID]
    assert provider["successor_effective_status"] == "resolved"
    assert provider["successor_transition_stage"] == gate.STAGE
    assert provider["successor_transition_action"] == (
        "resolved_by_fail_closed_quarantine_containment_v1"
    )
    assert current[gate.ATOM_PAIR_ISSUE_ID] == predecessor[
        gate.ATOM_PAIR_ISSUE_ID
    ]
    assert current[gate.ATOM_PAIR_ISSUE_ID][
        "successor_effective_status"
    ] == "resolved"


def _verify_manifest_and_determinism(outputs: dict[str, bytes]) -> dict:
    expected = (
        gate.build_covapie_real_provider_export_blocking_row_quarantine_materialization_artifacts_v1(
            ROOT
        )
    )
    assert outputs == expected
    assert expected == (
        gate.build_covapie_real_provider_export_blocking_row_quarantine_materialization_artifacts_v1(
            ROOT
        )
    )
    manifest = json.loads(outputs[gate.MANIFEST_FILE])
    required = {
        "materialization_outcome": "materialized",
        "quarantine_scope": "real_provider_export_ingestion_path_only",
        "quarantine_scope_compatible": True,
        "blocking_row_count": 11,
        "quarantine_row_count": 11,
        "unique_quarantine_row_count": 11,
        "quarantine_exclusion_matrix_row_count": 55,
        "quarantine_inventory_full_field_projection_verified": True,
        "quarantine_inventory_exact_schema_verified": True,
        "quarantine_inventory_exact_types_verified": True,
        "exclusion_inventory_full_field_projection_verified": True,
        "exclusion_inventory_exact_schema_verified": True,
        "exclusion_inventory_exact_types_verified": True,
        "source_provenance_preserved_count": 11,
        "provider_admitted_exclusion_count": 11,
        "provider_passed_exclusion_count": 11,
        "future_canonical_exclusion_count": 11,
        "tensorization_exclusion_count": 11,
        "training_exclusion_count": 11,
        "provider_rows_mutated": False,
        "provider_rows_present": True,
        "provider_rows_quarantined": True,
        "provider_values_resolved": False,
        "provider_reexport_still_required": True,
        "existing_final_dataset_modified": False,
        "atom_pair_validation_artifacts_modified": False,
        "provider_blocking_effect_contained": True,
        "provider_issue_resolved": True,
        "prevalidation_provider_issue_effective_status": "open",
        "provider_issue_transition_applied_after_validation": True,
        "provider_issue_transition_preconditions_verified": True,
        "provider_issue_transition_applied_exactly_once": True,
        "provider_issue_transition_changed_field_count": 4,
        "failure_observation_semantics_truthful": True,
        "failure_matrix_uses_actual_registry_validity": True,
        "invalid_candidate_provider_issue_effective_status": "open",
        "failure_matrix_required_for_issue_resolution": True,
        "effective_open_issue_count": 0,
        "effective_open_issues": [],
        "atom_pair_issue_resolved": True,
        "ready_for_feature_semantics_audit": True,
        "ready_for_tensorization": False,
        "feature_semantics_audit_completed": False,
        "ready_for_training": False,
        "failure_matrix_row_count": 36,
        "recommended_next_step": gate.RECOMMENDED_NEXT_STEP,
    }
    for key, value in required.items():
        assert manifest[key] == value
    for name, digest in manifest["evidence_sha256"].items():
        assert _sha(outputs[name]) == digest
    assert gate.MANIFEST_FILE not in manifest["evidence_sha256"]
    assert manifest["canonical_masks"] == [
        {"semantic_name": name, "display_alias": alias}
        for name, alias in gate.CANONICAL_MASKS
    ]
    return manifest


def main() -> None:
    outputs = _read_outputs()
    _verify_base_and_sources(outputs)
    _verify_scope_and_reconstruct_rows(outputs)
    _verify_failures_and_issues(outputs)
    manifest = _verify_manifest_and_determinism(outputs)
    lines = (
        f"materialization_outcome={manifest['materialization_outcome']}",
        "quarantine_scope_compatible=true",
        f"blocking_row_count={manifest['blocking_row_count']}",
        f"quarantine_row_count={manifest['quarantine_row_count']}",
        f"unique_quarantine_row_count={manifest['unique_quarantine_row_count']}",
        "quarantine_inventory_full_field_projection_verified=true",
        "quarantine_inventory_exact_schema_verified=true",
        "quarantine_inventory_exact_types_verified=true",
        "quarantine_exclusion_matrix_row_count="
        f"{manifest['quarantine_exclusion_matrix_row_count']}",
        "exclusion_inventory_full_field_projection_verified=true",
        "exclusion_inventory_exact_schema_verified=true",
        "exclusion_inventory_exact_types_verified=true",
        f"failure_matrix_row_count={manifest['failure_matrix_row_count']}",
        "source_provenance_preserved_count="
        f"{manifest['source_provenance_preserved_count']}",
        "provider_admitted_exclusion_count="
        f"{manifest['provider_admitted_exclusion_count']}",
        "provider_passed_exclusion_count="
        f"{manifest['provider_passed_exclusion_count']}",
        "future_canonical_exclusion_count="
        f"{manifest['future_canonical_exclusion_count']}",
        "tensorization_exclusion_count="
        f"{manifest['tensorization_exclusion_count']}",
        f"training_exclusion_count={manifest['training_exclusion_count']}",
        "provider_rows_mutated=false",
        "provider_values_resolved=false",
        "provider_reexport_still_required=true",
        "provider_blocking_effect_contained=true",
        "provider_issue_resolved=true",
        "prevalidation_provider_issue_effective_status=open",
        "provider_issue_transition_applied_after_validation=true",
        "failure_observation_semantics_truthful=true",
        "effective_open_issue_count=0",
        "atom_pair_issue_resolved=true",
        "ready_for_feature_semantics_audit=true",
        "ready_for_tensorization=false",
        "feature_semantics_audit_completed=false",
        "ready_for_training=false",
        "failure_matrix_sha256="
        f"{_sha(outputs[gate.FAILURE_MATRIX_FILE])}",
        f"manifest_sha256={_sha(outputs[gate.MANIFEST_FILE])}",
        f"recommended_next_step={gate.RECOMMENDED_NEXT_STEP}",
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
