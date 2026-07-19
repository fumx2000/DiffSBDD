#!/usr/bin/env python3
"""Independent checker for the ADMIT_009 duplicate-key design gate v1."""

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
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

EXPECTED_BASE_COMMIT = "c253e3909f170f141cbb70d659a98d203390d997"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_009 evaluator preconditions audit v1"
EXPECTED_STAGE = "covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1"
EXPECTED_OUTPUT_ROOT = Path("data/derived/covalent_small") / EXPECTED_STAGE
EXPECTED_RULE_ID = "ADMIT_009"
EXPECTED_RULE_NAME = "duplicate_identity_precheck"
EXPECTED_FIELD = "duplicate_identity_key"
EXPECTED_BATCH = "batch_duplicate_identity_keys"
EXPECTED_POLICY = "duplicate_identity_key_contract"
EXPECTED_PREFIX = "covapie_dup_v1_sha256_"
EXPECTED_REGEX = r"^covapie_dup_v1_sha256_[0-9a-f]{64}$"
EXPECTED_POLICY_VALUE = "covapie_duplicate_identity_key_contract_v1"
EXPECTED_BLOCKER = "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"
EXPECTED_COVERAGE = "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
EXPECTED_DUPLICATE_REASON = "DUPLICATE_IDENTITY_KEY_ALREADY_PRESENT"
EXPECTED_NEXT_STEP = "implement_covapie_admit_009_standalone_evaluator_interface_v1"

CONTRACT_FILE = "covapie_admit_009_duplicate_identity_key_contract.csv"
CONTEXT_FILE = "covapie_admit_009_batch_and_policy_context_contract.csv"
BOUNDARY_FILE = "covapie_admit_009_equivalence_and_provider_boundary_matrix.csv"
TRUTH_FILE = "covapie_admit_009_duplicate_identity_validation_truth_matrix.csv"
ISSUE_FILE = "covapie_admit_009_duplicate_identity_issue_readiness_inventory.csv"
MANIFEST_FILE = "covapie_admit_009_duplicate_identity_key_contract_manifest.json"
EXPECTED_FILES = (CONTRACT_FILE, CONTEXT_FILE, BOUNDARY_FILE, TRUTH_FILE, ISSUE_FILE, MANIFEST_FILE)
EXPECTED_OUTPUT_SHA256 = {
    CONTRACT_FILE: "484072cd901f7ba5264d207202be493477fb16cc4ddfad4341eabd19d8495a85",
    CONTEXT_FILE: "38ac90e04316d8efc8794d88d749a3fafc69a0ef66de5cf76cdfd82f6d9a9b57",
    BOUNDARY_FILE: "7b1d09956be5fa76f8b141c10a2a8efb895119271cfd75b9e816c37c88513297",
    TRUTH_FILE: "762255cc85a12501ccb592a6f3e82ea100221d33c244403386be743c99c64ac0",
    ISSUE_FILE: "2c461d4416742dda734789ba6768995c6d641fb2d1b6c460a0f80ea194482e92",
    MANIFEST_FILE: "d0d0d19e491f27621214ee887f630a871c1a7cfaf4caca93778599b0162dc48c",
}

AUDIT_ROOT = "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1"
RUNTIME_ROOT = "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1"
DESIGN_ROOT = "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
IMPLEMENTATION_ROOT = "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
EXPECTED_SOURCE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit.py",
    f"{AUDIT_ROOT}/covapie_admit_009_formal_evaluator_preconditions_manifest.json",
    f"{AUDIT_ROOT}/covapie_admit_009_evaluator_precondition_matrix.csv",
    f"{AUDIT_ROOT}/covapie_admit_009_duplicate_identity_vocabulary_inventory.csv",
    f"{AUDIT_ROOT}/covapie_admit_009_field_occurrence_inventory.csv",
    f"{AUDIT_ROOT}/covapie_admit_009_issue_readiness_inventory.csv",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008.py",
    f"{RUNTIME_ROOT}/covapie_admit_001_to_008_runtime_manifest.json",
    f"{DESIGN_ROOT}/covapie_bulk_download_admission_rule_registry.csv",
    f"{DESIGN_ROOT}/covapie_bulk_download_admission_schema_contract.csv",
    f"{IMPLEMENTATION_ROOT}/covapie_bulk_download_admission_field_semantics_matrix.csv",
    f"{IMPLEMENTATION_ROOT}/covapie_bulk_download_admission_rule_executability_matrix.csv",
    f"{IMPLEMENTATION_ROOT}/covapie_bulk_download_admission_evaluation_context_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1/covapie_candidate_record_id_semantics_contract.csv",
    "data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/covapie_final_leakage_group_assignment.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv",
)
EXPECTED_SOURCE_SHA256 = dict(zip(EXPECTED_SOURCE_PATHS, (
    "89b2240cc34b0b70a4a197b9615b86171f3e5347b148837e15017c1fa01a2f5e",
    "5d1be882bc51c3fad5eefa5dc106dec43ba5842eda0696c06eb04473db33a37b",
    "f509c25ea5c9843da97cc0582189884b3df9074cbc209a8315e9695699739868",
    "63126db3776eec209f2ea0f2517159889392762a89f609f246ba62ed3f6ac6cc",
    "feb35d0081c4489e6eb5900d72adc3458862f30195fc228a2806bda03d954e83",
    "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128",
    "b5022ee4b6a4e965cf783abf15e70a5909860f4f500c89f983fb41b6b8fd87e2",
    "6047e110c29d8ca7300236f8af8dbce31a92f2a62576cbc2a8fa2d5d1baf32cf",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "92f624705a611c0dac011229d13d6a3ba87fc1ab7a3e0bc9c090952a0838b318",
    "768c964f22e19a8fb6232b1fa26c531e53d023042abcd9b1bcca44df2b4f4416",
    "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
), strict=True))
UNIFIED_RESULT_CONTRACT_SOURCE = EXPECTED_SOURCE_PATHS[15]

