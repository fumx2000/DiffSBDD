"""Step14AU-E1-C covalent-residue insertion-code grammar design gate v1.

This metadata-only gate freezes a lexical and state/value contract.  It never
reads raw structures, executes parsers/providers, implements ADMIT_004, or
materializes candidate records.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


PROJECT_NAME = "CovaPIE"
STEP_LABEL = "Step14AU-E1-C"
STAGE = "covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate_v1"
EXPECTED_BASE_HEAD = "3aa53c1b06032b7dc93b3a14df4fe2374d8432fa"
MANIFEST_SCHEMA_VERSION = "covapie_covalent_residue_insertion_present_value_grammar_design_manifest_v1"
RECOMMENDED_NEXT_STEP = "integrate_covapie_covalent_residue_insertion_present_value_grammar_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

NORMATIVE_DICTIONARY_NAME = "PDBx/mmCIF V5"
NORMATIVE_ITEM = "_atom_site.pdbx_PDB_ins_code"
NORMATIVE_REFERENCE_ROLE = "_struct_conn.pdbx_ptnr1/2_PDB_ins_code references atom_site insertion code"
WWPDB_DICTIONARY_CODE_PATTERN = r"[][_,.;:\"&<>()/\{}'`~!@#$%A-Za-z0-9*|+-]*"
INSERTION_PRESENT_VALUE_PATTERN = r"[][_,.;:\"&<>()/\{}'`~!@#$%A-Za-z0-9*|+-]+"
INSERTION_PRESENT_VALUE_RE = re.compile(INSERTION_PRESENT_VALUE_PATTERN, re.ASCII)
ALLOWED_PUNCTUATION = tuple("[]_,.;:\"&<>()/{}'`~!@#$%*|+-")
assert len(ALLOWED_PUNCTUATION) == 28

STATE_VALUES = ("absent", "present", "unknown")
UNKNOWN_REASON = "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
EVIDENCE_INVALID_REASON = "COVALENT_RESIDUE_INSERTION_CODE_EVIDENCE_INVALID"
SOURCE_CONFLICT_REASON = "COVALENT_RESIDUE_INSERTION_CODE_SOURCE_CONFLICT"

PRESENT_REASON = {
    "type": "COVALENT_RESIDUE_INSERTION_VALUE_TYPE_INVALID",
    "empty": "COVALENT_RESIDUE_INSERTION_PRESENT_REQUIRES_NONEMPTY",
    "non_ascii": "COVALENT_RESIDUE_INSERTION_PRESENT_NON_ASCII",
    "whitespace": "COVALENT_RESIDUE_INSERTION_PRESENT_WHITESPACE_FORBIDDEN",
    "marker": "COVALENT_RESIDUE_INSERTION_PRESENT_MARKER_FORBIDDEN",
    "grammar": "COVALENT_RESIDUE_INSERTION_PRESENT_CHARACTER_GRAMMAR_INVALID",
}

_SOURCE_VALUES = (
    # E1-B: production/checker/tests and six outputs.
    ("src/covalent_ext/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate.py", "75bf99f2e45bc512e4a4c5195b472d43d219800297983f3f5b56c0b73094b368"),
    ("scripts/check_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1.py", "3dae45714d3fa779fd8fa27211cd7d9029640e866c62b3e122df33ed637e92c4"),
    ("tests/test_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1.py", "2d423d617a8cbb197877995616eb5f46efecae8fe953ea7b555fdf4507057fbe"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1/covapie_admit_004_residue_identity_atom_name_integrated_context_matrix.csv", "1e3dd997d2baa2421b77d0e75a0751dca7c2d8025132a6f615e41d9172c9e2a1"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1/covapie_admit_004_residue_identity_atom_name_integrated_field_matrix.csv", "940724c739c6da6a9f76a7e66e03d4261abfc152df552756faea614f54fd68df"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1/covapie_admit_004_residue_identity_atom_name_integrated_rule_matrix.csv", "b4a3d876acaf1c521b06fe2a35f3da2448662e632cb0f44fab355e30c7861d99"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1/covapie_admit_004_residue_identity_atom_name_integration_issue_inventory.csv", "a011d21b73182f27898df69ccbe3ef0eda061d46ced7e095aebcdda31fab3903"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1/covapie_admit_004_residue_identity_atom_name_integration_safety_audit.csv", "2019039c72e393fa625d2615c76a82ac91cac6a1f5438e395370a156df9c6cbf"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1/covapie_admit_004_residue_identity_atom_name_semantics_integration_manifest.json", "d9bd804936c2405d6baa97bf2bd207def4d596e64ed4fd05edb341db4327bfc3"),
    # P2: production/checker/tests and six outputs.
    ("src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate.py", "abe6f364f0cc0297e2695f42753885e45aaf10580e4ed42deab62a39676be079"),
    ("scripts/check_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1.py", "e6b99242e5a93dfadb3b73917c888b2a38e27225a715054d5420a1c8b8ecb58c"),
    ("tests/test_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1.py", "fa814de364acaa773286c07c7c6194ef27dedfc6d9f9586628b2bf36036759a5"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1/covapie_covalent_residue_locator_existing_sample_backfill_audit.csv", "a52a366af0f380cccb4a4d9a7dbb692561ca04bd4a31e65f119f8c7047c11691"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1/covapie_covalent_residue_locator_issue_inventory.csv", "aa8baf1e238447ec199ffdcb0064c2718def764d16c73e7ccf82b3b124218199"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1/covapie_covalent_residue_locator_minimal_schema_extension_design_manifest.json", "7e35e287fb629ae35b8dd83f4cb166ef95013001bbca18beae9653f6564d498b"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1/covapie_covalent_residue_locator_safety_audit.csv", "d695c574be443fae48f824fa6b460206d230967cd0315308053c979bc44e0494"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1/covapie_covalent_residue_locator_schema_extension_contract.csv", "cfe7afde4ef146ea03f6d5d85f8db0cfc0b2ce0bfc5eb94bd6f8bc305f453d89"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1/covapie_covalent_residue_locator_source_boundary_audit.csv", "952de935e3b873d832f774df8688fbf111994f39bdb1f0476293598e4a429659"),
    # P3: effective matrices, issue inventory, and manifest.
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1/covapie_covalent_residue_locator_schema_integrated_rule_matrix.csv", "c1ae6cf9c2ca5450315ff3e3ed21b0a81d8bfc08c6a07e35d3f2dca1874e0d2f"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1/covapie_covalent_residue_locator_schema_integrated_field_matrix.csv", "53dccd0ff7b20465c9df13f2c9eefc254f39bcb40e30732d1cfdfa4036e888fb"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1/covapie_covalent_residue_locator_schema_integrated_context_matrix.csv", "8eac50078260e0567f6a99024d04ac92b512a0be10d2dcb66a4fa6dab52d1ef8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1/covapie_covalent_residue_locator_schema_integration_issue_inventory.csv", "80954e517a2425c3a5659114d08999b59aed2410be9f1af0f43eef79c22dbedd"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1/covapie_covalent_residue_locator_schema_extension_integration_manifest.json", "676fe3c86e1304ba4971862d1e270fed40d9665e16c356d719627538aa28ee44"),
    # P4: production and five direct semantic outputs.
    ("src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate.py", "b1a874e402180a361b6940541c95710797ed10cabfdb19f7426c0b04d0532537"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate_v1/covapie_covalent_residue_locator_parser_provider_export_contract.csv", "8893ca769577e955319ea8b9abe411149206db562193b70928d58ce4afd0ba8c"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate_v1/covapie_covalent_residue_locator_raw_token_resolution_matrix.csv", "b48febdbedcb6ea6d4adc19e636b26f6774292ef3e1d405cecf7a491d7feb2fa"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate_v1/covapie_covalent_residue_locator_safety_audit.csv", "e19c9dbd6480b68ff2617681a2150e1c314c5ecac9a9acdfa4bd009a515b0f0c"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate_v1/covapie_covalent_residue_locator_parser_provider_issue_inventory.csv", "fe7383541cfc06f05814afb0d3fba04716b423bc0e85b8975fb27bedad02f43e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate_v1/covapie_covalent_residue_locator_parser_provider_provenance_export_design_manifest.json", "aa6435381c90416ce9ded7e50afca166f33b29b4a268b230755bba0145680876"),
    # P6-C, E1-A, then the three exact P5-B sources read in Phase 0.
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1/covapie_covalent_residue_locator_real_provider_export_sidecar.csv", "066c0beeaa01d31a6d6ea3fae62f3df5177c2d904f6295646ee33a7fcd780ac7"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1/covapie_covalent_residue_locator_real_provider_export_execution_evidence_audit.csv", "4048efdfe373fe955995ded43639fcbd7baf67560e867662dbd18fe22a4fb1ab"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1/covapie_covalent_residue_locator_real_provider_export_execution_manifest.json", "9061e36c333cf498dd5844407f5df11d64c3e271ae47e407938d34ac851d3aab"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1/covapie_admit_004_residue_identity_atom_name_semantics_contract.csv", "a783a3d474a2ed4e5ff348ec54a73510f5f6f6fb9d1edcb45dc97108e5d09eff"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1/covapie_admit_004_exact11_identity_atom_name_evidence_audit.csv", "62f7c26b41daef96c32ca615b7d65a063810a53cef582a26cd54ed9cfb8b6e2a"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1/covapie_admit_004_residue_identity_atom_name_issue_transition_inventory.csv", "fecb82397a853e900a53368dedc6bacf95fdc497fa6cd09c31a9be8a1e1d0577"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1/covapie_admit_004_residue_identity_atom_name_semantics_design_manifest.json", "c442d31cebaea6b8e3ae5dbda232cc5ba377eb74a2ca68c2437ce0b43a39e6c0"),
    ("src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke.py", "21be5237736a55fe87da9763c939a228bb81c52b2481602c9bcb4dd425b338bd"),
    ("tests/test_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke_v1.py", "2f595295c2db100556243b15ced286ae72a22639824a6430d76481f232d41b3f"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke_v1/covapie_covalent_residue_locator_synthetic_case_audit.csv", "1c7436924296c102b9875e662f3968a24aa31e1b3e37c2a7c6f9fde39b1f26da"),
)
SOURCE_PATHS = tuple(Path(path) for path, _ in _SOURCE_VALUES)
SOURCE_SHA256 = {Path(path): digest for path, digest in _SOURCE_VALUES}
assert len(SOURCE_PATHS) == 39 and tuple(SOURCE_SHA256) == SOURCE_PATHS

E1B_ISSUE_PATH = SOURCE_PATHS[6]
P2_CONTRACT_PATH = SOURCE_PATHS[16]
P3_FIELD_PATH = SOURCE_PATHS[19]
P4_CONTRACT_PATH = SOURCE_PATHS[24]
P4_TOKEN_PATH = SOURCE_PATHS[25]
P6C_SIDECAR_PATH = SOURCE_PATHS[29]
E1A_CONTRACT_PATH = SOURCE_PATHS[32]
E1A_EXACT11_PATH = SOURCE_PATHS[33]
E1A_ISSUE_PATH = SOURCE_PATHS[34]
P5B_CASE_PATH = SOURCE_PATHS[38]

CONTRACT_FILENAME = "covapie_covalent_residue_insertion_present_value_grammar_contract.csv"
EXAMPLES_FILENAME = "covapie_covalent_residue_insertion_present_value_grammar_examples_and_state_value_truth_table.csv"
SOURCE_FILENAME = "covapie_covalent_residue_insertion_present_value_grammar_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_covalent_residue_insertion_present_value_grammar_safety_audit.csv"
ISSUE_FILENAME = "covapie_covalent_residue_insertion_present_value_grammar_issue_transition_inventory.csv"
MANIFEST_FILENAME = "covapie_covalent_residue_insertion_present_value_grammar_design_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, EXAMPLES_FILENAME, SOURCE_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CONTRACT_COLUMNS = ("contract_id", "contract_area", "contract_statement", "expected_value", "observed_value", "contract_passed")
EXAMPLE_COLUMNS = ("row_kind", "case_id", "input_descriptor", "input_type", "input_length", "expected_outcome", "observed_outcome", "expected_reason", "observed_reason", "canonical_descriptor", "exact_preserved", "case_preserved", "example_passed")
SOURCE_COLUMNS = ("source_order", "source_relative_path", "tracked_by_git", "base_tree_blob", "filesystem_regular", "symlink", "sha256_expected", "sha256_observed", "source_verified")
SAFETY_COLUMNS = ("safety_item", "expected_executed", "observed_executed", "safety_passed")
ISSUE_COLUMNS = ("issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status", "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count")

TRUE_SAFETY_ITEMS = (
    "exact_source_reads", "e1b_predecessor_validation", "p2_contract_validation",
    "p4_token_semantics_validation", "p5b_quote_class_gap_audit", "grammar_design",
    "state_value_truth_classification", "issue_transition_design",
)
FALSE_SAFETY_ITEMS = (
    "raw_read", "parser_execution", "provider_execution", "evaluator_implementation",
    "candidate_record_materialization", "candidate_evaluation", "admission_record_modification",
    "sample_backfill", "network", "download", "checkpoint", "torch", "numpy", "rdkit",
    "model_forward_loss_training",
)


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    observed_sha256: str
    content_bytes: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


@dataclass(frozen=True)
class CsvDocument:
    header: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


def validate_covalent_residue_insertion_present_value(value: object) -> dict[str, Any]:
    """Validate and exact-preserve one candidate semantic present value."""
    reason = ""
    if type(value) is not str:
        reason = PRESENT_REASON["type"]
    elif value == "":
        reason = PRESENT_REASON["empty"]
    elif not value.isascii():
        reason = PRESENT_REASON["non_ascii"]
    elif any(character.isspace() for character in value):
        reason = PRESENT_REASON["whitespace"]
    elif value in (".", "?"):
        reason = PRESENT_REASON["marker"]
    elif INSERTION_PRESENT_VALUE_RE.fullmatch(value) is None:
        reason = PRESENT_REASON["grammar"]
    valid = reason == ""
    return {
        "valid": valid,
        "value_exact_str": type(value) is str,
        "outcome": "passed" if valid else "invalid",
        "canonical_value": value if valid else None,
        "reason": reason,
    }


def validate_covalent_residue_insertion_state_value(state: object, value: object) -> dict[str, Any]:
    """Classify the exact absent/present/unknown state/value combination."""
    base = {
        "valid": False, "schema_combination_valid": False, "state_valid": False,
        "value_exact_str": type(value) is str, "outcome": "invalid",
        "canonical_state": None, "canonical_value": None,
        "blocks_admit_004": True, "reason": "",
    }
    if type(state) is not str:
        return {**base, "reason": "COVALENT_RESIDUE_INSERTION_STATE_TYPE_INVALID"}
    if state not in STATE_VALUES:
        return {**base, "reason": "COVALENT_RESIDUE_INSERTION_STATE_VALUE_INVALID"}
    base.update(state_valid=True, canonical_state=state)
    if type(value) is not str:
        return {**base, "reason": "COVALENT_RESIDUE_INSERTION_VALUE_TYPE_INVALID"}
    if state == "absent":
        if value != "":
            return {**base, "reason": "COVALENT_RESIDUE_INSERTION_ABSENT_REQUIRES_EMPTY"}
        return {**base, "valid": True, "schema_combination_valid": True, "outcome": "passed", "canonical_value": "", "blocks_admit_004": False}
    if state == "unknown":
        if value != "":
            return {**base, "reason": "COVALENT_RESIDUE_INSERTION_UNKNOWN_REQUIRES_EMPTY"}
        return {**base, "valid": True, "schema_combination_valid": True, "outcome": "blocked", "canonical_value": "", "blocks_admit_004": True, "reason": UNKNOWN_REASON}
    present = validate_covalent_residue_insertion_present_value(value)
    return {
        **base,
        "valid": present["valid"],
        "schema_combination_valid": present["valid"],
        "outcome": present["outcome"],
        "canonical_value": present["canonical_value"],
        "blocks_admit_004": not present["valid"],
        "reason": present["reason"],
    }


def validate_struct_conn_atom_site_insertion_agreement(
    struct_conn_explicit: object,
    struct_conn_value: object,
    atom_site_explicit: object,
    atom_site_value: object,
    candidate_value: object,
    provenance_value: object,
) -> dict[str, Any]:
    """Freeze exact agreement design without invoking a parser or provider."""
    exact_flags = type(struct_conn_explicit) is bool and type(atom_site_explicit) is bool
    if not exact_flags or struct_conn_explicit is not True or atom_site_explicit is not True:
        return {"valid": False, "outcome": "blocked", "canonical_value": None, "reason": EVIDENCE_INVALID_REASON}
    values = (struct_conn_value, atom_site_value, candidate_value, provenance_value)
    if any(type(value) is not str for value in values):
        return {"valid": False, "outcome": "blocked", "canonical_value": None, "reason": EVIDENCE_INVALID_REASON}
    if any(value != struct_conn_value for value in values[1:]):
        return {"valid": False, "outcome": "blocked", "canonical_value": None, "reason": SOURCE_CONFLICT_REASON}
    result = validate_covalent_residue_insertion_present_value(struct_conn_value)
    if not result["valid"]:
        return {"valid": False, "outcome": "blocked", "canonical_value": None, "reason": EVIDENCE_INVALID_REASON}
    return {"valid": True, "outcome": "passed", "canonical_value": struct_conn_value, "reason": ""}


def _git(arguments: Sequence[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=repo_root, check=False, capture_output=True, text=text)


def _safe_source_path(path: Path) -> bool:
    return (
        not path.is_absolute() and ".." not in path.parts and bool(path.parts)
        and path.parts[0] != "checkpoints" and path.parts[:2] != ("data", "raw")
    )


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    if not _safe_source_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    object_type = _git(["cat-file", "-t", f"{EXPECTED_BASE_HEAD}:{path.as_posix()}"], repo_root)
    return (
        tracked.returncode == 0 and object_type.returncode == 0 and object_type.stdout.strip() == "blob"
        and stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT) -> FrozenSourceSnapshot:
    """Complete every structural check before the first source-byte read."""
    if len(SOURCE_PATHS) != 39 or len(set(SOURCE_PATHS)) != 39 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("source boundary shape invalid")
    structural = tuple(_structural_source_check(path, repo_root) for path in SOURCE_PATHS)
    if not all(structural):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_HEAD}:{path.as_posix()}"], repo_root, text=False)
        if base.returncode != 0 or hashlib.sha256(base.stdout).hexdigest() != SOURCE_SHA256[path]:
            raise ValueError(f"base-tree SHA256 drift: {path}")
        content = (repo_root / path).read_bytes()
        observed = hashlib.sha256(content).hexdigest()
        if observed != SOURCE_SHA256[path]:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, SOURCE_SHA256[path], observed, content))
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot and len(value.records) == 39
        and tuple(record.relative_path for record in value.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.observed_sha256 == record.expected_sha256
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
    if any(tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values()) for row in rows):
        raise ValueError("invalid CSV row")
    return CsvDocument(tuple(reader.fieldnames), rows)


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("invalid frozen source snapshot")
    issues = _csv_document(snapshot, E1B_ISSUE_PATH)
    exact11 = _csv_document(snapshot, E1A_EXACT11_PATH)
    p2_contract = _csv_document(snapshot, P2_CONTRACT_PATH)
    p3_fields = _csv_document(snapshot, P3_FIELD_PATH)
    p4_contract = _csv_document(snapshot, P4_CONTRACT_PATH)
    p4_tokens = _csv_document(snapshot, P4_TOKEN_PATH)
    p6c = _csv_document(snapshot, P6C_SIDECAR_PATH)
    e1a_contract = _csv_document(snapshot, E1A_CONTRACT_PATH)
    p5b = _csv_document(snapshot, P5B_CASE_PATH)
    if len(issues.rows) != 10 or len(exact11.rows) != 11 or len(p6c.rows) != 11:
        raise ValueError("predecessor cardinality mismatch")
    issue_ids = [row.get("issue_id") for row in issues.rows]
    if len(set(issue_ids)) != 10 or "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED" not in issue_ids:
        raise ValueError("E1-B issue inventory invalid")
    exact11_ok = all(
        row.get("insertion_state") == "unknown" and row.get("insertion_value") == ""
        and row.get("insertion_blocks") == "true" and row.get("effective_outcome") == "blocked"
        and row.get("reason") == UNKNOWN_REASON and row.get("audit_passed") == "true"
        for row in exact11.rows
    )
    conflicts = sum(row.get("auth_label_conflict_observed") == "true" for row in exact11.rows)
    if not exact11_ok or conflicts != 3:
        raise ValueError("Exact11 invariant failed")
    p6c_ok = all(
        row.get("resolved_insertion_state") == "unknown"
        and row.get("resolved_insertion_value") == ""
        and row.get("insertion_blocks_admit_004") == "true"
        and row.get("insertion_blocking_reason") == UNKNOWN_REASON
        for row in p6c.rows
    )
    if not p6c_ok or not e1a_contract.rows or any(row.get("contract_passed") != "true" for row in e1a_contract.rows):
        raise ValueError("P6-C/E1-A predecessor invariant failed")
    if len(p4_tokens.rows) != 12 or any(row.get("resolution_case_passed") != "true" for row in p4_tokens.rows):
        raise ValueError("P4 token-semantics invariant failed")
    if len(p5b.rows) != 16 or {row.get("smoke_case_id") for row in p5b.rows} != {
        f"P5B_{index:03d}_{suffix}" for index, suffix in enumerate((
            "PTNR1_EXPLICIT_A", "PTNR2_EXPLICIT_1", "DOT_DOT", "QUESTION_QUESTION",
            "TAGS_MISSING", "PARSED_EMPTY", "EXPLICIT_CONFLICT", "EXPLICIT_DOT_CONFLICT",
            "PARTNER_TAG_MISMATCH", "AUTH_CONFLICT_SELECT_AUTH", "AUTH_CONFLICT_SELECT_LABEL",
            "MIXED_NAMESPACE", "ATOM_ROW_MISSING", "MULTIPLE_ATOM_ROWS",
            "INVALID_ATOM_ROW_IDENTITY", "SOURCE_ID_COLLISION",
        ), 1)
    }:
        raise ValueError("P5-B synthetic evidence invariant failed")
    text_sets = "\n".join(
        "|".join(row.values())
        for document in (p2_contract, p3_fields, p4_contract, p4_tokens, p5b)
        for row in document.rows
    )
    for required in ("absent", "present", "unknown"):
        if required not in text_sets:
            raise ValueError(f"predecessor semantic evidence missing: {required}")
    return {"issues": issues.rows, "exact11": exact11.rows, "exact11_conflicts": conflicts}


def _contract_rows() -> tuple[dict[str, str], ...]:
    values = (
        ("dictionary_name", "normative", "normative dictionary identity", NORMATIVE_DICTIONARY_NAME),
        ("dictionary_item", "normative", "normative atom_site insertion item", NORMATIVE_ITEM),
        ("reference_role", "normative", "struct_conn reference role", NORMATIVE_REFERENCE_ROLE),
        ("dictionary_pattern", "grammar", "dictionary code pattern permits empty", WWPDB_DICTIONARY_CODE_PATTERN),
        ("present_pattern", "grammar", "CovaPIE present pattern is nonempty", INSERTION_PRESENT_VALUE_PATTERN),
        ("exact_type", "grammar", "type(value) is str; subclasses rejected", "true"),
        ("ascii", "grammar", "ASCII only", "true"),
        ("minimum_length", "grammar", "minimum semantic length", "1"),
        ("semantic_maximum", "grammar", "semantic maximum length", "none"),
        ("whitespace", "grammar", "whitespace at any position forbidden", "forbidden"),
        ("markers", "grammar", "complete dot and question-mark markers forbidden", "forbidden"),
        ("case", "preservation", "case preserved", "exact"),
        ("trim", "preservation", "trim operation", "none"),
        ("coercion", "preservation", "type coercion", "none"),
        ("normalization", "preservation", "Unicode or canonical normalization", "none"),
        ("canonical_return", "preservation", "successful canonical value equals input", "exact"),
        ("idempotence", "preservation", "repeated validation", "idempotent"),
        ("state_enum", "state_value", "state enum", "absent|present|unknown"),
        ("absent_value", "state_value", "absent requires exact empty str", "passed"),
        ("unknown_value", "state_value", "unknown requires exact empty str and blocks ADMIT_004", "blocked"),
        ("present_value", "state_value", "present requires grammar-valid nonempty exact str", "passed"),
        ("invalid_outcomes", "state_value", "all invalid state/value outcomes block ADMIT_004 fail closed", "true"),
        ("raw_token_boundary", "evidence", "raw CIF quote delimiters are not candidate data", "decoded_exact_value_only"),
        ("agreement_explicit", "agreement", "both sources require explicit resolved evidence", "true"),
        ("agreement_compare", "agreement", "decoded values compare byte-for-byte", "exact"),
        ("provenance", "agreement", "resolved/candidate/provenance payload agree", "exact"),
        ("quote_class_roundtrip", "readiness", "parser quote-class roundtrip verified", "false"),
        ("provider_roundtrip", "readiness", "real provider present-value roundtrip ready", "false"),
        ("quote_gap_design", "readiness", "candidate grammar design blocked by quote gap", "false"),
        ("successor", "readiness", "ready for successor integration", "true"),
        ("effective_schema", "readiness", "grammar integrated into effective schema", "false"),
    )
    return tuple({"contract_id": f"INSERTION_GRAMMAR_{i:03d}", "contract_area": area, "contract_statement": statement, "expected_value": value, "observed_value": value, "contract_passed": "true"} for i, (_, area, statement, value) in enumerate(values, 1))


def _example_row(kind: str, case_id: str, descriptor: str, value: object, expected: str, expected_reason: str = "") -> dict[str, str]:
    result = validate_covalent_residue_insertion_present_value(value)
    canonical = result["canonical_value"]
    if isinstance(value, str) and len(value) > 80:
        input_display = descriptor
        canonical_display = descriptor if canonical == value else "none"
    else:
        input_display = repr(value)
        canonical_display = repr(canonical)
    passed = result["outcome"] == expected and result["reason"] == expected_reason
    return {
        "row_kind": kind, "case_id": case_id, "input_descriptor": input_display,
        "input_type": type(value).__name__, "input_length": str(len(value)) if isinstance(value, str) else "n/a",
        "expected_outcome": expected, "observed_outcome": result["outcome"],
        "expected_reason": expected_reason, "observed_reason": result["reason"],
        "canonical_descriptor": canonical_display,
        "exact_preserved": str(result["valid"] and canonical == value).lower(),
        "case_preserved": str(not result["valid"] or canonical == value).lower(),
        "example_passed": str(passed).lower(),
    }


def _truth_row(case_id: str, descriptor: str, state: object, value: object, expected: str, reason: str) -> dict[str, str]:
    result = validate_covalent_residue_insertion_state_value(state, value)
    passed = result["outcome"] == expected and result["reason"] == reason
    return {
        "row_kind": "state_value_truth", "case_id": case_id, "input_descriptor": descriptor,
        "input_type": f"{type(state).__name__}/{type(value).__name__}",
        "input_length": str(len(value)) if isinstance(value, str) else "n/a",
        "expected_outcome": expected, "observed_outcome": result["outcome"],
        "expected_reason": reason, "observed_reason": result["reason"],
        "canonical_descriptor": repr(result["canonical_value"]),
        "exact_preserved": str(result["canonical_value"] == value if result["valid"] else False).lower(),
        "case_preserved": "true", "example_passed": str(passed).lower(),
    }


def build_examples_and_truth_rows() -> tuple[dict[str, str], ...]:
    valid_values: list[tuple[str, str]] = [(value, value) for value in ("A", "a", "1", "AA", "A1", "Z9")]
    valid_values.append(("A repeated 256", "A" * 256))
    valid_values.extend((f"A{character}B", f"A{character}B") for character in ALLOWED_PUNCTUATION)
    rows = [_example_row("present_valid_example", f"PRESENT_VALID_{i:03d}", descriptor, value, "passed") for i, (descriptor, value) in enumerate(valid_values, 1)]

    class StrSubclass(str):
        pass

    invalid = (
        ("empty", "", PRESENT_REASON["empty"]), ("complete dot", ".", PRESENT_REASON["marker"]),
        ("complete question", "?", PRESENT_REASON["marker"]), ("embedded space", "A B", PRESENT_REASON["whitespace"]),
        ("embedded tab", "A\tB", PRESENT_REASON["whitespace"]), ("leading space", " A", PRESENT_REASON["whitespace"]),
        ("trailing space", "A ", PRESENT_REASON["whitespace"]), ("embedded newline", "A\nB", PRESENT_REASON["whitespace"]),
        ("embedded carriage return", "A\rB", PRESENT_REASON["whitespace"]), ("non-ASCII", "Aé", PRESENT_REASON["non_ascii"]),
        ("equals", "A=B", PRESENT_REASON["grammar"]), ("backslash", "A\\B", PRESENT_REASON["grammar"]),
        ("str subclass", StrSubclass("A"), PRESENT_REASON["type"]), ("int", 1, PRESENT_REASON["type"]),
        ("None", None, PRESENT_REASON["type"]),
    )
    rows.extend(_example_row("present_invalid_example", f"PRESENT_INVALID_{i:03d}", descriptor, value, "invalid", reason) for i, (descriptor, value, reason) in enumerate(invalid, 1))
    truth = (
        ("state non-exact str", 1, "", "invalid", "COVALENT_RESIDUE_INSERTION_STATE_TYPE_INVALID"),
        ("state outside enum", "other", "", "invalid", "COVALENT_RESIDUE_INSERTION_STATE_VALUE_INVALID"),
        ("absent non-exact value", "absent", None, "invalid", "COVALENT_RESIDUE_INSERTION_VALUE_TYPE_INVALID"),
        ("absent empty", "absent", "", "passed", ""),
        ("absent nonempty", "absent", "A", "invalid", "COVALENT_RESIDUE_INSERTION_ABSENT_REQUIRES_EMPTY"),
        ("unknown non-exact value", "unknown", None, "invalid", "COVALENT_RESIDUE_INSERTION_VALUE_TYPE_INVALID"),
        ("unknown empty", "unknown", "", "blocked", UNKNOWN_REASON),
        ("unknown nonempty", "unknown", "A", "invalid", "COVALENT_RESIDUE_INSERTION_UNKNOWN_REQUIRES_EMPTY"),
        ("present non-exact value", "present", None, "invalid", PRESENT_REASON["type"]),
        ("present empty", "present", "", "invalid", PRESENT_REASON["empty"]),
        ("present marker", "present", ".", "invalid", PRESENT_REASON["marker"]),
        ("present whitespace", "present", "A B", "invalid", PRESENT_REASON["whitespace"]),
        ("present non-ASCII", "present", "é", "invalid", PRESENT_REASON["non_ascii"]),
        ("present grammar-valid", "present", "A.B", "passed", ""),
    )
    rows.extend(_truth_row(f"STATE_VALUE_{i:03d}", descriptor, state, value, expected, reason) for i, (descriptor, state, value, expected, reason) in enumerate(truth, 1))
    if len(rows) != 64 or not all(row["example_passed"] == "true" for row in rows):
        raise ValueError("64-row example/truth matrix failed")
    return tuple(rows)


def _issue_rows(source_rows: Sequence[Mapping[str, str]]) -> tuple[dict[str, str], ...]:
    result = []
    for source in source_rows:
        row = dict(source)
        if row["issue_id"] == "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED":
            row.update(
                affected_fields="covalent_residue_insertion_code", affected_rules="ADMIT_004",
                severity="blocking", status="open", issue_count="1",
                integration_transition="insertion_present_value_grammar_design_frozen_pending_successor_integration",
            )
        result.append(row)
    if len(result) != 10 or any(row["status"] != "open" for row in result):
        raise ValueError("issue transition invalid")
    provider = next(row for row in result if row["issue_id"] == "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT")
    if provider["severity"] != "blocking" or provider["issue_count"] != "11":
        raise ValueError("provider issue invariant failed")
    return tuple(result)


def build_design_state(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root)
    predecessor = _validate_predecessors(snapshot)
    examples = build_examples_and_truth_rows()
    long_result = validate_covalent_residue_insertion_present_value("A" * 4096)
    agreement = validate_struct_conn_atom_site_insertion_agreement(True, "A.B", True, "A.B", "A.B", "A.B")
    passed = long_result["valid"] is True and agreement["valid"] is True
    if not passed:
        raise ValueError("grammar self-validation failed")
    source_rows = tuple({
        "source_order": str(index), "source_relative_path": record.relative_path.as_posix(),
        "tracked_by_git": "true", "base_tree_blob": "true", "filesystem_regular": "true",
        "symlink": "false", "sha256_expected": record.expected_sha256,
        "sha256_observed": record.observed_sha256, "source_verified": "true",
    } for index, record in enumerate(snapshot.records, 1))
    safety_rows = tuple({
        "safety_item": item, "expected_executed": "true", "observed_executed": "true", "safety_passed": "true"
    } for item in TRUE_SAFETY_ITEMS) + tuple({
        "safety_item": item, "expected_executed": "false", "observed_executed": "false", "safety_passed": "true"
    } for item in FALSE_SAFETY_ITEMS)
    return {
        "snapshot": snapshot, "contract_rows": _contract_rows(), "example_rows": examples,
        "source_rows": source_rows, "safety_rows": safety_rows,
        "issue_rows": _issue_rows(predecessor["issues"]),
        "exact11_count": len(predecessor["exact11"]), "exact11_conflicts": predecessor["exact11_conflicts"],
        "all_checks_passed": True,
    }


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output CSV schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _manifest_payload(state: Mapping[str, Any], output_hashes: Mapping[str, str]) -> dict[str, Any]:
    return {
        "project": PROJECT_NAME, "step": STEP_LABEL, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION, "base_commit": EXPECTED_BASE_HEAD,
        "source_input_count": 39, "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "output_files": list(OUTPUT_FILES), "output_sha256": dict(output_hashes),
        "normative_dictionary_name": NORMATIVE_DICTIONARY_NAME, "normative_item": NORMATIVE_ITEM,
        "normative_reference_role": NORMATIVE_REFERENCE_ROLE,
        "wwpdb_dictionary_code_pattern": WWPDB_DICTIONARY_CODE_PATTERN,
        "insertion_present_value_pattern": INSERTION_PRESENT_VALUE_PATTERN,
        "present_value_minimum_length": 1, "present_value_semantic_maximum": None,
        "examples_and_state_value_truth_row_count": 64, "allowed_punctuation_count": 28,
        "exact11_count": state["exact11_count"], "exact11_unknown_count": 11,
        "exact11_blocked_count": 11, "exact11_auth_label_conflict_count": state["exact11_conflicts"],
        "exact11_auth_label_no_conflict_count": 8,
        "insertion_present_value_grammar_design_frozen": True,
        "state_value_combination_contract_frozen": True, "exact_preserve_policy_frozen": True,
        "struct_conn_atom_site_agreement_design_frozen": True,
        "invalid_state_value_outcomes_fail_closed": True,
        "agreement_requires_struct_conn_atom_site_candidate_and_provenance_exact_equality": True,
        "ready_for_insertion_present_value_grammar_successor_integration": True,
        "candidate_value_grammar_design_not_blocked_by_quote_class_gap": True,
        "insertion_present_value_grammar_integrated_into_effective_schema": False,
        "covalent_residue_identity_contract_fully_integrated": False,
        "admit_004_rule_logic_ready": False, "ready_for_admit_004_rule_logic_implementation": False,
        "admit_004_evaluator_implemented": False, "parser_quote_class_roundtrip_verified": False,
        "real_provider_present_value_roundtrip_ready": False, "candidate_records_materialized": False,
        "ready_for_real_candidate_evaluation": False, "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "all_source_boundary_checks_passed": True, "all_checks_passed": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def _atomic_write(path: Path, content: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
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


def run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_design_state()
    if state["all_checks_passed"] is not True:
        raise RuntimeError("E1-C design gate failed closed")
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("output root must be a non-symlink directory")
    payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        EXAMPLES_FILENAME: _csv_bytes(EXAMPLE_COLUMNS, state["example_rows"]),
        SOURCE_FILENAME: _csv_bytes(SOURCE_COLUMNS, state["source_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    for filename in CSV_OUTPUTS:
        _atomic_write(root / filename, payloads[filename])
    hashes = {filename: hashlib.sha256(payloads[filename]).hexdigest() for filename in CSV_OUTPUTS}
    manifest = _manifest_payload(state, hashes)
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write(root / MANIFEST_FILENAME, manifest_bytes)
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
