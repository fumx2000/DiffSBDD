"""Audit real-provider blocking rows and freeze a fail-closed V1 policy.

All evidence is read from blobs committed in ``BASE_COMMIT``.  Raw structure
references are retained only as opaque provenance strings and are never
dereferenced.  This step classifies evidence; it does not mutate provider
rows, resolve the provider issue, or materialize resolution/quarantine sets.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from covalent_ext import (
    covapie_bulk_download_admission_admit_004_rule_logic_interface as admit004,
)

__all__ = (
    "RealProviderExportBlockingRowsPolicyAuditDecision",
    "RealProviderExportResolutionOrQuarantinePolicyCaseDecision",
    "build_covapie_real_provider_export_blocking_rows_policy_audit_artifacts_v1",
    "classify_covapie_real_provider_export_blocking_row_evidence_v1",
    "derive_covapie_real_provider_export_blocking_rows_policy_audit_v1",
    "evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1",
    "serialize_covapie_real_provider_export_blocking_rows_policy_audit_decision_v1",
)

BASE_COMMIT = "e5563ed50db6e56cbdfb6cc629e5eb4fe9137edf"
BASE_PARENT = "7f432cecec8a3abed2339e4dd60dfa239cd2cbe7"
BASE_TREE = "7ab8a3cda9006fcda7c66f59472022e04a3c50a9"
BASE_SUBJECT = "add CovaPIE covalent bond atom-pair encoding contract validation v1"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE real-provider export blocking-row policy audit v1"
)
SCHEMA_VERSION = "covapie_real_provider_export_blocking_rows_policy_audit_v1"
STAGE = (
    "covapie_real_provider_export_blocking_rows_"
    "resolution_or_quarantine_policy_audit_v1"
)
ISSUE_ID = "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"
ISSUE_ORIGIN = (
    "covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_export_execution_smoke_v1"
)
ADMISSION_RULE = "ADMIT_004"
UNKNOWN_REASON = "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
STATE_VOCABULARY = ("absent", "present", "unknown")
DISPOSITIONS = (
    "explicitly_resolvable_from_committed_evidence",
    "quarantine_required_pending_provider_reexport",
    "contradictory_or_invalid_committed_evidence",
)
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)

OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
SOURCE_INVENTORY_FILE = (
    "covapie_real_provider_export_blocking_row_source_inventory.csv"
)
BLOCKING_MATRIX_FILE = (
    "covapie_real_provider_export_blocking_row_audit_matrix.csv"
)
SUFFICIENCY_MATRIX_FILE = (
    "covapie_real_provider_export_insertion_code_evidence_sufficiency_matrix.csv"
)
POLICY_MATRIX_FILE = (
    "covapie_real_provider_export_resolution_or_quarantine_policy_matrix.csv"
)
ISSUE_INVENTORY_FILE = "covapie_real_provider_export_issue_readiness_inventory.csv"
MANIFEST_FILE = (
    "covapie_real_provider_export_blocking_rows_"
    "resolution_or_quarantine_policy_audit_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_INVENTORY_FILE,
    BLOCKING_MATRIX_FILE,
    SUFFICIENCY_MATRIX_FILE,
    POLICY_MATRIX_FILE,
    ISSUE_INVENTORY_FILE,
    MANIFEST_FILE,
)

PREDECESSOR_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_"
    "current_canonical_evidence_validation_v1"
)
PREDECESSOR_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_covalent_bond_atom_pair_encoding_contract_"
    "current_canonical_evidence_validation_v1.py"
)
PREDECESSOR_MANIFEST = PREDECESSOR_ROOT / (
    "covapie_covalent_bond_atom_pair_encoding_contract_"
    "current_canonical_evidence_validation_manifest.json"
)
PREDECESSOR_ISSUES = PREDECESSOR_ROOT / (
    "covapie_atom_pair_contract_validation_issue_readiness_inventory.csv"
)
ORIGIN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_export_execution_smoke_v1"
)
ORIGIN_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_export_execution_smoke.py"
)
ORIGIN_TEST = Path(
    "tests/test_covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_export_execution_smoke_v1.py"
)
ORIGIN_CHECKER = Path(
    "scripts/check_covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_export_execution_smoke_v1.py"
)
ORIGIN_SUMMARY = Path(
    "docs/covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_export_execution_smoke_v1_summary.md"
)
ORIGIN_SIDECAR = ORIGIN_ROOT / (
    "covapie_covalent_residue_locator_real_provider_export_sidecar.csv"
)
ORIGIN_EVIDENCE = ORIGIN_ROOT / (
    "covapie_covalent_residue_locator_real_provider_export_execution_"
    "evidence_audit.csv"
)
ORIGIN_MANIFEST = ORIGIN_ROOT / (
    "covapie_covalent_residue_locator_real_provider_export_execution_manifest.json"
)
ORIGIN_ISSUES = ORIGIN_ROOT / (
    "covapie_covalent_residue_locator_real_provider_export_issue_inventory.csv"
)
BINDING_MATRIX = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_covalent_residue_locator_"
    "real_parser_provider_pipeline_integration_design_gate_v1/"
    "covapie_covalent_residue_locator_real_sample_binding_matrix.csv"
)
INTEGRATION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_sidecar_integration_gate_v1"
)
INTEGRATION_OVERLAY = INTEGRATION_ROOT / (
    "covapie_covalent_residue_locator_real_provider_integration_overlay.csv"
)
INTEGRATION_EVIDENCE = INTEGRATION_ROOT / (
    "covapie_covalent_residue_locator_real_provider_integration_evidence_audit.csv"
)
INTEGRATION_MANIFEST = INTEGRATION_ROOT / (
    "covapie_covalent_residue_locator_real_provider_sidecar_integration_manifest.json"
)
INTEGRATION_SUMMARY = Path(
    "docs/covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_sidecar_integration_gate_v1_summary.md"
)
ADMIT_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_004_rule_logic_interface.py"
)
ADMIT_TEST = Path(
    "tests/test_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1.py"
)
ADMIT_CHECKER = Path(
    "scripts/check_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1.py"
)
ADMIT_SUMMARY = Path(
    "docs/covapie_bulk_download_admission_admit_004_rule_logic_interface_v1_summary.md"
)
ADMIT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_004_rule_logic_interface_v1"
)
ADMIT_CONTRACT = ADMIT_ROOT / "covapie_admit_004_rule_logic_interface_contract.csv"
ADMIT_TRUTH = ADMIT_ROOT / "covapie_admit_004_rule_logic_interface_truth_matrix.csv"
ADMIT_MANIFEST = ADMIT_ROOT / "covapie_admit_004_rule_logic_interface_manifest.json"
DISPATCH_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py"
)
DISPATCH_TEST = Path(
    "tests/test_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1.py"
)
DISPATCH_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1"
)
DISPATCH_ROUTING = DISPATCH_ROOT / (
    "covapie_minimal_unified_dispatch_registry_and_routing_audit.csv"
)
DISPATCH_TRUTH = DISPATCH_ROOT / "covapie_minimal_unified_dispatch_shell_truth_matrix.csv"
DISPATCH_MANIFEST = DISPATCH_ROOT / "covapie_minimal_unified_dispatch_shell_manifest.json"

SOURCE_ROLES = (
    ("predecessor_validation_source", PREDECESSOR_SOURCE),
    ("predecessor_validation_manifest", PREDECESSOR_MANIFEST),
    ("current_issue_inventory", PREDECESSOR_ISSUES),
    ("issue_origin_source", ORIGIN_SOURCE),
    ("issue_origin_test", ORIGIN_TEST),
    ("issue_origin_checker", ORIGIN_CHECKER),
    ("issue_origin_summary", ORIGIN_SUMMARY),
    ("blocking_row_provider_export_sidecar", ORIGIN_SIDECAR),
    ("issue_origin_execution_evidence", ORIGIN_EVIDENCE),
    ("issue_origin_manifest", ORIGIN_MANIFEST),
    ("issue_origin_issue_inventory", ORIGIN_ISSUES),
    ("blocking_row_candidate_binding_matrix", BINDING_MATRIX),
    ("downstream_provider_overlay", INTEGRATION_OVERLAY),
    ("downstream_provider_evidence_audit", INTEGRATION_EVIDENCE),
    ("downstream_provider_manifest", INTEGRATION_MANIFEST),
    ("downstream_provider_summary", INTEGRATION_SUMMARY),
    ("admit_004_standalone_evaluator", ADMIT_SOURCE),
    ("admit_004_tests", ADMIT_TEST),
    ("admit_004_checker", ADMIT_CHECKER),
    ("admit_004_summary", ADMIT_SUMMARY),
    ("admit_004_contract", ADMIT_CONTRACT),
    ("admit_004_truth_matrix", ADMIT_TRUTH),
    ("admit_004_manifest", ADMIT_MANIFEST),
    ("admit_004_adapter_routing_source", DISPATCH_SOURCE),
    ("admit_004_adapter_routing_tests", DISPATCH_TEST),
    ("admit_004_adapter_routing_audit", DISPATCH_ROUTING),
    ("admit_004_adapter_truth_matrix", DISPATCH_TRUTH),
    ("admit_004_adapter_manifest", DISPATCH_MANIFEST),
)
FROZEN_SHA256 = {
    PREDECESSOR_SOURCE: "57b1acbf33950e4211d8d9404b3d3c0579f69683dbf4fc60299e0941ab906bea",
    PREDECESSOR_MANIFEST: "229f5430feb3b5c147edce6c80dce684703b614e3764c7c18afd8344c25c3152",
    PREDECESSOR_ISSUES: "09ee8271157343c4fd39c2edd73e38d6f0e896b8da247d8e3a8588c0b1cd0afa",
    ORIGIN_SOURCE: "5df4288eff9475ae6017fb57049a19790b6c278cfcb9a6eb22071ddef6c176b8",
    ORIGIN_TEST: "619034e6fe5f3597e5c733b1e2f29dfc523153513869254397e80f786d5e87f9",
    ORIGIN_CHECKER: "6b3a48d1a5b0b1f7864065b91376932b95da2b6cc8855906ddeb8e2da8d54358",
    ORIGIN_SUMMARY: "103bd958cff51563d0d291f1a1c24e9555dd117b3c028030aee31aa7759e1957",
    ORIGIN_SIDECAR: "066c0beeaa01d31a6d6ea3fae62f3df5177c2d904f6295646ee33a7fcd780ac7",
    ORIGIN_EVIDENCE: "4048efdfe373fe955995ded43639fcbd7baf67560e867662dbd18fe22a4fb1ab",
    ORIGIN_MANIFEST: "9061e36c333cf498dd5844407f5df11d64c3e271ae47e407938d34ac851d3aab",
    ORIGIN_ISSUES: "5bda40b683d649fb28a2172291f329c1f87d10f3a2bd122e1d5a6ab887a071c4",
    BINDING_MATRIX: "61a1e77c81a8a0d335bbafd454d2926be442c2dd794bce8b75dc8a1451f78e98",
    INTEGRATION_OVERLAY: "cc4c5965083340a040e4e1fc531da03bd74471e20fdc521ce92464d1d359627a",
    INTEGRATION_EVIDENCE: "c5efc4610762004829897064965bb4e06a1390d52c9f97254e66fbb1c7c899ec",
    INTEGRATION_MANIFEST: "37ce73b5c3608fad8eaac6d0f230cdd760b49347dce590998a7d1d7c7f7153db",
    INTEGRATION_SUMMARY: "2e6da2719030e0c20417d62b1a58db1d0d174ccaba57addb39b1b2ecc1490040",
    ADMIT_SOURCE: "5c05e166091a7a067014d9d4dbd8c7c4280b6f247c31765e14bf37d3f86adba3",
    ADMIT_TEST: "0f10c0689424e913135b80874e0270fc02376c6366bac22a640d639ff1b22f19",
    ADMIT_CHECKER: "a9ed9f63e0157f648e7865a849c80141dd81e8f56cfd79e291eeff72a9dfa51d",
    ADMIT_SUMMARY: "3e76235babb6a7da6603f371aa37594707a8b4c26b271484a720782caafae548",
    ADMIT_CONTRACT: "0c4fbc7f1307d3adb5c62dffb7668176b0ad54f2ff156b2f42ea02dec8d48250",
    ADMIT_TRUTH: "399fa0617aee4196c99051d99d26c75f54cbcc815a396425b7825dbeb9e7d83e",
    ADMIT_MANIFEST: "f000c7959c0e8a9f561d60b332c5460b4de84279d3e5c11556638334297723a6",
    DISPATCH_SOURCE: "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978",
    DISPATCH_TEST: "806dabf690d532f097006046d658c28e79719375d0410cb09a8debb101b94af6",
    DISPATCH_ROUTING: "74945a7d26507d17442a5eb7af925c0ae231be2ba8baacd4a408fffbba4d1c07",
    DISPATCH_TRUTH: "db104ad9de45743ed669be8d3afafdfc09592eb8003a17995580a3963c6bb679",
    DISPATCH_MANIFEST: "702492ff08760f3cddcdedd724f8078795d998a736958c87bb39642fa793c097",
}

SOURCE_COLUMNS = (
    "source_role", "source_path", "source_sha256", "committed_in_base",
    "data_row_count_if_tabular", "selector_or_symbol",
    "referenced_blocking_row_count", "verified",
)
BLOCKING_COLUMNS = (
    "audit_row_order", "blocking_row_identity", "provider_export_row_identity",
    "candidate_identity", "pdb_id", "ligand_identity", "residue_name",
    "residue_chain_or_asym_id", "residue_sequence_id",
    "observed_insertion_code_state", "observed_insertion_code",
    "admission_rule_id", "admit_004_outcome", "admit_004_reason",
    "provider_export_status", "blocking_reason",
    "state_code_combination_valid", "residue_locator_identity_complete",
    "provider_provenance_complete", "raw_required_to_resolve",
    "heuristic_inference_required", "audit_disposition", "audit_reason",
    "source_path", "source_selector", "source_sha256", "verified",
)
SUFFICIENCY_COLUMNS = (
    "blocking_row_identity", "evidence_item", "observed_value",
    "required_value_or_rule", "evidence_sufficient", "evidence_source",
    "failure_effect", "verified",
)
POLICY_COLUMNS = (
    "case_id", "input_condition", "expected_disposition", "expected_reason",
    "resolution_allowed", "quarantine_allowed",
    "contradiction_resolution_required", "provider_row_mutation_allowed",
    "fails_closed", "verified",
)

_SHA_RE = re.compile(r"[0-9a-f]{64}", re.ASCII)


@dataclass(frozen=True)
class RealProviderExportBlockingRowsPolicyAuditDecision:
    schema_version: str
    outcome: str
    predecessor_verified: bool
    blocking_row_count: int
    unique_blocking_row_count: int
    admit_004_contract_verified: bool
    resolvable_from_committed_evidence_count: int
    quarantine_required_count: int
    contradictory_or_invalid_count: int
    all_rows_classified: bool
    resolution_or_quarantine_policy_frozen: bool
    provider_rows_mutated: bool
    provider_issue_resolved: bool
    ready_for_resolution_materialization: bool
    ready_for_quarantine_materialization: bool
    ready_for_feature_semantics_audit: bool
    ready_for_tensorization: bool
    ready_for_training: bool
    recommended_next_step: str


@dataclass(frozen=True)
class RealProviderExportResolutionOrQuarantinePolicyCaseDecision:
    case_id: str
    disposition: str
    reason: str
    resolution_allowed: bool
    quarantine_allowed: bool
    contradiction_resolution_required: bool
    provider_row_mutation_allowed: bool
    fails_closed: bool


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git(repo_root: Path, *args: str) -> bytes:
    return subprocess.run(
        ("git", *args), cwd=repo_root, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _base_bytes(repo_root: Path, path: Path) -> bytes:
    if path.is_absolute() or ".." in path.parts or path.parts[:2] == ("data", "raw"):
        raise ValueError(f"unsafe committed source path: {path}")
    spec = f"{BASE_COMMIT}:{path.as_posix()}"
    _git(repo_root, "cat-file", "-e", spec)
    payload = _git(repo_root, "show", spec)
    if _sha(payload) != FROZEN_SHA256[path]:
        raise ValueError(f"BASE source SHA256 mismatch: {path}")
    return payload


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = [dict(row) for row in reader]
    if any(
        tuple(row) != tuple(reader.fieldnames)
        or any(type(value) is not str for value in row.values())
        for row in rows
    ):
        raise ValueError("invalid CSV row")
    return rows


def _csv_bytes(columns: tuple[str, ...], rows: list[Mapping[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if tuple(row) != columns:
            raise ValueError("output row schema/order mismatch")
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _json(payload: bytes) -> dict[str, Any]:
    value = json.loads(payload)
    if type(value) is not dict:
        raise ValueError("JSON document must be an object")
    return value


def _keyed(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            raise ValueError(f"missing/duplicate {key}")
        result[value] = row
    return result


def _state_code_valid(state: object, code: object) -> bool:
    if type(state) is not str or type(code) is not str:
        return False
    if state not in STATE_VOCABULARY:
        return False
    if state in ("absent", "unknown"):
        return code == ""
    return (
        code != ""
        and code.isascii()
        and not any(character.isspace() for character in code)
        and code not in (".", "?")
        and re.fullmatch(admit004.INSERTION_PRESENT_VALUE_PATTERN, code, re.ASCII)
        is not None
    )


def classify_covapie_real_provider_export_blocking_row_evidence_v1(
    *,
    state_field_present: bool,
    code_field_present: bool,
    state: object,
    code: object,
    provider_provenance_complete: bool,
    residue_identity_unique: bool,
    auth_label_consistent: bool,
    raw_required: bool,
    heuristic_required: bool,
    admit_outcome: str,
    admit_reason: str,
    recorded_provider_status: str,
    recorded_blocking_reason: str,
) -> tuple[str, str]:
    """Classify one evidence row without repairing or defaulting its values."""
    if type(state_field_present) is not bool or type(code_field_present) is not bool:
        raise TypeError("field-presence flags must be exact built-in bool values")
    if not state_field_present:
        return (
            DISPOSITIONS[1],
            "missing insertion-code state requires provider re-export or curated explicit evidence",
        )
    if not code_field_present:
        return (
            DISPOSITIONS[1],
            "missing insertion-code value field requires provider re-export or curated explicit evidence",
        )
    if not _state_code_valid(state, code):
        return (
            DISPOSITIONS[2],
            "state/code combination contradicts the committed ADMIT_004 contract",
        )
    if (
        recorded_provider_status != "exported_blocking"
        or admit_outcome != "blocked"
        or admit_reason != recorded_blocking_reason
    ):
        return (
            DISPOSITIONS[2],
            "provider row and reproduced ADMIT_004 evaluation disagree",
        )
    if (
        state == "unknown"
        or not provider_provenance_complete
        or not residue_identity_unique
        or not auth_label_consistent
        or raw_required
        or heuristic_required
    ):
        reasons = []
        if state == "unknown":
            reasons.append("insertion-code provenance state is unknown")
        if not provider_provenance_complete:
            reasons.append("provider provenance is incomplete")
        if not residue_identity_unique:
            reasons.append("residue identity is not unique")
        if not auth_label_consistent:
            reasons.append("auth/label locator evidence is conflicting")
        if raw_required:
            reasons.append("new raw/provider evidence is required to resolve")
        if heuristic_required:
            reasons.append("resolution would require forbidden heuristic inference")
        return DISPOSITIONS[1], "; ".join(reasons)
    return (
        DISPOSITIONS[0],
        "committed evidence explicitly and uniquely supports the state/code pair",
    )


def _predecessor_verified(payloads: Mapping[Path, bytes]) -> bool:
    manifest = _json(payloads[PREDECESSOR_MANIFEST])
    issues = _csv_rows(payloads[PREDECESSOR_ISSUES])
    issue_map = _keyed(issues, "issue_id")
    provider = issue_map[ISSUE_ID]
    checks = (
        len(issues) == 30,
        manifest.get("validation_outcome") == "validated",
        manifest.get("encoding_contract_validation_completed") is True,
        manifest.get("atom_pair_issue_resolved") is True,
        manifest.get("atom_pair_ready_for_downstream_contracts") is True,
        manifest.get("effective_open_issue_count") == 1,
        manifest.get("effective_open_issues") == [ISSUE_ID],
        manifest.get("next_training_preparation_blocker") == ISSUE_ID,
        manifest.get("ready_for_tensorization") is False,
        manifest.get("feature_semantics_audit_completed") is False,
        manifest.get("ready_for_training") is False,
        provider.get("affected_fields")
        == "covalent_residue_insertion_code_state|covalent_residue_insertion_code",
        provider.get("affected_rules") == ADMISSION_RULE,
        provider.get("status") == "open",
        provider.get("issue_origin") == ISSUE_ORIGIN,
        provider.get("issue_count") == "11",
    )
    return all(checks)


def _admit_contract_verified(payloads: Mapping[Path, bytes]) -> bool:
    source = payloads[ADMIT_SOURCE].decode("utf-8")
    contract = _csv_rows(payloads[ADMIT_CONTRACT])
    truth = _csv_rows(payloads[ADMIT_TRUTH])
    manifest = _json(payloads[ADMIT_MANIFEST])
    routing = _csv_rows(payloads[DISPATCH_ROUTING])
    dispatch_truth = _csv_rows(payloads[DISPATCH_TRUTH])
    dispatch_manifest = _json(payloads[DISPATCH_MANIFEST])
    required_source_fragments = (
        'state not in ("absent", "present", "unknown")',
        'if state == "absent":',
        'if state == "unknown":',
        'if state == "unknown" and value == "":',
        'return _result("blocked", UNKNOWN_REASON',
        'def evaluate_admit_004(',
    )
    checks = (
        admit004.CANDIDATE_FIELDS[5:7]
        == (
            "covalent_residue_insertion_code_state",
            "covalent_residue_insertion_code",
        ),
        tuple(STATE_VOCABULARY) == ("absent", "present", "unknown"),
        all(fragment in source for fragment in required_source_fragments),
        len(contract) == 43 and all(row["contract_passed"] == "true" for row in contract),
        len(truth) == 50 and all(row["truth_passed"] == "true" for row in truth),
        manifest.get("admit_004_rule_logic_interface_implemented") is True,
        manifest.get("provider_blocking_issue_id") == ISSUE_ID,
        manifest.get("provider_blocking_issue_count") == 11,
        manifest.get("real_provider_export_blocking_rows_resolved") is False,
        len(routing) == 15 and all(row["audit_passed"] == "true" for row in routing),
        len(dispatch_truth) == 24
        and all(row["truth_passed"] == "true" for row in dispatch_truth),
        dispatch_manifest.get("registered_rule_ids") == ["ADMIT_004"],
        dispatch_manifest.get("provider_blocking_issue_id") == ISSUE_ID,
        dispatch_manifest.get("provider_blocking_issue_count") == 11,
    )
    return all(checks)


def _candidate(
    binding: Mapping[str, str], sidecar: Mapping[str, str]
) -> dict[str, str]:
    return {
        "covalent_residue_name": binding["covalent_residue_name"],
        "covalent_residue_chain_id": binding["selected_residue_chain_id"],
        "covalent_residue_index": binding["selected_residue_index"],
        "covalent_residue_atom_name": binding["selected_residue_atom_name"],
        "covalent_residue_locator_namespace": sidecar[
            "covalent_residue_locator_namespace"
        ],
        "covalent_residue_insertion_code_state": sidecar[
            "covalent_residue_insertion_code_state"
        ],
        "covalent_residue_insertion_code": sidecar[
            "covalent_residue_insertion_code"
        ],
        "covalent_residue_locator_provenance_source_id": sidecar[
            "covalent_residue_locator_provenance_source_id"
        ],
        "covalent_residue_locator_provenance_sha256": sidecar[
            "covalent_residue_locator_provenance_sha256"
        ],
    }


def _source_rows(payloads: Mapping[Path, bytes]) -> list[dict[str, Any]]:
    referenced_roles = {
        "current_issue_inventory", "blocking_row_provider_export_sidecar",
        "issue_origin_execution_evidence", "issue_origin_manifest",
        "issue_origin_issue_inventory", "blocking_row_candidate_binding_matrix",
        "downstream_provider_overlay", "downstream_provider_evidence_audit",
        "downstream_provider_manifest", "admit_004_standalone_evaluator",
        "admit_004_contract", "admit_004_truth_matrix", "admit_004_manifest",
        "admit_004_adapter_routing_source", "admit_004_adapter_routing_audit",
        "admit_004_adapter_truth_matrix", "admit_004_adapter_manifest",
    }
    selectors = {
        "blocking_row_provider_export_sidecar": "provider_export_status=exported_blocking",
        "issue_origin_execution_evidence": "provider_export_status=exported_blocking",
        "blocking_row_candidate_binding_matrix": "binding_row_id join",
        "downstream_provider_overlay": "binding_row_id join",
        "downstream_provider_evidence_audit": "binding_row_id join",
        "admit_004_standalone_evaluator": "evaluate_admit_004",
        "admit_004_adapter_routing_source": "evaluate_admission_rule",
        "current_issue_inventory": f"issue_id={ISSUE_ID}",
        "issue_origin_issue_inventory": f"issue_id={ISSUE_ID}",
    }
    rows: list[dict[str, Any]] = []
    for role, path in SOURCE_ROLES:
        payload = payloads[path]
        count: str | int = ""
        if path.suffix == ".csv":
            count = len(_csv_rows(payload))
        rows.append({
            "source_role": role,
            "source_path": path.as_posix(),
            "source_sha256": _sha(payload),
            "committed_in_base": True,
            "data_row_count_if_tabular": count,
            "selector_or_symbol": selectors.get(role, "whole committed artifact"),
            "referenced_blocking_row_count": 11 if role in referenced_roles else 0,
            "verified": _sha(payload) == FROZEN_SHA256[path],
        })
    return rows


def _sufficiency_rows(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    identity = str(row["blocking_row_identity"])
    source = f"{ORIGIN_SIDECAR.as_posix()}#{row['source_selector']}"
    consistent = row["auth_label_consistent"]
    checks = (
        ("state field present", row["state_field_present"], "field exists in committed header", "quarantine"),
        ("code field present", row["code_field_present"], "field exists in committed header", "quarantine"),
        ("state vocabulary valid", row["state_vocabulary_valid"], "|".join(STATE_VOCABULARY), "contradiction"),
        ("state/code combination valid", row["state_code_combination_valid"], "absent/unknown=>empty; present=>valid nonempty", "contradiction"),
        ("provider provenance present", row["provider_provenance_complete"], "nonempty source id and lowercase SHA256", "quarantine"),
        ("candidate identity unique", row["candidate_identity_unique"], "exactly one blocking row", "quarantine"),
        ("residue identity unique", row["residue_identity_unique"], "exactly one pdb/residue locator", "quarantine"),
        ("auth locator available", row["auth_locator_available"], "auth chain and sequence available", "quarantine"),
        ("label locator available", row["label_locator_available"], "label chain and sequence available", "quarantine"),
        ("auth/label locator consistent", consistent, "auth and label locators identify one residue without conflict", "quarantine"),
        ("explicit no-insertion evidence available", row["explicit_no_insertion"], "state=absent and code empty", "quarantine"),
        ("explicit insertion-code evidence available", row["explicit_insertion"], "state=present and code nonempty", "quarantine"),
        ("raw access required", row["raw_required_to_resolve"], "false for resolution from committed evidence", "quarantine"),
        ("heuristic inference required", row["heuristic_inference_required"], "false", "quarantine"),
        ("ADMIT_004 evaluation reproducible", row["admit_reproducible"], "blocked with committed reason", "contradiction"),
    )
    result = []
    for item, observed, rule, effect in checks:
        if item in ("raw access required", "heuristic inference required"):
            sufficient = observed is False
        elif item.startswith("explicit "):
            sufficient = observed is True
        else:
            sufficient = observed is True
        # Explicit insertion evidence is intentionally insufficient for every
        # unknown row; that insufficiency is evidence for quarantine.
        result.append({
            "blocking_row_identity": identity,
            "evidence_item": item,
            "observed_value": str(observed).lower(),
            "required_value_or_rule": rule,
            "evidence_sufficient": sufficient,
            "evidence_source": source,
            "failure_effect": effect,
            "verified": row["verified"] is True,
        })
    return result


POLICY_CASES = (
    ("POLICY_001", "explicit present state + nonempty consistent code"),
    ("POLICY_002", "explicit absent state + empty code"),
    ("POLICY_003", "unknown state + empty code"),
    ("POLICY_004", "missing state"),
    ("POLICY_005", "missing code field"),
    ("POLICY_006", "present state + empty code"),
    ("POLICY_007", "absent state + nonempty code"),
    ("POLICY_008", "unsupported state"),
    ("POLICY_009", "duplicate identical evidence"),
    ("POLICY_010", "duplicate conflicting evidence"),
    ("POLICY_011", "auth/label consistent locator"),
    ("POLICY_012", "auth/label conflicting locator"),
    ("POLICY_013", "provider provenance missing"),
    ("POLICY_014", "raw required"),
    ("POLICY_015", "heuristic-only resolution"),
    ("POLICY_016", "ADMIT_004 blocked reproducibly"),
    ("POLICY_017", "ADMIT_004 outcome mismatch"),
)


def _policy_decision(
    case_id: str, disposition: str, reason: str,
) -> RealProviderExportResolutionOrQuarantinePolicyCaseDecision:
    if disposition not in DISPOSITIONS or not reason:
        raise ValueError("invalid policy-case decision")
    return RealProviderExportResolutionOrQuarantinePolicyCaseDecision(
        case_id=case_id,
        disposition=disposition,
        reason=reason,
        resolution_allowed=disposition == DISPOSITIONS[0],
        quarantine_allowed=disposition == DISPOSITIONS[1],
        contradiction_resolution_required=disposition == DISPOSITIONS[2],
        provider_row_mutation_allowed=False,
        fails_closed=True,
    )


def _policy_classifier_inputs(case_id: str) -> dict[str, Any] | None:
    values: dict[str, Any] = {
        "state_field_present": True,
        "code_field_present": True,
        "state": "absent",
        "code": "",
        "provider_provenance_complete": True,
        "residue_identity_unique": True,
        "auth_label_consistent": True,
        "raw_required": False,
        "heuristic_required": False,
        "admit_outcome": "blocked",
        "admit_reason": "ADMIT_004_BLOCKED_REPRODUCIBLY",
        "recorded_provider_status": "exported_blocking",
        "recorded_blocking_reason": "ADMIT_004_BLOCKED_REPRODUCIBLY",
    }
    overrides: dict[str, dict[str, Any] | None] = {
        "POLICY_001": {"state": "present", "code": "A"},
        "POLICY_002": {},
        "POLICY_003": {
            "state": "unknown", "code": "", "raw_required": True,
            "admit_reason": UNKNOWN_REASON,
            "recorded_blocking_reason": UNKNOWN_REASON,
        },
        "POLICY_004": {"state_field_present": False, "state": ""},
        "POLICY_005": {
            "code_field_present": False, "state": "absent", "code": None,
        },
        "POLICY_006": {"state": "present", "code": ""},
        "POLICY_007": {"state": "absent", "code": "A"},
        "POLICY_008": {"state": "unsupported", "code": ""},
        "POLICY_009": {"residue_identity_unique": False},
        "POLICY_010": None,
        "POLICY_011": {},
        "POLICY_012": {"auth_label_consistent": False},
        "POLICY_013": {"provider_provenance_complete": False},
        "POLICY_014": {"raw_required": True},
        "POLICY_015": {"heuristic_required": True},
        "POLICY_016": {
            "state": "unknown", "code": "",
            "admit_reason": UNKNOWN_REASON,
            "recorded_blocking_reason": UNKNOWN_REASON,
        },
        "POLICY_017": {
            "admit_outcome": "passed", "admit_reason": "",
        },
    }
    if case_id not in overrides or overrides[case_id] is None:
        return None
    values.update(overrides[case_id] or {})
    return values


def evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(
    case_id: str,
) -> RealProviderExportResolutionOrQuarantinePolicyCaseDecision:
    """Execute one frozen policy case; unknown IDs fail closed as invalid."""
    if type(case_id) is not str:
        raise TypeError("case_id must be an exact string")
    if case_id == "POLICY_010":
        return _policy_decision(
            case_id, DISPOSITIONS[2],
            "duplicate identity has conflicting locator evidence",
        )
    inputs = _policy_classifier_inputs(case_id)
    if inputs is None:
        return _policy_decision(
            case_id, DISPOSITIONS[2],
            "unknown policy case id fails closed as invalid",
        )
    disposition, reason = (
        classify_covapie_real_provider_export_blocking_row_evidence_v1(**inputs)
    )
    return _policy_decision(case_id, disposition, reason)


def _policy_classifier_consistency_verified() -> bool:
    consistency_cases = (
        "POLICY_001", "POLICY_002", "POLICY_003", "POLICY_004",
        "POLICY_005", "POLICY_006", "POLICY_007", "POLICY_008",
        "POLICY_013", "POLICY_014", "POLICY_015", "POLICY_017",
    )
    for case_id in consistency_cases:
        inputs = _policy_classifier_inputs(case_id)
        if inputs is None:
            return False
        classifier = classify_covapie_real_provider_export_blocking_row_evidence_v1(
            **inputs
        )
        policy = (
            evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(
                case_id
            )
        )
        if classifier != (policy.disposition, policy.reason):
            return False
    return True


def _policy_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id, condition in POLICY_CASES:
        decision = (
            evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(
                case_id
            )
        )
        verified = (
            decision.case_id == case_id
            and decision.disposition in DISPOSITIONS
            and sum((
                decision.resolution_allowed,
                decision.quarantine_allowed,
                decision.contradiction_resolution_required,
            )) == 1
            and decision.provider_row_mutation_allowed is False
            and decision.fails_closed is True
        )
        rows.append({
            "case_id": decision.case_id,
            "input_condition": condition,
            "expected_disposition": decision.disposition,
            "expected_reason": decision.reason,
            "resolution_allowed": decision.resolution_allowed,
            "quarantine_allowed": decision.quarantine_allowed,
            "contradiction_resolution_required": decision.contradiction_resolution_required,
            "provider_row_mutation_allowed": decision.provider_row_mutation_allowed,
            "fails_closed": decision.fails_closed,
            "verified": verified,
        })
    return rows


def derive_covapie_real_provider_export_blocking_rows_policy_audit_v1(
    repo_root: Path,
) -> dict[str, Any]:
    """Derive the audit solely from frozen BASE blobs."""
    if tuple(FROZEN_SHA256) != tuple(path for _, path in SOURCE_ROLES):
        raise ValueError("source inventory order/boundary mismatch")
    payloads = {path: _base_bytes(repo_root, path) for path in FROZEN_SHA256}
    predecessor_verified = _predecessor_verified(payloads)
    contract_verified = _admit_contract_verified(payloads)
    if not predecessor_verified or not contract_verified:
        raise ValueError("predecessor or ADMIT_004 contract validation failed")

    sidecar_rows = _csv_rows(payloads[ORIGIN_SIDECAR])
    binding_rows = _csv_rows(payloads[BINDING_MATRIX])
    evidence_rows = _csv_rows(payloads[ORIGIN_EVIDENCE])
    overlay_rows = _csv_rows(payloads[INTEGRATION_OVERLAY])
    integration_rows = _csv_rows(payloads[INTEGRATION_EVIDENCE])
    origin_manifest = _json(payloads[ORIGIN_MANIFEST])
    origin_issues = _keyed(_csv_rows(payloads[ORIGIN_ISSUES]), "issue_id")
    blocking = [
        row for row in sidecar_rows
        if row.get("provider_export_status") == "exported_blocking"
    ]
    if (
        len(sidecar_rows) != 11
        or len(blocking) != 11
        or origin_manifest.get("exported_blocking_count") != 11
        or origin_manifest.get("provider_row_count") != 11
        or origin_issues[ISSUE_ID].get("issue_count") != "11"
    ):
        raise ValueError("real provider blocking-row cardinality is not exactly 11")

    bindings = _keyed(binding_rows, "binding_row_id")
    evidence = _keyed(evidence_rows, "binding_row_id")
    overlays = _keyed(overlay_rows, "binding_row_id")
    integrations = _keyed(integration_rows, "binding_row_id")
    identities = [row["binding_row_id"] for row in blocking]
    if len(set(identities)) != 11:
        raise ValueError("blocking-row identities are not unique")
    candidate_counts: dict[str, int] = {}
    residue_counts: dict[tuple[str, ...], int] = {}
    for item in blocking:
        binding = bindings[item["binding_row_id"]]
        candidate_counts[binding["sample_preparation_input_id"]] = (
            candidate_counts.get(binding["sample_preparation_input_id"], 0) + 1
        )
        residue_key = (
            binding["pdb_id"], binding["covalent_residue_name"],
            binding["selected_residue_chain_id"], binding["selected_residue_index"],
            binding["selected_residue_atom_name"],
        )
        residue_counts[residue_key] = residue_counts.get(residue_key, 0) + 1

    audit_rows: list[dict[str, Any]] = []
    sufficiency_rows: list[dict[str, Any]] = []
    for order, sidecar in enumerate(blocking, start=1):
        identity = sidecar["binding_row_id"]
        binding = bindings[identity]
        origin_evidence = evidence[identity]
        overlay = overlays[identity]
        integrated = integrations[identity]
        candidate = _candidate(binding, sidecar)
        evaluation = admit004.evaluate_admit_004(candidate, {})
        state = sidecar["covalent_residue_insertion_code_state"]
        code = sidecar["covalent_residue_insertion_code"]
        state_valid = state in STATE_VOCABULARY
        combination_valid = _state_code_valid(state, code)
        provenance_complete = (
            bool(candidate["covalent_residue_locator_provenance_source_id"])
            and _SHA_RE.fullmatch(
                candidate["covalent_residue_locator_provenance_sha256"]
            ) is not None
        )
        candidate_unique = (
            candidate_counts[binding["sample_preparation_input_id"]] == 1
        )
        residue_key = (
            binding["pdb_id"], binding["covalent_residue_name"],
            binding["selected_residue_chain_id"], binding["selected_residue_index"],
            binding["selected_residue_atom_name"],
        )
        residue_unique = residue_counts[residue_key] == 1
        auth_available = bool(
            sidecar["struct_conn_residue_auth_asym_id"]
            and sidecar["struct_conn_residue_auth_seq_id"]
        )
        label_available = bool(
            sidecar["struct_conn_residue_label_asym_id"]
            and sidecar["struct_conn_residue_label_seq_id"]
        )
        auth_label_consistent = (
            sidecar["auth_label_conflict_observed"] == "false"
        )
        raw_required = state == "unknown"
        heuristic_required = False
        admit_reproducible = (
            evaluation.outcome == "blocked"
            and evaluation.reason == sidecar["provider_export_blocking_reason"]
            and origin_evidence["provider_export_status"] == "exported_blocking"
            and origin_evidence["provider_export_blocking_reason"] == evaluation.reason
            and integrated["integration_status"] == "integrated_blocking"
            and integrated["integration_blocking_reason"] == evaluation.reason
        )
        cross_artifact_match = (
            all(
                overlay[field] == sidecar[field]
                for field in (
                    "covalent_residue_locator_namespace",
                    "covalent_residue_insertion_code_state",
                    "covalent_residue_insertion_code",
                    "covalent_residue_locator_provenance_source_id",
                    "covalent_residue_locator_provenance_sha256",
                )
            )
            and integrated["provider_five_fields_match"] == "true"
            and origin_evidence["pdb_id"] == binding["pdb_id"]
            and origin_evidence["ligand_comp_id"] == binding["ligand_comp_id"]
        )
        disposition, reason = (
            classify_covapie_real_provider_export_blocking_row_evidence_v1(
                state_field_present=(
                    "covalent_residue_insertion_code_state" in sidecar
                ),
                code_field_present=(
                    "covalent_residue_insertion_code" in sidecar
                ),
                state=state,
                code=code,
                provider_provenance_complete=provenance_complete,
                residue_identity_unique=residue_unique,
                auth_label_consistent=auth_label_consistent,
                raw_required=raw_required,
                heuristic_required=heuristic_required,
                admit_outcome=evaluation.outcome,
                admit_reason=evaluation.reason,
                recorded_provider_status=sidecar["provider_export_status"],
                recorded_blocking_reason=sidecar[
                    "provider_export_blocking_reason"
                ],
            )
        )
        verified = (
            identity == f"REAL_LOCATOR_BINDING_{order:06d}"
            and combination_valid
            and candidate_unique
            and provenance_complete
            and admit_reproducible
            and cross_artifact_match
            and disposition in DISPOSITIONS
        )
        internal = {
            "blocking_row_identity": identity,
            "source_selector": f"binding_row_id={identity}",
            "state_field_present": (
                "covalent_residue_insertion_code_state" in sidecar
            ),
            "code_field_present": "covalent_residue_insertion_code" in sidecar,
            "state_vocabulary_valid": state_valid,
            "state_code_combination_valid": combination_valid,
            "provider_provenance_complete": provenance_complete,
            "candidate_identity_unique": candidate_unique,
            "residue_identity_unique": residue_unique,
            "auth_locator_available": auth_available,
            "label_locator_available": label_available,
            "auth_label_consistent": auth_label_consistent,
            "explicit_no_insertion": state == "absent" and code == "",
            "explicit_insertion": state == "present" and code != "",
            "raw_required_to_resolve": raw_required,
            "heuristic_inference_required": heuristic_required,
            "admit_reproducible": admit_reproducible,
            "verified": verified,
        }
        audit_rows.append({
            "audit_row_order": order,
            "blocking_row_identity": identity,
            "provider_export_row_identity": identity,
            "candidate_identity": binding["sample_preparation_input_id"],
            "pdb_id": binding["pdb_id"],
            "ligand_identity": binding["ligand_comp_id"],
            "residue_name": binding["covalent_residue_name"],
            "residue_chain_or_asym_id": binding["selected_residue_chain_id"],
            "residue_sequence_id": binding["selected_residue_index"],
            "observed_insertion_code_state": state,
            "observed_insertion_code": code,
            "admission_rule_id": ADMISSION_RULE,
            "admit_004_outcome": evaluation.outcome,
            "admit_004_reason": evaluation.reason,
            "provider_export_status": sidecar["provider_export_status"],
            "blocking_reason": sidecar["provider_export_blocking_reason"],
            "state_code_combination_valid": combination_valid,
            "residue_locator_identity_complete": (
                residue_unique and auth_available and label_available
                and auth_label_consistent
            ),
            "provider_provenance_complete": provenance_complete,
            "raw_required_to_resolve": raw_required,
            "heuristic_inference_required": heuristic_required,
            "audit_disposition": disposition,
            "audit_reason": reason,
            "source_path": ORIGIN_SIDECAR.as_posix(),
            "source_selector": f"binding_row_id={identity}",
            "source_sha256": FROZEN_SHA256[ORIGIN_SIDECAR],
            "verified": verified,
        })
        sufficiency_rows.extend(_sufficiency_rows(internal))

    if not all(row["verified"] is True for row in audit_rows):
        raise ValueError("one or more blocking rows failed verification")
    policy_rows = _policy_rows()
    if (
        len(policy_rows) != 17
        or not all(row["verified"] for row in policy_rows)
        or not _policy_classifier_consistency_verified()
    ):
        raise ValueError("policy matrix is incomplete or invalid")
    counts = {
        disposition: sum(
            row["audit_disposition"] == disposition for row in audit_rows
        )
        for disposition in DISPOSITIONS
    }
    if counts[DISPOSITIONS[2]] > 0:
        next_step = (
            "resolve_covapie_real_provider_export_blocking_row_"
            "evidence_contradictions_v1"
        )
    elif counts[DISPOSITIONS[1]] > 0:
        next_step = (
            "materialize_covapie_real_provider_export_blocking_row_quarantine_v1"
        )
    elif counts[DISPOSITIONS[0]] == 11:
        next_step = (
            "materialize_covapie_real_provider_export_insertion_code_resolution_v1"
        )
    else:
        raise ValueError("classified counts do not cover exact11")
    decision = RealProviderExportBlockingRowsPolicyAuditDecision(
        schema_version=SCHEMA_VERSION,
        outcome="audited_policy_frozen",
        predecessor_verified=True,
        blocking_row_count=len(audit_rows),
        unique_blocking_row_count=len({row["blocking_row_identity"] for row in audit_rows}),
        admit_004_contract_verified=True,
        resolvable_from_committed_evidence_count=counts[DISPOSITIONS[0]],
        quarantine_required_count=counts[DISPOSITIONS[1]],
        contradictory_or_invalid_count=counts[DISPOSITIONS[2]],
        all_rows_classified=sum(counts.values()) == 11,
        resolution_or_quarantine_policy_frozen=True,
        provider_rows_mutated=False,
        provider_issue_resolved=False,
        ready_for_resolution_materialization=counts[DISPOSITIONS[0]] > 0,
        ready_for_quarantine_materialization=(
            counts[DISPOSITIONS[1]] > 0 and counts[DISPOSITIONS[2]] == 0
        ),
        ready_for_feature_semantics_audit=False,
        ready_for_tensorization=False,
        ready_for_training=False,
        recommended_next_step=next_step,
    )
    return {
        "decision": decision,
        "source_rows": _source_rows(payloads),
        "audit_rows": audit_rows,
        "sufficiency_rows": sufficiency_rows,
        "policy_rows": policy_rows,
        "issue_payload": payloads[PREDECESSOR_ISSUES],
    }


def serialize_covapie_real_provider_export_blocking_rows_policy_audit_decision_v1(
    decision: RealProviderExportBlockingRowsPolicyAuditDecision,
) -> bytes:
    if type(decision) is not RealProviderExportBlockingRowsPolicyAuditDecision:
        raise TypeError("decision has the wrong exact type")
    return (
        json.dumps(asdict(decision), sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _non_manifest_artifacts(result: Mapping[str, Any]) -> dict[str, bytes]:
    return {
        SOURCE_INVENTORY_FILE: _csv_bytes(SOURCE_COLUMNS, result["source_rows"]),
        BLOCKING_MATRIX_FILE: _csv_bytes(BLOCKING_COLUMNS, result["audit_rows"]),
        SUFFICIENCY_MATRIX_FILE: _csv_bytes(
            SUFFICIENCY_COLUMNS, result["sufficiency_rows"]
        ),
        POLICY_MATRIX_FILE: _csv_bytes(POLICY_COLUMNS, result["policy_rows"]),
        ISSUE_INVENTORY_FILE: result["issue_payload"],
    }


def _manifest(result: Mapping[str, Any], artifacts: Mapping[str, bytes]) -> dict[str, Any]:
    decision = result["decision"]
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "real_provider_export_blocking_rows_policy_audit_completed": True,
        "audit_outcome": decision.outcome,
        "blocking_row_count": decision.blocking_row_count,
        "unique_blocking_row_count": decision.unique_blocking_row_count,
        "admit_004_contract_verified": decision.admit_004_contract_verified,
        "admit_004_insertion_code_state_vocabulary": list(STATE_VOCABULARY),
        "all_rows_classified": decision.all_rows_classified,
        "resolvable_from_committed_evidence_count": decision.resolvable_from_committed_evidence_count,
        "quarantine_required_count": decision.quarantine_required_count,
        "contradictory_or_invalid_count": decision.contradictory_or_invalid_count,
        "resolution_or_quarantine_policy_frozen": True,
        "policy_matrix_executable": True,
        "policy_matrix_classifier_consistency_verified": (
            _policy_classifier_consistency_verified()
        ),
        "missing_state_disposition": (
            evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(
                "POLICY_004"
            ).disposition
        ),
        "missing_code_field_disposition": (
            evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(
                "POLICY_005"
            ).disposition
        ),
        "unsupported_state_disposition": (
            evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(
                "POLICY_008"
            ).disposition
        ),
        "provider_rows_mutated": False,
        "provider_reexport_performed": False,
        "quarantine_materialized": False,
        "resolution_materialized": False,
        "provider_issue_resolved": False,
        "issue_status_changed": False,
        "resolved_issue_count": 0,
        "new_issue_count": 0,
        "deleted_issue_count": 0,
        "effective_open_issue_count": 1,
        "effective_open_issues": [ISSUE_ID],
        "atom_pair_issue_resolved": True,
        "atom_pair_ready_for_downstream_contracts": True,
        "ready_for_resolution_materialization": decision.ready_for_resolution_materialization,
        "ready_for_quarantine_materialization": decision.ready_for_quarantine_materialization,
        "ready_for_feature_semantics_audit": False,
        "ready_for_tensorization": False,
        "pair_tensor_materialized": False,
        "pair_tensor_shape_defined": False,
        "negative_pair_construction_defined": False,
        "negative_sampling_defined": False,
        "pair_loss_mask_defined": False,
        "pair_head_implemented": False,
        "pair_contrastive_loss_implemented": False,
        "provider_used": False,
        "network_used": False,
        "download_used": False,
        "raw_read": False,
        "raw_write": False,
        "checkpoint_access": False,
        "model_changed": False,
        "dataloader_changed": False,
        "forward_changed": False,
        "loss_changed": False,
        "training_used": False,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "feature_semantics_known": False,
        "unknown_atom_feature_policy_resolved": False,
        "ready_for_training": False,
        "canonical_masks": [
            {"semantic_name": name, "display_alias": alias}
            for name, alias in CANONICAL_MASKS
        ],
        "source_inventory_row_count": len(result["source_rows"]),
        "blocking_row_audit_matrix_row_count": len(result["audit_rows"]),
        "evidence_sufficiency_matrix_row_count": len(result["sufficiency_rows"]),
        "policy_matrix_row_count": len(result["policy_rows"]),
        "issue_inventory_row_count": 30,
        "evidence_sha256": {
            name: _sha(payload) for name, payload in artifacts.items()
        },
        "recommended_next_step": decision.recommended_next_step,
    }


def build_covapie_real_provider_export_blocking_rows_policy_audit_artifacts_v1(
    repo_root: Path,
) -> dict[str, bytes]:
    result = derive_covapie_real_provider_export_blocking_rows_policy_audit_v1(
        repo_root
    )
    artifacts = _non_manifest_artifacts(result)
    artifacts[MANIFEST_FILE] = (
        json.dumps(_manifest(result, artifacts), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return artifacts
