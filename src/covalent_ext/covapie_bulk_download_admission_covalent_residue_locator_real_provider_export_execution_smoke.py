"""CovaPIE Step14AU-E0-P6-C real provider export execution smoke v1.

This additive executor validates the committed P6-B predecessor before opening
only the eleven bound raw paths.  Each raw file is read once through a no-follow
descriptor walk; the same retained bytes are hashed, strictly decoded, parsed,
and supplied to the frozen P4 provider mapping.  Raw content is never written.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import io
import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, Callable, Mapping, Sequence


STEP_LABEL = "Step14AU-E0-P6-C"
STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_real_provider_"
    "export_execution_smoke_v1"
)
PREVIOUS_STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_"
    "precondition_gate_v1"
)
PROJECT_NAME = "CovaPIE"
MANIFEST_SCHEMA_VERSION = (
    "covapie_covalent_residue_locator_real_provider_export_execution_smoke_"
    "v1_manifest_v1"
)
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_covalent_residue_locator_real_provider_sidecar_"
    "integration_gate_v1"
)
BLOCKED_NEXT_STEP = (
    "resolve_covapie_covalent_residue_locator_real_provider_export_execution_"
    "smoke_v1_blockers"
)
REPO_ROOT = Path(__file__).resolve().parents[2]

P4_MODULE_PATH = Path(
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_"
    "parser_provider_provenance_export_design_gate.py"
)
P5B_MODULE_PATH = Path(
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_"
    "parser_provider_provenance_export_smoke.py"
)
P6A_MODULE_PATH = Path(
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_"
    "real_parser_provider_pipeline_integration_design_gate.py"
)
P6A_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_real_parser_provider_pipeline_integration_design_gate_v1"
)
P6A_BINDING_PATH = P6A_ROOT / "covapie_covalent_residue_locator_real_sample_binding_matrix.csv"
P6B_MODULE_PATH = Path(
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_"
    "real_raw_source_precondition_gate.py"
)
P6B_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_real_raw_source_precondition_gate_v1"
)
P6B_CONTRACT_PATH = P6B_ROOT / "covapie_covalent_residue_locator_real_raw_source_precondition_contract.csv"
P6B_MATRIX_PATH = P6B_ROOT / "covapie_covalent_residue_locator_real_raw_source_precondition_matrix.csv"
P6B_AUTHORITY_PATH = P6B_ROOT / "covapie_covalent_residue_locator_real_raw_source_authority_audit.csv"
P6B_SAFETY_PATH = P6B_ROOT / "covapie_covalent_residue_locator_real_raw_source_safety_audit.csv"
P6B_ISSUE_PATH = P6B_ROOT / "covapie_covalent_residue_locator_real_raw_source_issue_inventory.csv"
P6B_MANIFEST_PATH = P6B_ROOT / "covapie_covalent_residue_locator_real_raw_source_precondition_manifest.json"

P4_RUNTIME_MODULE_NAME = (
    "covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_"
    "parser_provider_provenance_export_design_gate"
)
P5B_RUNTIME_MODULE_NAME = (
    "covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_"
    "parser_provider_provenance_export_smoke"
)
FORBIDDEN_RUNTIME_MODULE_NAMES = (
    "covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_"
    "real_parser_provider_pipeline_integration_design_gate",
    "covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_"
    "real_raw_source_precondition_gate",
)

SOURCE_PATHS = (
    P4_MODULE_PATH,
    P5B_MODULE_PATH,
    P6A_MODULE_PATH,
    P6A_BINDING_PATH,
    P6B_MODULE_PATH,
    P6B_CONTRACT_PATH,
    P6B_MATRIX_PATH,
    P6B_AUTHORITY_PATH,
    P6B_SAFETY_PATH,
    P6B_ISSUE_PATH,
    P6B_MANIFEST_PATH,
)
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "b1a874e402180a361b6940541c95710797ed10cabfdb19f7426c0b04d0532537",
    "21be5237736a55fe87da9763c939a228bb81c52b2481602c9bcb4dd425b338bd",
    "7d43c30f87b3e4c8a44d27b63ec51ba63307dcf23c16571be1d562d0b737c650",
    "61a1e77c81a8a0d335bbafd454d2926be442c2dd794bce8b75dc8a1451f78e98",
    "bb5264affc9545189b616c549370522ea9b8628bd9b8a18dbb9edb69d17d5a19",
    "6386463c17df0041c9fe4dea248c74095d4534babec17ce6c088d6cb13286b37",
    "ddebe9fd671400bb3508408ba0f5e38b13c83cc1e125f37bc98ac572daa2ed0d",
    "53cf7fd4b8fc47bab67cfb443891c4b0e8f1464d8bf324edb686ba7b64c710be",
    "d5d1cec05d154b85f4bd597f7a06d86c901f66193a8083566644a1c60e02ac29",
    "4164ac59a2d3a16a0ee9de7996ea02b3d6cb52b563c51dfb80e9ca7f4515299e",
    "64c87a64002dc6dcc773a1540e54f54574265d8e6a080e1b2c2024292602a3f4",
)))

DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
CONTRACT_FILENAME = "covapie_covalent_residue_locator_real_provider_export_execution_contract.csv"
SIDECAR_FILENAME = "covapie_covalent_residue_locator_real_provider_export_sidecar.csv"
EVIDENCE_FILENAME = "covapie_covalent_residue_locator_real_provider_export_execution_evidence_audit.csv"
SAFETY_FILENAME = "covapie_covalent_residue_locator_real_provider_export_safety_audit.csv"
ISSUE_FILENAME = "covapie_covalent_residue_locator_real_provider_export_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_covalent_residue_locator_real_provider_export_execution_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, SIDECAR_FILENAME, EVIDENCE_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

P6B_OUTPUT_FILES = (
    "covapie_covalent_residue_locator_real_raw_source_precondition_contract.csv",
    "covapie_covalent_residue_locator_real_raw_source_precondition_matrix.csv",
    "covapie_covalent_residue_locator_real_raw_source_authority_audit.csv",
    "covapie_covalent_residue_locator_real_raw_source_safety_audit.csv",
    "covapie_covalent_residue_locator_real_raw_source_issue_inventory.csv",
    "covapie_covalent_residue_locator_real_raw_source_precondition_manifest.json",
)

P6A_BINDING_COLUMNS = (
    "binding_row_id", "source_pipeline", "sample_preparation_input_id",
    "sample_execution_id", "pdb_id", "ligand_comp_id", "conn_id",
    "covalent_residue_name", "selected_residue_chain_id",
    "selected_residue_index", "selected_residue_atom_name",
    "raw_target_relative_path", "sample_artifact_root",
    "covalent_event_table_relative_path",
    "ligand_residue_atom_pair_table_relative_path", "metadata_join_status",
    "raw_path_persisted", "conn_id_persisted",
    "residue_locator_hint_persisted", "partner_side_requires_raw_reparse",
    "namespace_evidence_requires_raw_reparse",
    "insertion_evidence_requires_raw_reparse",
    "matched_atom_site_row_requires_raw_reparse",
    "real_export_execution_allowed_current_step", "binding_status",
    "blocking_reason",
)
P6B_MATRIX_COLUMNS = (
    "precondition_row_id", "binding_row_id", "source_pipeline",
    "sample_preparation_input_id", "pdb_id", "ligand_comp_id",
    "raw_target_relative_path", "authority_scope",
    "expected_authority_source_relative_path", "expected_authority_row_id",
    "authority_join_status", "expected_sha256", "expected_file_size_bytes",
    "observed_sha256", "observed_file_size_bytes", "sha256_matches",
    "file_size_matches", "raw_path_exists", "raw_path_regular_file",
    "raw_path_symlink", "raw_path_confined_without_symlink",
    "raw_path_unique", "raw_git_tracking_state", "raw_git_worktree_clean",
    "raw_git_index_clean", "pre_hash_stat_fingerprint",
    "post_hash_stat_fingerprint", "stat_stable",
    "raw_source_precondition_status",
    "ready_for_real_provider_export_execution_smoke", "blocking_reason",
)
FUTURE_REAL_SIDECAR_COLUMNS = (
    "binding_row_id", "source_pipeline", "sample_execution_id",
    "raw_target_relative_path", "expected_raw_sha256", "observed_raw_sha256",
    "raw_source_precondition_status", "raw_source_precondition_blocking_reason",
    "smoke_case_id", "sample_preparation_input_id", "pdb_id", "conn_id",
    "residue_partner_side", "locator_namespace",
    "struct_conn_residue_auth_asym_id", "struct_conn_residue_auth_seq_id",
    "struct_conn_residue_label_asym_id", "struct_conn_residue_label_seq_id",
    "selected_chain_id", "selected_residue_index", "auth_label_conflict_observed",
    "matched_atom_site_id", "matched_residue_atom_name",
    "struct_conn_insertion_source_tag", "struct_conn_insertion_raw_value",
    "struct_conn_token_class", "atom_site_insertion_source_tag",
    "atom_site_insertion_raw_value", "atom_site_token_class",
    "resolved_insertion_state", "resolved_insertion_value",
    "insertion_evidence_agreement", "insertion_blocks_admit_004",
    "insertion_blocking_reason", "covalent_residue_locator_namespace",
    "covalent_residue_insertion_code_state", "covalent_residue_insertion_code",
    "covalent_residue_locator_provenance_source_id",
    "covalent_residue_locator_provenance_sha256", "provider_export_status",
    "provider_export_blocking_reason",
)
EVIDENCE_COLUMNS = (
    "execution_evidence_row_id", "binding_row_id", "smoke_case_id", "pdb_id",
    "ligand_comp_id", "raw_target_relative_path", "expected_raw_sha256",
    "observed_raw_sha256", "expected_raw_size_bytes", "observed_raw_size_bytes",
    "raw_secure_read_status", "strict_decode_status", "struct_conn_parse_status",
    "struct_conn_row_count", "selected_struct_conn_row_ordinal_1based",
    "selected_struct_conn_match_count", "residue_partner_side",
    "locator_namespace", "atom_site_parse_status", "atom_site_row_count",
    "selected_atom_site_row_ordinal_1based", "selected_atom_site_match_count",
    "provider_export_status", "provider_export_blocking_reason",
    "evidence_audit_passed",
)
CONTRACT_COLUMNS = (
    "contract_item_id", "contract_area", "requirement", "expected_value",
    "observed_value", "contract_passed", "blocking_reason",
)
SAFETY_COLUMNS = (
    "safety_item", "required_status", "observed_status", "safety_passed",
    "blocking_reason",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "severity", "status", "issue_count",
    "blocking_reason",
)

STAT_FIELDS = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
CHUNK_SIZE = 1024 * 1024
VALID_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    content_bytes: bytes
    sha256: str
    size_bytes: int
    pre_stat_fingerprint: tuple[int, ...]
    post_stat_fingerprint: tuple[int, ...]


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]
    status: str
    blocking_reason: str
    structural_check_count: int
    content_read_count: int


@dataclass(frozen=True)
class CsvDocument:
    header: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    status: str
    blocking_reason: str


@dataclass(frozen=True)
class VerifiedRawSource:
    relative_path: str
    content_bytes: bytes
    expected_sha256: str
    observed_sha256: str
    expected_size_bytes: int
    observed_size_bytes: int
    pre_stat_fingerprint: tuple[int, ...]
    post_stat_fingerprint: tuple[int, ...]
    passed: bool
    blocking_reason: str


@dataclass(frozen=True)
class SelectedStructConnEvent:
    row: Any
    row_ordinal_1based: int
    match_count: int
    residue_partner_side: str
    residue: tuple[tuple[str, str], ...]
    ligand: tuple[tuple[str, str], ...]

    def residue_dict(self) -> dict[str, str]:
        return dict(self.residue)


def _git(args: Sequence[str], repo_root: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo_root, text=True, capture_output=True, check=False
    )


def _stat_tuple(value: os.stat_result) -> tuple[int, ...]:
    return tuple(int(getattr(value, field)) for field in STAT_FIELDS)


def _valid_sha(value: object) -> bool:
    return type(value) is str and VALID_SHA256.fullmatch(value) is not None


def _safe_relative_path(value: object) -> bool:
    if type(value) is not str or not value or value != value.strip() or "\\" in value or "\x00" in value:
        return False
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value):
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and path.as_posix() == value
        and all(part not in ("", ".", "..", "?") for part in path.parts)
    )


def _safe_raw_path(value: object) -> bool:
    if not _safe_relative_path(value):
        return False
    path = PurePosixPath(value)
    return path.parts[:3] == ("data", "raw", "covalent_sources") and path.suffix in (".cif", ".mmcif")


def _structural_stat(repo_root: Path, relative: Path) -> os.stat_result | None:
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptors: list[int] = []
    try:
        current = os.open(os.fspath(repo_root), directory_flags)
        descriptors.append(current)
        for component in relative.parts[:-1]:
            current = os.open(component, directory_flags, dir_fd=current)
            descriptors.append(current)
        return os.stat(relative.parts[-1], dir_fd=current, follow_symlinks=False)
    except (OSError, TypeError, ValueError):
        return None
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _secure_read_expected_file(
    repo_root: Path,
    relative: Path,
    expected_sha256: str,
    *,
    read_fn: Callable[[int, int], bytes] = os.read,
) -> tuple[FrozenSourceRecord | None, str]:
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptors: list[int] = []
    try:
        current = os.open(os.fspath(repo_root), directory_flags)
        descriptors.append(current)
        for component in relative.parts[:-1]:
            current = os.open(component, directory_flags, dir_fd=current)
            descriptors.append(current)
        final_name = relative.parts[-1]
        entry = os.stat(final_name, dir_fd=current, follow_symlinks=False)
        if stat.S_ISLNK(entry.st_mode):
            return None, "SOURCE_FINAL_ENTRY_SYMLINK_REJECTED"
        if not stat.S_ISREG(entry.st_mode):
            return None, "SOURCE_NOT_REGULAR_FILE"
        file_fd = os.open(final_name, file_flags, dir_fd=current)
        descriptors.append(file_fd)
        pre = os.fstat(file_fd)
        if not stat.S_ISREG(pre.st_mode):
            return None, "SOURCE_NOT_REGULAR_FILE"
        if any(getattr(entry, field) != getattr(pre, field) for field in ("st_dev", "st_ino", "st_mode")):
            return None, "SOURCE_CHANGED_DURING_OPEN"
        chunks: list[bytes] = []
        while True:
            chunk = read_fn(file_fd, CHUNK_SIZE)
            if not chunk:
                break
            if type(chunk) is not bytes:
                return None, "SOURCE_READ_RESULT_NOT_BYTES"
            chunks.append(chunk)
        content_bytes = b"".join(chunks)
        post = os.fstat(file_fd)
        final_stat = os.stat(final_name, dir_fd=current, follow_symlinks=False)
        pre_fp = _stat_tuple(pre)
        post_fp = _stat_tuple(post)
        if pre_fp != post_fp or any(
            getattr(post, field) != getattr(final_stat, field)
            for field in STAT_FIELDS
        ):
            return None, "SOURCE_CHANGED_DURING_READ"
        if len(content_bytes) != post.st_size:
            return None, "SOURCE_PARTIAL_READ"
        digest = hashlib.sha256(content_bytes).hexdigest()
        if digest != expected_sha256:
            return None, "SOURCE_SHA256_MISMATCH"
        return FrozenSourceRecord(relative, content_bytes, digest, len(content_bytes), pre_fp, post_fp), ""
    except FileNotFoundError:
        return None, "SOURCE_MISSING"
    except NotADirectoryError:
        return None, "SOURCE_PARENT_NOT_DIRECTORY"
    except OSError:
        return None, "SOURCE_SECURE_FD_ACCESS_FAILED"
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT,
    *,
    git_provider: Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]] = _git,
    read_fn: Callable[[int, int], bytes] = os.read,
) -> FrozenSourceSnapshot:
    structural_count = 0
    for relative in SOURCE_PATHS:
        entry = _structural_stat(repo_root, relative)
        tracked = git_provider(("ls-files", "--error-unmatch", "--", relative.as_posix()), repo_root).returncode == 0
        if entry is None or not tracked or not stat.S_ISREG(entry.st_mode) or stat.S_ISLNK(entry.st_mode):
            return FrozenSourceSnapshot((), "blocked", "SOURCE_STRUCTURAL_BOUNDARY_FAILED", structural_count, 0)
        structural_count += 1
    records: list[FrozenSourceRecord] = []
    for relative in SOURCE_PATHS:
        record, reason = _secure_read_expected_file(
            repo_root, relative, SOURCE_SHA256[relative], read_fn=read_fn
        )
        if record is None:
            return FrozenSourceSnapshot((), "blocked", reason, structural_count, len(records))
        records.append(record)
    return FrozenSourceSnapshot(tuple(records), "passed", "", structural_count, len(records))


def validate_frozen_source_snapshot(snapshot: object) -> bool:
    return (
        type(snapshot) is FrozenSourceSnapshot
        and snapshot.status == "passed"
        and snapshot.blocking_reason == ""
        and snapshot.structural_check_count == len(SOURCE_PATHS)
        and snapshot.content_read_count == len(SOURCE_PATHS)
        and len(snapshot.records) == len(SOURCE_PATHS)
        and tuple(record.relative_path for record in snapshot.records) == SOURCE_PATHS
        and all(
            type(record.content_bytes) is bytes
            and record.sha256 == SOURCE_SHA256[record.relative_path]
            and hashlib.sha256(record.content_bytes).hexdigest() == record.sha256
            and len(record.content_bytes) == record.size_bytes
            and record.pre_stat_fingerprint == record.post_stat_fingerprint
            for record in snapshot.records
        )
    )


def _source_record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord | None:
    if not validate_frozen_source_snapshot(snapshot):
        return None
    matches = [record for record in snapshot.records if record.relative_path == path]
    return matches[0] if len(matches) == 1 else None


def _extract_literal_tuple_assignment(
    source_bytes: bytes,
    assignment_name: str,
) -> tuple[str, ...]:
    """Statically extract one module-level string tuple without executing code.

    A tuple/list may statically unpack another uniquely assigned module-level
    tuple/list.  This is needed for P6-A's literal schema composition; arbitrary
    names, calls, attributes, operators, comprehensions, and other expressions
    remain forbidden.
    """
    if type(source_bytes) is not bytes or type(assignment_name) is not str or not assignment_name:
        return ()
    try:
        tree = ast.parse(source_bytes.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, SyntaxError, ValueError, TypeError):
        return ()
    assignments: dict[str, list[ast.expr]] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(statement.value)
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            if statement.value is not None:
                assignments.setdefault(statement.target.id, []).append(statement.value)

    def resolve(name: str, active: frozenset[str]) -> tuple[str, ...]:
        nodes = assignments.get(name, [])
        if len(nodes) != 1 or name in active:
            return ()
        node = nodes[0]
        if not isinstance(node, (ast.Tuple, ast.List)) or not node.elts:
            return ()
        values: list[str] = []
        for element in node.elts:
            if isinstance(element, ast.Constant) and type(element.value) is str:
                values.append(element.value)
            elif (
                isinstance(element, ast.Starred)
                and isinstance(element.value, ast.Name)
            ):
                expanded = resolve(element.value.id, active | {name})
                if not expanded:
                    return ()
                values.extend(expanded)
            else:
                return ()
        if not values or len(values) != len(set(values)):
            return ()
        return tuple(values)

    return resolve(assignment_name, frozenset())


def _extract_frozen_schema_contract(
    snapshot: FrozenSourceSnapshot,
) -> tuple[bool, dict[str, tuple[str, ...]]]:
    p6a_record = _source_record(snapshot, P6A_MODULE_PATH)
    p6b_record = _source_record(snapshot, P6B_MODULE_PATH)
    if p6a_record is None or p6b_record is None:
        return False, {}
    extracted = {
        "p6a_future_real_sidecar_columns": _extract_literal_tuple_assignment(
            p6a_record.content_bytes, "FUTURE_REAL_SIDECAR_COLUMNS"
        ),
        "p6a_binding_columns": _extract_literal_tuple_assignment(
            p6a_record.content_bytes, "BINDING_COLUMNS"
        ),
        "p6b_matrix_columns": _extract_literal_tuple_assignment(
            p6b_record.content_bytes, "MATRIX_COLUMNS"
        ),
    }
    passed = (
        extracted["p6a_future_real_sidecar_columns"] == FUTURE_REAL_SIDECAR_COLUMNS
        and extracted["p6a_binding_columns"] == P6A_BINDING_COLUMNS
        and extracted["p6b_matrix_columns"] == P6B_MATRIX_COLUMNS
    )
    return passed, extracted if passed else {}


def _parse_csv_bytes(content_bytes: bytes) -> CsvDocument:
    try:
        text = content_bytes.decode("utf-8", errors="strict")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if reader.fieldnames is None:
            return CsvDocument((), (), "blocked", "CSV_HEADER_MISSING")
        header = tuple(reader.fieldnames)
        if not header or len(set(header)) != len(header) or any(not field for field in header):
            return CsvDocument(header, (), "blocked", "CSV_HEADER_INVALID")
        rows: list[dict[str, str]] = []
        for row in reader:
            if None in row or tuple(row) != header or any(type(value) is not str for value in row.values()):
                return CsvDocument(header, tuple(rows), "blocked", "CSV_ROW_INVALID")
            rows.append(dict(row))
        if not rows:
            return CsvDocument(header, (), "blocked", "CSV_ROWS_EMPTY")
        return CsvDocument(header, tuple(rows), "passed", "")
    except (UnicodeError, csv.Error):
        return CsvDocument((), (), "blocked", "CSV_READ_FAILED")


def _snapshot_csv(snapshot: FrozenSourceSnapshot, path: Path) -> CsvDocument:
    record = _source_record(snapshot, path)
    return _parse_csv_bytes(record.content_bytes) if record else CsvDocument((), (), "blocked", "SOURCE_ACCESS_NOT_ALLOWED")


def _snapshot_json(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    record = _source_record(snapshot, path)
    if record is None:
        return {}
    try:
        payload = json.loads(record.content_bytes.decode("utf-8", errors="strict"))
    except (UnicodeError, json.JSONDecodeError):
        return {}
    return payload if type(payload) is dict else {}


def _validate_p6b_predecessor(
    snapshot: FrozenSourceSnapshot,
) -> tuple[bool, list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    binding_doc = _snapshot_csv(snapshot, P6A_BINDING_PATH)
    contract = _snapshot_csv(snapshot, P6B_CONTRACT_PATH)
    matrix_doc = _snapshot_csv(snapshot, P6B_MATRIX_PATH)
    authority = _snapshot_csv(snapshot, P6B_AUTHORITY_PATH)
    safety = _snapshot_csv(snapshot, P6B_SAFETY_PATH)
    issues = _snapshot_csv(snapshot, P6B_ISSUE_PATH)
    manifest = _snapshot_json(snapshot, P6B_MANIFEST_PATH)
    bindings = list(binding_doc.rows)
    matrix = list(matrix_doc.rows)
    records_by_name = {record.relative_path.name: record for record in snapshot.records}
    manifest_hashes = manifest.get("output_sha256", {})
    expected_non_manifest = P6B_OUTPUT_FILES[:-1]
    output_hashes_valid = (
        type(manifest_hashes) is dict
        and set(manifest_hashes) == set(expected_non_manifest)
        and all(
            manifest_hashes.get(name) == records_by_name[name].sha256
            for name in expected_non_manifest
        )
    )
    binding_ok = (
        binding_doc.status == "passed"
        and binding_doc.header == P6A_BINDING_COLUMNS
        and len(bindings) == 11
        and [row["binding_row_id"] for row in bindings]
        == [f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)]
        and len({row["sample_preparation_input_id"] for row in bindings}) == 11
        and len({(row["pdb_id"], row["ligand_comp_id"]) for row in bindings}) == 11
        and all(
            row["metadata_join_status"] == "one_to_one_metadata_join_complete"
            and row["raw_path_persisted"] == "true"
            and _safe_raw_path(row["raw_target_relative_path"])
            for row in bindings
        )
    )
    matrix_ok = (
        matrix_doc.status == "passed"
        and matrix_doc.header == P6B_MATRIX_COLUMNS
        and len(matrix) == 11
        and [row["binding_row_id"] for row in matrix]
        == [f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)]
        and all(
            row["authority_join_status"] == "exact_authority_match"
            and _valid_sha(row["expected_sha256"])
            and row["expected_sha256"] == row["observed_sha256"]
            and row["expected_file_size_bytes"].isdecimal()
            and int(row["expected_file_size_bytes"]) > 0
            and row["expected_file_size_bytes"] == row["observed_file_size_bytes"]
            and row["sha256_matches"] == "true"
            and row["file_size_matches"] == "true"
            and row["stat_stable"] == "true"
            and row["raw_source_precondition_status"] == "passed"
            and row["ready_for_real_provider_export_execution_smoke"] == "true"
            and row["blocking_reason"] == ""
            for row in matrix
        )
        and [row["raw_git_tracking_state"] for row in matrix[:3]]
        == ["untracked_historical_authority_runtime"] * 3
        and [row["raw_git_tracking_state"] for row in matrix[3:]] == ["ignored_runtime"] * 8
    )
    direct_outputs_ok = (
        contract.status == "passed"
        and all(row.get("contract_passed") == "true" and row.get("blocking_reason") == "" for row in contract.rows)
        and authority.status == "passed"
        and len(authority.rows) == 2
        and [row.get("authority_row_count") for row in authority.rows] == ["3", "8"]
        and all(row.get("authority_check_passed") == "true" for row in authority.rows)
        and safety.status == "passed"
        and issues.status == "passed"
        and [row.get("issue_id") for row in issues.rows] == [
            "REAL_RESIDUE_LOCATOR_PROVIDER_EXPORT_NOT_YET_EXECUTED",
            "REAL_PROVIDER_SIDECAR_NOT_YET_MERGED_INTO_ADMISSION_SCHEMA",
        ]
    )
    manifest_ok = (
        manifest.get("stage") == PREVIOUS_STAGE
        and manifest.get("step_label") == "Step14AU-E0-P6-B"
        and manifest.get("all_checks_passed") is True
        and manifest.get("validation_failures") == []
        and manifest.get("output_files") == list(P6B_OUTPUT_FILES)
        and manifest.get("output_file_count") == 6
        and output_hashes_valid
        and manifest.get("source_input_count") == 9
        and manifest.get("authority_binding_match_count") == 11
        and manifest.get("raw_source_precondition_row_count") == 11
        and manifest.get("raw_source_precondition_passed_count") == 11
        and manifest.get("raw_source_precondition_blocked_count") == 0
        and manifest.get("raw_sha256_match_count") == 11
        and manifest.get("raw_file_size_match_count") == 11
        and manifest.get("raw_stat_stable_count") == 11
        and manifest.get("untracked_historical_authority_runtime_count") == 3
        and manifest.get("ignored_expansion_runtime_count") == 8
        and manifest.get("exact_raw_tracked_count") == 0
        and manifest.get("ready_for_real_provider_export_execution_smoke") is True
        and manifest.get("ready_for_real_provider_export_execution") is False
        and manifest.get("p5b_parser_called_current_step") is False
        and manifest.get("p4_provider_called_current_step") is False
    )
    return binding_ok and matrix_ok and direct_outputs_ok and manifest_ok, bindings, matrix, manifest


def _join_bindings_and_preconditions(
    bindings: Sequence[Mapping[str, str]], matrix: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    if len(bindings) != 11 or len(matrix) != 11:
        return []
    joined: list[dict[str, str]] = []
    for binding, raw in zip(bindings, matrix):
        binding_identity = (
            binding.get("binding_row_id"), binding.get("sample_preparation_input_id"),
            binding.get("pdb_id"), binding.get("ligand_comp_id"),
            binding.get("raw_target_relative_path"),
        )
        raw_identity = (
            raw.get("binding_row_id"), raw.get("sample_preparation_input_id"),
            raw.get("pdb_id"), raw.get("ligand_comp_id"),
            raw.get("raw_target_relative_path"),
        )
        if binding_identity != raw_identity:
            return []
        if (
            raw.get("expected_sha256") != raw.get("observed_sha256")
            or raw.get("expected_file_size_bytes") != raw.get("observed_file_size_bytes")
            or raw.get("raw_source_precondition_status") != "passed"
            or raw.get("ready_for_real_provider_export_execution_smoke") != "true"
        ):
            return []
        joined.append({
            **dict(binding),
            "expected_raw_sha256": raw["expected_sha256"],
            "prior_observed_raw_sha256": raw["observed_sha256"],
            "expected_raw_size_bytes": raw["expected_file_size_bytes"],
            "prior_observed_raw_size_bytes": raw["observed_file_size_bytes"],
        })
    expected_ids = [f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)]
    paths = [row["raw_target_relative_path"] for row in joined]
    return joined if [row["binding_row_id"] for row in joined] == expected_ids and len(set(paths)) == 11 else []


def secure_read_expected_raw_source(
    raw_relative_path: object,
    expected_sha256: object,
    expected_size_bytes: object,
    *,
    repo_root: Path = REPO_ROOT,
    read_fn: Callable[[int, int], bytes] = os.read,
) -> VerifiedRawSource:
    empty_path = raw_relative_path if type(raw_relative_path) is str else ""
    empty_hash = expected_sha256 if type(expected_sha256) is str else ""
    empty_size = expected_size_bytes if type(expected_size_bytes) is int else 0
    if (
        not _safe_raw_path(raw_relative_path)
        or not _valid_sha(expected_sha256)
        or type(expected_size_bytes) is not int
        or expected_size_bytes <= 0
    ):
        return VerifiedRawSource(empty_path, b"", empty_hash, "", empty_size, 0, (), (), False, "RAW_SOURCE_INPUT_INVALID")
    platform = (
        hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "O_CLOEXEC") and os.open in os.supports_dir_fd
        and os.stat in os.supports_dir_fd and os.stat in os.supports_follow_symlinks
    )
    if not platform:
        return VerifiedRawSource(raw_relative_path, b"", expected_sha256, "", expected_size_bytes, 0, (), (), False, "SECURE_FD_PLATFORM_CONTRACT_UNAVAILABLE")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptors: list[int] = []
    try:
        current = os.open(os.fspath(repo_root), directory_flags)
        descriptors.append(current)
        components = PurePosixPath(raw_relative_path).parts
        for component in components[:-1]:
            current = os.open(component, directory_flags, dir_fd=current)
            descriptors.append(current)
        final_name = components[-1]
        entry = os.stat(final_name, dir_fd=current, follow_symlinks=False)
        if stat.S_ISLNK(entry.st_mode):
            return VerifiedRawSource(raw_relative_path, b"", expected_sha256, "", expected_size_bytes, 0, (), (), False, "RAW_FINAL_ENTRY_SYMLINK_REJECTED")
        if not stat.S_ISREG(entry.st_mode):
            return VerifiedRawSource(raw_relative_path, b"", expected_sha256, "", expected_size_bytes, 0, (), (), False, "RAW_SOURCE_NOT_REGULAR_FILE")
        file_fd = os.open(final_name, file_flags, dir_fd=current)
        descriptors.append(file_fd)
        pre = os.fstat(file_fd)
        if not stat.S_ISREG(pre.st_mode):
            return VerifiedRawSource(raw_relative_path, b"", expected_sha256, "", expected_size_bytes, 0, (), (), False, "RAW_SOURCE_NOT_REGULAR_FILE")
        if any(getattr(entry, field) != getattr(pre, field) for field in ("st_dev", "st_ino", "st_mode")):
            return VerifiedRawSource(raw_relative_path, b"", expected_sha256, "", expected_size_bytes, int(pre.st_size), _stat_tuple(pre), (), False, "RAW_SOURCE_CHANGED_DURING_OPEN")
        chunks: list[bytes] = []
        while True:
            chunk = read_fn(file_fd, CHUNK_SIZE)
            if not chunk:
                break
            if type(chunk) is not bytes:
                return VerifiedRawSource(raw_relative_path, b"", expected_sha256, "", expected_size_bytes, 0, _stat_tuple(pre), (), False, "RAW_READ_RESULT_NOT_BYTES")
            chunks.append(chunk)
        content_bytes = b"".join(chunks)
        post = os.fstat(file_fd)
        final_stat = os.stat(final_name, dir_fd=current, follow_symlinks=False)
        pre_fp = _stat_tuple(pre)
        post_fp = _stat_tuple(post)
        stable = (
            pre_fp == post_fp
            and all(
                getattr(post, field) == getattr(final_stat, field)
                for field in STAT_FIELDS
            )
            and not stat.S_ISLNK(final_stat.st_mode)
        )
        if not stable:
            return VerifiedRawSource(raw_relative_path, b"", expected_sha256, "", expected_size_bytes, int(post.st_size), pre_fp, post_fp, False, "RAW_SOURCE_CHANGED_DURING_READ")
        if len(content_bytes) != post.st_size:
            return VerifiedRawSource(raw_relative_path, b"", expected_sha256, "", expected_size_bytes, int(post.st_size), pre_fp, post_fp, False, "RAW_SOURCE_PARTIAL_READ")
        observed_sha = hashlib.sha256(content_bytes).hexdigest()
        if observed_sha != expected_sha256:
            return VerifiedRawSource(raw_relative_path, b"", expected_sha256, observed_sha, expected_size_bytes, len(content_bytes), pre_fp, post_fp, False, "RAW_SOURCE_SHA256_MISMATCH")
        if len(content_bytes) != expected_size_bytes:
            return VerifiedRawSource(raw_relative_path, b"", expected_sha256, observed_sha, expected_size_bytes, len(content_bytes), pre_fp, post_fp, False, "RAW_SOURCE_SIZE_MISMATCH")
        return VerifiedRawSource(raw_relative_path, content_bytes, expected_sha256, observed_sha, expected_size_bytes, len(content_bytes), pre_fp, post_fp, True, "")
    except FileNotFoundError:
        reason = "RAW_SOURCE_MISSING"
    except NotADirectoryError:
        reason = "RAW_PARENT_NOT_DIRECTORY"
    except OSError as error:
        reason = "RAW_SYMLINK_OR_SECURE_OPEN_REJECTED" if error.errno in (20, 40) else "RAW_SOURCE_ACCESS_FAILED"
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass
    return VerifiedRawSource(raw_relative_path, b"", expected_sha256, "", expected_size_bytes, 0, (), (), False, reason)


def _available(value: object) -> str:
    return value if type(value) is str and value not in ("", ".", "?") else ""


def _all_available_match(values: Sequence[str], expected: str) -> bool:
    available = [_available(value) for value in values]
    present = [value for value in available if value]
    return bool(present) and all(value == expected for value in present)


def _struct_partner(row: Mapping[str, str], side: str) -> dict[str, str]:
    return {
        "side": side,
        "label_comp_id": row.get(f"_struct_conn.{side}_label_comp_id", ""),
        "auth_comp_id": row.get(f"_struct_conn.{side}_auth_comp_id", ""),
        "label_atom_id": row.get(f"_struct_conn.{side}_label_atom_id", ""),
        "auth_atom_id": row.get(f"_struct_conn.{side}_auth_atom_id", ""),
        "auth_asym_id": row.get(f"_struct_conn.{side}_auth_asym_id", ""),
        "auth_seq_id": row.get(f"_struct_conn.{side}_auth_seq_id", ""),
        "label_asym_id": row.get(f"_struct_conn.{side}_label_asym_id", ""),
        "label_seq_id": row.get(f"_struct_conn.{side}_label_seq_id", ""),
    }


def select_real_struct_conn_event(raw_result: Any, binding: Mapping[str, str]) -> tuple[SelectedStructConnEvent | None, str, int]:
    conn_matches = [
        row for row in raw_result.rows
        if row.as_dict().get("_struct_conn.id", "") == binding.get("conn_id", "")
    ]
    if not conn_matches:
        return None, "STRUCT_CONN_EVENT_NOT_FOUND", 0
    if len(conn_matches) != 1:
        return None, "MULTIPLE_STRUCT_CONN_EVENTS", len(conn_matches)
    raw_row = conn_matches[0]
    row = raw_row.as_dict()
    if _available(row.get("_struct_conn.conn_type_id", "")).lower() != "covale":
        return None, "STRUCT_CONN_TYPE_NOT_COVALE", 1
    selected_pair = (
        binding.get("selected_residue_chain_id", ""),
        binding.get("selected_residue_index", ""),
    )
    candidates: list[tuple[str, dict[str, str], dict[str, str]]] = []
    residue_without_ligand = False
    for side in ("ptnr1", "ptnr2"):
        opposite = "ptnr2" if side == "ptnr1" else "ptnr1"
        residue = _struct_partner(row, side)
        ligand = _struct_partner(row, opposite)
        auth_pair = (_available(residue["auth_asym_id"]), _available(residue["auth_seq_id"]))
        label_pair = (_available(residue["label_asym_id"]), _available(residue["label_seq_id"]))
        residue_ok = (
            _all_available_match((residue["label_comp_id"], residue["auth_comp_id"]), binding.get("covalent_residue_name", ""))
            and _all_available_match((residue["label_atom_id"], residue["auth_atom_id"]), binding.get("selected_residue_atom_name", ""))
            and selected_pair in (auth_pair, label_pair)
        )
        if not residue_ok:
            continue
        ligand_ok = _all_available_match(
            (ligand["label_comp_id"], ligand["auth_comp_id"]),
            binding.get("ligand_comp_id", ""),
        )
        if ligand_ok:
            candidates.append((side, residue, ligand))
        else:
            residue_without_ligand = True
    if not candidates:
        return None, "LIGAND_PARTNER_IDENTITY_MISMATCH" if residue_without_ligand else "RESIDUE_PARTNER_SIDE_NOT_RESOLVED", 1
    if len(candidates) != 1:
        return None, "MULTIPLE_RESIDUE_PARTNER_SIDES", 1
    side, residue, ligand = candidates[0]
    return SelectedStructConnEvent(
        raw_row, raw_row.row_ordinal_1based, 1, side,
        tuple(residue.items()), tuple(ligand.items()),
    ), "", 1


def resolve_real_locator_namespace(event: SelectedStructConnEvent, binding: Mapping[str, str]) -> tuple[str, str]:
    residue = event.residue_dict()
    selected = (
        binding.get("selected_residue_chain_id", ""),
        binding.get("selected_residue_index", ""),
    )
    auth = (_available(residue["auth_asym_id"]), _available(residue["auth_seq_id"]))
    label = (_available(residue["label_asym_id"]), _available(residue["label_seq_id"]))
    auth_match = all(auth) and auth == selected
    label_match = all(label) and label == selected
    if auth_match and not label_match:
        return "auth", ""
    if label_match and not auth_match:
        return "label", ""
    if auth_match and label_match and auth == label:
        return "auth", ""
    if auth_match and label_match:
        return "", "LOCATOR_NAMESPACE_AMBIGUOUS_CONFLICT"
    mixed = (
        (selected[0] == auth[0] and selected[1] == label[1])
        or (selected[0] == label[0] and selected[1] == auth[1])
    ) and selected not in (auth, label)
    return ("", "LOCATOR_NAMESPACE_MIXED_SELECTION_FORBIDDEN" if mixed else "LOCATOR_NAMESPACE_SELECTED_PAIR_NOT_FOUND")


def select_unique_real_atom_site_row(
    raw_result: Any,
    namespace: str,
    binding: Mapping[str, str],
) -> tuple[Any | None, str, int]:
    chain_tag = f"_atom_site.{namespace}_asym_id"
    seq_tag = f"_atom_site.{namespace}_seq_id"
    matches = []
    for raw_row in raw_result.rows:
        row = raw_row.as_dict()
        if (
            row.get(chain_tag, "") == binding.get("selected_residue_chain_id", "")
            and row.get(seq_tag, "") == binding.get("selected_residue_index", "")
            and _all_available_match(
                (row.get("_atom_site.label_comp_id", ""), row.get("_atom_site.auth_comp_id", "")),
                binding.get("covalent_residue_name", ""),
            )
            and _all_available_match(
                (row.get("_atom_site.label_atom_id", ""), row.get("_atom_site.auth_atom_id", "")),
                binding.get("selected_residue_atom_name", ""),
            )
        ):
            matches.append(raw_row)
    if not matches:
        return None, "MATCHED_ATOM_SITE_ROW_NOT_FOUND", 0
    if len(matches) != 1:
        return None, "MULTIPLE_MATCHED_ATOM_SITE_ROWS", len(matches)
    return matches[0], "", 1


def _empty_sidecar_row(binding: Mapping[str, str], index: int) -> dict[str, Any]:
    row: dict[str, Any] = {column: "" for column in FUTURE_REAL_SIDECAR_COLUMNS}
    row.update({
        "binding_row_id": binding.get("binding_row_id", ""),
        "source_pipeline": binding.get("source_pipeline", ""),
        "sample_execution_id": binding.get("sample_execution_id", ""),
        "raw_target_relative_path": binding.get("raw_target_relative_path", ""),
        "expected_raw_sha256": binding.get("expected_raw_sha256", ""),
        "raw_source_precondition_status": "blocked",
        "smoke_case_id": f"P6C_REAL_{index:06d}",
        "sample_preparation_input_id": binding.get("sample_preparation_input_id", ""),
        "pdb_id": binding.get("pdb_id", ""),
        "conn_id": binding.get("conn_id", ""),
        "selected_chain_id": binding.get("selected_residue_chain_id", ""),
        "selected_residue_index": binding.get("selected_residue_index", ""),
        "provider_export_status": "rejected",
    })
    return row


def _empty_evidence_row(binding: Mapping[str, str], index: int) -> dict[str, Any]:
    row: dict[str, Any] = {column: "" for column in EVIDENCE_COLUMNS}
    row.update({
        "execution_evidence_row_id": f"P6C_EXECUTION_EVIDENCE_{index:06d}",
        "binding_row_id": binding.get("binding_row_id", ""),
        "smoke_case_id": f"P6C_REAL_{index:06d}",
        "pdb_id": binding.get("pdb_id", ""),
        "ligand_comp_id": binding.get("ligand_comp_id", ""),
        "raw_target_relative_path": binding.get("raw_target_relative_path", ""),
        "expected_raw_sha256": binding.get("expected_raw_sha256", ""),
        "expected_raw_size_bytes": binding.get("expected_raw_size_bytes", ""),
        "raw_secure_read_status": "blocked",
        "strict_decode_status": "not_attempted",
        "struct_conn_parse_status": "not_attempted",
        "atom_site_parse_status": "not_attempted",
        "provider_export_status": "rejected",
        "evidence_audit_passed": False,
    })
    return row


def _reject(row: dict[str, Any], evidence: dict[str, Any], reason: str) -> tuple[dict[str, Any], dict[str, Any]]:
    row["provider_export_status"] = "rejected"
    row["provider_export_blocking_reason"] = reason
    evidence["provider_export_status"] = "rejected"
    evidence["provider_export_blocking_reason"] = reason
    evidence["evidence_audit_passed"] = False
    return row, evidence


def execute_one_binding(
    binding: Mapping[str, str],
    index: int,
    *,
    p4: ModuleType,
    p5b: ModuleType,
    repo_root: Path = REPO_ROOT,
    raw_reader: Callable[..., VerifiedRawSource] = secure_read_expected_raw_source,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    row = _empty_sidecar_row(binding, index)
    evidence = _empty_evidence_row(binding, index)
    counts = {"raw": 0, "decode": 0, "struct_parse": 0, "atom_parse": 0, "provider": 0}
    raw = raw_reader(
        binding.get("raw_target_relative_path"),
        binding.get("expected_raw_sha256"),
        int(binding.get("expected_raw_size_bytes", "0")),
        repo_root=repo_root,
    )
    if not raw.passed:
        row["raw_source_precondition_blocking_reason"] = raw.blocking_reason
        evidence["provider_export_blocking_reason"] = raw.blocking_reason
        return _reject(row, evidence, raw.blocking_reason) + (counts,)
    counts["raw"] = 1
    row.update({
        "observed_raw_sha256": raw.observed_sha256,
        "raw_source_precondition_status": "passed",
        "raw_source_precondition_blocking_reason": "",
    })
    evidence.update({
        "observed_raw_sha256": raw.observed_sha256,
        "observed_raw_size_bytes": raw.observed_size_bytes,
        "raw_secure_read_status": "passed",
    })
    try:
        text = raw.content_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        evidence["strict_decode_status"] = "failed"
        return _reject(row, evidence, "RAW_MMCIF_UTF8_DECODE_FAILED") + (counts,)
    counts["decode"] = 1
    evidence["strict_decode_status"] = "passed"
    struct_raw = p5b.parse_raw_preserving_mmcif_loop(text, "_struct_conn.")
    counts["struct_parse"] = 1
    evidence["struct_conn_parse_status"] = struct_raw.status
    evidence["struct_conn_row_count"] = len(struct_raw.rows)
    if not struct_raw.passed:
        return _reject(row, evidence, struct_raw.blocking_reason or "STRUCT_CONN_PARSE_FAILED") + (counts,)
    atom_raw = p5b.parse_raw_preserving_mmcif_loop(text, "_atom_site.")
    counts["atom_parse"] = 1
    evidence["atom_site_parse_status"] = atom_raw.status
    evidence["atom_site_row_count"] = len(atom_raw.rows)
    if not atom_raw.passed:
        return _reject(row, evidence, atom_raw.blocking_reason or "ATOM_SITE_PARSE_FAILED") + (counts,)
    event, reason, event_count = select_real_struct_conn_event(struct_raw, binding)
    evidence["selected_struct_conn_match_count"] = event_count
    if event is None:
        return _reject(row, evidence, reason) + (counts,)
    evidence["selected_struct_conn_row_ordinal_1based"] = event.row_ordinal_1based
    evidence["residue_partner_side"] = event.residue_partner_side
    row["residue_partner_side"] = event.residue_partner_side
    namespace, reason = resolve_real_locator_namespace(event, binding)
    if not namespace:
        return _reject(row, evidence, reason) + (counts,)
    evidence["locator_namespace"] = namespace
    row["locator_namespace"] = namespace
    residue = event.residue_dict()
    namespace_result = p4.resolve_locator_namespace_evidence(
        locator_namespace=namespace,
        struct_conn_residue_auth_asym_id=_available(residue["auth_asym_id"]),
        struct_conn_residue_auth_seq_id=_available(residue["auth_seq_id"]),
        struct_conn_residue_label_asym_id=_available(residue["label_asym_id"]),
        struct_conn_residue_label_seq_id=_available(residue["label_seq_id"]),
        selected_chain_id=binding["selected_residue_chain_id"],
        selected_residue_index=binding["selected_residue_index"],
    )
    if not namespace_result.passed:
        return _reject(row, evidence, namespace_result.blocking_reason) + (counts,)
    row.update({
        "struct_conn_residue_auth_asym_id": _available(residue["auth_asym_id"]),
        "struct_conn_residue_auth_seq_id": _available(residue["auth_seq_id"]),
        "struct_conn_residue_label_asym_id": _available(residue["label_asym_id"]),
        "struct_conn_residue_label_seq_id": _available(residue["label_seq_id"]),
        "auth_label_conflict_observed": namespace_result.auth_label_conflict_observed,
    })
    atom_match, reason, atom_count = select_unique_real_atom_site_row(atom_raw, namespace, binding)
    evidence["selected_atom_site_match_count"] = atom_count
    if atom_match is None:
        return _reject(row, evidence, reason) + (counts,)
    evidence["selected_atom_site_row_ordinal_1based"] = atom_match.row_ordinal_1based
    atom = atom_match.as_dict()
    atom_name = _available(atom.get("_atom_site.auth_atom_id", "")) or _available(atom.get("_atom_site.label_atom_id", ""))
    atom_identity = p4.validate_matched_atom_site_row_identity(atom.get("_atom_site.id", ""), atom_name)
    if not atom_identity.passed:
        return _reject(row, evidence, atom_identity.blocking_reason) + (counts,)
    row.update({
        "matched_atom_site_id": atom_identity.matched_atom_site_id,
        "matched_residue_atom_name": atom_identity.matched_residue_atom_name,
    })
    struct_tag = (
        p4.PARSER_INSERTION_SOURCE_TAGS[1]
        if event.residue_partner_side == "ptnr1"
        else p4.PARSER_INSERTION_SOURCE_TAGS[2]
    )
    atom_tag = p4.PARSER_INSERTION_SOURCE_TAGS[0]
    event_dict = event.row.as_dict()
    struct_source_tag = struct_tag if struct_tag in struct_raw.tags else ""
    atom_source_tag = atom_tag if atom_tag in atom_raw.tags else ""
    struct_raw_value = event_dict.get(struct_tag, "") if struct_source_tag else ""
    atom_raw_value = atom.get(atom_tag, "") if atom_source_tag else ""
    struct_token = p4.classify_insertion_code_raw_token(bool(struct_source_tag), struct_raw_value)
    atom_token = p4.classify_insertion_code_raw_token(bool(atom_source_tag), atom_raw_value)
    if not struct_token.passed or not atom_token.passed:
        reason = struct_token.blocking_reason or atom_token.blocking_reason or "COVALENT_RESIDUE_INSERTION_CODE_EVIDENCE_INVALID"
        return _reject(row, evidence, reason) + (counts,)
    resolution = p4.resolve_insertion_code_evidence(struct_token, atom_token)
    row.update({
        "struct_conn_insertion_source_tag": struct_source_tag,
        "struct_conn_insertion_raw_value": struct_raw_value,
        "struct_conn_token_class": struct_token.token_class,
        "atom_site_insertion_source_tag": atom_source_tag,
        "atom_site_insertion_raw_value": atom_raw_value,
        "atom_site_token_class": atom_token.token_class,
        "resolved_insertion_state": resolution.resolved_state,
        "resolved_insertion_value": resolution.resolved_value,
        "insertion_evidence_agreement": resolution.evidence_agreement,
        "insertion_blocks_admit_004": resolution.blocks_admit_004,
        "insertion_blocking_reason": resolution.blocking_reason,
    })
    try:
        counts["provider"] = 1
        provider_fields = p4.build_locator_provider_export_fields(
            locator_namespace=namespace,
            sample_preparation_input_id=binding["sample_preparation_input_id"],
            pdb_id=binding["pdb_id"],
            conn_id=binding["conn_id"],
            residue_partner_side=event.residue_partner_side,
            struct_conn_residue_auth_asym_id=row["struct_conn_residue_auth_asym_id"],
            struct_conn_residue_auth_seq_id=row["struct_conn_residue_auth_seq_id"],
            struct_conn_residue_label_asym_id=row["struct_conn_residue_label_asym_id"],
            struct_conn_residue_label_seq_id=row["struct_conn_residue_label_seq_id"],
            selected_chain_id=row["selected_chain_id"],
            selected_residue_index=row["selected_residue_index"],
            matched_atom_site_id=row["matched_atom_site_id"],
            matched_residue_atom_name=row["matched_residue_atom_name"],
            struct_conn_insertion_source_tag=struct_source_tag,
            struct_conn_insertion_raw_value=struct_raw_value,
            atom_site_insertion_source_tag=atom_source_tag,
            atom_site_insertion_raw_value=atom_raw_value,
        )
    except (TypeError, ValueError) as error:
        return _reject(row, evidence, str(error) or "PROVIDER_EXPORT_REJECTED") + (counts,)
    row.update(provider_fields)
    status = "exported_blocking" if resolution.blocks_admit_004 else "exported_pass"
    blocking_reason = resolution.blocking_reason if resolution.blocks_admit_004 else ""
    row["provider_export_status"] = status
    row["provider_export_blocking_reason"] = blocking_reason
    evidence["provider_export_status"] = status
    evidence["provider_export_blocking_reason"] = blocking_reason
    evidence["evidence_audit_passed"] = True
    return row, evidence, counts


def _load_runtime_modules() -> tuple[ModuleType, ModuleType]:
    """Import only the provider and parser needed by exact11 execution."""
    p4 = importlib.import_module(P4_RUNTIME_MODULE_NAME)
    p5b = importlib.import_module(P5B_RUNTIME_MODULE_NAME)
    return p4, p5b


def _validate_runtime_module(
    module: ModuleType,
    *,
    expected_module_name: str,
    expected_relative_path: Path,
    required_callables: Sequence[str],
    snapshot: FrozenSourceSnapshot,
    repo_root: Path,
) -> bool:
    record = _source_record(snapshot, expected_relative_path)
    module_file = getattr(module, "__file__", None)
    if (
        type(module) is not ModuleType
        or module.__name__ != expected_module_name
        or type(module_file) is not str
        or record is None
    ):
        return False
    expected_path = Path(os.path.abspath(repo_root / expected_relative_path))
    observed_path = Path(os.path.abspath(module_file))
    if (
        observed_path != expected_path
        or observed_path.is_symlink()
        or not observed_path.is_file()
        or any(not callable(getattr(module, name, None)) for name in required_callables)
    ):
        return False
    current, _ = _secure_read_expected_file(
        repo_root, expected_relative_path, record.sha256
    )
    return (
        current is not None
        and current.sha256 == record.sha256
        and current.content_bytes == record.content_bytes
    )


def _validate_runtime_modules(
    p4: ModuleType,
    p5b: ModuleType,
    *,
    snapshot: FrozenSourceSnapshot,
    repo_root: Path,
) -> bool:
    return (
        _validate_runtime_module(
            p4,
            expected_module_name=P4_RUNTIME_MODULE_NAME,
            expected_relative_path=P4_MODULE_PATH,
            required_callables=(
                "build_locator_provider_export_fields",
                "build_locator_provenance_source_id",
                "build_canonical_locator_provenance_payload",
                "sha256_canonical_locator_provenance_payload",
            ),
            snapshot=snapshot,
            repo_root=repo_root,
        )
        and _validate_runtime_module(
            p5b,
            expected_module_name=P5B_RUNTIME_MODULE_NAME,
            expected_relative_path=P5B_MODULE_PATH,
            required_callables=("parse_raw_preserving_mmcif_loop",),
            snapshot=snapshot,
            repo_root=repo_root,
        )
    )


CONTRACT_SPECS = (
    ("source", "exact source input count", "11", "source_count"),
    ("source", "source structural checks before content read", "11", "source_structural"),
    ("source", "source content reads from validated paths", "11", "source_reads"),
    ("source", "source hashes exact", "11", "source_hashes"),
    ("predecessor", "P6-B direct evidence valid", "true", "predecessor"),
    ("binding", "P6-A binding shape", "11x26", "binding_shape"),
    ("binding", "P6-B matrix shape", "11x31", "matrix_shape"),
    ("binding", "exact ordered full identity joins", "11", "joins"),
    ("raw", "secure same-bytes raw reads", "11", "raw_reads"),
    ("raw", "raw SHA matches", "11", "raw_hashes"),
    ("raw", "raw size matches", "11", "raw_sizes"),
    ("decode", "strict UTF-8 decode count", "11", "decode"),
    ("parser", "struct_conn parse count", "11", "struct_parse"),
    ("parser", "atom_site parse count", "11", "atom_parse"),
    ("selector", "unique struct_conn event count", "11", "events"),
    ("selector", "unique atom_site row count", "11", "atoms"),
    ("provider", "P4 provider call count", "11", "provider_calls"),
    ("output", "sidecar exact column count", "41", "sidecar_columns"),
    ("output", "sidecar exact row count", "11", "sidecar_rows"),
    ("output", "rejected row count", "0", "rejected"),
    ("output", "exported rows count", "11", "exported"),
    ("provenance", "provider row count", "11", "provider_rows"),
    ("provenance", "unique source ID count", "11", "source_ids"),
    ("provenance", "valid provenance SHA count", "11", "provenance_hashes"),
    ("evidence", "evidence audit passed count", "11", "evidence"),
    ("boundary", "admission modification", "false", "admission"),
    ("boundary", "sample backfill", "false", "backfill"),
    ("boundary", "ADMIT_004 ready", "false", "admit"),
    ("boundary", "E1 ready", "false", "e1"),
    ("boundary", "candidate evaluation ready", "false", "candidate"),
    ("boundary", "bulk download ready", "false", "download"),
    ("boundary", "training ready", "false", "training"),
)


def _contract_rows(observations: Mapping[str, object]) -> list[dict[str, Any]]:
    rows = []
    for index, (area, requirement, expected, key) in enumerate(CONTRACT_SPECS, 1):
        observed = _text(observations.get(key, ""))
        passed = observed == expected
        rows.append({
            "contract_item_id": f"P6C_C{index:03d}", "contract_area": area,
            "requirement": requirement, "expected_value": expected,
            "observed_value": observed, "contract_passed": passed,
            "blocking_reason": "" if passed else f"P6C_CONTRACT_{key.upper()}_FAILED",
        })
    return rows


def validate_contract_rows(rows: Sequence[Mapping[str, Any]], observations: Mapping[str, object]) -> bool:
    return [dict(row) for row in rows] == _contract_rows(observations)


SAFETY_SPECS = (
    ("exact_source_reads", True), ("exact11_raw_secure_read", True),
    ("strict_utf8_decode", True), ("struct_conn_parse", True),
    ("atom_site_parse", True), ("p4_provider_calls", True),
    ("sidecar_materialization", True), ("raw_directory_scan", False),
    ("raw_write", False), ("network_access", False), ("download", False),
    ("admission_modification", False), ("sample_backfill", False),
    ("checkpoint_access", False), ("torch_imported", False),
    ("numpy_imported", False), ("model_forward", False),
    ("loss_compute", False), ("training", False),
)


def _safety_rows(execution: Mapping[str, bool]) -> list[dict[str, Any]]:
    rows = []
    for item, required in SAFETY_SPECS:
        observed = execution.get(item, False)
        passed = type(observed) is bool and observed is required
        rows.append({
            "safety_item": item, "required_status": required,
            "observed_status": observed, "safety_passed": passed,
            "blocking_reason": "" if passed else f"P6C_SAFETY_{item.upper()}_FAILED",
        })
    return rows


def _issue_rows(exported_blocking: int, rejected: int) -> list[dict[str, Any]]:
    rows = [{
        "issue_id": "REAL_PROVIDER_SIDECAR_NOT_YET_MERGED_INTO_ADMISSION_SCHEMA",
        "issue_type": "schema_integration", "severity": "blocking", "status": "open",
        "issue_count": 1,
        "blocking_reason": "REAL_PROVIDER_SIDECAR_NOT_YET_MERGED_INTO_ADMISSION_SCHEMA",
    }]
    if exported_blocking:
        rows.append({
            "issue_id": "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            "issue_type": "provider_export", "severity": "blocking", "status": "open",
            "issue_count": exported_blocking,
            "blocking_reason": "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        })
    if rejected:
        rows.append({
            "issue_id": "REAL_PROVIDER_EXPORT_REJECTED_ROWS_PRESENT",
            "issue_type": "execution", "severity": "blocking", "status": "open",
            "issue_count": rejected,
            "blocking_reason": "REAL_PROVIDER_EXPORT_REJECTED_ROWS_PRESENT",
        })
    return rows


def _text(value: object) -> str:
    if type(value) is bool:
        return "true" if value else "false"
    return str(value)


def validate_sidecar_rows(
    rows: Sequence[Mapping[str, Any]],
    joined_rows: Sequence[Mapping[str, str]],
    *,
    p4: ModuleType | None = None,
) -> bool:
    try:
        actual = [dict(row) for row in rows]
    except (TypeError, ValueError):
        return False
    identity_valid = (
        len(actual) == len(joined_rows) == 11
        and all(tuple(row) == FUTURE_REAL_SIDECAR_COLUMNS for row in actual)
        and [row["binding_row_id"] for row in actual]
        == [f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)]
        and [row["smoke_case_id"] for row in actual]
        == [f"P6C_REAL_{index:06d}" for index in range(1, 12)]
        and all(
            (
                row["binding_row_id"], row["source_pipeline"],
                row["sample_preparation_input_id"], row["sample_execution_id"],
                row["pdb_id"], row["conn_id"], row["raw_target_relative_path"],
                row["expected_raw_sha256"],
            )
            == (
                joined["binding_row_id"], joined["source_pipeline"],
                joined["sample_preparation_input_id"], joined["sample_execution_id"],
                joined["pdb_id"], joined["conn_id"],
                joined["raw_target_relative_path"], joined["expected_raw_sha256"],
            )
            for row, joined in zip(actual, joined_rows)
        )
        and all(
            row["provider_export_status"]
            in ("exported_pass", "exported_blocking", "rejected")
            for row in actual
        )
    )
    if not identity_valid:
        return False
    if p4 is None:
        return True
    try:
        for row in actual:
            status = row["provider_export_status"]
            provider_fields = (
                row["covalent_residue_locator_namespace"],
                row["covalent_residue_insertion_code_state"],
                row["covalent_residue_insertion_code"],
                row["covalent_residue_locator_provenance_source_id"],
                row["covalent_residue_locator_provenance_sha256"],
            )
            if status == "rejected":
                if any(provider_fields):
                    return False
                continue
            expected_source_id = p4.build_locator_provenance_source_id(
                row["sample_preparation_input_id"], row["conn_id"],
                row["residue_partner_side"],
            )
            payload = p4.build_canonical_locator_provenance_payload(
                **{
                    key: row[key]
                    for key in p4.CANONICAL_PAYLOAD_KEYS
                    if key != "schema_version"
                }
            )
            expected_sha = p4.sha256_canonical_locator_provenance_payload(payload)
            if provider_fields != (
                row["locator_namespace"], row["resolved_insertion_state"],
                row["resolved_insertion_value"], expected_source_id, expected_sha,
            ):
                return False
    except (AttributeError, KeyError, TypeError, ValueError):
        return False
    return True


def validate_evidence_rows(
    rows: Sequence[Mapping[str, Any]],
    sidecar_rows: Sequence[Mapping[str, Any]] | None = None,
    joined_rows: Sequence[Mapping[str, str]] | None = None,
) -> bool:
    try:
        actual = [dict(row) for row in rows]
    except (TypeError, ValueError):
        return False
    shape_valid = (
        len(actual) == 11
        and all(tuple(row) == EVIDENCE_COLUMNS for row in actual)
        and [row["execution_evidence_row_id"] for row in actual]
        == [f"P6C_EXECUTION_EVIDENCE_{index:06d}" for index in range(1, 12)]
        and [row["smoke_case_id"] for row in actual]
        == [f"P6C_REAL_{index:06d}" for index in range(1, 12)]
    )
    if not shape_valid:
        return False
    if sidecar_rows is None or joined_rows is None:
        return True
    if len(sidecar_rows) != 11 or len(joined_rows) != 11:
        return False
    return all(
        (
            evidence["binding_row_id"], evidence["smoke_case_id"],
            evidence["pdb_id"], evidence["raw_target_relative_path"],
            evidence["expected_raw_sha256"], evidence["observed_raw_sha256"],
            str(evidence["expected_raw_size_bytes"]),
            str(evidence["observed_raw_size_bytes"]),
        )
        == (
            joined["binding_row_id"], sidecar["smoke_case_id"],
            joined["pdb_id"], joined["raw_target_relative_path"],
            joined["expected_raw_sha256"], sidecar["observed_raw_sha256"],
            joined["expected_raw_size_bytes"], joined["expected_raw_size_bytes"],
        )
        and evidence["raw_secure_read_status"] == "passed"
        and evidence["strict_decode_status"] == "passed"
        and evidence["struct_conn_parse_status"] in ("parsed_loop", "parsed_empty_loop")
        and evidence["atom_site_parse_status"] in ("parsed_loop", "parsed_empty_loop")
        and type(evidence["struct_conn_row_count"]) is int
        and evidence["struct_conn_row_count"] > 0
        and type(evidence["atom_site_row_count"]) is int
        and evidence["atom_site_row_count"] > 0
        and type(evidence["selected_struct_conn_row_ordinal_1based"]) is int
        and evidence["selected_struct_conn_row_ordinal_1based"] > 0
        and evidence["selected_struct_conn_match_count"] == 1
        and type(evidence["selected_atom_site_row_ordinal_1based"]) is int
        and evidence["selected_atom_site_row_ordinal_1based"] > 0
        and evidence["selected_atom_site_match_count"] == 1
        and evidence["residue_partner_side"] == sidecar["residue_partner_side"]
        and evidence["locator_namespace"] == sidecar["locator_namespace"]
        and evidence["provider_export_status"] == sidecar["provider_export_status"]
        and evidence["provider_export_blocking_reason"]
        == sidecar["provider_export_blocking_reason"]
        and evidence["evidence_audit_passed"] is True
        for evidence, sidecar, joined in zip(actual, sidecar_rows, joined_rows)
    )


def build_execution_state(
    *,
    repo_root: Path = REPO_ROOT,
    source_snapshot: FrozenSourceSnapshot | None = None,
    raw_reader: Callable[..., VerifiedRawSource] = secure_read_expected_raw_source,
    schema_validator: Callable[
        [FrozenSourceSnapshot], tuple[bool, dict[str, tuple[str, ...]]]
    ] = _extract_frozen_schema_contract,
    module_loader: Callable[[], tuple[ModuleType, ModuleType]] = _load_runtime_modules,
) -> dict[str, Any]:
    snapshot = source_snapshot or build_frozen_source_snapshot(repo_root)
    source_ok = validate_frozen_source_snapshot(snapshot)
    predecessor_ok = False
    bindings: list[dict[str, str]] = []
    matrix: list[dict[str, str]] = []
    predecessor_manifest: dict[str, Any] = {}
    if source_ok:
        predecessor_ok, bindings, matrix, predecessor_manifest = _validate_p6b_predecessor(snapshot)
    joined = _join_bindings_and_preconditions(bindings, matrix) if predecessor_ok else []
    join_ok = len(joined) == 11
    sidecar: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    extracted_schemas: dict[str, tuple[str, ...]] = {}
    schema_ok = False
    runtime_modules_ok = False
    runtime_module_names: tuple[str, ...] = ()
    # These counters intentionally cover execute_one_binding actions for the
    # real exact11 only.  They exclude P5-B's existing import-time synthetic
    # self-checks and are not process-global Python call telemetry.
    counters = {"raw": 0, "decode": 0, "struct_parse": 0, "atom_parse": 0, "provider": 0}
    modules_ok = False
    if join_ok:
        try:
            schema_ok, extracted_schemas = schema_validator(snapshot)
        except (AttributeError, TypeError, ValueError):
            schema_ok = False
            extracted_schemas = {}
        try:
            if schema_ok:
                p4, p5b = module_loader()
                runtime_module_names = (p4.__name__, p5b.__name__)
                runtime_modules_ok = _validate_runtime_modules(
                    p4, p5b, snapshot=snapshot, repo_root=repo_root
                )
            modules_ok = schema_ok and runtime_modules_ok
        except (ImportError, AttributeError, OSError, TypeError, ValueError):
            modules_ok = False
        if modules_ok:
            for index, binding in enumerate(joined, 1):
                row, audit, observed = execute_one_binding(
                    binding, index, p4=p4, p5b=p5b, repo_root=repo_root,
                    raw_reader=raw_reader,
                )
                sidecar.append(row)
                evidence.append(audit)
                for key in counters:
                    counters[key] += observed[key]
    exported_pass = sum(row.get("provider_export_status") == "exported_pass" for row in sidecar)
    exported_blocking = sum(row.get("provider_export_status") == "exported_blocking" for row in sidecar)
    rejected = sum(row.get("provider_export_status") == "rejected" for row in sidecar)
    provider_rows = sum(
        all(row.get(field) for field in (
            "covalent_residue_locator_namespace",
            "covalent_residue_insertion_code_state",
            "covalent_residue_locator_provenance_source_id",
            "covalent_residue_locator_provenance_sha256",
        )) and row.get("provider_export_status") != "rejected"
        for row in sidecar
    )
    source_ids = [row.get("covalent_residue_locator_provenance_source_id", "") for row in sidecar if row.get("provider_export_status") != "rejected"]
    provenance_hashes = [row.get("covalent_residue_locator_provenance_sha256", "") for row in sidecar if row.get("provider_export_status") != "rejected"]
    insertion_counts = {
        state: sum(row.get("resolved_insertion_state") == state for row in sidecar)
        for state in ("present", "absent", "unknown")
    }
    sidecar_shape = validate_sidecar_rows(sidecar, joined, p4=p4 if modules_ok else None)
    evidence_ok = (
        validate_evidence_rows(evidence, sidecar, joined)
        and all(row["evidence_audit_passed"] is True for row in evidence)
    )
    observations = {
        "source_count": len(snapshot.records) if source_ok else 0,
        "source_structural": snapshot.structural_check_count,
        "source_reads": snapshot.content_read_count,
        "source_hashes": sum(record.sha256 == SOURCE_SHA256[record.relative_path] for record in snapshot.records),
        "predecessor": predecessor_ok,
        "binding_shape": "11x26" if len(bindings) == 11 else "blocked",
        "matrix_shape": "11x31" if len(matrix) == 11 else "blocked",
        "joins": len(joined), "raw_reads": counters["raw"],
        "raw_hashes": sum(row.get("expected_raw_sha256") == row.get("observed_raw_sha256") and bool(row.get("observed_raw_sha256")) for row in sidecar),
        "raw_sizes": sum(str(row.get("expected_raw_size_bytes")) == str(row.get("observed_raw_size_bytes")) for row in evidence),
        "decode": counters["decode"], "struct_parse": counters["struct_parse"],
        "atom_parse": counters["atom_parse"],
        "events": sum(row.get("selected_struct_conn_match_count") == 1 for row in evidence),
        "atoms": sum(row.get("selected_atom_site_match_count") == 1 for row in evidence),
        "provider_calls": counters["provider"], "sidecar_columns": len(FUTURE_REAL_SIDECAR_COLUMNS),
        "sidecar_rows": len(sidecar), "rejected": rejected,
        "exported": exported_pass + exported_blocking, "provider_rows": provider_rows,
        "source_ids": len(set(source_ids)),
        "provenance_hashes": sum(_valid_sha(value) for value in provenance_hashes),
        "evidence": sum(row.get("evidence_audit_passed") is True for row in evidence),
        "admission": False, "backfill": False, "admit": False, "e1": False,
        "candidate": False, "download": False, "training": False,
    }
    contract = _contract_rows(observations)
    execution = {item: False for item, _ in SAFETY_SPECS}
    execution.update({
        "exact_source_reads": source_ok,
        "exact11_raw_secure_read": counters["raw"] == 11,
        "strict_utf8_decode": counters["decode"] == 11,
        "struct_conn_parse": counters["struct_parse"] == 11,
        "atom_site_parse": counters["atom_parse"] == 11,
        "p4_provider_calls": counters["provider"] == 11,
        "sidecar_materialization": sidecar_shape,
    })
    safety = _safety_rows(execution)
    issues = _issue_rows(exported_blocking, rejected)
    all_checks = (
        source_ok and predecessor_ok and join_ok and modules_ok and sidecar_shape
        and rejected == 0 and exported_pass + exported_blocking == 11
        and provider_rows == 11 and len(set(source_ids)) == 11
        and len(provenance_hashes) == 11 and all(_valid_sha(value) for value in provenance_hashes)
        and len(set(provenance_hashes)) == 11 and evidence_ok
        and validate_contract_rows(contract, observations)
        and all(row["contract_passed"] for row in contract)
        and all(row["safety_passed"] for row in safety)
    )
    return {
        "source_snapshot": snapshot, "source_ok": source_ok,
        "predecessor_ok": predecessor_ok, "predecessor_manifest": predecessor_manifest,
        "binding_rows": bindings, "matrix_rows": matrix, "joined_rows": joined,
        "schema_ok": schema_ok, "extracted_schemas": extracted_schemas,
        "runtime_modules_ok": runtime_modules_ok,
        "runtime_module_names": runtime_module_names,
        "modules_ok": modules_ok, "sidecar_rows": sidecar,
        "evidence_rows": evidence, "contract_rows": contract,
        "safety_rows": safety, "issue_rows": issues, "execution": execution,
        "observations": observations, "counters": counters,
        "exported_pass_count": exported_pass,
        "exported_blocking_count": exported_blocking, "rejected_count": rejected,
        "provider_row_count": provider_rows, "source_ids": source_ids,
        "provenance_hashes": provenance_hashes,
        "insertion_counts": insertion_counts, "sidecar_shape_valid": sidecar_shape,
        "evidence_audit_passed": evidence_ok, "all_checks_passed": all_checks,
        "validation_failures": [] if all_checks else [
            name for name, passed in (
                ("source_boundary", source_ok), ("p6b_predecessor", predecessor_ok),
                ("binding_join", join_ok), ("production_modules", modules_ok),
                ("sidecar", sidecar_shape and rejected == 0 and provider_rows == 11),
                ("evidence_audit", evidence_ok),
                ("contract", all(row["contract_passed"] for row in contract)),
                ("safety", all(row["safety_passed"] for row in safety)),
            ) if not passed
        ],
    }


def _csv_value(value: Any) -> str:
    if type(value) is bool:
        return "true" if value else "false"
    return str(value)


def _ensure_output_root(root: Path) -> None:
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("OUTPUT_ROOT_INVALID")
    root.mkdir(parents=True, exist_ok=True)


def _atomic_write_csv(path: Path, columns: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                if tuple(row) != tuple(columns):
                    raise ValueError("CSV_ROW_SCHEMA_MISMATCH")
                writer.writerow({column: _csv_value(row[column]) for column in columns})
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_payload(state: Mapping[str, Any], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    passed = state["all_checks_passed"]
    counts = state["insertion_counts"]
    snapshot = state["source_snapshot"]
    return {
        "stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME,
        "previous_stage": PREVIOUS_STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "all_checks_passed": passed,
        "validation_failures": state["validation_failures"],
        "source_input_count": len(SOURCE_PATHS),
        "source_input_sha256": {path.as_posix(): digest for path, digest in SOURCE_SHA256.items()},
        "source_structural_check_count": snapshot.structural_check_count,
        "source_content_read_count": snapshot.content_read_count,
        "source_boundary_before_content_read": state["source_ok"],
        "output_file_count": len(OUTPUT_FILES), "output_files": list(OUTPUT_FILES),
        "output_sha256": dict(output_sha256),
        "p6b_predecessor_validated": state["predecessor_ok"],
        "binding_count": len(state["joined_rows"]),
        "secure_raw_read_count": state["counters"]["raw"],
        "strict_decode_count": state["counters"]["decode"],
        "struct_conn_parse_count": state["counters"]["struct_parse"],
        "atom_site_parse_count": state["counters"]["atom_parse"],
        "provider_call_count": state["counters"]["provider"],
        "sidecar_column_count": len(FUTURE_REAL_SIDECAR_COLUMNS),
        "sidecar_row_count": len(state["sidecar_rows"]),
        "exported_pass_count": state["exported_pass_count"],
        "exported_blocking_count": state["exported_blocking_count"],
        "rejected_count": state["rejected_count"],
        "present_insertion_count": counts["present"],
        "absent_insertion_count": counts["absent"],
        "unknown_insertion_count": counts["unknown"],
        "provider_row_count": state["provider_row_count"],
        "provenance_source_id_unique_count": len(set(state["source_ids"])),
        "provenance_sha_valid_count": sum(_valid_sha(value) for value in state["provenance_hashes"]),
        "provenance_sha_unique_count": len(set(state["provenance_hashes"])),
        "evidence_audit_passed_count": sum(row["evidence_audit_passed"] is True for row in state["evidence_rows"]),
        "real_provider_export_execution_smoke_passed": passed,
        "real_provider_rows_materialized_current_step": passed and state["provider_row_count"] == 11,
        "ready_for_real_provider_sidecar_integration": passed,
        "insertion_code_provenance_export_ready_for_real_samples": passed,
        "admit_004_rule_logic_ready": False,
        "ready_for_e1_residue_identity_semantics_design": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "admission_records_modified_current_step": False,
        "real_samples_backfilled_current_step": 0,
        "raw_files_modified_current_step": False,
        "network_access_used_current_step": False,
        "download_attempted_current_step": False,
        "recommended_next_step": RECOMMENDED_NEXT_STEP if passed else BLOCKED_NEXT_STEP,
    }


def run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    root = output_root if output_root.is_absolute() else repo_root / output_root
    _ensure_output_root(root)
    state = build_execution_state(repo_root=repo_root)
    outputs = (
        (CONTRACT_FILENAME, CONTRACT_COLUMNS, state["contract_rows"]),
        (SIDECAR_FILENAME, FUTURE_REAL_SIDECAR_COLUMNS, state["sidecar_rows"]),
        (EVIDENCE_FILENAME, EVIDENCE_COLUMNS, state["evidence_rows"]),
        (SAFETY_FILENAME, SAFETY_COLUMNS, state["safety_rows"]),
        (ISSUE_FILENAME, ISSUE_COLUMNS, state["issue_rows"]),
    )
    for filename, columns, rows in outputs:
        _atomic_write_csv(root / filename, columns, rows)
    hashes = {filename: _file_sha256(root / filename) for filename in CSV_OUTPUTS}
    manifest = _manifest_payload(state, hashes)
    _atomic_write_json(root / MANIFEST_FILENAME, manifest)
    return {"state": state, "manifest": manifest}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1()
    if not result["manifest"]["all_checks_passed"]:
        raise SystemExit("P6-C smoke blocked: " + ",".join(result["manifest"]["validation_failures"]))
