#!/usr/bin/env python3
"""Independent fail-closed checker for the CovaPIE Exact11 runtime."""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import inspect
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import fields
from pathlib import Path
from types import MappingProxyType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = "covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011"
SUCCESSOR_SOURCE_RELATIVE_PATH = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py"
)
EXPECTED_SUCCESSOR_SOURCE_SHA256 = "ca8e64897b30f961d999d37ce8af5eb985ddf34f332af40c29bf2142bad6e2c8"
BASE = "fab48133058b826f5e9387c06d3cb0024657aec9"
SUBJECT = "add CovaPIE ADMIT_011 unified adapter contract design v1"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_011 v1"
STAGE = "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1"
MANIFEST_SCHEMA = "covapie_unified_dispatch_runtime_with_admit_001_to_011_manifest_v1"
OUTPUT_ROOT = ROOT / "data/derived/covalent_small" / STAGE
RULE_ID = "ADMIT_011"
RULE_NAME = "raw_overwrite_forbidden"
ADAPTER_ID = "covapie_admit_011_unified_adapter_v1"
KNOWN_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
REGISTERED_IDS = KNOWN_IDS[:11]
EXPECTED_RULE_NAMES = {
    "ADMIT_001": "unique_candidate_identity",
    "ADMIT_002": "valid_pdb_id_format",
    "ADMIT_003": "ligand_or_het_identity_present",
    "ADMIT_004": "covalent_residue_identity_present",
    "ADMIT_005": "cys_sg_scope_only_v1",
    "ADMIT_006": "explicit_covalent_event_evidence",
    "ADMIT_007": "distance_only_inference_forbidden",
    "ADMIT_008": "topology_restoration_disposition",
    "ADMIT_009": "duplicate_identity_precheck",
    "ADMIT_010": "leakage_group_assignment_before_split",
    "ADMIT_011": "raw_overwrite_forbidden",
}
EXPECTED_ADAPTER_IDS = {
    "ADMIT_001": "covapie_admit_001_unified_adapter_v1",
    "ADMIT_002": "covapie_admit_002_unified_adapter_v1",
    "ADMIT_003": "covapie_admit_003_unified_adapter_v1",
    "ADMIT_004": "covapie_admit_004_unified_adapter_v1",
    "ADMIT_005": "covapie_admit_005_unified_adapter_v1",
    "ADMIT_006": "covapie_admit_006_unified_adapter_v1",
    "ADMIT_007": "covapie_admit_007_unified_adapter_v1",
    "ADMIT_008": "covapie_admit_008_unified_adapter_v1",
    "ADMIT_009": "covapie_admit_009_unified_adapter_v1",
    "ADMIT_010": "covapie_admit_010_unified_adapter_v1",
    "ADMIT_011": "covapie_admit_011_unified_adapter_v1",
}
CANDIDATE_FIELDS = ("raw_target_relative_path",)
CONTEXT_ITEMS = (
    "raw_target_relative_path_contract",
    "existing_raw_target_relative_paths",
)
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
SOURCE_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_raw_target_relative_path", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
)
ERROR_FIELDS = (
    "code", "admission_rule_id", "known_rule", "callable_discovered",
    "adapter_ready", "reason",
)
ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
    "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOMES = ("passed", "blocked", "invalid", "rejected")
OUTPUTS = (
    "covapie_admit_001_to_011_runtime_contract.csv",
    "covapie_admit_001_to_011_runtime_truth_matrix.csv",
    "covapie_admit_001_to_011_registry_routing_and_oracle_audit.csv",
    "covapie_admit_001_to_011_runtime_safety_audit.csv",
    "covapie_admit_001_to_011_runtime_issue_inventory.csv",
    "covapie_admit_001_to_011_runtime_manifest.json",
)
FROZEN_OUTPUT_SHA256 = {
    "covapie_admit_001_to_011_runtime_contract.csv": "9616573151091786f07b3c4d1b6c8343a1ceb796f439e495023abd2f3ad37626",
    "covapie_admit_001_to_011_runtime_truth_matrix.csv": "c6d543b9c1ad6760e202074b981659ca34155c16ec0435b1cec3035c93d90901",
    "covapie_admit_001_to_011_registry_routing_and_oracle_audit.csv": "0ceb3aa607fb9a539a3d5a6fd519a685693d765b3606e52be9d3316ce476c752",
    "covapie_admit_001_to_011_runtime_safety_audit.csv": "3ec709b1e9cfd82e2fa17bd05013e7a392bf709de85f4f00e37886577a749dd1",
    "covapie_admit_001_to_011_runtime_issue_inventory.csv": "976e3b195d20cacaf0658b38fb88f922479bc9e4ac29e8834933cc734fe8935b",
    "covapie_admit_001_to_011_runtime_manifest.json": "9895bf9b82eb9ca0f9c90ef8012af644a2b325dd971c3e6655b361fc8ff83011",
}
FROZEN_CSV_SEMANTIC_SHA256 = {
    "covapie_admit_001_to_011_runtime_contract.csv": "f268eb3cd7663e9eb94d4e25db7389b05d145d7110bd0c823265f6b8b11252b7",
    "covapie_admit_001_to_011_runtime_truth_matrix.csv": "5043fb30b3f00d287342965dea3ef95d981f0713bcc362b85dfa64df14be1585",
    "covapie_admit_001_to_011_registry_routing_and_oracle_audit.csv": "aa7e28bdcdd0efc99b2f61fc9388334a6df1228aa39a8663e2a84446e766b0ef",
    "covapie_admit_001_to_011_runtime_safety_audit.csv": "fc2ae3cc201ba26fdc06ff73554bf5bc79f1826dc4ee9351c71c9080a7d35e3f",
    "covapie_admit_001_to_011_runtime_issue_inventory.csv": "e990891fa901b8355667f915642eabf67c1c0a6e80430d5ce9aeccb76675c943",
}
FROZEN_MANIFEST_SEMANTIC_SHA256 = "13db070a67a6f160bd1e04d8f61837cf7cf2f3baaa88b5a00e9b6b71af3d4334"
SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010.py", "b613321aa1563c7c559208fc08cf82d1e2ccee07cdc6b9c8c338d87b14c78436"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_manifest.json", "46dcef1d5e62c5a8904e9ff66b145b6ee9dae88fc406e42d669a8a7002285198"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_contract.csv", "da2ccbeef748a9ff503ff1e993bcdfb05ae436f92dcd4d46544c424f4f841874"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_truth_matrix.csv", "2d087ef178cd7402fa3d0d40a8a22d2b0a726ed0f49ff2549f6893db15cb20ee"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_registry_routing_and_oracle_audit.csv", "c797c6aad1a9951c61c85379fc2f633aa528bc593dd6f923de9416b7f07ccdbc"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_safety_audit.csv", "2c2ae91713cbd05361db3b0a1e74045cc9b810e06133caceff53e8daf0b5786b"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_issue_inventory.csv", "f59eecc7136ebdd148f2c6c6422b7a2bc0637e340322e09bc005eb00355db03c"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py", "73adad5c617ecae0dc5772d04ae5d777970a3d2a8c8963c3d2c4c4b19cbf85fc"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_manifest.json", "a3c053d7b4af149b67b818721f11bb6920b5de00d5d15fb5ec176e10e5a70c3c"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_contract.csv", "7624bfda25b7aca2a3db11fab18a883c52dee0e598a295ada0b0676a1847aea2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_truth_matrix.csv", "974bc68fdd8c6d8c500cce3f70970bd16d18f07d49d7e4162776bd62cd0e064b"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_source_boundary_audit.csv", "096f0016610a428a39aa63c071e145c8f78051a8cf500510057a0712638904b6"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_purity_audit.csv", "e4f6df108d51188e87ac0d7d0de9363b82cd22f18f0b2f97a79e0fd448f4a93e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_issue_readiness_inventory.csv", "eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate.py", "93e6e726092f8c3e66b19c7ab4c6d363d47962c07eeb694c7237b2b0d5a31346"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract_manifest.json", "d5ad2622b5182898c418d774e4c0deb33fc2fb643caaa5da0507cabb3824f884"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract.csv", "4b4b41295364fcb83f807c054e2e561ca2c4a31fbf27fd55d04607f3c127c2cc"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_candidate_projection_and_context_routing_matrix.csv", "be12ce9e9c551f5891cac9840d130dd9feabfb99fe849385db08dcf767486845"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_result_projection_truth_matrix.csv", "deb4b71376a27d00317d9255e822c9e534c39fc16f0a6636dc149a6ca205b01a"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_issue_readiness_inventory.csv", "eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.py", "c515afab9ac6dc4390d9ef0bf385de4261c612bb1cbe67a19b008c40c288cd7d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_contract_manifest.json", "9718090b212e3338bddef1fb7d6fb62e39d95e1911fe5bdd0ff6613b364e8bf4"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_grammar_truth_matrix.csv", "1b32c3cc658433da18b804336afec8c63a275bcf44f68556faf75804e3b386ca"),
)
CONTRACT_COLUMNS = (
    "contract_order", "contract_id", "contract_group", "contract_subject",
    "expected_value", "observed_value", "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "admission_rule_id", "behavior",
    "expected_result_or_error", "observed_result_or_error", "expected_reason",
    "observed_reason", "formal_call_count", "oracle_call_count",
    "candidate_access_status", "handler_identity_status", "case_passed",
)
REGISTRY_COLUMNS = (
    "rule_id", "rule_name", "known_rule", "callable_discovered", "adapter_ready",
    "registered", "adapter_id", "handler_identity_status", "dispatch_disposition",
    "audit_passed",
)
SAFETY_COLUMNS = (
    "safety_item", "expected_executed", "observed_executed", "safety_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity",
    "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count",
)
TRUE_READINESS = (
    "admit_011_standalone_evaluator_implemented", "evaluate_admit_011_implemented",
    "Admit011EvaluationResult_implemented", "admit_011_unified_adapter_contract_frozen",
    "admit_011_unified_adapter_implemented", "admit_011_registered_in_engine",
    "admit_011_context_routing_runtime_enforced",
    "admit_011_candidate_projection_runtime_enforced",
    "admit_011_source_exact10_validation_runtime_enforced",
    "admit_011_source_oracle_full_exact10_equality_runtime_enforced",
    "admit_011_exact10_to_exact13_projection_runtime_enforced",
    "admit_011_formal_exactly_once_runtime_enforced",
    "admit_011_oracle_exactly_once_runtime_enforced",
    "exact11_reuses_exact10_public_type_identity",
    "exact11_first_ten_handler_identity_preserved",
    "exact11_public_dispatch_uses_local_registry",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_012_started", "all_15_rules_covered", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen", "provider_mapping_validated",
    "real_provider_evaluation_ready", "ready_for_bulk_download_now",
    "checkpoint_compatibility_validated", "full_repository_canonical_validated",
    "ready_for_training",
)