CONTRACT_HEADER = ("contract_order", "contract_item", "exact_requirement", "forbidden_behavior", "contract_passed")
CONTEXT_HEADER = ("context_order", "context_item", "scope", "exact_contract", "validation_precedence", "invalid_reason", "context_passed")
BOUNDARY_HEADER = ("boundary_order", "boundary_item", "is_duplicate_identity_key", "exact_duplicate_claim_allowed", "evaluator_visible_component", "exact_statement", "boundary_passed")
TRUTH_HEADER = (
    "truth_order", "truth_group", "case_id", "input_summary", "scalar_classification",
    "policy_classification", "batch_classification", "outcome", "passed", "blocks_candidate",
    "reason", "canonical_duplicate_identity_key", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used", "truth_passed",
)
ISSUE_HEADER = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

SCALAR_REASONS = (
    "DUPLICATE_IDENTITY_KEY_TYPE_INVALID", "DUPLICATE_IDENTITY_KEY_EMPTY",
    "DUPLICATE_IDENTITY_KEY_NON_ASCII", "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID",
)
POLICY_REASONS = ("DUPLICATE_IDENTITY_KEY_CONTRACT_TYPE_INVALID", "DUPLICATE_IDENTITY_KEY_CONTRACT_VALUE_INVALID")
BATCH_REASONS = (
    "BATCH_DUPLICATE_IDENTITY_KEYS_TYPE_INVALID", "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_TYPE_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_INVALID", "BATCH_DUPLICATE_IDENTITY_KEYS_ORDER_OR_UNIQUENESS_INVALID",
)
TRUE_READINESS = (
    "admit_009_duplicate_key_exact_type_contract_available", "admit_009_duplicate_key_syntax_contract_available",
    "admit_009_duplicate_key_normalization_contract_available", "admit_009_duplicate_key_composition_contract_available",
    "admit_009_duplicate_equivalence_domain_contract_available", "admit_009_collision_handling_contract_available",
    "admit_009_batch_container_contract_available", "admit_009_batch_membership_semantics_contract_available",
    "admit_009_self_exclusion_contract_available", "admit_009_duplicate_vs_leakage_boundary_contract_available",
    "admit_009_reason_outcome_contract_available", "admit_009_canonical_state_contract_available",
    "admit_009_independent_semantic_oracle_available", "admit_009_standalone_evaluator_preconditions_complete",
    "admit_009_provider_mapping_boundary_preserved", "ready_for_admit_009_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "real_provider_duplicate_identity_mapping_validated", "real_provider_duplicate_identity_key_count_nonzero",
    "admit_009_standalone_evaluator_implemented", "admit_009_unified_adapter_contract_frozen",
    "admit_009_unified_adapter_implemented", "admit_009_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_009_implemented", "admit_010_standalone_evaluator_implemented",
    "admit_010_to_015_registered_in_engine", "all_15_rules_covered", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen", "real_candidate_evaluation", "ready_for_bulk_download_now",
    "ready_for_training", "ready_to_train_now",
)


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(arguments: Sequence[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, text=text, capture_output=True, check=False)


def _csv(path: Path, header: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != header or len(header) != len(set(header)):
            raise ValueError(f"header mismatch: {path.name}")
        rows = [dict(row) for row in reader]
    if any(tuple(row) != header or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"row shape mismatch: {path.name}")
    return rows


def _read_verified_sources() -> dict[str, bytes]:
    if (
        len(EXPECTED_SOURCE_PATHS) != 16
        or len(set(EXPECTED_SOURCE_PATHS)) != 16
        or tuple(EXPECTED_SOURCE_SHA256) != EXPECTED_SOURCE_PATHS
    ):
        raise ValueError("Exact16 source boundary invalid")
    subject = _git(["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"])
    if subject.returncode or ancestor.returncode or subject.stdout.strip() != EXPECTED_BASE_SUBJECT:
        raise ValueError("base lineage mismatch")
    for value in EXPECTED_SOURCE_PATHS:
        path = Path(value)
        if path.is_absolute() or ".." in path.parts or path.parts[0] == "checkpoints" or path.parts[:2] == ("data", "raw"):
            raise ValueError("unsafe source path")
        full = REPO_ROOT / path
        metadata = os.lstat(full)
        tracked = _git(["ls-files", "--error-unmatch", "--", value])
        tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", value])
        fields = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
        if tracked.returncode or len(fields) != 3 or fields[0] not in ("100644", "100755") or fields[1] != "blob":
            raise ValueError("source is not tracked base-tree regular blob")
        if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("source is not regular non-symlink")
    sources: dict[str, bytes] = {}
    for value in EXPECTED_SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{value}"], text=False)
        filesystem = (REPO_ROOT / value).read_bytes()
        if base.returncode or type(base.stdout) is not bytes:
            raise ValueError("base source read failed")
        if hashlib.sha256(base.stdout).hexdigest() != EXPECTED_SOURCE_SHA256[value]:
            raise ValueError("base source SHA mismatch")
        if hashlib.sha256(filesystem).hexdigest() != EXPECTED_SOURCE_SHA256[value]:
            raise ValueError("filesystem source SHA mismatch")
        sources[value] = filesystem
    return sources


def _validate_unified_result_contract(sources: Mapping[str, bytes]) -> None:
    reader = csv.DictReader(io.StringIO(sources[UNIFIED_RESULT_CONTRACT_SOURCE].decode("utf-8"), newline=""))
    expected_header = (
        "contract_order", "contract_kind", "field_name", "field_type", "contract_value", "contract_status",
    )
    if tuple(reader.fieldnames or ()) != expected_header:
        raise ValueError("unified result contract header mismatch")
    rows = [dict(row) for row in reader]
    expected = {
        "passed": "true_iff_outcome_passed",
        "blocks_candidate": "true_iff_outcome_not_passed",
        "passed_reason": "empty_exact_str",
        "nonpassed_reason": "nonempty_exact_str",
    }
    for field_name, contract_value in expected.items():
        matches = [
            row for row in rows
            if row["contract_kind"] == "result_invariant" and row["field_name"] == field_name
        ]
        if len(matches) != 1:
            raise ValueError("unified result invariant missing or duplicate")
        if matches[0]["contract_value"] != contract_value or matches[0]["contract_status"] != "frozen":
            raise ValueError("unified result invariant mismatch")


def _expected_contract() -> list[dict[str, str]]:
    specs = (
        ("identity", "ADMIT_009/duplicate_identity_precheck uses duplicate_identity_key", "substitute another identity"),
        ("exact_scalar_type", "type(value) is str", "accept subclasses or coercion"),
        ("versioned_prefix", EXPECTED_PREFIX, "accept aliases or other versions"),
        ("exact_regex", EXPECTED_REGEX, "partial match or alternate characters"),
        ("digest", "64 lowercase hexadecimal characters", "uppercase, short, long, or non-hex digest"),
        ("scalar_precedence", "type, non-empty, ASCII, regex fullmatch", "reorder or continue after failure"),
        ("normalization", "canonical key equals input byte-for-byte", "trim, case-fold, Unicode-normalize, alias, repair, recompute, regenerate"),
        ("composition", "atomic opaque producer-owned scalar", "split or parse chemical components"),
        ("evaluator_visible_components", "exactly zero", "promote candidate/group fields as key components"),
        ("producer_descriptor", "producer maintains canonical exact-duplicate descriptor", "evaluator constructs descriptor"),
        ("producer_determinism", "stable deterministic versioned assignment", "unstable or unversioned assignment"),
        ("duplicate_equivalence", "same key means producer-declared exact duplicate admission class", "reinterpret as similarity or grouping"),
        ("different_key_claim", "no duplicate is proved by this key", "claim chemical, ligand, protein, residue, or leakage distinctness"),
        ("collision_preimage", "producer retains or can rebuild canonical descriptor", "discard collision provenance"),
        ("collision_handling", "producer fails closed on same digest for different descriptors", "send ambiguous key to evaluator"),
        ("evaluator_collision_boundary", "evaluator does not detect collision or validate provenance", "assign collision responsibility to evaluator"),
        ("policy_context", EXPECTED_POLICY_VALUE, "fallback, alias, trim, or case-normalize"),
        ("batch_container", "type(value) is tuple; empty allowed", "accept list/set/frozenset/subclass"),
        ("batch_member", "each member exact str and full scalar-valid", "coerce or normalize members"),
        ("batch_order", "strict ascending original ASCII strings", "sort automatically"),
        ("batch_uniqueness", "members unique", "deduplicate automatically"),
        ("snapshot", "earlier admitted/queued canonical keys before current candidate", "include current record itself"),
        ("self_exclusion", "future caller excludes current record; equal key means another earlier candidate", "use candidate_record_id or batch position"),
        ("membership", "exact case-sensitive Python string equality", "prefix, substring, component, graph, or group comparison"),
        ("precedence", "scalar then policy then batch then membership with short-circuit", "evaluate later stages after invalid input"),
        ("outcomes", "passed, blocked, invalid", "use rejected or unresolved umbrella outcome"),
        ("blocks_candidate_invariant", "blocks_candidate is true exactly when outcome is not passed", "invalid or blocked result with blocks_candidate=false"),
        ("unique_state", "passed=true blocks=false reason empty; canonical pair retained", "drop validated canonical state"),
        ("duplicate_state", f"blocked; {EXPECTED_DUPLICATE_REASON}; canonical pair retained", "classify duplicate as invalid/rejected or use lowercase reason"),
        ("invalid_state", "scalar invalid clears canonical/pair; policy or batch invalid retains them", "invent or discard canonical state"),
        ("oracle", "independent pure in-memory full-input design classifier", "perform evaluator I/O"),
        ("provider_boundary", "real provider mapping unvalidated and real key count zero", "fabricate provider keys"),
        ("implementation_boundary", "formal evaluator/result/adapter/registration/runtime changes absent", "implement later stages in this gate"),
        ("execution_boundary", "no raw, network, download, training, model forward/loss", "perform external or training operations"),
    )
    return [{"contract_order": str(i), "contract_item": a, "exact_requirement": b, "forbidden_behavior": c, "contract_passed": "true"} for i, (a, b, c) in enumerate(specs, 1)]


def _expected_context() -> list[dict[str, str]]:
    specs = (
        (EXPECTED_FIELD, "candidate_scalar", "exact built-in str", "1", SCALAR_REASONS[0]),
        (EXPECTED_FIELD, "candidate_scalar", "non-empty", "2", SCALAR_REASONS[1]),
        (EXPECTED_FIELD, "candidate_scalar", "ASCII", "3", SCALAR_REASONS[2]),
        (EXPECTED_FIELD, "candidate_scalar", EXPECTED_REGEX, "4", SCALAR_REASONS[3]),
        (EXPECTED_POLICY, "evaluation_policy", "exact built-in str", "5", POLICY_REASONS[0]),
        (EXPECTED_POLICY, "evaluation_policy", EXPECTED_POLICY_VALUE, "6", POLICY_REASONS[1]),
        (EXPECTED_BATCH, "batch_snapshot", "exact built-in tuple", "7", BATCH_REASONS[0]),
        (EXPECTED_BATCH, "batch_snapshot", "member exact built-in str", "8", BATCH_REASONS[1]),
        (EXPECTED_BATCH, "batch_snapshot", "every member full scalar-valid", "9", BATCH_REASONS[2]),
        (EXPECTED_BATCH, "batch_snapshot", "strict ascending and unique", "10", BATCH_REASONS[3]),
        (EXPECTED_BATCH, "batch_snapshot", "empty tuple valid", "11", ""),
        (EXPECTED_BATCH, "caller_responsibility", "snapshot excludes current record", "12", ""),
        (EXPECTED_BATCH, "membership", "candidate key absent means unique", "13", ""),
        (EXPECTED_BATCH, "membership", "candidate key present means earlier duplicate", "14", EXPECTED_DUPLICATE_REASON),
        (EXPECTED_BATCH, "membership", "match multiplicity is zero or one", "15", ""),
    )
    return [{"context_order": str(i), "context_item": a, "scope": b, "exact_contract": c, "validation_precedence": d, "invalid_reason": e, "context_passed": "true"} for i, (a, b, c, d, e) in enumerate(specs, 1)]


def _expected_boundary() -> list[dict[str, str]]:
    specs = (
        ("candidate_record_id", False, False, False, "record identity is separate and not used for self-exclusion"),
        ("sample_index_row_id", False, False, False, "sample row identity is not a duplicate key"),
        ("assignment_id", False, False, False, "assignment identity is not a duplicate key"),
        ("pdb_id_alone", False, False, False, "structure identifier alone is not a duplicate key"),
        ("ligand_comp_id_alone", False, False, False, "ligand component alone is not a duplicate key"),
        ("ligand_graph_group_id", False, False, False, "ligand graph group is not an exact duplicate class"),
        ("ligand_scaffold_group_id", False, False, False, "scaffold group is not an exact duplicate class"),
        ("protein_group_id", False, False, False, "protein grouping is not an exact duplicate class"),
        ("leakage_group_id", False, False, False, "candidate leakage group is not an exact duplicate class"),
        ("final_leakage_group_id", False, False, False, "conservative must-link union is not an exact duplicate class"),
        ("same_leakage_group", False, False, False, "does not mean exact duplicate"),
        ("same_scaffold", False, False, False, "does not mean exact duplicate"),
        ("same_ligand_graph_group", False, False, False, "does not mean exact duplicate"),
        ("same_duplicate_identity_key", True, True, False, "producer declares same exact duplicate admission class"),
        ("different_duplicate_identity_key", False, False, False, "only means this key does not prove duplication"),
        ("canonical_descriptor", False, True, False, "producer-owned and invisible to evaluator"),
        ("sha256_collision_detection", False, False, False, "producer responsibility; evaluator does not inspect descriptor"),
        ("real_provider_mapping", False, False, False, "unvalidated; zero real keys materialized"),
    )
    return [{"boundary_order": str(i), "boundary_item": a, "is_duplicate_identity_key": _bool(b), "exact_duplicate_claim_allowed": _bool(c), "evaluator_visible_component": _bool(d), "exact_statement": e, "boundary_passed": "true"} for i, (a, b, c, d, e) in enumerate(specs, 1)]


def _oracle(key: object, batch: object, policy: object) -> dict[str, Any]:
    base = {"consumed_candidate_fields": (EXPECTED_FIELD,), "evaluator_io_used": False}
    if type(key) is not str:
        return {**base, "scalar_classification": "invalid", "policy_classification": "not_evaluated", "batch_classification": "not_evaluated", "outcome": "invalid", "passed": False, "blocks_candidate": True, "reason": SCALAR_REASONS[0], "canonical_duplicate_identity_key": "", "validated_candidate_fields": (), "consumed_context_items": ()}
    if key == "": reason = SCALAR_REASONS[1]
    elif not key.isascii(): reason = SCALAR_REASONS[2]
    elif re.fullmatch(EXPECTED_REGEX, key) is None: reason = SCALAR_REASONS[3]
    else: reason = ""
    if reason:
        return {**base, "scalar_classification": "invalid", "policy_classification": "not_evaluated", "batch_classification": "not_evaluated", "outcome": "invalid", "passed": False, "blocks_candidate": True, "reason": reason, "canonical_duplicate_identity_key": "", "validated_candidate_fields": (), "consumed_context_items": ()}
    pair = ((EXPECTED_FIELD, key),)
    if type(policy) is not str or policy != EXPECTED_POLICY_VALUE:
        reason = POLICY_REASONS[0] if type(policy) is not str else POLICY_REASONS[1]
        return {**base, "scalar_classification": "canonical", "policy_classification": "invalid", "batch_classification": "not_evaluated", "outcome": "invalid", "passed": False, "blocks_candidate": True, "reason": reason, "canonical_duplicate_identity_key": key, "validated_candidate_fields": pair, "consumed_context_items": (EXPECTED_POLICY,)}
    if type(batch) is not tuple: reason = BATCH_REASONS[0]
    elif any(type(x) is not str for x in batch): reason = BATCH_REASONS[1]
    elif any(x == "" or not x.isascii() or re.fullmatch(EXPECTED_REGEX, x) is None for x in batch): reason = BATCH_REASONS[2]
    elif any(a >= b for a, b in zip(batch, batch[1:])): reason = BATCH_REASONS[3]
    else: reason = ""
    if reason:
        return {**base, "scalar_classification": "canonical", "policy_classification": "valid", "batch_classification": "invalid", "outcome": "invalid", "passed": False, "blocks_candidate": True, "reason": reason, "canonical_duplicate_identity_key": key, "validated_candidate_fields": pair, "consumed_context_items": (EXPECTED_POLICY, EXPECTED_BATCH)}
    duplicate = key in batch
    return {**base, "scalar_classification": "canonical", "policy_classification": "valid", "batch_classification": "valid", "outcome": "blocked" if duplicate else "passed", "passed": not duplicate, "blocks_candidate": duplicate, "reason": EXPECTED_DUPLICATE_REASON if duplicate else "", "canonical_duplicate_identity_key": key, "validated_candidate_fields": pair, "consumed_context_items": (EXPECTED_POLICY, EXPECTED_BATCH)}


def _expected_truth() -> list[dict[str, str]]:
    class StringSubclass(str): pass
    class TupleSubclass(tuple): pass
    candidate = EXPECTED_PREFIX + "1" * 64; low = EXPECTED_PREFIX + "0" * 64
    high = EXPECTED_PREFIX + "2" * 64; unrelated = EXPECTED_PREFIX + "f" * 64
    policy = EXPECTED_POLICY_VALUE; empty: tuple[str, ...] = ()
    cases = [
        ("scalar", "scalar_none", None, empty, policy), ("scalar", "scalar_integer", 7, empty, policy),
        ("scalar", "scalar_str_subclass", StringSubclass(candidate), empty, policy), ("scalar", "scalar_empty", "", empty, policy),
        ("scalar", "scalar_non_ascii", EXPECTED_PREFIX + "é" * 64, empty, policy), ("scalar", "scalar_wrong_prefix", "covapie_dup_v2_sha256_" + "1" * 64, empty, policy),
        ("scalar", "scalar_uppercase_digest", EXPECTED_PREFIX + "A" * 64, empty, policy), ("scalar", "scalar_short_digest", EXPECTED_PREFIX + "1" * 63, empty, policy),
        ("scalar", "scalar_long_digest", EXPECTED_PREFIX + "1" * 65, empty, policy), ("scalar", "scalar_non_hex", EXPECTED_PREFIX + "g" * 64, empty, policy),
        ("scalar", "scalar_whitespace", " " + candidate, empty, policy), ("scalar", "scalar_canonical", candidate, empty, policy),
        ("policy", "policy_none", candidate, empty, None), ("policy", "policy_str_subclass", candidate, empty, StringSubclass(policy)),
        ("policy", "policy_wrong_value", candidate, empty, "covapie_duplicate_identity_key_contract_v2"), ("policy", "policy_exact_valid", candidate, empty, policy),
        ("batch", "batch_none", candidate, None, policy), ("batch", "batch_list", candidate, [], policy),
        ("batch", "batch_tuple_subclass", candidate, TupleSubclass(), policy), ("batch", "batch_non_str_member", candidate, (7,), policy),
        ("batch", "batch_str_subclass_member", candidate, (StringSubclass(unrelated),), policy), ("batch", "batch_malformed_member", candidate, ("bad",), policy),
        ("batch", "batch_unsorted", candidate, (high, low), policy), ("batch", "batch_duplicate_members", candidate, (unrelated, unrelated), policy),
        ("batch", "batch_empty_valid", candidate, (), policy), ("batch", "batch_one_unrelated", candidate, (unrelated,), policy),
        ("batch", "batch_one_matching", candidate, (candidate,), policy), ("batch", "batch_multiple_contains", candidate, (low, candidate, high), policy),
        ("outcome_state", "canonical_unique_passed", candidate, (unrelated,), policy), ("outcome_state", "canonical_duplicate_blocked", candidate, (candidate,), policy),
        ("outcome_state", "policy_invalid_retains_pair", candidate, (), "wrong"), ("outcome_state", "batch_invalid_retains_pair", candidate, [candidate], policy),
    ]
    rows = []
    for i, (group, case, key, batch, policy_value) in enumerate(cases, 1):
        result = _oracle(key, batch, policy_value)
        display = lambda value: f"{type(value).__name__}:{value!r}"
        rows.append({"truth_order": str(i), "truth_group": group, "case_id": case, "input_summary": f"key={display(key)};batch={display(batch)};policy={display(policy_value)}", "scalar_classification": result["scalar_classification"], "policy_classification": result["policy_classification"], "batch_classification": result["batch_classification"], "outcome": result["outcome"], "passed": _bool(result["passed"]), "blocks_candidate": _bool(result["blocks_candidate"]), "reason": result["reason"], "canonical_duplicate_identity_key": result["canonical_duplicate_identity_key"], "validated_candidate_fields": json.dumps(result["validated_candidate_fields"], separators=(",", ":")), "consumed_candidate_fields": json.dumps(result["consumed_candidate_fields"], separators=(",", ":")), "consumed_context_items": json.dumps(result["consumed_context_items"], separators=(",", ":")), "evaluator_io_used": _bool(result["evaluator_io_used"]), "truth_passed": "true"})
    return rows


def _validate_outcome_invariants(truth: Sequence[Mapping[str, str]]) -> None:
    if any(row["passed"] not in ("true", "false") or row["blocks_candidate"] not in ("true", "false") for row in truth):
        raise ValueError("outcome booleans invalid")
    if any((row["passed"] == "true") != (row["outcome"] == "passed") for row in truth):
        raise ValueError("passed invariant mismatch")
    if any((row["blocks_candidate"] == "true") != (row["outcome"] != "passed") for row in truth):
        raise ValueError("blocks_candidate invariant mismatch")
    if any((row["reason"] == "") != (row["outcome"] == "passed") for row in truth):
        raise ValueError("outcome reason invariant mismatch")
    scalar_invalid = [row for row in truth if row["truth_group"] == "scalar" and row["outcome"] == "invalid"]
    policy_invalid = [row for row in truth if row["truth_group"] == "policy" and row["outcome"] == "invalid"]
    batch_invalid = [row for row in truth if row["truth_group"] == "batch" and row["outcome"] == "invalid"]
    blocked = [row for row in truth if row["outcome"] == "blocked"]
    passed = [row for row in truth if row["outcome"] == "passed"]
    if not scalar_invalid or any(row["blocks_candidate"] != "true" for row in scalar_invalid):
        raise ValueError("scalar invalid must block candidate")
    if not policy_invalid or any(row["blocks_candidate"] != "true" for row in policy_invalid):
        raise ValueError("policy invalid must block candidate")
    if not batch_invalid or any(row["blocks_candidate"] != "true" for row in batch_invalid):
        raise ValueError("batch invalid must block candidate")
    if not blocked or any(row["blocks_candidate"] != "true" for row in blocked):
        raise ValueError("blocked outcome must block candidate")
    if not passed or any(row["blocks_candidate"] != "false" for row in passed):
        raise ValueError("passed outcome must not block candidate")


def _expected_issues(sources: Mapping[str, bytes]) -> list[dict[str, str]]:
    source = sources[EXPECTED_SOURCE_PATHS[5]].decode("utf-8")
    reader = csv.DictReader(io.StringIO(source, newline=""))
    if tuple(reader.fieldnames or ()) != ISSUE_HEADER:
        raise ValueError("predecessor issue header mismatch")
    rows = [dict(row) for row in reader]
    changed = 0
    for row in rows:
        if row["issue_id"] == EXPECTED_BLOCKER:
            row["status"] = "resolved"; row["integration_transition"] = "duplicate_identity_key_contract_frozen_v1"; changed += 1
    if changed != 1 or len(rows) != 11:
        raise ValueError("issue transition construction failed")
    return rows


def _readiness() -> dict[str, bool]:
    return {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def _source_verification() -> list[dict[str, Any]]:
    return [{"source_order": i, "source_relative_path": p, "expected_sha256": EXPECTED_SOURCE_SHA256[p], "base_tree_sha256": EXPECTED_SOURCE_SHA256[p], "filesystem_sha256": EXPECTED_SOURCE_SHA256[p], "tracked": True, "base_tree_blob": True, "filesystem_regular": True, "non_symlink": True, "source_verified": True} for i, p in enumerate(EXPECTED_SOURCE_PATHS, 1)]


def _expected_manifest(contract: list[dict[str, str]], context: list[dict[str, str]], boundary: list[dict[str, str]], truth: list[dict[str, str]], issues: list[dict[str, str]], output_sha: Mapping[str, str]) -> dict[str, Any]:
    readiness = _readiness(); groups = {g: sum(r["truth_group"] == g for r in truth) for g in ("scalar", "policy", "batch", "outcome_state")}
    manifest: dict[str, Any] = {
        "project": "CovaPIE", "step": "ADMIT_009 duplicate identity key contract design gate v1", "stage": EXPECTED_STAGE,
        "manifest_schema_version": "covapie_admit_009_duplicate_identity_key_contract_manifest_v1",
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": EXPECTED_RULE_ID, "admission_rule_name": EXPECTED_RULE_NAME, "candidate_field": EXPECTED_FIELD,
        "batch_context_item": EXPECTED_BATCH, "policy_context_item": EXPECTED_POLICY, "evaluation_phase": "pre_download",
        "future_evaluator_name_reserved_only": "evaluate_admit_009", "future_result_name_reserved_only": "Admit009EvaluationResult",
        "key_contract": {"exact_type": "builtins.str", "prefix": EXPECTED_PREFIX, "regex": EXPECTED_REGEX, "digest_length": 64, "digest_charset": "0123456789abcdef", "versioned": True, "deterministic": True, "atomic_opaque": True, "evaluator_visible_component_count": 0, "canonical_equals_input": True, "normalization_or_repair_allowed": False},
        "policy_contract": {"exact_type": "builtins.str", "only_value": EXPECTED_POLICY_VALUE},
        "batch_contract": {"exact_type": "builtins.tuple", "empty_allowed": True, "member_exact_type": "builtins.str", "members_full_scalar_valid": True, "strict_ascii_ascending": True, "unique": True, "automatic_sort_or_deduplicate": False, "current_record_excluded_by_caller": True},
        "validation_precedence": [EXPECTED_FIELD, EXPECTED_POLICY, EXPECTED_BATCH, "exact_membership"],
        "outcome_vocabulary": ["passed", "blocked", "invalid"], "scalar_invalid_reasons": list(SCALAR_REASONS),
        "blocks_candidate_invariant": "true_iff_outcome_not_passed", "invalid_blocks_candidate": True,
        "policy_invalid_reasons": list(POLICY_REASONS), "batch_invalid_reasons": list(BATCH_REASONS),
        "duplicate_blocked_reason": EXPECTED_DUPLICATE_REASON, "membership_semantics": "exact case-sensitive Python string equality",
        "composition_contract": "composition intentionally opaque and producer-owned",
        "duplicate_equivalence": "same key means producer-declared exact duplicate admission class",
        "different_key_limited_claim": "this key does not prove duplication; no chemical distinctness is asserted",
        "producer_responsibility": {"canonical_descriptor_maintained": True, "sha256_lowercase_hex": True, "preimage_retained_or_reconstructable": True, "collision_fail_closed": True, "version_change_requires_new_contract_and_prefix": True},
        "evaluator_detects_digest_collision": False, "evaluator_validates_descriptor_provenance": False,
        "identity_boundaries": {row["boundary_item"]: row["is_duplicate_identity_key"] == "true" for row in boundary},
        "real_provider_duplicate_identity_mapping_validated": False, "real_provider_duplicate_identity_key_count": 0,
        "design_oracle_name": "classify_admit_009_duplicate_identity_key_design", "design_oracle_is_formal_evaluator": False,
        "design_oracle_evaluator_io_used": False, "truth_matrix_contract": "Exact32", "truth_row_count": 32,
        "truth_pass_count": 32, "truth_group_counts": groups, "contract_row_count": len(contract), "context_row_count": len(context),
        "boundary_row_count": len(boundary), "issue_inventory_row_count": len(issues),
        "source_boundary_name": "fixed_ordered_exact16_committed_source_boundary", "source_input_count": 16,
        "source_input_paths": list(EXPECTED_SOURCE_PATHS), "source_input_sha256": dict(EXPECTED_SOURCE_SHA256),
        "source_input_verification": _source_verification(), "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True, "artifact_reference_paths_not_recursively_opened": True,
        "issue_transition": {"issue_id": EXPECTED_BLOCKER, "from_status": "open", "to_status": "resolved", "from_integration_transition": "unchanged_open", "to_integration_transition": "duplicate_identity_key_contract_frozen_v1", "only_authorized_issue_change": True},
        "coverage_issue_status": "open", "coverage_issue_affected_rules": "ADMIT_009–ADMIT_015", "coverage_issue_transition": "admit_008_implemented_and_removed_from_open_coverage_scope",
        "readiness": readiness, "output_file_count": 6, "output_files": list(EXPECTED_FILES), "output_sha256": dict(output_sha),
        "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": ["no_real_provider_key_generation", "no_provider_mapping_validation", "no_formal_evaluator", "no_result_class", "no_adapter_design_or_implementation", "no_exact8_runtime_change", "no_admit_009_registration", "no_admit_010", "no_evaluate_all_rules", "no_combined_verdict", "no_raw_network_download_or_training"],
        "recommended_next_step": EXPECTED_NEXT_STEP, "all_source_boundary_checks_passed": True, "all_contract_checks_passed": True,
        "all_context_checks_passed": True, "all_boundary_checks_passed": True, "all_truth_checks_passed": True,
        "all_issue_checks_passed": True, "all_readiness_checks_passed": True, "all_attestations_passed": True,
        "validation_failures": [],
    }
    manifest.update(readiness)
    return manifest


def _validate_entries(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("output root unsafe")
    entries = tuple(root.iterdir())
    if {p.name for p in entries} != set(EXPECTED_FILES) or len(entries) != 6:
        raise ValueError("output set is not Exact6")
    if any(p.is_symlink() or not p.is_file() for p in entries):
        raise ValueError("output is not regular non-symlink")


def _validate_disk(root: Path, *, enforce_frozen_hashes: bool = True) -> dict[str, Any]:
    _validate_entries(root)
    sources = _read_verified_sources()
    _validate_unified_result_contract(sources)
    contract = _csv(root / CONTRACT_FILE, CONTRACT_HEADER); context = _csv(root / CONTEXT_FILE, CONTEXT_HEADER)
    boundary = _csv(root / BOUNDARY_FILE, BOUNDARY_HEADER); truth = _csv(root / TRUTH_FILE, TRUTH_HEADER)
    issues = _csv(root / ISSUE_FILE, ISSUE_HEADER)
    if contract != _expected_contract() or context != _expected_context() or boundary != _expected_boundary():
        raise ValueError("contract/context/boundary semantic mismatch")
    _validate_outcome_invariants(truth)
    if truth != _expected_truth() or len(truth) != 32 or any(r["truth_passed"] != "true" for r in truth):
        raise ValueError("Exact32 truth mismatch")
    if issues != _expected_issues(sources):
        raise ValueError("successor issue mismatch")
    output_sha = {name: _sha(root / name) for name in EXPECTED_FILES if name != MANIFEST_FILE}
    manifest = json.loads((root / MANIFEST_FILE).read_text(encoding="utf-8"))
    expected_manifest = _expected_manifest(contract, context, boundary, truth, issues, output_sha)
    if type(manifest) is not dict or manifest != expected_manifest:
        raise ValueError("manifest complete-dict mismatch")
    if any(manifest[key] != manifest["readiness"][key] for key in (*TRUE_READINESS, *FALSE_READINESS)):
        raise ValueError("readiness mirror mismatch")
    if enforce_frozen_hashes:
        actual = {name: _sha(root / name) for name in EXPECTED_FILES}
        if actual != EXPECTED_OUTPUT_SHA256:
            raise ValueError("frozen output SHA mismatch")
    return manifest


def _validate_production_equivalence(root: Path) -> None:
    from covalent_ext.covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate import run_covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1
    with tempfile.TemporaryDirectory() as temporary:
        generated = Path(temporary) / "generated"
        run_covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1(generated)
        for name in EXPECTED_FILES:
            if (generated / name).read_bytes() != (root / name).read_bytes():
                raise ValueError("production/checker equivalence mismatch")


def _raises(function: Any, *args: Any, **kwargs: Any) -> None:
    try:
        function(*args, **kwargs)
    except (ValueError, OSError, json.JSONDecodeError):
        return
    raise AssertionError("negative check unexpectedly passed")


def _refresh_manifest_hash(root: Path, name: str) -> None:
    path = root / MANIFEST_FILE; value = json.loads(path.read_text(encoding="utf-8"))
    value["output_sha256"][name] = _sha(root / name)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _negative_checks(root: Path) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        tampered = base / "tampered"; shutil.copytree(root, tampered)
        rows = _csv(tampered / CONTRACT_FILE, CONTRACT_HEADER); rows[7]["exact_requirement"] = "parse components"
        with (tampered / CONTRACT_FILE).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CONTRACT_HEADER, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
        _refresh_manifest_hash(tampered, CONTRACT_FILE); _raises(_validate_disk, tampered, enforce_frozen_hashes=False)
        invalid = base / "invalid_blocks"; shutil.copytree(root, invalid)
        rows = _csv(invalid / TRUTH_FILE, TRUTH_HEADER); rows[0]["blocks_candidate"] = "false"
        with (invalid / TRUTH_FILE).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=TRUTH_HEADER, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
        _refresh_manifest_hash(invalid, TRUTH_FILE); _raises(_validate_disk, invalid, enforce_frozen_hashes=False)
        unknown = base / "unknown"; shutil.copytree(root, unknown)
        path = unknown / MANIFEST_FILE; manifest = json.loads(path.read_text()); manifest["unknown"] = True
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n"); _raises(_validate_disk, unknown, enforce_frozen_hashes=False)
        extra = base / "extra"; shutil.copytree(root, extra); (extra / "extra.csv").write_text("x\n")
        _raises(_validate_disk, extra, enforce_frozen_hashes=False)


def main() -> int:
    root = REPO_ROOT / EXPECTED_OUTPUT_ROOT
    manifest = _validate_disk(root)
    _validate_production_equivalence(root)
    _negative_checks(root)
    if manifest["truth_pass_count"] != 32 or manifest["real_provider_duplicate_identity_key_count"] != 0:
        raise AssertionError("checker final assertion failed")
    print("ADMIT_009 duplicate identity key contract design gate v1 check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
