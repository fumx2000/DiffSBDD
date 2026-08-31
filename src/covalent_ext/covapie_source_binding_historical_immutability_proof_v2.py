"""Read-only proof that Phase-A historical source bytes remain immutable."""

from __future__ import annotations

import ast
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import NoReturn

from covalent_ext import (
    covapie_source_binding_active_consumer_integration_v2 as integration_v2,
)
from covalent_ext import covapie_source_binding_policy_v2 as source_binding_v2


__all__ = (
    "SourceBindingHistoricalImmutabilityProofV2Error",
    "verify_covapie_source_binding_historical_immutability_proof_v2",
)


_ERROR_PREFIX = "COVAPIE_SOURCE_BINDING_HISTORICAL_IMMUTABILITY_PROOF_V2_ERROR"
_PHASE_A_COMMIT = "26555ff6240ee53c817726331c8353dcb62dc82e"
_PHASE_A_TREE = "24280fbf73dd8785268b64889193b4735b8ca875"
_PHASE_A_SUBJECT = "add CovaPIE source binding filesystem mode authority v2 audit"
_PHASE_A_PARENT = "89a8cf17a235cdca9eecad275794a5a86be2e01d"
_PHASE_B2_COMMIT = "049d446e0fa854fab9986a9e2fb302d0b9547231"
_PHASE_B2_TREE = "f4671ea46de9f0781e33be5778fd08aebdf8ce39"
_PHASE_B2_SUBJECT = "add CovaPIE source binding active consumer integration v2"
_PHASE_B2_PARENT = "1e77d93929e491e589060269416b34fe47c0fb15"

_AUDIT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_source_binding_filesystem_mode_authority_v2_audit"
)
_INVENTORY_PATH = _AUDIT_ROOT / (
    "covapie_source_binding_filesystem_mode_authority_v2_inventory.csv"
)
_SUMMARY_PATH = _AUDIT_ROOT / (
    "covapie_source_binding_filesystem_mode_authority_v2_summary.json"
)
_MANIFEST_PATH = _AUDIT_ROOT / (
    "covapie_source_binding_filesystem_mode_authority_v2_manifest.json"
)
_AUDIT_SPECS = (
    (
        "PHASE_A_INVENTORY",
        _INVENTORY_PATH,
        927298,
        "1a883153737428482e7e49b95ba26ab1b6790d1ff2daf3697cceaa3a722d26da",
    ),
    (
        "PHASE_A_SUMMARY",
        _SUMMARY_PATH,
        8728,
        "fe27c9e9aadbad76f8c330bf19286b840038cc0576b1a2de96fcd0546b5d10b0",
    ),
    (
        "PHASE_A_MANIFEST",
        _MANIFEST_PATH,
        609232,
        "bdd86d533517972013b20397865079ce666562845bde19d03987d58ba676af2b",
    ),
)

_PUBLISHED_SOURCE_SPECS = (
    (
        "SOURCE_BINDING_POLICY_V2",
        Path("src/covalent_ext/covapie_source_binding_policy_v2.py"),
        3704,
        "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
    ),
    (
        "SOURCE_BINDING_ACTIVE_CONSUMER_INTEGRATION_V2",
        Path(
            "src/covalent_ext/"
            "covapie_source_binding_active_consumer_integration_v2.py"
        ),
        33699,
        "42583a1b66c0a4a46ce653acdbd9e110f5988d39efc7a1ba3572bfc8b67c1022",
    ),
    (
        "SOURCE_BINDING_ACTIVE_CONSUMER_INTEGRATION_V2_CHECKER",
        Path(
            "scripts/check_covapie_source_binding_active_consumer_integration_v2.py"
        ),
        44670,
        "067559e1d663ae707cffe2a73b74415a1a383d4dedc098c7d1c2affe8e6c7416",
    ),
)

_MIGRATION_COMMITS = (
    (
        "94a59fef2922b8a450fe06538111ca62a0b78190",
        "add CovaPIE source binding policy v2",
    ),
    (
        "5a34e260e57598ab62905f0171e43a67acc188e2",
        "add CovaPIE YUN source binding successor v2",
    ),
    (
        "baab1358bcc8f776df20d8dc76ed476d51ba27f3",
        "add CovaPIE NEQ source binding successor v2",
    ),
    (
        "9e7d520de0baa5e5f107985f45b97f576bbd8fc0",
        "add CovaPIE CHT source binding successor v2",
    ),
    (
        "33d08ee6069592f0fe28ca53bed5615f578d10fc",
        "add CovaPIE OZJ source binding successor v2",
    ),
    (
        "a81be8b1260d14b385b0faf05e2ddcc56bd403d8",
        "add CovaPIE F24 source binding successor v2",
    ),
    (
        "1e77d93929e491e589060269416b34fe47c0fb15",
        "add CovaPIE 2A2 source binding successor v2",
    ),
    (
        _PHASE_B2_COMMIT,
        _PHASE_B2_SUBJECT,
    ),
)