RUNTIME_DEFINITION_NAMES = (
    "evaluate_admission_rule",
    "_raise_dispatch_error",
    "_admit011_context_failure",
    "_admit011_adapter_failure",
    "_admit011_candidate_invalid",
    "_prevalidate_admit011_source",
    "_expected_admit011_from_oracle",
    "_validate_admit011_oracle_equivalence",
    "_project_admit011_exact13",
    "_evaluate_registered_admit_011",
)
RUNTIME_SOURCE_DEFINITION_ORDER = (
    "_raise_dispatch_error",
    "_admit011_context_failure",
    "_admit011_adapter_failure",
    "_admit011_candidate_invalid",
    "_prevalidate_admit011_source",
    "_expected_admit011_from_oracle",
    "_validate_admit011_oracle_equivalence",
    "_project_admit011_exact13",
    "_evaluate_registered_admit_011",
    "evaluate_admission_rule",
)
EXPECTED_RUNTIME_DEFINITION_AST_SHA256 = {
    "evaluate_admission_rule": "11740861a0117d11a4fc64f9ead737a39010fdd957dbae2c2cf92e594c157548",
    "_raise_dispatch_error": "adb1d13a5bea21730e5d56742c1ba46faa30b5c31d80f827a892de73cc6e1356",
    "_admit011_context_failure": "b8f79418a5c7ac9c0ab746ccbcfdd2db09dd5fd88164f0379cd7990715eec237",
    "_admit011_adapter_failure": "f5e0ffb443aa5213f02e976e10da2f900e46e1634299a30d16bcbcb294a97a8a",
    "_admit011_candidate_invalid": "ccdb8c278eb486cf47dc09b41cdc91baf2df29a6e144d2871af77c55df752067",
    "_prevalidate_admit011_source": "3255e9a9603226375049d0b35abd0028c5ec67b12fe524595a50cabd9bb59da5",
    "_expected_admit011_from_oracle": "2b946d1772083ff244a9ea3d97be660048c48cee1ea06e0f1d7290b993af55a6",
    "_validate_admit011_oracle_equivalence": "3f75097ae9292f582d68d3f5ad33c275ff2f02e852bcd7f95b424fbfa104567c",
    "_project_admit011_exact13": "80d92d3210ddfb7483660aa360678b376450be4e12c9e8987aa4b4aff1b525ef",
    "_evaluate_registered_admit_011": "1f56e6b007f7c33e480e9b720a97db8236fa7bb6de7cb6b78b16a8d0bf94cbd4",
}

EXPECTED_RUNTIME_IMPORTS = (
    ("from", "__future__", "annotations", ""),
    ("import", "", "ast", ""),
    ("import", "", "csv", ""),
    ("import", "", "ctypes", ""),
    ("import", "", "hashlib", ""),
    ("import", "", "inspect", ""),
    ("import", "", "io", ""),
    ("import", "", "json", ""),
    ("import", "", "os", ""),
    ("import", "", "secrets", ""),
    ("import", "", "stat", ""),
    ("import", "", "subprocess", ""),
    ("from", "collections", "Counter", ""),
    ("from", "collections.abc", "Mapping", ""),
    ("from", "collections.abc", "Sequence", ""),
    ("from", "dataclasses", "dataclass", ""),
    ("from", "dataclasses", "fields", ""),
    ("from", "pathlib", "Path", ""),
    ("from", "types", "MappingProxyType", ""),
    ("from", "typing", "Any", ""),
    ("from", "typing", "NoReturn", ""),
    ("from", "covalent_ext", "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010", "predecessor"),
    ("from", "covalent_ext", "covapie_bulk_download_admission_admit_011_rule_logic_interface", "admit011"),
    ("from", "covalent_ext", "covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate", "admit011_oracle"),
)
PROJECT_IMPORT_PROVENANCE = {
    "predecessor": "covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010",
    "admit011": "covalent_ext.covapie_bulk_download_admission_admit_011_rule_logic_interface",
    "admit011_oracle": "covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate",
}

