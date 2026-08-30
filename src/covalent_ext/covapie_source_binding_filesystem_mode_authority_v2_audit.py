"""Read-only Phase-A audit of exact POSIX mode source-identity coupling.

The scan universe is frozen at the published 2A2 census baseline.  Existing
validators and authority bytes are inputs only.  This module creates audit
evidence and a V2 design gate; it does not implement a runtime/helper policy.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any, NoReturn


__all__ = (
    "SourceBindingFilesystemModeAuthorityV2AuditError",
    "classify_python_text_v2",
    "compute_covapie_source_binding_filesystem_mode_authority_v2_audit",
    "build_covapie_source_binding_filesystem_mode_authority_v2_audit_artifacts",
    "materialize_covapie_source_binding_filesystem_mode_authority_v2_audit_artifacts",
)


SCHEMA_VERSION = "covapie_source_binding_filesystem_mode_authority_v2_audit_v1"
STAGE = "COVAPIE_SOURCE_BINDING_FILESYSTEM_MODE_AUTHORITY_V2_AUDIT"
ERROR_TOKEN = "COVAPIE_SOURCE_BINDING_FILESYSTEM_MODE_AUTHORITY_V2_AUDIT_ERROR"

BASELINE_HEAD = "89a8cf17a235cdca9eecad275794a5a86be2e01d"
BASELINE_TREE = "1fade78157312f44ef27232953d958453837bfb1"
BASELINE_SUBJECT = "add CovaPIE global readiness census with 2A2 v1"

PRODUCTION_RELATIVE = Path(
    "src/covalent_ext/covapie_source_binding_filesystem_mode_authority_v2_audit.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_source_binding_filesystem_mode_authority_v2_audit.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_source_binding_filesystem_mode_authority_v2_audit.py"
)
GUIDE_RELATIVE = Path(
    "docs/covapie_source_binding_filesystem_mode_authority_v2_audit_guide.md"
)
OUTPUT_DIRECTORY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_source_binding_filesystem_mode_authority_v2_audit"
)
INVENTORY_FILE = "covapie_source_binding_filesystem_mode_authority_v2_inventory.csv"
SUMMARY_FILE = "covapie_source_binding_filesystem_mode_authority_v2_summary.json"
MANIFEST_FILE = "covapie_source_binding_filesystem_mode_authority_v2_manifest.json"

EXACT7_PATHS = (
    PRODUCTION_RELATIVE.as_posix(),
    CHECKER_RELATIVE.as_posix(),
    TEST_RELATIVE.as_posix(),
    GUIDE_RELATIVE.as_posix(),
    (OUTPUT_DIRECTORY_RELATIVE / INVENTORY_FILE).as_posix(),
    (OUTPUT_DIRECTORY_RELATIVE / SUMMARY_FILE).as_posix(),
    (OUTPUT_DIRECTORY_RELATIVE / MANIFEST_FILE).as_posix(),
)

CURRENT_CENSUS_OWNER_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1.py"
)
CURRENT_CENSUS_DIRECTORY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1"
)
CURRENT_CENSUS_MANIFEST_RELATIVE = CURRENT_CENSUS_DIRECTORY_RELATIVE / (
    "covapie_cumulative1000_current_global_readiness_manifest_with_2a2_v1.json"
)
CURRENT_CENSUS_SUMMARY_RELATIVE = CURRENT_CENSUS_DIRECTORY_RELATIVE / (
    "covapie_cumulative1000_current_global_readiness_summary_with_2a2_v1.json"
)
CURRENT_CENSUS_BINDING_COUNT = 108
CURRENT_CENSUS_BINDING_DIGEST = (
    "964f4b3747d42a43d05d1adc6f432264ce546ef93f9faace23fa3379452bfd15"
)
CURRENT_CENSUS_BINDING_FIELDS = (
    "artifact_role",
    "path",
    "path_namespace",
    "byte_count",
    "sha256",
)

EXTERNAL_SCAN_ROOT_RELATIVE = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1"
)
EXTERNAL_ALLOWED_STAGE_DIRECTORIES = frozenset(
    {
        "review-preparation-v1",
        "human-review-preview-v1",
        "formal-human-decision-v1",
    }
)
EXTERNAL_JSON_STAGE_DIRECTORIES = frozenset(
    {"human-review-preview-v1", "formal-human-decision-v1"}
)

TWO_A2_FORMAL_VALIDATOR_RELATIVE = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "2A2_COVAPIE_BULK_REVIEW_UNIT_6B422BBF7FAD44F6/"
    "formal-human-decision-v1/validate_2a2_formal_human_decision_v1.py"
)
KNOWN_REGRESSION_EXPECTATIONS = (
    (
        "published_role_profile_runtime_owner",
        "DiffSBDD-base/src/covalent_ext/"
        "covapie_direct_attachment_optional_linker_runtime_v1.py",
        "0644",
    ),
    (
        "canonical_role_and_task_semantics_owner",
        "DiffSBDD-base/src/covalent_ext/"
        "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py",
        "0644",
    ),
    (
        "published_1f8_event_task_label_availability",
        "DiffSBDD-base/data/derived/covalent_small/"
        "covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1/"
        "covapie_1f8_event_task_label_availability_v1.csv",
        "0600",
    ),
)

SEMANTIC_CLASSES = (
    "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE",
    "SECURITY_HYGIENE_MODE_CHECK",
    "CANDIDATE_ARTIFACT_MODE_HYGIENE",
    "GIT_EXECUTABLE_BIT_OR_FILE_CLASS_CONTRACT",
    "REPORTING_OR_DIAGNOSTIC_MODE_METADATA",
    "AMBIGUOUS_REQUIRES_HUMAN_REVIEW",
)
LIFECYCLE_CLASSES = (
    "HISTORICAL_IMMUTABLE_V1",
    "ACTIVE_CURRENT_DEPENDENCY",
    "NEW_CURRENT_V2_REFERENCE",
    "TEST_ONLY",
    "DOCUMENTATION_ONLY",
)
DEBT_DISPOSITIONS = (
    "V2_MIGRATION_REQUIRED",
    "PRESERVE_AS_IS",
    "PRESERVE_HISTORICAL_BUT_DO_NOT_PROPAGATE",
    "REVIEW_REQUIRED",
)

INVENTORY_COLUMNS = (
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

_PERMISSION_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:0o)?(?:0600|0644|0664|0755|0775|600|644|664|755|775|"
    r"100644|100755)(?![A-Za-z0-9_])"
)
_QUOTED_PERMISSION_RE = re.compile(
    r"[\"'](0?600|0?644|0?664|0?755|0?775|100644|100755|0o600|0o644|"
    r"0o664|0o755|0o775)[\"']"
)
_MODE_KEY_RE = re.compile(
    r"^(?:mode|posix_mode|filesystem_mode|st_mode|git_mode|path_modes|"
    r"head_candidate_path_modes|candidate_filesystem_modes)$"
)
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class SourceBindingFilesystemModeAuthorityV2AuditError(ValueError):
    """Raised unless the audit remains bounded, static, and fail-closed."""


def _fail(reason: str) -> NoReturn:
    raise SourceBindingFilesystemModeAuthorityV2AuditError(
        f"{ERROR_TOKEN}:{reason}"
    )


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _csv_bytes(rows: Sequence[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=INVENTORY_COLUMNS,
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode:
        _fail("GIT_COMMAND_FAILED:" + arguments[0])
    return completed.stdout.rstrip("\n")


def _read_regular(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        _fail("SOURCE_NOT_REGULAR_OR_SYMLINK:" + label)
    try:
        return path.read_bytes()
    except OSError as error:
        raise SourceBindingFilesystemModeAuthorityV2AuditError(
            f"{ERROR_TOKEN}:SOURCE_READ_FAILED:{label}"
        ) from error


def _validate_relative_path(relative: str, namespace: str) -> None:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        _fail("SCAN_PATH_ESCAPE:" + namespace + ":" + relative)


def _baseline_paths(root: Path) -> tuple[str, ...]:
    lines = _git(root, "ls-tree", "-r", "--name-only", BASELINE_HEAD).splitlines()
    if not lines:
        _fail("BASELINE_TREE_EMPTY")
    return tuple(sorted(lines))


def _repository_python_paths(root: Path) -> tuple[Path, ...]:
    selected: list[Path] = []
    for relative in _baseline_paths(root):
        if not relative.endswith(".py"):
            continue
        if relative.startswith("src/covalent_ext/"):
            selected.append(Path(relative))
        elif relative.startswith("scripts/check_covapie"):
            selected.append(Path(relative))
        elif relative.startswith("tests/test_covapie"):
            selected.append(Path(relative))
    if not selected:
        _fail("REPOSITORY_PYTHON_SCOPE_EMPTY")
    return tuple(sorted(selected, key=lambda item: item.as_posix()))


def _derived_json_paths(root: Path) -> tuple[Path, ...]:
    prefix = "data/derived/covalent_small/"
    selected = tuple(
        Path(relative)
        for relative in _baseline_paths(root)
        if relative.startswith(prefix) and relative.endswith(".json")
    )
    if not selected:
        _fail("DERIVED_JSON_SCOPE_EMPTY")
    return tuple(sorted(selected, key=lambda item: item.as_posix()))


def _external_paths(root: Path) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    scan_root = root.parent / EXTERNAL_SCAN_ROOT_RELATIVE
    if not scan_root.is_dir() or scan_root.is_symlink():
        _fail("EXTERNAL_SCAN_ROOT_INVALID")
    python_paths: list[Path] = []
    json_paths: list[Path] = []
    for path in sorted(scan_root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        stage = path.parent.name
        if path.suffix == ".py" and stage in EXTERNAL_ALLOWED_STAGE_DIRECTORIES:
            python_paths.append(path)
        elif path.suffix == ".json" and stage in EXTERNAL_JSON_STAGE_DIRECTORIES:
            json_paths.append(path)
    if not python_paths or not json_paths:
        _fail("EXTERNAL_SCAN_SCOPE_INCOMPLETE")
    resolved_root = scan_root.resolve()
    for path in (*python_paths, *json_paths):
        try:
            path.resolve().relative_to(resolved_root)
        except ValueError:
            _fail("EXTERNAL_SCAN_PATH_ESCAPE")
    return tuple(python_paths), tuple(json_paths)


def _source_binding(
    root: Path,
    path: Path,
    *,
    namespace: str,
    artifact_role: str,
) -> dict[str, object]:
    if namespace == "repository_relative":
        relative = path.as_posix()
        absolute = root / path
    elif namespace == "repository_parent_relative":
        absolute = path
        relative = path.relative_to(root.parent).as_posix()
    else:
        _fail("SOURCE_NAMESPACE_INVALID:" + namespace)
    _validate_relative_path(relative, namespace)
    payload = _read_regular(absolute, artifact_role + ":" + relative)
    return {
        "artifact_role": artifact_role,
        "path": relative,
        "path_namespace": namespace,
        "byte_count": len(payload),
        "sha256": _sha256(payload),
    }


def _node_text(lines: Sequence[str], node: ast.AST) -> str:
    start = getattr(node, "lineno", 1)
    end = getattr(node, "end_lineno", start)
    if start == end:
        line = lines[start - 1]
        return line[
            getattr(node, "col_offset", 0) : getattr(node, "end_col_offset", len(line))
        ]
    pieces = list(lines[start - 1 : end])
    if not pieces:
        return ""
    pieces[0] = pieces[0][getattr(node, "col_offset", 0) :]
    pieces[-1] = pieces[-1][: getattr(node, "end_col_offset", len(pieces[-1]))]
    return "\n".join(pieces)


def _normalized_modes(text: str) -> str:
    values: list[str] = []
    for match in _PERMISSION_TOKEN_RE.finditer(text):
        value = match.group(0).lower()
        if value.startswith("0o"):
            value = value[2:]
        if value in {"600", "644", "664", "755", "775"}:
            value = "0" + value
        if value not in values:
            values.append(value)
    return "|".join(values)


def _filesystem_signal(text: str) -> bool:
    lowered = text.lower()
    return bool(
        "stat.s_imode" in lowered
        or re.search(r"\bst_mode\b", lowered)
        or "chmod" in lowered
        or "stat.s_is" in lowered
        or "stat.s_iw" in lowered
        or "stat.s_ix" in lowered
        or re.search(r"\bfilesystem_mode\b", lowered)
        or re.search(r"\bposix_mode\b", lowered)
        or re.search(r"\bgit_mode\b", lowered)
        or re.search(r"\bpath_modes\b", lowered)
        or re.search(r"\bcandidate_filesystem_modes\b", lowered)
        or re.search(
            r"\b(?:expected_mode|current_mode|file_mode|live_mode)\b", lowered
        )
        or (
            _PERMISSION_TOKEN_RE.search(text)
            and re.search(r"\b(?:expected_|current_|file_|live_)?mode\b", lowered)
        )
    )


def _call_name(node: ast.Call) -> str:
    parts: list[str] = []
    current: ast.AST = node.func
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _enclosing_function(
    node: ast.AST, parents: Mapping[ast.AST, ast.AST]
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
        current = parents.get(current)
    return None


def _semantic_context(
    expression: str,
    function_text: str,
    nearby_text: str,
) -> bool:
    joined = "\n".join((expression, function_text, nearby_text)).lower()
    direct_drift = any(
        token in joined
        for token in (
            "source_drift",
            "source_mode_drift",
            "bound_source_mode_drift",
            "formal_evidence_source_drift",
        )
    )
    identity_terms = (
        ("sha256" in joined or "sha(" in joined or "_sha(" in joined)
        and (
            "byte_count" in joined
            or "len(payload)" in joined
            or "st_size" in joined
            or "expected_bytes" in joined
        )
    )
    binding_terms = any(
        token in joined
        for token in (
            "source_binding",
            "source_specs",
            "formal_binding",
            "evidence_binding",
            "bound_source",
            "read_bound_file",
            "verify_binding",
        )
    )
    return direct_drift or (identity_terms and binding_terms)


def _classify_expression(
    expression: str,
    *,
    function_text: str,
    nearby_text: str,
    node_kind: str,
    is_admit_reject: bool,
) -> tuple[str, str, bool, bool, str, str]:
    lowered = expression.lower()
    context = "\n".join((expression, function_text, nearby_text)).lower()
    modes = _normalized_modes(expression)
    bytes_or_sha = bool(
        ("sha" in context and ("byte" in context or "len(payload)" in context))
    )
    git_contract = bool(
        "100644" in context
        or "100755" in context
        or "git_mode" in context
        or "path_modes" in context
        or "ls-tree" in context
        or "ls-files" in context and "mode" in context
    )
    safe_family = bool(
        ({"0644", "0664"} <= set(modes.split("|")))
        and (" in " in lowered or "not in" in lowered)
    )
    security_bits = any(
        token in context
        for token in (
            "stat.s_isreg",
            "stat.s_islnk",
            "stat.s_isdir",
            "stat.s_iwoth",
            "stat.s_ix",
            "0o111",
            "world_writ",
            "symlink",
            "regular_file",
        )
    )
    semantic = _semantic_context(expression, function_text, nearby_text)
    candidate_terms = any(
        token in context
        for token in (
            "candidate",
            "artifact",
            "output",
            "package",
            "exact7",
            "exact",
            "file_hygiene",
            "materializ",
            "publication",
        )
    )

    if git_contract:
        semantic_class = "GIT_EXECUTABLE_BIT_OR_FILE_CLASS_CONTRACT"
        pattern = "git_executable_or_regular_blob_class"
        note = "Git 100644/100755 class; not runtime POSIX identity."
    elif node_kind == "DictModeMetadata":
        semantic_class = "REPORTING_OR_DIAGNOSTIC_MODE_METADATA"
        pattern = "mode_metadata_recording"
        note = "Mode metadata only; rejection is inventoried separately."
    elif safe_family:
        semantic_class = "CANDIDATE_ARTIFACT_MODE_HYGIENE"
        pattern = "candidate_safe_mode_family_0644_0664"
        note = "Candidate accepts non-executable 0644/0664."
    elif semantic and is_admit_reject:
        semantic_class = "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE"
        pattern = "exact_posix_mode_joined_to_byte_sha_source_identity"
        note = "Exact mode rejects source alongside byte/SHA identity."
    elif security_bits:
        semantic_class = "SECURITY_HYGIENE_MODE_CHECK"
        pattern = "regular_symlink_executable_or_writable_safety_check"
        note = "Filesystem type or dangerous-bit hygiene."
    elif "st_mode" in lowered and any(
        token in context for token in ("st_dev", "st_ino", "fstat")
    ):
        semantic_class = "SECURITY_HYGIENE_MODE_CHECK"
        pattern = "descriptor_or_path_identity_stability_hygiene"
        note = "Descriptor/path metadata stability hygiene."
    elif "chmod" in lowered or (
        candidate_terms and _filesystem_signal(expression)
    ) or (modes and is_admit_reject):
        semantic_class = "CANDIDATE_ARTIFACT_MODE_HYGIENE"
        pattern = "candidate_or_output_mode_hygiene"
        note = "Operational artifact mode; not source identity."
    elif semantic and modes:
        semantic_class = "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE"
        pattern = "exact_posix_mode_source_binding_specification"
        note = "Source binding specifies exact runtime POSIX mode."
    elif is_admit_reject and _filesystem_signal(expression):
        semantic_class = "AMBIGUOUS_REQUIRES_HUMAN_REVIEW"
        pattern = "mode_gate_semantics_not_statically_resolved"
        note = "Static evidence cannot resolve identity versus hygiene."
    else:
        semantic_class = "REPORTING_OR_DIAGNOSTIC_MODE_METADATA"
        pattern = "mode_reporting_or_intermediate_metadata"
        note = "Mode metadata without observed semantic rejection."
    risk = semantic_class == "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE"
    return semantic_class, pattern, bytes_or_sha, risk, modes, note


def _lifecycle_for_path(source_path: str, source_scope: str) -> str:
    if source_scope.startswith("EXTERNAL_") or source_scope == "DERIVED_JSON":
        return "HISTORICAL_IMMUTABLE_V1"
    if source_path.startswith("tests/"):
        return "TEST_ONLY"
    if source_path == GUIDE_RELATIVE.as_posix():
        return "DOCUMENTATION_ONLY"
    if source_path in {
        PRODUCTION_RELATIVE.as_posix(),
        CHECKER_RELATIVE.as_posix(),
    }:
        return "NEW_CURRENT_V2_REFERENCE"
    return "ACTIVE_CURRENT_DEPENDENCY"


def _disposition(semantic_class: str, lifecycle_class: str) -> str:
    if semantic_class == "AMBIGUOUS_REQUIRES_HUMAN_REVIEW":
        return "REVIEW_REQUIRED"
    if semantic_class == "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE":
        if lifecycle_class == "HISTORICAL_IMMUTABLE_V1":
            return "PRESERVE_HISTORICAL_BUT_DO_NOT_PROPAGATE"
        if lifecycle_class in {
            "ACTIVE_CURRENT_DEPENDENCY",
            "NEW_CURRENT_V2_REFERENCE",
        }:
            return "V2_MIGRATION_REQUIRED"
        return "PRESERVE_AS_IS"
    return "PRESERVE_AS_IS"


def _recommended_action(semantic_class: str, lifecycle_class: str) -> str:
    if semantic_class == "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE":
        if lifecycle_class == "HISTORICAL_IMMUTABLE_V1":
            return "freeze V1; no propagation; disposable replay only"
        if lifecycle_class == "TEST_ONLY":
            return "retain V1 test; add V2 separation regression"
        return "use content identity plus separate safe-mode gate"
    if semantic_class == "SECURITY_HYGIENE_MODE_CHECK":
        return "preserve explicit safety gate"
    if semantic_class == "CANDIDATE_ARTIFACT_MODE_HYGIENE":
        return "preserve non-executable 0644/0664 family"
    if semantic_class == "GIT_EXECUTABLE_BIT_OR_FILE_CLASS_CONTRACT":
        return "preserve Git 100644/100755 class"
    if semantic_class == "REPORTING_OR_DIAGNOSTIC_MODE_METADATA":
        return "preserve reporting; exclude from identity"
    return "human review before V2 change"


def _occurrence_id(row: Mapping[str, object]) -> str:
    identity = "|".join(
        str(row[key])
        for key in (
            "source_scope",
            "source_path_namespace",
            "source_path",
            "line_start",
            "line_end",
            "ast_node_type",
            "matched_semantic_pattern",
            "expected_or_literal_mode",
            "evidence_note",
        )
    )
    return "FMV2-" + _sha256(identity.encode("utf-8"))[:20].upper()


def _make_occurrence(
    *,
    source_scope: str,
    namespace: str,
    source_path: str,
    line_start: int,
    line_end: int,
    ast_node_type: str,
    semantic_class: str,
    matched_pattern: str,
    modes: str,
    lifecycle: str,
    bytes_or_sha: bool,
    risk: bool,
    note: str,
    is_admit_reject: bool,
) -> dict[str, object]:
    disposition = _disposition(semantic_class, lifecycle)
    row: dict[str, object] = {
        "source_scope": source_scope,
        "source_path_namespace": namespace,
        "source_path": source_path,
        "line_start": line_start,
        "line_end": line_end,
        "ast_node_type": ast_node_type,
        "matched_semantic_pattern": matched_pattern,
        "expected_or_literal_mode": modes,
        "semantic_class": semantic_class,
        "lifecycle_class": lifecycle,
        "debt_disposition": disposition,
        "is_git_tracked_source": source_scope in {
            "REPOSITORY_OWNER_PYTHON",
            "REPOSITORY_CHECKER_PYTHON",
            "REPOSITORY_TEST_PYTHON",
            "DERIVED_JSON",
        },
        "is_external_covapie_state_source": source_scope.startswith("EXTERNAL_"),
        "mode_participates_in_admit_reject_decision": (
            semantic_class == "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE"
            and is_admit_reject
        ),
        "bytes_or_sha_also_checked": bytes_or_sha,
        "known_checkout_reconstruction_risk": risk,
        "recommended_v2_action": _recommended_action(
            semantic_class, lifecycle
        ),
        "evidence_note": note,
    }
    row["occurrence_id"] = _occurrence_id(row)
    return {column: row[column] for column in INVENTORY_COLUMNS}


def classify_python_text_v2(
    text: str,
    *,
    source_path: str,
    source_scope: str,
    source_path_namespace: str,
) -> tuple[dict[str, object], ...]:
    """Classify filesystem-mode occurrences without executing the source."""

    try:
        tree = ast.parse(text, filename=source_path)
    except SyntaxError as error:
        _fail("PYTHON_AST_PARSE_FAILED:" + source_path + f":{error.lineno}")
    lines = text.splitlines()
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    lifecycle = _lifecycle_for_path(source_path, source_scope)
    occurrences: list[dict[str, object]] = []
    occupied: set[tuple[int, int, str]] = set()

    def add(
        node: ast.AST,
        expression: str,
        node_kind: str,
        *,
        admit_reject: bool,
    ) -> None:
        function = _enclosing_function(node, parents)
        function_text = _node_text(lines, function) if function is not None else ""
        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", start)
        nearby = "\n".join(lines[max(0, start - 4) : min(len(lines), end + 3)])
        classified = _classify_expression(
            expression,
            function_text=function_text,
            nearby_text=nearby,
            node_kind=node_kind,
            is_admit_reject=admit_reject,
        )
        semantic_class, pattern, bytes_or_sha, risk, modes, note = classified
        key = (start, end, node_kind + ":" + pattern)
        if key in occupied:
            return
        occupied.add(key)
        occurrences.append(
            _make_occurrence(
                source_scope=source_scope,
                namespace=source_path_namespace,
                source_path=source_path,
                line_start=start,
                line_end=end,
                ast_node_type=node_kind,
                semantic_class=semantic_class,
                matched_pattern=pattern,
                modes=modes,
                lifecycle=lifecycle,
                bytes_or_sha=bytes_or_sha,
                risk=risk,
                note=note,
                is_admit_reject=admit_reject,
            )
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            expression = _node_text(lines, node.test)
            if _filesystem_signal(expression):
                add(node.test, expression, "IfTest", admit_reject=True)
        elif isinstance(node, ast.Assert):
            expression = _node_text(lines, node.test)
            if _filesystem_signal(expression):
                add(node.test, expression, "AssertTest", admit_reject=True)
        elif isinstance(node, ast.Compare):
            expression = _node_text(lines, node)
            ancestor = parents.get(node)
            inside_guard = False
            while ancestor is not None:
                if isinstance(ancestor, (ast.If, ast.Assert)):
                    inside_guard = True
                    break
                if isinstance(ancestor, ast.stmt):
                    break
                ancestor = parents.get(ancestor)
            if not inside_guard and _filesystem_signal(expression):
                add(node, expression, "Compare", admit_reject=True)
        elif isinstance(node, ast.Assign):
            expression = _node_text(lines, node)
            target_text = " ".join(_node_text(lines, item) for item in node.targets)
            if (
                _filesystem_signal(_node_text(lines, node.value))
                and re.search(r"\b(?:mode|metadata|stat_result)\b", target_text.lower())
            ):
                add(node, expression, "ModeAssignment", admit_reject=False)
            elif (
                _PERMISSION_TOKEN_RE.search(expression)
                and re.search(
                    r"(?:BIND|SOURCE_SPEC|EXPECTED_MODE|ALLOWED_MODE|SAFE_MODE|"
                    r"GIT_MODE|PATH_MODE)",
                    target_text.upper(),
                )
            ):
                add(node, expression, "ModeSpecificationAssignment", admit_reject=False)
        elif isinstance(node, ast.AnnAssign):
            expression = _node_text(lines, node)
            target_text = _node_text(lines, node.target)
            if node.value is not None and (
                _filesystem_signal(_node_text(lines, node.value))
                or _PERMISSION_TOKEN_RE.search(expression)
                and "MODE" in target_text.upper()
            ):
                add(node, expression, "ModeSpecificationAssignment", admit_reject=False)
        elif isinstance(node, ast.Call):
            expression = _node_text(lines, node)
            name = _call_name(node).lower()
            permission_argument = bool(_PERMISSION_TOKEN_RE.search(expression))
            semantic_call = permission_argument and any(
                token in name for token in ("bound", "binding", "source")
            )
            mode_operation = "chmod" in name or any(
                keyword.arg == "mode" and _PERMISSION_TOKEN_RE.search(
                    _node_text(lines, keyword.value)
                )
                for keyword in node.keywords
                if keyword.arg is not None
            )
            if semantic_call:
                add(node, expression, "SourceBindingCall", admit_reject=True)
            elif mode_operation:
                add(node, expression, "ModeOperationCall", admit_reject=False)
        elif isinstance(node, ast.Dict):
            sibling_keys = {
                key.value
                for key in node.keys
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            }
            identity_siblings = bool(
                {"sha256", "byte_count", "path"} & sibling_keys
            )
            for key, value in zip(node.keys, node.values, strict=True):
                if not (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and _MODE_KEY_RE.fullmatch(key.value)
                ):
                    continue
                expression = _node_text(lines, value)
                if not (
                    _filesystem_signal(expression)
                    or _PERMISSION_TOKEN_RE.search(expression)
                    or key.value in {
                        "git_mode",
                        "path_modes",
                        "head_candidate_path_modes",
                        "candidate_filesystem_modes",
                    }
                    or identity_siblings and expression.strip() in {"mode", "expected_mode"}
                ):
                    continue
                synthetic = f"{key.value}: {expression}"
                add(value, synthetic, "DictModeMetadata", admit_reject=False)

    occurrences.sort(
        key=lambda row: (
            str(row["source_path"]),
            int(row["line_start"]),
            int(row["line_end"]),
            str(row["ast_node_type"]),
            str(row["occurrence_id"]),
        )
    )
    return tuple(occurrences)


def _json_mode_occurrences(
    payload: bytes,
    *,
    source_path: str,
    source_scope: str,
    namespace: str,
) -> tuple[dict[str, object], ...]:
    try:
        text = payload.decode("utf-8")
        document = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail("JSON_STATIC_PARSE_FAILED:" + source_path + ":" + str(error))
    located_lines = [
        index
        for index, line in enumerate(text.splitlines(), start=1)
        for _match in re.finditer(
            r'"(?:mode|posix_mode|filesystem_mode|st_mode|git_mode)"\s*:',
            line,
        )
    ]
    records: list[tuple[str, object, Mapping[str, object]]] = []

    def walk(value: object, json_path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = json_path + "." + str(key)
                if key in {
                    "mode",
                    "posix_mode",
                    "filesystem_mode",
                    "st_mode",
                    "git_mode",
                }:
                    records.append((child_path, child, value))
                walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{json_path}[{index}]")

    walk(document, "root")
    if len(records) != len(located_lines):
        _fail("JSON_MODE_LITERAL_LOCATION_MISMATCH:" + source_path)
    lifecycle = _lifecycle_for_path(source_path, source_scope)
    occurrences: list[dict[str, object]] = []
    for line, (json_path, value, parent) in zip(
        located_lines, records, strict=True
    ):
        literal = str(value)
        modes = _normalized_modes(literal)
        if not modes:
            continue
        if modes in {"100644", "100755"}:
            semantic_class = "GIT_EXECUTABLE_BIT_OR_FILE_CLASS_CONTRACT"
            pattern = "json_git_file_class_metadata"
            note = "JSON Git 100644/100755 class."
            bytes_or_sha = "sha256" in parent
            admit_reject = False
        elif {"path", "sha256", "byte_count"} <= set(parent):
            semantic_class = "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE"
            pattern = "json_source_binding_exact_posix_mode"
            note = "JSON binding joins exact mode to path/bytes/SHA."
            bytes_or_sha = True
            admit_reject = True
        else:
            semantic_class = "REPORTING_OR_DIAGNOSTIC_MODE_METADATA"
            pattern = "json_mode_reporting_metadata"
            note = "JSON numeric mode without full identity tuple."
            bytes_or_sha = "sha256" in parent or "byte_count" in parent
            admit_reject = False
        occurrences.append(
            _make_occurrence(
                source_scope=source_scope,
                namespace=namespace,
                source_path=source_path,
                line_start=line,
                line_end=line,
                ast_node_type="JsonObjectField",
                semantic_class=semantic_class,
                matched_pattern=pattern,
                modes=modes,
                lifecycle=lifecycle,
                bytes_or_sha=bytes_or_sha,
                risk=(
                    semantic_class
                    == "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE"
                ),
                note=note + " JSON path=" + json_path,
                is_admit_reject=admit_reject,
            )
        )
    return tuple(occurrences)


def _known_regression_cases(root: Path) -> tuple[dict[str, object], ...]:
    path = root.parent / TWO_A2_FORMAL_VALIDATOR_RELATIVE
    payload = _read_regular(path, "TWO_A2_HISTORICAL_FORMAL_VALIDATOR")
    text = payload.decode("utf-8")
    try:
        tree = ast.parse(text, filename=TWO_A2_FORMAL_VALIDATOR_RELATIVE.as_posix())
    except SyntaxError:
        _fail("TWO_A2_FORMAL_VALIDATOR_AST_INVALID")
    lines = text.splitlines()
    verifier = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "read_bound_file"
        ),
        None,
    )
    if verifier is None:
        _fail("TWO_A2_READ_BOUND_FILE_NOT_FOUND")
    verifier_text = _node_text(lines, verifier)
    required_tokens = (
        "stat.S_IMODE",
        "mode != expected_mode",
        "len(payload) != byte_count",
        "sha256(payload) != digest",
        "SOURCE_DRIFT",
    )
    if any(token not in verifier_text for token in required_tokens):
        _fail("TWO_A2_EXACT_MODE_SOURCE_DRIFT_CONTRACT_NOT_PROVEN")

    string_constants = {
        target.id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance((target := node.targets[0]), ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }
    expected_constant_paths = {
        "published_role_profile_runtime_owner": "ROLE_RUNTIME_PATH",
        "canonical_role_and_task_semantics_owner": "ROLE_OWNER_PATH",
        "published_1f8_event_task_label_availability": "ONE_F8_PATH",
    }

    cases: list[dict[str, object]] = []
    for role, source_path, expected_mode in KNOWN_REGRESSION_EXPECTATIONS:
        role_lines = [
            index
            for index, line in enumerate(lines, start=1)
            if repr(role) in line or f'"{role}"' in line
        ]
        if not role_lines:
            _fail("KNOWN_REGRESSION_ROLE_NOT_FOUND:" + role)
        mode_near_role = any(
            expected_mode in "\n".join(
                lines[max(0, line - 4) : min(len(lines), line + 12)]
            )
            for line in role_lines
        )
        if not mode_near_role:
            if role in {
                "published_role_profile_runtime_owner",
                "canonical_role_and_task_semantics_owner",
            } and 'role, "0644"' in text:
                mode_near_role = True
        constant_name = expected_constant_paths[role]
        if not mode_near_role or string_constants.get(constant_name) != source_path:
            _fail("KNOWN_REGRESSION_BINDING_NOT_PROVEN:" + role)
        cases.append(
            {
                "source_role": role,
                "path": source_path,
                "path_namespace": "project_parent_relative",
                "expected_mode": expected_mode,
                "content_identity_contract": ["byte_count", "sha256"],
                "semantic_class": "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE",
                "lifecycle_class": "HISTORICAL_IMMUTABLE_V1",
                "debt_disposition": "PRESERVE_HISTORICAL_BUT_DO_NOT_PROPAGATE",
                "static_contract_line": min(role_lines),
                "byte_sha_can_remain_exact_while_checkout_mode_changes": True,
            }
        )
    return tuple(cases)


def _current_good_reference(root: Path) -> dict[str, object]:
    path = root / CURRENT_CENSUS_MANIFEST_RELATIVE
    document = json.loads(_read_regular(path, "CURRENT_2A2_CENSUS_MANIFEST"))
    bindings = document.get("semantic_source_bindings")
    if not isinstance(bindings, list) or len(bindings) != CURRENT_CENSUS_BINDING_COUNT:
        _fail("CURRENT_2A2_CENSUS_BINDING_COUNT_INVALID")
    expected_fields = set(CURRENT_CENSUS_BINDING_FIELDS)
    if any(type(row) is not dict or set(row) != expected_fields for row in bindings):
        _fail("CURRENT_2A2_CENSUS_BINDING_SCHEMA_INVALID")
    digest = _sha256(_canonical_json(bindings).encode("utf-8"))
    if digest != CURRENT_CENSUS_BINDING_DIGEST:
        _fail("CURRENT_2A2_CENSUS_BINDING_DIGEST_INVALID")
    forbidden = {"mode", "posix_mode", "filesystem_mode", "st_mode"}
    mode_fields = sum(len(forbidden & set(row)) for row in bindings)
    if mode_fields:
        _fail("CURRENT_2A2_CENSUS_PROPAGATES_EXACT_POSIX_MODE")
    return {
        "semantic_binding_count": len(bindings),
        "canonical_digest": digest,
        "binding_fields": list(CURRENT_CENSUS_BINDING_FIELDS),
        "exact_posix_mode_field_count": mode_fields,
        "CURRENT_2A2_CENSUS_PROPAGATES_EXACT_POSIX_MODE_AUTHORITY": False,
        "negative_control_pass": True,
    }


def _scan_inventory(
    root: Path,
) -> tuple[
    tuple[dict[str, object], ...],
    tuple[dict[str, object], ...],
    dict[str, int],
]:
    repository_python = _repository_python_paths(root)
    derived_json = _derived_json_paths(root)
    external_python, external_json = _external_paths(root)
    occurrences: list[dict[str, object]] = []
    bindings: list[dict[str, object]] = []

    for relative in repository_python:
        if relative.as_posix().startswith("src/covalent_ext/"):
            scope = "REPOSITORY_OWNER_PYTHON"
        elif relative.as_posix().startswith("scripts/"):
            scope = "REPOSITORY_CHECKER_PYTHON"
        else:
            scope = "REPOSITORY_TEST_PYTHON"
        payload = _read_regular(root / relative, "REPOSITORY_PYTHON")
        bindings.append(
            _source_binding(
                root,
                relative,
                namespace="repository_relative",
                artifact_role="SCANNED_" + scope,
            )
        )
        occurrences.extend(
            classify_python_text_v2(
                payload.decode("utf-8"),
                source_path=relative.as_posix(),
                source_scope=scope,
                source_path_namespace="repository_relative",
            )
        )

    for path in external_python:
        relative = path.relative_to(root.parent).as_posix()
        payload = _read_regular(path, "EXTERNAL_PYTHON")
        bindings.append(
            _source_binding(
                root,
                path,
                namespace="repository_parent_relative",
                artifact_role="SCANNED_EXTERNAL_COVAPIE_STATE_PYTHON",
            )
        )
        occurrences.extend(
            classify_python_text_v2(
                payload.decode("utf-8"),
                source_path=relative,
                source_scope="EXTERNAL_COVAPIE_STATE_PYTHON",
                source_path_namespace="repository_parent_relative",
            )
        )

    for relative in derived_json:
        payload = _read_regular(root / relative, "DERIVED_JSON")
        bindings.append(
            _source_binding(
                root,
                relative,
                namespace="repository_relative",
                artifact_role="SCANNED_DERIVED_JSON",
            )
        )
        occurrences.extend(
            _json_mode_occurrences(
                payload,
                source_path=relative.as_posix(),
                source_scope="DERIVED_JSON",
                namespace="repository_relative",
            )
        )

    for path in external_json:
        relative = path.relative_to(root.parent).as_posix()
        payload = _read_regular(path, "EXTERNAL_AUTHORITY_JSON")
        bindings.append(
            _source_binding(
                root,
                path,
                namespace="repository_parent_relative",
                artifact_role="SCANNED_EXTERNAL_AUTHORITY_PROVENANCE_JSON",
            )
        )
        occurrences.extend(
            _json_mode_occurrences(
                payload,
                source_path=relative,
                source_scope="EXTERNAL_COVAPIE_STATE_JSON",
                namespace="repository_parent_relative",
            )
        )

    occurrences.sort(
        key=lambda row: (
            str(row["source_path_namespace"]),
            str(row["source_path"]),
            int(row["line_start"]),
            int(row["line_end"]),
            str(row["occurrence_id"]),
        )
    )
    if len({row["occurrence_id"] for row in occurrences}) != len(occurrences):
        _fail("OCCURRENCE_ID_COLLISION")
    bindings.sort(
        key=lambda row: (
            str(row["path_namespace"]),
            str(row["path"]),
            str(row["artifact_role"]),
        )
    )
    scope_counts = {
        "repository_python_files_scanned": len(repository_python),
        "external_covapie_state_python_files_scanned": len(external_python),
        "derived_json_files_inspected": len(derived_json),
        "external_authority_provenance_json_files_inspected": len(external_json),
        "authority_provenance_json_files_inspected": (
            len(derived_json) + len(external_json)
        ),
        "total_files_scanned": len(bindings),
    }
    return tuple(occurrences), tuple(bindings), scope_counts


def _counts(rows: Sequence[Mapping[str, object]], field: str, enum: Sequence[str]) -> dict[str, int]:
    counts = Counter(str(row[field]) for row in rows)
    unknown = set(counts) - set(enum)
    if unknown:
        _fail("INVENTORY_ENUM_INVALID:" + field + ":" + ",".join(sorted(unknown)))
    return {name: counts.get(name, 0) for name in enum}


def _summary(
    rows: Sequence[Mapping[str, object]],
    scope_counts: Mapping[str, int],
    known_cases: Sequence[Mapping[str, object]],
    good_reference: Mapping[str, object],
) -> dict[str, object]:
    semantic_counts = _counts(rows, "semantic_class", SEMANTIC_CLASSES)
    lifecycle_counts = _counts(rows, "lifecycle_class", LIFECYCLE_CLASSES)
    disposition_counts = _counts(rows, "debt_disposition", DEBT_DISPOSITIONS)
    exact_rows = [
        row
        for row in rows
        if row["semantic_class"]
        == "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE"
    ]
    debt_by_scope = Counter(str(row["source_scope"]) for row in exact_rows)
    debt_by_mode = Counter(
        mode
        for row in exact_rows
        for mode in str(row["expected_or_literal_mode"]).split("|")
        if mode
    )
    active_migration_targets = sorted(
        {
            str(row["source_path"])
            for row in rows
            if row["debt_disposition"] == "V2_MIGRATION_REQUIRED"
        }
    )
    readiness = {
        "audit_scope_complete": all(value > 0 for value in scope_counts.values()),
        "known_2a2_mode_regression_reproduced_by_static_contract": (
            len(known_cases) == 3
        ),
        "current_2a2_census_negative_control_pass": good_reference[
            "negative_control_pass"
        ],
        "historical_authority_modification_required": False,
        "ready_for_v2_implementation": bool(active_migration_targets)
        and len(known_cases) == 3
        and bool(good_reference["negative_control_pass"]),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "scope": {
            **scope_counts,
            "repository_scan_patterns": [
                "src/covalent_ext/**/*.py",
                "scripts/check_covapie*.py",
                "tests/test_covapie*.py",
                "data/derived/covalent_small/**/*.json",
            ],
            "external_scan_root": EXTERNAL_SCAN_ROOT_RELATIVE.as_posix(),
            "external_stage_directories": sorted(EXTERNAL_ALLOWED_STAGE_DIRECTORIES),
            "scan_is_static_and_does_not_execute_discovered_python": True,
            "path_escape_count": 0,
        },
        "inventory_counts": {
            "total_relevant_mode_occurrences": len(rows),
            "exact_posix_semantic_debt_occurrences": len(exact_rows),
            "active_v2_migration_target_file_count": len(active_migration_targets),
            "active_v2_migration_target_files": active_migration_targets,
            "exact_posix_debt_by_source_scope": dict(sorted(debt_by_scope.items())),
            "exact_posix_debt_by_literal_mode": dict(sorted(debt_by_mode.items())),
        },
        "semantic_class_counts": semantic_counts,
        "lifecycle_class_counts": lifecycle_counts,
        "debt_disposition_counts": disposition_counts,
        "known_regression_cases": list(known_cases),
        "current_good_reference": dict(good_reference),
        "proposed_v2_policy": {
            "git_tracked_semantic_source_identity": [
                "path",
                "path_namespace",
                "byte_count",
                "sha256",
            ],
            "optional_git_native_identity": ["git_blob_sha", "git_file_class"],
            "optional_git_native_identity_rationale": (
                "Git blob and 100644/100755 class are checkout-stable when repository "
                "executable identity matters; they are not runtime POSIX permissions."
            ),
            "external_semantic_source_identity": [
                "path",
                "path_namespace",
                "byte_count",
                "sha256",
                "schema_or_version_where_applicable",
            ],
            "exact_runtime_posix_mode_is_semantic_identity": False,
            "semantic_identity_and_security_hygiene_are_separate": True,
        },
        "historical_compatibility_policy": {
            "historical_v1_authority_bytes_remain_immutable": True,
            "historical_validator_rewrite_required": False,
            "normal_downstream_publication_requires_historical_mode_replay": False,
            "historical_replay_mechanism": (
                "disposable verification context reconstructing the frozen environment"
            ),
            "future_validators_forbid_exact_posix_numeric_mode_in_semantic_identity": True,
        },
        "security_hygiene_policy": {
            "regular_file": True,
            "non_symlink": True,
            "owner_readable": True,
            "not_world_writable": True,
            "expected_executable_class_where_relevant": True,
            "group_write_0664_automatically_forbidden": False,
            "candidate_safe_mode_family": ["0644", "0664"],
            "security_gate_is_not_semantic_identity": True,
            "evidence": (
                "published authority records contain legitimate 0664 files, so an "
                "owner-readable, non-world-writable policy must not reject group write by default"
            ),
        },
        "implementation_plan": [
            {
                "step": "V2-B1",
                "action": "add one common content-identity and separate security-policy helper",
            },
            {
                "step": "V2-B2",
                "action": "adopt it only in new/current active authority consumers listed by the audit",
            },
            {
                "step": "V2-B3",
                "action": "prove frozen historical validators and authority bytes remain untouched",
            },
            {
                "step": "V2-B4",
                "action": "retire exact POSIX semantic identity from future templates and checkers",
            },
        ],
        "separate_future_tech_debts": [
            {
                "name": "HISTORICAL_REPOSITORY_PROVENANCE_CONTRACT",
                "disposition": "SEPARATE_FUTURE_TECH_DEBT",
                "blocks_v2_mode_design": False,
            }
        ],
        "scientific_boundary": {
            "canonical_exact5_task_count": 5,
            "semantic_long_names": [
                "warhead_only",
                "linker_plus_warhead",
                "scaffold_plus_warhead",
                "scaffold_only",
                "scaffold_plus_linker_plus_warhead",
            ],
            "B3_present": True,
            "sixth_task_present": False,
            "I12_REVIEW_STARTED": False,
            "TRAINING_STARTED": False,
            "READY_FOR_TRAINING": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        },
        "readiness": readiness,
    }


def _manifest(
    root: Path,
    source_bindings: Sequence[Mapping[str, object]],
    inventory_payload: bytes,
    summary_payload: bytes,
    scope_counts: Mapping[str, int],
) -> dict[str, object]:
    current_bindings = []
    for role, relative in (
        ("CURRENT_2A2_CENSUS_OWNER", CURRENT_CENSUS_OWNER_RELATIVE),
        ("CURRENT_2A2_CENSUS_SUMMARY", CURRENT_CENSUS_SUMMARY_RELATIVE),
        ("CURRENT_2A2_CENSUS_MANIFEST", CURRENT_CENSUS_MANIFEST_RELATIVE),
    ):
        current_bindings.append(
            _source_binding(
                root,
                relative,
                namespace="repository_relative",
                artifact_role=role,
            )
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "artifact_role": "READ_ONLY_AUDIT_AND_V2_POLICY_DESIGN_PROVENANCE",
        "published_baseline": {
            "commit": BASELINE_HEAD,
            "tree": BASELINE_TREE,
            "subject": BASELINE_SUBJECT,
        },
        "scan_scope_counts": dict(scope_counts),
        "scanned_source_bindings": list(source_bindings),
        "current_good_reference_bindings": current_bindings,
        "output_bindings_excluding_manifest_self": [
            {
                "artifact_role": "AUDIT_INVENTORY",
                "path": (OUTPUT_DIRECTORY_RELATIVE / INVENTORY_FILE).as_posix(),
                "path_namespace": "repository_relative",
                "byte_count": len(inventory_payload),
                "sha256": _sha256(inventory_payload),
            },
            {
                "artifact_role": "AUDIT_SUMMARY",
                "path": (OUTPUT_DIRECTORY_RELATIVE / SUMMARY_FILE).as_posix(),
                "path_namespace": "repository_relative",
                "byte_count": len(summary_payload),
                "sha256": _sha256(summary_payload),
            },
        ],
        "semantic_binding_policy": {
            "allowed_fields": list(CURRENT_CENSUS_BINDING_FIELDS),
            "exact_posix_mode_field_present": False,
            "manifest_self_sha256_recorded": False,
        },
        "determinism_contract": {
            "timestamp_recorded": False,
            "hostname_recorded": False,
            "pid_recorded": False,
            "absolute_path_recorded": False,
        },
        "authority_boundary": {
            "historical_authority_modified": False,
            "external_covapie_state_modified": False,
            "runtime_helper_implemented": False,
            "I12_REVIEW_STARTED": False,
            "TRAINING_STARTED": False,
            "READY_FOR_TRAINING": False,
        },
    }


def compute_covapie_source_binding_filesystem_mode_authority_v2_audit(
    root: Path,
) -> dict[str, object]:
    root = root.resolve()
    if _git(root, "rev-parse", BASELINE_HEAD + "^{tree}") != BASELINE_TREE:
        _fail("BASELINE_TREE_MISMATCH")
    if _git(root, "show", "-s", "--format=%s", BASELINE_HEAD) != BASELINE_SUBJECT:
        _fail("BASELINE_SUBJECT_MISMATCH")
    rows, source_bindings, scope_counts = _scan_inventory(root)
    known_cases = _known_regression_cases(root)
    good_reference = _current_good_reference(root)
    summary = _summary(rows, scope_counts, known_cases, good_reference)
    return {
        "inventory": rows,
        "source_bindings": source_bindings,
        "scope_counts": scope_counts,
        "summary": summary,
    }


def build_covapie_source_binding_filesystem_mode_authority_v2_audit_artifacts(
    root: Path,
) -> dict[str, bytes]:
    computation = compute_covapie_source_binding_filesystem_mode_authority_v2_audit(
        root
    )
    inventory_payload = _csv_bytes(computation["inventory"])
    summary_payload = _json_bytes(computation["summary"])
    manifest = _manifest(
        root.resolve(),
        computation["source_bindings"],
        inventory_payload,
        summary_payload,
        computation["scope_counts"],
    )
    return {
        INVENTORY_FILE: inventory_payload,
        SUMMARY_FILE: summary_payload,
        MANIFEST_FILE: _json_bytes(manifest),
    }


def materialize_covapie_source_binding_filesystem_mode_authority_v2_audit_artifacts(
    root: Path,
) -> tuple[Path, ...]:
    root = root.resolve()
    artifacts = build_covapie_source_binding_filesystem_mode_authority_v2_audit_artifacts(
        root
    )
    output = root / OUTPUT_DIRECTORY_RELATIVE
    output.mkdir(parents=True, exist_ok=True)
    expected = {INVENTORY_FILE, SUMMARY_FILE, MANIFEST_FILE}
    existing = {path.name for path in output.iterdir()}
    if existing - expected:
        _fail("OUTPUT_DIRECTORY_HAS_UNEXPECTED_ENTRIES")
    written: list[Path] = []
    for filename in (INVENTORY_FILE, SUMMARY_FILE, MANIFEST_FILE):
        path = output / filename
        path.write_bytes(artifacts[filename])
        written.append(path)
    return tuple(written)


if __name__ == "__main__":
    repository = Path(__file__).resolve().parents[2]
    materialize_covapie_source_binding_filesystem_mode_authority_v2_audit_artifacts(
        repository
    )