_MIGRATION_EXACT32_PATHS = (
    "docs/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_cht_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_f24_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_neq_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_source_binding_active_consumer_integration_v2_guide.md",
    "docs/covapie_source_binding_policy_v2_guide.md",
    "docs/covapie_yun_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "scripts/check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_source_binding_active_consumer_integration_v2.py",
    "scripts/check_covapie_source_binding_policy_v2.py",
    "scripts/check_covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_source_binding_active_consumer_integration_v2.py",
    "src/covalent_ext/covapie_source_binding_policy_v2.py",
    "src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_source_binding_active_consumer_integration_v2.py",
    "tests/test_covapie_source_binding_policy_v2.py",
    "tests/test_covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py",
)

_ACTIVE_V1_TARGETS = (
    "scripts/check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py",
    "scripts/check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py",
    "src/covalent_ext/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py",
    "src/covalent_ext/covapie_cht_completed_decision_ingestion_and_task_label_availability_v1.py",
    "src/covalent_ext/covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py",
    "src/covalent_ext/covapie_neq_completed_decision_ingestion_and_task_label_availability_v1.py",
    "src/covalent_ext/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1.py",
    "src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py",
)

_KNOWN_REGRESSION_SPECS = (
    (
        "published_role_profile_runtime_owner",
        "DiffSBDD-base/src/covalent_ext/"
        "covapie_direct_attachment_optional_linker_runtime_v1.py",
        "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py",
        37255,
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
        "0644",
        622,
    ),
    (
        "canonical_role_and_task_semantics_owner",
        "DiffSBDD-base/src/covalent_ext/"
        "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py",
        "src/covalent_ext/"
        "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py",
        67274,
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
        "0644",
        628,
    ),
    (
        "published_1f8_event_task_label_availability",
        "DiffSBDD-base/data/derived/covalent_small/"
        "covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1/"
        "covapie_1f8_event_task_label_availability_v1.csv",
        "data/derived/covalent_small/"
        "covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1/"
        "covapie_1f8_event_task_label_availability_v1.csv",
        14662,
        "63520f56ddb1c9fa9f962fc79c009549897e18299139e6b160498ca48080fb30",
        "0600",
        481,
    ),
)

_PROVENANCE_VALIDATOR_IDENTITY = (
    "repository_parent_relative",
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "2A2_COVAPIE_BULK_REVIEW_UNIT_6B422BBF7FAD44F6/"
    "formal-human-decision-v1/validate_2a2_formal_human_decision_v1.py",
)