PROTECTED_RUNTIME_BINDINGS = RUNTIME_DEFINITION_NAMES + (
    "predecessor", "admit011", "admit011_oracle", "Mapping", "fields",
    "UnifiedAdmissionRuleEvaluation", "UnifiedAdmissionDispatchError",
    "RESULT_SCHEMA_VERSION", "RESULT_FIELDS", "DISPATCH_ERROR_FIELDS",
    "DISPATCH_ERROR_CODES", "OUTCOME_VOCABULARY", "KNOWN_RULE_IDS",
    "CALLABLE_DISCOVERED_RULE_IDS", "ADAPTER_READY_RULE_IDS",
    "LEGACY_ADAPTER_NOT_READY_RULE_IDS", "ADMISSION_RULE_ID",
    "ADMISSION_RULE_NAME", "ADAPTER_ID", "ADMIT_011_CANDIDATE_FIELDS",
    "ADMIT_011_CONTEXT_ITEMS", "RULE_NAMES", "ADAPTER_IDS",
    "EVALUATOR_REGISTRY",
)
EXPECTED_PROTECTED_BINDING_AST_SHA256 = {
    **EXPECTED_RUNTIME_DEFINITION_AST_SHA256,
    "predecessor": "ac683e7ace9f0157b0229d7695337d39108884144b2fbf5623ed5fa8e90843e0",
    "admit011": "3f6577ce57ac448d2b12c6242de97abb7721705d6561a600d444a2248ed0ce89",
    "admit011_oracle": "7a7dc45fd74450590c7187d8d7450e4592244b26ea8923cc8dae6f75007f08cc",
    "Mapping": "30311c3c6d5e6f6b3e2d229eaebd5ffb8bebdef309d4602d268cf5ed45badc57",
    "fields": "32df2ff93c2afdfbfcb2167378b0c1c9343e34ea67e571363bbc10189e991aca",
    "UnifiedAdmissionRuleEvaluation": "14481f1f96ddb2b3069709576855a7ebe6349cc787906aa93f0921338bda9bde",
    "UnifiedAdmissionDispatchError": "6bbdb088bdac8e4e5b9fd07ea006739d32eb0e7b8905c8ecb38ee27ca8e3dccb",
    "RESULT_SCHEMA_VERSION": "ae1c24267e00b68c35d07071467f4369a6fea14e5bd3aeec6797fcac163290ee",
    "RESULT_FIELDS": "dae7366fd4b384906d5f7672ca7f2e03590e2384c7781e8eccadf715a8b3d6d1",
    "DISPATCH_ERROR_FIELDS": "f2278551bbe241569bce9575373cd927c2e51ec717adecee94c09020ad1c7de4",
    "DISPATCH_ERROR_CODES": "cfa02f1ff0a0a1a569e41629f7e7ef0275c26b8b6e2b52bdbb110942c731aa52",
    "OUTCOME_VOCABULARY": "1bdebe385bdc981289cf2297f25c544222cfdc5d9b051d7f1efd3ffd7e90c4c1",
    "KNOWN_RULE_IDS": "1dff4d50414236c713f3dc6c2c3a62a7f6706c1cbffcb5ae080b9d7c702e8939",
    "CALLABLE_DISCOVERED_RULE_IDS": "670dc6f8c5dee9a416b7d5bef5964f4bb4f44f455a9be5df15e4058f680923f3",
    "ADAPTER_READY_RULE_IDS": "6e074736bc5c5143cf0d0ff7f7d133da074b81b477b23111b0b8b155a84c9232",
    "LEGACY_ADAPTER_NOT_READY_RULE_IDS": "80e74c8c64fb7340d0bdac9c9d31bcbb875332aa64e85dd2a62fae541417cdc6",
    "ADMISSION_RULE_ID": "59aa8e1301690c43f40c96a25927f7a81c4210a483a017c40b1a30693a1567be",
    "ADMISSION_RULE_NAME": "878fc6eff4b26536212c2e56822d97e8f3c5350cac68c76ca96ddf12328db673",
    "ADAPTER_ID": "e87dd02e3e18f835537aa0ab96490c4cc84919fab0a106c58d9aa36bd2aeff24",
    "ADMIT_011_CANDIDATE_FIELDS": "bff9a839c28b51b35b492d028f83e8aba8952b9f46519f4bbeef427c3969cb3f",
    "ADMIT_011_CONTEXT_ITEMS": "b9c30b0e77aace9dc6c5f7274b92e1d859513ff5ef4921faa7d5ad9694e2f4d4",
    "RULE_NAMES": "9410ac00ffd9888b81f6f7a67cd4abd98756a42d3dd09ae2b849fe3c55527167",
    "ADAPTER_IDS": "88525954b848e115f608b1461cb54fbb082a1708b8a95df298054bf3f0e9fa53",
    "EVALUATOR_REGISTRY": "e933760bd8d90b99df967bd2373fb5e63598cbf8a7eaa502a46c5c907c3765f7",
}


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _semantic_sha(value: object) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _git(*arguments: str) -> bytes:
    result = subprocess.run(
        ("git", *arguments), cwd=ROOT, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise AssertionError("source-boundary git command failed")
    return result.stdout


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return int(item.st_dev), int(item.st_ino), int(item.st_mode)


def _ast_sha(node: ast.AST) -> str:
    normalized = ast.dump(node, annotate_fields=True, include_attributes=False)
    return _sha(normalized.encode("utf-8"))


def _parent_chain(parent: Path, anchor: Path) -> None:
    current = parent
    while True:
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise AssertionError("parent chain unsafe")
        if current == anchor:
            break
        if current == current.parent:
            raise AssertionError("parent chain escaped")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise AssertionError("parent chain resolved drift")


def _read_descriptor(descriptor: int) -> bytes:
    chunks = []
    while True:
        chunk = os.read(descriptor, 1 << 16)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _attest_successor_source_before_import(
    repo_root: Path = ROOT,
    *,
    relative_path: Path = SUCCESSOR_SOURCE_RELATIVE_PATH,
    expected_sha256: str = EXPECTED_SUCCESSOR_SOURCE_SHA256,
    event_hook: Any = None,
) -> dict[str, Any]:
    """Attest the untracked successor structurally and by pinned bytes."""
    root = Path(os.path.abspath(repo_root))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise AssertionError("successor repository root unsafe")
    relative = Path(relative_path)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise AssertionError("successor relative path unsafe")
    target = root / relative
    if root not in target.parents:
        raise AssertionError("successor escaped repository")
    _parent_chain(target.parent, root)
    item = os.lstat(target)
    identity = _identity(item)
    if (
        not stat.S_ISREG(item.st_mode)
        or stat.S_ISLNK(item.st_mode)
        or target.resolve(strict=True) != target
    ):
        raise AssertionError("successor source leaf unsafe")
    if event_hook is not None:
        event_hook("before_open", target=target, identity=identity)
    descriptor = os.open(
        target,
        os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        if _identity(os.fstat(descriptor)) != identity:
            raise AssertionError("successor descriptor identity drift")
        content = _read_descriptor(descriptor)
        if event_hook is not None:
            event_hook("after_read", target=target, identity=identity)
        if (
            _identity(os.fstat(descriptor)) != identity
            or _identity(os.lstat(target)) != identity
        ):
            raise AssertionError("successor source changed during read")
    finally:
        os.close(descriptor)
    if _identity(os.lstat(root)) != root_identity:
        raise AssertionError("successor repository root identity drift")
    _parent_chain(target.parent, root)
    actual_sha256 = _sha(content)
    if actual_sha256 != expected_sha256:
        raise AssertionError("successor source SHA mismatch")
    tree = ast.parse(content, filename=str(target))
    return {
        "repo_root": root,
        "relative_path": relative,
        "path": target,
        "root_identity": root_identity,
        "identity": identity,
        "sha256": actual_sha256,
        "content": content,
        "tree": tree,
        "pinned_fd_read": True,
    }


def _assert_attested_successor_unchanged(attested: Mapping[str, Any]) -> None:
    root = attested["repo_root"]
    target = attested["path"]
    if _identity(os.lstat(root)) != attested["root_identity"]:
        raise AssertionError("attested repository root changed")
    _parent_chain(target.parent, root)
    item = os.lstat(target)
    if (
        _identity(item) != attested["identity"]
        or not stat.S_ISREG(item.st_mode)
        or stat.S_ISLNK(item.st_mode)
        or target.resolve(strict=True) != target
    ):
        raise AssertionError("attested successor lexical identity changed")
    descriptor = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if _identity(os.fstat(descriptor)) != attested["identity"]:
            raise AssertionError("attested successor descriptor changed")
        content = _read_descriptor(descriptor)
        if (
            _identity(os.fstat(descriptor)) != attested["identity"]
            or _identity(os.lstat(target)) != attested["identity"]
        ):
            raise AssertionError("attested successor changed during recheck")
    finally:
        os.close(descriptor)
    if content != attested["content"] or _sha(content) != attested["sha256"]:
        raise AssertionError("attested successor bytes changed")


def _verify_sources() -> tuple[dict[str, Any], ...]:
    if len(SOURCE_BOUNDARY) != 23 or len({path for path, _ in SOURCE_BOUNDARY}) != 23:
        raise AssertionError("Exact23 source boundary drift")
    if _git("show", "-s", "--format=%s", BASE).decode().rstrip("\n") != SUBJECT:
        raise AssertionError("base subject mismatch")
    _git("merge-base", "--is-ancestor", BASE, "HEAD")
    root = Path(os.path.abspath(ROOT))
    if root.resolve(strict=True) != root:
        raise AssertionError("repository identity drift")
    inspected = []
    for relative, expected in SOURCE_BOUNDARY:
        path = Path(relative)
        if (
            path.is_absolute() or not path.parts or ".." in path.parts
            or path.parts[:2] == ("data", "raw") or path.parts[0] == "checkpoints"
            or STAGE in path.parts
        ):
            raise AssertionError("unsafe source boundary path")
        target = root / path
        _parent_chain(target.parent, root)
        item = os.lstat(target)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode) or target.resolve(strict=True) != target:
            raise AssertionError("source leaf unsafe")
        if _git("ls-files", "--error-unmatch", "--", relative).decode() != f"{relative}\n":
            raise AssertionError("source not tracked")
        tree = _git("ls-tree", BASE, "--", relative).splitlines()
        if len(tree) != 1 or b"\t" not in tree[0]:
            raise AssertionError("base tree cardinality")
        metadata, tree_path = tree[0].split(b"\t", 1)
        parts = metadata.split()
        if tree_path.decode() != relative or len(parts) != 3 or parts[0] not in (b"100644", b"100755") or parts[1] != b"blob":
            raise AssertionError("base tree entry")
        inspected.append((relative, expected, target, _identity(item), parts[0].decode()))
    verified = []
    for index, (relative, expected, target, identity, mode) in enumerate(inspected, 1):
        descriptor = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            if _identity(os.fstat(descriptor)) != identity or _identity(os.lstat(target)) != identity:
                raise AssertionError("source descriptor identity")
            chunks = []
            while True:
                chunk = os.read(descriptor, 1 << 16)
                if not chunk:
                    break
                chunks.append(chunk)
            if _identity(os.fstat(descriptor)) != identity or _identity(os.lstat(target)) != identity:
                raise AssertionError("source changed during read")
        finally:
            os.close(descriptor)
        filesystem = b"".join(chunks)
        base_bytes = _git("show", f"{BASE}:{relative}")
        if expected != _sha(filesystem) or expected != _sha(base_bytes):
            raise AssertionError(f"source SHA mismatch: {relative}")
        verified.append({
            "source_order": index, "source_relative_path": relative,
            "tracked": True, "base_tree_blob": True, "base_tree_mode": mode,
            "filesystem_regular": True, "non_symlink": True,
            "parent_chain_non_symlink": True, "safe_descendant": True,
            "expected_sha256": expected, "base_tree_sha256": expected,
            "filesystem_sha256": expected, "pinned_fd_read": True,
            "source_verified": True, "content": filesystem,
        })
    return tuple(verified)


def _csv(content: bytes, columns: Sequence[str]) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != tuple(columns):
        raise AssertionError("CSV header mismatch")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(columns) or any(value is None for value in row.values()) for row in rows):
        raise AssertionError("CSV row shape mismatch")
    return rows


