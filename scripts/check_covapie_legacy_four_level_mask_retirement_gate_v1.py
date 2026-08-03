#!/usr/bin/env python3
"""Check any valid lifecycle state of the CovaPIE R3 retirement gate."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_legacy_four_level_mask_retirement_gate_v1 as gate


def _emit(name: str, value: object) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    print(f"{name}={rendered}")


def _validate_lifecycle_response(response: Mapping[str, object]) -> bool:
    """Validate the exact cross-field claims for one of the three R3 states."""

    profile = response.get("R3_gate_lifecycle_profile")
    commit = response.get("R3_gate_commit")
    claims = (
        response.get("R3_gate_committed"),
        response.get("R3_gate_published"),
        response.get("ready_for_R3_commit_review"),
        response.get("legacy_four_level_full_runtime_retired"),
        response.get("ready_for_repository_cli_forwarding_C1"),
        response.get("recommended_next_step"),
    )
    expected = {
        "r3_precommit_candidate": (
            None,
            (False, False, True, False, False,
             "commit_and_push_covapie_legacy_four_level_mask_retirement_gate_v1"),
        ),
        "r3_committed_unpushed": (
            "commit",
            (True, False, False, True, False,
             "push_covapie_legacy_four_level_mask_retirement_gate_v1"),
        ),
        "r3_published_successor": (
            "commit",
            (True, True, False, True, True, "begin_repository_cli_forwarding_C1"),
        ),
    }
    if (
        type(profile) is not str
        or profile not in expected
        or any(type(claim) is not bool for claim in claims[:5])
        or type(claims[5]) is not str
    ):
        raise ValueError("COVAPIE_LEGACY_FOUR_LEVEL_MASK_RETIREMENT_CHECK_INVALID")
    commit_contract, expected_claims = expected[profile]
    commit_valid = (
        commit is None
        if commit_contract is None
        else type(commit) is str
        and len(commit) == 40
        and all(character in "0123456789abcdef" for character in commit)
    )
    if not commit_valid or claims != expected_claims:
        raise ValueError("COVAPIE_LEGACY_FOUR_LEVEL_MASK_RETIREMENT_CHECK_INVALID")
    return True


def main() -> int:
    first = gate.evaluate_covapie_legacy_four_level_mask_retirement_gate_v1(
        repo_root=ROOT
    )
    second = gate.evaluate_covapie_legacy_four_level_mask_retirement_gate_v1(
        repo_root=ROOT
    )
    assert first == second
    assert tuple(first) == gate.LEGACY_FOUR_LEVEL_MASK_RETIREMENT_GATE_RESPONSE_FIELDS
    assert len(first) == 47
    assert gate._validate_response(first)
    unsigned = {
        field: first[field]
        for field in gate.LEGACY_FOUR_LEVEL_MASK_RETIREMENT_GATE_RESPONSE_FIELDS
        if field != "legacy_four_level_mask_retirement_gate_response_sha256"
    }
    assert first["legacy_four_level_mask_retirement_gate_response_sha256"] == hashlib.sha256(
        gate._canonical_json_bytes(unsigned)
    ).hexdigest()
    assert _validate_lifecycle_response(first)
    assert first["retirement_evidence_passed"] is True
    assert json.loads(gate._canonical_json_bytes(first)) == first

    negative = first["required_negative_runtime_evidence"]
    counts = first["reference_classification_counts"]
    _emit("source_R2_commit_bound", first["source_R2_commit"] == gate._R2_COMMIT)
    _emit("source_R2_exact_ten_path_scope", len(first["source_R2_scope"]) == 10)
    _emit("scan_evidence_mode", first["scan_evidence_mode"])
    _emit("scan_methods_complete", first["scan_methods"] == list(gate._SCAN_METHODS))
    _emit("scanned_tracked_path_count", first["scanned_tracked_path_count"])
    _emit("scanned_python_path_count", first["scanned_python_path_count"])
    _emit("scanned_notebook_path_count", first["scanned_notebook_path_count"])
    _emit("scanned_notebook_code_cell_count", first["scanned_notebook_code_cell_count"])
    _emit("active_legacy_reference_count", first["active_legacy_reference_count"])
    _emit("unresolved_legacy_reference_count", first["unresolved_legacy_reference_count"])
    _emit("retained_read_only_reference_count", first["retained_read_only_reference_count"])
    _emit("historical_read_only_reference_count", counts["historical_read_only"])
    _emit("negative_rejection_evidence_count", counts["negative_rejection_evidence"])
    _emit("design_or_documentation_evidence_count", counts["design_or_documentation_evidence"])
    _emit("gate_control_evidence_count", counts["gate_control_evidence"])
    _emit("legacy_builder_importable", negative["legacy_builder_importable"])
    _emit("legacy_schema_type_present", negative["legacy_schema_type_present"])
    _emit("legacy_cli_flag_present", negative["legacy_cli_flag_present"])
    _emit("legacy_short_token_runtime_input_supported", negative["legacy_short_token_runtime_input_supported"])
    _emit("legacy_dataset_short_key_supported", negative["legacy_dataset_short_key_supported"])
    _emit("canonical_mask_count", first["canonical_mask_count"])
    _emit("canonical_B2_is_scaffold_plus_warhead", first["canonical_B2_semantic"] == "scaffold_plus_warhead")
    _emit("canonical_B3_is_scaffold_only", first["canonical_B3_semantic"] == "scaffold_only")
    _emit("canonical_five_level_runtime_complete", first["canonical_five_level_runtime_complete"])
    _emit("retirement_evidence_passed", first["retirement_evidence_passed"])
    _emit("R3_gate_implemented", first["R3_gate_implemented"])
    _emit("R3_gate_lifecycle_profile", first["R3_gate_lifecycle_profile"])
    _emit("R3_gate_committed", first["R3_gate_committed"])
    _emit("R3_gate_published", first["R3_gate_published"])
    _emit("ready_for_R3_commit_review", first["ready_for_R3_commit_review"])
    _emit("legacy_four_level_full_runtime_retired", first["legacy_four_level_full_runtime_retired"])
    _emit("ready_for_repository_cli_forwarding_C1", first["ready_for_repository_cli_forwarding_C1"])
    _emit("training_or_parameter_update", first["training_or_parameter_update"])
    _emit("feature_semantics_audit_required_before_training", first["feature_semantics_audit_required_before_training"])
    _emit("legacy_four_level_mask_retirement_gate_response_sha256", first["legacy_four_level_mask_retirement_gate_response_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
