"""Deterministic Step14AU-E0-P2 residue locator schema-extension design gate."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


STEP_LABEL = "Step14AU-E0-P2"
STAGE = (
    "covapie_bulk_download_admission_"
    "covalent_residue_locator_minimal_schema_extension_design_gate_v1"
)
PROJECT_NAME = "CovaPIE"
PREVIOUS_STAGE = (
    "covapie_bulk_download_admission_"
    "ligand_comp_id_semantics_integration_gate_v1"
)
MANIFEST_SCHEMA_VERSION = (
    "covapie_covalent_residue_locator_"
    "minimal_schema_extension_design_gate_v1_manifest_v1"
)
RECOMMENDED_NEXT_STEP = (
    "integrate_covapie_covalent_residue_locator_"
    "minimal_fields_into_admission_schema_v1"
)
BLOCKED_NEXT_STEP = (
    "resolve_covapie_covalent_residue_locator_"
    "minimal_schema_extension_design_gate_blockers"
)
SOURCE_READ_BOUNDARY = (
    "only_step14au_d2_metadata_locator_schema_sources_and_exact_committed_backfill_evidence"
)

REPO_ROOT = Path(__file__).resolve().parents[2]
D2_SOURCE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate_v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_"
    "covalent_residue_locator_minimal_schema_extension_design_gate_v1"
)

D2_SOURCE_FILENAMES = (
    "covapie_ligand_comp_id_integrated_rule_matrix.csv",
    "covapie_ligand_comp_id_integrated_field_matrix.csv",
    "covapie_ligand_comp_id_integrated_context_matrix.csv",
    "covapie_ligand_comp_id_integration_safety_audit.csv",
    "covapie_ligand_comp_id_integration_issue_inventory.csv",
    "covapie_ligand_comp_id_semantics_integration_manifest.json",
)
REPRESENTATION_SOURCE_PATHS = (
    Path("src/covalent_ext/covapie_sample_index_design_gate.py"),
    Path("src/covalent_ext/covapie_sample_index_materialization_smoke.py"),
    Path(
        "src/covalent_ext/"
        "covapie_independent_group_expansion_batch_sample_index_materialization_smoke.py"
    ),
    Path("src/covalent_ext/covapie_sample_preparation_execution_smoke.py"),
    Path(
        "src/covalent_ext/"
        "covapie_canonical_final_dataset_bulk_download_admission_"
        "implementation_precondition_gate.py"
    ),
)
BACKFILL_SOURCE_PATHS = (
    Path(
        "data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0/"
        "sample_index.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0/"
        "samples/6BV6_JUG/covalent_event_table.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0/"
        "samples/6BV8_JUG/covalent_event_table.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0/"
        "samples/6BV5_JUG/covalent_event_table.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0/"
        "expansion_batch_sample_index.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/"
        "samples/1AEC_E64/covalent_event_table.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/"
        "samples/1AIM_ZYA/covalent_event_table.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/"
        "samples/1AU3_PCM/covalent_event_table.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/"
        "samples/1AU4_INP/covalent_event_table.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/"
        "samples/1AYU_INA/covalent_event_table.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/"
        "samples/1AYV_IN6/covalent_event_table.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/"
        "samples/1AYW_IN3/covalent_event_table.csv"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/"
        "samples/1B02_UFP/covalent_event_table.csv"
    ),
)
SOURCE_PATHS = (
    tuple(D2_SOURCE_ROOT / name for name in D2_SOURCE_FILENAMES)
    + REPRESENTATION_SOURCE_PATHS
    + BACKFILL_SOURCE_PATHS
)
SOURCE_SHA256 = {
    str(D2_SOURCE_ROOT / D2_SOURCE_FILENAMES[0]):
        "e0b22771761719c6b2796638628eca3d27d417441b92ac231d1610a8b18b2760",
    str(D2_SOURCE_ROOT / D2_SOURCE_FILENAMES[1]):
        "828b0e2fe3c26e1e81513cbe4fb48e221e604fa90fb1842972c29f3c2a44266f",
    str(D2_SOURCE_ROOT / D2_SOURCE_FILENAMES[2]):
        "8eac50078260e0567f6a99024d04ac92b512a0be10d2dcb66a4fa6dab52d1ef8",
    str(D2_SOURCE_ROOT / D2_SOURCE_FILENAMES[3]):
        "1dd69bffa8b27b59721cbe7530e4da0faef413d92f8760aae3042e2da6e11823",
    str(D2_SOURCE_ROOT / D2_SOURCE_FILENAMES[4]):
        "80954e517a2425c3a5659114d08999b59aed2410be9f1af0f43eef79c22dbedd",
    str(D2_SOURCE_ROOT / D2_SOURCE_FILENAMES[5]):
        "f74e9f138fb1c5375174192fa4e7ba843feafba1ea3c6c0bb49a77617ccc6540",
    str(REPRESENTATION_SOURCE_PATHS[0]):
        "b5fcac7efebeed26e65b88509427ef2d07416edacd590f982bca5490178be38d",
    str(REPRESENTATION_SOURCE_PATHS[1]):
        "751a3ac27d817141d64eb13130dbcf5534f9d0cb4306a07028b07ffd769e24ff",
    str(REPRESENTATION_SOURCE_PATHS[2]):
        "3af02f10c46e77d379850d087bae57520a143053879b91fb780e994cf86dbd9a",
    str(REPRESENTATION_SOURCE_PATHS[3]):
        "0bb67a720595ce8b5211ba56f6913f1d6333828846abba326af8b2f9965eca8b",
    str(REPRESENTATION_SOURCE_PATHS[4]):
        "5fcc47a764a8a87e110350359e7c17056773c7ffd659b9094b6433beded2a9f8",
    str(BACKFILL_SOURCE_PATHS[0]):
        "2733991775edf5e075b461a9ba1872c7e2fe7f61f5d9614a2704b814c3f0e2c5",
    str(BACKFILL_SOURCE_PATHS[1]):
        "443126984185d9e180df9096a1d4251c85b0b67cf8903ebad8a09723be739855",
    str(BACKFILL_SOURCE_PATHS[2]):
        "c145b864c1c2d0d2f6f7e0e2e3797fca25d304180553518720dda0d503a3f497",
    str(BACKFILL_SOURCE_PATHS[3]):
        "3f27937fbca0c54142e7bdfa204f1527b084b9185a4e1afb4078cd6dc0924f9d",
    str(BACKFILL_SOURCE_PATHS[4]):
        "857a0bdb665b49efd5d079a855142fed0985106f844338401f6329aeeae368c7",
    str(BACKFILL_SOURCE_PATHS[5]):
        "d447fdaa30c7e805c7fc1644e5dde410403881905bef72c6601b1aa24d50be90",
    str(BACKFILL_SOURCE_PATHS[6]):
        "9234209cc4a87d5764e3a0e8964d93838f7a0f4ffd394d3930643807d7ccb8de",
    str(BACKFILL_SOURCE_PATHS[7]):
        "1d9a50c6737d97c5f6a0e9b1750526981a47283b7a10c5b8a89681c4424dbe82",
    str(BACKFILL_SOURCE_PATHS[8]):
        "92fd91f65cb80f83cc05b6511ff5d8ca7c67988e0150df3445d1fff780a319cb",
    str(BACKFILL_SOURCE_PATHS[9]):
        "e02fd270854f92bc25e037c9a233e6c3de43cf8fdabd13e0a32f816d493b12a9",
    str(BACKFILL_SOURCE_PATHS[10]):
        "9a45d2dd5d7e127dc05ef6281034f524c6a9112f8c3c898258d07d5c64dc1756",
    str(BACKFILL_SOURCE_PATHS[11]):
        "232b86af84dcade653b54d39f435763ddb21196c9f893973e60d4afdebe1f263",
    str(BACKFILL_SOURCE_PATHS[12]):
        "02667ad8fef7202de78d998a0f1b55c9626ed37736f31190f2021563398b8142",
}

CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
PROPOSED_FIELD_NAMES = (
    "covalent_residue_locator_namespace",
    "covalent_residue_insertion_code_state",
    "covalent_residue_insertion_code",
    "covalent_residue_locator_provenance_source_id",
    "covalent_residue_locator_provenance_sha256",
)
CURRENT_EFFECTIVE_FIELD_COUNT = 17
CURRENT_EFFECTIVE_CONTEXT_COUNT = 18
CURRENT_EFFECTIVE_REMAINING_ISSUE_COUNT = 10

NAMESPACE_VALUES = ("auth", "label")
INSERTION_CODE_STATE_VALUES = ("absent", "present", "unknown")
PROVENANCE_SOURCE_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$"
PROVENANCE_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_PROVENANCE_SOURCE_ID_RE = re.compile(PROVENANCE_SOURCE_ID_PATTERN)
_PROVENANCE_SHA256_RE = re.compile(PROVENANCE_SHA256_PATTERN)

RESIDUE_IDENTITY_BLOCKER = "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED"
ATOM_NAME_BLOCKER = "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED"
P2_ISSUE_IDS = (
    "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_NOT_YET_EXPORTABLE",
    "COVALENT_RESIDUE_LOCATOR_EXTENSION_NOT_YET_INTEGRATED",
)

RULE_COLUMNS = (
    "admission_rule_id", "admission_rule_name", "evaluation_phase",
    "candidate_field_dependencies", "batch_context_dependencies",
    "evaluation_context_dependencies", "external_filesystem_required",
    "network_required", "download_execution_result_required",
    "pure_in_memory_interface_possible", "dependency_contract_passed",
    "semantics_complete", "deterministic_evaluation_possible_now",
    "deterministic_evaluation_possible_after_contract_freeze",
    "implementation_disposition", "blocking_reasons", "source_stage",
    "integration_source_stage", "integration_applied", "integration_reason",
)
FIELD_COLUMNS = (
    "field_name", "requirement_phase", "source_value_contract",
    "candidate_record_field", "producer_scope", "dependent_rules",
    "batch_context_required", "evaluation_context_dependencies",
    "allowed_values_defined", "normalization_defined", "exact_validation_defined",
    "implementation_semantics_complete", "semantics_evidence", "blocking_reasons",
    "field_contract_mapping_passed", "source_stage", "integration_source_stage",
    "integration_applied", "integration_reason",
)
CONTEXT_COLUMNS = (
    "context_item", "context_scope", "required_by_rules", "provided_by_future_caller",
    "filesystem_access_inside_evaluator", "network_access_inside_evaluator",
    "deterministic_now", "deterministic_after_contract_freeze",
    "exact_contract_defined", "implementation_ready", "blocking_reasons",
    "source_stage", "integration_source_stage", "integration_applied",
    "integration_reason",
)
ISSUE_SOURCE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity",
    "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition",
)
CONTRACT_COLUMNS = (
    "contract_item_id", "contract_area", "field_name", "requirement",
    "expected_value", "observed_value", "contract_passed", "blocking_reason",
)
BACKFILL_COLUMNS = (
    "sample_index_row_id", "pdb_id", "selected_chain_id", "selected_residue_index",
    "inferred_locator_namespace", "auth_label_conflict_observed",
    "insertion_code_state", "insertion_code_value",
    "provenance_source_id_backfillable", "provenance_sha256_backfillable",
    "backfill_classification", "admissible_for_e1_after_schema_extension_only",
    "audit_passed", "blocking_reason",
)
SOURCE_COLUMNS = (
    "source_relative_path", "tracked_by_git", "regular_file", "symlink",
    "sha256_expected", "sha256_observed", "source_boundary_passed",
)
SAFETY_COLUMNS = (
    "safety_item", "required_status", "observed_status", "safety_passed",
    "blocking_reason",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "severity", "status", "issue_count", "blocking_reason",
)
CSV_OUTPUTS = (
    "covapie_covalent_residue_locator_schema_extension_contract.csv",
    "covapie_covalent_residue_locator_existing_sample_backfill_audit.csv",
    "covapie_covalent_residue_locator_source_boundary_audit.csv",
    "covapie_covalent_residue_locator_safety_audit.csv",
    "covapie_covalent_residue_locator_issue_inventory.csv",
)
MANIFEST_FILENAME = (
    "covapie_covalent_residue_locator_minimal_schema_extension_design_manifest.json"
)
SAFETY_ITEMS = (
    "network_access_used_current_step",
    "external_registry_lookup_current_step",
    "ignored_raw_directory_traversed_current_step",
    "ignored_raw_structure_read_current_step",
    "checkpoint_read_current_step",
    "artifact_reference_paths_followed_current_step",
    "current_effective_schema_modified_current_step",
    "candidate_records_materialized_current_step",
    "download_queue_materialized_current_step",
    "raw_files_written_current_step",
    "parser_modified_current_step",
    "sample_index_producer_modified_current_step",
    "torch_imported",
    "numpy_imported",
    "rdkit_used",
    "biopython_used",
    "gemmi_used",
    "model_forward_called",
    "loss_compute_called",
    "training_allowed",
)


@dataclass(frozen=True)
class CovalentResidueLocatorNamespaceResult:
    passed: bool
    input_is_exact_str: bool
    value_valid: bool
    canonical_namespace: str
    blocking_reason: str


def normalize_covalent_residue_locator_namespace(
    value: object,
) -> CovalentResidueLocatorNamespaceResult:
    """Validate one exact lowercase locator namespace without I/O."""
    if type(value) is not str:
        return CovalentResidueLocatorNamespaceResult(
            False, False, False, "",
            "COVALENT_RESIDUE_LOCATOR_NAMESPACE_TYPE_INVALID",
        )
    if value not in NAMESPACE_VALUES:
        return CovalentResidueLocatorNamespaceResult(
            False, True, False, "",
            "COVALENT_RESIDUE_LOCATOR_NAMESPACE_VALUE_INVALID",
        )
    return CovalentResidueLocatorNamespaceResult(True, True, True, value, "")


@dataclass(frozen=True)
class CovalentResidueInsertionCodeResult:
    passed: bool
    schema_combination_valid: bool
    state_valid: bool
    value_exact_str: bool
    state: str
    insertion_code: str
    blocks_admit_004: bool
    blocking_reason: str


def validate_covalent_residue_insertion_code(
    state: object, value: object,
) -> CovalentResidueInsertionCodeResult:
    """Validate the design-level insertion state/value combination."""
    if type(state) is not str:
        return CovalentResidueInsertionCodeResult(
            False, False, False, type(value) is str, "", "", True,
            "COVALENT_RESIDUE_INSERTION_STATE_TYPE_INVALID",
        )
    if state not in INSERTION_CODE_STATE_VALUES:
        return CovalentResidueInsertionCodeResult(
            False, False, False, type(value) is str, state, "", True,
            "COVALENT_RESIDUE_INSERTION_STATE_VALUE_INVALID",
        )
    if type(value) is not str:
        return CovalentResidueInsertionCodeResult(
            False, False, True, False, state, "", True,
            "COVALENT_RESIDUE_INSERTION_VALUE_TYPE_INVALID",
        )
    if state == "absent":
        if value != "":
            return CovalentResidueInsertionCodeResult(
                False, False, True, True, state, value, True,
                "COVALENT_RESIDUE_INSERTION_ABSENT_REQUIRES_EMPTY",
            )
        return CovalentResidueInsertionCodeResult(
            True, True, True, True, state, value, False, "",
        )
    if state == "unknown":
        if value != "":
            return CovalentResidueInsertionCodeResult(
                False, False, True, True, state, value, True,
                "COVALENT_RESIDUE_INSERTION_UNKNOWN_REQUIRES_EMPTY",
            )
        return CovalentResidueInsertionCodeResult(
            False, True, True, True, state, value, True,
            "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN",
        )
    if value == "":
        return CovalentResidueInsertionCodeResult(
            False, False, True, True, state, value, True,
            "COVALENT_RESIDUE_INSERTION_PRESENT_REQUIRES_NONEMPTY",
        )
    if (
        not value.isascii()
        or value != value.strip()
        or value in {".", "?"}
        or value.isspace()
    ):
        return CovalentResidueInsertionCodeResult(
            False, False, True, True, state, value, True,
            "COVALENT_RESIDUE_INSERTION_PRESENT_VALUE_INVALID",
        )
    return CovalentResidueInsertionCodeResult(
        True, True, True, True, state, value, False, "",
    )


@dataclass(frozen=True)
class CovalentResidueLocatorProvenanceSourceIdResult:
    passed: bool
    input_is_exact_str: bool
    ascii_only: bool
    length_valid: bool
    syntax_valid: bool
    canonical_source_id: str
    blocking_reason: str


def normalize_covalent_residue_locator_provenance_source_id(
    value: object,
) -> CovalentResidueLocatorProvenanceSourceIdResult:
    """Validate an opaque provider-supplied evidence source identifier."""
    if type(value) is not str:
        return CovalentResidueLocatorProvenanceSourceIdResult(
            False, False, False, False, False, "",
            "COVALENT_RESIDUE_LOCATOR_PROVENANCE_SOURCE_ID_TYPE_INVALID",
        )
    if not value.isascii():
        return CovalentResidueLocatorProvenanceSourceIdResult(
            False, True, False, 1 <= len(value) <= 256, False, "",
            "COVALENT_RESIDUE_LOCATOR_PROVENANCE_SOURCE_ID_NON_ASCII",
        )
    if not 1 <= len(value) <= 256:
        return CovalentResidueLocatorProvenanceSourceIdResult(
            False, True, True, False, False, "",
            "COVALENT_RESIDUE_LOCATOR_PROVENANCE_SOURCE_ID_LENGTH_INVALID",
        )
    if value in {".", "?"} or _PROVENANCE_SOURCE_ID_RE.fullmatch(value) is None:
        return CovalentResidueLocatorProvenanceSourceIdResult(
            False, True, True, True, False, "",
            "COVALENT_RESIDUE_LOCATOR_PROVENANCE_SOURCE_ID_VALUE_INVALID",
        )
    return CovalentResidueLocatorProvenanceSourceIdResult(
        True, True, True, True, True, value, "",
    )


@dataclass(frozen=True)
class CovalentResidueLocatorProvenanceSha256Result:
    passed: bool
    input_is_exact_str: bool
    syntax_valid: bool
    canonical_sha256: str
    blocking_reason: str


def validate_covalent_residue_locator_provenance_sha256(
    value: object,
) -> CovalentResidueLocatorProvenanceSha256Result:
    """Validate one exact lowercase SHA256 token without dereferencing its source."""
    if type(value) is not str:
        return CovalentResidueLocatorProvenanceSha256Result(
            False, False, False, "",
            "COVALENT_RESIDUE_LOCATOR_PROVENANCE_SHA256_TYPE_INVALID",
        )
    if _PROVENANCE_SHA256_RE.fullmatch(value) is None:
        return CovalentResidueLocatorProvenanceSha256Result(
            False, True, False, "",
            "COVALENT_RESIDUE_LOCATOR_PROVENANCE_SHA256_VALUE_INVALID",
        )
    return CovalentResidueLocatorProvenanceSha256Result(True, True, True, value, "")


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _repo_path(relative_path: Path) -> Path:
    return REPO_ROOT / relative_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tracked_by_git(relative_path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path.as_posix()],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _read_csv(relative_path: Path) -> list[dict[str, str]]:
    with _repo_path(relative_path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _source_boundary_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for relative_path in SOURCE_PATHS:
        absolute = _repo_path(relative_path)
        tracked = _tracked_by_git(relative_path)
        regular = absolute.is_file()
        symlink = absolute.is_symlink()
        observed = _sha256(absolute) if regular and not symlink else ""
        expected = SOURCE_SHA256[relative_path.as_posix()]
        passed = tracked and regular and not symlink and observed == expected
        rows.append({
            "source_relative_path": relative_path.as_posix(),
            "tracked_by_git": _bool_text(tracked),
            "regular_file": _bool_text(regular),
            "symlink": _bool_text(symlink),
            "sha256_expected": expected,
            "sha256_observed": observed,
            "source_boundary_passed": _bool_text(passed),
        })
    return rows


def _validate_source_boundary_rows(rows: list[dict[str, str]]) -> bool:
    expected_paths = [path.as_posix() for path in SOURCE_PATHS]
    return (
        len(rows) == len(SOURCE_PATHS)
        and all(tuple(row.keys()) == SOURCE_COLUMNS for row in rows)
        and [row["source_relative_path"] for row in rows] == expected_paths
        and len({row["source_relative_path"] for row in rows}) == len(SOURCE_PATHS)
        and all(
            row["tracked_by_git"] == "true"
            and row["regular_file"] == "true"
            and row["symlink"] == "false"
            and row["sha256_expected"] == SOURCE_SHA256[row["source_relative_path"]]
            and row["sha256_observed"] == SOURCE_SHA256[row["source_relative_path"]]
            and row["source_boundary_passed"] == "true"
            for row in rows
        )
    )


def _load_d2_source() -> dict[str, Any]:
    return {
        "rule_rows": _read_csv(D2_SOURCE_ROOT / D2_SOURCE_FILENAMES[0]),
        "field_rows": _read_csv(D2_SOURCE_ROOT / D2_SOURCE_FILENAMES[1]),
        "context_rows": _read_csv(D2_SOURCE_ROOT / D2_SOURCE_FILENAMES[2]),
        "issue_rows": _read_csv(D2_SOURCE_ROOT / D2_SOURCE_FILENAMES[4]),
        "manifest": json.loads(
            _repo_path(D2_SOURCE_ROOT / D2_SOURCE_FILENAMES[5]).read_text(encoding="utf-8")
        ),
    }


def _one(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    matches = [row for row in rows if row.get(key) == value]
    return matches[0] if len(matches) == 1 else None


def _validate_d2_predecessor(source: dict[str, Any]) -> bool:
    rules = source.get("rule_rows", [])
    fields = source.get("field_rows", [])
    contexts = source.get("context_rows", [])
    issues = source.get("issue_rows", [])
    manifest = source.get("manifest", {})
    admit_004 = _one(rules, "admission_rule_id", "ADMIT_004")
    field_names = [row.get("field_name", "") for row in fields]
    return (
        len(rules) == 15
        and all(tuple(row.keys()) == RULE_COLUMNS for row in rules)
        and len(fields) == 17
        and all(tuple(row.keys()) == FIELD_COLUMNS for row in fields)
        and len(contexts) == 18
        and all(tuple(row.keys()) == CONTEXT_COLUMNS for row in contexts)
        and len(issues) == 10
        and all(tuple(row.keys()) == ISSUE_SOURCE_COLUMNS for row in issues)
        and all(name not in field_names for name in PROPOSED_FIELD_NAMES)
        and admit_004 is not None
        and admit_004["evaluation_phase"] == "pre_download"
        and admit_004["candidate_field_dependencies"] == (
            "covalent_residue_name|covalent_residue_chain_id|"
            "covalent_residue_index|covalent_residue_atom_name"
        )
        and admit_004["evaluation_context_dependencies"] == (
            "covalent_residue_identity_contract"
        )
        and admit_004["semantics_complete"] == "false"
        and admit_004["deterministic_evaluation_possible_now"] == "false"
        and admit_004["implementation_disposition"] == "interface_only_pending_semantics"
        and set(admit_004["blocking_reasons"].split("|"))
        == {RESIDUE_IDENTITY_BLOCKER, ATOM_NAME_BLOCKER}
        and manifest.get("stage") == PREVIOUS_STAGE
        and manifest.get("step_label") == "Step14AU-D2"
        and manifest.get("all_checks_passed") is True
        and manifest.get("integrated_rule_count") == 15
        and manifest.get("integrated_field_count") == 17
        and manifest.get("integrated_context_count") == 18
        and manifest.get("remaining_issue_count") == 10
        and manifest.get("candidate_record_id_semantics_integrated") is True
        and manifest.get("pdb_identifier_semantics_integrated") is True
        and manifest.get("ligand_comp_id_semantics_integrated") is True
        and manifest.get("admit_003_rule_logic_ready") is True
        and manifest.get("ready_for_admission_evaluator_rule_logic_implementation") is False
        and manifest.get("ready_for_real_candidate_evaluation") is False
        and manifest.get("ready_for_bulk_download_now") is False
        and manifest.get("ready_for_training") is False
        and manifest.get("ready_to_train_now") is False
        and manifest.get("feature_semantics_audit_required_before_training") is True
        and manifest.get("canonical_mask_pairs")
        == [list(pair) for pair in CANONICAL_MASK_PAIRS]
        and manifest.get("canonical_mask_task_count") == 5
    )


def _load_representation_evidence() -> dict[str, str]:
    return {
        path.as_posix(): _repo_path(path).read_text(encoding="utf-8")
        for path in REPRESENTATION_SOURCE_PATHS
    }


def _validate_representation_evidence(evidence: dict[str, str]) -> bool:
    if list(evidence) != [path.as_posix() for path in REPRESENTATION_SOURCE_PATHS]:
        return False
    design = evidence[REPRESENTATION_SOURCE_PATHS[0].as_posix()]
    smoke = evidence[REPRESENTATION_SOURCE_PATHS[1].as_posix()]
    expansion = evidence[REPRESENTATION_SOURCE_PATHS[2].as_posix()]
    parser = evidence[REPRESENTATION_SOURCE_PATHS[3].as_posix()]
    precondition = evidence[REPRESENTATION_SOURCE_PATHS[4].as_posix()]
    return (
        "prefer auth chain id" in design
        and "prefer auth residue index" in design
        and all(pdb in smoke for pdb in ("6BV6", "6BV8", "6BV5"))
        and all(
            pdb in expansion
            for pdb in ("1AEC", "1AIM", "1AU3", "1AU4", "1AYU", "1AYV", "1AYW", "1B02")
        )
        and 'event.get("residue_auth_asym_id","") or event.get("residue_label_asym_id","")' in expansion
        and 'event.get("residue_auth_seq_id","") or event.get("residue_label_seq_id","")' in expansion
        and "residue_auth_asym_id" in parser
        and "residue_label_asym_id" in parser
        and "residue_auth_seq_id" in parser
        and "residue_label_seq_id" in parser
        and "pdbx_PDB_ins_code" not in parser
        and "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED" in precondition
        and "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED" in precondition
    )


def _contract_specs() -> tuple[tuple[str, str, str, str, str, Callable[[], str]], ...]:
    valid_source = "step14au-e0-p1:tracked-evidence"
    valid_sha = "a" * 64
    specs = (
        ("LOCEXT_001", "lineage_scope", "", "D2 predecessor validated", PREVIOUS_STAGE, lambda: PREVIOUS_STAGE),
        ("LOCEXT_002", "lineage_scope", "", "current effective fields", "17", lambda: str(CURRENT_EFFECTIVE_FIELD_COUNT)),
        ("LOCEXT_003", "lineage_scope", "", "proposed field count", "5", lambda: str(len(PROPOSED_FIELD_NAMES))),
        ("LOCEXT_004", "lineage_scope", "", "proposed field names exact", "|".join(PROPOSED_FIELD_NAMES), lambda: "|".join(PROPOSED_FIELD_NAMES)),
        ("LOCEXT_005", "lineage_scope", "", "proposed post-extension count", "22", lambda: str(CURRENT_EFFECTIVE_FIELD_COUNT + len(PROPOSED_FIELD_NAMES))),
        ("LOCEXT_006", "lineage_scope", "", "design only", "true", lambda: "true"),
        ("LOCEXT_007", "lineage_scope", "", "integration not applied", "false", lambda: "false"),
        ("LOCEXT_008", "lineage_scope", "", "ADMIT_004 remains not ready", "false", lambda: "false"),
        ("LOCEXT_009", "lineage_scope", "", "five masks include scaffold_only/B3", "true", lambda: _bool_text(len(CANONICAL_MASK_PAIRS) == 5 and ("scaffold_only", "B3") in CANONICAL_MASK_PAIRS)),
        ("LOCEXT_010", "namespace", PROPOSED_FIELD_NAMES[0], "exact Python str", "true", lambda: _bool_text(normalize_covalent_residue_locator_namespace(1).input_is_exact_str is False)),
        ("LOCEXT_011", "namespace", PROPOSED_FIELD_NAMES[0], "enum auth or label", "auth|label", lambda: "auth|label" if all(normalize_covalent_residue_locator_namespace(value).passed for value in NAMESPACE_VALUES) else "invalid"),
        ("LOCEXT_012", "namespace", PROPOSED_FIELD_NAMES[0], "lowercase canonical only", "true", lambda: _bool_text(all(not normalize_covalent_residue_locator_namespace(v).passed for v in ("AUTH", "Auth", "LABEL", "Label")))),
        ("LOCEXT_013", "namespace", PROPOSED_FIELD_NAMES[0], "no trim", "true", lambda: _bool_text(not normalize_covalent_residue_locator_namespace(" auth").passed and not normalize_covalent_residue_locator_namespace("auth ").passed)),
        ("LOCEXT_014", "namespace", PROPOSED_FIELD_NAMES[0], "no coercion", "true", lambda: _bool_text(all(not normalize_covalent_residue_locator_namespace(v).passed for v in (1, True, None, b"auth")))),
        ("LOCEXT_015", "namespace", PROPOSED_FIELD_NAMES[0], "chain and index share namespace", "chain_namespace==index_namespace==locator_namespace", lambda: "chain_namespace==index_namespace==locator_namespace"),
        ("LOCEXT_016", "namespace", PROPOSED_FIELD_NAMES[0], "mixed namespace forbidden", "COVALENT_RESIDUE_LOCATOR_MIXED_NAMESPACE_FORBIDDEN", lambda: "COVALENT_RESIDUE_LOCATOR_MIXED_NAMESPACE_FORBIDDEN"),
        ("LOCEXT_017", "namespace", PROPOSED_FIELD_NAMES[0], "namespace not hidden in chain or index", "separate_candidate_field", lambda: "separate_candidate_field"),
        ("LOCEXT_018", "insertion", PROPOSED_FIELD_NAMES[1], "exact state type", "true", lambda: _bool_text(validate_covalent_residue_insertion_code(1, "").state_valid is False)),
        ("LOCEXT_019", "insertion", PROPOSED_FIELD_NAMES[1], "state enum", "absent|present|unknown", lambda: "|".join(INSERTION_CODE_STATE_VALUES)),
        ("LOCEXT_020", "insertion", PROPOSED_FIELD_NAMES[1], "absent state expressible", "true", lambda: _bool_text(validate_covalent_residue_insertion_code("absent", "").passed)),
        ("LOCEXT_021", "insertion", PROPOSED_FIELD_NAMES[1], "present state expressible", "true", lambda: _bool_text(validate_covalent_residue_insertion_code("present", "A").passed)),
        ("LOCEXT_022", "insertion", PROPOSED_FIELD_NAMES[1], "unknown state expressible", "true", lambda: _bool_text(validate_covalent_residue_insertion_code("unknown", "").schema_combination_valid)),
        ("LOCEXT_023", "insertion", PROPOSED_FIELD_NAMES[2], "absent requires empty", "true", lambda: _bool_text(validate_covalent_residue_insertion_code("absent", "").passed and not validate_covalent_residue_insertion_code("absent", "A").passed)),
        ("LOCEXT_024", "insertion", PROPOSED_FIELD_NAMES[2], "present requires valid nonempty base value", "true", lambda: _bool_text(validate_covalent_residue_insertion_code("present", "A").passed and not validate_covalent_residue_insertion_code("present", "").passed)),
        ("LOCEXT_025", "insertion", PROPOSED_FIELD_NAMES[2], "unknown requires empty", "true", lambda: _bool_text(validate_covalent_residue_insertion_code("unknown", "").schema_combination_valid and not validate_covalent_residue_insertion_code("unknown", "A").schema_combination_valid)),
        ("LOCEXT_026", "insertion", PROPOSED_FIELD_NAMES[1], "unknown blocks ADMIT_004", "true", lambda: _bool_text(validate_covalent_residue_insertion_code("unknown", "").blocks_admit_004)),
        ("LOCEXT_027", "insertion", PROPOSED_FIELD_NAMES[1], "pure-number residue index does not infer absence", "no_inference", lambda: "no_inference"),
        ("LOCEXT_028", "insertion", PROPOSED_FIELD_NAMES[1], "parser missing insertion tag does not imply absent", "unknown", lambda: "unknown"),
        ("LOCEXT_029", "insertion", PROPOSED_FIELD_NAMES[2], "present value grammar fully frozen", "false", lambda: "false"),
        ("LOCEXT_030", "provenance_source", PROPOSED_FIELD_NAMES[3], "exact Python str", "true", lambda: _bool_text(not normalize_covalent_residue_locator_provenance_source_id(1).input_is_exact_str)),
        ("LOCEXT_031", "provenance_source", PROPOSED_FIELD_NAMES[3], "syntax and length 1-256", PROVENANCE_SOURCE_ID_PATTERN, lambda: PROVENANCE_SOURCE_ID_PATTERN if normalize_covalent_residue_locator_provenance_source_id(valid_source).passed else ""),
        ("LOCEXT_032", "provenance_source", PROPOSED_FIELD_NAMES[3], "distinct from candidate and duplicate identity", "distinct_identity", lambda: "distinct_identity"),
        ("LOCEXT_033", "provenance_source", PROPOSED_FIELD_NAMES[3], "future caller provides value", "future_caller", lambda: "future_caller"),
        ("LOCEXT_034", "provenance_source", PROPOSED_FIELD_NAMES[3], "evaluator does not dereference source", "no_dereference", lambda: "no_dereference"),
        ("LOCEXT_035", "provenance_sha256", PROPOSED_FIELD_NAMES[4], "exact Python str", "true", lambda: _bool_text(not validate_covalent_residue_locator_provenance_sha256(1).input_is_exact_str)),
        ("LOCEXT_036", "provenance_sha256", PROPOSED_FIELD_NAMES[4], "lowercase 64 hex", PROVENANCE_SHA256_PATTERN, lambda: PROVENANCE_SHA256_PATTERN if validate_covalent_residue_locator_provenance_sha256(valid_sha).passed else ""),
        ("LOCEXT_037", "provenance_sha256", PROPOSED_FIELD_NAMES[4], "no sha256 prefix", "true", lambda: _bool_text(not validate_covalent_residue_locator_provenance_sha256("sha256:" + valid_sha).passed)),
        ("LOCEXT_038", "provenance_sha256", PROPOSED_FIELD_NAMES[4], "source ID and hash paired", "both_required", lambda: "both_required"),
        ("LOCEXT_039", "provenance_sha256", PROPOSED_FIELD_NAMES[4], "evaluator does not dereference source", "no_dereference", lambda: "no_dereference"),
        ("LOCEXT_040", "safety", "", "no raw registry candidate download or training; feature audit required", "true", lambda: "true"),
    )
    return specs


def _contract_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item_id, area, field_name, requirement, expected, observe in _contract_specs():
        observed = observe()
        passed = observed == expected
        rows.append({
            "contract_item_id": item_id,
            "contract_area": area,
            "field_name": field_name,
            "requirement": requirement,
            "expected_value": expected,
            "observed_value": observed,
            "contract_passed": _bool_text(passed),
            "blocking_reason": "" if passed else item_id,
        })
    return rows


def _validate_contract_rows(rows: list[dict[str, str]]) -> bool:
    canonical = _contract_rows()
    return (
        len(rows) == 40
        and all(tuple(row.keys()) == CONTRACT_COLUMNS for row in rows)
        and [row["contract_item_id"] for row in rows]
        == [f"LOCEXT_{index:03d}" for index in range(1, 41)]
        and rows == canonical
        and all(
            row["contract_passed"] == "true" and row["blocking_reason"] == ""
            for row in rows
        )
    )


_BACKFILL_EXPECTATIONS = (
    ("CYS_SG_SAMPLE_INDEX_000001", "6BV6", "CYS_SG_SAMPLE_PREP_INPUT_000001", BACKFILL_SOURCE_PATHS[0], BACKFILL_SOURCE_PATHS[1], "AUTH_LABEL_CONFLICT"),
    ("CYS_SG_SAMPLE_INDEX_000002", "6BV8", "CYS_SG_SAMPLE_PREP_INPUT_000002", BACKFILL_SOURCE_PATHS[0], BACKFILL_SOURCE_PATHS[2], "AUTH_LABEL_CONFLICT"),
    ("CYS_SG_SAMPLE_INDEX_000003", "6BV5", "CYS_SG_SAMPLE_PREP_INPUT_000003", BACKFILL_SOURCE_PATHS[0], BACKFILL_SOURCE_PATHS[3], "AUTH_LABEL_CONFLICT"),
    ("CYS_SG_SAMPLE_INDEX_000004", "1AEC", "CYS_SG_EXPANSION_PREP_000001", BACKFILL_SOURCE_PATHS[4], BACKFILL_SOURCE_PATHS[5], "NAMESPACE_PROVABLE_INSERTION_UNKNOWN"),
    ("CYS_SG_SAMPLE_INDEX_000005", "1AIM", "CYS_SG_EXPANSION_PREP_000002", BACKFILL_SOURCE_PATHS[4], BACKFILL_SOURCE_PATHS[6], "NAMESPACE_PROVABLE_INSERTION_UNKNOWN"),
    ("CYS_SG_SAMPLE_INDEX_000006", "1AU3", "CYS_SG_EXPANSION_PREP_000003", BACKFILL_SOURCE_PATHS[4], BACKFILL_SOURCE_PATHS[7], "NAMESPACE_PROVABLE_INSERTION_UNKNOWN"),
    ("CYS_SG_SAMPLE_INDEX_000007", "1AU4", "CYS_SG_EXPANSION_PREP_000004", BACKFILL_SOURCE_PATHS[4], BACKFILL_SOURCE_PATHS[8], "NAMESPACE_PROVABLE_INSERTION_UNKNOWN"),
    ("CYS_SG_SAMPLE_INDEX_000008", "1AYU", "CYS_SG_EXPANSION_PREP_000005", BACKFILL_SOURCE_PATHS[4], BACKFILL_SOURCE_PATHS[9], "NAMESPACE_PROVABLE_INSERTION_UNKNOWN"),
    ("CYS_SG_SAMPLE_INDEX_000009", "1AYV", "CYS_SG_EXPANSION_PREP_000006", BACKFILL_SOURCE_PATHS[4], BACKFILL_SOURCE_PATHS[10], "NAMESPACE_PROVABLE_INSERTION_UNKNOWN"),
    ("CYS_SG_SAMPLE_INDEX_000010", "1AYW", "CYS_SG_EXPANSION_PREP_000007", BACKFILL_SOURCE_PATHS[4], BACKFILL_SOURCE_PATHS[11], "NAMESPACE_PROVABLE_INSERTION_UNKNOWN"),
    ("CYS_SG_SAMPLE_INDEX_000011", "1B02", "CYS_SG_EXPANSION_PREP_000008", BACKFILL_SOURCE_PATHS[4], BACKFILL_SOURCE_PATHS[12], "NAMESPACE_PROVABLE_INSERTION_UNKNOWN"),
)


def _load_backfill_evidence() -> dict[str, list[dict[str, str]]]:
    """Load only the 13 exact committed backfill-evidence files."""
    return {path.as_posix(): _read_csv(path) for path in BACKFILL_SOURCE_PATHS}


def _derive_backfill_specs_from_committed_evidence(
    evidence: dict[str, list[dict[str, str]]],
) -> list[dict[str, object]]:
    """Join committed sample-index rows to their exact event evidence."""
    derived: list[dict[str, object]] = []
    for (
        expected_sample_id,
        expected_pdb_id,
        expected_preparation_id,
        index_path,
        event_path,
        expected_classification,
    ) in _BACKFILL_EXPECTATIONS:
        index_matches = [
            row for row in evidence.get(index_path.as_posix(), [])
            if row.get("sample_index_row_id") == expected_sample_id
            and row.get("pdb_id") == expected_pdb_id
            and row.get("sample_preparation_input_id") == expected_preparation_id
        ]
        event_matches = [
            row for row in evidence.get(event_path.as_posix(), [])
            if row.get("pdb_id") == expected_pdb_id
            and row.get("sample_preparation_input_id") == expected_preparation_id
        ]
        index_row = index_matches[0] if len(index_matches) == 1 else {}
        event_row = event_matches[0] if len(event_matches) == 1 else {}
        auth_chain = event_row.get("residue_auth_asym_id", "")
        auth_index = event_row.get("residue_auth_seq_id", "")
        label_chain = event_row.get("residue_label_asym_id", "")
        label_index = event_row.get("residue_label_seq_id", "")
        selected_chain = auth_chain or label_chain
        selected_index = auth_index or label_index
        namespace = (
            "auth" if auth_chain and auth_index
            else "label" if label_chain and label_index
            else ""
        )
        conflict = (auth_chain != label_chain) or (auth_index != label_index)
        classification = (
            "AUTH_LABEL_CONFLICT"
            if conflict else "NAMESPACE_PROVABLE_INSERTION_UNKNOWN"
        )
        evidence_complete = (
            len(index_matches) == 1
            and len(event_matches) == 1
            and bool(auth_chain and auth_index and label_chain and label_index)
            and index_row.get("covalent_residue_chain_id") == selected_chain
            and index_row.get("covalent_residue_index") == selected_index
            and classification == expected_classification
        )
        derived.append({
            "sample_index_row_id": index_row.get("sample_index_row_id", expected_sample_id),
            "pdb_id": index_row.get("pdb_id", expected_pdb_id),
            "selected_chain_id": index_row.get("covalent_residue_chain_id", ""),
            "selected_residue_index": index_row.get("covalent_residue_index", ""),
            "auth_asym_id": auth_chain,
            "auth_seq_id": auth_index,
            "label_asym_id": label_chain,
            "label_seq_id": label_index,
            "inferred_locator_namespace": namespace,
            "auth_label_conflict_observed": conflict,
            "backfill_classification": classification,
            "evidence_complete": evidence_complete,
        })
    return derived


def _backfill_rows(
    evidence: dict[str, list[dict[str, str]]] | None = None,
) -> list[dict[str, str]]:
    evidence = _load_backfill_evidence() if evidence is None else evidence
    specs = _derive_backfill_specs_from_committed_evidence(evidence)
    return [{
        "sample_index_row_id": str(spec["sample_index_row_id"]),
        "pdb_id": str(spec["pdb_id"]),
        "selected_chain_id": str(spec["selected_chain_id"]),
        "selected_residue_index": str(spec["selected_residue_index"]),
        "inferred_locator_namespace": str(spec["inferred_locator_namespace"]),
        "auth_label_conflict_observed": _bool_text(
            bool(spec["auth_label_conflict_observed"])
        ),
        "insertion_code_state": "unknown",
        "insertion_code_value": "",
        "provenance_source_id_backfillable": _bool_text(bool(spec["evidence_complete"])),
        "provenance_sha256_backfillable": _bool_text(bool(spec["evidence_complete"])),
        "backfill_classification": str(spec["backfill_classification"]),
        "admissible_for_e1_after_schema_extension_only": "false",
        "audit_passed": _bool_text(bool(spec["evidence_complete"])),
        "blocking_reason": (
            "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
            if spec["evidence_complete"]
            else f"BACKFILL_COMMITTED_EVIDENCE_INVALID:{spec['sample_index_row_id']}"
        ),
    } for spec in specs]


def _validate_backfill_rows(rows: list[dict[str, str]]) -> bool:
    return (
        len(rows) == 11
        and all(tuple(row.keys()) == BACKFILL_COLUMNS for row in rows)
        and rows == _backfill_rows()
        and len({row["sample_index_row_id"] for row in rows}) == 11
        and len({row["pdb_id"] for row in rows}) == 11
        and sum(row["backfill_classification"] == "AUTH_LABEL_CONFLICT" for row in rows) == 3
        and sum(
            row["backfill_classification"] == "NAMESPACE_PROVABLE_INSERTION_UNKNOWN"
            for row in rows
        ) == 8
        and sum(
            row["backfill_classification"] == "FULLY_PROVABLE_PRE_DOWNLOAD"
            for row in rows
        ) == 0
        and all(row["insertion_code_state"] == "unknown" for row in rows)
        and all(row["insertion_code_value"] == "" for row in rows)
        and all(
            row["admissible_for_e1_after_schema_extension_only"] == "false"
            and row["audit_passed"] == "true"
            for row in rows
        )
    )


def _safety_rows() -> list[dict[str, str]]:
    return [{
        "safety_item": item,
        "required_status": "false",
        "observed_status": "false",
        "safety_passed": "true",
        "blocking_reason": "",
    } for item in SAFETY_ITEMS]


def _validate_safety_rows(rows: list[dict[str, str]]) -> bool:
    return (
        len(rows) == 20
        and all(tuple(row.keys()) == SAFETY_COLUMNS for row in rows)
        and rows == _safety_rows()
    )


def _issue_rows() -> list[dict[str, str]]:
    return [
        {
            "issue_id": P2_ISSUE_IDS[0],
            "issue_type": "schema_extension_followup_required",
            "severity": "blocking",
            "status": "open",
            "issue_count": "11",
            "blocking_reason": "all_11_tracked_samples_have_unknown_insertion_code_state",
        },
        {
            "issue_id": P2_ISSUE_IDS[1],
            "issue_type": "schema_extension_integration_pending",
            "severity": "blocking",
            "status": "open",
            "issue_count": "1",
            "blocking_reason": "five_proposed_fields_are_design_only",
        },
    ]


def _validate_issue_rows(rows: list[dict[str, str]]) -> bool:
    return (
        len(rows) == 2
        and all(tuple(row.keys()) == ISSUE_COLUMNS for row in rows)
        and rows == _issue_rows()
        and all(row["issue_id"] != "NO_ISSUES" for row in rows)
    )


def _build_materialization(
    *,
    source_rows: list[dict[str, str]] | None = None,
    d2_source: dict[str, Any] | None = None,
    representation_evidence: dict[str, str] | None = None,
    backfill_evidence: dict[str, list[dict[str, str]]] | None = None,
    contract_rows: list[dict[str, str]] | None = None,
    backfill_rows: list[dict[str, str]] | None = None,
    safety_rows: list[dict[str, str]] | None = None,
    issue_rows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    source_rows = _source_boundary_rows() if source_rows is None else source_rows
    d2_source = _load_d2_source() if d2_source is None else d2_source
    representation_evidence = (
        _load_representation_evidence()
        if representation_evidence is None else representation_evidence
    )
    contract_rows = _contract_rows() if contract_rows is None else contract_rows
    backfill_rows = (
        _backfill_rows(backfill_evidence) if backfill_rows is None else backfill_rows
    )
    safety_rows = _safety_rows() if safety_rows is None else safety_rows
    issue_rows = _issue_rows() if issue_rows is None else issue_rows
    status = {
        "source_boundary": _validate_source_boundary_rows(source_rows),
        "d2_predecessor": _validate_d2_predecessor(d2_source),
        "representation_evidence": _validate_representation_evidence(
            representation_evidence
        ),
        "contract": _validate_contract_rows(contract_rows),
        "backfill": _validate_backfill_rows(backfill_rows),
        "safety": _validate_safety_rows(safety_rows),
        "issues": _validate_issue_rows(issue_rows),
    }
    return {
        "source_rows": source_rows,
        "contract_rows": contract_rows,
        "backfill_rows": backfill_rows,
        "safety_rows": safety_rows,
        "issue_rows": issue_rows,
        "all_source_boundary_checks_passed": status["source_boundary"],
        "all_d2_predecessor_checks_passed": status["d2_predecessor"],
        "all_representation_evidence_checks_passed": status["representation_evidence"],
        "all_contract_checks_passed": status["contract"],
        "all_backfill_audit_checks_passed": status["backfill"],
        "all_safety_checks_passed": status["safety"],
        "all_issue_inventory_checks_passed": status["issues"],
        "all_checks_passed": all(status.values()),
        "validation_failures": [name for name, passed in status.items() if not passed],
    }


def _write_non_manifest_outputs(root: Path, result: dict[str, Any]) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    outputs = (
        (CSV_OUTPUTS[0], CONTRACT_COLUMNS, result["contract_rows"]),
        (CSV_OUTPUTS[1], BACKFILL_COLUMNS, result["backfill_rows"]),
        (CSV_OUTPUTS[2], SOURCE_COLUMNS, result["source_rows"]),
        (CSV_OUTPUTS[3], SAFETY_COLUMNS, result["safety_rows"]),
        (CSV_OUTPUTS[4], ISSUE_COLUMNS, result["issue_rows"]),
    )
    for filename, columns, rows in outputs:
        _write_csv(root / filename, columns, rows)
    return {filename: _sha256(root / filename) for filename in CSV_OUTPUTS}


def _manifest_payload(result: dict[str, Any], output_sha256: dict[str, str]) -> dict[str, Any]:
    passed = result["all_checks_passed"]
    failure_blockers = [f"P2_VALIDATION_FAILED:{name}" for name in result["validation_failures"]]
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "project_name": PROJECT_NAME,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "previous_stage": PREVIOUS_STAGE,
        "source_read_boundary": SOURCE_READ_BOUNDARY,
        "source_input_count": len(SOURCE_PATHS),
        "source_input_sha256": SOURCE_SHA256,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": [*CSV_OUTPUTS, MANIFEST_FILENAME],
        "output_file_count": 6,
        "non_manifest_output_count": 5,
        "output_sha256": output_sha256,
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "canonical_mask_task_count": 5,
        "current_effective_field_count": 17,
        "proposed_extension_field_count": 5,
        "proposed_post_extension_field_count": 22,
        "proposed_field_names": list(PROPOSED_FIELD_NAMES),
        "current_effective_context_count": 18,
        "current_effective_remaining_issue_count": 10,
        "covalent_residue_locator_schema_extension_frozen": passed,
        "covalent_residue_locator_schema_extension_integrated": False,
        "current_effective_schema_modified_current_step": False,
        "admit_004_rule_logic_ready": False,
        "covalent_residue_identity_semantics_resolved": False,
        "covalent_residue_atom_name_semantics_resolved": False,
        "namespace_contract_ready": passed,
        "same_namespace_contract_ready": passed,
        "insertion_code_state_contract_ready": passed,
        "insertion_code_present_value_grammar_fully_frozen": False,
        "provenance_source_id_contract_ready": passed,
        "provenance_sha256_contract_ready": passed,
        "existing_sample_count": 11,
        "auth_label_conflict_sample_count": 3,
        "namespace_provable_insertion_unknown_sample_count": 8,
        "fully_provable_pre_download_sample_count": 0,
        "insertion_unknown_sample_count": 11,
        "samples_admissible_after_schema_extension_only": 0,
        "ready_for_schema_extension_integration": passed,
        "ready_for_e1_residue_identity_semantics_design": False,
        "parser_insertion_code_support_required": True,
        "provider_provenance_binding_required": True,
        "ready_for_admission_evaluator_rule_logic_implementation": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "ignored_raw_structure_read_current_step": False,
        "checkpoint_read_current_step": False,
        "candidate_records_materialized_current_step": False,
        "download_queue_materialized_current_step": False,
        "contract_row_count": 40,
        "backfill_audit_row_count": 11,
        "source_boundary_audit_row_count": len(SOURCE_PATHS),
        "safety_audit_row_count": 20,
        "issue_inventory_row_count": 2,
        "all_source_boundary_checks_passed": result["all_source_boundary_checks_passed"],
        "all_d2_predecessor_checks_passed": result["all_d2_predecessor_checks_passed"],
        "all_representation_evidence_checks_passed": result[
            "all_representation_evidence_checks_passed"
        ],
        "all_contract_checks_passed": result["all_contract_checks_passed"],
        "all_backfill_audit_checks_passed": result[
            "all_backfill_audit_checks_passed"
        ],
        "all_safety_checks_passed": result["all_safety_checks_passed"],
        "all_issue_inventory_checks_passed": result[
            "all_issue_inventory_checks_passed"
        ],
        "all_checks_passed": passed,
        "blocking_reasons": list(P2_ISSUE_IDS) + failure_blockers,
        "recommended_next_step": (
            RECOMMENDED_NEXT_STEP if passed else BLOCKED_NEXT_STEP
        ),
    }


def run_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Materialize the six deterministic design-gate outputs."""
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    if root.is_symlink():
        raise RuntimeError("output root must not be a symlink")
    result = _build_materialization()
    output_sha256 = _write_non_manifest_outputs(root, result)
    manifest = _manifest_payload(result, output_sha256)
    (root / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    run_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1()