def _output_bytes(
    output_root: Path,
    *,
    event_hook: Any = None,
) -> dict[str, bytes]:
    """Read an Exact6 tree only through identities frozen before any bytes."""
    root = Path(os.path.abspath(output_root))
    _parent_chain(root.parent, Path(root.anchor))
    parent_identity = _identity(os.lstat(root.parent))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise AssertionError("output root unsafe")
    names = tuple(os.listdir(root))
    if len(names) != len(OUTPUTS) or set(names) != set(OUTPUTS):
        raise AssertionError("output inventory")
    leaf_identities = {}
    for name in OUTPUTS:
        target = root / name
        item = os.lstat(target)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or target.resolve(strict=True) != target
        ):
            raise AssertionError("output leaf type")
        leaf_identities[name] = _identity(item)
    if event_hook is not None:
        event_hook("after_preflight", root=root, identities=dict(leaf_identities))
    descriptor = os.open(
        root,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        if (
            _identity(os.fstat(descriptor)) != root_identity
            or _identity(os.lstat(root)) != root_identity
        ):
            raise AssertionError("pinned output root identity")
        descriptor_names = tuple(os.listdir(descriptor))
        if len(descriptor_names) != len(OUTPUTS) or set(descriptor_names) != set(OUTPUTS):
            raise AssertionError("pinned output inventory")
        contents = {}
        for name in OUTPUTS:
            leaf_item = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if (
                _identity(leaf_item) != leaf_identities[name]
                or not stat.S_ISREG(leaf_item.st_mode)
                or stat.S_ISLNK(leaf_item.st_mode)
            ):
                raise AssertionError("pinned output leaf identity")
            if event_hook is not None:
                event_hook(
                    "before_leaf_open",
                    root=root,
                    name=name,
                    identity=leaf_identities[name],
                )
            leaf = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=descriptor)
            try:
                if _identity(os.fstat(leaf)) != leaf_identities[name]:
                    raise AssertionError("output leaf descriptor identity")
                chunks = []
                hook_called = False
                while True:
                    chunk = os.read(leaf, 1 << 16)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if event_hook is not None and not hook_called:
                        hook_called = True
                        event_hook(
                            "during_leaf_read",
                            root=root,
                            name=name,
                            identity=leaf_identities[name],
                        )
                if (
                    _identity(os.fstat(leaf)) != leaf_identities[name]
                    or _identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False))
                    != leaf_identities[name]
                ):
                    raise AssertionError("output leaf changed during read")
                contents[name] = b"".join(chunks)
            finally:
                os.close(leaf)
        if event_hook is not None:
            event_hook("before_final_validation", root=root, identities=dict(leaf_identities))
        _parent_chain(root.parent, Path(root.anchor))
        if (
            _identity(os.lstat(root.parent)) != parent_identity
            or _identity(os.fstat(descriptor)) != root_identity
            or _identity(os.lstat(root)) != root_identity
        ):
            raise AssertionError("output tree identity changed")
        final_names = tuple(os.listdir(descriptor))
        if len(final_names) != len(OUTPUTS) or set(final_names) != set(OUTPUTS):
            raise AssertionError("output inventory changed during read")
        for name in OUTPUTS:
            if (
                _identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False))
                != leaf_identities[name]
            ):
                raise AssertionError("output leaf identity changed after read")
        return contents
    finally:
        os.close(descriptor)


