#!/usr/bin/env python3
"""Check Step14AU-E1-E4 Phase 3 output evidence directly."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate
    as gate,
)


EXPECTED_OUTPUT_SHA256 = {
    gate.CONTRACT_FILENAME: "91e23f622b1c5109110a7f3f7b1fc0ebe68a7e718600df2b87851843be51c4e8",
    gate.REASON_FILENAME: "62392a4026f07ef3c6fb94832f45451d6437e001959b5140229c20150f34e707",
    gate.ROUTING_FILENAME: "be79b98c695d989f27c694aab3d460990fea735ee8308b620eb6d10a98b3b757",
    gate.SAFETY_FILENAME: "50231b751f75e16b1f9bc6ccb8484800786f52ccd2c34b8e319f170ff18a3ac7",
    gate.ISSUE_FILENAME: "4a7465b6ec0550635578ef9e65cafd49467448e2fdfd3fe49889318b08f5421e",
    gate.MANIFEST_FILENAME: "32dd20579fb47aae0deb1e074fc8feeff5b92b8cbdd44b4089c7ef15a590a754",
}

EXPECTED_CONTRACT_COLUMNS = (
    "admission_rule_id", "admission_rule_name", "legacy_callable_name",
    "legacy_callable_parameters", "legacy_result_exact_type",
    "legacy_result_key_order", "legacy_exact_string_fields", "adapter_id",
    "candidate_field", "runtime_batch_item", "allowed_outcomes",
    "normalized_values_contract", "validated_candidate_fields_contract",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
    "input_form_contract", "source_type_failure_reason",
    "source_invariant_failure_reason", "unknown_reason_failure_reason",
    "legacy_value_invariant_contract", "semantic_oracle_callable",
    "semantic_oracle_parameters", "expected_legacy_result_projection",
    "legacy_result_oracle_equivalence_required",
    "adapter_side_invalid_result_contract",
    "malformed_result_disposition", "unknown_reason_disposition",
    "adapter_implemented", "registered_in_engine", "contract_passed",
)
EXPECTED_ROUTING_COLUMNS = (
    "admission_rule_id", "contract_order", "contract_area", "contract_item",
    "exact_requirement", "failure_disposition", "dispatch_error_reason",
    "legacy_evaluator_called_on_failure", "contract_passed",
)
EXPECTED_EXECUTION_PRECEDENCE = (
    "1:rule-ID validation|2:known/registered/adapter-ready validation|"
    "3:runtime context routing validation|4:candidate Mapping validation|"
    "5:required candidate-field validation|6:legacy evaluator call|"
    "7:exact legacy-result type/key/field validation|"
    "8:legacy-result semantic invariant and semantic-oracle equivalence validation|"
    "9:reason-to-outcome mapping|"
    "10:UnifiedAdmissionRuleEvaluation construction"
)
EXPECTED_CONTEXT_ERROR_REASONS = {
    ("ADMIT_001", "batch_context_1_mapping"): "ADMIT_001_BATCH_CONTEXT_MAPPING_REQUIRED",
    ("ADMIT_001", "batch_context_2_key_presence"): "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_REQUIRED",
    ("ADMIT_001", "batch_context_3_exact_container"): "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_EXACT_LIST_OR_TUPLE_REQUIRED",
    ("ADMIT_001", "batch_context_4_nonempty"): "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_NONEMPTY_REQUIRED",
    ("ADMIT_001", "batch_context_5_member_syntax"): "ADMIT_001_BATCH_CANDIDATE_RECORD_ID_MEMBER_INVALID",
    ("ADMIT_001", "evaluation_context_6"): "ADMIT_001_EVALUATION_CONTEXT_MUST_BE_NONE",
    ("ADMIT_001", "download_result_context_7"): "ADMIT_001_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    ("ADMIT_001", "stage_authorization_context_8"): "ADMIT_001_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
    ("ADMIT_002", "batch_context_1"): "ADMIT_002_BATCH_CONTEXT_MUST_BE_NONE",
    ("ADMIT_002", "evaluation_context_2"): "ADMIT_002_EVALUATION_CONTEXT_MUST_BE_NONE",
    ("ADMIT_002", "download_result_context_3"): "ADMIT_002_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    ("ADMIT_002", "stage_authorization_context_4"): "ADMIT_002_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
    ("ADMIT_003", "batch_context_1"): "ADMIT_003_BATCH_CONTEXT_MUST_BE_NONE",
    ("ADMIT_003", "evaluation_context_2"): "ADMIT_003_EVALUATION_CONTEXT_MUST_BE_NONE",
    ("ADMIT_003", "download_result_context_3"): "ADMIT_003_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    ("ADMIT_003", "stage_authorization_context_4"): "ADMIT_003_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
EXPECTED_ADAPTER_FAILURE_REASONS = {
    "ADMIT_001": (
        "ADMIT_001_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        "ADMIT_001_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        "ADMIT_001_UNIFIED_ADAPTER_REASON_UNMAPPED",
    ),
    "ADMIT_002": (
        "ADMIT_002_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        "ADMIT_002_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        "ADMIT_002_UNIFIED_ADAPTER_REASON_UNMAPPED",
    ),
    "ADMIT_003": (
        "ADMIT_003_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        "ADMIT_003_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        "ADMIT_003_UNIFIED_ADAPTER_REASON_UNMAPPED",
    ),
}
EXPECTED_SEMANTIC_ORACLE_CONTRACTS = {
    "ADMIT_001": (
        "evaluate_candidate_record_id_batch_uniqueness",
        "candidate_record_id|batch_candidate_record_ids",
        "admission_rule_id=ADMIT_001;passed=oracle.passed;"
        "normalized_candidate_record_id=oracle.canonical_candidate_record_id;"
        "blocking_reason=oracle.blocking_reason",
    ),
    "ADMIT_002": (
        "normalize_pdb_identifier",
        "pdb_id",
        "admission_rule_id=ADMIT_002;passed=oracle.syntax_valid;"
        "canonical_pdb_id=oracle.canonical_pdb_id;input_form=oracle.input_form;"
        "blocking_reason=oracle.blocking_reason",
    ),
    "ADMIT_003": (
        "normalize_ligand_comp_id",
        "ligand_comp_id",
        "admission_rule_id=ADMIT_003;passed=oracle.passed;"
        "canonical_ligand_comp_id=oracle.canonical_ligand_comp_id;"
        "blocking_reason=oracle.blocking_reason",
    ),
}
EXPECTED_TUPLE_TEXT = {
    "ADMIT_001": ('("candidate_record_id",)', '("batch_candidate_record_ids",)'),
    "ADMIT_002": ('("pdb_id",)', "()"),
    "ADMIT_003": ('("ligand_comp_id",)', "()"),
}
EXPECTED_INVALID_PAYLOAD_SPECS = {
    "ADMIT_001": (
        "unique_candidate_identity", "candidate_record_id",
        '("batch_candidate_record_ids",)', "covapie_admit_001_unified_adapter_v1",
        "ADMIT_001_CANDIDATE_RECORD_MAPPING_INVALID",
        "ADMIT_001_CANDIDATE_FIELD_MISSING:candidate_record_id",
    ),
    "ADMIT_002": (
        "valid_pdb_id_format", "pdb_id", "()",
        "covapie_admit_002_unified_adapter_v1",
        "ADMIT_002_CANDIDATE_RECORD_MAPPING_INVALID",
        "ADMIT_002_CANDIDATE_FIELD_MISSING:pdb_id",
    ),
    "ADMIT_003": (
        "ligand_or_het_identity_present", "ligand_comp_id", "()",
        "covapie_admit_003_unified_adapter_v1",
        "ADMIT_003_CANDIDATE_RECORD_MAPPING_INVALID",
        "ADMIT_003_CANDIDATE_FIELD_MISSING:ligand_comp_id",
    ),
}
EXPECTED_REASON_SPECS = {
    "ADMIT_001": (
        ("", "passed"),
        ("candidate_record_id_not_exact_str", "invalid"),
        ("candidate_record_id_empty", "invalid"),
        ("candidate_record_id_non_ascii", "invalid"),
        ("candidate_record_id_length_out_of_range", "invalid"),
        ("candidate_record_id_pattern_invalid", "invalid"),
        ("candidate_record_id_missing_from_batch", "blocked"),
        ("candidate_record_id_repeated_in_batch", "blocked"),
        ("batch_candidate_record_ids_not_globally_unique", "blocked"),
    ),
    "ADMIT_002": (
        ("", "passed"), ("pdb_id_missing", "invalid"),
        ("pdb_id_not_string", "invalid"), ("pdb_id_empty", "invalid"),
        ("pdb_id_surrounding_whitespace_forbidden", "invalid"),
        ("pdb_id_non_ascii_forbidden", "invalid"),
        ("pdb_id_format_invalid", "invalid"),
        ("pdb_id_length_invalid", "invalid"),
    ),
    "ADMIT_003": (
        ("", "passed"), ("LIGAND_COMP_ID_TYPE_INVALID", "invalid"),
        ("LIGAND_COMP_ID_EMPTY", "invalid"),
        ("LIGAND_COMP_ID_NON_ASCII", "invalid"),
        ("LIGAND_COMP_ID_LENGTH_INVALID", "invalid"),
        ("LIGAND_COMP_ID_SYNTAX_INVALID", "invalid"),
    ),
}
EXPECTED_INVARIANT_FRAGMENTS = {
    "ADMIT_001": (
        "admission_rule_id exact ADMIT_001",
        "legacy passed exact bool and equals (mapped outcome == passed)",
        "passed=>reason empty",
        "normalized_candidate_record_id nonempty exact str and equals original candidate_record_id",
        "candidate_record_id_missing_from_batch|candidate_record_id_repeated_in_batch|batch_candidate_record_ids_not_globally_unique",
        "candidate_record_id_not_exact_str|candidate_record_id_empty|candidate_record_id_non_ascii|candidate_record_id_length_out_of_range|candidate_record_id_pattern_invalid",
        "normalized_candidate_record_id empty",
    ),
    "ADMIT_002": (
        "admission_rule_id exact ADMIT_002",
        "legacy passed exact bool and equals (mapped outcome == passed)",
        "canonical_pdb_id exact str matching ^pdb_[a-z0-9]{8}$",
        "input_form in legacy_4_character|extended_12_character",
        "pdb_id_missing|pdb_id_not_string|pdb_id_empty|pdb_id_surrounding_whitespace_forbidden|pdb_id_non_ascii_forbidden|pdb_id_format_invalid|pdb_id_length_invalid",
        "canonical_pdb_id empty",
        "input_form exact invalid",
    ),
    "ADMIT_003": (
        "admission_rule_id exact ADMIT_003",
        "legacy passed exact bool and equals (mapped outcome == passed)",
        "original ligand_comp_id exact str",
        "canonical_ligand_comp_id nonempty exact str and equals original ligand_comp_id.upper()",
        "matches ^[A-Z0-9]{1,32}$",
        "LIGAND_COMP_ID_TYPE_INVALID|LIGAND_COMP_ID_EMPTY|LIGAND_COMP_ID_NON_ASCII|LIGAND_COMP_ID_LENGTH_INVALID|LIGAND_COMP_ID_SYNTAX_INVALID",
        "canonical_ligand_comp_id empty",
    ),
}


def _read_regular_file(path: Path) -> bytes:
    metadata = os.lstat(path)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"unsafe output entry: {path.name}")
    return path.read_bytes()


def _csv_rows(content: bytes, expected_header: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(
        io.StringIO(content.decode("utf-8", errors="strict"), newline="")
    )
    if tuple(reader.fieldnames or ()) != expected_header:
        raise ValueError("output CSV header mismatch")
    rows = [dict(row) for row in reader]
    if any(
        tuple(row) != expected_header or any(value is None for value in row.values())
        for row in rows
    ):
        raise ValueError("output CSV row mismatch")
    return rows


def _invalid_payload_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in text.split(";"):
        if "=" not in item:
            raise ValueError("adapter-side invalid payload field invalid")
        key, value = item.split("=", 1)
        if not key or key in fields:
            raise ValueError("adapter-side invalid payload key invalid")
        fields[key] = value
    return fields


def _validate_revised_contracts(
    contract_rows: list[dict[str, str]],
    reason_rows: list[dict[str, str]],
    routing_rows: list[dict[str, str]],
) -> None:
    contract_map = {row["admission_rule_id"]: row for row in contract_rows}
    if set(contract_map) != set(EXPECTED_ADAPTER_FAILURE_REASONS):
        raise ValueError("adapter contract rule IDs invalid")
    for rule_id, expected_reasons in EXPECTED_ADAPTER_FAILURE_REASONS.items():
        row = contract_map[rule_id]
        observed_reasons = (
            row["source_type_failure_reason"],
            row["source_invariant_failure_reason"],
            row["unknown_reason_failure_reason"],
        )
        if observed_reasons != expected_reasons:
            raise ValueError(f"adapter exact failure reasons invalid: {rule_id}")
        observed_oracle = (
            row["semantic_oracle_callable"],
            row["semantic_oracle_parameters"],
            row["expected_legacy_result_projection"],
        )
        if (
            observed_oracle != EXPECTED_SEMANTIC_ORACLE_CONTRACTS[rule_id]
            or row["legacy_result_oracle_equivalence_required"] != "true"
            or row["source_invariant_failure_reason"]
            != f"{rule_id}_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        ):
            raise ValueError(f"semantic oracle equivalence contract invalid: {rule_id}")
        if (
            row["malformed_result_disposition"]
            != "fail_closed:UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY;no_partial_unified_result"
            or row["unknown_reason_disposition"]
            != "fail_closed:UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY;do_not_guess_outcome"
            or not all(
                fragment in row["legacy_value_invariant_contract"]
                for fragment in EXPECTED_INVARIANT_FRAGMENTS[rule_id]
            )
        ):
            raise ValueError(f"adapter invariant contract invalid: {rule_id}")
        tuple_text = (
            row["consumed_candidate_fields"], row["consumed_context_items"]
        )
        if tuple_text != EXPECTED_TUPLE_TEXT[rule_id]:
            raise ValueError(f"tuple text contract invalid: {rule_id}")
    serialized_contracts = json.dumps(contract_rows, sort_keys=True)
    if "(candidate_record_id)" in serialized_contracts or "(batch_candidate_record_ids)" in serialized_contracts:
        raise ValueError("ambiguous legacy tuple text remains")

    precedence_rows = [
        row for row in routing_rows if row["contract_item"] == "execution_precedence"
    ]
    if (
        len(precedence_rows) != 3
        or tuple(row["admission_rule_id"] for row in precedence_rows)
        != ("ADMIT_001", "ADMIT_002", "ADMIT_003")
        or any(
            row["exact_requirement"] != EXPECTED_EXECUTION_PRECEDENCE
            for row in precedence_rows
        )
    ):
        raise ValueError("explicit execution precedence invalid")

    context_rows = {
        (row["admission_rule_id"], row["contract_item"]): row
        for row in routing_rows
        if row["dispatch_error_reason"]
    }
    if set(context_rows) != set(EXPECTED_CONTEXT_ERROR_REASONS):
        raise ValueError("context error reason branch set invalid")
    for key, reason in EXPECTED_CONTEXT_ERROR_REASONS.items():
        row = context_rows[key]
        if (
            row["dispatch_error_reason"] != reason
            or row["failure_disposition"]
            != "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
            or row["legacy_evaluator_called_on_failure"] != "false"
        ):
            raise ValueError(f"context exact reason invalid: {key}")

    invalid_rows = [
        row
        for row in routing_rows
        if row["contract_item"]
        in (
            "candidate_non_mapping_unified_result",
            "candidate_missing_field_unified_result",
        )
    ]
    if len(invalid_rows) != 6:
        raise ValueError("adapter-side invalid payload row count invalid")
    invalid_by_rule: dict[str, list[dict[str, str]]] = {}
    for row in invalid_rows:
        invalid_by_rule.setdefault(row["admission_rule_id"], []).append(row)
        rule_id = row["admission_rule_id"]
        rule_name, field, context_tuple, adapter_id, non_mapping, missing = (
            EXPECTED_INVALID_PAYLOAD_SPECS[rule_id]
        )
        reason = (
            non_mapping
            if row["contract_item"] == "candidate_non_mapping_unified_result"
            else missing
        )
        expected_fields = {
            "schema_version": "covapie_unified_admission_rule_evaluation_v1",
            "admission_rule_id": rule_id,
            "admission_rule_name": rule_name,
            "outcome": "invalid",
            "passed": "false",
            "blocks_candidate": "true",
            "reason": reason,
            "normalized_values": "()",
            "validated_candidate_fields": "()",
            "consumed_candidate_fields": f'(\"{field}\",)',
            "consumed_context_items": context_tuple,
            "evaluator_io_used": "false",
            "adapter_id": adapter_id,
            "legacy_evaluator_called": "false",
        }
        if (
            _invalid_payload_fields(row["exact_requirement"]) != expected_fields
            or row["failure_disposition"]
            != "adapter_side_invalid_unified_result"
            or row["dispatch_error_reason"] != ""
            or row["legacy_evaluator_called_on_failure"] != "false"
        ):
            raise ValueError(f"adapter-side invalid payload invalid: {rule_id}")
    for rule_id, rows in invalid_by_rule.items():
        rows_by_item = {row["contract_item"]: row for row in rows}
        expected_contract = (
            "candidate_non_mapping_unified_result:"
            + rows_by_item["candidate_non_mapping_unified_result"]["exact_requirement"]
            + "|candidate_missing_field_unified_result:"
            + rows_by_item["candidate_missing_field_unified_result"]["exact_requirement"]
        )
        if contract_map[rule_id]["adapter_side_invalid_result_contract"] != expected_contract:
            raise ValueError(f"invalid payload contract summary mismatch: {rule_id}")

    observed_reason_specs = {
        rule_id: tuple(
            (row["legacy_blocking_reason"], row["unified_outcome"])
            for row in reason_rows
            if row["admission_rule_id"] == rule_id
        )
        for rule_id in EXPECTED_REASON_SPECS
    }
    if observed_reason_specs != EXPECTED_REASON_SPECS:
        raise ValueError("Exact23 reason mapping drifted")


def _check_output_evidence(root: Path) -> dict[str, Any]:
    root = root if root.is_absolute() else REPO_ROOT / root
    metadata = os.lstat(root)
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ValueError("output root must be a real non-symlink directory")
    entries = tuple(root.iterdir())
    if {entry.name for entry in entries} != set(gate.OUTPUT_FILES):
        raise ValueError("output file set mismatch")
    observed = {entry.name: _read_regular_file(entry) for entry in entries}

    state = gate.build_phase3_design_state()
    if state["all_checks_passed"] is not True:
        raise ValueError("live design state failed closed")
    canonical_payloads, canonical_manifest = gate._payloads(state)
    for filename in gate.OUTPUT_FILES:
        if observed[filename] != canonical_payloads[filename]:
            raise ValueError(f"output bytes mismatch: {filename}")

    observed_hashes = {
        filename: hashlib.sha256(observed[filename]).hexdigest()
        for filename in gate.OUTPUT_FILES
    }
    if (
        any(len(value) != 64 for value in EXPECTED_OUTPUT_SHA256.values())
        or observed_hashes != EXPECTED_OUTPUT_SHA256
    ):
        raise ValueError("frozen output SHA256 mismatch")

    if len(EXPECTED_CONTRACT_COLUMNS) != 31:
        raise ValueError("checker contract column cardinality invalid")
    if gate.CONTRACT_COLUMNS != EXPECTED_CONTRACT_COLUMNS:
        raise ValueError("production contract header constant drifted")
    if gate.ROUTING_COLUMNS != EXPECTED_ROUTING_COLUMNS:
        raise ValueError("production routing header constant drifted")
    contract_rows = _csv_rows(
        observed[gate.CONTRACT_FILENAME], EXPECTED_CONTRACT_COLUMNS
    )
    reason_rows = _csv_rows(observed[gate.REASON_FILENAME], gate.REASON_COLUMNS)
    routing_rows = _csv_rows(
        observed[gate.ROUTING_FILENAME], EXPECTED_ROUTING_COLUMNS
    )
    safety_rows = _csv_rows(observed[gate.SAFETY_FILENAME], gate.SAFETY_COLUMNS)
    issue_rows = _csv_rows(observed[gate.ISSUE_FILENAME], gate.ISSUE_COLUMNS)
    manifest = json.loads(observed[gate.MANIFEST_FILENAME].decode("utf-8"))
    if type(manifest) is not dict or manifest != canonical_manifest:
        raise ValueError("manifest direct evidence mismatch")
    if (
        len(contract_rows) != 3
        or len(reason_rows) != 23
        or len(routing_rows) != 74
        or len(safety_rows)
        != len(gate.TRUE_SAFETY_ITEMS) + len(gate.FALSE_SAFETY_ITEMS)
        or len(issue_rows) != 12
        or any(row["contract_passed"] != "true" for row in contract_rows)
        or any(row["mapping_contract_passed"] != "true" for row in reason_rows)
        or any(row["contract_passed"] != "true" for row in routing_rows)
        or any(row["safety_passed"] != "true" for row in safety_rows)
    ):
        raise ValueError("direct output row evidence failed")
    _validate_revised_contracts(contract_rows, reason_rows, routing_rows)
    if manifest["output_sha256"] != {
        filename: observed_hashes[filename] for filename in gate.CSV_OUTPUTS
    }:
        raise ValueError("manifest output hashes mismatch")
    if (
        manifest["all_checks_passed"] is not True
        or manifest["ready_for_admit_001_to_003_legacy_adapter_implementation"]
        is not True
        or manifest["legacy_evaluator_adapters_implemented"] is not False
        or manifest["phase2_runtime_registry_modified"] is not False
        or manifest["admit_001_registered_in_engine"] is not False
        or manifest["admit_002_registered_in_engine"] is not False
        or manifest["admit_003_registered_in_engine"] is not False
        or manifest["combined_candidate_verdict_implemented"] is not False
        or manifest["cross_rule_precedence_frozen"] is not False
        or manifest["ready_for_bulk_download_now"] is not False
        or manifest["ready_for_training"] is not False
        or manifest["feature_semantics_audit_required_before_training"] is not True
        or manifest["phase2_runtime_registry_rule_ids"] != ["ADMIT_004"]
        or manifest["semantic_oracle_contract_count"] != 3
        or manifest["legacy_result_oracle_equivalence_required_count"] != 3
        or manifest["semantic_oracle_mismatch_dispatch_code"]
        != "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    ):
        raise ValueError("manifest readiness overclaim detected")
    issue_map = {row["issue_id"]: row for row in issue_rows}
    implementation_issue = issue_map.get(
        "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_IMPLEMENTATION_PENDING"
    )
    provider_issue = issue_map.get("REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT")
    if (
        implementation_issue is None
        or implementation_issue["status"] != "open"
        or implementation_issue["severity"] != "blocking"
        or provider_issue is None
        or provider_issue["status"] != "open"
        or provider_issue["severity"] != "blocking"
        or provider_issue["issue_count"] != "11"
        or issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"]
        != "open"
        or issue_map[
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
        ]["status"]
        != "open"
    ):
        raise ValueError("issue boundary drifted")
    phase2_sha = hashlib.sha256(
        (REPO_ROOT / gate.PHASE2_SOURCE_PATH).read_bytes()
    ).hexdigest()
    if phase2_sha != "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978":
        raise ValueError("Phase 2 runtime source SHA changed")
    snapshot = state["source_snapshot"]
    registry = gate._registry_literal_keys(
        gate._ast_document(snapshot, gate.PHASE2_SOURCE_PATH)
    )
    if registry != ("ADMIT_004",):
        raise ValueError("Phase 2 runtime registry changed")
    return {
        "all_checks_passed": True,
        "output_root": root,
        "output_sha256": observed_hashes,
        "reason_row_count": len(reason_rows),
        "routing_row_count": len(routing_rows),
        "context_error_reason_count": len(EXPECTED_CONTEXT_ERROR_REASONS),
        "adapter_failure_reason_count": 9,
        "adapter_side_invalid_payload_row_count": 6,
        "semantic_oracle_contract_count": sum(
            bool(row["semantic_oracle_callable"]) for row in contract_rows
        ),
        "legacy_result_oracle_equivalence_required_count": sum(
            row["legacy_result_oracle_equivalence_required"] == "true"
            for row in contract_rows
        ),
        "active_issue_count": len(issue_rows),
        "phase2_runtime_source_sha256": phase2_sha,
        "phase2_runtime_registry_rule_ids": list(registry),
        "ready_for_implementation": manifest[
            "ready_for_admit_001_to_003_legacy_adapter_implementation"
        ],
        "ready_for_bulk_download_now": manifest["ready_for_bulk_download_now"],
        "ready_for_training": manifest["ready_for_training"],
    }


def _materializer_self_checks() -> dict[str, bool]:
    with tempfile.TemporaryDirectory(prefix="covapie-phase3-revised1-") as temporary:
        temporary_root = Path(temporary)

        double_root = temporary_root / "double"
        gate.run_covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate_v1(
            double_root
        )
        first = {
            name: (double_root / name).read_bytes() for name in gate.OUTPUT_FILES
        }
        gate.run_covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate_v1(
            double_root
        )
        second = {
            name: (double_root / name).read_bytes() for name in gate.OUTPUT_FILES
        }
        double_materialization_passed = first == second

        symlink_root = temporary_root / "symlink"
        symlink_root.mkdir()
        victim = temporary_root / "victim"
        victim.write_bytes(b"do-not-overwrite")
        (symlink_root / gate.CONTRACT_FILENAME).symlink_to(victim)
        try:
            gate.run_covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate_v1(
                symlink_root
            )
        except ValueError:
            symlink_rejected = True
        else:
            symlink_rejected = False
        symlink_victim_passed = (
            symlink_rejected and victim.read_bytes() == b"do-not-overwrite"
        )

        tamper_root = temporary_root / "tamper"
        gate.run_covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate_v1(
            tamper_root
        )
        with (tamper_root / gate.CONTRACT_FILENAME).open("ab") as handle:
            handle.write(b"tamper")
        try:
            _check_output_evidence(tamper_root)
        except ValueError:
            output_tamper_passed = True
        else:
            output_tamper_passed = False

    if not (
        double_materialization_passed
        and symlink_victim_passed
        and output_tamper_passed
    ):
        raise ValueError("materializer/checker self-check failed")
    return {
        "double_materialization_passed": double_materialization_passed,
        "symlink_victim_passed": symlink_victim_passed,
        "output_tamper_fail_closed_passed": output_tamper_passed,
    }


def check_output_root(output_root: Path = gate.DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    result = _check_output_evidence(output_root)
    result.update(_materializer_self_checks())
    return result


def main() -> int:
    result = check_output_root()
    assert result["all_checks_passed"] is True
    assert isinstance(result["output_root"], Path)
    assert result["output_sha256"] == EXPECTED_OUTPUT_SHA256
    assert result["reason_row_count"] == 23
    assert result["routing_row_count"] == 74
    assert result["context_error_reason_count"] == 16
    assert result["adapter_failure_reason_count"] == 9
    assert result["adapter_side_invalid_payload_row_count"] == 6
    assert result["semantic_oracle_contract_count"] == 3
    assert result["legacy_result_oracle_equivalence_required_count"] == 3
    assert result["active_issue_count"] == 12
    assert result["phase2_runtime_source_sha256"] == "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978"
    assert result["phase2_runtime_registry_rule_ids"] == ["ADMIT_004"]
    assert result["ready_for_implementation"] is True
    assert result["ready_for_bulk_download_now"] is False
    assert result["ready_for_training"] is False
    assert result["double_materialization_passed"] is True
    assert result["symlink_victim_passed"] is True
    assert result["output_tamper_fail_closed_passed"] is True
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
