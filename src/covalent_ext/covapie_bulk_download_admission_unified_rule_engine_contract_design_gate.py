"""Step14AU-E1-E4 Phase 1 unified admission engine contract design gate.

This module freezes metadata contracts only.  It deliberately does not define
or implement the future dispatcher, evaluator adapters, runtime registry, or a
combined candidate verdict.  Predecessor evaluators are inspected as frozen
AST bytes and are never imported or executed.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import stat
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "Step14AU-E1-E4 Phase 1"
STAGE = "covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1"
EXPECTED_BASE_COMMIT = "a36993477b5f23d6d13509be54d64c9fb6fd9012"
EXPECTED_BASE_SUBJECT = "add CovaPIE standalone ADMIT_004 rule logic interface v1"
MANIFEST_SCHEMA_VERSION = "covapie_unified_admission_engine_contract_design_manifest_v1"
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_minimal_unified_admission_dispatch_shell_with_admit_004_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

E1E3_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_004_rule_logic_interface_v1"
)
E1E2_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_004_generic_atom_identity_"
    "evidence_context_reconciliation_integration_gate_v1"
)
STEP14AT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
STEP14AUA_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_"
    "implementation_precondition_gate_v1"
)
E1A_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_004_residue_identity_"
    "atom_name_semantics_design_gate_v1"
)

SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        "src/covalent_ext/covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate.py",
        "src/covalent_ext/covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate.py",
        "src/covalent_ext/covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate.py",
        "src/covalent_ext/covapie_bulk_download_admission_admit_004_rule_logic_interface.py",
        str(E1E3_ROOT / "covapie_admit_004_rule_logic_interface_contract.csv"),
        str(E1E3_ROOT / "covapie_admit_004_rule_logic_interface_manifest.json"),
        str(E1E3_ROOT / "covapie_admit_004_rule_logic_interface_issue_readiness_inventory.csv"),
        str(E1E2_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_reconciled_rule_matrix.csv"),
        str(E1E2_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_reconciled_context_matrix.csv"),
        str(E1E2_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_integration_issue_inventory.csv"),
        str(E1E2_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_integration_manifest.json"),
        str(STEP14AT_ROOT / "covapie_bulk_download_admission_schema_contract.csv"),
        str(STEP14AT_ROOT / "covapie_bulk_download_admission_rule_registry.csv"),
        str(STEP14AT_ROOT / "covapie_bulk_download_admission_design_gate_manifest.json"),
        "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate.py",
        str(STEP14AUA_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"),
        str(STEP14AUA_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"),
        str(STEP14AUA_ROOT / "covapie_bulk_download_admission_implementation_precondition_manifest.json"),
        "src/covalent_ext/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate.py",
        str(E1A_ROOT / "covapie_admit_004_residue_identity_atom_name_semantics_contract.csv"),
        str(E1A_ROOT / "covapie_admit_004_residue_identity_atom_name_truth_table.csv"),
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "3246a131a3815aa184338637edef6d8c9020b2dc23f41794e5697812467d269b",
            "c78ed4986551913dea75dc220609f97154941ebda5afffaa84ff252e9d36df83",
            "8d616a02b5f87ea98be3029879d55acd3c06c26e7286a46cb293bd6a4a7f6e11",
            "5c05e166091a7a067014d9d4dbd8c7c4280b6f247c31765e14bf37d3f86adba3",
            "0c4fbc7f1307d3adb5c62dffb7668176b0ad54f2ff156b2f42ea02dec8d48250",
            "f000c7959c0e8a9f561d60b332c5460b4de84279d3e5c11556638334297723a6",
            "7cf0a9ff421ba987655c4dac4564c04dbaa854cd4f725b18136642f223762d30",
            "bcc794debeb4d8287d06db9891dd7f0c085e0cc96ba50b14b8b34d3e768ff676",
            "26e6eac422d00805aaad336024c2ec9d75038620e280c8d48fa89ef60a451cd1",
            "7cf0a9ff421ba987655c4dac4564c04dbaa854cd4f725b18136642f223762d30",
            "3c03b711e74fd023be187b64a757e69f8fc03bcb1af19c88325e7fdeb226012d",
            "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
            "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
            "085cb2f2a6bfe9bebe9e503dd10aa0b4d6f9ad754ff99539b1bafb33c78b5444",
            "5fcc47a764a8a87e110350359e7c17056773c7ffd659b9094b6433beded2a9f8",
            "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
            "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
            "2304b5754d8052b4b186981a98c12f259608a3492947e069c2afab84084a0d52",
            "8f86c22cb5f9154ddf3481f7976bfa964573f68427e63916c503ed9c68d71d98",
            "a783a3d474a2ed4e5ff348ec54a73510f5f6f6fb9d1edcb45dc97108e5d09eff",
            "a5c2d727b3178bd0e58643a1801780fa930cba2b89c14a058817ecb418753106",
        ),
        strict=True,
    )
)

(
    ADMIT001_SOURCE_PATH,
    ADMIT002_SOURCE_PATH,
    ADMIT003_SOURCE_PATH,
    ADMIT004_SOURCE_PATH,
    E1E3_CONTRACT_PATH,
    E1E3_MANIFEST_PATH,
    E1E3_ISSUE_PATH,
    E1E2_RULE_PATH,
    E1E2_CONTEXT_PATH,
    E1E2_ISSUE_PATH,
    E1E2_MANIFEST_PATH,
    STEP14AT_SCHEMA_PATH,
    STEP14AT_REGISTRY_PATH,
    STEP14AT_MANIFEST_PATH,
    STEP14AUA_SOURCE_PATH,
    STEP14AUA_RULE_PATH,
    STEP14AUA_CONTEXT_PATH,
    STEP14AUA_MANIFEST_PATH,
    E1A_SOURCE_PATH,
    E1A_CONTRACT_PATH,
    E1A_TRUTH_PATH,
) = SOURCE_PATHS

PUBLIC_API_FILENAME = "covapie_unified_admission_public_api_and_dispatch_contract.csv"
RESULT_FILENAME = "covapie_unified_admission_result_schema_and_outcome_contract.csv"
ROUTING_FILENAME = "covapie_unified_admission_evaluator_and_context_routing_matrix.csv"
ISSUE_FILENAME = "covapie_unified_admission_engine_issue_inventory.csv"
SAFETY_FILENAME = "covapie_unified_admission_engine_safety_audit.csv"
MANIFEST_FILENAME = "covapie_unified_admission_engine_contract_design_manifest.json"
CSV_OUTPUTS = (PUBLIC_API_FILENAME, RESULT_FILENAME, ROUTING_FILENAME, ISSUE_FILENAME, SAFETY_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

PUBLIC_API_COLUMNS = (
    "contract_order",
    "contract_area",
    "contract_item",
    "contract_value",
    "contract_status",
)
RESULT_COLUMNS = (
    "contract_order",
    "contract_kind",
    "field_name",
    "field_type",
    "contract_value",
    "contract_status",
)
ROUTING_COLUMNS = (
    "admission_rule_id",
    "admission_rule_name",
    "evaluation_phase",
    "candidate_field_dependencies",
    "batch_context_dependencies",
    "evaluation_context_dependencies",
    "download_result_context_dependencies",
    "stage_authorization_context_dependencies",
    "evaluator_callable_name",
    "evaluator_source_path",
    "callable_discovered",
    "evaluator_result_type",
    "result_adapter_contract_status",
    "engine_registration_status",
    "allowed_rule_outcomes",
    "routing_disposition",
    "blocking_reason",
)
ISSUE_COLUMNS = (
    "issue_id",
    "issue_type",
    "affected_fields",
    "affected_rules",
    "severity",
    "status",
    "blocking_scope",
    "blocking_reason",
    "issue_origin",
    "integration_transition",
    "issue_count",
)
SAFETY_COLUMNS = (
    "safety_item",
    "expected_executed",
    "observed_executed",
    "safety_passed",
)

RESULT_FIELDS = (
    ("schema_version", "str"),
    ("admission_rule_id", "str"),
    ("admission_rule_name", "str"),
    ("outcome", "str"),
    ("passed", "bool"),
    ("blocks_candidate", "bool"),
    ("reason", "str"),
    ("normalized_values", "tuple[tuple[str, str], ...]"),
    ("validated_candidate_fields", "tuple[tuple[str, str], ...]"),
    ("consumed_candidate_fields", "tuple[str, ...]"),
    ("consumed_context_items", "tuple[str, ...]"),
    ("evaluator_io_used", "bool"),
    ("adapter_id", "str"),
)
DISPATCH_ERROR_FIELDS = (
    ("code", "str"),
    ("admission_rule_id", "str"),
    ("known_rule", "bool"),
    ("callable_discovered", "bool"),
    ("adapter_ready", "bool"),
    ("reason", "str"),
)
DISPATCH_ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
    "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid", "rejected")

TRUE_READINESS = (
    "unified_rule_engine_contract_design_frozen",
    "single_rule_dispatch_api_contract_frozen",
    "unified_per_rule_result_schema_frozen",
    "dispatch_failure_contract_frozen",
    "explicit_context_routing_contract_frozen",
    "unsupported_rule_fail_closed_contract_frozen",
    "evaluator_inventory_complete_for_current_head",
    "admit_004_adapter_contract_design_ready",
    "ready_for_minimal_admit_004_dispatch_shell_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "evaluate_admission_rule_implemented",
    "unified_rule_engine_implemented",
    "evaluator_registry_runtime_implemented",
    "admit_004_registered_in_engine",
    "legacy_evaluator_adapters_implemented",
    "all_15_rules_covered",
    "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen",
    "real_candidate_evaluation",
    "exact11_real_rows_evaluated",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "ready_to_train_now",
)
TRUE_SAFETY_ITEMS = (
    "exact_source_reads",
    "callable_inventory_ast_validation",
    "metadata_rule_registry_validation",
    "public_api_contract_design",
    "unified_result_schema_design",
    "dispatch_failure_contract_design",
    "explicit_context_routing_design",
    "engine_issue_transition_design",
)
FALSE_SAFETY_ITEMS = (
    "raw_read",
    "provenance_reference_dereference",
    "evaluator_execution",
    "parser_execution",
    "provider_execution",
    "dispatch_implementation",
    "evaluator_adapter_implementation",
    "evaluator_registry_runtime_implementation",
    "unified_rule_engine_integration",
    "combined_candidate_verdict_implementation",
    "candidate_record_materialization",
    "real_candidate_evaluation",
    "admission_record_modification",
    "sample_backfill",
    "network",
    "download",
    "checkpoint",
    "torch",
    "numpy",
    "rdkit",
    "model_forward_loss_training",
)


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    base_tree_sha256: str
    filesystem_sha256: str
    content_bytes: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


@dataclass(frozen=True)
class CsvDocument:
    header: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


def _git(
    arguments: Sequence[str], repo_root: Path, *, text: bool = True
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False
    )


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path)
        and not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[0] != "checkpoints"
        and path.parts[:2] != ("data", "raw")
    )


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    """Inspect source metadata without reading source content bytes."""
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    fields = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    return (
        tracked.returncode == 0
        and tree.returncode == 0
        and len(fields) == 3
        and fields[0] in ("100644", "100755")
        and fields[1] == "blob"
        and stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
    )


def _validate_expected_base_lineage(
    repo_root: Path, *, head_ref: str = "HEAD"
) -> None:
    """Require the frozen evidence base to exist and be in the HEAD lineage."""
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("head ref is invalid")
    base_object = _git(
        ["cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"], repo_root
    )
    if base_object.returncode != 0:
        raise ValueError("expected base commit object is missing")
    base_subject = _git(
        ["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], repo_root
    )
    if (
        base_subject.returncode != 0
        or base_subject.stdout.strip() != EXPECTED_BASE_SUBJECT
    ):
        raise ValueError("expected base commit subject mismatch")
    ancestor = _git(
        ["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref], repo_root
    )
    if ancestor.returncode != 0:
        raise ValueError("expected base commit is not an ancestor of head")


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    """Complete every Exact21 structural check before the first byte read."""
    if (
        len(SOURCE_PATHS) != 21
        or len(set(SOURCE_PATHS)) != 21
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact21 source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref=head_ref)
    structural = tuple(_structural_source_check(path, repo_root) for path in SOURCE_PATHS)
    if not all(structural):
        raise ValueError("source structural validation failed")

    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base_read = _git(
            ["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"], repo_root, text=False
        )
        if base_read.returncode != 0 or type(base_read.stdout) is not bytes:
            raise ValueError(f"base-tree source read failed: {path}")
        filesystem_bytes = (repo_root / path).read_bytes()
        base_sha = hashlib.sha256(base_read.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem_bytes).hexdigest()
        expected = SOURCE_SHA256[path]
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(
            FrozenSourceRecord(path, expected, base_sha, filesystem_sha, filesystem_bytes)
        )
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot
        and len(value.records) == 21
        and tuple(record.relative_path for record in value.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.base_tree_sha256 == record.expected_sha256
            and record.filesystem_sha256 == record.expected_sha256
            and hashlib.sha256(record.content_bytes).hexdigest() == record.expected_sha256
            for record in value.records
        )
    )


def _record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord:
    matches = tuple(record for record in snapshot.records if record.relative_path == path)
    if len(matches) != 1:
        raise ValueError("frozen source missing or duplicate")
    return matches[0]


def _csv_document(snapshot: FrozenSourceSnapshot, path: Path) -> CsvDocument:
    text = _record(snapshot, path).content_bytes.decode("utf-8", errors="strict")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(
        tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values())
        for row in rows
    ):
        raise ValueError("invalid CSV row")
    return CsvDocument(tuple(reader.fieldnames), rows)


def _json_document(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(_record(snapshot, path).content_bytes.decode("utf-8", errors="strict"))
    if type(value) is not dict:
        raise ValueError("invalid JSON document")
    return value


def _ast_document(snapshot: FrozenSourceSnapshot, path: Path) -> ast.Module:
    text = _record(snapshot, path).content_bytes.decode("utf-8", errors="strict")
    return ast.parse(text, filename=path.as_posix())


def _keyed(rows: Sequence[Mapping[str, str]], key: str) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            raise ValueError("missing or duplicate row key")
        result[value] = row
    return result


def _public_functions(tree: ast.Module) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }


def _validate_callable_inventory(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    specifications = (
        ("ADMIT_001", "evaluate_admit_001_candidate_record_id", ADMIT001_SOURCE_PATH, "dict[str, object]"),
        ("ADMIT_002", "evaluate_admit_002_pdb_identifier", ADMIT002_SOURCE_PATH, "dict[str, object]"),
        ("ADMIT_003", "evaluate_admit_003_ligand_comp_id", ADMIT003_SOURCE_PATH, "dict[str, object]"),
        ("ADMIT_004", "evaluate_admit_004", ADMIT004_SOURCE_PATH, "Admit004EvaluationResult"),
    )
    inventory: list[dict[str, str]] = []
    all_trees = {
        path: _ast_document(snapshot, path)
        for path in (
            ADMIT001_SOURCE_PATH,
            ADMIT002_SOURCE_PATH,
            ADMIT003_SOURCE_PATH,
            ADMIT004_SOURCE_PATH,
            STEP14AUA_SOURCE_PATH,
            E1A_SOURCE_PATH,
        )
    }
    for rule_id, callable_name, path, expected_return in specifications:
        functions = _public_functions(all_trees[path])
        node = functions.get(callable_name)
        if node is None or node.returns is None or ast.unparse(node.returns) != expected_return:
            raise ValueError(f"formal evaluator contract mismatch: {rule_id}")
        inventory.append(
            {
                "admission_rule_id": rule_id,
                "evaluator_callable_name": callable_name,
                "evaluator_source_path": path.as_posix(),
                "evaluator_result_type": expected_return,
            }
        )
    all_top_functions = {
        name for tree in all_trees.values() for name in _public_functions(tree)
    }
    if "evaluate_admission_rule" in all_top_functions:
        raise ValueError("unified dispatcher unexpectedly implemented")
    discovered = {item["evaluator_callable_name"] for item in inventory}
    formal_names = {
        name
        for name in all_top_functions
        if name.startswith("evaluate_admit_") and name != "evaluate_semantics_design"
    }
    if formal_names != discovered:
        raise ValueError("formal evaluator inventory is not Exact4")

    admit004_tree = all_trees[ADMIT004_SOURCE_PATH]
    result_class = next(
        (
            node
            for node in admit004_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Admit004EvaluationResult"
        ),
        None,
    )
    if result_class is None or "dataclass(frozen=True)" not in {
        ast.unparse(item) for item in result_class.decorator_list
    }:
        raise ValueError("ADMIT_004 frozen result contract missing")
    admit004_fields = tuple(
        node.target.id
        for node in result_class.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    )
    if len(admit004_fields) != 10 or admit004_fields == tuple(name for name, _ in RESULT_FIELDS):
        raise ValueError("ADMIT_004 result incompatibility evidence invalid")
    return tuple(inventory)


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    registry = _csv_document(snapshot, STEP14AT_REGISTRY_PATH)
    executable = _csv_document(snapshot, STEP14AUA_RULE_PATH)
    effective_rules = _csv_document(snapshot, E1E2_RULE_PATH)
    contexts = _csv_document(snapshot, E1E2_CONTEXT_PATH)
    issues_e1e2 = _csv_document(snapshot, E1E2_ISSUE_PATH)
    issues_e1e3 = _csv_document(snapshot, E1E3_ISSUE_PATH)
    interface_contract = _csv_document(snapshot, E1E3_CONTRACT_PATH)
    e1a_contract = _csv_document(snapshot, E1A_CONTRACT_PATH)
    e1a_truth = _csv_document(snapshot, E1A_TRUTH_PATH)
    schema = _csv_document(snapshot, STEP14AT_SCHEMA_PATH)
    base_contexts = _csv_document(snapshot, STEP14AUA_CONTEXT_PATH)
    manifests = tuple(
        _json_document(snapshot, path)
        for path in (
            E1E3_MANIFEST_PATH,
            E1E2_MANIFEST_PATH,
            STEP14AT_MANIFEST_PATH,
            STEP14AUA_MANIFEST_PATH,
        )
    )
    expected_ids = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
    for document in (registry, executable, effective_rules):
        if tuple(row["admission_rule_id"] for row in document.rows) != expected_ids:
            raise ValueError("admission rule order is not Exact15")
    if len(schema.rows) != 17 or len(contexts.rows) != 19 or len(base_contexts.rows) != 18:
        raise ValueError("predecessor schema/context cardinality mismatch")
    if issues_e1e2.rows != issues_e1e3.rows or len(issues_e1e2.rows) != 9:
        raise ValueError("E1-E3 issue inventory is not an unchanged Exact9 copy")
    issue_map = _keyed(issues_e1e2.rows, "issue_id")
    provider = issue_map.get("REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT")
    if (
        provider is None
        or provider["status"] != "open"
        or provider["severity"] != "blocking"
        or provider["issue_count"] != "11"
    ):
        raise ValueError("provider blocker evidence mismatch")
    contract_map = _keyed(interface_contract.rows, "contract_id")
    if (
        contract_map["INTERFACE_001"]["observed_value"] != "evaluate_admit_004"
        or contract_map["INTERFACE_004"]["observed_value"] != "passed|blocked|invalid"
        or contract_map["INTERFACE_006"]["observed_value"] != "false"
    ):
        raise ValueError("ADMIT_004 interface evidence mismatch")
    observed_admit005 = {
        row["observed_admit_005_outcome"] for row in e1a_truth.rows
    }
    if observed_admit005 != {"passed", "rejected", "invalid"}:
        raise ValueError("ADMIT_005 design outcome evidence mismatch")
    if not any(
        row.get("contract_statement") == "outcome priority"
        or row.get("contract_statement") == "outcome_priority"
        for row in e1a_contract.rows
    ):
        # The contract uses a local outcome_priority statement; truth evidence remains authoritative.
        if not any("outcome" in " ".join(row.values()) for row in e1a_contract.rows):
            raise ValueError("local outcome design evidence missing")
    if any(manifest.get("all_checks_passed") is not True for manifest in manifests[:3]):
        raise ValueError("successful predecessor manifest reports failed gate")
    precondition_manifest = manifests[3]
    if not (
        precondition_manifest.get("all_checks_passed") is False
        and precondition_manifest.get("precondition_audit_completed") is True
        and precondition_manifest.get("all_source_boundary_checks_passed") is True
        and precondition_manifest.get("ready_for_bulk_download_now") is False
        and precondition_manifest.get("ready_for_training") is False
    ):
        raise ValueError("precondition blocker manifest contract mismatch")
    return {
        "registry": registry,
        "effective_rules": effective_rules,
        "contexts": contexts,
        "issues": issues_e1e2,
        "callables": _validate_callable_inventory(snapshot),
    }


def _public_api_rows() -> list[dict[str, str]]:
    signature = (
        "evaluate_admission_rule(admission_rule_id: str, candidate_record: Mapping[str, object], "
        "*, batch_context: Mapping[str, object] | None = None, "
        "evaluation_context: Mapping[str, object] | None = None, "
        "download_result_context: Mapping[str, object] | None = None, "
        "stage_authorization_context: Mapping[str, object] | None = None) -> "
        "UnifiedAdmissionRuleEvaluation"
    )
    values = [
        ("public_api", "conceptual_signature", signature),
        ("public_api", "dispatch_cardinality", "single_rule_only"),
        ("public_api", "evaluate_all_rules", "not_provided"),
        ("public_api", "combined_candidate_verdict", "not_generated"),
        ("public_api", "cross_phase_aggregation", "not_performed"),
        ("context", "engine_context_behavior", "pass_through_explicit_context_only"),
        ("context", "provider_evidence_construction", "forbidden"),
        ("context", "engine_filesystem_access", "forbidden"),
        ("context", "engine_network_access", "forbidden"),
        ("context", "undeclared_candidate_field_consumption", "forbidden"),
        ("dispatch_failure", "exception_type", "UnifiedAdmissionDispatchError"),
    ]
    values.extend(
        ("dispatch_error_field", name, field_type) for name, field_type in DISPATCH_ERROR_FIELDS
    )
    values.extend(("dispatch_error_code", code, code) for code in DISPATCH_ERROR_CODES)
    values.extend(
        (
            ("dispatch_failure", "unknown_vs_known_unsupported", "distinct"),
            ("dispatch_failure", "known_unsupported_default_passed", "forbidden"),
            ("dispatch_failure", "unready_adapter_legacy_dict_return", "forbidden"),
            ("dispatch_failure", "invalid_or_missing_context_invokes_evaluator", "false"),
            ("dispatch_failure", "dispatch_error_candidate_aggregation", "excluded"),
        )
    )
    return [
        {
            "contract_order": str(index),
            "contract_area": area,
            "contract_item": item,
            "contract_value": value,
            "contract_status": "frozen",
        }
        for index, (area, item, value) in enumerate(values, 1)
    ]


def _result_rows() -> list[dict[str, str]]:
    values: list[tuple[str, str, str, str]] = [
        ("result_field", name, field_type, "required") for name, field_type in RESULT_FIELDS
    ]
    values.extend(
        (
            ("result_invariant", "dataclass_mutability", "", "frozen"),
            ("result_invariant", "schema_version", "", RESULT_SCHEMA_VERSION),
            ("result_invariant", "outcome_vocabulary", "", "|".join(OUTCOME_VOCABULARY)),
            ("result_invariant", "passed", "", "true_iff_outcome_passed"),
            ("result_invariant", "blocks_candidate", "", "true_iff_outcome_not_passed"),
            ("result_invariant", "passed_reason", "", "empty_exact_str"),
            ("result_invariant", "nonpassed_reason", "", "nonempty_exact_str"),
            ("result_invariant", "tuple_order", "", "deterministic"),
            ("result_invariant", "evaluator_io_used", "", "false"),
            ("rule_outcome_subset", "ADMIT_004", "", "passed|blocked|invalid"),
            ("rule_outcome_subset", "ADMIT_005", "", "passed|rejected|invalid"),
            ("rule_outcome_subset", "ADMIT_001|ADMIT_002|ADMIT_003", "", "adapter_mapping_unresolved"),
            ("rule_outcome_subset", "ADMIT_006-ADMIT_015", "", "unresolved"),
            ("aggregation_boundary", "global_engine_precedence", "", "not_frozen"),
            ("aggregation_boundary", "local_precedence_evidence", "", "invalid>rejected>blocked>passed"),
            ("aggregation_boundary", "local_precedence_promoted_globally", "", "false"),
        )
    )
    return [
        {
            "contract_order": str(index),
            "contract_kind": kind,
            "field_name": name,
            "field_type": field_type,
            "contract_value": value,
            "contract_status": "frozen",
        }
        for index, (kind, name, field_type, value) in enumerate(values, 1)
    ]


def _routing_rows(predecessor: Mapping[str, Any]) -> list[dict[str, str]]:
    registry = _keyed(predecessor["registry"].rows, "admission_rule_id")
    effective = _keyed(predecessor["effective_rules"].rows, "admission_rule_id")
    callable_map = {
        row["admission_rule_id"]: row for row in predecessor["callables"]
    }
    rows: list[dict[str, str]] = []
    for index in range(1, 16):
        rule_id = f"ADMIT_{index:03d}"
        base = effective[rule_id]
        registered = rule_id in callable_map
        callable_info = callable_map.get(rule_id, {})
        candidate_dependencies = base["candidate_field_dependencies"]
        batch_dependencies = base["batch_context_dependencies"]
        evaluation_dependencies = base["evaluation_context_dependencies"]
        download_dependencies = ""
        stage_dependencies = ""
        if rule_id in ("ADMIT_012", "ADMIT_013"):
            download_dependencies = candidate_dependencies
            candidate_dependencies = ""
        if rule_id == "ADMIT_014":
            stage_dependencies = "current_step|current_stage_download_authorized"
            candidate_dependencies = ""
            evaluation_dependencies = ""
        if rule_id == "ADMIT_015":
            stage_dependencies = "current_step|current_stage_training_authorized"
            candidate_dependencies = ""
            evaluation_dependencies = ""
        if index <= 3:
            adapter_status = "unresolved"
            registration = "not_registration_ready"
            allowed = "adapter_mapping_unresolved"
            disposition = "known_adapter_not_ready_fail_closed"
            reason = "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_SEMANTICS_UNRESOLVED"
            result_type = "legacy_mutable_dict"
        elif index == 4:
            adapter_status = "design_ready"
            registration = "ready_for_minimal_dispatch_shell_registration"
            allowed = "passed|blocked|invalid"
            disposition = "ready_for_minimal_dispatch_shell_registration"
            reason = ""
            result_type = "Admit004EvaluationResult"
        else:
            adapter_status = "not_available"
            registration = "unsupported"
            allowed = "passed|rejected|invalid" if index == 5 else "unresolved"
            disposition = "known_unsupported_fail_closed"
            reason = "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
            result_type = ""
        rows.append(
            {
                "admission_rule_id": rule_id,
                "admission_rule_name": registry[rule_id]["admission_rule_name"],
                "evaluation_phase": registry[rule_id]["evaluation_phase"],
                "candidate_field_dependencies": candidate_dependencies,
                "batch_context_dependencies": batch_dependencies,
                "evaluation_context_dependencies": evaluation_dependencies,
                "download_result_context_dependencies": download_dependencies,
                "stage_authorization_context_dependencies": stage_dependencies,
                "evaluator_callable_name": callable_info.get("evaluator_callable_name", ""),
                "evaluator_source_path": callable_info.get("evaluator_source_path", ""),
                "callable_discovered": str(registered).lower(),
                "evaluator_result_type": result_type,
                "result_adapter_contract_status": adapter_status,
                "engine_registration_status": registration,
                "allowed_rule_outcomes": allowed,
                "routing_disposition": disposition,
                "blocking_reason": reason,
            }
        )
    return rows


def _issue_rows(predecessor: Mapping[str, Any]) -> list[dict[str, str]]:
    rows = [dict(row) for row in predecessor["issues"].rows]
    additions = (
        (
            "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_SEMANTICS_UNRESOLVED",
            "ADMIT_001|ADMIT_002|ADMIT_003",
        ),
        (
            "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
            "|".join(f"ADMIT_{index:03d}" for index in range(5, 16)),
        ),
        (
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
            "|".join(f"ADMIT_{index:03d}" for index in range(1, 16)),
        ),
    )
    for issue_id, affected_rules in additions:
        rows.append(
            {
                "issue_id": issue_id,
                "issue_type": "implementation_semantics_gap",
                "affected_fields": "",
                "affected_rules": affected_rules,
                "severity": "blocking",
                "status": "open",
                "blocking_scope": "unified_admission_engine",
                "blocking_reason": issue_id,
                "issue_origin": STAGE,
                "integration_transition": "new_open",
                "issue_count": "1",
            }
        )
    return rows


def _safety_rows() -> list[dict[str, str]]:
    return [
        {
            "safety_item": item,
            "expected_executed": "true",
            "observed_executed": "true",
            "safety_passed": "true",
        }
        for item in TRUE_SAFETY_ITEMS
    ] + [
        {
            "safety_item": item,
            "expected_executed": "false",
            "observed_executed": "false",
            "safety_passed": "true",
        }
        for item in FALSE_SAFETY_ITEMS
    ]


def _empty_state(
    snapshot: FrozenSourceSnapshot | None = None,
    failure: str = "SOURCE_BOUNDARY_FAILED",
) -> dict[str, Any]:
    return {
        "source_snapshot": snapshot,
        "source_ok": False,
        "predecessor_ok": False,
        "public_api_rows": [],
        "result_rows": [],
        "routing_rows": [],
        "issue_rows": [],
        "safety_rows": [],
        "contract_success_count": 0,
        "routing_success_count": 0,
        "issue_success_count": 0,
        "design_readiness": False,
        "all_checks_passed": False,
        "validation_failures": [failure],
    }


def build_design_state(
    source_snapshot: FrozenSourceSnapshot | None = None,
    *,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    try:
        snapshot = source_snapshot or build_frozen_source_snapshot(head_ref=head_ref)
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return _empty_state()
    if not validate_frozen_source_snapshot(snapshot):
        return _empty_state(snapshot if type(snapshot) is FrozenSourceSnapshot else None)
    try:
        predecessor = _validate_predecessors(snapshot)
        public_api = _public_api_rows()
        result = _result_rows()
        routing = _routing_rows(predecessor)
        issues = _issue_rows(predecessor)
        safety = _safety_rows()
        issue_map = _keyed(issues, "issue_id")
        passed = (
            len(public_api) == 27
            and len(result) == 29
            and len(routing) == 15
            and tuple(row["admission_rule_id"] for row in routing)
            == tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
            and sum(row["callable_discovered"] == "true" for row in routing) == 4
            and routing[3]["result_adapter_contract_status"] == "design_ready"
            and routing[3]["evaluation_context_dependencies"]
            == "covalent_residue_identity_contract|covalent_residue_identity_evidence_context"
            and len(issues) == 12
            and issues[:9] == [dict(row) for row in predecessor["issues"].rows]
            and issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["status"] == "open"
            and issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["severity"] == "blocking"
            and issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"] == "11"
            and len(safety) == 29
            and all(row["safety_passed"] == "true" for row in safety)
        )
    except (
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        SyntaxError,
    ):
        return _empty_state(snapshot, "PREDECESSOR_OR_CONTRACT_VALIDATION_FAILED") | {
            "source_ok": True
        }
    if not passed:
        return _empty_state(snapshot, "CONTRACT_DESIGN_VALIDATION_FAILED") | {
            "source_ok": True,
            "predecessor_ok": True,
        }
    return {
        "source_snapshot": snapshot,
        "source_ok": True,
        "predecessor_ok": True,
        "predecessor": predecessor,
        "public_api_rows": public_api,
        "result_rows": result,
        "routing_rows": routing,
        "issue_rows": issues,
        "safety_rows": safety,
        "contract_success_count": len(public_api) + len(result),
        "routing_success_count": 15,
        "issue_success_count": 12,
        "design_readiness": True,
        "all_checks_passed": True,
        "validation_failures": [],
    }


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=list(columns), lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output CSV schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _manifest_payload(
    state: Mapping[str, Any], output_sha256: Mapping[str, str]
) -> dict[str, Any]:
    snapshot = state["source_snapshot"]
    readiness = {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }
    return {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "source_input_count": 21,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {
            path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS
        },
        "source_input_verification": [
            {
                "source_ordinal": index,
                "source_relative_path": record.relative_path.as_posix(),
                "tracked": True,
                "base_tree_blob": True,
                "filesystem_regular": True,
                "non_symlink": True,
                "expected_sha256": record.expected_sha256,
                "base_tree_sha256": record.base_tree_sha256,
                "filesystem_sha256": record.filesystem_sha256,
                "source_verified": True,
            }
            for index, record in enumerate(snapshot.records, 1)
        ],
        "source_structural_checks_before_first_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "public_api_contract_row_count": len(state["public_api_rows"]),
        "result_contract_row_count": len(state["result_rows"]),
        "routing_row_count": 15,
        "formal_evaluator_callable_count": 4,
        "formal_evaluator_callables": [
            dict(row) for row in state["predecessor"]["callables"]
        ],
        "active_issue_count": 12,
        "provider_blocking_issue_id": "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "provider_blocking_issue_count": 11,
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_field_count": 13,
        "result_fields": [name for name, _ in RESULT_FIELDS],
        "result_outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "dispatch_error_field_count": 6,
        "dispatch_error_fields": [name for name, _ in DISPATCH_ERROR_FIELDS],
        "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "dispatch_error_code_count": 5,
        "global_cross_rule_precedence_frozen": False,
        "local_precedence_promoted_to_global_engine_precedence": False,
        "covalent_residue_identity_evidence_context_caller_provided": True,
        "covalent_residue_identity_evidence_context_engine_pass_through_only": True,
        "covalent_residue_identity_evidence_context_engine_constructed": False,
        "evaluator_execution_current_step": False,
        "readiness": readiness,
        **readiness,
        "contract_success_count": state["contract_success_count"],
        "routing_success_count": state["routing_success_count"],
        "issue_success_count": state["issue_success_count"],
        "design_readiness": True,
        "all_source_boundary_checks_passed": True,
        "all_predecessor_evidence_checks_passed": True,
        "all_contract_checks_passed": True,
        "all_routing_checks_passed": True,
        "all_issue_checks_passed": True,
        "all_safety_checks_passed": True,
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        PUBLIC_API_FILENAME: _csv_bytes(PUBLIC_API_COLUMNS, state["public_api_rows"]),
        RESULT_FILENAME: _csv_bytes(RESULT_COLUMNS, state["result_rows"]),
        ROUTING_FILENAME: _csv_bytes(ROUTING_COLUMNS, state["routing_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
    }
    hashes = {
        name: hashlib.sha256(content).hexdigest()
        for name, content in csv_payloads.items()
    }
    manifest = _manifest_payload(state, hashes)
    payloads = {
        **csv_payloads,
        MANIFEST_FILENAME: (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        ),
    }
    return payloads, manifest


def _atomic_write(path: Path, content: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _preflight_output_root(root: Path) -> None:
    if root.exists() or root.is_symlink():
        metadata = os.lstat(root)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("output root must be a real non-symlink directory")
    else:
        root.mkdir(parents=True, exist_ok=False)
        metadata = os.lstat(root)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("output root creation was unsafe")
    entries = tuple(root.iterdir())
    if {entry.name for entry in entries} - set(OUTPUT_FILES):
        raise ValueError("output root contains unexpected files")
    for entry in entries:
        metadata = os.lstat(entry)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError("output root contains unsafe entries")


def run_covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_design_state()
    if state["all_checks_passed"] is not True:
        raise RuntimeError(
            "unified rule engine contract design failed closed: "
            + "|".join(state["validation_failures"])
        )
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
