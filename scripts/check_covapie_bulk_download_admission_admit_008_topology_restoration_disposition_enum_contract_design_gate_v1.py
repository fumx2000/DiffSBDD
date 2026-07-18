#!/usr/bin/env python3
"""Independent checker for the ADMIT_008 disposition enum design gate v1."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate as gate,
)


EXPECTED_BASE_COMMIT = "6c8e563c529a2f60d5ca7a63bdd92ea901ca6d59"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_008 evaluator preconditions audit v1"
EXPECTED_STAGE = "covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1"
EXPECTED_OUTPUT_ROOT = Path("data/derived/covalent_small") / EXPECTED_STAGE
EXPECTED_NEXT_STEP = "implement_covapie_admit_008_standalone_evaluator_interface_v1"
EXPECTED_ENUM = (
    "approved_restoration_template",
    "explicit_manual_review_approved",
    "manual_review_required",
    "quarantine_required",
)
EXPECTED_ALLOWED = EXPECTED_ENUM[:2]
EXPECTED_SYNTAX = r"[a-z][a-z0-9_]{0,63}"
EXPECTED_SCALAR_REASONS = (
    "TOPOLOGY_RESTORATION_DISPOSITION_TYPE_INVALID",
    "TOPOLOGY_RESTORATION_DISPOSITION_EMPTY",
    "TOPOLOGY_RESTORATION_DISPOSITION_NON_ASCII",
    "TOPOLOGY_RESTORATION_DISPOSITION_SYNTAX_INVALID",
    "TOPOLOGY_RESTORATION_DISPOSITION_UNKNOWN",
)
EXPECTED_CONTEXT_REASONS = (
    "ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_TYPE_INVALID",
    "ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_CONTENT_INVALID",
)
EXPECTED_BLOCKED_REASONS = {
    "manual_review_required": "TOPOLOGY_RESTORATION_MANUAL_REVIEW_REQUIRED",
    "quarantine_required": "TOPOLOGY_RESTORATION_QUARANTINE_REQUIRED",
}
EXPECTED_FILES = (
    "covapie_admit_008_topology_restoration_disposition_enum_registry.csv",
    "covapie_admit_008_topology_restoration_disposition_validation_truth_matrix.csv",
    "covapie_admit_008_topology_restoration_disposition_category_mapping_matrix.csv",
    "covapie_admit_008_topology_restoration_disposition_source_boundary_audit.csv",
    "covapie_admit_008_topology_restoration_disposition_issue_readiness_inventory.csv",
    "covapie_admit_008_topology_restoration_disposition_enum_contract_manifest.json",
)
# Filled only with byte hashes frozen after deterministic materialization.
EXPECTED_OUTPUT_SHA256 = {
    "covapie_admit_008_topology_restoration_disposition_enum_registry.csv": "38e41ef09b62848e55e6d43fa2ee65ecc3b24378fd8ac9ca72fd2e313261556a",
    "covapie_admit_008_topology_restoration_disposition_validation_truth_matrix.csv": "d15cc2f468b158bdd0871386af041231f563af34ff394c2d25e8b5797fa3599b",
    "covapie_admit_008_topology_restoration_disposition_category_mapping_matrix.csv": "f449e7441045f52a2222f70f2b7378446424ea46610859641ae2baf5e4565be4",
    "covapie_admit_008_topology_restoration_disposition_source_boundary_audit.csv": "38bb2cc79380f6a561415f0ab3f3cd3756097ce9538f3c07e5538ce99204f7fa",
    "covapie_admit_008_topology_restoration_disposition_issue_readiness_inventory.csv": "229251600f0c6ae389633fff86af8859280b86664521ecce04c494906dc39695",
    "covapie_admit_008_topology_restoration_disposition_enum_contract_manifest.json": "4da97951abe63d46ded0ad5ffc6048e1a1c40eb2fdedd3553de094ac1ad0c85b",
}
EXPECTED_SOURCE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_008_formal_evaluator_preconditions_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_008_evaluator_precondition_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_008_disposition_vocabulary_inventory.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_008_issue_readiness_inventory.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv",
    "data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0/covalent_restoration_rule_registry_contract.csv",
    "data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0/ligand_topology_restoration_candidate_contract.csv",
    "data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0/ligand_topology_restoration_policy_design_gate_manifest.json",
    "data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0/ligand_topology_policy_review_decision_contract.csv",
    "data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0/ligand_topology_policy_review_gate_manifest.json",
)
EXPECTED_SOURCE_SHA256 = dict(zip(EXPECTED_SOURCE_PATHS, (
    "b621b143a0475f69db92a709d2612527595e2fe2fa6cc51fa51db20acfc2c2ac",
    "e93c43df4f64b6ce70c19c526546d3b1090c55f9150a944a76109ed0038cc136",
    "8d9f0dca15b8c851787f3808498f811f72f73f07caa70f4a51b5c88aaf314455",
    "45407488815876ebf2029027dcb42d65e3eeb18f53ece0b9f1454be10887ff71",
    "0a4cb44812ff5398ffba9a077f1217db3da3624d870922eec87848b60091c96e",
    "47de07417697808b044d30260f153ec7e5d46fb7c5b0e2c1f41187bcb09b89a0",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "61e00e08ca5d32b2508f0bec3e296bef0edd79fad220e4014a1ac32f5c86f92c",
    "7d506c058e5d4dc49b0c6397db1bb35d11520d157ef1805971acf44283a22751",
    "c104908df85b3a026e5aa83d72483d5698b25b5ed94f35c11b6d15cb4c5c57fc",
    "5b5bb3d4dec353c8dbeb4fce7aa840846464721d9fbd960835c052eaa4ed8a6a",
    "c1e24b4e583fa10c5338a6a9907b0fd683b51b34c8e26aaa5275ad5afb899bb9",
), strict=True))

ENUM_HEADER = (
    "enum_order", "canonical_value", "semantic_definition", "normative_contract_member",
    "passed_by_admit_008", "blocked_by_admit_008", "formal_reason",
    "included_in_allowed_context", "provider_mapping_required", "alias_allowed", "v1_enum_row_passed",
)
TRUTH_HEADER = (
    "case_id", "case_group", "scalar_input_kind", "scalar_input_display", "context_input_kind",
    "expected_scalar_classification", "expected_canonical_value", "expected_scalar_reason",
    "expected_context_valid", "expected_context_reason", "expected_outcome", "expected_passed",
    "expected_blocks_candidate", "expected_reason", "expected_validated_candidate_fields",
    "scalar_failure_precedence", "case_passed",
)
MAPPING_HEADER = (
    "mapping_order", "mapping_case_id", "policy_evidence", "expected_canonical_disposition",
    "expected_outcome", "expected_reason", "mapping_precedence",
    "real_provider_mapping_executed", "mapping_contract_passed",
)
SOURCE_HEADER = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256", "source_boundary_passed",
)
ISSUE_HEADER = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)
TRUE_READINESS = (
    "admit_008_topology_disposition_enum_contract_frozen", "admit_008_scalar_exact_type_contract_available",
    "admit_008_null_empty_standalone_contract_available", "admit_008_canonicalization_contract_available",
    "admit_008_category_mapping_contract_available", "admit_008_provenance_mapping_boundary_frozen",
    "admit_008_reason_outcome_contract_available", "admit_008_canonical_state_contract_available",
    "admit_008_context_contract_available", "admit_008_independent_semantic_oracle_available",
    "admit_008_standalone_evaluator_preconditions_complete",
    "ready_for_admit_008_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "real_provider_topology_disposition_mapping_validated", "real_provider_value_count_nonzero",
    "admit_008_standalone_evaluator_implemented", "admit_008_unified_adapter_contract_frozen",
    "admit_008_unified_adapter_implemented", "admit_008_registered_in_engine", "exact7_runtime_modified",
    "admit_009_standalone_evaluator_implemented", "admit_009_to_015_registered_in_engine",
    "all_15_rules_covered", "evaluate_all_rules_implemented", "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented", "cross_rule_precedence_frozen", "real_candidate_evaluation",
    "exact11_real_rows_evaluated", "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
)


class _StringSubclass(str):
    pass


def _sha_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _git(arguments: Sequence[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, text=text, capture_output=True, check=False)


def _source_kind(path: str) -> str:
    suffix = Path(path).suffix
    return "production_source" if suffix == ".py" else "committed_manifest" if suffix == ".json" else "committed_contract_csv"


def _csv(path: Path, header: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    assert tuple(reader.fieldnames or ()) == header
    rows = [dict(row) for row in reader]
    assert all(tuple(row) == header and all(value is not None for value in row.values()) for row in rows)
    return rows


def _read_verified_sources() -> dict[str, bytes]:
    subject = _git(["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"])
    assert subject.returncode == 0 and subject.stdout.strip() == EXPECTED_BASE_SUBJECT
    assert ancestor.returncode == 0
    for path in EXPECTED_SOURCE_PATHS:
        assert not path.startswith("data/raw/") and not path.startswith("checkpoints/")
        metadata = os.lstat(REPO_ROOT / path)
        tracked = _git(["ls-files", "--error-unmatch", "--", path])
        tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path])
        fields = tree.stdout.split("\t", 1)[0].split()
        assert tracked.returncode == 0 and tree.returncode == 0
        assert len(fields) == 3 and fields[0] in ("100644", "100755") and fields[1] == "blob"
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    result = {}
    for path in EXPECTED_SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path}"], text=False)
        filesystem = (REPO_ROOT / path).read_bytes()
        assert base.returncode == 0 and type(base.stdout) is bytes
        assert _sha_bytes(base.stdout) == _sha_bytes(filesystem) == EXPECTED_SOURCE_SHA256[path]
        result[path] = filesystem
    return result


def _expected_enum_rows() -> list[dict[str, str]]:
    definitions = (
        "approved reusable restoration template is valid for the current candidate or frozen scope",
        "candidate-specific manual review is complete, traceable, and explicitly approved",
        "topology restoration is not approved and requires completed human review",
        "unknown, untrusted, inapplicable, or quarantined residue-warhead restoration path",
    )
    rows = []
    for index, (value, definition) in enumerate(zip(EXPECTED_ENUM, definitions, strict=True), 1):
        passed = index <= 2
        rows.append({
            "enum_order": str(index), "canonical_value": value, "semantic_definition": definition,
            "normative_contract_member": "true", "passed_by_admit_008": str(passed).lower(),
            "blocked_by_admit_008": str(not passed).lower(),
            "formal_reason": "" if passed else EXPECTED_BLOCKED_REASONS[value],
            "included_in_allowed_context": str(passed).lower(), "provider_mapping_required": "true",
            "alias_allowed": "false", "v1_enum_row_passed": "true",
        })
    return rows


def _display(value: object) -> str:
    if type(value) is str:
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, _StringSubclass):
        return f"str_subclass:{json.dumps(str(value))}"
    return f"{type(value).__name__}:{repr(value)}"


def _classify(scalar: object, context: object) -> dict[str, Any]:
    canonical = ""
    validated = ""
    if type(scalar) is not str:
        scalar_class, scalar_reason = "invalid", EXPECTED_SCALAR_REASONS[0]
    elif scalar == "":
        scalar_class, scalar_reason = "invalid", EXPECTED_SCALAR_REASONS[1]
    elif not scalar.isascii():
        scalar_class, scalar_reason = "invalid", EXPECTED_SCALAR_REASONS[2]
    elif re.fullmatch(EXPECTED_SYNTAX, scalar, flags=re.ASCII) is None:
        scalar_class, scalar_reason = "invalid", EXPECTED_SCALAR_REASONS[3]
    elif scalar not in EXPECTED_ENUM:
        scalar_class, scalar_reason = "unknown", EXPECTED_SCALAR_REASONS[4]
    else:
        scalar_class, scalar_reason, canonical = "canonical", "", scalar
        validated = f"topology_restoration_disposition={scalar}"
    if type(context) is not tuple:
        context_valid, context_reason = False, EXPECTED_CONTEXT_REASONS[0]
    elif any(type(member) is not str for member in context) or context != EXPECTED_ALLOWED:
        context_valid, context_reason = False, EXPECTED_CONTEXT_REASONS[1]
    else:
        context_valid, context_reason = True, ""
    if scalar_class != "canonical":
        outcome, passed, blocks, reason, canonical, validated = "invalid", False, True, scalar_reason, "", ""
    elif not context_valid:
        outcome, passed, blocks, reason = "invalid", False, True, context_reason
    elif canonical in EXPECTED_ALLOWED:
        outcome, passed, blocks, reason = "passed", True, False, ""
    else:
        outcome, passed, blocks, reason = "blocked", False, True, EXPECTED_BLOCKED_REASONS[canonical]
    return {
        "scalar_class": scalar_class, "scalar_reason": scalar_reason, "canonical": canonical,
        "context_valid": context_valid, "context_reason": context_reason, "outcome": outcome,
        "passed": passed, "blocks": blocks, "reason": reason, "validated": validated,
    }


def _truth_definitions() -> tuple[tuple[str, str, object, str, object], ...]:
    exact = EXPECTED_ALLOWED
    scalar_cases = (
        ("canonical_approved_template", "canonical", EXPECTED_ENUM[0]),
        ("canonical_manual_approved", "canonical", EXPECTED_ENUM[1]),
        ("canonical_manual_required", "canonical", EXPECTED_ENUM[2]),
        ("canonical_quarantine", "canonical", EXPECTED_ENUM[3]),
        ("type_none", "scalar_type", None), ("type_int", "scalar_type", 7),
        ("type_bool", "scalar_type", True),
        ("type_str_subclass", "scalar_type", _StringSubclass(EXPECTED_ENUM[0])),
        ("type_list", "scalar_type", [EXPECTED_ENUM[0]]),
        ("type_mapping", "scalar_type", {"value": EXPECTED_ENUM[0]}),
        ("empty", "empty_syntax", ""), ("whitespace", "empty_syntax", " "),
        ("leading_whitespace", "empty_syntax", " approved_restoration_template"),
        ("trailing_whitespace", "empty_syntax", "approved_restoration_template "),
        ("uppercase", "empty_syntax", "Approved_restoration_template"),
        ("hyphen", "empty_syntax", "approved-restoration-template"),
        ("dot", "empty_syntax", "approved.restoration"), ("slash", "empty_syntax", "approved/restoration"),
        ("non_ascii", "empty_syntax", "approved_restoratión"),
        ("over_length", "empty_syntax", "a" * 65), ("leading_digit", "empty_syntax", "1approved"),
        ("unknown_valid", "unknown", "unregistered_disposition"),
        ("unknown_approved_looking", "unknown", "approved_manual_review"),
        ("unknown_manual_review_looking", "unknown", "manual_review_approved"),
        ("unknown_other", "unknown", "other"), ("unknown_unknown", "unknown", "unknown"),
    )
    contexts = (
        ("context_exact_tuple", exact), ("context_none", None), ("context_list", list(exact)),
        ("context_set", set(exact)), ("context_frozenset", frozenset(exact)),
        ("context_reversed", tuple(reversed(exact))), ("context_missing", exact[:1]),
        ("context_duplicate", (exact[0], exact[0])), ("context_blocked_added", (*exact, EXPECTED_ENUM[2])),
        ("context_unknown", (*exact, "unknown")),
        ("context_str_subclass_member", (_StringSubclass(exact[0]), exact[1])),
        ("context_extra", (*exact, "explicit_approval")),
    )
    result = [(case_id, group, scalar, "exact_tuple", exact) for case_id, group, scalar in scalar_cases]
    result.extend((case_id, "context", EXPECTED_ENUM[0], case_id.removeprefix("context_"), context) for case_id, context in contexts)
    return tuple(result)


def _expected_truth_rows() -> list[dict[str, str]]:
    rows = []
    for index, (case_id, group, scalar, context_kind, context) in enumerate(_truth_definitions(), 1):
        result = _classify(scalar, context)
        rows.append({
            "case_id": f"CASE_{index:03d}_{case_id}", "case_group": group,
            "scalar_input_kind": type(scalar).__name__, "scalar_input_display": _display(scalar),
            "context_input_kind": context_kind, "expected_scalar_classification": result["scalar_class"],
            "expected_canonical_value": result["canonical"], "expected_scalar_reason": result["scalar_reason"],
            "expected_context_valid": str(result["context_valid"]).lower(),
            "expected_context_reason": result["context_reason"], "expected_outcome": result["outcome"],
            "expected_passed": str(result["passed"]).lower(),
            "expected_blocks_candidate": str(result["blocks"]).lower(), "expected_reason": result["reason"],
            "expected_validated_candidate_fields": result["validated"],
            "scalar_failure_precedence": "true", "case_passed": "true",
        })
    assert len(rows) == 38
    return rows


def _expected_mapping_rows() -> list[dict[str, str]]:
    m = EXPECTED_BLOCKED_REASONS[EXPECTED_ENUM[2]]
    q = EXPECTED_BLOCKED_REASONS[EXPECTED_ENUM[3]]
    specs = (
        ("validated_current_scope_template", "validated approved reusable template for current candidate/scope", EXPECTED_ENUM[0], "passed", "", "validated template after quarantine/review checks"),
        ("candidate_specific_manual_approval", "traceable completed candidate-specific manual approval", EXPECTED_ENUM[1], "passed", "", "explicit manual approval after quarantine checks"),
        ("manual_review_not_completed", "manual review required but no completed approval", EXPECTED_ENUM[2], "blocked", m, "unfinished review overrides approval claim"),
        ("deferred_or_new_rule", "deferred, unvalidated, or new restoration rule", EXPECTED_ENUM[2], "blocked", m, "deferred/new rule requires review"),
        ("unknown_residue_warhead_pair", "unknown residue-warhead pair", EXPECTED_ENUM[3], "blocked", q, "unknown pair quarantines"),
        ("quarantine_flag", "quarantine flag is true", EXPECTED_ENUM[3], "blocked", q, "quarantine evidence first"),
        ("quarantine_over_template", "quarantine flag plus template approval claim", EXPECTED_ENUM[3], "blocked", q, "quarantine overrides template claim"),
        ("quarantine_over_manual_approval", "quarantine flag plus manual approval claim", EXPECTED_ENUM[3], "blocked", q, "quarantine overrides manual approval claim"),
        ("unvalidated_template", "template exists but current sample/scope validation absent", EXPECTED_ENUM[2], "blocked", m, "unvalidated template cannot approve"),
        ("manual_visual_review_required_true", "manual_visual_review_required=true without completed decision", EXPECTED_ENUM[2], "blocked", m, "review required is not review approved"),
        ("new_residue_or_warhead", "template claim generalized to a new residue or warhead", EXPECTED_ENUM[2], "blocked", m, "no residue/warhead auto-generalization"),
        ("no_v1_bypass", "not_applicable or no_restoration_required bypass claim", EXPECTED_ENUM[2], "blocked", m, "V1 has no bypass member"),
    )
    return [{
        "mapping_order": str(index), "mapping_case_id": case_id, "policy_evidence": evidence,
        "expected_canonical_disposition": canonical, "expected_outcome": outcome,
        "expected_reason": reason, "mapping_precedence": precedence,
        "real_provider_mapping_executed": "false", "mapping_contract_passed": "true",
    } for index, (case_id, evidence, canonical, outcome, reason, precedence) in enumerate(specs, 1)]


def _expected_source_rows() -> list[dict[str, str]]:
    return [{
        "source_order": str(index), "source_relative_path": path, "source_kind": _source_kind(path),
        "boundary_necessity": "normative ADMIT_008 identity, policy, issue, and runtime evidence",
        "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true", "non_symlink": "true",
        "expected_sha256": EXPECTED_SOURCE_SHA256[path], "base_tree_sha256": EXPECTED_SOURCE_SHA256[path],
        "filesystem_sha256": EXPECTED_SOURCE_SHA256[path], "source_boundary_passed": "true",
    } for index, path in enumerate(EXPECTED_SOURCE_PATHS, 1)]


def _expected_issue_rows(source_bytes: Mapping[str, bytes]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(source_bytes[EXPECTED_SOURCE_PATHS[5]].decode("utf-8"), newline=""))
    assert tuple(reader.fieldnames or ()) == ISSUE_HEADER
    rows = [dict(row) for row in reader]
    matches = [row for row in rows if row["issue_id"] == "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]
    assert len(rows) == 11 and len(matches) == 1
    matches[0]["status"] = "resolved"
    matches[0]["integration_transition"] = "topology_restoration_disposition_enum_contract_frozen_v1"
    return rows


def _readiness() -> dict[str, bool]:
    return {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def _expected_manifest(
    sources: list[dict[str, str]], truth: list[dict[str, str]], output_sha256: Mapping[str, str]
) -> dict[str, Any]:
    groups = {group: sum(row["case_group"] == group for row in truth)
              for group in ("canonical", "scalar_type", "empty_syntax", "unknown", "context")}
    readiness = _readiness()
    result: dict[str, Any] = {
        "project": "CovaPIE", "step": "ADMIT_008 topology restoration disposition enum contract design gate v1",
        "stage": EXPECTED_STAGE,
        "manifest_schema_version": "covapie_admit_008_topology_restoration_disposition_enum_contract_manifest_v1",
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": "ADMIT_008", "admission_rule_name": "topology_restoration_disposition",
        "candidate_field": "topology_restoration_disposition",
        "context_item": "allowed_topology_restoration_dispositions",
        "future_evaluator": "evaluate_admit_008", "future_result": "Admit008EvaluationResult",
        "future_signature_parameters": ["topology_restoration_disposition", "allowed_topology_restoration_dispositions"],
        "future_signature_required_positional_or_keyword": True,
        "standalone_interface": "required_direct_scalar_and_direct_context_objects",
        "candidate_mapping_accepted": False, "candidate_key_missing_handled_by_standalone": False,
        "source_boundary_name": "fixed_ordered_exact15_committed_source_boundary",
        "source_input_count": 15, "source_input_paths": list(EXPECTED_SOURCE_PATHS),
        "source_input_sha256": dict(EXPECTED_SOURCE_SHA256),
        "source_input_verification": [{
            "source_order": index, "source_relative_path": path,
            "expected_sha256": EXPECTED_SOURCE_SHA256[path], "base_tree_sha256": EXPECTED_SOURCE_SHA256[path],
            "filesystem_sha256": EXPECTED_SOURCE_SHA256[path], "tracked": True, "base_tree_blob": True,
            "filesystem_regular": True, "non_symlink": True, "source_verified": True,
        } for index, path in enumerate(EXPECTED_SOURCE_PATHS, 1)],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "normative_enum_member_count": 4, "normative_enum_members": list(EXPECTED_ENUM),
        "excluded_enum_members": [
            "approved_template_or_manual_review", "approved_or_manual_review", "topology_restoration_unapproved",
            "accepted", "quarantine_only", "unknown", "other", "unapproved", "deferred",
            "not_applicable", "no_restoration_required",
        ],
        "restoration_rule_ids_are_enum_members": False, "training_or_review_statuses_are_enum_members": False,
        "alias_support": False, "scalar_normalization_applied": False,
        "scalar_exact_runtime_type": "builtins.str", "scalar_canonical_syntax": EXPECTED_SYNTAX,
        "scalar_validation_precedence": ["exact_type", "nonempty", "ascii", "syntax", "membership"],
        "scalar_validation_reasons": list(EXPECTED_SCALAR_REASONS),
        "context_exact_runtime_type": "builtins.tuple",
        "allowed_topology_restoration_dispositions": list(EXPECTED_ALLOWED),
        "context_validation_precedence": ["exact_tuple_type", "exact_str_member_types", "exact_content_and_order"],
        "context_validation_reasons": list(EXPECTED_CONTEXT_REASONS),
        "outcome_vocabulary": ["passed", "blocked", "invalid"],
        "blocked_reason_mapping": dict(EXPECTED_BLOCKED_REASONS),
        "historical_lowercase_reason": "topology_restoration_unapproved",
        "historical_lowercase_reason_is_future_formal_reason": False,
        "candidate_fields": ["topology_restoration_disposition"],
        "context_items": ["allowed_topology_restoration_dispositions"],
        "invalid_scalar_canonical_value": "", "invalid_scalar_validated_candidate_fields": [],
        "canonical_scalar_context_invalid_retains_canonical_pair": True,
        "passed_and_blocked_retain_canonical_pair": True,
        "independent_design_oracle": "classify_admit_008_topology_restoration_disposition_design",
        "future_production_evaluator_must_not_call_design_oracle": True,
        "truth_matrix_row_count": 38, "truth_matrix_pass_count": 38,
        "truth_matrix_group_counts": groups, "category_mapping_row_count": 12,
        "category_mapping_pass_count": 12,
        "mapping_precedence": [
            "quarantine_evidence", "unfinished_or_required_manual_review",
            "validated_approved_reusable_template", "explicit_candidate_specific_manual_approval",
            "fail_closed_manual_review_or_quarantine",
        ],
        "provider_mapping_responsibility": "future_provider_or_candidate_materialization_contract",
        "standalone_provider_fields_consumed": [], "real_provider_value_count": 0,
        "real_provider_mapping_executed": False,
        "issue_inventory_row_count": 11, "issue_transition_count": 1,
        "issue_transition_id": "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED", "issue_transition_status": "resolved",
        "issue_integration_transition": "topology_restoration_disposition_enum_contract_frozen_v1",
        "unified_coverage_still_includes_admit_008": True,
        "readiness": readiness, **readiness,
        "output_file_count": 6, "output_files": list(EXPECTED_FILES),
        "output_sha256": dict(output_sha256), "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "no_evaluate_admit_008", "no_Admit008EvaluationResult", "no_adapter",
            "no_exact7_runtime_modification", "no_admit_008_registration", "no_provider_mapping_execution",
            "no_real_candidate_evaluation", "no_admit_009", "no_raw_network_download", "no_training",
        ],
        "recommended_next_step": EXPECTED_NEXT_STEP,
        "all_source_boundary_checks_passed": True, "all_enum_checks_passed": True,
        "all_truth_matrix_checks_passed": True, "all_category_mapping_checks_passed": True,
        "all_issue_checks_passed": True, "all_readiness_checks_passed": True,
        "all_attestations_passed": True, "validation_failures": [],
    }
    return result


def _validate_entries(root: Path) -> None:
    metadata = os.lstat(root)
    assert stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    assert tuple(sorted(path.name for path in root.iterdir())) == tuple(sorted(EXPECTED_FILES))
    for name in EXPECTED_FILES:
        metadata = os.lstat(root / name)
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)


def _validate_production_equivalence(root: Path) -> None:
    state = gate.build_design_state()
    expected = {
        EXPECTED_FILES[0]: gate._csv_bytes(gate.ENUM_REGISTRY_COLUMNS, state["enum_registry_rows"]),
        EXPECTED_FILES[1]: gate._csv_bytes(gate.TRUTH_MATRIX_COLUMNS, state["truth_matrix_rows"]),
        EXPECTED_FILES[2]: gate._csv_bytes(gate.CATEGORY_MAPPING_COLUMNS, state["category_mapping_rows"]),
        EXPECTED_FILES[3]: gate._csv_bytes(gate.SOURCE_BOUNDARY_COLUMNS, state["source_boundary_rows"]),
        EXPECTED_FILES[4]: gate._csv_bytes(gate.ISSUE_COLUMNS, state["issue_rows"]),
    }
    assert all((root / name).read_bytes() == content for name, content in expected.items())


def _validate_disk(root: Path, *, enforce_frozen_hashes: bool = True) -> dict[str, Any]:
    _validate_entries(root)
    source_bytes = _read_verified_sources()
    enum_rows = _csv(root / EXPECTED_FILES[0], ENUM_HEADER)
    truth = _csv(root / EXPECTED_FILES[1], TRUTH_HEADER)
    mappings = _csv(root / EXPECTED_FILES[2], MAPPING_HEADER)
    sources = _csv(root / EXPECTED_FILES[3], SOURCE_HEADER)
    issues = _csv(root / EXPECTED_FILES[4], ISSUE_HEADER)
    manifest = json.loads((root / EXPECTED_FILES[5]).read_text(encoding="utf-8"))
    assert type(manifest) is dict
    expected_truth = _expected_truth_rows()
    assert enum_rows == _expected_enum_rows()
    assert truth == expected_truth
    assert mappings == _expected_mapping_rows()
    assert sources == _expected_source_rows()
    assert issues == _expected_issue_rows(source_bytes)
    enum_issue = next(row for row in issues if row["issue_id"] == "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED")
    coverage = next(row for row in issues if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert enum_issue["status"] == "resolved"
    assert enum_issue["affected_fields"] == "topology_restoration_disposition"
    assert enum_issue["affected_rules"] == "ADMIT_008" and enum_issue["issue_count"] == "1"
    assert coverage["status"] == "open"
    assert coverage["affected_rules"] == "|".join(f"ADMIT_{index:03d}" for index in range(8, 16))
    assert coverage["integration_transition"] == "admit_007_implemented_and_removed_from_open_coverage_scope"
    output_sha = {name: _sha(root / name) for name in EXPECTED_FILES[:-1]}
    assert manifest == _expected_manifest(sources, expected_truth, output_sha)
    assert all(manifest[key] is manifest["readiness"][key] for key in (*TRUE_READINESS, *FALSE_READINESS))
    serialized = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in serialized.lower() and "/home/" not in serialized
    _validate_production_equivalence(root)
    if enforce_frozen_hashes:
        assert {name: _sha(root / name) for name in EXPECTED_FILES} == EXPECTED_OUTPUT_SHA256
    return manifest


def _raises(function: Any, *args: Any, **kwargs: Any) -> None:
    try:
        function(*args, **kwargs)
    except (AssertionError, ValueError, FileNotFoundError):
        return
    raise AssertionError("expected fail-closed rejection")


def _refresh_hash(root: Path, name: str) -> None:
    path = root / EXPECTED_FILES[5]
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["output_sha256"][name] = _sha(root / name)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _negative_checks(root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="covapie_admit008_enum_checker_") as temporary:
        temp = Path(temporary)
        enum_tamper = temp / "enum_tamper"
        shutil.copytree(root, enum_tamper)
        path = enum_tamper / EXPECTED_FILES[0]
        path.write_text(path.read_text(encoding="utf-8").replace(
            "approved_restoration_template", "not_applicable", 1
        ), encoding="utf-8")
        _refresh_hash(enum_tamper, EXPECTED_FILES[0])
        _raises(_validate_disk, enum_tamper, enforce_frozen_hashes=False)

        provider = temp / "provider"
        shutil.copytree(root, provider)
        path = provider / EXPECTED_FILES[5]
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["real_provider_value_count"] = 1
        manifest["real_provider_topology_disposition_mapping_validated"] = True
        manifest["readiness"]["real_provider_topology_disposition_mapping_validated"] = True
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _raises(_validate_disk, provider, enforce_frozen_hashes=False)

        extra = temp / "extra"
        shutil.copytree(root, extra)
        (extra / "unexpected.txt").write_text("unexpected", encoding="utf-8")
        _raises(_validate_disk, extra, enforce_frozen_hashes=False)


def main() -> int:
    root = REPO_ROOT / EXPECTED_OUTPUT_ROOT
    first = gate.run_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1(root)
    first_hashes = {name: _sha(root / name) for name in EXPECTED_FILES}
    second = gate.run_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1(root)
    second_hashes = {name: _sha(root / name) for name in EXPECTED_FILES}
    assert first["manifest"] == second["manifest"] and first_hashes == second_hashes
    manifest = _validate_disk(root)
    _negative_checks(root)
    print(f"stage={EXPECTED_STAGE}")
    print("all_checks_passed=true")
    print("source_boundary_exact15=true")
    print("enum_registry_exact4_passed=true")
    print("allowed_context_exact2=true")
    print("truth_matrix_exact38_passed=true")
    print("category_mapping_exact12_passed=true")
    print("issue_transition_exact1_passed=true")
    print("real_provider_value_count=0")
    print("real_provider_mapping_validated=false")
    print("ready_for_admit_008_standalone_evaluator_interface_implementation=true")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    print("outputs_byte_identical=true")
    print("covapie_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