def _verify_runtime_identity(runtime: Any) -> None:
    predecessor = runtime.predecessor
    for name in (
        "UnifiedAdmissionRuleEvaluation", "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION", "RESULT_FIELDS", "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES", "OUTCOME_VOCABULARY",
    ):
        if getattr(runtime, name) is not getattr(predecessor, name):
            raise AssertionError(f"public identity drift: {name}")
    if runtime.evaluate_admission_rule is predecessor.evaluate_admission_rule:
        raise AssertionError("successor dispatcher object reused")
    if inspect.signature(runtime.evaluate_admission_rule) != inspect.signature(predecessor.evaluate_admission_rule):
        raise AssertionError("dispatcher signature drift")
    if runtime.evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"] is not runtime.EVALUATOR_REGISTRY:
        raise AssertionError("dispatcher local registry binding drift")
    if type(runtime.EVALUATOR_REGISTRY) is not MappingProxyType or tuple(runtime.EVALUATOR_REGISTRY) != REGISTERED_IDS:
        raise AssertionError("Exact11 registry drift")
    if any(runtime.EVALUATOR_REGISTRY[rule] is not predecessor.EVALUATOR_REGISTRY[rule] for rule in KNOWN_IDS[:10]):
        raise AssertionError("first-ten handler identity drift")
    if runtime.EVALUATOR_REGISTRY[RULE_ID] is not runtime._evaluate_registered_admit_011:
        raise AssertionError("new ADMIT_011 handler identity drift")
    if tuple(runtime.KNOWN_RULE_IDS) != KNOWN_IDS or tuple(runtime.CALLABLE_DISCOVERED_RULE_IDS) != REGISTERED_IDS:
        raise AssertionError("known/callable rule IDs drift")
    if tuple(runtime.ADAPTER_READY_RULE_IDS) != REGISTERED_IDS or tuple(runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS) != ():
        raise AssertionError("adapter-ready IDs drift")
    if type(runtime.RULE_NAMES) is not MappingProxyType or dict(runtime.RULE_NAMES) != EXPECTED_RULE_NAMES:
        raise AssertionError("rule name mapping drift")
    if type(runtime.ADAPTER_IDS) is not MappingProxyType or dict(runtime.ADAPTER_IDS) != EXPECTED_ADAPTER_IDS:
        raise AssertionError("adapter ID mapping drift")
    if hasattr(runtime, "evaluate_all_rules") or hasattr(runtime, "combined_candidate_verdict"):
        raise AssertionError("aggregation leaked")


def _target_names(target: ast.AST) -> tuple[str, ...]:
    if isinstance(target, ast.Name):
        return (target.id,)
    if isinstance(target, (ast.Tuple, ast.List)):
        return tuple(name for item in target.elts for name in _target_names(item))
    return ()


def _module_binding_records(tree: ast.Module) -> dict[str, tuple[str, ...]]:
    protected = set(PROTECTED_RUNTIME_BINDINGS)
    records: dict[str, list[str]] = {name: [] for name in PROTECTED_RUNTIME_BINDINGS}

    def record(names: Sequence[str], node: ast.AST) -> None:
        digest = _ast_sha(node)
        for name in names:
            if name in protected:
                records[name].append(digest)

    def expression_targets(expression: ast.AST) -> None:
        for child in ast.walk(expression):
            if isinstance(child, ast.NamedExpr):
                record(_target_names(child.target), child)
            elif isinstance(child, ast.comprehension):
                record(_target_names(child.target), child)

    def statements(items: Sequence[ast.stmt]) -> None:
        for node in items:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                record((node.name,), node)
                for decorator in node.decorator_list:
                    expression_targets(decorator)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                record(
                    tuple(alias.asname or alias.name.split(".")[0] for alias in node.names),
                    node,
                )
            elif isinstance(node, ast.Assign):
                record(tuple(name for target in node.targets for name in _target_names(target)), node)
                expression_targets(node.value)
            elif isinstance(node, ast.AnnAssign):
                record(_target_names(node.target), node)
                if node.value is not None:
                    expression_targets(node.value)
            elif isinstance(node, ast.AugAssign):
                record(_target_names(node.target), node)
                expression_targets(node.value)
            elif isinstance(node, ast.Delete):
                record(tuple(name for target in node.targets for name in _target_names(target)), node)
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                record(_target_names(node.target), node)
                expression_targets(node.iter)
                statements(node.body)
                statements(node.orelse)
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if item.optional_vars is not None:
                        record(_target_names(item.optional_vars), node)
                    expression_targets(item.context_expr)
                statements(node.body)
            elif isinstance(node, ast.Try):
                statements(node.body)
                for handler in node.handlers:
                    if handler.name is not None:
                        record((handler.name,), handler)
                    statements(handler.body)
                statements(node.orelse)
                statements(node.finalbody)
            elif isinstance(node, (ast.If, ast.While)):
                expression_targets(node.test)
                statements(node.body)
                statements(node.orelse)
            elif isinstance(node, ast.Match):
                expression_targets(node.subject)
                for case in node.cases:
                    if case.guard is not None:
                        expression_targets(case.guard)
                    statements(case.body)
            else:
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.expr):
                        expression_targets(child)

    statements(tree.body)
    return {name: tuple(values) for name, values in records.items()}


def _runtime_import_inventory(tree: ast.Module) -> tuple[tuple[str, str, str, str], ...]:
    module_import_nodes = {
        id(node) for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
    }
    if any(
        isinstance(node, (ast.Import, ast.ImportFrom)) and id(node) not in module_import_nodes
        for node in ast.walk(tree)
    ):
        raise AssertionError("reachable or nested import forbidden")
    inventory = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            inventory.extend(("import", "", alias.name, alias.asname or "") for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            inventory.extend(
                ("from", node.module or "", alias.name, alias.asname or "")
                for alias in node.names
            )
    return tuple(inventory)


def _verify_closed_world_calls(functions: Mapping[str, ast.FunctionDef]) -> None:
    allowed_name_calls = set(RUNTIME_DEFINITION_NAMES) | {
        "UnifiedAdmissionDispatchError", "UnifiedAdmissionRuleEvaluation",
        "TypeError", "ValueError", "any", "fields", "getattr", "isinstance",
        "tuple", "type", "vars", "zip", "result_type",
    }
    allowed_attribute_calls = {
        "admit011.Admit011EvaluationResult",
        "admit011.evaluate_admit_011",
        "admit011_oracle.classify_admit_011_raw_target_relative_path_design",
    }
    canonical_registry_call = "EVALUATOR_REGISTRY[admission_rule_id]"
    for function_name in RUNTIME_DEFINITION_NAMES:
        function = functions[function_name]
        for node in ast.walk(function):
            if isinstance(node, (ast.Global, ast.Nonlocal, ast.Import, ast.ImportFrom, ast.With, ast.AsyncWith)):
                raise AssertionError(f"public closure mutation/import construct: {function_name}")
            if isinstance(node, (ast.Attribute, ast.Subscript)) and isinstance(node.ctx, (ast.Store, ast.Del)):
                raise AssertionError(f"public closure object mutation: {function_name}")
            if not isinstance(node, ast.Call):
                continue
            callable_node = node.func
            if isinstance(callable_node, ast.Name):
                if callable_node.id not in allowed_name_calls:
                    raise AssertionError(
                        f"public closure unknown local/dynamic callable: {callable_node.id}"
                    )
                if callable_node.id == "result_type" and function_name != "_expected_admit011_from_oracle":
                    raise AssertionError("result_type callable outside frozen oracle helper")
            elif isinstance(callable_node, ast.Attribute):
                dotted = ast.unparse(callable_node)
                if dotted not in allowed_attribute_calls:
                    raise AssertionError(f"public closure imported/module callable forbidden: {dotted}")
            elif isinstance(callable_node, ast.Subscript):
                rendered = ast.unparse(callable_node)
                if function_name != "evaluate_admission_rule" or rendered != canonical_registry_call:
                    raise AssertionError(f"public closure subscript callable forbidden: {rendered}")
            else:
                raise AssertionError(
                    f"public closure dynamic callable forbidden: {type(callable_node).__name__}"
                )


def _verify_runtime_ast(attested: Mapping[str, Any] | bytes) -> None:
    if isinstance(attested, bytes):
        content = attested
        tree = ast.parse(content)
    else:
        content = attested["content"]
        tree = attested["tree"]
    source = content.decode("utf-8")
    if _runtime_import_inventory(tree) != EXPECTED_RUNTIME_IMPORTS:
        raise AssertionError("successor import inventory/provenance drift")
    definitions: dict[str, list[ast.AST]] = {name: [] for name in RUNTIME_DEFINITION_NAMES}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in definitions:
            definitions[node.name].append(node)
    if any(
        len(nodes) != 1 or not isinstance(nodes[0], ast.FunctionDef)
        for nodes in definitions.values()
    ):
        raise AssertionError("Exact10 runtime definition cardinality/type drift")
    functions = {name: nodes[0] for name, nodes in definitions.items()}
    actual_source_order = tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in definitions
    )
    if actual_source_order != RUNTIME_SOURCE_DEFINITION_ORDER:
        raise AssertionError("Exact10 runtime definition source order drift")
    _verify_closed_world_calls(functions)
    binding_records = _module_binding_records(tree)
    expected_records = {
        name: (EXPECTED_PROTECTED_BINDING_AST_SHA256[name],)
        for name in PROTECTED_RUNTIME_BINDINGS
    }
    if binding_records != expected_records:
        raise AssertionError("protected runtime binding provenance/rebinding drift")
    decorators = {
        node.name: tuple(ast.unparse(item) for item in node.decorator_list)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.decorator_list
    }
    if decorators != {
        "FrozenSourceRecord": ("dataclass(frozen=True)",),
        "FrozenSourceSnapshot": ("dataclass(frozen=True)",),
        "OutputMaterializationPlan": ("dataclass(frozen=True)",),
    }:
        raise AssertionError("module decorator execution surface drift")
    top_level_expressions = [node for node in tree.body if isinstance(node, ast.Expr)]
    if (
        len(top_level_expressions) != 1
        or not isinstance(top_level_expressions[0].value, ast.Constant)
        or type(top_level_expressions[0].value.value) is not str
    ):
        raise AssertionError("module import-time expression surface drift")
    actual_ast_sha = {name: _ast_sha(functions[name]) for name in RUNTIME_DEFINITION_NAMES}
    if actual_ast_sha != EXPECTED_RUNTIME_DEFINITION_AST_SHA256:
        raise AssertionError("Exact10 normalized definition AST SHA drift")
    runner = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1"
    )
    runner_source = ast.get_source_segment(source, runner)
    if runner_source is None:
        raise AssertionError("runner source unavailable")
    order = (
        "_inspect_output_target_read_only(", "build_frozen_source_snapshot(",
        "build_runtime_state(", "_payloads(", "_materialize_set(",
    )
    positions = tuple(runner_source.index(token) for token in order)
    if positions != tuple(sorted(positions)):
        raise AssertionError("preflight/source/payload/publication order drift")
    for token in (
        "O_EXCL", "O_NOFOLLOW", "os.fsync", "RENAME_NOREPLACE",
        "_rename_noreplace", "repair forbidden", "_cleanup_staging",
    ):
        if token not in source:
            raise AssertionError(f"set-atomic materializer token missing: {token}")


