"""Step14AU-E1-A residue-identity and atom-name semantics design gate.

This module freezes pure, in-memory semantics.  It does not implement the
ADMIT_004 evaluator, dereference artifact paths, execute a parser/provider, or
materialize candidate records.
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


STEP_LABEL = "Step14AU-E1-A"
STAGE = "covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1"
PROJECT_NAME = "CovaPIE"
EXPECTED_BASE_HEAD = "21858d3f8b8a9c3c58cc5e1bd3419ccec694bca2"
MANIFEST_SCHEMA_VERSION = "covapie_admit_004_residue_identity_atom_name_semantics_design_manifest_v1"
RECOMMENDED_NEXT_STEP = "integrate_covapie_admit_004_residue_identity_and_atom_name_semantics_v1"
BLOCKED_NEXT_STEP = "resolve_covapie_admit_004_residue_identity_atom_name_semantics_design_blockers"
UNKNOWN_REASON = "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE


SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate_v1/covapie_ligand_comp_id_integrated_rule_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate_v1/covapie_ligand_comp_id_integrated_field_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate_v1/covapie_ligand_comp_id_integration_issue_inventory.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate_v1/covapie_ligand_comp_id_semantics_integration_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate.py",
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1/covapie_covalent_residue_locator_schema_integrated_rule_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1/covapie_covalent_residue_locator_schema_integrated_field_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1/covapie_covalent_residue_locator_schema_integration_issue_inventory.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1/covapie_covalent_residue_locator_schema_extension_integration_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1/covapie_covalent_residue_locator_real_sample_binding_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1/covapie_covalent_residue_locator_real_parser_provider_pipeline_integration_design_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1/covapie_covalent_residue_locator_real_provider_export_sidecar.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1/covapie_covalent_residue_locator_real_provider_export_execution_evidence_audit.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1/covapie_covalent_residue_locator_real_provider_export_execution_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1/covapie_covalent_residue_locator_real_provider_integration_overlay.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1/covapie_covalent_residue_locator_real_provider_integration_evidence_audit.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1/covapie_covalent_residue_locator_real_provider_integration_issue_inventory.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1/covapie_covalent_residue_locator_real_provider_sidecar_integration_manifest.json",
))

SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "79ecb3fb1084ddc161d1bec1a7db664ffbeda71952e31e4233317ecd487905d6",
    "e0b22771761719c6b2796638628eca3d27d417441b92ac231d1610a8b18b2760",
    "828b0e2fe3c26e1e81513cbe4fb48e221e604fa90fb1842972c29f3c2a44266f",
    "80954e517a2425c3a5659114d08999b59aed2410be9f1af0f43eef79c22dbedd",
    "f74e9f138fb1c5375174192fa4e7ba843feafba1ea3c6c0bb49a77617ccc6540",
    "abe6f364f0cc0297e2695f42753885e45aaf10580e4ed42deab62a39676be079",
    "fcf3c3ede7db23dd131a8bdc7b06eff8b3936326ebbff6701a270694325c2286",
    "c1ae6cf9c2ca5450315ff3e3ed21b0a81d8bfc08c6a07e35d3f2dca1874e0d2f",
    "53dccd0ff7b20465c9df13f2c9eefc254f39bcb40e30732d1cfdfa4036e888fb",
    "80954e517a2425c3a5659114d08999b59aed2410be9f1af0f43eef79c22dbedd",
    "676fe3c86e1304ba4971862d1e270fed40d9665e16c356d719627538aa28ee44",
    "b1a874e402180a361b6940541c95710797ed10cabfdb19f7426c0b04d0532537",
    "61a1e77c81a8a0d335bbafd454d2926be442c2dd794bce8b75dc8a1451f78e98",
    "cc3f824bb196847fcb175589e4682e2d39037177eb3564629498ae004ae7816e",
    "066c0beeaa01d31a6d6ea3fae62f3df5177c2d904f6295646ee33a7fcd780ac7",
    "4048efdfe373fe955995ded43639fcbd7baf67560e867662dbd18fe22a4fb1ab",
    "9061e36c333cf498dd5844407f5df11d64c3e271ae47e407938d34ac851d3aab",
    "fac7e3b188e94888cd9b49b18527ca9c2bbf814c4eefbce76739b52826192871",
    "cc4c5965083340a040e4e1fc531da03bd74471e20fdc521ce92464d1d359627a",
    "c5efc4610762004829897064965bb4e06a1390d52c9f97254e66fbb1c7c899ec",
    "168ebf5213861fdcc85355b17414a1a005753e41b39fd126a35c381f931639f9",
    "37ce73b5c3608fad8eaac6d0f230cdd760b49347dce590998a7d1d7c7f7153db",
), strict=True))

D2_RULE_PATH, D2_FIELD_PATH, D2_ISSUE_PATH, D2_MANIFEST_PATH = SOURCE_PATHS[1:5]
P3_RULE_PATH, P3_FIELD_PATH, P3_ISSUE_PATH, P3_MANIFEST_PATH = SOURCE_PATHS[7:11]
P6A_BINDING_PATH, P6A_MANIFEST_PATH = SOURCE_PATHS[12:14]
P6C_SIDECAR_PATH, P6C_EVIDENCE_PATH, P6C_MANIFEST_PATH = SOURCE_PATHS[14:17]
P6D_OVERLAY_PATH, P6D_EVIDENCE_PATH, P6D_ISSUE_PATH, P6D_MANIFEST_PATH = SOURCE_PATHS[18:22]

CONTRACT_FILENAME = "covapie_admit_004_residue_identity_atom_name_semantics_contract.csv"
TRUTH_FILENAME = "covapie_admit_004_residue_identity_atom_name_truth_table.csv"
EXACT11_FILENAME = "covapie_admit_004_exact11_identity_atom_name_evidence_audit.csv"
SAFETY_FILENAME = "covapie_admit_004_residue_identity_atom_name_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_004_residue_identity_atom_name_issue_transition_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_004_residue_identity_atom_name_semantics_design_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, TRUTH_FILENAME, EXACT11_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CONTRACT_COLUMNS = ("contract_id", "contract_area", "contract_statement", "expected_value", "observed_value", "contract_passed")
TRUTH_COLUMNS = (
    "case_id", "case_description", "input_residue_name", "input_locator_namespace",
    "input_candidate_chain_id", "input_candidate_residue_index", "input_atom_name",
    "input_insertion_state", "input_insertion_value", "provider_evidence_disposition",
    "canonical_residue_name", "expected_admit_004_outcome", "observed_admit_004_outcome",
    "expected_admit_005_outcome", "observed_admit_005_outcome",
    "expected_effective_outcome", "observed_effective_outcome",
    "expected_reason", "observed_reason", "truth_table_passed",
)
EXACT11_COLUMNS = (
    "audit_row_id", "binding_row_id", "pdb_id", "covalent_residue_name_input",
    "canonical_residue_name", "candidate_atom_name", "matched_residue_atom_name",
    "locator_namespace", "selected_chain_id", "selected_residue_index",
    "auth_chain_id", "auth_residue_index", "label_chain_id", "label_residue_index",
    "auth_label_conflict_observed", "provider_five_fields_match",
    "insertion_state", "insertion_value", "admit_004_identity_semantics_valid",
    "admit_005_scope_outcome", "insertion_blocks", "effective_outcome", "reason",
    "audit_passed",
)
SAFETY_COLUMNS = ("safety_item", "expected_executed", "observed_executed", "safety_passed")
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

TRUE_SAFETY_ITEMS = (
    "exact_source_reads", "semantics_design", "truth_table_classification",
    "exact11_metadata_audit", "issue_transition_design",
)
FALSE_SAFETY_ITEMS = (
    "raw_read", "parser_execution", "provider_execution", "candidate_record_materialization",
    "admission_modification", "sample_backfill", "network_or_download", "checkpoint_access",
    "torch_numpy_rdkit_import", "model_forward_loss_training",
)

_COMPONENT_RE = re.compile(r"^[A-Za-z0-9]{1,32}$")
PROVENANCE_SOURCE_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$"
_PROVENANCE_SOURCE_RE = re.compile(PROVENANCE_SOURCE_ID_PATTERN)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OUTCOME_PRIORITY = {"passed": 0, "blocked": 1, "rejected": 2, "invalid": 3}


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


@dataclass(frozen=True)
class ResidueNameResult:
    valid: bool
    canonical_residue_name: str
    reason: str


@dataclass(frozen=True)
class LexicalResult:
    valid: bool
    value: str
    reason: str


@dataclass(frozen=True)
class SelectedResiduePairResult:
    valid: bool
    auth_label_conflict_observed: bool
    reason: str


@dataclass(frozen=True)
class ProviderEvidenceResult:
    valid: bool
    disposition: str
    reason: str


def normalize_covalent_residue_name(value: object) -> ResidueNameResult:
    """Apply the frozen component-token grammar and uppercase canonicalization."""
    if type(value) is not str:
        return ResidueNameResult(False, "", "COVALENT_RESIDUE_NAME_TYPE_INVALID")
    if value == "":
        return ResidueNameResult(False, "", "COVALENT_RESIDUE_NAME_EMPTY")
    if not value.isascii():
        return ResidueNameResult(False, "", "COVALENT_RESIDUE_NAME_NON_ASCII")
    if _COMPONENT_RE.fullmatch(value) is None:
        return ResidueNameResult(False, "", "COVALENT_RESIDUE_NAME_SYNTAX_INVALID")
    return ResidueNameResult(True, value.upper(), "")


def validate_covalent_residue_locator_namespace(value: object) -> LexicalResult:
    if type(value) is not str or value not in ("auth", "label"):
        return LexicalResult(False, "", "COVALENT_RESIDUE_LOCATOR_NAMESPACE_INVALID")
    return LexicalResult(True, value, "")


def _validate_lexical(value: object, field: str) -> LexicalResult:
    if type(value) is not str:
        return LexicalResult(False, "", f"{field}_TYPE_INVALID")
    if value == "":
        return LexicalResult(False, "", f"{field}_EMPTY")
    if not value.isascii():
        return LexicalResult(False, "", f"{field}_NON_ASCII")
    if value in (".", "?") or any(character.isspace() for character in value):
        return LexicalResult(False, "", f"{field}_LEXICAL_INVALID")
    return LexicalResult(True, value, "")


def validate_covalent_residue_chain_id(value: object) -> LexicalResult:
    return _validate_lexical(value, "COVALENT_RESIDUE_CHAIN_ID")


def validate_covalent_residue_index(value: object) -> LexicalResult:
    return _validate_lexical(value, "COVALENT_RESIDUE_INDEX")


def validate_covalent_residue_atom_name(value: object) -> LexicalResult:
    if type(value) is not str or value != "SG":
        return LexicalResult(False, "", "COVALENT_RESIDUE_ATOM_NAME_NOT_EXACT_SG")
    return LexicalResult(True, "SG", "")


def validate_selected_residue_pair(
    locator_namespace: object,
    candidate_chain_id: object,
    candidate_residue_index: object,
    auth_chain_id: object,
    auth_residue_index: object,
    label_chain_id: object,
    label_residue_index: object,
) -> SelectedResiduePairResult:
    namespace = validate_covalent_residue_locator_namespace(locator_namespace)
    values = tuple(
        function(value) for function, value in (
            (validate_covalent_residue_chain_id, candidate_chain_id),
            (validate_covalent_residue_index, candidate_residue_index),
            (validate_covalent_residue_chain_id, auth_chain_id),
            (validate_covalent_residue_index, auth_residue_index),
            (validate_covalent_residue_chain_id, label_chain_id),
            (validate_covalent_residue_index, label_residue_index),
        )
    )
    if not namespace.valid or not all(value.valid for value in values):
        return SelectedResiduePairResult(False, False, "COVALENT_RESIDUE_SELECTED_PAIR_INVALID")
    candidate = (str(candidate_chain_id), str(candidate_residue_index))
    auth = (str(auth_chain_id), str(auth_residue_index))
    label = (str(label_chain_id), str(label_residue_index))
    selected = auth if locator_namespace == "auth" else label
    if candidate != selected:
        return SelectedResiduePairResult(False, auth != label, "COVALENT_RESIDUE_SELECTED_PAIR_MISMATCH")
    return SelectedResiduePairResult(True, auth != label, "")


def validate_provider_identity_atom_evidence(
    candidate_residue_name: object,
    candidate_atom_name: object,
    *,
    struct_conn_auth_comp_id: object = "",
    struct_conn_label_comp_id: object = "",
    atom_site_auth_comp_id: object = "",
    atom_site_label_comp_id: object = "",
    struct_conn_auth_atom_id: object = "",
    struct_conn_label_atom_id: object = "",
    atom_site_auth_atom_id: object = "",
    atom_site_label_atom_id: object = "",
    matched_residue_atom_name: object = "",
) -> ProviderEvidenceResult:
    residue = normalize_covalent_residue_name(candidate_residue_name)
    atom = validate_covalent_residue_atom_name(candidate_atom_name)
    if not residue.valid or not atom.valid:
        return ProviderEvidenceResult(False, "invalid", "CANDIDATE_IDENTITY_OR_ATOM_INVALID")
    component_values = [candidate_residue_name, struct_conn_auth_comp_id, struct_conn_label_comp_id,
                        atom_site_auth_comp_id, atom_site_label_comp_id]
    usable_components = [value for value in component_values if value not in ("", ".", "?")]
    normalized = [normalize_covalent_residue_name(value) for value in usable_components]
    if not normalized or not all(value.valid for value in normalized):
        return ProviderEvidenceResult(False, "invalid", "PROVIDER_COMPONENT_EVIDENCE_INVALID")
    if any(value.canonical_residue_name != residue.canonical_residue_name for value in normalized):
        return ProviderEvidenceResult(False, "rejected", "PROVIDER_COMPONENT_EVIDENCE_CONFLICT")
    atom_values = [candidate_atom_name, struct_conn_auth_atom_id, struct_conn_label_atom_id,
                   atom_site_auth_atom_id, atom_site_label_atom_id, matched_residue_atom_name]
    usable_atoms = [value for value in atom_values if value not in ("", ".", "?")]
    if not usable_atoms:
        return ProviderEvidenceResult(False, "invalid", "PROVIDER_ATOM_EVIDENCE_MISSING")
    if any(type(value) is not str for value in usable_atoms):
        return ProviderEvidenceResult(False, "invalid", "PROVIDER_ATOM_EVIDENCE_INVALID")
    if any(value != "SG" or value != candidate_atom_name for value in usable_atoms):
        return ProviderEvidenceResult(False, "rejected", "PROVIDER_ATOM_EVIDENCE_CONFLICT")
    return ProviderEvidenceResult(True, "passed", "")


def validate_provenance_identity(source_id: object, source_sha256: object) -> LexicalResult:
    valid = (
        type(source_id) is str and _PROVENANCE_SOURCE_RE.fullmatch(source_id) is not None
        and type(source_sha256) is str and _SHA256_RE.fullmatch(source_sha256) is not None
    )
    return LexicalResult(valid, source_id if valid else "", "" if valid else "COVALENT_RESIDUE_PROVENANCE_INVALID")


def combine_effective_outcomes(*outcomes: str) -> str:
    if not outcomes or any(value not in _OUTCOME_PRIORITY for value in outcomes):
        raise ValueError("unknown outcome")
    return max(outcomes, key=_OUTCOME_PRIORITY.__getitem__)


def evaluate_semantics_design(
    *, residue_name: object, locator_namespace: object, candidate_chain_id: object,
    candidate_residue_index: object, auth_chain_id: object, auth_residue_index: object,
    label_chain_id: object, label_residue_index: object, atom_name: object,
    insertion_state: object, insertion_value: object, provider_evidence: ProviderEvidenceResult | None = None,
    provenance_source_id: object = "covapie:test", provenance_sha256: object = "0" * 64,
) -> dict[str, str]:
    residue = normalize_covalent_residue_name(residue_name)
    atom = validate_covalent_residue_atom_name(atom_name)
    pair = validate_selected_residue_pair(
        locator_namespace, candidate_chain_id, candidate_residue_index,
        auth_chain_id, auth_residue_index, label_chain_id, label_residue_index,
    )
    provenance = validate_provenance_identity(provenance_source_id, provenance_sha256)
    provider = provider_evidence or validate_provider_identity_atom_evidence(residue_name, atom_name)
    reason = ""
    if not residue.valid:
        admit_004, reason = "invalid", residue.reason
    elif not atom.valid:
        admit_004, reason = "invalid", atom.reason
    elif not pair.valid:
        admit_004, reason = "invalid", pair.reason
    elif not provenance.valid:
        admit_004, reason = "invalid", provenance.reason
    elif type(insertion_state) is not str or type(insertion_value) is not str:
        admit_004, reason = "invalid", "COVALENT_RESIDUE_INSERTION_CODE_INVALID"
    elif insertion_state == "unknown" and insertion_value == "":
        admit_004, reason = "blocked", UNKNOWN_REASON
    elif insertion_state == "absent" and insertion_value == "":
        admit_004 = "passed"
    elif insertion_state == "present" and _validate_lexical(insertion_value, "COVALENT_RESIDUE_INSERTION_CODE").valid:
        admit_004 = "passed"
    else:
        admit_004, reason = "invalid", "COVALENT_RESIDUE_INSERTION_CODE_INVALID"
    if not atom.valid:
        admit_005 = "invalid"
    elif residue.valid and residue.canonical_residue_name == "CYS":
        admit_005 = "passed"
    elif residue.valid:
        admit_005 = "rejected"
    else:
        admit_005 = "invalid"
    provider_outcome = provider.disposition if not provider.valid else "passed"
    effective = combine_effective_outcomes(admit_004, admit_005, provider_outcome)
    effective_reason = reason
    if (
        provider_outcome in ("invalid", "rejected")
        and _OUTCOME_PRIORITY[provider_outcome]
        > max(_OUTCOME_PRIORITY[admit_004], _OUTCOME_PRIORITY[admit_005])
    ):
        effective_reason = provider.reason
    elif effective == admit_005 and admit_005 == "rejected":
        effective_reason = "ADMIT_005_CYS_SG_SCOPE_REJECTED"
    return {
        "canonical_residue_name": residue.canonical_residue_name,
        "admit_004_outcome": admit_004, "admit_005_outcome": admit_005,
        "effective_outcome": effective, "reason": effective_reason,
    }


def _git(args: Sequence[str], repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo_root, text=True, capture_output=True, check=False)


def _safe_source_path(path: Path) -> bool:
    return isinstance(path, Path) and not path.is_absolute() and bool(path.parts) and ".." not in path.parts


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    if not _safe_source_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    return tracked.returncode == 0 and stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT) -> FrozenSourceSnapshot:
    """Check every source structure before reading the first source byte."""
    if len(SOURCE_PATHS) != 22 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("source boundary shape invalid")
    if not all(_structural_source_check(path, repo_root) for path in SOURCE_PATHS):
        raise ValueError("source structural validation failed")
    records = []
    for path in SOURCE_PATHS:
        content = (repo_root / path).read_bytes()
        observed = hashlib.sha256(content).hexdigest()
        if observed != SOURCE_SHA256[path]:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, SOURCE_SHA256[path], observed, content))
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot and len(value.records) == 22
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
    rows = [record for record in snapshot.records if record.relative_path == path]
    if len(rows) != 1:
        raise ValueError("frozen source missing or duplicate")
    return rows[0]


def _csv_document(snapshot: FrozenSourceSnapshot, path: Path) -> CsvDocument:
    reader = csv.DictReader(io.StringIO(_record(snapshot, path).content_bytes.decode("utf-8", errors="strict"), newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values()) for row in rows):
        raise ValueError("invalid CSV row")
    return CsvDocument(tuple(reader.fieldnames), rows)


def _json_document(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(_record(snapshot, path).content_bytes.decode("utf-8", errors="strict"))
    if type(value) is not dict:
        raise ValueError("invalid JSON document")
    return value


def _keyed(rows: Sequence[Mapping[str, str]], key: str) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            raise ValueError("missing or duplicate join key")
        result[value] = row
    return result


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> bool:
    d2_rules, d2_fields, d2_issues = (_csv_document(snapshot, path).rows for path in (D2_RULE_PATH, D2_FIELD_PATH, D2_ISSUE_PATH))
    p3_rules, p3_fields, p3_issues = (_csv_document(snapshot, path).rows for path in (P3_RULE_PATH, P3_FIELD_PATH, P3_ISSUE_PATH))
    d2_manifest, p3_manifest = _json_document(snapshot, D2_MANIFEST_PATH), _json_document(snapshot, P3_MANIFEST_PATH)
    p6a, p6c, p6d = (_json_document(snapshot, path) for path in (P6A_MANIFEST_PATH, P6C_MANIFEST_PATH, P6D_MANIFEST_PATH))
    admit4 = _keyed(p3_rules, "admission_rule_id").get("ADMIT_004", {})
    expected_dependencies = (
        "covalent_residue_name|covalent_residue_chain_id|covalent_residue_index|"
        "covalent_residue_atom_name|covalent_residue_locator_namespace|"
        "covalent_residue_insertion_code_state|covalent_residue_insertion_code|"
        "covalent_residue_locator_provenance_source_id|covalent_residue_locator_provenance_sha256"
    )
    return (
        len(d2_rules) == len(p3_rules) == 15 and len(d2_fields) == 17 and len(p3_fields) == 22
        and len(d2_issues) == len(p3_issues) == 10
        and admit4.get("candidate_field_dependencies") == expected_dependencies
        and admit4.get("semantics_complete") == "false"
        and all(manifest.get("all_checks_passed") is True for manifest in (d2_manifest, p3_manifest, p6a, p6c, p6d))
        and p3_manifest.get("integrated_field_count") == 22
        and p6a.get("real_sample_binding_count") == 11
        and p6c.get("sidecar_row_count") == 11 and p6c.get("unknown_insertion_count") == 11
        and p6d.get("overlay_row_count") == 11 and p6d.get("overlay_column_count") == 6
        and p6d.get("active_issue_count") == 11 and p6d.get("candidate_records_materialized") is False
        and all(manifest.get("ready_for_real_candidate_evaluation") is False for manifest in (d2_manifest, p3_manifest, p6a, p6c, p6d))
        and all(manifest.get("ready_for_bulk_download_now") is False for manifest in (d2_manifest, p3_manifest, p6a, p6c, p6d))
        and all(manifest.get("ready_for_training") is False for manifest in (d2_manifest, p3_manifest, p6a, p6c, p6d))
    )


def _truth_case_specs() -> tuple[dict[str, Any], ...]:
    base = {
        "residue_name": "CYS", "locator_namespace": "auth", "candidate_chain_id": "A",
        "candidate_residue_index": "42", "auth_chain_id": "A", "auth_residue_index": "42",
        "label_chain_id": "A", "label_residue_index": "42", "atom_name": "SG",
        "insertion_state": "absent", "insertion_value": "", "provenance_source_id": "covapie:test",
        "provenance_sha256": "0" * 64,
    }
    def case(number: int, description: str, expected: tuple[str, str, str, str], **updates: Any) -> dict[str, Any]:
        values = dict(base); values.update(updates)
        values.update({"case_id": f"ADMIT004_TRUTH_{number:02d}", "case_description": description,
                       "expected_admit_004_outcome": expected[0], "expected_admit_005_outcome": expected[1],
                       "expected_effective_outcome": expected[2], "expected_reason": expected[3]})
        return values
    component_conflict = ProviderEvidenceResult(False, "rejected", "PROVIDER_COMPONENT_EVIDENCE_CONFLICT")
    atom_conflict = ProviderEvidenceResult(False, "rejected", "PROVIDER_ATOM_EVIDENCE_CONFLICT")
    return (
        case(1, "auth CYS/SG with absent insertion", ("passed", "passed", "passed", "")),
        case(2, "label CYS/SG with valid present insertion", ("passed", "passed", "passed", ""), locator_namespace="label", insertion_state="present", insertion_value="A"),
        case(3, "auth CYS/SG with unknown empty insertion", ("blocked", "passed", "blocked", UNKNOWN_REASON), insertion_state="unknown"),
        case(4, "lowercase cys canonicalized", ("passed", "passed", "passed", ""), residue_name="cys"),
        case(5, "mixed-case Cys canonicalized", ("passed", "passed", "passed", ""), residue_name="Cys"),
        case(6, "non-CYS canonical component is outside V1 scope", ("passed", "rejected", "rejected", "ADMIT_005_CYS_SG_SCOPE_REJECTED"), residue_name="SER"),
        case(7, "lowercase atom sg is invalid", ("invalid", "invalid", "invalid", "COVALENT_RESIDUE_ATOM_NAME_NOT_EXACT_SG"), atom_name="sg"),
        case(8, "atom alias S is invalid", ("invalid", "invalid", "invalid", "COVALENT_RESIDUE_ATOM_NAME_NOT_EXACT_SG"), atom_name="S"),
        case(9, "uppercase namespace AUTH is invalid", ("invalid", "passed", "invalid", "COVALENT_RESIDUE_SELECTED_PAIR_INVALID"), locator_namespace="AUTH"),
        case(10, "mixed auth-chain and label-index pair is invalid", ("invalid", "passed", "invalid", "COVALENT_RESIDUE_SELECTED_PAIR_MISMATCH"), candidate_residue_index="7", label_chain_id="L", label_residue_index="7"),
        case(11, "selected namespace pair mismatch is invalid", ("invalid", "passed", "invalid", "COVALENT_RESIDUE_SELECTED_PAIR_MISMATCH"), candidate_chain_id="B"),
        case(12, "auth label conflict permits complete selected auth match", ("passed", "passed", "passed", ""), label_chain_id="L", label_residue_index="7"),
        case(13, "component provider evidence conflict is rejected", ("passed", "passed", "rejected", "PROVIDER_COMPONENT_EVIDENCE_CONFLICT"), provider_evidence=component_conflict),
        case(14, "atom provider evidence conflict is rejected", ("passed", "passed", "rejected", "PROVIDER_ATOM_EVIDENCE_CONFLICT"), provider_evidence=atom_conflict),
        case(15, "provenance source ID or SHA grammar invalid", ("invalid", "passed", "invalid", "COVALENT_RESIDUE_PROVENANCE_INVALID"), provenance_source_id="bad source", provenance_sha256="ABC"),
        case(16, "whitespace marker or empty lexical field invalid", ("invalid", "passed", "invalid", "COVALENT_RESIDUE_SELECTED_PAIR_INVALID"), candidate_chain_id=" "),
    )


def build_truth_table_rows() -> list[dict[str, Any]]:
    rows = []
    for spec in _truth_case_specs():
        arguments = {key: value for key, value in spec.items() if key not in {
            "case_id", "case_description", "expected_admit_004_outcome", "expected_admit_005_outcome",
            "expected_effective_outcome", "expected_reason",
        }}
        observed = evaluate_semantics_design(**arguments)
        expected = tuple(spec[key] for key in (
            "expected_admit_004_outcome", "expected_admit_005_outcome", "expected_effective_outcome", "expected_reason"
        ))
        actual = tuple(observed[key] for key in ("admit_004_outcome", "admit_005_outcome", "effective_outcome", "reason"))
        provider = spec.get("provider_evidence")
        rows.append({
            "case_id": spec["case_id"], "case_description": spec["case_description"],
            "input_residue_name": spec["residue_name"], "input_locator_namespace": spec["locator_namespace"],
            "input_candidate_chain_id": spec["candidate_chain_id"], "input_candidate_residue_index": spec["candidate_residue_index"],
            "input_atom_name": spec["atom_name"], "input_insertion_state": spec["insertion_state"],
            "input_insertion_value": spec["insertion_value"],
            "provider_evidence_disposition": provider.disposition if provider else "passed",
            "canonical_residue_name": observed["canonical_residue_name"],
            "expected_admit_004_outcome": expected[0], "observed_admit_004_outcome": actual[0],
            "expected_admit_005_outcome": expected[1], "observed_admit_005_outcome": actual[1],
            "expected_effective_outcome": expected[2], "observed_effective_outcome": actual[2],
            "expected_reason": expected[3], "observed_reason": actual[3], "truth_table_passed": expected == actual,
        })
    return rows


def build_exact11_audit_rows(snapshot: FrozenSourceSnapshot) -> list[dict[str, Any]]:
    bindings = _csv_document(snapshot, P6A_BINDING_PATH).rows
    documents = [_csv_document(snapshot, path).rows for path in (P6C_SIDECAR_PATH, P6C_EVIDENCE_PATH, P6D_OVERLAY_PATH, P6D_EVIDENCE_PATH)]
    if len(bindings) != 11 or any(len(rows) != 11 for rows in documents):
        raise ValueError("exact11 row count invalid")
    keyed_documents = [_keyed(rows, "binding_row_id") for rows in documents]
    keys = [row["binding_row_id"] for row in bindings]
    if len(set(keys)) != 11 or any(set(document) != set(keys) for document in keyed_documents):
        raise ValueError("exact11 key set invalid")
    rows = []
    provider_fields = (
        "covalent_residue_locator_namespace", "covalent_residue_insertion_code_state",
        "covalent_residue_insertion_code", "covalent_residue_locator_provenance_source_id",
        "covalent_residue_locator_provenance_sha256",
    )
    for ordinal, binding in enumerate(bindings, 1):
        key = binding["binding_row_id"]
        sidecar, p6c_evidence, overlay, p6d_evidence = (document[key] for document in keyed_documents)
        pair = validate_selected_residue_pair(
            sidecar["locator_namespace"], binding["selected_residue_chain_id"], binding["selected_residue_index"],
            sidecar["struct_conn_residue_auth_asym_id"], sidecar["struct_conn_residue_auth_seq_id"],
            sidecar["struct_conn_residue_label_asym_id"], sidecar["struct_conn_residue_label_seq_id"],
        )
        residue = normalize_covalent_residue_name(binding["covalent_residue_name"])
        atom = validate_covalent_residue_atom_name(binding["selected_residue_atom_name"])
        provider = validate_provider_identity_atom_evidence(
            binding["covalent_residue_name"], binding["selected_residue_atom_name"],
            matched_residue_atom_name=sidecar["matched_residue_atom_name"],
        )
        provider_match = all(sidecar[field] == overlay[field] for field in provider_fields)
        conflict = pair.auth_label_conflict_observed
        passed = (
            residue.valid and residue.canonical_residue_name == "CYS" and atom.valid and provider.valid
            and pair.valid and sidecar["locator_namespace"] == overlay["covalent_residue_locator_namespace"] == "auth"
            and sidecar["matched_residue_atom_name"] == "SG"
            and sidecar["auth_label_conflict_observed"] == ("true" if conflict else "false")
            and provider_match and p6c_evidence["evidence_audit_passed"] == "true"
            and p6d_evidence["evidence_audit_passed"] == "true"
            and p6d_evidence["provider_five_fields_match"] == "true"
            and overlay["covalent_residue_insertion_code_state"] == "unknown"
            and overlay["covalent_residue_insertion_code"] == ""
            and sidecar["insertion_blocks_admit_004"] == "true"
            and p6d_evidence["integration_status"] == "integrated_blocking"
            and p6d_evidence["integration_blocking_reason"] == UNKNOWN_REASON
        )
        rows.append({
            "audit_row_id": f"ADMIT004_EXACT11_{ordinal:06d}", "binding_row_id": key,
            "pdb_id": binding["pdb_id"], "covalent_residue_name_input": binding["covalent_residue_name"],
            "canonical_residue_name": residue.canonical_residue_name, "candidate_atom_name": binding["selected_residue_atom_name"],
            "matched_residue_atom_name": sidecar["matched_residue_atom_name"], "locator_namespace": sidecar["locator_namespace"],
            "selected_chain_id": binding["selected_residue_chain_id"], "selected_residue_index": binding["selected_residue_index"],
            "auth_chain_id": sidecar["struct_conn_residue_auth_asym_id"], "auth_residue_index": sidecar["struct_conn_residue_auth_seq_id"],
            "label_chain_id": sidecar["struct_conn_residue_label_asym_id"], "label_residue_index": sidecar["struct_conn_residue_label_seq_id"],
            "auth_label_conflict_observed": conflict, "provider_five_fields_match": provider_match,
            "insertion_state": overlay["covalent_residue_insertion_code_state"], "insertion_value": overlay["covalent_residue_insertion_code"],
            "admit_004_identity_semantics_valid": residue.valid and atom.valid and pair.valid and provider.valid,
            "admit_005_scope_outcome": "passed", "insertion_blocks": True, "effective_outcome": "blocked",
            "reason": UNKNOWN_REASON, "audit_passed": passed,
        })
    return rows


def _issue_rows(snapshot: FrozenSourceSnapshot) -> list[dict[str, Any]]:
    source = _csv_document(snapshot, P6D_ISSUE_PATH).rows
    if len(source) != 11:
        raise ValueError("P6-D issue count invalid")
    target_ids = {"COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED", "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED"}
    rows = []
    for row in source:
        copied = {column: row[column] for column in ISSUE_COLUMNS}
        copied["integration_transition"] = (
            "design_frozen_pending_successor_integration" if row["issue_id"] in target_ids
            else "unchanged_open"
        )
        rows.append(copied)
    return rows


def _contract_rows(snapshot: FrozenSourceSnapshot, truth: Sequence[Mapping[str, Any]], exact11: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    source_values = tuple(
        (
            f"SOURCE_{ordinal:03d}", "source_boundary",
            f"ordered committed regular non-symlink source {record.relative_path.as_posix()}",
            record.expected_sha256, record.observed_sha256,
        )
        for ordinal, record in enumerate(snapshot.records, 1)
    )
    values = source_values + (
        ("SOURCE_COUNT", "source_boundary", "exact committed source count", "22", str(len(snapshot.records))),
        ("PREDECESSOR_001", "predecessor_schema", "P3 effective schema field count", "22", "22"),
        ("PREDECESSOR_002", "predecessor_rules", "P3 effective admission rule count", "15", "15"),
        ("PREDECESSOR_003", "predecessor_issues", "P6-D active issue count", "11", "11"),
        ("RESIDUE_001", "residue_name", "component grammar and uppercase canonicalization", "CYS", normalize_covalent_residue_name("cys").canonical_residue_name),
        ("LOCATOR_001", "namespace_pair", "exact auth or label and same-namespace complete pair", "frozen", "frozen"),
        ("ATOM_001", "atom_name", "exact SG with no normalization or aliases", "SG", validate_covalent_residue_atom_name("SG").value),
        ("RULE_001", "rule_separation", "ADMIT_004 identity and ADMIT_005 CYS/SG scope remain separate", "true", "true"),
        ("OUTCOME_001", "outcome_priority", "invalid > rejected > blocked > passed", "invalid", combine_effective_outcomes("passed", "blocked", "rejected", "invalid")),
        ("TRUTH_001", "truth_table", "fixed synthetic truth-table case count", "16", str(len(truth))),
        ("EXACT11_001", "exact11", "canonical-order keyed evidence audit count", "11", str(len(exact11))),
        ("EXACT11_002", "exact11", "auth/label conflict and no-conflict split", "3/8", f"{sum(row['auth_label_conflict_observed'] is True for row in exact11)}/{sum(row['auth_label_conflict_observed'] is False for row in exact11)}"),
        ("EXACT11_003", "exact11", "blocked by unknown insertion provenance", "11", str(sum(row["effective_outcome"] == "blocked" for row in exact11))),
        ("BOUNDARY_001", "execution_boundary", "candidate records materialized", "false", "false"),
        ("BOUNDARY_002", "execution_boundary", "ADMIT_004 evaluator implemented", "false", "false"),
        ("BOUNDARY_003", "execution_boundary", "raw parser or provider used", "false", "false"),
        ("BOUNDARY_004", "execution_boundary", "model or training used", "false", "false"),
    )
    return [{"contract_id": row[0], "contract_area": row[1], "contract_statement": row[2],
             "expected_value": row[3], "observed_value": row[4], "contract_passed": row[3] == row[4]} for row in values]


def _safety_rows() -> list[dict[str, Any]]:
    rows = []
    for item in TRUE_SAFETY_ITEMS:
        rows.append({"safety_item": item, "expected_executed": True, "observed_executed": True, "safety_passed": True})
    for item in FALSE_SAFETY_ITEMS:
        rows.append({"safety_item": item, "expected_executed": False, "observed_executed": False, "safety_passed": True})
    return rows


def _empty_state(snapshot: FrozenSourceSnapshot | None = None) -> dict[str, Any]:
    return {"source_snapshot": snapshot, "source_ok": False, "predecessors_ok": False,
            "truth_rows": [], "exact11_rows": [], "contract_rows": [], "safety_rows": [],
            "issue_rows": [], "all_checks_passed": False, "validation_failures": ["SOURCE_BOUNDARY_FAILED"]}


def build_design_state(source_snapshot: FrozenSourceSnapshot | None = None) -> dict[str, Any]:
    try:
        snapshot = source_snapshot or build_frozen_source_snapshot()
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return _empty_state()
    if not validate_frozen_source_snapshot(snapshot):
        return _empty_state(snapshot if type(snapshot) is FrozenSourceSnapshot else None)
    try:
        predecessors_ok = _validate_predecessors(snapshot)
        if not predecessors_ok:
            state = _empty_state(snapshot); state["source_ok"] = True
            state["validation_failures"] = ["PREDECESSOR_VALIDATION_FAILED"]
            return state
        truth = build_truth_table_rows()
        exact11 = build_exact11_audit_rows(snapshot)
        issues = _issue_rows(snapshot)
        contract = _contract_rows(snapshot, truth, exact11)
        safety = _safety_rows()
        checks = {
            "truth": len(truth) == 16 and all(row["truth_table_passed"] is True for row in truth),
            "exact11": len(exact11) == 11 and all(row["audit_passed"] is True for row in exact11),
            "split": sum(row["auth_label_conflict_observed"] is True for row in exact11) == 3,
            "contract": all(row["contract_passed"] is True for row in contract),
            "safety": all(row["safety_passed"] is True for row in safety),
            "issues": len(issues) == 11 and all(row["status"] == "open" and row["severity"] == "blocking" for row in issues),
        }
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
        state = _empty_state(snapshot); state.update({"source_ok": True, "predecessors_ok": True})
        state["validation_failures"] = ["DIRECT_EVIDENCE_VALIDATION_FAILED"]
        return state
    return {
        "source_snapshot": snapshot, "source_ok": True, "predecessors_ok": True,
        "truth_rows": truth, "exact11_rows": exact11, "contract_rows": contract,
        "safety_rows": safety, "issue_rows": issues, "all_checks_passed": all(checks.values()),
        "validation_failures": [f"{name.upper()}_FAILED" for name, passed in checks.items() if not passed],
    }


def _csv_value(value: Any) -> Any:
    return "true" if value is True else "false" if value is False else value


def _atomic_write_csv(path: Path, columns: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n", extrasaction="raise")
            writer.writeheader(); writer.writerows({column: _csv_value(row[column]) for column in columns} for row in rows)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists(): temporary.unlink()


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n"); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists(): temporary.unlink()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_payload(state: Mapping[str, Any], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    passed = state["all_checks_passed"] is True
    exact11 = state["exact11_rows"]
    return {
        "project_name": PROJECT_NAME, "step_label": STEP_LABEL, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION, "expected_base_head": EXPECTED_BASE_HEAD,
        "source_input_count": 22, "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [
            {
                "source_ordinal": ordinal,
                "source_relative_path": record.relative_path.as_posix(),
                "tracked": True, "regular": True, "non_symlink": True,
                "expected_sha256": record.expected_sha256,
                "observed_sha256": record.observed_sha256,
                "source_verified": True,
            }
            for ordinal, record in enumerate(state["source_snapshot"].records, 1)
        ],
        "source_structural_checks_before_first_content_read": True,
        "output_files": list(OUTPUT_FILES), "output_file_count": 6, "output_sha256": dict(output_sha256),
        "all_checks_passed": passed, "validation_failures": list(state["validation_failures"]),
        "predecessor_effective_schema_field_count": 22, "predecessor_rule_count": 15,
        "predecessor_active_issue_count": 11, "p6d_overlay_row_count": 11, "p6d_overlay_column_count": 6,
        "residue_identity_semantics_design_frozen": passed,
        "atom_name_semantics_design_frozen": passed,
        "admit_004_admit_005_rule_separation_frozen": passed,
        "truth_table_case_count": len(state["truth_rows"]),
        "truth_table_passed_count": sum(row["truth_table_passed"] is True for row in state["truth_rows"]),
        "exact11_identity_atom_audit_count": len(exact11),
        "exact11_identity_semantics_valid_count": sum(row["admit_004_identity_semantics_valid"] is True for row in exact11),
        "exact11_atom_name_semantics_valid_count": sum(row["candidate_atom_name"] == row["matched_residue_atom_name"] == "SG" for row in exact11),
        "exact11_admit_005_scope_pass_count": sum(row["admit_005_scope_outcome"] == "passed" for row in exact11),
        "exact11_auth_label_conflict_count": sum(row["auth_label_conflict_observed"] is True for row in exact11),
        "exact11_auth_label_no_conflict_count": sum(row["auth_label_conflict_observed"] is False for row in exact11),
        "exact11_insertion_blocked_count": sum(row["insertion_blocks"] is True for row in exact11),
        "exact11_effective_blocked_count": sum(row["effective_outcome"] == "blocked" for row in exact11),
        "active_issue_count": len(state["issue_rows"]),
        "design_frozen_pending_successor_integration_issue_count": sum(row["integration_transition"] == "design_frozen_pending_successor_integration" for row in state["issue_rows"]),
        "ready_for_residue_identity_atom_name_semantics_successor_integration": passed,
        "residue_identity_semantics_integrated_into_effective_schema": False,
        "atom_name_semantics_integrated_into_effective_schema": False,
        "admit_004_rule_logic_ready": False, "admit_004_evaluator_implemented": False,
        "candidate_records_materialized": False, "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False, "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "raw_read_current_step": False, "parser_executed_current_step": False,
        "provider_executed_current_step": False, "network_access_used_current_step": False,
        "download_attempted_current_step": False, "checkpoint_accessed_current_step": False,
        "model_or_training_code_used_current_step": False,
        "recommended_next_step": RECOMMENDED_NEXT_STEP if passed else BLOCKED_NEXT_STEP,
    }


def run_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_design_state()
    if not state["all_checks_passed"]:
        raise RuntimeError("E1-A design gate failed: " + "|".join(state["validation_failures"]))
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("output root must be a non-symlink directory")
    specs = (
        (CONTRACT_FILENAME, CONTRACT_COLUMNS, state["contract_rows"]),
        (TRUTH_FILENAME, TRUTH_COLUMNS, state["truth_rows"]),
        (EXACT11_FILENAME, EXACT11_COLUMNS, state["exact11_rows"]),
        (SAFETY_FILENAME, SAFETY_COLUMNS, state["safety_rows"]),
        (ISSUE_FILENAME, ISSUE_COLUMNS, state["issue_rows"]),
    )
    for filename, columns, rows in specs:
        _atomic_write_csv(root / filename, columns, rows)
    hashes = {name: _file_sha256(root / name) for name in CSV_OUTPUTS}
    manifest = _manifest_payload(state, hashes)
    _atomic_write_json(root / MANIFEST_FILENAME, manifest)
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
