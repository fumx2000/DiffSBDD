"""Step14AU-E1-E2 ADMIT_004 reconciliation integration gate v1.

This module reads only the twelve frozen, committed predecessor outputs declared
in ``SOURCE_SPECS``.  It validates every source boundary before the first source
content read, parses CSV/JSON exclusively from frozen bytes, and materializes a
metadata-only effective admission view.  It does not implement an evaluator.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path
import stat
import subprocess
import tempfile
from typing import Any, Callable, Iterable, Mapping, Sequence


PROJECT = "CovaPIE"
STEP = "Step14AU-E1-E2"
BASE_COMMIT = "d7995cb28b616c2097ae8ee2fbd77dc3761a4a01"
STAGE = (
    "covapie_bulk_download_admission_admit_004_generic_atom_identity_"
    "evidence_context_reconciliation_integration_gate_v1"
)
E1E1_STAGE = (
    "covapie_bulk_download_admission_admit_004_generic_atom_identity_"
    "evidence_context_reconciliation_design_gate_v1"
)
INTEGRATION_REASON = (
    "generic atom identity and exact9-bound identity evidence context semantics "
    "integrated; ADMIT_005 retains CYS/SG scope enforcement"
)
ATOM_SOURCE_VALUE_CONTRACT = (
    "generic exact non-empty ASCII atom identity; whitespace and complete "
    "dot/question markers forbidden; exact-preserve; no semantic maximum"
)
EVIDENCE_CONTEXT_ITEM = "covalent_residue_identity_evidence_context"
RESOLVED_ISSUE_ID = (
    "ADMIT_004_GENERIC_ATOM_AND_EVIDENCE_CONTEXT_SEMANTICS_UNRESOLVED"
)
PROVIDER_ISSUE_ID = "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"
EXACT11_REASON = "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
RECOMMENDED_NEXT_STEP = "implement_covapie_admit_004_rule_logic_interface_v1"

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_RELATIVE_DIR = Path("data/derived/covalent_small") / STAGE

E1D_DIR = (
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_covalent_residue_insertion_present_"
    "value_grammar_integration_gate_v1"
)
E1E1_DIR = f"data/derived/covalent_small/{E1E1_STAGE}"


@dataclass(frozen=True)
class SourceSpec:
    relative_path: str
    expected_sha256: str


@dataclass(frozen=True)
class SourceStructure:
    tracked: bool
    base_tree_blob: bool
    filesystem_regular: bool
    non_symlink: bool

    @property
    def passed(self) -> bool:
        return all(
            (
                self.tracked,
                self.base_tree_blob,
                self.filesystem_regular,
                self.non_symlink,
            )
        )


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    ordinal: int
    relative_path: str
    expected_sha256: str
    base_tree_sha256: str
    filesystem_sha256: str
    content: bytes
    structure: SourceStructure

    def verification_record(self) -> dict[str, Any]:
        return {
            "source_ordinal": self.ordinal,
            "source_relative_path": self.relative_path,
            "expected_sha256": self.expected_sha256,
            "base_tree_sha256": self.base_tree_sha256,
            "filesystem_sha256": self.filesystem_sha256,
            "tracked": self.structure.tracked,
            "base_tree_blob": self.structure.base_tree_blob,
            "filesystem_regular": self.structure.filesystem_regular,
            "non_symlink": self.structure.non_symlink,
            "source_verified": True,
        }


SOURCE_SPECS: tuple[SourceSpec, ...] = (
    SourceSpec(
        f"{E1D_DIR}/covapie_covalent_residue_insertion_present_value_grammar_integrated_rule_matrix.csv",
        "98e368781fe0c2bac6cd9123b0cbc49ffeecc8c1de577607ce9b4866c2b310d0",
    ),
    SourceSpec(
        f"{E1D_DIR}/covapie_covalent_residue_insertion_present_value_grammar_integrated_field_matrix.csv",
        "bd319bd2e5931b316c8579259729a94029d117844b2ceabda717604dc1d4483b",
    ),
    SourceSpec(
        f"{E1D_DIR}/covapie_covalent_residue_insertion_present_value_grammar_integrated_context_matrix.csv",
        "106f0080ef01c76983d594a039d12741dd29fd52cddb7fd2b205dcd75bd7e83b",
    ),
    SourceSpec(
        f"{E1D_DIR}/covapie_covalent_residue_insertion_present_value_grammar_integration_safety_audit.csv",
        "1cf577d6bc5bbbf1783606e5c8245592ed7ec00a357b43425aec325cdffcea3f",
    ),
    SourceSpec(
        f"{E1D_DIR}/covapie_covalent_residue_insertion_present_value_grammar_integration_issue_inventory.csv",
        "7cf0a9ff421ba987655c4dac4564c04dbaa854cd4f725b18136642f223762d30",
    ),
    SourceSpec(
        f"{E1D_DIR}/covapie_covalent_residue_insertion_present_value_grammar_integration_manifest.json",
        "3b2a9a4c83d1dca999bc805ead8f3298fb75687034c4eae7595e2a5e22e26fa2",
    ),
    SourceSpec(
        f"{E1E1_DIR}/covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_contract.csv",
        "162a39f0080589efb0e87c32dcabd05270025cd2cb3c10f4e3e6a14857104376",
    ),
    SourceSpec(
        f"{E1E1_DIR}/covapie_admit_004_generic_atom_identity_evidence_context_truth_matrix.csv",
        "7c65167c31c40170e06fa42ed8eab08c1b6d800a67e466aa33885ba3449551a3",
    ),
    SourceSpec(
        f"{E1E1_DIR}/covapie_admit_004_generic_atom_identity_evidence_context_source_boundary_audit.csv",
        "be149b86c79fe15da331ba9590884282d3b4a4ac504fea48802c73783e4b4305",
    ),
    SourceSpec(
        f"{E1E1_DIR}/covapie_admit_004_generic_atom_identity_evidence_context_safety_audit.csv",
        "0100fcc885c409e7c59a8e4bed3c293a764f806f410cac0e4c7bcc9c7d6c524b",
    ),
    SourceSpec(
        f"{E1E1_DIR}/covapie_admit_004_generic_atom_identity_evidence_context_issue_readiness_inventory.csv",
        "6a7c4f7b81cbcf6e2d2bd0a6bf07fab6a24e2d7e94aba65199cfa468e72c5a7a",
    ),
    SourceSpec(
        f"{E1E1_DIR}/covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_design_manifest.json",
        "7834abfca88d07d8cff92dc75212b1cc2ea932d3b46484602d97bc9acbb0a485",
    ),
)

RULE_OUTPUT = "covapie_admit_004_generic_atom_identity_evidence_context_reconciled_rule_matrix.csv"
FIELD_OUTPUT = "covapie_admit_004_generic_atom_identity_evidence_context_reconciled_field_matrix.csv"
CONTEXT_OUTPUT = "covapie_admit_004_generic_atom_identity_evidence_context_reconciled_context_matrix.csv"
SAFETY_OUTPUT = "covapie_admit_004_generic_atom_identity_evidence_context_integration_safety_audit.csv"
ISSUE_OUTPUT = "covapie_admit_004_generic_atom_identity_evidence_context_integration_issue_inventory.csv"
MANIFEST_OUTPUT = "covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_integration_manifest.json"
OUTPUT_FILENAMES = (
    RULE_OUTPUT,
    FIELD_OUTPUT,
    CONTEXT_OUTPUT,
    SAFETY_OUTPUT,
    ISSUE_OUTPUT,
    MANIFEST_OUTPUT,
)

RULE_FIELDS = (
    "admission_rule_id",
    "admission_rule_name",
    "evaluation_phase",
    "candidate_field_dependencies",
    "batch_context_dependencies",
    "evaluation_context_dependencies",
    "external_filesystem_required",
    "network_required",
    "download_execution_result_required",
    "pure_in_memory_interface_possible",
    "dependency_contract_passed",
    "semantics_complete",
    "deterministic_evaluation_possible_now",
    "deterministic_evaluation_possible_after_contract_freeze",
    "implementation_disposition",
    "blocking_reasons",
    "source_stage",
    "integration_source_stage",
    "integration_applied",
    "integration_reason",
)
FIELD_FIELDS = (
    "field_name",
    "requirement_phase",
    "source_value_contract",
    "candidate_record_field",
    "producer_scope",
    "dependent_rules",
    "batch_context_required",
    "evaluation_context_dependencies",
    "allowed_values_defined",
    "normalization_defined",
    "exact_validation_defined",
    "implementation_semantics_complete",
    "semantics_evidence",
    "blocking_reasons",
    "field_contract_mapping_passed",
    "source_stage",
    "integration_source_stage",
    "integration_applied",
    "integration_reason",
)
CONTEXT_FIELDS = (
    "context_item",
    "context_scope",
    "required_by_rules",
    "provided_by_future_caller",
    "filesystem_access_inside_evaluator",
    "network_access_inside_evaluator",
    "deterministic_now",
    "deterministic_after_contract_freeze",
    "exact_contract_defined",
    "implementation_ready",
    "blocking_reasons",
    "source_stage",
    "integration_source_stage",
    "integration_applied",
    "integration_reason",
)
SAFETY_FIELDS = (
    "safety_item",
    "expected_executed",
    "observed_executed",
    "safety_passed",
)
ISSUE_FIELDS = (
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
CONTRACT_FIELDS = (
    "contract_id",
    "contract_area",
    "contract_statement",
    "expected_value",
    "observed_value",
    "contract_passed",
)
TRUTH_FIELDS = (
    "row_kind",
    "case_id",
    "input_residue_name",
    "input_atom_descriptor",
    "insertion_state",
    "context_case",
    "expected_admit_004_outcome",
    "observed_admit_004_outcome",
    "expected_admit_005_outcome",
    "observed_admit_005_outcome",
    "expected_reason",
    "observed_reason",
    "canonical_value",
    "truth_passed",
)
SOURCE_AUDIT_FIELDS = (
    "source_order",
    "source_relative_path",
    "tracked_by_git",
    "base_tree_blob",
    "filesystem_regular",
    "non_symlink",
    "sha256_expected",
    "sha256_base_tree",
    "sha256_filesystem",
    "source_verified",
)

EXPECTED_CANDIDATE_DEPENDENCIES = (
    "covalent_residue_name|covalent_residue_chain_id|covalent_residue_index|"
    "covalent_residue_atom_name|covalent_residue_locator_namespace|"
    "covalent_residue_insertion_code_state|covalent_residue_insertion_code|"
    "covalent_residue_locator_provenance_source_id|"
    "covalent_residue_locator_provenance_sha256"
)

SAFETY_EXECUTED = (
    "exact_source_reads",
    "e1d_effective_matrix_validation",
    "e1e1_reconciliation_design_validation",
    "target_rule_dependency_overlay",
    "target_field_contract_overlay",
    "evidence_context_row_addition",
    "issue_resolution_overlay",
    "exact11_invariant_validation",
)
SAFETY_NOT_EXECUTED = (
    "raw_read",
    "provenance_reference_dereference",
    "parser_execution",
    "provider_execution",
    "evaluator_implementation",
    "unified_rule_engine_integration",
    "candidate_record_materialization",
    "candidate_evaluation",
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


def failure_state(failures: Iterable[str]) -> dict[str, Any]:
    """Return the mandatory fail-closed state for a rejected integration run."""

    return {
        "integrated_rule_count": 0,
        "integrated_field_count": 0,
        "integrated_context_count": 0,
        "active_issue_count": 0,
        "integration_readiness": False,
        "all_checks_passed": False,
        "validation_failures": list(failures),
    }


class IntegrationGateError(RuntimeError):
    """A fail-closed source, predecessor, overlay, or output validation error."""

    def __init__(self, message: str, failures: Iterable[str] | None = None) -> None:
        super().__init__(message)
        self.failures = tuple(failures or (message,))
        self.state = failure_state(self.failures)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _inspect_source_structure(
    repo_root: Path, base_commit: str, spec: SourceSpec
) -> SourceStructure:
    tracked_result = _git(repo_root, "ls-files", "--error-unmatch", "--", spec.relative_path)
    tracked = tracked_result.returncode == 0

    tree_result = _git(repo_root, "ls-tree", "-z", base_commit, "--", spec.relative_path)
    base_tree_blob = False
    if tree_result.returncode == 0 and tree_result.stdout.endswith(b"\0"):
        entry = tree_result.stdout[:-1]
        try:
            metadata, encoded_path = entry.split(b"\t", 1)
            mode, object_type, _object_id = metadata.split(b" ", 2)
            base_tree_blob = (
                object_type == b"blob"
                and mode in {b"100644", b"100755"}
                and os.fsdecode(encoded_path) == spec.relative_path
            )
        except ValueError:
            base_tree_blob = False

    try:
        source_stat = os.lstat(repo_root / spec.relative_path)
    except OSError:
        filesystem_regular = False
        non_symlink = False
    else:
        filesystem_regular = stat.S_ISREG(source_stat.st_mode)
        non_symlink = not stat.S_ISLNK(source_stat.st_mode)

    return SourceStructure(
        tracked=tracked,
        base_tree_blob=base_tree_blob,
        filesystem_regular=filesystem_regular,
        non_symlink=non_symlink,
    )


def _read_filesystem_bytes(repo_root: Path, spec: SourceSpec) -> bytes:
    return (repo_root / spec.relative_path).read_bytes()


def _read_base_blob(repo_root: Path, base_commit: str, spec: SourceSpec) -> bytes:
    result = _git(repo_root, "cat-file", "blob", f"{base_commit}:{spec.relative_path}")
    if result.returncode != 0:
        raise IntegrationGateError(
            f"base-tree byte read failed for {spec.relative_path}: "
            f"{result.stderr.decode('utf-8', errors='replace').strip()}"
        )
    return result.stdout


def freeze_source_snapshots(
    repo_root: Path = REPO_ROOT,
    base_commit: str = BASE_COMMIT,
    *,
    structure_reader: Callable[[Path, str, SourceSpec], SourceStructure] = _inspect_source_structure,
    filesystem_reader: Callable[[Path, SourceSpec], bytes] = _read_filesystem_bytes,
    base_blob_reader: Callable[[Path, str, SourceSpec], bytes] = _read_base_blob,
) -> tuple[FrozenSourceSnapshot, ...]:
    """Freeze exact12 after completing all structural checks for all sources."""

    repo_root = Path(repo_root)
    structures = tuple(
        structure_reader(repo_root, base_commit, spec) for spec in SOURCE_SPECS
    )
    structural_failures = [
        f"source structure rejected: {spec.relative_path} ({structure!r})"
        for spec, structure in zip(SOURCE_SPECS, structures)
        if not structure.passed
    ]
    if structural_failures:
        raise IntegrationGateError(
            "exact12 structural validation failed", structural_failures
        )

    snapshots: list[FrozenSourceSnapshot] = []
    hash_failures: list[str] = []
    for ordinal, (spec, structure) in enumerate(
        zip(SOURCE_SPECS, structures), start=1
    ):
        try:
            filesystem_bytes = filesystem_reader(repo_root, spec)
            base_tree_bytes = base_blob_reader(repo_root, base_commit, spec)
        except (OSError, IntegrationGateError) as exc:
            hash_failures.append(f"source byte read failed: {spec.relative_path}: {exc}")
            continue
        filesystem_sha256 = _sha256(filesystem_bytes)
        base_tree_sha256 = _sha256(base_tree_bytes)
        if not (
            spec.expected_sha256 == base_tree_sha256 == filesystem_sha256
            and base_tree_bytes == filesystem_bytes
        ):
            hash_failures.append(
                f"source SHA drift: {spec.relative_path}: expected={spec.expected_sha256} "
                f"base={base_tree_sha256} filesystem={filesystem_sha256}"
            )
            continue
        snapshots.append(
            FrozenSourceSnapshot(
                ordinal=ordinal,
                relative_path=spec.relative_path,
                expected_sha256=spec.expected_sha256,
                base_tree_sha256=base_tree_sha256,
                filesystem_sha256=filesystem_sha256,
                content=filesystem_bytes,
                structure=structure,
            )
        )
    if hash_failures or len(snapshots) != len(SOURCE_SPECS):
        raise IntegrationGateError("exact12 SHA validation failed", hash_failures)
    return tuple(snapshots)


def _snapshot_map(
    snapshots: Sequence[FrozenSourceSnapshot],
) -> dict[str, FrozenSourceSnapshot]:
    actual_paths = tuple(snapshot.relative_path for snapshot in snapshots)
    expected_paths = tuple(spec.relative_path for spec in SOURCE_SPECS)
    if actual_paths != expected_paths:
        raise IntegrationGateError("frozen snapshot order/path contract failed")
    return {snapshot.relative_path: snapshot for snapshot in snapshots}


def _parse_csv(
    snapshot: FrozenSourceSnapshot, expected_fields: Sequence[str]
) -> list[dict[str, str]]:
    try:
        text = snapshot.content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IntegrationGateError(
            f"CSV is not UTF-8: {snapshot.relative_path}: {exc}"
        ) from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != tuple(expected_fields):
        raise IntegrationGateError(
            f"CSV header drift: {snapshot.relative_path}: {reader.fieldnames!r}"
        )
    rows = [dict(row) for row in reader]
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise IntegrationGateError(f"malformed CSV row: {snapshot.relative_path}")
    return rows


def _parse_json(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    try:
        value = json.loads(snapshot.content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntegrationGateError(
            f"invalid JSON: {snapshot.relative_path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise IntegrationGateError(f"JSON root must be object: {snapshot.relative_path}")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IntegrationGateError(message)


def _find_unique(rows: Sequence[Mapping[str, str]], key: str, value: str) -> Mapping[str, str]:
    matches = [row for row in rows if row.get(key) == value]
    _require(len(matches) == 1, f"expected one {key}={value!r}, found {len(matches)}")
    return matches[0]


def _validate_e1d(
    source_map: Mapping[str, FrozenSourceSnapshot]
) -> dict[str, Any]:
    rules = _parse_csv(source_map[SOURCE_SPECS[0].relative_path], RULE_FIELDS)
    fields = _parse_csv(source_map[SOURCE_SPECS[1].relative_path], FIELD_FIELDS)
    contexts = _parse_csv(source_map[SOURCE_SPECS[2].relative_path], CONTEXT_FIELDS)
    safety = _parse_csv(source_map[SOURCE_SPECS[3].relative_path], SAFETY_FIELDS)
    issues = _parse_csv(source_map[SOURCE_SPECS[4].relative_path], ISSUE_FIELDS)
    manifest = _parse_json(source_map[SOURCE_SPECS[5].relative_path])

    _require(len(rules) == 15, "E1-D rule_count must be 15")
    _require(len(fields) == 22, "E1-D field_count must be 22")
    _require(len(contexts) == 18, "E1-D context_count must be 18")
    _require(len(issues) == 9, "E1-D active_issue_count must be 9")
    _require(len(safety) == 23, "E1-D safety row count must be 23")
    _require(
        [row["admission_rule_id"] for row in rules]
        == [f"ADMIT_{index:03d}" for index in range(1, 16)],
        "E1-D rule order drifted",
    )
    _require(
        sum(row["semantics_complete"] == "true" for row in rules) == 7,
        "E1-D semantics-complete rule count must be 7",
    )
    _require(
        sum(row["implementation_semantics_complete"] == "true" for row in fields)
        == 12,
        "E1-D implementation-semantics-complete field count must be 12",
    )
    _require(
        sum(row["implementation_ready"] == "true" for row in contexts) == 9,
        "E1-D implementation-ready context count must be 9",
    )
    admit_004 = _find_unique(rules, "admission_rule_id", "ADMIT_004")
    _require(
        admit_004["candidate_field_dependencies"] == EXPECTED_CANDIDATE_DEPENDENCIES,
        "E1-D ADMIT_004 exact9 candidate dependencies drifted",
    )
    _require(
        admit_004["evaluation_context_dependencies"]
        == "covalent_residue_identity_contract",
        "E1-D ADMIT_004 context dependency drifted",
    )
    for key, expected in {
        "semantics_complete": "true",
        "deterministic_evaluation_possible_now": "true",
        "deterministic_evaluation_possible_after_contract_freeze": "true",
        "implementation_disposition": "rule_logic_ready",
        "blocking_reasons": "",
    }.items():
        _require(admit_004[key] == expected, f"E1-D ADMIT_004 {key} drifted")
    atom_field = _find_unique(fields, "field_name", "covalent_residue_atom_name")
    _require(
        atom_field["source_value_contract"] == "must be SG for v1 Cys scope",
        "E1-D atom field predecessor contract drifted",
    )
    provider = _find_unique(issues, "issue_id", PROVIDER_ISSUE_ID)
    _require(
        provider["status"] == "open"
        and provider["severity"] == "blocking"
        and provider["issue_count"] == "11",
        "E1-D provider blocker must remain open/blocking/count=11",
    )
    _require(all(row["safety_passed"] == "true" for row in safety), "E1-D safety failed")

    expected_manifest = {
        "all_checks_passed": True,
        "integrated_rule_count": 15,
        "integrated_field_count": 22,
        "integrated_context_count": 18,
        "active_issue_count": 9,
        "semantics_complete_rule_count": 7,
        "implementation_semantics_complete_field_count": 12,
        "implementation_ready_context_count": 9,
        "admit_004_rule_logic_ready": True,
        "admit_005_rule_logic_ready": True,
        "exact11_count": 11,
        "exact11_insertion_unknown_count": 11,
        "exact11_insertion_value_empty_count": 11,
        "exact11_effective_blocked_count": 11,
        "exact11_reason": EXACT11_REASON,
        "provider_blocking_issue_count": 11,
        "real_provider_export_blocking_rows_resolved": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
    }
    for key, expected in expected_manifest.items():
        _require(manifest.get(key) == expected, f"E1-D manifest {key} drifted")
    return {
        "rules": rules,
        "fields": fields,
        "contexts": contexts,
        "issues": issues,
        "manifest": manifest,
    }


def _validate_e1e1(
    source_map: Mapping[str, FrozenSourceSnapshot], e1d: Mapping[str, Any]
) -> dict[str, Any]:
    contract = _parse_csv(source_map[SOURCE_SPECS[6].relative_path], CONTRACT_FIELDS)
    truth = _parse_csv(source_map[SOURCE_SPECS[7].relative_path], TRUTH_FIELDS)
    source_audit = _parse_csv(
        source_map[SOURCE_SPECS[8].relative_path], SOURCE_AUDIT_FIELDS
    )
    safety = _parse_csv(source_map[SOURCE_SPECS[9].relative_path], SAFETY_FIELDS)
    issues = _parse_csv(source_map[SOURCE_SPECS[10].relative_path], ISSUE_FIELDS)
    manifest = _parse_json(source_map[SOURCE_SPECS[11].relative_path])

    _require(len(contract) == 28, "E1-E1 contract count must be 28")
    _require(all(row["contract_passed"] == "true" for row in contract), "E1-E1 contract failed")
    _require(len(truth) == 36, "E1-E1 truth count must be 36")
    _require(all(row["truth_passed"] == "true" for row in truth), "E1-E1 truth failed")
    group_counts = {
        group: sum(row["row_kind"] == group for row in truth)
        for group in (
            "generic_atom_valid",
            "generic_atom_invalid",
            "admit_004_admit_005_scope",
            "evidence_context_binding",
        )
    }
    _require(
        group_counts
        == {
            "generic_atom_valid": 8,
            "generic_atom_invalid": 8,
            "admit_004_admit_005_scope": 8,
            "evidence_context_binding": 12,
        },
        "E1-E1 truth group counts drifted",
    )
    _require(len(source_audit) == 16, "E1-E1 source audit count must be 16")
    _require(
        all(row["source_verified"] == "true" for row in source_audit),
        "E1-E1 source audit contains unverified source",
    )
    _require(len(safety) == 25, "E1-E1 safety row count must be 25")
    _require(all(row["safety_passed"] == "true" for row in safety), "E1-E1 safety failed")
    _require(len(issues) == 10, "E1-E1 active issue count must be 10")
    _require(issues[-1]["issue_id"] == RESOLVED_ISSUE_ID, "E1-E1 new issue must be last")
    _require(issues[:9] == e1d["issues"], "E1-E1 original nine issues drifted from E1-D")

    contract_by_id = {row["contract_id"]: row for row in contract}
    for contract_id in (
        "ATOM_001",
        "ATOM_002",
        "ATOM_003",
        "ATOM_004",
        "ATOM_005",
        "ATOM_006",
        "ATOM_007",
        "ATOM_008",
        "SCOPE_001",
        "SCOPE_002",
        "BINDING_001",
        "CONTEXT_001",
        "CONTEXT_002",
        "CONTEXT_003",
        "CONTEXT_004",
        "CONTEXT_005",
        "CONTEXT_006",
        "CONTEXT_007",
        "CONTEXT_008",
        "CONTEXT_009",
        "PRECEDENCE_001",
        "QUOTE_001",
        "INSERTION_REUSE_001",
        "READINESS_001",
        "READINESS_002",
    ):
        _require(contract_id in contract_by_id, f"E1-E1 missing contract {contract_id}")

    expected_manifest = {
        "all_checks_passed": True,
        "contract_count": 28,
        "contract_pass_count": 28,
        "truth_matrix_row_count": 36,
        "truth_matrix_pass_count": 36,
        "output_active_issue_count": 10,
        "new_issue_count": 1,
        "new_issue_id": RESOLVED_ISSUE_ID,
        "generic_atom_identity_semantics_design_frozen": True,
        "admit_004_admit_005_scope_separation_design_frozen": True,
        "identity_evidence_context_schema_design_frozen": True,
        "candidate_attestation_binding_design_frozen": True,
        "e1c_insertion_present_value_grammar_reused_exactly": True,
        "ready_for_generic_atom_evidence_context_successor_integration": True,
        "reconciled_admit_004_interface_implementation_ready": False,
        "exact11_count": 11,
        "exact11_effective_blocked_count": 11,
        "exact11_reason": EXACT11_REASON,
        "provider_blocking_issue_count": 11,
        "real_provider_export_blocking_rows_resolved": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
    }
    for key, expected in expected_manifest.items():
        _require(manifest.get(key) == expected, f"E1-E1 manifest {key} drifted")
    _require(
        manifest.get("truth_matrix_group_counts")
        == {
            "admit_004_admit_005_scope": 8,
            "evidence_context_binding": 12,
            "generic_atom_invalid": 8,
            "generic_atom_valid": 8,
        },
        "E1-E1 manifest truth groups drifted",
    )
    return {
        "contract": contract,
        "truth": truth,
        "issues": issues,
        "manifest": manifest,
    }


def validate_predecessors(
    snapshots: Sequence[FrozenSourceSnapshot],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_map = _snapshot_map(snapshots)
    e1d = _validate_e1d(source_map)
    e1e1 = _validate_e1e1(source_map, e1d)
    return e1d, e1e1


def _overlay_rules(rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    output = [dict(row) for row in rows]
    target = _find_unique(output, "admission_rule_id", "ADMIT_004")
    target.update(
        {
            "evaluation_context_dependencies": (
                "covalent_residue_identity_contract|"
                "covalent_residue_identity_evidence_context"
            ),
            "integration_source_stage": E1E1_STAGE,
            "integration_applied": "true",
            "integration_reason": INTEGRATION_REASON,
        }
    )
    return output


def _overlay_fields(rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    output = [dict(row) for row in rows]
    target = _find_unique(output, "field_name", "covalent_residue_atom_name")
    target.update(
        {
            "source_value_contract": ATOM_SOURCE_VALUE_CONTRACT,
            "allowed_values_defined": "true",
            "normalization_defined": "true",
            "exact_validation_defined": "true",
            "implementation_semantics_complete": "true",
            "semantics_evidence": E1E1_STAGE,
            "blocking_reasons": "",
            "integration_source_stage": E1E1_STAGE,
            "integration_applied": "true",
            "integration_reason": INTEGRATION_REASON,
        }
    )
    return output


def _overlay_contexts(rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    output = [dict(row) for row in rows]
    context_items = [row["context_item"] for row in output]
    _require(EVIDENCE_CONTEXT_ITEM not in context_items, "evidence context already present")
    insertion_index = context_items.index("covalent_residue_identity_contract") + 1
    output.insert(
        insertion_index,
        {
            "context_item": EVIDENCE_CONTEXT_ITEM,
            "context_scope": "evaluation_record_evidence",
            "required_by_rules": "ADMIT_004",
            "provided_by_future_caller": "true",
            "filesystem_access_inside_evaluator": "false",
            "network_access_inside_evaluator": "false",
            "deterministic_now": "true",
            "deterministic_after_contract_freeze": "true",
            "exact_contract_defined": "true",
            "implementation_ready": "true",
            "blocking_reasons": "",
            "source_stage": E1E1_STAGE,
            "integration_source_stage": E1E1_STAGE,
            "integration_applied": "true",
            "integration_reason": INTEGRATION_REASON,
        },
    )
    return output


def _build_safety_rows() -> list[dict[str, str]]:
    rows = []
    for item in SAFETY_EXECUTED:
        rows.append(
            {
                "safety_item": item,
                "expected_executed": "true",
                "observed_executed": "true",
                "safety_passed": "true",
            }
        )
    for item in SAFETY_NOT_EXECUTED:
        rows.append(
            {
                "safety_item": item,
                "expected_executed": "false",
                "observed_executed": "false",
                "safety_passed": "true",
            }
        )
    return rows


def _csv_bytes(fieldnames: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode(
        "utf-8"
    )


def _validate_overlay(
    e1d: Mapping[str, Any],
    e1e1: Mapping[str, Any],
    rules: Sequence[Mapping[str, str]],
    fields: Sequence[Mapping[str, str]],
    contexts: Sequence[Mapping[str, str]],
    issues: Sequence[Mapping[str, str]],
) -> None:
    _require(len(rules) == 15, "integrated rule count must be 15")
    _require(len(fields) == 22, "integrated field count must be 22")
    _require(len(contexts) == 19, "integrated context count must be 19")
    _require(len(issues) == 9, "active issue count must be 9")

    for before, after in zip(e1d["rules"], rules):
        if before["admission_rule_id"] != "ADMIT_004":
            _require(after == before, f"non-target rule changed: {before['admission_rule_id']}")
            continue
        allowed = {
            "evaluation_context_dependencies",
            "integration_source_stage",
            "integration_applied",
            "integration_reason",
        }
        _require(
            all(after[key] == before[key] for key in RULE_FIELDS if key not in allowed),
            "ADMIT_004 changed outside the authorized rule overlay",
        )
        _require(
            after["evaluation_context_dependencies"]
            == "covalent_residue_identity_contract|covalent_residue_identity_evidence_context",
            "ADMIT_004 evaluation context overlay drifted",
        )
    for before, after in zip(e1d["fields"], fields):
        if before["field_name"] != "covalent_residue_atom_name":
            _require(after == before, f"non-target field changed: {before['field_name']}")
            continue
        allowed = {
            "source_value_contract",
            "allowed_values_defined",
            "normalization_defined",
            "exact_validation_defined",
            "implementation_semantics_complete",
            "semantics_evidence",
            "blocking_reasons",
            "integration_source_stage",
            "integration_applied",
            "integration_reason",
        }
        _require(
            all(after[key] == before[key] for key in FIELD_FIELDS if key not in allowed),
            "atom field changed outside the authorized field overlay",
        )
        _require(after["source_value_contract"] == ATOM_SOURCE_VALUE_CONTRACT, "atom contract drifted")
        _require(after["candidate_record_field"] == "true", "atom candidate field changed")
        _require(after["dependent_rules"] == "ADMIT_004|ADMIT_005", "atom dependent rules changed")

    context_items = [row["context_item"] for row in contexts]
    insertion_index = context_items.index(EVIDENCE_CONTEXT_ITEM)
    _require(insertion_index > 0, "evidence context insertion position invalid")
    _require(
        context_items[insertion_index - 1] == "covalent_residue_identity_contract",
        "evidence context must immediately follow identity contract",
    )
    original_after_removal = list(contexts[:insertion_index]) + list(contexts[insertion_index + 1 :])
    _require(original_after_removal == e1d["contexts"], "original context rows changed")
    _require(issues == e1e1["issues"][:9], "remaining issues changed from E1-E1")
    _require(issues == e1d["issues"], "remaining issues changed from E1-D")

    _require(sum(row["semantics_complete"] == "true" for row in rules) == 7, "ready rule count drifted")
    _require(
        sum(row["implementation_semantics_complete"] == "true" for row in fields) == 12,
        "ready field count drifted",
    )
    _require(
        sum(row["implementation_ready"] == "true" for row in contexts) == 10,
        "ready context count must be 10",
    )
    provider = _find_unique(issues, "issue_id", PROVIDER_ISSUE_ID)
    _require(
        provider["status"] == "open"
        and provider["severity"] == "blocking"
        and provider["issue_count"] == "11",
        "provider blocker overlay drifted",
    )


def build_output_bytes(
    repo_root: Path = REPO_ROOT, base_commit: str = BASE_COMMIT
) -> dict[str, bytes]:
    """Validate exact12 and build all six deterministic success outputs in memory."""

    snapshots = freeze_source_snapshots(repo_root, base_commit)
    e1d, e1e1 = validate_predecessors(snapshots)
    rules = _overlay_rules(e1d["rules"])
    fields = _overlay_fields(e1d["fields"])
    contexts = _overlay_contexts(e1d["contexts"])
    issues = [dict(row) for row in e1e1["issues"] if row["issue_id"] != RESOLVED_ISSUE_ID]
    safety = _build_safety_rows()
    _require(len(safety) == 25, "safety row count must be exactly 25")
    _validate_overlay(e1d, e1e1, rules, fields, contexts, issues)

    outputs = {
        RULE_OUTPUT: _csv_bytes(RULE_FIELDS, rules),
        FIELD_OUTPUT: _csv_bytes(FIELD_FIELDS, fields),
        CONTEXT_OUTPUT: _csv_bytes(CONTEXT_FIELDS, contexts),
        SAFETY_OUTPUT: _csv_bytes(SAFETY_FIELDS, safety),
        ISSUE_OUTPUT: _csv_bytes(ISSUE_FIELDS, issues),
    }
    output_sha256 = {name: _sha256(content) for name, content in outputs.items()}
    manifest: dict[str, Any] = {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "expected_base_commit": base_commit,
        "manifest_schema_version": (
            "covapie_admit_004_generic_atom_identity_evidence_context_"
            "reconciliation_integration_manifest_v1"
        ),
        "all_checks_passed": True,
        "integration_readiness": True,
        "all_source_boundary_checks_passed": True,
        "all_e1d_predecessor_checks_passed": True,
        "all_e1e1_predecessor_checks_passed": True,
        "all_overlay_checks_passed": True,
        "all_safety_checks_passed": True,
        "source_structural_checks_before_first_content_read": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "source_input_count": 12,
        "source_input_paths": [snapshot.relative_path for snapshot in snapshots],
        "source_input_sha256": {
            snapshot.relative_path: snapshot.expected_sha256 for snapshot in snapshots
        },
        "source_input_verification": [
            snapshot.verification_record() for snapshot in snapshots
        ],
        "predecessor_e1d_rule_count": 15,
        "predecessor_e1d_field_count": 22,
        "predecessor_e1d_context_count": 18,
        "predecessor_e1d_active_issue_count": 9,
        "predecessor_e1d_semantics_complete_rule_count": 7,
        "predecessor_e1d_implementation_semantics_complete_field_count": 12,
        "predecessor_e1d_implementation_ready_context_count": 9,
        "predecessor_e1e1_contract_count": 28,
        "predecessor_e1e1_contract_pass_count": 28,
        "predecessor_e1e1_truth_count": 36,
        "predecessor_e1e1_truth_pass_count": 36,
        "predecessor_e1e1_active_issue_count": 10,
        "integrated_rule_count": 15,
        "integrated_field_count": 22,
        "integrated_context_count": 19,
        "active_issue_count": 9,
        "semantics_complete_rule_count": 7,
        "implementation_semantics_complete_field_count": 12,
        "implementation_ready_context_count": 10,
        "resolved_issue_ids": [RESOLVED_ISSUE_ID],
        "remaining_issue_ids": [row["issue_id"] for row in issues],
        "provider_blocking_issue_id": PROVIDER_ISSUE_ID,
        "provider_blocking_issue_count": 11,
        "exact11_count": 11,
        "exact11_insertion_unknown_count": 11,
        "exact11_insertion_value_empty_count": 11,
        "exact11_effective_blocked_count": 11,
        "exact11_passed_count": 0,
        "exact11_reason": EXACT11_REASON,
        "admit_004_rule_dependency_reconciled": True,
        "covalent_residue_atom_name_field_contract_reconciled": True,
        "identity_evidence_context_row_added": True,
        "reconciliation_issue_resolved": True,
        "generic_atom_identity_semantics_integrated_into_effective_schema": True,
        "admit_004_admit_005_scope_separation_integrated_into_effective_schema": True,
        "identity_evidence_context_integrated_into_effective_schema": True,
        "candidate_attestation_binding_integrated_into_effective_schema": True,
        "reconciled_admit_004_interface_implementation_ready": True,
        "admit_004_rule_logic_ready": True,
        "ready_for_admit_004_rule_logic_interface_implementation": True,
        "admit_005_rule_logic_ready": True,
        "e1c_insertion_present_value_grammar_reused_exactly": True,
        "feature_semantics_audit_required_before_training": True,
        "admit_004_evaluator_implemented": False,
        "unified_rule_engine_integrated": False,
        "parser_quote_class_roundtrip_verified": False,
        "real_provider_present_value_roundtrip_ready": False,
        "real_provider_export_blocking_rows_resolved": False,
        "candidate_records_materialized": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "raw_read_current_step": False,
        "provenance_reference_dereferenced_current_step": False,
        "parser_executed_current_step": False,
        "provider_executed_current_step": False,
        "evaluator_implemented_current_step": False,
        "unified_rule_engine_integrated_current_step": False,
        "candidate_records_materialized_current_step": False,
        "candidate_evaluation_current_step": False,
        "admission_records_modified_current_step": False,
        "sample_backfill_current_step": False,
        "network_accessed_current_step": False,
        "download_attempted_current_step": False,
        "checkpoint_accessed_current_step": False,
        "torch_used_current_step": False,
        "numpy_used_current_step": False,
        "rdkit_used_current_step": False,
        "model_forward_loss_training_used_current_step": False,
        "output_file_count": 6,
        "output_files": list(OUTPUT_FILENAMES),
        "output_sha256": output_sha256,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "validation_failures": [],
    }
    outputs[MANIFEST_OUTPUT] = _json_bytes(manifest)
    return outputs


def _validate_materialization_destination(destination: Path) -> None:
    """Create or preflight a real output directory before any output write."""

    try:
        destination_mode = os.lstat(destination).st_mode
    except FileNotFoundError:
        try:
            destination.mkdir(parents=True, exist_ok=False)
            destination_mode = os.lstat(destination).st_mode
        except OSError as exc:
            raise IntegrationGateError(
                f"cannot create safe materialization destination: {destination}: {exc}"
            ) from exc
    except OSError as exc:
        raise IntegrationGateError(
            f"cannot inspect materialization destination: {destination}: {exc}"
        ) from exc

    if stat.S_ISLNK(destination_mode) or not stat.S_ISDIR(destination_mode):
        raise IntegrationGateError(
            f"materialization destination must be a real directory: {destination}"
        )

    try:
        entries = list(destination.iterdir())
    except OSError as exc:
        raise IntegrationGateError(
            f"cannot inspect materialization destination entries: {destination}: {exc}"
        ) from exc
    extras = sorted(entry.name for entry in entries if entry.name not in OUTPUT_FILENAMES)
    if extras:
        raise IntegrationGateError(f"output directory contains extra entries: {extras}")

    rejected: list[str] = []
    for entry in entries:
        try:
            entry_mode = os.lstat(entry).st_mode
        except OSError:
            rejected.append(entry.name)
            continue
        if stat.S_ISLNK(entry_mode) or not stat.S_ISREG(entry_mode):
            rejected.append(entry.name)
    if rejected:
        raise IntegrationGateError(
            f"existing materialization output structure rejected: {sorted(rejected)}"
        )


def _atomic_write(path: Path, content: bytes) -> None:
    """Atomically replace one output via a flushed same-directory temporary file."""

    file_descriptor = -1
    temporary_path: Path | None = None
    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(file_descriptor, "wb") as stream:
            file_descriptor = -1
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    except OSError as exc:
        raise IntegrationGateError(f"atomic output write failed for {path}: {exc}") from exc
    finally:
        if file_descriptor >= 0:
            os.close(file_descriptor)
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def materialize(
    output_dir: Path | None = None,
    repo_root: Path = REPO_ROOT,
    base_commit: str = BASE_COMMIT,
) -> dict[str, str]:
    """Materialize the exact six success outputs after all checks have passed."""

    repo_root = Path(repo_root)
    destination = Path(output_dir) if output_dir is not None else repo_root / OUTPUT_RELATIVE_DIR
    outputs = build_output_bytes(repo_root, base_commit)
    _validate_materialization_destination(destination)
    for name in OUTPUT_FILENAMES:
        _atomic_write(destination / name, outputs[name])
    return {name: _sha256(outputs[name]) for name in OUTPUT_FILENAMES}


def validate_output_directory(
    output_dir: Path | None = None,
    repo_root: Path = REPO_ROOT,
    base_commit: str = BASE_COMMIT,
) -> dict[str, str]:
    """Validate exact output structure and bytes without modifying any file."""

    repo_root = Path(repo_root)
    destination = Path(output_dir) if output_dir is not None else repo_root / OUTPUT_RELATIVE_DIR
    expected = build_output_bytes(repo_root, base_commit)
    if not destination.is_dir() or destination.is_symlink():
        raise IntegrationGateError("output directory missing, non-directory, or symlink")
    entries = sorted(path.name for path in destination.iterdir())
    if entries != sorted(OUTPUT_FILENAMES):
        raise IntegrationGateError(
            f"output file set drifted: expected={sorted(OUTPUT_FILENAMES)} actual={entries}"
        )
    structures: list[tuple[Path, bool]] = []
    for name in OUTPUT_FILENAMES:
        path = destination / name
        try:
            mode = os.lstat(path).st_mode
        except OSError:
            structures.append((path, False))
        else:
            structures.append((path, stat.S_ISREG(mode) and not stat.S_ISLNK(mode)))
    rejected = [str(path) for path, passed in structures if not passed]
    if rejected:
        raise IntegrationGateError(f"output structure rejected: {rejected}")
    actual = {name: (destination / name).read_bytes() for name in OUTPUT_FILENAMES}
    mismatches = [name for name in OUTPUT_FILENAMES if actual[name] != expected[name]]
    if mismatches:
        raise IntegrationGateError(f"output byte/hash validation failed: {mismatches}")
    manifest = json.loads(actual[MANIFEST_OUTPUT].decode("utf-8"))
    required_true = (
        "all_checks_passed",
        "integration_readiness",
        "reconciled_admit_004_interface_implementation_ready",
        "ready_for_admit_004_rule_logic_interface_implementation",
        "feature_semantics_audit_required_before_training",
    )
    required_false = (
        "admit_004_evaluator_implemented",
        "unified_rule_engine_integrated",
        "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now",
        "ready_for_training",
        "ready_to_train_now",
    )
    _require(all(manifest.get(key) is True for key in required_true), "manifest readiness underclaim")
    _require(all(manifest.get(key) is False for key in required_false), "manifest readiness overclaim")
    _require(MANIFEST_OUTPUT not in manifest["output_sha256"], "manifest records its own SHA")
    return {name: _sha256(actual[name]) for name in OUTPUT_FILENAMES}


def main() -> int:
    hashes = materialize()
    for name in OUTPUT_FILENAMES:
        print(f"{name} {hashes[name]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