def _verify_imported_successor(
    runtime: Any,
    attested: Mapping[str, Any],
    source_records: Sequence[Mapping[str, Any]] | None = None,
) -> None:
    module_path = Path(os.path.abspath(runtime.__file__))
    if module_path != attested["path"]:
        raise AssertionError("imported successor module path mismatch")
    if runtime.__spec__ is None or Path(os.path.abspath(runtime.__spec__.origin)) != attested["path"]:
        raise AssertionError("imported successor spec origin mismatch")
    if sys.modules.get(MODULE) is not runtime:
        raise AssertionError("imported successor module object identity mismatch")
    _assert_attested_successor_unchanged(attested)
    if source_records is None:
        return
    dependency_indices = {"predecessor": 0, "admit011": 7, "admit011_oracle": 20}
    for alias, module_name in PROJECT_IMPORT_PROVENANCE.items():
        value = getattr(runtime, alias)
        if sys.modules.get(module_name) is not value:
            raise AssertionError(f"project dependency module identity drift: {alias}")
        expected_path = ROOT / source_records[dependency_indices[alias]]["source_relative_path"]
        if Path(os.path.abspath(value.__file__)) != expected_path:
            raise AssertionError(f"project dependency module path drift: {alias}")


def _import_attested_successor(
    attested: Mapping[str, Any],
    source_records: Sequence[Mapping[str, Any]],
    *,
    importer: Any = importlib.import_module,
    before_import_hook: Any = None,
) -> Any:
    if before_import_hook is not None:
        before_import_hook()
    _assert_attested_successor_unchanged(attested)
    runtime = importer(MODULE)
    _verify_imported_successor(runtime, attested, source_records)
    return runtime


class _CountingMapping(Mapping):
    def __init__(self, values: Mapping[str, object], error: Exception | None = None) -> None:
        self.values = dict(values)
        self.error = error
        self.calls: list[object] = []
        self.iterated = False
        self.get_called = False
        self.contains_called = False
        self.len_called = False

    def __getitem__(self, key: str) -> object:
        self.calls.append(key)
        if self.error is not None:
            raise self.error
        return self.values[key]

    def __iter__(self):
        self.iterated = True
        return iter(self.values)

    def __len__(self) -> int:
        self.len_called = True
        return len(self.values)

    def get(self, key: str, default: object = None) -> object:
        self.get_called = True
        return super().get(key, default)

    def __contains__(self, key: object) -> bool:
        self.contains_called = True
        return super().__contains__(key)


class _Bomb(Mapping):
    def __getitem__(self, key: str) -> object:
        raise AssertionError("candidate accessed")

    def __iter__(self):
        raise AssertionError("candidate iterated")

    def __len__(self) -> int:
        raise AssertionError("candidate sized")


def _route(runtime: Any, candidate: object, **overrides: object) -> Any:
    kwargs = {
        "batch_context": None,
        "evaluation_context": {
            CONTEXT_ITEMS[0]: runtime.admit011_oracle.DEFAULT_CONTRACT,
            CONTEXT_ITEMS[1]: runtime.admit011._empty_snapshot(),
        },
        "download_result_context": None,
        "stage_authorization_context": None,
    }
    kwargs.update(overrides)
    return runtime.evaluate_admission_rule(RULE_ID, candidate, **kwargs)