_SCAN_SCOPE_COUNTS = {
    "repository_python_files_scanned": 1199,
    "derived_json_files_inspected": 528,
    "external_authority_provenance_json_files_inspected": 14,
    "external_covapie_state_python_files_scanned": 14,
    "authority_provenance_json_files_inspected": 542,
    "total_files_scanned": 1755,
}
_INVENTORY_COLUMNS = (
    "occurrence_id",
    "source_scope",
    "source_path_namespace",
    "source_path",
    "line_start",
    "line_end",
    "ast_node_type",
    "matched_semantic_pattern",
    "expected_or_literal_mode",
    "semantic_class",
    "lifecycle_class",
    "debt_disposition",
    "is_git_tracked_source",
    "is_external_covapie_state_source",
    "mode_participates_in_admit_reject_decision",
    "bytes_or_sha_also_checked",
    "known_checkout_reconstruction_risk",
    "recommended_v2_action",
    "evidence_note",
)
_LIFECYCLE_COUNTS = {
    "ACTIVE_CURRENT_DEPENDENCY": 1576,
    "HISTORICAL_IMMUTABLE_V1": 261,
    "NEW_CURRENT_V2_REFERENCE": 0,
    "TEST_ONLY": 334,
    "DOCUMENTATION_ONLY": 0,
}
_DISPOSITION_COUNTS = {
    "PRESERVE_AS_IS": 1979,
    "PRESERVE_HISTORICAL_BUT_DO_NOT_PROPAGATE": 180,
    "V2_MIGRATION_REQUIRED": 12,
    "REVIEW_REQUIRED": 0,
}
_SEMANTIC_COUNTS = {
    "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE": 198,
    "SECURITY_HYGIENE_MODE_CHECK": 1295,
    "CANDIDATE_ARTIFACT_MODE_HYGIENE": 144,
    "GIT_EXECUTABLE_BIT_OR_FILE_CLASS_CONTRACT": 421,
    "REPORTING_OR_DIAGNOSTIC_MODE_METADATA": 113,
    "AMBIGUOUS_REQUIRES_HUMAN_REVIEW": 0,
}
_BINDING_FIELDS = {
    "artifact_role",
    "path",
    "path_namespace",
    "byte_count",
    "sha256",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_GIT_COMMANDS = frozenset(
    {"rev-parse", "merge-base", "rev-list", "show", "diff"}
)


class SourceBindingHistoricalImmutabilityProofV2Error(ValueError):
    """Raised unless all frozen historical bytes and history remain exact."""


def _fail(reason: str) -> NoReturn:
    raise SourceBindingHistoricalImmutabilityProofV2Error(
        f"{_ERROR_PREFIX}:{reason}"
    )


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git_bytes(repo_root: Path, *arguments: str) -> bytes:
    if not arguments or arguments[0] not in _ALLOWED_GIT_COMMANDS:
        _fail("GIT_COMMAND_NOT_ALLOWED")
    try:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=repo_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as error:
        raise SourceBindingHistoricalImmutabilityProofV2Error(
            f"{_ERROR_PREFIX}:GIT_EXECUTION_FAILED:{arguments[0]}"
        ) from error
    if completed.returncode:
        _fail("GIT_COMMAND_FAILED:" + arguments[0])
    return completed.stdout


def _git_text(repo_root: Path, *arguments: str) -> str:
    try:
        return _git_bytes(repo_root, *arguments).decode("utf-8").rstrip("\n")
    except UnicodeDecodeError as error:
        raise SourceBindingHistoricalImmutabilityProofV2Error(
            f"{_ERROR_PREFIX}:GIT_OUTPUT_UTF8_INVALID:{arguments[0]}"
        ) from error


def _git_blob(repo_root: Path, commit: str, relative: str) -> bytes:
    return _git_bytes(repo_root, "show", f"{commit}:{relative}")


def _verify_bound_bytes(
    *,
    path: Path,
    expected_byte_count: int,
    expected_sha256: str,
    label: str,
    expected_executable: bool | None = None,
) -> bytes:
    try:
        return source_binding_v2.verify_bound_source_v2(
            path=path,
            expected_byte_count=expected_byte_count,
            expected_sha256=expected_sha256,
            label=label,
            expected_executable=expected_executable,
        )
    except source_binding_v2.SourceBindingPolicyV2Error as error:
        raise SourceBindingHistoricalImmutabilityProofV2Error(
            f"{_ERROR_PREFIX}:BOUND_SOURCE_REJECTED:{label}"
        ) from error


def _verify_published_sources(repo_root: Path) -> None:
    for label, relative, byte_count, sha256 in _PUBLISHED_SOURCE_SPECS:
        _verify_bound_bytes(
            path=repo_root / relative,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label=label,
            expected_executable=False,
        )


def _verify_commit_identity(
    repo_root: Path,
    *,
    commit: str,
    tree: str,
    subject: str,
    parent: str,
    label: str,
) -> None:
    lines = _git_text(
        repo_root, "show", "-s", "--format=%T%n%s%n%P", commit
    ).splitlines()
    if lines != [tree, subject, parent]:
        _fail(label + "_IDENTITY_INVALID")


def _verify_migration_history(repo_root: Path) -> dict[str, int]:
    _verify_commit_identity(
        repo_root,
        commit=_PHASE_A_COMMIT,
        tree=_PHASE_A_TREE,
        subject=_PHASE_A_SUBJECT,
        parent=_PHASE_A_PARENT,
        label="PHASE_A",
    )
    _verify_commit_identity(
        repo_root,
        commit=_PHASE_B2_COMMIT,
        tree=_PHASE_B2_TREE,
        subject=_PHASE_B2_SUBJECT,
        parent=_PHASE_B2_PARENT,
        label="PHASE_B2",
    )
    if _git_text(repo_root, "merge-base", _PHASE_A_COMMIT, _PHASE_B2_COMMIT) != (
        _PHASE_A_COMMIT
    ):
        _fail("PHASE_A_NOT_EXACT_MERGE_BASE")
    if _git_text(
        repo_root,
        "rev-list",
        "--left-right",
        "--count",
        f"{_PHASE_A_COMMIT}...{_PHASE_B2_COMMIT}",
    ).split() != ["0", "8"]:
        _fail("MIGRATION_AHEAD_BEHIND_INVALID")
    commits = tuple(
        filter(
            None,
            _git_text(
                repo_root,
                "rev-list",
                "--reverse",
                f"{_PHASE_A_COMMIT}..{_PHASE_B2_COMMIT}",
            ).splitlines(),
        )
    )
    if commits != tuple(commit for commit, _subject in _MIGRATION_COMMITS):
        _fail("MIGRATION_COMMIT_CHAIN_INVALID")
    expected_parent = _PHASE_A_COMMIT
    for commit, subject in _MIGRATION_COMMITS:
        lines = _git_text(
            repo_root, "show", "-s", "--format=%P%n%s", commit
        ).splitlines()
        if lines != [expected_parent, subject]:
            _fail("MIGRATION_LINEAR_HISTORY_INVALID:" + commit)
        expected_parent = commit

    rename_aware = tuple(
        filter(
            None,
            _git_text(
                repo_root,
                "diff",
                "--name-status",
                "-M",
                "-C",
                _PHASE_A_COMMIT,
                _PHASE_B2_COMMIT,
            ).splitlines(),
        )
    )
    no_renames = tuple(
        filter(
            None,
            _git_text(
                repo_root,
                "diff",
                "--name-status",
                "--no-renames",
                _PHASE_A_COMMIT,
                _PHASE_B2_COMMIT,
            ).splitlines(),
        )
    )
    expected_rows = tuple("A\t" + path for path in _MIGRATION_EXACT32_PATHS)
    if rename_aware != expected_rows or no_renames != expected_rows:
        _fail("MIGRATION_EXACT32_ADDITIVE_DELTA_INVALID")
    status_counts = Counter(row.split("\t", 1)[0][0] for row in rename_aware)
    return {
        "commit_count": len(commits),
        "added": status_counts.get("A", 0),
        "modified": status_counts.get("M", 0),
        "deleted": status_counts.get("D", 0),
        "renamed": status_counts.get("R", 0),
    }


def _load_frozen_audit_documents(
    repo_root: Path,
) -> tuple[bytes, bytes, bytes, dict[str, object], dict[str, object]]:
    payloads: dict[Path, bytes] = {}
    for label, relative, byte_count, sha256 in _AUDIT_SPECS:
        phase_a = _git_blob(repo_root, _PHASE_A_COMMIT, relative.as_posix())
        phase_b2 = _git_blob(repo_root, _PHASE_B2_COMMIT, relative.as_posix())
        if (
            len(phase_a) != byte_count
            or _sha256(phase_a) != sha256
            or phase_b2 != phase_a
        ):
            _fail("FROZEN_AUDIT_BLOB_INVALID:" + label)
        current = _verify_bound_bytes(
            path=repo_root / relative,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label=label,
        )
        if current != phase_a:
            _fail("CURRENT_AUDIT_ARTIFACT_DRIFT:" + label)
        payloads[relative] = phase_a
    try:
        summary = json.loads(payloads[_SUMMARY_PATH].decode("utf-8"))
        manifest = json.loads(payloads[_MANIFEST_PATH].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SourceBindingHistoricalImmutabilityProofV2Error(
            f"{_ERROR_PREFIX}:PHASE_A_AUDIT_JSON_INVALID"
        ) from error
    if type(summary) is not dict or type(manifest) is not dict:
        _fail("PHASE_A_AUDIT_DOCUMENT_TYPE_INVALID")
    return (
        payloads[_INVENTORY_PATH],
        payloads[_SUMMARY_PATH],
        payloads[_MANIFEST_PATH],
        summary,
        manifest,
    )


def _resolve_frozen_path(
    repo_root: Path,
    *,
    path_namespace: str,
    relative_path: str,
) -> Path:
    pure = PurePosixPath(relative_path)
    if (
        not relative_path
        or pure.is_absolute()
        or ".." in pure.parts
        or pure.as_posix() == "."
    ):
        _fail("FROZEN_SOURCE_PATH_ESCAPE")
    if path_namespace == "repository_relative":
        allowed_root = repo_root.resolve()
        candidate = repo_root / Path(pure.as_posix())
    elif path_namespace == "repository_parent_relative":
        allowed_root = (repo_root.parent / "covapie-state").resolve()
        candidate = repo_root.parent / Path(pure.as_posix())
    else:
        _fail("FROZEN_SOURCE_NAMESPACE_INVALID")
    try:
        candidate.resolve().relative_to(allowed_root)
    except (OSError, ValueError) as error:
        raise SourceBindingHistoricalImmutabilityProofV2Error(
            f"{_ERROR_PREFIX}:FROZEN_SOURCE_ROOT_ESCAPE"
        ) from error
    return candidate


def _verify_all_scanned_sources(
    repo_root: Path,
    manifest: dict[str, object],
) -> tuple[dict[tuple[str, str], dict[str, object]], bytes]:
    if manifest.get("scan_scope_counts") != _SCAN_SCOPE_COUNTS:
        _fail("PHASE_A_SCAN_SCOPE_COUNTS_INVALID")
    bindings = manifest.get("scanned_source_bindings")
    if type(bindings) is not list or len(bindings) != 1755:
        _fail("PHASE_A_SCANNED_BINDING_COUNT_INVALID")
    by_identity: dict[tuple[str, str], dict[str, object]] = {}
    namespace_counts: Counter[str] = Counter()
    provenance_validator = b""
    for index, record in enumerate(bindings):
        if type(record) is not dict or set(record) != _BINDING_FIELDS:
            _fail("PHASE_A_SCANNED_BINDING_SCHEMA_INVALID")
        path_value = record.get("path")
        namespace = record.get("path_namespace")
        byte_count = record.get("byte_count")
        sha256 = record.get("sha256")
        role = record.get("artifact_role")
        if (
            type(path_value) is not str
            or type(namespace) is not str
            or type(byte_count) is not int
            or byte_count < 0
            or type(sha256) is not str
            or _SHA256_RE.fullmatch(sha256) is None
            or type(role) is not str
            or not role
        ):
            _fail("PHASE_A_SCANNED_BINDING_VALUE_INVALID")
        identity = (namespace, path_value)
        if identity in by_identity:
            _fail("PHASE_A_SCANNED_BINDING_DUPLICATE")
        path = _resolve_frozen_path(
            repo_root,
            path_namespace=namespace,
            relative_path=path_value,
        )
        payload = _verify_bound_bytes(
            path=path,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label=f"PHASE_A_SCANNED_SOURCE_{index}",
            expected_executable=None,
        )
        by_identity[identity] = record
        namespace_counts[namespace] += 1
        if identity == _PROVENANCE_VALIDATOR_IDENTITY:
            provenance_validator = payload
    if namespace_counts != {
        "repository_relative": 1727,
        "repository_parent_relative": 28,
    }:
        _fail("PHASE_A_SCANNED_NAMESPACE_COMPOSITION_INVALID")
    if not provenance_validator:
        _fail("KNOWN_REGRESSION_PROVENANCE_VALIDATOR_UNMAPPED")
    return by_identity, provenance_validator


def _parse_inventory(inventory_payload: bytes) -> list[dict[str, str]]:
    try:
        text = inventory_payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SourceBindingHistoricalImmutabilityProofV2Error(
            f"{_ERROR_PREFIX}:PHASE_A_INVENTORY_UTF8_INVALID"
        ) from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != _INVENTORY_COLUMNS:
        _fail("PHASE_A_INVENTORY_HEADER_INVALID")
    rows = list(reader)
    if len(rows) != 2171 or any(set(row) != set(_INVENTORY_COLUMNS) for row in rows):
        _fail("PHASE_A_INVENTORY_ROWS_INVALID")
    return rows


def _verify_inventory_and_coverage(
    *,
    inventory_payload: bytes,
    summary: dict[str, object],
    bindings: dict[tuple[str, str], dict[str, object]],
) -> dict[str, int]:
    rows = _parse_inventory(inventory_payload)
    lifecycle = Counter(row["lifecycle_class"] for row in rows)
    disposition = Counter(row["debt_disposition"] for row in rows)
    semantic = Counter(row["semantic_class"] for row in rows)
    if set(lifecycle) - set(_LIFECYCLE_COUNTS) or {
        name: lifecycle.get(name, 0) for name in _LIFECYCLE_COUNTS
    } != _LIFECYCLE_COUNTS:
        _fail("PHASE_A_LIFECYCLE_COUNTS_INVALID")
    if set(disposition) - set(_DISPOSITION_COUNTS) or {
        name: disposition.get(name, 0) for name in _DISPOSITION_COUNTS
    } != _DISPOSITION_COUNTS:
        _fail("PHASE_A_DISPOSITION_COUNTS_INVALID")
    if set(semantic) - set(_SEMANTIC_COUNTS) or {
        name: semantic.get(name, 0) for name in _SEMANTIC_COUNTS
    } != _SEMANTIC_COUNTS:
        _fail("PHASE_A_SEMANTIC_COUNTS_INVALID")
    if (
        summary.get("lifecycle_class_counts") != _LIFECYCLE_COUNTS
        or summary.get("debt_disposition_counts") != _DISPOSITION_COUNTS
        or summary.get("semantic_class_counts") != _SEMANTIC_COUNTS
    ):
        _fail("PHASE_A_SUMMARY_CLASSIFICATION_COUNTS_INVALID")
    inventory_counts = summary.get("inventory_counts")
    if type(inventory_counts) is not dict or (
        inventory_counts.get("total_relevant_mode_occurrences") != 2171
        or inventory_counts.get("active_v2_migration_target_file_count") != 8
        or inventory_counts.get("active_v2_migration_target_files")
        != list(_ACTIVE_V1_TARGETS)
    ):
        _fail("PHASE_A_SUMMARY_INVENTORY_COUNTS_INVALID")

    all_identities = {
        (row["source_path_namespace"], row["source_path"]) for row in rows
    }
    if not all_identities <= set(bindings):
        _fail("PHASE_A_OCCURRENCE_SOURCE_UNMAPPED")
    historical_identities = {
        (row["source_path_namespace"], row["source_path"])
        for row in rows
        if row["lifecycle_class"] == "HISTORICAL_IMMUTABLE_V1"
    }
    preserve_identities = {
        (row["source_path_namespace"], row["source_path"])
        for row in rows
        if row["debt_disposition"]
        == "PRESERVE_HISTORICAL_BUT_DO_NOT_PROPAGATE"
    }
    historical_unmapped = len(historical_identities - set(bindings))
    preserve_unmapped = len(preserve_identities - set(bindings))
    if historical_unmapped or preserve_unmapped:
        _fail("PHASE_A_HISTORICAL_SOURCE_COVERAGE_INVALID")
    return {
        "historical_unmapped": historical_unmapped,
        "preserve_unmapped": preserve_unmapped,
    }


def _verify_active_v1_targets(
    repo_root: Path,
    bindings: dict[tuple[str, str], dict[str, object]],
) -> None:
    for relative in _ACTIVE_V1_TARGETS:
        phase_a = _git_blob(repo_root, _PHASE_A_COMMIT, relative)
        phase_b2 = _git_blob(repo_root, _PHASE_B2_COMMIT, relative)
        if phase_b2 != phase_a:
            _fail("ACTIVE_V1_TARGET_B2_DRIFT:" + relative)
        binding = bindings.get(("repository_relative", relative))
        if (
            binding is None
            or binding.get("byte_count") != len(phase_a)
            or binding.get("sha256") != _sha256(phase_a)
        ):
            _fail("ACTIVE_V1_TARGET_PHASE_A_BINDING_INVALID:" + relative)
        current = _verify_bound_bytes(
            path=repo_root / relative,
            expected_byte_count=len(phase_a),
            expected_sha256=_sha256(phase_a),
            label="ACTIVE_V1_TARGET:" + relative,
            expected_executable=None,
        )
        if current != phase_a:
            _fail("ACTIVE_V1_TARGET_CURRENT_DRIFT:" + relative)


def _assignment_constants(payload: bytes) -> dict[str, object]:
    try:
        tree = ast.parse(payload.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise SourceBindingHistoricalImmutabilityProofV2Error(
            f"{_ERROR_PREFIX}:KNOWN_REGRESSION_PROVENANCE_AST_INVALID"
        ) from error
    constants: dict[str, object] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant)
            and type(node.value.value) in {str, int}
        ):
            constants[node.targets[0].id] = node.value.value
    return constants


def _verify_known_regressions(
    *,
    repo_root: Path,
    summary: dict[str, object],
    bindings: dict[tuple[str, str], dict[str, object]],
    provenance_validator: bytes,
) -> None:
    cases = summary.get("known_regression_cases")
    if type(cases) is not list or len(cases) != 3:
        _fail("KNOWN_REGRESSION_CASES_NOT_EXACT3")
    for case, spec in zip(cases, _KNOWN_REGRESSION_SPECS, strict=True):
        role, published_path, _relative, _size, _sha, mode, line = spec
        expected_case = {
            "source_role": role,
            "path": published_path,
            "path_namespace": "project_parent_relative",
            "expected_mode": mode,
            "content_identity_contract": ["byte_count", "sha256"],
            "semantic_class": "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE",
            "lifecycle_class": "HISTORICAL_IMMUTABLE_V1",
            "debt_disposition": "PRESERVE_HISTORICAL_BUT_DO_NOT_PROPAGATE",
            "static_contract_line": line,
            "byte_sha_can_remain_exact_while_checkout_mode_changes": True,
        }
        if case != expected_case:
            _fail("KNOWN_REGRESSION_PHASE_A_METADATA_INVALID:" + role)

    constants = _assignment_constants(provenance_validator)
    expected_constants = {
        "ROLE_RUNTIME_PATH": _KNOWN_REGRESSION_SPECS[0][1],
        "ROLE_RUNTIME_BYTES": _KNOWN_REGRESSION_SPECS[0][3],
        "ROLE_RUNTIME_SHA256": _KNOWN_REGRESSION_SPECS[0][4],
        "ROLE_OWNER_PATH": _KNOWN_REGRESSION_SPECS[1][1],
        "ROLE_OWNER_BYTES": _KNOWN_REGRESSION_SPECS[1][3],
        "ROLE_OWNER_SHA256": _KNOWN_REGRESSION_SPECS[1][4],
        "ONE_F8_PATH": _KNOWN_REGRESSION_SPECS[2][1],
        "ONE_F8_BYTES": _KNOWN_REGRESSION_SPECS[2][3],
        "ONE_F8_SHA256": _KNOWN_REGRESSION_SPECS[2][4],
    }
    if any(constants.get(key) != value for key, value in expected_constants.items()):
        _fail("KNOWN_REGRESSION_PHASE_A_CONTENT_BINDING_INVALID")

    for _role, _published, relative, byte_count, sha256, _mode, _line in (
        _KNOWN_REGRESSION_SPECS
    ):
        phase_a = _git_blob(repo_root, _PHASE_A_COMMIT, relative)
        phase_b2 = _git_blob(repo_root, _PHASE_B2_COMMIT, relative)
        if (
            len(phase_a) != byte_count
            or _sha256(phase_a) != sha256
            or phase_b2 != phase_a
        ):
            _fail("KNOWN_REGRESSION_GIT_BLOB_INVALID:" + relative)
        current = _verify_bound_bytes(
            path=repo_root / relative,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label="KNOWN_REGRESSION_REFERENCE:" + relative,
            expected_executable=None,
        )
        if current != phase_a:
            _fail("KNOWN_REGRESSION_CURRENT_DRIFT:" + relative)
        binding = bindings.get(("repository_relative", relative))
        if relative.endswith(".py") and (
            binding is None
            or binding.get("byte_count") != byte_count
            or binding.get("sha256") != sha256
        ):
            _fail("KNOWN_REGRESSION_SCANNED_BINDING_INVALID:" + relative)


def _verify_b2_integration(repo_root: Path) -> dict[str, object]:
    try:
        result = integration_v2.verify_covapie_source_binding_active_consumer_integration_v2(
            repo_root=repo_root
        )
    except ValueError as error:
        raise SourceBindingHistoricalImmutabilityProofV2Error(
            f"{_ERROR_PREFIX}:PUBLISHED_B2_INTEGRATION_REJECTED"
        ) from error
    required = {
        "filesystem_source_acceptance_authority": "SOURCE_BINDING_POLICY_V2",
        "sample_scientific_projection_authority": "PUBLISHED_V1_ARTIFACTS",
        "current_global_state_authority": "PUBLISHED_2A2_V1_GLOBAL_CENSUS",
        "active_consumer_count": 6,
        "artifact_projection_count": 24,
        "all_V2_successor_sources_bound": True,
        "all_V2_projections_executed": True,
        "all_V1_scientific_projections_preserved": True,
        "current_2A2_census_unchanged": True,
        "scientific_authority_reinterpreted": False,
        "global_census_refreshed": False,
        "reconciliation_executed": False,
        "data_materialized": False,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "v2_migration_phase_b2_effective_state_integrated": True,
        "ready_for_training": False,
    }
    if type(result) is not dict:
        _fail("PUBLISHED_B2_RESULT_TYPE_INVALID")
    for key, expected in required.items():
        if result.get(key) != expected or type(result.get(key)) is not type(expected):
            _fail("PUBLISHED_B2_RESULT_INVALID:" + key)
    return result


def verify_covapie_source_binding_historical_immutability_proof_v2(
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Prove Phase-A source bytes and the additive Phase-B2 history are frozen."""

    if not isinstance(repo_root, Path):
        _fail("REPO_ROOT_TYPE_INVALID")
    repo_root = repo_root.resolve()
    _verify_published_sources(repo_root)
    migration = _verify_migration_history(repo_root)
    inventory_payload, _summary_payload, _manifest_payload, summary, manifest = (
        _load_frozen_audit_documents(repo_root)
    )
    bindings, provenance_validator = _verify_all_scanned_sources(
        repo_root, manifest
    )
    coverage = _verify_inventory_and_coverage(
        inventory_payload=inventory_payload,
        summary=summary,
        bindings=bindings,
    )
    _verify_active_v1_targets(repo_root, bindings)
    _verify_known_regressions(
        repo_root=repo_root,
        summary=summary,
        bindings=bindings,
        provenance_validator=provenance_validator,
    )
    b2 = _verify_b2_integration(repo_root)

    return {
        "schema_version": "covapie_source_binding_historical_immutability_proof_v2",
        "phase_a_audit_commit": _PHASE_A_COMMIT,
        "phase_b2_published_commit": _PHASE_B2_COMMIT,
        "migration_commit_count": migration["commit_count"],
        "migration_added_path_count": migration["added"],
        "migration_modified_path_count": migration["modified"],
        "migration_deleted_path_count": migration["deleted"],
        "migration_renamed_path_count": migration["renamed"],
        "phase_a_scanned_source_binding_count": len(bindings),
        "repository_scanned_source_binding_count": 1727,
        "external_covapie_state_scanned_source_binding_count": 28,
        "historical_immutable_occurrence_count": 261,
        "preserve_historical_do_not_propagate_occurrence_count": 180,
        "phase_a_v2_migration_required_occurrence_count": 12,
        "ambiguous_review_required_occurrence_count": 0,
        "active_v1_migration_target_file_count": len(_ACTIVE_V1_TARGETS),
        "known_regression_reference_count": len(_KNOWN_REGRESSION_SPECS),
        "historical_occurrence_source_unmapped_count": coverage[
            "historical_unmapped"
        ],
        "preserve_historical_source_unmapped_count": coverage[
            "preserve_unmapped"
        ],
        "all_phase_a_scanned_source_bytes_unchanged": True,
        "all_repository_scanned_source_bytes_unchanged": True,
        "all_external_covapie_state_scanned_source_bytes_unchanged": True,
        "all_historical_immutable_occurrence_sources_unchanged": True,
        "all_preserve_historical_occurrence_sources_unchanged": True,
        "all_active_v1_migration_target_bytes_unchanged": True,
        "known_regression_reference_bytes_unchanged": True,
        "phase_a_audit_artifacts_unchanged": True,
        "filesystem_source_acceptance_authority": (
            "SOURCE_BINDING_POLICY_V2"
        ),
        "sample_scientific_projection_authority": "PUBLISHED_V1_ARTIFACTS",
        "current_global_state_authority": "PUBLISHED_2A2_V1_GLOBAL_CENSUS",
        "historical_immutability_reference": (
            "PHASE_A_AUDIT_FROZEN_SOURCE_BINDINGS"
        ),
        "historical_v1_authority_modified": False,
        "historical_validator_rewrite_performed": False,
        "historical_exact_mode_metadata_rewritten": False,
        "historical_exact_mode_metadata_preserved": True,
        "scientific_authority_reinterpreted": False,
        "current_census_refreshed": False,
        "reconciliation_executed": False,
        "data_materialized": False,
        "b2_integration_verified": True,
        "active_consumer_count": b2["active_consumer_count"],
        "artifact_projection_count": b2["artifact_projection_count"],
        "all_V2_successor_sources_bound": b2[
            "all_V2_successor_sources_bound"
        ],
        "all_V2_projections_executed": b2["all_V2_projections_executed"],
        "all_V1_scientific_projections_preserved": b2[
            "all_V1_scientific_projections_preserved"
        ],
        "current_2A2_census_unchanged": b2["current_2A2_census_unchanged"],
        "global_canonical_task_count": b2["global_canonical_task_count"],
        "B3_present": b2["B3_present"],
        "sixth_task_present": b2["sixth_task_present"],
        "v2_migration_phase_b3_historical_immutability_proven": True,
        "ready_for_v2_migration_phase_b4_future_guard": True,
        "ready_for_training": False,
    }
