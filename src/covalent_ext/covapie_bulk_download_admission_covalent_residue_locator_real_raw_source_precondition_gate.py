"""Step14AU-E0-P6-B real raw-source precondition gate v1.

The gate validates nine frozen metadata/code sources before parsing any source
content, completes all eleven authority joins before raw access, and then uses
Linux ``dir_fd``/``O_NOFOLLOW`` file-descriptor walks to hash only the exact
bound raw paths.  Raw bytes are never decoded or parsed.
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
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

STEP_LABEL = "Step14AU-E0-P6-B"
STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_"
    "precondition_gate_v1"
)
PREVIOUS_STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_historical_raw_"
    "fingerprint_authority_consolidation_gate_v1"
)
MANIFEST_SCHEMA_VERSION = (
    "covapie_covalent_residue_locator_real_raw_source_precondition_gate_v1_"
    "manifest_v1"
)
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_covalent_residue_locator_real_provider_export_execution_"
    "smoke_v1"
)
BLOCKED_NEXT_STEP = (
    "resolve_covapie_covalent_residue_locator_real_raw_source_precondition_gate_"
    "blockers"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
P6B0_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_historical_raw_fingerprint_authority_consolidation_gate_v1"
)
P6A_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_real_parser_provider_pipeline_integration_design_gate_v1"
)
EXPANSION_ROOT = Path(
    "data/derived/covalent_small/covapie_independent_group_expansion_struct_conn_"
    "crosscheck_smoke_v0"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_real_raw_source_precondition_gate_v1"
)

SOURCE_PATHS = (
    Path("src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate.py"),
    P6B0_ROOT / "covapie_covalent_residue_locator_historical_raw_fingerprint_authority_contract.csv",
    P6B0_ROOT / "covapie_covalent_residue_locator_historical_raw_fingerprint_authority.csv",
    P6B0_ROOT / "covapie_covalent_residue_locator_historical_raw_fingerprint_source_boundary_audit.csv",
    P6B0_ROOT / "covapie_covalent_residue_locator_historical_raw_fingerprint_safety_audit.csv",
    P6B0_ROOT / "covapie_covalent_residue_locator_historical_raw_fingerprint_issue_inventory.csv",
    P6B0_ROOT / "covapie_covalent_residue_locator_historical_raw_fingerprint_authority_manifest.json",
    P6A_ROOT / "covapie_covalent_residue_locator_real_sample_binding_matrix.csv",
    EXPANSION_ROOT / "covapie_struct_conn_raw_fingerprint_audit.csv",
)
SOURCE_SHA256 = dict(zip(
    map(str, SOURCE_PATHS),
    (
        "672509b4a276087397499fcf956589375804230aae525b748d8ca4354ddb0e21",
        "7b26119e9eafaba15d547b955e9faa839e0a283c9bf61f714e7bc02d2594af20",
        "71cc0a46100e42318367514c86154493592eb0e82868178b2184d858c2cf2eaa",
        "40baae4a74fa8e530ef65bf401562b26bc06b0ea18649f78a2344ca09db26e0b",
        "9f00a983077b0fd95f0ef11c26fd6098bdbfab51edae1b70ea877621ee9c255f",
        "3105f89fded382828717d6e742391b0e85610d9784c0e4ec0309bd2a432d3146",
        "4712bddaa9d41e5b83dc84ed82e4286fe1d08f1a5835aa6749f6f003f193387c",
        "61a1e77c81a8a0d335bbafd454d2926be442c2dd794bce8b75dc8a1451f78e98",
        "7533c44a7867b6aa11f3766a02ce5d9a93c3099a247dbd95ad5a7f241d81c231",
    ),
))

P6B0_AUTHORITY_PATH = SOURCE_PATHS[2]
P6B0_MANIFEST_PATH = SOURCE_PATHS[6]
P6A_BINDING_PATH = SOURCE_PATHS[7]
EXPANSION_AUTHORITY_PATH = SOURCE_PATHS[8]
CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
HISTORICAL_IDENTITIES = (("6BV6", "JUG"), ("6BV8", "JUG"), ("6BV5", "JUG"))
EXPANSION_IDENTITIES = (
    ("1AEC", "E64"), ("1AIM", "ZYA"), ("1AU3", "PCM"),
    ("1AU4", "INP"), ("1AYU", "INA"), ("1AYV", "IN6"),
    ("1AYW", "IN3"), ("1B02", "UFP"),
)
HISTORICAL_RAW_PATHS = (
    "data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0/6bv6.cif",
    "data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0/6bv8.cif",
    "data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0/6bv5.cif",
)
EXPANSION_RAW_PATHS = tuple(
    "data/raw/covalent_sources/covpdb/independent_group_expansion_batch_000001/"
    + pdb_id.lower() + ".cif"
    for pdb_id, _ligand in EXPANSION_IDENTITIES
)
EXACT_RAW_PATHS = HISTORICAL_RAW_PATHS + EXPANSION_RAW_PATHS
DOMAIN_BLOCKING_REASONS = (
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
    "COVALENT_EVIDENCE_ENUM_UNRESOLVED",
    "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED",
    "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED",
    "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
    "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
    "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED",
    "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED",
    "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED",
)

P6A_BINDING_HEADER = (
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
P6B0_AUTHORITY_HEADER = (
    "authority_row_id", "binding_row_id", "sample_preparation_input_id", "pdb_id",
    "ligand_comp_id", "raw_target_relative_path", "availability_source_row_id",
    "integrity_source_row_id", "independence_source_row_id", "expected_sha256",
    "prior_observed_sha256", "sha256_matches", "independence_sha256_before",
    "independence_sha256_after", "independence_sha256_unchanged",
    "expected_file_size_bytes", "prior_observed_file_size_bytes",
    "file_size_matches", "identity_match", "raw_path_match",
    "all_source_statuses_passed", "authority_source_count", "authority_status",
    "permitted_for_raw_source_precondition", "blocking_reason",
)
EXPANSION_AUTHORITY_HEADER = (
    "raw_fingerprint_audit_id", "shortlist_rank", "pdb_id", "expected_het_id",
    "raw_filename", "raw_path", "expected_sha256", "observed_sha256",
    "sha256_matches", "file_size_bytes", "raw_file_exists",
    "permitted_for_struct_conn_parse", "fingerprint_audit_status",
    "blocking_reasons",
)
MATRIX_COLUMNS = (
    "precondition_row_id", "binding_row_id", "source_pipeline",
    "sample_preparation_input_id", "pdb_id", "ligand_comp_id",
    "raw_target_relative_path", "authority_scope",
    "expected_authority_source_relative_path", "expected_authority_row_id",
    "authority_join_status", "expected_sha256", "expected_file_size_bytes",
    "observed_sha256", "observed_file_size_bytes", "sha256_matches",
    "file_size_matches", "raw_path_exists", "raw_path_regular_file",
    "raw_path_symlink", "raw_path_confined_without_symlink", "raw_path_unique",
    "raw_git_tracking_state", "raw_git_worktree_clean", "raw_git_index_clean",
    "pre_hash_stat_fingerprint", "post_hash_stat_fingerprint", "stat_stable",
    "raw_source_precondition_status",
    "ready_for_real_provider_export_execution_smoke", "blocking_reason",
)
AUTHORITY_AUDIT_COLUMNS = (
    "authority_source_order", "authority_scope", "authority_source_relative_path",
    "authority_source_sha256", "authority_row_count", "binding_match_count",
    "expected_hash_count", "prior_observed_match_count", "expected_size_count",
    "duplicate_identity_count", "conflicting_hash_count", "authority_check_passed",
    "blocking_reason",
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
CONTRACT_FILENAME = "covapie_covalent_residue_locator_real_raw_source_precondition_contract.csv"
MATRIX_FILENAME = "covapie_covalent_residue_locator_real_raw_source_precondition_matrix.csv"
AUTHORITY_AUDIT_FILENAME = "covapie_covalent_residue_locator_real_raw_source_authority_audit.csv"
SAFETY_FILENAME = "covapie_covalent_residue_locator_real_raw_source_safety_audit.csv"
ISSUE_FILENAME = "covapie_covalent_residue_locator_real_raw_source_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_covalent_residue_locator_real_raw_source_precondition_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, MATRIX_FILENAME, AUTHORITY_AUDIT_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)
SECTION_NAMES = (
    "source_boundary", "p6b0_predecessor", "p6a_binding", "authority_mapping",
    "raw_access", "precondition_contract", "issue_inventory", "safety",
)
CHUNK_SIZE = 1024 * 1024
STAT_FIELDS = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")


@dataclass(frozen=True)
class CsvDocument:
    header: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    status: str
    blocking_reason: str


@dataclass(frozen=True)
class JsonDocument:
    payload: dict[str, Any]
    status: str
    blocking_reason: str


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    content_bytes: bytes
    sha256: str
    size_bytes: int
    pre_stat_fingerprint: tuple[int, ...]
    post_stat_fingerprint: tuple[int, ...]


@dataclass(frozen=True)
class RepoRootIdentity:
    lexical_absolute_path: str
    stat_fingerprint: tuple[int, int, int]


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    repo_root_identity: RepoRootIdentity
    records: tuple[FrozenSourceRecord, ...]
    source_rows: tuple[dict[str, Any], ...]
    status: str
    blocking_reason: str
    source_content_read_count: int


@dataclass(frozen=True)
class RawObservation:
    observed_sha256: str = ""
    observed_size: int = 0
    exists: bool = False
    regular: bool = False
    symlink: bool = False
    confined: bool = False
    pre_fingerprint: str = ""
    post_fingerprint: str = ""
    stat_stable: bool = False
    bytes_read: int = 0
    directory_component_open_count: int = 0
    final_entry_stat_performed: bool = False
    file_fd_opened: bool = False
    fd_fstat_performed: bool = False
    read_completed: bool = False
    hash_completed: bool = False
    blocking_reason: str = "RAW_SOURCE_ACCESS_FAILED"


def _valid_hash(value: object) -> bool:
    return type(value) is str and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _valid_size(value: object) -> bool:
    return type(value) is str and value.isdecimal() and int(value) > 0


def _csv_true(value: object) -> bool:
    return value in ("true", "True")


def _safe_raw_relative_path(value: object) -> bool:
    if type(value) is not str or not value or value != value.strip() or "\\" in value or "\x00" in value:
        return False
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value):
        return False
    parts = value.split("/")
    if any(part in ("", ".", "..", "?") for part in parts):
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and path.as_posix() == value
        and path.parts[:3] == ("data", "raw", "covalent_sources")
        and path.suffix in (".cif", ".mmcif")
    )


def _git(args: Sequence[str], repo_root: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo_root, text=True, capture_output=True, check=False
    )


def _safe_source_relative_path(value: object) -> bool:
    return (
        type(value) is type(SOURCE_PATHS[0])
        and not value.is_absolute()
        and bool(value.parts)
        and all(part not in ("", ".", "..") for part in value.parts)
        and value.as_posix() == str(value)
    )


def _repo_root_identity(repo_root: Path) -> RepoRootIdentity | None:
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptor: int | None = None
    try:
        raw_path = os.fspath(repo_root)
        if type(raw_path) is not str:
            return None
        lexical_absolute_path = os.path.abspath(raw_path)
        descriptor = os.open(lexical_absolute_path, directory_flags)
        root_stat = os.fstat(descriptor)
        fingerprint = (
            int(root_stat.st_dev), int(root_stat.st_ino), int(root_stat.st_mode),
        )
        if fingerprint[1] <= 0 or not stat.S_ISDIR(fingerprint[2]):
            return None
        return RepoRootIdentity(lexical_absolute_path, fingerprint)
    except (OSError, TypeError, ValueError):
        return None
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _empty_repo_root_identity() -> RepoRootIdentity:
    return RepoRootIdentity("", (0, 0, 0))


def _validate_repo_root_identity(identity: object, repo_root: Path) -> bool:
    if type(identity) is not RepoRootIdentity:
        return False
    fingerprint = identity.stat_fingerprint
    if (
        type(identity.lexical_absolute_path) is not str
        or type(fingerprint) is not tuple
        or len(fingerprint) != 3
        or any(type(value) is not int for value in fingerprint)
        or fingerprint[0] < 0
        or fingerprint[1] <= 0
        or not stat.S_ISDIR(fingerprint[2])
    ):
        return False
    current = _repo_root_identity(repo_root)
    return current is not None and current == identity


def _validate_source_stat_fingerprint(
    fingerprint: object,
    expected_size: int,
) -> bool:
    if (
        type(fingerprint) is not tuple
        or len(fingerprint) != len(STAT_FIELDS)
        or any(type(value) is not int for value in fingerprint)
        or type(expected_size) is not int
        or expected_size < 0
    ):
        return False
    device, inode, mode, link_count, size, mtime_ns, ctime_ns = fingerprint
    return (
        device >= 0
        and inode > 0
        and stat.S_ISREG(mode)
        and link_count >= 1
        and size == expected_size
        and mtime_ns >= 0
        and ctime_ns >= 0
    )


def _source_structural_stat(repo_root: Path, relative: Path) -> os.stat_result | None:
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptors: list[int] = []
    try:
        current_fd = os.open(str(repo_root), directory_flags)
        descriptors.append(current_fd)
        for component in relative.parts[:-1]:
            current_fd = os.open(component, directory_flags, dir_fd=current_fd)
            descriptors.append(current_fd)
        return os.stat(relative.parts[-1], dir_fd=current_fd, follow_symlinks=False)
    except OSError:
        return None
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _secure_read_frozen_source(
    repo_root: Path,
    relative: Path,
    expected_sha256: str,
    *,
    read_fn: Callable[[int, int], bytes] = os.read,
    after_source_read_hook: Callable[[Path, int], None] | None = None,
) -> tuple[FrozenSourceRecord | None, str, bool]:
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptors: list[int] = []
    content_read = False
    try:
        current_fd = os.open(str(repo_root), directory_flags)
        descriptors.append(current_fd)
        for component in relative.parts[:-1]:
            current_fd = os.open(component, directory_flags, dir_fd=current_fd)
            descriptors.append(current_fd)
        final_name = relative.parts[-1]
        entry_stat = os.stat(final_name, dir_fd=current_fd, follow_symlinks=False)
        if stat.S_ISLNK(entry_stat.st_mode):
            return None, "SOURCE_FINAL_ENTRY_SYMLINK_REJECTED", False
        if not stat.S_ISREG(entry_stat.st_mode):
            return None, "SOURCE_NOT_REGULAR_FILE", False
        file_fd = os.open(final_name, file_flags, dir_fd=current_fd)
        descriptors.append(file_fd)
        pre = os.fstat(file_fd)
        if not stat.S_ISREG(pre.st_mode):
            return None, "SOURCE_NOT_REGULAR_FILE", False
        if any(
            getattr(entry_stat, field) != getattr(pre, field)
            for field in ("st_dev", "st_ino", "st_mode")
        ):
            return None, "SOURCE_CHANGED_DURING_OPEN", False
        chunks: list[bytes] = []
        while True:
            chunk = read_fn(file_fd, CHUNK_SIZE)
            if not chunk:
                break
            if type(chunk) is not bytes:
                return None, "SOURCE_READ_RESULT_NOT_BYTES", content_read
            chunks.append(chunk)
            content_read = True
        content_bytes = b"".join(chunks)
        if after_source_read_hook is not None:
            after_source_read_hook(relative, file_fd)
        post = os.fstat(file_fd)
        path_stat = os.stat(final_name, dir_fd=current_fd, follow_symlinks=False)
        pre_fingerprint = tuple(int(getattr(pre, field)) for field in STAT_FIELDS)
        post_fingerprint = tuple(int(getattr(post, field)) for field in STAT_FIELDS)
        path_fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
        path_stable = all(getattr(post, field) == getattr(path_stat, field) for field in path_fields)
        if pre_fingerprint != post_fingerprint or not path_stable:
            return None, "SOURCE_CHANGED_DURING_READ", content_read
        if len(content_bytes) != post.st_size:
            return None, "SOURCE_PARTIAL_READ", content_read
        observed_sha256 = hashlib.sha256(content_bytes).hexdigest()
        if observed_sha256 != expected_sha256:
            return None, "SOURCE_SHA256_MISMATCH", content_read
        return FrozenSourceRecord(
            relative_path=relative,
            content_bytes=content_bytes,
            sha256=observed_sha256,
            size_bytes=len(content_bytes),
            pre_stat_fingerprint=pre_fingerprint,
            post_stat_fingerprint=post_fingerprint,
        ), "", content_read
    except FileNotFoundError:
        return None, "SOURCE_MISSING", content_read
    except NotADirectoryError:
        return None, "SOURCE_PARENT_NOT_DIRECTORY", content_read
    except OSError:
        return None, "SOURCE_SECURE_FD_ACCESS_FAILED", content_read
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT,
    *,
    git_provider: Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]] = _git,
    read_fn: Callable[[int, int], bytes] = os.read,
    after_boundary_hook: Callable[[], None] | None = None,
    after_source_read_hook: Callable[[Path, int], None] | None = None,
) -> FrozenSourceSnapshot:
    repo_root_identity = _repo_root_identity(repo_root)
    if repo_root_identity is None:
        return FrozenSourceSnapshot(
            _empty_repo_root_identity(), (), (), "blocked",
            "REPO_ROOT_IDENTITY_UNAVAILABLE", 0,
        )
    structural: list[dict[str, Any]] = []
    boundary_ok = True
    for order, relative in enumerate(SOURCE_PATHS, 1):
        expected = SOURCE_SHA256.get(str(relative), "")
        path_safe = _safe_source_relative_path(relative)
        tracked = path_safe and git_provider(
            ("ls-files", "--error-unmatch", "--", str(relative)), repo_root
        ).returncode == 0
        entry_stat = _source_structural_stat(repo_root, relative) if path_safe else None
        regular = entry_stat is not None and stat.S_ISREG(entry_stat.st_mode)
        symlink = entry_stat is not None and stat.S_ISLNK(entry_stat.st_mode)
        passed = bool(expected) and tracked and regular and not symlink and path_safe
        boundary_ok = boundary_ok and passed
        structural.append({
            "source_order": order,
            "source_relative_path": str(relative),
            "sha256_expected": expected,
            "tracked": tracked,
            "regular_file": regular,
            "symlink": symlink,
            "sha256_observed": "",
            "source_check_passed": False,
            "blocking_reason": "" if passed else "SOURCE_BOUNDARY_CHECK_FAILED",
        })
    if not boundary_ok:
        for row in structural:
            row["blocking_reason"] = "SOURCE_BOUNDARY_CHECK_FAILED"
        return FrozenSourceSnapshot(
            repo_root_identity, (), tuple(structural), "blocked",
            "SOURCE_BOUNDARY_CHECK_FAILED", 0,
        )
    if after_boundary_hook is not None:
        after_boundary_hook()
    records: list[FrozenSourceRecord] = []
    content_read_count = 0
    for index, relative in enumerate(SOURCE_PATHS):
        record, reason, content_read = _secure_read_frozen_source(
            repo_root, relative, SOURCE_SHA256[str(relative)], read_fn=read_fn,
            after_source_read_hook=after_source_read_hook,
        )
        content_read_count += int(content_read)
        if record is None:
            structural[index]["blocking_reason"] = reason
            return FrozenSourceSnapshot(
                repo_root_identity, (), tuple(structural), "blocked", reason,
                content_read_count,
            )
        records.append(record)
        structural[index].update({
            "sha256_observed": record.sha256,
            "source_check_passed": True,
            "blocking_reason": "",
        })
    return FrozenSourceSnapshot(
        repo_root_identity, tuple(records), tuple(structural), "passed", "",
        content_read_count,
    )


def _source_rows(repo_root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    return [dict(row) for row in _build_frozen_source_snapshot(repo_root).source_rows]


def _canonical_source_rows() -> list[dict[str, Any]]:
    return [{
        "source_order": i,
        "source_relative_path": str(path),
        "sha256_expected": SOURCE_SHA256[str(path)],
        "tracked": True,
        "regular_file": True,
        "symlink": False,
        "sha256_observed": SOURCE_SHA256[str(path)],
        "source_check_passed": True,
        "blocking_reason": "",
    } for i, path in enumerate(SOURCE_PATHS, 1)]


def validate_source_rows(rows: Sequence[Mapping[str, Any]]) -> bool:
    return list(rows) == _canonical_source_rows()


def _parse_csv_bytes(content_bytes: bytes) -> CsvDocument:
    try:
        text = content_bytes.decode("utf-8", errors="strict")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if reader.fieldnames is None:
            return CsvDocument((), (), "blocked", "CSV_HEADER_MISSING")
        header = tuple(reader.fieldnames)
        if not header or len(set(header)) != len(header) or any(not item for item in header):
            return CsvDocument(header, (), "blocked", "CSV_HEADER_INVALID")
        rows = []
        for row in reader:
            if None in row or tuple(row) != header or any(type(v) is not str for v in row.values()):
                return CsvDocument(header, tuple(rows), "blocked", "CSV_ROW_INVALID")
            rows.append(dict(row))
        if not rows:
            return CsvDocument(header, (), "blocked", "CSV_ROWS_EMPTY")
        return CsvDocument(header, tuple(rows), "passed", "")
    except (UnicodeError, csv.Error):
        return CsvDocument((), (), "blocked", "CSV_READ_FAILED")


def _snapshot_record(path: Path, snapshot: FrozenSourceSnapshot) -> FrozenSourceRecord | None:
    if (
        snapshot.status != "passed"
        or not validate_source_rows(snapshot.source_rows)
        or len(snapshot.records) != len(SOURCE_PATHS)
        or path not in SOURCE_PATHS
    ):
        return None
    matches = [record for record in snapshot.records if record.relative_path == path]
    return matches[0] if len(matches) == 1 else None


def validate_frozen_source_snapshot(
    snapshot: FrozenSourceSnapshot,
    repo_root: Path,
) -> bool:
    return (
        type(snapshot) is FrozenSourceSnapshot
        and _validate_repo_root_identity(snapshot.repo_root_identity, repo_root)
        and snapshot.status == "passed"
        and snapshot.blocking_reason == ""
        and snapshot.source_content_read_count == len(SOURCE_PATHS)
        and validate_source_rows(snapshot.source_rows)
        and len(snapshot.records) == len(SOURCE_PATHS)
        and tuple(record.relative_path for record in snapshot.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and type(record.content_bytes) is bytes
            and type(record.size_bytes) is int
            and record.size_bytes >= 0
            and record.sha256 == SOURCE_SHA256[str(record.relative_path)]
            and hashlib.sha256(record.content_bytes).hexdigest() == record.sha256
            and len(record.content_bytes) == record.size_bytes
            and record.pre_stat_fingerprint == record.post_stat_fingerprint
            and _validate_source_stat_fingerprint(
                record.pre_stat_fingerprint, record.size_bytes
            )
            and _validate_source_stat_fingerprint(
                record.post_stat_fingerprint, record.size_bytes
            )
            for record in snapshot.records
        )
    )


def _read_frozen_csv(path: Path, snapshot: FrozenSourceSnapshot) -> CsvDocument:
    record = _snapshot_record(path, snapshot)
    if record is None:
        return CsvDocument((), (), "blocked", "SOURCE_ACCESS_NOT_ALLOWED")
    return _parse_csv_bytes(record.content_bytes)


def _parse_json_bytes(content_bytes: bytes) -> JsonDocument:
    try:
        payload = json.loads(content_bytes.decode("utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return JsonDocument({}, "blocked", "JSON_READ_FAILED")
    if type(payload) is not dict:
        return JsonDocument({}, "blocked", "JSON_PAYLOAD_NOT_OBJECT")
    return JsonDocument(payload, "passed", "")


def _read_frozen_json(path: Path, snapshot: FrozenSourceSnapshot) -> JsonDocument:
    record = _snapshot_record(path, snapshot)
    if record is None:
        return JsonDocument({}, "blocked", "SOURCE_ACCESS_NOT_ALLOWED")
    return _parse_json_bytes(record.content_bytes)


def _p6b0_checks(manifest: Mapping[str, Any], document: CsvDocument) -> dict[str, bool]:
    rows = list(document.rows)
    return {
        "document": document.status == "passed" and document.header == P6B0_AUTHORITY_HEADER,
        "stage": manifest.get("stage") == PREVIOUS_STAGE,
        "step": manifest.get("step_label") == "Step14AU-E0-P6-B0",
        "all_checks": manifest.get("all_checks_passed") is True and manifest.get("validation_failures") == [],
        "consolidation": manifest.get("historical_raw_fingerprint_authority_consolidation_passed") is True,
        "counts": (manifest.get("historical_authority_row_count"), manifest.get("authority_passed_count"), manifest.get("authority_blocked_count")) == (3, 3, 0),
        "permitted": len(rows) == 3 and all(row.get("permitted_for_raw_source_precondition") == "true" for row in rows),
        "no_self_certification": manifest.get("current_raw_used_to_define_expected_hash") is False,
        "ready": manifest.get("ready_for_real_raw_source_precondition_gate") is True,
        "identities": [(r.get("pdb_id"), r.get("ligand_comp_id")) for r in rows] == list(HISTORICAL_IDENTITIES),
        "binding_ids": [r.get("binding_row_id") for r in rows] == [f"REAL_LOCATOR_BINDING_{i:06d}" for i in range(1, 4)],
        "row_truth": len(rows) == 3 and all(
            r.get("authority_status") == "passed"
            and r.get("blocking_reason") == ""
            and _valid_hash(r.get("expected_sha256"))
            and r.get("expected_sha256") == r.get("prior_observed_sha256") == r.get("independence_sha256_before") == r.get("independence_sha256_after")
            and r.get("sha256_matches") == r.get("independence_sha256_unchanged") == "true"
            and _valid_size(r.get("expected_file_size_bytes"))
            and r.get("expected_file_size_bytes") == r.get("prior_observed_file_size_bytes")
            and r.get("file_size_matches") == "true"
            and all(r.get(key) for key in ("availability_source_row_id", "integrity_source_row_id", "independence_source_row_id"))
            for r in rows
        ),
    }


def _p6a_checks(document: CsvDocument) -> dict[str, bool]:
    rows = list(document.rows)
    identities = HISTORICAL_IDENTITIES + EXPANSION_IDENTITIES
    return {
        "document": document.status == "passed" and document.header == P6A_BINDING_HEADER,
        "shape": len(rows) == 11 and all(tuple(row) == P6A_BINDING_HEADER for row in rows),
        "order": [r.get("binding_row_id") for r in rows] == [f"REAL_LOCATOR_BINDING_{i:06d}" for i in range(1, 12)],
        "identities": [(r.get("pdb_id"), r.get("ligand_comp_id")) for r in rows] == list(identities),
        "sources": len(rows) == 11 and all(r.get("source_pipeline") == ("historical_sample_preparation_execution_smoke_v0" if i < 3 else "independent_group_expansion_batch_sample_preparation_execution_smoke_v0") for i, r in enumerate(rows)),
        "status": len(rows) == 11 and all(
            r.get("metadata_join_status") == "one_to_one_metadata_join_complete"
            and r.get("raw_path_persisted") == "true"
            and r.get("real_export_execution_allowed_current_step") == "false"
            and r.get("binding_status") == "design_bound_raw_source_precondition_pending"
            and r.get("blocking_reason") == "REAL_RAW_SOURCE_SHA256_PRECONDITION_NOT_YET_FROZEN"
            and _safe_raw_relative_path(r.get("raw_target_relative_path"))
            for r in rows
        ),
    }


def _expansion_checks(document: CsvDocument) -> dict[str, bool]:
    rows = list(document.rows)
    return {
        "document": document.status == "passed" and document.header == EXPANSION_AUTHORITY_HEADER,
        "count": len(rows) == 8,
        "ranks": [r.get("shortlist_rank") for r in rows] == [str(i) for i in range(1, 9)],
        "identities": [(r.get("pdb_id"), r.get("expected_het_id")) for r in rows] == list(EXPANSION_IDENTITIES),
        "truth": len(rows) == 8 and all(
            _valid_hash(r.get("expected_sha256"))
            and r.get("expected_sha256") == r.get("observed_sha256")
            and r.get("sha256_matches") == "True"
            and _valid_size(r.get("file_size_bytes"))
            and r.get("raw_file_exists") == "True"
            and r.get("permitted_for_struct_conn_parse") == "True"
            and r.get("fingerprint_audit_status") == "passed"
            and r.get("blocking_reasons") == ""
            and r.get("raw_filename") == r.get("pdb_id", "").lower() + ".cif"
            and _safe_raw_relative_path(r.get("raw_path"))
            for r in rows
        ),
    }


def _authority_mapping(
    bindings: CsvDocument, historical: CsvDocument, expansion: CsvDocument
) -> list[dict[str, Any]]:
    historical_rows_valid = (
        historical.status == "passed"
        and historical.header == P6B0_AUTHORITY_HEADER
        and len(historical.rows) == 3
        and all(
            row.get("authority_status") == "passed"
            and row.get("permitted_for_raw_source_precondition") == "true"
            and row.get("blocking_reason") == ""
            for row in historical.rows
        )
    )
    if not historical_rows_valid or not all(_p6a_checks(bindings).values()) or not all(_expansion_checks(expansion).values()):
        return []
    by_historical = {(r["pdb_id"], r["ligand_comp_id"]): r for r in historical.rows}
    by_expansion = {(r["pdb_id"], r["expected_het_id"]): r for r in expansion.rows}
    mapping = []
    for index, binding in enumerate(bindings.rows):
        identity = (binding["pdb_id"], binding["ligand_comp_id"])
        if index < 3:
            authority = by_historical.get(identity)
            if authority is None:
                return []
            expected = {
                "authority_scope": "historical_committed_consensus",
                "authority_source": str(P6B0_AUTHORITY_PATH),
                "authority_row_id": authority["authority_row_id"],
                "binding_row_id": authority["binding_row_id"],
                "sample_id": authority["sample_preparation_input_id"],
                "pdb_id": authority["pdb_id"],
                "ligand": authority["ligand_comp_id"],
                "raw_path": authority["raw_target_relative_path"],
                "sha256": authority["expected_sha256"],
                "prior_sha256": authority["prior_observed_sha256"],
                "size": authority["expected_file_size_bytes"],
            }
        else:
            authority = by_expansion.get(identity)
            if authority is None:
                return []
            expected = {
                "authority_scope": "expansion_committed_fingerprint",
                "authority_source": str(EXPANSION_AUTHORITY_PATH),
                "authority_row_id": authority["raw_fingerprint_audit_id"],
                "binding_row_id": f"REAL_LOCATOR_BINDING_{index + 1:06d}",
                "sample_id": binding["sample_preparation_input_id"],
                "pdb_id": authority["pdb_id"],
                "ligand": authority["expected_het_id"],
                "raw_path": authority["raw_path"],
                "sha256": authority["expected_sha256"],
                "prior_sha256": authority["observed_sha256"],
                "size": authority["file_size_bytes"],
            }
        binding_tuple = (
            binding["binding_row_id"], binding["sample_preparation_input_id"],
            binding["pdb_id"], binding["ligand_comp_id"], binding["raw_target_relative_path"],
        )
        authority_tuple = (
            expected["binding_row_id"], expected["sample_id"], expected["pdb_id"],
            expected["ligand"], expected["raw_path"],
        )
        if binding_tuple != authority_tuple or expected["sha256"] != expected["prior_sha256"] or not _valid_hash(expected["sha256"]) or not _valid_size(expected["size"]):
            return []
        mapping.append({**expected, "source_pipeline": binding["source_pipeline"]})
    identities = [(m["pdb_id"], m["ligand"]) for m in mapping]
    paths = [m["raw_path"] for m in mapping]
    if len(mapping) != 11 or len(set(identities)) != 11 or len(set(paths)) != 11:
        return []
    return mapping


MAPPING_COLUMNS = (
    "authority_scope", "authority_source", "authority_row_id", "binding_row_id",
    "sample_id", "pdb_id", "ligand", "raw_path", "sha256",
    "prior_sha256", "size", "source_pipeline",
)
EXPECTED_MAPPING_SPECS = (
    ("HISTORICAL_RAW_AUTHORITY_000001", "CYS_SG_SAMPLE_PREP_INPUT_000001", "6BV6", "JUG", "5ca85f5ef727d9bc8c7a8e2254be8169fad6574ecfaa1a40d8feee5af594e65a", "810077"),
    ("HISTORICAL_RAW_AUTHORITY_000002", "CYS_SG_SAMPLE_PREP_INPUT_000002", "6BV8", "JUG", "a8cd3f5b104906343e7d6d882b85f41ed1ca1a3ad15e0a7b9c77df5987e4fcae", "814211"),
    ("HISTORICAL_RAW_AUTHORITY_000003", "CYS_SG_SAMPLE_PREP_INPUT_000003", "6BV5", "JUG", "78f68b15590fdb114ec45cdc24e42c6b908b061b5b7942ece1027acd302442b8", "826313"),
    ("FP_000001", "CYS_SG_EXPANSION_PREP_000001", "1AEC", "E64", "cfaf7e2b3fb2ba4ad7fa7667d6bb826fb45303db0c881bcdb280cb7a7da968ea", "283760"),
    ("FP_000002", "CYS_SG_EXPANSION_PREP_000002", "1AIM", "ZYA", "28c952563def4bfbbd33aa486d57f2e5e8efb169ebc93ec8f99a98e07663b8b8", "268208"),
    ("FP_000003", "CYS_SG_EXPANSION_PREP_000003", "1AU3", "PCM", "e4607c28b7741c8495bb78efb9f20af0be4f66e69f04732f1cd2e5adcd257ed2", "228535"),
    ("FP_000004", "CYS_SG_EXPANSION_PREP_000004", "1AU4", "INP", "13d7897786967a7abe8f574bf6192c4828ec6ae8ecff64f0c0410ce5dd42d12c", "227571"),
    ("FP_000005", "CYS_SG_EXPANSION_PREP_000005", "1AYU", "INA", "7a50b94adc96bef4222da8e55e7cdb3e854cdd80015fcf76b3a54f4cbf6a2830", "230527"),
    ("FP_000006", "CYS_SG_EXPANSION_PREP_000006", "1AYV", "IN6", "2da1f39b0d86c6285b06dc226004136356a6d45dc32255ed74505836a305519e", "239038"),
    ("FP_000007", "CYS_SG_EXPANSION_PREP_000007", "1AYW", "IN3", "e8402436f23cbccc6317342c5a2f0ffb01acb0ced0ed29df5f6029e9fabcb07d", "236287"),
    ("FP_000008", "CYS_SG_EXPANSION_PREP_000008", "1B02", "UFP", "8566dd300d42eb0301305b0b03eaa876b8d6fc311bf34c9ddf7be7203bf75aa9", "308673"),
)


def _canonical_authority_mapping() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, (authority_id, sample_id, pdb_id, ligand, digest, size) in enumerate(EXPECTED_MAPPING_SPECS):
        historical = index < 3
        rows.append({
            "authority_scope": "historical_committed_consensus" if historical else "expansion_committed_fingerprint",
            "authority_source": str(P6B0_AUTHORITY_PATH if historical else EXPANSION_AUTHORITY_PATH),
            "authority_row_id": authority_id,
            "binding_row_id": f"REAL_LOCATOR_BINDING_{index + 1:06d}",
            "sample_id": sample_id, "pdb_id": pdb_id, "ligand": ligand,
            "raw_path": EXACT_RAW_PATHS[index], "sha256": digest,
            "prior_sha256": digest, "size": size,
            "source_pipeline": (
                "historical_sample_preparation_execution_smoke_v0"
                if historical
                else "independent_group_expansion_batch_sample_preparation_execution_smoke_v0"
            ),
        })
    return rows


def validate_authority_mapping(rows: Sequence[Mapping[str, Any]]) -> bool:
    try:
        actual = [dict(row) for row in rows]
    except (TypeError, ValueError):
        return False
    expected = _canonical_authority_mapping()
    return (
        len(actual) == 11
        and all(tuple(row) == MAPPING_COLUMNS for row in actual)
        and actual == expected
        and len({(row["pdb_id"], row["ligand"]) for row in actual}) == 11
        and len({row["raw_path"] for row in actual}) == 11
        and all(row["sha256"] == row["prior_sha256"] and _valid_hash(row["sha256"]) and _valid_size(row["size"]) for row in actual)
    )


def _platform_checks() -> dict[str, bool]:
    return {
        "O_NOFOLLOW": hasattr(os, "O_NOFOLLOW"),
        "O_DIRECTORY": hasattr(os, "O_DIRECTORY"),
        "O_CLOEXEC": hasattr(os, "O_CLOEXEC"),
        "open_dir_fd": os.open in os.supports_dir_fd,
        "stat_dir_fd": os.stat in os.supports_dir_fd,
        "stat_follow_symlinks": os.stat in os.supports_follow_symlinks,
    }


def _stat_tuple(value: os.stat_result) -> tuple[int, ...]:
    return tuple(int(getattr(value, field)) for field in STAT_FIELDS)


def _stat_fingerprint(value: os.stat_result) -> str:
    return ";".join(f"{field.removeprefix('st_')}={int(getattr(value, field))}" for field in STAT_FIELDS)


def secure_hash_raw_source(
    raw_relative_path: str,
    *,
    repo_root: Path = REPO_ROOT,
    read_fn: Callable[[int, int], bytes] = os.read,
    after_entry_stat_hook: Callable[[], None] | None = None,
    after_read_hook: Callable[[int], None] | None = None,
) -> RawObservation:
    """Hash one exact raw path without following a parent or final symlink."""
    if not _safe_raw_relative_path(raw_relative_path):
        return RawObservation(blocking_reason="RAW_TARGET_PATH_INVALID")
    if not all(_platform_checks().values()):
        return RawObservation(blocking_reason="SECURE_FD_PLATFORM_CONTRACT_UNAVAILABLE")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    fds: list[int] = []
    directory_open_count = 0
    final_entry_stat_performed = False
    file_fd_opened = False
    fd_fstat_performed = False
    try:
        current_fd = os.open(str(repo_root), directory_flags)
        fds.append(current_fd)
        directory_open_count += 1
        components = PurePosixPath(raw_relative_path).parts
        for component in components[:-1]:
            current_fd = os.open(component, directory_flags, dir_fd=current_fd)
            fds.append(current_fd)
            directory_open_count += 1
        final_name = components[-1]
        entry_stat = os.stat(final_name, dir_fd=current_fd, follow_symlinks=False)
        final_entry_stat_performed = True
        entry_is_symlink = stat.S_ISLNK(entry_stat.st_mode)
        entry_is_regular = stat.S_ISREG(entry_stat.st_mode)
        if entry_is_symlink:
            return RawObservation(
                exists=True, regular=False, symlink=True, confined=False,
                directory_component_open_count=directory_open_count,
                final_entry_stat_performed=True,
                blocking_reason="RAW_FINAL_ENTRY_SYMLINK_REJECTED",
            )
        if not entry_is_regular:
            return RawObservation(
                exists=True, regular=False, symlink=False, confined=True,
                directory_component_open_count=directory_open_count,
                final_entry_stat_performed=True,
                blocking_reason="RAW_SOURCE_NOT_REGULAR_FILE",
            )
        if after_entry_stat_hook is not None:
            after_entry_stat_hook()
        file_fd = os.open(final_name, file_flags, dir_fd=current_fd)
        fds.append(file_fd)
        file_fd_opened = True
        pre = os.fstat(file_fd)
        fd_fstat_performed = True
        regular = stat.S_ISREG(pre.st_mode)
        if not regular:
            return RawObservation(
                exists=True, directory_component_open_count=directory_open_count,
                final_entry_stat_performed=True, file_fd_opened=True,
                fd_fstat_performed=True,
                blocking_reason="RAW_SOURCE_NOT_REGULAR_FILE",
            )
        if any(
            getattr(entry_stat, field) != getattr(pre, field)
            for field in ("st_dev", "st_ino", "st_mode")
        ):
            return RawObservation(
                observed_size=int(pre.st_size), exists=True, regular=True,
                confined=True, pre_fingerprint=_stat_fingerprint(pre),
                directory_component_open_count=directory_open_count,
                final_entry_stat_performed=True, file_fd_opened=True,
                fd_fstat_performed=True,
                blocking_reason="RAW_SOURCE_CHANGED_DURING_OPEN",
            )
        os.lseek(file_fd, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        byte_count = 0
        while True:
            chunk = read_fn(file_fd, CHUNK_SIZE)
            if not chunk:
                break
            if type(chunk) is not bytes:
                return RawObservation(
                    exists=True, regular=True, confined=True,
                    directory_component_open_count=directory_open_count,
                    final_entry_stat_performed=True, file_fd_opened=True,
                    fd_fstat_performed=True,
                    blocking_reason="RAW_READ_RESULT_NOT_BYTES",
                )
            digest.update(chunk)
            byte_count += len(chunk)
        if after_read_hook is not None:
            after_read_hook(file_fd)
        post = os.fstat(file_fd)
        path_stat = os.stat(final_name, dir_fd=current_fd, follow_symlinks=False)
        path_is_symlink = stat.S_ISLNK(path_stat.st_mode)
        fd_stable = _stat_tuple(pre) == _stat_tuple(post)
        path_fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
        path_stable = all(getattr(post, field) == getattr(path_stat, field) for field in path_fields)
        complete = byte_count == post.st_size and post.st_size > 0
        stable = fd_stable and path_stable and not path_is_symlink and complete
        reason = "" if stable else (
            "RAW_SOURCE_CHANGED_DURING_HASH"
            if not fd_stable or not path_stable or path_is_symlink
            else "RAW_SOURCE_PARTIAL_READ"
        )
        return RawObservation(
            observed_sha256=digest.hexdigest() if stable else "",
            observed_size=int(post.st_size), exists=True, regular=True,
            symlink=path_is_symlink, confined=not path_is_symlink,
            pre_fingerprint=_stat_fingerprint(pre),
            post_fingerprint=_stat_fingerprint(post), stat_stable=stable,
            bytes_read=byte_count,
            directory_component_open_count=directory_open_count,
            final_entry_stat_performed=True, file_fd_opened=True,
            fd_fstat_performed=True, read_completed=complete,
            hash_completed=stable, blocking_reason=reason,
        )
    except FileNotFoundError:
        return RawObservation(
            directory_component_open_count=directory_open_count,
            final_entry_stat_performed=final_entry_stat_performed,
            file_fd_opened=file_fd_opened,
            fd_fstat_performed=fd_fstat_performed,
            blocking_reason="RAW_SOURCE_MISSING",
        )
    except NotADirectoryError:
        return RawObservation(
            directory_component_open_count=directory_open_count,
            final_entry_stat_performed=final_entry_stat_performed,
            file_fd_opened=file_fd_opened,
            fd_fstat_performed=fd_fstat_performed,
            blocking_reason="RAW_PARENT_NOT_DIRECTORY",
        )
    except OSError as error:
        reason = "RAW_SYMLINK_OR_SECURE_OPEN_REJECTED" if error.errno in (40, 20) else "RAW_SOURCE_ACCESS_FAILED"
        return RawObservation(
            directory_component_open_count=directory_open_count,
            final_entry_stat_performed=final_entry_stat_performed,
            file_fd_opened=file_fd_opened,
            fd_fstat_performed=fd_fstat_performed,
            blocking_reason=reason,
        )
    finally:
        for descriptor in reversed(fds):
            try:
                os.close(descriptor)
            except OSError:
                pass


GitProvider = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]


def _git_state(raw_path: str, scope: str, *, repo_root: Path = REPO_ROOT, git_provider: GitProvider = _git) -> dict[str, Any]:
    tracked = git_provider(("ls-files", "--error-unmatch", "--", raw_path), repo_root).returncode == 0
    worktree_clean = git_provider(("diff", "--quiet", "--", raw_path), repo_root).returncode == 0
    index_clean = git_provider(("diff", "--cached", "--quiet", "--", raw_path), repo_root).returncode == 0
    ignored = git_provider(("check-ignore", "-q", "--", raw_path), repo_root).returncode == 0
    if (
        scope == "historical_committed_consensus"
        and raw_path in HISTORICAL_RAW_PATHS
        and not tracked
        and index_clean
    ):
        state = "untracked_historical_authority_runtime"
        passed = True
    elif (
        scope == "expansion_committed_fingerprint"
        and raw_path in EXPANSION_RAW_PATHS
        and not tracked
        and ignored
        and index_clean
    ):
        state = "ignored_runtime"
        passed = True
    else:
        state = "unknown"
        passed = False
    return {
        "state": state, "tracked": tracked, "ignored": ignored,
        "worktree_clean": worktree_clean, "index_clean": index_clean,
        "passed": passed,
    }


def _authority_audit_rows(mapping: Sequence[Mapping[str, Any]], authority_ok: bool) -> list[dict[str, Any]]:
    specs = (
        (1, "historical_committed_consensus", P6B0_AUTHORITY_PATH, 3),
        (2, "expansion_committed_fingerprint", EXPANSION_AUTHORITY_PATH, 8),
    )
    rows = []
    for order, scope, path, expected_count in specs:
        selected = [row for row in mapping if row.get("authority_scope") == scope]
        identities = [(row.get("pdb_id"), row.get("ligand")) for row in selected]
        hashes = [(row.get("sha256"), row.get("prior_sha256")) for row in selected]
        passed = authority_ok and len(selected) == expected_count
        rows.append({
            "authority_source_order": order, "authority_scope": scope,
            "authority_source_relative_path": str(path),
            "authority_source_sha256": SOURCE_SHA256[str(path)],
            "authority_row_count": len(selected),
            "binding_match_count": len(selected),
            "expected_hash_count": sum(_valid_hash(pair[0]) for pair in hashes),
            "prior_observed_match_count": sum(pair[0] == pair[1] and _valid_hash(pair[0]) for pair in hashes),
            "expected_size_count": sum(type(row.get("size")) is str and _valid_size(row.get("size")) for row in selected),
            "duplicate_identity_count": len(identities) - len(set(identities)),
            "conflicting_hash_count": sum(pair[0] != pair[1] for pair in hashes),
            "authority_check_passed": passed,
            "blocking_reason": "" if passed else "AUTHORITY_MAPPING_FAILED",
        })
    return rows


def validate_authority_audit_rows(
    rows: Sequence[Mapping[str, Any]],
    mapping: Sequence[Mapping[str, Any]],
) -> bool:
    try:
        actual = [dict(row) for row in rows]
        expected = _authority_audit_rows(mapping, validate_authority_mapping(mapping))
    except (TypeError, ValueError):
        return False
    return (
        validate_authority_mapping(mapping)
        and len(actual) == 2
        and all(tuple(row) == AUTHORITY_AUDIT_COLUMNS for row in actual)
        and actual == expected
        and [row["authority_row_count"] for row in actual] == [3, 8]
        and [row["binding_match_count"] for row in actual] == [3, 8]
        and [row["expected_hash_count"] for row in actual] == [3, 8]
        and [row["prior_observed_match_count"] for row in actual] == [3, 8]
        and [row["expected_size_count"] for row in actual] == [3, 8]
        and all(
            row["duplicate_identity_count"] == 0
            and row["conflicting_hash_count"] == 0
            and row["authority_check_passed"] is True
            and row["blocking_reason"] == ""
            for row in actual
        )
    )


SAFETY_SPECS = (
    ("frozen_metadata_sources_lstat_hash_read", True),
    ("exact_raw_path_component_opens", True),
    ("exact_raw_fd_fstat", True),
    ("exact_raw_fd_read", True),
    ("exact_raw_fd_sha256", True),
    ("git_state_checks_exact_11", True),
    ("raw_directory_listing_or_search", False),
    ("raw_decode", False), ("raw_parse", False), ("raw_write", False),
    ("raw_modification", False), ("network_access", False),
    ("registry_access", False), ("checkpoint_access", False),
    ("p5b_parser_called", False), ("p4_provider_called", False),
    ("real_provider_rows_materialized", False),
    ("admission_modified", False), ("queue_or_download", False),
    ("torch_numpy_model_loss_training", False),
)


def _safety_rows(execution: Mapping[str, bool]) -> list[dict[str, Any]]:
    rows = []
    for item, required in SAFETY_SPECS:
        observed = execution.get(item, False)
        passed = observed is required
        rows.append({
            "safety_item": item, "required_status": required,
            "observed_status": observed, "safety_passed": passed,
            "blocking_reason": "" if passed else "SAFETY_CONTRACT_FAILED",
        })
    return rows


def validate_safety_rows(
    rows: Sequence[Mapping[str, Any]], execution: Mapping[str, bool]
) -> bool:
    try:
        actual = [dict(row) for row in rows]
        expected = _safety_rows(execution)
    except (KeyError, TypeError, ValueError):
        return False
    return (
        len(actual) == len(SAFETY_SPECS)
        and all(tuple(row) == SAFETY_COLUMNS for row in actual)
        and actual == expected
        and all(
            row["safety_passed"] is True and row["blocking_reason"] == ""
            for row in actual
        )
    )


def _issue_rows() -> list[dict[str, Any]]:
    return [
        {"issue_id": "REAL_RESIDUE_LOCATOR_PROVIDER_EXPORT_NOT_YET_EXECUTED", "issue_type": "execution_readiness", "severity": "blocking", "status": "open", "issue_count": 11, "blocking_reason": "REAL_RESIDUE_LOCATOR_PROVIDER_EXPORT_NOT_YET_EXECUTED"},
        {"issue_id": "REAL_PROVIDER_SIDECAR_NOT_YET_MERGED_INTO_ADMISSION_SCHEMA", "issue_type": "schema_integration", "severity": "blocking", "status": "open", "issue_count": 1, "blocking_reason": "REAL_PROVIDER_SIDECAR_NOT_YET_MERGED_INTO_ADMISSION_SCHEMA"},
    ]


def validate_issue_rows(rows: Sequence[Mapping[str, Any]]) -> bool:
    return list(rows) == _issue_rows()


CONTRACT_SPECS = tuple(
    (f"P6B_C{i:03d}", area, requirement, expected)
    for i, (area, requirement, expected) in enumerate((
        ("predecessor", "p6b0_stage_and_all_checks", "true"),
        ("source", "source_input_count", "9"),
        ("binding", "p6a_binding_shape", "11x26"),
        ("authority", "historical_authority_count", "3"),
        ("authority", "expansion_authority_count", "8"),
        ("authority", "authority_join_count", "11"),
        ("authority", "current_raw_self_certification", "false"),
        ("raw", "exact_path_access_only", "true"),
        ("raw", "component_nofollow_walk", "true"),
        ("raw", "raw_directory_listing", "false"),
        ("raw", "regular_fd_count", "11"),
        ("raw", "unique_raw_path_count", "11"),
        ("git", "untracked_historical_authority_runtime_count", "3"),
        ("git", "ignored_expansion_count", "8"),
        ("git", "exact_raw_tracked_count", "0"),
        ("git", "raw_index_clean_count", "11"),
        ("raw", "pre_post_fstat_stable_count", "11"),
        ("raw", "path_entry_stable_count", "11"),
        ("raw", "sha256_match_count", "11"),
        ("raw", "size_match_count", "11"),
        ("raw", "passed_count", "11"),
        ("raw", "blocked_count", "0"),
        ("execution", "p5b_parser_called", "false"),
        ("execution", "p4_provider_called", "false"),
        ("samples", "existing_real_sample_count", "11"),
        ("samples", "real_insertion_unknown_count", "11"),
        ("samples", "real_insertion_absence_proven_count", "0"),
        ("readiness", "admit_004_ready", "false"),
        ("readiness", "e1_ready", "false"),
        ("readiness", "candidate_ready", "false"),
        ("readiness", "bulk_download_ready", "false"),
        ("readiness", "training_ready", "false"),
        ("training", "feature_semantics_audit_required", "true"),
        ("mask", "canonical_mask_count", "5"),
        ("mask", "scaffold_only_b3_present", "true"),
        ("platform", "o_nofollow_available", "true"),
        ("platform", "o_directory_available", "true"),
        ("platform", "o_cloexec_available", "true"),
        ("platform", "open_dir_fd_available", "true"),
        ("platform", "stat_dir_fd_available", "true"),
        ("raw", "raw_stat_current_step", "true"),
        ("raw", "raw_read_current_step", "true"),
        ("raw", "raw_hash_current_step", "true"),
        ("raw", "raw_parse_current_step", "false"),
        ("execution", "real_provider_rows_materialized", "false"),
        ("execution", "real_samples_backfilled", "0"),
        ("issues", "issue_inventory_count", "2"),
        ("blockers", "domain_blocker_count", "10"),
        ("readiness", "provider_smoke_ready", "true"),
        ("readiness", "provider_execution_ready", "false"),
    ), 1)
)


def _text(value: object) -> str:
    if type(value) is bool:
        return str(value).lower()
    return str(value)


def _contract_rows(observations: Mapping[str, object]) -> list[dict[str, Any]]:
    rows = []
    for item_id, area, requirement, expected in CONTRACT_SPECS:
        observed = _text(observations.get(requirement, "missing"))
        passed = observed == expected
        rows.append({
            "contract_item_id": item_id, "contract_area": area,
            "requirement": requirement, "expected_value": expected,
            "observed_value": observed, "contract_passed": passed,
            "blocking_reason": "" if passed else "PRECONDITION_CONTRACT_FAILED",
        })
    return rows


def validate_contract_rows(
    rows: Sequence[Mapping[str, Any]], observations: Mapping[str, object]
) -> bool:
    try:
        actual = [dict(row) for row in rows]
        expected = _contract_rows(observations)
    except (KeyError, TypeError, ValueError):
        return False
    return (
        len(actual) == 50
        and all(tuple(row) == CONTRACT_COLUMNS for row in actual)
        and actual == expected
        and [row["contract_item_id"] for row in actual] == [f"P6B_C{i:03d}" for i in range(1, 51)]
        and all(
            row["contract_passed"] is True and row["blocking_reason"] == ""
            for row in actual
        )
    )


_STAT_FINGERPRINT_PATTERN = re.compile(
    r"dev=(\d+);ino=(\d+);mode=(\d+);nlink=(\d+);size=(\d+);mtime_ns=(\d+);ctime_ns=(\d+)"
)


def _parse_stat_fingerprint(
    value: object,
) -> tuple[int, int, int, int, int, int, int] | None:
    if type(value) is not str:
        return None
    match = _STAT_FINGERPRINT_PATTERN.fullmatch(value)
    if match is None:
        return None
    return tuple(int(item) for item in match.groups())  # type: ignore[return-value]


def _build_matrix_rows(
    mapping: Sequence[Mapping[str, Any]],
    raw_observations: Sequence[RawObservation],
    git_states: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not (len(mapping) == len(raw_observations) == len(git_states)):
        return []
    rows: list[dict[str, Any]] = []
    raw_paths = [authority.get("raw_path") for authority in mapping]
    for index, (authority, observation, git) in enumerate(
        zip(mapping, raw_observations, git_states), 1
    ):
        expected_size = int(authority["size"])
        hash_match = (
            observation.observed_sha256 == authority["sha256"]
            and bool(observation.observed_sha256)
            and observation.hash_completed
        )
        size_match = observation.observed_size == expected_size and observation.observed_size > 0
        passed = all((
            hash_match, size_match, observation.exists, observation.regular,
            not observation.symlink, observation.confined, observation.stat_stable,
            observation.file_fd_opened, observation.fd_fstat_performed,
            observation.read_completed, observation.hash_completed,
            git.get("passed") is True,
        ))
        reasons = []
        if observation.blocking_reason:
            reasons.append(observation.blocking_reason)
        if not hash_match:
            reasons.append("RAW_SHA256_MISMATCH")
        if not size_match:
            reasons.append("RAW_FILE_SIZE_MISMATCH")
        if git.get("passed") is not True:
            reasons.append("RAW_GIT_TRACKING_CONTRACT_FAILED")
        rows.append({
            "precondition_row_id": f"REAL_RAW_PRECONDITION_{index:06d}",
            "binding_row_id": authority["binding_row_id"],
            "source_pipeline": authority["source_pipeline"],
            "sample_preparation_input_id": authority["sample_id"],
            "pdb_id": authority["pdb_id"], "ligand_comp_id": authority["ligand"],
            "raw_target_relative_path": authority["raw_path"],
            "authority_scope": authority["authority_scope"],
            "expected_authority_source_relative_path": authority["authority_source"],
            "expected_authority_row_id": authority["authority_row_id"],
            "authority_join_status": "exact_authority_match",
            "expected_sha256": authority["sha256"],
            "expected_file_size_bytes": expected_size,
            "observed_sha256": observation.observed_sha256,
            "observed_file_size_bytes": observation.observed_size,
            "sha256_matches": hash_match, "file_size_matches": size_match,
            "raw_path_exists": observation.exists,
            "raw_path_regular_file": observation.regular,
            "raw_path_symlink": observation.symlink,
            "raw_path_confined_without_symlink": observation.confined,
            "raw_path_unique": raw_paths.count(authority["raw_path"]) == 1,
            "raw_git_tracking_state": git.get("state", "unknown"),
            "raw_git_worktree_clean": git.get("worktree_clean") is True,
            "raw_git_index_clean": git.get("index_clean") is True,
            "pre_hash_stat_fingerprint": observation.pre_fingerprint,
            "post_hash_stat_fingerprint": observation.post_fingerprint,
            "stat_stable": observation.stat_stable,
            "raw_source_precondition_status": "passed" if passed else "blocked",
            "ready_for_real_provider_export_execution_smoke": passed,
            "blocking_reason": "" if passed else "|".join(dict.fromkeys(reasons)),
        })
    return rows


def validate_matrix_rows(
    rows: Sequence[Mapping[str, Any]],
    mapping: Sequence[Mapping[str, Any]],
    raw_observations: Sequence[RawObservation],
    git_states: Sequence[Mapping[str, Any]],
) -> bool:
    if not validate_authority_mapping(mapping):
        return False
    if len(raw_observations) != 11 or len(git_states) != 11:
        return False
    try:
        actual = [dict(row) for row in rows]
        expected = _build_matrix_rows(mapping, raw_observations, git_states)
    except (KeyError, TypeError, ValueError):
        return False
    if (
        len(actual) != 11
        or any(tuple(row) != MATRIX_COLUMNS for row in actual)
        or actual != expected
    ):
        return False
    for row in actual:
        pre = _parse_stat_fingerprint(row["pre_hash_stat_fingerprint"])
        post = _parse_stat_fingerprint(row["post_hash_stat_fingerprint"])
        if pre is None or post is None or pre != post:
            return False
        _dev, inode, mode, nlink, size, _mtime_ns, _ctime_ns = pre
        if (
            size != row["observed_file_size_bytes"]
            or size != row["expected_file_size_bytes"]
            or not stat.S_ISREG(mode)
            or nlink < 1
            or inode <= 0
            or row["stat_stable"] is not True
            or row["raw_source_precondition_status"] != "passed"
            or row["ready_for_real_provider_export_execution_smoke"] is not True
            or row["blocking_reason"] != ""
        ):
            return False
    return True


def build_precondition_state(
    *,
    repo_root: Path = REPO_ROOT,
    source_snapshot: FrozenSourceSnapshot | None = None,
    source_rows: Sequence[Mapping[str, Any]] | None = None,
    raw_reader: Callable[..., RawObservation] = secure_hash_raw_source,
    git_provider: GitProvider = _git,
    forced_section_failures: Sequence[str] = (),
) -> dict[str, Any]:
    forced = tuple(forced_section_failures)
    if len(forced) != len(set(forced)) or any(name not in SECTION_NAMES for name in forced):
        raise ValueError("FORCED_SECTION_FAILURES_INVALID")
    if source_snapshot is not None and source_rows is not None:
        raise ValueError("SOURCE_EVIDENCE_INPUT_CONFLICT")
    if source_snapshot is None:
        if source_rows is None:
            source_snapshot = _build_frozen_source_snapshot(
                repo_root, git_provider=git_provider
            )
        else:
            source_snapshot = FrozenSourceSnapshot(
                _repo_root_identity(repo_root) or _empty_repo_root_identity(),
                (), tuple(dict(row) for row in source_rows), "blocked",
                "SOURCE_ACCESS_NOT_ALLOWED", 0,
            )
    sources = [dict(row) for row in source_snapshot.source_rows]
    source_ok = (
        validate_frozen_source_snapshot(source_snapshot, repo_root)
        and "source_boundary" not in forced
    )
    empty = CsvDocument((), (), "blocked", "SOURCE_ACCESS_NOT_ALLOWED")
    if source_ok:
        historical = _read_frozen_csv(P6B0_AUTHORITY_PATH, source_snapshot)
        bindings = _read_frozen_csv(P6A_BINDING_PATH, source_snapshot)
        expansion = _read_frozen_csv(EXPANSION_AUTHORITY_PATH, source_snapshot)
        predecessor_manifest_document = _read_frozen_json(P6B0_MANIFEST_PATH, source_snapshot)
        predecessor_manifest = predecessor_manifest_document.payload
    else:
        historical = bindings = expansion = empty
        predecessor_manifest = {}
    p6b0_ok = source_ok and all(_p6b0_checks(predecessor_manifest, historical).values()) and "p6b0_predecessor" not in forced
    p6a_ok = source_ok and all(_p6a_checks(bindings).values()) and "p6a_binding" not in forced
    expansion_ok = source_ok and all(_expansion_checks(expansion).values())
    mapping = _authority_mapping(bindings, historical, expansion) if p6b0_ok and p6a_ok and expansion_ok else []
    if "authority_mapping" in forced:
        mapping = []
    authority_ok = validate_authority_mapping(mapping)
    raw_observations: list[RawObservation] = []
    git_states: list[dict[str, Any]] = []
    if authority_ok:
        for authority in mapping:
            observation = raw_reader(authority["raw_path"], repo_root=repo_root)
            raw_observations.append(observation)
            git = _git_state(authority["raw_path"], authority["authority_scope"], repo_root=repo_root, git_provider=git_provider)
            git_states.append(git)
    matrix = _build_matrix_rows(mapping, raw_observations, git_states)
    raw_component_open_success_count = sum(
        observation.directory_component_open_count == len(PurePosixPath(authority["raw_path"]).parts)
        and observation.final_entry_stat_performed
        and observation.file_fd_opened
        for authority, observation in zip(mapping, raw_observations)
    )
    raw_open_count = sum(observation.file_fd_opened for observation in raw_observations)
    raw_stat_count = sum(observation.fd_fstat_performed for observation in raw_observations)
    raw_read_count = sum(observation.read_completed for observation in raw_observations)
    raw_hash_count = sum(
        observation.hash_completed and _valid_hash(observation.observed_sha256)
        for observation in raw_observations
    )
    passed_count = sum(row["raw_source_precondition_status"] == "passed" for row in matrix)
    blocked_count = sum(row["raw_source_precondition_status"] == "blocked" for row in matrix)
    matrix_ok = validate_matrix_rows(matrix, mapping, raw_observations, git_states)
    raw_ok = authority_ok and matrix_ok and "raw_access" not in forced
    authority_audit = _authority_audit_rows(mapping, authority_ok)
    authority_audit_ok = validate_authority_audit_rows(authority_audit, mapping)
    platform = _platform_checks()
    observations = {
        "p6b0_stage_and_all_checks": p6b0_ok,
        "source_input_count": len(sources) if source_ok else 0,
        "p6a_binding_shape": "11x26" if p6a_ok else "blocked",
        "historical_authority_count": sum(m["authority_scope"] == "historical_committed_consensus" for m in mapping),
        "expansion_authority_count": sum(m["authority_scope"] == "expansion_committed_fingerprint" for m in mapping),
        "authority_join_count": len(mapping), "current_raw_self_certification": False,
        "exact_path_access_only": authority_ok, "component_nofollow_walk": all(platform.values()),
        "raw_directory_listing": False, "regular_fd_count": sum(r["raw_path_regular_file"] for r in matrix),
        "unique_raw_path_count": len({r["raw_target_relative_path"] for r in matrix}),
        "untracked_historical_authority_runtime_count": sum(r["raw_git_tracking_state"] == "untracked_historical_authority_runtime" for r in matrix),
        "ignored_expansion_count": sum(r["raw_git_tracking_state"] == "ignored_runtime" for r in matrix),
        "exact_raw_tracked_count": sum(state["tracked"] for state in git_states),
        "raw_index_clean_count": sum(r["raw_git_index_clean"] for r in matrix),
        "pre_post_fstat_stable_count": sum(r["stat_stable"] and r["pre_hash_stat_fingerprint"] == r["post_hash_stat_fingerprint"] for r in matrix),
        "path_entry_stable_count": sum(r["stat_stable"] for r in matrix),
        "sha256_match_count": sum(r["sha256_matches"] for r in matrix),
        "size_match_count": sum(r["file_size_matches"] for r in matrix),
        "passed_count": passed_count, "blocked_count": blocked_count,
        "p5b_parser_called": False, "p4_provider_called": False,
        "existing_real_sample_count": 11, "real_insertion_unknown_count": 11,
        "real_insertion_absence_proven_count": 0, "admit_004_ready": False,
        "e1_ready": False, "candidate_ready": False, "bulk_download_ready": False,
        "training_ready": False, "feature_semantics_audit_required": True,
        "canonical_mask_count": len(CANONICAL_MASK_PAIRS),
        "scaffold_only_b3_present": ("scaffold_only", "B3") in CANONICAL_MASK_PAIRS,
        "o_nofollow_available": platform["O_NOFOLLOW"],
        "o_directory_available": platform["O_DIRECTORY"],
        "o_cloexec_available": platform["O_CLOEXEC"],
        "open_dir_fd_available": platform["open_dir_fd"],
        "stat_dir_fd_available": platform["stat_dir_fd"],
        "raw_stat_current_step": raw_stat_count == 11,
        "raw_read_current_step": raw_read_count == 11,
        "raw_hash_current_step": raw_hash_count == 11,
        "raw_parse_current_step": False, "real_provider_rows_materialized": False,
        "real_samples_backfilled": 0, "issue_inventory_count": 2,
        "domain_blocker_count": len(DOMAIN_BLOCKING_REASONS),
        "provider_smoke_ready": raw_ok, "provider_execution_ready": False,
    }
    contract = _contract_rows(observations)
    execution = {item: False for item, _ in SAFETY_SPECS}
    execution.update({
        "frozen_metadata_sources_lstat_hash_read": source_ok,
        "exact_raw_path_component_opens": raw_component_open_success_count == 11,
        "exact_raw_fd_fstat": raw_stat_count == 11,
        "exact_raw_fd_read": raw_read_count == 11,
        "exact_raw_fd_sha256": raw_hash_count == 11,
        "git_state_checks_exact_11": len(matrix) == 11,
    })
    safety = _safety_rows(execution)
    issues = _issue_rows()
    sections = {
        "source_boundary": source_ok, "p6b0_predecessor": p6b0_ok,
        "p6a_binding": p6a_ok,
        "authority_mapping": authority_ok and authority_audit_ok,
        "raw_access": raw_ok,
        "precondition_contract": validate_contract_rows(contract, observations) and "precondition_contract" not in forced,
        "issue_inventory": validate_issue_rows(issues) and "issue_inventory" not in forced,
        "safety": validate_safety_rows(safety, execution) and "safety" not in forced,
    }
    all_checks = tuple(sections) == SECTION_NAMES and all(sections.values())
    return {
        "source_snapshot": source_snapshot,
        "source_rows": sources, "mapping": mapping, "matrix_rows": matrix,
        "source_content_read_count": source_snapshot.source_content_read_count,
        "source_snapshot_validated": validate_frozen_source_snapshot(
            source_snapshot, repo_root
        ),
        "raw_observations": raw_observations, "git_states": git_states,
        "authority_audit_rows": authority_audit, "contract_rows": contract,
        "safety_rows": safety, "issue_rows": issues, "sections": sections,
        "all_checks_passed": all_checks,
        "validation_failures": [name for name, passed in sections.items() if not passed],
        "raw_open_count": raw_open_count, "raw_stat_count": raw_stat_count,
        "raw_read_count": raw_read_count, "raw_hash_count": raw_hash_count,
        "passed_count": passed_count, "blocked_count": blocked_count,
        "observations": observations, "execution": execution,
    }


def _csv_value(value: Any) -> str:
    if type(value) is bool:
        return str(value).lower()
    return str(value)


def _ensure_output_root(root: Path) -> None:
    if root.exists():
        if root.is_symlink() or not root.is_dir():
            raise RuntimeError("OUTPUT_ROOT_NOT_SAFE_DIRECTORY")
    else:
        root.mkdir(parents=True)


def _atomic_write_csv(path: Path, columns: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                if tuple(row) != tuple(columns):
                    raise ValueError("OUTPUT_ROW_SCHEMA_MISMATCH")
                writer.writerow({key: _csv_value(row[key]) for key in columns})
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
        while chunk := handle.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_payload(state: Mapping[str, Any], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    matrix = state["matrix_rows"]
    all_checks = state["all_checks_passed"]
    return {
        "project_name": "CovaPIE", "step_label": STEP_LABEL, "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE, "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "all_checks_passed": all_checks, "validation_failures": state["validation_failures"],
        "sections": state["sections"], "source_input_count": 9,
        "source_input_sha256": SOURCE_SHA256,
        "source_boundary_all_passed": state["sections"]["source_boundary"],
        "source_boundary_before_content_read": True,
        "source_snapshot_validated_before_raw_access": state["sections"]["source_boundary"],
        "output_file_count": 6, "output_files": list(OUTPUT_FILES),
        "output_sha256": dict(output_sha256),
        "historical_authority_row_count": sum(
            row.get("authority_scope") == "historical_committed_consensus"
            for row in state["mapping"]
        ),
        "expansion_authority_row_count": sum(
            row.get("authority_scope") == "expansion_committed_fingerprint"
            for row in state["mapping"]
        ),
        "authority_binding_match_count": len(state["mapping"]),
        "authority_conflict_count": sum(
            row.get("conflicting_hash_count", 0)
            for row in state["authority_audit_rows"]
        ),
        "current_raw_used_to_define_expected_hash": False,
        "raw_source_precondition_row_count": len(matrix),
        "raw_source_precondition_passed_count": state["passed_count"],
        "raw_source_precondition_blocked_count": state["blocked_count"],
        "raw_sha256_precondition_frozen_count": sum(row["raw_source_precondition_status"] == "passed" for row in matrix),
        "raw_sha256_match_count": sum(row["sha256_matches"] for row in matrix),
        "raw_file_size_match_count": sum(row["file_size_matches"] for row in matrix),
        "raw_regular_file_count": sum(row["raw_path_regular_file"] for row in matrix),
        "raw_symlink_count": sum(row["raw_path_symlink"] for row in matrix),
        "raw_path_confined_count": sum(row["raw_path_confined_without_symlink"] for row in matrix),
        "raw_unique_path_count": len({row["raw_target_relative_path"] for row in matrix}),
        "untracked_historical_authority_runtime_count": sum(row["raw_git_tracking_state"] == "untracked_historical_authority_runtime" for row in matrix),
        "ignored_expansion_runtime_count": sum(row["raw_git_tracking_state"] == "ignored_runtime" for row in matrix),
        "exact_raw_tracked_count": state["observations"]["exact_raw_tracked_count"],
        "raw_worktree_clean_count": sum(row["raw_git_worktree_clean"] for row in matrix),
        "raw_index_clean_count": sum(row["raw_git_index_clean"] for row in matrix),
        "raw_stat_stable_count": sum(row["stat_stable"] for row in matrix),
        "real_raw_sources_stat_current_step": state["raw_stat_count"] == 11,
        "real_raw_sources_read_current_step": state["raw_read_count"] == 11,
        "real_raw_sources_hashed_current_step": state["raw_hash_count"] == 11,
        "real_raw_sources_parsed_current_step": False,
        "p5b_parser_called_current_step": False, "p4_provider_called_current_step": False,
        "real_executor_implemented": False,
        "real_provider_rows_materialized_current_step": False,
        "real_samples_backfilled_current_step": 0,
        "real_raw_source_precondition_gate_passed": all_checks,
        "ready_for_real_provider_export_execution_smoke": all_checks,
        "ready_for_real_provider_export_execution": False,
        "insertion_code_provenance_export_ready_for_real_samples": False,
        "admit_004_rule_logic_ready": False,
        "ready_for_e1_residue_identity_semantics_design": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False, "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "existing_real_sample_count": 11, "real_insertion_unknown_sample_count": 11,
        "real_insertion_absence_proven_sample_count": 0,
        "real_fully_provable_pre_download_sample_count": 0,
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "canonical_mask_task_count": 5,
        "current_domain_blocking_reasons": list(DOMAIN_BLOCKING_REASONS),
        "issue_ids": [row["issue_id"] for row in state["issue_rows"]],
        "recommended_next_step": RECOMMENDED_NEXT_STEP if all_checks else BLOCKED_NEXT_STEP,
    }


def run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
    source_snapshot: FrozenSourceSnapshot | None = None,
) -> dict[str, Any]:
    root = output_root if output_root.is_absolute() else repo_root / output_root
    _ensure_output_root(root)
    state = build_precondition_state(
        repo_root=repo_root, source_snapshot=source_snapshot
    )
    outputs = (
        (CONTRACT_FILENAME, CONTRACT_COLUMNS, state["contract_rows"]),
        (MATRIX_FILENAME, MATRIX_COLUMNS, state["matrix_rows"]),
        (AUTHORITY_AUDIT_FILENAME, AUTHORITY_AUDIT_COLUMNS, state["authority_audit_rows"]),
        (SAFETY_FILENAME, SAFETY_COLUMNS, state["safety_rows"]),
        (ISSUE_FILENAME, ISSUE_COLUMNS, state["issue_rows"]),
    )
    for filename, columns, rows in outputs:
        _atomic_write_csv(root / filename, columns, rows)
    hashes = {name: _file_sha256(root / name) for name in CSV_OUTPUTS}
    manifest = _manifest_payload(state, hashes)
    _atomic_write_json(root / MANIFEST_FILENAME, manifest)
    return {"state": state, "manifest": manifest}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1()
    if not result["manifest"]["all_checks_passed"]:
        raise SystemExit("P6-B gate blocked: " + ",".join(result["manifest"]["validation_failures"]))