def _verify_runtime_behavior(runtime: Any) -> None:
    context_cases = (
        ({"batch_context": object()}, "ADMIT_011_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": object()}, "ADMIT_011_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": {}}, "ADMIT_011_RAW_TARGET_RELATIVE_PATH_CONTRACT_REQUIRED"),
        ({"evaluation_context": {CONTEXT_ITEMS[0]: object()}}, "ADMIT_011_EXISTING_RAW_TARGET_RELATIVE_PATHS_REQUIRED"),
        ({"download_result_context": object()}, "ADMIT_011_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ({"stage_authorization_context": object()}, "ADMIT_011_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    )
    for overrides, reason in context_cases:
        try:
            _route(runtime, _Bomb(), **overrides)
        except runtime.UnifiedAdmissionDispatchError as error:
            actual = tuple(getattr(error, name) for name in ERROR_FIELDS)
            expected = (
                "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", RULE_ID,
                True, True, True, reason,
            )
            if actual != expected:
                raise AssertionError("context routing failure drift")
        else:
            raise AssertionError("context routing failure missing")

    contract = runtime.admit011_oracle.DEFAULT_CONTRACT
    snapshot = runtime.admit011._empty_snapshot()
    candidate = _CountingMapping({CANDIDATE_FIELDS[0]: "data/raw/a.cif", "extra": object()})
    context = _CountingMapping({CONTEXT_ITEMS[0]: contract, CONTEXT_ITEMS[1]: snapshot, "extra": object()})
    result = _route(runtime, candidate, evaluation_context=context)
    if result.outcome != "passed" or candidate.calls != list(CANDIDATE_FIELDS) or context.calls != list(CONTEXT_ITEMS):
        raise AssertionError("direct lookup or Mapping-subclass behavior drift")
    if any((candidate.iterated, context.iterated, candidate.get_called, context.get_called,
            candidate.contains_called, context.contains_called, candidate.len_called, context.len_called)):
        raise AssertionError("forbidden Mapping operation")
    for location in ("context", "candidate"):
        sentinel = RuntimeError(location)
        try:
            _route(
                runtime,
                _CountingMapping({}, sentinel) if location == "candidate" else {},
                evaluation_context=(
                    _CountingMapping({}, sentinel)
                    if location == "context"
                    else {CONTEXT_ITEMS[0]: contract, CONTEXT_ITEMS[1]: snapshot}
                ),
            )
        except RuntimeError as error:
            if error is not sentinel:
                raise AssertionError("non-KeyError identity drift")
        else:
            raise AssertionError("non-KeyError swallowed")

    for candidate_value, reason in (
        (object(), "ADMIT_011_CANDIDATE_RECORD_MAPPING_INVALID"),
        ({}, "raw_target_relative_path_missing"),
    ):
        value = _route(runtime, candidate_value)
        expected = (
            runtime.RESULT_SCHEMA_VERSION, RULE_ID, RULE_NAME, "invalid", False,
            True, reason, (), (), CANDIDATE_FIELDS, CONTEXT_ITEMS, False, ADAPTER_ID,
        )
        if tuple(getattr(value, name) for name in RESULT_FIELDS) != expected:
            raise AssertionError("candidate invalid Exact13 drift")

    scalar = object()
    snapshot_object = object()
    contract_object = object()
    calls: list[tuple[str, tuple[object, ...]]] = []
    formal_original = runtime.admit011.evaluate_admit_011
    oracle_original = runtime.admit011_oracle.classify_admit_011_raw_target_relative_path_design

    def formal(*args: object) -> object:
        calls.append(("formal", args))
        return formal_original(*args)

    def oracle(*args: object) -> object:
        calls.append(("oracle", args))
        return oracle_original(*args)

    runtime.admit011.evaluate_admit_011 = formal
    runtime.admit011_oracle.classify_admit_011_raw_target_relative_path_design = oracle
    try:
        _route(
            runtime,
            {CANDIDATE_FIELDS[0]: scalar},
            evaluation_context={CONTEXT_ITEMS[0]: contract_object, CONTEXT_ITEMS[1]: snapshot_object},
        )
    finally:
        runtime.admit011.evaluate_admit_011 = formal_original
        runtime.admit011_oracle.classify_admit_011_raw_target_relative_path_design = oracle_original
    expected_args = (scalar, snapshot_object, contract_object)
    if [name for name, _ in calls] != ["formal", "oracle"] or any(
        any(actual is not expected for actual, expected in zip(args, expected_args, strict=True))
        for _, args in calls
    ):
        raise AssertionError("formal/oracle order, count, or identity drift")

    source = formal_original("data/raw/a.cif", snapshot, contract)
    class ResultSubclass(type(source)):
        pass
    subclass = object.__new__(ResultSubclass)
    for name in SOURCE_FIELDS:
        object.__setattr__(subclass, name, getattr(source, name))
    for bad, reason in (
        (object(), "ADMIT_011_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
        (subclass, "ADMIT_011_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
    ):
        try:
            runtime._prevalidate_admit011_source(bad)
        except runtime.UnifiedAdmissionDispatchError as error:
            if error.reason != reason or error.adapter_ready is not False:
                raise AssertionError("source type failure drift")
        else:
            raise AssertionError("source type failure missing")
    storage = formal_original("data/raw/a.cif", snapshot, contract)
    first = SOURCE_FIELDS[0]
    saved = vars(storage).pop(first)
    vars(storage)[first] = saved
    invariant = formal_original("data/raw/a.cif", snapshot, contract)
    object.__setattr__(invariant, "evaluator_io_used", True)
    for bad in (storage, invariant):
        try:
            runtime._prevalidate_admit011_source(bad)
        except runtime.UnifiedAdmissionDispatchError as error:
            if error.reason != "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID":
                raise AssertionError("source invariant failure drift")
        else:
            raise AssertionError("source invariant failure missing")
    if tuple(field.name for field in fields(runtime.admit011.Admit011EvaluationResult)) != SOURCE_FIELDS:
        raise AssertionError("formal Exact10 dataclass order drift")

    oracle_value = oracle_original("data/raw/a.cif", snapshot, contract)
    if type(oracle_value) is not runtime.admit011_oracle.Admit011EvaluationResultDesign:
        raise AssertionError("oracle exact dataclass type drift")
    expected = runtime._expected_admit011_from_oracle("data/raw/a.cif", snapshot, contract)
    runtime._validate_admit011_oracle_equivalence(source, expected)
    mismatch = formal_original("docs/a", snapshot, contract)
    try:
        runtime._validate_admit011_oracle_equivalence(source, mismatch)
    except runtime.UnifiedAdmissionDispatchError as error:
        if error.reason != "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID":
            raise AssertionError("full Exact10 mismatch reason drift")
    else:
        raise AssertionError("full Exact10 mismatch accepted")


def _verify_predecessor_parity(runtime: Any) -> None:
    for rule_id in KNOWN_IDS[:10]:
        def observe(module: Any) -> tuple[str, tuple[object, ...]]:
            try:
                value = module.evaluate_admission_rule(rule_id, {})
            except runtime.UnifiedAdmissionDispatchError as error:
                return "error", tuple(getattr(error, name) for name in ERROR_FIELDS)
            return "result", tuple(getattr(value, name) for name in RESULT_FIELDS)
        if observe(runtime) != observe(runtime.predecessor):
            raise AssertionError(f"predecessor parity drift: {rule_id}")


def _verify_exact84(runtime: Any, source_records: tuple[dict[str, Any], ...]) -> None:
    standalone_rows = _csv(source_records[10]["content"], (
        "case_order", "case_id", "matrix_group", "candidate_representation",
        "contract_state", "snapshot_state", "admission_rule_id", "outcome",
        "passed", "blocks_candidate", "reason", "canonical_raw_target_relative_path",
        "validated_candidate_fields", "consumed_candidate_fields",
        "consumed_context_items", "evaluator_io_used", "expected_precedence", "truth_passed",
    ))
    if len(standalone_rows) != 84 or sum(row["case_id"].startswith("HIST_") for row in standalone_rows) != 47:
        raise AssertionError("Exact84/Exact47 source truth drift")
    for row in standalone_rows:
        scalar = ast.literal_eval(row["candidate_representation"])
        contract, snapshot = runtime.admit011._case_context(dict(row))
        value = runtime.evaluate_admission_rule(
            RULE_ID,
            {CANDIDATE_FIELDS[0]: scalar},
            evaluation_context={CONTEXT_ITEMS[0]: contract, CONTEXT_ITEMS[1]: snapshot},
        )
        validated = tuple(tuple(pair) for pair in json.loads(row["validated_candidate_fields"]))
        expected = (
            runtime.RESULT_SCHEMA_VERSION, RULE_ID, RULE_NAME, row["outcome"],
            row["passed"] == "true", row["blocks_candidate"] == "true",
            row["reason"], validated, validated,
            tuple(json.loads(row["consumed_candidate_fields"])),
            tuple(json.loads(row["consumed_context_items"])),
            row["evaluator_io_used"] == "true", ADAPTER_ID,
        )
        if tuple(getattr(value, name) for name in RESULT_FIELDS) != expected:
            raise AssertionError(f"Exact84 public projection drift: {row['case_id']}")


def _expected_registry_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for rule_id in KNOWN_IDS:
        registered = rule_id in REGISTERED_IDS
        rows.append({
            "rule_id": rule_id,
            "rule_name": EXPECTED_RULE_NAMES.get(rule_id, ""),
            "known_rule": "true",
            "callable_discovered": str(registered).lower(),
            "adapter_ready": str(registered).lower(),
            "registered": str(registered).lower(),
            "adapter_id": EXPECTED_ADAPTER_IDS.get(rule_id, ""),
            "handler_identity_status": (
                "reused_predecessor_handler_identity" if rule_id in KNOWN_IDS[:10]
                else "exact_new_admit011_handler" if rule_id == RULE_ID
                else "not_registered"
            ),
            "dispatch_disposition": "registered_local_handler" if registered else "not_registered",
            "audit_passed": "true",
        })
    return tuple(rows)


def _validate_output_tree(
    output_root: Path = OUTPUT_ROOT,
    *,
    enforce_frozen_hashes: bool = True,
    source_records: tuple[dict[str, Any], ...] | None = None,
) -> dict[str, str]:
    verified = _verify_sources() if source_records is None else source_records
    contents = _output_bytes(output_root)
    hashes = {name: _sha(content) for name, content in contents.items()}
    contract = _csv(contents[OUTPUTS[0]], CONTRACT_COLUMNS)
    truth = _csv(contents[OUTPUTS[1]], TRUTH_COLUMNS)
    registry = _csv(contents[OUTPUTS[2]], REGISTRY_COLUMNS)
    safety = _csv(contents[OUTPUTS[3]], SAFETY_COLUMNS)
    issues = _csv(contents[OUTPUTS[4]], ISSUE_COLUMNS)
    expected_counts = (36, 534, 15, 35, 11)
    if tuple(map(len, (contract, truth, registry, safety, issues))) != expected_counts:
        raise AssertionError("CSV exact row counts")
    if any(row["contract_passed"] != "true" for row in contract):
        raise AssertionError("contract status")
    expected_groups = {
        "predecessor_exact10_truth": 407, "global_dispatch": 9,
        "predecessor_handler_identity_and_parity": 10,
        "admit011_context_routing": 7, "admit011_mapping": 3,
        "admit011_candidate": 2, "admit011_standalone_exact84": 84,
        "admit011_source_oracle_failure": 12,
    }
    if Counter(row["case_group"] for row in truth) != expected_groups or any(row["case_passed"] != "true" for row in truth):
        raise AssertionError("truth natural counts/status")
    if tuple(row["case_order"] for row in truth) != tuple(str(index) for index in range(1, 535)):
        raise AssertionError("truth exact order")
    predecessor_truth = _csv(verified[3]["content"], (
        "case_id", "case_group", "admission_rule_id", "behavior",
        "expected_result_or_error", "observed_result_or_error", "expected_reason",
        "observed_reason", "formal_call_count", "oracle_call_count",
        "candidate_access_status", "predecessor_handler_identity_status", "case_passed",
    ))
    if tuple(row["case_id"] for row in truth[:407]) != tuple(f"EXACT10_{row['case_id']}" for row in predecessor_truth):
        raise AssertionError("predecessor Exact10 truth preservation")
    if registry != _expected_registry_rows():
        raise AssertionError("Exact15 registry complete equality")
    if any(row["safety_passed"] != "true" or row["expected_executed"] != row["observed_executed"] for row in safety):
        raise AssertionError("safety complete status")
    issue_map = {row["issue_id"]: row for row in issues}
    if (
        issue_map["RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED"]["status"] != "resolved"
        or issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] != "open"
        or issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] != "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
        or issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["integration_transition"] != "admit_011_implemented_and_removed_from_open_coverage_scope"
        or issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] != "open"
    ):
        raise AssertionError("Exact11 issue transition/state")
    semantic_hashes = {
        OUTPUTS[0]: _semantic_sha(contract), OUTPUTS[1]: _semantic_sha(truth),
        OUTPUTS[2]: _semantic_sha(registry), OUTPUTS[3]: _semantic_sha(safety),
        OUTPUTS[4]: _semantic_sha(issues),
    }
    if semantic_hashes != FROZEN_CSV_SEMANTIC_SHA256:
        raise AssertionError("CSV complete semantic equality")
    manifest = json.loads(contents[OUTPUTS[5]])
    if type(manifest) is not dict or _semantic_sha(manifest) != FROZEN_MANIFEST_SEMANTIC_SHA256:
        raise AssertionError("manifest complete semantic equality")
    readiness = {name: True for name in TRUE_READINESS} | {name: False for name in FALSE_READINESS}
    if manifest.get("readiness") != readiness or any(manifest.get(name) is not value for name, value in readiness.items()):
        raise AssertionError("manifest readiness")
    required_manifest = {
        "project": "CovaPIE", "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA, "expected_base_commit": BASE,
        "expected_base_subject": SUBJECT, "source_input_count": 23,
        "registered_rule_ids": list(REGISTERED_IDS),
        "known_not_registered_rule_ids": list(KNOWN_IDS[11:]),
        "registered_rule_count": 11, "adapter_design_gate_imported_by_runtime": False,
        "standalone_exact84_projection_count": 84,
        "standalone_historical_exact47_projection_count": 47,
        "issue_transition_count": 1, "admit_012_started": False,
        "evaluate_all_rules_implemented": False,
        "combined_candidate_verdict_implemented": False,
        "provider_mapping_validated": False, "ready_for_training": False,
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": "audit_covapie_admit_012_formal_evaluator_interface_preconditions_v1",
        "all_checks_passed": True,
    }
    if any(manifest.get(key) != value for key, value in required_manifest.items()):
        raise AssertionError("manifest required semantics")
    if manifest.get("source_input_paths") != [path for path, _ in SOURCE_BOUNDARY] or manifest.get("source_input_sha256") != dict(SOURCE_BOUNDARY):
        raise AssertionError("manifest source boundary")
    if manifest.get("output_sha256") != {name: hashes[name] for name in OUTPUTS[:5]}:
        raise AssertionError("manifest output SHA")
    if enforce_frozen_hashes and hashes != FROZEN_OUTPUT_SHA256:
        raise AssertionError("frozen output SHA")
    return hashes


def _verify_silent_import_subprocess(attested: Mapping[str, Any]) -> None:
    script = f"""
import hashlib
import importlib
import os
import stat
import sys
p = {str(attested['path'])!r}
before = os.lstat(p)
assert stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode)
fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
try:
    assert (os.fstat(fd).st_dev, os.fstat(fd).st_ino, os.fstat(fd).st_mode) == (before.st_dev, before.st_ino, before.st_mode)
    chunks = []
    while True:
        chunk = os.read(fd, 1 << 16)
        if not chunk:
            break
        chunks.append(chunk)
    assert (os.fstat(fd).st_dev, os.fstat(fd).st_ino, os.fstat(fd).st_mode) == (before.st_dev, before.st_ino, before.st_mode)
finally:
    os.close(fd)
assert hashlib.sha256(b''.join(chunks)).hexdigest() == {attested['sha256']!r}
sys.path.insert(0, {str(ROOT / 'src')!r})
importlib.import_module({MODULE!r})
"""
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        (sys.executable, "-B", "-c", script),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=environment,
    )
    if completed.returncode or completed.stdout or completed.stderr:
        raise AssertionError("successor subprocess import not silent")
    _assert_attested_successor_unchanged(attested)


def main() -> int:
    # Both predecessor and untracked successor attestation finish before import.
    source_records = _verify_sources()
    attested = _attest_successor_source_before_import()
    _verify_runtime_ast(attested)
    sys.path.insert(0, str(ROOT / "src"))
    runtime = _import_attested_successor(attested, source_records)
    _verify_runtime_identity(runtime)
    _verify_runtime_behavior(runtime)
    _verify_predecessor_parity(runtime)
    _verify_exact84(runtime, source_records)
    before = _output_bytes(OUTPUT_ROOT)
    _verify_silent_import_subprocess(attested)
    if _output_bytes(OUTPUT_ROOT) != before:
        raise AssertionError("runtime import side effect")
    hashes = _validate_output_tree(source_records=source_records)
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        first_root = Path(first) / "set"
        second_root = Path(second) / "set"
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(first_root, repo_root=ROOT)
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(second_root, repo_root=ROOT)
        first_bytes = _output_bytes(first_root)
        second_bytes = _output_bytes(second_root)
        if first_bytes != second_bytes or first_bytes != before:
            raise AssertionError("deterministic set materialization")
        inodes = {name: (first_root / name).stat().st_ino for name in OUTPUTS}
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(first_root, repo_root=ROOT)
        if inodes != {name: (first_root / name).stat().st_ino for name in OUTPUTS}:
            raise AssertionError("existing exact set is not inode-preserving no-op")
        _validate_output_tree(first_root, enforce_frozen_hashes=False, source_records=source_records)
    print(json.dumps({"checked": True, "output_sha256": hashes}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
